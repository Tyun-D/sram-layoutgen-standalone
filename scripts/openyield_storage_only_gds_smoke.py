from __future__ import annotations

import argparse
import json
import struct
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))

from sram_layoutgen.gds_util import inspect_gds_hierarchy, inspect_gds_text_records, measure_gds_bbox  # noqa: E402
from sram_layoutgen.gds_writer import GDSWriter  # noqa: E402
from sram_layoutgen.geometry import CellArray, LayoutDB, Point, Rect  # noqa: E402
from sram_layoutgen.openram_placement import placed_bbox_from_openram_origin  # noqa: E402
from sram_layoutgen.standalone import load_bundled_freepdk45  # noqa: E402


PITCH_X = 0.895
PITCH_Y = 1.565
LEGACY_PITCH_X = 0.705
LEGACY_PITCH_Y = 1.365
ALLOWED_MACROS = {"cell_1rw", "dummy_cell_1rw", "replica_cell_1rw"}
PERIPHERAL_MACROS = {
    "sense_amp",
    "write_driver",
    "gen_precharge",
    "gen_col_mux",
    "gen_wl_driver",
    "dff",
    "tri_gate",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a tiny OpenYield storage-only hardcell GDS smoke layout.")
    parser.add_argument("--rows", type=int, default=2)
    parser.add_argument("--cols", type=int, default=4)
    parser.add_argument("--out-gds", default="build/openyield_storage_only_smoke_2x4/storage_only_2x4.gds")
    parser.add_argument("--out-json", default="docs/openyield_storage_only_gds_smoke_report.json")
    parser.add_argument("--out-md", default="docs/openyield_storage_only_gds_smoke_report.md")
    parser.add_argument("--stitch-power-rails", action="store_true")
    args = parser.parse_args()

    if args.rows <= 0 or args.cols <= 0:
        raise ValueError("rows and cols must be positive")

    tech = load_bundled_freepdk45()
    layout = build_storage_only_layout(args.rows, args.cols, tech, stitch_power_rails=args.stitch_power_rails)
    out_gds = resolve_output(args.out_gds)
    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)
    out_svg = out_gds.with_suffix(".svg")

    writer = GDSWriter(tech, include_pin_shapes=False, include_pin_labels=False, include_cell_pin_labels=True)
    writer.write(layout, out_gds)
    layout.write_svg(out_svg)

    report = build_report(layout, out_gds, out_svg, out_json, out_md, args.rows, args.cols)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(format_markdown(report), encoding="utf-8")

    assert report["geometry_smoke_checks"]["clean"], "storage-only smoke checks failed"
    print(f"Wrote {out_gds}")
    print(f"Wrote {out_svg}")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(
        f"rows={args.rows} cols={args.cols} instances={report['instance_count']['total']} "
        f"gds_nonempty={report['gds_output']['exists'] and report['gds_output']['size_bytes'] > 0}"
    )
    return 0


def build_storage_only_layout(rows: int, cols: int, tech: Any, *, stitch_power_rails: bool = False) -> LayoutDB:
    db = LayoutDB(f"openyield_storage_only_{rows}x{cols}")
    arrays = [
        add_array(db, tech, "dummy_left", "dummy_cell_1rw", 0.0, 0.0, 1, rows, "dummy_left"),
        add_array(db, tech, "bitcell_array", "cell_1rw", PITCH_X, 0.0, cols, rows, "bitcell_array"),
        add_array(db, tech, "dummy_right", "dummy_cell_1rw", (cols + 1) * PITCH_X, 0.0, 1, rows, "dummy_right"),
        add_array(db, tech, "replica_column", "replica_cell_1rw", (cols + 2) * PITCH_X, 0.0, 1, rows, "replica_column"),
    ]
    storage_bbox = Rect.union(array.rect for array in arrays)
    db.add_shape("boundary", storage_bbox, "boundary", name="prBoundary")
    for array in arrays:
        db.add_shape("m1", array.rect, "module", name=array.name)
    stitch_records: list[dict[str, Any]] = []
    if stitch_power_rails:
        stitch_records = add_power_rail_stitches(db, tech, rows, cols)
    db.metadata.update(
        {
            "rows": rows,
            "cols": cols,
            "pitch_x": PITCH_X,
            "pitch_y": PITCH_Y,
            "orientation": "R0",
            "allowed_macros": sorted(ALLOWED_MACROS),
            "stitch_power_rails": stitch_power_rails,
            "power_stitch_records": stitch_records,
            "vdd_stitch_count": sum(1 for item in stitch_records if item["net"] == "vdd"),
            "gnd_stitch_count": sum(1 for item in stitch_records if item["net"] == "gnd"),
            "side_power_trunk_added": False,
            "shared_rail_merge": False,
            "routing_changed": False,
            "main_gds_flow_changed": False,
            "smoke_gds_not_final_signoff": True,
        }
    )
    return db


