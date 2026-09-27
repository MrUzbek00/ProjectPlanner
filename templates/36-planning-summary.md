<!-- doc-meta
title: Project Planning Summary
subtitle: What we are building, why, what comes first, and what is still unknown
project: TBD
version: TBD
date: TBD
status: DRAFT
-->

# Project Planning Summary

TEMPLATE — stage 13. Copy to `deliverables/planning-summary.md` once gate G12 has passed. It answers the fifteen questions every planning package must answer, in plain language, and points to the records that hold the detail. It restates; it adds nothing. Every ID it cites must exist, and every unknown is named as unknown with its Q-###.

Keep the fifteen headings exactly; `tools/check_gates.py` checks for gate G13 that each one is present and answered.

## What problem are we solving?

The business problem and the goal, citing GOAL-### and BR-###.

## Who are we solving it for?

Target users and stakeholders, citing roles.

## What is in scope?

The IN SCOPE items of the scope register, citing SCOPE-### and features.

## What is not in scope?

OUT OF SCOPE and FUTURE items with their rationale, and PENDING DECISION items with the question that decides them.

## What should the system do?

The in-scope requirements, grouped by module, citing IDs.

## What constraints must it respect?

Non-functional, security, data, integration and technical requirements, accepted ADRs and confirmed constraints.

## What are the major workflows?

The TO-BE processes (PROC-###), and how each differs from today.

## What are the major modules/features?

Modules (MOD-###) and features (FEAT-###).

## What requirements support each feature?

Feature → requirement mapping. Cite `traceability/requirement-map.md` for the full chains.

## What work needs to happen?

Epics, features and tasks, with counts by status. READY tasks are the ones that can be handed on.

## What depends on what?

Feature and task dependencies, external dependencies (DEP-###) and decisions still pending. Cite `reports/dependency-graph.md`.

## What should happen first?

The first roadmap phase and the tasks executable now, in dependency order.

## What risks exist?

The open risks with probability, impact, mitigation and owner (RISK-###).

## What is still unknown?

Every open question (Q-###) with its priority and owner, and every open assumption (ASM-###). Say plainly what is unresolved.

## What decisions were made?

The decision log (DEC-###) and accepted ADRs, with dates and who approved them.
