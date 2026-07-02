# Generate and open the Allure HTML report from the latest pytest run.
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
$ResultsDir = Join-Path $ProjectRoot "reports\allure-results"

if (-not (Test-Path $ResultsDir)) {
    Write-Error "Allure results not found. Run pytest first: reports/allure-results"
}

allure serve $ResultsDir
