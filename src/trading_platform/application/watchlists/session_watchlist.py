from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum

from trading_platform.application.instruments.instrument_context import (
    validate_instrument_symbol,
)


class SessionWatchlistState(StrEnum):
    """Explicit content state for the current in-memory watchlist."""

    EMPTY = "EMPTY"
    READY = "READY"


class SessionWatchlistAddResult(StrEnum):
    """Deterministic outcome of one explicit add request."""

    ADDED = "ADDED"
    ALREADY_EXISTS = "ALREADY EXISTS"


class SessionWatchlistRemoveResult(StrEnum):
    """Deterministic outcome of one explicit remove request."""

    REMOVED = "REMOVED"
    NOT_FOUND = "NOT FOUND"


@dataclass(frozen=True, slots=True)
class SessionWatchlist:
    """Immutable ordered Symbol collection for one cockpit session."""

    symbols: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.symbols, tuple):
            raise TypeError("symbols must be a tuple")

        validated_symbols = tuple(
            validate_instrument_symbol(symbol) for symbol in self.symbols
        )
        if len(set(validated_symbols)) != len(validated_symbols):
            raise ValueError("session watchlist must not contain duplicate symbols")

    @property
    def state(self) -> SessionWatchlistState:
        if self.symbols:
            return SessionWatchlistState.READY
        return SessionWatchlistState.EMPTY

    @classmethod
    def empty(cls) -> SessionWatchlist:
        return cls(symbols=())


SessionWatchlistListener = Callable[[SessionWatchlist], None]


class SessionWatchlistService:
    """Own and publish one ordered, duplicate-free in-memory watchlist."""

    def __init__(self) -> None:
        self._watchlist = SessionWatchlist.empty()
        self._listeners: list[SessionWatchlistListener] = []

    @property
    def watchlist(self) -> SessionWatchlist:
        return self._watchlist

    def add_symbol(self, symbol: str) -> SessionWatchlistAddResult:
        validated_symbol = validate_instrument_symbol(symbol)
        if validated_symbol in self._watchlist.symbols:
            return SessionWatchlistAddResult.ALREADY_EXISTS

        self._set_watchlist(
            SessionWatchlist(symbols=(*self._watchlist.symbols, validated_symbol))
        )
        return SessionWatchlistAddResult.ADDED

    def remove_symbol(self, symbol: str) -> SessionWatchlistRemoveResult:
        validated_symbol = validate_instrument_symbol(symbol)
        if validated_symbol not in self._watchlist.symbols:
            return SessionWatchlistRemoveResult.NOT_FOUND

        self._set_watchlist(
            SessionWatchlist(
                symbols=tuple(
                    item for item in self._watchlist.symbols if item != validated_symbol
                )
            )
        )
        return SessionWatchlistRemoveResult.REMOVED

    def subscribe(
        self,
        listener: SessionWatchlistListener,
        *,
        notify_current: bool = True,
    ) -> None:
        if not callable(listener):
            raise TypeError("listener must be callable")
        if listener in self._listeners:
            return

        self._listeners.append(listener)
        if notify_current:
            listener(self._watchlist)

    def unsubscribe(self, listener: SessionWatchlistListener) -> bool:
        try:
            self._listeners.remove(listener)
        except ValueError:
            return False
        return True

    def _set_watchlist(self, watchlist: SessionWatchlist) -> None:
        self._watchlist = watchlist
        for listener in tuple(self._listeners):
            listener(watchlist)
