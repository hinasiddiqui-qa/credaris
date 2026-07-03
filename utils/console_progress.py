"""Console progress messages for long-running session setup."""

from __future__ import annotations

import sys

from utils.logger import _running_under_pytest, get_logger


def announce(message: str) -> None:
    """Show setup progress in scripts; during pytest, write to log file only."""
    if _running_under_pytest():
        get_logger("credaris.progress").info(message)
        return

    print(f"\n>>> {message}", flush=True)
    sys.stdout.flush()
