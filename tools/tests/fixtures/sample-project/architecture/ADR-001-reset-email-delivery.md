# ADR-001 — Send reset emails through the existing notification service

TEST FIXTURE.

| Field | Value |
| --- | --- |
| Status | Accepted |
| Date | 2026-09-12 |
| Decision owner / Approver | Fixture owner |
| Approval evidence | DEC-002 |
| Decision question | None |
| Related requirements | FR-AUTH-001 |
| Related features | None |
| Affected modules | MOD-002 |
| Related decisions | DEC-002 |
| Principles | PRIN-001 |
| Depends on | DEP-001 |
| Conflicts with | None |
| Supersedes | None |
| Superseded by | None |

## Context

FR-AUTH-001 requires an email. The organization already operates a notification service with delivery logging.

## Decision

Password-reset emails are sent by calling the existing notification service. No new mail integration is added.

## Rationale

One delivery path keeps sending, logging and monitoring in one place (PRIN-001), and the owner chose it in DEC-002.

## Alternatives considered

| Option | Description | Advantages | Disadvantages | Outcome |
| --- | --- | --- | --- | --- |
| Existing notification service | Reuse the current service | One delivery path; existing logging | Depends on that service's availability | Chosen |
| Direct SMTP integration | Send mail from the authentication module | No dependency on another service | Second delivery path to secure and monitor | Rejected |

## Consequences

### Positive

- Delivery failures are visible in the notification service's existing log.

### Negative

- The reset request depends on the notification service being reachable.

## Risks

- RISK-001 — the notification service is unavailable and reset emails are delayed.

## Constraints introduced

- Reset emails are sent only through MOD-002; no module sends email directly.
- A new delivery channel for account emails requires a new ADR.

## Notes

None.
