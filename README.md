# Система прогнозирования профессионального выгорания на основе анализа цифровой активности пользователя

Итоговый проект курса OTUS «Python Developer. Basic».

Фоновый трекер собирает метрики работы за компьютером, из них считаются признаки за каждый день, а модель машинного обучения оценивает вероятность выгорания — низкую, среднюю или высокую. Анкета MBI (Maslach Burnout Inventory) служит проверкой прогноза.

## Как это работает

Работа разбита на шесть команд CLI, каждая берёт результат предыдущей:

| № | Команда | Что делает | Результат |
|---|---|---|---|
| 1 | `collect` | фоновый сбор метрик раз в минуту | `raw_data/metrics.csv` |
| 2 | `questionnaire` | обработка анкеты MBI из Google Forms | `data/questionnaire/mbi_results.csv` |
| 3 | `features` | дневные признаки из сырых метрик | `data/features.csv` |
| 4 | `merge` | средние признаки за период + анкета | `data/merged_data.csv` |
| 5 | `train` | обучение модели | `models_storage/burnout_model.pkl`, отчёты в `output/` |
| 6 | `predict` | вероятности Low / Medium / High и сравнение с MBI | `output/predictions.csv` |

## Требования

- Windows 10/11 — трекер использует WinAPI и имена процессов Windows.
- Python 3.12+ (проверено на 3.14).

## Установка

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

## Данные

| Что | Куда положить | Откуда |
|---|---|---|
| Ответы анкеты MBI | `data/questionnaire/answers.csv` | выгрузка CSV из Google Forms (первые 5 колонок — служебные: время, ФИО, возраст, пол, стаж; затем 15 вопросов) |
| Обучающий датасет | `data/developer_burnout_7000.zip` | Kaggle, Developer Burnout Dataset (7000 строк); ZIP распаковывать не нужно |
| Метрики трекера | `raw_data/metrics.csv` | создаёт команда `collect` или `BurnoutTracker.exe` |

Данные, модели и отчёты в репозиторий не входят (см. `.gitignore`).

## Использование

```bash
# 1. Сбор метрик (то же самое делает запуск без аргументов и BurnoutTracker.exe)
python main.py collect

# 2. Обработка анкеты
python main.py questionnaire [--file data/questionnaire/answers.csv]

# 3. Дневные признаки. Для файла без колонки user укажите ФИО,
#    для нестандартного графика — начало и конец рабочего дня
python main.py features [--tracker raw_data/metrics.csv] [--user "Иванов Иван Иванович"] [--work-start 08:30 --work-end 17:30]

# 4. Объединение признаков с анкетой
python main.py merge [--features data/features.csv] [--questionnaire data/questionnaire/mbi_results.csv]

# 5. Обучение модели
python main.py train [--file data/developer_burnout_7000.zip]

# 6. Прогноз
python main.py predict
```

Метрики каждого участника считаются отдельным запуском `features`: в `data/features.csv` заменяются только строки этого человека, признаки остальных сохраняются.

Связь метрик с анкетой — по ФИО: колонка `user` в метриках должна совпадать с полем «ФИО» в анкете. Трекер берёт имя из `USER_NAME` в `.env`, иначе из учётной записи Windows.

## Признаки

«Занятый» замер — пользователь активен или открыто окно звонка (во время звонка клавиатура и мышь простаивают). Экран блокировки (`LockApp.exe`) всегда считается простоем.

| Признак | Как считается |
|---|---|
| `daily_work_hours` | график работы + переработка (занятое время вне графика; в выходной — вся активность) |
| `work_hours` | занятое время в рабочих приложениях (IDE, API, БД, ИИ, мессенджеры) |
| `screen_time_hours` | всё занятое время |
| `meetings_count` | окна звонков от 5 минут (Zoom, Teams, окна с «Звонок» в заголовке) |
| `breaks_taken` | простои от 5 до 60 минут внутри дня |
| `after_hours_work` | 1, если вне графика занято не меньше 10 минут |
| `sleep_hours` | ночной простой до 12 ч; если измерить нельзя — 7 ч |

В модель входят `daily_work_hours`, `screen_time_hours`, `meetings_count` и `sleep_hours` — признаки, для которых есть аналоги в обучающем датасете.

## Модель и результаты

Модель обучается на открытом датасете Kaggle только на признаках, которые умеет считать трекер. Целевая переменная — `burnout_level` (Low / Medium / High). Сравниваются RandomForest и GradientBoosting с учётом дисбаланса классов, лучшая выбирается по F1-macro.

| Датасет | F1-macro | ROC-AUC |
|---|---|---|
| Work From Home Burnout (отклонён: риск задан долей выполненных задач, которую трекер не видит) | 0.33 | 0.48 |
| Developer Burnout 7000 | **0.59** | **0.78** |

Лучшая модель — GradientBoosting, высокий уровень выгорания распознаёт в 69 % случаев.

## Ограничения

- Обучающие датасеты синтетические: уровень выгорания в них задан через стресс, который трекер не измеряет.
- Реальная проверка проведена на одном участнике — это демонстрация подхода, а не оценка точности.
- Сон на рабочем компьютере не измеряется, используется значение по умолчанию.

## Настройки

Все параметры — в `config/settings.py`, каждый переопределяется в `.env` (пример — `.env.example`). Основные:

| Параметр | По умолчанию | Назначение |
|---|---|---|
| `COLLECTION_INTERVAL` | 60 | интервал сбора метрик, секунды |
| `DAYS_TO_COLLECT` | 14 | сколько дней работает трекер |
| `USER_NAME` | — | ФИО для колонки `user` в метриках |
| `WORK_DAY_START` / `WORK_DAY_END` | 08:30 / 17:30 | график работы |
| `SLEEP_DEFAULT_HOURS` | 7 | сон, если его нельзя измерить |
| `MERGE_WINDOW_DAYS` | 14 | за сколько последних дней усредняются признаки |
| `TRAIN_DATA_FILE` | `developer_burnout_7000.zip` | обучающий датасет в `data/` |

## Трекер в фоне

Сборка `.exe` без консольного окна:

```bash
python -m PyInstaller --onefile --noconsole --name BurnoutTracker main.py
```

Готовый файл — `dist/BurnoutTracker.exe`. Метрики и логи он пишет в папки `raw_data/` и `logs/` рядом с собой, `.env` читает оттуда же.

Автозапуск, способ 1 — папка автозагрузки:

1. `Win + R` → `shell:startup` → Enter.
2. Создать там ярлык на `BurnoutTracker.exe`.

Автозапуск, способ 2 — реестр:

```bash
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v BurnoutTracker /t REG_SZ /d "C:\путь\к\BurnoutTracker.exe"
```

Удаление из автозапуска:

```bash
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v BurnoutTracker
```

## Тесты

```bash
pytest
```

102 теста покрывают анкету, классификатор процессов, расчёт признаков, объединение данных, обучение и прогноз.

## Структура проекта

```
main.py                      CLI: команды collect … predict
config/settings.py           все параметры, переопределяются через .env
app/controllers/
    collector_controller.py  цикл сбора метрик и запись в CSV
app/models/
    aggregated_collector.py  объединение сборщиков метрик
    system_metrics.py        CPU и память (psutil)
    user_activity.py         активное окно и время простоя (WinAPI)
    process_classifier.py    категории процессов
    windows_user.py          имя пользователя Windows
    metrics.py               проверка замеров (pydantic)
    questionnaire.py         обработка анкеты MBI
    feature_builder.py       дневные признаки
    data_merger.py           объединение признаков с анкетой
    model_trainer.py         обучение модели
    predictor.py             прогноз
tests/                       тесты pytest
```
