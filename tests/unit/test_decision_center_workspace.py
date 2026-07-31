from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QScrollArea,
    QTableWidget,
)

from trading_platform.application.instruments.instrument_context import (
    InstrumentContextService,
)
from trading_platform.application.portfolio.portfolio_snapshot import (
    PortfolioSnapshotResult,
    PortfolioSnapshotService,
)
from trading_platform.application.trading_candidates.trading_candidates import (
    TradingCandidateService,
)
from trading_platform.application.trading_decisions.trading_decisions import (
    TradingDecisionAlreadyExistsError,
    TradingDecisionService,
)
from trading_platform.domain.portfolio.portfolio_snapshot import (
    PortfolioAccount,
    PortfolioPosition,
    PortfolioSnapshot,
)
from trading_platform.domain.trading_candidates.trading_candidate import (
    TradingCandidate,
    TradingCandidateStatus,
)
from trading_platform.domain.trading_decisions.trading_decision import (
    TradingDecision,
    TradingDecisionStatus,
)
from trading_platform.presentation.app.main import create_qt_application
from trading_platform.presentation.workspaces.decision_center_workspace import (
    DecisionCenterWorkspaceWidget,
)


@pytest.fixture(scope="module")
def qt_application() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return create_qt_application([])


class InMemoryTradingCandidateRepository:
    def __init__(self) -> None:
        self.candidates: dict[str, TradingCandidate] = {}

    def list_candidates(self) -> tuple[TradingCandidate, ...]:
        return tuple(self.candidates.values())

    def find_by_symbol(self, symbol: str) -> TradingCandidate | None:
        return self.candidates.get(symbol)

    def find_by_id(self, candidate_id: str) -> TradingCandidate | None:
        return next(
            (
                candidate
                for candidate in self.candidates.values()
                if candidate.candidate_id.value == candidate_id
            ),
            None,
        )

    def add(self, candidate: TradingCandidate) -> None:
        self.candidates[candidate.symbol] = candidate

    def update_status(
        self,
        candidate: TradingCandidate,
        *,
        expected_status: TradingCandidateStatus,
    ) -> None:
        stored = self.find_by_id(candidate.candidate_id.value)
        assert stored is not None
        assert stored.status is expected_status
        self.candidates[candidate.symbol] = candidate


class InMemoryTradingDecisionRepository:
    def __init__(
        self,
        candidate_repository: InMemoryTradingCandidateRepository,
    ) -> None:
        self.candidate_repository = candidate_repository
        self.decisions: dict[str, TradingDecision] = {}

    def find_by_candidate_id(self, candidate_id: str) -> TradingDecision | None:
        return self.decisions.get(candidate_id)

    def add(self, decision: TradingDecision) -> None:
        if decision.candidate_id.value in self.decisions:
            raise TradingDecisionAlreadyExistsError
        self.decisions[decision.candidate_id.value] = decision

    def accept(
        self,
        candidate: TradingCandidate,
        decision: TradingDecision,
        *,
        expected_candidate_status: TradingCandidateStatus,
        expected_decision_status: TradingDecisionStatus,
    ) -> None:
        stored_candidate = self.candidate_repository.find_by_id(
            candidate.candidate_id.value
        )
        stored_decision = self.find_by_candidate_id(candidate.candidate_id.value)
        assert stored_candidate is not None
        assert stored_decision is not None
        assert stored_candidate.status is expected_candidate_status
        assert stored_decision.status is expected_decision_status
        self.candidate_repository.candidates[candidate.symbol] = candidate
        self.decisions[candidate.candidate_id.value] = decision


class AdvancingClock:
    def __init__(self) -> None:
        self.current = datetime(2026, 7, 15, 15, 30, tzinfo=UTC)

    def now_utc(self) -> datetime:
        value = self.current
        self.current += timedelta(minutes=1)
        return value


class FixedPortfolioClock:
    def __init__(self, now: datetime) -> None:
        self.now = now

    def now_utc(self) -> datetime:
        return self.now


class MutablePortfolioProvider:
    def __init__(self, result: PortfolioSnapshotResult) -> None:
        self.result = result

    def load_snapshot(self) -> PortfolioSnapshotResult:
        return self.result


