"""Change-impact analysis: the impact graph, baselines, and the rules for changes.

A change is never a text edit. This module answers, from the records:

- what changed since the trusted baseline (``snapshot``, ``diff_baseline``);
- what depends on it, directly or through other records, and how certain
  that is (``Graph``, ``classify``);
- how serious the change is (``severity``);
- which artifacts must be reviewed, and what is now stale or invalid
  (``artifact_states``);
- what new work, roadmap, risk and document consequences follow
  (``missing_work``, ``roadmap_impact``, ``risk_impact``, ``document_impact``).

It depends only on ``planning_records`` and on a duck-typed bundle (the
indexed machine-handoff view built by ``validate_handoff.Bundle``), so the
generator, the validator, the gate checker and the command line share one
implementation.
"""

from __future__ import annotations

import datetime as _dt
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

import planning_records as pr

# --------------------------------------------------------------------------
# Vocabulary
# --------------------------------------------------------------------------

CHANGE_TYPES = (
    "REQUIREMENT_CHANGE", "ARCHITECTURE_CHANGE", "SCOPE_CHANGE", "BUSINESS_RULE_CHANGE", "WORKFLOW_CHANGE",
    "FEATURE_CHANGE", "DATA_CHANGE", "INTEGRATION_CHANGE", "SECURITY_CHANGE", "PRIORITY_CHANGE",
    "DEPENDENCY_CHANGE", "ROADMAP_CHANGE",
)
CHANGE_STATUSES = ("PROPOSED", "UNDER_ANALYSIS", "APPROVED", "REJECTED", "IMPLEMENTED_IN_PLAN", "SUPERSEDED")
# An approved change marks the plan for review; a proposed one never alters the authoritative plan.
MARKING_STATUSES = {"APPROVED", "IMPLEMENTED_IN_PLAN"}
OPEN_STATUSES = {"PROPOSED", "UNDER_ANALYSIS", "APPROVED"}
DECIDED_STATUSES = {"APPROVED", "REJECTED", "IMPLEMENTED_IN_PLAN"}
RESOLUTION_STATUSES = ("OPEN", "IN_PROGRESS", "RESOLVED")

LEVELS = ("DIRECT", "INDIRECT", "POTENTIAL", "NEW")
CONFIDENCES = ("CONFIRMED", "LIKELY", "POSSIBLE")
SEVERITIES = ("CRITICAL", "HIGH", "MEDIUM", "LOW")
SEVERITY_RANK = {s: i for i, s in enumerate(reversed(SEVERITIES))}  # LOW 0 .. CRITICAL 3
REVIEW_STATES = ("CURRENT", "NEEDS_REVIEW", "STALE", "INVALID")
STATE_RANK = {s: i for i, s in enumerate(REVIEW_STATES)}
RESOLUTIONS = ("UPDATED", "NO_CHANGE_NEEDED", "ADDED", "REMOVED", "DEFERRED", "REPLACED")
# Resolutions that say the record itself was edited, so it must differ from the baseline.
EDITING_RESOLUTIONS = {"UPDATED", "ADDED", "REMOVED", "REPLACED"}
RISK_EFFECTS = ("NEW", "INCREASED", "REDUCED", "RETIRED", "UNCHANGED")
REVIEW_RESULTS = ("DONE", "N/A", "PENDING")

# Records under change control once a baseline covers their kind.
CONTROLLED_RECORD_KINDS = (*pr.REQUIREMENT_KINDS, "PROC", "ENT", "ADR", "EPIC", "FEAT", "PHASE", "TASK", "TEST")
CONTROLLED_REGISTERS = {"MOD": ("MOD ID", "Module ID"), "SCOPE": ("Scope ID",), "PRIN": ("PRIN ID", "Principle ID")}
CONTROLLED_KINDS = (*CONTROLLED_RECORD_KINDS, *CONTROLLED_REGISTERS)
# A backlog item's planning status moves as planning proceeds; its content is what is controlled.
VOLATILE_FIELDS = {"EPIC": ("status",), "FEAT": ("status",), "TASK": ("status",)}
# Sections that record planning state, not content: a readiness transition is not a change to the task.
VOLATILE_SECTIONS = {"TASK": ("readiness history",)}
# Detail records found by the ID in their heading: pages, API contracts, integrations.
DETAIL_KINDS = ("PAGE", "API", "INT")
# Records that pass impact on to what depends on them. Context records are reported but stop there.
PROPAGATING = {*pr.REQUIREMENT_KINDS, "MOD", "ADR", "DEP", "FEAT", "TASK"}
PLANNING_KINDS = {*pr.REQUIREMENT_KINDS, "ADR", "MOD", "FEAT", "TASK", "PHASE"}

# The earliest gate whose evidence a change to this kind of record can alter.
KIND_GATE = {
    "GOAL": 3, "BR": 3, "RULE": 3, "FR": 3, "NFR": 3, "DR": 3, "IR": 3, "SR": 3, "UXR": 3, "TR": 3,
    "Q": 2, "ASM": 2, "RISK": 2, "DEP": 2, "DEC": 2, "SRC": 2,
    "PROC": 4, "ENT": 4, "MOD": 5, "SCOPE": 5, "ADR": 6, "PRIN": 6,
    "EPIC": 9, "FEAT": 9, "TASK": 9, "TEST": 9, "AC": 9, "PHASE": 11,
    "PAGE": 7, "API": 7, "INT": 7,
}
LAST_GATE = 13
APPROVAL_GATE = 8

