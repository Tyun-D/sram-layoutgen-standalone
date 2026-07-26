from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.wordlinedriver_adapter import (  # noqa: E402
    build_wordlinedriver_adapter,
    classify_wordlinedriver_power_status,
    inspect_local_wordlinedriver_macro,
    inspect_openyield_wordlinedriver_source,
)
from sram_layoutgen.openyield_adapter.wordlinedriver_placement import build_wordlinedriver_limited_placement_plan  # noqa: E402


DEFAULT_CONTRACTS = Path("docs/openyield_module_contracts.json")
DEFAULT_OPENYIELD_ROOT = Path("third_party/OpenYield")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a limited WORDLINEDRIVER placement plan smoke report.")
    parser.add_argument("--rows", type=int, default=4)
    parser.add_argument("--origin-x", type=float, default=0.0)
    parser.add_argument("--origin-y", type=float, default=0.0)
    parser.add_argument("--pitch-y", type=float, default=1.565)
    parser.add_argument("--contracts", default=str(DEFAULT_CONTRACTS))
    parser.add_argument("--openyield-root", default=str(DEFAULT_OPENYIELD_ROOT))
    parser.add_argument("--tech-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    contracts_path = resolve_path(args.contracts)
    openyield_root = resolve_path(args.openyield_root)
    tech_dir = resolve_path(args.tech_dir)
    contracts = json.loads(contracts_path.read_text(encoding="utf-8"))
    contract = find_contract(contracts, "WORDLINEDRIVER")
    local_macro = inspect_local_wordlinedriver_macro(tech_dir)
    source_audit = inspect_openyield_wordlinedriver_source(openyield_root)
    power_status = classify_wordlinedriver_power_status(local_macro, contract)
    adapter = build_wordlinedriver_adapter(local_macro, contract, source_audit)
    plan = build_wordlinedriver_limited_placement_plan(
        rows=args.rows,
        origin_x=args.origin_x,
        origin_y=args.origin_y,
        pitch_y=args.pitch_y,
        power_status=power_status,
        safe_for_physical_mapping=adapter.safe_for_physical_mapping,
        safe_for_shared_rail=adapter.safe_for_shared_rail,
    )

    report: dict[str, Any] = {
        "scope": "step5_13_wordlinedriver_placement_smoke",
        "inputs": {
            "contracts": str(contracts_path.resolve()),
            "openyield_root": str(openyield_root.resolve()),
            "tech_dir": str(tech_dir.resolve()),
            "rows": args.rows,
            "origin_x": args.origin_x,
            "origin_y": args.origin_y,
            "pitch_y": args.pitch_y,
        },
        "power_status": power_status,
        "adapter": adapter.to_dict(),
        "placement_plan": plan.to_dict(),
        "can_enter_wordlinedriver_limited_placement": adapter.can_enter_limited_placement,
        "standalone_modified": False,
        "routing_changed": False,
        "gds_writer_changed": False,
        "wordline_driver_changed": False,
        "notes": list(plan.notes)
        + [
            "This smoke is metadata-only and does not emit GDS.",
            "The physical wordline-driver flow is intentionally left untouched.",
        ],
    }

    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(report), encoding="utf-8")
    print(
        "rows={rows} limited={limited} placements={placements}".format(
            rows=report["placement_plan"]["rows"],
            limited=report["can_enter_wordlinedriver_limited_placement"],
            placements=len(report["placement_plan"]["placements"]),
        )
    )
    return 0


def render_markdown(report: dict[str, Any]) -> str:
    plan = report["placement_plan"]
    lines = [
        "# OpenYield WORDLINEDRIVER Placement Smoke Report",
        "",
        "This is a limited placement plan smoke. It does not modify standalone.py, routing, or the GDS writer.",
        "",
        "## Summary",
        "",
        f"- rows: `{plan['rows']}`",
        f"- origin: `({plan['origin_x']}, {plan['origin_y']})`",
        f"- pitch_y: `{plan['pitch_y']}`",
        f"- macro name: `{plan['macro_name']}`",
        f"- row orientation policy: `{plan['row_orientation_policy']}`",
        f"- power status: `{report['power_status']}`",
        f"- can enter limited placement: `{report['can_enter_wordlinedriver_limited_placement']}`",
        f"- standalone modified: `{report['standalone_modified']}`",
        f"- routing changed: `{report['routing_changed']}`",
        f"- GDS writer changed: `{report['gds_writer_changed']}`",
        f"- wordline_driver changed: `{report['wordline_driver_changed']}`",
        "",
        "## Placements",
        "",
        "| instance | row | x | y | orientation | a | b | z |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in plan["placements"][:8]:
        lines.append(
            f"| {item['instance_name']} | {item['row']} | {item['x']} | {item['y']} | {item['orientation']} | "
            f"{item['nets']['a']} | {item['nets']['b']} | {item['nets']['z']} |"
        )
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
    candidates = [raw, REPO_ROOT / raw]
    for parent in (REPO_ROOT, *REPO_ROOT.parents):
        candidates.append(parent / raw)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not resolve path: {path_text}")


def resolve_output(path_text: str) -> Path:
    raw = Path(path_text)
    return raw if raw.is_absolute() else REPO_ROOT / raw


if __name__ == "__main__":
    raise SystemExit(main())
