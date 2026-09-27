"""Tests for the independent specification review (tools/specification_review.py) and gate GR.

Run from the repository root:
    python -m unittest discover -s tools/tests -v

The fixture's review is in cycle 2: cycle 1 (version 0.9) raised a MAJOR finding
and an observation and failed; the author resolved the MAJOR finding and cycle 2
(version 1.0) verified it, leaving the observation open. Each test breaks one
thing and asserts what the review, the gates and the handoff say about it.
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

import check_gates as cg  # noqa: E402
import generate_handoff as gh  # noqa: E402
import specification_review as sr  # noqa: E402
import validate_handoff as vh  # noqa: E402
from test_gates import GateCase  # noqa: E402

REVIEW = "reviews/specification-review.md"
SNAPSHOT_1 = "reviews/history/specification-review-cycle-001.md"
SNAPSHOT_2 = "reviews/history/specification-review-cycle-002.md"
TIME = "2026-09-26T00:00:00Z"


class ReviewCase(GateCase):
    def evaluation(self) -> sr.Evaluation:
        _, src, _ = gh.build(self.project, TIME)
        return src.spec_review

    def handoff(self) -> tuple[dict, vh.Findings]:
        docs, src, _ = gh.build(self.project, TIME)
        _, findings, _ = gh.finalize(docs, src)
        return docs, findings

    def edit_finding(self, fid: str, old: str, new: str) -> None:
        """Edit inside one finding's record block only."""
        path = self.project / REVIEW
        text = path.read_text(encoding="utf-8")
        start = text.index(f"### {fid} ")
        end = min(i for i in (text.find("\n### ", start + 1), text.find("\n## ", start + 1)) if i != -1)
        block = text[start:end]
        self.assertIn(old, block, f"{old!r} not in {fid}")
        path.write_text(text[:start] + block.replace(old, new, 1) + text[end:], encoding="utf-8")

    def header(self, **values: str) -> None:
        for label, value in values.items():
            label = label.replace("_", " ").capitalize()
            path = self.project / REVIEW
            text = path.read_text(encoding="utf-8")
            prefix = f"| {label} | "
            start = text.index(prefix)
            end = text.index("\n", start)
            path.write_text(text[:start] + f"{prefix}{value} |" + text[end:], encoding="utf-8")

    def add_finding(self, fid: str, *, severity: str = "MINOR", status: str = "OPEN", raised: str = "2",
                    title: str = "Reset link wording differs between documents", affected: str = "FR-AUTH-002",
                    evidence: str = "FR-AUTH-002 says 'reset link'; AC-003 says 'link'.") -> None:
        block = f"""### {fid} — {title}

| Field | Value |
| --- | --- |
| Severity | {severity} |
| Category | TERMINOLOGY |
| Status | {status} |
| Raised in cycle | {raised} |
| Affected artifacts | {affected} |
| Return to stage | 3 — Requirement Analysis |

**Evidence**

{evidence}

**Why it matters**

Readers may take them for different things.

**Required action**

Use one term.

"""
        self.edit(REVIEW, "## Dismissed candidates", block + "## Dismissed candidates")

    def gr_messages(self) -> list[str]:
        gates, _ = self.gates()
        return [i.message for i in gates["GR"].issues]


