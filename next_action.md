# Next Action: Add a behavioral eval runner for GFT Harness

Reference source: `/Users/gft/Documents/AI/ai_code` (the `dirak` harness), specifically
`tests/claude-code/`, `tests/explicit-skill-requests/`, `docs/testing.md`.

## Current problem

`evals/smoke.yaml` in each skill/agent of GFT Harness is just a **scaffold**:
`lint_evals()` (`scripts/validate.py`) only checks that the file exists and has the
required fields (`id`, `skill`/`agent`, `scenario`, `expected`, `status: scaffold-only`).
Nothing actually calls the skill/agent and compares the result. `make validate` can
pass 100% even if a skill does not work at all (wrong description, trigger does
not fire, agent skips a required step...). This is a real gap: structure is
checked by a machine, but **behavior** is not.

The `ai_code` project solves this by splitting tests into two kinds:

| Kind | Cost | What it checks |
|---|---|---|
| Offline (already have it: `make validate`) | No token cost | Structure: headings, description-sync, protected-paths, good/bad examples |
| **Online (do not have it yet)** | Real token cost | Whether a skill triggers at the right time, whether an agent follows its invariants, whether step order is correct |

Their `docs/testing.md` says it directly: "Only a real session shows whether an
agent complies." Their offline suite (like our `make validate`) cannot give a
baseline to measure before/after a skill edit — something `skill-creator`/`writing-skills`
requires before changing a description.

## Plan (draft — needs review before starting)

### Phase 1 — Minimal test runner (offline plumbing, cheap)

1. Add `tests/skill-behavior/` (a name different from `evals/` so it does not
   collide with the existing `lint_evals` mechanism — `evals/smoke.yaml` keeps its
   role as "declares the scenario", and this new folder is "runs the real scenario").
