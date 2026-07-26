from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.composite_child_geometry_cloner import clone_child_for_composition
from sram_layoutgen.openyield_adapter.composite_hierarchy_closure import verify_composite_hierarchy_closure
from sram_layoutgen.openyield_adapter.composite_pin_namespace_verifier import verify_composite_pin_namespace
from sram_layoutgen.openyield_adapter.grid_legal_geometry import snap_bbox, snap_coordinate
from sram_layoutgen.openyield_adapter.hierarchical_connectivity_verifier import verify_hierarchical_connectivity
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import (
    geometry_fingerprint,
    non_text_geometry_fingerprint,
    run_cell_drc,
)
from sram_layoutgen.tech import Tech


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@dataclass
class ChildSpec:
    instance_name: str
    logical_module: str
    physical_cell_name: str
    gds_path: Path
    pin_map_path: Path
    connectivity_path: Path | None = None


@dataclass
class PlacedChild:
    spec: ChildSpec
    clone_root_name: str
    renamed_root_name: str
    clone_gds_path: Path
    placement_origin: tuple[float, float]
    bbox: list[float]
    placed_pin_map: dict[str, list[dict[str, Any]]]
    orientation: str = "R0"


def bbox_from_gds(gds_path: Path, top_name: str) -> list[float]:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    bbox = top.bounding_box()
    assert bbox is not None
    return [round(float(bbox[0][0]), 6), round(float(bbox[0][1]), 6), round(float(bbox[1][0]), 6), round(float(bbox[1][1]), 6)]


def clone_children(child_specs: list[ChildSpec], out_dir: Path) -> tuple[gdstk.Library, list[PlacedChild], list[dict[str, Any]]]:
    lib: gdstk.Library | None = None
    placed: list[PlacedChild] = []
    clone_rows: list[dict[str, Any]] = []
    for spec in child_specs:
        clone_root = f"TEAMB_CLONE__{spec.instance_name}"
        clone_gds = out_dir / f"{clone_root}.gds"
        clone_row = clone_child_for_composition(
            source_gds=spec.gds_path,
            source_top_name=spec.physical_cell_name,
            clone_root_name=clone_root,
            output_gds=clone_gds,
        )
        clone_rows.append(clone_row)
        child_lib = gdstk.read_gds(clone_gds)
        if lib is None:
            lib = gdstk.Library(unit=child_lib.unit, precision=child_lib.precision)
        existing = {cell.name for cell in lib.cells}
        for cell in child_lib.cells:
            if cell.name not in existing:
                lib.add(cell)
                existing.add(cell.name)
        placed.append(
            PlacedChild(
                spec=spec,
                clone_root_name=clone_root,
                renamed_root_name=clone_row["renamed_root_name"],
                clone_gds_path=clone_gds,
                placement_origin=(0.0, 0.0),
                bbox=bbox_from_gds(clone_gds, clone_row["renamed_root_name"]),
                placed_pin_map={},
            )
        )
    assert lib is not None
    return lib, placed, clone_rows


def shift_pin_map(pin_map: dict[str, list[dict[str, Any]]], dx: float, dy: float) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for pin_name, entries in pin_map.items():
        out[pin_name] = []
        for entry in entries:
            out[pin_name].append(
                {
                    **entry,
                    "lx": round(float(entry["lx"]) + dx, 6),
                    "by": round(float(entry["by"]) + dy, 6),
                    "rx": round(float(entry["rx"]) + dx, 6),
                    "uy": round(float(entry["uy"]) + dy, 6),
                }
            )
    return out


