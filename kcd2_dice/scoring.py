"""Pure KCD2 dice scoring helpers.

Scoring follows Kingdom Come: Deliverance 2 Farkle rules:
singles (1/5), n-of-a-kind (n>=3 with doubling extras), and straights.
Three pairs are intentionally not scored.
"""

from __future__ import annotations

from collections import Counter
from functools import lru_cache
from typing import Iterable, Optional, Sequence, Tuple

FaceCounts = Tuple[int, int, int, int, int, int]  # counts for faces 1..6

STRAIGHTS: tuple[tuple[tuple[int, ...], int], ...] = (
    ((1, 2, 3, 4, 5, 6), 1500),
    ((2, 3, 4, 5, 6), 750),
    ((1, 2, 3, 4, 5), 500),
)


def _as_counts(dice: Sequence[int]) -> Counter:
    counts: Counter = Counter()
    for value in dice:
        if value < 1 or value > 6:
            raise ValueError(f"invalid die face: {value}")
        counts[value] += 1
    return counts


def _to_key(counts: Counter) -> FaceCounts:
    return tuple(counts.get(face, 0) for face in range(1, 7))  # type: ignore[return-value]


def _from_key(key: FaceCounts) -> Counter:
    return Counter({face: key[face - 1] for face in range(1, 7) if key[face - 1]})


def n_of_a_kind_score(face: int, count: int) -> int:
    """Score for exactly `count` matching dice of `face` (count >= 3)."""
    if count < 3:
        raise ValueError("n-of-a-kind requires at least 3 dice")
    base = 1000 if face == 1 else face * 100
    return base * (2 ** (count - 3))


@lru_cache(maxsize=None)
def _max_full_score(key: FaceCounts) -> Optional[int]:
    """Maximum score that consumes every die in `key`, or None if impossible."""
    if sum(key) == 0:
        return 0

    counts = _from_key(key)
    best: Optional[int] = None

    def consider(points: int, next_counts: Counter) -> None:
        nonlocal best
        rest = _max_full_score(_to_key(next_counts))
        if rest is None:
            return
        total = points + rest
        if best is None or total > best:
            best = total

    if counts[1] > 0:
        nxt = counts.copy()
        nxt[1] -= 1
        consider(100, nxt)

    if counts[5] > 0:
        nxt = counts.copy()
        nxt[5] -= 1
        consider(50, nxt)

    for face in range(1, 7):
        available = counts[face]
        for n in range(3, available + 1):
            nxt = counts.copy()
            nxt[face] -= n
            consider(n_of_a_kind_score(face, n), nxt)

    for faces, points in STRAIGHTS:
        if all(counts[face] > 0 for face in faces):
            nxt = counts.copy()
            for face in faces:
                nxt[face] -= 1
            consider(points, nxt)

    return best


def score_selection(dice: Sequence[int]) -> Optional[int]:
    """Return score if every selected die is used in a legal combo; else None."""
    if not dice:
        return None
    result = _max_full_score(_to_key(_as_counts(dice)))
    if result is None or result <= 0:
        return None
    return result


def has_any_score(dice: Sequence[int]) -> bool:
    """True if the roll contains at least one legal scoring combination."""
    counts = _as_counts(dice)
    if counts[1] > 0 or counts[5] > 0:
        return True
    if any(counts[face] >= 3 for face in range(1, 7)):
        return True
    for faces, _ in STRAIGHTS:
        if all(counts[face] > 0 for face in faces):
            return True
    return False


def selection_score_or_zero(dice: Sequence[int]) -> int:
    scored = score_selection(dice)
    return 0 if scored is None else scored


def iter_scoring_index_sets(dice: Sequence[int]) -> Iterable[tuple[int, ...]]:
    """Yield sorted index tuples that form a valid non-empty scoring selection."""
    n = len(dice)
    for mask in range(1, 1 << n):
        indices = tuple(i for i in range(n) if mask & (1 << i))
        values = [dice[i] for i in indices]
        if score_selection(values) is not None:
            yield indices
