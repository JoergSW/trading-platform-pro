from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from trading_platform.application.scanner.scanner_history_csv_export import (
    SCANNER_HISTORY_CSV_HEADER,
    ScannerHistoryCsvExportService,
    render_scanner_history_csv,
)
from trading_platform.application.scanner.scanner_result_changes import (
    ScannerResultChangeState,
)
from trading_platform.application.scanner.scanner_results import ScannerResult
from trading_platform.application.scanner.scanner_symbol_history import (
    ScannerSymbolHistoryEntry,
)
from trading_platform.composition.composition_root import (
    create_scanner_history_csv_export_service,
)


class RecordingWriter:
    def __init__(self) -> None:
        self.path: Path | None = None
        self.content: str | None = None

    def write_text(self, path: Path, content: str) -> None:
        self.path = path
        self.content = content


def _entry(
    symbol: str = "AAPL",
    *,
    signal: str = "BREAKOUT",
    score: str = "94.5",
    observed_at: datetime | None = None,
    change_state: ScannerResultChangeState = ScannerResultChangeState.NEW,
) -> ScannerSymbolHistoryEntry:
    return ScannerSymbolHistoryEntry(
        ScannerResult(
            symbol=symbol,
            signal=signal,
            score=Decimal(score),
            observed_at=(observed_at or datetime(2026, 7, 14, 12, 0, tzinfo=UTC)),
        ),
        change_state,
    )


def test_render_scanner_history_csv_has_deterministic_header_and_rows() -> None:
    content = render_scanner_history_csv(
        (
            _entry(),
            _entry(
                "MSFT",
                signal="MOMENTUM",
                score="88",
                observed_at=datetime(2026, 7, 14, 12, 1, tzinfo=UTC),
                change_state=ScannerResultChangeState.UNCHANGED,
            ),
        )
    )

    assert content.splitlines() == [
        ",".join(SCANNER_HISTORY_CSV_HEADER),
        "AAPL,2026-07-14T12:00:00Z,BREAKOUT,94.5,NEW",
        "MSFT,2026-07-14T12:01:00Z,MOMENTUM,88,UNCHANGED",
    ]


def test_render_scanner_history_csv_neutralizes_formula_like_text() -> None:
    content = render_scanner_history_csv((_entry(signal="=HYPERLINK(1)"),))

    assert "'=HYPERLINK(1)" in content


def test_export_service_writes_complete_csv_and_returns_row_count() -> None:
    writer = RecordingWriter()
    service = ScannerHistoryCsvExportService(writer)
    path = Path("exports/scanner.csv")
    entries = (_entry(),)

    row_count = service.export(path, entries)

    assert row_count == 1
    assert writer.path == path
    assert writer.content == render_scanner_history_csv(entries)


def test_export_service_rejects_empty_history() -> None:
    service = ScannerHistoryCsvExportService(RecordingWriter())

    with pytest.raises(ValueError, match="must not be empty"):
        service.export(Path("scanner.csv"), ())


def test_composed_export_service_writes_utf8_csv(tmp_path: Path) -> None:
    path = tmp_path / "nested" / "scanner.csv"

    row_count = create_scanner_history_csv_export_service().export(path, (_entry(),))

    assert row_count == 1
    assert path.read_text(encoding="utf-8").splitlines()[1] == (
        "AAPL,2026-07-14T12:00:00Z,BREAKOUT,94.5,NEW"
    )
