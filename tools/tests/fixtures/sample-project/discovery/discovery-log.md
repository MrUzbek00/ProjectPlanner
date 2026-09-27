# Discovery Log

TEST FIXTURE.

## Coverage

| Category | Status | Confirmed information | Open questions | Assumptions | Risks | Sources |
| --- | --- | --- | --- | --- | --- | --- |
| Business | COMPLETE | Goal and business requirement confirmed (GOAL-001, BR-001) | Q-004 | | | SRC-001 |
| Users | COMPLETE | Registered portal users; no administrator role in scope | | | | SRC-001 |
| Workflows | COMPLETE | AS-IS help-desk reset and TO-BE self-service reset (PROC-001, PROC-002) | | | | Round 1 |
| Data | COMPLETE | Account and reset token (ENT-001, ENT-002) | | | | Round 2 |
| Integrations | COMPLETE | Existing notification service only (DEP-001) | | | RISK-001 | DEC-002 |
| Security | PARTIAL | Token expiry and single use confirmed (RULE-001, SR-001) | Q-002 | ASM-001 | RISK-002 | DEC-001 |
| Permissions | COMPLETE | Only the account holder can reset their password | | | | Round 2 |
| Reporting | NOT APPLICABLE | Owner confirmed no reports are needed | | | | Round 1 answer |
| Notifications | COMPLETE | One reset email per request | Q-003 | | | SRC-001 |
| Technical constraints | COMPLETE | Use the existing notification service | | | | DEC-002 |
| UI/UX | COMPLETE | Request form and new-password form | | | | SRC-001 |
| Operations | NOT APPLICABLE | No operational process changes; confirmed by owner | | | | Round 2 answer |
| Compliance | NOT APPLICABLE | No regulated data beyond account credentials; confirmed by owner | | | | Round 2 answer |
| Migration | NOT APPLICABLE | No existing reset data to migrate; confirmed by owner | | | | Round 2 answer |