REQ = tuple(pr.REQUIREMENT_KINDS)
TRACE = ("Traceability records", ())
DOCS = ("Human deliverables", ())
# What each type of change must be checked against. Every area is listed in the impact report with the
# records the graph found for it, or as "none found — confirm", and is recorded in the change record.
REVIEW_AREAS: dict[str, list[tuple[str, tuple[str, ...]]]] = {
    "REQUIREMENT_CHANGE": [
        ("Dependent requirements", REQ), ("Architecture decisions", ("ADR",)), ("Workflows", ("PROC",)),
        ("Modules", ("MOD",)), ("Features", ("FEAT",)), ("Tasks", ("TASK",)), ("Acceptance criteria and tests", ("TEST",)),
        ("Data entities", ("ENT", "DR")), ("API contracts", ("API",)), ("UI screens", ("PAGE", "UXR")),
        ("Security requirements", ("SR",)), ("Integrations", ("IR", "INT")), ("Roadmap", ("PHASE",)), ("Risks", ("RISK",)),
        TRACE, DOCS],
    "ARCHITECTURE_CHANGE": [
        ("Requirements", REQ), ("Superseded and dependent ADRs", ("ADR",)), ("Modules", ("MOD",)), ("Features", ("FEAT",)),
        ("Tasks", ("TASK",)), ("Integrations", ("IR", "INT")), ("Infrastructure assumptions", ("TR", "NFR", "DEP")),
        ("Risks", ("RISK",)), ("Roadmap", ("PHASE",)), ("Architecture review", ()), TRACE, DOCS],
    "SCOPE_CHANGE": [
        ("Requirements", REQ), ("Features", ("FEAT",)), ("Tasks", ("TASK",)), ("Roadmap and milestones", ("PHASE",)),
        ("Estimates", ()), ("Risks", ("RISK",)), ("Dependencies", ("DEP",)), ("Scope register", ("SCOPE",)), TRACE, DOCS],
    "BUSINESS_RULE_CHANGE": [
        ("Requirements", REQ), ("Features", ("FEAT",)), ("Workflows", ("PROC",)), ("UI screens", ("PAGE", "UXR")),
        ("Notifications", ()), ("Data", ("ENT", "DR")), ("Reports", ()), ("Acceptance criteria and tests", ("TEST",)),
        ("Tasks", ("TASK",)), TRACE, DOCS],
    "WORKFLOW_CHANGE": [
        ("Requirements", REQ), ("Data entities and states", ("ENT",)), ("Features", ("FEAT",)), ("Tasks", ("TASK",)),
        ("UI screens", ("PAGE", "UXR")), ("Permissions", ("SR",)), ("Acceptance criteria and tests", ("TEST",)), TRACE, DOCS],
    "FEATURE_CHANGE": [
        ("Requirements", REQ), ("Architecture decisions", ("ADR",)), ("Tasks", ("TASK",)),
        ("Acceptance criteria and tests", ("TEST",)), ("Dependencies", ("FEAT", "DEP")), ("Roadmap", ("PHASE",)), TRACE, DOCS],
    "DATA_CHANGE": [
        ("Data entities", ("ENT",)), ("Data requirements", ("DR",)), ("Workflows", ("PROC",)), ("API contracts", ("API",)),
        ("Integrations", ("IR", "INT")), ("Migration", ()), ("Tasks", ("TASK",)), ("Tests", ("TEST",)), TRACE, DOCS],
    "INTEGRATION_CHANGE": [
        ("Integration requirements", ("IR",)), ("External dependencies", ("DEP",)), ("API contracts", ("API", "INT")),
        ("Architecture decisions", ("ADR",)), ("Features", ("FEAT",)), ("Tasks", ("TASK",)), ("Risks", ("RISK",)), TRACE, DOCS],
    "SECURITY_CHANGE": [
        ("Security requirements", ("SR",)), ("Permissions and workflows", ("PROC",)), ("Architecture decisions", ("ADR",)),
        ("Data entities", ("ENT",)), ("Features", ("FEAT",)), ("Tasks", ("TASK",)), ("Tests", ("TEST",)), ("Risks", ("RISK",)),
        TRACE, DOCS],
    "PRIORITY_CHANGE": [
        ("Requirements", REQ), ("Features", ("FEAT",)), ("Tasks", ("TASK",)), ("Sequencing", ()), ("Roadmap", ("PHASE",)),
        DOCS],
    "DEPENDENCY_CHANGE": [
        ("Tasks", ("TASK",)), ("Features", ("FEAT",)), ("External dependencies", ("DEP",)), ("Sequencing and cycles", ()),
        ("Roadmap order", ("PHASE",)), ("Milestone risk", ("RISK",)), DOCS],
    "ROADMAP_CHANGE": [
        ("Phases", ("PHASE",)), ("Tasks", ("TASK",)), ("Commitments", ("DEC",)), ("Risks", ("RISK",)), DOCS],
}

BASELINE_FILE = pr.BASELINE_FILE
HISTORY_DIR = "changes/history"
REPORT_SUFFIX = pr.CHANGE_REPORT_SUFFIX


def rank_key(identifier: str) -> tuple:
    return pr.natural_key(identifier or "")


# --------------------------------------------------------------------------
# Baseline: the trusted state of every change-controlled record
# --------------------------------------------------------------------------


def _normalise(lines: list[str]) -> str:
    out: list[str] = []
    for line in lines:
        text = line.rstrip()
        if not text and (not out or not out[-1]):
            continue
        out.append(text)
    while out and not out[-1]:
        out.pop()
    return "\n".join(out)


def _record_texts(path: Path) -> list[tuple[str, str]]:
    """Every controlled record block in a file, as (ID, text) — nested records excluded."""
    lines = pr._meaningful_lines(path.read_text(encoding="utf-8"))
    heads = []
    for position, (_, line) in enumerate(lines):
        match = pr.HEADING_RE.match(line)
        if match:
            record = pr.RECORD_HEADING_RE.match(pr.clean(match.group(2)))
            heads.append((position, len(match.group(1)), record.group("id") if record else None))
    out = []
    for index, (position, level, identifier) in enumerate(heads):
        if identifier is None or pr.kind_of(identifier) not in CONTROLLED_RECORD_KINDS:
            continue
        end = len(lines)
        for later, later_level, later_id in heads[index + 1:]:
            if later_level <= level or later_id is not None:
                end = later
                break
        volatile = VOLATILE_FIELDS.get(pr.kind_of(identifier), ())
        sections = VOLATILE_SECTIONS.get(pr.kind_of(identifier), ())
        body, skipping = [], False
        for _, line in lines[position:end]:
            heading = pr.HEADING_RE.match(line)
            label = pr.BOLD_LABEL_RE.match(line.strip())
            if heading or label:
                skipping = pr.norm_key(heading.group(2) if heading else label.group(1)) in sections
            if skipping or any(re.match(rf"^\s*\|\s*{name}\s*\|", line, re.IGNORECASE) for name in volatile):
                continue
            body.append(line)
        out.append((identifier, _normalise(body)))
    return out


def _record_sources(project: Path) -> list[Path]:
    """Planning records: every Markdown source except project state and the change records themselves,
    which may quote a record's previous text."""
    changes = set(pr.change_files(project))
    return [p for p in pr.source_files(project)
            if p.suffix == ".md" and p.name != pr.STATE_FILE and p not in changes]


