# Specification Review

TEMPLATE — stage 8A, Independent Specification Review. Copy to `reviews/specification-review.md`. The review happens after gate G7 and before approval (stage 8B) and before any backlog is finalised.

The review exists so that ProjectPlanner never trusts its own specification without a second pass. It is performed by the **SPECIFICATION REVIEWER**. The reviewer acts as a skeptical senior business analyst, solution architect and QA reviewer, and is not the **SPECIFICATION AUTHOR** who wrote the specification.

| Role | Does | Does not |
| --- | --- | --- |
| SPECIFICATION AUTHOR | Writes and updates the specification and the records it consolidates; resolves findings in the stage that owns them | Grade their own work; close a finding without the reviewer's re-review |
| SPECIFICATION REVIEWER | Evaluates the specification independently against the source records; raises findings with evidence; recommends; re-reviews | Assume the author's conclusions are correct; summarise instead of review; rewrite requirements, ADRs, scope, workflows, roadmap or features |

When the planner is an AI agent, independence means a separate review pass. That pass starts from the records, not from the author's reasoning or conversation. It follows `prompts/specification-reviewer.md` and writes only this file. A person may review instead. Either way, name the reviewer and the author below, and say how the reviewer is independent.

**How a review cycle runs.** The review never fixes what it finds:

```text
detect → document (REVIEW-### finding) → recommend (required action) → wait for resolution by the author → re-review in the next cycle
```

1. Run `python tools/check_gates.py projects/<project>`. Gates G1–G7 pass; their warnings are inputs to the review. Read `reports/specification-review-aid.md`, which lists candidates computed from the records. It is not proof of anything: judge each candidate.
2. Examine the specification against the source records, area by area (checklist), and answer the twelve review questions.
3. Record every problem as a finding. Prefer a few well-evidenced findings over volume. Do not raise duplicates, vague findings, purely stylistic complaints, speculation, or contradictions that are not real.
4. Conclude: state the overall result and the counts, which must be the ones the findings support (rule below).
5. Close the cycle with `python tools/specification_review.py projects/<project> --start-cycle`. It freezes this file in `reviews/history/specification-review-cycle-NNN.md`, adds the cycle to the history table, and reopens every check and question as NOT REVIEWED for the next cycle. The author then resolves findings in the stage each one names, and the reviewer re-reviews.

`python tools/specification_review.py projects/<project>` prints the computed status at any time. `tools/check_gates.py` enforces it as gate **GR — Specification reviewed**.

## Review record

| Field | Value |
| --- | --- |
| Reviewed version | TBD — the specification version under review; must equal *Specification version* in `project-state.md` |
| Review cycle | 1 |
| Review date | TBD — YYYY-MM-DD, set when the cycle is complete |
| Reviewer | TBD — name of the SPECIFICATION REVIEWER |
| Specification author | TBD — name of the SPECIFICATION AUTHOR; must differ from the reviewer |
| Independence | TBD — how the reviewer is independent of the author, for example "separate review pass from the records only (prompts/specification-reviewer.md); no access to the author's reasoning" |
| Reviewed files | TBD — files covered by this cycle |
| Overall result | TBD — PASS, PASS WITH WARNINGS or FAIL, as the findings support |
| Open critical | 0 |
| Open major | 0 |
| Open minor | 0 |
| Open observations | 0 |
| Open findings | 0 |
| Accepted risks | 0 |
| Resolved since previous review | 0 |
| Findings raised | 0 |

**The result rule.** An unresolved CRITICAL finding gives FAIL, and so does an unresolved MAJOR finding: there is no threshold, and one is enough. If only MINOR or OBSERVATION findings are open, or findings are accepted risks, the result is PASS WITH WARNINGS. With no open finding the result is PASS. *Open* counts OPEN, ACKNOWLEDGED and IN_RESOLUTION findings. *Resolved since previous review* counts findings RESOLVED in this cycle. *Findings raised* counts every finding ever recorded.

## Checklist

Record every row as PASS, FAIL, N/A with a reason, or NOT REVIEWED. The evidence names what was examined: IDs and records, not impressions. A FAIL row cites the REVIEW-### finding that records the problem, and the finding's severity, not the row, decides the result. Gate GR fails while a row is blank, NOT REVIEWED, N/A without a reason, or FAIL without an open finding, and while an area below has no row. A blank checklist is not a pass. Rows about the backlog and roadmap are N/A with a reason before the backlog exists; they apply when the review is repeated after a change.

