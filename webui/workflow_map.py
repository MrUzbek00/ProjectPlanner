"""The workflow map: the method's stages drawn as a pipeline, coloured by a project's gates.

The layout is computed here, not in the browser: every node has a fixed position
in a five-lane grid, and every edge is an SVG cubic Bézier between node anchors,
with the exit gate of its source stage drawn on it. Stage names and purposes
come from method.stages() (WORKFLOW.md); statuses come from the project's gate
results (check_gates.evaluate). Without a project the map shows the method only.
"""

from __future__ import annotations

from dataclasses import dataclass

from . import method
from .data import GateRow, ProjectView

CARD_W, CARD_H = 250, 112
LANE_W, ROW_H = 300, 150
LEFT, TOP = 30, 70

# Lane, row and short title of every stage, keyed by stage label.
LANES = [
    ("discover", "Discover", "#8b7cf6"),
    ("analyse", "Analyse", "#f0b429"),
    ("decide", "Decide & specify", "#f97316"),
    ("plan", "Plan the work", "#ff4d6d"),
    ("deliver", "Validate & deliver", "#2dd4bf"),
]
PLACEMENT = {
    "1": (0, 0), "2": (0, 1),
    "3": (1, 0), "4": (1, 1), "5": (1, 2),
    "6": (2, 0), "7": (2, 1), "8A": (2, 2), "8B": (2, 3),
    "9": (3, 0), "10A": (3, 1), "10B": (3, 2), "11": (3, 3),
    "12": (4, 0), "13": (4, 1),
}
TERMINAL_ROW = 2
# Card titles that would not fit on one line; the full name stays in the tooltip.
SHORT_NAMES = {"8B": "Resolution and Approval", "10A": "Dependencies and Priorities",
               "10B": "Backlog Readiness", "8A": "Independent Review"}
STATUS_TEXT = {"pass": "passed", "warn": "warnings", "fail": "failing", "notdue": "not yet due"}


@dataclass
class Node:
    label: str
    name: str
    short: str
    purpose: str
    gate: str
    gate_name: str
    lane: int
    x: int
    y: int
    color: str
    href: str
    status: str | None = None        # pass | warn | fail | notdue
    current: bool = False
    issues: int = 0
    templates: int = 0


@dataclass
class Edge:
    path: str
    color: str
    gate: str | None = None
    gate_status: str | None = None
    mx: float = 0
    my: float = 0
    label_dx: int = 0
    dashed: bool = False
    # Animation: whether work is shown flowing along this edge, and its timing in seconds.
    flow: bool = True
    duration: float = 1.6
    delay: float = 0.0


@dataclass
class Map:
    nodes: list[Node]
    edges: list[Edge]
    lanes: list[dict]
    terminal: dict
    width: int
    height: int
    loop_caption: dict
    change_gate: GateRow | None = None


def _bezier_mid(p0, p1, p2, p3) -> tuple[float, float]:
    return tuple(0.125 * a + 0.375 * b + 0.375 * c + 0.125 * d for a, b, c, d in zip(p0, p1, p2, p3))


def _travel_time(p0, p3, curved: bool) -> float:
    """Seconds for a particle to cross an edge at a steady ~110 px/s, never faster than 0.9 s."""
    length = ((p3[0] - p0[0]) ** 2 + (p3[1] - p0[1]) ** 2) ** 0.5 * (1.25 if curved else 1.0)
    return round(max(0.9, length / 110), 2)


def _curve(p0, p3, bend: int = 60) -> tuple[str, tuple[float, float]]:
    p1 = (p0[0] + bend, p0[1])
    p2 = (p3[0] - bend, p3[1])
    path = f"M {p0[0]} {p0[1]} C {p1[0]} {p1[1]}, {p2[0]} {p2[1]}, {p3[0]} {p3[1]}"
    return path, _bezier_mid(p0, p1, p2, p3)


