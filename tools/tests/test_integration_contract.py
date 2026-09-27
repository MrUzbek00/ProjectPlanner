"""Tests for the ProjectPlanner -> SoftwareFactory integration contract, planner side.

Run from the repository root:
    python -m unittest discover -s tools/tests -v

The contract is handoff-manifest.json plus the consumer views in
schemas/integration/. These tests pin what a consumer relies on: the manifest's
status and flags, stable task content hashes, the handoff version label, and
that a manifest never claims more than the files support.
"""

from __future__ import annotations

import contextlib
import io
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))

import generate_handoff as gh  # noqa: E402
import handoff_contract as hc  # noqa: E402
import validate_handoff as vh  # noqa: E402

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "sample-project"
FIXED_TIME = "2026-09-26T00:00:00Z"
LATER_TIME = "2026-09-27T09:30:00Z"


class ContractCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.project = Path(self._tmp.name) / "sample-project"
        shutil.copytree(FIXTURE, self.project, ignore=shutil.ignore_patterns("machine-handoff", "requirement-map.md"))
        self.handoff = self.project / "machine-handoff"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def edit(self, rel: str, old: str, new: str) -> None:
        path = self.project / rel
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text, f"fixture text not found in {rel}: {old!r}")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")

    def generate(self, when: str = FIXED_TIME) -> int:
        with contextlib.redirect_stdout(io.StringIO()):
            return gh.main([str(self.project), "--generated-at", when])

    def manifest(self) -> dict:
        return json.loads((self.handoff / hc.MANIFEST_FILE).read_text(encoding="utf-8"))

    def task(self, task_id: str) -> dict:
        return json.loads((self.handoff / "tasks" / f"{task_id}.json").read_text(encoding="utf-8"))

    def validate_directory(self) -> vh.Findings:
        raw = vh.read_directory(self.handoff)
        findings, bundle = vh.validate_files(raw, self.project)
        manifest_path = self.handoff / hc.MANIFEST_FILE
        findings.extend(vh.manifest_findings(manifest_path.read_bytes() if manifest_path.is_file() else None,
                                             raw, bundle, findings))
        return findings

    def rewrite(self, rel: str, change) -> None:
        path = self.handoff / rel
        document = json.loads(path.read_text(encoding="utf-8"))
        change(document)
        path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    def codes(self, findings: vh.Findings) -> set[str]:
        return {f.code for f in findings.errors}


class Manifest(ContractCase):
    def test_manifest_is_the_ready_entry_point(self):
        self.assertEqual(0, self.generate())
        manifest = self.manifest()
        vh.load_validators()[vh.CONTRACT_PREFIX + hc.MANIFEST_SCHEMA].validate(manifest)
        self.assertEqual(hc.CONTRACT_VERSION, manifest["schema_version"])
        self.assertEqual(vh.SCHEMA_VERSION, manifest["planner_schema_version"])
        self.assertEqual("READY_FOR_HANDOFF", manifest["handoff_status"])
        self.assertEqual(["TASK-001", "TASK-002", "TASK-003"], manifest["ready_tasks"])
        self.assertTrue(all(manifest["validation"].values()), manifest["validation"])
        self.assertEqual({"tasks_total": 4, "tasks_ready": 3, "tasks_needs_discovery": 1},
                         {k: manifest["summary"][k] for k in ("tasks_total", "tasks_ready", "tasks_needs_discovery")})
        roles = {f["role"] for f in manifest["files"]}
        for required in ("project", "requirements", "architecture", "traceability", "backlog_readiness", "changes",
                         "specification_review", "task"):
            self.assertIn(required, roles)
        listed = {entry["id"]: entry for entry in manifest["tasks"]}
        self.assertEqual(self.task("TASK-002")["content_hash"], listed["TASK-002"]["content_hash"])
        self.assertEqual(1, listed["TASK-002"]["revision"])

    def test_written_handoff_and_manifest_validate_standalone(self):
        self.assertEqual(0, self.generate())
        findings = self.validate_directory()
        self.assertEqual([], [(f.code, f.message) for f in findings.errors])
        self.assertEqual([], [(f.code, f.message) for f in findings.warnings])

    def test_every_file_satisfies_the_consumer_views(self):
        self.assertEqual(0, self.generate())
        validators = vh.load_validators()
        requirements = json.loads((self.handoff / "requirements.json").read_text(encoding="utf-8"))["requirements"]
        decisions = json.loads((self.handoff / "architecture.json").read_text(encoding="utf-8"))["decisions"]
        for schema, items in ((hc.TASK_VIEW_SCHEMA, [self.task(f"TASK-00{n}") for n in range(1, 5)]),
                              (hc.REQUIREMENT_VIEW_SCHEMA, requirements), (hc.ADR_VIEW_SCHEMA, decisions)):
            for item in items:
                validators[vh.CONTRACT_PREFIX + schema].validate(item)

    def test_missing_manifest_is_an_error(self):
        self.assertEqual(0, self.generate())
        (self.handoff / hc.MANIFEST_FILE).unlink()
        self.assertIn("MANIFEST_MISSING", self.codes(self.validate_directory()))

    def test_unsupported_contract_version_is_an_error(self):
        self.assertEqual(0, self.generate())
        self.rewrite(hc.MANIFEST_FILE, lambda m: m.update(schema_version="2.0"))
        self.assertIn("MANIFEST_UNSUPPORTED_VERSION", self.codes(self.validate_directory()))

    def test_edited_task_file_is_detected_by_manifest_and_content_hash(self):
        self.assertEqual(0, self.generate())
        self.rewrite("tasks/TASK-002.json", lambda t: t.update(objective="Something the planner never approved."))
        codes = self.codes(self.validate_directory())
        self.assertIn("MANIFEST_HASH_MISMATCH", codes)
        self.assertIn("TASK_CONTENT_HASH_MISMATCH", codes)

    def test_manifest_task_revision_must_match_the_task_file(self):
        self.assertEqual(0, self.generate())
        self.rewrite(hc.MANIFEST_FILE, lambda m: m["tasks"][1].update(revision=7))
        self.assertIn("MANIFEST_TASK_MISMATCH", self.codes(self.validate_directory()))

    def test_invalid_handoff_is_not_ready_for_handoff_and_its_flags_cannot_be_raised(self):
        self.edit("backlog/tasks/TASK-001.md", "| Blocked By | None |", "| Blocked By | TASK-002 |")
        self.assertEqual(1, self.generate())
        manifest = self.manifest()
        self.assertEqual("INVALID", manifest["handoff_status"])
        self.assertFalse(manifest["validation"]["dependency_graph_valid"])
        self.assertEqual([], manifest["ready_tasks"])

        def claim_ready(m: dict) -> None:
            m["validation"]["dependency_graph_valid"] = True
            m["handoff_status"] = "READY_FOR_HANDOFF"

        self.rewrite(hc.MANIFEST_FILE, claim_ready)
        codes = self.codes(self.validate_directory())
        self.assertIn("MANIFEST_FLAG_UNSUPPORTED", codes)
        self.assertIn("MANIFEST_STATUS_MISMATCH", codes)


