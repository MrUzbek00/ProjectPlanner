# ADR-000 — Decision title stated as the choice made

TEMPLATE — stage 6, Architecture Governance. Copy to `architecture/ADR-###-<short-title>.md`, one decision per file, and name the file after its ID (for example `architecture/ADR-004-modular-monolith.md`). Keep the heading, the field table and the section labels as shown; `tools/generate_handoff.py` reads them into `machine-handoff/architecture.json`. Register the ID in `architecture/architecture-register.md` (`templates/27`) the moment you assign it.

An ADR records one **significant** architecture decision: a choice with project-wide or long-term consequences that constrains what downstream planning may do. It is not a requirement, and it is not implementation design. Write one when the choice concerns an architecture style, a platform or framework, the frontend architecture, data storage, authentication or authorisation, the API style, integration, events or background processing, caching, file storage, deployment, multi-tenancy, data ownership, communication between major modules, observability, a security-sensitive boundary, a dependency on an external service, or a scalability strategy. Do not write one for a helper name, a CSS class or a small utility library unless that choice has project-wide consequences.

## Lifecycle

| Status | Meaning | Who sets it |
| --- | --- | --- |
| Proposed | Under consideration. Governs nothing yet; every task bound by it stays out of READY. Names the open question (Q-###) that decides it | The analyst, whenever an architecture question is identified |
| Accepted | Approved; governs all planning until it is superseded or deprecated | Only the named decision owner, recorded as a DEC-### or SRC-### |
| Rejected | Considered and not accepted. Kept so the question is not reopened without its context | The decision owner, with evidence |
| Superseded | Replaced by a newer accepted ADR, named in *Superseded by* | Set when the successor is accepted |
| Deprecated | Historically relevant; no new planning may rely on it | The decision owner, with evidence |

Never edit an accepted ADR to represent a new direction. Write a new ADR that names this one under *Supersedes*; when the decision owner accepts it, set this one to Superseded and name the successor under *Superseded by*. Both links must agree, and a proposed ADR replaces nothing. IDs are never reused and ADR files are never deleted — a withdrawn idea is Rejected, not removed.

| Field | Value |
| --- | --- |
| Status | Proposed / Accepted / Rejected / Superseded / Deprecated |
| Date | YYYY-MM-DD of the decision; TBD while Proposed |
| Decision owner / Approver | Named authority from the stakeholder register, or TBD (Q-###) while Proposed |
| Approval evidence | DEC-### or SRC-### recording the human decision; None while Proposed |
| Decision question | Q-### whose answer decides this ADR while Proposed; None once decided |
| Related requirements | Requirement IDs this decision serves or constrains — only where it materially affects them |
| Related features | FEAT-### known when the ADR is written, or None. Features that name this ADR are linked automatically |
| Affected modules | MOD-### IDs from `specification/solution-structure.md` |
| Related decisions | DEC-### records behind it, or None |
| Principles | PRIN-### principles it applies, or None |
| Depends on | ADR-### or DEP-### it relies on, or None |
| Conflicts with | ADR-### that cannot hold at the same time as this one, or None |
| Supersedes | ADR-### replaced by this one, or None |
| Superseded by | ADR-### that replaced this one, or None |

## Context

The problem and the forces behind the decision: the confirmed requirements, constraints, risks and principles, with their IDs. Facts only; a recommendation is labelled as one.

## Decision

What was decided, stated at architecture level so that an implementer can follow it without reinterpretation. Name the approach, not the code: "Authentication belongs to the shared identity module", not "Create class AuthService in src/auth/service.py".

## Rationale

Why this option was chosen over the others, citing the requirements, constraints and principles it satisfies.

## Alternatives considered

| Option | Description | Advantages | Disadvantages | Outcome |
| --- | --- | --- | --- | --- |

Record the option chosen and every realistic option rejected, with *Outcome* `Chosen` or `Rejected — reason`. The gate checker searches requirements, features and tasks for the names of options an accepted ADR rejected and reports each hit as an ARCHITECTURE CONFLICT, so name options specifically ("GraphQL", "Firebase Authentication"). An accepted ADR with no alternatives is reported as a warning.

## Consequences

### Positive

- What becomes easier, safer or cheaper.

### Negative

- What becomes harder, more expensive or riskier, including follow-up work.

## Risks

- RISK-### or a described risk the decision introduces or accepts. `None` if there is none.

## Constraints introduced

- One constraint per line, in testable or reviewable language: "All business modules are deployed as one application"; "No module reads another module's tables directly". Not "keep the architecture clean", "use best practices" or "make it scalable" — the gate checker flags such wording.

## Notes

Anything else a reader needs, or None.

---

## Example — a complete ADR

The example below is illustrative. Its IDs, modules and people do not belong to any project; never copy it into a project as if it were a decision.

```markdown
# ADR-004 — Use a modular monolith

| Field | Value |
| --- | --- |
| Status | Accepted |
| Date | 2026-03-18 |
| Decision owner / Approver | Head of Engineering (stakeholder register) |
| Approval evidence | DEC-011 |
| Decision question | None |
| Related requirements | NFR-004, TR-002 |
| Related features | None |
| Affected modules | MOD-001, MOD-002, MOD-003 |
| Related decisions | DEC-011 |
| Principles | PRIN-001 |
| Depends on | None |
| Conflicts with | None |
| Supersedes | None |
| Superseded by | None |

## Context

TR-002 limits operations to one application runtime maintained by a team of four (SRC-003).
NFR-004 requires that the authentication and billing areas can be changed independently.
PRIN-001 prefers simplicity over premature distribution.

## Decision

The solution is one deployable application divided into modules with explicit boundaries.
Modules communicate only through their published internal interfaces.

## Rationale

One deployable unit satisfies TR-002; explicit module boundaries satisfy NFR-004 without the
operational cost of independently deployed services.

## Alternatives considered

| Option | Description | Advantages | Disadvantages | Outcome |
| --- | --- | --- | --- | --- |
| Modular monolith | One application, explicit modules | One runtime to operate; clear boundaries | Modules scale together | Chosen |
| Microservices | One service per module | Independent scaling and deployment | Several runtimes for a team of four (TR-002) | Rejected — exceeds TR-002 |

## Consequences

### Positive

- One deployment pipeline and one runtime to monitor.

### Negative

- A module cannot be scaled on its own; if NFR-004 grows into that need, a new ADR is required.

## Risks

- RISK-007 — module boundaries erode without review.

## Constraints introduced

- All business modules are deployed as one application.
- Modules communicate only through their published internal interfaces; no module reads another module's data store directly.
- No independently deployed service is introduced without a new ADR that supersedes this one.

## Notes

None.
```

With ADR-004 accepted, a feature that proposes "a separate microservice for notifications" is reported as an ARCHITECTURE CONFLICT ("Microservices" was rejected). Planning then changes the feature, or records ADR-012 as Proposed with *Supersedes* ADR-004, obtains the decision owner's approval, and only then marks ADR-004 Superseded.

## How an ADR applies

- **Requirements.** The ADR's *Related requirements* links it to the requirements it materially affects; a requirement may also name ADRs in its own *Architecture decisions* field. Do not force a link on every requirement.
- **Features.** A feature names the ADRs it relies on in *Architecture decisions* (`templates/07`); ADRs reached through its requirements or modules are added automatically, so constraints are visible before any task is written.
- **Tasks.** A task is bound by an ADR when it names it, through a source requirement, through a module, or when its feature names it. The generator records which in each task's `architecture_decisions`, and a task bound by an ADR that is not Accepted cannot be READY.
- **Inactive decisions.** Rejected, superseded and deprecated ADRs apply to nothing. A live requirement, feature or task that names one fails its gate, with the successor named when there is one.
