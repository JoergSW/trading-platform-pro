from __future__ import annotations

from typing import Any

from trading_platform.application.diagnostics.project_analysis_report import (
    ProjectAnalysisReportService,
)
from trading_platform.application.market_data.market_snapshot import (
    MarketSnapshotService,
)
from trading_platform.infrastructure.diagnostics.project_analysis_agent import (
    ProjectAnalysisAgentReportGenerator,
)
from trading_platform.infrastructure.market_data.unavailable_market_snapshot import (
    UnavailableMarketSnapshotProvider,
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


def create_market_snapshot_service() -> MarketSnapshotService:
    """Compose the read-only Market Snapshot application service."""
    return MarketSnapshotService(UnavailableMarketSnapshotProvider())
