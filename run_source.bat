@echo off
REM Quick run from source (development)
setlocal
cd /d "%~dp0"
set PY=python
if exist ".venv\Scripts\python.exe" set PY=.venv\Scripts\python.exe
%PY% -m pip install -r requirements.txt
%PY% main.py
