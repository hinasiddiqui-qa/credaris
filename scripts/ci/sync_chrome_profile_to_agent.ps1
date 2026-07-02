# Copy a logged-in Chrome profile to the Jenkins agent so CI skips Microsoft MFA.
# Run once on the agent machine while Chrome is closed.

param(
    [string]$SourceProfile = "$env:USERPROFILE\credaris-selenium-automation\.chrome-profile\credaris-automation",
    [string]$TargetProfile = "C:\jenkins-agent\.chrome-profile\credaris-automation"
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $SourceProfile)) {
    Write-Error @"
Source profile not found: $SourceProfile

Run bootstrap locally first:
  cd credaris-selenium-automation
  py -3 scripts\bootstrap_session.py
"@
}

Write-Host "Copying Chrome profile..."
Write-Host "  From: $SourceProfile"
Write-Host "  To:   $TargetProfile"

New-Item -ItemType Directory -Force -Path (Split-Path $TargetProfile -Parent) | Out-Null

# robocopy exit codes 0-7 are success
robocopy $SourceProfile $TargetProfile /MIR /R:1 /W:2 /NFL /NDL /NJH /NJS /nc /ns /np
if ($LASTEXITCODE -gt 7) {
    Write-Error "robocopy failed with exit code $LASTEXITCODE"
}

Write-Host ""
Write-Host "Done. Jenkins CI will use Scenario 2 (reuse.session=true) and skip MFA."
Write-Host "Run credaris-selenium-automation -> Build Now"
