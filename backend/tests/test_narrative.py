import pytest
from app.simulation.narrative import narrate_event
from app.simulation.phases import GameState
from app.simulation.events import PassAttempt, DribbleAttempt, ShotAttempt, SetPiece, PhysicalDuel, SpecialEvent


@pytest.fixture
def gs():
    return GameState()


def test_narrate_short_pass_success(gs):
    event = PassAttempt(phase=1, zone="buildup", passer="Mbappé", target="Bellingham", pass_type="short", success=True)
    text = narrate_event(event, gs)
    assert isinstance(text, str)
    assert len(text) > 0
    assert "Mbappé" in text

def test_narrate_short_pass_fail(gs):
    event = PassAttempt(phase=1, zone="buildup", passer="Mbappé", target="teammate", pass_type="short", success=False)
    text = narrate_event(event, gs)
    assert isinstance(text, str)
    assert "Mbappé" in text

def test_narrate_through_ball_success(gs):
    event = PassAttempt(phase=1, zone="midfield", passer="Mbappé", target="Bellingham", pass_type="through_ball", success=True)
    text = narrate_event(event, gs)
    assert "Mbappé" in text
    assert "Bellingham" in text

def test_narrate_through_ball_fail(gs):
    event = PassAttempt(phase=1, zone="midfield", passer="Mbappé", target="teammate", pass_type="through_ball", success=False)
    text = narrate_event(event, gs)
    assert isinstance(text, str)
    assert len(text) > 0

def test_narrate_cutback_success(gs):
    event = PassAttempt(phase=1, zone="final_third", passer="Mbappé", target="teammate", pass_type="cutback", success=True)
    text = narrate_event(event, gs)
    assert "Mbappé" in text

def test_narrate_dribble_success(gs):
    event = DribbleAttempt(phase=1, zone="midfield", dribbler="Mbappé", defender="Van Dijk", success=True, foul=False)
    text = narrate_event(event, gs)
    assert "Mbappé" in text
    assert "Van Dijk" in text

def test_narrate_dribble_fail(gs):
    event = DribbleAttempt(phase=1, zone="midfield", dribbler="Mbappé", defender="Van Dijk", success=False, foul=False)
    text = narrate_event(event, gs)
    assert "Mbappé" in text
    assert "Van Dijk" in text

def test_narrate_dribble_foul(gs):
    event = DribbleAttempt(phase=1, zone="midfield", dribbler="Mbappé", defender="Van Dijk", success=False, foul=True)
    text = narrate_event(event, gs)
    assert "Mbappé" in text
    assert "Van Dijk" in text

def test_narrate_all_shot_outcomes(gs):
    for outcome in ["goal", "save", "block", "miss"]:
        event = ShotAttempt(phase=1, zone="final_third", shooter="Mbappé", shot_type="power_shot", quality=0.3, outcome=outcome, assister=None)
        text = narrate_event(event, gs)
        assert isinstance(text, str)
        assert len(text) > 0
        assert "Mbappé" in text

def test_narrate_set_piece_all_outcomes(gs):
    for outcome in ["goal", "save", "cleared"]:
        event = SetPiece(phase=1, zone="set_piece", taker="Mbappé", piece_type="free_kick", outcome=outcome)
        text = narrate_event(event, gs)
        assert isinstance(text, str)
        assert len(text) > 0
        assert "Mbappé" in text

def test_narrate_physical_duel(gs):
    event = PhysicalDuel(phase=1, zone="midfield", player_a="Mbappé", player_b="Van Dijk", winner="Van Dijk")
    text = narrate_event(event, gs)
    assert isinstance(text, str)
    assert "Van Dijk" in text

def test_narrate_special_brilliance(gs):
    event = SpecialEvent(phase=1, zone="midfield", player="Mbappé", special_type="brilliance", description="solo_run", resulted_in_goal=True)
    text = narrate_event(event, gs)
    assert isinstance(text, str)
    assert "Mbappé" in text

def test_narrate_special_error(gs):
    event = SpecialEvent(phase=1, zone="buildup", player="Mbappé", special_type="error", description="misplaced_backpass", resulted_in_goal=False)
    text = narrate_event(event, gs)
    assert isinstance(text, str)
    assert "Mbappé" in text

def test_narrate_never_crashes_on_any_pass_type(gs):
    for pass_type in ["short", "long", "through_ball", "switch", "cutback"]:
        for success in [True, False]:
            event = PassAttempt(phase=1, zone="midfield", passer="Mbappé", target="teammate", pass_type=pass_type, success=success)
            text = narrate_event(event, gs)
            assert isinstance(text, str)
