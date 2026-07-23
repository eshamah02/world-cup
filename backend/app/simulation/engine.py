import random
from app.player_profile import PlayerProfile
from app.simulation.phases import GameState, resolve_phase
from app.simulation.events import ShotAttempt, SpecialEvent
from app.simulation.narrative import narrate_event
from app.models import MatchResponse, MatchEvent

def simulate_match(team_a: list[PlayerProfile], team_b: list[PlayerProfile]) -> MatchResponse:
    total_phases = random.randint(24, 30)
    game_state = GameState(
        possessing_team=random.randint(0, 1),
        total_phases=total_phases
    )
    match_events = []
    goal_involvements = {}

    while game_state.phase_number < total_phases:
        phase_events = resolve_phase(game_state, team_a, team_b)
        score_now = game_state.score[:]

        for event in phase_events:
            text = narrate_event(event, game_state)
            match_events.append(MatchEvent(
                phase=event.phase,
                zone=event.zone,
                event_type=event.event_type,
                outcome=getattr(event, "outcome", ""),
                text=text,
                score=score_now,
                players_involved=[]
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
