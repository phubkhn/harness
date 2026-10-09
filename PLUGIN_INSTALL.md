# Install the `gft` plugin (GFT Harness) in Claude Code

There are 2 ways to do this: **manual** (using the `/plugin` command inside a Claude Code session) or **automatic** (using `make install-plugin`, no interactive session needed). Both give the same result — pick whichever is easier for you.

Important: no matter which way you install it, the plugin points **directly** to this folder (it does not copy it). Any edit to `agents/`, `skills/`, `rules/`, `hooks/` here takes effect the next time the plugin loads, with no need to reinstall. You only need to **open a new Claude Code session** (or restart the current one) for it to read the files again.

## Method 1 — Manual, using the `/plugin` command (inside Claude Code)

```
/plugin marketplace add /Users/gft/Documents/AI/harness
/plugin install gft@gft-harness
```

The first command registers this folder as a "marketplace" named `gft-harness` (read from `.claude-plugin/marketplace.json`). The second command installs the plugin named `gft` that is declared inside it (from `.claude-plugin/plugin.json`). The short plugin name (`gft`) lets you call a skill/agent quickly using the prefix `gft:<name>` (for example `gft:task-spec`), instead of typing a longer name.

**To uninstall**: run `/plugin uninstall gft@gft-harness`, or `/plugin marketplace remove gft-harness` to also remove the marketplace.

## Method 2 — Automatic, using `make` (no session needed)

```bash
make install-plugin                                   # user scope (default) — applies to EVERY project on this machine
make install-plugin SCOPE=project TARGET=/path/to/proj # project scope — applies only to that one project
```

This command writes directly into Claude Code's `settings.json` (`extraKnownMarketplaces` + `enabledPlugins`) — the same mechanism `/plugin` uses, just without typing a command in a session. It is safe to run more than once (idempotent) and does not touch other fields already in your `settings.json`.

| Scope | File that gets edited | Applies to |
|---|---|---|
| `user` (default) | `~/.claude/settings.json` | Every project you open with Claude Code on this machine |
| `project` | `<TARGET>/.claude/settings.json` | Only the project at `TARGET` |

**To uninstall**: run `make uninstall-plugin` (with the same `SCOPE`/`TARGET` you used to install).

## Checking that it installed correctly

Go from the fastest check (just confirms it is *registered*) to the most certain one (confirms it is *really loaded*).

### 1. Fastest — no need to open Claude Code

```bash
cat ~/.claude/settings.json                    # user scope
cat /path/to/project/.claude/settings.json     # project scope
```
You should see `"gft-harness"` in `extraKnownMarketplaces` and `"gft@gft-harness": true` in `enabledPlugins`. **This only confirms registration** — whether Claude Code has really loaded it is checked in step 2.

### 2. Inside a Claude Code session (open a new one, or restart, to load it)

```
/plugin list --enabled       # lists the active plugins — you should see "gft"
/plugin marketplace list     # lists known marketplaces — you should see "gft-harness"
/plugin                      # or open the UI and check the "Installed" tab
```

### 3. Confirm the real content loaded (matches this harness's agents/skills)

- 4 agents (`solution-architect`, `developer`, `qa-engineer`, `code-reviewer`) appear in the list of available agents, or in the "Installed" tab of `/plugin`.
- The plugin's skills appear with the `gft:` prefix (the normal Claude Code convention for a plugin's skills — for example `gft:task-spec`, `gft:plan-review`).
- Try to `Edit` a file inside `rules/**` in this harness itself (if you have it open) — the hook should block it (see `hooks/README.md`).

If step 1 is correct but step 2/3 shows nothing: typing the command in the **old** session is not enough — you must open a **new** session (or run `/plugin marketplace update gft-harness` if you just edited the harness content) so Claude Code reads the files again. If it still does not show up, check that the scope you installed (`user` vs `project`) matches where you are opening Claude Code.
