# Operating Workflow

## 1. Purpose and principles

This workflow turns incomplete project information into a validated, traceable, prioritised and actionable project plan. Its main job is to **reduce uncertainty progressively**: each stage turns some of what is unknown into what is confirmed, records what is still unknown, and proves — at a gate — that it is safe to build the next stage on top. It is the working method of a senior business analyst, product manager and project planner. It is not a document-generation pipeline: documents are produced from the analysis at the end, and producing them proves nothing about the analysis.

### Behavioural rules

These apply in every stage.

1. **Do not invent missing requirements.** A gap becomes a question (`Q-###`), never a plausible answer. Business rules, roles, permissions, integrations, approval paths, calculations, fields, states, targets and technical constraints come from a source or a decision.
2. **Do not confuse assumptions with confirmed facts.** Every statement carries its confidence (section 4). An assumption is recorded as one, with the question that will settle it.
3. **Do not jump into implementation.** Planning describes outcomes and constraints. Code-level design, data schemas and technology choices appear only where a source or decision requires them, and then as recorded decisions.
4. **Do not create backlog items before requirements are stable.** Epics, features and tasks come from a specification that has passed its independent review (gate GR) and been approved (gate G8), never from raw notes. The author of a specification never grades it: a separate reviewer does (section 13).
5. **Do not create fake precision.** No estimate without sizing and capacity, no date without a stated basis, no percentage or target without a source.
6. **Do not treat generated documentation as proof of completeness.** A document that exists, or a build that succeeded, says nothing about whether the plan is right. Gates and reviews do.
7. **Do not let contradictions disappear between stages.** A contradiction is a finding or a question until a recorded decision resolves it; it never silently takes one side.
8. **Reuse existing IDs.** Search the registers before creating a record. One concept has one ID for its whole life.
9. **Prefer explicit state and validation over implied progress.** The current stage and every gate result are recorded in `project-state.md`, and `tools/check_gates.py` verifies them. A stage is complete when its gate passes, not when it feels finished.
10. **When information changes, update every affected link.** Record the change and analyse its impact first (section 19.5), then change the records, then re-run the gates from the earliest affected stage. A meaningful change is never an isolated text edit.

Prefer "This is unresolved" over an invented answer. An honest `TBD (Q-###)` is progress; a confident guess is a defect waiting to be found.

### Three output layers

```text
Markdown / editable source records          (1) Source of truth
        |
        +--> Human deliverables              (2) Markdown, DOCX, XLSX, PNG, SVG, .drawio, .excalidraw
        |
        +--> Machine handoff                 (3) Validated, versioned JSON -> downstream engineering (SoftwareFactory)
```

The **source of truth** is the set of Markdown records the stages produce. The **human deliverables** are generated from them for stakeholders (section 22). The **machine handoff** is generated from them for engineering automation (section 23). Humans should not need JSON to understand the project, and machines should not need to reinterpret Word documents to execute it. Nothing generated is ever edited and fed back.

## 2. The workflow at a glance

```text
INPUT ─▶ DISCOVERY ─▶ REQUIREMENT ANALYSIS ─▶ PROCESS / DOMAIN ANALYSIS ─▶ SOLUTION PLANNING & SCOPE
  G1         G2                G3                        G4                            G5
─▶ ARCHITECTURE GOVERNANCE ─▶ SPECIFICATION ─▶ INDEPENDENT SPECIFICATION REVIEW ─▶ RESOLUTION & APPROVAL
             G6                     G7                      GR (8A)                       G8 (8B)
─▶ BACKLOG DECOMPOSITION ─▶ DEPENDENCY & SEQUENCING ─▶ BACKLOG READINESS VALIDATION ─▶ ROADMAP / PROJECT PLAN
            G9                     G10 (10A)                     GB (10B)                        G11
─▶ TRACEABILITY VALIDATION ─▶ FINAL PLANNING PACKAGE
             G12                        G13
```