def snapshot(project: Path) -> dict[str, dict]:
    """ID → {text, hash, source_path} for every change-controlled record in the project."""
    records: dict[str, dict] = {}

    def keep(identifier: str, text: str, path: Path) -> None:
        if identifier in records:
            return
        records[identifier] = {"text": text, "hash": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                               "source_path": pr.rel(project, path)}

    for path in _record_sources(project):
        for identifier, text in _record_texts(path):
            keep(identifier, text, path)
        for kind, headers in CONTROLLED_REGISTERS.items():
            for _, row in pr.read_register(path, headers, kind):
                cells = " | ".join(pr.clean(v) for k, v in row.items() if k != "__id__")
                keep(row["__id__"], cells, path)
    return dict(sorted(records.items(), key=lambda kv: rank_key(kv[0])))


def load_baseline(project: Path) -> dict | None:
    path = project / BASELINE_FILE
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def diff_baseline(baseline: dict | None, current: dict[str, dict]) -> dict[str, dict]:
    """Records added, modified or removed since the baseline, for the kinds the baseline controls."""
    if not baseline:
        return {}
    controlled = set(baseline.get("controlled_kinds") or [])
    before = baseline.get("records") or {}
    out: dict[str, dict] = {}
    for identifier in sorted(set(before) | set(current), key=rank_key):
        if pr.kind_of(identifier) not in controlled:
            continue
        old, new = before.get(identifier), current.get(identifier)
        if old and new and old["hash"] == new["hash"]:
            continue
        change = "added" if old is None else "removed" if new is None else "modified"
        out[identifier] = {"id": identifier, "change": change,
                           "previous": old["text"] if old else None, "current": new["text"] if new else None,
                           "source_path": (new or old)["source_path"]}
    return out


