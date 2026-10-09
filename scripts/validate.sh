#!/usr/bin/env bash
# Thin wrapper so validation can be invoked as `scripts/validate.sh ...`
# without callers needing to know it's a python script.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/validate.py" "$@"
