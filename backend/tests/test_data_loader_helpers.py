import random

from app.data_loader import (
    get_all_players,
    get_player,
    filter_players,
    to_summary,
    to_detail,
    resolve_random_entries,
)
from app.models import PlayerSummary, PlayerDetail

# Run: pytest tests/test_data_loader_helpers.py -v   (from backend/)

MBAPPE = 231747


# ---------- filter_players ----------

def test_filter_no_filters_returns_all():
    players = get_all_players()
    assert len(filter_players(players)) == len(players)


def test_filter_query_substring_matches_name_club_or_country():
    players = get_all_players()
    result = filter_players(players, query="mbappé")
    assert len(result) > 0
    for p in result:
        hay = " ".join([
            p.name.lower(),
            p.club_name.lower() if isinstance(p.club_name, str) else "",
            p.country_name.lower() if isinstance(p.country_name, str) else "",
        ])
        assert "mbappé" in hay


def test_filter_position_membership():
    players = get_all_players()
    result = filter_players(players, position="ST")
    assert len(result) > 0
    assert all("ST" in p.positions for p in result)


def test_filter_country_exact_case_insensitive():
    players = get_all_players()
    result = filter_players(players, country="france")
    assert len(result) > 0
    assert all(
        isinstance(p.country_name, str) and p.country_name.lower() == "france"
        for p in result
    )


def test_filter_club_exact_case_insensitive():
    players = get_all_players()
    club = get_player(MBAPPE).club_name
    result = filter_players(players, club=club.lower())
    assert len(result) > 0
    assert all(
        isinstance(p.club_name, str) and p.club_name.lower() == club.lower()
        for p in result
    )


def test_filter_rating_range_inclusive():
    players = get_all_players()
    result = filter_players(players, min_rating=85, max_rating=90)
    assert len(result) > 0
    assert all(85 <= p.overall_rating <= 90 for p in result)


def test_filter_conjunction_all_predicates_apply():
    players = get_all_players()
    result = filter_players(players, position="ST", min_rating=88)
    assert len(result) > 0
    for p in result:
        assert "ST" in p.positions
        assert p.overall_rating >= 88


def test_filter_no_match_returns_empty():
    players = get_all_players()
    assert filter_players(players, query="zzzzz-no-such-player-xyz") == []


# ---------- to_summary ----------

def test_to_summary_maps_fields():
    p = get_player(MBAPPE)
    s = to_summary(p)
    assert isinstance(s, PlayerSummary)
    assert s.player_id == p.player_id
    assert s.name == p.name
    assert s.image == p.image
    assert s.overall_rating == p.overall_rating
    assert isinstance(s.overall_rating, int)
    assert s.club_name == p.club_name
    assert s.country_name == p.country_name
    assert s.positions == p.positions


# ---------- to_detail ----------

def test_to_detail_populates_all_curated_groups():
    p = get_player(MBAPPE)
    d = to_detail(p)
    assert isinstance(d, PlayerDetail)
    assert d.player_id == p.player_id
    assert d.full_name == p.full_name
    assert isinstance(d.overall_rating, int)
    for group in (d.pace, d.shooting, d.passing, d.dribbling, d.defending, d.physical):
        assert len(group) > 0
        assert all(isinstance(v, int) for v in group.values())
    assert d.pace["sprint_speed"] == p.sprint_speed
    assert d.shooting["finishing"] == p.finishing
    assert d.defending["standing_tackle"] == p.standing_tackle


# ---------- resolve_random_entries ----------

def _valid_ids():
    return {p.player_id for p in get_all_players()}


def test_resolve_all_explicit_preserves_order():
    entries = [231747, 237692, 238794, 192985, 188545, 212198]
    assert resolve_random_entries(entries) == entries


def test_resolve_all_random_distinct_and_valid():
    random.seed(0)
    valid = _valid_ids()
    result = resolve_random_entries(["random"] * 6)
    assert len(result) == 6
    assert len(set(result)) == 6
    assert all(pid in valid for pid in result)


def test_resolve_mixed_distinct_and_preserves_explicit():
    random.seed(1)
    valid = _valid_ids()
    explicit = [231747, 237692, 238794]
    entries = [231747, "random", 237692, "random", 238794, "random"]
    result = resolve_random_entries(entries)
    assert len(result) == 6
    assert len(set(result)) == 6
    assert all(pid in valid for pid in result)
    assert result[0] == 231747 and result[2] == 237692 and result[4] == 238794
    randoms = [result[1], result[3], result[5]]
    assert all(r not in explicit for r in randoms)