class Fixture(ReviewCase):
    def test_fixture_review_passes_with_warnings(self):
        ev = self.evaluation()
        self.assertEqual(sr.WARN, ev.overall)
        self.assertEqual(2, ev.cycle)
        self.assertEqual({"critical": 0, "major": 0, "minor": 0, "observation": 1, "open": 1, "accepted_risk": 0,
                          "resolved_since_previous": 1, "total": 2, "resolved": 1, "rejected": 0}, ev.counts)
        self.assertEqual([], [i.message for i in ev.errors])
        self.assertGate("GR", cg.WARN, "OBSERVATION finding REVIEW-002 is OPEN")

    def test_machine_output_carries_cycles_findings_and_summary(self):
        docs, findings = self.handoff()
        self.assertEqual([], [(f.code, f.message) for f in findings.errors])
        review = docs["specification-review.json"]
        self.assertEqual("PASS_WITH_WARNINGS", review["overall_result"])
        self.assertEqual("1.0", review["review_version"])
        self.assertEqual([(1, "FAIL", 2, "0.9"), (2, "PASS_WITH_WARNINGS", 1, "1.0")],
                         [(c["review_cycle"], c["overall_result"], c["finding_count"], c["review_version"]) for c in review["cycles"]])
        self.assertEqual(["REVIEW-001", "REVIEW-002"], [f["id"] for f in review["findings"]])
        resolved = review["findings"][0]
        self.assertEqual(("RESOLVED", 1, 2), (resolved["status"], resolved["raised_in_cycle"], resolved["closed_in_cycle"]))
        self.assertEqual(["FR-AUTH-003", "SCOPE-002"], resolved["resolution"]["changed_artifacts"])
        self.assertEqual({"result": "PASS_WITH_WARNINGS", "review_cycle": 2, "review_version": "1.0"},
                         docs["project.json"]["specification_review"])
        self.assertEqual("ready", docs["project.json"]["handoff_status"])

    def test_result_rule(self):
        self.assertEqual(sr.PASS, sr.result_for([]))
        self.assertEqual(sr.PASS, sr.result_for([("MAJOR", "RESOLVED"), ("MINOR", "REJECTED")]))
        self.assertEqual(sr.WARN, sr.result_for([("MINOR", "OPEN"), ("OBSERVATION", "ACKNOWLEDGED")]))
        self.assertEqual(sr.WARN, sr.result_for([("MAJOR", "ACCEPTED_RISK")]))
        self.assertEqual(sr.FAIL, sr.result_for([("MAJOR", "IN_RESOLUTION")]))
        self.assertEqual(sr.FAIL, sr.result_for([("CRITICAL", "ACCEPTED_RISK")]))
        self.assertEqual(sr.FAIL, sr.result_for([("MAJOR", "ACKNOWLEDGED"), ("MINOR", "RESOLVED")]))


class Independence(ReviewCase):
    def test_author_cannot_review_their_own_specification(self):
        self.header(reviewer="Fixture analyst — SPECIFICATION REVIEWER")
        self.assertGate("GR", cg.FAIL, "is the specification's author. The author does not grade their own work")

    def test_independence_must_be_stated(self):
        self.header(independence="")
        self.assertGate("GR", cg.FAIL, "does not state how the reviewer is independent")


class ResultAndConclusion(ReviewCase):
    def make_major_open(self) -> None:
        self.edit_finding("REVIEW-002", "| Severity | OBSERVATION |", "| Severity | MAJOR |")
        self.header(overall_result="FAIL", open_major="1", open_observations="0")
        self.edit(REVIEW, "| Is the specification safe to use as the basis for backlog planning? | YES |",
                  "| Is the specification safe to use as the basis for backlog planning? | NO |")

    def test_unresolved_major_finding_fails_and_blocks_the_backlog(self):
        self.make_major_open()
        gates, _ = self.gates()
        self.assertEqual(["MAJOR finding REVIEW-002 is OPEN: Reset email language is undecided (return to stage 2 — Discovery)."],
                         [i.message for i in gates["GR"].issues if i.level == "error"])
        self.assertIn("Prerequisite gate GR fails.", [i.message for i in gates["G8"].issues])
        self.assertEqual(cg.FAIL, gates["G9"].result)
        self.assertTrue(any("backlog is provisional" in i.message for i in gates["GR"].issues))
        docs, findings = self.handoff()
        self.assertEqual("FAIL", docs["specification-review.json"]["overall_result"])
        self.assertIn("Specification review fails (cycle 2): 1 open MAJOR.", docs["tasks/TASK-001.json"]["readiness_gaps"])
        self.assertIn("READY_NOT_MET", {f.code for f in findings.errors})
        self.assertNotEqual("ready", docs["project.json"]["handoff_status"])

    def test_stated_result_must_be_the_one_the_findings_support(self):
        self.header(overall_result="PASS")
        self.assertGate("GR", cg.FAIL, "states 'Overall result' PASS; its findings support PASS WITH WARNINGS")

    def test_counts_must_match_the_findings(self):
        self.header(open_observations="0")
        self.assertGate("GR", cg.FAIL, "states Open observations: 0; the findings show 1")

    def test_conclusion_must_agree_with_the_result(self):
        self.make_major_open()
        self.edit(REVIEW, "| Is the specification safe to use as the basis for backlog planning? | NO |",
                  "| Is the specification safe to use as the basis for backlog planning? | YES |")
        self.assertGate("GR", cg.FAIL, "but its result is FAIL; the answer is NO")

    def test_problem_answer_needs_an_open_finding(self):
        self.edit(REVIEW, "| Are permissions defined? | YES |", "| Are permissions defined? | NO |")
        self.assertGate("GR", cg.FAIL, "'Are permissions defined?' is answered NO but cites no open REVIEW-### finding")


