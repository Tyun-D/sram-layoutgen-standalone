from __future__ import annotations

import argparse
import json
import struct
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))

from sram_layoutgen.gds_util import inspect_gds_text_records, measure_gds_bbox  # noqa: E402
from sram_layoutgen.geometry import Rect  # noqa: E402
from sram_layoutgen.openram_placement import placed_bbox_from_openram_origin  # noqa: E402
from sram_layoutgen.standalone import load_bundled_freepdk45  # noqa: E402


POWER_LABELS = {"vdd", "gnd"}
BITLINE_LABELS = {"bl", "br", "rbl", "rblb"}
WORDLINE_LABELS = {"wl"}
ROUTING_LABELS = POWER_LABELS | BITLINE_LABELS | WORDLINE_LABELS
HARMLESS_LAYER_CLASSES = {"well", "implant", "threshold", "text_marker", "power_rail"}
RISK_LAYER_CLASSES = {"active", "poly", "contact", "via", "signal_metal", "unknown"}
AREA_EPS = 1e-12


@dataclass(frozen=True)
class GdsShape:
    layer: int
    datatype: int
    lpp: str
    layer_name: str
    rect: Rect


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit legal abutment pitch for storage-array GDS cells.")
    parser.add_argument("--tech-dir", default="technology/freepdk45")
    parser.add_argument("--macros", nargs="+", default=["cell_1rw", "dummy_cell_1rw", "replica_cell_1rw"])
    parser.add_argument("--legacy-pitch-x", type=float, required=True)
    parser.add_argument("--legacy-pitch-y", type=float, required=True)
    parser.add_argument("--audit-pitch-x", type=float, required=True)
    parser.add_argument("--audit-pitch-y", type=float, required=True)
    parser.add_argument("--out-json", default="docs/openyield_storage_pitch_audit_report.json")
    parser.add_argument("--out-md", default="docs/openyield_storage_pitch_audit_report.md")
    args = parser.parse_args()

    tech = load_bundled_freepdk45()
    lpp_to_layer = build_lpp_layer_map(args.tech_dir)
    macro_reports = [
        audit_macro(
            tech,
            macro,
            lpp_to_layer,
            args.legacy_pitch_x,
            args.legacy_pitch_y,
            args.audit_pitch_x,
            args.audit_pitch_y,
        )
        for macro in args.macros
    ]
    policy = recommend_policy(macro_reports)
    report = {
        "inputs": {
            "tech_dir": args.tech_dir,
            "macros": args.macros,
            "legacy_pitch": {"x": args.legacy_pitch_x, "y": args.legacy_pitch_y},
            "audit_bbox_pitch": {"x": args.audit_pitch_x, "y": args.audit_pitch_y},
        },
        "recommended_storage_pitch_policy": policy["policy"],
        "policy_reason": policy["reason"],
        "area_impact": policy["area_impact"],
        "drc_risk": policy["drc_risk"],
        "lvs_risk": policy["lvs_risk"],
        "openyield_netlist_semantic_relation": (
            "Pitch policy is physical-layout metadata only. It does not change OpenYield netlist hierarchy, "
            "ports, or instance connectivity."
        ),
        "keep_enable_openyield_array_aggregation_default_closed": True,
        "connectivity_not_proven": True,
        "manual_layout_review_required": True,
        "macros": macro_reports,
        "should_modify_array_aggregation_py": False,
        "array_aggregation_py_recommendation": (
            "Do not change array_aggregation.py yet. First decide whether to add separate "
            "physical_bbox_pitch, legal_abutment_pitch, routing_keepout_pitch, and report_bbox_pitch metadata."
        ),
        "next_step_recommendations": [
            "Keep the OpenYield enabled path on full bbox pitch for now; use legacy logical marker pitch only as an area baseline unless DRC/manual review proves the overlap is legal.",
            "Add explicit pitch metadata fields before changing the enabled OpenYield aggregation path.",
            "Run KLayout visual/DRC review on a tiny storage-only array to classify well/implant/rail stitching versus illegal active/poly overlap.",
        ],
    }

    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(format_markdown(report), encoding="utf-8")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(f"recommended_storage_pitch_policy={report['recommended_storage_pitch_policy']}")
    for item in macro_reports:
        legacy = item["legacy_pitch_overlap"]
        print(
            f"{item['macro']}: legacy bbox overlap x={legacy['bbox_overlap_x']} "
            f"y={legacy['bbox_overlap_y']} safe={legacy['classification']['acceptable_as_legal_abutment']}"
        )
    return 0


