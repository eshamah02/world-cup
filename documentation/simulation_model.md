# Simulation Model — How the Match Engine Works

## Type of Simulation

This is a **probabilistic event-based simulation**, not machine learning and not a physics engine. It works by:

1. Dividing the match into discrete phases (moments of play)
2. Each phase: determining who has the ball, what they attempt, and whether it succeeds
3. Using player stats as weights and probabilities throughout
4. Accumulating events until the match ends

The core insight is that football is not random — better players succeed more often — but it is also not deterministic — even the best players fail sometimes. The simulation captures both truths by converting stats into probabilities and then rolling against those probabilities.

---

## The Zone System

The ball is always in one of four zones. Zone is the most important piece of state in the simulation — it determines what actions are possible and what the stakes of each action are.

### `buildup`
The team is in their own half, in safe possession. No immediate danger, no immediate opportunity. The goal from here is to advance the ball without losing it. Actions available: short pass, long ball, dribble carry.

In real football this is a team playing out from the back, a goalkeeper distribution, or a defender recycling possession. The priority is security — keep the ball and find a way forward.

### `midfield`
The ball is in the contested central area. Both teams are competing for control. This is where the game is won and lost — winning the midfield battle means more time in the final third. Actions available: through ball, skill move, physical duel, switch play.

In real football this is the press, the counter-press, the central midfield battle. A team that dominates midfield creates more chances. A team that loses midfield is constantly defending.

### `final_third`
The attacking team is in a dangerous position near goal. This is where goals come from. Actions available: finesse shot, power shot, header, cutback, dribble into box.

In real football this is the penalty area and the area just outside it. Every action here has a direct path to goal. The defending team is under maximum pressure.

### `set_piece`
Play has stopped. A foul was committed or the ball went out for a corner. The attacking team gets a dead ball delivery. This zone is handled separately from the normal action flow — it resolves immediately and always returns to midfield after.

In real football roughly 30% of goals come from set pieces. They are a distinct tactical situation with completely different skills involved.

---

## Zone Transitions

Zone transitions are the backbone of the simulation. Every action either advances the zone, resets it, or flips possession. This creates the natural ebb and flow of a match.

```
buildup ──(success)──► midfield ──(success)──► final_third ──(shot)──► midfield
   │                       │                        │
(fail)                  (fail)                   (fail)
   │                       │                        │
   ▼                       ▼                        ▼
midfield              midfield                  midfield
(possession           (possession               (possession
 flips)                flips)                    flips)
```

Key rules:
- **Possession flips always reset zone to midfield** — the other team starts from a neutral position, not from where they won the ball
- **Goals reset to midfield with possession to the conceding team** — like a kickoff
- **Set pieces always return to midfield** — regardless of outcome
- **Long ball and through ball skip midfield** — they jump straight to final_third on success, reflecting their high-risk high-reward nature
- **Switch play goes backwards** — success sends the zone back to buildup, because switching the play resets the angle rather than advancing
- **Physical duel success advances zone and emits a carry event** — winning a 50/50 battle moves the ball forward one step. A carry `DribbleAttempt` is emitted immediately after to bridge the zone jump narratively, so the reader sees the duel win followed by the player surging forward before the next action.
- **Skill move success advances one step** — a successful trick moves the ball forward one zone, not straight to the final third

---

## The Phase Loop

A match runs for a randomized number of phases between 24 and 30. Each phase is one tick of the game clock. The randomization means no two matches have exactly the same length, which prevents patterns from feeling mechanical.

Each phase follows this sequence:

```
1. Is zone "set_piece"?
   YES → resolve set piece, return, done
   NO  → continue

2. Pick ball carrier from attacking team (weighted by zone-relevant stats)
3. Pick defender from defending team (weighted by defensive stats)

4. Check for special events
   - Brilliance check on ball carrier (~3-5% for elite players) → instant goal, return
   - Error check on ball carrier (~2-5% for average players) → instant turnover, return

5. Emit bridging pass if ball carrier changed within the same possession
   (suppressed only on cutback_assisted — the cutback text already named the recipient;
    dribble_assisted does NOT suppress since dribble_into_box names no recipient)
6. Select action (weighted by ball carrier's stats for current zone)
7. Resolve action (compute composites, roll probability, update game state)
8. Update momentum and last_ball_carrier
9. Increment phase number
10. Return events list
```

