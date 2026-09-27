# Requirement Register — <Business goals and requirements / Business rules / Functional / Non-functional / Data / Integration / Security / UX / Technical>

Project: TBD · Specification version: TBD · Updated: TBD

TEMPLATE — stage 3. Write requirements only after discovery has passed gate G2; a requirement drafted from a raw note is a guess with an ID. Copy this template once per register file into `specification/`:

| Project file | ID | Type |
| --- | --- | --- |
| `specification/business-requirements.md` | `GOAL-###` | Business goal: the measurable outcome the organisation wants |
| `specification/business-requirements.md` | `BR-###` | Business requirement: what the business needs in order to reach a goal |
| `specification/business-rules.md` | `RULE-###` | Business rule: a policy, calculation or constraint the business imposes |
| `specification/functional-requirements.md` | `FR-###` or `FR-<MODULE>-###` | Functional requirement: behaviour the system must provide |
| `specification/non-functional-requirements.md` | `NFR-###` | Non-functional requirement: a measurable quality — performance, availability, accessibility, localisation, … |
| `specification/data-requirements.md` | `DR-###` | Data requirement: data that must be captured, kept, migrated, retained or reported |
| `specification/integration-requirements.md` | `IR-###` | Integration requirement: an exchange with another system |
| `specification/security-requirements.md` | `SR-###` | Security requirement: protection, authentication, authorisation, audit, privacy |
| `specification/ux-requirements.md` | `UXR-###` | UX requirement: a user-experience need that is not a single function |
| `specification/technical-requirements.md` | `TR-###` | Technical requirement: an approved technical constraint or enabler |

Each entry is the **canonical** definition of that requirement: its ID, title, status, scope, links and acceptance criteria exist here and nowhere else. The specification, the deliverables and the Excel registers restate or reference it; `tools/generate_handoff.py` reads it into `machine-handoff/requirements.json`. Keep the heading, the field table and the section labels exactly as shown. One ID is one need: two unrelated needs are two requirements.

## Entry format — repeat per requirement

### FR-000 — Short, specific requirement title

| Field | Value |
| --- | --- |
| Status | Draft / Confirmed / Approved / Superseded / Rejected |
| Scope | In scope / Out of scope / Future / Pending decision |
| Confidence | Confirmed / Likely / Assumption / Unknown |
| Priority | In the project's scheme: Critical / High / Medium / Low, or Must / Should / Could / Won't |
| Priority basis | Confirmed — DEC-### or source / Proposed — rationale awaiting decision |
| Source | Upstream requirement this one serves: the GOAL a BR serves, the BR an FR serves. None only for a GOAL |
| Evidence | SRC-### with exact location; DEC-### |
| Related stakeholder | Who stated or owns the need |
| Dependencies | Requirement IDs this one needs, or None |
| Business rules | RULE-### applied by this requirement, or None |
| Related modules | MOD-### from `specification/solution-structure.md` (stage 5), or None yet |
| Architecture decisions | Optional: ADR-### that materially affect this requirement (stage 6), or omit. The ADR's *Related requirements* links it too; do not force a link on every requirement |
| Actor | FR: the role or system that acts |
| Trigger | FR: the event, action or schedule that starts the behaviour |
| Permissions | FR: who may and may not, under which condition; `N/A — reason` for pure system behaviour |
| Category | NFR / SR / DR / IR / TR: the quality or concern addressed |
| Superseded by | Replacement ID when Superseded; otherwise None |
| Detail | Path of the detail record if one exists (`requirements/FR-000.md`); otherwise None |

**Description**

One precise, observable statement in the project's confirmed terminology. Unknown parts are `TBD (Q-###)`, never guessed. State the need, not the design: no tables, endpoints or frameworks in a business, functional or UX requirement.

**Rationale**

Why the requirement exists — the problem it solves or the goal it serves.

**Acceptance criteria**

- AC-000 — Measurable, verifiable condition. Given/When/Then wording is welcome.
- AC-000 — Include denial, validation-failure and error outcomes where they apply.

**Notes**

Anything the reader needs that is not a requirement: context, history, related open questions.

A business goal replaces *Acceptance criteria* with three fields:

| Field | Value |
| --- | --- |
| Measure | What is measured, with its unit |
| Baseline | Current value and how it was obtained, or TBD (Q-###) |
| Target | Confirmed target and measurement period, or TBD (Q-###) |

## Field rules

| Field | Rule |
| --- | --- |
| Status | Lifecycle only. `Confirmed`: source-backed, with Confidence *Confirmed*. `Approved`: covered by an approved specification (gate G8) — the generator rejects Approved while the specification is not approved. Whether something is in the release is its *Scope*, not its status. |
| Scope | Classified by gate G5. IN SCOPE is delivered; OUT OF SCOPE and FUTURE are not; PENDING DECISION waits for the open question that names it. See `templates/33`. |
| Confidence | A Confirmed or Approved requirement must rest on Confirmed information. Likely, Assumption and Unknown belong in drafts, with the question or assumption that will settle them. |
| Priority | One scheme for the whole project, declared in `project-state.md`. Priority reflects business value, user value, risk, dependencies and regulatory need; it is not implementation order, and not everything is top priority. |
| Source | Every requirement except a GOAL has one. An FR, NFR, DR, IR, SR, UXR or TR traces to a BR; a BR traces to a GOAL. The reverse links are derived. |
| Acceptance criteria | Required for every Confirmed or Approved BR, FR, NFR, DR, IR, SR, UXR and TR. |
| Open questions | Not a field: a question names this ID under *Affected IDs* in `discovery/open-questions.md`, or the entry writes `TBD (Q-###)`. Both are picked up. |

Do not add numeric targets, security policies or performance values that no source or decision supports.

## Gate G3 — Requirements ready

`python tools/check_gates.py projects/<project> --gate G3` checks that at least one goal, business requirement and system requirement exist; that every live requirement has description, rationale, evidence, stakeholder, source and acceptance condition; that confidence is Confirmed; and that each traces upward. It lints wording and structure, and it requires `reviews/requirement-quality-review.md` (`templates/31`) with a complete checklist and no open CRITICAL or MAJOR finding.
