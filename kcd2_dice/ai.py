"""Heuristic AI opponent for KCD2 dice (independent of the old monolith)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from random import Random
from typing import Optional

from kcd2_dice.game import MatchState, Phase, Player, set_selection
from kcd2_dice.scoring import iter_scoring_index_sets, score_selection


class AiActionKind(str, Enum):
    SELECT_AND_CONTINUE = "select_and_continue"
    SELECT_AND_PASS = "select_and_pass"


@dataclass(frozen=True)
class AiAction:
    kind: AiActionKind
    indices: tuple[int, ...]


def _active_local_map(state: MatchState) -> tuple[list[int], list[int]]:
    """Return (active_values, active_global_indices)."""
    values: list[int] = []
    globals_: list[int] = []
    for i in state.active_indices:
        values.append(state.dice[i])
        globals_.append(i)
    return values, globals_


def choose_selection(state: MatchState) -> tuple[int, ...]:
    """Pick a scoring subset that balances points and remaining dice."""
    values, globals_ = _active_local_map(state)
    if not values:
        return ()

    best: Optional[tuple[int, ...]] = None
    best_key: Optional[tuple[float, int, int]] = None

    for local_idx in iter_scoring_index_sets(values):
        global_idx = tuple(globals_[i] for i in local_idx)
        pts = score_selection([values[i] for i in local_idx]) or 0
        remaining = len(values) - len(local_idx)
        # Prefer keeping dice alive on weak opens; still reward raw points.
        key = (pts + remaining * 35.0, remaining, pts)
        if best_key is None or key > best_key:
            best_key = key
            best = global_idx

    return best or ()


def should_continue(state: MatchState, selection: tuple[int, ...]) -> bool:
    """Decide whether to press luck after applying `selection`."""
    pts = score_selection([state.dice[i] for i in selection]) or 0
    projected_turn = state.turn_score + pts
    remaining_after = len(state.active_indices) - len(selection)
    hot = remaining_after == 0

    my_score = state.scores[state.current]
    opp = Player.AI if state.current == Player.HUMAN else Player.HUMAN
    opp_score = state.scores[opp]
    need = state.target - my_score

    if projected_turn >= need:
        return False  # bank the win
    if hot:
        return True
    if remaining_after >= 4:
        return projected_turn < 800 or (my_score + projected_turn) < opp_score
    if remaining_after >= 3:
        return projected_turn < 400 and my_score + 400 < state.target
    # 1–2 dice left: usually bank
    return projected_turn < 150 and (my_score + projected_turn) + 300 < opp_score


def decide(state: MatchState, rng: Optional[Random] = None) -> Optional[AiAction]:
    """Return the next AI action for a selecting-phase state, or None."""
    del rng  # reserved for future stochastic policies
    if state.phase != Phase.SELECTING or state.current != Player.AI:
        return None

    selection = choose_selection(state)
    if not selection:
        return None

    if should_continue(state, selection):
        return AiAction(AiActionKind.SELECT_AND_CONTINUE, selection)
    return AiAction(AiActionKind.SELECT_AND_PASS, selection)


def apply_choice(state: MatchState, action: AiAction) -> MatchState:
    return set_selection(state, action.indices)
