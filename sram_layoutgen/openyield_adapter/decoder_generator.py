from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.teamb_composite_helper import (
    ChildSpec,
    PlacedChild,
    add_top_label,
    annotate_from_bboxes,
    bbox_from_gds,
    bridge_power_rails,
    clone_children,
    instantiate_children,
    make_review_atlas,
    read_json,
    transform_pin_map,
    write_csv,
    write_gds,
    write_json,
)
from sram_layoutgen.tech import Tech

DETERMINISTIC_GDS_TIMESTAMP = datetime(2026, 1, 1, 0, 0, 0)


def _center(bbox: dict[str, float]) -> tuple[float, float]:
    return (round((bbox["lx"] + bbox["rx"]) * 0.5, 6), round((bbox["by"] + bbox["uy"]) * 0.5, 6))


def _m1_rect(top: gdstk.Cell, bbox: dict[str, float]) -> None:
    top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=11, datatype=0))


def _m2_rect(top: gdstk.Cell, bbox: dict[str, float]) -> None:
    top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=13, datatype=0))


def _m3_rect(top: gdstk.Cell, bbox: dict[str, float]) -> None:
    top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=15, datatype=0))


def _via1_rect(top: gdstk.Cell, bbox: dict[str, float]) -> None:
    top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=12, datatype=0))


def _via2_rect(top: gdstk.Cell, bbox: dict[str, float]) -> None:
    top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=14, datatype=0))


def _snap_box(box: dict[str, float], grid: float) -> dict[str, float]:
    return {key: round(round(float(value) / grid) * grid, 6) for key, value in box.items()}


def _child_specs(contract: dict[str, Any]) -> list[ChildSpec]:
    specs: list[ChildSpec] = []
    for row in contract["child_assets"]:
        specs.append(
            ChildSpec(
                instance_name=row["instance_name"],
                logical_module=row["module"],
                physical_cell_name=row["root_cell_name"],
                gds_path=Path(row["gds_path"]),
                pin_map_path=Path(row["pin_map_path"]),
            )
        )
    return specs


def _place_children(contract: dict[str, Any], placed_children: list[PlacedChild]) -> list[PlacedChild]:
    desired = {
        "upper_enable_stage": (0.0, 0.0),
        "lower_wordline_stage_0": (46.0, 0.0),
        "lower_wordline_stage_1": (92.0, 0.0),
    }
    bbox_by_name = {item.spec.instance_name: item.bbox for item in placed_children}
    updated: list[PlacedChild] = []
    for item in placed_children:
        bbox = bbox_by_name[item.spec.instance_name]
        place_x, place_y = desired[item.spec.instance_name]
        pin_map = read_json(item.spec.pin_map_path)
        placed_pin_map, origin = transform_pin_map(
            pin_map,
            bbox=bbox,
            placement_x=place_x,
            placement_y=place_y,
            orientation="R0",
        )
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        updated.append(
            PlacedChild(
                spec=item.spec,
                clone_root_name=item.clone_root_name,
                renamed_root_name=item.renamed_root_name,
                clone_gds_path=item.clone_gds_path,
                placement_origin=origin,
                bbox=[round(place_x, 6), round(place_y, 6), round(place_x + width, 6), round(place_y + height, 6)],
                placed_pin_map=placed_pin_map,
            )
        )
    return updated


def _rail_tap(
    *,
    rail_box: dict[str, float],
    x_center: float,
    tech: Tech,
) -> dict[str, float]:
    grid = tech.manufacturing_grid
    width = max(tech.layer("m1").min_width, 0.14)
    return _snap_box(
        {
            "lx": x_center - width * 0.5,
            "by": float(rail_box["by"]),
            "rx": x_center + width * 0.5,
            "uy": float(rail_box["uy"]),
        },
        grid,
    )


def _m2_bus_route(
    *,
    top: gdstk.Cell,
    tech: Tech,
    endpoint_boxes: list[dict[str, float]],
    top_pin_x: float,
    track_y: float,
    branch_x_shift: float = 0.0,
) -> dict[str, Any]:
    grid = tech.manufacturing_grid
    width = tech.layer("m2").min_width
    route_rows: list[dict[str, Any]] = []
    centers = [_center(box) for box in endpoint_boxes]
    track_y = round(round(track_y / grid) * grid, 6)
    branch_centers = [round(cx + branch_x_shift, 6) for cx, _ in centers]
    trunk = _snap_box(
        {
            "lx": top_pin_x,
            "by": track_y - width * 0.5,
            "rx": max(branch_centers),
            "uy": track_y + width * 0.5,
        },
        grid,
    )
    _m2_rect(top, trunk)
    route_rows.append({"m2_trunk_bbox": trunk})
    top_pin_bbox = _snap_box(
        {
            "lx": top_pin_x - width * 0.5,
            "by": track_y - width * 0.5,
            "rx": top_pin_x + width * 0.5,
            "uy": track_y + width * 0.5,
        },
        grid,
    )
    _m2_rect(top, top_pin_bbox)
    route_rows.append({"top_pin_bbox": top_pin_bbox})
    for box, (cx, cy), branch_cx in zip(endpoint_boxes, centers, branch_centers):
        endpoint_span = _snap_box(
            {
                "lx": min(float(box["lx"]), branch_cx - width * 0.5),
                "by": float(box["by"]),
                "rx": max(float(box["rx"]), branch_cx + width * 0.5),
                "uy": float(box["uy"]),
            },
            grid,
        )
        vertical_branch = _snap_box(
            {
                "lx": branch_cx - width * 0.5,
                "by": min(cy, track_y) - width * 0.5,
                "rx": branch_cx + width * 0.5,
                "uy": max(cy, track_y) + width * 0.5,
            },
            grid,
        )
        _m2_rect(top, endpoint_span)
        _m2_rect(top, vertical_branch)
        route_rows.append({"endpoint_bbox": box, "m2_endpoint_span_bbox": endpoint_span, "m2_branch_bbox": vertical_branch})
    return {"route_rows": route_rows, "top_pin_bbox": top_pin_bbox}


