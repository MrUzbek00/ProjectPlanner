"""Tests for the stage gates (tools/check_gates.py) and impact analysis.

Run from the repository root:
    python -m unittest discover -s tools/tests -v

The fixture project is at stage 13 with gates G1-G12 and GR passing. Each test breaks
one thing and asserts which gate fails, and why.
"""

from __future__ import annotations

import contextlib
import io
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

import check_gates as cg  # noqa: E402
import impact_analysis as ia  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample-project"


class GateCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.project = Path(self._tmp.name) / "sample-project"
        shutil.copytree(FIXTURE, self.project, ignore=shutil.ignore_patterns("machine-handoff", "reports"))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def edit(self, rel: str, old: str, new: str) -> None:
        path = self.project / rel
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text, f"fixture text not found in {rel}: {old!r}")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def append(self, rel: str, text: str) -> None:
        path = self.project / rel
        path.write_text(path.read_text(encoding="utf-8").rstrip("\n") + "\n" + text + "\n", encoding="utf-8")

    def rereview(self, date: str = "2026-09-27") -> None:
        """Close the current specification review cycle and complete the next one, as a reviewer who
        re-examined every check and question and found nothing new."""
        import generate_handoff as gh
        import specification_review as sr
        _, _, bundle = gh.build(self.project, "2026-09-26T00:00:00Z")
        ok, messages = sr.start_cycle(self.project, bundle)
        self.assertTrue(ok, messages)
        self.complete_review_cycle(date)

    def complete_review_cycle(self, date: str = "2026-09-27") -> None:
        path = self.project / "reviews" / "specification-review.md"
        lines = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if "| NOT REVIEWED |" in line and not line.startswith("| Overall result"):
                first = line.split("|")[1]
                answer = "NO" if "unresolved contradictions" in first else "YES" if "?" in first else "PASS"
                line = line.replace("| NOT REVIEWED |", f"| {answer} |", 1)
            lines.append(line)
        text = "\n".join(lines) + "\n"
        for old, new in (("| Review date | TBD |", f"| Review date | {date} |"),
                         ("| Overall result | NOT REVIEWED |", "| Overall result | PASS WITH WARNINGS |"),
                         ("| Resolved since previous review | 1 |", "| Resolved since previous review | 0 |")):
            text = text.replace(old, new)
        path.write_text(text, encoding="utf-8")

    def gates(self):
        results, violations, _ = cg.evaluate(self.project)
        return {r.gate: r for r in results}, violations

    def assertGate(self, gate: str, result: str, fragment: str = "") -> None:
        gates, _ = self.gates()
        actual = gates[gate]
        messages = [i.message for i in actual.issues]
        self.assertEqual(result, actual.result, f"{gate}: {messages}")
        if fragment:
            self.assertTrue(any(fragment in m for m in messages), f"{gate} lacks {fragment!r}: {messages}")


class Fixture(GateCase):
    def test_gates_one_to_twelve_pass_and_thirteen_is_in_progress(self):
        gates, violations = self.gates()
        for gate in [f"G{n}" for n in range(1, 13)] + ["GR", "GB"]:
            self.assertNotEqual(cg.FAIL, gates[gate].result, f"{gate}: {[i.message for i in gates[gate].issues]}")
        self.assertEqual(cg.FAIL, gates["G13"].result)
        self.assertEqual([], [v.message for v in violations])

    def test_cli_exit_code_and_reports(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, cg.main([str(self.project)]))
        self.assertTrue((self.project / "reports" / "gate-report.md").is_file())
        self.assertIn("flowchart LR", (self.project / "reports" / "dependency-graph.md").read_text(encoding="utf-8"))


class IntakeAndDiscovery(GateCase):
    def test_missing_intake_item_fails_g1_and_everything_after(self):
        self.edit("discovery/project-intake.md", "| Deadlines | None stated by the owner | CONFIRMED | Round 1 answer |\n", "")
        gates, violations = self.gates()
        self.assertEqual(cg.FAIL, gates["G1"].result)
        self.assertIn("Prerequisite gate G1 fails.", [i.message for i in gates["G5"].issues])
        self.assertTrue(any("Return to stage 1" in v.message for v in violations))

    def test_unclassified_intake_item(self):
        self.edit("discovery/project-intake.md", "| Screenshots | None supplied | CONFIRMED |", "| Screenshots | None supplied | |")
        self.assertGate("G1", cg.FAIL, "'Screenshots' is not classified")

    def test_uninvestigated_category_fails_g2(self):
        self.edit("discovery/discovery-log.md", "| Migration | NOT APPLICABLE |", "| Migration | NOT STARTED |")
        self.assertGate("G2", cg.FAIL, "'Migration' has not been investigated")

    def test_project_wide_blocker_fails_g2(self):
        self.append("discovery/open-questions.md",
                    "| Q-009 | Business | Is the portal being replaced next year? | Changes the whole plan | BLOCKER | | Fixture owner | 3 | OPEN | | |")
        self.assertGate("G2", cg.FAIL, "BLOCKER question Q-009 is open and affects the whole project")

    def test_blocker_on_in_scope_work_is_not_quarantined(self):
        self.edit("discovery/open-questions.md", "| FR-AUTH-003, FEAT-002, SCOPE-002 |", "| FR-AUTH-003, FEAT-002, SCOPE-002, FR-AUTH-001 |")
        self.assertGate("G2", cg.FAIL, "BLOCKER question Q-002 is open")


