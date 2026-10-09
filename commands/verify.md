---
description: Activate the verify phase — run empirical proof (qa-engineer) and a security review (security-reviewer).
argument-hint: [path to task-spec.yaml + the diff to verify]
---

Activate the `verify` phase (see `registry/activation-rules.yaml`, id: `verify-phase`) for: $ARGUMENTS

- Agent: `qa-engineer` (`agents/qa-engineer/agent.md`), runs skill `verify-change`
- Agent: `security-reviewer` (`agents/security-reviewer/agent.md`) if the diff touches `escalate_paths` (`rules/protected-paths.yaml`) or has a high risk tier, runs skill `security-review`
- If any acceptance criterion fails, or the verdict is blocker, run skill `ratchet-log` — this is required, not optional.
- Skill `systematic-debugging` (`skills/systematic-debugging/SKILL.md`) — not a fixed step, only use it when a check fails and the cause is not clear right away.

Exit gate: `scripts/validate.sh verify-change <path>` PASSES; if security-review ran, `scripts/validate.sh review-change <path>` must also PASS. Then move to `/gft:review`.
