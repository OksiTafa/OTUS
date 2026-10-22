"""Тесты расчёта дневных признаков (app/models/feature_builder.py)."""

import pandas as pd
import pytest

from app.models.feature_builder import FEATURE_COLUMNS, DailyFeatureBuilder
from config import settings

USER = "Иванов И.И."


@pytest.fixture(autouse=True)
def fixed_settings(monkeypatch):
    """Фиксирует настройки, чтобы тесты не зависели от .env и умолчаний."""
    monkeypatch.setattr(settings, "WORK_DAY_START", "09:00")
    monkeypatch.setattr(settings, "WORK_DAY_END", "19:00")
    monkeypatch.setattr(settings, "AFTER_HOURS_MIN_MINUTES", 10)
    monkeypatch.setattr(settings, "SLEEP_DEFAULT_HOURS", 8.0)


def minutes(start, count, process="code.exe", title="", active=True):
    """Замеры раз в минуту, начиная с start."""
    begin = pd.Timestamp(start)
    return [
        {
            "user": USER,
            "timestamp": (begin + pd.Timedelta(minutes=i)).isoformat(),
            "window.window_title": title,
            "window.process_name": process,
            "activity.is_active": active,
        }
        for i in range(count)
    ]


def make_csv(tmp_path, rows, drop_user=False):
    df = pd.DataFrame(rows)
    if drop_user:
        df = df.drop(columns=["user"])
    path = tmp_path / "metrics.csv"
    df.to_csv(path, index=False)
    return path


def build(tmp_path, rows, **kwargs):
    builder = DailyFeatureBuilder(make_csv(tmp_path, rows), **kwargs)
    return builder.process()


def day(features, date):
    return features[features["date"] == pd.Timestamp(date).date()].iloc[0]


