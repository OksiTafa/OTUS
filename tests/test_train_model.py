"""Тесты обучения ML-модели (app/models/model_trainer.py)."""

import zipfile

import joblib
import numpy as np
import pandas as pd
import pytest

from app.models.model_trainer import (
    MODEL_FEATURES,
    BurnoutModelTrainer,
    prepare_features,
)


def make_dataset(n: int = 900) -> pd.DataFrame:
    """Синтетический датасет со схемой developer_burnout_7000."""
    rng = np.random.default_rng(42)
    work = rng.uniform(4, 14, n)
    screen = (work + rng.normal(3, 1.5, n)).clip(5, 19)
    meetings = rng.integers(0, 10, n)
    sleep = rng.uniform(4, 9, n)
    stress = (6 * work + 2 * screen + 3 * meetings - 4 * sleep + rng.normal(0, 8, n))
    stress = 100 * (stress - stress.min()) / (stress.max() - stress.min())
    level = np.where(stress >= 70, "High", np.where(stress >= 35, "Medium", "Low"))

    df = pd.DataFrame({
        "age": rng.integers(20, 45, n),
        "experience_years": rng.integers(0, 20, n),
        "daily_work_hours": work.round(2),
        "sleep_hours": sleep.round(2),
        "caffeine_intake": rng.integers(0, 8, n),
        "bugs_per_day": rng.integers(0, 20, n),
        "commits_per_day": rng.integers(0, 30, n),
        "meetings_per_day": meetings,
        "screen_time": screen.round(2),
        "exercise_hours": rng.uniform(0, 2, n).round(2),
        "stress_level": stress.round(2),
        "burnout_level": level,
    })
    # Пропуски, как в реальном датасете
    df.loc[rng.random(n) < 0.02, "sleep_hours"] = np.nan
    df.loc[rng.random(n) < 0.02, "burnout_level"] = np.nan
    return df


@pytest.fixture(scope="module")
def trained(tmp_path_factory):
    """Один раз обучает модель на синтетическом датасете для всех тестов."""
    tmp = tmp_path_factory.mktemp("train_data")
    data_path = tmp / "developer_burnout.csv"
    make_dataset().to_csv(data_path, index=False)

    trainer = BurnoutModelTrainer(data_path, test_size=0.25, random_state=42)
    trainer.load().preprocess().train()
    return trainer, tmp


class TestLoad:
    def test_file_not_found(self, tmp_path):
        trainer = BurnoutModelTrainer(tmp_path / "missing.csv")
        with pytest.raises(FileNotFoundError):
            trainer.load()

    def test_missing_columns(self, tmp_path):
        path = tmp_path / "bad.csv"
        make_dataset(20).drop(columns=["screen_time"]).to_csv(path, index=False)
        with pytest.raises(ValueError, match="screen_time"):
            BurnoutModelTrainer(path).load()

    def test_unknown_class(self, tmp_path):
        df = make_dataset(20)
        df.loc[0, "burnout_level"] = "Extreme"
        path = tmp_path / "bad.csv"
        df.to_csv(path, index=False)
        with pytest.raises(ValueError, match="Extreme"):
            BurnoutModelTrainer(path).load()

    def test_reads_zip(self, tmp_path):
        csv_path = tmp_path / "developer_burnout_dataset_7000.csv"
        make_dataset(20).to_csv(csv_path, index=False)
        zip_path = tmp_path / "developer_burnout_7000.zip"
        with zipfile.ZipFile(zip_path, "w") as zf:
            zf.write(csv_path, csv_path.name)

        trainer = BurnoutModelTrainer(zip_path).load()
        assert len(trainer.data) == 20


