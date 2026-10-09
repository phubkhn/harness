---
description: Activate the execute phase — the developer implements inside the approved scope.
argument-hint: [path to an approved task-spec.yaml]
---

Activate the `execute` phase (see `registry/activation-rules.yaml`, id: `execute-phase`) for this task-spec: $ARGUMENTS

- Agent: `developer` (`agents/developer/agent.md`) — the full process (including the definition-of-ready gate in step 0) is there, it is not repeated here.

Skill: `systematic-debugging` (`skills/systematic-debugging/SKILL.md`) — not a fixed step, only use it when implementation hits an error/failing test and the cause is not clear right away (see "When to use" in that `SKILL.md`).

Exit gate: `agents/developer/agent.md#Verification` — hand off to `verify-change`/`review-change`, the developer does not certify its own work. Then move to `/gft:verify`.
