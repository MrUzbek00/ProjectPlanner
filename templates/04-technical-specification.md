# Project Technical Specification / Technical Assignment

TEMPLATE — DRAFT — NOT APPROVED

Stage 7. Generate the specification only after gates G2–G6 pass: discovery is sufficient, blocking questions are resolved or scoped out, requirements are reviewed, workflows and entities are modelled, and scope is defined. The specification **consolidates** the approved planning records — requirement registers, process and domain models, the solution structure, the scope register and the discovery registers. It introduces no requirement, rule, role, field or decision of its own; `tools/check_gates.py` fails gate G7 when it mentions an ID that no record defines. When writing it reveals a gap, record a question or finding and return to the stage the gap belongs to; never fill it in here.

Use one confirmed document language throughout the populated specification. Retain all 26 sections. Use sourced content, `TBD (Q-###)` in drafts, or `N/A — reason; evidence`. Repeat detail records for every applicable requirement, page, entity and integration. Normative linked files belong to the same approval manifest.

## 1. Project Information

### 1.1 Project Name

TBD

### 1.2 Client / Department

TBD

### 1.3 Document Version

| Version | Date | Author / editor | Changes | Source / decision references |
| --- | --- | --- | --- | --- |

### 1.4 Document Status

Status: DRAFT. Approved version: none. Approval evidence and complete revision manifest: TBD.

### 1.5 Authors / Stakeholders

| Name / stakeholder | Organization / department | Responsibility | Decision / approval authority | Source |
| --- | --- | --- | --- | --- |

Document language: TBD. Canonical glossary location: TBD. Source inventory: TBD.

## 2. Project Objective

Explain why the system is being built, which business processes it will automate, and the expected measurable improvement. Distinguish an unmeasured aspiration from an agreed target.

| BR ID | Business objective | Process automated | Measure / unit | Baseline | Target | Measurement window / method | Owner | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## 3. Project Overview

### 3.1 Current AS-IS Process

TBD — describe actual inputs, actors, systems/documents, handoffs and outputs; reference PROC IDs and sources.

### 3.2 Current Problems

| Problem | Evidence / observed impact | Affected process / actors | Related BR IDs |
| --- | --- | --- | --- |

### 3.3 Proposed TO-BE Solution

TBD — distinguish confirmed behavior from recommendations awaiting a decision.

### 3.4 Project Scope

| Included capability / process | Boundary / release | Related requirements | Confirmation |
| --- | --- | --- | --- |

### 3.5 Out of Scope

Restate the OUT OF SCOPE, FUTURE and PENDING DECISION entries of `specification/scope.md` (`templates/33`) with their IDs.

| OOS ID | Excluded or deferred item | Reason / consequence | Authorizing source / decision |
| --- | --- | --- | --- |

### 3.6 Assumptions

| ASM ID | Assumption | Impact if wrong | Confirmation question | Disposition |
| --- | --- | --- | --- | --- |

### 3.7 Dependencies

| Dependency | Department / system / owner | Required input / condition | Availability | Affected requirements | Risk / question |
| --- | --- | --- | --- | --- | --- |

## 4. Stakeholders and User Roles

For each actual role, define responsibility, module access, action permissions and record scope. Do not assume all staff have system accounts or that administrators can access all business data.

| Role ID / name | Responsibility | Accessible modules | Create permission | View permission | Edit permission | Delete permission | Approve / reject permission | Export permission | Administrative permission | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Role-permission matrix:

| Role | Module / page / entity / action | Create | View | Edit | Delete | Approve | Reject | Export | Admin | Record scope | Conditions / rules |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Values: Allowed, Denied, Conditional with defined condition, or TBD. Confirm server enforcement and UI visibility behavior where applicable.

## 5. User Scenarios

Repeat for every role's meaningful end-to-end scenarios, including applicable failure/alternative paths.

| SCN ID | Role | Trigger | User action | System response | Next step | Final result | Related FR / PROC / PAGE IDs |
| --- | --- | --- | --- | --- | --- | --- | --- |

## 6. System Modules

Create the actual module hierarchy; the workflow's authentication/dashboard/warehouse examples are not a mandatory module list.

| MOD ID | Module name | Parent module | Purpose | Roles | Processes / requirements | Pages |
| --- | --- | --- | --- | --- | --- | --- |

Page map / navigation:

| PAGE ID | Page name | Module | Navigation source | Related detail file | Allowed roles / access conditions |
| --- | --- | --- | --- | --- | --- |

## 7. Detailed Functional Requirements

Use `FR-###` or `FR-<MODULE>-###` IDs. The canonical entries are the record blocks in `specification/functional-requirements.md` ([template 26](26-requirement-register.md)); this section lists them by module for reading, with the same IDs and titles, and links each to its entry and any [requirement detail record](05-requirement-detail.md). Requirement detail is normative, not optional.