The special event check happens before normal action selection. If it fires, the phase ends immediately — no action is selected, no normal resolution happens. This is intentional: special moments bypass the normal flow, which is exactly what makes them feel special.

The phase number is stamped on the event *before* incrementing — the same pattern as normal actions. This ensures phase numbers are sequential with no gaps or duplicates in the response.

A single phase can return multiple events — a bridging pass plus the main action, or a physical duel plus a carry event. All sub-events within a phase share the same phase number.

---

## Narrative Continuity

The simulation tracks `game_state.last_ball_carrier` — the name of the player who ended the previous phase with the ball. This is used to emit bridging events that make the play-by-play read as a continuous flow rather than disconnected snapshots.

**Bridging pass:** If the ball carrier changes between phases within the same possession, a `PassAttempt(pass_type="short", success=True)` is prepended to the phase's events before the main action. This produces a line like *"De Bruyne plays it simple to Lewandowski"* before *"Lewandowski fires it into the net!"* — making the transition feel natural.

Bridging passes are suppressed only when `cutback_assisted=True` — the cutback text already named the recipient. `dribble_assisted` does not suppress the bridging pass because `dribble_into_box` names no recipient, so the bridging pass is still needed to show who receives the ball.

**Through ball receiver lock:** When a through ball succeeds and names a specific receiver, `game_state.through_ball_receiver` is set to that player's name. On the very next phase, `resolve_phase` looks up that player in the attacking team and locks them in as ball carrier, bypassing `pick_ball_carrier`. This ensures the player named as "clean through" is actually the one who acts next. The field is cleared after use and on any possession flip, set piece, or special event.

**Named targets on all passes:** Every pass action — `short_pass`, `long_ball`, `through_ball`, `switch_play`, and `cutback` — picks a real receiver name from the rest of the team using `pick_ball_carrier` weighted by zone-relevant stats. The target is used purely for narrative on all passes except `through_ball`, where the receiver is also locked in as ball carrier on the next phase.

**Carry event after duel win:** When a physical duel is won, the zone advances one step. To bridge this zone jump narratively, a `DribbleAttempt` carry event is emitted immediately after the duel event, using an empty defender string to signal it is a carry rather than a contested dribble. This produces a line like *"Fernandes surges forward into the final third"* between the duel win and the next action. `last_ball_carrier` is reset to `""` after a duel win so no additional bridging pass fires on top of the carry.

**Possession-flip narrative:** When possession changes, the reader needs to know who won the ball and which team now has it — not just that the previous action failed.

- **Pass and dribble turnovers:** The `turnover_player` field on `PassAttempt` and `DribbleAttempt` names the defender who won the ball. When this field is set, `narrate_event` selects a `_fail_turnover` template variant that names both the interceptor and the new possessing team — e.g. *"De Bruyne reads it perfectly — team B win possession."* When `turnover_player` is empty (bridging passes, carry events), the plain `_fail` template is used instead.

- **Duel losses:** After a `PhysicalDuel` where the defender wins, `resolve_phase` appends a `PossessionChange` event naming the winner and the new possessing team. This produces a follow-up line like *"Van Dijk wins it back for team A"* immediately after the duel narrative, closing the gap between "who won the duel" and "who now has the ball."

**Resets:** `last_ball_carrier` is reset to `""` on any possession flip, set piece, special event, or duel win — any situation where the narrative context changes enough that a bridging pass would be misleading.

---

## Score Stamping

Every event carries its own `score` snapshot at the time it was created, reflecting the score *after* any state changes from that event. This means:
- A goal event's score shows the new score including that goal
- A bridging pass before a goal shows the pre-goal score
- All sub-events within a phase (e.g. duel + carry) carry the same score snapshot taken after the duel resolves

The engine reads `event.score` directly rather than capturing a single score per phase, which previously caused bridging passes to show the post-goal score even though they occurred before the goal.

When possession stays with the same team, their momentum counter increments. When possession flips, the losing team's counter resets to zero and the gaining team's counter increments.

## Momentum

