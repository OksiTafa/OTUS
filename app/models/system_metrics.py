import psutil


class SystemMetricsCollector:
    """
          Собирает метрики системы через psutil.

          Отвечает за получение данных о:
          - Загрузке CPU
          - Использовании RAM

          Эти метрики используются для анализа паттернов работы
          и последующего предсказания риска выгорания.
    """

    def __init__(self):
        self.metrics = {}
        # "Прогрев" - первый вызов вернёт 0.0
        psutil.cpu_percent(interval=None)

    def collect_cpu(self) -> float:
        # это вернёт среднюю загрузку за последние COLLECTION_INTERVAL сек
        return psutil.cpu_percent(interval=None)

    def collect_ram(self) -> dict:
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "used": memory.used,
            "available": memory.available,
            "percent": memory.percent,
            "free": memory.free,
        }