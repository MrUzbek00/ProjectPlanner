"""Tests for change-impact analysis: baselines, change records, review states, readiness and gate GC.

Run from the repository root:
    python -m unittest discover -s tools/tests -v

Each test copies the fixture, records a baseline (the trusted, approved plan),
then changes something and asserts what the analysis, the handoff and the
gates say about it.
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import analyze_change_impact as aci  # noqa: E402
import change_impact as ci  # noqa: E402
import check_gates as cg  # noqa: E402
import generate_handoff as gh  # noqa: E402
import validate_handoff as vh  # noqa: E402
from test_gates import GateCase  # noqa: E402

FR = "specification/functional-requirements.md"
DESCRIPTION = "A user can request a password-reset email by entering an email address."
NEW_DESCRIPTION = "A user can request a password-reset email by entering an email address or a username."


class ChangeCase(GateCase):
    def setUp(self) -> None:
        super().setUp()
        self.run_tool("--baseline", "--reason", "Specification 1.0 approved")

    def run_tool(self, *args: str) -> tuple[int, str]:
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = aci.main([str(self.project), *args])
        return code, out.getvalue() + err.getvalue()

    def changes(self) -> dict:
        docs, _, _ = gh.build(self.project, "2026-09-26T00:00:00Z")
        return docs["changes.json"]

    def docs(self) -> dict:
        docs, _, _ = gh.build(self.project, "2026-09-26T00:00:00Z")
        return docs

    def write_change(self, number: int = 1, *, status: str = "Approved", changed: str = "FR-AUTH-001",
                     change_type: str = "REQUIREMENT_CHANGE", approved_by: str = "Fixture owner", evidence: str = "DEC-001",
                     severity: str = "TBD", affected: str = "", reviews: str = "", new_work: str = "", roadmap: str = "",
                     risks: str = "", reason: str = "Users forget which address they registered with.") -> str:
        cid = f"CHANGE-{number:03d}"
        text = f"""# {cid} — Allow a reset by username

| Field | Value |
| --- | --- |
| Status | {status} |
| Date | 2026-09-26 |
| Change type | {change_type} |
| Changed artifacts | {changed} |
| Changed by | Fixture owner |
| Approved by | {approved_by} |
| Approval evidence | {evidence} |
| Severity | {severity} |
| Decisions required | None |
| Resolution status | Open |
| Superseded by | None |

## Previous state

{DESCRIPTION}

## New state

{NEW_DESCRIPTION}

## Reason

{reason}

## Affected artifacts

| Artifact | Impact level | Confidence | Review state | Resolution | Notes |
| --- | --- | --- | --- | --- | --- |
{affected}

## Required reviews

| Review area | Result | Evidence |
| --- | --- | --- |
{reviews}

## Risk impact

| Risk | Effect | Rationale |
| --- | --- | --- |
{risks}

## Roadmap impact

{roadmap}

## New work required