| Area | Check | Result | Evidence / IDs |
| --- | --- | --- | --- |
| Requirements quality | Every in-scope requirement states one need, unambiguously, without vague wording (fast, secure, user-friendly…) | NOT REVIEWED | |
| Requirements quality | Every requirement has rationale, source, evidence, stakeholder, priority and acceptance condition; its status and confidence match its evidence | NOT REVIEWED | |
| Requirements quality | No duplicated requirement; duplicates were consolidated without losing provenance | NOT REVIEWED | |
| Requirements quality | Priorities use the project's one scheme and are consistent with dependencies | NOT REVIEWED | |
| Scope consistency | Every in-scope capability is supported by an approved requirement; the specification introduces none of its own | NOT REVIEWED | |
| Scope consistency | No OUT OF SCOPE or FUTURE item appears as current work in the specification, features or tasks | NOT REVIEWED | |
| Scope consistency | No PENDING DECISION item is presented as approved | NOT REVIEWED | |
| Workflow completeness | Every major workflow names its actors, trigger, preconditions, main, alternative and exception paths, failure handling and result | NOT REVIEWED | |
| Workflow completeness | Every entity lifecycle is complete: every state reachable, transitions and forbidden transitions defined, rejection and cancellation where they exist | NOT REVIEWED | |
| Workflow completeness | No two workflows contradict each other | NOT REVIEWED | |
| Missing scenarios | Every major workflow covers the scenarios that make sense for it — success, failure, validation error, permission denied, external service unavailable, duplicate action, cancel, retry, timeout, empty state, invalid state transition; no meaningless edge case was added | NOT REVIEWED | |
| Permissions and authorisation | Every action states who may and may not perform it, with record scope and denial behaviour | NOT REVIEWED | |
| Permissions and authorisation | Administrative actions are controlled; ownership, escalation and approval rules are defined where they apply | NOT REVIEWED | |
| Permissions and authorisation | Tenant or organisation boundaries are explicit where more than one exists | NOT REVIEWED | |
| Security | Authentication, session behaviour and account recovery are specified, or raised as questions | NOT REVIEWED | |
| Security | Sensitive data, secrets, file uploads and external integrations have handling rules or open questions | NOT REVIEWED | |
| Security | Auditability, abuse cases and rate limiting are addressed where relevant; no security requirement was invented | NOT REVIEWED | |
| Data model | Every referenced entity is defined; no concept exists twice under different names | NOT REVIEWED | |
| Data model | Ownership, relationships and cardinality are consistent and possible; states do not conflict | NOT REVIEWED | |
| Data model | Lifecycle, retention and deletion behaviour are defined where relevant | NOT REVIEWED | |
| Integrations | Every external integration states purpose, owner, inputs, outputs, authentication and data ownership | NOT REVIEWED | |
| Integrations | Every external integration states failure, timeout and retry assumptions, fallback behaviour and its dependency risk | NOT REVIEWED | |
| Architecture consistency | No requirement or feature conflicts with an accepted ADR; accepted ADRs do not contradict each other | NOT REVIEWED | |
| Architecture consistency | No requirement relies on a decision that is PROPOSED or DECISION REQUIRED as if it were made; no superseded, rejected or deprecated ADR is used as active | NOT REVIEWED | |
| Architecture consistency | No major architecture decision is made in prose without an ADR | NOT REVIEWED | |
| Independent traceability | The chain GOAL → BR → FR/NFR → ADR → MOD → FEAT → AC was re-derived from the records, not read from the generated traceability | NOT REVIEWED | |
| Independent traceability | Every active requirement maps somewhere meaningful; every feature maps to an active requirement; no reference is broken, duplicated or points to a cancelled or superseded artifact | NOT REVIEWED | |
| Contradictions | Contradiction patterns were searched for (one vs many, delete vs retain, anonymous vs authenticated, and others); every contradiction candidate in the review aid is a finding or dismissed with a reason | NOT REVIEWED | |
| Acceptance criteria | Acceptance criteria are observable, testable, complete and free of contradiction and vague wording | NOT REVIEWED | |
| Terminology | One term per concept, used consistently; similar terms for distinct concepts are explicitly distinguished | NOT REVIEWED | |
| Assumptions | No assumption is treated as confirmed; every assumption still relied on is visible with its question | NOT REVIEWED | |
| Risks | Every major specification decision, external dependency and critical integration has its risk in the register | NOT REVIEWED | |
| Change consistency | Approved changes since the last review propagated: affected artifacts reviewed, stale items updated, invalid READY items reset, traceability refreshed, roadmap reconsidered | NOT REVIEWED | |
| Roadmap consistency | Sequencing follows dependencies; no blocked feature or milestone is scheduled too early or depends on an unresolved decision; scope and roadmap agree; no timeline assumption is unsupported | NOT REVIEWED | |
| Review quality | Every finding is specific, evidenced and not a duplicate; every CRITICAL and MAJOR finding cites the conflicting artifacts | NOT REVIEWED | |

