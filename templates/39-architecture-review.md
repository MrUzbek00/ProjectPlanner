# Architecture Review

TEMPLATE — stage 6, after every architecture concern is classified and before the specification is written. Copy to `reviews/architecture-review.md`. Repeat it whenever an ADR changes status, and whenever a later stage reports an ARCHITECTURE CONFLICT.

Run `python tools/check_gates.py projects/<project>` first. It writes `reports/architecture-report.md`: the counts, every decision with what it reaches, the concern coverage, every conflict it detected and every unresolved critical decision. Copy the counts into the table below — gate G6 compares them with the records and fails on any difference, so a stale review cannot pass. What the tool cannot decide — whether two accepted decisions contradict in substance, whether a feature quietly works around a constraint — is judged here.

| Field | Value |
| --- | --- |
| Reviewer | TBD |
| Date | TBD |
| Active ADRs | Number of Accepted ADRs |
| Proposed ADRs | TBD |
| Superseded ADRs | TBD |
| Rejected ADRs | TBD |
| Deprecated ADRs | TBD |
| Conflicts | Conflicts detected by the gate checker (`reports/architecture-report.md`); each one has a finding below |
| Unresolved critical decisions | Proposed ADRs and DECISION REQUIRED concerns whose question is an open BLOCKER |
| Warnings | G6 warnings at the time of review |
| Overall | PASS / PASS WITH WARNINGS / FAIL |

## Reviewed decisions

One row per ADR, in its current status. Gate G6 fails when an ADR is missing here or when *Status reviewed* differs from the ADR file — a status change needs a fresh review.

| ADR ID | Status reviewed | Consistent with other active ADRs | Notes |
| --- | --- | --- | --- |

## Checklist

Record every row as PASS, FAIL, N/A with a reason, or NOT REVIEWED. A blank checklist is not a pass.

| Check | Result | Evidence / IDs |
| --- | --- | --- |
| Every major architecture concern is classified | NOT REVIEWED | |
| No critical architecture decision is unresolved or hidden | NOT REVIEWED | |
| Accepted ADRs are internally consistent | NOT REVIEWED | |
| No active ADR contradicts another active ADR | NOT REVIEWED | |
| Requirements reference the ADRs that materially affect them | NOT REVIEWED | |
| Major features respect accepted architecture constraints (N/A until stage 9 creates them) | NOT REVIEWED | |
| Superseded ADRs are correctly linked | NOT REVIEWED | |
| No rejected, superseded or deprecated ADR is treated as active | NOT REVIEWED | |
| Constraints are stated in reviewable language | NOT REVIEWED | |
| ADRs stay at architecture level, not implementation detail | NOT REVIEWED | |
| Every accepted ADR has a named approver and approval evidence | NOT REVIEWED | |

## Findings

*Type* is ARCHITECTURE CONFLICT, MISSING DECISION, INCONSISTENCY, LINK ERROR or OTHER. Severity is CRITICAL, MAJOR, MINOR or OBSERVATION; a CRITICAL or MAJOR finding is resolved or withdrawn, never accepted.

For an **ARCHITECTURE CONFLICT** — a requirement, feature or task that contradicts an accepted ADR, or two decisions that cannot both hold:

1. Identify the conflict and name the conflicting item in *Affected IDs* and the ADR in *ADR*.
2. Explain in *Finding* why it conflicts.
3. Keep it CRITICAL or MAJOR while it is open, and resolve it by exactly one of:
   - `CHANGE PROPOSAL` — the proposed item is changed to respect the ADR;
   - `NEW ADR — ADR-###` — a new decision covers the case without replacing the old one;
   - `SUPERSEDE ADR — ADR-###` — a new decision replaces the old one, which is then Superseded.

Gate G6 accepts a resolution by NEW ADR or SUPERSEDE ADR only once the new ADR is Accepted by its decision owner, and SUPERSEDE ADR only once the old ADR is marked Superseded by it. A possible conflict that is not one (for example, a rejected option mentioned in order to exclude it) is `WITHDRAWN` with the reason in *Resolution*. Every ARCHITECTURE CONFLICT the gate checker reports must appear here; an unrecorded one fails the gate of the item that raised it.

| Finding ID | Severity | Type | Finding | Affected IDs | ADR | Resolution | Return to stage | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Status is OPEN, IN PROGRESS, RESOLVED or WITHDRAWN.