class TestLoad:
    def test_file_missing(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            DailyFeatureBuilder(tmp_path / "nope.csv").load()

    def test_required_columns(self, tmp_path):
        path = tmp_path / "metrics.csv"
        pd.DataFrame([{"timestamp": "2026-10-15 10:00"}]).to_csv(path, index=False)
        with pytest.raises(ValueError, match="отсутствуют колонки"):
            DailyFeatureBuilder(path).load()

    def test_no_user_column_requires_user(self, tmp_path, monkeypatch):
        monkeypatch.setattr(settings, "USER_NAME", "")
        path = make_csv(tmp_path, minutes("2026-10-15 10:00", 5), drop_user=True)
        with pytest.raises(ValueError, match="--user"):
            DailyFeatureBuilder(path).load()

    def test_no_user_column_filled_from_param(self, tmp_path):
        path = make_csv(tmp_path, minutes("2026-10-15 10:00", 5), drop_user=True)
        features = DailyFeatureBuilder(path, user="Петров П.П.").process()
        assert features["user"].tolist() == ["Петров П.П."]


class TestTime:
    def test_screen_and_work_hours(self, tmp_path):
        rows = minutes("2026-10-15 10:00", 60, process="code.exe") + minutes(
            "2026-10-15 11:00", 30, process="chrome.exe"
        )
        f = day(build(tmp_path, rows), "2026-10-15")
        assert f["screen_time_hours"] == 1.5
        assert f["work_hours"] == 1.0

    def test_lock_screen_is_idle(self, tmp_path):
        rows = minutes("2026-10-15 10:00", 30) + minutes(
            "2026-10-15 10:30", 30, process="LockApp.exe", active=True
        )
        f = day(build(tmp_path, rows), "2026-10-15")
        assert f["screen_time_hours"] == 0.5

    def test_day_without_activity_skipped(self, tmp_path):
        rows = minutes("2026-10-15 10:00", 10) + minutes(
            "2026-10-16 10:00", 10, process="LockApp.exe", active=False
        )
        features = build(tmp_path, rows)
        assert features["date"].astype(str).tolist() == ["2026-10-15"]

    def test_columns(self, tmp_path):
        features = build(tmp_path, minutes("2026-10-15 10:00", 10))
        assert features.columns.tolist() == ["user", "date"] + FEATURE_COLUMNS


class TestCalls:
    def test_call_without_input_is_busy(self, tmp_path):
        rows = minutes(
            "2026-10-15 10:00", 10, process="app.exe", title="Звонок", active=False
        )
        f = day(build(tmp_path, rows), "2026-10-15")
        assert f["screen_time_hours"] == round(10 / 60, 2)
        assert f["work_hours"] == round(10 / 60, 2)
        assert f["meetings_count"] == 1

    def test_short_call_not_meeting(self, tmp_path):
        rows = minutes("2026-10-15 10:00", 3, process="app.exe", title="Звонок")
        assert day(build(tmp_path, rows), "2026-10-15")["meetings_count"] == 0

    def test_chat_window_not_meeting(self, tmp_path):
        rows = minutes("2026-10-15 10:00", 20, process="app.exe", title="hippo")
        assert day(build(tmp_path, rows), "2026-10-15")["meetings_count"] == 0

    def test_close_call_segments_merged(self, tmp_path):
        rows = (
            minutes("2026-10-15 10:00", 4, process="app.exe", title="Звонок")
            + minutes("2026-10-15 10:04", 2, process="code.exe")
            + minutes("2026-10-15 10:06", 4, process="app.exe", title="Звонок")
            + minutes("2026-10-15 10:30", 6, process="zoom.exe")
        )
        assert day(build(tmp_path, rows), "2026-10-15")["meetings_count"] == 2


class TestBreaks:
    def test_breaks_between_min_and_max(self, tmp_path):
        rows = (
            minutes("2026-10-15 10:00", 30)
            + minutes("2026-10-15 10:30", 10, active=False)  # перерыв 10 мин
            + minutes("2026-10-15 10:40", 30)
            + minutes("2026-10-15 11:10", 2, active=False)  # слишком короткий
            + minutes("2026-10-15 11:12", 30)
            + minutes("2026-10-15 11:42", 90, active=False)  # слишком длинный
            + minutes("2026-10-15 13:12", 10)
        )
        assert day(build(tmp_path, rows), "2026-10-15")["breaks_taken"] == 1

    def test_tracker_gap_counts_as_break(self, tmp_path):
        rows = minutes("2026-10-15 10:00", 30) + minutes("2026-10-15 10:50", 30)
        assert day(build(tmp_path, rows), "2026-10-15")["breaks_taken"] == 1


class TestCalendar:
    def test_after_hours(self, tmp_path):
        rows = minutes("2026-10-15 10:00", 10) + minutes("2026-10-16 20:00", 10)
        features = build(tmp_path, rows)
        assert day(features, "2026-10-15")["after_hours_work"] == 0
        assert day(features, "2026-10-16")["after_hours_work"] == 1

    def test_custom_work_day(self, tmp_path):
        rows = (
            minutes("2026-10-15 08:30", 10)  # в рабочее время 8:30–17:30
            + minutes("2026-10-16 08:15", 20)  # 15 мин до начала
            + minutes("2026-10-19 17:25", 20)  # 15 мин после конца
        )
        features = build(tmp_path, rows, work_start="08:30", work_end="17:30")
        assert (features["scheduled_hours"] == 9.0).all()
        assert day(features, "2026-10-15")["after_hours_work"] == 0
        assert day(features, "2026-10-16")["after_hours_work"] == 1
        assert day(features, "2026-10-19")["after_hours_work"] == 1

    def test_after_hours_below_threshold(self, tmp_path):
        rows = minutes("2026-10-15 18:55", 14)  # 9 мин после 19:00
        f = day(build(tmp_path, rows), "2026-10-15")
        assert f["after_hours_work"] == 0

    def test_after_hours_threshold_from_settings(self, tmp_path, monkeypatch):
        monkeypatch.setattr(settings, "AFTER_HOURS_MIN_MINUTES", 1)
        rows = minutes("2026-10-15 18:55", 6)  # 1 мин после 19:00
        f = day(build(tmp_path, rows), "2026-10-15")
        assert f["after_hours_work"] == 1

    def test_work_day_from_settings(self, tmp_path, monkeypatch):
        monkeypatch.setattr(settings, "WORK_DAY_START", "08:30")
        monkeypatch.setattr(settings, "WORK_DAY_END", "17:30")
        features = build(tmp_path, minutes("2026-10-15 08:30", 10))
        assert day(features, "2026-10-15")["after_hours_work"] == 0

    @pytest.mark.parametrize(
        "start, end", [("8.30", "17:30"), ("25:00", "17:30"), ("18:00", "09:00")]
    )
    def test_invalid_work_day(self, tmp_path, start, end):
        with pytest.raises(ValueError):
            DailyFeatureBuilder(tmp_path / "m.csv", work_start=start, work_end=end)

    def test_overtime_weekday(self, tmp_path):
        rows = (
            minutes("2026-10-15 08:00", 30)  # 30 мин до 8:30
            + minutes("2026-10-15 12:00", 60)  # в графике
            + minutes("2026-10-15 17:30", 60)  # 60 мин после 17:30
        )
        f = day(
            build(tmp_path, rows, work_start="08:30", work_end="17:30"), "2026-10-15"
        )
        assert f["scheduled_hours"] == 9.0
        assert f["overtime_hours"] == 1.5
        assert f["daily_work_hours"] == 10.5

    def test_no_overtime(self, tmp_path):
        rows = minutes("2026-10-15 10:00", 60)
        f = day(
            build(tmp_path, rows, work_start="08:30", work_end="17:30"), "2026-10-15"
        )
        assert f["overtime_hours"] == 0
        assert f["daily_work_hours"] == 9.0

    def test_weekend_all_activity_is_overtime(self, tmp_path):
        rows = minutes("2026-10-17 12:00", 90)  # суббота, в часы графика
        f = day(
            build(tmp_path, rows, work_start="08:30", work_end="17:30"), "2026-10-17"
        )
        assert f["scheduled_hours"] == 0
        assert f["overtime_hours"] == 1.5
        assert f["daily_work_hours"] == 1.5

    def test_day_type(self, tmp_path):
        rows = minutes("2026-10-16 10:00", 10) + minutes("2026-10-17 10:00", 10)
        features = build(tmp_path, rows)
        assert day(features, "2026-10-16")["day_type"] == "Weekday"
        assert day(features, "2026-10-17")["day_type"] == "Weekend"


class TestSleep:
    def test_night_idle_is_sleep(self, tmp_path):
        rows = (
            minutes("2026-10-15 22:00", 60)  # до 22:59
            + minutes("2026-10-15 23:00", 480, active=False)  # до 06:59
            + minutes("2026-10-16 07:00", 10)
        )
        f = day(build(tmp_path, rows), "2026-10-16")
        assert f["sleep_hours"] == 8.0

    def test_tracker_gap_default_sleep(self, tmp_path):
        rows = minutes("2026-10-15 22:00", 60) + minutes("2026-10-16 07:00", 10)
        f = day(build(tmp_path, rows), "2026-10-16")
        assert f["sleep_hours"] == settings.SLEEP_DEFAULT_HOURS

    def test_too_long_idle_default_sleep(self, tmp_path):
        rows = (
            minutes("2026-10-15 10:00", 10)
            + minutes("2026-10-15 10:10", 20 * 60, active=False)
            + minutes("2026-10-16 06:10", 10)
        )
        f = day(build(tmp_path, rows), "2026-10-16")
        assert f["sleep_hours"] == settings.SLEEP_DEFAULT_HOURS

    def test_first_day_default_sleep(self, tmp_path, monkeypatch):
        monkeypatch.setattr(settings, "SLEEP_DEFAULT_HOURS", 7.5)
        f = day(build(tmp_path, minutes("2026-10-15 10:00", 10)), "2026-10-15")
        assert f["sleep_hours"] == 7.5


def test_save(tmp_path):
    builder = DailyFeatureBuilder(make_csv(tmp_path, minutes("2026-10-15 10:00", 10)))
    builder.process()
    out = builder.save(tmp_path / "out" / "features.csv")
    assert out.exists()
    assert len(pd.read_csv(out, encoding="utf-8-sig")) == 1


class TestSaveAccumulates:
    def save_user(self, tmp_path, out, user, days):
        rows = []
        for date in days:
            rows += minutes(f"{date} 10:00", 10)
        path = make_csv(tmp_path, rows, drop_user=True)
        builder = DailyFeatureBuilder(path, user=user)
        builder.process()
        builder.save(out)

    def test_other_users_kept(self, tmp_path):
        out = tmp_path / "features.csv"
        self.save_user(tmp_path, out, "Петров П.П.", ["2026-10-15", "2026-10-16"])
        self.save_user(tmp_path, out, "Иванов И.И.", ["2026-10-15"])

        saved = pd.read_csv(out, encoding="utf-8-sig")
        assert saved.groupby("user").size().to_dict() == {
            "Иванов И.И.": 1,
            "Петров П.П.": 2,
        }

    def test_same_user_replaced(self, tmp_path):
        out = tmp_path / "features.csv"
        self.save_user(tmp_path, out, "Иванов И.И.", ["2026-10-15", "2026-10-16"])
        self.save_user(tmp_path, out, "Петров П.П.", ["2026-10-15"])
        self.save_user(tmp_path, out, "Иванов И.И.", ["2026-10-19"])

        saved = pd.read_csv(out, encoding="utf-8-sig")
        ivan = saved[saved["user"] == "Иванов И.И."]
        assert ivan["date"].tolist() == ["2026-10-19"]
        assert (saved["user"] == "Петров П.П.").sum() == 1
