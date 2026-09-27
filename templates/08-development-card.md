# TASK-### — <Outcome the task delivers, stated as a result>

TEMPLATE — create executable task cards only after approval of the specification they implement. Save each card as `backlog/tasks/TASK-###.md`, named after its ID, with this heading as its only `TASK-###` heading. Populate every requested field. Do not mark a card complete merely because its document is written.

Phrase the title and objective as the outcome the task delivers — "Allow administrators to suspend a user account", not "Create endpoint", "Add model", "Update serializer" or "Fix auth". At planning level a task is an independently actionable, verifiable piece of the product; decomposition into code-level steps belongs to engineering planning, downstream. Do not combine unrelated outcomes into one giant task, and do not split one cohesive outcome into microtasks: gate GB flags both, along with possible duplicates and contradictory tasks, for review.

**A generated task is not a ready task.** READY is earned: the card passes every Definition of Ready check at the end of this template, evaluated by the tools, never declared.

The card is the canonical record of the task. `tools/generate_handoff.py` reads the metadata table and the Objective, Description, impact, Acceptance Criteria, Constraints, Testing Checklist and Readiness history sections into `machine-handoff/tasks/TASK-###.json`, and every other section into that file's `details`. Keep the field names and section headings as shown. Include an impact section only where the task touches that area: do not force meaningless fields.

## Card metadata

| Field | Value |
| --- | --- |
| Epic | EPIC-### and title |
| Feature | FEAT-### and title |
| Parent task | Parent TASK-### for a subtask (TASK-###-S##), otherwise None |
| Type | backend / frontend / fullstack / database / integration / infrastructure / security / testing / documentation / design / other |
| Related Requirement IDs | Approved BR / FR / NFR / TR IDs; RULE IDs where applicable |
| Approved specification version | Exact baseline / manifest and approval evidence |
| Priority | Critical / High / Medium / Low / Unspecified |
| Priority basis | Confirmed — DEC-### / Proposed — rationale awaiting decision |
| Estimated Complexity | XS / S / M / L / XL, with drivers and unknowns |
| Phase | PHASE-## from the roadmap, or None |
| Blocked By | Required predecessor TASK-### IDs; `None` only after dependency review. Blank or TBD means dependencies are unknown |
| External dependencies | DEP-### from `discovery/dependencies.md` the task relies on, or None |
| Architecture decisions | ADR-### IDs this task must follow, or None. ADRs linked through its requirements, its modules or its feature are added automatically. Only Accepted ADRs let a task be READY; naming a rejected, superseded or deprecated ADR fails gate G9 |
| Related modules | MOD-### IDs, or None |
| Required test levels | unit / integration / contract / e2e / security / performance / accessibility / migration / manual / uat — comma-separated |
| Scope | Only when the task narrows its feature's scope: Future / Out of scope / Pending decision. Omit it otherwise — the feature's scope applies. Only IN SCOPE work can be READY |
| Risks | RISK-### the task is exposed to, or None. A risk blocks the task only when the risk register marks it *Blocks readiness* |
| Status | DRAFT / NEEDS_DISCOVERY / NEEDS_REVIEW / BLOCKED / READY / CANCELLED — see *Task status* below |
| Revision | 1, incremented whenever the task's definition changes materially after it was validated. A changed task is a new revision, not the same unchanged task; gate GB compares it with the change-control baseline |
| Readiness blockers | Unresolved decisions, external inputs or other blockers with references; `None` after review. Blank or TBD counts as a blocker |

The tasks this card blocks are derived from the other cards' *Blocked By* fields; they are not written here, so the two directions can never disagree.

## Objective

State one observable outcome, and why it exists: the approved requirement or business objective it serves. (A section headed *Goal* is read the same way.)

## Description

Define the bounded change, current/expected behavior where relevant, included work and explicit exclusions. A developer should not need to reinterpret stakeholder intent. Reference the baseline; do not introduce new behavior through this card.

## User Story

As a [confirmed role], I need [specific capability], so that [business result].

For technical enablers, use a precise technical outcome and its approved NFR/TR/business justification instead of inventing a user role.

## Dependencies

| Prerequisite card / document / external condition | Why needed | Required completion evidence | Current availability / state | Owner if known |
| --- | --- | --- | --- | --- |

Hierarchy membership is not an execution dependency. Keep internal prerequisite IDs consistent with Blocked By; the reverse links are derived.

## Inputs

| Input | Source / baseline path | Required shape / content | Availability | Related requirement |
| --- | --- | --- | --- | --- |

