"""Tests for architecture governance: gate G6, ADR lifecycle rules, conflicts and drift.

Run from the repository root:
    python -m unittest discover -s tools/tests -v

Each test starts from the fixture project (two accepted ADRs, every architecture
concern classified, a complete architecture review), changes one thing, and
asserts which gate reports it and why.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
import sys
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_gates as cg  # noqa: E402
import generate_handoff as gh  # noqa: E402
import impact_analysis as ia  # noqa: E402
from test_gates import GateCase  # noqa: E402

REGISTER = "architecture/architecture-register.md"
REVIEW = "reviews/architecture-review.md"
ADR_001 = "architecture/ADR-001-reset-email-delivery.md"
ADR_002 = "architecture/ADR-002-reset-token-storage.md"


class ArchitectureCase(GateCase):
    def add_adr(self, number: int, title: str, status: str, *, owner: str = "Fixture owner", evidence: str = "DEC-002",
                question: str = "None", requirements: str = "None", features: str = "None", modules: str = "None",
                supersedes: str = "None", superseded_by: str = "None", conflicts: str = "None",
                constraint: str = "Account emails are sent through one delivery path.",
                alternatives: str = "| Chosen option | Summary | Pro | Con | Chosen |") -> str:
        """Write an ADR file and register it and its review row, so that only the tested rule fails."""
        aid = f"ADR-{number:03d}"
        date = "2026-09-15" if status != "Proposed" else "TBD"
        text = f"""# {aid} — {title}

| Field | Value |
| --- | --- |
| Status | {status} |
| Date | {date} |
| Decision owner / Approver | {owner} |
| Approval evidence | {evidence} |
| Decision question | {question} |
| Related requirements | {requirements} |
| Related features | {features} |
| Affected modules | {modules} |
| Related decisions | None |
| Principles | None |
| Depends on | None |
| Conflicts with | {conflicts} |
| Supersedes | {supersedes} |
| Superseded by | {superseded_by} |

## Context

A test decision.

## Decision

{title}.

## Rationale

It is a test.

## Alternatives considered

| Option | Description | Advantages | Disadvantages | Outcome |
| --- | --- | --- | --- | --- |
{alternatives}

## Consequences

### Positive

- Test.

## Constraints introduced

