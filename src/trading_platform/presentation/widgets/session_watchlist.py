from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import (
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from trading_platform.application.instruments.instrument_context import (
    InstrumentContextService,
    InstrumentContextState,
)
from trading_platform.application.watchlists.session_watchlist import (
    SessionWatchlist,
    SessionWatchlistListener,
    SessionWatchlistRemoveResult,
    SessionWatchlistService,
)


class SessionWatchlistWidget(QWidget):
    """Display and publish one explicit session-local watchlist selection."""

    def __init__(
        self,
        watchlist_service: SessionWatchlistService,
        instrument_context_service: InstrumentContextService,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("sessionWatchlistWidget")
        self._watchlist_service = watchlist_service
        self._instrument_context_service = instrument_context_service
        self._published_instrument_symbol: str | None = None
        self._watchlist_listener: SessionWatchlistListener = self._on_watchlist_changed

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self._state_label = QLabel(self)
        self._state_label.setObjectName("sessionWatchlistState")
        layout.addWidget(self._state_label)

        self._empty_label = QLabel(
            "Add an explicitly selected Scanner Symbol to this session.",
            self,
        )
        self._empty_label.setObjectName("sessionWatchlistEmpty")
        self._empty_label.setWordWrap(True)
        layout.addWidget(self._empty_label)

        self._list = QListWidget(self)
        self._list.setObjectName("sessionWatchlistList")
        self._list.currentTextChanged.connect(self._on_selection_changed)
        layout.addWidget(self._list, 1)

        self._remove_button = QPushButton("Remove Selected", self)
        self._remove_button.setObjectName("sessionWatchlistRemoveButton")
        self._remove_button.setEnabled(False)
        self._remove_button.clicked.connect(self.remove_selected_symbol)
        layout.addWidget(self._remove_button)

        self._action_status = QLabel("READY", self)
        self._action_status.setObjectName("sessionWatchlistActionStatus")
        layout.addWidget(self._action_status)

        self._detail_label = QLabel(
            "Session-local only. No persistence, quotes or trading actions.",
            self,
        )
        self._detail_label.setObjectName("sessionWatchlistDetail")
        self._detail_label.setWordWrap(True)
        layout.addWidget(self._detail_label)

        self._watchlist_service.subscribe(self._watchlist_listener)

    @property
    def watchlist(self) -> SessionWatchlist:
        return self._watchlist_service.watchlist

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self._watchlist_service.unsubscribe(self._watchlist_listener)
        super().closeEvent(event)

    def remove_selected_symbol(self) -> None:
        current_item = self._list.currentItem()
        if current_item is None:
            return

        symbol = current_item.text()
        result = self._watchlist_service.remove_symbol(symbol)
        self._action_status.setText(result.value)
        if result is SessionWatchlistRemoveResult.REMOVED:
            self._clear_published_instrument_context(symbol)

    def _on_watchlist_changed(self, watchlist: SessionWatchlist) -> None:
        selected_symbol = None
        current_item = self._list.currentItem()
        if current_item is not None:
            selected_symbol = current_item.text()

        self._list.blockSignals(True)
        try:
            self._list.clear()
            self._list.addItems(watchlist.symbols)
            if selected_symbol in watchlist.symbols:
                matching_items = self._list.findItems(
                    selected_symbol, Qt.MatchFlag.MatchExactly
                )
                if matching_items:
                    self._list.setCurrentItem(matching_items[0])
        finally:
            self._list.blockSignals(False)

        self._state_label.setText(watchlist.state.value)
        self._empty_label.setVisible(not watchlist.symbols)
        self._list.setVisible(bool(watchlist.symbols))
        self._remove_button.setEnabled(self._list.currentItem() is not None)

        published_symbol = self._published_instrument_symbol
        if published_symbol is not None and published_symbol not in watchlist.symbols:
            self._clear_published_instrument_context(published_symbol)

    def _on_selection_changed(self, symbol: str) -> None:
        if not symbol:
            self._remove_button.setEnabled(False)
            published_symbol = self._published_instrument_symbol
            if published_symbol is not None:
                self._clear_published_instrument_context(published_symbol)
            return

        self._remove_button.setEnabled(True)
        self._instrument_context_service.select_instrument(symbol, "Watchlist")
        self._published_instrument_symbol = symbol
        self._action_status.setText("READY")

    def _clear_published_instrument_context(self, symbol: str) -> None:
        context = self._instrument_context_service.context
        if (
            context.state is InstrumentContextState.SELECTED
            and context.source == "Watchlist"
            and context.symbol == symbol
        ):
            self._instrument_context_service.clear_instrument("Watchlist")
        if self._published_instrument_symbol == symbol:
            self._published_instrument_symbol = None
