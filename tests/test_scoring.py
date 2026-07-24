"""Table-driven tests for KCD2 dice scoring."""

import pytest

from kcd2_dice.scoring import has_any_score, score_selection


@pytest.mark.parametrize(
    "dice, expected",
    [
        ([1], 100),
        ([5], 50),
        ([1, 5], 150),
        ([1, 1, 1], 1000),
        ([2, 2, 2], 200),
        ([3, 3, 3], 300),
        ([4, 4, 4], 400),
        ([5, 5, 5], 500),
        ([6, 6, 6], 600),
        ([1, 1, 1, 1], 2000),
        ([2, 2, 2, 2], 400),
        ([5, 5, 5, 5], 1000),
        ([1, 1, 1, 1, 1], 4000),
        ([6, 6, 6, 6, 6, 6], 4800),
        ([1, 1, 1, 1, 1, 1], 8000),
        ([1, 2, 3, 4, 5], 500),
        ([2, 3, 4, 5, 6], 750),
        ([1, 2, 3, 4, 5, 6], 1500),
        # KCD2 multi-combo: keep 1 + three 4s + 5 (leave the non-scoring 2 out)
        ([1, 4, 4, 4, 5], 550),
        ([1, 2, 3, 4, 5, 5], 550),
        ([2, 3, 4, 5, 5, 6], 800),
        ([3, 3, 3, 1, 5], 450),
    ],
)
def test_score_selection_valid(dice, expected):
    assert score_selection(dice) == expected


def test_nonscoring_die_cannot_be_included():
    assert score_selection([1, 2, 4, 4, 4, 5]) is None
    assert has_any_score([1, 2, 4, 4, 4, 5]) is True


@pytest.mark.parametrize(
    "dice",
    [
        [],
        [2],
        [2, 2],
        [2, 3, 4],
        [2, 2, 3, 3],
        [2, 2, 3, 3, 4, 4],
        [1, 2, 3, 4],
        [2, 2, 2, 3],
        [1, 1, 2, 2, 3, 3],
    ],
)
def test_score_selection_invalid(dice):
    assert score_selection(dice) is None


@pytest.mark.parametrize(
    "dice, expected",
    [
        ([2, 3, 4, 6, 6, 6], True),
        ([2, 3, 4, 6, 6, 2], False),
        ([1, 2, 3, 4, 6, 6], True),
        ([2, 3, 4, 6, 2, 3], False),
        ([1, 2, 3, 4, 5, 6], True),
    ],
)
def test_has_any_score(dice, expected):
    assert has_any_score(dice) is expected
