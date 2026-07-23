# Stats and Probability — The Math Behind the Simulation

## Philosophy

Every number in this simulation comes from a real player stat. There is no hidden randomness that ignores player quality — the randomness is always weighted by the players involved. A 95-finishing player converts more shots than a 70-finishing player, every time, across many simulations. But in any single simulation, the 70-finishing player might score and the 95-finishing player might miss. That's football.

---

## Player Stats — The Raw Inputs

Every player has stats on a 0–99 scale (with `skill_moves` normalized from a 1–5 star rating to 0–100 by multiplying by 20 during data loading).

Stats are grouped into categories:

| Category | Stats |
|----------|-------|
| Attacking | crossing, finishing, heading_accuracy, short_passing, volleys |
| Skill | dribbling, curve, fk_accuracy, long_passing, ball_control |
| Movement | acceleration, sprint_speed, agility, reactions, balance |
| Power | shot_power, jumping, stamina, strength, long_shots |
| Mentality | aggression, interceptions, vision, penalties, composure, attack_position |
| Defending | defensive_awareness, standing_tackle, sliding_tackle |
| Goalkeeping | gk_diving, gk_handling, gk_kicking, gk_positioning, gk_reflexes |

In a 3v3 match without a goalkeeper, the goalkeeping stats are not used in simulation. Defensive outfield stats absorb the goalkeeper's role.

---

## `compute_composite`

**File:** `probability.py`

**Purpose:** Converts multiple stats into a single number representing a player's ability for a specific task.

**Formula:**
```
composite = sum(stat * weight for each stat) / sum(weights)
```

If no weights are provided, all stats are weighted equally (weight = 1 for each).

**Examples:**
```python
# Equal weights — simple average
compute_composite(mbappe, ["finishing", "shot_power", "composure"])
# = (94 + 91 + 88) / 3 = 91.0

# Custom weights — finishing matters most
compute_composite(mbappe, ["finishing", "shot_power", "composure"], [0.5, 0.3, 0.2])
# = (94*0.5 + 91*0.3 + 88*0.2) / 1.0 = 92.1
```

**Why this approach:** Different actions require different combinations of stats. A short pass requires passing accuracy, ball control, and composure — but not equally. By specifying which stats matter and optionally weighting them, each action gets a precise measure of the relevant ability.

In the current implementation, all composites use equal weights (no weights argument passed). Custom weights are available for future tuning.

---

## `success_probability`

**File:** `probability.py`

**Purpose:** Converts two composite scores (attacker vs defender) into a probability that the attacker succeeds.

**Formula:**
```
base = attacker / (attacker + defender)
noise = random.uniform(-0.05, 0.05)
result = clamp(base + noise, 0.05, 0.95)
```

**Properties:**
- When composites are equal (e.g., both 75), base = 0.5 — a true 50/50
- When attacker is much stronger (90 vs 60), base = 0.60 — attacker wins 60% of the time
- When attacker is much weaker (60 vs 90), base = 0.40 — attacker wins 40% of the time
- The ±5% noise prevents perfectly equal matchups from alternating predictably
- Clamped to [0.05, 0.95] — nothing is ever guaranteed or impossible

**Example matchups:**

| Attacker | Defender | Base probability | Interpretation |
|----------|----------|-----------------|----------------|
| 90 | 90 | ~0.50 | Even contest |
| 90 | 60 | ~0.60 | Attacker favored |
| 95 | 50 | ~0.66 | Attacker strongly favored |
| 60 | 90 | ~0.40 | Defender favored |
| 99 | 1 | 0.95 (clamped) | Near certain success |
| 1 | 99 | 0.05 (clamped) | Near certain failure |

**Why this formula:** `a / (a + b)` is a natural way to express relative strength. It gives intuitive results — if you're twice as good as your opponent, you win two-thirds of the time. It scales smoothly across the full stat range without needing manual calibration.

---

## `roll`

**File:** `probability.py`

**Purpose:** The core dice roll. Takes a probability and returns True or False.

**Formula:**
```python
return random.random() < probability
```

`random.random()` returns a float uniformly distributed between 0.0 and 1.0. If the probability is 0.6, then 60% of the time `random.random()` will be less than 0.6, and `roll` returns True.

This is used everywhere in the simulation. Every action resolution, every foul check, every shot outcome — all go through `roll`.

---

## `shot_quality`

**File:** `probability.py`

**Purpose:** Calculates the probability that a shot results in a goal, based on how the chance was created and the shooter's finishing ability.

**Formula:**
```
quality = base_quality[creation_method] * (shooter.finishing / 80)
quality = clamp(quality, 0.02, 0.85)
```

**Base qualities by creation method:**

| Creation method | Base quality | Interpretation |
|----------------|-------------|----------------|
| dribble_into_box | 0.45 | Inside the box, beaten the defender |
| cutback | 0.40 | Pulled back across goal, clean look |
| through_ball | 0.35 | Clean through on goal |
| header | 0.25 | Aerial chance, harder to convert |
| volley | 0.15 | First-time aerial effort |
| free_kick | 0.10 | Dead ball from distance |
| long_shot | 0.08 | Speculative effort from range |

**Finishing modifier:** `finishing / 80` normalizes finishing around 1.0 at 80 finishing. A player with exactly 80 finishing gets the base quality unchanged. A player with 94 finishing (Mbappé) gets `94/80 = 1.175` — a 17.5% boost. A player with 60 finishing gets `60/80 = 0.75` — a 25% reduction.

**Why 80 as the baseline:** 80 is approximately the finishing stat of a solid professional striker. Elite players (90+) get a meaningful bonus; average players (60-70) get a meaningful penalty; the baseline player gets exactly the designed base quality.

