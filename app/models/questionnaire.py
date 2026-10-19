"""
Обработка анкеты MBI (Maslach Burnout Inventory, сокращённый вариант).
- Загрузка CSV с ответами из Google Forms
- Расчёт индексов по 3 субшкалам
- Классификация уровня по каждой субшкале
- Определение целевой переменной "выгорание" (0/1) для ML
- Общий уровень выгорания Low/Medium/High (mbi_level) — для сравнения с прогнозом
- Сохранение результатов в data/questionnaire/
"""

from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

from config import settings

# Шкала частоты MBI (0..6) — текстовые варианты ответов Google Forms
ANSWER_LABELS = {
    "никогда": 0,
    "очень редко": 1,
    "редко": 2,
    "иногда": 3,
    "часто": 4,
    "очень часто": 5,
    "каждый день": 6,
}

LEVEL_NAMES = {0: "low", 1: "medium", 2: "high"}


class MBIQuestionnaireProcessor:
    """
    Разбирает CSV ответов Google Forms и считает показатели MBI.
    """

    def __init__(
            self,
            file_path,
            skip_columns: int = None,
            items_count: int = None,
            answer_labels: dict = None,
    ):
        self.file_path = Path(file_path)
        self.skip_columns = (
            skip_columns
            if skip_columns is not None
            else settings.QUESTIONNAIRE_SKIP_COLUMNS
        )
        self.items_count = items_count or settings.QUESTIONNAIRE_ITEMS_COUNT
        self.answer_labels = answer_labels or ANSWER_LABELS

        self._raw: pd.DataFrame | None = None
        self._answers: pd.DataFrame | None = None
        self.scores: pd.DataFrame | None = None
        self.levels: pd.DataFrame | None = None
        self.results: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # Загрузка данных
    # ------------------------------------------------------------------
    def load(self, file_path=None) -> "MBIQuestionnaireProcessor":
        """Читает CSV из Google Forms, отделяет служебные колонки."""
        path = Path(file_path) if file_path else self.file_path
        if not path.exists():
            raise FileNotFoundError(f"Файл с ответами не найден: {path}")

        self._raw = pd.read_csv(path)

        # Проверяем, что колонок достаточно
        required = self.skip_columns + self.items_count
        if self._raw.shape[1] < required:
            raise ValueError(
                f"В файле {path.name} только {self._raw.shape[1]} колонок, "
                f"а ожидается минимум {required} "
                f"({self.skip_columns} служебных + {self.items_count} вопросов)"
            )

        answers_raw = self._raw.iloc[
            :, self.skip_columns:self.skip_columns + self.items_count
        ]
        self._answers = answers_raw.map(self._to_numeric)
        self._answers.columns = [f"q{i + 1}" for i in range(self.items_count)]
        return self

    def _to_numeric(self, value):
        """Переводит ответ в число 0..6 (принимает цифры и текстовые метки)."""
        if pd.isna(value):
            return np.nan
        text = str(value).strip().lower()
        if text == "":
            return np.nan
        try:
            num = float(text)
            return int(num) if num.is_integer() else num
        except ValueError:
            pass
        label = " ".join(text.split())
        if label in self.answer_labels:
            return self.answer_labels[label]
        return np.nan

    # ------------------------------------------------------------------
    # Расчёт MBI
    # ------------------------------------------------------------------
    @staticmethod
    def _subscale_items(scale_cfg: dict) -> list:
        """Номера вопросов субшкалы (с 1) → индексы колонок."""
        return [i - 1 for i in scale_cfg["items"]]

    def compute_mbi(self) -> pd.DataFrame:
        """Считает сумму баллов по каждой субшкале."""
        if self._answers is None:
            self.load()

        subscale_scores = {}
        for scale_name, cfg in settings.MBI_SUBSCALES.items():
            cols = self._subscale_items(cfg)
            subscale_scores[scale_name] = self._answers.iloc[:, cols].sum(axis=1)

        scores_df = pd.DataFrame(subscale_scores)
        # Дополнительно отмечаем незаполненные субшкалы
        for scale_name, cfg in settings.MBI_SUBSCALES.items():
            cols = self._subscale_items(cfg)
            complete = self._answers.iloc[:, cols].notna().all(axis=1)
            scores_df[f"{scale_name}_complete"] = complete

        self.scores = scores_df
        return scores_df

    # ------------------------------------------------------------------
    # Классификация
    # ------------------------------------------------------------------
    @staticmethod
    def classify_scale(score, thresholds: dict) -> int:
        """Возвращает уровень (0=low, 1=medium, 2=high) по порогам."""
        if pd.isna(score):
            return None
        if score >= thresholds["high"]:
            return 2
        if score >= thresholds["medium"]:
            return 1
        return 0

    def classify(self) -> pd.DataFrame:
        """Определяет уровень по каждой субшкале и целевой признак выгорания."""
        if self.scores is None:
            self.compute_mbi()

        levels = pd.DataFrame(index=self.scores.index)
        burnout_flags = []
        severities = []

        for scale_name, cfg in settings.MBI_SUBSCALES.items():
            thresholds = settings.MBI_THRESHOLDS[scale_name]
            levels[f"{scale_name}_level"] = self.scores[scale_name].apply(
                lambda s: LEVEL_NAMES[self.classify_scale(s, thresholds)]
                if not pd.isna(s) else ""
            )

            # Признак "сильный риск" по шкале (по правилам выгорания)
            rule = settings.MBI_BURNOUT_RULES[scale_name]
            if rule == ">= high":
                risk = self.scores[scale_name] >= thresholds["high"]
            else:  # "< medium"
                risk = self.scores[scale_name] < thresholds["medium"]
            burnout_flags.append(risk.fillna(False))

            # Тяжесть по шкале: 0..2, для обратной шкалы — наоборот
            level_index = self.scores[scale_name].apply(
                lambda s: self.classify_scale(s, thresholds)
            ).astype(float)
            severities.append(2 - level_index if cfg["reversed"] else level_index)

        levels["burnout"] = pd.concat(burnout_flags, axis=1).any(axis=1).astype(int)

        severity = pd.concat(severities, axis=1)
        levels["mbi_level"] = np.select(
            [
                levels["burnout"] == 1,
                severity.sum(axis=1) >= settings.MBI_OVERALL_MEDIUM_SCORE,
                severity.notna().any(axis=1),
            ],
            ["High", "Medium", "Low"],
            default="",
        )

        self.levels = levels
        return levels

    # ------------------------------------------------------------------
    # Итоговая таблица и сохранение
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_service_columns(service: pd.DataFrame) -> pd.DataFrame:
        """Приводит служебные колонки к единому формату.

        Google Forms называет колонку времени «Отметка времени»,
        а ФИО — «ФИО». Для объединения данных нужны стандартные имена
        timestamp и full_name.
        """
        rename_map = {}
        for col in service.columns:
            lowered = str(col).lower()
            if "отметка" in lowered or "времен" in lowered:
                rename_map[col] = "timestamp"
            if "фио" in lowered or "ф.и.о" in lowered:
                rename_map[col] = "full_name"
        service = service.rename(columns=rename_map)

        if "timestamp" not in service.columns and service.shape[1] >= 1:
            service.insert(0, "timestamp", "")
        if "full_name" not in service.columns and service.shape[1] >= 2:
            service["full_name"] = service.iloc[:, 1]
        return service

    def process(self) -> pd.DataFrame:
        """Полный цикл: загрузка → расчёт → классификация."""
        if self._answers is None:
            self.load()
        self.compute_mbi()
        self.classify()

        service = self._normalize_service_columns(
            self._raw.iloc[:, :self.skip_columns].reset_index(drop=True)
        )
        result = pd.concat([service, self._answers, self.scores, self.levels], axis=1)
        self.results = result
        return result

    def save(self, output_dir=None, file_name: str = "mbi_results.csv") -> Path:
        """Сохраняет результаты в data/questionnaire/."""
        if self.results is None:
            self.process()

        out_dir = Path(output_dir) if output_dir else settings.QUESTIONNAIRE_RESULTS_DIR
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / file_name

        self.results.to_csv(out_path, index=False, encoding="utf-8-sig")
        logger.info(f"Результаты анкеты сохранены: {out_path}")
        return out_path