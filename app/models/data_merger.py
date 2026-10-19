"""Объединение дневных признаков трекера и анкет (Этап 4, merge).

Схема работы:
1. Загружает дневные признаки трекера (data/features.csv, команда features).
2. Загружает результаты анкеты MBI (data/questionnaire/mbi_results.csv).
3. Усредняет признаки по пользователю за последние MERGE_WINDOW_DAYS дней
   его данных (after_hours_work после усреднения — доля дней с работой
   вне графика).
4. Соединяет средние с результатами анкеты по user/full_name.
5. Сохраняет объединённый датасет в data/merged_data.csv.

Нормализация признаков в этом этапе НЕ выполняется — значения остаются
в исходных единицах (часы, штуки, доли).
"""

from pathlib import Path

import pandas as pd
from loguru import logger

from app.models.feature_builder import FEATURE_COLUMNS
from config import settings

# Признаки, которые усредняются за период (day_type — категориальный)
NUMERIC_FEATURES = [c for c in FEATURE_COLUMNS if c != "day_type"]


def questionnaire_columns() -> list[str]:
    """Колонки анкеты, попадающие в объединённый датасет."""
    columns = []
    for scale_name in settings.MBI_SUBSCALES:
        columns += [scale_name, f"{scale_name}_complete", f"{scale_name}_level"]
    return columns + ["burnout", "mbi_level"]


class DataMerger:
    """Пайплайн: загрузка → усреднение признаков → джойн → сохранение."""

    def __init__(self, features_file=None, questionnaire_file=None, window_days=None):
        """
        :param features_file: CSV дневных признаков (по умолчанию data/features.csv)
        :param questionnaire_file: CSV результатов анкеты
            (по умолчанию data/questionnaire/mbi_results.csv)
        :param window_days: за сколько последних дней усреднять признаки
            (по умолчанию MERGE_WINDOW_DAYS)
        """
        self.features_file = (
            Path(features_file) if features_file else settings.FEATURES_FILE
        )
        self.questionnaire_file = (
            Path(questionnaire_file)
            if questionnaire_file
            else settings.QUESTIONNAIRE_RESULTS_FILE
        )
        self.window_days = (
            window_days if window_days is not None else settings.MERGE_WINDOW_DAYS
        )

        self.features: pd.DataFrame | None = None
        self.features_agg: pd.DataFrame | None = None
        self.questionnaires: pd.DataFrame | None = None
        self.merged: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # Загрузка данных
    # ------------------------------------------------------------------
    def load_features(self, file_path=None) -> "DataMerger":
        """Читает CSV дневных признаков."""
        path = Path(file_path) if file_path else self.features_file
        if not path.exists():
            raise FileNotFoundError(
                f"Файл дневных признаков не найден: {path}. "
                f"Запустите команду features."
            )
        df = pd.read_csv(path, encoding="utf-8-sig")
        missing = {"user", "date"} - set(df.columns)
        if missing:
            raise ValueError(f"В {path.name} отсутствуют колонки: {sorted(missing)}")

        df["date"] = pd.to_datetime(df["date"])
        self.features = df
        logger.info(f"Загружено дневных признаков: {len(df)} из {path.name}")
        return self

    def load_questionnaires(self, file_path=None) -> "DataMerger":
        """Читает результаты анкеты MBI."""
        path = Path(file_path) if file_path else self.questionnaire_file
        if not path.exists():
            raise FileNotFoundError(
                f"Файл с результатами анкеты не найден: {path}. "
                f"Запустите команду questionnaire."
            )
        df = pd.read_csv(path, encoding="utf-8-sig")
        if "full_name" not in df.columns:
            raise ValueError(f"В {path.name} нет колонки full_name")

        self.questionnaires = df
        logger.info(f"Загружено анкет: {len(df)} из {path.name}")
        return self

    # ------------------------------------------------------------------
    # Усреднение признаков
    # ------------------------------------------------------------------
    def aggregate(self) -> pd.DataFrame:
        """Усредняет дневные признаки по пользователю за последние window_days дней."""
        if self.features is None:
            self.load_features()

        df = self.features
        if self.window_days:
            last_date = df.groupby("user")["date"].transform("max")
            df = df[df["date"] > last_date - pd.Timedelta(days=self.window_days)]

        present = [c for c in NUMERIC_FEATURES if c in df.columns]
        grouped = df.groupby("user")
        agg = grouped[present].mean().round(2)
        agg["days_count"] = grouped.size()
        agg["period_start"] = grouped["date"].min().dt.date
        agg["period_end"] = grouped["date"].max().dt.date

        self.features_agg = agg.reset_index()
        logger.info(f"Усреднены признаки: {len(self.features_agg)} пользователей")
        return self.features_agg

    # ------------------------------------------------------------------
    # Объединение с анкетами
    # ------------------------------------------------------------------
    def merge(self) -> pd.DataFrame:
        """Соединяет средние признаки с результатами анкет по user/full_name."""
        if self.features_agg is None:
            self.aggregate()
        if self.questionnaires is None:
            self.load_questionnaires()

        q = self.questionnaires.rename(columns={"full_name": "user"})
        q_cols = ["user"] + [c for c in questionnaire_columns() if c in q.columns]

        merged = q[q_cols].merge(self.features_agg, on="user", how="left")

        self.merged = merged
        logger.info(
            f"Объединено анкет: {len(merged)}, "
            f"с признаками трекера: {int(merged['days_count'].notna().sum())}"
        )
        return merged

    # ------------------------------------------------------------------
    # Сохранение
    # ------------------------------------------------------------------
    def save(self, output_path=None) -> Path:
        """Сохраняет объединённый датасет в CSV."""
        if self.merged is None:
            self.merge()

        path = Path(output_path) if output_path else settings.MERGED_FILE
        path.parent.mkdir(parents=True, exist_ok=True)
        self.merged.to_csv(path, index=False, encoding="utf-8-sig")
        logger.info(f"Объединённый датасет сохранён: {path}")
        return path

    def process(self) -> pd.DataFrame:
        """Полный цикл: загрузка → усреднение → джойн."""
        self.load_features()
        self.load_questionnaires()
        self.aggregate()
        self.merge()
        return self.merged
