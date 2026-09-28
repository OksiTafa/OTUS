"""
Агрегатор всех метрик.
Собирает данные от SystemMetricsCollector и UserActivityTracker
в единый словарь для дальнейшей валидации и записи в CSV.
"""

from app.models.base_collector import BaseCollector
from app.models.system_metrics import SystemMetricsCollector
from app.models.user_activity import UserActivityTracker


class AggregatedCollector(BaseCollector):
    """Собирает все метрики через отдельные коллекторы."""

    def __init__(self):
        self.system = SystemMetricsCollector()
        self.activity = UserActivityTracker()

    def collect(self) -> dict:
        """Единый метод: объединяет метрики системы и активности пользователя."""
        self.metrics = {
            **self.system.collect(),
            **self.activity.collect(),
        }
        return self.metrics