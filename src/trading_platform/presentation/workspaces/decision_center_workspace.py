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
    QPlainTextEdit,
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
from trading_platform.application.trading_decisions.trading_decisions import (
    TradingDecisionDraftCreateResult,
    TradingDecisionDraftLoadResult,
    TradingDecisionService,
)
from trading_platform.domain.trading_candidates.trading_candidate import (
    TradingCandidate,
    TradingCandidateStatus,
)
from trading_platform.domain.trading_decisions.trading_decision import TradingDecision

DECISION_CENTER_CONTEXT_SOURCE = "Decision Center"


class DecisionCenterWorkspaceWidget(QWidget):
    """Display candidates and explicitly create traceable decision drafts."""

    def __init__(
        self,
        instrument_context_service: InstrumentContextService,
        parent: QWidget | None = None,
        *,
        trading_candidate_service: TradingCandidateService | None = None,
        trading_decision_service: TradingDecisionService | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("decisionCenterWorkspaceWidget")
        self._instrument_context_service = instrument_context_service
        self._trading_candidate_service = trading_candidate_service
        self._trading_decision_service = trading_decision_service
        self._candidates: tuple[TradingCandidate, ...] = ()
        self._selected_candidate_id: str | None = None
        self._selected_decision: TradingDecision | None = None
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

        candidate_panel = QFrame(self)
        candidate_panel.setObjectName("decisionCenterCandidatePanel")
        candidate_layout = QVBoxLayout(candidate_panel)
        candidate_layout.setContentsMargins(14, 12, 14, 14)
        candidate_layout.setSpacing(10)

        review_actions = QHBoxLayout()
        review_actions.setContentsMargins(0, 0, 0, 0)
        review_actions.setSpacing(8)

        self._review_status_label = QLabel(self)
        self._review_status_label.setObjectName("decisionCenterReviewStatus")
        review_actions.addWidget(self._review_status_label)
        review_actions.addStretch(1)

        self._start_review_button = QPushButton("Start Review", candidate_panel)
        self._start_review_button.setObjectName("decisionCenterStartReviewButton")
        self._start_review_button.clicked.connect(self._start_review)
        review_actions.addWidget(self._start_review_button)

        self._reject_button = QPushButton("Reject", candidate_panel)
        self._reject_button.setObjectName("decisionCenterRejectButton")
        self._reject_button.clicked.connect(self._reject)
        review_actions.addWidget(self._reject_button)

        self._archive_button = QPushButton("Archive", candidate_panel)
        self._archive_button.setObjectName("decisionCenterArchiveButton")
        self._archive_button.clicked.connect(self._archive)
        review_actions.addWidget(self._archive_button)
        candidate_layout.addLayout(review_actions)

        self._detail_label = QLabel(candidate_panel)
        self._detail_label.setObjectName("decisionCenterDetail")
        self._detail_label.setWordWrap(True)
        candidate_layout.addWidget(self._detail_label)

        self._table = QTableWidget(candidate_panel)
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
        candidate_layout.addWidget(self._table, 1)
        layout.addWidget(candidate_panel, 1)

        decision_panel = QFrame(self)
        decision_panel.setObjectName("decisionCenterDecisionDraftPanel")
        decision_layout = QVBoxLayout(decision_panel)
        decision_layout.setContentsMargins(14, 12, 14, 14)
        decision_layout.setSpacing(8)

        decision_header = QHBoxLayout()
        decision_title = QLabel("Trading Decision Draft", decision_panel)
        decision_title.setObjectName("decisionCenterDecisionDraftTitle")
        decision_header.addWidget(decision_title)
        decision_header.addStretch(1)
        self._decision_status_label = QLabel(decision_panel)
        self._decision_status_label.setObjectName("decisionCenterDecisionDraftStatus")
        decision_header.addWidget(self._decision_status_label)
        decision_layout.addLayout(decision_header)

        self._decision_metadata_label = QLabel(decision_panel)
        self._decision_metadata_label.setObjectName(
            "decisionCenterDecisionDraftMetadata"
        )
        self._decision_metadata_label.setWordWrap(True)
        decision_layout.addWidget(self._decision_metadata_label)

        rationale_label = QLabel("Required rationale", decision_panel)
        rationale_label.setObjectName("decisionCenterDecisionRationaleLabel")
        decision_layout.addWidget(rationale_label)

        self._decision_rationale = QPlainTextEdit(decision_panel)
        self._decision_rationale.setObjectName("decisionCenterDecisionRationale")
        self._decision_rationale.setPlaceholderText(
            "Document the evidence and reasoning for this Trading Decision draft."
        )
        self._decision_rationale.setMaximumHeight(110)
        self._decision_rationale.textChanged.connect(self._update_decision_draft_action)
        decision_layout.addWidget(self._decision_rationale)

        decision_action_row = QHBoxLayout()
        self._decision_detail_label = QLabel(decision_panel)
        self._decision_detail_label.setObjectName("decisionCenterDecisionDraftDetail")
        self._decision_detail_label.setWordWrap(True)
        decision_action_row.addWidget(self._decision_detail_label, 1)

        self._create_decision_button = QPushButton(
            "Create Decision Draft",
            decision_panel,
        )
        self._create_decision_button.setObjectName(
            "decisionCenterCreateDecisionDraftButton"
        )
        self._create_decision_button.clicked.connect(self._create_decision_draft)
        decision_action_row.addWidget(self._create_decision_button)
        decision_layout.addLayout(decision_action_row)
        layout.addWidget(decision_panel)

        safety_note = QLabel(
            "Candidate review and Decision Draft only. Draft creation records "
            "rationale "
            "but does not accept the candidate, prepare an order, connect to a broker "
            "or perform a LIVE action.",
            self,
        )
        safety_note.setObjectName("decisionCenterSafetyNote")
        safety_note.setWordWrap(True)
        layout.addWidget(safety_note)

        self._set_review_status("NO SELECTION", "idle")
        self._render_decision_unavailable_or_unselected()
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
        self._load_selected_decision()

    def _publish_selected_candidate(self) -> None:
        candidate = self._candidate_for_selected_row()
        if candidate is None:
            self._selected_candidate_id = None
            self._set_review_status("NO SELECTION", "idle")
            self._update_review_actions()
            self._load_selected_decision()
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
        self._load_selected_decision()

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

    def _load_selected_decision(self) -> None:
        candidate = self._selected_candidate()
        self._selected_decision = None
        if candidate is None:
            self._render_decision_unavailable_or_unselected()
            return
        if self._trading_decision_service is None:
            self._set_decision_status("UNAVAILABLE", "unavailable")
            self._set_decision_metadata(None)
            self._set_decision_rationale("", editable=False)
            self._decision_detail_label.setText(
                "No Trading Decision persistence service is available."
            )
            self._update_decision_draft_action()
            return

        outcome = self._trading_decision_service.load_draft_for_candidate(
            candidate.candidate_id.value
        )
        self._decision_detail_label.setText(outcome.detail)
        if outcome.result is TradingDecisionDraftLoadResult.READY:
            if outcome.decision is None:
                self._set_decision_status("ERROR", "error")
                self._set_decision_metadata(None)
                self._set_decision_rationale("", editable=False)
                self._decision_detail_label.setText(
                    "Trading Decision load returned no decision."
                )
            else:
                self._render_decision(outcome.decision, status_text="DRAFT")
        elif outcome.result is TradingDecisionDraftLoadResult.NO_DRAFT:
            status = (
                "NO DRAFT"
                if candidate.status is TradingCandidateStatus.REVIEWING
                else "NOT AVAILABLE"
            )
            self._set_decision_status(status, "idle")
            self._set_decision_metadata(None)
            self._set_decision_rationale(
                "",
                editable=candidate.status is TradingCandidateStatus.REVIEWING,
            )
            self._update_decision_draft_action()
        elif outcome.result is TradingDecisionDraftLoadResult.NOT_FOUND:
            self._set_decision_status("NOT FOUND", "error")
            self._set_decision_metadata(None)
            self._set_decision_rationale("", editable=False)
            self._update_decision_draft_action()
        else:
            self._set_decision_status("ERROR", "error")
            self._set_decision_metadata(None)
            self._set_decision_rationale("", editable=False)
            self._update_decision_draft_action()

    def _create_decision_draft(self) -> None:
        candidate = self._selected_candidate()
        if candidate is None or self._trading_decision_service is None:
            return
        outcome = self._trading_decision_service.create_draft(
            candidate.candidate_id.value,
            self._decision_rationale.toPlainText(),
        )
        self._decision_detail_label.setText(outcome.detail)
        if outcome.result is TradingDecisionDraftCreateResult.CREATED:
            if outcome.decision is None:
                self._set_decision_status("ERROR", "error")
                self._decision_detail_label.setText(
                    "Trading Decision creation returned no decision."
                )
            else:
                self._render_decision(outcome.decision, status_text="CREATED")
        elif outcome.result is TradingDecisionDraftCreateResult.ALREADY_EXISTS:
            if outcome.decision is None:
                self._set_decision_status("ERROR", "error")
                self._decision_detail_label.setText(
                    "Existing Trading Decision could not be restored."
                )
            else:
                self._render_decision(
                    outcome.decision,
                    status_text="ALREADY EXISTS",
                )
        elif outcome.result is TradingDecisionDraftCreateResult.CANDIDATE_NOT_REVIEWING:
            self._set_decision_status("NOT REVIEWING", "error")
            self._update_decision_draft_action()
        elif outcome.result is TradingDecisionDraftCreateResult.NOT_FOUND:
            self._set_decision_status("NOT FOUND", "error")
            self._update_decision_draft_action()
        elif outcome.result is TradingDecisionDraftCreateResult.INVALID_RATIONALE:
            self._set_decision_status("INVALID RATIONALE", "error")
            self._update_decision_draft_action()
        else:
            self._set_decision_status("ERROR", "error")
            self._update_decision_draft_action()

    def _render_decision(
        self,
        decision: TradingDecision,
        *,
        status_text: str,
    ) -> None:
        self._selected_decision = decision
        self._set_decision_status(status_text, "success")
        self._set_decision_metadata(decision)
        self._set_decision_rationale(decision.rationale, editable=False)
        self._update_decision_draft_action()

    def _render_decision_unavailable_or_unselected(self) -> None:
        if self._trading_decision_service is None:
            status = "UNAVAILABLE"
            detail = "No Trading Decision database was explicitly configured."
        else:
            status = "NO SELECTION"
            detail = "Select a REVIEWING Trading Candidate to create or view a draft."
        self._set_decision_status(
            status, "unavailable" if status == "UNAVAILABLE" else "idle"
        )
        self._set_decision_metadata(None)
        self._set_decision_rationale("", editable=False)
        self._decision_detail_label.setText(detail)
        self._update_decision_draft_action()

    def _set_decision_metadata(self, decision: TradingDecision | None) -> None:
        if decision is None:
            self._decision_metadata_label.setText(
                "Decision ID: — | Status: — | Created UTC: — | Updated UTC: —"
            )
            return
        self._decision_metadata_label.setText(
            f"Decision ID: {decision.decision_id.value} | "
            f"Status: {decision.status.value} | "
            f"Created UTC: {_format_utc_timestamp(decision.created_at)} | "
            f"Updated UTC: {_format_utc_timestamp(decision.updated_at)}"
        )

    def _set_decision_rationale(self, text: str, *, editable: bool) -> None:
        self._decision_rationale.blockSignals(True)
        self._decision_rationale.setPlainText(text)
        self._decision_rationale.setReadOnly(not editable)
        self._decision_rationale.setEnabled(editable or bool(text))
        self._decision_rationale.blockSignals(False)

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

    def _update_decision_draft_action(self) -> None:
        candidate = self._selected_candidate()
        self._create_decision_button.setEnabled(
            self._trading_decision_service is not None
            and candidate is not None
            and candidate.status is TradingCandidateStatus.REVIEWING
            and self._selected_decision is None
            and bool(self._decision_rationale.toPlainText().strip())
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

    def _set_decision_status(self, text: str, state: str) -> None:
        self._decision_status_label.setText(text)
        self._decision_status_label.setProperty("decisionDraftState", state)
        self._decision_status_label.style().unpolish(self._decision_status_label)
        self._decision_status_label.style().polish(self._decision_status_label)


def _format_utc_timestamp(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S UTC")
