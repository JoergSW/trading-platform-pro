from __future__ import annotations

import csv
from collections.abc import Sequence
from datetime import UTC
from io import StringIO
from pathlib import Path
from typing import Protocol

from trading_platform.application.scanner.scanner_symbol_history import (
    ScannerSymbolHistoryEntry,
)

SCANNER_HISTORY_CSV_HEADER = (
    "Symbol",
    "Observed UTC",
    "Signal",
    "Score",
    "Change",
)


class ScannerHistoryCsvWriter(Protocol):
    """Application port for explicitly writing one rendered CSV export."""

    def write_text(self, path: Path, content: str) -> None:
        """Write the complete CSV text to the selected path."""
        ...


class ScannerHistoryCsvExportService:
    """Render and explicitly write scanner history without mutating source state."""

    def __init__(self, writer: ScannerHistoryCsvWriter) -> None:
        self._writer = writer

    def export(
        self,
        path: Path,
        entries: tuple[ScannerSymbolHistoryEntry, ...],
    ) -> int:
        if not isinstance(path, Path):
            raise TypeError("path must be a Path")
        if not isinstance(entries, tuple):
            raise TypeError("entries must be a tuple")
        if not entries:
            raise ValueError("entries must not be empty")
        if not all(isinstance(entry, ScannerSymbolHistoryEntry) for entry in entries):
            raise TypeError("entries must contain ScannerSymbolHistoryEntry values")

        self._writer.write_text(path, render_scanner_history_csv(entries))
        return len(entries)


def render_scanner_history_csv(
    entries: Sequence[ScannerSymbolHistoryEntry],
) -> str:
    """Render scanner history as deterministic UTF-8 CSV text."""

    if isinstance(entries, (str, bytes)) or not isinstance(entries, Sequence):
        raise TypeError("entries must be a sequence")
    if not all(isinstance(entry, ScannerSymbolHistoryEntry) for entry in entries):
        raise TypeError("entries must contain ScannerSymbolHistoryEntry values")

    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(SCANNER_HISTORY_CSV_HEADER)
    for entry in entries:
        result = entry.result
        writer.writerow(
            (
                _safe_csv_text(result.symbol),
                result.observed_at.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
                _safe_csv_text(result.signal),
                format(result.score, "f"),
                entry.change_state.value,
            )
        )
    return output.getvalue()


def _safe_csv_text(value: str) -> str:
    if value.startswith(("=", "+", "-", "@", "\t", "\r")):
        return f"'{value}"
    return value
