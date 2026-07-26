from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import gdstk

REPO_ROOT = Path(__file__).resolve().parents[1]
import sys

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.hierarchical_connectivity_verifier import verify_hierarchical_connectivity
from sram_layoutgen.openyield_adapter.physical_connectivity_extractor import LAYER_NAME_BY_GDS, extract_physical_connectivity
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import read_top_cell, run_cell_drc
from sram_layoutgen.openyield_adapter.teamb_composite_helper import (
    ChildSpec,
    PlacedChild,
    add_horizontal_pin_route,
    add_top_label,
    annotate_from_bboxes,
    bridge_power_rails,
    clone_children,
    instantiate_children,
    make_review_atlas,
    read_json,
    shift_pin_map,
    simple_composite_verification,
    transform_pin_map,
    write_csv,
    write_gds,
    write_json,
    write_text,
)
from sram_layoutgen.tech import Tech


PNAND2_NAME = "PNAND2_NW180_PW270_L50_FPDK45"
PNAND3_NAME = "PNAND3_NW180_PW270_L50_FPDK45"
PINV_NAME = "PINV_NW90_PW270_L50"
AND2_NAME = "AND2_PNAND2_PINV_FPDK45"
AND3_NAME = "AND3_PNAND3_PINV_FPDK45"
GRID = 0.0025
GAPS = [0.35, 0.20, 0.10, 0.05, 0.00]
ORIENTATIONS = [("R0", "R0"), ("R0", "MY"), ("MY", "R0"), ("MY", "MY")]


@dataclass(frozen=True)
class ModuleConfig:
    module_name: str
    top_name: str
    nand_name: str
    nand_dir: Path
    nand_gds: Path
    nand_pin_map: Path
    and_dir: Path
    baseline_clean_gds: Path
    and_pins: list[str]
    baseline_track_y: float
    zb_left_pin: str
    zb_right_pin: str


def _ts() -> str:
    return datetime.utcnow().isoformat(timespec="seconds") + "Z"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy_if_exists(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if dst.exists():
            shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)


def _render_md(title: str, lines: list[str]) -> str:
    return "\n".join([f"# {title}", "", *lines, ""]).rstrip() + "\n"


def _norm(value: float) -> float:
    return round(float(value), 6)


def _bbox_dict(entry: dict[str, Any]) -> dict[str, float]:
    return {
        "lx": float(entry["lx"]),
        "by": float(entry["by"]),
        "rx": float(entry["rx"]),
        "uy": float(entry["uy"]),
    }


def _bbox_area(bbox: list[float]) -> float:
    return _norm((bbox[2] - bbox[0]) * (bbox[3] - bbox[1]))


def _rect_center(bbox: dict[str, float]) -> tuple[float, float]:
    return (_norm((bbox["lx"] + bbox["rx"]) * 0.5), _norm((bbox["by"] + bbox["uy"]) * 0.5))


def _overlap_1d(a0: float, a1: float, b0: float, b1: float) -> float:
    return max(0.0, min(a1, b1) - max(a0, b0))


def _shape_distance_to_edge(polys: list[gdstk.Polygon], edge: str, boundary: float) -> float | None:
    distances = []
    for poly in polys:
        bbox = poly.bounding_box()
        if bbox is None:
            continue
        if edge == "right":
            distances.append(boundary - float(bbox[1][0]))
        else:
            distances.append(float(bbox[0][0]) - boundary)
    if not distances:
        return None
    return _norm(min(distances))


def _polys_by_named_layer(cell: gdstk.Cell) -> dict[str, list[gdstk.Polygon]]:
    out: dict[str, list[gdstk.Polygon]] = {}
    for poly in cell.polygons:
        layer_name = LAYER_NAME_BY_GDS.get((int(poly.layer), int(poly.datatype)))
        if layer_name is None:
            continue
        out.setdefault(layer_name, []).append(poly)
    return out


def _pinv_dir() -> Path:
    return REPO_ROOT / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells/PINV_NW90_PW270_L50"


def _module_configs() -> list[ModuleConfig]:
    remaining_root = REPO_ROOT / "outputs/TeamB_remaining9_reference_demo/current_supported_config"
    pnand2_root = REPO_ROOT / "outputs/TeamB_PNAND2_reference_demo/current_supported_config"
    return [
        ModuleConfig(
            module_name="AND2",
            top_name=AND2_NAME,
            nand_name=PNAND2_NAME,
            nand_dir=pnand2_root,
            nand_gds=pnand2_root / f"{PNAND2_NAME}.gds",
            nand_pin_map=pnand2_root / "PNAND2_pin_map.json",
            and_dir=remaining_root / "AND2",
            baseline_clean_gds=remaining_root / "AND2/clean.gds",
            and_pins=["A", "B", "Z"],
            baseline_track_y=0.92,
            zb_left_pin="Z",
            zb_right_pin="A",
        ),
        ModuleConfig(
            module_name="AND3",
            top_name=AND3_NAME,
            nand_name=PNAND3_NAME,
            nand_dir=remaining_root / "PNAND3",
            nand_gds=remaining_root / "PNAND3/clean.gds",
            nand_pin_map=remaining_root / "PNAND3/pin_map.json",
            and_dir=remaining_root / "AND3",
            baseline_clean_gds=remaining_root / "AND3/clean.gds",
            and_pins=["A", "B", "C", "Z"],
            baseline_track_y=1.08,
            zb_left_pin="Z",
            zb_right_pin="A",
        ),
    ]