| FR ID | Module | Requirement summary | Actor | BR IDs | RULE IDs | Detail location | Source / decision | Acceptance IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Every FR detail must state: Requirement ID, Module, Requirement, Actor, Precondition, Trigger, System Behaviour, Business Rules, Validation Rules, Permissions, Success Result, Failure Result and Related Requirements. Include provenance and measurable acceptance links.

## 8. Page / Screen Specifications

Use a complete [page specification](06-page-specification.md) for EVERY applicable page. Update template links to actual project files before approval.

| PAGE ID | Page name | Purpose | Allowed roles | Navigation source | Related requirements | Complete specification location |
| --- | --- | --- | --- | --- | --- | --- |

Each page defines filters, search, sort, pagination, KPIs, charts, tables, buttons, forms, status indicators, permissions, exports, notifications, empty states, validation and error states. Define every table column, form field and action using the detailed template. An API-only capability may have no page when that is explicitly established.

## 9. Business Rules

`RULE-###` identifies rules; business requirements use `BR-###`. The canonical rule entries are in `specification/business-rules.md` ([template 26](26-requirement-register.md)); this table restates them for reading and must match.

| RULE ID | Rule category | Exact rule / formula / decision table | Inputs / source | Units / precision / rounding | Conditions / exceptions | Result / validation failure | Related FR / entity / state IDs | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Review applicability of calculations, status changes, approvals, deletion restrictions, dependencies, automatic values, data consistency, quantity calculations, thresholds and duplicate prevention. For applicable calculations define date basis, null/zero/negative handling, boundary cases and worked examples with expected results. Numerical values remain TBD until confirmed.

## 10. Workflow and Approval Rules

Process model reference: TBD. State dictionary reference: TBD. Record evidence if no approval workflow applies.

State transition table — repeat for every workflow:

| Workflow / entity | Initial status | Actor | Action | Preconditions / permission | Next status | Notification recipient | Rejection behaviour | Required comment | Required attachment | Audit entry | Data change / failure behavior | FR / RULE IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Define allowed and forbidden transitions, applicable terminal states, alternative paths and what happens when a request becomes stale. Diagrams must agree with this table.

## 11. Master Data

List actual reference datasets only. Users, roles, departments, product types, statuses, suppliers, customers, units, machines, models, shops, materials and categories are possible topics, not confirmed scope.

| Dataset / entity | Purpose | Fields / keys | Source / owner | Create / edit / deactivate permissions | Validation / duplicate prevention | Referenced by | Import / maintenance process | Lifecycle / deletion restrictions |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## 12. Dashboard Requirements

| KPI ID / name | Definition | Calculation formula | Data source / field IDs | Update frequency | Filter / date basis | User roles | Drill-down behaviour | Unit / precision / missing-data behavior | Acceptance example |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

| Chart ID / name | Chart type | X-axis | Y-axis | Grouping | Filter | Date range / time zone | Drill-down | Data / KPI source | Empty / error behavior |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Specify data visibility scope, refresh behavior, and reconciliation between a KPI, its drill-down and corresponding reports.

## 13. Reports and Exports

| Report ID / name | Source | Columns / types | Filters | Excel export | PDF export | Permissions / record scope | Sort / grouping / totals | Limits / file naming | Empty / error behavior |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Define whether export respects current filters, selection, pagination and visible columns. Confirm localization, date/number formatting and sensitive-field behavior. Do not assume every report supports both formats.

## 14. Notifications

| NOTIF ID | Trigger | Recipient / selection rule | Channel | Message / variable definitions | Link / access behavior | Read / unread behaviour | Delivery timing / failure handling | Related requirements |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Confirm what happens if a recipient is missing, cannot access the linked entity, or an external channel fails. Retry/deduplication behavior is specified only when applicable and confirmed.

## 15. Audit Logs

Review applicable events: created, edited, deleted, submitted, approved, rejected, assigned, reassigned, status changed, file uploaded and login events.

| Event | Trigger / entity | User | Role | Department | Action | Entity identifier | Old value | New value | Timestamp / time zone | Comment | Visibility / masking | Requirement IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Audit access, protection, retention, search/export and failure behavior: TBD. Confirm which fields apply to each event and how secrets/sensitive values are excluded or masked. Do not assume a retention period or legal obligation.

## 16. Integrations

Repeat for each integration. Explicitly label dependency on third-party API documentation, access, licensing or capabilities that have not been verified.

