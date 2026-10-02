from app.controllers.collector_controller import CollectorController
from app.models.aggregated_collector import AggregatedCollector


def main():
    controller = CollectorController(AggregatedCollector())
    controller.run()


if __name__ == "__main__":
    main()