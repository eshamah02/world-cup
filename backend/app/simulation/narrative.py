import random
from app.simulation.events import PassAttempt, DribbleAttempt, ShotAttempt, SetPiece, PhysicalDuel, SpecialEvent, PossessionChange, GameEvent
from app.simulation.phases import GameState


PARTICLES = {"de", "van", "von", "di", "da", "dos", "del", "der", "le", "la"}


def short_name(name: str) -> str:
    parts = name.split()
    if len(parts) <= 2:
        return name
    # find the last meaningful surname token, keeping particles attached
    # walk backwards to find where the surname starts (first particle or last word)
    surname_start = len(parts) - 1
    while surname_start > 1 and parts[surname_start - 1].lower() in PARTICLES:
        surname_start -= 1
    return f"{parts[0]} {' '.join(parts[surname_start:])}"

TEMPLATES = {
    # --- PASS ---
    ("pass", "short"): [
        "{passer} plays it simple to {target}.",
        "{passer} keeps it ticking, finds {target}.",
        "Quick ball from {passer} to {target}.",
    ],
    ("pass", "short_fail"): [
        "{passer}'s pass is cut out.",
        "Sloppy ball from {passer}, intercepted.",
        "{passer} gives it away with a loose pass.",
    ],
    ("pass", "short_fail_turnover"): [
        "{turnover_player} intercepts {passer}'s pass and {team} are on the attack.",
        "{turnover_player} reads it perfectly — {team} win possession.",
        "Stolen by {turnover_player}! {team} break forward.",
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
    ("pass", "long_fail_turnover"): [
        "{turnover_player} wins the aerial duel and {team} have it.",
        "{passer}'s long ball is claimed by {turnover_player} — {team} in possession.",
        "{turnover_player} picks it up and {team} are away.",
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
    ("pass", "through_ball_fail_turnover"): [
        "{turnover_player} reads the through ball and {team} break.",
        "Intercepted by {turnover_player}! {team} counter.",
        "{turnover_player} cuts it out — {team} on the counter-attack.",
    ],
    ("pass", "switch"): [
        "{passer} switches the play to {target}, opening up space.",
        "Nice switch from {passer} to {target} to change the angle.",
        "{passer} moves it wide to {target} with a diagonal ball.",
    ],
    ("pass", "switch_fail"): [
        "{passer}'s switch intended for {target} is intercepted.",
        "The switch from {passer} doesn't come off.",
        "Turnover — {passer}'s diagonal ball is picked off.",
    ],
    ("pass", "switch_fail_turnover"): [
        "{turnover_player} intercepts the switch and {team} are on the move.",
        "Picked off by {turnover_player} — {team} win it back.",
        "{turnover_player} reads the diagonal and {team} have possession.",
    ],
    ("pass", "cutback"): [
        "{passer} cuts it back for {target} — dangerous!",
        "Smart cutback from {passer} to {target} across the face of goal.",
        "{passer} pulls it back for {target}, setting up a chance.",
    ],
    ("pass", "cutback_fail"): [
        "{passer} tries the cutback but it's blocked.",
        "The cutback from {passer} is cleared.",
        "{passer}'s pullback is intercepted.",
    ],
    ("pass", "cutback_fail_turnover"): [
        "{turnover_player} blocks the cutback — {team} clear their lines.",
        "Cleared by {turnover_player}! {team} break out.",
        "{turnover_player} intercepts the pullback and {team} are away.",
    ],

    # --- DRIBBLE ---
    ("dribble", "success"): [
        "{dribbler} glides past {defender} with ease.",
        "{dribbler} drops a shoulder and leaves {defender} behind.",
        "Beautiful footwork from {dribbler}, {defender} can't live with it.",
        "{dribbler} beats {defender} and drives forward.",
    ],
    ("dribble", "carry"): [
        "{dribbler} surges forward into the final third.",
        "{dribbler} drives into a dangerous position.",
        "{dribbler} bursts forward with the ball.",
    ],
    ("dribble", "fail"): [
        "{defender} stands firm and wins the ball from {dribbler}.",
        "Good defending from {defender}, stops {dribbler} in their tracks.",
        "{dribbler} tries to go past {defender} but loses it.",
    ],
    ("dribble", "fail_turnover"): [
        "{turnover_player} takes it off {dribbler} — {team} on the attack.",
        "{turnover_player} wins it cleanly from {dribbler} and {team} break forward.",
        "{dribbler} loses it — {turnover_player} pounces for {team}.",
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

    # --- POSSESSION CHANGE (duel win) ---
    ("possession_change", "duel"): [
        "{player} wins it back for {team}.",
        "{player} claims possession — {team} are on the attack.",
        "{team} have it now, {player} winning the ball.",
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

_TEAM_LABELS = {0: "team A", 1: "team B"}


def _team_label(game_state: GameState, team_idx: int) -> str:
    return game_state.team_names[team_idx] if hasattr(game_state, "team_names") and len(game_state.team_names) > team_idx else _TEAM_LABELS[team_idx]


def narrate_event(event: GameEvent, game_state: GameState) -> str:
    if isinstance(event, PassAttempt):
        if event.success:
            key = ("pass", event.pass_type)
            templates = TEMPLATES.get(key)
            if not templates:
                return f"{event.passer} plays a {event.pass_type} pass."
            return random.choice(templates).format(passer=short_name(event.passer), target=short_name(event.target))
        else:
            turnover_key = ("pass", f"{event.pass_type}_fail_turnover")
            base_key = ("pass", f"{event.pass_type}_fail")
            if event.turnover_player and TEMPLATES.get(turnover_key):
                team_label = _team_label(game_state, game_state.possessing_team)
                return random.choice(TEMPLATES[turnover_key]).format(
                    passer=short_name(event.passer),
                    target=short_name(event.target),
                    turnover_player=short_name(event.turnover_player),
                    team=team_label,
                )
            templates = TEMPLATES.get(base_key)
            if not templates:
                return f"{event.passer} gives it away."
            return random.choice(templates).format(passer=short_name(event.passer), target=short_name(event.target))

    elif isinstance(event, DribbleAttempt):
        if event.success and event.defender == "":
            key = ("dribble", "carry")
            templates = TEMPLATES.get(key, [])
            return random.choice(templates).format(dribbler=short_name(event.dribbler))
        elif event.success:
            key = ("dribble", "success")
        elif event.foul:
            key = ("dribble", "foul")
        elif event.turnover_player and TEMPLATES.get(("dribble", "fail_turnover")):
            team_label = _team_label(game_state, game_state.possessing_team)
            return random.choice(TEMPLATES[("dribble", "fail_turnover")]).format(
                dribbler=short_name(event.dribbler),
                turnover_player=short_name(event.turnover_player),
                team=team_label,
            )
        else:
            key = ("dribble", "fail")
        templates = TEMPLATES.get(key, [])
        if not templates:
            return f"{event.dribbler} attempts a dribble."
        return random.choice(templates).format(dribbler=short_name(event.dribbler), defender=short_name(event.defender))

    elif isinstance(event, ShotAttempt):
        key = ("shot", event.outcome)
        templates = TEMPLATES.get(key, [])
        if not templates:
            return f"{event.shooter} shoots — {event.outcome}."
        return random.choice(templates).format(shooter=short_name(event.shooter))

    elif isinstance(event, SetPiece):
        key = ("set_piece", event.outcome)
        templates = TEMPLATES.get(key, [])
        if not templates:
            return f"{event.taker} takes the {event.piece_type} — {event.outcome}."
        return random.choice(templates).format(taker=short_name(event.taker), piece_type=event.piece_type.replace("_", " "))

    elif isinstance(event, PhysicalDuel):
        loser = event.player_b if event.winner == event.player_a else event.player_a
        key = ("duel", "win")
        templates = TEMPLATES.get(key, [])
        if not templates:
            return f"{event.winner} wins the duel against {loser}."
        return random.choice(templates).format(winner=short_name(event.winner), loser=short_name(loser))

    elif isinstance(event, PossessionChange):
        key = ("possession_change", event.method)
        templates = TEMPLATES.get(key, [])
        if not templates:
            return f"{event.player} wins possession for {_team_label(game_state, event.team)}."
        team_label = _team_label(game_state, event.team)
        return random.choice(templates).format(player=short_name(event.player), team=team_label)

    elif isinstance(event, SpecialEvent):
        key = ("special", event.special_type)
        templates = TEMPLATES.get(key, [])
        if not templates:
            return f"{event.player} — {event.special_type}!"
        return random.choice(templates).format(player=short_name(event.player))

    return f"Phase {event.phase}: {event.event_type}"
