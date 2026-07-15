from __future__ import annotations

import os

import pytest
from PySide6.QtWidgets import QApplication, QLabel, QListWidget, QPushButton

from trading_platform.application.instruments.instrument_context import (
    InstrumentContextService,
    InstrumentContextState,
)
from trading_platform.application.watchlists.session_watchlist import (
    SessionWatchlistService,
)
from trading_platform.presentation.app.main import create_qt_application
from trading_platform.presentation.widgets.session_watchlist import (
    SessionWatchlistWidget,
)


@pytest.fixture(scope="module")
def qt_application() -> QApplication:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    return create_qt_application([])


def _label_text(widget: SessionWatchlistWidget, object_name: str) -> str:
    label = widget.findChild(QLabel, object_name)
    assert label is not None
    return label.text()


def _list_items(widget: QListWidget) -> tuple[str, ...]:
    return tuple(widget.item(index).text() for index in range(widget.count()))


def test_session_watchlist_widget_shows_empty_state(
    qt_application: QApplication,
) -> None:
    widget = SessionWatchlistWidget(
        SessionWatchlistService(),
        InstrumentContextService(),
    )
    watchlist = widget.findChild(QListWidget, "sessionWatchlistList")
    remove_button = widget.findChild(QPushButton, "sessionWatchlistRemoveButton")

    assert watchlist is not None
    assert remove_button is not None
    assert _label_text(widget, "sessionWatchlistState") == "EMPTY"
    assert watchlist.count() == 0
    assert not remove_button.isEnabled()

    widget.close()


def test_session_watchlist_widget_renders_ordered_service_state(
    qt_application: QApplication,
) -> None:
    watchlist_service = SessionWatchlistService()
    widget = SessionWatchlistWidget(
        watchlist_service,
        InstrumentContextService(),
    )
    watchlist = widget.findChild(QListWidget, "sessionWatchlistList")

    watchlist_service.add_symbol("AAPL")
    watchlist_service.add_symbol("MSFT")

    assert watchlist is not None
    assert _list_items(watchlist) == ("AAPL", "MSFT")
    assert _label_text(widget, "sessionWatchlistState") == "READY"

    widget.close()


def test_session_watchlist_selection_publishes_instrument_context(
    qt_application: QApplication,
) -> None:
    watchlist_service = SessionWatchlistService()
    context_service = InstrumentContextService()
    watchlist_service.add_symbol("AAPL")
    widget = SessionWatchlistWidget(watchlist_service, context_service)
    watchlist = widget.findChild(QListWidget, "sessionWatchlistList")

    assert watchlist is not None
    watchlist.setCurrentRow(0)

    assert context_service.context.state is InstrumentContextState.SELECTED
    assert context_service.context.symbol == "AAPL"
    assert context_service.context.source == "Watchlist"

    widget.close()


def test_removing_selected_watchlist_symbol_clears_own_context(
    qt_application: QApplication,
) -> None:
    watchlist_service = SessionWatchlistService()
    context_service = InstrumentContextService()
    watchlist_service.add_symbol("AAPL")
    widget = SessionWatchlistWidget(watchlist_service, context_service)
    watchlist = widget.findChild(QListWidget, "sessionWatchlistList")
    remove_button = widget.findChild(QPushButton, "sessionWatchlistRemoveButton")

    assert watchlist is not None
    assert remove_button is not None
    watchlist.setCurrentRow(0)
    remove_button.click()

    assert watchlist_service.watchlist.symbols == ()
    assert context_service.context.state is InstrumentContextState.NO_SELECTION
    assert context_service.context.source == "Watchlist"
    assert _label_text(widget, "sessionWatchlistActionStatus") == "REMOVED"

    widget.close()


def test_removing_watchlist_symbol_does_not_clear_other_source_context(
    qt_application: QApplication,
) -> None:
    watchlist_service = SessionWatchlistService()
    context_service = InstrumentContextService()
    watchlist_service.add_symbol("AAPL")
    widget = SessionWatchlistWidget(watchlist_service, context_service)
    watchlist = widget.findChild(QListWidget, "sessionWatchlistList")
    remove_button = widget.findChild(QPushButton, "sessionWatchlistRemoveButton")

    assert watchlist is not None
    assert remove_button is not None
    watchlist.setCurrentRow(0)
    context_service.select_instrument("MSFT", "Scanner")
    remove_button.click()

    assert context_service.context.state is InstrumentContextState.SELECTED
    assert context_service.context.symbol == "MSFT"
    assert context_service.context.source == "Scanner"

    widget.close()
