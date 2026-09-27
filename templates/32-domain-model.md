# Domain Model

Project: TBD · Version: TBD · Updated: TBD

TEMPLATE — stage 4. Copy to `specification/domain-model.md`. Identify the important business entities and their relationships before the backlog is decomposed. This is the **business** model: what the organisation keeps track of and the rules around it. It is not a database design — tables, columns, keys and indexes come later, as a proposal, in `templates/25`.

Each entity is a record block that `tools/generate_handoff.py` reads into `machine-handoff/domain.json`. Keep the heading, field names and section labels as shown. Where something does not apply, write `None — reason`; a blank field fails gate G4.

## Entity — repeat

### ENT-000 — Entity name in the confirmed business term

| Field | Value |
| --- | --- |
| Purpose | What the business uses it for |
| Ownership | The module (MOD-###) or role that owns and maintains it |
| Lifecycle states | Comma-separated states in order, for example DRAFT, SUBMITTED, PAID, CANCELLED; `None — reason` if it has no lifecycle |
| Permissions | Who can create, view, change and delete it, and under what condition |
| Business rules | RULE-### that govern it, or None |
| Related requirements | Requirement IDs that create, read or change it |
| Confidence | CONFIRMED / LIKELY / ASSUMPTION / UNKNOWN |

**Key attributes**

- Business attributes the requirements depend on, in business terms. Not a field list for a table.

**Relationships**

- Relationship to ENT-### with its business meaning; cardinality only when confirmed, otherwise `TBD (Q-###)`.

State transitions — who may move the entity from one state to another, under which condition, with which side effects — are defined in the process model (`templates/03`) as STATE-### records. Every state listed here appears there, including rejection and cancellation where they exist.

## Gate G4 — Models ready (with the process model)

| Criterion | Checked by |
| --- | --- |
| At least one entity; each states purpose, key attributes, relationships, lifecycle states, ownership and permissions | `check_gates.py` |
| Entities named by processes, modules and requirements exist | `validate_handoff.py` via `check_gates.py` |
| Entities modelled on LIKELY, ASSUMPTION or UNKNOWN information are visible | `check_gates.py` (warning) |
