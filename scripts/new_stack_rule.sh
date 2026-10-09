#!/usr/bin/env bash
# Scaffolds a new stack rule: scripts/new_stack_rule.sh <stack-name> "<description>"
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

NAME="${1:?usage: new_stack_rule.sh <stack-name> \"<description>\"}"
DESC="${2:-TODO: describe which stack this convention applies to}"
FILE="$ROOT/rules/stacks/$NAME.yaml"

if [ -e "$FILE" ]; then
  echo "rules/stacks/$NAME.yaml already exists" >&2
  exit 1
fi

mkdir -p "$ROOT/rules/stacks"

cat > "$FILE" <<EOF
id: stack-$NAME
version: 1.0.0
description: "$DESC"
severity: advisory
applies_to: [agent, skill]
applies_when:
  paths:
    - "TODO: **/marker-file-for-this-stack"
statements:
  - id: TODO
    text: TODO
EOF

echo "Created rules/stacks/$NAME.yaml. Edit applies_when.paths and statements, then run: scripts/validate.sh"