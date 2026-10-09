#!/usr/bin/env bash
# Scans a project to see which stack rule in rules/stacks/ matches.
# Usage: scripts/detect_stack.sh <project-dir>
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/detect_stack.py" "$@"