def _m3_bus_from_m2_pins_route(
    *,
    top: gdstk.Cell,
    tech: Tech,
    endpoint_boxes: list[dict[str, float]],
    top_pin_x: float,
    track_y: float,
    branch_x_shift: float = 0.0,
) -> dict[str, Any]:
    grid = tech.manufacturing_grid
    m2_w = tech.layer("m2").min_width
    m3_w = tech.layer("m3").min_width
    via2 = tech.via_between("m2", "m3")
    assert via2 is not None
    via_enc = 0.035
    landing_half_w_m2 = max(m2_w * 0.5, via2.size * 0.5 + via_enc)
    landing_half_w_m3 = max(m3_w * 0.5, via2.size * 0.5 + via_enc)
    track_y = round(round(track_y / grid) * grid, 6)
    centers = [_center(box) for box in endpoint_boxes]
    route_rows: list[dict[str, Any]] = []
    branch_centers = [round(cx + branch_x_shift, 6) for cx, _ in centers] + [round(top_pin_x, 6)]
    trunk = _snap_box(
        {
            "lx": min(branch_centers) - landing_half_w_m3,
            "by": track_y - landing_half_w_m3,
            "rx": max(branch_centers) + landing_half_w_m3,
            "uy": track_y + landing_half_w_m3,
        },
        grid,
    )
    _m3_rect(top, trunk)
    route_rows.append({"m3_trunk_bbox": trunk})

    top_pin_bbox = _snap_box(
        {
            "lx": top_pin_x - landing_half_w_m2,
            "by": track_y - landing_half_w_m2,
            "rx": top_pin_x + landing_half_w_m2,
            "uy": track_y + landing_half_w_m2,
        },
        grid,
    )
    top_pin_via2 = _snap_box(
        {
            "lx": top_pin_x - via2.size * 0.5,
            "by": track_y - via2.size * 0.5,
            "rx": top_pin_x + via2.size * 0.5,
            "uy": track_y + via2.size * 0.5,
        },
        grid,
    )
    _m2_rect(top, top_pin_bbox)
    _via2_rect(top, top_pin_via2)
    route_rows.append({"top_pin_bbox": top_pin_bbox, "top_pin_via2_bbox": top_pin_via2})

    for box, (cx, cy), branch_cx in zip(endpoint_boxes, centers, branch_centers):
        endpoint_pad = _snap_box(
            {
                "lx": float(box["lx"]),
                "by": float(box["by"]),
                "rx": float(box["rx"]),
                "uy": float(box["uy"]),
            },
            grid,
        )
        m2_horizontal = _snap_box(
            {
                "lx": min(cx, branch_cx) - landing_half_w_m2,
                "by": cy - landing_half_w_m2,
                "rx": max(cx, branch_cx) + landing_half_w_m2,
                "uy": cy + landing_half_w_m2,
            },
            grid,
        )
        m2_vertical = _snap_box(
            {
                "lx": branch_cx - landing_half_w_m2,
                "by": min(cy, track_y) - landing_half_w_m2,
                "rx": branch_cx + landing_half_w_m2,
                "uy": max(cy, track_y) + landing_half_w_m2,
            },
            grid,
        )
        via2_bbox = _snap_box(
            {
                "lx": branch_cx - via2.size * 0.5,
                "by": track_y - via2.size * 0.5,
                "rx": branch_cx + via2.size * 0.5,
                "uy": track_y + via2.size * 0.5,
            },
            grid,
        )
        _m2_rect(top, endpoint_pad)
        _m2_rect(top, m2_horizontal)
        _m2_rect(top, m2_vertical)
        _via2_rect(top, via2_bbox)
        route_rows.append(
            {
                "endpoint_bbox": box,
                "m2_horizontal_bbox": m2_horizontal,
                "m2_vertical_bbox": m2_vertical,
                "endpoint_via2_bbox": via2_bbox,
            }
        )
    return {"route_rows": route_rows, "top_pin_bbox": top_pin_bbox}


