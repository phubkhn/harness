# skills

This process does not depend on a role. Any agent can use it, at any point in the lifecycle: intake → spec → plan → execute → verify → review. Each skill is a folder with:

- `SKILL.md` — the Claude Code skill format (YAML frontmatter `name`/`description`), with a body that has exactly 6 required headings, checked by `lint_skill_sections()` in `scripts/validate.py`: `## When to use it`, `## Process`, `## Output`, `## Verification`, `## Next step`, `## Related` (see the repo's root CLAUDE.md for details on each one).
- `manifest.yaml` — a machine-checkable contract: the activation phase, the authority level, and how `scripts/validate.sh` checks the skill's output. The `description` here must match the `description` in the `SKILL.md` frontmatter exactly (`lint_description_sync()`).
- `examples/good.<kind>.yaml` and `examples/bad.<kind>.yaml` — runnable examples, not decorative docs. `lint_examples()` runs the real `scripts/validate.sh <kind>` on each file: `good.*` must PASS, and `bad.*` must FAIL with exactly one error that matches the `# expect_fail: ...` comment at the top of the file.
- `references/*.md` (optional) — long checklists or detailed explanations kept separate from `SKILL.md` to keep the skill short (progressive disclosure). `## Related` links to these and says when to read them.
- `evals/smoke.yaml` — declares one minimal sample scenario for the skill (input/situation + expected output). **This is only a scaffold right now**: `scripts/validate.sh` checks that this file exists and has the needed fields, but there is no eval runner yet that actually *runs* the skill with that scenario and compares the result. That needs its own runner (one that calls Claude Code with this skill active, captures the output, and compares it), which has not been built yet.

Add a new skill with `scripts/new_skill.sh <name> "<description>"` (this script also creates `evals/smoke.yaml` for you). Then write all 6 headings and add `examples/good.*`/`bad.*` right away — do not leave this for later.

## Input/output for each skill

| Skill | Phase | Input | Output (template) | Verify with |
|---|---|---|---|---|
| `intake-request` | intake | a raw request/ticket | `intake-brief.yaml`: problem statement, business goal, named stakeholder with a role, success metric, or an open question that explains why there is none yet | `scripts/validate.sh intake-request <file.yaml>` |
| `task-spec` | spec | a raw request | `task-spec.yaml`: outcome, acceptance criteria with stable ids, `allowed_scope`/`protected_scope` that do not overlap, risk tier | `scripts/validate.sh task-spec <file.yaml>` |
| `impact-analysis` | spec | a planned change, suspected to touch many modules/services/projects | `impact-analysis.yaml`: affected components with an impact level + reason, downstream consumers, `rollback_feasible`, risk tier | `scripts/validate.sh impact-analysis <file.yaml>` |
| `adr` | spec, plan | an architecture problem with more than one reasonable way to solve it | `adr.yaml`: at least 2 options, each with at least 1 `cons` (downside), a decision + consequence | `scripts/validate.sh adr <file.yaml>` |
| `plan-review` | plan | task-spec, a proposed implementation plan | `plan-review-result.yaml`: verdict `approved`/`changes-requested`/`escalate`, with findings if not approved directly | `scripts/validate.sh plan-review <file.yaml>` |
| `test-plan` | plan | acceptance criteria from the task-spec | `test-plan.yaml`: each AC has at least 1 test case that refers to it, and there is a case with `covers_negative_path: true` | `scripts/validate.sh test-plan <file.yaml>` |
| `verify-change` | verify | implemented code, task-spec | `verification-result.yaml`: each command has an exit code, each acceptance criterion has a pass/fail result | `scripts/validate.sh verify-change <file.yaml>` |
| `security-review` | verify | diff, task-spec, verification-result | `review-result.yaml` (uses the same format as review-change): security findings + verdict | `scripts/validate.sh review-change <file.yaml>` |
| `review-change` | review | diff, task-spec, verification-result | `review-result.yaml`: findings with a file/line reference, verdict `approve`/`blocker` | `scripts/validate.sh review-change <file.yaml>` |
| `pr-description` | review | task-spec, a passed verification-result, an approved review-result | `pr-description.yaml`: task_id, changed_paths, references to verify/review, breaking_change | `scripts/validate.sh pr-description <file.yaml>` |
| `ratchet-log` | verify, review | a `verification-result.yaml` with a failed AC, or a `review-result.yaml` with verdict blocker | a new entry in the project's `.gft/ratchet-log.yaml`, plus `ratchet_ref` written back into the file that caused the failure | `scripts/validate.sh ratchet-log <file.yaml>` |
| `systematic-debugging` | execute, verify | an error/test failure with no clear cause yet, after at least 1 failed fix attempt | no artifact produced — the root cause + fix are written into the report of the agent that calls this skill (`developer`/`qa-engineer`) | no separate subcommand — `scripts/validate.sh` (with no arguments) confirms that the rules it points to (`testing-quality-gate.yaml`, `evidence-requirements.yaml`) still exist and are valid |
| `using-gft` | not tied to a phase — session-wide, injected through the `SessionStart` hook | a new user request, when it is not clear which skill/agent to use | no artifact produced — the output is a routing decision (which agent/skill is active) for the rest of the session | no separate subcommand — `scripts/validate.sh` (with no arguments) confirms that `registry/activation-rules.yaml`/`capability-catalog.yaml` are consistent (`lint_registry()`) |

`security-review` deliberately reuses the validator and template of `review-change` (`review-result.yaml`) instead of making its own format. The same kind of artifact (finding + verdict) should have only one source of truth. The two skills differ in their review checklist (security vs. correctness/scope), not in the output schema.

`ratchet-log` is enforcement, not a suggestion: `validate_verify_change`/`validate_review_change` in `scripts/validate.py` FAIL right away if there is a failed AC/blocker verdict with no `ratchet_ref`. A failure cannot "disappear" just because the agent did not mention it.

`systematic-debugging` and `using-gft` differ from the other 10 skills in one way: they do not produce an artifact (`output.artifact: null` in `manifest.yaml`). So they have no separate `scripts/validate.sh <kind> <path>` subcommand, and no `examples/good.*`/`bad.*` either (there is nothing to compare good vs. bad without an artifact). "Can be verified" for these two skills means indirect verification: `using-gft` is verified through the consistency of the `registry/` data it reads; `systematic-debugging` is verified through the final fix satisfying `rules/testing-quality-gate.yaml`/`rules/evidence-requirements.yaml`. This does not verify the skill's own behavior — it verifies the result the skill leads to.

## A minimal lockfile for manifest.yaml

Each `manifest.yaml` (for agents and skills) has a `content_hash` field, computed by `scripts/hash_manifest.py` (a sha256 hash of the file's content, excluding the `content_hash` line itself). `scripts/new_skill.sh`/`scripts/new_agent.sh` fill this in automatically when a new one is created. After you edit a `manifest.yaml` by hand, run `make hash-manifests` before you commit. `make validate` fails if the hash does not match, so it can catch a case where a skill/agent's content changed but its `version` did not (silent primitive drift).
