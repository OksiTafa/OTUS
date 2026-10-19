"""Прогноз выгорания по метрикам трекера (Этап 5.5, predict).

Схема работы:
1. Загружает обученную модель (models_storage/burnout_model.pkl, команда train).
2. Загружает дневные признаки трекера (data/features.csv, команда features)
   и усредняет их по пользователю за период — так же, как merge.
3. Считает вероятности Low / Medium / High и итоговый уровень.
4. Если есть результаты анкеты MBI — добавляет общий уровень по анкете
   (mbi_level) и отмечает, совпал ли прогноз с анкетой.
5. Сохраняет результат в output/predictions.csv.
"""

from pathlib import Path

import joblib
import pandas as pd
from loguru import logger

from app.models.data_merger import DataMerger
from app.models.model_trainer import prepare_features
from config import settings

# Человекочитаемый вывод уровня
PREDICTION_TEXT = {
    "Low": "низкая вероятность выгорания",
    "Medium": "средняя вероятность выгорания",
    "High": "высокая вероятность выгорания",
}


class BurnoutPredictor:
    """Пайплайн: модель + признаки трекера → вероятности → сравнение с MBI → CSV."""

    def __init__(
            self,
            model_file=None,
            features_file=None,
            questionnaire_file=None,
            window_days=None,
    ):
        """
        :param model_file: файл модели (по умолчанию models_storage/burnout_model.pkl)
        :param features_file: дневные признаки (по умолчанию data/features.csv)
        :param questionnaire_file: результаты анкеты
            (по умолчанию data/questionnaire/mbi_results.csv); если файла нет,
            прогноз считается без сравнения с MBI
        :param window_days: за сколько последних дней усреднять признаки
            (по умолчанию MERGE_WINDOW_DAYS)
        """
        self.model_file = Path(model_file) if model_file else settings.MODEL_FILE
        self.merger = DataMerger(
            features_file=features_file,
            questionnaire_file=questionnaire_file,
            window_days=window_days,
        )

        self.bundle: dict | None = None
        self.predictions: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # Загрузка
    # ------------------------------------------------------------------
    def load_model(self) -> "BurnoutPredictor":
        """Загружает модель, imputer и список признаков."""
        if not self.model_file.exists():
            raise FileNotFoundError(
                f"Модель не найдена: {self.model_file}. Запустите команду train."
            )
        self.bundle = joblib.load(self.model_file)
        logger.info(
            f"Загружена модель {self.bundle['model_name']} из {self.model_file.name}"
        )
        return self

    def _load_mbi(self) -> pd.DataFrame | None:
        """Общий уровень MBI по пользователю (если анкета есть)."""
        if not self.merger.questionnaire_file.exists():
            logger.warning(
                f"Анкета не найдена ({self.merger.questionnaire_file.name}) — "
                f"прогноз без сравнения с MBI"
            )
            return None
        q = self.merger.load_questionnaires().questionnaires
        cols = [c for c in ("burnout", "mbi_level") if c in q.columns]
        return q.rename(columns={"full_name": "user"})[["user"] + cols].rename(
            columns={"burnout": "mbi_burnout"}
        )

    # ------------------------------------------------------------------
    # Прогноз
    # ------------------------------------------------------------------
    def predict(self) -> pd.DataFrame:
        """Считает вероятности уровней выгорания для каждого пользователя."""
        if self.bundle is None:
            self.load_model()

        agg = self.merger.aggregate()
        if agg.empty:
            raise ValueError("Нет дневных признаков для прогноза")

        X = prepare_features(agg)[self.bundle["feature_columns"]]
        X = pd.DataFrame(self.bundle["imputer"].transform(X), columns=X.columns)

        model = self.bundle["model"]
        proba = pd.DataFrame(model.predict_proba(X), columns=model.classes_)
        classes = self.bundle["classes"]
        proba = proba[classes]

        result = agg[["user", "period_start", "period_end", "days_count"]].copy()
        result[list(X.columns)] = X.round(2).values
        for cls in classes:
            result[f"prob_{cls.lower()}"] = proba[cls].round(3).values
        result["predicted_level"] = proba.idxmax(axis=1).values
        result["prediction"] = result["predicted_level"].map(PREDICTION_TEXT)

        mbi = self._load_mbi()
        if mbi is not None:
            result = result.merge(mbi, on="user", how="left")
            if "mbi_level" in result.columns:
                has_mbi = result["mbi_level"].fillna("").astype(str) != ""
                result["match"] = (
                    result["predicted_level"] == result["mbi_level"]
                ).where(has_mbi)

        self.predictions = result
        for row in result.itertuples():
            probs = ", ".join(
                f"{cls} {getattr(row, f'prob_{cls.lower()}'):.0%}" for cls in classes
            )
            mbi_text = (
                f", по анкете MBI: {row.mbi_level}"
                if "mbi_level" in result.columns and isinstance(row.mbi_level, str)
                and row.mbi_level else ""
            )
            logger.info(f"{row.user}: {row.prediction} ({probs}){mbi_text}")
        return result

    # ------------------------------------------------------------------
    # Сохранение
    # ------------------------------------------------------------------
    def save(self, output_path=None) -> Path:
        """Сохраняет прогноз в CSV."""
        if self.predictions is None:
            self.predict()

        path = Path(output_path) if output_path else settings.PREDICTIONS_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        self.predictions.to_csv(path, index=False, encoding="utf-8-sig")
        logger.info(f"Прогноз сохранён: {path}")
        return path

    def process(self) -> pd.DataFrame:
        """Полный цикл: модель → признаки → прогноз."""
        self.load_model()
        self.merger.load_features()
        return self.predict()
