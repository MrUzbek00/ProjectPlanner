# Discovery Log

Project: TBD · Updated: TBD · Latest round: TBD

TEMPLATE — stage 2. Copy to `discovery/discovery-log.md`. Discovery establishes what is known and what still needs clarification, category by category. It is complete when every category is understood, explicitly not applicable, or only partially understood with its gaps recorded as questions — and no BLOCKER question is left affecting in-scope planning.

The registers this log points to are the canonical records: `discovery/open-questions.md`, `assumptions.md`, `risks.md`, `decisions.md`, `dependencies.md` and `sources.md` (`templates/02`). The log does not restate them; it shows coverage.

## Coverage

Keep the first column header exactly `Category` and keep all fourteen rows; `tools/check_gates.py` reads this table for gate G2.

| Category | Status | Confirmed information | Open questions | Assumptions | Risks | Sources |
| --- | --- | --- | --- | --- | --- | --- |
| Business | NOT STARTED | | | | | |
| Users | NOT STARTED | | | | | |
| Workflows | NOT STARTED | | | | | |
| Data | NOT STARTED | | | | | |
| Integrations | NOT STARTED | | | | | |
| Security | NOT STARTED | | | | | |
| Permissions | NOT STARTED | | | | | |
| Reporting | NOT STARTED | | | | | |
| Notifications | NOT STARTED | | | | | |
| Technical constraints | NOT STARTED | | | | | |
| UI/UX | NOT STARTED | | | | | |
| Operations | NOT STARTED | | | | | |
| Compliance | NOT STARTED | | | | | |
| Migration | NOT STARTED | | | | | |

| Status | Meaning |
| --- | --- |
| COMPLETE | Everything planning needs from this category is confirmed and sourced |
| PARTIAL | Some information is confirmed; the rest is open questions listed in the row |
| NOT STARTED | Not investigated — gate G2 fails |
| NOT APPLICABLE | Does not apply; the row states why and who confirmed it |

## Category detail — repeat per category as it is investigated

### <Category>

- **Confirmed:** statement — source (SRC-### location or round and date).
- **Likely:** statement — why it is likely; confirmation question Q-###.
- **Assumed:** ASM-### — what planning does until it is confirmed.
- **Unknown:** Q-### — why it matters and what it blocks.
- **Risks:** RISK-###.

## Interview rounds

Ask about three to five questions per round, the most important first, and only questions that the materials do not already answer. A BLOCKER question comes before any HIGH one.

| Round | Date | Questions asked | Answers received | Records updated |
| --- | --- | --- | --- | --- |

## Gate G2 — Discovery ready

| Criterion | Checked by |
| --- | --- |
| All fourteen categories are COMPLETE, PARTIAL or NOT APPLICABLE with a reason | `check_gates.py` |
| `open-questions.md`, `assumptions.md` and `risks.md` exist | `check_gates.py` |
| No open BLOCKER question affects in-scope planning. A blocker is resolved, or everything it affects is classified PENDING DECISION, FUTURE or OUT OF SCOPE | `check_gates.py` |
| Open HIGH questions and PARTIAL categories are visible | `check_gates.py` (warnings) |
| Every open question has a priority and a decision owner | `check_gates.py` |

A BLOCKER means that planning which depends on the answer cannot be trusted. Discovery does not end by guessing it; it ends by answering it or by explicitly taking what it affects out of the current scope.
