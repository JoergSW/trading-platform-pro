class MetricsRegistry:
    def __init__(self):
        self._metrics = {}

    def increment(self, name, amount=1):
        self._metrics[name] = self._metrics.get(name, 0) + amount

    def snapshot(self):
        return dict(self._metrics)
