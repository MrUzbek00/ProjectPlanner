#!/usr/bin/env python3
"""Validate a machine-handoff directory deterministically.

Checks JSON syntax, conformance to the schemas in ``schemas/``, unique IDs,
that every referenced ID exists, dependency cycles, the Definition of Ready
for every READY task, traceability, architecture governance (ADR lifecycle,
supersession, conflicts between active decisions, references to inactive
decisions, drift from accepted decisions), change impact (review states derived from
the change records, readiness withdrawn from tasks under review), the independent
specification review (its result recomputed from its findings), agreement
between backlog.json and the task files, artifact hashes, task content hashes,
conformance to the integration contract's consumer views, whether
project.json's handoff_status is justified, and whether handoff-manifest.json
agrees with all of it. When the project's Markdown sources are available it
also detects a stale handoff.

It reads only the JSON. It does not need the Markdown, so a downstream system
can run it on a copied handoff before consuming anything.

Usage:
    python tools/validate_handoff.py projects/<project>/machine-handoff
    python tools/validate_handoff.py <dir> --sources projects/<project>
    python tools/validate_handoff.py <dir> --json

Exit codes: 0 valid (warnings allowed), 1 validation errors, 2 cannot run.
"""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import change_impact as ci  # noqa: E402
import handoff_contract as hc  # noqa: E402
import planning_records as pr  # noqa: E402
import specification_review as sr  # noqa: E402
import backlog_readiness as br  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = REPO_ROOT / "schemas"
SCHEMA_VERSION = "1.5"

DOCUMENT_SCHEMAS = {
    "project.json": "project.schema.json",
    "requirements.json": "requirements.schema.json",
    "architecture.json": "architecture.schema.json",
    "decisions.json": "decisions.schema.json",
    "backlog.json": "backlog.schema.json",
    "traceability.json": "traceability.schema.json",
    "tests.json": "tests.schema.json",
    "domain.json": "domain.schema.json",
    "changes.json": "changes.schema.json",
    "specification-review.json": "specification-review.schema.json",
    "backlog-readiness.json": "backlog-readiness.schema.json",
}
TASK_SCHEMA = "task.schema.json"
REPORT_FILE = "validation-report.json"
MANIFEST_FILE = hc.MANIFEST_FILE
UNLISTED_FILES = {"project.json", REPORT_FILE}
# Integration contract schemas are registered as "integration/<file name>".
CONTRACT_PREFIX = "integration/"
# Finding codes behind the manifest's architecture and dependency-graph flags.
ARCHITECTURE_CODES = {"ARCHITECTURE_CONFLICT", "VAGUE_CONSTRAINT"}
DEPENDENCY_GRAPH_CODES = {"DEPENDENCY_CYCLE", "PARENT_CYCLE", "SELF_DEPENDENCY", "FEATURE_DEPENDENCY_CYCLE"}

# Planning statuses. Execution (coding, testing, review, merge, deployment) belongs to downstream engineering.
TASK_STATUSES = ("DRAFT", "NEEDS_DISCOVERY", "NEEDS_REVIEW", "BLOCKED", "READY", "CANCELLED")
ENGINEERING_STATUSES = ("IN_PROGRESS", "CODING", "TESTING", "PR_OPEN", "IN_REVIEW", "MERGED", "DEPLOYED", "DONE")
DEPENDENCY_OK = {"READY"}
PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "unspecified": 4}
LIVE_STATUSES = {"approved", "confirmed"}
IMPLEMENTABLE = {"functional", "non_functional", "data", "integration", "security", "ux", "technical"}
REALISED_DOWNSTREAM = {"business_goal", "business", "business_rule"}
TOP_PRIORITY = {"critical", "must"}
SCHEME_VALUES = {"levels": {"critical", "high", "medium", "low"}, "moscow": {"must", "should", "could", "wont"}}
# ADR statuses that govern nothing: kept for history, never applied to new planning.
INACTIVE_ADR = {"rejected", "superseded", "deprecated"}
# Constraint wording that cannot be reviewed or tested.
VAGUE_CONSTRAINT_TERMS = ["clean", "best practice", "best practices", "scalable", "robust", "modern", "flexible",
                          "as needed", "as appropriate", "where appropriate", "high quality", "state of the art",
                          "future-proof", "industry standard"]
# Code-level detail that belongs to implementation planning, not to an ADR.
IMPLEMENTATION_DETAIL_RE = re.compile(
    r"\b[\w/.-]+\.(?:py|js|jsx|ts|tsx|java|cs|go|rb|php|kt|swift)\b|\b(?:src|lib|app)/[\w/.-]+|"
    r"\b[a-z_][a-z0-9_]*\(\)|\bclass\s+[A-Z]\w+")


def in_release(req: dict) -> bool:
    """Live and not excluded. An unclassified scope still counts, so gaps show up
    before scope is decided rather than being hidden."""
    return req.get("status") in LIVE_STATUSES and req.get("scope") in (None, "in_scope")

STEP_SPEC = "1-specification"
STEP_REQ = "2-requirements"
STEP_BACKLOG = "3-backlog"
STEP_SCHEMA = "5-schema"
STEP_TRACE = "6-traceability"


@dataclass
class Finding:
    severity: str  # error | warning
    step: str
    code: str
    message: str
    location: str = ""

    def as_json(self) -> dict:
        return {"step": self.step, "code": self.code, "message": self.message, "location": self.location}


class Findings:
    def __init__(self) -> None:
        self.items: list[Finding] = []

    def error(self, step: str, code: str, message: str, location: str = "") -> None:
        self.items.append(Finding("error", step, code, message, location))

    def warn(self, step: str, code: str, message: str, location: str = "") -> None:
        self.items.append(Finding("warning", step, code, message, location))

    def extend(self, other: "Findings") -> None:
        self.items.extend(other.items)

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.items if f.severity == "error"]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.items if f.severity == "warning"]


# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------


class SchemaUnavailable(RuntimeError):
    pass


_VALIDATORS: dict[str, object] = {}


def load_validators() -> dict[str, object]:
    if _VALIDATORS:
        return _VALIDATORS
    try:
        from jsonschema import Draft202012Validator, FormatChecker
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise SchemaUnavailable(
            "The jsonschema package (>= 4.18) is required for schema validation. "
            "Run: python -m pip install -r tools/requirements-handoff.txt"
        ) from exc

    schemas = {}
    for path in sorted(SCHEMA_DIR.glob("*.schema.json")):
        schemas[path.name] = json.loads(path.read_text(encoding="utf-8"))
    for path in hc.contract_schemas():
        schemas[CONTRACT_PREFIX + path.name] = json.loads(path.read_text(encoding="utf-8"))
    resources = [
        (schema["$id"], Resource.from_contents(schema, default_specification=DRAFT202012))
        for schema in schemas.values()
    ]
    registry = Registry().with_resources(resources)
    for name, schema in schemas.items():
        Draft202012Validator.check_schema(schema)
        _VALIDATORS[name] = Draft202012Validator(schema, registry=registry, format_checker=FormatChecker())
    return _VALIDATORS


def schema_findings(name: str, document: object, validator, findings: Findings) -> None:
    errors = sorted(validator.iter_errors(document), key=lambda e: (list(map(str, e.absolute_path)), e.message))
    for err in errors:
        where = "/".join(str(p) for p in err.absolute_path) or "(root)"
        message = err.message if len(err.message) <= 300 else err.message[:297] + "..."
        findings.error(STEP_SCHEMA, "SCHEMA_VIOLATION", f"{where}: {message}", name)


# --------------------------------------------------------------------------
# Graph helpers shared with the generator
# --------------------------------------------------------------------------


def sequence_tasks(tasks: list[dict], phase_order: dict[str, int]) -> tuple[list[str], dict[str, int], set[str]]:
    """Deterministic topological order of tasks.

    Ties are broken by phase order, then priority, then natural ID order, so
    the same backlog always yields the same sequence. Returns the order, the
    depth of each sequenced task, and the tasks that could not be sequenced
    because they are in, or downstream of, a dependency cycle. While any cycle
    exists the order is empty: no execution sequence is generated around it.
    """
    by_id = {t["id"]: t for t in tasks}
    indegree = {tid: 0 for tid in by_id}
    successors: dict[str, list[str]] = {tid: [] for tid in by_id}
    for tid, task in by_id.items():
        for dep in task.get("dependencies", []):
            if dep in by_id and dep != tid:
                indegree[tid] += 1
                successors[dep].append(tid)

    def rank(tid: str) -> tuple:
        task = by_id[tid]
        return (
            phase_order.get(task.get("phase") or "", 10**6),
            PRIORITY_RANK.get(task.get("priority", "unspecified"), 9),
            pr.natural_key(tid),
            tid,
        )

    heap = [rank(tid) for tid, degree in indegree.items() if degree == 0]
    heapq.heapify(heap)
    order: list[str] = []
    while heap:
        tid = heapq.heappop(heap)[-1]
        order.append(tid)
        for succ in successors[tid]:
            indegree[succ] -= 1
            if indegree[succ] == 0:
                heapq.heappush(heap, rank(succ))

    unsequenced = set(by_id) - set(order)
    if unsequenced:
        # A dependency cycle makes every order a guess: none is produced until the cycle is resolved.
        return [], {}, unsequenced
    depth: dict[str, int] = {}
    for tid in order:
        deps = [d for d in by_id[tid].get("dependencies", []) if d in depth]
        depth[tid] = max((depth[d] + 1 for d in deps), default=0)
    return order, depth, unsequenced


def find_cycles(nodes: list[str], edges: dict[str, list[str]]) -> list[list[str]]:
    """Strongly connected components with more than one node, or a self-loop."""
    index_of: dict[str, int] = {}
    low: dict[str, int] = {}
    stack: list[str] = []
    on_stack: set[str] = set()
    cycles: list[list[str]] = []
    counter = [0]

    def visit(start: str) -> None:
        # Iterative Tarjan to avoid recursion limits on long chains.
        work = [(start, iter(sorted(edges.get(start, []), key=pr.natural_key)))]
        index_of[start] = low[start] = counter[0]
        counter[0] += 1
        stack.append(start)
        on_stack.add(start)
        while work:
            node, children = work[-1]
            advanced = False
            for child in children:
                if child not in index_of:
                    index_of[child] = low[child] = counter[0]
                    counter[0] += 1
                    stack.append(child)
                    on_stack.add(child)
                    work.append((child, iter(sorted(edges.get(child, []), key=pr.natural_key))))
                    advanced = True
                    break
                if child in on_stack:
                    low[node] = min(low[node], index_of[child])
            if advanced:
                continue
            work.pop()
            if work:
                parent = work[-1][0]
                low[parent] = min(low[parent], low[node])
            if low[node] == index_of[node]:
                component = []
                while True:
                    member = stack.pop()
                    on_stack.discard(member)
                    component.append(member)
                    if member == node:
                        break
                if len(component) > 1 or node in edges.get(node, []):
                    cycles.append(sorted(component, key=pr.natural_key))

    for node in sorted(nodes, key=pr.natural_key):
        if node not in index_of:
            visit(node)
    return sorted(cycles, key=lambda c: pr.natural_key(c[0]))


# --------------------------------------------------------------------------
# Bundle context
# --------------------------------------------------------------------------


class Bundle:
    """Indexed view of the parsed handoff documents."""

    def __init__(self, docs: dict[str, object]):
        self.docs = docs
        get = lambda name: docs.get(name) if isinstance(docs.get(name), dict) else {}  # noqa: E731
        self.project = get("project.json")
        self.requirements_doc = get("requirements.json")
        self.architecture = get("architecture.json")
        self.decisions_doc = get("decisions.json")
        self.backlog = get("backlog.json")
        self.traceability = get("traceability.json")
        self.tests_doc = get("tests.json")
        self.domain = get("domain.json")
        self.changes_doc = get("changes.json")
        self.spec_review = get("specification-review.json")
        self.backlog_readiness = get("backlog-readiness.json")
        self.task_docs = {
            name: doc for name, doc in docs.items() if name.startswith("tasks/") and isinstance(doc, dict)
        }

        def listing(doc: dict, key: str) -> list[dict]:
            value = doc.get(key, [])
            return [v for v in value if isinstance(v, dict)] if isinstance(value, list) else []

        self.requirements = listing(self.requirements_doc, "requirements")
        self.sources = listing(self.requirements_doc, "sources")
        self.modules = listing(self.architecture, "modules")
        self.adrs = listing(self.architecture, "decisions")
        self.principles = listing(self.architecture, "principles")
        self.coverage = listing(self.architecture, "coverage")
        self.decisions = listing(self.decisions_doc, "decisions")
        self.questions = listing(self.decisions_doc, "questions")
        self.assumptions = listing(self.decisions_doc, "assumptions")
        self.epics = listing(self.backlog, "epics")
        self.features = listing(self.backlog, "features")
        self.phases = listing(self.backlog, "phases")
        self.backlog_tasks = listing(self.backlog, "tasks")
        self.tests = listing(self.tests_doc, "tests")
        self.tasks = [doc for _, doc in sorted(self.task_docs.items())]
        self.risks = listing(self.decisions_doc, "risks")
        self.dependencies = listing(self.backlog, "external_dependencies")
        self.scope_items = listing(self.requirements_doc, "scope_items")
        self.processes = listing(self.domain, "processes")
        self.changes = listing(self.changes_doc, "changes")
        self.unrecorded = listing(self.changes_doc, "unrecorded_changes")
        self.artifact_state = {e.get("id"): e for e in listing(self.changes_doc, "artifact_states")}
        self.entities = listing(self.domain, "entities")
        self.review_findings = listing(self.spec_review, "findings")

        index = lambda items: {i.get("id"): i for i in items if isinstance(i.get("id"), str)}  # noqa: E731
        self.req_by_id = index(self.requirements)
        self.src_by_id = index(self.sources)
        self.mod_by_id = index(self.modules)
        self.adr_by_id = index(self.adrs)
        self.prin_by_id = index(self.principles)
        self.dec_by_id = index(self.decisions)
        self.q_by_id = index(self.questions)
        self.epic_by_id = index(self.epics)
        self.feat_by_id = index(self.features)
        self.phase_by_id = index(self.phases)
        self.task_by_id = index(self.tasks)
        self.test_by_id = index(self.tests)
        self.risk_by_id = index(self.risks)
        self.dep_by_id = index(self.dependencies)
        self.scope_by_id = index(self.scope_items)
        self.proc_by_id = index(self.processes)
        self.ent_by_id = index(self.entities)
        self.review_by_id = index(self.review_findings)
        self.change_by_id = {c.get("change_id"): c for c in self.changes if isinstance(c.get("change_id"), str)}
        self.phase_order = {
            p["id"]: p.get("order", 0) for p in self.phases if isinstance(p.get("id"), str)
        }
        # Which requirements define each acceptance criterion, so a task's criteria can be checked against its sources.
        self.ac_owners: dict[str, set[str]] = {}
        for req in self.requirements:
            for criterion in req.get("acceptance_criteria", []) or []:
                head = str(criterion).split(":", 1)[0].strip()
                if pr.FULL_ID_RE["AC"].match(head):
                    self.ac_owners.setdefault(head, set()).add(req.get("id"))
        self.ac_ids = set()
        for item in self.requirements + self.tasks:
            for criterion in item.get("acceptance_criteria", []) or []:
                if isinstance(criterion, str):
                    head = criterion.split(":", 1)[0].strip()
                    if pr.FULL_ID_RE["AC"].match(head):
                        self.ac_ids.add(head)

    @property
    def spec_approved(self) -> bool:
        return self.project.get("specification_status") == "approved"

    def review_gap(self) -> str | None:
        """Why the independent specification review does not support readiness, or None when it does."""
        review = self.spec_review or {}
        result = review.get("overall_result") or "NOT_REVIEWED"
        cycle = review.get("review_cycle") or 0
        if result == "NOT_REVIEWED":
            return f"Specification has not been independently reviewed ({pr.SPECIFICATION_REVIEW_FILE})."
        if result not in ("PASS", "PASS_WITH_WARNINGS"):
            summary = review.get("summary") or {}
            reasons = [f"{summary.get(k, 0)} open {k.upper()}" for k in ("critical", "major") if summary.get(k)]
            if review.get("issues"):
                reasons.append(f"{len(review['issues'])} defect(s) in the review record")
            return f"Specification review fails (cycle {cycle}): {', '.join(reasons) or 'see specification-review.json'}."
        if review.get("review_version") != self.project.get("version"):
            return (f"Specification review covers version {review.get('review_version')}, not the current "
                    f"version {self.project.get('version')}.")
        return None

    def known(self, identifier: str) -> bool | None:
        """Whether an ID exists in the bundle; None when its kind is not part of the handoff."""
        kind = pr.kind_of(identifier)
        tables = {kind: self.req_by_id for kind in pr.REQUIREMENT_KINDS}
        tables.update({
            "TASK": self.task_by_id, "FEAT": self.feat_by_id, "EPIC": self.epic_by_id,
            "TEST": self.test_by_id, "ADR": self.adr_by_id, "MOD": self.mod_by_id, "DEC": self.dec_by_id,
            "PRIN": self.prin_by_id, "CHANGE": self.change_by_id,
            "Q": self.q_by_id, "PHASE": self.phase_by_id, "SRC": self.src_by_id, "RISK": self.risk_by_id,
            "DEP": self.dep_by_id, "SCOPE": self.scope_by_id, "PROC": self.proc_by_id, "ENT": self.ent_by_id,
            "REVIEW": self.review_by_id,
        })
        if kind == "AC":
            return identifier in self.ac_ids
        if kind not in tables:
            return None
        return identifier in tables[kind]


