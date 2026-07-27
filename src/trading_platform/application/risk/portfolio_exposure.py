from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from trading_platform.application.portfolio.portfolio_snapshot import (
    PortfolioSnapshotResult,
    PortfolioSnapshotState,
)
from trading_platform.domain.risk.portfolio_exposure import (
    PortfolioExposureCompleteness,
    PortfolioExposureSummary,
    PortfolioPositionExposure,
    PortfolioPositionExposureDirection,
    calculate_portfolio_exposure,
)


class PortfolioExposureState(StrEnum):
    """Application-owned availability state for read-only Portfolio exposure."""

    UNAVAILABLE = "UNAVAILABLE"
    LOADING = "LOADING"
    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"
    ERROR = "ERROR"


class PortfolioPositionExposureState(StrEnum):
    """Application-owned valuation state for one position exposure row."""

    VALUED = "VALUED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True, slots=True)
class PortfolioPositionExposureResult:
    """Application result for one read-only position exposure contribution."""

    state: PortfolioPositionExposureState
    symbol: str
    direction: PortfolioPositionExposureDirection | None
    signed_current_value: Decimal | None
    absolute_exposure: Decimal | None
    gross_exposure_share_pct: Decimal | None
    currency: str

    def __post_init__(self) -> None:
        if not isinstance(self.state, PortfolioPositionExposureState):
            raise TypeError("state must be PortfolioPositionExposureState")
        if not isinstance(self.symbol, str) or not self.symbol.strip():
            raise ValueError("symbol must be non-blank text")
        if self.symbol != self.symbol.strip():
            raise ValueError("symbol must be normalized text")
        if not isinstance(self.currency, str) or not self.currency.strip():
            raise ValueError("currency must be non-blank text")
        if self.currency != self.currency.strip():
            raise ValueError("currency must be normalized text")

        values = (
            self.signed_current_value,
            self.absolute_exposure,
            self.gross_exposure_share_pct,
        )
        if self.state is PortfolioPositionExposureState.UNAVAILABLE:
            if self.direction is not None or any(value is not None for value in values):
                raise ValueError(
                    "UNAVAILABLE position exposure must not contain values"
                )
            return

        if not isinstance(self.direction, PortfolioPositionExposureDirection):
            raise TypeError("VALUED position exposure requires a direction")
        if any(not isinstance(value, Decimal) for value in values):
            raise TypeError("VALUED position exposure requires Decimal values")


@dataclass(frozen=True, slots=True)
class PortfolioExposureResult:
    """Application result for one Portfolio exposure summary."""

    state: PortfolioExposureState
    snapshot_state: PortfolioSnapshotState
    summary: PortfolioExposureSummary | None
    position_exposures: tuple[PortfolioPositionExposureResult, ...]
    source_name: str | None
    detail: str

    def __post_init__(self) -> None:
        if not isinstance(self.state, PortfolioExposureState):
            raise TypeError("state must be PortfolioExposureState")
        if not isinstance(self.snapshot_state, PortfolioSnapshotState):
            raise TypeError("snapshot_state must be PortfolioSnapshotState")
        if not isinstance(self.position_exposures, tuple):
            raise TypeError("position_exposures must be a tuple")
        if not all(
            isinstance(position, PortfolioPositionExposureResult)
            for position in self.position_exposures
        ):
            raise TypeError(
                "position_exposures must contain PortfolioPositionExposureResult values"
            )
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
            if len(self.position_exposures) != self.summary.total_position_count:
                raise ValueError(
                    "position_exposures must match summary total_position_count"
                )
            if tuple(position.symbol for position in self.position_exposures) != tuple(
                position.symbol for position in self.summary.position_exposures
            ):
                raise ValueError(
                    "position_exposures must preserve summary position order"
                )
            return

        if self.summary is not None:
            raise ValueError(f"{self.state.value} must not contain a summary")
        if self.position_exposures:
            raise ValueError(f"{self.state.value} must not contain position exposures")


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
            position_exposures=(),
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
        position_exposures=tuple(
            _map_position_exposure(position, summary.currency)
            for position in summary.position_exposures
        ),
        source_name=summary.source_name,
        detail=detail,
    )


def _map_position_exposure(
    position: PortfolioPositionExposure,
    currency: str,
) -> PortfolioPositionExposureResult:
    state = (
        PortfolioPositionExposureState.VALUED
        if position.signed_current_value is not None
        else PortfolioPositionExposureState.UNAVAILABLE
    )
    return PortfolioPositionExposureResult(
        state=state,
        symbol=position.symbol,
        direction=position.direction,
        signed_current_value=position.signed_current_value,
        absolute_exposure=position.absolute_exposure,
        gross_exposure_share_pct=position.gross_exposure_share_pct,
        currency=currency,
    )
