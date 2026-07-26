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
    build_standalone_storage_array_aggregation,
    load_ready_storage_macro_specs,
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
    standalone_disabled = build_standalone_storage_array_aggregation(args.rows, args.cols)
    standalone_enabled = build_standalone_storage_array_aggregation(
        args.rows,
        args.cols,
        enable_openyield_array_aggregation=args.enable_openyield_array_aggregation,
        gds_pin_audit_path=audit_path,
        origins=standalone_origins(args.rows, args.cols, audit_path),
    )
    metadata_count = sum(len(plan.placements) for plan in enabled.plans)
    standalone_count = sum(plan.rows * plan.cols for plan in standalone_enabled.plans)
    report = {
        "enable_openyield_array_aggregation_requested": args.enable_openyield_array_aggregation,
        "default_disabled_check": disabled.to_dict(),
        "enabled_plan": enabled.to_dict(),
        "standalone_integration": {
            "enabled": standalone_enabled.enabled,
            "default_closed_old_behavior_preserved": (not standalone_disabled.enabled and not standalone_disabled.plans),
            "storage_placement_replaced": standalone_enabled.enabled,
            "only_storage_placement_replaced": True,
            "plans": standalone_enabled.to_dict()["plans"],
            "macro_list": sorted(
                {
                    plan.cell_macro
                    for plan in standalone_enabled.plans
                }
            ),
            "macro_counts": macro_counts(standalone_enabled),
            "instance_count": standalone_count,
            "bbox_pitch_origin": bbox_pitch_origin(standalone_enabled),
            "peripherals_old_path": True,
            "generated_gds": False,
            "routing_changed": standalone_enabled.routing_changed,
            "shared_rail_merge": standalone_enabled.shared_rail_merge,
            "power_rail_policy": standalone_enabled.power_rail_policy,
            "metadata_only_plan_count": metadata_count,
            "match_against_metadata_only_plan_count": standalone_count == metadata_count,
            "metadata_count_note": (
                "metadata-only plan includes a dummy row; standalone integration preserves "
                "the existing bitcell + left dummy + right dummy + replica column topology."
            ),
        },
        "rows": args.rows,
        "cols": args.cols,
        "allowed_macros": ALLOWED_AGGREGATION_MACROS,
        "excluded_peripheral_macros": EXCLUDED_PERIPHERAL_MACROS,
        "changed_gds_flow": False,
        "generated_gds": False,
        "smoke_checks": smoke_checks(
            disabled.to_dict(),
            enabled.to_dict(),
            args.enable_openyield_array_aggregation,
            standalone_disabled.to_dict(),
            standalone_enabled.to_dict(),
        ),
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


def smoke_checks(
    disabled: dict[str, Any],
    enabled: dict[str, Any],
    requested: bool,
    standalone_disabled: dict[str, Any],
    standalone_enabled: dict[str, Any],
) -> list[dict[str, Any]]:
    enabled_macros = {
        placement["macro_name"]
        for plan in enabled.get("plans", [])
        for placement in plan.get("placements", [])
    }
    standalone_macros = {plan["cell_macro"] for plan in standalone_enabled.get("plans", [])}
    disallowed = set(EXCLUDED_PERIPHERAL_MACROS) & enabled_macros
    standalone_disallowed = set(EXCLUDED_PERIPHERAL_MACROS) & standalone_macros
    expected_count = 0
    if requested:
        rows = int(enabled["rows"])
        cols = int(enabled["cols"])
        expected_count = rows * cols + cols + rows + rows
    actual_count = sum(len(plan.get("placements", [])) for plan in enabled.get("plans", []))
    standalone_count = sum(int(plan.get("rows", 0)) * int(plan.get("cols", 0)) for plan in standalone_enabled.get("plans", []))
    expected_standalone_count = int(standalone_enabled.get("rows", 0)) * int(standalone_enabled.get("cols", 0)) + 3 * int(standalone_enabled.get("rows", 0)) if requested else 0
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
        {
            "name": "standalone_default_disabled_keeps_legacy_path",
            "passed": standalone_disabled.get("enabled") is False and not standalone_disabled.get("plans"),
        },
        {
            "name": "standalone_only_allowed_storage_macros_present",
            "passed": standalone_macros <= set(ALLOWED_AGGREGATION_MACROS),
            "observed_macros": sorted(standalone_macros),
        },
        {
            "name": "standalone_peripheral_macros_excluded",
            "passed": not standalone_disallowed,
            "disallowed_observed": sorted(standalone_disallowed),
        },
        {
            "name": "standalone_storage_instance_count_matches_existing_topology",
            "passed": standalone_count == expected_standalone_count,
            "expected": expected_standalone_count,
            "actual": standalone_count,
        },
        {
            "name": "standalone_gds_and_routing_flow_unchanged",
            "passed": standalone_enabled.get("changed_gds_flow") is False
            and standalone_enabled.get("routing_changed") is False
            and standalone_enabled.get("shared_rail_merge") is False,
        },
    ]


