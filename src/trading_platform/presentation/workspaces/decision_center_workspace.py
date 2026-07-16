from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from trading_platform.application.instruments.instrument_context import (
    InstrumentContextService,
    InstrumentContextState,
)
from trading_platform.application.trading_candidates.trading_candidates import (
    TradingCandidateCollection,
    TradingCandidateCollectionListener,
    TradingCandidateCollectionState,
    TradingCandidateReviewResult,
    TradingCandidateService,
)
from trading_platform.domain.trading_candidates.trading_candidate import (
    TradingCandidate,
    TradingCandidateStatus,
)

DECISION_CENTER_CONTEXT_SOURCE = "Decision Center"


class DecisionCenterWorkspaceWidget(QWidget):
    """Display and explicitly review persistent Trading Candidates."""

    def __init__(
        self,
        instrument_context_service: InstrumentContextService,
        parent: QWidget | None = None,
        *,
        trading_candidate_service: TradingCandidateService | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("decisionCenterWorkspaceWidget")
        self._instrument_context_service = instrument_context_service
        self._trading_candidate_service = trading_candidate_service
        self._candidates: tuple[TradingCandidate, ...] = ()
        self._selected_candidate_id: str | None = None
        self._collection_listener: TradingCandidateCollectionListener = (
            self._on_collection_changed
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(10)

        title = QLabel("Decision Center", self)
        title.setObjectName("decisionCenterWorkspaceTitle")
        header.addWidget(title)
        header.addStretch(1)

        self._refresh_button = QPushButton("Refresh", self)
        self._refresh_button.setObjectName("decisionCenterRefreshButton")
        self._refresh_button.clicked.connect(self.refresh_candidates)
        header.addWidget(self._refresh_button)

        self._state_label = QLabel(self)
        self._state_label.setObjectName("decisionCenterState")
        header.addWidget(self._state_label)
        layout.addLayout(header)

        panel = QFrame(self)
        panel.setObjectName("decisionCenterCandidatePanel")
        panel_layout = QVBoxLayout(panel)
        panel_layout.setContentsMargins(14, 12, 14, 14)
        panel_layout.setSpacing(10)

        review_actions = QHBoxLayout()
        review_actions.setContentsMargins(0, 0, 0, 0)
        review_actions.setSpacing(8)

        self._review_status_label = QLabel(self)
        self._review_status_label.setObjectName("decisionCenterReviewStatus")
        review_actions.addWidget(self._review_status_label)
        review_actions.addStretch(1)

        self._start_review_button = QPushButton("Start Review", panel)
        self._start_review_button.setObjectName("decisionCenterStartReviewButton")
        self._start_review_button.clicked.connect(self._start_review)
        review_actions.addWidget(self._start_review_button)

        self._reject_button = QPushButton("Reject", panel)
        self._reject_button.setObjectName("decisionCenterRejectButton")
        self._reject_button.clicked.connect(self._reject)
        review_actions.addWidget(self._reject_button)

        self._archive_button = QPushButton("Archive", panel)
        self._archive_button.setObjectName("decisionCenterArchiveButton")
        self._archive_button.clicked.connect(self._archive)
        review_actions.addWidget(self._archive_button)
        panel_layout.addLayout(review_actions)

        self._detail_label = QLabel(panel)
        self._detail_label.setObjectName("decisionCenterDetail")
        self._detail_label.setWordWrap(True)
        panel_layout.addWidget(self._detail_label)

        self._table = QTableWidget(panel)
        self._table.setObjectName("decisionCenterCandidateTable")
        self._table.setColumnCount(5)
        self._table.setHorizontalHeaderLabels(
            ("Symbol", "Origin", "Status", "Created UTC", "Updated UTC")
        )
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        header_view = self._table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_view.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header_view.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        self._table.itemSelectionChanged.connect(self._publish_selected_candidate)
        panel_layout.addWidget(self._table, 1)
        layout.addWidget(panel, 1)

        safety_note = QLabel(
            "Candidate review only. Review actions update the persistent candidate "
            "lifecycle; they do not accept a Trading Decision, prepare an order, "
            "connect to a broker or perform a LIVE action.",
            self,
        )
        safety_note.setObjectName("decisionCenterSafetyNote")
        safety_note.setWordWrap(True)
        layout.addWidget(safety_note)

        self._set_review_status("NO SELECTION", "idle")
        self._update_review_actions()

        if self._trading_candidate_service is None:
            self._refresh_button.setEnabled(False)
            self._render_collection(
                TradingCandidateCollection.unavailable(
                    "No Trading Candidate database was explicitly configured."
                )
            )
        else:
            self._trading_candidate_service.subscribe(self._collection_listener)
            self.refresh_candidates()

    @property
    def candidates(self) -> tuple[TradingCandidate, ...]:
        return self._candidates

    def refresh_candidates(self) -> None:
        if self._trading_candidate_service is None:
            return
        self._set_state("LOADING", "loading")
        self._detail_label.setText("Loading persistent Trading Candidates.")
        self._trading_candidate_service.refresh()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        if self._trading_candidate_service is not None:
            self._trading_candidate_service.unsubscribe(self._collection_listener)
        super().closeEvent(event)

    def _on_collection_changed(self, collection: TradingCandidateCollection) -> None:
        self._render_collection(collection)

    def _render_collection(self, collection: TradingCandidateCollection) -> None:
        context = self._instrument_context_service.context
        context_symbol = (
            context.symbol
            if context.state is InstrumentContextState.SELECTED
            and context.source == DECISION_CENTER_CONTEXT_SOURCE
            else None
        )

        self._candidates = collection.candidates
        self._table.blockSignals(True)
        self._table.clearContents()
        self._table.setRowCount(len(self._candidates))

        selected_row: int | None = None
        for row, candidate in enumerate(self._candidates):
            self._set_table_item(row, 0, candidate.symbol)
            self._set_table_item(row, 1, candidate.origin.value)
            self._set_table_item(row, 2, candidate.status.value)
            self._set_table_item(row, 3, _format_utc_timestamp(candidate.created_at))
            self._set_table_item(row, 4, _format_utc_timestamp(candidate.updated_at))
            if candidate.candidate_id.value == self._selected_candidate_id:
                selected_row = row
            elif (
                self._selected_candidate_id is None
                and candidate.symbol == context_symbol
            ):
                selected_row = row
                self._selected_candidate_id = candidate.candidate_id.value

        if selected_row is not None:
            self._table.selectRow(selected_row)
        else:
            self._selected_candidate_id = None
            self._table.clearSelection()
            if context_symbol is not None:
                self._instrument_context_service.clear_instrument(
                    DECISION_CENTER_CONTEXT_SOURCE
                )
        self._table.blockSignals(False)

        self._detail_label.setText(collection.detail)
        if collection.state is TradingCandidateCollectionState.READY:
            self._set_state("READY", "ready")
            if self._selected_candidate_id is None:
                self._set_review_status("NO SELECTION", "idle")
        elif collection.state is TradingCandidateCollectionState.EMPTY:
            self._set_state("EMPTY", "empty")
            self._set_review_status("NO SELECTION", "idle")
        elif collection.state is TradingCandidateCollectionState.ERROR:
            self._set_state("ERROR", "error")
            self._set_review_status("ERROR", "error")
        else:
            self._set_state("UNAVAILABLE", "unavailable")
            self._set_review_status("UNAVAILABLE", "unavailable")
        self._update_review_actions()

    def _publish_selected_candidate(self) -> None:
        candidate = self._candidate_for_selected_row()
        if candidate is None:
            self._selected_candidate_id = None
            self._set_review_status("NO SELECTION", "idle")
            self._update_review_actions()
            return
        self._selected_candidate_id = candidate.candidate_id.value
        self._instrument_context_service.select_instrument(
            candidate.symbol,
            DECISION_CENTER_CONTEXT_SOURCE,
        )
        self._set_review_status("READY", "ready")
        self._detail_label.setText(
            f"{candidate.symbol} is selected with status {candidate.status.value}."
        )
        self._update_review_actions()

    def _start_review(self) -> None:
        self._transition_selected_candidate(TradingCandidateStatus.REVIEWING)

    def _reject(self) -> None:
        self._transition_selected_candidate(TradingCandidateStatus.REJECTED)

    def _archive(self) -> None:
        self._transition_selected_candidate(TradingCandidateStatus.ARCHIVED)

    def _transition_selected_candidate(
        self,
        target_status: TradingCandidateStatus,
    ) -> None:
        candidate = self._selected_candidate()
        if candidate is None or self._trading_candidate_service is None:
            return
        outcome = self._trading_candidate_service.transition_candidate(
            candidate.candidate_id.value,
            target_status,
        )
        self._detail_label.setText(outcome.detail)
        if outcome.result is TradingCandidateReviewResult.UPDATED:
            self._set_review_status("UPDATED", "success")
        elif outcome.result is TradingCandidateReviewResult.INVALID_TRANSITION:
            self._set_review_status("INVALID TRANSITION", "error")
        elif outcome.result is TradingCandidateReviewResult.NOT_FOUND:
            self._set_review_status("NOT FOUND", "error")
        elif outcome.result is TradingCandidateReviewResult.CONFLICT:
            self._set_review_status("CONFLICT", "error")
        else:
            self._set_review_status("ERROR", "error")
        self._update_review_actions()

    def _candidate_for_selected_row(self) -> TradingCandidate | None:
        selected_rows = self._table.selectionModel().selectedRows()
        if not selected_rows:
            return None
        row = selected_rows[0].row()
        if row < 0 or row >= len(self._candidates):
            return None
        return self._candidates[row]

    def _selected_candidate(self) -> TradingCandidate | None:
        if self._selected_candidate_id is None:
            return None
        return next(
            (
                candidate
                for candidate in self._candidates
                if candidate.candidate_id.value == self._selected_candidate_id
            ),
            None,
        )

    def _update_review_actions(self) -> None:
        candidate = self._selected_candidate()
        review_available = (
            self._trading_candidate_service is not None and candidate is not None
        )
        self._start_review_button.setEnabled(
            review_available
            and candidate is not None
            and candidate.can_transition_to(TradingCandidateStatus.REVIEWING)
        )
        self._reject_button.setEnabled(
            review_available
            and candidate is not None
            and candidate.can_transition_to(TradingCandidateStatus.REJECTED)
        )
        self._archive_button.setEnabled(
            review_available
            and candidate is not None
            and candidate.can_transition_to(TradingCandidateStatus.ARCHIVED)
        )

    def _set_table_item(self, row: int, column: int, text: str) -> None:
        item = QTableWidgetItem(text)
        item.setTextAlignment(
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
        )
        self._table.setItem(row, column, item)

    def _set_state(self, text: str, state: str) -> None:
        self._state_label.setText(text)
        self._state_label.setProperty("decisionCenterState", state)
        self._state_label.style().unpolish(self._state_label)
        self._state_label.style().polish(self._state_label)

    def _set_review_status(self, text: str, state: str) -> None:
        self._review_status_label.setText(text)
        self._review_status_label.setProperty("candidateReviewState", state)
        self._review_status_label.style().unpolish(self._review_status_label)
        self._review_status_label.style().polish(self._review_status_label)


def _format_utc_timestamp(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S UTC")