# --------------------------------------------------------------------------
# Derived values: the generator writes them, the validator recomputes them
# --------------------------------------------------------------------------


def _declared(entries, via: str) -> list[str]:
    """ADR IDs a record names itself (its entries whose applies_via includes ``via``)."""
    return [e.get("id") for e in entries or [] if isinstance(e, dict) and via in (e.get("applies_via") or [])]


def _adr_links(via: dict[str, list[str]], bundle: Bundle) -> list[dict]:
    out = []
    for adr_id in sorted(via, key=lambda i: pr.natural_key(i or "")):
        adr = bundle.adr_by_id.get(adr_id, {})
        out.append({"id": adr_id, "status": adr.get("status", "proposed"), "applies_via": via[adr_id]})
    return out


def governing(adr: dict) -> bool:
    """Accepted and proposed ADRs reach other records; rejected, superseded and deprecated ones never do."""
    return adr.get("status") not in INACTIVE_ADR


def requirement_adrs(req: dict, bundle: Bundle) -> list[dict]:
    """ADRs that materially affect a requirement: named by it, or naming it."""
    via: dict[str, list[str]] = {}
    for adr_id in _declared(req.get("architecture_decisions"), "requirement"):
        via.setdefault(adr_id, []).append("requirement")
    for adr in bundle.adrs:
        if governing(adr) and req.get("id") in (adr.get("related_requirements") or []):
            via.setdefault(adr["id"], []).append("adr")
    return _adr_links(via, bundle)


def requirement_adr_ids(rid: str, bundle: Bundle) -> list[str]:
    """ADRs that spread from a requirement to the features and tasks built on it."""
    req = bundle.req_by_id.get(rid)
    if req is None:
        return []
    return [link["id"] for link in requirement_adrs(req, bundle)
            if governing(bundle.adr_by_id.get(link["id"], {"status": "proposed"}))]


def feature_adrs(feature: dict, bundle: Bundle) -> list[dict]:
    """ADRs a feature must respect: named by it or by the ADR, or reached through its requirements or modules."""
    via: dict[str, list[str]] = {}
    for adr_id in _declared(feature.get("architecture_decisions"), "feature"):
        via.setdefault(adr_id, []).append("feature")
    for adr in bundle.adrs:
        if governing(adr) and feature.get("id") in (adr.get("related_features") or []):
            via.setdefault(adr["id"], []).append("adr")
    for rid in sorted(feature.get("requirement_ids") or [], key=pr.natural_key):
        for adr_id in requirement_adr_ids(rid, bundle):
            via.setdefault(adr_id, []).append(f"requirement:{rid}")
    modules = set(feature.get("module_ids") or [])
    for adr in bundle.adrs:
        if governing(adr):
            for mod in sorted(modules & set(adr.get("affected_modules") or []), key=pr.natural_key):
                via.setdefault(adr["id"], []).append(f"module:{mod}")
    return _adr_links(via, bundle)


def applicable_adrs(task: dict, bundle: Bundle) -> list[dict]:
    """ADRs that apply to a task: named by it, or linked by requirement, module or its feature."""
    via: dict[str, list[str]] = {}
    for adr_id in _declared(task.get("architecture_decisions"), "task"):
        via.setdefault(adr_id, []).append("task")
    for rid in sorted(task.get("source_requirements", []) or [], key=pr.natural_key):
        for adr_id in requirement_adr_ids(rid, bundle):
            via.setdefault(adr_id, []).append(f"requirement:{rid}")
    modules = set(task.get("related_modules", []) or [])
    for adr in bundle.adrs:
        if governing(adr):
            for mod in sorted(modules & set(adr.get("affected_modules", []) or []), key=pr.natural_key):
                via.setdefault(adr["id"], []).append(f"module:{mod}")
    feature = bundle.feat_by_id.get(task.get("feature")) if task.get("feature") else None
    if feature is not None:
        # Only decisions the feature states directly, or that name the feature, bind all of its tasks;
        # a decision reached through one of the feature's requirements binds the tasks for that requirement.
        for link in feature_adrs(feature, bundle):
            if {"feature", "adr"} & set(link["applies_via"]) and governing(bundle.adr_by_id.get(link["id"], {})):
                via.setdefault(link["id"], []).append(f"feature:{feature['id']}")
    return _adr_links(via, bundle)


def architecture_summary(adrs: list[dict], coverage: list[dict]) -> dict:
    counts = {status: sum(1 for a in adrs if a.get("status") == status)
              for status in ("accepted", "proposed", "rejected", "superseded", "deprecated")}
    counts["decisions_required"] = sum(1 for c in coverage if c.get("status") == "decision_required")
    return counts


def active_successor(adr_id: str, bundle: Bundle) -> str | None:
    """Follow 'superseded by' links to the decision that governs now, if any."""
    seen: set[str] = set()
    current = bundle.adr_by_id.get(adr_id, {}).get("superseded_by")
    while current and current not in seen:
        seen.add(current)
        successor = bundle.adr_by_id.get(current)
        if successor is None:
            return None
        if successor.get("status") == "accepted":
            return current
        current = successor.get("superseded_by")
    return None


def expected_architecture_trace(bundle: Bundle) -> list[dict]:
    """For every ADR: what it governs. Declared links on both sides, plus derived feature and task reach."""
    req_links = {r["id"]: {link["id"] for link in requirement_adrs(r, bundle)} for r in bundle.requirements if "id" in r}
    feat_links = {f["id"]: {link["id"] for link in feature_adrs(f, bundle)} for f in bundle.features if "id" in f}
    task_links = {t["id"]: {link.get("id") for link in t.get("architecture_decisions") or []} for t in bundle.tasks if "id" in t}
    out = []
    for adr in sorted(bundle.adrs, key=lambda a: pr.natural_key(a.get("id", ""))):
        aid = adr.get("id")
        out.append({
            "adr_id": aid,
            "status": adr.get("status"),
            "active": adr.get("status") == "accepted",
            "requirement_ids": sorted(set(adr.get("related_requirements") or []) | {r for r, ids in req_links.items() if aid in ids},
                                      key=pr.natural_key),
            "feature_ids": sorted(set(adr.get("related_features") or []) | {f for f, ids in feat_links.items() if aid in ids},
                                  key=pr.natural_key),
            "task_ids": sorted((t for t, ids in task_links.items() if aid in ids), key=pr.natural_key),
            "module_ids": sorted(adr.get("affected_modules") or [], key=pr.natural_key),
            "supersedes": sorted(adr.get("supersedes") or [], key=pr.natural_key),
            "superseded_by": adr.get("superseded_by"),
        })
    return out


def expected_open_questions(task: dict, bundle: Bundle) -> set[str]:
    targets = {task.get("id")} | set(task.get("source_requirements", []) or [])
    return {
        q["id"] for q in bundle.questions
        if not q.get("resolved") and targets & set(q.get("affected_ids", []) or [])
    }


# The Definition of Ready, as named checks. Every READY task must pass all of them; the generator and the
# validator evaluate them from the JSON alone, so a status of READY is earned, never declared.
READINESS_CHECKS = (
    "specification_ready", "task_id_valid", "title_clear", "objective_clear", "source_requirement_valid",
    "feature_valid", "scope_valid", "acceptance_criteria_valid", "acceptance_criteria_testable", "dependencies_valid",
    "external_dependencies_available", "architecture_valid", "architecture_conflicts_clear", "security_valid",
    "data_impact_known", "api_impact_known", "ui_impact_known", "integration_impact_known", "verification_defined",
    "open_questions_clear", "not_stale", "review_findings_clear", "blocking_risks_clear",
)
# The planning status a failed check points to, most urgent first. A failure may carry its own.
STATUS_HINT = {
    "not_stale": "NEEDS_REVIEW", "review_findings_clear": "NEEDS_REVIEW", "architecture_conflicts_clear": "NEEDS_REVIEW",
    "open_questions_clear": "NEEDS_DISCOVERY", "dependencies_valid": "BLOCKED", "external_dependencies_available": "BLOCKED",
    "blocking_risks_clear": "BLOCKED",
}
HINT_ORDER = ("NEEDS_REVIEW", "NEEDS_DISCOVERY", "BLOCKED", "DRAFT")
# Acceptance-criterion wording that nobody can observe or test.
UNTESTABLE_WORDING = ["work well", "works well", "working properly", "properly", "correctly", "as expected",
                      "appropriately", "user-friendly", "user friendly", "intuitive", "seamless", "seamlessly",
                      "fast", "quickly", "easily", "robust", "nice", "good experience", "etc", "and so on"]
# Areas where a task must state its security behaviour; "N/A" is not accepted for them.
SENSITIVE_AREAS = [
    ("authentication", r"\b(authenticat\w*|log ?in|sign[- ]?in|password\w*|session\w*|two-factor|mfa)\b"),
    ("authorisation", r"\b(authori[sz]\w*|permission\w*|roles?|access control|privilege\w*)\b"),
    ("payments", r"\b(payments?|billing|card numbers?|refunds?|invoices?|checkout)\b"),
    ("personal data", r"\b(personal data|pii|date of birth|passport|phone numbers?|email address\w*|home address\w*)\b"),
    ("secrets", r"\b(secrets?|credentials?|api keys?|tokens?|private keys?)\b"),
    ("file uploads", r"\b(uploads?|uploaded|attachments?)\b"),
    ("external APIs", r"\b(external api\w*|third[- ]party|webhooks?)\b"),
    ("administrative actions", r"\b(admin\w*|administrat\w*|suspend\w*|impersonat\w*)\b"),
    ("account recovery", r"\b(recover\w*|resets?|forgot\w*)\b"),
    ("audit", r"\b(audit\w*)\b"),
]
IMPACT_KINDS = ("data", "api", "ui", "integration")
API_CHANGES = ("none", "create", "modify", "remove")
FAILURE_WORDING = re.compile(r"\b(fail\w*|unavailable|time ?outs?|timed out|errors?|retr(?:y|ies|ied)|fallback|down|reject\w*)\b",
                             re.IGNORECASE)


def task_text(task: dict, bundle: Bundle | None = None, with_requirements: bool = False) -> str:
    parts = [task.get("title") or "", task.get("objective") or "", task.get("description") or "",
             " ".join(task.get("acceptance_criteria") or [])]
    if with_requirements and bundle is not None:
        for rid in task.get("source_requirements") or []:
            req = bundle.req_by_id.get(rid, {})
            parts += [req.get("title") or "", req.get("description") or "", req.get("permissions") or ""]
    return " ".join(parts)


def sensitive_areas(task: dict, bundle: Bundle) -> list[str]:
    text = task_text(task, bundle, with_requirements=True)
    return [name for name, pattern in SENSITIVE_AREAS if re.search(pattern, text, re.IGNORECASE)]


def impact_signals(task: dict, bundle: Bundle) -> dict[str, list[str]]:
    """Why each impact kind applies to a task. An impact nobody needs is not demanded."""
    blob = " ".join([task_text(task), json.dumps(task.get("details") or {}, ensure_ascii=False)])
    ids = pr.extract_ids(blob)
    sources = task.get("source_requirements") or []
    kind_type = task.get("type")
    signals: dict[str, list[str]] = {k: [] for k in IMPACT_KINDS}
    signals["data"] += [f"implements {r}" for r in sources if pr.kind_of(r) == "DR"]
    signals["data"] += [f"names {i}" for i in ids if pr.kind_of(i) == "ENT"]
    signals["data"] += ["type database"] if kind_type == "database" else []
    signals["api"] += [f"names {i}" for i in ids if pr.kind_of(i) == "API"]
    signals["api"] += [f"implements {r}" for r in sources if pr.kind_of(r) == "IR"]
    signals["ui"] += [f"names {i}" for i in ids if pr.kind_of(i) == "PAGE"]
    signals["ui"] += [f"implements {r}" for r in sources if pr.kind_of(r) == "UXR"]
    signals["ui"] += [f"type {kind_type}"] if kind_type in ("frontend", "fullstack", "design") else []
    signals["integration"] += [f"names {i}" for i in ids if pr.kind_of(i) == "INT"]
    signals["integration"] += [f"implements {r}" for r in sources if pr.kind_of(r) == "IR"]
    signals["integration"] += [f"relies on {d}" for d in task.get("external_dependencies") or []]
    signals["integration"] += ["type integration"] if kind_type == "integration" else []
    return signals