def audit_macro(
    tech: Any,
    macro: str,
    lpp_to_layer: dict[str, str],
    legacy_pitch_x: float,
    legacy_pitch_y: float,
    audit_pitch_x: float,
    audit_pitch_y: float,
) -> dict[str, Any]:
    cell = tech.cell(macro)
    if cell.gds_path is None:
        raise ValueError(f"macro has no GDS path: {macro}")
    path = Path(cell.gds_path)
    shapes = parse_gds_shapes(path, lpp_to_layer)
    text_records = inspect_gds_text_records(path)
    physical_bbox = measure_gds_bbox(path, ignored_layers={239})
    marker_bbox = measure_gds_bbox(path, boundary_layers={239})
    if physical_bbox is None:
        raise ValueError(f"no physical shapes found in {path}")

    pin_bboxes = extract_pin_bboxes(text_records, shapes)
    boundary_extension = {
        "left": rounded(0.0 - physical_bbox.x0),
        "right": rounded(physical_bbox.x1 - cell.width),
        "bottom": rounded(0.0 - physical_bbox.y0),
        "top": rounded(physical_bbox.y1 - cell.height),
        "negative_origin": physical_bbox.x0 < 0.0 or physical_bbox.y0 < 0.0,
    }

    legacy = pitch_overlap_report(cell, shapes, pin_bboxes, legacy_pitch_x, legacy_pitch_y, "legacy_logical_marker_pitch")
    audit = pitch_overlap_report(cell, shapes, pin_bboxes, audit_pitch_x, audit_pitch_y, "audit_full_bbox_pitch")
    recommended = recommend_macro_pitch(cell, legacy, audit)
    return {
        "macro": macro,
        "gds_path": str(path),
        "logical_marker_pitch": {"x": rounded(cell.width), "y": rounded(cell.height)},
        "gds_bbox": bbox_to_dict(physical_bbox),
        "text_marker_bbox": bbox_to_dict(marker_bbox) if marker_bbox is not None else None,
        "pin_or_rail_bbox": pin_bboxes,
        "boundary_extension": boundary_extension,
        "legacy_pitch_overlap": legacy,
        "audit_bbox_pitch_overlap": audit,
        "recommended_pitch_x": recommended["x"],
        "recommended_pitch_y": recommended["y"],
        "confidence": recommended["confidence"],
        "reason": recommended["reason"],
        "connectivity_not_proven": True,
        "manual_layout_review_required": True,
    }


def pitch_overlap_report(
    cell: Any,
    shapes: list[GdsShape],
    pin_bboxes: dict[str, Any],
    pitch_x: float,
    pitch_y: float,
    name: str,
) -> dict[str, Any]:
    bbox_r0 = placed_bbox_from_openram_origin(cell, 0.0, 0.0, "R0")
    bbox_x = placed_bbox_from_openram_origin(cell, pitch_x, 0.0, "R0")
    bbox_y = placed_bbox_from_openram_origin(cell, 0.0, pitch_y, "MX")
    horizontal = overlap_shapes(
        place_shapes(shapes, cell, 0.0, 0.0, "R0"),
        place_shapes(shapes, cell, pitch_x, 0.0, "R0"),
        place_pin_bboxes(pin_bboxes, cell, 0.0, 0.0, "R0"),
        place_pin_bboxes(pin_bboxes, cell, pitch_x, 0.0, "R0"),
    )
    vertical = overlap_shapes(
        place_shapes(shapes, cell, 0.0, 0.0, "R0"),
        place_shapes(shapes, cell, 0.0, pitch_y, "MX"),
        place_pin_bboxes(pin_bboxes, cell, 0.0, 0.0, "R0"),
        place_pin_bboxes(pin_bboxes, cell, 0.0, pitch_y, "MX"),
    )
    bbox_overlap_x = max(0.0, min(bbox_r0.x1, bbox_x.x1) - max(bbox_r0.x0, bbox_x.x0))
    bbox_overlap_y = max(0.0, min(bbox_r0.y1, bbox_y.y1) - max(bbox_r0.y0, bbox_y.y0))
    classification = classify_overlap(horizontal, vertical)
    return {
        "pitch_name": name,
        "pitch_x": rounded(pitch_x),
        "pitch_y": rounded(pitch_y),
        "bbox_overlap_x": rounded(bbox_overlap_x),
        "bbox_overlap_y": rounded(bbox_overlap_y),
        "horizontal_neighbor": horizontal,
        "vertical_neighbor_r0_to_mx": vertical,
        "fully_bbox_separated": bbox_overlap_x <= 1e-9 and bbox_overlap_y <= 1e-9,
        "extra_gap_x": rounded(max(0.0, pitch_x - cell.bbox_x1 + cell.bbox_x0)),
        "extra_gap_y": rounded(max(0.0, pitch_y - cell.bbox_y1 + cell.bbox_y0)),
        "classification": classification,
    }


