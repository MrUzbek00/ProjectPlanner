# Entity-Relationship and Data Workflow Diagrams

TEMPLATE — diagram specifications and generation record — NOT APPROVED

Data and workflow diagrams are drawn with the draw.io diagram skill ([Agents365-ai/drawio-skill](https://github.com/Agents365-ai/drawio-skill)), which writes native `.drawio` files and provides table containers with primary and foreign key notation for ER diagrams and `mxgraph.bpmn.*` shapes for flow diagrams. Output stays editable in draw.io, so the business can correct a model without regenerating it from scratch.

These diagrams visualize the confirmed data model in the technical specification and the confirmed state transitions in the process model. The database design they show is a **proposed physical model** derived from confirmed logical entities. Label it that way: a candidate schema is a recommendation until the business and the implementation team accept it.

## 1. Model Status Statement

State this in every exported data diagram's caption and in the deliverable that embeds it:

> Proposed physical data model derived from the confirmed logical entities in the approved specification. Column types, keys and indexes are design recommendations pending implementation acceptance.

Keep the two layers distinct throughout:

| Layer | Contains | Authority | Where it lives |
| --- | --- | --- | --- |
| Logical model | Entities, attributes, relationships, ownership and lifecycle that the business confirmed | Confirmed requirement | SRS data requirements and the process model |
| Physical model | Tables, column types, keys, indexes, constraints, join tables | Recommendation until accepted | This record and the generated ER diagram |

A table, column, key or index that no confirmed entity or attribute supports is a design proposal and is marked as one. It never enters the diagram as though the business had asked for it.

## 2. Diagram Inventory

| DIAG ID | Diagram title | Type (ER / state / data flow / workflow) | Subject | Source records | `.drawio` file in `diagrams/source/` | Exported PNG or SVG in `diagrams/exported/` | Embedded in | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

## 3. Entity-Relationship Diagram

### 3.1 Table Inventory

<!-- xlsx: workbook=requirements; sheet=Data Model -->

| Table | Derived from entity (ENT-###) | Purpose | Owner role | Row estimate | Lifecycle | Confirmed entity or proposed structure | Source |
| --- | --- | --- | --- | --- | --- | --- | --- |

### 3.2 Columns

Repeat per table. Every column states whether the business confirmed the underlying attribute or whether it is a structural proposal such as a surrogate key, audit column or join column.

<!-- xlsx: workbook=requirements; sheet=Data Dictionary -->

| Table | Column | Type | Length / precision | Key (PK / FK / unique) | Nullable | Default | References | Validation rule | Sensitive | Confirmed attribute or proposed | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

### 3.3 Relationships

| From table | To table | Cardinality | Optionality | Foreign key column | On delete | On update | Business meaning | Confirmed | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Cardinality and optionality come from the confirmed business relationship. Where the model does not state whether a relationship is optional, record `TBD (Q-###)` rather than choosing a constraint that will later be wrong in production.

### 3.4 Indexes and Constraints

| Table | Index or constraint | Columns | Type | Justification | Derived from requirement | Proposed or confirmed |
| --- | --- | --- | --- | --- | --- | --- |

### 3.5 Structural Proposals

Every element on the diagram that the business did not confirm, listed once so a reviewer can see exactly what is being proposed.

| Element | Type (surrogate key, join table, audit column, soft-delete flag, denormalization, index) | Rationale | Alternative considered | Accepted by | Decision reference |
| --- | --- | --- | --- | --- | --- |

### 3.6 Diagram Layout

- **Grouping:** TBD — cluster tables by module (MOD-###) so the picture matches the system's structure
- **Central tables:** TBD — the entities most relationships converge on
- **Reference data placement:** TBD
- **Join tables placement:** TBD
- **Excluded from the diagram:** TBD, with reason — for example audit tables shown as a single annotated group rather than repeated per entity

## 4. State and Workflow Diagrams

One diagram per entity whose lifecycle the model confirms. State names are entity-scoped; the same word can mean different things for different entities, and the diagram must not merge them.

### 4.1 State Diagram Specification

Repeat per entity.

- **DIAG ID:** TBD
- **Entity:** TBD (ENT-###)
- **Initial state:** TBD
- **Terminal states:** TBD
- **Source records:** TBD

| Transition | From state | To state | Actor role | Permission | Guard condition | Side effects | Notification | Audit record | Reversible | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

| State | Meaning | Editable fields | Visible to | Permitted actions | Time limit | Source |
| --- | --- | --- | --- | --- | --- | --- |

Draw only transitions the model confirms. A state with no confirmed way out is drawn as it is, with an annotation naming the open question — not quietly connected to something plausible.

### 4.2 Data Flow Diagrams

| DIAG ID | Flow | Trigger | Source system | Transformation | Destination | Format | Frequency | Failure handling | Related INT | Source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

## 5. Generation Record

| DIAG ID | Skill invoked | Source of truth used | Output file | Export format | Reviewed by | Date | Result |
| --- | --- | --- | --- | --- | --- | --- | --- |

Where a schema already exists, prefer the skill's SQL extractor over hand-written XML so the diagram reflects the real structure rather than an interpretation of it. For a system not yet built, generate from this record and keep the `.drawio` file as the editable source.

Export PNG for embedding in the Word deliverables and keep the `.drawio` file for editing. Exports carry the diagram XML when the draw.io CLI is available, so an exported image remains editable in draw.io.

## 6. Verification

| Check | Result | Evidence | Findings |
| --- | --- | --- | --- |
| Every confirmed entity appears in the ER diagram, or its absence is explained | TBD | TBD | TBD |
| Every table traces to a confirmed entity or is listed as a structural proposal | TBD | TBD | TBD |
| Every column traces to a confirmed attribute or is listed as a structural proposal | TBD | TBD | TBD |
| No relationship, cardinality or constraint was invented to make the model look complete | TBD | TBD | TBD |
| Optionality that the business has not confirmed is marked TBD, not assumed | TBD | TBD | TBD |
| Foreign keys match the confirmed business relationships in direction and meaning | TBD | TBD | TBD |
| Delete behavior matches the confirmed retention and destructive-action decisions | TBD | TBD | TBD |
| Sensitive columns match the confirmed data protection requirements | TBD | TBD | TBD |
| State diagrams match the state transition tables exactly, including rejection and cancellation | TBD | TBD | TBD |
| State names are entity-scoped and not merged across entities | TBD | TBD | TBD |
| Every state is reachable and every non-terminal state has a confirmed exit or an annotated question | TBD | TBD | TBD |
| The exported image was opened and visually inspected | TBD | TBD | TBD |
| No table, label or relationship is clipped or unreadable at delivered size | TBD | TBD | TBD |
| The model status statement appears in the caption | TBD | TBD | TBD |
| The diagram matches the current approved revision of the data model | TBD | TBD | TBD |

## 7. Embedding

Reference each exported diagram from the deliverable that carries it, using a relative path from the deliverable Markdown file:

```markdown
![DIAG-010 — Proposed physical data model. Derived from the confirmed logical entities; types, keys and indexes are design recommendations.](../diagrams/exported/diag-010-er-model.png)
```

The build tool embeds the image and renders the caption beneath it.

## 8. Open Questions

| Q ID | Question | Affected diagram | Why it matters | Owner | Status | Answer |
| --- | --- | --- | --- | --- | --- | --- |
