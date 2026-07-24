# Kingdom Come: Deliverance 2 — Dice

从零重写的《天国拯救 II》骰子小游戏（Python / Tkinter）。

## 运行

桌面版（需 Tkinter）：

```bash
python3 main.py
```

网页体验版（仅标准库，默认 `8765` 端口）：

```bash
python3 web_server.py
# 浏览器打开 http://127.0.0.1:8765
```

无需第三方运行时依赖（仅标准库）。开发测试：

```bash
python3 -m pip install pytest
python3 -m pytest -q
```

## 结构

```
kcd2_dice/
  scoring.py   # 纯规则计分
  game.py      # 回合 / 对局状态机
  ai.py        # 对手策略
  ui.py        # Tk 界面
main.py
tests/
```

旧版单文件 `UI_12_DICE.py` 已从此分支移除，逻辑不复用。

## 规则摘要

- 1=100，5=50；三连及以上按 KCD2 翻倍表计分
- 顺子：1-5=500，2-6=750，1-6=1500
- 选中的骰子必须全部可计分；爆点清零本轮；全计分可重掷六颗
- 默认目标分 3000

详见 `docs/superpowers/specs/2026-07-24-kcd2-dice-design.md`。
