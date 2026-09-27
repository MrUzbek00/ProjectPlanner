---
name: project-planning-workflow
description: Turn a business idea, stakeholder explanations, documents, screenshots, spreadsheets or meeting notes into a validated, traceable, prioritised project plan through thirteen gated stages — intake, discovery, requirement analysis, process and domain analysis, solution and scope planning, architecture governance with Architecture Decision Records, specification, review, backlog decomposition, dependency mapping and prioritisation, roadmap, traceability validation and the final package — producing an approved technical specification, an outcome-oriented dependency-ordered backlog, and a full pre-development document package — PRD, BRD, SRS, SOW and Scope Statement, User Journey and User Stories, Wireframes and UI/UX Specification, and Project Plan and Roadmap — delivered as Word documents and Excel workbooks with generated BPMN process diagrams and a proposed database ER model — plus a validated JSON machine handoff (requirements, architecture decisions, backlog, per-task contracts, traceability) that downstream engineering automation such as SoftwareFactory can consume without reinterpreting documents. Use when the user wants to plan, scope, specify or document a software project before development, asks for a technical assignment, requirements gathering, a business analysis interview, a project specification, development cards, a project roadmap, or any of those documents by name.
license: See LICENSE of each bundled component
---

# Project Planning Workflow

A business-analysis and project-planning workflow that progressively reduces uncertainty until incomplete project information becomes a validated, traceable, prioritised and actionable plan. It moves through thirteen stages, each ending in a gate that `tools/check_gates.py` evaluates from the records — PASS, PASS WITH WARNINGS or FAIL with reasons. Only a validated plan is turned into a specification, a backlog, a stakeholder document package and a machine handoff.

The governing rule throughout: **nothing is invented**. Every requirement, rule, role, permission, calculation, field, state, integration, figure and date is either traced to an attributable source or recorded as `TBD (Q-###)` with an owner.

## First run: provision the toolchain

Before the diagram or export stages, make sure the dependencies are in place:

```bash
python tools/setup_workflow.py --check     # report readiness, change nothing
python tools/setup_workflow.py             # install what is missing
```

This installs the two diagram skills the workflow draws with, the Python packages the document builder needs, and the Excalidraw render pipeline. It is safe to re-run, updates rather than replaces, and leaves alone any skill another installation already provides.

