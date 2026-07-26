from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.writedriver_adapter import (  # noqa: E402
    build_writedriver_adapter,
    classify_writedriver_power_status,
    inspect_local_writedriver_macro,
)
from sram_layoutgen.openyield_adapter.writedriver_placement import build_writedriver_limited_placement_plan  # noqa: E402


DEFAULT_CONTRACTS = Path("docs/openyield_module_contracts.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a limited write_driver placement plan smoke report.")
    parser.add_argument("--cols", type=int, required=True)
    parser.add_argument("--mux-ratio", type=int, required=True)
    parser.add_argument("--origin-x", type=float, required=True)
    parser.add_argument("--origin-y", type=float, required=True)
    parser.add_argument("--pitch-x", type=float, required=True)
    parser.add_argument("--extra-cols", type=int)
    parser.add_argument("--extra-mux-ratio", type=int)
    parser.add_argument("--contracts", default=str(DEFAULT_CONTRACTS))
    parser.add_argument("--tech-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    contracts_path = resolve_path(args.contracts)
    tech_dir = resolve_path(args.tech_dir)
    contracts = json.loads(contracts_path.read_text(encoding="utf-8"))
    contract = find_contract(contracts, "WRITEDRIVER")
    local_macro = inspect_local_writedriver_macro(tech_dir)
    power_status = classify_writedriver_power_status(local_macro, contract)
    adapter = build_writedriver_adapter(local_macro, contract)

    primary_plan = build_writedriver_limited_placement_plan(
        cols=args.cols,
        mux_ratio=args.mux_ratio,
        origin_x=args.origin_x,
        origin_y=args.origin_y,
        pitch_x=args.pitch_x,
        power_status=power_status,
        safe_for_physical_mapping=adapter.safe_for_physical_mapping,
        safe_for_shared_rail=adapter.safe_for_shared_rail,
        use_grouped_semantics=args.mux_ratio > 1,
    )
    primary_case = summarize_plan("primary", primary_plan, adapter)

    extra_case = None
    if args.extra_cols and args.extra_mux_ratio:
        extra_origin_x = args.origin_x
        extra_origin_y = args.origin_y
        extra_pitch_x = args.pitch_x * max(1, args.extra_mux_ratio)
        extra_plan = build_writedriver_limited_placement_plan(
            cols=args.extra_cols,
            mux_ratio=args.extra_mux_ratio,
            origin_x=extra_origin_x,
            origin_y=extra_origin_y,
            pitch_x=extra_pitch_x,
            power_status=power_status,
            safe_for_physical_mapping=adapter.safe_for_physical_mapping,
            safe_for_shared_rail=adapter.safe_for_shared_rail,
            use_grouped_semantics=True,
        )
        extra_case = summarize_plan("extra_grouped", extra_plan, adapter)

    report = {
        "scope": "step5_10_writedriver_placement_smoke",
        "inputs": {
            "contracts": str(contracts_path.resolve()),
            "tech_dir": str(tech_dir.resolve()),
            "cols": args.cols,
            "mux_ratio": args.mux_ratio,
            "origin_x": args.origin_x,
            "origin_y": args.origin_y,
            "pitch_x": args.pitch_x,
            "extra_cols": args.extra_cols,
            "extra_mux_ratio": args.extra_mux_ratio,
        },
        "power_status": power_status,
        "adapter": adapter.to_dict(),
        "primary_plan": primary_case,
        "extra_plan": extra_case,
        "safe_for_physical_mapping": adapter.safe_for_physical_mapping,
        "safe_for_shared_rail": adapter.safe_for_shared_rail,
        "can_enter_writedriver_limited_placement": adapter.safe_for_physical_mapping and not adapter.safe_for_shared_rail,
        "semantic_coexistence": {
            "with_columnmux": True,
            "with_senseamp": True,
            "with_storage_array": True,
            "reason": "placement planning is metadata-only and leaves routing/shared rails untouched.",
        },
        "standalone_modified": False,
        "routing_changed": False,
        "gds_writer_changed": False,
        "write_driver_changed": False,
        "notes": list(adapter.notes) + [
            "This smoke is metadata-only and does not modify standalone, routing, or GDS writer code.",
            "The physical write path is intentionally left untouched.",
        ],
    }

    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(report), encoding="utf-8")
    print(
        "primary_ok={primary} limited={limited} grouped_confirmation={grouped}".format(
            primary=primary_case["generated_gds_like"] if "generated_gds_like" in primary_case else True,
            limited=report["can_enter_writedriver_limited_placement"],
            grouped=primary_case["grouped_write_mapping_needs_confirmation"],
        )
    )
    return 0