def _m2_to_m1_rail_route(
    *,
    top: gdstk.Cell,
    tech: Tech,
    endpoint_boxes: list[dict[str, float]],
    rail_box: dict[str, float],
    branch_x: float,
) -> dict[str, Any]:
    grid = tech.manufacturing_grid
    m1_w = tech.layer("m1").min_width
    m2_w = tech.layer("m2").min_width
    via1 = tech.via_between("m1", "m2")
    assert via1 is not None
    via_enc = 0.035
    route_rows: list[dict[str, Any]] = []
    rail_y = round((float(rail_box["by"]) + float(rail_box["uy"])) * 0.5, 6)
    tap = _snap_box(
        {
            "lx": branch_x - max(m1_w * 0.5, via1.size * 0.5 + via_enc),
            "by": float(rail_box["by"]),
            "rx": branch_x + max(m1_w * 0.5, via1.size * 0.5 + via_enc),
            "uy": float(rail_box["uy"]),
        },
        grid,
    )
    _m1_rect(top, tap)
    route_rows.append({"rail_tap_bbox": tap})
    for box in endpoint_boxes:
        cx, cy = _center(box)
        endpoint_pad = _snap_box(
            {
                "lx": float(box["lx"]),
                "by": float(box["by"]),
                "rx": float(box["rx"]),
                "uy": float(box["uy"]),
            },
            grid,
        )
        m2_h = _snap_box(
            {
                "lx": min(cx, branch_x) - m2_w * 0.5,
                "by": cy - m2_w * 0.5,
                "rx": max(cx, branch_x) + m2_w * 0.5,
                "uy": cy + m2_w * 0.5,
            },
            grid,
        )
        m2_v = _snap_box(
            {
                "lx": branch_x - m2_w * 0.5,
                "by": min(cy, rail_y) - m2_w * 0.5,
                "rx": branch_x + m2_w * 0.5,
                "uy": max(cy, rail_y) + m2_w * 0.5,
            },
            grid,
        )
        via1_bbox = _snap_box(
            {
                "lx": branch_x - via1.size * 0.5,
                "by": rail_y - via1.size * 0.5,
                "rx": branch_x + via1.size * 0.5,
                "uy": rail_y + via1.size * 0.5,
            },
            grid,
        )
        _m2_rect(top, endpoint_pad)
        _m2_rect(top, m2_h)
        _m2_rect(top, m2_v)
        _via1_rect(top, via1_bbox)
        route_rows.append(
            {
                "endpoint_bbox": box,
                "m2_horizontal_bbox": m2_h,
                "m2_vertical_bbox": m2_v,
                "via1_bbox": via1_bbox,
            }
        )
    return {"route_rows": route_rows}


def _m2m3_pin_to_m1_rail_route(
    *,
    top: gdstk.Cell,
    tech: Tech,
    endpoint_boxes: list[dict[str, float]],
    rail_box: dict[str, float],
    branch_x: float,
) -> dict[str, Any]:
    grid = tech.manufacturing_grid
    m1_w = tech.layer("m1").min_width
    m2_w = tech.layer("m2").min_width
    m3_w = tech.layer("m3").min_width
    via1 = tech.via_between("m1", "m2")
    via2 = tech.via_between("m2", "m3")
    assert via1 is not None
    assert via2 is not None
    via1_enc = 0.035
    via2_enc = 0.035
    half_w = max(m1_w * 0.5, via1.size * 0.5 + via1_enc)
    m2_v_half_w = max(m2_w * 0.5, via1.size * 0.5 + via1_enc, via2.size * 0.5 + via2_enc)
    m3_h_half_w = max(m3_w * 0.5, via2.size * 0.5 + via2_enc)
    route_rows: list[dict[str, Any]] = []
    rail_y = round((float(rail_box["by"]) + float(rail_box["uy"])) * 0.5, 6)
    rail_extension = _snap_box(
        {
            "lx": min(branch_x - half_w, float(rail_box["lx"])),
            "by": float(rail_box["by"]),
            "rx": max(branch_x + half_w, float(rail_box["lx"])),
            "uy": float(rail_box["uy"]),
        },
        grid,
    )
    _m1_rect(top, rail_extension)
    route_rows.append({"rail_extension_bbox": rail_extension})
    for box in endpoint_boxes:
        cx, cy = _center(box)
        endpoint_pad = _snap_box(
            {
                "lx": float(box["lx"]),
                "by": float(box["by"]),
                "rx": float(box["rx"]),
                "uy": float(box["uy"]),
            },
            grid,
        )
        endpoint_via2 = _snap_box(
            {
                "lx": cx - via2.size * 0.5,
                "by": cy - via2.size * 0.5,
                "rx": cx + via2.size * 0.5,
                "uy": cy + via2.size * 0.5,
            },
            grid,
        )
        branch_via2 = _snap_box(
            {
                "lx": branch_x - via2.size * 0.5,
                "by": cy - via2.size * 0.5,
                "rx": branch_x + via2.size * 0.5,
                "uy": cy + via2.size * 0.5,
            },
            grid,
        )
        m3_h = _snap_box(
            {
                "lx": min(cx, branch_x) - m3_h_half_w,
                "by": cy - m3_h_half_w,
                "rx": max(cx, branch_x) + m3_h_half_w,
                "uy": cy + m3_h_half_w,
            },
            grid,
        )
        m2_v = _snap_box(
            {
                "lx": branch_x - m2_v_half_w,
                "by": min(cy, rail_y) - m2_v_half_w,
                "rx": branch_x + m2_v_half_w,
                "uy": max(cy, rail_y) + m2_v_half_w,
            },
            grid,
        )
        via1_bbox = _snap_box(
            {
                "lx": branch_x - via1.size * 0.5,
                "by": rail_y - via1.size * 0.5,
                "rx": branch_x + via1.size * 0.5,
                "uy": rail_y + via1.size * 0.5,
            },
            grid,
        )
        _m2_rect(top, endpoint_pad)
        _via2_rect(top, endpoint_via2)
        _m3_rect(top, m3_h)
        _via2_rect(top, branch_via2)
        _m2_rect(top, m2_v)
        _via1_rect(top, via1_bbox)
        route_rows.append(
            {
                "endpoint_bbox": box,
                "endpoint_via2_bbox": endpoint_via2,
                "m3_horizontal_bbox": m3_h,
                "branch_via2_bbox": branch_via2,
                "m2_vertical_bbox": m2_v,
                "via1_bbox": via1_bbox,
            }
        )
    return {"route_rows": route_rows}


