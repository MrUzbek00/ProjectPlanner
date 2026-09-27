# Specification Review

TEST FIXTURE. Cycle 1 of the independent specification review, frozen when the cycle was closed.

## Review record

| Field | Value |
| --- | --- |
| Reviewed version | 0.9 |
| Review cycle | 1 |
| Review date | 2026-09-18 |
| Reviewer | Fixture reviewer — SPECIFICATION REVIEWER |
| Specification author | Fixture analyst — SPECIFICATION AUTHOR |
| Independence | Separate review pass from the records only (prompts/specification-reviewer.md); the author's reasoning was not used |
| Reviewed files | specification/, discovery/, architecture/, reviews/requirement-quality-review.md, reviews/architecture-review.md |
| Overall result | FAIL |
| Open critical | 0 |
| Open major | 1 |
| Open minor | 0 |
| Open observations | 1 |
| Open findings | 2 |
| Accepted risks | 0 |
| Resolved since previous review | 0 |
| Findings raised | 2 |

## Checklist

| Area | Check | Result | Evidence / IDs |
| --- | --- | --- | --- |
| Requirements quality | Every in-scope requirement states one need, unambiguously, without vague wording | PASS | FR-AUTH-001, FR-AUTH-002, SR-001, RULE-001 |
| Requirements quality | Every requirement has rationale, source, evidence, stakeholder, priority and acceptance condition; status and confidence match evidence | FAIL | REVIEW-001 |
| Requirements quality | No duplicated requirement | PASS | Titles and descriptions compared across specification/ |
| Requirements quality | Priorities use one scheme and agree with dependencies | PASS | Levels |
| Scope consistency | Every in-scope capability is supported by an approved requirement | PASS | SCOPE-001 to SCOPE-004 |
| Scope consistency | No OUT OF SCOPE or FUTURE item appears as current work | PASS | specification/scope.md |
| Scope consistency | No PENDING DECISION item is presented as approved | FAIL | REVIEW-001 |
| Workflow completeness | Every major workflow names actors, trigger, preconditions, paths, failure handling and result | PASS | PROC-001, PROC-002 |
| Workflow completeness | Every entity lifecycle is complete | PASS | ENT-002 |
| Workflow completeness | No two workflows contradict each other | PASS | PROC-002 replaces PROC-001 |
| Missing scenarios | Every major workflow covers the scenarios that make sense for it | PASS | PROC-002 |
| Permissions and authorisation | Every action states who may and may not perform it | PASS | FR-AUTH-001, FR-AUTH-002 |
| Permissions and authorisation | Administrative actions are controlled | N/A | No administrative action is in scope |
| Permissions and authorisation | Tenant or organisation boundaries are explicit | N/A | Single organisation (SRC-001) |
| Security | Authentication, session behaviour and account recovery are specified or raised as questions | FAIL | REVIEW-001 |
| Security | Sensitive data, secrets, uploads and integrations have handling rules or questions | PASS | SR-001, ADR-002 |
| Security | Auditability, abuse cases and rate limiting addressed where relevant; nothing invented | PASS | AC-002 |
| Data model | Every referenced entity is defined; no duplicate concept | PASS | ENT-001, ENT-002 |
| Data model | Ownership, relationships and cardinality are consistent | PASS | specification/domain-model.md |
| Data model | Lifecycle, retention and deletion behaviour defined where relevant | PASS | RULE-001 |
| Integrations | Every integration states purpose, owner, inputs, outputs, authentication and data ownership | PASS | DEP-001, ADR-001 |
| Integrations | Every integration states failure, timeout and retry, fallback and dependency risk | PASS | RISK-001 |
| Architecture consistency | No requirement or feature conflicts with an accepted ADR | PASS | ADR-001, ADR-002 |
| Architecture consistency | Nothing relies on an undecided or inactive decision | PASS | No proposed ADR |
| Architecture consistency | No major architecture decision is made in prose without an ADR | PASS | Technical specification sections 13 and 20 |
| Independent traceability | The chain was re-derived from the records | PASS | GOAL-001 → BR-001 → FR-AUTH-001, FR-AUTH-002, SR-001 |
| Independent traceability | Every active requirement maps somewhere; no broken or stale reference | PASS | Review aid lists none |
| Contradictions | Contradiction patterns searched; every candidate judged | PASS | No candidate |
| Acceptance criteria | Criteria are observable, testable, complete and non-contradictory | PASS | AC-001 to AC-006 |
| Terminology | One term per concept | PASS | ENT-002 |
| Assumptions | No assumption is treated as confirmed | FAIL | REVIEW-001 |
| Risks | Major decisions, dependencies and integrations have risks | PASS | RISK-001 |
| Change consistency | Approved changes since the last review propagated | N/A | No change is recorded |
| Roadmap consistency | Sequencing, milestones and scope agree | N/A | The backlog and roadmap do not exist yet |
| Review quality | Findings are specific, evidenced and not duplicated | PASS | REVIEW-001, REVIEW-002 |

## Review questions

| Review question | Answer | Evidence / findings |
| --- | --- | --- |
| Is the specification internally consistent? | YES | Checklist areas above |
| Are requirements complete enough? | PARTIAL | REVIEW-001 |
| Are requirements testable? | YES | AC-001 to AC-006 |
| Are assumptions visible? | NO | REVIEW-001 |
| Are workflows coherent? | YES | PROC-001, PROC-002 |
| Are permissions defined? | YES | FR-AUTH-001, FR-AUTH-002 |
| Are major security concerns covered? | PARTIAL | REVIEW-001 |
| Does the architecture match the specification? | YES | ADR-001, ADR-002 |
| Is traceability valid? | YES | Re-derived chain above |
| Did recent changes propagate correctly? | N/A | No change is recorded |
| Are there unresolved contradictions? | NO | No candidate |
| Is the specification safe to use as the basis for backlog planning? | NO | REVIEW-001 is an open MAJOR finding |

## Findings

### REVIEW-001 — Lockout threshold was specified without a source

| Field | Value |
| --- | --- |
| Severity | MAJOR |
| Category | REQUIREMENT |
| Status | OPEN |
| Raised in cycle | 1 |
| Affected artifacts | FR-AUTH-003, AC-005 |
| Return to stage | 3 — Requirement Analysis |

**Evidence**

FR-AUTH-003 locks an account after five failed sign-ins. SRC-001 and the decision log contain no threshold, and Q-002 asks for it.

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
