"""
Конфигурация проекта "Burnout Prediction"
Загружает настройки из .env, с стандартными значениями по умолчанию.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env (если он есть)
load_dotenv()



# ============================================
# Параметры трекера (из .env или стандартные)
# ============================================

# Интервал сбора метрик (в секундах)
COLLECTION_INTERVAL = int(os.getenv("COLLECTION_INTERVAL", 60))

# Сколько дней собирать данные
DAYS_TO_COLLECT = int(os.getenv("DAYS_TO_COLLECT", 14))

# Список процессов, которые считаются "активными" (для категоризации)
IDE_PROCESSES = [
    "code.exe",           # VS Code
    "pycharm64.exe",      # PyCharm
    "idea64.exe",         # IntelliJ IDEA
    "sublime_text.exe",   # Sublime Text
    "Far.exe",            # FAR Manager (для староверов 😄)
]

# Инструменты для работы с API
API_PROCESSES = [
    "postman.exe",        # Postman
    "insomnia.exe",       # Insomnia (альтернатива Postman)
    "swagger.exe",        # Swagger Editor
]

# Инструменты для работы с базами данных
DB_PROCESSES = [
    "dbeaver.exe",        # DBeaver
    "pgadmin.exe",        # pgAdmin (PostgreSQL)
    "sqlite3.exe",  # SQLite (встроенная БД)
    "sqlservr.exe",  # MS SQL Server (сервер)
    "ssms.exe",  # SQL Server Management Studio
    "mysqlworkbench.exe", # MySQL Workbench
    "datagrip64.exe",     # DataGrip (JetBrains)
    "navicat.exe",        # Navicat
]

# Браузеры
BROWSER_PROCESSES = [
    "chrome.exe",           # Google Chrome
    "firefox.exe",          # Mozilla Firefox
    "msedge.exe",           # Microsoft Edge
    "opera.exe",            # Opera
    "yandex.exe",           # Яндекс Браузер
    "vivaldi.exe",          # Vivaldi
]

# Инструменты для работы с сообщениями
MESSENGER_PROCESSES = [
    "Teams.exe",         # Microsoft Teams (замена Skype)
    "slack.exe",         # Slack (корпоративное общение)
    "telegram.exe",      # Telegram
    "whatsapp.exe",      # WhatsApp
    "discord.exe",       # Discord (голосовые каналы)
    "zoom.exe",          # Zoom (видеозвонки)
]

