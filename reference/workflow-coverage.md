# Workflow Coverage Review

Scope: the reusable workflow package, not a business project specification.

Source: [original user request](original-user-request.txt), preserved from the supplied attachment. No actual business process, organization, roles, technology stack or deployment target was supplied for specification drafting.

## Source-to-package coverage

| Requested capability | Implementation in the workflow package |
| --- | --- |
| Two connected deliverables | README, WORKFLOW sections 1/7/8/16, specification and card templates, handoff |
| Analyze all supplied materials first | Source inventory, original-location evidence, unreadable-content reporting, discovery procedure |
| No invented rules, roles, integrations, approvals, calculations, fields or permissions | AGENTS, evidence/classification rules and tracked TBDs |
| Separate confirmed/assumption/recommendation/open/out-of-scope | Registers and project-state/discovery templates |
| Detect duplicates and contradictions | Discovery reconciliation tables, decision log, quality checks |
| Full discovery extraction list | Discovery gap matrix covers identity/process/actors/data/UI/reporting/integration/security/constraints/acceptance topics |
| Requirement Gap Analysis before final specification | Discovery template and G1/G2 gates |
| Small logical interview rounds | Eight round topics, 3–5-question guidance, no repeated answered questions, round update record |
| Seven-part starting response | AGENTS and discovery sections 1–7 |
| Process record with trigger/actors/preconditions/main/alternative/approval/rejection/status/notifications/data/output/failures/audit | Process template |
| Useful Mermaid models | Process template diagram inventory, confirmed-model rules; no fabricated business diagram |
| All 26 technical specification sections | Technical specification template sections 1–26 |
| Role details and Role-Permission Matrix | Process model and specification section 4 |
| Realistic end-to-end role scenarios | Specification section 5 and acceptance scenarios |
| Module hierarchy and page map | Specification section 6 |
| Complete FR fields and stable IDs | Requirement detail and ID namespace conventions |
| Every page/table/form/button detail | Page specification with all requested fields |
| Business rules, statuses, calculations and approvals | Specification sections 9–10 and process state/transition records |
| Master data, KPIs, charts, reports and exports | Specification sections 11–13 |
| Notifications and audit event/field definitions | Specification sections 14–15 |
| Integration contract and third-party API dependency | Specification section 16 and API contract |
| File management and NFR topics | Specification sections 17–18 |
| Confirmed vs recommended technology stack | Specification section 19 and recommendation register |
| Entities, fields, relationships, ownership, lifecycle and ERD | Specification section 20 and process entity inventory |
| Given/When/Then measurable acceptance and testing categories | Specification sections 21–22 and acceptance-test template |
| Delivery phases and deliverables | Specification sections 23–24; roadmap and delivery-documentation templates |
| Open questions and risks with impact/probability/mitigation/owner | Specification sections 25–26 and registers |
| Specification approval before cards | Gate G8, approval statement/manifest, state record and instructions on card templates |
| Epic → Feature → Task → optional Subtask | Hierarchy/index and full executable-leaf contract |
| Every requested development-card field | Development-card template metadata and sections |
| Implementation-sized cards | Bounded-outcome decomposition and readiness rules |
| Dependency mapping and correct sequencing | Blocked By with derived reverse links, cycle and missing-ID detection in `tools/validate_handoff.py`, deterministic topological order in `backlog.json` |
| Phase objective/cards/dependencies/deliverable/exit criteria | Roadmap phase record |
| XS/S/M/L/XL; no unsupported dates | Relative complexity scale and capacity requirement |
| Business → functional → module/page → card → acceptance traceability | Forward/reverse matrix plus NFR/TR coverage and exclusion disposition |
| No orphan cards or important uncovered requirements | Final traceability checks and G4/G5 |
| Specification Quality Report covering requested weaknesses | Specification review (template 12) and final planning review (template 34) with evidence, severity-classified findings and gate results; readiness conclusions |
| Critical recommendations without silent scope changes | Recommendation/decision registers and change control |
| Preserve domain terms and one final language | Glossary and document-language instructions |
| Persistent progress across interview rounds | State, source/decision registers, round history, baseline manifest and resume prompt |

## Later addition: the deliverable document package

Requested after the original source: once all project information is gathered, produce a detailed PRD, BRD, SRS, SOW and Scope Statement, User Journey and User Stories, Wireframes and UI/UX designs, and Project Plan and Roadmap, as Word and Excel files.

