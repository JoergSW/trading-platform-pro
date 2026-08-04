import pytest

from trading_platform.domain.trading_candidate_tags import (
    MAX_TRADING_CANDIDATE_TAG_LENGTH,
    TradingCandidateTag,
)


def test_candidate_tag_normalizes_whitespace_and_preserves_display_case() -> None:
    tag = TradingCandidateTag("  High\t  Conviction  ")

    assert tag.value == "High Conviction"
    assert tag.normalized_key == "high conviction"


def test_candidate_tag_accepts_maximum_length() -> None:
    tag = TradingCandidateTag("x" * MAX_TRADING_CANDIDATE_TAG_LENGTH)

    assert len(tag.value) == MAX_TRADING_CANDIDATE_TAG_LENGTH


@pytest.mark.parametrize(
    "value",
    ["", "   ", "x" * (MAX_TRADING_CANDIDATE_TAG_LENGTH + 1)],
)
def test_candidate_tag_rejects_invalid_value(value: str) -> None:
    with pytest.raises(ValueError):
        TradingCandidateTag(value)
