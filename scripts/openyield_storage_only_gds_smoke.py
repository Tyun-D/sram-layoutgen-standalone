from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))

from sram_layoutgen.gds_util import inspect_gds_hierarchy, measure_gds_bbox  # noqa: E402
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
    args = parser.parse_args()

    if args.rows <= 0 or args.cols <= 0:
        raise ValueError("rows and cols must be positive")

    tech = load_bundled_freepdk45()
    layout = build_storage_only_layout(args.rows, args.cols, tech)
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


def build_storage_only_layout(rows: int, cols: int, tech: Any) -> LayoutDB:
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
    db.metadata.update(
        {
            "rows": rows,
            "cols": cols,
            "pitch_x": PITCH_X,
            "pitch_y": PITCH_Y,
            "orientation": "R0",
            "allowed_macros": sorted(ALLOWED_MACROS),
            "shared_rail_merge": False,
            "routing_changed": False,
            "main_gds_flow_changed": False,
            "smoke_gds_not_final_signoff": True,
        }
    )
    return db


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
            f"- SVG: `{report['svg_output']['path']}`",
            f"- layout bbox: `{bbox_text(report['layout_bbox'])}`",
            f"- only allowed macros: `{report['only_allowed_macros']}`",
            f"- contains peripheral macro: `{report['contains_peripheral_macro']}`",
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
