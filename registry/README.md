# registry

This is the coordination layer. It is separate from the content (`agents/`, `skills/`) and from the constraints (`rules/`):

- `capability-catalog.yaml` — the full list of agents and skills that exist. `scripts/validate.sh` checks that this list matches the real folders, in both directions. This way, a new skill or agent can never stay unregistered by mistake, and an old catalog entry can never outlive the folder it points to after that folder is deleted.
- `activation-rules.yaml` — maps each lifecycle phase (`spec`/`plan`/`execute`/`verify`/`review`) to the agents and skills that must be active in that phase. This is the only place that answers "who runs in phase X". It is cross-checked against `activation.phases` in each `manifest.yaml`, instead of being copied by hand into every agent/skill file.

When you add a new agent or skill, update both files at the same time: register it in `capability-catalog.yaml`, then add or extend a rule in `activation-rules.yaml` for the phase (or phases) it needs to run in. `make validate` will fail if you forget either step.

Exception: a skill that is not tied to a specific phase (for example `using-gft`, which is session-wide and is injected directly by the `SessionStart` hook instead of going through `activation-rules.yaml`) only needs to be registered in `capability-catalog.yaml`. It does not need to appear in any rule in `activation-rules.yaml`. The `lint_registry()` check only checks the other direction: every id that an activation rule activates must exist in the catalog. It does not check that every id in the catalog must be activated by some rule.
