@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title VALORANT Scoreboard

echo =====================================
echo   VALORANT SCOREBOARD - START
echo =====================================

set "PYTHON_BOOTSTRAP="

where py >nul 2>&1
if not errorlevel 1 (
    py -3 -c "import sys" >nul 2>&1
    if not errorlevel 1 set "PYTHON_BOOTSTRAP=py -3"
)

if not defined PYTHON_BOOTSTRAP (
    where python >nul 2>&1
    if not errorlevel 1 (
        python -c "import sys" >nul 2>&1
        if not errorlevel 1 set "PYTHON_BOOTSTRAP=python"
    )
)

if not defined PYTHON_BOOTSTRAP goto python_missing

set "VENV_PYTHON=%~dp0.venv\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo [EINRICHTUNG] Lokale Python-Umgebung wird erstellt ...
    %PYTHON_BOOTSTRAP% -m venv "%~dp0.venv"
    if errorlevel 1 goto venv_failed
)

"%VENV_PYTHON%" -c "import flask, flask_cors" >nul 2>&1
if errorlevel 1 (
    echo [EINRICHTUNG] Benoetigte Pakete werden installiert ...
    "%VENV_PYTHON%" -m pip install -r "%~dp0requirements.txt"
    if errorlevel 1 goto dependencies_failed
)

"%VENV_PYTHON%" "%~dp0start_scoreboard.py" %*
set "START_EXIT=%ERRORLEVEL%"

if "%START_EXIT%"=="0" exit /b 0

echo.
echo [FEHLER] Das Scoreboard konnte nicht vollstaendig gestartet werden.
echo Bitte die Fehlermeldung oberhalb pruefen.
pause
exit /b %START_EXIT%

:python_missing
echo [FEHLER] Python 3 wurde nicht gefunden.
echo Bitte Python von https://www.python.org/downloads/ installieren
echo und dabei "Add Python to PATH" aktivieren.
pause
exit /b 1

:venv_failed
echo [FEHLER] Die lokale Python-Umgebung konnte nicht erstellt werden.
echo Falls bereits ein Ordner .venv existiert, diesen entfernen und erneut starten.
pause
exit /b 1

:dependencies_failed
echo [FEHLER] Die benoetigten Pakete konnten nicht installiert werden.
echo Bitte Internetverbindung und Python-Installation pruefen.
pause
exit /b 1
