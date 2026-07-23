# Data Models — All Data Structures

## Overview

The system uses three categories of data structures:
1. **Player data** — `PlayerProfile` dataclass, loaded from CSV
2. **Simulation state** — `GameState` dataclass and event dataclasses, used internally during a match
3. **API models** — Pydantic models defining what the API accepts and returns

---

## PlayerProfile

**File:** `player_profile.py`

The central data structure. Every player in the database is represented as a `PlayerProfile`. It is a pure data container — no methods, no logic, just fields.

```python
@dataclass
class PlayerProfile:
    # Identity
    player_id: int          # unique identifier (matches SoFIFA ID)
    name: str               # display name (e.g., "Kylian Mbappé")
    full_name: str          # full legal name
    image: str              # URL to player image
    height_cm: int
    weight_kg: int
    dob: str                # date of birth
    positions: list[str]    # e.g., ["ST", "LW", "LM"]
    overall_rating: int     # 1-99
    potential: int          # 1-99
    preferred_foot: str     # "Left" or "Right"
    weak_foot: int          # 1-5 star rating
    skill_moves: int        # normalized: original 1-5 * 20 = 20-100
    international_reputation: int  # 1-5
    body_type: str

    # Club and country info
    club_name: str
    club_league_name: str
    club_position: str
    club_kit_number: int
    country_name: str
    country_position: str
    country_kit_number: int

    # Attacking (0-99)
    crossing: int
    finishing: int
    heading_accuracy: int
    short_passing: int
    volleys: int

    # Skill (0-99)
    dribbling: int
    curve: int
    fk_accuracy: int
    long_passing: int
    ball_control: int

    # Movement (0-99)
    acceleration: int
    sprint_speed: int
    agility: int
    reactions: int
    balance: int

    # Power (0-99)
    shot_power: int
    jumping: int
    stamina: int
    strength: int
    long_shots: int

    # Mentality (0-99)
    aggression: int
    interceptions: int
    vision: int
    penalties: int
    composure: int
    attack_position: int

    # Defending (0-99)
    defensive_awareness: int
    standing_tackle: int
    sliding_tackle: int

    # Goalkeeping (0-99)
    gk_diving: int
    gk_handling: int
    gk_kicking: int
    gk_positioning: int
    gk_reflexes: int

    # Meta
    specialities: list[str]   # e.g., ["Speedster", "Dribbler"]
    play_styles: list[str]    # e.g., ["Quick step", "Finesse shot"]
    value: int                # market value in euros
    wage: int                 # weekly wage in euros
```

**Important note on `skill_moves`:** The raw CSV value is a 1–5 star rating. During loading in `data_loader.py`, it is multiplied by 20 to normalize it to the 0–100 scale used by all other stats. This allows it to be used directly in `compute_composite` alongside other stats without special handling.

---

## GameState

**File:** `phases.py`

Tracks the current state of the match. A single `GameState` object is created at the start of each match and mutated in place throughout. Every call to `resolve_phase` reads from and writes to this object.