| Stage | Purpose | Main outputs | Exit gate |
| --- | --- | --- | --- |
| 1. Project Intake | Capture what is known and how well | `discovery/project-intake.md` | G1 — Intake complete |
| 2. Discovery | Establish what is known and what still needs clarification | Discovery log; open questions, assumptions, risks, decisions, dependencies | G2 — Discovery ready |
| 3. Requirement Analysis | Write requirements and prove their quality | Requirement registers; requirement quality review | G3 — Requirements ready |
| 4. Process and Domain Analysis | Model workflows and business entities | Process model; domain model | G4 — Models ready |
| 5. Solution Planning and Scope | Define the logical solution and the release boundary | Module register; scope register | G5 — Solution and scope ready |
| 6. Architecture Governance | Make significant technical decisions explicit, approved and enforceable | Architecture register; principles; ADRs; architecture review | G6 — Architecture ready |
| 7. Specification | Consolidate the approved planning information | Technical specification | G7 — Specification complete |
| 8A. Independent Specification Review | A reviewer who is not the author finds what would make the plan wrong | Specification review (REVIEW-### findings, cycles, history); `specification-review.json` | GR — Specification reviewed |
| 8B. Specification Resolution and Approval | Resolve the findings in the stages that own them; re-review; obtain approval | Resolved records; later review cycles; approval record | G8 — Specification ready |
| 9. Backlog Decomposition | Turn approved requirements into outcome-oriented work: features, then tasks | Epics, features, task cards | G9 — Backlog decomposed |
| 10A. Dependency Mapping and Prioritisation | Order the work by what it depends on and what matters | Dependencies, priorities, dependency graph | G10 — Sequencing ready |
| 10B. Backlog Readiness Validation | Prove every READY task earned it; show what can start now | Readiness report, `backlog-readiness.json`, work sets, task statuses | GB — Backlog ready |
| 11. Roadmap and Project Plan | Phase the work honestly | Roadmap phases; risk-informed plan | G11 — Roadmap ready |
| 12. Traceability Validation | Prove the whole plan hangs together | Traceability; final planning review | G12 — Planning validated |
| 13. Final Planning Package | Produce the package from the validated plan | Planning summary, deliverables, diagrams, machine handoff | G13 — Planning package ready |

Some disciplines run through every stage rather than belonging to one: the risk register, the decision log, traceability, confidence and uncertainty, change management and the prevention of architecture drift (section 19).

Stages can overlap in time — a discovery answer can arrive while requirements are being written — but they cannot overlap in **completion**: a stage's gate cannot pass while an earlier gate fails, and `project-state.md` cannot claim a later stage than the gates support. ProjectPlanner never moves from raw input to backlog creation; the gates between them make that impossible to do silently.

## 3. Start, resume and project state

**Start.** Read this document and `AGENTS.md`. Create a folder under `projects/` (layout in `projects/README.md`) and `project-state.md` from `templates/00` with *Current stage* `1 — Project Intake`. Preserve or reference original inputs in `sources/`, recording filenames, versions, authors if known, locations and authority. For screenshots and forms, record visible fields and unreadable areas without guessing. Copy only the templates the current stage needs; do not create completed-looking content from examples.

**Resume.** Read `project-state.md`, then run:

```bash
python tools/check_gates.py projects/<project>
```

Continue at the first gate that fails; if gate GC reports an unrecorded change, record and analyse it before anything else. Read the latest discovery round, `discovery/open-questions.md`, `discovery/decisions.md` and the latest review before asking anything new. Verify which specification revision is approved before doing work that depends on it.

**Persist.** After each round or material change, update the affected records and `project-state.md` together: current stage, gate results as the tool printed them, open blockers, next step. Before handing control back to the user, save the stage, revision, approvals, next step and open blockers.

## 4. Evidence, confidence and scope

### Confidence

Every statement that planning relies on carries one of four confidence levels:

| Confidence | Meaning | What it may support |
| --- | --- | --- |
| CONFIRMED | Stated by an attributable source or the decision authority, with no unresolved conflict | Confirmed and approved requirements, decisions, scope |
| LIKELY | Strongly suggested by the evidence but not stated | Draft requirements with a confirming question |
| ASSUMPTION | A working hypothesis recorded in `discovery/assumptions.md` | Draft work only; never a confirmed requirement |
| UNKNOWN | Not known; a question is open | Nothing — it is a `TBD (Q-###)` |

Confidence rises only through evidence or a recorded decision. It is never raised to make a gate pass.

### Classification of statements

| Classification | Meaning | How it changes |
| --- | --- | --- |
| Confirmed requirement | Explicit requirement supported by an attributable authoritative source or user answer, with no unresolved conflict | Change only through recorded decisions; assess impact on approved scope |
| Assumption | Provisional interpretation without sufficient confirmation | Confirm, reject or replace through a decision; never silently promote |
| Recommendation | Analyst proposal with rationale and tradeoffs | Becomes scope only if accepted in the decision log |
| Open question | Missing or conflicting decision with an owner and consequence | Resolve with an answer and update every affected artifact |
| Out of scope / future | Explicitly excluded or deferred, with reason and authority | Reintroduce only through change control |

### Scope

Every requirement and feature is classified IN SCOPE, OUT OF SCOPE, FUTURE or PENDING DECISION (`templates/33`). Future ideas never drift into the current scope; they move only by recorded decision. A PENDING DECISION item is named by the open question that decides it.

### Unknowns and non-applicability

`TBD (Q-###)` means unknown and names the question that will resolve it. `N/A — reason; SRC/DEC reference` means non-applicability is established. Neither a blank field nor an illustrative example is evidence. Do not assign an unconfirmed person as a decision owner: write `TBD (Q-###)`.

Keep an original statement and a normalised interpretation when wording matters. Record contradictions as competing statements with both source locations, and raise a question. Consolidate duplicates only when meaning, permissions, conditions and outcomes match; retain all source links and retired-ID aliases.

## 5. Identifiers and terminology

IDs are unique within a project, stable after assignment and never reused. The same ID names the same thing in the Markdown records, the Word and Excel deliverables and the machine-handoff JSON; no output invents its own numbering. The patterns below define namespaces, not project records.

| Pattern | Record |
| --- | --- |
| GOAL-001 | Business goal: a measurable outcome the organisation wants |
| BR-001 | Business requirement: what the business needs to reach a goal |
| RULE-001 | Business rule: a policy, calculation or constraint |
| FR-001, FR-AUTH-001 | Functional requirement; a module code only when it is confirmed |
| NFR-001 / DR-001 / IR-001 / SR-001 / UXR-001 / TR-001 | Non-functional / data / integration / security / UX / technical requirement |
| SRC-001 / DEC-001 / Q-001 / ASM-001 / RISK-001 / DEP-001 | Source / decision / open question / assumption / risk / external dependency |
| SCOPE-001 / REC-001 / CHANGE-001 | Scope register item / recommendation / change record |
| ROLE-001 / MOD-001 / PAGE-001 / ENT-001 | Role / module / page / business entity |
| PROC-001 / STATE-001 / SCN-001 | Process / entity-scoped state / scenario |
| KPI-001 / REPORT-001 / NOTIF-001 / INT-001 / API-001 | KPI / report / notification / integration / API contract |
| ADR-001 / PRIN-001 | Architecture decision record / architecture principle |
| EPIC-001 / FEAT-001 / TASK-001 / TASK-001-S01 | Epic / feature / task / optional subtask |
| AC-001 / TEST-001 | Acceptance criterion / test definition |
| PHASE-01 / FIND-001 / DIAG-001 | Roadmap phase / finding of the requirement, architecture or final planning review / diagram |
| REVIEW-001 | Finding of the independent specification review, numbered across all review cycles |
| WS-01 | Ready work set, generated by the tools; renumbered on every run |

Retired forms — `BIZ-###` for business requirements, `EPIC-01`, `FEAT-01-01`, `AT-###`, `CR-###` for change requests and area-prefixed task IDs — are reported as warnings. The machine-handoff patterns are defined once in `schemas/common.schema.json`.

Use the confirmed domain glossary. Define units, time zones, business dates and synonyms before using them in formulas or filters. Clarify terms such as "approved", "confirmed" and "completed" when their meanings differ by entity. Preserve necessary Uzbek and Russian domain terms in the glossary with normalised definitions.

## 6. Stage 1 — Project Intake

**Purpose.** Capture what is already known about the project, and how well it is known, before any analysis begins.

**Inputs.** The initial idea; supplied files, screenshots, spreadsheets and notes; the first conversation.

**Activities.**
- Read every supplied material. Register each in `discovery/sources.md` with its authority and any unreadable or inaccessible part; report what could not be read.
- Fill the fourteen intake items: project name, objective, business problem, target users, stakeholders, known scope, constraints, deadlines, existing systems, available files, screenshots, stakeholder notes, known assumptions, known risks.
- Classify each item CONFIRMED, LIKELY, ASSUMED or UNKNOWN. Record assumptions in `discovery/assumptions.md` and unknowns as questions in `discovery/open-questions.md`.
- Give the project a Project ID in `project-state.md`. A project without a name keeps a temporary folder label and its name stays UNKNOWN.

**Outputs.** `discovery/project-intake.md` (`templates/29`), the first registers, `project-state.md`.

**Gate G1 — Intake complete.** All fourteen items are present and classified; UNKNOWN items name their question and ASSUMED items their assumption; the Project ID is set.

**Move on when** G1 passes. Set *Current stage* to 2.

## 7. Stage 2 — Discovery

**Purpose.** Determine what is known and what still needs clarification, in every area planning will depend on.

**Inputs.** The intake and its registers; answers from interview rounds; further materials.

**Activities.**
- Produce the seven-part initial analysis (`templates/01`): Project Understanding, Extracted Requirements, Identified Actors, Identified Workflows, Missing Information, Conflicts / Ambiguities, Discovery Questions.
- Track coverage in fourteen categories in `discovery/discovery-log.md` (`templates/30`): Business, Users, Workflows, Data, Integrations, Security, Permissions, Reporting, Notifications, Technical constraints, UI/UX, Operations, Compliance, Migration. For each: confirmed information, open questions, assumptions, risks and sources.
- Prioritise every question BLOCKER, HIGH, MEDIUM or LOW (`templates/02`). A **blocker** means downstream planning cannot be trusted until it is resolved. A question is blocking if its answer can change scope, access, calculations, state transitions, data ownership, integration behaviour, security, acceptance outcomes, or the ability to implement affected work without reinterpretation.
- Interview in small rounds of about three to five questions, blockers first, and only questions the materials do not already answer. For each, state the missing decision, why it matters, and an example answer format when helpful. Separate a suggested design from a request for fact.
- After each round: record answers verbatim or faithfully with their source; list newly confirmed facts, rejected assumptions and remaining gaps; update the registers and the log; record decisions; explain any conflict with an earlier decision; save the next questions and the stage.
- Record risks (`discovery/risks.md`) and external dependencies (`discovery/dependencies.md`) as they surface.

Useful round topics, in an order adaptable to dependencies:

| Round | Investigate only unanswered areas |
| --- | --- |
| Business process | Project/client, objective, AS-IS, problems, TO-BE, scope boundaries, success measures |
| Users and permissions | Stakeholders, roles, ownership, module/action/record scope, delegation, create/view/edit/delete/approve/export/admin |
| Modules and data | Entities, lifecycle, master data, business documents, pages, forms and actions, uploads, statuses, validation, search/filter/sort, import/export |
| Approval workflows | Whether approvals exist; actor and sequence, prerequisites, rejection and resubmission, cancellation, comments, attachments, notifications, concurrency, audit |
| Integrations | Systems and owners, API evidence and access, direction, authentication, payloads, frequency, failures, retries, logging |
| Reports and dashboards | Decisions supported, KPI definitions, formulas, units, date basis, grouping, filters, refresh, drill-down, export and visibility |
| Technical constraints | Confirmed stack, security and authentication, volume, performance, availability, devices, localisation, backup, retention |
| Acceptance and deployment | UAT authority and scenarios, test data, rollout, migration, environments, training, support, deliverable formats, team capacity |

**Outputs.** Discovery log; open questions; assumptions; risks; decisions; dependencies; interview rounds (`discovery/rounds/`).

**Gate G2 — Discovery ready.** Every category is COMPLETE, PARTIAL or NOT APPLICABLE with a reason; the registers exist; every open question has a priority and an owner; **no open BLOCKER question affects in-scope planning**. A blocker is resolved, or everything it affects is classified PENDING DECISION, FUTURE or OUT OF SCOPE so the rest of the plan can proceed without it. Open HIGH questions and PARTIAL categories are reported as warnings.

**Move on when** G2 passes. Discovery continues alongside later stages as answers arrive; every new blocker re-opens the gates it affects.

## 8. Stage 3 — Requirement Analysis

**Purpose.** Turn understood information into individually identified, testable requirements, and prove their quality before anything is built on them.

**Inputs.** The discovery log and registers; the confirmed sources.

**Activities.**
- Write requirements only for information discovery has made sufficiently clear. Record each in its register (`templates/26`): GOAL, BR, RULE, FR, NFR, DR, IR, SR, UXR or TR.
- Give each requirement: ID, title, description, rationale, source (the goal or business requirement it serves), evidence, priority and its basis, status, scope, confidence, related stakeholder, dependencies, acceptance condition and notes. Functional requirements also state actor, trigger and permissions.
- One ID is one need. Do not combine unrelated requirements; do not split one need across IDs.
- State needs, not designs. No tables, endpoints or frameworks in business, functional or UX requirements.
- Run `python tools/check_gates.py projects/<project> --gate G3`. Its heuristics flag unmeasured wording (fast, easy, modern, user-friendly, secure, flexible, efficient … with no measurable criterion), implementation detail, requirements that may combine several needs, functional requirements without actor, trigger, permission rule or failure case, missing rationale, evidence or stakeholder, duplicate titles, and requirements that do not trace upward.
- Review every requirement in `reviews/requirement-quality-review.md` (`templates/31`) for ambiguity, duplication, contradiction, missing actors, triggers and outcomes, undefined terminology, untestable wording, implementation assumptions, missing error cases and missing permission rules. Record findings by severity and return each to the stage it belongs to.

**Outputs.** Requirement registers; requirement quality review.

**Gate G3 — Requirements ready.** At least one goal, business requirement and system requirement exist; every Confirmed or Approved requirement is complete, rests on CONFIRMED information and traces upward (system requirement → BR → GOAL); no open BLOCKER affects in-scope requirements; the review's checklist is complete with no open CRITICAL or MAJOR finding. Lint findings are warnings for the reviewer to disposition.

**Move on when** G3 passes.

## 9. Stage 4 — Process and Domain Analysis

**Purpose.** Understand how work flows and what the business keeps track of, before designing a solution for it.

**Inputs.** Confirmed requirements; discovery answers about workflows, data and permissions.

**Activities.**
- Model each important workflow as a process record (`templates/03`): actor, trigger, preconditions, main flow, alternative flow, exceptions, result, business rules and data involved. Model AS-IS and TO-BE separately where the process changes, and list the differences explicitly.
- Define entity-scoped states and every permitted transition: actor, permission, guard conditions, side effects, failure behaviour, notification and audit. Ask whether cancellation, resubmission, delegation or concurrent change applies; do not add them by default.
- Model the business entities (`templates/32`): purpose, key attributes, relationships, lifecycle states, ownership, permissions and governing rules. This is the business model, not a database design.
- Mermaid is welcome inside working records as a thinking aid for a confirmed flow. Delivered diagrams are generated only once the logical workflow is understood (section 21).

**Outputs.** `specification/process-model.md`; `specification/domain-model.md`.

**Gate G4 — Models ready.** At least one process and one entity; every process states all its elements (or `None — reason`); every entity states purpose, attributes, relationships, lifecycle, ownership and permissions; referenced entities and rules exist. Warnings: an AS-IS process with no TO-BE, a functional requirement in no workflow, models resting on assumptions.

**Move on when** G4 passes.

## 10. Stage 5 — Solution Planning and Scope

**Purpose.** Define the logical structure of the solution and draw the release boundary explicitly.

**Inputs.** Requirements, process and domain models, confirmed constraints.

**Activities.**
- Identify the modules (`templates/37`): user-facing areas, administrative areas, integrations, external services, reporting, notifications and platform capabilities. For each: type, purpose, security boundary and the entities it owns. This is the logical structure; technology and other binding choices are made in stage 6.
- Map every in-scope system requirement to one or more modules through its *Related modules* field.
- Note every architecture question the structure raises; stage 6 records it.
- Build the scope register (`templates/33`) and classify every requirement and feature IN SCOPE, OUT OF SCOPE, FUTURE or PENDING DECISION.

**Outputs.** `specification/solution-structure.md`; `specification/scope.md`.

**Gate G5 — Solution and scope ready.** Modules exist with type and purpose; every live requirement has a scope; every in-scope system requirement maps to a module; the scope register exists; every PENDING DECISION item is named by an open question. Warnings: out-of-scope items without a rationale.

**Move on when** G5 passes.

## 11. Stage 6 — Architecture Governance

**Purpose.** Make the significant technical decisions explicit, reviewable, versioned and traceable before the specification consolidates them, so that no later stage can contradict them silently. This stage works at system level — styles, platforms, boundaries, integration patterns, data ownership, security architecture. It is not low-level implementation design: "use a modular monolith", "authentication belongs to the shared identity module" and "REST for public APIs" belong here; "create class AuthService in src/auth/service.py" does not.

Architecture governance answers six questions: What major technical decisions have been made? Why? What alternatives were considered? What constraints do they create? Which requirements and features depend on them? Is any proposed work in conflict with an accepted decision?

**Inputs.** Requirements (G3), process and domain models (G4), the solution structure and scope (G5), confirmed technical constraints, existing systems and technology from the sources.

**Activities.**
- **Identify every architecture question.** Classify each concern in the coverage table of `architecture/architecture-register.md` (`templates/27`): architecture style, backend platform, frontend architecture, data storage, authentication, authorisation model, API style, integration strategy, event-driven messaging, background processing, caching, file storage, deployment model, multi-tenancy, data ownership, module communication, logging and observability, security architecture, external service dependencies and scalability strategy — plus any concern specific to the project. Each is DECIDED, PROPOSED, DECISION REQUIRED, DELEGATED or NOT APPLICABLE, with the evidence its status needs.
- **Detect missing decisions.** An unresolved technical choice that affects requirements, scope, security or the structure of the backlog — authentication method unknown, storage technology unknown, multi-tenancy unknown, integration strategy unknown, deployment model unknown — is flagged **ARCHITECTURE DECISION REQUIRED** with a question (`Q-###`), a priority and an owner. It is never answered by an invented solution.
- **Record principles** in `architecture/principles.md` (`templates/38`): few, meaningful, and stated by a source or the decision authority. A principle guides decisions; it never replaces an ADR.
- **Record each significant decision as an ADR** (`templates/28`) in `architecture/ADR-###-<short-title>.md`, registered at once in the ADR register. Write an ADR for a choice with project-wide or long-term consequences; do not write one for a helper name, a CSS class or a small utility library unless that choice has project-wide consequences. An ADR states context, decision, rationale, alternatives with their advantages and disadvantages, positive and negative consequences, risks, the constraints it introduces in reviewable language, and its links to requirements, features, modules, decisions, principles and other ADRs.
- **Follow the proposed-ADR workflow.** Architecture question identified → ADR created as PROPOSED, naming the question that decides it → options analysed → consequences documented → human review → ACCEPTED or REJECTED by the named decision owner, with the approval recorded as `DEC-###` or `SRC-###`. The planner never marks an important decision accepted on its own authority.
- **Link requirements to decisions** only where a decision materially affects them — through the ADR's *Related requirements*, or the requirement's own *Architecture decisions* field. Do not force every requirement to reference an ADR.
- **Review the architecture** (`templates/39`, `reviews/architecture-review.md`): run `tools/check_gates.py`, copy the counts from the generated `reports/architecture-report.md`, review every ADR in its current status, complete the checklist and record findings. An **ARCHITECTURE CONFLICT** is identified, referenced to the affected ADR, explained, and resolved by exactly one of: change the proposal (`CHANGE PROPOSAL`), add a decision (`NEW ADR`), or replace the old decision (`SUPERSEDE ADR`).

**ADR lifecycle.** PROPOSED — under consideration, governs nothing, and every task bound by it stays out of READY. ACCEPTED — approved; governs all planning until superseded or deprecated. REJECTED — considered and not accepted. SUPERSEDED — replaced by a newer accepted ADR named in *Superseded by*. DEPRECATED — historically relevant, but no new planning may rely on it. Only ACCEPTED decisions are active.

**Supersession.** When a decision changes, write a new ADR that names the old one under *Supersedes*. When the decision owner accepts it, mark the old ADR SUPERSEDED with *Superseded by* naming the new one. Both links must agree, and a proposed ADR replaces nothing. The old ADR keeps its content: history is never rewritten.

**Core rules.**
1. Never hide an important architecture decision inside general prose.
2. Never silently change an accepted architecture decision.
3. Never reuse an ADR ID; never delete an ADR file.
4. Never treat a proposed ADR as accepted.
5. Never treat a rejected, superseded or deprecated ADR as active.
6. Never allow conflicting accepted ADRs without a validation error.
7. Never let downstream planning silently contradict accepted architecture.
8. Prefer a new ADR over rewriting history.
9. Keep ADRs focused on significant decisions.
10. Keep architecture governance separate from low-level implementation detail.

**What the tools enforce.** `tools/validate_handoff.py` and `tools/check_gates.py` report: a proposed ADR without a deciding question; an accepted, rejected, superseded or deprecated ADR without a named decision owner and approval evidence; an accepted ADR without context, decision or rationale; two accepted ADRs recorded as conflicting, or an accepted ADR superseded by another accepted one while still accepted; supersession links that disagree, or a decision "replaced" by an ADR that is not accepted; an accepted ADR depending on an inactive one; a requirement, feature or task that names a rejected, superseded or deprecated ADR (with the successor named); an ADR ID registered without a file or a file not registered; and, as warnings, missing alternatives or constraints, vague constraint wording and code-level detail. Whether two accepted decisions contradict in substance is a judgement recorded in the architecture review.

**Outputs.** `architecture/architecture-register.md`, `architecture/principles.md`, `architecture/README.md` (`templates/40`), `architecture/ADR-###-*.md`, `reviews/architecture-review.md`; `reports/architecture-report.md` (generated).

**Gate G6 — Architecture ready.** The register, principles and review exist; every standard architecture concern is classified with its evidence; every ADR is registered and agrees with its file; no proposed ADR or DECISION REQUIRED concern rests on an open BLOCKER question that affects in-scope work; accepted ADRs are complete, approved by a named owner and free of recorded conflicts; supersession is consistent; no live requirement relies on an inactive ADR; the architecture review is complete, current for every ADR's status and count, with no open CRITICAL or MAJOR finding and every architecture conflict resolved or withdrawn with a reason. Warnings: proposed ADRs, non-blocking DECISION REQUIRED concerns, proposed principles, in-scope technical or integration requirements linked to no ADR, missing alternatives or constraints, vague constraints, implementation detail.

**Move on when** G6 passes. A critical unresolved architecture decision that materially affects the solution blocks the specification; it is decided, or everything it affects is classified PENDING DECISION, FUTURE or OUT OF SCOPE.

## 12. Stage 7 — Specification

**Purpose.** Consolidate the approved planning information into the technical specification.

**Inputs.** Everything gates G2–G6 have validated.

**Activities.**
- Write all 26 sections of `templates/04`, with detail records (`templates/05`, `06`, `14`) where needed. Retain an inapplicable section with an evidence-based N/A.
- **Consolidate; do not create.** Every requirement, rule, entity, decision and question the specification mentions exists in a record. No numerical target, policy, permission or integration promise is inferred from convention.
- When writing reveals a gap, do not fill it here. Raise a question or finding and return to the stage that owns it: an unanswered fact to stage 2, a defective requirement to stage 3, a missing workflow or entity to stage 4, a scope or module question to stage 5, an architecture question or a conflict with an accepted ADR to stage 6.

**Outputs.** `specification/technical-specification.md` and its detail records.

**Gate G7 — Specification complete.** All 26 sections are present; the specification mentions no ID that no record defines. Warnings: an in-scope requirement or an accepted ADR the specification does not reference, `TBD` without a question, `TBD (Q-###)` for a question that has been answered.

**Move on when** G7 passes.

## 13. Stage 8 — Independent Specification Review and Resolution

**Purpose.** Stop ProjectPlanner from trusting its own specification. A second, independent pass looks for contradictions, omissions, ambiguity, untestable requirements, broken traceability, stale assumptions and architectural inconsistencies. That pass happens before anyone approves the specification or builds a backlog on it. This is a quality gate, not a document milestone: a polished document is not automatically a correct specification.

The stage has two halves, each with its own gate:

```text
SPECIFICATION (G7) ─▶ 8A INDEPENDENT SPECIFICATION REVIEW (GR) ─▶ 8B SPECIFICATION RESOLUTION AND APPROVAL (G8) ─▶ BACKLOG (G9)
                              ▲                                              │
                              └──────── next review cycle ◀── findings resolved in the stages that own them
```

**Inputs.** The specification; gate reports G1–G7; the source records; `reports/specification-review-aid.md`.

### Two roles

| Role | Does | Never |
| --- | --- | --- |
| **SPECIFICATION AUTHOR** | Writes and updates the specification and the records it consolidates; resolves findings in the stage each belongs to | Grades their own work; closes a finding without the reviewer's re-review |
| **SPECIFICATION REVIEWER** | Evaluates the specification independently against the source records, like a skeptical senior business analyst, solution architect and QA reviewer; raises findings with evidence; recommends; re-reviews | Assumes the author's conclusions are correct; summarises instead of reviewing; rewrites requirements, ADRs, scope, workflows, the roadmap or features |

The two are different people, or, for an AI planner, different passes. The review pass starts fresh from the records in the project folder, without the author's reasoning or conversation. It follows `prompts/specification-reviewer.md` and writes only `reviews/specification-review.md`. The review names both roles and states how the reviewer is independent. A reviewer who is also the author fails gate GR.

### 8A — Independent Specification Review

**Activities.**
- Run `python tools/check_gates.py projects/<project>` and read `reports/specification-review-aid.md`. The aid is generated from the records and lists candidates for the reviewer to judge, never findings of its own. It covers possible contradictions, and traceability re-derived from the records rather than read from the generated files. It also covers assumptions that live requirements rest on, acceptance criteria with vague wording, the scenario families each workflow mentions, missing permission rules and undecided security concerns, integrations and dependencies without risks, terminology used side by side, and change state.
- Review the specification against the source records, area by area (`templates/12`). The areas are requirements quality, scope consistency, workflow completeness, missing scenarios, permissions and authorisation, security, the data model, integrations, architecture consistency with accepted ADRs, independent traceability, contradictions, acceptance criteria, terminology, assumptions, risks, change consistency, roadmap consistency and review quality. What each area examines:

| Area | The reviewer checks |
| --- | --- |
| Requirements quality | Ambiguity, duplication, contradiction, missing rationale or source, missing or untestable acceptance criteria, vague wording, hidden assumptions, incorrect status, inconsistent priority |
| Scope | In-scope features are supported by requirements; out-of-scope and FUTURE items do not appear as current work; PENDING DECISION items are not presented as approved |
| Workflows and missing scenarios | Actors, triggers, preconditions, alternative and exception paths, failure handling, complete lifecycle states, contradictory workflows. For every major workflow, the scenarios that make sense for it: success, failure, validation error, permission denied, external service unavailable, duplicate action, cancel, retry, timeout, empty state, invalid state transition. Never meaningless edge cases |
| Permissions and security | Who can perform each action; role, ownership, escalation and approval rules; control of administrative actions; tenant boundaries; authentication, authorisation, sensitive data, secrets, file uploads, integrations, auditability, abuse cases, account recovery, sessions, rate limiting where relevant. A missing security requirement is a finding, never an invented requirement |
| Data model | Entities referenced but not defined, conflicting states, inconsistent ownership, impossible relationships, missing lifecycle, retention or deletion rules, one concept under two names |
| Integrations | For each: purpose, ownership, inputs, outputs, authentication, failure behaviour, timeout and retry assumptions, dependency risk, fallback, data ownership |
| Architecture | Conflicts with accepted ADRs; requirements that need an undecided architecture; contradictory accepted ADRs; superseded, rejected or deprecated ADRs still used; major decisions made in prose without an ADR |
| Traceability | GOAL → BR → FR/NFR → ADR → MOD → FEAT → AC, re-derived independently: orphaned requirements and features, missing links, references to missing, cancelled or superseded artifacts, broken or duplicate IDs |
| Contradictions | Searched for explicitly — one versus many, delete versus retain, anonymous versus authenticated, and any other pair of statements that cannot both hold. Contradictory statements are never two valid requirements |
| Acceptance criteria | Observable, testable, complete, free of contradiction and vague wording ("the page should work well" is not a criterion; "a suspended user cannot create a new booking" is) |
| Terminology | One term per concept: Organization is not also Company, Tenant, Workspace or Account without an explicit distinction |
| Assumptions | No assumption is treated as confirmed without stakeholder evidence ("Only administrators need reports" does not become "Reports are only available to administrators") |
| Risks | Every major specification decision, critical dependency and integration has its risk in the register |
| Change consistency | After approved changes: affected artifacts reviewed, stale items updated, invalid READY items reset, traceability refreshed, roadmap reconsidered. Propagation is verified, never assumed |
| Roadmap | When a backlog exists: dependencies against sequencing, blocked features scheduled too early, milestones resting on unresolved decisions, scope and roadmap mismatches, unsupported timeline assumptions |

- Record every problem as a **finding** (`REVIEW-###`), a record block in the review. Each finding carries a severity, a category and a status. It carries *Raised in cycle*, and the *Affected artifacts* it concerns. It has *Evidence* that cites specific artifacts and what they state, a *Conflict* section for a contradiction, *Why it matters*, *Required action*, and the stage that resolves it. Write "FR-021 defines membership of several organisations, while SR-009 assumes exactly one", never "the specification seems unclear". Prefer a few well-evidenced findings to volume: no duplicates, vague or purely stylistic findings, speculation, fake contradictions or findings without evidence. Finding IDs are stable across cycles and never reused.
- **Severity.** CRITICAL: the specification cannot safely proceed — a direct contradiction, a fundamental architecture conflict, unresolved security-critical behaviour, an impossible workflow, a missing core business rule. MAJOR: a substantial planning problem — incomplete authorisation rules, an important missing exception path, a significant traceability gap, a feature no approved requirement supports. MINOR: usable but should be corrected — inconsistent terminology, incomplete metadata, minor duplication. OBSERVATION: not necessarily a defect but worth review.
- **Category.** REQUIREMENT, SCOPE, WORKFLOW, DATA, SECURITY, AUTHORIZATION, ARCHITECTURE, INTEGRATION, TRACEABILITY, ROADMAP, RISK, TERMINOLOGY, CHANGE_IMPACT, ACCEPTANCE_CRITERIA, ASSUMPTION.
- Complete the checklist — every area, every row examined with its evidence, a FAIL row citing its finding. Answer the twelve review questions: Is the specification internally consistent? Are requirements complete enough? Are they testable? Are assumptions visible? Are workflows coherent? Are permissions defined? Are major security concerns covered? Does the architecture match the specification? Is traceability valid? Did recent changes propagate correctly? Are there unresolved contradictions? Is the specification safe to use as the basis for backlog planning?
- Conclude with the result the findings support, and the counts. The reviewer **does not fix anything**: detect → document → recommend → wait for resolution → re-review.

**The result rule.** An unresolved CRITICAL finding gives **FAIL**, and so does an unresolved MAJOR finding. There is no arbitrary threshold: one is enough. Only open MINOR or OBSERVATION findings, or accepted risks, give **PASS WITH WARNINGS**. No open finding gives **PASS**.

### 8B — Specification Resolution and Approval

**Activities.**
- The author resolves each finding in the stage it names, never by patching the specification alone. An unanswered fact goes back to stage 2, a defective requirement to stage 3, a missing workflow or entity to stage 4, a scope or module question to stage 5, and an architecture conflict to stage 6 as a new or superseding ADR. The specification is then regenerated from the corrected records. After the baseline exists, a resolution that changes an approved record is a change record (section 19.5).
- Close the cycle with `python tools/specification_review.py projects/<project> --start-cycle`. It freezes the cycle in `reviews/history/specification-review-cycle-NNN.md` and appends it to the review's cycle history. It then reopens every check and question as NOT REVIEWED, so nothing is carried forward unexamined. The reviewer re-reviews every check and verifies each resolution, raises new findings with new IDs, dates the cycle and concludes. Repeat until the review passes.
- **Finding statuses.** OPEN, ACKNOWLEDGED and IN_RESOLUTION are unresolved. **RESOLVED** is set only by the reviewer, in a cycle later than the one that raised the finding. It records *Resolution*, *Resolved by*, *Resolution date*, *Changed artifacts* and *Verification*. **ACCEPTED_RISK** is a deliberate human decision: *Approved by* names a person who is neither the author nor the reviewer, and *Approval evidence* cites DEC-### or SRC-###. It is never available for a CRITICAL finding. An accepted MAJOR finding also has its risk in the register. It stays visible as a warning in every later gate and is never converted to RESOLVED. **REJECTED** means the finding is judged not to be a defect, with the reason; rejecting a CRITICAL or MAJOR finding also needs a named human decision with evidence.
- Once gate GR passes, present the concrete specification for approval, only when it is reviewable. Present it with its revision manifest, the review, the decisions and the explicit exclusions. Record the approval statement, approver, date, version and covered files in `project-state.md`, and set approved requirements to Approved. The approval follows a passing review of that version and never replaces it. Approval is required because the workflow source states: "After the Technical Specification is approved, convert it into executable Project Cards." Do not ask again for approval of unchanged approved content. Source-backed extraction is not approval of the whole specification; record both independently.
- Expose the review in `project-state.md` (`templates/00`, table *Review measure*): specification review result, last review cycle, open critical, open major, open minor, open observations, accepted risks — copied from the tool, never better than the records show.

**Outputs.** `reviews/specification-review.md` (`templates/12`) and every closed cycle in `reviews/history/`; `reports/specification-review-aid.md` (generated); `machine-handoff/specification-review.json` (section 23); the approval record; approved requirement statuses; a baseline in `baselines/<version>/`; the change-control baseline `changes/baseline.json`, recorded with `python tools/analyze_change_impact.py projects/<project> --baseline` once approval is recorded (section 19.5).

`python tools/specification_review.py projects/<project>` verifies the review record, prints its computed result and counts, and writes the review aid. With `--json` it prints the computed `specification-review.json`.

**Gate GR — Specification reviewed** (end of 8A). The review exists for the current specification version, numbered and dated. Its reviewer is named and is not the author, and its independence is stated. Every review area has an examined checklist row, and every FAIL row cites an open finding. All twelve questions are answered: every answer that reports a problem cites an open finding, and the conclusion agrees with the result. Every finding has a severity, category, status and cycle, plus evidence; a CRITICAL or MAJOR finding also cites existing artifacts and the stage that resolves it. Every closed finding records what its status requires, and no CRITICAL finding is an accepted risk. The stated result and counts are those the findings support. Every closed cycle is frozen and agrees with its history row, and no finding was deleted, backdated or reused. Every contradiction candidate is a finding or dismissed with a reason. No approved change is dated after the review; a MEDIUM or higher change fails the gate and requires a new cycle. **No CRITICAL or MAJOR finding is unresolved.** Warnings: open MINOR and OBSERVATION findings, accepted risks, checks passed without evidence, a provisional backlog, and a `project-state.md` without the review summary. A summary in `project-state.md` that is better than the records is a workflow violation.

**Gate G8 — Specification ready** (end of 8B). GR passes. The specification is APPROVED with an approval record for this version, dated on or after a passing independent review of the version. Every in-scope requirement is Approved, and no open BLOCKER affects in-scope work. Open assumptions and still-proposed ADRs are reported as warnings.

**When the review fails.** While GR fails, G8 and every later gate fail, and the Definition of Ready fails for every task (section 14), so `handoff_status` cannot be `ready`. Nothing may be called backlog-ready or planning-complete. Drafting the backlog may continue when it helps a later cycle, but it stays provisional: its tasks stay DRAFT, NEEDS_DISCOVERY or BLOCKED.

**Reviewer principles.**
1. The author does not grade its own work.
2. Evidence is required for major findings.
3. Findings are not silently fixed.
4. Contradictions are resolved explicitly.
5. Assumptions do not become facts without evidence.
6. Accepted ADRs are respected.
7. Traceability is verified independently.
8. Stale planning is detected.
9. Security and authorisation gaps are not ignored.
10. A polished document is not automatically a correct specification.

**Move on when** G8 passes. Only now may backlog items be finalised.

## 14. Stage 9 — Backlog Decomposition

**Purpose.** Turn approved requirements into outcome-oriented, independently verifiable work: feature decomposition, then task decomposition. Generating the backlog is not finishing it — readiness is validated in stage 10B.

**Inputs.** The approved specification, whose independent review passes (GR), and the requirement registers.

**Activities.**
- Build one hierarchy, used consistently: **EPIC** (a large business capability or project area) → **FEATURE** (a user- or business-visible capability) → **TASK** (an independently actionable unit of work) → **SUBTASK** (`TASK-###-S##`, optional, only when a task genuinely needs internal breakdown — never to create more cards). Epics and features go in `backlog/backlog.md` (`templates/07`, `09`); each task gets its own card, `backlog/tasks/TASK-###.md` (`templates/08`).
- Every feature links to requirements, its modules and its scope, and names in *Architecture decisions* the accepted ADRs it relies on; ADRs reached through its requirements and modules are added automatically, so every constraint is visible before a task is written. Every in-scope feature has tasks, or a *No tasks reason* — already implemented, documentation only, external vendor responsibility, no implementation required — with its evidence. Every task links to its feature, its requirements and its acceptance criteria.
- **Respect accepted architecture.** A feature or task never introduces a choice that contradicts an accepted ADR because it is convenient for that one item — GraphQL for one module under an accepted "REST APIs" decision, Firebase Authentication under an accepted internal-authentication decision. The contradiction is an ARCHITECTURE CONFLICT: record it in the architecture review and resolve it by changing the item, adding an ADR, or superseding the ADR — back in stage 6. Until then the task cannot be READY. When a feature needs an architecture choice nobody has made, create a PROPOSED ADR; its tasks stay out of READY until the decision owner accepts it.
- Every task describes an **outcome**: "Allow administrators to suspend a user account", not "Create endpoint", "Add model", "Update serializer", "Fix auth". Code-level decomposition belongs to engineering planning, downstream. Split by a coherent, verifiable outcome — a list page, a state transition, a calculation, an integration exchange, a cross-cutting requirement — and combine tightly coupled UI, backend and data changes when that is what makes the outcome complete. Do not combine unrelated outcomes into a giant task; do not split one outcome into microtasks.
- Every card states its objective, behaviour, failure handling, constraints, security considerations, and — only where the task touches them — its data, API, UI and integration impact, plus its verification requirements, open questions, blocking issues and risks (`templates/08`). Acceptance criteria are observable, testable, specific, non-contradictory and aligned with the source requirement: "a suspended user cannot create a new booking", "an expired reset token is rejected" — never "the feature should work correctly" or "the page should be user-friendly". Relevant failure cases are covered; irrelevant ones are not invented. Do not defer a design decision that affects the outcome to "developer to decide": record a decision or open a question. A new requirement discovered here goes through change control before affected cards become READY.
- Technical enablers trace to an approved TR or NFR; do not invent a user story for infrastructure.

**Task statuses.** Planning statuses only. ProjectPlanner does not own engineering execution statuses — coding, testing, pull request open, merged, deployed, done — and the tools reject them on a card.

| Status | Meaning |
| --- | --- |
| DRAFT | Being specified; not yet validated |
| NEEDS_DISCOVERY | An open question must be answered first |
| NEEDS_REVIEW | Its foundation changed, a serious specification finding or an architecture conflict touches it, or its security behaviour is undefined: revalidate before READY |
| BLOCKED | A dependency, external input, blocking risk or unknown integration behaviour prevents it |
| READY | Passes every Definition of Ready check |
| CANCELLED | Dropped by a recorded decision; kept for history |

Excluding work from the release is a scope classification (FUTURE, OUT OF SCOPE, PENDING DECISION), not a status. Every status transition is recorded in the card's *Readiness history* (date, from, to, reason, change); the last entry matches the status, and a READY card records its validation. A task whose definition changes materially after validation gets a new *Revision*.

**Definition of Ready.** A task may be READY only when it passes every named check — deterministic, evaluated from the records by the generator and recomputed by the validator, never taken on trust: `specification_ready` (approved, and the independent review passes for the current version); `task_id_valid`; `title_clear` and `objective_clear` (title, objective and description stated, no TBD); `source_requirement_valid` (at least one requirement, each Approved and IN SCOPE); `feature_valid` and `scope_valid` (an existing, active, in-scope parent feature; the task in scope); `acceptance_criteria_valid` and `acceptance_criteria_testable` (present, no TBD, observable wording, each AC-### belonging to a source requirement); `dependencies_valid` (reviewed, existing, not itself, not cancelled, in scope, acyclic, and READY); `external_dependencies_available`; `architecture_valid` (constraints documented, every applicable ADR Accepted) and `architecture_conflicts_clear` (no open or unreviewed ARCHITECTURE CONFLICT); `security_valid` (security stated; `N/A` accepted only when the task involves no authentication, authorisation, payments, personal data, secrets, file uploads, external APIs, administrative actions, account recovery or audit); `data_impact_known`, `api_impact_known`, `ui_impact_known` and `integration_impact_known` (stated without TBD wherever the task touches that area — data impact names its entities, API impact its change: NONE, CREATE, MODIFY or REMOVE, integration impact its failure, timeout and fallback behaviour); `verification_defined` (the evidence that proves completion — unit, integration, end-to-end, security, manual acceptance, API contract, UI acceptance, migration — and every named test exists); `open_questions_clear` (no readiness blocker, no open BLOCKER question); `not_stale` (not under change review, section 19.5); `review_findings_clear` (no unresolved CRITICAL or MAJOR specification finding names the task, its feature, epic or requirements — an accepted risk is kept as a reference and does not block); `blocking_risks_clear` (no live risk the register marks *Blocks readiness* names it). Each task's `readiness` records the result, every check, the failures and the status they point to. READY means fully defined, not necessarily startable today.

**Outputs.** `backlog/backlog.md`; `backlog/tasks/`; test definitions (`quality/acceptance-tests.md`, `templates/11`).

**Gate G9 — Backlog decomposed.** At least one epic, feature and task; every feature has a scope and a requirement; every in-scope system requirement is delivered by a feature and implemented by a task (or by a feature with a recorded *No tasks reason*); every in-scope feature has tasks or a reason; no orphan feature or task; the backlog index agrees with the cards; no feature or task relies on a rejected, superseded or deprecated ADR; every ARCHITECTURE CONFLICT the checker reports is recorded in the architecture review. Warnings: features bound by proposed ADRs, features without tasks that record why, possible conflicts that were reviewed and withdrawn.

**Move on when** G9 passes.

## 15. Stage 10 — Dependency Mapping, Prioritisation and Backlog Readiness

Stage 10 has two halves: **10A** orders the work (gate G10), and **10B** validates that the backlog is ready for implementation (gate GB).

### 10A — Dependency Mapping and Prioritisation

**Purpose.** Order the work by what it depends on and by what matters, without confusing the two.

**Inputs.** The backlog; external dependencies; open questions; the risk register.

**Activities.**
- Record dependencies explicitly: between requirements (*Dependencies*), features (*Depends on*), tasks (*Blocked By*), external systems and inputs (*External dependencies*, `DEP-###`) and stakeholder decisions (open questions naming the item).
- Detect missing dependency IDs, self-dependencies, circular dependencies, dependencies on cancelled or out-of-scope work, invalid cross-feature dependencies and hidden prerequisites (a task depending on another feature's task without the feature dependency being declared), impossible sequencing and features blocked by unresolved decisions. Resolve cycles by rethinking the split; never by picking an arbitrary order. While a cycle exists no execution sequence is generated at all.
- Declare one project-wide prioritisation scheme in `project-state.md` — Levels (Critical, High, Medium, Low) or MoSCoW (Must, Should, Could, Won't) — and prioritise every in-scope requirement, feature and task on business value, user value, risk, dependencies, regulatory or security need and sequencing. Priority is proposed with its rationale until the decision authority confirms it. Not everything is top priority. **Priority is business importance; sequence is the recommended implementation order**, computed from the dependencies. They are separate fields, and high-priority work does not go first when its prerequisites are missing.
- `tools/check_gates.py` writes `reports/dependency-graph.md`: the dependency graph and the deterministic execution order.

**Outputs.** Dependency fields on the records; prioritised backlog; dependency graph.

**Gate G10 — Sequencing ready.** A priority scheme is declared and every in-scope item uses it; every in-scope task's dependencies are reviewed; no dependency cycle or impossible sequencing. Warnings: hidden prerequisites, features blocked by decisions, unconfirmed priorities, external dependencies not yet available, more than 60% of prioritised requirements at the top priority.

### 10B — Backlog Readiness Validation

**Purpose.** Turn the backlog from a generated task list into a validated, execution-ready planning artifact. Tasks existing is not the backlog being ready: every READY task has earned it, what is not ready says why, and what can start now is known.

**Inputs.** The sequenced backlog; the specification review; the architecture review; change state; the risk register.

**Activities.**
- Run `python tools/generate_handoff.py projects/<project>` (or `python tools/backlog_readiness.py projects/<project>`). Every task's Definition of Ready is evaluated. The results are written to `backlog/readiness-report.md` and `machine-handoff/backlog-readiness.json`:
  - the backlog status — READY (every active task), PARTIALLY_READY (a valid subset) or NOT_READY;
  - counts by status and the ready percentage;
  - for each task: its result, the failed checks, the failures, the status they point to, its priority and sequence, revision, related risks and accepted-risk findings;
  - the validation summary: dependency cycles, architecture conflicts, traceability, unresolved critical findings and serious findings affecting the backlog, critical blockers, approval of scope;
  - each phase's status and its planning-completeness questions;
  - the ready work sets;
  - coverage metrics and flags for review.
- **Set each task to the status its checks support.** READY only when every check passes. When a check fails, the task takes the status the failures point to: NEEDS_REVIEW, NEEDS_DISCOVERY, BLOCKED or DRAFT. Record every transition in the task's readiness history. A task a change reaches loses READY until it is revalidated (section 19.5). Revalidation is automatic on every run; the people revalidate only what the impact analysis shows is affected.
- **Answer the planning-completeness questions for every phase before calling it ready.** Do we know what needs to be built? Why does it need to exist? What requirement supports it? What does success look like? What does it depend on? What constraints apply? What could block it? How will completion be verified? A phase whose tasks cannot answer them is not ready.
- **Allow partial readiness.** The whole project does not have to be resolved before useful work begins: Phase 1 may be READY while Phase 2 NEEDS_DISCOVERY and Phase 3 is BLOCKED. The **ready work sets** name what can run now. WS-01 holds READY, in-scope tasks that pass the Definition of Ready and depend on nothing; each later set holds tasks whose prerequisites all sit in earlier sets. Work depending on anything not ready is in no set. Downstream engineering (SoftwareFactory) consumes these sets.
- **Review the flags.** They are heuristics for a person, never automatic changes:
  - *NEEDS_DECOMPOSITION* — a task that spans several modules, workflows, actors or integrations, or lists several objectives. Not judged by text length.
  - *FRAGMENTATION* — microtasks that deliver one cohesive behaviour between them.
  - *POSSIBLE_DUPLICATE* — overlapping objectives. Never merge without confirmation.
  - *CONTRADICTION* — two tasks that cannot both hold, traced back to their requirements.
  - *MISSING_ERROR_BEHAVIOUR* — only the failure cases relevant to the task.
  - *VERIFICATION_GAP* — impacts that the required test levels do not verify.
  - *IMPLEMENTATION_STEP* — a title that reads as a coding instruction.
- **Use the coverage metrics to expose gaps, not as targets**: requirements with implementation coverage, features with tasks, tasks with valid acceptance criteria and dependencies, architecture-relevant tasks with ADR links, tasks needing review.

**Outputs.** `backlog/readiness-report.md` (generated); `machine-handoff/backlog-readiness.json` (generated); task statuses and readiness histories; `backlog_status` in `project.json`.

**Gate GB — Backlog ready.** The gate fails when any of these holds:
- no task exists, or no in-scope task is READY and passes the Definition of Ready (the backlog is NOT READY);
- a dependency cycle exists, or a READY task fails a Definition of Ready check;
- a CRITICAL specification review finding is unresolved, or an unresolved CRITICAL or MAJOR finding affects the active backlog;
- an active task has an unresolved architecture conflict;
- traceability is broken: a task without requirement, feature or acceptance criteria, a task tracing only to superseded or rejected requirements, an in-scope feature with neither tasks nor a reason, or an in-scope requirement no task implements;
- scope approval is missing (the specification is not approved, or its review does not pass);
- the readiness history disagrees with a task's status, or records READY without its validation;
- a task changed since the baseline without a new revision.

Warnings: a PARTIALLY READY backlog, each active task not yet READY with what blocks it, tasks that pass the Definition of Ready but are not marked READY, and every flag.

**Move on when** GB passes. Nothing is called backlog-ready or implementation-ready while it fails.

## 16. Stage 11 — Roadmap and Project Plan

**Purpose.** Phase the work according to dependencies, priority, risk, milestones and external constraints — honestly.

**Inputs.** The sequenced backlog; the risk register; stakeholder deadlines; confirmed capacity if any.

**Activities.**
- Group tasks into phases (`PHASE-##` in `backlog/backlog.md`) named by outcome — for example Foundation, Core Product, Operations, Enhancement, Launch Preparation. Every in-scope task belongs to a phase; phases run in ID order and no task sits in an earlier phase than its predecessor.
- Give each phase an objective and exit criteria. Cover the applicable planning categories — design, UI/UX, build, integrations, testing, UAT, deployment, training and post-launch support — as outcomes, not as a mandatory waterfall. Completed planning stages link to evidence instead of fabricated cards.
- Distinguish **target**, **estimate** and **commitment** for every date. A commitment cites the decision that records it. Without confirmed capacity there are targets or no dates, never estimates. Use XS–XL complexity with stated drivers; do not convert it to calendar time by assumption.
- Let risks change the plan: bring risky work forward, add mitigation outcomes, hold work behind pending decisions. Every open high risk has a mitigation and a named owner.

**Outputs.** Roadmap phases; the project plan (`templates/22` when the package is produced); the updated risk register.

**Gate G11 — Roadmap ready.** Phases exist with objectives and exit criteria; every in-scope task is scheduled; phase order respects dependencies; every date has a basis and every commitment a decision; every open high risk has a mitigation and an owner. Warnings: target dates, an empty risk register.

**Move on when** G11 passes.

## 17. Stage 12 — Traceability Validation

**Purpose.** Prove that the whole plan hangs together before anything is packaged.

**Inputs.** All records; the gate report.

**Activities.**
- Validate the chain for every in-scope item: GOAL → BR → FR/NFR/DR/IR/SR/UXR/TR → MOD → FEAT → TASK → AC → TEST, and the architecture chain requirement → ADR → feature → task, which explains why each technical constraint exists. Detect and fix orphaned requirements, features and tasks.
- Run `python tools/generate_handoff.py projects/<project> --check`: it validates every reference, derived link, the Definition of Ready and coverage, and writes nothing. Review `traceability/traceability.md` (`templates/10`) against the generated `traceability/requirement-map.md`.
- Run the final planning review (`templates/34`): no unresolved blocker affects in-scope work; approved scope is clear; requirements are consistent; major workflows are defined; requirements and backlog items are traceable; the dependency graph is valid; major risks are documented; the roadmap reflects dependencies; accepted architecture decisions are respected downstream; assumptions and open decisions are visible.

**Outputs.** `reviews/final-planning-review.md`; a clean handoff check.

**Gate G12 — Planning validated.** Every earlier gate passes; the handoff check reports no errors; no orphan and no coverage gap in scope; the final review covers the current version with a complete checklist and no open CRITICAL or MAJOR finding. Remaining open questions are reported as warnings so they stay visible.

**Move on when** G12 passes. The final package is produced only now.

## 18. Stage 13 — Final Planning Package

**Purpose.** Produce the planning package from the validated plan, for people and for machines.

**Inputs.** The validated records (G12).

**Activities.**
- Write `deliverables/planning-summary.md` (`templates/36`), which answers the fifteen questions every plan must answer: what problem we are solving; for whom; what is in and out of scope; what the system should do; which constraints it respects; the major workflows; the major modules and features; which requirements support each feature; what work is needed; what depends on what; what happens first; what risks exist; what is still unknown; what was decided.
- Generate the diagrams (section 21), author the seven stakeholder deliverables and the manifest, and build the Word and Excel files (section 22).
- Generate the machine handoff (section 23).
- Open and verify every export; record the results in the package manifest.

**Outputs.** Planning summary; deliverables and their builds; diagrams; `machine-handoff/`; the planning handoff (`templates/13`).

**Gate G13 — Planning package ready.** The planning summary answers all fifteen questions; every deliverable and the manifest exist and are built; the manifest's export verification and consistency checklists are complete; the machine handoff is valid, current and `ready`; no deliverable mentions an ID that no record defines or disagrees with the task cards.

## 19. Continuous disciplines

### 19.1 Risk management

`discovery/risks.md` is started at intake and updated in every stage — not assembled at the end. Each risk records ID, description, category (scope, technical, business, dependency, integration, security, data, timeline, stakeholder), probability, impact, mitigation, owner and status. Risks change the plan: a discovery risk can create a question or requirement, a sequencing risk can reorder phases. Do not invent probabilities as percentages or owners; use qualitative levels with their basis and `TBD (Q-###)` for an unknown owner.

### 19.2 Decision log

`discovery/decisions.md` records every decision that settles a question, chooses between options, changes scope or confirms a priority: decision ID, date, question, options considered, decision, rationale, impact, approved by and related requirements. It exists so that the same issue is not reconsidered without its context. A reversal is a new decision that supersedes the old one; the old row stays. A significant architecture decision is also recorded as an ADR (section 11), and its human approval is the decision-log entry the ADR cites as *Approval evidence*.

### 19.3 Traceability

Traceability is maintained from the first requirement, not generated at the end. Every requirement names what it serves; every feature and task names what it implements. `tools/generate_handoff.py` derives the reverse links and reports orphans; `tools/check_gates.py` fails the gates they belong to. Every backlog item has a reason to exist.

### 19.4 Confidence and uncertainty

Uncertainty is communicated, never hidden to make a document look complete. Confidence levels (section 4) travel with every requirement, process and entity; open questions, open assumptions and pending decisions are listed in every review and in the final package. Where appropriate, the planner states plainly: *this is unresolved*.

### 19.5 Change-impact analysis

A project evolves; the plan must not continue on outdated assumptions. Once a baseline exists, every meaningful change is a **change record**, analysed through the links the records hold, decided by a person, and resolved in the plan — never a text edit. The system must be able to answer, for any change: what changed and why; what directly and indirectly depends on it; what is now stale or invalid; what must be reviewed; what new work may be required; which risks and roadmap items changed; and which documents need regenerating.

**The baseline.** At specification approval (stage 8B), and again whenever an implemented change should become the new trusted state, record the baseline:

```bash
python tools/analyze_change_impact.py projects/<project> --baseline --reason "Specification 1.0 approved"
```

`changes/baseline.json` holds the normalised text of every change-controlled record — requirements and rules, workflows, entities, modules, ADRs, principles, scope items, and, once they exist when the baseline is taken, epics, features, phases, tasks and tests. A backlog item's planning *Status* is not change-controlled; its content is. The tools compare the current records with the baseline on every run, so an edit with no approved change record is detected, whoever made it, and the previous value is always recoverable. A new baseline is refused while any change is unrecorded, approved but not implemented, or implemented with artifacts still under review; the previous baseline is archived in `changes/history/`.

**Change records.** `changes/CHANGE-###.md` (`templates/35`), one change per file, IDs never reused. Each states its type — REQUIREMENT_CHANGE, ARCHITECTURE_CHANGE, SCOPE_CHANGE, BUSINESS_RULE_CHANGE, WORKFLOW_CHANGE, FEATURE_CHANGE, DATA_CHANGE, INTEGRATION_CHANGE, SECURITY_CHANGE, PRIORITY_CHANGE, DEPENDENCY_CHANGE or ROADMAP_CHANGE, never one generic type — the changed artifacts, who requested and who approved it with evidence, the previous and new state, the reason, the affected artifacts with their dispositions, the required reviews, and the risk, roadmap, new-work and document impact.

**Lifecycle.**

```text
Change requested → PROPOSED → impact analysis (UNDER_ANALYSIS) → human review → APPROVED or REJECTED
  → affected planning artifacts updated → IMPLEMENTED_IN_PLAN          (SUPERSEDED when a later change replaces it)
```

A PROPOSED or UNDER_ANALYSIS change does not alter the authoritative plan: nothing is marked, and an affected record edited before approval is reported. A REJECTED change leaves its artifacts at their baseline state.

**Analysis.** `python tools/analyze_change_impact.py projects/<project> CHANGE-007` (or `FR-021 --type REQUIREMENT_CHANGE` for a what-if without a record) runs ten steps: identify the changed artifacts; load the relationships; detect direct dependencies; detect downstream dependencies; detect upstream assumptions; classify impact; calculate severity; mark affected items for review; withdraw readiness where necessary; write `changes/CHANGE-###-impact-report.md`. It follows the impact graph — goal → business requirement → requirement → ADR → module → feature → task → acceptance criteria and tests → roadmap phase, plus workflows, entities, pages, API and integration contracts, risks, questions and decisions — and never relies on keyword matching alone.

| Classification | Meaning |
| --- | --- |
| DIRECT | One link away from a changed artifact |
| INDIRECT | Further away, through records that pass impact on (requirements, modules, ADRs, external dependencies, features, tasks) |
| POTENTIAL | An upstream assumption (the requirement a changed one derives from), a requirement sharing a module, or a record that only mentions the change |
| CONFIRMED / LIKELY / POSSIBLE | Every link on the path is an explicit dependency / a membership or context link is on the path / the link is inferred |

Impact is never presented as equally certain, and indirect impact is never hidden.

**Severity** is computed, explained and never understated: **CRITICAL** — the plan may be fundamentally invalid (the business basis changed under in-scope work, or an accepted ADR reaching several modules changed); **HIGH** — several planning artifacts need review (READY tasks lose readiness, two or more features, eight or more planning artifacts, an architecture or security change with downstream planning, a committed phase); **MEDIUM** — a limited downstream review; **LOW** — documents or context only. A change record may declare a higher severity, never a lower one.

**Review states.** Every artifact is CURRENT, NEEDS_REVIEW, STALE or INVALID. The state is derived, never typed into the artifact: an APPROVED change makes every DIRECT and INDIRECT artifact NEEDS_REVIEW until its row in the change record says otherwise (STALE — out of date, must be updated; INVALID — no longer valid; CURRENT — reviewed, with a resolution). An unrecorded change makes the changed record and everything it reaches NEEDS_REVIEW. Nobody can mark an affected artifact CURRENT except by recording its review.

**Readiness.** The Definition of Ready includes "not under change review" (`not_stale`): a READY task that a change reaches, or whose foundation changed without a record, fails the Definition of Ready until the change record dispositions it CURRENT. Set it to NEEDS_REVIEW with a readiness history entry naming the change; if its own definition changes, increment its revision. A readiness transition is not itself a change: the readiness history is outside change control. Sequencing is re-validated on every run, so a task whose new predecessor is BLOCKED is no longer actionable.

**Consequences the analysis reports.** *Required reviews* per change type (for a requirement change: dependent requirements, ADRs, workflows, modules, features, tasks, acceptance criteria, entities, APIs, UI screens, security, integrations, roadmap, risks, traceability, deliverables), each with the records found or "none found — confirm". *New work*: a changed requirement with no feature or task, an acceptance criterion no task or test covers, criteria gained since the baseline, modules no feature covers — and always a prompt to confirm that existing tasks cover the new state, because they are never assumed to. *Roadmap*: the affected phases, and that they need re-estimation; committed dates to reconfirm; no invented timing. *Risks* linked to the change, to record as NEW, INCREASED, REDUCED or RETIRED. *Documents* that mention an affected artifact and need regenerating — and only those.

**Applying an approved change.** Update the affected records; disposition every DIRECT and INDIRECT artifact; complete every required review; record the new work as records, the risk and roadmap impact; re-review the specification in a new review cycle, because propagation is verified, never assumed — gate GR fails while an approved change of MEDIUM or higher severity is dated after the latest review (section 13); regenerate the handoff and the deliverables the report lists; set *Current stage* back to the earliest affected stage (the report names the gates to re-run) and re-run the gates; then mark the change IMPLEMENTED_IN_PLAN and, when the plan is again trusted, record a new baseline. A new specification version needs approval before affected tasks return to READY; unchanged approved content keeps its approval. Traceability is regenerated from the updated records, and orphans the change creates — a feature with no live requirement, a task with no active feature, an accepted ADR with no consumer, a phase with no active task — are flagged for review.

An accepted ADR is never edited to change direction, before or after approval: the change is a new ADR that supersedes it (section 11), recorded as an ARCHITECTURE_CHANGE. Dependent records are updated only after the impact analysis has been reviewed — never rewritten blindly. Before a baseline exists, drafts are updated directly, but decision history is still kept.

**Gate GC — Change impact reviewed.** A continuous gate, evaluated on every run and required by G12 and G13. It fails when a change-controlled record differs from the baseline with no approved change record (or before its change was approved, or although it was rejected); a decided change names no approver and evidence; an approved or implemented change does not state its previous and new state; a declared severity is below the computed one; CRITICAL impact is unresolved; a change is IMPLEMENTED_IN_PLAN while an affected artifact is not CURRENT, a disposition lacks a resolution, a required review is pending, the new work, roadmap or (for HIGH and CRITICAL) risk impact is not stated, a required stakeholder decision is open, a changed artifact is unchanged since the baseline, or a resolution claims an edit the records do not show; a READY task is under review; or, whenever a change exists, the plan still carries architecture conflicts, roadmap contradictions, dependency cycles, broken references or traceability defects. It warns about approved changes still under review, orphans, retired risks still open, and an approved specification with no baseline.

The project-level change state — open changes, critical changes, items needing review, stale tasks, invalid READY tasks, unrecorded changes — is in `machine-handoff/changes.json`, the gate report and `analyze_change_impact.py --summary`.

### 19.6 Architecture drift

Once an ADR is accepted, downstream planning respects it until it is explicitly superseded or deprecated. No later stage introduces a conflicting architecture choice because it seems convenient for one feature. `tools/validate_handoff.py` reports every live requirement, feature or task that names an inactive ADR, and searches requirements, features and tasks for options an accepted ADR considered and rejected; `tools/check_gates.py` fails the gate of any such ARCHITECTURE CONFLICT that is not recorded and dispositioned in `reviews/architecture-review.md`. The review is repeated whenever an ADR changes status or a conflict is reported; its counts are compared with the records, so a stale review cannot pass.

## 20. Quality gates

Every stage ends in a gate. `tools/check_gates.py` evaluates all thirteen from the records, together with the independent-review gate GR that closes stage 8A (section 13), the backlog-readiness gate GB that closes stage 10B (section 15) and the continuous change-impact gate GC (section 19.5), and reports each as:

| Result | Meaning |
| --- | --- |
| PASS | Every automated criterion is met |
| PASS WITH WARNINGS | Criteria are met; the listed warnings need a recorded disposition |
| FAIL | At least one mandatory criterion fails; the exact reasons are listed |

```bash
python tools/check_gates.py projects/<project>              # all gates, reports/gate-report.md and reports/architecture-report.md
python tools/check_gates.py projects/<project> --gate G3    # one gate in detail
```

| Gate | Stage exited | Checks, in summary |
| --- | --- | --- |
| G1 — Intake complete | 1 | Fourteen intake items classified; Project ID |
| G2 — Discovery ready | 2 | Fourteen categories investigated; registers exist; no uncontained BLOCKER |
| G3 — Requirements ready | 3 | Complete, confirmed, traceable requirements; lint; requirement review complete |
| G4 — Models ready | 4 | Complete process and entity records; valid references |
| G5 — Solution and scope ready | 5 | Classified modules; requirement-to-module mapping; scope classified; pending items have questions |
| G6 — Architecture ready | 6 | Every architecture concern classified; ADRs registered, approved by a named owner, consistent and free of active conflicts; no critical decision hidden; architecture review complete and current |
| G7 — Specification complete | 7 | 26 sections; no undefined IDs; in-scope requirements and accepted ADRs referenced |
| GR — Specification reviewed | 8A | Independent review of the current version by a reviewer who is not the author; complete checklist and questions; evidenced REVIEW-### findings; stated result and counts supported; history frozen; contradiction candidates judged; no change after the review; no unresolved CRITICAL/MAJOR |
| G8 — Specification ready | 8B | GR passes; approved after a passing review of this version; in-scope requirements approved |
| G9 — Backlog decomposed | 9 | Requirements covered by features and tasks; features have tasks or a reason; no orphans; no reliance on inactive ADRs; conflicts reviewed |
| G10 — Sequencing ready | 10A | Priority scheme; priorities set; dependencies reviewed; no cycles or impossible sequencing |
| GB — Backlog ready | 10B | Some in-scope work READY and passing every Definition of Ready check; no READY task failing one; no cycle, open architecture conflict, serious finding on the backlog or broken traceability; scope approved; readiness history and revisions honest |
| G11 — Roadmap ready | 11 | Phases with objectives and exit criteria; tasks scheduled; honest dates; risks owned |
| G12 — Planning validated | 12 | Full validation clean; no orphans or coverage gaps; final review complete |
| G13 — Planning package ready | 13 | Planning summary; built and verified deliverables; valid, current, ready handoff |
| GC — Change impact reviewed | continuous | No unrecorded change; every change decided by a person and resolved in the plan; no READY task under review; no contradiction left by a change. Required by G12 and G13 |

Rules that make the gates binding:

- **A gate cannot pass on a failed earlier gate.** Every later gate reports "Prerequisite gate Gn fails"; GR sits between G7 and G8, so a failed review fails approval and everything after it. G12 and G13 also fail while GC fails: a plan with unresolved change impact is not validated.
- **The current stage cannot outrun the gates.** If `project-state.md` says the project is at stage *k*, gates 1 to *k*−1 must pass; otherwise the tool reports a violation and exits non-zero.
- **A claim cannot outrun the evidence.** Recording PASS in `project-state.md` for a gate that fails, or PASS for one that passes only with warnings, is a violation. So is a specification review summary (result, cycle, open findings, accepted risks) that differs from what the review records show. Record the result the tool printed, with its date.
- **Judgement is recorded, then checked.** What a tool cannot decide — whether a requirement is right, whether two statements contradict — is recorded in a review with a checklist and severity-classified findings. The gate checks that the review is complete and current and that no serious finding is open. A blank checklist is not a pass.
- **Automated checks are not the whole review.** A passing gate means the records meet every checkable criterion; it does not mean the plan is correct. Say so when reporting.

Gates govern project records. Creating or changing the reusable workflow and its blank templates needs no project approval.

## 21. Diagram generation

Once the process model and data model are confirmed, generate the project's diagrams before authoring the deliverables that embed them. A diagram is a view of a confirmed model. It shows what the model states and nothing else; a lane, gateway, table, column or relationship that appears only in a picture is an invented requirement.

### Tools

| Diagram | Tool | Output | Specification |
| --- | --- | --- | --- |
| BPMN process diagrams, AS-IS and TO-BE | Excalidraw diagram skill — [coleam00/excalidraw-diagram-skill](https://github.com/coleam00/excalidraw-diagram-skill) | `.excalidraw` source plus a rendered PNG | `templates/24-bpmn-process-diagrams.md` |
| Entity-relationship model of the proposed database, entity state diagrams, data flows | draw.io diagram skill — [Agents365-ai/drawio-skill](https://github.com/Agents365-ai/drawio-skill) | `.drawio` source plus an exported PNG or SVG | `templates/25-er-data-diagrams.md` |

Both skills are provisioned by the workflow's own installer:

```bash
python tools/setup_workflow.py --check     # report readiness, change nothing
python tools/setup_workflow.py             # install what is missing
```

It clones each skill, locates the skill directory inside the repository — one of them publishes its skill under `skills/<name>/` rather than at the root — installs it where the assistant will discover it, installs the document-builder and validator packages, and prepares the Excalidraw render pipeline with `uv` when present and a virtual environment otherwise. It is safe to re-run and leaves alone any skill another installation already provides. The report also covers optional pieces — the draw.io desktop CLI for image export and Graphviz for automatic layout — and ends with a render smoke test, because the Excalidraw render page imports its library from `esm.sh` at render time and a restricted network breaks verification with no obvious symptom.

Where a skill is unavailable, say so and stop rather than hand-drawing a substitute and presenting it as generated output. Both tools draw whatever they are told to draw; neither checks a claim against a source record. That is done by completing the diagram specification before generating anything.

### Specify before drawing

Complete the diagram record in `templates/24` or `templates/25` first: participants, flow elements, gateway conditions, message flows, end events, or tables, columns, keys, relationships and states. Each row names the confirmed record it comes from. Draw AS-IS and TO-BE as separate diagrams; never overlay a proposed change on an observed process.

### Accuracy rules

- Every element traces to a confirmed record. Unknown behaviour is an annotation naming its open question, outside the confirmed flow — never a guessed gateway, relationship or constraint.
- Rejection, cancellation, delegation and failure paths appear where the model confirms them and are absent where it does not.
- Lane names match confirmed `ROLE-###` records; data objects and tables match confirmed `ENT-###` records; states match the entity-scoped `STATE-###` transitions exactly.
- The ER diagram shows a **proposed physical model** derived from the confirmed domain model. Surrogate keys, join tables, audit columns, indexes and denormalisation are design proposals and are listed as such.
- Optionality, cardinality and delete behaviour that the business has not confirmed stay `TBD (Q-###)`.

### Label the artifact honestly

An Excalidraw drawing in BPMN notation is a notation-conformant process diagram, not a BPMN 2.0 XML interchange file, and it will not run in a BPMN engine. Carry that statement in the caption. If an executable or interchangeable BPMN file is genuinely required, record it as a separate confirmed requirement with an owner and a tool decision. The data model's caption states that it is a proposed physical model pending implementation acceptance.

### Verify

Render every diagram, open the image and look at it. The Excalidraw skill's render-view-fix loop is mandatory and typically takes several iterations; record how many were run. Complete both the visual and the tracing checks in the diagram template. A diagram that was generated but never viewed is unverified, and a diagram that renders cleanly can still assert something no record supports.

### Store and embed

Keep editable sources (`.excalidraw`, `.drawio`) in `projects/<project>/diagrams/source/` and rendered exports (PNG, SVG) in `projects/<project>/diagrams/exported/`. Embed an export in a deliverable with a captioned image reference relative to the Markdown file:

```markdown
![DIAG-001 — Purchase approval, TO-BE. Drawn in BPMN 2.0 notation; not a BPMN 2.0 XML interchange file.](../diagrams/exported/diag-001-purchase-approval-tobe.png)
```

The build tool embeds the image, scales it to the text column and renders the caption beneath it. A missing image file is a build error. Keep the DIAG ID first in every caption. Regenerate a diagram whenever its source model changes, and rebuild the documents that embed it.

## 22. Deliverable document package

The package restates the validated plan for its audiences and adds nothing. It is produced in stage 13, after gate G12.

| Deliverable | Template | Answers |
| --- | --- | --- |
| Project Planning Summary | `templates/36-planning-summary.md` | The fifteen questions every plan must answer |
| Product Requirements Document (PRD) | `templates/16-prd.md` | What the product does, for whom, which features are in the MVP, how success is measured |
| Business Requirements Document (BRD) | `templates/17-brd.md` | Why the organisation is funding this, the business objectives, the justification and the financial expectations |
| Software Requirements Specification (SRS) | `templates/18-srs.md` | System architecture, data model, interfaces, functional and non-functional behaviour, security rules and APIs |
| Statement of Work and Scope Statement (SOW) | `templates/19-sow-scope-statement.md` | Deliverables, boundaries, the strict MVP set, milestones, acceptance and change control |
| User Journey and User Stories | `templates/20-user-journey-stories.md` | End-to-end journeys, pain points, epics, the story backlog and acceptance criteria |
| Wireframes and UI/UX Design Specification | `templates/21-wireframes-uiux.md` | Information architecture, screen layouts, component states, interactions and asset handoff |
| Project Plan and Roadmap | `templates/22-project-plan-roadmap.md` | Phases, milestones, sprints, task sequence, dependencies, resources and RACI |
| Deliverable Package Manifest | `templates/23-deliverable-package.md` | What was generated from which source, the generation log and the export verification |

Deployment documentation, user guides and test execution evidence may require an implemented system. Establish their required content and owner during planning; never label a placeholder as completed implementation evidence.

### Authoring rules

Author each deliverable as Markdown in `projects/<project>/deliverables/`. Every statement traces to an approved record. A sentence that appears in a deliverable and in no source record is a defect; raise it as a change record `CHANGE-###` rather than writing it in. If the user asks for the package before G12, produce it from what is approved, mark every unresolved area `TBD (Q-###)`, and state plainly in the manifest which gates are still open.

Each document carries exactly one canonical version of any shared content, and the others reference it:

| Content | Canonical location | Referenced from |
| --- | --- | --- |
| MVP feature set | PRD section 6.1, restated identically in SOW section 5 | Roadmap, story map |
| Personas | PRD section 4 | User Journey document |
| Business objectives and KPIs | BRD section 5 | PRD success metrics |
| Requirement behaviour | SRS section 6 | PRD features, user stories |
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

Build with `python tools/build_deliverables.py projects/<project>/deliverables --project "<name>"`. Run `--check` first and resolve its errors. See [tools/README.md](tools/README.md). Generated files are output, never source: regenerate after any change to an approved record and never hand-edit an export. Record every run in the manifest generation log.

### Verification

A clean build means the files were written, not that they are right. Open each exported file, refresh the Word fields, and complete the export verification and cross-document consistency checklists in the manifest. Report what was actually inspected; an unopened export is unverified, and gate G13 fails while those checklists are incomplete.

## 23. Machine handoff

The machine handoff is the integration contract between this workflow and downstream engineering automation such as SoftwareFactory. It is JSON, generated deterministically from the source records, validated against the versioned schemas in `schemas/`, and never edited by hand. Every value in it comes from a Markdown record; a fact that exists only in the JSON is a defect.

### Canonical structured records

The generator reads only structured parts of the records, never free prose:

| Record | Source file | Template | JSON |
| --- | --- | --- | --- |
| Project identity, priority scheme, specification status, approval | `project-state.md` | 00 | `project.json` |
| Goals, business requirements, rules, FR, NFR, DR, IR, SR, UXR, TR | `specification/*-requirements.md`, `specification/business-rules.md` | 26 | `requirements.json` |
| Scope register | `specification/scope.md` | 33 | `requirements.json` |
| Processes and entities | `specification/process-model.md`, `specification/domain-model.md` | 03, 32 | `domain.json` |
| Modules | `specification/solution-structure.md` | 37 | `architecture.json` |
| Architecture decisions, principles, concern coverage | `architecture/ADR-###-*.md`, `architecture/principles.md`, `architecture/architecture-register.md` | 28, 38, 27 | `architecture.json` |
| Decisions, questions, assumptions, risks, sources | `discovery/decisions.md`, `open-questions.md`, `assumptions.md`, `risks.md`, `sources.md` | 02 | `decisions.json`, `requirements.json` |
| External dependencies, epics, features, phases | `discovery/dependencies.md`, `backlog/backlog.md` | 02, 07, 09 | `backlog.json` |
| Tasks | `backlog/tasks/TASK-###.md` | 08 | `tasks/TASK-###.json`, indexed in `backlog.json` |
| Test definitions | `quality/acceptance-tests.md` | 11 | `tests.json` |
| Change records, baseline | `changes/CHANGE-###.md`, `changes/baseline.json` | 35 | `changes.json` |
| Backlog readiness: every task's Definition of Ready result, work sets, phases, flags | derived from the task and backlog records | — | `backlog-readiness.json`, `backlog/readiness-report.md`; `backlog_status` in `project.json` |
| Independent specification review: findings, cycles, result | `reviews/specification-review.md`, `reviews/history/specification-review-cycle-###.md` | 12 | `specification-review.json`; summary in `project.json` |
| Traceability | derived from all of the above | — | `traceability.json`, `traceability/requirement-map.md` |

A rich record — requirement, process, entity, ADR, epic, feature, phase, task, test — is a *record block*: a heading that begins with its ID, a `| Field | Value |` table, and labelled sections. A short record — question, decision, assumption, risk, dependency, source, module, principle, scope item — is a row in a *register table* whose first column is its ID. Each relationship is written in one direction only and every reverse link is derived, which is what makes the output deterministic and free of internal contradiction.

### generate-machine-handoff

```bash
python tools/generate_handoff.py projects/<project>            # generate, validate, write
python tools/generate_handoff.py projects/<project> --check    # validate only, write nothing
python tools/validate_handoff.py projects/<project>/machine-handoff   # re-validate what was written
```

The command runs eight steps and prints each result: (1) validate the specification — identity, status and approval record; (2) validate the requirements; (3) validate backlog readiness, evaluating the Definition of Ready for every task; (4) generate the JSON artifacts; (5) validate them against the schemas; (6) validate traceability and every reference; (7) report blocked and non-ready tasks with their reasons; (8) write `handoff-manifest.json` and print the handoff summary:

```text
Specification: APPROVED (version 1.0)
Specification review: PASS WITH WARNINGS (cycle 2)
Machine handoff: VALID
Handoff status: ready
Backlog readiness: PARTIALLY READY
Ready tasks: 18
Blocked tasks: 3
Errors: 0
Warnings: 2
Schema version: 1.5
Integration contract: 1.0
Handoff manifest: READY_FOR_HANDOFF (handoff 1.3, written)
Ready for handoff: TASK-001, TASK-004, TASK-007, …
```

Copy that summary into `project-state.md` and the planning handoff exactly as printed. Never state that the handoff is valid or ready without having run the command against the current records.

### What validation checks

JSON syntax; conformance to every schema; unique IDs; that every referenced ID exists; dependency cycles among tasks, features, parents, requirement derivation, modules and ADR supersession; the Definition of Ready for every READY task, as named checks, and each task's stored readiness evaluation and readiness history; `backlog-readiness.json` recomputed from the tasks; the independent specification review — its result and counts recomputed from its findings, no CRITICAL finding accepted as a risk, every closed finding with a resolution, every cycle listed, and agreement with the summary in `project.json`; acceptance criteria for in-scope requirements; the priority scheme; hidden prerequisites and impossible sequencing; unsupported roadmap commitments; review states derived from the change records, and readiness withdrawn from tasks under change review; orphan features and tasks; that `backlog.json`, the task files and `traceability.json` agree with each other and with the records they derive from; that the index in `backlog/backlog.md` agrees with the task cards; architecture governance — ADR references, lifecycle and approval, supersession, conflicts between active decisions, references to inactive decisions and drift from rejected options; artifact hashes, so a hand-edited or leftover file is detected; every task's content hash, recomputed; conformance of every task, requirement and ADR to the integration contract's consumer views; staleness against the current Markdown; that `project.json` claims no better `handoff_status` than the evidence supports; and that `handoff-manifest.json` agrees with every file it lists and claims no better status or validation flag than the evidence supports.

`handoff_status` is `ready` only when there are no errors, the specification is approved, its independent review passes (PASS or PASS_WITH_WARNINGS) for the current version, and at least one task is READY; `not_ready` when valid but nothing may be handed off yet; `invalid` otherwise. When validation fails the handoff is still written — marked `invalid`, with `validation-report.json` listing every finding — so an earlier `ready` output never survives beside changed records.

### Consuming the handoff

A downstream system reads `handoff-manifest.json` first and only through it: it checks the contract `schema_version`, requires `handoff_status: READY_FOR_HANDOFF` and every validation flag true, verifies every listed file against its SHA-256, and takes only the tasks in `ready_tasks`, in that order. It never scans the project folders to discover work. It may also re-run `tools/validate_handoff.py` on the copy it received. `specification-review.json` carries the independent review: the reviewed version, the cycle, reviewer and author, the overall result (PASS, PASS_WITH_WARNINGS, FAIL or NOT_REVIEWED), the counts, every cycle with its date and counts, every REVIEW-### finding with its severity, category, status, affected artifacts, evidence and resolution, and any defect the tools found in the review record — which alone makes the result FAIL. `changes.json` carries the change state: the baseline, the records changed since it and those no approved change accounts for, every change with its classified impact, severity and consequences, the review state of every artifact that is not CURRENT, and a summary for dashboards. `architecture.json` carries the architecture state — a status summary, the principles, the modules, the concern coverage and every ADR with its constraints, consequences, alternatives and links; requirements and features carry the ADRs that apply to them, and `traceability.json` lists for each ADR the requirements, features and tasks it reaches. The ADR Markdown stays the source of truth. Each task file carries everything needed to plan the work — source requirements, scope, acceptance criteria, constraints, the ADRs that apply and why, external dependencies, verification method, predecessors — plus the remaining card sections as structured `details`. Traceability records carry empty `pull_requests`, `commits` and `releases` slots for downstream engineering to extend the chain. The schema version changes only when the contract does; a consumer rejects a version it does not know.

### Engineering boundary

The machine handoff is the only channel to downstream engineering (SoftwareFactory): a versioned, file-based contract, with no API, queue or agent-to-agent conversation. ProjectPlanner defines what must be achieved — requirements, scope, specification, architecture decisions, features, tasks, acceptance criteria, dependencies, readiness and traceability. The engineering system determines how the existing repository achieves it — repository inspection, implementation strategy, code-level planning, branches, code, tests, security checks, commits and pull requests. A task states outcomes and constraints; a file, module, table or endpoint name appears in it only as an approved constraint (an accepted ADR or a recorded task constraint), never as a planning guess.

- **Contract.** `schemas/integration/` is the canonical contract: `handoff-manifest.schema.json`, the consumer views `task-handoff`, `requirement-reference` and `architecture-reference`, and the engineering side's `factory-status` and `factory-intake-report`. `contract.json` locks their hashes; `python tools/handoff_contract.py --check-lock` fails when a schema changed without it. The manifest's `schema_version` is the contract version (1.0), separate from the planner's file-format version (`planner_schema_version`, 1.5). The generated files are validated against the consumer views, so a planner change that would break the consumer fails here first. Removing, renaming or narrowing a field the views name is a new contract version.
- **Identity.** Every task carries `revision` — increment it on the card whenever the task's definition changes materially after validation — and `content_hash`, a SHA-256 over the task's content and the requirements and ADRs it relies on (basis `task-intent/1`; timestamps, status and readiness bookkeeping excluded). A changed requirement statement changes the hash of every task built on it. The manifest lists each task's revision, status and hash, so a consumer detects a planning change without re-reading the package.
- **Version label.** `handoff_version` is `1.0` for a first handoff, keeps its value while the content fingerprint is unchanged, increments its minor number on any content change, and starts a new major number with a new specification version.
- **Engineering status.** The engineering system writes its own status per task (`factory-status.schema.json`: accepted, inspected, planned, implementing, validating, PR created, blocked, completed, planning changed, rejected — with the branch and pull request). Those statuses belong to engineering. The planner may later display them as external status; they never change a planning status or a record, and they never count as planning evidence. Rejections name their owner — `PROJECT_PLANNER`, `SOFTWARE_FACTORY` or `HUMAN_DECISION` — and a `PROJECT_PLANNER` rejection is a planning defect to fix in the records here, then regenerate.

## 24. Handoff and persistence

Use `templates/13-handoff.md`. Deliver the approved specification and the task cards with their supporting records, the planning summary, the generated deliverable package and its manifest, and the machine handoff. Include the active revision, approval evidence, the gate report, the specification review result with its open findings and accepted risks, requirement/task/test coverage, the first executable tasks, known external prerequisites, open questions and assumptions, and every remaining non-blocking weakness.

List all three layers: the Markdown source records; the generated Word, Excel and diagram files, with the build date and the source revision each was produced from; and the machine handoff, with its validation summary and source fingerprint. A recipient must be able to tell which output corresponds to which approved revision.

Record exact paths and the next action in `project-state.md`. Keep final documents in the chosen language. Do not claim that tracker import, implementation, UAT, deployment, training or support happened unless actual evidence exists.
