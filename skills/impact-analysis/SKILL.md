---
name: impact-analysis
description: Find the scope of impact of a change across several modules, services, or projects before writing a task-spec, together with downstream consumers and rollback options. Use this at the spec stage when a change may cross the boundary of a single repo or module. Do NOT use it for a change that clearly stays inside one module — skip it and write the task-spec directly.
---

# impact-analysis

## When to use it

| Situation | Use it? |
|---|---|
| You suspect the change touches several modules, services, or projects, or has a downstream consumer | Yes |
| The change clearly stays inside one module, and nothing else calls into it | No — write the `task-spec` directly |
| You need to compare several architecture options (not measure scope) | No — use `adr` |

## Process

_Announce before you start. Print this exact line: ``Using `<id-of-this-skill/agent>` to <short purpose>.`` Then do step 1 (details: `rules/announce-convention.yaml`)._

1. Summarize the planned change in one sentence (`change_summary`).
2. List each affected component, with its real impact level (`breaking` / `behavior-change` / `none`) — do not default everything to `none`.
3. List the downstream consumers (other teams or services that call into the changed part) — this is the group that must be told before the merge.
4. Assess `rollback_feasible`: if a bug is found after deploy, can you roll back, and why.
5. Set `risk_tier` (R0-R4, see `rules/context-hierarchy.yaml`) — this value feeds directly into the `risk_tier` of the task-spec.
6. Stop and ask if you have not found all the downstream consumers yet — do not assume "probably nobody uses this".

## Output

| File | Template | Main content |
|---|---|---|
| `impact-analysis.yaml` | `templates/impact-analysis.yaml` | `affected_components` (impact/reason), `downstream_consumers`, `rollback_feasible`, `risk_tier` |

## Verification

```
scripts/validate.sh impact-analysis <path-to-filled-impact-analysis.yaml>
```

PASS when: `affected_components` is not empty, each component has `impact` set to one of {`breaking`, `behavior-change`, `none`} and has a `reason`; `risk_tier` is not empty.

## Next step

Use the `risk_tier` and `affected_components` you just set as input when you write the `task-spec`.

## Related

- `rules/context-hierarchy.yaml` — read this for the full R0-R4 risk tier table
- `skills/task-spec/SKILL.md` — read this to see which field in the task-spec impact-analysis feeds into
- `skills/impact-analysis/examples/` — read this to compare a valid analysis with an invalid one
