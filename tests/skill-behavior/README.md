# tests/skill-behavior

A **real behavior** test, very different from `make validate` (which only checks
static structure). It calls `claude -p` headless with the `gft` plugin active
(`--plugin-dir`), captures every tool call through `--output-format
stream-json`, then checks two things for each skill/agent:

1. **Correct id announced** — does the line ``Using `<id>` to <short purpose>.``
   get printed, and is `<id>` a real id registered in
   `registry/capability-catalog.yaml` (not a phase name, not Claude Code's
   internal `subagent_type`).
2. **Correct rule file read** — for a *skill* whose `## Process` has a bullet
   like "Read `rules/X.yaml` with a real Read tool call", does a real `Read`
   tool call target that exact file (not just a mention of the rule's name in
   text). This check only runs for `kind: "skill"` cases. An *agent* case
   dispatches through the Task tool, so its Read calls happen inside the
   subagent's own transcript, not the top-level one this script captures —
   there is no way to see them from here, so `reads_ok` is reported as `N/A`
   for every agent case instead of a false "missing reads".

This is the first version of the "behavioral eval runner" idea (see the
history in `next_action.md`, the "Current problem" section about
`evals/*/smoke.yaml` — that file only declares a scenario, nothing runs it;
this script is the first real runner).

## Run it

```bash
make test-behavior                       # all 18 cases, ~20-40 min
make test-behavior ONLY=developer,adr    # run only a few cases, faster
```

**Costs real money** — each case calls a real model through `claude -p`
(dispatching a subagent where the case is an agent costs one more nested
call). It does not run in `.github/workflows/validate.yml` — only `make
validate` (offline, using `scripts/validate.py`) runs in CI.

## How it works

- `run_behavior_probe.py` defines 18 cases in the `CASES` variable — each case
  has `id`, `kind` (agent/skill), `prompt`, `files` (fixtures copied into a
  simulated scratch project before running — it reuses the existing
  `examples/good.*.yaml` of each skill as valid input, so there is no need to
  invent new ones), and `expected_reads`.
- For an agent/skill where the same phase has both an agent and a skill with
  the same job (e.g. `business-analyst`/`intake-request`,
  `qa-engineer`/`verify-change`, `security-reviewer`/`security-review` —
  `registry/activation-rules.yaml` activates both), the `accept_ids` field
  lists all the ids that count as correct — it does not force the model to
  always pick the agent over the matching skill.
- Each case runs in its own scratch folder (`tempfile.mkdtemp`), and cleans up
  after itself — it never touches the harness repo itself.
- The full result (including every tool call) is written to
  `last_probe_results.json` after each run; the raw transcript for each case
  is in a temp folder printed at the top of the log ("Output raw transcripts:
  ...") — useful when you need to look into one specific failed case.

## Notes for reading a FAIL result

Before you decide it is a real harness bug, check these 2 common causes
(both have happened while building this script):

1. **Non-deterministic model behavior** — the same prompt, the same harness,
   can give 2 different results between runs (e.g. whether it really
   dispatches a subagent or not). One FAIL is not enough proof — run `--only
   <id>` a few more times before you call it a real regression.
2. **The case's own prompt is unclear** — if the agent refuses to answer, or
   asks a question back instead of acting, check whether that is the CORRECT
   behavior under that agent's own `## Required Input`/gate (an agent is
   allowed to refuse when the real input is not clear enough) before you call
   it a failure.

## When you add a new skill or agent

Add one entry to `CASES` in `run_behavior_probe.py`: `id` must match
`registry/capability-catalog.yaml`, `prompt` must describe the situation
correctly, matching the "When to use it" table of that skill/agent, `files`
is the minimal fixture that must already exist on disk (reuse
`skills/<name>/examples/good.*.yaml` when that skill consumes the output of
another skill), `expected_reads` is the list of `rules/*.yaml` files that the
skill/agent's own `## Process`/`## Invariants` requires it to read — leave it
empty if there is no "Read ... with a real Read tool call" bullet.
