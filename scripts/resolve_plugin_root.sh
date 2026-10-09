#!/usr/bin/env bash
# A thin wrapper for resolve_plugin_root.py -- see that file's docstring for
# why this script is needed (${CLAUDE_PLUGIN_ROOT} does not auto-expand in
# SKILL.md/agent.md content, it only expands in hooks.json/mcp/*.json).
# Usage: scripts/resolve_plugin_root.sh [plugin-name] [marketplace-hint]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/resolve_plugin_root.py" "$@"
