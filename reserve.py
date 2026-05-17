"""Thin CLI entry point — config + flows + logging.

The old monolithic script has been split into ``ticketbot/``; see README
for the architecture.
"""
from __future__ import annotations

import argparse
import sys

from ticketbot.config import UserConfig
from ticketbot.flows import book
from ticketbot.logging_setup import configure as configure_logging


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="thaiticketmajor concert reservation bot")
    p.add_argument(
        "--config",
        default="userdetail.json",
        help="path to userdetail.json (default: %(default)s)",
    )
    p.add_argument("--headless", action="store_true", help="run Chrome headless")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    configure_logging()
    cfg = UserConfig.load(args.config)
    return book(cfg, headless=args.headless)


if __name__ == "__main__":
    sys.exit(main())