class SequentialIdGenerator:
    def __init__(self, start: int = 1) -> None:
        self._next = start

    def new_id(self) -> str:
        value = f"00000000-0000-4000-8000-{self._next:012d}"
        self._next += 1
        return value


def _services() -> tuple[TradingCandidateService, TradingDecisionService]:
    candidate_repository = InMemoryTradingCandidateRepository()
    decision_repository = InMemoryTradingDecisionRepository(candidate_repository)
    clock = AdvancingClock()
    return (
        TradingCandidateService(
            candidate_repository,
            clock,
            SequentialIdGenerator(),
        ),
        TradingDecisionService(
            candidate_repository,
            decision_repository,
            clock,
            SequentialIdGenerator(start=101),
        ),
    )


def _service() -> TradingCandidateService:
    return _services()[0]


def _portfolio_snapshot(
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
            )
        ),
        source_name="Local Portfolio Export",
        observed_at=datetime(2026, 7, 27, 10, 15, tzinfo=UTC),
    )


def _label_text(widget: DecisionCenterWorkspaceWidget, object_name: str) -> str:
    label = widget.findChild(QLabel, object_name)
    assert label is not None
    return label.text()


def _button(widget: DecisionCenterWorkspaceWidget, object_name: str) -> QPushButton:
    button = widget.findChild(QPushButton, object_name)
    assert button is not None
    return button


def test_decision_center_is_unavailable_without_explicit_database_service(
    qt_application: QApplication,
) -> None:
    widget = DecisionCenterWorkspaceWidget(InstrumentContextService())

    assert _label_text(widget, "decisionCenterState") == "UNAVAILABLE"
    assert _label_text(widget, "decisionCenterReviewStatus") == "UNAVAILABLE"
    table = widget.findChild(QTableWidget, "decisionCenterCandidateTable")
    refresh = _button(widget, "decisionCenterRefreshButton")
    assert table is not None
    assert table.rowCount() == 0
    assert not refresh.isEnabled()
    assert not _button(widget, "decisionCenterStartReviewButton").isEnabled()
    assert not _button(widget, "decisionCenterRejectButton").isEnabled()
    assert not _button(widget, "decisionCenterArchiveButton").isEnabled()
    assert _label_text(widget, "decisionCenterDecisionDraftStatus") == "UNAVAILABLE"
    assert not _button(widget, "decisionCenterCreateDecisionDraftButton").isEnabled()
    assert not _button(widget, "decisionCenterAcceptDecisionButton").isEnabled()
    assert _label_text(widget, "decisionCenterPortfolioContextState") == (
        "NO SELECTION"
    )
    assert _label_text(widget, "decisionCenterPortfolioPnlState") == "NO SELECTION"
    assert _label_text(widget, "decisionCenterPortfolioExposureState") == (
        "NO SELECTION"
    )
    assert (
        _label_text(
            widget,
            "decisionCenterPortfolioPositionExposureContribution",
        )
        == "Position Exposure: UNAVAILABLE"
    )
    assert not _button(
        widget,
        "decisionCenterPortfolioContextRefreshButton",
    ).isEnabled()
    widget.close()


def test_decision_center_updates_after_intake_and_publishes_selection(
    qt_application: QApplication,
) -> None:
    context_service = InstrumentContextService()
    service = _service()
    widget = DecisionCenterWorkspaceWidget(
        context_service,
        trading_candidate_service=service,
    )
    table = widget.findChild(QTableWidget, "decisionCenterCandidateTable")
    assert table is not None
    assert _label_text(widget, "decisionCenterState") == "EMPTY"

    service.add_candidate("AAPL", "Scanner")
    qt_application.processEvents()

    assert _label_text(widget, "decisionCenterState") == "READY"
    assert table.rowCount() == 1
    assert table.item(0, 0).text() == "AAPL"
    assert table.item(0, 1).text() == "Scanner"
    assert table.item(0, 2).text() == "NEW"

    table.selectRow(0)
    qt_application.processEvents()

    assert context_service.context.symbol == "AAPL"
    assert context_service.context.source == "Decision Center"
    assert _label_text(widget, "decisionCenterReviewStatus") == "READY"
    assert _label_text(widget, "decisionCenterPortfolioContextState") == ("UNAVAILABLE")
    assert _label_text(widget, "decisionCenterPortfolioPnlState") == "UNAVAILABLE"
    assert _label_text(widget, "decisionCenterPortfolioExposureState") == (
        "UNAVAILABLE"
    )
    assert not _button(
        widget,
        "decisionCenterPortfolioContextRefreshButton",
    ).isEnabled()

    widget.refresh_candidates()
    qt_application.processEvents()

    assert table.currentRow() == 0
    assert context_service.context.symbol == "AAPL"
    assert context_service.context.source == "Decision Center"
    widget.close()