def parse_gds_shapes(path: Path, lpp_to_layer: dict[str, str]) -> list[GdsShape]:
    data = path.read_bytes()
    offset = 0
    db_unit_microns = 0.001
    in_boundary = False
    layer = None
    datatype = 0
    shapes: list[GdsShape] = []
    while offset + 4 <= len(data):
        size, record_type, _data_type = struct.unpack(">HBB", data[offset : offset + 4])
        if size < 4 or offset + size > len(data):
            break
        payload = data[offset + 4 : offset + size]
        if record_type == 0x03 and len(payload) >= 16:
            db_unit_meters = parse_gds_real8(payload[8:16])
            if db_unit_meters:
                db_unit_microns = db_unit_meters * 1e6
        elif record_type == 0x08:
            in_boundary = True
            layer = None
            datatype = 0
        elif record_type == 0x0D and in_boundary and len(payload) >= 2:
            layer = struct.unpack(">h", payload[:2])[0]
        elif record_type == 0x0E and in_boundary and len(payload) >= 2:
            datatype = struct.unpack(">h", payload[:2])[0]
        elif record_type == 0x10 and in_boundary and layer is not None:
            coords = [struct.unpack(">i", payload[i : i + 4])[0] for i in range(0, len(payload), 4)]
            xs = coords[0::2]
            ys = coords[1::2]
            rect = Rect(
                min(xs) * db_unit_microns,
                min(ys) * db_unit_microns,
                max(xs) * db_unit_microns,
                max(ys) * db_unit_microns,
            )
            lpp = f"{layer}/{datatype}"
            shapes.append(GdsShape(layer, datatype, lpp, lpp_to_layer.get(lpp, lpp), rect))
        elif record_type == 0x11:
            in_boundary = False
        offset += size
    return shapes


