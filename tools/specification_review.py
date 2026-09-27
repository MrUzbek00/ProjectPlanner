#!/usr/bin/env python3
"""Independent specification review: verify reviews/specification-review.md and summarise it.

Stage 8A of the workflow (WORKFLOW.md section 13). A SPECIFICATION REVIEWER who
is not the SPECIFICATION AUTHOR examines the specification against the source
records and records findings (REVIEW-###). The reviewer never rewrites the
specification: it detects, documents, recommends, waits for the resolution and
re-reviews in a later cycle. This module checks that the review record can be
relied on and computes what it concludes:

- the header: reviewed version, cycle, date, a reviewer who is not the author;
- the checklist, one row or more for every review area, each examined;
- the twelve review questions, each answered, every NO or PARTIAL backed by a finding;
- every finding: severity, category, status, evidence that cites artifacts,
  affected artifacts that exist, and a resolution, accepted risk or rejection
  recorded the way its status requires;
- the cycle history: every closed cycle frozen in reviews/history/, agreeing
  with its snapshot, with no finding deleted or backdated;
- possible contradictions between requirements (heuristic): each is a finding
  or dismissed with a reason;
- approved changes dated after the review, which make it stale.

The review result follows one rule. An unresolved CRITICAL or MAJOR finding
fails it; a CRITICAL finding cannot be accepted as a risk. Open MINOR or
OBSERVATION findings, and accepted risks, pass it with warnings. No open
finding passes it.

It also writes the automated review aid, reports/specification-review-aid.md:
candidates for the reviewer to judge, never findings of their own.

Usage:
    python tools/specification_review.py projects/<project>                 # status; writes the review aid
    python tools/specification_review.py projects/<project> --start-cycle   # freeze this cycle, open the next
    python tools/specification_review.py projects/<project> --json          # the computed specification-review.json

Exit codes: 0 when the review passes (warnings allowed), 1 when it fails or the
command is refused, 2 when the tool cannot run.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import planning_records as pr  # noqa: E402

REVIEW_FILE = pr.SPECIFICATION_REVIEW_FILE
HISTORY_DIR = "reviews/history"
AID_FILE = "reports/specification-review-aid.md"

PASS, WARN, FAIL, NOT_REVIEWED = "PASS", "PASS WITH WARNINGS", "FAIL", "NOT REVIEWED"
JSON_RESULT = {PASS: "PASS", WARN: "PASS_WITH_WARNINGS", FAIL: "FAIL", NOT_REVIEWED: "NOT_REVIEWED"}

SEVERITIES = ("CRITICAL", "MAJOR", "MINOR", "OBSERVATION")
SERIOUS = ("CRITICAL", "MAJOR")
CATEGORIES = ("REQUIREMENT", "SCOPE", "WORKFLOW", "DATA", "SECURITY", "AUTHORIZATION", "ARCHITECTURE", "INTEGRATION",
              "TRACEABILITY", "ROADMAP", "RISK", "TERMINOLOGY", "CHANGE_IMPACT", "ACCEPTANCE_CRITERIA", "ASSUMPTION")
STATUSES = ("OPEN", "ACKNOWLEDGED", "IN_RESOLUTION", "RESOLVED", "ACCEPTED_RISK", "REJECTED")
UNRESOLVED = ("OPEN", "ACKNOWLEDGED", "IN_RESOLUTION")
CLOSED = ("RESOLVED", "ACCEPTED_RISK", "REJECTED")

# The areas every review covers. A project may add rows; it may not drop an area.
REVIEW_AREAS = [
    "Requirements quality", "Scope consistency", "Workflow completeness", "Missing scenarios",
    "Permissions and authorisation", "Security", "Data model", "Integrations", "Architecture consistency",
    "Independent traceability", "Contradictions", "Acceptance criteria", "Terminology", "Assumptions", "Risks",
    "Change consistency", "Roadmap consistency", "Review quality",
]
CHECK_RESULTS = ("PASS", "FAIL", "N/A", "NOT REVIEWED")
# What the review must be able to answer. The last one is its conclusion.
REVIEW_QUESTIONS = [
    "Is the specification internally consistent?",
    "Are requirements complete enough?",
    "Are requirements testable?",
    "Are assumptions visible?",
    "Are workflows coherent?",
    "Are permissions defined?",
    "Are major security concerns covered?",
    "Does the architecture match the specification?",
    "Is traceability valid?",
    "Did recent changes propagate correctly?",
    "Are there unresolved contradictions?",
    "Is the specification safe to use as the basis for backlog planning?",
]
ANSWERS = ("YES", "NO", "PARTIAL", "N/A")
# The answer that reports a problem. For the contradiction question a YES is the problem.
PROBLEM_ANSWER = {pr.norm_key("Are there unresolved contradictions?"): "YES"}
SAFE_QUESTION = pr.norm_key(REVIEW_QUESTIONS[-1])

# (label in the review header and in the history table, key in the computed counts)
COUNT_FIELDS = [
    ("Open critical", "critical"), ("Open major", "major"), ("Open minor", "minor"),
    ("Open observations", "observation"), ("Open findings", "open"), ("Accepted risks", "accepted_risk"),
    ("Resolved since previous review", "resolved_since_previous"), ("Findings raised", "total"),
]
# Errors that do not stop a cycle from being closed: they are why a new cycle is needed.
CYCLE_TOLERATED = {"UNRESOLVED_FINDING", "REVIEW_VERSION", "CHANGE_AFTER_REVIEW", "CONTRADICTION_UNREVIEWED",
                   "BACKLOG_PROVISIONAL"}
ISO_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
LIVE = {"approved", "confirmed"}


# --------------------------------------------------------------------------
# Values
# --------------------------------------------------------------------------


def enum(value: str | None) -> str:
    text = pr.clean(value or "").split("—")[0].split(" - ")[0].split("(")[0]
    return re.sub(r"\s+", " ", text).strip().upper()


def token(value: str | None) -> str:
    """ACCEPTED RISK, accepted-risk and ACCEPTED_RISK all read as ACCEPTED_RISK."""
    return enum(value).replace("-", "_").replace(" ", "_")


def result_label(value: str | None) -> str:
    return enum(value).replace("_", " ")


def given(value: str | None) -> bool:
    text = pr.clean(value or "")
    return bool(text) and not pr.has_tbd(text) and not pr.is_none(text)


def number(value: str | None) -> int | None:
    match = re.match(r"^\s*(\d+)\b", pr.clean(value or ""))
    return int(match.group(1)) if match else None


def person(value: str | None) -> str:
    """A name without its role annotation, for comparing who did what."""
    return re.sub(r"\s+", " ", pr.clean(value or "").split("—")[0].split("(")[0]).strip().casefold()


def snapshot_path(cycle: int) -> str:
    return f"{HISTORY_DIR}/specification-review-cycle-{cycle:03d}.md"


def col(row: dict, *names: str) -> str:
    for name in names:
        key = pr.norm_key(name)
        if key in row:
            return pr.clean(row[key])
    for name in names:
        key = pr.norm_key(name)
        for existing in row:
            if existing.startswith(key):
                return pr.clean(row[existing])
    return ""


def is_unresolved(severity: str, status: str) -> bool:
    """Not closed, closed with a status that does not exist, or a CRITICAL finding 'accepted' as a risk."""
    return status not in CLOSED or (status == "ACCEPTED_RISK" and severity == "CRITICAL")


def result_for(pairs) -> str:
    """The review result from (severity, status) pairs.

    CRITICAL or MAJOR unresolved -> FAIL. Otherwise open MINOR or OBSERVATION findings, or accepted risks,
    -> PASS WITH WARNINGS. No open finding -> PASS. There is no threshold: one unresolved MAJOR fails it.
    """
    pairs = list(pairs)
    if any(is_unresolved(s, st) and s not in ("MINOR", "OBSERVATION") for s, st in pairs):
        return FAIL
    if any(is_unresolved(s, st) or st == "ACCEPTED_RISK" for s, st in pairs):
        return WARN
    return PASS


def counts_for(findings: list["ReviewFinding"], cycle: int | None) -> dict:
    out = {key: 0 for _, key in COUNT_FIELDS}
    out.update({"resolved": 0, "rejected": 0})
    labels = {"CRITICAL": "critical", "MAJOR": "major", "MINOR": "minor", "OBSERVATION": "observation"}
    for f in findings:
        out["total"] += 1
        if is_unresolved(f.severity, f.status):
            out[labels.get(f.severity, "major")] += 1
            out["open"] += 1
        elif f.status == "ACCEPTED_RISK":
            out["accepted_risk"] += 1
        elif f.status == "RESOLVED":
            out["resolved"] += 1
            if cycle is not None and f.closed_in == cycle:
                out["resolved_since_previous"] += 1
        elif f.status == "REJECTED":
            out["rejected"] += 1
    return out


# --------------------------------------------------------------------------
# Records
# --------------------------------------------------------------------------


@dataclass
class Issue:
    level: str  # error | warning
    code: str
    message: str
    location: str = ""


@dataclass
class ReviewFinding:
    id: str
    title: str
    line: int
    severity: str
    category: str
    status: str
    raised_in: int | None
    closed_in: int | None
    affected: list[str]
    return_to_stage: str
    evidence: str
    conflict: str
    why: str
    action: str
    resolution: str
    resolved_by: str
    resolution_date: str
    changed: list[str]
    verification: str
    approved_by: str
    approval_evidence: list[str]
    field_lines: dict[str, int] = field(default_factory=dict)

    def as_json(self) -> dict:
        closure = None
        if self.status in CLOSED:
            closure = {
                "text": self.resolution,
                "resolved_by": self.resolved_by or None,
                "resolution_date": self.resolution_date if ISO_DATE.match(self.resolution_date) else None,
                "changed_artifacts": self.changed,
                "verification": self.verification,
                "approved_by": self.approved_by or None,
                "approval_evidence": self.approval_evidence,
            }
        return {
            "id": self.id, "title": self.title, "severity": self.severity, "category": self.category,
            "status": self.status, "raised_in_cycle": self.raised_in, "closed_in_cycle": self.closed_in,
            "affected_artifacts": self.affected, "return_to_stage": self.return_to_stage or None,
            "evidence": self.evidence, "conflict": self.conflict, "why_it_matters": self.why,
            "required_action": self.action, "resolution": closure, "source_path": REVIEW_FILE,
        }


@dataclass
class Cycle:
    cycle: int
    date: str | None
    version: str | None
    reviewer: str
    result: str
    counts: dict
    snapshot: str | None
    line: int = 0

    def as_json(self) -> dict:
        return {
            "review_cycle": self.cycle, "review_date": self.date, "review_version": self.version,
            "overall_result": JSON_RESULT.get(self.result, "FAIL"),
            "finding_count": sum(self.counts.get(k, 0) for k in ("critical", "major", "minor", "observation")),
            "critical_count": self.counts.get("critical", 0), "major_count": self.counts.get("major", 0),
            "minor_count": self.counts.get("minor", 0), "observation_count": self.counts.get("observation", 0),
            "accepted_risk_count": self.counts.get("accepted_risk", 0),
            "resolved_since_previous": self.counts.get("resolved_since_previous", 0),
            "snapshot": self.snapshot,
        }


@dataclass
class Candidate:
    kind: str
    ids: tuple[str, str]
    detail: str
    disposition: str = ""  # REVIEW-### that records it, "dismissed", or "" when nobody has judged it


@dataclass
class Evaluation:
    exists: bool = False
    fields: dict[str, str] = field(default_factory=dict)
    field_lines: dict[str, int] = field(default_factory=dict)
    cycle: int | None = None
    review_date: str | None = None
    reviewed_version: str | None = None
    specification_version: str | None = None
    reviewer: str = ""
    author: str = ""
    findings: list[ReviewFinding] = field(default_factory=list)
    history: list[Cycle] = field(default_factory=list)
    counts: dict = field(default_factory=lambda: counts_for([], None))
    result: str = NOT_REVIEWED
    stated_result: str = ""
    candidates: list[Candidate] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)

    def error(self, code: str, message: str, location: str = REVIEW_FILE) -> None:
        self.issues.append(Issue("error", code, message, location))

    def warn(self, code: str, message: str, location: str = REVIEW_FILE) -> None:
        self.issues.append(Issue("warning", code, message, location))

    @property
    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.level == "error"]

    @property
    def defects(self) -> list[Issue]:
        """Errors in the review record itself, not the open findings it reports."""
        return [i for i in self.errors if i.code != "UNRESOLVED_FINDING"]

    @property
    def overall(self) -> str:
        """What downstream may rely on: NOT REVIEWED without a review, FAIL when the record is defective."""
        if not self.exists:
            return NOT_REVIEWED
        return FAIL if self.errors else self.result

    def current_cycle(self) -> Cycle | None:
        if self.cycle is None:
            return None
        return Cycle(self.cycle, self.review_date, self.reviewed_version, self.reviewer, self.overall, self.counts, None)

    def summary_rows(self) -> list[tuple[str, str]]:
        """The specification-review summary project-state.md exposes (templates/00)."""
        return [("Specification review", self.overall), ("Last review cycle", str(self.cycle or 0)),
                ("Open critical", str(self.counts["critical"])), ("Open major", str(self.counts["major"])),
                ("Open minor", str(self.counts["minor"])), ("Open observations", str(self.counts["observation"])),
                ("Accepted risks", str(self.counts["accepted_risk"]))]


def _text(record: pr.Record, *names: str) -> str:
    value = pr.clean(record.field(*names) or "")
    if value:
        return value
    section = record.section(*names)
    if section is None:
        return ""
    parts = [section.text] if section.text else []
    parts += [pr.clean(item) for item in section.items]
    return "\n".join(p for p in parts if p).strip()


def read_findings(path: Path) -> list[ReviewFinding]:
    out = []
    for record in pr.read_records(path, ("REVIEW",)):
        out.append(ReviewFinding(
            id=record.id, title=record.title, line=record.line,
            severity=token(record.field("severity")), category=token(record.field("category")),
            status=token(record.field("status")),
            raised_in=number(record.field("raised in cycle", "raised in")),
            closed_in=number(record.field("closed in cycle", "closed in")),
            affected=pr.extract_ids(pr.clean(record.field("affected artifacts", "affected ids") or "")),
            return_to_stage=pr.clean(record.field("return to stage") or ""),
            evidence=_text(record, "evidence"), conflict=_text(record, "conflict"),
            why=_text(record, "why it matters"), action=_text(record, "required action"),
            resolution=_text(record, "resolution", "reason"),
            resolved_by=pr.clean(record.field("resolved by", "decided by") or ""),
            resolution_date=pr.clean(record.field("resolution date") or ""),
            changed=pr.extract_ids(pr.clean(record.field("changed artifacts") or "")),
            verification=_text(record, "verification"),
            approved_by=pr.clean(record.field("approved by") or ""),
            approval_evidence=pr.extract_ids(pr.clean(record.field("approval evidence") or ""), ("DEC", "SRC")),
            field_lines=dict(record.field_lines),
        ))
    return out


def _header(path: Path) -> tuple[dict[str, str], dict[str, int]]:
    for table in pr.read_tables(path):
        if table.keys()[:1] == ["field"]:
            fields, lines = {}, {}
            for line, row in table.dict_rows():
                values = list(row.values())
                key = pr.norm_key(values[0]) if values else ""
                if key:
                    fields[key] = pr.clean(values[1]) if len(values) > 1 else ""
                    lines[key] = line
            return fields, lines
    return {}, {}


def _tables(path: Path, first: str) -> list[pr.Table]:
    return [t for t in pr.read_tables(path) if t.keys()[:1] == [pr.norm_key(first)]]


def _area_key(label: str) -> str:
    return pr.norm_key(label).replace("authoriz", "authoris")


# --------------------------------------------------------------------------
# Contradiction candidates (heuristic — the reviewer judges each one)
# --------------------------------------------------------------------------

_ONE = re.compile(r"\b(?:exactly one|only one|one and only one|at most one|no more than one|a single|one single)\s+((?:[\w-]+\s+){0,2}[\w-]+)",
                  re.IGNORECASE)
_MANY = re.compile(r"\b(?:multiple|several|many|more than one|one or more|any number of)\s+((?:[\w-]+\s+){0,2}[\w-]+)",
                   re.IGNORECASE)
_DELETE = re.compile(r"\b(?:permanent(?:ly)?\s+(?:delet\w*|remov\w*)|(?:delet\w*|remov\w*)\s+(?:[\w-]+\s+){0,3}?permanently|"
                     r"hard[- ]delet\w*|purg\w+|irreversibl\w+ delet\w*)\b", re.IGNORECASE)
_RETAIN = re.compile(r"\b(?:retain\w*|retention|must be kept|kept for|preserved? for|archiv\w+|stored for|must not be deleted)\b",
                     re.IGNORECASE)
_ANONYMOUS = re.compile(r"\b(?:anonymous(?:ly)?|unauthenticated|guests?|without (?:an? )?(?:account|log ?in|logging in|"
                        r"signing in|sign-in|authentication|registration))\b", re.IGNORECASE)
_AUTHENTICATED = re.compile(r"\b(?:requires? (?:an? )?(?:authenticat\w+|log ?in|sign-in|signed-in|account)|must be "
                            r"(?:logged in|signed in|authenticated)|only (?:authenticated|registered|signed-in|logged-in)|"
                            r"authenticated users? only)\b", re.IGNORECASE)
_STOP = {"user", "users", "system", "must", "shall", "should", "will", "can", "may", "able", "that", "this", "which",
         "with", "from", "have", "been", "data", "their", "they", "them", "only", "each", "every", "when", "then",
         "into", "also", "more", "than", "same", "other", "after", "before", "within", "exactly", "single", "multiple",
         "several", "many", "permanently", "delete", "deleted", "retained", "retain", "kept", "anonymous",
         "authenticated", "require", "requires", "place", "make"}


def _stem(word: str) -> str:
    word = word.lower().replace("isation", "ization").replace("ise", "ize")
    for suffix in ("ies", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 4:
            return word[: -len(suffix)] + ("y" if suffix == "ies" else "")
    return word


def _nouns(text: str) -> set[str]:
    return {_stem(w) for w in re.findall(r"[A-Za-z][A-Za-z-]{3,}", text) if w.lower() not in _STOP}


def _windows(regex: re.Pattern, text: str, before: int = 4, after: int = 5) -> set[str]:
    out: set[str] = set()
    for match in regex.finditer(text):
        head = text[: match.start()].split()[-before:]
        tail = text[match.end():].split()[:after]
        out |= _nouns(" ".join(head + [match.group(0)] + tail))
    return out


def _requirement_text(req: dict) -> str:
    return " ".join([req.get("title") or "", req.get("description") or "", req.get("permissions") or "",
                     " ".join(req.get("acceptance_criteria") or [])])


_NEGATED = re.compile(r"\b(?:never|not|cannot|can't|no)\b[\w\s-]{0,25}$", re.IGNORECASE)


def _deletion(text: str, negated: bool) -> list[re.Match]:
    """Permanent-deletion statements; ``negated`` selects the ones that forbid deletion ("must never be deleted")."""
    return [m for m in _DELETE.finditer(text) if bool(_NEGATED.search(text[max(0, m.start() - 30):m.start()])) == negated]


def _match_windows(matches: list[re.Match], text: str, before: int = 4, after: int = 5) -> set[str]:
    out: set[str] = set()
    for match in matches:
        head = text[: match.start()].split()[-before:]
        tail = text[match.end():].split()[:after]
        out |= _nouns(" ".join(head + [match.group(0)] + tail))
    return out


def contradiction_pairs(items: list[dict]) -> list[Candidate]:
    """Pairs of statements that may contradict. Each item is {"id", "text", "related"}: related holds the IDs
    (modules, requirements, features) that tie it to others. A candidate, never a finding."""
    found: dict[tuple[str, str], Candidate] = {}

    def related(a: dict, b: dict) -> bool:
        ra, rb = set(a.get("related") or []) - {None}, set(b.get("related") or []) - {None}
        return bool(ra & rb) or a["id"] in rb or b["id"] in ra

    def add(kind: str, x: str, y: str, detail: str) -> None:
        key = tuple(sorted((x, y), key=pr.natural_key))
        found.setdefault(key, Candidate(kind, key, detail))

    for a in items:
        for b in items:
            if a["id"] == b["id"]:
                continue
            ta, tb = a["text"], b["text"]
            one = {_stem(w) for m in _ONE.finditer(ta) for w in m.group(1).split() if w.lower() not in _STOP}
            many = {_stem(w) for m in _MANY.finditer(tb) for w in m.group(1).split() if w.lower() not in _STOP}
            shared = sorted(n for n in one & many if len(n) >= 4)
            if shared:
                add("CARDINALITY", a["id"], b["id"], f"{a['id']} allows exactly one '{shared[0]}'; {b['id']} allows several")
            deletes = _deletion(ta, negated=False)
            keeps = _deletion(tb, negated=True)
            if deletes and (keeps or _RETAIN.search(tb)):
                common = _match_windows(deletes, ta) & (_match_windows(keeps, tb) | _windows(_RETAIN, tb))
                if common or related(a, b):
                    add("DELETION_RETENTION", a["id"], b["id"],
                        f"{a['id']} permits permanent deletion; {b['id']} requires retention or forbids deletion"
                        + (f" ('{sorted(common)[0]}')" if common else ""))
            if _ANONYMOUS.search(ta) and _AUTHENTICATED.search(tb):
                common = _windows(_ANONYMOUS, ta) & _windows(_AUTHENTICATED, tb)
                if common or related(a, b):
                    add("ACCESS", a["id"], b["id"],
                        f"{a['id']} allows anonymous or unauthenticated use; {b['id']} requires authentication"
                        + (f" ('{sorted(common)[0]}')" if common else ""))
    return [found[k] for k in sorted(found, key=lambda k: (pr.natural_key(k[0]), pr.natural_key(k[1])))]


def contradiction_candidates(bundle) -> list[Candidate]:
    """Pairs of live requirements that may state contradictory things. A candidate, never a finding."""
    items = [{"id": r["id"], "text": _requirement_text(r),
              "related": set(r.get("related_modules") or []) | set(r.get("source") or []) | set(r.get("dependencies") or [])}
             for r in bundle.requirements if r.get("status") in LIVE and r.get("scope") not in ("out_of_scope", "future")]
    return contradiction_pairs(items)


# --------------------------------------------------------------------------
# Evaluation
# --------------------------------------------------------------------------


def evaluate(project: Path, bundle) -> Evaluation:
    """Read and verify the specification review. ``bundle`` is the validator's view of the records."""
    ev = Evaluation(specification_version=bundle.project.get("version"))
    ev.candidates = contradiction_candidates(bundle)
    path = project / REVIEW_FILE
    if not path.is_file():
        ev.error("REVIEW_MISSING", f"{REVIEW_FILE} has not been written: the specification has not been independently "
                                   f"reviewed. Copy templates/12 and review it as the SPECIFICATION REVIEWER.")
        return ev
    ev.exists = True
    ev.fields, ev.field_lines = _header(path)
    ev.findings = read_findings(path)
    if any(pr.FULL_ID_RE["FIND"].match(pr.clean(row[0])) for t in _tables(path, "Finding ID") for row in t.rows if row):
        ev.error("LEGACY_FINDINGS", "The review records findings in a FIND-### table. Specification review findings are "
                                    "REVIEW-### record blocks with evidence, affected artifacts and a resolution "
                                    "(templates/12); migrate them, keeping each finding's history.")
    own = {f.id for f in ev.findings}

    def known(identifier: str) -> bool | None:
        kind = pr.kind_of(identifier)
        if kind == "REVIEW":
            return identifier in own
        if kind == "FIND":
            return None
        return bundle.known(identifier)

    def at(key: str) -> str:
        line = ev.field_lines.get(pr.norm_key(key))
        return f"{REVIEW_FILE}:{line}" if line else REVIEW_FILE

    _check_header(ev, at)
    ev.history = _read_history(project, path, ev)
    _check_checklist(ev, path)
    _check_questions(ev, path)
    _check_findings(ev, project, known, bundle)
    ev.counts = counts_for(ev.findings, ev.cycle)
    ev.result = result_for((f.severity, f.status) for f in ev.findings)
    _check_history(ev, project)
    _check_conclusion(ev, at)
    _check_safe_answer(ev, path)
    _check_candidates(ev, path)
    _check_changes(ev, bundle)
    if ev.result == FAIL and bundle.tasks:
        ev.warn("BACKLOG_PROVISIONAL",
                f"{len(bundle.tasks)} task(s) exist while the specification review fails. The backlog is provisional: no "
                f"task can be READY, and it cannot be called backlog-ready or planning-complete.", "backlog/")
    return ev


