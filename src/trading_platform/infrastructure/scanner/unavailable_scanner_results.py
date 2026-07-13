from __future__ import annotations

from trading_platform.application.scanner.scanner_results import ScannerResults


class UnavailableScannerResultsProvider:
    """Safe infrastructure adapter used until a scanner source is configured."""

    def load_results(self) -> ScannerResults:
        return ScannerResults.unavailable()