| Provisioned | Source | Used for |
| --- | --- | --- |
| `excalidraw-diagram` skill | [coleam00/excalidraw-diagram-skill](https://github.com/coleam00/excalidraw-diagram-skill) | BPMN process diagrams |
| `drawio-skill` skill | [Agents365-ai/drawio-skill](https://github.com/Agents365-ai/drawio-skill) | ER, state and data-flow diagrams |
| `python-docx`, `openpyxl` | PyPI | Word and Excel generation |
| Playwright + headless Chromium | PyPI | Rendering Excalidraw diagrams so they can be inspected |

The readiness report also flags optional components — the draw.io CLI for image export and Graphviz for automatic layout — with the exact command to install each. It ends with a render smoke test, because the Excalidraw render page imports its library from `esm.sh` at render time and a restricted network breaks diagram verification without any obvious symptom.

Run the setup only when the user is starting the diagram or export stages, or when they ask for it. Discovery and specification work needs none of it.

## How to run the workflow

Read [`WORKFLOW.md`](WORKFLOW.md) for the operating procedure and [`AGENTS.md`](AGENTS.md) for the behavioral rules, then work through the stages using [`templates/`](templates/) as the document contract.

| Stage | Produces | Gate |
| --- | --- | --- |
| 1 Project Intake | What is known and how well — CONFIRMED / ASSUMED / UNKNOWN | G1 |
| 2 Discovery | Fourteen-category discovery log; prioritised questions, assumptions, risks, decisions | G2 |
| 3 Requirement Analysis | GOAL, BR, RULE, FR, NFR, DR, IR, SR, UXR, TR records; requirement quality review | G3 |
| 4 Process and Domain Analysis | AS-IS / TO-BE workflows; business entities | G4 |
| 5 Solution Planning and Scope | Modules, scope register | G5 |
| 6 Architecture Governance | Architecture concerns classified; principles; ADRs proposed and approved by a named owner; architecture review | G6 |
| 7 Specification | The 26-section specification, consolidated from the records | G7 |
| 8A Independent Specification Review | A reviewer who is not the author records evidenced REVIEW-### findings, in cycles | GR |
| 8B Specification Resolution and Approval | Findings resolved where they belong and re-reviewed; approval | G8 |
| 9 Backlog Decomposition | Outcome-oriented epics, features, tasks with objectives, impacts and testable criteria | G9 |
| 10A Dependency Mapping and Prioritisation | Dependencies, one priority scheme, dependency graph | G10 |
| 10B Backlog Readiness Validation | Every READY task passes the Definition of Ready; readiness report, work sets | GB |
| 11 Roadmap and Project Plan | Phases; dates as target, estimate or commitment | G11 |
| 12 Traceability Validation | Goal-to-test traceability; final planning review | G12 |
| 13 Final Planning Package | Planning summary, PRD/BRD/SRS/SOW/journeys/UI-UX/plan in Word and Excel, diagrams, machine handoff | G13 |

Templates are indexed by stage in [`templates/README.md`](templates/README.md).

Start a project with the entry prompt in [`README.md`](README.md), or resume one from its `project-state.md`.

## Non-negotiables

- Make significant architecture decisions explicit as ADRs in `architecture/`. A new ADR is PROPOSED until its named human decision owner accepts it; only ACCEPTED ADRs govern planning. Never edit an accepted ADR to change direction — supersede it with a new one — and never let a requirement, feature or task silently contradict one: record the ARCHITECTURE CONFLICT and resolve it.
- Analyze the supplied materials before writing anything, and report what could not be read.
- Ask a small round of roughly 3–5 unanswered questions at a time, explaining why each answer matters. Never re-ask something the materials already answer.
- Keep confirmed requirements, assumptions, recommendations, open questions and scope exclusions separate at all times; classify confidence CONFIRMED, LIKELY, ASSUMPTION or UNKNOWN.
- Never advance past a failing gate, and never record a gate result the gate checker did not print.
- Never grade your own specification. It is reviewed independently (a separate pass with `prompts/specification-reviewer.md`, or a person), findings are evidenced and never silently fixed, and any unresolved CRITICAL or MAJOR finding fails gate GR. A CRITICAL finding is never accepted as a risk.
- Create backlog items only after the review passes and the user approves a specific specification revision (gates GR and G8). Keep tasks outcome-oriented.
- A generated task is not a ready task. READY is earned by passing every Definition of Ready check, which the tools evaluate; planning statuses only (DRAFT, NEEDS_DISCOVERY, NEEDS_REVIEW, BLOCKED, READY, CANCELLED). Report backlog readiness — READY, PARTIALLY READY or NOT READY — as the readiness report states it, with the work sets that can start now.
- No fake precision: every date is a target, an estimate or a commitment backed by a decision.
- Never treat a meaningful change as a text edit. Once the specification is approved, record a baseline; record every change as `changes/CHANGE-###.md`, analyse it with `tools/analyze_change_impact.py`, have a person approve it, disposition every affected artifact, and never leave a READY task READY when its foundation changed. Gate GC fails otherwise.
- A diagram is a view of a confirmed model. Specify it before drawing it, render it, and actually look at the result.
- A deliverable document restates approved records for an audience and adds nothing of its own.
- Markdown is the source; `.docx`, `.xlsx`, diagram exports and the `machine-handoff/` JSON are generated output. Regenerate after any change rather than editing an output.
- A task is READY only when it meets the Definition of Ready. The handoff generator checks every READY task and every reference; report its printed summary, never a status inferred without running it.
- Report honestly: a build that succeeded is not a document that was verified, and a defined test is not an executed one.

## Scope

This workflow authorizes local planning documents, running the setup script, generating diagrams, building the Office package and generating the machine handoff. It does not authorize implementing the application, deploying anything, publishing to an external tracker, or messaging other people. Those need separate instructions.
