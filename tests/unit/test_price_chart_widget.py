from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from PySide6.QtWidgets import QApplication

from trading_platform.application.market_data.price_history import (
    PriceBar,
    PriceHistory,
)
from trading_platform.presentation.app.main import create_qt_application
from trading_platform.presentation.widgets.price_chart import PriceChartWidget


@pytest.fixture(scope="module")
def qt_application() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return create_qt_application([])


def test_price_chart_accepts_ready_history_and_renders(
    qt_application: QApplication,
) -> None:
    history = PriceHistory.ready(
        "AAPL",
        "Test Feed",
        "1D",
        (
            PriceBar(
                datetime(2026, 7, 1, 20, tzinfo=UTC),
                Decimal("100"),
                Decimal("103"),
                Decimal("99"),
                Decimal("102"),
                1000,
            ),
            PriceBar(
                datetime(2026, 7, 2, 20, tzinfo=UTC),
                Decimal("102"),
                Decimal("104"),
                Decimal("100"),
                Decimal("101"),
                1500,
            ),
        ),
    )
    widget = PriceChartWidget()
    widget.resize(640, 360)

    widget.set_history(history)
    image = widget.grab().toImage()

    assert widget.history is history
    assert not image.isNull()
    widget.close()
