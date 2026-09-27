"""Tests for backlog readiness validation: the Definition of Ready as named checks, the planning status lifecycle,
backlog-readiness.json, the readiness report and gate GB.

Run from the repository root:
    python -m unittest discover -s tools/tests -v

In the fixture, TASK-001 to TASK-003 are READY and pass every check; TASK-004 waits on Q-002 in a feature that
is PENDING DECISION, so it is outside the release. The backlog is READY: WS-01 is TASK-001, WS-02 is TASK-002 and
TASK-003. Each test breaks one thing and asserts what the task, the backlog and the gates say about it.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import analyze_change_impact as aci  # noqa: E402
import backlog_readiness as br  # noqa: E402
import check_gates as cg  # noqa: E402
import generate_handoff as gh  # noqa: E402
import validate_handoff as vh  # noqa: E402
from test_gates import GateCase  # noqa: E402

TIME = "2026-09-26T00:00:00Z"
T1, T2, T3, T4 = (f"backlog/tasks/TASK-00{i}.md" for i in range(1, 5))


class ReadinessCase(GateCase):
    def handoff(self) -> tuple[dict, vh.Findings]:
        docs, src, _ = gh.build(self.project, TIME)
        _, findings, _ = gh.finalize(docs, src)
        all_findings = vh.Findings()
        all_findings.extend(src.findings)
        all_findings.extend(findings)
        return docs, all_findings

    def readiness(self, tid: str) -> dict:
        docs, _ = self.handoff()
        return docs[f"tasks/{tid}.json"]["readiness"]

    def set_status(self, rel: str, status: str, reason: str = "Readiness withdrawn for the test") -> None:
        """Change a card's status the way the workflow requires: with a readiness history entry."""
        text = (self.project / rel).read_text(encoding="utf-8")
        current = next(line.split("|")[2].strip() for line in text.splitlines() if line.startswith("| Status |"))
        self.edit(rel, f"| Status | {current} |", f"| Status | {status} |")
        self.append(rel, f"| 2026-09-26 | {current} | {status} | {reason} | |")
        index = self.project / "backlog/backlog.md"
        tid = Path(rel).stem
        index.write_text("\n".join(line.replace(f"| {current} |", f"| {status} |") if line.startswith(f"| {tid} |") else line
                                   for line in index.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")

    def failures(self, tid: str) -> list[str]:
        return self.readiness(tid)["failures"]


class Fixture(ReadinessCase):
    def test_ready_tasks_pass_every_named_check(self):
        docs, findings = self.handoff()
        self.assertEqual([], [(f.code, f.message) for f in findings.errors])
        readiness = docs["tasks/TASK-002.json"]["readiness"]
        self.assertEqual("PASS", readiness["result"])
        self.assertEqual(set(vh.READINESS_CHECKS), set(readiness["checks"]))
        self.assertTrue(all(readiness["checks"].values()))
        self.assertEqual("READY", readiness["recommended_status"])

    def test_backlog_document(self):
        docs, _ = self.handoff()
        doc = docs["backlog-readiness.json"]
        self.assertEqual("READY", doc["status"])
        self.assertEqual("READY", docs["project.json"]["backlog_status"])
        self.assertEqual([["TASK-001"], ["TASK-002", "TASK-003"]], [ws["task_ids"] for ws in doc["work_sets"]])
        self.assertEqual(["TASK-001"], docs["backlog.json"]["executable_now"])
        self.assertEqual((4, 3, 3, 100.0), (doc["summary"]["total"], doc["summary"]["active"], doc["summary"]["ready_valid"],
                                             doc["summary"]["ready_percentage"]))
        self.assertTrue(doc["validation"]["dependency_graph_valid"] and doc["validation"]["traceability_valid"])
        task = next(t for t in doc["tasks"] if t["id"] == "TASK-002")
        self.assertEqual(("high", 2), (task["priority"], task["sequence"]))  # priority and sequence are distinct
        self.assertEqual(["RISK-001"], task["related_risks"])
        self.assertEqual("NEEDS_DISCOVERY", next(t for t in doc["tasks"] if t["id"] == "TASK-004")["recommended_status"])
        phase = doc["phases"][0]
        self.assertEqual(("PHASE-01", "READY"), (phase["id"], phase["status"]))
        self.assertTrue(all(q["answered"] for q in phase["planning_questions"]))
        self.assertEqual([], doc["flags"])

    def test_gate_gb_passes_and_report_is_written(self):
        self.assertGate("GB", cg.PASS)
        self.assertGate("G9", cg.PASS)
        with contextlib.redirect_stdout(io.StringIO()):
            gh.main([str(self.project), "--generated-at", TIME])
        report = (self.project / br.REPORT_FILE).read_text(encoding="utf-8")
        self.assertIn("**Backlog status: READY.**", report)
        self.assertIn("- **WS-01**: TASK-001", report)


class StatusLifecycle(ReadinessCase):
    def test_engineering_status_is_refused(self):
        self.edit(T2, "| Status | READY |", "| Status | IN_PROGRESS |")
        _, findings = self.handoff()
        self.assertTrue(any(f.code == "INVALID_VALUE" and "engineering execution status" in f.message for f in findings.errors))

    def test_deferred_is_retired(self):
        self.edit(T4, "| Status | NEEDS_DISCOVERY |", "| Status | DEFERRED |")
        _, findings = self.handoff()
        self.assertTrue(any("DEFERRED is retired" in f.message for f in findings.errors))

    def test_ready_is_earned_not_declared(self):
        self.edit(T2, "| Status | READY |", "| Status | READY |")  # unchanged; now break a check
        self.edit(T2, "| AC-001 | an active account with that email | a reset is requested | one reset email is sent |",
                  "| AC-001 | an active account with that email | a reset is requested | the feature should work correctly |")
        docs, findings = self.handoff()
        readiness = docs["tasks/TASK-002.json"]["readiness"]
        self.assertFalse(readiness["checks"]["acceptance_criteria_testable"])
        self.assertTrue(any(f.code == "READY_NOT_MET" and "is not observable (correctly)" in f.message for f in findings.errors))
        self.assertAlmostEqual(66.7, docs["backlog-readiness.json"]["summary"]["ready_percentage"])
        self.assertEqual(["TASK-002"], docs["backlog-readiness.json"]["validation"]["ready_tasks_failing_definition_of_ready"])

    def test_readiness_history_must_record_ready(self):
        text = (self.project / T1).read_text(encoding="utf-8")
        (self.project / T1).write_text(text[:text.index("## Readiness history")], encoding="utf-8")
        self.assertGate("GB", cg.FAIL, "TASK-001 is READY but its readiness history records no transition to READY")

    def test_status_change_needs_a_history_entry(self):
        self.edit(T3, "| Status | READY |", "| Status | NEEDS_REVIEW |")
        self.assertGate("GB", cg.FAIL, "TASK-003 is NEEDS_REVIEW but its readiness history ends at READY")

    def test_partial_readiness_and_work_sets(self):
        self.set_status(T3, "NEEDS_REVIEW")
        docs, findings = self.handoff()
        self.assertEqual([], [(f.code, f.message) for f in findings.errors])
        doc = docs["backlog-readiness.json"]
        self.assertEqual("PARTIALLY_READY", doc["status"])
        self.assertEqual([["TASK-001"], ["TASK-002"]], [ws["task_ids"] for ws in doc["work_sets"]])
        self.assertEqual("PARTIALLY_READY", doc["phases"][0]["status"])
        self.assertEqual(["TASK-003"], doc["summary"]["meets_definition_of_ready_not_marked_ready"])
        self.assertGate("GB", cg.WARN, "The backlog is PARTIALLY READY: 2 of 3 active task(s) are ready")

    def test_no_ready_work_fails_the_gate(self):
        self.edit("project-state.md", "| Specification status | APPROVED |", "| Specification status | IN REVIEW |")
        gates, _ = self.gates()
        messages = [i.message for i in gates["GB"].issues]
        self.assertIn("No in-scope task is READY and passes the Definition of Ready: nothing can be handed to implementation.", messages)


class Dependencies(ReadinessCase):
    def test_blocked_dependency_blocks_readiness(self):
        self.set_status(T1, "BLOCKED", "Token store hosting unavailable")
        readiness = self.readiness("TASK-002")
        self.assertIn("Dependency TASK-001 is BLOCKED; it must be READY.", readiness["failures"])
        self.assertEqual("BLOCKED", readiness["recommended_status"])
        docs, _ = self.handoff()
        self.assertEqual([], docs["backlog-readiness.json"]["work_sets"])

    def test_cancelled_dependency(self):
        self.set_status(T1, "CANCELLED", "Dropped by DEC-001")
        self.assertIn("Dependency TASK-001 is CANCELLED.", self.failures("TASK-002"))

    def test_cycle_stops_sequencing(self):
        self.edit(T1, "| Blocked By | None |", "| Blocked By | TASK-003 |")
        docs, _ = self.handoff()
        self.assertEqual([], docs["backlog.json"]["sequencing"]["order"])
        self.assertIn("Task is in, or depends on, a dependency cycle.", docs["tasks/TASK-003.json"]["readiness"]["failures"])
        self.assertEqual(1, docs["backlog-readiness.json"]["validation"]["dependency_cycles"])
        self.assertGate("GB", cg.FAIL, "1 dependency cycle(s): no execution sequence exists until they are resolved.")


class Content(ReadinessCase):
    def test_criteria_align_with_the_source_requirements(self):
        self.edit(T3, "| AC-003 |", "| AC-006 |")
        self.assertIn("AC-006 belongs to SR-001, which the task does not implement.", self.failures("TASK-003"))

    def test_integration_impact_must_be_stated(self):
        text = (self.project / T2).read_text(encoding="utf-8")
        start, end = text.index("## Integration Impact"), text.index("## Constraints")
        (self.project / T2).write_text(text[:start] + text[end:], encoding="utf-8")
        readiness = self.readiness("TASK-002")
        self.assertFalse(readiness["checks"]["integration_impact_known"])
        self.assertTrue(any("Integration impact is not stated although the task relies on DEP-001" in f for f in readiness["failures"]))

    def test_unknown_integration_behaviour_blocks(self):
        self.edit(T2, "- Failure behaviour: when the service is unavailable the user still sees the neutral confirmation, and the "
                      "failure is logged (RISK-001).", "- Failure behaviour: TBD (Q-003).")
        readiness = self.readiness("TASK-002")
        self.assertIn("Integration impact contains TBD.", readiness["failures"])
        self.assertEqual("BLOCKED", readiness["recommended_status"])

    def test_api_impact_states_its_change(self):
        self.edit(T2, "## Constraints", "## API Impact\n\nThe reset request contract accepts an email address.\n\n## Constraints")
        self.assertIn("API impact does not state its change: NONE, CREATE, MODIFY or REMOVE.", self.failures("TASK-002"))

    def test_security_of_sensitive_work_cannot_be_not_applicable(self):
        self.edit(T1, "| Security | Token values carry at least 128 bits of randomness | SR-001 |\n"
                      "| Security | Marking a token used is atomic, so a token cannot be redeemed twice | RULE-001 |",
                  "| Security | N/A — nothing sensitive | DEC-001 |")
        readiness = self.readiness("TASK-001")
        self.assertFalse(readiness["checks"]["security_valid"])
        self.assertEqual("NEEDS_REVIEW", readiness["recommended_status"])

    def test_blocking_risk(self):
        self.edit("discovery/risks.md", "| Affected IDs | Last reviewed |", "| Affected IDs | Last reviewed | Blocks readiness |")
        self.edit("discovery/risks.md", "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
                  "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
        self.edit("discovery/risks.md", "| DEP-001, FR-AUTH-001 | 2026-09-24 |", "| DEP-001, FR-AUTH-001 | 2026-09-24 | Yes |")
        readiness = self.readiness("TASK-002")
        self.assertFalse(readiness["checks"]["blocking_risks_clear"])
        self.assertEqual("BLOCKED", readiness["recommended_status"])
        self.assertTrue(self.readiness("TASK-003")["checks"]["blocking_risks_clear"])

    def test_architecture_conflict_blocks_until_settled(self):
        self.edit(T2, "is emailed through the notification service.", "is emailed through a direct SMTP integration.")
        readiness = self.readiness("TASK-002")
        self.assertFalse(readiness["checks"]["architecture_conflicts_clear"])
        self.assertEqual("NEEDS_REVIEW", readiness["recommended_status"])
        self.assertGate("GB", cg.FAIL, "TASK-002 has an unresolved architecture conflict.")
        self.append("reviews/architecture-review.md",
                    "| FIND-001 | MAJOR | Architecture conflict | TASK-002 names direct SMTP | TASK-002 | ADR-001 | CHANGE PROPOSAL "
                    "| 9 | OPEN |")
        self.assertIn("ARCHITECTURE CONFLICT FIND-001 with ADR-001 is OPEN", " ".join(self.failures("TASK-002")))
        self.edit("reviews/architecture-review.md", "| 9 | OPEN |", "| 9 | WITHDRAWN |")
        self.assertTrue(self.readiness("TASK-002")["checks"]["architecture_conflicts_clear"])

    def test_major_review_finding_on_a_requirement_blocks_its_tasks(self):
        path = self.project / "reviews/specification-review.md"
        text = path.read_text(encoding="utf-8")
        start = text.index("### REVIEW-002")
        path.write_text(text[:start] + text[start:].replace("| Severity | OBSERVATION |", "| Severity | MAJOR |", 1), encoding="utf-8")
        readiness = self.readiness("TASK-002")
        self.assertIn("MAJOR specification review finding REVIEW-002 is OPEN: Reset email language is undecided.",
                      readiness["failures"])
        self.assertTrue(self.readiness("TASK-001")["checks"]["review_findings_clear"])


class Coverage(ReadinessCase):
    FEATURE = ("\n#### FEAT-003 — Reset audit trail\n\n| Field | Value |\n| --- | --- |\n| Epic | EPIC-001 |\n| Scope | In scope |\n"
               "| Goal | Resets are traceable |\n| Related Requirement IDs | FR-AUTH-001 |\n| Modules | MOD-001 |\n| Depends on | None |\n"
               "| External dependencies | None |\n| Priority | High |\n| Priority basis | Confirmed — SRC-001 |\n| Status | DRAFT |\n{extra}")

    def add_feature(self, extra: str = "") -> None:
        self.edit("backlog/backlog.md", "## Backlog index", self.FEATURE.format(extra=extra) + "\n## Backlog index")

    def test_feature_without_tasks_needs_a_reason(self):
        self.add_feature()
        self.assertGate("G9", cg.FAIL, "In-scope FEAT-003 has no task and records no reason why none is needed")

    def test_feature_without_tasks_with_a_reason(self):
        self.add_feature("| No tasks reason | Already implemented by the identity platform (SRC-001) |\n")
        self.assertGate("G9", cg.WARN, "FEAT-003 has no task: Already implemented by the identity platform (SRC-001)")
        docs, _ = self.handoff()
        self.assertEqual(1, docs["backlog-readiness.json"]["coverage"]["features_without_tasks_explained"])


class Revision(ReadinessCase):
    def baseline(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()):
            aci.main([str(self.project), "--baseline", "--reason", "Specification 1.0 approved"])

    def test_material_change_needs_a_new_revision(self):
        self.baseline()
        self.edit(T2, "The response is identical", "The response is always identical")
        self.assertGate("GB", cg.FAIL, "TASK-002 changed materially since the baseline but is still revision 1")
        self.edit(T2, "| Revision | 1 |", "| Revision | 2 |")
        gates, _ = self.gates()
        self.assertFalse(any("still revision" in i.message for i in gates["GB"].issues))

    def test_readiness_transition_is_not_a_change(self):
        self.baseline()
        self.set_status(T3, "NEEDS_REVIEW")
        docs, _ = self.handoff()
        self.assertNotIn("TASK-003", {d["id"] for d in docs["changes.json"]["detected_changes"]})


class Heuristics(unittest.TestCase):
    """Flags are for a reviewer to judge; these cases are the examples the workflow is meant to catch."""

    def bundle(self, tasks: list[dict], requirements: list[dict] | None = None) -> SimpleNamespace:
        for task in tasks:
            task.setdefault("status", "DRAFT")
            task.setdefault("scope", "in_scope")
            task.setdefault("acceptance_criteria", ["AC-900: a result is shown"])
            task.setdefault("source_requirements", [])
        reqs = requirements or []
        return SimpleNamespace(tasks=tasks, task_by_id={t["id"]: t for t in tasks}, req_by_id={r["id"]: r for r in reqs},
                               processes=[])

    def kinds(self, bundle) -> dict[str, list[list[str]]]:
        out: dict[str, list[list[str]]] = {}
        for flag in br.flags(bundle):
            out.setdefault(flag["kind"], []).append(flag["task_ids"])
        return out

    def test_possible_duplicate(self):
        found = self.kinds(self.bundle([{"id": "TASK-021", "title": "Allow admin to deactivate users"},
                                        {"id": "TASK-033", "title": "Add admin ability to disable user accounts"}]))
        self.assertEqual([["TASK-021", "TASK-033"]], found["POSSIBLE_DUPLICATE"])

    def test_contradictory_tasks(self):
        found = self.kinds(self.bundle([{"id": "TASK-014", "title": "Users may permanently delete their account"},
                                        {"id": "TASK-025", "title": "User accounts must never be permanently deleted"}]))
        self.assertEqual([["TASK-014", "TASK-025"]], found["CONTRADICTION"])

    def test_overloaded_task(self):
        found = self.kinds(self.bundle([{
            "id": "TASK-021", "title": "Implement complete user management, authentication, notifications, reporting, and audit history",
            "related_modules": ["MOD-001", "MOD-002", "MOD-003", "MOD-004"]}]))
        self.assertEqual([["TASK-021"]], found["NEEDS_DECOMPOSITION"])

    def test_fragmented_tasks(self):
        steps = [("TASK-030", "Create model"), ("TASK-031", "Add serializer"), ("TASK-032", "Add route"), ("TASK-033", "Add button")]
        found = self.kinds(self.bundle([{"id": i, "title": title, "feature": "FEAT-001", "source_requirements": ["FR-001"]}
                                        for i, title in steps]))
        self.assertEqual([["TASK-030", "TASK-031", "TASK-032", "TASK-033"]], found["FRAGMENTATION"])

    def test_missing_error_behaviour_names_relevant_cases_only(self):
        found = br.flags(self.bundle([{"id": "TASK-040", "title": "Users can upload a profile image",
                                       "acceptance_criteria": ["AC-901: the image appears on the profile"]}]))
        message = next(f["message"] for f in found if f["kind"] == "MISSING_ERROR_BEHAVIOUR")
        self.assertIn("unsupported file format, oversized file, upload failure", message)
        self.assertNotIn("external service", message)


if __name__ == "__main__":
    unittest.main()
