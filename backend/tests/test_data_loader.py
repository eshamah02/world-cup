import pytest
from app.data_loader import load_players, get_player, get_all_players, search_players

# Run pytest test/test_data_loader.py -v
# to test with this file


def test_players_load():
    players = get_all_players()
    assert len(players) > 0

def test_known_player_lookup():
    player = get_player(231747)
    assert player.name == "Kylian Mbappé"
    assert player.player_id == 231747
    assert player.overall_rating == 91

def test_stat_mapping():
    player = get_player(231747)
    assert player.finishing == 94
    assert player.acceleration == 97
    assert player.dribbling == 92
    assert player.sprint_speed == 96
    assert player.composure == 88
    assert player.standing_tackle == 34
    assert player.shot_power == 91
    assert player.vision == 83
    assert player.strength == 77

def test_list_fields_parse():
    player = get_player(231747)
    
    assert isinstance(player.positions, list)
    assert player.positions == ["ST", "LW", "LM"]

    assert isinstance(player.play_styles, list)
    assert "Quick step" in player.play_styles
    assert "Finesse shot" in player.play_styles

    assert isinstance(player.specialities, list)
    assert "Speedster" in player.specialities
    assert "Dribbler" in player.specialities

    assert not any (s.startswith('#') for s in player.specialities)

def test_invalid_id_raises():
    with pytest.raises(ValueError):
        get_player(9999999)

def test_search_finds_player():
    results = search_players("Mbappé")
    assert len(results) > 0

    assert any("Mbappé" in p.name for p in results)

def test_search_case_insensitive():
    results = search_players('mbappé')
    assert len(results) > 0

def test_search_no_results():
    results = search_players("ThisShouldNotMatchAnything")
    assert not results

def test_numeric_fields_are_int():
    player = get_player(231747)
    assert isinstance(player.player_id, int)
    assert isinstance(player.height_cm, int)
    assert isinstance(player.weight_kg, int)
    assert isinstance(player.overall_rating, int)
    assert isinstance(player.potential, int)
    assert isinstance(player.weak_foot, int)

def test_no_nan_leakeage():
    for player in get_all_players():
        assert player.name != 'nan'
        assert player.club_name != 'nan'
        assert player.country_name != 'nan'

def test_all_players_have_required_fields():
    for player in get_all_players():
        assert player.player_id > 0
        assert len(player.name) > 0
        assert 1 <= player.overall_rating <= 99
        assert len(player.positions) > 0
