# Development Backlog, Dependencies and Roadmap

Project: TBD · Approved specification: TBD · Approval evidence: TBD

Populate after specification approval, in `backlog/backlog.md`, together with the epic and feature records from `templates/07`. Each executable task is its own card in `backlog/tasks/TASK-###.md` (`templates/08`), and that card is canonical for the task. A task is READY only when it passes every Definition of Ready check (`templates/08`); generating it does not make it ready. A READY card may still wait on predecessors, and its place in the order comes from its dependencies. Priority is business importance; sequence is the recommended order. A high-priority task whose prerequisites are missing does not go first.

Stage 10B validates readiness: `tools/generate_handoff.py` and `tools/backlog_readiness.py` write `backlog/readiness-report.md` and `machine-handoff/backlog-readiness.json`. They record the backlog status (READY, PARTIALLY READY or NOT READY), what blocks each task, phase readiness, the ready work sets and the flags for review. Gate GB evaluates it. The backlog does not have to be READY everywhere before useful work starts: a valid subset may be, while the rest stays visibly unresolved.

`tools/generate_handoff.py` reads the epics, features and phases in this file and the task cards into `machine-handoff/backlog.json`, computes a deterministic dependency order, and checks this file's backlog index against the cards. A status, epic, feature or *Blocked By* value here that differs from the card is an error, so update the card first and the index with it.

## Backlog index

| Task ID | Level | Epic | Feature | Parent task if any | Title / detail path | Requirement IDs | Priority / confirmation | Complexity | Status | Blocked By | Phase |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Blocking relationships (the reverse of *Blocked By*) and the execution sequence are generated into `backlog.json` and `traceability/requirement-map.md`; they are not maintained by hand.

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

| Predecessor task | Successor task | Required output / completion evidence | Reason | Edge type / external dependency reference |
| --- | --- | --- | --- | --- |

External prerequisites:

| Prerequisite | Affected cards | Required evidence | Owner | Availability | Risk / Q ID |
| --- | --- | --- | --- | --- | --- |

Optional dependency diagram: create Mermaid from actual edges only. Do not copy a generic database → authentication → roles sequence as if it were confirmed for this project.

### Dependency review

- [ ] Every predecessor/successor ID exists and refers to the intended executable unit.
- [ ] There are no self-dependencies or directed cycles.
- [ ] Every edge here matches the successor card's Blocked By field (the generator derives the reverse links).
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

Name phases by the outcome they deliver. Useful defaults: **Foundation** (what everything else depends on), **Core Product** (the in-scope capabilities the goal needs), **Operations** (what running the product requires), **Enhancement** (valuable additions and work waiting on pending decisions), **Launch Preparation** (acceptance, migration, training, go-live readiness). Order comes from dependencies, then priority — priority alone is not an order.

Every date in the plan carries a basis, and the basis is stated wherever the date appears:

| Date basis | Meaning | Required evidence |
| --- | --- | --- |
| Target | A date someone would like; nobody has checked it is achievable | Who wants it |
| Estimate | Derived from sized work and known capacity | The sizing and the capacity it assumes |
| Commitment | Agreed by the people accountable for delivering it | A decision (DEC-###) recording the agreement |
| None | No date is set | — |

A date without a basis, or a commitment without a decision, fails gate G11. Without confirmed capacity there are no estimates, only targets or no date; do not convert complexity into calendar time by assumption.

### PHASE-00 — Foundation / Core Product / Operations / Enhancement / Launch Preparation

| Field | Value |
| --- | --- |
| Objective | Observable outcome |
| Dependencies | Prior phases/tasks and external conditions |
| Internal order / parallel work | Actual dependency-compatible sequence |
| Expected Deliverable | Reviewable result with path/type |
| Exit Criteria | Measurable criteria and required evidence |
| Complexity / capacity basis | Relative size or evidence-backed capacity |
| Date | YYYY-MM-DD, or None |
| Date basis | Target / Estimate / Commitment / None |
| Commitment decision | DEC-### when the basis is Commitment; otherwise None |

A task joins a phase through the *Phase* field on its card; the phase's task list is derived. Phases run in ID order, and a task scheduled in an earlier phase than one of its predecessors is an error. Completed planning stages link to artifacts instead of cards.

Cover applicable Discovery, System Design, UI/UX, Backend Development, Frontend Development, Integrations, Testing, UAT, Deployment, Training and Post-launch Support outcomes. Organize implementation into dependency-based increments; those labels do not require one card or one sprint per module/layer.

## Execution handoff

Copy the ready work sets from `backlog/readiness-report.md`; WS-01 is what can start now.

| Work set / task(s) | Why ready | Inputs / artifact paths | Remaining external conditions | Expected evidence |
| --- | --- | --- | --- | --- |

Excluded or cancelled work — a FUTURE, OUT OF SCOPE or PENDING DECISION scope, or a CANCELLED task:

| Task / requirement IDs | Reason | Authorizing decision | Current-release consequence | Re-entry condition |
| --- | --- | --- | --- | --- |
