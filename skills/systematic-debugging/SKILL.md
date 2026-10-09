---
name: systematic-debugging
description: Use this when implementing or verifying hits an error/test failure with no clear cause right away — investigate the root cause in a systematic way before trying a fix, instead of guessing one attempt at a time.
---

## When to use it

| Situation | Use it? | Why |
|---|---|---|
| A test/build fails and the cause is not clear right away from the error message | Yes | A guessed fix with no hypothesis can easily hide the real root cause, which causes it to come back |
| You already tried 1 fix, ran it again, and it still fails (even a different error) | Yes | This is a signal that the earlier hypothesis was wrong — go back and investigate, do not try another fix based on the same assumption |
| A clear one-line error with an obvious cause (e.g. a typo, a missing import, a wrong field name) | No | Fix it directly, run it again to confirm per `rules/evidence-requirements.yaml` — no need for the full process |
| A new acceptance criterion that has never run yet (no failure yet, writing the test for the first time) | No | This is a TDD step (`rules/testing-quality-gate.yaml`), not debugging — use this skill when there is a real error/failure, not when writing code for the first time |

## Process

_Announce before you start. Print this exact line: ``Using `<id-of-this-skill/agent>` to <short purpose>.`` Then do step 1 (details: `rules/announce-convention.yaml`)._

1. **Read `rules/evidence-requirements.yaml` and `rules/testing-quality-gate.yaml` with the real Read tool** before you investigate — knowing a rule's name from text does not mean you have read its content; you must actively Read it. If the file is not at the plain path (the current cwd is the project you are working in, not the plugin root), resolve the plugin root first with `scripts/resolve_plugin_root.sh gft` (see the CLAUDE.md section 'Resolve path when the plugin is installed via git') and then Read it by absolute path — do not conclude a rule does not exist just because it is not at the current cwd.
2. **Root cause investigation**: read the full error message/stack trace (not just the first line), make the error reproduce in a stable way before doing anything else, and check if the most recent changes (`git diff`/`git log -p`) could be related. If the system has several layers (API → service → DB, or UI → state → network), add instrumentation at each layer's boundary to find which layer the error comes from, instead of guessing.
3. **Pattern analysis**: find a similar place in the same codebase that works correctly, and diff it against the broken place — that difference is often the cause, or a direct clue to the cause.
4. **One clear hypothesis**: state it as one specific, testable sentence ("X fails because of Y"), then design a minimal test that changes only one variable to confirm or reject that hypothesis. Do not change many things at once — you will not be able to tell which change actually fixed anything.
5. **Implement the fix**: write a test that reproduces the error (it fails for the exact reason stated in the hypothesis, not because of a syntax/import error), make exactly one minimal change, run it again to confirm that test passes and no other test breaks.
6. **The 3-strikes rule**: after 3 failed fix attempts in a row for the same error (the test still fails, even if it fails for a different reason each time), STOP — do not try a 4th fix on your own. Tell the user that the current hypothesis is likely wrong at its root, possibly because of a wrong architecture assumption rather than a wrong implementation detail, and that the user needs to decide the next direction.

## Output

This skill does not create its own artifact. The result is: (a) the fix is implemented with a regression test per `rules/testing-quality-gate.yaml`, and (b) the hypothesis + root cause are written into the report of the agent that calls this skill (`docs/execute/<task_id>-developer-report.md` if called from `developer`) — not a separate file for the skill.

## Verification

There is no separate `<path-to-output>` for this skill. "The process was followed correctly" is checked indirectly through two things that already exist: the final fix has a regression test that reproduces the error (`rules/testing-quality-gate.yaml`, statement `regression-test-required-for-bugfix`), and the report of the agent that calls this skill records the real command + exit code per `rules/evidence-requirements.yaml` (not just "it's fixed now"). The 3-strikes rule in step 5 is currently self-discipline (advisory); it is **not** counted or hard-blocked by `check_agent_manifest.py` in this version — see the matching TODO note in `hooks/check_agent_manifest.py` if you want to make it a hard block later.

## Next step

After you confirm the fix passes, go back to the original process that called this skill (`developer` step 5 runs `verify-change`, or `qa-engineer` step 3 runs `verify-change`) — this skill does not close the task on its own.

## Related

- `rules/testing-quality-gate.yaml` — a regression test is required for a bug fix; this applies to the fix found in step 4.
- `rules/evidence-requirements.yaml` — the required evidence format when reporting root cause and fix, including `fresh_evidence_only`/`banned_hedge_phrases`.
- `agents/developer/agent.md` — where this skill is called when step 3/4 hits an unexpected error.
- `agents/qa-engineer/agent.md` — where this skill is called when `verify-change` finds a failure with no clear cause.
- `hooks/check_agent_manifest.py` — where the 3-strikes rule could be upgraded from advisory to a hard block (by counting consecutive execute→verify failure rounds for the same task_id), not done in this version.
