# Security Requirements

TEST FIXTURE.

### SR-001 — Reset tokens are unguessable and stored only as hashes

| Field | Value |
| --- | --- |
| Status | Approved |
| Scope | In scope |
| Confidence | Confirmed |
| Priority | High |
| Priority basis | Confirmed — SRC-001 section 3 |
| Source | BR-001 |
| Evidence | SRC-001 |
| Related stakeholder | Fixture owner |
| Dependencies | None |
| Related modules | MOD-001 |
| Category | Credential protection |

**Description**

Reset tokens carry at least 128 bits of randomness and only a hash of each token is stored.

**Rationale**

A leaked token store must not allow anyone to reset a password.

**Acceptance criteria**

- AC-006 — The token store contains no plain-text token value.
