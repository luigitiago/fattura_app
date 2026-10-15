#!/usr/bin/env bash
# ---------------------------------------------------------------
#  Portable launcher (Linux)
#  Keeps all data in a "dati" folder next to this script, so the
#  whole thing can live on a USB stick and travel with the user.
# ---------------------------------------------------------------
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
export FAKTURA_DATA_DIR="$HERE/dati"
mkdir -p "$FAKTURA_DATA_DIR"
exec "$HERE/FakturaManager"
