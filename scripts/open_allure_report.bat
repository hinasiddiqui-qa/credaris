@echo off
setlocal

set "PROJECT_ROOT=%~dp0.."
set "RESULTS_DIR=%PROJECT_ROOT%reports\allure-results"

if not exist "%RESULTS_DIR%" (
    echo Allure results not found. Run pytest first to generate reports\allure-results
    exit /b 1
)

where allure.cmd >nul 2>&1
if %ERRORLEVEL%==0 (
    allure.cmd serve "%RESULTS_DIR%"
    exit /b %ERRORLEVEL%
)

where allure >nul 2>&1
if %ERRORLEVEL%==0 (
    allure serve "%RESULTS_DIR%"
    exit /b %ERRORLEVEL%
)

echo Allure CLI not found on PATH. Install it or use:
echo   C:\Users\hina.siddiqui\AppData\Local\allure\allure-2.32.2\bin\allure.bat serve "%RESULTS_DIR%"
exit /b 1
