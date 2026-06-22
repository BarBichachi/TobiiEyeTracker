@echo off
rem Launches the TobiiEyeTracker app using the project venv if present.
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" main.py
) else (
    echo [run] .venv not found, falling back to system Python
    python main.py
)

endlocal
