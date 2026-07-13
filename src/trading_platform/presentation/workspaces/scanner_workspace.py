from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from trading_platform.application.scanner.scanner_results import (
    ScannerResults,
    ScannerResultsState,
)


class ScannerWorkspaceWidget(QWidget):
    """Display one immutable, read-only Application-owned scanner result set."""

    def __init__(
        self,
        results: ScannerResults | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("scannerWorkspaceWidget")
        self._results = results or ScannerResults.unavailable()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        title = QLabel("Scanner Results", self)
        title.setObjectName("scannerWorkspaceTitle")
        header_layout.addWidget(title)

        self._state_label = QLabel(self)
        self._state_label.setObjectName("scannerWorkspaceState")
        header_layout.addWidget(self._state_label)
        header_layout.addStretch(1)
        layout.addLayout(header_layout)

        self._detail_label = QLabel(self)
        self._detail_label.setObjectName("scannerWorkspaceDetail")
        self._detail_label.setWordWrap(True)
        layout.addWidget(self._detail_label)

        cards_layout = QHBoxLayout()
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(12)
        source_card, self._source_label = self._status_card(
            "Data Source",
            "scannerWorkspaceDataSource",
        )
        cards_layout.addWidget(source_card)
        count_card, self._count_label = self._status_card(
            "Result Count",
            "scannerWorkspaceResultCount",
        )
        cards_layout.addWidget(count_card)
        layout.addLayout(cards_layout)

        table_title = QLabel("Validated Candidates", self)
        table_title.setObjectName("scannerWorkspaceTableTitle")
        layout.addWidget(table_title)

        self._empty_label = QLabel(self)
        self._empty_label.setObjectName("scannerWorkspaceEmpty")
        layout.addWidget(self._empty_label)

        self._table = QTableWidget(0, 4, self)
        self._table.setObjectName("scannerWorkspaceTable")
        self._table.setHorizontalHeaderLabels(
            ("Symbol", "Signal", "Score", "Observed (UTC)")
        )
        self._table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._table.verticalHeader().setVisible(False)
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table.setMinimumHeight(240)
        layout.addWidget(self._table, 1)

        safety_note = QLabel(
            "Read-only view. Results are loaded only from the explicitly configured "
            "local JSON source. No external connections or executable actions.",
            self,
        )
        safety_note.setObjectName("scannerWorkspaceSafetyNote")
        safety_note.setWordWrap(True)
        layout.addWidget(safety_note)

        self._apply_results(self._results)

    @property
    def results(self) -> ScannerResults:
        return self._results

    def _apply_results(self, results: ScannerResults) -> None:
        self._results = results
        self._set_state_label(
            results.state.value,
            results.state.value.lower().replace(" ", "_"),
        )
        self._detail_label.setText(results.detail)
        self._source_label.setText(results.source_name or "NOT CONFIGURED")
        self._count_label.setText(str(len(results.results)))
        self._render_table()

    def _render_table(self) -> None:
        rows = self._results.results
        self._table.setRowCount(len(rows))
        self._table.setVisible(bool(rows))
        self._empty_label.setVisible(not rows)
        self._empty_label.setText(_empty_text(self._results.state))

        for row_index, result in enumerate(rows):
            values = (
                result.symbol,
                result.signal,
                _format_score(result.score),
                _format_observed_at(result.observed_at),
            )
            for column_index, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(row_index, column_index, item)

    def _set_state_label(self, text: str, state: str) -> None:
        self._state_label.setText(text)
        _set_dynamic_property(self._state_label, "scannerState", state)

    def _status_card(
        self,
        title_text: str,
        value_object_name: str,
    ) -> tuple[QFrame, QLabel]:
        card = QFrame(self)
        card.setObjectName("scannerWorkspaceCard")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        title = QLabel(title_text, card)
        title.setObjectName("scannerWorkspaceCardTitle")
        layout.addWidget(title)

        value = QLabel(card)
        value.setObjectName(value_object_name)
        value.setWordWrap(True)
        layout.addWidget(value)
        layout.addStretch(1)

        return card, value


def _set_dynamic_property(widget: QWidget, name: str, value: str) -> None:
    widget.setProperty(name, value)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def _empty_text(state: ScannerResultsState) -> str:
    if state is ScannerResultsState.NO_DATA:
        return "The configured source returned no scanner candidates."
    if state is ScannerResultsState.UNAVAILABLE:
        return "Scanner results are unavailable."
    return "No scanner candidates are available."


def _format_score(value: Decimal) -> str:
    return format(value, "f")


def _format_observed_at(value: datetime) -> str:
    return value.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S UTC")