def _check_header(ev: Evaluation, at) -> None:
    f = ev.fields
    version = f.get("reviewed version", "")
    ev.reviewed_version = version if given(version) else None
    if not ev.reviewed_version:
        ev.error("REVIEW_VERSION", "The review does not state the 'Reviewed version'.", at("reviewed version"))
    elif ev.specification_version and ev.reviewed_version != ev.specification_version:
        ev.error("REVIEW_VERSION", f"The review covers version {ev.reviewed_version}; the specification is version "
                                   f"{ev.specification_version}. Review the current version in a new cycle "
                                   f"(tools/specification_review.py --start-cycle).", at("reviewed version"))
    ev.cycle = number(f.get("review cycle"))
    if not ev.cycle:
        ev.error("REVIEW_CYCLE", f"'Review cycle' is {f.get('review cycle') or 'blank'}; number the cycles from 1.",
                 at("review cycle"))
    date = f.get("review date", f.get("date", ""))
    if ISO_DATE.match(date):
        ev.review_date = date
    else:
        ev.error("REVIEW_DATE", f"Review cycle {ev.cycle or '?'} has no review date ({date or 'blank'}); a cycle is dated "
                                f"when the reviewer completes it.", at("review date"))
    ev.reviewer, ev.author = f.get("reviewer", ""), f.get("specification author", "")
    if not given(ev.reviewer):
        ev.error("REVIEWER_MISSING", "The review does not name its reviewer (SPECIFICATION REVIEWER).", at("reviewer"))
    if not given(ev.author):
        ev.error("AUTHOR_MISSING", "The review does not name the specification's author (SPECIFICATION AUTHOR).",
                 at("specification author"))
    if given(ev.reviewer) and given(ev.author) and person(ev.reviewer) == person(ev.author):
        ev.error("REVIEWER_NOT_INDEPENDENT", f"The reviewer ({ev.reviewer}) is the specification's author. The author "
                                             f"does not grade their own work: use an independent reviewer or a separate "
                                             f"review pass (prompts/specification-reviewer.md).", at("reviewer"))
    if not given(f.get("independence")):
        ev.error("INDEPENDENCE_MISSING", "The review does not state how the reviewer is independent of the author "
                                         "('Independence').", at("independence"))
    ev.stated_result = result_label(f.get("overall result"))