def _rejected_option_hits(bundle: Bundle) -> dict[str, list[tuple[dict, str]]]:
    """Live requirements, features and tasks that name an option an accepted ADR considered and rejected."""
    cached = getattr(bundle, "_rejected_hits", None)
    if cached is not None:
        return cached
    rejected = []
    for adr in bundle.adrs:
        if adr.get("status") != "accepted":
            continue
        for alt in adr.get("alternatives") or []:
            pattern = _option_pattern(alt.get("option") or "")
            if pattern and "reject" in (alt.get("outcome") or "").lower():
                rejected.append((adr, alt.get("option"), pattern))
    hits: dict[str, list[tuple[dict, str]]] = {}
    if rejected:
        texts = []
        for req in bundle.requirements:
            if in_release(req):
                texts.append((req.get("id"), " ".join([req.get("title", ""), req.get("description", "")])))
        for feature in bundle.features:
            if feature.get("scope") in (None, "in_scope", "pending_decision") and feature.get("status") != "CANCELLED":
                texts.append((feature.get("id"), " ".join([feature.get("title", ""), feature.get("goal", "")])))
        for task in bundle.tasks:
            if task.get("status") != "CANCELLED":
                constraints = task.get("constraints") or {}
                parts = [task.get("title", ""), task.get("description", "")]
                parts += [c for kind, values in constraints.items() if kind != "not_applicable" for c in values or []]
                texts.append((task.get("id"), " ".join(parts)))
        for item_id, text in texts:
            lowered = text.lower()
            for adr, option, pattern in rejected:
                if pattern.search(lowered):
                    hits.setdefault(item_id, []).append((adr, option))
    bundle._rejected_hits = hits
    return hits


def architecture_conflicts(item_ids: set[str], bundle: Bundle) -> list[str]:
    """Unresolved ARCHITECTURE CONFLICTs on these items: open conflict reviews, and rejected options that no
    resolved or withdrawn review accounts for."""
    out = []
    reviews = bundle.architecture.get("conflict_reviews") or []
    for review in reviews:
        if item_ids & set(review.get("affected_ids") or []) and review.get("status") not in ("RESOLVED", "WITHDRAWN"):
            out.append(f"ARCHITECTURE CONFLICT {review.get('finding_id')} with {', '.join(review.get('adr_ids') or []) or 'an ADR'} "
                       f"is {review.get('status') or 'OPEN'} ({pr.ARCHITECTURE_REVIEW_FILE}).")
    hits = _rejected_option_hits(bundle)
    for item in sorted(item_ids, key=lambda i: pr.natural_key(i or "")):
        for adr, option in hits.get(item, []):
            settled = any(item in (r.get("affected_ids") or []) and adr["id"] in (r.get("adr_ids") or [])
                          and r.get("status") in ("RESOLVED", "WITHDRAWN") for r in reviews)
            if not settled:
                out.append(f"ARCHITECTURE CONFLICT: {item} mentions '{option}', which accepted {adr['id']} rejected, and no "
                           f"architecture review finding resolves or withdraws it.")
    return out


def readiness_failures(task: dict, bundle: Bundle, unsequenced: set[str]) -> list[tuple[str, str, str]]:
    """Every Definition of Ready failure as (check, message, planning status it points to), in a fixed order."""
    out: list[tuple[str, str, str]] = []

    def fail(check: str, message: str, hint: str | None = None) -> None:
        out.append((check, message, hint or STATUS_HINT.get(check, "DRAFT")))

    tbd = lambda value: pr.has_tbd(value if isinstance(value, str) else json.dumps(value))  # noqa: E731
    tid = task.get("id") or ""

    # The specification the task rests on is approved and has passed its independent review.
    if not bundle.spec_approved:
        fail("specification_ready", f"Specification is not approved (status: {bundle.project.get('specification_status')}).")
    review_gap = bundle.review_gap()
    if review_gap:
        fail("specification_ready", review_gap, "NEEDS_REVIEW")

    # Identity, title, objective.
    if not pr.FULL_ID_RE["TASK"].match(tid):
        fail("task_id_valid", f"Task ID {tid!r} is not TASK-### or TASK-###-S##.")
    elif "-S" in tid:
        parent = tid.rsplit("-S", 1)[0]
        if task.get("parent_task") != parent or parent not in bundle.task_by_id:
            fail("task_id_valid", f"Subtask {tid} must name its parent {parent}, which must exist.")
    title = (task.get("title") or "").strip()
    if tbd(title) or len(title.split()) < 3:
        fail("title_clear", "Title does not state an outcome (at least three words, no TBD).")
    if not (task.get("objective") or "").strip():
        fail("objective_clear", "Objective is not stated ('Objective' or 'Goal': the outcome and why it matters).")
    elif tbd(task.get("objective")):
        fail("objective_clear", "Objective contains TBD.")
    if not (task.get("description") or "").strip():
        fail("objective_clear", "Description is empty.")
    elif tbd(task.get("description")):
        fail("objective_clear", "Description contains TBD.")

    # Traceability to approved, in-scope requirements.
    requirements = task.get("source_requirements", []) or []
    if not requirements:
        fail("source_requirement_valid", "No source requirement is linked.")
    for req_id in requirements:
        req = bundle.req_by_id.get(req_id)
        if req is None:
            fail("source_requirement_valid", f"Source requirement {req_id} does not exist.")
        elif req.get("status") != "approved":
            fail("source_requirement_valid", f"Source requirement {req_id} is {req.get('status')}, not approved.")
        elif req.get("scope") != "in_scope":
            fail("source_requirement_valid", f"Source requirement {req_id} is not in scope (scope: {req.get('scope') or 'unclassified'}).")

    # Parent feature and scope.
    feature = bundle.feat_by_id.get(task.get("feature")) if task.get("feature") else None
    if not task.get("feature"):
        fail("feature_valid", "Task belongs to no feature.")
    elif feature is None:
        fail("feature_valid", f"Feature {task.get('feature')} does not exist.")
    else:
        if feature.get("status") == "CANCELLED":
            fail("feature_valid", f"Feature {feature['id']} is CANCELLED.")
        if task.get("epic") and feature.get("epic") != task.get("epic"):
            fail("feature_valid", f"Task names epic {task.get('epic')}, but {feature['id']} belongs to {feature.get('epic')}.")
        if feature.get("scope") != "in_scope":
            fail("scope_valid", f"Feature {feature['id']} is not in scope (scope: {feature.get('scope') or 'unclassified'}).")
    if task.get("scope") != "in_scope" and (feature is None or feature.get("scope") == "in_scope"):
        fail("scope_valid", f"Task is not in scope (scope: {task.get('scope') or 'unclassified'}).")

    # Acceptance criteria: present, free of TBD, observable, aligned with the source requirements.
    criteria = task.get("acceptance_criteria", []) or []
    if not criteria:
        fail("acceptance_criteria_valid", "No acceptance criteria.")
    elif any(tbd(c) for c in criteria):
        fail("acceptance_criteria_valid", "An acceptance criterion contains TBD.")
    for criterion in criteria:
        lowered = f" {criterion.lower()} "
        vague = [w for w in UNTESTABLE_WORDING if re.search(rf"(?<![\w-]){re.escape(w)}(?![\w-])", lowered)]
        if vague:
            fail("acceptance_criteria_testable", f"Acceptance criterion '{criterion}' is not observable ({', '.join(vague)}).")
    for ac_id in acceptance_ids(task):
        owners = bundle.ac_owners.get(ac_id, set())
        if owners and not owners & set(requirements):
            fail("acceptance_criteria_testable", f"{ac_id} belongs to {', '.join(sorted(owners, key=pr.natural_key))}, "
                                                 f"which the task does not implement.")

    # Dependencies: reviewed, existing, acyclic, active, in scope and themselves READY.
    if not task.get("dependencies_reviewed"):
        fail("dependencies_valid", "Dependencies have not been reviewed ('Blocked By' is blank or TBD).", "DRAFT")
    for dep in task.get("dependencies", []) or []:
        predecessor = bundle.task_by_id.get(dep)
        if dep == tid:
            fail("dependencies_valid", f"{tid} depends on itself.", "DRAFT")
        elif predecessor is None:
            fail("dependencies_valid", f"Dependency {dep} does not exist.", "DRAFT")
        elif predecessor.get("status") == "CANCELLED":
            fail("dependencies_valid", f"Dependency {dep} is CANCELLED.", "DRAFT")
        elif predecessor.get("scope") != "in_scope":
            fail("dependencies_valid", f"Dependency {dep} is not in scope (scope: {predecessor.get('scope') or 'unclassified'}).", "DRAFT")
        elif predecessor.get("status") not in DEPENDENCY_OK:
            fail("dependencies_valid", f"Dependency {dep} is {predecessor.get('status')}; it must be READY.")
    if tid in unsequenced:
        fail("dependencies_valid", "Task is in, or depends on, a dependency cycle.", "DRAFT")
    for dep_id in task.get("external_dependencies", []) or []:
        external = bundle.dep_by_id.get(dep_id)
        if external is None:
            fail("external_dependencies_available", f"External dependency {dep_id} does not exist.")
        elif external.get("status") != "AVAILABLE":
            fail("external_dependencies_available", f"External dependency {dep_id} is {external.get('status')}, not AVAILABLE.")

    # Architecture: constraints documented, every applicable ADR accepted, no unresolved conflict.
    constraints = task.get("constraints", {}) or {}
    not_applicable = constraints.get("not_applicable", {}) or {}
    adrs = task.get("architecture_decisions", []) or []
    if not (constraints.get("architecture") or adrs or not_applicable.get("architecture")):
        fail("architecture_valid", "Architecture constraints are not documented (list them, link an ADR, or record N/A with a reason).")
    for entry in adrs:
        adr = bundle.adr_by_id.get(entry.get("id"))
        if adr is None:
            fail("architecture_valid", f"Architecture decision {entry.get('id')} does not exist.")
        elif adr.get("status") != "accepted":
            fail("architecture_valid", f"Architecture decision {entry.get('id')} is {adr.get('status')}, not accepted.")
    for conflict in architecture_conflicts({tid, task.get("feature")} - {None}, bundle):
        fail("architecture_conflicts_clear", conflict)

    # Security: stated for sensitive work; N/A only where nothing sensitive is involved.
    areas = sensitive_areas(task, bundle)
    if constraints.get("security"):
        pass
    elif not_applicable.get("security") and areas:
        fail("security_valid", f"The task involves {', '.join(areas)}; its security behaviour must be stated, not N/A. "
                               f"Where it is undefined, raise it for review.", "NEEDS_REVIEW")
    elif not not_applicable.get("security"):
        fail("security_valid", "Security requirements are not documented (list them, or record N/A with a reason).",
             "NEEDS_REVIEW" if areas else "DRAFT")
    if any(tbd(c) for kind in ("architecture", "security", "performance", "data", "compliance", "other")
           for c in constraints.get(kind, []) or []):
        fail("security_valid" if any(tbd(c) for c in constraints.get("security", []) or []) else "architecture_valid",
             "A constraint contains TBD.")

    # Data, API, UI and integration impact: known wherever the task touches them.
    impacts = task.get("impacts") or {}
    signals = impact_signals(task, bundle)
    labels = {"data": "Data impact", "api": "API impact", "ui": "UI impact", "integration": "Integration impact"}
    for kind in IMPACT_KINDS:
        impact = impacts.get(kind) or {}
        check = f"{kind}_impact_known"
        if not impact.get("stated"):
            if signals[kind]:
                fail(check, f"{labels[kind]} is not stated although the task {'; '.join(signals[kind][:3])}. State it, "
                            f"or record 'None — reason'.")
            continue
        text = impact.get("text") or ""
        if tbd(text):
            fail(check, f"{labels[kind]} contains TBD.", "BLOCKED" if kind == "integration" else None)
            continue
        if impact.get("not_applicable"):
            continue
        if kind == "data" and not [i for i in impact.get("ids") or [] if pr.kind_of(i) == "ENT"]:
            fail(check, "Data impact names no affected entity (ENT-###).")
        if kind == "api" and impact.get("change") not in API_CHANGES:
            fail(check, "API impact does not state its change: NONE, CREATE, MODIFY or REMOVE.")
        if kind == "integration" and not FAILURE_WORDING.search(text):
            fail(check, "Integration impact does not state failure, timeout and retry, or fallback behaviour.", "BLOCKED")

    # Verification.
    verification = task.get("verification", {}) or {}
    if not verification.get("required_tests"):
        fail("verification_defined", "Required verification method is not defined ('Required test levels').")
    for test_id in verification.get("test_ids", []) or []:
        if test_id not in bundle.test_by_id:
            fail("verification_defined", f"Test {test_id} does not exist.")

    # Nothing open that blocks it: questions, blockers, change review, review findings, blocking risks.
    for issue in task.get("blocking_issues", []) or []:
        unreviewed = issue.startswith("Readiness blockers have not been reviewed")
        fail("open_questions_clear", issue if unreviewed else f"Unresolved blocker: {issue}", "DRAFT" if unreviewed else "BLOCKED")
    questions = expected_open_questions(task, bundle) | {
        q.get("id") for q in task.get("open_questions", []) or [] if isinstance(q, dict) and q.get("id")
    }
    for question in sorted(questions, key=pr.natural_key):
        register = bundle.q_by_id.get(question)
        if register is not None and not register.get("resolved") and register.get("blocking", True):
            fail("open_questions_clear", f"Unresolved critical question {question}.")
    review = bundle.artifact_state.get(tid)
    if review and review.get("state") != "CURRENT":
        fail("not_stale", f"Under change review: {review.get('state')} ({', '.join(review.get('change_ids') or [])}).")
    targets = {tid, task.get("feature"), task.get("epic"), *requirements} - {None}
    for finding in bundle.review_findings:
        if finding.get("severity") in ("CRITICAL", "MAJOR") and sr.is_unresolved(finding.get("severity"), finding.get("status")) \
                and targets & set(finding.get("affected_artifacts") or []):
            fail("review_findings_clear", f"{finding.get('severity')} specification review finding {finding.get('id')} is "
                                          f"{finding.get('status')}: {finding.get('title')}.")
    for risk in blocking_risks(task, bundle):
        fail("blocking_risks_clear", f"{risk['id']} blocks readiness and is {risk.get('status')}: {risk.get('description')}")
    return out


def blocking_risks(task: dict, bundle: Bundle) -> list[dict]:
    """Risks the register marks as blocking readiness, still live, that name the task, its feature or requirements."""
    targets = {task.get("id"), task.get("feature"), *(task.get("source_requirements") or [])} - {None}
    return [r for r in bundle.risks
            if r.get("blocks_readiness") and r.get("status") in ("OPEN", "MITIGATING", "OCCURRED")
            and (targets & set(r.get("affected_ids") or []) or r.get("id") in (task.get("risk_ids") or []))]


def accepted_review_risks(task: dict, bundle: Bundle) -> list[str]:
    """Specification review findings accepted as risks that concern the task: kept visible, never blocking."""
    targets = {task.get("id"), task.get("feature"), task.get("epic"), *(task.get("source_requirements") or [])} - {None}
    return sorted((f.get("id") for f in bundle.review_findings if f.get("status") == "ACCEPTED_RISK"
                   and targets & set(f.get("affected_artifacts") or [])), key=lambda i: pr.natural_key(i or ""))


