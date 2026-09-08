# 📋 To-Do List: Burnout Prediction

## Этап 1: Структура проекта
- [x] Создать структуру папок (data/, models_storage/, output/)
- [ ] Проверить config/settings.py
- [x] Установить зависимости в requirements.txt

## Этап 2: Трекер метрик (data_collector.py)
- [х] Сбор CPU и RAM через psutil
- [ ] Определение активных процессов (IDE, браузеры, API, БД)
- [ ] Подсчёт времени в каждой категории
- [ ] Сбор Git-коммитов
- [ ] Запись данных в CSV
- [ ] Логирование в консоль
- [ ] Цикл сбора по COLLECTION_INTERVAL
- [ ] Остановка по DAYS_TO_COLLECT
- [ ] Тест на реальном компьютере

## Этап 2.5: Упаковка и установка
- [ ] Написать код для фонового режима (без окон)
- [ ] Собрать трекер в .exe (PyInstaller, Windows)
- [ ] Собрать для macOS (.app) и Linux (бинарник)
- [ ] Создать setup.exe (Inno Setup или свой скрипт)
- [ ] Настроить автозапуск (Startup / LaunchAgents / systemd)
- [ ] Добавить config.ini для гибкой настройки
- [ ] Протестировать на чистой машине без Python

## Этап 3: Обработка анкеты (questionnaire.py)
- [x] Создать Google Форму для анкеты
- [ ] Загрузка CSV из Google Forms
- [ ] Расчёт индекса MBI (3 субшкалы)
- [ ] Классификация результата
- [ ] Сохранение в data/questionnaire/

## Этап 4: Объединение данных (merge_data.py)
- [ ] Загрузка данных трекера
- [ ] Загрузка анкет
- [ ] Объединение по ФИО
- [ ] Нормализация признаков
- [ ] Обработка пропусков

## Этап 5: ML-модель (train_model.py)
- [x] Найти сырые данные для обучения модели
- [ ] Загрузка данных
- [ ] Разделение train/test
- [ ] RandomForestClassifier
- [ ] GradientBoostingClassifier
- [ ] Оценка (accuracy, F1, ROC-AUC)
- [ ] Confusion matrix
- [ ] Сохранение модели

## Этап 6: Анализ и визуализация (analyze.py)
- [ ] Корреляционная матрица
- [ ] Важность признаков
- [ ] Сравнение групп (boxplots)
- [ ] Сохранение графиков

## Этап 7: Главный модуль (main.py)
- [ ] CLI-интерфейс (argparse)
- [ ] Команды: collect, questionnaire, train, analyze
- [ ] Обработка ошибок

## Этап 8: Финальные штрихи
- [ ] README.md
- [ ] Пример данных (dummy)
- [ ] Полный цикл: collect → questionnaire → merge → train → analyze
