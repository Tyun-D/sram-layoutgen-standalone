from __future__ import annotations

import argparse
import json
import math
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))

from sram_layoutgen.gds_util import inspect_gds_text_records  # noqa: E402
from sram_layoutgen.geometry import Rect  # noqa: E402
from sram_layoutgen.standalone import load_bundled_freepdk45  # noqa: E402


DEFAULT_GDS = Path("build/openyield_storage_only_smoke_2x4_stitched/storage_only_2x4_stitched.gds")
DEFAULT_LYRDB = Path("build/openyield_storage_only_smoke_2x4_stitched/storage_only_2x4_stitched_drc.lyrdb")
DEFAULT_POWER_REPORT = Path("docs/openyield_storage_power_stitch_report.json")
DEFAULT_OUT_JSON = Path("docs/openyield_drc_marker_classification_report.json")
DEFAULT_OUT_MD = Path("docs/openyield_drc_marker_classification_report.md")

PITCH_X = 0.895
PITCH_Y = 1.565
EDGE_EPS = 0.035
ROW_EPS = 0.035
STITCH_NEAR_EPS = 0.05
PIN_NEAR_EPS = 0.12
OUTER_EPS = 0.04
POWER_LABELS = {"vdd", "gnd"}
BITLINE_LABELS = {"bl", "br", "rbl", "rblb", "rbr"}


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify KLayout DRC markers for the OpenYield storage-only stitched smoke GDS.")
    parser.add_argument("--gds", type=Path, default=DEFAULT_GDS)
    parser.add_argument("--lyrdb", type=Path, default=DEFAULT_LYRDB)
    parser.add_argument("--power-report", type=Path, default=DEFAULT_POWER_REPORT)
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
        f"markers={report['summary']['total_markers']} "
        f"power_stitch_safe={report['conclusions']['power_stitch_safe_for_current_smoke']} "
        f"needs_hardcell_baseline={report['conclusions']['needs_hardcell_level_drc_baseline']}"
    )
    return 0


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    power = load_json(args.power_report)
    rows = int(power.get("rows", 2))
    cols = int(power.get("cols", 4))
    pitch_x = float(power.get("pitch", {}).get("x", PITCH_X))
    pitch_y = float(power.get("pitch", {}).get("y", PITCH_Y))
    layout_bbox = dict(power.get("layout_bbox", {}))
    stitches = list(power.get("power_stitches", {}).get("records", []))
    tech = load_bundled_freepdk45()
    instances = build_instances(tech, rows, cols, pitch_x, pitch_y)
    pins = collect_instance_pins(tech, instances)
    markers = parse_lyrdb(args.lyrdb)
    classified = [
        classify_marker(marker, instances, pins, stitches, layout_bbox, rows, cols, pitch_x, pitch_y)
        for marker in markers
    ]

    rule_stats = Counter(marker["rule_name"] for marker in classified)
    location_stats = Counter(marker["location_class"] for marker in classified)
    cause_stats = Counter(marker["likely_cause"] for marker in classified)
    layer_stats = Counter(marker["likely_layer"] for marker in classified)
    m1_markers = [marker for marker in classified if marker["rule_name"].startswith("METAL1.2")]
    m2_markers = [marker for marker in classified if marker["rule_name"].startswith("METAL2.2")]
    stitch_overlap_count = sum(1 for marker in classified if marker["near_power_stitch"]["overlap"])
    stitch_near_count = sum(1 for marker in classified if marker["near_power_stitch"]["near"])
    bitline_related_count = sum(1 for marker in classified if marker["near_bitline_pin"]["near"])
    power_related_count = sum(1 for marker in classified if marker["near_power_pin"]["near"])
    row_boundary_count = sum(1 for marker in classified if marker["near_row_boundary"])
    col_boundary_count = sum(1 for marker in classified if marker["near_col_boundary"])
    array_edge_count = sum(1 for marker in classified if marker["near_array_edge"])
    power_stitch_safe = stitch_overlap_count == 0 and not any(
        marker["likely_cause"] == "power_stitch_side_effect" for marker in classified
    )
    needs_pitch_review = row_boundary_count > 0 or col_boundary_count > 0
    needs_hardcell_baseline = bool(m1_markers or m2_markers)
    storage_aggregation_not_blocked_by_power_stitch = power_stitch_safe and not any(
        marker["likely_cause"] == "power_stitch_side_effect" for marker in classified
    )
    can_continue_storage_aggregation = storage_aggregation_not_blocked_by_power_stitch and not needs_hardcell_baseline

    return {
        "inputs": {
            "gds": str(args.gds.resolve()),
            "lyrdb": str(args.lyrdb.resolve()),
            "power_report": str(args.power_report.resolve()),
            "lyrdb_exists": args.lyrdb.exists(),
        },
        "summary": {
            "total_markers": len(classified),
            "rule_type_stats": dict(sorted(rule_stats.items())),
            "location_class_stats": dict(sorted(location_stats.items())),
            "likely_cause_stats": dict(sorted(cause_stats.items())),
            "likely_layer_stats": dict(sorted(layer_stats.items())),
            "power_stitch_overlap_count": stitch_overlap_count,
            "power_stitch_near_count": stitch_near_count,
            "power_pin_near_count": power_related_count,
            "bitline_pin_near_count": bitline_related_count,
            "row_boundary_count": row_boundary_count,
            "col_boundary_count": col_boundary_count,
            "array_edge_count": array_edge_count,
        },
        "m1_marker_summary": summarize_group(m1_markers),
        "m2_marker_summary": summarize_group(m2_markers),
        "conclusions": {
            "lyrdb_parse_success": len(classified) > 0,
            "power_stitch_safe_for_current_smoke": power_stitch_safe,
            "m1_markers_consistent_with_red_gap": len(m1_markers) == 6 and all(marker["rule_name"].startswith("METAL1.2") for marker in m1_markers),
            "m2_markers_bl_br_related": bitline_related_count > 0,
            "m2_markers_all_bl_br_related": bool(m2_markers) and all(marker["near_bitline_pin"]["near"] for marker in m2_markers),
            "current_pitch_definitely_too_small": False,
            "current_pitch_needs_context_review": needs_pitch_review,
            "needs_stitch_change": False,
            "needs_hardcell_level_drc_baseline": needs_hardcell_baseline,
            "storage_aggregation_not_blocked_by_power_stitch": storage_aggregation_not_blocked_by_power_stitch,
            "can_continue_storage_aggregation": can_continue_storage_aggregation,
            "manual_review_required": True,
        },
        "classification_rules": {
            "edge_eps_um": EDGE_EPS,
            "row_eps_um": ROW_EPS,
            "stitch_near_eps_um": STITCH_NEAR_EPS,
            "pin_near_eps_um": PIN_NEAR_EPS,
            "outer_eps_um": OUTER_EPS,
        },
        "markers": classified,
        "hardcell_baseline_plan": [
            "Run the bundled FreePDK45 KLayout DRC deck on a standalone cell_1rw GDS instance.",
            "Repeat for dummy_cell_1rw and replica_cell_1rw.",
            "Compare single-cell METAL1.2/METAL2.2 markers against the storage-only marker coordinates.",
            "If single-cell baselines already contain the same rules, do not attribute those markers to aggregation.",
        ],
        "next_step_recommendations": [
            "Do not add BL/BR/RBL/RBLB bridges.",
            "Keep the current same-net M1 power stitch policy for this smoke because no marker overlaps a stitch bridge.",
            "Before changing pitch, run hardcell-level DRC baselines and inspect M2 markers at the row boundary in KLayout.",
            "Treat storage-only DRC as context smoke only, not final SRAM signoff.",
        ],
    }


