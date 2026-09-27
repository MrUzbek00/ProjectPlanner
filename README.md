# Project Planning Workflow

Turn a business idea — plus whatever material exists: stakeholder notes, documents, screenshots, spreadsheets, forms, diagrams — into a validated, traceable, prioritised plan, a complete pre-development document package, and a versioned JSON handoff that engineering automation can execute without reinterpreting anything.

The workflow behaves like a disciplined senior business analyst, product manager and project planner working with you through an AI assistant. It is not a document generator. Each of its thirteen stages turns some unknowns into confirmed facts, records what is still unknown, and ends in a gate that a tool checks against the records. Nothing is invented: every requirement, rule, role, figure and date traces to a source or stays an open question with an owner.

## What you get

| Output | What it is |
| --- | --- |
| **Approved specification** | A 26-section Project Technical Specification built from reviewed requirements, process and domain models, an explicit scope register and governed Architecture Decision Records — independently reviewed before approval |
| **Actionable backlog and roadmap** | Epics, features and outcome-oriented tasks with acceptance criteria, dependencies, a deterministic sequence, a dependency-based roadmap, and traceability from business goal to test |
| **Stakeholder package** | PRD, BRD, SRS, SOW and Scope Statement, User Journey and User Stories, Wireframes and UI/UX Specification, Project Plan and Roadmap — as Word documents with generated BPMN and data-model diagrams, plus Excel registers |
| **Machine handoff** | Validated JSON under `machine-handoff/`: requirements, architecture decisions, backlog, one contract per task, traceability — entered through `handoff-manifest.json` and consumed by [SoftwareFactory](#handoff-to-softwarefactory) |

## Quick start

**1. Install**

```bash
git clone <this-repo> project-planning-workflow
cd project-planning-workflow
python tools/setup_workflow.py            # add --check to only report readiness
```

The setup script provisions the two diagram skills, the Python packages for the document builder and the handoff tools, and the Excalidraw render pipeline. It reports what is ready and the exact command for each gap, and it is safe to re-run. `--scope project` keeps the skills inside this folder. Discovery needs nothing installed; the gate checker and handoff tools need `jsonschema`.

**2. Start a project** — open this folder with your AI assistant and send:

> Follow AGENTS.md and WORKFLOW.md. Start a new project named [name]. My initial idea is [description]. The available project materials are [paths or attachments]. Use [English / Uzbek / Russian] for project deliverables. Complete the project intake from the materials, then ask only the next small round of unanswered discovery questions, blockers first.

An idea alone is enough to begin; an unnamed project gets a temporary folder label. The assistant asks three to five questions at a time, blockers first, and updates the records after each round. For an assistant that does not read `AGENTS.md` by itself, give it [the portable prompt](prompts/project-analyst.md), [WORKFLOW.md](WORKFLOW.md) and the templates.

**3. Resume later**

> Resume projects/[project-folder]. Read project-state.md, run tools/check_gates.py, and continue at the first failing gate without repeating confirmed questions.

## How it works

```text
INTAKE → DISCOVERY → REQUIREMENTS → PROCESS & DOMAIN → SOLUTION & SCOPE → ARCHITECTURE
  → SPECIFICATION → INDEPENDENT REVIEW → APPROVAL → BACKLOG → SEQUENCING → READINESS
  → ROADMAP → TRACEABILITY → FINAL PACKAGE + MACHINE HANDOFF
```

| # | Stage | Result | Gate |
| --- | --- | --- | --- |
| 1 | Project Intake | Everything known, each item CONFIRMED, ASSUMED or UNKNOWN | G1 |
| 2 | Discovery | Coverage of fourteen categories; prioritised questions, assumptions, risks, decisions | G2 |
| 3 | Requirement Analysis | GOAL, BR, RULE, FR, NFR, DR, IR, SR, UXR, TR records and a quality review | G3 |
| 4 | Process and Domain Analysis | AS-IS / TO-BE workflows with exceptions; entities and lifecycles | G4 |
| 5 | Solution Planning and Scope | Modules and a scope register: in, out, future, pending decision | G5 |
| 6 | Architecture Governance | Every architecture concern classified; ADRs accepted or rejected by a named owner | G6 |
| 7 | Specification | The 26-section specification, consolidated from the records — introducing nothing | G7 |
| 8A | Independent Specification Review | A reviewer who is not the author records evidenced findings | GR |
| 8B | Resolution and Approval | Findings resolved where they belong and re-reviewed; the reviewed version approved | G8 |
| 9 | Backlog Decomposition | Epic → Feature → Task, outcome-oriented, every item traced | G9 |
| 10A | Dependency Mapping and Prioritisation | Dependency graph, one priority scheme, priority kept apart from sequence | G10 |
| 10B | Backlog Readiness Validation | Every READY task passes the Definition of Ready | GB |
| 11 | Roadmap and Project Plan | Phases by outcome; every date a labelled target, estimate or commitment | G11 |
| 12 | Traceability Validation | Goal → requirement → feature → task → test, and requirement → ADR → task | G12 |
| 13 | Final Planning Package | Planning summary, documents, diagrams, machine handoff | G13 |

The risk register, decision log, traceability and change control run through every stage. A gate cannot pass while an earlier one fails, and `project-state.md` cannot claim a stage the gates do not support. What a tool cannot judge — whether a requirement is right — is recorded in a review with a checklist and findings, and the gates check that the review is complete. [WORKFLOW.md](WORKFLOW.md) describes every stage's inputs, activities, outputs and exit conditions.

```bash
python tools/check_gates.py projects/<project>             # every gate: PASS / PASS WITH WARNINGS / FAIL, with reasons
python tools/specification_review.py projects/<project>    # the independent review's result and counts
python tools/backlog_readiness.py projects/<project>       # READY / PARTIALLY READY / NOT READY, and why
python tools/analyze_change_impact.py projects/<project> CHANGE-007   # what a change affects, before making it
```

## One source, three layers

> Humans should not need JSON to understand the project, and machines should not need to reinterpret Word documents to execute it.

| Layer | Contents | Where | Edited by hand? |
| --- | --- | --- | --- |
| **Source of truth** | Discovery records, requirement registers, ADRs, specification, task cards, tests, change records | `discovery/`, `specification/`, `architecture/`, `backlog/`, `changes/`, `quality/`, `diagrams/source/` | Yes — the only place facts are written |
| **Human deliverables** | Word documents, Excel registers, BPMN and ER diagrams | `deliverables/`, `deliverables/build/`, `diagrams/exported/` | No — generated from the records |
| **Machine handoff** | Versioned, schema-validated JSON | `machine-handoff/` | Never — generated by `tools/generate_handoff.py` |

Stable IDs tie the layers together: `FR-018` is `FR-018` in the register, the SRS, the Excel workbook, `requirements.json`, every task that implements it, and — downstream — the branch, commit and pull request. Nothing renumbers anything.

## Safeguards built into the workflow

**Independent specification review.** The workflow never trusts its own specification. A reviewer who did not write it — a separate pass started from the records alone with [prompts/specification-reviewer.md](prompts/specification-reviewer.md), or a person — looks for contradictions, omissions, untestable requirements, broken traceability, missing security rules and conflicts with accepted ADRs. Problems become `REVIEW-###` findings with a severity (CRITICAL, MAJOR, MINOR, OBSERVATION) and evidence. The reviewer records findings and never fixes them. An unresolved CRITICAL or MAJOR finding fails gate GR and blocks approval, the backlog and every later gate. `tools/specification_review.py` checks the review record itself and freezes each cycle in `reviews/history/`. See WORKFLOW.md section 13.

**Architecture governance.** Significant technical decisions — architecture style, data storage, authentication, integration strategy, deployment model and the like — are recorded as Architecture Decision Records in `architecture/ADR-###-<title>.md`. A new ADR is PROPOSED and names the question that decides it; only a named human decision owner accepts it, with evidence. An accepted ADR is never rewritten: a new ADR supersedes it. The tools report any requirement, feature or task that relies on an inactive ADR or proposes an option an accepted ADR rejected, as an ARCHITECTURE CONFLICT that must be resolved explicitly. See WORKFLOW.md section 11.

**Backlog readiness.** A generated task is not a ready task. READY is earned by passing named Definition of Ready checks: approved and reviewed specification, approved in-scope requirements, testable acceptance criteria, READY and acyclic dependencies, accepted ADRs, stated security, known data, API, UI and integration impact, defined verification, and no open blocker, stale state or blocking risk. Task statuses are planning statuses only — DRAFT, NEEDS_DISCOVERY, NEEDS_REVIEW, BLOCKED, READY, CANCELLED. The backlog is honestly READY, PARTIALLY READY or NOT READY, with *ready work sets* naming what can start now. See WORKFLOW.md section 15.

**Change control.** After approval, a meaningful change is never a text edit. It is a `changes/CHANGE-###.md` record, analysed with `tools/analyze_change_impact.py` — direct, indirect and potential impact, each with a confidence and a computed severity — and decided by a named person. Everything it reaches becomes NEEDS_REVIEW until dispositioned, and a READY task whose foundation changed loses its readiness. A baseline recorded at approval catches edits made without a change record (gate GC). See WORKFLOW.md section 19.5.

## The deliverable package

Produced in stage 13, only after gate G12 passes. Every document restates approved records for its audience and introduces nothing of its own.

| Document | Word | Excel |
| --- | --- | --- |
| Project Planning Summary — the fifteen planning questions answered | Yes | — |
| Product Requirements Document | Yes | Success metrics, features |
| Business Requirements Document | Yes | Business requirements, rules |
| Software Requirements Specification | Yes | Requirements, traceability |
| Statement of Work and Scope Statement | Yes | Scope, deliverables, WBS |
| User Journey and User Stories | Yes | Stories, acceptance criteria |
| Wireframes and UI/UX Specification | Yes | — |
| Project Plan and Roadmap | Yes | Milestones, phases, schedule, dependencies, RACI |

BPMN process diagrams (AS-IS and TO-BE) are drawn with the [Excalidraw diagram skill](https://github.com/coleam00/excalidraw-diagram-skill); the proposed database model, state diagrams and data flows with the [draw.io skill](https://github.com/Agents365-ai/drawio-skill). Each diagram is specified from confirmed records first (`templates/24`, `templates/25`) and labelled honestly: a BPMN-notation drawing, not an executable BPMN 2.0 file; a proposed data model, not a confirmed schema.

```bash
python -m pip install -r tools/requirements-docs.txt
python tools/build_deliverables.py projects/<project>/deliverables --check
python tools/build_deliverables.py projects/<project>/deliverables --project "Project Name"
```

A clean build is not verification: every exported file is opened and checked against the package manifest. See [tools/README.md](tools/README.md).

## The machine handoff

```bash
python tools/generate_handoff.py projects/<project>           # generate, validate, write
python tools/generate_handoff.py projects/<project> --check   # validate only
python tools/validate_handoff.py projects/<project>/machine-handoff
```

The generator validates the specification, requirements and backlog readiness, writes the JSON, validates it against the schemas and every reference, and ends with a summary. On the committed fixture project:

```text
Specification: APPROVED (version 1.0)
Specification review: PASS WITH WARNINGS (cycle 2)
Machine handoff: VALID
Handoff status: ready
Backlog readiness: READY
Ready tasks: 3
Blocked tasks: 0
Other non-ready tasks: NEEDS_DISCOVERY 1
Errors: 0
Warnings: 0
Schema version: 1.5
Integration contract: 1.0
Handoff manifest: READY_FOR_HANDOFF (handoff 1.0, written)
Ready for handoff: TASK-001, TASK-002, TASK-003
```

When validation fails, every finding is listed at the Markdown line to fix, the command exits non-zero, and the handoff is written marked `invalid`, so an older `ready` output never survives beside changed records. The same records always produce the same bytes apart from `generated_at`.

```text
machine-handoff/
├── handoff-manifest.json     entry point for engineering: contract version, status, validation flags,
│                             file hashes, ready tasks, each task's revision and content hash
├── project.json              identity, specification status and review, counts, source fingerprint
├── requirements.json         sources, scope register, every requirement with the ADRs that affect it
├── architecture.json         principles, modules, concern coverage, every ADR
├── decisions.json            decision log, questions, assumptions, risks
├── backlog.json              epics, features, phases, dependency order, ready tasks
├── traceability.json         goal → requirement → feature → task → test, per-ADR reach, delivery slots
├── changes.json              baseline, changes and their analysed impact, review states
├── specification-review.json the independent review and every finding
├── backlog-readiness.json    backlog status, per-task readiness, ready work sets
├── domain.json, tests.json   processes, entities, test definitions
├── validation-report.json    every error and warning; why each non-ready task is not ready
└── tasks/TASK-###.json       one contract per task
```

The complete example is committed at [`tools/tests/fixtures/sample-project/machine-handoff/`](tools/tests/fixtures/sample-project/machine-handoff/). A task file carries everything needed to plan the work — trimmed here:

```json
{
  "id": "TASK-002",
  "revision": 1,
  "content_hash": "sha256:…",
  "status": "READY",
  "objective": "Let a user start a password reset without contacting the help desk (BR-001).",
  "source_requirements": ["FR-AUTH-001"],
  "acceptance_criteria": [
    "AC-001: Given an active account with that email, when a reset is requested, then one reset email is sent",
    "AC-002: Given an address with no active account, when a reset is requested, then the request is rejected silently: no email is sent and the response is identical"
  ],
  "dependencies": ["TASK-001"],
  "constraints": { "architecture": ["Send the email through the existing notification service (ADR-001)"] },
  "architecture_decisions": [{ "id": "ADR-001", "status": "accepted", "applies_via": ["requirement:FR-AUTH-001"] }],
  "readiness": { "result": "PASS", "recommended_status": "READY", "failures": [] }
}
```

## Handoff to SoftwareFactory

The machine handoff is the only channel to downstream engineering: a versioned, file-based contract, with no API, queue or agent-to-agent conversation.

| ProjectPlanner defines **what** must be achieved | SoftwareFactory determines **how** the repository achieves it |
| --- | --- |
| requirements, scope, specification, architecture decisions | repository inspection, implementation strategy, code-level planning |
| features, tasks, acceptance criteria, dependencies | branches, worktrees, code, tests, security checks |
| readiness validation, planning traceability | commits and pull requests |

A task states outcomes and constraints. File, module, table or endpoint choices appear in it only as approved constraints — an accepted ADR or a recorded task constraint.

- **One entry point.** A consumer reads `handoff-manifest.json` and nothing else first. It rejects an unknown contract `schema_version`, requires `handoff_status: READY_FOR_HANDOFF` and every validation flag true, verifies every file against its SHA-256, and takes only the tasks listed in `ready_tasks`.
- **Detectable planning changes.** Every task carries a `revision`, incremented when its definition changes materially, and a `content_hash` over its content and the requirements and ADRs it relies on (timestamps, status and readiness bookkeeping excluded). Rewording a requirement changes the hash of every task built on it. A consumer stores both at intake and stops when either changes.
- **A contract, not a convention.** [`schemas/integration/`](schemas/integration/README.md) is the canonical contract: the manifest, the consumer views of a task, requirement and ADR, and the factory's status and intake-report formats. `contract.json` locks their hashes and SoftwareFactory vendors an identical copy. The contract version (1.0) is separate from the planner's file-format version (1.5), and the generated files are validated against the consumer views, so a planner change that would break the consumer fails here first.
- **Engineering status stays engineering's.** SoftwareFactory writes a status file per task — accepted, inspected, planned, implementing, validating, PR created, blocked, completed, planning changed, rejected. The planner may later display it as external status; it never changes a planning status, a record or a gate. A rejection names its owner — `PROJECT_PLANNER`, `SOFTWARE_FACTORY` or `HUMAN_DECISION` — and a planning defect is fixed in the Markdown records, never in the JSON.

On the SoftwareFactory side, `ingest-handoff` validates the handoff and accepts READY tasks, and `plan_task.py` carries one task into repository inspection and implementation planning. See WORKFLOW.md section 23, *Engineering boundary*.

## Common requests

**Approve a specification** — only after its independent review passes; you see the open MINOR and OBSERVATION findings and any accepted risks first:

> I approve specification version [version] at [path], including decision records [IDs]. Create the backlog, dependency map and roadmap for that approved scope.

Approval is recorded once and not requested again for the same unchanged revision. Only you, as decision owner, can accept a MAJOR finding as a risk; a CRITICAL finding cannot be accepted.

**Change something approved:**

> Change FR-014 so that [new behaviour]. Record the change, analyse its impact and show me what is affected before changing anything.

The assistant records the change as PROPOSED, shows its impact and severity, and edits nothing until you approve. It then updates exactly the affected records, has the specification re-reviewed, regenerates the handoff and the affected documents, and re-runs the gates.

**Change an architecture decision:**

> Replace ADR-004 with [new direction]. Run the impact analysis on ADR-004 first.

A new ADR is proposed that supersedes ADR-004; ADR-004 becomes SUPERSEDED only after the decision owner accepts its successor.

**Produce the final package** — once gate G12 passes:

> Produce the final planning package for projects/[project-folder]: the planning summary, the BPMN process diagrams and proposed data model, the PRD, BRD, SRS, SOW and Scope Statement, User Journey and User Stories, Wireframes and UI/UX Specification, Project Plan and Roadmap, the package manifest, and the machine handoff. Build the Word and Excel files, verify every export, and report gate G13 and the handoff summary exactly as the tools print them.

## Tools

| Tool | Purpose |
| --- | --- |
| `tools/setup_workflow.py` | Provision and check diagram skills, packages and the render pipeline |
| `tools/check_gates.py` | Evaluate every gate against the records |
| `tools/specification_review.py` | Verify the independent review record; `--start-cycle` freezes a cycle |
| `tools/backlog_readiness.py` | Definition of Ready per task, backlog status, work sets, flags |
| `tools/analyze_change_impact.py` | Baseline and change-impact analysis (alias `impact_analysis.py`) |
| `tools/build_deliverables.py` | Build Word and Excel deliverables from Markdown |
| `tools/generate_handoff.py` | Generate and validate the machine handoff and its manifest |
| `tools/validate_handoff.py` | Re-validate a handoff directory, including a copy received downstream |
| `tools/handoff_contract.py` | Task content hash, manifest checks; `--check-lock` for the integration contract |

Details, options and output formats are in [tools/README.md](tools/README.md). Run the test suite with:

```bash
python -m unittest discover -s tools/tests
```

## Repository layout

| Path | Contents |
| --- | --- |
| [AGENTS.md](AGENTS.md) | Rules an AI assistant follows in this workspace, discovered automatically by compatible agents |
| [WORKFLOW.md](WORKFLOW.md) | The operating procedure: stages, gates, identifiers, change control, handoff |
| [SKILL.md](SKILL.md) | Skill manifest, so the workflow can be installed into a skills directory |
| [prompts/](prompts/) | Portable entry prompt and the independent reviewer's prompt |
| [templates/](templates/) | One template per record type, indexed in [templates/README.md](templates/README.md) |
| [tools/](tools/) | Gate checker, review verifier, readiness and impact analysis, document builder, handoff generator and validator, tests |
| [schemas/](schemas/) | JSON Schemas for the handoff files; [schemas/integration/](schemas/integration/README.md) for the engineering contract |
| [projects/](projects/README.md) | One folder per project, and how to resume one |
| [reference/](reference/) | The original workflow request and a coverage review |

This repository is a reusable method. It contains no real business project; examples in the source request and the fixture project are illustrative and never become project scope.

## Working rules

- A gap is a question with an owner. "This is unresolved" beats a plausible guess.
- Every statement is CONFIRMED, LIKELY, ASSUMPTION or UNKNOWN; an assumption is never presented as a fact.
- One requirement ID is one need, with rationale, source, evidence, priority, scope, confidence and an acceptance condition.
- No backlog before the specification is independently reviewed and approved; tasks describe outcomes, not coding steps.
- READY is earned through the Definition of Ready, never declared; partial readiness is reported honestly.
- One project-wide priority scheme; priority is not implementation order.
- No fake precision: every date is a target, an estimate or a commitment with a decision behind it.
- Contradictions are exposed for a decision, never resolved silently.
- A meaningful change is a recorded, analysed, human-approved change — never a quiet edit.
- One language per project's final documents; domain terms in Uzbek or Russian are kept with normalised definitions, and IDs stay stable across languages.
- The workflow plans. It does not build the application, publish to a tracker, deploy, or message stakeholders unless separately asked.
