# Operating Workflow

## 1. What this workflow produces

Work proceeds in two connected layers.

The analysis layer is the working record: a versioned Technical Specification / Technical Assignment and a connected set of Development Cards, supported by process flows, an ERD, architecture, a page map, a role-permission matrix, API contracts where applicable, acceptance test definitions, a dependency-based roadmap, a traceability matrix and a Specification Quality Report. These are Markdown and remain the single source of truth.

The deliverable layer is the stakeholder-facing package, generated from the completed analysis layer once the project information is gathered and the specification is approved. It contains seven documents plus its own manifest:

| Deliverable | Template | Answers |
| --- | --- | --- |
| Product Requirements Document (PRD) | `templates/16-prd.md` | What the product does, for whom, which features are in the MVP, how success is measured |
| Business Requirements Document (BRD) | `templates/17-brd.md` | Why the organization is funding this, the business objectives, the justification and the financial expectations |
| Software Requirements Specification (SRS) | `templates/18-srs.md` | System architecture, data model, interfaces, functional and non-functional behavior, security rules and APIs |
| Statement of Work and Scope Statement (SOW) | `templates/19-sow-scope-statement.md` | Deliverables, boundaries, the strict MVP set, milestones, acceptance and change control |
| User Journey and User Stories | `templates/20-user-journey-stories.md` | End-to-end journeys, pain points, epics, the story backlog and acceptance criteria |
| Wireframes and UI/UX Design Specification | `templates/21-wireframes-uiux.md` | Information architecture, screen layouts, component states, interactions and asset handoff |
| Project Plan and Roadmap | `templates/22-project-plan-roadmap.md` | Phases, milestones, sprints, task sequence, dependencies, resources and RACI |
| Deliverable Package Manifest | `templates/23-deliverable-package.md` | What was generated from which source, the generation log and the export verification |

The package also carries generated diagrams: BPMN process diagrams and an entity-relationship model of the proposed database, specified in `templates/24-bpmn-process-diagrams.md` and `templates/25-er-data-diagrams.md`.

Diagrams are generated as described in section 11. Each deliverable is authored as Markdown and exported to Word with its diagrams embedded, and the wide registers are also exported to Excel, as described in section 12.

Deployment documentation, user guides and test execution evidence may require an implemented system. Establish their required content and delivery owner during planning; never label a placeholder as completed implementation evidence.

## 2. Start and resume

1. Read this document and `AGENTS.md`.
2. For a new project, create a distinct folder under `projects/`. Copy only the templates needed for the current stage. Do not create completed-looking business content from examples.
3. Preserve or reference original inputs in `sources/`. Record filenames, versions, authors if known, locations and source authority. For screenshots/forms, record visible fields and unreadable areas without guessing.
4. Create `project-state.md` from the state template. Start with project identity and business scope as TBD if unknown.
5. On resume, read state, source register, decisions, current discovery round and latest quality findings. Verify which revision is approved before doing dependent work.
6. After each round or material change, update the state and affected records together.

## 3. Evidence and classification

| Classification | Meaning | How it changes |
| --- | --- | --- |
| Confirmed requirement | Explicit requirement supported by an attributable authoritative source or user answer, with no unresolved conflict | Change only through recorded decisions; assess impact on approved scope |
| Assumption | Provisional interpretation without sufficient confirmation | Confirm, reject or replace through a decision; never silently promote |
| Recommendation | Analyst proposal with rationale and tradeoffs | Becomes scope only if accepted |
| Open question | Missing or conflicting decision with an owner and consequence | Resolve with an answer and update every affected artifact |
| Out of scope | Explicitly excluded or deferred item with reason and authority | Reintroduce through scope change control |

`TBD (Q-###)` means unknown. `N/A — reason; SRC/DEC reference` means non-applicability is established. Neither a blank field nor an illustrative example is evidence. Do not assign an unconfirmed person as decision owner: write `TBD (Q-###)`.

Keep an original statement and a normalized interpretation when wording matters. Record contradictions as competing statements with both source locations. Consolidate duplicates only when their meaning, permissions, conditions and outcomes match; retain all source links and retired-ID aliases.

## 4. Identifiers and terminology

IDs are unique within a project, stable after assignment, and never reused. The patterns below define namespaces, not actual project records.

