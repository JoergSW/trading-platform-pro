from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from PySide6.QtWidgets import QApplication, QLabel, QPushButton

from trading_platform.application.instruments.instrument_context import (
    InstrumentContextService,
    InstrumentContextState,
)
from trading_platform.application.market_data.price_history import (
    PriceBar,
    PriceHistory,
    PriceHistoryService,
)
from trading_platform.presentation.app.main import create_qt_application
from trading_platform.presentation.widgets.price_chart import PriceChartWidget
from trading_platform.presentation.workspaces.analysis_workspace import (
    AnalysisWorkspaceWidget,
)


@pytest.fixture(scope="module")
def qt_application() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return create_qt_application([])


class MappingPriceHistoryProvider:
    def __init__(self, histories: dict[str, PriceHistory]) -> None:
        self.histories = histories
        self.loaded_symbols: list[str] = []

    def load_history(self, symbol: str) -> PriceHistory:
        self.loaded_symbols.append(symbol)
        return self.histories[symbol]


def _ready_history(symbol: str, close_price: str = "102.00") -> PriceHistory:
    return PriceHistory.ready(
        symbol,
        "Test History Feed",
        "1D",
        (
            PriceBar(
                observed_at=datetime(2026, 7, 1, 20, tzinfo=UTC),
                open_price=Decimal("100.00"),
                high_price=Decimal("103.00"),
                low_price=Decimal("99.00"),
                close_price=Decimal(close_price),
                volume=1000,
            ),
        ),
    )


def _label_text(widget: AnalysisWorkspaceWidget, object_name: str) -> str:
    label = widget.findChild(QLabel, object_name)
    assert label is not None
    return label.text()


def test_analysis_workspace_shows_no_selection_initially(
    qt_application: QApplication,
) -> None:
    service = InstrumentContextService()
    widget = AnalysisWorkspaceWidget(service)

    assert widget.instrument_context.state is InstrumentContextState.NO_SELECTION
    assert _label_text(widget, "analysisWorkspaceState") == "NO SELECTION"
    assert _label_text(widget, "analysisWorkspaceActiveSymbol") == "NO SELECTION"
    assert _label_text(widget, "analysisWorkspaceContextSource") == "NOT AVAILABLE"
    assert _label_text(widget, "analysisPriceHistoryState") == "NO SELECTION"
    assert _label_text(widget, "analysisPriceHistoryBarCount") == "0"

    refresh = widget.findChild(QPushButton, "analysisPriceHistoryRefreshButton")
    assert refresh is not None
    assert not refresh.isEnabled()
    widget.close()


def test_analysis_workspace_follows_selected_instrument_context_without_source(
    qt_application: QApplication,
) -> None:
    service = InstrumentContextService()
    widget = AnalysisWorkspaceWidget(service)

    service.select_instrument("AAPL", "Scanner")
    qt_application.processEvents()

    assert _label_text(widget, "analysisWorkspaceState") == "SELECTED"
    assert _label_text(widget, "analysisWorkspaceActiveSymbol") == "AAPL"
    assert _label_text(widget, "analysisWorkspaceContextSource") == "Scanner"
    assert _label_text(widget, "analysisPriceHistoryState") == "UNAVAILABLE"

    service.clear_instrument("Scanner")
    qt_application.processEvents()

    assert _label_text(widget, "analysisWorkspaceState") == "NO SELECTION"
    assert _label_text(widget, "analysisWorkspaceActiveSymbol") == "NO SELECTION"
    assert _label_text(widget, "analysisWorkspaceContextSource") == "Scanner"
    assert _label_text(widget, "analysisPriceHistoryState") == "NO SELECTION"

    widget.close()


def test_analysis_workspace_loads_ready_history_for_selected_symbol(
    qt_application: QApplication,
) -> None:
    context_service = InstrumentContextService()
    history = _ready_history("AAPL")
    provider = MappingPriceHistoryProvider({"AAPL": history})
    widget = AnalysisWorkspaceWidget(
        context_service,
        price_history_service=PriceHistoryService(provider),
    )

    context_service.select_instrument("AAPL", "Watchlist")
    qt_application.processEvents()

    assert provider.loaded_symbols == ["AAPL"]
    assert widget.price_history is history
    assert _label_text(widget, "analysisPriceHistoryState") == "READY"
    assert _label_text(widget, "analysisPriceHistorySource") == "Test History Feed"
    assert _label_text(widget, "analysisPriceHistoryTimeframe") == "1D"
    assert _label_text(widget, "analysisPriceHistoryBarCount") == "1"
    assert _label_text(widget, "analysisPriceHistoryPeriod") == (
        "2026-07-01 UTC → 2026-07-01 UTC"
    )

    chart = widget.findChild(PriceChartWidget, "analysisPriceChartCanvas")
    assert chart is not None
    assert chart.history is history
    widget.close()


def test_analysis_workspace_displays_no_data_and_error_states(
    qt_application: QApplication,
) -> None:
    context_service = InstrumentContextService()
    provider = MappingPriceHistoryProvider(
        {
            "AAPL": PriceHistory.no_data("AAPL", "Test Feed"),
            "MSFT": PriceHistory.error("MSFT", "Controlled invalid payload."),
        }
    )
    widget = AnalysisWorkspaceWidget(
        context_service,
        price_history_service=PriceHistoryService(provider),
    )

    context_service.select_instrument("AAPL", "Scanner")
    qt_application.processEvents()
    assert _label_text(widget, "analysisPriceHistoryState") == "NO DATA"

    context_service.select_instrument("MSFT", "Scanner")
    qt_application.processEvents()
    assert _label_text(widget, "analysisPriceHistoryState") == "ERROR"
    assert "Controlled invalid payload" in _label_text(
        widget,
        "analysisPriceHistoryDetail",
    )
    widget.close()


def test_analysis_workspace_manual_refresh_reloads_current_symbol(
    qt_application: QApplication,
) -> None:
    context_service = InstrumentContextService()
    history = _ready_history("AAPL")
    provider = MappingPriceHistoryProvider({"AAPL": history})
    widget = AnalysisWorkspaceWidget(
        context_service,
        price_history_service=PriceHistoryService(provider),
    )
    context_service.select_instrument("AAPL", "Scanner")
    qt_application.processEvents()

    refresh = widget.findChild(QPushButton, "analysisPriceHistoryRefreshButton")
    assert refresh is not None
    refresh.click()
    qt_application.processEvents()

    assert provider.loaded_symbols == ["AAPL", "AAPL"]
    assert widget.price_history is history
    assert _label_text(widget, "analysisPriceHistoryState") == "READY"
    widget.close()


def test_analysis_workspace_ignores_obsolete_queued_request(
    qt_application: QApplication,
) -> None:
    context_service = InstrumentContextService()
    provider = MappingPriceHistoryProvider(
        {
            "AAPL": _ready_history("AAPL"),
            "MSFT": _ready_history("MSFT", "101.00"),
        }
    )
    widget = AnalysisWorkspaceWidget(
        context_service,
        price_history_service=PriceHistoryService(provider),
    )

    context_service.select_instrument("AAPL", "Scanner")
    context_service.select_instrument("MSFT", "Scanner")
    qt_application.processEvents()

    assert provider.loaded_symbols == ["MSFT"]
    assert widget.price_history is not None
    assert widget.price_history.symbol == "MSFT"
    assert _label_text(widget, "analysisWorkspaceActiveSymbol") == "MSFT"
    widget.close()