**Example calculations:**

| Player | Finishing | Creation | Base | Quality |
|--------|-----------|----------|------|---------|
| Mbappé | 94 | cutback | 0.40 | 0.47 |
| Mbappé | 94 | cutback + assisted | 0.40 | 0.62 |
| Average | 75 | through_ball | 0.35 | 0.33 |
| Average | 75 | long_shot | 0.08 | 0.075 |
| Poor finisher | 55 | cutback | 0.40 | 0.275 |

**Assisted bonus:** When `game_state.assisted == True`, a flat +0.15 is added to quality before clamping. This represents the premium nature of a cutback or dribble-into-box chance — the goalkeeper is out of position, the defender is beaten, the shooter has time and space.

---

## `special_event_check`

**File:** `probability.py`

**Purpose:** Determines whether a special event (brilliance or error) fires for a given player.

**Brilliance formula:**
```
chance = (overall_rating + skill_moves + composure) / 9000
```

For Mbappé (91 overall, 100 skill_moves after normalization, 88 composure):
```
chance = (91 + 100 + 88) / 9000 = 0.031 = 3.1% per phase
```

Over a 27-phase match, the probability of at least one brilliance moment:
```
1 - (1 - 0.031)^27 = 1 - 0.969^27 ≈ 57%
```

**Error formula:**
```
chance = (200 - composure - ball_control) / 3000
```

For a player with 65 composure and 70 ball_control:
```
chance = (200 - 65 - 70) / 3000 = 65/3000 = 0.022 = 2.2% per phase
```

For an elite player with 88 composure and 90 ball_control:
```
chance = (200 - 88 - 90) / 3000 = 22/3000 = 0.007 = 0.7% per phase
```

**Why these formulas:**
- Brilliance scales with overall quality, technical flair (skill_moves), and mental composure — the combination of being good enough, creative enough, and calm enough to produce something extraordinary
- Error scales inversely with composure and ball_control — players who are mentally fragile or technically poor make more mistakes
- The denominators (9000 and 3000) are tuned to produce realistic rates: ~3-5% brilliance for elite players, ~2-4% errors for average players

---

## Foul Probability

**Used in:** `dribble_carry`, `skill_move`, `dribble_into_box` failure paths

**Formula:**
```python
foul = roll(defender.aggression / 200)
```

A defender with 90 aggression has a 45% chance of fouling when they fail to win the ball cleanly. A defender with 40 aggression has a 20% chance.

This only triggers on the failure path — if the dribble succeeds, no foul check happens. The foul check represents a defender who couldn't win the ball fairly and resorted to a foul.

**Why `/ 200`:** Aggression stats typically range from 40–95. Dividing by 200 maps this to a 20–47.5% foul probability range. This feels realistic — aggressive defenders foul regularly but not every time, and calm defenders rarely foul.

---

## Shot Outcome Resolution

When a shot doesn't result in a goal, the outcome is determined by two sequential rolls:

```python
if roll(0.4):
    outcome = "save"
elif roll(0.5):
    outcome = "block"
else:
    outcome = "miss"
```

This produces the following distribution:
- Save: 40%
- Block: 30% (50% of the remaining 60%)
- Miss: 30% (50% of the remaining 60%)

These are fixed probabilities — they don't depend on player stats. The shot quality already encodes how dangerous the chance was. The outcome split just determines what kind of non-goal it was, which affects the narrative.

---

## Action Selection Weights

Action selection uses `random.choices(actions, weights=weights)`. The weights are sums of the ball carrier's relevant stats for each action.

**Example — Mbappé in the final third:**

| Action | Stats | Mbappé values | Weight |
|--------|-------|---------------|--------|
| finesse_shot | finishing + curve | 94 + 82 | 176 |
| power_shot | shot_power + long_shots | 91 + 76 | 167 |
| cutback | vision + short_passing | 83 + 80 | 163 |
| dribble_into_box | dribbling + agility | 92 + 92 | 184 |
| header | heading_accuracy + jumping | 70 + 68 | 138 |

Total weight: 828. Probabilities:
- finesse_shot: 176/828 = 21.3%
- power_shot: 167/828 = 20.2%
- cutback: 163/828 = 19.7%
- dribble_into_box: 184/828 = 22.2%
- header: 138/828 = 16.7%

Mbappé attempts dribbles into the box most often, headers least often — which matches his real playing style.

**Switch play weight reduction:** The raw stat-based weight for switch play is multiplied by `0.4` after calculation. Without this, players with high `long_passing` and `vision` (e.g. De Bruyne) would attempt switch play on nearly every midfield phase, sending the ball back to buildup repeatedly. The 0.4 multiplier keeps switch play as a meaningful option without letting it dominate.

**Assisted flag forces a shot:** When `game_state.assisted` is `True` and the zone is `final_third`, the normal weighted action selection is bypassed entirely. Only `finesse_shot`, `power_shot`, and `header` are eligible, weighted by the ball carrier's relevant stats. This guarantees that a cutback or dribble-into-box always produces a shot on the very next phase — matching real football where a pulled-back ball is always met with a shot attempt.

**Example — Mbappé in midfield with switch play weight reduction:**

| Action | Raw weight | Multiplier | Final weight |
|--------|-----------|------------|-------------|
| through_ball | vision(83) + short_passing(80) = 163 | 1.0 | 163 |
| skill_move | skill_moves(100) + agility(92) = 192 | 1.0 | 192 |
| physical_duel | strength(76) + aggression(62) = 138 | 1.0 | 138 |
| switch_play | long_passing(77) + vision(83) = 160 | 0.4 | 64 |

Total: 557. Switch play probability: 64/557 = 11.5% (down from 28.7% without the multiplier).
