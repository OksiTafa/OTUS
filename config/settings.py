"""
Конфигурация проекта "Burnout Prediction"
Загружает настройки из .env, с стандартными значениями по умолчанию.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env (если он есть)
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