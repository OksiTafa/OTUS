"""Тесты объединения дневных признаков и анкет (app/models/data_merger.py)."""

import pandas as pd
import pytest

from app.models.data_merger import DataMerger, questionnaire_columns

SUBSCALES = ["emotional_exhaustion", "depersonalization", "personal_accomplishment"]


def feature_row(user, date, **values):
    row = {
        "user": user,
        "date": date,
        "day_type": "Weekday",
        "scheduled_hours": 9.0,
        "work_hours": 4.0,
        "screen_time_hours": 6.0,
        "meetings_count": 2,
        "breaks_taken": 3,
        "after_hours_work": 0,
        "sleep_hours": 8.0,
    }
    row.update(values)
    return row


def make_features_csv(tmp_path, rows=None):
    if rows is None:
        rows = [
            feature_row(
                "Иванов И.И.", "2026-10-01", work_hours=4.0, after_hours_work=1
            ),
            feature_row(
                "Иванов И.И.", "2026-10-02", work_hours=6.0, after_hours_work=0
            ),
            feature_row("Петров П.П.", "2026-10-01", work_hours=2.0),
        ]
    path = tmp_path / "features.csv"
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")
    return path


def questionnaire_row(full_name, burnout=0, **values):
    row = {
        "timestamp": "2026-10-08 10:00",
        "full_name": full_name,
        "Ваш возраст?": 35,
        "q1": 1,
        "emotional_exhaustion": 20,
        "depersonalization": 15,
        "personal_accomplishment": 25,
        "emotional_exhaustion_complete": True,
        "depersonalization_complete": True,
        "personal_accomplishment_complete": True,
        "emotional_exhaustion_level": "medium",
        "depersonalization_level": "medium",
        "personal_accomplishment_level": "high",
        "burnout": burnout,
        "mbi_level": "High" if burnout else "Medium",
    }
    row.update(values)
    return row


def make_questionnaire_csv(tmp_path, rows=None):
    if rows is None:
        rows = [
            questionnaire_row("Иванов И.И.", burnout=0),
            questionnaire_row("Петров П.П.", burnout=1, depersonalization=22),
        ]
    path = tmp_path / "mbi_results.csv"
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")
    return path


class TestLoad:
    def test_features_missing(self, tmp_path):
        merger = DataMerger(features_file=tmp_path / "missing.csv")
        with pytest.raises(FileNotFoundError, match="features"):
            merger.load_features()

    def test_features_without_user(self, tmp_path):
        path = tmp_path / "features.csv"
        pd.DataFrame([{"date": "2026-10-01", "work_hours": 1}]).to_csv(
            path, index=False
        )
        with pytest.raises(ValueError, match="user"):
            DataMerger(features_file=path).load_features()

    def test_questionnaire_missing(self, tmp_path):
        merger = DataMerger(questionnaire_file=tmp_path / "missing.csv")
        with pytest.raises(FileNotFoundError):
            merger.load_questionnaires()

    def test_questionnaire_without_full_name(self, tmp_path):
        path = make_questionnaire_csv(tmp_path)
        df = pd.read_csv(path, encoding="utf-8-sig").drop(columns=["full_name"])
        bad_path = tmp_path / "bad.csv"
        df.to_csv(bad_path, index=False, encoding="utf-8-sig")

        with pytest.raises(ValueError):
            DataMerger(questionnaire_file=bad_path).load_questionnaires()


class TestAggregate:
    def test_averages_per_user(self, tmp_path):
        merger = DataMerger(features_file=make_features_csv(tmp_path))
        rows = merger.aggregate().set_index("user")

        assert rows.loc["Иванов И.И.", "work_hours"] == pytest.approx(5.0)
        assert rows.loc["Иванов И.И.", "after_hours_work"] == pytest.approx(0.5)
        assert rows.loc["Петров П.П.", "work_hours"] == pytest.approx(2.0)
        assert rows.loc["Иванов И.И.", "scheduled_hours"] == pytest.approx(9.0)
        assert rows.loc["Иванов И.И.", "days_count"] == 2
        assert rows.loc["Петров П.П.", "days_count"] == 1
        assert "day_type" not in rows.columns

    def test_period(self, tmp_path):
        merger = DataMerger(features_file=make_features_csv(tmp_path))
        ivan = merger.aggregate().set_index("user").loc["Иванов И.И."]
        assert str(ivan["period_start"]) == "2026-10-01"
        assert str(ivan["period_end"]) == "2026-10-02"

    def test_window_keeps_last_days(self, tmp_path):
        rows = [
            feature_row("Иванов И.И.", "2026-10-01", work_hours=10.0),
            feature_row("Иванов И.И.", "2026-10-10", work_hours=2.0),
            feature_row("Иванов И.И.", "2026-10-11", work_hours=4.0),
        ]
        merger = DataMerger(
            features_file=make_features_csv(tmp_path, rows), window_days=7
        )
        ivan = merger.aggregate().set_index("user").loc["Иванов И.И."]
        assert ivan["days_count"] == 2
        assert ivan["work_hours"] == pytest.approx(3.0)

    def test_window_zero_keeps_all(self, tmp_path):
        rows = [
            feature_row("Иванов И.И.", "2026-09-01"),
            feature_row("Иванов И.И.", "2026-10-11"),
        ]
        merger = DataMerger(
            features_file=make_features_csv(tmp_path, rows), window_days=0
        )
        assert merger.aggregate().iloc[0]["days_count"] == 2


class TestMergeProcess:
    def make_merger(self, tmp_path, **kwargs):
        return DataMerger(
            features_file=make_features_csv(tmp_path, kwargs.get("features")),
            questionnaire_file=make_questionnaire_csv(tmp_path, kwargs.get("answers")),
        )

    def test_all_subscales_kept(self, tmp_path):
        merged = self.make_merger(tmp_path).process()
        for scale in SUBSCALES:
            assert scale in merged.columns
            assert f"{scale}_level" in merged.columns
            assert f"{scale}_complete" in merged.columns
        petrov = merged.set_index("user").loc["Петров П.П."]
        assert petrov["depersonalization"] == 22

    def test_columns_order(self, tmp_path):
        merged = self.make_merger(tmp_path).process()
        expected_start = ["user"] + questionnaire_columns()
        assert merged.columns.tolist()[: len(expected_start)] == expected_start

    def test_service_columns_dropped(self, tmp_path):
        merged = self.make_merger(tmp_path).process()
        assert not {"timestamp", "Ваш возраст?", "q1", "full_name"} & set(
            merged.columns
        )

    def test_merged_shape_and_keys(self, tmp_path):
        merged = self.make_merger(tmp_path).process()
        assert len(merged) == 2
        assert {"user", "burnout", "work_hours", "days_count"} <= set(merged.columns)
        assert set(merged["burnout"]) == {0, 1}

    def test_user_without_features(self, tmp_path):
        merger = self.make_merger(
            tmp_path,
            features=[feature_row("Петров П.П.", "2026-10-01")],
        )
        merged = merger.process()
        ivan = merged[merged["user"] == "Иванов И.И."].iloc[0]
        assert pd.isna(ivan["days_count"])
        assert pd.isna(ivan["work_hours"])
        assert ivan["emotional_exhaustion"] == 20

    def test_save_creates_file(self, tmp_path):
        merger = self.make_merger(tmp_path)
        merger.process()
        saved = merger.save(output_path=tmp_path / "out" / "merged.csv")

        assert saved.exists()
        assert len(pd.read_csv(saved, encoding="utf-8-sig")) == 2