| Field | Specification |
| --- | --- |
| Integration ID / System | TBD |
| Purpose / related requirements | TBD |
| Direction | TBD |
| API availability / evidence / third-party dependency | TBD |
| Authentication | TBD |
| Data sent / field mapping | TBD |
| Data received / field mapping | TBD |
| Trigger | TBD |
| Frequency | TBD |
| Failure handling | TBD |
| Retry / stopping condition | TBD |
| Logging / sensitive-data handling | TBD |
| Ownership / support contact | TBD |
| Contract / API specification reference | TBD |
| Acceptance and negative scenarios | TBD |

Use [the API contract template](14-api-contract.md) where applicable. Mark unverified feasibility as an open dependency, not a promised capability.

## 17. File Management

| Context / entity | Allowed file types | Maximum size / count | Attachment requirements | Versioning | Upload permissions | Download permissions | Delete permissions | Preview behaviour | Validation / error behavior | Storage / retention |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Confirm applicable file naming, replacement, ownership, deleted-parent behavior, unauthorized access, failed upload and malicious-file handling. All limits and policies require evidence or explicit recommendation/decision status.

## 18. Non-Functional Requirements

Assign `NFR-###` and use measurable targets with test conditions. Capture actual constraints or reasoned N/A for every category; do not invent numeric values. The canonical entries are in `specification/non-functional-requirements.md` ([template 26](26-requirement-register.md)); this table restates them.

| NFR ID | Category | Required behavior / measurable target | Workload / environment / assumptions | Measurement / acceptance method | Owner | Evidence / status | Related BR / FR / TEST IDs |
| --- | --- | --- | --- | --- | --- | --- | --- |

Coverage topics:

- Security, including applicable sensitive data and threat considerations.
- Authentication and session behavior.
- Authorization and record/data scope.
- Performance under defined volume, concurrency and response conditions.
- Scalability and growth assumptions.
- Browser support and supported versions policy.
- Backup and tested restoration, including confirmed recovery objectives.
- Logging, access, redaction and operational diagnosis.
- Availability and maintenance expectations.
- Responsive design and supported devices; accessibility if applicable.
- Localization, languages, time zones, dates, numbers and units.
- Maintainability and handover requirements.
- Data retention, archival and deletion.

## 19. Technology Stack

Keep confirmed technologies and recommendations visibly separate. Technology selection must follow actual requirements and constraints.

| Layer | Confirmed technology / version constraint | Source / DEC ID | Recommended option if undecided | Recommendation rationale / tradeoffs | Decision needed |
| --- | --- | --- | --- | --- | --- |
| Frontend | TBD | TBD | TBD | TBD | TBD |
| Backend | TBD | TBD | TBD | TBD | TBD |
| Database | TBD | TBD | TBD | TBD | TBD |
| Infrastructure | TBD | TBD | TBD | TBD | TBD |
| Authentication | TBD | TBD | TBD | TBD | TBD |
| Storage | TBD | TBD | TBD | TBD | TBD |
| Deployment | TBD | TBD | TBD | TBD | TBD |
| Monitoring | TBD | TBD | TBD | TBD | TBD |

System architecture: TBD — confirmed boundaries, components, data flows, external systems and deployment assumptions, maintained in `specification/solution-structure.md` ([template 37](37-solution-structure.md)). Every significant architecture choice is an Architecture Decision Record in `architecture/ADR-###-*.md` ([template 28](28-architecture-decision-record.md)), registered in `architecture/architecture-register.md` ([template 27](27-architecture-register.md)); a confirmed technology above cites its accepted ADR, and a recommended one cites its proposed ADR or the DECISION REQUIRED concern. Restate each accepted ADR's constraints here with its ID; gate G7 warns about an accepted ADR the specification does not reference. The specification introduces no architecture decision of its own. Approved technical requirements use TR-### and link to BR/FR/NFR as appropriate.

## 20. Data Model

Distinguish business concepts, logical data requirements and approved physical design decisions. Do not invent database fields to make an ERD appear complete.

| Entity ID / name | Purpose | Important fields | Relationships | Ownership | Lifecycle | Source / requirement IDs |
| --- | --- | --- | --- | --- | --- | --- |

Field detail:

| Entity / field | Business definition | Data type | Required / nullable | Default / source | Validation / uniqueness | Sensitive? / access | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- |

Relationship detail:

| From entity | Relationship | To entity | Cardinality | Optionality | Ownership / deletion behavior | Evidence |
| --- | --- | --- | --- | --- | --- | --- |

ERD: TBD or reasoned N/A. Include Mermaid source when useful and confirmed. Lifecycle and deletion behavior must match the workflow and permission definitions.

## 21. Acceptance Criteria

| AC ID | Requirement IDs | Given | When | Then / And — measurable outcome | Test data / boundary | TEST IDs | Acceptance authority |
| --- | --- | --- | --- | --- | --- | --- | --- |