def transform_pin_map(
    pin_map: dict[str, list[dict[str, Any]]],
    *,
    bbox: list[float],
    placement_x: float,
    placement_y: float,
    orientation: str,
) -> tuple[dict[str, list[dict[str, Any]]], tuple[float, float]]:
    if orientation not in {"R0", "MY", "MX", "R180"}:
        raise ValueError(f"unsupported orientation: {orientation}")
    x0, y0, x1, y1 = [float(value) for value in bbox]
    if orientation == "R0":
        origin_x = placement_x - x0
        origin_y = placement_y - y0
    elif orientation == "MY":
        origin_x = placement_x + x1
        origin_y = placement_y - y0
    elif orientation == "MX":
        origin_x = placement_x - x0
        origin_y = placement_y + y1
    else:
        origin_x = placement_x + x1
        origin_y = placement_y + y1
    out: dict[str, list[dict[str, Any]]] = {}
    for pin_name, entries in pin_map.items():
        out[pin_name] = []
        for entry in entries:
            ex0 = float(entry["lx"])
            ey0 = float(entry["by"])
            ex1 = float(entry["rx"])
            ey1 = float(entry["uy"])
            if orientation == "R0":
                tx0 = ex0 + origin_x
                tx1 = ex1 + origin_x
                ty0 = ey0 + origin_y
                ty1 = ey1 + origin_y
            elif orientation == "MY":
                tx0 = (-ex1) + origin_x
                tx1 = (-ex0) + origin_x
                ty0 = ey0 + origin_y
                ty1 = ey1 + origin_y
            elif orientation == "MX":
                tx0 = ex0 + origin_x
                tx1 = ex1 + origin_x
                ty0 = (-ey1) + origin_y
                ty1 = (-ey0) + origin_y
            else:
                tx0 = (-ex1) + origin_x
                tx1 = (-ex0) + origin_x
                ty0 = (-ey1) + origin_y
                ty1 = (-ey0) + origin_y
            out[pin_name].append(
                {
                    **entry,
                    "lx": round(min(tx0, tx1), 6),
                    "by": round(min(ty0, ty1), 6),
                    "rx": round(max(tx0, tx1), 6),
                    "uy": round(max(ty0, ty1), 6),
                }
            )
    return out, (round(origin_x, 6), round(origin_y, 6))


def place_children_single_row(placed_children: list[PlacedChild], *, start_x: float, start_y: float, gap: float) -> list[PlacedChild]:
    cursor = start_x
    updated = []
    for item in placed_children:
        bbox = item.bbox
        width = bbox[2] - bbox[0]
        dx = round(cursor - bbox[0], 6)
        dy = round(start_y - bbox[1], 6)
        updated.append(
            PlacedChild(
                spec=item.spec,
                clone_root_name=item.clone_root_name,
                renamed_root_name=item.renamed_root_name,
                clone_gds_path=item.clone_gds_path,
                placement_origin=(dx, dy),
                bbox=[round(bbox[0] + dx, 6), round(bbox[1] + dy, 6), round(bbox[2] + dx, 6), round(bbox[3] + dy, 6)],
                placed_pin_map=shift_pin_map(read_json(item.spec.pin_map_path), dx, dy),
            )
        )
        cursor = round(cursor + width + gap, 6)
    return updated


def instantiate_children(lib: gdstk.Library, top_name: str, placed_children: list[PlacedChild]) -> gdstk.Cell:
    top = lib.new_cell(top_name)
    for item in placed_children:
        kwargs: dict[str, Any] = {}
        if item.orientation == "MY":
            kwargs["rotation"] = 3.141592653589793
            kwargs["x_reflection"] = True
        elif item.orientation == "MX":
            kwargs["x_reflection"] = True
        elif item.orientation == "R180":
            kwargs["rotation"] = 3.141592653589793
        ref = gdstk.Reference(
            next(cell for cell in lib.cells if cell.name == item.renamed_root_name),
            origin=item.placement_origin,
            **kwargs,
        )
        top.add(ref)
    return top


def _m1_rect(top: gdstk.Cell, bbox: dict[str, float]) -> None:
    top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=11, datatype=0))


def _m2_rect(top: gdstk.Cell, bbox: dict[str, float]) -> None:
    top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=13, datatype=0))


def _via1_rect(top: gdstk.Cell, bbox: dict[str, float]) -> None:
    top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=12, datatype=0))


