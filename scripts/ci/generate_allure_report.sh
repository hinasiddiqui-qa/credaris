#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

RESULTS_DIR="reports/allure-results"
REPORT_DIR="reports/allure-report"
ZIP_PATH="reports/allure-report.zip"

if [[ ! -d "$RESULTS_DIR" ]] || [[ -z "$(ls -A "$RESULTS_DIR" 2>/dev/null || true)" ]]; then
    echo "No Allure results found in $RESULTS_DIR"
    exit 0
fi

if ! command -v allure >/dev/null 2>&1; then
    echo "Allure CLI not found on PATH — Jenkins Allure plugin will still publish results."
    exit 0
fi

allure generate "$RESULTS_DIR" -o "$REPORT_DIR" --clean

rm -f "$ZIP_PATH"
if command -v zip >/dev/null 2>&1; then
    (cd reports && zip -qr allure-report.zip allure-report)
elif command -v tar >/dev/null 2>&1; then
    tar -czf "$ZIP_PATH" -C reports allure-report
else
    echo "Neither zip nor tar available — email attachment will be skipped."
    exit 0
fi

echo "Allure report ready: $REPORT_DIR"
echo "Allure archive ready: $ZIP_PATH"
