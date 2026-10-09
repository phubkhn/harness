#!/usr/bin/env python3
"""A minimal validator, with no outside library dependency, for the GFT harness.

Usage:
  scripts/validate.py                          # checks the structure of the whole harness
  scripts/validate.py task-spec <file.yaml>
  scripts/validate.py scope-amendment <file.yaml>  # extends a task-spec that is already running, see templates/scope-amendment.yaml
  scripts/validate.py adr <file.yaml>
  scripts/validate.py plan-review <file.yaml>
  scripts/validate.py verify-change <file.yaml>
  scripts/validate.py review-change <file.yaml>
  scripts/validate.py test-plan <file.yaml>
  scripts/validate.py impact-analysis <file.yaml>
  scripts/validate.py pr-description <file.yaml>
  scripts/validate.py project-config <file.yaml>   # .gft/project.yaml of a project that uses the harness
  scripts/validate.py ratchet-log <file.yaml>      # .gft/ratchet-log.yaml of a project that uses the harness
  scripts/validate.py agent-output <role> <file.md>

Exit code 0 = pass, 1 = fail. No third-party library dependency.
"""
import sys
import json
import re
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import minimal_yaml as yaml  # noqa: E402  (a small self-written parser, no outside library dependency)
import hash_manifest as manifest_hash  # noqa: E402  (a minimal lockfile for manifest.yaml)

ROOT = Path(__file__).resolve().parent.parent
FAILURES = []


def fail(msg):
    FAILURES.append(msg)


def load_yaml(path):
    return yaml.safe_load(Path(path).read_text())


def parse_frontmatter(path):
    text = Path(path).read_text()
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not m:
        return {}
    return yaml.safe_load(m.group(1)) or {}


# ---- structural lint -------------------------------

def lint_skills():
    for d in sorted((ROOT / "skills").iterdir()):
        if not d.is_dir():
            continue
        skill_md = d / "SKILL.md"
        manifest = d / "manifest.yaml"
        if not skill_md.exists():
            fail(f"skills/{d.name}: missing SKILL.md")
            continue
        fm = parse_frontmatter(skill_md)
        for key in ("name", "description"):
            if not fm.get(key):
                fail(f"skills/{d.name}/SKILL.md: missing frontmatter field '{key}'")
        if not manifest.exists():
            fail(f"skills/{d.name}: missing manifest.yaml")
            continue
        data = load_yaml(manifest) or {}
        for key in ("id", "type", "version", "owner", "description"):
            if not data.get(key):
                fail(f"skills/{d.name}/manifest.yaml: missing field '{key}'")


def lint_agents():
    for d in sorted((ROOT / "agents").iterdir()):
        if not d.is_dir():
            continue
        agent_md = d / "agent.md"
        manifest = d / "manifest.yaml"
        if not agent_md.exists():
            fail(f"agents/{d.name}: missing agent.md")
            continue
        fm = parse_frontmatter(agent_md)
        for key in ("name", "description"):
            if not fm.get(key):
                fail(f"agents/{d.name}/agent.md: missing frontmatter field '{key}'")
        if not manifest.exists():
            fail(f"agents/{d.name}: missing manifest.yaml")
            continue
        data = load_yaml(manifest) or {}
        for key in ("id", "type", "version", "owner", "description", "authority"):
            if not data.get(key):
                fail(f"agents/{d.name}/manifest.yaml: missing field '{key}'")


# The required section contract for SKILL.md/agent.md (see CLAUDE.md). Every
# skill/agent that exists today already follows it — when adding a new
# skill/agent, write all 6 headings from the start, do not add an exemption
# mechanism again.
_SKILL_REQUIRED_SECTIONS = (
    "## When to use it", "## Process", "## Output",
    "## Verification", "## Next step", "## Related",
)
_AGENT_REQUIRED_SECTIONS = (
    "## Required Input", "## Invariants", "## Process",
    "## Do Not", "## Output to the Caller", "## Verification",
)


def _lint_section_contract(dirname, required_sections, filename):
    for d in sorted((ROOT / dirname).iterdir()):
        if not d.is_dir():
            continue
        f = d / filename
        if not f.exists():
            continue
        text = f.read_text()
        for section in required_sections:
            if section not in text:
                fail(f"{dirname}/{d.name}/{filename}: missing required heading '{section}'")


def lint_skill_sections():
    _lint_section_contract("skills", _SKILL_REQUIRED_SECTIONS, "SKILL.md")


def lint_agent_sections():
    _lint_section_contract("agents", _AGENT_REQUIRED_SECTIONS, "agent.md")


# An explicit mapping between the 'tools:' vocabulary in agent.md (Claude
# Code's subagent frontmatter) and the 'allowed_tools' vocabulary in
# manifest.yaml. No implicit guessing — adding a new tool means adding a
# line here first.
_TOOLS_VOCAB = {
    "Read": "read",
    "Grep": "search",
    "Glob": "search",
    "Bash": "shell",
    "Edit": "write",
    "Write": "write",
}


