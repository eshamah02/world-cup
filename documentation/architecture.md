# Architecture — File Responsibilities and System Design

## Directory Structure

```
world-cup/
├── backend/
│   ├── app/
│   │   ├── player_profile.py       # PlayerProfile dataclass
│   │   ├── data_loader.py          # CSV → PlayerProfile objects
│   │   ├── models.py               # API request/response Pydantic models
│   │   ├── main.py                 # FastAPI app and endpoints
│   │   └── simulation/
│   │       ├── probability.py      # Math: stats → probabilities
│   │       ├── events.py           # Event dataclasses
│   │       ├── phases.py           # Single phase resolution
│   │       ├── engine.py           # Match loop orchestrator
│   │       └── narrative.py        # Events → text strings
│   ├── data/
│   │   └── fc26_sofifa_player_stats.csv
│   ├── tests/
│   │   ├── test_data_loader.py
│   │   ├── test_probability.py
│   │   ├── test_phases.py
│   │   ├── test_engine.py
│   │   └── test_narrative.py
│   └── conftest.py
├── frontend/
└── documentation/
```

---

## File Responsibilities

### `player_profile.py` — The Data Shape
**What it is:** Pure data definition. No logic, no I/O, no imports from other app files.

**What it contains:** The `PlayerProfile` dataclass with all 40+ player stat fields.

**Why it's separate:** Every other file imports `PlayerProfile`. If it lived in `data_loader.py`, any file that needed the type but not the loading logic would create a circular import. Keeping it isolated means any file can import it without pulling in pandas or CSV logic.

**Knows about:** Nothing.
**Doesn't know about:** Everything else.

---

### `data_loader.py` — CSV to Python Objects
**What it is:** The bridge between the raw CSV file and the rest of the application. Reads once at startup, stores in memory, serves player objects on demand.

**What it contains:**
- `COLUMN_MAP` — maps CSV column names to `PlayerProfile` field names (e.g., `"attacking_finishing"` → `"finishing"`)
- `INT_FIELDS` — list of fields that should be cast to int
- `_players: dict[int, PlayerProfile]` — the in-memory store, keyed by player_id
- `parse_list()` — converts comma-separated strings to lists, strips `#` prefixes from specialities
- `_row_to_player()` — converts one pandas row to a `PlayerProfile`
- `load_players()` — reads the CSV, populates `_players`
- `get_player()` — lookup by ID, raises `ValueError` if not found
- `get_all_players()` — returns all players
- `search_players()` — name/club/country substring search

**When it runs:** `load_players()` is called once at app startup via the FastAPI lifespan handler. After that, all lookups are in-memory dictionary reads — O(1) per player.

**Knows about:** CSV format, pandas, `PlayerProfile`.
**Doesn't know about:** Simulation logic, API, probability math.

---

### `models.py` — API Contracts
**What it is:** Pydantic models defining what the API accepts and returns. The contract between frontend and backend.

**What it contains:** `MatchRequest`, `MatchEvent`, `MatchResponse`, `PlayerSummary`.

**Why Pydantic:** FastAPI uses Pydantic models for automatic request validation and JSON serialization. If the frontend sends `team_a` with 4 players instead of 3, Pydantic rejects it before any simulation code runs.

**Knows about:** Pydantic, response shapes.
**Doesn't know about:** Simulation internals, CSV, probability math.

---

### `main.py` — API Endpoints
**What it is:** The FastAPI application. Thin layer — receives requests, calls the right functions, returns responses.

**What it contains:**
- App initialization with CORS middleware
- Lifespan handler that calls `load_players()` at startup
- `GET /players/search?q=` — player search
- `GET /players/{player_id}` — single player lookup
- `POST /simulate` — accepts `MatchRequest`, fetches players, runs simulation, returns `MatchResponse`

**What it does NOT contain:** Any simulation logic, probability math, data parsing.

**Knows about:** FastAPI, `data_loader`, `engine`, `models`.
**Doesn't know about:** Probability math, phases, events, narrative.

---

### `simulation/probability.py` — The Math
**What it is:** Pure functions that convert stats into probabilities. No game state, no events, no side effects.

**What it contains:**
- `compute_composite()` — weighted average of stats
- `success_probability()` — two composites → float 0.05–0.95
- `roll()` — random check → True/False
- `shot_quality()` — creation method + shooter stats → goal probability
- `special_event_check()` — player + event type → True/False

**Why it's separate:** These are the tuning knobs. When games have too many goals or too few, you adjust formulas here without touching game logic. Unit testing is also clean — you can test probability functions with hardcoded stats without needing a full game state.

**Knows about:** `PlayerProfile` stats.
**Doesn't know about:** Game state, events, narrative, API.

---

### `simulation/events.py` — Event Data Structures
**What it is:** Dataclasses representing things that happen in a match. No logic — just containers.

**What it contains:** `PassAttempt`, `DribbleAttempt`, `ShotAttempt`, `SetPiece`, `PhysicalDuel`, `SpecialEvent`, `PossessionChange`, and the `GameEvent` union type.

**Why it's separate:** Events are created in `phases.py`, collected in `engine.py`, and consumed in `narrative.py`. If event definitions lived in any of those files, the others would need to import from them, creating coupling. A separate file means all three can import from `events.py` without depending on each other.

**Knows about:** Nothing (just Python dataclasses).
**Doesn't know about:** Everything else.

