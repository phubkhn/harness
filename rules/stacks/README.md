# rules/stacks

Tech stack rules (Java/Spring, ReactJS, .NET, Angular...) are different in nature from the rules in `rules/*.yaml` (general NFRs like `safety-invariants.yaml`): an NFR applies to **every** task, while a stack rule only applies **when the project being worked on actually uses that stack**.

## Structure of a stack rule

```yaml
id: stack-java-spring
version: 1.0.0
description: Conventions used when a project uses Java + Spring.
severity: advisory        # advisory, not blocking — this is a convention, not a safety invariant
applies_to: [agent, skill]
applies_when:
  paths:                  # required: at least 1 glob pattern, matched against a path in the project BEING WORKED ON (not this harness)
    - "**/pom.xml"
    - "**/build.gradle"
  contains:                # optional: use this when the path alone cannot tell the stack apart (for example, package.json is shared by React/Angular/Vue)
    - path: "**/package.json"
      pattern: "\"react\":"
statements:
  - id: ...
    text: ...
```

## How "apply" works — 2 levels, do not mix them up

1. **Declared level (always true)**: `applies_when` is data that describes *when this rule is relevant*. `scripts/validate.sh` only checks that `applies_when.paths` exists and is not empty — it does not run detection itself.
2. **Real detection level (`scripts/detect_stack.sh <project-dir>`)**: this scans the folder tree of the **project being worked on** (not the harness), matches `applies_when.paths`/`applies_when.contains` from each file in `rules/stacks/*.yaml`, and prints which stack matches. This is the step an agent (especially `solution-architect` and `developer`) should run at the start of a task, to know which stack rule to read next. No hook blocks anything automatically based on a stack rule (unlike `protected-paths.yaml`), because this is a convention, not a hard safety rule.

## Adding a new stack

```bash
scripts/new_stack_rule.sh <stack-name> "<description>"
```
This generates `rules/stacks/<stack-name>.yaml` following the structure above. Edit `applies_when.paths`/`statements`, then run `scripts/validate.sh`.
