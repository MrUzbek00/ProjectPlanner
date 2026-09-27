# Per-project Records

Create one folder per actual business project after receiving its initial idea or materials. This directory intentionally contains no fictional business project; the only fixture project lives under `tools/tests/fixtures/` and exists to test the tools.

Every project folder separates three layers. **Source** records are authored Markdown and are the only place facts are written. **Generated** files — reports, the requirement map, diagram exports, Word and Excel builds, the machine handoff — are produced from them and never edited by hand. The stage column shows when each record is started; most records keep being updated afterwards.

```text
projects/<project-folder>/
  project-state.md                  SOURCE  stage 1+  identity, current stage, gate results, approval record
  sources/                          SOURCE  stage 1+  originals or source-location references

  discovery/                        SOURCE
    project-intake.md                       stage 1   the fourteen intake items, classified
    sources.md                              stage 1   source inventory (SRC-###)
    discovery-log.md                        stage 2   coverage of the fourteen discovery categories
    discovery.md                            stage 2   seven-part initial analysis
    open-questions.md                       stage 1+  the one question register (Q-###), prioritised
    assumptions.md                          stage 1+  assumptions (ASM-###)
    risks.md                                stage 1+  risk register (RISK-###)
    decisions.md                            stage 1+  decision log (DEC-###)
    dependencies.md                         stage 2+  external dependencies (DEP-###)
    registers.md                            stage 2+  stakeholders, glossary, recommendations
    rounds/round-01.md                      stage 2+  dated question/answer history

  specification/                    SOURCE
    business-requirements.md                stage 3   GOAL-### and BR-### record blocks
    business-rules.md                       stage 3   RULE-###
    functional-requirements.md              stage 3   FR-###
    non-functional-requirements.md          stage 3   NFR-###
    data-requirements.md                    stage 3   DR-###
    integration-requirements.md             stage 3   IR-###
    security-requirements.md                stage 3   SR-###
    ux-requirements.md                      stage 3   UXR-###
    technical-requirements.md               stage 3   TR-###, if any
    process-model.md                        stage 4   PROC-### processes, permissions, states
    domain-model.md                         stage 4   ENT-### business entities
    solution-structure.md                   stage 5   modules (MOD-###), system context
    scope.md                                stage 5   scope register (SCOPE-###)
    technical-specification.md              stage 7   the 26-section specification
    requirements/<FR-ID>.md                 stage 7   detail records when needed
    pages/<PAGE-ID>.md                      stage 7   page/form/table/action records

  architecture/                     SOURCE  stage 6 — architecture governance
    README.md                               how decisions are governed in this project
    architecture-register.md                ADR ledger (every ADR ID ever assigned) and concern coverage
    principles.md                           architecture principles (PRIN-###)
    ADR-001-<short-title>.md                one architecture decision record per file; never deleted

  reviews/                          SOURCE
    requirement-quality-review.md           stage 3
    architecture-review.md                  stage 6
    specification-review.md                 stage 8A  independent review: REVIEW-### findings, checklist, cycle history
    history/specification-review-cycle-001.md       every closed review cycle, frozen; never edited or deleted
    final-planning-review.md                stage 12

  backlog/                          SOURCE  stage 9+ — only after gates GR and G8
    backlog.md                              epics, features, index, dependency edges, phases
    tasks/TASK-001.md                       one card per task — canonical, with its readiness history
    readiness-report.md             GENERATED  backlog readiness: status, per-task checks, work sets, flags

  quality/                          SOURCE
    acceptance-tests.md                     stage 9   TEST-### record blocks

  traceability/
    traceability.md                 SOURCE     stage 3+  reviewed coverage matrix and dispositions
    requirement-map.md              GENERATED            GOAL → BR → FR → FEAT → TASK → TEST chains; ADR → requirement → feature → task

  reports/                          GENERATED  gate report, dependency graph, architecture report, impact analyses
    gate-report.md                          every gate's result and reasons (check_gates.py)
    specification-review-aid.md             candidates for the specification reviewer to judge (check_gates.py, specification_review.py)
    dependency-graph.md                     dependency graph and execution order (check_gates.py)
    impact-<IDs>.md                         what-if impact analyses (analyze_change_impact.py)

  changes/                          SOURCE  change control, once the specification is approved
    baseline.json                   BASELINE  trusted state of every change-controlled record; written only by --baseline
    history/baseline-<time>.json    BASELINE  previous baselines, archived
    CHANGE-001.md                   SOURCE  one change record per file (templates/35)
    CHANGE-001-impact-report.md     GENERATED  impact report from tools/analyze_change_impact.py

  diagrams/
    source/                         SOURCE     stage 13  .excalidraw and .drawio files
    exported/                       GENERATED            rendered PNG / SVG

  deliverables/                     HUMAN DELIVERABLES — stage 13, only after gate G12
    planning-summary.md                     the fifteen planning questions answered
    prd.md  brd.md  srs.md  sow.md          audience documents that restate the records
    user-journey-stories.md
    wireframes-uiux.md
    project-plan-roadmap.md
    package-manifest.md
    build/                          GENERATED  .docx and .xlsx

  machine-handoff/                  GENERATED  stage 13 — never edit
    handoff-manifest.json           entry point for downstream engineering
    project.json  requirements.json  domain.json  architecture.json  decisions.json
    backlog.json  traceability.json  tests.json  changes.json  specification-review.json
    backlog-readiness.json
    validation-report.json
    tasks/TASK-001.json

  delivery/handoff.md               SOURCE  planning handoff
  baselines/<approved-version>/     SOURCE  snapshot of files covered by approval
```

