# User Journey and User Stories

TEMPLATE — generated from approved project records — NOT APPROVED

Journeys describe how a confirmed role actually completes a confirmed process, including where it currently hurts. Stories are the implementation-facing restatement of approved functional requirements. A story that no `FR-###` supports is not a story; it is a change request.

<!-- doc-meta
title: User Journey and User Stories
subtitle: Personas, end-to-end journeys, story backlog and acceptance criteria
project: TBD
client: TBD
version: 0.1 DRAFT
date: TBD
author: TBD
status: DRAFT
-->

## 1. Document Control

| Version | Date | Author / editor | Change summary | Source records | Status |
| --- | --- | --- | --- | --- | --- |

Source specification revision: TBD. Document language: TBD.

## 2. Personas

Personas mirror the PRD. Keep one canonical definition; if they differ, the PRD is wrong or this document is stale.

| Persona ID | Persona | ROLE ID | Context of use | Primary goal | Key constraints | Success signal | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |

## 3. Journey Inventory

| Journey ID | Journey | Persona | Business process (PROC-###) | Trigger | End state | Frequency | Criticality | Related BIZ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## 4. Journey Maps

Repeat this structure for every journey. Keep the current-state and future-state columns distinct; do not merge an observed pain point with a proposed solution.

### Journey ID: TBD — TBD

- **Persona:** TBD
- **Goal:** TBD
- **Trigger:** TBD
- **Preconditions:** TBD
- **Successful end state:** TBD
- **Evidence:** TBD

| Step | Stage | What the user does today (AS-IS) | Touchpoint / system today | Time and effort | Thoughts and feelings | Pain point | Evidence | What the user does in the new system (TO-BE) | Screen (PAGE-###) | Supporting FR | Opportunity / improvement | Measured by |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

**Moments that matter**

| Moment | Why it is decisive | Risk if it fails | Requirement that addresses it |
| --- | --- | --- | --- |

**Journey exits and failure paths**

| Exit point | Cause | Current outcome | New-system outcome | Handled by (FR / BR) |
| --- | --- | --- | --- | --- |

### 4.1 Process Diagram

Embed the generated BPMN process diagrams here, one per confirmed process, with the caption carrying the DIAG ID and the notation statement. Specify each diagram in the BPMN diagram record before generating it.

```markdown
![DIAG-001 — <process>, TO-BE. Drawn in BPMN 2.0 notation; not a BPMN 2.0 XML interchange file.](diagrams/diag-001-<process>-tobe.png)
```

A journey map and a BPMN diagram answer different questions: the journey carries what the person experiences, the BPMN diagram carries who performs which step in which order. Keep both; do not replace one with the other.

## 5. Service Blueprint

Include only where the confirmed process involves backstage work, handoffs or supporting systems worth making explicit.

| Journey step | Frontstage user action | Visible system response | Backstage action | Actor | Supporting system | Handoff | Failure point |
| --- | --- | --- | --- | --- | --- | --- | --- |

## 6. Cross-journey Pain Point Register

| Pain ID | Pain point | Journeys affected | Personas affected | Frequency | Business impact | Evidence | Addressed by | Residual after release |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Every confirmed pain point is either addressed by an approved requirement or explicitly recorded as not addressed, with a reason.

## 7. Epics

| Epic ID | Epic | Business outcome | Personas | Journeys covered | Related BIZ | Features | Stories | Release | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## 8. User Story Backlog

<!-- xlsx: workbook=requirements; sheet=User Stories -->

| Story ID | Epic | Feature | As a (persona / ROLE) | I want | So that | Journey step | Screen (PAGE) | Related FR | Related BR | Priority (MoSCoW) | Complexity | Release | Dependencies | Card ID | Acceptance criteria IDs | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

A story is ready when its persona is a confirmed role, its value statement traces to an approved objective, its acceptance criteria are measurable, and its dependencies are known.

## 9. Story Detail

Repeat per story. Detail is required before a story is treated as ready.

- **Story ID:** TBD
- **Title:** TBD
- **As a** TBD **I want** TBD **so that** TBD
- **Journey and step:** TBD
- **Preconditions:** TBD
- **Permissions required:** TBD (ROLE-###)
- **Data touched:** TBD (ENT-###)
- **Business rules applied:** TBD (BR-###)
- **Screens:** TBD (PAGE-###)
- **Notifications triggered:** TBD (NOTIF-###)
- **Out of scope for this story:** TBD
- **Open questions:** TBD (Q-###)
- **Traceability:** FR TBD / Card TBD / Test TBD

## 10. Acceptance Criteria

<!-- xlsx: workbook=requirements; sheet=Acceptance Criteria -->

| AC ID | Story ID | Scenario name | Given | When | Then | Measurable condition | Type (happy path / alternative / negative / permission / validation) | Test ID | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Each story carries at least one happy-path criterion, one negative or validation criterion where inputs exist, and one permission criterion where access is restricted. A criterion that cannot be observed and judged is not acceptance criteria.

## 11. Story Map

Rows are releases; columns are journey activities. Cells hold story IDs.

| Activity → / Release ↓ | Activity 1 | Activity 2 | Activity 3 | Activity 4 |
| --- | --- | --- | --- | --- |
| MVP | TBD | TBD | TBD | TBD |
| Release 2 | TBD | TBD | TBD | TBD |
| Later | TBD | TBD | TBD | TBD |

The MVP row must form a complete walking path across the activities of at least one confirmed end-to-end journey. If it does not, the MVP definition is incomplete.

## 12. Edge Cases and Negative Paths

| Case ID | Journey / story | Condition | Expected system behavior | User-facing message | Recovery | Covered by (FR / AC) | Confirmed |
| --- | --- | --- | --- | --- | --- | --- | --- |

## 13. Accessibility and Inclusion in Journeys

| Consideration | Journeys affected | Requirement | Confirmed or recommended | Evidence |
| --- | --- | --- | --- | --- |

## 14. Story Estimation Summary

| Complexity | Count | Story IDs | Drivers |
| --- | --- | --- | --- |
| XS | TBD | TBD | TBD |
| S | TBD | TBD | TBD |
| M | TBD | TBD | TBD |
| L | TBD | TBD | TBD |
| XL | TBD | TBD | TBD |

Complexity does not convert to a date until team capacity is confirmed. Decompose every L or XL story that cannot be implemented and tested as one bounded task.

## 15. Coverage Check

| Check | Result | Evidence | Findings |
| --- | --- | --- | --- |
| Every approved FR maps to at least one story | TBD | TBD | TBD |
| Every story maps to an approved FR | TBD | TBD | TBD |
| Every confirmed journey has stories covering its end-to-end path | TBD | TBD | TBD |
| Every story has measurable acceptance criteria | TBD | TBD | TBD |
| Every restricted action has a permission criterion | TBD | TBD | TBD |
| No story depends on an unanswered blocking question | TBD | TBD | TBD |

## 16. Open Questions

| Q ID | Question | Affected journey / story | Why it matters | Owner | Status | Answer |
| --- | --- | --- | --- | --- | --- | --- |