class Requirements(GateCase):
    def test_unmeasured_wording_is_flagged(self):
        self.edit("specification/functional-requirements.md",
                  "A user can request a password-reset email by entering an email address.",
                  "A user can quickly and easily request a password-reset email.")
        self.assertGate("G3", cg.WARN, "unmeasured wording (easily, quickly)")

    def test_implementation_detail_is_flagged(self):
        self.edit("specification/functional-requirements.md",
                  "A user can request a password-reset email by entering an email address.",
                  "A user can request a password-reset email through a REST endpoint.")
        self.assertGate("G3", cg.WARN, "states implementation detail")

    def test_missing_rationale_fails(self):
        self.edit("specification/security-requirements.md", "**Rationale**\n\nA leaked token store must not allow anyone to reset a password.\n", "")
        self.assertGate("G3", cg.FAIL, "SR-001 is approved but has no rationale")

    def test_assumed_requirement_cannot_be_approved(self):
        self.edit("specification/security-requirements.md", "| Confidence | Confirmed |", "| Confidence | Likely |")
        self.assertGate("G3", cg.FAIL, "SR-001 is approved but its confidence is likely")

    def test_functional_requirement_needs_actor(self):
        self.edit("specification/functional-requirements.md", "| Actor | Registered user |\n| Trigger | The user asks", "| Trigger | The user asks")
        self.assertGate("G3", cg.WARN, "FR-AUTH-001 has no actor")

    def test_open_major_review_finding_fails(self):
        self.append("reviews/requirement-quality-review.md",
                    "| FIND-009 | MAJOR | FR-AUTH-002 contradicts RULE-001 | FR-AUTH-002 | 3 | OPEN | |")
        self.assertGate("G3", cg.FAIL, "MAJOR finding FIND-009 is open")

    def test_unreviewed_checklist_item_fails(self):
        self.edit("reviews/requirement-quality-review.md", "| No duplicate requirements | PASS |", "| No duplicate requirements | NOT REVIEWED |")
        self.assertGate("G3", cg.FAIL, "'No duplicate requirements' is NOT REVIEWED")


class ModelsScopeSpecification(GateCase):
    def test_process_without_exceptions_fails_g4(self):
        self.edit("specification/process-model.md",
                  "**Exceptions**\n\n- Identity cannot be verified: the call ends without a reset.\n", "")
        self.assertGate("G4", cg.FAIL, "PROC-001 does not state: exceptions")

    def test_unmapped_requirement_fails_g5(self):
        self.edit("specification/security-requirements.md", "| Related modules | MOD-001 |\n", "")
        self.assertGate("G5", cg.FAIL, "SR-001 is not mapped to any module")

    def test_pending_decision_needs_a_question(self):
        self.edit("discovery/open-questions.md", "| FR-AUTH-003, FEAT-002, SCOPE-002 |", "| FR-AUTH-003, FEAT-002 |")
        self.assertGate("G5", cg.FAIL, "SCOPE-002 is PENDING DECISION but no open question names it")

    def test_specification_cannot_introduce_requirements(self):
        self.edit("specification/technical-specification.md", "RULE-001 — a reset link", "RULE-001 and FR-AUTH-099 — a reset link")
        self.assertGate("G7", cg.FAIL, "mentions FR-AUTH-099, which no record defines")

    def test_specification_needs_all_sections(self):
        self.edit("specification/technical-specification.md", "## 17. File Management", "## File Management")
        self.assertGate("G7", cg.FAIL, "missing section(s) 17")

    def test_stale_specification_review_fails_gr_and_g8(self):
        self.edit("reviews/specification-review.md", "| Reviewed version | 1.0 |", "| Reviewed version | 0.9 |")
        self.assertGate("GR", cg.FAIL, "covers version 0.9; the specification is version 1.0")
        self.assertGate("G8", cg.FAIL, "Prerequisite gate GR fails.")

    def test_open_critical_finding_fails_gr(self):
        self.edit("reviews/specification-review.md", "| Severity | OBSERVATION |", "| Severity | CRITICAL |")
        self.assertGate("GR", cg.FAIL, "CRITICAL finding REVIEW-002 is OPEN: Reset email language is undecided (return to stage 2")