def _check_checklist(ev: Evaluation, path: Path) -> None:
    tables = _tables(path, "Area")
    rows = [(line, row) for table in tables for line, row in table.dict_rows() if col(row, "check")]
    if not rows:
        ev.error("CHECKLIST_MISSING", "The review has no checklist (a table whose first column is 'Area'); a blank "
                                      "checklist is not a pass.")
        return
    covered = {_area_key(col(row, "area")) for _, row in rows}
    for area in REVIEW_AREAS:
        if _area_key(area) not in covered:
            ev.error("CHECKLIST_AREA", f"The checklist does not cover the review area '{area}'.")
    closed = {f.id for f in ev.findings if f.status in ("RESOLVED", "REJECTED")}
    for line, row in rows:
        where = f"{REVIEW_FILE}:{line}"
        check, outcome = col(row, "check"), enum(col(row, "result"))
        evidence = col(row, "evidence / ids", "evidence", "findings")
        cited = pr.extract_ids(evidence, ("REVIEW",))
        if outcome not in CHECK_RESULTS:
            ev.error("CHECKLIST_RESULT", f"Check '{check}' has result {outcome or 'blank'}; use PASS, FAIL, N/A or "
                                         f"NOT REVIEWED.", where)
        elif outcome == "NOT REVIEWED":
            ev.error("CHECKLIST_NOT_REVIEWED", f"Check '{check}' is NOT REVIEWED.", where)
        elif outcome == "N/A" and not evidence:
            ev.error("CHECKLIST_NA", f"Check '{check}' is N/A without a reason.", where)
        elif outcome == "FAIL":
            if not cited:
                ev.error("CHECKLIST_FAIL_UNRECORDED", f"Check '{check}' FAILED but cites no REVIEW-### finding: every "
                                                      f"problem the review finds is recorded as a finding.", where)
            elif all(c in closed for c in cited):
                ev.error("CHECKLIST_STALE", f"Check '{check}' is still FAIL but {', '.join(cited)} "
                                            f"{'is' if len(cited) == 1 else 'are'} closed; re-review the check.", where)
        elif outcome == "PASS" and not evidence:
            ev.warn("CHECKLIST_NO_EVIDENCE", f"Check '{check}' is PASS without evidence; name what was examined.", where)
        for identifier in cited:
            if identifier not in {f.id for f in ev.findings}:
                ev.error("UNKNOWN_FINDING", f"Check '{check}' cites {identifier}, which is not a finding in this review.", where)