Include confirmed source data, approved designs/contracts, prerequisite outputs and test fixtures as applicable. Do not place passwords or production credentials in cards.

## Implementation Requirements

| Step / outcome | Required behavior | Input / output | Approved requirement / design reference | Failure handling |
| --- | --- | --- | --- | --- |

Specify the contracts and constraints needed for implementation. Leave routine internal coding choices to the implementation team when they do not affect requirements; unresolved product/interface/data decisions remain blockers.

## Constraints

| Kind | Constraint | Reference |
| --- | --- | --- |
| Architecture | Binding architectural constraint, or `N/A — reason` | ADR / TR / DEC ID |
| Security | Binding security requirement, or `N/A — reason` | NFR / RULE / DEC ID |

Kind is one of Architecture, Security, Performance, Data, Compliance or Other. Each constraint states an approved requirement or decision in implementable terms and cites it; nothing here is new scope. Architecture and Security each need at least one row — a constraint, or `N/A — reason` when the task genuinely has none. A READY task cannot leave either undocumented.

## Business Rules

| RULE ID | Applicable rule / exact condition | Formula / boundary / exception | Approved reference |
| --- | --- | --- | --- |

## UI Impact

Only when the task changes what users see. Affected screens (PAGE IDs), new or modified screens, and the user states the task must handle: normal, empty, error and permission-denied states. Link the approved page records; no pixel-level instructions unless the UI specification already defines them. State `None — reason` if a UI-typed task has no UI change.

## Backend Requirements

Define processing, authorization, data scope, state transitions, persistence/transaction expectations, calculations, audit, notifications and failure/retry/concurrency behavior as applicable. Each behavior needs an approved source. Use reasoned N/A for a card with no backend work.

## Data Impact

