# Development Backlog, Dependencies and Roadmap

Project: TBD · Approved specification: TBD · Approval evidence: TBD

Populate after specification approval. A final backlog contains definition-complete leaf cards; future tasks may be blocked by predecessor completion. Do not mark them READY before their required inputs exist.

## Backlog index

| Card ID | Level | Epic | Feature | Parent task if any | Title / detail path | Requirement IDs | Priority / confirmation | Complexity | Definition completeness | Status | Blocked By | Blocking Cards | Phase |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Complexity scale

These are relative planning definitions, not calendar durations. Confirm the team's interpretation before using them for commitments.

| Size | Suggested interpretation |
| --- | --- |
| XS | One small, understood change with narrow validation |
| S | Bounded behavior with few interfaces and limited test variation |
| M | Coherent outcome across several components or meaningful rule/permission cases |
| L | Broad change with several interfaces or substantial verification; evaluate splitting |
| XL | Too broad or uncertain for predictable execution; decompose or resolve uncertainty |

Record complexity drivers. Missing business decisions cannot be hidden by choosing XL. Do not sum parent and child sizes as if they were independent effort estimates.

## Dependency edges

Direction is predecessor → successor.

| Predecessor card | Successor card | Required output / completion evidence | Reason | Edge type / external dependency reference |
| --- | --- | --- | --- | --- |

External prerequisites:

| Prerequisite | Affected cards | Required evidence | Owner | Availability | Risk / Q ID |
| --- | --- | --- | --- | --- | --- |

Optional dependency diagram: create Mermaid from actual edges only. Do not copy a generic database → authentication → roles sequence as if it were confirmed for this project.

### Dependency review

- [ ] Every predecessor/successor ID exists and refers to the intended executable unit.
- [ ] There are no self-dependencies or directed cycles.
- [ ] Every Blocked By edge has the corresponding reverse Blocking Cards link.
- [ ] Hierarchy parents are not accidentally treated as prerequisites for their own children.
- [ ] External prerequisites and unresolved questions are distinguishable from card edges.
- [ ] Every roadmap task appears in a dependency-consistent phase/sequence.
- [ ] A same-phase dependency has an explicit order and completion condition.

Review evidence / issues: TBD.

## Capacity and scheduling basis

- Team size / roles / availability: TBD
- Capacity / estimation evidence: TBD
- Confirmed deadline / external constraints: TBD
- Calendar dates permitted by available evidence? TBD
- If capacity is unknown: use complexity and dependency order; leave dates uncommitted.

## Roadmap — repeat for each phase or sprint

| Field | Phase definition |
| --- | --- |
| Phase ID / name | PHASE-## / confirmed name |
| Objective | Observable outcome |
| Cards | Executable card IDs; completed planning stages link to artifacts instead |
| Dependencies | Prior phases/cards and external conditions |
| Internal order / parallel work | Actual dependency-compatible sequence |
| Expected Deliverable | Reviewable result with path/type |
| Exit Criteria | Measurable criteria and required evidence |
| Complexity / capacity basis | Relative size or evidence-backed capacity |
| Dates if supported | TBD / uncommitted unless confirmed |

Cover applicable Discovery, System Design, UI/UX, Backend Development, Frontend Development, Integrations, Testing, UAT, Deployment, Training and Post-launch Support outcomes. Organize implementation into dependency-based increments; those labels do not require one card or one sprint per module/layer.

## Execution handoff

| First executable card(s) | Why ready | Inputs / artifact paths | Remaining external conditions | Expected evidence |
| --- | --- | --- | --- | --- |

Deferred work:

| Card / requirement IDs | Deferral reason | Authorizing decision | Current-release consequence | Re-entry condition |
| --- | --- | --- | --- | --- |
