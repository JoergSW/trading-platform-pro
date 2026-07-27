from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
)

from trading_platform.application.instruments.instrument_context import (
    InstrumentContextService,
)
from trading_platform.application.portfolio.portfolio_snapshot import (
    PortfolioSnapshotResult,
    PortfolioSnapshotService,
)
from trading_platform.domain.portfolio.portfolio_snapshot import (
    PortfolioAccount,
    PortfolioPosition,
    PortfolioSnapshot,
)
from trading_platform.presentation.app.main import create_qt_application
from trading_platform.presentation.workspaces.portfolio_workspace import (
    PORTFOLIO_CONTEXT_SOURCE,
    PortfolioWorkspaceWidget,
)


@pytest.fixture(scope="module")
def qt_application() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return create_qt_application([])


class FixedClock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def now_utc(self) -> datetime:
        return self.now


class MutableProvider:
    def __init__(self, result: PortfolioSnapshotResult) -> None:
        self.result = result

    def load_snapshot(self) -> PortfolioSnapshotResult:
        return self.result


def _snapshot(
    *,
    positions: tuple[PortfolioPosition, ...] | None = None,
) -> PortfolioSnapshot:
    return PortfolioSnapshot(
        account=PortfolioAccount(
            "LOCAL-ACCOUNT",
            "USD",
            cash=Decimal("0"),
            net_liquidation_value=None,
            unrealized_pnl=Decimal("25.50"),
        ),
        positions=(
            positions
            if positions is not None
            else (
                PortfolioPosition(
                    "AAPL",
                    Decimal("10"),
                    average_price=Decimal("180.25"),
                    current_price=None,
                    current_value=Decimal("1901.00"),
                    unrealized_pnl=Decimal("98.50"),
                ),
                PortfolioPosition(
                    "MSFT",
                    Decimal("5"),
                ),
            )
        ),
        source_name="Local Portfolio Export",
        observed_at=datetime(2026, 7, 27, 10, 15, tzinfo=UTC),
    )


def _label(widget: PortfolioWorkspaceWidget, name: str) -> QLabel:
    label = widget.findChild(QLabel, name)
    assert label is not None
    return label


def _button(widget: PortfolioWorkspaceWidget, name: str) -> QPushButton:
    button = widget.findChild(QPushButton, name)
    assert button is not None
    return button


def test_portfolio_workspace_is_unavailable_without_explicit_service(
    qt_application: QApplication,
) -> None:
    widget = PortfolioWorkspaceWidget()
    table = widget.findChild(QTableWidget, "portfolioWorkspacePositionsTable")

    assert _label(widget, "portfolioWorkspaceState").text() == "UNAVAILABLE"
    assert _label(widget, "portfolioWorkspaceCash").text() == "UNAVAILABLE"
    assert _label(widget, "portfolioWorkspaceSource").text() == "NOT CONFIGURED"
    assert not _button(widget, "portfolioWorkspaceRefreshButton").isEnabled()
    assert table is not None
    assert table.rowCount() == 0
    widget.close()


def test_portfolio_workspace_displays_exact_values_and_unavailable_fields(
    qt_application: QApplication,
) -> None:
    result = PortfolioSnapshotResult.ready(_snapshot())
    widget = PortfolioWorkspaceWidget(result)
    table = widget.findChild(QTableWidget, "portfolioWorkspacePositionsTable")

    assert _label(widget, "portfolioWorkspaceState").text() == "READY"
    assert _label(widget, "portfolioWorkspaceCash").text() == "0 USD"
    assert (
        _label(widget, "portfolioWorkspaceNetLiquidationValue").text() == "UNAVAILABLE"
    )
    assert _label(widget, "portfolioWorkspaceUnrealizedPnl").text() == "25.50 USD"
    assert table is not None
    assert table.rowCount() == 2
    assert table.item(0, 0).text() == "AAPL"
    assert table.item(0, 3).text() == "UNAVAILABLE"
    assert table.item(1, 2).text() == "UNAVAILABLE"
    assert table.item(1, 4).text() == "UNAVAILABLE"
    widget.close()


