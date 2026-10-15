#!/usr/bin/env bash
# Build a standalone macOS app bundle with PyInstaller (must run on macOS).
set -euo pipefail
cd "$(dirname "$0")/.."

PY="${PYTHON:-python3}"
if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
fi

"$PY" -m pip install --upgrade pip >/dev/null
"$PY" -m pip install -r requirements.txt pyinstaller

"$PY" -m PyInstaller --noconfirm --clean --onefile --windowed \
  --name "FakturaManager" \
  --icon "assets/icon.ico" \
  --collect-all customtkinter \
  --add-data "assets:assets" \
  main.py

echo
echo ">> Done. App bundle: $(pwd)/dist/FakturaManager.app"
