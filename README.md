# Project Planning Workflow

Turn business ideas, stakeholder explanations, documents, screenshots, spreadsheets, forms, diagrams, and meeting notes into a complete pre-development package:

1. An approved Project Technical Specification / Technical Assignment.
2. An implementation-ready development backlog with dependencies, acceptance tests, and requirement traceability.
3. Seven stakeholder-facing documents generated from that approved analysis — PRD, BRD, SRS, SOW and Scope Statement, User Journey and User Stories, Wireframes and UI/UX Specification, and Project Plan and Roadmap — delivered as formatted Word files with generated BPMN and data-model diagrams embedded, and with the requirement, story, traceability and schedule registers also delivered as Excel workbooks.

This folder is a reusable analysis workflow. It does not contain a specification for an actual business project yet. The source request supplies the method; it does not establish a warehouse, approval system, technology stack, or any other example as project scope.

## Install

```bash
git clone <this-repo> project-planning-workflow
cd project-planning-workflow
python tools/setup_workflow.py
```

The setup script provisions everything the workflow needs: the two diagram skills it draws with, the Python packages the document builder uses, and the Excalidraw render pipeline. It reports what is ready, what is optional and missing, and the exact command for each gap. Re-run it any time; it updates rather than replaces and leaves alone any skill you already have.

Use `--check` to see readiness without changing anything, and `--scope project` to keep the skills inside this folder instead of your account-wide skills directory.

Only the diagram and export stages need it. Discovery and specification work runs with nothing installed.

## Start here

Open this folder with your AI assistant and send:

> Follow AGENTS.md and WORKFLOW.md. Start discovery for a new project named [name]. My initial idea is [description]. The available project materials are [paths or attachments]. Use [English / Uzbek / Russian] for project deliverables. Analyze the materials first and ask only the next small round of unanswered discovery questions.

If the project has no name, use a temporary folder label and record the actual name as TBD. An idea alone is sufficient to begin. Supply additional reference materials as they become available.

For an assistant that does not read AGENTS.md automatically, provide [the portable prompt](prompts/project-analyst.md) together with [the workflow](WORKFLOW.md) and the relevant templates.

## How it works

| Stage | Result | Completion condition |
| --- | --- | --- |
| Discovery | Initial understanding, source register, requirement gap analysis, interview records | Important ambiguities are resolved or explicitly deferred outside the release |
| Process modeling | AS-IS / TO-BE process records, role matrix, states, data relationships | Confirmed flows include applicable alternatives, rejection and failure behavior |
| Specification | Complete 26-section technical specification and linked detail records | Quality review passes and the user approves a specific revision |
| Backlog | Epic → Feature → Task → optional Subtask, dependency map and roadmap | Every executable card is sufficiently defined and traced to approved requirements |
| Diagrams | BPMN process diagrams, the proposed database model and entity state diagrams | Every element traces to a confirmed record, and every export has been rendered and looked at |
| Deliverable package | PRD, BRD, SRS, SOW, User Journey and Stories, Wireframes and UI/UX, Project Plan and Roadmap, plus the package manifest — as Word documents with embedded diagrams, and Excel workbooks | Every document is authored from approved records, generated, opened and verified |
| Handoff | Specification, development cards, traceability, quality report, generated package | No unresolved blocker is represented as implementation-ready |

Discovery and process modeling can iterate together. Draft specification sections can be updated during discovery. Executable development cards are created only after specification approval, and the deliverable package is generated once the analysis records are complete.

## The deliverable package

| Document | Answers | Word | Excel |
| --- | --- | --- | --- |
| Product Requirements Document | What the product does, for whom, the MVP feature set, how success is measured | Yes | Success metrics, product features |
| Business Requirements Document | Why the organization is funding this, objectives, justification, financial expectations | Yes | Business requirements, business rules |
| Software Requirements Specification | Architecture, data model, interfaces, behavior, security rules, APIs | Yes | Functional and non-functional requirements, traceability |
| Statement of Work and Scope Statement | Deliverables, boundaries, the strict MVP set, milestones, acceptance, change control | Yes | Scope, deliverables, WBS |
| User Journey and User Stories | Journeys, pain points, epics, story backlog, acceptance criteria | Yes | User stories, acceptance criteria |
| Wireframes and UI/UX Specification | Information architecture, screen layouts, states, interactions, asset handoff | Yes | — |
| Project Plan and Roadmap | Phases, milestones, sprints, task sequence, dependencies, resources, RACI | Yes | Milestones, phases, sprints, task schedule, dependencies, resources, RACI, releases |

### Diagrams

