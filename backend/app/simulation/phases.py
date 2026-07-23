import random
from dataclasses import dataclass, field
from app.player_profile import PlayerProfile
from app.simulation.probability import compute_composite, success_probability, roll, shot_quality, special_event_check
from app.simulation.events import PossessionChange, PassAttempt, DribbleAttempt, ShotAttempt, SetPiece, PhysicalDuel, SpecialEvent, GameEvent

ZONE_ORDER = ["buildup", "midfield", "final_third"]

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




def resolve_action(action: str, ball_carrier: PlayerProfile, defender: PlayerProfile, game_state: GameState, team_a: list[PlayerProfile], team_b: list[PlayerProfile]) -> GameEvent:
    
    current_zone = game_state.zone
    possessing_team = team_a if game_state.possessing_team == 0 else team_b

    if action == "short_pass":
        atk = compute_composite(ball_carrier, ["short_passing", "ball_control", "composure"])
        dfn = compute_composite(defender, ["interceptions", "reactions", "defensive_awareness"])
        succeeded = roll(success_probability(atk, dfn))
        
        if succeeded:
            game_state.zone = ZONE_ORDER[min(ZONE_ORDER.index(current_zone) + 1, 2)]
        else:
            game_state.possessing_team = 1 - game_state.possessing_team
            game_state.zone = "midfield"
        return PassAttempt(
            phase=game_state.phase_number,
            zone=current_zone,
            passer=ball_carrier.name,
            target="teammate",
            pass_type="short",
            success=succeeded
        )
    elif action == "long_ball":
        current_zone = game_state.zone
        atk = compute_composite(ball_carrier, ["long_passing", "vision"])
        dfn = compute_composite(defender, ["reactions", "sprint_speed", "jumping"])
        succeeded = roll(success_probability(atk, dfn))
        if succeeded:
            game_state.zone = "final_third"
        else:
            game_state.possessing_team = 1 - game_state.possessing_team
            game_state.zone = "midfield"
        return PassAttempt(
            phase=game_state.phase_number,
            zone=current_zone,
            passer=ball_carrier.name,
            target="teammate",
            pass_type="long",
            success=succeeded
        )
    elif action == "through_ball":
        current_zone = game_state.zone
        atk = compute_composite(ball_carrier, ["vision", "short_passing", "composure"])
        dfn = compute_composite(defender, ["defensive_awareness", "reactions", "sprint_speed"])
        succeeded = roll(success_probability(atk, dfn))
        receiver_name = "teammate"
        if succeeded:
            game_state.zone = "final_third"
            rest = [p for p in possessing_team if p.player_id != ball_carrier.player_id]
            if rest:
                receiver = pick_ball_carrier(rest, "final_third")
                receiver_name = receiver.name
        else:
            game_state.possessing_team = 1 - game_state.possessing_team
            game_state.zone = "midfield"
        return PassAttempt(
            phase=game_state.phase_number,
            zone=current_zone,
            passer=ball_carrier.name,
            target=receiver_name,
            pass_type="through_ball",
            success=succeeded
        )
    elif action == "switch_play":
        current_zone = game_state.zone
        atk = compute_composite(ball_carrier, ["long_passing", "vision"])
        dfn = compute_composite(defender, ["acceleration", "reactions", "sprint_speed"])
        succeeded = roll(success_probability(atk, dfn))
        if succeeded:
            game_state.zone = "buildup"
        else:
            game_state.possessing_team = 1 - game_state.possessing_team
            game_state.zone = "midfield"
        return PassAttempt(
            phase=game_state.phase_number,
            zone=current_zone,
            passer=ball_carrier.name,
            target="teammate",
            pass_type="switch",
            success=succeeded
        )
    elif action == "dribble_carry":
        current_zone = game_state.zone
        atk = compute_composite(ball_carrier, ["dribbling", "agility", "balance", "ball_control"])
        dfn = compute_composite(defender, ["reactions", "aggression", "standing_tackle"])
        succeeded = roll(success_probability(atk, dfn))
        foul = False
        if succeeded:
            game_state.zone = ZONE_ORDER[min(ZONE_ORDER.index(current_zone) + 1, 2)]
        else:
            foul = roll(defender.aggression / 200)
            if foul:
                game_state.zone = "set_piece"
            else:
                game_state.possessing_team = 1 - game_state.possessing_team
                game_state.zone = "midfield"
        return DribbleAttempt(
            phase=game_state.phase_number,
            zone=current_zone,
            dribbler=ball_carrier.name,
            defender=defender.name,
            success=succeeded,
            foul=foul
        )
    elif action == "skill_move":
        current_zone = game_state.zone
        atk = compute_composite(ball_carrier, ["dribbling", "agility", "ball_control", "balance"])
        dfn = compute_composite(defender, ["standing_tackle", "aggression", "reactions"])
        succeeded = roll(success_probability(atk, dfn))
        foul = False
        if succeeded:
            game_state.zone = "final_third"
        else:
            foul = roll(defender.aggression / 200)
            if foul:
                game_state.zone = "set_piece"
            else:
                game_state.possessing_team = 1 - game_state.possessing_team
                game_state.zone = "midfield"
        return DribbleAttempt(
            phase=game_state.phase_number,
            zone=current_zone,
            dribbler=ball_carrier.name,
            defender=defender.name,
            success=succeeded,
            foul=foul
        )
    elif action == "dribble_into_box":
        current_zone = game_state.zone
        atk = compute_composite(ball_carrier, ["dribbling", "agility", "ball_control", "balance"])
        dfn = compute_composite(defender, ["standing_tackle", "aggression", "reactions"])
        succeeded = roll(success_probability(atk, dfn))
        foul = False
        if succeeded:
            game_state.zone = "final_third"
            game_state.assisted = True
        else:
            foul = roll(defender.aggression / 200)
            if foul:
                game_state.zone = "set_piece"
            else:
                game_state.possessing_team = 1 - game_state.possessing_team
                game_state.zone = "midfield"
        return DribbleAttempt(
            phase=game_state.phase_number,
            zone=current_zone,
            dribbler=ball_carrier.name,
            defender=defender.name,
            success=succeeded,
            foul=foul
        )
    elif action == "physical_duel":
        current_zone = game_state.zone
        atk = compute_composite(ball_carrier, ["strength", "aggression", "stamina"])
        dfn = compute_composite(defender, ["strength", "standing_tackle", "aggression"])
        succeeded = roll(success_probability(atk, dfn))
        if succeeded:
            game_state.zone = ZONE_ORDER[min(ZONE_ORDER.index(current_zone) + 1, 2)]
        else:
            game_state.possessing_team = 1 - game_state.possessing_team
        winner = ball_carrier.name if succeeded else defender.name
        return PhysicalDuel(
            phase=game_state.phase_number,
            zone=current_zone,
            player_a=ball_carrier.name,
            player_b=defender.name,
            winner=winner
        )
    elif action == "cutback":
        current_zone = game_state.zone
        atk = compute_composite(ball_carrier, ["short_passing", "vision", "composure"])
        dfn = compute_composite(defender, ["interceptions", "reactions"])
        succeeded = roll(success_probability(atk, dfn))
        if succeeded:
            game_state.assisted = True
            # zone stays "final_third", possession stays
        else:
            game_state.possessing_team = 1 - game_state.possessing_team
            game_state.zone = "midfield"
        return PassAttempt(
            phase=game_state.phase_number,
            zone=current_zone,
            passer=ball_carrier.name,
            target="teammate",
            pass_type="cutback",
            success=succeeded
        )
    elif action in ("finesse_shot", "power_shot", "header"):
        current_zone = game_state.zone
        creation_map = {
            "finesse_shot": "cutback",
            "power_shot": "long_shot",
            "header": "header"
        }
        quality = shot_quality(creation_map[action], ball_carrier)
        if game_state.assisted:
            quality = min(0.85, quality + 0.15)
            game_state.assisted = False
        is_goal = roll(quality)
        if is_goal:
            outcome = "goal"
            game_state.score[game_state.possessing_team] += 1
        else:
            if roll(0.4):
                outcome = "save"
            elif roll(0.5):
                outcome = "block"
            else:
                outcome = "miss"
        game_state.possessing_team = 1 - game_state.possessing_team
        game_state.zone = "midfield"
        return ShotAttempt(
            phase=game_state.phase_number,
            zone=current_zone,
            shooter=ball_carrier.name,
            shot_type=action,
            quality=quality,
            outcome=outcome,
            assister=None
        )