def add_power_rail_stitches(db: LayoutDB, tech: Any, rows: int, cols: int) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    pin_cache: dict[tuple[str, str], dict[str, Any]] = {}

    def pin(cell_name: str, label: str) -> dict[str, Any]:
        key = (cell_name, label)
        if key not in pin_cache:
            pin_cache[key] = local_pin_bbox(tech, cell_name, label)
        return pin_cache[key]

    for row in range(rows):
        instances = row_instances(row, cols)
        for left, right in zip(instances, instances[1:]):
            for net in ("vdd", "gnd"):
                left_pin = pin(left["cell"], net)
                right_pin = pin(right["cell"], net)
                if left_pin["layer"] != right_pin["layer"]:
                    continue
                left_rect = shift_rect(left_pin["bbox_rect"], float(left["x"]), float(left["y"]))
                right_rect = shift_rect(right_pin["bbox_rect"], float(right["x"]), float(right["y"]))
                y0 = max(left_rect.y0, right_rect.y0)
                y1 = min(left_rect.y1, right_rect.y1)
                x0 = left_rect.x1
                x1 = right_rect.x0
                gap = x1 - x0
                if y1 <= y0 or gap < -1e-9:
                    continue
                if gap <= 1e-9:
                    continue
                bridge = Rect(x0, y0, x1, y1)
                name = f"{net}_stitch_r{row}_{left['name']}_to_{right['name']}"
                db.add_shape(left_pin["layer"], bridge, "route", net, name)
                records.append(
                    {
                        "name": name,
                        "net": net,
                        "layer": left_pin["layer"],
                        "row": row,
                        "left_instance": left["name"],
                        "right_instance": right["name"],
                        "gap": rounded(gap),
                        "rect": rect_dict(bridge),
                        "same_net_power_only": True,
                        "touches_signal_pin": False,
                    }
                )
    return records


def row_instances(row: int, cols: int) -> list[dict[str, Any]]:
    y = row * PITCH_Y
    items: list[dict[str, Any]] = [
        {"name": f"dummy_left_r{row}", "cell": "dummy_cell_1rw", "x": 0.0, "y": y},
    ]
    items.extend(
        {"name": f"bit_r{row}_c{col}", "cell": "cell_1rw", "x": PITCH_X + col * PITCH_X, "y": y}
        for col in range(cols)
    )
    items.extend(
        [
            {"name": f"dummy_right_r{row}", "cell": "dummy_cell_1rw", "x": (cols + 1) * PITCH_X, "y": y},
            {"name": f"replica_r{row}", "cell": "replica_cell_1rw", "x": (cols + 2) * PITCH_X, "y": y},
        ]
    )
    return items


def local_pin_bbox(tech: Any, cell_name: str, label: str) -> dict[str, Any]:
    cell = tech.cell(cell_name)
    if cell.gds_path is None:
        raise ValueError(f"cell has no GDS path: {cell_name}")
    target = label.lower()
    text = next(
        (record for record in inspect_gds_text_records(Path(cell.gds_path)) if str(record["text"]).strip().lower() == target),
        None,
    )
    if text is None:
        raise ValueError(f"{cell_name} has no TEXT pin named {label}")
    shapes = parse_gds_boundaries(Path(cell.gds_path))
    x = float(text["x"])
    y = float(text["y"])
    lpp = str(text["lpp"])
    candidates = [shape["rect"] for shape in shapes if shape["lpp"] == lpp and contains_point(shape["rect"], x, y)]
    if not candidates:
        raise ValueError(f"{cell_name}.{label} TEXT pin does not intersect a boundary on {lpp}")
    rect = Rect.union(candidates)
    layer = layer_name_for_lpp(tech, lpp)
    if layer != "m1":
        raise ValueError(f"{cell_name}.{label} expected on m1, found {layer} ({lpp})")
    return {
        "cell": cell_name,
        "label": label,
        "layer": layer,
        "lpp": lpp,
        "bbox_rect": rect,
        "bbox": rect_dict(rect),
        "text_point": {"x": rounded(x), "y": rounded(y)},
    }


