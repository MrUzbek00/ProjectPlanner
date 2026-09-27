#!/usr/bin/env python3
"""generate-machine-handoff: turn a project's Markdown records into validated JSON.

The Markdown records remain the source of truth. This tool reads their
structured parts (record blocks and register tables, see planning_records.py),
writes the machine-handoff contract under ``machine-handoff/``, validates it
with tools/validate_handoff.py, writes ``handoff-manifest.json`` (the entry
point for a downstream engineering system, see tools/handoff_contract.py), and
writes the human-readable chain view ``traceability/requirement-map.md`` from
the same data.

Steps, in order:
    1. validate the specification (identity, status, approval record, independent review)
    2. validate requirements
    3. validate backlog readiness (Definition of Ready for every task)
    4. generate the JSON artifacts
    5. validate them against schemas/
    6. validate traceability and references
    7. report blocked and non-ready tasks
    8. write the handoff manifest and print the handoff summary

Usage:
    python tools/generate_handoff.py projects/<project>
    python tools/generate_handoff.py projects/<project> --check
    python tools/generate_handoff.py projects/<project> --generated-at 2026-09-26T10:00:00Z

Exit codes: 0 valid (warnings allowed), 1 validation errors, 2 cannot run.
The handoff is written even when invalid, with handoff_status "invalid", so
that no earlier "ready" output survives next to changed sources.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import backlog_readiness as br  # noqa: E402
import change_impact as ci  # noqa: E402
import handoff_contract as hc  # noqa: E402
import planning_records as pr  # noqa: E402
import specification_review as sr  # noqa: E402
import validate_handoff as vh  # noqa: E402

GENERATOR_NAME = "project-planning-workflow/generate_handoff"
GENERATOR_VERSION = "1.5.0"
OUTPUT_DIR = "machine-handoff"
REQUIREMENT_MAP = "traceability/requirement-map.md"

STEP_GENERATE = "4-generate"
REQ_TYPE = {
    "GOAL": "business_goal", "BR": "business", "RULE": "business_rule", "FR": "functional", "NFR": "non_functional",
    "DR": "data", "IR": "integration", "SR": "security", "UXR": "ux", "TR": "technical",
}
REQ_STATUS = {"draft": "draft", "confirmed": "confirmed", "approved": "approved", "superseded": "superseded",
              "rejected": "rejected"}
SCOPE = {
    "in scope": "in_scope", "in": "in_scope", "out of scope": "out_of_scope", "out": "out_of_scope",
    "future": "future", "pending decision": "pending_decision", "pending": "pending_decision",
    "pending approval": "pending_decision",
}
CONFIDENCE = {"confirmed": "confirmed", "likely": "likely", "assumption": "assumption", "assumed": "assumption",
              "unknown": "unknown"}
QUESTION_PRIORITY = ("BLOCKER", "HIGH", "MEDIUM", "LOW")
RISK_LEVELS = {"high", "medium", "low", "unknown"}
RISK_CATEGORIES = {"scope", "technical", "business", "dependency", "integration", "security", "data", "timeline",
                   "stakeholder", "other"}
RISK_STATUS = {"OPEN", "MITIGATING", "ACCEPTED", "CLOSED", "OCCURRED"}
DEPENDENCY_STATUS = {"AVAILABLE", "PENDING", "UNAVAILABLE", "UNKNOWN"}
DEPENDENCY_TYPES = {"external system": "external_system", "external_system": "external_system", "system": "external_system",
                    "department": "department", "vendor": "vendor", "data": "data", "decision": "decision",
                    "other": "other"}
MODULE_TYPES = {"user-facing": "user_facing", "user facing": "user_facing", "administration": "administration",
                "admin": "administration", "integration": "integration", "external service": "external_service",
                "reporting": "reporting", "notification": "notification", "notifications": "notification",
                "platform": "platform", "other": "other"}
DATE_BASIS = {"target": "target", "estimate": "estimate", "commitment": "commitment", "none": "none"}
SPEC_STATUS = {
    "not started": "not_started", "draft": "draft", "in review": "in_review", "in_review": "in_review",
    "approved": "approved", "superseded": "superseded",
}
PRIORITY_LEVELS = ("critical", "high", "medium", "low")
PRIORITY_MOSCOW = ("must", "should", "could", "wont")
PRIORITIES = {*PRIORITY_LEVELS, *PRIORITY_MOSCOW, "unspecified"}
TASK_TYPES = {"backend", "frontend", "fullstack", "database", "integration", "infrastructure", "security",
              "testing", "documentation", "design", "other"}
TEST_LEVELS = {"unit", "integration", "contract", "e2e", "security", "performance", "accessibility",
               "migration", "manual", "uat"}
TEST_LEVEL_ALIASES = {"end-to-end": "e2e", "end to end": "e2e", "acceptance": "uat", "user acceptance": "uat"}
ADR_STATUS = {"proposed", "accepted", "rejected", "superseded", "deprecated"}
COVERAGE_STATUS = {"decided": "decided", "proposed": "proposed", "decision required": "decision_required",
                   "delegated": "delegated", "not applicable": "not_applicable", "n/a": "not_applicable",
                   "not assessed": "not_assessed"}
PRINCIPLE_STATUS = {"proposed": "proposed", "accepted": "accepted", "retired": "retired"}
CONSTRAINT_KINDS = ("architecture", "security", "performance", "data", "compliance")
QUESTION_STATUS = {"OPEN", "ANSWERED", "RESOLVED", "DEFERRED", "WITHDRAWN", "CLOSED"}
RESOLVED = {"ANSWERED", "RESOLVED", "WITHDRAWN", "CLOSED"}
TASK_CORE_SECTIONS = {"", "description", "acceptance criteria", "constraints", "goal", "objective", "readiness history",
                      "data impact", "database requirements", "api impact", "api requirements", "ui impact",
                      "ui requirements", "integration impact"}
# Where each impact is written on a task card: the impact section, or the older requirements section.
IMPACT_SECTIONS = {"data": ("data impact", "database requirements"), "api": ("api impact", "api requirements"),
                   "ui": ("ui impact", "ui requirements"), "integration": ("integration impact",)}
ISO_DATE = re.compile(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$")
AC_ITEM = re.compile(rf"^(?P<id>{pr.ID_PATTERNS['AC']})\s*(?:—|–|-|:)\s*(?P<text>.+)$")


class Source:
    """Source-level parsing with findings located at file:line."""

    def __init__(self, project: Path):
        self.project = project
        self.findings = vh.Findings()
        self.spec_review: sr.Evaluation | None = None

    def loc(self, path: Path, line: int | None = None) -> str:
        where = pr.rel(self.project, path)
        return f"{where}:{line}" if line else where

    def rloc(self, record: pr.Record, key: str | None = None) -> str:
        line = record.field_lines.get(pr.norm_key(key)) if key else None
        return self.loc(record.path, line or record.line)


# --------------------------------------------------------------------------
# Field helpers
# --------------------------------------------------------------------------


def ids_in(value: str | None, *kinds: str) -> list[str]:
    return pr.extract_ids(pr.clean(value or ""), kinds or None)


def first_id(value: str | None, kind: str) -> str | None:
    found = ids_in(value, kind)
    return found[0] if found else None


def norm_enum(value: str | None) -> str:
    return re.sub(r"\s+", " ", pr.clean(value or "").split("—")[0].split(" - ")[0].split("(")[0]).strip()


def section_text(section: pr.Section | None) -> str:
    if section is None:
        return ""
    parts = [section.text] if section.text else []
    parts += [f"- {pr.clean(item)}" for item in section.items]
    return "\n".join(parts).strip()


def criteria(section: pr.Section | None) -> list[str]:
    """Acceptance criteria from list items or a table, as 'AC-###: text'."""
    if section is None:
        return []
    out: list[str] = []
    for item in section.items:
        text = pr.clean(item)
        match = AC_ITEM.match(text)
        out.append(f"{match.group('id')}: {match.group('text').strip()}" if match else text)
    for table in section.tables:
        keys = table.keys()
        for _, row in table.dict_rows():
            ac_id = pr.clean(row.get("ac id", ""))
            given = pr.clean(row.get("given", ""))
            when = pr.clean(row.get("when", ""))
            then = next((pr.clean(v) for k, v in row.items() if k.startswith("then")), "")
            plain = next((pr.clean(row[k]) for k in keys if k in ("criterion", "acceptance criterion", "description")), "")
            if given or when or then:
                text = ", ".join(p for p in (f"Given {given}" if given else "", f"when {when}" if when else "",
                                             f"then {then}" if then else "") if p)
            else:
                text = plain
            if not text:
                continue
            out.append(f"{ac_id}: {text}" if pr.FULL_ID_RE["AC"].match(ac_id) else text)
    return [c for c in out if c]


def priority(src: Source, record: pr.Record, step: str = vh.STEP_REQ) -> tuple[str, bool]:
    raw = record.field("priority")
    value = norm_enum(raw).lower().replace("’", "").replace("'", "")
    if not value or pr.has_tbd(raw or ""):
        value = "unspecified"
    elif value not in PRIORITIES:
        src.findings.error(step, "INVALID_VALUE",
                           f"{record.id}: priority {raw!r} is not one of Critical, High, Medium, Low or "
                           f"Must, Should, Could, Won't (or Unspecified).",
                           src.rloc(record, "priority"))
    basis = pr.clean(record.field("priority basis") or "").lower()
    return value, basis.startswith("confirmed")


def question_mentions(record: pr.Record) -> list[str]:
    return pr.extract_ids(record.raw, ("Q",))


def mapped(src: Source, raw: str | None, mapping: dict, what: str, where: str, step: str,
           record_id: str = "") -> str | None:
    """Normalize an enumerated field. Blank or TBD is None (not yet classified);
    anything else outside the mapping is an error and is passed through so the
    schema reports it too."""
    value = norm_enum(raw).lower().replace("_", " ")
    if not value or pr.has_tbd(raw or ""):
        return None
    if value in mapping:
        return mapping[value]
    allowed = ", ".join(sorted({k.title() for k in mapping}))
    src.findings.error(step, "INVALID_VALUE", f"{record_id + ': ' if record_id else ''}{what} {raw!r} is not one of {allowed}.", where)
    return value


def record_field_enum(src: Source, record: pr.Record, names: tuple[str, ...], mapping: dict, what: str,
                      step: str) -> str | None:
    return mapped(src, record.field(*names), mapping, what, src.rloc(record, names[0]), step, record.id)


def text_field(record: pr.Record, *names: str) -> str:
    """A field value, or the section of the same name when it is written as prose."""
    value = pr.clean(record.field(*names) or "")
    return value or section_text(record.section(*names))


def items_field(record: pr.Record, *names: str) -> list[str]:
    """A list: the items of a section of that name, or a field split on ';' or new lines."""
    section = record.section(*names)
    if section and section.items:
        return [pr.clean(i) for i in section.items]
    value = pr.clean(record.field(*names) or "") or (section.text if section else "")
    if not value or pr.is_none(value):
        return []
    return [part.strip() for part in re.split(r"[;\n]", value) if part.strip()]


# --------------------------------------------------------------------------
# Readers
# --------------------------------------------------------------------------


def read_state(src: Source) -> dict:
    path = src.project / pr.STATE_FILE
    state = {"project_id": None, "name": None, "version": None, "status": "not_started", "language": None,
             "approval": None, "priority_scheme": None}
    if not path.is_file():
        src.findings.error(vh.STEP_SPEC, "MISSING_SOURCE", "project-state.md not found.", pr.STATE_FILE)
        return state
    tables = pr.read_tables(path)
    fields: dict[str, tuple[str, int]] = {}
    for table in tables:
        if table.keys()[:1] == ["field"]:
            for line, row in table.dict_rows():
                keys = list(row)
                fields[pr.norm_key(row[keys[0]])] = (pr.clean(row[keys[1]]) if len(keys) > 1 else "", line)
            break

    def value(*names: str) -> tuple[str, int | None]:
        for name in names:
            if name in fields:
                return fields[name]
        return "", None

    project_id, line = value("project id", "project id / folder")
    project_id = project_id.split("/")[0].strip()
    if not project_id or pr.has_tbd(project_id) or not re.match(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*$", project_id):
        src.findings.error(vh.STEP_SPEC, "MISSING_PROJECT_ID",
                           f"'Project ID' must be an upper-case identifier such as ACME or PROJECT-001 (found {project_id!r}).",
                           src.loc(path, line))
    state["project_id"] = project_id or None
    name, line = value("project name")
    if not name or pr.has_tbd(name):
        src.findings.error(vh.STEP_SPEC, "MISSING_PROJECT_NAME", "'Project name' is blank or TBD.", src.loc(path, line))
    state["name"] = name or None
    state["language"] = value("document language")[0] or None
    scheme_raw, scheme_line = value("priority scheme")
    scheme = norm_enum(scheme_raw).lower()
    if scheme and not pr.has_tbd(scheme_raw):
        if scheme.startswith("moscow") or scheme.startswith("must"):
            state["priority_scheme"] = "moscow"
        elif scheme.startswith("level") or scheme.startswith("critical"):
            state["priority_scheme"] = "levels"
        else:
            src.findings.error(vh.STEP_SPEC, "INVALID_VALUE",
                               f"Priority scheme {scheme_raw!r} is not MoSCoW or Levels.", src.loc(path, scheme_line))

    version, _ = value("specification version")
    status_raw, status_line = value("specification status")
    if not version and not status_raw:
        combined, status_line = value("current specification version / status")
        version, _, status_raw = combined.partition("/")
    version = version.strip()
    state["version"] = None if not version or pr.has_tbd(version) or pr.is_none(version) else version
    status_key = norm_enum(status_raw).lower().replace("_", " ")
    if status_key in SPEC_STATUS:
        state["status"] = SPEC_STATUS[status_key]
    else:
        src.findings.error(vh.STEP_SPEC, "INVALID_VALUE",
                           f"Specification status {status_raw!r} is not one of NOT STARTED, DRAFT, IN REVIEW, APPROVED, SUPERSEDED.",
                           src.loc(path, status_line))

    for table in tables:
        if table.keys()[:1] != ["approval id"]:
            continue
        for line, row in table.dict_rows():
            approved_version = pr.clean(next((v for k, v in row.items() if k.startswith("specification version")), ""))
            approver = pr.clean(next((v for k, v in row.items() if k.startswith("approver")), ""))
            if state["version"] and approved_version == state["version"] and approver:
                state["approval"] = {
                    "approval_id": pr.clean(row.get("approval id", "")),
                    "approved_by": approver,
                    "approved_on": pr.clean(row.get("date", "")),
                    "specification_version": approved_version,
                }
    if state["status"] == "approved" and state["approval"] is None:
        src.findings.error(vh.STEP_SPEC, "SPEC_APPROVAL_MISSING",
                           f"Specification status is APPROVED but the approval record has no row for version {state['version']!r} with an approver.",
                           pr.STATE_FILE)
    return state


def read_registers(src: Source, kind_key: str, headers: tuple[str, ...], kind: str) -> list[tuple[str, int, dict]]:
    rows: list[tuple[str, int, dict]] = []
    seen: dict[str, str] = {}
    for rel in pr.REGISTER_FILES[kind_key]:
        path = src.project / rel
        if not path.is_file():
            continue
        for line, row in pr.read_register(path, headers, kind):
            identifier = row["__id__"]
            where = src.loc(path, line)
            if identifier in seen:
                src.findings.error(vh.STEP_REQ, "DUPLICATE_ID", f"{identifier} is also defined at {seen[identifier]}.", where)
                continue
            seen[identifier] = where
            rows.append((where, line, row))
    return rows


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


def read_questions(src: Source) -> list[dict]:
    out = []
    for where, _, row in read_registers(src, "questions", ("Question ID", "Q ID"), "Q"):
        status_raw = col(row, "status")
        status = norm_enum(status_raw).upper().replace(" ", "_") or "OPEN"
        if status not in QUESTION_STATUS:
            src.findings.error(vh.STEP_REQ, "INVALID_VALUE",
                               f"{row['__id__']}: status {status_raw!r} is not one of {', '.join(sorted(QUESTION_STATUS))}.", where)
        priority_raw = col(row, "priority")
        question_priority = norm_enum(priority_raw).upper()
        if not question_priority:
            # Older registers carried a Yes/No "Blocking?" column instead.
            blocking_raw = col(row, "blocking? / rationale", "blocking?", "blocking").lower()
            question_priority = "MEDIUM" if blocking_raw.startswith("no") else "BLOCKER"
            if not blocking_raw:
                src.findings.error(vh.STEP_REQ, "MISSING_FIELD",
                                   f"{row['__id__']}: Priority is blank; it is treated as BLOCKER until set.", where)
        elif question_priority not in QUESTION_PRIORITY:
            src.findings.error(vh.STEP_REQ, "INVALID_VALUE",
                               f"{row['__id__']}: priority {priority_raw!r} is not one of BLOCKER, HIGH, MEDIUM, LOW.", where)
        out.append({
            "id": row["__id__"],
            "question": col(row, "focused question", "question for the user", "missing decision / question", "question"),
            "why_it_matters": col(row, "why it matters", "why this answer matters"),
            "priority": question_priority,
            "blocking": question_priority == "BLOCKER",
            "category": col(row, "category", "discovery category"),
            "affected_ids": pr.extract_ids(col(row, "affected requirement/artifact ids", "affected requirement / artifact ids", "affected ids", "affected")),
            "owner": col(row, "decision owner", "owner"),
            "status": status,
            "resolved": status in RESOLVED,
            "resolution": col(row, "answer / source / decision", "resolution / deferral authority", "resolution"),
        })
    return out


def read_decisions(src: Source) -> list[dict]:
    out = []
    for _, _, row in read_registers(src, "decisions", ("Decision ID", "DEC ID"), "DEC"):
        related = col(row, "related requirements", "affected ids / files", "affected ids")
        out.append({
            "id": row["__id__"],
            "date": col(row, "date"),
            "question": col(row, "question"),
            "options": col(row, "options considered", "alternatives considered", "alternatives", "options"),
            "decision": col(row, "decision"),
            "rationale": col(row, "rationale"),
            "impact": col(row, "impact"),
            "approved_by": col(row, "approved by", "decision maker / authority", "decision maker", "authority"),
            "related_requirements": pr.extract_ids(related, pr.REQUIREMENT_KINDS),
            "affected_ids": pr.extract_ids(" ".join([related, col(row, "affected ids / files", "affected ids", "impact")])),
            "supersedes": pr.extract_ids(col(row, "supersedes"), ("DEC",)),
        })
    return out


def read_risks(src: Source) -> list[dict]:
    out = []
    for where, _, row in read_registers(src, "risks", ("Risk ID",), "RISK"):
        rid = row["__id__"]

        def level(name: str) -> str:
            value = norm_enum(col(row, name)).lower() or "unknown"
            if value not in RISK_LEVELS:
                src.findings.error(vh.STEP_REQ, "INVALID_VALUE", f"{rid}: {name} {value!r} is not High, Medium, Low or Unknown.", where)
            return value

        category = norm_enum(col(row, "category")).lower() or "other"
        if category not in RISK_CATEGORIES:
            src.findings.error(vh.STEP_REQ, "INVALID_VALUE", f"{rid}: category {category!r} is not one of {', '.join(sorted(RISK_CATEGORIES))}.", where)
        status = norm_enum(col(row, "status")).upper() or "OPEN"
        if status not in RISK_STATUS:
            src.findings.error(vh.STEP_REQ, "INVALID_VALUE", f"{rid}: status {status!r} is not one of {', '.join(sorted(RISK_STATUS))}.", where)
        out.append({
            "id": rid,
            "description": col(row, "description", "risk / cause", "risk"),
            "category": category,
            "probability": level("probability"),
            "impact": level("impact"),
            "mitigation": col(row, "mitigation"),
            "owner": col(row, "owner"),
            "status": status,
            "affected_ids": pr.extract_ids(col(row, "affected ids", "affected")),
            "blocks_readiness": norm_enum(col(row, "blocks readiness")).lower() in ("yes", "true", "y"),
        })
    return out


def read_dependencies(src: Source) -> list[dict]:
    out = []
    for where, _, row in read_registers(src, "dependencies", ("Dependency ID", "DEP ID"), "DEP"):
        rid = row["__id__"]
        status = norm_enum(col(row, "status", "current availability")).upper() or "UNKNOWN"
        if status not in DEPENDENCY_STATUS:
            src.findings.error(vh.STEP_BACKLOG, "INVALID_VALUE", f"{rid}: status {status!r} is not AVAILABLE, PENDING, UNAVAILABLE or UNKNOWN.", where)
        dtype = mapped(src, col(row, "type"), DEPENDENCY_TYPES, "type", where, vh.STEP_BACKLOG, rid) or "other"
        out.append({
            "id": rid,
            "description": col(row, "description", "department / system / input", "dependency"),
            "type": dtype,
            "owner": col(row, "owner"),
            "status": status,
            "needed_for": pr.extract_ids(col(row, "needed for", "needed for requirement or stage")),
            "risk_ids": pr.extract_ids(col(row, "related risk / question", "risk ids", "related risk"), ("RISK",)),
        })
    return out


def read_scope_items(src: Source) -> list[dict]:
    path = src.project / pr.SCOPE_FILE
    if not path.is_file():
        return []
    out, seen = [], set()
    for line, row in pr.read_register(path, ("Scope ID",), "SCOPE"):
        where = src.loc(path, line)
        if row["__id__"] in seen:
            src.findings.error(vh.STEP_REQ, "DUPLICATE_ID", f"{row['__id__']} is defined more than once.", where)
            continue
        seen.add(row["__id__"])
        out.append({
            "id": row["__id__"],
            "item": col(row, "item", "scope item"),
            "classification": mapped(src, col(row, "classification", "scope"), SCOPE, "classification", where,
                                     vh.STEP_REQ, row["__id__"]) or "pending_decision",
            "related_ids": pr.extract_ids(col(row, "related ids", "related")),
            "rationale": col(row, "rationale", "reason"),
            "authority": col(row, "authority", "decision", "authority / decision"),
        })
    return out


def read_assumptions(src: Source) -> list[dict]:
    out = []
    for where, _, row in read_registers(src, "assumptions", ("ASM ID",), "ASM"):
        status_raw = col(row, "status")
        status = norm_enum(status_raw).upper() or "OPEN"
        if status not in {"OPEN", "CONFIRMED", "REJECTED"}:
            src.findings.error(vh.STEP_REQ, "INVALID_VALUE", f"{row['__id__']}: status {status_raw!r} is not OPEN, CONFIRMED or REJECTED.", where)
        out.append({
            "id": row["__id__"],
            "statement": col(row, "provisional statement", "statement"),
            "risk_if_wrong": col(row, "risk if wrong"),
            "affected_ids": pr.extract_ids(col(row, "affected ids")),
            "question_ids": pr.extract_ids(col(row, "q id", "question id"), ("Q",)),
            "status": status,
        })
    return out


def read_sources(src: Source) -> list[dict]:
    return [
        {
            "id": row["__id__"],
            "title": col(row, "title / filename / path or url", "title"),
            "type": col(row, "type"),
            "authority": col(row, "authority"),
            "version": col(row, "date / version", "version"),
        }
        for _, _, row in read_registers(src, "sources", ("Source ID",), "SRC")
    ]


def read_modules(src: Source) -> list[dict]:
    path = src.project / pr.SOLUTION_FILE
    if not path.is_file():
        return []
    out, seen = [], set()
    for line, row in pr.read_register(path, ("MOD ID", "Module ID"), "MOD"):
        if row["__id__"] in seen:
            src.findings.error(vh.STEP_REQ, "DUPLICATE_ID", f"{row['__id__']} is defined more than once.", src.loc(path, line))
            continue
        seen.add(row["__id__"])
        out.append({
            "id": row["__id__"],
            "name": col(row, "module name", "name"),
            "parent": first_id(col(row, "parent module", "parent"), "MOD"),
            "type": mapped(src, col(row, "type", "area"), MODULE_TYPES, "module type", src.loc(path, line),
                           vh.STEP_REQ, row["__id__"]),
            "purpose": col(row, "purpose", "responsibility"),
            "security_boundary": col(row, "security boundary"),
            "data_ownership": pr.extract_ids(col(row, "data ownership", "owned entities"), ("ENT",)),
        })
    return out


def read_processes(src: Source) -> list[dict]:
    path = src.project / pr.PROCESS_FILE
    if not path.is_file():
        return []
    out = []
    for record in unique_records(src, pr.read_records(path, ("PROC",)), vh.STEP_REQ):
        perspective = norm_enum(record.field("perspective", "as-is or to-be", "as-is / to-be")).lower().replace("-", "_").replace(" ", "_")
        if perspective not in ("as_is", "to_be"):
            if perspective:
                src.findings.error(vh.STEP_REQ, "INVALID_VALUE", f"{record.id}: perspective {perspective!r} is not AS-IS or TO-BE.",
                                   src.rloc(record, "perspective"))
            perspective = None
        out.append({
            "id": record.id,
            "title": record.title,
            "perspective": perspective,
            "actors": text_field(record, "actor", "actors"),
            "trigger": text_field(record, "trigger"),
            "preconditions": text_field(record, "preconditions", "precondition"),
            "main_flow": items_field(record, "main flow"),
            "alternative_flows": items_field(record, "alternative flow", "alternative flows"),
            "exceptions": items_field(record, "exceptions", "exception flow"),
            "result": text_field(record, "result", "outcome"),
            "business_rules": ids_in(record.field("business rules") or section_text(record.section("business rules")), "RULE"),
            "data_involved": ids_in(record.field("data involved") or section_text(record.section("data involved")), "ENT"),
            "related_requirements": ids_in(record.field("related requirements", "requirements"), *pr.REQUIREMENT_KINDS),
            "compares_to": first_id(record.field("replaces", "compares to", "as-is process"), "PROC"),
            "differences": items_field(record, "differences from as-is", "differences"),
            "confidence": record_field_enum(src, record, ("confidence",), CONFIDENCE, "confidence", vh.STEP_REQ),
            "source_path": pr.rel(src.project, record.path),
        })
    return sorted(out, key=lambda x: pr.natural_key(x["id"]))


def read_entities(src: Source) -> list[dict]:
    path = src.project / pr.DOMAIN_FILE
    if not path.is_file():
        return []
    out = []
    for record in unique_records(src, pr.read_records(path, ("ENT",)), vh.STEP_REQ):
        out.append({
            "id": record.id,
            "name": record.title,
            "purpose": text_field(record, "purpose"),
            "key_attributes": items_field(record, "key attributes"),
            "relationships": items_field(record, "relationships"),
            "states": [s for s in (p.strip() for p in re.split(r"[,;\n]|\u2192|->", text_field(record, "lifecycle states", "states"))) if s and not pr.is_none(s)],
            "owner": text_field(record, "ownership", "owner"),
            "permissions": text_field(record, "permissions"),
            "business_rules": ids_in(record.field("business rules") or section_text(record.section("business rules")), "RULE"),
            "related_requirements": ids_in(record.field("related requirements", "requirements"), *pr.REQUIREMENT_KINDS),
            "confidence": record_field_enum(src, record, ("confidence",), CONFIDENCE, "confidence", vh.STEP_REQ),
            "source_path": pr.rel(src.project, record.path),
        })
    return sorted(out, key=lambda x: pr.natural_key(x["id"]))


def unique_records(src: Source, records: list[pr.Record], step: str) -> list[pr.Record]:
    seen: dict[str, str] = {}
    out = []
    for record in records:
        where = src.rloc(record)
        if record.id in seen:
            src.findings.error(step, "DUPLICATE_ID", f"{record.id} is also defined at {seen[record.id]}.", where)
            continue
        seen[record.id] = where
        out.append(record)
    return out


def read_requirements(src: Source, questions: list[dict]) -> list[dict]:
    records: list[pr.Record] = []
    for rel in pr.REQUIREMENT_FILES:
        path = src.project / rel
        if path.is_file():
            records += pr.read_records(path, pr.REQUIREMENT_KINDS)
    q_by_id = {q["id"]: q for q in questions}
    out = []
    for record in unique_records(src, records, vh.STEP_REQ):
        kind = pr.kind_of(record.id)
        status_raw = record.field("status")
        status_key = norm_enum(status_raw).lower()
        status = REQ_STATUS.get(status_key)
        if status is None:
            hint = " Release boundaries are recorded in the Scope field." if status_key in ("deferred", "out of scope") else ""
            src.findings.error(vh.STEP_REQ, "INVALID_VALUE",
                               f"{record.id}: status {status_raw!r} is not one of Draft, Confirmed, Approved, Superseded, Rejected.{hint}",
                               src.rloc(record, "status"))
            status = status_key or "draft"
        prio, confirmed = priority(src, record)
        description = section_text(record.section("description")) or pr.clean(
            record.field("description", "requirement", "rule", "business need / outcome") or "")
        dependencies = ids_in(record.field("dependencies"), *pr.REQUIREMENT_KINDS)
        dependencies += [b for b in ids_in(record.field("business rules", "business rule ids"), "RULE") if b not in dependencies]
        affected = {q["id"] for q in questions if not q["resolved"] and record.id in q["affected_ids"]}
        mentioned = {q for q in question_mentions(record) if not q_by_id.get(q, {}).get("resolved")}
        out.append({
            "id": record.id,
            "type": REQ_TYPE[kind],
            "title": record.title,
            "description": description,
            "rationale": text_field(record, "rationale"),
            "source": ids_in(record.field("source", "derived from", "parent requirements", "business requirements",
                                          "business goals"), *pr.REQUIREMENT_KINDS),
            "status": status,
            "priority": prio,
            "acceptance_criteria": criteria(record.section("acceptance criteria", "acceptance condition",
                                                           "acceptance conditions")),
            "dependencies": [d for d in dependencies if d != record.id],
            "related_modules": ids_in(record.field("related modules", "modules", "module"), "MOD"),
            "stakeholder": pr.clean(record.field("related stakeholder", "stakeholder", "stakeholders") or ""),
            "notes": text_field(record, "notes"),
            "evidence": ids_in(record.field("evidence", "source evidence", "source / decision"), "SRC", "DEC"),
            "priority_confirmed": confirmed,
            "confidence": record_field_enum(src, record, ("confidence",), CONFIDENCE, "confidence", vh.STEP_REQ),
            "scope": record_field_enum(src, record, ("scope",), SCOPE, "scope", vh.STEP_REQ),
            "actor": pr.clean(record.field("actor", "actors") or "") or None,
            "trigger": pr.clean(record.field("trigger") or "") or None,
            "permissions": pr.clean(record.field("permissions") or "") or None,
            "category": pr.clean(record.field("category") or "") or None,
            "business_measure": {
                "measure": pr.clean(record.field("measure", "measure / unit") or ""),
                "baseline": pr.clean(record.field("baseline") or ""),
                "target": pr.clean(record.field("target") or ""),
            } if kind == "GOAL" else None,
            "open_questions": sorted(affected | mentioned, key=pr.natural_key),
            "superseded_by": first_id(record.field("superseded by"), kind) or next(
                iter(ids_in(record.field("superseded by"), *pr.REQUIREMENT_KINDS)), None),
            # Named by the requirement itself; the ADRs that name it are added once ADRs are read.
            "architecture_decisions": declared_adrs(record, "requirement"),
            "source_path": pr.rel(src.project, record.path),
        })
        if kind in pr.IMPLEMENTABLE_KINDS and status in ("approved", "confirmed") and not out[-1]["acceptance_criteria"]:
            src.findings.error(vh.STEP_REQ, "EMPTY_ACCEPTANCE_CRITERIA",
                               f"{record.id} is {status} but its 'Acceptance criteria' section is empty or missing.", src.rloc(record))
    return sorted(out, key=lambda r: (list(REQ_TYPE).index(pr.kind_of(r["id"])), pr.natural_key(r["id"])))


def declared_adrs(record: pr.Record, via: str) -> list[dict]:
    """ADRs a requirement, feature or task names itself; statuses are filled in once ADRs are known."""
    return [{"id": a, "status": "proposed", "applies_via": [via]}
            for a in ids_in(record.field("architecture decisions", "adrs", "architecture decision ids"), "ADR")]


def consequence_lists(record: pr.Record) -> dict:
    """Positive and negative consequences, from '### Positive' / '### Negative' sections or 'Positive:' items."""
    out: dict[str, list[str]] = {"positive": [], "negative": [], "other": []}
    for kind in ("positive", "negative"):
        section = record.section(kind, f"{kind} consequences")
        if section:
            if section.text:
                out[kind].append(section.text)
            out[kind] += [pr.clean(i) for i in section.items if pr.clean(i)]
    section = record.section("consequences")
    if section:
        if section.text:
            out["other"].append(section.text)
        for item in section.items:
            text = pr.clean(item)
            match = re.match(r"^(positive|negative|pro|con)\s*:\s*(.+)$", text, re.IGNORECASE)
            if match:
                kind = "positive" if match.group(1).lower() in ("positive", "pro") else "negative"
                out[kind].append(match.group(2).strip())
            elif text:
                out["other"].append(text)
    return out


def section_items(record: pr.Record, *names: str) -> list[str]:
    """A section's prose and list items as a list, ignoring an explicit 'None'."""
    section = record.section(*names)
    if section is None:
        return []
    items = [pr.clean(i) for i in section.items if pr.clean(i) and not pr.is_none(i)]
    if section.text and not pr.is_none(section.text):
        items.insert(0, section.text)
    return items


