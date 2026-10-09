#!/usr/bin/env python3
"""Behavioral probe for every agent/skill in GFT Harness — runs a real headless
claude -p (--plugin-dir), captures tool_use through --output-format
stream-json, and checks two things: (1) does it announce the id registered in
registry/capability-catalog.yaml, (2) does it Read the right rule files that
agent.md/SKILL.md requires.

This is a manual scaffold for Part 1 (behavioral eval runner) in
next_action.md — not a full test suite, just enough to get a real signal
instead of guessing. Each run costs real money (it calls a real model).

Usage: python3 run_behavior_probe.py [--only id1,id2,...]
"""
import json
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path

HARNESS_ROOT = Path(__file__).resolve().parent.parent.parent
FIXTURES = Path(__file__).resolve().parent / "fixtures"

def read_fixture(name):
    return (FIXTURES / name).read_text()

TASK_SPEC = (HARNESS_ROOT / "skills/task-spec/examples/good.task-spec.yaml").read_text()
INTAKE_BRIEF = (HARNESS_ROOT / "skills/intake-request/examples/good.intake-brief.yaml").read_text()
VERIFICATION_RESULT_PASS = (HARNESS_ROOT / "skills/verify-change/examples/good.verification-result.yaml").read_text()
REVIEW_RESULT_APPROVE = (HARNESS_ROOT / "skills/review-change/examples/good.review-result.yaml").read_text()

VERIFICATION_RESULT_FAIL = """task_id: TASK-042
commands:
  - command: "npm test"
    exit_code: 1
    duration_seconds: 4
acceptance_results:
  - id: AC-1
    result: pass
  - id: AC-2
    result: fail
ratchet_ref: ""
details_ref: ""
"""

RATE_LIMIT_SRC = """// gateway/config/rate-limit.yaml (simulated as src for the test)
function checkRateLimit(apiKey, count) {
  if (count > 100) return { allowed: false, status: 429 };
  return { allowed: true };
}
module.exports = { checkRateLimit };
"""

AUTH_SRC = """// src/auth.js - middleware simulated for the security-review test
function requireAuth(req, res, next) {
  const token = req.headers['authorization'];
  if (!token) return res.status(401).json({ error: 'missing token' });
  next();
}
module.exports = { requireAuth };
"""

# task_id matches AUTH_SRC (different from TASK-042 in TASK_SPEC/VERIFICATION_RESULT_PASS
# — mixing 2 different task_ids would correctly make security-review STOP at step 1
# because "the diff scope is not clear", which is not a bug, but it would make
# this test fixture useless).
AUTH_VERIFICATION_RESULT_PASS = """task_id: TASK-099
commands:
  - command: "npm test -- auth.spec.ts"
    exit_code: 0
    duration_seconds: 5
acceptance_results:
  - id: AC-1
    result: pass
ratchet_ref: ""
details_ref: ""
"""

BUGGY_SRC = """function parsePrice(input) {
  return parseInt(input) * 100;
}
module.exports = { parsePrice };
"""