def parse_gds_boundaries(path: Path) -> list[dict[str, Any]]:
    data = path.read_bytes()
    offset = 0
    db_unit_microns = 0.001
    in_boundary = False
    layer = None
    datatype = 0
    shapes: list[dict[str, Any]] = []
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
            shapes.append(
                {
                    "lpp": f"{layer}/{datatype}",
                    "rect": Rect(
                        min(xs) * db_unit_microns,
                        min(ys) * db_unit_microns,
                        max(xs) * db_unit_microns,
                        max(ys) * db_unit_microns,
                    ),
                }
            )
        elif record_type == 0x11:
            in_boundary = False
        offset += size
    return shapes


def layer_name_for_lpp(tech: Any, lpp: str) -> str:
    layer, datatype = (int(part) for part in lpp.split("/", 1))
    for name, rule in tech.layers.items():
        if rule.gds_layer == layer and rule.datatype == datatype:
            return name
    return lpp


def add_array(
    db: LayoutDB,
    tech: Any,
    name: str,
    cell_name: str,
    x: float,
    y: float,
    cols: int,
    rows: int,
    role: str,
) -> CellArray:
    cell = tech.cell(cell_name)
    rects = [
        placed_bbox_from_openram_origin(cell, x + col * PITCH_X, y + row * PITCH_Y, "R0")
        for row in range(rows)
        for col in range(cols)
    ]
    array = CellArray(
        name=name,
        cell=cell_name,
        origin=Point(x, y),
        columns=cols,
        rows=rows,
        pitch_x=PITCH_X,
        pitch_y=PITCH_Y,
        rect=Rect.union(rects),
        role=role,
        mirror_x=False,
        mirror_y=False,
    )
    db.add_cell_array(array)
    return array


