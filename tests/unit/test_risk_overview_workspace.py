from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QTableWidget,
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
from trading_platform.presentation.workspaces.risk_overview_workspace import (
    RiskOverviewWorkspaceWidget,
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
        account=PortfolioAccount("LOCAL-ACCOUNT", "USD"),
        positions=(
            positions
            if positions is not None
            else (
                PortfolioPosition(
                    "AAPL",
                    Decimal("10"),
                    current_value=Decimal("1901.00"),
                ),
                PortfolioPosition(
                    "SPY",
                    Decimal("-2"),
                    current_value=Decimal("-500.00"),
                ),
                PortfolioPosition(
                    "MSFT",
                    Decimal("5"),
                    current_price=Decimal("450.00"),
                ),
            )
        ),
        source_name="Local Portfolio Export",
        observed_at=datetime(2026, 7, 28, 6, 15, tzinfo=UTC),
    )


def _label(widget: RiskOverviewWorkspaceWidget, name: str) -> QLabel:
    label = widget.findChild(QLabel, name)
    assert label is not None
    return label


def _button(widget: RiskOverviewWorkspaceWidget, name: str) -> QPushButton:
    button = widget.findChild(QPushButton, name)
    assert button is not None
    return button


def test_risk_overview_is_unavailable_without_explicit_source(
    qt_application: QApplication,
) -> None:
    widget = RiskOverviewWorkspaceWidget()
    table = widget.findChild(QTableWidget, "riskOverviewPositionExposureTable")

    assert _label(widget, "riskOverviewSnapshotState").text() == "UNAVAILABLE"
    assert _label(widget, "riskOverviewExposureState").text() == "UNAVAILABLE"
    assert _label(widget, "riskOverviewSource").text() == "NOT CONFIGURED"
    assert _label(widget, "riskOverviewGrossExposure").text() == "UNAVAILABLE"
    assert _label(widget, "riskOverviewUnvaluedPositions").text() == "UNAVAILABLE"
    assert not _button(widget, "riskOverviewRefreshButton").isEnabled()
    assert table is not None
    assert table.rowCount() == 0
    assert table.isHidden()
    widget.close()


def test_risk_overview_displays_existing_exposure_results_without_reconstruction(
    qt_application: QApplication,
) -> None:
    widget = RiskOverviewWorkspaceWidget(PortfolioSnapshotResult.ready(_snapshot()))
    table = widget.findChild(QTableWidget, "riskOverviewPositionExposureTable")

    assert _label(widget, "riskOverviewSnapshotState").text() == "READY"
    assert _label(widget, "riskOverviewExposureState").text() == "INCOMPLETE"
    assert _label(widget, "riskOverviewSource").text() == "Local Portfolio Export"
    assert _label(widget, "riskOverviewObservedAt").text() == (
        "2026-07-28 06:15:00 UTC"
    )
    assert _label(widget, "riskOverviewLongExposure").text() == "1901.00 USD"
    assert _label(widget, "riskOverviewShortExposure").text() == "500.00 USD"
    assert _label(widget, "riskOverviewGrossExposure").text() == "2401.00 USD"
    assert _label(widget, "riskOverviewNetExposure").text() == "1401.00 USD"
    assert _label(widget, "riskOverviewLargestPosition").text() == (
        "AAPL | 1901.00 USD"
    )
    assert _label(widget, "riskOverviewLargestConcentration").text() == "79.18 %"
    assert _label(widget, "riskOverviewValuationCoverage").text() == "2 / 3"
    assert _label(widget, "riskOverviewUnvaluedPositions").text() == "MSFT"
    assert table is not None
    assert table.rowCount() == 3
    assert table.item(0, 1).text() == "LONG"
    assert table.item(0, 4).text() == "79.18 %"
    assert table.item(1, 1).text() == "SHORT"
    assert table.item(1, 4).text() == "20.82 %"
    assert table.item(2, 0).text() == "MSFT"
    assert table.item(2, 1).text() == "UNAVAILABLE"
    assert table.item(2, 2).text() == "UNAVAILABLE"
    assert table.item(2, 5).text() == "UNAVAILABLE"
    widget.close()