---

### `simulation/phases.py` — One Tick of the Game
**What it is:** The decision-making brain. Given the current game state, determines what happens in one phase.

**What it contains:**
- `GameState` dataclass
- `ZONE_ORDER` constant
- `pick_ball_carrier()` — weighted selection of who's on the ball
- `pick_defender()` — weighted selection of who's defending
- `select_action()` — weighted selection of what action to attempt
- `resolve_action()` — resolves the chosen action, mutates game state, returns event
- `resolve_set_piece()` — resolves a dead ball situation
- `resolve_phase()` — orchestrates one full phase tick

**Why it's the hardest file:** It ties together probability math, event creation, and game state mutation. Every action type has its own logic. It's also the file most likely to need tuning — if the simulation feels wrong, the action resolution logic is where you look first.

**Knows about:** `probability`, `events`, `PlayerProfile`, `GameState`.
**Doesn't know about:** Narrative, API, CSV.

---

### `simulation/engine.py` — The Game Loop
**What it is:** Orchestrates a full match from start to finish.

**What it contains:** `simulate_match()` — the only function. Creates `GameState`, loops calling `resolve_phase()`, collects events, builds `MatchEvent` objects, determines winner, picks MVP, returns `MatchResponse`.

**Why it's intentionally simple:** The engine delegates everything to `phases.py` and `narrative.py`. Its only job is the loop and the final assembly. This makes it easy to test — you can verify the loop runs the right number of times, the score is tracked correctly, and the response is built properly, without needing to understand phase resolution.

**Knows about:** `phases`, `narrative`, `events`, `models`, `PlayerProfile`.
**Doesn't know about:** Probability details, CSV, individual action logic.

---

### `simulation/narrative.py` — Text Generation
**What it is:** Converts structured event objects into human-readable play-by-play text.

**What it contains:**
- `TEMPLATES` dictionary — keyed by `(event_type, outcome)` → list of template strings
- `narrate_event()` — looks up the right template list, picks randomly, formats with player names

**Why random template selection:** 3–5 templates per event/outcome combination means the same type of event doesn't always produce the same sentence. Over a 27-phase match, this creates variety in the commentary.

**Knows about:** `events`, `GameState`.
**Doesn't know about:** Probability, game logic, API, CSV.

---

## Full Data Flow

```
Frontend
  │
  │  POST /simulate
  │  { "team_a": [231747, 237692, 238794],
  │    "team_b": [192985, 188545, 212198] }
  ▼
main.py
  │  Validates MatchRequest (Pydantic)
  │  Checks for duplicate player IDs
  │  Calls get_player() × 6
  ▼
data_loader.py
  │  Returns 6 PlayerProfile objects from _players dict
  ▼
main.py
  │  Calls simulate_match(team_a_players, team_b_players)
  ▼
engine.py
  │  Creates GameState (coin flip possession, random total_phases)
  │  Loops while phase_number < total_phases:
  │    ├── Calls resolve_phase(game_state, team_a, team_b)
  │    │     ├── Checks set_piece zone → resolve_set_piece if needed
  │    │     ├── pick_ball_carrier() → PlayerProfile
  │    │     ├── pick_defender() → PlayerProfile
  │    │     ├── special_event_check() → maybe return early
  │    │     ├── select_action() → action string
  │    │     └── resolve_action() → GameEvent + mutates GameState
  │    │           └── compute_composite() × 2
  │    │               success_probability()
  │    │               roll()
  │    │               [shot_quality() for shots]
  │    ├── Snapshots score
  │    ├── Calls narrate_event(event, game_state) → str
  │    └── Builds MatchEvent, appends to match_events
  │  Determines winner from final score
  │  Picks MVP from goal_involvements
  │  Returns MatchResponse
  ▼
main.py
  │  Returns MatchResponse (FastAPI serializes to JSON)
  ▼
Frontend receives JSON play-by-play
```

---

## Dependency Graph

```
player_profile.py
       ↑
       │ (imports PlayerProfile)
       ├──────────────────────────────────────────┐
       │                                          │
data_loader.py                            probability.py
       ↑                                          ↑
       │                                          │
       │                                   phases.py ←── events.py
       │                                          ↑
       │                                          │
       │                                    engine.py ←── narrative.py
       │                                          ↑
       │                                          │
       └──────────────────────────────────── main.py ←── models.py
```

Arrows point from importer to imported. `main.py` is the only file that imports from both the data layer (`data_loader`) and the simulation layer (`engine`). The simulation files form a clean internal hierarchy with no circular dependencies.

---

## What Each File Knows About

| File | Knows About | Doesn't Know About |
|------|------------|-------------------|
| `player_profile.py` | Nothing | Everything |
| `data_loader.py` | CSV, pandas, `PlayerProfile` | Simulation, API |
| `models.py` | Pydantic, response shapes | Simulation, CSV |
| `main.py` | FastAPI, `data_loader`, `engine`, `models` | Probability math, phases |
| `probability.py` | `PlayerProfile` stats | Game state, events, narrative |
| `events.py` | Python dataclasses | Everything else |
| `phases.py` | `probability`, `events`, `PlayerProfile`, `GameState` | Narrative, API, CSV |
| `engine.py` | `phases`, `narrative`, `events`, `models` | Probability details, CSV |
| `narrative.py` | `events`, `GameState` | Probability, game logic, API |
