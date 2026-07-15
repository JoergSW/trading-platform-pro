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
    TradingCandidateService,
)
from trading_platform.domain.trading_candidates.trading_candidate import (
    TradingCandidate,
)

DECISION_CENTER_CONTEXT_SOURCE = "Decision Center"


class DecisionCenterWorkspaceWidget(QWidget):
    """Display persistent Trading Candidates without creating trading decisions."""

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
            "Candidate review foundation only. Selecting a row publishes instrument "
            "context; it does not create a Trading Decision, prepare an order, connect "
            "to a broker or perform a LIVE action.",
            self,
        )
        safety_note.setObjectName("decisionCenterSafetyNote")
        safety_note.setWordWrap(True)
        layout.addWidget(safety_note)

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
        selected_symbol = (
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
            if candidate.symbol == selected_symbol:
                selected_row = row

        if selected_row is not None:
            self._table.selectRow(selected_row)
        else:
            self._table.clearSelection()
        self._table.blockSignals(False)

        self._detail_label.setText(collection.detail)
        if collection.state is TradingCandidateCollectionState.READY:
            self._set_state("READY", "ready")
        elif collection.state is TradingCandidateCollectionState.EMPTY:
            self._set_state("EMPTY", "empty")
            if selected_symbol is not None:
                self._instrument_context_service.clear_instrument(
                    DECISION_CENTER_CONTEXT_SOURCE
                )
        elif collection.state is TradingCandidateCollectionState.ERROR:
            self._set_state("ERROR", "error")
        else:
            self._set_state("UNAVAILABLE", "unavailable")

    def _publish_selected_candidate(self) -> None:
        selected_rows = self._table.selectionModel().selectedRows()
        if not selected_rows:
            return
        row = selected_rows[0].row()
        if row < 0 or row >= len(self._candidates):
            return
        candidate = self._candidates[row]
        self._instrument_context_service.select_instrument(
            candidate.symbol,
            DECISION_CENTER_CONTEXT_SOURCE,
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


def _format_utc_timestamp(value: datetime) -> str:
    return value.strftime("%Y-%m-%d %H:%M:%S UTC")
