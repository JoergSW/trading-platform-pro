from __future__ import annotations

import pytest

from trading_platform.application.instruments.instrument_context import (
    InstrumentContext,
    InstrumentContextService,
    InstrumentContextState,
)


def test_instrument_context_service_defaults_to_no_selection() -> None:
    service = InstrumentContextService()

    assert service.context == InstrumentContext.no_selection()
    assert service.context.state is InstrumentContextState.NO_SELECTION


def test_instrument_context_service_publishes_selection_and_clear() -> None:
    service = InstrumentContextService()
    observed: list[InstrumentContext] = []
    service.subscribe(observed.append)

    selected = service.select_instrument("AAPL", "Scanner")
    cleared = service.clear_instrument("Scanner")

    assert observed == [
        InstrumentContext.no_selection(),
        selected,
        cleared,
    ]
    assert selected == InstrumentContext.selected("AAPL", "Scanner")
    assert cleared == InstrumentContext.no_selection("Scanner")
    assert service.context is cleared


def test_instrument_context_service_does_not_republish_unchanged_context() -> None:
    service = InstrumentContextService()
    observed: list[InstrumentContext] = []
    service.subscribe(observed.append, notify_current=False)

    service.select_instrument("AAPL", "Scanner")
    service.select_instrument("AAPL", "Scanner")

    assert observed == [InstrumentContext.selected("AAPL", "Scanner")]


def test_instrument_context_service_unsubscribes_listener() -> None:
    service = InstrumentContextService()
    observed: list[InstrumentContext] = []
    service.subscribe(observed.append, notify_current=False)

    assert service.unsubscribe(observed.append)
    assert not service.unsubscribe(observed.append)

    service.select_instrument("AAPL", "Scanner")

    assert observed == []


@pytest.mark.parametrize(
    ("symbol", "error_type", "message"),
    (
        ("aapl", ValueError, "uppercase"),
        (" AAPL", ValueError, "normalized"),
        ("ÄAPL", ValueError, "ASCII"),
        ("AAPL$", ValueError, "unsupported"),
        (None, TypeError, "symbol must be a string"),
    ),
)
def test_selected_instrument_context_rejects_invalid_symbols(
    symbol: str | None,
    error_type: type[Exception],
    message: str,
) -> None:
    with pytest.raises(error_type, match=message):
        InstrumentContext.selected(symbol, "Scanner")  # type: ignore[arg-type]


def test_selected_instrument_context_requires_normalized_source() -> None:
    with pytest.raises(ValueError, match="source must be normalized"):
        InstrumentContext.selected("AAPL", " Scanner")