def test_risk_overview_keeps_cards_readable_at_narrow_workspace_width(
    qt_application: QApplication,
) -> None:
    widget = RiskOverviewWorkspaceWidget(PortfolioSnapshotResult.ready(_snapshot()))
    scroll_area = widget.findChild(QScrollArea, "riskOverviewScrollArea")
    table = widget.findChild(QTableWidget, "riskOverviewPositionExposureTable")
    assert scroll_area is not None
    assert table is not None

    widget.resize(520, 760)
    widget.show()
    qt_application.processEvents()

    source_label = _label(widget, "riskOverviewSource")
    observed_label = _label(widget, "riskOverviewObservedAt")
    coverage_label = _label(widget, "riskOverviewValuationCoverage")
    unvalued_label = _label(widget, "riskOverviewUnvaluedPositions")
    snapshot_state_label = _label(widget, "riskOverviewSnapshotState")
    exposure_state_label = _label(widget, "riskOverviewExposureState")
    refresh_status = _label(widget, "riskOverviewRefreshStatus")
    refresh_button = _button(widget, "riskOverviewRefreshButton")
    source_card = source_label.parentWidget()
    observed_card = observed_label.parentWidget()
    coverage_card = coverage_label.parentWidget()
    unvalued_card = unvalued_label.parentWidget()
    assert isinstance(source_card, QFrame)
    assert isinstance(observed_card, QFrame)
    assert isinstance(coverage_card, QFrame)
    assert isinstance(unvalued_card, QFrame)

    assert source_card.y() == observed_card.y()
    assert coverage_card.y() == unvalued_card.y()
    assert coverage_card.y() > source_card.y()
    assert source_card.x() < observed_card.x()
    assert coverage_card.x() < unvalued_card.x()
    assert all(
        card.width() >= 220
        for card in (source_card, observed_card, coverage_card, unvalued_card)
    )
    assert observed_label.wordWrap()
    assert (
        scroll_area.horizontalScrollBarPolicy() is Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    )
    assert scroll_area.horizontalScrollBar().maximum() == 0
    assert all(
        label.width() >= label.fontMetrics().horizontalAdvance(label.text())
        for label in (snapshot_state_label, exposure_state_label, refresh_status)
    )
    assert refresh_button.isVisible()
    assert refresh_button.geometry().right() <= scroll_area.widget().width()

    table.setFixedWidth(420)
    qt_application.processEvents()
    assert table.horizontalScrollBarPolicy() is Qt.ScrollBarPolicy.ScrollBarAsNeeded
    assert table.horizontalScrollBar().maximum() > 0

    narrow_card_width = source_card.width()
    widget.resize(820, 760)
    qt_application.processEvents()
    assert source_card.width() > narrow_card_width
    assert scroll_area.horizontalScrollBar().maximum() == 0
    widget.close()


def test_risk_overview_empty_portfolio_has_known_zero_exposure(
    qt_application: QApplication,
) -> None:
    snapshot = _snapshot(positions=())
    widget = RiskOverviewWorkspaceWidget(PortfolioSnapshotResult.empty(snapshot))
    table = widget.findChild(QTableWidget, "riskOverviewPositionExposureTable")

    assert _label(widget, "riskOverviewSnapshotState").text() == "EMPTY"
    assert _label(widget, "riskOverviewExposureState").text() == "COMPLETE"
    assert _label(widget, "riskOverviewLongExposure").text() == "0 USD"
    assert _label(widget, "riskOverviewShortExposure").text() == "0 USD"
    assert _label(widget, "riskOverviewGrossExposure").text() == "0 USD"
    assert _label(widget, "riskOverviewNetExposure").text() == "0 USD"
    assert _label(widget, "riskOverviewLargestPosition").text() == "NONE"
    assert _label(widget, "riskOverviewLargestConcentration").text() == "0.00 %"
    assert _label(widget, "riskOverviewValuationCoverage").text() == "0 / 0"
    assert _label(widget, "riskOverviewUnvaluedPositions").text() == "NONE"
    assert table is not None
    assert table.rowCount() == 0
    assert table.isHidden()
    widget.close()


def test_risk_overview_refresh_preserves_stale_and_completeness_states(
    qt_application: QApplication,
) -> None:
    snapshot = _snapshot()
    provider = MutableProvider(PortfolioSnapshotResult.ready(snapshot))
    clock = FixedClock(datetime(2026, 7, 28, 6, 15, 30, tzinfo=UTC))
    service = PortfolioSnapshotService(provider, clock)
    widget = RiskOverviewWorkspaceWidget(
        PortfolioSnapshotResult.ready(snapshot),
        snapshot_service=service,
    )

    clock.now = datetime(2026, 7, 28, 6, 20, tzinfo=UTC)
    _button(widget, "riskOverviewRefreshButton").click()
    qt_application.processEvents()

    assert _label(widget, "riskOverviewSnapshotState").text() == "STALE"
    assert _label(widget, "riskOverviewExposureState").text() == "INCOMPLETE"
    assert _label(widget, "riskOverviewRefreshStatus").text() == "UPDATED"
    assert _label(widget, "riskOverviewGrossExposure").text() == "2401.00 USD"
    assert _label(widget, "riskOverviewUnvaluedPositions").text() == "MSFT"
    widget.close()


def test_risk_overview_refresh_error_clears_previous_values(
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
        FixedClock(datetime(2026, 7, 28, 6, 15, 30, tzinfo=UTC)),
    )
    widget = RiskOverviewWorkspaceWidget(
        PortfolioSnapshotResult.ready(snapshot),
        snapshot_service=service,
    )
    table = widget.findChild(QTableWidget, "riskOverviewPositionExposureTable")
    assert table is not None
    assert table.rowCount() == 3

    _button(widget, "riskOverviewRefreshButton").click()
    qt_application.processEvents()

    assert _label(widget, "riskOverviewSnapshotState").text() == "ERROR"
    assert _label(widget, "riskOverviewExposureState").text() == "ERROR"
    assert _label(widget, "riskOverviewGrossExposure").text() == "UNAVAILABLE"
    assert _label(widget, "riskOverviewUnvaluedPositions").text() == "UNAVAILABLE"
    assert _label(widget, "riskOverviewRefreshStatus").text() == "ERROR"
    assert table.rowCount() == 0
    assert table.isHidden()
    widget.close()
