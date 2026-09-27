# Requirement Quality Review

TEMPLATE — stage 3, after the requirements are written and before gate G3. Copy to `reviews/requirement-quality-review.md`.

Run `python tools/check_gates.py projects/<project> --gate G3` first. Its G3 section lists the heuristic findings — unmeasured wording, implementation detail, requirements that may combine several needs, functional requirements without an actor, trigger, permission rule or failure case, missing rationale, evidence or stakeholder, duplicate titles, and requirements that do not trace to a business requirement. The heuristics find candidates; this review decides. Checks that need judgement — contradictions, undefined terms, whether a criterion really proves the requirement — are recorded here.

| Field | Value |
| --- | --- |
| Reviewed version | Specification or register version reviewed |
| Reviewer | Name |
| Date | YYYY-MM-DD |
| Gate report reviewed | reports/gate-report.md, G3 section |

## Checklist

Record every row as PASS, FAIL, N/A with a reason, or NOT REVIEWED. A blank or NOT REVIEWED row fails gate G3; so does FAIL.

| Check | Result | Evidence / IDs |
| --- | --- | --- |
| Every requirement states one need; none combines unrelated requirements | NOT REVIEWED | |
| No ambiguous or unmeasured wording remains (fast, easy, modern, user-friendly, secure, flexible, efficient … without a measurable criterion) | NOT REVIEWED | |
| No duplicate requirements; consolidated duplicates keep all sources | NOT REVIEWED | |
| No contradictions between requirements, rules and decisions | NOT REVIEWED | |
| Every functional requirement has an actor, trigger and observable outcome | NOT REVIEWED | |
| Terminology is defined in the glossary and used consistently | NOT REVIEWED | |
| Every requirement is testable through its acceptance condition | NOT REVIEWED | |
| No implementation-specific assumptions in business, functional or UX requirements | NOT REVIEWED | |
| Error and failure cases are covered | NOT REVIEWED | |
| Permission rules are stated for every action | NOT REVIEWED | |
| Every requirement traces to a business requirement (and every BR to a business goal) | NOT REVIEWED | |
| Every confirmed requirement rests on CONFIRMED information, not an assumption | NOT REVIEWED | |

## Findings

Severity: CRITICAL (planning built on it would be wrong), MAJOR (materially ambiguous or inconsistent), MINOR (low-impact, recorded disposition), OBSERVATION (no action required). An open CRITICAL or MAJOR finding fails gate G3. *Return to stage* names where the fix belongs — usually 2 (a missing answer) or 3 (a badly written requirement).

| Finding ID | Severity | Finding | Affected IDs | Return to stage | Status | Resolution |
| --- | --- | --- | --- | --- | --- | --- |

Status is OPEN, RESOLVED, ACCEPTED (MINOR or OBSERVATION only, with the reason in Resolution) or WITHDRAWN. Finding IDs (FIND-###) are unique across all reviews in the project.
