# TASK-001 — Reset tokens are stored so that they cannot be recovered

TEST FIXTURE.

## Card metadata

| Field | Value |
| --- | --- |
| Epic | EPIC-001 Self-service account access |
| Feature | FEAT-001 Password reset by email |
| Parent task | None |
| Type | database |
| Related Requirement IDs | SR-001, RULE-001 |
| Approved specification version | 1.0 (APR-001) |
| Priority | High |
| Priority basis | Confirmed — SRC-001 |
| Estimated Complexity | S — one kind of record and its lookup |
| Phase | PHASE-01 |
| Blocked By | None |
| External dependencies | None |
| Architecture decisions | ADR-002 |
| Related modules | MOD-001 |
| Required test levels | unit, integration |
| Status | READY |
| Revision | 1 |
| Readiness blockers | None |

## Goal

Provide what FR-AUTH-001 and FR-AUTH-002 need to issue and redeem reset links safely.

## Description

Issued reset tokens are kept as one-way hashes together with their account, issue time and used flag, so that a token can be found by its hash and marked used exactly once.

## Data Impact

- Affected entities: ENT-002 (reset token).
- Create / update / delete: a token record is created on issue; its used flag is updated on redemption; nothing is deleted.
- Ownership: MOD-001 owns the token store.
- Lifecycle: ISSUED → USED or EXPIRED (RULE-001).
- Migration expected: none — the store is new.
- Retention impact: none stated in the sources.

## Constraints

| Kind | Constraint | Reference |
| --- | --- | --- |
| Architecture | Store only a hash of the token; never the token itself | ADR-002 |
| Security | Token values carry at least 128 bits of randomness | SR-001 |
| Security | Marking a token used is atomic, so a token cannot be redeemed twice | RULE-001 |

## Acceptance Criteria

| AC ID | Given | When | Then / And — measurable result | Requirement IDs | TEST IDs |
| --- | --- | --- | --- | --- | --- |
| AC-006 | a token has been issued | the store is inspected | no plain-text token value is present | SR-001 | TEST-001 |

## Testing Checklist

| TEST ID | Type | Fixture / preconditions | Expected evidence | Required for this card? / reason | Execution status / evidence |
| --- | --- | --- | --- | --- | --- |
| TEST-001 | Integration | Empty store | Stored record holds a hash only | Yes — SR-001 | NOT RUN |

## Readiness history

| Date | From | To | Reason | Change ID |
| --- | --- | --- | --- | --- |
| 2026-09-22 | — | DRAFT | Card written from FEAT-001 | |
| 2026-09-22 | DRAFT | READY | Definition of Ready passed; validated by the fixture analyst | |
