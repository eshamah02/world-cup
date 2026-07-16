import random
from dataclasses import dataclass, field
from app.player_profile import PlayerProfile
from app.simulation.probability import compute_composite, success_probability, roll, shot_quality, special_event_check
from app.simulation.events import PossessionChange, PassAttempt, DribbleAttempt, ShotAttempt, SetPiece, PhysicalDuel, SpecialEvent, GameEvent



@dataclass
class GameState:
    zone: str = "midfield" # buildup, midfield, final_third, set_piece
    possessing_team: int = 0 # 0 or 1 for team a and b respectively
    score: list[int] = field(default_factory=lambda: [0, 0]) # team a goals, team b goals
    phase_number: int = 0
    total_phases: int = 25
    momentum: list[int] = field(default_factory=lambda: [0, 0]) # consecutive possession phases per team
    last_event: str = "" # pass, dribble, shot
    assisted: bool = False # did a cutback just happen? if so next shot gets quality boost
    set_piece_team: str = "" # which team was fouled?



def pick_ball_carrier(team: list[PlayerProfile], zone: str) -> PlayerProfile:
    stats_per_zone = {
        "buildup": ["ball_control", "short_passing"],
        "midfield": ["vision", "dribbling", "short_passing"],
        "final_third": ["finishing", "dribbling", "attack_position"]
    }
    weights = [0] * len(team)
    for idx, player in enumerate(team):
        for stat in stats_per_zone[zone]:
            weights[idx] += getattr(player, stat)
    return random.choices(team, weights=weights, k=1)[0]


def pick_defender(team: list[PlayerProfile]) -> PlayerProfile:
    defense_stats = ['defensive_awareness', 'standing_tackle', 'interceptions', 'reactions']
    weights = [0] * len(team)
    for idx, player in enumerate(team):
        for stat in defense_stats:
            weights[idx] += getattr(player, stat)
    return random.choices(team, weights=weights, k=1)[0]
 

def select_action(ball_carrier: PlayerProfile, game_state: GameState) -> str:
    zone_actions = {
        "buildup": ["short_pass", "long_ball", "dribble_carry"],
        "midfield": ["through_ball", "skill_move", "physical_duel", "switch_play"],
        "final_third": ["finesse_shot", "power_shot", "cutback", "dribble_into_box", "header"]
    }
    action_stats = {
        "short_pass": ["short_passing"],
        "long_ball": ["long_passing"],
        "dribble_carry": ["dribbling"],
        "through_ball": ["vision", "short_passing"],
        "skill_move": ["skill_moves", "agility"],
        "physical_duel": ["strength", "aggression"],
        "switch_play": ["long_passing", "vision"],
        "finesse_shot": ["finishing", "curve"],
        "power_shot": ["shot_power", "long_shots"],
        "cutback": ["vision", "short_passing"],
        "dribble_into_box": ["dribbling", "agility"],
        "header": ["heading_accuracy", "jumping"]
    }

    weights = [0] * len(zone_actions[game_state.zone])
    for idx, action in enumerate(zone_actions[game_state.zone]):
        for stat in action_stats[action]:
            weights[idx] += getattr(ball_carrier, stat)

    # if possessing team is losing and we're in the third quarter of the game, then intensify the finesse shots, power shots, and headers
    if game_state.score[game_state.possessing_team] < game_state.score[1 - game_state.possessing_team] and game_state.phase_number > game_state.total_phases * 0.75:
        for idx, action in enumerate(zone_actions[game_state.zone]):
            if action in ["finesse_shot", "power_shot", "header"]:
                weights[idx] *= 1.5
    
    return random.choices(zone_actions[game_state.zone], weights=weights, k=1)[0]