def lint_tools_vocabulary():
    for d in sorted((ROOT / "agents").iterdir()):
        if not d.is_dir():
            continue
        agent_md = d / "agent.md"
        manifest = d / "manifest.yaml"
        if not agent_md.exists() or not manifest.exists():
            continue
        fm = parse_frontmatter(agent_md)
        tools_raw = fm.get("tools") or ""
        tools = [t.strip() for t in str(tools_raw).split(",") if t.strip()]
        unknown = [t for t in tools if t not in _TOOLS_VOCAB]
        if unknown:
            fail(f"agents/{d.name}/agent.md: tool(s) not yet in _TOOLS_VOCAB: {unknown}")
            continue
        expected = {_TOOLS_VOCAB[t] for t in tools}
        data = load_yaml(manifest) or {}
        allowed = set(data.get("allowed_tools") or [])
        missing = expected - allowed
        if missing:
            fail(
                f"agents/{d.name}: agent.md declares tools that need {sorted(missing)} "
                f"but manifest.yaml allowed_tools only has {sorted(allowed)}"
            )


def lint_agent_markers():
    """agent.md must still mention the English marker that
    validate_agent_output() greps for in the agent's real output (see
    AGENT_OUTPUT_MARKERS) — if agent.md stops mentioning it, the agent will
    not know to put that word in its output, and validate_agent_output will
    always fail in a confusing way."""
    for role, markers in AGENT_OUTPUT_MARKERS.items():
        agent_md = ROOT / "agents" / role / "agent.md"
        if not agent_md.exists():
            continue
        text = agent_md.read_text().lower()
        for marker in markers:
            if marker not in text:
                fail(
                    f"agents/{role}/agent.md: missing marker '{marker}' that "
                    "validate_agent_output() needs to see in the real output — do not translate or remove this word"
                )


def lint_description_sync():
    """The frontmatter 'description' in SKILL.md/agent.md and the manifest
    'description' must match exactly — two different copies are two sources
    of truth, and one of them will drift over time if lint does not catch
    it. Changing the description means changing both files at the same
    time, on purpose (see CLAUDE.md)."""
    for kind, filename in (("skills", "SKILL.md"), ("agents", "agent.md")):
        for d in sorted((ROOT / kind).iterdir()):
            if not d.is_dir():
                continue
            src = d / filename
            manifest = d / "manifest.yaml"
            if not src.exists() or not manifest.exists():
                continue
            fm_desc = parse_frontmatter(src).get("description")
            manifest_desc = (load_yaml(manifest) or {}).get("description")
            if fm_desc != manifest_desc:
                fail(
                    f"{kind}/{d.name}: description in {filename} and manifest.yaml do not match — "
                    "change both files at the same time, then run `make hash-manifests`"
                )


def lint_rules():
    for f in sorted((ROOT / "rules").rglob("*.yaml")):
        rel = f.relative_to(ROOT)
        data = load_yaml(f) or {}
        for key in ("id", "version", "description", "severity"):
            if not data.get(key):
                fail(f"{rel}: missing field '{key}'")
        applies_when = data.get("applies_when")
        if applies_when is not None:
            paths = applies_when.get("paths") if isinstance(applies_when, dict) else None
            if not paths:
                fail(f"{rel}: applies_when must have at least one pattern in 'paths'")


def lint_templates():
    for f in sorted((ROOT / "templates").glob("*.yaml")):
        try:
            load_yaml(f)
        except Exception as e:  # the self-written parser has no dedicated exception type
            fail(f"templates/{f.name}: invalid YAML ({e})")


def lint_evals():
    # evals/smoke.yaml is a scaffold declaring an example scenario — there is
    # NO eval runner yet that runs it. We only check that it exists and has
    # enough fields, so it does not drift or go missing when a new skill or
    # agent is added.
    for kind, key in (("skills", "skill"), ("agents", "agent")):
        for d in sorted((ROOT / kind).iterdir()):
            if not d.is_dir():
                continue
            eval_file = d / "evals" / "smoke.yaml"
            if not eval_file.exists():
                fail(f"{kind}/{d.name}: missing evals/smoke.yaml")
                continue
            data = load_yaml(eval_file) or {}
            for field in ("id", key, "scenario", "expected", "status"):
                if not data.get(field):
                    fail(f"{kind}/{d.name}/evals/smoke.yaml: missing field '{field}'")
            if data.get(key) not in (None, d.name):
                fail(
                    f"{kind}/{d.name}/evals/smoke.yaml: field '{key}' must be "
                    f"'{d.name}', got '{data.get(key)}'"
                )


_EXAMPLE_EXPECT_FAIL_RE = re.compile(r"^#\s*expect_fail:\s*(.+)$", re.MULTILINE)
_VALIDATE_COMMAND_RE = re.compile(r"scripts/validate\.sh\s+(\S+)")


