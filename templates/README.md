# Template Index

Copy templates into the per-project structure described in [projects/README.md](../projects/README.md) when the stage that needs them begins. Do not fill the shared originals as though they belonged to one project. Each template states the stage it belongs to and the gate that checks it; see [WORKFLOW.md](../WORKFLOW.md) sections 6–18.

## By stage

| Stage | Templates | Project files | Gate |
| --- | --- | --- | --- |
| 1 Project Intake | [00 Project State](00-project-state.md), [29 Project Intake](29-project-intake.md), [02 Registers](02-registers.md) | `project-state.md`, `discovery/project-intake.md`, `discovery/sources.md` | G1 |
| 2 Discovery | [01 Discovery](01-discovery.md), [30 Discovery Log](30-discovery-log.md), [02 Registers](02-registers.md) | `discovery/discovery.md`, `discovery-log.md`, `open-questions.md`, `assumptions.md`, `risks.md`, `decisions.md`, `dependencies.md` | G2 |
| 3 Requirement Analysis | [26 Requirement Register](26-requirement-register.md), [31 Requirement Quality Review](31-requirement-quality-review.md) | `specification/*-requirements.md`, `business-rules.md`, `reviews/requirement-quality-review.md` | G3 |
| 4 Process and Domain Analysis | [03 Process Model](03-process-model.md), [32 Domain Model](32-domain-model.md) | `specification/process-model.md`, `domain-model.md` | G4 |
| 5 Solution Planning and Scope | [37 Solution Structure](37-solution-structure.md), [33 Scope Register](33-scope-register.md) | `specification/solution-structure.md`, `scope.md` | G5 |
| 6 Architecture Governance | [27 Architecture Register](27-architecture-register.md), [28 ADR](28-architecture-decision-record.md), [38 Principles](38-architecture-principles.md), [39 Architecture Review](39-architecture-review.md), [40 Architecture README](40-architecture-readme.md) | `architecture/architecture-register.md`, `architecture/ADR-###-*.md`, `architecture/principles.md`, `architecture/README.md`, `reviews/architecture-review.md` | G6 |
| 7 Specification | [04 Technical Specification](04-technical-specification.md), [05 Requirement Detail](05-requirement-detail.md), [06 Page Specification](06-page-specification.md), [14 API Contract](14-api-contract.md) | `specification/technical-specification.md` and detail records | G7 |
| 8A Independent Specification Review | [12 Specification Review](12-specification-review.md) | `reviews/specification-review.md`, closed cycles in `reviews/history/` | GR |
| 8B Specification Resolution and Approval | [12 Specification Review](12-specification-review.md) (later cycles), [00 Project State](00-project-state.md) (approval record, review summary) | Resolved records; approval record | G8 |
| 9 Backlog Decomposition | [07 Epic and Feature](07-epic-feature.md), [08 Task Card](08-development-card.md), [11 Acceptance Tests](11-acceptance-tests.md) | `backlog/backlog.md`, `backlog/tasks/`, `quality/acceptance-tests.md` | G9 |
| 10A Dependency Mapping and Prioritisation | [09 Backlog and Roadmap](09-backlog-roadmap.md) (dependencies), [02 Registers](02-registers.md) (external dependencies) | `backlog/`, `discovery/dependencies.md` | G10 |
| 10B Backlog Readiness Validation | [08 Task Card](08-development-card.md) (Definition of Ready, readiness history), [09 Backlog and Roadmap](09-backlog-roadmap.md) | `backlog/readiness-report.md` (generated), task statuses | GB |
| 11 Roadmap and Project Plan | [09 Backlog and Roadmap](09-backlog-roadmap.md) (phases) | `backlog/backlog.md` | G11 |
| 12 Traceability Validation | [10 Traceability](10-traceability-matrix.md), [34 Final Planning Review](34-final-planning-review.md) | `traceability/traceability.md`, `reviews/final-planning-review.md` | G12 |
| 13 Final Planning Package | [36 Planning Summary](36-planning-summary.md), [16–23 deliverables](#deliverable-package), [24](24-bpmn-process-diagrams.md) and [25](25-er-data-diagrams.md) diagrams, [13 Handoff](13-handoff.md), [15 Delivery Documentation](15-delivery-documentation.md) | `deliverables/`, `diagrams/`, `delivery/handoff.md` | G13 |
| Any stage, once a baseline exists | [35 Change Record](35-change-request.md) | `changes/CHANGE-###.md`, `changes/baseline.json`; generated `changes/CHANGE-###-impact-report.md` | GC; re-run gates from the earliest affected stage |

## All templates

| Template | Purpose |
| --- | --- |
| [00 — Project State](00-project-state.md) | Identity, current stage, priority scheme, gate results, approval record, next action |
| [01 — Discovery](01-discovery.md) | Seven-part initial analysis, gap matrix, conflicts and questions |
| [02 — Registers](02-registers.md) | Sources, open questions, assumptions, risks, decision log, external dependencies, stakeholders, glossary, recommendations |
| [03 — Process Model](03-process-model.md) | AS-IS and TO-BE process records, permissions, states and transitions |
| [04 — Technical Specification](04-technical-specification.md) | The 26-section specification, consolidated from the records |
| [05 — Requirement Detail](05-requirement-detail.md) | Detailed behaviour, validation and failure handling for one FR |
| [06 — Page Specification](06-page-specification.md) | Page, table, form and action contracts |
| [07 — Epic and Feature](07-epic-feature.md) | Backlog hierarchy with scope, modules, dependencies and the ADRs each feature relies on |
| [08 — Task Card](08-development-card.md) | One outcome-oriented task, its constraints and the Definition of Ready |
| [09 — Backlog and Roadmap](09-backlog-roadmap.md) | Index, dependency edges, phases, honest dates |
| [10 — Traceability](10-traceability-matrix.md) | Reviewed coverage from goal to test |
| [11 — Acceptance Tests](11-acceptance-tests.md) | Test definitions; execution is recorded only when it happens |
| [12 — Specification Review](12-specification-review.md) | Stage 8A independent review by a reviewer who is not the author: checklist by review area, twelve review questions, evidenced REVIEW-### findings with severity, category, status and resolution, review cycles and their history |
| [13 — Handoff](13-handoff.md) | Final planning handoff across all three layers |
| [14 — API Contract](14-api-contract.md) | Request, response, error and retry definitions for required interfaces |
| [15 — Delivery Documentation](15-delivery-documentation.md) | Deployment, user-guide, training and support requirements |
| [26 — Requirement Register](26-requirement-register.md) | GOAL, BR, RULE, FR, NFR, DR, IR, SR, UXR and TR record blocks |
| [27 — Architecture Register](27-architecture-register.md) | Ledger of every ADR ID and the coverage of the twenty standard architecture concerns |
| [28 — Architecture Decision Record](28-architecture-decision-record.md) | One significant architecture decision: lifecycle, alternatives, consequences, constraints, links; with a complete example |
| [29 — Project Intake](29-project-intake.md) | The fourteen intake items, classified |
| [30 — Discovery Log](30-discovery-log.md) | Coverage of the fourteen discovery categories |
| [31 — Requirement Quality Review](31-requirement-quality-review.md) | Stage 3 review of the requirements |
| [32 — Domain Model](32-domain-model.md) | Business entities, attributes, relationships, lifecycles |
| [33 — Scope Register](33-scope-register.md) | IN SCOPE, OUT OF SCOPE, FUTURE, PENDING DECISION |
| [34 — Final Planning Review](34-final-planning-review.md) | Stage 12 project-level review |
| [35 — Change Record](35-change-request.md) | One change: type, lifecycle, previous and new state, reason, affected artifacts with review states, required reviews, risk, roadmap, new-work and document impact |
| [36 — Planning Summary](36-planning-summary.md) | The fifteen questions every plan answers |
| [37 — Solution Structure](37-solution-structure.md) | Classified module register, security boundaries, data ownership |
| [38 — Architecture Principles](38-architecture-principles.md) | The few principles that guide architecture decisions |
| [39 — Architecture Review](39-architecture-review.md) | Stage 6 review: counts, reviewed decisions, checklist, architecture conflicts and their resolution |
| [40 — Architecture README](40-architecture-readme.md) | Orientation for a project's `architecture/` folder |

## Deliverable package

Stakeholder documents authored in stage 13, after gate G12, and exported to Word and Excel. See [WORKFLOW.md](../WORKFLOW.md) section 22 and [tools/README.md](../tools/README.md).

| Template | Audience | Purpose |
| --- | --- | --- |
| [16 — PRD](16-prd.md) | Product, business, delivery | Product intent, personas, success metrics, MVP feature set, release criteria |
| [17 — BRD](17-brd.md) | Sponsors and stakeholders | Business case, objectives, justification, financial expectations, governance |
| [18 — SRS](18-srs.md) | Engineering | Architecture, data, interfaces, functional and non-functional behaviour, security, APIs |
| [19 — SOW and Scope Statement](19-sow-scope-statement.md) | Contracting and delivery | Deliverables, boundaries, MVP definition, milestones, acceptance, change control |
| [20 — User Journey and User Stories](20-user-journey-stories.md) | Product and delivery | Journeys, pain points, epics, story backlog, acceptance criteria |
| [21 — Wireframes and UI/UX](21-wireframes-uiux.md) | Design and frontend | Information architecture, screen layouts, states, interactions, asset handoff |
| [22 — Project Plan and Roadmap](22-project-plan-roadmap.md) | Delivery management | Phases, milestones, sprints, task sequence, dependencies, resources, RACI |
| [23 — Deliverable Package Manifest](23-deliverable-package.md) | Package governance | Contents, source coverage, generation log, export verification, release decision |
| [24 — BPMN Process Diagrams](24-bpmn-process-diagrams.md) | Business and engineering | BPMN notation contract, per-diagram specification, verification |
| [25 — ER and Data Diagrams](25-er-data-diagrams.md) | Engineering and data | Proposed physical data model, state and data-flow diagrams, verification |

Tables tagged with `<!-- xlsx: workbook=<key>; sheet=<name> -->` are also written to the Excel workbooks. Keep the marker directly above its table when copying a template.

## Machine-read structure

The tools read structure, never prose. Keep these exactly as the templates show them:

- **Record blocks** — a heading that begins with the ID (`### FR-014 — Title`), a `| Field | Value |` table, and bold or heading section labels. Used for requirements, processes, entities, ADRs, epics, features, phases, tasks and tests.
- **Register tables** — a table whose first column header names the ID (`Question ID`, `Decision ID`, `Risk ID`, `Dependency ID`, `ASM ID`, `Source ID`, `MOD ID`, `PRIN ID`, `ADR ID`, `Scope ID`). Rows whose first cell is not a valid ID are ignored.
- **Stage tables** — `Intake item` (29), `Category` (30), `Concern` (27), `Check` and `Finding ID` (reviews 31, 34, 39 and the manifest 23), `Area`, `Review question`, `Candidate` and `Cycle` in the specification review (12), whose findings are `REVIEW-###` record blocks, `ADR ID` in the architecture review (39), and the *Current stage*, *Priority scheme* and gate rows of `project-state.md` (00).

## Completion rules

- A template is not a completed record. A copied template stays a template until populated and reviewed, and its placeholders fail the gates that read it.
- Populate every applicable field with evidence. Use a tracked `Q-###` for a missing decision and a reason plus evidence for N/A.
- Keep one canonical definition; link to it elsewhere. A requirement, rule or decision that exists only in the specification or a deliverable is a defect.
- Do not create backlog records before gates GR and G8, or deliverables before gate G12.
- Do not mark an ADR Accepted without its named decision owner and approval evidence; do not edit an accepted ADR to change direction — supersede it.
- Generated reports, maps, exports, builds and the machine handoff are output. Edit the records and regenerate.
- Specify a diagram before generating it, and verify it by looking at the rendered image.
- Project facts, language, scope and technologies come from the project's own discovery, never from these blank templates.
