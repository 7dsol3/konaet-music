@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" py -3 -m venv .venv
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements-runtime.lock --disable-pip-version-check
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install --no-deps --no-build-isolation -e . --disable-pip-version-check
if errorlevel 1 goto failed
set EMPORIO_PROVIDER=local
echo Open http://127.0.0.1:8000 in your browser. No language model is used in this mode.
".venv\Scripts\python.exe" -m emporio serve
exit /b 0
:failed
echo Installation failed. Read the error above.
pause
exit /b 1