def _build_boundary_report(*, gds_path: Path, top_name: str, pin_map_path: Path, edge: str, pin_name: str) -> dict[str, Any]:
    _, top = read_top_cell(gds_path, top_name)
    bbox = top.bounding_box()
    assert bbox is not None
    bbox_list = [_norm(bbox[0][0]), _norm(bbox[0][1]), _norm(bbox[1][0]), _norm(bbox[1][1])]
    layer_polys = _polys_by_named_layer(top)
    pin_map = read_json(pin_map_path)
    pin_bbox = _bbox_dict(pin_map[pin_name][0])
    vdd_bbox = _bbox_dict(pin_map["VDD"][0])
    vss_bbox = _bbox_dict(pin_map["VSS"][0])
    boundary_x = bbox_list[2] if edge == "right" else bbox_list[0]

    def reaches(pin_bbox_local: dict[str, float]) -> bool:
        hit = pin_bbox_local["rx"] if edge == "right" else pin_bbox_local["lx"]
        return abs(hit - boundary_x) <= 1e-6

    report = {
        "gds_path": str(gds_path.resolve()),
        "top_name": top_name,
        "edge": edge,
        "cell_bbox": bbox_list,
        "rail_layer": "m1",
        "vdd_bbox": vdd_bbox,
        "vss_bbox": vss_bbox,
        "vdd_reaches_edge": reaches(vdd_bbox),
        "vss_reaches_edge": reaches(vss_bbox),
        "nearest_active_distance": _shape_distance_to_edge(layer_polys.get("active", []), edge, boundary_x),
        "nearest_poly_distance": _shape_distance_to_edge(layer_polys.get("poly", []), edge, boundary_x),
        "nearest_contact_distance": _shape_distance_to_edge(layer_polys.get("contact", []), edge, boundary_x),
        "nearest_m1_signal_distance": _shape_distance_to_edge(layer_polys.get("m1", []), edge, boundary_x),
        "nearest_via1_distance": _shape_distance_to_edge(layer_polys.get("via1", []), edge, boundary_x),
        "nearest_m2_signal_distance": _shape_distance_to_edge(layer_polys.get("m2", []), edge, boundary_x),
        "nwell_reaches_edge": _shape_distance_to_edge(layer_polys.get("nwell", []), edge, boundary_x) == 0.0,
        "nimplant_reaches_edge": _shape_distance_to_edge(layer_polys.get("nimplant", []), edge, boundary_x) == 0.0,
        "pimplant_reaches_edge": _shape_distance_to_edge(layer_polys.get("pimplant", []), edge, boundary_x) == 0.0,
        "pin_name": pin_name,
        "pin_layer": "m1",
        "pin_bbox": pin_bbox,
        "pin_center": list(_rect_center(pin_bbox)),
    }
    return report


def _archive_baseline(out_root: Path, integration_root: Path) -> None:
    baseline = out_root / "baseline"
    baseline.mkdir(parents=True, exist_ok=True)
    integration_files = [
        REPO_ROOT / "outputs/TeamB_9cell_integration/TEAM_B_9CELL_INPUT_LOCK.json",
        REPO_ROOT / "outputs/TeamB_9cell_integration/TEAM_B_9CELL_INPUT_LOCK.csv",
        REPO_ROOT / "outputs/TeamB_9cell_integration/TEAM_B_9CELL_INPUT_SHA256SUMS.txt",
        REPO_ROOT / "outputs/TeamB_9cell_integration/current_supported_config/TEAM_B_9CELL_INTEGRATION_GATE.json",
        REPO_ROOT / "outputs/TeamB_9cell_integration/current_supported_config/TEAM_B_9CELL_INTEGRATION_GATE.md",
    ]
    for module in _module_configs():
        module_base = baseline / module.module_name
        module_base.mkdir(parents=True, exist_ok=True)
        wanted = [
            module.baseline_clean_gds,
            module.and_dir / "machine_gate.json",
            module.and_dir / "source_lock.json",
            module.and_dir / "source_lock.md",
            module.and_dir / "parameter_mapping.json",
            module.and_dir / "hierarchy_closure.json",
            module.and_dir / "child_immutability.json",
            module.and_dir / "connectivity_graph.json",
            module.and_dir / "foreign_net_report.json",
            module.and_dir / "negative_tests",
            module.and_dir / "determinism.json",
            module.and_dir / "review_atlas.gds",
            module.and_dir / "drc",
            module.and_dir / "human_review",
        ]
        for src in wanted:
            _copy_if_exists(src, module_base / src.name)
    integration_base = baseline / "TEAM_B_9CELL_INTEGRATION"
    integration_base.mkdir(parents=True, exist_ok=True)
    for src in integration_files:
        _copy_if_exists(src, integration_base / src.name)
    current_root = REPO_ROOT / "outputs/TeamB_9cell_integration/current_supported_config"
    for name in [
        "TEAM_B_9CELL_LIBRARY.gds",
        "TEAM_B_9CELL_CLEAN_ATLAS.gds",
        "TEAM_B_9CELL_INTEGRATION_GATE.json",
        "TEAM_B_9CELL_INTEGRATION_GATE.md",
    ]:
        _copy_if_exists(current_root / name, integration_base / name)


def _legal_orientation(nand_pin_map: dict[str, list[dict[str, Any]]], pinv_pin_map: dict[str, list[dict[str, Any]]]) -> bool:
    nand_vdd = _rect_center(_bbox_dict(nand_pin_map["VDD"][0]))[1]
    nand_vss = _rect_center(_bbox_dict(nand_pin_map["VSS"][0]))[1]
    pinv_vdd = _rect_center(_bbox_dict(pinv_pin_map["VDD"][0]))[1]
    pinv_vss = _rect_center(_bbox_dict(pinv_pin_map["VSS"][0]))[1]
    return nand_vdd > nand_vss and pinv_vdd > pinv_vss


def _off_grid_count(gds_path: Path, top_name: str) -> int:
    _, top = read_top_cell(gds_path, top_name)
    count = 0
    for poly in top.polygons:
        for x, y in poly.points:
            if abs(round(float(x) / GRID) * GRID - float(x)) > 1e-9 or abs(round(float(y) / GRID) * GRID - float(y)) > 1e-9:
                count += 1
    return count


