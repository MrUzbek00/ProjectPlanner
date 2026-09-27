# Project Intake

Project: TBD · Intake date: TBD · Analyst: TBD

TEMPLATE — stage 1. Copy to `discovery/project-intake.md` and fill it from the materials and the first conversation, before any analysis. Its job is to record what is known *and how well it is known*, not to fill gaps.

Every item carries a classification:

| Classification | Meaning |
| --- | --- |
| CONFIRMED | Stated by an attributable source or the decision authority. Cite it. |
| LIKELY | Strongly suggested by the materials but not stated. Say why. |
| ASSUMED | A working assumption. Record it in `discovery/assumptions.md` and cite the ASM-###. |
| UNKNOWN | Not known. Raise a question in `discovery/open-questions.md` and cite the Q-###. |

"None supplied" is a confirmed fact, not an unknown, when the owner has said so. An assumption written as a fact is the defect this record exists to prevent.

## Intake

Keep the first column header exactly `Intake item` and keep every row; `tools/check_gates.py` checks all fourteen for gate G1.

| Intake item | Information | Classification | Source |
| --- | --- | --- | --- |
| Project name | TBD | UNKNOWN | TBD |
| Project objective | TBD | UNKNOWN | TBD |
| Business problem | TBD | UNKNOWN | TBD |
| Target users | TBD | UNKNOWN | TBD |
| Stakeholders | TBD | UNKNOWN | TBD |
| Known scope | TBD | UNKNOWN | TBD |
| Constraints | TBD | UNKNOWN | TBD |
| Deadlines | TBD | UNKNOWN | TBD |
| Existing systems | TBD | UNKNOWN | TBD |
| Available files | TBD | UNKNOWN | TBD |
| Screenshots | TBD | UNKNOWN | TBD |
| Stakeholder notes | TBD | UNKNOWN | TBD |
| Known assumptions | TBD | UNKNOWN | TBD |
| Known risks | TBD | UNKNOWN | TBD |

Register every supplied file in `discovery/sources.md` (SRC-###) and every known risk in `discovery/risks.md` (RISK-###) as you go.

## Gate G1 — Intake complete

| Criterion | Checked by |
| --- | --- |
| All fourteen items are present and classified CONFIRMED, LIKELY, ASSUMED or UNKNOWN | `check_gates.py` |
| Every UNKNOWN item names the question that will resolve it; every ASSUMED item names its assumption record | `check_gates.py` (warning) |
| `project-state.md` has a Project ID | `check_gates.py` |
| Supplied materials are registered with their readability gaps | Analyst |

When G1 passes, set *Current stage* in `project-state.md` to `2 — Discovery`.
