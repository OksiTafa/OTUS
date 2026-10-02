"""
Конфигурация проекта "Burnout Prediction"
Загружает настройки из .env, с стандартными значениями по умолчанию.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env: рядом с exe (для сборки) или в рабочей папке
if getattr(sys, 'frozen', False):
    load_dotenv(Path(sys.executable).resolve().parent / ".env")
else:
    load_dotenv()


def get_app_dir() -> Path:
    """
    Определяет корневую папку приложения.
    Работает и для Python-скрипта, и для скомпилированного .exe.
    """
    try:
        if getattr(sys, 'frozen', False):
            # Режим .exe (PyInstaller): sys.executable - путь к exe
            return Path(sys.executable).resolve().parent
        elif os.getenv("OUTPUT_DIR"):
            return Path(os.getenv("OUTPUT_DIR"))
        else:
            return Path(__file__).resolve().parent.parent
    except Exception as e:
        return Path(__file__).resolve().parent.parent


# ============================================
# Параметры трекера (из .env или стандартные)
# ============================================

# Интервал сбора метрик (в секундах)
COLLECTION_INTERVAL = int(os.getenv("COLLECTION_INTERVAL", 60))

# Сколько дней собирать данные
DAYS_TO_COLLECT = int(os.getenv("DAYS_TO_COLLECT", 14))

# Путь для сохранения данных
BASE_DIR = get_app_dir()      #корень проекта
RAW_DATA_DIR = BASE_DIR /"raw_data"
LOG_DIR = BASE_DIR /"logs"

# Имена файлов (можно переопределить через .env)
METRICS_FILE = os.getenv("METRICS_FILE", "metrics.csv")
LOG_FILE = os.getenv("LOG_FILE", "logs.csv")

# Полные пути к файлам
METRICS_PATH = RAW_DATA_DIR / METRICS_FILE
LOG_PATH = LOG_DIR / LOG_FILE

# Список процессов, которые считаются "активными" (для категоризации)
PROCESS_CATEGORIES = {
    "ide": [
        "code.exe",           # VS Code
        "pycharm64.exe",      # PyCharm
        "idea64.exe",         # IntelliJ IDEA
        "sublime_text.exe",   # Sublime Text
        "Far.exe",            # FAR Manager
    ],
    "api": [
        "postman.exe",        # Postman
        "insomnia.exe",       # Insomnia
        "swagger.exe",        # Swagger Editor
    ],
    "db": [
        "dbeaver.exe",        # DBeaver
        "pgadmin.exe",        # pgAdmin
        "sqlite3.exe",        # SQLite
        "sqlservr.exe",       # MS SQL Server
        "ssms.exe",           # SSMS
        "mysqlworkbench.exe", # MySQL Workbench
        "datagrip64.exe",     # DataGrip
        "navicat.exe",        # Navicat
    ],
    "browser": [
        "chrome.exe",           # Google Chrome
        "firefox.exe",          # Mozilla Firefox
        "msedge.exe",           # Microsoft Edge
        "opera.exe",            # Opera
        "yandex.exe",           # Яндекс Браузер
        "vivaldi.exe",          # Vivaldi
    ],
    "messenger": [
        "Teams.exe",         # Microsoft Teams
        "slack.exe",         # Slack
        "telegram.exe",      # Telegram
        "whatsapp.exe",      # WhatsApp
        "discord.exe",       # Discord
        "zoom.exe",          # Zoom
    ],
}

# Список колонок для CSV-файла с метриками
CSV_FIELD_NAMES = [
    "timestamp",
    "window.window_title",
    "window.process_name",
    "window.pid",
    "activity.idle_seconds",
    "activity.state",
    "activity.is_active",
    "cpu",
    "ram.total",
    "ram.used",
    "ram.available",
    "ram.percent",
    "ram.free",
]

# ============================================
# Параметры анкеты MBI
# ============================================

# Сколько служебных колонок в CSV ответов (время + ФИО/почта)
QUESTIONNAIRE_SKIP_COLUMNS = int(os.getenv("QUESTIONNAIRE_SKIP_COLUMNS", 2))

# Количество вопросов в анкете MBI
# (сокращённый вариант для IT-специалистов: по 5 вопросов на каждую субшкалу)
QUESTIONNAIRE_ITEMS_COUNT = int(os.getenv("QUESTIONNAIRE_ITEMS_COUNT", 15))

# Максимальный балл одного вопроса (шкала частоты 0..6)
MBI_MAX_ITEM_SCORE = int(os.getenv("MBI_MAX_ITEM_SCORE", 6))

# Соответствие субшкал номерам вопросов (нумерация с 1)
# reversed=True означает: чем выше сырой балл, тем ЛУЧШЕ состояние
# (обратное направление относительно выгорания).
MBI_SUBSCALES = {
    "emotional_exhaustion": {
        "items": [1, 2, 3, 4, 5],
        "reversed": False,
    },
    "depersonalization": {
        "items": [6, 7, 8, 9, 10],
        "reversed": False,
    },
    "personal_accomplishment": {
        "items": [11, 12, 13, 14, 15],
        "reversed": True,
    },
}

# Пороги уровней для сокращённого варианта MBI (макс. по субшкале = 30)
# Это начала диапазонов: low / medium / high.
#   ЭИ:   0-10 низкий,  11-20 средний,  21-30 высокий
#   Д:    0-8  низкий,  9-18  средний,  19-30 высокий
#   РА:   0-12 низкий (выгорание), 13-21 средний, 22-30 высокий (хорошо)
# Для ЭИ и Д: чем больше баллов, тем сильнее выгорание.
# Для РА: шкала обратная — чем больше баллов, тем лучше достижения.
MBI_THRESHOLDS = {
    "emotional_exhaustion": {"low": 0, "medium": 11, "high": 21},
    "depersonalization": {"low": 0, "medium": 9, "high": 19},
    "personal_accomplishment": {"low": 0, "medium": 13, "high": 22},
}

# Правило определения выгорания (целевая переменная для ML):
# выгорание = 1, если ЭИ >= 21 ИЛИ Д >= 19 ИЛИ РА <= 12.
MBI_BURNOUT_RULES = {
    "emotional_exhaustion": ">= high",
    "depersonalization": ">= high",
    "personal_accomplishment": "< medium",
}

# Папка для результатов анкет
QUESTIONNAIRE_RESULTS_DIR = BASE_DIR / "data" / "questionnaire"