def read_adrs(src: Source) -> list[dict]:
    out = []
    records: list[pr.Record] = []
    for path in sorted(src.project.glob(pr.ADR_GLOB)):
        found = pr.read_records(path, ("ADR",))
        if len(found) != 1:
            src.findings.error(vh.STEP_REQ, "ADR_FILE_STRUCTURE",
                               f"Expected exactly one ADR record heading ('# ADR-### — Title'), found {len(found)}.", src.loc(path))
        records += found[:1]
    for record in unique_records(src, records, vh.STEP_REQ):
        status_raw = record.field("status")
        status = norm_enum(status_raw).lower()
        if status not in ADR_STATUS:
            src.findings.error(vh.STEP_REQ, "INVALID_VALUE",
                               f"{record.id}: status {status_raw!r} is not one of Proposed, Accepted, Rejected, Superseded, Deprecated.",
                               src.rloc(record, "status"))
        date = pr.clean(record.field("date") or "")
        if date and not ISO_DATE.match(date) and not pr.has_tbd(date):
            src.findings.error(vh.STEP_REQ, "INVALID_VALUE", f"{record.id}: date {date!r} is not YYYY-MM-DD.", src.rloc(record, "date"))
        alternatives = []
        section = record.section("alternatives considered", "alternatives", "options considered")
        if section:
            for table in section.tables:
                for _, row in table.dict_rows():
                    option = col(row, "option", "alternative")
                    if option:
                        alternatives.append({
                            "option": option,
                            "description": col(row, "description", "summary"),
                            "advantages": col(row, "advantages", "pros"),
                            "disadvantages": col(row, "disadvantages", "cons"),
                            "outcome": col(row, "outcome", "why not chosen", "decision"),
                        })
            for item in section.items:
                option, _, rest = pr.clean(item).partition("—")
                alternatives.append({"option": option.strip() or pr.clean(item), "description": rest.strip(),
                                     "advantages": "", "disadvantages": "", "outcome": ""})
        owner = pr.clean(record.field("decision owner / approver", "decision owner", "approver", "deciders",
                                      "decision makers") or "")
        risks = section_items(record, "risks")
        out.append({
            "id": record.id,
            "title": record.title,
            "status": status,
            "active": status == "accepted",
            "date": date if ISO_DATE.match(date) else None,
            "decision_owner": "" if pr.is_none(owner) else owner,
            "approval_evidence": ids_in(record.field("approval evidence", "approval"), "DEC", "SRC"),
            "decision_questions": ids_in(record.field("decision question", "decision questions", "open question"), "Q"),
            "context": section_text(record.section("context")),
            "decision": section_text(record.section("decision")),
            "rationale": section_text(record.section("rationale")),
            "alternatives": alternatives,
            "consequences": consequence_lists(record),
            "risks": risks,
            "risk_ids": pr.extract_ids(" ".join(risks), ("RISK",)),
            "constraints": section_items(record, "constraints introduced", "constraints"),
            "related_requirements": ids_in(record.field("related requirements", "requirements"), *pr.REQUIREMENT_KINDS),
            "related_features": ids_in(record.field("related features", "features"), "FEAT"),
            "affected_modules": ids_in(record.field("affected modules", "modules"), "MOD"),
            "related_decisions": ids_in(record.field("related decisions", "decisions"), "DEC"),
            "principles": ids_in(record.field("principles", "principles applied"), "PRIN"),
            "depends_on": [i for i in ids_in(record.field("depends on", "dependencies"), "ADR", "DEP") if i != record.id],
            "conflicts_with": [i for i in ids_in(record.field("conflicts with"), "ADR") if i != record.id],
            "supersedes": [i for i in ids_in(record.field("supersedes"), "ADR") if i != record.id],
            "superseded_by": first_id(record.field("superseded by"), "ADR"),
            "notes": "" if pr.is_none(section_text(record.section("notes"))) else section_text(record.section("notes")),
            "source_path": pr.rel(src.project, record.path),
        })
    return sorted(out, key=lambda a: pr.natural_key(a["id"]))


