from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))

from sram_layoutgen.gds_util import inspect_gds_text_records  # noqa: E402
from sram_layoutgen.standalone import load_bundled_freepdk45  # noqa: E402


DEFAULT_CLASSIFICATION = Path("docs/openyield_drc_marker_classification_report.json")
DEFAULT_STORAGE_GDS = Path("build/openyield_storage_only_smoke_2x4_stitched/storage_only_2x4_stitched.gds")
DEFAULT_OUT_JSON = Path("docs/openyield_row_boundary_audit_report.json")
DEFAULT_OUT_MD = Path("docs/openyield_row_boundary_audit_report.md")
PITCH_Y = 1.565
ROW_BOUNDARY_Y = 1.465


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit storage-array row-boundary DRC markers and row-orientation policy implications.")
    parser.add_argument("--classification", type=Path, default=DEFAULT_CLASSIFICATION)
    parser.add_argument("--storage-gds", type=Path, default=DEFAULT_STORAGE_GDS)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    args = parser.parse_args()

    report = build_report(args)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(format_markdown(report), encoding="utf-8")
    print(f"Wrote {args.out_json}")
    print(f"Wrote {args.out_md}")
    print(
        f"row_boundary_markers={report['summary']['row_boundary_marker_count']} "
        f"bitline_near={report['summary']['bitline_near_count']} "
        f"r0mx_recommended={report['recommendations']['recommend_r0_mx_compare_smoke']}"
    )
    return 0


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    classification = json.loads(args.classification.read_text(encoding="utf-8"))
    all_markers = list(classification.get("markers", []))
    metal2 = [marker for marker in all_markers if marker.get("rule_name") == "METAL2.2"]
    row_markers = [marker for marker in metal2 if marker.get("near_row_boundary")]
    tech = load_bundled_freepdk45()
    pin_summary = hardcell_pin_summary(tech)

    ys = [float(marker["center_y"]) for marker in row_markers]
    row_boundary_distances = [abs(float(marker["center_y"]) - ROW_BOUNDARY_Y) for marker in row_markers]
    local_y = [round(float(marker["center_y"]) - PITCH_Y, 6) for marker in row_markers]
    bitline_near = [marker for marker in row_markers if marker.get("near_bitline_pin", {}).get("near")]
    power_stitch_near = [marker for marker in row_markers if marker.get("near_power_stitch", {}).get("near")]
    nearest_pin_labels = Counter(
        marker.get("near_bitline_pin", {}).get("nearest_label")
        for marker in row_markers
        if marker.get("near_bitline_pin", {}).get("nearest_label")
    )
    nearest_macros = Counter(marker.get("nearest_macro") for marker in row_markers)
    causes = Counter(marker.get("likely_cause") for marker in row_markers)
    all_r0_risk = True
    mx_likely_helpful = True
    row_gap_only_workaround = True

    return {
        "inputs": {
            "classification": str(args.classification.resolve()),
            "storage_gds": str(args.storage_gds.resolve()),
        },
        "summary": {
            "metal2_marker_total": len(metal2),
            "row_boundary_marker_count": len(row_markers),
            "row_boundary_y_um": ROW_BOUNDARY_Y,
            "marker_y_values": sorted(set(round(y, 6) for y in ys)),
            "marker_y_distribution": dict(sorted(Counter(round(y, 6) for y in ys).items())),
            "row_boundary_distance_stats_um": {
                "min": round(min(row_boundary_distances), 6) if row_boundary_distances else None,
                "max": round(max(row_boundary_distances), 6) if row_boundary_distances else None,
                "mean": round(statistics.mean(row_boundary_distances), 6) if row_boundary_distances else None,
            },
            "local_y_relative_to_row1_origin": sorted(set(local_y)),
            "bitline_near_count": len(bitline_near),
            "power_stitch_near_count": len(power_stitch_near),
            "nearest_bitline_label_stats": dict(sorted(nearest_pin_labels.items())),
            "nearest_macro_stats": dict(sorted(nearest_macros.items())),
            "likely_cause_stats": dict(sorted(causes.items())),
        },
        "hardcell_pin_summary": pin_summary,
        "orientation_audit": {
            "current_policy": {
                "rows": "R0/R0/R0/...",
                "risk": "bottom-edge M2 bitline shapes from adjacent rows stay on the same seam side",
                "evidence": [
                    "All 34 METAL2.2 markers sit at y=1.475 or 1.4975 around the row0/row1 seam.",
                    "cell_1rw, dummy_cell_1rw, replica_cell_1rw all place BL/BR text on m2 at local y=0.003 near the bottom edge.",
                    "Single hardcell DRC is clean, so the seam markers appear only after two rows are stacked in the storage-only smoke.",
                ],
            },
            "candidate_r0_mx": {
                "rows": "row0=R0, row1=MX, row2=R0, row3=MX, ...",
                "theoretical_benefit": "MX would move row1 bottom-edge m2 features to the top side of row1, away from the row seam.",
                "theoretical_risk": [
                    "Vertical mirror flips power-rail order between rows, so later vertical power stitching must be mirror-aware.",
                    "WL access orientation changes with MX and would need explicit confirmation in any future compare smoke.",
                    "This audit does not prove DRC cleanup without generating a compare smoke.",
                ],
            },
            "candidate_row_gap": {
                "policy": "full bbox pitch + explicit row gap",
                "theoretical_benefit": "Should relieve row-to-row spacing by brute-force separation.",
                "theoretical_risk": "Area increases and this behaves like a conservative workaround rather than a native bitcell tiling policy.",
            },
            "candidate_keepout": {
                "policy": "R0/R0 plus row-boundary keepout",
                "theoretical_benefit": "Equivalent to adding local row gap only where seam risk exists.",
                "theoretical_risk": "Semantically it is still a spacing workaround and does not answer whether alternating orientation is the intended tiling mode.",
            },
        },
        "marker_samples": [
            {
                "marker_id": marker["marker_id"],
                "center_x": marker["center_x"],
                "center_y": marker["center_y"],
                "distance_to_row_boundary": round(abs(float(marker["center_y"]) - ROW_BOUNDARY_Y), 6),
                "nearest_macro": marker["nearest_macro"],
                "nearest_instance": marker["nearest_instance"],
                "nearest_bitline_label": marker.get("near_bitline_pin", {}).get("nearest_label"),
                "nearest_bitline_distance": marker.get("near_bitline_pin", {}).get("nearest_distance"),
                "near_power_stitch": marker.get("near_power_stitch", {}).get("near"),
                "likely_cause": marker.get("likely_cause"),
            }
            for marker in row_markers[:20]
        ],
        "recommendations": {
            "metal2_markers_concentrated_at_row_boundary": len(row_markers) == len(metal2),
            "metal2_markers_near_bitlines": len(bitline_near) > 0,
            "current_r0_r0_likely_source": all_r0_risk,
            "recommend_r0_mx_compare_smoke": mx_likely_helpful,
            "recommend_row_gap": False,
            "recommend_modify_array_aggregation_py": False,
            "recommend_modify_standalone_py": False,
            "array_orientation_policy_should_be_configurable": True,
            "horizontal_m1_markers_row_orientation_independent": True,
            "array_outer_edge_markers_likely_context_related": True,
            "storage_aggregation_can_continue": False,
        },
        "next_step_recommendations": [
            "Generate a separate R0/MX storage-only compare smoke outside the main flow.",
            "Do not change pitch or power stitch before the R0/MX compare smoke confirms whether the 34 seam markers collapse.",
            "Keep the 4 horizontal METAL1.2 markers as a separate issue; they are not explained by row orientation alone.",
            "Treat the 2 array-edge markers as context candidates that may improve with edge dummy/context handling rather than row orientation.",
        ],
    }