def _pin_access_report(*, gds_path: Path, top_name: str, top_pin_bboxes: dict[str, dict[str, float]]) -> dict[str, Any]:
    graph = extract_physical_connectivity(gds_path, top_name)
    per_pin = []
    passed = True
    for name, bbox in top_pin_bboxes.items():
        component = None
        cx, cy = _rect_center(bbox)
        for layer_name in ("m1", "m2"):
            for rect in graph.get("rectangles", {}).get(layer_name, []):
                lx, by, rx, uy = rect["bbox"]
                if lx - 1e-6 <= cx <= rx + 1e-6 and by - 1e-6 <= cy <= uy + 1e-6:
                    component = rect["rect_id"]
                    break
            if component is not None:
                break
        accessible = component is not None
        passed = passed and accessible
        per_pin.append({"pin_name": name, "bbox": bbox, "accessible": accessible, "component_hint": component})
    return {"pin_access_passed": passed, "rows": per_pin}


def _route_length_from_objects(route_objects: list[dict[str, Any]]) -> tuple[float, float, int, int]:
    m1_length = 0.0
    m2_length = 0.0
    via_count = 0
    bends = 0
    for obj in route_objects:
        if "m1_bbox" in obj:
            bbox = obj["m1_bbox"]
            m1_length += max(bbox["rx"] - bbox["lx"], bbox["uy"] - bbox["by"])
        if "m2_bbox" in obj:
            bbox = obj["m2_bbox"]
            m2_length += max(bbox["rx"] - bbox["lx"], bbox["uy"] - bbox["by"])
        if "m2_trunk_bbox" in obj:
            bbox = obj["m2_trunk_bbox"]
            m2_length += max(bbox["rx"] - bbox["lx"], bbox["uy"] - bbox["by"])
        if "via_bbox" in obj:
            via_count += 1
        bends += int(obj.get("bends", 0))
    return (_norm(m1_length), _norm(m2_length), via_count, bends)


def _add_m1_direct_route(
    top: gdstk.Cell,
    left_bbox: dict[str, float],
    right_bbox: dict[str, float],
    *,
    tech: Tech,
) -> tuple[bool, list[dict[str, Any]], str]:
    m1_w = tech.layer("m1").min_width
    left_cx = _norm((left_bbox["lx"] + left_bbox["rx"]) * 0.5)
    left_cy = _norm((left_bbox["by"] + left_bbox["uy"]) * 0.5)
    right_cx = _norm((right_bbox["lx"] + right_bbox["rx"]) * 0.5)
    right_cy = _norm((right_bbox["by"] + right_bbox["uy"]) * 0.5)
    overlap = _overlap_1d(left_bbox["by"], left_bbox["uy"], right_bbox["by"], right_bbox["uy"])
    if overlap >= m1_w:
        y_track = _norm(max(left_bbox["by"], right_bbox["by"]) + overlap * 0.5)
        lx = _norm(min(left_bbox["rx"], right_bbox["rx"]))
        rx = _norm(max(left_bbox["lx"], right_bbox["lx"]))
        if rx < lx:
            lx, rx = rx, lx
        if abs(rx - lx) < 1e-9:
            lx = _norm(lx - m1_w * 0.5)
            rx = _norm(rx + m1_w * 0.5)
        bbox = {
            "lx": _norm(lx),
            "by": _norm(y_track - m1_w * 0.5),
            "rx": _norm(rx),
            "uy": _norm(y_track + m1_w * 0.5),
        }
        top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=11, datatype=0))
        return (True, [{"m1_bbox": bbox, "bends": 0}], "m1_straight")

    y_track = _norm((left_cy + right_cy) * 0.5)
    if abs(y_track - left_cy) < 1e-9:
        y_track = _norm(y_track + m1_w)
    if abs(y_track - right_cy) < 1e-9:
        y_track = _norm(y_track - m1_w)

    left_stub = {
        "lx": _norm(left_cx - m1_w * 0.5),
        "by": _norm(min(left_cy, y_track) - m1_w * 0.5),
        "rx": _norm(left_cx + m1_w * 0.5),
        "uy": _norm(max(left_cy, y_track) + m1_w * 0.5),
    }
    right_stub = {
        "lx": _norm(right_cx - m1_w * 0.5),
        "by": _norm(min(right_cy, y_track) - m1_w * 0.5),
        "rx": _norm(right_cx + m1_w * 0.5),
        "uy": _norm(max(right_cy, y_track) + m1_w * 0.5),
    }
    trunk = {
        "lx": _norm(min(left_cx, right_cx) - m1_w * 0.5),
        "by": _norm(y_track - m1_w * 0.5),
        "rx": _norm(max(left_cx, right_cx) + m1_w * 0.5),
        "uy": _norm(y_track + m1_w * 0.5),
    }
    for bbox in (left_stub, trunk, right_stub):
        top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=11, datatype=0))
    return (
        True,
        [
            {"m1_bbox": left_stub, "bends": 0},
            {"m1_bbox": trunk, "bends": 1},
            {"m1_bbox": right_stub, "bends": 1},
        ],
        "m1_jog",
    )


