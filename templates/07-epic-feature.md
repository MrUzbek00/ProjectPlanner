# Epic and Feature Hierarchy

TEMPLATE — stage 9. Populate only after the specification has passed its independent review (gate GR) and approval (gate G8), in `backlog/backlog.md`; a feature built from raw stakeholder notes skips the analysis the backlog depends on. Epics and features group work; executable tasks use the full task card template (`templates/08`) in `backlog/tasks/TASK-###.md`.

Approved specification version / approval evidence: TBD

**Levels.** One hierarchy, used consistently:

| Level | Is | Is not |
| --- | --- | --- |
| EPIC | A large business capability or project area | A deliverable in itself |
| FEATURE | A user- or business-visible capability | A technical layer |
| TASK | An independently actionable, verifiable unit of work that delivers an outcome (`templates/08`) | A coding instruction ("create model", "add serializer") |
| SUBTASK (`TASK-###-S##`) | An optional internal breakdown of a task that genuinely needs one | A way to create more cards |

Each epic and feature is a record block: a heading that starts with its ID, then a `| Field | Value |` table. `tools/generate_handoff.py` reads them into `machine-handoff/backlog.json`. Membership is recorded in one direction only — a feature names its epic, a task names its feature — and the reverse lists (an epic's features, a feature's tasks) are derived, so they cannot disagree.

## Epic — repeat

### EPIC-000 — Confirmed business capability / outcome

| Field | Value |
| --- | --- |
| Goal | Business result and measure |
| Description / scope | Included capability and explicit exclusions |
| Related Requirement IDs | BR and applicable FR / NFR / TR IDs |
| User Story | As [confirmed role], I need [capability], so that [business result]; use a technical outcome for an approved technical epic |
| Dependencies | Other required outcomes / external inputs; distinguish hierarchy from execution edges |
| Acceptance Criteria | Measurable outcome and AC / TEST links |
| Priority | Critical / High / Medium / Low / Unspecified |
| Priority basis | Confirmed — DEC-### / Proposed — rationale |
| Estimated Complexity | Aggregate indication only; avoid double-counting child estimates |
| Status | DRAFT / NEEDS_DISCOVERY / NEEDS_REVIEW / BLOCKED / READY / CANCELLED — planning statuses only; execution states belong to engineering |
| Completion rule | Required child outcomes plus epic acceptance evidence |

## Feature — repeat under its epic

#### FEAT-000 — Coherent functional capability

| Field | Value |
| --- | --- |
| Epic | EPIC-### |
| Scope | In scope / Out of scope / Future / Pending decision — consistent with its requirements |
| Goal | Observable user/system outcome |
| Description / scope | Included behaviors and boundaries |
| Related Requirement IDs | Approved requirement IDs — every feature links to at least one |
| Modules | MOD-### the feature delivers into |
| Architecture decisions | Accepted ADR-### the feature relies on, or None. ADRs reached through its requirements or modules are added automatically; naming a rejected, superseded or deprecated ADR fails gate G9 |
| Depends on | FEAT-### that must be delivered first, or None |
| External dependencies | DEP-### the feature relies on, or None |
| User Story | Confirmed actor, need and value, or approved technical outcome |
| Dependencies | Required capabilities and external conditions |
| Acceptance Criteria | AC / TEST IDs and measurable feature outcome |
| Priority | Critical / High / Medium / Low / Unspecified |
| Priority basis | Confirmed — DEC-### / Proposed — rationale |
| Estimated Complexity | Aggregate indication only |
| Status | DRAFT / NEEDS_DISCOVERY / NEEDS_REVIEW / BLOCKED / READY / CANCELLED, with basis; do not imply implementation progress during planning |
| No tasks reason | Only for an in-scope feature with no task: already implemented, documentation only, external vendor responsibility, or no implementation required — with its evidence. Otherwise leave the row out; gate G9 fails an in-scope feature with neither tasks nor a reason |
| Completion rule | Required tasks and feature-level validation |

## Hierarchy index

For reading only; the generated `traceability/requirement-map.md` shows the same hierarchy from the records.

| Epic ID | Feature ID | Task ID | Optional subtask ID | Related requirements | Executable leaf? | Detail location |
| --- | --- | --- | --- | --- | --- | --- |

If a task contains subtasks (`TASK-###-S##`), explicitly identify the executable leaves and task-level integration acceptance. Do not count the parent and its children as independent delivery of the same requirement. Every leaf uses the full task template; non-applicable fields have a reasoned N/A.

## Architecture constraints

A feature respects every accepted ADR that applies to it — the ones it names and the ones reached through its requirements and modules, listed per feature in `machine-handoff/backlog.json` and in `traceability/requirement-map.md`. A feature that needs something an accepted ADR rules out (a rejected option, a second delivery path, another API style) is an ARCHITECTURE CONFLICT: record it in `reviews/architecture-review.md` and resolve it by changing the feature, adding an ADR or superseding the ADR (`templates/39`). A feature that needs an architecture choice nobody has made gets a PROPOSED ADR; its tasks stay out of READY until the decision owner accepts it.
