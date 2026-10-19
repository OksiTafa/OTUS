"""Тесты классификатора процессов (app/models/process_classifier.py)."""

import pytest

from app.models.process_classifier import ProcessClassifier


@pytest.fixture
def classifier():
    return ProcessClassifier()


@pytest.mark.parametrize(
    "process_name, category",
    [
        ("Code.exe", "ide"),
        ("Zed.exe", "ide"),
        ("TOTALCMD64.EXE", "ide"),
        ("WindowsTerminal.exe", "ide"),
        ("Docker Desktop.exe", "ide"),
        ("dbeaver.exe", "db"),
        ("vivaldi.exe", "browser"),
        ("browser.exe", "browser"),
        ("claude.exe", "ai"),
        ("Teams.exe", "messenger"),
        ("app.exe", "messenger"),
    ],
)
def test_known_processes(classifier, process_name, category):
    assert classifier.classify(process_name) == category


def test_case_insensitive(classifier):
    assert classifier.classify("CODE.EXE") == classifier.classify("code.exe") == "ide"


@pytest.mark.parametrize("process_name", ["LockApp.exe", "EyeLeo.exe", "explorer.exe"])
def test_unknown_process_is_other(classifier, process_name):
    assert classifier.classify(process_name) == "other"


@pytest.mark.parametrize("process_name", ["", None])
def test_empty_process_is_unknown(classifier, process_name):
    assert classifier.classify(process_name) == "unknown"
