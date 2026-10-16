#!/usr/bin/env bash
# Run every automated test. Execute from anywhere; the script finds the project root.
set -u
cd "$(dirname "$0")/.." || exit 1
export PROJECT_DIR="$PWD"

PY="python3"
[ -x ".venv/bin/python" ] && PY=".venv/bin/python"

failed=0
for t in test_core test_features test_flows test_gui; do
    echo "=================================================="
    echo ">>> $t"
    echo "=================================================="
    if $PY "tests/$t.py"; then
        :
    else
        echo "!!! $t FAILED"
        failed=1
    fi
done

echo
if [ "$failed" -eq 0 ]; then
    echo "ALL TEST FILES PASSED"
else
    echo "SOME TESTS FAILED"
fi
exit "$failed"
