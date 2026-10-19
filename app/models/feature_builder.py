"""Расчёт дневных признаков из метрик трекера (Этап 4, features).

Сырые замеры трекера (raw_data/metrics.csv, одна строка раз в
COLLECTION_INTERVAL секунд) агрегируются по пользователю и дню в признаки:

    day_type           — Weekday / Weekend
    scheduled_hours    — длительность рабочего дня по графику
                         (WORK_DAY_START..WORK_DAY_END или --work-start/--work-end;
                         в выходной — 0)
    overtime_hours     — занятое время вне графика (в выходной — всё занятое время)
    daily_work_hours   — scheduled_hours + overtime_hours (график + переработка)
    work_hours         — занятое время в рабочих приложениях (WORK_CATEGORIES)
    screen_time_hours  — всё занятое время за компьютером
    meetings_count     — число звонков не короче MEETING_MIN_MINUTES
    breaks_taken       — число простоев от BREAK_MIN до BREAK_MAX минут
    after_hours_work   — 1, если вне рабочего дня занято не меньше
                         AFTER_HOURS_MIN_MINUTES минут (график — WORK_DAY_START..
                         WORK_DAY_END или --work-start/--work-end)
    sleep_hours        — ночной простой перед первой активностью дня
                         (если измерить нельзя — SLEEP_DEFAULT_HOURS)

Замер считается «занятым», если пользователь активен (activity.is_active)
или открыто окно звонка — во время звонка клавиатура и мышь простаивают.
Экран блокировки (LockApp.exe) всегда считается бездействием.

Подробное соответствие признаков — в feature_mapping.md.
"""

from pathlib import Path

import pandas as pd
from loguru import logger

from app.models.process_classifier import ProcessClassifier
from config import settings

REQUIRED_COLUMNS = ["timestamp", "window.process_name", "activity.is_active"]

FEATURE_COLUMNS = [
    "day_type",
    "scheduled_hours",
    "overtime_hours",
    "daily_work_hours",
    "work_hours",
    "screen_time_hours",
    "meetings_count",
    "breaks_taken",
    "after_hours_work",
    "sleep_hours",
]