def read_principles(src: Source) -> list[dict]:
    path = src.project / pr.PRINCIPLES_FILE
    if not path.is_file():
        return []
    out, seen = [], set()
    for line, row in pr.read_register(path, ("PRIN ID", "Principle ID"), "PRIN"):
        if row["__id__"] in seen:
            src.findings.error(vh.STEP_REQ, "DUPLICATE_ID", f"{row['__id__']} is defined more than once.", src.loc(path, line))
            continue
        seen.add(row["__id__"])
        out.append({
            "id": row["__id__"],
            "statement": col(row, "principle", "statement") or row["__id__"],
            "rationale": col(row, "rationale"),
            "implications": col(row, "implications", "implication"),
            "evidence": pr.extract_ids(col(row, "evidence", "source / decision", "source"), ("SRC", "DEC")),
            "status": mapped(src, col(row, "status"), PRINCIPLE_STATUS, "principle status", src.loc(path, line),
                             vh.STEP_REQ, row["__id__"]) or "proposed",
        })
    return out


def read_conflict_reviews(src: Source) -> list[dict]:
    """ARCHITECTURE CONFLICT findings of the architecture review, so readiness can tell open conflicts from settled ones."""
    path = src.project / pr.ARCHITECTURE_REVIEW_FILE
    if not path.is_file():
        return []
    out = []
    for table in pr.read_tables(path):
        if table.keys()[:1] != ["finding id"]:
            continue
        for _, row in table.dict_rows():
            fid = col(row, "finding id")
            if not pr.FULL_ID_RE["FIND"].match(fid) or norm_enum(col(row, "type")).upper() != "ARCHITECTURE CONFLICT":
                continue
            out.append({"finding_id": fid, "severity": norm_enum(col(row, "severity")).upper() or None,
                        "status": norm_enum(col(row, "status")).upper() or "OPEN",
                        "adr_ids": pr.extract_ids(col(row, "adr"), ("ADR",)),
                        "affected_ids": pr.extract_ids(col(row, "affected ids")),
                        "resolution": col(row, "resolution")})
    return sorted(out, key=lambda r: pr.natural_key(r["finding_id"]))