# Each case: id (kebab-case id in capability-catalog), kind ("agent"/"skill"),
# prompt, files (dict path->content copied into a scratch project before running),
# expected_reads (list of rules/*.yaml that a Read call must target).
CASES = [
    {
        "id": "business-analyst", "kind": "agent",
        "prompt": "My boss said they want to 'do something so customers complain less'. Please act as your business-analyst role to elicit this request.",
        "files": {}, "expected_reads": ["rules/safety-invariants.yaml"],
        # registry: the intake phase activates both agents:[business-analyst] and skills:[intake-request] —
        # the two really do overlap in function, so accept either as correct.
        "accept_ids": ["business-analyst", "intake-request"],
    },
    {
        "id": "solution-architect", "kind": "agent",
        "prompt": "The team is deciding between storing the session in Redis or in the main DB for the payment service. Please act as your solution-architect role.",
        "files": {}, "expected_reads": ["rules/architecture-principles.yaml", "rules/safety-invariants.yaml"],
    },
    {
        "id": "qa-engineer", "kind": "agent",
        "prompt": "The task-spec in task-spec.yaml already has acceptance criteria; the code is already implemented in gateway/config/rate-limit.yaml (see the file). Please act as your qa-engineer role to design and run checks.",
        "files": {"task-spec.yaml": TASK_SPEC, "gateway/config/rate-limit.yaml": RATE_LIMIT_SRC},
        "expected_reads": ["rules/error-handling.yaml", "rules/evidence-requirements.yaml", "rules/testing-quality-gate.yaml", "rules/safety-invariants.yaml"],
        "accept_ids": ["qa-engineer", "verify-change"],
    },
    {
        "id": "security-reviewer", "kind": "agent",
        "prompt": "The diff adds src/auth.js (see the file). The verification result already passed in verification-result.yaml. Please review as your security-reviewer role.",
        "files": {"src/auth.js": AUTH_SRC, "verification-result.yaml": AUTH_VERIFICATION_RESULT_PASS},
        "expected_reads": ["rules/security-baseline.yaml", "rules/protected-paths.yaml"],
        "accept_ids": ["security-reviewer", "security-review"],
    },
    {
        "id": "task-spec", "kind": "skill",
        "prompt": "I want the /public/search endpoint to reject requests over 100 req/minute per API key with HTTP 429. Please use the right skill to turn this into a task-spec.",
        "files": {}, "expected_reads": [],
    },
    {
        "id": "intake-request", "kind": "skill",
        "prompt": "I want to do something to reduce customer complaints, but I don't know exactly what yet.",
        "files": {}, "expected_reads": [],
    },
    {
        "id": "adr", "kind": "skill",
        "prompt": "The team has argued for several rounds between REST and GraphQL for the new API, and we need to record the official architecture decision. Use the adr skill.",
        "files": {}, "expected_reads": [],
    },
    {
        "id": "feature-roadmap", "kind": "skill",
        "prompt": "The intake brief is ready in intake-brief.yaml (ready_for_spec: true). This feature is quite large, and needs to be split into phases by risk before writing the task-spec. Use the feature-roadmap skill.",
        "files": {"intake-brief.yaml": INTAKE_BRIEF}, "expected_reads": [],
    },
    {
        "id": "impact-analysis", "kind": "skill",
        "prompt": "We plan to change the format of the 'order.created' event on the message queue — this event is consumed by many other services. Use the impact-analysis skill to assess the scope of the impact.",
        "files": {}, "expected_reads": [],
    },
    {
        "id": "plan-review", "kind": "skill",
        "prompt": "The task-spec is in task-spec.yaml. Proposed plan: (1) edit gateway/config/rate-limit.yaml to add a 100 req/minute rule per key, (2) write a test in gateway/tests/rate-limit.test.js. Please review this plan with the plan-review skill.",
        "files": {"task-spec.yaml": TASK_SPEC},
        "expected_reads": ["rules/protected-paths.yaml", "rules/safety-invariants.yaml"],
    },
    {
        "id": "test-plan", "kind": "skill",
        "prompt": "The task-spec in task-spec.yaml already has acceptance criteria, not implemented yet. Use the test-plan skill to plan the tests.",
        "files": {"task-spec.yaml": TASK_SPEC}, "expected_reads": [],
    },
    {
        "id": "verify-change", "kind": "skill",
        "prompt": "The task-spec in task-spec.yaml is already approved. The code is already implemented in gateway/config/rate-limit.yaml (see the file). Please run the verify-change skill to record evidence.",
        "files": {"task-spec.yaml": TASK_SPEC, "gateway/config/rate-limit.yaml": RATE_LIMIT_SRC,
                  "package.json": '{"name":"fp","scripts":{"test":"echo ok && exit 0"}}'},
        "expected_reads": ["rules/evidence-requirements.yaml"],
    },
    {
        "id": "review-change", "kind": "skill",
        "prompt": "The diff adds gateway/config/rate-limit.yaml (see the file). The task-spec is in task-spec.yaml, and the verification result already passed in verification-result.yaml. Please review with the review-change skill.",
        "files": {"task-spec.yaml": TASK_SPEC, "gateway/config/rate-limit.yaml": RATE_LIMIT_SRC,
                  "verification-result.yaml": VERIFICATION_RESULT_PASS},
        "expected_reads": ["rules/change-management.yaml", "rules/safety-invariants.yaml"],
    },
    {
        "id": "security-review", "kind": "skill",
        "prompt": "The diff adds src/auth.js (see the file), touching authentication. The verification result already passed in verification-result.yaml. Please review with the security-review skill.",
        "files": {"src/auth.js": AUTH_SRC, "verification-result.yaml": AUTH_VERIFICATION_RESULT_PASS},
        "expected_reads": ["rules/protected-paths.yaml", "rules/security-baseline.yaml"],
    },
    {
        "id": "ratchet-log", "kind": "skill",
        "prompt": "verification-result.yaml just ran and has one acceptance criterion that failed (see the file). Please use the ratchet-log skill to record it.",
        "files": {"verification-result.yaml": VERIFICATION_RESULT_FAIL},
        "expected_reads": ["rules/evidence-requirements.yaml", "rules/safety-invariants.yaml"],
    },
    {
        "id": "pr-description", "kind": "skill",
        "prompt": "verify-change already passed (verification-result.yaml) and review-change already approved it (review-result.yaml). Please use the pr-description skill to generate the PR description.",
        "files": {"verification-result.yaml": VERIFICATION_RESULT_PASS, "review-result.yaml": REVIEW_RESULT_APPROVE},
        "expected_reads": [],
    },
    {
        "id": "systematic-debugging", "kind": "skill",
        "prompt": "The parsePrice function in src/price.js (see the file) is failing a test with input '12.50' (parseInt drops the decimal part, giving a wrong result). We already tried one fix (changing parseInt to Number) but a different test then failed. Please use the systematic-debugging skill to investigate before trying another fix.",
        "files": {"src/price.js": BUGGY_SRC}, "expected_reads": ["rules/evidence-requirements.yaml", "rules/testing-quality-gate.yaml"],
    },
]


