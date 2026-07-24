"""Tests for the rebuilt AI policy."""

from kcd2_dice.ai import AiActionKind, choose_selection, decide, should_continue
from kcd2_dice.game import MatchState, Phase, Player, new_match, roll
from tests.helpers import ScriptedRandom


def test_choose_selection_skips_nonscorer():
    state = new_match()
    state = roll(state, ScriptedRandom([1, 2, 4, 4, 4, 5]))
    picked = choose_selection(state)
    values = sorted(state.dice[i] for i in picked)
    assert values == [1, 4, 4, 4, 5]


def test_decide_banks_winning_turn():
    state = MatchState(
        target=200,
        scores={Player.HUMAN: 0, Player.AI: 100},
        current=Player.AI,
        turn_score=0,
        dice=(1, 2, 3, 4, 6, 6),
        held=(False,) * 6,
        selected=(False,) * 6,
        phase=Phase.SELECTING,
    )
    action = decide(state)
    assert action is not None
    assert action.kind == AiActionKind.SELECT_AND_PASS
    assert should_continue(state, action.indices) is False