def test_decision_center_review_actions_follow_valid_lifecycle(
    qt_application: QApplication,
) -> None:
    context_service = InstrumentContextService()
    service = _service()
    service.add_candidate("AAPL", "Scanner")
    widget = DecisionCenterWorkspaceWidget(
        context_service,
        trading_candidate_service=service,
    )
    table = widget.findChild(QTableWidget, "decisionCenterCandidateTable")
    assert table is not None
    start_review = _button(widget, "decisionCenterStartReviewButton")
    reject = _button(widget, "decisionCenterRejectButton")
    archive = _button(widget, "decisionCenterArchiveButton")

    assert not start_review.isEnabled()
    assert not reject.isEnabled()
    assert not archive.isEnabled()

    table.selectRow(0)
    qt_application.processEvents()

    assert start_review.isEnabled()
    assert reject.isEnabled()
    assert archive.isEnabled()
    created_timestamp = table.item(0, 3).text()
    initial_updated_timestamp = table.item(0, 4).text()

    start_review.click()
    qt_application.processEvents()

    assert table.item(0, 2).text() == "REVIEWING"
    assert table.item(0, 3).text() == created_timestamp
    assert table.item(0, 4).text() != initial_updated_timestamp
    assert table.currentRow() == 0
    assert context_service.context.symbol == "AAPL"
    assert context_service.context.source == "Decision Center"
    assert _label_text(widget, "decisionCenterReviewStatus") == "UPDATED"
    assert not start_review.isEnabled()
    assert reject.isEnabled()
    assert archive.isEnabled()

    reject.click()
    qt_application.processEvents()

    assert table.item(0, 2).text() == "REJECTED"
    assert not start_review.isEnabled()
    assert not reject.isEnabled()
    assert archive.isEnabled()

    archive.click()
    qt_application.processEvents()

    assert table.item(0, 2).text() == "ARCHIVED"
    assert table.currentRow() == 0
    assert context_service.context.symbol == "AAPL"
    assert context_service.context.source == "Decision Center"
    assert not start_review.isEnabled()
    assert not reject.isEnabled()
    assert not archive.isEnabled()
    widget.close()


