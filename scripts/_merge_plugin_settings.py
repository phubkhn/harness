#!/usr/bin/env python3
"""Merges/removes the gft plugin + marketplace registration in a Claude Code
settings.json (project or user scope), without touching other fields
already in the file.

The real Claude Code schema (confirmed by reading an actual settings.json
with real content, not guessed):

  "extraKnownMarketplaces": {
    "<marketplace-name>": {
      "source": {"source": "file", "path": "/path/to/marketplace.json"}
    }
  },
  "enabledPlugins": {
    "<plugin-name>@<marketplace-name>": true
  }

extraKnownMarketplaces is an OBJECT keyed by marketplace name, not an array.

Usage: _merge_plugin_settings.py <settings-file> <harness-root> <enable|disable>
"""
import json
import sys
from pathlib import Path

MARKETPLACE_NAME = "gft-harness"
PLUGIN_KEY = f"gft@{MARKETPLACE_NAME}"


def main():
    if len(sys.argv) != 4:
        print("usage: _merge_plugin_settings.py <settings-file> <harness-root> <enable|disable>", file=sys.stderr)
        sys.exit(1)

    settings_file = Path(sys.argv[1])
    harness_root = Path(sys.argv[2])
    action = sys.argv[3]

    data = {}
    if settings_file.exists():
        text = settings_file.read_text().strip()
        if text:
            data = json.loads(text)

    marketplaces = data.get("extraKnownMarketplaces")
    if marketplaces is None:
        marketplaces = {}
        data["extraKnownMarketplaces"] = marketplaces
    elif not isinstance(marketplaces, dict):
        print(
            f"ERROR: 'extraKnownMarketplaces' in {settings_file} is not an object as expected "
            f"(it is {type(marketplaces).__name__}). Stopping, not auto-fixing it to avoid breaking the file — "
            "please check it by hand.",
            file=sys.stderr,
        )
        sys.exit(1)

    if action == "enable":
        marketplace_json = str(harness_root / ".claude-plugin" / "marketplace.json")
        marketplaces[MARKETPLACE_NAME] = {
            "source": {"source": "file", "path": marketplace_json}
        }
        enabled = data.setdefault("enabledPlugins", {})
        enabled[PLUGIN_KEY] = True
    elif action == "disable":
        marketplaces.pop(MARKETPLACE_NAME, None)
        if not marketplaces:
            data.pop("extraKnownMarketplaces", None)
        enabled = data.get("enabledPlugins", {})
        enabled.pop(PLUGIN_KEY, None)
        if "enabledPlugins" in data and not data["enabledPlugins"]:
            data.pop("enabledPlugins", None)
    else:
        print(f"unknown action: {action}", file=sys.stderr)
        sys.exit(1)

    settings_file.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
