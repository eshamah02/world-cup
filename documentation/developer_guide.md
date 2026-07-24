# Developer Guide — Setup, Testing, Tuning, and Extending

## Setup

### Requirements
- Python 3.11+
- Dependencies: `fastapi`, `uvicorn[standard]`, `pandas`, `pydantic`, `pytest`, `pytest-asyncio`, `httpx`

### Install
macOS system Python is externally managed — always use a virtual environment:

```bash
cd world-cup/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

> You must run `source venv/bin/activate` every time you open a new terminal before running the server or tests. Your prompt will show `(venv)` when active.

### Run the server
```bash
cd world-cup/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or without activating the venv:
```bash
./venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The server loads all players from CSV on startup via the lifespan handler. This takes a few seconds on first start. After that, all player lookups are in-memory.

### Run tests
```bash
cd world-cup/backend
pytest tests/ -v
```

Run a specific test file:
```bash
pytest tests/test_phases.py -v
pytest tests/test_engine.py -v
```

Run with output (useful for debugging simulation behavior):
```bash
pytest tests/ -v -s
```

---

## API Endpoints

### `POST /simulate`
Runs a full match simulation.

**Request:**
```json
{
  "team_a": [231747, 237692, 238794],
  "team_b": [192985, 188545, 212198]
}
```

Run it with curl:
```bash
curl -X POST http://localhost:8000/simulate \
  -H "Content-Type: application/json" \
  -d '{"team_a": [231747, 237692, 238794], "team_b": [192985, 188545, 212198]}'
```

Or open `http://localhost:8000/docs` in your browser — FastAPI auto-generates a Swagger UI where you can paste the request body and click Execute.

If you don't know player IDs, search first:
```bash
curl "http://localhost:8000/players/search?q=mbappe"
```

**Response:**
```json
{
  "events": [
    {
      "phase": 1,
      "zone": "midfield",
      "event_type": "pass",
      "outcome": "",
      "text": "Mbappé plays it simple to a teammate.",
      "score": [0, 0],
      "players_involved": []
    },
    ...
  ],
  "final_score": [2, 1],
  "winner": "team_a",
  "mvp": "Kylian Mbappé",
  "team_a_names": ["Kylian Mbappé", "Jude Bellingham", "Vinícius Júnior"],
  "team_b_names": ["Kevin De Bruyne", "Virgil van Dijk", "Erling Haaland"]
}
```

**Errors:**
- `400` — duplicate player IDs across both teams
- `404` — one or more player IDs not found in the database

> Note: `team_a` and `team_b` must each contain exactly 3 player IDs.

### `GET /players/search?q=mbappe`
Returns a list of `PlayerSummary` objects matching the query. Searches name, club, and country.

### `GET /players/{player_id}`
Returns full player details as a dict.

---

## Testing Philosophy

Tests are organized by file, each testing one layer of the system:

| Test file | Tests |
|-----------|-------|
| `test_data_loader.py` | CSV loading, player lookup, search, field types |
| `test_probability.py` | Math functions, probability distributions, edge cases |
| `test_phases.py` | Player selection, action selection, action resolution, phase orchestration |
| `test_engine.py` | Full match simulation, response structure, score validity |
| `test_narrative.py` | Text generation for all event types and outcomes |

### Shared fixtures (`conftest.py`)
```python
strong_team = [Mbappé, Bellingham, Vinícius Jr]   # player IDs: 231747, 237692, 238794
weak_team   = [De Bruyne, Van Dijk, Haaland]       # player IDs: 192985, 188545, 212198
```

These are session-scoped — loaded once and reused across all tests. The `setup` fixture calls `load_players()` automatically before any test runs.

### Testing probabilistic code
Many tests run the same action 100–300 times and assert that certain outcomes occur at least once, or that distributions fall within expected ranges. This is the correct approach for probabilistic systems — you can't assert a specific outcome from a single roll, but you can assert that over many rolls the behavior is correct.

Example pattern:
```python
def test_resolve_action_shot_updates_score_on_goal(strong_team, weak_team):
    goals = 0
    for _ in range(100):
        gs = GameState(zone="final_third", possessing_team=0)
        event = resolve_action("finesse_shot", strong_team[0], weak_team[0], gs, strong_team, weak_team)
        if event.outcome == "goal":
            assert gs.score[0] == 1   # verify score updated correctly
            goals += 1
    assert goals > 0   # verify goals actually happen over 100 attempts
```

---

## Tuning the Simulation

The simulation has several tuning knobs. If the results feel wrong (too many goals, too few, too predictable), here's where to look:

### Too many goals
- Lower the base quality values in `shot_creation` dict in `probability.py`
- Lower the assisted bonus in `resolve_action` (currently +0.15)
- Increase the denominator in `shot_quality` formula (currently `finishing / 80` — try `finishing / 90`)

### Too few goals
- Raise the base quality values in `shot_creation`
- Raise the assisted bonus
- Lower the denominator in `shot_quality`

### Special events too frequent
- Increase the denominators in `special_event_check` (currently 9000 for brilliance, 3000 for error)

### Special events too rare
- Decrease the denominators

### Games feel too one-sided
- The `success_probability` formula naturally gives ~60% to a team with 90 composite vs 60 composite. If this feels too extreme, add a floor to the defender composite or reduce the spread.

### Switch play too frequent
- The switch play action weight is multiplied by `0.4` in `select_action` to prevent it dominating midfield. If you want more switch play, raise this multiplier. If games still feel too static in midfield, lower it further.

### Assisted flag not forcing shots
- When `game_state.cutback_assisted` or `game_state.dribble_assisted` is `True` in the final third, `select_action` forces a shot. If you want to allow other actions after a cutback (e.g. another dribble), remove the early return block at the top of `select_action`.

