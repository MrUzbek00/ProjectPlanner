# Technical Specification — Sample Portal

TEST FIXTURE. Version 1.0 · APPROVED (APR-001). This specification consolidates the records; it defines nothing of its own.

## 1. Project Information

Sample Portal, owned by the fixture owner. Version 1.0.

## 2. Project Objective

GOAL-001 — users regain account access without help-desk involvement. Baseline and target: TBD (Q-004).

## 3. Project Overview

AS-IS: PROC-001, help-desk reset. TO-BE: PROC-002, self-service reset. Scope register: SCOPE-001 in scope; SCOPE-002 pending decision; SCOPE-003 out of scope; SCOPE-004 future.

## 4. Stakeholders and User Roles

Fixture owner (sponsor, decision authority). Registered users.

## 5. User Scenarios

A registered user resets a forgotten password from an emailed link (BR-001).

## 6. System Modules

MOD-001 Authentication; MOD-002 Notifications.

## 7. Detailed Functional Requirements

FR-AUTH-001 request a password reset; FR-AUTH-002 set a new password with a reset link. FR-AUTH-003 account lockout is PENDING DECISION (Q-002).

## 8. Page / Screen Specifications

Reset request form and new-password form, as described in FR-AUTH-001 and FR-AUTH-002.

## 9. Business Rules

RULE-001 — a reset link is valid for 30 minutes and only once.

## 10. Workflow and Approval Rules

No approvals. Reset token states in ENT-002: ISSUED, USED, EXPIRED.

## 11. Master Data

N/A — no master data; confirmed by the owner (discovery log).

## 12. Dashboard Requirements

N/A — reporting is not applicable (discovery log).

## 13. Reports and Exports

N/A — reporting is not applicable (discovery log).

## 14. Notifications

One reset email per request, through MOD-002 (ADR-001).

## 15. Audit Logs

Delivery failures are logged by the notification service (RISK-001).

## 16. Integrations

Existing notification service (DEP-001, ADR-001).

## 17. File Management

N/A — no files are handled.

## 18. Non-Functional Requirements

SR-001 — reset tokens are unguessable and stored only as hashes.

## 19. Technology Stack

ADR-001 and ADR-002.

## 20. Data Model

ENT-001 Account; ENT-002 Reset token.

## 21. Acceptance Criteria

As recorded with FR-AUTH-001, FR-AUTH-002, SR-001 and BR-001.

## 22. Testing Requirements

TEST-001 to TEST-004 in quality/acceptance-tests.md.

## 23. Project Phases

PHASE-01 core product; PHASE-02 enhancement, pending Q-002.

## 24. Deliverables

The planning package listed in the manifest.

## 25. Open Questions

Q-002 (BLOCKER, scoped out with FR-AUTH-003), Q-003, Q-004.

## 26. Risks and Dependencies

RISK-001, RISK-002; DEP-001.
