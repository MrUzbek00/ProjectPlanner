# Workflow Tools

| Script | Purpose |
| --- | --- |
| `setup_workflow.py` | Provision the diagram skills, document packages and render pipeline |
| `build_deliverables.py` | Convert the deliverable Markdown into Word documents and Excel workbooks |

## setup_workflow.py

```powershell
python tools/setup_workflow.py --check     # report readiness, change nothing
python tools/setup_workflow.py             # install what is missing
```

| Option | Effect |
| --- | --- |
| `--check` | Report only; exits non-zero when a required item is missing |
| `--scope user` | Install into `~/.claude/skills` (default) |
| `--scope project` | Install into this repository's `.claude/skills` instead |
| `--skills-dir PATH` | Install into an explicit directory |
| `--no-update` | Leave already-installed skills at their current revision |
| `--offline` | Do not use the network |
| `--skip-renderer` | Skip the Excalidraw render pipeline and its smoke test |

It clones each diagram skill into `<skills-dir>/.workflow-sources/<name>`, finds the directory that actually holds `SKILL.md` — one upstream repository publishes its skill under `skills/<name>/` rather than at the root — and copies it to `<skills-dir>/<name>` where the assistant discovers it. Copying merges rather than replaces, so a prepared render environment survives updates. A skill another installation already provides is detected and left untouched.

Required: git, the two diagram skills, `python-docx` and `openpyxl`. Optional and reported with install commands: the draw.io CLI (image export), Graphviz (automatic layout), and a working `python3` command. The run ends with a render smoke test, because the Excalidraw render page fetches its library from `esm.sh` at render time and a restricted network breaks verification silently.

## build_deliverables.py

It converts the completed deliverable Markdown under `projects/<project>/deliverables/` into the Word and Excel package described in [WORKFLOW.md](../WORKFLOW.md) section 12.

Markdown stays the authored source. The Office files are generated output: reviewable, reproducible and regenerated whenever a source record changes. Never hand-edit a generated `.docx` or `.xlsx` and then treat it as the source — the next build overwrites it.

## Install

```powershell
python -m pip install -r tools/requirements-docs.txt
```

Dependencies are `python-docx` and `openpyxl`. Nothing else is required, and no network access is used at build time.

## Run

```powershell
# Validate without writing anything
python tools/build_deliverables.py projects/<project>/deliverables --check

# Build the package
python tools/build_deliverables.py projects/<project>/deliverables --project "Project Name"

# Build one document while iterating
python tools/build_deliverables.py projects/<project>/deliverables --only srs
```

| Option | Effect |
| --- | --- |
| `--out DIR` | Output directory; defaults to `<source>/build` |
| `--project NAME` | Name used on cover pages and in output file names; defaults to the `project` value in `doc-meta`, then to the project folder name |
| `--check` | Validate and report only; exits non-zero on errors, zero on warnings |
| `--only NAME` | Build only the Markdown files whose name contains `NAME` |

## What it produces

One `.docx` per Markdown file, each with a cover page, a table of contents field, styled headings, formatted tables, embedded diagrams with captions, monospaced layout blocks and page numbers in the footer. Word populates the contents list when fields are refreshed (`Ctrl+A`, then `F9`).

Workbooks are assembled from tagged tables. Every sheet carries a styled header row, frozen panes, an autofilter and sized columns, and each workbook opens on an `Index` sheet naming the source document and section behind every sheet.

| Workbook key | Output file | Typical sheets |
| --- | --- | --- |
| `requirements` | `<Project>-Requirements-and-Traceability.xlsx` | Business Requirements, Product Features, Functional Requirements, Business Rules, Non-Functional Requirements, Success Metrics, User Stories, Acceptance Criteria, Traceability |
| `plan` | `<Project>-Project-Plan-and-Roadmap.xlsx` | Scope, Deliverables, WBS, Milestones, Phases, Sprints, Task Schedule, Dependencies, Resource Allocation, RACI, Release Plan |

Any other workbook key is accepted and produces a file named after it.

## Tagging a table for Excel

Place the marker on its own line directly above the table:

```markdown
<!-- xlsx: workbook=requirements; sheet=Functional Requirements -->

| FR ID | Requirement | Module |
| --- | --- | --- |
| FR-AUTH-001 | ... | ... |
```

| Key | Required | Meaning |
| --- | --- | --- |
| `workbook` | no | Workbook key; defaults to `requirements` |
| `sheet` | yes | Sheet name; truncated to 31 characters and de-duplicated automatically |
| `freeze` | no | Freeze-pane cell; defaults to `A2` |

A table without a marker appears in the Word document only. A tagged table appears in both.

## Embedding diagrams

A standalone image line is embedded in the Word document and its caption is rendered beneath it, centred and italic:

```markdown
![DIAG-001 — Purchase approval, TO-BE. Drawn in BPMN 2.0 notation; not a BPMN 2.0 XML interchange file.](diagrams/diag-001-purchase-approval-tobe.png)
```

The path is relative to the Markdown file. A diagram wider than the text column is scaled down to fit; a smaller one keeps its natural size rather than being blown up. Images are Word-only and never enter a workbook.

A referenced file that does not exist is a build **error**, so a broken diagram reference cannot ship silently. An image with no caption is a warning — captions carry the DIAG ID and the notation or model-status statement, so a reader can find the specification behind the picture.

Diagram sources and exports live in the project's `deliverables/diagrams/` folder. This tool embeds them; it does not create them. Diagrams are generated with the Excalidraw and draw.io skills as described in [WORKFLOW.md](../WORKFLOW.md) section 11.

## Cover page metadata

Each Markdown file may open with a `doc-meta` comment. Its values fill the cover page and are ignored in the body.

```markdown
<!-- doc-meta
title: Software Requirements Specification
subtitle: System behavior, architecture, data, interfaces and quality requirements
project: Acme Portal
client: Operations
version: 1.2
date: 2026-09-22
author: Analyst name
status: APPROVED
-->
```

## Value handling

Cells that contain only a number become numbers in Excel so they sort and total correctly. Anything carrying a unit, currency symbol, percent sign or identifier stays as text and reads exactly as the source record wrote it. Inline Markdown emphasis is rendered in Word and stripped in Excel.

## What `--check` reports

- Missing `doc-meta` blocks
- Tables with no data rows
- Unresolved `TBD` and `TBD (Q-###)` counts per document
- Surviving template instruction text
- `xlsx` markers without a sheet name (an error, not a warning)
- Tables whose rows have inconsistent column counts
- Referenced images that do not exist (an error, not a warning)
- Images with no caption

Warnings are expected while a document is still in draft. They are not expected in a released package; record their disposition in the deliverable package manifest.

## Wide tables

Word narrows the font for tables beyond six and beyond ten columns so they stay on the page. The widest registers — requirements, stories, traceability, task schedule — are primarily delivered in Excel for that reason; the Word copy is there for reading, the workbook is there for working.

## Verification

A successful exit means the files were written, not that they are correct. Open each exported file, refresh the Word fields, and complete the export verification checks in the deliverable package manifest before delivering anything.