def _m1_to_m2_route(
    *,
    top: gdstk.Cell,
    tech: Tech,
    source_box: dict[str, float],
    dest_box: dict[str, float],
    track_y: float,
    source_branch_x_shift: float = 0.0,
    dest_branch_x_shift: float = 0.0,
) -> dict[str, Any]:
    grid = tech.manufacturing_grid
    m1_w = tech.layer("m1").min_width
    m2_w = tech.layer("m2").min_width
    via1 = tech.via_between("m1", "m2")
    assert via1 is not None
    src_cx, src_cy = _center(source_box)
    dst_cx, dst_cy = _center(dest_box)
    src_branch_x = round(round((src_cx + source_branch_x_shift) / grid) * grid, 6)
    dst_branch_x = round(round((dst_cx + dest_branch_x_shift) / grid) * grid, 6)
    track_y = round(round(track_y / grid) * grid, 6)
    src_m1 = _snap_box(
        {
            "lx": float(source_box["lx"]),
            "by": min(float(source_box["by"]), src_cy - m1_w * 0.5),
            "rx": float(source_box["rx"]),
            "uy": max(float(source_box["uy"]), src_cy + m1_w * 0.5),
        },
        grid,
    )
    via1_src = _snap_box(
        {
            "lx": src_branch_x - via1.size * 0.5,
            "by": src_cy - via1.size * 0.5,
            "rx": src_branch_x + via1.size * 0.5,
            "uy": src_cy + via1.size * 0.5,
        },
        grid,
    )
    src_m1_h = _snap_box(
        {
            "lx": min(src_cx, src_branch_x) - m1_w * 0.5,
            "by": src_cy - m1_w * 0.5,
            "rx": max(src_cx, src_branch_x) + m1_w * 0.5,
            "uy": src_cy + m1_w * 0.5,
        },
        grid,
    )
    src_m2_v = _snap_box(
        {
            "lx": src_branch_x - m2_w * 0.5,
            "by": min(src_cy, track_y) - m2_w * 0.5,
            "rx": src_branch_x + m2_w * 0.5,
            "uy": max(src_cy, track_y) + m2_w * 0.5,
        },
        grid,
    )
    trunk = _snap_box(
        {
            "lx": min(src_branch_x, dst_branch_x) - m2_w * 0.5,
            "by": track_y - m2_w * 0.5,
            "rx": max(src_branch_x, dst_branch_x) + m2_w * 0.5,
            "uy": track_y + m2_w * 0.5,
        },
        grid,
    )
    dst_m2_h = _snap_box(
        {
            "lx": min(dst_cx, dst_branch_x) - m2_w * 0.5,
            "by": dst_cy - m2_w * 0.5,
            "rx": max(dst_cx, dst_branch_x) + m2_w * 0.5,
            "uy": dst_cy + m2_w * 0.5,
        },
        grid,
    )
    dst_m2_v = _snap_box(
        {
            "lx": dst_branch_x - m2_w * 0.5,
            "by": min(dst_cy, track_y) - m2_w * 0.5,
            "rx": dst_branch_x + m2_w * 0.5,
            "uy": max(dst_cy, track_y) + m2_w * 0.5,
        },
        grid,
    )
    _m1_rect(top, src_m1)
    _m1_rect(top, src_m1_h)
    _via1_rect(top, via1_src)
    _m2_rect(top, src_m2_v)
    _m2_rect(top, trunk)
    _m2_rect(top, dst_m2_h)
    _m2_rect(top, dst_m2_v)
    return {
        "route_rows": [
            {
                "source_bbox": source_box,
                "dest_bbox": dest_box,
                "source_m1_bbox": src_m1,
                "source_m1_horizontal_bbox": src_m1_h,
                "source_via1_bbox": via1_src,
                "source_m2_vertical_bbox": src_m2_v,
                "m2_trunk_bbox": trunk,
                "dest_m2_horizontal_bbox": dst_m2_h,
                "dest_m2_vertical_bbox": dst_m2_v,
            }
        ]
    }


