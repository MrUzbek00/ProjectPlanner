# Architecture Principles

Project: TBD · Updated: TBD

TEMPLATE — stage 6. Copy to `architecture/principles.md`. Principles are the few, stable rules that guide architecture decisions in this project. They are not decisions: a principle says what the project prefers ("prefer simplicity over premature distribution"); an ADR records what it chose ("use a modular monolith", `templates/28`). An ADR cites the principles it applies in its *Principles* field.

Keep principles **few and meaningful** — typically three to seven. `tools/check_gates.py` warns above ten. A principle nobody could violate ("write good software") is not a principle.

Do not invent principles. A principle that a source or the decision authority stated is `Accepted` with its evidence (SRC-### or DEC-###); gate G6 fails an accepted principle without evidence. A principle the analyst recommends is `Proposed` — a recommendation, visible as a warning, until the decision authority accepts it. A principle that no longer applies is `Retired`, never deleted.

Keep the first column header exactly `PRIN ID`.

| PRIN ID | Principle | Rationale | Implications | Evidence | Status |
| --- | --- | --- | --- | --- | --- |

*Implications* says what the principle means for decisions in practice: "a new delivery channel needs an ADR explaining why the existing one cannot serve".

## Examples of well-formed principles

Illustrative only. Adopt one only when a source or the decision authority states it.

- Prefer simplicity over premature distribution.
- Keep domain boundaries explicit.
- Avoid duplicated sources of truth.
- Security-sensitive operations require explicit authorisation.
- Critical integrations must define their failure behaviour.
