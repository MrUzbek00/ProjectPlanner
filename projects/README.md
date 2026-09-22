# Per-project Records

Create one folder per actual business project after receiving its initial idea or materials. This directory intentionally contains no fictional business project.

```text
projects/<project-folder>/
  project-state.md
  sources/                         # Originals or source-location references
  discovery/
    discovery.md                   # Understanding, gaps, current interview
    registers.md                   # Sources, requirements, decisions, glossary
    rounds/round-01.md              # Dated question/answer history
  models/process-model.md          # Processes, permissions, states, relationships
  specification/
    technical-specification.md     # Central 26-section specification
    requirements/<FR-ID>.md        # Detailed records when needed
    pages/<PAGE-ID>.md             # Detailed page/form/table/action records
    diagrams/                     # Actual confirmed Mermaid models, if useful
  backlog/                         # Create after specification approval
    hierarchy.md
    cards/<CARD-ID>.md
    roadmap.md
  quality/
    traceability.md
    acceptance-tests.md
    specification-quality-report.md
  deliverables/                    # Create after the analysis records are complete
    prd.md
    brd.md
    srs.md
    sow.md
    user-journey-stories.md
    wireframes-uiux.md
    project-plan-roadmap.md
    package-manifest.md
    diagrams/                      # .excalidraw and .drawio sources plus rendered PNG/SVG
    build/                         # Generated .docx and .xlsx; output, not source
  delivery/handoff.md
  baselines/<approved-version>/    # Snapshot of files covered by approval
```

Copy templates as needed and replace placeholders with sourced content. Do not fill every directory with blank files just to resemble completion. Keep draft and approved revisions distinguishable; include normative linked files in the approval manifest.

`deliverables/` holds the seven stakeholder documents and the package manifest, authored from `templates/16` through `templates/23` once the analysis records are complete. Build the Word and Excel files with `python tools/build_deliverables.py projects/<project-folder>/deliverables`. Everything under `build/` is regenerated output: change the Markdown and rebuild rather than editing an export.

`deliverables/diagrams/` holds the BPMN process diagrams generated with the Excalidraw skill and the proposed data model and state diagrams generated with the draw.io skill, specified in `templates/24` and `templates/25`. Keep both the editable source and the rendered export; the deliverable Markdown embeds the export with a captioned image reference.

The specification is the canonical approved requirement set. Registers provide provenance and decision history. Cards reference the approved specification rather than introducing competing definitions. The traceability matrix and roadmap index links across artifacts; update them when IDs, scope or dependencies change.

To resume: read `project-state.md`, the latest round, `discovery/registers.md`, the specification approval record and the quality report. Continue the next unresolved gate. A copied template remains a template until populated and reviewed.
