from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QRegularExpression, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QCloseEvent, QRegularExpressionValidator
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from trading_platform.application.scanner.scanner_results import (
    ScannerResult,
    ScannerResults,
    ScannerResultsService,
    ScannerResultsState,
)


class ScannerWorkspaceWidget(QWidget):
    """Display and refresh one read-only Application-owned scanner result set."""

    refresh_finished = Signal()

    def __init__(
        self,
        results: ScannerResults | None = None,
        parent: QWidget | None = None,
        *,
        results_service: ScannerResultsService | None = None,
        auto_refresh_seconds: int | None = None,
    ) -> None:
        super().__init__(parent)
        if auto_refresh_seconds is not None and auto_refresh_seconds <= 0:
            raise ValueError("auto_refresh_seconds must be greater than zero")
        if auto_refresh_seconds is not None and results_service is None:
            raise ValueError("auto refresh requires a scanner results service")

        self.setObjectName("scannerWorkspaceWidget")
        self._results = results or ScannerResults.unavailable()
        self._results_service = results_service
        self._auto_refresh_seconds = auto_refresh_seconds
        self._refresh_pending = False
        self._sort_column: int | None = None
        self._sort_order = Qt.SortOrder.AscendingOrder
        self._displayed_results: tuple[ScannerResult, ...] = ()

        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.setObjectName("scannerResultsAutoRefreshTimer")
        self._auto_refresh_timer.setSingleShot(False)
        self._auto_refresh_timer.timeout.connect(self.refresh_results)

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

        self._refresh_status = QLabel(self)
        self._refresh_status.setObjectName("scannerWorkspaceRefreshStatus")
        header_layout.addWidget(self._refresh_status)

        self._refresh_button = QPushButton("Refresh", self)
        self._refresh_button.setObjectName("scannerWorkspaceRefreshButton")
        self._refresh_button.setEnabled(results_service is not None)
        self._refresh_button.clicked.connect(self.refresh_results)
        header_layout.addWidget(self._refresh_button)
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
        visible_count_card, self._visible_count_label = self._status_card(
            "Visible Results",
            "scannerWorkspaceVisibleResultCount",
        )
        cards_layout.addWidget(visible_count_card)
        layout.addLayout(cards_layout)

        filters = QFrame(self)
        filters.setObjectName("scannerWorkspaceFilters")
        filters_layout = QHBoxLayout(filters)
        filters_layout.setContentsMargins(12, 10, 12, 10)
        filters_layout.setSpacing(10)

        symbol_label = QLabel("Symbol", filters)
        symbol_label.setObjectName("scannerWorkspaceFilterLabel")
        filters_layout.addWidget(symbol_label)

        self._symbol_filter = QLineEdit(filters)
        self._symbol_filter.setObjectName("scannerWorkspaceSymbolFilter")
        self._symbol_filter.setPlaceholderText("Contains...")
        self._symbol_filter.setMaxLength(32)
        self._symbol_filter.textChanged.connect(self._on_filters_changed)
        filters_layout.addWidget(self._symbol_filter, 1)

        signal_label = QLabel("Signal", filters)
        signal_label.setObjectName("scannerWorkspaceFilterLabel")
        filters_layout.addWidget(signal_label)

        self._signal_filter = QComboBox(filters)
        self._signal_filter.setObjectName("scannerWorkspaceSignalFilter")
        self._signal_filter.currentIndexChanged.connect(self._on_filters_changed)
        filters_layout.addWidget(self._signal_filter, 1)

        minimum_score_label = QLabel("Minimum Score", filters)
        minimum_score_label.setObjectName("scannerWorkspaceFilterLabel")
        filters_layout.addWidget(minimum_score_label)

        self._minimum_score_filter = QLineEdit(filters)
        self._minimum_score_filter.setObjectName("scannerWorkspaceMinimumScoreFilter")
        self._minimum_score_filter.setPlaceholderText("Any")
        self._minimum_score_filter.setMaxLength(20)
        self._minimum_score_filter.setValidator(
            QRegularExpressionValidator(
                QRegularExpression(r"(?:100(?:\.0*)?|[0-9]{1,2}(?:\.[0-9]*)?)"),
                self._minimum_score_filter,
            )
        )
        self._minimum_score_filter.textChanged.connect(self._on_filters_changed)
        filters_layout.addWidget(self._minimum_score_filter, 1)

        self._clear_filters_button = QPushButton("Clear Filters", filters)
        self._clear_filters_button.setObjectName("scannerWorkspaceClearFiltersButton")
        self._clear_filters_button.clicked.connect(self.clear_filters)
        filters_layout.addWidget(self._clear_filters_button)
        layout.addWidget(filters)

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
        table_header = self._table.horizontalHeader()
        table_header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table_header.setSectionsClickable(True)
        table_header.setSortIndicatorShown(False)
        table_header.sectionClicked.connect(self._sort_by_column)
        self._table.setMinimumHeight(240)
        self._table.currentCellChanged.connect(self._on_table_selection_changed)
        layout.addWidget(self._table, 1)

        details = QFrame(self)
        details.setObjectName("scannerWorkspaceResultDetails")
        details_layout = QGridLayout(details)
        details_layout.setContentsMargins(12, 10, 12, 10)
        details_layout.setHorizontalSpacing(18)
        details_layout.setVerticalSpacing(6)

        details_title = QLabel("Selected Result", details)
        details_title.setObjectName("scannerWorkspaceResultDetailsTitle")
        details_layout.addWidget(details_title, 0, 0, 1, 5)

        detail_fields = (
            ("Symbol", "scannerWorkspaceSelectedSymbol"),
            ("Signal", "scannerWorkspaceSelectedSignal"),
            ("Score", "scannerWorkspaceSelectedScore"),
            ("Observed (UTC)", "scannerWorkspaceSelectedObservedAt"),
            ("Data Source", "scannerWorkspaceSelectedSource"),
        )
        self._selection_detail_labels: list[QLabel] = []
        for column, (caption, object_name) in enumerate(detail_fields):
            caption_label = QLabel(caption, details)
            caption_label.setObjectName("scannerWorkspaceResultDetailsLabel")
            details_layout.addWidget(caption_label, 1, column)
            value_label = QLabel(details)
            value_label.setObjectName(object_name)
            value_label.setWordWrap(True)
            details_layout.addWidget(value_label, 2, column)
            self._selection_detail_labels.append(value_label)
        layout.addWidget(details)

        safety_note = QLabel(
            "Read-only view. Filters and sorting affect only the displayed rows. "
            "Results are loaded only from the explicitly configured local JSON "
            "source. No external connections or executable actions.",
            self,
        )
        safety_note.setObjectName("scannerWorkspaceSafetyNote")
        safety_note.setWordWrap(True)
        layout.addWidget(safety_note)

        self._apply_results(self._results)
        if results_service is None:
            self._set_refresh_status("NOT CONFIGURED", "unavailable")
        elif auto_refresh_seconds is None:
            self._set_refresh_status("IDLE", "idle")
        else:
            self._set_refresh_status(f"AUTO {auto_refresh_seconds}s", "idle")
            self._auto_refresh_timer.start(auto_refresh_seconds * 1_000)

    @property
    def results(self) -> ScannerResults:
        return self._results

    @property
    def is_refreshing(self) -> bool:
        return self._refresh_pending

    @property
    def auto_refresh_seconds(self) -> int | None:
        return self._auto_refresh_seconds

    @Slot()
    def refresh_results(self) -> None:
        if self._results_service is None or self._refresh_pending:
            return

        self._refresh_pending = True
        self._refresh_button.setEnabled(False)
        self._set_refresh_status("REFRESHING", "loading")
        QTimer.singleShot(0, self._perform_refresh)

    @Slot()
    def clear_filters(self) -> None:
        filter_widgets = (
            self._symbol_filter,
            self._signal_filter,
            self._minimum_score_filter,
        )
        for widget in filter_widgets:
            widget.blockSignals(True)
        try:
            self._symbol_filter.clear()
            self._signal_filter.setCurrentIndex(0)
            self._minimum_score_filter.clear()
        finally:
            for widget in filter_widgets:
                widget.blockSignals(False)
        self._render_table()

    def wait_for_refresh(self) -> bool:
        return not self._refresh_pending

    def closeEvent(self, event: QCloseEvent) -> None:
        self._auto_refresh_timer.stop()
        super().closeEvent(event)

    @Slot()
    def _perform_refresh(self) -> None:
        results_service = self._results_service
        if results_service is None:
            self._finish_refresh()
            return

        try:
            results = results_service.load_results()
        except Exception as exc:
            self._show_refresh_error(
                f"Scanner results refresh raised {type(exc).__name__}."
            )
        else:
            self._handle_refreshed_results(results)
        finally:
            self._finish_refresh()

    def _handle_refreshed_results(self, results: ScannerResults) -> None:
        if not isinstance(results, ScannerResults):
            self._show_refresh_error(
                "Scanner results refresh returned an invalid result set."
            )
            return

        if (
            results.state is ScannerResultsState.UNAVAILABLE
            and self._results.state is not ScannerResultsState.UNAVAILABLE
        ):
            self._show_refresh_error(results.detail)
            return

        results_changed = not _results_have_same_content(self._results, results)
        self._apply_results(results)
        if results.state is ScannerResultsState.UNAVAILABLE:
            self._set_refresh_status("ERROR", "error")
        elif results_changed:
            self._set_refresh_status("UPDATED", "success")
        else:
            self._set_refresh_status("UNCHANGED", "unchanged")

    def _finish_refresh(self) -> None:
        self._refresh_pending = False
        self._refresh_button.setEnabled(self._results_service is not None)
        self.refresh_finished.emit()

    def _show_refresh_error(self, detail: str) -> None:
        if self._results.state is ScannerResultsState.UNAVAILABLE:
            self._detail_label.setText(detail)
            self._set_refresh_status("ERROR", "error")
            return

        self._set_state_label("STALE", "stale")
        self._detail_label.setText(
            f"Refresh failed: {detail} Previous results retained and may be stale."
        )
        self._set_refresh_status("ERROR", "error")

    def _apply_results(self, results: ScannerResults) -> None:
        self._results = results
        self._set_state_label(
            results.state.value,
            results.state.value.lower().replace(" ", "_"),
        )
        self._detail_label.setText(results.detail)
        self._source_label.setText(results.source_name or "NOT CONFIGURED")
        self._count_label.setText(str(len(results.results)))
        self._update_signal_filter_options()
        self._render_table()

    def _update_signal_filter_options(self) -> None:
        selected_signal = self._signal_filter.currentData()
        available_signals = {result.signal for result in self._results.results}
        if selected_signal is not None:
            available_signals.add(selected_signal)
        signals = sorted(available_signals, key=str.casefold)

        self._signal_filter.blockSignals(True)
        try:
            self._signal_filter.clear()
            self._signal_filter.addItem("All signals", None)
            for signal in signals:
                self._signal_filter.addItem(signal, signal)
            selected_index = self._signal_filter.findData(selected_signal)
            self._signal_filter.setCurrentIndex(max(selected_index, 0))
        finally:
            self._signal_filter.blockSignals(False)

    def _on_filters_changed(self, *_: object) -> None:
        self._render_table()

    def _on_table_selection_changed(
        self,
        current_row: int,
        _current_column: int,
        _previous_row: int,
        _previous_column: int,
    ) -> None:
        if 0 <= current_row < len(self._displayed_results):
            self._show_selected_result(self._displayed_results[current_row])
        else:
            self._show_no_selection()

    def _show_selected_result(self, result: ScannerResult) -> None:
        values = (
            result.symbol,
            result.signal,
            _format_score(result.score),
            _format_observed_at(result.observed_at),
            self._results.source_name or "NOT CONFIGURED",
        )
        for label, value in zip(self._selection_detail_labels, values, strict=True):
            label.setText(value)

    def _show_no_selection(self) -> None:
        for label in self._selection_detail_labels:
            label.setText("NO SELECTION")

    def _sort_by_column(self, column: int) -> None:
        if self._sort_column == column:
            self._sort_order = (
                Qt.SortOrder.DescendingOrder
                if self._sort_order == Qt.SortOrder.AscendingOrder
                else Qt.SortOrder.AscendingOrder
            )
        else:
            self._sort_column = column
            self._sort_order = Qt.SortOrder.AscendingOrder
        self._displayed_results: tuple[ScannerResult, ...] = ()

        table_header = self._table.horizontalHeader()
        table_header.setSortIndicatorShown(True)
        table_header.setSortIndicator(column, self._sort_order)
        self._render_table()

    def _visible_results(self) -> tuple[ScannerResult, ...]:
        symbol_query = self._symbol_filter.text().strip().casefold()
        selected_signal = self._signal_filter.currentData()
        minimum_score = self._minimum_score()

        rows = tuple(
            result
            for result in self._results.results
            if (not symbol_query or symbol_query in result.symbol.casefold())
            and (selected_signal is None or result.signal == selected_signal)
            and (minimum_score is None or result.score >= minimum_score)
        )

        if self._sort_column is None:
            return rows

        key_functions = (
            lambda result: (result.symbol.casefold(), result.signal.casefold()),
            lambda result: (result.signal.casefold(), result.symbol.casefold()),
            lambda result: (result.score, result.symbol.casefold()),
            lambda result: (result.observed_at, result.symbol.casefold()),
        )
        return tuple(
            sorted(
                rows,
                key=key_functions[self._sort_column],
                reverse=self._sort_order == Qt.SortOrder.DescendingOrder,
            )
        )

    def _minimum_score(self) -> Decimal | None:
        value = self._minimum_score_filter.text().strip()
        if not value:
            return None
        try:
            return Decimal(value)
        except InvalidOperation:
            return None

    def _has_active_filters(self) -> bool:
        return bool(
            self._symbol_filter.text().strip()
            or self._signal_filter.currentData() is not None
            or self._minimum_score_filter.text().strip()
        )

    def _render_table(self) -> None:
        rows = self._visible_results()
        total_count = len(self._results.results)
        self._visible_count_label.setText(f"{len(rows)} of {total_count}")
        self._clear_filters_button.setEnabled(self._has_active_filters())
        self._displayed_results = rows
        self._table.clearSelection()
        self._show_no_selection()
        self._table.setRowCount(len(rows))
        self._table.setVisible(bool(rows))
        self._empty_label.setVisible(not rows)
        if not rows and total_count and self._has_active_filters():
            self._empty_label.setText("No scanner candidates match the active filters.")
        else:
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

    def _set_refresh_status(self, text: str, state: str) -> None:
        self._refresh_status.setText(text)
        _set_dynamic_property(self._refresh_status, "refreshState", state)

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


def _results_have_same_content(
    current: ScannerResults,
    loaded: ScannerResults,
) -> bool:
    return (
        current.state is loaded.state
        and current.source_name == loaded.source_name
        and current.results == loaded.results
    )


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
