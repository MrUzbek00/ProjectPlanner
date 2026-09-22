# Epic and Feature Hierarchy

TEMPLATE — populate after specification approval. Epics and features group work; executable tasks use the full development-card template.

Approved specification version / approval evidence: TBD

## Epic — repeat

| Field | Definition |
| --- | --- |
| Card ID | EPIC-## |
| Title | Confirmed business capability / outcome |
| Goal | Business result and measure |
| Description / scope | Included capability and explicit exclusions |
| Related Requirement IDs | BIZ and applicable FR / NFR / TR IDs |
| User Story | As [confirmed role], I need [capability], so that [business result]; use a technical outcome for an approved technical epic |
| Features | FEAT IDs |
| Dependencies | Other required outcomes / external inputs; distinguish hierarchy from execution edges |
| Acceptance Criteria | Measurable outcome and AC / AT links |
| Priority | Confirmed value or proposed value with rationale awaiting decision |
| Estimated Complexity | Aggregate indication only; avoid double-counting child estimates |
| Status | DRAFT / BLOCKED / READY / IN_PROGRESS / DONE / DEFERRED with basis |
| Completion rule | Required child outcomes plus epic acceptance evidence |

## Feature — repeat under its epic

| Field | Definition |
| --- | --- |
| Card ID | FEAT-##-## |
| Epic | EPIC ID |
| Title | Coherent functional capability |
| Goal | Observable user/system outcome |
| Description / scope | Included behaviors and boundaries |
| Related Requirement IDs | Approved requirement IDs |
| User Story | Confirmed actor, need and value, or approved technical outcome |
| Tasks | Actual executable task IDs |
| Dependencies | Required capabilities and external conditions |
| Acceptance Criteria | AC / AT IDs and measurable feature outcome |
| Priority | Confirmed or explicitly proposed |
| Estimated Complexity | Aggregate indication only |
| Status | Status with basis; do not imply implementation progress during planning |
| Completion rule | Required tasks and feature-level validation |

## Hierarchy index

| Epic ID | Feature ID | Task ID | Optional subtask ID | Related requirements | Executable leaf? | Detail location |
| --- | --- | --- | --- | --- | --- | --- |

If a task contains subtasks, explicitly identify the executable leaves and task-level integration acceptance. Do not count the parent and its children as independent delivery of the same requirement. Every leaf uses the full task template; non-applicable fields have a reasoned N/A.
