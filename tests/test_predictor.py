"""Тесты прогноза выгорания (app/models/predictor.py)."""

import numpy as np
import pandas as pd
import pytest

from app.models.model_trainer import BurnoutModelTrainer
from app.models.predictor import PREDICTION_TEXT, BurnoutPredictor
from tests.test_train_model import make_dataset

TIRED = "Усталов У.У."
RESTED = "Бодров Б.Б."


@pytest.fixture(scope="module")
def model_file(tmp_path_factory):
    """Один раз обучает модель на синтетическом датасете."""
    tmp = tmp_path_factory.mktemp("model")
    data_path = tmp / "developer_burnout.csv"
    make_dataset().to_csv(data_path, index=False)
    trainer = BurnoutModelTrainer(data_path, random_state=42)
    trainer.load().preprocess().train()
    return trainer.save(model_path=tmp / "model.pkl", output_dir=tmp / "out")


def feature_row(user, date, daily, screen, meetings, sleep):
    return {
        "user": user, "date": date, "day_type": "Weekday",
        "scheduled_hours": 9.0, "overtime_hours": daily - 9.0,
        "daily_work_hours": daily, "work_hours": screen / 2,
        "screen_time_hours": screen, "meetings_count": meetings,
        "breaks_taken": 3, "after_hours_work": int(daily > 9), "sleep_hours": sleep,
    }


def make_features(tmp_path):
    rows = [
        feature_row(TIRED, "2026-10-15", 13.5, 17.0, 9, 4.0),
        feature_row(TIRED, "2026-10-16", 13.0, 16.0, 8, 4.5),
        feature_row(RESTED, "2026-10-15", 4.5, 5.5, 0, 9.0),
    ]
    path = tmp_path / "features.csv"
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")
    return path


def make_questionnaire(tmp_path, rows=None):
    if rows is None:
        rows = [
            {"full_name": TIRED, "burnout": 1, "mbi_level": "High"},
            {"full_name": "Без Трекера", "burnout": 0, "mbi_level": "Low"},
        ]
    path = tmp_path / "mbi_results.csv"
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig")
    return path


def predict(tmp_path, model_file, questionnaire=True):
    predictor = BurnoutPredictor(
        model_file=model_file,
        features_file=make_features(tmp_path),
        questionnaire_file=(
            make_questionnaire(tmp_path) if questionnaire else tmp_path / "none.csv"
        ),
    )
    return predictor, predictor.process().set_index("user")


def test_model_missing(tmp_path):
    with pytest.raises(FileNotFoundError, match="train"):
        BurnoutPredictor(model_file=tmp_path / "missing.pkl").load_model()


class TestPredict:
    def test_probabilities(self, tmp_path, model_file):
        _, result = predict(tmp_path, model_file)
        probs = result[["prob_low", "prob_medium", "prob_high"]]
        assert np.allclose(probs.sum(axis=1), 1.0, atol=0.01)
        assert (probs >= 0).all().all()

    def test_predicted_level_is_argmax(self, tmp_path, model_file):
        _, result = predict(tmp_path, model_file)
        for user, row in result.iterrows():
            probs = {"Low": row["prob_low"], "Medium": row["prob_medium"],
                     "High": row["prob_high"]}
            assert row["predicted_level"] == max(probs, key=probs.get)
            assert row["prediction"] == PREDICTION_TEXT[row["predicted_level"]]

    def test_load_raises_risk(self, tmp_path, model_file):
        _, result = predict(tmp_path, model_file)
        assert result.loc[TIRED, "prob_high"] > result.loc[RESTED, "prob_high"]
        assert result.loc[RESTED, "prob_low"] > result.loc[TIRED, "prob_low"]

    def test_features_averaged(self, tmp_path, model_file):
        _, result = predict(tmp_path, model_file)
        assert result.loc[TIRED, "days_count"] == 2
        assert result.loc[TIRED, "daily_work_hours"] == pytest.approx(13.25)
        assert result.loc[TIRED, "screen_time"] == pytest.approx(16.5)


class TestCompareWithMBI:
    def test_match_with_questionnaire(self, tmp_path, model_file):
        _, result = predict(tmp_path, model_file)
        tired = result.loc[TIRED]
        assert tired["mbi_level"] == "High"
        assert tired["mbi_burnout"] == 1
        assert tired["match"] == (tired["predicted_level"] == "High")

    def test_user_without_questionnaire(self, tmp_path, model_file):
        _, result = predict(tmp_path, model_file)
        assert pd.isna(result.loc[RESTED, "mbi_level"])
        assert pd.isna(result.loc[RESTED, "match"])

    def test_questionnaire_only_users_skipped(self, tmp_path, model_file):
        _, result = predict(tmp_path, model_file)
        assert "Без Трекера" not in result.index

    def test_without_questionnaire_file(self, tmp_path, model_file):
        _, result = predict(tmp_path, model_file, questionnaire=False)
        assert len(result) == 2
        assert "mbi_level" not in result.columns
        assert "match" not in result.columns


def test_save(tmp_path, model_file):
    predictor, _ = predict(tmp_path, model_file)
    out = predictor.save(tmp_path / "out" / "predictions.csv")
    saved = pd.read_csv(out, encoding="utf-8-sig")
    assert set(saved["user"]) == {TIRED, RESTED}
    assert {"prob_low", "prob_medium", "prob_high", "predicted_level",
            "prediction", "mbi_level", "match"} <= set(saved.columns)
