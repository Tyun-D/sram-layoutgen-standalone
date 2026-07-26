"""Generate a read-only OpenYield sense_amp placement adapter smoke report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.architecture_adapter import build_senseamp_architecture_adapter
from sram_layoutgen.openyield_adapter.senseamp_placement import (
    LOCAL_SENSEAMP_PINS,
    build_senseamp_placement_plan,
    example_placements,
    inspect_local_senseamp_macro,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cols", type=int, required=True)
    parser.add_argument("--mux-ratio", type=int, required=True)
    parser.add_argument("--origin-x", type=float, required=True)
    parser.add_argument("--origin-y", type=float, required=True)
    parser.add_argument("--pitch-x", type=float, required=True)
    parser.add_argument("--tech-dir", default="technology/freepdk45")
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    tech_dir = resolve_existing_path(args.tech_dir)
    local_macro = inspect_local_senseamp_macro(tech_dir)
    adapter = build_senseamp_architecture_adapter(qb_required_downstream=False)
    plan = build_senseamp_placement_plan(
        cols=args.cols,
        mux_ratio=args.mux_ratio,
        origin_x=args.origin_x,
        origin_y=args.origin_y,
        pitch_x=args.pitch_x,
        adapter=adapter,
        local_macro=local_macro,
    )

    fake_dout_b_present = any(
        any(net_name in {"dout_b", "qb", "sense_qb"} for net_name in placement.nets.values())
        for placement in plan.placements
    )
    placements_payload = [item.to_dict() for item in plan.placements]
    report: dict[str, Any] = {
        "scope": "step5_2_senseamp_placement_adapter_smoke_read_only",
        "inputs": {
            "cols": args.cols,
            "mux_ratio": args.mux_ratio,
            "origin_x": args.origin_x,
            "origin_y": args.origin_y,
            "pitch_x": args.pitch_x,
            "tech_dir": str(tech_dir.resolve()),
        },
        "adapter_strategy": plan.adapter_strategy,
        "openyield_senseamp_pin_list": ["VDD", "VSS", "EN", "IN", "INB", "Q", "QB"],
        "local_senseamp_pin_list": list(local_macro.spice_pins),
        "local_senseamp_expected_pin_list": list(LOCAL_SENSEAMP_PINS),
        "placement_count": len(plan.placements),
        "plan": plan.to_dict(),
        "example_placements": example_placements(plan, limit=min(4, len(plan.placements))),
        "pin_net_mapping_table": [
            {
                "instance_name": item["instance_name"],
                "macro_name": item["macro_name"],
                "orientation": item["orientation"],
                "nets": item["nets"],
            }
            for item in placements_payload
        ],
        "dropped_pin_table": [
            {
                "instance_name": item["instance_name"],
                "dropped_pins": item["dropped_pins"],
            }
            for item in placements_payload
        ],
        "checks": {
            "local_macro_is_sense_amp": local_macro.macro_name == "sense_amp",
            "local_pins_match_expected": tuple(local_macro.spice_pins) == LOCAL_SENSEAMP_PINS,
            "q_to_dout_established": local_macro.q_to_dout_established,
            "qb_to_dout_b_established": local_macro.qb_to_dout_b_established,
            "qb_recorded_as_dropped": all("QB" in item.dropped_pins for item in plan.placements),
            "fake_dout_b_generated": fake_dout_b_present,
            "safe_for_physical_mapping": local_macro.safe_for_physical_mapping and adapter.safe_for_physical_mapping,
            "requires_netlist_rewrite": plan.requires_netlist_rewrite,
            "requires_layout_pin": plan.requires_layout_pin,
            "modified_standalone": False,
            "modified_routing_or_gds_writer": False,
        },
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "can_enter_standalone_opt_in_placement": True,
        "next_step_recommendation": (
            "Use this placement adapter as an explicit opt-in layer before touching standalone peripheral placement."
        ),
        "notes": [
            "This smoke report plans only sense_amp instances.",
            "QB is retained in metadata as dropped_complementary_output and does not become a physical net.",
            "The grouped mux-ratio mode records mux_out/mux_out_b expectations without placing column mux macros.",
        ],
    }

    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    out_md.write_text(render_markdown(report), encoding="utf-8")
    print(
        "placements={count} strategy={strategy} fake_dout_b={fake} safe={safe}".format(
            count=report["placement_count"],
            strategy=report["adapter_strategy"],
            fake=report["checks"]["fake_dout_b_generated"],
            safe=report["checks"]["safe_for_physical_mapping"],
        )
    )
    return 0


def resolve_existing_path(path_text: str) -> Path:
    raw = Path(path_text)
    candidates = [raw, REPO_ROOT / raw]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not resolve path: {path_text}")


def render_markdown(report: dict[str, Any]) -> str:
    checks = report["checks"]
    lines = [
        "# OpenYield SenseAmp Placement Adapter Report",
        "",
        "This Step 5.2 report is adapter-only smoke. It does not modify standalone placement, routing, GDS writer, or OpenYield source.",
        "",
        "## Inputs",
        "",
    ]
    for key, value in report["inputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines += [
        "",
        "## Summary",
        "",
        f"- adapter strategy: `{report['adapter_strategy']}`",
        f"- placement count: `{report['placement_count']}`",
        f"- local sense_amp pins: `{', '.join(report['local_senseamp_pin_list'])}`",
        f"- OpenYield SENSEAMP pins: `{', '.join(report['openyield_senseamp_pin_list'])}`",
        f"- requires netlist rewrite: `{checks['requires_netlist_rewrite']}`",
        f"- requires layout pin: `{checks['requires_layout_pin']}`",
        f"- generated fake dout_b: `{checks['fake_dout_b_generated']}`",
        f"- can enter standalone sense_amp opt-in placement: `{report['can_enter_standalone_opt_in_placement']}`",
        "",
        "## Mapping Rules",
        "",
        "| OpenYield pin | Local pin/net meaning | Physical? |",
        "| --- | --- | --- |",
        "| VDD | vdd | yes |",
        "| VSS | gnd | yes |",
        "| EN | en / sense_enable | yes |",
        "| IN | bl | yes |",
        "| INB | br | yes |",
        "| Q | dout | yes |",
        "| QB | dropped_complementary_output | no |",
        "",
        "## Example Placements",
        "",
        "| instance | x | y | orientation | nets | dropped pins |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["example_placements"]:
        lines.append(
            f"| {item['instance_name']} | {item['x']} | {item['y']} | {item['orientation']} | "
            f"`{item['nets']}` | `{item['dropped_pins']}` |"
        )
    lines += [
        "",
        "## Checks",
        "",
    ]
    for key in (
        "local_macro_is_sense_amp",
        "local_pins_match_expected",
        "q_to_dout_established",
        "qb_to_dout_b_established",
        "qb_recorded_as_dropped",
        "fake_dout_b_generated",
        "safe_for_physical_mapping",
        "requires_netlist_rewrite",
        "requires_layout_pin",
        "modified_standalone",
        "modified_routing_or_gds_writer",
    ):
        lines.append(f"- {key}: `{checks[key]}`")
    lines += [
        "",
        "## Conclusions",
        "",
        "- `QB` is recorded only in metadata and dropped-pin tables.",
        "- No physical `dout_b`, `qb`, or `sense_qb` output net is generated.",
        "- The plan is safe only for the current single-ended `Q -> dout` sense_amp architecture.",
        "- This smoke does not place write drivers, column muxes, wordline drivers, or control logic.",
        "",
        "## Next Step",
        "",
        f"- {report['next_step_recommendation']}",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
