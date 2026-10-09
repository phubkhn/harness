---
name: task-spec
description: Turns a raw request into a versioned, testable task contract — outcome, acceptance criteria, allowed/protected scope, risk tier. Use this before starting any implementation work. Do NOT use it to choose between several architecture options (use `adr`) or to measure the impact on many modules (use `impact-analysis`) — task-spec assumes the scope is already clear.
---

# task-spec

## When to use it

| Situation | Use it? |
|---|---|
| There is a raw request, ready to implement | Yes |
| There is more than one reasonable way to solve it, and a choice is needed | Run `adr` first, then come back to task-spec |
| You suspect the change touches many modules/services | Run `impact-analysis` first, then come back to task-spec |

## Process

_Announce before you start. Print this exact line: ``Using `<id-of-this-skill/agent>` to <short purpose>.`` Then do step 1 (details: `rules/announce-convention.yaml`)._

1. State one observable outcome, in one sentence. If you cannot state a concrete outcome, STOP and ask — do not guess.
2. Write acceptance criteria as Given/When/Then, each item with a stable id (e.g. `AC-1`).
3. Declare `allowed_scope` (paths/modules this task is allowed to touch) and `protected_scope` (paths it must not touch) — these two sets must not overlap.
4. List constraints, out-of-scope items, risk tier (R0-R4, see `rules/context-hierarchy.yaml`), and open questions.
5. Stop and ask if there is an unresolved ambiguity that could change behavior, security, or scope.

## Output

| File | Template | Main content |
|---|---|---|
| `task-spec.yaml` | `templates/task-spec.yaml` | `outcome`, `acceptance_criteria` (stable id), `allowed_scope`/`protected_scope`, `risk_tier` |

## Verification

```
scripts/validate.sh task-spec <path-to-filled-task-spec.yaml>
```

PASS when: `outcome`/`risk_tier`/`allowed_scope`/`protected_scope`/`acceptance_criteria` are not empty; each acceptance criterion has an `id`; `allowed_scope` and `protected_scope` share no elements.

## Next step

After the task-spec is valid, run `plan-review` (and `test-plan` if needed) before moving to execute.

## Related

- `rules/context-hierarchy.yaml` — read this when you need the full R0-R4 risk tier table
- `skills/plan-review/SKILL.md` — read this to see how the task-spec will be reviewed next
- `skills/task-spec/examples/` — read these when you need to compare a valid task-spec with an invalid one