```python
@dataclass
class GameState:
    zone: str = "midfield"
    # Current ball position: "buildup", "midfield", "final_third", "set_piece"

    possessing_team: int = 0
    # Which team has the ball: 0 = team_a, 1 = team_b

    score: list[int] = field(default_factory=lambda: [0, 0])
    # [team_a_goals, team_b_goals]

    phase_number: int = 0
    # Current phase (0-indexed internally, 1-indexed in API output)

    total_phases: int = 25
    # Total phases for this match (randomized 24-30 at match start)

    momentum: list[int] = field(default_factory=lambda: [0, 0])
    # Consecutive possession phases per team: [team_a_streak, team_b_streak]

    last_event: str = ""
    # Type of the last event: "pass", "dribble", "shot"

    cutback_assisted: bool = False
    # Set True by a successful cutback. Forces a shot next phase with +0.15 quality bonus.
    # Suppresses the bridging pass since the cutback text already names the recipient.
    # Cleared after shot resolves or on any possession flip, set piece, or special event.

    dribble_assisted: bool = False
    # Set True by a successful dribble_into_box. Forces a shot next phase with +0.15 quality bonus.
    # Does NOT suppress the bridging pass — dribble_into_box names no recipient.
    # Cleared after shot resolves or on any possession flip, set piece, or special event.

    set_piece_type: str = "free_kick"
    # Type of set piece to resolve: "free_kick" or "corner"

    last_ball_carrier: str = ""
    # Name of the player who ended the previous phase with the ball.
    # Used to emit bridging pass events when the ball carrier changes within
    # the same possession. Reset to "" on possession flip, set piece,
    # special event, or physical duel win.

    through_ball_receiver: str = ""
    # Name of the player who was named as the receiver of a successful through ball.
    # On the very next phase, this player is locked in as ball carrier instead of
    # calling pick_ball_carrier, ensuring the named runner actually gets the ball.
    # Cleared after use and on any possession flip, set piece, or special event.
```

**Mutation pattern:** `GameState` is mutated in place by `resolve_action` and `resolve_set_piece`. The caller (`resolve_phase`) passes it in and reads the updated state after the call returns. This means the state flows through the entire match as a single shared object — no copying, no returning new state objects.

---

## Event Dataclasses

**File:** `events.py`

Each event represents one thing that happened in a phase. Events are created inside `resolve_action` and `resolve_set_piece`, collected by `engine.py`, and passed to `narrative.py` for text generation.

All events share `phase` and `zone` fields. The `event_type` field is a string constant with a default value — it identifies the event type without needing `isinstance` checks in the narrative layer.

### `PassAttempt`
```python
@dataclass
class PassAttempt:
    phase: int
    zone: str           # zone where the pass was attempted
    passer: str         # player name
    target: str         # receiver name — always a real player name for all pass types
    pass_type: str      # "short", "long", "through_ball", "switch", "cutback"
    success: bool
    turnover_player: str = ""  # name of the defender who won the ball on a failed pass; empty on success
    score: list         # score snapshot at the time this event was created
    event_type: str = "pass"
```

### `DribbleAttempt`
```python
@dataclass
class DribbleAttempt:
    phase: int
    zone: str
    dribbler: str
    defender: str       # empty string "" for carry events (post-duel zone bridge)
    success: bool
    foul: bool          # True if defender committed a foul on the failed attempt
    turnover_player: str = ""  # name of the defender who won the ball on a failed non-foul dribble; empty on success or foul
    score: list         # score snapshot at the time this event was created
    event_type: str = "dribble"
```

Note: `foul` is only ever True when `success` is False. A successful dribble never produces a foul. `turnover_player` is only set when `success` is False and `foul` is False — the defender who cleanly won the ball.

Carry events are `DribbleAttempt` instances with `success=True` and `defender=""`. They are emitted after a physical duel win to bridge the zone jump narratively. The narrative layer detects the empty defender and routes them to the `("dribble", "carry")` template.

### `ShotAttempt`
```python
@dataclass
class ShotAttempt:
    phase: int
    zone: str
    shooter: str
    shot_type: str      # "finesse_shot", "power_shot", "header"
    quality: float      # xG-like value 0.0-1.0, the actual probability used
    outcome: str        # "goal", "save", "block", "miss"
    assister: str | None  # name of the player who created the chance, or None
    score: list         # score snapshot after this event (includes the goal if scored)
    event_type: str = "shot"
```

### `SetPiece`
```python
@dataclass
class SetPiece:
    phase: int
    zone: str           # always "set_piece"
    taker: str
    piece_type: str     # "free_kick" or "corner"
    outcome: str        # "goal", "save", "cleared"
    score: list         # score snapshot after this event
    event_type: str = "set_piece"
```