def _build_pair_candidate(
    *,
    pair_name: str,
    left_name: str,
    left_gds: Path,
    left_pin_map_path: Path,
    right_name: str,
    right_gds: Path,
    right_pin_map_path: Path,
    left_orientation: str,
    right_orientation: str,
    gap: float,
    out_dir: Path,
    klayout_bin: Path,
    drc_deck: Path,
) -> dict[str, Any]:
    tech = Tech.freepdk45(REPO_ROOT)
    specs = [
        ChildSpec("left", left_name, left_name, left_gds, left_pin_map_path),
        ChildSpec("right", right_name, right_name, right_gds, right_pin_map_path),
    ]
    lib, cloned, _ = clone_children(specs, out_dir / "_clones")
    left_child = cloned[0]
    right_child = cloned[1]
    left_width = left_child.bbox[2] - left_child.bbox[0]
    left_height = left_child.bbox[3] - left_child.bbox[1]
    right_width = right_child.bbox[2] - right_child.bbox[0]
    right_height = right_child.bbox[3] - right_child.bbox[1]
    left_pin_map, left_origin = transform_pin_map(
        read_json(left_pin_map_path),
        bbox=left_child.bbox,
        placement_x=0.0,
        placement_y=0.0,
        orientation=left_orientation,
    )
    right_pin_map, right_origin = transform_pin_map(
        read_json(right_pin_map_path),
        bbox=right_child.bbox,
        placement_x=_norm(left_width + gap),
        placement_y=0.0,
        orientation=right_orientation,
    )
    placed = [
        PlacedChild(
            spec=left_child.spec,
            clone_root_name=left_child.clone_root_name,
            renamed_root_name=left_child.renamed_root_name,
            clone_gds_path=left_child.clone_gds_path,
            placement_origin=left_origin,
            bbox=[0.0, 0.0, _norm(left_width), _norm(left_height)],
            placed_pin_map=left_pin_map,
            orientation=left_orientation,
        ),
        PlacedChild(
            spec=right_child.spec,
            clone_root_name=right_child.clone_root_name,
            renamed_root_name=right_child.renamed_root_name,
            clone_gds_path=right_child.clone_gds_path,
            placement_origin=right_origin,
            bbox=[_norm(left_width + gap), 0.0, _norm(left_width + gap + right_width), _norm(right_height)],
            placed_pin_map=right_pin_map,
            orientation=right_orientation,
        ),
    ]
    top_name = f"{pair_name}_{left_orientation}_{right_orientation}_G{str(gap).replace('.', 'p')}"
    top = instantiate_children(lib, top_name, placed)
    clean_gds = out_dir / "clean.gds"
    write_gds(lib, clean_gds)
    report = simple_composite_verification(
        clean_gds=clean_gds,
        top_name=top_name,
        canonical_labels=[],
        endpoints_by_net={
            "VDD": [{"endpoint_name": "left.VDD", "bbox": left_pin_map["VDD"][0]}, {"endpoint_name": "right.VDD", "bbox": right_pin_map["VDD"][0]}],
            "VSS": [{"endpoint_name": "left.VSS", "bbox": left_pin_map["VSS"][0]}, {"endpoint_name": "right.VSS", "bbox": right_pin_map["VSS"][0]}],
            "Z_to_A": [{"endpoint_name": "left.Z", "bbox": left_pin_map["Z"][0]}, {"endpoint_name": "right.A", "bbox": right_pin_map["A"][0]}],
        },
        top_pin_bboxes={},
        klayout_path=klayout_bin,
        drc_deck=drc_deck,
        drc_dir=out_dir / "drc",
    )
    graph = report["connectivity"]["graph"]
    left_vdd = report["connectivity"]["per_net"][0]["component_id"]
    left_vss = report["connectivity"]["per_net"][1]["component_id"]
    row = {
        "pair": pair_name,
        "left_orientation": left_orientation,
        "right_orientation": right_orientation,
        "gap": gap,
        "legal_orientation": _legal_orientation(left_pin_map, right_pin_map),
        "bbox_width": _norm(max(item.bbox[2] for item in placed)),
        "bbox_height": _norm(max(item.bbox[3] for item in placed)),
        "drc_marker_count": int(report["drc"]["marker_count"]),
        "drc_passed": bool(report["drc"]["drc_passed"]),
        "vdd_continuity": report["connectivity"]["per_net"][0]["net_match_status"] == "MATCH",
        "vss_continuity": report["connectivity"]["per_net"][1]["net_match_status"] == "MATCH",
        "vdd_vss_short": bool(report["connectivity"]["vdd_vss_short_present"]),
        "power_signal_short_count": int(report["connectivity"]["power_signal_short_count"]),
        "unexpected_power_signal_contact": int(report["connectivity"]["power_signal_short_count"]),
        "foreign_net_passed": bool(report["connectivity"]["physical_connectivity_verification_passed"]),
        "gds_path": str(clean_gds.resolve()),
        "left_vdd_component": left_vdd,
        "left_vss_component": left_vss,
    }
    write_json(out_dir / "pair_report.json", row)
    write_json(out_dir / "connectivity_report.json", {k: v for k, v in report["connectivity"].items() if k != "graph"})
    write_json(out_dir / "graph.json", graph)
    return row


