#!/usr/bin/env python3
"""analyze-change-impact: what a change affects, what is now stale or invalid, and what must be reviewed.

A change is never a text edit. This command analyses a recorded change
(``changes/CHANGE-###.md``), or a what-if change to any record, through the
links the records hold — not through keyword matching — and writes the impact
report. It changes no source record; review states are derived from the
change records, and only a person's disposition in the change record clears
them.

Steps, in order:
     1. identify the changed artifacts
     2. load the relationships between records
     3. detect direct dependencies
     4. detect downstream dependencies
     5. detect upstream assumptions
     6. classify impact (DIRECT / INDIRECT / POTENTIAL; CONFIRMED / LIKELY / POSSIBLE)
     7. calculate severity
     8. mark affected items for review (only once the change is APPROVED)
     9. withdraw readiness where necessary
    10. generate the impact report

Usage:
    python tools/analyze_change_impact.py projects/<project> CHANGE-007
    python tools/analyze_change_impact.py projects/<project> FR-021 --type REQUIREMENT_CHANGE   # what-if
    python tools/analyze_change_impact.py projects/<project> --detect
    python tools/analyze_change_impact.py projects/<project> --baseline --reason "Specification 1.0 approved"
    python tools/analyze_change_impact.py projects/<project> --summary

Writes changes/CHANGE-###-impact-report.md for a recorded change and
reports/impact-<IDs>.md for a what-if, unless --no-write is given. Exit code
0 on success, 1 when --baseline is refused, 2 when the tool cannot run.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import change_impact as ci  # noqa: E402
import generate_handoff as gh  # noqa: E402
import planning_records as pr  # noqa: E402
import validate_handoff as vh  # noqa: E402


def now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def load(project: Path):
    docs, src, bundle = gh.build(project, now())
    return docs, src, bundle


def print_entry(entry: dict, ctx: ci.SourceContext) -> None:
    changed = entry.get("changed_artifacts") or []
    affected = entry.get("affected") or []
    level = lambda name: [a for a in affected if a["level"] == name]  # noqa: E731
    print(f" 1. Changed artifacts         {', '.join(changed) or 'none'}"
          + "".join(f"  [{ctx.detected[c]['change']} since baseline]" for c in changed if c in ctx.detected))
    print(" 2. Relationships             loaded from the records (requirements, workflows, entities, modules, ADRs, "
          "features, tasks, tests, phases, registers, detail records)")
    print(f" 3. Direct dependencies       {len(level('DIRECT'))}")
    print(f" 4. Downstream dependencies   {len(level('INDIRECT'))}")
    upstream = [a for a in level("POTENTIAL") if a["reason"].startswith("upstream")]
    print(f" 5. Upstream assumptions      {len(upstream)}")
    confirmed = sum(1 for a in affected if a["confidence"] == "CONFIRMED")
    print(f" 6. Classified                {len(level('DIRECT'))} direct, {len(level('INDIRECT'))} indirect, "
          f"{len(level('POTENTIAL'))} potential ({confirmed} confirmed)")
    print(f" 7. Severity                  {entry['computed_severity']}" +
          (f" (declared {entry['declared_severity']})" if entry.get("declared_severity") else ""))
    for driver in entry.get("severity_drivers") or []:
        print(f"      - {driver}")
    marked = [a["id"] for a in affected if a["review_state"] != "CURRENT"]
    if entry.get("marks_plan"):
        print(f" 8. Marked for review         {len(marked)}: {', '.join(marked) or 'none'}")
    else:
        print(f" 8. Marked for review         none — the change is {entry.get('status')}; the authoritative plan changes "
              f"only once it is APPROVED")
    print(f" 9. Readiness withdrawn       {', '.join(entry.get('invalidated_items') or []) or 'none'}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Analyse the impact of a change on the plan.")
    parser.add_argument("project", type=Path)
    parser.add_argument("ids", nargs="*", help="CHANGE-### to analyse a recorded change, or record IDs for a what-if")
    parser.add_argument("--type", dest="change_type", choices=ci.CHANGE_TYPES, help="Change type for a what-if analysis")
    parser.add_argument("--detect", action="store_true", help="List records changed since the baseline")
    parser.add_argument("--baseline", action="store_true", help="Record the current records as the trusted baseline")
    parser.add_argument("--reason", default="", help="Why the baseline is recorded (with --baseline)")
    parser.add_argument("--summary", action="store_true", help="Print the project's change state")
    parser.add_argument("--no-write", action="store_true")
    args = parser.parse_args(argv)

    project = args.project.resolve()
    if not (project / pr.STATE_FILE).is_file():
        print(f"{args.project} has no {pr.STATE_FILE}; is it a project folder?", file=sys.stderr)
        return 2
    try:
        docs, _, bundle = load(project)
    except vh.SchemaUnavailable as exc:
        print(str(exc), file=sys.stderr)
        return 2
    doc = docs["changes.json"]
    ctx = ci.source_context(project)

    if args.baseline:
        return make_baseline(project, bundle, doc, args.reason)
    if args.detect:
        return detect(doc)
    if args.summary:
        print(f"Change state for {args.project}")
        for key, value in doc["summary"].items():
            print(f"  {key.replace('_', ' ').capitalize():<22} {value}")
        return 0
    if not args.ids:
        parser.error("name a CHANGE-### or record IDs, or use --detect, --baseline or --summary")

    changes = {c["change_id"]: c for c in doc["changes"]}
    if len(args.ids) == 1 and pr.kind_of(args.ids[0]) == "CHANGE":
        entry = changes.get(args.ids[0])
        if entry is None:
            print(f"{args.ids[0]} is not recorded in changes/.", file=sys.stderr)
            return 2
        out = project / "changes" / f"{entry['change_id']}{ci.REPORT_SUFFIX}"
    else:
        unknown = [i for i in args.ids if pr.kind_of(i) is None or (bundle.known(i) is False and i not in ctx.detected)]
        if unknown:
            print(f"Not defined in any record: {', '.join(unknown)}", file=sys.stderr)
            return 2
        record = {"change_id": None, "title": "What-if analysis", "status": "PROPOSED", "change_type": args.change_type,
                  "changed_artifacts": list(args.ids), "declared_severity": None, "dispositions": {}}
        entry = ci.analyse_change(record, bundle, ci.Graph(bundle, ctx.details), ctx)
        out = project / "reports" / f"impact-{'-'.join(args.ids)}.md"

    title = entry.get("change_id") or "What-if"
    print(f"analyze-change-impact: {title} ({entry.get('change_type') or 'type not stated'})")
    print_entry(entry, ctx)
    accepted = [i for i in entry.get("changed_artifacts") or [] if bundle.adr_by_id.get(i, {}).get("status") == "accepted"]
    if accepted:
        print(f"      {', '.join(accepted)} ACCEPTED: supersede with a new ADR rather than editing the decision.")
    if bundle.spec_approved and min((ci.KIND_GATE.get(pr.kind_of(i) or "", ci.LAST_GATE) for i in entry.get("changed_artifacts") or []),
                                    default=ci.LAST_GATE) <= ci.APPROVAL_GATE:
        print("      The approved specification is affected: record the change, obtain approval, and re-approve before "
              "affected tasks return to READY.")
    gates = entry.get("rerun_gates") or []
    if not args.no_write:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(ci.impact_report(entry, bundle, ctx.detected, now()), encoding="utf-8", newline="\n")
        print(f"10. Impact report             {pr.rel(project, out)}")
    else:
        print("10. Impact report             not written (--no-write)")
    if gates:
        print(f"    Re-run {gates[0]} to {gates[-1]} and GC.")
    return 0


def detect(doc: dict) -> int:
    baseline = doc["baseline"]
    if not baseline["exists"]:
        print(f"No baseline ({pr.BASELINE_FILE}); nothing can be detected. Record one with --baseline.")
        return 0
    print(f"Changes since the baseline of {baseline['created_at']} (specification {baseline['specification_version']}):")
    unrecorded = {u["id"]: u for u in doc["unrecorded_changes"]}
    for item in doc["detected_changes"]:
        flag = ""
        if item["id"] in unrecorded:
            covered = unrecorded[item["id"]]["covered_by"]
            flag = f"  UNRECORDED{' — ' + ', '.join(covered) + ' not approved' if covered else ''}"
        print(f"  {item['id']:<14} {item['change']:<9} {item['source_path']}{flag}")
    if not doc["detected_changes"]:
        print("  none")
    return 0


def make_baseline(project: Path, bundle, doc: dict, reason: str) -> int:
    problems = []
    for entry in doc["unrecorded_changes"]:
        problems.append(f"{entry['id']} changed without an approved change record")
    for change in doc["changes"]:
        if change["status"] in ("APPROVED",):
            problems.append(f"{change['change_id']} is approved but not yet IMPLEMENTED_IN_PLAN")
        if change["status"] == "IMPLEMENTED_IN_PLAN" and change.get("review_required"):
            problems.append(f"{change['change_id']} still has affected artifacts under review")
    if problems:
        print("Baseline refused: the plan is not in a trusted state.", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return 1
    previous = ci.load_baseline(project) or {}
    implemented = [c["change_id"] for c in doc["changes"] if c["status"] == "IMPLEMENTED_IN_PLAN"]
    path = ci.write_baseline(project, ci.snapshot(project), bundle.project.get("version"),
                             list(previous.get("incorporated_changes") or []) + implemented,
                             reason or "Baseline recorded")
    records = ci.load_baseline(project)["records"]
    print(f"Baseline written to {pr.rel(project, path)}: {len(records)} change-controlled records"
          + (f"; previous baseline archived in {ci.HISTORY_DIR}/" if previous else "") + ".")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
