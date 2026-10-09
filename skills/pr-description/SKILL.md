---
name: pr-description
description: Generate a PR description with traceability to the task-spec id, the changed scope, and the verify/review result. Use this at the review stage, after review-change has given an approve verdict. Do NOT use it when verify or review has not passed yet — pr-description only records a result that is already achieved. It is not a place to "ask for" a verdict.
---

# pr-description

## When to use it

| Situation | Use it? |
|---|---|
| `verify-change` has passed and `review-change`/`security-review` already has `verdict: approve` | Yes |
| Verify or review has not run yet, or still has `verdict: blocker` | No — go back to `/gft:verify`/`/gft:review` first |

## Process

_Announce before you start. Print this exact line: ``Using `<id-of-this-skill/agent>` to <short purpose>.`` Then do step 1 (details: `rules/announce-convention.yaml`)._

1. Get `task_id` from the task-spec — never create a PR description that cannot reference a task.
2. Write a one-sentence `summary`: what this PR does, not a full list of the diff.
3. List `changed_paths` exactly as the list already verified in the verification-result — do not add or remove anything.
4. Reference `verification_ref` and `review_ref` to the exact result files that already passed/approved. If review has not approved yet, STOP — do not write the PR description first.
5. Set `breaking_change` clearly to true or false. Never leave it empty.

## Output

| File | Template | Main content |
|---|---|---|
| `pr-description.yaml` | `templates/pr-description.yaml` | `task_id`, `summary`, `changed_paths`, `verification_ref`, `review_ref`, `breaking_change` |

## Verification

```
scripts/validate.sh pr-description <path-to-filled-pr-description.yaml>
```

PASS when: `task_id`/`changed_paths`/`verification_ref`/`review_ref` are not empty; `breaking_change` is `true` or `false` (not null).

## Next step

Use the filled content to create the real PR in the source control tool (GitHub/GitLab, etc.) — pr-description does not create the PR itself, it only standardizes the description content.

## Related

- `skills/review-change/SKILL.md` — read this when `review_ref` does not have an approve verdict yet
- `skills/pr-description/examples/` — read this to compare a valid description with an invalid one
