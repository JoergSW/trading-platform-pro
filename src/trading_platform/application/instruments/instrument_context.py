from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum


class InstrumentContextState(StrEnum):
    """Explicit selection state shared by compatible cockpit workspaces."""

    NO_SELECTION = "NO SELECTION"
    SELECTED = "SELECTED"


@dataclass(frozen=True, slots=True)
class InstrumentContext:
    """Immutable session-local active-instrument context."""

    state: InstrumentContextState
    symbol: str | None
    source: str | None

    def __post_init__(self) -> None:
        if not isinstance(self.state, InstrumentContextState):
            raise TypeError("state must be an InstrumentContextState")

        if self.state is InstrumentContextState.SELECTED:
            _validate_symbol(self.symbol)
            _require_normalized_text(self.source, "source", max_length=64)
            return

        if self.symbol is not None:
            raise ValueError(
                "NO SELECTION instrument context must not contain a symbol"
            )
        if self.source is not None:
            _require_normalized_text(self.source, "source", max_length=64)

    @classmethod
    def no_selection(cls, source: str | None = None) -> InstrumentContext:
        return cls(
            state=InstrumentContextState.NO_SELECTION,
            symbol=None,
            source=source,
        )

    @classmethod
    def selected(cls, symbol: str, source: str) -> InstrumentContext:
        return cls(
            state=InstrumentContextState.SELECTED,
            symbol=symbol,
            source=source,
        )


InstrumentContextListener = Callable[[InstrumentContext], None]


class InstrumentContextService:
    """Own and publish one observable in-memory instrument context."""

    def __init__(self) -> None:
        self._context = InstrumentContext.no_selection()
        self._listeners: list[InstrumentContextListener] = []

    @property
    def context(self) -> InstrumentContext:
        return self._context

    def select_instrument(self, symbol: str, source: str) -> InstrumentContext:
        return self._set_context(InstrumentContext.selected(symbol, source))

    def clear_instrument(self, source: str) -> InstrumentContext:
        return self._set_context(InstrumentContext.no_selection(source))

    def subscribe(
        self,
        listener: InstrumentContextListener,
        *,
        notify_current: bool = True,
    ) -> None:
        if not callable(listener):
            raise TypeError("listener must be callable")
        if listener in self._listeners:
            return

        self._listeners.append(listener)
        if notify_current:
            listener(self._context)

    def unsubscribe(self, listener: InstrumentContextListener) -> bool:
        try:
            self._listeners.remove(listener)
        except ValueError:
            return False
        return True

    def _set_context(self, context: InstrumentContext) -> InstrumentContext:
        if context == self._context:
            return self._context

        self._context = context
        for listener in tuple(self._listeners):
            listener(context)
        return context


def _validate_symbol(value: str | None) -> None:
    _require_normalized_text(value, "symbol", max_length=32)
    assert isinstance(value, str)
    if not value.isascii():
        raise ValueError("symbol must use ASCII characters")
    if value != value.upper():
        raise ValueError("symbol must use uppercase characters")
    if not all(character.isalnum() or character in ".-/^" for character in value):
        raise ValueError("symbol contains unsupported characters")


def _require_normalized_text(
    value: str | None,
    field_name: str,
    *,
    max_length: int,
) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be normalized non-blank text")
    if len(value) > max_length:
        raise ValueError(f"{field_name} must not exceed {max_length} characters")
