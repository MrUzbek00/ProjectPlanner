#!/usr/bin/env python3
"""The ProjectPlanner -> SoftwareFactory integration contract, planner side.

The machine handoff is the only channel between the two systems. This module
owns the parts of it that exist for the consumer:

- the task content hash, a fingerprint of what a task asks for that ignores
  timestamps and readiness bookkeeping, so a consumer can tell whether the
  planning intent behind a task it ingested has changed;
- ``handoff-manifest.json``, the single entry point a consumer reads first;
- the checks that a manifest agrees with the files it describes;
- the hash lock over ``schemas/integration/``, the canonical copy of the
  contract schemas that SoftwareFactory vendors.

Versioning: the manifest's ``schema_version`` is the integration contract
version (CONTRACT_VERSION). It is independent of the planner's own file-format
version (validate_handoff.SCHEMA_VERSION), which the manifest reports as
``planner_schema_version``. The fields a consumer relies on are pinned by the
reference schemas in ``schemas/integration/``; the planner's generated files
are validated against them, so a planner change that would break a consumer
fails here first.

Usage:
    python tools/handoff_contract.py --check-lock
    python tools/handoff_contract.py --write-lock
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_DIR = REPO_ROOT / "schemas" / "integration"
CONTRACT_LOCK = CONTRACT_DIR / "contract.json"
CONTRACT_NAME = "project-planner/software-factory"
CONTRACT_VERSION = "1.0"

MANIFEST_FILE = "handoff-manifest.json"
MANIFEST_SCHEMA = "handoff-manifest.schema.json"
TASK_VIEW_SCHEMA = "task-handoff.schema.json"
REQUIREMENT_VIEW_SCHEMA = "requirement-reference.schema.json"
ADR_VIEW_SCHEMA = "architecture-reference.schema.json"

STATUS = {"ready": "READY_FOR_HANDOFF", "not_ready": "NOT_READY", "invalid": "INVALID"}
STATUS_RANK = {"INVALID": 0, "NOT_READY": 1, "READY_FOR_HANDOFF": 2}
FLAGS = ("schema_valid", "traceability_valid", "architecture_valid", "dependency_graph_valid",
         "specification_review_passed", "backlog_readiness_valid")
FILE_ROLES = {
    "project.json": "project",
    "requirements.json": "requirements",
    "architecture.json": "architecture",
    "decisions.json": "decisions",
    "domain.json": "domain",
    "backlog.json": "backlog",
    "tests.json": "tests",
    "traceability.json": "traceability",
    "changes.json": "changes",
    "specification-review.json": "specification_review",
    "backlog-readiness.json": "backlog_readiness",
}
VERSION_RE = re.compile(r"^([0-9]+)\.([0-9]+)$")

# Task content hash, basis task-intent/1. Everything a task says is hashed except
# its identity bookkeeping, planning-process state and derived views; the
# requirements and architecture decisions it relies on are hashed with it, so a
# changed requirement statement changes the hash of every task built on it.
TASK_HASH_BASIS = "task-intent/1"
TASK_HASH_EXCLUDED = (
    "schema_version", "project_id", "revision", "status", "content_hash", "priority", "priority_confirmed",
    "complexity", "phase", "dependencies_reviewed", "blocks", "readiness_gaps", "readiness", "readiness_history",
    "source_path",
)
REQUIREMENT_HASH_EXCLUDED = ("source_path", "priority", "priority_confirmed")
ADR_HASH_EXCLUDED = ("source_path",)


def canonical(document: object) -> bytes:
    """Deterministic JSON bytes: sorted keys, no insignificant whitespace."""
    return json.dumps(document, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def file_digest(data: bytes) -> str:
    """sha256 of LF-normalised bytes, so a CRLF checkout does not look like an edit."""
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def _without(record: dict, excluded: tuple[str, ...]) -> dict:
    return {key: value for key, value in record.items() if key not in excluded}


def task_content_hash(task: dict, req_by_id: dict[str, dict], adr_by_id: dict[str, dict]) -> str:
    requirements = []
    for rid in task.get("source_requirements") or []:
        req = req_by_id.get(rid)
        requirements.append(_without(req, REQUIREMENT_HASH_EXCLUDED) if req else {"id": rid, "missing": True})
    decisions = []
    for link in task.get("architecture_decisions") or []:
        aid = link.get("id") if isinstance(link, dict) else None
        adr = adr_by_id.get(aid)
        decisions.append(_without(adr, ADR_HASH_EXCLUDED) if adr else {"id": aid, "missing": True})
    payload = {
        "basis": TASK_HASH_BASIS,
        "task": _without(task, TASK_HASH_EXCLUDED),
        "requirements": requirements,
        "architecture_decisions": decisions,
    }
    return "sha256:" + hashlib.sha256(canonical(payload)).hexdigest()


def hash_description() -> dict:
    return {
        "algorithm": "sha256",
        "basis": TASK_HASH_BASIS,
        "covers": ["task (every field not excluded)", "source requirements (every field not excluded)",
                   "architecture decisions the task relies on (every field not excluded)"],
        "excludes": [f"task.{k}" for k in TASK_HASH_EXCLUDED]
        + [f"requirement.{k}" for k in REQUIREMENT_HASH_EXCLUDED] + [f"architecture_decision.{k}" for k in ADR_HASH_EXCLUDED],
    }


def stable_digest(name: str, data: bytes) -> str:
    """File digest for the content fingerprint: project.json without its timestamp."""
    if name != "project.json":
        return file_digest(data)
    try:
        project = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return file_digest(data)
    if isinstance(project, dict):
        project = {k: v for k, v in project.items() if k != "generated_at"}
    return hashlib.sha256(canonical(project)).hexdigest()


def content_fingerprint(raw: dict[str, bytes]) -> str:
    digest = hashlib.sha256()
    for name in sorted(raw):
        digest.update(name.encode("utf-8") + b"\0" + stable_digest(name, raw[name]).encode("ascii") + b"\n")
    return "sha256:" + digest.hexdigest()


def role_of(name: str) -> str | None:
    return "task" if name.startswith("tasks/") else FILE_ROLES.get(name)


def next_handoff_version(previous: dict | None, project_id: str, fingerprint: str, spec_version: str | None) -> str:
    """1.0 for a first handoff; unchanged content keeps its label; a new specification
    version starts a new major number; any other content change increments the minor number."""
    if not isinstance(previous, dict) or previous.get("project_id") != project_id:
        return "1.0"
    match = VERSION_RE.match(str(previous.get("handoff_version") or ""))
    if not match:
        return "1.0"
    if previous.get("content_fingerprint") == fingerprint:
        return match.group(0)
    major, minor = int(match.group(1)), int(match.group(2))
    if previous.get("specification_version") != spec_version:
        return f"{major + 1}.0"
    return f"{major}.{minor + 1}"


def manifest_status(project_status: str | None, flags: dict[str, bool]) -> str:
    status = STATUS.get(str(project_status), "INVALID")
    if status == "READY_FOR_HANDOFF" and not all(flags.values()):
        return "NOT_READY"
    return status


def task_entries(bundle) -> list[dict]:
    return [
        {"id": t.get("id"), "revision": t.get("revision"), "status": t.get("status"),
         "content_hash": t.get("content_hash"), "file": f"tasks/{t.get('id')}.json"}
        for t in bundle.tasks
    ]


def summary(bundle) -> dict:
    statuses = [t.get("status") for t in bundle.tasks]
    return {
        "requirements": len(bundle.requirements),
        "tasks_total": len(statuses),
        "tasks_ready": statuses.count("READY"),
        "tasks_blocked": statuses.count("BLOCKED"),
        "tasks_needs_review": statuses.count("NEEDS_REVIEW"),
        "tasks_needs_discovery": statuses.count("NEEDS_DISCOVERY"),
        "tasks_draft": statuses.count("DRAFT"),
        "tasks_cancelled": statuses.count("CANCELLED"),
    }


def build_manifest(raw: dict[str, bytes], bundle, flags: dict[str, bool], generated_at: str, generator: dict,
                   planner_schema_version: str, previous: dict | None) -> dict:
    """The manifest for the handoff files in ``raw`` (manifest and validation report excluded)."""
    project = bundle.project
    fingerprint = content_fingerprint(raw)
    spec_version = project.get("version")
    return {
        "schema_version": CONTRACT_VERSION,
        "handoff_version": next_handoff_version(previous, project.get("project_id"), fingerprint, spec_version),
        "planner_schema_version": planner_schema_version,
        "producer": {"system": "ProjectPlanner", "generator": generator["name"], "generator_version": generator["version"]},
        "project_id": project.get("project_id"),
        "project_name": project.get("name") or "",
        "specification_version": spec_version,
        "handoff_status": manifest_status(project.get("handoff_status"), flags),
        "generated_at": generated_at,
        "content_fingerprint": fingerprint,
        "task_content_hash": hash_description(),
        "summary": summary(bundle),
        "ready_tasks": list((bundle.backlog or {}).get("ready_task_ids") or []),
        "tasks": task_entries(bundle),
        "files": [{"path": name, "role": role_of(name), "sha256": file_digest(raw[name])}
                  for name in sorted(raw, key=lambda n: (n.startswith("tasks/"), n))],
        "validation": {flag: bool(flags.get(flag)) for flag in FLAGS},
    }


def check_manifest(manifest: object, raw: dict[str, bytes], bundle, expected_flags: dict[str, bool],
                   expected_project_status: str, planner_schema_version: str, validator, findings, step: str) -> None:
    """Report every way the manifest disagrees with the files it describes.

    A manifest may be more conservative than the evidence (a warning), never
    more optimistic (an error): the generator also sees source-level problems
    that the JSON alone cannot show.
    """
    where = MANIFEST_FILE
    if not isinstance(manifest, dict):
        findings.error(step, "MANIFEST_INVALID", "The manifest is not a JSON object.", where)
        return
    if manifest.get("schema_version") != CONTRACT_VERSION:
        findings.error(step, "MANIFEST_UNSUPPORTED_VERSION",
                       f"Contract version {manifest.get('schema_version')!r} is not {CONTRACT_VERSION}.", where)
        return
    for err in sorted(validator.iter_errors(manifest), key=lambda e: list(map(str, e.absolute_path))):
        path = "/".join(str(p) for p in err.absolute_path) or "(root)"
        findings.error(step, "MANIFEST_SCHEMA_VIOLATION", f"{path}: {err.message[:300]}", where)

    project = bundle.project
    for key, expected in (("project_id", project.get("project_id")), ("specification_version", project.get("version")),
                          ("planner_schema_version", planner_schema_version)):
        if manifest.get(key) != expected:
            findings.error(step, "MANIFEST_MISMATCH", f"{key} is {manifest.get(key)!r}; the handoff says {expected!r}.", where)

    listed = {f.get("path"): f for f in manifest.get("files") or [] if isinstance(f, dict)}
    for name in sorted(set(raw) - set(listed)):
        findings.error(step, "MANIFEST_FILE_UNLISTED", f"{name} is not listed in the manifest.", where)
    for name in sorted(set(listed) - set(raw)):
        findings.error(step, "MANIFEST_FILE_MISSING", f"{name} is listed in the manifest but missing.", where)
    for name in sorted(set(raw) & set(listed)):
        if listed[name].get("sha256") != file_digest(raw[name]):
            findings.error(step, "MANIFEST_HASH_MISMATCH", f"{name} differs from the hash in the manifest.", where)
        if listed[name].get("role") != role_of(name):
            findings.error(step, "MANIFEST_ROLE_MISMATCH", f"{name} has role {listed[name].get('role')!r}, expected {role_of(name)!r}.", where)
    if manifest.get("content_fingerprint") != content_fingerprint(raw):
        findings.error(step, "MANIFEST_FINGERPRINT_MISMATCH", "content_fingerprint does not match the handoff files.", where)

    if manifest.get("tasks") != task_entries(bundle):
        findings.error(step, "MANIFEST_TASK_MISMATCH", "The task list (id, revision, status, content hash) does not match the task files.", where)
    ready = list((bundle.backlog or {}).get("ready_task_ids") or [])
    if manifest.get("ready_tasks") != ready:
        findings.error(step, "MANIFEST_READY_TASKS_MISMATCH", f"ready_tasks is {manifest.get('ready_tasks')}; backlog.json says {ready}.", where)
    if manifest.get("summary") != summary(bundle):
        findings.error(step, "MANIFEST_COUNT_MISMATCH", "summary does not match the handoff files.", where)

    claimed_flags = manifest.get("validation") if isinstance(manifest.get("validation"), dict) else {}
    for flag in FLAGS:
        claimed, expected = claimed_flags.get(flag), bool(expected_flags.get(flag))
        if claimed is True and not expected:
            findings.error(step, "MANIFEST_FLAG_UNSUPPORTED", f"validation.{flag} is true; the validation result says false.", where)
        elif claimed is False and expected:
            findings.warn(step, "MANIFEST_FLAG_CONSERVATIVE",
                          f"validation.{flag} is false although the JSON alone supports true; see validation-report.json.", where)
    expected_status = manifest_status(expected_project_status, expected_flags)
    claimed_status = manifest.get("handoff_status")
    if STATUS_RANK.get(claimed_status, -1) > STATUS_RANK[expected_status]:
        findings.error(step, "MANIFEST_STATUS_MISMATCH",
                       f"handoff_status is {claimed_status!r}; the validation result supports only {expected_status!r}.", where)
    elif claimed_status != expected_status:
        findings.warn(step, "MANIFEST_STATUS_CONSERVATIVE",
                      f"handoff_status is {claimed_status!r} although the JSON alone supports {expected_status!r}.", where)


# --------------------------------------------------------------------------
# Contract lock
# --------------------------------------------------------------------------


def contract_schemas() -> list[Path]:
    return sorted(CONTRACT_DIR.glob("*.schema.json"))


def expected_lock() -> dict:
    return {
        "contract": CONTRACT_NAME,
        "contract_version": CONTRACT_VERSION,
        "canonical_source": "ProjectPlanner: schemas/integration/",
        "schemas": {path.name: file_digest(path.read_bytes()) for path in contract_schemas()},
    }


def lock_problems() -> list[str]:
    try:
        current = json.loads(CONTRACT_LOCK.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"{CONTRACT_LOCK.name} cannot be read: {exc}"]
    expected = expected_lock()
    problems = [f"{key} is {current.get(key)!r}, expected {expected[key]!r}"
                for key in ("contract", "contract_version", "canonical_source") if current.get(key) != expected[key]]
    locked = current.get("schemas") or {}
    for name in sorted(set(expected["schemas"]) | set(locked)):
        if locked.get(name) != expected["schemas"].get(name):
            problems.append(f"{name}: locked hash does not match the schema file" if name in locked and name in expected["schemas"]
                            else f"{name}: {'not locked' if name not in locked else 'locked but missing'}")
    for path in contract_schemas():
        schema = json.loads(path.read_text(encoding="utf-8"))
        segment = f"/integration/{CONTRACT_VERSION}/{path.name}"
        if not str(schema.get("$id", "")).endswith(segment):
            problems.append(f"{path.name}: $id does not end with {segment}")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check or refresh the integration contract hash lock.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check-lock", action="store_true", help="Fail when schemas/integration/ differs from contract.json")
    group.add_argument("--write-lock", action="store_true",
                       help="Rewrite contract.json from the schema files. Change CONTRACT_VERSION first when the change "
                            "is not backward compatible.")
    args = parser.parse_args(argv)
    if args.write_lock:
        CONTRACT_LOCK.write_text(json.dumps(expected_lock(), indent=2) + "\n", encoding="utf-8", newline="\n")
        print(f"Wrote {CONTRACT_LOCK.relative_to(REPO_ROOT).as_posix()} (contract {CONTRACT_VERSION}).")
        return 0
    problems = lock_problems()
    for problem in problems:
        print(f"ERROR {problem}")
    print(f"Integration contract {CONTRACT_VERSION}: {'LOCK CURRENT' if not problems else 'LOCK STALE'}")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