def readiness_evaluation(task: dict, bundle: Bundle, unsequenced: set[str]) -> dict:
    """The task's readiness result: every named check, its failures, and the planning status they point to."""
    if task.get("status") == "CANCELLED":
        return {"result": "NOT_APPLICABLE", "checks": {c: True for c in READINESS_CHECKS}, "failures": [],
                "recommended_status": "CANCELLED", "accepted_risk_findings": accepted_review_risks(task, bundle)}
    failures = readiness_failures(task, bundle, unsequenced)
    failed = {check for check, _, _ in failures}
    hints = {hint for _, _, hint in failures}
    return {
        "result": "FAIL" if failures else "PASS",
        "checks": {check: check not in failed for check in READINESS_CHECKS},
        "failures": [message for _, message, _ in failures],
        "recommended_status": next((h for h in HINT_ORDER if h in hints), "DRAFT") if failures else "READY",
        "accepted_risk_findings": accepted_review_risks(task, bundle),
    }


def readiness_gaps(task: dict, bundle: Bundle, unsequenced: set[str]) -> list[str]:
    """Definition of Ready conditions the task does not meet, in a fixed order."""
    if task.get("status") == "CANCELLED":
        return []
    return [message for _, message, _ in readiness_failures(task, bundle, unsequenced)]


def derived_blocks(tasks: list[dict]) -> dict[str, list[str]]:
    blocks: dict[str, list[str]] = {t.get("id"): [] for t in tasks}
    for task in tasks:
        for dep in task.get("dependencies", []) or []:
            if dep in blocks and task.get("id") not in blocks[dep]:
                blocks[dep].append(task.get("id"))
    return {k: sorted(v, key=pr.natural_key) for k, v in blocks.items()}


def acceptance_ids(item: dict) -> list[str]:
    out = []
    for criterion in item.get("acceptance_criteria", []) or []:
        head = str(criterion).split(":", 1)[0].strip()
        if pr.FULL_ID_RE["AC"].match(head) and head not in out:
            out.append(head)
    return sorted(out, key=pr.natural_key)


def expected_traceability(bundle: Bundle) -> tuple[list[dict], list[dict], dict, dict]:
    reqs = sorted(bundle.requirements, key=lambda r: pr.natural_key(r.get("id", "")))
    tasks = sorted(bundle.tasks, key=lambda t: pr.natural_key(t.get("id", "")))
    downstream: dict[str, set[str]] = {r["id"]: set() for r in reqs}
    for req in reqs:
        for upstream in req.get("source", []) or []:
            downstream.setdefault(upstream, set()).add(req["id"])
    # A business rule is realised by whatever cites it as a dependency.
    for req in reqs:
        for dep in req.get("dependencies", []) or []:
            if pr.kind_of(dep) == "RULE":
                downstream.setdefault(dep, set()).add(req["id"])

    records = []
    summary = dict.fromkeys(
        ["in_release_requirements", "covered", "missing_task", "missing_test", "missing_task_and_test",
         "missing_downstream", "excluded", "tasks_without_requirements"], 0,
    )
    for req in reqs:
        rid = req["id"]
        task_ids = sorted({t["id"] for t in tasks if rid in (t.get("source_requirements") or [])}, key=pr.natural_key)
        feature_ids = {f["id"] for f in bundle.features if rid in (f.get("requirement_ids") or [])}
        feature_ids |= {t["feature"] for t in tasks if t.get("feature") and rid in (t.get("source_requirements") or [])}
        test_ids = sorted({t["id"] for t in bundle.tests if rid in (t.get("requirement_ids") or [])}, key=pr.natural_key)
        adr_ids = sorted({link["id"] for link in requirement_adrs(req, bundle)}, key=pr.natural_key)
        # A task that applies a business rule directly realises it too.
        for tid in task_ids:
            if pr.kind_of(rid) == "RULE":
                downstream.setdefault(rid, set()).add(tid)

        if not in_release(req):
            coverage = "excluded"
        elif req.get("type") in REALISED_DOWNSTREAM:
            coverage = "covered" if downstream.get(rid) else "missing_downstream"
        elif task_ids and test_ids:
            coverage = "covered"
        elif task_ids:
            coverage = "missing_test"
        elif test_ids:
            coverage = "missing_task"
        else:
            coverage = "missing_task_and_test"
        summary[coverage] += 1
        if coverage != "excluded":
            summary["in_release_requirements"] += 1

        records.append({
            "requirement_id": rid,
            "requirement_type": req.get("type"),
            "status": req.get("status"),
            "upstream_requirement_ids": sorted(req.get("source", []) or [], key=pr.natural_key),
            "downstream_requirement_ids": sorted(
                (d for d in downstream.get(rid, set()) if pr.kind_of(d) in pr.REQUIREMENT_KINDS), key=pr.natural_key
            ),
            "feature_ids": sorted(feature_ids, key=pr.natural_key),
            "task_ids": task_ids,
            "test_ids": test_ids,
            "adr_ids": adr_ids,
            "coverage": coverage,
            "scope": req.get("scope"),
            "module_ids": sorted(req.get("related_modules", []) or [], key=pr.natural_key),
            "process_ids": sorted((p["id"] for p in bundle.processes if rid in (p.get("related_requirements") or [])),
                                  key=pr.natural_key),
        })

    task_records = []
    for task in tasks:
        if not task.get("source_requirements"):
            summary["tasks_without_requirements"] += 1
        task_records.append({
            "task_id": task["id"],
            "requirement_ids": sorted(task.get("source_requirements", []) or [], key=pr.natural_key),
            "feature_id": task.get("feature"),
            "epic_id": task.get("epic"),
            "test_ids": sorted((task.get("verification") or {}).get("test_ids", []) or [], key=pr.natural_key),
            "acceptance_criteria_ids": acceptance_ids(task),
            "adr_ids": sorted((a.get("id") for a in task.get("architecture_decisions", []) or []), key=pr.natural_key),
            "delivery": {"pull_requests": [], "commits": [], "releases": []},
        })

    orphans = {
        # Everything except a business goal needs a reason upstream; a rule's
        # reason may be its evidence, so rules are judged by their use instead.
        "requirements": sorted(
            (r["id"] for r in reqs if in_release(r) and r.get("type") not in ("business_goal", "business_rule")
             and not r.get("source")), key=pr.natural_key),
        "features": sorted((f["id"] for f in bundle.features if not f.get("requirement_ids")), key=pr.natural_key),
        "tasks": sorted(
            (t["id"] for t in tasks if not t.get("source_requirements") or not t.get("feature")
             or not t.get("acceptance_criteria")), key=pr.natural_key),
    }
    return records, task_records, summary, orphans


def expected_handoff_status(error_count: int, bundle: Bundle) -> str:
    if error_count:
        return "invalid"
    ready = sum(1 for t in bundle.tasks if t.get("status") == "READY")
    return "ready" if bundle.spec_approved and bundle.review_gap() is None and ready else "not_ready"


def validation_flags(findings: Findings, bundle: Bundle) -> dict[str, bool]:
    """The manifest's validation flags: each is true when no error of that kind was found."""
    errors = findings.errors

    def clear(kind) -> bool:
        return not any(kind(e) for e in errors)

    def dependency_error(e: Finding) -> bool:
        unknown_task = e.code == "UNKNOWN_REFERENCE" and (" references task " in e.message or "unknown parent task" in e.message)
        return e.code in DEPENDENCY_GRAPH_CODES or unknown_task

    return {
        "schema_valid": clear(lambda e: e.step == STEP_SCHEMA),
        "traceability_valid": clear(lambda e: e.step == STEP_TRACE),
        "architecture_valid": clear(lambda e: e.code.startswith("ADR_") or e.code in ARCHITECTURE_CODES),
        "dependency_graph_valid": clear(dependency_error),
        "specification_review_passed": bundle.review_gap() is None,
        "backlog_readiness_valid": clear(lambda e: e.step == STEP_BACKLOG),
    }


def manifest_findings(manifest_bytes: bytes | None, raw: dict[str, bytes], bundle: Bundle, findings: Findings) -> Findings:
    """Check handoff-manifest.json against the files and against ``findings``, the validation result without it."""
    out = Findings()
    if manifest_bytes is None:
        out.error(STEP_SCHEMA, "MANIFEST_MISSING", "The handoff has no manifest; regenerate it.", MANIFEST_FILE)
        return out
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        out.error(STEP_SCHEMA, "JSON_SYNTAX", f"Not valid JSON: {exc}", MANIFEST_FILE)
        return out
    hc.check_manifest(manifest, raw, bundle, validation_flags(findings, bundle),
                      expected_handoff_status(len(findings.errors), bundle), SCHEMA_VERSION,
                      load_validators()[CONTRACT_PREFIX + hc.MANIFEST_SCHEMA], out, STEP_SCHEMA)
    return out


# --------------------------------------------------------------------------
# Semantic checks
# --------------------------------------------------------------------------


def _unique(items: list[dict], label: str, where: str, findings: Findings, step: str) -> None:
    seen: set[str] = set()
    for item in items:
        identifier = item.get("id")
        if identifier in seen:
            findings.error(step, "DUPLICATE_ID", f"{label} {identifier} is defined more than once.", where)
        seen.add(identifier)


def _refs(ids, exists, label: str, owner: str, where: str, findings: Findings, step: str, warn: bool = False) -> None:
    for identifier in ids or []:
        if not exists(identifier):
            message = f"{owner} references {label} {identifier}, which does not exist."
            (findings.warn if warn else findings.error)(step, "UNKNOWN_REFERENCE", message, where)


def business_chain(rid: str, bundle: Bundle) -> set[str]:
    """Every requirement reachable upstream through 'source' links."""
    seen: set[str] = set()
    stack = list(bundle.req_by_id.get(rid, {}).get("source") or [])
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        stack += list(bundle.req_by_id.get(current, {}).get("source") or [])
    return seen


def feature_closure(fid: str, bundle: Bundle) -> set[str]:
    seen: set[str] = set()
    stack = list(bundle.feat_by_id.get(fid, {}).get("dependencies") or [])
    while stack:
        current = stack.pop()
        if current in seen:
            continue
        seen.add(current)
        stack += list(bundle.feat_by_id.get(current, {}).get("dependencies") or [])
    return seen


def planning_findings(bundle: Bundle, f: Findings) -> None:
    """Scope, prioritisation, dependency, roadmap and domain-model checks."""
    # Prioritisation: one project-wide scheme, applied with discrimination.
    scheme = bundle.project.get("priority_scheme")
    prioritised = [(i.get("id"), i.get("priority")) for i in
                   bundle.requirements + bundle.epics + bundle.features + bundle.tasks
                   if i.get("priority") not in (None, "unspecified")]
    used = {value for _, value in prioritised}
    if scheme in SCHEME_VALUES:
        for identifier, value in prioritised:
            if value not in SCHEME_VALUES[scheme]:
                f.error(STEP_BACKLOG, "PRIORITY_SCHEME",
                        f"{identifier} has priority {value!r}, outside the project's {scheme} scheme.", "project.json")
    elif prioritised:
        if used & SCHEME_VALUES["levels"] and used & SCHEME_VALUES["moscow"]:
            f.error(STEP_BACKLOG, "PRIORITY_SCHEME", "Priorities mix Critical/High/Medium/Low with MoSCoW; choose one scheme.", "project.json")
        else:
            f.warn(STEP_BACKLOG, "PRIORITY_SCHEME_UNDECLARED", "Priorities are used but project-state.md declares no 'Priority scheme'.", "project.json")
    ranked = [r for r in bundle.requirements if in_release(r) and r.get("priority") not in (None, "unspecified")]
    if len(ranked) >= 4:
        top = sum(1 for r in ranked if r.get("priority") in TOP_PRIORITY)
        if top / len(ranked) > 0.6:
            f.warn(STEP_BACKLOG, "PRIORITY_NOT_DISCRIMINATING",
                   f"{top} of {len(ranked)} prioritised in-scope requirements carry the top priority; priority no longer separates what matters most.",
                   "requirements.json")

    # Features: dependencies, scope and decisions.
    edges = {x["id"]: [d for d in x.get("dependencies") or [] if d in bundle.feat_by_id] for x in bundle.features if "id" in x}
    for cycle in find_cycles(list(edges), edges):
        f.error(STEP_BACKLOG, "FEATURE_DEPENDENCY_CYCLE", f"Features depend on each other in a cycle: {' -> '.join(cycle + [cycle[0]])}.", "backlog.json")
    blocker_targets: dict[str, list[str]] = {}
    for q in bundle.questions:
        if q.get("blocking") and not q.get("resolved"):
            for target in q.get("affected_ids") or []:
                blocker_targets.setdefault(target, []).append(q["id"])
    for feature in bundle.features:
        fid, where = feature.get("id"), feature.get("source_path", "backlog.json")
        _refs(feature.get("dependencies"), lambda i: i in bundle.feat_by_id, "feature", fid, where, f, STEP_BACKLOG)
        _refs(feature.get("external_dependencies"), lambda i: i in bundle.dep_by_id, "external dependency", fid, where, f, STEP_BACKLOG)
        _refs(feature.get("module_ids"), lambda i: i in bundle.mod_by_id, "module", fid, where, f, STEP_BACKLOG)
        reqs = [bundle.req_by_id[r] for r in feature.get("requirement_ids") or [] if r in bundle.req_by_id]
        if feature.get("scope") == "in_scope" and reqs and not any(r.get("scope") == "in_scope" for r in reqs):
            f.warn(STEP_BACKLOG, "SCOPE_MISMATCH", f"{fid} is in scope but none of its requirements is.", where)
        if feature.get("scope") == "in_scope":
            for r in reqs:
                if r.get("scope") in ("out_of_scope", "future"):
                    f.warn(STEP_BACKLOG, "SCOPE_MISMATCH", f"{fid} is in scope but implements {r['id']}, which is {r['scope']}.", where)
        blockers = sorted({q for target in [fid, *(feature.get("requirement_ids") or [])] for q in blocker_targets.get(target, [])},
                          key=pr.natural_key)
        if blockers and feature.get("scope") == "in_scope":
            f.warn(STEP_BACKLOG, "BLOCKED_BY_DECISION", f"{fid} is in scope but depends on unresolved BLOCKER question(s) {', '.join(blockers)}.", where)

    # Tasks: hidden prerequisites and impossible sequencing.
    for task in bundle.tasks:
        tid, where = task.get("id"), task.get("source_path") or f"tasks/{task.get('id')}.json"
        _refs(task.get("external_dependencies"), lambda i: i in bundle.dep_by_id, "external dependency", tid, where, f, STEP_BACKLOG)
        for dep in task.get("dependencies") or []:
            predecessor = bundle.task_by_id.get(dep)
            if not predecessor:
                continue
            if task.get("scope") == "in_scope" and task.get("status") != "CANCELLED" and (
                    predecessor.get("scope") in ("out_of_scope", "future", "pending_decision")
                    or predecessor.get("status") == "CANCELLED"):
                what = "CANCELLED" if predecessor.get("status") == "CANCELLED" else predecessor.get("scope")
                f.error(STEP_BACKLOG, "IMPOSSIBLE_SEQUENCING", f"{tid} is in scope but depends on {dep}, which is {what}.", where)
            a, b = task.get("feature"), predecessor.get("feature")
            if a and b and a != b and b not in feature_closure(a, bundle):
                f.warn(STEP_BACKLOG, "HIDDEN_PREREQUISITE",
                       f"{tid} ({a}) depends on {dep} ({b}), but {a} does not declare a dependency on {b}.", where)

    # External dependencies and roadmap commitments.
    for dep in bundle.dependencies:
        _refs(dep.get("risk_ids"), lambda i: i in bundle.risk_by_id, "risk", dep.get("id"), "backlog.json", f, STEP_BACKLOG, warn=True)
        for ref in dep.get("needed_for") or []:
            if bundle.known(ref) is False:
                f.warn(STEP_BACKLOG, "UNKNOWN_REFERENCE", f"{dep.get('id')} is needed for {ref}, which does not exist.", "backlog.json")
    for phase in bundle.phases:
        if phase.get("date_basis") == "commitment":
            decision = phase.get("commitment_decision")
            if not decision or decision not in bundle.dec_by_id:
                f.error(STEP_BACKLOG, "UNSUPPORTED_COMMITMENT",
                        f"{phase.get('id')} states a committed date without an existing decision recording the commitment.",
                        phase.get("source_path", "backlog.json"))

    # Process and domain model.
    for proc in bundle.processes:
        pid, where = proc.get("id"), proc.get("source_path", "domain.json")
        _refs(proc.get("data_involved"), lambda i: i in bundle.ent_by_id, "entity", pid, where, f, STEP_REQ)
        _refs(proc.get("business_rules"), lambda i: i in bundle.req_by_id, "business rule", pid, where, f, STEP_REQ)
        _refs(proc.get("related_requirements"), lambda i: i in bundle.req_by_id, "requirement", pid, where, f, STEP_REQ)
        if proc.get("compares_to"):
            base = bundle.proc_by_id.get(proc["compares_to"])
            if base is None:
                f.error(STEP_REQ, "UNKNOWN_REFERENCE", f"{pid} replaces {proc['compares_to']}, which does not exist.", where)
            elif base.get("perspective") != "as_is":
                f.error(STEP_REQ, "PROCESS_COMPARISON", f"{pid} replaces {proc['compares_to']}, which is not an AS-IS process.", where)
            if not proc.get("differences"):
                f.warn(STEP_REQ, "PROCESS_COMPARISON", f"{pid} replaces {proc['compares_to']} but lists no differences.", where)
    for ent in bundle.entities:
        eid, where = ent.get("id"), ent.get("source_path", "domain.json")
        _refs(ent.get("business_rules"), lambda i: i in bundle.req_by_id, "business rule", eid, where, f, STEP_REQ)
        _refs(ent.get("related_requirements"), lambda i: i in bundle.req_by_id, "requirement", eid, where, f, STEP_REQ)
    for module in bundle.modules:
        _refs(module.get("data_ownership"), lambda i: i in bundle.ent_by_id, "entity", module.get("id"), pr.SOLUTION_FILE, f, STEP_REQ)

    # Registers.
    for risk in bundle.risks:
        for ref in risk.get("affected_ids") or []:
            if bundle.known(ref) is False:
                f.warn(STEP_REQ, "UNKNOWN_REFERENCE", f"Risk {risk.get('id')} names {ref}, which does not exist.", "decisions.json")
    for decision in bundle.decisions:
        _refs(decision.get("related_requirements"), lambda i: i in bundle.req_by_id, "requirement", decision.get("id"), "decisions.json", f, STEP_REQ, warn=True)
    for item in bundle.scope_items:
        for ref in item.get("related_ids") or []:
            if bundle.known(ref) is False:
                f.warn(STEP_REQ, "UNKNOWN_REFERENCE", f"Scope item {item.get('id')} names {ref}, which does not exist.", "requirements.json")