class TestPrepareFeatures:
    def test_dataset_columns(self):
        X = prepare_features(make_dataset(10))
        assert list(X.columns) == MODEL_FEATURES

    def test_tracker_columns_renamed(self):
        tracker = pd.DataFrame([{
            "user": "Иванов И.И.", "date": "2026-10-15", "day_type": "Weekday",
            "scheduled_hours": 9.0, "overtime_hours": 0.5, "daily_work_hours": 9.5,
            "work_hours": 4.0, "screen_time_hours": 6.0,
            "meetings_count": 2, "breaks_taken": 3, "after_hours_work": 1,
            "sleep_hours": 7.0,
        }])
        X = prepare_features(tracker)
        assert list(X.columns) == MODEL_FEATURES
        assert X.iloc[0].to_dict() == {
            "daily_work_hours": 9.5, "screen_time": 6.0,
            "meetings_per_day": 2, "sleep_hours": 7.0,
        }

    def test_missing_feature(self):
        with pytest.raises(ValueError, match="screen_time"):
            prepare_features(pd.DataFrame([{"daily_work_hours": 9, "sleep_hours": 7,
                                            "meetings_count": 1}]))


class TestPreprocess:
    def test_only_tracker_features(self, trained):
        trainer, _ = trained
        assert list(trainer.X.columns) == MODEL_FEATURES
        assert "stress_level" not in trainer.X.columns

    def test_rows_without_target_dropped(self, trained):
        trainer, _ = trained
        assert trainer.y.notna().all()
        assert len(trainer.y) == trainer.data["burnout_level"].notna().sum()

    def test_split_shapes(self, trained):
        trainer, _ = trained
        assert len(trainer.X_train) == len(trainer.y_train)
        assert len(trainer.X_test) == len(trainer.y_test)
        assert set(trainer.y_test.unique()) == {"Low", "Medium", "High"}


class TestTrain:
    def test_both_models_trained(self, trained):
        trainer, _ = trained

        assert set(trainer.models) == {"random_forest", "gradient_boosting"}
        for m in trainer.metrics.values():
            for key in ("accuracy", "f1_macro", "roc_auc",
                        "recall_low", "recall_medium", "recall_high"):
                assert 0.0 <= m[key] <= 1.0
            assert len(m["confusion_matrix"]) == 3

    def test_best_model_by_f1_macro(self, trained):
        trainer, _ = trained

        best = max(trainer.metrics, key=lambda n: trainer.metrics[n]["f1_macro"])
        assert trainer.best_model_name == best
        assert trainer.best_model is not None

    def test_predict_proba_three_classes(self, trained):
        trainer, _ = trained
        X = pd.DataFrame(
            trainer.imputer.transform(trainer.X_test), columns=MODEL_FEATURES
        )
        proba = trainer.best_model.predict_proba(X)
        assert proba.shape[1] == 3
        assert np.allclose(proba.sum(axis=1), 1.0)

    def test_learns_signal(self, trained):
        trainer, _ = trained
        assert trainer.metrics[trainer.best_model_name]["f1_macro"] > 0.5


class TestSave:
    def test_save_model_and_report(self, trained):
        trainer, tmp = trained

        model_path = tmp / "models" / "model.pkl"
        out_dir = tmp / "output"
        trainer.save(model_path=model_path, output_dir=out_dir)

        assert model_path.exists()
        bundle = joblib.load(model_path)
        assert bundle["model_name"] == trainer.best_model_name
        assert bundle["feature_columns"] == MODEL_FEATURES
        assert bundle["classes"] == ["Low", "Medium", "High"]
        assert "imputer" in bundle

        report = pd.read_csv(out_dir / "train_metrics.csv", encoding="utf-8-sig")
        assert set(report["model"]) == {"random_forest", "gradient_boosting"}
        assert {"f1_macro", "roc_auc", "recall_high"} <= set(report.columns)
        assert report["is_best"].sum() == 1

        matrix = (out_dir / "confusion_matrix_random_forest.txt").read_text(encoding="utf-8")
        assert "true_High" in matrix and "pred_Low" in matrix
        assert (out_dir / "confusion_matrix_gradient_boosting.txt").exists()
