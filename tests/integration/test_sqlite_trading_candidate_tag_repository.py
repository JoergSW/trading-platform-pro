from datetime import UTC, datetime

from trading_platform.domain.trading_candidate_tags import TradingCandidateTag
from trading_platform.domain.trading_candidates.trading_candidate import (
    TradingCandidate,
    TradingCandidateOrigin,
)
from trading_platform.infrastructure.trading_candidate_tags.sqlite_repository import (
    SqliteTradingCandidateTagRepository,
)
from trading_platform.infrastructure.trading_candidates.sqlite_repository import (
    SqliteTradingCandidateRepository,
)


def test_sqlite_candidate_tags_are_persistent_duplicate_safe_and_sorted(
    tmp_path,
) -> None:
    database_path = tmp_path / "candidates.db"
    candidate_repository = SqliteTradingCandidateRepository(database_path)
    tag_repository = SqliteTradingCandidateTagRepository(database_path)
    candidate = TradingCandidate.create_new(
        candidate_id="00000000-0000-4000-8000-000000000001",
        symbol="AAPL",
        origin=TradingCandidateOrigin.SCANNER,
        observed_at=datetime(2026, 8, 4, 12, 0, tzinfo=UTC),
    )
    candidate_repository.add(candidate)

    assert tag_repository.add(candidate.candidate_id.value, TradingCandidateTag("zeta"))
    assert tag_repository.add(
        candidate.candidate_id.value,
        TradingCandidateTag("Alpha"),
    )
    assert tag_repository.add(
        candidate.candidate_id.value,
        TradingCandidateTag("middle tag"),
    )
    assert not tag_repository.add(
        candidate.candidate_id.value,
        TradingCandidateTag(" alpha "),
    )

    reloaded_repository = SqliteTradingCandidateTagRepository(database_path)
    loaded = reloaded_repository.list_for_candidate(candidate.candidate_id.value)

    assert [tag.value for tag in loaded] == ["Alpha", "middle tag", "zeta"]
    assert reloaded_repository.remove(
        candidate.candidate_id.value,
        TradingCandidateTag("ALPHA"),
    )
    assert [
        tag.value
        for tag in reloaded_repository.list_for_candidate(candidate.candidate_id.value)
    ] == ["middle tag", "zeta"]