def test_decision_center_displays_selected_candidate_portfolio_context(
    qt_application: QApplication,
) -> None:
    context_service = InstrumentContextService()
    candidate_service = _service()
    candidate_service.add_candidate("AAPL", "Scanner")
    widget = DecisionCenterWorkspaceWidget(
        context_service,
        trading_candidate_service=candidate_service,
        portfolio_snapshot=PortfolioSnapshotResult.ready(_portfolio_snapshot()),
    )
    table = widget.findChild(QTableWidget, "decisionCenterCandidateTable")
    assert table is not None

    table.selectRow(0)
    qt_application.processEvents()

    assert _label_text(widget, "decisionCenterPortfolioContextState") == "READY"
    assert "Account: LOCAL-ACCOUNT" in _label_text(
        widget,
        "decisionCenterPortfolioContextMetadata",
    )
    assert "Source: Local Portfolio Export" in _label_text(
        widget,
        "decisionCenterPortfolioContextMetadata",
    )
    assert "Observed UTC: 2026-07-27 10:15:00 UTC" in _label_text(
        widget,
        "decisionCenterPortfolioContextMetadata",
    )
    assert "Cash: 0 USD" in _label_text(
        widget,
        "decisionCenterPortfolioContextFinancials",
    )
    assert "Net Liquidation Value: UNAVAILABLE" in _label_text(
        widget,
        "decisionCenterPortfolioContextFinancials",
    )
    assert _label_text(widget, "decisionCenterPortfolioPnlState") == "COMPLETE"
    pnl_summary_label = widget.findChild(
        QLabel,
        "decisionCenterPortfolioPnlSummary",
    )
    assert pnl_summary_label is not None
    assert pnl_summary_label.wordWrap()
    pnl_summary = pnl_summary_label.text()
    assert "Positive: 98.50 USD" in pnl_summary
    assert "Loss: 0 USD" in pnl_summary
    assert "Net: 98.50 USD" in pnl_summary
    assert "P&L Coverage: 1 / 1" in pnl_summary
    pnl_detail = _label_text(widget, "decisionCenterPortfolioPnlDetail")
    assert "Largest Winner: AAPL (98.50 USD)" in pnl_detail
    assert "Largest Loser: NONE" in pnl_detail
    assert "Account Unrealized P&L remains a separate source field" in pnl_detail
    assert _label_text(widget, "decisionCenterPortfolioPositionStatus") == (
        "EXISTING POSITION"
    )
    assert "Quantity: 10" in _label_text(
        widget,
        "decisionCenterPortfolioPositionDetails",
    )
    assert "Current Price: UNAVAILABLE" in _label_text(
        widget,
        "decisionCenterPortfolioPositionDetails",
    )
    assert _label_text(widget, "decisionCenterPortfolioExposureState") == ("COMPLETE")
    assert "Long: 1901.00 USD" in _label_text(
        widget,
        "decisionCenterPortfolioExposureSummary",
    )
    assert "Gross: 1901.00 USD" in _label_text(
        widget,
        "decisionCenterPortfolioExposureSummary",
    )
    assert "Coverage: 1 / 1" in _label_text(
        widget,
        "decisionCenterPortfolioExposureSummary",
    )
    assert "Largest Position: AAPL (1901.00 USD)" in _label_text(
        widget,
        "decisionCenterPortfolioExposureDetail",
    )
    position_exposure = _label_text(
        widget,
        "decisionCenterPortfolioPositionExposureContribution",
    )
    assert "Direction LONG" in position_exposure
    assert "Current Value: 1901.00 USD" in position_exposure
    assert "Absolute Exposure: 1901.00 USD" in position_exposure
    assert "Gross Share: 100.00 %" in position_exposure
    assert "Valuation: VALUED" in position_exposure
    assert context_service.context.symbol == "AAPL"
    assert context_service.context.source == "Decision Center"
    widget.close()


def test_decision_center_portfolio_context_remains_readable_at_narrow_width(
    qt_application: QApplication,
) -> None:
    context_service = InstrumentContextService()
    candidate_service = _service()
    candidate_service.add_candidate("AAPL", "Scanner")
    widget = DecisionCenterWorkspaceWidget(
        context_service,
        trading_candidate_service=candidate_service,
        portfolio_snapshot=PortfolioSnapshotResult.ready(_portfolio_snapshot()),
    )
    table = widget.findChild(QTableWidget, "decisionCenterCandidateTable")
    scroll_area = widget.findChild(QScrollArea, "decisionCenterScrollArea")
    assert table is not None
    assert scroll_area is not None

    table.selectRow(0)
    widget.resize(520, 760)
    widget.show()
    qt_application.processEvents()

    assert (
        scroll_area.horizontalScrollBarPolicy() is Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    )
    assert scroll_area.verticalScrollBar().maximum() > 0

    responsive_label_names = (
        "decisionCenterPortfolioContextMetadata",
        "decisionCenterPortfolioContextFinancials",
        "decisionCenterPortfolioPnlSummary",
        "decisionCenterPortfolioPnlDetail",
        "decisionCenterPortfolioExposureSummary",
        "decisionCenterPortfolioExposureDetail",
        "decisionCenterPortfolioPositionDetails",
        "decisionCenterPortfolioPositionExposureContribution",
        "decisionCenterPortfolioContextDetail",
    )
    for object_name in responsive_label_names:
        label = widget.findChild(QLabel, object_name)
        assert label is not None
        assert label.wordWrap()
        required_height = label.heightForWidth(label.width())
        assert required_height > 0
        assert label.height() >= required_height

    widget.close()


