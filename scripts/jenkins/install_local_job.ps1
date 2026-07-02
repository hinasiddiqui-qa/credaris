# Registers the Credaris pipeline job with your local Jenkins (port 10000).
#
# Run AFTER you are logged into Jenkins as an admin.
# Then open Script Console and paste the reload command shown below.

$JenkinsHome = "C:\ProgramData\Jenkins\.jenkins"
$JobName = "credaris-selenium-automation"
$SourceXml = Join-Path $PSScriptRoot "credaris-pipeline-job.xml"
$JobDir = Join-Path $JenkinsHome "jobs\$JobName"
$TargetXml = Join-Path $JobDir "config.xml"
$NextBuild = Join-Path $JobDir "nextBuildNumber"

Write-Host "Installing Jenkins job: $JobName"
New-Item -ItemType Directory -Force -Path $JobDir | Out-Null
Copy-Item $SourceXml $TargetXml -Force
if (-not (Test-Path $NextBuild)) {
    Set-Content -Path $NextBuild -Value "1" -NoNewline
}
Write-Host "Job files written to: $JobDir"
Write-Host ""
Write-Host 'NEXT STEP - reload Jenkins:'
Write-Host '1. Open http://localhost:10000/script'
Write-Host '2. Paste and Run:'
Write-Host '   jenkins.model.Jenkins.getInstance().doReload()'
Write-Host ""
Write-Host 'Or: Manage Jenkins -> Reload Configuration from Disk'
Write-Host ""
Write-Host "Then open: http://localhost:10000/job/$JobName/"
Start-Process 'http://localhost:10000/script'
