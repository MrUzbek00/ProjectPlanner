# TASK-004 — Accounts lock after repeated failed sign-ins

TEST FIXTURE.

## Card metadata

| Field | Value |
| --- | --- |
| Epic | EPIC-001 Self-service account access |
| Feature | FEAT-002 Account lockout |
| Parent task | None |
| Type | backend |
| Related Requirement IDs | FR-AUTH-003 |
| Approved specification version | 1.0 (APR-001) |
| Priority | Medium |
| Priority basis | Proposed — awaiting Q-002 |
| Estimated Complexity | S |
| Phase | PHASE-02 |
| Blocked By | None |
| External dependencies | None |
| Architecture decisions | None |
| Related modules | MOD-001 |
| Required test levels | unit, integration |
| Status | NEEDS_DISCOVERY |
| Revision | 1 |
| Readiness blockers | The lockout threshold is unknown until Q-002 is answered |

## Goal

Stop repeated guessing of a password by locking the account (FR-AUTH-003).

## Description

Lock the account after the confirmed number of consecutive failed sign-ins: TBD (Q-002).

## Constraints

| Kind | Constraint | Reference |
| --- | --- | --- |
| Architecture | N/A — no architecture decision beyond the existing module | MOD-001 |
| Security | Lockout applies per account (unconfirmed, ASM-001) | Q-002 |

## Acceptance Criteria

| AC ID | Given | When | Then / And — measurable result | Requirement IDs | TEST IDs |
| --- | --- | --- | --- | --- | --- |
| AC-005 | TBD (Q-002) consecutive failed sign-ins | another sign-in is attempted | the account is locked | FR-AUTH-003 | TEST-004 |

## Testing Checklist

| TEST ID | Type | Fixture / preconditions | Expected evidence | Required for this card? / reason | Execution status / evidence |
| --- | --- | --- | --- | --- | --- |
| TEST-004 | Integration | Account with failed attempts | Account locked at the threshold | Yes — FR-AUTH-003 | NOT RUN |

## Readiness history

| Date | From | To | Reason | Change ID |
| --- | --- | --- | --- | --- |
| 2026-09-22 | — | DRAFT | Card written from FEAT-002 | |
| 2026-09-22 | DRAFT | NEEDS_DISCOVERY | Threshold awaits Q-002 | |