def _center(bbox: dict[str, float]) -> tuple[float, float]:
    return (round((bbox["lx"] + bbox["rx"]) * 0.5, 6), round((bbox["by"] + bbox["uy"]) * 0.5, 6))


def add_horizontal_pin_route(top: gdstk.Cell, left_bbox: dict[str, float], right_bbox: dict[str, float], *, tech: Tech, track_y: float | None = None) -> list[dict[str, Any]]:
    grid = tech.manufacturing_grid
    m1_w = tech.layer("m1").min_width
    m2_w = tech.layer("m2").min_width
    via = tech.via_between("m1", "m2")
    assert via is not None
    # FreePDK45 deck requires via1 to be fully enclosed by metal1 and by metal2 on opposite sides.
    via_enc = 0.035
    landing_half_w_m1 = max(m1_w * 0.5, via.size * 0.5 + via_enc)
    landing_half_w_m2 = max(m2_w * 0.5, via.size * 0.5 + via_enc)
    left_cx, left_cy = _center(left_bbox)
    right_cx, right_cy = _center(right_bbox)
    if track_y is None:
        track_y = max(left_bbox["uy"], right_bbox["uy"]) + 0.18
    track_y = snap_coordinate(track_y, grid)
    route_objects = []
    for cx, cy, endpoint_name in [(left_cx, left_cy, "left"), (right_cx, right_cy, "right")]:
        m1_landing = snap_bbox(
            {
                "lx": cx - landing_half_w_m1,
                "by": min(cy, track_y - via.size * 0.5),
                "rx": cx + landing_half_w_m1,
                "uy": max(cy, track_y + via.size * 0.5),
            },
            grid,
        )
        _m1_rect(top, m1_landing)
        m2_landing = snap_bbox({"lx": cx - landing_half_w_m2, "by": track_y - landing_half_w_m2, "rx": cx + landing_half_w_m2, "uy": track_y + landing_half_w_m2}, grid)
        _m2_rect(top, m2_landing)
        via_bbox = snap_bbox({"lx": cx - via.size * 0.5, "by": track_y - via.size * 0.5, "rx": cx + via.size * 0.5, "uy": track_y + via.size * 0.5}, grid)
        _via1_rect(top, via_bbox)
        route_objects.append({"endpoint": endpoint_name, "m1_landing_bbox": m1_landing, "m2_landing_bbox": m2_landing, "via_bbox": via_bbox})
    trunk = snap_bbox({"lx": min(left_cx, right_cx), "by": track_y - landing_half_w_m2, "rx": max(left_cx, right_cx), "uy": track_y + landing_half_w_m2}, grid)
    _m2_rect(top, trunk)
    route_objects.append({"endpoint": "trunk", "m2_trunk_bbox": trunk})
    return route_objects


def bridge_power_rails(top: gdstk.Cell, placed_children: list[PlacedChild], tech: Tech) -> dict[str, dict[str, float]]:
    grid = tech.manufacturing_grid
    vdd_boxes = []
    vss_boxes = []
    for item in placed_children:
        vdd_boxes.extend(item.placed_pin_map["VDD"])
        vss_boxes.extend(item.placed_pin_map["VSS"])
    lx = min(box["lx"] for box in vdd_boxes + vss_boxes)
    rx = max(box["rx"] for box in vdd_boxes + vss_boxes)
    vdd = snap_bbox({"lx": lx, "by": vdd_boxes[0]["by"], "rx": rx, "uy": vdd_boxes[0]["uy"]}, grid)
    vss = snap_bbox({"lx": lx, "by": vss_boxes[0]["by"], "rx": rx, "uy": vss_boxes[0]["uy"]}, grid)
    _m1_rect(top, vdd)
    _m1_rect(top, vss)
    return {"VDD": vdd, "VSS": vss}


