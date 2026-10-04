"""Read-only view of planning projects.

Everything comes from tools/check_gates.evaluate(), which builds the gate
results and the complete machine-handoff documents in memory from the current
Markdown records. The CLIs that write reports are never called, so viewing a
project changes nothing on disk. Results are cached per project and keyed on the
source fingerprint, so an edited record shows on the next page load.
"""

from __future__ import annotations

import json
import re
import threading
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import SAMPLE_PROJECT
import check_gates as cg  # noqa: E402
import planning_records as pr  # noqa: E402
import validate_handoff as vh  # noqa: E402

RESULT_CLASS = {cg.PASS: "pass", cg.WARN: "warn", cg.FAIL: "fail"}


# --------------------------------------------------------------------------
# Project discovery
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Project:
    slug: str
    path: Path
    label: str


class Registry:
    """The projects the UI may show. A URL names a slug, never a path."""

    def __init__(self, projects_dir: Path | None, extra: list[Path] | None = None, sample: bool = False):
        self.projects_dir = projects_dir
        self.extra = [Path(p).resolve() for p in extra or []]
        if sample:
            self.extra.append(SAMPLE_PROJECT.resolve())
        self._cache: dict[str, tuple[str, ProjectView | ProjectError]] = {}
        self._lock = threading.Lock()

    def projects(self) -> list[Project]:
        paths: list[Path] = []
        if self.projects_dir and self.projects_dir.is_dir():
            paths += sorted(p for p in self.projects_dir.iterdir() if (p / pr.STATE_FILE).is_file())
        paths += [p for p in self.extra if (p / pr.STATE_FILE).is_file()]
        out: list[Project] = []
        used: set[str] = set()
        for path in dict.fromkeys(p.resolve() for p in paths):
            base = re.sub(r"[^a-z0-9]+", "-", path.name.lower()).strip("-") or "project"
            slug, n = base, 2
            while slug in used:
                slug, n = f"{base}-{n}", n + 1
            used.add(slug)
            out.append(Project(slug, path, path.name))
        return out

    def get(self, slug: str) -> Project | None:
        return next((p for p in self.projects() if p.slug == slug), None)

    def load(self, project: Project) -> ProjectView | ProjectError:
        fingerprint = pr.fingerprint(project.path)
        with self._lock:
            cached = self._cache.get(project.slug)
            if cached and cached[0] == fingerprint:
                return cached[1]
        view = build_view(project, fingerprint)
        with self._lock:
            self._cache[project.slug] = (fingerprint, view)
        return view

    def forget(self, slug: str) -> None:
        with self._lock:
            self._cache.pop(slug, None)


# --------------------------------------------------------------------------
# View models
# --------------------------------------------------------------------------


@dataclass
class ProjectError:
    project: Project
    message: str
    detail: str


@dataclass
class GateRow:
    gate: str
    name: str
    stage: str
    label: str
    number: int
    result: str
    css: str
    due: bool
    claimed: str | None
    issues: list[cg.Issue]


@dataclass
class StageStep:
    label: str
    number: int
    name: str
    gates: list[GateRow]
    state: str  # done | warn | fail | current | future


