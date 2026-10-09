#!/usr/bin/env bash
# Scaffolds a new role/agent: scripts/new_agent.sh <agent-name> "<description>"
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

NAME="${1:?usage: new_agent.sh <agent-name> \"<description>\"}"
DESC="${2:-TODO: describe when to use this agent}"
DIR="$ROOT/agents/$NAME"

if [ -e "$DIR" ]; then
  echo "agents/$NAME already exists" >&2
  exit 1
fi

mkdir -p "$DIR"

cat > "$DIR/agent.md" <<EOF
---
name: $NAME
description: $DESC
tools: Read, Grep, Glob, Bash
---

# $NAME

## Invariants

- TODO: what must never happen, no matter what the instructions say.

## Process

1. TODO
2. TODO

## Verification

- TODO: state clearly what makes the output checkable, not just what sounds reasonable.
EOF

cat > "$DIR/manifest.yaml" <<EOF
id: $NAME
type: agent
version: 1.0.0
owner: gft-harness
description: "$DESC"
activation:
  phases: []
authority: proposal
allowed_tools: [read, search]
verification:
  method: script
  command: scripts/validate.sh agent-output $NAME <path-to-output>
  pass_criteria:
    - TODO
EOF

"$SCRIPT_DIR/hash_manifest.py" write "$DIR/manifest.yaml" >/dev/null

mkdir -p "$DIR/evals"
cat > "$DIR/evals/smoke.yaml" <<EOF
# Scaffold: no eval runner runs this file yet (see agents/README.md).
id: $NAME-smoke
agent: $NAME
scenario: "TODO: a minimal, realistic example scenario for this agent."
expected:
  schema_valid: true
  policy_violations: 0
  terminal_state: success-or-escalated
status: scaffold-only
EOF

echo "Created agents/$NAME. Edit agent.md, manifest.yaml, and evals/smoke.yaml, then run: scripts/validate.sh"