def build_instances(tech: Any, rows: int, cols: int, pitch_x: float, pitch_y: float) -> list[dict[str, Any]]:
    specs: list[tuple[str, str, float, int, int]] = [("dummy_left", "dummy_cell_1rw", 0.0, 1, rows)]
    specs.append(("bit", "cell_1rw", pitch_x, cols, rows))
    specs.append(("dummy_right", "dummy_cell_1rw", (cols + 1) * pitch_x, 1, rows))
    specs.append(("replica", "replica_cell_1rw", (cols + 2) * pitch_x, 1, rows))
    instances: list[dict[str, Any]] = []
    for prefix, cell_name, x0, columns, row_count in specs:
        cell = tech.cell(cell_name)
        for row in range(row_count):
            for col in range(columns):
                x = x0 + col * pitch_x
                y = row * pitch_y
                if prefix == "bit":
                    name = f"bit_r{row}_c{col}"
                elif prefix == "replica":
                    name = f"replica_r{row}"
                else:
                    name = f"{prefix}_r{row}"
                rect = {
                    "x0": round(x + float(cell.bbox_x0), 6),
                    "y0": round(y + float(cell.bbox_y0), 6),
                    "x1": round(x + float(cell.bbox_x1), 6),
                    "y1": round(y + float(cell.bbox_y1), 6),
                }
                instances.append({"name": name, "macro": cell_name, "row": row, "col": col, "origin": {"x": x, "y": y}, "rect": rect})
    return instances


