from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.gds_util import inspect_gds_hierarchy, inspect_gds_layers, inspect_gds_text_records  # noqa: E402
from sram_layoutgen.openyield_adapter.gds_pin_audit import BBox, read_gds_labels_and_shapes  # noqa: E402


DEFAULT_SOURCE_GDS = Path("technology/freepdk45/gds_lib/openram_replacements/gen_col_mux.gds")
DEFAULT_POWER_REPORT = Path("docs/openyield_columnmux_power_metadata_report.json")
DEFAULT_LABEL = "vdd"
DEFAULT_LAYER = 11
DEFAULT_TEXTTYPE = 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a non-destructive repaired candidate GDS by adding a VDD label to gen_col_mux.")
    parser.add_argument("--tech-dir", required=True)
    parser.add_argument("--source-gds", default=str(DEFAULT_SOURCE_GDS))
    parser.add_argument("--power-report", default=str(DEFAULT_POWER_REPORT))
    parser.add_argument("--out-gds", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--label-name", default=DEFAULT_LABEL)
    parser.add_argument("--label-layer", type=int, default=DEFAULT_LAYER)
    parser.add_argument("--label-texttype", type=int, default=DEFAULT_TEXTTYPE)
    args = parser.parse_args()

    tech_dir = resolve_existing_path(args.tech_dir)
    source_gds = resolve_existing_path(args.source_gds)
    power_report_path = resolve_optional_path(args.power_report)
    out_gds = resolve_output(args.out_gds)
    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)

    power_report = json.loads(power_report_path.read_text(encoding="utf-8")) if power_report_path and power_report_path.exists() else None
    candidate = choose_candidate(power_report, source_gds)
    if candidate is None:
        candidate = fallback_candidate_from_gds(source_gds)

    repaired = write_repaired_candidate(
        source_gds=source_gds,
        out_gds=out_gds,
        label_name=args.label_name,
        label_layer=args.label_layer,
        label_texttype=args.label_texttype,
        x=float(candidate["center"]["x"]),
        y=float(candidate["center"]["y"]),
    )

    source_audit = audit_gds(source_gds)
    repaired_audit = audit_gds(out_gds)
    before_after = compare_audits(source_audit, repaired_audit)

    after_vdd = next((item for item in repaired_audit["labels"] if str(item["text"]).lower() == "vdd"), None)
    matched_shape = match_label_to_shape(after_vdd, repaired_audit["shapes"]) if after_vdd else None
    vdd_inside_candidate = bool(after_vdd and candidate["bbox"] and bbox_contains(candidate["bbox"], after_vdd["x"], after_vdd["y"], tol=0.02))

    power_before = str((power_report or {}).get("power_status", "unknown"))
    power_after = "vdd_label_present" if after_vdd and matched_shape else power_before
    safe_for_physical_mapping = True
    safe_for_shared_rail = False
    can_enter_columnmux_placement = "limited_or_metadata_only" if safe_for_physical_mapping and not safe_for_shared_rail else False
    recommended_integration = "add_repaired_macro_alias" if power_after == "vdd_label_present" else "proof_only"

    report: dict[str, Any] = {
        "scope": "step5_6_columnmux_vdd_pinproof_repair",
        "inputs": {
            "tech_dir": str(tech_dir.resolve()),
            "source_gds": str(source_gds.resolve()),
            "power_report": str(power_report_path.resolve()) if power_report_path else None,
            "label_name": args.label_name,
            "label_layer": args.label_layer,
            "label_texttype": args.label_texttype,
        },
        "modified_original_gds": False,
        "source_gds_path": str(source_gds.resolve()),
        "repaired_candidate_gds_path": str(out_gds.resolve()),
        "selected_candidate_shape": candidate,
        "new_text_label": {
            "name": args.label_name,
            "layer": args.label_layer,
            "texttype": args.label_texttype,
            "x": repaired["label_x"],
            "y": repaired["label_y"],
        },
        "labels_before": source_audit["labels"],
        "labels_after": repaired_audit["labels"],
        "polygon_count_before": source_audit["polygon_count"],
        "polygon_count_after": repaired_audit["polygon_count"],
        "text_count_before": source_audit["text_count"],
        "text_count_after": repaired_audit["text_count"],
        "bbox_before": source_audit["bbox"],
        "bbox_after": repaired_audit["bbox"],
        "vdd_label_present_before": source_audit["vdd_label_present"],
        "vdd_label_present_after": repaired_audit["vdd_label_present"],
        "vdd_shape_candidate_present_before": bool((power_report or {}).get("vdd_shape_candidate_present", False)),
        "vdd_shape_candidate_present_after": bool((power_report or {}).get("vdd_shape_candidate_present", False)),
        "vdd_label_matches_m1_shape": bool(after_vdd and matched_shape and after_vdd["layer"] == 11),
        "vdd_label_inside_candidate_shape": vdd_inside_candidate,
        "power_status_before": power_before,
        "power_status_after": power_after,
        "safe_for_physical_mapping": safe_for_physical_mapping,
        "safe_for_shared_rail": safe_for_shared_rail,
        "can_enter_columnmux_placement": can_enter_columnmux_placement,
        "requires_metadata_fix": power_after != "vdd_label_present",
        "recommended_integration": recommended_integration,
        "polygon_count_unchanged": source_audit["polygon_count"] == repaired_audit["polygon_count"],
        "labels_added_count": len(repaired_audit["labels"]) - len(source_audit["labels"]),
        "layout_hierarchy_before": source_audit["hierarchy"],
        "layout_hierarchy_after": repaired_audit["hierarchy"],
        "layer_summary_before": source_audit["layers"],
        "layer_summary_after": repaired_audit["layers"],
        "notes": [
            "The repair only appends one TEXT element; no polygon coordinates are changed.",
            "The candidate is proof-only and does not modify the original replacement GDS or replacement_macros.json.",
            "Shared rail still remains unproven; this repair only upgrades pin metadata from unlabeled shape to label-backed pin.",
        ],
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(report), encoding="utf-8")
    print(
        "before={before} after={after} labels_added={added} polygon_unchanged={same} recommended={rec}".format(
            before=report["power_status_before"],
            after=report["power_status_after"],
            added=report["labels_added_count"],
            same=report["polygon_count_unchanged"],
            rec=report["recommended_integration"],
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


def resolve_optional_path(path_text: str) -> Path | None:
    raw = Path(path_text)
    candidates = [raw, REPO_ROOT / raw]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def resolve_output(path_text: str) -> Path:
    raw = Path(path_text)
    if raw.is_absolute():
        return raw
    return REPO_ROOT / raw


def choose_candidate(power_report: dict[str, Any] | None, source_gds: Path) -> dict[str, Any] | None:
    if power_report:
        candidates = list(power_report.get("replacement_gds_audit", {}).get("suspected_vdd_shapes", []))
        if candidates:
            candidate = max(
                candidates,
                key=lambda item: (
                    float(item.get("bbox", {}).get("x1", 0.0)) - float(item.get("bbox", {}).get("x0", 0.0)),
                    float(item.get("bbox", {}).get("y1", 0.0)) - float(item.get("bbox", {}).get("y0", 0.0)),
                ),
            )
            bbox = candidate.get("bbox", {})
            return {
                "source": "power_report_suspected_shape",
                "bbox": bbox,
                "center": {
                    "x": round((float(bbox.get("x0", 0.0)) + float(bbox.get("x1", 0.0))) / 2.0, 6),
                    "y": round((float(bbox.get("y0", 0.0)) + float(bbox.get("y1", 0.0))) / 2.0, 6),
                },
                "reason": candidate.get("reason", "unknown"),
            }
    return None


def fallback_candidate_from_gds(source_gds: Path) -> dict[str, Any]:
    labels, shapes, bbox = read_gds_labels_and_shapes(source_gds)
    unlabeled = []
    for shape in shapes:
        if shape.layer != 11:
            continue
        if shape.bbox.y1 < (bbox.y1 if bbox else 0.0) - 0.05 and shape.bbox.width >= 0.2:
            unlabeled.append(shape)
    if not unlabeled:
        raise ValueError("Could not identify a fallback VDD candidate shape")
    shape = max(unlabeled, key=lambda item: item.bbox.width)
    return {
        "source": "fallback_unlabeled_m1_shape",
        "bbox": shape.bbox.to_dict(),
        "center": {"x": round(shape.bbox.center.x, 6), "y": round(shape.bbox.center.y, 6)},
        "reason": "largest_unlabeled_m1_shape_near_top_boundary",
    }


def write_repaired_candidate(
    *,
    source_gds: Path,
    out_gds: Path,
    label_name: str,
    label_layer: int,
    label_texttype: int,
    x: float,
    y: float,
) -> dict[str, Any]:
    data = source_gds.read_bytes()
    db_units_per_micron = read_db_units_per_micron(data)
    text_bytes = make_text_record(label_layer, label_texttype, label_name, x, y, db_units_per_micron)
    spans = find_structure_spans(data)
    if not spans:
        raise ValueError("No GDS structure found in source file")
    target = max(spans, key=lambda item: item["end"] - item["start"])
    insertion = target["end"] - 4  # before ENDSTR
    repaired = data[:insertion] + text_bytes + data[insertion:]
    out_gds.parent.mkdir(parents=True, exist_ok=True)
    out_gds.write_bytes(repaired)
    return {
        "label_x": x,
        "label_y": y,
        "db_units_per_micron": db_units_per_micron,
        "target_structure": target,
    }


def read_db_units_per_micron(data: bytes) -> float:
    offset = 0
    while offset + 4 <= len(data):
        size, record_type, data_type = struct.unpack(">HBB", data[offset : offset + 4])
        if size < 4 or offset + size > len(data):
            break
        payload = data[offset + 4 : offset + size]
        if record_type == 0x03 and data_type == 0x05 and len(payload) >= 16:
            db_unit_meters = gds_real8(payload[8:16])
            if db_unit_meters > 0:
                return 1.0 / (db_unit_meters * 1e6)
        offset += size
    return 2000.0


def find_structure_spans(data: bytes) -> list[dict[str, Any]]:
    offset = 0
    spans: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    while offset + 4 <= len(data):
        size, record_type, _data_type = struct.unpack(">HBB", data[offset : offset + 4])
        if size < 4 or offset + size > len(data):
            break
        payload = data[offset + 4 : offset + size]
        if record_type == 0x05:
            current = {"start": offset, "name": None}
        elif record_type == 0x06 and current is not None and current.get("name") is None:
            current["name"] = payload.rstrip(b"\0").decode("ascii", errors="ignore")
        elif record_type == 0x07 and current is not None:
            current["end"] = offset + size
            spans.append(current)
            current = None
        offset += size
    return [item for item in spans if item.get("name")]


def make_text_record(layer: int, texttype: int, text: str, x: float, y: float, db_units_per_micron: float) -> bytes:
    data = bytearray()
    data += record(0x0C, 0x00, b"")
    data += int2_record(0x0D, [layer])
    data += int2_record(0x16, [texttype])
    data += xy_record([(x, y)], db_units_per_micron)
    data += str_record(0x19, text)
    data += record(0x11, 0x00, b"")
    return bytes(data)


def record(record_type: int, data_type: int, payload: bytes) -> bytes:
    return struct.pack(">HBB", len(payload) + 4, record_type, data_type) + payload


def int2_record(record_type: int, values: list[int]) -> bytes:
    payload = b"".join(struct.pack(">h", value) for value in values)
    return record(record_type, 0x02, payload)


def str_record(record_type: int, value: str) -> bytes:
    payload = value.encode("ascii", errors="ignore")
    if len(payload) % 2:
        payload += b"\0"
    return record(record_type, 0x06, payload)


def xy_record(points: list[tuple[float, float]], db_units_per_micron: float) -> bytes:
    ints = []
    for x, y in points:
        ints.append(round(x * db_units_per_micron))
        ints.append(round(y * db_units_per_micron))
    payload = b"".join(struct.pack(">i", value) for value in ints)
    return record(0x10, 0x03, payload)


def gds_real8(data: bytes) -> float:
    if data == b"\0" * 8:
        return 0.0
    sign = -1.0 if data[0] & 0x80 else 1.0
    exponent = (data[0] & 0x7F) - 64
    mantissa = int.from_bytes(data[1:], "big") / float(1 << 56)
    return sign * mantissa * (16.0**exponent)


def audit_gds(path: Path) -> dict[str, Any]:
    labels, shapes, bbox = read_gds_labels_and_shapes(path)
    hierarchy = inspect_gds_hierarchy(path)
    layers = inspect_gds_layers(path)
    return {
        "path": str(path.resolve()),
        "bbox": bbox.to_dict() if bbox else None,
        "labels": [label.to_dict() for label in labels],
        "shapes": [shape.to_dict() for shape in shapes],
        "polygon_count": len(shapes),
        "text_count": hierarchy.get("text_count", 0),
        "vdd_label_present": any(label.text.lower() == "vdd" for label in labels),
        "gnd_label_present": any(label.text.lower() == "gnd" for label in labels),
        "hierarchy": hierarchy,
        "layers": layers,
    }


def compare_audits(before: dict[str, Any], after: dict[str, Any]) -> dict[str, Any]:
    return {
        "polygon_count_delta": after["polygon_count"] - before["polygon_count"],
        "text_count_delta": after["text_count"] - before["text_count"],
        "label_count_delta": len(after["labels"]) - len(before["labels"]),
    }


def match_label_to_shape(label: dict[str, Any], shapes: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not label:
        return None
    x = float(label["x"])
    y = float(label["y"])
    for shape in shapes:
        bbox = shape["bbox"]
        if bbox_contains(bbox, x, y, tol=0.02):
            return shape
    return None


def bbox_contains(bbox: dict[str, Any], x: float, y: float, tol: float = 0.0) -> bool:
    return (
        float(bbox["x0"]) - tol <= x <= float(bbox["x1"]) + tol
        and float(bbox["y0"]) - tol <= y <= float(bbox["y1"]) + tol
    )


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield ColumnMux VDD Pin-Proof Report",
        "",
        "This Step 5.6 report is read-only. It generates a repaired candidate GDS by adding a single `vdd` TEXT label to the suspected top M1 rail and then re-audits the result.",
        "",
        "## Summary",
        "",
        f"- source GDS: `{report['source_gds_path']}`",
        f"- repaired candidate GDS: `{report['repaired_candidate_gds_path']}`",
        f"- modified original GDS: `{report['modified_original_gds']}`",
        f"- selected candidate source: `{report['selected_candidate_shape']['source']}`",
        f"- selected candidate bbox: `{report['selected_candidate_shape']['bbox']}`",
        f"- new text label: `{report['new_text_label']}`",
        f"- vdd_label_present_before: `{report['vdd_label_present_before']}`",
        f"- vdd_label_present_after: `{report['vdd_label_present_after']}`",
        f"- power_status before: `{report['power_status_before']}`",
        f"- power_status after: `{report['power_status_after']}`",
        f"- safe_for_physical_mapping: `{report['safe_for_physical_mapping']}`",
        f"- safe_for_shared_rail: `{report['safe_for_shared_rail']}`",
        f"- can_enter_columnmux_placement: `{report['can_enter_columnmux_placement']}`",
        f"- recommended_integration: `{report['recommended_integration']}`",
        "",
        "## Before / After",
        "",
        f"- polygon count before: `{report['polygon_count_before']}`",
        f"- polygon count after: `{report['polygon_count_after']}`",
        f"- polygon count unchanged: `{report['polygon_count_unchanged']}`",
        f"- text count before: `{report['text_count_before']}`",
        f"- text count after: `{report['text_count_after']}`",
        f"- labels added count: `{report['labels_added_count']}`",
        f"- vdd label matches M1 shape: `{report['vdd_label_matches_m1_shape']}`",
        f"- vdd label inside candidate shape: `{report['vdd_label_inside_candidate_shape']}`",
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
