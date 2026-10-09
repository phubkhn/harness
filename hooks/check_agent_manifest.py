#!/usr/bin/env python3
"""SubagentStop hook: when a subagent (agents/<name>/agent.md) ends, this
compares the 'tools:' field in the agent.md frontmatter with 'allowed_tools'
in the matching manifest.yaml, then (if the subagent's transcript can be
read) logs usage/budget, runs verification.command on the real output, and
compares which tool groups the agent ACTUALLY used with the declared
'authority'. This version only warns (exit 0 + stderr), it does not block —
see the TODO at the end of the file for stricter enforcement steps planned
for later."""
import json
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT / "agents"

sys.path.insert(0, str(ROOT / "scripts"))
from minimal_yaml import safe_load  # noqa: E402

# Maps a Claude Code tool name (agent.md frontmatter, and the real tool_use
# name in the transcript) -> the group used in manifest.yaml 'allowed_tools'.
# Matches the current convention in agents/*/manifest.yaml (read, search,
# write, shell). A tool not in this table (Task, WebFetch, ...) is skipped
# safely instead of guessing a group for it.
TOOL_TO_GROUP = {
    "Read": "read",
    "Grep": "search",
    "Glob": "search",
    "Bash": "shell",
    "Edit": "write",
    "Write": "write",
}

# The maximum tool groups each authority level is allowed to ACTUALLY use at
# run time. This differs from the allowed_tools declared in the manifest: it
# is meant to catch a mismatch between the declared authority and the real
# runtime behavior, even when allowed_tools was declared wrong to match (for
# example, someone mistakenly added 'write' to the allowed_tools of an agent
# with authority: read-only).
AUTHORITY_MAX_GROUPS = {
    "read-only": {"read", "search", "shell"},
    "proposal": {"read", "search", "shell"},
    "bounded-write": {"read", "search", "shell", "write"},
    "deny": set(),
}

# Keys that may hold the subagent identifier in the SubagentStop payload.
# We have not confirmed for sure what the real Claude Code field is for this
# event, so we try them one by one — if no key is found, we skip safely
# (exit 0).
AGENT_KEY_CANDIDATES = ("agent_type", "subagent_type", "agent", "name")

# Same idea — we have not confirmed for sure which field name Claude Code
# uses for the (sub)agent's transcript path in the SubagentStop payload. We
# try them one by one, and skip safely (no usage/authority/verification
# measured) if none is found.
TRANSCRIPT_KEY_CANDIDATES = ("transcript_path", "agent_transcript_path", "subagent_transcript_path")

REPORT_FILENAME_RE = re.compile(r"report\.md$", re.IGNORECASE)
PLACEHOLDER = "<path-to-output.md>"


def parse_frontmatter_tools(agent_md_path):
    text = agent_md_path.read_text()
    match = re.search(r"^---\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return None
    for line in match.group(1).splitlines():
        line = line.strip()
        if line.startswith("tools:"):
            value = line[len("tools:") :].strip()
            return [t.strip() for t in value.split(",") if t.strip()]
    return None


def load_manifest(manifest_path):
    try:
        return safe_load(manifest_path.read_text())
    except Exception:
        # Skip safely instead of crashing the hook if the manifest does not
        # match the YAML subset that minimal_yaml.py supports — make
        # validate will catch that error separately.
        return None


def resolve_agent_name(payload):
    for key in AGENT_KEY_CANDIDATES:
        value = payload.get(key)
        if value and (AGENTS_DIR / value).is_dir():
            return value
    return None


def resolve_transcript_path(payload):
    for key in TRANSCRIPT_KEY_CANDIDATES:
        value = payload.get(key)
        if value and Path(value).is_file():
            return Path(value)
    return None


def read_transcript_entries(transcript_path):
    entries = []
    try:
        with transcript_path.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    except OSError:
        return []
    return entries


def summarize_transcript(entries):
    """Returns (turns, usage_totals, tool_calls) from the transcript JSONL.
    The real Claude Code field for each transcript line is also not
    confirmed for sure (like TRANSCRIPT_KEY_CANDIDATES), so we check several
    candidate locations for 'usage', and skip safely any field we don't
    find instead of guessing."""
    turns = 0
    usage_totals = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
    }
    tool_calls = []  # list of (tool_name, file_path_or_None)
    for entry in entries:
        if entry.get("type") != "assistant":
            continue
        turns += 1
        message = entry.get("message") or {}
        usage = message.get("usage") or entry.get("usage") or {}
        for key in usage_totals:
            value = usage.get(key)
            if isinstance(value, int):
                usage_totals[key] += value
        content = message.get("content")
        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tool_input = block.get("input") or {}
                    file_path = tool_input.get("file_path") or tool_input.get("path")
                    tool_calls.append((block.get("name"), file_path))
    return turns, usage_totals, tool_calls


def find_report_candidate(tool_calls):
    """Finds the most recent report file that the agent wrote or edited in
    the transcript, following the '<...>-report.md' convention
    (agents/developer/agent.md step 6). Not every role writes a report file
    (only developer must), so returning None is normal, not an error."""
    candidates = [
        fp
        for name, fp in tool_calls
        if name in ("Write", "Edit") and fp and REPORT_FILENAME_RE.search(fp)
    ]
    return candidates[-1] if candidates else None


