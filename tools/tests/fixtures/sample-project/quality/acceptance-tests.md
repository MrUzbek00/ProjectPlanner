# Acceptance Criteria and Test Definitions

TEST FIXTURE. Project: Sample Portal · Specification baseline: 1.0

### TEST-001 — Token store keeps no plain-text token

| Field | Value |
| --- | --- |
| Test level | integration |
| Category | Security |
| Requirement IDs | SR-001 |
| Acceptance criteria | AC-006 |
| Preconditions | Empty token store |
| Expected result | The stored record holds a hash; searching the store for the token value finds nothing |
| Execution status | NOT RUN |

| Step | Action / input | Expected observable result |
| --- | --- | --- |
| 1 | Issue a token | One record is stored |
| 2 | Search the store for the token value | No match |

### TEST-002 — Reset request sends one email and does not reveal accounts

| Field | Value |
| --- | --- |
| Test level | integration |
| Category | Functional, negative |
| Requirement IDs | FR-AUTH-001 |
| Acceptance criteria | AC-001, AC-002 |
| Preconditions | One active account |
| Expected result | One email for the known address; identical responses for known and unknown addresses |
| Execution status | NOT RUN |

### TEST-003 — Only a fresh, unused token sets a new password

| Field | Value |
| --- | --- |
| Test level | integration |
| Category | Functional, boundary |
| Requirement IDs | FR-AUTH-002, RULE-001 |
| Acceptance criteria | AC-003, AC-004 |
| Preconditions | Tokens issued 29 and 31 minutes ago; one already used |
| Expected result | Only the 29-minute unused token succeeds; the others are rejected and the password is unchanged |
| Execution status | NOT RUN |

### TEST-004 — Account locks at the confirmed threshold

| Field | Value |
| --- | --- |
| Test level | integration |
| Category | Functional |
| Requirement IDs | FR-AUTH-003 |
| Acceptance criteria | AC-005 |
| Preconditions | Account with consecutive failed sign-ins |
| Expected result | The account locks at the threshold confirmed by Q-002 |
| Execution status | NOT RUN |
