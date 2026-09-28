"""
Базовый класс для всех коллекторов метрик.
Определяет единый интерфейс сбора данных.
"""

from abc import ABC, abstractmethod


class BaseCollector(ABC):
    """Базовый класс для всех коллекторов метрик."""

    def __init__(self):
        self.metrics = {}

    @abstractmethod
    def collect(self) -> dict:
        """
        Собирает метрики и возвращает словарь.
        Каждый наследник реализует свою логику сбора метрик.
        """
        pass

    def get_metrics(self) -> dict:
        """Возвращает словарь с метриками."""
        return self.metrics

    def reset(self):
        """Очищаюет собранные метрики"""
        self.metrics = {}