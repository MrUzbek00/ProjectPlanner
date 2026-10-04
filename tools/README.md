# Workflow Tools

| Script | Purpose |
| --- | --- |
| `check_gates.py` | Evaluate the thirteen stage gates from the project records, including architecture governance and the independent specification review (gate GR); detect claims the evidence does not support |
| `backlog_readiness.py` | Backlog readiness from every task's Definition of Ready result: backlog status, per-task blockers, phases, ready work sets, coverage and review flags; writes `backlog/readiness-report.md` |
| `specification_review.py` | Verify the independent specification review (`reviews/specification-review.md`), compute its result and counts, write the review aid, and close a review cycle (`--start-cycle`) |
| `analyze_change_impact.py` | `analyze-change-impact`: record the baseline, detect changes, analyse a change's direct, indirect and potential impact, severity, review states and consequences, and write the impact report |
| `change_impact.py` | The impact graph, baselines, classification, severity and review-state rules shared by the tools |
| `impact_analysis.py` | Alias of the what-if mode of `analyze_change_impact.py` |
| `setup_workflow.py` | Provision the diagram skills, document and validator packages, and render pipeline |
| `build_deliverables.py` | Convert the deliverable Markdown into Word documents and Excel workbooks |
| `generate_handoff.py` | Generate and validate the JSON machine handoff from the project's Markdown records (`generate-machine-handoff`) |
| `validate_handoff.py` | Validate a machine-handoff directory on its own, without the Markdown |
| `planning_records.py` | Shared reader for record blocks and register tables; used by all the tools above |
| `tests/` | Test suite and fixture project for the handoff tools |

## check_gates.py

Evaluates the thirteen stage gates, the independent-review gate GR (stage 8A), the backlog-readiness gate GB (stage 10B) and the continuous change-impact gate GC described in [WORKFLOW.md](../WORKFLOW.md) section 20 and reports each as PASS, PASS WITH WARNINGS or FAIL with the exact reasons.

```powershell
python tools/check_gates.py projects/<project>              # all gates; writes reports/
python tools/check_gates.py projects/<project> --gate G3    # one gate in full detail
python tools/check_gates.py projects/<project> --verbose    # every issue of every gate
python tools/check_gates.py projects/<project> --no-write   # print only
```

It reads the same records as the handoff generator, plus the stage records the handoff does not carry: the intake, the discovery log, the ADR register, the four reviews, the specification and the planning summary. For each gate it combines:

- the gate's own checks — completeness and classification of the stage records, open BLOCKER questions that are not contained by scope, requirement-to-module mapping, coverage of in-scope requirements by features and tasks, priority scheme, honest dates, owned risks, the review checklists and findings;
- architecture governance at G6 — every standard architecture concern classified with its evidence (ARCHITECTURE DECISION REQUIRED when a choice is open, a failure when its question is a BLOCKER affecting in-scope work), the ADR register agreeing with the ADR files so no ID is reused or lost, proposed decisions visible, accepted principles evidenced, and the architecture review complete, covering every ADR in its current status, stating the current counts, and resolving every ARCHITECTURE CONFLICT by CHANGE PROPOSAL, NEW ADR or SUPERSEDE ADR;
- architecture drift — an ARCHITECTURE CONFLICT the validator reports (a record naming an option an accepted ADR rejected) fails the gate of the item that raised it (G6 for requirements, G9 for features and tasks) until the architecture review records it;
- the independent specification review at GR — everything `specification_review.py` verifies (below); G8 then requires GR and an approval dated after a passing review of the approved version;
- backlog readiness at GB — from `backlog-readiness.json`: some in-scope work READY and passing every Definition of Ready check; no READY task failing one; no dependency cycle, unresolved architecture conflict, serious specification finding on the backlog or broken traceability; approved scope; readiness histories that match the statuses; a new revision for every task changed since the baseline. Partial readiness, tasks not yet ready and every review flag are warnings;
- requirement-quality heuristics at G3 — unmeasured wording, implementation detail, requirements that may combine several needs, functional requirements without actor, trigger, permission rule or failure case, duplicate titles;
- every validator and generator finding, assigned to the gate it belongs to. Coverage and orphan warnings from the handoff validator are escalated to failures at the gate that requires coverage.