def _check_questions(ev: Evaluation, path: Path) -> None:
    tables = _tables(path, "Review question")
    rows = {pr.norm_key(col(row, "review question")).rstrip("?"): (line, row)
            for table in tables for line, row in table.dict_rows()}
    open_ids = {f.id for f in ev.findings if is_unresolved(f.severity, f.status) or f.status == "ACCEPTED_RISK"}
    for question in REVIEW_QUESTIONS:
        key = pr.norm_key(question)
        found = rows.get(key.rstrip("?"))
        if found is None:
            ev.error("QUESTION_MISSING", f"The review does not answer '{question}'.")
            continue
        line, row = found
        where = f"{REVIEW_FILE}:{line}"
        answer = enum(col(row, "answer"))
        evidence = col(row, "evidence / findings", "evidence", "findings")
        if answer not in ANSWERS:
            ev.error("QUESTION_UNANSWERED", f"'{question}' is answered {answer or 'blank'}; answer YES, NO, PARTIAL "
                                            f"or N/A with a reason.", where)
            continue
        if answer == "N/A" and not evidence:
            ev.error("QUESTION_NA", f"'{question}' is N/A without a reason.", where)
        problem = answer == PROBLEM_ANSWER.get(key, "NO") or answer == "PARTIAL"
        cited = [c for c in pr.extract_ids(evidence, ("REVIEW",)) if c in open_ids]
        if key == SAFE_QUESTION:
            continue
        if problem and not cited:
            ev.error("QUESTION_UNRECORDED", f"'{question}' is answered {answer} but cites no open REVIEW-### finding: a "
                                            f"problem the review sees is recorded as a finding.", where)


def _check_findings(ev: Evaluation, project: Path, known, bundle) -> None:
    seen: dict[str, int] = {}
    titles: dict[str, str] = {}
    snapshots = {c: _snapshot_findings(project, c) for c in range(1, (ev.cycle or 1))}
    for f in ev.findings:
        where = f"{REVIEW_FILE}:{f.line}"

        def floc(name: str) -> str:
            line = f.field_lines.get(pr.norm_key(name))
            return f"{REVIEW_FILE}:{line}" if line else where

        if f.id in seen:
            ev.error("FINDING_ID_REUSED", f"{f.id} is recorded twice (also line {seen[f.id]}); a finding ID names one "
                                          f"finding and is never reused.", where)
            continue
        seen[f.id] = f.line
        key = re.sub(r"\W+", " ", f.title.lower()).strip()
        if key in titles:
            ev.error("FINDING_DUPLICATE", f"{f.id} duplicates {titles[key]} ('{f.title}'); record one finding per problem.", where)
        titles.setdefault(key, f.id)
        if f.severity not in SEVERITIES:
            ev.error("FINDING_SEVERITY", f"{f.id} has severity {f.severity or 'blank'}; use {', '.join(SEVERITIES)}.",
                     floc("severity"))
        if f.category not in CATEGORIES:
            ev.error("FINDING_CATEGORY", f"{f.id} has category {f.category or 'blank'}; use one of {', '.join(CATEGORIES)}.",
                     floc("category"))
        if f.status not in STATUSES:
            ev.error("FINDING_STATUS", f"{f.id} has status {f.status or 'blank'}; use one of {', '.join(STATUSES)}.",
                     floc("status"))
        if f.raised_in is None or not 1 <= f.raised_in <= (ev.cycle or 1):
            ev.error("FINDING_CYCLE", f"{f.id} is raised in cycle {f.raised_in or 'blank'}; it must be a cycle from 1 to "
                                      f"{ev.cycle or '?'}.", floc("raised in cycle"))
        elif f.raised_in in snapshots and snapshots[f.raised_in] is not None and f.id not in snapshots[f.raised_in]:
            ev.error("FINDING_BACKDATED", f"{f.id} claims to be raised in cycle {f.raised_in}, but that cycle's snapshot "
                                          f"does not contain it.", floc("raised in cycle"))

        # Evidence: specific, citable, and pointing at records that exist.
        if not f.evidence:
            ev.error("FINDING_NO_EVIDENCE", f"{f.id} states no evidence; a finding without evidence is speculation.", where)
        if f.severity in SERIOUS:
            if not f.affected:
                ev.error("FINDING_NO_ARTIFACTS", f"{f.severity} finding {f.id} names no affected artifact; cite the "
                                                 f"specific records (for example FR-021, SR-009).", floc("affected artifacts"))
            if f.evidence and not pr.extract_ids(f.evidence + " " + f.conflict):
                ev.error("FINDING_VAGUE", f"{f.severity} finding {f.id} does not cite a specific artifact in its evidence; "
                                          f"say which records state what.", where)
            if not f.return_to_stage:
                ev.error("FINDING_NO_STAGE", f"{f.severity} finding {f.id} does not say which stage resolves it "
                                             f"('Return to stage').", floc("return to stage"))
        elif f.severity == "MINOR" and not f.affected:
            ev.warn("FINDING_NO_ARTIFACTS", f"MINOR finding {f.id} names no affected artifact.", floc("affected artifacts"))
        for identifier in f.affected + pr.extract_ids(f.evidence + " " + f.conflict) + f.changed:
            if known(identifier) is False:
                ev.error("FINDING_UNKNOWN_REFERENCE", f"{f.id} refers to {identifier}, which no record defines.", where)
        if not f.why:
            ev.error("FINDING_NO_IMPACT", f"{f.id} does not say why it matters.", where)
        if not f.action and f.severity != "OBSERVATION":
            ev.error("FINDING_NO_ACTION", f"{f.id} does not state the required action.", where)
        _check_status(ev, f, floc, bundle)

    open_sets: dict[tuple, str] = {}
    for f in ev.findings:
        if f.affected and is_unresolved(f.severity, f.status):
            key = (f.category, tuple(sorted(f.affected)))
            if key in open_sets:
                ev.warn("FINDING_POSSIBLE_DUPLICATE", f"{f.id} and {open_sets[key]} are open {f.category} findings about "
                                                      f"the same artifacts; merge them if they describe one problem.",
                        f"{REVIEW_FILE}:{f.line}")
            open_sets.setdefault(key, f.id)


def _check_status(ev: Evaluation, f: ReviewFinding, floc, bundle) -> None:
    label = f"{f.severity} finding {f.id}" if f.severity in SEVERITIES else f.id
    if f.status in UNRESOLVED:
        if f.closed_in is not None:
            ev.error("FINDING_CLOSURE", f"{f.id} is {f.status} but records 'Closed in cycle' {f.closed_in}.", floc("closed in cycle"))
        if f.severity in SERIOUS:
            back = f" (return to stage {f.return_to_stage})" if f.return_to_stage else ""
            ev.error("UNRESOLVED_FINDING", f"{label} is {f.status}: {f.title}{back}.", floc("status"))
        elif f.severity in ("MINOR", "OBSERVATION"):
            ev.warn("OPEN_FINDING", f"{label} is {f.status}: {f.title}.", floc("status"))
        return
    if f.status not in CLOSED:
        return
    if f.closed_in is None:
        ev.error("FINDING_CLOSURE", f"{f.id} is {f.status} but does not record 'Closed in cycle'.", floc("closed in cycle"))
    elif ev.cycle and f.closed_in > ev.cycle:
        ev.error("FINDING_CLOSURE", f"{f.id} is closed in cycle {f.closed_in}, after the current cycle {ev.cycle}.",
                 floc("closed in cycle"))
    elif f.raised_in and f.closed_in < f.raised_in:
        ev.error("FINDING_CLOSURE", f"{f.id} is closed in cycle {f.closed_in}, before it was raised (cycle {f.raised_in}).",
                 floc("closed in cycle"))
    if not f.resolution:
        what = {"RESOLVED": "how it was resolved", "ACCEPTED_RISK": "why the risk is accepted",
                "REJECTED": "why it is not a defect"}[f.status]
        ev.error("FINDING_NO_RESOLUTION", f"{f.id} is {f.status} without recording {what} ('Resolution').", floc("resolution"))
    authors = {person(ev.author), person(ev.reviewer)} - {""}

    if f.status == "RESOLVED":
        if f.closed_in is not None and f.raised_in is not None and f.closed_in <= f.raised_in:
            ev.error("FINDING_NOT_REREVIEWED", f"{f.id} is RESOLVED in the cycle that raised it. The reviewer does not fix "
                                               f"findings: the author resolves them and a later review cycle verifies it.",
                     floc("closed in cycle"))
        if not given(f.resolved_by):
            ev.error("FINDING_NO_RESOLVER", f"{f.id} is RESOLVED without 'Resolved by'.", floc("resolved by"))
        if not ISO_DATE.match(f.resolution_date):
            ev.error("FINDING_NO_DATE", f"{f.id} is RESOLVED without a 'Resolution date' (YYYY-MM-DD).", floc("resolution date"))
        if not f.changed:
            ev.error("FINDING_NO_CHANGED_ARTIFACTS", f"{f.id} is RESOLVED but names no changed artifact; a resolution "
                                                     f"changes a record.", floc("changed artifacts"))
        if not f.verification:
            ev.error("FINDING_NOT_VERIFIED", f"{f.id} is RESOLVED without 'Verification' of the re-review.", floc("verification"))
        return

    if f.status == "ACCEPTED_RISK":
        if f.severity == "CRITICAL":
            ev.error("CRITICAL_ACCEPTED", f"CRITICAL finding {f.id} is recorded as ACCEPTED_RISK. The specification cannot "
                                          f"safely proceed with it: resolve it, or move what it affects to PENDING DECISION, "
                                          f"FUTURE or OUT OF SCOPE.", floc("status"))
            return
        _check_human_decision(ev, f, floc, bundle, authors, "accepts the risk")
        if f.severity == "MAJOR" and not any(r in bundle.risk_by_id for r in f.affected + f.changed + pr.extract_ids(f.resolution, ("RISK",))):
            ev.warn("ACCEPTED_RISK_UNREGISTERED", f"MAJOR finding {f.id} is an accepted risk that no RISK-### in the risk "
                                                  f"register records; keep it visible there.", floc("status"))
        ev.warn("ACCEPTED_RISK", f"{label} is an ACCEPTED RISK, approved by {f.approved_by or 'nobody'}: {f.title}. It stays "
                                 f"visible and is not resolved.", floc("status"))
        return

    # REJECTED: the finding is judged not to be a defect.
    if not given(f.resolved_by):
        ev.error("FINDING_NO_RESOLVER", f"{f.id} is REJECTED without saying who decided it ('Resolved by').", floc("resolved by"))
    if f.severity in SERIOUS:
        _check_human_decision(ev, f, floc, bundle, authors, "rejects the finding")


