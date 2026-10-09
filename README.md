# GFT Harness

GFT Harness is an AI-SDLC base system: role-based agents, reusable skills, rules that can be enforced, pre-filled templates, and a policy enforcement system. Every step has a clear definition, so the output can be checked, not just judged by feeling. The runtime with full support now is Claude Code (packaged as a plugin). The core content — rules, skills, templates, registry — is designed to be runtime-neutral. This way, we can later add support for other LLMs or CLIs without rewriting everything.

The project does not use Java, Gradle, or a build step. The content is yaml/markdown. The only real code is a few bash and python3 scripts.

## Directory structure

```
agents/     role-based agents (solution-architect, developer, qa-engineer, code-reviewer, security-reviewer, business-analyst)
skills/     shared process steps for every role (task-spec, plan-review, verify-change, review-change, adr, security-review, test-plan, impact-analysis, pr-description, intake-request, ratchet-log, feature-roadmap, systematic-debugging, using-gft)
commands/   plugin slash commands (/gft:spec, /gft:plan, /gft:execute, /gft:verify, /gft:review, /gft:adr) — thin wrappers that point to registry/activation-rules.yaml
rules/      fixed yaml rules that every agent/skill/hook must follow (includes rules/stacks/ for tech-stack conventions)
registry/   the coordination layer: which agents/skills exist, and which phase activates which one
templates/  pre-filled yaml templates for artifacts that skills/agents create (includes project-config.yaml, ratchet-log.yaml — templates that belong to a project using the harness, not to one specific phase)
hooks/      rule enforcement at runtime (currently built for Claude Code)
mcp/        MCP server definitions the plugin carries (currently just a format example, no real server bundled yet)
scripts/    check and scaffold scripts (bash + python3, no external library dependencies)
.github/    CI (the validate.yml workflow runs `make validate` on every PR)
CODEOWNERS  requires review for protected paths, matching rules/protected-paths.yaml one to one
```

Each folder — `agents/`, `skills/`, `commands/`, `rules/`, `registry/`, `templates/`, `hooks/`, `mcp/`, `scripts/` — has its own `README.md` that explains that folder's own conventions.

## CI and path protection (governance)

The local hook (`hooks/check-protected-paths`) only gives fast feedback inside one Claude Code session — it is **not** the final authority, because it can be skipped if a change comes from outside that session. `.github/workflows/validate.yml` runs `make validate` on every PR and on every push to `main`. After you push this repo to GitHub, go to **Settings > Branches** and turn on the required status check named `validate` for the `main` branch. That step cannot be done through a file — you must turn it on by hand.

The `CODEOWNERS` file at the repo root requires review for the exact set of paths listed in `rules/protected-paths.yaml` (the `paths` field). These two files must match. The function `lint_codeowners()` in `scripts/validate.py` checks the other direction — it finds any protected path that is missing its matching CODEOWNERS line — every time `make validate` runs. So if you edit protected-paths.yaml, you must always edit CODEOWNERS at the same time.

## Settings for one project that uses the harness