class AcceptedRisk(ReviewCase):
    def accept(self, severity: str = "MAJOR", approver: str = "Fixture owner", evidence: str = "DEC-002",
               affected: str = "Q-003, FR-AUTH-001, RISK-001") -> None:
        self.edit_finding("REVIEW-002", "| Severity | OBSERVATION |", f"| Severity | {severity} |")
        self.edit_finding("REVIEW-002", "| Status | OPEN |", "| Status | ACCEPTED_RISK |")
        self.edit_finding("REVIEW-002", "| Affected artifacts | Q-003, FR-AUTH-001 |", f"| Affected artifacts | {affected} |")
        self.edit_finding("REVIEW-002", "| Closed in cycle | |", "| Closed in cycle | 2 |")
        self.edit_finding("REVIEW-002", "| Resolution | |", "| Resolution | English-only email is acceptable for the release |")
        self.edit_finding("REVIEW-002", "| Approved by | |", f"| Approved by | {approver} |")
        self.edit_finding("REVIEW-002", "| Approval evidence | |", f"| Approval evidence | {evidence} |")
        self.header(open_observations="0", open_findings="0", accepted_risks="1")

    def test_major_accepted_by_a_person_passes_with_a_visible_warning(self):
        self.accept()
        self.assertGate("GR", cg.WARN, "is an ACCEPTED RISK, approved by Fixture owner")
        ev = self.evaluation()
        self.assertEqual((1, 1), (ev.counts["accepted_risk"], ev.counts["resolved"]))
        docs, _ = self.handoff()
        finding = docs["specification-review.json"]["findings"][1]
        self.assertEqual("ACCEPTED_RISK", finding["status"])
        self.assertEqual(["DEC-002"], finding["resolution"]["approval_evidence"])

    def test_accepted_major_risk_belongs_in_the_risk_register(self):
        self.accept(affected="Q-003, FR-AUTH-001")
        self.assertGate("GR", cg.WARN, "no RISK-### in the risk register records")

    def test_critical_finding_cannot_be_accepted(self):
        self.accept(severity="CRITICAL")
        self.assertGate("GR", cg.FAIL, "CRITICAL finding REVIEW-002 is recorded as ACCEPTED_RISK")

    def test_the_author_cannot_accept_the_risk(self):
        self.accept(approver="Fixture analyst")
        self.assertGate("GR", cg.FAIL, "who wrote or reviewed the specification")

    def test_acceptance_needs_recorded_evidence(self):
        self.accept(evidence="DEC-099")
        self.assertGate("GR", cg.FAIL, "cites DEC-099 as approval evidence, but it is not in the decision log")


class Resolution(ReviewCase):
    def test_resolved_needs_verification(self):
        self.edit_finding("REVIEW-001", "| Verification | Re-reviewed in cycle 2:", "| Verification | |\n| Notes | Re-reviewed in cycle 2:")
        self.assertGate("GR", cg.FAIL, "REVIEW-001 is RESOLVED without 'Verification'")

    def test_resolution_is_verified_in_a_later_cycle(self):
        self.edit_finding("REVIEW-001", "| Raised in cycle | 1 |", "| Raised in cycle | 2 |")
        self.assertGate("GR", cg.FAIL, "REVIEW-001 is RESOLVED in the cycle that raised it")

    def reject(self, severity: str = "OBSERVATION") -> None:
        self.edit_finding("REVIEW-002", "| Severity | OBSERVATION |", f"| Severity | {severity} |")
        self.edit_finding("REVIEW-002", "| Status | OPEN |", "| Status | REJECTED |")
        self.edit_finding("REVIEW-002", "| Closed in cycle | |", "| Closed in cycle | 2 |")
        self.edit_finding("REVIEW-002", "| Resolution | |", "| Resolution | The email language is fixed by SRC-001 |")
        self.edit_finding("REVIEW-002", "| Resolved by | |", "| Resolved by | Fixture reviewer |")
        self.header(overall_result="PASS", open_observations="0", open_findings="0")
        self.edit(REVIEW, "PASS WITH WARNINGS: REVIEW-002 is an observation", "PASS")

    def test_rejected_observation_closes_the_review(self):
        self.reject()
        self.assertGate("GR", cg.PASS)
        self.assertEqual(sr.PASS, self.evaluation().overall)

    def test_rejecting_a_major_finding_needs_a_human_decision(self):
        self.reject(severity="MAJOR")
        self.assertGate("GR", cg.FAIL, "REVIEW-002 is REJECTED without 'Approved by'")

    def test_resolution_names_the_changed_records(self):
        self.edit_finding("REVIEW-001", "| Changed artifacts | FR-AUTH-003, SCOPE-002 |", "| Changed artifacts | None |")
        self.assertGate("GR", cg.FAIL, "REVIEW-001 is RESOLVED but names no changed artifact")