def _option_pattern(option: str) -> re.Pattern | None:
    words = option.strip().lower()
    if len(re.sub(r"\W", "", words)) < 4:
        return None
    return re.compile(rf"(?<![\w-]){re.escape(words)}(?![\w-])")


def architecture_findings(bundle: Bundle, f: Findings) -> None:
    """Architecture governance: ADR lifecycle and approval, supersession, conflicts between active
    decisions, references to inactive decisions, and drift from accepted decisions."""
    adrs = bundle.adr_by_id

    def where_of(adr: dict) -> str:
        return adr.get("source_path") or "architecture.json"

    for adr in bundle.adrs:
        aid, where, status = adr.get("id"), where_of(adr), adr.get("status")
        _refs(adr.get("affected_modules"), lambda i: i in bundle.mod_by_id, "module", aid, where, f, STEP_REQ)
        _refs(adr.get("related_requirements"), lambda i: i in bundle.req_by_id, "requirement", aid, where, f, STEP_REQ)
        _refs(adr.get("related_features"), lambda i: i in bundle.feat_by_id, "feature", aid, where, f, STEP_REQ)
        _refs(adr.get("related_decisions"), lambda i: i in bundle.dec_by_id, "decision", aid, where, f, STEP_REQ)
        _refs(adr.get("principles"), lambda i: i in bundle.prin_by_id, "principle", aid, where, f, STEP_REQ)
        _refs(adr.get("supersedes"), lambda i: i in adrs, "ADR", aid, where, f, STEP_REQ)
        _refs(adr.get("conflicts_with"), lambda i: i in adrs, "ADR", aid, where, f, STEP_REQ)
        _refs(adr.get("decision_questions"), lambda i: i in bundle.q_by_id, "question", aid, where, f, STEP_REQ)
        _refs(adr.get("risk_ids"), lambda i: i in bundle.risk_by_id, "risk", aid, where, f, STEP_REQ, warn=True)
        _refs(adr.get("depends_on"), lambda i: i in adrs or i in bundle.dep_by_id, "ADR or external dependency", aid, where, f, STEP_REQ)
        for evidence in adr.get("approval_evidence") or []:
            known = bundle.dec_by_id if pr.kind_of(evidence) == "DEC" else bundle.src_by_id
            if evidence not in known:
                f.error(STEP_REQ, "UNKNOWN_REFERENCE", f"{aid} cites approval evidence {evidence}, which does not exist.", where)
        if adr.get("superseded_by") and adr["superseded_by"] not in adrs:
            f.error(STEP_REQ, "UNKNOWN_REFERENCE", f"{aid} is superseded by unknown {adr['superseded_by']}.", where)
        stem = where.rsplit("/", 1)[-1][:-3] if where.endswith(".md") else None
        if stem is not None and stem != aid and not stem.startswith(f"{aid}-"):
            f.warn(STEP_REQ, "ADR_FILE_NAME", f"{aid} is stored in {where}; name the file {aid}.md or {aid}-<short-title>.md.", where)

        if status == "proposed":
            questions = adr.get("decision_questions") or []
            if not questions:
                f.error(STEP_REQ, "ADR_DECISION_QUESTION_MISSING",
                        f"{aid} is proposed but names no open question (Q-###) whose answer decides it; an undecided "
                        f"architecture choice must be visible with an owner and a priority.", where)
            for q_id in questions:
                if bundle.q_by_id.get(q_id, {}).get("resolved"):
                    f.warn(STEP_REQ, "ADR_DECISION_PENDING",
                           f"{aid} is still proposed although its question {q_id} is answered; record the human decision "
                           f"and mark the ADR ACCEPTED or REJECTED.", where)
        else:
            # Human approval is the authority for every outcome other than 'proposed'.
            owner = adr.get("decision_owner") or ""
            if not owner.strip() or pr.has_tbd(owner):
                f.error(STEP_REQ, "ADR_APPROVAL_MISSING",
                        f"{aid} is {status} but names no decision owner / approver; only a named human authority can "
                        f"accept, reject, supersede or deprecate a decision.", where)
            if not adr.get("approval_evidence"):
                f.error(STEP_REQ, "ADR_APPROVAL_MISSING",
                        f"{aid} is {status} but cites no approval evidence (a DEC-### decision-log entry or SRC-### source).", where)
            if status != "accepted" and not adr.get("date"):
                f.error(STEP_REQ, "ADR_INCOMPLETE", f"{aid} is {status} but records no decision date.", where)
        if status == "accepted":
            missing = [name for name in ("context", "decision", "rationale") if not (adr.get(name) or "").strip()]
            if not any((adr.get("consequences") or {}).get(kind) for kind in ("positive", "negative", "other")):
                missing.append("consequences")
            if missing:
                f.error(STEP_REQ, "ADR_INCOMPLETE", f"{aid} is accepted but has no {', '.join(missing)}.", where)
            if not adr.get("alternatives"):
                f.warn(STEP_REQ, "ADR_NO_ALTERNATIVES", f"{aid} is accepted but records no alternatives considered.", where)
            if not adr.get("constraints"):
                f.warn(STEP_REQ, "ADR_NO_CONSTRAINTS",
                       f"{aid} is accepted but states no constraint it introduces; say what downstream planning must and must not do.", where)
        for constraint in adr.get("constraints") or []:
            lowered = f" {constraint.lower()} "
            vague = [t for t in VAGUE_CONSTRAINT_TERMS if re.search(rf"(?<![\w-]){re.escape(t)}(?![\w-])", lowered)]
            if vague:
                f.warn(STEP_REQ, "VAGUE_CONSTRAINT",
                       f"{aid} constraint '{constraint}' uses unreviewable wording ({', '.join(vague)}); state what can be checked.", where)
        for text in [adr.get("decision") or "", *(adr.get("constraints") or [])]:
            match = IMPLEMENTATION_DETAIL_RE.search(text)
            if match:
                f.warn(STEP_REQ, "ADR_IMPLEMENTATION_DETAIL",
                       f"{aid} names '{match.group(0)}', an implementation detail; an ADR constrains architecture and leaves "
                       f"code structure to implementation planning.", where)
                break

    # Supersession: both sides agree, and only an accepted decision replaces another.
    for adr in bundle.adrs:
        aid, status = adr.get("id"), adr.get("status")
        for old_id in adr.get("supersedes") or []:
            old = adrs.get(old_id)
            if old is None:
                continue
            if status in ("accepted", "superseded", "deprecated"):
                if old.get("status") == "accepted":
                    f.error(STEP_REQ, "ADR_ACTIVE_CONFLICT",
                            f"{aid} supersedes {old_id}, but {old_id} is still ACCEPTED: two active decisions govern the same "
                            f"choice. Mark {old_id} SUPERSEDED with 'Superseded by: {aid}'.", where_of(old))
                elif old.get("superseded_by") != aid:
                    f.error(STEP_REQ, "ADR_SUPERSESSION_MISMATCH",
                            f"{aid} supersedes {old_id}, but {old_id} names {old.get('superseded_by') or 'no successor'} under 'Superseded by'.",
                            where_of(old))
        successor_id = adr.get("superseded_by")
        successor = adrs.get(successor_id) if successor_id else None
        if successor_id and status != "superseded":
            f.error(STEP_REQ, "ADR_SUPERSESSION_MISMATCH",
                    f"{aid} names {successor_id} under 'Superseded by' but its status is {status}, not SUPERSEDED.", where_of(adr))
        if successor is not None:
            if successor.get("status") not in ("accepted", "superseded", "deprecated"):
                f.error(STEP_REQ, "ADR_SUPERSESSION_MISMATCH",
                        f"{aid} is superseded by {successor_id}, which is {successor.get('status')}; a decision is replaced only "
                        f"when its successor is ACCEPTED. Keep {aid} ACCEPTED until then.", where_of(adr))
            if aid not in (successor.get("supersedes") or []):
                f.error(STEP_REQ, "ADR_SUPERSESSION_MISMATCH",
                        f"{aid} is superseded by {successor_id}, but {successor_id} does not list {aid} under 'Supersedes'.",
                        where_of(successor))

    supersede_edges = {a["id"]: [s for s in a.get("supersedes", []) or [] if s in adrs] for a in bundle.adrs if "id" in a}
    for cycle in find_cycles(list(supersede_edges), supersede_edges):
        f.error(STEP_REQ, "ADR_SUPERSEDE_CYCLE", f"ADRs supersede each other in a cycle: {' -> '.join(cycle)}.",
                where_of(adrs.get(cycle[0], {})))
    depend_edges = {a["id"]: [d for d in a.get("depends_on", []) or [] if d in adrs] for a in bundle.adrs if "id" in a}
    for cycle in find_cycles(list(depend_edges), depend_edges):
        f.error(STEP_REQ, "ADR_DEPENDENCY_CYCLE", f"ADRs depend on each other in a cycle: {' -> '.join(cycle)}.",
                where_of(adrs.get(cycle[0], {})))

    # Active decisions do not contradict each other, and do not rest on inactive ones.
    reported: set[tuple[str, str]] = set()
    for adr in bundle.adrs:
        if adr.get("status") != "accepted":
            continue
        aid = adr.get("id")
        for other_id in adr.get("conflicts_with") or []:
            other = adrs.get(other_id)
            pair = tuple(sorted((aid, other_id), key=pr.natural_key))
            if other is not None and other.get("status") == "accepted" and pair not in reported:
                reported.add(pair)
                f.error(STEP_REQ, "ADR_ACTIVE_CONFLICT",
                        f"{pair[0]} and {pair[1]} are both ACCEPTED but are recorded as conflicting. Supersede one of them, "
                        f"or reject the one that should not govern.", where_of(adr))
        for dep_id in adr.get("depends_on") or []:
            dep = adrs.get(dep_id)
            if dep is None:
                continue
            if dep.get("status") in INACTIVE_ADR:
                f.error(STEP_REQ, "ADR_INACTIVE_DEPENDENCY",
                        f"Accepted {aid} depends on {dep_id}, which is {dep.get('status')}; revisit {aid} with a new ADR.", where_of(adr))
            elif dep.get("status") == "proposed":
                f.warn(STEP_REQ, "ADR_DEPENDS_ON_PROPOSED",
                       f"Accepted {aid} depends on {dep_id}, which is still proposed.", where_of(adr))

    # No record treats a rejected, superseded or deprecated decision as active.
    def inactive_reference(item_id: str, adr_id: str, where: str, step: str) -> None:
        adr = adrs.get(adr_id)
        if adr is None:
            f.error(step, "UNKNOWN_REFERENCE", f"{item_id} names ADR {adr_id}, which does not exist.", where)
            return
        if adr.get("status") not in INACTIVE_ADR:
            return
        successor = active_successor(adr_id, bundle)
        hint = (f" Follow {successor}, which replaced it." if successor else
                " Change the item, or record a new ADR if the decision must change.")
        f.error(step, "ADR_INACTIVE_REFERENCE",
                f"{item_id} relies on {adr_id}, which is {str(adr.get('status')).upper()} and governs nothing.{hint}", where)

    for req in bundle.requirements:
        if req.get("status") in LIVE_STATUSES:
            for adr_id in _declared(req.get("architecture_decisions"), "requirement"):
                inactive_reference(req.get("id"), adr_id, req.get("source_path", "requirements.json"), STEP_REQ)
    for feature in bundle.features:
        if feature.get("status") != "CANCELLED" and feature.get("scope") not in ("out_of_scope", "future"):
            for adr_id in _declared(feature.get("architecture_decisions"), "feature"):
                inactive_reference(feature.get("id"), adr_id, feature.get("source_path", "backlog.json"), STEP_BACKLOG)
    for task in bundle.tasks:
        if task.get("status") != "CANCELLED":
            for adr_id in _declared(task.get("architecture_decisions"), "task"):
                inactive_reference(task.get("id"), adr_id, task.get("source_path") or f"tasks/{task.get('id')}.json", STEP_BACKLOG)

    # Drift: downstream work that names an option an accepted ADR considered and rejected.
    for item_id, hits in sorted(_rejected_option_hits(bundle).items(), key=lambda kv: pr.natural_key(kv[0] or "")):
        item = bundle.req_by_id.get(item_id) or bundle.feat_by_id.get(item_id) or bundle.task_by_id.get(item_id) or {}
        step = STEP_REQ if item_id in bundle.req_by_id else STEP_BACKLOG
        where = item.get("source_path") or f"tasks/{item_id}.json"
        for adr, option in hits:
            f.warn(step, "ARCHITECTURE_CONFLICT",
                   f"ARCHITECTURE CONFLICT: {item_id} mentions '{option}', which accepted {adr['id']} "
                   f"({adr.get('title')}) considered and rejected. Change {item_id}, or record a new ADR that "
                   f"supersedes {adr['id']}; do not proceed silently.", where)
    for review in bundle.architecture.get("conflict_reviews") or []:
        for ref in (review.get("affected_ids") or []) + (review.get("adr_ids") or []):
            if bundle.known(ref) is False:
                f.warn(STEP_BACKLOG, "UNKNOWN_REFERENCE",
                       f"Architecture conflict {review.get('finding_id')} names {ref}, which does not exist.", pr.ARCHITECTURE_REVIEW_FILE)

    # Derived links and counts.
    for req in bundle.requirements:
        if (req.get("architecture_decisions") or []) != requirement_adrs(req, bundle):
            f.error(STEP_TRACE, "ADR_LINK_MISMATCH", f"{req.get('id')} architecture_decisions do not match the ADRs that affect it.",
                    req.get("source_path", "requirements.json"))
    for feature in bundle.features:
        if (feature.get("architecture_decisions") or []) != feature_adrs(feature, bundle):
            f.error(STEP_TRACE, "ADR_LINK_MISMATCH", f"{feature.get('id')} architecture_decisions do not match the ADRs that apply to it.",
                    feature.get("source_path", "backlog.json"))
    if bundle.architecture.get("summary") != architecture_summary(bundle.adrs, bundle.coverage):
        f.error(STEP_SCHEMA, "COUNT_MISMATCH", "architecture.json summary does not match the decisions and coverage.", "architecture.json")
    for row in bundle.coverage:
        where = pr.ARCHITECTURE_REGISTER_FILE
        _refs(row.get("adr_ids"), lambda i: i in adrs, "ADR", f"Concern '{row.get('concern')}'", where, f, STEP_REQ)
        _refs(row.get("question_ids"), lambda i: i in bundle.q_by_id, "question", f"Concern '{row.get('concern')}'", where, f, STEP_REQ)
    for principle in bundle.principles:
        for evidence in principle.get("evidence") or []:
            known = bundle.dec_by_id if pr.kind_of(evidence) == "DEC" else bundle.src_by_id
            if evidence not in known:
                f.error(STEP_REQ, "UNKNOWN_REFERENCE", f"{principle.get('id')} cites {evidence}, which does not exist.", pr.PRINCIPLES_FILE)


