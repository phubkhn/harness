---
name: feature-roadmap
description: Decide and record whether a feature needs to split into several task-specs by stage (staged), or stay as one task (single), after all blocking open questions are answered. Use this before writing the first task-spec of a feature, when the outcome is big or risky enough to consider splitting by risk tier or technical dependency. Do NOT use it for a small, clear fix that fits in one task (for example, a one-line fix) — skip it and go straight to `task-spec`.
---

# feature-roadmap

## When to use it

| Situation | Use it? |
|---|---|
| The feature is big or risky enough to consider splitting into stages | Yes |
| A small, clear fix that fits in one task | You can skip it and go straight to `task-spec` |
| There are still blocking open questions from intake with no answer | No — answer them all first. This is a required gate at step 2 |

## Process

_Announce before you start. Print this exact line: ``Using `<id-of-this-skill/agent>` to <short purpose>.`` Then do step 1 (details: `rules/announce-convention.yaml`)._

1. Read the intake brief (if there is one) and any `open_questions` still open there or from an earlier exchange.
2. **Required gate — stop and ask the user, do not decide alone:**
   - List every blocking open question that does not yet have a clear answer. If any remain, STOP here. Do not continue the roadmap until the user answers (do not assume an answer yourself).
   - Once every open question has a clear answer, ask the user directly: "Should this feature fit in one task-spec (`single`), or split into several stages by risk tier or technical dependency (`staged`)?" Do not decide this for the user while it is still unclear.
3. If `single`: set `split_decision: single`, keep `stages` with exactly one item that summarizes the whole scope, then move to `/gft:spec`.
4. If `staged`: list each `stage` in the order it will run. Each stage must have:
   - `scope_summary` — one sentence that summarizes the scope of this stage only (specific enough that a reader cannot mistake this stage for the whole feature — this is exactly why this skill exists; see the TASK-001 case where a skeleton-only stage was mistaken for "the full backend").
   - `risk_tier` — using the same R0-R4 scale used in task-spec.
   - `depends_on` — which stage must finish before this one (empty if it can run on its own).
   - `rationale` — why this stage is split out on its own (higher risk, a technical dependency, or a need for separate approval — never split a stage just "to keep things tidy" without a reason).
5. For each stage, `/gft:spec` will create a separate task-spec. Once that task-spec has an `id`, come back and fill in `task_ref` on the matching stage in this roadmap file, to keep the two-way link.

## Output

| File | Template | Main content |
|---|---|---|
| `feature-roadmap.yaml` | `templates/feature-roadmap.yaml` | `split_decision` (single/staged), `open_questions_resolved`, `stages` (scope_summary/risk_tier/depends_on/rationale/task_ref) |

## Verification

```
scripts/validate.sh feature-roadmap <path-to-filled-feature-roadmap.yaml>
```

PASS when: `outcome` is not empty; `split_decision` is `single` or `staged`; `open_questions_resolved` is `true`; if `staged`, there are at least 2 `stages`, each stage has `scope_summary`/`risk_tier`, and `depends_on` only points to a `stage_no` that exists in this same roadmap.

## Next step

Run `/gft:spec` (skill `task-spec`) for each stage — a separate task-spec for each stage if `staged`, or a single task-spec if `single`.

## Related

- `skills/intake-request/SKILL.md` — read this when a blocking open question has not been answered at step 1-2
- `skills/task-spec/SKILL.md` — read this to see how each stage turns into a task-spec
- `skills/feature-roadmap/examples/` — read this to compare a valid roadmap with an invalid one
