#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

python -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r requirements.txt

python scripts/ci/generate_config_from_env.py

mkdir -p reports logs screenshots
pytest -m "${PYTEST_MARKER:-smoke}" -v "$@"
