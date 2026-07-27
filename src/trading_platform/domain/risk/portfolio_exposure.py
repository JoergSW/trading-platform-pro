from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum

from trading_platform.domain.instruments.instrument_symbol import (
    validate_instrument_symbol,
)
from trading_platform.domain.portfolio.portfolio_snapshot import PortfolioSnapshot


class PortfolioExposureCompleteness(StrEnum):
    """Whether every current Portfolio position contributes a current value."""

    COMPLETE = "COMPLETE"
    INCOMPLETE = "INCOMPLETE"


class PortfolioPositionExposureDirection(StrEnum):
    """Direction derived from one source-provided current value."""

    LONG = "LONG"
    SHORT = "SHORT"
    FLAT = "FLAT"


@dataclass(frozen=True, slots=True)
class PortfolioPositionExposure:
    """Exact exposure contribution for one Portfolio position."""

    symbol: str
    direction: PortfolioPositionExposureDirection | None
    signed_current_value: Decimal | None
    absolute_exposure: Decimal | None
    gross_exposure_share_pct: Decimal | None

    def __post_init__(self) -> None:
        validate_instrument_symbol(self.symbol)
        if self.signed_current_value is None:
            if self.direction is not None:
                raise ValueError("unvalued position exposure must not have a direction")
            if self.absolute_exposure is not None:
                raise ValueError(
                    "unvalued position exposure must not have absolute_exposure"
                )
            if self.gross_exposure_share_pct is not None:
                raise ValueError(
                    "unvalued position exposure must not have gross_exposure_share_pct"
                )
            return

        _validate_decimal(self.signed_current_value, "signed_current_value")
        if not isinstance(self.direction, PortfolioPositionExposureDirection):
            raise TypeError(
                "valued position exposure requires PortfolioPositionExposureDirection"
            )
        if self.absolute_exposure is None:
            raise ValueError("valued position exposure requires absolute_exposure")
        _validate_non_negative_decimal(self.absolute_exposure, "absolute_exposure")
        if self.absolute_exposure != abs(self.signed_current_value):
            raise ValueError("absolute_exposure must equal absolute current value")
        expected_direction = _direction_for_value(self.signed_current_value)
        if self.direction is not expected_direction:
            raise ValueError("direction must match signed_current_value")
        if self.gross_exposure_share_pct is None:
            raise ValueError(
                "valued position exposure requires gross_exposure_share_pct"
            )
        _validate_non_negative_decimal(
            self.gross_exposure_share_pct,
            "gross_exposure_share_pct",
        )
        if self.gross_exposure_share_pct > Decimal("100"):
            raise ValueError("gross_exposure_share_pct must not exceed 100")
        if self.absolute_exposure == Decimal("0"):
            if self.gross_exposure_share_pct != Decimal("0"):
                raise ValueError("zero exposure requires zero gross share")


