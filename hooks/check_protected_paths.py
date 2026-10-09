#!/usr/bin/env python3
"""Reads the Claude Code PreToolUse hook payload from stdin and checks the
target file_path against rules/protected-paths.yaml. Exit 2 blocks the
tool call (Claude Code's convention); exit 0 lets it continue, unless the
path matches escalate_paths — in that case it prints JSON with
permissionDecision: "ask" to stdout, so Claude Code shows a confirmation
prompt to the user.

If the project being worked on (the cwd of the Claude Code session, read
from payload['cwd']) has a .gft/project.yaml file (level 2 'project-config'
in rules/context-hierarchy.yaml, see templates/project-config.yaml), the
paths in its protected_paths_extra / escalate_paths_extra are ADDED to the
harness list — they can never be used to reduce or loosen a harness rule
(level 1).

IMPORTANT — matching scope: a harness pattern (rules/protected-paths.yaml,
argument 1) is only matched against a file that is REALLY inside the plugin
root (argument 2, PLUGIN_ROOT) — not against the whole cwd of the project
that uses the plugin. Reason: patterns like 'rules/**'/'hooks/**'/'registry/**'
are very common directory names in a real project (a business rule engine,
webhooks, a service registry...); if matched directly against the cwd, the
hook would wrongly block a directory in that project even though it has
nothing to do with harness governance. On the other hand,
protected_paths_extra/escalate_paths_extra in .gft/project.yaml still match
against the project's own cwd as before, because the project itself declares
them to protect its own files."""
import fnmatch
import json
import os
import sys


def resolve_abs(path, base):
    if os.path.isabs(path):
        return os.path.normpath(path)
    return os.path.normpath(os.path.join(base, path))


def relative_if_within(abs_path, root):
    """Returns the relative path of abs_path from root, or None if abs_path
    is not really inside root (compared by directory component, not a plain
    substring — this avoids treating 'rules-extra' as being inside the
    root 'rules')."""
    root = os.path.normpath(root)
    if abs_path == root:
        return "."
    prefix = root + os.sep
    if abs_path.startswith(prefix):
        return os.path.relpath(abs_path, root)
    return None


def path_matches(file_path, pattern):
    """fnmatch treats '*' as matching '/' too, so a pattern like '**/x/**'
    does not match by itself when 'x' is right at the root (there is no '/'
    before 'x'). We make up for this by also trying the pattern with the
    '**/' prefix removed."""
    if fnmatch.fnmatch(file_path, pattern):
        return True
    if pattern.startswith("**/"):
        tail = pattern[3:]
        return fnmatch.fnmatch(file_path, tail)
    return False


def read_list(rules_file, section):
    items = []
    in_section = False
    with open(rules_file) as f:
        for line in f:
            stripped = line.rstrip("\n")
            if stripped.startswith(f"{section}:"):
                in_section = True
                continue
            if in_section:
                if stripped.startswith("  - "):
                    items.append(stripped[4:].strip().strip('"'))
                elif stripped and not stripped.startswith(" "):
                    break
    return items


def project_config_lists(payload):
    """Reads .gft/project.yaml in the cwd of the current session, if it
    exists. Only reads the two '*_extra' extension keys — it deliberately
    does not read any '*_override' key even if project.yaml declares one,
    because the contract of the project-config level is to only add
    constraints, never to loosen the harness level."""
    cwd = payload.get("cwd") or os.getcwd()
    project_file = os.path.join(cwd, ".gft", "project.yaml")
    if not os.path.isfile(project_file):
        return [], []
    return read_list(project_file, "protected_paths_extra"), read_list(project_file, "escalate_paths_extra")


def main():
    rules_file = sys.argv[1]
    # PLUGIN_ROOT is optional (argument 2), for backward compatibility if
    # someone calls this script by hand without going through
    # check-protected-paths.sh; it is inferred from the location of
    # rules_file when missing (rules_file is always
    # <plugin_root>/rules/protected-paths.yaml).
    plugin_root = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.dirname(os.path.abspath(rules_file)))
    payload = json.load(sys.stdin)

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("path")
    if not file_path:
        return 0

    cwd = payload.get("cwd") or os.getcwd()
    abs_file = resolve_abs(file_path, cwd)
    # A harness pattern is only matched against the relative path from the
    # PLUGIN ROOT (None if this file is not really inside the plugin — for
    # example, editing a file in a different consuming project, even if
    # that project happens to have a directory with the same name as
    # 'rules/'/'hooks/'/'registry/'). A project's *_extra patterns still
    # match against that project's own cwd, as before.
    plugin_rel = relative_if_within(abs_file, plugin_root)
    project_rel = relative_if_within(abs_file, cwd) or file_path

    project_protected, project_escalate = project_config_lists(payload)
    protected = [(p, "rules/protected-paths.yaml", plugin_rel) for p in read_list(rules_file, "paths")]
    protected += [(p, ".gft/project.yaml (protected_paths_extra)", project_rel) for p in project_protected]
    escalate = [(p, "rules/protected-paths.yaml", plugin_rel) for p in read_list(rules_file, "escalate_paths")]
    escalate += [(p, ".gft/project.yaml (escalate_paths_extra)", project_rel) for p in project_escalate]

    for pattern, source, target in protected:
        if target is not None and path_matches(target, pattern):
            print(
                f"BLOCKED: '{file_path}' matches protected path '{pattern}' "
                f"in {source}",
                file=sys.stderr,
            )
            return 2

    for pattern, source, target in escalate:
        if target is not None and path_matches(target, pattern):
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "permissionDecision": "ask",
                            "permissionDecisionReason": (
                                f"'{file_path}' matches escalate path '{pattern}' "
                                f"in {source} — needs confirmation "
                                "from the user before writing."
                            ),
                        }
                    }
                )
            )
            return 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
