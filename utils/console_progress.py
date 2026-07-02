"""Console progress messages for long-running session setup."""

from __future__ import annotations

import sys


def announce(message: str) -> None:
    """Print immediately so local pytest runs show setup progress."""
    print(f"\n>>> {message}", flush=True)
    sys.stdout.flush()