class FindingQuality(ReviewCase):
    def test_major_finding_must_cite_specific_artifacts(self):
        self.add_finding("REVIEW-003", severity="MAJOR", affected="None", evidence="The specification seems unclear.")
        messages = self.gr_messages()
        self.assertTrue(any("MAJOR finding REVIEW-003 names no affected artifact" in m for m in messages), messages)
        self.assertTrue(any("does not cite a specific artifact in its evidence" in m for m in messages), messages)

    def test_reference_to_a_missing_record_is_broken(self):
        self.edit_finding("REVIEW-002", "| Affected artifacts | Q-003, FR-AUTH-001 |", "| Affected artifacts | Q-003, FR-AUTH-099 |")
        self.assertGate("GR", cg.FAIL, "REVIEW-002 refers to FR-AUTH-099, which no record defines")

    def test_duplicate_findings_are_rejected(self):
        self.add_finding("REVIEW-003", title="Reset email language is undecided")
        self.assertGate("GR", cg.FAIL, "REVIEW-003 duplicates REVIEW-002")

    def test_finding_ids_are_never_reused(self):
        self.add_finding("REVIEW-002")
        self.assertGate("GR", cg.FAIL, "REVIEW-002 is recorded twice")

    def test_new_finding_in_this_cycle_is_counted(self):
        self.add_finding("REVIEW-003")
        self.header(open_minor="1", open_findings="2", findings_raised="3")
        self.assertGate("GR", cg.WARN, "MINOR finding REVIEW-003 is OPEN")


class Checklist(ReviewCase):
    def test_failed_check_needs_a_finding(self):
        self.edit(REVIEW, "| Terminology | One term per concept | PASS |", "| Terminology | One term per concept | FAIL |")
        self.assertGate("GR", cg.FAIL, "Check 'One term per concept' FAILED but cites no REVIEW-### finding")

    def test_failed_check_on_a_closed_finding_must_be_rereviewed(self):
        self.edit(REVIEW, "match evidence | PASS | FR-AUTH-003 now states TBD (Q-002); REVIEW-001 verified |",
                  "match evidence | FAIL | REVIEW-001 |")
        self.assertGate("GR", cg.FAIL, "is still FAIL but REVIEW-001 is closed")

    def test_every_review_area_is_covered(self):
        self.edit(REVIEW, "| Terminology | One term per concept | PASS | \"reset link\" and \"reset token\" are distinguished in ENT-002 |\n", "")
        self.assertGate("GR", cg.FAIL, "does not cover the review area 'Terminology'")

    def test_unexamined_check_fails(self):
        self.edit(REVIEW, "| Data model | Every referenced entity is defined; no duplicate concept | PASS |",
                  "| Data model | Every referenced entity is defined; no duplicate concept | NOT REVIEWED |")
        self.assertGate("GR", cg.FAIL, "is NOT REVIEWED")


