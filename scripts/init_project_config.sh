#!/usr/bin/env bash
# Scaffolds .gft/project.yaml for A PROJECT THAT USES the harness (not this harness itself).
# Usage: scripts/init_project_config.sh <project-path>
# Pre-fills 'stacks' using scripts/detect_stack.sh — you must still check it by
# hand before committing, because detect_stack.py is a heuristic (it can be wrong in a monorepo).
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PROJECT_DIR="${1:?usage: init_project_config.sh <project-path>}"
PROJECT_DIR="$(cd "$PROJECT_DIR" && pwd)"
OUT_DIR="$PROJECT_DIR/.gft"
OUT_FILE="$OUT_DIR/project.yaml"

if [ -e "$OUT_FILE" ]; then
  echo "$OUT_FILE already exists — not overwriting" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"
cp "$ROOT/templates/project-config.yaml" "$OUT_FILE"

echo "Detected stack (check this by hand before filling in 'stacks:'):"
"$SCRIPT_DIR/detect_stack.sh" "$PROJECT_DIR" || true

echo
echo "Created $OUT_FILE. Fill in project.id, project.owner_team, commands.test (required),"
echo "and stacks (based on the detection result above), then run:"
echo "  scripts/validate.sh project-config $OUT_FILE"
