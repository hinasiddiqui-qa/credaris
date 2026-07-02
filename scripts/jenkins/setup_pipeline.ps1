# Create or update the Credaris Jenkins pipeline job via REST API.
#
# Usage (recommended: API token, not password):
#   $env:JENKINS_URL   = "http://localhost:10000"
#   $env:JENKINS_USER  = "hina.siddiqui@rolustech.com"
#   $env:JENKINS_TOKEN = "<your-jenkins-api-token>"
#   .\scripts\jenkins\setup_pipeline.ps1
#
# Create an API token in Jenkins:
#   Click your name (top right) → Security → Add new Token

param(
    [string]$JenkinsUrl = $env:JENKINS_URL,
    [string]$JenkinsUser = $env:JENKINS_USER,
    [string]$JenkinsToken = $env:JENKINS_TOKEN,
    [string]$JobName = "credaris-selenium-automation"
)

$ErrorActionPreference = "Stop"

if (-not $JenkinsUrl) { $JenkinsUrl = "http://localhost:10000" }
if (-not $JenkinsUser) {
    Write-Error "Set JENKINS_USER (your Jenkins login email)."
}
if (-not $JenkinsToken) {
    Write-Error "Set JENKINS_TOKEN (Jenkins API token — not your login password)."
}

$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$configPath = Join-Path $PSScriptRoot "credaris-pipeline-job.xml"
if (-not (Test-Path $configPath)) {
    Write-Error "Missing job config: $configPath"
}

$configXml = Get-Content $configPath -Raw -Encoding UTF8
$pair = "${JenkinsUser}:${JenkinsToken}"
$bytes = [System.Text.Encoding]::ASCII.GetBytes($pair)
$basic = [Convert]::ToBase64String($bytes)
$headers = @{
    Authorization = "Basic $basic"
    "Content-Type" = "application/xml; charset=UTF-8"
}

Write-Host "Checking Jenkins at $JenkinsUrl ..."
try {
    $info = Invoke-RestMethod -Uri "$JenkinsUrl/api/json?tree=mode,numExecutors" -Headers $headers -TimeoutSec 15
    Write-Host "Connected. Jenkins mode: $($info.mode)"
} catch {
    Write-Error "Cannot connect to Jenkins or authentication failed. Use an API token, not your web login password. Details: $($_.Exception.Message)"
}

$jobCheck = "$JenkinsUrl/job/$([uri]::EscapeDataString($JobName))/api/json"
$jobExists = $false
try {
    Invoke-RestMethod -Uri $jobCheck -Headers $headers -TimeoutSec 10 | Out-Null
    $jobExists = $true
} catch {
    if ($_.Exception.Response.StatusCode.value__ -ne 404) {
        throw
    }
}

if ($jobExists) {
    Write-Host "Updating existing job: $JobName"
    $url = "$JenkinsUrl/job/$([uri]::EscapeDataString($JobName))/config.xml"
    Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $configXml -TimeoutSec 30 | Out-Null
} else {
    Write-Host "Creating job: $JobName"
    $url = "$JenkinsUrl/createItem?name=$([uri]::EscapeDataString($JobName))"
    Invoke-RestMethod -Uri $url -Method Post -Headers $headers -Body $configXml -TimeoutSec 30 | Out-Null
}

Write-Host ""
Write-Host "Done. Open: $JenkinsUrl/job/$JobName/"
Write-Host "Next: configure SMTP under Manage Jenkins → System → Extended E-mail Notification"
