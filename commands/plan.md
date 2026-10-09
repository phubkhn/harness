---
description: Activate the plan phase — review the implementation plan, decide on a test-plan, write an ADR if needed.
argument-hint: [path to task-spec.yaml]
---

Activate the `plan` phase (see `registry/activation-rules.yaml`, id: `plan-phase`) for this task-spec: $ARGUMENTS

- Agent: `solution-architect` (`agents/solution-architect/agent.md`)
- Skill, in this order: `plan-review` → `test-plan` → `adr` (if there is a controversial architecture decision). The full process is in each `SKILL.md`, it is not repeated here.

Exit gate: `scripts/validate.sh plan-review <path>` PASSES with verdict `approved`, and `scripts/validate.sh test-plan <path>` PASSES. Then move to `/gft:execute`.
