import random
from app.simulation.events import PassAttempt, DribbleAttempt, ShotAttempt, SetPiece, PhysicalDuel, SpecialEvent, GameEvent
from app.simulation.phases import GameState

TEMPLATES = {
    # --- PASS ---
    ("pass", "short"): [
        "{passer} plays it simple to {target}.",
        "{passer} keeps it moving with a short pass.",
        "Quick ball from {passer} to {target}.",
    ],
    ("pass", "short_fail"): [
        "{passer}'s pass is cut out.",
        "Sloppy ball from {passer}, intercepted.",
        "{passer} gives it away with a loose pass.",
    ],
    ("pass", "long"): [
        "{passer} launches it long — {target} is in behind!",
        "Big ball over the top from {passer}.",
        "{passer} finds {target} with a raking long pass.",
    ],
    ("pass", "long_fail"): [
        "{passer}'s long ball is too heavy, defender wins it.",
        "The long ball from {passer} doesn't find anyone.",
        "Overhit from {passer}, possession lost.",
    ],
    ("pass", "through_ball"): [
        "{passer} threads it through to {target} — brilliant ball!",
        "Incisive through ball from {passer}, {target} is clean through.",
        "{passer} splits the defense and finds {target}.",
    ],
    ("pass", "through_ball_fail"): [
        "{passer} tries to play {target} in but it's read by the defense.",
        "The through ball from {passer} is intercepted.",
        "{passer} attempts the killer pass but it's cut out.",
    ],
    ("pass", "switch"): [
        "{passer} switches the play, opening up space.",
        "Nice switch from {passer} to change the angle.",
        "{passer} moves it wide with a diagonal ball.",
    ],
    ("pass", "switch_fail"): [
        "{passer}'s switch is intercepted.",
        "The switch from {passer} doesn't come off.",
        "Turnover — {passer}'s diagonal ball is picked off.",
    ],
    ("pass", "cutback"): [
        "{passer} cuts it back for a teammate — dangerous!",
        "Smart cutback from {passer} across the face of goal.",
        "{passer} pulls it back, setting up a chance.",
    ],
    ("pass", "cutback_fail"): [
        "{passer} tries the cutback but it's blocked.",
        "The cutback from {passer} is cleared.",
        "{passer}'s pullback is intercepted.",
    ],

    # --- DRIBBLE ---
    ("dribble", "success"): [
        "{dribbler} glides past {defender} with ease.",
        "{dribbler} drops a shoulder and leaves {defender} behind.",
        "Beautiful footwork from {dribbler}, {defender} can't live with it.",
        "{dribbler} beats {defender} and drives forward.",
    ],
    ("dribble", "fail"): [
        "{defender} stands firm and wins the ball from {dribbler}.",
        "Good defending from {defender}, stops {dribbler} in their tracks.",
        "{dribbler} tries to go past {defender} but loses it.",
    ],
    ("dribble", "foul"): [
        "{defender} can't stop {dribbler} fairly — foul given!",
        "{dribbler} is brought down by {defender}. Free kick.",
        "Cynical foul from {defender} on {dribbler}.",
    ],

    # --- SHOT ---
    ("shot", "goal"): [
        "{shooter} fires it into the net! GOAL!",
        "Clinical finish from {shooter}!",
        "{shooter} makes no mistake — bottom corner!",
        "GET IN! {shooter} scores!",
    ],
    ("shot", "save"): [
        "{shooter} forces a save.",
        "Good effort from {shooter} but it's kept out.",
        "{shooter} tests the defense — saved!",
    ],
    ("shot", "block"): [
        "{shooter}'s shot is blocked!",
        "Blocked! {shooter} can't find a way through.",
        "The defense gets in the way of {shooter}'s effort.",
    ],
    ("shot", "miss"): [
        "{shooter} blazes it over the bar.",
        "Off target from {shooter} — chance wasted.",
        "{shooter} pulls it wide. Should have done better.",
    ],

    # --- DUEL ---
    ("duel", "win"): [
        "{winner} wins the physical battle against {loser}.",
        "{winner} muscles {loser} off the ball.",
        "Strong from {winner}, comes out on top against {loser}.",
    ],
    ("duel", "loss"): [
        "{winner} wins the physical battle against {loser}.",
        "{loser} is outmuscled by {winner}.",
        "{winner} wins the 50/50 against {loser}.",
    ],

    # --- SET PIECE ---
    ("set_piece", "goal"): [
        "{taker} curls it in — straight from the set piece! GOAL!",
        "Brilliant delivery from {taker} finds the net!",
        "{taker} scores direct from the {piece_type}!",
    ],
    ("set_piece", "save"): [
        "{taker}'s delivery is dealt with.",
        "The {piece_type} from {taker} is saved.",
        "Good delivery from {taker} but it's kept out.",
    ],
    ("set_piece", "cleared"): [
        "The defense clears {taker}'s {piece_type}.",
        "{taker}'s delivery is headed clear.",
        "Defended well — {taker}'s {piece_type} comes to nothing.",
    ],

    # --- SPECIAL ---
    ("special", "brilliance"): [
        "MOMENT OF MAGIC! {player} produces something special and scores!",
        "{player} with an outrageous piece of skill — GOAL!",
        "You can't legislate for that! {player} scores out of nothing!",
    ],
    ("special", "error"): [
        "Terrible mistake from {player} — possession given away!",
        "{player} switches off and loses the ball cheaply.",
        "Unforced error from {player}, the other team pounces.",
    ],
}


def narrate_event(event: GameEvent, game_state: GameState) -> str:
    if isinstance(event, PassAttempt):
        if event.success:
            key = ("pass", event.pass_type)
        else:
            key = ("pass", f"{event.pass_type}_fail")
        templates = TEMPLATES.get(key)
        if not templates:
            return f"{event.passer} plays a {event.pass_type} pass."
        return random.choice(templates).format(passer=event.passer, target=event.target)

    elif isinstance(event, DribbleAttempt):
        if event.success:
            key = ("dribble", "success")
        elif event.foul:
            key = ("dribble", "foul")
        else:
            key = ("dribble", "fail")
        templates = TEMPLATES.get(key, [])
        if not templates:
            return f"{event.dribbler} attempts a dribble."
        return random.choice(templates).format(dribbler=event.dribbler, defender=event.defender)

    elif isinstance(event, ShotAttempt):
        key = ("shot", event.outcome)
        templates = TEMPLATES.get(key, [])
        if not templates:
            return f"{event.shooter} shoots — {event.outcome}."
        return random.choice(templates).format(shooter=event.shooter)

    elif isinstance(event, SetPiece):
        key = ("set_piece", event.outcome)
        templates = TEMPLATES.get(key, [])
        if not templates:
            return f"{event.taker} takes the {event.piece_type} — {event.outcome}."
        return random.choice(templates).format(taker=event.taker, piece_type=event.piece_type)

    elif isinstance(event, PhysicalDuel):
        loser = event.player_b if event.winner == event.player_a else event.player_a
        key = ("duel", "win")
        templates = TEMPLATES.get(key, [])
        if not templates:
            return f"{event.winner} wins the duel against {loser}."
        return random.choice(templates).format(winner=event.winner, loser=loser)

    elif isinstance(event, SpecialEvent):
        key = ("special", event.special_type)
        templates = TEMPLATES.get(key, [])
        if not templates:
            return f"{event.player} — {event.special_type}!"
        return random.choice(templates).format(player=event.player)

    return f"Phase {event.phase}: {event.event_type}"
