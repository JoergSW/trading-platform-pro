from __future__ import annotations

import os
from datetime import UTC, datetime

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

    def add(self, candidate: TradingCandidate) -> None:
        self.candidates[candidate.symbol] = candidate


class FixedClock:
    def now_utc(self) -> datetime:
        return datetime(2026, 7, 15, 15, 30, tzinfo=UTC)


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
        FixedClock(),
        SequentialIdGenerator(),
    )


def _label_text(widget: DecisionCenterWorkspaceWidget, object_name: str) -> str:
    label = widget.findChild(QLabel, object_name)
    assert label is not None
    return label.text()


def test_decision_center_is_unavailable_without_explicit_database_service(
    qt_application: QApplication,
) -> None:
    widget = DecisionCenterWorkspaceWidget(InstrumentContextService())

    assert _label_text(widget, "decisionCenterState") == "UNAVAILABLE"
    table = widget.findChild(QTableWidget, "decisionCenterCandidateTable")
    refresh = widget.findChild(QPushButton, "decisionCenterRefreshButton")
    assert table is not None
    assert table.rowCount() == 0
    assert refresh is not None
    assert not refresh.isEnabled()
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

    widget.refresh_candidates()
    qt_application.processEvents()

    assert table.currentRow() == 0
    assert context_service.context.symbol == "AAPL"
    assert context_service.context.source == "Decision Center"
    widget.close()
