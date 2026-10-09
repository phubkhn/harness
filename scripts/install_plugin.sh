#!/usr/bin/env bash
# Registers gft-harness as a Claude Code plugin in settings.json (no need for
# an interactive /plugin session). See PLUGIN_INSTALL.md for both install
# methods (by hand + this script).
#
# Usage:
#   scripts/install_plugin.sh user                   # user scope:    ~/.claude/settings.json
#   scripts/install_plugin.sh project [target-dir]    # project scope: <target-dir|cwd>/.claude/settings.json
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

SCOPE="${1:?usage: install_plugin.sh <user|project> [target-project-dir]}"

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

mkdir -p "$(dirname "$SETTINGS_FILE")"
python3 "$SCRIPT_DIR/_merge_plugin_settings.py" "$SETTINGS_FILE" "$ROOT" enable

echo "Registered the 'gft' plugin (marketplace gft-harness pointing to $ROOT) in $SETTINGS_FILE."
echo "Open a new Claude Code session (or restart the current session) for the plugin to take effect."
