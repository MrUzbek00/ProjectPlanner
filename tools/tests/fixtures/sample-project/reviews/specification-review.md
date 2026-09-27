# Specification Review

TEST FIXTURE. Cycle 2 of the independent specification review; cycle 1 is frozen in `reviews/history/`.

## Review record

| Field | Value |
| --- | --- |
| Reviewed version | 1.0 |
| Review cycle | 2 |
| Review date | 2026-09-19 |
| Reviewer | Fixture reviewer — SPECIFICATION REVIEWER |
| Specification author | Fixture analyst — SPECIFICATION AUTHOR |
| Independence | Separate review pass from the records only (prompts/specification-reviewer.md); the author's reasoning was not used |
| Reviewed files | specification/, discovery/, architecture/, reviews/requirement-quality-review.md, reviews/architecture-review.md |
| Overall result | PASS WITH WARNINGS |
| Open critical | 0 |
| Open major | 0 |
| Open minor | 0 |
| Open observations | 1 |
| Open findings | 1 |
| Accepted risks | 0 |
| Resolved since previous review | 1 |
| Findings raised | 2 |

## Checklist

| Area | Check | Result | Evidence / IDs |
| --- | --- | --- | --- |
| Requirements quality | Every in-scope requirement states one need, unambiguously, without vague wording | PASS | FR-AUTH-001, FR-AUTH-002, SR-001, RULE-001 |
| Requirements quality | Every requirement has rationale, source, evidence, stakeholder, priority and acceptance condition; status and confidence match evidence | PASS | FR-AUTH-003 now states TBD (Q-002); REVIEW-001 verified |
| Requirements quality | No duplicated requirement | PASS | Titles and descriptions compared across specification/ |
| Requirements quality | Priorities use one scheme and agree with dependencies | PASS | Levels; FR-AUTH-002 depends on FR-AUTH-001, both High |
| Scope consistency | Every in-scope capability is supported by an approved requirement | PASS | SCOPE-001 to SCOPE-004 against the registers |
| Scope consistency | No OUT OF SCOPE or FUTURE item appears as current work | PASS | specification/scope.md; technical specification section 3 |
| Scope consistency | No PENDING DECISION item is presented as approved | PASS | FR-AUTH-003 is Confirmed and PENDING DECISION (Q-002) |
| Workflow completeness | Every major workflow names actors, trigger, preconditions, paths, failure handling and result | PASS | PROC-001, PROC-002 |
| Workflow completeness | Every entity lifecycle is complete | PASS | ENT-002 ISSUED, USED, EXPIRED; RULE-001 |
| Workflow completeness | No two workflows contradict each other | PASS | PROC-002 replaces PROC-001 |
| Missing scenarios | Every major workflow covers the scenarios that make sense for it | PASS | PROC-002: unknown address, expired or used link; notification outage is RISK-001 |
| Permissions and authorisation | Every action states who may and may not perform it | PASS | FR-AUTH-001, FR-AUTH-002 permissions fields |
| Permissions and authorisation | Administrative actions are controlled | N/A | No administrative action is in scope (SCOPE-001 to SCOPE-004) |
| Permissions and authorisation | Tenant or organisation boundaries are explicit | N/A | Single organisation; no tenancy in the sources (SRC-001) |
| Security | Authentication, session behaviour and account recovery are specified or raised as questions | PASS | FR-AUTH-001, FR-AUTH-002; lockout is Q-002 |
| Security | Sensitive data, secrets, uploads and integrations have handling rules or questions | PASS | SR-001, ADR-002; DEP-001 |
| Security | Auditability, abuse cases and rate limiting addressed where relevant; nothing invented | PASS | AC-002 silent rejection; rate limiting awaits Q-002 |
| Data model | Every referenced entity is defined; no duplicate concept | PASS | ENT-001, ENT-002 |
| Data model | Ownership, relationships and cardinality are consistent | PASS | specification/domain-model.md |
| Data model | Lifecycle, retention and deletion behaviour defined where relevant | PASS | ENT-002 expires after 30 minutes (RULE-001) |
| Integrations | Every integration states purpose, owner, inputs, outputs, authentication and data ownership | PASS | DEP-001, ADR-001 |
| Integrations | Every integration states failure, timeout and retry, fallback and dependency risk | PASS | RISK-001 mitigation; ADR-001 constraints |
| Architecture consistency | No requirement or feature conflicts with an accepted ADR | PASS | ADR-001, ADR-002 against FR-AUTH-001 and SR-001 |
| Architecture consistency | Nothing relies on an undecided or inactive decision | PASS | reports/architecture-report.md: no proposed ADR |
| Architecture consistency | No major architecture decision is made in prose without an ADR | PASS | technical specification sections 13 and 20 |
| Independent traceability | The chain was re-derived from the records | PASS | GOAL-001 → BR-001 → FR-AUTH-001, FR-AUTH-002, SR-001 → MOD-001, MOD-002 |
| Independent traceability | Every active requirement maps somewhere; no broken or stale reference | PASS | reports/specification-review-aid.md lists none |
| Contradictions | Contradiction patterns searched; every candidate judged | PASS | The review aid lists no candidate |
| Acceptance criteria | Criteria are observable, testable, complete and non-contradictory | PASS | AC-001 to AC-006; AC-005 waits on Q-002 |
| Terminology | One term per concept | PASS | "reset link" and "reset token" are distinguished in ENT-002 |
| Assumptions | No assumption is treated as confirmed | PASS | ASM-001 applies only to FR-AUTH-003, PENDING DECISION |
| Risks | Major decisions, dependencies and integrations have risks | PASS | RISK-001 (DEP-001), RISK-002 (Q-002) |
| Change consistency | Approved changes since the last review propagated | N/A | No change is recorded; the specification is not yet baselined |
| Roadmap consistency | Sequencing, milestones and scope agree | N/A | The backlog and roadmap do not exist yet (stage 8A); repeated after changes |
| Review quality | Findings are specific, evidenced and not duplicated | PASS | REVIEW-001, REVIEW-002 |