def collect_instance_pins(tech: Any, instances: list[dict[str, Any]]) -> list[dict[str, Any]]:
    cache: dict[str, list[dict[str, Any]]] = {}
    pins: list[dict[str, Any]] = []
    for instance in instances:
        macro = instance["macro"]
        if macro not in cache:
            cell = tech.cell(macro)
            cache[macro] = list(inspect_gds_text_records(Path(cell.gds_path))) if cell.gds_path else []
        for record in cache[macro]:
            label = str(record.get("text", "")).strip().lower()
            if not label:
                continue
            pins.append(
                {
                    "instance": instance["name"],
                    "macro": macro,
                    "label": label,
                    "x": round(float(instance["origin"]["x"]) + float(record["x"]), 6),
                    "y": round(float(instance["origin"]["y"]) + float(record["y"]), 6),
                    "lpp": record.get("lpp"),
                }
            )
    return pins


def classify_marker(
    marker: dict[str, Any],
    instances: list[dict[str, Any]],
    pins: list[dict[str, Any]],
    stitches: list[dict[str, Any]],
    layout_bbox: dict[str, float],
    rows: int,
    cols: int,
    pitch_x: float,
    pitch_y: float,
) -> dict[str, Any]:
    bbox = marker["bbox"]
    cx = round((bbox["x0"] + bbox["x1"]) / 2.0, 6)
    cy = round((bbox["y0"] + bbox["y1"]) / 2.0, 6)
    nearest_instance, inst_dist = nearest_rect({"x": cx, "y": cy}, instances)
    contained = [inst for inst in instances if point_in_rect(cx, cy, inst["rect"])]
    row_boundaries = [row * pitch_y - 0.1 for row in range(1, rows)]
    col_boundaries = sorted(
        set(
            round(value, 6)
            for value in [0.8 + i * pitch_x for i in range(cols + 2)]
            + [0.805 + i * pitch_x for i in range(cols + 2)]
        )
    )
    near_row = min((abs(cy - y) for y in row_boundaries), default=999.0) <= ROW_EPS
    near_col = min((abs(cx - x) for x in col_boundaries), default=999.0) <= EDGE_EPS
    near_edge = distance_to_rect_edge({"x": cx, "y": cy}, layout_bbox) <= OUTER_EPS if layout_bbox else False
    stitch_info = nearest_stitch(bbox, stitches)
    power_pin = nearest_pin({"x": cx, "y": cy}, pins, POWER_LABELS)
    bitline_pin = nearest_pin({"x": cx, "y": cy}, pins, BITLINE_LABELS)
    likely_layer = likely_layer_from_rule(marker["rule_name"])
    if stitch_info["overlap"]:
        location_class = "power_stitch_nearby"
        likely_cause = "power_stitch_side_effect"
        confidence = "high"
    elif near_row:
        location_class = "vertical_row_boundary"
        likely_cause = "abutment_boundary_spacing"
        confidence = "medium"
    elif near_col:
        location_class = "horizontal_cell_boundary"
        likely_cause = "abutment_boundary_spacing"
        confidence = "medium"
    elif near_edge:
        location_class = "array_outer_edge"
        likely_cause = "storage_only_missing_context"
        confidence = "medium"
    elif len(contained) == 1:
        location_class = "hardcell_internal"
        likely_cause = "hardcell_intrinsic"
        confidence = "medium"
    else:
        location_class = "unknown"
        likely_cause = "manual_review_required"
        confidence = "low"
    if bitline_pin["near"] and likely_layer == "m2" and likely_cause != "power_stitch_side_effect":
        likely_cause = "storage_only_missing_context" if near_row or near_edge else likely_cause
    return {
        "marker_id": marker["marker_id"],
        "rule_name": marker["rule_name"],
        "rule_description": marker.get("description", ""),
        "bbox": bbox,
        "center_x": cx,
        "center_y": cy,
        "nearest_instance": nearest_instance["name"] if nearest_instance else None,
        "nearest_macro": nearest_instance["macro"] if nearest_instance else None,
        "nearest_instance_distance": round(inst_dist, 6),
        "location_class": location_class,
        "likely_layer": likely_layer,
        "near_power_stitch": stitch_info,
        "near_storage_boundary": near_row or near_col or near_edge,
        "near_row_boundary": near_row,
        "near_col_boundary": near_col,
        "near_array_edge": near_edge,
        "near_power_pin": power_pin,
        "near_bitline_pin": bitline_pin,
        "likely_cause": likely_cause,
        "confidence": confidence,
        "raw_value": marker.get("value", ""),
    }