def read_coverage(src: Source) -> list[dict]:
    """The architecture concern coverage table in the architecture register."""
    path = src.project / pr.ARCHITECTURE_REGISTER_FILE
    if not path.is_file():
        return []
    out = []
    for table in pr.read_tables(path):
        if table.keys()[:1] != ["concern"]:
            continue
        for line, row in table.dict_rows():
            concern = col(row, "concern")
            if not concern:
                continue
            rationale = col(row, "rationale / evidence", "rationale", "evidence")
            out.append({
                "concern": concern,
                "status": mapped(src, col(row, "status"), COVERAGE_STATUS, "coverage status", src.loc(path, line),
                                 vh.STEP_REQ, concern),
                "adr_ids": pr.extract_ids(col(row, "adr ids", "adrs", "adr"), ("ADR",)),
                "question_ids": pr.extract_ids(col(row, "question", "questions", "q id"), ("Q",)),
                "rationale": rationale,
                "evidence": pr.extract_ids(rationale, ("SRC", "DEC")),
            })
    return out


def upper_enum(value: str | None) -> str:
    return re.sub(r"[\s-]+", "_", norm_enum(value).upper())


def read_changes(src: Source) -> list[dict]:
    """Change records (changes/CHANGE-###.md): what changed, why, its lifecycle and its dispositions."""
    records: list[pr.Record] = []
    for path in pr.change_files(src.project):
        found = pr.read_records(path, ("CHANGE",))
        if len(found) != 1:
            src.findings.error(vh.STEP_TRACE, "CHANGE_FILE_STRUCTURE",
                               f"Expected exactly one change record heading ('# CHANGE-### — Title'), found {len(found)}.", src.loc(path))
            continue
        if path.stem != found[0].id and not path.stem.startswith(f"{found[0].id}-"):
            src.findings.warn(vh.STEP_TRACE, "CHANGE_FILE_NAME", f"{found[0].id} is stored in {path.name}; name the file {found[0].id}.md.",
                              src.loc(path))
        records.append(found[0])
    out = []
    for record in unique_records(src, records, vh.STEP_TRACE):
        cid = record.id

        def enum(names: tuple[str, ...], allowed, what: str, default=None):
            raw = record.field(*names)
            value = upper_enum(raw)
            if not value or pr.has_tbd(raw or "") or pr.is_none(raw or ""):
                return default
            if value not in allowed:
                src.findings.error(vh.STEP_TRACE, "INVALID_VALUE",
                                   f"{cid}: {what} {raw!r} is not one of {', '.join(allowed)}.", src.rloc(record, names[0]))
                return default
            return value

        status = enum(("status",), ci.CHANGE_STATUSES, "status", "PROPOSED")
        date = pr.clean(record.field("date") or "")
        if date and not ISO_DATE.match(date) and not pr.has_tbd(date):
            src.findings.error(vh.STEP_TRACE, "INVALID_VALUE", f"{cid}: date {date!r} is not YYYY-MM-DD.", src.rloc(record, "date"))
        dispositions: dict[str, dict] = {}
        section = record.section("affected artifacts")
        for table in section.tables if section else []:
            for line, row in table.dict_rows():
                identifier = next(iter(pr.extract_ids(col(row, "artifact", "artifact id", "id"))), None)
                if not identifier:
                    continue
                entry = {}
                for key, names, allowed in (("level", ("impact level", "level"), ci.LEVELS),
                                            ("confidence", ("confidence",), ci.CONFIDENCES),
                                            ("review_state", ("review state", "state"), ci.REVIEW_STATES),
                                            ("resolution", ("resolution",), ci.RESOLUTIONS)):
                    raw = col(row, *names)
                    value = upper_enum(raw)
                    if value and not pr.has_tbd(raw) and not pr.is_none(raw):
                        if value not in allowed:
                            src.findings.error(vh.STEP_TRACE, "INVALID_VALUE",
                                               f"{cid}: {identifier} {key.replace('_', ' ')} {raw!r} is not one of {', '.join(allowed)}.",
                                               src.loc(record.path, line))
                            value = None
                        entry[key] = value
                    else:
                        entry[key] = None
                entry["notes"] = col(row, "notes", "rationale")
                dispositions[identifier] = entry
        reviews = []
        section = record.section("required reviews")
        for table in section.tables if section else []:
            for _, row in table.dict_rows():
                area = col(row, "review area", "area")
                if area:
                    result = upper_enum(col(row, "result")).replace("N_A", "N/A") or "PENDING"
                    reviews.append({"area": area, "result": result if result in ci.REVIEW_RESULTS else "PENDING",
                                    "evidence": col(row, "evidence", "evidence / ids")})
        risks = []
        section = record.section("risk impact")
        for table in section.tables if section else []:
            for _, row in table.dict_rows():
                risk = next(iter(pr.extract_ids(col(row, "risk", "risk id"), ("RISK",))), None)
                effect = upper_enum(col(row, "effect"))
                if risk or effect:
                    risks.append({"risk": risk, "effect": effect if effect in ci.RISK_EFFECTS else None,
                                  "rationale": col(row, "rationale", "notes")})
        out.append({
            "change_id": cid,
            "title": record.title,
            "status": status,
            "date": date if ISO_DATE.match(date) else None,
            "change_type": enum(("change type", "type"), ci.CHANGE_TYPES, "change type"),
            "changed_artifacts": pr.extract_ids(pr.clean(record.field("changed artifacts", "changed artifact") or "")),
            "changed_by": pr.clean(record.field("changed by", "requested by") or ""),
            "approved_by": "" if pr.is_none(record.field("approved by") or "") else pr.clean(record.field("approved by") or ""),
            "approval_evidence": ids_in(record.field("approval evidence"), "DEC", "SRC"),
            "declared_severity": enum(("severity", "declared severity"), ci.SEVERITIES, "severity"),
            "decisions_required": ids_in(record.field("decisions required", "required decisions"), "Q"),
            "resolution_status": enum(("resolution status",), ci.RESOLUTION_STATUSES, "resolution status", "OPEN"),
            "superseded_by": first_id(record.field("superseded by"), "CHANGE"),
            "previous_state": section_text(record.section("previous state")),
            "new_state": section_text(record.section("new state")),
            "reason": section_text(record.section("reason")),
            "required_reviews": reviews,
            "risk_impact": risks,
            "roadmap_notes": section_text(record.section("roadmap impact")),
            "new_work": section_text(record.section("new work required", "new work")),
            "document_notes": section_text(record.section("document impact")),
            "dispositions": dispositions,
            "source_path": pr.rel(src.project, record.path),
        })
    return sorted(out, key=lambda c: pr.natural_key(c["change_id"]))


