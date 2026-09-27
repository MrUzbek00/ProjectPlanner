# CHANGE-000 — Short description of the change

TEMPLATE — change control, used at any stage once a baseline exists (`changes/baseline.json`, recorded at specification approval) or once a record has been approved or relied on by later stages. Copy to `changes/CHANGE-###.md`, one change per file; IDs are never reused. `tools/generate_handoff.py` reads it into `machine-handoff/changes.json`; `tools/analyze_change_impact.py projects/<project> CHANGE-###` analyses it and writes `changes/CHANGE-###-impact-report.md`; gate GC checks it.

A meaningful change is never a text edit. Record it here **before** editing the affected records: a change that is PROPOSED or UNDER_ANALYSIS does not alter the authoritative plan, and an edit made before approval is reported as such by gate GC. An edit with no change record at all is detected against the baseline and fails GC.

## Lifecycle

```text
Change requested → PROPOSED → impact analysis (UNDER_ANALYSIS) → human review → APPROVED or REJECTED
  → affected planning artifacts updated and dispositioned below → IMPLEMENTED_IN_PLAN
```

| Status | Meaning |
| --- | --- |
| PROPOSED | Requested; nothing in the plan changes |
| UNDER_ANALYSIS | Impact being analysed; nothing in the plan changes |
| APPROVED | Decided by the named authority. Every DIRECT and INDIRECT artifact becomes NEEDS_REVIEW until dispositioned below, and READY tasks among them lose their readiness |
| REJECTED | Decided against; the changed artifacts must keep their baseline state |
| IMPLEMENTED_IN_PLAN | Every affected artifact is dispositioned CURRENT with a resolution; every required review is done; the change is visible in the records |
| SUPERSEDED | Replaced by a later change named in *Superseded by* |

| Field | Value |
| --- | --- |
| Status | PROPOSED / UNDER_ANALYSIS / APPROVED / REJECTED / IMPLEMENTED_IN_PLAN / SUPERSEDED |
| Date | YYYY-MM-DD the change was requested |
| Change type | REQUIREMENT_CHANGE / ARCHITECTURE_CHANGE / SCOPE_CHANGE / BUSINESS_RULE_CHANGE / WORKFLOW_CHANGE / FEATURE_CHANGE / DATA_CHANGE / INTEGRATION_CHANGE / SECURITY_CHANGE / PRIORITY_CHANGE / DEPENDENCY_CHANGE / ROADMAP_CHANGE |
| Changed artifacts | The record IDs this change alters, for example FR-021 |
| Changed by | Who requested it — person, round or SRC-### |
| Approved by | The named decision authority, or TBD (Q-###) until decided |
| Approval evidence | DEC-### or SRC-### recording the approval or rejection; None until decided |
| Severity | CRITICAL / HIGH / MEDIUM / LOW, or TBD. The tool computes it; a declared severity may be higher, never lower |
| Decisions required | Q-### stakeholder decisions the change waits on, or None |
| Resolution status | OPEN / IN_PROGRESS / RESOLVED |
| Superseded by | CHANGE-### that replaced this one, or None |

Choose the most specific type. A change that is genuinely two changes — a scope move and a rule change — is two records.

## Previous state

The approved value before the change, verbatim with its IDs. The baseline keeps the full previous text of every record; this section says what matters.

## New state

The value after the change, verbatim with its IDs.

## Reason

Why the change is needed, with its source (SRC-###, round, DEC-###).

## Affected artifacts

The canonical record of impact. Run `python tools/analyze_change_impact.py projects/<project> CHANGE-###` and copy every DIRECT and INDIRECT artifact from the report; add POTENTIAL ones you confirm, and every record this change adds (*Impact level* NEW). Direct impact is the DIRECT rows; indirect impact the INDIRECT rows.

| Artifact | Impact level | Confidence | Review state | Resolution | Notes |
| --- | --- | --- | --- | --- | --- |

| Column | Values |
| --- | --- |
| Impact level | DIRECT (one link away), INDIRECT (further, through records that pass impact on), POTENTIAL (upstream assumption, shared module, mention only), NEW (a record this change creates) |
| Confidence | CONFIRMED (explicit links only), LIKELY (a membership or context link on the way), POSSIBLE (inferred) |
| Review state | NEEDS_REVIEW (not yet reviewed — the default for DIRECT and INDIRECT once approved), STALE (reviewed; out of date and must be updated), INVALID (no longer valid; rework, remove or defer it), CURRENT (reviewed and consistent with the new state) |
| Resolution | UPDATED, NO_CHANGE_NEEDED, ADDED, REMOVED, DEFERRED, REPLACED. UPDATED, ADDED, REMOVED and REPLACED must be visible as a difference from the baseline |

Review states are derived from this table, never typed into the affected records themselves: an artifact stays under review until a row here says CURRENT.

## Required reviews

One row per review area the impact report lists for this change type — for a requirement change: dependent requirements, architecture decisions, workflows, modules, features, tasks, acceptance criteria and tests, data entities, API contracts, UI screens, security requirements, integrations, roadmap, risks, traceability records and human deliverables. *Result* is DONE, N/A (with the reason in *Evidence*) or PENDING. IMPLEMENTED_IN_PLAN requires every area DONE or N/A.

| Review area | Result | Evidence |
| --- | --- | --- |

## Risk impact

Every risk the change creates, increases, reduces or retires. A NEW risk is added to `discovery/risks.md` first; a RETIRED risk is closed there. Required for a HIGH or CRITICAL change.

| Risk | Effect | Rationale |
| --- | --- | --- |

Effect is NEW, INCREASED, REDUCED, RETIRED or UNCHANGED.

## Roadmap impact

Affected phases and milestones, new dependencies, and whether the roadmap must be re-estimated. State only what can be determined; when timing cannot be determined reliably, say that re-estimation is required — never invent a date. A committed date in an affected phase needs its decision owner to reconfirm it.

## New work required

Work the change needs that no existing task covers: new features, tasks, tests or migrations, added as records and listed above with *Impact level* NEW. Existing tasks are never assumed to cover a changed requirement. Write `None — reason` when there is none.

## Document impact

The human deliverables that mention an affected artifact, from the impact report, and whether each was rebuilt.

## History

Nothing above is overwritten once the change is decided. A later correction is a new change that supersedes this one. The previous baseline is archived in `changes/history/` whenever a new baseline is recorded.