def extract_pin_bboxes(text_records: list[dict[str, object]], shapes: list[GdsShape]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for record in text_records:
        label = str(record["text"]).strip().lower()
        x = float(record["x"])
        y = float(record["y"])
        lpp = str(record["lpp"])
        candidates = [
            shape.rect
            for shape in shapes
            if shape.lpp == lpp and contains_point(shape.rect, x, y)
        ]
        if not candidates:
            candidates = [
                shape.rect
                for shape in shapes
                if shape.lpp == lpp and shape.rect.inflate(0.01).overlaps(Rect(x, y, x, y))
            ]
        rect = Rect.union(candidates) if candidates else Rect(x, y, x, y)
        result[label] = {
            "label": label,
            "lpp": lpp,
            "layer_name": next((shape.layer_name for shape in shapes if shape.lpp == lpp), lpp),
            "text_point": {"x": rounded(x), "y": rounded(y)},
            "bbox": rect_dict(rect),
            "found_boundary_shape": bool(candidates),
        }
    return result


def place_shapes(shapes: Iterable[GdsShape], cell: Any, x: float, y: float, mirror: str) -> list[GdsShape]:
    return [
        GdsShape(shape.layer, shape.datatype, shape.lpp, shape.layer_name, transform_rect(shape.rect, cell, x, y, mirror))
        for shape in shapes
        if shape.layer != 239
    ]


def place_pin_bboxes(pin_bboxes: dict[str, Any], cell: Any, x: float, y: float, mirror: str) -> dict[str, Rect]:
    placed: dict[str, Rect] = {}
    for label, item in pin_bboxes.items():
        bbox = item.get("bbox", {})
        placed[label] = transform_rect(
            Rect(float(bbox["x0"]), float(bbox["y0"]), float(bbox["x1"]), float(bbox["y1"])),
            cell,
            x,
            y,
            mirror,
        )
    return placed


def transform_rect(rect: Rect, cell: Any, xoffset: float, yoffset: float, mirror: str) -> Rect:
    ox = xoffset + (cell.width if mirror in {"MY", "XY"} else 0.0)
    oy = yoffset + (cell.height if mirror in {"MX", "XY"} else 0.0)
    if mirror in {"MY", "XY"}:
        x0, x1 = ox - rect.x1, ox - rect.x0
    else:
        x0, x1 = ox + rect.x0, ox + rect.x1
    if mirror in {"MX", "XY"}:
        y0, y1 = oy - rect.y1, oy - rect.y0
    else:
        y0, y1 = oy + rect.y0, oy + rect.y1
    return Rect(x0, y0, x1, y1)


def overlap_shapes(
    a_shapes: list[GdsShape],
    b_shapes: list[GdsShape],
    a_pins: dict[str, Rect],
    b_pins: dict[str, Rect],
) -> dict[str, Any]:
    by_lpp_b: dict[str, list[GdsShape]] = {}
    for shape in b_shapes:
        by_lpp_b.setdefault(shape.lpp, []).append(shape)
    overlaps: list[dict[str, Any]] = []
    layer_summary: dict[str, dict[str, Any]] = {}
    for left in a_shapes:
        for right in by_lpp_b.get(left.lpp, []):
            overlap = intersect_rect(left.rect, right.rect)
            if overlap is None or overlap.area <= AREA_EPS:
                continue
            labels = overlap_pin_labels(overlap, a_pins, b_pins)
            layer_class = classify_layer(left.layer_name, labels)
            overlaps.append(
                {
                    "layer": left.layer_name,
                    "lpp": left.lpp,
                    "class": layer_class,
                    "area": rounded(overlap.area),
                    "rect": rect_dict(overlap),
                    "pin_labels": sorted(labels),
                }
            )
            key = left.layer_name
            item = layer_summary.setdefault(
                key,
                {"lpp": left.lpp, "class": layer_class, "count": 0, "area": 0.0, "pin_labels": set()},
            )
            item["count"] += 1
            item["area"] += overlap.area
            item["pin_labels"].update(labels)
            if layer_class in RISK_LAYER_CLASSES:
                item["class"] = layer_class
    summary = []
    for layer, item in sorted(layer_summary.items()):
        summary.append(
            {
                "layer": layer,
                "lpp": item["lpp"],
                "class": item["class"],
                "count": item["count"],
                "area": rounded(item["area"]),
                "pin_labels": sorted(item["pin_labels"]),
            }
        )
    risky = [item for item in summary if item["class"] in RISK_LAYER_CLASSES]
    power_or_boundary = [item for item in summary if item["class"] in HARMLESS_LAYER_CLASSES]
    return {
        "overlap_count": len(overlaps),
        "total_overlap_area": rounded(sum(float(item["area"]) for item in overlaps)),
        "overlap_layers": summary,
        "risky_overlap_layers": risky,
        "power_or_boundary_overlap_layers": power_or_boundary,
        "sample_overlaps": overlaps[:20],
    }


def classify_overlap(horizontal: dict[str, Any], vertical: dict[str, Any]) -> dict[str, Any]:
    risky_layers = sorted(
        {
            item["layer"]
            for source in (horizontal, vertical)
            for item in source["risky_overlap_layers"]
        }
    )
    nonzero = horizontal["overlap_count"] > 0 or vertical["overlap_count"] > 0
    return {
        "has_real_shape_overlap": nonzero,
        "risky_layers": risky_layers,
        "mostly_power_or_boundary": nonzero and not risky_layers,
        "acceptable_as_legal_abutment": nonzero and not risky_layers,
        "connectivity_not_proven": True,
        "manual_layout_review_required": bool(risky_layers),
        "reason": (
            "Only well/implant/threshold/power-rail-like overlaps were found."
            if nonzero and not risky_layers
            else "Risk layers overlap; manual GDS/DRC review is required."
            if risky_layers
            else "No same-layer shape overlap was found."
        ),
    }


def classify_layer(layer_name: str, pin_labels: set[str]) -> str:
    name = layer_name.lower()
    if pin_labels & POWER_LABELS and name in {"m1", "metal1"}:
        return "power_rail"
    if name in {"pwell", "nwell"}:
        return "well"
    if name in {"nimplant", "pimplant"}:
        return "implant"
    if name in {"vtg", "vth", "thkox"}:
        return "threshold"
    if name in {"active"}:
        return "active"
    if name == "poly":
        return "poly"
    if name == "contact":
        return "contact"
    if name.startswith("via"):
        return "via"
    if name in {"m1", "m2", "m3", "m4", "metal1", "metal2", "metal3", "metal4"}:
        return "signal_metal" if not (pin_labels & POWER_LABELS) else "power_rail"
    if name in {"text"}:
        return "text_marker"
    return "unknown"


def recommend_macro_pitch(cell: Any, legacy: dict[str, Any], audit: dict[str, Any]) -> dict[str, Any]:
    if legacy["classification"]["acceptable_as_legal_abutment"]:
        return {
            "x": rounded(cell.width),
            "y": rounded(cell.height),
            "confidence": "medium",
            "reason": "Legacy logical marker pitch overlaps only classified harmless layers, but connectivity is not proven.",
        }
    if not audit["classification"]["has_real_shape_overlap"]:
        return {
            "x": rounded(audit["pitch_x"]),
            "y": rounded(audit["pitch_y"]),
            "confidence": "medium",
            "reason": "Full bbox pitch eliminates same-layer physical overlap; legacy pitch has risky overlaps.",
        }
    return {
        "x": rounded(audit["pitch_x"]),
        "y": rounded(audit["pitch_y"]),
        "confidence": "low",
        "reason": "Neither pitch is fully proven by this parser; manual GDS review is required.",
    }


def recommend_policy(macro_reports: list[dict[str, Any]]) -> dict[str, Any]:
    legacy_has_risky = any(
        item["legacy_pitch_overlap"]["classification"]["risky_layers"]
        for item in macro_reports
    )
    audit_has_overlap = any(
        item["audit_bbox_pitch_overlap"]["classification"]["has_real_shape_overlap"]
        for item in macro_reports
    )
    all_legacy_marker = all(
        abs(float(item["recommended_pitch_x"]) - float(item["logical_marker_pitch"]["x"])) < 1e-6
        and abs(float(item["recommended_pitch_y"]) - float(item["logical_marker_pitch"]["y"])) < 1e-6
        for item in macro_reports
    )
    if all_legacy_marker and not legacy_has_risky:
        return {
            "policy": "use_legacy_pitch",
            "reason": (
                "The legacy logical marker pitch is the OpenRAM placement pitch. This audit found bbox overlap, "
                "but no active/poly/contact/via/signal-metal overlap in the same-layer overlap regions."
            ),
            "area_impact": "Using legacy pitch avoids the 4.736% to 9.798% area increase observed with full bbox pitch.",
            "drc_risk": "medium: parser suggests overlaps are stitch/rail/boundary-like, but signoff DRC is not proven.",
            "lvs_risk": "low-to-medium: pitch does not alter netlist semantics, but physical rail/bitline continuity needs extraction review.",
        }
    if not audit_has_overlap:
        return {
            "policy": "use_full_bbox_pitch",
            "reason": "Full bbox pitch is conservative and eliminates same-layer physical overlap.",
            "area_impact": "Area increases by the amount measured in Step 4.6.",
            "drc_risk": "low for cell-cell overlap, higher for global placement/routing impact.",
            "lvs_risk": "low for pitch policy alone.",
        }
    return {
        "policy": "need_manual_gds_review",
        "reason": "The parser could not prove either pitch legally abuts all storage macros.",
        "area_impact": "Unknown until legal pitch is resolved.",
        "drc_risk": "unknown.",
        "lvs_risk": "unknown.",
    }


def build_lpp_layer_map(tech_dir: str) -> dict[str, str]:
    path = resolve_input(tech_dir) / "layers.map"
    mapping: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        parts = line.split()
        if len(parts) >= 4:
            mapping[f"{int(parts[2])}/{int(parts[3])}"] = normalize_layer_name(parts[0])
    return mapping


def normalize_layer_name(value: str) -> str:
    aliases = {"metal1": "m1", "metal2": "m2", "metal3": "m3", "metal4": "m4"}
    return aliases.get(value, value)


def format_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Storage Pitch Audit Report",
        "",
        "This report audits storage-cell legal abutment pitch using GDS boundary rectangles and TEXT pin records. It does not modify placement policy, routing, GDS writer behavior, shared rails, or peripheral aggregation.",
        "",
        "## Conclusion",
        "",
        f"- recommended_storage_pitch_policy: `{report['recommended_storage_pitch_policy']}`",
        f"- reason: {report['policy_reason']}",
        f"- area impact: {report['area_impact']}",
        f"- DRC risk: {report['drc_risk']}",
        f"- LVS risk: {report['lvs_risk']}",
        f"- OpenYield netlist semantics: {report['openyield_netlist_semantic_relation']}",
        f"- keep enable_openyield_array_aggregation default closed: `{report['keep_enable_openyield_array_aggregation_default_closed']}`",
        f"- connectivity_not_proven: `{report['connectivity_not_proven']}`",
        f"- manual_layout_review_required: `{report['manual_layout_review_required']}`",
        "",
        "## Macro Summary",
        "",
        md_table(
            [
                "macro",
                "bbox",
                "legacy overlap x/y",
                "legacy risky layers",
                "audit overlap",
                "recommended pitch",
                "confidence",
            ],
            [
                [
                    item["macro"],
                    bbox_text(item["gds_bbox"]),
                    f"{item['legacy_pitch_overlap']['bbox_overlap_x']} / {item['legacy_pitch_overlap']['bbox_overlap_y']}",
                    ", ".join(item["legacy_pitch_overlap"]["classification"]["risky_layers"]) or "-",
                    item["audit_bbox_pitch_overlap"]["classification"]["has_real_shape_overlap"],
                    f"{item['recommended_pitch_x']} x {item['recommended_pitch_y']}",
                    item["confidence"],
                ]
                for item in report["macros"]
            ],
        ),
        "",
    ]
    for item in report["macros"]:
        lines.extend(
            [
                f"## {item['macro']}",
                "",
                f"- GDS bbox: `{bbox_text(item['gds_bbox'])}`",
                f"- logical marker pitch: `{item['logical_marker_pitch']['x']} x {item['logical_marker_pitch']['y']}`",
                f"- text marker bbox: `{bbox_text(item['text_marker_bbox']) if item['text_marker_bbox'] else 'none'}`",
                f"- boundary extension: `{item['boundary_extension']}`",
                "",
                "Pin / rail bbox:",
                "",
                md_table(
                    ["pin", "layer", "point", "bbox", "found boundary"],
                    [
                        [
                            pin,
                            data["layer_name"],
                            data["text_point"],
                            bbox_text(data["bbox"]),
                            data["found_boundary_shape"],
                        ]
                        for pin, data in sorted(item["pin_or_rail_bbox"].items())
                    ],
                ),
                "",
                "Legacy pitch overlap:",
                "",
                overlap_block(item["legacy_pitch_overlap"]),
                "",
                "Audit bbox pitch overlap:",
                "",
                overlap_block(item["audit_bbox_pitch_overlap"]),
                "",
                f"Recommendation: `{item['recommended_pitch_x']} x {item['recommended_pitch_y']}` ({item['confidence']}) - {item['reason']}",
                "",
            ]
        )
    lines.extend(
        [
            "## Pitch Metadata Recommendation",
            "",
            "The generator should distinguish `physical_bbox_pitch`, `legal_abutment_pitch`, `routing_keepout_pitch`, and `report_bbox_pitch`. Full bbox pitch is useful for reporting and conservative spacing, while legal abutment pitch should remain a separate field until DRC/manual review proves the allowed overlap.",
            "",
            f"- should modify `array_aggregation.py` now: `{report['should_modify_array_aggregation_py']}`",
            f"- recommendation: {report['array_aggregation_py_recommendation']}",
            "",
            "## Next Steps",
            "",
            *[f"- {item}" for item in report["next_step_recommendations"]],
            "",
        ]
    )
    return "\n".join(lines)


