# Action Reference — Every Action Explained

Each phase of the match, the ball carrier attempts one action. The action is chosen by weighted random selection — the ball carrier's stats determine how likely they are to attempt each action. This means a player with 95 dribbling will attempt dribbles far more often than a player with 60 dribbling, but the same player might occasionally play a short pass instead.

This document covers every action: what it means in football, why a player would choose it, what stats determine whether they attempt it, what stats determine whether it succeeds, and what happens to the game state.

---

## Buildup Zone Actions

These actions are available when the ball is in the team's own half. The priority is safe progression — keep the ball and move it forward without giving it away cheaply.

---

### `short_pass`

**In football:** The simplest, safest option. A player passes to a nearby teammate to maintain possession and move the ball forward one step. No risk, no reward — just keeping the ball.

**Why a player chooses it:** Players with high `short_passing` naturally gravitate toward this. It's the default option for technically gifted players who value possession. A player with 90 short passing will attempt this frequently; a player with 55 short passing will look for other options.

**Action weight:** `short_passing`

**Attacker composite:** `short_passing, ball_control, composure`
- `short_passing` — technical accuracy of the pass
- `ball_control` — ability to set the ball up cleanly before passing
- `composure` — not rushing the pass under pressure

**Defender composite:** `interceptions, reactions, defensive_awareness`
- `interceptions` — reading the pass and getting in the way
- `reactions` — speed of response to the pass
- `defensive_awareness` — positioning to cut off passing lanes

**Success:** Zone advances one step (buildup → midfield, midfield → final_third)

**Failure:** Possession flips, zone resets to midfield. `turnover_player` on the returned `PassAttempt` is set to the defender's name, enabling the narrative to name who intercepted it and which team now has possession.

**Returns:** `PassAttempt(pass_type="short")`

---

### `long_ball`

**In football:** A player bypasses midfield entirely with a direct ball over the top or into space behind the defensive line. High risk — if it doesn't find a teammate, possession is lost. High reward — if it works, the team is immediately in a dangerous position.

**Why a player chooses it:** Players with high `long_passing` will attempt this more. It's the option for teams that want to play direct rather than build through midfield. A center-back with 85 long passing might launch it forward; a midfielder with 90 long passing might play a diagonal switch.

**Action weight:** `long_passing`

**Attacker composite:** `long_passing, vision`
- `long_passing` — technical ability to hit the target from distance
- `vision` — seeing the run and picking the right moment

**Defender composite:** `reactions, sprint_speed, jumping`
- `reactions` — reading the ball early to intercept
- `sprint_speed` — tracking the runner to win the race
- `jumping` — winning the aerial ball if it's in the air

**Success:** Zone jumps straight to `final_third` — skips midfield entirely

**Failure:** Possession flips, zone resets to midfield. `turnover_player` on the returned `PassAttempt` is set to the defender's name.

**Returns:** `PassAttempt(pass_type="long")`

---

### `dribble_carry`

**In football:** A player runs with the ball, using their body and pace to advance rather than passing. Not a trick or skill move — just carrying the ball forward under pressure. Common when a player has space to run into or when passing options are limited.

**Why a player chooses it:** Players with high `dribbling` will carry the ball more. It's the option when a player sees space ahead or when the passing options are poor. A winger with 88 dribbling will carry the ball forward regularly; a center-back with 45 dribbling will rarely attempt it.

**Action weight:** `dribbling`

**Attacker composite:** `dribbling, agility, ball_control, balance`
- `dribbling` — technical ability to keep the ball while moving
- `agility` — changing direction to avoid challenges
- `ball_control` — first touch and close control
- `balance` — staying on feet when challenged

**Defender composite:** `reactions, aggression, standing_tackle`
- `reactions` — getting into position quickly
- `aggression` — willingness to challenge
- `standing_tackle` — winning the ball cleanly

**Success:** Zone advances one step

**Failure:** Foul check — `roll(defender.aggression / 200)`
- If foul: zone becomes `set_piece`, possession stays (the fouled team keeps it)
- If no foul: possession flips, zone resets to midfield. `turnover_player` on the returned `DribbleAttempt` is set to the defender's name.

The foul check reflects a real football truth: defenders who can't win the ball fairly often resort to fouling. A defender with 90 aggression has a 45% chance of fouling when they fail to win the ball cleanly. A defender with 40 aggression has only a 20% chance.

