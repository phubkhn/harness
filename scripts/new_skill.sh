#!/usr/bin/env bash
# Scaffolds a new skill: scripts/new_skill.sh <skill-name> "<description>"
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

NAME="${1:?usage: new_skill.sh <skill-name> \"<description>\"}"
DESC="${2:-TODO: describe this skill}"
DIR="$ROOT/skills/$NAME"

if [ -e "$DIR" ]; then
  echo "skills/$NAME already exists" >&2
  exit 1
fi

mkdir -p "$DIR"

cat > "$DIR/SKILL.md" <<EOF
---
name: $NAME
description: $DESC
---

# $NAME

## Process

1. TODO
2. TODO

## Verification

- TODO: state clearly what makes this skill's output checkable, not just what sounds reasonable.
EOF

cat > "$DIR/manifest.yaml" <<EOF
id: $NAME
type: skill
version: 1.0.0
owner: gft-harness
description: "$DESC"
activation:
  phases: []
authority: proposal
verification:
  method: script
  command: scripts/validate.sh $NAME <path-to-output>
  pass_criteria:
    - TODO
EOF

"$SCRIPT_DIR/hash_manifest.py" write "$DIR/manifest.yaml" >/dev/null

mkdir -p "$DIR/evals"
cat > "$DIR/evals/smoke.yaml" <<EOF
# Scaffold: no eval runner runs this file yet (see skills/README.md).
id: $NAME-smoke
skill: $NAME
scenario: "TODO: a minimal, realistic example scenario for this skill."
expected:
  schema_valid: true
  policy_violations: 0
status: scaffold-only
EOF

echo "Created skills/$NAME. Edit SKILL.md, manifest.yaml, and evals/smoke.yaml, then run: scripts/validate.sh"