def lint_examples():
    """Runs the REAL scripts/validate.sh (as a subprocess) for every
    skills/<name>/examples/{good,bad}.*.yaml — this turns the examples into
    a real test for the validator itself, instead of just decorative
    documentation.

    It deliberately shells out instead of calling validate_*() in-process:
    FAILURES is a module-level global variable that fail() only appends to,
    with no place that resets it — calling the validate function directly
    here would leak bad.yaml's INTENTIONAL error into the error list of the
    current `make validate` run itself.
    """
    validate_sh = ROOT / "scripts" / "validate.sh"
    for d in sorted((ROOT / "skills").iterdir()):
        if not d.is_dir():
            continue
        examples_dir = d / "examples"
        if not examples_dir.exists():
            continue
        manifest = d / "manifest.yaml"
        if not manifest.exists():
            continue
        data = load_yaml(manifest) or {}
        command = (data.get("verification") or {}).get("command") or ""
        m = _VALIDATE_COMMAND_RE.search(command)
        if not m:
            fail(
                f"skills/{d.name}/manifest.yaml: verification.command is not in the form "
                "'scripts/validate.sh <kind> ...' needed for lint_examples to work out the kind"
            )
            continue
        kind = m.group(1)

        template_rel = (data.get("output") or {}).get("template")
        template_keys = None
        if template_rel:
            template_path = ROOT / template_rel
            if template_path.exists():
                template_keys = set((load_yaml(template_path) or {}).keys())

        for f in sorted(examples_dir.glob("good.*")):
            proc = subprocess.run(
                [str(validate_sh), kind, str(f)], capture_output=True, text=True
            )
            if proc.returncode != 0:
                fail(f"skills/{d.name}/examples/{f.name}: should PASS ({kind}) but FAILED:\n{proc.stdout.strip()}")
            if template_keys is not None:
                good_keys = set((load_yaml(f) or {}).keys())
                missing = template_keys - good_keys
                if missing:
                    fail(
                        f"skills/{d.name}/examples/{f.name}: missing a key that is in the "
                        f"template ({template_rel}): {sorted(missing)} — the template/validator may have drifted apart"
                    )

        for f in sorted(examples_dir.glob("bad.*")):
            text = f.read_text()
            em = _EXAMPLE_EXPECT_FAIL_RE.search(text)
            if not em:
                fail(f"skills/{d.name}/examples/{f.name}: missing the comment '# expect_fail: <reason>' at the top of the file")
                continue
            expect = em.group(1).strip()
            proc = subprocess.run(
                [str(validate_sh), kind, str(f)], capture_output=True, text=True
            )
            if proc.returncode == 0:
                fail(f"skills/{d.name}/examples/{f.name}: should FAIL ({kind}) but PASSED instead")
                continue
            error_lines = [ln for ln in proc.stdout.splitlines() if ln.strip().startswith("- ")]
            if len(error_lines) != 1:
                fail(
                    f"skills/{d.name}/examples/{f.name}: must fail with exactly ONE error, to be sure "
                    f"it fails for the reason stated in expect_fail, but got {len(error_lines)} errors:\n{proc.stdout.strip()}"
                )
                continue
            if expect not in error_lines[0]:
                fail(
                    f"skills/{d.name}/examples/{f.name}: the real error does not match expect_fail "
                    f"({expect!r}): {error_lines[0].strip()!r}"
                )


def lint_hooks():
    hooks_json = ROOT / "hooks" / "hooks.json"
    if hooks_json.exists():
        try:
            json.loads(hooks_json.read_text())
        except json.JSONDecodeError as e:
            fail(f"hooks/hooks.json: invalid JSON ({e})")


def lint_mcp():
    # Checks that every *.mcp.json file in mcp/ (including the example, and
    # the real .mcp.json if there is one at the repo root) is valid JSON and
    # that every server declares a command.
    candidates = list((ROOT / "mcp").glob("*.mcp.json"))
    root_mcp = ROOT / ".mcp.json"
    if root_mcp.exists():
        candidates.append(root_mcp)
    for f in candidates:
        rel = f.relative_to(ROOT)
        try:
            data = json.loads(f.read_text())
        except json.JSONDecodeError as e:
            fail(f"{rel}: invalid JSON ({e})")
            continue
        servers = data.get("mcpServers") or {}
        if not servers:
            fail(f"{rel}: missing or empty 'mcpServers'")
        for name, server in servers.items():
            if not server.get("command"):
                fail(f"{rel}: server '{name}' is missing field 'command'")


def lint_commands():
    # commands/*.md are Claude Code slash-command entry points — thin
    # wrappers pointing to a phase/skill registered in registry/. This only
    # checks the minimal structure (frontmatter has 'description'); whether
    # the wrapper content matches the right phase is the writer's
    # responsibility, and is outside the scope of this structural lint.
    commands_dir = ROOT / "commands"
    if not commands_dir.exists():
        return
    for f in sorted(commands_dir.glob("*.md")):
        if f.name == "README.md":
            continue
        fm = parse_frontmatter(f)
        if not fm.get("description"):
            fail(f"commands/{f.name}: missing frontmatter field 'description'")


