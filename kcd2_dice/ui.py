"""Tkinter UI for the KCD2 dice rebuild — presentation only."""

from __future__ import annotations

import tkinter as tk
from random import Random
from tkinter import font, messagebox
from typing import Optional

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

DICE_FACES = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}

BG = "#1F3A2A"
PANEL = "#2A4A36"
ACCENT = "#C6A15B"
TEXT = "#F2E6C9"
MUTED = "#A8C0B0"
DANGER = "#B85C38"


class DiceApp:
    def __init__(self, root: tk.Tk, target: int = 3000) -> None:
        self.root = root
        self.root.title("天国拯救 II · 骰子")
        self.root.geometry("1280x720")
        self.root.configure(bg=BG)
        self.root.minsize(960, 540)

        self.rng = Random()
        self.state: MatchState = new_match(target=target)
        self._ai_job: Optional[str] = None

        self.title_font = font.Font(family="Georgia", size=22, weight="bold")
        self.label_font = font.Font(family="Georgia", size=14)
        self.dice_font = font.Font(family="Segoe UI Symbol", size=36)
        self.small_font = font.Font(family="Georgia", size=11)

        self._build()
        self._render()

    def _build(self) -> None:
        shell = tk.Frame(self.root, bg=BG)
        shell.pack(fill="both", expand=True, padx=16, pady=16)

        play = tk.Frame(shell, bg=BG)
        play.pack(side="left", fill="both", expand=True)

        rules = tk.Frame(shell, bg=PANEL, width=360)
        rules.pack(side="right", fill="y", padx=(16, 0))
        rules.pack_propagate(False)
        self._build_rules(rules)

        brand = tk.Label(
            play,
            text="天国拯救 II",
            font=self.title_font,
            bg=BG,
            fg=ACCENT,
        )
        brand.pack(anchor="w")
        tk.Label(
            play,
            text="先将本轮得分入账，率先达到目标者获胜",
            font=self.small_font,
            bg=BG,
            fg=MUTED,
        ).pack(anchor="w", pady=(0, 12))

        self.opponent_frame = self._build_player_strip(play, "对手", is_top=True)
        tk.Frame(play, height=2, bg=ACCENT).pack(fill="x", pady=12)
        self.player_frame = self._build_player_strip(play, "你", is_top=False)

        controls = tk.Frame(play, bg=BG)
        controls.pack(fill="x", pady=16)

        self.roll_btn = tk.Button(
            controls, text="掷骰子", font=self.label_font, bg=ACCENT, fg="#1A1A1A",
            relief="flat", padx=18, pady=8, command=self.on_roll,
        )
        self.roll_btn.pack(side="left", padx=(0, 10))

        self.continue_btn = tk.Button(
            controls, text="得分并继续", font=self.label_font, bg=PANEL, fg=TEXT,
            relief="flat", padx=18, pady=8, command=self.on_continue,
        )
        self.continue_btn.pack(side="left", padx=(0, 10))

        self.pass_btn = tk.Button(
            controls, text="得分并结束", font=self.label_font, bg=PANEL, fg=TEXT,
            relief="flat", padx=18, pady=8, command=self.on_pass,
        )
        self.pass_btn.pack(side="left", padx=(0, 10))

        self.reset_btn = tk.Button(
            controls, text="新游戏", font=self.small_font, bg=BG, fg=MUTED,
            relief="flat", command=self.on_reset,
        )
        self.reset_btn.pack(side="right")

        self.message = tk.Label(
            play, text="", font=self.label_font, bg=BG, fg=TEXT, anchor="w",
        )
        self.message.pack(fill="x", pady=(8, 0))

        self.selection_label = tk.Label(
            play, text="当前选择: 0", font=self.small_font, bg=BG, fg=ACCENT, anchor="w",
        )
        self.selection_label.pack(fill="x")

    def _build_player_strip(self, parent: tk.Frame, title: str, is_top: bool) -> dict:
        frame = tk.Frame(parent, bg=BG)
        frame.pack(fill="x", pady=8)

        header = tk.Frame(frame, bg=BG)
        header.pack(fill="x")
        name = tk.Label(header, text=title, font=self.label_font, bg=BG, fg=TEXT)
        name.pack(side="left")
        total = tk.Label(header, text="总分 0", font=self.label_font, bg=BG, fg=MUTED)
        total.pack(side="right")
        round_score = tk.Label(header, text="本轮 0", font=self.label_font, bg=BG, fg=MUTED)
        round_score.pack(side="right", padx=16)

        dice_row = tk.Frame(frame, bg=BG)
        dice_row.pack(fill="x", pady=10)
        dice_widgets: list[tk.Widget] = []
        for i in range(6):
            if is_top:
                lbl = tk.Label(
                    dice_row, text=DICE_FACES[1], font=self.dice_font,
                    bg=PANEL, fg=TEXT, width=2, relief="ridge", bd=2,
                )
                lbl.pack(side="left", padx=8)
                dice_widgets.append(lbl)
            else:
                btn = tk.Button(
                    dice_row, text=DICE_FACES[1], font=self.dice_font,
                    bg=PANEL, fg=TEXT, width=2, relief="ridge", bd=2,
                    command=lambda idx=i: self.on_toggle(idx),
                )
                btn.pack(side="left", padx=8)
                dice_widgets.append(btn)

        return {
            "frame": frame,
            "name": name,
            "total": total,
            "round": round_score,
            "dice": dice_widgets,
        }

    def _build_rules(self, parent: tk.Frame) -> None:
        tk.Label(
            parent, text="计分规则", font=self.label_font, bg=PANEL, fg=ACCENT,
        ).pack(anchor="w", padx=16, pady=(16, 8))

        lines = [
            "1 = 100　5 = 50",
            "三个 1 = 1000",
            "三个 N(2-6) = N×100",
            "每多一颗相同骰子，组合分翻倍",
            "1-2-3-4-5 = 500",
            "2-3-4-5-6 = 750",
            "1-2-3-4-5-6 = 1500",
            "",
            "可选多个得分组合，但选中的",
            "每一颗都必须能计分。",
            "全部计分后可重掷全部六颗",
            "（热骰，本轮分仍未入账）。",
            "无计分组合则爆点，本轮清零。",
            f"目标分：{self.state.target}",
        ]
        for line in lines:
            tk.Label(
                parent, text=line, font=self.small_font, bg=PANEL, fg=TEXT,
                justify="left", anchor="w",
            ).pack(anchor="w", padx=16, pady=1)

    def _human_can_act(self) -> bool:
        return (
            self.state.phase != Phase.GAME_OVER
            and self.state.current == Player.HUMAN
        )

    def on_roll(self) -> None:
        if not self._human_can_act() or self.state.phase != Phase.NEED_ROLL:
            return
        self.state = roll(self.state, self.rng)
        self._render()
        self._maybe_start_ai()

    def on_toggle(self, index: int) -> None:
        if not self._human_can_act() or self.state.phase != Phase.SELECTING:
            return
        self.state = toggle_die(self.state, index)
        self._render()

    def on_continue(self) -> None:
        if not self._human_can_act() or not self.state.selection_is_valid:
            return
        self.state = score_and_continue(self.state, self.rng)
        self._render()
        self._maybe_start_ai()

    def on_pass(self) -> None:
        if not self._human_can_act() or not self.state.selection_is_valid:
            return
        self.state = score_and_pass(self.state)
        self._render()
        if self.state.phase == Phase.GAME_OVER:
            self._announce_winner()
            return
        self._maybe_start_ai()

    def on_reset(self) -> None:
        if self._ai_job is not None:
            self.root.after_cancel(self._ai_job)
            self._ai_job = None
        self.state = new_match(target=self.state.target)
        self._render()

    def _maybe_start_ai(self) -> None:
        if self.state.phase == Phase.GAME_OVER:
            return
        if self.state.current != Player.AI:
            return
        self._ai_job = self.root.after(700, self._ai_step)

    def _ai_step(self) -> None:
        self._ai_job = None
        if self.state.current != Player.AI or self.state.phase == Phase.GAME_OVER:
            return

        if self.state.phase == Phase.NEED_ROLL:
            self.state = roll(self.state, self.rng)
            self._render()
            if self.state.current == Player.AI and self.state.phase == Phase.SELECTING:
                self._ai_job = self.root.after(900, self._ai_step)
            elif self.state.current == Player.HUMAN:
                return
            elif self.state.phase == Phase.GAME_OVER:
                self._announce_winner()
            return

        action = decide(self.state, self.rng)
        if action is None:
            # Should not happen if scoring is consistent; recover by ending turn.
            self.state = score_and_pass(self.state) if self.state.selection_is_valid else self.state
            self._render()
            return

        self.state = apply_choice(self.state, action)
        self._render()

        def finish() -> None:
            if action.kind == AiActionKind.SELECT_AND_CONTINUE:
                self.state = score_and_continue(self.state, self.rng)
            else:
                self.state = score_and_pass(self.state)
            self._render()
            if self.state.phase == Phase.GAME_OVER:
                self._announce_winner()
                return
            if self.state.current == Player.AI:
                self._ai_job = self.root.after(700, self._ai_step)

        self._ai_job = self.root.after(800, finish)

    def _announce_winner(self) -> None:
        who = "你" if self.state.winner == Player.HUMAN else "对手"
        if messagebox.askyesno("游戏结束", f"{who}达到 {self.state.target} 分获胜！再来一局？"):
            self.on_reset()

    def _render(self) -> None:
        s = self.state
        self.opponent_frame["total"].config(text=f"总分 {s.scores[Player.AI]}")
        self.player_frame["total"].config(text=f"总分 {s.scores[Player.HUMAN]}")

        opp_round = s.turn_score if s.current == Player.AI else 0
        you_round = s.turn_score if s.current == Player.HUMAN else 0
        self.opponent_frame["round"].config(text=f"本轮 {opp_round}")
        self.player_frame["round"].config(text=f"本轮 {you_round}")

        for i, widget in enumerate(self.opponent_frame["dice"]):
            self._style_die(widget, i, interactive=False)
        for i, widget in enumerate(self.player_frame["dice"]):
            self._style_die(widget, i, interactive=True)

        sel = s.selection_score
        self.selection_label.config(
            text=f"当前选择: {sel if sel is not None else 0}"
            + ("" if sel is not None or not s.selected_indices else "（无效）")
        )
        self.message.config(text=s.message)

        human = self._human_can_act()
        self.roll_btn.config(
            state=("normal" if human and s.phase == Phase.NEED_ROLL else "disabled")
        )
        can_score = human and s.phase == Phase.SELECTING and s.selection_is_valid
        self.continue_btn.config(state=("normal" if can_score else "disabled"))
        self.pass_btn.config(state=("normal" if can_score else "disabled"))

        turn_color = ACCENT if s.current == Player.HUMAN else DANGER
        self.player_frame["name"].config(
            fg=turn_color if s.current == Player.HUMAN else TEXT
        )
        self.opponent_frame["name"].config(
            fg=turn_color if s.current == Player.AI else TEXT
        )

    def _style_die(self, widget: tk.Widget, index: int, interactive: bool) -> None:
        face = DICE_FACES[self.state.dice[index]]
        held = self.state.held[index]
        selected = self.state.selected[index]

        if held:
            bg, fg = "#3E2F1A", ACCENT
        elif selected:
            bg, fg = ACCENT, "#1A1A1A"
        else:
            bg, fg = PANEL, TEXT

        widget.config(text=face, bg=bg, fg=fg)
        if interactive and isinstance(widget, tk.Button):
            enable = (
                self._human_can_act()
                and self.state.phase == Phase.SELECTING
                and not held
            )
            widget.config(state=("normal" if enable else "disabled"))


def run(target: int = 3000) -> None:
    root = tk.Tk()
    DiceApp(root, target=target)
    root.mainloop()
