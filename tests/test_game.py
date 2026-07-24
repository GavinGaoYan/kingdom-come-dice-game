"""Tests for the KCD2 match state machine."""

from kcd2_dice.game import (
    Phase,
    Player,
    new_match,
    roll,
    score_and_continue,
    score_and_pass,
    set_selection,
    toggle_die,
)
from tests.helpers import ScriptedRandom


def test_bust_clears_turn_and_switches():
    state = new_match(target=3000)
    # No scorers: 2,3,4,6,2,3
    state = roll(state, ScriptedRandom([2, 3, 4, 6, 2, 3]))
    assert state.turn_score == 0
    assert state.current == Player.AI
    assert state.phase == Phase.NEED_ROLL


def test_bank_adds_score_and_can_win():
    state = new_match(target=100)
    state = roll(state, ScriptedRandom([1, 2, 3, 4, 6, 6]))
    state = toggle_die(state, 0)  # select the 1
    assert state.selection_score == 100
    state = score_and_pass(state)
    assert state.scores[Player.HUMAN] == 100
    assert state.winner == Player.HUMAN
    assert state.phase == Phase.GAME_OVER


def test_hot_dice_unlocks_all_six():
    state = new_match()
    # Full straight → select all → continue → hot dice reroll all six
    state = roll(state, ScriptedRandom([1, 2, 3, 4, 5, 6]))
    for i in range(6):
        state = toggle_die(state, i)
    assert state.selection_score == 1500
    # Next roll faces for all six after hot dice
    state = score_and_continue(state, ScriptedRandom([1, 5, 2, 3, 4, 6]))
    assert state.turn_score == 1500
    assert state.held == (False,) * 6
    assert state.phase == Phase.SELECTING
    assert state.dice == (1, 5, 2, 3, 4, 6)


def test_continue_holds_selected_and_rerolls_rest():
    state = new_match()
    state = roll(state, ScriptedRandom([1, 2, 2, 3, 4, 6]))
    state = set_selection(state, [0])  # keep the 1
    # Reroll the five non-held dice
    state = score_and_continue(state, ScriptedRandom([5, 5, 2, 3, 4]))
    assert state.turn_score == 100
    assert state.held[0] is True
    assert state.dice[0] == 1
    assert state.dice[1:] == (5, 5, 2, 3, 4)
