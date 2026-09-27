# Project State

TEST FIXTURE — a deliberately small, fictional project used by `tools/tests/` to exercise the workflow's gates and the machine handoff. It is not a business project and none of its content is a requirement for any real project.

| Field | Value |
| --- | --- |
| Project ID | SAMPLE |
| Project folder | tools/tests/fixtures/sample-project |
| Project name | Sample Portal |
| Client / department | Fixture |
| Document language | English |
| Current stage | 13 — Final Planning Package |
| Priority scheme | Levels |
| Specification version | 1.0 |
| Specification status | APPROVED |
| Approved baseline version / location | 1.0 / baselines/1.0/ |

## Gate history

| Gate | Status | Evidence | Date | Outstanding conditions |
| --- | --- | --- | --- | --- |
| G1 — Intake complete | PASS | reports/gate-report.md | 2026-09-02 | |
| G2 — Discovery ready | PASS WITH WARNINGS | reports/gate-report.md | 2026-09-10 | Security partially understood (Q-002, quarantined) |
| G3 — Requirements ready | PASS | reports/gate-report.md | 2026-09-14 | |
| G4 — Models ready | PASS | reports/gate-report.md | 2026-09-15 | |
| G5 — Solution and scope ready | PASS | reports/gate-report.md | 2026-09-16 | |
| G6 — Architecture ready | PASS | reports/gate-report.md, reports/architecture-report.md | 2026-09-16 | |
| G7 — Specification complete | PASS | reports/gate-report.md | 2026-09-18 | |
| GR — Specification reviewed | PASS WITH WARNINGS | reports/gate-report.md | 2026-09-19 | REVIEW-002 observation open |
| G8 — Specification ready | PASS WITH WARNINGS | reports/gate-report.md | 2026-09-20 | ASM-001 open, scoped out with FR-AUTH-003 |
| G9 — Backlog decomposed | PASS | reports/gate-report.md | 2026-09-22 | |
| G10 — Sequencing ready | PASS | reports/gate-report.md | 2026-09-23 | |
| GB — Backlog ready | PASS | reports/gate-report.md, backlog/readiness-report.md | 2026-09-23 | TASK-004 is outside the release (PENDING DECISION) |
| G11 — Roadmap ready | PASS | reports/gate-report.md | 2026-09-24 | |
| G12 — Planning validated | PASS WITH WARNINGS | reports/gate-report.md | 2026-09-25 | Q-003 and Q-004 open, non-blocking |
| G13 — Planning package ready | IN PROGRESS | | | Deliverables not yet authored |

## Specification review

| Review measure | Value |
| --- | --- |
| Specification review | PASS WITH WARNINGS |
| Last review cycle | 2 |
| Open critical | 0 |
| Open major | 0 |
| Open minor | 0 |
| Open observations | 1 |
| Accepted risks | 0 |

## Approval record

| Approval ID | Approver / authority | Exact statement or attributable reference | Date | Specification version | Manifest / baseline path | Conditions / exclusions |
| --- | --- | --- | --- | --- | --- | --- |
| APR-001 | Fixture owner | "I approve specification version 1.0." | 2026-09-20 | 1.0 | baselines/1.0/ | FR-AUTH-003 lockout remains PENDING DECISION until Q-002 is answered |
