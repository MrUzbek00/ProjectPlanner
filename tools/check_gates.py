#!/usr/bin/env python3
"""Evaluate the workflow's stage gates, the review gate GR, the backlog gate GB and the change-impact gate GC.

Every stage of the workflow ends in a gate. This tool evaluates each gate from
what the records actually contain, and reports PASS, PASS WITH WARNINGS or
FAIL with the exact reasons. It also checks that project-state.md does not
claim a gate or a stage that the evidence does not support, which is how the
workflow stops a stage from claiming completion while a mandatory criterion
fails.

What it checks is deliberately limited to what can be decided from the
records: presence and completeness of required records, classifications,
open blockers, traceability, dependencies, review checklists and findings,
architecture governance (concern coverage, ADR lifecycle and register,
conflicts, drift), the independent specification review (gate GR, verified
by tools/specification_review.py), backlog readiness (gate GB, from
tools/backlog_readiness.py) and requirement-quality heuristics. Whether
a requirement is *right* is a human judgement, recorded in the review documents
this tool reads.

Usage:
    python tools/check_gates.py projects/<project>
    python tools/check_gates.py projects/<project> --gate G3
    python tools/check_gates.py projects/<project> --no-write

Writes reports/gate-report.md, reports/dependency-graph.md,
reports/architecture-report.md and reports/specification-review-aid.md unless
--no-write is given. Exit code 1 when a gate before the current stage fails
or project-state.md claims a gate the evidence does not support; 0 otherwise;
2 when the tool cannot run.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import change_impact as ci  # noqa: E402
import generate_handoff as gh  # noqa: E402
import backlog_readiness as br  # noqa: E402
import planning_records as pr  # noqa: E402
import specification_review as sr  # noqa: E402
import validate_handoff as vh  # noqa: E402

PASS, WARN, FAIL = "PASS", "PASS WITH WARNINGS", "FAIL"

STAGES = [
    # number, stage, gate id, gate name
    (1, "Project Intake", "G1", "Intake complete"),
    (2, "Discovery", "G2", "Discovery ready"),
    (3, "Requirement Analysis", "G3", "Requirements ready"),
    (4, "Process and Domain Analysis", "G4", "Models ready"),
    (5, "Solution Planning and Scope", "G5", "Solution and scope ready"),
    (6, "Architecture Governance", "G6", "Architecture ready"),
    (7, "Specification", "G7", "Specification complete"),
    # Stage 8 has two halves: 8A, the independent review (GR), then 8B, resolution and approval (G8).
    (8, "Independent Specification Review", "GR", "Specification reviewed"),
    (8, "Specification Resolution and Approval", "G8", "Specification ready"),
    (9, "Backlog Decomposition", "G9", "Backlog decomposed"),
    # Stage 10 has two halves: 10A, dependencies and priorities (G10), then 10B, readiness validation (GB).
    (10, "Dependency Mapping and Prioritisation", "G10", "Sequencing ready"),
    (10, "Backlog Readiness Validation", "GB", "Backlog ready"),
    (11, "Roadmap and Project Plan", "G11", "Roadmap ready"),
    (12, "Traceability Validation", "G12", "Planning validated"),
    (13, "Final Planning Package", "G13", "Planning package ready"),
]
LAST_STAGE = STAGES[-1][0]
STAGE_LABEL = {"GR": "8A", "G8": "8B", "G10": "10A", "GB": "10B"}

# The architecture concerns every project classifies at gate G6. A project may add rows; it may not drop these.
ARCH_CONCERNS = [
    "Architecture style", "Backend platform", "Frontend architecture", "Data storage", "Authentication",
    "Authorization model", "API style", "Integration strategy", "Event-driven messaging", "Background processing",
    "Caching", "File storage", "Deployment model", "Multi-tenancy", "Data ownership", "Module communication",
    "Logging and observability", "Security architecture", "External service dependencies", "Scalability strategy",
]
CONFLICT_RESOLUTIONS = ("CHANGE PROPOSAL", "NEW ADR", "SUPERSEDE ADR")
# Findings that report a contradiction with the accepted architecture.
CONFLICT_CODES = {"ADR_ACTIVE_CONFLICT", "ADR_INACTIVE_REFERENCE", "ARCHITECTURE_CONFLICT"}
# The continuous change-impact gate. It belongs to no stage; gates G12 and G13 require it.
CHANGE_GATE = ("GC", "Change impact reviewed", "Change control (continuous)")
# Contradictions a change must not leave behind: re-checked by GC whenever a change exists.
POST_CHANGE_CODES = {"ADR_ACTIVE_CONFLICT", "ADR_INACTIVE_REFERENCE", "PHASE_ORDER", "UNSUPPORTED_COMMITMENT",
                     "IMPOSSIBLE_SEQUENCING", "DEPENDENCY_CYCLE", "FEATURE_DEPENDENCY_CYCLE", "ORPHAN_FEATURE", "ORPHAN_TASK",
                     "TRACEABILITY_MISMATCH", "UNKNOWN_REFERENCE"}
GATE_NUMBER = {gate: number for number, _, gate, _ in STAGES}

INTAKE_ITEMS = [
    "Project name", "Project objective", "Business problem", "Target users", "Stakeholders", "Known scope",
    "Constraints", "Deadlines", "Existing systems", "Available files", "Screenshots", "Stakeholder notes",
    "Known assumptions", "Known risks",
]
INTAKE_CLASSES = {"CONFIRMED", "LIKELY", "ASSUMED", "ASSUMPTION", "UNKNOWN"}
DISCOVERY_CATEGORIES = [
    "Business", "Users", "Workflows", "Data", "Integrations", "Security", "Permissions", "Reporting",
    "Notifications", "Technical constraints", "UI/UX", "Operations", "Compliance", "Migration",
]
DISCOVERY_STATUS = {"COMPLETE", "PARTIAL", "NOT STARTED", "NOT APPLICABLE"}
SUMMARY_QUESTIONS = [
    "What problem are we solving?", "Who are we solving it for?", "What is in scope?", "What is not in scope?",
    "What should the system do?", "What constraints must it respect?", "What are the major workflows?",
    "What are the major modules/features?", "What requirements support each feature?",
    "What work needs to happen?", "What depends on what?", "What should happen first?", "What risks exist?",
    "What is still unknown?", "What decisions were made?",
]
DELIVERABLES = ["prd.md", "brd.md", "srs.md", "sow.md", "user-journey-stories.md", "wireframes-uiux.md",
                "project-plan-roadmap.md", "package-manifest.md"]
SEVERITIES = ("CRITICAL", "MAJOR", "MINOR", "OBSERVATION")
OPEN_FINDING = {"OPEN", "IN PROGRESS", ""}

WEAK_TERMS = ["fast", "easy", "easily", "modern", "user-friendly", "user friendly", "secure", "flexible", "efficient",
              "simple", "intuitive", "quickly", "robust", "scalable", "seamless", "as appropriate", "etc"]
IMPLEMENTATION_TERMS = ["database", "table", "column", "endpoint", "api", "rest", "json", "sql", "react", "django",
                        "microservice", "serializer", "framework", "redis", "kafka", "cron", "orm"]
ERROR_WORDS = re.compile(r"\b(reject|rejected|deny|denied|error|invalid|fail|fails|failed|not allowed|cannot|"
                         r"unauthori[sz]ed|expired|refus|blocked|locked|unchanged|prevent)", re.IGNORECASE)

# Where validator and generator findings belong. Code first, then location, then step.
CODE_GATE = {
    "MISSING_PROJECT_ID": "G1", "MISSING_PROJECT_NAME": "G7",
    "SPEC_APPROVAL_MISSING": "G8", "APPROVED_WITHOUT_SPECIFICATION": "G8", "APPROVAL_VERSION_MISMATCH": "G8",
    "CONFIRMED_NOT_APPROVED": "G8",
    "DEPENDENCY_CYCLE": "G10", "SELF_DEPENDENCY": "G10", "PARENT_CYCLE": "G10", "FEATURE_DEPENDENCY_CYCLE": "G10",
    "HIDDEN_PREREQUISITE": "G10", "IMPOSSIBLE_SEQUENCING": "G10", "BLOCKED_BY_DECISION": "G10",
    "PRIORITY_SCHEME": "G10", "PRIORITY_SCHEME_UNDECLARED": "G10", "PRIORITY_NOT_DISCRIMINATING": "G10",
    "PHASE_ORDER": "G11", "UNSUPPORTED_COMMITMENT": "G11", "UNQUALIFIED_DATE": "G11",
    "ORPHAN_FEATURE": "G9", "ORPHAN_TASK": "G9", "BACKLOG_INDEX_CONFLICT": "G9", "READY_NOT_MET": "GB",
    "READINESS_MISMATCH": "GB", "READINESS_HISTORY": "GB", "BACKLOG_READINESS_MISMATCH": "GB",
    "ORPHAN_REQUIREMENT": "G12", "REQUIREMENT_WITHOUT_TASK": "G12", "REQUIREMENT_WITHOUT_TEST": "G12",
    "REQUIREMENT_NOT_REALISED": "G12", "ORPHAN_TEST": "G12",
    "UNDEFINED_ID_IN_DOCUMENT": "G13", "DELIVERABLE_OUT_OF_DATE": "G13", "LEGACY_ID": "G12",
    "PROCESS_COMPARISON": "G4",
    "ADR_FILE_STRUCTURE": "G6", "ADR_FILE_NAME": "G6", "ADR_DECISION_QUESTION_MISSING": "G6", "ADR_DECISION_PENDING": "G6",
    "ADR_APPROVAL_MISSING": "G6", "ADR_INCOMPLETE": "G6", "ADR_NO_ALTERNATIVES": "G6", "ADR_NO_CONSTRAINTS": "G6",
    "VAGUE_CONSTRAINT": "G6", "ADR_IMPLEMENTATION_DETAIL": "G6", "ADR_ACTIVE_CONFLICT": "G6",
    "ADR_SUPERSESSION_MISMATCH": "G6", "ADR_SUPERSEDE_CYCLE": "G6", "ADR_DEPENDENCY_CYCLE": "G6",
    "ADR_INACTIVE_DEPENDENCY": "G6", "ADR_DEPENDS_ON_PROPOSED": "G6",
    "CHANGE_FILE_STRUCTURE": "GC", "CHANGE_FILE_NAME": "GC", "CHANGE_STATE_MISMATCH": "GC",
    "SPEC_REVIEW_RESULT_MISMATCH": "GR", "SPEC_REVIEW_COUNT_MISMATCH": "GR", "SPEC_REVIEW_CRITICAL_ACCEPTED": "GR",
    "SPEC_REVIEW_UNRESOLVED_CLOSURE": "GR", "SPEC_REVIEW_HISTORY": "GR", "SPEC_REVIEW_STALE": "GR",
    "SPEC_REVIEW_MISMATCH": "GR",
}
# Findings about how a record uses the architecture: governance (G6) for requirements and ADRs,
# backlog (G9) for features and tasks.
ARCH_ITEM_CODES = {"ADR_INACTIVE_REFERENCE", "ARCHITECTURE_CONFLICT", "ADR_LINK_MISMATCH"}
# Findings that are only warnings for the machine handoff but mean a gate is not met.
ESCALATE = {"ORPHAN_REQUIREMENT", "REQUIREMENT_WITHOUT_TASK", "REQUIREMENT_WITHOUT_TEST", "REQUIREMENT_NOT_REALISED",
            "NO_BUSINESS_SOURCE", "NO_GOAL_SOURCE", "UNDEFINED_ID_IN_DOCUMENT", "DELIVERABLE_OUT_OF_DATE",
            "PRIORITY_SCHEME_UNDECLARED"}
IGNORE = {"HANDOFF_STATUS_MISMATCH", "HANDOFF_STATUS_CONSERVATIVE", "TASKS_BEFORE_APPROVAL"}
LOCATION_GATE = [
    ("changes/", "GC"), ("changes.json", "GC"),
    ("discovery/", "G2"), ("decisions.json", "G2"),
    ("specification/process-model", "G4"), ("specification/domain-model", "G4"), ("domain.json", "G4"),
    ("specification/solution-structure", "G5"), ("specification/scope", "G5"),
    ("architecture/", "G6"), ("architecture.json", "G6"), ("reviews/architecture-review", "G6"),
    ("specification/", "G3"), ("requirements.json", "G3"),
    ("project-state", "G8"), ("project.json", "G8"),
    ("backlog/", "G9"), ("backlog.json", "G9"), ("tasks/", "G9"),
    ("quality/", "G12"), ("tests.json", "G12"), ("traceability", "G12"),
    ("backlog-readiness.json", "GB"), ("backlog/readiness-report", "GB"),
    ("specification-review.json", "GR"), ("reviews/specification-review", "GR"), ("reviews/history/", "GR"),
    ("deliverables/", "G13"), ("reviews/", "G12"),
]
STEP_GATE = {vh.STEP_SPEC: "G8", vh.STEP_REQ: "G3", vh.STEP_BACKLOG: "G9", vh.STEP_SCHEMA: "G12", vh.STEP_TRACE: "G12"}


@dataclass
class Issue:
    level: str  # error | warning
    message: str
    location: str = ""


@dataclass
class GateResult:
    gate: str
    name: str
    stage: str
    number: int
    issues: list[Issue] = field(default_factory=list)

    def error(self, message: str, location: str = "") -> None:
        self.issues.append(Issue("error", message, location))

    def warn(self, message: str, location: str = "") -> None:
        self.issues.append(Issue("warning", message, location))

    @property
    def result(self) -> str:
        if any(i.level == "error" for i in self.issues):
            return FAIL
        return WARN if self.issues else PASS


# --------------------------------------------------------------------------
# Reading stage records
# --------------------------------------------------------------------------


def field_table(path: Path) -> dict[str, str]:
    for table in pr.read_tables(path):
        if table.keys()[:1] == ["field"]:
            return {pr.norm_key(row[0]): pr.clean(row[1]) if len(row) > 1 else "" for row in table.rows if row}
    return {}


def first_table(path: Path, *first_headers: str) -> pr.Table | None:
    wanted = {pr.norm_key(h) for h in first_headers}
    for table in pr.read_tables(path):
        if table.keys()[:1] and table.keys()[0] in wanted:
            return table
    return None


def cell(row: dict, *names: str) -> str:
    return gh.col(row, *names)


@dataclass
class Review:
    path: Path
    fields: dict[str, str]
    checklist: list[tuple[int, str, str, str]]  # line, check, result, evidence
    findings: list[tuple[int, dict]]


def read_review(project: Path, rel: str) -> Review | None:
    path = project / rel
    if not path.is_file():
        return None
    checklist = []
    # Every table whose first column is 'Check' is part of the checklist.
    for table in pr.read_tables(path):
        if table.keys()[:1] != ["check"]:
            continue
        for line, row in table.dict_rows():
            check = cell(row, "check")
            if check:
                evidence = cell(row, "evidence / ids", "evidence", "findings")
                checklist.append((line, check, gh.norm_enum(cell(row, "result")).upper(), evidence))
    findings = []
    table = first_table(path, "Finding ID")
    if table:
        for line, row in table.dict_rows():
            fid = cell(row, "finding id")
            if pr.FULL_ID_RE["FIND"].match(fid):
                findings.append((line, row))
    return Review(path, field_table(path), checklist, findings)


def review_issues(result: GateResult, review: Review | None, label: str, project: Path,
                  expected_version: str | None = None) -> None:
    """A review counts only when its checklist is complete and no serious finding is open."""
    if review is None:
        result.error(f"The {label} has not been written.")
        return
    where = pr.rel(project, review.path)
    if expected_version:
        reviewed = review.fields.get("reviewed version", "")
        if reviewed != expected_version:
            result.error(f"The {label} covers version {reviewed or 'unstated'}; the specification is version {expected_version}. Review the current version.", where)
    if not review.checklist:
        result.error(f"The {label} has no completed checklist; a blank checklist is not a pass.", where)
    for line, check, outcome, evidence in review.checklist:
        loc = f"{where}:{line}"
        if outcome not in ("PASS", "FAIL", "N/A", "NOT REVIEWED"):
            result.error(f"Checklist item '{check}' has result {outcome or 'blank'}; use PASS, FAIL, N/A or NOT REVIEWED.", loc)
        elif outcome == "NOT REVIEWED":
            result.error(f"Checklist item '{check}' is NOT REVIEWED.", loc)
        elif outcome == "FAIL":
            result.error(f"Checklist item '{check}' FAILED: {evidence or 'no evidence recorded'}.", loc)
        elif outcome == "N/A" and not evidence:
            result.error(f"Checklist item '{check}' is N/A without a reason.", loc)
    for line, row in review.findings:
        severity = gh.norm_enum(cell(row, "severity")).upper()
        status = gh.norm_enum(cell(row, "status")).upper()
        fid = cell(row, "finding id")
        text = cell(row, "finding")
        loc = f"{where}:{line}"
        if severity not in SEVERITIES:
            result.error(f"{fid} has severity {severity or 'blank'}; use CRITICAL, MAJOR, MINOR or OBSERVATION.", loc)
        elif severity in ("CRITICAL", "MAJOR") and status not in ("RESOLVED", "WITHDRAWN"):
            # A serious finding is fixed or withdrawn; it cannot be accepted away.
            back = cell(row, "return to stage")
            state = "is open" if status in OPEN_FINDING else f"is {status}, which does not close a {severity} finding"
            result.error(f"{severity} finding {fid} {state}: {text}" + (f" (return to stage {back})" if back else ""), loc)
        elif status in OPEN_FINDING and severity == "MINOR":
            result.warn(f"MINOR finding {fid} is open: {text}", loc)


# --------------------------------------------------------------------------
# Context
# --------------------------------------------------------------------------


class Context:
    def __init__(self, project: Path):
        self.project = project
        now = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
        docs, src, _ = gh.build(project, now)
        _, json_findings, bundle = gh.finalize(docs, src)
        self.docs = docs
        self.bundle = bundle
        self.spec_review: sr.Evaluation = src.spec_review
        self.findings = src.findings.items + json_findings.items
        self.state = field_table(project / pr.STATE_FILE) if (project / pr.STATE_FILE).is_file() else {}
        stage_raw = self.state.get("current stage", "")
        match = re.search(r"\d+", stage_raw)
        self.current_stage = int(match.group(0)) if match else None
        self.claims: dict[str, tuple[str, int]] = {}
        state_path = project / pr.STATE_FILE
        if state_path.is_file():
            table = first_table(state_path, "Gate")
            if table:
                for line, row in table.dict_rows():
                    gate = re.match(r"\s*(G\d+|GC|GR|GB)\b", cell(row, "gate"))
                    if gate:
                        self.claims[gate.group(1)] = (gh.norm_enum(cell(row, "status")).upper(), line)
        self.review_summary: dict[str, tuple[str, int]] | None = None
        if state_path.is_file():
            table = first_table(state_path, "Review measure")
            if table:
                self.review_summary = {pr.norm_key(cell(row, "review measure")): (cell(row, "value"), line)
                                       for line, row in table.dict_rows()}
        b = bundle
        self.blockers = [q for q in b.questions if q.get("blocking") and not q.get("resolved")]
        self.live = [r for r in b.requirements if r.get("status") in vh.LIVE_STATUSES]
        self.in_scope = [r for r in self.live if r.get("scope") == "in_scope"]
        review = read_review(project, pr.ARCHITECTURE_REVIEW_FILE)
        self.conflict_findings = [row for _, row in (review.findings if review else [])
                                  if gh.norm_enum(cell(row, "type")).upper() == "ARCHITECTURE CONFLICT"]

    def exists(self, rel: str) -> bool:
        return (self.project / rel).is_file()

    def rel(self, path: str) -> str:
        return path

    def quarantined(self, question: dict) -> bool:
        """A blocker is contained when everything it affects is outside the current scope."""
        targets = question.get("affected_ids") or []
        if not targets:
            return False
        for target in targets:
            item = (self.bundle.req_by_id.get(target) or self.bundle.feat_by_id.get(target)
                    or self.bundle.scope_by_id.get(target))
            if item is None:
                return False
            scope = item.get("scope") if "scope" in item else item.get("classification")
            if scope not in ("pending_decision", "future", "out_of_scope"):
                return False
        return True


# --------------------------------------------------------------------------
# Gate checks
# --------------------------------------------------------------------------


def check_g1(ctx: Context, g: GateResult) -> None:
    rel = pr.INTAKE_FILE
    if not ctx.exists(rel):
        g.error(f"{rel} does not exist; record the project intake first.")
        return
    table = first_table(ctx.project / rel, "Intake item")
    if table is None:
        g.error("The intake has no table whose first column is 'Intake item'.", rel)
        return
    rows = {pr.norm_key(cell(row, "intake item")): (line, row) for line, row in table.dict_rows()}
    for item in INTAKE_ITEMS:
        found = rows.get(pr.norm_key(item))
        if found is None:
            g.error(f"Intake item '{item}' is missing.", rel)
            continue
        line, row = found
        classification = gh.norm_enum(cell(row, "classification")).upper()
        info = cell(row, "information")
        if classification not in INTAKE_CLASSES:
            g.error(f"Intake item '{item}' is not classified CONFIRMED, ASSUMED or UNKNOWN.", f"{rel}:{line}")
        elif classification == "UNKNOWN" and not pr.extract_ids(info + " " + cell(row, "source"), ("Q",)):
            g.warn(f"Intake item '{item}' is UNKNOWN without a question (Q-###) to resolve it.", f"{rel}:{line}")
        elif classification in ("ASSUMED", "ASSUMPTION") and not pr.extract_ids(info + " " + cell(row, "source"), ("ASM",)):
            g.warn(f"Intake item '{item}' is ASSUMED without an assumption record (ASM-###).", f"{rel}:{line}")
        if classification == "UNKNOWN" and item in ("Project objective", "Business problem"):
            g.warn(f"'{item}' is still UNKNOWN; discovery must resolve it before requirements are written.", f"{rel}:{line}")


def blocker_issues(ctx: Context, g: GateResult, label: str) -> None:
    for q in ctx.blockers:
        if not ctx.quarantined(q):
            affected = ", ".join(q.get("affected_ids") or []) or "the whole project"
            g.error(f"BLOCKER question {q['id']} is open and affects {affected}: {q.get('question')} "
                    f"Resolve it, or classify everything it affects as PENDING DECISION, FUTURE or OUT OF SCOPE, before {label}.",
                    "discovery/open-questions.md")


def check_g2(ctx: Context, g: GateResult) -> None:
    for rel in (pr.DISCOVERY_LOG_FILE, "discovery/open-questions.md", "discovery/assumptions.md", "discovery/risks.md"):
        if not ctx.exists(rel) and not (rel != pr.DISCOVERY_LOG_FILE and ctx.exists("discovery/registers.md")):
            g.error(f"{rel} does not exist.")
    if ctx.exists(pr.DISCOVERY_LOG_FILE):
        table = first_table(ctx.project / pr.DISCOVERY_LOG_FILE, "Category")
        rows = {}
        if table is None:
            g.error("The discovery log has no coverage table whose first column is 'Category'.", pr.DISCOVERY_LOG_FILE)
        else:
            rows = {pr.norm_key(cell(row, "category")): (line, row) for line, row in table.dict_rows()}
        for category in DISCOVERY_CATEGORIES:
            found = rows.get(pr.norm_key(category))
            if table is not None and found is None:
                g.error(f"Discovery category '{category}' is missing from the coverage table.", pr.DISCOVERY_LOG_FILE)
                continue
            if found is None:
                continue
            line, row = found
            loc = f"{pr.DISCOVERY_LOG_FILE}:{line}"
            status = gh.norm_enum(cell(row, "status")).upper()
            if status not in DISCOVERY_STATUS:
                g.error(f"Category '{category}' has status {status or 'blank'}; use COMPLETE, PARTIAL, NOT STARTED or NOT APPLICABLE.", loc)
            elif status == "NOT STARTED":
                g.error(f"Category '{category}' has not been investigated.", loc)
            elif status == "NOT APPLICABLE" and not (cell(row, "confirmed information") or cell(row, "sources")):
                g.error(f"Category '{category}' is NOT APPLICABLE without a reason and source.", loc)
            elif status == "PARTIAL":
                g.warn(f"Category '{category}' is only partially understood; its open questions: "
                       f"{', '.join(pr.extract_ids(cell(row, 'open questions'), ('Q',))) or 'none listed'}.", loc)
    blocker_issues(ctx, g, "planning continues")
    for q in ctx.bundle.questions:
        if q.get("resolved"):
            continue
        if q.get("priority") == "HIGH":
            g.warn(f"HIGH question {q['id']} is open: {q.get('question')}", "discovery/open-questions.md")
        if not q.get("owner"):
            g.warn(f"Open question {q['id']} has no decision owner.", "discovery/open-questions.md")


def lint_requirement(req: dict) -> list[str]:
    """Heuristic requirement-quality findings. Warnings for the reviewer, not verdicts."""
    notes = []
    text = " ".join([req.get("title", ""), req.get("description", "")])
    criteria = " ".join(req.get("acceptance_criteria") or [])
    # Identifiers such as AC-001 contain digits but measure nothing.
    measurable = bool(re.search(r"\d", pr.ANY_ID_RE.sub("", req.get("description", "") + " " + criteria)))
    lowered = f" {text.lower()} {criteria.lower()} "
    weak = [w for w in WEAK_TERMS if re.search(rf"(?<![\w-]){re.escape(w)}(?![\w-])", lowered)]
    if weak and not measurable:
        notes.append(f"uses unmeasured wording ({', '.join(weak)}); define a measurable criterion")
    if req.get("type") in ("business_goal", "business", "functional", "ux"):
        tech = [w for w in IMPLEMENTATION_TERMS if re.search(rf"\b{re.escape(w)}\b", req.get("description", "").lower())]
        if tech:
            notes.append(f"states implementation detail ({', '.join(tech)}); describe the need, not the design")
    modals = len(re.findall(r"\b(must|shall)\b", req.get("description", "").lower()))
    if modals > 1:
        notes.append("contains several 'must/shall' statements; it may combine unrelated requirements")
    if req.get("type") == "functional":
        if not req.get("actor"):
            notes.append("has no actor")
        if not req.get("trigger"):
            notes.append("has no trigger")
        if not req.get("permissions"):
            notes.append("has no permission rule (state who may and may not, or N/A with a reason)")
        if criteria and not ERROR_WORDS.search(criteria):
            notes.append("no acceptance criterion covers an error, denial or failure case")
    return notes


def check_g3(ctx: Context, g: GateResult) -> None:
    b = ctx.bundle
    kinds = {pr.kind_of(r["id"]) for r in b.requirements}
    for kind, label in (("GOAL", "business goal (GOAL)"), ("BR", "business requirement (BR)")):
        if kind not in kinds:
            g.error(f"No {label} is recorded.", "specification/business-requirements.md")
    if not kinds & set(pr.IMPLEMENTABLE_KINDS):
        g.error("No functional, non-functional, data, integration, security, UX or technical requirement is recorded.")
    titles: dict[str, str] = {}
    for req in b.requirements:
        rid, where = req["id"], req.get("source_path", "")
        if req.get("status") == "draft":
            g.warn(f"{rid} is still a draft; it cannot enter the specification until confirmed.", where)
            continue
        if req.get("status") not in vh.LIVE_STATUSES:
            continue
        missing = []
        if not req.get("description"):
            missing.append("description")
        if not req.get("rationale"):
            missing.append("rationale")
        if not req.get("evidence"):
            missing.append("evidence (SRC or DEC)")
        if not req.get("stakeholder"):
            missing.append("related stakeholder")
        if req.get("type") != "business_goal" and not req.get("source"):
            missing.append("source")
        if req.get("type") in vh.IMPLEMENTABLE | {"business"} and not req.get("acceptance_criteria"):
            missing.append("acceptance condition")
        if req.get("type") == "business_goal":
            measure = req.get("business_measure") or {}
            if not measure.get("measure"):
                missing.append("measure")
        if missing:
            g.error(f"{rid} is {req['status']} but has no {', '.join(missing)}.", where)
        if req.get("confidence") != "confirmed":
            g.error(f"{rid} is {req['status']} but its confidence is {req.get('confidence') or 'unclassified'}; "
                    f"only CONFIRMED information can be a confirmed requirement.", where)
        if req.get("priority") in (None, "unspecified"):
            g.warn(f"{rid} has no priority yet.", where)
        for note in lint_requirement(req):
            g.warn(f"{rid} {note}.", where)
        key = re.sub(r"\W+", " ", req.get("title", "").lower()).strip()
        if key in titles:
            g.warn(f"{rid} has the same title as {titles[key]}; check for duplication.", where)
        titles.setdefault(key, rid)
    blocker_issues(ctx, g, "requirements are relied on")
    review_issues(g, read_review(ctx.project, pr.REQUIREMENT_REVIEW_FILE), "requirement quality review", ctx.project)


def has_content(record: pr.Record, *names: str) -> bool:
    value = record.field(*names)
    if value is not None and pr.clean(value):
        return True
    section = record.section(*names)
    return bool(section and not section.is_empty())


def check_g4(ctx: Context, g: GateResult) -> None:
    b = ctx.bundle
    process_path = ctx.project / pr.PROCESS_FILE
    if not process_path.is_file() or not b.processes:
        g.error(f"{pr.PROCESS_FILE} has no process record (PROC-###).")
    else:
        required = [("perspective",), ("actor", "actors"), ("trigger",), ("preconditions", "precondition"),
                    ("main flow",), ("alternative flow", "alternative flows"), ("exceptions",), ("result", "outcome"),
                    ("business rules",), ("data involved",)]
        for record in pr.read_records(process_path, ("PROC",)):
            missing = [names[0] for names in required if not has_content(record, *names)]
            if missing:
                g.error(f"{record.id} does not state: {', '.join(missing)} (write 'None — reason' where nothing applies).",
                        f"{pr.PROCESS_FILE}:{record.line}")
        replaced = {p.get("compares_to") for p in b.processes if p.get("compares_to")}
        for proc in b.processes:
            if proc.get("perspective") == "as_is" and proc["id"] not in replaced:
                g.warn(f"AS-IS process {proc['id']} has no TO-BE process that replaces it.", proc.get("source_path", ""))
            if proc.get("confidence") in ("assumption", "unknown"):
                g.warn(f"{proc['id']} is modelled on {proc['confidence']} information.", proc.get("source_path", ""))
        covered = {r for p in b.processes for r in p.get("related_requirements") or []}
        for req in ctx.live:
            if req.get("type") == "functional" and req.get("scope") in (None, "in_scope") and req["id"] not in covered:
                g.warn(f"{req['id']} is not part of any modelled workflow.", req.get("source_path", ""))
    domain_path = ctx.project / pr.DOMAIN_FILE
    if not domain_path.is_file() or not b.entities:
        g.error(f"{pr.DOMAIN_FILE} has no business entity (ENT-###).")
    else:
        required = [("purpose",), ("key attributes",), ("relationships",), ("lifecycle states", "states"),
                    ("ownership", "owner"), ("permissions",)]
        for record in pr.read_records(domain_path, ("ENT",)):
            missing = [names[0] for names in required if not has_content(record, *names)]
            if missing:
                g.error(f"{record.id} does not state: {', '.join(missing)}.", f"{pr.DOMAIN_FILE}:{record.line}")
        for ent in b.entities:
            if ent.get("confidence") in ("assumption", "unknown"):
                g.warn(f"{ent['id']} is modelled on {ent['confidence']} information.", ent.get("source_path", ""))


def check_g5(ctx: Context, g: GateResult) -> None:
    b = ctx.bundle
    if not b.modules:
        g.error(f"{pr.SOLUTION_FILE} has no module register entry (MOD-###).")
    for module in b.modules:
        if not module.get("type"):
            g.error(f"{module['id']} has no type (user-facing, administration, integration, external service, reporting, notification, platform, other).",
                    pr.SOLUTION_FILE)
        if not module.get("purpose"):
            g.error(f"{module['id']} has no purpose.", pr.SOLUTION_FILE)
    for req in ctx.live:
        where = req.get("source_path", "")
        if req.get("scope") is None:
            g.error(f"{req['id']} has no scope classification (IN SCOPE, OUT OF SCOPE, FUTURE, PENDING DECISION).", where)
        if req.get("type") in vh.IMPLEMENTABLE and req.get("scope") in (None, "in_scope") and not req.get("related_modules"):
            g.error(f"{req['id']} is not mapped to any module.", where)
    if not ctx.exists(pr.SCOPE_FILE):
        g.error(f"{pr.SCOPE_FILE} does not exist; record the scope register.")
    open_targets = {t for q in b.questions if not q.get("resolved") for t in q.get("affected_ids") or []}
    pending = [r for r in ctx.live if r.get("scope") == "pending_decision"] + \
              [s for s in b.scope_items if s.get("classification") == "pending_decision"]
    for item in pending:
        if item["id"] not in open_targets:
            g.error(f"{item['id']} is PENDING DECISION but no open question names it.", item.get("source_path", pr.SCOPE_FILE))
    for item in b.scope_items:
        if item.get("classification") in ("out_of_scope", "future") and not item.get("rationale"):
            g.warn(f"{item['id']} is {item['classification']} without a rationale.", pr.SCOPE_FILE)


def open_blockers(ctx: Context, question_ids: list[str]) -> list[dict]:
    """Open BLOCKER questions among ``question_ids`` that are not contained by scope."""
    out = []
    for q_id in question_ids:
        q = ctx.bundle.q_by_id.get(q_id)
        if q and q.get("blocking") and not q.get("resolved") and not ctx.quarantined(q):
            out.append(q)
    return out


def critical_decisions(ctx: Context) -> list[str]:
    """Proposed ADRs and undecided concerns whose deciding question is an open BLOCKER."""
    b = ctx.bundle
    out = []
    for adr in b.adrs:
        if adr.get("status") == "proposed" and any(
                b.q_by_id.get(q, {}).get("blocking") and not b.q_by_id.get(q, {}).get("resolved")
                for q in adr.get("decision_questions") or []):
            out.append(adr["id"])
    for row in b.coverage:
        if row.get("status") == "decision_required" and any(
                b.q_by_id.get(q, {}).get("blocking") and not b.q_by_id.get(q, {}).get("resolved")
                for q in row.get("question_ids") or []):
            out.append(row["concern"])
    return out


def detected_conflicts(ctx: Context) -> list:
    return [f for f in ctx.findings if f.code in CONFLICT_CODES]


def check_coverage(ctx: Context, g: GateResult) -> None:
    b = ctx.bundle
    where = pr.ARCHITECTURE_REGISTER_FILE
    if not b.coverage:
        g.error("The architecture register has no coverage table whose first column is 'Concern'; "
                "every major architecture question must be identified.", where)
        return
    rows = {pr.norm_key(row["concern"]): row for row in b.coverage}
    for concern in ARCH_CONCERNS:
        if pr.norm_key(concern) not in rows:
            g.error(f"Architecture concern '{concern}' is missing from the coverage table.", where)
    for row in b.coverage:
        concern, status = row["concern"], row.get("status")
        adrs = [b.adr_by_id[a] for a in row.get("adr_ids") or [] if a in b.adr_by_id]
        questions = [b.q_by_id[q] for q in row.get("question_ids") or [] if q in b.q_by_id]
        if status in (None, "not_assessed"):
            g.error(f"Architecture concern '{concern}' has not been assessed; classify it DECIDED, PROPOSED, "
                    f"DECISION REQUIRED, DELEGATED or NOT APPLICABLE.", where)
        elif status == "decided":
            if not any(a.get("status") == "accepted" for a in adrs):
                g.error(f"Architecture concern '{concern}' is DECIDED but names no ACCEPTED ADR.", where)
            for adr in adrs:
                if adr.get("status") in vh.INACTIVE_ADR:
                    g.error(f"Architecture concern '{concern}' lists {adr['id']}, which is {adr['status'].upper()}; list only "
                            f"the decisions that govern now (the ADR register keeps the history).", where)
        elif status == "proposed":
            if not any(a.get("status") == "proposed" for a in adrs):
                g.error(f"Architecture concern '{concern}' is PROPOSED but names no PROPOSED ADR.", where)
        elif status == "decision_required":
            if not questions:
                g.error(f"ARCHITECTURE DECISION REQUIRED: '{concern}' names no open question (Q-###); an undecided "
                        f"architecture choice needs a question with an owner and a priority.", where)
            elif all(q.get("resolved") for q in questions):
                g.warn(f"'{concern}' is still DECISION REQUIRED although its question is answered; record the decision as an ADR.", where)
            else:
                blocking = open_blockers(ctx, row.get("question_ids") or [])
                label = ", ".join(f"{q['id']} {q.get('priority')}" for q in questions if not q.get("resolved"))
                if blocking:
                    g.error(f"ARCHITECTURE DECISION REQUIRED: '{concern}' is undecided and {', '.join(q['id'] for q in blocking)} "
                            f"is a BLOCKER that affects in-scope work. Decide it, or classify what it affects as PENDING "
                            f"DECISION, FUTURE or OUT OF SCOPE.", where)
                else:
                    g.warn(f"ARCHITECTURE DECISION REQUIRED: '{concern}' is undecided ({label}); do not plan work that "
                           f"depends on it as if it were decided.", where)
        elif status in ("delegated", "not_applicable"):
            label = "DELEGATED" if status == "delegated" else "NOT APPLICABLE"
            if not row.get("rationale"):
                g.error(f"Architecture concern '{concern}' is {label} without a reason.", where)
            elif not row.get("evidence"):
                g.error(f"Architecture concern '{concern}' is {label} without evidence (SRC-### or DEC-###).", where)


def check_adr_register(ctx: Context, g: GateResult) -> None:
    """The ADR register lists every ADR ID ever assigned, and agrees with the ADR files."""
    b = ctx.bundle
    path = ctx.project / pr.ARCHITECTURE_REGISTER_FILE
    table = first_table(path, "ADR ID")
    if table is None:
        g.error("The architecture register has no ADR register table whose first column is 'ADR ID'.", pr.ARCHITECTURE_REGISTER_FILE)
        return
    rows: dict[str, tuple[int, dict]] = {}
    for line, row in table.dict_rows():
        aid = pr.clean(cell(row, "adr id"))
        if not pr.FULL_ID_RE["ADR"].match(aid):
            continue
        loc = f"{pr.ARCHITECTURE_REGISTER_FILE}:{line}"
        if aid in rows:
            g.error(f"{aid} appears twice in the ADR register; an ADR ID names one decision and is never reused.", loc)
            continue
        rows[aid] = (line, row)
    for adr in b.adrs:
        if adr["id"] not in rows:
            g.error(f"{adr['id']} is not in the ADR register; list every ADR ID ever assigned so that none is reused.",
                    pr.ARCHITECTURE_REGISTER_FILE)
    for aid, (line, row) in sorted(rows.items(), key=lambda kv: pr.natural_key(kv[0])):
        loc = f"{pr.ARCHITECTURE_REGISTER_FILE}:{line}"
        adr = b.adr_by_id.get(aid)
        if adr is None:
            g.error(f"{aid} is registered but has no record in architecture/. ADR records are never deleted: restore it "
                    f"and mark it REJECTED or DEPRECATED; never reuse the ID.", loc)
            continue
        checks = [
            ("title", pr.clean(cell(row, "title")), adr.get("title") or ""),
            ("status", gh.norm_enum(cell(row, "status")).lower(), adr.get("status") or ""),
            ("date", pr.clean(cell(row, "date")), adr.get("date") or ""),
        ]
        if "superseded by" in row:
            checks.append(("superseded by", gh.first_id(cell(row, "superseded by"), "ADR") or "", adr.get("superseded_by") or ""))
        for column, listed, actual in checks:
            if column == "date" and (not listed or pr.has_tbd(listed) or pr.is_none(listed)) and not actual:
                continue
            if column in row and listed != actual:
                g.error(f"{aid} {column} is {listed or 'blank'!r} in the ADR register but {actual or 'blank'!r} in its record; "
                        f"the ADR file is canonical.", loc)


def check_architecture_review(ctx: Context, g: GateResult) -> None:
    b = ctx.bundle
    review = read_review(ctx.project, pr.ARCHITECTURE_REVIEW_FILE)
    review_issues(g, review, "architecture review", ctx.project)
    if review is None:
        return
    where = pr.rel(ctx.project, review.path)
    table = first_table(review.path, "ADR ID")
    reviewed = {}
    if table is not None:
        for line, row in table.dict_rows():
            aid = pr.clean(cell(row, "adr id"))
            if pr.FULL_ID_RE["ADR"].match(aid):
                reviewed[aid] = (line, gh.norm_enum(cell(row, "status reviewed", "status")).lower())
    for adr in b.adrs:
        entry = reviewed.get(adr["id"])
        if entry is None:
            g.error(f"The architecture review does not cover {adr['id']}; review every ADR in its current status.", where)
        elif entry[1] != adr.get("status"):
            g.error(f"The architecture review reviewed {adr['id']} as {entry[1].upper() or 'blank'}; it is now "
                    f"{str(adr.get('status')).upper()}. Review the current state.", f"{where}:{entry[0]}")
    summary = vh.architecture_summary(b.adrs, b.coverage)
    expected = {
        "Active ADRs": summary["accepted"], "Proposed ADRs": summary["proposed"],
        "Superseded ADRs": summary["superseded"], "Rejected ADRs": summary["rejected"],
        "Deprecated ADRs": summary["deprecated"], "Unresolved critical decisions": len(critical_decisions(ctx)),
        "Conflicts": len(detected_conflicts(ctx)),
    }
    for label, actual in expected.items():
        stated = review.fields.get(pr.norm_key(label))
        if stated is None:
            g.error(f"The architecture review does not state '{label}'.", where)
            continue
        number = re.match(r"\s*(\d+)", stated)
        if not number or int(number.group(1)) != actual:
            g.error(f"The architecture review states {label}: {stated or 'blank'}; the records show {actual}. "
                    f"Update the review from reports/architecture-report.md.", where)
    overall = gh.norm_enum(review.fields.get("overall", "")).upper()
    if overall not in (PASS, WARN, FAIL):
        g.error(f"The architecture review's Overall is {overall or 'blank'}; use PASS, PASS WITH WARNINGS or FAIL.", where)
    elif overall == FAIL:
        g.error("The architecture review concludes FAIL.", where)

    for line, row in review.findings:
        if gh.norm_enum(cell(row, "type")).upper() != "ARCHITECTURE CONFLICT":
            continue
        loc = f"{where}:{line}"
        fid = cell(row, "finding id")
        severity = gh.norm_enum(cell(row, "severity")).upper()
        status = gh.norm_enum(cell(row, "status")).upper()
        conflicting = pr.extract_ids(cell(row, "adr"), ("ADR",))
        resolution = cell(row, "resolution")
        if not conflicting:
            g.error(f"{fid} is an ARCHITECTURE CONFLICT but names no ADR in the 'ADR' column.", loc)
        if status not in ("RESOLVED", "WITHDRAWN") and severity not in ("CRITICAL", "MAJOR"):
            g.error(f"{fid} is an unresolved ARCHITECTURE CONFLICT recorded as {severity or 'blank'}; an open conflict is "
                    f"CRITICAL or MAJOR until it is resolved or withdrawn.", loc)
        if status == "WITHDRAWN" and not resolution:
            g.error(f"{fid} is WITHDRAWN without the reason it is not a conflict.", loc)
        if status != "RESOLVED":
            continue
        kind = gh.norm_enum(resolution).upper()
        if kind not in CONFLICT_RESOLUTIONS:
            g.error(f"{fid} is RESOLVED as '{resolution or 'blank'}'; resolve an architecture conflict by CHANGE PROPOSAL, "
                    f"NEW ADR or SUPERSEDE ADR.", loc)
            continue
        if kind == "CHANGE PROPOSAL":
            continue
        new = [a for a in pr.extract_ids(resolution, ("ADR",)) if a not in conflicting]
        if not new:
            g.error(f"{fid} is resolved by {kind} but names no new ADR in its resolution.", loc)
        for new_id in new:
            adr = b.adr_by_id.get(new_id)
            if adr is None:
                g.error(f"{fid} is resolved by {new_id}, which does not exist.", loc)
            elif adr.get("status") != "accepted":
                g.error(f"{fid} is resolved by {new_id}, which is {str(adr.get('status')).upper()}; the conflict stays open "
                        f"until {new_id} is ACCEPTED by its decision owner.", loc)
        if kind == "SUPERSEDE ADR":
            for old_id in conflicting:
                old = b.adr_by_id.get(old_id, {})
                if old.get("status") != "superseded" or old.get("superseded_by") not in new:
                    g.error(f"{fid} says {old_id} was superseded, but {old_id} is {str(old.get('status')).upper()} "
                            f"with 'Superseded by' {old.get('superseded_by') or 'None'}.", loc)


def reviewed_conflict(ctx: Context, item_id: str, adr_id: str) -> bool:
    """Whether the architecture review records a conflict between an item and an ADR."""
    for row in ctx.conflict_findings:
        if adr_id in pr.extract_ids(cell(row, "adr"), ("ADR",)) and item_id in pr.extract_ids(cell(row, "affected ids")):
            return True
    return False


def check_g6(ctx: Context, g: GateResult) -> None:
    b = ctx.bundle
    for rel, label in ((pr.ARCHITECTURE_REGISTER_FILE, "the architecture register (templates/27)"),
                       (pr.PRINCIPLES_FILE, "the architecture principles (templates/38)")):
        if not ctx.exists(rel):
            g.error(f"{rel} does not exist; record {label}.")
    if not ctx.exists(pr.ARCHITECTURE_README_FILE):
        g.warn(f"{pr.ARCHITECTURE_README_FILE} does not exist; copy templates/40 so readers know how decisions are governed.")
    if ctx.exists(pr.ARCHITECTURE_REGISTER_FILE):
        check_coverage(ctx, g)
        check_adr_register(ctx, g)

    for adr in b.adrs:
        if adr.get("status") != "proposed":
            continue
        where = adr.get("source_path", "")
        blocking = open_blockers(ctx, adr.get("decision_questions") or [])
        if blocking:
            g.error(f"ARCHITECTURE DECISION REQUIRED: {adr['id']} ({adr.get('title')}) is unresolved and "
                    f"{', '.join(q['id'] for q in blocking)} is a BLOCKER that affects in-scope work. Obtain the decision, "
                    f"or classify what it affects as PENDING DECISION, FUTURE or OUT OF SCOPE.", where)
        else:
            questions = ", ".join(f"{q} {b.q_by_id.get(q, {}).get('priority') or ''}".strip()
                                  for q in adr.get("decision_questions") or []) or "no question"
            g.warn(f"{adr['id']} ({adr.get('title')}) is PROPOSED: the decision has not been made ({questions}); "
                   f"work bound by it cannot be READY.", where)

    if ctx.exists(pr.PRINCIPLES_FILE):
        if not b.principles:
            g.warn("No architecture principle is recorded; confirm that none has been stated rather than leaving it blank.",
                   pr.PRINCIPLES_FILE)
        live = [p for p in b.principles if p.get("status") != "retired"]
        if len(live) > 10:
            g.warn(f"{len(live)} principles are in force; keep principles few and meaningful, and record concrete choices as ADRs.",
                   pr.PRINCIPLES_FILE)
        for principle in b.principles:
            if principle.get("status") == "accepted" and not principle.get("evidence"):
                g.error(f"{principle['id']} is ACCEPTED without evidence (SRC-### or DEC-###); an unconfirmed principle is PROPOSED.",
                        pr.PRINCIPLES_FILE)
            elif principle.get("status") == "proposed":
                g.warn(f"{principle['id']} is PROPOSED: a recommendation until the decision authority accepts it.", pr.PRINCIPLES_FILE)

    for req in ctx.in_scope:
        if pr.kind_of(req["id"]) in ("TR", "IR") and not req.get("architecture_decisions"):
            g.warn(f"In-scope {req['id']} is linked to no ADR; confirm that no architecture decision governs it.",
                   req.get("source_path", ""))

    check_architecture_review(ctx, g)


def check_gc(ctx: Context, g: GateResult) -> None:
    """GC — Change impact reviewed. Continuous: every change is recorded, analysed, decided by a person,
    and resolved in the plan; nothing affected by it stays silently trusted."""
    b = ctx.bundle
    doc = b.changes_doc or {}
    baseline = doc.get("baseline") or {}
    records = b.changes
    if not baseline.get("exists"):
        if records:
            g.error(f"Change records exist but there is no baseline ({pr.BASELINE_FILE}) to verify them against. "
                    f"Record it with `python tools/analyze_change_impact.py projects/<project> --baseline`.", pr.BASELINE_FILE)
        elif b.spec_approved:
            g.warn(f"The specification is approved but no baseline ({pr.BASELINE_FILE}) has been recorded, so a change to an "
                   f"approved record cannot be detected. Run `python tools/analyze_change_impact.py projects/<project> --baseline`.",
                   pr.BASELINE_FILE)
    detected = {d["id"]: d for d in doc.get("detected_changes") or []}
    incorporated = set(baseline.get("incorporated_changes") or [])

    for entry in b.unrecorded:
        rid, where = entry["id"], entry.get("source_path", "")
        reach = f"; it reaches {len(entry.get('affected') or [])} record(s), now NEEDS_REVIEW" if entry.get("affected") else ""
        covering = [b.change_by_id.get(c, {}) for c in entry.get("covered_by") or []]
        rejected = [c["change_id"] for c in covering if c.get("status") == "REJECTED"]
        pending = [c["change_id"] for c in covering if c.get("status") in ("PROPOSED", "UNDER_ANALYSIS")]
        if rejected:
            g.error(f"{rid} was {entry['change']} although {', '.join(rejected)} was REJECTED; restore the approved state{reach}.", where)
        elif pending:
            g.error(f"{rid} was {entry['change']} before {', '.join(pending)} was approved; a proposed change does not alter "
                    f"the authoritative plan{reach}.", where)
        else:
            g.error(f"{rid} was {entry['change']} since the baseline without a change record. A meaningful change is never a "
                    f"text edit: record it as CHANGE-###, analyse it and have it approved{reach}.", where)

    for change in records:
        cid, where, status = change["change_id"], change.get("source_path", ""), change.get("status")
        if not change.get("change_type"):
            g.error(f"{cid} has no change type; use one of {', '.join(ci.CHANGE_TYPES)}.", where)
        if not change.get("changed_artifacts"):
            g.error(f"{cid} names no changed artifact.", where)
        if not change.get("reason"):
            g.error(f"{cid} does not state why the change is needed (*Reason*).", where)
        if not change.get("changed_by"):
            g.error(f"{cid} does not say who requested the change (*Changed by*).", where)
        if status in ci.DECIDED_STATUSES:
            approver = change.get("approved_by") or ""
            if not approver.strip() or pr.has_tbd(approver) or not change.get("approval_evidence"):
                g.error(f"{cid} is {status} but records no human decision: name *Approved by* and cite *Approval evidence* "
                        f"(DEC-### or SRC-###).", where)
        if status in ci.MARKING_STATUSES and not (change.get("previous_state") and change.get("new_state")):
            g.error(f"{cid} does not preserve history: state the *Previous state* and the *New state*.", where)
        declared, computed = change.get("declared_severity"), change.get("computed_severity")
        if declared and ci.SEVERITY_RANK[declared] < ci.SEVERITY_RANK[computed]:
            g.error(f"{cid} declares severity {declared}, below the computed {computed} ({'; '.join(change.get('severity_drivers') or [])}).",
                    where)
        if status == "SUPERSEDED" and not change.get("superseded_by"):
            g.error(f"{cid} is SUPERSEDED but names no successor change.", where)
        for risk in change.get("risk_impact") or []:
            register = b.risk_by_id.get(risk.get("risk")) if risk.get("risk") else None
            if risk.get("effect") == "NEW" and register is None:
                g.error(f"{cid} records a NEW risk that is not in the risk register; add it as RISK-###.", where)
            if risk.get("effect") == "RETIRED" and register is not None and register.get("status") != "CLOSED":
                g.warn(f"{cid} retires {risk['risk']}, which is still {register.get('status')} in the risk register.", where)

        unresolved = [a for a in change.get("affected") or [] if a.get("review_state") != "CURRENT"]
        label = ", ".join(f"{a['id']} {a['review_state']}" for a in unresolved[:8]) + (" …" if len(unresolved) > 8 else "")
        if status == "APPROVED":
            if unresolved and computed == "CRITICAL":
                g.error(f"CRITICAL impact of {cid} is unresolved: {label}.", where)
            elif unresolved:
                g.warn(f"{cid} is approved and {len(unresolved)} affected artifact(s) are still under review: {label}.", where)
            for q in change.get("decisions_required") or []:
                if not b.q_by_id.get(q, {}).get("resolved"):
                    g.warn(f"{cid} waits on the stakeholder decision {q}.", where)
        if status != "IMPLEMENTED_IN_PLAN":
            continue
        if unresolved:
            g.error(f"{cid} is IMPLEMENTED_IN_PLAN but affected artifacts are not current: {label}.", where)
        undisposed = [a["id"] for a in change.get("affected") or [] if a["level"] in ("DIRECT", "INDIRECT") and not a.get("resolution")]
        if undisposed:
            g.error(f"{cid} is IMPLEMENTED_IN_PLAN but does not record how {', '.join(undisposed)} were resolved.", where)
        done = {pr.norm_key(r["area"]): r for r in change.get("required_reviews") or []}
        for area in change.get("review_areas") or []:
            review = done.get(pr.norm_key(area["area"]))
            if review is None or review.get("result") == "PENDING":
                g.error(f"{cid} has not completed the required review '{area['area']}'.", where)
            elif review.get("result") == "N/A" and not review.get("evidence"):
                g.error(f"{cid} marks the review '{area['area']}' N/A without a reason.", where)
        if not change.get("new_work"):
            g.error(f"{cid} does not state the new work it requires (*New work required*; write 'None — reason').", where)
        if (change.get("roadmap") or {}).get("phases") and not change.get("roadmap_notes"):
            g.error(f"{cid} reaches {', '.join(change['roadmap']['phases'])} but records no *Roadmap impact*.", where)
        if computed in ("CRITICAL", "HIGH") and not change.get("risk_impact"):
            g.error(f"{cid} is {computed} but records no *Risk impact*; state which risks are new, increased, reduced or retired.", where)
        for q in change.get("decisions_required") or []:
            if not b.q_by_id.get(q, {}).get("resolved"):
                g.error(f"{cid} is IMPLEMENTED_IN_PLAN while the required stakeholder decision {q} is open.", where)
        if cid not in incorporated:
            for identifier in change.get("changed_artifacts") or []:
                if identifier not in detected:
                    g.error(f"{cid} is IMPLEMENTED_IN_PLAN but {identifier} is unchanged since the baseline.", where)
            for a in change.get("affected") or []:
                if a.get("resolution") in ci.EDITING_RESOLUTIONS and a["id"] not in detected:
                    g.error(f"{cid} records {a['id']} as {a['resolution']}, but {a['id']} is unchanged since the baseline.", where)

    for tid, state in sorted(b.artifact_state.items(), key=lambda kv: pr.natural_key(kv[0] or "")):
        task = b.task_by_id.get(tid)
        if task and task.get("status") == "READY":
            g.error(f"{tid} is READY but {state['state']} ({'; '.join(state.get('reasons') or [])}); its readiness is withdrawn "
                    f"until the change record dispositions it.", task.get("source_path", ""))

    if records or b.unrecorded:
        # After a change the plan is validated again: contradictions it leaves behind are not accepted.
        for finding in ctx.findings:
            unreviewed = finding.code == "ARCHITECTURE_CONFLICT" and not reviewed_conflict(
                ctx, next(iter(pr.extract_ids(finding.message)), ""), next(iter(pr.extract_ids(finding.message, ("ADR",))), ""))
            if (finding.code in POST_CHANGE_CODES and finding.severity == "error") or unreviewed:
                g.error(f"After the change: {finding.code}: {finding.message}", finding.location)
        live = {r["id"] for r in ctx.live if r.get("scope") in (None, "in_scope")}
        for feature in b.features:
            if feature.get("scope") == "in_scope" and feature.get("requirement_ids") and not live & set(feature["requirement_ids"]):
                g.warn(f"{feature['id']} no longer maps to any live, in-scope requirement.", feature.get("source_path", ""))
        for task in b.tasks:
            feature = b.feat_by_id.get(task.get("feature"))
            if task.get("status") != "CANCELLED" and (feature is None or feature.get("scope") == "out_of_scope"):
                g.warn(f"{task['id']} no longer maps to an active, in-scope feature.", task.get("source_path", ""))
        for adr in b.adrs:
            consumers = [e for e in (b.traceability.get("architecture") or []) if e.get("adr_id") == adr["id"]]
            reach = consumers[0] if consumers else {}
            if adr.get("status") == "accepted" and not (reach.get("requirement_ids") or reach.get("feature_ids") or reach.get("task_ids")):
                g.warn(f"Accepted {adr['id']} no longer has an active consumer (no requirement, feature or task).", adr.get("source_path", ""))
        for phase in b.phases:
            active = [t for t in phase.get("task_ids") or [] if b.task_by_id.get(t, {}).get("status") != "CANCELLED"]
            if phase.get("task_ids") is not None and not active:
                g.warn(f"{phase['id']} schedules no active task; the roadmap item may reference removed scope.", phase.get("source_path", ""))


def check_g7(ctx: Context, g: GateResult) -> None:
    path = ctx.project / pr.SPECIFICATION_FILE
    if not path.is_file():
        g.error(f"{pr.SPECIFICATION_FILE} does not exist.")
        return
    text = path.read_text(encoding="utf-8")
    present = {int(m.group(1)) for m in re.finditer(r"^##\s+(\d+)\.", text, re.MULTILINE)}
    missing = [str(n) for n in range(1, 27) if n not in present]
    if missing:
        g.error(f"The specification is missing section(s) {', '.join(missing)} of 26.", pr.SPECIFICATION_FILE)
    mentioned = set(pr.extract_ids(text))
    for identifier in sorted(mentioned, key=pr.natural_key):
        kind = pr.kind_of(identifier)
        if kind in (*pr.REQUIREMENT_KINDS, "MOD", "ENT", "PROC", "ADR", "DEC", "Q", "RISK", "SCOPE") \
                and ctx.bundle.known(identifier) is False:
            g.error(f"The specification mentions {identifier}, which no record defines; the specification must not introduce requirements or decisions.",
                    pr.SPECIFICATION_FILE)
    for req in ctx.in_scope:
        if req["id"] not in mentioned:
            g.warn(f"In-scope {req['id']} is not referenced by the specification.", pr.SPECIFICATION_FILE)
    for adr in ctx.bundle.adrs:
        if adr.get("status") == "accepted" and adr["id"] not in mentioned:
            g.warn(f"Accepted {adr['id']} is not referenced by the specification; state the architecture constraints the plan relies on.",
                   pr.SPECIFICATION_FILE)
    for number, line in enumerate(text.splitlines(), start=1):
        for q_id in re.findall(r"TBD \((Q-[0-9]{3,})\)", line):
            q = ctx.bundle.q_by_id.get(q_id)
            if q and q.get("resolved"):
                g.warn(f"'TBD ({q_id})' remains although {q_id} is {q['status']}; carry the answer into the specification.",
                       f"{pr.SPECIFICATION_FILE}:{number}")
        if re.search(r"\bTBD\b(?! \(Q-)", line):
            g.warn("TBD without a question reference; every unknown needs a Q-###.", f"{pr.SPECIFICATION_FILE}:{number}")


def check_gr(ctx: Context, g: GateResult) -> None:
    """GR — Specification reviewed. The independent review is complete, current and coherent, and no
    CRITICAL or MAJOR finding is unresolved. tools/specification_review.py does the verification."""
    for issue in ctx.spec_review.issues:
        (g.error if issue.level == "error" else g.warn)(issue.message, issue.location)
    if ctx.spec_review.exists and ctx.review_summary is None:
        g.warn("project-state.md does not expose the specification review summary (a table whose first column is "
               "'Review measure', templates/00).", pr.STATE_FILE)


def review_summary_violations(ctx: Context) -> list[Issue]:
    """project-state.md may not state a better review than the one the records show."""
    if ctx.review_summary is None:
        return []
    out = []
    for label, actual in ctx.spec_review.summary_rows():
        stated = ctx.review_summary.get(pr.norm_key(label))
        if stated is None:
            continue
        value, line = stated
        count = sr.number(value)
        normal = sr.result_label(value) if label == "Specification review" else str(count) if count is not None else value
        if normal != actual:
            out.append(Issue("error", f"project-state.md states {label}: {value or 'blank'}; the specification review shows "
                                      f"{actual}. Copy it from tools/specification_review.py or the gate report.",
                             f"{pr.STATE_FILE}:{line}"))
    return out


def check_g8(ctx: Context, g: GateResult) -> None:
    """G8 — Specification ready. The findings of the review are resolved (GR passes) and the reviewed version is
    approved by a person, after the review."""
    b = ctx.bundle
    review = ctx.spec_review
    approval = b.project.get("specification_approval") or {}
    if b.spec_approved and review.exists:
        approved_on, version = approval.get("approved_on") or "", approval.get("specification_version")
        cycles = review.history + ([review.current_cycle()] if review.cycle else [])
        passing = [c for c in cycles if c.version == version and c.result in (sr.PASS, sr.WARN) and c.date]
        if not sr.ISO_DATE.match(approved_on):
            g.warn(f"The approval date {approved_on or 'blank'} is not YYYY-MM-DD, so it cannot be shown to follow the "
                   f"independent review.", pr.STATE_FILE)
        elif not any(c.date <= approved_on for c in passing):
            g.error(f"Specification version {version} was approved on {approved_on}, but no passing independent review of "
                    f"that version precedes it. Approval follows the review; it never replaces it.", pr.STATE_FILE)
    if not ctx.bundle.spec_approved:
        g.error(f"The specification is {ctx.bundle.project.get('specification_status')}, not APPROVED with an approval record.",
                pr.STATE_FILE)
    for req in ctx.in_scope:
        if req.get("status") != "approved":
            g.error(f"In-scope {req['id']} is {req['status']}, not approved.", req.get("source_path", ""))
    blocker_issues(ctx, g, "the specification is approved")
    for adr in ctx.bundle.adrs:
        if adr.get("status") == "proposed":
            g.warn(f"{adr['id']} is still PROPOSED at approval; tasks bound by it cannot be READY until it is accepted.",
                   adr.get("source_path", ""))
    for asm in ctx.bundle.assumptions:
        if asm.get("status") == "OPEN":
            g.warn(f"Assumption {asm['id']} is still open: {asm.get('statement')}", "discovery/assumptions.md")


def check_g9(ctx: Context, g: GateResult) -> None:
    b = ctx.bundle
    if not b.epics or not b.features or not b.tasks:
        g.error("The backlog needs at least one epic, feature and task.", pr.BACKLOG_FILE)
    for feature in b.features:
        if feature.get("scope") is None:
            g.error(f"{feature['id']} has no scope classification.", feature.get("source_path", ""))
        if feature.get("scope") == "in_scope":
            pending = [link["id"] for link in feature.get("architecture_decisions") or [] if link.get("status") == "proposed"]
            if pending:
                g.warn(f"{feature['id']} is bound by proposed {', '.join(pending)}; its tasks cannot be READY until the decision is accepted.",
                       feature.get("source_path", ""))
    explained = {r for f in b.features if f.get("no_tasks_reason") for r in f.get("requirement_ids") or []}
    for req in ctx.in_scope:
        if req.get("type") not in vh.IMPLEMENTABLE:
            continue
        if not any(req["id"] in (f.get("requirement_ids") or []) for f in b.features):
            g.error(f"In-scope {req['id']} is not delivered by any feature.", req.get("source_path", ""))
        if req["id"] not in explained and not any(req["id"] in (t.get("source_requirements") or []) for t in b.tasks
                                                  if t.get("status") != "CANCELLED"):
            g.error(f"In-scope {req['id']} is not implemented by any task.", req.get("source_path", ""))
    for feature in b.features:
        if feature.get("scope") == "in_scope" and feature.get("status") != "CANCELLED" and not feature.get("task_ids"):
            if feature.get("no_tasks_reason"):
                g.warn(f"{feature['id']} has no task: {feature['no_tasks_reason']}", feature.get("source_path", ""))
            else:
                g.error(f"In-scope {feature['id']} has no task and records no reason why none is needed ('No tasks reason': "
                        f"already implemented, documentation only, external vendor responsibility, no implementation required).",
                        feature.get("source_path", ""))


def check_gb(ctx: Context, g: GateResult) -> None:
    """GB — Backlog ready. Every READY task has earned READY, and at least a valid subset of the backlog is ready;
    nothing that would make that subset unsafe (a cycle, an open conflict, a serious finding, broken traceability,
    unapproved scope) remains."""
    b = ctx.bundle
    doc = b.backlog_readiness or {}
    if not b.tasks or not doc:
        g.error("The backlog has no task; nothing can be ready.", pr.BACKLOG_FILE)
        return
    v, s = doc["validation"], doc["summary"]
    active = [t for t in doc["tasks"] if t["scope"] == "in_scope" and t["status"] != "CANCELLED"]
    if v["dependency_cycles"]:
        g.error(f"{v['dependency_cycles']} dependency cycle(s): no execution sequence exists until they are resolved.",
                pr.BACKLOG_FILE)
    if not (v["specification_approved"] and v["specification_review_passed"]):
        g.error("Approved scope is missing: the specification is not approved, or its independent review does not pass "
                "for the current version.", pr.STATE_FILE)
    if v["unresolved_critical_findings"]:
        g.error(f"{v['unresolved_critical_findings']} CRITICAL specification review finding(s) are unresolved.",
                pr.SPECIFICATION_REVIEW_FILE)
    for fid in v["unresolved_major_findings_affecting_backlog"]:
        g.error(f"Specification review finding {fid} is unresolved and affects active backlog items.", pr.SPECIFICATION_REVIEW_FILE)
    for task in active:
        if "architecture_conflicts_clear" in task["failed_checks"]:
            conflict = next((f for f in task["failures"] if "ARCHITECTURE CONFLICT" in f), "")
            g.error(f"{task['id']} has an unresolved architecture conflict. {conflict}", pr.ARCHITECTURE_REVIEW_FILE)
    for issue in v["traceability_issues"]:
        g.error(f"Traceability: {issue}", pr.BACKLOG_FILE)
    if doc["status"] == "NOT_READY":
        g.error("No in-scope task is READY and passes the Definition of Ready: nothing can be handed to implementation.",
                pr.BACKLOG_FILE)
    revision_issues(ctx, g)
    if doc["status"] == "PARTIALLY_READY":
        g.warn(f"The backlog is PARTIALLY READY: {s['ready_valid']} of {s['active']} active task(s) are ready "
               f"({s['ready_percentage']}%). The rest stays visibly unresolved.", br.REPORT_FILE)
    for task in active:
        if task["status"] != "READY" and task["result"] == "FAIL":
            g.warn(f"{task['id']} is {task['status']} (the checks point to {task['recommended_status']}): {task['failures'][0]}",
                   b.task_by_id.get(task["id"], {}).get("source_path", ""))
    for tid in s["meets_definition_of_ready_not_marked_ready"]:
        g.warn(f"{tid} passes the Definition of Ready but is not READY; mark it READY once validated, with a readiness "
               f"history entry.", b.task_by_id.get(tid, {}).get("source_path", ""))
    for flag in doc["flags"]:
        g.warn(f"{flag['kind']}: {flag['message']}", b.task_by_id.get(flag["task_ids"][0], {}).get("source_path", ""))


def revision_issues(ctx: Context, g: GateResult) -> None:
    """A task whose definition changed since the baseline is a new revision of it, not the same task."""
    baseline = ci.load_baseline(ctx.project) or {}
    before = baseline.get("records") or {}
    detected = {d["id"]: d for d in (ctx.bundle.changes_doc or {}).get("detected_changes") or []}
    for task in ctx.bundle.tasks:
        entry, base = detected.get(task["id"]), before.get(task["id"])
        if not entry or not base or entry.get("change") != "modified":
            continue
        match = re.search(r"^\|\s*Revision\s*\|\s*(\d+)", base.get("text") or "", re.MULTILINE | re.IGNORECASE)
        previous = int(match.group(1)) if match else 1
        if task.get("revision", 1) <= previous:
            g.error(f"{task['id']} changed materially since the baseline but is still revision {task.get('revision', 1)}; "
                    f"increment its Revision (baseline: {previous}) so the changed task is not mistaken for the validated one.",
                    task.get("source_path", ""))


def check_g10(ctx: Context, g: GateResult) -> None:
    b = ctx.bundle
    if not b.project.get("priority_scheme"):
        g.error("project-state.md declares no 'Priority scheme' (Levels or MoSCoW).", pr.STATE_FILE)
    items = [(r["id"], r) for r in ctx.in_scope] + \
            [(x["id"], x) for x in b.features + b.tasks if x.get("scope") == "in_scope"]
    unprioritised = [i for i, x in items if x.get("priority") in (None, "unspecified")]
    if unprioritised:
        g.error(f"In-scope items without a priority: {', '.join(unprioritised)}.")
    proposed = [r["id"] for r in ctx.in_scope if not r.get("priority_confirmed") and r.get("priority") not in (None, "unspecified")]
    if proposed:
        g.warn(f"Priorities still proposed, not confirmed: {', '.join(proposed)}.")
    for task in b.tasks:
        if task.get("scope") == "in_scope" and not task.get("dependencies_reviewed"):
            g.error(f"{task['id']} has not had its dependencies reviewed ('Blocked By' is blank or TBD).", task.get("source_path", ""))
    for dep in b.dependencies:
        users = [x["id"] for x in b.features + b.tasks if dep["id"] in (x.get("external_dependencies") or [])
                 and x.get("scope") == "in_scope"]
        if users and dep.get("status") != "AVAILABLE":
            g.warn(f"External dependency {dep['id']} is {dep['status']} and in-scope work depends on it: {', '.join(users)}.",
                   "discovery/dependencies.md")


def check_g11(ctx: Context, g: GateResult) -> None:
    b = ctx.bundle
    if not b.phases:
        g.error("The roadmap has no phase (PHASE-##).", pr.BACKLOG_FILE)
    for phase in b.phases:
        where = phase.get("source_path", "")
        if not phase.get("objective"):
            g.error(f"{phase['id']} has no objective.", where)
        if not phase.get("exit_criteria"):
            g.error(f"{phase['id']} has no exit criteria.", where)
        if phase.get("date_basis") == "target":
            g.warn(f"{phase['id']} date {phase.get('date')} is a TARGET, not an estimate or commitment.", where)
    for task in b.tasks:
        if task.get("scope") == "in_scope" and task.get("status") != "CANCELLED" and not task.get("phase"):
            g.error(f"In-scope {task['id']} is not scheduled in any phase.", task.get("source_path", ""))
    if not b.risks:
        g.warn("The risk register is empty; confirm that no planning risk exists rather than leaving it blank.", "discovery/risks.md")
    for risk in b.risks:
        if risk.get("status") in ("OPEN", "MITIGATING", "OCCURRED") and "high" in (risk.get("impact"), risk.get("probability")):
            if not risk.get("mitigation") or not risk.get("owner"):
                g.error(f"High risk {risk['id']} has no {'mitigation' if not risk.get('mitigation') else 'owner'}.", "discovery/risks.md")


def check_g12(ctx: Context, g: GateResult) -> None:
    review_issues(g, read_review(ctx.project, pr.FINAL_REVIEW_FILE), "final planning review", ctx.project,
                  ctx.bundle.project.get("version"))
    for q in ctx.bundle.questions:
        if not q.get("resolved") and not q.get("blocking"):
            g.warn(f"{q.get('priority')} question {q['id']} remains open and must stay visible in the package: {q.get('question')}",
                   "discovery/open-questions.md")


def check_g13(ctx: Context, g: GateResult) -> None:
    summary = ctx.project / pr.PLANNING_SUMMARY_FILE
    if not summary.is_file():
        g.error(f"{pr.PLANNING_SUMMARY_FILE} does not exist.")
    else:
        text = summary.read_text(encoding="utf-8")
        sections = {}
        current = None
        for line in text.splitlines():
            heading = re.match(r"^#{2,3}\s+(.*?)\s*$", line)
            if heading:
                current = pr.norm_key(heading.group(1)).rstrip("?")
                sections[current] = []
            elif current is not None and line.strip() and not line.strip().startswith("<!--"):
                sections[current].append(line)
        for question in SUMMARY_QUESTIONS:
            body = sections.get(pr.norm_key(question).rstrip("?"))
            if body is None:
                g.error(f"The planning summary does not answer '{question}'.", pr.PLANNING_SUMMARY_FILE)
            elif not body:
                g.error(f"The planning summary's answer to '{question}' is empty.", pr.PLANNING_SUMMARY_FILE)
    for name in DELIVERABLES:
        rel = f"deliverables/{name}"
        if not ctx.exists(rel):
            g.error(f"{rel} does not exist.")
        elif not list((ctx.project / "deliverables" / "build").glob(f"*{Path(name).stem}*.docx")):
            g.error(f"{rel} has not been built to Word (deliverables/build/).")
    manifest = read_review(ctx.project, "deliverables/package-manifest.md")
    if manifest is not None:
        review_issues(g, manifest, "export verification in the package manifest", ctx.project)
    handoff = ctx.project / gh.OUTPUT_DIR
    if not (handoff / "project.json").is_file():
        g.error("The machine handoff has not been generated (tools/generate_handoff.py).")
    else:
        findings, bundle = vh.validate_files(vh.read_directory(handoff), ctx.project)
        for finding in findings.errors[:5]:
            g.error(f"Machine handoff: {finding.code} {finding.message}", finding.location)
        if len(findings.errors) > 5:
            g.error(f"Machine handoff: {len(findings.errors) - 5} more error(s); run tools/validate_handoff.py for the full list.",
                    "machine-handoff/")
        status = bundle.project.get("handoff_status")
        if status != "ready":
            g.error(f"The machine handoff status is {status}, not ready.", "machine-handoff/project.json")


CHECKS = {"G1": check_g1, "G2": check_g2, "G3": check_g3, "G4": check_g4, "G5": check_g5, "G6": check_g6,
          "G7": check_g7, "GR": check_gr, "G8": check_g8, "G9": check_g9, "G10": check_g10, "GB": check_gb, "G11": check_g11, "G12": check_g12,
          "G13": check_g13}


def gate_for(finding: vh.Finding) -> str:
    if finding.code in ARCH_ITEM_CODES:
        return "G9" if finding.location.startswith(("backlog/", "backlog.json", "tasks/")) else "G6"
    if finding.code in CODE_GATE:
        return CODE_GATE[finding.code]
    for prefix, gate in LOCATION_GATE:
        if finding.location.startswith(prefix):
            return gate
    return STEP_GATE.get(finding.step, "G12")


# --------------------------------------------------------------------------
# Evaluation
# --------------------------------------------------------------------------


def evaluate(project: Path) -> tuple[list[GateResult], list[Issue], Context]:
    ctx = Context(project)
    results = [GateResult(gate, name, stage, number) for number, stage, gate, name in STAGES]
    change_gate = GateResult(CHANGE_GATE[0], CHANGE_GATE[1], CHANGE_GATE[2], 0)
    by_gate = {r.gate: r for r in results + [change_gate]}
    for result in results:
        CHECKS[result.gate](ctx, result)
    check_gc(ctx, change_gate)
    seen: set[tuple] = set()
    for finding in ctx.findings:
        if finding.code in IGNORE:
            continue
        key = (finding.code, finding.message, finding.location)
        if key in seen:
            continue
        seen.add(key)
        target = by_gate[gate_for(finding)]
        level = "error" if finding.severity == "error" or finding.code in ESCALATE else "warning"
        target.issues.append(Issue(level, f"{finding.code}: {finding.message}", finding.location))
        if finding.code == "ARCHITECTURE_CONFLICT":
            # A possible conflict with an accepted decision is never accepted silently: it is either
            # recorded and dispositioned in the architecture review, or the gate fails.
            ids = pr.extract_ids(finding.message)
            item = ids[0] if ids else ""
            adr = next(iter(pr.extract_ids(finding.message, ("ADR",))), "")
            if not reviewed_conflict(ctx, item, adr):
                target.issues.append(Issue(
                    "error", f"ARCHITECTURE CONFLICT between {item} and {adr} is not recorded in "
                             f"{pr.ARCHITECTURE_REVIEW_FILE}; record it as a finding and resolve it by CHANGE PROPOSAL, "
                             f"NEW ADR or SUPERSEDE ADR, or withdraw it with the reason it is not a conflict.",
                    finding.location))
    # A plan with unresolved change impact is not validated: G12 and G13 require GC.
    if change_gate.result == FAIL:
        for gate in ("G12", "G13"):
            by_gate[gate].issues.insert(0, Issue("error", "Change-impact review (GC) fails; resolve the change impact before the plan is validated."))
    # A gate cannot pass on top of a failed earlier gate: later planning would rest on it.
    first_failure = None
    for result in results:
        if first_failure is not None:
            result.issues.insert(0, Issue("error", f"Prerequisite gate {first_failure} fails."))
        elif result.result == FAIL:
            first_failure = result.gate

    violations: list[Issue] = review_summary_violations(ctx)
    if ctx.current_stage is None:
        violations.append(Issue("error", f"project-state.md does not state 'Current stage' as a number 1-{LAST_STAGE}.", pr.STATE_FILE))
    else:
        for result in results:
            if result.number < ctx.current_stage and result.result == FAIL:
                violations.append(Issue(
                    "error",
                    f"Current stage is {ctx.current_stage}, but {result.gate} ({result.name}), the exit gate of stage "
                    f"{result.number}, fails. Return to stage {result.number}.", pr.STATE_FILE))
                break
    results.append(change_gate)
    for gate, (claimed, line) in sorted(ctx.claims.items(), key=lambda kv: GATE_NUMBER.get(kv[0], 99)):
        result = by_gate.get(gate)
        if result is None:
            continue
        if claimed in (PASS, WARN) and result.result == FAIL:
            violations.append(Issue("error", f"project-state.md claims {gate} {claimed}, but it fails.", f"{pr.STATE_FILE}:{line}"))
        elif claimed == PASS and result.result == WARN:
            violations.append(Issue("error", f"project-state.md claims {gate} PASS, but it passes only with warnings.",
                                    f"{pr.STATE_FILE}:{line}"))
    return results, violations, ctx


# --------------------------------------------------------------------------
# Reports
# --------------------------------------------------------------------------


def dependency_graph(ctx: Context) -> str:
    b = ctx.bundle
    node = lambda i: re.sub(r"[^A-Za-z0-9_]", "_", i)  # noqa: E731
    lines = ["# Dependency Graph", "",
             "<!-- GENERATED by tools/check_gates.py. Do not edit: change the records and regenerate. -->", "",
             "Arrows point from prerequisite to dependent. Features are boxes, tasks are rounded, external dependencies are "
             "hexagons and open BLOCKER questions are flagged. A thinking aid generated from the records, not a delivered diagram.",
             "", "```mermaid", "flowchart LR"]
    for feature in b.features:
        lines.append(f'  {node(feature["id"])}["{feature["id"]} {feature["title"]} ({feature.get("scope") or "unscoped"})"]')
        for dep in feature.get("dependencies") or []:
            lines.append(f"  {node(dep)} ==> {node(feature['id'])}")
        for ext in feature.get("external_dependencies") or []:
            lines.append(f"  {node(ext)} -.-> {node(feature['id'])}")
    for task in b.tasks:
        lines.append(f'  {node(task["id"])}("{task["id"]} {task["status"]}")')
        if task.get("feature"):
            lines.append(f"  {node(task['feature'])} --- {node(task['id'])}")
        for dep in task.get("dependencies") or []:
            lines.append(f"  {node(dep)} --> {node(task['id'])}")
        for ext in task.get("external_dependencies") or []:
            lines.append(f"  {node(ext)} -.-> {node(task['id'])}")
    for dep in b.dependencies:
        lines.append(f'  {node(dep["id"])}{{{{"{dep["id"]} {dep["status"]}"}}}}')
    for q in ctx.blockers:
        lines.append(f'  {node(q["id"])}[/"{q["id"]} BLOCKER"/]')
        for target in q.get("affected_ids") or []:
            if target in b.feat_by_id or target in b.task_by_id:
                lines.append(f"  {node(q['id'])} -.-x {node(target)}")
    lines += ["```", ""]
    order = b.backlog.get("sequencing", {}).get("order", [])
    lines += ["## Execution order", "", "| Sequence | Task | Status | Depends on |", "| --- | --- | --- | --- |"]
    for position, tid in enumerate(order, start=1):
        task = b.task_by_id.get(tid, {})
        lines.append(f"| {position} | {tid} | {task.get('status')} | {', '.join(task.get('dependencies') or []) or '—'} |")
    lines.append("")
    return "\n".join(lines)


def architecture_report(results: list[GateResult], ctx: Context, when: str) -> str:
    """The automated half of the architecture review: counts, decisions, coverage, conflicts, open decisions."""
    b = ctx.bundle
    g6 = next(r for r in results if r.gate == "G6")
    summary = vh.architecture_summary(b.adrs, b.coverage)
    conflicts = detected_conflicts(ctx)
    critical = critical_decisions(ctx)
    trace = {entry["adr_id"]: entry for entry in b.traceability.get("architecture", [])}
    md = gh.md_cell
    lines = ["# Architecture Report", "",
             "<!-- GENERATED by tools/check_gates.py. Do not edit: change the architecture records and regenerate. -->", "",
             f"Project: {b.project.get('name')} ({b.project.get('project_id')}) · Evaluated: {when}", "",
             "The automated half of the architecture review. Copy the summary into `reviews/architecture-review.md`; "
             "the judgement — whether accepted decisions are consistent and whether planning respects them — is recorded there.", "",
             "## Summary", "", "| Measure | Count |", "| --- | --- |",
             f"| Active ADRs | {summary['accepted']} |",
             f"| Proposed ADRs | {summary['proposed']} |",
             f"| Superseded ADRs | {summary['superseded']} |",
             f"| Rejected ADRs | {summary['rejected']} |",
             f"| Deprecated ADRs | {summary['deprecated']} |",
             f"| Decisions required | {summary['decisions_required']} |",
             f"| Unresolved critical decisions | {len(critical)} |",
             f"| Conflicts | {len(conflicts)} |",
             f"| Warnings | {sum(1 for i in g6.issues if i.level == 'warning')} |",
             f"| Overall (G6, automated) | {g6.result} |",
             "", "## Decisions", "",
             "| ADR | Title | Status | Decision owner | Date | Requirements | Features | Tasks | Supersedes | Superseded by |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for adr in b.adrs:
        entry = trace.get(adr["id"], {})
        lines.append("| " + " | ".join(md(v) for v in (
            adr["id"], adr.get("title"), str(adr.get("status")).upper(), adr.get("decision_owner"), adr.get("date"),
            entry.get("requirement_ids"), entry.get("feature_ids"), entry.get("task_ids"), adr.get("supersedes"),
            adr.get("superseded_by"))) + " |")
    lines += ["", "## Concern coverage", "", "| Concern | Status | ADRs | Questions |", "| --- | --- | --- | --- |"]
    for row in b.coverage:
        status = str(row.get("status") or "not assessed").replace("_", " ").upper()
        lines.append("| " + " | ".join(md(v) for v in (row["concern"], status, row.get("adr_ids"), row.get("question_ids"))) + " |")
    lines += ["", "## Conflicts", ""]
    lines += [f"- {f.code}: {f.message} `{f.location}`" for f in conflicts] or ["None detected."]
    lines += ["", "## Unresolved critical decisions", ""]
    lines += [f"- {item}" for item in critical] or ["None."]
    lines += ["", "## G6 issues", ""]
    lines += [f"- {'FAIL' if i.level == 'error' else 'WARN'} {i.message}" + (f" `{i.location}`" if i.location else "")
              for i in g6.issues] or ["All automated criteria are met."]
    lines.append("")
    return "\n".join(line.replace("|", "\\|") if line.startswith("- ") else line for line in lines)


def report_markdown(results: list[GateResult], violations: list[Issue], ctx: Context, when: str) -> str:
    lines = ["# Gate Report", "",
             "<!-- GENERATED by tools/check_gates.py. Do not edit: fix the records and regenerate. -->", "",
             f"Project: {ctx.bundle.project.get('name')} ({ctx.bundle.project.get('project_id')}) · "
             f"Current stage: {ctx.current_stage or 'not stated'} · Evaluated: {when}", "",
             "| Gate | Stage | Result | Errors | Warnings |", "| --- | --- | --- | --- | --- |"]
    for r in results:
        errors = sum(1 for i in r.issues if i.level == "error")
        warnings = sum(1 for i in r.issues if i.level == "warning")
        due = "" if ctx.current_stage is None or r.number <= ctx.current_stage else " (not yet due)"
        stage = f"{STAGE_LABEL.get(r.gate, r.number)}. {r.stage}" if r.number else r.stage
        lines.append(f"| {r.gate} — {r.name} | {stage} | {r.result}{due} | {errors} | {warnings} |")
    review = ctx.spec_review
    lines += ["", "## Specification review", "",
              f"From `{pr.SPECIFICATION_REVIEW_FILE}`, verified by `tools/specification_review.py`. Copy it into the "
              f"'Review measure' table of `project-state.md`.", "", "| Review measure | Value |", "| --- | --- |"]
    lines += [f"| {label} | {value} |" for label, value in review.summary_rows()]
    readiness = ctx.bundle.backlog_readiness or {}
    if readiness:
        s = readiness["summary"]
        lines += ["", "## Backlog readiness", "", f"From `{br.REPORT_FILE}` (regenerated by `tools/generate_handoff.py`).", "",
                  "| Measure | Value |", "| --- | --- |", f"| Backlog status | {readiness['status'].replace('_', ' ')} |",
                  f"| Active tasks | {s['active']} |", f"| READY and valid | {s['ready_valid']} |",
                  f"| Ready percentage | {s['ready_percentage']}% |",
                  f"| Work sets | {'; '.join(ws['id'] + ': ' + ', '.join(ws['task_ids']) for ws in readiness['work_sets']) or 'none'} |"]
    summary = (ctx.bundle.changes_doc or {}).get("summary") or {}
    if summary:
        lines += ["", "## Change state", "", "| Measure | Count |", "| --- | --- |"]
        lines += [f"| {key.replace('_', ' ').capitalize()} | {value} |" for key, value in summary.items()]
    lines += ["", "## Workflow state", ""]
    if violations:
        lines += [f"- **VIOLATION** {v.message}" + (f" `{v.location}`" if v.location else "") for v in violations]
    else:
        lines.append("- No stage or gate is claimed beyond what the evidence supports.")
    for r in results:
        lines += ["", f"## {r.gate} — {r.name}: {r.result}", ""]
        if not r.issues:
            lines.append("All automated criteria are met.")
        for issue in r.issues:
            label = "FAIL" if issue.level == "error" else "WARN"
            lines.append(f"- {label} {issue.message}" + (f" `{issue.location}`" if issue.location else ""))
    lines.append("")
    return "\n".join(line.replace("|", "\\|") if line.startswith("- ") else line for line in lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate the workflow's quality gates for one project.")
    parser.add_argument("project", type=Path)
    parser.add_argument("--gate", help="Show only this gate, for example G3")
    parser.add_argument("--no-write", action="store_true", help="Do not write reports/")
    parser.add_argument("--verbose", action="store_true", help="List every issue, not only failing gates")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        # Record text may hold characters a Windows console cannot encode; print them replaced, never crash.
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")

    project = args.project.resolve()
    if not (project / pr.STATE_FILE).is_file():
        print(f"{args.project} has no {pr.STATE_FILE}; is it a project folder?", file=sys.stderr)
        return 2
    try:
        results, violations, ctx = evaluate(project)
    except vh.SchemaUnavailable as exc:
        print(str(exc), file=sys.stderr)
        return 2
    when = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    if not args.no_write:
        reports = project / "reports"
        reports.mkdir(exist_ok=True)
        (reports / "gate-report.md").write_text(report_markdown(results, violations, ctx, when), encoding="utf-8", newline="\n")
        (reports / "dependency-graph.md").write_text(dependency_graph(ctx), encoding="utf-8", newline="\n")
        (reports / "architecture-report.md").write_text(architecture_report(results, ctx, when), encoding="utf-8", newline="\n")
        (project / sr.AID_FILE).write_text(sr.aid_markdown(ctx.bundle, ctx.spec_review, when, ctx.findings),
                                           encoding="utf-8", newline="\n")
        if (project / "backlog").is_dir() and ctx.bundle.backlog_readiness:
            (project / br.REPORT_FILE).write_text(br.report_markdown(ctx.bundle.backlog_readiness, ctx.bundle, when),
                                                  encoding="utf-8", newline="\n")

    shown = [r for r in results if not args.gate or r.gate == args.gate.upper()]
    print(f"Gates for {args.project} (current stage: {ctx.current_stage or 'not stated'})")
    for r in shown:
        due = "" if ctx.current_stage is None or r.number <= ctx.current_stage else "  (not yet due)"
        print(f"  {r.gate:<4} {r.name:<26} {r.result}{due}")
    if not args.gate or args.gate.upper() == "GR":
        review = ctx.spec_review
        c = review.counts
        print(f"\nSpecification review: {review.overall} (cycle {review.cycle or 0}) - open critical {c['critical']}, "
              f"major {c['major']}, minor {c['minor']}, observations {c['observation']}; accepted risks {c['accepted_risk']}")
    for r in shown:
        detail = args.gate or args.verbose or (r.result != PASS and (ctx.current_stage is None or r.number <= ctx.current_stage))
        if not detail or not r.issues:
            continue
        print(f"\n{r.gate} - {r.name}: {r.result}")
        for issue in r.issues:
            label = "FAIL" if issue.level == "error" else "WARN"
            print(f"  {label} {issue.message}" + (f" [{issue.location}]" if issue.location else ""))
    if violations:
        print("\nWorkflow state violations:")
        for v in violations:
            print(f"  VIOLATION {v.message} [{v.location}]")
    if not args.no_write:
        print("\nWrote reports/gate-report.md, reports/dependency-graph.md, reports/architecture-report.md and "
              "reports/specification-review-aid.md, and backlog/readiness-report.md when a backlog exists")
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
