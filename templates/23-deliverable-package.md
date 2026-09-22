# Deliverable Document Package Manifest

TEMPLATE — package index, generation log and pre-release review

This record governs the Word and Excel package generated from the completed project Markdown. It states which source records each document was built from, which files were produced, what the generator reported, and what was verified by reading the exported files.

<!-- doc-meta
title: Deliverable Document Package Manifest
subtitle: Package contents, sources, generation log and release review
project: TBD
client: TBD
version: 0.1 DRAFT
date: TBD
author: TBD
status: DRAFT
-->

## 1. Package Identity

| Item | Value |
| --- | --- |
| Project | TBD |
| Package version | TBD |
| Generated on | TBD |
| Document language | TBD |
| Source specification revision | TBD |
| Source backlog revision | TBD |
| Approval baseline covered | TBD |
| Generator version | TBD |
| Output location | TBD |

## 2. Package Contents

| Document | Source Markdown | Word output | Status | Approved by | Date |
| --- | --- | --- | --- | --- | --- |
| Product Requirements Document | `deliverables/prd.md` | TBD | TBD | TBD | TBD |
| Business Requirements Document | `deliverables/brd.md` | TBD | TBD | TBD | TBD |
| Software Requirements Specification | `deliverables/srs.md` | TBD | TBD | TBD | TBD |
| Statement of Work and Scope Statement | `deliverables/sow.md` | TBD | TBD | TBD | TBD |
| User Journey and User Stories | `deliverables/user-journey-stories.md` | TBD | TBD | TBD | TBD |
| Wireframes and UI/UX Specification | `deliverables/wireframes-uiux.md` | TBD | TBD | TBD | TBD |
| Project Plan and Roadmap | `deliverables/project-plan-roadmap.md` | TBD | TBD | TBD | TBD |

| Diagram | DIAG ID | Tool | Editable source | Export embedded | Embedded in | Rendered and inspected | Status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| BPMN process diagram | TBD | Excalidraw skill | TBD | TBD | TBD | TBD | TBD |
| Proposed data model (ER) | TBD | draw.io skill | TBD | TBD | TBD | TBD | TBD |
| Entity state diagram | TBD | draw.io skill | TBD | TBD | TBD | TBD | TBD |

| Workbook | Sheets | Source sections | Output | Status |
| --- | --- | --- | --- | --- |
| Requirements and traceability | Business Requirements, Product Features, Functional Requirements, Business Rules, Non-Functional Requirements, Success Metrics, User Stories, Acceptance Criteria, Traceability | PRD 3 and 6.1; BRD 5 and 11; SRS 6.1, 11, 19; Stories 8 and 10 | TBD | TBD |
| Project plan and roadmap | Scope, Deliverables, WBS, Milestones, Phases, Sprints, Task Schedule, Dependencies, Resource Allocation, RACI, Release Plan | SOW 4.1, 6, 7; Plan 3, 4, 6, 7, 8, 9, 10, 11 | TBD | TBD |
| Requirements and traceability, data sheets | Data Model, Data Dictionary | ER diagram record 3.1 and 3.2 | TBD | TBD |

## 3. Source Coverage

| Deliverable document | Project records it was built from | Records deliberately excluded | Reason for exclusion |
| --- | --- | --- | --- |

Every deliverable document is derived from completed project Markdown. A statement that appears in a deliverable and in no source record is a defect, not an improvement.

## 4. Generation Log

| Run | Date | Command | Documents produced | Workbooks produced | Warnings | Errors | Resolved |
| --- | --- | --- | --- | --- | --- | --- | --- |

## 5. Unresolved Content Report

| Document | Open `TBD (Q-###)` count | Blocking questions | Non-blocking deferrals | Empty tables | Disposition |
| --- | --- | --- | --- | --- | --- |

A `TBD (Q-###)` in a released package is acceptable only where it is non-blocking and has a recorded owner and disposition. Blocking unknowns keep the package in draft.

## 6. Export Verification

Verification means the exported file was opened and inspected, not that the generator exited successfully.

| Check | Result | Evidence | Findings |
| --- | --- | --- | --- |
| Every Word document opens and renders its headings, tables and layout blocks | TBD | TBD | TBD |
| Table of contents is present and correct after field update | TBD | TBD | TBD |
| No table is truncated or missing columns | TBD | TBD | TBD |
| ASCII layout blocks render in a monospaced style and stay aligned | TBD | TBD | TBD |
| Every embedded diagram appears, is legible at delivered size and is not clipped | TBD | TBD | TBD |
| Every diagram caption carries its DIAG ID and its notation or model-status statement | TBD | TBD | TBD |
| No diagram reference is broken and no export is stale against its source model | TBD | TBD | TBD |
| Every workbook opens and every declared sheet exists | TBD | TBD | TBD |
| Sheet headers, filters and frozen panes behave as intended | TBD | TBD | TBD |
| Identifiers match their Markdown source exactly | TBD | TBD | TBD |
| No template instruction text survives in a released document | TBD | TBD | TBD |
| Cross-document references resolve to real records | TBD | TBD | TBD |
| Document language is consistent across the package | TBD | TBD | TBD |

## 7. Consistency Checks Across Documents

| Check | Result | Findings |
| --- | --- | --- |
| The MVP definition is identical in the PRD and the SOW | TBD | TBD |
| Personas are identical in the PRD and the journey document | TBD | TBD |
| The RACI appears only in the Project Plan and is referenced elsewhere | TBD | TBD |
| Business objectives in the BRD match the approved BIZ register | TBD | TBD |
| Requirements in the SRS match the approved specification with no additions | TBD | TBD |
| Every story in the backlog traces to an approved requirement | TBD | TBD |
| Every scheduled card exists in the approved backlog | TBD | TBD |
| Success metrics agree between the PRD and the BRD | TBD | TBD |
| Out-of-scope lists agree across the PRD, SOW and specification | TBD | TBD |
| Diagrams agree with the process model, state transitions and data model they depict | TBD | TBD |
| No diagram shows a lane, gateway, table, column or relationship absent from a confirmed record | TBD | TBD |

## 8. Release Decision

| Item | Value |
| --- | --- |
| Package status | DRAFT / READY FOR REVIEW / RELEASED |
| Outstanding blockers | TBD |
| Known non-blocking weaknesses | TBD |
| Released to | TBD |
| Released on | TBD |
| Next scheduled regeneration trigger | TBD |

Regenerate the package whenever an approved source record changes. A stale export presented as current is a reporting failure, not a formatting detail.
