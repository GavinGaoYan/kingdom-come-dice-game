# KCD2 Dice Game — Design Spec

Date: 2026-07-24  
Branch: `cursor/kcd2-dice-rebuild-6c73`

## Goal

Rebuild the Kingdom Come: Deliverance 2 dice minigame from scratch as a local Python desktop app. Do **not** reuse logic, structure, or AI from `UI_12_DICE.py`.

## Scope (v1)

- 1 human vs 1 AI opponent
- Standard six-sided dice only (no loaded dice, Devil’s Head, badges)
- Accurate KCD2 scoring + turn flow
- Tkinter UI with rules panel
- Pure-Python rules engine with unit tests
- Configurable win target (default **3000**)

Out of scope: multiplayer, wager/economy, special dice, badges, PyInstaller packaging polish.

## Rules (KCD2)

### Turn loop

1. Start turn with 6 active dice; roll them.
2. Player must select a non-empty subset that is fully scoring.
3. Then either **Score & continue** (bank selection into turn total, reroll leftover dice) or **Score & pass** (add turn total to match score, end turn).
4. If a roll has no scoring combination → **bust**: turn total = 0, end turn.
5. **Hot dice**: if the selection uses every remaining die, unlock all 6 and continue the turn with the turn total still at risk.
6. First player to reach/exceed the target wins after banking.

### Scoring table

| Combination | Score |
| --- | --- |
| Single 1 | 100 |
| Single 5 | 50 |
| Three 1s | 1000 |
| Three N (2–6) | N × 100 |
| Each extra matching die beyond 3 | doubles the n-of-a-kind score |
| Straight 1–5 | 500 |
| Straight 2–6 | 750 |
| Straight 1–6 | 1500 |

Multiple combinations may score in one selection (e.g. `1,2,4,4,4,5` → 550).  
Every selected die must participate in some scoring combination; leftover non-scorers invalidate the selection.  
**Three pairs are not a KCD2 combo** (explicitly excluded).

### Selection validity

A selection is valid iff there exists a partition of the selected multiset into legal combos (singles 1/5, n-of-a-kind ≥3, or one of the three straights) whose scores sum > 0 and that consumes every die. When multiple partitions exist, use the **maximum** total.

## Architecture

```
kcd2_dice/
  scoring.py   # pure functions: score_selection, has_any_score, combo helpers
  game.py      # immutable-friendly state machine: TurnState / MatchState
  ai.py        # opponent policy over GameState (no UI)
  ui.py        # Tkinter presentation + input only
main.py        # entrypoint
tests/         # pytest for scoring + game transitions
```

### Boundaries

- `scoring.py` has zero UI/game dependencies.
- `game.py` owns turn/match rules; calls scoring only.
- `ai.py` reads state and returns an action (`Select`, `Continue`, `Pass`).
- `ui.py` renders state and dispatches player actions; AI runs via `root.after` timers (main-thread only — no background Tk updates).

## AI (v1)

Heuristic, not copied from the old file:

1. Among valid selections, prefer the one maximizing `score + λ * remaining_dice` (keep dice alive on weak opens).
2. Continue if remaining dice ≥ 4, or turn total is low relative to points needed; pass when remaining ≤ 2 unless behind and desperate.
3. Always continue on hot dice unless banking already wins.

## UI

- 16:9 window, tavern-green table theme
- Opponent area (top), player area (bottom), rules (right)
- Controls: Roll / Score & Continue / Score & Pass
- Click dice to toggle selection; live selected-score readout
- Chinese labels OK (match existing product language)

## Testing

- Table-driven scoring cases (singles, triples, multipliers, straights, multi-combo, invalid leftovers)
- Game transitions: bust, bank, hot dice, win
- No UI screenshot tests in v1

## Migration

- Remove `UI_12_DICE.py` and `大战盗圣亨利.spec` from this branch (replaced, not refactored).
- Rewrite `README.md` with run/test instructions.