def test_decision_center_marks_exposure_incomplete_without_estimating_values(
    qt_application: QApplication,
) -> None:
    candidate_service = _service()
    candidate_service.add_candidate("AAPL", "Scanner")
    snapshot = _portfolio_snapshot(
        positions=(
            PortfolioPosition(
                "AAPL",
                Decimal("10"),
                current_value=Decimal("1901.00"),
            ),
            PortfolioPosition("MSFT", Decimal("5")),
        )
    )
    widget = DecisionCenterWorkspaceWidget(
        InstrumentContextService(),
        trading_candidate_service=candidate_service,
        portfolio_snapshot=PortfolioSnapshotResult.ready(snapshot),
    )
    table = widget.findChild(QTableWidget, "decisionCenterCandidateTable")
    assert table is not None

    table.selectRow(0)
    qt_application.processEvents()

    assert _label_text(widget, "decisionCenterPortfolioExposureState") == ("INCOMPLETE")
    assert _label_text(widget, "decisionCenterPortfolioPnlState") == "INCOMPLETE"
    assert "P&L Coverage: 0 / 2" in _label_text(
        widget,
        "decisionCenterPortfolioPnlSummary",
    )
    assert "Missing values are not estimated" in _label_text(
        widget,
        "decisionCenterPortfolioPnlDetail",
    )
    assert "Coverage: 1 / 2" in _label_text(
        widget,
        "decisionCenterPortfolioExposureSummary",
    )
    assert "Missing values are not estimated" in _label_text(
        widget,
        "decisionCenterPortfolioExposureDetail",
    )
    assert "Valuation: VALUED" in _label_text(
        widget,
        "decisionCenterPortfolioPositionExposureContribution",
    )
    widget.close()


def test_decision_center_marks_selected_position_exposure_unavailable(
    qt_application: QApplication,
) -> None:
    candidate_service = _service()
    candidate_service.add_candidate("MSFT", "Scanner")
    snapshot = _portfolio_snapshot(
        positions=(
            PortfolioPosition(
                "AAPL",
                Decimal("10"),
                current_value=Decimal("1901.00"),
            ),
            PortfolioPosition(
                "MSFT",
                Decimal("5"),
                current_price=Decimal("450.00"),
            ),
        )
    )
    widget = DecisionCenterWorkspaceWidget(
        InstrumentContextService(),
        trading_candidate_service=candidate_service,
        portfolio_snapshot=PortfolioSnapshotResult.ready(snapshot),
    )
    table = widget.findChild(QTableWidget, "decisionCenterCandidateTable")
    assert table is not None

    table.selectRow(0)
    qt_application.processEvents()

    contribution = _label_text(
        widget,
        "decisionCenterPortfolioPositionExposureContribution",
    )
    assert "Direction UNAVAILABLE" in contribution
    assert "Current Value: UNAVAILABLE" in contribution
    assert "Absolute Exposure: UNAVAILABLE" in contribution
    assert "Gross Share: UNAVAILABLE" in contribution
    assert "Valuation: UNAVAILABLE" in contribution
    widget.close()


def test_decision_center_reports_no_existing_position_without_inference(
    qt_application: QApplication,
) -> None:
    candidate_service = _service()
    candidate_service.add_candidate("AAPL", "Scanner")
    empty_snapshot = _portfolio_snapshot(positions=())
    widget = DecisionCenterWorkspaceWidget(
        InstrumentContextService(),
        trading_candidate_service=candidate_service,
        portfolio_snapshot=PortfolioSnapshotResult.empty(empty_snapshot),
    )
    table = widget.findChild(QTableWidget, "decisionCenterCandidateTable")
    assert table is not None

    table.selectRow(0)
    qt_application.processEvents()

    assert _label_text(widget, "decisionCenterPortfolioContextState") == "EMPTY"
    assert _label_text(widget, "decisionCenterPortfolioPositionStatus") == (
        "NO EXISTING POSITION"
    )
    assert _label_text(widget, "decisionCenterPortfolioExposureState") == ("COMPLETE")
    assert _label_text(widget, "decisionCenterPortfolioPnlState") == "COMPLETE"
    assert "Positive: 0 USD" in _label_text(
        widget,
        "decisionCenterPortfolioPnlSummary",
    )
    assert "P&L Coverage: 0 / 0" in _label_text(
        widget,
        "decisionCenterPortfolioPnlSummary",
    )
    assert "Long: 0 USD" in _label_text(
        widget,
        "decisionCenterPortfolioExposureSummary",
    )
    assert "Coverage: 0 / 0" in _label_text(
        widget,
        "decisionCenterPortfolioExposureSummary",
    )
    assert _label_text(widget, "decisionCenterPortfolioPositionDetails") == (
        "Quantity: UNAVAILABLE | Average Price: UNAVAILABLE | "
        "Current Price: UNAVAILABLE | Current Value: UNAVAILABLE | "
        "Unrealized P&L: UNAVAILABLE"
    )
    assert (
        _label_text(
            widget,
            "decisionCenterPortfolioPositionExposureContribution",
        )
        == "Position Exposure: NO EXISTING POSITION"
    )
    widget.close()


