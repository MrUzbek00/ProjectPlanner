# Project Planning Workflow

Turn business ideas, stakeholder explanations, documents, screenshots, spreadsheets, forms, diagrams, and meeting notes into two connected deliverables:

1. An approved Project Technical Specification / Technical Assignment.
2. An implementation-ready development backlog with dependencies, acceptance tests, and requirement traceability.

This folder is a reusable analysis workflow. It does not contain a specification for an actual business project yet. The source request supplies the method; it does not establish a warehouse, approval system, technology stack, or any other example as project scope.

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
| Handoff | Specification, development cards, traceability, quality report | No unresolved blocker is represented as implementation-ready |

Discovery and process modeling can iterate together. Draft specification sections can be updated during discovery. Executable development cards are created only after specification approval.

## Files

| File / folder | Purpose |
| --- | --- |
| [AGENTS.md](AGENTS.md) | Instructions automatically discoverable by compatible coding agents |
| [WORKFLOW.md](WORKFLOW.md) | Operating procedure, gates, terminology, identifiers, change control |
| [prompts/project-analyst.md](prompts/project-analyst.md) | Portable entry prompt |
| [templates/](templates/) | Copyable records for each stage; the specification is the central document |
| [projects/README.md](projects/README.md) | Per-project folder layout and resume instructions |
| [reference/](reference/) | Original user instructions and workflow coverage review |

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

## Delivery formats

Markdown is the portable working format. The requested final format and backlog destination are established during discovery. Use document/spreadsheet/presentation tools when those formats are requested, and inspect exported artifacts before delivery. Naming a tracker does not authorize creating records in it.