def _m1_to_m3_to_m2_route(
    *,
    top: gdstk.Cell,
    tech: Tech,
    source_box: dict[str, float],
    dest_box: dict[str, float],
    track_y: float,
    source_branch_x_shift: float = 0.0,
    dest_branch_x_shift: float = 0.0,
    source_jog_y: float | None = None,
    source_jog_x_shift: float = 0.0,
) -> dict[str, Any]:
    grid = tech.manufacturing_grid
    m1_w = tech.layer("m1").min_width
    m2_w = tech.layer("m2").min_width
    m3_w = tech.layer("m3").min_width
    via1 = tech.via_between("m1", "m2")
    via2 = tech.via_between("m2", "m3")
    assert via1 is not None
    assert via2 is not None
    via1_enc = 0.035
    via2_enc = 0.035
    m1_via1_half_w = max(m1_w * 0.5, via1.size * 0.5 + via1_enc)
    m2_via1_via2_half_w = max(m2_w * 0.5, via1.size * 0.5 + via1_enc, via2.size * 0.5 + via2_enc)
    m3_via2_half_w = max(m3_w * 0.5, via2.size * 0.5 + via2_enc)
    src_cx, src_cy = _center(source_box)
    dst_cx, dst_cy = _center(dest_box)
    src_branch_x = round(round((src_cx + source_branch_x_shift) / grid) * grid, 6)
    src_trunk_x = round(round((src_branch_x + source_jog_x_shift) / grid) * grid, 6) if source_jog_y is not None else src_branch_x
    dst_branch_x = round(round((dst_cx + dest_branch_x_shift) / grid) * grid, 6)
    track_y = round(round(track_y / grid) * grid, 6)

    src_m1 = _snap_box(
        {
            "lx": float(source_box["lx"]),
            "by": min(float(source_box["by"]), src_cy - m1_w * 0.5),
            "rx": float(source_box["rx"]),
            "uy": max(float(source_box["uy"]), src_cy + m1_w * 0.5),
        },
        grid,
    )
    src_m1_h = _snap_box(
        {
            "lx": min(src_cx, src_branch_x) - m1_via1_half_w,
            "by": src_cy - m1_via1_half_w,
            "rx": max(src_cx, src_branch_x) + m1_via1_half_w,
            "uy": src_cy + m1_via1_half_w,
        },
        grid,
    )
    src_via1 = _snap_box(
        {
            "lx": src_branch_x - via1.size * 0.5,
            "by": src_cy - via1.size * 0.5,
            "rx": src_branch_x + via1.size * 0.5,
            "uy": src_cy + via1.size * 0.5,
        },
        grid,
    )
    if source_jog_y is None:
        src_m2_v = _snap_box(
            {
                "lx": src_branch_x - m2_via1_via2_half_w,
                "by": min(src_cy, track_y) - m2_via1_via2_half_w,
                "rx": src_branch_x + m2_via1_via2_half_w,
                "uy": max(src_cy, track_y) + m2_via1_via2_half_w,
            },
            grid,
        )
        src_m2_jog = None
        src_m2_v_upper = None
    else:
        jog_y = round(round(source_jog_y / grid) * grid, 6)
        src_m2_v = _snap_box(
            {
                "lx": src_branch_x - m2_via1_via2_half_w,
                "by": min(src_cy, jog_y) - m2_via1_via2_half_w,
                "rx": src_branch_x + m2_via1_via2_half_w,
                "uy": max(src_cy, jog_y) + m2_via1_via2_half_w,
            },
            grid,
        )
        src_m2_jog = _snap_box(
            {
                "lx": min(src_branch_x, src_trunk_x) - m2_via1_via2_half_w,
                "by": jog_y - m2_via1_via2_half_w,
                "rx": max(src_branch_x, src_trunk_x) + m2_via1_via2_half_w,
                "uy": jog_y + m2_via1_via2_half_w,
            },
            grid,
        )
        src_m2_v_upper = _snap_box(
            {
                "lx": src_trunk_x - m2_via1_via2_half_w,
                "by": min(jog_y, track_y) - m2_via1_via2_half_w,
                "rx": src_trunk_x + m2_via1_via2_half_w,
                "uy": max(jog_y, track_y) + m2_via1_via2_half_w,
            },
            grid,
        )
    source_via2_half = via2.size * 0.5
    src_via2 = _snap_box(
        {
            "lx": src_trunk_x - source_via2_half,
            "by": track_y - source_via2_half,
            "rx": src_trunk_x + source_via2_half,
            "uy": track_y + source_via2_half,
        },
        grid,
    )
    dst_via2 = _snap_box(
        {
            "lx": dst_branch_x - via2.size * 0.5,
            "by": track_y - via2.size * 0.5,
            "rx": dst_branch_x + via2.size * 0.5,
            "uy": track_y + via2.size * 0.5,
        },
        grid,
    )
    trunk = _snap_box(
        {
            "lx": min(src_trunk_x, dst_branch_x) - m3_via2_half_w,
            "by": track_y - m3_via2_half_w,
            "rx": max(src_trunk_x, dst_branch_x) + m3_via2_half_w,
            "uy": track_y + m3_via2_half_w,
        },
        grid,
    )
    dst_m2_v = _snap_box(
        {
            "lx": dst_branch_x - m2_via1_via2_half_w,
            "by": min(dst_cy, track_y) - m2_via1_via2_half_w,
            "rx": dst_branch_x + m2_via1_via2_half_w,
            "uy": max(dst_cy, track_y) + m2_via1_via2_half_w,
        },
        grid,
    )
    dst_m2_h = _snap_box(
        {
            "lx": min(dst_cx, dst_branch_x) - m2_w * 0.5,
            "by": dst_cy - m2_w * 0.5,
            "rx": max(dst_cx, dst_branch_x) + m2_w * 0.5,
            "uy": dst_cy + m2_w * 0.5,
        },
        grid,
    )
    _m1_rect(top, src_m1)
    _m1_rect(top, src_m1_h)
    _via1_rect(top, src_via1)
    _m2_rect(top, src_m2_v)
    if src_m2_jog is not None and src_m2_v_upper is not None:
        _m2_rect(top, src_m2_jog)
        _m2_rect(top, src_m2_v_upper)
    _via2_rect(top, src_via2)
    _m3_rect(top, trunk)
    _via2_rect(top, dst_via2)
    _m2_rect(top, dst_m2_v)
    _m2_rect(top, dst_m2_h)
    return {
        "route_rows": [
            {
                "source_bbox": source_box,
                "dest_bbox": dest_box,
                "source_m1_bbox": src_m1,
                "source_m1_horizontal_bbox": src_m1_h,
                "source_via1_bbox": src_via1,
                "source_m2_vertical_bbox": src_m2_v,
                **({"source_m2_jog_bbox": src_m2_jog, "source_m2_upper_vertical_bbox": src_m2_v_upper} if src_m2_jog is not None and src_m2_v_upper is not None else {}),
                "source_via2_bbox": src_via2,
                "m3_trunk_bbox": trunk,
                "dest_via2_bbox": dst_via2,
                "dest_m2_vertical_bbox": dst_m2_v,
                "dest_m2_horizontal_bbox": dst_m2_h,
            }
        ]
    }