def task_status(src: Source, record: pr.Record, default: str = "DRAFT") -> str:
    raw = record.field("status")
    value = norm_enum(raw).upper().replace(" ", "_").replace("-", "_")
    if not value:
        src.findings.error(vh.STEP_BACKLOG, "MISSING_FIELD", f"{record.id}: 'Status' is blank.", src.rloc(record, "status"))
        return default
    if value in vh.ENGINEERING_STATUSES:
        src.findings.error(vh.STEP_BACKLOG, "INVALID_VALUE",
                           f"{record.id}: status {raw!r} is an engineering execution status, owned by downstream delivery. "
                           f"ProjectPlanner uses planning statuses only: {', '.join(vh.TASK_STATUSES)}.", src.rloc(record, "status"))
    elif value == "DEFERRED":
        src.findings.error(vh.STEP_BACKLOG, "INVALID_VALUE",
                           f"{record.id}: DEFERRED is retired. Classify the scope FUTURE or OUT OF SCOPE, or set the status "
                           f"CANCELLED when the work is dropped by a recorded decision.", src.rloc(record, "status"))
    elif value not in vh.TASK_STATUSES:
        src.findings.error(vh.STEP_BACKLOG, "INVALID_VALUE",
                           f"{record.id}: status {raw!r} is not one of {', '.join(vh.TASK_STATUSES)}.", src.rloc(record, "status"))
    return value


def read_hierarchy(src: Source) -> tuple[list[dict], list[dict], list[dict]]:
    path = src.project / pr.BACKLOG_FILE
    if not path.is_file():
        return [], [], []
    records = unique_records(src, pr.read_records(path, ("EPIC", "FEAT", "PHASE")), vh.STEP_BACKLOG)
    epics, features, phases = [], [], []
    for record in records:
        kind = pr.kind_of(record.id)
        common = {
            "id": record.id,
            "title": record.title,
            "source_path": pr.rel(src.project, record.path),
        }
        if kind == "PHASE":
            date = pr.clean(record.field("date", "target date") or "")
            basis = record_field_enum(src, record, ("date basis",), DATE_BASIS, "date basis", vh.STEP_BACKLOG)
            if date and not pr.has_tbd(date) and not pr.is_none(date) and basis in (None, "none"):
                src.findings.error(vh.STEP_BACKLOG, "UNQUALIFIED_DATE",
                                   f"{record.id} has date {date!r} without a date basis; state TARGET, ESTIMATE or COMMITMENT.",
                                   src.rloc(record, "date"))
            phases.append({
                **common,
                "order": int(record.id.split("-")[1]),
                "objective": pr.clean(record.field("objective") or "") or section_text(record.section("objective")),
                "exit_criteria": pr.clean(record.field("exit criteria") or "") or section_text(record.section("exit criteria")),
                "task_ids": [],
                "date": None if not date or pr.has_tbd(date) or pr.is_none(date) else date,
                "date_basis": basis or "none",
                "commitment_decision": first_id(record.field("commitment decision", "commitment evidence"), "DEC"),
            })
            continue
        entry = {
            **common,
            "goal": pr.clean(record.field("goal") or "") or section_text(record.section("goal")),
            "status": task_status(src, record),
            "priority": priority(src, record, vh.STEP_BACKLOG)[0],
            "requirement_ids": ids_in(record.field("related requirement ids", "related requirements", "requirements"),
                                      *pr.REQUIREMENT_KINDS),
        }
        if kind == "EPIC":
            epics.append({**entry, "feature_ids": []})
        else:
            features.append({
                **entry,
                "epic": first_id(record.field("epic"), "EPIC"),
                "task_ids": [],
                "scope": record_field_enum(src, record, ("scope",), SCOPE, "scope", vh.STEP_BACKLOG),
                "module_ids": ids_in(record.field("modules", "related modules", "module"), "MOD"),
                "dependencies": [f for f in ids_in(record.field("depends on", "feature dependencies"), "FEAT") if f != record.id],
                "external_dependencies": ids_in(record.field("external dependencies"), "DEP"),
                "architecture_decisions": declared_adrs(record, "feature"),
                "no_tasks_reason": text_field(record, "no tasks reason", "tasks not required") or None,
            })
    order = lambda item: pr.natural_key(item["id"])  # noqa: E731
    features = [{k: f[k] for k in ("id", "epic", "title", "goal", "status", "priority", "requirement_ids", "task_ids",
                                   "source_path", "scope", "module_ids", "dependencies", "external_dependencies",
                                   "architecture_decisions", "no_tasks_reason")}
                for f in sorted(features, key=order)]
    epics = [{k: e[k] for k in ("id", "title", "goal", "status", "priority", "requirement_ids", "feature_ids", "source_path")}
             for e in sorted(epics, key=order)]
    phases = [{k: p[k] for k in ("id", "title", "order", "objective", "exit_criteria", "task_ids", "source_path",
                                 "date", "date_basis", "commitment_decision")}
              for p in sorted(phases, key=order)]
    return epics, features, phases


def constraints_from(section: pr.Section | None) -> dict:
    out = {kind: [] for kind in (*CONSTRAINT_KINDS, "other")}
    out["not_applicable"] = {}
    if section is None:
        return out

    def add(kind_raw: str, text: str, reference: str) -> None:
        kind = pr.norm_key(kind_raw)
        kind = kind if kind in CONSTRAINT_KINDS else "other"
        text = pr.clean(text)
        if not text:
            return
        if re.match(r"^n/?a\b", text, re.IGNORECASE):
            reason = re.sub(r"^n/?a\s*(?:—|–|-|:)?\s*", "", text, flags=re.IGNORECASE).strip()
            if kind in CONSTRAINT_KINDS:
                out["not_applicable"][kind] = reason or "Not applicable."
            return
        reference = pr.clean(reference)
        if reference and not pr.is_none(reference) and reference not in text:
            text = f"{text} ({reference})"
        out[kind].append(text)

    for table in section.tables:
        for _, row in table.dict_rows():
            add(col(row, "kind", "type", "category"), col(row, "constraint", "requirement", "description"),
                col(row, "reference", "source", "references"))
    for item in section.items:
        kind, sep, text = pr.clean(item).partition(":")
        if sep:
            add(kind, text, "")
        else:
            add("other", item, "")
    return out


def full_text(section: pr.Section | None) -> str:
    """A section's prose, list items and table rows, as one text."""
    if section is None:
        return ""
    parts = [section_text(section)]
    for table in section.tables:
        for row in table.rows:
            cells = [pr.clean(c) for c in row if pr.clean(c)]
            if cells:
                parts.append(": ".join(cells))
    return "\n".join(p for p in parts if p).strip()


def read_impact(record: pr.Record, kind: str) -> dict:
    names = IMPACT_SECTIONS[kind]
    text = pr.clean(record.field(*names) or "") or full_text(record.section(*names))
    if not text:
        return {"stated": False, "text": "", "ids": [], "change": None, "not_applicable": False}
    not_applicable = pr.is_none(text) or bool(re.match(r"^n/?a\b", text, re.IGNORECASE))
    change = None
    if kind == "api":
        found = re.search(r"\b(NONE|CREATE|MODIFY|REMOVE)\b", text.upper())
        change = found.group(1).lower() if found else ("none" if not_applicable else None)
    return {"stated": True, "text": text, "ids": pr.extract_ids(text), "change": change, "not_applicable": not_applicable}


def read_readiness_history(src: Source, record: pr.Record) -> list[dict]:
    """Every readiness transition the card records: date, from, to, reason, the change behind it."""
    section = record.section("readiness history")
    out = []
    for table in section.tables if section else []:
        for line, row in table.dict_rows():
            to = norm_enum(col(row, "to", "new status")).upper().replace(" ", "_")
            if not to:
                continue
            before = norm_enum(col(row, "from", "previous status")).upper().replace(" ", "_")
            before = None if not before or pr.is_none(before) else before
            for value in (before, to):
                if value is not None and value not in vh.TASK_STATUSES:
                    src.findings.error(vh.STEP_BACKLOG, "INVALID_VALUE",
                                       f"{record.id}: readiness history status {value!r} is not one of {', '.join(vh.TASK_STATUSES)}.",
                                       src.loc(record.path, line))
            date = col(row, "date")
            out.append({"date": date if ISO_DATE.match(date) else None, "from": before, "to": to,
                        "reason": col(row, "reason"), "change_id": first_id(col(row, "change id", "change", "evidence"), "CHANGE")})
    return out


