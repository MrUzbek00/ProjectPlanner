# Machine Handoff Schemas

JSON Schema (draft 2020-12) contract for the files under `projects/<project>/machine-handoff/`. `tools/validate_handoff.py` validates every generated file against these schemas, then checks what a schema cannot express: references, cycles, the Definition of Ready, agreement between files, hashes and staleness. See [WORKFLOW.md](../WORKFLOW.md) section 23.

| Schema | Validates |
| --- | --- |
| `common.schema.json` | Shared definitions: every ID pattern, status and enum. The single definition of the identifier conventions |
| `project.schema.json` | `project.json` |
| `requirements.schema.json` | `requirements.json`, using `requirement.schema.json` for each entry |
| `requirement.schema.json` | One GOAL, BR, RULE, FR, NFR, DR, IR, SR, UXR or TR requirement |
| `domain.schema.json` | `domain.json` — processes and business entities |
| `architecture.schema.json` | `architecture.json` — summary, principles, modules, concern coverage — using `architecture-decision.schema.json` for each ADR |
| `architecture-decision.schema.json` | One architecture decision record |
| `decisions.schema.json` | `decisions.json` — decision log, questions, assumptions, risks |
| `backlog.schema.json` | `backlog.json` |
| `task.schema.json` | Each `tasks/TASK-###.json` |
| `tests.schema.json` | `tests.json` |
| `traceability.schema.json` | `traceability.json` |
| `validation-report.schema.json` | `validation-report.json` |
| `changes.schema.json` | `changes.json` — change records with their analysed impact, detected and unrecorded changes, review states, summary |
| `backlog-readiness.schema.json` | `backlog-readiness.json` — backlog status, summary, validation, coverage, phases, ready work sets, flags, per-task readiness |
| `specification-review.schema.json` | `specification-review.json` — the independent specification review: reviewed version, cycle, reviewer and author, overall result, counts, every cycle, every REVIEW-### finding with its resolution, and the defects found in the review record |

## Versioning

Every handoff file carries `"schema_version": "1.5"`, fixed by `common.schema.json`. A consumer must reject a version it does not know.

This is the planner's own file-format version. The engineering integration contract - `handoff-manifest.json` and the consumer views a downstream system relies on - is versioned separately in [`integration/`](integration/README.md); the manifest reports this version as `planner_schema_version`.

- Adding an optional property a consumer can ignore does not change the version.
- Adding a required property, removing or renaming one, narrowing an enum or pattern, or changing a meaning is a new version. Change `schemaVersion` in `common.schema.json`, `SCHEMA_VERSION` in `tools/validate_handoff.py`, and the `$id` path segment together, and describe the change here.

Schemas use `additionalProperties: false` throughout, so an unexpected field is an error rather than silently passed through.

## Version history

| Version | Change |
| --- | --- |
| 1.0 | Initial contract |
| 1.1 | Architecture governance. `architecture.json` gains `summary`, `principles` and `coverage`; each ADR gains `active`, `decision_owner` (replacing `deciders`), `approval_evidence`, `decision_questions`, `rationale`, `risks`, `risk_ids`, `constraints`, `related_features`, `principles`, `depends_on`, `conflicts_with` and `notes`, and `consequences` becomes `{positive, negative, other}`. Requirements and features gain `architecture_decisions` (shared `adrLink` definition, also used by tasks, whose `applies_via` may now include `feature:FEAT-###`). `traceability.json` gains `architecture`, the per-ADR reach. New identifier `PRIN-###` (`principleId`) |
| 1.2 | Change-impact analysis. New required file `changes.json` (`changes.schema.json`). The Definition of Ready gains "not under change review", so a task's `readiness_gaps` may name the change that withdraws its readiness. New identifier forms `CHANGE-###`, `PAGE-###`, `API-###`, `INT-###` accepted by `anyId`; `CR-###` is retired |
| 1.3 | Independent specification review. New required file `specification-review.json` (`specification-review.schema.json`); `project.json` gains the required `specification_review` summary (`result`, `review_cycle`, `review_version`). `handoff_status` is `ready` only when that result is PASS or PASS_WITH_WARNINGS for the current version, and the Definition of Ready gains the same condition, so a task's `readiness_gaps` may name a failing or missing review. New identifier `REVIEW-###` (`reviewFindingId`) and value set `reviewResult` |
| 1.4 | Backlog readiness. New required file `backlog-readiness.json` (`backlog-readiness.schema.json`); `project.json` gains `backlog_status`. Task statuses are planning statuses only: `DRAFT`, `NEEDS_DISCOVERY`, `NEEDS_REVIEW`, `BLOCKED`, `READY`, `CANCELLED` (`IN_PROGRESS`, `DONE` and `DEFERRED` are removed). Each task gains `revision`, `objective`, `declared_scope`, `impacts` (data, API, UI, integration), `risk_ids`, `readiness` (the named Definition of Ready checks, failures and recommended status) and `readiness_history`. Features gain `no_tasks_reason`; risks gain `blocks_readiness`; `architecture.json` gains `conflict_reviews`. `executable_now` becomes the first ready work set. While a dependency cycle exists, `sequencing.order` is empty. New value sets `readinessCheck` and `backlogStatus` |
| 1.5 | Engineering integration. Each task gains the required `content_hash` (`sha256:` + 64 hex, new definition `contentHash`): a fingerprint of the task's content and the requirements and ADRs it relies on, basis `task-intent/1`, recomputed by the validator. The handoff gains `handoff-manifest.json`, validated against `integration/handoff-manifest.schema.json` (contract 1.0) rather than a file-format schema, and every task, requirement and ADR is also validated against the contract's consumer views |