**Returns:** `DribbleAttempt(success=..., foul=..., turnover_player=...)`

---

## Midfield Zone Actions

These actions are available when the ball is in the contested central area. The stakes are higher — success here means a dangerous attacking position, failure means the other team counter-attacks.

---

### `through_ball`

**In football:** A precisely weighted pass played into the space behind the defensive line for a teammate to run onto. The most dangerous pass in football — if it works, the receiver is clean through on goal. If it doesn't, the defense wins it and counter-attacks.

**Why a player chooses it:** Players with high `vision` and `short_passing` attempt this more. It's the option for creative midfielders who can see and execute the killer pass. Mbappé, De Bruyne, Bellingham — players who can split defenses with one pass.

**Action weight:** `vision + short_passing`

**Attacker composite:** `vision, short_passing, composure`
- `vision` — seeing the run before it happens
- `short_passing` — weighting the pass perfectly into space
- `composure` — executing under pressure without rushing

**Defender composite:** `defensive_awareness, reactions, sprint_speed`
- `defensive_awareness` — reading the pass before it's played
- `reactions` — getting across to intercept
- `sprint_speed` — winning the race to the ball

**Success:** Zone to `final_third`. A different teammate is selected as the receiver (the passer cannot receive their own through ball). The receiver is chosen by `pick_ball_carrier` from the remaining team members, weighted by `finishing, dribbling, attack_position` — the most dangerous attacker makes the run.

**Failure:** Possession flips, zone resets to midfield. `turnover_player` on the returned `PassAttempt` is set to the defender's name.

**Returns:** `PassAttempt(pass_type="through_ball", target=receiver.name)`

---

### `skill_move`

**In football:** A specific technical trick — a stepover, a roulette, a nutmeg, a rainbow flick — designed to beat a defender with technique rather than pace. More ambitious than a dribble carry. The intent is to get into the final third in one move.

**Why a player chooses it:** Players with high `skill_moves` and `agility` attempt this more. It's the option for technically gifted players who can execute tricks under pressure. A 5-star skill player will attempt skill moves frequently; a 2-star player almost never will. Note: `skill_moves` in the database is a 1-5 star rating that gets normalized to a 0-100 scale (multiplied by 20) during data loading, so it integrates naturally with other stats.

**Action weight:** `skill_moves + agility`

**Attacker composite:** `dribbling, agility, ball_control, balance`

**Defender composite:** `standing_tackle, aggression, reactions`

**Success:** Zone advances one step — a successful skill move beats the immediate defender and moves the ball forward one zone (buildup → midfield, midfield → final_third). It does not teleport to the final third from buildup.

**Failure:** Same foul check as dribble_carry (`roll(defender.aggression / 200)`). On a clean tackle (no foul), `turnover_player` is set to the defender's name.

**Returns:** `DribbleAttempt(success=..., foul=..., turnover_player=...)`

---

### `physical_duel`

**In football:** A 50/50 contest where two players compete for the same ball through raw physicality — shoulder charges, holding off, winning aerial balls. Neither player has clean possession. This is the press, the counter-press, the midfield battle for a loose ball.

**Why a player chooses it:** Players with high `strength` and `aggression` attempt this more. It's the option for physically dominant players who can bully opponents off the ball. A powerful defensive midfielder will win these contests regularly; a slight technical player will avoid them.

**Action weight:** `strength + aggression`

**Attacker composite:** `strength, aggression, stamina`
- `strength` — raw physical power
- `aggression` — willingness to go into challenges
- `stamina` — maintaining intensity through the contest

**Defender composite:** `strength, standing_tackle, aggression`

**Success:** Zone advances one step, possession stays — winning the physical battle moves the ball forward. A duel win in midfield pushes into the final third; a duel win in buildup pushes into midfield.