@dataclass(frozen=True, slots=True)
class PortfolioExposureSummary:
    """Exact read-only exposure derived only from source-provided current values."""

    currency: str
    long_exposure: Decimal
    short_exposure: Decimal
    gross_exposure: Decimal
    net_exposure: Decimal
    largest_position_symbol: str | None
    largest_position_value: Decimal | None
    largest_position_concentration_pct: Decimal
    valued_position_count: int
    total_position_count: int
    completeness: PortfolioExposureCompleteness
    position_exposures: tuple[PortfolioPositionExposure, ...]
    source_name: str
    observed_at: datetime

    def __post_init__(self) -> None:
        _validate_currency(self.currency)
        _validate_non_negative_decimal(self.long_exposure, "long_exposure")
        _validate_non_negative_decimal(self.short_exposure, "short_exposure")
        _validate_non_negative_decimal(self.gross_exposure, "gross_exposure")
        _validate_decimal(self.net_exposure, "net_exposure")
        _validate_non_negative_decimal(
            self.largest_position_concentration_pct,
            "largest_position_concentration_pct",
        )
        if self.largest_position_concentration_pct > Decimal("100"):
            raise ValueError("largest_position_concentration_pct must not exceed 100")
        if self.gross_exposure != self.long_exposure + self.short_exposure:
            raise ValueError("gross_exposure must equal long plus short exposure")
        if self.net_exposure != self.long_exposure - self.short_exposure:
            raise ValueError("net_exposure must equal long minus short exposure")

        _validate_count(self.valued_position_count, "valued_position_count")
        _validate_count(self.total_position_count, "total_position_count")
        if self.valued_position_count > self.total_position_count:
            raise ValueError(
                "valued_position_count must not exceed total_position_count"
            )
        if not isinstance(self.completeness, PortfolioExposureCompleteness):
            raise TypeError("completeness must be PortfolioExposureCompleteness")
        expected_completeness = (
            PortfolioExposureCompleteness.COMPLETE
            if self.valued_position_count == self.total_position_count
            else PortfolioExposureCompleteness.INCOMPLETE
        )
        if self.completeness is not expected_completeness:
            raise ValueError("completeness must match valuation coverage")

        if not isinstance(self.position_exposures, tuple):
            raise TypeError("position_exposures must be a tuple")
        if not all(
            isinstance(position, PortfolioPositionExposure)
            for position in self.position_exposures
        ):
            raise TypeError(
                "position_exposures must contain only PortfolioPositionExposure values"
            )
        if len(self.position_exposures) != self.total_position_count:
            raise ValueError("position_exposures must match total_position_count")
        position_symbols = tuple(
            position.symbol for position in self.position_exposures
        )
        if len(position_symbols) != len(set(position_symbols)):
            raise ValueError("position_exposures must contain unique symbols")
        valued_exposure_count = sum(
            position.signed_current_value is not None
            for position in self.position_exposures
        )
        if valued_exposure_count != self.valued_position_count:
            raise ValueError("position_exposures must match valued_position_count")
        position_gross_exposure = sum(
            (
                position.absolute_exposure
                for position in self.position_exposures
                if position.absolute_exposure is not None
            ),
            Decimal("0"),
        )
        if position_gross_exposure != self.gross_exposure:
            raise ValueError("position_exposures must reconcile to gross_exposure")

        if self.largest_position_symbol is None:
            if self.largest_position_value is not None:
                raise ValueError(
                    "largest_position_value requires largest_position_symbol"
                )
            if self.largest_position_concentration_pct != Decimal("0"):
                raise ValueError("missing largest position requires zero concentration")
        else:
            validate_instrument_symbol(self.largest_position_symbol)
            if self.largest_position_value is None:
                raise ValueError(
                    "largest_position_symbol requires largest_position_value"
                )
            _validate_decimal(
                self.largest_position_value,
                "largest_position_value",
            )
            if self.largest_position_value == Decimal("0"):
                raise ValueError("largest_position_value must not be zero")
            if abs(self.largest_position_value) > self.gross_exposure:
                raise ValueError(
                    "largest_position_value must not exceed gross exposure"
                )

        _require_normalized_text(self.source_name, "source_name", max_length=200)
        _require_aware_datetime(self.observed_at, "observed_at")
        object.__setattr__(self, "observed_at", self.observed_at.astimezone(UTC))