def build(view: ProjectView | None, stage_href, project_href=None) -> Map:
    stages, _ = method.stages()
    gates = {g.gate: g for g in view.gates} if view else {}
    nodes: list[Node] = []
    for stage in stages:
        lane, row = PLACEMENT.get(stage.label, (4, 3))
        gate = gates.get(stage.gate)
        nodes.append(Node(
            label=stage.label, name=stage.name, short=SHORT_NAMES.get(stage.label, stage.name),
            purpose=stage.purpose, gate=stage.gate,
            gate_name=stage.gate_name, lane=lane, x=LEFT + lane * LANE_W, y=TOP + row * ROW_H,
            color=LANES[lane][2],
            href=project_href(stage.gate) if view and project_href else stage_href(stage.number),
            status=gate.css if gate else None,
            current=bool(view and view.current_stage == stage.number),
            issues=len(gate.issues) if gate and gate.due else 0, templates=len(stage.templates),
        ))

    edges: list[Edge] = []
    for index, (source, target) in enumerate(zip(nodes, nodes[1:])):
        gate = gates.get(source.gate)
        if source.lane == target.lane:
            x = source.x + CARD_W / 2
            p0, p3 = (x, source.y + CARD_H), (x, target.y)
            edge = Edge(f"M {p0[0]} {p0[1]} L {p3[0]} {p3[1]}", source.color,
                        mx=x, my=(p0[1] + p3[1]) / 2, label_dx=18)
            edge.duration = _travel_time(p0, p3, curved=False)
        else:
            p0, p3 = (source.x + CARD_W, source.y + CARD_H / 2), (target.x, target.y + CARD_H / 2)
            path, (mx, my) = _curve(p0, p3)
            edge = Edge(path, source.color, mx=mx, my=my, label_dx=18)
            edge.duration = _travel_time(p0, p3, curved=True)
        edge.gate, edge.gate_status = source.gate, gate.css if gate else None
        # Work flows along the path a project has already travelled; the method alone flows everywhere.
        edge.flow = view is None or target.current or target.status not in (None, "notdue")
        edge.delay = round(index * 0.3, 2)
        edges.append(edge)

    # The last stage hands off to engineering; its gate sits on that edge.
    last = nodes[-1]
    tx, ty = LEFT + 4 * LANE_W, TOP + TERMINAL_ROW * ROW_H + 20
    gate = gates.get(last.gate)
    p0, p3 = (last.x + CARD_W / 2, last.y + CARD_H), (tx + CARD_W / 2, ty)
    edges.append(Edge(f"M {p0[0]} {p0[1]} L {p3[0]} {p3[1]}", last.color,
                      gate=last.gate, gate_status=gate.css if gate else None,
                      mx=p0[0], my=(p0[1] + p3[1]) / 2, label_dx=18,
                      # Nothing reaches engineering until the final gate passes.
                      flow=view is None or bool(gate and gate.css in ("pass", "warn")),
                      duration=_travel_time(p0, p3, curved=False), delay=round(len(nodes) * 0.3, 2)))

    # Review loop: specification findings go back to the stage that owns them (3-7), then are re-reviewed.
    by_label = {n.label: n for n in nodes}
    loop_caption = {}
    if "8B" in by_label and "5" in by_label:
        start, end = by_label["8B"], by_label["5"]
        p0 = (start.x, start.y + CARD_H / 2)
        p3 = (end.x + CARD_W / 2, end.y + CARD_H)
        path = f"M {p0[0]} {p0[1]} C {p0[0] - 90} {p0[1]}, {p3[0]} {p3[1] + 100}, {p3[0]} {p3[1]}"
        edges.append(Edge(path, LANES[2][2], dashed=True, duration=3.2, delay=1.5))
        loop_caption = {"x": end.x, "y": start.y + CARD_H + 22, "w": start.x + CARD_W - end.x,
                        "text": "Review loop · findings resolved in stages 3–7 · re-reviewed before approval"}

    height = TOP + 4 * ROW_H + 50
    width = LEFT + 5 * LANE_W
    lanes = [{"key": k, "title": t, "color": c, "x": LEFT + i * LANE_W - 25, "w": LANE_W}
             for i, (k, t, c) in enumerate(LANES)]
    terminal = {"x": tx, "y": ty, "w": CARD_W,
                "text": "Machine handoff → engineering (SoftwareFactory)",
                "status": (view.handoff.get("manifest") or {}).get("handoff_status") if view else None}
    return Map(nodes, edges, lanes, terminal, width, height, loop_caption,
               change_gate=gates.get("GC"))
