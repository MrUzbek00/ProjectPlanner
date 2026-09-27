# TASK-002 — Users can request a password-reset email

TEST FIXTURE.

## Card metadata

| Field | Value |
| --- | --- |
| Epic | EPIC-001 Self-service account access |
| Feature | FEAT-001 Password reset by email |
| Parent task | None |
| Type | fullstack |
| Related Requirement IDs | FR-AUTH-001 |
| Approved specification version | 1.0 (APR-001) |
| Priority | High |
| Priority basis | Confirmed — SRC-001 |
| Estimated Complexity | M — request form, token issue and email |
| Phase | PHASE-01 |
| Blocked By | TASK-001 |
| External dependencies | DEP-001 |
| Architecture decisions | None |
| Related modules | MOD-001, MOD-002 |
| Required test levels | unit, integration, security, e2e |
| Status | READY |
| Revision | 1 |
| Risks | RISK-001 |
| Readiness blockers | None |

## Goal

Let a user start a password reset without contacting the help desk (BR-001).

## Description

A user enters an email address. When it belongs to an active account, a reset token is issued and the reset link is emailed through the notification service. The response is identical whether or not the address belongs to an account.

## Data Impact

- Affected entities: ENT-002 (reset token) is created when an active account requests a reset; ENT-001 is read, not changed.
- Migration expected: none.

## UI Impact

- Modified screen: the sign-in screen gains a "Forgot password" entry; a new request screen takes an email address.
- User states: the same confirmation message for every submitted address (AC-002); a validation error for an empty or malformed address.

## Integration Impact

- Provider: the existing notification service (DEP-001, ADR-001); purpose: deliver the reset email.
- Request: recipient address and reset link. Response: accepted or rejected by the service. Authentication: the service's existing credentials.
- Failure behaviour: when the service is unavailable the user still sees the neutral confirmation, and the failure is logged (RISK-001). Timeout and retry: as the notification service already handles them. Fallback: none in scope.

## Constraints

| Kind | Constraint | Reference |
| --- | --- | --- |
| Architecture | Send the email through the existing notification service | ADR-001 |
| Security | Do not reveal whether an email address belongs to an account | FR-AUTH-001 |

## Acceptance Criteria

| AC ID | Given | When | Then / And — measurable result | Requirement IDs | TEST IDs |
| --- | --- | --- | --- | --- | --- |
| AC-001 | an active account with that email | a reset is requested | one reset email is sent | FR-AUTH-001 | TEST-002 |
| AC-002 | an address with no active account | a reset is requested | the request is rejected silently: no email is sent and the response is identical | FR-AUTH-001 | TEST-002 |

## Testing Checklist

| TEST ID | Type | Fixture / preconditions | Expected evidence | Required for this card? / reason | Execution status / evidence |
| --- | --- | --- | --- | --- | --- |
| TEST-002 | Integration | One active account | Email sent; responses identical | Yes — FR-AUTH-001 | NOT RUN |

## Readiness history

| Date | From | To | Reason | Change ID |
| --- | --- | --- | --- | --- |
| 2026-09-22 | — | DRAFT | Card written from FEAT-001 | |
| 2026-09-22 | DRAFT | READY | Definition of Ready passed; validated by the fixture analyst | |