def overlap_block(data: dict[str, Any]) -> str:
    return "\n".join(
        [
            f"- pitch: `{data['pitch_x']} x {data['pitch_y']}`",
            f"- bbox overlap x/y: `{data['bbox_overlap_x']} / {data['bbox_overlap_y']}`",
            f"- fully bbox separated: `{data['fully_bbox_separated']}`",
            f"- extra gap x/y: `{data['extra_gap_x']} / {data['extra_gap_y']}`",
            f"- classification: `{data['classification']}`",
            "",
            md_table(
                ["direction", "overlap count", "area", "layers", "risky layers"],
                [
                    [
                        "horizontal",
                        data["horizontal_neighbor"]["overlap_count"],
                        data["horizontal_neighbor"]["total_overlap_area"],
                        layer_list(data["horizontal_neighbor"]["overlap_layers"]),
                        layer_list(data["horizontal_neighbor"]["risky_overlap_layers"]),
                    ],
                    [
                        "vertical R0-MX",
                        data["vertical_neighbor_r0_to_mx"]["overlap_count"],
                        data["vertical_neighbor_r0_to_mx"]["total_overlap_area"],
                        layer_list(data["vertical_neighbor_r0_to_mx"]["overlap_layers"]),
                        layer_list(data["vertical_neighbor_r0_to_mx"]["risky_overlap_layers"]),
                    ],
                ],
            ),
        ]
    )


