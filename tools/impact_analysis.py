#!/usr/bin/env python3
"""Impact analysis of one or more records — the what-if form of analyze-change-impact.

Kept for existing commands and scripts. It runs the same analysis as
``tools/analyze_change_impact.py`` without a change record: what the change
would reach, classified DIRECT / INDIRECT / POTENTIAL with confidence, its
severity, the gates to re-run, and the report in reports/impact-<IDs>.md.
It changes nothing. To change the plan, record a CHANGE-### and analyse that.

Usage:
    python tools/impact_analysis.py projects/<project> FR-014
    python tools/impact_analysis.py projects/<project> FR-014 RULE-003 --no-write
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_change_impact as aci  # noqa: E402
import change_impact as ci  # noqa: E402

Graph = ci.Graph
KIND_GATE = ci.KIND_GATE


def main(argv: list[str] | None = None) -> int:
    return aci.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
