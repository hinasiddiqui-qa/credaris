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

set "ALLURE_TOOL_HOME=C:\jenkins-agent\tools\org.allurereport.jenkins.tools.AllureCommandlineInstallation\Allure"

where allure >nul 2>&1
if errorlevel 1 (
    if exist "%ALLURE_TOOL_HOME%\bin\allure.bat" (
        set "ALLURE_BIN=%ALLURE_TOOL_HOME%\bin\allure.bat"
        set "APP_HOME=%ALLURE_TOOL_HOME%"
    ) else (
        echo Allure CLI not found on PATH — Jenkins Allure plugin will still publish results.
        exit /b 0
    )
) else (
    set "ALLURE_BIN=allure"
)

rem Work around a known Allure Commandline 2.40+ Windows launcher bug: allure.bat
rem does "endlocal & java ..." which clears APP_HOME right before starting Java,
rem so the backend silently skips generating data/behaviors.json and
rem data/packages.json (Categories/Suites still work). Pre-setting APP_HOME here
rem survives that endlocal, since it restores the OUTER scope's value instead of
rem clearing it. Upstream bug: allure-framework/allure2#3351 (fixed in #3353).
"%ALLURE_BIN%" generate "%RESULTS_DIR%" -o "%REPORT_DIR%" --clean
if errorlevel 1 exit /b 1

if exist "%ZIP_PATH%" del /f /q "%ZIP_PATH%"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "if (Test-Path '%REPORT_DIR%') { Compress-Archive -Path '%REPORT_DIR%\*' -DestinationPath '%ZIP_PATH%' -Force; Write-Host 'Allure archive ready: %ZIP_PATH%' }"

exit /b 0