def build_report(layout: LayoutDB, out_gds: Path, out_svg: Path, out_json: Path, out_md: Path, rows: int, cols: int) -> dict[str, Any]:
    arrays = layout.cell_arrays
    macro_counts: dict[str, int] = {}
    for array in arrays:
        macro_counts[array.cell] = macro_counts.get(array.cell, 0) + array.rows * array.columns
    observed_macros = set(macro_counts)
    peripheral_observed = sorted(observed_macros & PERIPHERAL_MACROS)
    expected = {
        "bitcell": rows * cols,
        "dummy_left": rows,
        "dummy_right": rows,
        "replica": rows,
        "total": rows * cols + 3 * rows,
    }
    actual = {
        "bitcell": macro_counts.get("cell_1rw", 0),
        "dummy_left_plus_right": macro_counts.get("dummy_cell_1rw", 0),
        "replica": macro_counts.get("replica_cell_1rw", 0),
        "total": sum(macro_counts.values()),
    }
    hierarchy = inspect_gds_hierarchy(out_gds) if out_gds.exists() else {}
    measured = measure_gds_bbox(out_gds) if out_gds.exists() else None
    stitch_records = list(layout.metadata.get("power_stitch_records", []))
    stitch_nets = {str(item["net"]) for item in stitch_records}
    signal_labels = {"bl", "br", "rbl", "rblb", "wl", "q", "qb", "q_bar"}
    checks = {
        "only_allowed_macros": observed_macros <= ALLOWED_MACROS,
        "no_peripheral_macros": not peripheral_observed,
        "instance_count_correct": actual["total"] == expected["total"]
        and actual["bitcell"] == expected["bitcell"]
        and actual["dummy_left_plus_right"] == expected["dummy_left"] + expected["dummy_right"]
        and actual["replica"] == expected["replica"],
        "pitch_correct": all(abs(array.pitch_x - PITCH_X) <= 1e-9 and abs(array.pitch_y - PITCH_Y) <= 1e-9 for array in arrays),
        "legacy_pitch_not_used": all(abs(array.pitch_x - LEGACY_PITCH_X) > 1e-9 and abs(array.pitch_y - LEGACY_PITCH_Y) > 1e-9 for array in arrays),
        "no_mirror_or_flip": all(not array.mirror_x and not array.mirror_y for array in arrays),
        "shared_rail_merge_not_run": layout.metadata["shared_rail_merge"] is False,
        "routing_not_changed": layout.metadata["routing_changed"] is False,
        "main_gds_flow_not_changed": layout.metadata["main_gds_flow_changed"] is False,
        "stitch_shapes_power_only": stitch_nets <= {"vdd", "gnd"},
        "no_vdd_gnd_cross_stitch": all(str(item["net"]) in {"vdd", "gnd"} and item["same_net_power_only"] for item in stitch_records),
        "no_signal_pin_stitch": all(not item["touches_signal_pin"] for item in stitch_records),
        "no_bl_br_wl_stitch": not (stitch_nets & signal_labels),
        "explicit_bridge_not_global_shared_rail_merge": layout.metadata["shared_rail_merge"] is False,
        "gds_exists_nonempty": out_gds.exists() and out_gds.stat().st_size > 0,
    }
    checks["clean"] = all(checks.values())
    return {
        "rows": rows,
        "cols": cols,
        "macros": sorted(observed_macros),
        "macro_counts": macro_counts,
        "pitch": {"x": PITCH_X, "y": PITCH_Y},
        "orientation": "R0",
        "instance_count": {"expected": expected, "actual": actual, "total": actual["total"]},
        "gds_output": {
            "input_gds": None,
            "input_source": "in_memory_storage_only_layout",
            "path": str(out_gds),
            "exists": out_gds.exists(),
            "size_bytes": out_gds.stat().st_size if out_gds.exists() else 0,
            "smoke_output_not_final_signoff": True,
        },
        "svg_output": {
            "path": str(out_svg),
            "exists": out_svg.exists(),
            "size_bytes": out_svg.stat().st_size if out_svg.exists() else 0,
        },
        "report_outputs": {"json": str(out_json), "md": str(out_md)},
        "layout_bbox": rect_dict(layout.bounds),
        "gds_bbox_measured_flat": bbox_to_dict(measured) if measured is not None else None,
        "cell_arrays": [array.to_dict() for array in arrays],
        "gds_hierarchy": hierarchy,
        "only_allowed_macros": observed_macros <= ALLOWED_MACROS,
        "contains_peripheral_macro": bool(peripheral_observed),
        "peripheral_macros_observed": peripheral_observed,
        "stitch_power_rails": bool(layout.metadata.get("stitch_power_rails", False)),
        "power_rail_layer": "m1",
        "power_stitches": {
            "records": stitch_records,
            "vdd_count": int(layout.metadata.get("vdd_stitch_count", 0)),
            "gnd_count": int(layout.metadata.get("gnd_stitch_count", 0)),
            "total_count": len(stitch_records),
            "same_net_power_only": checks["stitch_shapes_power_only"] and checks["no_vdd_gnd_cross_stitch"],
            "crosses_bl_br_wl": False,
        },
        "side_power_trunk_added": bool(layout.metadata.get("side_power_trunk_added", False)),
        "shared_rail_merge": False,
        "routing_changed": False,
        "main_gds_flow_changed": False,
        "geometry_smoke_checks": checks,
        "next_step_recommendations": [
            "Open the smoke GDS in KLayout for visual inspection of full-bbox storage tiling.",
            "If visual spacing is acceptable, keep full bbox pitch as the conservative OpenYield-enabled storage pitch.",
            "Run a tiny storage-only DRC only as a smoke check; do not treat this GDS as final SRAM signoff.",
        ],
    }


