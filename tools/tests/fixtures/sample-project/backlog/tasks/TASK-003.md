# TASK-003 — Users can set a new password from a valid reset link

TEST FIXTURE.

## Card metadata

| Field | Value |
| --- | --- |
| Epic | EPIC-001 Self-service account access |
| Feature | FEAT-001 Password reset by email |
| Parent task | None |
| Type | fullstack |
| Related Requirement IDs | FR-AUTH-002, RULE-001 |
| Approved specification version | 1.0 (APR-001) |
| Priority | High |
| Priority basis | Confirmed — SRC-001 |
| Estimated Complexity | M — link validation and password change |
| Phase | PHASE-01 |
| Blocked By | TASK-001 |
| External dependencies | None |
| Architecture decisions | None |
| Related modules | MOD-001 |
| Required test levels | unit, integration, security, e2e |
| Status | READY |
| Revision | 1 |
| Readiness blockers | None |

## Goal

Let a user regain access by choosing a new password from the emailed link (BR-001).

## Description

A user who opens a reset link that is valid, unused and less than 30 minutes old sets a new password, and the link is marked used at the same moment. Any other link is rejected and the password stays unchanged.

## Data Impact

- Affected entities: ENT-001 (the account's password is replaced) and ENT-002 (the token is marked used).
- Migration expected: none.

## UI Impact

- New screen: set a new password from the link.
- User states: success, and a rejection message for an expired or used link (AC-004).

## Constraints

| Kind | Constraint | Reference |
| --- | --- | --- |
| Architecture | Look tokens up by hash through the token store | ADR-002 |
| Security | A token expires 30 minutes after issue and is single use | RULE-001 |

## Acceptance Criteria

| AC ID | Given | When | Then / And — measurable result | Requirement IDs | TEST IDs |
| --- | --- | --- | --- | --- | --- |
| AC-003 | a token issued 29 minutes ago and unused | a new password is submitted | the password changes and the token is marked used | FR-AUTH-002 | TEST-003 |
| AC-004 | a token issued 31 minutes ago, or already used | a new password is submitted | the request is rejected and the password is unchanged | FR-AUTH-002, RULE-001 | TEST-003 |

## Testing Checklist

| TEST ID | Type | Fixture / preconditions | Expected evidence | Required for this card? / reason | Execution status / evidence |
| --- | --- | --- | --- | --- | --- |
| TEST-003 | Integration | Tokens at 29 and 31 minutes, one used | Only the fresh unused token succeeds | Yes — FR-AUTH-002, RULE-001 | NOT RUN |

## Readiness history

| Date | From | To | Reason | Change ID |
| --- | --- | --- | --- | --- |
| 2026-09-22 | — | DRAFT | Card written from FEAT-001 | |
| 2026-09-22 | DRAFT | READY | Definition of Ready passed; validated by the fixture analyst | |
