# ADR-002 — Store only a hash of each reset token

TEST FIXTURE.

| Field | Value |
| --- | --- |
| Status | Accepted |
| Date | 2026-09-14 |
| Decision owner / Approver | Fixture owner |
| Approval evidence | DEC-003 |
| Decision question | None |
| Related requirements | SR-001 |
| Related features | None |
| Affected modules | MOD-001 |
| Related decisions | DEC-003 |
| Principles | None |
| Depends on | None |
| Conflicts with | None |
| Supersedes | None |
| Superseded by | None |

## Context

SR-001 forbids storing reset tokens in a recoverable form.

## Decision

The token store keeps a one-way hash of each token, its account, its issue time and its used flag. The token itself exists only in the email.

## Rationale

A leaked token store must not let anyone reset a password (SR-001); only a one-way hash guarantees that.

## Alternatives considered

| Option | Description | Advantages | Disadvantages | Outcome |
| --- | --- | --- | --- | --- |
| Hash only | Store a hash of the token | A leaked store yields no usable token | Tokens cannot be re-sent | Chosen |
| Encrypted token | Store the token encrypted | Tokens can be re-sent | A leaked key exposes every live token | Rejected |

## Consequences

### Positive

- A leaked token store yields no usable token.

### Negative

- A lost email means requesting a new link; the old one cannot be re-sent.

## Risks

None.

## Constraints introduced

- No reset token is stored in a recoverable form, encrypted or plain.
- A reset link cannot be re-sent; a new request issues a new token.

## Notes

None.
