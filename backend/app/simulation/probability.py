from app.player_profile import PlayerProfile
from typing import Optional
import random

shot_creation = {
    "through_ball": 0.35,
    "dribble_into_box": 0.45,
    "cutback": 0.40,
    "long_shot": 0.08,
    "header": 0.25,
    "volley": 0.15,
    "free_kick": 0.10
}

def compute_composite(player: PlayerProfile, stat_names: list, weights: list[float]=[]) -> float:
    res = 0
    if not weights:
        weights = [1] * len(stat_names)
    for idx, stat in enumerate(stat_names):
        res += getattr(player, stat) * weights[idx]
    
    return res / sum(weights)



def success_probability(attacker_composite: float, defender_composite: float) -> float:
    res = attacker_composite / (attacker_composite + defender_composite)
    res += random.uniform(-0.05, 0.05)
    return max(0.05, min(0.95, res))

def roll(probability: float) -> bool:
    return random.random() < probability


def shot_quality(creation_method: str, shooter: PlayerProfile) -> float:
    if creation_method not in shot_creation.keys():
        raise Exception(f"{creation_method} not in {shot_creation.keys()}")
    res = shot_creation.get(creation_method) * (shooter.finishing / 80)
    return max(0.02, min(0.85, res))


def special_event_check(player: PlayerProfile, event_type: str) -> bool:
    if event_type == "brilliance":
        chance = (player.overall_rating + player.skill_moves * 10 + player.composure) / 3000
    elif event_type == "error":
        chance = (200 - player.composure - player.ball_control) / 3000
    else:
        raise Exception(f"Event type has to be of value 'brilliance' or 'error'.")

    return roll(chance)




