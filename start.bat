@echo off
echo ========================================================
echo Starting NutriTrack Web Application...
echo ========================================================

set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python312\python.exe"
if not exist "%PYTHON_EXE%" (
    set "PYTHON_EXE=python"
)

"%PYTHON_EXE%" app.py
pause
