---
name: adr
description: Record an important architecture decision that is hard to reverse or open to debate. Include the options you considered and the downside of each option. Use this at the spec or plan stage when there is more than one reasonable way to solve the problem. Do NOT use it for a small decision that is easy to reverse, or when there is only one reasonable option — write that directly in the task-spec. Do not create an ADR for every choice.
---

# adr

## When to use it

| Situation | Use it? |
|---|---|
| There are 2 or more reasonable options, the choice is hard to reverse, or it affects many modules | Yes |
| There is only one reasonable way to do it, or it is easy to reverse in a later PR | No — write it directly in `task-spec`. No ADR needed |
| You need to check the impact of a change on many components or services | No — use `impact-analysis`. An ADR is about choosing between options, not about measuring the scope of impact |

## Process

_Announce before you start. Print this exact line: ``Using `<id-of-this-skill/agent>` to <short purpose>.`` Then do step 1 (details: `rules/announce-convention.yaml`)._

1. State the context: the problem that needs a decision and the related constraints (NFRs, deadline, cost, team). If the problem is not clear enough to compare options, STOP and ask again. Do not guess the constraints yourself.
2. List at least 2 options. Each option must have at least one concrete downside (no option can have "only pros").
3. Choose the decision, and state clearly which constraint drove that choice.
4. List the consequences (including negative ones or costs you must pay).
5. If this ADR replaces an older ADR, set `superseded_by` and update the old ADR's status to `superseded`.

## Output

| File | Template | Main content |
|---|---|---|
| `adr.yaml` | `templates/adr.yaml` | `title`, `context`, `options` (each option has `cons`), `decision`, `consequences` |

## Verification

```
scripts/validate.sh adr <path-to-filled-adr.yaml>
```

PASS when: `title`/`context`/`options`/`decision` are not empty; each option in `options` has at least one `cons`.

## Next step

After the ADR has a decision, continue writing or updating the `task-spec` to match that decision, then move on to `plan-review`.

## Related

- `skills/task-spec/SKILL.md` — read this to see where the ADR connects to the task-spec (constraint, allowed_scope)
- `skills/adr/examples/` — read this to compare a valid ADR with an invalid one
