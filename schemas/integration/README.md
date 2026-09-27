# ProjectPlanner → SoftwareFactory Integration Contract

This folder is the one canonical source of the file contract between
ProjectPlanner and SoftwareFactory. ProjectPlanner hosts it because it produces
the handoff and will later read the factory's status files back. SoftwareFactory
vendors an identical copy (`my-software-factory/schemas/integration/`) and keeps
it in sync with its `tools/contract-sync/`.

```text
ProjectPlanner                                   SoftwareFactory
  tools/generate_handoff.py
        │
        ▼
  machine-handoff/ ─── versioned JSON contract ──► ingest-handoff (validate, accept READY tasks)
    handoff-manifest.json   (entry point)             │
    tasks/TASK-###.json                               ▼
    requirements.json, architecture.json, …        repository inspection → implementation plan
                                                      │
  (later: read as external status) ◄── software-factory-output/tasks/TASK-###-status.json
```

There is no API, queue, or agent-to-agent conversation. The first integration is
deliberately a directory of files: deterministic, inspectable, and testable.

## Ownership

| ProjectPlanner owns — what must be achieved | SoftwareFactory owns — how this repository achieves it |
| --- | --- |
| requirements, scope, specification | repository inspection |
| architecture decisions | implementation strategy, code-level planning |
| features, tasks, acceptance criteria | branches, worktrees, code changes |
| dependencies, readiness validation | tests, validation, security checks |
| planning traceability | commits, pull requests |

A task never carries file, module, table or endpoint choices unless they are
approved constraints (an accepted ADR or a recorded task constraint).

## Schemas

| Schema | Describes | Written by | Read by |
| --- | --- | --- | --- |
| `handoff-manifest.schema.json` | `machine-handoff/handoff-manifest.json`: contract version, `handoff_status`, validation flags, every file with its SHA-256, `ready_tasks`, each task's revision, status and content hash | ProjectPlanner | SoftwareFactory, first |
| `task-handoff.schema.json` | the fields of `tasks/TASK-###.json` a consumer relies on | ProjectPlanner | SoftwareFactory |
| `requirement-reference.schema.json` | one entry of `requirements.json` a task names | ProjectPlanner | SoftwareFactory |
| `architecture-reference.schema.json` | one ADR of `architecture.json` a task relies on | ProjectPlanner | SoftwareFactory |
| `factory-status.schema.json` | `software-factory-output/tasks/TASK-###-status.json`: engineering status, never planning authority | SoftwareFactory | ProjectPlanner, later |
| `factory-intake-report.schema.json` | `software-factory-output/intake-report.json`: what one ingest accepted and rejected, and who must fix each rejection | SoftwareFactory | people, ProjectPlanner later |

The three reference schemas are *consumer views*. They require exactly the
fields the consumer uses and tolerate the rest, so the planner can add an
optional field without breaking the contract. The planner's full shapes remain
governed by `schemas/*.schema.json`, and `tools/validate_handoff.py` validates
every generated task, requirement and ADR against these views too — a planner
change that would break the consumer fails in the planner first.

Every schema here is self-contained (local `$defs` only) and uses only the
keywords SoftwareFactory's dependency-free validator implements, which its
tests enforce.

## Versioning

- The manifest's `schema_version` is the **contract version**, currently `1.0`.
  It is independent of the planner's file-format version, reported as
  `planner_schema_version`.
- A consumer declares the contract versions it supports and rejects any other.
  It never interprets an unknown version on a best guess.
- Adding an optional field that a consumer can ignore does not change the
  version. Removing, renaming or retyping a field a view names, narrowing an
  enum or a pattern, or changing a meaning is a new contract version: change the
  schemas' `$id` segment, `CONTRACT_VERSION` in `tools/handoff_contract.py`,
  and the supported versions on the consumer side together.
- `contract.json` locks the SHA-256 of every schema here. After a deliberate
  change, run `python tools/handoff_contract.py --write-lock`; the test suite
  fails while the lock is stale (`--check-lock`).

## Task identity

Every task carries `revision` — incremented on the card when the definition
changes materially after validation — and `content_hash`, a SHA-256 over the
task's content and the requirements and ADRs it relies on (basis
`task-intent/1`, described in every manifest's `task_content_hash`). Timestamps,
status and readiness bookkeeping are excluded, so an unchanged task keeps its
hash across regenerations, and a changed requirement statement changes the hash
of every task built on it. A consumer stores both at intake and compares them
before each engineering step.

## Errors and owners

Every rejection names the side that must act: `PROJECT_PLANNER` for a planning
defect (fix the Markdown records and regenerate — never the JSON),
`SOFTWARE_FACTORY` for an engineering-side problem, `HUMAN_DECISION` for a
decision only an authorised person can make.
