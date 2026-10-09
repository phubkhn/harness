---
name: verify-change
description: Runs the declared verification commands for a change and records evidence (real exit code, pass/fail for each acceptance criterion). Use this right after implementation is done, before review. Do NOT use it to judge the quality/scope/safety of a diff — that is the job of `review-change`/`security-review`. verify-change only answers "does it run", not "if it runs, is it correct".
---

# verify-change

## When to use it

| Situation | Use it? |
|---|---|
| Just finished implementing a task-spec, need real evidence before review | Yes |
| Need to judge if a diff has the right scope, the right convention, and is safe | No — use `review-change` (correctness/scope) or `security-review` (security) |
| The task-spec has no acceptance criteria yet | No — go back to `task-spec` first |

## Process

_Announce before you start. Print this exact line: ``Using `<id-of-this-skill/agent>` to <short purpose>.`` Then do step 1 (details: `rules/announce-convention.yaml`)._

1. **Read `rules/evidence-requirements.yaml` with the real Read tool** before you run verify — knowing a rule's name from text does not mean you have read its content; you must actively Read it. If the file is not at the plain path (the current cwd is the project you are working in, not the plugin root), resolve the plugin root first with `scripts/resolve_plugin_root.sh gft` (see the CLAUDE.md section 'Resolve path when the plugin is installed via git') and then Read it by absolute path — do not conclude a rule does not exist just because it is not at the current cwd.
2. Read the approved task spec; if it has no acceptance criteria, STOP and report it — do not invent criteria just to run verify.
3. Read the commands declared for this project (build, lint, test) — if the project belongs to a stack with its own rules (`rules/stacks/`), the lint/format commands are usually how that convention is enforced.
4. Run each command; record the exact exit code, the run time, and the output (length-limited).
5. Map each acceptance criterion in the task spec to a pass/fail result.
6. Never change a test, an oracle, or an acceptance criterion just to turn a failure into a pass.
7. If any acceptance criterion fails, run the `ratchet-log` skill to record an entry before you treat verify-change as done — a failure must not "disappear" from the record.
8. Record the result following `rules/evidence-requirements.yaml` exactly. Fill in `templates/verification-result.yaml` and save it as the result file.

## Output

| File | Template | Main content |
|---|---|---|
| `verification-result.yaml` | `templates/verification-result.yaml` | each command with an exit code, each acceptance criterion with pass/fail, `ratchet_ref` if there is a failure |

## Verification

```
scripts/validate.sh verify-change <path-to-filled-verification-result.yaml>
```

PASS when: each command has an exit_code; `acceptance_results` is not empty and each item has a valid id + result (`pass`/`fail`); if there is any `result: fail`, `ratchet_ref` must not be empty.

## Next step

After verify-change PASSes (or a ratchet_ref has been recorded for every failure), run `/gft:review` (skill `review-change` and/or `security-review`).

## Related

- `rules/evidence-requirements.yaml` — read this when you need the exact required evidence format
- `skills/ratchet-log/SKILL.md` — read this when an acceptance criterion fails, before writing `ratchet_ref`
- `skills/verify-change/examples/` — read these when you need to compare a valid result with an invalid one
