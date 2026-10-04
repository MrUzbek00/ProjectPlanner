"""Tests for the read-only web UI.

Run from the repository root:
    python -m unittest discover -s webui/tests -v

Each test copies the fixture project to a temporary folder and serves it with
Flask's test client. The central promise is checked directly: visiting every
page leaves every byte of the project unchanged.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

try:
    import flask  # noqa: F401
    import markdown  # noqa: F401
except ImportError:  # pragma: no cover - environment dependent
    flask = None

FIXTURE = ROOT / "tools" / "tests" / "fixtures" / "sample-project"


def snapshot(folder: Path) -> dict[str, bytes]:
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


@unittest.skipIf(flask is None, "Flask and Markdown are needed: python -m pip install -r webui/requirements.txt")
class WebUI(unittest.TestCase):
    def setUp(self) -> None:
        from webui.app import create_app
        from webui.data import Registry

        self._tmp = tempfile.TemporaryDirectory()
        self.projects = Path(self._tmp.name) / "projects"
        self.project = self.projects / "sample-project"
        shutil.copytree(FIXTURE, self.project)
        self.registry = Registry(self.projects)
        self.client = create_app(self.registry).test_client()
        self.base = "/projects/sample-project"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def get(self, url: str, status: int = 200) -> str:
        response = self.client.get(url)
        self.assertEqual(status, response.status_code, url)
        return response.get_data(as_text=True)

    def edit(self, rel: str, old: str, new: str) -> None:
        path = self.project / rel
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    # pages -------------------------------------------------------------------

    def test_home_lists_the_project(self):
        html = self.get("/")
        self.assertIn("Sample Portal", html)
        self.assertIn(f'href="{self.base}"', html)

    def test_home_draws_the_workflow_map_with_gate_status(self):
        html = self.get("/")
        self.assertIn("Workflow <span>Map</span>", html)
        for gate in ("G1", "G5", "GR", "G8", "G10", "GB", "G13"):
            self.assertIn(f'href="{self.base}#gate-{gate}"', html)
        self.assertIn("wm-card st-fail current", html)  # G13 fails and stage 13 is current on the fixture
        self.assertIn('class="wm-gate pass"', html)
        self.assertIn("Review loop", html)

    def test_work_flows_only_along_the_path_already_travelled(self):
        from webui import workflow_map

        view = self.registry.load(self.registry.get("sample-project"))
        wmap = workflow_map.build(view, stage_href=str, project_href=str)
        handoff = wmap.edges[len(wmap.nodes) - 1]  # the edge from the last stage to engineering
        self.assertFalse(handoff.flow, "nothing reaches engineering while G13 fails")
        self.assertTrue(all(e.flow for e in wmap.edges[: len(wmap.nodes) - 1]))
        html = self.get("/")
        self.assertIn("<animateMotion", html)
        self.assertIn("wm-edge idle", html)

    def test_map_without_a_project_shows_the_method(self):
        html = self.get("/?project=none")
        self.assertIn("No project selected", html)
        self.assertIn('href="/method/stages/6"', html)
        self.assertNotIn("wm-card st-pass", html)

    def test_empty_projects_folder_explains_how_to_start(self):
        from webui.app import create_app
        from webui.data import Registry

        empty = Path(self._tmp.name) / "empty"
        empty.mkdir()
        html = create_app(Registry(empty)).test_client().get("/").get_data(as_text=True)
        self.assertIn("No projects yet", html)
        self.assertIn("--sample", html)

    def test_method_guide_shows_every_stage_and_gate(self):
        html = self.get("/method")
        for gate in ("G1", "G2", "G6", "GR", "G8", "G9", "G10", "GB", "G12", "G13", "GC"):
            self.assertIn(f"<strong>{gate}</strong>", html)
        self.assertIn("Independent Specification Review", html)
        self.assertIn("08-development-card.md", html)
        stage = self.get("/method/stages/6")
        self.assertIn("Architecture Governance", stage)
        self.assertIn("<table>", self.get("/method/templates/28-architecture-decision-record.md"))

    def test_overview_shows_gates_as_check_gates_reports_them(self):
        sys.path.insert(0, str(ROOT / "tools"))
        import check_gates as cg

        results, _, _ = cg.evaluate(self.project)
        html = self.get(self.base)
        for result in results:
            self.assertIn(f'<span class="gid">{result.gate}</span>', html)
        self.assertIn("Final Planning Package", html)
        self.assertIn('class="gate fail"', html)  # G13 fails on the fixture

    def test_record_pages_show_their_records(self):
        self.assertIn("FR-AUTH-001", self.get(f"{self.base}/requirements"))
        requirement = self.get(f"{self.base}/requirements/FR-AUTH-001")
        self.assertIn("Request a password reset", requirement)
        self.assertIn(f'href="{self.base}/tasks/TASK-002"', requirement)
        self.assertIn("Send reset emails through the existing notification service",
                      self.get(f"{self.base}/architecture/ADR-001"))
        task = self.get(f"{self.base}/tasks/TASK-002")
        self.assertIn("Definition of Ready", task)
        self.assertIn("sha256:", task)
        self.assertIn("Why this task is not READY", self.get(f"{self.base}/tasks/TASK-004"))
        self.assertIn("WS-01", self.get(f"{self.base}/backlog"))

    def test_every_project_tab_renders(self):
        for tab in ("requirements", "architecture", "backlog", "traceability", "review", "changes",
                    "decisions", "handoff"):
            self.assertIn("Re-run checks", self.get(f"{self.base}/{tab}"), tab)
        self.assertIn("REVIEW-001", self.get(f"{self.base}/review"))
        self.assertIn("Q-002", self.get(f"{self.base}/decisions"))
        self.assertIn("READY FOR HANDOFF", self.get(f"{self.base}/handoff"))

    def test_unknown_items_are_404(self):
        self.get("/projects/no-such-project", 404)
        self.get(f"{self.base}/tasks/TASK-999", 404)
        self.get(f"{self.base}/requirements/FR-999", 404)
        self.get(f"{self.base}/architecture/ADR-999", 404)
        self.get("/method/stages/99", 404)
        self.get("/method/templates/..%2FAGENTS.md", 404)

    def test_viewing_every_page_writes_nothing(self):
        before = snapshot(self.project)
        for url in ("/", "/method", self.base, *(f"{self.base}/{tab}" for tab in (
                "requirements", "architecture", "backlog", "traceability", "review", "changes", "decisions",
                "handoff", "requirements/FR-AUTH-001", "architecture/ADR-002", "tasks/TASK-001"))):
            self.get(url)
        self.client.post(f"{self.base}/refresh")
        self.assertEqual(before, snapshot(self.project))

    def test_an_edited_record_shows_on_the_next_load(self):
        self.assertIn("Request a password reset", self.get(f"{self.base}/requirements"))
        self.edit("specification/functional-requirements.md", "Request a password reset",
                  "Ask for a password reset")
        self.assertIn("Ask for a password reset", self.get(f"{self.base}/requirements"))

    def test_handoff_page_reports_a_stale_handoff(self):
        self.edit("specification/functional-requirements.md", "by entering an email address.",
                  "by entering an email address or user name.")
        self.assertIn("Stale.", self.get(f"{self.base}/handoff"))

    def test_refresh_redirects_to_the_overview(self):
        response = self.client.post(f"{self.base}/refresh")
        self.assertEqual(302, response.status_code)
        self.assertTrue(response.headers["Location"].endswith(self.base))
        self.assertEqual(404, self.client.post("/projects/nope/refresh").status_code)

    def test_a_broken_project_shows_an_error_panel_not_a_server_error(self):
        from webui import data

        original = data.cg.evaluate

        def broken(_project):
            raise ValueError("unreadable record block in backlog/tasks/TASK-001.md")

        data.cg.evaluate = broken
        try:
            html = self.get(self.base)
        finally:
            data.cg.evaluate = original
        self.assertIn("This project cannot be evaluated", html)
        self.assertIn("unreadable record block", html)

    def test_record_text_is_escaped(self):
        self.edit("specification/functional-requirements.md", "Request a password reset",
                  "Request a <script>alert(1)</script> reset")
        html = self.get(f"{self.base}/requirements")
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;", html)


if __name__ == "__main__":
    unittest.main()
