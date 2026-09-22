@echo off
rem Version 0.6.1: Bedienfeld mit lokaler Python-Umgebung starten.
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
  echo Bitte zuerst Einrichtung.ps1 ausfuehren. Siehe README.md.
  pause
  exit /b 1
)
start "SolarTracker" ".venv\Scripts\pythonw.exe" "bedienfeld_qt.py"
