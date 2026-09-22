# Requirement-to-Delivery Traceability

Project: TBD · Specification version: TBD · Stage: PRE-APPROVAL / POST-APPROVAL / HANDOFF

Use stable IDs and links to actual project artifacts. One requirement may span several rows/cards/tests. Do not put unrelated comma-separated IDs in one row when that would hide which test validates which behavior.

## Business and functional traceability

| Business Requirement | Functional Requirement | Business Rule IDs | Module | Page | Development Card | Acceptance Criterion | Acceptance Test | Source / decision | Coverage disposition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Before specification approval, Development Card is `Pending — specification not approved`. At handoff, every in-release FR has actual executable card and test links. A non-UI requirement has `N/A — confirmed non-UI behavior` with evidence in the relevant model; do not invent a page.

## Non-functional and technical traceability

| BIZ / related FR or NFR | NFR / TR ID | Approved rationale / source | Affected module / component | Page or reasoned N/A | Executable Card | AC ID | AT / verification method | Approval version | Coverage disposition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Technical enablers must trace to approved requirements. Requirements established only during decomposition need a recorded decision and baseline update before affected cards become ready.

## Business outcome coverage

| BIZ ID | Implementing FR / NFR / TR IDs | Business acceptance measure / AT IDs | Covered / gap / explicitly excluded | Evidence / decision |
| --- | --- | --- | --- | --- |

Distinguish software capability verification from a post-launch business metric that requires actual operational data.

## Reverse card coverage

| Executable Card ID | Approved requirement IDs | AC / AT IDs | Parent feature / epic | Detail file | Orphan? / finding |
| --- | --- | --- | --- | --- | --- |

## Deferred / superseded coverage

| Requirement ID | Disposition | Authorizing decision | Replacement ID if any | Why no current-release card | Consequence |
| --- | --- | --- | --- | --- | --- |

## Coverage review

Record counts only after calculating them from the actual inventories. Do not infer completeness from the existence of this matrix.

| Measure | Count | Evidence / inventory |
| --- | --- | --- |
| In-release business requirements | TBD | TBD |
| In-release functional requirements | TBD | TBD |
| In-release NFRs and technical requirements | TBD | TBD |
| Requirements with appropriate acceptance tests | TBD | TBD |
| Requirements with executable cards (post-approval) | TBD | TBD |
| Requirements missing cards (post-approval) | TBD | TBD |
| Requirements missing measurable criteria/tests | TBD | TBD |
| Executable cards without approved requirements | TBD | TBD |
| Broken / undefined IDs | TBD | TBD |
| Explicitly deferred/excluded requirements | TBD | TBD |

Review criteria:

- Every in-release BIZ outcome maps to implementing requirements and a measurable acceptance approach.
- Every in-release FR/NFR/TR maps to appropriate tests and, after approval, executable cards.
- Every card maps back to approved scope; hierarchy containers have linked child coverage.
- IDs, page/module mappings and approved versions agree across the specification and cards.
- All exclusions are authorized and visible; no gap is hidden as N/A.
