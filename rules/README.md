# rules

These are the fixed rules, written in yaml, that every agent, skill, and hook must follow. A rule has higher priority than anything else, except when the user gives clear confirmation for an action under `escalate_paths` (see `context-hierarchy.yaml`).

Do not copy a rule's content into another place (for example, hardcoding a protected path inside a hook script). Read the rule file at run time instead, so there is only one place to change when the rule changes.

## Two kinds of rules

- **General rules** (`rules/*.yaml`, for example `safety-invariants.yaml`) — `severity: blocking`, used for **every** task and every agent/skill, with no condition.
- **Tech stack rules** (`rules/stacks/*.yaml`, for example `java-spring.yaml`) — `severity: advisory`, used only **when the project being worked on uses that exact stack**, decided by the `applies_when` field. See `rules/stacks/README.md` for how to declare this and how detection works (`scripts/detect_stack.sh`).

## Which agent or skill points to which rule

This is a lookup table. The real source of truth is still the actual reference line in each `agent.md`/`SKILL.md` file. Update this table when a reference is added or removed.

| Agent / Skill | context-hierarchy | safety-invariants | evidence-requirements | protected-paths | stacks/* |
|---|:-:|:-:|:-:|:-:|:-:|
| `solution-architect` | ✅ | ✅ | | | ✅ |
| `developer` | | ✅ | ✅ | ✅ | ✅ |
| `qa-engineer` | | ✅ | ✅ | | ✅ |
| `code-reviewer` | | ✅ | ✅ | ✅ | ✅ |
| `task-spec` (skill) | ✅ | | | | |
| `plan-review` (skill) | | ✅ | | ✅ | ✅ |
| `verify-change` (skill) | | | ✅ | | (qua command lint/test) |
| `review-change` (skill) | | ✅ | ✅ | ✅ | ✅ |

The guiding rule is: only point to a rule that is truly relevant to what that role does. Do not add all 8 rules to every file as a blanket rule, because that dilutes the signal — the agent would have to read every rule even when it is not relevant, and it becomes easy to miss the important one.

`announce-convention.yaml` is an intentional exception to this rule. It applies to **every** agent/skill (not to one specific role), so it does not appear in the table above (a column that is all checkmarks carries no signal). Every `SKILL.md`/`agent.md` file has exactly one marker line, right at the start of `## Process`, with the literal announce format already inlined (pointing only to the rule file's path is not enough — real behavior tests showed that, see `tests/skill-behavior/README.md`). The only exception is `skills/using-gft/SKILL.md`, because that skill defines the announce behavior itself, so it explains it in more detail instead of just using the common marker.