def add_top_label(top: gdstk.Cell, text: str, bbox: dict[str, float]) -> None:
    x, y = _center(bbox)
    top.add(gdstk.Label(text, (x, y), layer=11, texttype=2))


def write_gds(lib: gdstk.Library, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lib.write_gds(path, timestamp=datetime(2000, 1, 1, 0, 0, 0))


def make_review_atlas(clean_gds: Path, annotated_gds: Path, top_name: str, output_gds: Path) -> dict[str, Any]:
    atlas = gdstk.Library()
    clean_lib = gdstk.read_gds(clean_gds)
    anno_lib = gdstk.read_gds(annotated_gds)
    for cell in clean_lib.cells:
        if cell.name not in {c.name for c in atlas.cells}:
            atlas.add(cell)
    for cell in anno_lib.cells:
        if cell.name not in {c.name for c in atlas.cells}:
            atlas.add(cell)
    top = atlas.new_cell(f"{top_name}_REVIEW_ATLAS")
    clean_cell = next(cell for cell in atlas.cells if cell.name == top_name)
    anno_cell = next(cell for cell in atlas.cells if cell.name == f"{top_name}_ANNOTATED")
    bbox = clean_cell.bounding_box()
    assert bbox is not None
    width = float(bbox[1][0] - bbox[0][0])
    top.add(gdstk.Reference(clean_cell, origin=(0, 0)))
    top.add(gdstk.Reference(anno_cell, origin=(width + 1.0, 0)))
    top.add(gdstk.Label("CLEAN", (0.2, float(bbox[1][1]) + 0.2), layer=239, texttype=0))
    top.add(gdstk.Label("ANNOTATED", (width + 1.2, float(bbox[1][1]) + 0.2), layer=239, texttype=0))
    output_gds.parent.mkdir(parents=True, exist_ok=True)
    atlas.write_gds(output_gds, timestamp=datetime(2000, 1, 1, 0, 0, 0))
    return {"atlas_top_cell": top.name, "panel_count": 2}


def annotate_from_bboxes(clean_gds: Path, top_name: str, bboxes: list[dict[str, Any]], output_gds: Path) -> None:
    lib = gdstk.read_gds(clean_gds)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    top.name = f"{top_name}_ANNOTATED"
    for row in bboxes:
        bbox = row["bbox"]
        top.add(gdstk.rectangle((bbox[0], bbox[1]), (bbox[2], bbox[3]), layer=238, datatype=0))
        top.add(gdstk.Label(row["label"], ((bbox[0] + bbox[2]) * 0.5, bbox[3] + 0.08), layer=239, texttype=0))
    output_gds.parent.mkdir(parents=True, exist_ok=True)
    lib.write_gds(output_gds, timestamp=datetime(2000, 1, 1, 0, 0, 0))


def simple_composite_verification(
    *,
    clean_gds: Path,
    top_name: str,
    canonical_labels: list[str],
    endpoints_by_net: dict[str, list[dict[str, Any]]],
    top_pin_bboxes: dict[str, dict[str, float]],
    klayout_path: Path,
    drc_deck: Path,
    drc_dir: Path,
) -> dict[str, Any]:
    namespace = verify_composite_pin_namespace(clean_gds, top_name, canonical_labels)
    hierarchy = verify_composite_hierarchy_closure(clean_gds, top_name)
    connectivity = verify_hierarchical_connectivity(gds_path=clean_gds, top_name=top_name, endpoints_by_net=endpoints_by_net, top_pin_bboxes=top_pin_bboxes)
    drc_dir.mkdir(parents=True, exist_ok=True)
    drc = run_cell_drc(klayout_path, drc_deck, clean_gds, top_name, drc_dir)
    return {
        "namespace": namespace,
        "hierarchy": hierarchy,
        "connectivity": connectivity,
        "drc": drc,
        "geometry_fingerprint": geometry_fingerprint(clean_gds, top_name),
        "non_text_geometry_fingerprint": non_text_geometry_fingerprint(clean_gds, top_name),
    }
