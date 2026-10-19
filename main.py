"""Главный модуль: CLI-интерфейс (argparse).

Команды:
    collect       — сбор метрик цифровой активности (по умолчанию)
    questionnaire — обработка анкеты MBI
    features      — расчёт дневных признаков из метрик трекера
    train         — обучение ML-модели
    merge         — объединение дневных признаков с анкетами
    predict       — прогноз выгорания по признакам трекера
    analyze       — анализ и визуализация (будет добавлена)
"""

import argparse

from loguru import logger

from app.controllers.collector_controller import CollectorController
from app.models.aggregated_collector import AggregatedCollector
from app.models.data_merger import DataMerger
from app.models.feature_builder import DailyFeatureBuilder
from app.models.model_trainer import BurnoutModelTrainer
from app.models.predictor import BurnoutPredictor
from app.models.questionnaire import MBIQuestionnaireProcessor
from config import settings


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="burnout",
        description="Система прогнозирования профессионального выгорания",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("collect", help="Сбор метрик цифровой активности")

    questionnaire_parser = subparsers.add_parser(
        "questionnaire", help="Обработка анкеты MBI"
    )
    questionnaire_parser.add_argument(
        "--file",
        help="CSV с ответами Google Forms "
             "(по умолчанию data/questionnaire/answers.csv)",
    )

    features_parser = subparsers.add_parser(
        "features", help="Расчёт дневных признаков из метрик трекера"
    )
    features_parser.add_argument(
        "--tracker",
        help="CSV метрик трекера (по умолчанию raw_data/metrics.csv)",
    )
    features_parser.add_argument(
        "--user",
        help="ФИО для метрик без колонки user (по умолчанию USER_NAME из .env)",
    )
    features_parser.add_argument(
        "--work-start",
        help="Начало рабочего дня ЧЧ:ММ (по умолчанию WORK_DAY_START, 08:30)",
    )
    features_parser.add_argument(
        "--work-end",
        help="Конец рабочего дня ЧЧ:ММ (по умолчанию WORK_DAY_END, 17:30)",
    )

    train_parser = subparsers.add_parser(
        "train", help="Обучение ML-модели прогнозирования выгорания"
    )
    train_parser.add_argument(
        "--file",
        help="CSV с обучающим датасетом "
             "(по умолчанию data/developer_burnout_7000.zip)",
    )

    merge_parser = subparsers.add_parser(
        "merge", help="Объединение дневных признаков с результатами анкет"
    )
    merge_parser.add_argument(
        "--features",
        help="CSV дневных признаков (по умолчанию data/features.csv)",
    )
    merge_parser.add_argument(
        "--questionnaire",
        help="CSV результатов анкеты (по умолчанию data/questionnaire/mbi_results.csv)",
    )

    predict_parser = subparsers.add_parser(
        "predict", help="Прогноз выгорания по признакам трекера"
    )
    predict_parser.add_argument(
        "--features",
        help="CSV дневных признаков (по умолчанию data/features.csv)",
    )
    predict_parser.add_argument(
        "--questionnaire",
        help="CSV результатов анкеты (по умолчанию data/questionnaire/mbi_results.csv)",
    )

    return parser


def run_collect() -> None:
    """Запускает сбор метрик цифровой активности (фоновая команда)."""
    controller = CollectorController(AggregatedCollector())
    controller.run()


def run_questionnaire(file_path=None) -> None:
    """Обрабатывает анкету MBI.

    :param file_path: путь к CSV с ответами Google Forms
        (по умолчанию data/questionnaire/answers.csv).
    """
    path = file_path or settings.QUESTIONNAIRE_FILE
    processor = MBIQuestionnaireProcessor(path)
    results = processor.process()
    out_path = processor.save()

    logger.info(f"Обработано анкет: {len(results)}")
    logger.info(
        f"Выгорание (burnout=1): {int(results['burnout'].sum())} из {len(results)}"
    )
    logger.success(f"Готово: {out_path}")


def run_features(tracker_file=None, user=None, work_start=None, work_end=None) -> None:
    """Считает дневные признаки из метрик трекера.

    :param tracker_file: путь к CSV метрик трекера
        (по умолчанию raw_data/metrics.csv)
    :param user: ФИО для метрик без колонки user
    :param work_start: начало рабочего дня ЧЧ:ММ
    :param work_end: конец рабочего дня ЧЧ:ММ
    """
    builder = DailyFeatureBuilder(
        tracker_file=tracker_file,
        user=user,
        work_start=work_start,
        work_end=work_end,
    )
    features = builder.process()
    out_path = builder.save()

    logger.info(f"Дней с активностью: {len(features)}")
    logger.success(f"Готово: {out_path}")


def run_train(file_path=None) -> None:
    """Обучает ML-модель на developer_burnout_7000 (мультикласс Low/Medium/High).

    :param file_path: путь к датасету
        (по умолчанию data/developer_burnout_7000.zip).
    """
    trainer = BurnoutModelTrainer(file_path)
    trainer.load().preprocess().train()
    trainer.save()


def run_merge(features_file=None, questionnaire_file=None) -> None:
    """Объединяет дневные признаки трекера с результатами анкет.

    :param features_file: путь к CSV дневных признаков
        (по умолчанию data/features.csv)
    :param questionnaire_file: путь к CSV анкеты
        (по умолчанию data/questionnaire/mbi_results.csv)
    """
    merger = DataMerger(
        features_file=features_file,
        questionnaire_file=questionnaire_file,
    )
    merged = merger.process()
    out_path = merger.save()

    logger.info(f"Объединено записей: {len(merged)}")
    logger.success(f"Датасет сохранён: {out_path}")


def run_predict(features_file=None, questionnaire_file=None) -> None:
    """Прогнозирует выгорание по признакам трекера и сравнивает с анкетой MBI.

    :param features_file: путь к CSV дневных признаков
        (по умолчанию data/features.csv)
    :param questionnaire_file: путь к CSV анкеты
        (по умолчанию data/questionnaire/mbi_results.csv)
    """
    predictor = BurnoutPredictor(
        features_file=features_file,
        questionnaire_file=questionnaire_file,
    )
    predictions = predictor.process()
    out_path = predictor.save()

    logger.info(f"Прогнозов: {len(predictions)}")
    logger.success(f"Готово: {out_path}")


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Без аргументов (например, автозапуск .exe) — по умолчанию сбор метрик
    if args.command in (None, "collect"):
        run_collect()
    elif args.command == "questionnaire":
        run_questionnaire(file_path=args.file)
    elif args.command == "features":
        run_features(
            tracker_file=args.tracker,
            user=args.user,
            work_start=args.work_start,
            work_end=args.work_end,
        )
    elif args.command == "train":
        run_train(file_path=args.file)
    elif args.command == "merge":
        run_merge(
            features_file=args.features,
            questionnaire_file=args.questionnaire,
        )
    elif args.command == "predict":
        run_predict(
            features_file=args.features,
            questionnaire_file=args.questionnaire,
        )


if __name__ == "__main__":
    main()