def run_case(case, out_dir):
    scratch = Path(tempfile.mkdtemp(prefix=f"gft-probe-{case['id']}-"))
    (scratch / ".git").mkdir()
    for relpath, content in case["files"].items():
        p = scratch / relpath
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)

    out_file = out_dir / f"{case['id']}.jsonl"
    cmd = [
        "claude", "-p", case["prompt"],
        "--plugin-dir", str(HARNESS_ROOT),
        "--allowed-tools", "Task,Read,Write,Edit,Bash,Grep,Glob,Skill",
        "--output-format", "stream-json", "--verbose",
    ]
    with open(out_file, "wb") as f:
        proc = subprocess.run(cmd, cwd=scratch, stdout=f, stderr=subprocess.STDOUT, timeout=280)
    shutil.rmtree(scratch, ignore_errors=True)
    return out_file, proc.returncode


def analyze(out_file, case):
    announce = None
    reads = set()
    dispatched_agent = None
    try:
        lines = out_file.read_text(errors="ignore").splitlines()
    except Exception:
        return {"announce": None, "reads": [], "dispatched_agent": None, "error": "no output file"}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if obj.get("type") != "assistant":
            continue
        for b in obj.get("message", {}).get("content", []):
            if b.get("type") == "text" and announce is None and "Using `" in b["text"]:
                # Get the exact line that has "Using `", do not assume it is always at the start of the block.
                for ln in b["text"].splitlines():
                    if "Using `" in ln:
                        announce = ln.strip()[:200]
                        break
            if b.get("type") == "tool_use":
                name = b.get("name")
                inp = b.get("input", {})
                if name == "Read":
                    fp = inp.get("file_path", "")
                    if "/rules/" in fp:
                        try:
                            rel = "rules/" + fp.split("/rules/", 1)[1]
                            reads.add(rel)
                        except Exception:
                            pass
                if name == "Agent":
                    dispatched_agent = inp.get("subagent_type")
    return {"announce": announce, "reads": sorted(reads), "dispatched_agent": dispatched_agent}


def main():
    only = None
    if len(sys.argv) > 1 and sys.argv[1] == "--only":
        only = set(sys.argv[2].split(","))

    out_dir = Path(tempfile.mkdtemp(prefix="gft-probe-results-"))
    print(f"Output raw transcripts: {out_dir}")

    results = []
    for case in CASES:
        if only and case["id"] not in only:
            continue
        print(f"=== Running: {case['id']} ({case['kind']}) ===", flush=True)
        try:
            out_file, rc = run_case(case, out_dir)
        except subprocess.TimeoutExpired:
            print(f"  TIMEOUT")
            results.append({"id": case["id"], "kind": case["kind"], "status": "TIMEOUT"})
            continue
        info = analyze(out_file, case)
        accept_ids = case.get("accept_ids", [case["id"]])
        matched_id = next((aid for aid in accept_ids if info["announce"] and f"`{aid}`" in info["announce"]), None)
        announce_ok = matched_id is not None
        # If the model follows an alternative id (a skill with the same function)
        # instead of the main id, do not require the main id's rule reads — it is
        # a different path with different requirements.
        #
        # An "agent" case dispatches through the Task tool, so its Read calls
        # happen inside the subagent's own transcript, not the top-level one
        # this script captures — reads_ok can never be checked for these, so
        # skip the check instead of reporting a false "missing reads".
        if case["kind"] == "agent":
            reads_ok = None
            missing_reads = []
        else:
            expected_reads = case["expected_reads"] if matched_id == case["id"] else []
            missing_reads = [r for r in expected_reads if r not in info["reads"]]
            reads_ok = len(missing_reads) == 0
        results.append({
            "id": case["id"], "kind": case["kind"], "matched_id": matched_id,
            "announce": info["announce"], "announce_ok": announce_ok,
            "reads": info["reads"], "missing_reads": missing_reads, "reads_ok": reads_ok,
            "dispatched_agent": info["dispatched_agent"],
        })
        print(f"  announce: {info['announce']!r} (ok={announce_ok})")
        if reads_ok is None:
            print(f"  reads: {info['reads']} (not checked — agent case, reads happen inside the subagent)")
        else:
            print(f"  reads: {info['reads']} missing={missing_reads}")

    print("\n\n===== SUMMARY =====")
    print(f"{'id':<22}{'kind':<8}{'announce_ok':<14}{'matched_id':<18}{'reads_ok':<10}missing_reads")
    for r in results:
        if r.get("status") == "TIMEOUT":
            print(f"{r['id']:<22}{r['kind']:<8}{'TIMEOUT':<14}")
            continue
        reads_ok_str = "N/A" if r["reads_ok"] is None else str(r["reads_ok"])
        print(f"{r['id']:<22}{r['kind']:<8}{str(r['announce_ok']):<14}{str(r.get('matched_id')):<18}{reads_ok_str:<10}{r['missing_reads']}")

    results_file = Path(__file__).resolve().parent / "last_probe_results.json"
    results_file.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"\nFull results JSON: {results_file}")


if __name__ == "__main__":
    main()
