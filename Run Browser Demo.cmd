@echo off
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 goto python
py -3 scripts/serve_browser.py
goto done
:python
python scripts/serve_browser.py
:done
if errorlevel 1 (
  echo Install Python 3.11 or newer and run this file again.
  pause
)
