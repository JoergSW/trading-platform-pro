from __future__ import annotations

from pathlib import Path
from typing import Any

from trading_platform.application.diagnostics.project_analysis_report import (
    ProjectAnalysisReportService,
)
from trading_platform.application.instruments.instrument_context import (
    InstrumentContextService,
)
from trading_platform.application.market_data.market_snapshot import (
    MarketSnapshotService,
)
from trading_platform.application.market_data.price_history import (
    PriceHistoryService,
)
from trading_platform.application.scanner.scanner_history_csv_export import (
    ScannerHistoryCsvExportService,
)
from trading_platform.application.scanner.scanner_results import ScannerResultsService
from trading_platform.application.trading_candidates.trading_candidates import (
    TradingCandidateService,
)
from trading_platform.application.trading_decisions.trading_decisions import (
    TradingDecisionService,
)
from trading_platform.application.watchlists.session_watchlist import (
    SessionWatchlistService,
)
from trading_platform.infrastructure.clock.clock import SystemClock
from trading_platform.infrastructure.diagnostics.project_analysis_agent import (
    ProjectAnalysisAgentReportGenerator,
)
from trading_platform.infrastructure.files.file_writer import FileWriter
from trading_platform.infrastructure.identity.id_generator import IdGenerator
from trading_platform.infrastructure.market_data.json_market_snapshot import (
    JsonMarketSnapshotProvider,
)
from trading_platform.infrastructure.market_data.json_price_history import (
    JsonPriceHistoryProvider,
)
from trading_platform.infrastructure.market_data.unavailable_market_snapshot import (
    UnavailableMarketSnapshotProvider,
)
from trading_platform.infrastructure.market_data.unavailable_price_history import (
    UnavailablePriceHistoryProvider,
)
from trading_platform.infrastructure.scanner.json_scanner_results import (
    JsonScannerResultsProvider,
)
from trading_platform.infrastructure.scanner.unavailable_scanner_results import (
    UnavailableScannerResultsProvider,
)
from trading_platform.infrastructure.trading_candidates.sqlite_repository import (
    SqliteTradingCandidateRepository,
)
from trading_platform.infrastructure.trading_decisions.sqlite_repository import (
    SqliteTradingDecisionRepository,
)


class CompositionRoot:
    def __init__(self) -> None:
        self._modules: list[Any] = []

    def register(self, module: Any) -> None:
        self._modules.append(module)

    def build(self, container: Any) -> None:
        for module in self._modules:
            module.register(container)


def create_project_analysis_report_service() -> ProjectAnalysisReportService:
    """Compose the reusable Project Analysis report application service."""
    return ProjectAnalysisReportService(ProjectAnalysisAgentReportGenerator())


def create_instrument_context_service() -> InstrumentContextService:
    """Compose the session-local shared instrument context service."""
    return InstrumentContextService()


def create_session_watchlist_service() -> SessionWatchlistService:
    """Compose the ordered session-local watchlist service."""
    return SessionWatchlistService()


def create_trading_candidate_service(
    database_path: Path,
) -> TradingCandidateService:
    """Compose explicit local SQLite Trading Candidate persistence."""
    return TradingCandidateService(
        SqliteTradingCandidateRepository(database_path),
        SystemClock(),
        IdGenerator(),
    )


def create_trading_decision_service(
    database_path: Path,
) -> TradingDecisionService:
    """Compose explicit local SQLite Trading Decision draft persistence."""
    return TradingDecisionService(
        SqliteTradingCandidateRepository(database_path),
        SqliteTradingDecisionRepository(database_path),
        SystemClock(),
        IdGenerator(),
    )


def create_price_history_service(
    json_history_path: Path | None = None,
) -> PriceHistoryService:
    """Compose the read-only historical price-data application service."""
    if json_history_path is None:
        return PriceHistoryService(UnavailablePriceHistoryProvider())

    return PriceHistoryService(JsonPriceHistoryProvider(json_history_path))


def create_market_snapshot_service(
    json_snapshot_path: Path | None = None,
) -> MarketSnapshotService:
    """Compose the read-only Market Snapshot application service."""
    if json_snapshot_path is None:
        return MarketSnapshotService(UnavailableMarketSnapshotProvider())

    return MarketSnapshotService(JsonMarketSnapshotProvider(json_snapshot_path))


def create_scanner_results_service(
    json_results_path: Path | None = None,
) -> ScannerResultsService:
    """Compose the read-only Scanner Results application service."""
    if json_results_path is None:
        return ScannerResultsService(UnavailableScannerResultsProvider())

    return ScannerResultsService(JsonScannerResultsProvider(json_results_path))


def create_scanner_history_csv_export_service() -> ScannerHistoryCsvExportService:
    """Compose the explicit Scanner session-history CSV export service."""
    return ScannerHistoryCsvExportService(FileWriter())
