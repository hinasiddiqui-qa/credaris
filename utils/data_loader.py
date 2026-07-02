"""Test data loading helpers."""

from __future__ import annotations

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEST_DATA_DIR = PROJECT_ROOT / "test_data"


def load_json(filename: str) -> dict | list:
    path = TEST_DATA_DIR / filename
    return json.loads(path.read_text(encoding="utf-8"))