def read_tasks(src: Source, questions: list[dict], features: list[dict]) -> list[dict]:
    q_by_id = {q["id"]: q for q in questions}
    feature_epic = {f["id"]: f["epic"] for f in features}
    records: list[pr.Record] = []
    for path in sorted(src.project.glob(pr.TASK_GLOB), key=lambda p: pr.natural_key(p.stem)):
        found = pr.read_records(path, ("TASK",))
        if len(found) != 1:
            src.findings.error(vh.STEP_BACKLOG, "TASK_FILE_STRUCTURE",
                               f"Expected exactly one task heading ('# TASK-### — Title'), found {len(found)}.", src.loc(path))
            continue
        if path.stem != found[0].id:
            src.findings.error(vh.STEP_BACKLOG, "TASK_FILE_NAME", f"{found[0].id} is stored in {path.name}; name the file {found[0].id}.md.", src.loc(path))
        records.append(found[0])

    out = []
    for record in unique_records(src, records, vh.STEP_BACKLOG):
        tid = record.id
        status = task_status(src, record)
        type_raw = record.field("type", "task type")
        task_type = norm_enum(type_raw).lower() or "other"
        if task_type not in TASK_TYPES:
            src.findings.error(vh.STEP_BACKLOG, "INVALID_VALUE",
                               f"{tid}: type {type_raw!r} is not one of {', '.join(sorted(TASK_TYPES))}.", src.rloc(record, "type"))
        prio, confirmed = priority(src, record, vh.STEP_BACKLOG)
        complexity_raw = norm_enum(record.field("estimated complexity", "complexity")).split(" ")[0].upper()
        complexity = complexity_raw if complexity_raw in {"XS", "S", "M", "L", "XL"} else "unspecified"

        blocked_by = record.field("blocked by", "dependencies")
        reviewed = bool(blocked_by is not None and pr.clean(blocked_by) and not pr.has_tbd(blocked_by)
                        and (pr.is_none(blocked_by) or ids_in(blocked_by, "TASK")))
        dependencies = [] if blocked_by is None or pr.is_none(blocked_by) else [d for d in ids_in(blocked_by, "TASK")]

        blockers_raw = record.field("readiness blockers", "blocking issues")
        if blockers_raw is None or not pr.clean(blockers_raw) or pr.has_tbd(blockers_raw):
            blocking_issues = ["Readiness blockers have not been reviewed ('Readiness blockers' is blank or TBD)."]
        elif pr.is_none(blockers_raw):
            blocking_issues = []
        else:
            blocking_issues = [p.strip() for p in re.split(r"[;\n]", pr.clean(blockers_raw)) if p.strip()]

        levels = []
        for part in re.split(r"[,;/]", pr.clean(record.field("required test levels", "required tests") or "")):
            level = TEST_LEVEL_ALIASES.get(part.strip().lower(), part.strip().lower())
            if not level or pr.has_tbd(level.upper()):
                continue
            if level not in TEST_LEVELS:
                src.findings.error(vh.STEP_BACKLOG, "INVALID_VALUE",
                                   f"{tid}: test level {part.strip()!r} is not one of {', '.join(sorted(TEST_LEVELS))}.",
                                   src.rloc(record, "required test levels"))
            if level not in levels:
                levels.append(level)

        test_ids: list[str] = []
        for name in ("testing checklist", "acceptance criteria", "verification"):
            section = record.section(name)
            if section:
                blob = " ".join([section.text, *section.items] + [" ".join(" ".join(r) for r in t.rows) for t in section.tables])
                test_ids += [t for t in pr.extract_ids(blob, ("TEST",)) if t not in test_ids]

        feature = first_id(record.field("feature"), "FEAT")
        epic = first_id(record.field("epic"), "EPIC") or feature_epic.get(feature)
        revision_raw = pr.clean(record.field("revision") or "")
        revision = int(revision_raw) if revision_raw.isdigit() and int(revision_raw) >= 1 else 1
        if revision_raw and not (revision_raw.isdigit() and int(revision_raw) >= 1):
            src.findings.error(vh.STEP_BACKLOG, "INVALID_VALUE", f"{tid}: revision {revision_raw!r} is not a whole number from 1.",
                               src.rloc(record, "revision"))
        requirements = ids_in(record.field("related requirement ids", "source requirements", "requirements"), *pr.REQUIREMENT_KINDS)
        parent = next((t for t in ids_in(record.field("parent task", "parent task / optional subtask ids"), "TASK") if t != tid), None)

        affected = {q["id"] for q in questions if not q["resolved"] and ({tid, *requirements} & set(q["affected_ids"]))}
        mentioned = {q for q in question_mentions(record) if not q_by_id.get(q, {}).get("resolved")}
        open_questions = [
            {"id": q, "question": q_by_id.get(q, {}).get("question", ""), "blocking": q_by_id.get(q, {}).get("blocking", True)}
            for q in sorted(affected | mentioned, key=pr.natural_key)
        ]
        details = {
            pr.slug_key(section.label): section.as_json()
            for key, section in record.sections.items()
            if key not in TASK_CORE_SECTIONS and not section.is_empty() and pr.slug_key(section.label)
        }
        out.append({
            "schema_version": vh.SCHEMA_VERSION,
            "project_id": None,  # filled in once the project is known
            "id": tid,
            "title": record.title,
            "revision": revision,
            "content_hash": None,  # set once requirements and ADR links are final
            "status": status,
            "type": task_type,
            "objective": text_field(record, "objective", "goal"),
            "declared_scope": record_field_enum(src, record, ("scope", "scope status"), SCOPE, "scope", vh.STEP_BACKLOG),
            "source_requirements": requirements,
            "feature": feature,
            "epic": epic,
            "description": section_text(record.section("description")),
            "acceptance_criteria": criteria(record.section("acceptance criteria")),
            "dependencies": dependencies,
            "constraints": constraints_from(record.section("constraints")),
            "verification": {"required_tests": levels, "test_ids": sorted(test_ids, key=pr.natural_key)},
            "open_questions": open_questions,
            "blocking_issues": blocking_issues,
            "priority": prio,
            "priority_confirmed": confirmed,
            "complexity": complexity,
            "phase": first_id(record.field("phase"), "PHASE"),
            "parent_task": parent,
            "dependencies_reviewed": reviewed,
            "blocks": [],
            "architecture_decisions": declared_adrs(record, "task"),
            "related_modules": ids_in(record.field("related modules", "modules"), "MOD"),
            "readiness_gaps": [],
            "scope": None,  # the feature's scope, set once features are known
            "external_dependencies": ids_in(record.field("external dependencies"), "DEP"),
            "impacts": {kind: read_impact(record, kind) for kind in IMPACT_SECTIONS},
            "risk_ids": ids_in(record.field("risks", "related risks"), "RISK"),
            "readiness": None,  # the Definition of Ready evaluation, set once the whole plan is known
            "readiness_history": read_readiness_history(src, record),
            "details": details,
            "source_path": pr.rel(src.project, record.path),
        })
    return out


def read_tests(src: Source) -> list[dict]:
    path = src.project / pr.TESTS_FILE
    if not path.is_file():
        return []
    out = []
    for record in unique_records(src, pr.read_records(path, ("TEST",)), vh.STEP_TRACE):
        level_raw = norm_enum(record.field("test level", "level")).lower()
        level = TEST_LEVEL_ALIASES.get(level_raw, level_raw) or None
        if level and level not in TEST_LEVELS:
            src.findings.error(vh.STEP_TRACE, "INVALID_VALUE",
                               f"{record.id}: test level {level_raw!r} is not one of {', '.join(sorted(TEST_LEVELS))}.",
                               src.rloc(record, "test level"))
        status_raw = norm_enum(record.field("execution status")).upper().replace(" ", "_") or "NOT_RUN"
        refs = " ".join(filter(None, [record.field("requirement ids", "requirements", "requirement / ac ids"),
                                      record.field("acceptance criteria", "ac ids")]))
        steps = []
        for section in record.sections.values():
            for table in section.tables:
                keys = table.keys()
                if keys and keys[0] == "step":
                    for _, row in table.dict_rows():
                        steps.append({"action": col(row, "action / input", "action"),
                                      "expected": col(row, "expected observable result", "expected result", "expected")})
        out.append({
            "id": record.id,
            "title": record.title,
            "level": level,
            "category": pr.clean(record.field("category", "test type", "title / test type") or ""),
            "requirement_ids": ids_in(refs, *pr.REQUIREMENT_KINDS),
            "acceptance_criteria_ids": ids_in(refs, "AC"),
            "preconditions": pr.clean(record.field("preconditions") or ""),
            "steps": steps,
            "expected_result": pr.clean(record.field("expected result") or ""),
            "execution_status": status_raw,
            "source_path": pr.rel(src.project, record.path),
        })
    return sorted(out, key=lambda t: pr.natural_key(t["id"]))


# --------------------------------------------------------------------------
# Cross-document identifier consistency (human documents)
# --------------------------------------------------------------------------


def scan_references(src: Source, bundle: vh.Bundle) -> None:
    files: list[Path] = []
    for pattern in pr.REFERENCE_SCAN_GLOBS:
        files += sorted(src.project.glob(pattern))
    files += [p for p in pr.source_files(src.project)]
    reported: set[tuple[str, str]] = set()
    for path in sorted(set(files)):
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for legacy in pr.LEGACY_ID_RE.findall(line):
                key = (str(path), legacy)
                if key not in reported:
                    reported.add(key)
                    src.findings.warn(vh.STEP_TRACE, "LEGACY_ID",
                                      f"{legacy} uses a retired identifier form; use EPIC-###, FEAT-###, TEST-### and CHANGE-###.",
                                      src.loc(path, number))
            for identifier in pr.extract_ids(line):
                if bundle.known(identifier) is False and (str(path), identifier) not in reported:
                    reported.add((str(path), identifier))
                    src.findings.warn(vh.STEP_TRACE, "UNDEFINED_ID_IN_DOCUMENT",
                                      f"{identifier} is mentioned but not defined in any canonical record.",
                                      src.loc(path, number))


def compare_task_tables(src: Source, bundle: vh.Bundle) -> None:
    """A task index in a human document must agree with the task records."""
    candidates = [(src.project / pr.BACKLOG_FILE, True)] + [(p, False) for p in sorted(src.project.glob("deliverables/*.md"))]
    for path, authoritative in candidates:
        if not path.is_file():
            continue
        for table in pr.read_tables(path):
            keys = table.keys()
            if not keys or keys[0] not in ("task id", "card id"):
                continue
            for line, row in table.dict_rows():
                tid = pr.clean(row.get(keys[0], ""))
                task = bundle.task_by_id.get(tid)
                if not pr.FULL_ID_RE["TASK"].match(tid):
                    continue
                where = src.loc(path, line)
                report = src.findings.error if authoritative else src.findings.warn
                code = "BACKLOG_INDEX_CONFLICT" if authoritative else "DELIVERABLE_OUT_OF_DATE"
                if task is None:
                    report(vh.STEP_BACKLOG, code, f"{tid} is listed but has no task file.", where)
                    continue
                checks = {
                    "status": task["status"],
                    "epic": task["epic"],
                    "feature": task["feature"],
                    "blocked by": task["dependencies"],
                }
                for column, expected in checks.items():
                    if column not in row or not pr.clean(row[column]):
                        continue
                    cell = pr.clean(row[column])
                    if column == "status":
                        actual = norm_enum(cell).upper().replace(" ", "_")
                    elif column == "blocked by":
                        actual = [] if pr.is_none(cell) else pr.extract_ids(cell, ("TASK",))
                        expected = list(expected)
                    else:
                        actual = first_id(cell, "EPIC" if column == "epic" else "FEAT")
                    if actual != expected:
                        report(vh.STEP_BACKLOG, code, f"{tid} {column} is {cell!r} here but {expected!r} in its task file.", where)


