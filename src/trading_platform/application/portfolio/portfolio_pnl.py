from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from trading_platform.application.portfolio.portfolio_snapshot import (
    PortfolioSnapshotResult,
    PortfolioSnapshotState,
)
from trading_platform.domain.portfolio.portfolio_pnl import (
    PortfolioPnlCompleteness,
    PortfolioPnlSummary,
    calculate_portfolio_pnl,
)


class PortfolioPnlState(StrEnum):
    """Application-owned availability state for read-only position P&L."""

    UNAVAILABLE = "UNAVAILABLE"
    LOADING = "LOADING"
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class PortfolioPnlResult:
    """Application result for one read-only position P&L summary."""

    state: PortfolioPnlState
    snapshot_state: PortfolioSnapshotState
    summary: PortfolioPnlSummary | None
    source_name: str | None
    detail: str

    def __post_init__(self) -> None:
        if not isinstance(self.state, PortfolioPnlState):
            raise TypeError("state must be PortfolioPnlState")
        if not isinstance(self.snapshot_state, PortfolioSnapshotState):
            raise TypeError("snapshot_state must be PortfolioSnapshotState")
        if not isinstance(self.detail, str) or not self.detail.strip():
            raise ValueError("detail must be non-blank text")
        if self.detail != self.detail.strip():
            raise ValueError("detail must be normalized text")

        if self.state in {
            PortfolioPnlState.COMPLETE,
            PortfolioPnlState.INCOMPLETE,
        }:
            if not isinstance(self.summary, PortfolioPnlSummary):
                raise TypeError(f"{self.state.value} requires a summary")
            expected_state = (
                PortfolioPnlState.COMPLETE
                if self.summary.completeness is PortfolioPnlCompleteness.COMPLETE
                else PortfolioPnlState.INCOMPLETE
            )
            if self.state is not expected_state:
                raise ValueError("state must match summary completeness")
            if self.source_name != self.summary.source_name:
                raise ValueError("source_name must match the P&L summary")
            return

        if self.summary is not None:
            raise ValueError(f"{self.state.value} must not contain a summary")


def summarize_portfolio_pnl(
    portfolio_result: PortfolioSnapshotResult,
) -> PortfolioPnlResult:
    """Translate one Portfolio snapshot result into explicit position P&L state."""
    if not isinstance(portfolio_result, PortfolioSnapshotResult):
        raise TypeError("portfolio_result must be PortfolioSnapshotResult")

    snapshot = portfolio_result.snapshot
    if snapshot is None:
        state = {
            PortfolioSnapshotState.UNAVAILABLE: PortfolioPnlState.UNAVAILABLE,
            PortfolioSnapshotState.LOADING: PortfolioPnlState.LOADING,
            PortfolioSnapshotState.ERROR: PortfolioPnlState.ERROR,
        }.get(portfolio_result.state)
        if state is None:
            raise RuntimeError("Portfolio snapshot state requires a snapshot for P&L")
        return PortfolioPnlResult(
            state=state,
            snapshot_state=portfolio_result.state,
            summary=None,
            source_name=portfolio_result.source_name,
            detail=(
                "Position P&L is unavailable because no validated snapshot is "
                "available. Missing values are not estimated."
                if state is not PortfolioPnlState.LOADING
                else "Loading position P&L from the configured Portfolio snapshot."
            ),
        )

    summary = calculate_portfolio_pnl(snapshot)
    state = (
        PortfolioPnlState.COMPLETE
        if summary.completeness is PortfolioPnlCompleteness.COMPLETE
        else PortfolioPnlState.INCOMPLETE
    )
    if summary.total_position_count == 0:
        detail = (
            "The Portfolio contains no positions. Positive, negative and net "
            "position P&L are known zero."
        )
    elif state is PortfolioPnlState.COMPLETE:
        detail = (
            "Position P&L uses source-provided unrealized_pnl for all "
            f"{summary.total_position_count} positions. Account Unrealized P&L "
            "remains a separate source field."
        )
    else:
        detail = (
            "Position P&L is incomplete: "
            f"{summary.reported_position_count} of {summary.total_position_count} "
            "positions provide unrealized_pnl. Missing values are not estimated "
            "or reconciled against Account Unrealized P&L."
        )
    return PortfolioPnlResult(
        state=state,
        snapshot_state=portfolio_result.state,
        summary=summary,
        source_name=summary.source_name,
        detail=detail,
    )
