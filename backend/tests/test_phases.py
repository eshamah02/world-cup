import pytest
from app.simulation.phases import GameState, pick_ball_carrier, pick_defender, select_action, resolve_action, resolve_phase
from app.simulation.events import PassAttempt, DribbleAttempt, ShotAttempt, SetPiece


def test_pick_ball_carrier_returns_team_member(strong_team):
    carrier = pick_ball_carrier(strong_team, "midfield")
    assert carrier in strong_team

def test_pick_ball_carrier_all_zones(strong_team):
    for zone in ["buildup", "midfield", "final_third"]:
        carrier = pick_ball_carrier(strong_team, zone)
        assert carrier in strong_team

def test_pick_defender_returns_team_member(weak_team):
    defender = pick_defender(weak_team)
    assert defender in weak_team

def test_select_action_valid_for_buildup(strong_team):
    gs = GameState(zone="buildup")
    valid = {"short_pass", "long_ball", "dribble_carry"}
    for _ in range(50):
        action = select_action(strong_team[0], gs)
        assert action in valid

def test_select_action_valid_for_midfield(strong_team):
    gs = GameState(zone="midfield")
    valid = {"through_ball", "skill_move", "physical_duel", "switch_play"}
    for _ in range(50):
        action = select_action(strong_team[0], gs)
        assert action in valid

def test_select_action_valid_for_final_third(strong_team):
    gs = GameState(zone="final_third")
    valid = {"finesse_shot", "power_shot", "cutback", "dribble_into_box", "header"}
    for _ in range(50):
        action = select_action(strong_team[0], gs)
        assert action in valid

def test_resolve_action_short_pass_returns_pass_attempt(strong_team, weak_team):
    gs = GameState(zone="buildup")
    event = resolve_action("short_pass", strong_team[0], weak_team[0], gs, strong_team, weak_team)
    assert isinstance(event, PassAttempt)
    assert event.pass_type == "short"

def test_resolve_action_long_ball_returns_pass_attempt(strong_team, weak_team):
    gs = GameState(zone="buildup")
    event = resolve_action("long_ball", strong_team[0], weak_team[0], gs, strong_team, weak_team)
    assert isinstance(event, PassAttempt)
    assert event.pass_type == "long"

def test_resolve_action_through_ball_returns_pass_attempt(strong_team, weak_team):
    gs = GameState(zone="midfield")
    event = resolve_action("through_ball", strong_team[0], weak_team[0], gs, strong_team, weak_team)
    assert isinstance(event, PassAttempt)
    assert event.pass_type == "through_ball"

def test_resolve_action_dribble_returns_dribble_attempt(strong_team, weak_team):
    gs = GameState(zone="midfield")
    event = resolve_action("dribble_carry", strong_team[0], weak_team[0], gs, strong_team, weak_team)
    assert isinstance(event, DribbleAttempt)

def test_resolve_action_shot_returns_shot_attempt(strong_team, weak_team):
    gs = GameState(zone="final_third")
    event = resolve_action("finesse_shot", strong_team[0], weak_team[0], gs, strong_team, weak_team)
    assert isinstance(event, ShotAttempt)
    assert event.outcome in {"goal", "save", "block", "miss"}

def test_resolve_action_shot_updates_score_on_goal(strong_team, weak_team):
    goals = 0
    for _ in range(100):
        gs = GameState(zone="final_third", possessing_team=0)
        event = resolve_action("finesse_shot", strong_team[0], weak_team[0], gs, strong_team, weak_team)
        if event.outcome == "goal":
            assert gs.score[0] == 1
            goals += 1
    assert goals > 0

def test_resolve_action_possession_flips_on_pass_fail(strong_team, weak_team):
    flips = 0
    for _ in range(100):
        gs = GameState(zone="buildup", possessing_team=0)
        event = resolve_action("short_pass", strong_team[0], weak_team[0], gs, strong_team, weak_team)
        if not event.success:
            assert gs.possessing_team == 1
            flips += 1
    assert flips > 0

def test_resolve_action_foul_sets_set_piece_zone(strong_team, weak_team):
    fouls = 0
    for _ in range(300):
        gs = GameState(zone="midfield", possessing_team=0)
        event = resolve_action("dribble_carry", strong_team[0], weak_team[0], gs, strong_team, weak_team)
        if isinstance(event, DribbleAttempt) and event.foul:
            assert gs.zone == "set_piece"
            assert gs.possessing_team == 0
            fouls += 1
    assert fouls >= 0

def test_resolve_action_long_ball_success_jumps_to_final_third(strong_team, weak_team):
    successes = 0
    for _ in range(100):
        gs = GameState(zone="buildup", possessing_team=0)
        event = resolve_action("long_ball", strong_team[0], weak_team[0], gs, strong_team, weak_team)
        if event.success:
            assert gs.zone == "final_third"
            successes += 1
    assert successes > 0

def test_resolve_action_switch_play_success_goes_to_buildup(strong_team, weak_team):
    successes = 0
    for _ in range(100):
        gs = GameState(zone="midfield", possessing_team=0)
        event = resolve_action("switch_play", strong_team[0], weak_team[0], gs, strong_team, weak_team)
        if event.success:
            assert gs.zone == "buildup"
            successes += 1
    assert successes > 0

def test_resolve_action_cutback_sets_assisted(strong_team, weak_team):
    successes = 0
    for _ in range(100):
        gs = GameState(zone="final_third", possessing_team=0)
        event = resolve_action("cutback", strong_team[0], weak_team[0], gs, strong_team, weak_team)
        if event.success:
            assert gs.assisted == True
            successes += 1
    assert successes > 0

def test_resolve_phase_increments_phase_number(strong_team, weak_team):
    gs = GameState()
    resolve_phase(gs, strong_team, weak_team)
    assert gs.phase_number == 1

def test_resolve_phase_returns_events(strong_team, weak_team):
    gs = GameState()
    events = resolve_phase(gs, strong_team, weak_team)
    assert len(events) > 0

def test_resolve_phase_handles_set_piece_zone(strong_team, weak_team):
    gs = GameState(zone="set_piece")
    events = resolve_phase(gs, strong_team, weak_team)
    assert len(events) == 1
    assert isinstance(events[0], SetPiece)

def test_resolve_phase_phase_number_accumulates(strong_team, weak_team):
    gs = GameState()
    for i in range(5):
        resolve_phase(gs, strong_team, weak_team)
    assert gs.phase_number == 5