## Review questions

The review's conclusions. Answer YES, NO, PARTIAL, or N/A with a reason. An answer that reports a problem — NO or PARTIAL, or YES to "Are there unresolved contradictions?" — cites the open REVIEW-### finding that records it. The last answer is YES exactly when the result is not FAIL.

| Review question | Answer | Evidence / findings |
| --- | --- | --- |
| Is the specification internally consistent? | NOT REVIEWED | |
| Are requirements complete enough? | NOT REVIEWED | |
| Are requirements testable? | NOT REVIEWED | |
| Are assumptions visible? | NOT REVIEWED | |
| Are workflows coherent? | NOT REVIEWED | |
| Are permissions defined? | NOT REVIEWED | |
| Are major security concerns covered? | NOT REVIEWED | |
| Does the architecture match the specification? | NOT REVIEWED | |
| Is traceability valid? | NOT REVIEWED | |
| Did recent changes propagate correctly? | NOT REVIEWED | |
| Are there unresolved contradictions? | NOT REVIEWED | |
| Is the specification safe to use as the basis for backlog planning? | NOT REVIEWED | |

## Findings

One record block per finding, `### REVIEW-### — Title`. Finding IDs are stable, numbered across all cycles, and never reused. A finding is never deleted: it is closed with a status, and the history snapshots prove it existed.

**Severity**

| Severity | Meaning | Examples | Effect |
| --- | --- | --- | --- |
| CRITICAL | The specification cannot safely proceed | Direct requirement contradiction; fundamental architecture conflict; unresolved security-critical behaviour; impossible workflow; missing core business rule | FAIL until RESOLVED or REJECTED; can never be an accepted risk |
| MAJOR | A substantial planning problem | Incomplete authorisation rules; an important missing exception path; a significant traceability gap; a feature not supported by approved requirements | FAIL until RESOLVED, REJECTED, or accepted as a risk by an authorised human |
| MINOR | Usable, but should be corrected | Inconsistent terminology; incomplete metadata; minor duplication | Warning |
| OBSERVATION | Not necessarily a defect; worth review | A future scalability concern; an optional clarification; a documentation improvement | Warning |

**Category**: REQUIREMENT, SCOPE, WORKFLOW, DATA, SECURITY, AUTHORIZATION, ARCHITECTURE, INTEGRATION, TRACEABILITY, ROADMAP, RISK, TERMINOLOGY, CHANGE_IMPACT, ACCEPTANCE_CRITERIA or ASSUMPTION.

**Status**