{new_work}
"""
        (self.project / "changes" / f"{cid}.md").write_text(text, encoding="utf-8")
        return cid

    def apply_description_change(self) -> None:
        self.edit(FR, DESCRIPTION, NEW_DESCRIPTION)

    def complete_change(self, *, resolution: str = "NO_CHANGE_NEEDED", status: str = "Implemented in plan") -> str:
        """Record CHANGE-001 with every analysed artifact dispositioned and every review done."""
        self.write_change(status="Approved")
        entry = self.changes()["changes"][0]
        rows = "\n".join(f"| {a['id']} | {a['level']} | {a['confidence']} | CURRENT | {resolution} | Reviewed |"
                         for a in entry["affected"] if a["level"] in ("DIRECT", "INDIRECT"))
        reviews = "\n".join(f"| {area['area']} | DONE | Reviewed with the owner |" for area in entry["review_areas"])
        return self.write_change(status=status, affected=rows, reviews=reviews, new_work="None — the reset form gains one field.",
                                 roadmap="PHASE-01 unchanged; no re-estimation needed.",
                                 risks="| RISK-001 | UNCHANGED | Delivery path unchanged |")


class Baseline(ChangeCase):
    def test_baseline_records_controlled_records(self):
        baseline = json.loads((self.project / ci.BASELINE_FILE).read_text(encoding="utf-8"))
        self.assertIn("FR-AUTH-001", baseline["records"])
        self.assertIn("TASK-002", baseline["records"])
        self.assertIn("MOD-001", baseline["records"])
        self.assertNotIn("Q-001", baseline["records"])
        self.assertEqual([], self.changes()["detected_changes"])

    def test_gate_is_clean_with_a_baseline_and_no_change(self):
        self.assertGate("GC", cg.PASS)

    def test_task_status_is_not_change_controlled(self):
        self.edit("backlog/tasks/TASK-004.md", "| Status | NEEDS_DISCOVERY |", "| Status | BLOCKED |")
        self.edit("backlog/backlog.md", "| S | NEEDS_DISCOVERY | None | PHASE-02 |", "| S | BLOCKED | None | PHASE-02 |")
        self.assertEqual([], self.changes()["detected_changes"])

    def test_baseline_is_refused_while_a_change_is_unrecorded(self):
        self.apply_description_change()
        code, out = self.run_tool("--baseline")
        self.assertEqual(1, code)
        self.assertIn("FR-AUTH-001 changed without an approved change record", out)

    def test_rebaseline_archives_history_and_incorporates_the_change(self):
        self.apply_description_change()
        self.complete_change()
        code, out = self.run_tool("--baseline", "--reason", "CHANGE-001 implemented")
        self.assertEqual(0, code, out)
        baseline = json.loads((self.project / ci.BASELINE_FILE).read_text(encoding="utf-8"))
        self.assertEqual(["CHANGE-001"], baseline["incorporated_changes"])
        self.assertEqual(1, len(list((self.project / ci.HISTORY_DIR).glob("baseline-*.json"))))
        self.assertIn(NEW_DESCRIPTION, baseline["records"]["FR-AUTH-001"]["text"])
        self.assertGate("GC", cg.PASS)


class UnrecordedChanges(ChangeCase):
    def test_a_text_edit_is_detected_and_fails_gc(self):
        self.apply_description_change()
        self.assertGate("GC", cg.FAIL, "FR-AUTH-001 was modified since the baseline without a change record")

    def test_a_text_edit_withdraws_readiness_downstream(self):
        self.apply_description_change()
        docs = self.docs()
        self.assertIn("Under change review: NEEDS_REVIEW (UNRECORDED).", docs["tasks/TASK-002.json"]["readiness_gaps"])
        summary = docs["changes.json"]["summary"]
        self.assertEqual(1, summary["unrecorded_changes"])
        self.assertGreaterEqual(summary["invalid_ready_tasks"], 1)
        gates, _ = self.gates()
        self.assertTrue(any("READY_NOT_MET" in i.message and "TASK-002" in i.message for i in gates["GB"].issues))
        self.assertTrue(any("Change-impact review (GC) fails" in i.message for i in gates["G12"].issues))

    def test_edit_before_approval_is_reported(self):
        self.apply_description_change()
        self.write_change(status="Proposed", approved_by="TBD", evidence="None")
        self.assertGate("GC", cg.FAIL, "FR-AUTH-001 was modified before CHANGE-001 was approved")

    def test_rejected_change_must_not_be_applied(self):
        self.apply_description_change()
        self.write_change(status="Rejected")
        self.assertGate("GC", cg.FAIL, "although CHANGE-001 was REJECTED")


class Analysis(ChangeCase):
    def entry(self) -> dict:
        self.write_change(status="Proposed", approved_by="TBD", evidence="None")
        return self.changes()["changes"][0]

    def test_levels_and_confidence(self):
        entry = self.entry()
        affected = {a["id"]: a for a in entry["affected"]}
        self.assertEqual(("DIRECT", "CONFIRMED"), (affected["FEAT-001"]["level"], affected["FEAT-001"]["confidence"]))
        self.assertEqual(("DIRECT", "CONFIRMED"), (affected["TASK-002"]["level"], affected["TASK-002"]["confidence"]))
        self.assertEqual("INDIRECT", affected["PHASE-01"]["level"])
        self.assertEqual(("POTENTIAL", "POSSIBLE"), (affected["BR-001"]["level"], affected["BR-001"]["confidence"]))
        self.assertIn("upstream assumption", affected["BR-001"]["reason"])
        self.assertEqual(("DIRECT", "CONFIRMED"), (affected["FR-AUTH-002"]["level"], affected["FR-AUTH-002"]["confidence"]))
        self.assertEqual("INDIRECT", affected["TASK-001"]["level"])
        self.assertEqual(("INDIRECT", "LIKELY"), (affected["EPIC-001"]["level"], affected["EPIC-001"]["confidence"]))
        self.assertEqual("POTENTIAL", affected["FR-AUTH-003"]["level"])
        self.assertIn("shares MOD-001", affected["FR-AUTH-003"]["reason"])

    def test_severity_is_computed_and_explained(self):
        entry = self.entry()
        self.assertEqual("HIGH", entry["computed_severity"])
        self.assertTrue(any("READY tasks lose their readiness" in d for d in entry["severity_drivers"]))

    def test_business_basis_change_is_critical(self):
        self.write_change(status="Proposed", changed="BR-001", approved_by="TBD", evidence="None")
        self.assertEqual("CRITICAL", self.changes()["changes"][0]["computed_severity"])

    def test_proposed_change_does_not_alter_the_plan(self):
        entry = self.entry()
        self.assertFalse(entry["marks_plan"])
        self.assertTrue(all(a["review_state"] == "CURRENT" for a in entry["affected"]))
        self.assertNotIn("Under change review", " ".join(self.docs()["tasks/TASK-002.json"]["readiness_gaps"]))

    def test_new_acceptance_criterion_is_reported_as_missing_work(self):
        self.edit(FR, "- AC-002 — A request for an address with no active account is rejected silently: no email is sent and the response is identical.",
                  "- AC-002 — A request for an address with no active account is rejected silently: no email is sent and the response is identical.\n"
                  "- AC-099 — A request by username is rejected silently when the username does not exist.")
        entry = self.entry()
        self.assertTrue(any("AC-099 of FR-AUTH-001 is delivered by no task" in m for m in entry["missing_work"]))
        self.assertTrue(any("gains AC-099 since the baseline" in m for m in entry["missing_work"]))
        self.assertTrue(any("Confirm that the existing tasks (TASK-002) cover the new state" in m for m in entry["missing_work"]))

    def test_impact_report_is_written(self):
        self.write_change(status="Proposed", approved_by="TBD", evidence="None")
        code, out = self.run_tool("CHANGE-001")
        self.assertEqual(0, code, out)
        report = (self.project / "changes" / "CHANGE-001-impact-report.md").read_text(encoding="utf-8")
        for heading in ("## Direct impact", "## Indirect impact", "## Potential impact", "## Required reviews",
                        "## New work that may be required", "## Roadmap impact", "## Risk impact", "## Documents to regenerate or review"):
            self.assertIn(heading, report)
        self.assertIn(" 7. Severity                  HIGH", out)

    def test_report_shows_previous_and_current_state(self):
        self.apply_description_change()
        self.write_change(status="Approved")
        self.run_tool("CHANGE-001")
        report = (self.project / "changes" / "CHANGE-001-impact-report.md").read_text(encoding="utf-8")
        self.assertIn("FR-AUTH-001 — previous state (baseline)", report)
        self.assertIn(NEW_DESCRIPTION, report)

    def test_what_if_needs_no_change_record(self):
        code, out = self.run_tool("SR-001", "--type", "SECURITY_CHANGE", "--no-write")
        self.assertEqual(0, code, out)
        self.assertIn("TASK-001", out)


class Lifecycle(ChangeCase):
    def test_approved_change_marks_affected_artifacts_for_review(self):
        self.apply_description_change()
        self.write_change(status="Approved")
        docs = self.docs()
        states = {s["id"]: s for s in docs["changes.json"]["artifact_states"]}
        self.assertEqual("NEEDS_REVIEW", states["TASK-002"]["state"])
        self.assertEqual(["CHANGE-001"], states["TASK-002"]["change_ids"])
        self.assertIn("TASK-002", docs["changes.json"]["changes"][0]["invalidated_items"])
        self.assertGate("GC", cg.FAIL, "TASK-002 is READY but NEEDS_REVIEW")

    def test_decision_needs_a_person(self):
        self.apply_description_change()
        self.write_change(status="Approved", approved_by="TBD", evidence="None")
        self.assertGate("GC", cg.FAIL, "CHANGE-001 is APPROVED but records no human decision")

    def test_severity_cannot_be_understated(self):
        self.write_change(status="Proposed", approved_by="TBD", evidence="None", severity="Low")
        self.assertGate("GC", cg.FAIL, "declares severity LOW, below the computed HIGH")

    def test_reason_is_required(self):
        self.write_change(status="Proposed", approved_by="TBD", evidence="None", reason="")
        self.assertGate("GC", cg.FAIL, "does not state why the change is needed")

    def test_invalid_disposition_is_kept_and_withdraws_readiness(self):
        self.apply_description_change()
        self.write_change(status="Approved", affected="| TASK-002 | DIRECT | CONFIRMED | INVALID | | Rework the request form |")
        docs = self.docs()
        states = {s["id"]: s for s in docs["changes.json"]["artifact_states"]}
        self.assertEqual("INVALID", states["TASK-002"]["state"])
        self.assertIn("Under change review: INVALID (CHANGE-001).", docs["tasks/TASK-002.json"]["readiness_gaps"])

    def test_critical_impact_cannot_stay_unresolved(self):
        self.edit("specification/business-requirements.md", "### BR-001 — Users can reset a forgotten password by themselves",
                  "### BR-001 — Users can reset a forgotten password or username by themselves")
        self.write_change(status="Approved", changed="BR-001")
        self.assertGate("GC", cg.FAIL, "CRITICAL impact of CHANGE-001 is unresolved")

    def test_fully_implemented_change_passes(self):
        self.apply_description_change()
        self.complete_change()
        # Propagation is never assumed: the specification is re-reviewed after the change.
        self.assertGate("GR", cg.FAIL, "CHANGE-001 (REQUIREMENT_CHANGE, HIGH) is dated 2026-09-26, after review cycle 2")
        self.rereview()
        gates, _ = self.gates()
        self.assertNotEqual(cg.FAIL, gates["GR"].result, [i.message for i in gates["GR"].issues])
        self.assertNotEqual(cg.FAIL, gates["GC"].result, [i.message for i in gates["GC"].issues])
        docs = self.docs()
        self.assertEqual([], docs["tasks/TASK-002.json"]["readiness_gaps"])
        self.assertEqual(0, docs["changes.json"]["summary"]["items_needing_review"])

    def test_implemented_change_needs_every_review(self):
        self.apply_description_change()
        self.complete_change()
        self.edit("changes/CHANGE-001.md", "| UI screens | DONE |", "| UI screens | PENDING |")
        self.assertGate("GC", cg.FAIL, "has not completed the required review 'UI screens'")

    def test_implemented_change_must_actually_change_the_plan(self):
        self.complete_change()
        self.assertGate("GC", cg.FAIL, "CHANGE-001 is IMPLEMENTED_IN_PLAN but FR-AUTH-001 is unchanged since the baseline")

    def test_claimed_update_must_be_real(self):
        self.apply_description_change()
        self.complete_change(resolution="UPDATED")
        self.assertGate("GC", cg.FAIL, "records TASK-002 as UPDATED, but TASK-002 is unchanged since the baseline")

    def test_implemented_change_needs_new_work_statement(self):
        self.apply_description_change()
        self.complete_change()
        self.edit("changes/CHANGE-001.md", "None — the reset form gains one field.", "")
        self.assertGate("GC", cg.FAIL, "does not state the new work it requires")


class Handoff(ChangeCase):
    def test_changes_json_validates_standalone(self):
        self.apply_description_change()
        self.write_change(status="Approved")
        with contextlib.redirect_stdout(io.StringIO()):
            gh.main([str(self.project), "--generated-at", "2026-09-26T00:00:00Z"])
        findings, bundle = vh.validate_files(vh.read_directory(self.project / "machine-handoff"), self.project)
        codes = {f.code for f in findings.errors}
        self.assertEqual([], [f.message for f in findings.errors if f.location == "changes.json"])
        self.assertNotIn("CHANGE_STATE_MISMATCH", codes)
        self.assertIn("READY_NOT_MET", codes)
        self.assertEqual("NEEDS_REVIEW", bundle.artifact_state["TASK-002"]["state"])

    def test_hand_edited_state_is_detected(self):
        self.apply_description_change()
        self.write_change(status="Approved")
        docs = self.docs()
        docs["changes.json"]["artifact_states"] = []
        bundle = vh.Bundle(docs)
        findings = vh.Findings()
        vh.change_findings(bundle, findings)
        self.assertIn("CHANGE_STATE_MISMATCH", {f.code for f in findings.errors})


if __name__ == "__main__":
    unittest.main()
