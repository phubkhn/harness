---
name: review-change
description: Does an independent, read-only review of a diff, checked against rules and acceptance criteria. Use this after verify-change, before the change is applied/merged. Do NOT use it to re-run tests or implementation — review-change only reads, it does not run anything again. For a deeper security review (authn/authz, secrets, input validation), also use `security-review` in parallel. It does not replace review-change.
---

# review-change

## When to use it

| Situation | Use it? |
|---|---|
| A diff exists, `verify-change` has already run, ready to apply/merge | Yes |
| No verify-change result yet | No — run `verify-change` first; review-change needs that evidence as input |
| Need a separate, deep security check | Add `security-review`, do not replace this skill |

## Process

_Announce before you start. Print this exact line: ``Using `<id-of-this-skill/agent>` to <short purpose>.`` Then do step 1 (details: `rules/announce-convention.yaml`)._

1. If there is no `verify-change` result yet, STOP and ask for `verify-change` to run first — review-change needs that evidence as input, and must not re-run the implementation to guess at it.
2. Read the diff, the task spec, and the verification result.
3. **Read `skills/review-change/references/checklist.md`, `rules/change-management.yaml`, and `rules/safety-invariants.yaml` with the real Read tool** — knowing these file names from text does not mean you have read their content; you must actively Read them. If the file is not at the plain path (the current cwd is the project you are working in, not the plugin root), resolve the plugin root first with `scripts/resolve_plugin_root.sh gft` (see the CLAUDE.md section 'Resolve path when the plugin is installed via git') and then Read it by absolute path — do not conclude a rule does not exist just because it is not at the current cwd. Then check the diff against each checklist item.
4. List findings by severity (blocker, major, minor), with a file and line reference.
5. Return a verdict: `approve` or `blocker` (one blocker finding is enough to make the verdict `blocker`).
6. If the verdict is `blocker`, run the `ratchet-log` skill before you treat review-change as done. Fill in `templates/review-result.yaml` and save it as the result file.

## Output

| File | Template | Main content |
|---|---|---|
| `review-result.yaml` | `templates/review-result.yaml` | `findings` (severity/file/line/summary), `verdict` (approve/blocker), `ratchet_ref` if blocker |

## Verification

```
scripts/validate.sh review-change <path-to-filled-review-result.yaml>
```

PASS when: `verdict` is `approve` or `blocker`; each finding has a `file` reference; verdict is `blocker` whenever there is at least one finding with severity blocker, and in that case `ratchet_ref` must not be empty.

## Next step

If `approve`: run `pr-description`. If `blocker`: go back to `developer` to fix it, then run `verify-change` → `review-change` again.

## Related

- `skills/review-change/references/checklist.md` — read this before writing a finding; this is the full checklist
- `rules/change-management.yaml`, `rules/safety-invariants.yaml` — read these when you need details on a checklist item
- `skills/ratchet-log/SKILL.md` — read this when the verdict is blocker, before writing `ratchet_ref`
- `skills/review-change/examples/` — read these when you need to compare a valid result with an invalid one
