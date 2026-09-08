from app.models.metrics_collector import MetricCollector

class CollectorController:
    """
    Управляет процессом сбора данных:
    - Запуск/остановка цикла
    - Сохранение в CSV
    - Логирование
    - Обработка ошибок
    """

    def __init__(self, collector: MetricCollector):
        self.collector = collector
        self