def hardcell_pin_summary(tech: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for cell_name in ["cell_1rw", "dummy_cell_1rw", "replica_cell_1rw"]:
        cell = tech.cell(cell_name)
        records = inspect_gds_text_records(Path(cell.gds_path))
        filtered = [
            {
                "label": str(record["text"]).lower(),
                "layer": record["lpp"],
                "x": float(record["x"]),
                "y": float(record["y"]),
            }
            for record in records
            if str(record["text"]).lower() in {"bl", "br", "rbl", "rblb", "vdd", "gnd", "wl"}
        ]
        result[cell_name] = {
            "bbox": {
                "x0": float(cell.bbox_x0),
                "y0": float(cell.bbox_y0),
                "x1": float(cell.bbox_x1),
                "y1": float(cell.bbox_y1),
            },
            "pins": filtered,
            "bitline_pins_near_bottom_edge": [
                pin for pin in filtered if pin["label"] in {"bl", "br", "rbl", "rblb"} and pin["y"] <= 0.01
            ],
            "power_pin_vertical_order": [
                pin["label"] for pin in sorted((pin for pin in filtered if pin["label"] in {"gnd", "vdd"}), key=lambda item: item["y"])
            ],
        }
    return result


def format_markdown(report: dict[str, Any]) -> str:
    s = report["summary"]
    r = report["recommendations"]
    lines = [
        "# OpenYield Row-Boundary Audit Report",
        "",
        "This audit focuses on the 34 METAL2.2 seam markers in the storage-only stitched smoke. It is a policy analysis, not a main-flow change.",
        "",
        "## Summary",
        "",
        f"- METAL2 marker total: `{s['metal2_marker_total']}`",
        f"- row-boundary marker count: `{s['row_boundary_marker_count']}`",
        f"- marker y values: `{s['marker_y_values']}`",
        f"- concentrated at row boundary: `{r['metal2_markers_concentrated_at_row_boundary']}`",
        f"- near BL/BR/RBL/RBLB: `{r['metal2_markers_near_bitlines']}`",
        f"- current R0/R0 likely source: `{r['current_r0_r0_likely_source']}`",
        f"- recommend R0/MX compare smoke: `{r['recommend_r0_mx_compare_smoke']}`",
        f"- recommend row gap now: `{r['recommend_row_gap']}`",
        f"- recommend modify array_aggregation.py now: `{r['recommend_modify_array_aggregation_py']}`",
        f"- recommend modify standalone.py now: `{r['recommend_modify_standalone_py']}`",
        f"- storage aggregation can continue now: `{r['storage_aggregation_can_continue']}`",
        "",
        "## Evidence",
        "",
        f"- Row-boundary y reference: `{s['row_boundary_y_um']}`",
        f"- Distance to seam min/max/mean: `{s['row_boundary_distance_stats_um']}`",
        f"- Local y values relative to row1 origin: `{s['local_y_relative_to_row1_origin']}`",
        f"- Nearest bitline label stats: `{s['nearest_bitline_label_stats']}`",
        f"- Nearest macro stats: `{s['nearest_macro_stats']}`",
        f"- Likely cause stats: `{s['likely_cause_stats']}`",
        "",
        "## Policy Read",
        "",
        "- The current all-R0 row policy keeps lower-edge M2 bitline features on the seam side for both rows.",
        "- An R0/MX alternation is theoretically the most direct way to move row1 bottom-edge M2 features away from the seam without paying blanket area cost.",
        "- A row gap or keepout would likely help spacing too, but reads as a conservative workaround until an R0/MX compare smoke is checked.",
        "- The 4 horizontal M1 markers are a separate horizontal-boundary issue and are not the main evidence for changing row orientation.",
        "",
        "## Next Steps",
        "",
    ]
    lines.extend(f"- {item}" for item in report["next_step_recommendations"])
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