| Pattern | Record |
| --- | --- |
| SRC-001 / DEC-001 / Q-001 | Source / decision / question or gap |
| ASM-001 / REC-001 / OOS-001 / RISK-001 | Assumption / recommendation / exclusion / risk |
| BIZ-001 | Business requirement or measurable business objective |
| FR-AUTH-001, FR-<MODULE>-001 | Functional requirement; use actual confirmed module codes |
| BR-001 | Business rule (distinct from BIZ) |
| NFR-001 / TR-001 | Non-functional requirement / approved technical requirement |
| ROLE-001 / MOD-001 / PAGE-001 / ENT-001 | Role / module / page / entity |
| PROC-001 / STATE-001 / SCN-001 | Process / entity-scoped state / scenario |
| KPI-001 / REPORT-001 / NOTIF-001 / INT-001 / API-001 | KPI / report / notification / integration / API contract |
| AC-001 / AT-001 | Acceptance criterion / acceptance test definition |
| EPIC-01 / FEAT-01-01 / <AREA>-001 / <AREA>-001-S01 | Epic / feature / task / optional subtask |
| PHASE-01 / FIND-001 / CR-001 | Roadmap phase / quality finding / change request |

Use the confirmed domain glossary. Define units, time zones, business dates and synonyms before using them in formulas or filters. Clarify terms such as “approved,” “confirmed,” and “completed” if their meanings differ by entity.

## 5. Discovery and requirement gap analysis

Produce the seven-part initial analysis using `templates/01-discovery.md`. Include the gap matrix even when all business details are unknown. The first business interview can begin with: the project/department; one real current process from trigger to outcome; its problems; and the desired measurable change. Ask only unanswered questions from that set.

Run approximately 3–5 focused questions per round, fewer when possible. For each, state the missing decision, why it matters, and an example answer format when helpful. Do not request another interview if source evidence already answers a question. Separate a suggested design from a request for factual clarification.

| Round | Investigate only unanswered areas | Update |
| --- | --- | --- |
| 1 — Business Process | Project/client, objective, AS-IS, problems, TO-BE, scope boundaries, success measures | Understanding, BIZ register, processes, scope, glossary |
| 2 — Users and Permissions | Stakeholders, actual roles, ownership, module/action/record scope, delegation, create/view/edit/delete/approve/export/admin | Stakeholders, roles and permission matrix |
| 3 — Modules and Data | Entities, lifecycle, master data, business documents, pages, tables/forms/actions, uploads, statuses, validation, search/filter/sort/pagination, import/export | Module/page/entity records and FR/BR register |
| 4 — Approval Workflows | Whether approvals exist; actor/sequence, prerequisites, rejection/resubmission, cancellation, comments, attachments, notifications, concurrent actions, audit | Process models and state transition tables |
| 5 — Integrations | Systems and owners, API evidence/access, direction, authentication, payloads, triggers/frequency, failures/retries/logging, dependencies | Integration contracts and risks |
| 6 — Reports and Dashboards | Decisions supported, KPI definitions/formulas/units, source/date basis, chart axes/grouping, filters, refresh, drill-down, export/visibility | KPI, report and notification requirements |
| 7 — Technical Constraints | Confirmed/recommended stack, security/auth, volume/load, performance, availability, browsers/devices, localization, backup/restore, storage, retention, maintainability | Measurable NFRs, architecture constraints and risks |
| 8 — Acceptance and Deployment | UAT authority/scenarios, test data, rollout/migration, environments, training/support, deliverable formats, tracker destination, team capacity | Acceptance/test plan, delivery responsibilities, roadmap constraints |

The round order is adaptable to dependencies. Mark a topic complete only when answered, or non-applicable with evidence. At the end of each round:

1. Record answers verbatim or with a faithful summary and source reference.
2. List newly confirmed facts, rejected assumptions, accepted/rejected recommendations and remaining gaps.
3. Update requirements, processes, glossary and affected specification draft sections.
4. Explain any conflict or impact on an earlier decision.
5. Save the next focused questions and the current stage.

## 6. Business process model

Use `templates/03-process-model.md` for every major confirmed process, keeping AS-IS and TO-BE distinct. Include trigger, actors, preconditions, main/alternative flows, approvals, rejection, state changes, notifications, modified data, output, failures and audit.