| Requested capability | Implementation in the workflow package |
| --- | --- |
| Produced after information gathering is finished | WORKFLOW section 22 and gate G13; the package is built from completed analysis records |
| Product Requirements Document | Template 16 with personas, success metrics, MVP feature set, feature records, release criteria |
| Business Requirements Document | Template 17 with objectives, justification, options, financial expectations, governance, compliance |
| Software Requirements Specification | Template 18, including an explicit map from all 26 specification sections |
| Statement of Work and Scope Statement | Template 19 with deliverables, boundaries, strict MVP definition, acceptance, change control |
| User Journey and User Stories | Template 20 with journey maps, service blueprint, pain points, story backlog, Given/When/Then criteria, story map |
| Wireframes and UI/UX designs | Template 21 with information architecture, textual wireframes, component inventory, screen states, accessibility, asset handoff |
| Project Plan and Roadmap | Template 22 with phases, milestones, sprints, task schedule, dependency validation, resources, RACI, releases |
| Detailed rather than summary content | Every template carries per-record detail blocks alongside its registers; deliverables restate approved content without compressing behavior away |
| Word files | `tools/build_deliverables.py` renders each Markdown file to `.docx` with cover page, contents field, styled headings and tables |
| Excel files | Tables tagged with an `xlsx` marker are collected into a requirements and traceability workbook and a project plan and roadmap workbook, each with an index sheet |
| No fabricated content in stakeholder documents | Canonical-location rules, restatement-only constraint, and `TBD (Q-###)` handling in AGENTS, WORKFLOW section 13 and every deliverable template |
| Verified delivery | Template 23 manifest with generation log, export verification and cross-document consistency checks; gate G13 requires opened and inspected exports |

## Later addition: generated diagrams

Requested after the deliverable package: generate a BPMN diagram with the Excalidraw diagram skill, and a workflow and ER diagram of the possible database with the draw.io diagram skill.

| Requested capability | Implementation in the workflow package |
| --- | --- |
| BPMN generated with `coleam00/excalidraw-diagram-skill` | WORKFLOW section 21 tool table; template 24 specifies the diagram before it is drawn |
| BPMN notation the skill does not itself supply | Template 24 carries the element vocabulary — pools, lanes, event types, task types, gateway types, sequence and message flows, data objects, boundary and terminate events — and the rules that go with them |
| ER diagram of the possible database with `Agents365-ai/drawio-skill` | WORKFLOW section 21; template 25 with table inventory, columns, keys, relationships, indexes and structural proposals |
| Workflow diagrams of the database | Template 25 entity state diagrams and data flow records, generated from the confirmed state transition tables |
| Diagrams as part of the delivered documents | Image embedding in `tools/build_deliverables.py`; embed slots in the PRD, SRS and journey templates; missing image is a build error |
| No invented process or schema content | Specify-before-drawing rule, per-element source columns, annotated open questions, and the confirmed-versus-proposed split between logical entities and physical model |
| Honest labeling | Notation conformance statement in template 24 and model status statement in template 25, carried in every caption and enforced at gate G5 |
| Verified diagrams | Mandatory render-view-fix loop with a recorded iteration count, plus tracing and visual verification checks in templates 24, 25 and 23 |

## Later addition: works out of the box

Requested after the diagram stage: a new user installing the Project Planning Workflow should get the two GitHub diagram skills working without manual setup.

| Requested capability | Implementation in the workflow package |
| --- | --- |
| Installable as a skill | `SKILL.md` at the repository root with a trigger-rich description, stage map and non-negotiables |
| Diagram skills provisioned automatically | `tools/setup_workflow.py` clones both repositories and installs them where the assistant discovers them |
| Upstream layouts that differ | `locate_skill_dir` finds the real skill directory; the draw.io repository publishes its skill under `skills/drawio-skill/` rather than at the root, which a plain clone would leave undiscoverable |
| Repeatable and non-destructive | Clones live in `.workflow-sources/`; installs merge rather than replace, so a prepared render environment survives an update; a skill another installation already provides is detected and left alone |
| Python packages | `python-docx` and `openpyxl` installed from `tools/requirements-docs.txt` |
| Render pipeline without `uv` | Falls back to a virtual environment built with the running interpreter, then downloads headless Chromium |
| Honest readiness reporting | Required and optional items separated, exact install command per gap, real error extracted rather than a package manager's upgrade notice |
| Network-dependent rendering surfaced early | A render smoke test catches the case where the Excalidraw render page cannot reach `esm.sh`, which otherwise fails silently mid-project |
| No third-party code redistributed | `.claude/skills/` and the setup state file are git-ignored; each skill keeps its own upstream licence |

## Three-layer output model and machine handoff

Source: the request to separate ProjectPlanner outputs into Source of Truth, Human Deliverables and Machine Handoff.

