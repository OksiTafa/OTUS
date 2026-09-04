import time

class MetricCollector:


    def collect_all(self):
        self.metrics = {
            "cpu": self.collect_cpu(),
            "ram": self.collect_ram(),
            "time": time.time(), # когда собран этот снимок
        }
        return self.metrics



