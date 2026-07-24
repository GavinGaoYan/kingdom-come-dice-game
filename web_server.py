"""Minimal browser front-end for the KCD2 dice rebuild (stdlib only)."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from random import Random
from typing import Any
from urllib.parse import urlparse

from kcd2_dice.ai import AiActionKind, apply_choice, decide
from kcd2_dice.game import (
    MatchState,
    Phase,
    Player,
    new_match,
    roll,
    score_and_continue,
    score_and_pass,
    toggle_die,
)

HOST = "0.0.0.0"
PORT = 8765

_lock = threading.Lock()
_rng = Random()
_state: MatchState = new_match(target=3000)


def _public_state(state: MatchState) -> dict[str, Any]:
    return {
        "target": state.target,
        "scores": {
            "human": state.scores[Player.HUMAN],
            "ai": state.scores[Player.AI],
        },
        "current": state.current.value,
        "turn_score": state.turn_score,
        "dice": list(state.dice),
        "held": list(state.held),
        "selected": list(state.selected),
        "phase": state.phase.value,
        "winner": state.winner.value if state.winner else None,
        "message": state.message,
        "selection_score": state.selection_score,
        "selection_valid": state.selection_is_valid,
    }


def _run_ai_until_human(state: MatchState) -> MatchState:
    """Resolve a full AI turn (or until game over / human's turn)."""
    guard = 0
    while state.current == Player.AI and state.phase != Phase.GAME_OVER and guard < 40:
        guard += 1
        if state.phase == Phase.NEED_ROLL:
            state = roll(state, _rng)
            continue
        action = decide(state, _rng)
        if action is None:
            break
        state = apply_choice(state, action)
        if action.kind == AiActionKind.SELECT_AND_CONTINUE:
            state = score_and_continue(state, _rng)
        else:
            state = score_and_pass(state)
    return state


INDEX_HTML = """<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>天国拯救 II · 骰子</title>
  <style>
    :root {
      --bg: #163024;
      --panel: #214233;
      --accent: #c6a15b;
      --text: #f2e6c9;
      --muted: #9fb7a8;
      --danger: #b85c38;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0; min-height: 100vh;
      font-family: "Songti SC", "Noto Serif SC", Georgia, serif;
      color: var(--text);
      background:
        radial-gradient(ellipse at top, #24503a 0%, transparent 55%),
        linear-gradient(160deg, #0f2119, #163024 40%, #1a2c22);
    }
    main {
      max-width: 920px; margin: 0 auto; padding: 28px 18px 48px;
    }
    h1 { margin: 0; font-size: clamp(1.8rem, 4vw, 2.6rem); color: var(--accent); letter-spacing: 0.04em; }
    .sub { color: var(--muted); margin: 6px 0 22px; }
    .board {
      display: grid; gap: 18px;
      background: color-mix(in srgb, var(--panel) 88%, black);
      border: 1px solid color-mix(in srgb, var(--accent) 35%, transparent);
      border-radius: 18px; padding: 18px;
      box-shadow: 0 20px 60px rgba(0,0,0,.35);
    }
    .row { display: flex; justify-content: space-between; align-items: baseline; gap: 12px; }
    .name.active { color: var(--accent); }
    .dice { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 12px; }
    .die {
      width: 64px; height: 64px; border-radius: 12px;
      border: 2px solid color-mix(in srgb, var(--accent) 40%, transparent);
      background: var(--panel); color: var(--text);
      font-size: 2rem; display: grid; place-items: center;
      cursor: pointer; transition: transform .12s ease, background .12s ease;
    }
    .die:hover:not(:disabled) { transform: translateY(-2px); }
    .die.held { background: #3e2f1a; color: var(--accent); cursor: default; }
    .die.selected { background: var(--accent); color: #1a1a1a; }
    .die:disabled { opacity: .75; cursor: default; }
    .controls { display: flex; flex-wrap: wrap; gap: 10px; margin-top: 8px; }
    button.action {
      border: 0; border-radius: 999px; padding: 12px 18px;
      font: inherit; font-size: 1rem; cursor: pointer;
      background: var(--accent); color: #1a1a1a;
    }
    button.action.secondary { background: var(--panel); color: var(--text); border: 1px solid var(--accent); }
    button.action:disabled { opacity: .45; cursor: not-allowed; }
    .msg { min-height: 1.4em; margin-top: 10px; color: var(--muted); }
    .sel { color: var(--accent); }
    .rules {
      margin-top: 18px; color: var(--muted); font-size: .95rem; line-height: 1.55;
      columns: 2; column-gap: 24px;
    }
    @media (max-width: 700px) { .rules { columns: 1; } .die { width: 52px; height: 52px; font-size: 1.6rem; } }
  </style>
</head>
<body>
  <main>
    <h1>天国拯救 II</h1>
    <p class="sub">网页体验版 · 目标 <span id="target">3000</span> 分</p>
    <section class="board">
      <div>
        <div class="row">
          <strong id="ai-name" class="name">对手</strong>
          <span>总分 <b id="ai-score">0</b> · 本轮 <b id="ai-turn">0</b></span>
        </div>
        <div class="dice" id="ai-dice"></div>
      </div>
      <hr style="border:0;border-top:1px solid #c6a15b55;margin:4px 0;" />
      <div>
        <div class="row">
          <strong id="you-name" class="name">你</strong>
          <span>总分 <b id="you-score">0</b> · 本轮 <b id="you-turn">0</b></span>
        </div>
        <div class="dice" id="you-dice"></div>
      </div>
      <div class="controls">
        <button class="action" id="btn-roll">掷骰子</button>
        <button class="action secondary" id="btn-continue">得分并继续</button>
        <button class="action secondary" id="btn-pass">得分并结束</button>
        <button class="action secondary" id="btn-reset">新游戏</button>
      </div>
      <div class="sel">当前选择：<span id="selection">0</span></div>
      <div class="msg" id="message"></div>
    </section>
    <div class="rules">
      <div>1=100 · 5=50</div>
      <div>三个1=1000 · 三个N=N×100</div>
      <div>多一颗相同则组合分翻倍</div>
      <div>1-5=500 · 2-6=750 · 1-6=1500</div>
      <div>选中骰子须全部可计分</div>
      <div>全计分可重掷六颗（热骰）</div>
    </div>
  </main>
  <script>
    const FACES = {1:"⚀",2:"⚁",3:"⚂",4:"⚃",5:"⚄",6:"⚅"};
    let state = null;

    async function api(path, body) {
      const res = await fetch(path, {
        method: "POST",
        headers: {"Content-Type":"application/json"},
        body: body ? JSON.stringify(body) : "{}",
      });
      state = await res.json();
      render();
    }

    function renderDie(container, i, interactive) {
      const btn = document.createElement("button");
      btn.className = "die";
      btn.textContent = FACES[state.dice[i]];
      if (state.held[i]) btn.classList.add("held");
      if (state.selected[i]) btn.classList.add("selected");
      const canClick = interactive && state.current === "human" && state.phase === "selecting" && !state.held[i];
      btn.disabled = !canClick;
      if (canClick) btn.onclick = () => api("/api/toggle", {index: i});
      container.appendChild(btn);
    }

    function render() {
      document.getElementById("target").textContent = state.target;
      document.getElementById("ai-score").textContent = state.scores.ai;
      document.getElementById("you-score").textContent = state.scores.human;
      document.getElementById("ai-turn").textContent = state.current === "ai" ? state.turn_score : 0;
      document.getElementById("you-turn").textContent = state.current === "human" ? state.turn_score : 0;
      document.getElementById("ai-name").classList.toggle("active", state.current === "ai");
      document.getElementById("you-name").classList.toggle("active", state.current === "human");
      document.getElementById("message").textContent = state.message || "";
      const sel = state.selection_score;
      document.getElementById("selection").textContent =
        sel != null ? sel : (state.selected.some(Boolean) ? "无效" : "0");

      const aiDice = document.getElementById("ai-dice");
      const youDice = document.getElementById("you-dice");
      aiDice.innerHTML = ""; youDice.innerHTML = "";
      for (let i = 0; i < 6; i++) {
        renderDie(aiDice, i, false);
        renderDie(youDice, i, true);
      }

      const human = state.current === "human" && state.phase !== "game_over";
      document.getElementById("btn-roll").disabled = !(human && state.phase === "need_roll");
      const canScore = human && state.phase === "selecting" && state.selection_valid;
      document.getElementById("btn-continue").disabled = !canScore;
      document.getElementById("btn-pass").disabled = !canScore;
    }

    document.getElementById("btn-roll").onclick = () => api("/api/roll");
    document.getElementById("btn-continue").onclick = () => api("/api/continue");
    document.getElementById("btn-pass").onclick = () => api("/api/pass");
    document.getElementById("btn-reset").onclick = () => api("/api/reset");

    fetch("/api/state").then(r => r.json()).then(s => { state = s; render(); });
  </script>
</body>
</html>
"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt: str, *args: Any) -> None:  # quieter
        pass

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, payload: dict[str, Any], code: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self._send(code, data, "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            self._send(200, INDEX_HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if path == "/api/state":
            with _lock:
                self._json(_public_state(_state))
            return
        self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        global _state
        path = urlparse(self.path).path
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._json({"error": "invalid json"}, 400)
            return

        with _lock:
            state = _state
            if path == "/api/reset":
                state = new_match(target=state.target)
            elif path == "/api/roll":
                if state.current == Player.HUMAN and state.phase == Phase.NEED_ROLL:
                    state = roll(state, _rng)
                    state = _run_ai_until_human(state)
            elif path == "/api/toggle":
                idx = int(payload.get("index", -1))
                if state.current == Player.HUMAN:
                    state = toggle_die(state, idx)
            elif path == "/api/continue":
                if state.current == Player.HUMAN and state.selection_is_valid:
                    state = score_and_continue(state, _rng)
                    state = _run_ai_until_human(state)
            elif path == "/api/pass":
                if state.current == Player.HUMAN and state.selection_is_valid:
                    state = score_and_pass(state)
                    state = _run_ai_until_human(state)
            else:
                self._json({"error": "not found"}, 404)
                return
            _state = state
            self._json(_public_state(state))


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"KCD2 dice web UI on http://0.0.0.0:{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
