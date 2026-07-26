from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.columnmux_placement import build_columnmux_limited_placement_plan  # noqa: E402


DEFAULT_ALIAS_REPORT = Path("docs/openyield_colmux_vdd_pinproof_report.json")
DEFAULT_COLUMNMUX_REPORT = Path("docs/openyield_columnmux_adapter_report.json")
DEFAULT_SENSEAMP_REPORT = Path("docs/openyield_senseamp_adapter_report.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate repaired column mux alias and limited placement plan smoke reports.")
    parser.add_argument("--cols", type=int, required=True)
    parser.add_argument("--mux-ratio", type=int, required=True)
    parser.add_argument("--origin-x", type=float, required=True)
    parser.add_argument("--origin-y", type=float, required=True)
    parser.add_argument("--pitch-x", type=float, required=True)
    parser.add_argument("--use-repaired-vdd-label", action="store_true")
    parser.add_argument("--alias-source-report", default=str(DEFAULT_ALIAS_REPORT))
    parser.add_argument("--columnmux-report", default=str(DEFAULT_COLUMNMUX_REPORT))
    parser.add_argument("--senseamp-report", default=str(DEFAULT_SENSEAMP_REPORT))
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-alias-json", default="docs/openyield_repaired_macro_aliases_candidate.json")
    parser.add_argument("--out-alias-md", default="docs/openyield_colmux_repaired_alias_report.md")
    parser.add_argument("--out-alias-report-json", default="docs/openyield_colmux_repaired_alias_report.json")
    args = parser.parse_args()

    alias_source_report_path = resolve_path(args.alias_source_report)
    columnmux_report_path = resolve_path(args.columnmux_report)
    senseamp_report_path = resolve_path(args.senseamp_report)
    alias_source = load_json(alias_source_report_path)
    columnmux_report = load_json(columnmux_report_path)
    senseamp_report = load_json(senseamp_report_path)

    candidate_alias = build_candidate_alias(alias_source)
    alias_out_json = resolve_output(args.out_alias_json)
    alias_out_json.parent.mkdir(parents=True, exist_ok=True)
    alias_out_json.write_text(json.dumps(candidate_alias, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    alias_report = build_alias_report(alias_source, candidate_alias)
    alias_report_json = resolve_output(args.out_alias_report_json)
    alias_report_md = resolve_output(args.out_alias_md)
    alias_report_json.parent.mkdir(parents=True, exist_ok=True)
    alias_report_md.parent.mkdir(parents=True, exist_ok=True)
    alias_report_json.write_text(json.dumps(alias_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    alias_report_md.write_text(render_alias_markdown(alias_report), encoding="utf-8")

    power_status = str(alias_source.get("power_status_after", alias_source.get("power_status", "unknown")))
    safe_for_physical_mapping = bool(alias_source.get("safe_for_physical_mapping", False))
    safe_for_shared_rail = bool(alias_source.get("safe_for_shared_rail", False))
    plan = build_columnmux_limited_placement_plan(
        cols=args.cols,
        mux_ratio=args.mux_ratio,
        origin_x=args.origin_x,
        origin_y=args.origin_y,
        pitch_x=args.pitch_x,
        use_repaired_vdd_label=args.use_repaired_vdd_label,
        power_status=power_status,
        safe_for_physical_mapping=safe_for_physical_mapping,
        safe_for_shared_rail=safe_for_shared_rail,
    )

    placement_report = build_placement_report(
        alias_source=alias_source,
        alias_report=alias_report,
        columnmux_report=columnmux_report,
        senseamp_report=senseamp_report,
        plan=plan,
        source_alias_json=alias_out_json,
        source_alias_report_json=alias_report_json,
        alias_source_report_path=alias_source_report_path,
        columnmux_report_path=columnmux_report_path,
        senseamp_report_path=senseamp_report_path,
    )

    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(placement_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(render_placement_markdown(placement_report), encoding="utf-8")

    print(
        "alias={alias} placements={count} mux_ratio={mux} pair={pair} shared={shared} limited={limited}".format(
            alias=candidate_alias["aliases"][0]["local_macro"],
            count=len(plan.placements),
            mux=plan.mux_ratio,
            pair=placement_report["senseamp_pairing"]["can_pair"],
            shared=plan.safe_for_shared_rail,
            limited=placement_report["can_enter_columnmux_limited_placement"],
        )
    )
    return 0


def resolve_path(path_text: str) -> Path:
    raw = Path(path_text)
    candidates = [raw, REPO_ROOT / raw]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not resolve path: {path_text}")


def resolve_output(path_text: str) -> Path:
    raw = Path(path_text)
    return raw if raw.is_absolute() else REPO_ROOT / raw


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def build_candidate_alias(alias_source: dict[str, Any]) -> dict[str, Any]:
    repair_type = "add_vdd_text_label_only"
    return {
        "version": 1,
        "description": "OpenYield repaired macro alias candidate generated from proof-only VDD label repair.",
        "aliases": [
            {
                "openyield_module": "COLUMNMUX",
                "local_macro": "gen_col_mux_vdd_labeled",
                "source_macro": "gen_col_mux",
                "source_gds": alias_source["source_gds_path"],
                "candidate_gds": alias_source["repaired_candidate_gds_path"],
                "repair_type": repair_type,
                "polygon_changed": False,
                "safe_for_physical_mapping": True,
                "safe_for_shared_rail": False,
                "power_status": "vdd_label_present",
                "notes": [
                    "Proof candidate only; do not overwrite original replacement GDS.",
                    "Shared rail remains disabled.",
                    "Candidate GDS is the proof-only file produced in Step 5.6.",
                ],
            }
        ],
    }


def build_alias_report(alias_source: dict[str, Any], candidate_alias: dict[str, Any]) -> dict[str, Any]:
    alias = candidate_alias["aliases"][0]
    return {
        "scope": "step5_7_columnmux_repaired_alias_candidate",
        "source_report": alias_source["source_gds_path"],
        "candidate_gds": alias["candidate_gds"],
        "repaired_alias_candidate": alias,
        "polygon_changed": alias["polygon_changed"],
        "power_status": alias["power_status"],
        "safe_for_physical_mapping": alias["safe_for_physical_mapping"],
        "safe_for_shared_rail": alias["safe_for_shared_rail"],
        "recommended_integration": "add_repaired_macro_alias",
        "notes": list(alias["notes"]) + [
            "This alias candidate is intentionally separate from replacement_macros.json.",
        ],
    }


def build_placement_report(
    *,
    alias_source: dict[str, Any],
    alias_report: dict[str, Any],
    columnmux_report: dict[str, Any],
    senseamp_report: dict[str, Any],
    plan,
    source_alias_json: Path,
    source_alias_report_json: Path,
    alias_source_report_path: Path,
    columnmux_report_path: Path,
    senseamp_report_path: Path,
) -> dict[str, Any]:
    placement_examples = [item.to_dict() for item in plan.placements[:3]]
    senseamp_pairing = {
        "can_pair": bool(columnmux_report.get("columnmux_can_pair_with_senseamp_adapter", False)),
        "senseamp_input_map": {
            "IN": "mux_out[group]",
            "INB": "mux_out_b[group]",
            "Q": "dout[group]",
            "QB": "dropped_complementary_output",
        },
        "senseamp_adapter_safe": bool(senseamp_report.get("adapter", {}).get("safe_for_physical_mapping", False)),
        "senseamp_q_to_dout": bool(senseamp_report.get("q_to_dout_established", False)),
        "senseamp_qb_to_dout_b": bool(senseamp_report.get("qb_to_dout_b_established", False)),
    }
    return {
        "scope": "step5_7_columnmux_limited_placement_smoke",
        "inputs": {
            "alias_candidate_json": str(source_alias_json.resolve()),
            "alias_candidate_report_json": str(source_alias_report_json.resolve()),
            "alias_source_report": str(alias_source_report_path.resolve()),
            "columnmux_report": str(columnmux_report_path.resolve()),
            "senseamp_report": str(senseamp_report_path.resolve()),
            "use_repaired_vdd_label": True,
        },
        "repaired_alias_candidate": alias_report["repaired_alias_candidate"],
        "source_gds": alias_source["source_gds_path"],
        "candidate_gds": alias_source["repaired_candidate_gds_path"],
        "labels_before": alias_source["labels_before"],
        "labels_after": alias_source["labels_after"],
        "power_status_before": alias_source["power_status_before"],
        "power_status_after": alias_source["power_status_after"],
        "safe_for_physical_mapping": alias_source["safe_for_physical_mapping"],
        "safe_for_shared_rail": alias_source["safe_for_shared_rail"],
        "can_enter_columnmux_limited_placement": bool(alias_source["vdd_label_present_after"]),
        "placement_count": len(plan.placements),
        "mux_ratio": plan.mux_ratio,
        "macro_name": plan.macro_name,
        "placement_plan": plan.to_dict(),
        "example_placements": placement_examples,
        "net_mapping_table": [
            {"openyield_pin": "VDD", "local_pin": "vdd", "canonical_signal": "vdd", "required": True},
            {"openyield_pin": "VSS", "local_pin": "gnd", "canonical_signal": "gnd", "required": True},
            {"openyield_pin": "SEL", "local_pin": "col_sel[group]", "canonical_signal": "column_select", "required": True},
            {"openyield_pin": "BL", "local_pin": "bl[col0]", "canonical_signal": "bl", "required": True},
            {"openyield_pin": "BR", "local_pin": "br[col0]", "canonical_signal": "br", "required": True},
            {"openyield_pin": "OUT", "local_pin": "mux_out[group]", "canonical_signal": "mux_out", "required": True},
            {"openyield_pin": "OUTB", "local_pin": "mux_out_b[group]", "canonical_signal": "mux_out_b", "required": True},
        ],
        "senseamp_pairing": senseamp_pairing,
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "shared_rail_merge": False,
        "notes": list(plan.notes) + [
            "The placement plan is grouped semantic only when mux_ratio > 1.",
            "Physical BL/BLB fan-in is intentionally not expanded in this smoke.",
            "No standalone or routing code paths are changed.",
        ],
    }


def render_alias_markdown(report: dict[str, Any]) -> str:
    alias = report["repaired_alias_candidate"]
    lines = [
        "# OpenYield ColumnMux Repaired Alias Report",
        "",
        f"- source GDS: `{report['source_report']}`",
        f"- candidate GDS: `{report['candidate_gds']}`",
        f"- local macro: `{alias['local_macro']}`",
        f"- source macro: `{alias['source_macro']}`",
        f"- repair type: `{alias['repair_type']}`",
        f"- polygon changed: `{report['polygon_changed']}`",
        f"- power status: `{report['power_status']}`",
        f"- safe_for_physical_mapping: `{report['safe_for_physical_mapping']}`",
        f"- safe_for_shared_rail: `{report['safe_for_shared_rail']}`",
        f"- recommended_integration: `{report['recommended_integration']}`",
        "",
    ]
    for note in report["notes"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def render_placement_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield ColumnMux Placement Smoke Report",
        "",
        f"- placement count: `{report['placement_count']}`",
        f"- mux ratio: `{report['mux_ratio']}`",
        f"- macro name: `{report['macro_name']}`",
        f"- can enter limited placement: `{report['can_enter_columnmux_limited_placement']}`",
        f"- safe_for_physical_mapping: `{report['safe_for_physical_mapping']}`",
        f"- safe_for_shared_rail: `{report['safe_for_shared_rail']}`",
        "",
        "## Repaired Alias",
        "",
        f"- local macro: `{report['repaired_alias_candidate']['local_macro']}`",
        f"- source macro: `{report['repaired_alias_candidate']['source_macro']}`",
        f"- candidate GDS: `{report['candidate_gds']}`",
        "",
        "## SenseAmp Pairing",
        "",
        f"- can pair: `{report['senseamp_pairing']['can_pair']}`",
        f"- IN map: `{report['senseamp_pairing']['senseamp_input_map']['IN']}`",
        f"- INB map: `{report['senseamp_pairing']['senseamp_input_map']['INB']}`",
        f"- Q map: `{report['senseamp_pairing']['senseamp_input_map']['Q']}`",
        f"- QB map: `{report['senseamp_pairing']['senseamp_input_map']['QB']}`",
        "",
        "## Example Placements",
        "",
        "| instance | group | cols | x | y | orientation | macro |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["example_placements"]:
        lines.append(
            f"| {item['instance_name']} | {item['group']} | {', '.join(str(col) for col in item['cols'])} | "
            f"{item['x']} | {item['y']} | {item['orientation']} | {item['macro_name']} |"
        )
    lines += [
        "",
        "## Net Mapping",
        "",
        "| OpenYield pin | Local pin | Canonical | Required |",
        "| --- | --- | --- | --- |",
    ]
    for item in report["net_mapping_table"]:
        lines.append(f"| {item['openyield_pin']} | {item['local_pin']} | {item['canonical_signal']} | {item['required']} |")
    lines += [
        "",
        "## Notes",
        "",
    ]
    for note in report["notes"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