2. `tests/skill-behavior/test-helpers.sh` — copy the 4 core assert functions from
   `ai_code/tests/claude-code/test-helpers.sh`:
   - `run_claude "<prompt>" [timeout] [allowed_tools]` — calls `claude -p`
     headless, captures the output.
   - `assert_contains` / `assert_not_contains` — case-insensitive grep on the
     output (a prose keyword, not structure).
   - `assert_order` — pattern A must appear before pattern B (used to check
     that the agent does steps in the right order — for example, "STOP when input
     is missing" must appear before the agent creates a file).
3. `tests/skill-behavior/run-skill-tests.sh` — a runner like their
   `run-skill-tests.sh`: an array of tests, a per-file timeout, `--verbose`,
   a Passed/Failed/Skipped summary, exit code 1 on failure.

### Phase 2 — Write the first test as a proof of concept

Pick the skill with the highest regression risk for the first sample test. The
suggestion is `skills/task-spec` (it has 2 invariants that a machine can really
check: `allowed_scope`/`protected_scope` must not overlap, and each AC needs a
stable `id` — easy to write a prompt that checks whether the agent follows this).

`tests/skill-behavior/test-task-spec-gate.sh`:
- Prompt the agent to create a task-spec **missing a required input** → assert the
  output contains "STOP" or the matching gate keyword (step 1 in the
  `## Procedure` contract of SKILL.md), assert the output does **not** contain
  "task_id:" (meaning it did not guess and create the file anyway).
- Prompt the agent to create a task-spec with full input, but with `allowed_scope`
  deliberately overlapping `protected_scope` → assert the agent catches the error
  before writing the file, or assert the created file fails `make check KIND=task-spec`.

### Phase 3 — Integrate into README + CLAUDE.md

- Add an "Offline vs Online tests" table to `README.md` (modeled on the table in
  `docs/testing.md`), stating clearly that online tests cost tokens and need the
  `claude` CLI on PATH.
- Update the Commands section of `CLAUDE.md`: add
  `tests/skill-behavior/run-skill-tests.sh` next to `make validate`,
  noting clearly that this test costs money and does not run in CI by default.
- Do **not** change `evals/*/smoke.yaml` away from `scaffold-only` status until
  this runner is really reviewed and runs reliably — as already noted in
  CLAUDE.md ("that is the point when `status` should finally change from
  `scaffold-only`").

### Out of scope (not for this round)

- Do not borrow `ai_code`'s registry-free / agent-free design — this harness
  keeps its agents/registry layer; we have already confirmed that is one of
  our stronger points.
- Do not build a cross-platform hook (`run-hook.cmd` style) unless there is a
  real need to support Windows.
- Do not build version-drift auditing (`.version-bump.json` style) — this
  harness does not hardcode a version string anywhere yet, so there is nothing
  to audit.

## Things to decide before coding

1. Should we add a separate `lint` check in `scripts/validate.py` that requires
   every "high risk" skill (how would that be marked?) to have at least 1 file
   in `tests/skill-behavior/`? Or should this stay optional, not enforced like
   `examples/`?
2. Should `tests/skill-behavior/` be part of `make validate` (fast, offline) or
   split into its own `make test-behavior` (costs money, does not run by
   default)? — the suggestion is to split it off, following the same spirit as
   `ai_code`.
3. The "measure before changing a skill" baseline (idea #2 from the review) —
   should this become a rule in `rules/` (e.g. `rules/skill-change-discipline.yaml`),
   or just be written as a convention in `CLAUDE.md`/`skills/README.md`?

---

# Part 2: Cross-platform hooks + SessionStart injection [DONE]

> Already implemented: `hooks/run-hook.cmd` (polyglot wrapper), renamed
> `check-protected-paths`/`check-agent-manifest` to extensionless names,
> `hooks.json` now calls through the wrapper + a new `SessionStart` entry,
> `hooks/session-start` injects `skills/using-gft/SKILL.md` (a new skill,
> content adapted from `using-dirak` for this harness's registry-driven
> model — registered in `registry/capability-catalog.yaml`). `make validate`
> PASSES; all 3 hooks were tested by hand through `hooks/run-hook.cmd`
> (blocks a protected path with exit 2, a safe path gives exit 0,
> session-start prints valid JSON). The real Windows branch has not been
> tested (no Windows machine available) — this risk was noted from the start.

Reference source: `/Users/gft/Documents/AI/ai_code/hooks/` (`hooks.json`,
`run-hook.cmd`, `session-start`). Scope agreed with the user: (a) make the
current hooks run on Windows (polyglot wrapper), (b) add a new `SessionStart`
hook. **Do not** extend the `PreToolUse` matcher to other tools (Bash,
NotebookEdit...) this round — the user already removed that branch when
choosing the scope.

## Current state of the harness (`hooks/`)

- `hooks.json` has 2 hooks, both calling a `.sh` file directly through
  `${CLAUDE_PLUGIN_ROOT}`:
  - `PreToolUse` (matcher `Edit|Write`) → `check-protected-paths.sh` →
    delegates to `check_protected_paths.py`.
  - `SubagentStop` → `check-agent-manifest.sh` → delegates to
    `check_agent_manifest.py` (has an uncommitted edit in progress — check
    `git status`, be careful touching this file, read it closely before
    editing).
- Both bash scripts resolve `PLUGIN_ROOT` themselves using
  `$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)` — they do not depend on
  `${CLAUDE_PLUGIN_ROOT}` inside the script itself; only `hooks.json` uses that
  variable to point to the entry point.
- On Windows, `hooks.json` currently calls `check-protected-paths.sh` directly
  (with the `.sh` extension). Based on a comment in `ai_code/hooks/run-hook.cmd`,
  Claude Code can auto-detect and prepend `bash` for a command containing
  `.sh`, but that is not reliable (it does not search for bash at
  `C:\Program Files\Git\bin`, and there is no fallback to "exit quietly if bash
  is missing"). This is why `ai_code` wrote its own `run-hook.cmd` instead of
  relying on that heuristic.

## Plan

### 2.1 — Polyglot wrapper `hooks/run-hook.cmd`

1. Copy the whole `run-hook.cmd` logic block from `ai_code` (a polyglot file:
   the first half is batch inside `: << 'CMDBLOCK' ... CMDBLOCK`, the second
   half is a bash `exec`), only changing the comments to match this repo's
   usual language style. The wrapper takes `<script-name> [args...]`, searches
   for bash (PATH, then `C:\Program Files\Git\bin\bash.exe`, then
   `C:\Program Files (x86)\Git\bin\bash.exe`), and exits quietly (`exit /b 0`)
   if it cannot find one — so the plugin does not break on a Windows machine
   without Git Bash.
2. Rename the 2 hook scripts to be **extensionless** (for the same reason
   `ai_code` gives: to avoid Windows auto-prepending `bash`, which would
   interfere with `run-hook.cmd`'s own routing):
   - `check-protected-paths.sh` → `check-protected-paths`
   - `check-agent-manifest.sh` → `check-agent-manifest`
   - Keep `check_protected_paths.py` / `check_agent_manifest.py` unchanged —
     only the 2 bash entry-point scripts get renamed.
3. Edit `hooks.json`: change both `command` entries from calling the file
   directly to calling through the wrapper, and add `"shell": "bash"` like
   ai_code does:
   ```json
   "command": "\"${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.cmd\" check-protected-paths",
   "shell": "bash",
   "async": false
   ```
   (the same for `check-agent-manifest`).
4. Update `hooks/README.md`: change every mention of the `.sh` file name to
   the extensionless name, and add a paragraph describing `run-hook.cmd` and
   why it is cross-platform.
5. Grep the whole repo for other places that still hardcode
   `check-protected-paths.sh` / `check-agent-manifest.sh` (already found in
   `README.md`, the original `CLAUDE.md`, `rules/context-hierarchy.yaml`,
   `rules/protected-paths.yaml`) — update them together, so there are not two
   different sources of truth for the file name.
6. Test by hand on the current machine (macOS, has bash) by calling
   `hooks/run-hook.cmd check-protected-paths` directly, and check that the
   behavior matches calling the old `check-protected-paths` directly. There is
   no Windows machine to test the batch branch — accept that risk and state it
   clearly in the PR description.

### 2.2 — New `SessionStart` hook

Unlike `ai_code` (which dumps the full content of one "meta" skill,
`using-dirak`, into context), this harness **does not yet have** a general
overview skill like that — `skills/README.md` is the closest thing to that
role. We need to decide what content to inject before writing code (see
"Things to decide" below), but the technical shape is the same:

1. Add `hooks/session-start` (extensionless, same style as 2.1):
   - Resolve `PLUGIN_ROOT` the same way as the other two scripts.
   - Read the content to inject (see options A/B/C below).
   - Escape JSON using the exact `escape_for_json` function (bash parameter
     substitution, not a loop) — copied directly from
     `ai_code/hooks/session-start`, which already notes the performance
     reason for this.
   - Output in the correct format: `hookSpecificOutput.hookEventName:
     "SessionStart"` + `additionalContext`.
   - `exit 0` even if reading the file fails (report the error in the content,
     do not block session start) — keeping this harness's "escalate, do not
     hard-block" spirit (unlike `check-protected-paths`, which *does*
     hard-block).
2. Add a `SessionStart` entry to `hooks.json`, matcher `"startup|clear|compact"`
   like ai_code, calling through `run-hook.cmd session-start`.
3. Update `hooks/README.md` to describe the new hook.

**Content to inject — pick 1 of 3 before coding:**
- **A. A short navigation summary** (lowest-risk option): a few lines about the
  `intake → spec → plan → execute → verify → review` lifecycle, pointing to
  `registry/activation-rules.yaml` to see which agent/skill is active in which
  phase, and noting that `rules/context-hierarchy.yaml` is the tie-breaker in
  a conflict. Does not dump any whole file.
- **B. Dump `skills/README.md` + `agents/README.md`** — similar to ai_code's
  approach (dumping one whole file), but here it would be 2 index files
  instead of 1 "meta" skill.
- **C. No static content injection on SessionStart — instead, only inject
  dynamic warnings.** For example, if `.gft/project.yaml` is missing in the
  project being worked on, remind the agent to create it before using a skill.
  This has a different value from A/B: it is not "teaching the agent the
  process", it is "warning about missing config", which avoids duplicating
  content already in `CLAUDE.md` (`CLAUDE.md` already auto-loads every
  session, so A/B might be unnecessary duplication — needs careful thought
  before doing this).

## Out of scope (this round)

- Do not extend the `PreToolUse` matcher to Bash/NotebookEdit/MCP write tools.
- Do not change the existing hard-block logic in `check-protected-paths` —
  only change *how* it is called (through the wrapper), not the Python logic
  inside it.

## Things to decide before coding

1. What content should `SessionStart` inject: A, B, or C above? (A has the
   lowest risk and the least duplication with CLAUDE.md — suggested as the
   default if there is no other preference).
2. Is it acceptable to take the risk of "the real Windows branch is untested"
   (only reviewed by eye, no Windows machine), or do we need another way to
   test it (a VM, a Windows CI runner)?
3. Does renaming the hook files to extensionless break anything in the user's
   current setup (for example, some personal script that calls
   `check-protected-paths.sh` directly, outside of `hooks.json`)? — the user
   needs to confirm nothing else depends on the old file name before we
   rename it.

---

# Part 3: Improve the execute phase (`developer`) using implementation discipline from ai_code

Reference source: `/Users/gft/Documents/AI/ai_code/skills/test-driven-development/`,
`skills/systematic-debugging/` (+ `references/root-cause-tracing.md`,
`defense-in-depth.md`, `condition-based-waiting.md`, `find-polluter.sh`),
`skills/verification-before-completion/`.

## Already checked: most of this is NOT a real gap

Before writing the plan, each idea was checked against what
`agents/developer/agent.md` and the current `rules/` already do — to avoid
repeating the same mistake warned about in Part 1 ("borrowing an idea without
checking if we already have it"):

| ai_code's idea | Does gft already have it? | Why |
|---|---|---|
| `verification-before-completion` — forbids claiming success without proof, requires running real commands | **Mostly already have it** | `rules/evidence-requirements.yaml` already states directly "Self-reported success is not evidence", and requires `commands_run_with_exit_codes`; `agents/developer/agent.md` steps 5-6 already require writing the report to a file, with no self-certification |
| `test-driven-development` — a bug fix needs a test that reproduces the bug before fixing it | **Already have it** | `rules/testing-quality-gate.yaml`'s `regression-test-required-for-bugfix` statement already says clearly "fail before the fix, pass after the fix" |
| `subagent-driven-development` — fresh subagent/task, a ledger, a capped fix-loop | **No need to port this** | gft's `developer -> qa-engineer -> code-reviewer` lifecycle already plays a similar role, just at a coarser level (per-phase, not per-task); porting this directly would overlap with `registry/activation-rules.yaml` |
| `using-git-worktrees` | **Out of scope** | gft is prose guidance — it does not manage sessions or environments |
| `receiving`/`requesting-code-review` | **No need to port this** | We already have a separate `code-reviewer`/`review-change`; the developer does not request its own review |

## Real gaps worth doing

### 3.1 — TDD for NEW features, not just bug fixes

`rules/testing-quality-gate.yaml` currently only requires "fail before the fix"
for **bug fixes**. ai_code's `test-driven-development` (the Iron Law "NO
PRODUCTION CODE WITHOUT A FAILING TEST FIRST") applies more broadly: every new
acceptance criterion must also show a failing test before writing code that
satisfies it. This is a real gap, not something we already have.

- Edit `rules/testing-quality-gate.yaml`: add a new statement (e.g.
  `failing-test-before-new-behavior`) — every new acceptance criterion in
  `test-plan.yaml` must have a test written first, run to show it FAILS for
  the right reason (not a syntax/import error), then implement code until it
  PASSES.
- Edit `agents/developer/agent.md` steps 3-4: change the order. Right now
  step 3 (implement) comes before step 4 (check against the test-plan/write
  extra tests). This should become "write the test for the missing case →
  run it and see it FAIL → implement → run it and see it PASS" for each
  acceptance criterion, instead of implementing first and adding tests
  afterward. This is a change with real process impact, so it needs careful
  thought because it reorders the current steps 3/4.

### 3.2 — New `systematic-debugging` skill (a complete gap — gft has nothing like it yet)

gft currently has no rule or skill for debugging when implementation or
verification hits an unexpected error — `developer` only has "implement the
smallest change", with no guidance for when an acceptance criterion keeps
failing repeatedly.

- Create `skills/systematic-debugging/SKILL.md` + `manifest.yaml` (following
  the usual 6-heading contract + `make new-skill`), with content adapted from
  ai_code:
  - 4 phases: root-cause investigation (read the full error, reproduce it,
    check the most recent diff) → pattern analysis (compare with where it
    works correctly) → one clear hypothesis, changing one variable at a time
    → implement (1 fix, verify, do not try a second fix until the first one
    is confirmed wrong).
  - **The 3-strikes rule**: after 3 failed fix attempts in a row for the same
    error, STOP and tell the user to suspect a wrong architecture/assumption,
    instead of trying a 4th attempt on its own. This is a specific rule that
    is easy for a machine to check through `verify-change` (count how many
    execute→verify loops failed in a row for the same task; if ≥3, require a
    `verdict: blocker` with a recommendation to stop, no automatic retry).
  - Do not port `find-polluter.sh`/`condition-based-waiting.md` (too specific
    to ai_code's JS/npm test runner) — only port the general backward-tracing
    technique (`root-cause-tracing.md`), rewritten in stack-neutral language.
- `activation.phases: [execute, verify]` — both `developer` and `qa-engineer`
  call this skill when they hit an unexpected error (not only during
  execute), so it should be registered for both phases in
  `registry/activation-rules.yaml`.
- Edit `agents/developer/agent.md`'s `## Related`/step 3: add a line pointing
  to `systematic-debugging` for when implementation hits an unexpected error
  or an unclear failing test — do not repeat content, just reference it.
- Consider: should `qa-engineer`/`agents/qa-engineer/agent.md` also point to
  this skill (verify-change can also hit errors that need debugging)? — yes,
  since `activation.phases` already includes `verify`.

### 3.3 — Clarify "fresh evidence" + ban vague phrases (a small tweak, not a new skill)

`rules/evidence-requirements.yaml` already has the right spirit but does not
yet state 2 things that ai_code has: (a) evidence must come from the **most
recent run**, not an old log or a previous run; (b) vague phrases like
"should pass"/"probably works" are banned as a substitute for actually
running something.

- Add 1 statement to `rules/evidence-requirements.yaml` (do not create a new
  rule file — this is the right place for it): `fresh_evidence_only` —
  evidence must come from the most recent run in the current session; it
  cannot reuse the output of an earlier run, or a run that another agent
  already self-reported.
- This is cheap and low-risk, and should be done before 3.1/3.2 if you want
  to see value quickly.

## Things to decide before coding

1. **3.1, reordering `developer`'s steps 3/4** — this is a real behavior
   change (not just adding a rule), and needs your confirmation first since
   it affects how `developer` works on every task from now on, not just a
   documentation update.
2. **Should the 3-strikes rule in 3.2 hard-block (an automatic `verdict:
   blocker`) or just advise (advisory, like `escalate_paths`)?** — a hard
   block needs extra logic to count consecutive failed loops somewhere a
   machine can read (e.g. across multiple
   `docs/execute/<task_id>-developer-report.md` files, or a new field in the
   `verify-change` output) — noticeably more effort than just writing it as
   advice in `SKILL.md`.
3. Should 3.1/3.2/3.3 all be done at once, or should 3.3 (cheap, safe) come
   first, then 3.2 (a new skill, does not touch existing behavior), leaving
   3.1 (changing behavior that is already running) for last, done
   separately?

## [DONE] — done in the order 3.3 → 3.2 → 3.1

- **3.3**: `rules/evidence-requirements.yaml` got `fresh_evidence_only` +
  `banned_hedge_phrases` added. `developer`/`qa-engineer` were not edited,
  since both already point to the whole rule file (following "one rule, one
  place") — the new field is automatically in scope.
- **3.2**: new skill `skills/systematic-debugging/` (full 6-heading format,
  registered in `registry/capability-catalog.yaml`, active in both `execute`
  and `verify` in `registry/activation-rules.yaml`). The 3-strikes rule
  stays **advisory** (not a hard block) — decision #2 picked the cheaper
  option, since research confirmed: ai_code's original version
  (`subagent-driven-development`) also does **not** hard-enforce the round
  cap in code — it is just ledger prose that Claude counts itself. gft's
  `check_agent_manifest.py` already has a stronger mechanism for counting
  turns/usage from the transcript than ai_code does, so upgrading 3-strikes
  to a hard block later (counting consecutive execute→verify failures for
  the same task_id) is separate work, not bundled into this round — it is
  already noted as a TODO reference right in
  `skills/systematic-debugging/SKILL.md`'s Verification section.
  `developer` step 3 and `qa-engineer` step 3 both now point to this skill
  for errors with no clear cause.
- **3.1**: `rules/testing-quality-gate.yaml` got the
  `failing-test-before-new-behavior` statement added (only applies when a
  task has a `test-plan.yaml`, no made-up cases). `agents/developer/agent.md`
  reordered steps 3/4: step 3 is now "write the test first, see it FAIL for
  the right reason", step 4 is "implement until it PASSES" — while keeping
  the old safety net (if an unexpected case shows up during step 3, add a
  test for it right in step 4, instead of letting `qa-engineer` catch it
  late).

`make validate` PASSES after all 3 parts. No real behavior test has been run
yet (that is Part 1's job, not done yet) to confirm `developer` really
follows the new test-first order — only structure/registry consistency has
been confirmed through `make validate`.

---

## Part 1 [DONE — different from the original draft plan above]

The draft plan above (Phase 1/2/3, copying `ai_code`'s `tests/claude-code/`
style using bash + `test-helpers.sh` with `assert_contains`) was **not used
as written**. It was actually built in Python
(`tests/skill-behavior/run_behavior_probe.py`) instead, for this reason: we
needed to parse `--output-format stream-json` (structured JSON, specific
tool_use blocks) to check exactly *which tool was called with which path* —
not just grep the text output like ai_code's `assert_contains`. The final
scope also ended up broader than the original draft: it covers **all 18
skills/agents** (not just 3 sample tests like the Phase 1 draft), with 2 main
checks:

1. Does it announce the correct id (matching
   `registry/capability-catalog.yaml`, not the phase name or Claude Code's
   internal `subagent_type`)?
2. Does it really `Read` the rule file that `## Procedure` requires (not just
   name the rule in `## Invariants` without reading it)?

**Real evidence gathered across many test runs** (not guesswork):
- Root cause found: `using-gft` (injected by `SessionStart`) only pointed to
  the path `rules/announce-convention.yaml` without inlining the literal
  format, so the model improvised its own announce sentence, not matching
  the template. Fix: inline the literal format directly into the injected
  content → the announce format became correct right away.
- A bigger finding: an agent/skill bullet like "Follow rules/X.yaml" in
  `## Invariants` (just naming the file) does **not** make the model `Read`
  that file on its own — a real test with `developer` showed 0 `Read` calls
  targeting `rules/*.yaml`, even though the task touched
  `error-handling.yaml` directly. Fix: add an explicit action bullet, "Read
  rules/X.yaml using the real Read tool", into `## Procedure` (not just
  `## Invariants`) for all 6 agents + 6 skills that reference a real rule —
  retesting confirmed the Read really happened.
- A secondary finding: the id in the announce could get confused with the
  phase name (`when.phase`) or Claude Code's internal `subagent_type`
  (`gft:<agent>:<agent>`) — fixed `rules/announce-convention.yaml` +
  `using-gft` to clearly separate these 3 easily-confused sources.
- Another secondary finding: `solution-architect` dispatches correctly but
  looks for `rules/*.yaml` in the consuming project's cwd (not the plugin
  root), wrongly concluding "the rule does not exist" — this is exactly the
  problem CLAUDE.md's "Resolve the path when the plugin is installed through
  git" section already warned about, but the newly added Read bullet had not
  applied it yet. Fix: add the instruction to run
  `scripts/resolve_plugin_root.sh gft` to all 12 Read bullets.

**Already integrated into the official docs**: `Makefile` (`make
test-behavior`), the original `README.md` (the "Offline vs Online test"
section), `CLAUDE.md` (the Commands section + a note on `evals/smoke.yaml`),
`tests/skill-behavior/README.md` (full details on how it works, how to read
a FAIL result correctly — telling apart a real bug vs. non-determinism vs. a
vague test prompt).

**Not done yet** (not urgent, noted here so it is not forgotten):
- `evals/smoke.yaml` has not been connected to `CASES` in
  `run_behavior_probe.py` yet — the 2 sources of scenarios are still
  separate, and `evals/smoke.yaml` still keeps `status: scaffold-only`.
- No case has been added to `CASES` yet for `using-gft` (already tested
  carefully by hand, over many rounds, before the script existed) and for
  `developer`/`code-reviewer` (also already tested carefully by hand before
  the script existed) — these should be added so a future `make
  test-behavior` run covers all 18/18 in one command, instead of relying on
  memory that 3 of them were already tested by hand.
- The 3-strikes rule (Part 3.2) and `failing-test-before-new-behavior` (Part
  3.1) have no real behavior case in `CASES` yet (this needs a more complex
  fixture: 1 error repeating 3 times, or 1 new acceptance criterion with a
  test-plan) — left for a later round.