def test_portfolio_context_refresh_preserves_candidate_and_clears_errors(
    qt_application: QApplication,
) -> None:
    context_service = InstrumentContextService()
    candidate_service = _service()
    candidate_service.add_candidate("AAPL", "Scanner")
    snapshot = _portfolio_snapshot()
    provider = MutablePortfolioProvider(PortfolioSnapshotResult.ready(snapshot))
    service = PortfolioSnapshotService(
        provider,
        FixedPortfolioClock(datetime(2026, 7, 27, 10, 20, tzinfo=UTC)),
    )
    widget = DecisionCenterWorkspaceWidget(
        context_service,
        trading_candidate_service=candidate_service,
        portfolio_snapshot=PortfolioSnapshotResult.ready(snapshot),
        portfolio_snapshot_service=service,
    )
    table = widget.findChild(QTableWidget, "decisionCenterCandidateTable")
    refresh = _button(widget, "decisionCenterPortfolioContextRefreshButton")
    assert table is not None
    table.selectRow(0)
    qt_application.processEvents()

    assert refresh.isEnabled()
    refresh.click()
    qt_application.processEvents()

    assert _label_text(widget, "decisionCenterPortfolioContextState") == "STALE"
    assert _label_text(widget, "decisionCenterPortfolioPnlState") == "COMPLETE"
    assert "Snapshot State: STALE" in _label_text(
        widget,
        "decisionCenterPortfolioPnlDetail",
    )
    assert _label_text(widget, "decisionCenterPortfolioExposureState") == ("COMPLETE")
    assert "Snapshot State: STALE" in _label_text(
        widget,
        "decisionCenterPortfolioExposureDetail",
    )
    assert table.item(0, 2).text() == "NEW"
    assert table.currentRow() == 0
    assert context_service.context.symbol == "AAPL"
    assert context_service.context.source == "Decision Center"

    provider.result = PortfolioSnapshotResult.error(
        "Controlled Portfolio context failure.",
        source_name="JSON file: temp/portfolio.json",
    )
    refresh.click()
    qt_application.processEvents()

    assert _label_text(widget, "decisionCenterPortfolioContextState") == "ERROR"
    assert "Cash: UNAVAILABLE" in _label_text(
        widget,
        "decisionCenterPortfolioContextFinancials",
    )
    assert _label_text(widget, "decisionCenterPortfolioPositionStatus") == (
        "UNAVAILABLE"
    )
    assert _label_text(widget, "decisionCenterPortfolioPnlState") == "ERROR"
    assert "Positive: UNAVAILABLE" in _label_text(
        widget,
        "decisionCenterPortfolioPnlSummary",
    )
    assert _label_text(widget, "decisionCenterPortfolioExposureState") == "ERROR"
    assert "Gross: UNAVAILABLE" in _label_text(
        widget,
        "decisionCenterPortfolioExposureSummary",
    )
    assert (
        _label_text(
            widget,
            "decisionCenterPortfolioPositionExposureContribution",
        )
        == "Position Exposure: UNAVAILABLE"
    )
    assert table.item(0, 2).text() == "NEW"
    assert table.currentRow() == 0
    assert context_service.context.symbol == "AAPL"
    assert context_service.context.source == "Decision Center"
    widget.close()


