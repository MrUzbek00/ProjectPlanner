# Business Rules

TEST FIXTURE.

### RULE-001 — A reset link is valid for 30 minutes and only once

| Field | Value |
| --- | --- |
| Status | Approved |
| Scope | In scope |
| Confidence | Confirmed |
| Priority | High |
| Priority basis | Confirmed — DEC-001 |
| Source | BR-001 |
| Evidence | DEC-001 |
| Related stakeholder | Fixture owner |
| Dependencies | None |
| Related modules | MOD-001 |

**Description**

A password-reset link expires 30 minutes after it is issued and cannot be used a second time.

**Rationale**

Decided in DEC-001 to balance security and convenience.
