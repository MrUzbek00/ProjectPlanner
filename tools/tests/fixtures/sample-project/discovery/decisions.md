# Decision Log

TEST FIXTURE.

| Decision ID | Date | Question | Options considered | Decision | Rationale | Impact | Approved by | Related requirements | Supersedes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DEC-001 | 2026-09-10 | How long is a reset link valid? (Q-001) | 15 minutes; 30 minutes; 24 hours | Reset links expire 30 minutes after issue | Balances security and convenience | Sets RULE-001 | Fixture owner | RULE-001 | None |
| DEC-002 | 2026-09-12 | How are reset emails sent? | Existing notification service; new mail integration | Use the existing notification service | Avoids a second delivery path | Recorded as ADR-001; creates DEP-001 | Fixture owner | FR-AUTH-001 | None |
| DEC-003 | 2026-09-14 | How are reset tokens stored? | Hash only; encrypted token | Store only a hash of each token | A leaked store must yield no usable token | Recorded as ADR-002 | Fixture owner | SR-001 | None |