Copy templates as the stages need them and replace placeholders with sourced content. Do not fill directories with blank files to resemble progress; progress is a passing gate. Keep draft and approved revisions distinguishable and include normative linked files in the approval manifest.

## Where each fact lives

| Fact | Canonical location | Template |
| --- | --- | --- |
| What was known at the start, and how well | `discovery/project-intake.md` | 29 |
| Discovery coverage by category | `discovery/discovery-log.md` | 30 |
| A question, assumption, risk, decision, dependency, source | Its row in the matching `discovery/` register | 02 |
| A requirement's ID, status, scope, confidence, links, acceptance criteria | Its record block in `specification/*-requirements.md` or `business-rules.md` | 26 |
| A process, a state transition | `specification/process-model.md` | 03 |
| A business entity | `specification/domain-model.md` | 32 |
| A module | `specification/solution-structure.md` | 37 |
| An architecture decision, its status, constraints and links | `architecture/ADR-###-<short-title>.md` | 28 |
| Which ADR IDs exist; how each architecture concern stands | `architecture/architecture-register.md` | 27 |
| An architecture principle | `architecture/principles.md` | 38 |
| A scope boundary | `specification/scope.md` | 33 |
| A review's checklist and findings, including architecture conflicts | `reviews/` | 12, 31, 34, 39 |
| A specification review finding (REVIEW-###), its status and resolution; the review result and cycle | `reviews/specification-review.md`; closed cycles in `reviews/history/` | 12 |
| An epic, feature or phase | Its record block in `backlog/backlog.md` | 07, 09 |
| A task — status, dependencies, constraints, tests | `backlog/tasks/TASK-###.md` | 08 |
| A test definition | `quality/acceptance-tests.md` | 11 |
| A change, its decision, its dispositions and its impact | `changes/CHANGE-###.md` | 35 |
| The approved state a change is measured against | `changes/baseline.json` (generated by `--baseline`, never edited) | — |

The technical specification and the deliverables restate these records and link to them; they never hold a second, competing definition. The tools warn about any ID a document mentions that no record defines.

## Commands

| Purpose | Command | Writes |
| --- | --- | --- |
| Evaluate every gate | `python tools/check_gates.py projects/<project-folder>` | `reports/gate-report.md`, `reports/dependency-graph.md`, `reports/architecture-report.md`, `reports/specification-review-aid.md` |
| Verify the specification review; print its result | `python tools/specification_review.py projects/<project-folder>` | `reports/specification-review-aid.md` |
| Report backlog readiness | `python tools/backlog_readiness.py projects/<project-folder>` | `backlog/readiness-report.md` |
| Close a review cycle and open the next | `python tools/specification_review.py projects/<project-folder> --start-cycle` | `reviews/history/specification-review-cycle-###.md`, `reviews/specification-review.md` |
| Record the change-control baseline | `python tools/analyze_change_impact.py projects/<project-folder> --baseline --reason "..."` | `changes/baseline.json` |
| Analyse a recorded change | `python tools/analyze_change_impact.py projects/<project-folder> CHANGE-007` | `changes/CHANGE-007-impact-report.md` |
| What-if analysis of a record (including an ADR) | `python tools/analyze_change_impact.py projects/<project-folder> FR-014 --type REQUIREMENT_CHANGE` | `reports/impact-FR-014.md` |
| What changed since the baseline; change dashboard | `python tools/analyze_change_impact.py projects/<project-folder> --detect` / `--summary` | nothing |
| Validate the plan without writing the handoff | `python tools/generate_handoff.py projects/<project-folder> --check` | nothing |
| Generate the machine handoff | `python tools/generate_handoff.py projects/<project-folder>` | `machine-handoff/`, `traceability/requirement-map.md` |
| Re-validate a handoff | `python tools/validate_handoff.py projects/<project-folder>/machine-handoff` | nothing |
| Build Word and Excel | `python tools/build_deliverables.py projects/<project-folder>/deliverables` | `deliverables/build/` |

Everything marked GENERATED is regenerated output: change the source Markdown and rerun the command rather than editing it.

## Resume

Read `project-state.md`, then run `python tools/check_gates.py projects/<project-folder>` and continue at the first failing gate. Before asking anything new, read the latest round, `discovery/open-questions.md`, `discovery/decisions.md` and the latest review. A copied template remains a template until populated and reviewed.
