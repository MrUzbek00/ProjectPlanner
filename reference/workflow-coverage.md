# Workflow Coverage Review

Scope: the reusable workflow package, not a business project specification.

Source: [original user request](original-user-request.txt), preserved from the supplied attachment. No actual business process, organization, roles, technology stack or deployment target was supplied for specification drafting.

## Source-to-package coverage

| Requested capability | Implementation in the workflow package |
| --- | --- |
| Two connected deliverables | README, WORKFLOW sections 1/7/8/13, specification and card templates, handoff |
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

## Structural improvements

- `BIZ-###` identifies business requirements; `BR-###` retains the requested business-rule namespace to avoid ID ambiguity.
- Source-backed extraction, whole-specification approval, card definition completeness and execution readiness are recorded separately.
- `Blocked By` contains prerequisites; `Blocking Cards` is the reverse list of affected successors.
- Technical and non-UI work stays traceable through approved NFR/TR requirements without fictional pages or user roles.
- Major ambiguities cannot be hidden under accepted risks or N/A. Explicit scope deferral remains visible.
- Approved revisions include linked normative files. Post-approval changes preserve baseline history and affected approval status.
- Test definitions and planned deployment/user-guide deliverables are distinguished from completed implementation evidence.

## Limits and outstanding inputs

This package has reusable instructions and blank templates. It has no approved business specification, actual development backlog, rendered business diagrams, product test results or published tracker records. Those require an actual project and its discovery answers.

Quality/dependency/traceability checks are documented review procedures, not a claimed automated semantic validator. Blank template TBDs and example ID patterns are intentional. A populated project must replace them or record evidence-based non-applicability before passing the relevant gate.