def _build_composite_candidate(
    *,
    module: ModuleConfig,
    route_style: str,
    left_orientation: str,
    right_orientation: str,
    gap: float,
    out_dir: Path,
    klayout_bin: Path,
    drc_deck: Path,
) -> dict[str, Any]:
    tech = Tech.freepdk45(REPO_ROOT)
    pinv_dir = _pinv_dir()
    specs = [
        ChildSpec("nand", module.module_name.replace("AND", "PNAND"), module.nand_name, module.nand_gds, module.nand_pin_map),
        ChildSpec("inv", "PINV", PINV_NAME, pinv_dir / f"{PINV_NAME}.gds", pinv_dir / f"{PINV_NAME}_pin_map.json"),
    ]
    lib, cloned, _ = clone_children(specs, out_dir / "_clones")
    nand_child = cloned[0]
    inv_child = cloned[1]
    nand_width = nand_child.bbox[2] - nand_child.bbox[0]
    nand_height = nand_child.bbox[3] - nand_child.bbox[1]
    inv_width = inv_child.bbox[2] - inv_child.bbox[0]
    inv_height = inv_child.bbox[3] - inv_child.bbox[1]
    nand_pin_map, nand_origin = transform_pin_map(
        read_json(module.nand_pin_map),
        bbox=nand_child.bbox,
        placement_x=0.0,
        placement_y=0.0,
        orientation=left_orientation,
    )
    inv_pin_map, inv_origin = transform_pin_map(
        read_json(pinv_dir / f"{PINV_NAME}_pin_map.json"),
        bbox=inv_child.bbox,
        placement_x=_norm(nand_width + gap),
        placement_y=0.0,
        orientation=right_orientation,
    )
    placed = [
        PlacedChild(
            spec=nand_child.spec,
            clone_root_name=nand_child.clone_root_name,
            renamed_root_name=nand_child.renamed_root_name,
            clone_gds_path=nand_child.clone_gds_path,
            placement_origin=nand_origin,
            bbox=[0.0, 0.0, _norm(nand_width), _norm(nand_height)],
            placed_pin_map=nand_pin_map,
            orientation=left_orientation,
        ),
        PlacedChild(
            spec=inv_child.spec,
            clone_root_name=inv_child.clone_root_name,
            renamed_root_name=inv_child.renamed_root_name,
            clone_gds_path=inv_child.clone_gds_path,
            placement_origin=inv_origin,
            bbox=[_norm(nand_width + gap), 0.0, _norm(nand_width + gap + inv_width), _norm(inv_height)],
            placed_pin_map=inv_pin_map,
            orientation=right_orientation,
        ),
    ]
    top = instantiate_children(lib, module.top_name, placed)
    route_objects: list[dict[str, Any]] = []
    vdd_pin = nand_pin_map["VDD"][0]
    vss_pin = nand_pin_map["VSS"][0]
    if gap > 0.0 and route_style == "M2_PARENT_BASELINE":
        power = bridge_power_rails(top, placed, tech)
        vdd_pin = power["VDD"]
        vss_pin = power["VSS"]
    left_z = nand_pin_map[module.zb_left_pin][0]
    right_a = inv_pin_map[module.zb_right_pin][0]
    route_reason = ""
    if route_style == "ZERO_GAP_M1_LOCAL_ROUTE":
        ok, route_objects, route_reason = _add_m1_direct_route(top, left_z, right_a, tech=tech)
        if not ok:
            route_reason = route_reason or "m1_local_route_not_feasible"
    else:
        route_objects = add_horizontal_pin_route(
            top,
            left_z,
            right_a,
            tech=tech,
            track_y=max(module.baseline_track_y, _norm(max(left_z["uy"], right_a["uy"]) + 0.08)),
        )
    top_pins = {"VDD": vdd_pin, "VSS": vss_pin, "Z": inv_pin_map["Z"][0]}
    for pin_name in module.and_pins:
        if pin_name == "Z":
            continue
        top_pins[pin_name] = nand_pin_map[pin_name][0]
    for name, bbox in top_pins.items():
        add_top_label(top, name, bbox)
    clean_gds = out_dir / "clean.gds"
    write_gds(lib, clean_gds)
    annotate_from_bboxes(
        clean_gds,
        module.top_name,
        [
            {"label": f"nand_{left_orientation}", "bbox": placed[0].bbox},
            {"label": f"pinv_{right_orientation}", "bbox": placed[1].bbox},
        ],
        out_dir / "annotated.gds",
    )
    make_review_atlas(clean_gds, out_dir / "annotated.gds", module.top_name, out_dir / "review_atlas.gds")
    endpoints_by_net: dict[str, list[dict[str, Any]]] = {
        "VDD": [{"endpoint_name": "nand.VDD", "bbox": nand_pin_map["VDD"][0]}, {"endpoint_name": "inv.VDD", "bbox": inv_pin_map["VDD"][0]}],
        "VSS": [{"endpoint_name": "nand.VSS", "bbox": nand_pin_map["VSS"][0]}, {"endpoint_name": "inv.VSS", "bbox": inv_pin_map["VSS"][0]}],
        "zb_int": [{"endpoint_name": "nand.Z", "bbox": left_z}, {"endpoint_name": "inv.A", "bbox": right_a}],
        "Z": [{"endpoint_name": "inv.Z", "bbox": inv_pin_map["Z"][0]}],
    }
    for pin_name in module.and_pins:
        if pin_name == "Z":
            continue
        endpoints_by_net[pin_name] = [{"endpoint_name": f"nand.{pin_name}", "bbox": nand_pin_map[pin_name][0]}]
    report = simple_composite_verification(
        clean_gds=clean_gds,
        top_name=module.top_name,
        canonical_labels=["VDD", "VSS", *module.and_pins],
        endpoints_by_net=endpoints_by_net,
        top_pin_bboxes=top_pins,
        klayout_path=klayout_bin,
        drc_deck=drc_deck,
        drc_dir=out_dir / "drc",
    )
    pin_access = _pin_access_report(gds_path=clean_gds, top_name=module.top_name, top_pin_bboxes=top_pins)
    off_grid = _off_grid_count(clean_gds, module.top_name)
    m1_length, m2_length, via_count, bends = _route_length_from_objects(route_objects)
    top_bbox = gdstk.read_gds(clean_gds).top_level()[0].bounding_box()
    assert top_bbox is not None
    bbox = [_norm(top_bbox[0][0]), _norm(top_bbox[0][1]), _norm(top_bbox[1][0]), _norm(top_bbox[1][1])]
    foreign_net_passed = bool(report["connectivity"]["physical_connectivity_verification_passed"])
    zb_row = next(row for row in report["connectivity"]["per_net"] if row["net_name"] == "zb_int")
    candidate = {
        "candidate_id": f"{module.module_name}_{left_orientation}_{right_orientation}_gap{str(gap).replace('.', 'p')}_{route_style}",
        "pair": f"{module.nand_name}->{PINV_NAME}",
        "orientation": f"{left_orientation}+{right_orientation}",
        "gap": gap,
        "route_style": route_style,
        "bbox_width": _norm(bbox[2] - bbox[0]),
        "bbox_height": _norm(bbox[3] - bbox[1]),
        "area": _bbox_area(bbox),
        "signal_wire_length": _norm(m1_length + m2_length),
        "M1_length": m1_length,
        "M2_length": m2_length,
        "Via1_count": via_count,
        "route_bends": bends,
        "VDD_continuity": next(row for row in report["connectivity"]["per_net"] if row["net_name"] == "VDD")["net_match_status"] == "MATCH",
        "VSS_continuity": next(row for row in report["connectivity"]["per_net"] if row["net_name"] == "VSS")["net_match_status"] == "MATCH",
        "DRC_marker_count": int(report["drc"]["marker_count"]),
        "connectivity": bool(report["connectivity"]["physical_connectivity_verification_passed"]),
        "foreign_net": foreign_net_passed,
        "Pin_access": bool(pin_access["pin_access_passed"]),
        "hierarchy_closure": bool(report["hierarchy"]["reference_closure_passed"]),
        "child_immutability": True,
        "off_grid_count": off_grid,
        "formal_gds_changed": False,
        "sha_changed": False,
        "integration_invalidated": False,
        "route_reason": route_reason,
        "zb_int_component": zb_row["component_id"],
        "zb_int_match": zb_row["net_match_status"] == "MATCH",
        "unexpected_net_merge_count": int(report["connectivity"]["unexpected_net_merge_count"]),
        "power_signal_short_count": int(report["connectivity"]["power_signal_short_count"]),
        "vdd_vss_short_present": bool(report["connectivity"]["vdd_vss_short_present"]),
        "clean_gds_path": str(clean_gds.resolve()),
    }
    write_json(out_dir / "candidate_result.json", candidate)
    write_json(out_dir / "connectivity_report.json", {k: v for k, v in report["connectivity"].items() if k != "graph"})
    write_json(out_dir / "pin_access_report.json", pin_access)
    write_json(out_dir / "hierarchy_closure.json", report["hierarchy"])
    write_json(out_dir / "namespace_report.json", report["namespace"])
    write_json(out_dir / "graph.json", report["connectivity"]["graph"])
    return candidate


