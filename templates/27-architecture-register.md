# Architecture Register

Project: TBD · Updated: TBD

TEMPLATE — stage 6, Architecture Governance, after the solution structure and the scope register pass gate G5. Copy to `architecture/architecture-register.md`. It answers two questions at a glance: **which architecture decisions exist and what state they are in**, and **which major architecture questions are decided, still open, delegated or not applicable**. `tools/check_gates.py` reads both tables for gate G6; `tools/generate_handoff.py` writes the coverage table into `machine-handoff/architecture.json`.

The ADR files in `architecture/` are canonical (`templates/28`). This register is their ledger: it lists every ADR ID ever assigned — accepted, proposed, rejected, superseded and deprecated alike — so that no ID is ever reused, and its title, status, date and successor must agree with the ADR file. Register an ID the moment you assign it; never delete a row.

## ADR register

Keep the first column header exactly `ADR ID`. Gate G6 fails when an ADR file is missing from this table, when a row has no ADR file, or when the title, status, date or *Superseded by* differs from the file.

| ADR ID | Title | Status | Date | Decision owner | Related requirements | Superseded by |
| --- | --- | --- | --- | --- | --- | --- |

Status is Proposed, Accepted, Rejected, Superseded or Deprecated. Only Accepted decisions govern planning. `reports/architecture-report.md`, written by `tools/check_gates.py`, shows the current state with the requirements, features and tasks each decision reaches.

## Architecture decision coverage

Keep the first column header exactly `Concern`. Every concern below stays in the table; add rows for project-specific concerns. This is how the plan proves that all major architecture questions were identified and that none is hidden: an undecided choice that affects requirements, scope, security or the shape of the backlog is **ARCHITECTURE DECISION REQUIRED**, never a silently invented solution.

| Concern | Status | ADR IDs | Question | Rationale / evidence |
| --- | --- | --- | --- | --- |
| Architecture style | NOT ASSESSED | | | |
| Backend platform | NOT ASSESSED | | | |
| Frontend architecture | NOT ASSESSED | | | |
| Data storage | NOT ASSESSED | | | |
| Authentication | NOT ASSESSED | | | |
| Authorization model | NOT ASSESSED | | | |
| API style | NOT ASSESSED | | | |
| Integration strategy | NOT ASSESSED | | | |
| Event-driven messaging | NOT ASSESSED | | | |
| Background processing | NOT ASSESSED | | | |
| Caching | NOT ASSESSED | | | |
| File storage | NOT ASSESSED | | | |
| Deployment model | NOT ASSESSED | | | |
| Multi-tenancy | NOT ASSESSED | | | |
| Data ownership | NOT ASSESSED | | | |
| Module communication | NOT ASSESSED | | | |
| Logging and observability | NOT ASSESSED | | | |
| Security architecture | NOT ASSESSED | | | |
| External service dependencies | NOT ASSESSED | | | |
| Scalability strategy | NOT ASSESSED | | | |

| Status | Meaning | Gate G6 requires |
| --- | --- | --- |
| DECIDED | An accepted ADR settles it | At least one Accepted ADR in *ADR IDs*, and no rejected, superseded or deprecated one |
| PROPOSED | A proposed ADR is waiting for its decision | A Proposed ADR in *ADR IDs* |
| DECISION REQUIRED | The choice is open and matters; no ADR yet | An open question in *Question*. A BLOCKER question that affects in-scope work fails the gate; otherwise it is a visible warning |
| DELEGATED | Deliberately left to implementation within the accepted constraints | A reason and the SRC-### or DEC-### that delegated it |
| NOT APPLICABLE | The concern does not arise in this project | A reason and SRC-### or DEC-### evidence |
| NOT ASSESSED | Not yet considered | Nothing — the gate fails until it is assessed |

## Gate G6 — Architecture ready

| Criterion | Checked by |
| --- | --- |
| This register, `architecture/principles.md` and `reviews/architecture-review.md` exist | `check_gates.py` |
| Every standard concern is present and classified with the evidence its status needs | `check_gates.py` |
| Every ADR file is registered, every registered ID has a file, and register and file agree | `check_gates.py` |
| Proposed ADRs name the question that decides them; a BLOCKER one that affects in-scope work fails, others warn | `validate_handoff.py`, `check_gates.py` |
| Accepted, rejected, superseded and deprecated ADRs name their decision owner and approval evidence; accepted ones state context, decision and rationale | `validate_handoff.py` |
| No two accepted ADRs are recorded as conflicting; supersession links agree on both sides; only an accepted ADR replaces another | `validate_handoff.py` |
| No live requirement relies on a rejected, superseded or deprecated ADR | `validate_handoff.py` |
| Constraints are reviewable, and ADRs stay out of code-level detail (warnings) | `validate_handoff.py` |
| The architecture review is complete, covers every ADR in its current status, states the current counts, and every architecture conflict is resolved by CHANGE PROPOSAL, NEW ADR or SUPERSEDE ADR, or withdrawn with a reason | `check_gates.py` |