Gate GC — change impact reviewed — belongs to no stage and is evaluated on every run: an edit to a change-controlled record without an approved change record, an undecided or unresolved change, a READY task under change review, or a contradiction a change left behind fails it, and G12 and G13 fail while it does. A gate cannot pass on a failed earlier gate. Two further conditions are reported as **violations** and make the tool exit 1: `project-state.md` names a *Current stage* beyond a failing gate, or it records a gate as PASS (or PASS WITH WARNINGS) that the evidence does not support, or its specification review summary (the *Review measure* table) differs from what the review shows. Gates after the current stage are evaluated too and marked "not yet due"; their failures do not affect the exit code.

It writes `reports/gate-report.md` — every gate, its result and its reasons — `reports/dependency-graph.md`, a Mermaid graph of features, tasks, external dependencies and blocking questions with the deterministic execution order, and `reports/architecture-report.md` — the ADR counts, every decision with the requirements, features and tasks it reaches, the concern coverage, every detected conflict and every unresolved critical decision, which the architecture review copies its counts from, and `reports/specification-review-aid.md` (below). All four are generated; do not edit them. The gate report also lists the specification review summary to copy into `project-state.md`.

What it cannot do: decide whether a requirement is correct, whether two statements contradict, or whether a criterion really proves a requirement. Those judgements are recorded in the reviews, and the gate checks that the review is complete, current and free of open CRITICAL or MAJOR findings.

## backlog_readiness.py

Stage 10B, Backlog Readiness Validation ([WORKFLOW.md](../WORKFLOW.md) section 15). A generated task is not a ready task: every task earns READY by passing the Definition of Ready, which `validate_handoff.py` evaluates as named checks and stores in the task's `readiness`. This tool turns those results into the backlog view. It is also what `generate_handoff.py` uses to write `machine-handoff/backlog-readiness.json` and `backlog/readiness-report.md`.

```powershell
python tools/backlog_readiness.py projects/<project>            # summary; writes backlog/readiness-report.md
python tools/backlog_readiness.py projects/<project> --json     # the computed backlog-readiness.json
python tools/backlog_readiness.py projects/<project> --no-write # print only
```

It reports:

- **Backlog status.** READY (every active task), PARTIALLY_READY (a valid subset — useful work can start) or NOT_READY.
- **Counts and percentage.** Counts by planning status, and the percentage of active tasks that are READY and valid.
- **Per task.** The result, failed checks, failures, the status they point to, priority and sequence (kept separate), revision, related risks and accepted-risk review findings.
- **Validation.** Dependency cycles, architecture conflicts, traceability issues, unresolved critical findings, serious findings affecting the backlog, critical blockers, scope approval, and READY tasks failing the Definition of Ready.
- **Phases.** Each phase's readiness and the eight planning-completeness questions: what, why, which requirement, what success looks like, dependencies, constraints, blockers, verification.
- **Ready work sets.** WS-01 holds READY tasks with no prerequisite; each later set holds tasks whose prerequisites sit in earlier sets. WS-01 is also `executable_now` in `backlog.json`.
- **Coverage metrics**, to expose gaps rather than to be maximised.
- **Flags for review.** Tasks needing decomposition, judged by modules, workflows, actors, integrations, criteria and objectives rather than text length; fragmentation into microtasks; possible duplicates; contradictory tasks; missing error behaviour, with only the relevant cases; verification gaps; implementation-step titles.

Everything is computed from the machine-handoff bundle alone, so `validate_handoff.py` recomputes it and reports `BACKLOG_READINESS_MISMATCH` when the file disagrees with the tasks. Exit code 0 when some in-scope work is READY, 1 when none is, 2 when the tool cannot run.

## specification_review.py

Stage 8A, the Independent Specification Review ([WORKFLOW.md](../WORKFLOW.md) section 13, `templates/12`). The review is written by a SPECIFICATION REVIEWER who is not the specification's author (`prompts/specification-reviewer.md`). This tool verifies that the record can be relied on and computes what it concludes; it never edits a requirement, ADR or any other planning record.