def _check_human_decision(ev: Evaluation, f: ReviewFinding, floc, bundle, authors: set[str], what: str) -> None:
    """Accepting a risk, or rejecting a serious finding, is a decision for a named human with evidence."""
    if not given(f.approved_by):
        ev.error("FINDING_NOT_APPROVED", f"{f.id} is {f.status} without 'Approved by': an authorised human {what}.",
                 floc("approved by"))
    elif person(f.approved_by) in authors:
        ev.error("FINDING_SELF_APPROVED", f"{f.id} is approved by {f.approved_by}, who wrote or reviewed the specification; "
                                          f"the decision owner {what}.", floc("approved by"))
    if not f.approval_evidence:
        ev.error("FINDING_NO_APPROVAL_EVIDENCE", f"{f.id} is {f.status} without 'Approval evidence' (DEC-### or SRC-###).",
                 floc("approval evidence"))
    for identifier in f.approval_evidence:
        if identifier not in bundle.dec_by_id and identifier not in bundle.src_by_id:
            ev.error("FINDING_NO_APPROVAL_EVIDENCE", f"{f.id} cites {identifier} as approval evidence, but it is not in the "
                                                     f"decision log or the source inventory.", floc("approval evidence"))


def _snapshot_findings(project: Path, cycle: int) -> dict[str, str] | None:
    path = project / snapshot_path(cycle)
    if not path.is_file():
        return None
    return {f.id: f.title for f in read_findings(path)}


def _read_history(project: Path, path: Path, ev: Evaluation) -> list[Cycle]:
    out = []
    for table in _tables(path, "Cycle"):
        for line, row in table.dict_rows():
            cycle = number(col(row, "cycle"))
            if cycle is None:
                continue
            counts = {key: number(col(row, label)) or 0 for label, key in COUNT_FIELDS if label not in ("Open findings", "Findings raised")}
            date = col(row, "review date")
            version = col(row, "reviewed version")
            out.append(Cycle(cycle, date if ISO_DATE.match(date) else None, version or None, col(row, "reviewer"),
                             result_label(col(row, "overall result")), counts,
                             col(row, "snapshot") or snapshot_path(cycle), line))
    return sorted(out, key=lambda c: c.cycle)


def _check_history(ev: Evaluation, project: Path) -> None:
    """Every closed cycle is listed once and frozen in its snapshot; no finding disappears."""
    current = ev.cycle or 1
    listed = {}
    for c in ev.history:
        where = f"{REVIEW_FILE}:{c.line}"
        if c.cycle in listed:
            ev.error("HISTORY", f"Cycle {c.cycle} is listed twice in the cycle history.", where)
            continue
        listed[c.cycle] = c
        if c.cycle >= current:
            ev.error("HISTORY", f"The cycle history lists cycle {c.cycle}; it lists closed cycles only, and the current "
                                f"cycle is {current}.", where)
            continue
        snap = project / (c.snapshot or snapshot_path(c.cycle))
        if not snap.is_file():
            ev.error("HISTORY_SNAPSHOT", f"Cycle {c.cycle}'s snapshot {c.snapshot} does not exist; closed cycles are kept, "
                                         f"never deleted.", where)
            continue
        fields, _ = _header(snap)
        if number(fields.get("review cycle")) != c.cycle:
            ev.error("HISTORY_SNAPSHOT", f"{c.snapshot} records review cycle {fields.get('review cycle') or 'blank'}, not {c.cycle}.", where)
        mismatches = []
        for label, value in (("review date", c.date), ("reviewed version", c.version),
                             ("overall result", c.result)):
            stated = result_label(fields.get(label)) if label == "overall result" else fields.get(label, "") or None
            if (stated or None) != (value or None):
                mismatches.append(f"{label} {value or 'blank'} (snapshot: {stated or 'blank'})")
        for label, key in COUNT_FIELDS:
            if key in c.counts and number(fields.get(pr.norm_key(label))) != c.counts[key]:
                mismatches.append(f"{label.lower()} {c.counts[key]} (snapshot: {fields.get(pr.norm_key(label)) or 'blank'})")
        if mismatches:
            ev.error("HISTORY_MISMATCH", f"The history row for cycle {c.cycle} disagrees with its snapshot: "
                                         f"{'; '.join(mismatches)}. History is never rewritten.", where)
        titles = {f.id: f.title for f in ev.findings}
        for fid, title in (_snapshot_findings(project, c.cycle) or {}).items():
            if fid not in titles:
                ev.error("FINDING_DELETED", f"{fid} was recorded in cycle {c.cycle} and is missing from the review; "
                                            f"findings are never deleted — close them with a status.", where)
            elif re.sub(r"\W+", " ", title.lower()).strip() != re.sub(r"\W+", " ", titles[fid].lower()).strip():
                ev.warn("FINDING_RETITLED", f"{fid} was '{title}' in cycle {c.cycle} and is now '{titles[fid]}'; an ID "
                                            f"is never reused for a different problem.", where)
    for cycle in range(1, current):
        if cycle not in listed:
            ev.error("HISTORY", f"Cycle {cycle} is missing from the cycle history ('Cycle' table); close each cycle with "
                                f"tools/specification_review.py --start-cycle.")
    for snap in sorted(project.glob(pr.SPECIFICATION_REVIEW_HISTORY_GLOB)):
        match = re.search(r"cycle-(\d+)\.md$", snap.name)
        if match and int(match.group(1)) >= current:
            ev.error("HISTORY_SNAPSHOT", f"{pr.rel(project, snap)} freezes cycle {int(match.group(1))}, but the current "
                                         f"cycle is {current}.", pr.rel(project, snap))


def _check_conclusion(ev: Evaluation, at) -> None:
    """The stated result and counts are the ones the findings support."""
    if ev.stated_result not in (PASS, WARN, FAIL):
        ev.error("RESULT_NOT_CONCLUDED", f"The review's 'Overall result' is {ev.stated_result or 'blank'}; conclude PASS, "
                                         f"PASS WITH WARNINGS or FAIL (the findings support {ev.result}).", at("overall result"))
    elif ev.stated_result != ev.result:
        ev.error("RESULT_MISMATCH", f"The review states 'Overall result' {ev.stated_result}; its findings support "
                                    f"{ev.result}. Unresolved CRITICAL or MAJOR -> FAIL; open MINOR, OBSERVATION or "
                                    f"accepted risk -> PASS WITH WARNINGS; none -> PASS.", at("overall result"))
    for label, key in COUNT_FIELDS:
        stated = ev.fields.get(pr.norm_key(label))
        if stated is None:
            ev.error("COUNT_MISSING", f"The review does not state '{label}'.")
        elif number(stated) != ev.counts[key]:
            ev.error("COUNT_MISMATCH", f"The review states {label}: {stated or 'blank'}; the findings show {ev.counts[key]}.",
                     at(label))


def _check_candidates(ev: Evaluation, path: Path) -> None:
    dismissed: list[tuple[int, set[str], str]] = []
    for table in _tables(path, "Candidate"):
        for line, row in table.dict_rows():
            ids = set(pr.extract_ids(col(row, "artifacts") + " " + col(row, "candidate")))
            reason = col(row, "reason")
            if not ids:
                continue
            if not reason:
                ev.error("CANDIDATE_NO_REASON", f"Dismissed candidate {', '.join(sorted(ids))} has no reason.", f"{REVIEW_FILE}:{line}")
            dismissed.append((line, ids, reason))
    for candidate in ev.candidates:
        pair = set(candidate.ids)
        finding = next((f.id for f in ev.findings if pair <= set(f.affected)), None)
        if finding:
            candidate.disposition = finding
        elif any(pair <= ids and reason for _, ids, reason in dismissed):
            candidate.disposition = "dismissed"
        else:
            ev.error("CONTRADICTION_UNREVIEWED",
                     f"Possible contradiction between {candidate.ids[0]} and {candidate.ids[1]} ({candidate.detail}) is "
                     f"neither a finding nor dismissed with a reason. Contradictory statements are never two valid "
                     f"requirements: raise a finding, or record why they do not conflict.")


def _check_changes(ev: Evaluation, bundle) -> None:
    """A change approved after the review makes the review stale: propagation is re-reviewed, never assumed."""
    if not ev.review_date:
        return
    for change in bundle.changes:
        date = change.get("date")
        if change.get("status") not in ("APPROVED", "IMPLEMENTED_IN_PLAN") or not date or date <= ev.review_date:
            continue
        severity = change.get("computed_severity") or "LOW"
        message = (f"{change.get('change_id')} ({change.get('change_type') or 'change'}, {severity}) is dated {date}, after "
                   f"review cycle {ev.cycle} ({ev.review_date}). Re-review the specification in a new cycle and verify "
                   f"the change propagated: affected artifacts reviewed, stale items updated, READY items reset, "
                   f"traceability refreshed, roadmap reconsidered.")
        if severity == "LOW":
            ev.warn("CHANGE_AFTER_REVIEW", message, change.get("source_path") or REVIEW_FILE)
        else:
            ev.error("CHANGE_AFTER_REVIEW", message, change.get("source_path") or REVIEW_FILE)


