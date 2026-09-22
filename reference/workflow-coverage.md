# Workflow Coverage Review

Scope: the reusable workflow package, not a business project specification.

Source: [original user request](original-user-request.txt), preserved from the supplied attachment. No actual business process, organization, roles, technology stack or deployment target was supplied for specification drafting.

## Source-to-package coverage

| Requested capability | Implementation in the workflow package |
| --- | --- |
| Two connected deliverables | README, WORKFLOW sections 1/7/8/15, specification and card templates, handoff |
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
| Specification approval before cards | G3, approval statement/manifest, state record and instructions on card templates |
| Epic → Feature → Task → optional Subtask | Hierarchy/index and full executable-leaf contract |
| Every requested development-card field | Development-card template metadata and sections |
| Implementation-sized cards | Bounded-outcome decomposition and readiness rules |
| Dependency mapping and correct sequencing | Blocked By / derived Blocking Cards, cycle/missing-ID review and roadmap ordering |
| Phase objective/cards/dependencies/deliverable/exit criteria | Roadmap phase record |
| XS/S/M/L/XL; no unsupported dates | Relative complexity scale and capacity requirement |
| Business → functional → module/page → card → acceptance traceability | Forward/reverse matrix plus NFR/TR coverage and exclusion disposition |
| No orphan cards or important uncovered requirements | Final traceability checks and G4/G5 |
| Specification Quality Report covering requested weaknesses | Quality template with evidence, findings, severity and readiness conclusions |
| Critical recommendations without silent scope changes | Recommendation/decision registers and change control |
| Preserve domain terms and one final language | Glossary and document-language instructions |
| Persistent progress across interview rounds | State, source/decision registers, round history, baseline manifest and resume prompt |

## Later addition: the deliverable document package

Requested after the original source: once all project information is gathered, produce a detailed PRD, BRD, SRS, SOW and Scope Statement, User Journey and User Stories, Wireframes and UI/UX designs, and Project Plan and Roadmap, as Word and Excel files.

| Requested capability | Implementation in the workflow package |
| --- | --- |
| Produced after information gathering is finished | WORKFLOW section 12 preconditions and gate G6; the package is built from completed analysis records |
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
| No fabricated content in stakeholder documents | Canonical-location rules, restatement-only constraint, and `TBD (Q-###)` handling in AGENTS, WORKFLOW section 12 and every deliverable template |
| Verified delivery | Template 23 manifest with generation log, export verification and cross-document consistency checks; gate G6 requires opened and inspected exports |

## Later addition: generated diagrams

Requested after the deliverable package: generate a BPMN diagram with the Excalidraw diagram skill, and a workflow and ER diagram of the possible database with the draw.io diagram skill.

| Requested capability | Implementation in the workflow package |
| --- | --- |
| BPMN generated with `coleam00/excalidraw-diagram-skill` | WORKFLOW section 11 tool table; template 24 specifies the diagram before it is drawn |
| BPMN notation the skill does not itself supply | Template 24 carries the element vocabulary — pools, lanes, event types, task types, gateway types, sequence and message flows, data objects, boundary and terminate events — and the rules that go with them |
| ER diagram of the possible database with `Agents365-ai/drawio-skill` | WORKFLOW section 11; template 25 with table inventory, columns, keys, relationships, indexes and structural proposals |
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

## Structural improvements

- `BIZ-###` identifies business requirements; `BR-###` retains the requested business-rule namespace to avoid ID ambiguity.
- Source-backed extraction, whole-specification approval, card definition completeness and execution readiness are recorded separately.
- `Blocked By` contains prerequisites; `Blocking Cards` is the reverse list of affected successors.
- Technical and non-UI work stays traceable through approved NFR/TR requirements without fictional pages or user roles.
- Major ambiguities cannot be hidden under accepted risks or N/A. Explicit scope deferral remains visible.
- Approved revisions include linked normative files. Post-approval changes preserve baseline history and affected approval status.
- Test definitions and planned deployment/user-guide deliverables are distinguished from completed implementation evidence.
- The analysis layer and the deliverable layer are separated: Markdown records remain the single source of truth, and Word, Excel and diagram files are regenerated output rather than independently edited documents.
- A Mermaid sketch in a working record is a thinking aid; the delivered diagrams are generated separately, specified first, and verified by looking at the rendered image.

## Limits and outstanding inputs

This package has reusable instructions and blank templates. It has no approved business specification, actual development backlog, rendered business diagrams, product test results or published tracker records. Those require an actual project and its discovery answers.

Quality/dependency/traceability checks are documented review procedures, not a claimed automated semantic validator. Blank template TBDs and example ID patterns are intentional. A populated project must replace them or record evidence-based non-applicability before passing the relevant gate.
