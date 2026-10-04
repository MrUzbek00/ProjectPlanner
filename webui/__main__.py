"""python -m webui — serve the read-only Project Planning Workflow UI locally."""

from __future__ import annotations

import argparse
from pathlib import Path

from . import REPO_ROOT
from .app import create_app, default_registry


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Serve the read-only Project Planning Workflow UI.")
    parser.add_argument("--projects-dir", type=Path, default=REPO_ROOT / "projects",
                        help="Folder whose sub-folders with a project-state.md are projects (default: projects/)")
    parser.add_argument("--project", type=Path, action="append", default=[],
                        help="An additional project folder to show; may be repeated")
    parser.add_argument("--sample", action="store_true",
                        help="Also show the committed sample project (tools/tests/fixtures/sample-project)")
    parser.add_argument("--host", default="127.0.0.1", help="Interface to bind (default: 127.0.0.1, local only)")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true", help="Flask debug mode with auto-reload")
    args = parser.parse_args(argv)

    app = create_app(default_registry(args.projects_dir.resolve(), args.project, args.sample))
    print(f"Project Planning Workflow UI on http://{args.host}:{args.port}/  (read-only; Ctrl+C to stop)")
    app.run(host=args.host, port=args.port, debug=args.debug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