def resolve_set_piece(possessing_team: list[PlayerProfile], defending_team: list[PlayerProfile], game_state: GameState) -> GameEvent:
    taker = max(possessing_team, key=lambda p: p.fk_accuracy)
    aerial_defender = max(defending_team, key=lambda p: p.jumping + p.heading_accuracy)
    is_direct = roll(0.5)

    if is_direct:
        piece_type = "free_kick"
        quality = shot_quality("free_kick", taker)
        if roll(quality):
            outcome = "goal"
            game_state.score[game_state.possessing_team] += 1
        else:
            outcome = "save"
    else:
        piece_type = "corner"
        delivery = compute_composite(taker, ["crossing", "curve"])
        defense = compute_composite(aerial_defender, ["jumping", "heading_accuracy"])
        if roll(success_probability(delivery, defense)):
            # delivery beat the defender, now a teammate attacks it
            attacker = max([p for p in possessing_team if p.player_id != taker.player_id], 
                        key=lambda p: p.heading_accuracy + p.jumping)
            header_quality = shot_quality("header", attacker)
            if roll(header_quality):
                outcome = "goal"
                game_state.score[game_state.possessing_team] += 1
            else:
                outcome = "save"
        else:
            outcome = "cleared"

    game_state.zone = "midfield"
    game_state.possessing_team = 1 - game_state.possessing_team

    return SetPiece(
        phase=game_state.phase_number,
        zone="set_piece",
        taker=taker.name,
        piece_type=piece_type,
        outcome=outcome
    )


