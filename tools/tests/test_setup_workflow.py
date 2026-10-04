"""Tests for the Excalidraw render-page pin in tools/setup_workflow.py.

Run from the repository root:
    python -m unittest discover -s tools/tests -v

The skill ships `import { exportToSvg } from "https://esm.sh/@excalidraw/excalidraw?bundle";`
with no version, which currently resolves to a build that never loads. Setup pins
that one line in every installed copy and leaves everything else alone.
"""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

import setup_workflow as sw  # noqa: E402

UNPINNED = "https://esm.sh/@excalidraw/excalidraw?bundle"
PAGE = (
    "<!DOCTYPE html>\r\n<html>\r\n<body>\r\n  <script type=\"module\">\r\n"
    f"    import {{ exportToSvg }} from \"{UNPINNED}\";\r\n"
    "    window.__ready = true;\r\n  </script>\r\n</body>\r\n</html>\r\n"
)


class RenderPin(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name) / "skills"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def skill(self, relative: str, page: str = PAGE) -> Path:
        directory = self.root / relative
        (directory / "references").mkdir(parents=True)
        (directory / "SKILL.md").write_text("---\nname: excalidraw-diagram\n---\n", encoding="utf-8")
        (directory / sw.RENDER_TEMPLATE).write_bytes(page.encode("utf-8"))
        return directory

    def pin(self, dirs: list[Path], check_only: bool = False) -> sw.Result:
        return sw.pin_renderer(dirs, check_only, skip=False)

    def test_pin_changes_only_the_import_line(self):
        template = self.skill("excalidraw-diagram") / sw.RENDER_TEMPLATE
        changed, previous = sw.pin_render_template(template)
        after = template.read_bytes().decode("utf-8")
        self.assertTrue(changed)
        self.assertEqual(UNPINNED, previous)
        self.assertEqual(PAGE.replace(UNPINNED, sw.EXCALIDRAW_PIN), after)
        self.assertIn("\r\n", after, "line endings must survive")

    def test_pinning_twice_changes_nothing(self):
        template = self.skill("excalidraw-diagram") / sw.RENDER_TEMPLATE
        sw.pin_render_template(template)
        once = template.read_bytes()
        changed, url = sw.pin_render_template(template)
        self.assertFalse(changed)
        self.assertEqual(sw.EXCALIDRAW_PIN, url)
        self.assertEqual(once, template.read_bytes())

    def test_a_version_the_skill_chose_is_left_alone(self):
        chosen = "https://esm.sh/@excalidraw/excalidraw@0.18.2?bundle"
        template = self.skill("excalidraw-diagram", PAGE.replace(UNPINNED, chosen)) / sw.RENDER_TEMPLATE
        before = template.read_bytes()
        result = self.pin([template.parent.parent])
        self.assertEqual(sw.OK, result.status)
        self.assertEqual(before, template.read_bytes())
        self.assertTrue(any("already pinned by the skill" in note for note in result.notes))

    def test_check_reports_an_unpinned_page_without_changing_it(self):
        directory = self.skill("excalidraw-diagram")
        before = (directory / sw.RENDER_TEMPLATE).read_bytes()
        result = self.pin([directory], check_only=True)
        self.assertEqual(sw.PARTIAL, result.status)
        self.assertIn("unversioned", result.detail)
        self.assertIn(sw.EXCALIDRAW_PIN, result.hint)
        self.assertEqual(before, (directory / sw.RENDER_TEMPLATE).read_bytes())

    def test_setup_pins_every_installed_copy_but_not_the_source_clone(self):
        project_copy = self.skill("excalidraw-diagram")
        synced_copy = self.skill("synced/account-sync/excalidraw-diagram")
        clone = self.skill(f"{sw.SOURCES_DIRNAME}/excalidraw-diagram")
        dirs = sw.installed_skill_dirs("excalidraw-diagram", [self.root, self.root / "synced"])
        self.assertIn(project_copy.resolve(), dirs)
        self.assertNotIn(clone.resolve(), dirs)

        with contextlib.redirect_stdout(io.StringIO()):
            result = self.pin(dirs + [synced_copy.resolve()])
        self.assertEqual(sw.OK, result.status)
        for directory in (project_copy, synced_copy):
            self.assertEqual(sw.EXCALIDRAW_PIN, sw.excalidraw_import(directory / sw.RENDER_TEMPLATE))
        self.assertEqual(UNPINNED, sw.excalidraw_import(clone / sw.RENDER_TEMPLATE))
        self.assertTrue(any(note.startswith("pinned") for note in result.notes))

    def test_a_page_without_a_recognisable_import_is_reported(self):
        directory = self.skill("excalidraw-diagram", PAGE.replace(UNPINNED, "./local-excalidraw.js"))
        result = self.pin([directory])
        self.assertEqual(sw.PARTIAL, result.status)
        self.assertIn("no recognisable Excalidraw import", result.detail)

    def test_skip_and_absent_skill(self):
        self.assertEqual(sw.SKIPPED, sw.pin_renderer([], False, skip=True).status)
        self.assertEqual(sw.SKIPPED, sw.pin_renderer([], False, skip=False).status)


if __name__ == "__main__":
    unittest.main()