# --------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------


def dump(document: object) -> bytes:
    return (json.dumps(document, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def build(project: Path, generated_at: str) -> tuple[dict[str, object], Source, vh.Bundle]:
    src = Source(project)
    state = read_state(src)
    questions = read_questions(src)
    decisions = read_decisions(src)
    assumptions = read_assumptions(src)
    risks = read_risks(src)
    dependencies = read_dependencies(src)
    sources = read_sources(src)
    scope_items = read_scope_items(src)
    modules = read_modules(src)
    processes = read_processes(src)
    entities = read_entities(src)
    requirements = read_requirements(src, questions)
    adrs = read_adrs(src)
    principles = read_principles(src)
    coverage = read_coverage(src)
    conflict_reviews = read_conflict_reviews(src)
    epics, features, phases = read_hierarchy(src)
    tasks = read_tasks(src, questions, features)
    tests = read_tests(src)
    changes = read_changes(src)
    project_id = state["project_id"] or "UNKNOWN"

    feature_scope = {f["id"]: f["scope"] for f in features}
    for task in tasks:
        task["project_id"] = project_id
        task["scope"] = task["declared_scope"] or feature_scope.get(task["feature"])

    docs: dict[str, object] = {
        "project.json": {
            "schema_version": vh.SCHEMA_VERSION,
            "project_id": project_id,
            "name": state["name"] or "",
            "version": state["version"],
            "specification_status": state["status"],
            "specification_approval": state["approval"],
            "specification_review": {"result": "NOT_REVIEWED", "review_cycle": 0, "review_version": None},
            "backlog_status": "NOT_READY",
            "priority_scheme": state["priority_scheme"],
            "handoff_status": "invalid",
            "generated_at": generated_at,
            "generator": {"name": GENERATOR_NAME, "version": GENERATOR_VERSION},
            "source_fingerprint": pr.fingerprint(project),
            "language": state["language"],
            "requirements_count": len(requirements),
            "tasks_count": len(tasks),
            "ready_tasks_count": sum(1 for t in tasks if t["status"] == "READY"),
            "blocked_tasks_count": sum(1 for t in tasks if t["status"] == "BLOCKED"),
            "task_status_counts": {s: sum(1 for t in tasks if t["status"] == s) for s in vh.TASK_STATUSES},
            "artifacts": [],
        },
        "requirements.json": {
            "schema_version": vh.SCHEMA_VERSION, "project_id": project_id,
            "specification_version": state["version"], "sources": sources, "requirements": requirements,
            "scope_items": scope_items,
        },
        "architecture.json": {
            "schema_version": vh.SCHEMA_VERSION, "project_id": project_id,
            "summary": vh.architecture_summary(adrs, coverage), "principles": principles, "modules": modules,
            "coverage": coverage, "decisions": adrs, "conflict_reviews": conflict_reviews,
        },
        "decisions.json": {
            "schema_version": vh.SCHEMA_VERSION, "project_id": project_id,
            "decisions": decisions, "questions": questions, "assumptions": assumptions, "risks": risks,
        },
        "domain.json": {
            "schema_version": vh.SCHEMA_VERSION, "project_id": project_id, "processes": processes, "entities": entities,
        },
        "tests.json": {"schema_version": vh.SCHEMA_VERSION, "project_id": project_id, "tests": tests},
    }
    for task in sorted(tasks, key=lambda t: pr.natural_key(t["id"])):
        docs[f"tasks/{task['id']}.json"] = task
    docs["backlog.json"] = {
        "schema_version": vh.SCHEMA_VERSION, "project_id": project_id, "specification_version": state["version"],
        "epics": epics, "features": features, "phases": phases, "tasks": [],
        "sequencing": {"method": "topological", "tie_break": ["phase_order", "priority", "id"], "order": []},
        "ready_task_ids": [], "executable_now": [], "external_dependencies": dependencies,
    }
    docs["traceability.json"] = {"schema_version": vh.SCHEMA_VERSION, "project_id": project_id}

    # Derived values: computed once, from the same records the validator reads.
    bundle = vh.Bundle(docs)
    blocks = vh.derived_blocks(tasks)
    # ADR links in dependency order: requirements, then features, then tasks.
    for req in requirements:
        req["architecture_decisions"] = vh.requirement_adrs(req, bundle)
    for feature in features:
        feature["architecture_decisions"] = vh.feature_adrs(feature, bundle)
    for task in tasks:
        task["blocks"] = blocks.get(task["id"], [])
        task["architecture_decisions"] = vh.applicable_adrs(task, bundle)
    for feature in features:
        feature["task_ids"] = sorted((t["id"] for t in tasks if t["feature"] == feature["id"]), key=pr.natural_key)
    for epic in epics:
        epic["feature_ids"] = sorted((f["id"] for f in features if f["epic"] == epic["id"]), key=pr.natural_key)
    for phase in phases:
        phase["task_ids"] = sorted((t["id"] for t in tasks if t["phase"] == phase["id"]), key=pr.natural_key)

    # Change impact: what the change records and the baseline say must be reviewed. Computed before
    # readiness, because a task whose foundation changed cannot be READY.
    docs["changes.json"] = ci.changes_document(changes, bundle, ci.source_context(project), vh.SCHEMA_VERSION, project_id)
    bundle = vh.Bundle(docs)

    # The independent specification review, also before readiness: no task is READY on an unreviewed specification,
    # or on one whose review fails. Its own defects are reported by check_gates.py (gate GR), not here.
    src.spec_review = sr.evaluate(project, bundle)
    review = docs["specification-review.json"] = sr.document(src.spec_review, vh.SCHEMA_VERSION, project_id)
    docs["project.json"]["specification_review"] = {
        "result": review["overall_result"], "review_cycle": review["review_cycle"], "review_version": review["review_version"],
    }
    bundle = vh.Bundle(docs)

    order, depth, unsequenced = vh.sequence_tasks(tasks, bundle.phase_order)
    for task in tasks:
        task["readiness_gaps"] = vh.readiness_gaps(task, bundle, unsequenced)
        task["readiness"] = vh.readiness_evaluation(task, bundle, unsequenced)
        task["content_hash"] = hc.task_content_hash(task, bundle.req_by_id, bundle.adr_by_id)
    by_id = {t["id"]: t for t in tasks}
    position = {tid: i for i, tid in enumerate(order, start=1)}
    backlog = docs["backlog.json"]
    backlog["tasks"] = [
        {
            "id": t["id"], "title": t["title"], "status": t["status"], "type": t["type"], "priority": t["priority"],
            "complexity": t["complexity"], "epic": t["epic"], "feature": t["feature"], "phase": t["phase"],
            "source_requirements": t["source_requirements"], "dependencies": t["dependencies"], "blocks": t["blocks"],
            "sequence": position.get(t["id"]), "depth": depth.get(t["id"]), "file": f"tasks/{t['id']}.json",
            "scope": t["scope"], "external_dependencies": t["external_dependencies"],
        }
        for t in sorted(tasks, key=lambda t: (position.get(t["id"], 10**9), pr.natural_key(t["id"])))
    ]
    backlog["sequencing"]["order"] = order
    backlog["ready_task_ids"] = [tid for tid in order if by_id[tid]["status"] == "READY"]
    sets = br.work_sets(vh.Bundle(docs))
    backlog["executable_now"] = sets[0] if sets else []

    records, task_records, summary, orphans = vh.expected_traceability(bundle)
    docs["traceability.json"] = {
        "schema_version": vh.SCHEMA_VERSION, "project_id": project_id,
        "requirements": records, "tasks": task_records, "architecture": vh.expected_architecture_trace(bundle),
        "coverage_summary": summary, "orphans": orphans,
    }
    bundle = vh.Bundle(docs)
    # Backlog readiness: the backlog-level view of every task's Definition of Ready result.
    readiness = docs["backlog-readiness.json"] = br.document(bundle, vh.SCHEMA_VERSION, project_id)
    docs["project.json"]["backlog_status"] = readiness["status"]
    bundle = vh.Bundle(docs)
    scan_references(src, bundle)
    compare_task_tables(src, bundle)
    return docs, src, bundle


def serialize(docs: dict[str, object]) -> dict[str, bytes]:
    raw: dict[str, bytes] = {}
    artifacts = []
    for name in sorted(docs, key=lambda n: (n.startswith("tasks/"), pr.natural_key(n))):
        if name == "project.json":
            continue
        raw[name] = dump(docs[name])
        schema = vh.DOCUMENT_SCHEMAS.get(name, vh.TASK_SCHEMA)
        artifacts.append({"path": name, "schema": schema, "sha256": hashlib.sha256(raw[name]).hexdigest()})
    docs["project.json"]["artifacts"] = artifacts
    raw["project.json"] = dump(docs["project.json"])
    return raw


def finalize(docs: dict[str, object], src: Source) -> tuple[dict[str, bytes], vh.Findings, vh.Bundle]:
    """Validate, set handoff_status from the result, and re-validate."""
    raw = serialize(docs)
    findings, bundle = vh.validate_files(raw)
    for _ in range(2):
        errors = len(src.findings.errors) + len([f for f in findings.errors if f.code != "HANDOFF_STATUS_MISMATCH"])
        status = vh.expected_handoff_status(errors, bundle)
        if docs["project.json"]["handoff_status"] == status:
            break
        docs["project.json"]["handoff_status"] = status
        raw = serialize(docs)
        findings, bundle = vh.validate_files(raw)
    return raw, findings, bundle


def write_output(out_dir: Path, raw: dict[str, bytes]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    tasks_dir = out_dir / "tasks"
    for owned in [*vh.DOCUMENT_SCHEMAS, vh.REPORT_FILE]:
        (out_dir / owned).unlink(missing_ok=True)
    if tasks_dir.is_dir():
        for stale in tasks_dir.glob("*.json"):
            stale.unlink()
    for name, data in raw.items():
        target = out_dir / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def report_document(project_doc: dict, generated_at: str, findings: vh.Findings, bundle: vh.Bundle) -> dict:
    statuses = [t.get("status") for t in bundle.tasks]
    return {
        "schema_version": vh.SCHEMA_VERSION,
        "project_id": project_doc.get("project_id"),
        "generated_at": generated_at,
        "result": "VALID" if not findings.errors else "INVALID",
        "specification": str(project_doc.get("specification_status")).upper(),
        "handoff_status": project_doc.get("handoff_status"),
        "summary": {
            "ready_tasks": statuses.count("READY"),
            "blocked_tasks": statuses.count("BLOCKED"),
            "other_non_ready_tasks": sum(statuses.count(s) for s in ("DRAFT", "NEEDS_DISCOVERY", "NEEDS_REVIEW")),
            "errors": len(findings.errors),
            "warnings": len(findings.warnings),
        },
        "errors": [f.as_json() for f in findings.errors],
        "warnings": [f.as_json() for f in findings.warnings],
        "non_ready_tasks": vh.non_ready_tasks(bundle),
    }


def md_cell(value) -> str:
    if isinstance(value, (list, tuple)):
        value = ", ".join(value) if value else "—"
    text = str(value) if value not in (None, "") else "—"
    return text.replace("|", "\\|").replace("\n", " ")


def requirement_map(bundle: vh.Bundle, generated_at: str) -> str:
    project = bundle.project
    trace = {r["requirement_id"]: r for r in bundle.traceability.get("requirements", [])}
    req = bundle.req_by_id
    lines = [
        "# Requirement Map",
        "",
        "<!-- GENERATED by tools/generate_handoff.py. Do not edit: change the source records and regenerate. -->",
        "",
        f"Project: {project.get('name')} ({project.get('project_id')}) · Specification: {project.get('version') or 'TBD'} "
        f"({str(project.get('specification_status')).upper()}) · Generated: {generated_at} · "
        f"Source fingerprint: {str(project.get('source_fingerprint'))[:12]}",
        "",
        "The human-readable view of `machine-handoff/traceability.json`. Both are generated from the same canonical "
        "records, so they cannot disagree. Read a row left to right: business goal → requirement → feature → task → tests; "
        "the ADRs column shows the architecture decisions that govern the row.",
        "",
        "## Traceability chains",
        "",
        "| Business goal | Requirement | Title | Coverage | Feature | Task | Task status | Tests | ADRs |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]

    def rows_for(root: str | None, rid: str) -> list[str]:
        record = trace.get(rid, {})
        out = []
        tasks = record.get("task_ids") or [None]
        for tid in tasks:
            task = bundle.task_by_id.get(tid) if tid else None
            out.append("| " + " | ".join(md_cell(v) for v in (
                root, rid, req.get(rid, {}).get("title"), record.get("coverage"),
                task.get("feature") if task else record.get("feature_ids"), tid,
                task.get("status") if task else None, record.get("test_ids"), record.get("adr_ids"),
            )) + " |")
        return out

    reached: set[str] = set()
    for biz in sorted((r for r in req if pr.kind_of(r) == "GOAL"), key=pr.natural_key):
        reached.add(biz)
        stack = list(reversed(trace.get(biz, {}).get("downstream_requirement_ids", [])))
        if not stack:
            lines += rows_for(biz, biz)
        seen: set[str] = set()
        while stack:
            rid = stack.pop()
            if rid in seen:
                continue
            seen.add(rid)
            reached.add(rid)
            lines += rows_for(biz, rid)
            stack += list(reversed(trace.get(rid, {}).get("downstream_requirement_ids", [])))
    orphans = sorted((r for r in req if r not in reached), key=pr.natural_key)
    for rid in orphans:
        lines += rows_for(None, rid)

    lines += [
        "",
        "## Tasks in sequence",
        "",
        "| Sequence | Task | Title | Status | Epic | Feature | Requirements | Depends on | Tests | ADRs | Readiness gaps |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for entry in bundle.backlog_tasks:
        task = bundle.task_by_id.get(entry["id"], {})
        lines.append("| " + " | ".join(md_cell(v) for v in (
            entry.get("sequence"), entry["id"], entry.get("title"), entry.get("status"), entry.get("epic"),
            entry.get("feature"), entry.get("source_requirements"), entry.get("dependencies"),
            (task.get("verification") or {}).get("test_ids"), [a["id"] for a in task.get("architecture_decisions", [])],
            "; ".join(task.get("readiness_gaps") or []) or "None",
        )) + " |")

    lines += [
        "",
        "## Architecture decisions",
        "",
        "Why each technical constraint exists and what it reaches. Only ACCEPTED decisions govern planning; "
        "rejected, superseded and deprecated decisions are kept for history and apply to nothing new.",
        "",
        "| ADR | Title | Status | Requirements | Features | Tasks | Modules | Supersedes | Superseded by |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for entry in bundle.traceability.get("architecture", []):
        adr = bundle.adr_by_id.get(entry["adr_id"], {})
        lines.append("| " + " | ".join(md_cell(v) for v in (
            entry["adr_id"], adr.get("title"), str(entry.get("status")).upper(), entry.get("requirement_ids"),
            entry.get("feature_ids"), entry.get("task_ids"), entry.get("module_ids"), entry.get("supersedes"),
            entry.get("superseded_by"),
        )) + " |")

    summary = bundle.traceability.get("coverage_summary", {})
    lines += ["", "## Coverage summary", "", "| Measure | Count |", "| --- | --- |"]
    lines += [f"| {key.replace('_', ' ').capitalize()} | {value} |" for key, value in summary.items()]
    lines.append("")
    return "\n".join(lines)


def read_previous_manifest(out_dir: Path) -> dict | None:
    try:
        previous = json.loads((out_dir / hc.MANIFEST_FILE).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None
    return previous if isinstance(previous, dict) else None


def manifest_document(raw: dict[str, bytes], bundle: vh.Bundle, findings: vh.Findings, generated_at: str,
                      previous: dict | None) -> dict:
    manifest = hc.build_manifest(raw, bundle, vh.validation_flags(findings, bundle), generated_at,
                                 {"name": GENERATOR_NAME, "version": GENERATOR_VERSION}, vh.SCHEMA_VERSION, previous)
    vh.load_validators()[vh.CONTRACT_PREFIX + hc.MANIFEST_SCHEMA].validate(manifest)
    return manifest


def print_report(project: Path, out_dir: Path | None, findings: vh.Findings, bundle: vh.Bundle, file_count: int,
                 manifest: dict) -> None:
    def step_line(number: int, label: str, step: str) -> str:
        errors = [f for f in findings.errors if f.step == step]
        warnings = [f for f in findings.warnings if f.step == step]
        result = "FAIL" if errors else "PASS"
        extra = []
        if errors:
            extra.append(f"{len(errors)} error{'s' * (len(errors) != 1)}")
        if warnings:
            extra.append(f"{len(warnings)} warning{'s' * (len(warnings) != 1)}")
        return f" {number}. {label:<26} {result}" + (f" ({', '.join(extra)})" if extra else "")

    print(f"generate-machine-handoff: {project}")
    print(step_line(1, "Specification", vh.STEP_SPEC))
    print(step_line(2, "Requirements", vh.STEP_REQ))
    print(step_line(3, "Backlog readiness", vh.STEP_BACKLOG))
    if out_dir:
        try:
            shown = os.path.relpath(out_dir)
        except ValueError:  # different drive on Windows
            shown = str(out_dir)
        written = f"written to {shown} ({file_count} JSON files)"
    else:
        written = "not written (--check)"
    generate_errors = [f for f in findings.errors if f.step == STEP_GENERATE]
    print(f" 4. {'Generate JSON':<26} {'FAIL' if generate_errors else 'DONE'} - {written}")
    print(step_line(5, "JSON schemas", vh.STEP_SCHEMA))
    print(step_line(6, "Traceability", vh.STEP_TRACE))
    non_ready = vh.non_ready_tasks(bundle)
    print(f" 7. {'Blocked / non-ready tasks':<26} {len(non_ready)}")
    for task in non_ready:
        print(f"      {task['id']} {task['status']}: {' '.join(task['reasons'][:3])}"
              + (f" (+{len(task['reasons']) - 3} more)" if len(task['reasons']) > 3 else ""))
    print(" 8. Summary")
    for line in vh.summary_lines(findings, bundle):
        print(f"      {line}")
    ready = ", ".join(manifest["ready_tasks"]) or "none"
    print(f"      Handoff manifest: {manifest['handoff_status']} (handoff {manifest['handoff_version']}, "
          f"{'written' if out_dir else 'not written'})")
    print(f"      Ready for handoff: {ready}")
    if findings.items:
        print()
        vh.print_findings(findings)


def resolve_generated_at(value: str | None) -> str:
    if value:
        return value
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    moment = _dt.datetime.fromtimestamp(int(epoch), _dt.timezone.utc) if epoch else _dt.datetime.now(_dt.timezone.utc)
    return moment.replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate and validate the machine handoff for one project.")
    parser.add_argument("project", type=Path, help="Project folder, for example projects/acme-portal")
    parser.add_argument("--out", type=Path, default=None, help=f"Output directory; defaults to <project>/{OUTPUT_DIR}")
    parser.add_argument("--check", action="store_true", help="Validate and report without writing anything")
    parser.add_argument("--generated-at", default=None,
                        help="Timestamp to record (YYYY-MM-DDTHH:MM:SSZ). Defaults to SOURCE_DATE_EPOCH, then now. "
                             "Fix it to reproduce a byte-identical handoff.")
    parser.add_argument("--no-map", action="store_true", help=f"Do not write {REQUIREMENT_MAP}")
    args = parser.parse_args(argv)

    project = args.project.resolve()
    if not (project / pr.STATE_FILE).is_file():
        print(f"{args.project} has no {pr.STATE_FILE}; is it a project folder?", file=sys.stderr)
        return 2
    generated_at = resolve_generated_at(args.generated_at)
    if not re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$", generated_at):
        print(f"--generated-at must look like 2026-09-26T10:00:00Z, got {generated_at!r}", file=sys.stderr)
        return 2

    try:
        docs, src, _ = build(project, generated_at)
        raw, json_findings, bundle = finalize(docs, src)
    except vh.SchemaUnavailable as exc:
        print(str(exc), file=sys.stderr)
        return 2

    out_dir = None
    if not args.check:
        out_dir = (args.out or project / OUTPUT_DIR).resolve()
        write_output(out_dir, raw)
        # Authoritative result: validate what is actually on disk, including staleness.
        json_findings, bundle = vh.validate_files(vh.read_directory(out_dir), project)
    findings = vh.Findings()
    findings.extend(src.findings)
    findings.extend(json_findings)

    report = report_document(docs["project.json"], generated_at, findings, bundle)
    vh.load_validators()["validation-report.schema.json"].validate(report)
    target_dir = (args.out or project / OUTPUT_DIR).resolve()
    planning_files = vh.read_directory(out_dir) if out_dir is not None else raw
    manifest = manifest_document(planning_files, bundle, findings, generated_at, read_previous_manifest(target_dir))
    if out_dir is not None:
        (out_dir / vh.REPORT_FILE).write_bytes(dump(report))
        manifest_bytes = dump(manifest)
        (out_dir / hc.MANIFEST_FILE).write_bytes(manifest_bytes)
        # The manifest must agree with what is on disk; any disagreement is a generator defect.
        findings.extend(vh.manifest_findings(manifest_bytes, planning_files, bundle, findings))
        if not args.no_map:
            target = project / REQUIREMENT_MAP
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(requirement_map(bundle, generated_at), encoding="utf-8", newline="\n")
        if (project / "backlog").is_dir() and bundle.backlog_readiness:
            (project / br.REPORT_FILE).write_text(br.report_markdown(bundle.backlog_readiness, bundle, generated_at),
                                                  encoding="utf-8", newline="\n")

    print_report(args.project, out_dir, findings, bundle, len(raw), manifest)
    return 1 if findings.errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