def change_findings(bundle: Bundle, f: Findings) -> None:
    """Change records: references, and the review states and counts derived from them."""
    removed = {u.get("id") for u in bundle.unrecorded if u.get("change") == "removed"}
    removed |= {d.get("id") for d in bundle.changes_doc.get("detected_changes", []) or [] if d.get("change") == "removed"}
    for change in bundle.changes:
        cid, where = change.get("change_id"), change.get("source_path", "changes.json")
        for identifier in change.get("changed_artifacts") or []:
            if bundle.known(identifier) is False and identifier not in removed:
                f.error(STEP_TRACE, "UNKNOWN_REFERENCE", f"{cid} changes {identifier}, which no record defines.", where)
        for evidence in change.get("approval_evidence") or []:
            known = bundle.dec_by_id if pr.kind_of(evidence) == "DEC" else bundle.src_by_id
            if evidence not in known:
                f.error(STEP_TRACE, "UNKNOWN_REFERENCE", f"{cid} cites approval evidence {evidence}, which does not exist.", where)
        _refs(change.get("decisions_required"), lambda i: i in bundle.q_by_id, "question", cid, where, f, STEP_TRACE)
        if change.get("superseded_by") and change["superseded_by"] not in bundle.change_by_id:
            f.error(STEP_TRACE, "UNKNOWN_REFERENCE", f"{cid} is superseded by unknown {change['superseded_by']}.", where)
    states = ci.artifact_states(bundle.changes, bundle.unrecorded)
    if list(states.values()) != (bundle.changes_doc.get("artifact_states") or []):
        f.error(STEP_TRACE, "CHANGE_STATE_MISMATCH", "artifact_states do not match the dispositions in the change records.", "changes.json")
    if bundle.changes_doc and bundle.changes_doc.get("summary") != ci.summary(bundle.changes, bundle.unrecorded, states, bundle.tasks):
        f.error(STEP_SCHEMA, "COUNT_MISMATCH", "changes.json summary does not match the changes and the review states.", "changes.json")


def review_findings(bundle: Bundle, f: Findings) -> None:
    """The specification review's result, counts and summary are the ones its findings support."""
    review = bundle.spec_review
    if not review:
        return
    where = "specification-review.json"
    _unique(bundle.review_findings, "Review finding", where, f, STEP_SPEC)
    findings = bundle.review_findings
    pairs = [(x.get("severity"), x.get("status")) for x in findings]
    if review.get("review_cycle", 0) == 0 and review.get("source_path") is None:
        expected = "NOT_REVIEWED"
    elif review.get("issues"):
        expected = "FAIL"
    else:
        expected = sr.JSON_RESULT[sr.result_for(pairs)]
    if review.get("overall_result") != expected:
        f.error(STEP_SPEC, "SPEC_REVIEW_RESULT_MISMATCH",
                f"overall_result is {review.get('overall_result')!r}; the findings and issues support {expected!r}.", where)
    unresolved = [x for x in findings if sr.is_unresolved(x.get("severity"), x.get("status"))]
    counts = {key: sum(1 for x in unresolved if x.get("severity") == key.upper())
              for key in ("critical", "major", "minor", "observation")}
    counts.update({
        "open": len(unresolved),
        "accepted_risk": sum(1 for x in findings if x.get("status") == "ACCEPTED_RISK" and x.get("severity") != "CRITICAL"),
        "resolved": sum(1 for x in findings if x.get("status") == "RESOLVED"),
        "rejected": sum(1 for x in findings if x.get("status") == "REJECTED"),
        "total": len(findings),
        "resolved_since_previous": sum(1 for x in findings if x.get("status") == "RESOLVED"
                                       and x.get("closed_in_cycle") == review.get("review_cycle")),
    })
    summary = review.get("summary") or {}
    for key, value in counts.items():
        if summary.get(key) != value:
            f.error(STEP_SPEC, "SPEC_REVIEW_COUNT_MISMATCH", f"summary.{key} is {summary.get(key)}; the findings give {value}.", where)
    for finding in findings:
        if finding.get("severity") == "CRITICAL" and finding.get("status") == "ACCEPTED_RISK":
            f.error(STEP_SPEC, "SPEC_REVIEW_CRITICAL_ACCEPTED",
                    f"{finding.get('id')} is a CRITICAL finding recorded as ACCEPTED_RISK; a CRITICAL finding cannot be accepted.",
                    where)
        if finding.get("status") in sr.CLOSED and not finding.get("resolution"):
            f.error(STEP_SPEC, "SPEC_REVIEW_UNRESOLVED_CLOSURE", f"{finding.get('id')} is {finding.get('status')} without a resolution.",
                    where)
        for ref in finding.get("affected_artifacts") or []:
            if bundle.known(ref) is False:
                f.warn(STEP_SPEC, "UNKNOWN_REFERENCE",
                       f"Review finding {finding.get('id')} names {ref}, which does not exist in the handoff.", where)
    cycles = review.get("cycles") or []
    numbers = [c.get("review_cycle") for c in cycles]
    if numbers != list(range(1, len(cycles) + 1)) or (cycles and numbers[-1] != review.get("review_cycle")):
        f.error(STEP_SPEC, "SPEC_REVIEW_HISTORY", "cycles must list every review cycle from 1 to review_cycle, in order.", where)
    if review.get("review_cycle") and review.get("review_version") != bundle.project.get("version"):
        f.warn(STEP_SPEC, "SPEC_REVIEW_STALE",
               f"The specification review covers version {review.get('review_version')!r}; the handoff is version "
               f"{bundle.project.get('version')!r}.", where)
    stated = bundle.project.get("specification_review")
    actual = {"result": review.get("overall_result"), "review_cycle": review.get("review_cycle"),
              "review_version": review.get("review_version")}
    if stated is not None and stated != actual:
        f.error(STEP_SPEC, "SPEC_REVIEW_MISMATCH",
                f"project.json specification_review is {stated}; specification-review.json says {actual}.", "project.json")


