# Requirement-to-Delivery Traceability

Project: TBD · Specification version: TBD · Stage: PRE-APPROVAL / POST-APPROVAL / HANDOFF

Use stable IDs and links to actual project artifacts. One requirement may span several rows/cards/tests. Do not put unrelated comma-separated IDs in one row when that would hide which test validates which behavior.

Traceability is maintained from the moment the first requirement is written, not assembled at the end. The chain every in-scope item must complete is:

```text
Business goal (GOAL) → Business requirement (BR) → FR / NFR / DR / IR / SR / UXR / TR
    → Module (MOD) → Feature (FEAT) → Task (TASK) → Acceptance criteria (AC) → Test (TEST)
```

Architecture traceability explains why each technical constraint exists:

```text
Requirement → ADR → Feature → Task          (which decisions govern this work)
ADR → affected requirements → affected features → affected tasks   (what a decision reaches)
```

Both directions are generated: `traceability/requirement-map.md` has an *Architecture decisions* section and an ADRs column on every chain, and `machine-handoff/traceability.json` lists, for each ADR, the requirements, features, tasks and modules it governs. `tools/analyze_change_impact.py projects/<project> ADR-###` lists the same reach before an ADR changes.

Every backlog item needs a reason to exist. `tools/generate_handoff.py` reports orphans — in-scope requirements with nothing upstream, features with no requirement, tasks with no requirement, feature or acceptance criteria — and `tools/check_gates.py` fails gate G9 or G12 on them. When a record changes, record the change and run `tools/analyze_change_impact.py`; update every link it lists, and keep traceability consistent before and after the change.

Copy to `traceability/traceability.md`. This matrix is the analyst's review record: coverage dispositions, deferral authority and findings. The links themselves are also generated from the canonical records by `tools/generate_handoff.py`, into `traceability/requirement-map.md` for people and `machine-handoff/traceability.json` for tools. When this matrix and the generated map disagree, the records are right and this matrix is out of date; the generator warns about any ID written here that no record defines. Take the coverage counts below from the generated coverage summary rather than counting by hand.

## Business and functional traceability

| Business goal / requirement | Functional Requirement | Business Rule IDs | Module | Page | Task | Acceptance Criterion | Acceptance Test | Source / decision | Coverage disposition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Before specification approval, Task is `Pending — specification not approved`. At handoff, every in-release FR has actual task and test links. A non-UI requirement has `N/A — confirmed non-UI behavior` with evidence in the relevant model; do not invent a page.

## Non-functional and technical traceability

| BR / related FR | NFR / DR / IR / SR / UXR / TR ID | Approved rationale / source | Affected module / component | Page or reasoned N/A | Task | AC ID | TEST / verification method | Approval version | Coverage disposition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Technical enablers must trace to approved requirements. Requirements established only during decomposition need a recorded decision and baseline update before affected cards become ready.

## Business outcome coverage

| GOAL / BR ID | Implementing FR / NFR / DR / IR / SR / UXR / TR IDs | Business acceptance measure / TEST IDs | Covered / gap / explicitly excluded | Evidence / decision |
| --- | --- | --- | --- | --- |

Distinguish software capability verification from a post-launch business metric that requires actual operational data.

## Reverse card coverage

| Task ID | Approved requirement IDs | AC / TEST IDs | Parent feature / epic | Detail file | Orphan? / finding |
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

- Every in-release BR outcome maps to implementing requirements and a measurable acceptance approach.
- Every in-release FR/NFR/TR maps to appropriate tests and, after approval, executable cards.
- Every card maps back to approved scope; hierarchy containers have linked child coverage.
- IDs, page/module mappings and approved versions agree across the specification and cards.
- All exclusions are authorized and visible; no gap is hidden as N/A.