def layer_list(items: list[dict[str, Any]]) -> str:
    if not items:
        return "-"
    return ", ".join(f"{item['layer']}:{item['area']}" for item in items)


def bbox_text(rect: dict[str, Any] | None) -> str:
    if not rect:
        return "none"
    return f"({rect['x0']}, {rect['y0']})-({rect['x1']}, {rect['y1']}); {rect['width']} x {rect['height']}"


def bbox_to_dict(bbox: Any) -> dict[str, Any]:
    return {
        "x0": rounded(bbox.x0),
        "y0": rounded(bbox.y0),
        "x1": rounded(bbox.x1),
        "y1": rounded(bbox.y1),
        "width": rounded(bbox.width),
        "height": rounded(bbox.height),
        "shape_count": int(getattr(bbox, "shape_count", 0)),
    }


def rect_dict(rect: Rect) -> dict[str, float]:
    return {
        "x0": rounded(rect.x0),
        "y0": rounded(rect.y0),
        "x1": rounded(rect.x1),
        "y1": rounded(rect.y1),
        "width": rounded(rect.width),
        "height": rounded(rect.height),
        "area": rounded(rect.area),
    }


def contains_point(rect: Rect, x: float, y: float, eps: float = 1e-9) -> bool:
    return rect.x0 - eps <= x <= rect.x1 + eps and rect.y0 - eps <= y <= rect.y1 + eps


