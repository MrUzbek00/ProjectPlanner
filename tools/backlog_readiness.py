#!/usr/bin/env python3
"""Backlog readiness validation: is the backlog a validated, execution-ready planning artifact?

Stage 10B of the workflow (WORKFLOW.md section 15). Tasks existing is not the
same as tasks being ready. Every task earns READY by passing the Definition of
Ready, evaluated deterministically by tools/validate_handoff.py as named checks.
This module turns those per-task results into the backlog view:

- the backlog status: READY, PARTIALLY_READY (a valid subset can start) or NOT_READY;
- counts by planning status, the ready percentage, and what blocks each task;
- phase readiness and the planning-completeness questions for every phase;
- ready work sets: waves of READY tasks whose prerequisites are all ready;
- coverage metrics (requirements, features, criteria, dependencies, ADR links);
- heuristic flags for a reviewer: overloaded tasks, fragmented microtasks,
  possible duplicates, contradictory tasks, missing error behaviour, gaps
  between a task's impacts and its verification.

Everything here is computed from the machine-handoff bundle alone, so the
validator recomputes it and backlog-readiness.json can never disagree with the
tasks. Heuristic flags are warnings for a person to judge, never verdicts.

Usage:
    python tools/backlog_readiness.py projects/<project>            # summary; writes backlog/readiness-report.md
    python tools/backlog_readiness.py projects/<project> --json     # the computed backlog-readiness.json
    python tools/backlog_readiness.py projects/<project> --no-write

Exit codes: 0 when some in-scope work is READY, 1 when none is, 2 when the tool cannot run.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import planning_records as pr  # noqa: E402
import specification_review as sr  # noqa: E402

REPORT_FILE = "backlog/readiness-report.md"
PLANNING_STATUSES = ("DRAFT", "NEEDS_DISCOVERY", "NEEDS_REVIEW", "BLOCKED", "READY", "CANCELLED")
# What a phase must be able to answer before it is ready, and the Definition of Ready checks that answer it.
PLANNING_QUESTIONS = [
    ("what", "Do we know what needs to be built?", ("title_clear", "objective_clear")),
    ("why", "Why does it need to exist?", ("objective_clear", "source_requirement_valid")),
    ("requirement", "What requirement supports it?", ("source_requirement_valid",)),
    ("success", "What does success look like?", ("acceptance_criteria_valid", "acceptance_criteria_testable")),
    ("dependencies", "What does it depend on?", ("dependencies_valid", "external_dependencies_available")),
    ("constraints", "What constraints apply?", ("architecture_valid", "architecture_conflicts_clear", "security_valid",
                                                "data_impact_known", "api_impact_known", "ui_impact_known",
                                                "integration_impact_known")),
    ("blockers", "What could block it?", ("open_questions_clear", "blocking_risks_clear", "not_stale", "review_findings_clear")),
    ("verification", "How will completion be verified?", ("verification_defined",)),
]
IMPLEMENTATION_STEP = re.compile(
    r"^(create|implement|build|add|write|develop|set ?up|configure|make|update|fix)\b.*\b(model|models|serializer|serializers|"
    r"endpoint|endpoints|api|table|tables|schema|migration|controller|class|database|db|view|views|route|routes|"
    r"button|component|field|column)\b", re.IGNORECASE)
NEGATIVE = re.compile(r"\b(reject\w*|den(?:y|ied)|error\w*|invalid|fail\w*|not allowed|cannot|can't|unauthori[sz]ed|"
                      r"expired|refus\w*|blocked|locked|unchanged|prevent\w*|no \w+ is sent|not sent|unavailable|time ?out)",
                      re.IGNORECASE)
SYNONYMS = {"deactivate": "disable", "deactivates": "disable", "deactivation": "disable", "disables": "disable",
            "suspend": "disable", "suspends": "disable", "block": "disable", "users": "user", "accounts": "user",
            "account": "user", "administrator": "admin", "administrators": "admin", "admins": "admin",
            "remove": "delete", "removes": "delete", "erase": "delete", "deletes": "delete", "create": "add",
            "creates": "add", "new": "add", "modify": "edit", "update": "edit", "change": "edit", "edits": "edit"}
DUPLICATE_STOP = {"allow", "allows", "let", "lets", "add", "ability", "able", "to", "a", "an", "the", "of", "for", "and",
                  "or", "can", "may", "be", "is", "are", "their", "its", "with", "by", "in", "on", "so", "that", "from", "own"}
TEST_LEVELS_UI = {"e2e", "manual", "uat", "accessibility"}
# A data impact that expects a migration: "migration" not followed closely by none, no or not.
MIGRATION = re.compile(r"\bmigrat\w*(?![^\n.;]{0,25}\b(?:none|no|not)\b)", re.IGNORECASE)


def _active(task: dict) -> bool:
    return task.get("status") != "CANCELLED" and task.get("scope") == "in_scope"


def _ready(task: dict) -> bool:
    return task.get("status") == "READY" and (task.get("readiness") or {}).get("result") == "PASS"


def _failed_checks(task: dict) -> set[str]:
    return {c for c, ok in ((task.get("readiness") or {}).get("checks") or {}).items() if not ok}


def _tasks(bundle) -> list[dict]:
    return sorted(bundle.tasks, key=lambda t: pr.natural_key(t.get("id", "")))


# --------------------------------------------------------------------------
# Work sets, phases, status
# --------------------------------------------------------------------------


def work_sets(bundle) -> list[list[str]]:
    """Waves of executable work. Set 1 holds READY, in-scope tasks that pass the Definition of Ready and depend
    on nothing; set k holds those whose prerequisites all sit in earlier sets. A task that depends on work that is
    not ready is in no set. Within a set, tasks keep the backlog sequence."""
    eligible = {t["id"]: t for t in bundle.tasks if _active(t) and _ready(t)}
    position = {entry["id"]: entry.get("sequence") or 10**9 for entry in bundle.backlog_tasks}
    placed: dict[str, int] = {}
    sets: list[list[str]] = []
    while True:
        wave = [tid for tid, task in eligible.items() if tid not in placed
                and all(d in placed for d in task.get("dependencies") or [])]
        if not wave:
            return sets
        wave.sort(key=lambda tid: (position.get(tid, 10**9), pr.natural_key(tid)))
        for tid in wave:
            placed[tid] = len(sets)
        sets.append(wave)


def backlog_status(bundle) -> str:
    active = [t for t in bundle.tasks if _active(t)]
    ready = [t for t in active if _ready(t)]
    if active and len(ready) == len(active):
        return "READY"
    return "PARTIALLY_READY" if ready else "NOT_READY"


def phases(bundle) -> list[dict]:
    out = []
    for phase in sorted(bundle.phases, key=lambda p: (p.get("order", 0), p.get("id", ""))):
        tasks = [bundle.task_by_id[t] for t in phase.get("task_ids") or [] if t in bundle.task_by_id]
        active = [t for t in tasks if _active(t)]
        ready = [t for t in active if _ready(t)]
        status = "EMPTY" if not active else "READY" if len(ready) == len(active) else "PARTIALLY_READY" if ready else "NOT_READY"
        questions = []
        for key, question, checks in PLANNING_QUESTIONS:
            failing = sorted((t["id"] for t in active if _failed_checks(t) & set(checks)), key=pr.natural_key)
            questions.append({"key": key, "question": question, "answered": bool(active) and not failing,
                              "unanswered_for": failing})
        out.append({"id": phase["id"], "title": phase.get("title"), "status": status,
                    "active_tasks": len(active), "ready_tasks": len(ready),
                    "status_counts": {s: sum(1 for t in tasks if t.get("status") == s) for s in PLANNING_STATUSES},
                    "planning_questions": questions})
    return out


# --------------------------------------------------------------------------
# Heuristic flags: for a reviewer to judge, never verdicts
# --------------------------------------------------------------------------


def _tokens(text: str) -> set[str]:
    words = re.findall(r"[a-z][a-z-]+", text.lower())
    return {SYNONYMS.get(w, w) for w in words if w not in DUPLICATE_STOP and len(w) > 2}


def _requirements(task: dict, bundle) -> list[dict]:
    return [bundle.req_by_id[r] for r in task.get("source_requirements") or [] if r in bundle.req_by_id]


def overload_signals(task: dict, bundle) -> list[str]:
    """Signs that a task holds several independent outcomes. Text length is deliberately not one of them."""
    reqs = _requirements(task, bundle)
    signals = []
    modules = set(task.get("related_modules") or []) | {m for r in reqs for m in r.get("related_modules") or []}
    if len(modules) > 2:
        signals.append(f"spans {len(modules)} modules")
    processes = {p["id"] for p in bundle.processes for r in reqs if r["id"] in (p.get("related_requirements") or [])}
    if len(processes) > 1:
        signals.append(f"serves {len(processes)} workflows ({', '.join(sorted(processes, key=pr.natural_key))})")
    actors = {re.sub(r"\W+", " ", (r.get("actor") or "").lower()).strip() for r in reqs if r.get("actor")}
    if len(actors) > 1:
        signals.append(f"serves {len(actors)} actors")
    integrations = {r["id"] for r in reqs if pr.kind_of(r["id"]) == "IR"} | set(task.get("external_dependencies") or [])
    integrations |= set((((task.get("impacts") or {}).get("integration") or {}).get("ids")) or [])
    if len(integrations) > 1:
        signals.append(f"touches {len(integrations)} integrations")
    if len(task.get("acceptance_criteria") or []) > 8:
        signals.append(f"has {len(task['acceptance_criteria'])} acceptance criteria")
    clauses = [c for c in re.split(r",|;|\band\b", task.get("title") or "") if c.strip()]
    if len(clauses) >= 3:
        signals.append(f"its title lists {len(clauses)} objectives")
    return signals


def flags(bundle) -> list[dict]:
    out: list[dict] = []
    tasks = [t for t in _tasks(bundle) if t.get("status") != "CANCELLED"]

    for task in tasks:
        signals = overload_signals(task, bundle)
        if len(signals) >= 2:
            out.append({"kind": "NEEDS_DECOMPOSITION", "severity": "warning", "task_ids": [task["id"]],
                        "message": f"{task['id']} may combine several independent outcomes: {'; '.join(signals)}. "
                                   f"Consider decomposing it into outcome-oriented tasks."})

    groups: dict[tuple, list[dict]] = {}
    for task in tasks:
        groups.setdefault((task.get("feature"), tuple(sorted(task.get("source_requirements") or []))), []).append(task)
    for (feature, reqs), members in groups.items():
        steps = [t for t in members if IMPLEMENTATION_STEP.search(t.get("title") or "")]
        tiny = [t for t in members if len(t.get("acceptance_criteria") or []) <= 1]
        if len(members) >= 2 and (len(steps) >= 2 or (len(members) >= 3 and len(tiny) == len(members))):
            ids = [t["id"] for t in members]
            out.append({"kind": "FRAGMENTATION", "severity": "warning", "task_ids": ids,
                        "message": f"{', '.join(ids)} implement the same requirements ({', '.join(reqs) or 'none'}) in "
                                   f"{feature or 'no feature'} as separate steps. If they deliver one cohesive behaviour, "
                                   f"combine them into one outcome-oriented task."})

    tokens = {t["id"]: _tokens(t.get("title") or "") for t in tasks}
    for i, a in enumerate(tasks):
        for b in tasks[i + 1:]:
            ta, tb = tokens[a["id"]], tokens[b["id"]]
            if len(ta) >= 2 and len(tb) >= 2 and len(ta & tb) / len(ta | tb) >= 0.75:
                out.append({"kind": "POSSIBLE_DUPLICATE", "severity": "warning", "task_ids": [a["id"], b["id"]],
                            "message": f"{a['id']} ('{a.get('title')}') and {b['id']} ('{b.get('title')}') have overlapping "
                                       f"objectives. Review them; do not merge without confirmation."})

    items = [{"id": t["id"], "text": " ".join([t.get("title") or "", t.get("objective") or "", t.get("description") or "",
                                               " ".join(t.get("acceptance_criteria") or [])]),
              "related": set(t.get("related_modules") or []) | set(t.get("source_requirements") or []) | {t.get("feature")}}
             for t in tasks]
    for candidate in sr.contradiction_pairs(items):
        a, b = (bundle.task_by_id[i] for i in candidate.ids)
        trace = "; ".join(f"{t['id']} → {', '.join(t.get('source_requirements') or []) or 'no requirement'}" for t in (a, b))
        out.append({"kind": "CONTRADICTION", "severity": "warning", "task_ids": list(candidate.ids),
                    "message": f"Possible contradiction: {candidate.detail}. Trace: {trace}. Resolve it in the requirements "
                               f"before either task is built."})

    for task in tasks:
        if task.get("type") in ("documentation", "infrastructure", "testing") or not task.get("acceptance_criteria"):
            continue
        if NEGATIVE.search(" ".join(task["acceptance_criteria"])):
            continue
        text = " ".join([task.get("title") or "", task.get("objective") or "", task.get("description") or ""]).lower()
        reqs = _requirements(task, bundle)
        suggestions = []
        if re.search(r"\b(upload\w*|attach\w*|image|file)\b", text):
            suggestions += ["unsupported file format", "oversized file", "upload failure"]
        impacts = task.get("impacts") or {}
        if (impacts.get("integration") or {}).get("stated") or task.get("external_dependencies"):
            suggestions.append("external service unavailable or timing out")
        if any(r.get("permissions") and not pr.is_none(r["permissions"]) and not r["permissions"].lower().startswith("n/a")
               and not r["permissions"].lower().startswith("anyone") for r in reqs):
            suggestions.append("permission denied")
        if re.search(r"\b(enter\w*|submit\w*|form|input\w*|request\w*)\b", text):
            suggestions.append("invalid input")
        if re.search(r"\b(approv\w*|reject\w*|cancel\w*|suspend\w*|status|state|transition\w*)\b", text):
            suggestions.append("invalid state transition")
        if suggestions:
            out.append({"kind": "MISSING_ERROR_BEHAVIOUR", "severity": "warning", "task_ids": [task["id"]],
                        "message": f"{task['id']}: no acceptance criterion covers a failure. Relevant cases to consider: "
                                   f"{', '.join(dict.fromkeys(suggestions))}."})

    for task in tasks:
        levels = set((task.get("verification") or {}).get("required_tests") or [])
        impacts = task.get("impacts") or {}
        wanted = []

        def live(kind: str) -> bool:
            impact = impacts.get(kind) or {}
            return bool(impact.get("stated")) and not impact.get("not_applicable")

        if live("api") and (impacts["api"].get("change") or "none") != "none" and not levels & {"contract", "integration"}:
            wanted.append("an API contract validation (contract)")
        if live("integration") and not levels & {"integration", "contract", "e2e"}:
            wanted.append("an integration test")
        if live("data") and MIGRATION.search(impacts["data"].get("text") or "") and "migration" not in levels:
            wanted.append("a data migration validation (migration)")
        if live("ui") and not levels & TEST_LEVELS_UI:
            wanted.append("UI acceptance (e2e, manual, uat or accessibility)")
        if wanted:
            out.append({"kind": "VERIFICATION_GAP", "severity": "warning", "task_ids": [task["id"]],
                        "message": f"{task['id']} states impacts its required test levels ({', '.join(sorted(levels)) or 'none'}) "
                                   f"do not verify: consider {', '.join(wanted)}."})

    for task in tasks:
        if IMPLEMENTATION_STEP.search(task.get("title") or ""):
            out.append({"kind": "IMPLEMENTATION_STEP", "severity": "warning", "task_ids": [task["id"]],
                        "message": f"{task['id']} '{task.get('title')}' reads as an implementation step; state the outcome "
                                   f"it delivers. Code-level decomposition belongs to engineering planning."})
    return out


# --------------------------------------------------------------------------
# Validation, coverage, document
# --------------------------------------------------------------------------


def validation(bundle, cycles: list[list[str]]) -> dict:
    tasks = _tasks(bundle)
    active = [t for t in tasks if _active(t)]
    targets = {x for t in active for x in [t["id"], t.get("feature"), t.get("epic"), *(t.get("source_requirements") or [])] if x}
    unresolved = [f for f in bundle.review_findings if sr.is_unresolved(f.get("severity"), f.get("status"))]
    issues = []
    for task in tasks:
        if task.get("status") == "CANCELLED":
            continue
        missing = [n for n, ok in (("requirement", task.get("source_requirements")), ("feature", task.get("feature")),
                                   ("acceptance criteria", task.get("acceptance_criteria"))) if not ok]
        if missing:
            issues.append(f"{task['id']} has no {', no '.join(missing)}.")
        reqs = _requirements(task, bundle)
        if reqs and all(r.get("status") in ("superseded", "rejected") for r in reqs):
            issues.append(f"{task['id']} traces only to superseded or rejected requirements "
                          f"({', '.join(r['id'] for r in reqs)}).")
    for feature in bundle.features:
        if feature.get("scope") == "in_scope" and feature.get("status") != "CANCELLED" \
                and not feature.get("task_ids") and not feature.get("no_tasks_reason"):
            issues.append(f"{feature['id']} is in scope but has no task and no recorded reason why none is needed.")
    explained = {r for f in bundle.features if f.get("no_tasks_reason") for r in f.get("requirement_ids") or []}
    covered = {r for t in tasks if t.get("status") != "CANCELLED" for r in t.get("source_requirements") or []}
    for req in bundle.requirements:
        if req.get("status") in ("approved", "confirmed") and req.get("scope") in (None, "in_scope") \
                and pr.kind_of(req["id"]) in pr.IMPLEMENTABLE_KINDS and req["id"] not in covered | explained and bundle.tasks:
            issues.append(f"{req['id']} is in scope but no task implements it.")
    blockers = sorted({q["id"] for q in bundle.questions if q.get("blocking") and not q.get("resolved")
                       and targets & set(q.get("affected_ids") or [])}, key=pr.natural_key)
    return {
        "dependency_graph_valid": not cycles and all(d in bundle.task_by_id for t in tasks for d in t.get("dependencies") or []),
        "dependency_cycles": len(cycles),
        "architecture_conflicts": sum(1 for t in active if "architecture_conflicts_clear" in _failed_checks(t)),
        "traceability_valid": not issues,
        "traceability_issues": issues,
        "unresolved_critical_findings": sum(1 for f in unresolved if f.get("severity") == "CRITICAL"),
        "unresolved_major_findings_affecting_backlog": sorted(
            (f["id"] for f in unresolved if f.get("severity") in ("CRITICAL", "MAJOR")
             and targets & set(f.get("affected_artifacts") or [])), key=pr.natural_key),
        "critical_blockers": blockers,
        "specification_approved": bundle.spec_approved,
        "specification_review_passed": bundle.review_gap() is None,
        "ready_tasks_failing_definition_of_ready": sorted(
            (t["id"] for t in tasks if t.get("status") == "READY" and not _ready(t)), key=pr.natural_key),
    }


def coverage(bundle) -> dict:
    tasks = [t for t in _tasks(bundle) if _active(t)]
    reqs = [r for r in bundle.requirements if r.get("status") in ("approved", "confirmed") and r.get("scope") in (None, "in_scope")
            and pr.kind_of(r["id"]) in pr.IMPLEMENTABLE_KINDS]
    implemented = {r for t in tasks for r in t.get("source_requirements") or []}
    features = [f for f in bundle.features if f.get("scope") == "in_scope" and f.get("status") != "CANCELLED"]
    relevant = [t for t in tasks if t.get("type") in ("integration", "infrastructure", "security", "database")
                or any((t.get("impacts") or {}).get(k, {}).get("stated") and not (t.get("impacts") or {}).get(k, {}).get("not_applicable")
                       for k in ("api", "integration", "data"))]
    return {
        "requirements_in_scope": len(reqs),
        "requirements_with_task_coverage": sum(1 for r in reqs if r["id"] in implemented),
        "features_in_scope": len(features),
        "features_with_tasks": sum(1 for f in features if f.get("task_ids")),
        "features_without_tasks_explained": sum(1 for f in features if not f.get("task_ids") and f.get("no_tasks_reason")),
        "tasks_active": len(tasks),
        "tasks_with_valid_acceptance_criteria": sum(1 for t in tasks if not _failed_checks(t) & {"acceptance_criteria_valid",
                                                                                                    "acceptance_criteria_testable"}),
        "tasks_with_valid_dependencies": sum(1 for t in tasks if "dependencies_valid" not in _failed_checks(t)),
        "tasks_architecture_relevant": len(relevant),
        "tasks_architecture_relevant_with_adr_links": sum(1 for t in relevant if t.get("architecture_decisions")),
        "tasks_needing_review": sum(1 for t in tasks if t.get("status") == "NEEDS_REVIEW" or "not_stale" in _failed_checks(t)),
    }


def document(bundle, schema_version: str | None, project_id: str | None) -> dict:
    """backlog-readiness.json, computed from the bundle alone. Never edited by hand."""
    tasks = _tasks(bundle)
    active = [t for t in tasks if _active(t)]
    ready = [t for t in active if _ready(t)]
    edges = {t["id"]: [d for d in t.get("dependencies") or [] if d in bundle.task_by_id] for t in tasks}
    cycles = _cycles(edges)
    sequence = {entry["id"]: entry.get("sequence") for entry in bundle.backlog_tasks}
    flagged: dict[str, list[str]] = {}
    all_flags = flags(bundle)
    for flag in all_flags:
        for tid in flag["task_ids"]:
            flagged.setdefault(tid, []).append(flag["kind"])
    risk_links = {t["id"]: sorted(set(t.get("risk_ids") or []) | {r["id"] for r in bundle.risks
                                  if {t["id"], t.get("feature")} & set(r.get("affected_ids") or [])}, key=pr.natural_key)
                  for t in tasks}
    counts = {s.lower(): sum(1 for t in tasks if t.get("status") == s) for s in PLANNING_STATUSES}
    return {
        "schema_version": schema_version,
        "project_id": project_id,
        "status": backlog_status(bundle),
        "summary": {
            "total": len(tasks),
            "active": len(active),
            **counts,
            "out_of_scope": sum(1 for t in tasks if t.get("status") != "CANCELLED" and t.get("scope") != "in_scope"),
            "ready_valid": len(ready),
            "ready_percentage": round(100 * len(ready) / len(active), 1) if active else 0.0,
            "meets_definition_of_ready_not_marked_ready": sorted(
                (t["id"] for t in active if (t.get("readiness") or {}).get("result") == "PASS" and t.get("status") != "READY"),
                key=pr.natural_key),
        },
        "validation": validation(bundle, cycles),
        "coverage": coverage(bundle),
        "phases": phases(bundle),
        "work_sets": [{"id": f"WS-{i:02d}", "task_ids": ids} for i, ids in enumerate(work_sets(bundle), start=1)],
        "flags": all_flags,
        "tasks": [{
            "id": t["id"], "title": t.get("title"), "status": t.get("status"), "scope": t.get("scope"),
            "priority": t.get("priority"), "sequence": sequence.get(t["id"]), "phase": t.get("phase"),
            "revision": t.get("revision", 1),
            "readiness_valid": (t.get("readiness") or {}).get("result") == "PASS",
            "result": (t.get("readiness") or {}).get("result"),
            "recommended_status": (t.get("readiness") or {}).get("recommended_status"),
            "failed_checks": sorted(_failed_checks(t)),
            "failures": (t.get("readiness") or {}).get("failures") or [],
            "accepted_risk_findings": (t.get("readiness") or {}).get("accepted_risk_findings") or [],
            "related_risks": risk_links[t["id"]],
            "flags": sorted(set(flagged.get(t["id"], []))),
        } for t in tasks],
    }


def _cycles(edges: dict[str, list[str]]) -> list[list[str]]:
    import validate_handoff as vh  # imported here: the validator imports this module
    return vh.find_cycles(list(edges), edges)


# --------------------------------------------------------------------------
# Report: backlog/readiness-report.md
# --------------------------------------------------------------------------


def report_markdown(doc: dict, bundle, generated_at: str) -> str:
    s, v, c = doc["summary"], doc["validation"], doc["coverage"]
    project = bundle.project
    md = lambda value: str(value if value not in (None, "", []) else "—").replace("|", "\\|")  # noqa: E731
    listed = lambda ids: f"{len(ids)} ({', '.join(ids)})" if ids else "0"  # noqa: E731
    lines = [
        "# Backlog Readiness", "",
        "<!-- GENERATED by tools/generate_handoff.py and tools/backlog_readiness.py from the task cards. Do not edit: "
        "fix the records and regenerate. -->", "",
        f"Project: {project.get('name')} ({project.get('project_id')}) · Specification: {project.get('version') or 'TBD'} · "
        f"Generated: {generated_at}", "",
        f"**Backlog status: {doc['status'].replace('_', ' ')}.** A task is READY only when it passes every Definition of "
        f"Ready check (`WORKFLOW.md` section 14); generating a task does not make it ready. PARTIALLY READY means a valid "
        f"subset of work can start while the rest stays visibly unresolved.", "",
        "## Summary", "", "| Measure | Value |", "| --- | --- |",
        f"| Total tasks | {s['total']} |", f"| Active (in scope, not cancelled) | {s['active']} |",
        *(f"| {status.replace('_', ' ')} | {s[status.lower()]} |" for status in PLANNING_STATUSES),
        f"| Out of scope | {s['out_of_scope']} |",
        f"| READY and passing the Definition of Ready | {s['ready_valid']} |",
        f"| Ready percentage (of active) | {s['ready_percentage']}% |",
        f"| Critical blockers (open BLOCKER questions) | {listed(v['critical_blockers'])} |",
        f"| Dependency cycles | {v['dependency_cycles']} |",
        f"| Architecture conflicts | {v['architecture_conflicts']} |",
        f"| Unresolved critical specification findings | {v['unresolved_critical_findings']} |",
        f"| Unresolved CRITICAL / MAJOR findings affecting the backlog | {listed(v['unresolved_major_findings_affecting_backlog'])} |",
        f"| READY tasks failing the Definition of Ready | {listed(v['ready_tasks_failing_definition_of_ready'])} |",
        f"| Traceability valid | {'yes' if v['traceability_valid'] else 'no'} |",
        f"| Specification approved and review passed | {'yes' if v['specification_approved'] and v['specification_review_passed'] else 'no'} |",
        "", "## Ready work sets", "",
        "Waves of READY work whose prerequisites are all ready: set 1 can start now; each later set can start once the "
        "earlier sets are complete. Work that depends on anything not ready is in no set.", "",
    ]
    lines += [f"- **{ws['id']}**: {', '.join(ws['task_ids'])}" for ws in doc["work_sets"]] or ["No task is ready to start."]
    lines += ["", "## Phases", "", "| Phase | Status | Active | Ready | Unanswered planning questions |", "| --- | --- | --- | --- | --- |"]
    for phase in doc["phases"]:
        unanswered = "; ".join(f"{q['question']} ({', '.join(q['unanswered_for'])})" for q in phase["planning_questions"]
                               if not q["answered"] and q["unanswered_for"])
        lines.append(f"| {phase['id']} {md(phase['title'])} | {phase['status'].replace('_', ' ')} | {phase['active_tasks']} | "
                     f"{phase['ready_tasks']} | {md(unanswered)} |")
    lines += ["", "## Tasks", "",
              "| Task | Status | Scope | Priority | Sequence | Readiness | Recommended status | What blocks it | Flags |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for task in doc["tasks"]:
        lines.append("| " + " | ".join(md(x) for x in (
            f"{task['id']} r{task['revision']}", task["status"], task["scope"], task["priority"], task["sequence"],
            task["result"], task["recommended_status"], " ".join(task["failures"][:3]) + (" …" if len(task["failures"]) > 3 else ""),
            ", ".join(task["flags"]))) + " |")
    lines += ["", "Priority is business importance; sequence is the recommended order, set by dependencies. A high-priority "
                  "task whose prerequisites are missing is not done first.", "",
              "## Coverage", "", "| Measure | Value |", "| --- | --- |"]
    lines += [f"| {key.replace('_', ' ').capitalize()} | {value} |" for key, value in c.items()]
    lines += ["", "Metrics expose gaps; they are not targets to reach mechanically.", "", "## Traceability issues", ""]
    lines += [f"- {md(i)}" for i in v["traceability_issues"]] or ["None."]
    lines += ["", "## Flags for review", "",
              "Heuristic signals for a person to judge — overloaded or fragmented tasks, possible duplicates, contradictions, "
              "missing error behaviour, verification gaps. None is merged, split or changed automatically.", ""]
    lines += [f"- **{f['kind']}** {md(f['message'])}" for f in doc["flags"]] or ["None."]
    lines.append("")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import datetime as _dt
    import json

    parser = argparse.ArgumentParser(description="Report a project's backlog readiness.")
    parser.add_argument("project", type=Path)
    parser.add_argument("--json", action="store_true", help="Print the computed backlog-readiness.json")
    parser.add_argument("--no-write", action="store_true", help=f"Do not write {REPORT_FILE}")
    args = parser.parse_args(argv)
    for stream in (sys.stdout, sys.stderr):
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
        docs, _, bundle = gh.build(project, when)
    except vh.SchemaUnavailable as exc:
        print(str(exc), file=sys.stderr)
        return 2
    doc = docs["backlog-readiness.json"]
    if args.json:
        print(json.dumps(doc, indent=2, ensure_ascii=False))
    else:
        s, v = doc["summary"], doc["validation"]
        print(f"Backlog readiness: {doc['status'].replace('_', ' ')}")
        print(f"  Tasks {s['total']} | active {s['active']} | READY {s['ready']} | BLOCKED {s['blocked']} | "
              f"NEEDS_REVIEW {s['needs_review']} | NEEDS_DISCOVERY {s['needs_discovery']} | DRAFT {s['draft']} | "
              f"CANCELLED {s['cancelled']}")
        print(f"  Ready percentage {s['ready_percentage']}% | dependency cycles {v['dependency_cycles']} | architecture "
              f"conflicts {v['architecture_conflicts']} | traceability {'valid' if v['traceability_valid'] else 'broken'}")
        for ws in doc["work_sets"]:
            print(f"  {ws['id']}: {', '.join(ws['task_ids'])}")
        for task in doc["tasks"]:
            if task["result"] == "FAIL":
                print(f"  {task['id']} {task['status']} (recommended {task['recommended_status']}): {task['failures'][0]}")
        for flag in doc["flags"]:
            print(f"  WARN {flag['kind']}: {flag['message']}")
        if not args.no_write and (project / "backlog").is_dir():
            (project / REPORT_FILE).write_text(report_markdown(doc, bundle, when), encoding="utf-8", newline="\n")
            print(f"\nWrote {REPORT_FILE}")
    return 0 if doc["status"] != "NOT_READY" else 1


if __name__ == "__main__":
    raise SystemExit(main())