def test_positions_table_keeps_observed_utc_reachable_with_as_needed_scrolling(
    qt_application: QApplication,
) -> None:
    widget = PortfolioWorkspaceWidget(PortfolioSnapshotResult.ready(_snapshot()))
    table = widget.findChild(QTableWidget, "portfolioWorkspacePositionsTable")
    assert table is not None
    widget.show()
    qt_application.processEvents()

    header = table.horizontalHeader()
    assert table.horizontalScrollBarPolicy() is Qt.ScrollBarPolicy.ScrollBarAsNeeded
    assert table.horizontalScrollMode() is QAbstractItemView.ScrollMode.ScrollPerPixel
    assert not header.stretchLastSection()
    assert all(
        header.sectionResizeMode(column) is QHeaderView.ResizeMode.ResizeToContents
        for column in range(table.columnCount())
    )

    observed_text = table.item(0, 6).text()
    observed_text_width = table.fontMetrics().horizontalAdvance(observed_text)
    assert header.sectionSize(6) > observed_text_width

    table.setFixedWidth(520)
    qt_application.processEvents()
    horizontal_scrollbar = table.horizontalScrollBar()
    assert horizontal_scrollbar.maximum() > 0
    horizontal_scrollbar.setValue(horizontal_scrollbar.maximum())
    assert horizontal_scrollbar.value() == horizontal_scrollbar.maximum()

    table.setFixedWidth(header.length() + 100)
    qt_application.processEvents()
    assert horizontal_scrollbar.maximum() == 0
    widget.close()


def test_position_selection_publishes_portfolio_instrument_context(
    qt_application: QApplication,
) -> None:
    context_service = InstrumentContextService()
    widget = PortfolioWorkspaceWidget(
        PortfolioSnapshotResult.ready(_snapshot()),
        instrument_context_service=context_service,
    )
    table = widget.findChild(QTableWidget, "portfolioWorkspacePositionsTable")
    assert table is not None

    table.selectRow(1)
    qt_application.processEvents()

    assert context_service.context.symbol == "MSFT"
    assert context_service.context.source == PORTFOLIO_CONTEXT_SOURCE
    widget.close()


def test_refresh_preserves_selected_position_and_classifies_stale(
    qt_application: QApplication,
) -> None:
    snapshot = _snapshot()
    provider = MutableProvider(PortfolioSnapshotResult.ready(snapshot))
    clock = FixedClock(datetime(2026, 7, 27, 10, 15, 30, tzinfo=UTC))
    service = PortfolioSnapshotService(provider, clock)
    context_service = InstrumentContextService()
    widget = PortfolioWorkspaceWidget(
        PortfolioSnapshotResult.ready(snapshot),
        snapshot_service=service,
        instrument_context_service=context_service,
    )
    table = widget.findChild(QTableWidget, "portfolioWorkspacePositionsTable")
    assert table is not None
    table.selectRow(0)
    qt_application.processEvents()

    clock.now = datetime(2026, 7, 27, 10, 20, tzinfo=UTC)
    _button(widget, "portfolioWorkspaceRefreshButton").click()
    qt_application.processEvents()

    assert _label(widget, "portfolioWorkspaceState").text() == "STALE"
    assert _label(widget, "portfolioWorkspaceRefreshStatus").text() == "UPDATED"
    assert table.currentRow() == 0
    assert context_service.context.symbol == "AAPL"
    assert context_service.context.source == PORTFOLIO_CONTEXT_SOURCE
    widget.close()


def test_empty_snapshot_keeps_account_context_without_inventing_positions(
    qt_application: QApplication,
) -> None:
    snapshot = _snapshot(positions=())
    widget = PortfolioWorkspaceWidget(PortfolioSnapshotResult.empty(snapshot))
    table = widget.findChild(QTableWidget, "portfolioWorkspacePositionsTable")

    assert _label(widget, "portfolioWorkspaceState").text() == "EMPTY"
    assert _label(widget, "portfolioWorkspaceAccountReference").text() == (
        "LOCAL-ACCOUNT"
    )
    assert table is not None
    assert table.rowCount() == 0
    assert table.isHidden()
    widget.close()


def test_refresh_error_clears_previous_values_instead_of_reusing_them(
    qt_application: QApplication,
) -> None:
    snapshot = _snapshot()
    provider = MutableProvider(
        PortfolioSnapshotResult.error(
            "Controlled refresh failure.",
            source_name="JSON file: temp/portfolio.json",
        )
    )
    service = PortfolioSnapshotService(
        provider,
        FixedClock(datetime(2026, 7, 27, 10, 15, 30, tzinfo=UTC)),
    )
    widget = PortfolioWorkspaceWidget(
        PortfolioSnapshotResult.ready(snapshot),
        snapshot_service=service,
    )

    _button(widget, "portfolioWorkspaceRefreshButton").click()
    qt_application.processEvents()

    assert _label(widget, "portfolioWorkspaceState").text() == "ERROR"
    assert _label(widget, "portfolioWorkspaceCash").text() == "UNAVAILABLE"
    assert _label(widget, "portfolioWorkspaceRefreshStatus").text() == "ERROR"
    widget.close()
