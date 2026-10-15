@echo off
REM ---------------------------------------------------------------
REM  Portable launcher (Windows)
REM  Keeps all data in a "dati" folder next to this file, so the
REM  whole thing can live on a USB stick and travel with the user.
REM ---------------------------------------------------------------
setlocal
set "HERE=%~dp0"
set "FAKTURA_DATA_DIR=%HERE%dati"
if not exist "%FAKTURA_DATA_DIR%" mkdir "%FAKTURA_DATA_DIR%"
start "" "%HERE%FakturaManager.exe"
endlocal