Include observable success, permission denial, validation, failure and side-effect outcomes as applicable. Avoid “works correctly,” “fast” or “user-friendly” without measurable definitions.

## 22. Testing Requirements

| Test type | Applicable scope / requirement IDs | Environment / data | Expected evidence | Responsibility | Entry / exit criteria | TEST references |
| --- | --- | --- | --- | --- | --- | --- |
| Functional testing | TBD | TBD | TBD | TBD | TBD | TBD |
| Permission testing | TBD | TBD | TBD | TBD | TBD | TBD |
| Validation testing | TBD | TBD | TBD | TBD | TBD | TBD |
| Workflow testing | TBD | TBD | TBD | TBD | TBD | TBD |
| Integration testing | TBD | TBD | TBD | TBD | TBD | TBD |
| Export testing | TBD | TBD | TBD | TBD | TBD | TBD |
| Negative testing | TBD | TBD | TBD | TBD | TBD | TBD |
| Acceptance testing / UAT | TBD | TBD | TBD | TBD | TBD | TBD |

Additional testing for confirmed NFRs: TBD. Detailed test definitions use [the acceptance-test template](11-acceptance-tests.md). Execution results remain NOT RUN until actual validation occurs.

## 23. Project Phases

| Phase | Objective | Inputs / dependencies | Expected deliverable | Exit criteria | Responsibility / capacity constraints |
| --- | --- | --- | --- | --- | --- |
| Discovery | TBD | TBD | TBD | TBD | TBD |
| System Design | TBD | TBD | TBD | TBD | TBD |
| UI/UX | TBD | TBD | TBD | TBD | TBD |
| Backend Development | TBD | TBD | TBD | TBD | TBD |
| Frontend Development | TBD | TBD | TBD | TBD | TBD |
| Integrations | TBD | TBD | TBD | TBD | TBD |
| Testing | TBD | TBD | TBD | TBD | TBD |
| UAT | TBD | TBD | TBD | TBD | TBD |
| Deployment | TBD | TBD | TBD | TBD | TBD |
| Training | TBD | TBD | TBD | TBD | TBD |
| Post-launch Support | TBD | TBD | TBD | TBD | TBD |

These categories may overlap or be N/A with evidence. After approval, the development roadmap adds actual cards and dependency order. No calendar commitment is made without known capacity.

## 24. Deliverables

| Deliverable | Required content / acceptance condition | Format / path | Owner | Delivery stage | Current status / evidence |
| --- | --- | --- | --- | --- | --- |
| Technical Specification | TBD | TBD | TBD | TBD | TBD |
| BPMN / Process Flow | TBD | TBD | TBD | TBD | TBD |
| ERD | TBD | TBD | TBD | TBD | TBD |
| System Architecture | TBD | TBD | TBD | TBD | TBD |
| Page Map | TBD | TBD | TBD | TBD | TBD |
| Role-Permission Matrix | TBD | TBD | TBD | TBD | TBD |
| API Specification | TBD | TBD | TBD | TBD | TBD |
| Test Cases | TBD | TBD | TBD | TBD | TBD |
| Deployment Documentation | TBD | TBD | TBD | TBD | TBD |
| User Guide | TBD | TBD | TBD | TBD | TBD |
| Project Development Cards | All requested fields, dependencies and requirement/test links | TBD | TBD | After specification approval | Pending — specification not approved |
| Implementation Roadmap | Dependency-ordered phases, deliverables and exit criteria | TBD | TBD | After specification approval | Pending — specification not approved |
| Traceability Matrix | Forward/reverse coverage | TBD | TBD | Progressive; final at handoff | TBD |
| Specification review, final planning review and gate report | Evidence-based checks, findings and remaining weaknesses | TBD | TBD | Pre-approval and final handoff | TBD |

Record reasoned N/A where a supporting artifact does not apply. Distinguish planned content from a completed deliverable.

## 25. Open Questions

| Q ID | Missing decision / question | Why it matters | Affected IDs | Blocking? | Owner | Status | Resolution / deferral authority |
| --- | --- | --- | --- | --- | --- | --- | --- |

Before approval, resolve major ambiguities or explicitly exclude the affected scope. Retain resolved decision history in the register; do not delete it to hide earlier uncertainty. The canonical register is `discovery/open-questions.md`; this section lists the questions relevant to the specification with the same IDs.

## 26. Risks and Dependencies

| Risk ID | Risk | Impact | Probability / basis | Mitigation | Owner | Dependencies / trigger | Status / affected requirements |
| --- | --- | --- | --- | --- | --- | --- | --- |

Dependency register reference: TBD. Outstanding external API availability and department/system inputs must be explicit.
