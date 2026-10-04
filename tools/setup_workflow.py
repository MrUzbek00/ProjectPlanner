#!/usr/bin/env python3
"""Provision everything the Project Planning Workflow needs to run.

Installs the two diagram skills the workflow generates diagrams with, the Python
packages the document builder and the machine-handoff validator need, and the
Excalidraw render pipeline. Detects
the draw.io CLI and explains how to install it rather than installing a desktop
application unprompted.

Usage::

    python tools/setup_workflow.py            # install and report
    python tools/setup_workflow.py --check    # report only, change nothing
    python tools/setup_workflow.py --scope project

Safe to re-run. Existing skills are updated rather than replaced, and a skill
already provided by another installation is left alone - except for one line:
the Excalidraw render page's library import is pinned to a known-good version in
every installed copy, and re-pinned on every run, because the skill ships an
unversioned import that currently resolves to a build that never loads.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

OK = "ready"
MISSING = "missing"
PARTIAL = "partial"
SKIPPED = "skipped"


@dataclass
class SkillSpec:
    name: str
    repo: str
    purpose: str
    required: bool = True


SKILLS = [
    SkillSpec(
        name="excalidraw-diagram",
        repo="https://github.com/coleam00/excalidraw-diagram-skill.git",
        purpose="BPMN process diagrams (templates/24)",
    ),
    SkillSpec(
        name="drawio-skill",
        repo="https://github.com/Agents365-ai/drawio-skill.git",
        purpose="ER, state and data-flow diagrams (templates/25)",
    ),
]


@dataclass
class Result:
    item: str
    status: str
    detail: str = ""
    hint: str = ""
    required: bool = True
    notes: list[str] = field(default_factory=list)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def have(executable: str) -> str | None:
    return shutil.which(executable)


def run(command: list[str], cwd: Path | None = None, timeout: int = 900):
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        timeout=timeout,
    )


def failure_detail(result) -> str:
    """Pull the meaningful line out of a failed command.

    Package managers emit upgrade notices on stderr, so the last line is often
    not the error. Prefer an explicit ERROR line, and ignore notices entirely.
    """
    lines = [
        line.strip()
        for line in ((result.stderr or "") + "\n" + (result.stdout or "")).splitlines()
        if line.strip() and not line.strip().startswith(("[notice]", "WARNING:", "HINT:"))
    ]
    if not lines:
        return "command failed"
    for line in lines:
        if line.upper().startswith("ERROR"):
            if "enable-long-paths" in (result.stderr or "") + (result.stdout or ""):
                return line + " (Windows long-path support may need enabling)"
            return line
    return lines[-1]


def say(message: str = "") -> None:
    print(message, flush=True)


def skills_root(scope: str, override: Path | None) -> Path:
    if override:
        return override.expanduser().resolve()
    if scope == "project":
        return REPO_ROOT / ".claude" / "skills"
    return Path.home() / ".claude" / "skills"


#: Clones live here; the discoverable skill is materialized next to them.
SOURCES_DIRNAME = ".workflow-sources"

#: The Excalidraw library the render page imports. The skill imports
#: `https://esm.sh/@excalidraw/excalidraw?bundle` with no version; that resolves to
#: 0.18.1, one of whose dependencies esm.sh serves as 404, so the page never loads
#: and every render times out. 0.18.0 from jsDelivr loads and provides exportToSvg,
#: and does not depend on esm.sh's on-the-fly builds at all.
EXCALIDRAW_PIN = "https://cdn.jsdelivr.net/npm/@excalidraw/excalidraw@0.18.0/+esm"
RENDER_TEMPLATE = Path("references") / "render_template.html"
#: An `import ... from "<url>"` whose URL loads @excalidraw/excalidraw from any CDN.
EXCALIDRAW_IMPORT = re.compile(r"""(\bfrom\s*)(["'])(https?://[^"']*@excalidraw/excalidraw\b[^"']*)\2""")
#: A URL that names an explicit version, e.g. .../@excalidraw/excalidraw@0.18.0...
VERSIONED = re.compile(r"@excalidraw/excalidraw@\d")

#: Never copied out of a source checkout into the skills directory.
COPY_IGNORE = shutil.ignore_patterns(
    ".git", ".github", ".gitignore", "node_modules", "__pycache__", "*.pyc", "tests", ".venv"
)


def locate_skill_dir(repo_dir: Path, name: str) -> Path | None:
    """Find the directory holding SKILL.md inside a cloned repository.

    Some skills are published as a repository whose root is the skill; others are
    monorepos that keep the skill under `skills/<name>/`. An assistant only
    discovers `<skills-root>/<name>/SKILL.md`, so the right directory has to be
    found before anything is put in place.
    """
    if (repo_dir / "SKILL.md").is_file():
        return repo_dir
    preferred = repo_dir / "skills" / name
    if (preferred / "SKILL.md").is_file():
        return preferred
    for pattern in ("*/SKILL.md", "*/*/SKILL.md"):
        for match in sorted(repo_dir.glob(pattern)):
            if ".git" not in match.parts:
                return match.parent
    return None


def materialize(source: Path, destination: Path) -> None:
    """Copy a skill into place, preserving anything already there.

    Merging rather than replacing keeps a previously prepared render environment
    alive across updates.
    """
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination, ignore=COPY_IGNORE, dirs_exist_ok=True)


def find_existing_skill(root: Path, name: str, max_depth: int = 3) -> Path | None:
    """Look for <name>/SKILL.md at or below the skills root.

    Some setups keep skills in a nested directory, for example a `synced/` folder
    populated by an account sync. A skill found there is already available to the
    assistant, so installing a second copy would only create a duplicate name.
    """
    direct = root / name
    if (direct / "SKILL.md").is_file():
        return direct
    if not root.is_dir():
        return None
    for depth in range(1, max_depth + 1):
        pattern = "/".join(["*"] * depth) + f"/{name}/SKILL.md"
        for match in root.glob(pattern):
            if SOURCES_DIRNAME not in match.parts:
                return match.parent
    return None


# --------------------------------------------------------------------------
# Steps
# --------------------------------------------------------------------------


def check_git() -> Result:
    path = have("git")
    if path:
        version = run(["git", "--version"]).stdout.strip()
        return Result("git", OK, version or path)
    return Result(
        "git",
        MISSING,
        "not found on PATH",
        "Install Git from https://git-scm.com/downloads, then re-run this script.",
    )


def install_skill(
    spec: SkillSpec,
    root: Path,
    check_only: bool,
    update: bool,
    offline: bool,
    also_search: list[Path] | None = None,
) -> Result:
    target = root / spec.name
    existing = find_existing_skill(root, spec.name)
    # A skill installed under the other scope still works, so report it rather
    # than claiming it is missing and installing a second copy.
    for alternate in also_search or []:
        if existing:
            break
        existing = find_existing_skill(alternate, spec.name)

    if existing and existing != target:
        return Result(
            spec.name,
            OK,
            f"already provided at {existing}",
            required=spec.required,
            notes=["Managed outside this installer; not updated by it."],
        )

    installed = (target / "SKILL.md").is_file()

    if check_only:
        if installed:
            return Result(spec.name, OK, f"installed at {target}", required=spec.required)
        return Result(
            spec.name,
            MISSING,
            f"not installed in {root}",
            "Run: python tools/setup_workflow.py",
            required=spec.required,
        )

    if installed and (not update or offline):
        return Result(spec.name, OK, f"installed at {target}", required=spec.required)

    if offline:
        return Result(
            spec.name,
            MISSING,
            "not installed and --offline was given",
            f"Run without --offline, or clone {spec.repo} into {target}",
            required=spec.required,
        )

    if not have("git"):
        return Result(spec.name, MISSING, "git is required to install this skill", required=spec.required)

    sources = root / SOURCES_DIRNAME / spec.name
    notes: list[str] = []

    if (sources / ".git").is_dir():
        say(f"  updating {spec.name}")
        pulled = run(["git", "-C", str(sources), "pull", "--ff-only"])
        if pulled.returncode != 0:
            notes.append(f"Update skipped: {failure_detail(pulled)}")
    else:
        if sources.exists():
            shutil.rmtree(sources, ignore_errors=True)
        sources.parent.mkdir(parents=True, exist_ok=True)
        say(f"  cloning {spec.repo}")
        cloned = run(["git", "clone", "--depth", "1", spec.repo, str(sources)])
        if cloned.returncode != 0:
            return Result(
                spec.name,
                MISSING,
                failure_detail(cloned),
                f'Clone it manually: git clone {spec.repo} "{sources}"',
                required=spec.required,
            )

    skill_dir = locate_skill_dir(sources, spec.name)
    if skill_dir is None:
        return Result(
            spec.name,
            PARTIAL,
            f"no SKILL.md found anywhere in {sources}",
            "The upstream layout changed; check the repository.",
            required=spec.required,
        )

    if skill_dir != sources:
        notes.append(f"Skill published under {skill_dir.relative_to(sources).as_posix()} in the repository.")

    try:
        materialize(skill_dir, target)
    except OSError as error:
        return Result(spec.name, MISSING, f"could not install into {target}: {error}", required=spec.required)

    if not (target / "SKILL.md").is_file():
        return Result(
            spec.name,
            PARTIAL,
            f"copied to {target} but SKILL.md is not present",
            required=spec.required,
        )
    return Result(spec.name, OK, f"installed at {target}", required=spec.required, notes=notes)


def _missing_packages(pairs) -> list[str]:
    missing = []
    for module, package in pairs:
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    return missing


def install_python_packages(check_only: bool, label: str, pairs, requirements_file: str, present: str) -> Result:
    missing = _missing_packages(pairs)
    if not missing:
        return Result(label, OK, f"{present} available")

    if check_only:
        return Result(
            label,
            MISSING,
            f"missing: {', '.join(missing)}",
            f"Run: python -m pip install -r {requirements_file}",
        )

    say(f"  installing {', '.join(missing)}")
    requirements = REPO_ROOT / requirements_file
    result = run([sys.executable, "-m", "pip", "install", "-q", "-r", str(requirements)])
    if result.returncode != 0:
        return Result(
            label,
            MISSING,
            failure_detail(result),
            f"Run: {sys.executable} -m pip install -r {requirements_file}",
        )
    return Result(label, OK, f"{present} installed")


def install_build_dependencies(check_only: bool) -> Result:
    return install_python_packages(
        check_only,
        "document builder packages",
        (("docx", "python-docx"), ("openpyxl", "openpyxl")),
        "tools/requirements-docs.txt",
        "python-docx and openpyxl",
    )


def install_handoff_dependencies(check_only: bool) -> Result:
    # referencing ships with jsonschema >= 4.18 and resolves $ref across schemas/.
    return install_python_packages(
        check_only,
        "machine handoff validator packages",
        (("jsonschema", "jsonschema"), ("referencing", "jsonschema")),
        "tools/requirements-handoff.txt",
        "jsonschema",
    )


def setup_renderer(skill_dir: Path | None, check_only: bool, skip: bool) -> Result:
    """Prepare the Excalidraw render pipeline.

    The skill documents `uv`. Where `uv` is absent, fall back to a virtual
    environment created with the running interpreter; the renderer only needs
    Playwright.
    """
    item = "Excalidraw renderer"
    if skip:
        return Result(item, SKIPPED, "skipped by --skip-renderer", required=False)
    if skill_dir is None:
        return Result(item, MISSING, "the Excalidraw skill is not installed yet")

    references = skill_dir / "references"
    script = references / "render_excalidraw.py"
    if not script.is_file():
        return Result(
            item,
            MISSING,
            f"render_excalidraw.py not found in {references}",
            "Check the upstream skill layout.",
        )

    recorded = references / "RENDER-COMMAND.txt"
    if check_only:
        if recorded.is_file():
            return Result(item, OK, recorded.read_text(encoding="utf-8").strip().splitlines()[-1])
        return Result(item, MISSING, "not set up", "Run: python tools/setup_workflow.py")

    uv = have("uv")
    if uv:
        say("  preparing the renderer with uv")
        sync = run([uv, "sync"], cwd=references)
        if sync.returncode == 0:
            browser = run([uv, "run", "playwright", "install", "chromium"], cwd=references)
            if browser.returncode == 0:
                command = f'cd "{references}" && uv run python render_excalidraw.py <file.excalidraw>'
                recorded.write_text(
                    "Render an Excalidraw diagram to PNG with:\n" + command + "\n", encoding="utf-8"
                )
                return Result(item, OK, "uv environment with Chromium ready")
            return Result(
                item,
                PARTIAL,
                "uv sync succeeded but the Chromium download failed",
                f'cd "{references}" && uv run playwright install chromium',
            )
        say("  uv could not prepare the environment; falling back to a virtual environment")

    venv = references / ".venv-render"
    python = venv / ("Scripts" if os.name == "nt" else "bin") / ("python.exe" if os.name == "nt" else "python")
    if not python.is_file():
        say("  creating a virtual environment for the renderer")
        created = run([sys.executable, "-m", "venv", str(venv)])
        if created.returncode != 0:
            return Result(item, MISSING, failure_detail(created))

    say("  installing Playwright")
    installed = run([str(python), "-m", "pip", "install", "-q", "playwright>=1.40.0"])
    if installed.returncode != 0:
        return Result(
            item,
            MISSING,
            failure_detail(installed),
            f'"{python}" -m pip install "playwright>=1.40.0"',
        )

    say("  downloading headless Chromium (this can take a few minutes)")
    browser = run([str(python), "-m", "playwright", "install", "chromium"])
    if browser.returncode != 0:
        return Result(
            item,
            PARTIAL,
            failure_detail(browser),
            f'"{python}" -m playwright install chromium',
        )

    command = f'"{python}" "{script}" <file.excalidraw>'
    recorded.write_text("Render an Excalidraw diagram to PNG with:\n" + command + "\n", encoding="utf-8")
    return Result(item, OK, "virtual environment with Chromium ready")


DRAWIO_HINTS = {
    "Windows": "winget install JGraph.Draw",
    "Darwin": "brew install --cask drawio",
    "Linux": "Download a package from https://github.com/jgraph/drawio-desktop/releases",
}

DRAWIO_PATHS = {
    "Windows": [
        Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "draw.io" / "draw.io.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "draw.io" / "draw.io.exe",
    ],
    "Darwin": [Path("/Applications/draw.io.app/Contents/MacOS/draw.io")],
    "Linux": [Path("/usr/bin/drawio"), Path("/opt/drawio/drawio")],
}


def check_drawio_cli() -> Result:
    item = "draw.io CLI (image export)"
    found = have("drawio") or have("draw.io")
    if not found:
        for candidate in DRAWIO_PATHS.get(platform.system(), []):
            if str(candidate) and candidate.is_file():
                found = str(candidate)
                break
    if found:
        return Result(item, OK, str(found), required=False)
    hint = DRAWIO_HINTS.get(platform.system(), "Install the draw.io desktop application.")
    return Result(
        item,
        MISSING,
        "not found",
        hint,
        required=False,
        notes=[
            "Diagrams can still be authored as editable .drawio files.",
            "Only PNG, SVG and PDF export needs the desktop CLI.",
        ],
    )


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------


SMOKE_DIAGRAM = {
    "type": "excalidraw",
    "version": 2,
    "source": "project-planning-workflow-setup",
    "elements": [
        {
            "id": "smoke", "type": "rectangle", "x": 100, "y": 100, "width": 200, "height": 80,
            "angle": 0, "strokeColor": "#1971c2", "backgroundColor": "#a5d8ff", "fillStyle": "solid",
            "strokeWidth": 2, "strokeStyle": "solid", "roughness": 1, "opacity": 100, "groupIds": [],
            "frameId": None, "roundness": {"type": 3}, "seed": 1, "version": 1, "versionNonce": 1,
            "isDeleted": False, "boundElements": [], "updated": 1, "link": None, "locked": False,
        }
    ],
    "appState": {"viewBackgroundColor": "#ffffff", "gridSize": None},
    "files": {},
}


def installed_skill_dirs(name: str, roots: list[Path]) -> list[Path]:
    """Every installed copy of a skill under the given roots, never a source clone."""
    found: list[Path] = []
    for root in roots:
        for candidate in (root / name, find_existing_skill(root, name)):
            if candidate and (candidate / "SKILL.md").is_file() and SOURCES_DIRNAME not in candidate.parts:
                resolved = candidate.resolve()
                if resolved not in found:
                    found.append(resolved)
    return found


def excalidraw_import(template: Path) -> str | None:
    """The Excalidraw URL a render template imports, or None when it imports none."""
    match = EXCALIDRAW_IMPORT.search(template.read_text(encoding="utf-8"))
    return match.group(3) if match else None


def pin_render_template(template: Path) -> tuple[bool, str | None]:
    """Pin an unversioned Excalidraw import to EXCALIDRAW_PIN, changing nothing else.

    Returns (changed, the URL found). An import that already names a version - ours
    or one the skill's authors chose - is left as it is.
    """
    text = template.read_bytes().decode("utf-8")  # bytes, so line endings survive untouched
    match = EXCALIDRAW_IMPORT.search(text)
    if match is None:
        return False, None
    url = match.group(3)
    if url == EXCALIDRAW_PIN or VERSIONED.search(url):
        return False, url
    pinned = text[: match.start(3)] + EXCALIDRAW_PIN + text[match.end(3):]
    template.write_bytes(pinned.encode("utf-8"))
    return True, url


def pin_renderer(skill_dirs: list[Path], check_only: bool, skip: bool) -> Result:
    """Pin the render page's Excalidraw import in every installed copy of the skill.

    Runs on every setup, so a skill sync that restores the unversioned import is
    repaired by the next run; --check reports a copy that still needs it.
    """
    item = "Excalidraw render page pin"
    if skip:
        return Result(item, SKIPPED, "skipped by --skip-renderer", required=False)
    templates = [d / RENDER_TEMPLATE for d in skill_dirs if (d / RENDER_TEMPLATE).is_file()]
    if not templates:
        return Result(item, SKIPPED, "no installed Excalidraw render page to check", required=False)

    notes: list[str] = []
    unpinned: list[tuple[Path, str]] = []
    unreadable: list[Path] = []
    for template in templates:
        url = excalidraw_import(template)
        if url is None:
            unreadable.append(template)
        elif url == EXCALIDRAW_PIN:
            continue
        elif VERSIONED.search(url):
            notes.append(f"{template}: already pinned by the skill to {url}; left as is.")
        else:
            unpinned.append((template, url))

    if unpinned and not check_only:
        for template, url in unpinned:
            try:
                pin_render_template(template)
            except OSError as error:
                return Result(item, MISSING, f"could not update {template}: {error}",
                              "Edit the import line by hand: " + EXCALIDRAW_PIN)
            notes.append(f"pinned {template} (was {url})")
            if REPO_ROOT not in template.parents:
                notes.append("  managed outside this installer: a skill sync may restore the old line; "
                             "re-run this script after syncing.")
        unpinned = []

    for template in unreadable:
        notes.append(f"{template}: no Excalidraw import found; the skill's layout changed.")
    if unpinned:
        notes += [f"{template} imports {url}" for template, url in unpinned]
        return Result(item, PARTIAL, f"{len(unpinned)} render page(s) import an unversioned Excalidraw build",
                      "Run: python tools/setup_workflow.py  (pins " + EXCALIDRAW_PIN + ")", notes=notes)
    if unreadable:
        return Result(item, PARTIAL, "a render page has no recognisable Excalidraw import",
                      "Check references/render_template.html in the skill.", notes=notes)
    return Result(item, OK, f"pinned to {EXCALIDRAW_PIN}", notes=notes)


def verify_render(skill_dir: Path | None, check_only: bool, skip: bool) -> Result:
    """Render a throwaway diagram to prove the pipeline actually works.

    The render page imports Excalidraw from a CDN at render time, so a working
    install can still fail on a restricted network or on a broken library build.
    Finding that out here beats finding it out halfway through a project.
    """
    item = "render smoke test"
    if skip or check_only:
        return Result(item, SKIPPED, "not run", required=False)
    if skill_dir is None:
        return Result(item, MISSING, "the Excalidraw skill is not installed", required=False)

    references = skill_dir / "references"
    script = references / "render_excalidraw.py"
    venv_python = references / ".venv-render" / ("Scripts" if os.name == "nt" else "bin") / (
        "python.exe" if os.name == "nt" else "python"
    )
    interpreter = str(venv_python) if venv_python.is_file() else None
    if interpreter is None and have("uv") is None:
        return Result(item, SKIPPED, "no renderer environment to test", required=False)

    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        sample = Path(tmp) / "setup-smoke-test.excalidraw"
        sample.write_text(json.dumps(SMOKE_DIAGRAM), encoding="utf-8")
        if interpreter:
            command = [interpreter, str(script), str(sample)]
            cwd = references
        else:
            command = [have("uv"), "run", "python", str(script), str(sample)]
            cwd = references
        try:
            result = run(command, cwd=cwd, timeout=180)
        except subprocess.TimeoutExpired:
            return Result(item, MISSING, "rendering timed out", required=False, notes=RENDER_NOTES)

        produced = list(Path(tmp).glob("*.png"))
        if produced and produced[0].stat().st_size > 0:
            return Result(item, OK, f"rendered a {produced[0].stat().st_size} byte PNG", required=False)

        detail = failure_detail(result) if result.returncode != 0 else "no PNG was produced"
        if "Timeout" in (result.stderr or "") + (result.stdout or ""):
            detail = "the render page never finished loading"
        return Result(item, MISSING, detail, required=False, notes=RENDER_NOTES)


RENDER_NOTES = [
    "The render page imports Excalidraw from a CDN at render time; it should be pinned to",
    f"{EXCALIDRAW_PIN} (see 'Excalidraw render page pin' above).",
    "If it is pinned and still never loads, check that the headless browser can reach cdn.jsdelivr.net.",
    "Diagrams can still be authored; only the mandatory render-and-inspect loop is affected.",
]


def check_python_for_skills() -> Result:
    """The draw.io skill drives `scripts/diagramctl.py` and expects a Python 3."""
    item = "python3 for the draw.io skill"
    for candidate in ("python3", "python"):
        if not have(candidate):
            continue
        # On Windows, `python3` can resolve to a Microsoft Store alias that is not
        # an interpreter at all, so actually execute it before believing it.
        probe = run([candidate, "-c", "import sys; print('.'.join(map(str, sys.version_info[:3])))"])
        version = probe.stdout.strip()
        if probe.returncode != 0 or not version or not version[0].isdigit():
            continue
        if candidate == "python3":
            return Result(item, OK, f"python3 -> {version}", required=False)
        return Result(
            item,
            OK,
            f"python -> {version}",
            required=False,
            notes=["`python3` is not a working command here; use `python` when running the skill's scripts."],
        )
    return Result(
        item,
        MISSING,
        "no Python interpreter on PATH",
        "Install Python 3 and make sure it is on PATH.",
        required=False,
    )


def check_graphviz() -> Result:
    item = "Graphviz (draw.io auto-layout)"
    path = have("dot")
    if path:
        return Result(item, OK, str(path), required=False)
    hints = {
        "Windows": "winget install Graphviz.Graphviz",
        "Darwin": "brew install graphviz",
        "Linux": "sudo apt install graphviz",
    }
    return Result(
        item,
        MISSING,
        "not found",
        hints.get(platform.system(), "Install Graphviz."),
        required=False,
        notes=["Only the draw.io skill's automatic layout needs it."],
    )


SYMBOLS = {OK: "[ok]", MISSING: "[--]", PARTIAL: "[~ ]", SKIPPED: "[  ]"}


def report(results: list[Result], root: Path, check_only: bool) -> int:
    width = max(len(r.item) for r in results) + 2
    say()
    say("Project Planning Workflow - readiness")
    say(f"Skills directory: {root}")
    say("-" * (width + 46))
    for result in results:
        label = "" if result.required else " (optional)"
        say(f"{SYMBOLS[result.status]} {result.item.ljust(width)}{result.detail}{label}")
        for note in result.notes:
            say(f"     {note}")
        if result.status in (MISSING, PARTIAL) and result.hint:
            say(f"     fix: {result.hint}")
    say("-" * (width + 46))

    blocking = [r for r in results if r.required and r.status in (MISSING, PARTIAL)]
    optional_gaps = [r for r in results if not r.required and r.status == MISSING]

    if blocking:
        say(f"{len(blocking)} required item(s) still missing.")
        if check_only:
            say("Run `python tools/setup_workflow.py` to install them.")
        return 1

    say("All required components are ready.")
    if optional_gaps:
        say(f"{len(optional_gaps)} optional item(s) unavailable; see the notes above.")
    say()
    say("Next: open this workflow with your assistant and start discovery.")
    say("Diagram generation is described in WORKFLOW.md section 21.")
    return 0


def write_state(root: Path, results: list[Result]) -> None:
    state = {
        "skills_directory": str(root),
        "python": sys.executable,
        "platform": platform.platform(),
        "items": {r.item: {"status": r.status, "detail": r.detail} for r in results},
    }
    path = REPO_ROOT / "tools" / ".workflow-setup.json"
    try:
        path.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except OSError:
        pass


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true", help="Report readiness without changing anything")
    parser.add_argument(
        "--scope",
        choices=["user", "project"],
        default="user",
        help="Install skills for the whole account (default) or only inside this repository",
    )
    parser.add_argument("--skills-dir", type=Path, default=None, help="Explicit skills directory")
    parser.add_argument("--no-update", action="store_true", help="Do not pull updates for skills already installed")
    parser.add_argument("--offline", action="store_true", help="Do not use the network")
    parser.add_argument("--skip-renderer", action="store_true", help="Skip the Excalidraw render pipeline setup")
    args = parser.parse_args(argv)

    root = skills_root(args.scope, args.skills_dir)
    other = skills_root("project" if args.scope == "user" else "user", None)
    also_search = [other] if args.skills_dir is None and other != root else []
    if not args.check:
        say(f"Provisioning into {root}")

    results: list[Result] = []
    if not args.check:
        results.append(check_git())

    excalidraw_dir: Path | None = None
    for spec in SKILLS:
        result = install_skill(spec, root, args.check, not args.no_update, args.offline, also_search)
        result.item = f"{spec.name} - {spec.purpose}"
        results.append(result)
        if spec.name == "excalidraw-diagram" and result.status == OK:
            excalidraw_dir = find_existing_skill(root, spec.name)
            for alternate in also_search:
                if excalidraw_dir:
                    break
                excalidraw_dir = find_existing_skill(alternate, spec.name)

    results.append(install_build_dependencies(args.check))
    results.append(install_handoff_dependencies(args.check))
    # Pin before preparing and smoke-testing the renderer, so the test exercises the pinned page.
    results.append(pin_renderer(installed_skill_dirs("excalidraw-diagram", [root, *also_search]),
                                args.check, args.skip_renderer))
    results.append(setup_renderer(excalidraw_dir, args.check, args.skip_renderer))
    results.append(verify_render(excalidraw_dir, args.check, args.skip_renderer))
    results.append(check_python_for_skills())
    results.append(check_drawio_cli())
    results.append(check_graphviz())

    code = report(results, root, args.check)
    if not args.check:
        write_state(root, results)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