def _check_safe_answer(ev: Evaluation, path: Path) -> None:
    """The review's answer to 'safe to use as the basis for backlog planning?' agrees with its result."""
    for table in _tables(path, "Review question"):
        for line, row in table.dict_rows():
            if pr.norm_key(col(row, "review question")).rstrip("?") != SAFE_QUESTION.rstrip("?"):
                continue
            answer = enum(col(row, "answer"))
            expected = "NO" if ev.result == FAIL else "YES"
            if answer in ANSWERS and answer != expected:
                ev.error("CONCLUSION_MISMATCH", f"The review answers '{REVIEW_QUESTIONS[-1]}' {answer}, but its result is "
                                                f"{ev.result}; the answer is {expected}.", f"{REVIEW_FILE}:{line}")


# --------------------------------------------------------------------------
# Machine handoff: specification-review.json
# --------------------------------------------------------------------------


def document(ev: Evaluation, schema_version: str, project_id: str) -> dict:
    """The computed review, as machine-handoff/specification-review.json. Never edited by hand."""
    cycles = [c.as_json() for c in ev.history if c.cycle < (ev.cycle or 1)]
    current = ev.current_cycle()
    if current is not None:
        cycles.append(current.as_json())
    return {
        "schema_version": schema_version,
        "project_id": project_id,
        "review_version": ev.reviewed_version,
        "review_cycle": ev.cycle or 0,
        "review_date": ev.review_date,
        "reviewer": ev.reviewer or None,
        "specification_author": ev.author or None,
        "overall_result": JSON_RESULT[ev.overall],
        "summary": {key: ev.counts[key] for key in ("critical", "major", "minor", "observation", "open", "accepted_risk",
                                                    "resolved", "rejected", "total", "resolved_since_previous")},
        "cycles": cycles,
        "findings": [f.as_json() for f in sorted(ev.findings, key=lambda f: pr.natural_key(f.id))],
        "issues": [i.message for i in ev.defects],
        "source_path": REVIEW_FILE if ev.exists else None,
    }


# --------------------------------------------------------------------------
# Review aid: candidates for the reviewer, never findings
# --------------------------------------------------------------------------

WEAK_CRITERIA = ["work well", "works well", "properly", "correctly", "as expected", "appropriate", "appropriately",
                 "user-friendly", "user friendly", "secure", "securely", "fast", "quickly", "easily", "easy", "intuitive",
                 "robust", "seamless", "efficient", "reasonable", "etc", "and so on", "should", "good", "nice"]
NEGATIVE = re.compile(r"\b(reject|rejected|deny|denied|error|invalid|fail|fails|failed|not allowed|cannot|unauthori[sz]ed|"
                      r"expired|refus|blocked|locked|unchanged|prevent|no email|not sent)", re.IGNORECASE)
SCENARIOS = [
    ("failure", r"\b(fail\w*|error\w*|cannot|unable|rejected)\b"),
    ("validation error", r"\b(invalid|validation|incorrect|malformed|missing|not recogni[sz]ed|no active)\b"),
    ("permission denied", r"\b(permission|denied|not allowed|unauthori[sz]ed|forbidden|only the|only an?)\b"),
    ("external service unavailable", r"\b(unavailable|outage|not respond\w*|service is down|delay\w*|offline)\b"),
    ("duplicate action", r"\b(duplicate\w*|already|twice|second time|repeat\w*|again)\b"),
    ("cancel", r"\b(cancel\w*|abandon\w*|withdraw\w*)\b"),
    ("retry", r"\b(retr(?:y|ies|ied)|resend\w*|try again)\b"),
    ("timeout", r"\b(time ?out|expire\w*|expir\w+|time limit)\b"),
    ("empty state", r"\b(empty|no results?|none found|nothing to|no active|no records?)\b"),
    ("invalid state transition", r"\b(already used|invalid state|not allowed in|cannot be (?:moved|changed|reopened)|used)\b"),
]
EXTERNAL = re.compile(r"\b(service|external|integration|provider|gateway|third[- ]party|email|notification)\b|"
                      r"\b(?:INT|IR|DEP)-[0-9]{3,}", re.IGNORECASE)
TERM_GROUPS = [
    ["organization", "organisation", "company", "tenant", "workspace"],
    ["booking", "reservation", "appointment"],
    ["customer", "client", "buyer"],
    ["employee", "staff member", "worker"],
]
SECURITY_CONCERNS = ["Authentication", "Authorization model", "Multi-tenancy", "Security architecture", "Data ownership"]
INACTIVE_ADR = {"rejected", "superseded", "deprecated"}
CODE_AREAS = [
    ("Independent traceability", ("ORPHAN_", "UNKNOWN_REFERENCE", "NO_BUSINESS_SOURCE", "NO_GOAL_SOURCE",
                                  "REQUIREMENT_NOT_REALISED", "REQUIREMENT_WITHOUT_", "TRACEABILITY_MISMATCH", "LEGACY_ID",
                                  "UNDEFINED_ID_IN_DOCUMENT")),
    ("Architecture consistency", ("ADR_", "ARCHITECTURE_CONFLICT")),
    ("Roadmap consistency", ("PHASE_ORDER", "UNSUPPORTED_COMMITMENT", "IMPOSSIBLE_SEQUENCING", "BLOCKED_BY_DECISION",
                             "HIDDEN_PREREQUISITE", "DEPENDENCY_CYCLE", "FEATURE_DEPENDENCY_CYCLE", "UNQUALIFIED_DATE",
                             "PRIORITY_")),
    ("Scope consistency", ("TASK_ON_EXCLUDED_REQUIREMENT", "CONFIRMED_NOT_APPROVED")),
    ("Change consistency", ("CHANGE_", "READINESS_MISMATCH")),
    ("Acceptance criteria", ("EMPTY_ACCEPTANCE_CRITERIA",)),
]


def _in_release(req: dict) -> bool:
    return req.get("status") in LIVE and req.get("scope") in (None, "in_scope")


def _implementable(req: dict) -> bool:
    return pr.kind_of(req.get("id", "")) in pr.IMPLEMENTABLE_KINDS


def _upstream(rid: str, bundle, seen: set[str] | None = None) -> set[str]:
    """Every requirement ``rid`` derives from, followed through the records themselves."""
    seen = set() if seen is None else seen
    for parent in bundle.req_by_id.get(rid, {}).get("source") or []:
        if parent not in seen:
            seen.add(parent)
            _upstream(parent, bundle, seen)
    return seen


def _traceability(bundle) -> list[str]:
    out = []
    reqs = bundle.requirements
    for req in reqs:
        rid = req["id"]
        if _in_release(req) and _implementable(req) and not any(pr.kind_of(u) == "BR" for u in _upstream(rid, bundle)):
            out.append(f"{rid} does not trace to a business requirement (BR).")
        if _in_release(req) and pr.kind_of(rid) == "BR" and not any(pr.kind_of(u) == "GOAL" for u in req.get("source") or []):
            out.append(f"{rid} does not trace to a business goal (GOAL).")
        for label, ids in (("derives from", req.get("source")), ("depends on", req.get("dependencies")),
                           ("maps to", req.get("related_modules"))):
            for ref in ids or []:
                if bundle.known(ref) is False:
                    out.append(f"{rid} {label} {ref}, which no record defines.")
                elif req.get("status") in LIVE and bundle.req_by_id.get(ref, {}).get("status") in ("superseded", "rejected"):
                    out.append(f"{rid} {label} {ref}, which is {bundle.req_by_id[ref]['status'].upper()}.")
        if _in_release(req) and _implementable(req) and not req.get("related_modules"):
            out.append(f"{rid} is in scope but maps to no module.")
    for feature in bundle.features:
        fid = feature["id"]
        live = [r for r in feature.get("requirement_ids") or [] if _in_release(bundle.req_by_id.get(r, {}))]
        if feature.get("scope") == "in_scope" and not live:
            out.append(f"{fid} is in scope but maps to no live, in-scope requirement.")
        for ref in feature.get("requirement_ids") or []:
            req = bundle.req_by_id.get(ref)
            if req is None:
                out.append(f"{fid} names {ref}, which no record defines.")
            elif req.get("status") in ("superseded", "rejected"):
                out.append(f"{fid} names {ref}, which is {req['status'].upper()}.")
            elif req.get("scope") in ("out_of_scope", "future") and feature.get("scope") == "in_scope":
                out.append(f"In-scope {fid} names {ref}, which is {req['scope'].replace('_', ' ').upper()}.")
    if bundle.features:
        delivered = {r for f in bundle.features for r in f.get("requirement_ids") or []}
        for req in reqs:
            if _in_release(req) and _implementable(req) and req["id"] not in delivered:
                out.append(f"{req['id']} is in scope but no feature delivers it.")
    for task in bundle.tasks:
        for ref in task.get("source_requirements") or []:
            req = bundle.req_by_id.get(ref)
            if req is None:
                out.append(f"{task['id']} implements {ref}, which no record defines.")
            elif task.get("status") != "DEFERRED" and (req.get("status") in ("superseded", "rejected")
                                                       or req.get("scope") in ("out_of_scope", "future")):
                out.append(f"{task['id']} implements {ref}, which is excluded ({req.get('status')}, {req.get('scope')}).")
    for item in list(reqs) + list(bundle.features) + list(bundle.tasks):
        for link in item.get("architecture_decisions") or []:
            adr = bundle.adr_by_id.get(link.get("id"))
            own = {"requirement", "feature", "task"} & set(link.get("applies_via") or [])
            if adr is None:
                out.append(f"{item['id']} names {link.get('id')}, which no ADR record defines.")
            elif own and adr.get("status") in INACTIVE_ADR:
                successor = adr.get("superseded_by")
                out.append(f"{item['id']} names {adr['id']}, which is {adr['status'].upper()}"
                           + (f"; its successor is {successor}." if successor else "."))
    return out


