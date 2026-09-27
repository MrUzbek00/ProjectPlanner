# Development Backlog, Dependencies and Roadmap

TEST FIXTURE. Project: Sample Portal · Approved specification: 1.0 · Approval evidence: APR-001

## Epics and features

### EPIC-001 — Self-service account access

| Field | Value |
| --- | --- |
| Goal | Users regain access without the help desk |
| Related Requirement IDs | BR-001 |
| Priority | High |
| Priority basis | Confirmed — SRC-001 |
| Status | READY |

#### FEAT-001 — Password reset by email

| Field | Value |
| --- | --- |
| Epic | EPIC-001 |
| Scope | In scope |
| Goal | A user resets a forgotten password from an emailed link |
| Related Requirement IDs | FR-AUTH-001, FR-AUTH-002, SR-001, RULE-001 |
| Modules | MOD-001, MOD-002 |
| Architecture decisions | ADR-001, ADR-002 |
| Depends on | None |
| External dependencies | DEP-001 |
| Priority | High |
| Priority basis | Confirmed — SRC-001 |
| Status | READY |

#### FEAT-002 — Account lockout

| Field | Value |
| --- | --- |
| Epic | EPIC-001 |
| Scope | Pending decision |
| Goal | Repeated failed sign-ins lock the account |
| Related Requirement IDs | FR-AUTH-003 |
| Modules | MOD-001 |
| Depends on | None |
| External dependencies | None |
| Priority | Medium |
| Priority basis | Proposed — awaiting Q-002 |
| Status | NEEDS_DISCOVERY |

## Backlog index

| Task ID | Level | Epic | Feature | Parent task if any | Title / detail path | Requirement IDs | Priority / confirmation | Complexity | Status | Blocked By | Phase |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TASK-001 | Task | EPIC-001 | FEAT-001 | None | tasks/TASK-001.md | SR-001, RULE-001 | High / confirmed | S | READY | None | PHASE-01 |
| TASK-002 | Task | EPIC-001 | FEAT-001 | None | tasks/TASK-002.md | FR-AUTH-001 | High / confirmed | M | READY | TASK-001 | PHASE-01 |
| TASK-003 | Task | EPIC-001 | FEAT-001 | None | tasks/TASK-003.md | FR-AUTH-002, RULE-001 | High / confirmed | M | READY | TASK-001 | PHASE-01 |
| TASK-004 | Task | EPIC-001 | FEAT-002 | None | tasks/TASK-004.md | FR-AUTH-003 | Medium / proposed | S | NEEDS_DISCOVERY | None | PHASE-02 |

## Roadmap

### PHASE-01 — Core product: password reset

| Field | Value |
| --- | --- |
| Objective | Users can reset a forgotten password end to end |
| Exit Criteria | TEST-001 to TEST-003 defined and passing in the test environment |
| Date | None |
| Date basis | None |

### PHASE-02 — Enhancement: account lockout

| Field | Value |
| --- | --- |
| Objective | Accounts lock after the confirmed number of failed sign-ins, once Q-002 is answered |
| Exit Criteria | TEST-004 defined and passing |
| Date | None |
| Date basis | None |
