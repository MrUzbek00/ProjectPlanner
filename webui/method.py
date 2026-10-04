"""The workflow method, read from the documents that define it.

Nothing about the method is restated here. Stages, purposes and outputs come
from the table in WORKFLOW.md section 2, gate checks from section 20, templates
and project files from templates/README.md, and the tool list from README.md.
Stage IDs and gate names come from tools/check_gates.py. Edit those documents
and the guide follows.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import markdown
from markupsafe import Markup

from . import REPO_ROOT
import check_gates as cg  # noqa: E402  (tools/ is on sys.path via webui/__init__)
import planning_records as pr  # noqa: E402

WORKFLOW = REPO_ROOT / "WORKFLOW.md"
TEMPLATES_DIR = REPO_ROOT / "templates"
TEMPLATES_INDEX = TEMPLATES_DIR / "README.md"
README = REPO_ROOT / "README.md"

GATE_ID = re.compile(r"^\s*(G\d+|GR|GB|GC)\b")
STAGE_LABEL = re.compile(r"^\s*(\d+[AB]?)\b")
MD_LINK = re.compile(r"\[([^\]]+)\]\(([^)#\s]+)(?:#[^)]*)?\)")
STAGE_HEADING = re.compile(r"^## \d+\. Stage (\d+) — (.+)$", re.MULTILINE)


@dataclass
class TemplateRef:
    title: str
    file: str


@dataclass
class Stage:
    label: str            # "1" ... "13", "8A", "8B", "10A", "10B"
    number: int
    name: str
    purpose: str = ""
    outputs: str = ""
    gate: str = ""
    gate_name: str = ""
    checks: str = ""
    templates: list[TemplateRef] = field(default_factory=list)
    files: str = ""


def _strip(text: str) -> str:
    return pr.clean(text or "").strip()


def _table(path: Path, *first_keys: str):
    for table in pr.read_tables(path):
        if table.keys()[: len(first_keys)] == list(first_keys):
            return table
    return None


def template_refs(cell: str) -> list[TemplateRef]:
    return [TemplateRef(title, file) for title, file in MD_LINK.findall(cell or "")
            if file.endswith(".md") and (TEMPLATES_DIR / file).is_file()]


@lru_cache(maxsize=1)
def _stages_cached(mtimes: tuple) -> tuple[list[Stage], Stage]:
    gate_names = {gate: name for _, _, gate, name in cg.STAGES}
    gate_numbers = {gate: number for number, _, gate, _ in cg.STAGES}
    checks: dict[str, str] = {}
    gate_table = _table(WORKFLOW, "gate", "stage exited")
    if gate_table:
        for _, row in gate_table.dict_rows():
            match = GATE_ID.match(row.get("gate", ""))
            if match:
                checks[match.group(1)] = _strip(next((v for k, v in row.items() if k.startswith("checks")), ""))

    templates: dict[str, tuple[list[TemplateRef], str]] = {}
    continuous_templates: list[TemplateRef] = []
    continuous_files = ""
    index = _table(TEMPLATES_INDEX, "stage", "templates")
    if index:
        for _, row in index.dict_rows():
            label = STAGE_LABEL.match(row.get("stage", ""))
            refs, files = template_refs(row.get("templates", "")), _strip(row.get("project files", ""))
            if label:
                templates[label.group(1)] = (refs, files)
            else:
                continuous_templates, continuous_files = refs, files

    stages: list[Stage] = []
    overview = _table(WORKFLOW, "stage", "purpose")
    for _, row in overview.dict_rows() if overview else []:
        label_match = STAGE_LABEL.match(row.get("stage", ""))
        gate_match = GATE_ID.match(row.get("exit gate", ""))
        if not label_match or not gate_match:
            continue
        label, gate = label_match.group(1), gate_match.group(1)
        refs, files = templates.get(label, ([], ""))
        stages.append(Stage(
            label=label, number=gate_numbers.get(gate, int(re.match(r"\d+", label).group(0))),
            name=_strip(re.sub(r"^\s*\d+[AB]?\.?\s*", "", row.get("stage", ""))),
            purpose=_strip(row.get("purpose", "")), outputs=_strip(row.get("main outputs", "")),
            gate=gate, gate_name=gate_names.get(gate, ""), checks=checks.get(gate, ""),
            templates=refs, files=files,
        ))
    gc_id, gc_name, gc_stage = cg.CHANGE_GATE
    continuous = Stage(label="∞", number=0, name=gc_stage, purpose="Every meaningful change after approval is recorded, analysed and human-decided.",
                       gate=gc_id, gate_name=gc_name, checks=checks.get(gc_id, ""),
                       templates=continuous_templates, files=continuous_files)
    return stages, continuous


def _mtimes() -> tuple:
    return tuple(path.stat().st_mtime_ns if path.is_file() else 0 for path in (WORKFLOW, TEMPLATES_INDEX))


def stages() -> tuple[list[Stage], Stage]:
    """The method's stages in order, and the continuous change-control gate."""
    return _stages_cached(_mtimes())


def tools() -> list[dict[str, str]]:
    table = _table(README, "tool", "purpose")
    if not table:
        return []
    return [{"tool": _strip(row.get("tool", "")), "purpose": _strip(row.get("purpose", ""))}
            for _, row in table.dict_rows()]


def template_files() -> list[str]:
    return sorted(path.name for path in TEMPLATES_DIR.glob("*.md"))


# --------------------------------------------------------------------------
# Markdown rendering of trusted repository documents
# --------------------------------------------------------------------------


def render_markdown(text: str, link_template) -> Markup:
    """Render repository Markdown; relative links to templates become UI links."""
    html = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
    known = set(template_files())

    def relink(match: re.Match) -> str:
        target = match.group(1)
        name = target.split("/")[-1]
        if name in known and (target == name or target.startswith("templates/")):
            return f'href="{link_template(name)}"'
        return match.group(0)

    return Markup(re.sub(r'href="([^"#]+\.md)(?:#[^"]*)?"', relink, html))


def stage_section(number: int) -> tuple[str, str] | None:
    """(title, Markdown) of WORKFLOW.md's section for stage ``number``."""
    text = WORKFLOW.read_text(encoding="utf-8")
    matches = list(STAGE_HEADING.finditer(text))
    for i, match in enumerate(matches):
        if int(match.group(1)) == number:
            end = text.find("\n## ", match.end())
            body = text[match.end(): end if end != -1 else len(text)]
            return f"Stage {number} — {match.group(2).strip()}", body.strip()
    return None


def template_document(name: str) -> str | None:
    if name not in template_files():
        return None
    return (TEMPLATES_DIR / name).read_text(encoding="utf-8")