State names are entity-scoped. Define every state and permitted transition. Each transition identifies actor, permission, guard conditions, side effects, failure behavior, notification and audit requirements. Ask whether cancellation, resubmission, delegation or concurrent changes apply; do not automatically add them.

Use Mermaid inside the working records for a quick view of a confirmed flow, approval path, state transition, entity relationship or architecture while the model is still being built. Unknown edges are explained as open questions outside the confirmed flow. A diagram must not introduce an unconfirmed field, relationship or step. Record logical entities first; distinguish approved implementation decisions from business data requirements.

The delivered diagrams are generated separately once the model is confirmed — BPMN process diagrams and the proposed data model — as described in section 11. A Mermaid sketch in a working record is a thinking aid; it is not the deliverable diagram and does not substitute for one.

## 7. Specification drafting and approval

Use all 26 sections of `templates/04-technical-specification.md`. Repeat the detailed requirement and screen records as needed using `templates/05-requirement-detail.md` and `templates/06-page-specification.md`. Related detail files are normative parts of the specification and must appear in its revision manifest.

Retain a section with an evidence-based N/A explanation when it does not apply. Every applicable field needs confirmed content, a reasoned N/A, or a tracked TBD while in draft. No numerical target, policy, permission or integration promise is inferred from convention.

Run the specification review in `templates/12-quality-report.md` before requesting approval. Cards are pending at this stage; lack of cards is not a pre-approval specification defect. Missing requirements, undefined behavior and unresolved major decisions are defects.

An ambiguity is blocking if it can change scope, access, calculations, state transitions, data ownership/schema, integration behavior, security, acceptance outcomes, or the ability to implement affected work without reinterpretation. A lower-impact editorial gap can remain only with an explicit deferral, owner and disposition. Do not use an “accepted risk” label to hide a blocking requirement.

Present the full specification, revision manifest, quality report, decisions and explicit exclusions. Request user approval only when the result is concrete and reviewable. Record the actual approval statement, approver, date, version and covered files. User approval is required here because the supplied workflow explicitly says: “After the Technical Specification is approved, convert it into executable Project Cards.”

## 8. Development cards

After approval, create epic/feature containers with `templates/07-epic-feature.md` and executable work with `templates/08-development-card.md`. Maintain the index and dependency map in `templates/09-backlog-roadmap.md`.

Split by a coherent, verifiable outcome: a list page, a detail view, a state transition, a calculation, an integration exchange, or a cross-cutting requirement. Combine tightly coupled UI/backend/data changes if needed for a complete outcome; avoid imposing a generic database-first sequence. Decompose L/XL work when it cannot be implemented and tested as one bounded task.

Each executable card must contain every requested card field, precise input/output and failure behavior, approved requirement links and measurable acceptance criteria. Use reasoned N/A for an irrelevant UI/backend/database/API section. Do not defer design decisions that affect implementation into “developer to decide.” Record an approved technical choice or open a question.

Technical enablers require an approved TR or NFR tied to the business objective or another approved requirement. If decomposition reveals a new requirement or unresolved design decision, handle it through change control before marking affected cards ready.

### Card status and dependency semantics

These are planning/backlog statuses, not statuses for the business application's entities.

| Status | Meaning |
| --- | --- |
| DRAFT | Card is being specified and has not passed readiness review |
| BLOCKED | Missing decision, external prerequisite, or unfinished required card prevents execution |
| READY | Scope is approved, details are complete, and execution prerequisites are satisfied |
| IN_PROGRESS | An authorized implementation task has started; planning does not set this speculatively |
| DONE | Implementation and required validation evidence satisfy Definition of Done |
| DEFERRED | Explicitly excluded from the current release with a decision reference |

Separately record `Definition completeness: COMPLETE / INCOMPLETE`. A complete future card can remain BLOCKED solely on predecessor completion and still belong in an implementation-ready backlog. No final-release card may be INCOMPLETE.

`Blocked By` lists predecessor task IDs. `Blocking Cards` is its derived reverse relationship: successor tasks this card blocks. `Dependencies` explains those edges plus external/document prerequisites. An epic/feature parent is hierarchy, not automatically an execution dependency. Planning dates do not mark dependencies done.