class BacklogSequencingRoadmap(GateCase):
    def test_implementation_level_task_title_warns(self):
        self.edit("backlog/tasks/TASK-001.md", "# TASK-001 — Reset tokens are stored so that they cannot be recovered",
                  "# TASK-001 — Create reset token model and table")
        self.assertGate("GB", cg.WARN, "reads as an implementation step")

    def test_in_scope_requirement_without_task_fails_g9(self):
        self.edit("backlog/tasks/TASK-001.md", "| Related Requirement IDs | SR-001, RULE-001 |", "| Related Requirement IDs | RULE-001 |")
        self.assertGate("G9", cg.FAIL, "In-scope SR-001 is not implemented by any task")

    def test_no_priority_scheme_fails_g10(self):
        self.edit("project-state.md", "| Priority scheme | Levels |\n", "")
        self.assertGate("G10", cg.FAIL, "declares no 'Priority scheme'")

    def test_mixed_priority_schemes_fail(self):
        self.edit("specification/security-requirements.md", "| Priority | High |", "| Priority | Must |")
        self.assertGate("G10", cg.FAIL, "outside the project's levels scheme")

    def test_hidden_prerequisite_warns(self):
        self.edit("backlog/tasks/TASK-004.md", "| Blocked By | None |", "| Blocked By | TASK-001 |")
        self.edit("backlog/backlog.md", "| S | NEEDS_DISCOVERY | None | PHASE-02 |", "| S | NEEDS_DISCOVERY | TASK-001 | PHASE-02 |")
        self.assertGate("G10", cg.WARN, "FEAT-002 does not declare a dependency on FEAT-001")

    def test_commitment_needs_a_decision(self):
        self.edit("backlog/backlog.md", "| Date | None |\n| Date basis | None |", "| Date | 2026-12-01 |\n| Date basis | Commitment |")
        self.assertGate("G11", cg.FAIL, "committed date without an existing decision")

    def test_date_without_basis_fails(self):
        self.edit("backlog/backlog.md", "| Date | None |\n| Date basis | None |", "| Date | 2026-12-01 |\n| Date basis | None |")
        self.assertGate("G11", cg.FAIL, "without a date basis")

    def test_high_risk_without_owner_fails(self):
        self.edit("discovery/risks.md", "failures are logged by the service | Fixture owner |", "failures are logged by the service | |")
        self.assertGate("G11", cg.FAIL, "High risk RISK-001 has no owner")


class FinalAndClaims(GateCase):
    def test_final_review_must_be_complete(self):
        self.edit("reviews/final-planning-review.md", "| The roadmap reflects dependencies | PASS |", "| The roadmap reflects dependencies | |")
        self.assertGate("G12", cg.FAIL, "'The roadmap reflects dependencies' has result blank")

    def test_claiming_a_failing_gate_is_a_violation(self):
        self.edit("specification/security-requirements.md", "| Related modules | MOD-001 |\n", "")
        _, violations = self.gates()
        messages = [v.message for v in violations]
        self.assertTrue(any("claims G5 PASS, but it fails" in m for m in messages), messages)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(1, cg.main([str(self.project), "--no-write"]))

    def test_planning_summary_must_answer_every_question(self):
        (self.project / "deliverables").mkdir()
        (self.project / "deliverables" / "planning-summary.md").write_text(
            "# Planning Summary\n\n## What problem are we solving?\n\nResets need the help desk.\n", encoding="utf-8")
        self.assertGate("G13", cg.FAIL, "does not answer 'What is still unknown?'")


class Impact(GateCase):
    def affected(self, *ids: str) -> set[str]:
        import generate_handoff as gh
        _, _, bundle = gh.build(self.project, "2026-09-26T00:00:00Z")
        return set(ia.Graph(bundle).affected(list(ids)))

    def test_rule_change_reaches_its_tasks_but_not_unrelated_workflows(self):
        affected = self.affected("RULE-001")
        self.assertTrue({"FR-AUTH-001", "FR-AUTH-002", "TASK-001", "TASK-003", "PROC-002", "PHASE-01"} <= affected)
        self.assertNotIn("PROC-001", affected)
        self.assertNotIn("TASK-004", affected)

    def test_entity_change_reaches_the_requirements_that_govern_it(self):
        self.assertIn("SR-001", self.affected("ENT-002"))

    def test_unknown_id_is_refused(self):
        with contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(2, ia.main([str(self.project), "FR-AUTH-099", "--no-write"]))


if __name__ == "__main__":
    unittest.main()
