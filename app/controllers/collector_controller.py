import csv
from datetime import datetime, timedelta
from pathlib import Path

import time

from config import settings
from app.models.base_collector import BaseCollector
from app.models.metrics import CollectedMetrics
from loguru import logger
from pydantic import ValidationError


class CollectorController:
    """
    Управляет процессом сбора данных:
    - Запуск/остановка цикла
    - Сохранение в CSV
    - Валидация через Pydantic
    - Логирование
    """

    def __init__(
            self,
            collector: BaseCollector,
            collection_interval: int = None,
            days_to_collect: int = None,
            metrics_file: str = None,
    ):
        self.collector = collector
        self.collection_interval = collection_interval or settings.COLLECTION_INTERVAL
        self.days_to_collect = days_to_collect or settings.DAYS_TO_COLLECT
        self.metrics_file = Path(metrics_file) if metrics_file else settings.METRICS_PATH

        # Схема колонок CSV из настроек
        self.FIELD_NAMES = settings.CSV_FIELD_NAMES

        self._running = False
        self._start_time = None

        # Настройка лог-файла
        log_file = settings.LOG_PATH
        log_file.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_file,
            rotation="1 day",
            retention="7 days",
            encoding="utf-8",
            level="INFO",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
        )

    #Валидация
    def _validate_metrics(self, metrics: dict) -> CollectedMetrics:
        """Проверяет корректность метрик через Pydantic."""
        try:
            return CollectedMetrics.model_validate(metrics)
        except ValidationError as e:
            logger.error(f"Ошибка валидации метрик: {e}")
            raise ValueError("Метрики не прошли валидацию") from e

    #CSV
    def _flatten_dict(self, d: dict, parent_key: str = "", sep: str = ".") -> dict:
        """Разворачивает вложенные словари в плоский dict."""
        items = {}
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.update(self._flatten_dict(v, new_key, sep=sep))
            else:
                items[new_key] = v
        return items

    def _save_metrics(self, metrics: dict):
        """Валидирует и записывает метрики в CSV."""
        validated = self._validate_metrics(metrics)

        row = self._flatten_dict(validated.model_dump())
        row["timestamp"] = datetime.now().isoformat()

        # Отбираем только известные поля
        filtered = {k: row.get(k, "") for k in self.FIELD_NAMES}

        # Создаём папку при необходимости
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)

        need_header = not self.metrics_file.exists() or self.metrics_file.stat().st_size == 0

        with open(self.metrics_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.FIELD_NAMES)
            if need_header:
                writer.writeheader()
            writer.writerow(filtered)

    #Цикл сбора данных
    def run(self):
        """Запускает цикл сбора данных."""
        self._running = True
        self._start_time = datetime.now()
        end_time = self._start_time + timedelta(days=self.days_to_collect)

        logger.info(
            f"Сбор данных запущен. Интервал: {self.collection_interval} сек, "
            f"дней сбора: {self.days_to_collect}"
        )
        logger.info(f"Данные будут сохраняться в: {self.metrics_file}")

        try:
            while self._running and datetime.now() < end_time:
                try:
                    metrics = self.collector.collect()
                    self._save_metrics(metrics)
                    logger.info("Итерация успешна. Запись сохранена.")
                except Exception as e:
                    logger.error(f"Ошибка при сборе данных: {e}")

                time.sleep(self.collection_interval)
        except Exception as e:
            logger.error(f"Критическая ошибка цикла: {e}")
        finally:
            self._running = False
            logger.info("Сбор данных остановлен.")

    def stop(self):
        """Останавливает цикл."""
        self._running = False