def semantic_findings(bundle: Bundle, raw: dict[str, bytes], sources: Path | None) -> Findings:
    f = Findings()
    project = bundle.project

    # Project identity -----------------------------------------------------
    project_id = project.get("project_id")
    for name, doc in sorted(bundle.docs.items()):
        if isinstance(doc, dict) and "project_id" in doc and doc.get("project_id") != project_id:
            f.error(STEP_SPEC, "PROJECT_ID_MISMATCH", f"project_id is {doc.get('project_id')!r}; project.json says {project_id!r}.", name)
        if isinstance(doc, dict) and doc.get("schema_version") not in (None, SCHEMA_VERSION):
            f.error(STEP_SCHEMA, "UNSUPPORTED_SCHEMA_VERSION", f"schema_version {doc.get('schema_version')!r} is not {SCHEMA_VERSION}.", name)

    # Uniqueness ------------------------------------------------------------
    for items, label, where, step in (
        (bundle.requirements, "Requirement", "requirements.json", STEP_REQ),
        (bundle.sources, "Source", "requirements.json", STEP_REQ),
        (bundle.modules, "Module", "architecture.json", STEP_REQ),
        (bundle.adrs, "ADR", "architecture.json", STEP_REQ),
        (bundle.principles, "Principle", "architecture.json", STEP_REQ),
        (bundle.decisions, "Decision", "decisions.json", STEP_REQ),
        (bundle.questions, "Question", "decisions.json", STEP_REQ),
        (bundle.assumptions, "Assumption", "decisions.json", STEP_REQ),
        (bundle.epics, "Epic", "backlog.json", STEP_BACKLOG),
        (bundle.features, "Feature", "backlog.json", STEP_BACKLOG),
        (bundle.phases, "Phase", "backlog.json", STEP_BACKLOG),
        (bundle.backlog_tasks, "Task", "backlog.json", STEP_BACKLOG),
        (bundle.tests, "Test", "tests.json", STEP_TRACE),
        (bundle.risks, "Risk", "decisions.json", STEP_REQ),
        (bundle.dependencies, "External dependency", "backlog.json", STEP_BACKLOG),
        (bundle.scope_items, "Scope item", "requirements.json", STEP_REQ),
        (bundle.processes, "Process", "domain.json", STEP_REQ),
        (bundle.entities, "Entity", "domain.json", STEP_REQ),
        (bundle.tasks, "Task", "tasks/", STEP_BACKLOG),
    ):
        _unique(items, label, where, f, step)
    for name, doc in sorted(bundle.task_docs.items()):
        if name != f"tasks/{doc.get('id')}.json":
            f.error(STEP_BACKLOG, "TASK_FILE_NAME", f"File name does not match task id {doc.get('id')!r}.", name)

    # Integration contract ------------------------------------------------------
    # The consumer views pin the fields SoftwareFactory reads, so a planner change
    # that would break the consumer fails here, in the planner, first.
    validators = load_validators()
    for task in bundle.tasks:
        if task.get("content_hash") != hc.task_content_hash(task, bundle.req_by_id, bundle.adr_by_id):
            f.error(STEP_SCHEMA, "TASK_CONTENT_HASH_MISMATCH",
                    f"{task.get('id')}: content_hash does not match the task's content; regenerate the handoff.",
                    f"tasks/{task.get('id')}.json")
    for items, schema, where in ((bundle.tasks, hc.TASK_VIEW_SCHEMA, None),
                                 (bundle.requirements, hc.REQUIREMENT_VIEW_SCHEMA, "requirements.json"),
                                 (bundle.adrs, hc.ADR_VIEW_SCHEMA, "architecture.json")):
        validator = validators[CONTRACT_PREFIX + schema]
        for item in items:
            for err in sorted(validator.iter_errors(item), key=lambda e: list(map(str, e.absolute_path))):
                path = "/".join(str(p) for p in err.absolute_path) or "(root)"
                f.error(STEP_SCHEMA, "CONTRACT_VIOLATION", f"{item.get('id')} {path}: {err.message[:300]} (integration/{schema})",
                        where or f"tasks/{item.get('id')}.json")

    # Artifacts and counts ------------------------------------------------------
    listed = {a.get("path"): a for a in project.get("artifacts", []) or [] if isinstance(a, dict)}
    present = {name for name in raw if name not in UNLISTED_FILES}
    for name in sorted(present - set(listed)):
        f.error(STEP_SCHEMA, "ARTIFACT_UNLISTED", "File is not listed in project.json artifacts (stale or hand-added).", name)
    for name in sorted(set(listed) - present):
        f.error(STEP_SCHEMA, "ARTIFACT_MISSING", "File listed in project.json artifacts is missing.", name)
    for name in sorted(present & set(listed)):
        # Hash LF-normalized bytes: a git checkout with CRLF conversion must not
        # look like a hand edit. Any change to the JSON itself still does.
        digest = hashlib.sha256(raw[name].replace(b"\r\n", b"\n")).hexdigest()
        if listed[name].get("sha256") != digest:
            f.error(STEP_SCHEMA, "ARTIFACT_HASH_MISMATCH", "Content differs from the hash in project.json; the file was edited after generation.", name)
        expected_schema = DOCUMENT_SCHEMAS.get(name, TASK_SCHEMA if name.startswith("tasks/") else None)
        if listed[name].get("schema") != expected_schema:
            f.error(STEP_SCHEMA, "ARTIFACT_SCHEMA_MISMATCH", f"Listed schema {listed[name].get('schema')!r}, expected {expected_schema!r}.", name)

    status_counts = {s: sum(1 for t in bundle.tasks if t.get("status") == s) for s in TASK_STATUSES}
    for key, actual in (
        ("requirements_count", len(bundle.requirements)),
        ("tasks_count", len(bundle.tasks)),
        ("ready_tasks_count", status_counts["READY"]),
        ("blocked_tasks_count", status_counts["BLOCKED"]),
    ):
        if project.get(key) != actual:
            f.error(STEP_SCHEMA, "COUNT_MISMATCH", f"{key} is {project.get(key)}; the bundle contains {actual}.", "project.json")
    if project.get("task_status_counts") and project.get("task_status_counts") != status_counts:
        f.error(STEP_SCHEMA, "COUNT_MISMATCH", "task_status_counts does not match the task files.", "project.json")

    # Specification ------------------------------------------------------------
    approval = project.get("specification_approval")
    if bundle.spec_approved and isinstance(approval, dict) and approval.get("specification_version") != project.get("version"):
        f.error(STEP_SPEC, "APPROVAL_VERSION_MISMATCH",
                f"Approval covers version {approval.get('specification_version')!r}; the handoff is version {project.get('version')!r}.",
                "project.json")
    for req in bundle.requirements:
        if req.get("status") == "approved" and not bundle.spec_approved:
            f.error(STEP_SPEC, "APPROVED_WITHOUT_SPECIFICATION",
                    f"{req.get('id')} is approved but the specification is {project.get('specification_status')}.",
                    req.get("source_path", "requirements.json"))
        if req.get("status") == "confirmed" and bundle.spec_approved and req.get("scope") == "in_scope":
            f.warn(STEP_SPEC, "CONFIRMED_NOT_APPROVED",
                   f"{req.get('id')} is confirmed but not approved although the specification is approved; approve, defer or exclude it.",
                   req.get("source_path", "requirements.json"))
    if bundle.tasks and not bundle.spec_approved:
        f.warn(STEP_SPEC, "TASKS_BEFORE_APPROVAL", "Tasks exist although the specification is not approved.", "backlog.json")

    # Requirements ------------------------------------------------------------
    for req in bundle.requirements:
        where = req.get("source_path", "requirements.json")
        rid = req.get("id")
        _refs(req.get("source"), lambda i: i in bundle.req_by_id, "requirement", rid, where, f, STEP_REQ)
        _refs(req.get("dependencies"), lambda i: i in bundle.req_by_id, "requirement", rid, where, f, STEP_REQ)
        _refs(req.get("related_modules"), lambda i: i in bundle.mod_by_id, "module", rid, where, f, STEP_REQ)
        _refs(req.get("open_questions"), lambda i: i in bundle.q_by_id, "question", rid, where, f, STEP_REQ)
        for evidence in req.get("evidence", []) or []:
            if pr.kind_of(evidence) == "DEC" and evidence not in bundle.dec_by_id:
                f.error(STEP_REQ, "UNKNOWN_REFERENCE", f"{rid} cites decision {evidence}, which does not exist.", where)
            if pr.kind_of(evidence) == "SRC" and evidence not in bundle.src_by_id:
                (f.error if bundle.sources else f.warn)(
                    STEP_REQ, "UNKNOWN_REFERENCE", f"{rid} cites source {evidence}, which is not in the source inventory.", where)
        if req.get("superseded_by") and req["superseded_by"] not in bundle.req_by_id:
            f.error(STEP_REQ, "UNKNOWN_REFERENCE", f"{rid} is superseded by {req['superseded_by']}, which does not exist.", where)
        if req.get("type") in IMPLEMENTABLE and in_release(req) and not req.get("acceptance_criteria"):
            f.error(STEP_REQ, "EMPTY_ACCEPTANCE_CRITERIA", f"{rid} is {req.get('status')} but has no acceptance criteria.", where)
        if req.get("type") in IMPLEMENTABLE and in_release(req) and not any(
                pr.kind_of(s) == "BR" for s in business_chain(rid, bundle)):
            f.warn(STEP_REQ, "NO_BUSINESS_SOURCE", f"{rid} does not trace to a business requirement (BR).", where)
        if req.get("type") == "business" and in_release(req) and not any(
                pr.kind_of(s) == "GOAL" for s in req.get("source") or []):
            f.warn(STEP_REQ, "NO_GOAL_SOURCE", f"{rid} does not trace to a business goal (GOAL).", where)
        expected_q = {q["id"] for q in bundle.questions if not q.get("resolved") and rid in (q.get("affected_ids") or [])}
        if expected_q - set(req.get("open_questions") or []):
            f.error(STEP_REQ, "OPEN_QUESTION_MISSING",
                    f"{rid} omits open question(s) {', '.join(sorted(expected_q - set(req.get('open_questions') or []), key=pr.natural_key))} that affect it.",
                    where)
        for q_id in req.get("open_questions") or []:
            if bundle.q_by_id.get(q_id, {}).get("resolved"):
                f.error(STEP_REQ, "RESOLVED_QUESTION_LISTED", f"{rid} lists {q_id} as open but it is resolved.", where)

    source_edges = {r["id"]: [s for s in r.get("source", []) or [] if s in bundle.req_by_id] for r in bundle.requirements if "id" in r}
    for cycle in find_cycles(list(source_edges), source_edges):
        f.error(STEP_REQ, "DERIVATION_CYCLE", f"Requirements derive from each other in a cycle: {' -> '.join(cycle)}.", "requirements.json")
    dependency_edges = {r["id"]: [d for d in r.get("dependencies", []) or [] if d in bundle.req_by_id] for r in bundle.requirements if "id" in r}
    for cycle in find_cycles(list(dependency_edges), dependency_edges):
        f.warn(STEP_REQ, "REQUIREMENT_DEPENDENCY_CYCLE", f"Requirements depend on each other in a cycle: {' -> '.join(cycle)}.", "requirements.json")

    # Architecture --------------------------------------------------------------
    for module in bundle.modules:
        if module.get("parent") and module["parent"] not in bundle.mod_by_id:
            f.error(STEP_REQ, "UNKNOWN_REFERENCE", f"Module {module.get('id')} has unknown parent {module['parent']}.", pr.SOLUTION_FILE)
    parent_edges = {m["id"]: [m["parent"]] if m.get("parent") in bundle.mod_by_id else [] for m in bundle.modules if "id" in m}
    for cycle in find_cycles(list(parent_edges), parent_edges):
        f.error(STEP_REQ, "MODULE_HIERARCHY_CYCLE", f"Module hierarchy is circular: {' -> '.join(cycle)}.", pr.SOLUTION_FILE)
    architecture_findings(bundle, f)
    change_findings(bundle, f)
    review_findings(bundle, f)

    # Discovery registers -----------------------------------------------------
    for record, label in [(q, "Question") for q in bundle.questions] + [(d, "Decision") for d in bundle.decisions] + [(a, "Assumption") for a in bundle.assumptions]:
        for ref in record.get("affected_ids", []) or []:
            if bundle.known(ref) is False:
                f.warn(STEP_REQ, "UNKNOWN_REFERENCE", f"{label} {record.get('id')} names {ref}, which does not exist in the handoff.", "decisions.json")
    for assumption in bundle.assumptions:
        _refs(assumption.get("question_ids"), lambda i: i in bundle.q_by_id, "question", assumption.get("id"), "decisions.json", f, STEP_REQ)
    for decision in bundle.decisions:
        _refs(decision.get("supersedes"), lambda i: i in bundle.dec_by_id, "decision", decision.get("id"), "decisions.json", f, STEP_REQ)
    for question in bundle.questions:
        resolved = question.get("status") in {"ANSWERED", "RESOLVED", "WITHDRAWN", "CLOSED"}
        if question.get("resolved") != resolved:
            f.error(STEP_REQ, "QUESTION_STATE_MISMATCH", f"{question.get('id')} has status {question.get('status')} but resolved={question.get('resolved')}.", "decisions.json")

    # Backlog hierarchy ----------------------------------------------------------
    for epic in bundle.epics:
        where = epic.get("source_path", "backlog.json")
        _refs(epic.get("requirement_ids"), lambda i: i in bundle.req_by_id, "requirement", epic.get("id"), where, f, STEP_BACKLOG)
        _refs(epic.get("feature_ids"), lambda i: i in bundle.feat_by_id, "feature", epic.get("id"), where, f, STEP_BACKLOG)
        expected = sorted((x["id"] for x in bundle.features if x.get("epic") == epic.get("id")), key=pr.natural_key)
        if (epic.get("feature_ids") or []) != expected:
            f.error(STEP_BACKLOG, "HIERARCHY_MISMATCH", f"{epic.get('id')} lists features {epic.get('feature_ids')}; features naming it are {expected}.", where)
    for feature in bundle.features:
        where = feature.get("source_path", "backlog.json")
        if feature.get("epic") and feature["epic"] not in bundle.epic_by_id:
            f.error(STEP_BACKLOG, "UNKNOWN_REFERENCE", f"{feature.get('id')} belongs to unknown epic {feature['epic']}.", where)
        if not feature.get("epic"):
            f.warn(STEP_BACKLOG, "FEATURE_WITHOUT_EPIC", f"{feature.get('id')} does not name an epic.", where)
        _refs(feature.get("requirement_ids"), lambda i: i in bundle.req_by_id, "requirement", feature.get("id"), where, f, STEP_BACKLOG)
        expected = sorted((t["id"] for t in bundle.tasks if t.get("feature") == feature.get("id")), key=pr.natural_key)
        if (feature.get("task_ids") or []) != expected:
            f.error(STEP_BACKLOG, "HIERARCHY_MISMATCH", f"{feature.get('id')} lists tasks {feature.get('task_ids')}; tasks naming it are {expected}.", where)
    for phase in bundle.phases:
        expected = sorted((t["id"] for t in bundle.tasks if t.get("phase") == phase.get("id")), key=pr.natural_key)
        if (phase.get("task_ids") or []) != expected:
            f.error(STEP_BACKLOG, "HIERARCHY_MISMATCH", f"{phase.get('id')} lists tasks {phase.get('task_ids')}; tasks naming it are {expected}.", phase.get("source_path", "backlog.json"))

    # Tasks -----------------------------------------------------------------
    order, depth, unsequenced = sequence_tasks(bundle.tasks, bundle.phase_order)
    dep_edges = {t["id"]: [d for d in t.get("dependencies", []) or [] if d in bundle.task_by_id] for t in bundle.tasks if "id" in t}
    for cycle in find_cycles(list(dep_edges), dep_edges):
        f.error(STEP_BACKLOG, "DEPENDENCY_CYCLE", f"Task dependencies form a cycle: {' -> '.join(cycle + [cycle[0]])}.", "backlog.json")
    parent_edges = {t["id"]: [t["parent_task"]] if t.get("parent_task") in bundle.task_by_id else [] for t in bundle.tasks if "id" in t}
    for cycle in find_cycles(list(parent_edges), parent_edges):
        f.error(STEP_BACKLOG, "PARENT_CYCLE", f"Parent tasks form a cycle: {' -> '.join(cycle)}.", "backlog.json")
    blocks = derived_blocks(bundle.tasks)

    for task in bundle.tasks:
        tid = task.get("id")
        where = task.get("source_path") or f"tasks/{tid}.json"
        _refs(task.get("source_requirements"), lambda i: i in bundle.req_by_id, "requirement", tid, where, f, STEP_BACKLOG)
        _refs(task.get("dependencies"), lambda i: i in bundle.task_by_id, "task", tid, where, f, STEP_BACKLOG)
        _refs(task.get("related_modules"), lambda i: i in bundle.mod_by_id, "module", tid, where, f, STEP_BACKLOG)
        _refs((task.get("verification") or {}).get("test_ids"), lambda i: i in bundle.test_by_id, "test", tid, where, f, STEP_TRACE)
        if tid in (task.get("dependencies") or []):
            f.error(STEP_BACKLOG, "SELF_DEPENDENCY", f"{tid} depends on itself.", where)
        if task.get("parent_task") and task["parent_task"] not in bundle.task_by_id:
            f.error(STEP_BACKLOG, "UNKNOWN_REFERENCE", f"{tid} names unknown parent task {task['parent_task']}.", where)
        feature = bundle.feat_by_id.get(task.get("feature")) if task.get("feature") else None
        if task.get("feature") and feature is None:
            f.error(STEP_BACKLOG, "UNKNOWN_REFERENCE", f"{tid} belongs to unknown feature {task['feature']}.", where)
        if task.get("epic") and task["epic"] not in bundle.epic_by_id:
            f.error(STEP_BACKLOG, "UNKNOWN_REFERENCE", f"{tid} belongs to unknown epic {task['epic']}.", where)
        if feature and feature.get("epic") != task.get("epic"):
            f.error(STEP_BACKLOG, "HIERARCHY_MISMATCH", f"{tid} names epic {task.get('epic')} but its feature {feature.get('id')} belongs to {feature.get('epic')}.", where)
        if task.get("phase") and task["phase"] not in bundle.phase_by_id:
            f.error(STEP_BACKLOG, "UNKNOWN_REFERENCE", f"{tid} is scheduled in unknown phase {task['phase']}.", where)
        if (task.get("blocks") or []) != blocks.get(tid, []):
            f.error(STEP_BACKLOG, "DERIVED_MISMATCH", f"{tid} blocks {task.get('blocks')}; the dependency graph says {blocks.get(tid, [])}.", where)
        if (task.get("architecture_decisions") or []) != applicable_adrs(task, bundle):
            f.error(STEP_TRACE, "ADR_LINK_MISMATCH", f"{tid} architecture_decisions do not match the ADRs that apply to it.", where)
        for entry in task.get("architecture_decisions") or []:
            if entry.get("id") not in bundle.adr_by_id:
                f.error(STEP_TRACE, "UNKNOWN_REFERENCE", f"{tid} references ADR {entry.get('id')}, which does not exist.", where)
        listed_q = {q.get("id") for q in task.get("open_questions") or []}
        expected_q = expected_open_questions(task, bundle)
        if expected_q - listed_q:
            f.error(STEP_BACKLOG, "OPEN_QUESTION_MISSING", f"{tid} omits open question(s) {', '.join(sorted(expected_q - listed_q, key=pr.natural_key))} that affect it.", where)
        for q in task.get("open_questions") or []:
            register = bundle.q_by_id.get(q.get("id"))
            if register is None:
                f.error(STEP_BACKLOG, "UNKNOWN_REFERENCE", f"{tid} references question {q.get('id')}, which does not exist.", where)
            elif register.get("resolved"):
                f.error(STEP_BACKLOG, "RESOLVED_QUESTION_LISTED", f"{tid} lists {q.get('id')} as open but it is resolved.", where)
            elif register.get("blocking") != q.get("blocking"):
                f.error(STEP_BACKLOG, "QUESTION_STATE_MISMATCH", f"{tid} records {q.get('id')} blocking={q.get('blocking')}; the register says {register.get('blocking')}.", where)
        for dep in task.get("dependencies") or []:
            predecessor = bundle.task_by_id.get(dep)
            if predecessor and predecessor.get("phase") and task.get("phase"):
                if bundle.phase_order.get(predecessor["phase"], 0) > bundle.phase_order.get(task["phase"], 0):
                    f.error(STEP_BACKLOG, "PHASE_ORDER", f"{tid} ({task['phase']}) depends on {dep}, scheduled in the later {predecessor['phase']}.", where)

        gaps = readiness_gaps(task, bundle, unsequenced)
        if (task.get("readiness_gaps") or []) != gaps:
            f.error(STEP_BACKLOG, "READINESS_MISMATCH", f"{tid} readiness_gaps do not match the Definition of Ready evaluation.", where)
        if task.get("readiness") != readiness_evaluation(task, bundle, unsequenced):
            f.error(STEP_BACKLOG, "READINESS_MISMATCH", f"{tid} readiness does not match the Definition of Ready evaluation.", where)
        history = task.get("readiness_history") or []
        if task.get("status") == "READY" and not any(h.get("to") == "READY" for h in history):
            f.error(STEP_BACKLOG, "READINESS_HISTORY",
                    f"{tid} is READY but its readiness history records no transition to READY; record who validated it and when.",
                    where)
        if history and history[-1].get("to") != task.get("status"):
            f.error(STEP_BACKLOG, "READINESS_HISTORY",
                    f"{tid} is {task.get('status')} but its readiness history ends at {history[-1].get('to')}; record the "
                    f"transition, its reason and the change behind it.", where)
        for entry in history:
            if entry.get("from") == "READY" and entry.get("to") != "READY" and not entry.get("reason"):
                f.error(STEP_BACKLOG, "READINESS_HISTORY",
                        f"{tid} lost READY on {entry.get('date') or 'an undated day'} without a recorded reason.", where)
        if task.get("status") == "READY":
            for gap in gaps:
                f.error(STEP_BACKLOG, "READY_NOT_MET", f"{tid} is READY but: {gap}", where)
        if task.get("status") != "CANCELLED" and (not task.get("source_requirements") or not task.get("feature")
                                                  or not task.get("acceptance_criteria")):
            missing = [name for name, ok in (("requirement", task.get("source_requirements")), ("feature", task.get("feature")),
                                              ("acceptance criteria", task.get("acceptance_criteria"))) if not ok]
            f.error(STEP_TRACE, "ORPHAN_TASK", f"{tid} has no {', no '.join(missing)}; every task needs a reason to exist.", where)
        for req_id in task.get("source_requirements") or []:
            req = bundle.req_by_id.get(req_id)
            if not req or task.get("status") == "CANCELLED":
                continue
            if req.get("status") in {"superseded", "rejected"}:
                f.warn(STEP_BACKLOG, "TASK_ON_EXCLUDED_REQUIREMENT", f"{tid} implements {req_id}, which is {req.get('status')}.", where)
            elif req.get("scope") in {"out_of_scope", "future"}:
                f.warn(STEP_BACKLOG, "TASK_ON_EXCLUDED_REQUIREMENT", f"{tid} implements {req_id}, which is {req.get('scope')}.", where)

    # backlog.json agrees with the task files ------------------------------------
    index = {t.get("id"): t for t in bundle.backlog_tasks}
    if set(index) != set(bundle.task_by_id):
        missing = sorted(set(bundle.task_by_id) - set(index), key=pr.natural_key)
        extra = sorted(set(index) - set(bundle.task_by_id), key=lambda i: pr.natural_key(i or ""))
        f.error(STEP_BACKLOG, "BACKLOG_MISMATCH", f"backlog.json task index differs from tasks/: missing {missing}, extra {extra}.", "backlog.json")
    sequence = {tid: position for position, tid in enumerate(order, start=1)}
    for tid, task in bundle.task_by_id.items():
        entry = index.get(tid)
        if not entry:
            continue
        for key in ("title", "status", "type", "priority", "complexity", "epic", "feature", "phase",
                    "source_requirements", "dependencies", "blocks"):
            if entry.get(key) != task.get(key):
                f.error(STEP_BACKLOG, "BACKLOG_MISMATCH", f"{tid}.{key} is {entry.get(key)!r} in backlog.json but {task.get(key)!r} in its task file.", "backlog.json")
        if entry.get("file") != f"tasks/{tid}.json":
            f.error(STEP_BACKLOG, "BACKLOG_MISMATCH", f"{tid}.file should be tasks/{tid}.json.", "backlog.json")
        if entry.get("sequence") != sequence.get(tid) or entry.get("depth") != depth.get(tid):
            f.error(STEP_BACKLOG, "BACKLOG_MISMATCH", f"{tid} sequence/depth do not match the dependency order.", "backlog.json")
    sequencing = bundle.backlog.get("sequencing") or {}
    if sequencing.get("order") != order:
        f.error(STEP_BACKLOG, "BACKLOG_MISMATCH", "sequencing.order does not match the deterministic dependency order.", "backlog.json")
    ready = [tid for tid in order if bundle.task_by_id[tid].get("status") == "READY"]
    if bundle.backlog.get("ready_task_ids") != ready:
        f.error(STEP_BACKLOG, "BACKLOG_MISMATCH", "ready_task_ids does not match the READY tasks in sequence order.", "backlog.json")
    sets = br.work_sets(bundle)
    if bundle.backlog.get("executable_now") != (sets[0] if sets else []):
        f.error(STEP_BACKLOG, "BACKLOG_MISMATCH", "executable_now does not match the first ready work set.", "backlog.json")
    if bundle.backlog_readiness:
        expected = br.document(bundle, bundle.backlog_readiness.get("schema_version"), bundle.backlog_readiness.get("project_id"))
        for key in expected:
            if bundle.backlog_readiness.get(key) != expected[key]:
                f.error(STEP_BACKLOG, "BACKLOG_READINESS_MISMATCH",
                        f"backlog-readiness.json {key} does not match the readiness recomputed from the tasks.", "backlog-readiness.json")
        if bundle.project.get("backlog_status") not in (None, expected["status"]):
            f.error(STEP_BACKLOG, "BACKLOG_READINESS_MISMATCH",
                    f"project.json backlog_status is {bundle.project.get('backlog_status')!r}; the tasks support {expected['status']!r}.",
                    "project.json")

    # Tests and traceability ------------------------------------------------------
    for test in bundle.tests:
        where = test.get("source_path", "tests.json")
        _refs(test.get("requirement_ids"), lambda i: i in bundle.req_by_id, "requirement", test.get("id"), where, f, STEP_TRACE)
        _refs(test.get("acceptance_criteria_ids"), lambda i: i in bundle.ac_ids, "acceptance criterion", test.get("id"), where, f, STEP_TRACE)
        if not test.get("requirement_ids"):
            f.warn(STEP_TRACE, "ORPHAN_TEST", f"{test.get('id')} does not verify any requirement.", where)

    trace = bundle.traceability
    planning_findings(bundle, f)
    for feature in bundle.features:
        if not feature.get("requirement_ids"):
            f.error(STEP_TRACE, "ORPHAN_FEATURE", f"{feature.get('id')} links to no requirement.", feature.get("source_path", "backlog.json"))

    records, task_records, summary, orphans = expected_traceability(bundle)
    if trace.get("orphans") is not None and trace.get("orphans") != orphans:
        f.error(STEP_TRACE, "TRACEABILITY_MISMATCH", "traceability.json orphans do not match the records.", "traceability.json")
    for rid in orphans["requirements"]:
        f.warn(STEP_TRACE, "ORPHAN_REQUIREMENT", f"{rid} is in scope but traces to nothing upstream.", "traceability.json")
    if trace.get("requirements") != records:
        f.error(STEP_TRACE, "TRACEABILITY_MISMATCH", "traceability.json requirement links do not match the records they are derived from.", "traceability.json")
    if trace.get("tasks") is not None and [dict(t, delivery=None) for t in trace.get("tasks") or []] != [dict(t, delivery=None) for t in task_records]:
        f.error(STEP_TRACE, "TRACEABILITY_MISMATCH", "traceability.json task links do not match the task files.", "traceability.json")
    if trace.get("architecture") is not None and trace.get("architecture") != expected_architecture_trace(bundle):
        f.error(STEP_TRACE, "TRACEABILITY_MISMATCH", "traceability.json architecture links do not match the ADRs and the records that name them.",
                "traceability.json")
    if trace.get("coverage_summary") != summary:
        f.error(STEP_TRACE, "TRACEABILITY_MISMATCH", "coverage_summary does not match the computed coverage.", "traceability.json")
    if bundle.tasks:
        for record in records:
            if record["coverage"] in ("missing_task", "missing_task_and_test"):
                f.warn(STEP_TRACE, "REQUIREMENT_WITHOUT_TASK", f"{record['requirement_id']} is in release but no task implements it.", "traceability.json")
    for record in records:
        if record["coverage"] in ("missing_test", "missing_task_and_test"):
            f.warn(STEP_TRACE, "REQUIREMENT_WITHOUT_TEST", f"{record['requirement_id']} is in release but no test verifies it.", "traceability.json")
        if record["coverage"] == "missing_downstream":
            f.warn(STEP_TRACE, "REQUIREMENT_NOT_REALISED", f"{record['requirement_id']} is in release but nothing realises it.", "traceability.json")

    # Staleness ------------------------------------------------------------------
    if sources is not None:
        current = pr.fingerprint(sources)
        if project.get("source_fingerprint") != current:
            f.error(STEP_SPEC, "STALE_HANDOFF", "The Markdown sources changed after this handoff was generated; regenerate it.", str(sources))

    # handoff_status is justified --------------------------------------------------
    # A claim better than the evidence is an error. A more conservative claim is
    # allowed: the generator also sees Markdown-level problems that the JSON
    # alone cannot show, and records them in validation-report.json.
    expected = expected_handoff_status(len(f.errors), bundle)
    claimed = project.get("handoff_status")
    rank = {"invalid": 0, "not_ready": 1, "ready": 2}
    if claimed not in rank or rank[claimed] > rank[expected]:
        f.error(STEP_SPEC, "HANDOFF_STATUS_MISMATCH",
                f"project.json claims handoff_status {claimed!r}; the validation result supports only {expected!r}.",
                "project.json")
    elif claimed != expected:
        f.warn(STEP_SPEC, "HANDOFF_STATUS_CONSERVATIVE",
               f"project.json claims {claimed!r} although the JSON alone supports {expected!r}; see validation-report.json for source-level findings.",
               "project.json")
    return f


