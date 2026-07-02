@echo off
setlocal
set "ROOT=%~dp0..\.."
cd /d "%ROOT%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0prepare_ci_session.ps1" -WorkspaceRoot "%ROOT%"
exit /b %ERRORLEVEL%
