from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QTableWidget,
)

from trading_platform.application.instruments.instrument_context import (
    InstrumentContextService,
)
from trading_platform.application.trading_candidate_notes import (
    TradingCandidateNoteService,
)
from trading_platform.application.trading_candidates.trading_candidates import (
    TradingCandidateService,
)
from trading_platform.domain.trading_candidates.trading_candidate import (
    CandidateId,
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


class Repository:
    def __init__(self) -> None:
        self.candidates: dict[str, TradingCandidate] = {}
        self.notes = []

    def list_candidates(self) -> tuple[TradingCandidate, ...]:
        return tuple(self.candidates.values())

    def find_by_symbol(self, symbol: str) -> TradingCandidate | None:
        return self.candidates.get(symbol)

    def find_by_id(self, candidate_id: str) -> TradingCandidate | None:
        return next(
            (
                candidate
                for candidate in self.candidates.values()
                if candidate.candidate_id == CandidateId(candidate_id)
            ),
            None,
        )

    def add(self, value) -> None:
        if isinstance(value, TradingCandidate):
            self.candidates[value.symbol] = value
        else:
            self.notes.append(value)

    def update_status(
        self,
        candidate: TradingCandidate,
        *,
        expected_status: TradingCandidateStatus,
    ) -> None:
        assert self.candidates[candidate.symbol].status is expected_status
        self.candidates[candidate.symbol] = candidate

    def list_for_candidate(self, candidate_id: str):
        return tuple(
            note
            for note in reversed(self.notes)
            if note.candidate_id.value == candidate_id
        )


class Clock:
    def now_utc(self) -> datetime:
        return datetime(2026, 8, 3, 10, 0, tzinfo=UTC)


class IdGenerator:
    def __init__(self) -> None:
        self.value = 1

    def new_id(self) -> str:
        result = f"00000000-0000-4000-8000-{self.value:012d}"
        self.value += 1
        return result


def test_decision_center_adds_and_displays_candidate_note(
    qt_application: QApplication,
) -> None:
    repository = Repository()
    clock = Clock()
    ids = IdGenerator()
    candidate_service = TradingCandidateService(repository, clock, ids)
    note_service = TradingCandidateNoteService(repository, repository, clock, ids)
    candidate_service.add_candidate("AAPL", "Scanner")
    context = InstrumentContextService()
    widget = DecisionCenterWorkspaceWidget(
        context,
        trading_candidate_service=candidate_service,
        trading_candidate_note_service=note_service,
    )
    candidate_table = widget.findChild(QTableWidget, "decisionCenterCandidateTable")
    note_table = widget.findChild(QTableWidget, "decisionCenterCandidateNotesTable")
    note_input = widget.findChild(QPlainTextEdit, "decisionCenterCandidateNoteInput")
    add_button = widget.findChild(QPushButton, "decisionCenterCandidateNoteAddButton")
    assert candidate_table is not None
    assert note_table is not None
    assert note_input is not None
    assert add_button is not None

    candidate_table.selectRow(0)
    note_input.setPlainText("Volume confirms the setup.")
    qt_application.processEvents()
    assert add_button.isEnabled()

    add_button.click()
    qt_application.processEvents()

    assert note_table.rowCount() == 1
    assert context.context.symbol == "AAPL"
    note_table.selectRow(0)
    qt_application.processEvents()
    selection = widget.findChild(QLabel, "decisionCenterCandidateNoteSelection")
    assert selection is not None
    assert "Volume confirms the setup." in selection.text()
    widget.close()
