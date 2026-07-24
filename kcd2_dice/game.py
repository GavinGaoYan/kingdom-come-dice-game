"""Match/turn state machine for the KCD2 dice minigame."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum
from random import Random
from typing import Optional, Sequence

from kcd2_dice.scoring import has_any_score, score_selection


class Player(str, Enum):
    HUMAN = "human"
    AI = "ai"


class Phase(str, Enum):
    NEED_ROLL = "need_roll"
    SELECTING = "selecting"
    GAME_OVER = "game_over"


@dataclass(frozen=True)
class MatchState:
    target: int = 3000
    scores: dict[Player, int] = field(
        default_factory=lambda: {Player.HUMAN: 0, Player.AI: 0}
    )
    current: Player = Player.HUMAN
    turn_score: int = 0
    dice: tuple[int, ...] = (1, 1, 1, 1, 1, 1)
    held: tuple[bool, ...] = (False, False, False, False, False, False)
    selected: tuple[bool, ...] = (False, False, False, False, False, False)
    phase: Phase = Phase.NEED_ROLL
    winner: Optional[Player] = None
    message: str = "点击掷骰子开始回合"

    @property
    def active_indices(self) -> tuple[int, ...]:
        return tuple(i for i, locked in enumerate(self.held) if not locked)

    @property
    def selected_indices(self) -> tuple[int, ...]:
        return tuple(i for i, on in enumerate(self.selected) if on)

    @property
    def selected_values(self) -> tuple[int, ...]:
        return tuple(self.dice[i] for i in self.selected_indices)

    @property
    def selection_score(self) -> Optional[int]:
        if not self.selected_indices:
            return None
        return score_selection(self.selected_values)

    @property
    def selection_is_valid(self) -> bool:
        return self.selection_score is not None


def new_match(target: int = 3000) -> MatchState:
    return MatchState(target=target)


def _clear_selection(state: MatchState) -> MatchState:
    return replace(state, selected=(False,) * 6)


def _set_selected(state: MatchState, indices: Sequence[int]) -> MatchState:
    selected = [False] * 6
    for idx in indices:
        selected[idx] = True
    return replace(state, selected=tuple(selected))


def toggle_die(state: MatchState, index: int) -> MatchState:
    if state.phase != Phase.SELECTING:
        return state
    if index < 0 or index >= 6 or state.held[index]:
        return state
    selected = list(state.selected)
    selected[index] = not selected[index]
    return replace(state, selected=tuple(selected))


def roll(state: MatchState, rng: Random) -> MatchState:
    """Roll all non-held dice. Busts end the turn with turn_score cleared."""
    if state.phase != Phase.NEED_ROLL:
        return state

    dice = list(state.dice)
    for i in state.active_indices:
        dice[i] = rng.randint(1, 6)
    rolled = replace(
        state,
        dice=tuple(dice),
        selected=(False,) * 6,
        phase=Phase.SELECTING,
    )

    active_values = [rolled.dice[i] for i in rolled.active_indices]
    if not has_any_score(active_values):
        return _end_turn_after_bust(rolled)

    return replace(rolled, message="请选择得分骰子")


def _end_turn_after_bust(state: MatchState) -> MatchState:
    nxt = Player.AI if state.current == Player.HUMAN else Player.HUMAN
    return replace(
        state,
        turn_score=0,
        held=(False,) * 6,
        selected=(False,) * 6,
        current=nxt,
        phase=Phase.NEED_ROLL,
        message=f"{'你' if state.current == Player.HUMAN else '对手'}爆点，本轮得分清零",
    )


def _apply_selection(state: MatchState) -> MatchState:
    score = state.selection_score
    if score is None:
        return state

    held = list(state.held)
    for i in state.selected_indices:
        held[i] = True

    turn_score = state.turn_score + score
    # Hot dice: every die contributed this throw → unlock all six.
    if all(held):
        held = [False] * 6

    return replace(
        state,
        turn_score=turn_score,
        held=tuple(held),
        selected=(False,) * 6,
        message=f"本轮累计 {turn_score} 分",
    )


def score_and_continue(state: MatchState, rng: Random) -> MatchState:
    if state.phase != Phase.SELECTING or not state.selection_is_valid:
        return state
    applied = _apply_selection(state)
    return roll(replace(applied, phase=Phase.NEED_ROLL), rng)


def score_and_pass(state: MatchState) -> MatchState:
    if state.phase != Phase.SELECTING or not state.selection_is_valid:
        return state

    applied = _apply_selection(state)
    scores = dict(applied.scores)
    scores[applied.current] = scores[applied.current] + applied.turn_score

    if scores[applied.current] >= applied.target:
        return replace(
            applied,
            scores=scores,
            turn_score=0,
            held=(False,) * 6,
            selected=(False,) * 6,
            phase=Phase.GAME_OVER,
            winner=applied.current,
            message=f"{'你' if applied.current == Player.HUMAN else '对手'}获胜！",
        )

    nxt = Player.AI if applied.current == Player.HUMAN else Player.HUMAN
    return replace(
        applied,
        scores=scores,
        turn_score=0,
        held=(False,) * 6,
        selected=(False,) * 6,
        current=nxt,
        phase=Phase.NEED_ROLL,
        message="回合结束，交换玩家",
    )


def set_selection(state: MatchState, indices: Sequence[int]) -> MatchState:
    """Replace the current selection (used by AI)."""
    if state.phase != Phase.SELECTING:
        return state
    cleaned = []
    for idx in indices:
        if 0 <= idx < 6 and not state.held[idx]:
            cleaned.append(idx)
    return _set_selected(state, cleaned)
