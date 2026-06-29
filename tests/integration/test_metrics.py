from trading_platform.infrastructure.monitoring.metrics import MetricsRegistry

def test_metrics():
    m = MetricsRegistry()
    m.increment("events")
    assert m.snapshot()["events"] == 1
