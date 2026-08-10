/** Heuristic AI for KCD2 dice (browser). */

import { iterScoringIndexSets, scoreSelection } from "./scoring.js";
import {
  Phase,
  Player,
  activeIndices,
  setSelection,
} from "./game.js";

export function chooseSelection(state) {
  const active = activeIndices(state);
  const values = active.map((i) => state.dice[i]);
  if (!values.length) return [];

  let best = null;
  let bestKey = null;
  for (const local of iterScoringIndexSets(values)) {
    const globals = local.map((i) => active[i]);
    const pts = scoreSelection(local.map((i) => values[i])) || 0;
    const remaining = values.length - local.length;
    const key = [pts + remaining * 35, remaining, pts];
    if (
      !bestKey ||
      key[0] > bestKey[0] ||
      (key[0] === bestKey[0] && key[1] > bestKey[1]) ||
      (key[0] === bestKey[0] && key[1] === bestKey[1] && key[2] > bestKey[2])
    ) {
      bestKey = key;
      best = globals;
    }
  }
  return best || [];
}

export function shouldContinue(state, selection) {
  const pts = scoreSelection(selection.map((i) => state.dice[i])) || 0;
  const projected = state.turnScore + pts;
  const remaining = activeIndices(state).length - selection.length;
  const hot = remaining === 0;
  const mine = state.scores[state.current];
  const oppKey = state.current === Player.HUMAN ? Player.AI : Player.HUMAN;
  const opp = state.scores[oppKey];
  const need = state.target - mine;

  if (projected >= need) return false;
  if (hot) return true;
  if (remaining >= 4) return projected < 800 || mine + projected < opp;
  if (remaining >= 3) return projected < 400 && mine + 400 < state.target;
  return projected < 150 && mine + projected + 300 < opp;
}

export function decide(state) {
  if (state.phase !== Phase.SELECTING || state.current !== Player.AI) return null;
  const indices = chooseSelection(state);
  if (!indices.length) return null;
  return {
    indices,
    continue: shouldContinue(state, indices),
  };
}

export function applyAiChoice(state, action) {
  return setSelection(state, action.indices);
}
