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

from sram_layoutgen.openyield_adapter.gds_pin_audit import audit_macros  # noqa: E402


FOCUS_MACROS = (
    "cell_1rw",
    "dummy_cell_1rw",
    "replica_cell_1rw",
    "sense_amp",
    "write_driver",
    "dff",
    "tri_gate",
    "gen_precharge",
    "gen_col_mux",
    "gen_wl_driver",
    "gen_nand2",
    "gen_nand4",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit local FreePDK45 GDS TEXT pins, pin-shape hints, and rail continuity.")
    parser.add_argument("--tech-dir", default="technology/freepdk45")
    parser.add_argument("--aliases", default="technology/freepdk45/openyield_macro_aliases.json")
    parser.add_argument("--out-json", default="docs/openyield_gds_pin_audit_report.json")
    parser.add_argument("--out-md", default="docs/openyield_gds_pin_audit_report.md")
    args = parser.parse_args()

    tech_dir = resolve_input(args.tech_dir)
    aliases = resolve_input(args.aliases)
    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)

    report = audit_macros(tech_dir, aliases, FOCUS_MACROS)
    report["aliases_path"] = str(aliases.resolve())
    report["focus_macros"] = FOCUS_MACROS
    report["semantic_conclusions"] = semantic_conclusions(report)
    report["can_enter_placement_aggregation"] = False
    report["placement_aggregation_blockers"] = [
        "The internal parser extracted labels and nearby shape bboxes, but it does not prove electrical connectivity across hierarchy.",
        "SENSEAMP requires an architecture adapter because local sense_amp has no proven QB/dout_b physical output.",
        "WORDLINEDRIVER still needs semantic confirmation for B/wordline_enable before routing.",
        "COLUMNMUX is missing vdd metadata and must not be allowed to share rails.",
        "Power rail sharing must be validated with a full GDS pin-shape/connectivity audit before placement aggregation.",
    ]

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    out_md.write_text(format_markdown(report), encoding="utf-8", newline="\n")
    smoke_assertions(report)
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(
        "audited_macros="
        f"{report['macro_count']} ready={len(report['summary']['macros_ready_for_aggregation'])} "
        f"manual={len(report['summary']['macros_need_manual_confirmation'])}"
    )
    return 0


def semantic_conclusions(report: dict[str, Any]) -> dict[str, Any]:
    by_name = {item["macro_name"]: item for item in report["audited_macros"]}
    sense = by_name.get("sense_amp", {})
    wl = by_name.get("gen_wl_driver", {})
    col = by_name.get("gen_col_mux", {})
    sense_pins = {pin["canonical_pin"]: pin for pin in sense.get("pins", [])}
    wl_pins = {pin["canonical_pin"]: pin for pin in wl.get("pins", [])}
    col_pins = {pin["canonical_pin"]: pin for pin in col.get("pins", [])}
    return {
        "SENSEAMP": {
            "IN_to_bl": sense_pins.get("bl", {}).get("pin_shape_source") != "missing",
            "INB_to_br": sense_pins.get("br", {}).get("pin_shape_source") != "missing",
            "Q_to_dout": sense_pins.get("dout", {}).get("pin_shape_source") != "missing",
            "QB_to_dout_b": sense_pins.get("dout_b", {}).get("pin_shape_source") != "missing",
            "conclusion": "architecture_adapter_required",
            "recommendation": "Do not force-match QB/dout_b. Current local layoutgen uses single-ended dout sense_amp; adapt Q/QB to dout at architecture contract level.",
        },
        "WORDLINEDRIVER": {
            "A_decoder_input_present": wl_pins.get("decoder_input", {}).get("pin_shape_source") != "missing",
            "B_wordline_enable_present": wl_pins.get("wordline_enable", {}).get("pin_shape_source") != "missing",
            "Z_wl_present": wl_pins.get("wl", {}).get("pin_shape_source") != "missing",
            "conclusion": "needs_semantic_confirmation",
            "recommendation": "Do not directly route OpenYield B as wordline_enable until gen_wl_driver polarity and physical B/equivalent pin are confirmed.",
        },
        "COLUMNMUX": {
            "has_vdd_metadata": col_pins.get("vdd", {}).get("pin_shape_source") != "missing",
            "has_gnd_metadata": col_pins.get("gnd", {}).get("pin_shape_source") != "missing",
            "conclusion": "missing_power_metadata" if col_pins.get("vdd", {}).get("pin_shape_source") == "missing" else "power_metadata_present",
            "recommendation": "Do not allow shared rail for gen_col_mux until vdd metadata or a proven vdd shape is added.",
        },
    }


