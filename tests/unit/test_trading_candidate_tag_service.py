from datetime import UTC, datetime

import pytest

from trading_platform.application.trading_candidate_tags import (
    TradingCandidateTagAddResult,
    TradingCandidateTagRemoveResult,
    TradingCandidateTags,
    TradingCandidateTagService,
    TradingCandidateTagsState,
)
from trading_platform.domain.trading_candidate_tags import TradingCandidateTag
from trading_platform.domain.trading_candidates.trading_candidate import (
    CandidateId,
    TradingCandidate,
    TradingCandidateOrigin,
    TradingCandidateStatus,
)


class CandidateRepository:
    def __init__(self, candidate: TradingCandidate | None) -> None:
        self.candidate = candidate

    def find_by_id(self, candidate_id: str) -> TradingCandidate | None:
        if self.candidate is None:
            return None
        if self.candidate.candidate_id.value != candidate_id:
            return None
        return self.candidate


class TagRepository:
    def __init__(self) -> None:
        self.tags: dict[str, TradingCandidateTag] = {}
        self.add_calls = 0
        self.remove_calls = 0

    def list_for_candidate(
        self,
        candidate_id: str,
    ) -> tuple[TradingCandidateTag, ...]:
        return tuple(reversed(tuple(self.tags.values())))

    def add(self, candidate_id: str, tag: TradingCandidateTag) -> bool:
        self.add_calls += 1
        if tag.normalized_key in self.tags:
            return False
        self.tags[tag.normalized_key] = tag
        return True

    def remove(self, candidate_id: str, tag: TradingCandidateTag) -> bool:
        self.remove_calls += 1
        return self.tags.pop(tag.normalized_key, None) is not None


def _candidate(status: TradingCandidateStatus) -> TradingCandidate:
    observed_at = datetime(2026, 8, 4, 12, 0, tzinfo=UTC)
    return TradingCandidate(
        candidate_id=CandidateId("00000000-0000-4000-8000-000000000001"),
        symbol="AAPL",
        origin=TradingCandidateOrigin.SCANNER,
        status=status,
        created_at=observed_at,
        updated_at=observed_at,
    )


def test_candidate_tag_collection_exposes_explicit_states() -> None:
    tag = TradingCandidateTag("Evidence")

    assert (
        TradingCandidateTags.unavailable("Unavailable.").state
        is TradingCandidateTagsState.UNAVAILABLE
    )
    assert TradingCandidateTags.loading().state is TradingCandidateTagsState.LOADING
    assert TradingCandidateTags.from_tags(()).state is TradingCandidateTagsState.EMPTY
    assert (
        TradingCandidateTags.from_tags((tag,)).state is TradingCandidateTagsState.READY
    )
    assert (
        TradingCandidateTags.error("Failed.").state is TradingCandidateTagsState.ERROR
    )


@pytest.mark.parametrize(
    "status",
    [TradingCandidateStatus.NEW, TradingCandidateStatus.REVIEWING],
)
def test_candidate_tags_can_be_added_removed_and_reloaded_for_open_statuses(
    status: TradingCandidateStatus,
) -> None:
    candidate = _candidate(status)
    candidate_repository = CandidateRepository(candidate)
    tag_repository = TagRepository()
    service = TradingCandidateTagService(candidate_repository, tag_repository)

    first = service.add_tag(candidate.candidate_id.value, "  zeta  ")
    second = service.add_tag(candidate.candidate_id.value, "Alpha")
    duplicate = service.add_tag(candidate.candidate_id.value, " alpha ")
    loaded = service.load_tags(candidate.candidate_id.value)
    removed = service.remove_tag(candidate.candidate_id.value, "ZETA")
    reloaded = service.load_tags(candidate.candidate_id.value)

    assert first.result is TradingCandidateTagAddResult.ADDED
    assert second.result is TradingCandidateTagAddResult.ADDED
    assert duplicate.result is TradingCandidateTagAddResult.ALREADY_EXISTS
    assert loaded.state is TradingCandidateTagsState.READY
    assert [tag.value for tag in loaded.tags] == ["Alpha", "zeta"]
    assert removed.result is TradingCandidateTagRemoveResult.REMOVED
    assert [tag.value for tag in reloaded.tags] == ["Alpha"]
    assert candidate_repository.candidate == candidate


@pytest.mark.parametrize(
    "status",
    [
        TradingCandidateStatus.REJECTED,
        TradingCandidateStatus.ACCEPTED,
        TradingCandidateStatus.ARCHIVED,
    ],
)
def test_candidate_tag_changes_are_blocked_for_closed_statuses(
    status: TradingCandidateStatus,
) -> None:
    candidate = _candidate(status)
    tag_repository = TagRepository()
    tag_repository.tags["existing"] = TradingCandidateTag("Existing")
    service = TradingCandidateTagService(
        CandidateRepository(candidate),
        tag_repository,
    )

    loaded = service.load_tags(candidate.candidate_id.value)
    added = service.add_tag(candidate.candidate_id.value, "New")
    removed = service.remove_tag(candidate.candidate_id.value, "Existing")

    assert loaded.state is TradingCandidateTagsState.READY
    assert [tag.value for tag in loaded.tags] == ["Existing"]
    assert added.result is TradingCandidateTagAddResult.NOT_ALLOWED
    assert removed.result is TradingCandidateTagRemoveResult.NOT_ALLOWED
    assert tag_repository.add_calls == 0
    assert tag_repository.remove_calls == 0


def test_candidate_tag_service_reports_missing_and_invalid_candidate() -> None:
    tag_repository = TagRepository()
    service = TradingCandidateTagService(CandidateRepository(None), tag_repository)

    missing = service.add_tag(
        "00000000-0000-4000-8000-000000000001",
        "Evidence",
    )
    invalid = service.remove_tag("not-a-candidate-id", "Evidence")
    loaded = service.load_tags("not-a-candidate-id")

    assert missing.result is TradingCandidateTagAddResult.CANDIDATE_NOT_FOUND
    assert invalid.result is TradingCandidateTagRemoveResult.INVALID
    assert loaded.state is TradingCandidateTagsState.ERROR
    assert tag_repository.add_calls == 0
    assert tag_repository.remove_calls == 0
