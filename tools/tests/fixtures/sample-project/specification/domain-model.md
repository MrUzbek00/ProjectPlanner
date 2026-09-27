# Domain Model

TEST FIXTURE.

### ENT-001 — Account

| Field | Value |
| --- | --- |
| Purpose | A registered user's access to the portal |
| Ownership | MOD-001 Authentication |
| Lifecycle states | ACTIVE, INACTIVE |
| Permissions | Only the account holder can change its password |
| Business rules | None |
| Related requirements | FR-AUTH-001, FR-AUTH-002 |
| Confidence | Confirmed |

**Key attributes**

- Email address
- Password (never stored in plain text)
- State

**Relationships**

- Has zero or more reset tokens (ENT-002)

### ENT-002 — Reset token

| Field | Value |
| --- | --- |
| Purpose | Proof that a reset was requested for an account |
| Ownership | MOD-001 Authentication |
| Lifecycle states | ISSUED, USED, EXPIRED |
| Permissions | Created by the system; redeemed only by the holder of the link |
| Business rules | RULE-001 |
| Related requirements | FR-AUTH-001, FR-AUTH-002, SR-001 |
| Confidence | Confirmed |

**Key attributes**

- Token hash
- Issue time
- Used flag

**Relationships**

- Belongs to exactly one account (ENT-001)
