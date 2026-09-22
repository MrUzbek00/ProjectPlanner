# Template Index

Copy templates into the per-project structure described in [projects/README.md](../projects/README.md). Do not rename or fill the shared originals as though they belonged to one business project. Replace template-to-template links with links to the actual populated project records.

| Template | When used | Purpose |
| --- | --- | --- |
| [00 — Project State](00-project-state.md) | Start and every resume/update | Project model, artifact index, gates, approval manifest and next action |
| [01 — Discovery](01-discovery.md) | Before final specification | Seven-part initial analysis, full gap coverage, conflicts, questions and interview updates |
| [02 — Registers](02-registers.md) | Throughout | Sources, BIZ/FR/BR indexes, stakeholders, glossary, decisions, assumptions, recommendations, exclusions, risks and changes |
| [03 — Process Model](03-process-model.md) | Discovery/design | AS-IS/TO-BE, main/alternative/rejection/failure paths, roles, permissions, states, entities and diagram requirements |
| [04 — Technical Specification](04-technical-specification.md) | Draft progressively; approve after gaps resolved | Central document with all 26 required sections |
| [05 — Requirement Detail](05-requirement-detail.md) | Once a requirement can be specified | Complete record per FR with validations, errors and acceptance links |
| [06 — Page Specification](06-page-specification.md) | Once screens are identified | Complete page/table/form/action contracts |
| [07 — Epic and Feature](07-epic-feature.md) | After specification approval | Backlog hierarchy and container outcomes |
| [08 — Development Card](08-development-card.md) | After specification approval | Every requested field for each executable task/subtask |
| [09 — Backlog and Roadmap](09-backlog-roadmap.md) | After specification approval | Index, complexity, dependency edges, phase sequencing and execution readiness |
| [10 — Traceability](10-traceability-matrix.md) | Throughout; cards pending before approval | Forward/reverse BIZ → FR → module/page → card → acceptance-test coverage, plus NFR/TR coverage |
| [11 — Acceptance Tests](11-acceptance-tests.md) | During specification | Measurable criteria, functional/permission/validation/workflow/integration/export/negative/UAT test definitions |
| [12 — Quality Report](12-quality-report.md) | Before approval and at final handoff | Evidence-based checks, contradictions, remaining weaknesses and readiness conclusion |
| [13 — Handoff](13-handoff.md) | Final planning handoff | Connected deliverables, baseline approval, readiness, prerequisites and export mapping |
| [14 — API Contract](14-api-contract.md) | For actual required interfaces | Request/response/error/authentication/data/retry/verification definitions |
| [15 — Delivery Documentation](15-delivery-documentation.md) | Requirements during planning; instructions when implemented | Deployment, user-guide, training and support content/ownership/stages |

## Deliverable package templates

Used after the analysis records are complete, to author the stakeholder-facing documents that are exported to Word and Excel. See [WORKFLOW.md](../WORKFLOW.md) section 12 and [tools/README.md](../tools/README.md).

| Template | Audience | Purpose |
| --- | --- | --- |
| [16 — PRD](16-prd.md) | Product, business, delivery | Product intent, personas, success metrics, MVP feature set, release criteria |
| [17 — BRD](17-brd.md) | Sponsors and stakeholders | Business case, objectives, justification, financial expectations, governance |
| [18 — SRS](18-srs.md) | Engineering | Architecture, data, interfaces, functional and non-functional behavior, security, APIs |
| [19 — SOW and Scope Statement](19-sow-scope-statement.md) | Contracting and delivery | Deliverables, boundaries, MVP definition, milestones, acceptance, change control |
| [20 — User Journey and User Stories](20-user-journey-stories.md) | Product and delivery | Journeys, pain points, epics, story backlog, acceptance criteria |
| [21 — Wireframes and UI/UX](21-wireframes-uiux.md) | Design and frontend | Information architecture, screen layouts, states, interactions, asset handoff |
| [22 — Project Plan and Roadmap](22-project-plan-roadmap.md) | Delivery management | Phases, milestones, sprints, task sequence, dependencies, resources, RACI |
| [23 — Deliverable Package Manifest](23-deliverable-package.md) | Package governance | Contents, source coverage, generation log, export verification, release decision |
| [24 — BPMN Process Diagrams](24-bpmn-process-diagrams.md) | Business and engineering | BPMN notation contract, per-diagram specification, generation record and verification |
| [25 — ER and Data Diagrams](25-er-data-diagrams.md) | Engineering and data | Proposed physical data model, state and data-flow diagrams, structural proposals, verification |

Tables tagged with `<!-- xlsx: workbook=<key>; sheet=<name> -->` are also written to the Excel workbooks. Keep the marker directly above its table when copying a template.

Diagrams are generated with the Excalidraw and draw.io skills named in templates 24 and 25, specified before they are drawn, and embedded in the Word deliverables with captioned image references.

## Completion rules

- A template is not a completed deliverable. Empty tables and TBD entries are intentional only in templates and appropriate drafts.
- Populate every applicable field with evidence-backed content. Use a tracked Q ID for missing decisions and a reason plus evidence for N/A.
- Keep one canonical definition; use stable links elsewhere. Linked requirement/page/model records are part of the specification approval manifest.
- Repeat records per actual process, role, requirement, page, table, form, action, integration, entity and card.
- Do not create executable business project cards before specification approval. Blank reusable card templates do not constitute project cards.
- Do not author a deliverable document before the analysis records it restates are complete. A deliverable adds no requirement of its own; content that exists only there is a defect.
- Generated Word and Excel files are output. Edit the Markdown and rebuild; never hand-edit an export and treat it as the source.
- Specify a diagram before generating it, and verify it by looking at the rendered image. A diagram shows only what a confirmed record states.
- Preserve source statements and decisions. A recommendation is not a confirmed requirement until accepted.
- Project facts, language, scope and technologies come from project discovery, not from these blank templates.
