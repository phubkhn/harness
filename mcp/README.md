# mcp

Where the `gft` plugin declares an MCP (Model Context Protocol) server — for example, an internal server that gives the agent extra tools (querying GFT's internal systems, calling a private API...), different from Claude Code's built-in tools (Read/Edit/Bash...).

**Current state: there is only a format example, no real MCP server is bundled yet.** This is the base harness — this directory exists so you have the right template ready when you need to add a real MCP server, not to use it right away.

## Where Claude Code reads MCP declarations (confirmed, not guessed)

There are 2 valid places, pick one:

1. **`.mcp.json` at the plugin root** (next to `.claude-plugin/`) — the recommended way, kept separate from `plugin.json`, the same way `hooks/hooks.json` is kept separate from `plugin.json`.
2. The `mcpServers` field declared directly in `.claude-plugin/plugin.json`.

This harness uses method 1 when there is a real server — consistent with the "one file per mechanism" convention already used for hooks.

## Schema

```json
{
  "mcpServers": {
    "server-name": {
      "command": "command-to-run",
      "args": ["arg1", "arg2"],
      "env": { "KEY": "value" }
    }
  }
}
```

- `command` — **required**.
- `args`, `env` — optional.
- If `type` is not declared, it defaults to stdio (the server runs as a child process, talking over stdin/stdout). There are also remote servers using `type: "http"` / `"sse"` / `"ws"` with `url`/`headers` — **the detailed schema for these types is not fully confirmed**, check again (`claude mcp --help` or the official docs) before using a remote type.
- The variables `${CLAUDE_PLUGIN_ROOT}` (the installed plugin's root path), `${CLAUDE_PLUGIN_DATA}`, `${CLAUDE_PROJECT_DIR}` can be used in `command`/`args`/`env` — use them to point to a script already inside the plugin without an absolute path.

## Example (see `mcp/example.mcp.json`)

That file is a **copy-and-fill template** (like `templates/*.yaml`), not an active file — the real `.mcp.json` at the plugin root **does not exist yet**, because there is no real server to bundle yet. If a `.mcp.json` with a fake command were placed at the root, Claude Code would try to start it as soon as the plugin loads and would report an error right away — so it is deliberately kept inactive until there is a real server.

## When there is a real MCP server to add

1. Copy `mcp/example.mcp.json` to `.mcp.json` at the harness root.
2. Edit `command`/`args`/`env` to point to the real server (use `${CLAUDE_PLUGIN_ROOT}` if the server lives inside this same repo).
3. Run `scripts/validate.sh` to check the JSON is valid (see `lint_mcp()` in `scripts/validate.py`).
4. Reinstall / open a new session for Claude Code to load the server.
