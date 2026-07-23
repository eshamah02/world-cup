import pytest
from app.simulation.engine import simulate_match
from app.models import MatchResponse, MatchEvent


def test_simulate_match_returns_match_response(strong_team, weak_team):
    result = simulate_match(strong_team, weak_team)
    assert isinstance(result, MatchResponse)

def test_simulate_match_has_events(strong_team, weak_team):
    result = simulate_match(strong_team, weak_team)
    assert len(result.events) > 0

def test_simulate_match_events_are_match_events(strong_team, weak_team):
    result = simulate_match(strong_team, weak_team)
    for event in result.events:
        assert isinstance(event, MatchEvent)

def test_simulate_match_score_is_non_negative(strong_team, weak_team):
    result = simulate_match(strong_team, weak_team)
    assert result.final_score[0] >= 0
    assert result.final_score[1] >= 0

def test_simulate_match_winner_matches_score(strong_team, weak_team):
    result = simulate_match(strong_team, weak_team)
    if result.final_score[0] > result.final_score[1]:
        assert result.winner == "team_a"
    elif result.final_score[1] > result.final_score[0]:
        assert result.winner == "team_b"
    else:
        assert result.winner is None

def test_simulate_match_mvp_is_valid_string(strong_team, weak_team):
    result = simulate_match(strong_team, weak_team)
    assert isinstance(result.mvp, str)
    assert len(result.mvp) > 0

def test_simulate_match_mvp_is_one_of_the_players(strong_team, weak_team):
    all_names = [p.name for p in strong_team + weak_team]
    result = simulate_match(strong_team, weak_team)
    assert result.mvp in all_names

def test_simulate_match_team_names(strong_team, weak_team):
    result = simulate_match(strong_team, weak_team)
    assert result.team_a_names == [p.name for p in strong_team]
    assert result.team_b_names == [p.name for p in weak_team]

def test_simulate_match_event_scores_are_lists(strong_team, weak_team):
    result = simulate_match(strong_team, weak_team)
    for event in result.events:
        assert isinstance(event.score, list)
        assert len(event.score) == 2

def test_simulate_match_event_texts_are_non_empty(strong_team, weak_team):
    result = simulate_match(strong_team, weak_team)
    for event in result.events:
        assert isinstance(event.text, str)
        assert len(event.text) > 0

def test_simulate_match_score_is_realistic(strong_team, weak_team):
    # 3v3 match should not produce cricket scores
    for _ in range(5):
        result = simulate_match(strong_team, weak_team)
        assert result.final_score[0] <= 10
        assert result.final_score[1] <= 10

def test_simulate_match_final_score_matches_last_event_score(strong_team, weak_team):
    result = simulate_match(strong_team, weak_team)
    last_score = result.events[-1].score
    assert last_score == result.final_score