```powershell
python tools/specification_review.py projects/<project>                 # status and issues; writes reports/specification-review-aid.md
python tools/specification_review.py projects/<project> --start-cycle   # freeze this cycle in reviews/history/, open the next
python tools/specification_review.py projects/<project> --json          # the computed specification-review.json
python tools/specification_review.py projects/<project> --no-write      # print only
```

It checks the parts of the review record in turn:

- **The header.** The review covers the current specification version and is numbered and dated. It names a reviewer who is not the author, and states how the reviewer is independent.
- **The checklist and questions.** Every review area has examined checklist rows, and every FAIL row cites an open REVIEW-### finding. The twelve review questions are answered, and every answer that reports a problem cites an open finding. The answer to "safe to use as the basis for backlog planning?" agrees with the result.
- **Each finding.** It has a valid severity, category and status, and the cycle that raised it. It has evidence; a CRITICAL or MAJOR finding also cites existing artifacts and the stage that resolves it. It has why it matters, the required action, and no duplicate.
- **Each closure.** RESOLVED is verified in a later cycle and records the resolution, who resolved it, the date, the changed artifacts and the verification. ACCEPTED_RISK is never CRITICAL, and it is approved by a named person who is neither author nor reviewer, with DEC-### or SRC-### evidence. Rejecting a serious finding needs the same human decision.
- **The conclusion.** The stated result and counts are those the findings support: unresolved CRITICAL or MAJOR gives FAIL; open MINOR, OBSERVATION or accepted risk gives PASS WITH WARNINGS; none gives PASS.
- **The history.** Every closed cycle is listed and frozen in `reviews/history/specification-review-cycle-###.md`, and each history row agrees with its snapshot. No finding in a snapshot has disappeared, and none is backdated.
- **Contradictions.** Every possible contradiction the heuristics detect — one versus many, permanent deletion versus retention, anonymous versus authenticated access — is a finding or is dismissed with a reason.
- **Changes.** No approved change is dated after the review. A MEDIUM or higher change fails the review and requires a new cycle; a LOW one warns.

`--start-cycle` refuses to close a cycle whose record is incomplete or incoherent, and never overwrites a snapshot. It copies the review byte for byte into the history and appends the cycle's row to the history table. It then sets the next cycle number and resets the date, the overall result and every checklist row and review question to NOT REVIEWED, so nothing is carried into the next cycle unexamined. Findings are left exactly as they are.

`reports/specification-review-aid.md` lists candidates for the reviewer to judge, computed from the records. It covers contradictions; traceability re-derived from the requirement, feature, task and ADR records rather than read from the generated traceability; assumptions that live requirements rest on; vague acceptance criteria; the scenario families each workflow mentions; missing permission rules and undecided security concerns; integrations and dependencies without risks; terminology used side by side; the data model; change state; and the validator's findings grouped by review area. A candidate is never a finding by itself: heuristics miss problems and raise false alarms.

Exit code 0 when the review passes (warnings allowed), 1 when it fails, is missing or `--start-cycle` is refused, 2 when the tool cannot run.

## analyze_change_impact.py

`analyze-change-impact`: what a change affects, what is now stale or invalid, and what must be reviewed ([WORKFLOW.md](../WORKFLOW.md) section 19.5). It changes no source record.

```powershell
python tools/analyze_change_impact.py projects/<project> --baseline --reason "Specification 1.0 approved"   # trusted state
python tools/analyze_change_impact.py projects/<project> CHANGE-007          # analyse a recorded change
python tools/analyze_change_impact.py projects/<project> FR-021 --type REQUIREMENT_CHANGE   # what-if, no record
python tools/analyze_change_impact.py projects/<project> --detect            # records changed since the baseline
python tools/analyze_change_impact.py projects/<project> --summary           # change dashboard
```

| Mode | Writes |
| --- | --- |
| `--baseline` | `changes/baseline.json` — the normalised text of every change-controlled record; the previous baseline is archived in `changes/history/`. Refused (exit 1) while a change is unrecorded, approved but not implemented, or implemented with artifacts under review |
| `CHANGE-###` | `changes/CHANGE-###-impact-report.md` |
| Record IDs | `reports/impact-<IDs>.md` |
| `--detect`, `--summary` | nothing |

