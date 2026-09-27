# Solution Structure and Module Register

Project: TBD · Specification version: TBD · Updated: TBD

TEMPLATE — stage 5, after the processes and the domain model are understood (gate G4). Copy to `specification/solution-structure.md`. It defines the **logical** solution: the modules the requirements belong to, the areas users and administrators work in, the integrations and external services, the security boundaries and who owns which data. It makes no technology choice: binding architecture choices are Architecture Decision Records, made in stage 6 (`templates/27`, `28`).

`tools/generate_handoff.py` reads the module register into `machine-handoff/architecture.json`. Requirements, features, tasks and ADRs refer to modules by `MOD-###`; that is how the plan knows which decisions apply to which work.

## System context

Confirmed boundaries, external systems and data flows, and who uses what. Link the generated diagrams in `diagrams/exported/`. Unknown elements are `TBD (Q-###)`.

## Module register

Keep the first column header exactly `MOD ID`. Every in-scope FR, NFR, DR, IR, SR, UXR and TR maps to at least one module through its *Related modules* field — gate G5 fails otherwise. The mapping is written on the requirement, not repeated here.

| MOD ID | Module name | Type | Parent module | Purpose | Security boundary | Data ownership |
| --- | --- | --- | --- | --- | --- | --- |

| Type | Use for |
| --- | --- |
| User-facing | Areas end users work in |
| Administration | Areas administrators and back-office staff work in |
| Integration | Exchanges with other systems |
| External service | A service the solution depends on but does not own |
| Reporting | Reports, dashboards, exports |
| Notification | Messages to people or systems |
| Platform | Cross-cutting capabilities such as authentication or audit |
| Other | State what it is in *Purpose* |

*Security boundary* states who may reach the module and what crosses its edge. *Data ownership* lists the entities (ENT-###) the module is responsible for; each entity has exactly one owner.

## Gate G5 — Solution and scope ready (with the scope register)

| Criterion | Checked by |
| --- | --- |
| At least one module; every module has a type and a purpose | `check_gates.py` |
| Every live requirement has a scope classification; every in-scope system requirement maps to a module | `check_gates.py` |
| Entities named under *Data ownership* exist; the module hierarchy has no cycle | `validate_handoff.py` via `check_gates.py` |
| `specification/scope.md` exists and every PENDING DECISION item has an open question (`templates/33`) | `check_gates.py` |
