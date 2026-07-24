/** Mobile UI controller for KCD2 web dice. */

import { decide, applyAiChoice } from "./ai.js";
import {
  Phase,
  Player,
  newMatch,
  roll,
  scoreAndContinue,
  scoreAndPass,
  selectionScore,
  selectionValid,
  toggleDie,
} from "./game.js";

const FACES = { 1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅" };
const TARGET = 3000;
const AI_STEP_MS = 700;

let state = newMatch(TARGET);
let busy = false;
let aiTimer = 0;

const $ = (id) => document.getElementById(id);

function renderDice(container, interactive) {
  container.innerHTML = "";
  for (let i = 0; i < 6; i++) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "die";
    btn.textContent = FACES[state.dice[i]];
    if (state.held[i]) btn.classList.add("held");
    if (state.selected[i]) btn.classList.add("selected");

    const can =
      interactive &&
      !busy &&
      state.current === Player.HUMAN &&
      state.phase === Phase.SELECTING &&
      !state.held[i];

    btn.disabled = !can;
    if (can) {
      btn.addEventListener("click", () => {
        state = toggleDie(state, i);
        render();
      });
    }
    container.appendChild(btn);
  }
}

function pulseRoll() {
  for (const root of [$("ai-dice"), $("you-dice")]) {
    for (const die of root.querySelectorAll(".die")) {
      die.classList.add("rolling");
    }
  }
}

function render() {
  $("target").textContent = String(state.target);
  $("you-score").textContent = String(state.scores[Player.HUMAN]);
  $("ai-score").textContent = String(state.scores[Player.AI]);
  $("you-turn").textContent = String(
    state.current === Player.HUMAN ? state.turnScore : 0
  );
  $("ai-turn").textContent = String(
    state.current === Player.AI ? state.turnScore : 0
  );

  $("you-hud").classList.toggle("active", state.current === Player.HUMAN);
  $("ai-hud").classList.toggle("active", state.current === Player.AI);
  $("you-name").classList.toggle("turn", state.current === Player.HUMAN);
  $("ai-name").classList.toggle("turn", state.current === Player.AI);

  renderDice($("ai-dice"), false);
  renderDice($("you-dice"), true);

  const sel = selectionScore(state);
  $("selection").textContent =
    sel !== null ? String(sel) : state.selected.some(Boolean) ? "无效" : "0";
  $("message").textContent = state.message;

  const human =
    !busy && state.current === Player.HUMAN && state.phase !== Phase.GAME_OVER;
  $("btn-roll").disabled = !(human && state.phase === Phase.NEED_ROLL);
  const canScore = human && state.phase === Phase.SELECTING && selectionValid(state);
  $("btn-continue").disabled = !canScore;
  $("btn-pass").disabled = !canScore;

  if (state.phase === Phase.GAME_OVER) {
    $("win-title").textContent =
      state.winner === Player.HUMAN ? "胜利" : "惜败";
    $("win-text").textContent =
      state.winner === Player.HUMAN
        ? `你先达到 ${state.target} 分`
        : `对手先达到 ${state.target} 分`;
    $("win-overlay").classList.add("open");
  } else {
    $("win-overlay").classList.remove("open");
  }
}

function afterHumanAction() {
  render();
  if (state.current === Player.AI && state.phase !== Phase.GAME_OVER) {
    scheduleAi();
  }
}

function scheduleAi() {
  busy = true;
  render();
  clearTimeout(aiTimer);
  aiTimer = setTimeout(aiStep, AI_STEP_MS);
}

function aiStep() {
  if (state.current !== Player.AI || state.phase === Phase.GAME_OVER) {
    busy = false;
    render();
    return;
  }

  if (state.phase === Phase.NEED_ROLL) {
    pulseRoll();
    state = roll(state);
    render();
    aiTimer = setTimeout(aiStep, AI_STEP_MS);
    return;
  }

  const action = decide(state);
  if (!action) {
    busy = false;
    render();
    return;
  }

  state = applyAiChoice(state, action);
  render();

  aiTimer = setTimeout(() => {
    state = action.continue ? scoreAndContinue(state) : scoreAndPass(state);
    if (state.current === Player.AI && state.phase !== Phase.GAME_OVER) {
      render();
      aiTimer = setTimeout(aiStep, AI_STEP_MS);
    } else {
      busy = false;
      render();
    }
  }, AI_STEP_MS);
}

$("btn-roll").addEventListener("click", () => {
  if (busy || state.current !== Player.HUMAN || state.phase !== Phase.NEED_ROLL) return;
  pulseRoll();
  state = roll(state);
  afterHumanAction();
});

$("btn-continue").addEventListener("click", () => {
  if (busy || !selectionValid(state)) return;
  pulseRoll();
  state = scoreAndContinue(state);
  afterHumanAction();
});

$("btn-pass").addEventListener("click", () => {
  if (busy || !selectionValid(state)) return;
  state = scoreAndPass(state);
  afterHumanAction();
});

$("btn-reset").addEventListener("click", () => {
  clearTimeout(aiTimer);
  busy = false;
  state = newMatch(TARGET);
  render();
});

$("btn-again").addEventListener("click", () => {
  clearTimeout(aiTimer);
  busy = false;
  state = newMatch(TARGET);
  render();
});

$("btn-rules").addEventListener("click", () => {
  $("rules-sheet").classList.add("open");
});
$("btn-close-rules").addEventListener("click", () => {
  $("rules-sheet").classList.remove("open");
});
$("rules-sheet").addEventListener("click", (e) => {
  if (e.target.id === "rules-sheet") $("rules-sheet").classList.remove("open");
});

render();
