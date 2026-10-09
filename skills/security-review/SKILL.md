---
name: security-review
description: Does an independent, read-only security review of a diff — authn/authz, input validation, secrets, sensitive data. Use this at verify, in parallel with or after review-change, especially when the diff touches escalate_paths in rules/protected-paths.yaml. Does NOT replace `review-change` — security-review only looks at security, not scope/convention/architecture.
---

# security-review

## When to use it

| Situation | Use it? |
|---|---|
| The diff touches authn/authz, user input, secrets, or sensitive data | Yes |
| The diff touches `escalate_paths` in `rules/protected-paths.yaml` | Yes, required |
| You only need a normal scope/convention/correctness check | No — use `review-change` |

## Process

_Announce before you start. Print this exact line: ``Using `<id-of-this-skill/agent>` to <short purpose>.`` Then do step 1 (details: `rules/announce-convention.yaml`)._

1. If there is no `verify-change` result yet, or the scope of the diff to check is not clear, STOP and ask for that first — do not re-run the implementation to guess at it.
2. Read the diff, the task spec, and the verification result.
3. **Read `skills/security-review/references/checklist.md`, `rules/security-baseline.yaml`, and `rules/protected-paths.yaml` with the real Read tool** — knowing these file names from text does not mean you have read their content; you must actively Read them. If the file is not at the plain path (the current cwd is the project you are working in, not the plugin root), resolve the plugin root first with `scripts/resolve_plugin_root.sh gft` (see the CLAUDE.md section 'Resolve path when the plugin is installed via git') and then Read it by absolute path — do not conclude a rule does not exist just because it is not at the current cwd. Then check the diff against each checklist item.
4. List findings by severity, with a file/line reference.
5. Return a verdict: `approve` or `blocker` (one blocker finding is enough to make the verdict `blocker`).
6. If the verdict is `blocker`, run the `ratchet-log` skill before you treat security-review as done. Fill in `templates/review-result.yaml` (same format as `review-change`) and save it as the result file.

## Output

| File | Template | Main content |
|---|---|---|
| `review-result.yaml` | `templates/review-result.yaml` | `findings` (severity/file/line/summary), `verdict` (approve/blocker), `ratchet_ref` if blocker |

## Verification

```
scripts/validate.sh review-change <path-to-filled-review-result.yaml>
```

PASS when: `verdict` is `approve` or `blocker`; each finding has a `file` reference; verdict is `blocker` whenever there is a finding with severity blocker, and in that case `ratchet_ref` must not be empty. (Uses the same validator as `review-change` — the same kind of finding+verdict artifact, with a different checklist.)

## Next step

If `approve`: continue along with `review-change`, then move to `pr-description`. If `blocker`: go back to `developer` to fix it, then run `verify-change` → security-review again.

## Related

- `skills/security-review/references/checklist.md` — read this before writing a finding
- `rules/security-baseline.yaml`, `rules/protected-paths.yaml` — read these when you need details on a checklist item
- `skills/ratchet-log/SKILL.md` — read this when the verdict is blocker, before writing `ratchet_ref`
- `skills/security-review/examples/` — read these when you need to compare a valid result with an invalid one