| Status | Meaning | Must record |
| --- | --- | --- |
| OPEN | Raised; nobody has acted | — |
| ACKNOWLEDGED | The author accepts it is a problem | — |
| IN_RESOLUTION | The resolution is under way (a question, decision or change record may be named in *Required action*) | — |
| RESOLVED | The author changed the records, and the reviewer verified the change in a **later** cycle | *Closed in cycle* (later than *Raised in cycle*), *Resolution*, *Resolved by*, *Resolution date*, *Changed artifacts*, *Verification* |
| ACCEPTED_RISK | An authorised human deliberately accepts it. Never for CRITICAL. It stays visible as a warning and is never converted to RESOLVED | *Closed in cycle*, *Resolution* (the reason), *Approved by* (not the author or reviewer), *Approval evidence* (DEC-### or SRC-###); for MAJOR, a RISK-### in the risk register |
| REJECTED | Judged not to be a defect | *Closed in cycle*, *Resolution* (why), *Resolved by*; for CRITICAL or MAJOR also *Approved by* and *Approval evidence* |

**What a finding must contain.** *Evidence* names specific artifacts and says what each states — "FR-021 allows several organisations per user, while SR-009 assumes exactly one" — never "the specification seems unclear". A CRITICAL or MAJOR finding lists its *Affected artifacts* and its *Return to stage*. *Why it matters* explains the consequence. *Required action* says what resolution is needed, without writing it: the reviewer recommends; the author resolves.

A contradiction is never two valid requirements. It is one finding, naming both sides under *Conflict*, until a recorded decision resolves it.

### REVIEW-001 — Title stating the problem, not the fix

| Field | Value |
| --- | --- |
| Severity | CRITICAL / MAJOR / MINOR / OBSERVATION |
| Category | One category from the list above |
| Status | OPEN |
| Raised in cycle | 1 |
| Affected artifacts | Every ID the finding concerns, for example FR-021, SR-009, ADR-006, FEAT-014 |
| Return to stage | The stage that owns the resolution, for example 3 — Requirement Analysis |
| Closed in cycle | Blank while unresolved |
| Resolution | Blank while unresolved |
| Resolved by | Blank while unresolved |
| Resolution date | Blank while unresolved |
| Changed artifacts | Blank while unresolved |
| Verification | Blank while unresolved |
| Approved by | Only for ACCEPTED_RISK, or REJECTED of a CRITICAL or MAJOR finding |
| Approval evidence | DEC-### or SRC-### recording that human decision |

**Evidence**

Which records state what, with their IDs.

**Conflict**

Only for a contradiction: the opposing statement, with its ID. Delete the section otherwise.

**Why it matters**

The consequence if the specification proceeds unchanged.

**Required action**

What must be resolved, and before which step (for example, before backlog approval).

## Dismissed candidates

Contradiction candidates from `reports/specification-review-aid.md` that are not real contradictions. Record why, so that the dismissal is reviewable. A candidate that is real becomes a finding instead.

| Candidate | Artifacts | Reason | Dismissed by |
| --- | --- | --- | --- |

## Cycle history

One row per **closed** cycle, added by `tools/specification_review.py --start-cycle` from the review record and frozen in its snapshot. The current cycle is the review record above. History is never rewritten: a row that disagrees with its snapshot, a missing snapshot, or a finding recorded in a snapshot and missing now fails gate GR.

| Cycle | Review date | Reviewed version | Reviewer | Overall result | Open critical | Open major | Open minor | Open observations | Accepted risks | Resolved since previous review | Snapshot |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## Gate GR — Specification reviewed

| Criterion | Checked by |
| --- | --- |
| The review exists, covers the current specification version, is dated and numbered | `specification_review.py` |
| The reviewer is named and is not the specification author; independence is stated | `specification_review.py` |
| Every review area has a checklist row; every row is examined; every FAIL row cites an open finding | `specification_review.py` |
| All twelve review questions are answered; every problem answer cites an open finding; the conclusion agrees with the result | `specification_review.py` |
| Every finding has severity, category, status, cycle and evidence; CRITICAL and MAJOR findings cite existing artifacts | `specification_review.py` |
| Every closed finding records its resolution, acceptance or rejection as its status requires; RESOLVED is verified in a later cycle; no CRITICAL finding is an accepted risk | `specification_review.py` |
| The stated result and counts are the ones the findings support | `specification_review.py` |
| Every closed cycle is frozen and agrees with its history row; no finding was deleted or backdated | `specification_review.py` |
| Every contradiction candidate is a finding or dismissed with a reason | `specification_review.py` |
| No approved change is dated after the review (otherwise re-review in a new cycle) | `specification_review.py` |
| No CRITICAL or MAJOR finding is unresolved | `specification_review.py` |
| `project-state.md` states the review summary the records show | `check_gates.py` (violation) |

Gate G8 (stage 8B) then requires GR to pass and a person's approval of the reviewed version, dated after a passing review of it. A failed review blocks approval, the backlog (G9) and every later gate, and no task can be READY. Backlog drafting may continue if it is useful, but it stays provisional: nothing may be called backlog-ready or planning-complete.