def run_verification(manifest, report_path, project_cwd):
    verification = manifest.get("verification") or {}
    command = verification.get("command")
    if not command or PLACEHOLDER not in command or not report_path:
        return None

    report_abs = Path(report_path)
    if not report_abs.is_absolute():
        report_abs = Path(project_cwd) / report_path
    if not report_abs.is_file():
        return {"ran": False, "reason": f"report path does not exist: {report_abs}"}

    tokens = shlex.split(command)
    tokens = [str(report_abs) if t == PLACEHOLDER else t for t in tokens]
    try:
        proc = subprocess.run(
            tokens,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception as exc:  # the command failed to run (not found, timeout, ...)
        return {"ran": False, "reason": f"error running verification.command: {exc}", "command": tokens}

    return {
        "ran": True,
        "command": tokens,
        "exit_code": proc.returncode,
        "passed": proc.returncode == 0,
        "stderr_tail": proc.stderr[-2000:],
    }


def check_authority(manifest, tool_calls):
    authority = manifest.get("authority")
    allowed_max_groups = AUTHORITY_MAX_GROUPS.get(authority)
    used_groups = sorted({TOOL_TO_GROUP[name] for name, _ in tool_calls if name in TOOL_TO_GROUP})
    violation = None
    if allowed_max_groups is not None:
        excess = sorted(set(used_groups) - allowed_max_groups)
        if excess:
            violation = excess
    return authority, used_groups, violation


def write_log(project_cwd, entry):
    log_dir = Path(project_cwd) / ".gft" / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        with (log_dir / "agent-runs.jsonl").open("a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError as exc:
        print(f"WARNING: could not write log agent-runs.jsonl: {exc}", file=sys.stderr)


def main():
    payload = json.load(sys.stdin)
    project_cwd = payload.get("cwd") or "."

    agent_name = resolve_agent_name(payload)
    if not agent_name:
        # Could not identify which subagent just stopped -- skip safely.
        return 0

    agent_dir = AGENTS_DIR / agent_name
    agent_md = agent_dir / "agent.md"
    manifest_path = agent_dir / "manifest.yaml"
    if not agent_md.exists() or not manifest_path.exists():
        return 0

    manifest = load_manifest(manifest_path)
    if manifest is None:
        return 0

    tools = parse_frontmatter_tools(agent_md) or []
    allowed_tools = set(manifest.get("allowed_tools") or [])

    required_groups = {TOOL_TO_GROUP[t] for t in tools if t in TOOL_TO_GROUP}
    missing = required_groups - allowed_tools
    if missing:
        print(
            f"WARNING: agents/{agent_name} — tools frontmatter needs group "
            f"{sorted(missing)} but manifest.yaml.allowed_tools "
            f"({sorted(allowed_tools)}) is missing this group. Update "
            f"agents/{agent_name}/manifest.yaml to match agent.md.",
            file=sys.stderr,
        )

    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "agent": agent_name,
    }

    transcript_path = resolve_transcript_path(payload)
    if transcript_path is None:
        log_entry["transcript"] = "unavailable"
        write_log(project_cwd, log_entry)
        return 0

    entries = read_transcript_entries(transcript_path)
    turns, usage_totals, tool_calls = summarize_transcript(entries)

    budgets = manifest.get("budgets") or {}
    max_turns = budgets.get("max_turns")
    over_budget = isinstance(max_turns, int) and turns > max_turns
    log_entry["turns"] = turns
    log_entry["max_turns"] = max_turns
    log_entry["over_budget"] = over_budget
    log_entry["usage"] = usage_totals
    if over_budget:
        print(
            f"WARNING: agents/{agent_name} — used {turns} turns, over "
            f"budgets.max_turns={max_turns} in manifest.yaml.",
            file=sys.stderr,
        )

    authority, used_groups, authority_violation = check_authority(manifest, tool_calls)
    log_entry["authority"] = authority
    log_entry["tool_groups_used"] = used_groups
    log_entry["authority_violation"] = authority_violation
    if authority_violation:
        print(
            f"WARNING: agents/{agent_name} — declared authority '{authority}' but "
            f"actually used tool group {authority_violation}, beyond what is allowed.",
            file=sys.stderr,
        )

    report_path = find_report_candidate(tool_calls)
    verification_result = run_verification(manifest, report_path, project_cwd)
    log_entry["verification"] = verification_result
    if verification_result and verification_result.get("ran") and not verification_result.get("passed"):
        print(
            f"WARNING: agents/{agent_name} — verification.command FAILED on "
            f"'{report_path}':\n{verification_result.get('stderr_tail', '')}",
            file=sys.stderr,
        )

    write_log(project_cwd, log_entry)
    return 0


if __name__ == "__main__":
    sys.exit(main())

# TODO (later — not done in this version):
# - Real enforcement: return a permissionDecision other than allow, or
#   block, instead of just warning, when tools/authority/verification
#   do not match.
# - Read budgets.max_recovery_attempts and compare with the real number of
#   recovery attempts (needs confirming which payload/transcript field
#   reflects this).
# - Check 'authority' against the allowed_scope/risk_tier of the active
#   task-spec (needs deciding how the hook knows which task-spec is
#   active — right now the agent reads the task-spec itself, and the hook
#   has no reference to that file).