class ContentHash(ContractCase):
    def test_timestamps_do_not_change_hashes_or_the_handoff_version(self):
        self.assertEqual(0, self.generate(FIXED_TIME))
        first = self.manifest()
        self.assertEqual("1.0", first["handoff_version"])
        self.assertEqual(0, self.generate(LATER_TIME))
        second = self.manifest()
        self.assertEqual(LATER_TIME, second["generated_at"])
        self.assertEqual(first["content_fingerprint"], second["content_fingerprint"])
        self.assertEqual(first["tasks"], second["tasks"])
        self.assertEqual("1.0", second["handoff_version"])

    def test_changed_requirement_changes_the_hash_of_tasks_built_on_it(self):
        self.assertEqual(0, self.generate())
        before = {entry["id"]: entry["content_hash"] for entry in self.manifest()["tasks"]}
        self.edit("specification/functional-requirements.md",
                  "A user can request a password-reset email by entering an email address.",
                  "A user can request a password-reset email by entering an email address or a user name.")
        self.generate()
        after = {entry["id"]: entry["content_hash"] for entry in self.manifest()["tasks"]}
        using = {tid for tid in before if "FR-AUTH-001" in self.task(tid)["source_requirements"]}
        self.assertIn("TASK-002", using)
        for tid in before:
            (self.assertNotEqual if tid in using else self.assertEqual)(before[tid], after[tid], tid)
        self.assertEqual("1.1", self.manifest()["handoff_version"])

    def test_priority_is_not_task_content(self):
        self.assertEqual(0, self.generate())
        before = self.task("TASK-003")["content_hash"]
        self.edit("backlog/tasks/TASK-003.md", "| Priority | High |", "| Priority | Medium |")
        self.generate()
        self.assertEqual("medium", self.task("TASK-003")["priority"])
        self.assertEqual(before, self.task("TASK-003")["content_hash"])

    def test_handoff_version_follows_the_specification_version(self):
        previous = {"project_id": "SAMPLE", "handoff_version": "1.4", "content_fingerprint": "sha256:" + "0" * 64,
                    "specification_version": "1.0"}
        fingerprint = "sha256:" + "1" * 64
        self.assertEqual("1.5", hc.next_handoff_version(previous, "SAMPLE", fingerprint, "1.0"))
        self.assertEqual("2.0", hc.next_handoff_version(previous, "SAMPLE", fingerprint, "1.1"))
        self.assertEqual("1.4", hc.next_handoff_version(previous, "SAMPLE", previous["content_fingerprint"], "1.0"))
        self.assertEqual("1.0", hc.next_handoff_version(previous, "OTHER", fingerprint, "1.0"))
        self.assertEqual("1.0", hc.next_handoff_version(None, "SAMPLE", fingerprint, "1.0"))


class ContractLock(unittest.TestCase):
    def test_contract_lock_matches_the_schema_files(self):
        self.assertEqual([], hc.lock_problems())

    def test_contract_schemas_are_valid_and_self_contained(self):
        from jsonschema import Draft202012Validator

        for path in hc.contract_schemas():
            schema = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
            refs = [ref for ref in _refs(schema) if not ref.startswith("#/$defs/")]
            self.assertEqual([], refs, f"{path.name} must use local $defs only, so a consumer needs no registry")


def _refs(node) -> list[str]:
    if isinstance(node, dict):
        found = [node["$ref"]] if isinstance(node.get("$ref"), str) else []
        return found + [ref for value in node.values() for ref in _refs(value)]
    if isinstance(node, list):
        return [ref for value in node for ref in _refs(value)]
    return []


if __name__ == "__main__":
    unittest.main()
