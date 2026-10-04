"""A read-only web UI for the Project Planning Workflow.

It shows the workflow method (stages, gates, templates, tools) and every
project's state, records and validation results. It never writes to a project:
all data comes from the pure, in-memory functions in tools/ (check_gates.evaluate
and the handoff builders), never from the CLIs that write reports.

Run:  python -m webui --sample
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = REPO_ROOT / "tools"
SAMPLE_PROJECT = TOOLS_DIR / "tests" / "fixtures" / "sample-project"

if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))