class DailyFeatureBuilder:
    """Пайплайн: загрузка метрик → разметка замеров → дневные признаки → сохранение."""

    def __init__(self, tracker_file=None, user=None, work_start=None, work_end=None):
        """
        :param tracker_file: CSV метрик трекера (по умолчанию raw_data/metrics.csv)
        :param user: ФИО для метрик без колонки user
            (по умолчанию USER_NAME из .env)
        :param work_start: начало рабочего дня ЧЧ:ММ (по умолчанию WORK_DAY_START)
        :param work_end: конец рабочего дня ЧЧ:ММ (по умолчанию WORK_DAY_END)
        """
        self.tracker_file = Path(tracker_file) if tracker_file else settings.TRACKER_FILE
        self.user = user or settings.USER_NAME.strip() or None
        self.work_start = self._parse_time(work_start or settings.WORK_DAY_START)
        self.work_end = self._parse_time(work_end or settings.WORK_DAY_END)
        if self.work_start >= self.work_end:
            raise ValueError(
                f"Начало рабочего дня ({work_start or settings.WORK_DAY_START}) "
                f"должно быть раньше конца ({work_end or settings.WORK_DAY_END})"
            )

        self.classifier = ProcessClassifier()
        self.metrics: pd.DataFrame | None = None
        self.features: pd.DataFrame | None = None

    # ------------------------------------------------------------------
    # Загрузка данных
    # ------------------------------------------------------------------
    def load(self, file_path=None) -> "DailyFeatureBuilder":
        """Читает CSV метрик трекера и приводит типы колонок."""
        path = Path(file_path) if file_path else self.tracker_file
        if not path.exists():
            raise FileNotFoundError(
                f"Файл метрик трекера не найден: {path}. "
                f"Запустите команду collect."
            )

        df = pd.read_csv(path)
        missing = set(REQUIRED_COLUMNS) - set(df.columns)
        if missing:
            raise ValueError(f"В {path.name} отсутствуют колонки: {sorted(missing)}")

        # Старые версии трекера не писали колонку user
        if "user" not in df.columns:
            df["user"] = None
        if df["user"].isna().any():
            if not self.user:
                raise ValueError(
                    f"В {path.name} нет имени пользователя. "
                    f"Укажите --user или USER_NAME в .env."
                )
            logger.warning(f"Метрикам без колонки user присвоено имя: {self.user}")
            df["user"] = df["user"].fillna(self.user)

        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"])
        df["activity.is_active"] = (
            df["activity.is_active"].astype(str).str.strip().str.lower() == "true"
        )
        df["window.process_name"] = df["window.process_name"].fillna("")
        if "window.window_title" not in df.columns:
            df["window.window_title"] = ""
        df["window.window_title"] = df["window.window_title"].fillna("")

        self.metrics = df.sort_values(["user", "timestamp"]).reset_index(drop=True)
        logger.info(f"Загружено замеров трекера: {len(self.metrics)} из {path.name}")
        return self

    # ------------------------------------------------------------------
    # Разметка замеров
    # ------------------------------------------------------------------
    def _mark_samples(self, df: pd.DataFrame) -> pd.DataFrame:
        """Добавляет флаги is_call, is_busy, is_work к каждому замеру."""
        df = df.copy()
        process = df["window.process_name"].str.lower()
        title = df["window.window_title"].str.lower()

        call_processes = [p.lower() for p in settings.CALL_PROCESSES]
        is_call = process.isin(call_processes)
        for keyword in settings.CALL_WINDOW_KEYWORDS:
            is_call |= title.str.contains(keyword.lower(), regex=False)

        is_locked = process == settings.LOCK_SCREEN_PROCESS.lower()

        categories = {
            name: self.classifier.classify(name)
            for name in df["window.process_name"].unique()
        }
        category = df["window.process_name"].map(categories)

        df["is_call"] = is_call & ~is_locked
        df["is_busy"] = (df["activity.is_active"] | df["is_call"]) & ~is_locked
        df["is_work"] = df["is_busy"] & category.isin(settings.WORK_CATEGORIES)
        return df

    @staticmethod
    def _parse_time(value: str) -> int:
        """Переводит время ЧЧ:ММ в минуты от полуночи."""
        try:
            hours, minutes = str(value).strip().split(":")
            hours, minutes = int(hours), int(minutes)
        except ValueError:
            raise ValueError(f"Время должно быть в формате ЧЧ:ММ, получено: {value}")
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError(f"Некорректное время: {value}")
        return hours * 60 + minutes

    @staticmethod
    def _interval_seconds(df: pd.DataFrame) -> float:
        """Интервал между замерами: медиана по данным, иначе из настроек."""
        diffs = df["timestamp"].diff().dt.total_seconds().dropna()
        diffs = diffs[diffs > 0]
        return float(diffs.median()) if not diffs.empty else float(settings.COLLECTION_INTERVAL)

    # ------------------------------------------------------------------
    # Признаки одного пользователя
    # ------------------------------------------------------------------
    def _count_meetings(self, call_times: pd.Series, interval: float) -> int:
        """Число звонков: склеивает близкие отрезки и отбрасывает короткие."""
        if call_times.empty:
            return 0
        merge_gap = settings.MEETING_MERGE_GAP_MINUTES * 60 + interval
        segment_id = (call_times.diff().dt.total_seconds() > merge_gap).cumsum()
        durations = call_times.groupby(segment_id).agg(
            lambda t: (t.max() - t.min()).total_seconds() + interval
        )
        return int((durations >= settings.MEETING_MIN_MINUTES * 60).sum())

    def _build_user(self, user: str, df: pd.DataFrame) -> list[dict]:
        """Считает дневные признаки для одного пользователя."""
        interval = self._interval_seconds(df)

        # Непрерывные участки записи: разрыв больше двух интервалов —
        # трекер не работал (компьютер выключен)
        record_gap = df["timestamp"].diff().dt.total_seconds() > 2 * interval
        df = df.assign(record_id=record_gap.cumsum(), date=df["timestamp"].dt.date)

        busy = df[df["is_busy"]].copy()
        if busy.empty:
            logger.warning(f"{user}: нет ни одного замера с активностью")
            return []

        # Простой перед каждым занятым замером (от предыдущего занятого)
        prev_time = busy["timestamp"].shift()
        busy["idle_minutes"] = (
            (busy["timestamp"] - prev_time).dt.total_seconds() - interval
        ) / 60
        busy["prev_date"] = busy["date"].shift()
        busy["continuous"] = busy["record_id"] == busy["record_id"].shift()

        hours = interval / 3600
        rows = []
        for date, day in busy.groupby("date"):
            same_day = day["prev_date"] == date
            idle = day.loc[same_day, "idle_minutes"]
            breaks = idle.between(settings.BREAK_MIN_MINUTES, settings.BREAK_MAX_MINUTES)

            minute_of_day = day["timestamp"].dt.hour * 60 + day["timestamp"].dt.minute
            outside = (minute_of_day < self.work_start) | (minute_of_day >= self.work_end)
            after_hours = outside.sum() * interval / 60 >= settings.AFTER_HOURS_MIN_MINUTES

            # Сон: простой перед первой активностью дня, если трекер
            # писал без разрывов и простой не длиннее SLEEP_MAX_HOURS;
            # иначе — значение по умолчанию
            first = day.iloc[0]
            sleep = first["idle_minutes"] / 60
            if (
                pd.isna(sleep)
                or not first["continuous"]
                or sleep > settings.SLEEP_MAX_HOURS
            ):
                sleep = settings.SLEEP_DEFAULT_HOURS

            call_times = df.loc[(df["date"] == date) & df["is_call"], "timestamp"]

            # Рабочий день = график + переработка (занятое время вне графика).
            # В выходной графика нет — вся активность считается переработкой
            is_weekend = pd.Timestamp(date).dayofweek >= 5
            if is_weekend:
                scheduled, overtime = 0.0, len(day) * hours
            else:
                scheduled = (self.work_end - self.work_start) / 60
                overtime = outside.sum() * hours

            rows.append({
                "user": user,
                "date": date,
                "day_type": "Weekend" if is_weekend else "Weekday",
                "scheduled_hours": round(scheduled, 2),
                "overtime_hours": round(overtime, 2),
                "daily_work_hours": round(scheduled + overtime, 2),
                "work_hours": round(day["is_work"].sum() * hours, 2),
                "screen_time_hours": round(len(day) * hours, 2),
                "meetings_count": self._count_meetings(call_times, interval),
                "breaks_taken": int(breaks.sum()),
                "after_hours_work": int(after_hours),
                "sleep_hours": round(sleep, 2),
            })

        total_days = df["date"].nunique()
        if total_days > len(rows):
            logger.info(
                f"{user}: дней без активности пропущено: {total_days - len(rows)}"
            )
        return rows

    # ------------------------------------------------------------------
    # Расчёт и сохранение
    # ------------------------------------------------------------------
    def build(self) -> pd.DataFrame:
        """Считает дневные признаки для всех пользователей."""
        if self.metrics is None:
            self.load()

        marked = self._mark_samples(self.metrics)
        rows = []
        for user, user_df in marked.groupby("user"):
            rows.extend(self._build_user(user, user_df.reset_index(drop=True)))

        self.features = pd.DataFrame(rows, columns=["user", "date"] + FEATURE_COLUMNS)
        logger.info(
            f"Рассчитано дневных признаков: {len(self.features)} "
            f"(пользователей: {self.features['user'].nunique()})"
        )
        return self.features

    def save(self, output_path=None) -> Path:
        """Сохраняет дневные признаки в CSV.

        Если файл уже есть, в нём заменяются только строки пользователей
        из текущего расчёта — признаки остальных участников сохраняются.
        """
        if self.features is None:
            self.build()

        path = Path(output_path) if output_path else settings.FEATURES_FILE
        path.parent.mkdir(parents=True, exist_ok=True)

        result = self.features
        if path.exists():
            existing = pd.read_csv(path, encoding="utf-8-sig")
            kept = existing[~existing["user"].isin(self.features["user"])]
            if not kept.empty:
                logger.info(
                    f"Сохранены признаки других пользователей: "
                    f"{kept['user'].nunique()} ({len(kept)} дней)"
                )
                result = pd.concat([kept, self.features.astype({"date": str})])
            result = result.sort_values(["user", "date"]).reset_index(drop=True)

        result.to_csv(path, index=False, encoding="utf-8-sig")
        logger.info(f"Дневные признаки сохранены: {path}")
        return path

    def process(self) -> pd.DataFrame:
        """Полный цикл: загрузка → расчёт признаков."""
        self.load()
        return self.build()
