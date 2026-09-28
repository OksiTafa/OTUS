from config.settings import PROCESS_CATEGORIES


class ProcessClassifier:
    """
    Классифицирует процессы по категориям.
    Определяет, чем занимается пользователь.
    """
    def classify(self, process_name: str) -> str:
        if not process_name:
            return "unknown"

        process_name = process_name.lower()

        for category, processes in PROCESS_CATEGORIES.items():
            if process_name in [p.lower() for p in processes]:
                return category

        return "other"
