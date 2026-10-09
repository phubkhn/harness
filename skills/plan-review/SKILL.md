---
name: plan-review
description: Review an implementation plan against the harness rules and the task spec, before any code is written. Use this before starting to execute a non-trivial task, or whenever the plan touches an escalate_path. Do NOT use it after the code is already written — that is the job of `review-change`. plan-review only looks at a plan that is still on paper.
---

# plan-review

## When to use it

| Situation | Use it? |
|---|---|
| A task-spec and a proposed plan exist, no code written yet | Yes |
| The task is just one trivial step (for example, a one-line fix that does not touch an escalate_path) | No — you can skip this and go straight to `developer` |
| A diff already exists and needs review | No — use `review-change`/`security-review`, not plan-review |

## Process

_Announce before you start. Print this exact line: ``Using `<id-of-this-skill/agent>` to <short purpose>.`` Then do step 1 (details: `rules/announce-convention.yaml`)._

1. **Read `rules/protected-paths.yaml` and `rules/safety-invariants.yaml` with the real Read tool** before you review. Knowing a rule's name from text does not mean you have read its content — you must actively Read it. If the file is not at the plain path (the current cwd is the project you are working in, not the plugin root), first resolve the plugin root with `scripts/resolve_plugin_root.sh gft` (see the CLAUDE.md section "Resolve path when the plugin is installed through git"), then Read it by absolute path. Do not conclude a rule does not exist just because it is not at the current cwd.
2. Read `allowed_scope`, `protected_scope`, and the acceptance criteria in the task spec. If there is no task-spec yet, STOP and ask for `task-spec` to be run first.
3. Check that the plan only touches `allowed_scope`, and never touches `protected_scope` or `rules/protected-paths.yaml`.
4. Check that the plan does not break `rules/safety-invariants.yaml` (for example, no step that edits the task's own spec/rule/hook).
5. Check that each acceptance criterion maps to at least one concrete step in the plan.
6. If the project belongs to a stack with its own rules (`rules/stacks/`, detected with `scripts/detect_stack.sh`), check that the plan does not go against the declared conventions.
7. Mark every step that touches an escalate_path (see `rules/protected-paths.yaml`) as needing clear confirmation.
8. Return one of three values: `approved`, `changes-requested` (with the exact line/step and reason), or `escalate`. Fill in `templates/plan-review-result.yaml` and save it as the result file.
9. If the verdict is `approved`: fill in `task_spec_ref` (the path of the task-spec just reviewed) and `task_spec_hash` (run `scripts/hash_manifest.py compute <task_spec_ref>`) — this is a snapshot that prevents editing the task-spec in secret after approval (see `rules/safety-invariants.yaml#no-self-edit`). `validate.sh` will FAIL if these 2 fields are missing.

## Output

| File | Template | Main content |
|---|---|---|
| `plan-review-result.yaml` | `templates/plan-review-result.yaml` | `verdict` (approved/changes-requested/escalate), `findings` with step/summary if not approved directly |

## Verification

```
scripts/validate.sh plan-review <path-to-filled-plan-review-result.yaml>
```

PASS when: `verdict` is one of `approved`/`changes-requested`/`escalate`; if verdict is `changes-requested` or `escalate` then at least one finding is required; if verdict is `approved` then `task_spec_ref`/`task_spec_hash` are required, and if that task-spec's hash changes later, there must be a `scope_amendments` entry (status: approved) explaining it — otherwise the next validate run will FAIL (suspected silent edit of the task-spec).

## Next step

If `approved`: run `/gft:execute` (agent `developer`). If `changes-requested`/`escalate`: go back and adjust the plan, then run `plan-review` again. Do not execute on your own before approval. If several rounds are needed before approval, add each round to the rounds field of the same file (not a separate `.md` history file) — validate.sh applies the same "changes-requested/escalate needs a finding" rule to each round, and the last round must match the verdict at the top of the file.

## Related

- `rules/protected-paths.yaml` — read this to decide whether a step touches an escalate_path
- `rules/safety-invariants.yaml` — read this when unsure whether a step in the plan edits its own spec/rule
- `skills/plan-review/examples/` — read this to compare a valid result with an invalid one