### `PhysicalDuel`
```python
@dataclass
class PhysicalDuel:
    phase: int
    zone: str
    player_a: str       # the ball carrier
    player_b: str       # the defender
    winner: str         # name of whoever won the contest
    score: list         # score snapshot at the time this event was created
    event_type: str = "duel"
```

### `SpecialEvent`
```python
@dataclass
class SpecialEvent:
    phase: int
    zone: str
    player: str
    special_type: str       # "brilliance" or "error"
    description: str        # "solo_run", "misplaced_backpass", etc.
    resulted_in_goal: bool
    score: list             # score snapshot after this event (includes the goal if brilliance)
    event_type: str = "special"
```

### `PossessionChange`
```python
@dataclass
class PossessionChange:
    phase: int
    zone: str
    player: str         # player who won the ball
    method: str         # "duel" (currently); extensible to "interception", "tackle", etc.
    team: int           # team that now has possession (0 = team_a, 1 = team_b)
    score: list         # score snapshot at the time this event was created
    event_type: str = "possession_change"
```

Note: `PossessionChange` is currently emitted after a lost `physical_duel` to explicitly name who won the ball and which team now has possession. For pass and dribble turnovers, the winner is named inline via `turnover_player` on the originating event rather than as a separate event.

### `GameEvent` type alias
```python
GameEvent = PossessionChange | PassAttempt | DribbleAttempt | ShotAttempt | SetPiece | PhysicalDuel | SpecialEvent
```

This union type is used as the return type annotation for functions that can return any event type.

---

## API Models

**File:** `models.py`

Pydantic models define the contract between the frontend and backend. They handle validation automatically — if the frontend sends invalid data, Pydantic rejects it before it reaches any simulation code.

### `MatchRequest`
What the frontend sends to start a simulation.
```python
class MatchRequest(BaseModel):
    team_a: list[int]   # exactly 3 player IDs
    team_b: list[int]   # exactly 3 player IDs
```

The `Field(ge=3, le=3)` constraint enforces exactly 3 players per team at the Pydantic validation level.

### `MatchEvent`
One event in the play-by-play, as returned to the frontend.
```python
class MatchEvent(BaseModel):
    phase: int          # 1-indexed phase number (ge=1, le=30)
    zone: str           # zone where the event occurred
    event_type: str     # "pass", "dribble", "shot", "duel", "set_piece", "special"
    outcome: str        # event-specific outcome string
    text: str           # human-readable narrative text
    score: list[int]    # score at the time of this event, read from event.score
```

The `score` field reflects the state at the moment the event was created — not the end-of-phase state. This means a bridging pass before a goal shows the pre-goal score, and the goal event itself shows the updated score.

### `MatchResponse`
The full match result returned to the frontend.
```python
class MatchResponse(BaseModel):
    events: list[MatchEvent]    # full play-by-play
    final_score: list[int]      # [team_a_goals, team_b_goals]
    winner: str | None          # "team_a", "team_b", or None for draw
    mvp: str                    # player name
    team_a_names: list[str]     # names of team_a players in order
    team_b_names: list[str]     # names of team_b players in order
```

### `PlayerSummary`
Lightweight player info for search results and player browsing.
```python
class PlayerSummary(BaseModel):
    player_id: int
    name: str
    image: str
    overall_rating: str     # note: stored as string for display flexibility
    club_name: str
    country_name: str
    positions: list[str]
```

---

## Data Flow Between Models

```
CSV row
  ↓ data_loader._row_to_player()
PlayerProfile (dataclass)
  ↓ engine.simulate_match()
GameState (dataclass) + list[GameEvent] (dataclasses)
  ↓ narrative.narrate_event()
str (text for each event)
  ↓ engine builds MatchEvent for each event
MatchEvent (Pydantic)
  ↓ engine returns MatchResponse
MatchResponse (Pydantic)
  ↓ FastAPI serializes to JSON
Frontend receives JSON
```
