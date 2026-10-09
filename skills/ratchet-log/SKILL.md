---
name: ratchet-log
description: Write an entry into the ratchet-log of the project when verify-change or review-change/security-review finds a failure (a failed acceptance criterion, or a blocker verdict) — turn a failure into institutional memory that accumulates, instead of just retrying until it passes. Use this as soon as `verification-result.yaml` has `result: fail` or `review-result.yaml` has `verdict: blocker`. Do NOT use it to log something that passed on the first try — ratchet-log only records failures, it is not a normal execution log.
---

# ratchet-log

## When to use it

| Situation | Use it? |
|---|---|
| `verify-change` returns at least one `acceptance_results[].result: fail` | Yes |
| `review-change`/`security-review` returns `verdict: blocker` | Yes |
| Verify/review passed on the first try, with no fail/blocker | No — nothing to log |
| You want to log normal change history (not a failure) | No — use `pr-description` or the project's git log, not ratchet-log |

## Process

_Announce before you start. Print this exact line: ``Using `<id-of-this-skill/agent>` to <short purpose>.`` Then do step 1 (details: `rules/announce-convention.yaml`)._

1. **Read `rules/evidence-requirements.yaml` and `rules/safety-invariants.yaml` with the real Read tool** before writing an entry. Knowing a rule's name from text does not mean you have read its content — you must actively Read it. If the file is not at the plain path (the current cwd is the project you are working in, not the plugin root), first resolve the plugin root with `scripts/resolve_plugin_root.sh gft` (see the CLAUDE.md section "Resolve path when the plugin is installed through git"), then Read it by absolute path. Do not conclude a rule does not exist just because it is not at the current cwd.
2. Find the trigger: read the `verification-result.yaml`/`review-result.yaml` just created. If there is no `result: fail` or `verdict: blocker`, STOP — there is nothing to log.
3. Find the current project's `.gft/ratchet-log.yaml` (build it from `templates/ratchet-log.yaml` if the project does not have this file yet).
4. Add a new entry with a stable id (`RATCHET-NNN`), `task_id`, the `phase` where it was found, `failure_class` from the taxonomy (`scope-creep` / `invisible-deletion` / `context-window` / `prompt-satisfaction` / `hallucination` / `consistency` / `other`), `root_cause`, `status: open`, and `owner`.
5. Write the new id into the `ratchet_ref` field of the matching `verification-result.yaml`/`review-result.yaml` — this is required evidence under `rules/evidence-requirements.yaml`, checked by `validate_verify_change`/`validate_review_change`: a fail/blocker without `ratchet_ref` will FAIL.
6. Only move `status` to `regression-added` or `closed` when `control_added` points to a REAL rule/hook/regression-test that already exists — never close an entry just by editing the output to make it pass (stay true to the spirit of `rules/safety-invariants.yaml#no-self-edit`).

## Output

| File | Template | Main content |
|---|---|---|
| `.gft/ratchet-log.yaml` (in the project using the harness, not this harness itself) | `templates/ratchet-log.yaml` | a list of `entries`, each with a stable id, `failure_class`, `root_cause`, `status`, and `control_added` once closed |

## Verification

```
scripts/validate.sh ratchet-log <path-to-.gft/ratchet-log.yaml>
```

PASS when: each entry has a valid `id`/`task_id`/`phase`/`failure_class`/`root_cause`/`status`; an entry with `status` other than `open` must have a non-empty `control_added`.

## Next step

After writing the entry and filling in `ratchet_ref` back in the result file, go back to `/gft:verify` or `/gft:review` to continue the phase in progress — ratchet-log does not move the phase forward on its own.

## Related

- `rules/evidence-requirements.yaml` — read this to find exactly where the `ratchet_ref` field is required
- `rules/safety-invariants.yaml` — read this when unsure whether you can close an entry yourself
- `skills/ratchet-log/examples/` — read this for an example of a valid entry and an invalid one, to compare before validating