Only when the task affects persistent data. Affected entities (ENT-###); create, update and delete behaviour; ownership; lifecycle and state changes; whether a migration is expected; retention impact. No database implementation detail at planning stage. A new unapproved field or a destructive migration is a change or a question, not an assumption.

## API Impact

Only when the task affects an API contract. State the change — NONE, CREATE, MODIFY or REMOVE — and the expected contract-level behaviour: API IDs, authentication and authorisation, request and response content, validation and error contracts, pagination, idempotency and versioning where they apply. No code-level handler files.

## Integration Impact

Only when the task touches an external system (INT-###, IR-###, DEP-###). Provider or system, purpose, expected request and response, authentication, failure behaviour, timeout and retry expectations, fallback. Where critical integration behaviour is unknown, write `TBD (Q-###)`: the task cannot be READY and is BLOCKED until it is known.

## Permissions

| Role / actor | Action | Data / record scope | Allowed / denied / conditional | Enforcement and expected denied response | Requirement IDs |
| --- | --- | --- | --- | --- | --- |

## Validation Rules

| Input / condition | Rule / boundary | Validation point | Error response | Data/state preservation | RULE / FR IDs |
| --- | --- | --- | --- | --- | --- |

## Edge Cases

| Condition | Expected behavior | Data / state impact | Recovery | Related AC / TEST IDs |
| --- | --- | --- | --- | --- |

Assess relevant empty data, boundary values, unauthorized actions, duplicate requests, concurrent changes, invalid transitions, missing/deleted references, failed uploads and unavailable integrations. Record applicability; do not invent flows to fill the table.

## Acceptance Criteria

| AC ID | Given | When | Then / And — measurable result | Requirement IDs | TEST IDs |
| --- | --- | --- | --- | --- | --- |

Include applicable success, denied permission, validation failure, negative paths and required side effects. Every criterion needs a verifiable outcome.

## Testing Checklist

| TEST ID | Type | Fixture / preconditions | Expected evidence | Required for this card? / reason | Execution status / evidence |
| --- | --- | --- | --- | --- | --- |

Review applicable functional, permission, validation, workflow, integration, export, negative, acceptance and NFR tests. Verification states what evidence will prove completion — unit, integration, end-to-end, security, manual acceptance, API contract validation, UI acceptance, data migration validation — not the commands that run it. Every TEST ID is defined in `quality/acceptance-tests.md`. *Required test levels* in the metadata states the verification method; this table names the concrete tests. Initially execution status is NOT RUN; planning does not claim passing implementation tests.

## Definition of Done

- [ ] Approved behavior and applicable contracts are implemented; no unapproved scope was added.
- [ ] All card acceptance criteria pass with linked evidence.
- [ ] Required permission, validation, negative-path and other applicable tests pass.
- [ ] Applicable data changes, migrations and side effects are verified.
- [ ] Applicable audit, notifications and failure handling match the approved specification.
- [ ] Changed user/deployment/API documentation is updated where required.
- [ ] Requirement, test, dependency and card links remain consistent.
- [ ] Required project review and quality checks are complete with no unresolved blocker.

Tailor project-specific evidence and review requirements from the approved specification. This checklist is a completion contract, not evidence that work is already done.

## Task status

Planning statuses only. Execution — coding, testing, pull requests, merging, deployment, done — belongs to downstream engineering, and the tools reject those statuses on a card.

| Status | Meaning |
| --- | --- |
| DRAFT | Being specified; not yet validated |
| NEEDS_DISCOVERY | An open question must be answered first |
| NEEDS_REVIEW | Its foundation changed, a serious review finding or architecture conflict touches it, or its security behaviour is undefined: revalidate before READY |
| BLOCKED | A dependency, external input, blocking risk or unknown integration behaviour prevents it |
| READY | Passes every Definition of Ready check |
| CANCELLED | Dropped by a recorded decision; kept for history |

## Definition of Ready

A card may be `READY` only when every check below passes. `tools/generate_handoff.py` evaluates the checks from the records and stores the result in the task's `readiness`: the result, each named check, the failures, and the status the failures point to. The handoff is rejected if a READY card fails a check. A task that loses readiness — for example when a change marks it NEEDS_REVIEW — is set back to the status its failures point to, with a readiness history entry.

| Check | Passes when |
| --- | --- |
| `specification_ready` | The specification is approved, and its independent review passes for the current version |
| `task_id_valid` | The ID is TASK-### or TASK-###-S##; a subtask names its existing parent |
| `title_clear` | The title states an outcome (no TBD) |
| `objective_clear` | *Objective* and *Description* are stated, without TBD |
| `source_requirement_valid` | At least one source requirement; each exists, is Approved and IN SCOPE |
| `feature_valid` | The parent feature exists, is not cancelled, and belongs to the task's epic |
| `scope_valid` | The task and its feature are IN SCOPE |
| `acceptance_criteria_valid` | Acceptance criteria exist, without TBD |
| `acceptance_criteria_testable` | Every criterion is observable ("an expired reset token is rejected", never "should work correctly" or "user-friendly"), and every AC-### belongs to one of the task's source requirements |
| `dependencies_valid` | *Blocked By* is reviewed; every predecessor exists, is not the task itself, not cancelled, in scope, not in a cycle, and READY |
| `external_dependencies_available` | Every external dependency named is AVAILABLE |
| `architecture_valid` | Architecture constraints are documented; every applicable ADR is Accepted |
| `architecture_conflicts_clear` | No ARCHITECTURE CONFLICT on the task or its feature is open in the architecture review, and no rejected option of an accepted ADR is named without a resolved or withdrawn conflict finding |
| `security_valid` | Security constraints are stated. `N/A — reason` is accepted only when the task involves no sensitive area — authentication, authorisation, payments, personal data, secrets, file uploads, external APIs, administrative actions, account recovery, audit |
| `data_impact_known`, `api_impact_known`, `ui_impact_known`, `integration_impact_known` | Where the task touches that area (its type, its requirements, or the IDs it names), the impact is stated without TBD; data impact names its entities, API impact its change, integration impact its failure behaviour |
| `verification_defined` | *Required test levels* are stated and every named test exists |
| `open_questions_clear` | *Readiness blockers* is `None` and no open BLOCKER question names the task or its requirements |
| `not_stale` | No approved change leaves it NEEDS_REVIEW, STALE or INVALID, and nothing it rests on changed without a change record |
| `review_findings_clear` | No unresolved CRITICAL or MAJOR specification review finding names the task, its feature, epic or requirements. An accepted risk does not block; it stays listed in the task's readiness |
| `blocking_risks_clear` | No risk marked *Blocks readiness* is live and names the task, its feature or requirements |

READY means fully defined, not that it can start today. `backlog/readiness-report.md` groups READY tasks into work sets: WS-01 can start now, and each later set can start once the earlier sets are done.

## Readiness history

Every status transition, oldest first. The last row's *To* is the card's status, and a READY card records the transition that validated it. Losing READY records the reason and the change behind it. The history is planning state, not content: adding a row is not a change to the task.

| Date | From | To | Reason | Change ID |
| --- | --- | --- | --- | --- |
| YYYY-MM-DD | — | DRAFT | Card written from FEAT-### | |

Reviewer / date / remaining blockers: TBD.
