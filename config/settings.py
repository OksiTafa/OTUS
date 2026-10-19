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
        "zed.exe",            # Zed
        "TOTALCMD64.EXE",     # Total Commander
        "WindowsTerminal.exe",  # Windows Terminal
        "Docker Desktop.exe",   # Docker Desktop
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
        "browser.exe",          # Яндекс Браузер
        "vivaldi.exe",          # Vivaldi
    ],
    "ai": [
        "claude.exe",        # Claude
    ],
    "messenger": [
        "Teams.exe",         # Microsoft Teams
        "slack.exe",         # Slack
        "telegram.exe",      # Telegram
        "whatsapp.exe",      # WhatsApp
        "discord.exe",       # Discord
        "zoom.exe",          # Zoom
        "app.exe",           # Корпоративные созвоны (hippo)
    ],
}

# Имя пользователя (ФИО), под которым работает трекер.
# Если не задано — берётся из учётной записи Windows (GetUserNameExW)
# или системный логин.
USER_NAME = os.getenv("USER_NAME", "")

# Список колонок для CSV-файла с метриками
CSV_FIELD_NAMES = [
    "user",
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

# Сколько служебных колонок в CSV ответов (время, возраст, ФИО, пол, стаж)
QUESTIONNAIRE_SKIP_COLUMNS = int(os.getenv("QUESTIONNAIRE_SKIP_COLUMNS", 5))

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

# Общий уровень выгорания по MBI (mbi_level) — для сравнения с прогнозом модели.
# Тяжесть субшкалы: 0/1/2 по уровню low/medium/high (для reversed-шкалы
# наоборот: high = 0, low = 2). Итог:
#   High   — burnout = 1 (сработало правило MBI_BURNOUT_RULES);
#   Medium — сумма тяжестей >= MBI_OVERALL_MEDIUM_SCORE;
#   Low    — иначе.
MBI_OVERALL_MEDIUM_SCORE = int(os.getenv("MBI_OVERALL_MEDIUM_SCORE", 2))

# Папка для результатов анкет
QUESTIONNAIRE_RESULTS_DIR = BASE_DIR / "data" / "questionnaire"

# CSV с ответами Google Forms (по умолчанию — выгруженный файл в data/questionnaire/)
QUESTIONNAIRE_FILE = BASE_DIR / "data" / "questionnaire" / os.getenv(
    "QUESTIONNAIRE_FILE", "answers.csv"
)

# Результаты обработки анкеты (полный цикл questionnaire)
QUESTIONNAIRE_RESULTS_FILE = BASE_DIR / "data" / "questionnaire" / "mbi_results.csv"

# ============================================
# Параметры расчёта дневных признаков (features)
# ============================================

# Дневные признаки из метрик трекера (команда features)
FEATURES_FILE = BASE_DIR / "data" / os.getenv("FEATURES_FILE", "features.csv")

# Границы рабочего дня (ЧЧ:ММ): активность вне [START, END) — after_hours_work.
# Для конкретного человека переопределяются в команде features
# (--work-start / --work-end)
WORK_DAY_START = os.getenv("WORK_DAY_START", "08:30")
WORK_DAY_END = os.getenv("WORK_DAY_END", "17:30")

# Работа вне рабочего дня засчитывается (after_hours_work = 1),
# если занятых минут вне графика не меньше порога
AFTER_HOURS_MIN_MINUTES = int(os.getenv("AFTER_HOURS_MIN_MINUTES", 10))

# Категории процессов, время в которых считается рабочим (work_hours)
WORK_CATEGORIES = ["ide", "api", "db", "ai", "messenger"]

# Процесс экрана блокировки: такие замеры всегда считаются бездействием
LOCK_SCREEN_PROCESS = "LockApp.exe"

# Звонки: процессы-звонилки и подстроки заголовка окна звонка.
# Во время звонка клавиатура и мышь простаивают (is_active = False),
# поэтому окно звонка считается занятым временем, а не перерывом.
CALL_PROCESSES = ["zoom.exe", "Teams.exe"]
CALL_WINDOW_KEYWORDS = ["звонок"]

# Перерыв — простой внутри рабочего дня длиной от MIN до MAX минут
BREAK_MIN_MINUTES = int(os.getenv("BREAK_MIN_MINUTES", 5))
BREAK_MAX_MINUTES = int(os.getenv("BREAK_MAX_MINUTES", 60))

# Встреча — отрезок звонка не короче MIN минут;
# отрезки с разрывом меньше MERGE_GAP минут склеиваются в одну встречу
MEETING_MIN_MINUTES = int(os.getenv("MEETING_MIN_MINUTES", 5))
MEETING_MERGE_GAP_MINUTES = int(os.getenv("MEETING_MERGE_GAP_MINUTES", 5))

# Сон — ночной простой перед первой активностью дня. Больше MAX часов
# (вечер без компьютера, выходные) или с разрывом в записи трекера — не считается (NaN)
SLEEP_MAX_HOURS = float(os.getenv("SLEEP_MAX_HOURS", 12))

# Сон по умолчанию — если ночной простой измерить нельзя
SLEEP_DEFAULT_HOURS = float(os.getenv("SLEEP_DEFAULT_HOURS", 7))

# ============================================
# Параметры объединения данных (merge)
# ============================================

# Файл с метриками трекера (вход команды features)
TRACKER_FILE = BASE_DIR / "raw_data" / os.getenv("TRACKER_FILE", "metrics.csv")

# Итоговый объединённый датасет
MERGED_FILE = BASE_DIR / "data" / os.getenv("MERGED_FILE", "merged_data.csv")

# За сколько последних дней данных каждого пользователя усредняются признаки
# (0 — за весь период)
MERGE_WINDOW_DAYS = int(os.getenv("MERGE_WINDOW_DAYS", 14))

# ============================================
# Параметры обучения ML-модели
# ============================================

# Обучающий датасет (Kaggle: developer_burnout_7000, CSV или ZIP с одним CSV)
TRAIN_DATA_FILE = BASE_DIR / "data" / os.getenv(
    "TRAIN_DATA_FILE", "developer_burnout_7000.zip"
)

# Классы целевой переменной burnout_level (от низкого риска к высокому)
BURNOUT_CLASSES = ["Low", "Medium", "High"]

# Доля тестовой выборки и random_state для воспроизводимости
TEST_SIZE = float(os.getenv("TEST_SIZE", 0.2))
RANDOM_STATE = int(os.getenv("RANDOM_STATE", 42))

# Папка и файл для сохранения обученной модели
MODELS_DIR = BASE_DIR / "models_storage"
MODEL_FILE = MODELS_DIR / os.getenv("MODEL_FILE", "burnout_model.pkl")

# Папка для отчётов обучения (метрики, confusion matrix)
OUTPUT_DIR = BASE_DIR / "output"

# Прогноз выгорания по данным трекера (команда predict)
PREDICTIONS_FILE = OUTPUT_DIR / os.getenv("PREDICTIONS_FILE", "predictions.csv")