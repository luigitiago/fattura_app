#!/usr/bin/env bash
# Quick run from source (development) – creates a venv if needed.
set -euo pipefail
cd "$(dirname "$0")"

if [ ! -x ".venv/bin/python" ]; then
  echo ">> Creating virtual environment"
  python3 -m venv .venv || python3 -m virtualenv .venv
  .venv/bin/python -m pip install --upgrade pip >/dev/null
  .venv/bin/python -m pip install -r requirements.txt
fi

exec .venv/bin/python main.py