def intersect_rect(a: Rect, b: Rect) -> Rect | None:
    x0 = max(a.x0, b.x0)
    y0 = max(a.y0, b.y0)
    x1 = min(a.x1, b.x1)
    y1 = min(a.y1, b.y1)
    if x1 - x0 <= 1e-12 or y1 - y0 <= 1e-12:
        return None
    return Rect(x0, y0, x1, y1)


def overlap_pin_labels(overlap: Rect, a_pins: dict[str, Rect], b_pins: dict[str, Rect]) -> set[str]:
    labels: set[str] = set()
    for label, rect in list(a_pins.items()) + list(b_pins.items()):
        if overlap.overlaps(rect) or contains_point(overlap, rect.center.x, rect.center.y):
            labels.add(label)
    return labels


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(out)


def rounded(value: float) -> float:
    return round(float(value), 6)


def parse_gds_real8(data: bytes) -> float:
    if data == b"\0" * 8:
        return 0.0
    sign = -1.0 if data[0] & 0x80 else 1.0
    exponent = (data[0] & 0x7F) - 64
    mantissa = int.from_bytes(data[1:], "big") / float(1 << 56)
    return sign * mantissa * (16.0**exponent)


def resolve_input(value: str) -> Path:
    path = Path(value)
    if path.exists():
        return path
    return STANDALONE_ROOT / path


def resolve_output(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return STANDALONE_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