| Diagram | Tool | Output |
| --- | --- | --- |
| BPMN process diagrams, AS-IS and TO-BE | [coleam00/excalidraw-diagram-skill](https://github.com/coleam00/excalidraw-diagram-skill) | `.excalidraw` source plus a rendered PNG |
| Proposed database model, entity state diagrams, data flows | [Agents365-ai/drawio-skill](https://github.com/Agents365-ai/drawio-skill) | `.drawio` source plus an exported PNG or SVG |

Each diagram is specified in `templates/24` or `templates/25` before it is drawn, so every lane, gateway, table and relationship traces to a confirmed record. Diagrams are embedded in the Word documents with captions that state what the artifact is: a BPMN-notation drawing rather than a BPMN 2.0 XML interchange file, and a proposed physical data model rather than a confirmed schema.

Markdown is authored and reviewed; the Office files are generated from it:

```powershell
python -m pip install -r tools/requirements-docs.txt
python tools/build_deliverables.py projects/<project>/deliverables --check
python tools/build_deliverables.py projects/<project>/deliverables --project "Project Name"
```

Generated files are output, never source. Change the Markdown and rebuild. See [tools/README.md](tools/README.md).

## Files

| File / folder | Purpose |
| --- | --- |
| [AGENTS.md](AGENTS.md) | Instructions automatically discoverable by compatible coding agents |
| [WORKFLOW.md](WORKFLOW.md) | Operating procedure, gates, terminology, identifiers, change control |
| [prompts/project-analyst.md](prompts/project-analyst.md) | Portable entry prompt |
| [templates/](templates/) | Copyable records for each stage; 00–15 for analysis, 16–23 for the deliverable package, 24–25 for diagrams |
| [tools/](tools/) | Word and Excel generator for the deliverable package, and its dependencies |
| Diagram skills | [excalidraw-diagram-skill](https://github.com/coleam00/excalidraw-diagram-skill) for BPMN, [drawio-skill](https://github.com/Agents365-ai/drawio-skill) for the data model; installed alongside your assistant, not in this repo |
| [projects/README.md](projects/README.md) | Per-project folder layout and resume instructions |
| [reference/](reference/) | Original user instructions and workflow coverage review |
| [SKILL.md](SKILL.md) | Skill manifest, so this workflow can be installed into a skills directory |

## Working rules

- Ask a focused round of approximately 3–5 relevant questions, fewer when possible. Explain why each answer matters. Do not repeat questions already answered by the materials.
- Keep confirmed requirements, assumptions, recommendations, open questions and out-of-scope items separate.
- Use `TBD (Q-###)` for unresolved decisions. Use `N/A — reason; evidence` only when non-applicability is established.
- Record source locations, confirmations and decisions. An assumption or recommendation becomes confirmed only through attributable evidence or user confirmation.
- Maintain Business Requirement → Functional Requirement → Module/Page → Development Card → Acceptance Test links. Also trace non-functional requirements and technical enablers.
- Use one chosen language for final project deliverables; preserve domain-specific Uzbek/Russian terms in the glossary. Identifiers remain stable across languages.
- Estimate complexity with XS/S/M/L/XL. Calendar estimates require known capacity and constraints.
- Do not build the application, publish a backlog, or send stakeholder messages as part of this planning workflow unless separately instructed.

## Continue an existing project

> Resume projects/[project-folder]. Read project-state.md, the latest discovery round, the decision log, and the current quality report. Identify the next unresolved gate and continue from there without repeating confirmed questions.

## Approve a completed specification

After reviewing the concrete document, the user can say:

> I approve specification version [version] at [path], including decision records [IDs]. Create the development cards and dependency-based roadmap for that approved scope.

Record that approval once. Do not ask again for the same unchanged revision. Approval does not make an ambiguous requirement executable; any outstanding implementation blocker must be resolved or explicitly removed/deferred from the release.

## Generate the deliverable package

Once the analysis records are complete, the user can say:

> Generate the deliverable package for projects/[project-folder]. Specify and generate the BPMN process diagrams and the proposed data model, then author the PRD, BRD, SRS, SOW and Scope Statement, User Journey and User Stories, Wireframes and UI/UX Specification, Project Plan and Roadmap, and the package manifest from the approved records. Then build the Word and Excel files and report the verification results.

Every document is derived from approved records. Nothing new is introduced at this stage; anything missing is a tracked question or a change request.

## Delivery formats

Markdown is the authored, reviewable, version-controlled format for every record. The deliverable package is exported from it to Word and Excel by `tools/build_deliverables.py`; the backlog destination and any additional requested format are established during discovery. Inspect every exported file before delivery — a successful build is not verification. Naming a tracker does not authorize creating records in it.
