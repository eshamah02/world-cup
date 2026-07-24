import random
from app.player_profile import PlayerProfile
from app.simulation.phases import GameState, resolve_phase
from app.simulation.events import ShotAttempt, SpecialEvent
from app.simulation.narrative import narrate_event, short_name
from app.models import MatchResponse, MatchEvent


def short_team_name(team: list[PlayerProfile]) -> str:
    """Derive a short display label for a team from its players' surnames."""
    surnames = [short_name(p.name).split()[-1] for p in team]
    return " & ".join(surnames)

def simulate_match(team_a: list[PlayerProfile], team_b: list[PlayerProfile]) -> MatchResponse:
    total_phases = random.randint(24, 30)
    game_state = GameState(
        possessing_team=random.randint(0, 1),
        total_phases=total_phases,
        team_names=[short_team_name(team_a), short_team_name(team_b)]
    )
    match_events = []
    goal_involvements = {}

    while game_state.phase_number < total_phases:
        phase_events = resolve_phase(game_state, team_a, team_b)

        for event in phase_events:
            text = narrate_event(event, game_state)
            match_events.append(MatchEvent(
                phase=event.phase + 1,
                zone=event.zone,
                event_type=event.event_type,
                outcome=getattr(event, "outcome", ""),
                text=text,
                score=event.score
            ))

            if isinstance(event, ShotAttempt) and event.outcome == "goal":
                goal_involvements[event.shooter] = goal_involvements.get(event.shooter, 0) + 1
                if event.assister:
                    goal_involvements[event.assister] = goal_involvements.get(event.assister, 0) + 1
            elif isinstance(event, SpecialEvent) and event.resulted_in_goal:
                goal_involvements[event.player] = goal_involvements.get(event.player, 0) + 1

    # keep running extra phases until the ball leaves the final third or set piece
    # cap at 4 extra phases to prevent infinite loops
    extra = 0
    while game_state.zone in ("final_third", "set_piece") and extra < 4:
        extra += 1
        for event in resolve_phase(game_state, team_a, team_b):
            text = narrate_event(event, game_state)
            match_events.append(MatchEvent(
                phase=event.phase + 1,
                zone=event.zone,
                event_type=event.event_type,
                outcome=getattr(event, "outcome", ""),
                text=text,
                score=event.score
            ))
            if isinstance(event, ShotAttempt) and event.outcome == "goal":
                goal_involvements[event.shooter] = goal_involvements.get(event.shooter, 0) + 1
                if event.assister:
                    goal_involvements[event.assister] = goal_involvements.get(event.assister, 0) + 1
            elif isinstance(event, SpecialEvent) and event.resulted_in_goal:
                goal_involvements[event.player] = goal_involvements.get(event.player, 0) + 1

    if game_state.score[0] > game_state.score[1]:
        winner = "team_a"
    elif game_state.score[1] > game_state.score[0]:
        winner = "team_b"
    else:
        winner = None

    if goal_involvements:
        mvp = max(goal_involvements, key=lambda name: goal_involvements[name])
    elif winner == "team_a":
        mvp = max(team_a, key=lambda p: p.overall_rating).name
    elif winner == "team_b":
        mvp = max(team_b, key=lambda p: p.overall_rating).name
    else:
        mvp = max(team_a + team_b, key=lambda p: p.overall_rating).name

    return MatchResponse(
        events=match_events,
        final_score=game_state.score,
        winner=winner,
        mvp=mvp,
        team_a_names=[p.name for p in team_a],
        team_b_names=[p.name for p in team_b]
    )
