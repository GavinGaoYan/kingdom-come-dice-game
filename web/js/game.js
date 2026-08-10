/** Match / turn state machine for KCD2 dice. */

import { hasAnyScore, scoreSelection } from "./scoring.js";

export const Player = { HUMAN: "human", AI: "ai" };
export const Phase = {
  NEED_ROLL: "need_roll",
  SELECTING: "selecting",
  GAME_OVER: "game_over",
};

export function newMatch(target = 3000) {
  return {
    target,
    scores: { [Player.HUMAN]: 0, [Player.AI]: 0 },
    current: Player.HUMAN,
    turnScore: 0,
    dice: [1, 1, 1, 1, 1, 1],
    held: [false, false, false, false, false, false],
    selected: [false, false, false, false, false, false],
    phase: Phase.NEED_ROLL,
    winner: null,
    message: "点「掷骰子」开始",
  };
}

function clone(state) {
  return {
    ...state,
    scores: { ...state.scores },
    dice: [...state.dice],
    held: [...state.held],
    selected: [...state.selected],
  };
}

export function activeIndices(state) {
  return state.held.map((h, i) => (!h ? i : -1)).filter((i) => i >= 0);
}

export function selectedIndices(state) {
  return state.selected.map((on, i) => (on ? i : -1)).filter((i) => i >= 0);
}

export function selectionScore(state) {
  const idx = selectedIndices(state);
  if (!idx.length) return null;
  return scoreSelection(idx.map((i) => state.dice[i]));
}

export function selectionValid(state) {
  return selectionScore(state) !== null;
}

export function toggleDie(state, index) {
  const s = clone(state);
  if (s.phase !== Phase.SELECTING || s.held[index]) return s;
  s.selected[index] = !s.selected[index];
  return s;
}

export function setSelection(state, indices) {
  const s = clone(state);
  if (s.phase !== Phase.SELECTING) return s;
  s.selected = s.selected.map(() => false);
  for (const i of indices) {
    if (!s.held[i]) s.selected[i] = true;
  }
  return s;
}

function endTurnAfterBust(state) {
  const s = clone(state);
  const loser = s.current;
  s.turnScore = 0;
  s.held = s.held.map(() => false);
  s.selected = s.selected.map(() => false);
  s.current = loser === Player.HUMAN ? Player.AI : Player.HUMAN;
  s.phase = Phase.NEED_ROLL;
  s.message = loser === Player.HUMAN ? "你爆点了，本轮清零" : "对手爆点，本轮清零";
  return s;
}

export function roll(state, rng = Math.random) {
  let s = clone(state);
  if (s.phase !== Phase.NEED_ROLL) return s;

  const active = activeIndices(s);
  for (const i of active) {
    s.dice[i] = 1 + Math.floor(rng() * 6);
  }
  s.selected = s.selected.map(() => false);
  s.phase = Phase.SELECTING;

  const values = active.map((i) => s.dice[i]);
  if (!hasAnyScore(values)) return endTurnAfterBust(s);

  s.message = "选出得分骰子";
  return s;
}

function applySelection(state) {
  const score = selectionScore(state);
  if (score === null) return state;
  const s = clone(state);
  for (let i = 0; i < 6; i++) {
    if (s.selected[i]) s.held[i] = true;
  }
  s.turnScore += score;
  if (s.held.every(Boolean)) s.held = s.held.map(() => false); // hot dice
  s.selected = s.selected.map(() => false);
  s.message = `本轮累计 ${s.turnScore}`;
  return s;
}

export function scoreAndContinue(state, rng = Math.random) {
  if (state.phase !== Phase.SELECTING || !selectionValid(state)) return state;
  let s = applySelection(state);
  s.phase = Phase.NEED_ROLL;
  return roll(s, rng);
}

export function scoreAndPass(state) {
  if (state.phase !== Phase.SELECTING || !selectionValid(state)) return state;
  let s = applySelection(state);
  s.scores[s.current] += s.turnScore;

  if (s.scores[s.current] >= s.target) {
    s.winner = s.current;
    s.phase = Phase.GAME_OVER;
    s.turnScore = 0;
    s.held = s.held.map(() => false);
    s.selected = s.selected.map(() => false);
    s.message = s.winner === Player.HUMAN ? "你赢了！" : "对手获胜";
    return s;
  }

  const prev = s.current;
  s.turnScore = 0;
  s.held = s.held.map(() => false);
  s.selected = s.selected.map(() => false);
  s.current = prev === Player.HUMAN ? Player.AI : Player.HUMAN;
  s.phase = Phase.NEED_ROLL;
  s.message = "回合结束";
  return s;
}
