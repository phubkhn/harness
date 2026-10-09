---
name: test-plan
description: Decides what to test before writing code. Maps each test case to an acceptance criterion in the task-spec, and requires a case for the failure path. Use this at plan, before the developer starts implementing and before verify-change runs any evidence. Do NOT use it to record evidence that already ran — that is the job of `verify-change`. test-plan only decides before there is code.
---

# test-plan

## When to use it

| Situation | Use it? |
|---|---|
| The task-spec already has acceptance criteria, not implemented yet | Yes |
| Already implemented, need to run real tests and record evidence | No — use `verify-change` |
| A very simple story, only 1 low-risk AC (e.g. a static text change) | Consider skipping it, but if unsure, just run it |

## Process

_Announce before you start. Print this exact line: ``Using `<id-of-this-skill/agent>` to <short purpose>.`` Then do step 1 (details: `rules/announce-convention.yaml`)._

1. Read the `acceptance_criteria` of the related task-spec; if there is no task-spec yet, STOP and ask for `task-spec` to run first.
2. For each acceptance criterion, write at least one test case that refers to its exact id (`acceptance_criteria_ref`).
3. For each criterion with risk (a failure path, a limit, a race condition), add at least one case with `covers_negative_path: true` — do not only test the happy path.
4. State the `kind` for each case (unit/integration/e2e/manual) — this decision affects which command verify-change will run.
5. Record any open question about test data/environment/oracle that is not settled yet.

## Output

| File | Template | Main content |
|---|---|---|
| `test-plan.yaml` | `templates/test-plan.yaml` | `cases` (id, acceptance_criteria_ref, kind, covers_negative_path), `open_questions` |

## Verification

```
scripts/validate.sh test-plan <path-to-filled-test-plan.yaml>
```

PASS when: `cases` is not empty; each case has a stable `id` and an `acceptance_criteria_ref`; at least one case in the whole plan has `covers_negative_path: true`. This is only the machine-checkable floor — step 3 above asks for more (each risky criterion must have its own negative-path case); check step 3 yourself during review, do not rely only on this command passing.

## Next step

After the test-plan has enough cases, move to `/gft:execute` (agent `developer`) — the developer implements according to both the task-spec and the test-plan.

## Related

- `skills/task-spec/SKILL.md` — read this when acceptance criteria are not clear enough to write a case
- `skills/verify-change/SKILL.md` — read this to see how a case in the test-plan will be run and how evidence is recorded
- `skills/test-plan/examples/` — read these when you need to compare a valid test-plan with an invalid one
