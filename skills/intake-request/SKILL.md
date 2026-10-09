---
name: intake-request
description: Turn a rough request or ticket into a testable intake brief — business goal, stakeholder, success metric, definition of done. Use this when the business goal, stakeholder, or success metric is not clear yet, before writing a task-spec. Do NOT use it when the request is already clear (you know the outcome, who needs it, and how to measure it) — go straight to `task-spec`. Do not create an intake brief for every ticket.
---

# intake-request

## When to use it

| Situation | Use it? |
|---|---|
| A rough ticket or request, with an unclear business goal, stakeholder, or success metric | Yes |
| The request is already clear: you know the outcome, who needs it, and how to measure it | No — go straight to `task-spec` |
| There is already an intake brief, but the feature needs to split into several tasks by stage | Run `feature-roadmap` next. Do not repeat intake-request |

## Process

_Announce before you start. Print this exact line: ``Using `<id-of-this-skill/agent>` to <short purpose>.`` Then do step 1 (details: `rules/announce-convention.yaml`)._

1. If the rough request does not even give a basic business goal or who needs it, STOP and ask the requester again. Do not make up `business_goal`/`stakeholders` to fill the gap.
2. Restate the rough request in one `problem_statement` sentence.
3. State the `business_goal`: the business problem or opportunity to solve, kept separate from the technical solution.
4. List the `stakeholders`: who needs this, and who has the authority to set scope and priority.
5. State a measurable `success_metric`. If it cannot be measured yet, put that into `open_questions` instead of making up a number.
6. Declare `priority`, `assumptions` (explicit, not hidden), and `out_of_scope`.
7. List all blocking `open_questions` before treating the brief as ready for `task-spec`.
8. When an `open_question` gets an answer: if the answer is a **confirmed fact** (someone with the authority gave a clear answer), put that answer directly into the field the question was blocking (`business_goal`, `success_metric`, `priority`, `stakeholders`, etc.) and **delete** that entry from `open_questions` — do not move it to `assumptions`. Only move it to `assumptions` when the answer has **not been formally confirmed** and you chose that assumption yourself to avoid being blocked.
9. Write `definition_of_done`: at least one **specific, checkable** condition that tells you this brief itself is "done" — read `references/definition-of-done.md` if you are not sure how to write it.
10. Once `open_questions` is truly empty (every blocking question has been answered per step 8), set `ready_for_spec: true` — this is a machine-checkable gate (`validate.sh` FAILS if `ready_for_spec: true` while `open_questions` still has an item). It is not a plain self-declaration. If any open_question remains, keep `ready_for_spec: false`.

## Output

| File | Template | Main content |
|---|---|---|
| `intake-brief.yaml` | `templates/intake-brief.yaml` | `problem_statement`, `business_goal`, `stakeholders`, `success_metric`, `open_questions`, `definition_of_done` |

## Verification

```
scripts/validate.sh intake-request <path-to-filled-intake-brief.yaml>
```

PASS when: `problem_statement`/`business_goal`/`stakeholders` are not empty; at least one stakeholder has a `name` or `role`; `success_metric` is not empty, or the reason it cannot be measured is in `open_questions`; `definition_of_done` has at least one non-empty condition; and if `ready_for_spec: true` then `open_questions` must be empty (otherwise FAIL — this is a real gate, not just a suggestion).

## Next step

Only continue when `ready_for_spec: true`. If the feature is big or risky enough to consider splitting by stage, run `feature-roadmap` next. Otherwise, go straight to `/gft:spec` (skill `task-spec`).

## Related

- `skills/intake-request/references/definition-of-done.md` — read this when you are not sure how to write a specific `definition_of_done`
- `skills/feature-roadmap/SKILL.md` — read this when a feature needs to split into several stages after intake
- `skills/intake-request/examples/` — read this to compare a valid intake brief with an invalid one
