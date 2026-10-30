@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo Setting up Power BI Audit Center for first use...
  py -3 -m venv .venv
  if errorlevel 1 goto :error
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 goto :error
)

echo Starting Power BI Audit Center...
".venv\Scripts\python.exe" run_audit_center.py
exit /b 0

:error
echo.
echo Setup failed. Make sure Python 3 is installed and available via the Windows 'py' launcher.
pause
exit /b 1
