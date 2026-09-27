# Functional Requirements

TEST FIXTURE.

### FR-AUTH-001 — Request a password reset

| Field | Value |
| --- | --- |
| Status | Approved |
| Scope | In scope |
| Confidence | Confirmed |
| Priority | High |
| Priority basis | Confirmed — SRC-001 section 2 |
| Source | BR-001 |
| Evidence | SRC-001 |
| Related stakeholder | Fixture owner |
| Actor | Registered user |
| Trigger | The user asks to reset a forgotten password |
| Permissions | Anyone may request a reset; the email only reaches the account's own address |
| Dependencies | None |
| Business rules | RULE-001 |
| Related modules | MOD-001, MOD-002 |

**Description**

A user can request a password-reset email by entering an email address.

**Rationale**

The first step of the self-service reset in PROC-002.

**Acceptance criteria**

- AC-001 — A reset email is sent when the address belongs to an active account.
- AC-002 — A request for an address with no active account is rejected silently: no email is sent and the response is identical.

### FR-AUTH-002 — Set a new password with a reset link

| Field | Value |
| --- | --- |
| Status | Approved |
| Scope | In scope |
| Confidence | Confirmed |
| Priority | High |
| Priority basis | Confirmed — SRC-001 section 2 |
| Source | BR-001 |
| Evidence | SRC-001 |
| Related stakeholder | Fixture owner |
| Actor | Registered user |
| Trigger | The user opens the link from the reset email |
| Permissions | Only the holder of a valid link can set the password for that account |
| Dependencies | FR-AUTH-001 |
| Business rules | RULE-001 |
| Related modules | MOD-001 |

**Description**

A user who follows a valid reset link can set a new password.

**Rationale**

Completes the self-service reset in PROC-002.

**Acceptance criteria**

- AC-003 — A valid, unused link within 30 minutes of issue accepts a new password.
- AC-004 — An expired or already used link is rejected and the password is unchanged.

### FR-AUTH-003 — Lock an account after repeated failed sign-ins

| Field | Value |
| --- | --- |
| Status | Confirmed |
| Scope | Pending decision |
| Confidence | Confirmed |
| Priority | Medium |
| Priority basis | Proposed — awaiting Q-002 |
| Source | BR-001 |
| Evidence | SRC-001 |
| Related stakeholder | Fixture owner |
| Actor | Registered user |
| Trigger | Consecutive failed sign-ins |
| Permissions | N/A — system behaviour, no user action is permitted or denied beyond sign-in |
| Dependencies | None |
| Related modules | MOD-001 |

**Description**

An account is locked after a number of consecutive failed sign-ins: TBD (Q-002).

**Rationale**

Requested by the owner in round 2; the threshold is undecided.

**Acceptance criteria**

- AC-005 — The account is locked after the confirmed number of consecutive failures: TBD (Q-002).
