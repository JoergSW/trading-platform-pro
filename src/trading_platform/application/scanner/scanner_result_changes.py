from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from trading_platform.application.scanner.scanner_results import (
    ScannerResult,
    ScannerResults,
    ScannerResultsState,
)


class ScannerResultChangeState(StrEnum):
    """Application-owned comparison state for one current scanner result."""

    NEW = "NEW"
    CHANGED = "CHANGED"
    UNCHANGED = "UNCHANGED"


@dataclass(frozen=True, slots=True)
class ScannerResultChange:
    """One current scanner result and its relation to the prior READY set."""

    result: ScannerResult
    state: ScannerResultChangeState
    previous_result: ScannerResult | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.result, ScannerResult):
            raise TypeError("result must be a ScannerResult")
        if not isinstance(self.state, ScannerResultChangeState):
            raise TypeError("state must be a ScannerResultChangeState")
        if self.previous_result is not None and not isinstance(
            self.previous_result,
            ScannerResult,
        ):
            raise TypeError("previous_result must be a ScannerResult or None")

        if self.state is ScannerResultChangeState.NEW:
            if self.previous_result is not None:
                raise ValueError("NEW results must not have a previous result")
            return

        if self.previous_result is None:
            raise ValueError(f"{self.state.value} results require a previous result")
        if self.previous_result.symbol != self.result.symbol:
            raise ValueError("comparison results must use the same symbol")

        content_is_equal = self.previous_result == self.result
        if self.state is ScannerResultChangeState.UNCHANGED and not content_is_equal:
            raise ValueError("UNCHANGED results must have identical content")
        if self.state is ScannerResultChangeState.CHANGED and content_is_equal:
            raise ValueError("CHANGED results must have different content")


def calculate_scanner_result_changes(
    previous: ScannerResults | None,
    current: ScannerResults,
) -> tuple[ScannerResultChange, ...]:
    """Compare current rows with the immediately prior successful READY set."""

    if previous is not None:
        _require_ready_results(previous, "previous")
    _require_ready_results(current, "current")

    previous_by_symbol = (
        {result.symbol: result for result in previous.results}
        if previous is not None
        else {}
    )
    changes: list[ScannerResultChange] = []
    for result in current.results:
        previous_result = previous_by_symbol.get(result.symbol)
        if previous_result is None:
            state = ScannerResultChangeState.NEW
        elif previous_result == result:
            state = ScannerResultChangeState.UNCHANGED
        else:
            state = ScannerResultChangeState.CHANGED
        changes.append(
            ScannerResultChange(
                result=result,
                state=state,
                previous_result=previous_result,
            )
        )
    return tuple(changes)


def _require_ready_results(results: ScannerResults, field_name: str) -> None:
    if not isinstance(results, ScannerResults):
        raise TypeError(f"{field_name} must be ScannerResults")
    if results.state is not ScannerResultsState.READY:
        raise ValueError(f"{field_name} must be READY scanner results")