For a change it runs ten steps and prints each: identify the changed artifacts; load the relationships; detect direct dependencies; detect downstream dependencies; detect upstream assumptions; classify impact; calculate severity; mark affected items for review; withdraw readiness; write the report.

The impact graph links requirements (derivation, dependencies), workflows, entities, modules, ADRs (what they constrain, what they govern, supersession, dependencies), features, tasks, tests, phases, the discovery registers and detail records (`PAGE-###`, `API-###`, `INT-###` under `specification/`). Each link is strong (an explicit dependency) or weak (membership or context). Impact one link away is **DIRECT**; further, through requirements, modules, ADRs, external dependencies, features and tasks, it is **INDIRECT**; context records are reported but pass nothing on. **POTENTIAL** impact is an upstream assumption, a requirement sharing a module, or a record that only mentions the change. Confidence is **CONFIRMED** when every link on the path is strong, **LIKELY** when one is weak, **POSSIBLE** for potential impact. Severity (CRITICAL / HIGH / MEDIUM / LOW) is computed with the reasons that set it.

The report states the previous (baseline) and current text of each changed artifact, direct, indirect and potential impact with confidence and review state, the artifacts marked for review and the readiness withdrawn, the readiness of every affected task, the required reviews for the change type with the records found in each area, the new work that may be required, the roadmap, risk and document impact, the gates to re-run, and the required actions.

Review states are not written into any record: `generate_handoff.py` derives them from the change records and the baseline into `machine-handoff/changes.json`, and the Definition of Ready withdraws readiness from every task that is not CURRENT.

`impact_analysis.py` is kept as an alias of the what-if mode: `python tools/impact_analysis.py projects/<project> FR-014` runs the same analysis without a change record.

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

Required: git, the two diagram skills, `python-docx`, `openpyxl` and `jsonschema`. Optional and reported with install commands: the draw.io CLI (image export), Graphviz (automatic layout), and a working `python3` command. Before preparing the renderer it pins the Excalidraw render page's import to `@excalidraw/excalidraw@0.18.0` from jsDelivr in every installed copy of the skill, including one provided by an account sync: the skill's unversioned import currently resolves to a build that never loads. Only that one line is changed, a version the skill's authors pin themselves is left alone, and `--check` reports any copy a later sync has reverted. The run ends with a render smoke test, because the render page fetches its library from a CDN at render time and a restricted network breaks verification silently.

## build_deliverables.py

It converts the completed deliverable Markdown under `projects/<project>/deliverables/` into the Word and Excel package described in [WORKFLOW.md](../WORKFLOW.md) section 22.

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
![DIAG-001 — Purchase approval, TO-BE. Drawn in BPMN 2.0 notation; not a BPMN 2.0 XML interchange file.](../diagrams/exported/diag-001-purchase-approval-tobe.png)
```

The path is relative to the Markdown file. A diagram wider than the text column is scaled down to fit; a smaller one keeps its natural size rather than being blown up. Images are Word-only and never enter a workbook.

A referenced file that does not exist is a build **error**, so a broken diagram reference cannot ship silently. An image with no caption is a warning — captions carry the DIAG ID and the notation or model-status statement, so a reader can find the specification behind the picture.

Diagram sources live in the project's `diagrams/source/` folder and exports in `diagrams/exported/`; a deliverable references an export as `../diagrams/exported/<file>.png`. This tool embeds them; it does not create them. Diagrams are generated with the Excalidraw and draw.io skills as described in [WORKFLOW.md](../WORKFLOW.md) section 21.

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

## generate_handoff.py

`generate-machine-handoff` for one project. It reads the structured parts of the Markdown records — record blocks and register tables, never free prose — and writes the machine-handoff contract described in [WORKFLOW.md](../WORKFLOW.md) section 23.

```powershell
python -m pip install -r tools/requirements-handoff.txt

# Generate, validate and write machine-handoff/ and traceability/requirement-map.md
python tools/generate_handoff.py projects/<project>

# Validate and report only; write nothing
python tools/generate_handoff.py projects/<project> --check

