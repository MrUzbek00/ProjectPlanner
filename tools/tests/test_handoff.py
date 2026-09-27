"""Tests for the machine handoff: generator, validator and Definition of Ready.

Run from the repository root:
    python -m unittest discover -s tools/tests -v

Each test copies the fixture project to a temporary folder, breaks it in one
specific way, and asserts the exact finding the tools must report.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

import generate_handoff as gh  # noqa: E402
import validate_handoff as vh  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample-project"
FIXED_TIME = "2026-09-26T00:00:00Z"
GENERATED = ("machine-handoff", "traceability/requirement-map.md")


class HandoffCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.project = Path(self._tmp.name) / "sample-project"
        shutil.copytree(FIXTURE, self.project, ignore=shutil.ignore_patterns("machine-handoff", "requirement-map.md"))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # helpers ---------------------------------------------------------------

    def edit(self, rel: str, old: str, new: str, count: int = 1) -> None:
        path = self.project / rel
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text, f"fixture text not found in {rel}: {old!r}")
        path.write_text(text.replace(old, new, count), encoding="utf-8")

    def check(self) -> tuple[vh.Findings, dict]:
        docs, src, _ = gh.build(self.project, FIXED_TIME)
        _, json_findings, _ = gh.finalize(docs, src)
        findings = vh.Findings()
        findings.extend(src.findings)
        findings.extend(json_findings)
        return findings, docs

    def generate(self) -> int:
        with contextlib.redirect_stdout(io.StringIO()):
            return gh.main([str(self.project), "--generated-at", FIXED_TIME])

    def error_codes(self, findings: vh.Findings) -> set[str]:
        return {f.code for f in findings.errors}

    def assertError(self, findings: vh.Findings, code: str, fragment: str = "") -> None:
        matches = [f for f in findings.errors if f.code == code and fragment in f.message]
        self.assertTrue(matches, f"expected {code} containing {fragment!r}; got {[(f.code, f.message) for f in findings.errors]}")


class ValidFixture(HandoffCase):
    def test_fixture_is_valid_and_ready(self):
        findings, docs = self.check()
        self.assertEqual([], [(f.code, f.message) for f in findings.errors])
        project = docs["project.json"]
        self.assertEqual("ready", project["handoff_status"])
        self.assertEqual(3, project["ready_tasks_count"])
        self.assertEqual(["TASK-001", "TASK-002", "TASK-003", "TASK-004"], docs["backlog.json"]["sequencing"]["order"])
        self.assertEqual(["TASK-001"], docs["backlog.json"]["executable_now"])

    def test_non_ready_task_reports_every_reason(self):
        _, docs = self.check()
        gaps = docs["tasks/TASK-004.json"]["readiness_gaps"]
        self.assertIn("Unresolved critical question Q-002.", gaps)
        self.assertTrue(any(g.startswith("Unresolved blocker:") for g in gaps))

    def test_output_is_deterministic_and_matches_committed_example(self):
        self.assertEqual(0, self.generate())
        first = {p.relative_to(self.project): p.read_bytes() for p in (self.project / "machine-handoff").rglob("*.json")}
        self.assertEqual(0, self.generate())
        second = {p.relative_to(self.project): p.read_bytes() for p in (self.project / "machine-handoff").rglob("*.json")}
        self.assertEqual(first, second, "two runs with the same inputs must be byte-identical")

        committed = FIXTURE / "machine-handoff"
        if not committed.is_dir():
            self.skipTest("no committed example output")
        for rel in [*sorted((self.project / "machine-handoff").rglob("*.json")), self.project / GENERATED[1]]:
            name = rel.relative_to(self.project)
            expected = (FIXTURE / name).read_bytes().replace(b"\r\n", b"\n")
            self.assertEqual(expected, rel.read_bytes().replace(b"\r\n", b"\n"),
                             f"{name} differs from the committed example; regenerate it")

    def test_written_handoff_validates_standalone(self):
        self.assertEqual(0, self.generate())
        findings, _ = vh.validate_files(vh.read_directory(self.project / "machine-handoff"), self.project)
        self.assertEqual([], [(f.code, f.message) for f in findings.errors])


class DefinitionOfReady(HandoffCase):
    def test_open_critical_question_blocks_ready(self):
        self.edit("discovery/open-questions.md", "| FR-AUTH-003, FEAT-002, SCOPE-002 |", "| FR-AUTH-003, FEAT-002, SCOPE-002, TASK-002 |")
        findings, docs = self.check()
        self.assertError(findings, "READY_NOT_MET", "TASK-002 is READY but: Unresolved critical question Q-002.")
        self.assertEqual("invalid", docs["project.json"]["handoff_status"])

    def test_open_non_blocking_question_does_not_block(self):
        findings, docs = self.check()
        self.assertNotIn("READY_NOT_MET", self.error_codes(findings))
        self.assertEqual([{"id": "Q-003", "question": "Should the reset email be sent in the user's language?", "blocking": False}],
                         docs["tasks/TASK-002.json"]["open_questions"])

    def test_missing_acceptance_criteria(self):
        self.edit("backlog/tasks/TASK-003.md",
                  "| AC-003 | a token issued 29 minutes ago and unused | a new password is submitted | the password changes and the token is marked used | FR-AUTH-002 | TEST-003 |\n", "")
        self.edit("backlog/tasks/TASK-003.md",
                  "| AC-004 | a token issued 31 minutes ago, or already used | a new password is submitted | the request is rejected and the password is unchanged | FR-AUTH-002, RULE-001 | TEST-003 |\n", "")
        findings, _ = self.check()
        self.assertError(findings, "READY_NOT_MET", "No acceptance criteria.")
        self.assertIn("SCHEMA_VIOLATION", self.error_codes(findings))

    def test_undocumented_security(self):
        self.edit("backlog/tasks/TASK-003.md", "| Security | A token expires 30 minutes after issue and is single use | RULE-001 |\n", "")
        findings, _ = self.check()
        self.assertError(findings, "READY_NOT_MET", "Security requirements are not documented")

    def test_security_not_applicable_is_refused_for_sensitive_work(self):
        # A password reset involves authentication and account recovery: its security behaviour must be stated.
        self.edit("backlog/tasks/TASK-003.md", "| Security | A token expires 30 minutes after issue and is single use | RULE-001 |",
                  "| Security | N/A — reason recorded for the test | DEC-001 |")
        findings, docs = self.check()
        self.assertError(findings, "READY_NOT_MET", "its security behaviour must be stated, not N/A")
        self.assertEqual({"security": "reason recorded for the test"}, docs["tasks/TASK-003.json"]["constraints"]["not_applicable"])
        self.assertEqual("NEEDS_REVIEW", docs["tasks/TASK-003.json"]["readiness"]["recommended_status"])

    def test_unreviewed_dependencies(self):
        self.edit("backlog/tasks/TASK-003.md", "| Blocked By | TASK-001 |", "| Blocked By | TBD |")
        findings, _ = self.check()
        self.assertError(findings, "READY_NOT_MET", "Dependencies have not been reviewed")

    def test_unreviewed_readiness_blockers(self):
        self.edit("backlog/tasks/TASK-003.md", "| Readiness blockers | None |", "| Readiness blockers | |")
        findings, _ = self.check()
        self.assertError(findings, "READY_NOT_MET", "Readiness blockers have not been reviewed")

    def test_missing_verification_method(self):
        self.edit("backlog/tasks/TASK-003.md", "| Required test levels | unit, integration, security, e2e |", "| Required test levels | |")
        findings, _ = self.check()
        self.assertError(findings, "READY_NOT_MET", "Required verification method is not defined")

    def test_proposed_adr_blocks_ready(self):
        self.edit("architecture/ADR-001-reset-email-delivery.md", "| Status | Accepted |", "| Status | Proposed |")
        findings, _ = self.check()
        self.assertError(findings, "READY_NOT_MET", "Architecture decision ADR-001 is proposed, not accepted.")

    def test_ready_task_depending_on_non_ready_task(self):
        self.edit("backlog/tasks/TASK-003.md", "| Blocked By | TASK-001 |", "| Blocked By | TASK-001, TASK-004 |")
        findings, _ = self.check()
        self.assertError(findings, "READY_NOT_MET", "Dependency TASK-004 is not in scope (scope: pending_decision).")

    def test_unapproved_specification(self):
        self.edit("project-state.md", "| Specification status | APPROVED |", "| Specification status | IN REVIEW |")
        findings, docs = self.check()
        self.assertError(findings, "APPROVED_WITHOUT_SPECIFICATION")
        self.assertError(findings, "READY_NOT_MET", "Specification is not approved")
        self.assertEqual("invalid", docs["project.json"]["handoff_status"])

    def test_approved_status_without_approval_record(self):
        self.edit("project-state.md", "| APR-001 | Fixture owner |", "| APR-001 | |")
        findings, _ = self.check()
        self.assertError(findings, "SPEC_APPROVAL_MISSING")


class References(HandoffCase):
    def test_unknown_requirement(self):
        self.edit("backlog/tasks/TASK-002.md", "| Related Requirement IDs | FR-AUTH-001 |", "| Related Requirement IDs | FR-AUTH-001, FR-AUTH-099 |")
        findings, _ = self.check()
        self.assertError(findings, "UNKNOWN_REFERENCE", "FR-AUTH-099")

    def test_duplicate_requirement_id(self):
        path = self.project / "specification/functional-requirements.md"
        text = path.read_text(encoding="utf-8")
        block = text[text.index("### FR-AUTH-001"):text.index("### FR-AUTH-002")]
        path.write_text(text + "\n" + block, encoding="utf-8")
        findings, _ = self.check()
        self.assertError(findings, "DUPLICATE_ID", "FR-AUTH-001")

    def test_dependency_cycle(self):
        self.edit("backlog/tasks/TASK-001.md", "| Blocked By | None |", "| Blocked By | TASK-003 |")
        findings, docs = self.check()
        self.assertError(findings, "DEPENDENCY_CYCLE", "TASK-001 -> TASK-003 -> TASK-001")
        self.assertIsNone(next(t for t in docs["backlog.json"]["tasks"] if t["id"] == "TASK-001")["sequence"])

    def test_self_dependency(self):
        self.edit("backlog/tasks/TASK-001.md", "| Blocked By | None |", "| Blocked By | TASK-001 |")
        findings, _ = self.check()
        self.assertError(findings, "SELF_DEPENDENCY")

    def test_phase_order_violation(self):
        self.edit("backlog/tasks/TASK-001.md", "| Phase | PHASE-01 |", "| Phase | PHASE-02 |")
        findings, _ = self.check()
        self.assertError(findings, "PHASE_ORDER", "TASK-002 (PHASE-01) depends on TASK-001")

    def test_feature_epic_mismatch(self):
        self.edit("backlog/tasks/TASK-002.md", "| Epic | EPIC-001 Self-service account access |", "| Epic | EPIC-002 Unknown |")
        findings, _ = self.check()
        self.assertError(findings, "HIERARCHY_MISMATCH", "TASK-002 names epic EPIC-002")

    def test_backlog_index_conflict(self):
        self.edit("backlog/backlog.md", "| High / confirmed | M | READY | TASK-001 | PHASE-01 |\n| TASK-003",
                  "| High / confirmed | M | BLOCKED | TASK-001 | PHASE-01 |\n| TASK-003")
        findings, _ = self.check()
        self.assertError(findings, "BACKLOG_INDEX_CONFLICT", "TASK-002 status")

    def test_test_names_unknown_acceptance_criterion(self):
        self.edit("quality/acceptance-tests.md", "| Acceptance criteria | AC-006 |", "| Acceptance criteria | AC-099 |")
        findings, _ = self.check()
        self.assertError(findings, "UNKNOWN_REFERENCE", "AC-099")

    def test_invalid_enum_value_is_located(self):
        self.edit("backlog/tasks/TASK-003.md", "| Status | READY |", "| Status | Ready-ish |")
        findings, _ = self.check()
        located = [f for f in findings.errors if f.code == "INVALID_VALUE"]
        self.assertTrue(located and located[0].location.startswith("backlog/tasks/TASK-003.md:"))
        self.assertIn("SCHEMA_VIOLATION", self.error_codes(findings))

    def test_legacy_identifier_warns(self):
        self.edit("backlog/backlog.md", "## Roadmap", "Legacy note: AT-001, BIZ-001 and FEAT-01-01.\n\n## Roadmap")
        findings, _ = self.check()
        self.assertTrue(any(f.code == "LEGACY_ID" for f in findings.warnings))


class WrittenOutput(HandoffCase):
    def handoff(self) -> Path:
        self.assertEqual(0, self.generate())
        return self.project / "machine-handoff"

    def test_hand_edited_json_is_detected(self):
        out = self.handoff()
        path = out / "tasks" / "TASK-001.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        data["status"] = "Ready"
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        findings, _ = vh.validate_files(vh.read_directory(out), self.project)
        codes = self.error_codes(findings)
        self.assertIn("ARTIFACT_HASH_MISMATCH", codes)
        self.assertIn("SCHEMA_VIOLATION", codes)
        self.assertIn("HANDOFF_STATUS_MISMATCH", codes)

    def test_invalid_json_syntax(self):
        out = self.handoff()
        (out / "requirements.json").write_text("{\n", encoding="utf-8")
        findings, _ = vh.validate_files(vh.read_directory(out), self.project)
        self.assertIn("JSON_SYNTAX", self.error_codes(findings))

    def test_crlf_checkout_is_not_a_hand_edit(self):
        out = self.handoff()
        for path in out.rglob("*.json"):
            path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
        findings, _ = vh.validate_files(vh.read_directory(out), self.project)
        self.assertEqual([], [(f.code, f.message) for f in findings.errors])

    def test_stale_handoff(self):
        out = self.handoff()
        self.edit("specification/functional-requirements.md", "A user can request", "A user may request")
        findings, _ = vh.validate_files(vh.read_directory(out), self.project)
        self.assertIn("STALE_HANDOFF", self.error_codes(findings))

    def test_unlisted_leftover_task_file(self):
        out = self.handoff()
        shutil.copy(out / "tasks" / "TASK-001.json", out / "tasks" / "TASK-099.json")
        findings, _ = vh.validate_files(vh.read_directory(out), self.project)
        self.assertIn("ARTIFACT_UNLISTED", self.error_codes(findings))
        self.assertIn("TASK_FILE_NAME", self.error_codes(findings))

    def test_invalid_handoff_is_written_as_invalid(self):
        self.edit("backlog/tasks/TASK-001.md", "| Blocked By | None |", "| Blocked By | TASK-003 |")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(1, gh.main([str(self.project), "--generated-at", FIXED_TIME]))
        project = json.loads((self.project / "machine-handoff" / "project.json").read_text(encoding="utf-8"))
        report = json.loads((self.project / "machine-handoff" / "validation-report.json").read_text(encoding="utf-8"))
        self.assertEqual("invalid", project["handoff_status"])
        self.assertEqual("INVALID", report["result"])

    def test_check_mode_writes_nothing(self):
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(0, gh.main([str(self.project), "--check", "--generated-at", FIXED_TIME]))
        self.assertFalse((self.project / "machine-handoff").exists())


class Schemas(unittest.TestCase):
    def test_every_schema_is_valid_draft_2020_12(self):
        validators = vh.load_validators()
        self.assertGreaterEqual(len(validators), 13)

    def test_id_patterns_match_the_parser(self):
        import planning_records as pr
        common = json.loads((TOOLS.parent / "schemas" / "common.schema.json").read_text(encoding="utf-8"))["$defs"]
        pairs = {"epicId": "EPIC", "featureId": "FEAT", "taskId": "TASK", "testId": "TEST", "adrId": "ADR",
                 "decisionId": "DEC", "questionId": "Q", "moduleId": "MOD", "phaseId": "PHASE", "acceptanceCriterionId": "AC",
                 "riskId": "RISK", "dependencyId": "DEP", "scopeItemId": "SCOPE", "processId": "PROC", "entityId": "ENT",
                 "principleId": "PRIN", "reviewFindingId": "REVIEW"}
        for schema_key, kind in pairs.items():
            self.assertEqual(common[schema_key]["pattern"], f"^{pr.ID_PATTERNS[kind]}$", schema_key)
        requirement = "|".join(pr.ID_PATTERNS[k] for k in pr.REQUIREMENT_KINDS)
        self.assertEqual(common["requirementId"]["pattern"], f"^(?:{requirement})$")
        for value in ("GOAL-001", "BR-001", "RULE-012", "FR-001", "FR-AUTH-001", "NFR-003", "DR-001", "IR-002", "SR-003", "UXR-004", "TR-004"):
            self.assertTrue(re.match(common["requirementId"]["pattern"], value), value)


if __name__ == "__main__":
    unittest.main()