def _bus_route(
    *,
    top: gdstk.Cell,
    tech: Tech,
    endpoint_boxes: list[dict[str, float]],
    track_y: float,
    top_pin_name: str | None = None,
    top_pin_x: float | None = None,
    branch_x_shift: float = 0.0,
) -> dict[str, Any]:
    grid = tech.manufacturing_grid
    m1_w = tech.layer("m1").min_width
    m2_w = tech.layer("m2").min_width
    m3_w = tech.layer("m3").min_width
    via1 = tech.via_between("m1", "m2")
    via2 = tech.via_between("m2", "m3")
    assert via1 is not None
    assert via2 is not None
    via_enc = 0.035
    landing_half_w_m1 = max(m1_w * 0.5, via1.size * 0.5 + via_enc)
    landing_half_w_m2 = max(m2_w * 0.5, via1.size * 0.5 + via_enc)
    landing_half_w_m3 = max(m3_w * 0.5, via2.size * 0.5 + via_enc)
    track_y = round(round(track_y / grid) * grid, 6)
    centers = [_center(box) for box in endpoint_boxes]
    branch_centers = [round(cx + branch_x_shift, 6) for cx, _ in centers]
    min_cx = min(branch_centers)
    max_cx = max(branch_centers)
    route_rows: list[dict[str, Any]] = []
    pin_bbox: dict[str, float] | None = None
    for box, (cx, cy), branch_cx in zip(endpoint_boxes, centers, branch_centers):
        escape_up = track_y >= cy
        via_cy = (
            max(cy, float(box["uy"]) + via1.size * 0.5 + via_enc)
            if escape_up
            else min(cy, float(box["by"]) - via1.size * 0.5 - via_enc)
        )
        m1_landing = _snap_box(
            {
                "lx": min(cx, branch_cx) - landing_half_w_m1,
                "by": min(float(box["by"]), via_cy - landing_half_w_m1),
                "rx": max(cx, branch_cx) + landing_half_w_m1,
                "uy": max(float(box["uy"]), via_cy + landing_half_w_m1),
            },
            grid,
        )
        m2_lower_pad = _snap_box(
            {
                "lx": branch_cx - landing_half_w_m2,
                "by": via_cy - landing_half_w_m2,
                "rx": branch_cx + landing_half_w_m2,
                "uy": via_cy + landing_half_w_m2,
            },
            grid,
        )
        m2_upper_pad = _snap_box(
            {
                "lx": branch_cx - landing_half_w_m2,
                "by": track_y - landing_half_w_m2,
                "rx": branch_cx + landing_half_w_m2,
                "uy": track_y + landing_half_w_m2,
            },
            grid,
        )
        m2_branch = _snap_box(
            {
                "lx": branch_cx - m2_w * 0.5,
                "by": min(via_cy, track_y),
                "rx": branch_cx + m2_w * 0.5,
                "uy": max(via_cy, track_y),
            },
            grid,
        )
        via1_bbox = _snap_box(
            {
                "lx": branch_cx - via1.size * 0.5,
                "by": via_cy - via1.size * 0.5,
                "rx": branch_cx + via1.size * 0.5,
                "uy": via_cy + via1.size * 0.5,
            },
            grid,
        )
        via2_bbox = _snap_box(
            {
                "lx": branch_cx - via2.size * 0.5,
                "by": track_y - via2.size * 0.5,
                "rx": branch_cx + via2.size * 0.5,
                "uy": track_y + via2.size * 0.5,
            },
            grid,
        )
        m3_landing = _snap_box(
            {
                "lx": branch_cx - landing_half_w_m3,
                "by": track_y - landing_half_w_m3,
                "rx": branch_cx + landing_half_w_m3,
                "uy": track_y + landing_half_w_m3,
            },
            grid,
        )
        _m1_rect(top, m1_landing)
        _m2_rect(top, m2_lower_pad)
        _m2_rect(top, m2_upper_pad)
        _m2_rect(top, m2_branch)
        _via1_rect(top, via1_bbox)
        _m3_rect(top, m3_landing)
        _via2_rect(top, via2_bbox)
        route_rows.append(
            {
                "m1_landing_bbox": m1_landing,
                "m2_lower_pad_bbox": m2_lower_pad,
                "m2_upper_pad_bbox": m2_upper_pad,
                "m2_branch_bbox": m2_branch,
                "via1_bbox": via1_bbox,
                "m3_landing_bbox": m3_landing,
                "via2_bbox": via2_bbox,
            }
        )
    if top_pin_name is not None and top_pin_x is not None:
        pin_bbox = _snap_box(
            {
                "lx": top_pin_x - landing_half_w_m2,
                "by": track_y - landing_half_w_m2,
                "rx": top_pin_x + landing_half_w_m2,
                "uy": track_y + landing_half_w_m2,
            },
            grid,
        )
        pin_via2 = _snap_box(
            {
                "lx": top_pin_x - via2.size * 0.5,
                "by": track_y - via2.size * 0.5,
                "rx": top_pin_x + via2.size * 0.5,
                "uy": track_y + via2.size * 0.5,
            },
            grid,
        )
        pin_m3_landing = _snap_box(
            {
                "lx": top_pin_x - landing_half_w_m3,
                "by": track_y - landing_half_w_m3,
                "rx": top_pin_x + landing_half_w_m3,
                "uy": track_y + landing_half_w_m3,
            },
            grid,
        )
        _m2_rect(top, pin_bbox)
        _via2_rect(top, pin_via2)
        _m3_rect(top, pin_m3_landing)
        route_rows.append(
            {
                "top_pin_bbox": pin_bbox,
                "top_pin_via2_bbox": pin_via2,
                "top_pin_m3_landing_bbox": pin_m3_landing,
            }
        )
        min_cx = min(min_cx, top_pin_x)
        max_cx = max(max_cx, top_pin_x)
    trunk = _snap_box(
        {
            "lx": min_cx,
            "by": track_y - landing_half_w_m3,
            "rx": max_cx,
            "uy": track_y + landing_half_w_m3,
        },
        grid,
    )
    _m3_rect(top, trunk)
    route_rows.append({"m3_trunk_bbox": trunk})
    return {"route_rows": route_rows, "top_pin_bbox": pin_bbox}