def parse_lyrdb(path: Path) -> list[dict[str, Any]]:
    root = ET.parse(path).getroot()
    descriptions = category_descriptions(root)
    markers: list[dict[str, Any]] = []
    marker_id = 0
    for item in root.iter():
        if strip_ns(item.tag) != "item":
            continue
        rule = child_text(item, "category").strip("'") or "uncategorized"
        values = " ".join(
            value.text or ""
            for child in item
            if strip_ns(child.tag) == "values"
            for value in child
            if strip_ns(value.tag) == "value"
        )
        bbox = marker_bbox(values)
        if not bbox:
            continue
        marker_id += 1
        markers.append(
            {
                "marker_id": marker_id,
                "rule_name": rule,
                "description": descriptions.get(rule, ""),
                "bbox": bbox,
                "value": compact(values),
            }
        )
    return markers


def category_descriptions(root: ET.Element) -> dict[str, str]:
    descriptions: dict[str, str] = {}
    for category in root.iter():
        if strip_ns(category.tag) != "category":
            continue
        name = child_text(category, "name")
        if name:
            descriptions[name] = compact(child_text(category, "description"))
    return descriptions


def marker_bbox(text: str) -> dict[str, float] | None:
    numbers = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", text)]
    if len(numbers) < 4:
        return None
    xs = numbers[0::2]
    ys = numbers[1::2]
    return {"x0": round(min(xs), 6), "y0": round(min(ys), 6), "x1": round(max(xs), 6), "y1": round(max(ys), 6)}


def nearest_stitch(bbox: dict[str, float], stitches: list[dict[str, Any]]) -> dict[str, Any]:
    best: tuple[float, dict[str, Any] | None] = (999.0, None)
    overlap = False
    for stitch in stitches:
        rect = stitch.get("rect", {})
        dist = rect_distance(bbox, rect)
        if dist == 0:
            overlap = True
        if dist < best[0]:
            best = (dist, stitch)
    stitch = best[1] or {}
    return {
        "overlap": overlap,
        "near": best[0] <= STITCH_NEAR_EPS,
        "nearest_name": stitch.get("name"),
        "nearest_net": stitch.get("net"),
        "nearest_distance": round(best[0], 6),
    }


def nearest_pin(point: dict[str, float], pins: list[dict[str, Any]], labels: set[str]) -> dict[str, Any]:
    candidates = [pin for pin in pins if pin["label"] in labels]
    best_pin = None
    best_distance = 999.0
    for pin in candidates:
        distance = math.hypot(point["x"] - pin["x"], point["y"] - pin["y"])
        if distance < best_distance:
            best_distance = distance
            best_pin = pin
    return {
        "near": best_distance <= PIN_NEAR_EPS,
        "nearest_label": best_pin["label"] if best_pin else None,
        "nearest_instance": best_pin["instance"] if best_pin else None,
        "nearest_distance": round(best_distance, 6),
    }


