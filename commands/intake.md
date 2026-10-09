---
description: Activate the intake phase — turn a raw request/ticket into an intake brief before writing a task-spec.
argument-hint: [description of the raw request, or a ticket path]
---

Activate the `intake` phase (see `registry/activation-rules.yaml`, id: `intake-phase`) for this request: $ARGUMENTS

- Agent: `business-analyst` (`agents/business-analyst/agent.md`)
- Skill: `intake-request` (`skills/intake-request/SKILL.md`) — the full process is there, it is not repeated here.

Exit gate: `scripts/validate.sh intake-request <path>` PASSES. Then move to `/gft:spec` (or `/gft:spec` will run `feature-roadmap` on its own if the feature is big enough).
