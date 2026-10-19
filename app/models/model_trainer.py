"""Обучение ML-модели прогнозирования выгорания (Этап 5, train_model.py).

Источник данных: Kaggle developer_burnout_7000 (data/developer_burnout_7000.zip,
внутри developer_burnout_dataset_7000.csv) — одна строка = один разработчик:
age, experience_years, daily_work_hours, sleep_hours, caffeine_intake,
bugs_per_day, commits_per_day, meetings_per_day, screen_time, exercise_hours,
stress_level, burnout_level.

Модель обучается только на признаках, которые можно получить из трекера
(команда features, см. feature_mapping.md):

    daily_work_hours  ← daily_work_hours  (график + переработка вне графика)
    screen_time       ← screen_time_hours (занятое время за компьютером)
    meetings_per_day  ← meetings_count    (звонки)
    sleep_hours       ← sleep_hours       (ночной простой или значение по умолчанию)

stress_level трекер не измеряет (а burnout_level почти полностью им
определяется), остальные колонки — тоже вне трекера, поэтому в обучение
не входят.

Целевая переменная: burnout_level = Low / Medium / High (мультикласс).
Модели обучаются с весами классов, лучшая выбирается по F1-macro.
Обучаются RandomForestClassifier и GradientBoostingClassifier,
лучшая сохраняется в models_storage/.
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from loguru import logger
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.utils.class_weight import compute_sample_weight

from config import settings

TARGET = "burnout_level"

# Признаки модели (имена колонок обучающего датасета)
MODEL_FEATURES = ["daily_work_hours", "screen_time", "meetings_per_day", "sleep_hours"]

# Соответствие дневных признаков трекера (features.csv) признакам модели
TRACKER_TO_MODEL = {
    "daily_work_hours": "daily_work_hours",
    "screen_time_hours": "screen_time",
    "meetings_count": "meetings_per_day",
    "sleep_hours": "sleep_hours",
}

REQUIRED_COLUMNS = MODEL_FEATURES + [TARGET]


def prepare_features(df: pd.DataFrame) -> pd.DataFrame:
    """Приводит данные к матрице признаков модели.

    Принимает как обучающий датасет (колонки MODEL_FEATURES), так и
    признаки трекера (features.csv / merged_data.csv) — их колонки
    переименовываются по TRACKER_TO_MODEL.
    """
    rename = {
        src: dst for src, dst in TRACKER_TO_MODEL.items()
        if src in df.columns and dst not in df.columns
    }
    X = df.rename(columns=rename)
    missing = [c for c in MODEL_FEATURES if c not in X.columns]
    if missing:
        raise ValueError(f"Нет признаков для модели: {missing}")
    return X[MODEL_FEATURES].apply(pd.to_numeric, errors="coerce")


class BurnoutModelTrainer:
    """Пайплайн: загрузка → предобработка → обучение → оценка → сохранение."""

    def __init__(self, file_path=None, test_size=None, random_state=None):
        self.file_path = Path(file_path) if file_path else settings.TRAIN_DATA_FILE
        self.test_size = test_size if test_size is not None else settings.TEST_SIZE
        self.random_state = (
            random_state if random_state is not None else settings.RANDOM_STATE
        )
        self.classes = list(settings.BURNOUT_CLASSES)

        self.data: pd.DataFrame | None = None
        self.X: pd.DataFrame | None = None
        self.y: pd.Series | None = None
        self.X_train = self.X_test = None
        self.y_train = self.y_test = None
        self.imputer: SimpleImputer | None = None
        self.models: dict = {}
        self.metrics: dict = {}
        self.best_model = None
        self.best_model_name: str | None = None

    # ------------------------------------------------------------------
    # Загрузка данных
    # ------------------------------------------------------------------
    def load(self, file_path=None) -> "BurnoutModelTrainer":
        """Читает датасет (CSV или ZIP с одним CSV) и проверяет колонки."""
        path = Path(file_path) if file_path else self.file_path
        if not path.exists():
            raise FileNotFoundError(
                f"Обучающий датасет не найден: {path}. "
                f"Скачайте developer_burnout_7000 с Kaggle и положите в data/."
            )

        self.data = pd.read_csv(path)
        missing = set(REQUIRED_COLUMNS) - set(self.data.columns)
        if missing:
            raise ValueError(
                f"В {path.name} отсутствуют колонки: {sorted(missing)}"
            )
        unknown = set(self.data[TARGET].dropna()) - set(self.classes)
        if unknown:
            raise ValueError(
                f"Неизвестные значения {TARGET}: {sorted(unknown)}, "
                f"ожидаются {self.classes}"
            )
        logger.info(f"Загружено {len(self.data)} записей из {path.name}")
        return self

    # ------------------------------------------------------------------
    # Предобработка
    # ------------------------------------------------------------------
    def preprocess(self) -> "BurnoutModelTrainer":
        """Формирует признаки и целевую переменную, делит на train/test."""
        if self.data is None:
            self.load()

        df = self.data.dropna(subset=[TARGET]).reset_index(drop=True)
        dropped = len(self.data) - len(df)
        if dropped:
            logger.warning(f"Строк без {TARGET} отброшено: {dropped}")

        self.X = prepare_features(df)
        self.y = df[TARGET]

        counts = self.y.value_counts().reindex(self.classes, fill_value=0)
        logger.info(
            f"Признаков: {self.X.shape[1]}, классы: "
            + ", ".join(f"{c}={n}" for c, n in counts.items())
        )

        self.X_train, self.X_test, self.y_train, self.y_test = train_test_split(
            self.X,
            self.y,
            test_size=self.test_size,
            random_state=self.random_state,
            stratify=self.y,
        )
        return self

    # ------------------------------------------------------------------
    # Обучение и оценка
    # ------------------------------------------------------------------
    def _make_models(self) -> dict:
        return {
            "random_forest": RandomForestClassifier(
                n_estimators=300,
                min_samples_leaf=5,
                class_weight="balanced",
                random_state=self.random_state,
                n_jobs=-1,
            ),
            "gradient_boosting": GradientBoostingClassifier(
                random_state=self.random_state,
            ),
        }

    def _evaluate_model(self, model, X_test, y_test) -> dict:
        y_pred = model.predict(X_test)
        try:
            roc_auc = roc_auc_score(
                y_test,
                model.predict_proba(X_test),
                multi_class="ovr",
                average="macro",
                labels=model.classes_,
            )
        except ValueError:
            # В тестовой выборке представлены не все классы
            roc_auc = float("nan")
        recalls = recall_score(
            y_test, y_pred, labels=self.classes, average=None, zero_division=0
        )
        return {
            "accuracy": accuracy_score(y_test, y_pred),
            "f1_macro": f1_score(
                y_test, y_pred, labels=self.classes, average="macro", zero_division=0
            ),
            "roc_auc": roc_auc,
            **{f"recall_{c.lower()}": r for c, r in zip(self.classes, recalls)},
            "confusion_matrix": confusion_matrix(
                y_test, y_pred, labels=self.classes
            ).tolist(),
        }

    def train(self) -> "BurnoutModelTrainer":
        """Обучает модели, оценивает и выбирает лучшую по F1-macro."""
        if self.X_train is None:
            self.preprocess()

        # Заполнение пропусков медианой, посчитанной по train
        self.imputer = SimpleImputer(strategy="median").fit(self.X_train)
        cols = list(self.X_train.columns)
        X_train = pd.DataFrame(self.imputer.transform(self.X_train), columns=cols)
        X_test = pd.DataFrame(self.imputer.transform(self.X_test), columns=cols)

        # GradientBoosting не умеет class_weight — передаём веса строк
        sample_weight = compute_sample_weight("balanced", self.y_train)

        self.models = self._make_models()
        self.metrics = {}
        for name, model in self.models.items():
            if name == "gradient_boosting":
                model.fit(X_train, self.y_train, sample_weight=sample_weight)
            else:
                model.fit(X_train, self.y_train)
            self.metrics[name] = self._evaluate_model(model, X_test, self.y_test)
            m = self.metrics[name]
            logger.info(
                f"{name}: accuracy={m['accuracy']:.3f}, "
                f"f1_macro={m['f1_macro']:.3f}, roc_auc={m['roc_auc']:.3f}, "
                f"recall_high={m['recall_high']:.3f}"
            )

        self.best_model_name = max(
            self.metrics, key=lambda n: self.metrics[n]["f1_macro"]
        )
        self.best_model = self.models[self.best_model_name]
        logger.success(f"Лучшая модель: {self.best_model_name}")
        return self

    # ------------------------------------------------------------------
    # Сохранение модели и отчёта
    # ------------------------------------------------------------------
    def save(self, model_path=None, output_dir=None) -> Path:
        """Сохраняет лучшую модель (joblib) и отчёт с метриками."""
        if self.best_model is None:
            self.train()

        model_file = Path(model_path) if model_path else settings.MODEL_FILE
        model_file.parent.mkdir(parents=True, exist_ok=True)
        bundle = {
            "model": self.best_model,
            "model_name": self.best_model_name,
            "imputer": self.imputer,
            "feature_columns": list(self.X.columns),
            "classes": self.classes,
        }
        joblib.dump(bundle, model_file)
        logger.info(f"Модель сохранена: {model_file}")

        out_dir = Path(output_dir) if output_dir else settings.OUTPUT_DIR
        out_dir.mkdir(parents=True, exist_ok=True)

        rows = []
        for name, m in self.metrics.items():
            row = {"model": name}
            for key, value in m.items():
                if key != "confusion_matrix":
                    row[key] = round(value, 4) if not np.isnan(value) else value
            row["is_best"] = name == self.best_model_name
            rows.append(row)

            matrix = pd.DataFrame(
                m["confusion_matrix"],
                index=[f"true_{c}" for c in self.classes],
                columns=[f"pred_{c}" for c in self.classes],
            )
            (out_dir / f"confusion_matrix_{name}.txt").write_text(
                matrix.to_string(), encoding="utf-8"
            )
        report_path = out_dir / "train_metrics.csv"
        pd.DataFrame(rows).to_csv(report_path, index=False, encoding="utf-8-sig")
        logger.info(f"Отчёт обучения: {report_path}")
        return model_file
