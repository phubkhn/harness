---
name: using-gft
description: Use this when starting any request related to the intake/spec/plan/execute/verify/review SDLC lifecycle of GFT Harness — look up registry/activation-rules.yaml to find the agent/skill that needs to be active before acting, instead of guessing or skipping the routing step.
---

## When to use it

| Situation | Use it? | Why |
|---|---|---|
| Starting a new request that belongs to the SDLC lifecycle (intake, spec, plan, execute, verify, review) | Yes | You must check `registry/activation-rules.yaml` before picking a skill/agent, not guess |
| Already dispatched as a subagent with a specific `agents/<role>/agent.md` for an assigned task | No | That agent already has its own `## Process`, which is self-sufficient — routing again is redundant and could conflict |
| A pure lookup question, with no lifecycle artifact being created/changed (e.g. "explain what file X does") | No | There is no phase to look up — answer directly |
| Not sure if the request belongs to the SDLC lifecycle or not | Yes | Checking the registry is still cheaper than guessing wrong; if no rule matches, treat it as "No" and answer directly |
| The request looks simple at first glance, and you want to ask a quick clarifying question or just answer fast | Yes | "Simple" is not a reason to skip this — checking the registry only costs one step, while answering/asking the wrong skill/agent costs a whole extra loop to fix |
| The user has clearly said in chat that they want to skip this routing step (e.g. "just answer directly, no need to go through a skill/agent") | No | A direct request from the user in the conversation takes priority over forced routing — but only when they have said so clearly, never inferred from silence |

A similar but narrower case: if you already know exactly that you need `task-spec`, `adr`, `verify-change`, etc., call that skill directly — `using-gft` is only needed when it is NOT yet clear which skill/agent to use.

## Process

1. **Gate 1 (subagent)**: if you are already running as a subagent with its own `agent.md` for the current task, STOP — skip this skill, and follow that `agent.md` instead.
2. **Gate 2 (user override)**: if the user has clearly said in chat that they want to skip this routing step (e.g. "just answer directly", "no need for a skill/agent, just do it yourself"), STOP here and follow that direct request exactly — do not infer this from a short or simple-looking question and assume the user wants to skip it. A direct request from the user in the conversation always takes priority over forced routing through a skill/agent, but only when they have said so clearly.
3. Figure out the current phase of the request in the lifecycle `intake -> spec -> plan -> execute -> verify -> review` (based on which artifact already exists: nothing yet → `intake`; an intake-brief exists → `spec`; a task-spec exists → `plan`/`execute`; a diff exists → `verify`/`review`).
4. Look up `registry/activation-rules.yaml`, find the rule whose `when.phase` matches (e.g. `when.phase: execute`), then take the id from the `activate.agents`/`activate.skills` list of **that same rule** (e.g. `activate.agents: [developer]` → the id is `developer`) — **not** the value of `when.phase`.
5. **Announce**: before calling the agent/skill found in step 4, print **exactly one
   line** in this form:

   > Using `<id from activate.agents/activate.skills in step 4>` to <short purpose>.

   A real example: ``Using `intake-request` to turn the raw request into an intake brief.``
   `<id>` **must** be an id registered in `registry/capability-catalog.yaml` (e.g.
   `developer`, `code-reviewer`) — **not** one of these 3 easy-to-confuse things:
   - the **phase** name (`intake`/`spec`/`plan`/`execute`/`verify`/`review`) — that is the value of `when.phase`, not the agent/skill id;
   - Claude Code's technical `subagent_type` when dispatching through the Task tool (in the form `gft:<agent>:<agent>`, e.g. `gft:code-reviewer:code-reviewer`) — that is Claude Code's own internal naming, not the id this harness uses;
   - the id of `using-gft` itself.
   Print this line on its own, separate line — do not merge it into explanatory
   prose. This is a general rule for every skill/agent in the harness (`rules/announce-convention.yaml`),
   not something specific to this routing step; see that rule to learn how to
   handle calling several skills/agents one after another.
6. **Make the real call** to the skill/agent you just announced **before** answering, even when the
   request looks like a simple clarifying question — "make the real call" means:
   - If that id is in `activate.skills` (e.g. `intake-request`, `task-spec`): use the **Skill** tool.
   - If that id is in `activate.agents` (e.g. `developer`, `code-reviewer`): use the **Task** tool with the matching `subagent_type` — **do NOT just role-play as that agent in words and then do the work yourself** (e.g. saying "I will act as the developer role" and then directly using Edit/Write without dispatching through Task). The reason this is required: the full content of that agent's `## Invariants`/`## Process` (including rules it must `Read` before acting) is only loaded into context when Claude Code actually dispatches through the Task tool with the right `subagent_type` — role-playing in words skips all of that content, even if you announced the right id.
   After calling it, that agent/skill follows its own `## Process` (the first
   step of that `## Process` will announce again by the same rule on its own —
   there is no need to announce twice for the same id).
7. If there is a conflict between several sources of guidance (harness rules, project config, task spec, current code), resolve it using the order in `rules/context-hierarchy.yaml` — do not choose based on feeling.
8. Do not try to edit paths listed in `rules/protected-paths.yaml`, even if the task seems to ask for it — the `PreToolUse` hook (`hooks/check-protected-paths`) already blocks this at runtime, so any attempt will be refused anyway.

## Output

This skill does not create its own artifact — the output is a routing decision (which agent/skill is active) that applies to the rest of the session. There is no matching file/template.

## Verification

There is no `<path-to-output>` to check, because this skill produces no artifact. "Checkable" here means that the data source it looks up must be internally consistent: run `scripts/validate.sh` (with no arguments) — if `registry/activation-rules.yaml` activates an agent/skill that no longer exists, or an `agents/*`/`skills/*` on disk is not registered in `registry/capability-catalog.yaml`, this command FAILs right away (`lint_registry()`).

## Next step

After step 4, call the exact agent/skill that the matched rule listed. If there is no lifecycle artifact yet (a completely new start), the default entry point is `intake-request`.

## Related

- `registry/activation-rules.yaml` — read this to look up the active agent/skill by phase; the single source of truth for this mapping.
- `registry/capability-catalog.yaml` — the full list of valid agent/skill ids.
- `rules/context-hierarchy.yaml` — read this when there is a conflict between several sources of guidance.
- `rules/announce-convention.yaml` — the announce format shared by every skill/agent, not just this routing step.
- `rules/protected-paths.yaml` — read this to know which paths are hard-blocked by the hook, so you avoid a pointless attempt.
- `hooks/README.md` — read this when you need to understand which `SessionStart` hook injected this skill's content at the start of the session.
