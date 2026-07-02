@echo off
setlocal enabledelayedexpansion

set "ROOT=%~dp0..\.."
cd /d "%ROOT%"

if not exist .venv\Scripts\python.exe (
    python -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

python scripts\ci\generate_config_from_env.py
if errorlevel 1 exit /b 1

if not exist reports mkdir reports
if not exist logs mkdir logs
if not exist screenshots mkdir screenshots

if not defined PYTEST_MARKER set "PYTEST_MARKER=smoke"
pytest -m %PYTEST_MARKER% -v %*
