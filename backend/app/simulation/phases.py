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
    last_phase_was_turnover: bool = False # True if the previous phase ended with a possession flip via turnover/interception (not a goal)
    is_kickoff: bool = False # True on the first phase after a goal — prevents long ball skipping straight to final_third from kickoff
    cutback_assisted: bool = False # did a cutback just set up a premium chance?
    dribble_assisted: bool = False # did a dribble_into_box just set up a premium chance?
    set_piece_type: str = "free_kick" # free_kick or corner
    last_ball_carrier: str = "" # name of player who had the ball at end of last phase
    through_ball_receiver: str = "" # name of player who should carry the ball next phase after a successful through ball or cutback
    team_names: list[str] = field(default_factory=lambda: ["team A", "team B"]) # display names for each team



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

    # on kickoff, disallow long_ball and dribble_carry to prevent one-pass goals and fouls straight from restart
    if game_state.is_kickoff and game_state.zone == "buildup":
        zone_actions["buildup"] = ["short_pass"]
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

    # if assisted flag is set, force a shot immediately
    if (game_state.cutback_assisted or game_state.dribble_assisted) and game_state.zone == "final_third":
        shot_actions = ["finesse_shot", "power_shot", "header"]
        shot_weights = []
        for action in shot_actions:
            w = sum(getattr(ball_carrier, s) for s in action_stats[action])
            shot_weights.append(w)
        return random.choices(shot_actions, weights=shot_weights, k=1)[0]

    weights = [0] * len(zone_actions[game_state.zone])
    for idx, action in enumerate(zone_actions[game_state.zone]):
        for stat in action_stats[action]:
            weights[idx] += getattr(ball_carrier, stat)

    # reduce switch_play weight to 40% to prevent it dominating midfield
    if game_state.zone == "midfield":
        switch_idx = zone_actions["midfield"].index("switch_play")
        weights[switch_idx] *= 0.4

    # if possessing team is losing and we're in the last quarter, intensify shots
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
        if game_state.is_kickoff:
            succeeded = True  # kickoff pass always succeeds
        rest = [p for p in possessing_team if p.player_id != ball_carrier.player_id]
        target_name = pick_ball_carrier(rest, current_zone).name if rest else ball_carrier.name
        if succeeded:
            game_state.zone = ZONE_ORDER[min(ZONE_ORDER.index(current_zone) + 1, 2)]
        else:
            game_state.possessing_team = 1 - game_state.possessing_team
            game_state.zone = "midfield"
        return PassAttempt(
            phase=game_state.phase_number,
            zone=current_zone,
            passer=ball_carrier.name,
            target=target_name,
            pass_type="short",
            success=succeeded,
            turnover_player=defender.name if not succeeded else "",
            score=game_state.score[:]
        )
    elif action == "long_ball":
        current_zone = game_state.zone
        atk = compute_composite(ball_carrier, ["long_passing", "vision"])
        dfn = compute_composite(defender, ["reactions", "sprint_speed", "jumping"])
        succeeded = roll(success_probability(atk, dfn))
        rest = [p for p in possessing_team if p.player_id != ball_carrier.player_id]
        target_name = pick_ball_carrier(rest, "final_third").name if rest else ball_carrier.name
        if succeeded:
            game_state.zone = "final_third"
            game_state.through_ball_receiver = target_name  # lock in the named runner
        else:
            game_state.possessing_team = 1 - game_state.possessing_team
            game_state.zone = "midfield"
        return PassAttempt(
            phase=game_state.phase_number,
            zone=current_zone,
            passer=ball_carrier.name,
            target=target_name,
            pass_type="long",
            success=succeeded,
            turnover_player=defender.name if not succeeded else "",
            score=game_state.score[:]
        )
    elif action == "through_ball":
        current_zone = game_state.zone
        atk = compute_composite(ball_carrier, ["vision", "short_passing", "composure"])
        dfn = compute_composite(defender, ["defensive_awareness", "reactions", "sprint_speed"])
        succeeded = roll(success_probability(atk, dfn))
        rest = [p for p in possessing_team if p.player_id != ball_carrier.player_id]
        receiver = pick_ball_carrier(rest, "final_third") if rest else ball_carrier
        receiver_name = receiver.name
        if succeeded:
            game_state.zone = "final_third"
            game_state.through_ball_receiver = receiver_name
        else:
            game_state.possessing_team = 1 - game_state.possessing_team
            game_state.zone = "midfield"
        return PassAttempt(
            phase=game_state.phase_number,
            zone=current_zone,
            passer=ball_carrier.name,
            target=receiver_name,
            pass_type="through_ball",
            success=succeeded,
            turnover_player=defender.name if not succeeded else "",
            score=game_state.score[:]
        )
    elif action == "switch_play":
        current_zone = game_state.zone
        atk = compute_composite(ball_carrier, ["long_passing", "vision"])
        dfn = compute_composite(defender, ["acceleration", "reactions", "sprint_speed"])
        succeeded = roll(success_probability(atk, dfn))
        rest = [p for p in possessing_team if p.player_id != ball_carrier.player_id]
        target_name = pick_ball_carrier(rest, "buildup").name if rest else ball_carrier.name
        if succeeded:
            game_state.zone = "midfield"
        else:
            game_state.possessing_team = 1 - game_state.possessing_team
            game_state.zone = "midfield"
        return PassAttempt(
            phase=game_state.phase_number,
            zone=current_zone,
            passer=ball_carrier.name,
            target=target_name,
            pass_type="switch",
            success=succeeded,
            turnover_player=defender.name if not succeeded else "",
            score=game_state.score[:]
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
                game_state.set_piece_type = "free_kick"
            else:
                game_state.possessing_team = 1 - game_state.possessing_team
                game_state.zone = "midfield"
        dribble_event = DribbleAttempt(
            phase=game_state.phase_number,
            zone=current_zone,
            dribbler=ball_carrier.name,
            defender=defender.name,
            success=succeeded,
            foul=foul,
            turnover_player=defender.name if not succeeded and not foul else "",
            score=game_state.score[:]
        )
        if succeeded:
            carry_event = DribbleAttempt(
                phase=game_state.phase_number,
                zone=game_state.zone,
                dribbler=ball_carrier.name,
                defender="",
                success=True,
                foul=False,
                score=game_state.score[:]
            )
            return [dribble_event, carry_event]
        return dribble_event
    elif action == "skill_move":
        current_zone = game_state.zone
        atk = compute_composite(ball_carrier, ["dribbling", "agility", "ball_control", "balance"])
        dfn = compute_composite(defender, ["standing_tackle", "aggression", "reactions"])
        succeeded = roll(success_probability(atk, dfn))
        foul = False
        if succeeded:
            game_state.zone = ZONE_ORDER[min(ZONE_ORDER.index(current_zone) + 1, 2)]
        else:
            foul = roll(defender.aggression / 200)
            if foul:
                game_state.zone = "set_piece"
                game_state.set_piece_type = "free_kick"
            else:
                game_state.possessing_team = 1 - game_state.possessing_team
                game_state.zone = "midfield"
        dribble_event = DribbleAttempt(
            phase=game_state.phase_number,
            zone=current_zone,
            dribbler=ball_carrier.name,
            defender=defender.name,
            success=succeeded,
            foul=foul,
            turnover_player=defender.name if not succeeded and not foul else "",
            score=game_state.score[:]
        )
        if succeeded:
            carry_event = DribbleAttempt(
                phase=game_state.phase_number,
                zone=game_state.zone,
                dribbler=ball_carrier.name,
                defender="",
                success=True,
                foul=False,
                score=game_state.score[:]
            )
            return [dribble_event, carry_event]
        return dribble_event
    elif action == "dribble_into_box":
        current_zone = game_state.zone
        atk = compute_composite(ball_carrier, ["dribbling", "agility", "ball_control", "balance"])
        dfn = compute_composite(defender, ["standing_tackle", "aggression", "reactions"])
        succeeded = roll(success_probability(atk, dfn))
        foul = False
        if succeeded:
            game_state.zone = "final_third"
            game_state.dribble_assisted = True
        else:
            foul = roll(defender.aggression / 200)
            if foul:
                game_state.zone = "set_piece"
                game_state.set_piece_type = "free_kick"
            else:
                game_state.possessing_team = 1 - game_state.possessing_team
                game_state.zone = "midfield"
        return DribbleAttempt(
            phase=game_state.phase_number,
            zone=current_zone,
            dribbler=ball_carrier.name,
            defender=defender.name,
            success=succeeded,
            foul=foul,
            turnover_player=defender.name if not succeeded and not foul else "",
            score=game_state.score[:]
        )
    elif action == "physical_duel":
        current_zone = game_state.zone
        atk = compute_composite(ball_carrier, ["strength", "aggression", "stamina"])
        dfn = compute_composite(defender, ["strength", "standing_tackle", "aggression"])
        succeeded = roll(success_probability(atk, dfn))
        if succeeded:
            game_state.zone = ZONE_ORDER[min(ZONE_ORDER.index(current_zone) + 1, 2)]
            game_state.last_ball_carrier = ""  # zone jumped — next phase starts fresh
        else:
            game_state.possessing_team = 1 - game_state.possessing_team
        winner = ball_carrier.name if succeeded else defender.name
        score_snap = game_state.score[:]
        duel_event = PhysicalDuel(
            phase=game_state.phase_number,
            zone=current_zone,
            player_a=ball_carrier.name,
            player_b=defender.name,
            winner=winner,
            score=score_snap
        )
        if succeeded:
            # emit a carry event to bridge the zone jump narratively
            carry_event = DribbleAttempt(
                phase=game_state.phase_number,
                zone=game_state.zone,
                dribbler=ball_carrier.name,
                defender="",
                success=True,
                foul=False,
                score=score_snap
            )
            return [duel_event, carry_event]
        return duel_event
    elif action == "cutback":
        current_zone = game_state.zone
        atk = compute_composite(ball_carrier, ["short_passing", "vision", "composure"])
        dfn = compute_composite(defender, ["interceptions", "reactions"])
        succeeded = roll(success_probability(atk, dfn))
        rest = [p for p in possessing_team if p.player_id != ball_carrier.player_id]
        target_name = pick_ball_carrier(rest, "final_third").name if rest else ball_carrier.name
        if succeeded:
            game_state.cutback_assisted = True
            game_state.through_ball_receiver = target_name  # lock in the named recipient as shooter
            game_state.last_ball_carrier = ball_carrier.name  # suppress bridging pass next phase
        else:
            game_state.possessing_team = 1 - game_state.possessing_team
            game_state.zone = "midfield"
        return PassAttempt(
            phase=game_state.phase_number,
            zone=current_zone,
            passer=ball_carrier.name,
            target=target_name,
            pass_type="cutback",
            success=succeeded,
            turnover_player=defender.name if not succeeded else "",
            score=game_state.score[:]
        )
    elif action in ("finesse_shot", "power_shot", "header"):
        current_zone = game_state.zone
        creation_map = {
            "finesse_shot": "cutback",
            "power_shot": "long_shot",
            "header": "header"
        }
        quality = shot_quality(creation_map[action], ball_carrier)
        if game_state.cutback_assisted or game_state.dribble_assisted:
            quality = min(0.85, quality + 0.15)
            game_state.cutback_assisted = False
            game_state.dribble_assisted = False
        is_goal = roll(quality)
        if is_goal:
            outcome = "goal"
            game_state.score[game_state.possessing_team] += 1
            game_state.possessing_team = 1 - game_state.possessing_team
            game_state.zone = "buildup"  # kickoff restart after a goal
            game_state.is_kickoff = True
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
            assister=None,
            score=game_state.score[:]
        )