def resolve_phase(game_state: GameState, team_a: list[PlayerProfile], team_b: list[PlayerProfile]) -> list[GameEvent]:
    attacking_team = team_a if game_state.possessing_team == 0 else team_b
    defending_team = team_b if game_state.possessing_team == 0 else team_a

    if game_state.zone == "set_piece":
        event = resolve_set_piece(attacking_team, defending_team, game_state)
        game_state.phase_number += 1
        return [event]
    
    ball_carrier = pick_ball_carrier(attacking_team, game_state.zone)
    defender = pick_defender(defending_team)

    if special_event_check(ball_carrier, "brilliance"):
        game_state.score[game_state.possessing_team] += 1
        game_state.zone = "midfield"
        game_state.possessing_team = 1 - game_state.possessing_team
        game_state.phase_number += 1
        return [SpecialEvent(
            phase=game_state.phase_number,
            zone=game_state.zone,
            player=ball_carrier.name,
            special_type="brilliance",
            description="solo_run",
            resulted_in_goal=True
        )]

    if special_event_check(ball_carrier, "error"):
        game_state.possessing_team = 1 - game_state.possessing_team
        game_state.zone = "midfield"
        game_state.phase_number += 1
        return [SpecialEvent(
            phase=game_state.phase_number,
            zone=game_state.zone,
            player=ball_carrier.name,
            special_type="error",
            description="misplaced_backpass",
            resulted_in_goal=False
        )]
    
    team_before = game_state.possessing_team  # snapshot BEFORE resolve_action
    action = select_action(ball_carrier, game_state)
    event = resolve_action(action, ball_carrier, defender, game_state, team_a, team_b)

    # now update momentum
    if game_state.possessing_team == team_before:
        # possession stayed — increment momentum for that team
        game_state.momentum[team_before] += 1
    else:
        # possession flipped — reset the team that just lost it
        game_state.momentum[team_before] = 0
        game_state.momentum[game_state.possessing_team] += 1

    game_state.phase_number += 1
    return [event]

