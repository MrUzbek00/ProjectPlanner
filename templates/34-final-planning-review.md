# Final Planning Review

TEMPLATE — stage 12, after traceability validation and before the final package is produced. Copy to `reviews/final-planning-review.md`.

This is the project-level review of the whole plan. Run `python tools/check_gates.py projects/<project>` and `python tools/generate_handoff.py projects/<project> --check` first and attach their results; the checklist below records what a person confirmed on top of them. Gate G12 fails while any row is blank, NOT REVIEWED or FAIL, while any CRITICAL or MAJOR finding is open, or when *Reviewed version* differs from the current specification version.

| Field | Value |
| --- | --- |
| Reviewed version | Specification version |
| Reviewer | Name |
| Date | YYYY-MM-DD |
| Gate report | reports/gate-report.md — date |
| Handoff check | Summary as printed by generate_handoff.py --check |

## Checklist

| Check | Result | Evidence / IDs |
| --- | --- | --- |
| No unresolved BLOCKER question affects in-scope work | NOT REVIEWED | |
| Approved scope is clear; the scope register, requirements and features agree | NOT REVIEWED | |
| Requirements are internally consistent | NOT REVIEWED | |
| All major workflows are defined, including alternatives and exceptions | NOT REVIEWED | |
| All requirements are traceable: goal → business requirement → requirement → module → feature → task → acceptance criteria | NOT REVIEWED | |
| All backlog items are traceable; no orphan requirement, feature or task | NOT REVIEWED | |
| Every in-scope task meets the Definition of Ready, or its gaps are recorded | NOT REVIEWED | |
| The dependency graph is valid: no cycles, hidden prerequisites or impossible sequencing | NOT REVIEWED | |
| Priorities use the one project scheme and are not all the top value | NOT REVIEWED | |
| Major risks are documented with probability, impact, mitigation and owner | NOT REVIEWED | |
| The roadmap reflects dependencies; every date is a labelled target, estimate or commitment | NOT REVIEWED | |
| Assumptions are visible and none supports a confirmed requirement | NOT REVIEWED | |
| Open questions and pending decisions are visible with owners | NOT REVIEWED | |
| Decisions are recorded with rationale and approval | NOT REVIEWED | |
| Binding architecture choices are accepted ADRs | NOT REVIEWED | |
| Accepted architecture decisions are respected downstream; no feature or task relies on an inactive ADR; every ARCHITECTURE CONFLICT is resolved | NOT REVIEWED | |
| The architecture review is current (`reviews/architecture-review.md`) | NOT REVIEWED | |
| Every change since the baseline is recorded, decided and implemented in the plan; gate GC passes; nothing affected remains under review | NOT REVIEWED | |
| Stakeholder deliverables are consistent with the records (N/A until stage 13 produces them) | NOT REVIEWED | |

## Findings

| Finding ID | Severity | Finding | Affected IDs | Return to stage | Status | Resolution |
| --- | --- | --- | --- | --- | --- | --- |

Severity is CRITICAL, MAJOR, MINOR or OBSERVATION. A finding is fixed in the stage it names under *Return to stage*; after the fix, re-run the gates from that stage forward.

## Conclusion

- Gates G1–G11 as last evaluated: TBD
- Remaining warnings and their disposition: TBD
- Ready to produce the final planning package? Yes only when G12 passes.
