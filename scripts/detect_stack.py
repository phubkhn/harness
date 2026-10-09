#!/usr/bin/env python3
"""Scans a project (the project being worked on — NOT this harness itself)
to find which stack rules in rules/stacks/*.yaml match, based on
applies_when.paths (and applies_when.contains if present).

Usage: scripts/detect_stack.py <project-dir>
"""
import fnmatch
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import minimal_yaml as yaml  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
SKIP_DIRS = {".git", "node_modules", "dist", "build", "target", ".venv", "__pycache__", "bin", "obj"}


def matches(relpath_posix, pattern):
    """fnmatch treats '*' as matching '/' too, so a pattern like '**/x' does
    not match 'x' at the project root by itself (there is no '/' before it).
    We make up for this by also trying the pattern with the '**/' prefix
    removed."""
    if fnmatch.fnmatch(relpath_posix, pattern):
        return True
    if pattern.startswith("**/"):
        tail = pattern[3:]
        return fnmatch.fnmatch(relpath_posix, tail) or fnmatch.fnmatch(Path(relpath_posix).name, tail)
    return False


def collect_files(project_dir):
    files = []
    for p in project_dir.rglob("*"):
        if not p.is_file():
            continue
        if any(part in SKIP_DIRS for part in p.parts):
            continue
        files.append(p.relative_to(project_dir))
    return files


def check_rule(data, files, project_dir):
    applies_when = data.get("applies_when") or {}
    path_patterns = applies_when.get("paths") or []
    matched_files = []
    for rel in files:
        posix = rel.as_posix()
        if any(matches(posix, pat) for pat in path_patterns):
            matched_files.append(rel)
    if not matched_files:
        return None

    contains = applies_when.get("contains") or []
    for entry in contains:
        c_pattern = entry.get("path")
        c_regex = entry.get("pattern")
        if not c_pattern or not c_regex:
            continue
        candidates = [f for f in files if matches(f.as_posix(), c_pattern)]
        found = False
        for f in candidates:
            try:
                text = (project_dir / f).read_text(errors="ignore")
            except OSError:
                continue
            if re.search(c_regex, text):
                found = True
                break
        if not found:
            return None  # contains is required but not found -> no match

    return matched_files[0]


def main():
    if len(sys.argv) != 2:
        print("usage: scripts/detect_stack.py <project-dir>", file=sys.stderr)
        sys.exit(1)

    project_dir = Path(sys.argv[1]).resolve()
    if not project_dir.is_dir():
        print(f"Could not find project directory: {project_dir}", file=sys.stderr)
        sys.exit(1)

    stack_files = sorted((ROOT / "rules" / "stacks").glob("*.yaml"))
    if not stack_files:
        print("There are no stack rules yet in rules/stacks/.")
        return

    files = collect_files(project_dir)

    matched = []
    unmatched = []
    for f in stack_files:
        data = yaml.safe_load(f.read_text()) or {}
        rule_id = data.get("id", f.stem)
        evidence = check_rule(data, files, project_dir)
        if evidence is not None:
            matched.append((rule_id, f.relative_to(ROOT), evidence.as_posix()))
        else:
            unmatched.append(rule_id)

    if matched:
        print("Matching stack rules (based on applies_when):")
        for rule_id, rel, evidence in matched:
            print(f"  - {rule_id} ({rel}) — matched: {evidence}")
    else:
        print("No stack rule matches this project.")

    if unmatched:
        print("No match: " + ", ".join(unmatched))


if __name__ == "__main__":
    main()
