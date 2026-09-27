# Business Process and Access Model

Project: TBD · Revision: TBD · Classification: DRAFT

Populate only confirmed processes and relationships. AS-IS observations and proposed TO-BE behavior must remain distinguishable. Use tracked questions for unknown steps. Business entities, their attributes and lifecycles are defined in `specification/domain-model.md` (`templates/32`); this file defines the processes, permissions and state transitions that act on them.

## Process inventory

| Process ID | Name | AS-IS / TO-BE | Business objective IDs | Owner / actors | Trigger | Output | Detail reference | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Process record — repeat for each major process

TEMPLATE — stage 4. Copy this file to `specification/process-model.md`. Model a workflow before designing the solution for it: who does what, when, under which conditions, what can go differently and what can go wrong. Model AS-IS and TO-BE as separate records where the process changes, and state the differences explicitly. Diagrams (`templates/24`) are generated only after the logical workflow here is understood.

Each process is a record block that `tools/generate_handoff.py` reads into `machine-handoff/domain.json` and `tools/check_gates.py` checks for gate G4. Keep the field names and section labels. Every field needs content; where nothing applies write `None — reason`.

### PROC-000 — Process name

| Field | Value |
| --- | --- |
| Perspective | AS-IS / TO-BE |
| Replaces | TO-BE only: the AS-IS PROC-### this process replaces |
| Actor | ROLE IDs or confirmed actors, including systems |
| Trigger | The event, action or schedule that starts it |
| Preconditions | What must be true before it starts |
| Result | The observable business outcome when it succeeds |
| Business rules | RULE-### applied, or `None — reason` |
| Data involved | ENT-### read or changed |
| Related requirements | BR / FR / NFR / DR / IR / SR / UXR IDs the process realises |
| Confidence | CONFIRMED / LIKELY / ASSUMPTION / UNKNOWN |

**Main flow**

1. Ordered steps: actor, action, system response, data or state change, requirement IDs.

**Alternative flow**

- Condition → steps → where it rejoins or how it ends. `None — reason` when there is none.

**Exceptions**

- Failing condition → required behaviour → data kept or rolled back → notification. Include permission, validation, external-system and concurrency failures where they apply.

**Differences from AS-IS**

- TO-BE only: each difference from the process it replaces — removed steps, new steps, changed actors, changed rules.

Approval, rejection, notification and audit behaviour are part of the main, alternative and exception flows where the process has them; state transitions are recorded below.

### Main flow detail — optional, for complex processes

| Step | Actor | User / external action | System behavior | Input | Output / data change | State before → after | Rule / requirement IDs |
| --- | --- | --- | --- | --- | --- | --- | --- |

## Roles and permissions

| Role ID / name | Responsibility | Accessible modules | Record / department / organization scope | Create | View | Edit | Delete | Approve / Reject | Export | Administrative permission | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

For each permission use Allowed / Denied / Conditional / TBD. Define every condition. Hiding a button does not define server-side authorization; specify both when the system has UI and backend layers.

### Detailed role-permission matrix

| ROLE ID | MOD / PAGE / entity / action | Create | View | Edit | Delete | Approve | Reject | Export | Admin | Record scope | Conditions / RULE IDs | Evidence |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## State dictionary

| STATE ID | Entity | Status name | Business meaning | Initial? | Terminal? | Permitted editing / ownership rules | Source / decision |
| --- | --- | --- | --- | --- | --- | --- | --- |

## State transition and approval table

| Entity / workflow | Initial status | Actor / permission | Action | Guard / preconditions | Next status | Data effects | Notification recipient / channel | Rejection behavior | Required comment | Required attachment | Audit entry | Failure / concurrent-action behavior | Requirement / rule IDs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Confirm which transitions are forbidden and the response to an invalid transition. Ask about cancellation, resubmission, delegation or parallel approval only when relevant; do not add them automatically.

## Entities

Entities, their attributes, relationships, lifecycle states, ownership and permissions are defined once, in `specification/domain-model.md` (`templates/32`). Refer to them here by ENT-### and STATE-###; do not keep a second entity inventory.

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
