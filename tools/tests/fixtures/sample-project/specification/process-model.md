# Process Model

TEST FIXTURE.

### PROC-001 — Password reset through the help desk

| Field | Value |
| --- | --- |
| Perspective | AS-IS |
| Actor | Registered user; help-desk agent |
| Trigger | The user cannot sign in and phones the help desk |
| Preconditions | The user can prove their identity to the agent |
| Result | The agent sets a temporary password and reads it to the user |
| Business rules | None — the help desk follows no written rule |
| Data involved | ENT-001 |
| Related requirements | BR-001 |
| Confidence | Confirmed |

**Main flow**

1. The user phones the help desk.
2. The agent verifies the user's identity.
3. The agent sets a temporary password.

**Alternative flow**

- None observed.

**Exceptions**

- Identity cannot be verified: the call ends without a reset.

### PROC-002 — Self-service password reset

| Field | Value |
| --- | --- |
| Perspective | TO-BE |
| Replaces | PROC-001 |
| Actor | Registered user |
| Trigger | The user asks to reset a forgotten password |
| Preconditions | The user can read email at the account's address |
| Result | The user signs in with a new password they chose |
| Business rules | RULE-001 |
| Data involved | ENT-001, ENT-002 |
| Related requirements | BR-001, FR-AUTH-001, FR-AUTH-002, SR-001 |
| Confidence | Confirmed |

**Main flow**

1. The user enters their email address (FR-AUTH-001).
2. The system issues a reset token and sends the link (FR-AUTH-001, SR-001).
3. The user opens the link and sets a new password (FR-AUTH-002).

**Alternative flow**

- The address has no active account: the same response is shown and no email is sent.

**Exceptions**

- The link is expired or used: it is rejected and the password is unchanged (RULE-001).

**Differences from AS-IS**

- No help-desk agent is involved.
- The user chooses the new password; no temporary password is read out.
