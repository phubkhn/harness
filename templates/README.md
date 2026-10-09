# templates

Pre-filled yaml templates (copy-and-fill) for the artifacts that a skill/agent creates: `task-spec.yaml`, `adr.yaml`, `plan-review-result.yaml`, `review-result.yaml`, `verification-result.yaml`. A filled-in version is checked with `scripts/validate.sh <type> <file>` — see each skill's `manifest.yaml` for the exact command to run (the `output.template` field points to the matching template file).

`ratchet-log.yaml` is not tied to one skill in a specific phase. It is tied to the **project that uses the harness** (like `project-config.yaml`), and lives at `.gft/ratchet-log.yaml` in that project. You must fill it in — it is not optional — any time `verify-change` has a failing AC, or `review-change`/`security-review` has a `blocker` verdict (see `skills/ratchet-log/SKILL.md`). Check it with `scripts/validate.sh ratchet-log <file>`.

(We considered and dropped two templates, `run-record.yaml`/`pilot-baseline.yaml` — they had a schema/validator, but no skill/command/script actually created or needed them, so the artifact existed but nobody used it. By the rule of failure-driven improvement, we will add them back only when a real pilot run shows we need to measure a baseline/run trace.)