def _assumptions(bundle) -> list[str]:
    out = []
    for asm in bundle.assumptions:
        if asm.get("status") != "OPEN":
            continue
        for ref in asm.get("affected_ids") or []:
            req = bundle.req_by_id.get(ref)
            if req and req.get("status") in LIVE:
                out.append(f"{ref} is {req['status'].upper()} ({(req.get('scope') or 'unscoped').replace('_', ' ')}) and "
                           f"rests on OPEN {asm['id']} ('{asm.get('statement')}'). Is it presented as confirmed?")
    for item in list(bundle.processes) + list(bundle.entities):
        if item.get("confidence") in ("assumption", "likely", "unknown"):
            out.append(f"{item['id']} is modelled on {item['confidence']} information.")
    return out


def _criteria(bundle) -> list[str]:
    out = []
    for req in bundle.requirements:
        if not _in_release(req):
            continue
        for criterion in req.get("acceptance_criteria") or []:
            lowered = f" {criterion.lower()} "
            weak = [w for w in WEAK_CRITERIA if re.search(rf"(?<![\w-]){re.escape(w)}(?![\w-])", lowered)]
            if weak:
                out.append(f"{req['id']}: '{criterion}' uses {', '.join(repr(w) for w in weak)}: observable and testable?")
        if req.get("type") == "functional" and req.get("acceptance_criteria") and \
                not NEGATIVE.search(" ".join(req["acceptance_criteria"])):
            out.append(f"{req['id']}: no acceptance criterion covers a denial, error or failure.")
    return out


def _scenarios(bundle) -> list[str]:
    out = []
    for proc in bundle.processes:
        if proc.get("perspective") == "as_is":
            continue
        body = " ".join([proc.get("preconditions") or "", " ".join(proc.get("main_flow") or []),
                         " ".join(proc.get("alternative_flows") or []), " ".join(proc.get("exceptions") or []),
                         proc.get("result") or ""])
        covered, missing = [], []
        for name, pattern in SCENARIOS:
            if name == "external service unavailable" and not EXTERNAL.search(body + " " + (proc.get("title") or "")):
                continue
            (covered if re.search(pattern, body, re.IGNORECASE) else missing).append(name)
        out.append(f"{proc['id']} ({proc.get('title')}): mentions {', '.join(covered) or 'none'}; does not mention "
                   f"{', '.join(missing) or 'none'}.")
    return out


def _security(bundle) -> list[str]:
    out = []
    for req in bundle.requirements:
        if _in_release(req) and req.get("type") == "functional" and not req.get("permissions"):
            out.append(f"{req['id']} does not say who may and may not perform it.")
    if not any(pr.kind_of(r["id"]) == "SR" and r.get("status") in LIVE for r in bundle.requirements):
        out.append("No live security requirement (SR) is recorded; confirm that none is needed, or raise a question.")
    coverage = {pr.norm_key(c.get("concern", "")): c for c in bundle.coverage}
    for concern in SECURITY_CONCERNS:
        row = coverage.get(pr.norm_key(concern))
        status = (row or {}).get("status") or "not assessed"
        if status not in ("decided", "not_applicable", "delegated"):
            out.append(f"Architecture concern '{concern}' is {status.replace('_', ' ').upper()}.")
    for ent in bundle.entities:
        missing = [label for label, key in (("ownership", "owner"), ("permissions", "permissions")) if not ent.get(key)]
        if missing:
            out.append(f"{ent['id']} ({ent.get('name')}) does not state {' or '.join(missing)}.")
    return out


def _risked(bundle) -> set[str]:
    return {i for risk in bundle.risks for i in risk.get("affected_ids") or []}


def _integrations(bundle) -> list[str]:
    out = []
    risked = _risked(bundle)
    for req in bundle.requirements:
        if _in_release(req) and pr.kind_of(req["id"]) == "IR":
            out.append(f"{req['id']} ({req.get('title')}): purpose, owner, inputs, outputs, authentication, failure, "
                       f"timeout and retry, fallback and data ownership stated?"
                       + ("" if req["id"] in risked else " No risk in the register names it."))
    for dep in bundle.dependencies:
        out.append(f"{dep['id']} ({dep.get('description')}) is {dep.get('status')}"
                   + ("." if dep["id"] in risked else "; no risk in the register names it."))
    return out


def _architecture(bundle) -> list[str]:
    out = []
    for adr in bundle.adrs:
        if adr.get("status") == "proposed":
            bound = [r["id"] for r in bundle.requirements
                     if adr["id"] in {link.get("id") for link in r.get("architecture_decisions") or []}]
            out.append(f"{adr['id']} ({adr.get('title')}) is PROPOSED" + (f" and binds {', '.join(bound)}" if bound else "")
                       + ": nothing may rely on it as decided.")
    for row in bundle.coverage:
        if row.get("status") == "decision_required":
            out.append(f"ARCHITECTURE DECISION REQUIRED: '{row.get('concern')}' "
                       f"({', '.join(row.get('question_ids') or []) or 'no question'}).")
    return out


def _risks(bundle) -> list[str]:
    out = []
    risked = _risked(bundle)
    for dep in bundle.dependencies:
        if dep["id"] not in risked:
            out.append(f"External dependency {dep['id']} has no risk in the register.")
    for req in bundle.requirements:
        if _in_release(req) and pr.kind_of(req["id"]) == "IR" and req["id"] not in risked:
            out.append(f"Integration requirement {req['id']} has no risk in the register.")
    for adr in bundle.adrs:
        if adr.get("status") in ("accepted", "proposed") and adr.get("risks") and not adr.get("risk_ids"):
            out.append(f"{adr['id']} states risks but links no RISK-### in the register.")
    return out


def _terminology(bundle) -> list[str]:
    texts = {r["id"]: _requirement_text(r) for r in bundle.requirements if r.get("status") in LIVE}
    texts.update({p["id"]: " ".join([p.get("title") or "", p.get("actors") or "", " ".join(p.get("main_flow") or [])])
                  for p in bundle.processes})
    texts.update({e["id"]: " ".join([e.get("name") or "", e.get("purpose") or ""]) for e in bundle.entities})
    out = []
    for group in TERM_GROUPS:
        used = {}
        for term in group:
            where = [i for i, t in texts.items() if re.search(rf"\b{re.escape(term)}s?\b", t, re.IGNORECASE)]
            if where:
                used[term] = where
        if len({t.replace("organisation", "organization") for t in used}) > 1:
            out.append("; ".join(f"'{t}' in {', '.join(sorted(ids, key=pr.natural_key)[:4])}" for t, ids in used.items())
                       + ". One concept or distinct ones? Define the distinction or use one term.")
    return out


def _data(bundle) -> list[str]:
    out = []
    names: dict[str, str] = {}
    for ent in bundle.entities:
        key = _stem(re.sub(r"\W+", " ", (ent.get("name") or "").lower()).strip())
        if key in names:
            out.append(f"{ent['id']} and {names[key]} have the same name; one concept under two IDs?")
        names.setdefault(key, ent["id"])
        if not ent.get("states"):
            out.append(f"{ent['id']} ({ent.get('name')}) states no lifecycle.")
    for proc in bundle.processes:
        for ref in proc.get("data_involved") or []:
            if bundle.known(ref) is False:
                out.append(f"{proc['id']} involves {ref}, which no entity record defines.")
    return out


def _changes(bundle, ev: Evaluation) -> list[str]:
    out = []
    summary = (bundle.changes_doc or {}).get("summary") or {}
    if any(summary.values()):
        out.append("Change state: " + ", ".join(f"{k.replace('_', ' ')} {v}" for k, v in summary.items()) + ".")
    for change in bundle.changes:
        if change.get("status") in ("APPROVED", "IMPLEMENTED_IN_PLAN"):
            unresolved = [a["id"] for a in change.get("affected") or [] if a.get("review_state") != "CURRENT"]
            late = ev.review_date and change.get("date") and change["date"] > ev.review_date
            out.append(f"{change['change_id']} ({change.get('status')}, {change.get('computed_severity')}, dated "
                       f"{change.get('date') or 'undated'}{', after the review' if late else ''}): {len(unresolved)} "
                       f"affected artifact(s) not CURRENT" + (f" ({', '.join(unresolved[:6])})" if unresolved else "") + ".")
    for entry in bundle.unrecorded:
        out.append(f"{entry['id']} was {entry.get('change')} since the baseline with no change record.")
    return out


def aid_sections(bundle, ev: Evaluation, tool_findings=None) -> list[tuple[str, str, list[str]]]:
    contradictions = [f"{c.ids[0]} / {c.ids[1]}: {c.detail}. Disposition: "
                      + (c.disposition if c.disposition.startswith("REVIEW") else
                         "dismissed in the review" if c.disposition else "**not yet judged** (gate GR fails until it is)")
                      for c in ev.candidates]
    sections = [
        ("Contradictions", "Pairs of live requirements whose wording may conflict (cardinality, deletion versus retention, "
                           "anonymous versus authenticated access). Each must be a finding or dismissed with a reason.",
         contradictions),
        ("Independent traceability", "Re-derived from the requirement, feature, task and ADR records, not read from the "
                                     "generated traceability files.", _traceability(bundle)),
        ("Assumptions", "Assumptions that live records rest on, and models built on unconfirmed information.",
         _assumptions(bundle)),
        ("Acceptance criteria", "Criteria with vague wording, and functional requirements with no negative criterion.",
         _criteria(bundle)),
        ("Missing scenarios", "Which scenario families each workflow mentions. Only the ones that make sense for the "
                              "workflow need to be specified; do not add meaningless edge cases.", _scenarios(bundle)),
        ("Permissions and authorisation", "Actions without permission rules, security concerns not decided, entities "
                                          "without ownership.", _security(bundle)),
        ("Integrations", "Every integration requirement and external dependency, with its risk-register coverage.",
         _integrations(bundle)),
        ("Architecture consistency", "Decisions that are not yet made.", _architecture(bundle)),
        ("Risks", "Dependencies, integrations and decisions that no risk records.", _risks(bundle)),
        ("Terminology", "Words that often name one concept, used side by side.", _terminology(bundle)),
        ("Data model", "Duplicate entity names, entities without lifecycle, references to undefined entities.", _data(bundle)),
        ("Change consistency", "Approved changes and what they left under review.", _changes(bundle, ev)),
    ]
    if tool_findings:
        grouped: dict[str, list[str]] = {}
        for finding in tool_findings:
            area = next((name for name, prefixes in CODE_AREAS if finding.code.startswith(prefixes)), None)
            if area:
                line = f"{finding.code}: {finding.message}" + (f" `{finding.location}`" if finding.location else "")
                if line not in grouped.setdefault(area, []):
                    grouped[area].append(line)
        for area, lines in grouped.items():
            sections.append((f"Tool findings: {area}", "Reported by the validator and generator.", lines))
    return sections