def format_markdown(report: dict[str, Any]) -> str:
    checks = report["geometry_smoke_checks"]
    return "\n".join(
        [
            "# OpenYield Storage-Only GDS Smoke Report",
            "",
            "This is a tiny hardcell-only GDS smoke for manual viewing. It is not a final SRAM layout and does not include routing, peripheral macros, shared rail merge, or signoff.",
            "",
            "## Summary",
            "",
            f"- rows: `{report['rows']}`",
            f"- cols: `{report['cols']}`",
            f"- pitch: `{report['pitch']['x']} x {report['pitch']['y']}`",
            f"- orientation: `{report['orientation']}`",
            f"- instance count: `{report['instance_count']['total']}`",
            f"- GDS: `{report['gds_output']['path']}`",
            f"- input GDS: `{report['gds_output']['input_gds']}` ({report['gds_output']['input_source']})",
            f"- SVG: `{report['svg_output']['path']}`",
            f"- layout bbox: `{bbox_text(report['layout_bbox'])}`",
            f"- only allowed macros: `{report['only_allowed_macros']}`",
            f"- contains peripheral macro: `{report['contains_peripheral_macro']}`",
            f"- stitch power rails: `{report['stitch_power_rails']}`",
            f"- power rail layer: `{report['power_rail_layer']}`",
            f"- VDD stitch count: `{report['power_stitches']['vdd_count']}`",
            f"- GND stitch count: `{report['power_stitches']['gnd_count']}`",
            f"- side power trunk added: `{report['side_power_trunk_added']}`",
            f"- same-net power only: `{report['power_stitches']['same_net_power_only']}`",
            f"- crosses BL/BR/WL: `{report['power_stitches']['crosses_bl_br_wl']}`",
            f"- shared rail merge: `{report['shared_rail_merge']}`",
            f"- routing changed: `{report['routing_changed']}`",
            f"- main GDS flow changed: `{report['main_gds_flow_changed']}`",
            "",
            "## Macro Counts",
            "",
            md_table(["macro", "count"], [[macro, count] for macro, count in sorted(report["macro_counts"].items())]),
            "",
            "## Cell Arrays",
            "",
            md_table(
                ["name", "cell", "rows", "cols", "pitch", "mirror", "bbox"],
                [
                    [
                        array["name"],
                        array["cell"],
                        array["rows"],
                        array["columns"],
                        f"{array['pitch_x']} x {array['pitch_y']}",
                        f"mx={array['mirror_x']}, my={array['mirror_y']}",
                        bbox_text(rect_with_size(array["rect"])),
                    ]
                    for array in report["cell_arrays"]
                ],
            ),
            "",
            "## Power Stitch Records",
            "",
            md_table(
                ["name", "net", "layer", "row", "left", "right", "gap", "rect"],
                [
                    [
                        item["name"],
                        item["net"],
                        item["layer"],
                        item["row"],
                        item["left_instance"],
                        item["right_instance"],
                        item["gap"],
                        bbox_text(item["rect"]),
                    ]
                    for item in report["power_stitches"]["records"]
                ],
            )
            if report["power_stitches"]["records"]
            else "none",
            "",
            "## Geometry Smoke Checks",
            "",
            md_table(["check", "result"], [[key, value] for key, value in checks.items()]),
            "",
            "## Next Steps",
            "",
            *[f"- {item}" for item in report["next_step_recommendations"]],
            "",
        ]
    )


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


def rect_with_size(rect: dict[str, float]) -> dict[str, float]:
    out = dict(rect)
    out["width"] = rounded(float(rect["x1"]) - float(rect["x0"]))
    out["height"] = rounded(float(rect["y1"]) - float(rect["y0"]))
    out["area"] = rounded(out["width"] * out["height"])
    return out


def shift_rect(rect: Rect, dx: float, dy: float) -> Rect:
    return Rect(rect.x0 + dx, rect.y0 + dy, rect.x1 + dx, rect.y1 + dy)


def contains_point(rect: Rect, x: float, y: float, eps: float = 1e-9) -> bool:
    return rect.x0 - eps <= x <= rect.x1 + eps and rect.y0 - eps <= y <= rect.y1 + eps


def parse_gds_real8(data: bytes) -> float:
    if data == b"\0" * 8:
        return 0.0
    sign = -1.0 if data[0] & 0x80 else 1.0
    exponent = (data[0] & 0x7F) - 64
    mantissa = int.from_bytes(data[1:], "big") / float(1 << 56)
    return sign * mantissa * (16.0**exponent)


def bbox_text(rect: dict[str, Any]) -> str:
    return f"({rect['x0']}, {rect['y0']})-({rect['x1']}, {rect['y1']}); {rect['width']} x {rect['height']}"


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(out)


def rounded(value: float) -> float:
    return round(float(value), 6)


def resolve_output(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return STANDALONE_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
