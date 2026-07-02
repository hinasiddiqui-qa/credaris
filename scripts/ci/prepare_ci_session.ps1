# Prepare authenticated session artifacts for Jenkins CI (skip MFA when possible).

param(
    [string]$SourceProject = "$env:USERPROFILE\credaris-selenium-automation",
    [string]$AgentProfile = "C:\jenkins-agent\.chrome-profile\credaris-automation",
    [string]$WorkspaceRoot = (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent)
)

$ErrorActionPreference = "Stop"

$sourceProfile = Join-Path $SourceProject ".chrome-profile\credaris-automation"
$sourceCookies = Join-Path $SourceProject "sessions\credaris_cookies.json"
$workspaceSessions = Join-Path $WorkspaceRoot "sessions"
$workspaceCookies = Join-Path $workspaceSessions "credaris_cookies.json"
$agentSessions = "C:\jenkins-agent\sessions"
$agentCookies = Join-Path $agentSessions "credaris_cookies.json"

function Sync-Profile {
    if (-not (Test-Path (Join-Path $sourceProfile "Default"))) {
        Write-Host "Local Chrome profile not found — run: py -3 scripts\bootstrap_session.py"
        return
    }
    if (-not (Test-Path (Join-Path $AgentProfile "Default"))) {
        Write-Host "Syncing Chrome profile to agent..."
        & (Join-Path $PSScriptRoot "sync_chrome_profile_to_agent.ps1") `
            -SourceProfile $sourceProfile `
            -TargetProfile $AgentProfile
    } else {
        Write-Host "Agent Chrome profile already present."
    }
}

function Sync-Cookies {
    if (-not (Test-Path $sourceCookies)) {
        Write-Host "Local cookie file not found — profile-only session reuse."
        return
    }
    New-Item -ItemType Directory -Force -Path $workspaceSessions | Out-Null
    New-Item -ItemType Directory -Force -Path $agentSessions | Out-Null
    if ($sourceCookies -ne $workspaceCookies) {
        Copy-Item $sourceCookies $workspaceCookies -Force
    }
    Copy-Item $sourceCookies $agentCookies -Force
    Write-Host "Session cookies copied to workspace and agent."
}

function Clear-ProfileLocks {
    foreach ($name in @("SingletonLock", "SingletonCookie", "SingletonSocket")) {
        $lock = Join-Path $AgentProfile $name
        if (Test-Path $lock) {
            Remove-Item $lock -Force -ErrorAction SilentlyContinue
        }
    }
}

Write-Host "=== Credaris CI session prepare ==="
& Sync-Profile
& Sync-Cookies
& Clear-ProfileLocks

$profileOk = Test-Path (Join-Path $AgentProfile "Default")
$cookiesOk = (Test-Path $workspaceCookies) -or $profileOk
Write-Host "Agent profile ready: $profileOk"
Write-Host "Workspace cookies ready: $(Test-Path $workspaceCookies)"
if (-not $profileOk -and -not (Test-Path $workspaceCookies)) {
    Write-Warning "No session artifacts - CI will require Microsoft MFA approval on phone."
}
