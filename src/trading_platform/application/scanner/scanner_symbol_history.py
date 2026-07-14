from __future__ import annotations

from dataclasses import dataclass

from trading_platform.application.scanner.scanner_result_changes import (
    ScannerResultChange,
    ScannerResultChangeState,
)
from trading_platform.application.scanner.scanner_results import ScannerResult

DEFAULT_SCANNER_SYMBOL_HISTORY_LIMIT = 20


@dataclass(frozen=True, slots=True)
class ScannerSymbolHistoryEntry:
    """One successful scanner observation and its comparison state."""

    result: ScannerResult
    change_state: ScannerResultChangeState

    def __post_init__(self) -> None:
        if not isinstance(self.result, ScannerResult):
            raise TypeError("result must be a ScannerResult")
        if not isinstance(self.change_state, ScannerResultChangeState):
            raise TypeError("change_state must be a ScannerResultChangeState")


class ScannerSymbolHistory:
    """Bounded in-memory history for each symbol in successful READY updates."""

    def __init__(
        self,
        max_entries_per_symbol: int = DEFAULT_SCANNER_SYMBOL_HISTORY_LIMIT,
    ) -> None:
        if isinstance(max_entries_per_symbol, bool) or not isinstance(
            max_entries_per_symbol,
            int,
        ):
            raise TypeError("max_entries_per_symbol must be an integer")
        if max_entries_per_symbol <= 0:
            raise ValueError("max_entries_per_symbol must be greater than zero")

        self._max_entries_per_symbol = max_entries_per_symbol
        self._entries_by_symbol: dict[str, list[ScannerSymbolHistoryEntry]] = {}

    @property
    def max_entries_per_symbol(self) -> int:
        return self._max_entries_per_symbol

    def entries_for(self, symbol: str) -> tuple[ScannerSymbolHistoryEntry, ...]:
        """Return the selected symbol history newest first."""

        if not isinstance(symbol, str):
            raise TypeError("symbol must be a string")
        return tuple(self._entries_by_symbol.get(symbol, ()))

    def all_entries(self) -> tuple[ScannerSymbolHistoryEntry, ...]:
        """Return all session entries newest first and Symbol-stable on ties."""

        entries = [
            entry
            for symbol_entries in self._entries_by_symbol.values()
            for entry in symbol_entries
        ]
        entries.sort(key=lambda entry: entry.result.symbol)
        entries.sort(key=lambda entry: entry.result.observed_at, reverse=True)
        return tuple(entries)

    def record_changes(
        self,
        changes: tuple[ScannerResultChange, ...],
    ) -> tuple[ScannerSymbolHistoryEntry, ...]:
        """Record one successful READY update and return the created entries."""

        if not isinstance(changes, tuple):
            raise TypeError("changes must be a tuple")
        if not all(isinstance(change, ScannerResultChange) for change in changes):
            raise TypeError("changes must contain only ScannerResultChange values")

        symbols = [change.result.symbol for change in changes]
        if len(symbols) != len(set(symbols)):
            raise ValueError("changes must contain unique symbols")

        recorded: list[ScannerSymbolHistoryEntry] = []
        for change in changes:
            entry = ScannerSymbolHistoryEntry(
                result=change.result,
                change_state=change.state,
            )
            entries = self._entries_by_symbol.setdefault(change.result.symbol, [])
            entries.insert(0, entry)
            del entries[self._max_entries_per_symbol :]
            recorded.append(entry)
        return tuple(recorded)
