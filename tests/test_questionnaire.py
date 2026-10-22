"""Тесты обработки анкеты MBI (app/models/questionnaire.py)."""

import pandas as pd
import pytest

from app.models.questionnaire import MBIQuestionnaireProcessor

SERVICE_HEADER = [
    "Отметка времени",
    "Ваш возраст?",
    "ФИО",
    "Ваш пол?",
    "Стаж работы в годах?",
]
ITEMS_HEADER = [f"q{i}" for i in range(1, 16)]


def make_csv(tmp_path, rows, name="answers.csv"):
    header = SERVICE_HEADER + ITEMS_HEADER
    path = tmp_path / name
    lines = [",".join(header)]
    lines.extend(",".join(row) for row in rows)
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def answers_row(values):
    return ["2026-10-08 10:00:00", "35", "Иванов И.И.", "Женский", "10"] + values


class TestLoad:
    def test_file_not_found(self, tmp_path):
        processor = MBIQuestionnaireProcessor(tmp_path / "missing.csv")
        with pytest.raises(FileNotFoundError):
            processor.load()

    def test_text_labels_converted(self, tmp_path):
        row = answers_row(["никогда"] * 5 + ["редко"] * 5 + ["каждый день"] * 5)
        path = make_csv(tmp_path, [row])

        processor = MBIQuestionnaireProcessor(path).load()

        assert processor._answers.shape == (1, 15)
        assert processor._answers.iloc[0, 0] == 0
        assert processor._answers.iloc[0, 5] == 2
        assert processor._answers.iloc[0, 14] == 6

    def test_numeric_answers_accepted(self, tmp_path):
        row = answers_row([str(i) for i in range(15)])
        path = make_csv(tmp_path, [row])

        processor = MBIQuestionnaireProcessor(path).load()

        assert processor._answers.iloc[0].tolist() == list(range(15))

    def test_empty_answer_becomes_nan(self, tmp_path):
        row = answers_row([""] + ["никогда"] * 14)
        path = make_csv(tmp_path, [row])

        processor = MBIQuestionnaireProcessor(path).load()

        assert pd.isna(processor._answers.iloc[0, 0])

    def test_too_few_columns(self, tmp_path):
        path = make_csv(tmp_path, [answers_row(["никогда"] * 15)])
        processor = MBIQuestionnaireProcessor(path, items_count=20)
        with pytest.raises(ValueError):
            processor.load()


class TestComputeMBI:
    def test_subscale_sums(self, tmp_path):
        row = answers_row(["часто"] * 5 + ["иногда"] * 5 + ["очень редко"] * 5)
        path = make_csv(tmp_path, [row])

        scores = MBIQuestionnaireProcessor(path).compute_mbi()

        assert scores["emotional_exhaustion"].iloc[0] == 20
        assert scores["depersonalization"].iloc[0] == 15
        assert scores["personal_accomplishment"].iloc[0] == 5

    def test_complete_flags(self, tmp_path):
        row = answers_row(["часто"] * 4 + [""] + ["никогда"] * 10)
        path = make_csv(tmp_path, [row])

        scores = MBIQuestionnaireProcessor(path).compute_mbi()

        assert not scores["emotional_exhaustion_complete"].iloc[0]
        assert bool(scores["depersonalization_complete"].iloc[0])


class TestClassify:
    def make_processor(self, tmp_path, row):
        path = make_csv(tmp_path, [row])
        processor = MBIQuestionnaireProcessor(path)
        processor.process()
        return processor

    def test_burnout_case(self, tmp_path):
        # ЭИ=30 (high), Д=20 (high), РА=0 (< medium) → выгорание
        processor = self.make_processor(
            tmp_path,
            answers_row(["каждый день"] * 5 + ["часто"] * 5 + ["никогда"] * 5),
        )
        levels = processor.levels

        assert levels["emotional_exhaustion_level"].iloc[0] == "high"
        assert levels["depersonalization_level"].iloc[0] == "high"
        assert levels["personal_accomplishment_level"].iloc[0] == "low"
        assert levels["burnout"].iloc[0] == 1
        assert levels["mbi_level"].iloc[0] == "High"

    def test_healthy_case(self, tmp_path):
        # ЭИ=0, Д=0, РА=30 → нет выгорания
        processor = self.make_processor(
            tmp_path,
            answers_row(["никогда"] * 5 + ["никогда"] * 5 + ["каждый день"] * 5),
        )
        levels = processor.levels

        assert levels["burnout"].iloc[0] == 0
        assert levels["mbi_level"].iloc[0] == "Low"

    def test_medium_thresholds(self, tmp_path):
        # ЭИ=5+5+5+4+4=23? нет: часто=4 → 5*4=20 (medium), Д=5*2=10 (medium),
        # РА=5*3=15 (medium) → нет выгорания
        processor = self.make_processor(
            tmp_path,
            answers_row(["часто"] * 5 + ["редко"] * 5 + ["иногда"] * 5),
        )
        levels = processor.levels

        assert levels["emotional_exhaustion_level"].iloc[0] == "medium"
        assert levels["depersonalization_level"].iloc[0] == "medium"
        assert levels["personal_accomplishment_level"].iloc[0] == "medium"
        assert levels["burnout"].iloc[0] == 0
        assert levels["mbi_level"].iloc[0] == "Medium"

    def test_single_medium_subscale_is_low(self, tmp_path):
        # ЭИ=15 (medium, тяжесть 1), Д=0 (low), РА=30 (high → тяжесть 0) → сумма 1
        processor = self.make_processor(
            tmp_path,
            answers_row(["иногда"] * 5 + ["никогда"] * 5 + ["каждый день"] * 5),
        )
        assert processor.levels["mbi_level"].iloc[0] == "Low"

    def test_reversed_scale_severity(self, tmp_path):
        # ЭИ=0, Д=0, РА=15 (medium → тяжесть 1) + Д=10 (medium) → сумма 2
        processor = self.make_processor(
            tmp_path,
            answers_row(["никогда"] * 5 + ["редко"] * 5 + ["иногда"] * 5),
        )
        assert processor.levels["burnout"].iloc[0] == 0
        assert processor.levels["mbi_level"].iloc[0] == "Medium"


class TestProcessAndSave:
    def test_results_structure_and_save(self, tmp_path):
        row = answers_row(["никогда"] * 15)
        path = make_csv(tmp_path, [row])

        out_dir = tmp_path / "out"
        processor = MBIQuestionnaireProcessor(path)
        processor.save(output_dir=out_dir)

        result = pd.read_csv(out_dir / "mbi_results.csv", encoding="utf-8-sig")
        assert list(result["full_name"]) == ["Иванов И.И."]
        assert "burnout" in result.columns
        assert "emotional_exhaustion" in result.columns
