# Requirement Detail — FR-<MODULE>-###

Copy one record per functional requirement, or embed complete records in specification section 7. Replace the template ID with a stable project ID.

| Field | Requirement definition |
| --- | --- |
| Requirement ID | FR-<MODULE>-### |
| Module | MOD ID and confirmed name |
| Requirement | One precise capability / observable behavior |
| Actor | ROLE ID or confirmed system/external actor |
| Precondition | Required record state, data, access and dependencies |
| Trigger | Specific user action, event or schedule |
| System Behaviour | Ordered processing and observable responses; detail below |
| Business Rules | BR IDs and applicable conditions |
| Validation Rules | Validation table below |
| Permissions | Allowed/denied actors, record scope, conditions and enforcement |
| Success Result | Observable output, resulting state and side effects |
| Failure Result | Errors, data/state preservation and recovery behavior |
| Related Requirements | BIZ, FR, NFR, TR, BR and dependency IDs as applicable |
| Classification | Confirmed / Assumption / Recommendation; unresolved decisions are Q IDs |
| Source evidence | SRC IDs and exact locations; DEC IDs when applicable |
| Approved specification version | None until actual approval |
| Related process / page / entity / API IDs | TBD or reasoned N/A |
| Acceptance criteria / test IDs | AC and AT references |
| Open questions | Q IDs or None after review |

## System behaviour

| Step | Input / event | Processing / rule | Output / user-visible response | Data or state effect | Failure branch |
| --- | --- | --- | --- | --- | --- |

## Validation rules

| Field / input / condition | Type / format / allowed range | Required / default | Validation timing and enforcement | Error message / code | Resulting state / retained input | BR / source |
| --- | --- | --- | --- | --- | --- | --- |

## Failure and edge cases

| Condition | Expected behavior | User / caller response | Data rollback / preservation | Retry or recovery | Notification / audit | Evidence |
| --- | --- | --- | --- | --- | --- | --- |

Assess applicable empty/missing data, unauthorized access, invalid state, duplicate requests, concurrent edits, external unavailability and boundary calculations. These are review prompts; they do not establish unconfirmed behavior.

## Acceptance criteria

| AC ID | Given | When | Then / And | Related AT IDs |
| --- | --- | --- | --- | --- |

## Traceability

- Business requirement IDs: TBD
- Functional requirement ID: this record
- Module / page: TBD or page N/A with confirmed reason
- Development card IDs: Pending — specification not approved
- Acceptance criterion / test IDs: TBD