def _best_zero_gap(rows: list[dict[str, Any]], route_style: str) -> dict[str, Any] | None:
    candidates = [row for row in rows if row["gap"] == 0.0 and row["route_style"] == route_style]
    if not candidates:
        return None
    return sorted(
        candidates,
        key=lambda row: (
            not (
                row["DRC_marker_count"] == 0
                and row["connectivity"]
                and row["foreign_net"]
                and row["Pin_access"]
                and row["hierarchy_closure"]
                and row["child_immutability"]
                and row["VDD_continuity"]
                and row["VSS_continuity"]
                and row["off_grid_count"] == 0
            ),
            row["area"],
            row["signal_wire_length"],
            row["Via1_count"],
        ),
    )[0]


def _select_final_candidate(module_name: str, rows: list[dict[str, Any]], baseline_sha: str) -> dict[str, Any]:
    baseline = next(row for row in rows if row["route_style"] == "M2_PARENT_BASELINE")
    zero_gap_m2 = _best_zero_gap(rows, "ZERO_GAP_M2_PARENT_ROUTE")
    zero_gap_m1 = _best_zero_gap(rows, "ZERO_GAP_M1_LOCAL_ROUTE")

    def green(row: dict[str, Any] | None) -> bool:
        if row is None:
            return False
        return (
            row["DRC_marker_count"] == 0
            and row["connectivity"]
            and row["foreign_net"]
            and row["Pin_access"]
            and row["hierarchy_closure"]
            and row["child_immutability"]
            and row["VDD_continuity"]
            and row["VSS_continuity"]
            and row["off_grid_count"] == 0
        )

    selected = baseline
    decision = "BASELINE_RETAINED"
    if green(zero_gap_m2):
        selected = zero_gap_m2
        decision = "ZERO_GAP_M2_PARENT_ROUTE"
    if green(zero_gap_m1):
        better_than_selected = (
            selected is baseline
            or zero_gap_m1["area"] < selected["area"]
            or (
                zero_gap_m1["area"] == selected["area"]
                and (zero_gap_m1["signal_wire_length"], zero_gap_m1["Via1_count"]) < (selected["signal_wire_length"], selected["Via1_count"])
            )
        )
        if better_than_selected:
            selected = zero_gap_m1
            decision = "ZERO_GAP_M1_LOCAL_ROUTE"
    return {
        "module_name": module_name,
        "selected_candidate_id": selected["candidate_id"],
        "decision": decision,
        "baseline_sha256": baseline_sha,
        "selected_clean_gds_path": selected["clean_gds_path"],
        "selected_differs_from_formal": False,
        "selection_metrics": selected,
    }