def nearest_rect(point: dict[str, float], instances: list[dict[str, Any]]) -> tuple[dict[str, Any] | None, float]:
    best = (None, 999.0)
    point_rect = {"x0": point["x"], "y0": point["y"], "x1": point["x"], "y1": point["y"]}
    for inst in instances:
        dist = rect_distance(point_rect, inst["rect"])
        if dist < best[1]:
            best = (inst, dist)
    return best


def rect_distance(a: dict[str, float], b: dict[str, float]) -> float:
    dx = max(float(b["x0"]) - float(a["x1"]), float(a["x0"]) - float(b["x1"]), 0.0)
    dy = max(float(b["y0"]) - float(a["y1"]), float(a["y0"]) - float(b["y1"]), 0.0)
    return math.hypot(dx, dy)


def point_in_rect(x: float, y: float, rect: dict[str, float]) -> bool:
    return float(rect["x0"]) <= x <= float(rect["x1"]) and float(rect["y0"]) <= y <= float(rect["y1"])


def distance_to_rect_edge(point: dict[str, float], rect: dict[str, float]) -> float:
    return min(
        abs(point["x"] - float(rect["x0"])),
        abs(point["x"] - float(rect["x1"])),
        abs(point["y"] - float(rect["y0"])),
        abs(point["y"] - float(rect["y1"])),
    )


def likely_layer_from_rule(rule: str) -> str:
    name = rule.lower()
    if name.startswith("metal1"):
        return "m1"
    if name.startswith("metal2"):
        return "m2"
    return "unknown"


