# Checklist review-change

Read this file before you write a finding — this is the full list of items to check, kept separate from `SKILL.md` to keep the skill short.

1. The diff stays inside `allowed_scope` and follows `rules/protected-paths.yaml`.
2. No test has been deleted, disabled, or weakened just to make verification pass (`rules/safety-invariants.yaml`).
3. The verification result has enough evidence per `rules/evidence-requirements.yaml` (exit code, result for each acceptance criterion, etc.), not just a summary like "it passed".
4. If the project belongs to a stack with its own rules (`rules/stacks/`, detected with `scripts/detect_stack.sh`), check the diff against the related convention; a violation becomes a finding.
5. Check the diff against `rules/architecture-principles.yaml`, `rules/error-handling.yaml`, `rules/security-baseline.yaml`, `rules/observability.yaml`, and `rules/testing-quality-gate.yaml`; a violation becomes a finding with severity based on its real-world impact, not the rule's default severity (advisory/blocking).
6. Check `rules/change-management.yaml` (paths outside `allowed_scope`, missing links back to a task-spec/ADR, a breaking change with no migration note).
