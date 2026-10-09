#!/usr/bin/env bash
# Removes the gft-harness registration from settings.json (the reverse of install_plugin.sh).
# Usage:
#   scripts/uninstall_plugin.sh user
#   scripts/uninstall_plugin.sh project [target-dir]
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SCOPE="${1:?usage: uninstall_plugin.sh <user|project> [target-project-dir]}"

case "$SCOPE" in
  user)
    SETTINGS_FILE="$HOME/.claude/settings.json"
    ;;
  project)
    TARGET_DIR="${2:-$(pwd)}"
    SETTINGS_FILE="$TARGET_DIR/.claude/settings.json"
    ;;
  *)
    echo "scope must be 'user' or 'project', got '$SCOPE'" >&2
    exit 1
    ;;
esac

if [ ! -f "$SETTINGS_FILE" ]; then
  echo "Could not find $SETTINGS_FILE — it may not be installed." >&2
  exit 0
fi

python3 "$SCRIPT_DIR/_merge_plugin_settings.py" "$SETTINGS_FILE" "$ROOT" disable
echo "Removed the 'gft' plugin from $SETTINGS_FILE."