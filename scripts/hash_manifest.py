#!/usr/bin/env python3
"""Computes/checks the `content_hash` for an agents/skills manifest.yaml — a
minimal lockfile against 'silent primitive drift' (a skill/agent whose
content changes while its version stays the same, see
wiki/foundations/failure-modes.md). This is not a real version (it does not
track history), it is only proof that the current content matches the last
time someone actively ran this command.

Usage:
  scripts/hash_manifest.py write <manifest.yaml>   # recomputes and writes content_hash into the file
  scripts/hash_manifest.py check <manifest.yaml>   # exits 1 if content_hash does not match the current content
  scripts/hash_manifest.py compute <file.yaml>     # prints the hash to stdout, writes nothing to the file — used when
                                                    # plan-review needs a snapshot of task_spec_hash at the
                                                    # moment it is approved (see templates/plan-review-result.yaml)

`scripts/validate.py` (lint_manifest_hashes, validate_plan_review) imports this module to reuse
compute_hash instead of shelling out, and runs 'check' on every manifest.yaml when
`make validate` runs. `make hash-manifests` runs 'write' in bulk.
"""
import hashlib
import re
import sys
from pathlib import Path

HASH_LINE_RE = re.compile(r"^content_hash:.*\n?", re.MULTILINE)


def canonical_content(text):
    """Removes the content_hash line itself before hashing, to avoid a
    self-referencing loop (the file's hash depending on the hash already
    written in it)."""
    return HASH_LINE_RE.sub("", text)


def compute_hash(path):
    text = Path(path).read_text()
    return hashlib.sha256(canonical_content(text).encode()).hexdigest()


def stored_hash(path):
    text = Path(path).read_text()
    m = re.search(r"^content_hash:\s*(\S+)", text, re.MULTILINE)
    return m.group(1) if m else None


def write(path):
    text = Path(path).read_text()
    digest = compute_hash(path)
    if "content_hash:" in text:
        new_text = HASH_LINE_RE.sub(f"content_hash: {digest}\n", text, count=1)
    else:
        new_text = text.rstrip("\n") + f"\ncontent_hash: {digest}\n"
    Path(path).write_text(new_text)
    return digest


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in ("write", "check", "compute"):
        print("usage: hash_manifest.py <write|check|compute> <file.yaml>", file=sys.stderr)
        sys.exit(1)
    mode, path = sys.argv[1], sys.argv[2]
    if mode == "write":
        digest = write(path)
        print(f"{path}: content_hash = {digest}")
        sys.exit(0)
    if mode == "compute":
        print(compute_hash(path))
        sys.exit(0)
    digest = compute_hash(path)
    stored = stored_hash(path)
    if stored != digest:
        print(
            f"{path}: content_hash does not match (stored={stored}, computed={digest}) — "
            f"run `scripts/hash_manifest.py write {path}` then commit again",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"{path}: OK")


if __name__ == "__main__":
    main()
