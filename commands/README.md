# commands

Slash commands of the `gft` plugin — the entry point for users, called with `/gft:<name>` after the plugin is installed (see [PLUGIN_INSTALL.md](../PLUGIN_INSTALL.md)). Each file is a **thin** wrapper: it does not define its own process, it just points to the right phase in `registry/activation-rules.yaml` and lists the agent/skill that must be active — this avoids a second source of truth for "who runs in which phase".

| Command | Phase | Activates |
|---|---|---|
| `/gft:intake` | intake | `business-analyst`, `intake-request` |
| `/gft:spec` | spec | `solution-architect`, `business-analyst`, `feature-roadmap`, `task-spec`, `impact-analysis`, `adr` |
| `/gft:plan` | plan | `solution-architect`, `plan-review`, `test-plan`, `adr` |
| `/gft:execute` | execute | `developer` |
| `/gft:verify` | verify | `qa-engineer`, `verify-change`, `security-reviewer`, `security-review`, `ratchet-log` (if there is a failure) |
| `/gft:review` | review | `code-reviewer`, `review-change`, `security-reviewer`, `ratchet-log` (if there is a blocker), `pr-description` |
| `/gft:adr` | independent of phase | `adr` — use any time there is an important architecture decision |

File format: minimal YAML frontmatter with `description` (required, `lint_commands()` in `scripts/validate.py` checks it exists), and the optional `argument-hint`. The body uses `$ARGUMENTS` to take the input the user typed after the command name.

When you change `registry/activation-rules.yaml` (add or remove an agent or skill for a phase), remember to also check the matching commands here — `lint_commands()` only checks the frontmatter structure, it does **not** cross-check the command content against the registry.