**Failure:** Possession flips, zone stays midfield (the ball doesn't go anywhere — it just changes feet in the same area). A `PossessionChange` event is appended after the `PhysicalDuel` event, naming the winning defender and the team that now has possession — e.g. *"Van Dijk wins it back for team A."*

**Returns:** `PhysicalDuel(winner=...)` on failure; `[PhysicalDuel(winner=...), DribbleAttempt(carry)]` on success

---

### `switch_play`

**In football:** A long diagonal pass to the opposite flank to change the angle of attack. The play is congested on one side, so the ball is moved to the other side where there's more space. This doesn't advance the team — it resets them to a better position.

**Why a player chooses it:** Players with high `long_passing` and `vision` attempt this more. It's the option for players who can see the whole pitch and execute the diagonal ball. A deep-lying playmaker or a center-back with good distribution will switch play regularly.

**Action weight:** `long_passing + vision`

**Attacker composite:** `long_passing, vision`

**Defender composite:** `sprint_speed, acceleration, reactions`
- `sprint_speed` and `acceleration` — tracking across the pitch to cover the switch
- `reactions` — reading the ball early

**Success:** Zone goes back to `buildup` — the team resets to a better position but doesn't advance. This is correct: switching play creates space, it doesn't create a chance directly.

**Failure:** Possession flips, zone resets to midfield. `turnover_player` on the returned `PassAttempt` is set to the defender's name.

**Returns:** `PassAttempt(pass_type="switch")`

---

## Final Third Zone Actions

These actions are available when the ball is in a dangerous attacking position near goal. Every action here has a direct path to a shot or a goal.

---

### `finesse_shot`

**In football:** A placed shot using the inside of the foot, curled into the corner. Prioritizes accuracy over power. The classic "near post curl" or "far post placement." Lower power than a power shot but more precise.

**Why a player chooses it:** Players with high `finishing` and `curve` attempt this more. It's the option for technically gifted forwards who can place the ball precisely. Mbappé's inside-foot finish, Messi's curled efforts — this is that shot.

**Action weight:** `finishing + curve`

**Shot quality:** Uses `shot_quality("cutback", ball_carrier)` — base quality 0.40, modified by `finishing / 80`. A player with 80 finishing gets exactly the base quality. A player with 94 finishing (Mbappé) gets `0.40 * (94/80) = 0.47`. With an assisted bonus (+0.15), this becomes 0.62 — a very dangerous chance.

**Assisted bonus:** If `game_state.cutback_assisted` or `game_state.dribble_assisted` is `True`, quality gets +0.15 before clamping to 0.85

**Outcome resolution:**
- `roll(quality)` → True = goal
- If not goal: `roll(0.4)` → save, else `roll(0.5)` → block, else miss

**Returns:** `ShotAttempt(shot_type="finesse_shot", quality=..., outcome=...)`

---

### `power_shot`

**In football:** A shot hit with maximum power, relying on pace to beat the goalkeeper rather than placement. The long-range screamer, the driven effort from outside the box. Lower accuracy than a finesse shot but can beat a keeper through sheer speed.

**Why a player chooses it:** Players with high `shot_power` and `long_shots` attempt this more. It's the option for players who can generate pace on the ball. A midfielder with 88 shot_power might try one from distance; a striker with 91 shot_power will blast it when the opportunity arises.

**Action weight:** `shot_power + long_shots`

**Shot quality:** Uses `shot_quality("long_shot", ball_carrier)` — base quality 0.08, modified by `finishing / 80`. Much lower base than finesse shot, reflecting the lower conversion rate of power shots. With an assisted bonus, this becomes 0.23 — still a meaningful chance.

**Returns:** `ShotAttempt(shot_type="power_shot", quality=..., outcome=...)`

---

### `header`

**In football:** Directing the ball into the goal with the head, typically from a cross or a set piece delivery. Requires good timing, jumping ability, and heading technique. Headers are harder to convert than ground shots but are the natural outcome of aerial situations.

**Why a player chooses it:** Players with high `heading_accuracy` and `jumping` attempt this more. It's the option when the ball is in the air — from a long ball, a cross, or a set piece. A tall striker with 85 heading_accuracy will be a constant aerial threat.

**Action weight:** `heading_accuracy + jumping`

**Shot quality:** Uses `shot_quality("header", ball_carrier)` — base quality 0.25, modified by `finishing / 80`. Moderate base quality — headers are dangerous but not as reliable as ground shots.

**Returns:** `ShotAttempt(shot_type="header", quality=..., outcome=...)`

---

### `cutback`

**In football:** A player near the byline or the edge of the box pulls the ball back across the face of goal for a teammate arriving late. The goalkeeper is set for a cross, the defenders are tracking the ball carrier, and the arriving player has a clean look at goal from close range. One of the highest quality chances in football.

**Why a player chooses it:** Players with high `vision` and `short_passing` attempt this more. It's the option for wide players or players who have beaten their man and are in a position to create rather than shoot themselves.

**Action weight:** `vision + short_passing`

**Attacker composite:** `short_passing, vision, composure`

**Defender composite:** `interceptions, reactions`

**Success:** Zone stays `final_third`, `game_state.cutback_assisted = True`. The cutback itself doesn't score — it sets up the next action. The next shot taken will receive a +0.15 quality bonus.

**Failure:** Possession flips, zone resets to midfield. `turnover_player` on the returned `PassAttempt` is set to the defender's name.

**Returns:** `PassAttempt(pass_type="cutback")`

---

### `dribble_into_box`

**In football:** A player takes on their marker inside or just outside the penalty area, trying to get into a better shooting position. More dangerous than a dribble carry because the stakes are higher — success creates a premium chance, failure in the box often results in a foul (penalty in real football, set piece here).

**Why a player chooses it:** Players with high `dribbling` and `agility` attempt this more. It's the option for attackers who can beat their man in tight spaces. A player like Mbappé or Neymar will attempt this regularly in the final third.

**Action weight:** `dribbling + agility`

**Attacker composite:** `dribbling, agility, ball_control, balance`

**Defender composite:** `standing_tackle, aggression, reactions`

**Success:** Zone stays `final_third`, `game_state.dribble_assisted = True` — the player is now in a better position inside the box, creating a premium shooting opportunity

**Failure:** Foul check — `roll(defender.aggression / 200)`
- If foul: zone becomes `set_piece` (a foul inside the box — penalty/free kick)
- If no foul: possession flips, zone resets to midfield. `turnover_player` on the returned `DribbleAttempt` is set to the defender's name.

**Returns:** `DribbleAttempt(success=..., foul=..., turnover_player=...)`

---

## Set Piece Resolution

Set pieces are not selected as actions — they are triggered automatically when `game_state.zone == "set_piece"`. This happens after a foul from a dribble attempt.

The set piece type is determined by how the set piece was won — it is stored in `game_state.set_piece_type` and set at the point of the foul, not decided randomly at resolution time.

- Fouls from `dribble_carry`, `skill_move`, or `dribble_into_box` always produce a **free kick** (`set_piece_type = "free_kick"`)
- Corners are not currently triggered by open play — they would need to be set explicitly (e.g. when a shot goes wide)

### Free Kick
The player with the highest `fk_accuracy` takes it. Quality is `shot_quality("free_kick", taker)` — base 0.10, modified by `finishing / 80`. Low base quality reflects the difficulty of scoring directly from a free kick. Outcome: goal or save.

### Corner
The taker's `crossing + curve` is compared against the best aerial defender's `jumping + heading_accuracy`. If the delivery beats the defender, the best aerial attacker (by `heading_accuracy + jumping`, excluding the taker) gets a header attempt. Outcome: goal, save, or cleared.

---

## Action Selection Summary

| Zone | Action | Key Stats for Selection |
|------|--------|------------------------|
| buildup | short_pass | short_passing |
| buildup | long_ball | long_passing |
| buildup | dribble_carry | dribbling |
| midfield | through_ball | vision + short_passing |
| midfield | skill_move | skill_moves + agility |
| midfield | physical_duel | strength + aggression |
| midfield | switch_play | long_passing + vision |
| final_third | finesse_shot | finishing + curve |
| final_third | power_shot | shot_power + long_shots |
| final_third | cutback | vision + short_passing |
| final_third | dribble_into_box | dribbling + agility |
| final_third | header | heading_accuracy + jumping |

## Zone Transition Summary

| Action | Success → zone | Failure → zone |
|--------|---------------|----------------|
| short_pass | +1 step | midfield (flip) |
| long_ball | final_third | midfield (flip) |
| dribble_carry | +1 step | midfield or set_piece |
| through_ball | final_third | midfield (flip) |
| skill_move | +1 step | midfield or set_piece |
| physical_duel | +1 step | midfield (flip) |
| switch_play | buildup | midfield (flip) |
| cutback | final_third (assisted) | midfield (flip) |
| dribble_into_box | final_third (assisted) | midfield or set_piece |
| finesse_shot | midfield (flip) | midfield (flip) |
| power_shot | midfield (flip) | midfield (flip) |
| header | midfield (flip) | midfield (flip) |