# Reproduce a byte-identical handoff
python tools/generate_handoff.py projects/<project> --generated-at 2026-09-26T10:00:00Z
```

| Option | Effect |
| --- | --- |
| `--check` | Run every step and report; write nothing |
| `--out DIR` | Output directory; defaults to `<project>/machine-handoff` |
| `--generated-at TS` | Timestamp recorded in `project.json`; defaults to `SOURCE_DATE_EPOCH`, then the current UTC time. Everything else is already deterministic |
| `--no-map` | Do not write `traceability/requirement-map.md` |

Exit code 0 means valid (warnings allowed), 1 means validation errors, 2 means the tool could not run (not a project folder, `jsonschema` missing).

### Steps and output

```text
generate-machine-handoff: tools/tests/fixtures/sample-project
 1. Specification              PASS
 2. Requirements               PASS
 3. Backlog readiness          PASS
 4. Generate JSON              DONE - written to tools/tests/fixtures/sample-project/machine-handoff (15 JSON files)
 5. JSON schemas               PASS
 6. Traceability               PASS
 7. Blocked / non-ready tasks  1
      TASK-004 NEEDS_DISCOVERY: Title or description contains TBD. An acceptance criterion contains TBD. Unresolved blocker: The lockout threshold is unknown until Q-002 is answered (+1 more)
 8. Summary
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

Every finding is then listed as `ERROR|WARNING <step> <CODE> [file:line]: message`, located at the Markdown line where it can be fixed whenever the problem is in a source record.

| File | Contents | Schema |
| --- | --- | --- |
| `handoff-manifest.json` | The entry point for engineering: contract version, `handoff_status` (`READY_FOR_HANDOFF`, `NOT_READY`, `INVALID`), validation flags, every file with its role and SHA-256, content fingerprint, `ready_tasks`, and each task's revision, status and content hash | `integration/handoff-manifest.schema.json` |
| `project.json` | Identity, specification status and approval, specification review summary, `handoff_status`, counts, source fingerprint, SHA-256 of every other file | `project.schema.json` |
| `requirements.json` | Source inventory, scope register, and every GOAL, BR, RULE, FR, NFR, DR, IR, SR, UXR and TR with the ADRs that affect it | `requirements.schema.json`, `requirement.schema.json` |
| `architecture.json` | Status summary, principles, module register, architecture concern coverage and every ADR (lifecycle, owner, approval evidence, alternatives, consequences, risks, constraints, links) | `architecture.schema.json`, `architecture-decision.schema.json` |
| `decisions.json` | Decision log, questions (with `priority`, `blocking` and `resolved`), assumptions, risks | `decisions.schema.json` |
| `backlog.json` | Epics, features (with the ADRs each must respect), phases, external dependencies, a task index, the deterministic sequence, `ready_task_ids`, `executable_now` | `backlog.schema.json` |
| `tasks/TASK-###.json` | One file per task: the full task contract, with its `revision` and `content_hash` | `task.schema.json`; the fields engineering reads, `integration/task-handoff.schema.json` |
| `tests.json` | Test definitions | `tests.schema.json` |
| `domain.json` | Processes and business entities | `domain.schema.json` |
| `traceability.json` | Per-requirement, per-task and per-ADR links, coverage, delivery slots | `traceability.schema.json` |
| `changes.json` | Baseline, records changed since it, unrecorded changes, every change with its classified impact and consequences, review states of every artifact not CURRENT, dashboard summary | `changes.schema.json` |
| `backlog-readiness.json` | Backlog status, summary, validation, coverage, phases with planning questions, ready work sets, review flags, and every task's readiness | `backlog-readiness.schema.json` |
| `specification-review.json` | The independent specification review: reviewed version, cycle, reviewer and author, overall result, counts, every cycle, every REVIEW-### finding with its resolution, and defects in the review record | `specification-review.schema.json` |
| `validation-report.json` | Every error and warning, including Markdown-level findings, and the non-ready tasks with reasons | `validation-report.schema.json` |

The handoff is written even when it is invalid, marked `handoff_status: invalid`, so an older `ready` output never survives beside changed sources. `--check` never writes.

### Determinism

The same records always produce the same bytes, apart from `generated_at`. Lists are ordered by natural ID order; the task sequence is a topological sort that breaks ties by phase order, then priority, then ID; every reverse link (a task's `blocks`, an epic's features, a feature's tasks, a requirement's downstream requirements) is derived from the one direction written in the records. Fix `--generated-at` to reproduce a handoff byte for byte.

