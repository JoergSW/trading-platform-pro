from datetime import UTC, datetime
from trading_platform.infrastructure.clock.test_clock import TestClock

def test_test_clock_returns_fixed_time():
    fixed = datetime(2026, 1, 1, tzinfo=UTC)
    clock = TestClock(fixed)
    assert clock.now_utc() == fixed
