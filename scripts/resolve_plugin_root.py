#!/usr/bin/env python3
"""Finds the real install path (on disk) of a Claude Code plugin by name.

Why this script is needed: the ${CLAUDE_PLUGIN_ROOT} variable is only
substituted by the Claude Code runtime for structured fields in
hooks.json/mcp/*.json (command/args/env) when it spawns a subprocess for
those files. It does NOT exist as a normal persistent environment variable,
and it does NOT auto-resolve when it appears as plain text in
SKILL.md/agent.md/manifest.yaml -- that content is just prose that the agent
reads and then calls Read/Bash with, so the agent must work out the
absolute path itself first.

Usage:
  scripts/resolve_plugin_root.py [plugin-name] [marketplace-hint]

  plugin-name       default: gft
  marketplace-hint  optional substring to tell apart the same plugin name
                     installed from several different marketplaces

Resolve order (stops at the first step that gives a directory that really exists):
  1. ~/.claude/plugins/installed_plugins.json -- exact match on the key
     "name@marketplace", or a fuzzy, case-insensitive substring match on
     the plugin name part if there is no exact match.
  2. ~/.claude/plugins/known_marketplaces.json -- fuzzy match the
     marketplace name, then read that marketplace's own marketplace.json
     to get the plugin's "source" field (relative to the marketplace's
     installLocation).
  3. Walk up from the current working directory to its parent directories,
     looking for a .claude-plugin/plugin.json whose "name" matches (this
     catches local dev that was never registered as a marketplace).

Prints the absolute path to stdout and exits 0 if found; prints an error to
stderr and exits 1 if nothing is found.
"""
import json
import os
import sys

PLUGINS_DIR = os.path.expanduser("~/.claude/plugins")


def _load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, NotADirectoryError):
        return None


def _from_installed_plugins(name, marketplace_hint):
    data = _load_json(os.path.join(PLUGINS_DIR, "installed_plugins.json"))
    if not data:
        return None
    plugins = data.get("plugins", {})

    def candidates():
        for key, records in plugins.items():
            plugin_name, _, marketplace = key.partition("@")
            yield plugin_name, marketplace, records

    def matches(exact):
        for plugin_name, marketplace, records in candidates():
            name_ok = plugin_name == name if exact else name.lower() in plugin_name.lower()
            if name_ok and (not marketplace_hint or marketplace_hint.lower() in marketplace.lower()):
                yield records

    pool = list(matches(exact=True)) or list(matches(exact=False))
    if not pool:
        return None

    best = None
    for records in pool:
        for record in records:
            if best is None:
                best = record
            elif record.get("scope") == "project" and best.get("scope") != "project":
                best = record
            elif record.get("lastUpdated", "") > best.get("lastUpdated", ""):
                best = record
    return best.get("installPath") if best else None


def _from_known_marketplaces(name, marketplace_hint):
    data = _load_json(os.path.join(PLUGINS_DIR, "known_marketplaces.json"))
    if not data:
        return None

    hint = marketplace_hint or name
    matched = None
    for mp_name in data:
        if hint.lower() in mp_name.lower():
            matched = mp_name
            break
    if not matched:
        return None

    install_location = data[matched].get("installLocation")
    if not install_location:
        return None

    marketplace_manifest = _load_json(os.path.join(install_location, ".claude-plugin", "marketplace.json"))
    source = "."
    if marketplace_manifest:
        for plugin in marketplace_manifest.get("plugins", []):
            if plugin.get("name") == name:
                source = plugin.get("source", ".")
                break
    return os.path.normpath(os.path.join(install_location, source))


def _from_cwd_walk(name):
    current = os.getcwd()
    while True:
        manifest = _load_json(os.path.join(current, ".claude-plugin", "plugin.json"))
        if manifest and manifest.get("name") == name:
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return None
        current = parent


def resolve(name, marketplace_hint=None):
    for resolver in (
        lambda: _from_installed_plugins(name, marketplace_hint),
        lambda: _from_known_marketplaces(name, marketplace_hint),
        lambda: _from_cwd_walk(name),
    ):
        result = resolver()
        if result and os.path.isdir(result):
            return result
    return None


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "gft"
    marketplace_hint = sys.argv[2] if len(sys.argv) > 2 else None

    root = resolve(name, marketplace_hint)
    if not root:
        print(
            f"Could not find plugin '{name}' via {PLUGINS_DIR}/installed_plugins.json, "
            f"{PLUGINS_DIR}/known_marketplaces.json, or by walking up from "
            "the current directory looking for .claude-plugin/plugin.json.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(root)


if __name__ == "__main__":
    main()
