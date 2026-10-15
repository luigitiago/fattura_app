#!/usr/bin/env bash
# Build a standalone Linux executable with PyInstaller.
# The result is written to ../dist/FakturaManager
set -euo pipefail
cd "$(dirname "$0")/.."

PY="${PYTHON:-python3}"
if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
fi

echo ">> Installing dependencies"
"$PY" -m pip install --upgrade pip >/dev/null
"$PY" -m pip install -r requirements.txt pyinstaller

echo ">> Building with PyInstaller"
"$PY" -m PyInstaller --noconfirm --clean --onefile --windowed \
  --name "FakturaManager" \
  --icon "assets/icon.png" \
  --collect-all customtkinter \
  --add-data "assets:assets" \
  main.py

echo
echo ">> Done. Executable: $(pwd)/dist/FakturaManager"