_NEXT_STEP_TOKEN_RE = re.compile(r"`([a-z][a-z0-9-]*[a-z0-9])`")
# Enum values (verdict/status) used in artifacts — they look like a
# kebab-case id but are not the name of any skill/agent, so they are
# excluded explicitly instead of being guessed with some other heuristic.
_NEXT_STEP_ENUM_EXCLUDE = {
    "approve", "approved", "blocker", "changes-requested", "escalate",
    "single", "staged", "pass", "fail", "open", "closed", "regression-added",
}


def lint_next_step():
    """Every kebab-case id inside backticks in the '## Next step' section
    of a SKILL.md must exist in registry/capability-catalog.yaml (as a skill
    or an agent) — this catches a typo, or a reference to a skill that was
    renamed or deleted, instead of silently pointing to a name that no
    longer exists."""
    catalog_file = ROOT / "registry" / "capability-catalog.yaml"
    if not catalog_file.exists():
        return
    catalog = load_yaml(catalog_file) or {}
    known_ids = set(catalog.get("agents") or []) | set(catalog.get("skills") or [])
    for d in sorted((ROOT / "skills").iterdir()):
        if not d.is_dir():
            continue
        skill_md = d / "SKILL.md"
        if not skill_md.exists():
            continue
        text = skill_md.read_text()
        m = re.search(r"^## Next step\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
        if not m:
            continue
        section = m.group(1)
        for token in _NEXT_STEP_TOKEN_RE.findall(section):
            if token in _NEXT_STEP_ENUM_EXCLUDE:
                continue
            if token not in known_ids:
                fail(
                    f"skills/{d.name}/SKILL.md: '## Next step' mentions "
                    f"'{token}' but this id is not in registry/capability-catalog.yaml"
                )


def lint_registry():
    catalog_file = ROOT / "registry" / "capability-catalog.yaml"
    rules_file = ROOT / "registry" / "activation-rules.yaml"
    if not catalog_file.exists() or not rules_file.exists():
        fail("registry/: both capability-catalog.yaml and activation-rules.yaml must exist")
        return

    catalog = load_yaml(catalog_file) or {}
    catalog_agents = set(catalog.get("agents") or [])
    catalog_skills = set(catalog.get("skills") or [])

    actual_agents = {d.name for d in (ROOT / "agents").iterdir() if d.is_dir()}
    actual_skills = {d.name for d in (ROOT / "skills").iterdir() if d.is_dir()}

    for missing in actual_agents - catalog_agents:
        fail(f"registry/capability-catalog.yaml: agents/{missing} exists but is not registered")
    for stale in catalog_agents - actual_agents:
        fail(f"registry/capability-catalog.yaml: agent '{stale}' is registered but agents/{stale} does not exist")
    for missing in actual_skills - catalog_skills:
        fail(f"registry/capability-catalog.yaml: skills/{missing} exists but is not registered")
    for stale in catalog_skills - actual_skills:
        fail(f"registry/capability-catalog.yaml: skill '{stale}' is registered but skills/{stale} does not exist")

    activation = load_yaml(rules_file) or {}
    for rule in activation.get("rules") or []:
        activate = rule.get("activate") or {}
        for agent_id in activate.get("agents") or []:
            if agent_id not in catalog_agents:
                fail(f"registry/activation-rules.yaml: rule '{rule.get('id')}' activates unknown agent '{agent_id}'")
        for skill_id in activate.get("skills") or []:
            if skill_id not in catalog_skills:
                fail(f"registry/activation-rules.yaml: rule '{rule.get('id')}' activates unknown skill '{skill_id}'")


def lint_codeowners():
    """CODEOWNERS at the repo root must mirror rules/protected-paths.yaml
    (the 'paths' field, not escalate_paths) — it must not be hardcoded on
    its own. This is a loose check: each protected path must appear in some
    form (with the '**'/'*' characters removed to compare the bare path) in
    a line of CODEOWNERS."""
    codeowners = ROOT / "CODEOWNERS"
    protected_file = ROOT / "rules" / "protected-paths.yaml"
    if not protected_file.exists():
        return
    if not codeowners.exists():
        fail("CODEOWNERS: file is missing at the repo root — see rules/protected-paths.yaml")
        return
    protected = load_yaml(protected_file) or {}
    paths = protected.get("paths") or []
    owners_text = codeowners.read_text()
    owners_lines = [
        line.split()[0]
        for line in owners_text.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    def normalize(p):
        return p.strip("/").replace("**", "").replace("*", "").rstrip("/")

    normalized_lines = [normalize(line) for line in owners_lines]
    for p in paths:
        np = normalize(p)
        if not any(np == nl or np.startswith(nl) or nl.startswith(np) for nl in normalized_lines if nl):
            fail(
                f"CODEOWNERS: missing a line for protected path '{p}' (declared in rules/protected-paths.yaml) "
                "— add a matching line, do not just change protected-paths.yaml"
            )


def lint_manifest_hashes():
    """Every agents/*/manifest.yaml and skills/*/manifest.yaml must have a
    content_hash field that matches the current content (see
    scripts/hash_manifest.py) — a minimal lockfile against silent primitive
    drift. If it is missing or does not match, run `make hash-manifests`
    then commit again."""
    for kind in ("agents", "skills"):
        for d in sorted((ROOT / kind).iterdir()):
            if not d.is_dir():
                continue
            manifest = d / "manifest.yaml"
            if not manifest.exists():
                continue
            stored = manifest_hash.stored_hash(manifest)
            if not stored:
                fail(f"{kind}/{d.name}/manifest.yaml: missing field 'content_hash' — run `make hash-manifests`")
                continue
            computed = manifest_hash.compute_hash(manifest)
            if stored != computed:
                fail(
                    f"{kind}/{d.name}/manifest.yaml: content_hash does not match the current content "
                    "— run `make hash-manifests` then commit again"
                )


def run_lint():
    lint_skills()
    lint_agents()
    lint_skill_sections()
    lint_agent_sections()
    lint_tools_vocabulary()
    lint_agent_markers()
    lint_examples()
    lint_evals()
    lint_rules()
    lint_templates()
    lint_hooks()
    lint_mcp()
    lint_commands()
    lint_next_step()
    lint_description_sync()
    lint_registry()
    lint_codeowners()
    lint_manifest_hashes()


# ---- validator for each artifact type -----------------------------------

def validate_task_spec(path):
    data = load_yaml(path) or {}
    for key in ("outcome", "risk_tier", "allowed_scope", "protected_scope", "acceptance_criteria"):
        if not data.get(key):
            fail(f"{path}: missing or empty field '{key}'")
    ac = data.get("acceptance_criteria") or []
    if not isinstance(ac, list) or len(ac) == 0:
        fail(f"{path}: acceptance_criteria must be a non-empty list")
    else:
        for item in ac:
            if not item.get("id"):
                fail(f"{path}: an item in acceptance_criteria is missing 'id'")
    allowed = set(data.get("allowed_scope") or [])
    protected = set(data.get("protected_scope") or [])
    overlap = allowed & protected
    if overlap:
        fail(f"{path}: allowed_scope and protected_scope overlap: {overlap}")


VALID_SCOPE_AMENDMENT_KINDS = {"scope", "acceptance_criteria", "constraint"}
VALID_SCOPE_AMENDMENT_STATUS = {"approved", "rejected", "pending"}


def validate_scope_amendment(path):
    """H-04 (pilot): an agent must not edit its own task-spec/AC
    (rules/safety-invariants.yaml#no-self-edit), even with permission — the
    change must live in a separate file following
    templates/scope-amendment.yaml. It is not tied to a specific skill,
    following the precedent of `project-config` (which also has only a
    template + a validator, and no dedicated skill)."""
    data = load_yaml(path) or {}
    for key in ("task_id", "amendment_id", "kind", "reason", "approved_by", "approved_at", "status"):
        if not data.get(key):
            fail(f"{path}: missing or empty field '{key}'")
    kind = data.get("kind")
    if kind and kind not in VALID_SCOPE_AMENDMENT_KINDS:
        fail(f"{path}: kind must be one of {sorted(VALID_SCOPE_AMENDMENT_KINDS)}, got {kind!r}")
    status = data.get("status")
    if status and status not in VALID_SCOPE_AMENDMENT_STATUS:
        fail(f"{path}: status must be one of {sorted(VALID_SCOPE_AMENDMENT_STATUS)}, got {status!r}")
    group_by_kind = {
        "scope": "additional_allowed_paths",
        "acceptance_criteria": "additional_acceptance_criteria",
        "constraint": "additional_constraints",
    }
    expected_group = group_by_kind.get(kind)
    if expected_group and not (data.get(expected_group) or []):
        fail(f"{path}: kind='{kind}' but '{expected_group}' is empty — this amendment changes nothing")
    if status == "approved" and not data.get("approved_by"):
        fail(f"{path}: status=approved but approved_by is missing")


def validate_adr(path):
    data = load_yaml(path) or {}
    for key in ("title", "context", "options", "decision"):
        if not data.get(key):
            fail(f"{path}: missing or empty field '{key}'")
    for opt in data.get("options") or []:
        if not opt.get("cons"):
            fail(f"{path}: option '{opt.get('name', '?')}' lists no downside yet (cons)")


def validate_plan_review(path):
    data = load_yaml(path) or {}
    verdict = data.get("verdict")
    if verdict not in ("approved", "changes-requested", "escalate"):
        fail(f"{path}: verdict must be one of approved/changes-requested/escalate, got {verdict!r}")
    if verdict in ("changes-requested", "escalate") and not data.get("findings"):
        fail(f"{path}: verdict '{verdict}' requires at least one finding")

    _check_plan_review_rounds(path, data, verdict)

    if verdict == "approved":
        _check_task_spec_not_self_edited(path, data)


def _check_plan_review_rounds(path, data, verdict):
    """H-03 (pilot): previously, "went through N rounds of independent
    review" was only prose narration in an .md file that validate.sh never
    checked — there was no way to tell a real multi-round review apart from
    approving right away and then making up a history. If the skill writes
    `rounds`, every round is held to the same rule the final round is still
    held to (changes-requested/escalate must have a finding), and the final
    round must match the verdict at the top of the file — the history must
    not tell a story different from the final result."""
    rounds = data.get("rounds") or []
    if not rounds:
        return
    for r in rounds:
        r_verdict = r.get("verdict")
        if r_verdict not in ("approved", "changes-requested", "escalate"):
            fail(f"{path}: rounds[{r.get('round_no', '?')}].verdict must be approved/changes-requested/escalate, got {r_verdict!r}")
            continue
        if r_verdict in ("changes-requested", "escalate") and not r.get("findings"):
            fail(f"{path}: rounds[{r.get('round_no', '?')}] verdict '{r_verdict}' requires at least one finding")
    last_verdict = rounds[-1].get("verdict")
    if last_verdict != verdict:
        fail(
            f"{path}: the verdict at the top of the file ({verdict!r}) does not match the verdict of the last round in 'rounds' "
            f"({last_verdict!r}) — the history must reflect the real final result"
        )


def _check_task_spec_not_self_edited(review_path, review_data):
    """H-04 (pilot): turns the no-self-edit invariant from prose into
    something machine-checkable. plan-review snapshots the task-spec's hash
    at the moment of approval; if the task-spec has changed since then with
    no scope_amendments (status: approved) explaining it, this is treated
    as a suspected self-edit. It cannot prove EXACTLY which diff matches
    which amendment — this is a deliberate limit, traded for simplicity,
    not a full semantic diff mechanism."""
    task_spec_ref = review_data.get("task_spec_ref")
    task_spec_hash = review_data.get("task_spec_hash")
    if not task_spec_ref or not task_spec_hash:
        fail(
            f"{review_path}: verdict is approved but task_spec_ref/task_spec_hash is missing — "
            "a snapshot of the task-spec hash at approval time is needed (scripts/hash_manifest.py compute <task_spec_ref>)"
        )
        return
    spec_path = Path(task_spec_ref)
    if not spec_path.is_file():
        fail(f"{review_path}: task_spec_ref '{task_spec_ref}' does not exist (resolved from the directory validate.sh is run in)")
        return
    current_hash = manifest_hash.compute_hash(spec_path)
    if current_hash == task_spec_hash:
        return
    spec_data = load_yaml(spec_path) or {}
    amendments = spec_data.get("scope_amendments") or []
    if not amendments:
        fail(
            f"{review_path}: task-spec '{task_spec_ref}' content changed after plan-review approved it "
            f"(hash at approval={task_spec_hash[:12]}…, current={current_hash[:12]}…) and there are no "
            "scope_amendments explaining it — suspected self-edit of the task-spec (rules/safety-invariants.yaml#no-self-edit)"
        )
        return
    for amend_ref in amendments:
        amend_path = Path(amend_ref)
        if not amend_path.is_file():
            fail(f"{review_path}: scope_amendments in '{task_spec_ref}' points to '{amend_ref}' which does not exist")
            continue
        amend_data = load_yaml(amend_path) or {}
        if amend_data.get("status") != "approved":
            fail(
                f"{review_path}: scope_amendment '{amend_ref}' has status={amend_data.get('status')!r}, "
                "it needs to be 'approved' to explain a task-spec change after plan-review has approved it"
            )


def validate_verify_change(path):
    data = load_yaml(path) or {}
    commands = data.get("commands") or []
    if not commands:
        fail(f"{path}: commands must be a non-empty list")
    for c in commands:
        if c.get("exit_code") is None:
            fail(f"{path}: command '{c.get('command', '?')}' is missing exit_code")
    results = data.get("acceptance_results") or []
    if not results:
        fail(f"{path}: acceptance_results must be a non-empty list")
    has_fail = False
    for r in results:
        if not r.get("id") or r.get("result") not in ("pass", "fail"):
            fail(f"{path}: invalid item in acceptance_results: {r}")
        if r.get("result") == "fail":
            has_fail = True
    if has_fail and not data.get("ratchet_ref"):
        fail(
            f"{path}: there is an acceptance_results with result: fail but 'ratchet_ref' is missing — "
            "run the ratchet-log skill first to write an entry to .gft/ratchet-log.yaml (see skills/ratchet-log/SKILL.md)"
        )


def validate_review_change(path):
    data = load_yaml(path) or {}
    findings = data.get("findings") or []
    verdict = data.get("verdict")
    if verdict not in ("approve", "blocker"):
        fail(f"{path}: verdict must be approve or blocker, got {verdict!r}")
    has_blocker = any(f.get("severity") == "blocker" for f in findings)
    if has_blocker and verdict != "blocker":
        fail(f"{path}: there is a finding with severity blocker but verdict is '{verdict}'")
    for f in findings:
        if not f.get("file"):
            fail(f"{path}: finding is missing a 'file' reference: {f}")
    if verdict == "blocker" and not data.get("ratchet_ref"):
        fail(
            f"{path}: verdict is 'blocker' but 'ratchet_ref' is missing — "
            "run the ratchet-log skill first to write an entry to .gft/ratchet-log.yaml (see skills/ratchet-log/SKILL.md)"
        )


def validate_test_plan(path):
    data = load_yaml(path) or {}
    cases = data.get("cases") or []
    if not cases:
        fail(f"{path}: cases must be a non-empty list")
    has_negative = False
    for c in cases:
        if not c.get("id"):
            fail(f"{path}: case is missing a stable id: {c}")
        if not c.get("acceptance_criteria_ref"):
            fail(f"{path}: case '{c.get('id', '?')}' is missing acceptance_criteria_ref")
        if c.get("covers_negative_path") is True:
            has_negative = True
    if not has_negative:
        fail(f"{path}: needs at least one case with covers_negative_path: true")


def validate_impact_analysis(path):
    data = load_yaml(path) or {}
    components = data.get("affected_components") or []
    if not components:
        fail(f"{path}: affected_components must be a non-empty list")
    for c in components:
        if c.get("impact") not in ("breaking", "behavior-change", "none"):
            fail(f"{path}: component '{c.get('name', '?')}' has an invalid impact: {c.get('impact')!r}")
        if not c.get("reason"):
            fail(f"{path}: component '{c.get('name', '?')}' is missing reason")
    if not data.get("risk_tier"):
        fail(f"{path}: missing risk_tier")


def validate_project_config(path):
    """Checks .gft/project.yaml of a project that USES the harness (level 2
    'project-config' in rules/context-hierarchy.yaml). It only accepts
    extension fields in the '*_extra' form (adding to a harness rule) — any
    field in the '*_override' form is treated as an attempt to loosen
    level 1 and fails outright."""
    data = load_yaml(path) or {}
    project = data.get("project") or {}
    if not project.get("id"):
        fail(f"{path}: missing project.id")
    if not project.get("owner_team"):
        fail(f"{path}: missing project.owner_team")
    commands = data.get("commands") or {}
    if not commands.get("test"):
        fail(f"{path}: missing commands.test — verify-change/qa-engineer needs this project's real test command")
    forbidden = [k for k in data.keys() if k.endswith("_override")]
    if forbidden:
        fail(
            f"{path}: field not allowed {forbidden} — project-config can only ADD "
            "(protected_paths_extra/escalate_paths_extra), it cannot loosen a harness rule"
        )


VALID_FAILURE_CLASSES = {
    "scope-creep",
    "invisible-deletion",
    "context-window",
    "prompt-satisfaction",
    "hallucination",
    "consistency",
    "other",
}
VALID_RATCHET_STATUS = {"open", "regression-added", "closed"}


def validate_ratchet_log(path):
    data = load_yaml(path) or {}
    entries = data.get("entries") or []
    if not entries:
        fail(f"{path}: entries must be a non-empty list")
        return
    for e in entries:
        for key in ("id", "task_id", "phase", "failure_class", "root_cause", "status"):
            if not e.get(key):
                fail(f"{path}: entry is missing or has an empty field '{key}': {e}")
        if e.get("failure_class") and e.get("failure_class") not in VALID_FAILURE_CLASSES:
            fail(f"{path}: entry '{e.get('id', '?')}' has an invalid failure_class: {e.get('failure_class')!r}")
        if e.get("status") and e.get("status") not in VALID_RATCHET_STATUS:
            fail(f"{path}: entry '{e.get('id', '?')}' has an invalid status: {e.get('status')!r}")
        if e.get("status") not in (None, "open") and not e.get("control_added"):
            fail(f"{path}: entry '{e.get('id', '?')}' has status '{e.get('status')}' but is missing control_added")


def validate_intake_request(path):
    data = load_yaml(path) or {}
    for key in ("problem_statement", "business_goal", "stakeholders"):
        if not data.get(key):
            fail(f"{path}: missing or empty field '{key}'")
    stakeholders = data.get("stakeholders") or []
    if not isinstance(stakeholders, list) or len(stakeholders) == 0:
        fail(f"{path}: stakeholders must be a non-empty list")
    else:
        for s in stakeholders:
            if not s.get("name") and not s.get("role"):
                fail(f"{path}: a stakeholder is missing both 'name' and 'role'")
    if not data.get("success_metric") and not (data.get("open_questions") or []):
        fail(f"{path}: if success_metric is empty, the reason must be stated in open_questions")

    dod = [d for d in (data.get("definition_of_done") or []) if d]
    if not dod:
        fail(f"{path}: definition_of_done is empty — at least one concrete condition is needed to know this brief is 'done'")

    # H-01 (pilot): previously nothing checked open_questions that are still
    # open against whether the brief is ready for /gft:spec — definition_of_done
    # was only checked for "not empty". ready_for_spec is a real gate: if it
    # is true while open_questions still has items, this FAILS, instead of
    # letting task-spec/feature-roadmap guess that the brief is done.
    if data.get("ready_for_spec") and (data.get("open_questions") or []):
        fail(
            f"{path}: ready_for_spec=true but open_questions still has "
            f"{len(data.get('open_questions'))} unclosed item(s) — answer them all, or set ready_for_spec: false"
        )


def validate_feature_roadmap(path):
    data = load_yaml(path) or {}
    if not data.get("outcome"):
        fail(f"{path}: missing outcome")

    split_decision = data.get("split_decision")
    if split_decision not in ("single", "staged"):
        fail(f"{path}: split_decision must be 'single' or 'staged', got {split_decision!r}")
        return

    if not data.get("open_questions_resolved"):
        fail(
            f"{path}: split_decision is set to '{split_decision}' but open_questions_resolved "
            "is not yet true — every blocking open question must be answered before locking in the roadmap"
        )

    if split_decision == "staged":
        stages = data.get("stages") or []
        if len(stages) < 2:
            fail(f"{path}: split_decision=staged but there is only {len(stages)} stage — there must be at least 2")
        stage_nos = {s.get("stage_no") for s in stages}
        for s in stages:
            if not s.get("scope_summary"):
                fail(f"{path}: stage {s.get('stage_no')} is missing scope_summary")
            if not s.get("risk_tier"):
                fail(f"{path}: stage {s.get('stage_no')} is missing risk_tier")
            for dep in (s.get("depends_on") or []):
                if dep not in stage_nos:
                    fail(f"{path}: stage {s.get('stage_no')} depends_on {dep} which does not exist in this roadmap")


def validate_pr_description(path):
    data = load_yaml(path) or {}
    for key in ("task_id", "changed_paths", "verification_ref", "review_ref"):
        if not data.get(key):
            fail(f"{path}: missing or empty field '{key}'")
    if data.get("breaking_change") not in (True, False):
        fail(f"{path}: breaking_change must be true or false, got {data.get('breaking_change')!r}")


# These keywords are deliberately kept in English: they are markers that
# the agent must really mention in its own output (see agents/README.md). Do not translate them.
AGENT_OUTPUT_MARKERS = {
    "solution-architect": ["downside", "trade-off", "constraint"],
    "developer": ["exit code", "changed path"],
    "qa-engineer": ["exit code", "acceptance"],
    "code-reviewer": ["verdict"],
    "security-reviewer": ["verdict"],
    "business-analyst": ["stakeholder", "acceptance criteria", "assumption"],
}


def validate_agent_output(role, path):
    text = Path(path).read_text().lower()
    if not text.strip():
        fail(f"{path}: file is empty")
        return
    markers = AGENT_OUTPUT_MARKERS.get(role)
    if markers is None:
        fail(f"unknown role '{role}' for agent-output check")
        return
    for marker in markers:
        if marker not in text:
            fail(f"{path}: output must mention '{marker}' for role '{role}'")


def main():
    args = sys.argv[1:]
    if not args:
        run_lint()
    else:
        kind = args[0]
        try:
            if kind == "task-spec":
                validate_task_spec(args[1])
            elif kind == "scope-amendment":
                validate_scope_amendment(args[1])
            elif kind == "adr":
                validate_adr(args[1])
            elif kind == "plan-review":
                validate_plan_review(args[1])
            elif kind == "verify-change":
                validate_verify_change(args[1])
            elif kind == "review-change":
                validate_review_change(args[1])
            elif kind == "test-plan":
                validate_test_plan(args[1])
            elif kind == "impact-analysis":
                validate_impact_analysis(args[1])
            elif kind == "pr-description":
                validate_pr_description(args[1])
            elif kind == "intake-request":
                validate_intake_request(args[1])
            elif kind == "feature-roadmap":
                validate_feature_roadmap(args[1])
            elif kind == "project-config":
                validate_project_config(args[1])
            elif kind == "ratchet-log":
                validate_ratchet_log(args[1])
            elif kind == "agent-output":
                validate_agent_output(args[1], args[2])
            else:
                print(f"Unrecognized validate kind: {kind}", file=sys.stderr)
                sys.exit(1)
        except yaml.UnsupportedYamlError as e:
            # YAML syntax outside the subset minimal_yaml.py supports (for
            # example a block scalar '>'/'|') — report the real cause right
            # here, instead of letting it surface as a confusing field
            # error in the field-by-field validator below.
            fail(str(e))

    if FAILURES:
        print(f"FAIL ({len(FAILURES)} errors):")
        for f in FAILURES:
            print(f"  - {f}")
        sys.exit(1)
    print("PASS")
    sys.exit(0)


if __name__ == "__main__":
    main()
