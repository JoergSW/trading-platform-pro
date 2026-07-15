from __future__ import annotations

import pytest

from trading_platform.application.watchlists.session_watchlist import (
    SessionWatchlist,
    SessionWatchlistAddResult,
    SessionWatchlistRemoveResult,
    SessionWatchlistService,
    SessionWatchlistState,
)


def test_session_watchlist_service_defaults_to_empty() -> None:
    service = SessionWatchlistService()

    assert service.watchlist == SessionWatchlist.empty()
    assert service.watchlist.state is SessionWatchlistState.EMPTY


def test_session_watchlist_service_adds_symbols_in_explicit_order() -> None:
    service = SessionWatchlistService()

    first_result = service.add_symbol("AAPL")
    second_result = service.add_symbol("MSFT")

    assert first_result is SessionWatchlistAddResult.ADDED
    assert second_result is SessionWatchlistAddResult.ADDED
    assert service.watchlist.symbols == ("AAPL", "MSFT")
    assert service.watchlist.state is SessionWatchlistState.READY


def test_session_watchlist_service_prevents_duplicate_symbols() -> None:
    service = SessionWatchlistService()
    service.add_symbol("AAPL")

    result = service.add_symbol("AAPL")

    assert result is SessionWatchlistAddResult.ALREADY_EXISTS
    assert service.watchlist.symbols == ("AAPL",)


def test_session_watchlist_service_removes_only_requested_symbol() -> None:
    service = SessionWatchlistService()
    service.add_symbol("AAPL")
    service.add_symbol("MSFT")

    removed = service.remove_symbol("AAPL")
    missing = service.remove_symbol("NVDA")

    assert removed is SessionWatchlistRemoveResult.REMOVED
    assert missing is SessionWatchlistRemoveResult.NOT_FOUND
    assert service.watchlist.symbols == ("MSFT",)


def test_session_watchlist_service_publishes_only_content_changes() -> None:
    service = SessionWatchlistService()
    observed: list[SessionWatchlist] = []
    service.subscribe(observed.append)

    service.add_symbol("AAPL")
    service.add_symbol("AAPL")
    service.remove_symbol("NVDA")
    service.remove_symbol("AAPL")

    assert observed == [
        SessionWatchlist.empty(),
        SessionWatchlist(("AAPL",)),
        SessionWatchlist.empty(),
    ]


def test_session_watchlist_service_unsubscribes_listener() -> None:
    service = SessionWatchlistService()
    observed: list[SessionWatchlist] = []
    service.subscribe(observed.append, notify_current=False)

    assert service.unsubscribe(observed.append)
    assert not service.unsubscribe(observed.append)

    service.add_symbol("AAPL")

    assert observed == []


@pytest.mark.parametrize("symbol", ("aapl", " AAPL", "ÄAPL", "AAPL$"))
def test_session_watchlist_rejects_invalid_symbols(symbol: str) -> None:
    service = SessionWatchlistService()

    with pytest.raises(ValueError):
        service.add_symbol(symbol)