def aid_markdown(bundle, ev: Evaluation, when: str, tool_findings=None) -> str:
    sections = aid_sections(bundle, ev, tool_findings)
    project = bundle.project
    lines = ["# Specification Review Aid", "",
             "<!-- GENERATED by tools/specification_review.py and tools/check_gates.py. Do not edit: it is recomputed "
             "from the records. -->", "",
             f"Project: {project.get('name')} ({project.get('project_id')}) · Specification: {project.get('version') or 'TBD'} "
             f"· Review: cycle {ev.cycle or 0}, {ev.overall} · Evaluated: {when}", "",
             "Candidates for the SPECIFICATION REVIEWER to judge, computed from the records. Nothing here is a finding, "
             "and nothing here proves the specification sound: heuristics miss problems and raise false alarms. Record a "
             "real problem as a REVIEW-### finding with its evidence; dismiss a false alarm. Contradiction candidates are "
             "binding: gate GR fails until each is a finding or is dismissed with a reason in the review.", "",
             "| Area | Candidates |", "| --- | --- |"]
    lines += [f"| {title} | {len(items)} |" for title, _, items in sections]
    for title, note, items in sections:
        lines += ["", f"## {title}", "", note, ""]
        lines += [f"- {item}" for item in items] or ["None."]
    lines.append("")
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Closing a cycle
# --------------------------------------------------------------------------


def _row(cells: list[str]) -> str:
    return "| " + " | ".join(c.replace("|", "\\|") for c in cells) + " |"


def _history_value(header: str, ev: Evaluation) -> str:
    values = {"cycle": str(ev.cycle), "review date": ev.review_date or "", "reviewed version": ev.reviewed_version or "",
              "reviewer": ev.reviewer, "overall result": ev.result, "snapshot": snapshot_path(ev.cycle or 0)}
    values.update({pr.norm_key(label): str(ev.counts[key]) for label, key in COUNT_FIELDS})
    return values.get(header, "")


def _open_next_cycle(text: str, ev: Evaluation) -> str | None:
    """The review text for the next cycle: the header reopened, every check and question back to NOT REVIEWED,
    and the closed cycle appended to the history. Findings are left exactly as they are."""
    crlf = "\r\n" in text
    lines = text.replace("\r\n", "\n").split("\n")
    meaning = [line for _, line in pr._meaningful_lines("\n".join(lines))]
    meaning += [""] * (len(lines) - len(meaning))
    header_done = history_done = False
    index = 0
    while index < len(lines):
        if not (meaning[index].strip().startswith("|") and index + 1 < len(lines)
                and pr.TABLE_SEP_RE.match(meaning[index + 1])):
            index += 1
            continue
        headers = [pr.norm_key(h) for h in pr.split_row(lines[index])]
        end = index + 2
        while end < len(lines) and meaning[end].strip().startswith("|"):
            end += 1
        first = headers[0] if headers else ""
        result_col = next((i for i, h in enumerate(headers) if h in ("result", "answer")), None)
        evidence_col = next((i for i, h in enumerate(headers) if h.startswith("evidence")), None)
        for row in range(index + 2, end):
            cells = pr.split_row(lines[row])
            cells += [""] * (len(headers) - len(cells))
            if first == "field" and not header_done:
                key = pr.norm_key(cells[0])
                if key == "review cycle":
                    cells[1] = str((ev.cycle or 0) + 1)
                elif key in ("review date", "date"):
                    cells[1] = "TBD"
                elif key == "overall result":
                    cells[1] = NOT_REVIEWED
            elif first in ("area", "review question") and result_col is not None:
                cells[result_col] = NOT_REVIEWED
                if evidence_col is not None:
                    cells[evidence_col] = ""
            else:
                continue
            lines[row] = _row(cells)
        if first == "field":
            header_done = True
        if first == "cycle" and not history_done:
            lines.insert(end, _row([_history_value(h, ev) for h in headers]))
            meaning.insert(end, lines[end])
            end += 1
            history_done = True
        index = end
    if not history_done:
        return None
    out = "\n".join(lines)
    return out.replace("\n", "\r\n") if crlf else out


def start_cycle(project: Path, bundle) -> tuple[bool, list[str]]:
    """Freeze the current cycle in reviews/history/ and open the next one."""
    ev = evaluate(project, bundle)
    if not ev.exists:
        return False, [f"{REVIEW_FILE} does not exist; there is no cycle to close. Copy templates/12 first."]
    blocking = [i for i in ev.errors if i.code not in CYCLE_TOLERATED]
    if blocking:
        return False, [f"Cycle {ev.cycle or '?'} cannot be closed until its record is complete and coherent:"] + \
            [f"  {i.message} [{i.location}]" for i in blocking]
    target = project / snapshot_path(ev.cycle)
    if target.exists():
        return False, [f"{snapshot_path(ev.cycle)} already exists; a closed cycle is never overwritten."]
    path = project / REVIEW_FILE
    raw = path.read_bytes()
    reopened = _open_next_cycle(raw.decode("utf-8"), ev)
    if reopened is None:
        return False, [f"{REVIEW_FILE} has no cycle history table (first column 'Cycle'); copy it from templates/12."]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    path.write_bytes(reopened.encode("utf-8"))
    return True, [
        f"Closed review cycle {ev.cycle} ({ev.result}) and froze it in {snapshot_path(ev.cycle)}.",
        f"Opened review cycle {ev.cycle + 1}: every check and review question is NOT REVIEWED again, and the date is TBD.",
        "Next: the SPECIFICATION AUTHOR resolves findings in the records they belong to (never the reviewer, never by "
        "patching the specification alone). The SPECIFICATION REVIEWER then re-reviews every check, verifies each "
        "resolution (RESOLVED needs Closed in cycle, Resolved by, Resolution date, Changed artifacts and Verification), "
        "raises new findings with new IDs, dates the cycle and concludes.",
    ]


# --------------------------------------------------------------------------
# Command line
# --------------------------------------------------------------------------


def print_status(project_label: str, ev: Evaluation) -> None:
    c = ev.counts
    print(f"Specification review: {project_label}/{REVIEW_FILE}")
    if ev.exists:
        print(f"  Reviewed version: {ev.reviewed_version or 'unstated'} (specification: {ev.specification_version or 'unstated'})")
        print(f"  Review cycle: {ev.cycle or '?'} - {ev.review_date or 'undated'} - reviewer: {ev.reviewer or 'unnamed'}; "
              f"author: {ev.author or 'unnamed'}")
    print(f"  Result: {ev.overall}")
    print(f"  Open critical {c['critical']} | Open major {c['major']} | Open minor {c['minor']} | "
          f"Open observations {c['observation']} | Accepted risks {c['accepted_risk']}")
    print(f"  Resolved since previous review {c['resolved_since_previous']} | Findings raised {c['total']}")
    undisposed = [cand for cand in ev.candidates if not cand.disposition]
    print(f"  Contradiction candidates: {len(ev.candidates)} ({len(undisposed)} not yet judged)")
    if ev.issues:
        print("\nIssues:")
        for issue in ev.issues:
            label = "FAIL" if issue.level == "error" else "WARN"
            print(f"  {label} {issue.message}" + (f" [{issue.location}]" if issue.location else ""))


def main(argv: list[str] | None = None) -> int:
    import datetime as _dt
    import json

    parser = argparse.ArgumentParser(description="Verify and summarise a project's independent specification review.")
    parser.add_argument("project", type=Path)
    parser.add_argument("--start-cycle", action="store_true",
                        help="Freeze the current cycle in reviews/history/ and open the next one")
    parser.add_argument("--json", action="store_true", help="Print the computed specification-review.json")
    parser.add_argument("--no-write", action="store_true", help=f"Do not write {AID_FILE}")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
        # Record text may hold characters a Windows console cannot encode; print them replaced, never crash.
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")

    project = args.project.resolve()
    if not (project / pr.STATE_FILE).is_file():
        print(f"{args.project} has no {pr.STATE_FILE}; is it a project folder?", file=sys.stderr)
        return 2
    import generate_handoff as gh  # imported here: the generator imports this module
    import validate_handoff as vh

    when = _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        docs, src, bundle = gh.build(project, when)
        _, json_findings, _ = gh.finalize(docs, src)
    except vh.SchemaUnavailable as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.start_cycle:
        ok, messages = start_cycle(project, bundle)
        print("\n".join(messages))
        return 0 if ok else 1
    ev = src.spec_review
    if args.json:
        print(json.dumps(docs["specification-review.json"], indent=2, ensure_ascii=False))
        return 0 if ev.overall in (PASS, WARN) else 1
    print_status(str(args.project), ev)
    if not args.no_write:
        target = project / AID_FILE
        target.parent.mkdir(exist_ok=True)
        target.write_text(aid_markdown(bundle, ev, when, src.findings.items + json_findings.items),
                          encoding="utf-8", newline="\n")
        print(f"\nWrote {AID_FILE}")
    return 0 if ev.overall in (PASS, WARN) else 1


if __name__ == "__main__":
    raise SystemExit(main())
