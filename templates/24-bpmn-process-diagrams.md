# BPMN Process Diagrams

TEMPLATE — diagram specifications and generation record — NOT APPROVED

Business process diagrams are drawn in BPMN notation with the Excalidraw diagram skill ([coleam00/excalidraw-diagram-skill](https://github.com/coleam00/excalidraw-diagram-skill)), one diagram per confirmed process. This record is the contract the diagram is drawn from: it fixes the participants, the flow and the notation before any shape is placed.

A diagram is a view of the confirmed process model in `specification/process-model.md`. It shows what that model states and nothing else. A lane, gateway, message flow or end event that appears in a diagram and not in the model is an invented requirement — remove it or raise it through the model first.

## 1. Notation Conformance Statement

State this in every exported diagram's caption and in the deliverable that embeds it:

> Drawn in BPMN 2.0 notation. This is a notation-conformant process drawing, not a BPMN 2.0 XML interchange file, and it is not executable in a BPMN engine.

The Excalidraw skill produces `.excalidraw` JSON and a rendered PNG. It does not produce BPMN 2.0 XML. Where an executable or interchangeable BPMN file is genuinely required, record that as a separate confirmed requirement with an owner and a tool decision; do not imply this artifact satisfies it.

## 2. Diagram Inventory

| DIAG ID | Process (PROC-###) | Diagram title | Perspective (AS-IS / TO-BE) | Participants | Source records | `.excalidraw` file in `diagrams/source/` | Rendered PNG in `diagrams/exported/` | Embedded in | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

Draw AS-IS and TO-BE as separate diagrams. Do not overlay a proposed change onto an observed process; the difference between them is the argument the pair has to make.

## 3. BPMN Element Vocabulary

Use only these elements, and only where the process model confirms them. The Excalidraw skill carries no BPMN notation rules of its own, so this table is the notation contract.

| BPMN element | Meaning | Excalidraw rendering | Use only when |
| --- | --- | --- | --- |
| Pool | An independent participant or organization | Outer rectangle, labelled on the left edge, containing its lanes | Two or more participants exchange messages |
| Lane | A role or department inside a pool | Horizontal band inside the pool, labelled on the left | The model assigns steps to distinct roles |
| Start event | What begins the process | Thin-stroke circle | The model states a confirmed trigger |
| Message start event | Started by an incoming message | Thin-stroke circle with an envelope glyph | The trigger is an inbound message or integration |
| Timer start event | Started by a schedule or elapsed time | Thin-stroke circle with a clock glyph | The model confirms a schedule |
| Task | A unit of work performed by a lane | Rounded rectangle, verb-first label | The model lists a discrete step |
| User task | Work a person performs in the system | Rounded rectangle with a person glyph | A confirmed role acts through a screen |
| Service task | Work the system performs unattended | Rounded rectangle with a gear glyph | The model confirms automated behavior |
| Send / receive task | An exchange with another participant | Rounded rectangle with an envelope glyph | A confirmed integration or notification |
| Exclusive gateway | Exactly one outgoing path is taken | Diamond with an X | The model states mutually exclusive conditions |
| Parallel gateway | All outgoing paths are taken | Diamond with a plus | The model confirms concurrent work |
| Inclusive gateway | One or more paths are taken | Diamond with a circle | The model confirms condition-dependent multiples |
| Sequence flow | Order of work inside one pool | Solid arrow, labelled with the condition on gateway outputs | Always, between steps in the same pool |
| Message flow | Communication between pools | Dashed arrow with an open arrowhead | Always, between separate pools — never inside one |
| Data object | A document or record consumed or produced | Rectangle with a folded corner | The model names the document or entity |
| Data store | Persisted data | Cylinder | The model confirms a system of record |
| Intermediate event | Something that happens mid-flow | Double-stroke circle | The model confirms a wait, message or timer |
| Boundary error event | An interruption attached to a task | Double-stroke circle on the task border | The model confirms a failure path |
| End event | A terminal outcome | Thick-stroke circle | Every distinct outcome, including rejection |
| Terminate end event | Ends the whole process instance | Thick-stroke circle with a filled circle | The model confirms hard termination |
| Annotation | A clarifying note | Open bracket with text, dotted connector | Explaining an open question or a boundary |

Rules that hold in every diagram:

- Every gateway that splits is labelled with the question it asks, and every outgoing flow is labelled with its condition.
- Every path reaches an end event. A dangling flow is a modeling defect, not a drawing shortcut.
- Rejection, cancellation and failure paths are drawn wherever the model confirms them, and omitted wherever it does not.
- A message flow never appears inside a single pool; a sequence flow never crosses a pool boundary.
- Unknown behavior is drawn as an annotation naming the open question, outside the confirmed flow — never as a guessed gateway.

## 4. Diagram Specification

Repeat this record for every diagram in the inventory. Complete it before generating the diagram.

### DIAG ID: TBD — TBD

- **Process:** TBD (PROC-###)
- **Perspective:** AS-IS / TO-BE
- **Source records:** TBD
- **Purpose of this diagram:** TBD — the one thing a reader should understand from it
- **Trigger:** TBD
- **Successful outcome:** TBD
- **Other terminal outcomes:** TBD
- **Scope boundary:** TBD — what is deliberately outside the frame

**Pools and lanes**

| Pool | Represents | Lanes | ROLE IDs | Source |
| --- | --- | --- | --- | --- |

**Flow elements in order**

| Sequence | Element type | Label | Lane | Inputs / data objects | Outputs / state change | Notes |
| --- | --- | --- | --- | --- | --- | --- |

**Gateways**

| Gateway | Type | Question asked | Outgoing flows and conditions | Default flow | Business rule (RULE-###) | Source |
| --- | --- | --- | --- | --- | --- | --- |

**Message flows**

| From pool | To pool | Message | Trigger | Channel | Related NOTIF / INT | Source |
| --- | --- | --- | --- | --- | --- | --- |

**Data objects and stores**

| Element | Type | Entity (ENT-###) | Read or written | At which step | Source |
| --- | --- | --- | --- | --- | --- |

**End events**

| End event | Outcome | Reached from | State reached (STATE-###) | Notification | Source |
| --- | --- | --- | --- | --- | --- |

**Deliberately not drawn**

| Behavior | Why it is not in this diagram | Where it is covered instead |
| --- | --- | --- |

**Open questions shown as annotations:** TBD (Q-###)

## 5. Generation Record

| DIAG ID | Skill invoked | Source file | Render command | Render iterations | Reviewed by | Date | Result |
| --- | --- | --- | --- | --- | --- | --- | --- |

The Excalidraw skill requires a render-view-fix loop: render the `.excalidraw` file to PNG, look at the PNG, fix defects, and repeat until the drawing is clean. Record how many iterations were actually run. A diagram that was generated but never rendered and viewed is unverified.

```bash
# from the skill's references directory
uv run python render_excalidraw.py <path-to-diagram.excalidraw>
```

## 6. Verification

| Check | Result | Evidence | Findings |
| --- | --- | --- | --- |
| Every confirmed process in the model has a diagram, or a recorded reason it needs none | TBD | TBD | TBD |
| Every element in the diagram traces to a confirmed record | TBD | TBD | TBD |
| No lane, gateway, message flow or end event was invented for the drawing | TBD | TBD | TBD |
| AS-IS and TO-BE are separate diagrams and are not conflated | TBD | TBD | TBD |
| Every gateway states its question and labels every outgoing condition | TBD | TBD | TBD |
| Every path terminates in an end event | TBD | TBD | TBD |
| Rejection, cancellation and failure paths match the confirmed state transitions | TBD | TBD | TBD |
| Message flows cross pools only; sequence flows stay within a pool | TBD | TBD | TBD |
| Lane names match confirmed ROLE IDs exactly | TBD | TBD | TBD |
| Data objects match confirmed ENT IDs exactly | TBD | TBD | TBD |
| Open questions appear as annotations, not as guessed behavior | TBD | TBD | TBD |
| The PNG was rendered and visually inspected, not just generated | TBD | TBD | TBD |
| No text is clipped, overlapping or unreadable at delivered size | TBD | TBD | TBD |
| The notation conformance statement appears in the caption | TBD | TBD | TBD |
| The diagram matches the current approved revision of the process model | TBD | TBD | TBD |

## 7. Embedding

Reference each rendered diagram from the deliverable that carries it, using a relative path from the deliverable Markdown file:

```markdown
![DIAG-001 — Purchase approval, TO-BE. Drawn in BPMN 2.0 notation; not a BPMN 2.0 XML interchange file.](../diagrams/exported/diag-001-purchase-approval-tobe.png)
```

The build tool embeds the PNG and renders the caption beneath it. Keep the DIAG ID first in the caption so a reader can find the specification behind the picture.

## 8. Open Questions

| Q ID | Question | Affected diagram | Why it matters | Owner | Status | Answer |
| --- | --- | --- | --- | --- | --- | --- |