- {constraint}
"""
        (self.project / "architecture" / f"{aid}-test.md").write_text(text, encoding="utf-8")
        self.edit(REGISTER, "| ADR-002 | Store only a hash of each reset token | Accepted | 2026-09-14 | Fixture owner | SR-001 | None |\n",
                  "| ADR-002 | Store only a hash of each reset token | Accepted | 2026-09-14 | Fixture owner | SR-001 | None |\n"
                  f"| {aid} | {title} | {status} | {date} | {owner} | {requirements} | {superseded_by} |\n")
        self.edit(REVIEW, "| ADR-002 | Accepted | Yes | |\n", f"| ADR-002 | Accepted | Yes | |\n| {aid} | {status} | Yes | |\n")
        return aid

    def set_review(self, label: str, value: str) -> None:
        path = self.project / REVIEW
        text = path.read_text(encoding="utf-8")
        text, count = re.subn(rf"^\| {re.escape(label)} \| [^|]* \|$", f"| {label} | {value} |", text, flags=re.MULTILINE)
        self.assertEqual(1, count, label)
        path.write_text(text, encoding="utf-8")

    def set_adr_status(self, rel: str, aid: str, old: str, new: str, register_title: str) -> None:
        self.edit(rel, f"| Status | {old} |", f"| Status | {new} |")
        self.edit(REGISTER, f"| {aid} | {register_title} | {old} |", f"| {aid} | {register_title} | {new} |")
        self.edit(REVIEW, f"| {aid} | {old} |", f"| {aid} | {new} |")


class Fixture(ArchitectureCase):
    def test_fixture_architecture_is_ready(self):
        self.assertGate("G6", cg.PASS)

    def test_architecture_report_is_written(self):
        with contextlib.redirect_stdout(io.StringIO()):
            cg.main([str(self.project)])
        report = (self.project / "reports" / "architecture-report.md").read_text(encoding="utf-8")
        self.assertIn("| Active ADRs | 2 |", report)
        self.assertIn("| Overall (G6, automated) | PASS |", report)


class Coverage(ArchitectureCase):
    def test_missing_concern_fails(self):
        self.edit(REGISTER, "| Caching | NOT APPLICABLE | | | No caching need is stated (SRC-001) |\n", "")
        self.assertGate("G6", cg.FAIL, "Architecture concern 'Caching' is missing")

    def test_unassessed_concern_fails(self):
        self.edit(REGISTER, "| Caching | NOT APPLICABLE |", "| Caching | NOT ASSESSED |")
        self.assertGate("G6", cg.FAIL, "'Caching' has not been assessed")

    def test_not_applicable_needs_evidence(self):
        self.edit(REGISTER, "No caching need is stated (SRC-001)", "No caching need is stated")
        self.assertGate("G6", cg.FAIL, "'Caching' is NOT APPLICABLE without evidence")

    def test_decision_required_needs_a_question(self):
        self.edit(REGISTER, "| Caching | NOT APPLICABLE | | | No caching need is stated (SRC-001) |",
                  "| Caching | DECISION REQUIRED | | | Load is unknown |")
        self.assertGate("G6", cg.FAIL, "ARCHITECTURE DECISION REQUIRED: 'Caching' names no open question")

    def test_non_blocking_decision_required_is_visible(self):
        self.append("discovery/open-questions.md",
                    "| Q-010 | Technical constraints | Is a cache needed for the sign-in page? | Sets the caching approach | HIGH | | Fixture owner | 3 | OPEN | | |")
        self.edit(REGISTER, "| Caching | NOT APPLICABLE | | | No caching need is stated (SRC-001) |",
                  "| Caching | DECISION REQUIRED | | Q-010 | Load is unknown |")
        self.assertGate("G6", cg.WARN, "ARCHITECTURE DECISION REQUIRED: 'Caching' is undecided (Q-010 HIGH)")

    def test_blocking_decision_required_fails(self):
        self.append("discovery/open-questions.md",
                    "| Q-010 | Technical constraints | Where are reset tokens hosted? | Sets data storage | BLOCKER | SR-001 | Fixture owner | 3 | OPEN | | |")
        self.edit(REGISTER, "| Data storage | NOT APPLICABLE | | | Reset tokens use the portal's existing store (SRC-001) |",
                  "| Data storage | DECISION REQUIRED | | Q-010 | Hosting is undecided |")
        self.set_review("Unresolved critical decisions", "1")
        self.assertGate("G6", cg.FAIL, "is a BLOCKER that affects in-scope work")

    def test_decided_concern_cannot_rest_on_a_superseded_adr(self):
        self.add_adr(3, "Send account emails through the messaging gateway", "Accepted", evidence="DEC-002",
                     supersedes="ADR-001", requirements="FR-AUTH-001", modules="MOD-002")
        self.edit(ADR_001, "| Status | Accepted |", "| Status | Superseded |")
        self.edit(ADR_001, "| Superseded by | None |", "| Superseded by | ADR-003 |")
        self.edit(REGISTER, "| ADR-001 | Send reset emails through the existing notification service | Accepted | 2026-09-12 | Fixture owner | FR-AUTH-001 | None |",
                  "| ADR-001 | Send reset emails through the existing notification service | Superseded | 2026-09-12 | Fixture owner | FR-AUTH-001 | ADR-003 |")
        self.edit(REVIEW, "| ADR-001 | Accepted |", "| ADR-001 | Superseded |")
        self.set_review("Active ADRs", "2")
        self.set_review("Superseded ADRs", "1")
        gates, _ = self.gates()
        messages = [i.message for i in gates["G6"].issues]
        self.assertTrue(any("'Integration strategy' lists ADR-001, which is SUPERSEDED" in m for m in messages), messages)
        # Once the register and the feature name the governing decision, supersession is clean.
        self.edit("backlog/backlog.md", "| Architecture decisions | ADR-001, ADR-002 |", "| Architecture decisions | ADR-003, ADR-002 |")
        path = self.project / REGISTER
        path.write_text(path.read_text(encoding="utf-8").replace("| DECIDED | ADR-001 |", "| DECIDED | ADR-003 |"), encoding="utf-8")
        self.assertGate("G6", cg.PASS)


class Lifecycle(ArchitectureCase):
    def test_proposed_adr_needs_a_deciding_question(self):
        self.add_adr(3, "Cache sign-in pages", "Proposed", owner="TBD (Q-003)", evidence="None")
        self.set_review("Proposed ADRs", "1")
        self.assertGate("G6", cg.FAIL, "ADR-003 is proposed but names no open question")

    def test_proposed_adr_is_a_visible_warning(self):
        self.add_adr(3, "Cache sign-in pages", "Proposed", owner="TBD (Q-003)", evidence="None", question="Q-003")
        self.set_review("Proposed ADRs", "1")
        self.assertGate("G6", cg.WARN, "ADR-003 (Cache sign-in pages) is PROPOSED")

    def test_accepted_adr_needs_approval_evidence(self):
        self.edit(ADR_002, "| Approval evidence | DEC-003 |", "| Approval evidence | None |")
        self.assertGate("G6", cg.FAIL, "ADR-002 is accepted but cites no approval evidence")

    def test_accepted_adr_needs_a_named_approver(self):
        self.edit(ADR_002, "| Decision owner / Approver | Fixture owner |", "| Decision owner / Approver | TBD (Q-004) |")
        self.assertGate("G6", cg.FAIL, "ADR-002 is accepted but names no decision owner")

    def test_rejected_adr_also_needs_its_human_decision(self):
        self.add_adr(3, "Cache sign-in pages", "Rejected", owner="None", evidence="None")
        self.set_review("Rejected ADRs", "1")
        self.assertGate("G6", cg.FAIL, "ADR-003 is rejected but names no decision owner")

    def test_vague_constraint_warns(self):
        self.edit(ADR_002, "- No reset token is stored in a recoverable form, encrypted or plain.",
                  "- Keep the token store clean and scalable.")
        self.assertGate("G6", cg.WARN, "uses unreviewable wording (clean, scalable)")

    def test_implementation_detail_warns(self):
        self.edit(ADR_002, "- A reset link cannot be re-sent; a new request issues a new token.",
                  "- Tokens are hashed by hash_token() in src/auth/tokens.py.")
        self.assertGate("G6", cg.WARN, "an implementation detail")

    def test_accepted_adr_needs_consequences(self):
        self.edit(ADR_002, "### Positive\n\n- A leaked token store yields no usable token.\n", "")
        self.edit(ADR_002, "### Negative\n\n- A lost email means requesting a new link; the old one cannot be re-sent.\n", "")
        self.assertGate("G6", cg.FAIL, "ADR-002 is accepted but has no consequences")

    def test_accepted_principle_needs_evidence(self):
        self.edit("architecture/principles.md", "| DEC-002 | Accepted |", "| | Accepted |")
        self.assertGate("G6", cg.FAIL, "PRIN-001 is ACCEPTED without evidence")


class Register(ArchitectureCase):
    def test_adr_missing_from_register_fails(self):
        self.edit(REGISTER, "| ADR-002 | Store only a hash of each reset token | Accepted | 2026-09-14 | Fixture owner | SR-001 | None |\n", "")
        self.assertGate("G6", cg.FAIL, "ADR-002 is not in the ADR register")

    def test_deleted_adr_record_fails(self):
        self.edit(REGISTER, "| ADR-002 | Store only a hash of each reset token | Accepted | 2026-09-14 | Fixture owner | SR-001 | None |\n",
                  "| ADR-002 | Store only a hash of each reset token | Accepted | 2026-09-14 | Fixture owner | SR-001 | None |\n"
                  "| ADR-003 | Cache sign-in pages | Rejected | 2026-09-15 | Fixture owner | None | None |\n")
        self.assertGate("G6", cg.FAIL, "ADR-003 is registered but has no record in architecture/. ADR records are never deleted")

    def test_register_must_agree_with_the_record(self):
        self.edit(REGISTER, "| ADR-002 | Store only a hash of each reset token | Accepted |", "| ADR-002 | Store only a hash of each reset token | Proposed |")
        self.assertGate("G6", cg.FAIL, "ADR-002 status is 'proposed' in the ADR register but 'accepted' in its record")


class Consistency(ArchitectureCase):
    def test_superseding_without_retiring_the_old_decision_is_a_conflict(self):
        self.add_adr(3, "Send account emails through the messaging gateway", "Accepted", supersedes="ADR-001")
        self.set_review("Active ADRs", "3")
        self.assertGate("G6", cg.FAIL, "ADR-003 supersedes ADR-001, but ADR-001 is still ACCEPTED")

    def test_a_proposed_adr_replaces_nothing(self):
        self.add_adr(3, "Send account emails through the messaging gateway", "Proposed", owner="TBD (Q-003)",
                     evidence="None", question="Q-003", supersedes="ADR-001")
        self.set_adr_status(ADR_001, "ADR-001", "Accepted", "Superseded", "Send reset emails through the existing notification service")
        self.edit(ADR_001, "| Superseded by | None |", "| Superseded by | ADR-003 |")
        self.assertGate("G6", cg.FAIL, "a decision is replaced only when its successor is ACCEPTED")

    def test_supersession_links_must_agree(self):
        self.add_adr(3, "Send account emails through the messaging gateway", "Accepted", supersedes="None")
        self.set_adr_status(ADR_001, "ADR-001", "Accepted", "Superseded", "Send reset emails through the existing notification service")
        self.edit(ADR_001, "| Superseded by | None |", "| Superseded by | ADR-003 |")
        self.assertGate("G6", cg.FAIL, "ADR-003 does not list ADR-001 under 'Supersedes'")

    def test_conflicting_active_adrs_fail(self):
        self.edit(ADR_002, "| Conflicts with | None |", "| Conflicts with | ADR-001 |")
        self.assertGate("G6", cg.FAIL, "ADR-001 and ADR-002 are both ACCEPTED but are recorded as conflicting")

    def test_review_must_cover_current_statuses(self):
        self.edit(REVIEW, "| ADR-002 | Accepted |", "| ADR-002 | Proposed |")
        self.assertGate("G6", cg.FAIL, "reviewed ADR-002 as PROPOSED; it is now ACCEPTED")

    def test_review_summary_must_match_the_records(self):
        self.set_review("Active ADRs", "3")
        self.assertGate("G6", cg.FAIL, "states Active ADRs: 3; the records show 2")


class Drift(ArchitectureCase):
    def reject_adr(self) -> str:
        return self.add_adr(3, "Send account emails by SMS", "Rejected")

    def test_feature_relying_on_a_rejected_adr_fails_the_backlog_gate(self):
        self.set_review("Rejected ADRs", "1")
        self.reject_adr()
        self.edit("backlog/backlog.md", "| Architecture decisions | ADR-001, ADR-002 |", "| Architecture decisions | ADR-001, ADR-002, ADR-003 |")
        self.set_review("Conflicts", "1")
        self.assertGate("G9", cg.FAIL, "FEAT-001 relies on ADR-003, which is REJECTED and governs nothing")

    def test_superseded_reference_names_the_successor(self):
        self.add_adr(3, "Send account emails through the messaging gateway", "Accepted", supersedes="ADR-002")
        self.set_adr_status(ADR_002, "ADR-002", "Accepted", "Superseded", "Store only a hash of each reset token")
        self.edit(ADR_002, "| Superseded by | None |", "| Superseded by | ADR-003 |")
        gates, _ = self.gates()
        messages = [i.message for i in gates["G9"].issues]
        self.assertTrue(any("relies on ADR-002, which is SUPERSEDED" in m and "Follow ADR-003" in m for m in messages), messages)

    def test_superseded_adr_no_longer_binds_tasks(self):
        self.add_adr(3, "Store reset tokens as salted hashes", "Accepted", supersedes="ADR-002", requirements="SR-001", modules="MOD-001")
        self.set_adr_status(ADR_002, "ADR-002", "Accepted", "Superseded", "Store only a hash of each reset token")
        self.edit(ADR_002, "| Superseded by | None |", "| Superseded by | ADR-003 |")
        self.edit("backlog/backlog.md", "| Architecture decisions | ADR-001, ADR-002 |", "| Architecture decisions | ADR-001, ADR-003 |")
        docs, _, _ = gh.build(self.project, "2026-09-26T00:00:00Z")
        applied = {a["id"]: a["applies_via"] for a in docs["tasks/TASK-003.json"]["architecture_decisions"]}
        self.assertIn("ADR-003", applied)
        self.assertNotIn("ADR-002", applied)
        sr = next(r for r in docs["requirements.json"]["requirements"] if r["id"] == "SR-001")
        self.assertEqual(["ADR-003"], [a["id"] for a in sr["architecture_decisions"]])
        # TASK-001 names ADR-002 itself: the link stays visible and is an error, never silently dropped.
        self.assertEqual(["task"], {a["id"]: a["applies_via"] for a in docs["tasks/TASK-001.json"]["architecture_decisions"]}["ADR-002"])
        self.assertGate("G9", cg.FAIL, "TASK-001 relies on ADR-002, which is SUPERSEDED")

    def test_rejected_option_in_a_feature_needs_review(self):
        self.edit("backlog/backlog.md", "| Goal | Repeated failed sign-ins lock the account |",
                  "| Goal | Repeated failed sign-ins lock the account and alert the user by direct SMTP integration |")
        self.set_review("Conflicts", "1")
        self.assertGate("G9", cg.FAIL, "ARCHITECTURE CONFLICT between FEAT-002 and ADR-001 is not recorded")

    def test_withdrawn_conflict_leaves_a_visible_warning(self):
        self.edit("backlog/backlog.md", "| Goal | Repeated failed sign-ins lock the account |",
                  "| Goal | Repeated failed sign-ins lock the account and alert the user by direct SMTP integration |")
        self.set_review("Conflicts", "1")
        self.append(REVIEW, "| FIND-001 | OBSERVATION | Architecture conflict | FEAT-002 mentions a rejected option | FEAT-002 | ADR-001 "
                            "| Wording only; the alert goes through MOD-002 | 6 | WITHDRAWN |")
        self.assertGate("G9", cg.WARN, "ARCHITECTURE CONFLICT: FEAT-002 mentions 'Direct SMTP integration'")

    def test_conflict_resolved_by_an_unaccepted_adr_stays_open(self):
        self.edit("backlog/backlog.md", "| Goal | Repeated failed sign-ins lock the account |",
                  "| Goal | Repeated failed sign-ins lock the account and alert the user by direct SMTP integration |")
        self.set_review("Conflicts", "1")
        self.add_adr(3, "Allow direct SMTP for lockout alerts", "Proposed", owner="TBD (Q-003)", evidence="None", question="Q-003")
        self.set_review("Proposed ADRs", "1")
        self.append(REVIEW, "| FIND-001 | MAJOR | Architecture conflict | FEAT-002 needs a second delivery path | FEAT-002 | ADR-001 "
                            "| NEW ADR — ADR-003 | 6 | RESOLVED |")
        self.assertGate("G6", cg.FAIL, "FIND-001 is resolved by ADR-003, which is PROPOSED")

    def test_requirement_can_name_its_adr(self):
        self.edit("specification/security-requirements.md", "| Related modules | MOD-001 |",
                  "| Related modules | MOD-001 |\n| Architecture decisions | ADR-002 |")
        docs, _, _ = gh.build(self.project, "2026-09-26T00:00:00Z")
        sr = next(r for r in docs["requirements.json"]["requirements"] if r["id"] == "SR-001")
        self.assertEqual([{"id": "ADR-002", "status": "accepted", "applies_via": ["requirement", "adr"]}], sr["architecture_decisions"])


class Impact(ArchitectureCase):
    def affected(self, *ids: str) -> set[str]:
        _, _, bundle = gh.build(self.project, "2026-09-26T00:00:00Z")
        return set(ia.Graph(bundle).affected(list(ids)))

    def test_adr_change_reaches_what_it_governs(self):
        affected = self.affected("ADR-001")
        self.assertTrue({"FR-AUTH-001", "MOD-002", "FEAT-001", "TASK-001", "TASK-002", "TASK-003"} <= affected, affected)
        self.assertNotIn("SR-001", affected)

    def test_requirement_change_does_not_fan_out_through_its_adr(self):
        affected = self.affected("FR-AUTH-001")
        self.assertIn("ADR-001", affected)
        self.assertNotIn("SR-001", affected)

    def test_changing_an_accepted_adr_says_to_supersede_it(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(0, ia.main([str(self.project), "ADR-001", "--no-write"]))
        self.assertIn("supersede with a new ADR", out.getvalue())
        self.assertIn("Re-run G6 to G13", out.getvalue())


class Handoff(ArchitectureCase):
    def test_architecture_json_carries_governance_state(self):
        docs, _, _ = gh.build(self.project, "2026-09-26T00:00:00Z")
        architecture = docs["architecture.json"]
        self.assertEqual({"accepted": 2, "proposed": 0, "rejected": 0, "superseded": 0, "deprecated": 0, "decisions_required": 0},
                         architecture["summary"])
        adr = architecture["decisions"][0]
        self.assertTrue(adr["active"])
        self.assertEqual(["Reset emails are sent only through MOD-002; no module sends email directly.",
                          "A new delivery channel for account emails requires a new ADR."], adr["constraints"])
        self.assertEqual(20, len(architecture["coverage"]))
        trace = {entry["adr_id"]: entry for entry in docs["traceability.json"]["architecture"]}
        self.assertEqual(["FEAT-001"], trace["ADR-001"]["feature_ids"])
        feature = docs["backlog.json"]["features"][0]
        self.assertEqual(["feature", "requirement:FR-AUTH-001", "module:MOD-002"], feature["architecture_decisions"][0]["applies_via"])
        json.dumps(docs["architecture.json"])


if __name__ == "__main__":
    unittest.main()
