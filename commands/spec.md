---
description: Activate the spec phase — turn a raw request into a task-spec (with impact-analysis/adr if needed).
argument-hint: [description of the request, or a ticket path]
---

Activate the `spec` phase (see `registry/activation-rules.yaml`, id: `spec-phase`) for this request: $ARGUMENTS

- Agent: `solution-architect` if the request has an architecture angle (`agents/solution-architect/agent.md`); `business-analyst` if the business goal/stakeholder/success metric is not clear yet (`agents/business-analyst/agent.md`)
- Skill, in this order, as needed: `feature-roadmap` → `impact-analysis` → `task-spec` → `adr`. When to use each skill is in the "When to use" section of its own `SKILL.md`, it is not repeated here.

Exit gate: `scripts/validate.sh task-spec <path>` PASSES (and `feature-roadmap`/`impact-analysis`/`adr` too, if used). Then move to `/gft:plan`.
