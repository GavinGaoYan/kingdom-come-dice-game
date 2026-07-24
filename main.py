#!/usr/bin/env python3
"""Entrypoint for the KCD2 dice rebuild."""

from kcd2_dice.ui import run


def main() -> None:
    run(target=3000)


if __name__ == "__main__":
    main()