Momentum tracks how many consecutive phases each team has had possession. It is stored as `[team_a_consecutive, team_b_consecutive]`.

The simulation is context-aware. It knows the score and how far through the match we are.

**Late game, losing team:** If a team is losing and more than 75% of phases have elapsed, their shot-related action weights are multiplied by 1.5. This means they attempt more shots, more headers, more power shots — the desperate push for an equalizer. In real football this is the team throwing everyone forward in the final minutes.

This modifier only applies in the final third zone, where shot actions are available. It does not affect buildup or midfield behavior.

---

## Set Piece Type

The type of set piece (free kick or corner) is determined at the point the foul occurs, not randomly at resolution time. `game_state.set_piece_type` is set to `"free_kick"` whenever a dribble foul is committed. This means a foul in open play always produces a free kick — corners would need to be triggered separately (e.g. from a shot going wide).

This prevents the narrative mismatch of a foul on a player producing a corner instead of a free kick.

---

## The Assisted Flags

Two boolean flags track whether the current attacking move has created a premium shooting opportunity:

- `cutback_assisted` — set to `True` by a successful cutback. The cutback text names the recipient, so the bridging pass is suppressed on the next phase.
- `dribble_assisted` — set to `True` by a successful `dribble_into_box`. The dribble text names no recipient, so the bridging pass is NOT suppressed — it still fires to show who receives.

When either flag is `True` and the zone is `final_third`, `select_action` forces a shot on the next phase. The shot quality gets a flat `+0.15` bonus before clamping. Both flags reset to `False` after any shot resolves, possession flip, set piece, or special event.

---

## Special Events

Every phase has a small probability of a special event firing before normal resolution. There are two types:

**Brilliance** — a moment of individual genius. The ball carrier does something extraordinary that bypasses the normal action flow entirely and scores. Probability formula: `(overall_rating + skill_moves + composure) / 9000`. For an elite player (91 overall, 100 skill_moves, 88 composure) this is approximately 3.1% per phase. Over a 27-phase match, that's roughly a 57% chance of at least one brilliance moment — which feels right for a match featuring world-class players.

**Error** — an unforced mistake. The ball carrier loses possession without any defensive action. Probability formula: `(200 - composure - ball_control) / 3000`. For an average player (65 composure, 70 ball_control) this is approximately 2.2% per phase. Elite players with high composure and ball control have very low error rates.

Special events are checked in order: brilliance first, then error. If brilliance fires, error is never checked. Both return early from the phase — no normal action resolution happens.

---

## Set Piece Resolution

Set pieces are resolved by `resolve_set_piece` and follow a different logic from normal phases:

1. The player with the highest `fk_accuracy` on the attacking team takes the set piece
2. A coin flip (50/50) decides direct free kick vs corner/crossed delivery
3. **Direct free kick**: `shot_quality("free_kick", taker)` is used as the goal probability directly. Outcome is goal or save.
4. **Corner**: The taker's `crossing + curve` is compared against the best aerial defender's `jumping + heading_accuracy`. If the delivery beats the defender, the best aerial attacker (by `heading_accuracy + jumping`) gets a header attempt using `shot_quality("header", attacker)`. If the delivery is cleared, outcome is "cleared".

After any outcome, zone resets to midfield and possession flips.

---

## Score and Winner

Goals are tracked in `game_state.score` as `[team_a_goals, team_b_goals]`. The score is updated in place whenever a goal is scored — inside `resolve_action` for normal shots and inside `resolve_set_piece` for set pieces.

After all phases complete, the winner is determined by comparing the two scores. Equal scores produce a draw (`winner = None`).

---

## MVP Selection

The MVP is the player most involved in goals. The engine tracks a `goal_involvements` dictionary during the match loop, incrementing a player's count when:
- They score a goal (`ShotAttempt` with `outcome == "goal"`, shooter gets +1)
- They assist a goal (`ShotAttempt` with a non-None assister, assister gets +1)
- They score via a special event (`SpecialEvent` with `resulted_in_goal == True`, player gets +1)

The player with the highest count is the MVP. If no goals were scored, the fallback MVP is the highest-rated player from the winning team — or from either team on a draw. This ensures the MVP always comes from the winning side when there is one.