## 9. Roadmap and traceability

Schedule executable leaf tasks in a topological order of their real dependencies. Detect missing references, self-dependencies and cycles. Explain and resolve cycles; do not simply choose an arbitrary order. Independent work may share a phase. A prerequisite in the same phase needs an explicit internal sequence; it cannot be assumed complete at phase entry.

For every roadmap phase, supply objective, cards, dependencies, expected deliverable and exit criteria. Cover applicable Discovery, System Design, UI/UX, Backend, Frontend, Integrations, Testing, UAT, Deployment, Training and Post-launch Support stages. These are planning categories, not a mandatory waterfall. Already-completed planning stages link to evidence instead of fabricated implementation cards.

Use XS/S/M/L/XL complexity with stated drivers. Capacity is unknown until confirmed; do not convert complexity to dates by assumption. Priority is proposed with rationale until the user confirms it.

Use `templates/10-traceability-matrix.md` for forward and reverse coverage. Before approval: BIZ → FR → module/page → AC/AT, with cards marked pending. At handoff: add actual card IDs. Non-UI requirements use an explicitly explained N/A page, not a fabricated screen. Track NFR/TR coverage separately and link it into the same acceptance/card graph.

## 10. Acceptance and quality review

Use `templates/11-acceptance-tests.md` for executable test definitions. Distinguish tests defined from tests executed. Planning can establish coverage; it cannot prove that an unbuilt system passes.

Review requirements, role permissions, statuses, approval/rejection paths, validation, failure behavior, calculations, data consistency, audit, integration contracts, dependencies, security and destructive-action confirmation decisions. Check for duplicate/conflicting requirements, uncovered scope and orphan cards. Check generated documents for broken links and placeholder residue appropriate to their stage.

Report PASS / FAIL / N/A with evidence and concrete findings. If a review was not performed, mark NOT REVIEWED. Use a pre-approval specification review and a final combined specification/backlog review. A blank checklist is not a pass.

## 11. Diagram generation

Once the process model and data model are confirmed, generate the project's diagrams before authoring the deliverables that embed them. A diagram is a view of a confirmed model. It shows what the model states and nothing else; a lane, gateway, table, column or relationship that appears only in a picture is an invented requirement.

### Tools

