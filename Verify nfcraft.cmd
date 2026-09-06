@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" scripts\verify.py
) else (
  where py >nul 2>nul
  if errorlevel 1 (python scripts\verify.py) else (py -3 scripts\verify.py)
)
pause
endlocal
