@echo off
setlocal enabledelayedexpansion

set "ROOT=%~dp0..\.."
cd /d "%ROOT%"

where py >nul 2>&1
if errorlevel 1 (
    echo Python launcher 'py' was not found on this agent.
    echo Install Python from https://www.python.org/downloads/ and include the py launcher.
    exit /b 1
)

if not exist .venv\Scripts\python.exe (
    py -3 -m venv .venv
    if errorlevel 1 exit /b 1
)

call .venv\Scripts\activate.bat
py -3 -m pip install --upgrade pip
if errorlevel 1 exit /b 1
py -3 -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

call scripts\ci\prepare_ci_session.bat
if errorlevel 1 exit /b 1

py -3 scripts\ci\generate_config_from_env.py
if errorlevel 1 exit /b 1

if not exist reports mkdir reports
if not exist logs mkdir logs
if not exist screenshots mkdir screenshots

if not defined PYTEST_MARKER set "PYTEST_MARKER=smoke"
echo.
echo Starting Credaris tests (session login may take several minutes on first run)...
echo Approve Microsoft MFA on your phone if prompted.
echo.
py -3 -m pytest -m %PYTEST_MARKER% -v -s --log-cli-level=INFO %*
exit /b %ERRORLEVEL%