@dataclass
class ProjectView:
    project: Project
    fingerprint: str
    state: dict[str, str]
    current_stage: int | None
    gates: list[GateRow]
    steps: list[StageStep]
    violations: list[cg.Issue]
    review_summary: dict[str, str]
    docs: dict[str, Any]
    handoff: dict[str, Any]
    index: dict[str, str] = field(default_factory=dict)  # ID -> kind

    # convenience ------------------------------------------------------------
    def doc(self, name: str) -> dict[str, Any]:
        value = self.docs.get(name)
        return value if isinstance(value, dict) else {}

    @property
    def name(self) -> str:
        return self.doc("project.json").get("name") or self.state.get("project name") or self.project.label

    @property
    def project_id(self) -> str:
        return self.doc("project.json").get("project_id") or "—"

    @property
    def gate_tally(self) -> dict[str, int]:
        due = [g for g in self.gates if g.due]
        return {"pass": sum(g.css == "pass" for g in due), "warn": sum(g.css == "warn" for g in due),
                "fail": sum(g.css == "fail" for g in due), "notdue": sum(not g.due for g in self.gates)}

    @property
    def requirements(self) -> list[dict]:
        return self.doc("requirements.json").get("requirements", [])

    @property
    def adrs(self) -> list[dict]:
        return self.doc("architecture.json").get("decisions", [])

    @property
    def tasks(self) -> list[dict]:
        order = {t["id"]: (t.get("sequence") or 10**6) for t in self.doc("backlog.json").get("tasks", [])}
        tasks = [doc for name, doc in self.docs.items() if name.startswith("tasks/") and isinstance(doc, dict)]
        return sorted(tasks, key=lambda t: (order.get(t.get("id"), 10**6), pr.natural_key(t.get("id", ""))))

    def find(self, items: list[dict], identifier: str) -> dict | None:
        return next((item for item in items if item.get("id") == identifier), None)

    def requirement(self, rid: str) -> dict | None:
        return self.find(self.requirements, rid)

    def adr(self, aid: str) -> dict | None:
        return self.find(self.adrs, aid)

    def task(self, tid: str) -> dict | None:
        return self.find(self.tasks, tid)

    def feature(self, fid: str) -> dict | None:
        return self.find(self.doc("backlog.json").get("features", []), fid)

    def test(self, test_id: str) -> dict | None:
        return self.find(self.doc("tests.json").get("tests", []), test_id)

    def trace_for(self, rid: str) -> dict:
        return next((r for r in self.doc("traceability.json").get("requirements", [])
                     if r.get("requirement_id") == rid), {})

    def adr_reach(self, aid: str) -> dict:
        return next((r for r in self.doc("traceability.json").get("architecture", [])
                     if r.get("adr_id") == aid), {})

    def task_readiness(self, tid: str) -> dict:
        return next((t for t in self.doc("backlog-readiness.json").get("tasks", []) if t.get("id") == tid), {})

    def title_of(self, identifier: str) -> str:
        for item in (self.requirement(identifier), self.adr(identifier), self.task(identifier),
                     self.feature(identifier), self.test(identifier)):
            if item:
                return item.get("title") or ""
        return ""


def build_view(project: Project, fingerprint: str) -> ProjectView | ProjectError:
    try:
        results, violations, ctx = cg.evaluate(project.path)
    except vh.SchemaUnavailable as exc:
        return ProjectError(project, "The jsonschema package is required to evaluate projects.", str(exc))
    except Exception as exc:  # a broken record must show as a panel, not a server error
        return ProjectError(project, f"{type(exc).__name__}: {exc}", traceback.format_exc(limit=6))

    current = ctx.current_stage
    gates = []
    for r in results:
        due = r.number == 0 or current is None or r.number <= current
        claim = ctx.claims.get(r.gate)
        gates.append(GateRow(
            gate=r.gate, name=r.name, stage=r.stage,
            label="Continuous" if r.number == 0 else cg.STAGE_LABEL.get(r.gate, str(r.number)),
            number=r.number, result=r.result if due else "NOT YET DUE",
            css=RESULT_CLASS[r.result] if due else "notdue", due=due,
            claimed=claim[0] if claim else None, issues=list(r.issues),
        ))

    steps = []
    for number in range(1, cg.LAST_STAGE + 1):
        stage_gates = [g for g in gates if g.number == number]
        name = " / ".join(g.stage for g in stage_gates)
        label = " · ".join(dict.fromkeys(g.label for g in stage_gates))
        if current is not None and number > current:
            state = "future"
        elif any(g.css == "fail" for g in stage_gates):
            state = "fail"
        elif current == number:
            state = "current"
        elif any(g.css == "warn" for g in stage_gates):
            state = "warn"
        else:
            state = "done"
        steps.append(StageStep(label, number, name, stage_gates, state))

    view = ProjectView(
        project=project, fingerprint=fingerprint, state=dict(ctx.state), current_stage=current,
        gates=gates, steps=steps, violations=list(violations),
        review_summary={k: v[0] for k, v in (ctx.review_summary or {}).items()},
        docs=ctx.docs, handoff=disk_handoff(project.path, fingerprint),
    )
    view.index = id_index(view)
    return view


def id_index(view: ProjectView) -> dict[str, str]:
    """Which page each linkable ID belongs to."""
    index: dict[str, str] = {}
    for item in view.requirements:
        index[item["id"]] = "requirement"
    for item in view.adrs:
        index[item["id"]] = "adr"
    for item in view.tasks:
        index[item["id"]] = "task"
    return index


def _read_json(path: Path) -> dict | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def disk_handoff(project: Path, fingerprint: str) -> dict[str, Any]:
    """What the generated machine handoff on disk says, and whether it is stale."""
    folder = project / "machine-handoff"
    project_json = _read_json(folder / "project.json")
    manifest = _read_json(folder / "handoff-manifest.json")
    report = _read_json(folder / "validation-report.json")
    stale = bool(project_json) and project_json.get("source_fingerprint") != fingerprint
    return {
        "exists": folder.is_dir() and project_json is not None,
        "manifest": manifest,
        "report": report,
        "project": project_json,
        "stale": stale,
        "generated_at": (manifest or project_json or {}).get("generated_at"),
    }
