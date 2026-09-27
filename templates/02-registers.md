# Evidence, Uncertainty and Decision Registers

Project: TBD · Version: TBD · Updated: TBD

These registers hold what the project knows, what it does not know, what it has assumed, what could go wrong and what it has decided. They are living records: started at intake, updated in every stage, and read by every gate. A register kept only as a final document is not a register.

Each register is copied into its own project file. The first six are read by `tools/generate_handoff.py` and `tools/check_gates.py`, so keep their first column header exactly as shown; rows whose first cell is not a valid ID are ignored.

| Register | Project file | Machine handoff |
| --- | --- | --- |
| Source inventory | `discovery/sources.md` | `requirements.json` → `sources` |
| Open questions | `discovery/open-questions.md` | `decisions.json` → `questions` |
| Assumptions | `discovery/assumptions.md` | `decisions.json` → `assumptions` |
| Risks | `discovery/risks.md` | `decisions.json` → `risks` |
| Decision log | `discovery/decisions.md` | `decisions.json` → `decisions` |
| External dependencies | `discovery/dependencies.md` | `backlog.json` → `external_dependencies` |
| Requirements and business rules | `specification/*-requirements.md`, `specification/business-rules.md` (`templates/26`) | `requirements.json` |
| Scope boundaries | `specification/scope.md` (`templates/33`) | `requirements.json` → `scope_items` |
| Stakeholders, glossary, recommendations, reconciliation | `discovery/registers.md` | Not exported |
| Change records | `changes/CHANGE-###.md` (`templates/35`); baseline `changes/baseline.json` | `changes.json` |

A project that keeps the first six in one `discovery/registers.md` still works: the generator reads them from there when their own files do not exist. Never define the same ID in both places.

## Source inventory

| Source ID | Title / filename / path or URL | Type | Author / owner | Date / version | Authority: authoritative / reference example / unconfirmed | Exact analyzed locations | Readability / access gaps | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

For chat answers, record message date and identifying context. For documents, use section/page; for spreadsheets, use sheet/cells; for screenshots, use filename and visible region. Preserve originals where supplied. Do not claim to have read inaccessible content.

## Open questions

Copy to `discovery/open-questions.md`. This is the one register of open questions; discovery rounds, the specification, reviews and task cards refer to it by `Q-###`.

| Question ID | Category | Focused question | Why it matters | Priority | Affected IDs | Decision owner | Round | Status | Answer / source / decision | Resolution impact |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

| Priority | Meaning | Effect |
| --- | --- | --- |
| BLOCKER | Planning that depends on the answer cannot be trusted | Fails every gate from G2 while it is open, unless everything under *Affected IDs* is PENDING DECISION, FUTURE or OUT OF SCOPE. Keeps affected tasks out of READY |
| HIGH | The answer will materially change requirements, scope or sequencing | Warning at G2; ask in the next round |
| MEDIUM | The answer refines a detail | Visible in reviews and the package |
| LOW | Useful to know; no plan depends on it | Visible in the package |

*Category* is one of the fourteen discovery categories (`templates/30`). *Affected IDs* names the requirements, features, tasks and scope items the answer changes — this is how a question is linked; do not repeat the link on the records. Status is OPEN, ANSWERED, RESOLVED, DEFERRED, WITHDRAWN or CLOSED; DEFERRED is still unresolved. When a question is answered, record the answer, update every affected record, and record the decision in the decision log.

## Assumptions

Copy to `discovery/assumptions.md`.

| ASM ID | Provisional statement | Confidence | Why considered | Risk if wrong | Affected IDs | Q ID | Status | Resolution / DEC ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Confidence is LIKELY, ASSUMPTION or UNKNOWN — an assumption is never CONFIRMED; a confirmed assumption becomes a fact with a source and the row closes. Status is OPEN, CONFIRMED or REJECTED. Every open assumption has the question that will settle it. No Confirmed or Approved requirement may rest on an open assumption.

## Risks

Copy to `discovery/risks.md`. Update it in every stage: a risk found in discovery can change requirements; a risk found while sequencing can change the roadmap.

| Risk ID | Description | Category | Probability | Impact | Mitigation | Owner | Status | Affected IDs | Last reviewed | Blocks readiness |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

| Column | Values |
| --- | --- |
| Category | Scope, Technical, Business, Dependency, Integration, Security, Data, Timeline, Stakeholder, Other |
| Probability, Impact | High, Medium, Low, Unknown — a qualitative assessment; state its basis in *Mitigation* or *Description*. Do not invent percentages |
| Status | OPEN, MITIGATING, ACCEPTED, CLOSED, OCCURRED |
| Blocks readiness | Yes or No. A risk does not block work automatically: Yes records the decision that, while the risk is OPEN, MITIGATING or OCCURRED, no task, feature or requirement it names in *Affected IDs* may be READY |

An open risk with High probability or High impact needs a mitigation and a named owner by gate G11; an owner is never guessed — write `TBD (Q-###)` and ask.

## Decision log

Copy to `discovery/decisions.md`. Record every decision that settles a question, chooses between options, changes scope or confirms a priority, so the same issue is not reopened without context.

| Decision ID | Date | Question | Options considered | Decision | Rationale | Impact | Approved by | Related requirements | Supersedes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

*Approved by* is the person or body with authority for this decision, taken from the stakeholder register — never assumed. A decision that reverses an earlier one names it under *Supersedes*; the earlier row stays. Architecture decisions are also recorded as ADRs (`templates/28`) that cite the DEC-###.

## External dependencies

Copy to `discovery/dependencies.md`. Features and task cards name the dependencies they rely on in their *External dependencies* field; a task cannot be READY while one of them is not AVAILABLE.

| Dependency ID | Description | Type | Owner | Status | Needed for | Related risk / question |
| --- | --- | --- | --- | --- | --- | --- |

Type is External system, Department, Vendor, Data, Decision or Other. Status is AVAILABLE, PENDING, UNAVAILABLE or UNKNOWN.

## Stakeholders

| Stakeholder | Organization / department | Responsibility | Project decision authority | System role ID if applicable | Confirmation source |
| --- | --- | --- | --- | --- | --- |

## Glossary

| Term | Canonical definition | Uzbek / Russian domain term or synonym | Avoid / ambiguous alternatives | Units / context | Source / decision |
| --- | --- | --- | --- | --- | --- |

## Recommendations

| REC ID | Proposed improvement | Problem addressed | Benefits | Tradeoffs / cost / risks | Affected scope | Decision owner | Status: PROPOSED / ACCEPTED / REJECTED | DEC ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

A recommendation changes nothing until accepted in the decision log.

## Requirement reconciliation

| Retired / duplicate ID | Canonical ID | Why consolidated / replaced | Source references preserved | Links updated | Decision / revision |
| --- | --- | --- | --- | --- | --- |

Out-of-scope and deferred items are recorded in the scope register (`templates/33`); post-approval changes are change requests (`templates/35`).