def summarize_plan(name: str, plan, adapter) -> dict[str, Any]:
    placements = [item.to_dict() for item in plan.placements]
    gds_like = True
    grouped_confirmation = any("grouped_write_mapping_needs_confirmation" in note for note in plan.notes)
    return {
        "name": name,
        "cols": plan.cols,
        "mux_ratio": plan.mux_ratio,
        "macro_name": plan.macro_name,
        "power_status": plan.power_status,
        "safe_for_physical_mapping": plan.safe_for_physical_mapping,
        "safe_for_shared_rail": plan.safe_for_shared_rail,
        "placement_count": len(placements),
        "placements": placements,
        "example_placements": placements[:3],
        "generated_gds_like": gds_like,
        "grouped_write_mapping_needs_confirmation": grouped_confirmation,
        "notes": list(plan.notes) + [
            "Placement planning is adapter-only and does not emit GDS or change the main flow.",
        ],
        "expected_mapping": {
            "VDD": "vdd",
            "VSS": "gnd",
            "EN": "write_enable",
            "DIN": "din",
            "BL": "bl",
            "BLB": "br",
        },
    }


def render_markdown(report: dict[str, Any]) -> str:
    primary = report["primary_plan"]
    lines = [
        "# OpenYield WRITEDRIVER Placement Smoke Report",
        "",
        f"- power status: `{report['power_status']}`",
        f"- safe_for_physical_mapping: `{report['safe_for_physical_mapping']}`",
        f"- safe_for_shared_rail: `{report['safe_for_shared_rail']}`",
        f"- can enter limited placement: `{report['can_enter_writedriver_limited_placement']}`",
        f"- semantic coexistence with column mux / sense amp / storage array: `{report['semantic_coexistence']['with_columnmux'] and report['semantic_coexistence']['with_senseamp'] and report['semantic_coexistence']['with_storage_array']}`",
        f"- standalone modified: `{report['standalone_modified']}`",
        f"- routing changed: `{report['routing_changed']}`",
        f"- GDS writer changed: `{report['gds_writer_changed']}`",
        f"- write_driver changed: `{report['write_driver_changed']}`",
        "",
        "## Primary Plan",
        "",
        f"- placement count: `{primary['placement_count']}`",
        f"- macro name: `{primary['macro_name']}`",
        f"- grouped mapping needs confirmation: `{primary['grouped_write_mapping_needs_confirmation']}`",
        f"- semantic coexistence reason: `{report['semantic_coexistence']['reason']}`",
        f"- example placements: `{len(primary['example_placements'])}`",
        "",
        "| instance | col | group | cols | x | y | orientation | macro |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in primary["example_placements"]:
        lines.append(
            f"| {item['instance_name']} | {item['col']} | {item['group']} | {', '.join(str(col) for col in item['cols'])} | "
            f"{item['x']} | {item['y']} | {item['orientation']} | {item['macro_name']} |"
        )
    lines.extend([
        "",
        "## Pin Mapping",
        "",
        "| OpenYield pin | Local pin | Canonical signal |",
        "| --- | --- | --- |",
    ])
    for pin, local in primary["expected_mapping"].items():
        lines.append(f"| {pin} | {local} | {local if pin not in {'EN', 'BLB'} else {'EN': 'write_enable', 'BLB': 'br'}[pin]} |")
    if report["extra_plan"] is not None:
        extra = report["extra_plan"]
        lines.extend([
            "",
            "## Extra Grouped Example",
            "",
            f"- placement count: `{extra['placement_count']}`",
            f"- grouped mapping needs confirmation: `{extra['grouped_write_mapping_needs_confirmation']}`",
            f"- macro name: `{extra['macro_name']}`",
        ])
    lines.extend(["", "## Notes", ""])
    for note in report["notes"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def find_contract(contracts: Any, original_module_name: str) -> dict[str, Any]:
    for item in contracts if isinstance(contracts, list) else contracts.get("contracts", []):
        if item.get("original_module_name") == original_module_name:
            return item
    raise ValueError(f"Could not find contract: {original_module_name}")


def resolve_path(path_text: str) -> Path:
    raw = Path(path_text)
    for candidate in (raw, REPO_ROOT / raw):
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not resolve path: {path_text}")


def resolve_output(path_text: str) -> Path:
    raw = Path(path_text)
    return raw if raw.is_absolute() else REPO_ROOT / raw


if __name__ == "__main__":
    raise SystemExit(main())
