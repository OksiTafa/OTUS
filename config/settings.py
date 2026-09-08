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
            return Path(__file__).resolve().parent
    except Exception as e:
        return Path(__file__).resolve().parent


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

# Путь к файлу с данными
DATA_FILE = "metrics.csv"

# Список процессов, которые считаются "активными" (для категоризации)
IDE_PROCESSES = [
    "code.exe",  # VS Code
    "pycharm64.exe",  # PyCharm
    "idea64.exe",  # IntelliJ IDEA
    "sublime_text.exe",  # Sublime Text
    "Far.exe",  # FAR Manager (для староверов 😄)
]

# Инструменты для работы с API
API_PROCESSES = [
    "postman.exe",  # Postman
    "insomnia.exe",  # Insomnia (альтернатива Postman)
    "swagger.exe",  # Swagger Editor
]

# Инструменты для работы с базами данных
DB_PROCESSES = [
    "dbeaver.exe",  # DBeaver
    "pgadmin.exe",  # pgAdmin (PostgreSQL)
    "sqlite3.exe",  # SQLite (встроенная БД)
    "sqlservr.exe",  # MS SQL Server (сервер)
    "ssms.exe",  # SQL Server Management Studio
    "mysqlworkbench.exe",  # MySQL Workbench
    "datagrip64.exe",  # DataGrip (JetBrains)
    "navicat.exe",  # Navicat
]

# Браузеры
BROWSER_PROCESSES = [
    "chrome.exe",  # Google Chrome
    "firefox.exe",  # Mozilla Firefox
    "msedge.exe",  # Microsoft Edge
    "opera.exe",  # Opera
    "yandex.exe",  # Яндекс Браузер
    "vivaldi.exe",  # Vivaldi
]

# Инструменты для работы с сообщениями
MESSENGER_PROCESSES = [
    "Teams.exe",  # Microsoft Teams (замена Skype)
    "slack.exe",  # Slack (корпоративное общение)
    "telegram.exe",  # Telegram
    "whatsapp.exe",  # WhatsApp
    "discord.exe",  # Discord (голосовые каналы)
    "zoom.exe",  # Zoom (видеозвонки)
]
