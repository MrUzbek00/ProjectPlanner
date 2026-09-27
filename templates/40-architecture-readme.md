# Architecture — Project TBD

TEMPLATE — stage 6. Copy to `architecture/README.md` and replace the project name. It tells anyone opening this folder how the project's architecture decisions are governed. Keep it short; the rules live in `WORKFLOW.md` section 11.

## What is here

| File | What it holds |
| --- | --- |
| `architecture-register.md` | Every ADR ID ever assigned, with its status, and how each major architecture concern stands (decided, proposed, decision required, delegated, not applicable) |
| `principles.md` | The few principles that guide decisions (PRIN-###) |
| `ADR-###-<short-title>.md` | One file per architecture decision record |

The review of these decisions is `../reviews/architecture-review.md`; the generated current state is `../reports/architecture-report.md`; the machine-readable form is `../machine-handoff/architecture.json`. The Markdown files here are the source of truth; the report and the JSON are generated from them.

## Rules

- Only **Accepted** ADRs govern planning. Proposed ones are waiting for a named human decision owner; rejected, superseded and deprecated ones apply to nothing new.
- An accepted ADR is never edited to change direction. A new ADR supersedes it once accepted.
- ADR IDs are never reused and ADR files are never deleted.
- Downstream requirements, features and tasks respect accepted ADRs. A contradiction is an ARCHITECTURE CONFLICT, recorded in the architecture review and resolved by changing the proposal, adding an ADR or superseding one.
- An open architecture choice that matters is ARCHITECTURE DECISION REQUIRED, with a question and an owner — never an invented answer.
- Before changing an ADR, record the change (`changes/CHANGE-###.md`) and run `python tools/analyze_change_impact.py projects/<project> CHANGE-###`.
