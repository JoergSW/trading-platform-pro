from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from trading_platform.application.portfolio.portfolio_snapshot import (
    PortfolioSnapshotResult,
    PortfolioSnapshotState,
)
from trading_platform.domain.risk.portfolio_exposure import (
    PortfolioExposureCompleteness,
    PortfolioExposureSummary,
    calculate_portfolio_exposure,
)


class PortfolioExposureState(StrEnum):
    """Application-owned availability state for read-only Portfolio exposure."""

    UNAVAILABLE = "UNAVAILABLE"
    LOADING = "LOADING"
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    ERROR = "ERROR"


@dataclass(frozen=True, slots=True)
class PortfolioExposureResult:
    """Application result for one Portfolio exposure summary."""

    state: PortfolioExposureState
    snapshot_state: PortfolioSnapshotState
    summary: PortfolioExposureSummary | None
    source_name: str | None
    detail: str

    def __post_init__(self) -> None:
        if not isinstance(self.state, PortfolioExposureState):
            raise TypeError("state must be PortfolioExposureState")
        if not isinstance(self.snapshot_state, PortfolioSnapshotState):
            raise TypeError("snapshot_state must be PortfolioSnapshotState")
        if not isinstance(self.detail, str) or not self.detail.strip():
            raise ValueError("detail must be non-blank text")
        if self.detail != self.detail.strip():
            raise ValueError("detail must be normalized text")

        if self.state in {
            PortfolioExposureState.COMPLETE,
            PortfolioExposureState.INCOMPLETE,
        }:
            if not isinstance(self.summary, PortfolioExposureSummary):
                raise TypeError(f"{self.state.value} requires a summary")
            expected_state = (
                PortfolioExposureState.COMPLETE
                if self.summary.completeness is PortfolioExposureCompleteness.COMPLETE
                else PortfolioExposureState.INCOMPLETE
            )
            if self.state is not expected_state:
                raise ValueError("state must match summary completeness")
            if self.source_name != self.summary.source_name:
                raise ValueError("source_name must match the exposure summary")
            return

        if self.summary is not None:
            raise ValueError(f"{self.state.value} must not contain a summary")


def summarize_portfolio_exposure(
    portfolio_result: PortfolioSnapshotResult,
) -> PortfolioExposureResult:
    """Translate one Portfolio snapshot result into explicit exposure state."""
    if not isinstance(portfolio_result, PortfolioSnapshotResult):
        raise TypeError("portfolio_result must be PortfolioSnapshotResult")

    snapshot = portfolio_result.snapshot
    if snapshot is None:
        state = {
            PortfolioSnapshotState.UNAVAILABLE: PortfolioExposureState.UNAVAILABLE,
            PortfolioSnapshotState.LOADING: PortfolioExposureState.LOADING,
            PortfolioSnapshotState.ERROR: PortfolioExposureState.ERROR,
        }.get(portfolio_result.state)
        if state is None:
            raise RuntimeError(
                "Portfolio snapshot state requires a snapshot for exposure"
            )
        return PortfolioExposureResult(
            state=state,
            snapshot_state=portfolio_result.state,
            summary=None,
            source_name=portfolio_result.source_name,
            detail=(
                "Portfolio exposure is unavailable because no validated snapshot "
                "is available. Missing values are not estimated."
                if state is not PortfolioExposureState.LOADING
                else "Loading Portfolio exposure from the configured snapshot."
            ),
        )

    summary = calculate_portfolio_exposure(snapshot)
    state = (
        PortfolioExposureState.COMPLETE
        if summary.completeness is PortfolioExposureCompleteness.COMPLETE
        else PortfolioExposureState.INCOMPLETE
    )
    if summary.total_position_count == 0:
        detail = (
            "The Portfolio contains no positions. Long, short, gross and net "
            "exposure are known zero."
        )
    elif state is PortfolioExposureState.COMPLETE:
        detail = (
            "Portfolio exposure uses source-provided current_value for all "
            f"{summary.total_position_count} positions."
        )
    else:
        detail = (
            "Portfolio exposure is incomplete: "
            f"{summary.valued_position_count} of {summary.total_position_count} "
            "positions provide current_value. Missing values are not estimated."
        )
    return PortfolioExposureResult(
        state=state,
        snapshot_state=portfolio_result.state,
        summary=summary,
        source_name=summary.source_name,
        detail=detail,
    )