### MVP from losing team with 0 goals
- The fallback MVP now picks from the winning team only. If there's a draw, it picks the highest-rated player across both teams. This is handled in `engine.py` after the winner is determined.

### Fouls too common / rare
- Adjust the `defender.aggression / 200` formula in dribble failure paths. Dividing by 150 makes fouls more common; dividing by 250 makes them rarer.

---

## Extending the Simulation

### Adding a new action type

1. Add the action string to the appropriate zone in `zone_actions` in `select_action`
2. Add the action's weight stats to `action_stats` in `select_action`
3. Add a new `elif` branch in `resolve_action` with the composite stats, probability roll, game state mutation, and event return
4. Add narrative templates for the new action in `TEMPLATES` in `narrative.py`
5. Add tests in `test_phases.py`

### Adding a new event type

1. Define a new dataclass in `events.py` with `phase`, `zone`, and `event_type` fields
2. Add it to the `GameEvent` union type
3. Create instances of it in `resolve_action` or `resolve_set_piece`
4. Add handling in `narrate_event` in `narrative.py`
5. Add tests in `test_narrative.py`

### Adding a new stat influence

If you want a stat to influence an existing action, add it to the composite list in the relevant `resolve_action` branch. For example, to make `composure` affect power shots:

```python
# Before
atk = compute_composite(ball_carrier, ["shot_power", "long_shots"])

# After
atk = compute_composite(ball_carrier, ["shot_power", "long_shots", "composure"])
```

You can also add weights to emphasize certain stats:
```python
atk = compute_composite(ball_carrier, ["shot_power", "long_shots", "composure"], [0.5, 0.3, 0.2])
```

### Adding momentum effects

`game_state.momentum` tracks consecutive possession phases per team but currently only affects narrative feel. To add a mechanical effect:

In `resolve_phase`, after updating momentum, apply a modifier:
```python
# Example: composure penalty after 5+ consecutive defending phases
if game_state.momentum[1 - game_state.possessing_team] >= 5:
    # defending team has been under pressure — apply penalty
    # could reduce their composite scores in the next resolve_action call
    pass
```

### Adding stamina degradation

`PlayerProfile` has a `stamina` field. To simulate fatigue:
- Track a `fatigue: list[float]` in `GameState` (one per team, starting at 1.0)
- Reduce fatigue each phase: `fatigue[team] *= 0.99`
- Multiply composites by the fatigue factor in `resolve_action`

### Changing match length

`total_phases = random.randint(24, 30)` in `engine.py`. Adjust the range to make matches longer or shorter. More phases = more events = higher scores on average.

Note: after the main loop, one extra phase runs if the ball is in `final_third` or `set_piece` to avoid the match ending mid-attack. The `MatchEvent` phase cap (`le=32` in `models.py`) accounts for this.

---

## Common Issues

### `ModuleNotFoundError: No module named 'fastapi'` (or any dependency)
The venv is not active, or you're using the system/Homebrew uvicorn instead of the venv one. Run `source venv/bin/activate` first, then confirm with `which uvicorn` — it should point to `venv/bin/uvicorn`, not `/opt/homebrew/...`.

### `ModuleNotFoundError: No module named 'data_loader'`
Imports inside `app/` must use the `app.` prefix (e.g. `from app.data_loader import ...`) because the server runs from the `backend/` directory, not from inside `app/`. Also ensure `app/__init__.py` and `app/simulation/__init__.py` exist — without them Python won't treat those directories as packages.

### `TypeError: CORSMiddleware.__init__() missing 1 required positional argument: 'app'`
`add_middleware` takes the middleware class as the first argument, not an instance. Use:
```python
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
```
not `app.add_middleware(CORSMiddleware(...))` — FastAPI handles instantiation internally.

### `TypeError: Unable to apply constraint 'ge' to supplied value [...]`
Pydantic's `ge`/`le` are numeric constraints and can't be applied to lists. Use `min_length`/`max_length` instead for list fields:
```python
team_a: list[int] = Field(min_length=3, max_length=3)
```

### `ValueError: Player with id X not found`
The player ID doesn't exist in the CSV. Check that `load_players()` was called before `get_player()`. In tests, the `setup` fixture in `conftest.py` handles this automatically.

### `ValidationError: phase — Input should be greater than or equal to 1`
`MatchEvent` requires `phase >= 1` but `GameState.phase_number` is 0-indexed. The fix is `phase=event.phase + 1` when constructing `MatchEvent` in `engine.py`.

### `KeyError` in `shot_quality`
The creation method string passed to `shot_quality` doesn't exist in `shot_creation`. Check the `creation_map` in `resolve_action` — the keys must exactly match the keys in `shot_creation` in `probability.py`.

### Narrative returns generic fallback text
A template key is missing from `TEMPLATES` in `narrative.py`. The fallback `return f"{event.passer} plays a {event.pass_type} pass."` fires when the key isn't found. Add the missing template.

### `Phases skipped or two events share the same phase number`
Special events (brilliance/error) were stamping the phase number after incrementing instead of before. The fix is to construct the event with `phase=game_state.phase_number` and then call `game_state.phase_number += 1` — the same order as normal actions.
Shot quality values are too low, or the simulation is never reaching the final third. Add print statements in `resolve_phase` to trace zone transitions and verify the ball is reaching `final_third` and shots are being attempted.

---

## Data Source

Player stats come from the FC26 SoFIFA dataset (`data/fc26_sofifa_player_stats.csv`). The CSV column names use prefixed format (`attacking_finishing`, `skill_dribbling`, etc.) which are mapped to clean field names by `COLUMN_MAP` in `data_loader.py`.

To update to a new season's data, replace the CSV file and verify the column names still match `COLUMN_MAP`. If SoFIFA changes column naming conventions, update `COLUMN_MAP` accordingly.
