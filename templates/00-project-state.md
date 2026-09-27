# Project State

Template only — replace placeholders with evidence; no project approval is implied.

The first table, the gate history, the specification review summary and the approval record are read by `tools/generate_handoff.py` and `tools/check_gates.py`. Keep their field names. `Project ID` is an upper-case identifier such as `ACME` or `PROJECT-001` and stays the same for the life of the project. *Current stage* is the stage being worked on, as a number from 1 to 13 (stage 8 covers 8A, the independent specification review, and 8B, resolution and approval; stage 10 covers 10A, dependencies and priorities, and 10B, backlog readiness validation): every gate before it must pass, and `check_gates.py` reports a violation if one does not. *Priority scheme* is `Levels` (Critical, High, Medium, Low) or `MoSCoW` (Must, Should, Could, Won't), chosen once for the whole project by stage 10. *Specification status* is NOT STARTED, DRAFT, IN REVIEW, APPROVED or SUPERSEDED.

| Field | Value |
| --- | --- |
| Project ID | TBD |
| Project folder | TBD |
| Project name | TBD |
| Client / department | TBD |
| Business owner / decision authority | TBD |
| Document language | TBD |
| Current stage | 1 — Project Intake |
| Priority scheme | TBD |
| Specification version | TBD |
| Specification status | NOT STARTED |
| Approved baseline version / location | None |
| Last updated / by | TBD |
| Latest completed interview round | None |
| Current focus | Obtain initial project context and analyze actual materials |
| Next action | TBD |

## Project model snapshot

- Confirmed objective and success measures: TBD
- Confirmed scope: TBD
- Explicit exclusions / deferred scope: TBD
- AS-IS / TO-BE process references: TBD
- Stakeholders / roles: TBD
- Module / page / entity references: TBD
- Key confirmed rules and decisions: TBD
- Confirmed technology constraints: TBD
- Assumptions: TBD
- Recommendations awaiting decision: TBD
- Material dependencies: TBD

## Open blockers

| Question / finding ID | Missing decision | Affected artifacts / requirements | Why it blocks | Decision owner | Next action |
| --- | --- | --- | --- | --- | --- |

## Artifact index

| Artifact | Relative path | Version | Status | Last review | Evidence / source |
| --- | --- | --- | --- | --- | --- |

## Gate history

Record the result `tools/check_gates.py` printed — PASS, PASS WITH WARNINGS or FAIL — never a result it did not print. Status otherwise is NOT STARTED or IN PROGRESS. Claiming PASS for a gate that fails, or PASS for one that passes only with warnings, is reported as a violation.

| Gate | Status | Evidence | Date | Outstanding conditions |
| --- | --- | --- | --- | --- |
| G1 — Intake complete | NOT STARTED | | | |
| G2 — Discovery ready | NOT STARTED | | | |
| G3 — Requirements ready | NOT STARTED | | | |
| G4 — Models ready | NOT STARTED | | | |
| G5 — Solution and scope ready | NOT STARTED | | | |
| G6 — Architecture ready | NOT STARTED | | | |
| G7 — Specification complete | NOT STARTED | | | |
| GR — Specification reviewed | NOT STARTED | | | Stage 8A; independent review by a reviewer who is not the author |
| G8 — Specification ready | NOT STARTED | | | |
| G9 — Backlog decomposed | NOT STARTED | | | |
| G10 — Sequencing ready | NOT STARTED | | | Stage 10A |
| GB — Backlog ready | NOT STARTED | | | Stage 10B; backlog readiness validation |
| G11 — Roadmap ready | NOT STARTED | | | |
| G12 — Planning validated | NOT STARTED | | | |
| G13 — Planning package ready | NOT STARTED | | | |
| GC — Change impact reviewed | NOT STARTED | | | Continuous; required by G12 and G13 |

When a change reopens an earlier stage, set *Current stage* back to it and re-run the gates from there; an earlier PASS does not survive a change to the records it was based on.

## Specification review

The independent specification review (stage 8A, `reviews/specification-review.md`), as `tools/specification_review.py` or the gate report prints it. Never state a better result, a later cycle or fewer open findings than the records show: `check_gates.py` reports that as a violation. While the result is FAIL, nothing is backlog-ready or planning-complete.

| Review measure | Value |
| --- | --- |
| Specification review | NOT REVIEWED |
| Last review cycle | 0 |
| Open critical | 0 |
| Open major | 0 |
| Open minor | 0 |
| Open observations | 0 |
| Accepted risks | 0 |

## Deliverable package status

| Deliverable | Markdown authored | Word generated | Excel sheets included | Export verified | Outstanding |
| --- | --- | --- | --- | --- | --- |
| Product Requirements Document | NOT STARTED | | | | |
| Business Requirements Document | NOT STARTED | | | | |
| Software Requirements Specification | NOT STARTED | | | | |
| Statement of Work and Scope Statement | NOT STARTED | | | | |
| User Journey and User Stories | NOT STARTED | | | | |
| Wireframes and UI/UX Specification | NOT STARTED | | | | |
| Project Plan and Roadmap | NOT STARTED | | | | |
| Deliverable Package Manifest | NOT STARTED | | | | |

| Diagram | DIAG ID | Tool | Specified | Generated | Rendered and inspected | Embedded in |
| --- | --- | --- | --- | --- | --- | --- |
| BPMN process diagrams | | Excalidraw skill | NOT STARTED | | | |
| Proposed data model (ER) | | draw.io skill | NOT STARTED | | | |
| Entity state diagrams | | draw.io skill | NOT STARTED | | | |

Last build command and date: not run. Build output location: TBD. Diagram source location: `diagrams/source/`; exports: `diagrams/exported/`.

## Machine handoff status

| Field | Value |
| --- | --- |
| Last `generate_handoff.py` run | Not run |
| Result / handoff status | TBD — copy from the tool's summary, never from memory |
| Backlog readiness | TBD — READY, PARTIALLY READY or NOT READY, from `backlog/readiness-report.md`; never better than the report |
| Ready / blocked / other non-ready tasks | TBD |
| Errors / warnings | TBD |
| Source fingerprint | TBD — from `machine-handoff/project.json` |

## Change control

- Baseline: `changes/baseline.json`, recorded TBD with `python tools/analyze_change_impact.py projects/<project> --baseline` once the specification is approved
- Open changes: TBD (CHANGE-### and status)
- Change state: copy the summary from `python tools/analyze_change_impact.py projects/<project> --summary` — open changes, critical changes, items needing review, stale tasks, invalid READY tasks, unrecorded changes

## Approval record

No approval recorded. Populate only from an actual user/authorized stakeholder approval, given after the independent specification review of that version passes (gate GR); `check_gates.py` fails G8 when the approval date precedes every passing review of the version. The generator treats the specification as approved only when *Specification status* is APPROVED and a row below names an approver for that exact *Specification version*.

| Approval ID | Approver / authority | Exact statement or attributable reference | Date | Specification version | Manifest / baseline path | Conditions / exclusions |
| --- | --- | --- | --- | --- | --- | --- |

## Approved revision manifest

Include the central specification and every normative linked requirement, page, process, model and acceptance definition. Preserve the approved content as a baseline; a version label alone does not preserve it.

| Relative path | Revision / content fingerprint if available | Included in approval | Notes |
| --- | --- | --- | --- |

## Session handoff

- Work completed: TBD
- New confirmations and source references: TBD
- Changes affecting prior decisions: TBD
- Pending user questions: TBD
- Independent work that can continue: TBD
- Exact next step: TBD