def test_decision_center_creates_and_restores_linked_decision_draft(
    qt_application: QApplication,
) -> None:
    context_service = InstrumentContextService()
    candidate_service, decision_service = _services()
    added = candidate_service.add_candidate("AAPL", "Scanner")
    assert added.candidate is not None
    candidate_service.transition_candidate(
        added.candidate.candidate_id.value,
        TradingCandidateStatus.REVIEWING,
    )
    widget = DecisionCenterWorkspaceWidget(
        context_service,
        trading_candidate_service=candidate_service,
        trading_decision_service=decision_service,
    )
    table = widget.findChild(QTableWidget, "decisionCenterCandidateTable")
    rationale = widget.findChild(
        QPlainTextEdit,
        "decisionCenterDecisionRationale",
    )
    create_button = _button(widget, "decisionCenterCreateDecisionDraftButton")
    assert table is not None
    assert rationale is not None

    table.selectRow(0)
    qt_application.processEvents()

    assert table.item(0, 2).text() == "REVIEWING"
    assert _label_text(widget, "decisionCenterDecisionDraftStatus") == "NO DRAFT"
    assert rationale.isEnabled()
    assert not rationale.isReadOnly()
    assert not create_button.isEnabled()

    rationale.setPlainText("Price structure and volume confirm the reviewed setup.")
    qt_application.processEvents()
    assert create_button.isEnabled()

    create_button.click()
    qt_application.processEvents()

    assert _label_text(widget, "decisionCenterDecisionDraftStatus") == "CREATED"
    assert "Status: DRAFT" in _label_text(
        widget,
        "decisionCenterDecisionDraftMetadata",
    )
    assert rationale.toPlainText() == (
        "Price structure and volume confirm the reviewed setup."
    )
    assert rationale.isReadOnly()
    assert not create_button.isEnabled()
    assert table.item(0, 2).text() == "REVIEWING"
    assert table.currentRow() == 0
    assert context_service.context.source == "Decision Center"
    widget.close()

    restored_widget = DecisionCenterWorkspaceWidget(
        context_service,
        trading_candidate_service=candidate_service,
        trading_decision_service=decision_service,
    )
    restored_table = restored_widget.findChild(
        QTableWidget,
        "decisionCenterCandidateTable",
    )
    restored_rationale = restored_widget.findChild(
        QPlainTextEdit,
        "decisionCenterDecisionRationale",
    )
    assert restored_table is not None
    assert restored_rationale is not None
    restored_table.selectRow(0)
    qt_application.processEvents()

    assert _label_text(restored_widget, "decisionCenterDecisionDraftStatus") == (
        "DRAFT"
    )
    assert restored_rationale.toPlainText() == (
        "Price structure and volume confirm the reviewed setup."
    )
    assert not _button(
        restored_widget,
        "decisionCenterCreateDecisionDraftButton",
    ).isEnabled()
    restored_widget.close()


def test_decision_center_accepts_draft_and_preserves_selection(
    qt_application: QApplication,
) -> None:
    context_service = InstrumentContextService()
    candidate_service, decision_service = _services()
    added = candidate_service.add_candidate("AAPL", "Scanner")
    assert added.candidate is not None
    candidate_service.transition_candidate(
        added.candidate.candidate_id.value,
        TradingCandidateStatus.REVIEWING,
    )
    created = decision_service.create_draft(
        added.candidate.candidate_id.value,
        "Price structure and volume confirm the reviewed setup.",
    )
    assert created.decision is not None
    widget = DecisionCenterWorkspaceWidget(
        context_service,
        trading_candidate_service=candidate_service,
        trading_decision_service=decision_service,
    )
    table = widget.findChild(QTableWidget, "decisionCenterCandidateTable")
    accept_button = _button(widget, "decisionCenterAcceptDecisionButton")
    reject_button = _button(widget, "decisionCenterRejectButton")
    archive_button = _button(widget, "decisionCenterArchiveButton")
    assert table is not None

    table.selectRow(0)
    qt_application.processEvents()

    assert table.item(0, 2).text() == "REVIEWING"
    assert _label_text(widget, "decisionCenterDecisionDraftStatus") == "DRAFT"
    assert accept_button.isEnabled()

    accept_button.click()
    qt_application.processEvents()

    assert table.item(0, 2).text() == "ACCEPTED"
    assert _label_text(widget, "decisionCenterDecisionDraftStatus") == "ACCEPTED"
    assert "Status: ACCEPTED" in _label_text(
        widget,
        "decisionCenterDecisionDraftMetadata",
    )
    assert _label_text(widget, "decisionCenterReviewStatus") == "ACCEPTED"
    assert table.currentRow() == 0
    assert context_service.context.symbol == "AAPL"
    assert context_service.context.source == "Decision Center"
    assert not accept_button.isEnabled()
    assert not reject_button.isEnabled()
    assert not archive_button.isEnabled()
    widget.close()