# --------------------------------------------------------------------------
# Entry points
# --------------------------------------------------------------------------


def validate_files(raw: dict[str, bytes], sources: Path | None = None) -> tuple[Findings, Bundle]:
    """Validate a handoff given as {relative path: bytes}."""
    findings = Findings()
    validators = load_validators()
    docs: dict[str, object] = {}

    for name in DOCUMENT_SCHEMAS:
        if name not in raw:
            findings.error(STEP_SCHEMA, "MISSING_FILE", "Required handoff file is missing.", name)
    for name in sorted(raw):
        try:
            docs[name] = json.loads(raw[name].decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            findings.error(STEP_SCHEMA, "JSON_SYNTAX", f"Not valid JSON: {exc}", name)
            continue
        schema = DOCUMENT_SCHEMAS.get(name) or (TASK_SCHEMA if name.startswith("tasks/") else None)
        if schema is None:
            findings.error(STEP_SCHEMA, "UNEXPECTED_FILE", "File is not part of the handoff contract.", name)
            continue
        schema_findings(name, docs[name], validators[schema], findings)

    bundle = Bundle(docs)
    semantic = semantic_findings(bundle, raw, sources)
    findings.extend(semantic)
    return findings, bundle


def read_directory(directory: Path) -> dict[str, bytes]:
    """The planning files of a handoff: everything except the manifest and the validation report."""
    raw: dict[str, bytes] = {}
    for path in sorted(directory.glob("*.json")):
        if path.name not in (REPORT_FILE, MANIFEST_FILE):
            raw[path.name] = path.read_bytes()
    for path in sorted((directory / "tasks").glob("*.json")) if (directory / "tasks").is_dir() else []:
        raw[f"tasks/{path.name}"] = path.read_bytes()
    return raw


def non_ready_tasks(bundle: Bundle) -> list[dict]:
    out = []
    for task in sorted(bundle.tasks, key=lambda t: pr.natural_key(t.get("id", ""))):
        if task.get("status") in ("READY", "CANCELLED"):
            continue
        reasons = list(task.get("readiness_gaps") or []) or [f"Status is {task.get('status')}."]
        out.append({"id": task.get("id"), "status": task.get("status"), "reasons": reasons})
    return out


def summary_lines(findings: Findings, bundle: Bundle) -> list[str]:
    project = bundle.project
    statuses = [t.get("status") for t in bundle.tasks]
    ready = statuses.count("READY")
    blocked = statuses.count("BLOCKED")
    other = {s: statuses.count(s) for s in ("DRAFT", "NEEDS_DISCOVERY", "NEEDS_REVIEW", "CANCELLED") if statuses.count(s)}
    spec = str(project.get("specification_status") or "unknown").upper()
    version = project.get("version")
    review = bundle.spec_review or {}
    lines = [
        f"Specification: {spec}" + (f" (version {version})" if version else ""),
        f"Specification review: {str(review.get('overall_result') or 'NOT_REVIEWED').replace('_', ' ')}"
        + (f" (cycle {review.get('review_cycle')})" if review.get("review_cycle") else ""),
        f"Machine handoff: {'VALID' if not findings.errors else 'INVALID'}",
        f"Handoff status: {expected_handoff_status(len(findings.errors), bundle)}",
        f"Backlog readiness: {str((bundle.backlog_readiness or {}).get('status') or 'NOT_READY').replace('_', ' ')}",
        f"Ready tasks: {ready}",
        f"Blocked tasks: {blocked}",
    ]
    if other:
        lines.append("Other non-ready tasks: " + ", ".join(f"{k} {v}" for k, v in other.items()))
    lines += [
        f"Errors: {len(findings.errors)}",
        f"Warnings: {len(findings.warnings)}",
        f"Schema version: {SCHEMA_VERSION}",
        f"Integration contract: {hc.CONTRACT_VERSION}",
    ]
    return lines


def print_findings(findings: Findings, stream=None) -> None:
    stream = stream or sys.stdout
    for label, items in (("ERROR", findings.errors), ("WARNING", findings.warnings)):
        for item in items:
            where = f" [{item.location}]" if item.location else ""
            print(f"{label} {item.step} {item.code}{where}: {item.message}", file=stream)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate a machine-handoff directory.")
    parser.add_argument("directory", type=Path, help="Path to projects/<project>/machine-handoff")
    parser.add_argument(
        "--sources", type=Path, default=None,
        help="Project folder holding the Markdown sources, to detect a stale handoff. "
             "Defaults to the handoff's parent folder when it contains project-state.md.",
    )
    parser.add_argument("--no-sources", action="store_true", help="Skip the staleness check")
    parser.add_argument("--json", action="store_true", help="Print findings as JSON")
    args = parser.parse_args(argv)

    if not args.directory.is_dir():
        print(f"Not a directory: {args.directory}", file=sys.stderr)
        return 2
    sources = args.sources
    if sources is None and not args.no_sources and (args.directory.parent / pr.STATE_FILE).is_file():
        sources = args.directory.parent
    try:
        raw = read_directory(args.directory)
        findings, bundle = validate_files(raw, None if args.no_sources else sources)
        manifest_path = args.directory / MANIFEST_FILE
        findings.extend(manifest_findings(manifest_path.read_bytes() if manifest_path.is_file() else None, raw, bundle, findings))
    except SchemaUnavailable as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps({
            "result": "VALID" if not findings.errors else "INVALID",
            "errors": [f.as_json() for f in findings.errors],
            "warnings": [f.as_json() for f in findings.warnings],
            "non_ready_tasks": non_ready_tasks(bundle),
        }, indent=2, ensure_ascii=False))
    else:
        print_findings(findings)
        if findings.items:
            print()
        print("\n".join(summary_lines(findings, bundle)))
    return 1 if findings.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