def smoke_assertions(report: dict[str, Any]) -> None:
    names = {item["macro_name"] for item in report["audited_macros"]}
    for name in FOCUS_MACROS:
        assert name in names, f"{name} was not audited"
    conclusions = report["semantic_conclusions"]
    assert conclusions["SENSEAMP"]["conclusion"] == "architecture_adapter_required"
    assert conclusions["WORDLINEDRIVER"]["conclusion"] == "needs_semantic_confirmation"
    assert conclusions["COLUMNMUX"]["conclusion"] == "missing_power_metadata"


def format_markdown(report: dict[str, Any]) -> str:
    rows = []
    for item in report["audited_macros"]:
        power = item["power_rail_audit"]
        rows.append(
            [
                item["macro_name"],
                item["gds_reader_status"],
                _fmt_bbox(item["bbox"]),
                item["width"],
                item["height"],
                len(item["labels"]),
                _pin_side_summary(item),
                power["rail_continuity_status"],
                f"vdd:{power['vdd_side']} gnd:{power['gnd_side']}",
                f"LR:{power['can_share_left_right']} TB:{power['can_share_top_bottom']}",
                item["abutment_readiness"],
                ", ".join(item["semantic_flags"]) or "-",
            ]
        )
    pin_rows = []
    for item in report["audited_macros"]:
        for pin in item["pins"]:
            pin_rows.append(
                [
                    item["macro_name"],
                    pin["pin_name"],
                    pin["canonical_pin"],
                    pin["pin_layer"],
                    pin["pin_side"],
                    pin["distance_to_boundary"],
                    pin["pin_shape_source"],
                    _fmt_bbox(pin["pin_shape_bbox"]),
                ]
            )
    return "\n".join(
        [
            "# OpenYield GDS Pin And Rail Audit",
            "",
            "This report reads local GDS TEXT labels and BOUNDARY/PATH bboxes with a read-only internal GDSII parser. It does not write GDS, modify placement/routing, or change OpenYield source.",
            "",
            "## Reader",
            "",
            f"- reader: `{report['gds_reader']}`",
            "- limitations:",
            *[f"  - {item}" for item in report["gds_reader_limitations"]],
            "",
            "## Summary",
            "",
            f"- audited GDS macros: `{report['macro_count']}`",
            f"- rail status counts: `{json.dumps(report['summary']['rail_status_counts'], ensure_ascii=False)}`",
            f"- abutment readiness counts: `{json.dumps(report['summary']['abutment_readiness_counts'], ensure_ascii=False)}`",
            f"- macros ready for aggregation: `{', '.join(report['summary']['macros_ready_for_aggregation']) or 'none'}`",
            f"- macros needing manual confirmation: `{', '.join(report['summary']['macros_need_manual_confirmation']) or 'none'}`",
            "",
            "## Macro Audit",
            "",
            md_table(
                [
                    "macro",
                    "reader",
                    "bbox",
                    "width",
                    "height",
                    "labels",
                    "pin sides",
                    "rail status",
                    "power sides",
                    "share rails",
                    "abutment",
                    "semantic flags",
                ],
                rows,
            ),
            "",
            "## Pin Details",
            "",
            md_table(
                ["macro", "pin", "canonical", "layer", "side", "distance", "shape source", "shape bbox"],
                pin_rows,
            ),
            "",
            "## Semantic Conclusions",
            "",
            "```json",
            json.dumps(report["semantic_conclusions"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Placement Aggregation Readiness",
            "",
            f"- can enter placement aggregation now: `{report['can_enter_placement_aggregation']}`",
            "",
            "Blockers:",
            "",
            list_block(report["placement_aggregation_blockers"]),
        ]
    )


def _pin_side_summary(item: dict[str, Any]) -> str:
    return ", ".join(f"{pin['canonical_pin']}:{pin['pin_side']}" for pin in item["pins"]) or "-"


def _fmt_bbox(bbox: dict[str, Any] | None) -> str:
    if not bbox:
        return "-"
    return f"({bbox['x0']:.4g},{bbox['y0']:.4g})-({bbox['x1']:.4g},{bbox['y1']:.4g})"


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(out)


def list_block(items: list[str]) -> str:
    if not items:
        return "none"
    return "\n".join(f"- `{item}`" for item in items)


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
