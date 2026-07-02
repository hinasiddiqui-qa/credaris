@echo off
setlocal

set "ROOT=%~dp0..\.."
cd /d "%ROOT%"

set "RESULTS_DIR=reports\allure-results"
set "REPORT_DIR=reports\allure-report"
set "ZIP_PATH=reports\allure-report.zip"

if not exist "%RESULTS_DIR%" (
    echo No Allure results found in %RESULTS_DIR%
    exit /b 0
)

where allure >nul 2>&1
if errorlevel 1 (
    if exist "C:\jenkins-agent\tools\org.allurereport.jenkins.tools.AllureCommandlineInstallation\Allure\bin\allure.bat" (
        set "ALLURE_BIN=C:\jenkins-agent\tools\org.allurereport.jenkins.tools.AllureCommandlineInstallation\Allure\bin\allure.bat"
    ) else (
        echo Allure CLI not found on PATH — Jenkins Allure plugin will still publish results.
        exit /b 0
    )
) else (
    set "ALLURE_BIN=allure"
)

"%ALLURE_BIN%" generate "%RESULTS_DIR%" -o "%REPORT_DIR%" --clean
if errorlevel 1 exit /b 1

if exist "%ZIP_PATH%" del /f /q "%ZIP_PATH%"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "if (Test-Path '%REPORT_DIR%') { Compress-Archive -Path '%REPORT_DIR%\*' -DestinationPath '%ZIP_PATH%' -Force; Write-Host 'Allure archive ready: %ZIP_PATH%' }"

exit /b 0