def _build_endpoints(placed_by_name: dict[str, PlacedChild]) -> dict[str, list[dict[str, Any]]]:
    endpoints: dict[str, list[dict[str, Any]]] = {}
    upper = placed_by_name["upper_enable_stage"]
    lower0 = placed_by_name["lower_wordline_stage_0"]
    lower1 = placed_by_name["lower_wordline_stage_1"]

    def add(net_name: str, item: PlacedChild, pin_name: str) -> None:
        endpoints.setdefault(net_name, []).append(
            {
                "endpoint_name": f"{item.spec.instance_name}.{pin_name}",
                "bbox": item.placed_pin_map[pin_name][0],
            }
        )

    for pin in ["VDD", "VSS"]:
        add(pin, upper, pin)
        add(pin, lower0, pin)
        add(pin, lower1, pin)
    add("VDD", upper, "EN")
    add("VSS", upper, "A0")
    add("VSS", upper, "A1")
    add("A3", upper, "A2")

    for top_net, formal_pin in [("A0", "A2"), ("A1", "A1"), ("A2", "A0")]:
        add(top_net, lower0, formal_pin)
        add(top_net, lower1, formal_pin)

    add("EN_0_0_0", upper, "WL0")
    add("EN_0_0_0", lower0, "EN")
    add("EN_0_0_1", upper, "WL1")
    add("EN_0_0_1", lower1, "EN")

    for bit in range(8):
        add(f"WL{bit}", lower0, f"WL{bit}")
        add(f"WL{8 + bit}", lower1, f"WL{bit}")
    return endpoints