| Requested capability | Implementation |
| --- | --- |
| 1. Markdown as source of truth; source separated from generated output | README *Output model*; WORKFLOW section 1; `projects/README.md` layout marks every folder SOURCE or GENERATED; AGENTS three-layer rule |
| 2. Human deliverables kept: Markdown, DOCX, XLSX, PNG, SVG, draw.io, Excalidraw | Unchanged build path (`tools/build_deliverables.py`, templates 16–25); diagrams moved to `diagrams/source/` and `diagrams/exported/`; deliverables embed `../diagrams/exported/` |
| 3. `machine-handoff/` with project, requirements, architecture, decisions, backlog, traceability JSON and `tasks/TASK-###.json` | `tools/generate_handoff.py`; also `tests.json` (test definitions the traceability references) and `validation-report.json` |
| 4. Stable IDs across Markdown, JSON, Excel and documents | WORKFLOW section 5; `schemas/common.schema.json` is the single pattern definition, asserted equal to the parser's patterns by a test; generator warns on IDs a document mentions but no record defines, and on retired forms |
| 5. Requirement JSON schema | `schemas/requirement.schema.json`; source format in template 26 |
| 6. Task JSON schema, one file per task | `schemas/task.schema.json`; source format in template 08 |
| 7. Definition of Ready; statuses DRAFT / NEEDS_DISCOVERY / BLOCKED / READY / IN_PROGRESS / DONE | WORKFLOW section 14; template 08 checklist; enforced in `validate_handoff.readiness_gaps` and by `task.schema.json` for the structural part; DEFERRED retained from the existing workflow. Superseded by the planning status lifecycle in *Backlog readiness and task readiness validation* below |
| 8. ADRs in source form, exported to `architecture.json`; which ADRs apply to a task | Templates 27–28; `architecture/ADR-###-*.md`; each task lists applicable ADRs with how each applies (task, requirement or module) |
| 9. Traceability GOAL → BR → FR → FEAT → TASK → TEST, extensible to PR / commit / release | `traceability.json` per requirement and per task, with empty `delivery` slots; human view generated as `traceability/requirement-map.md` |
| 10. `project.json` with schema version and counts | `schemas/project.schema.json`; adds source fingerprint and per-file SHA-256 |
| 11. Deterministic validation, not an LLM claim | `tools/validate_handoff.py`: syntax, schemas, unique IDs, references, cycles, Definition of Ready, empty criteria, traceability, ADR references, cross-file agreement, hashes, staleness, status claim; tests in `tools/tests/test_handoff.py` |
| 12. Reusable schemas under `schemas/` | Thirteen draft 2020-12 schemas with a shared `common.schema.json` |
| 13. `backlog.md` for humans and `backlog.json` for tools, no conflicting duplication | Task card canonical; `backlog.json` is an index generated from it; the validator requires equality, and the generator rejects a `backlog.md` index that disagrees with the cards |
| 14. `generate-machine-handoff` command with the eight steps and final summary | `python tools/generate_handoff.py projects/<project>`; `--check` validates without writing |
| 15. Backward compatibility | Word, Excel and diagram pipeline unchanged; registers can stay in `discovery/registers.md`; ID changes limited to those needed for consistent IDs (EPIC-###, FEAT-###, TASK-###, TEST-###) |
| 16. README documents the model with examples | README *Output model* and *The machine handoff*, with examples generated from the fixture's real output |
| 17. JSON is an added integration contract, Markdown is not replaced | JSON is generated only; AGENTS and WORKFLOW forbid editing or hand-writing it |

Identifier decision: the original workflow request used `BR-###` for business rules, while the two later requests used `BR-###` for business requirements. On 2026-09-26 the user chose the later convention: `BR-###` is a business requirement, business rules are `RULE-###`, business goals are `GOAL-###`, and the earlier `BIZ-###` form is retired (reported as a legacy ID). No project records existed, so nothing needed migration. Each JSON requirement also carries an explicit `type`.

## Staged workflow, gates and planning discipline

Source: the request to make ProjectPlanner clearer, stricter and more reliable from discovery to the final planning package.

| Requested capability | Implementation |
| --- | --- |
| Explicit stages with purpose, inputs, activities, outputs, gate and exit condition; no jump from raw input to backlog | WORKFLOW sections 2 and 6–18; *Current stage* in `project-state.md`; `tools/check_gates.py` reports a violation when the stage outruns its gates |
| Phase 1 — Project intake, CONFIRMED / ASSUMED / UNKNOWN | Template 29; gate G1 checks all fourteen items and their classification |
| Phase 2 — Discovery by category; open questions, assumptions, risks; BLOCKER / HIGH / MEDIUM / LOW | Template 30 (fourteen categories), template 02 registers; gate G2 fails on an open blocker not contained by scope |
| Phase 3 — Requirement types BR, FR, NFR, DR, IR, SR, UXR with the requested fields; one need per ID | Template 26 (plus GOAL, RULE, TR); parser, schemas and generator; gate G3 checks fields, confidence and upward traceability |
| Phase 4 — Requirement quality review; weak wording flagged | Template 31; G3 heuristics for unmeasured wording, implementation detail, compound requirements, missing actor, trigger, permissions and error cases, duplicates |
| Phase 5 — Process analysis with AS-IS / TO-BE and explicit differences | Template 03 process records; `domain.json`; gate G4 |
| Phase 6 — Domain and data analysis, business-first | Template 32; gate G4; the physical model stays a later proposal (template 25) |
| Phase 7 — Solution planning: modules, areas, integrations, security boundaries, data ownership; requirements mapped to modules | Template 27; gate G5 requires every in-scope system requirement to map to a module |
| Phase 8 — Scope: IN / OUT / FUTURE / PENDING DECISION | Template 33; *Scope* field on requirements and features; gate G5; pending items must be named by an open question |
| Phase 9 — Specification only after discovery, reviewed requirements, workflows and scope; no new requirements | WORKFLOW section 12; template 04; gate G7 fails when the specification mentions an ID no record defines |
| Phase 10 — Specification review with CRITICAL / MAJOR / MINOR / OBSERVATION | Template 12 rewritten as the specification review; now the independent review of stage 8A, whose gate GR blocks approval (G8) on any unresolved CRITICAL or MAJOR finding (see *Independent specification review* below) |
| Phase 11 — Feature decomposition from approved requirements; outcome-oriented tasks | Templates 07 and 08; gate G9 (coverage, orphans, Definition of Ready); implementation-worded task titles warned |
| Phase 12 — Dependency mapping between requirements, features, tasks, external systems, decisions; cycles, hidden prerequisites, impossible sequencing | Feature *Depends on*, task *Blocked By*, `DEP-###` register, questions; validator checks; `reports/dependency-graph.md`; gate G10 |
| Phase 13 — One prioritisation scheme; not everything high | *Priority scheme* in `project-state.md`; gate G10 fails on missing or mixed schemes and warns when more than 60% sits at the top priority |
| Phase 14 — Roadmap; target vs estimate vs commitment | Phase *Date basis* and *Commitment decision*; gate G11 fails an unqualified date or an unsupported commitment |
| Phase 15 — Risk register maintained throughout | Template 02 risk register with the requested fields and categories; gates G2 and G11 |
| Phase 16 — Decision log | Template 02 decision log with the requested fields; `decisions.json` |
| Phase 17 — Traceability throughout; orphans reported | Goal → BR → requirement → module → feature → task → criteria → test; orphans in `traceability.json`; gates G9 and G12 |
| Phase 18 — Gates with PASS / PASS WITH WARNINGS / FAIL and exact reasons | `tools/check_gates.py`, thirteen gates, `reports/gate-report.md`; claims in `project-state.md` checked against the evidence |
| Phase 19 — Confidence and uncertainty | CONFIRMED / LIKELY / ASSUMPTION / UNKNOWN on intake items, requirements, processes, entities and assumptions; open questions and assumptions surfaced in reviews and the package |
| Phase 20 — Change management with impact analysis first | `tools/analyze_change_impact.py`; template 35; gate GC; WORKFLOW section 19.5 |
| Phase 21 — Final planning review | Template 34; gate G12 |
| Phase 22 — Final output answering fifteen questions, only after the final gate | Template 36; gate G13 checks every question is answered; the package is produced only after G12 |
| Behavioural rules 1–10 | WORKFLOW section 1 and AGENTS.md, each backed by a gate where it can be checked |

What the gates cannot establish: whether a requirement is correct, whether two statements contradict, whether a criterion really proves its requirement. Those judgements are made in the three reviews, and the gates only verify that each review is complete, current and has no serious finding open.

## Structural improvements

- `GOAL-###` business goals, `BR-###` business requirements and `RULE-###` business rules are separate namespaces, so a business requirement and a business rule can never share an ID.
- Source-backed extraction, whole-specification approval and task readiness are recorded separately; task readiness is the Definition of Ready, checked by the handoff generator.
- `Blocked By` contains prerequisites; the reverse list of affected successors is derived, never maintained by hand.
- Technical and non-UI work stays traceable through approved NFR/TR requirements without fictional pages or user roles.
- Major ambiguities cannot be hidden under accepted risks or N/A. Explicit scope deferral remains visible.
- Approved revisions include linked normative files. Post-approval changes preserve baseline history and affected approval status.
- Test definitions and planned deployment/user-guide deliverables are distinguished from completed implementation evidence.
- The analysis layer and the deliverable layer are separated: Markdown records remain the single source of truth, and Word, Excel and diagram files are regenerated output rather than independently edited documents.
- A Mermaid sketch in a working record is a thinking aid; the delivered diagrams are generated separately, specified first, and verified by looking at the rendered image.

## Architecture governance

The request to add a formal Architecture Governance layer based on Architecture Decision Records, and where each of its points is implemented.

| Requested | Implemented by |
| --- | --- |
| 1. A governance stage between process/domain analysis and specification | Stage 6 — Architecture Governance, gate G6 *Architecture ready* (WORKFLOW section 11); later stages renumbered 7–13 |
| 2. A dedicated `architecture/` location with stable, never-reused ADR IDs | `projects/<project>/architecture/` (README, register, principles, `ADR-###-*.md`); the ADR register lists every ID ever assigned and G6 fails on an unregistered file or a registered ID without a file |
| 3. ADR structure | Template 28: status, date, decision owner / approver, approval evidence, decision question, related requirements and features, affected modules, related decisions, principles, depends on, conflicts with, supersedes, superseded by; context, decision, rationale, alternatives, positive and negative consequences, risks, constraints, notes |
| 4. Lifecycle PROPOSED / ACCEPTED / REJECTED / SUPERSEDED / DEPRECATED; no silent modification | Template 28 lifecycle; `active` only for accepted; `ADR_SUPERSESSION_MISMATCH`, `ADR_ACTIVE_CONFLICT`; `impact_analysis.py` tells the planner to supersede an accepted ADR rather than edit it |
| 5. Which decisions need an ADR, which do not | Template 28, WORKFLOW section 11, README *Architecture governance*; the twenty standard concerns in the coverage table |
| 6. Architecture decision register | `architecture/architecture-register.md` (template 27), checked against the ADR files at G6; `reports/architecture-report.md` generated with the current state |
| 7. Machine-readable architecture | `machine-handoff/architecture.json` (schema 1.1): summary, principles, modules, coverage, every ADR with constraints; Markdown remains the source |
| 8. Requirements reference ADRs where material | ADR *Related requirements* and an optional requirement *Architecture decisions* field → `requirements.json` `architecture_decisions`; G6 warns only for in-scope TR / IR with no ADR |
| 9. Features reference ADRs | Feature *Architecture decisions* field (template 07); derived links through requirements and modules → `backlog.json` `architecture_decisions` |
| 10. Explicit, reviewable constraints | *Constraints introduced* section → `constraints`; `VAGUE_CONSTRAINT` and `ADR_NO_CONSTRAINTS` warnings |
| 11. Conflict detection before specification, features, backlog | `ADR_ACTIVE_CONFLICT`, `ADR_INACTIVE_REFERENCE`, and `ARCHITECTURE_CONFLICT` for mentions of options an accepted ADR rejected; an unrecorded conflict fails the item's gate (G6 or G9); resolution by CHANGE PROPOSAL, NEW ADR or SUPERSEDE ADR in the architecture review |
| 12. Proposed-ADR workflow with human approval | PROPOSED ADRs name their deciding question; every other status needs a named decision owner and DEC / SRC approval evidence (`ADR_DECISION_QUESTION_MISSING`, `ADR_APPROVAL_MISSING`) |
| 13. Gate — architecture ready | `check_gates.py` G6: concern coverage, register agreement, critical decisions, consistency, supersession, inactive references, review completeness and currency |
| 14. Architecture review report | `reviews/architecture-review.md` (template 39) with counts validated against the records; `reports/architecture-report.md` generated |
| 15. Prevent drift | WORKFLOW section 19.6; drift detection at every validation; the review is repeated when a conflict is reported or an ADR changes status |
| 16. Change impact for ADRs | `analyze_change_impact.py` follows an ADR to the requirements, modules, features, tasks and ADRs it governs, supersedes or depends on |
| 17. Architecture, not implementation | Template 28 guidance; `ADR_IMPLEMENTATION_DETAIL` warning for file paths, function calls and class names |
| 18. Principles | `architecture/principles.md` (template 38), `PRIN-###`; accepted principles need evidence; more than ten warns |
| 19. Detect missing decisions | Coverage status DECISION REQUIRED with a question; a BLOCKER that affects in-scope work fails G6, otherwise a visible warning |
| 20. Traceability requirement → ADR → feature → task, and ADR → affected requirements → features | `traceability.json` `architecture`; requirement map *Architecture decisions* section and ADR columns; task `applies_via` including `feature:FEAT-###` |
| 21. Documentation with a complete ADR example | README *Architecture governance*; template 28 example; template 40 project README |
| 22. Core rules | WORKFLOW section 11 *Core rules*; AGENTS.md *Architecture governance*; enforced as listed above |

What remains judgement rather than automation: whether two accepted decisions contradict in substance when neither records the conflict, and whether work contradicts a constraint without naming a rejected option. Both are recorded in the architecture review, whose checklist and findings the gate requires. The rejected-option search matches option names as written, so a specific option name ("GraphQL") is detected and a generic one ("Option B") is not.

## Change-impact analysis

The request to add a formal Change-Impact Analysis system, and where each of its points is implemented.

| Requested | Implemented by |
| --- | --- |
| 1. Change records with stable, never-reused IDs | `changes/CHANGE-###.md` (template 35) with every requested field; `CHANGE-###` identifier; `CR-###` retired and reported as a legacy form |
| 2. Specific change types | Twelve types, validated; one record per change |
| 3. Lifecycle PROPOSED → IMPLEMENTED_IN_PLAN; a proposed change does not alter the plan | Only APPROVED and IMPLEMENTED_IN_PLAN changes mark artifacts; an edit made before approval, or despite rejection, fails GC |
| 4. Impact graph | `tools/change_impact.py` `Graph`: goals, requirements, rules, ADRs, modules, features, tasks, tests and criteria, phases, workflows, entities, pages / API / integration detail records, risks, decisions, questions, scope items — strong and weak links, not keyword matching |
| 5. DIRECT / INDIRECT / POTENTIAL | `classify`; POTENTIAL for upstream assumptions, shared modules and mentions |
| 6–10. Requirement, ADR, scope, business-rule and dependency change impact | Review areas per change type; ADR governance edges; scope items reach what they classify; readiness and sequencing re-validated from the records |
| 11. Stale-state detection | Review states CURRENT / NEEDS_REVIEW / STALE / INVALID, derived from the change records and the baseline into `changes.json`; an unrecorded edit marks the record and everything it reaches |
| 12. Readiness invalidation | Definition of Ready condition "not under change review"; READY_NOT_MET and GC failure for a READY task under review |
| 13. Severity | Computed CRITICAL / HIGH / MEDIUM / LOW with its drivers; a declared severity may not be lower |
| 14. Confidence | CONFIRMED (strong path), LIKELY (weak link on the path), POSSIBLE (inferred) |
| 15. Impact report | `changes/CHANGE-###-impact-report.md` |
| 16. Machine-readable output | `machine-handoff/changes.json` (`changes.schema.json`, schema 1.2) |
| 17. Change-impact command | `tools/analyze_change_impact.py` — the ten steps; `--baseline`, `--detect`, `--summary`, what-if mode |
| 18. Change review gate | Gate GC, required by G12 and G13 |
| 19. Traceability after change | Regenerated from the updated records; orphans the change creates are flagged; history kept in the baseline archive |
| 20. History | Previous and new state in the change record; the full previous text in `changes/baseline.json` and `changes/history/`; decided records are superseded, not rewritten |
| 21. Orphaned artifacts | GC warnings: feature without a live requirement, task without an active feature, accepted ADR without a consumer, phase without an active task |
| 22. Newly missing work | `missing_work`: no feature or task for the new state, criteria no task or test covers, criteria gained since the baseline, modules no feature covers, and a prompt that existing tasks are not assumed sufficient |
| 23. Roadmap impact | Affected phases, re-estimation stated without invented timing, committed dates to reconfirm; roadmap impact required before implementation |
| 24. Risk impact | Linked risks listed; *Risk impact* table (NEW / INCREASED / REDUCED / RETIRED / UNCHANGED) checked against the risk register |
| 25. Document impact | Only the human documents that mention an affected artifact are listed for regeneration |
| 26. Dashboard data | `changes.json` `summary`, `--summary`, the gate report's *Change state* |
| 27. Core rules | WORKFLOW section 19.5; AGENTS.md *Change impact*; enforced by GC and the Definition of Ready |

What remains judgement: whether an affected artifact is really unaffected (the change record's disposition), whether new work is sufficient, and the size of any roadmap delay. The tools make each of these an explicit, recorded review rather than a silent assumption; they do not decide them. Change detection covers the kinds the baseline controls; a backlog item's planning status is deliberately outside it.

## Independent specification review

The request to add a formal Independent Specification Review stage, so that ProjectPlanner never trusts its own specification without a second pass, and where each of its points is implemented.

| Requested | Implemented by |
| --- | --- |
| 1. Separate review stage before the backlog | Stage 8 split into 8A Independent Specification Review (gate GR) and 8B Specification Resolution and Approval (gate G8), between Specification (G7) and Backlog (G9). Stage numbers 9–13 and their gates keep their numbers so existing projects stay valid. GR fails → G8 and every later gate fail |
| 2. Author and reviewer roles | SPECIFICATION AUTHOR and SPECIFICATION REVIEWER (WORKFLOW section 13, template 12, AGENTS.md). The review names both and states its independence; a reviewer who is the author fails GR. `prompts/specification-reviewer.md` gives an AI reviewer a fresh pass from the records only, writing only the review |
| 3. Review scope | Checklist by eighteen review areas (template 12), each required by GR: requirements quality, scope, workflows, missing scenarios, permissions and authorisation, security, data model, integrations, architecture, independent traceability, contradictions, acceptance criteria, terminology, assumptions, risks, change consistency, roadmap consistency, review quality |
| 4–5. Structured findings with stable IDs | `REVIEW-###` record blocks (template 12): severity, category, status, raised and closed cycle, affected artifacts, evidence, conflict, why it matters, required action, return to stage. `REVIEW-###` pattern in `planning_records.py` and `common.schema.json` (`reviewFindingId`); an ID recorded twice fails GR |
| 6. Severity | CRITICAL, MAJOR, MINOR, OBSERVATION with the requested definitions (template 12, WORKFLOW section 13) |
| 7. Categories | The fourteen requested categories plus ASSUMPTION, for the assumption review (item 20) |
| 8. Statuses; RESOLVED needs a recorded resolution | OPEN, ACKNOWLEDGED, IN_RESOLUTION, RESOLVED, ACCEPTED_RISK, REJECTED; each closed status is checked for the fields it requires |
| 9. Resolution records | *Resolution*, *Resolved by*, *Resolution date*, *Changed artifacts* (existing IDs), *Verification*; RESOLVED only in a cycle later than the one that raised the finding |
| 10. Evidence for serious findings | A CRITICAL or MAJOR finding must list affected artifacts, cite an ID in its evidence and name the stage that resolves it; a reference to a record that does not exist fails GR |
| 11. No auto-fix | The reviewer writes only the review; RESOLVED requires a later cycle's re-review; `--start-cycle` never touches a finding; the reviewer prompt forbids edits to planning records |
| 12. Review cycles | *Review cycle* in the header; `tools/specification_review.py --start-cycle` closes a cycle and reopens every check; per-cycle `review_cycle`, `review_date`, `finding_count`, `critical_count`, `major_count`, `minor_count`, `observation_count` in `specification-review.json` |
| 13. Specification review report | `reviews/specification-review.md`: result, cycle, open counts, resolved since the previous review, open findings, then each finding |
| 14. Machine-readable output | `machine-handoff/specification-review.json` (`specification-review.schema.json`, schema 1.3), with the requested keys and more; `project.json` carries its summary; the validator recomputes the result and counts |
| 15. Independent traceability review | Review area and checklist rows; `reports/specification-review-aid.md` re-derives the chain from the requirement, feature, task and ADR records, not from the generated traceability, and lists broken, orphaned and stale references |
| 16. Contradiction detection | Heuristic candidates for one-versus-many, deletion-versus-retention and anonymous-versus-authenticated statements; each must be a finding or dismissed with a reason, or GR fails |
| 17. Missing-scenario review | Review area; the aid shows which of the eleven scenario families each workflow mentions, applying "external service unavailable" only where the workflow involves one |
| 18. Acceptance-criteria review | Review area; the aid flags vague wording in criteria and functional requirements without a negative criterion |
| 19. Terminology review | Review area; the aid flags common synonym groups (organisation, company, tenant, workspace …) used side by side |
| 20. Assumption review | Review area and ASSUMPTION category; the aid lists live requirements resting on open assumptions and models built on unconfirmed information |
| 21. Risk review | Review area; the aid lists dependencies, integrations and ADR risks that no risk register entry covers |
| 22. ADR review | Review area; the aid lists proposed ADRs and undecided concerns; the validator's ADR findings are grouped into it |
| 23. Change-impact review | Review area; an approved change dated after the review fails GR (MEDIUM or higher) and requires a new cycle; `rerun_gates` in the change analysis now includes GR |
| 24. Specification review gate | Gate GR: unresolved CRITICAL or MAJOR → FAIL; only MINOR, OBSERVATION or accepted risks → PASS WITH WARNINGS; none → PASS. No threshold |
| 25. Human accepted risk | ACCEPTED_RISK needs *Approved by* (not the author or reviewer) and DEC-### or SRC-### evidence; never for CRITICAL; a MAJOR one needs a risk register entry; it stays a visible warning and is counted separately, never as resolved |
| 26. No backlog-ready claim on a failed review | GR failure fails G8–G13; the Definition of Ready requires a passing review of the current version, so no task can be READY and `handoff_status` cannot be `ready`; a backlog drafted meanwhile is reported as provisional |
| 27. Review quality | Duplicate titles and reused IDs fail GR; overlapping open findings warn; findings without evidence, artifacts or impact fail; the checklist has a review-quality area |
| 28. Review history | Closed cycles frozen byte for byte in `reviews/history/specification-review-cycle-###.md`; each history row must match its snapshot; a finding recorded in a snapshot and missing now, or backdated to a cycle whose snapshot lacks it, fails GR |
| 29. Summary in project status | *Specification review* table in `project-state.md` (template 00); a better summary than the records show is a workflow violation; the gate report lists it |
| 30. Reviewer principles | WORKFLOW section 13 *Reviewer principles*; `prompts/specification-reviewer.md`; enforced as listed above |

What remains judgement rather than automation: whether a requirement is right, whether a finding is real, and whether a resolution truly removes the problem. The tools make the review complete, evidenced, independent in name, historically honest and binding on the plan. They also surface heuristic candidates. They cannot make the reviewer skeptical: that is what the reviewer role and prompt are for. The contradiction heuristics match wording patterns; a contradiction phrased differently is found only by the reviewer.

## Backlog readiness and task readiness validation

The request to add a formal Backlog Readiness and Task Readiness Validation system, so that tasks existing is never mistaken for the backlog being ready, and where each of its points is implemented.

| Requested | Implemented by |
| --- | --- |
| 1. Backlog readiness stage | Stage 10 split into 10A Dependency Mapping and Prioritisation (G10) and 10B Backlog Readiness Validation (gate GB), after feature and task decomposition (stage 9, now "Backlog decomposed") and before the roadmap and handoff. G11–G13 fail while GB fails |
| 2. Item levels | EPIC → FEATURE → TASK → optional SUBTASK, defined in WORKFLOW section 14 and template 07; subtasks only when a task genuinely needs internal breakdown |
| 3. Outcome-oriented tasks | WORKFLOW section 14, template 08; the IMPLEMENTATION_STEP flag for titles that read as coding instructions |
| 4. Deterministic Definition of Ready | 23 named checks in `validate_handoff.readiness_failures`, evaluated by the generator and recomputed by the validator; a READY task failing one is `READY_NOT_MET` |
| 5. Planning status lifecycle | DRAFT, NEEDS_DISCOVERY, NEEDS_REVIEW, BLOCKED, READY, CANCELLED; engineering statuses (IN_PROGRESS, CODING, TESTING, PR_OPEN, MERGED, DEPLOYED, DONE) are rejected with an explanation; DEFERRED is retired in favour of scope or CANCELLED |
| 6. Task readiness result | `readiness` on every task file: result, every named check, failures, the status the failures point to, accepted-risk findings |
| 7. Strengthened task schema | Template 08 and `task.schema.json`: objective, revision, declared scope, risks, impacts, readiness, readiness history alongside the existing fields; impact sections only where relevant |
| 8. Acceptance-criteria quality | `acceptance_criteria_valid` and `acceptance_criteria_testable`: no TBD, no vague wording, every AC-### belongs to a source requirement |
| 9. Task overload | NEEDS_DECOMPOSITION flag from modules, workflows, actors, integrations, criteria count and listed objectives — not text length |
| 10. Task fragmentation | FRAGMENTATION flag for tasks that implement the same requirements in one feature as implementation steps or single-criterion slivers |
| 11. Dependency validation | `dependencies_valid`: reviewed, existing, not itself, not cancelled, in scope, acyclic, READY; hidden prerequisites and impossible sequencing at G10 |
| 12. Circular dependencies | DEPENDENCY_CYCLE; the execution sequence is empty while any cycle exists; GB fails |
| 13. Priority separate from sequence | Distinct `priority` and `sequence` on every backlog and readiness entry; WORKFLOW 10A |
| 14. Scope validation | Task scope is its feature's or its own narrower declaration; only IN SCOPE work can be READY; "Pending approval" is read as PENDING DECISION |
| 15. Requirement traceability | `source_requirement_valid`; GB traceability issues for tasks without requirement, feature or criteria, tasks tracing only to superseded or rejected requirements, and uncovered in-scope requirements |
| 16. Feature coverage | Feature *No tasks reason*; G9 fails an in-scope feature with neither tasks nor a reason and warns with the reason when there is one |
| 17. Architecture validation | `architecture_valid` and `architecture_conflicts_clear`: accepted ADRs only; open conflict reviews and unreviewed rejected options block READY; the architecture review's conflict findings travel in `architecture.json` |
| 18. Security readiness | `security_valid`: N/A is refused for work touching authentication, authorisation, payments, personal data, secrets, file uploads, external APIs, administrative actions, account recovery or audit, and points to NEEDS_REVIEW; no controls are invented |
| 19–22. Data, API, UI and integration impact | Impact sections on the card; `*_impact_known` checks apply only where the task touches the area; data impact names entities, API impact its NONE / CREATE / MODIFY / REMOVE change, integration impact its failure, timeout and fallback behaviour; unknown integration behaviour points to BLOCKED |
| 23. Verification requirements | `verification_defined`; VERIFICATION_GAP flag when stated impacts are not covered by the required test levels |
| 24. Specification review findings | `review_findings_clear`: an unresolved CRITICAL or MAJOR finding on the task, feature, epic or requirements blocks READY; accepted risks stay listed in `accepted_risk_findings` |
| 25. Change-impact state | `not_stale`; a READY task a change reaches must move to NEEDS_REVIEW with a history entry |
| 26. Risk-aware validation | Task *Risks* and register links reported as `related_risks`; the risk register's explicit *Blocks readiness* column is the only way a risk blocks a task (`blocking_risks_clear`) |
| 27. Ready backlog summary | `backlog/readiness-report.md` |
| 28. Machine-readable readiness | `machine-handoff/backlog-readiness.json` (`backlog-readiness.schema.json`, since schema 1.4), recomputed by the validator |
| 29. Backlog quality gate | Gate GB with the requested failure conditions, plus no ready work, dishonest readiness histories and unrevised changed tasks |
| 30. Partial readiness | Backlog status READY / PARTIALLY_READY / NOT_READY; phase statuses READY / PARTIALLY_READY / NOT_READY / EMPTY |
| 31. Ready work sets | WS-01, WS-02 … in the report and JSON; WS-01 is `executable_now` |
| 32. Coverage metrics | `coverage` in the readiness JSON and report, presented as gap indicators |
| 33. Duplicate tasks | POSSIBLE_DUPLICATE flag with synonym-aware title overlap; never merged automatically |
| 34. Contradictory tasks | CONTRADICTION flag using the specification review's negation-aware contradiction patterns, traced to both tasks' requirements |
| 35. Missing error behaviour | MISSING_ERROR_BEHAVIOUR flag naming only relevant cases (upload, external service, permission, input, state transition) |
| 36. Readiness revalidation | Every run re-evaluates every task deterministically; the change-impact graph names what people must revalidate; GB is among the gates a change re-runs |
| 37. Readiness history | *Readiness history* on each card (date, from, to, reason, change); the last entry must match the status, READY must be recorded, losing READY needs a reason; the history is outside change control |
| 38. Task revision | *Revision* on each card; GB fails a task changed since the baseline without a higher revision |
| 39. Planning completeness | The eight questions answered per phase in the readiness report and JSON, from the named checks |
| 40. Core principles | WORKFLOW sections 14–15, AGENTS.md, template 08; enforced as listed above |

What remains judgement rather than automation: whether a flagged task really needs decomposition, is really a duplicate, or really contradicts another, and whether a stated impact is complete. The tools make readiness earned and auditable, not a declaration. They cannot tell a well-written objective from a plausible one; the reviewer and the stakeholders do that.

## Limits and outstanding inputs

This package has reusable instructions and blank templates. It has no approved business specification, actual development backlog, rendered business diagrams, product test results or published tracker records. Those require an actual project and its discovery answers.

Quality and specification-content checks are documented review procedures, not an automated semantic validator. The machine-handoff validator checks structure, references, readiness rules and consistency deterministically; it cannot judge whether a requirement is correct, complete or well written. Blank template TBDs and example ID patterns are intentional. A populated project must replace them or record evidence-based non-applicability before passing the relevant gate.
