# agents

Agent roles for the basic SDLC jobs: `solution-architect`, `developer`, `qa-engineer`, `code-reviewer`, `security-reviewer`, `business-analyst`. Each agent is a folder with:

- `agent.md` — the Claude Code subagent format (YAML frontmatter with `name`/`description`/`tools`). The body must have exactly 6 required headings. `lint_agent_sections()` checks this: `## Required Input`, `## Invariants`, `## Process`, `## Do Not`, `## Output to the Caller`, `## Verification`.
- `manifest.yaml` — a contract a machine can check: the activation phase, the authority level, the allowed tools, and how `scripts/validate.sh` checks the agent's output. The `description` here must match the `description` in the `agent.md` frontmatter exactly (`lint_description_sync()`). `allowed_tools` must match the `tools:` field in `agent.md`, through the vocabulary table `_TOOLS_VOCAB` in `scripts/validate.py` (`lint_tools_vocabulary()`).
- `evals/smoke.yaml` — a minimal sample scenario for the agent (a situation plus the expected `terminal_state`). **This is only a scaffold**, like in skills: `scripts/validate.sh` only checks that this file exists and has the needed fields. There is no eval runner yet that gives the agent real work and scores the output.

Add a new role with `scripts/new_agent.sh <name> "<description>"` (this script also creates `evals/smoke.yaml`).

Note: the `agent.md` files keep some English technical words on purpose (`trade-off`, `downside`, `constraint`, `exit code`, `changed path`, `acceptance`, `verdict`, `stakeholder`, `assumption`). These are the words that `scripts/validate.py` (`AGENT_OUTPUT_MARKERS`) looks for in the agent's real output, to check that the output has the needed content. Do not translate these words when you edit the file. `lint_agent_markers()`, run in `make validate`, will fail if an `agent.md` drops its role's marker.

## Input/output for each agent

| Agent | Phase | Input | Output | Verify with |
|---|---|---|---|---|
| `solution-architect` | spec, plan | a raw request + constraints of the current system | an architecture proposal/decision that states `trade-off`/`downside`/`constraint` | `scripts/validate.sh agent-output solution-architect <file.md>` |
| `developer` | execute | an approved task-spec + plan | a diff inside `allowed_scope`, with a list of `changed path` items and the commands run with their `exit code` | `scripts/validate.sh agent-output developer <file.md>` |
| `qa-engineer` | verify | implemented code + task-spec | real evidence from running checks: the `exit code` of each command, and the result for each `acceptance` criterion — uses the skill `verify-change` to write `verification-result.yaml` | `scripts/validate.sh agent-output qa-engineer <file.md>` |
| `code-reviewer` | review | diff + task-spec + verification-result | findings with a file/line reference, a `verdict` of approve/blocker — uses the skill `review-change` to write `review-result.yaml` | `scripts/validate.sh agent-output code-reviewer <file.md>` |
| `security-reviewer` | verify, review | diff + task-spec + verification-result | security findings (authn/authz, secrets, input validation, PII) with a file/line reference, a `verdict` of approve/blocker — uses the skill `security-review` to write `review-result.yaml` | `scripts/validate.sh agent-output security-reviewer <file.md>` |
| `business-analyst` | intake, spec | a raw request/ticket, with an unclear business goal, stakeholder, or success metric | an intake brief that states the `stakeholder`, the `acceptance criteria` that still need work, and a clear `assumption` list — uses the skill `intake-request` to write `intake-brief.yaml` | `scripts/validate.sh agent-output business-analyst <file.md>` |

`qa-engineer` and `code-reviewer`/`security-reviewer` differ only in **the kind of question they answer**: verify gives real evidence ("it runs"), review gives an independent judgment ("it runs, but that does not mean it has the right scope, is safe, or follows convention") — see `skills/verify-change/SKILL.md` and `skills/review-change/SKILL.md`.

`developer` and `qa-engineer` both call the skill `systematic-debugging` when implementing or verifying hits an error with no clear cause (`developer` step 4, `qa-engineer` step 3) — this finds the root cause in a systematic way before trying a fix, instead of guessing one fix at a time. `developer` also follows `rules/testing-quality-gate.yaml` (the `failing-test-before-new-behavior` statement): for a new case in `test-plan.yaml`, it must write a test and see it FAIL before implementing (step 3), then implement until that test PASSes (step 4) — not just check the test-plan after the code is already done.