def generate_decoder_bundle(repo_root: Path, out_dir: Path, contract: dict[str, Any]) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    tech = Tech.freepdk45(repo_root)
    specs = _child_specs(contract)
    lib, placed, clone_rows = clone_children(specs, out_dir / "clones")
    placed = _place_children(contract, placed)
    placed_by_name = {item.spec.instance_name: item for item in placed}
    top = instantiate_children(lib, contract["top_cell_name"], placed)
    rails = bridge_power_rails(top, placed, tech)

    route_report: dict[str, Any] = {"top_input_buses": {}, "internal_buses": {}, "power_ties": {}}
    top_pin_bboxes: dict[str, dict[str, float]] = {"VDD": rails["VDD"], "VSS": rails["VSS"]}
    top_pin_labels = contract["expected_top_pins"]["inputs"] + contract["expected_top_pins"]["outputs"] + contract["expected_top_pins"]["power"]
    min_x = min(item.bbox[0] for item in placed)
    top_pin_x = round(min_x - 0.35, 6)

    route_report["power_ties"]["upper_A0_A1_to_VSS"] = _m2m3_pin_to_m1_rail_route(
        top=top,
        tech=tech,
        endpoint_boxes=[
            placed_by_name["upper_enable_stage"].placed_pin_map["A0"][0],
            placed_by_name["upper_enable_stage"].placed_pin_map["A1"][0],
        ],
        rail_box=rails["VSS"],
        branch_x=-0.95,
    )
    route_report["power_ties"]["upper_EN_to_VDD"] = _m2m3_pin_to_m1_rail_route(
        top=top,
        tech=tech,
        endpoint_boxes=[placed_by_name["upper_enable_stage"].placed_pin_map["EN"][0]],
        rail_box=rails["VDD"],
        branch_x=-1.35,
    )

    a3_route = _m3_bus_from_m2_pins_route(
        top=top,
        tech=tech,
        endpoint_boxes=[placed_by_name["upper_enable_stage"].placed_pin_map["A2"][0]],
        top_pin_x=top_pin_x,
        track_y=6.65,
        branch_x_shift=0.0,
    )
    route_report["top_input_buses"]["A3"] = a3_route
    assert a3_route["top_pin_bbox"] is not None
    top_pin_bboxes["A3"] = a3_route["top_pin_bbox"]
    add_top_label(top, "A3", a3_route["top_pin_bbox"])

    for net_name, formal_pin, branch_x_shift in [("A0", "A2", -0.42), ("A1", "A1", -0.77), ("A2", "A0", -1.12)]:
        route = _m3_bus_from_m2_pins_route(
            top=top,
            tech=tech,
            endpoint_boxes=[
                placed_by_name["lower_wordline_stage_0"].placed_pin_map[formal_pin][0],
                placed_by_name["lower_wordline_stage_1"].placed_pin_map[formal_pin][0],
            ],
            top_pin_x=top_pin_x,
            track_y={"A0": 4.25, "A1": 4.75, "A2": 5.25}[net_name],
            branch_x_shift=branch_x_shift,
        )
        route_report["top_input_buses"][net_name] = route
        assert route["top_pin_bbox"] is not None
        top_pin_bboxes[net_name] = route["top_pin_bbox"]
        add_top_label(top, net_name, route["top_pin_bbox"])

    en0_route = _m1_to_m3_to_m2_route(
        top=top,
        tech=tech,
        source_box=placed_by_name["upper_enable_stage"].placed_pin_map["WL0"][0],
        dest_box=placed_by_name["lower_wordline_stage_0"].placed_pin_map["EN"][0],
        track_y=7.15,
        source_branch_x_shift=0.28,
        dest_branch_x_shift=-1.47,
    )
    en1_route = _m1_to_m3_to_m2_route(
        top=top,
        tech=tech,
        source_box=placed_by_name["upper_enable_stage"].placed_pin_map["WL1"][0],
        dest_box=placed_by_name["lower_wordline_stage_1"].placed_pin_map["EN"][0],
        track_y=7.65,
        source_branch_x_shift=0.28,
        dest_branch_x_shift=-1.47,
    )
    route_report["internal_buses"]["EN_0_0_0"] = en0_route
    route_report["internal_buses"]["EN_0_0_1"] = en1_route

    for bit in range(8):
        output_box = placed_by_name["lower_wordline_stage_0"].placed_pin_map[f"WL{bit}"][0]
        top_pin_bboxes[f"WL{bit}"] = output_box
        add_top_label(top, f"WL{bit}", output_box)
    for bit in range(8):
        output_box = placed_by_name["lower_wordline_stage_1"].placed_pin_map[f"WL{bit}"][0]
        top_pin_bboxes[f"WL{8 + bit}"] = output_box
        add_top_label(top, f"WL{8 + bit}", output_box)
    add_top_label(top, "VDD", rails["VDD"])
    add_top_label(top, "VSS", rails["VSS"])

    clean_gds = out_dir / "decoder_rebuild_clean.gds"
    review_gds = out_dir / "decoder_rebuild_review_atlas.gds"
    lib.write_gds(clean_gds, timestamp=DETERMINISTIC_GDS_TIMESTAMP)

    child_boxes = [{"label": item.spec.instance_name, "bbox": item.bbox} for item in placed]
    annotated = out_dir / "decoder_rebuild_annotated.gds"
    annotate_from_bboxes(clean_gds, contract["top_cell_name"], child_boxes, annotated)
    atlas_meta = make_review_atlas(clean_gds, annotated, contract["top_cell_name"], review_gds)

    placement_rows = [
        {
            "instance_name": item.spec.instance_name,
            "module": item.spec.logical_module,
            "x0": item.bbox[0],
            "y0": item.bbox[1],
            "x1": item.bbox[2],
            "y1": item.bbox[3],
            "orientation": item.orientation,
        }
        for item in placed
    ]
    write_csv(out_dir / "decoder_placement.csv", placement_rows)
    write_json(out_dir / "decoder_hierarchy_manifest.json", {"unresolved_references": [], "clone_rows": clone_rows})
    write_json(out_dir / "decoder_route_strategy.json", contract["route_strategy"])
    write_json(out_dir / "decoder_route_geometry.json", route_report)
    write_json(out_dir / "decoder_top_pin_map.json", {name: [bbox] for name, bbox in top_pin_bboxes.items()})
    write_json(
        out_dir / "decoder_layout_metrics.json",
        {
            "top_cell_name": contract["top_cell_name"],
            "instance_count": len(placed),
            "route_strategy": contract["route_strategy"],
            "child_instances": [row["instance_name"] for row in placement_rows],
            "fresh_rebuild": True,
            "top_bbox": bbox_from_gds(clean_gds, contract["top_cell_name"]),
        },
    )
    write_json(
        out_dir / "decoder_instance_manifest.json",
        {
            "instance_rows": [
                {
                    "instance_name": item.spec.instance_name,
                    "module": item.spec.logical_module,
                    "physical_cell_name": item.spec.physical_cell_name,
                    "clone_root_name": item.clone_root_name,
                    "renamed_root_name": item.renamed_root_name,
                    "placement_origin": list(item.placement_origin),
                }
                for item in placed
            ]
        },
    )
    return {
        "clean_gds_path": str(clean_gds.resolve()),
        "review_atlas_path": str(review_gds.resolve()),
        "annotated_gds_path": str(annotated.resolve()),
        "placement_csv_path": str((out_dir / "decoder_placement.csv").resolve()),
        "hierarchy_manifest_path": str((out_dir / "decoder_hierarchy_manifest.json").resolve()),
        "layout_metrics_path": str((out_dir / "decoder_layout_metrics.json").resolve()),
        "route_geometry_path": str((out_dir / "decoder_route_geometry.json").resolve()),
        "top_pin_map_path": str((out_dir / "decoder_top_pin_map.json").resolve()),
        "review_atlas_meta": atlas_meta,
        "top_pin_labels": top_pin_labels,
        "top_pin_bboxes": top_pin_bboxes,
        "endpoints_by_net": _build_endpoints(placed_by_name),
    }