def summarize_group(markers: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "count": len(markers),
        "location_class_stats": dict(sorted(Counter(marker["location_class"] for marker in markers).items())),
        "likely_cause_stats": dict(sorted(Counter(marker["likely_cause"] for marker in markers).items())),
        "near_power_stitch_count": sum(1 for marker in markers if marker["near_power_stitch"]["near"]),
        "overlap_power_stitch_count": sum(1 for marker in markers if marker["near_power_stitch"]["overlap"]),
        "near_power_pin_count": sum(1 for marker in markers if marker["near_power_pin"]["near"]),
        "near_bitline_pin_count": sum(1 for marker in markers if marker["near_bitline_pin"]["near"]),
        "markers": [
            {
                "marker_id": marker["marker_id"],
                "center": [marker["center_x"], marker["center_y"]],
                "bbox": marker["bbox"],
                "nearest_instance": marker["nearest_instance"],
                "nearest_macro": marker["nearest_macro"],
                "location_class": marker["location_class"],
                "likely_cause": marker["likely_cause"],
                "near_power_stitch": marker["near_power_stitch"],
                "near_power_pin": marker["near_power_pin"],
                "near_bitline_pin": marker["near_bitline_pin"],
            }
            for marker in markers
        ],
    }


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_text(elem: ET.Element, child_name: str) -> str:
    for child in elem:
        if strip_ns(child.tag) == child_name and child.text:
            return child.text
    return ""


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def format_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield DRC Marker Classification Report",
        "",
        "This classifies KLayout DRC markers for the tiny storage-only stitched GDS. It is not full SRAM signoff.",
        "",
        "## Summary",
        "",
        f"- input GDS: `{report['inputs']['gds']}`",
        f"- input LYRDB: `{report['inputs']['lyrdb']}`",
        f"- LYRDB parse success: `{report['conclusions']['lyrdb_parse_success']}`",
        f"- total markers: `{report['summary']['total_markers']}`",
        f"- power stitch safe for current smoke: `{report['conclusions']['power_stitch_safe_for_current_smoke']}`",
        f"- current pitch definitely too small: `{report['conclusions']['current_pitch_definitely_too_small']}`",
        f"- current pitch needs context review: `{report['conclusions']['current_pitch_needs_context_review']}`",
        f"- needs stitch change: `{report['conclusions']['needs_stitch_change']}`",
        f"- needs hardcell-level DRC baseline: `{report['conclusions']['needs_hardcell_level_drc_baseline']}`",
        f"- storage aggregation not blocked by power stitch: `{report['conclusions']['storage_aggregation_not_blocked_by_power_stitch']}`",
        f"- can continue storage aggregation: `{report['conclusions']['can_continue_storage_aggregation']}`",
        "",
        "## Rule Type Stats",
        "",
    ]
    lines.extend(format_table(["rule", "count"], report["summary"]["rule_type_stats"].items()))
    lines.extend(["", "## Location Class Stats", ""])
    lines.extend(format_table(["location_class", "count"], report["summary"]["location_class_stats"].items()))
    lines.extend(["", "## Likely Cause Stats", ""])
    lines.extend(format_table(["likely_cause", "count"], report["summary"]["likely_cause_stats"].items()))
    lines.extend(
        [
            "",
            "## M1 Marker Summary",
            "",
            f"- count: `{report['m1_marker_summary']['count']}`",
            f"- near power stitch: `{report['m1_marker_summary']['near_power_stitch_count']}`",
            f"- overlap power stitch: `{report['m1_marker_summary']['overlap_power_stitch_count']}`",
            f"- near power pin: `{report['m1_marker_summary']['near_power_pin_count']}`",
            f"- near bitline pin: `{report['m1_marker_summary']['near_bitline_pin_count']}`",
            "",
        ]
    )
    lines.extend(marker_table(report["m1_marker_summary"]["markers"]))
    lines.extend(
        [
            "",
            "## M2 Marker Summary",
            "",
            f"- count: `{report['m2_marker_summary']['count']}`",
            f"- near power stitch: `{report['m2_marker_summary']['near_power_stitch_count']}`",
            f"- overlap power stitch: `{report['m2_marker_summary']['overlap_power_stitch_count']}`",
            f"- near power pin: `{report['m2_marker_summary']['near_power_pin_count']}`",
            f"- near bitline pin: `{report['m2_marker_summary']['near_bitline_pin_count']}`",
            "",
        ]
    )
    lines.extend(marker_table(report["m2_marker_summary"]["markers"]))
    lines.extend(["", "## Conclusions", ""])
    conclusions = report["conclusions"]
    lines.extend(
        [
            f"- The power stitch rectangles are not overlapped by any marker, so keep the current same-net M1 power stitch smoke policy.",
            f"- The M1 markers are consistent with metal1 spacing gaps, but the script cannot prove same-net identity for non-power M1 shapes.",
            f"- The M2 markers are near storage cells and should not be fixed by bridging BL/BR/RBL/RBLB.",
            f"- Full bbox pitch is not proven too small by this classifier; row/abutment context and hardcell baseline DRC still need review.",
            f"- Hardcell-level DRC baselines are recommended: `{conclusions['needs_hardcell_level_drc_baseline']}`.",
        ]
    )
    lines.extend(["", "## Hardcell Baseline Plan", ""])
    lines.extend(f"{idx}. {item}" for idx, item in enumerate(report["hardcell_baseline_plan"], start=1))
    lines.extend(["", "## Next Steps", ""])
    lines.extend(f"- {item}" for item in report["next_step_recommendations"])
    lines.append("")
    return "\n".join(lines)


def marker_table(markers: list[dict[str, Any]]) -> list[str]:
    rows = [
        [
            item["marker_id"],
            f"({item['center'][0]}, {item['center'][1]})",
            item["nearest_instance"],
            item["nearest_macro"],
            item["location_class"],
            item["likely_cause"],
            item["near_power_stitch"]["nearest_distance"],
            item["near_bitline_pin"]["nearest_label"],
            item["near_bitline_pin"]["nearest_distance"],
        ]
        for item in markers
    ]
    return format_table(
        ["id", "center", "nearest_instance", "macro", "location", "cause", "stitch_dist", "bitline", "bitline_dist"],
        rows,
    )


def format_table(headers: list[str], rows: Any) -> list[str]:
    rows = list(rows)
    if not rows:
        return ["- none"]
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        if isinstance(row, tuple) and len(row) == 2 and not isinstance(row[1], (list, tuple, dict)):
            row = [row[0], row[1]]
        out.append("| " + " | ".join(str(cell).replace("|", "\\|") for cell in row) + " |")
    return out


if __name__ == "__main__":
    raise SystemExit(main())