def calculate_portfolio_exposure(
    snapshot: PortfolioSnapshot,
) -> PortfolioExposureSummary:
    """Calculate exposure from available current values without reconstruction."""
    if not isinstance(snapshot, PortfolioSnapshot):
        raise TypeError("snapshot must be PortfolioSnapshot")

    valued_positions = tuple(
        position
        for position in snapshot.positions
        if position.current_value is not None
    )
    current_values = tuple(
        position.current_value
        for position in valued_positions
        if position.current_value is not None
    )
    long_exposure = sum(
        (value for value in current_values if value > Decimal("0")),
        Decimal("0"),
    )
    short_exposure = sum(
        (-value for value in current_values if value < Decimal("0")),
        Decimal("0"),
    )
    gross_exposure = long_exposure + short_exposure
    net_exposure = long_exposure - short_exposure

    position_exposures = tuple(
        _calculate_position_exposure(
            position.symbol,
            position.current_value,
            gross_exposure,
        )
        for position in snapshot.positions
    )
    non_zero_positions = tuple(
        position
        for position in valued_positions
        if position.current_value not in {None, Decimal("0")}
    )
    largest_position = (
        max(
            non_zero_positions,
            key=lambda position: abs(position.current_value or Decimal("0")),
        )
        if non_zero_positions
        else None
    )
    largest_position_value = (
        largest_position.current_value if largest_position is not None else None
    )
    concentration = (
        abs(largest_position_value) / gross_exposure * Decimal("100")
        if largest_position_value is not None and gross_exposure > Decimal("0")
        else Decimal("0")
    )
    valued_position_count = len(valued_positions)
    total_position_count = len(snapshot.positions)
    completeness = (
        PortfolioExposureCompleteness.COMPLETE
        if valued_position_count == total_position_count
        else PortfolioExposureCompleteness.INCOMPLETE
    )

    return PortfolioExposureSummary(
        currency=snapshot.account.currency,
        long_exposure=long_exposure,
        short_exposure=short_exposure,
        gross_exposure=gross_exposure,
        net_exposure=net_exposure,
        largest_position_symbol=(
            largest_position.symbol if largest_position is not None else None
        ),
        largest_position_value=largest_position_value,
        largest_position_concentration_pct=concentration,
        valued_position_count=valued_position_count,
        total_position_count=total_position_count,
        completeness=completeness,
        position_exposures=position_exposures,
        source_name=snapshot.source_name,
        observed_at=snapshot.observed_at,
    )


def _calculate_position_exposure(
    symbol: str,
    current_value: Decimal | None,
    gross_exposure: Decimal,
) -> PortfolioPositionExposure:
    if current_value is None:
        return PortfolioPositionExposure(
            symbol=symbol,
            direction=None,
            signed_current_value=None,
            absolute_exposure=None,
            gross_exposure_share_pct=None,
        )

    absolute_exposure = abs(current_value)
    gross_share = (
        absolute_exposure / gross_exposure * Decimal("100")
        if gross_exposure > Decimal("0")
        else Decimal("0")
    )
    return PortfolioPositionExposure(
        symbol=symbol,
        direction=_direction_for_value(current_value),
        signed_current_value=current_value,
        absolute_exposure=absolute_exposure,
        gross_exposure_share_pct=gross_share,
    )


def _direction_for_value(value: Decimal) -> PortfolioPositionExposureDirection:
    if value > Decimal("0"):
        return PortfolioPositionExposureDirection.LONG
    if value < Decimal("0"):
        return PortfolioPositionExposureDirection.SHORT
    return PortfolioPositionExposureDirection.FLAT


def _validate_currency(value: str) -> None:
    _require_normalized_text(value, "currency", max_length=3)
    if len(value) != 3 or not value.isascii() or not value.isalpha():
        raise ValueError("currency must be a three-letter ASCII code")
    if value != value.upper():
        raise ValueError("currency must use uppercase characters")


def _validate_decimal(value: Decimal, field_name: str) -> None:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field_name} must be Decimal")
    if not value.is_finite():
        raise ValueError(f"{field_name} must be finite")


def _validate_non_negative_decimal(value: Decimal, field_name: str) -> None:
    _validate_decimal(value, field_name)
    if value < Decimal("0"):
        raise ValueError(f"{field_name} must not be negative")


def _validate_count(value: int, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must not be negative")


def _require_aware_datetime(value: datetime, field_name: str) -> None:
    if not isinstance(value, datetime):
        raise TypeError(f"{field_name} must be a datetime")
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must be timezone-aware")


def _require_normalized_text(
    value: str,
    field_name: str,
    *,
    max_length: int,
) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{field_name} must be normalized non-blank text")
    if len(value) > max_length:
        raise ValueError(f"{field_name} must not exceed {max_length} characters")
