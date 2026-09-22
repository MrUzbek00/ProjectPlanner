# Business Process and Access Model

Project: TBD · Revision: TBD · Classification: DRAFT

Populate only confirmed processes and relationships. AS-IS observations and proposed TO-BE behavior must remain distinguishable. Use tracked questions for unknown steps.

## Process inventory

| Process ID | Name | AS-IS / TO-BE | Business objective IDs | Owner / actors | Trigger | Output | Detail reference | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Process record — repeat for each major process

| Field | Definition |
| --- | --- |
| Process ID / name | TBD |
| AS-IS / TO-BE | TBD |
| Purpose / related BIZ and FR IDs | TBD |
| Trigger | TBD |
| Actors / ROLE IDs | TBD |
| Preconditions | TBD |
| Main flow | Ordered steps in the table below |
| Alternative flows | Trigger condition, steps, rejoin point or final outcome |
| Approval steps | Confirmed path or N/A with evidence |
| Rejection flow | Reason/comment, actor, status, edit/resubmit eligibility and output |
| Status transitions | Entity and state IDs; transition table below |
| Notifications | Trigger, recipient, channel and NOTIF IDs |
| Data created or modified | ENT IDs, changed values, ownership and transaction boundary if confirmed |
| Output | Observable successful business result |
| Failure cases | Preconditions/validation/permission/external/concurrent failures as applicable |
| Audit requirements | Events and captured values linked to requirements |
| Source / decision references | TBD |
| Unresolved questions | TBD |

### Main flow

| Step | Actor | User / external action | System behavior | Input | Output / data change | State before → after | Rule / requirement IDs |
| --- | --- | --- | --- | --- | --- | --- | --- |

### Alternatives, rejection and failure

| Path ID | Branch condition / failing step | Actor | Required behavior | Rejoin point or terminal outcome | Data retained / changed / rolled back | Notification | Audit | Evidence / open question |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Roles and permissions

| Role ID / name | Responsibility | Accessible modules | Record / department / organization scope | Create | View | Edit | Delete | Approve / Reject | Export | Administrative permission | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

For each permission use Allowed / Denied / Conditional / TBD. Define every condition. Hiding a button does not define server-side authorization; specify both when the system has UI and backend layers.

### Detailed role-permission matrix

| ROLE ID | MOD / PAGE / entity / action | Create | View | Edit | Delete | Approve | Reject | Export | Admin | Record scope | Conditions / BR IDs | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## State dictionary

| STATE ID | Entity | Status name | Business meaning | Initial? | Terminal? | Permitted editing / ownership rules | Source / decision |
| --- | --- | --- | --- | --- | --- | --- | --- |

## State transition and approval table

| Entity / workflow | Initial status | Actor / permission | Action | Guard / preconditions | Next status | Data effects | Notification recipient / channel | Rejection behavior | Required comment | Required attachment | Audit entry | Failure / concurrent-action behavior | Requirement / rule IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Confirm which transitions are forbidden and the response to an invalid transition. Ask about cancellation, resubmission, delegation or parallel approval only when relevant; do not add them automatically.

## Entity and relationship inventory

| ENT ID / name | Business purpose | Confirmed important fields | Ownership | Lifecycle / states | Source | Unresolved data decisions |
| --- | --- | --- | --- | --- | --- | --- |

| From entity | Relationship | To entity | Cardinality | Optionality | Ownership / delete implications | Evidence / DEC ID |
| --- | --- | --- | --- | --- | --- | --- |

## Diagrams

Create only useful, actual diagrams after confirming the corresponding model. Store Mermaid source with a legend, version and related IDs. Include readable text/table definitions so diagrams do not become the only source of rules.

| Diagram | Applicability / purpose | Required confirmed inputs | File / model references |
| --- | --- | --- | --- |
| Process flow | TBD | Trigger, actors, ordered steps and branches | TBD |
| BPMN-like flow | TBD | Responsibilities and handoffs; label as BPMN-like | TBD |
| Approval workflow | TBD | Guards, decisions, rejection paths and states | TBD |
| State diagram | TBD | Entity-scoped states and allowed transitions | TBD |
| ERD | TBD | Entities, cardinality and optionality | TBD |
| System architecture | TBD | Boundaries, confirmed components and integration direction | TBD |

No illustrative business diagram is included in this blank template to avoid implying unconfirmed behavior.