| Diagram | Tool | Output | Specification |
| --- | --- | --- | --- |
| BPMN process diagrams, AS-IS and TO-BE | Excalidraw diagram skill — [coleam00/excalidraw-diagram-skill](https://github.com/coleam00/excalidraw-diagram-skill) | `.excalidraw` source plus a rendered PNG | `templates/24-bpmn-process-diagrams.md` |
| Entity-relationship model of the proposed database, entity state diagrams, data flows | draw.io diagram skill — [Agents365-ai/drawio-skill](https://github.com/Agents365-ai/drawio-skill) | `.drawio` source plus an exported PNG or SVG | `templates/25-er-data-diagrams.md` |

Both skills are provisioned by the workflow's own installer, so a new user does not have to find or configure them:

```bash
python tools/setup_workflow.py --check     # report readiness, change nothing
python tools/setup_workflow.py             # install what is missing
```

It clones each skill, locates the skill directory inside the repository — one of them publishes its skill under `skills/<name>/` rather than at the root — installs it where the assistant will discover it, installs the document-builder packages, and prepares the Excalidraw render pipeline with `uv` when present and a virtual environment otherwise. It is safe to re-run and leaves alone any skill another installation already provides.

The report also covers the optional pieces and how to get them: the draw.io desktop CLI for PNG, SVG and PDF export, and Graphviz for automatic layout. Without the draw.io CLI, diagrams are still authored as editable `.drawio` files; only image export is unavailable.

It finishes with a render smoke test. The Excalidraw render page imports its library from `esm.sh` at render time, so a restricted network breaks diagram verification with no obvious symptom — the smoke test surfaces that at setup instead of mid-project.

Where a skill is unavailable, say so and stop rather than hand-drawing a substitute and presenting it as generated output.

Both tools draw whatever they are told to draw. Neither enforces notation or checks a claim against a source record — that is this workflow's job, and it is done by completing the diagram specification before generating anything.

### Specify before drawing

Complete the diagram record in `templates/24` or `templates/25` first: participants, flow elements, gateway conditions, message flows, end events, or tables, columns, keys, relationships and states. Each row names the confirmed record it comes from. Generating a diagram from an incomplete specification produces a picture that has to be argued about instead of reviewed.

Draw AS-IS and TO-BE as separate diagrams. Never overlay a proposed change on an observed process.

### Accuracy rules

- Every element traces to a confirmed record. Unknown behavior is drawn as an annotation naming its open question, outside the confirmed flow — never as a guessed gateway, relationship or constraint.
- Rejection, cancellation, delegation and failure paths appear where the model confirms them and are absent where it does not.
- Lane names match confirmed `ROLE-###` records; data objects and tables match confirmed `ENT-###` records; states match the entity-scoped `STATE-###` transitions exactly.
- The ER diagram shows a **proposed physical model** derived from confirmed logical entities. Surrogate keys, join tables, audit columns, indexes and denormalization are design proposals and are listed as such in the record.
- Optionality, cardinality and delete behavior that the business has not confirmed stay `TBD (Q-###)`. Do not pick a constraint to make the picture look finished.

### Label the artifact honestly

An Excalidraw drawing in BPMN notation is a notation-conformant process diagram, not a BPMN 2.0 XML interchange file, and it will not run in a BPMN engine. Carry that statement in the caption. If an executable or interchangeable BPMN file is genuinely required, record it as a separate confirmed requirement with an owner and a tool decision. The same applies to the data model: the caption states that it is a proposed physical model pending implementation acceptance.

### Verify

Render every diagram, open the image, and look at it. The Excalidraw skill's render-view-fix loop is mandatory and typically takes several iterations; record how many were run. Then complete the verification checks in the diagram template — both the visual checks and the tracing checks. A diagram that was generated but never viewed is unverified, and a diagram that renders cleanly can still assert something no record supports.

### Store and embed

Keep sources and exports in `projects/<project>/deliverables/diagrams/`. Embed an export in a deliverable with a captioned image reference relative to the Markdown file:

```markdown
![DIAG-001 — Purchase approval, TO-BE. Drawn in BPMN 2.0 notation; not a BPMN 2.0 XML interchange file.](diagrams/diag-001-purchase-approval-tobe.png)
```

The build tool embeds the image, scales it to the text column and renders the caption beneath it. A missing image file is a build error, not a silent gap. Keep the DIAG ID first in every caption so a reader can find the specification behind the picture.

Regenerate a diagram whenever its source model changes, and rebuild the documents that embed it. A stale picture contradicting a current requirement is worse than no picture.

## 12. Deliverable document package

Once the project information is gathered and the analysis layer is complete — discovery closed, process model built, specification approved, cards and roadmap in place — generate the seven-document package and its manifest. This stage restates approved content for its audiences and adds nothing.

### Preconditions

Do not start this stage until G1 through G5 are met — the diagrams the deliverables embed are generated and verified before the documents that carry them are written. A package built on an unapproved specification is a draft of a draft; it hides which parts are decided. If the user asks for the package earlier, produce it from what is approved, mark every unresolved area as `TBD (Q-###)`, and state plainly in the manifest which gates are still open.

### Authoring rules

Author each deliverable as Markdown in `projects/<project>/deliverables/` from `templates/16` through `templates/23`. Every statement traces to an approved record. A sentence that appears in a deliverable and in no source record is a defect; raise it as `CR-###` rather than writing it in.

Each document carries exactly one canonical version of any shared content, and the others reference it:

| Content | Canonical location | Referenced from |
| --- | --- | --- |
| MVP feature set | PRD section 6.1, restated identically in SOW section 5 | Roadmap, story map |
| Personas | PRD section 4 | User Journey document |
| Business objectives and KPIs | BRD section 5 | PRD success metrics |
| Requirement behavior | SRS section 6 | PRD features, user stories |
| Screen detail | Wireframes document | SRS section 5.1, PRD section 8 |
| RACI | Project Plan section 4 | SOW section 10, BRD governance |
| Deliverables and acceptance | SOW section 6 | Project Plan milestones |
| BPMN process diagrams | Diagram record, `templates/24` | SRS process sections, PRD key flows, User Journey document |
| Data model and state diagrams | Diagram record, `templates/25` | SRS data requirements and state machines |

Where the same fact must appear twice, it appears with the same wording and the same IDs. A discrepancy between two deliverables is a finding, not a style difference.

### Export

Word is the document format and carries the embedded diagrams; Excel carries the wide registers that people filter, sort and work in. Tag a table for Excel by placing `<!-- xlsx: workbook=<key>; sheet=<name> -->` directly above it. Two workbooks are standard:

| Workbook | Contents |
| --- | --- |
| Requirements and traceability | Business requirements, product features, functional requirements, business rules, non-functional requirements, success metrics, user stories, acceptance criteria, traceability |
| Project plan and roadmap | Scope, deliverables, WBS, milestones, phases, sprints, task schedule, dependencies, resource allocation, RACI, release plan |

Build with `python tools/build_deliverables.py projects/<project>/deliverables --project "<name>"`. Run `--check` first and resolve its errors. See [tools/README.md](tools/README.md) for options, markers and metadata.

Generated files are output, never source. Regenerate after any change to an approved record; do not hand-edit an exported file and present it as current. Record every run in the manifest generation log.

### Verification

A clean build means the files were written, not that they are right. Open each exported file, refresh the Word fields, and complete the export verification and cross-document consistency checks in `templates/23-deliverable-package.md`. Report what was actually inspected; an unopened export is unverified.

## 13. Gates

| Gate | Required evidence | If not met |
| --- | --- | --- |
| G1 — Discovery sufficient | Analyzed source inventory; gap register; important decisions resolved; explicitly deferred scope documented | Ask the next focused round and continue independent analysis |
| G2 — Model and specification reviewable | Complete applicable 26 sections; process/permission/state/data consistency; measurable criteria; no unresolved major ambiguity | Revise draft and quality findings |
| G3 — Specification approved | User approval tied to a version and complete manifest; no unresolved implementation blocker in approved release | Keep cards pending; present the concrete approval request when ready |
| G4 — Backlog complete | All leaf cards definition-complete; requirements/tests linked; dependencies acyclic; roadmap ordered | Repair decomposition, coverage or decisions |
| G5 — Diagrams generated and verified | Diagram specifications complete and traced to confirmed records; BPMN and data diagrams generated with the named skills; every export rendered and visually inspected; notation and model-status captions present | Complete the specification, regenerate, and re-inspect; do not hand-draw a substitute or ship an unviewed diagram |
| G6 — Deliverable package built | Seven deliverables plus manifest authored from approved records; diagrams embedded; `--check` errors cleared; Word and Excel files generated; every export opened and verified; cross-document consistency checks passed | Fix the source Markdown and rebuild; do not deliver an unverified or hand-edited export |
| G7 — Handoff ready | Final quality report; connected deliverables; valid links; open items explicitly disposed; no incomplete in-release card | State remaining weaknesses; do not claim implementation readiness |

Gates govern project artifacts. Creating the reusable workflow and blank templates does not require a project specification approval.

## 14. Change control

Before approval, update drafts and retain decision history. After approval:

1. Record the requested change as CR-### with its source, rationale and affected requirement IDs.
2. Analyze effects on rules, processes, roles, screens, data, integrations, tests, cards, dependencies and roadmap.
3. Create a new draft revision and mark only impacted approvals/cards as needing review; retain the approved baseline.
4. Obtain approval for changed scope when required; existing unchanged approval remains valid. Clearly attributable user confirmation of a concrete change may serve as its approval.
5. Update the baseline manifest, traceability, reverse dependency links, quality findings and state. Do not rewrite the historical record to imply an earlier approval covered later content.

## 15. Handoff and persistence

Use `templates/13-handoff.md`. Deliver the approved technical specification and development cards with their supporting artifacts, together with the generated deliverable package and its manifest. Include the active revision, approval evidence, requirement/card/test coverage, first executable tasks, known external prerequisites and any remaining non-blocking weakness.

List both layers in the handoff: the Markdown source records and the generated Word and Excel files, with the build date and the source revision each export was produced from. A recipient must be able to tell which export corresponds to which approved revision.

Record exact paths and the next action in `project-state.md`. Keep final documents in the chosen language. Do not claim that tracker import, implementation, UAT, deployment, training or support happened unless actual evidence exists.