### Engineering contract

`handoff_contract.py` holds the parts of the handoff that exist for the engineering consumer: the task content hash (basis `task-intent/1`), the manifest builder and its consistency checks, and the hash lock over `schemas/integration/`:

```bash
python tools/handoff_contract.py --check-lock   # schemas/integration/ matches contract.json
python tools/handoff_contract.py --write-lock   # after a deliberate contract change
```

The manifest's `handoff_version` is read from the previous manifest in the output folder: unchanged content keeps it, changed content increments the minor number, and a new specification version starts a new major number. See WORKFLOW.md section 23, *Engineering boundary*.

## validate_handoff.py

Validates a machine-handoff directory from the JSON alone, so a downstream system can check the copy it received before consuming it.

```powershell
python tools/validate_handoff.py projects/<project>/machine-handoff            # human-readable
python tools/validate_handoff.py projects/<project>/machine-handoff --json     # findings as JSON
python tools/validate_handoff.py <dir> --sources projects/<project>            # also detect staleness
```

When the directory sits inside a project folder the staleness check runs automatically; `--no-sources` turns it off. It checks:

| Check | Error codes |
| --- | --- |
| JSON syntax, required files, unexpected files | `JSON_SYNTAX`, `MISSING_FILE`, `UNEXPECTED_FILE` |
| Conformance to the schemas in `schemas/` | `SCHEMA_VIOLATION`, `UNSUPPORTED_SCHEMA_VERSION` |
| Unique IDs; file names match task IDs | `DUPLICATE_ID`, `TASK_FILE_NAME` |
| Every referenced ID exists | `UNKNOWN_REFERENCE` |
| Cycles in task dependencies, parents, requirement derivation, modules, ADR supersession and ADR dependencies | `DEPENDENCY_CYCLE`, `SELF_DEPENDENCY`, `PARENT_CYCLE`, `DERIVATION_CYCLE`, `MODULE_HIERARCHY_CYCLE`, `ADR_SUPERSEDE_CYCLE`, `ADR_DEPENDENCY_CYCLE` |
| ADR lifecycle: a proposed ADR names its deciding question; every other status names a decision owner and approval evidence; an accepted ADR states context, decision and rationale | `ADR_DECISION_QUESTION_MISSING`, `ADR_APPROVAL_MISSING`, `ADR_INCOMPLETE` |
| No two accepted ADRs conflict; supersession links agree and only an accepted ADR replaces another; accepted ADRs rest on no inactive one | `ADR_ACTIVE_CONFLICT`, `ADR_SUPERSESSION_MISMATCH`, `ADR_INACTIVE_DEPENDENCY` |
| No live requirement, feature or task relies on a rejected, superseded or deprecated ADR | `ADR_INACTIVE_REFERENCE` |
| Definition of Ready for every READY task, as named checks — including a passing specification review of the current version, no open architecture conflict or serious review finding, stated impacts, and 'not under change review'; stored `readiness` and readiness gaps match the rules; the readiness history matches the status | `READY_NOT_MET`, `READINESS_MISMATCH`, `READINESS_HISTORY` |
| `backlog-readiness.json` and `project.json` `backlog_status` match the readiness recomputed from the tasks; `executable_now` is the first ready work set | `BACKLOG_READINESS_MISMATCH`, `BACKLOG_MISMATCH` |
| In-release requirements have acceptance criteria | `EMPTY_ACCEPTANCE_CRITERIA` |
| Hierarchy and phase order agree | `HIERARCHY_MISMATCH`, `PHASE_ORDER` |
| `backlog.json` agrees with the task files; sequence is the deterministic order | `BACKLOG_MISMATCH`, `DERIVED_MISMATCH` |
| Traceability and ADR links (requirements, features, tasks, per-ADR reach) match what they are derived from | `TRACEABILITY_MISMATCH`, `ADR_LINK_MISMATCH` |
| Review states and the change summary match the change records; change references exist | `CHANGE_STATE_MISMATCH`, `COUNT_MISMATCH`, `UNKNOWN_REFERENCE` |
| Open questions are complete and current | `OPEN_QUESTION_MISSING`, `RESOLVED_QUESTION_LISTED`, `QUESTION_STATE_MISMATCH` |
| Specification approval is consistent | `APPROVED_WITHOUT_SPECIFICATION`, `APPROVAL_VERSION_MISMATCH` |
| The specification review's result and counts are the ones its findings support; no CRITICAL finding is an accepted risk; every closed finding has a resolution; every cycle is listed; `project.json` agrees | `SPEC_REVIEW_RESULT_MISMATCH`, `SPEC_REVIEW_COUNT_MISMATCH`, `SPEC_REVIEW_CRITICAL_ACCEPTED`, `SPEC_REVIEW_UNRESOLVED_CLOSURE`, `SPEC_REVIEW_HISTORY`, `SPEC_REVIEW_MISMATCH` |
| Files are unchanged since generation and none is missing or extra | `ARTIFACT_HASH_MISMATCH`, `ARTIFACT_UNLISTED`, `ARTIFACT_MISSING`, `COUNT_MISMATCH` |
| Sources have not changed since generation | `STALE_HANDOFF` |
| `project.json` claims no better status than the evidence | `HANDOFF_STATUS_MISMATCH` |

