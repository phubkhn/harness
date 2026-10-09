# How to write `definition_of_done` for an intake brief

`definition_of_done` is different from `success_metric` (which measures the **business outcome** after the feature ships) and from `open_questions` (points that are still unclear and **not yet** answered). It answers this question: "how do I know this **analysis/intake work itself** is done and ready to move to `/gft:spec`, without guessing or asking from scratch again?"

Write it as a checkable condition, not a vague adjective:

- Good: "Stakeholder Y has confirmed a specific number for `success_metric`", "No `open_question` is still marked blocking", "A concrete example exists for each `acceptance` expected later in the task-spec".
- Bad: "The request is clear enough", "The problem is understood" — these cannot be checked for who/when/how.

If you find it hard to write a specific `definition_of_done`, that is usually a sign this intake is still unclear. Add `open_questions` instead of forcing a vague line.

**Different from `ready_for_spec`**: `definition_of_done` is a self-check list (checklist) for the brief writer to compare against — `validate.sh` only checks that it is not empty, it does not read the content of each line. `ready_for_spec: true` is the **real, machine-checked gate**: setting it `true` while `open_questions` still has an item will FAIL validation. Writing a full `definition_of_done` does not automatically make `ready_for_spec` correct — the two fields are independent. You must set `ready_for_spec` yourself after closing all `open_questions`.