class History(ReviewCase):
    def test_a_finding_is_never_deleted(self):
        path = self.project / REVIEW
        text = path.read_text(encoding="utf-8")
        start, end = text.index("### REVIEW-002"), text.index("## Dismissed candidates")
        path.write_text(text[:start] + text[end:], encoding="utf-8")
        self.assertGate("GR", cg.FAIL, "REVIEW-002 was recorded in cycle 1 and is missing from the review")

    def test_history_cannot_be_rewritten(self):
        self.edit(REVIEW, "| 0.9 | Fixture reviewer — SPECIFICATION REVIEWER | FAIL | 0 | 1 |",
                  "| 0.9 | Fixture reviewer — SPECIFICATION REVIEWER | PASS | 0 | 0 |")
        self.assertGate("GR", cg.FAIL, "The history row for cycle 1 disagrees with its snapshot")

    def test_closed_cycle_snapshot_must_exist(self):
        (self.project / SNAPSHOT_1).unlink()
        self.assertGate("GR", cg.FAIL, "Cycle 1's snapshot reviews/history/specification-review-cycle-001.md does not exist")

    def test_finding_cannot_be_backdated(self):
        self.add_finding("REVIEW-003", raised="1")
        self.assertGate("GR", cg.FAIL, "REVIEW-003 claims to be raised in cycle 1, but that cycle's snapshot does not contain it")

    def test_start_cycle_freezes_the_cycle_and_reopens_every_check(self):
        before = (self.project / REVIEW).read_bytes()
        _, _, bundle = gh.build(self.project, TIME)
        ok, messages = sr.start_cycle(self.project, bundle)
        self.assertTrue(ok, messages)
        self.assertEqual(before, (self.project / SNAPSHOT_2).read_bytes())
        text = (self.project / REVIEW).read_text(encoding="utf-8")
        self.assertIn("| Review cycle | 3 |", text)
        self.assertIn("| Review date | TBD |", text)
        self.assertNotIn("| PASS |", text)
        self.assertIn("| 2 | 2026-09-19 | 1.0 | Fixture reviewer — SPECIFICATION REVIEWER | PASS WITH WARNINGS | 0 | 0 | 0 | 1 | 0 | 1 | "
                      "reviews/history/specification-review-cycle-002.md |", text)
        self.assertIn("| Status | RESOLVED |", text)  # findings are left exactly as they were
        messages = self.gr_messages()
        self.assertTrue(any("Review cycle 3 has no review date" in m for m in messages), messages)
        self.complete_review_cycle()
        gates, _ = self.gates()
        self.assertEqual(cg.WARN, gates["GR"].result, [i.message for i in gates["GR"].issues])
        self.assertEqual(3, len(self.handoff()[0]["specification-review.json"]["cycles"]))

    def test_start_cycle_refuses_an_incomplete_cycle(self):
        self.edit(REVIEW, "| Terminology | One term per concept | PASS |", "| Terminology | One term per concept | NOT REVIEWED |")
        _, _, bundle = gh.build(self.project, TIME)
        ok, messages = sr.start_cycle(self.project, bundle)
        self.assertFalse(ok)
        self.assertIn("cannot be closed", messages[0])
        self.assertFalse((self.project / SNAPSHOT_2).exists())

    def test_start_cycle_never_overwrites_a_closed_cycle(self):
        (self.project / SNAPSHOT_2).write_text("frozen", encoding="utf-8")
        _, _, bundle = gh.build(self.project, TIME)
        ok, messages = sr.start_cycle(self.project, bundle)
        self.assertFalse(ok)
        self.assertEqual("frozen", (self.project / SNAPSHOT_2).read_text(encoding="utf-8"))


