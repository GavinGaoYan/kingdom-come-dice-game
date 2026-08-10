/** KCD2 dice scoring — pure functions, no DOM. */

const STRAIGHTS = [
  { faces: [1, 2, 3, 4, 5, 6], score: 1500 },
  { faces: [2, 3, 4, 5, 6], score: 750 },
  { faces: [1, 2, 3, 4, 5], score: 500 },
];

function countsOf(dice) {
  const c = [0, 0, 0, 0, 0, 0, 0];
  for (const v of dice) {
    if (v < 1 || v > 6) throw new Error(`invalid face ${v}`);
    c[v] += 1;
  }
  return c;
}

function keyOf(c) {
  return c.slice(1).join(",");
}

function nOfAKindScore(face, n) {
  const base = face === 1 ? 1000 : face * 100;
  return base * 2 ** (n - 3);
}

const memo = new Map();

/** Max score using every die, or null if impossible. */
function maxFullScoreFromCounts(c) {
  const key = keyOf(c);
  if (memo.has(key)) return memo.get(key);

  const total = c.slice(1).reduce((a, b) => a + b, 0);
  if (total === 0) {
    memo.set(key, 0);
    return 0;
  }

  let best = null;
  const consider = (points, next) => {
    const rest = maxFullScoreFromCounts(next);
    if (rest === null) return;
    const sum = points + rest;
    if (best === null || sum > best) best = sum;
  };

  if (c[1] > 0) {
    const n = c.slice();
    n[1] -= 1;
    consider(100, n);
  }
  if (c[5] > 0) {
    const n = c.slice();
    n[5] -= 1;
    consider(50, n);
  }
  for (let face = 1; face <= 6; face++) {
    for (let n = 3; n <= c[face]; n++) {
      const next = c.slice();
      next[face] -= n;
      consider(nOfAKindScore(face, n), next);
    }
  }
  for (const { faces, score } of STRAIGHTS) {
    if (faces.every((f) => c[f] > 0)) {
      const next = c.slice();
      for (const f of faces) next[f] -= 1;
      consider(score, next);
    }
  }

  memo.set(key, best);
  return best;
}

export function scoreSelection(dice) {
  if (!dice.length) return null;
  const result = maxFullScoreFromCounts(countsOf(dice));
  return result === null || result <= 0 ? null : result;
}

export function hasAnyScore(dice) {
  const c = countsOf(dice);
  if (c[1] > 0 || c[5] > 0) return true;
  for (let f = 1; f <= 6; f++) if (c[f] >= 3) return true;
  return STRAIGHTS.some(({ faces }) => faces.every((f) => c[f] > 0));
}

/** Yield arrays of local indices that form a valid scoring subset. */
export function* iterScoringIndexSets(dice) {
  const n = dice.length;
  for (let mask = 1; mask < 1 << n; mask++) {
    const idx = [];
    const vals = [];
    for (let i = 0; i < n; i++) {
      if (mask & (1 << i)) {
        idx.push(i);
        vals.push(dice[i]);
      }
    }
    if (scoreSelection(vals) !== null) yield idx;
  }
}
