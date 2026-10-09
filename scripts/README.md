# scripts

Plain bash plus a small python3 validator. No Java, no Gradle, no build step.

- `validate.sh` / `validate.py` — checks the structure of the whole harness (no arguments), or checks one filled-in artifact (`validate.sh <type> <file>`). It has no dependency other than python3 (it uses the included `minimal_yaml.py`, a minimal YAML reader — not a general YAML parser).
- `new_skill.sh`, `new_agent.sh` — scaffold a new skill/agent following the conventions in `skills/README.md` / `agents/README.md`.
- `resolve_plugin_root.sh` / `resolve_plugin_root.py` — find the `gft` plugin's real install path on disk, by reading Claude Code's runtime metadata (`~/.claude/plugins/installed_plugins.json`, `known_marketplaces.json`, fuzzy matched by name). This is needed for any path in `SKILL.md`/`agent.md` that points to `templates/`/`scripts/` (`${CLAUDE_PLUGIN_ROOT}` does **not** auto-expand in that content — it only expands in `hooks.json`/`mcp/*.json`). Usage: `scripts/resolve_plugin_root.sh [plugin-name] [marketplace-hint]`.
  - **A chicken-and-egg problem when the cwd is not the plugin root**: to call this script, the agent must already know the plugin root — the script cannot "know where it is" the way `hooks.json` can. If the agent is running in a different project (not the harness repo itself), bootstrap first with an inline command that only uses the fixed path `~/.claude/plugins/known_marketplaces.json` (always correct no matter the cwd):
    ```bash
    python3 -c "
    import json, os
    d = json.load(open(os.path.expanduser('~/.claude/plugins/known_marketplaces.json')))
    for k, v in d.items():
        if 'gft' in k.lower():
            print(v['installLocation']); break
    "
    ```
    Once you have `PLUGIN_ROOT` from the command above, call `"$PLUGIN_ROOT/scripts/resolve_plugin_root.sh"` (more complete: it also handles several installed copies, with fuzzy matching) or use `"$PLUGIN_ROOT/templates/..."`, `"$PLUGIN_ROOT/scripts/validate.sh"` directly.

Prefer `make <target>` (see the `Makefile` at the repo root) instead of calling these scripts directly.