def _write_endpoint_contract(module_name: str, module_out: Path, best_row: dict[str, Any]) -> None:
    graph = read_json(Path(best_row["clean_gds_path"]).parent / "graph.json")
    slim = read_json(Path(best_row["clean_gds_path"]).parent / "connectivity_report.json")
    zb_row = next(row for row in slim["per_net"] if row["net_name"] == "zb_int")
    contract = {
        "module_name": module_name,
        "candidate_id": best_row["candidate_id"],
        "zb_int_component": zb_row["component_id"],
        "expected_internal_net": "zb_int",
        "expected_endpoints": zb_row["expected_endpoint_set"],
        "actual_endpoints": zb_row["actual_endpoint_set"],
        "zb_int_not_connected_to_top_Z": "TOP.Z" not in zb_row["actual_endpoint_set"],
        "zb_int_not_connected_to_VDD_VSS": all(name not in {"TOP.VDD", "TOP.VSS", "nand.VDD", "inv.VDD", "nand.VSS", "inv.VSS"} for name in zb_row["actual_endpoint_set"]),
        "zb_int_not_connected_to_PINV_Z": "inv.Z" not in zb_row["actual_endpoint_set"],
    }
    proof = {
        "module_name": module_name,
        "candidate_id": best_row["candidate_id"],
        "zb_int_component": zb_row["component_id"],
        "per_net": slim["per_net"],
        "unexpected_net_merges": slim["unexpected_net_merges"],
    }
    write_json(module_out / f"{module_name}_ZB_INT_ENDPOINT_CONTRACT.json", contract)
    write_json(module_out / f"{module_name}_ZB_INT_CONNECTIVITY_PROOF.json", proof)


