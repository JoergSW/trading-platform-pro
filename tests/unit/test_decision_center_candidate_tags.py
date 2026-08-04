from __future__ import annotations

import os
from datetime import UTC, datetime

import pytest
from PySide6.QtWidgets import (
    QApplication,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QTableWidget,
)

from trading_platform.application.instruments.instrument_context import (
    InstrumentContextService,
)
from trading_platform.application.trading_candidate_tags import (
    TradingCandidateTagService,
    TradingCandidateTagsState,
)
from trading_platform.application.trading_candidates.trading_candidates import (
    TradingCandidateService,
)
from trading_platform.domain.trading_candidate_tags import TradingCandidateTag
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


class CandidateRepository:
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
                if candidate.candidate_id == CandidateId(candidate_id)
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
        assert self.candidates[candidate.symbol].status is expected_status
        self.candidates[candidate.symbol] = candidate


class TagRepository:
    def __init__(self) -> None:
        self.tags: dict[str, dict[str, TradingCandidateTag]] = {}

    def list_for_candidate(
        self,
        candidate_id: str,
    ) -> tuple[TradingCandidateTag, ...]:
        return tuple(self.tags.get(candidate_id, {}).values())

    def add(self, candidate_id: str, tag: TradingCandidateTag) -> bool:
        candidate_tags = self.tags.setdefault(candidate_id, {})
        if tag.normalized_key in candidate_tags:
            return False
        candidate_tags[tag.normalized_key] = tag
        return True

    def remove(self, candidate_id: str, tag: TradingCandidateTag) -> bool:
        candidate_tags = self.tags.setdefault(candidate_id, {})
        return candidate_tags.pop(tag.normalized_key, None) is not None


class Clock:
    def now_utc(self) -> datetime:
        return datetime(2026, 8, 4, 12, 0, tzinfo=UTC)


class IdGenerator:
    def new_id(self) -> str:
        return "00000000-0000-4000-8000-000000000001"


def test_decision_center_candidate_tags_add_remove_refresh_and_lock_closed_status(
    qt_application: QApplication,
) -> None:
    candidate_repository = CandidateRepository()
    tag_repository = TagRepository()
    candidate_service = TradingCandidateService(
        candidate_repository,
        Clock(),
        IdGenerator(),
    )
    tag_service = TradingCandidateTagService(candidate_repository, tag_repository)
    added = candidate_service.add_candidate("AAPL", "Scanner")
    assert added.candidate is not None
    context = InstrumentContextService()
    widget = DecisionCenterWorkspaceWidget(
        context,
        trading_candidate_service=candidate_service,
        trading_candidate_tag_service=tag_service,
    )
    candidate_table = widget.findChild(QTableWidget, "decisionCenterCandidateTable")
    tag_state = widget.findChild(QLabel, "decisionCenterCandidateTagsState")
    tag_list = widget.findChild(QListWidget, "decisionCenterCandidateTagsList")
    tag_input = widget.findChild(QLineEdit, "decisionCenterCandidateTagInput")
    add_button = widget.findChild(QPushButton, "decisionCenterCandidateTagAddButton")
    remove_button = widget.findChild(
        QPushButton,
        "decisionCenterCandidateTagRemoveButton",
    )
    tag_refresh_button = widget.findChild(
        QPushButton,
        "decisionCenterCandidateTagsRefreshButton",
    )
    candidate_refresh_button = widget.findChild(
        QPushButton,
        "decisionCenterRefreshButton",
    )
    reject_button = widget.findChild(QPushButton, "decisionCenterRejectButton")
    assert candidate_table is not None
    assert tag_state is not None
    assert tag_list is not None
    assert tag_input is not None
    assert add_button is not None
    assert remove_button is not None
    assert tag_refresh_button is not None
    assert candidate_refresh_button is not None
    assert reject_button is not None

    assert widget.candidate_tags_state is TradingCandidateTagsState.UNAVAILABLE
    assert tag_state.text() == "UNAVAILABLE"
    assert not tag_refresh_button.isEnabled()
    assert not tag_input.isEnabled()
    assert not add_button.isEnabled()
    assert not remove_button.isEnabled()

    candidate_table.selectRow(0)
    qt_application.processEvents()
    selected_id = added.candidate.candidate_id.value

    assert widget.candidate_tags_state is TradingCandidateTagsState.EMPTY
    assert tag_state.text() == "EMPTY"
    assert tag_refresh_button.isEnabled()
    assert tag_input.isEnabled()
    assert not add_button.isEnabled()
    assert not remove_button.isEnabled()

    tag_input.setText("  zeta   setup ")
    qt_application.processEvents()
    assert add_button.isEnabled()
    add_button.click()
    tag_input.setText("Alpha")
    add_button.click()
    qt_application.processEvents()

    assert [tag_list.item(row).text() for row in range(tag_list.count())] == [
        "Alpha",
        "zeta setup",
    ]
    assert candidate_table.currentRow() == 0
    assert context.context.symbol == "AAPL"
    assert context.context.source == "Decision Center"
    selected_candidate = candidate_repository.find_by_id(selected_id)
    assert selected_candidate is not None
    assert selected_candidate.status is TradingCandidateStatus.NEW

    tag_list.setCurrentRow(1)
    qt_application.processEvents()
    assert remove_button.isEnabled()
    remove_button.click()
    qt_application.processEvents()
    assert [tag_list.item(row).text() for row in range(tag_list.count())] == ["Alpha"]

    tag_refresh_button.click()
    candidate_refresh_button.click()
    qt_application.processEvents()
    assert candidate_table.currentRow() == 0
    assert context.context.symbol == "AAPL"
    assert context.context.source == "Decision Center"

    reject_button.click()
    qt_application.processEvents()
    tag_list.setCurrentRow(0)
    qt_application.processEvents()

    assert candidate_table.item(0, 2).text() == "REJECTED"
    assert widget.candidate_tags_state is TradingCandidateTagsState.READY
    assert tag_state.text() == "READY"
    assert tag_list.item(0).text() == "Alpha"
    assert tag_refresh_button.isEnabled()
    assert not tag_input.isEnabled()
    assert not add_button.isEnabled()
    assert not remove_button.isEnabled()
    assert context.context.symbol == "AAPL"
    assert context.context.source == "Decision Center"
    widget.close()
