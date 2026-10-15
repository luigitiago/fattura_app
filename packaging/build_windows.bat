@echo off
REM Build a standalone Windows executable with PyInstaller.
REM The result is written to ..\dist\FakturaManager.exe
setlocal
cd /d "%~dp0\.."

set PY=python
if exist ".venv\Scripts\python.exe" set PY=.venv\Scripts\python.exe

echo ^>^> Installing dependencies
%PY% -m pip install --upgrade pip
%PY% -m pip install -r requirements.txt pyinstaller

echo ^>^> Building with PyInstaller
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed ^
  --name "FakturaManager" ^
  --icon "assets\icon.ico" ^
  --collect-all customtkinter ^
  --add-data "assets;assets" ^
  main.py

echo.
echo ^>^> Done. Executable: %CD%\dist\FakturaManager.exe
pause