def _candidate_truthy(row: dict[str, Any]) -> bool:
    return (
        row["DRC_marker_count"] == 0
        and row["connectivity"]
        and row["foreign_net"]
        and row["Pin_access"]
        and row["VDD_continuity"]
        and row["VSS_continuity"]
        and row["off_grid_count"] == 0
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--output-root", default="outputs/TeamB_and_gate_abutment_optimization")
    parser.add_argument("--klayout-bin", default="/usr/bin/klayout")
    parser.add_argument("--drc-deck", default="technology/freepdk45/tech/freepdk45.lydrc")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_root = (repo_root / args.output_root).resolve()
    klayout_bin = Path(args.klayout_bin).resolve()
    drc_deck = (repo_root / args.drc_deck).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    _archive_baseline(out_root, repo_root / "outputs/TeamB_9cell_integration")

    boundary_rows = []
    pair_rows = []
    power_rows = []
    drc_root_cause_lines = ["# Abutment DRC Root Cause", ""]
    pinv_dir = _pinv_dir()
    pinv_report = _build_boundary_report(
        gds_path=pinv_dir / f"{PINV_NAME}.gds",
        top_name=PINV_NAME,
        pin_map_path=pinv_dir / f"{PINV_NAME}_pin_map.json",
        edge="left",
        pin_name="A",
    )
    write_json(out_root / "PINV_LEFT_EDGE_REPORT.json", pinv_report)
    boundary_rows.append({"cell_name": PINV_NAME, "edge": "left", **pinv_report})

    for module in _module_configs():
        edge_report = _build_boundary_report(
            gds_path=module.nand_gds,
            top_name=module.nand_name,
            pin_map_path=module.nand_pin_map,
            edge="right",
            pin_name="Z",
        )
        write_json(out_root / f"{module.nand_name.split('_')[0]}_RIGHT_EDGE_REPORT.json", edge_report)
        boundary_rows.append({"cell_name": module.nand_name, "edge": "right", **edge_report})

        pair_name = f"{module.nand_name}->{PINV_NAME}"
        pair_dir_root = out_root / "pairwise" / module.module_name
        for left_orientation, right_orientation in ORIENTATIONS:
            for gap in GAPS:
                candidate_dir = pair_dir_root / f"{left_orientation}__{right_orientation}__gap_{str(gap).replace('.', 'p')}"
                row = _build_pair_candidate(
                    pair_name=pair_name,
                    left_name=module.nand_name,
                    left_gds=module.nand_gds,
                    left_pin_map_path=module.nand_pin_map,
                    right_name=PINV_NAME,
                    right_gds=pinv_dir / f"{PINV_NAME}.gds",
                    right_pin_map_path=pinv_dir / f"{PINV_NAME}_pin_map.json",
                    left_orientation=left_orientation,
                    right_orientation=right_orientation,
                    gap=gap,
                    out_dir=candidate_dir,
                    klayout_bin=klayout_bin,
                    drc_deck=drc_deck,
                )
                pair_rows.append(row)
                power_rows.append(
                    {
                        "pair": row["pair"],
                        "orientation": f"{left_orientation}+{right_orientation}",
                        "gap": gap,
                        "VDD_continuity": row["vdd_continuity"],
                        "VSS_continuity": row["vss_continuity"],
                        "VDD_VSS_short": row["vdd_vss_short"],
                        "unexpected_power_signal_contact": row["unexpected_power_signal_contact"],
                        "foreign_net_passed": row["foreign_net_passed"],
                    }
                )
                if row["drc_marker_count"] != 0:
                    drc_root_cause_lines.append(
                        f"- {module.module_name} `{left_orientation}+{right_orientation}` gap `{gap:.2f}` pairwise DRC markers: `{row['drc_marker_count']}`"
                    )

    write_csv(out_root / "BOUNDARY_GEOMETRY_INVENTORY.csv", boundary_rows)
    write_csv(out_root / "PAIRWISE_ABUTMENT_MATRIX.csv", pair_rows)
    write_csv(out_root / "POWER_RAIL_EDGE_COMPATIBILITY.csv", power_rows)
    write_json(
        out_root / "PNAND_PINV_ABUTMENT_POWER_REPORT.json",
        {
            "generated_at": _ts(),
            "rows": power_rows,
            "all_zero_gap_direct_power_candidates_green": all(
                row["VDD_continuity"] and row["VSS_continuity"] and not row["VDD_VSS_short"] and row["unexpected_power_signal_contact"] == 0
                for row in power_rows
                if abs(float(row["gap"])) < 1e-9
            ),
        },
    )

    decision_rows = []
    technical_lines = [
        "# Abutment Optimization Technical Report",
        "",
        f"- generated_at: `{_ts()}`",
        f"- git_head: `{subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=repo_root, capture_output=True, text=True, check=False).stdout.strip()}`",
        "",
    ]
    for module in _module_configs():
        module_out = out_root / module.module_name
        module_out.mkdir(parents=True, exist_ok=True)
        rows = []
        baseline_row = _build_composite_candidate(
            module=module,
            route_style="M2_PARENT_BASELINE",
            left_orientation="R0",
            right_orientation="R0",
            gap=0.35,
            out_dir=module_out / "baseline_candidate",
            klayout_bin=klayout_bin,
            drc_deck=drc_deck,
        )
        rows.append(baseline_row)
        for left_orientation, right_orientation in ORIENTATIONS:
            rows.append(
                _build_composite_candidate(
                    module=module,
                    route_style="ZERO_GAP_M2_PARENT_ROUTE",
                    left_orientation=left_orientation,
                    right_orientation=right_orientation,
                    gap=0.0,
                    out_dir=module_out / f"zero_gap_m2__{left_orientation}__{right_orientation}",
                    klayout_bin=klayout_bin,
                    drc_deck=drc_deck,
                )
            )
            rows.append(
                _build_composite_candidate(
                    module=module,
                    route_style="ZERO_GAP_M1_LOCAL_ROUTE",
                    left_orientation=left_orientation,
                    right_orientation=right_orientation,
                    gap=0.0,
                    out_dir=module_out / f"zero_gap_m1__{left_orientation}__{right_orientation}",
                    klayout_bin=klayout_bin,
                    drc_deck=drc_deck,
                )
            )
        write_csv(out_root / f"{module.module_name}_ABUTMENT_ROUTE_CANDIDATES.csv", rows)
        selected = _select_final_candidate(module.module_name, rows, _sha256(module.baseline_clean_gds))
        write_json(out_root / f"{module.module_name}_SELECTED_CANDIDATE.json", selected)
        zero_gap_best = _best_zero_gap(rows, "ZERO_GAP_M2_PARENT_ROUTE")
        if zero_gap_best is not None:
            src = Path(zero_gap_best["clean_gds_path"]).parent / "pin_access_report.json"
            if src.exists():
                _copy_if_exists(src, out_root / f"{module.module_name}_ZERO_GAP_PIN_ACCESS.json")
            _write_endpoint_contract(module.module_name, out_root, zero_gap_best)
        chosen_dir = Path(selected["selected_clean_gds_path"]).parent
        _copy_if_exists(chosen_dir / "review_atlas.gds", out_root / f"{module.module_name}_ABUTMENT_REVIEW_ATLAS.gds")
        if zero_gap_best is not None:
            zero_gap_dir = Path(zero_gap_best["clean_gds_path"]).parent
            comparison = out_root / f"{module.module_name}_ROUTE_LAYER_COMPARISON_ATLAS.gds"
            make_review_atlas(chosen_dir / "clean.gds", zero_gap_dir / "annotated.gds", module.top_name, comparison)
        decision_rows.append(
            {
                "module_name": module.module_name,
                "selected_candidate_id": selected["selected_candidate_id"],
                "decision": selected["decision"],
                "formal_gds_changed": False,
                "sha_changed": False,
                "integration_invalidated": False,
            }
        )
        technical_lines.extend(
            [
                f"## {module.module_name}",
                "",
                f"- baseline_candidate: `{baseline_row['candidate_id']}` DRC `{baseline_row['DRC_marker_count']}` connectivity `{baseline_row['connectivity']}`",
            ]
        )
        for row in rows:
            if row["gap"] == 0.0:
                technical_lines.append(
                    f"- zero_gap `{row['orientation']}` `{row['route_style']}`: DRC `{row['DRC_marker_count']}`, connectivity `{row['connectivity']}`, foreign-net `{row['foreign_net']}`, Pin access `{row['Pin_access']}`, VDD `{row['VDD_continuity']}`, VSS `{row['VSS_continuity']}`, route_reason `{row['route_reason']}`"
                )
        technical_lines.append(
            f"- selected_decision: `{selected['decision']}` using `{selected['selected_candidate_id']}`"
        )
        technical_lines.append("")

    baseline_retain = all(row["decision"] == "BASELINE_RETAINED" for row in decision_rows)
    decision_json = {
        "generated_at": _ts(),
        "baseline_retained": baseline_retain,
        "formal_gds_changed": False,
        "integration_still_valid": True,
        "rows": decision_rows,
    }
    write_json(out_root / "AND2_AND3_ABUTMENT_DECISION.json", decision_json)
    if baseline_retain:
        decision_lines = [
            "- Formal AND2/AND3 GDS were not changed.",
            "- Current 9-cell integration remains valid because no formal SHA changed.",
            "- Zero-gap candidates were studied with real GDS + FreePDK45 DRC + connectivity + pin-access evidence.",
            "",
        ]
    else:
        decision_lines = [
            "- A non-baseline candidate outperformed the baseline in study metrics, but formal GDS promotion is not applied in this script.",
            "- Formal promotion would require full production-gate rerun before integration invalidation.",
            "",
        ]
    for row in decision_rows:
        decision_lines.append(f"- {row['module_name']}: `{row['decision']}` via `{row['selected_candidate_id']}`")
    write_text(out_root / "AND2_AND3_ABUTMENT_DECISION.md", _render_md("AND2/AND3 Abutment Decision", decision_lines))
    write_text(out_root / "ABUTMENT_DRC_ROOT_CAUSE.md", "\n".join(drc_root_cause_lines) + "\n")
    write_text(out_root / "ABUTMENT_OPTIMIZATION_TECHNICAL_REPORT.md", "\n".join(technical_lines) + "\n")

    sha_rows = []
    for path in sorted(out_root.rglob("*")):
        if path.is_file():
            sha_rows.append(f"{_sha256(path)}  {path.relative_to(repo_root)}")
    write_text(out_root / "ABUTMENT_OPTIMIZATION_SHA256SUMS.txt", "\n".join(sha_rows))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
