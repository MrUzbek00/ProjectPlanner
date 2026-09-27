# Scope Register

Project: TBD · Version: TBD · Updated: TBD

TEMPLATE — stage 5. Copy to `specification/scope.md`. The scope register makes the release boundary explicit, so that nothing drifts into or out of the project unnoticed.

| Classification | Meaning | What it takes |
| --- | --- | --- |
| IN SCOPE | Delivered in this project | Confirmed requirements, approved at G8 |
| OUT OF SCOPE | Will not be delivered | A rationale and the authority that excluded it |
| FUTURE | Wanted, but not in this project | A rationale; never silently pulled into the current plan |
| PENDING DECISION | Cannot be classified until a question is answered | An open question in `discovery/open-questions.md` that names it |

Scope is recorded in two places that do not overlap. Every requirement (`templates/26`) and every feature (`templates/07`) carries its own *Scope* field. This register holds the boundary statements that are not a single requirement — whole capabilities, channels, user groups, platforms, integrations — and groups the requirements and features they cover under *Related IDs*.

Keep the first column header exactly `Scope ID`; `tools/generate_handoff.py` reads this table into `machine-handoff/requirements.json`.

| Scope ID | Item | Classification | Related IDs | Rationale | Authority |
| --- | --- | --- | --- | --- | --- |

## Rules

- A future idea stays FUTURE until a recorded decision (DEC-###) and change control move it. Enthusiasm in a meeting is not a scope change.
- An open BLOCKER question does not have to stop the whole plan: classify everything it affects as PENDING DECISION and the rest of the plan can pass its gates. What it affects cannot be READY until the question is answered.
- A requirement that is PENDING DECISION, FUTURE or OUT OF SCOPE is not approved into the release, is excluded from coverage, and no in-scope task may depend on its tasks.

## Gate G5 — Solution and scope ready (with the architecture register)

| Criterion | Checked by |
| --- | --- |
| This register exists; every live requirement and every feature has a scope classification | `check_gates.py` |
| Every PENDING DECISION item is named by an open question | `check_gates.py` |
| OUT OF SCOPE and FUTURE items state a rationale | `check_gates.py` (warning) |
