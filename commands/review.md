---
description: Activate the review phase — an independent, read-only review (code-reviewer, security-reviewer), then create a pr-description.
argument-hint: [path to the diff + a passing verification-result]
---

Activate the `review` phase (see `registry/activation-rules.yaml`, id: `review-phase`) for: $ARGUMENTS

- Agent: `code-reviewer` (`agents/code-reviewer/agent.md`), runs skill `review-change`
- Agent: `security-reviewer` (`agents/security-reviewer/agent.md`) if the `verify` phase already activated it, or the diff touches escalate_paths, runs skill `security-review`
- If any `verdict: blocker` appears, run skill `ratchet-log` — this is required.
- Only when EVERY verdict is `approve`, run skill `pr-description`.

Exit gate: `scripts/validate.sh review-change <path>` PASSES with verdict `approve`, then `scripts/validate.sh pr-description <path>` PASSES.