## Review questions

| Review question | Answer | Evidence / findings |
| --- | --- | --- |
| Is the specification internally consistent? | YES | Checklist areas above |
| Are requirements complete enough? | YES | FR-AUTH-003 is held as PENDING DECISION (Q-002) |
| Are requirements testable? | YES | AC-001 to AC-006 |
| Are assumptions visible? | YES | ASM-001 |
| Are workflows coherent? | YES | PROC-001, PROC-002 |
| Are permissions defined? | YES | FR-AUTH-001, FR-AUTH-002 |
| Are major security concerns covered? | YES | SR-001, ADR-002, Q-002 |
| Does the architecture match the specification? | YES | ADR-001, ADR-002 |
| Is traceability valid? | YES | Re-derived chain above |
| Did recent changes propagate correctly? | N/A | No change is recorded |
| Are there unresolved contradictions? | NO | No candidate; REVIEW-001 resolved |
| Is the specification safe to use as the basis for backlog planning? | YES | PASS WITH WARNINGS: REVIEW-002 is an observation |

## Findings

### REVIEW-001 — Lockout threshold was specified without a source

| Field | Value |
| --- | --- |
| Severity | MAJOR |
| Category | REQUIREMENT |
| Status | RESOLVED |
| Raised in cycle | 1 |
| Affected artifacts | FR-AUTH-003, AC-005 |
| Return to stage | 3 — Requirement Analysis |
| Closed in cycle | 2 |
| Resolution | The invented threshold was removed. FR-AUTH-003 and AC-005 state TBD (Q-002), and FR-AUTH-003 is PENDING DECISION through SCOPE-002 |
| Resolved by | Fixture analyst |
| Resolution date | 2026-09-19 |
| Changed artifacts | FR-AUTH-003, SCOPE-002 |
| Verification | Re-reviewed in cycle 2: FR-AUTH-003 and AC-005 contain no number; SCOPE-002 is PENDING DECISION and names Q-002 |
| Approved by | |
| Approval evidence | |

**Evidence**

FR-AUTH-003 in version 0.9 locked an account after five failed sign-ins. SRC-001 and the decision log contain no threshold, and Q-002 asks for it.

**Why it matters**

A guessed security threshold would be built and tested as if the owner had decided it.

**Required action**

Remove the number, keep the requirement pending until Q-002 is answered, and hold it out of the release.

### REVIEW-002 — Reset email language is undecided

| Field | Value |
| --- | --- |
| Severity | OBSERVATION |
| Category | REQUIREMENT |
| Status | OPEN |
| Raised in cycle | 1 |
| Affected artifacts | Q-003, FR-AUTH-001 |
| Return to stage | 2 — Discovery |
| Closed in cycle | |
| Resolution | |
| Resolved by | |
| Resolution date | |
| Changed artifacts | |
| Verification | |
| Approved by | |
| Approval evidence | |

**Evidence**

Q-003 (reset email language) is open, and FR-AUTH-001 does not state the language of the reset email.

**Why it matters**

Not a defect for the release: the template text can change later without changing behaviour.

**Required action**

Record the answer to Q-003 when it arrives.

## Dismissed candidates

| Candidate | Artifacts | Reason | Dismissed by |
| --- | --- | --- | --- |

## Cycle history

| Cycle | Review date | Reviewed version | Reviewer | Overall result | Open critical | Open major | Open minor | Open observations | Accepted risks | Resolved since previous review | Snapshot |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 2026-09-18 | 0.9 | Fixture reviewer — SPECIFICATION REVIEWER | FAIL | 0 | 1 | 0 | 1 | 0 | 0 | reviews/history/specification-review-cycle-001.md |