class Contradictions(ReviewCase):
    def contradict(self) -> None:
        self.edit("specification/functional-requirements.md", "by entering an email address.",
                  "by entering an email address. Each user belongs to exactly one organization.")
        self.edit("specification/functional-requirements.md", "can set a new password.",
                  "can set a new password. A user may belong to multiple organizations.")

    def test_contradiction_candidate_must_be_judged(self):
        self.contradict()
        self.assertGate("GR", cg.FAIL, "Possible contradiction between FR-AUTH-001 and FR-AUTH-002")

    def test_dismissed_candidate_with_a_reason_passes(self):
        self.contradict()
        self.edit(REVIEW, "| Candidate | Artifacts | Reason | Dismissed by |\n| --- | --- | --- | --- |\n",
                  "| Candidate | Artifacts | Reason | Dismissed by |\n| --- | --- | --- | --- |\n"
                  "| Organisation cardinality | FR-AUTH-001, FR-AUTH-002 | FR-AUTH-002 describes guest access across partner organisations, a distinct concept | Fixture reviewer |\n")
        self.assertNotIn("Possible contradiction", " ".join(self.gr_messages()))

    def test_candidate_recorded_as_a_finding_passes(self):
        self.contradict()
        self.add_finding("REVIEW-003", severity="MINOR", affected="FR-AUTH-001, FR-AUTH-002",
                         title="Organisation membership cardinality conflicts",
                         evidence="FR-AUTH-001 says one organization per user; FR-AUTH-002 says several.")
        self.assertNotIn("Possible contradiction", " ".join(self.gr_messages()))

    def test_patterns(self):
        def req(rid, text, module="MOD-001", scope="in_scope"):
            return {"id": rid, "status": "approved", "scope": scope, "title": "", "description": text,
                    "related_modules": [module]}
        bundle = SimpleNamespace(requirements=[
            req("FR-001", "Users may delete records permanently."),
            req("DR-001", "Records must be retained for seven years.", module="MOD-005"),
            req("FR-002", "Anonymous users can place orders.", module="MOD-002"),
            req("FR-003", "Checkout requires authenticated users.", module="MOD-002"),
            req("FR-004", "Guests can read the help pages.", module="MOD-009"),
            req("FR-005", "A user belongs to exactly one organisation.", module="MOD-003"),
            req("FR-006", "Users can join multiple organizations.", module="MOD-004"),
            req("FR-007", "Users can join multiple organizations.", module="MOD-004", scope="future"),
        ])
        found = {(c.kind, c.ids) for c in sr.contradiction_candidates(bundle)}
        self.assertEqual({("DELETION_RETENTION", ("DR-001", "FR-001")), ("ACCESS", ("FR-002", "FR-003")),
                          ("CARDINALITY", ("FR-005", "FR-006"))}, found)


class HandoffAndState(ReviewCase):
    def test_missing_review_blocks_readiness(self):
        (self.project / REVIEW).unlink()
        self.assertGate("GR", cg.FAIL, "has not been written: the specification has not been independently reviewed")
        docs, findings = self.handoff()
        self.assertEqual("NOT_REVIEWED", docs["specification-review.json"]["overall_result"])
        self.assertIn("Specification has not been independently reviewed (reviews/specification-review.md).",
                      docs["tasks/TASK-001.json"]["readiness_gaps"])
        self.assertEqual("invalid", docs["project.json"]["handoff_status"])

    def test_validator_recomputes_the_review_result(self):
        docs, src, _ = gh.build(self.project, TIME)
        docs["specification-review.json"]["overall_result"] = "PASS"
        docs["specification-review.json"]["findings"][1]["severity"] = "CRITICAL"
        docs["specification-review.json"]["findings"][1]["status"] = "ACCEPTED_RISK"
        findings, _ = vh.validate_files(gh.serialize(docs))
        codes = {f.code for f in findings.errors}
        self.assertTrue({"SPEC_REVIEW_RESULT_MISMATCH", "SPEC_REVIEW_CRITICAL_ACCEPTED", "SPEC_REVIEW_UNRESOLVED_CLOSURE",
                         "SPEC_REVIEW_COUNT_MISMATCH", "SPEC_REVIEW_MISMATCH"} <= codes, codes)

    def test_project_state_cannot_overstate_the_review(self):
        self.edit("project-state.md", "| Open observations | 1 |", "| Open observations | 0 |")
        _, violations = self.gates()
        self.assertTrue(any("states Open observations: 0; the specification review shows 1" in v.message for v in violations),
                        [v.message for v in violations])

    def test_approval_must_follow_a_passing_review(self):
        self.edit("project-state.md", '"I approve specification version 1.0." | 2026-09-20 |',
                  '"I approve specification version 1.0." | 2026-09-18 |')
        self.assertGate("G8", cg.FAIL, "no passing independent review of that version precedes it")

    def test_command_line_status_json_and_aid(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(0, sr.main([str(self.project)]))
        self.assertIn("Result: PASS WITH WARNINGS", out.getvalue())
        aid = (self.project / sr.AID_FILE).read_text(encoding="utf-8")
        self.assertIn("## Independent traceability", aid)
        self.assertIn("## Missing scenarios", aid)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(0, sr.main([str(self.project), "--json"]))
        self.assertEqual(2, json.loads(out.getvalue())["review_cycle"])


if __name__ == "__main__":
    unittest.main()
