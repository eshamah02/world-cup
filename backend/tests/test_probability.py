import pytest
from app.simulation.probability import compute_composite, success_probability, roll, shot_quality, special_event_check
from app.player_profile import PlayerProfile
from app.data_loader import get_player, load_players

@pytest.fixture
def avg_player():
    p = get_player(231747)
    p.finishing = 90
    p.shot_power = 80
    p.composure = 70
    return p

@pytest.fixture
def elite_player():
    p = get_player(231747)
    p.overall = 91
    p.skill_moves = 5
    p.composure = 88
    return p

def test_compute_composite(avg_player):
    composite_no_weights = compute_composite(avg_player, ['finishing', 'shot_power', 'composure'])
    assert composite_no_weights == 80
    composite_weights = compute_composite(avg_player, ['finishing', 'shot_power', 'composure'], [0.5, 0.3, 0.2])
    assert composite_weights == 83.0

def test_compute_composite_single_stat(avg_player):
    composite = compute_composite(avg_player, ['finishing'])
    assert composite == 90

def test_success_probability_equal_matchup():
    res = []
    for i in range(1000):
        res.append(success_probability(80, 80))
    assert(0.05 <= i <= 0.95 for i in res)
    assert(0.45 <= sum(res) / 1000 <= 0.55)

def test_success_probability_dominant_attacker():
    res = success_probability(90, 60)
    assert(0.55 <= res <= 0.65)

def test_success_probability_clamping():
    max_clamp = success_probability(99, 1)
    assert(max_clamp == 0.95)
    min_clamp = success_probability(1, 99)
    assert(min_clamp == 0.05)

def test_roll_always_true():
    for i in range(100):
        assert(roll(1.0) == True)
        assert(roll(0.0) == False)

def test_roll_distribution():
    res = []
    for i in range(10000):
        res.append(roll(0.7))

    assert(6500 <= res.count(True) <= 7500)

def test_shot_quality_values(avg_player):
    avg_player.finishing = 80
    assert(shot_quality("through_ball", avg_player) == 0.35)
    assert(shot_quality("long_shot", avg_player) == 0.08)
    avg_player.finishing = 100
    assert(shot_quality("through_ball", avg_player) == 0.4375)
    avg_player.finishing = 40
    assert(shot_quality("through_ball", avg_player) == 0.175)

def test_special_event_check_rates(avg_player, elite_player):
    elite_res = []
    for i in range(10000):
        elite_res.append(special_event_check(elite_player, "brilliance"))
    assert(610 <= elite_res.count(True) <= 910)

    avg_player.composure = 65
    avg_player.ball_control = 70
    avg_res = []
    for i in range(10000):
        avg_res.append(special_event_check(avg_player, "error"))
    assert(120 <= avg_res.count(True) <= 320)

def test_special_event_check_invalid_type(avg_player):
    with pytest.raises(Exception):
        special_event_check(avg_player, "invalid_type") 
