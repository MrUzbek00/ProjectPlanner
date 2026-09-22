# <AREA>-### — <Specific implementation outcome>

TEMPLATE — create executable cards only after approval of the specification they implement. Populate every requested field. Do not mark a card complete merely because its document is written.

## Card metadata

| Field | Value |
| --- | --- |
| Card ID | <AREA>-### |
| Epic | EPIC-## and title |
| Feature | FEAT-##-## and title |
| Parent task / optional subtask IDs | Actual relationship or N/A |
| Title | Specific, bounded outcome |
| Related Requirement IDs | Approved BIZ / FR / NFR / TR IDs; BR IDs where applicable |
| Approved specification version | Exact baseline / manifest and approval evidence |
| Priority | Confirmed priority or proposed value + rationale / Q ID |
| Estimated Complexity | XS / S / M / L / XL, with drivers and unknowns |
| Blocking Cards | Successor IDs that this card blocks; derived from their Blocked By lists |
| Blocked By | Required predecessor task IDs; None only after dependency review |
| Status | DRAFT / BLOCKED / READY / IN_PROGRESS / DONE / DEFERRED |
| Definition completeness | COMPLETE / INCOMPLETE |
| Readiness blockers | Missing decision, external input or unfinished predecessor; include references |

## Goal

State one observable outcome and why it supports the approved business objective.

## Description

Define the bounded change, current/expected behavior where relevant, included work and explicit exclusions. A developer should not need to reinterpret stakeholder intent. Reference the baseline; do not introduce new behavior through this card.

## User Story

As a [confirmed role], I need [specific capability], so that [business result].

For technical enablers, use a precise technical outcome and its approved NFR/TR/business justification instead of inventing a user role.

## Dependencies

| Prerequisite card / document / external condition | Why needed | Required completion evidence | Current availability / state | Owner if known |
| --- | --- | --- | --- | --- |

Hierarchy membership is not an execution dependency. Keep internal prerequisite IDs consistent with Blocked By and derive reverse Blocking Cards links.

## Inputs

| Input | Source / baseline path | Required shape / content | Availability | Related requirement |
| --- | --- | --- | --- | --- |

Include confirmed source data, approved designs/contracts, prerequisite outputs and test fixtures as applicable. Do not place passwords or production credentials in cards.

## Implementation Requirements

| Step / outcome | Required behavior | Input / output | Approved requirement / design reference | Failure handling |
| --- | --- | --- | --- | --- |

Specify the contracts and constraints needed for implementation. Leave routine internal coding choices to the implementation team when they do not affect requirements; unresolved product/interface/data decisions remain blockers.

## Business Rules

| BR ID | Applicable rule / exact condition | Formula / boundary / exception | Approved reference |
| --- | --- | --- | --- |

## UI Requirements

Define PAGE IDs, navigation, visible data, controls, forms, table columns, filters/search/sort/pagination, permitted actions, validation, loading/empty/error/success states, responsive/localization requirements and exports as applicable. Link complete approved page records and summarize the exact portion this card implements.

## Backend Requirements

Define processing, authorization, data scope, state transitions, persistence/transaction expectations, calculations, audit, notifications and failure/retry/concurrency behavior as applicable. Each behavior needs an approved source. Use reasoned N/A for a card with no backend work.

## Database Requirements

Define affected approved entities/fields/relationships, constraints, migration/backfill needs, ownership and deletion behavior. Link the approved data model. A new unapproved field or destructive migration requirement is a change/question, not an assumption.

## API Requirements

Specify contract IDs and the relevant method/path or event, authentication/authorization, request/response fields, validation, error contracts and pagination/idempotency/version behavior where applicable. Link the approved API definition. Do not assume an integration endpoint exists.

## Permissions

| Role / actor | Action | Data / record scope | Allowed / denied / conditional | Enforcement and expected denied response | Requirement IDs |
| --- | --- | --- | --- | --- | --- |

## Validation Rules

| Input / condition | Rule / boundary | Validation point | Error response | Data/state preservation | BR / FR IDs |
| --- | --- | --- | --- | --- | --- |

## Edge Cases

| Condition | Expected behavior | Data / state impact | Recovery | Related AC / AT IDs |
| --- | --- | --- | --- | --- |

Assess relevant empty data, boundary values, unauthorized actions, duplicate requests, concurrent changes, invalid transitions, missing/deleted references, failed uploads and unavailable integrations. Record applicability; do not invent flows to fill the table.

## Acceptance Criteria

| AC ID | Given | When | Then / And — measurable result | Requirement IDs | AT IDs |
| --- | --- | --- | --- | --- | --- |

Include applicable success, denied permission, validation failure, negative paths and required side effects. Every criterion needs a verifiable outcome.

## Testing Checklist

| Test / AT ID | Type | Fixture / preconditions | Expected evidence | Required for this card? / reason | Execution status / evidence |
| --- | --- | --- | --- | --- | --- |

Review applicable functional, permission, validation, workflow, integration, export, negative, acceptance and NFR tests. Initially execution status is NOT RUN; planning does not claim passing implementation tests.

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

## Readiness review

| Check | Result / evidence |
| --- | --- |
| Approved scope and baseline references valid | TBD |
| All sections specified or reasoned N/A | TBD |
| No unresolved requirement/design decision affects implementation | TBD |
| Acceptance criteria and test definitions complete | TBD |
| Prerequisites known and dependency graph valid | TBD |
| All execution prerequisites satisfied for READY | TBD |

Reviewer / date / remaining blockers: TBD. If definition-complete but waiting on another card, use COMPLETE + BLOCKED and identify that predecessor.