def resolve_set_piece(possessing_team: list[PlayerProfile], defending_team: list[PlayerProfile], game_state: GameState) -> GameEvent:
    taker = max(possessing_team, key=lambda p: p.fk_accuracy)
    aerial_defender = max(defending_team, key=lambda p: p.jumping + p.heading_accuracy)
    piece_type = game_state.set_piece_type

    if piece_type == "free_kick":
        quality = shot_quality("free_kick", taker)
        if roll(quality):
            outcome = "goal"
            game_state.score[game_state.possessing_team] += 1
            game_state.zone = "buildup"
            game_state.is_kickoff = True
        else:
            outcome = "save"
            game_state.zone = "midfield"
    else:  # corner
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
                game_state.zone = "buildup"
                game_state.is_kickoff = True
            else:
                outcome = "save"
                game_state.zone = "midfield"
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
        event.score = game_state.score[:]
        game_state.last_ball_carrier = ""
        game_state.through_ball_receiver = ""
        game_state.cutback_assisted = False
        game_state.dribble_assisted = False
        game_state.phase_number += 1
        return [event]
    
    ball_carrier = pick_ball_carrier(attacking_team, game_state.zone)
    # if a through ball named a specific receiver last phase, lock them in as ball carrier
    if game_state.through_ball_receiver:
        locked = next((p for p in attacking_team if p.name == game_state.through_ball_receiver), None)
        if locked:
            ball_carrier = locked
        game_state.through_ball_receiver = ""
        game_state.dribble_assisted = False
        game_state.last_ball_carrier = ball_carrier.name  # suppress bridging pass
    elif game_state.last_ball_carrier:
        # if we know who had the ball last phase, keep continuity — lock them in
        locked = next((p for p in attacking_team if p.name == game_state.last_ball_carrier), None)
        if locked:
            ball_carrier = locked
    defender = pick_defender(defending_team)

    if not game_state.last_phase_was_turnover and not game_state.is_kickoff:
        if special_event_check(ball_carrier, "brilliance"):
            current_zone = game_state.zone
            game_state.score[game_state.possessing_team] += 1
            game_state.zone = "midfield"
            game_state.possessing_team = 1 - game_state.possessing_team
            game_state.last_ball_carrier = ""
            game_state.through_ball_receiver = ""
            game_state.cutback_assisted = False
            game_state.dribble_assisted = False
            game_state.last_phase_was_turnover = False
            event = SpecialEvent(
                phase=game_state.phase_number,
                zone=current_zone,
                player=ball_carrier.name,
                special_type="brilliance",
                description="solo_run",
                resulted_in_goal=True,
                score=game_state.score[:]
            )
            game_state.phase_number += 1
            return [event]

        if special_event_check(ball_carrier, "error"):
            current_zone = game_state.zone
            game_state.possessing_team = 1 - game_state.possessing_team
            game_state.zone = "midfield"
            game_state.last_ball_carrier = ""
            game_state.through_ball_receiver = ""
            game_state.cutback_assisted = False
            game_state.dribble_assisted = False
            game_state.last_phase_was_turnover = True
            event = SpecialEvent(
                phase=game_state.phase_number,
                zone=current_zone,
                player=ball_carrier.name,
                special_type="error",
                description="misplaced_backpass",
                resulted_in_goal=False,
                score=game_state.score[:]
            )
            game_state.phase_number += 1
            return [event]
    
    team_before = game_state.possessing_team  # snapshot BEFORE resolve_action

    # if the ball carrier changed within the same possession, emit a bridging pass
    # suppress only on cutback_assisted — the cutback text already named the setup
    # dribble_assisted does NOT suppress — dribble_into_box names no recipient
    events = []
    if game_state.last_ball_carrier and game_state.last_ball_carrier != ball_carrier.name and not game_state.cutback_assisted:
        events.append(PassAttempt(
            phase=game_state.phase_number,
            zone=game_state.zone,
            passer=game_state.last_ball_carrier,
            target=ball_carrier.name,
            pass_type="short",
            success=True,
            score=game_state.score[:]
        ))

    action = select_action(ball_carrier, game_state)
    result = resolve_action(action, ball_carrier, defender, game_state, team_a, team_b)
    if isinstance(result, list):
        events.extend(result)
    else:
        events.append(result)

    # now update momentum
    if game_state.possessing_team == team_before:
        game_state.momentum[team_before] += 1
        game_state.last_phase_was_turnover = False
        game_state.is_kickoff = False
        last_event = events[-1] if events else None
        if isinstance(last_event, PassAttempt) and last_event.success and last_event.pass_type not in ("cutback", "through_ball", "long"):
            game_state.last_ball_carrier = last_event.target
        elif isinstance(last_event, DribbleAttempt) and last_event.success and last_event.defender == "":
            game_state.last_ball_carrier = last_event.dribbler  # carry event — track the dribbler for bridging
        else:
            game_state.last_ball_carrier = ball_carrier.name
    else:
        game_state.momentum[team_before] = 0
        game_state.momentum[game_state.possessing_team] += 1
        game_state.last_ball_carrier = ""
        game_state.through_ball_receiver = ""
        game_state.cutback_assisted = False
        game_state.dribble_assisted = False
        game_state.last_phase_was_turnover = True
        last_event = events[-1] if events else None
        if isinstance(last_event, PhysicalDuel):
            events.append(PossessionChange(
                phase=game_state.phase_number,
                zone=game_state.zone,
                player=last_event.winner,
                method="duel",
                team=game_state.possessing_team,
                score=game_state.score[:]
            ))

    game_state.phase_number += 1
    return events

