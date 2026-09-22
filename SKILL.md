---
name: project-planning-workflow
description: Turn a business idea, stakeholder explanations, documents, screenshots, spreadsheets or meeting notes into an approved technical specification, a dependency-ordered development backlog, and a full pre-development document package — PRD, BRD, SRS, SOW and Scope Statement, User Journey and User Stories, Wireframes and UI/UX Specification, and Project Plan and Roadmap — delivered as Word documents and Excel workbooks with generated BPMN process diagrams and a proposed database ER model. Use when the user wants to plan, scope, specify or document a software project before development, asks for a technical assignment, requirements gathering, a business analysis interview, a project specification, development cards, a project roadmap, or any of those documents by name.
license: See LICENSE of each bundled component
---

# Project Planning Workflow

A business-analysis workflow that converts real project materials into planning documents that a development team can build from. It gathers requirements through focused interview rounds, models the processes and data, produces an approved specification, decomposes it into an implementation-ready backlog, generates diagrams, and exports a stakeholder document package.

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

| Stage | Produces | Templates |
| --- | --- | --- |
| Discovery | Seven-part analysis, source register, gap analysis, interview rounds | 00–02 |
| Process modeling | AS-IS and TO-BE processes, roles, permissions, states, entities | 03 |
| Specification | The 26-section technical specification and linked detail records | 04–06, 14 |
| Backlog | Epic → Feature → Task, dependency map, roadmap, traceability, tests | 07–11 |
| Diagrams | BPMN process diagrams, proposed database model, state diagrams | 24–25 |
| Deliverable package | PRD, BRD, SRS, SOW, journeys and stories, UI/UX spec, project plan | 16–23 |
| Handoff | Connected deliverables with approval evidence and open items | 12–13, 15 |

Start a project with the entry prompt in [`README.md`](README.md), or resume one from its `project-state.md`.

## Non-negotiables

- Analyze the supplied materials before writing anything, and report what could not be read.
- Ask a small round of roughly 3–5 unanswered questions at a time, explaining why each answer matters. Never re-ask something the materials already answer.
- Keep confirmed requirements, assumptions, recommendations, open questions and out-of-scope items separate at all times.
- Create executable development cards only after the user approves a specific specification revision.
- A diagram is a view of a confirmed model. Specify it before drawing it, render it, and actually look at the result.
- A deliverable document restates approved records for an audience and adds nothing of its own.
- Markdown is the source; `.docx`, `.xlsx` and diagram exports are generated output. Regenerate after any change rather than editing an export.
- Report honestly: a build that succeeded is not a document that was verified, and a defined test is not an executed one.

## Scope

This workflow authorizes local planning documents, running the setup script, generating diagrams and building the Office package. It does not authorize implementing the application, deploying anything, publishing to an external tracker, or messaging other people. Those need separate instructions.
