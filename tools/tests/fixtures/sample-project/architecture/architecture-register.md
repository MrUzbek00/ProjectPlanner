# Architecture Register

TEST FIXTURE.

## ADR register

| ADR ID | Title | Status | Date | Decision owner | Related requirements | Superseded by |
| --- | --- | --- | --- | --- | --- | --- |
| ADR-001 | Send reset emails through the existing notification service | Accepted | 2026-09-12 | Fixture owner | FR-AUTH-001 | None |
| ADR-002 | Store only a hash of each reset token | Accepted | 2026-09-14 | Fixture owner | SR-001 | None |

## Architecture decision coverage

| Concern | Status | ADR IDs | Question | Rationale / evidence |
| --- | --- | --- | --- | --- |
| Architecture style | NOT APPLICABLE | | | The project extends the existing portal and chooses no architecture style (SRC-001) |
| Backend platform | DELEGATED | | | The portal team's existing platform is used unchanged (SRC-001) |
| Frontend architecture | NOT APPLICABLE | | | The reset pages are added to the existing portal (SRC-001) |
| Data storage | NOT APPLICABLE | | | Reset tokens use the portal's existing store (SRC-001) |
| Authentication | NOT APPLICABLE | | | Sign-in itself is unchanged by this project (SRC-001) |
| Authorization model | NOT APPLICABLE | | | Reset needs no role; possession of the link is the credential (SRC-001) |
| API style | NOT APPLICABLE | | | No API is published (SRC-001) |
| Integration strategy | DECIDED | ADR-001 | | Reuse of the notification service (DEC-002) |
| Event-driven messaging | NOT APPLICABLE | | | No asynchronous messaging is in scope (SRC-001) |
| Background processing | NOT APPLICABLE | | | No scheduled or queued work is in scope (SRC-001) |
| Caching | NOT APPLICABLE | | | No caching need is stated (SRC-001) |
| File storage | NOT APPLICABLE | | | No files are stored (SRC-001) |
| Deployment model | DELEGATED | | | Released with the portal's existing deployment (SRC-001) |
| Multi-tenancy | NOT APPLICABLE | | | Single organization (SRC-001) |
| Data ownership | NOT APPLICABLE | | | Entity ownership is recorded per module in the solution structure (SRC-001) |
| Module communication | DECIDED | ADR-001 | | Authentication calls Notifications (DEC-002) |
| Logging and observability | NOT APPLICABLE | | | Delivery is logged by the existing notification service (DEC-002) |
| Security architecture | DECIDED | ADR-002 | | Token storage (DEC-003) |
| External service dependencies | DECIDED | ADR-001 | | DEP-001 (DEC-002) |
| Scalability strategy | NOT APPLICABLE | | | No volume target is stated (SRC-001) |