Warnings cover coverage gaps (`REQUIREMENT_WITHOUT_TASK`, `REQUIREMENT_WITHOUT_TEST`, `REQUIREMENT_NOT_REALISED`, `NO_BUSINESS_SOURCE`), orphans (`ORPHAN_TASK`, `ORPHAN_TEST`), a task on a deferred requirement, a specification review of another version (`SPEC_REVIEW_STALE`), architecture findings (`ADR_NO_ALTERNATIVES`, `ADR_NO_CONSTRAINTS`, `VAGUE_CONSTRAINT`, `ADR_IMPLEMENTATION_DETAIL`, `ADR_DECISION_PENDING`, `ADR_DEPENDS_ON_PROPOSED`, `ADR_FILE_NAME`), `ARCHITECTURE_CONFLICT` — a live requirement, feature or task that mentions an option an accepted ADR considered and rejected, which `check_gates.py` turns into a failure until the architecture review records it — and — from the generator — IDs mentioned in human documents that no record defines (`UNDEFINED_ID_IN_DOCUMENT`), retired ID forms (`LEGACY_ID`) and a deliverable task table that disagrees with the cards (`DELIVERABLE_OUT_OF_DATE`).

Artifact hashes are computed over LF-normalized bytes, so a Git checkout that converts line endings is not mistaken for an edit. The repository's `.gitattributes` keeps handoff JSON in LF regardless.

## Tests

```powershell
python -m unittest discover -s tools/tests -v
```

`tools/tests/fixtures/sample-project/` is a deliberately small fictional project, labelled as a fixture in every file. It is not a business project and not a template. It sits at stage 13 with gates G1–G12, GR and GB passing, and its specification review is in its second cycle (the first is frozen in `reviews/history/`), and its committed `machine-handoff/` and `traceability/requirement-map.md` are the reference example of a complete handoff. `test_handoff.py` regenerates the handoff and fails if the output drifts, then breaks the fixture one way at a time to prove each Definition of Ready rule and validation check fires. `test_gates.py` does the same for every gate, the workflow-state violations and the impact analysis. `test_changes.py` covers change-impact analysis: the baseline and its refusal, detection of unrecorded edits, impact levels and confidence, severity, the lifecycle, dispositions and review states, readiness withdrawal, gate GC and `changes.json`. `test_backlog_readiness.py` covers backlog readiness: the named Definition of Ready checks and the status each failure points to, planning statuses, readiness history, partial readiness and work sets, dependencies and cycles, criteria alignment, impacts, sensitive-work security, blocking risks, architecture conflicts, review findings, feature coverage, revisions, gate GB and the heuristic flags. `test_specification_review.py` covers the independent specification review: reviewer independence, the result rule, accepted risks, resolutions verified in a later cycle, evidence and duplicate findings, the checklist and review questions, cycle history and `--start-cycle`, contradiction candidates, readiness and `specification-review.json`, the project-state summary and approval after review. `test_architecture.py` covers architecture governance: concern coverage, the ADR lifecycle and approval, the register, supersession, conflicts between active decisions, references to inactive decisions, drift and its review, ADR impact analysis and `architecture.json`.
