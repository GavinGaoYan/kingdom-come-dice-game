# KCD2 Dice — Mobile Web Design

Date: 2026-07-24  
Branch: `cursor/kcd2-web-mobile-6c73`

## Goal

From-scratch **mobile-first web** recreation of Kingdom Come: Deliverance 2 dice.  
**No Tkinter.** Playable in a phone browser via a public HTTPS tunnel.

## Stack

- Static front-end: HTML / CSS / vanilla JS (game rules + AI in the browser)
- Tiny Python `http.server` only to host static files
- Cloudflare quick tunnel for phone access

## Rules (KCD2)

Same as prior research: 1/5 singles, n-of-a-kind with doubling, straights 1-5 / 2-6 / 1-6, hot dice, bust, score&continue / score&pass. Target default **3000**. No three-pairs, no loaded dice/badges in v1.

## UX

- One full-viewport composition; brand “天国拯救 II” as hero signal
- Large touch dice and bottom action bar
- Opponent on top, player below
- Rules behind a sheet / expandable panel (not cluttering first view)

## Out of scope

Tk UI, PyInstaller, multiplayer networking, special dice.
