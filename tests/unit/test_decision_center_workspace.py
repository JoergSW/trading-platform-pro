from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest
from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QTableWidget

from trading_platform.application.instruments.instrument_context import (
    InstrumentContextService,
)
from trading_platform.application.trading_candidates.trading_candidates import (
    TradingCandidateService,
)
from trading_platform.domain.trading_candidates.trading_candidate import (
    TradingCandidate,
    TradingCandidateStatus,
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


class AdvancingClock:
    def __init__(self) -> None:
        self.current = datetime(2026, 7, 15, 15, 30, tzinfo=UTC)

    def now_utc(self) -> datetime:
        value = self.current
        self.current += timedelta(minutes=1)
        return value


class SequentialIdGenerator:
    def __init__(self) -> None:
        self._next = 1

    def new_id(self) -> str:
        value = f"00000000-0000-4000-8000-{self._next:012d}"
        self._next += 1
        return value


def _service() -> TradingCandidateService:
    return TradingCandidateService(
        InMemoryTradingCandidateRepository(),
        AdvancingClock(),
        SequentialIdGenerator(),
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
