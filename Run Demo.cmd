@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements-runtime.lock --disable-pip-version-check
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install --no-deps --no-build-isolation -e . --disable-pip-version-check
if errorlevel 1 goto failed
if not exist "var\model\manifest.json" ".venv\Scripts\python.exe" scripts\local_model.py setup
if errorlevel 1 goto failed
echo Open http://127.0.0.1:8000 in your browser. English is the default language.
".venv\Scripts\python.exe" scripts\local_model.py app
if errorlevel 1 goto failed
exit /b 0
:failed
echo The demo could not start. Read the error above and the README troubleshooting section.
pause
exit /b 1