`rules/context-hierarchy.yaml` defines level 2 as `project-config` — rules that belong to one project only (different from the harness's shared rules at level 1). This is stored in `.gft/project.yaml` **inside that project's own repo** (not inside this harness):

```bash
make init-project TARGET=/path/to/project   # scaffold the file, pre-fill 'stacks' using scripts/detect_stack.sh
make check KIND=project-config FILE=/path/to/project/.gft/project.yaml
```

This file can only **add** rules (`protected_paths_extra`, `escalate_paths_extra`). It can never loosen a harness rule — `validate_project_config` fails right away if it sees a field named `*_override`. `hooks/check_protected_paths.py` reads the union of `rules/protected-paths.yaml` and this file when it checks Edit/Write actions.

## Lifecycle

```
intake (intake-request / business-analyst)
  -> spec (task-spec, impact-analysis, adr / business-analyst, solution-architect)
  -> plan (plan-review, adr, test-plan)
  -> execute (developer)
  -> verify (verify-change / qa-engineer, security-review / security-reviewer)
  -> review (review-change / code-reviewer, pr-description, security-reviewer)
```

`systematic-debugging` does not sit at a fixed spot in this chain. It is active in both `execute` and `verify`. `developer`/`qa-engineer` calls it when they hit a bug or a failing test with no clear cause yet. `using-gft` also does not belong to one phase. The `SessionStart` hook injects it at the start of every session, so it can check `registry/activation-rules.yaml` and pick the right entry point in the chain above (see `hooks/README.md`).

`rules/context-hierarchy.yaml` sets the order that wins in a conflict: harness rules > project config > task spec > code/context > the current run. The mapping from phase to agent/skill lives in `registry/activation-rules.yaml` — do not copy that table here when you edit it.

## Input/output for each agent and skill

The table below answers "what goes in, what comes out" for each item. Use it to get a quick understanding before you open the full `agent.md`/`SKILL.md` files. The **Verify with** column is the `scripts/validate.sh` subcommand that checks that output.

### Agents

| Agent | Phase | Input | Output | Verify with |
|---|---|---|---|---|
| `solution-architect` | spec, plan | raw requirement, constraints of the current system | architecture proposal/decision, with trade-offs and downsides | `agent-output solution-architect` |
| `developer` | execute | approved task-spec, plan | diff inside `allowed_scope`, list of changed paths + commands run | `agent-output developer` |
| `qa-engineer` | verify | implemented code, task-spec | `verification-result.yaml`: exit code for each command, pass/fail for each acceptance criterion | `agent-output qa-engineer` (matching skill: `verify-change`) |
| `code-reviewer` | review | diff, task-spec, verification-result | `review-result.yaml`: findings by severity + approve/blocker verdict | `agent-output code-reviewer` (matching skill: `review-change`) |
| `security-reviewer` | verify, review | diff, task-spec, verification-result | `review-result.yaml`: security findings (authn/authz, secrets, input validation, PII) + approve/blocker verdict | `agent-output security-reviewer` (matching skill: `security-review`) |
| `business-analyst` | intake, spec | raw requirement/ticket | `intake-brief.yaml`: business goal, stakeholder, success metric, open question | `agent-output business-analyst` (matching skill: `intake-request`) |

### Skills

| Skill | Phase | Input | Output (template) | Verify with |
|---|---|---|---|---|
| `intake-request` | intake | raw requirement/ticket | `intake-brief.yaml`: problem statement, business goal, stakeholder, success metric, open question | `intake-request` |
| `task-spec` | spec | raw requirement | `task-spec.yaml`: outcome, acceptance criteria with ids, allowed/protected scope, risk tier | `task-spec` |
| `impact-analysis` | spec | a change expected to touch many modules/services | `impact-analysis.yaml`: affected components + impact level, downstream consumers, risk tier | `impact-analysis` |
| `adr` | spec, plan | an architecture problem with more than one valid solution | `adr.yaml`: options with downsides, decision, consequences | `adr` |
| `plan-review` | plan | task-spec, proposed plan | `plan-review-result.yaml`: approved/changes-requested/escalate verdict | `plan-review` |
| `test-plan` | plan | acceptance criteria from the task-spec | `test-plan.yaml`: test cases mapped to each AC, including negative-path cases | `test-plan` |
| `verify-change` | verify | implemented code, task-spec | `verification-result.yaml`: exit code + pass/fail for each AC | `verify-change` |
| `security-review` | verify | diff, task-spec, verification-result | `review-result.yaml` (uses the same format as review-change) | `review-change` |
| `review-change` | review | diff, task-spec, verification-result | `review-result.yaml`: findings + verdict | `review-change` |
| `pr-description` | review | task-spec, a passed verification-result, an approved review-result | `pr-description.yaml`: PR description with traceability to the task_id | `pr-description` |
| `ratchet-log` | verify, review | a verification-result with a failed AC, or a review-result with a blocker verdict | a new entry in the project's `.gft/ratchet-log.yaml` + `ratchet_ref` filled back in — required, not optional | `ratchet-log` |
| `systematic-debugging` | execute, verify | a bug/failing test with no clear cause during implementation or verification | produces no artifact — the root cause and fix are written into the report of the agent that called this skill | none (checked indirectly through `testing-quality-gate`/`evidence-requirements` on the final fix) |
| `using-gft` | every phase (session-wide) | a new requirement, unclear which skill/agent to use | produces no artifact — decides which agent/skill to use based on `registry/activation-rules.yaml` | none (checked indirectly — `make validate` confirms the registry is consistent) |

## Current runtime: Claude Code

This harness is now fully built for Claude Code, packaged as a plugin (`.claude-plugin/plugin.json`). For install steps — both manual (`/plugin` inside a session) and automatic (`make install-plugin`) — see [PLUGIN_INSTALL.md](PLUGIN_INSTALL.md). If you only want to use the hooks in a project without installing this harness as a plugin, copy the content of `hooks/hooks.json` into that project's `.claude/settings.json`.

The parts tied specifically to Claude Code are just the frontmatter of `SKILL.md`/`agent.md` files and all of `hooks/`. Everything else — `rules/`, `registry/`, `templates/`, and the Procedure/Invariants/Verification content inside each skill/agent — is runtime-neutral content. This is the part that will be reused when the harness adds support for other runtimes/LLMs. The Claude Code–specific part will be split into its own adapter layer when needed, the same way many other multi-runtime systems are organized.

## Commands

Each skill/agent also has an `evals/smoke.yaml` file, which declares one minimal sample scenario. Right now this is just a **scaffold** — there is no real eval runner yet (see `skills/README.md` / `agents/README.md`). `make validate` only checks that the file exists and has the required fields.

```bash
make validate                              # check the structure of the whole harness (includes registry cross-check, evals scaffold)
make check KIND=task-spec FILE=path.yaml   # check one filled-in artifact
make new-skill NAME=my-skill DESC="..."    # scaffold a new skill
make new-agent NAME=my-role DESC="..."     # scaffold a new role/agent
make list                                  # list current skills/agents/rules/templates

scripts/new_stack_rule.sh <stack-name> "<description>"   # scaffold a new stack rule in rules/stacks/
scripts/detect_stack.sh <project-path>                    # scan a project, print which stack rule matches (see rules/stacks/README.md)
make init-project TARGET=<project-path>                   # scaffold .gft/project.yaml for that project
make hash-manifests                                       # recompute content_hash for every manifest.yaml after a manual edit
```

When you add a new skill/agent, you must register it in `registry/capability-catalog.yaml` and add a matching activation rule in `registry/activation-rules.yaml`. `make validate` fails if either one is missing (see `registry/README.md`).

### Offline vs Online tests

There are two separate kinds of checks. The difference is whether a real model call happens or not:

| | Offline (`make validate`) | Online (`make test-behavior`) |
|---|---|---|
| What runs | `scripts/validate.py` — parses yaml/markdown, does static cross-checks | a real headless `claude -p` run, with the `gft` plugin active |
| Cost | None | **Yes** — calls the real model for each case |
| Runs in CI | Yes (`.github/workflows/validate.yml`, every PR) | No |
| What it checks | Structure: all headings present, description matches the manifest, registry is consistent, good/bad examples pass/fail for the right reason | Real behavior: does the agent announce the correct id, does it actually `Read` the rule file named in `## Procedure` (not just name it) |
| What it cannot check | Whether the agent actually follows the text of SKILL.md/agent.md | — |

`make validate` cannot detect an agent.md file that is written with correct syntax but whose content is not strong enough for the model to really follow it. For example: a bullet that just says "follow rules/X.yaml" is structurally valid, but the model will not `Read` that file on its own without a clearer instruction. This is why `tests/skill-behavior/` exists — see `tests/skill-behavior/README.md`.

## The "must be verifiable" principle

Every skill and agent declares, right inside its own `manifest.yaml`, exactly how `scripts/validate.sh` checks its output. An artifact that cannot be checked structurally — no stable id, a missing required field, a verdict outside the fixed set of values, a command with no exit code — is not considered "done". See `rules/evidence-requirements.yaml`.