def write_baseline(project: Path, records: dict[str, dict], specification_version: str | None,
                   incorporated: list[str], reason: str, created_at: str | None = None) -> Path:
    """Archive the previous baseline and record the current records as the trusted state."""
    created_at = created_at or _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    path = project / BASELINE_FILE
    previous = load_baseline(project)
    if previous is not None:
        history = project / HISTORY_DIR
        history.mkdir(parents=True, exist_ok=True)
        stamp = str(previous.get("created_at", "unknown")).replace(":", "").replace("-", "")
        (history / f"baseline-{stamp}.json").write_text(path.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
    kinds = sorted({pr.kind_of(i) for i in records} & set(CONTROLLED_KINDS))
    document = {
        "format": 1,
        "created_at": created_at,
        "specification_version": specification_version,
        "reason": reason,
        "incorporated_changes": sorted(set(incorporated), key=rank_key),
        "controlled_kinds": kinds,
        "records": records,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return path


# --------------------------------------------------------------------------
# Source-side context: detail records and explicit mentions
# --------------------------------------------------------------------------


def detail_links(project: Path) -> dict[str, list[str]]:
    """Pages, API contracts and integration records, with the IDs each one references."""
    out: dict[str, list[str]] = {}
    for path in sorted(project.glob("specification/**/*.md")):
        for record in pr.read_records(path, DETAIL_KINDS):
            refs = [i for i in pr.extract_ids(record.raw) if i != record.id]
            out.setdefault(record.id, [])
            out[record.id] += [r for r in refs if r not in out[record.id]]
    return out


def record_mentions(project: Path) -> dict[str, set[str]]:
    """For every record, the IDs its own text mentions (used only for POTENTIAL impact)."""
    out: dict[str, set[str]] = {}
    for path in _record_sources(project):
        for identifier, text in _record_texts(path):
            out[identifier] = set(pr.extract_ids(text)) - {identifier}
    return out


def document_mentions(project: Path) -> dict[str, set[str]]:
    """Human documents (deliverables, specification, traceability review) and the IDs they mention."""
    out: dict[str, set[str]] = {}
    for pattern in ("deliverables/*.md", pr.SPECIFICATION_FILE, "traceability/traceability.md",
                    "specification/pages/*.md", "specification/requirements/*.md"):
        for path in sorted(project.glob(pattern)):
            out[pr.rel(project, path)] = set(pr.extract_ids(path.read_text(encoding="utf-8")))
    return out


@dataclass
class SourceContext:
    baseline: dict | None
    detected: dict[str, dict]
    details: dict[str, list[str]]
    mentions: dict[str, set[str]]
    documents: dict[str, set[str]]


def source_context(project: Path) -> SourceContext:
    baseline = load_baseline(project)
    return SourceContext(baseline, diff_baseline(baseline, snapshot(project)), detail_links(project),
                         record_mentions(project), document_mentions(project))


# --------------------------------------------------------------------------
# The impact graph
# --------------------------------------------------------------------------


class Graph:
    """Typed links between planning records.

    Each link is *strong* (an explicit dependency: derivation, implementation, binding, verification,
    scheduling) or *weak* (membership or context: a module, a workflow using an entity, a question
    about a record). Impact reached only through strong links is CONFIRMED; any weak link on the way
    makes it LIKELY.
    """

    def __init__(self, bundle, details: dict[str, list[str]] | None = None):
        self.b = bundle
        self.edges: dict[str, dict[str, tuple[str, bool]]] = {}
        # What an ADR governs. Followed only from a changed ADR, so that a changed requirement reaches
        # its ADR without fanning out to every other requirement the ADR happens to govern.
        self.governs: dict[str, dict[str, tuple[str, bool]]] = {}

        def add(table: dict, a: str, b: str, why: str, strong: bool) -> None:
            if not a or not b or a == b:
                return
            current = table.setdefault(a, {}).get(b)
            if current is None or (strong and not current[1]):
                table[a][b] = (why, strong)

        def link(a: str, b: str, why: str, strong: bool = True) -> None:
            add(self.edges, a, b, why, strong)

        def govern(adr: str, target: str, why: str) -> None:
            add(self.governs, adr, target, why, True)

        for r in bundle.requirements:
            for up in r.get("source") or []:
                link(up, r["id"], f"{r['id']} is derived from {up}")
            for dep in r.get("dependencies") or []:
                link(dep, r["id"], f"{r['id']} depends on {dep}")
            for mod in r.get("related_modules") or []:
                link(mod, r["id"], f"{r['id']} belongs to {mod}", strong=False)
        for p in bundle.processes:
            for ref in (p.get("related_requirements") or []) + (p.get("business_rules") or []):
                link(ref, p["id"], f"workflow {p['id']} applies {ref}")
            for ref in p.get("data_involved") or []:
                link(ref, p["id"], f"workflow {p['id']} uses {ref}", strong=False)
            if p.get("compares_to"):
                link(p["compares_to"], p["id"], f"{p['id']} replaces {p['compares_to']}", strong=False)
        for e in bundle.entities:
            for ref in (e.get("related_requirements") or []) + (e.get("business_rules") or []):
                link(ref, e["id"], f"entity {e['id']} is governed by {ref}")
        for f in bundle.features:
            for ref in (f.get("requirement_ids") or []) + (f.get("dependencies") or []) + (f.get("external_dependencies") or []):
                link(ref, f["id"], f"feature {f['id']} relies on {ref}")
            for ref in f.get("module_ids") or []:
                link(ref, f["id"], f"feature {f['id']} delivers into {ref}", strong=False)
            for entry in f.get("architecture_decisions") or []:
                link(entry["id"], f["id"], f"feature {f['id']} must respect {entry['id']}")
            if f.get("epic"):
                link(f["id"], f["epic"], f"{f['id']} is part of {f['epic']}", strong=False)
        for t in bundle.tasks:
            for ref in (t.get("source_requirements") or []) + (t.get("dependencies") or []) + (t.get("external_dependencies") or []):
                link(ref, t["id"], f"task {t['id']} relies on {ref}")
            for ref in t.get("related_modules") or []:
                link(ref, t["id"], f"task {t['id']} works in {ref}", strong=False)
            if t.get("feature"):
                # Membership: a task under an affected feature is likely affected, not certainly.
                link(t["feature"], t["id"], f"{t['id']} delivers {t['feature']}", strong=False)
            if t.get("phase"):
                link(t["id"], t["phase"], f"{t['id']} is scheduled in {t['phase']}")
            for entry in t.get("architecture_decisions") or []:
                link(entry["id"], t["id"], f"{t['id']} is bound by {entry['id']}")
            for test in (t.get("verification") or {}).get("test_ids") or []:
                link(t["id"], test, f"{test} verifies {t['id']}")
        for test in bundle.tests:
            for ref in (test.get("requirement_ids") or []) + (test.get("acceptance_criteria_ids") or []):
                link(ref, test["id"], f"{test['id']} verifies {ref}")
        for a in bundle.adrs:
            for ref in a.get("related_requirements") or []:
                link(ref, a["id"], f"{a['id']} constrains or follows from {ref}")
            for ref in (a.get("affected_modules") or []) + (a.get("related_decisions") or []) + (a.get("principles") or []):
                link(ref, a["id"], f"{a['id']} constrains or follows from {ref}", strong=False)
            for ref in a.get("depends_on") or []:
                link(ref, a["id"], f"{a['id']} depends on {ref}")
            for ref in a.get("related_requirements") or []:
                govern(a["id"], ref, f"{ref} is governed by {a['id']}")
            for ref in a.get("related_features") or []:
                govern(a["id"], ref, f"{a['id']} names feature {ref}")
            for ref in a.get("affected_modules") or []:
                govern(a["id"], ref, f"{ref} is affected by {a['id']}")
            for old in a.get("supersedes") or []:
                govern(a["id"], old, f"{a['id']} supersedes {old}")
                govern(old, a["id"], f"{old} is superseded by {a['id']}")
            for other in a.get("conflicts_with") or []:
                govern(a["id"], other, f"{a['id']} is recorded as conflicting with {other}")
        for r in bundle.requirements:
            for entry in r.get("architecture_decisions") or []:
                govern(entry["id"], r["id"], f"{r['id']} is governed by {entry['id']}")
        for item in bundle.questions + bundle.decisions + bundle.risks + bundle.assumptions + bundle.scope_items:
            for ref in item.get("affected_ids") or item.get("related_ids") or []:
                link(ref, item["id"], f"{item['id']} concerns {ref}", strong=False)
        for detail, refs in (details or {}).items():
            for ref in refs:
                if pr.kind_of(ref) in (*pr.REQUIREMENT_KINDS, "ENT", "PROC", "FEAT", "MOD"):
                    link(ref, detail, f"{detail} specifies {ref}", strong=False)

    def impact(self, start: list[str]) -> dict[str, tuple[int, str, bool]]:
        """Breadth-first: each reached ID with its distance, the first reason and whether the path is all strong.

        Impact flows through records that carry obligations to other records — requirements,
        modules, ADRs, external dependencies, features and tasks. Context records (workflows,
        entities, questions, decisions, risks, scope items, phases, tests, epics, pages) are
        reported but do not pass the impact on: a changed rule touches the workflow that applies
        it, not every other requirement that shares that workflow. A changed context record also
        affects the records that point at it, which is how upstream assumptions are found.
        """
        reverse: dict[str, dict[str, tuple[str, bool]]] = {}
        for source, targets in self.edges.items():
            for target, (why, strong) in targets.items():
                reverse.setdefault(target, {})[source] = (why, strong)
        out: dict[str, tuple[int, str, bool]] = {}
        frontier = {s: ("changed", True) for s in start}
        depth = 0
        while frontier:
            nxt: dict[str, tuple[str, bool]] = {}
            for node in sorted(frontier, key=rank_key):
                if node in out:
                    continue
                why, strong = frontier[node]
                out[node] = (depth, why, strong)
                kind = pr.kind_of(node)
                if depth > 0 and kind not in PROPAGATING:
                    continue
                links = dict(self.edges.get(node, {}))
                if depth == 0 and kind not in PROPAGATING:
                    links.update({k: v for k, v in reverse.get(node, {}).items() if k not in links})
                if depth == 0 and kind == "ADR":
                    links.update({k: v for k, v in self.governs.get(node, {}).items() if k not in links})
                for target, (reason, link_strong) in links.items():
                    if target in out or target in frontier:
                        continue
                    path_strong = strong and link_strong
                    previous = nxt.get(target)
                    if previous is None or (path_strong and not previous[1]) or \
                            (path_strong == previous[1] and reason < previous[0]):
                        nxt[target] = (reason, path_strong)
            frontier = nxt
            depth += 1
        return out

    def affected(self, start: list[str]) -> dict[str, tuple[int, str]]:
        """Each affected ID with its distance and reason (the changed IDs at distance 0)."""
        return {k: (d, why) for k, (d, why, _) in self.impact(start).items()}


# --------------------------------------------------------------------------
# Classification
# --------------------------------------------------------------------------


@dataclass
class ImpactItem:
    id: str
    level: str          # DIRECT | INDIRECT | POTENTIAL
    confidence: str     # CONFIRMED | LIKELY | POSSIBLE
    depth: int
    reason: str

    def as_json(self) -> dict:
        return {"id": self.id, "level": self.level, "confidence": self.confidence, "reason": self.reason}


def classify(graph: Graph, bundle, changed: list[str], mentions: dict[str, set[str]] | None = None) -> list[ImpactItem]:
    """DIRECT (one link away), INDIRECT (further, through records that pass impact on) and POTENTIAL
    (upstream assumptions, requirements sharing a module, records that only mention the change)."""
    items: dict[str, ImpactItem] = {}
    for identifier, (depth, why, strong) in graph.impact(changed).items():
        if identifier in changed or depth == 0:
            continue
        items[identifier] = ImpactItem(identifier, "DIRECT" if depth == 1 else "INDIRECT",
                                       "CONFIRMED" if strong else "LIKELY", depth, why)

    def potential(identifier: str, why: str) -> None:
        if identifier and identifier not in items and identifier not in changed:
            items[identifier] = ImpactItem(identifier, "POTENTIAL", "POSSIBLE", 99, why)

    modules: set[str] = set()
    for c in changed:
        req = bundle.req_by_id.get(c)
        if req:
            for up in req.get("source") or []:
                potential(up, f"upstream assumption: {c} is derived from {up}; confirm {up} still holds")
            for up in req.get("dependencies") or []:
                potential(up, f"upstream assumption: {c} depends on {up}")
            modules |= set(req.get("related_modules") or [])
        if pr.kind_of(c) == "MOD":
            modules.add(c)
        feature = bundle.feat_by_id.get(c)
        if feature:
            modules |= set(feature.get("module_ids") or [])
    for req in sorted(bundle.requirements, key=lambda r: rank_key(r.get("id"))):
        shared = sorted(modules & set(req.get("related_modules") or []), key=rank_key)
        if shared and req.get("status") in ("approved", "confirmed"):
            potential(req["id"], f"shares {', '.join(shared)} with the changed record")
    for identifier, mentioned in sorted((mentions or {}).items(), key=lambda kv: rank_key(kv[0])):
        hit = sorted(mentioned & set(changed), key=rank_key)
        if hit:
            potential(identifier, f"its record mentions {', '.join(hit)}")
    order = {"DIRECT": 0, "INDIRECT": 1, "POTENTIAL": 2}
    return sorted(items.values(), key=lambda i: (order[i.level], i.depth, rank_key(i.id)))


def by_level(items: list[ImpactItem], level: str) -> list[str]:
    return [i.id for i in items if i.level == level]


# --------------------------------------------------------------------------
# Severity
# --------------------------------------------------------------------------


def severity(change_type: str | None, changed: list[str], items: list[ImpactItem], bundle) -> tuple[str, list[str]]:
    """CRITICAL, HIGH, MEDIUM or LOW, with the reasons that set it. Deterministic and explainable:
    CRITICAL means the current plan may be fundamentally invalid; HIGH that several planning artifacts
    need review; MEDIUM a limited downstream review; LOW documentation or minor planning updates."""
    reached = [i for i in items if i.level in ("DIRECT", "INDIRECT")]
    planning = [i.id for i in reached if pr.kind_of(i.id) in PLANNING_KINDS]
    tasks = [bundle.task_by_id[i.id] for i in reached if i.id in bundle.task_by_id]
    ready = sorted((t["id"] for t in tasks if t.get("status") == "READY"), key=rank_key)
    features = [i.id for i in reached if pr.kind_of(i.id) == "FEAT"]
    modules = {i.id for i in reached if pr.kind_of(i.id) == "MOD"}
    for c in changed:
        modules |= set((bundle.req_by_id.get(c) or {}).get("related_modules") or [])
        modules |= set((bundle.adr_by_id.get(c) or {}).get("affected_modules") or [])
    committed = sorted({t.get("phase") for t in tasks if t.get("phase")
                        and (bundle.phase_by_id.get(t.get("phase")) or {}).get("date_basis") == "commitment"}, key=rank_key)

    critical, high = [], []
    for c in changed:
        req = bundle.req_by_id.get(c)
        if req and pr.kind_of(c) in ("GOAL", "BR") and req.get("scope") in (None, "in_scope") and planning:
            critical.append(f"{c} is part of the business basis and in-scope planning rests on it")
        adr = bundle.adr_by_id.get(c)
        if adr and adr.get("status") in ("accepted", "superseded") and len(modules) >= 2:
            critical.append(f"{c} is an architecture decision that reaches {len(modules)} modules")
    if ready:
        high.append(f"READY tasks lose their readiness: {', '.join(ready)}")
    if len(features) >= 2:
        high.append(f"{len(features)} features are affected")
    if len(planning) >= 8:
        high.append(f"{len(planning)} planning artifacts are affected")
    if change_type in ("ARCHITECTURE_CHANGE", "SECURITY_CHANGE") and planning:
        high.append(f"{change_type.replace('_', ' ').lower()} with downstream planning")
    if committed:
        high.append(f"committed roadmap phases are affected: {', '.join(committed)}")
    if critical:
        return "CRITICAL", critical + high
    if high:
        return "HIGH", high
    if planning:
        return "MEDIUM", [f"{len(planning)} planning artifact(s) need a limited review"]
    return "LOW", ["only documents or context records are affected"]


# --------------------------------------------------------------------------
# Consequences: review areas, new work, roadmap, risks, documents
# --------------------------------------------------------------------------


def review_areas(change_type: str | None, items: list[ImpactItem]) -> list[dict]:
    areas = REVIEW_AREAS.get(change_type or "", [("Affected records", tuple(CONTROLLED_KINDS)), TRACE, DOCS])
    out = []
    for label, kinds in areas:
        found = [i.id for i in items if pr.kind_of(i.id) in kinds] if kinds else []
        out.append({"area": label, "ids": found})
    return out


def _acceptance_ids(item: dict) -> set[str]:
    out = set()
    for criterion in item.get("acceptance_criteria") or []:
        head = str(criterion).split(":", 1)[0].strip()
        if pr.FULL_ID_RE["AC"].match(head):
            out.add(head)
    return out


def missing_work(bundle, changed: list[str], detected: dict[str, dict]) -> list[str]:
    """New work a change may require that no task yet covers. Findings, never assumptions of coverage."""
    out: list[str] = []
    tested = set()
    for test in bundle.tests:
        tested |= set(test.get("acceptance_criteria_ids") or [])
    for task in bundle.tasks:
        tested |= _acceptance_ids(task)
    for c in changed:
        req = bundle.req_by_id.get(c)
        if req and req.get("status") in ("approved", "confirmed") and req.get("scope") in (None, "in_scope") \
                and pr.kind_of(c) in pr.IMPLEMENTABLE_KINDS:
            tasks = [t["id"] for t in bundle.tasks if c in (t.get("source_requirements") or [])]
            features = [f for f in bundle.features if c in (f.get("requirement_ids") or [])]
            if not features:
                out.append(f"No feature delivers {c} in its new state; new planning work is required.")
            if not tasks:
                out.append(f"No task implements {c} in its new state; new planning work is required.")
            covered_modules = {m for f in features for m in f.get("module_ids") or []}
            uncovered = sorted(set(req.get("related_modules") or []) - covered_modules, key=rank_key)
            if features and uncovered:
                out.append(f"{c} now concerns {', '.join(uncovered)}, which no feature delivering it covers.")
            for ac in sorted(_acceptance_ids(req) - tested, key=rank_key):
                out.append(f"{ac} of {c} is delivered by no task and verified by no test.")
            previous = (detected.get(c) or {}).get("previous")
            if previous:
                new_acs = sorted(_acceptance_ids(req) - set(re.findall(pr.ID_PATTERNS["AC"], previous)), key=rank_key)
                if new_acs:
                    out.append(f"{c} gains {', '.join(new_acs)} since the baseline; confirm which task delivers each.")
            if tasks:
                out.append(f"Confirm that the existing tasks ({', '.join(sorted(tasks, key=rank_key))}) cover the new state of {c}; "
                           f"existing tasks are not assumed to cover a changed requirement.")
        feature = bundle.feat_by_id.get(c)
        if feature and feature.get("scope") == "in_scope" and not feature.get("task_ids"):
            out.append(f"{c} is in scope but has no task; new planning work is required.")
    return out


def roadmap_impact(bundle, items: list[ImpactItem]) -> dict:
    ids = {i.id for i in items if i.level in ("DIRECT", "INDIRECT")}
    phases = {i for i in ids if pr.kind_of(i) == "PHASE"}
    phases |= {bundle.task_by_id[i].get("phase") for i in ids if i in bundle.task_by_id and bundle.task_by_id[i].get("phase")}
    phases = sorted(phases, key=rank_key)
    committed = [p for p in phases if (bundle.phase_by_id.get(p) or {}).get("date_basis") == "commitment"]
    notes = []
    if phases:
        notes.append(f"The roadmap requires re-estimation for {', '.join(phases)}; no timing is inferred from this analysis.")
    for p in committed:
        notes.append(f"{p} carries a committed date ({(bundle.phase_by_id.get(p) or {}).get('commitment_decision')}); "
                     f"the commitment must be reconfirmed by its decision owner.")
    return {"phases": phases, "committed_phases": committed, "notes": notes}


def risk_impact(bundle, changed: list[str], items: list[ImpactItem]) -> list[str]:
    ids = {i.id for i in items} | set(changed)
    risks = {i for i in ids if pr.kind_of(i) == "RISK"}
    for risk in bundle.risks:
        if ids & set(risk.get("affected_ids") or []):
            risks.add(risk["id"])
    return sorted(risks, key=rank_key)


def document_impact(documents: dict[str, set[str]], changed: list[str], items: list[ImpactItem]) -> list[dict]:
    ids = set(changed) | {i.id for i in items if i.level in ("DIRECT", "INDIRECT")}
    out = []
    for path, mentioned in sorted(documents.items()):
        hit = sorted(mentioned & ids, key=rank_key)
        if hit:
            out.append({"path": path, "ids": hit})
    return out


def rerun_gates(changed: list[str]) -> list[str]:
    earliest = min((KIND_GATE.get(pr.kind_of(i) or "", LAST_GATE) for i in changed), default=LAST_GATE)
    gates = [f"G{n}" for n in range(earliest, LAST_GATE + 1)]
    # A change that reaches the specification needs its independent re-review (GR) before approval (G8); one that
    # reaches the backlog needs its readiness revalidated (GB) after sequencing (G10).
    return [g for gate in gates for g in (("GR", gate) if gate == "G8" else (gate, "GB") if gate == "G10" else (gate,))]


# --------------------------------------------------------------------------
# Change records → changes.json
# --------------------------------------------------------------------------


def effective_state(level: str, disposition: dict | None, marks_plan: bool) -> str:
    if disposition and disposition.get("review_state") in REVIEW_STATES:
        return disposition["review_state"]
    if not marks_plan:
        return "CURRENT"
    return "NEEDS_REVIEW" if level in ("DIRECT", "INDIRECT", "NEW") else "CURRENT"


def analyse_change(record: dict, bundle, graph: Graph, ctx: SourceContext) -> dict:
    """The analysed form of one change record, as written to changes.json."""
    changed = record.get("changed_artifacts") or []
    items = classify(graph, bundle, changed, ctx.mentions)
    marks = record.get("status") in MARKING_STATUSES
    dispositions = record.get("dispositions") or {}
    computed, drivers = severity(record.get("change_type"), changed, items, bundle)
    affected = []
    for item in items:
        disposition = dispositions.get(item.id)
        affected.append({**item.as_json(), "review_state": effective_state(item.level, disposition, marks),
                         "resolution": (disposition or {}).get("resolution")})
    known = {i.id for i in items}
    for identifier, disposition in sorted(dispositions.items(), key=lambda kv: rank_key(kv[0])):
        if identifier in known:
            continue
        level = disposition.get("level") if disposition.get("level") in LEVELS else "POTENTIAL"
        affected.append({"id": identifier, "level": level, "confidence": disposition.get("confidence") or "POSSIBLE",
                         "reason": "recorded in the change record", "review_state": effective_state(level, disposition, marks),
                         "resolution": disposition.get("resolution")})
    ready = {t["id"] for t in bundle.tasks if t.get("status") == "READY"}
    reached = [a for a in affected if a["level"] in ("DIRECT", "INDIRECT", "NEW")]
    invalidated = sorted({a["id"] for a in affected if a["review_state"] == "INVALID"}
                         | {a["id"] for a in reached if a["id"] in ready and marks and a["review_state"] != "CURRENT"}, key=rank_key)
    return {
        **{k: v for k, v in record.items() if k not in ("dispositions",)},
        "marks_plan": marks,
        "computed_severity": computed,
        "severity_drivers": drivers,
        "direct_impact": by_level(items, "DIRECT"),
        "indirect_impact": by_level(items, "INDIRECT"),
        "potential_impact": by_level(items, "POTENTIAL"),
        "affected": affected,
        "invalidated_items": invalidated,
        "review_required": any(a["review_state"] != "CURRENT" for a in affected),
        "review_areas": review_areas(record.get("change_type"), items),
        "missing_work": missing_work(bundle, changed, ctx.detected),
        "roadmap": roadmap_impact(bundle, items),
        "risks": risk_impact(bundle, changed, items),
        "documents": document_impact(ctx.documents, changed, items),
        "rerun_gates": rerun_gates(changed),
    }


def coverage_of(changes: list[dict]) -> dict[str, list[tuple[str, str]]]:
    """Which change records account for an edit to each record: (change ID, status)."""
    out: dict[str, list[tuple[str, str]]] = {}
    for change in changes:
        ids = set(change.get("changed_artifacts") or [])
        ids |= {a["id"] for a in change.get("affected") or [] if a.get("resolution") in EDITING_RESOLUTIONS}
        for identifier in ids:
            out.setdefault(identifier, []).append((change["change_id"], change.get("status")))
    return out


def unrecorded_changes(changes: list[dict], detected: dict[str, dict], bundle, graph: Graph) -> list[dict]:
    """Records that differ from the baseline without an approved change record accounting for them."""
    covered = coverage_of(changes)
    out = []
    for identifier, diff in detected.items():
        by = covered.get(identifier, [])
        if any(status in MARKING_STATUSES for _, status in by):
            continue
        reached = classify(graph, bundle, [identifier])
        out.append({
            "id": identifier,
            "change": diff["change"],
            "covered_by": sorted((c for c, _ in by), key=rank_key),
            "affected": [i.id for i in reached if i.level in ("DIRECT", "INDIRECT") and i.confidence in ("CONFIRMED", "LIKELY")],
            "source_path": diff["source_path"],
        })
    return out


def artifact_states(changes: list[dict], unrecorded: list[dict]) -> dict[str, dict]:
    """Every artifact that is not CURRENT, with its worst state, the changes behind it and why."""
    out: dict[str, dict] = {}

    def mark(identifier: str, state: str, change: str, reason: str) -> None:
        entry = out.setdefault(identifier, {"id": identifier, "state": "CURRENT", "change_ids": [], "reasons": []})
        if STATE_RANK[state] > STATE_RANK[entry["state"]]:
            entry["state"] = state
        if change not in entry["change_ids"]:
            entry["change_ids"].append(change)
        if reason not in entry["reasons"]:
            entry["reasons"].append(reason)

    for change in changes:
        if not change.get("marks_plan"):
            continue
        for item in change.get("affected") or []:
            if item.get("review_state") in REVIEW_STATES and item["review_state"] != "CURRENT":
                mark(item["id"], item["review_state"], change["change_id"],
                     f"{change['change_id']}: {item['review_state'].replace('_', ' ').lower()}")
    for entry in unrecorded:
        reason = f"{entry['id']} changed since the baseline without an approved change record"
        mark(entry["id"], "NEEDS_REVIEW", "UNRECORDED", reason)
        for identifier in entry.get("affected") or []:
            mark(identifier, "NEEDS_REVIEW", "UNRECORDED", reason)
    for entry in out.values():
        entry["change_ids"].sort(key=rank_key)
    return {k: out[k] for k in sorted(out, key=rank_key) if out[k]["state"] != "CURRENT"}


def summary(changes: list[dict], unrecorded: list[dict], states: dict[str, dict], tasks: list[dict]) -> dict:
    open_changes = [c for c in changes if c.get("status") in OPEN_STATUSES]
    task_status = {t.get("id"): t.get("status") for t in tasks}
    stale_tasks = [i for i in states if i in task_status]
    return {
        "open_changes": len(open_changes),
        "critical_changes": sum(1 for c in open_changes if c.get("computed_severity") == "CRITICAL"),
        "items_needing_review": len(states),
        "stale_tasks": len(stale_tasks),
        "invalid_ready_tasks": sum(1 for i in stale_tasks if task_status.get(i) == "READY"),
        "unrecorded_changes": len(unrecorded),
    }


def changes_document(records: list[dict], bundle, ctx: SourceContext, schema_version: str, project_id: str) -> dict:
    graph = Graph(bundle, ctx.details)
    changes = [analyse_change(r, bundle, graph, ctx) for r in sorted(records, key=lambda r: rank_key(r["change_id"]))]
    unrecorded = unrecorded_changes(changes, ctx.detected, bundle, graph)
    states = artifact_states(changes, unrecorded)
    baseline = ctx.baseline or {}
    return {
        "schema_version": schema_version,
        "project_id": project_id,
        "baseline": {
            "exists": ctx.baseline is not None,
            "created_at": baseline.get("created_at"),
            "specification_version": baseline.get("specification_version"),
            "incorporated_changes": baseline.get("incorporated_changes") or [],
            "controlled_kinds": baseline.get("controlled_kinds") or [],
        },
        "summary": summary(changes, unrecorded, states, bundle.tasks),
        "detected_changes": [{"id": d["id"], "change": d["change"], "source_path": d["source_path"]} for d in ctx.detected.values()],
        "unrecorded_changes": unrecorded,
        "changes": changes,
        "artifact_states": list(states.values()),
    }


# --------------------------------------------------------------------------
# Reports
# --------------------------------------------------------------------------


def _cell(value) -> str:
    if isinstance(value, (list, tuple)):
        value = ", ".join(str(v) for v in value) if value else "—"
    text = str(value) if value not in (None, "") else "—"
    return text.replace("|", "\\|").replace("\n", " ")


def impact_report(entry: dict, bundle, detected: dict[str, dict], generated_at: str) -> str:
    """changes/CHANGE-###-impact-report.md: the structured answer to 'what does this change affect?'."""
    cid = entry.get("change_id") or "What-if"
    lines = [f"# {cid} — Impact Report", "",
             "<!-- GENERATED by tools/analyze_change_impact.py. Do not edit: change the records and re-run the analysis. -->", "",
             f"Title: {entry.get('title') or '—'} · Type: {entry.get('change_type') or '—'} · Status: {entry.get('status') or '—'} · "
             f"Analysed: {generated_at}", "",
             "Links come from the records, not from keyword matching. DIRECT is one link away; INDIRECT is reached through "
             "records that pass impact on; POTENTIAL is an upstream assumption, a requirement sharing a module, or a record "
             "that only mentions the change. CONFIRMED means every link on the way is an explicit dependency; LIKELY that "
             "one is a membership or context link; POSSIBLE that the link is inferred.", "",
             "## Changed artifacts", ""]
    for identifier in entry.get("changed_artifacts") or []:
        diff = detected.get(identifier)
        state = f"{diff['change']} since the baseline" if diff else "unchanged since the baseline (not yet applied, or already baselined)"
        lines.append(f"- {identifier} — {state}")
    for identifier in entry.get("changed_artifacts") or []:
        diff = detected.get(identifier)
        if diff and diff.get("previous") is not None:
            lines += ["", f"### {identifier} — previous state (baseline)", "", "```text", diff["previous"], "```"]
        if diff and diff.get("current") is not None:
            lines += ["", f"### {identifier} — current state", "", "```text", diff["current"], "```"]
    lines += ["", "## Severity", "", f"**{entry['computed_severity']}** (computed)"
              + (f" · declared {entry['declared_severity']}" if entry.get("declared_severity") else ""), ""]
    lines += [f"- {d}" for d in entry.get("severity_drivers") or []]
    for level, title in (("DIRECT", "Direct impact"), ("INDIRECT", "Indirect impact"), ("POTENTIAL", "Potential impact")):
        rows = [a for a in entry.get("affected") or [] if a["level"] == level]
        lines += ["", f"## {title}", ""]
        if not rows:
            lines.append("None.")
            continue
        lines += ["| Artifact | Confidence | Review state | Resolution | Why |", "| --- | --- | --- | --- | --- |"]
        lines += [f"| {_cell(a['id'])} | {a['confidence']} | {a['review_state']} | {_cell(a.get('resolution'))} | {_cell(a['reason'])} |"
                  for a in rows]
    new = [a for a in entry.get("affected") or [] if a["level"] == "NEW"]
    if new:
        lines += ["", "## New artifacts recorded by this change", ""] + [f"- {a['id']} — {_cell(a.get('resolution'))}" for a in new]
    marked = [a["id"] for a in entry.get("affected") or [] if a["review_state"] != "CURRENT"]
    lines += ["", "## Artifacts marked for review", ""]
    if not entry.get("marks_plan"):
        lines.append(f"None yet: the change is {entry.get('status')}, and a change that is not APPROVED does not alter the "
                     f"authoritative plan. Once approved, every DIRECT and INDIRECT artifact above is NEEDS_REVIEW until "
                     f"the change record dispositions it.")
    else:
        lines += [f"- {i}" for i in marked] or ["None — every affected artifact is dispositioned CURRENT."]
    lines += ["", "## Readiness withdrawn", ""]
    lines += [f"- {i}" for i in entry.get("invalidated_items") or []] or ["None."]
    tasks = [bundle.task_by_id[a["id"]] for a in entry.get("affected") or []
             if a["level"] in ("DIRECT", "INDIRECT") and a["id"] in bundle.task_by_id]
    lines += ["", "## Readiness of affected tasks", "",
              "Sequencing is re-validated from the records: a task whose predecessor is no longer READY, IN_PROGRESS or "
              "DONE, or that now sits in a dependency cycle, is not actionable whatever this change record says.", ""]
    if tasks:
        lines += ["| Task | Status | Depends on | Readiness gaps |", "| --- | --- | --- | --- |"]
        lines += [f"| {t['id']} | {t.get('status')} | {_cell(t.get('dependencies'))} | {_cell('; '.join(t.get('readiness_gaps') or []) or 'None')} |"
                  for t in sorted(tasks, key=lambda t: rank_key(t["id"]))]
    else:
        lines.append("No task is reached.")
    lines += ["", "## Required reviews", "", "| Review area | Artifacts the graph found |", "| --- | --- |"]
    lines += [f"| {area['area']} | {_cell(area['ids']) if area['ids'] else 'None found by the graph — confirm'} |"
              for area in entry.get("review_areas") or []]
    lines += ["", "## New work that may be required", ""]
    lines += [f"- {m}" for m in entry.get("missing_work") or []] or ["None detected. Confirm it in the change record's *New work required*."]
    roadmap = entry.get("roadmap") or {}
    lines += ["", "## Roadmap impact", ""]
    lines += [f"- {n}" for n in roadmap.get("notes") or []] or ["No roadmap phase is reached."]
    lines += ["", "## Risk impact", ""]
    if entry.get("risks"):
        lines.append(f"Review {', '.join(entry['risks'])}: each may be increased, reduced or retired by this change. "
                     f"Record the effect, and any new risk, in the change record's *Risk impact* table and the risk register.")
    else:
        lines.append("No linked risk. Consider whether the change creates one; record it in the change record either way.")
    lines += ["", "## Documents to regenerate or review", ""]
    lines += [f"- `{d['path']}` — mentions {', '.join(d['ids'])}" for d in entry.get("documents") or []] or \
        ["No human document mentions an affected artifact."]
    lines.append("- `traceability/requirement-map.md`, `machine-handoff/` and `reports/` are regenerated by the tools.")
    lines += ["", "## Gates to re-run", "", f"{', '.join(entry.get('rerun_gates') or [])} and GC — `python tools/check_gates.py projects/<project>`", ""]
    lines += ["## Required actions", "",
              "1. Record the human decision: APPROVED or REJECTED, with *Approved by* and *Approval evidence*.",
              "2. Disposition every DIRECT and INDIRECT artifact in the change record's *Affected artifacts* table: CURRENT, STALE or INVALID, with a resolution.",
              "3. Complete every required review area, the risk impact and the roadmap impact; record the new work, and add it as records.",
              "4. Update the affected records, then regenerate and re-run the gates listed above.",
              "5. Mark the change IMPLEMENTED_IN_PLAN only when no affected artifact remains NEEDS_REVIEW, STALE or INVALID.", ""]
    return "\n".join(lines)
