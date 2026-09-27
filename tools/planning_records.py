"""Read the structured parts of the workflow's Markdown records.

The Markdown files stay the source of truth. This module reads two conventions
from them, and nothing else, so that the machine handoff never depends on
interpreting free prose:

Record block
    A heading whose text starts with a stable ID, followed by a two-column
    ``| Field | Value |`` table and optional labelled sections::

        ### FR-018 — Password reset

        | Field | Value |
        | --- | --- |
        | Status | Approved |

        **Description**

        Users must be able to reset ...

        **Acceptance criteria**

        - AC-041 — User can request a reset email

    A section label is either a deeper heading or a line holding only bold
    text. Each section keeps its prose, list items and tables separately.

Register table
    A table whose first header names an ID column (``Question ID``,
    ``DEC ID`` ...). Each row whose first cell is a valid ID is one record.

Nothing here decides what a record means; the generator does that.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path

# --------------------------------------------------------------------------
# Identifiers. These patterns mirror schemas/common.schema.json exactly.
# --------------------------------------------------------------------------

ID_PATTERNS: dict[str, str] = {
    # Requirement kinds, in traceability order.
    "GOAL": r"GOAL-[0-9]{3,}",
    "BR": r"BR-[0-9]{3,}",
    "RULE": r"RULE-[0-9]{3,}",
    "FR": r"FR-(?:[A-Z][A-Z0-9]{1,11}-)?[0-9]{3,}",
    "NFR": r"NFR-[0-9]{3,}",
    "DR": r"DR-[0-9]{3,}",
    "IR": r"IR-[0-9]{3,}",
    "SR": r"SR-[0-9]{3,}",
    "UXR": r"UXR-[0-9]{3,}",
    "TR": r"TR-[0-9]{3,}",
    "EPIC": r"EPIC-[0-9]{3,}",
    "FEAT": r"FEAT-[0-9]{3,}",
    "TASK": r"TASK-[0-9]{3,}(?:-S[0-9]{2,})?",
    "TEST": r"TEST-[0-9]{3,}",
    "AC": r"AC-[0-9]{3,}",
    "ADR": r"ADR-[0-9]{3,}",
    "PRIN": r"PRIN-[0-9]{3,}",
    "DEC": r"DEC-[0-9]{3,}",
    "Q": r"Q-[0-9]{3,}",
    "ASM": r"ASM-[0-9]{3,}",
    "SRC": r"SRC-[0-9]{3,}",
    "MOD": r"MOD-[0-9]{3,}",
    "PHASE": r"PHASE-[0-9]{2,}",
    "RISK": r"RISK-[0-9]{3,}",
    "DEP": r"DEP-[0-9]{3,}",
    "SCOPE": r"SCOPE-[0-9]{3,}",
    "PROC": r"PROC-[0-9]{3,}",
    "ENT": r"ENT-[0-9]{3,}",
    "FIND": r"FIND-[0-9]{3,}",
    "REVIEW": r"REVIEW-[0-9]{3,}",
    "CHANGE": r"CHANGE-[0-9]{3,}",
    # Detail records: pages, API contracts, integration contracts.
    "PAGE": r"PAGE-[0-9]{3,}",
    "API": r"API-[0-9]{3,}",
    "INT": r"INT-[0-9]{3,}",
}

REQUIREMENT_KINDS = ("GOAL", "BR", "RULE", "FR", "NFR", "DR", "IR", "SR", "UXR", "TR")
# Kinds that describe system behaviour: each must be mapped to a module,
# implemented by a task and verified by a test. GOAL, BR and RULE are
# realised through them.
IMPLEMENTABLE_KINDS = ("FR", "NFR", "DR", "IR", "SR", "UXR", "TR")

# Longest alternatives first so that NFR is never read as FR and so on; the
# leading \b already prevents matches inside a longer word.
_ANY_ID = "|".join(ID_PATTERNS[k] for k in sorted(ID_PATTERNS, key=len, reverse=True))
ANY_ID_RE = re.compile(rf"\b(?:{_ANY_ID})\b")
FULL_ID_RE = {kind: re.compile(rf"^{pattern}$") for kind, pattern in ID_PATTERNS.items()}

# Identifier forms used before the machine handoff existed. Seeing one in a
# current record means it was not migrated.
LEGACY_ID_RE = re.compile(r"\b(?:BIZ-[0-9]{3,}|EPIC-[0-9]{2}|FEAT-[0-9]{2}-[0-9]{2}|AT-[0-9]{3,}|CR-[0-9]{3,})\b")


def kind_of(identifier: str) -> str | None:
    for kind, regex in FULL_ID_RE.items():
        if regex.match(identifier):
            return kind
    return None


def extract_ids(text: str, kinds: tuple[str, ...] | None = None) -> list[str]:
    """Return IDs in first-seen order, optionally limited to some kinds."""
    seen: list[str] = []
    for match in ANY_ID_RE.finditer(text or ""):
        value = match.group(0)
        if kinds is not None and kind_of(value) not in kinds:
            continue
        if value not in seen:
            seen.append(value)
    return seen


def natural_key(identifier: str) -> tuple:
    parts = re.split(r"([0-9]+)", identifier)
    return tuple(int(p) if p.isdigit() else p for p in parts)


# --------------------------------------------------------------------------
# Values
# --------------------------------------------------------------------------

_NONE_VALUES = {"none", "n/a", "na", "-", "—", "–", "nil", "no", "empty", "not applicable"}
_TBD_RE = re.compile(r"\bTBD\b")


def clean(value: str | None) -> str:
    """Strip Markdown decoration that carries no meaning in a field value."""
    if value is None:
        return ""
    text = value.replace("<br>", "\n").replace("<br/>", "\n").replace("<br />", "\n")
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    return "\n".join(line.strip() for line in text.strip().splitlines()).strip()


def is_none(value: str) -> bool:
    """True when a value explicitly states that nothing applies."""
    head = clean(value).lower().split("—")[0].split(" - ")[0].strip().rstrip(".")
    return head in _NONE_VALUES or head.startswith("none")


def has_tbd(value: str) -> bool:
    return bool(_TBD_RE.search(value or ""))


def is_blank(value: str) -> bool:
    return not clean(value)


# --------------------------------------------------------------------------
# Markdown structure
# --------------------------------------------------------------------------

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
BOLD_LABEL_RE = re.compile(r"^\*\*([^*]+?)\*\*:?\s*$")
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|[0-9]+[.)])\s+(.*)$")
TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(?:\|\s*:?-{3,}:?\s*)*\|?\s*$")
RECORD_HEADING_RE = re.compile(rf"^(?P<id>{_ANY_ID})\s*(?:—|–|-|:)\s*(?P<title>.+)$")


def split_row(line: str) -> list[str]:
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    cells, current, escaped = [], [], False
    for char in body:
        if escaped:
            current.append(char)
            escaped = False
        elif char == "\\":
            escaped = True
            current.append(char)
        elif char == "|":
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    cells.append("".join(current).strip())
    return [c.replace("\\|", "|") for c in cells]


def norm_key(label: str) -> str:
    text = clean(label).lower()
    text = text.rstrip(":").strip()
    return re.sub(r"\s+", " ", text)


def slug_key(label: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", norm_key(label)).strip("_")


@dataclass
class Table:
    headers: list[str]
    rows: list[list[str]]
    line: int  # 1-based line of the header row

    def keys(self) -> list[str]:
        return [norm_key(h) for h in self.headers]

    def dict_rows(self) -> list[tuple[int, dict[str, str]]]:
        keys = self.keys()
        out = []
        for offset, row in enumerate(self.rows):
            padded = row + [""] * (len(keys) - len(row))
            out.append((self.line + 2 + offset, dict(zip(keys, padded))))
        return out


@dataclass
class Section:
    label: str
    text_lines: list[str] = field(default_factory=list)
    items: list[str] = field(default_factory=list)
    tables: list[Table] = field(default_factory=list)

    @property
    def text(self) -> str:
        return clean("\n".join(self.text_lines))

    def as_json(self) -> dict:
        return {
            "text": self.text,
            "items": [clean(i) for i in self.items],
            "tables": [
                {"headers": [clean(h) for h in t.headers], "rows": [[clean(c) for c in r] for r in t.rows]}
                for t in self.tables
            ],
        }

    def is_empty(self) -> bool:
        return not self.text and not self.items and not self.tables


@dataclass
class Record:
    id: str
    title: str
    level: int
    path: Path
    line: int
    fields: dict[str, str] = field(default_factory=dict)
    field_lines: dict[str, int] = field(default_factory=dict)
    sections: dict[str, Section] = field(default_factory=dict)
    raw: str = ""

    def field(self, *names: str) -> str | None:
        """Value of the first field present among ``names`` (normalized)."""
        for name in names:
            key = norm_key(name)
            if key in self.fields:
                return self.fields[key]
        return None

    def section(self, *names: str) -> Section | None:
        for name in names:
            key = norm_key(name)
            if key in self.sections:
                return self.sections[key]
        return None


def _meaningful_lines(text: str) -> list[tuple[int, str]]:
    """Lines with fenced code and HTML comments blanked out, numbered from 1."""
    out: list[tuple[int, str]] = []
    in_fence = False
    in_comment = False
    for number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if in_comment:
            if "-->" in stripped:
                in_comment = False
            out.append((number, ""))
            continue
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            out.append((number, ""))
            continue
        if in_fence:
            out.append((number, ""))
            continue
        if stripped.startswith("<!--"):
            if "-->" not in stripped:
                in_comment = True
            out.append((number, ""))
            continue
        out.append((number, line))
    return out


def _collect_table(lines: list[tuple[int, str]], index: int) -> tuple[Table | None, int]:
    """Parse a table starting at ``index``; return it and the next index."""
    number, header = lines[index]
    if not header.strip().startswith("|") or index + 1 >= len(lines):
        return None, index
    if not TABLE_SEP_RE.match(lines[index + 1][1]):
        return None, index
    headers = split_row(header)
    rows = []
    cursor = index + 2
    while cursor < len(lines) and lines[cursor][1].strip().startswith("|"):
        rows.append(split_row(lines[cursor][1]))
        cursor += 1
    return Table(headers=headers, rows=rows, line=number), cursor


def read_tables(path: Path) -> list[Table]:
    lines = _meaningful_lines(path.read_text(encoding="utf-8"))
    tables, index = [], 0
    while index < len(lines):
        table, nxt = _collect_table(lines, index)
        if table:
            tables.append(table)
            index = nxt
        else:
            index += 1
    return tables


def read_records(path: Path, kinds: tuple[str, ...]) -> list[Record]:
    """Every record block in ``path`` whose ID is one of ``kinds``."""
    lines = _meaningful_lines(path.read_text(encoding="utf-8"))
    records: list[Record] = []

    heads = []
    for position, (number, line) in enumerate(lines):
        match = HEADING_RE.match(line)
        if match:
            heads.append((position, len(match.group(1)), clean(match.group(2))))

    for h_index, (position, level, heading) in enumerate(heads):
        match = RECORD_HEADING_RE.match(heading)
        if not match or kind_of(match.group("id")) not in kinds:
            continue
        end = len(lines)
        for later_position, later_level, _ in heads[h_index + 1:]:
            if later_level <= level:
                end = later_position
                break
        record = Record(
            id=match.group("id"),
            title=match.group("title").strip(),
            level=level,
            path=path,
            line=lines[position][0],
            # Comments and code fences are already blanked, so an ID quoted in
            # an HTML comment is not mistaken for a real reference.
            raw="\n".join(line for _, line in lines[position:end]),
        )
        _fill_record(record, lines[position + 1:end], level)
        records.append(record)
    return records


def _fill_record(record: Record, body: list[tuple[int, str]], level: int) -> None:
    current = Section(label="")
    record.sections[""] = current
    field_table_seen = False
    index = 0
    last_item_open = False
    while index < len(body):
        number, line = body[index]
        stripped = line.strip()

        heading = HEADING_RE.match(line)
        label_match = BOLD_LABEL_RE.match(stripped)
        if (heading and len(heading.group(1)) > level) or label_match:
            label = clean(heading.group(2) if heading else label_match.group(1))
            current = Section(label=label)
            record.sections[norm_key(label)] = current
            last_item_open = False
            index += 1
            continue

        table, nxt = _collect_table(body, index)
        if table:
            keys = table.keys()
            if not field_table_seen and len(keys) >= 2 and keys[0] == "field":
                field_table_seen = True
                for offset, row in enumerate(table.rows):
                    if not row or not clean(row[0]):
                        continue
                    key = norm_key(row[0])
                    record.fields[key] = row[1] if len(row) > 1 else ""
                    record.field_lines[key] = table.line + 2 + offset
            else:
                current.tables.append(table)
            last_item_open = False
            index = nxt
            continue

        item = LIST_ITEM_RE.match(line)
        if item:
            current.items.append(item.group(1).strip())
            last_item_open = True
        elif stripped and last_item_open and line.startswith((" ", "\t")):
            current.items[-1] += " " + stripped
        elif stripped:
            current.text_lines.append(stripped)
            last_item_open = False
        else:
            last_item_open = False
        index += 1


def read_register(path: Path, id_headers: tuple[str, ...], kind: str) -> list[tuple[int, dict[str, str]]]:
    """Rows of every table in ``path`` whose first header is one of ``id_headers``.

    Only rows whose first cell is a valid ``kind`` ID are returned, so blank
    template rows are ignored rather than reported as records.
    """
    wanted = {norm_key(h) for h in id_headers}
    rows: list[tuple[int, dict[str, str]]] = []
    for table in read_tables(path):
        keys = table.keys()
        if not keys or keys[0] not in wanted:
            continue
        for line, row in table.dict_rows():
            first = clean(row.get(keys[0], ""))
            if FULL_ID_RE[kind].match(first):
                row["__id__"] = first
                rows.append((line, row))
    return rows


# --------------------------------------------------------------------------
# Project layout: the files the machine handoff is generated from
# --------------------------------------------------------------------------

REQUIREMENT_FILES = (
    "specification/business-requirements.md",   # GOAL and BR
    "specification/business-rules.md",          # RULE
    "specification/functional-requirements.md",
    "specification/non-functional-requirements.md",
    "specification/data-requirements.md",
    "specification/integration-requirements.md",
    "specification/security-requirements.md",
    "specification/ux-requirements.md",
    "specification/technical-requirements.md",
)
REGISTER_FILES = {
    "sources": ("discovery/sources.md", "discovery/registers.md"),
    "questions": ("discovery/open-questions.md", "discovery/registers.md"),
    "assumptions": ("discovery/assumptions.md", "discovery/registers.md"),
    "decisions": ("discovery/decisions.md", "discovery/registers.md"),
    "risks": ("discovery/risks.md", "discovery/registers.md"),
    "dependencies": ("discovery/dependencies.md", "discovery/registers.md"),
}
STATE_FILE = "project-state.md"
SCOPE_FILE = "specification/scope.md"
PROCESS_FILE = "specification/process-model.md"
DOMAIN_FILE = "specification/domain-model.md"
SOLUTION_FILE = "specification/solution-structure.md"
ARCHITECTURE_DIR = "architecture"
ADR_GLOB = "architecture/ADR-*.md"
ARCHITECTURE_REGISTER_FILE = "architecture/architecture-register.md"
PRINCIPLES_FILE = "architecture/principles.md"
ARCHITECTURE_README_FILE = "architecture/README.md"
BACKLOG_FILE = "backlog/backlog.md"
TASK_GLOB = "backlog/tasks/*.md"
CHANGE_GLOB = "changes/CHANGE-*.md"
CHANGE_REPORT_SUFFIX = "-impact-report.md"
BASELINE_FILE = "changes/baseline.json"
TESTS_FILE = "quality/acceptance-tests.md"

# Stage records read by the gate checker (tools/check_gates.py). They are
# authored evidence about the plan, not part of the machine handoff.
INTAKE_FILE = "discovery/project-intake.md"
DISCOVERY_LOG_FILE = "discovery/discovery-log.md"
SPECIFICATION_FILE = "specification/technical-specification.md"
REQUIREMENT_REVIEW_FILE = "reviews/requirement-quality-review.md"
SPECIFICATION_REVIEW_FILE = "reviews/specification-review.md"
# Closed review cycles, frozen: reviews/history/specification-review-cycle-001.md, ...
SPECIFICATION_REVIEW_HISTORY_GLOB = "reviews/history/specification-review-cycle-*.md"
ARCHITECTURE_REVIEW_FILE = "reviews/architecture-review.md"
FINAL_REVIEW_FILE = "reviews/final-planning-review.md"
PLANNING_SUMMARY_FILE = "deliverables/planning-summary.md"

# Human-facing files scanned only for identifier consistency.
REFERENCE_SCAN_GLOBS = (
    SPECIFICATION_FILE,
    "traceability/traceability.md",
    "reviews/*.md",
    "deliverables/*.md",
)


def source_files(project: Path) -> list[Path]:
    """Every Markdown file the handoff is generated from, in a stable order."""
    candidates: set[Path] = set()
    for rel in (STATE_FILE, SCOPE_FILE, PROCESS_FILE, DOMAIN_FILE, SOLUTION_FILE, ARCHITECTURE_REGISTER_FILE,
                PRINCIPLES_FILE, BACKLOG_FILE, TESTS_FILE, SPECIFICATION_REVIEW_FILE, ARCHITECTURE_REVIEW_FILE,
                *REQUIREMENT_FILES):
        candidates.add(project / rel)
    for rels in REGISTER_FILES.values():
        for rel in rels:
            candidates.add(project / rel)
    candidates.update(project.glob(SPECIFICATION_REVIEW_HISTORY_GLOB))
    candidates.update(project.glob(ADR_GLOB))
    candidates.update(project.glob(TASK_GLOB))
    candidates.update(change_files(project))
    candidates.add(project / BASELINE_FILE)
    existing = [p for p in candidates if p.is_file()]
    return sorted(existing, key=lambda p: p.relative_to(project).as_posix())


def change_files(project: Path) -> list[Path]:
    """Change records; their generated impact reports are not sources."""
    return sorted(p for p in project.glob(CHANGE_GLOB) if not p.name.endswith(CHANGE_REPORT_SUFFIX))


def fingerprint(project: Path) -> str:
    """SHA-256 over (relative path, normalized content) of every source file.

    Line endings are normalized so that a checkout on another platform yields
    the same fingerprint for the same content.
    """
    digest = hashlib.sha256()
    for path in source_files(project):
        rel = path.relative_to(project).as_posix()
        data = path.read_bytes().replace(b"\r\n", b"\n")
        digest.update(rel.encode("utf-8") + b"\0")
        digest.update(hashlib.sha256(data).hexdigest().encode("ascii") + b"\n")
    return digest.hexdigest()


def rel(project: Path, path: Path) -> str:
    try:
        return path.relative_to(project).as_posix()
    except ValueError:
        return path.as_posix()
