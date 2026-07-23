# World Cup 3v3 Match Simulator — Overview

## What Is This?

This is a **3v3 football match simulator**. You pick three real players from a database of thousands, your opponent picks three, and the system simulates a short match between them — producing a play-by-play narrative, a final score, and a winner.

The simulation is not a video game. There are no graphics, no controls, no real-time input. It is a **probabilistic event engine** — a system that uses each player's real stats to determine the likelihood of every moment in the match, then rolls weighted dice to decide what actually happens.

---

## What Makes It Interesting

Every player in the database has 40+ individual stats — finishing, dribbling, vision, strength, composure, and more. These stats are not decorative. They are the direct inputs to every decision the simulation makes.

When Mbappé (97 acceleration, 92 dribbling) tries to beat a defender with 60 sprint speed, the simulation knows that's a very different contest than a midfielder with 72 dribbling trying the same thing. The outcome reflects the specific matchup, not a generic coin flip.

This means:
- The same six players will produce different results every time you simulate
- But over many simulations, the better team wins more often
- Individual star players genuinely change outcomes — a player with 95 finishing converts chances that a 70-finishing player misses
- Tactical mismatches matter — a team with elite dribblers will dominate a team with poor tackling

---

## How a Match Feels

A match runs through 24–30 **phases**. Each phase is one moment of play — a pass, a dribble, a shot, a tackle. The phases chain together to tell a story:

```
Phase 1:  Mbappé plays it short to a teammate — possession maintained
Phase 2:  Through ball attempt — intercepted, possession changes
Phase 3:  De Bruyne carries the ball forward into midfield
Phase 4:  Skill move — De Bruyne beats his man, drives into the final third
Phase 5:  Power shot — GOAL! De Bruyne scores
Phase 6:  Kickoff, Mbappé's team now attacking...
...
Phase 27: Final whistle. Team B 2 - Team A 1
```

Each phase produces a line of commentary. The full match produces a readable play-by-play that feels like a real game.

---

## The 3v3 Format

3v3 is intentional. In a full 11v11 match, individual players get lost in the crowd. In 3v3:
- Every player is involved in almost every phase
- Individual quality is amplified — one elite player can carry a team
- Mismatches are immediately visible
- Matches are short enough to simulate in milliseconds but long enough to feel complete

---

## What the System Tracks

During a match the simulation tracks:
- **Zone** — where the ball is (buildup, midfield, final third, set piece)
- **Possession** — which team has the ball
- **Score** — goals scored by each team
- **Momentum** — how many consecutive phases a team has controlled
- **Assisted flag** — whether a cutback or dribble into the box just created a better shooting opportunity
- **Phase number** — how far through the match we are

At the end it produces:
- Full play-by-play event list with commentary text
- Final score
- Winner (or draw)
- MVP — the player most involved in goals and assists

---

## What the System Does Not Do

- It does not simulate goalkeeper saves as a separate player — defensive stats on outfield players absorb this role in 3v3
- It does not track stamina degradation over the match
- It does not simulate injuries
- It does not have formations — zone-based positioning replaces tactical shape
- It is not real-time — the entire match resolves instantly when requested