def format_markdown(report: dict[str, Any]) -> str:
    enabled = report["enabled_plan"]
    standalone = report["standalone_integration"]
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
    standalone_rows = [
        [
            plan["array_name"],
            plan["role"],
            plan["cell_macro"],
            plan["rows"],
            plan["cols"],
            plan["pitch_x"],
            plan["pitch_y"],
            plan["orientation"],
            plan["power_rail_policy"],
        ]
        for plan in standalone.get("plans", [])
    ]
    return "\n".join(
        [
            "# OpenYield Array Aggregation Integration Report",
            "",
            "This smoke report covers the metadata-only OpenYield plan and the limited standalone storage-array integration path. It does not generate GDS, alter routing, merge rails, or touch peripheral macros.",
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
            f"- standalone storage placement replaced: `{standalone['storage_placement_replaced']}`",
            f"- standalone instance count: `{standalone['instance_count']}`",
            f"- metadata-only plan count: `{standalone['metadata_only_plan_count']}`",
            f"- count matches metadata-only plan: `{standalone['match_against_metadata_only_plan_count']}`",
            "",
            "## Metadata-Only Plans",
            "",
            md_table(
                ["role", "macro", "rows", "cols", "instances", "width", "height", "power policy", "notes"],
                plan_rows,
            )
            if plan_rows
            else "none",
            "",
            "## Standalone Storage Integration",
            "",
            md_table(
                ["array", "role", "macro", "rows", "cols", "pitch_x", "pitch_y", "orientation", "power policy"],
                standalone_rows,
            )
            if standalone_rows
            else "none",
            "",
            f"Count note: {standalone['metadata_count_note']}",
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


def standalone_origins(rows: int, cols: int, audit_path: Path) -> dict[str, tuple[float, float]]:
    specs = load_ready_storage_macro_specs(audit_path)
    bitcell_w = specs["cell_1rw"]["width"]
    dummy_w = specs["dummy_cell_1rw"]["width"]
    replica_w = specs["replica_cell_1rw"]["width"]
    return {
        "bitcell_array": (0.0, 0.0),
        "dummy_left_array": (-dummy_w, 0.0),
        "replica_bitline_array": (cols * bitcell_w, 0.0),
        "dummy_right_array": (cols * bitcell_w + replica_w, 0.0),
    }


def macro_counts(result: Any) -> dict[str, int]:
    counts: dict[str, int] = {}
    for plan in result.plans:
        counts[plan.cell_macro] = counts.get(plan.cell_macro, 0) + plan.rows * plan.cols
    return counts


def bbox_pitch_origin(result: Any) -> dict[str, Any]:
    if not result.plans:
        return {}
    return {
        plan.array_name: {
            "origin": {"x": plan.origin_x, "y": plan.origin_y},
            "pitch": {"x": plan.pitch_x, "y": plan.pitch_y},
            "width": plan.width,
            "height": plan.height,
        }
        for plan in result.plans
    }


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
