from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
REPO_ROOT = STANDALONE_ROOT.parents[1]
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))

from sram_layoutgen.openyield_adapter.array_aggregation import (  # noqa: E402
    ALLOWED_AGGREGATION_MACROS,
    EXCLUDED_PERIPHERAL_MACROS,
    build_limited_array_aggregation,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test limited OpenYield bitcell/dummy/replica aggregation planning.")
    parser.add_argument("--rows", type=int, default=2)
    parser.add_argument("--cols", type=int, default=16)
    parser.add_argument("--gds-pin-audit", default="docs/openyield_gds_pin_audit_report.json")
    parser.add_argument("--out-json", default="docs/openyield_limited_array_aggregation_report.json")
    parser.add_argument("--out-md", default="docs/openyield_limited_array_aggregation_report.md")
    parser.add_argument("--enable-openyield-array-aggregation", action="store_true")
    args = parser.parse_args()

    audit_path = resolve_input(args.gds_pin_audit)
    disabled = build_limited_array_aggregation(args.rows, args.cols, gds_pin_audit_path=audit_path)
    enabled = build_limited_array_aggregation(
        args.rows,
        args.cols,
        enable_openyield_array_aggregation=args.enable_openyield_array_aggregation,
        gds_pin_audit_path=audit_path,
    )
    report = {
        "enable_openyield_array_aggregation_requested": args.enable_openyield_array_aggregation,
        "default_disabled_check": disabled.to_dict(),
        "enabled_plan": enabled.to_dict(),
        "rows": args.rows,
        "cols": args.cols,
        "allowed_macros": ALLOWED_AGGREGATION_MACROS,
        "excluded_peripheral_macros": EXCLUDED_PERIPHERAL_MACROS,
        "changed_gds_flow": False,
        "generated_gds": False,
        "smoke_checks": smoke_checks(disabled.to_dict(), enabled.to_dict(), args.enable_openyield_array_aggregation),
    }
    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    out_md.write_text(format_markdown(report), encoding="utf-8", newline="\n")
    assert all(item["passed"] for item in report["smoke_checks"]), "one or more smoke checks failed"
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(
        "enabled="
        f"{enabled.enabled} plans={len(enabled.plans)} "
        f"placements={sum(len(plan.placements) for plan in enabled.plans)} generated_gds=False"
    )
    return 0


def smoke_checks(disabled: dict[str, Any], enabled: dict[str, Any], requested: bool) -> list[dict[str, Any]]:
    enabled_macros = {
        placement["macro_name"]
        for plan in enabled.get("plans", [])
        for placement in plan.get("placements", [])
    }
    disallowed = set(EXCLUDED_PERIPHERAL_MACROS) & enabled_macros
    expected_count = 0
    if requested:
        rows = int(enabled["rows"])
        cols = int(enabled["cols"])
        expected_count = rows * cols + cols + rows + rows
    actual_count = sum(len(plan.get("placements", [])) for plan in enabled.get("plans", []))
    return [
        {
            "name": "default_disabled_keeps_empty_plan",
            "passed": disabled.get("enabled") is False and not disabled.get("plans"),
        },
        {
            "name": "explicit_switch_controls_enabled_plan",
            "passed": enabled.get("enabled") is requested,
        },
        {
            "name": "only_allowed_macros_present",
            "passed": enabled_macros <= set(ALLOWED_AGGREGATION_MACROS),
            "observed_macros": sorted(enabled_macros),
        },
        {
            "name": "peripheral_macros_excluded",
            "passed": not disallowed,
            "disallowed_observed": sorted(disallowed),
        },
        {
            "name": "placement_count_matches_expected",
            "passed": (actual_count == expected_count) if requested else (actual_count == 0),
            "expected": expected_count,
            "actual": actual_count,
        },
        {
            "name": "gds_flow_unchanged",
            "passed": enabled.get("changed_gds_flow") is False,
        },
    ]


def format_markdown(report: dict[str, Any]) -> str:
    enabled = report["enabled_plan"]
    plan_rows = [
        [
            plan["role"],
            plan["cell_macro"],
            plan["rows"],
            plan["cols"],
            len(plan["placements"]),
            plan["width"],
            plan["height"],
            plan["power_rail_policy"],
            "; ".join(plan["notes"]) or "-",
        ]
        for plan in enabled.get("plans", [])
    ]
    return "\n".join(
        [
            "# OpenYield Limited Array Aggregation Report",
            "",
            "This smoke report builds a metadata-only aggregation plan for audited storage-array cells. It does not generate GDS, alter placement, merge rails, or touch peripheral macros.",
            "",
            "## Summary",
            "",
            f"- requested enable_openyield_array_aggregation: `{report['enable_openyield_array_aggregation_requested']}`",
            f"- default disabled keeps empty plan: `{report['default_disabled_check']['enabled'] is False and not report['default_disabled_check']['plans']}`",
            f"- enabled plan active: `{enabled['enabled']}`",
            f"- rows: `{report['rows']}`",
            f"- cols: `{report['cols']}`",
            f"- changed GDS flow: `{report['changed_gds_flow']}`",
            f"- generated GDS: `{report['generated_gds']}`",
            f"- allowed macros: `{', '.join(report['allowed_macros'])}`",
            "",
            "## Plans",
            "",
            md_table(
                ["role", "macro", "rows", "cols", "instances", "width", "height", "power policy", "notes"],
                plan_rows,
            )
            if plan_rows
            else "none",
            "",
            "## Excluded Macros",
            "",
            md_table(
                ["macro", "reason"],
                [[name, reason] for name, reason in sorted(report["excluded_peripheral_macros"].items())],
            ),
            "",
            "## Smoke Checks",
            "",
            md_table(
                ["check", "passed", "details"],
                [
                    [
                        item["name"],
                        item["passed"],
                        ", ".join(f"{k}={v}" for k, v in item.items() if k not in {"name", "passed"}) or "-",
                    ]
                    for item in report["smoke_checks"]
                ],
            ),
        ]
    )


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(out)


def resolve_input(value: str) -> Path:
    path = Path(value)
    if path.exists():
        return path
    for base in (Path.cwd(), STANDALONE_ROOT, REPO_ROOT):
        candidate = base / value
        if candidate.exists():
            return candidate
    return path


def resolve_output(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if Path.cwd().resolve() == REPO_ROOT.resolve():
        return STANDALONE_ROOT / value
    return Path.cwd() / value


if __name__ == "__main__":
    raise SystemExit(main())
