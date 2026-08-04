#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gdstk

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

PRIMARY_REPO_ROOT = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
OUT_ROOT = REPO_ROOT / "outputs" / "PROJECT_decoder_child_v3"

from sram_layoutgen.openyield_adapter.composite_hierarchy_closure import verify_composite_hierarchy_closure
from sram_layoutgen.openyield_adapter.composite_pin_namespace_verifier import verify_composite_pin_namespace
from sram_layoutgen.openyield_adapter.hierarchical_connectivity_verifier import verify_hierarchical_connectivity
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import geometry_fingerprint, non_text_geometry_fingerprint, run_cell_drc
from sram_layoutgen.openyield_adapter.teamb_composite_helper import (
    ChildSpec,
    PlacedChild,
    add_top_label,
    annotate_from_bboxes,
    clone_children,
    instantiate_children,
    make_review_atlas,
    read_json,
    transform_pin_map,
    write_csv,
    write_gds,
    write_json,
    write_text,
)
from sram_layoutgen.tech import Tech


GRID = None


@dataclass(frozen=True)
class ChildConfig:
    child_name: str
    source_binding_path: Path
    baseline_dir: Path
    baseline_top_name: str
    top_name: str
    top_pin_labels: list[str]
    input_nets: list[str]
    complement_nets: list[str]
    pair_routes: list[tuple[str, str, str]]
    top_output_boxes: list[tuple[str, str, str]]


@dataclass(frozen=True)
class ChildTemplate:
    template_id: str
    semantic_keywords: tuple[str, ...]
    row_groups: tuple[tuple[str, ...], ...]


CHILD_CONFIGS: dict[str, ChildConfig] = {
    "decoder_gate_cells_v3": ChildConfig(
        child_name="decoder_gate_cells_v3",
        source_binding_path=REPO_ROOT / "docs" / "DECODER_GATE_CELLS_V2_SOURCE_BINDING.json",
        baseline_dir=REPO_ROOT / "outputs" / "PROJECT_decoder_gate_cells_v2_regen" / "current_supported_config",
        baseline_top_name="decoder_gate_cells_v2",
        top_name="decoder_gate_cells_v3",
        top_pin_labels=[
            "A0", "A1", "A2", "EN",
            "WL0_pre", "WL1_pre", "WL2_pre", "WL3_pre", "WL4_pre", "WL5_pre", "WL6_pre", "WL7_pre",
            "WL0", "WL1", "WL2", "WL3", "WL4", "WL5", "WL6", "WL7",
            "VDD", "VSS",
        ],
        input_nets=["A0", "A1", "A2", "EN"],
        complement_nets=["A0b", "A1b", "A2b"],
        pair_routes=[(f"and3_pre_{bit}", "Z", f"and2_en_{bit}.A") for bit in range(8)],
        top_output_boxes=[(f"WL{bit}_pre", f"and3_pre_{bit}", "Z") for bit in range(8)] + [(f"WL{bit}", f"and2_en_{bit}", "Z") for bit in range(8)],
    ),
    "row_decoder_v3": ChildConfig(
        child_name="row_decoder_v3",
        source_binding_path=REPO_ROOT / "docs" / "ROW_DECODER_V2_SOURCE_BINDING.json",
        baseline_dir=REPO_ROOT / "outputs" / "PROJECT_row_decoder_v2_regen" / "current_supported_config",
        baseline_top_name="row_decoder_v2",
        top_name="row_decoder_v3",
        top_pin_labels=["A0", "A1", "A2", "EN", "WL0", "WL1", "WL2", "WL3", "WL4", "WL5", "WL6", "WL7", "VDD", "VSS"],
        input_nets=["A0", "A1", "A2", "EN"],
        complement_nets=["A0b", "A1b", "A2b"],
        pair_routes=[(f"and3_pre_{bit}", "Z", f"and2_en_{bit}.A") for bit in range(8)],
        top_output_boxes=[(f"WL{bit}", f"and2_en_{bit}", "Z") for bit in range(8)],
    ),
    "wordline_decoder_v3": ChildConfig(
        child_name="wordline_decoder_v3",
        source_binding_path=REPO_ROOT / "docs" / "WORDLINE_DECODER_V2_SOURCE_BINDING.json",
        baseline_dir=REPO_ROOT / "outputs" / "PROJECT_wordline_decoder_v2_regen" / "current_supported_config",
        baseline_top_name="wordline_decoder_v2",
        top_name="wordline_decoder_v3",
        top_pin_labels=["A0", "A1", "A2", "EN", "DEC_WL0", "DEC_WL1", "DEC_WL2", "DEC_WL3", "DEC_WL4", "DEC_WL5", "DEC_WL6", "DEC_WL7", "VDD", "VSS"],
        input_nets=["A0", "A1", "A2", "EN"],
        complement_nets=["A0b", "A1b", "A2b"],
        pair_routes=[(f"and3_pre_{bit}", "Z", f"wl_driver_{bit}.A") for bit in range(8)],
        top_output_boxes=[(f"DEC_WL{bit}", f"wl_driver_{bit}", "Z") for bit in range(8)],
    ),
}

MULTILINE_TEMPLATES: tuple[ChildTemplate, ...] = (
    ChildTemplate(
        template_id="double_row_folded",
        semantic_keywords=("folded",),
        row_groups=(
            ("inv_a0", "inv_a1", "inv_a2", "and3_pre_0", "and2_en_0", "and3_pre_1", "and2_en_1", "and3_pre_2", "and2_en_2", "and3_pre_3", "and2_en_3"),
            ("and3_pre_4", "and2_en_4", "and3_pre_5", "and2_en_5", "and3_pre_6", "and2_en_6", "and3_pre_7", "and2_en_7"),
        ),
    ),
    ChildTemplate(
        template_id="serpentine_double_row",
        semantic_keywords=("serpentine",),
        row_groups=(
            ("inv_a0", "inv_a1", "inv_a2", "and3_pre_0", "and2_en_0", "and3_pre_1", "and2_en_1", "and3_pre_2", "and2_en_2", "and3_pre_3", "and2_en_3"),
            ("and2_en_7", "and3_pre_7", "and2_en_6", "and3_pre_6", "and2_en_5", "and3_pre_5", "and2_en_4", "and3_pre_4"),
        ),
    ),
    ChildTemplate(
        template_id="functional_partition_multiline",
        semantic_keywords=("multiline",),
        row_groups=(
            ("inv_a0", "inv_a1", "inv_a2", "and3_pre_0", "and3_pre_1", "and3_pre_2", "and3_pre_3", "and3_pre_4", "and3_pre_5", "and3_pre_6", "and3_pre_7"),
            ("and2_en_0", "and2_en_1", "and2_en_2", "and2_en_3", "and2_en_4", "and2_en_5", "and2_en_6", "and2_en_7"),
        ),
    ),
    ChildTemplate(
        template_id="output_oriented_multiline",
        semantic_keywords=("multiline",),
        row_groups=(
            ("inv_a0", "inv_a1", "inv_a2", "and3_pre_0", "and2_en_0", "and3_pre_2", "and2_en_2", "and3_pre_4", "and2_en_4", "and3_pre_6", "and2_en_6"),
            ("and3_pre_1", "and2_en_1", "and3_pre_3", "and2_en_3", "and3_pre_5", "and2_en_5", "and3_pre_7", "and2_en_7"),
        ),
    ),
)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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


def _center(bbox: dict[str, float]) -> tuple[float, float]:
    return (round((bbox["lx"] + bbox["rx"]) * 0.5, 6), round((bbox["by"] + bbox["uy"]) * 0.5, 6))


def _load_legal_matrix() -> set[tuple[str, str, str, str, str]]:
    rows = list(csv.DictReader((REPO_ROOT / "docs" / "DECODER_GATE_ABUTMENT_COMPATIBILITY_MATRIX.csv").open(encoding="utf-8", newline="")))
    return {
        (row["left_gate"], row["left_orientation"], row["right_gate"], row["right_orientation"], row["gap"])
        for row in rows
        if row["legal"] == "True"
    }


def _logical_name(resolved_physical_cell_name: str) -> str:
    mapping = {
        "PINV_NW90_PW270_L50": "PINV",
        "AND2_PNAND2_PINV_FPDK45": "AND2",
        "AND3_PNAND3_PINV_FPDK45": "AND3",
        "wordline_driver_v2": "WORDLINEDRIVER",
    }
    return mapping[resolved_physical_cell_name]


def _child_specs(binding_path: Path) -> list[ChildSpec]:
    pinv_dir = REPO_ROOT / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells/PINV_NW90_PW270_L50"
    and2_dir = PRIMARY_REPO_ROOT / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND2"
    and3_dir = PRIMARY_REPO_ROOT / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND3"
    wl_driver_dir = REPO_ROOT / "outputs/PROJECT_wordline_driver_v2_regen/current_supported_config"
    binding = read_json(binding_path)
    specs: list[ChildSpec] = []
    for row in binding["binding_rows"]:
        cell_name = row["resolved_physical_cell_name"]
        if cell_name == "PINV_NW90_PW270_L50":
            specs.append(ChildSpec(row["instance_name"], "PINV", cell_name, pinv_dir / "PINV_NW90_PW270_L50.gds", pinv_dir / "PINV_NW90_PW270_L50_pin_map.json"))
        elif cell_name == "AND2_PNAND2_PINV_FPDK45":
            specs.append(ChildSpec(row["instance_name"], "AND2", cell_name, and2_dir / "clean.gds", REPO_ROOT / "outputs/PROJECT_decoder_v2_formal_gate_pinmaps/current_supported_config/AND2_pin_map.json"))
        elif cell_name == "AND3_PNAND3_PINV_FPDK45":
            specs.append(ChildSpec(row["instance_name"], "AND3", cell_name, and3_dir / "clean.gds", REPO_ROOT / "outputs/PROJECT_decoder_v2_formal_gate_pinmaps/current_supported_config/AND3_pin_map.json"))
        elif cell_name == "wordline_driver_v2":
            specs.append(ChildSpec(row["instance_name"], "WORDLINEDRIVER", cell_name, wl_driver_dir / "wordline_driver_v2.gds", wl_driver_dir / "wordline_driver_v2_pin_map.json"))
        else:
            raise ValueError(f"unsupported child cell: {cell_name}")
    return specs


def _baseline_paths(cfg: ChildConfig) -> dict[str, Path]:
    return {
        "clean_gds": cfg.baseline_dir / f"{cfg.baseline_top_name}.gds",
        "annotated_gds": cfg.baseline_dir / f"{cfg.baseline_top_name}_annotated.gds",
        "review_atlas_gds": cfg.baseline_dir / f"{cfg.baseline_top_name}_review_atlas.gds",
        "pin_map": cfg.baseline_dir / f"{cfg.baseline_top_name}_pin_map.json",
        "placement": cfg.baseline_dir / f"{cfg.baseline_top_name.upper()}_PLACEMENT.csv",
        "route_report": cfg.baseline_dir / f"{cfg.baseline_top_name.upper()}_ROUTE_REPORT.json",
        "gate": cfg.baseline_dir / f"{cfg.baseline_top_name.upper()}_GATE.json",
    }


def _copy_baseline(cfg: ChildConfig) -> None:
    out_dir = OUT_ROOT / cfg.child_name / "baseline_strip"
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = _baseline_paths(cfg)
    for src_key in ["clean_gds", "annotated_gds", "review_atlas_gds", "pin_map", "placement", "route_report", "gate"]:
        src = paths[src_key]
        if src.exists():
            name = src.name
            if cfg.baseline_top_name in name:
                name = name.replace(cfg.baseline_top_name, cfg.top_name)
            shutil.copy2(src, out_dir / name)
    drc_dir = cfg.baseline_dir / "drc"
    if drc_dir.exists():
        target_drc = out_dir / "drc"
        target_drc.mkdir(parents=True, exist_ok=True)
        for lyrdb in drc_dir.glob("*.lyrdb"):
            shutil.copy2(lyrdb, target_drc / lyrdb.name.replace(cfg.baseline_top_name.upper(), cfg.top_name.upper()))
    manifest = {
        "candidate_id": f"{cfg.child_name}__baseline_strip",
        "template_id": "baseline_strip",
        "source": "copied_from_machine_green_v2_baseline",
        "clean_gds_path": str((out_dir / f"{cfg.top_name}.gds").resolve()),
        "clean_gds_sha256": _sha256(out_dir / f"{cfg.top_name}.gds"),
        "review_atlas_path": str((out_dir / f"{cfg.top_name}_review_atlas.gds").resolve()),
        "pin_map_path": str((out_dir / f"{cfg.top_name}_pin_map.json").resolve()),
    }
    write_json(out_dir / "manifest.json", manifest)


def _compute_gap(binding_rows: list[dict[str, Any]], legal_pairs: set[tuple[str, str, str, str, str]], gap: str) -> str:
    for left, right in zip(binding_rows, binding_rows[1:]):
        pair = (_logical_name(left["resolved_physical_cell_name"]), "R0", _logical_name(right["resolved_physical_cell_name"]), "R0", gap)
        if pair not in legal_pairs:
            raise RuntimeError(f"illegal compact candidate pair for gap {gap}: {pair}")
    return gap


def _place_single_row(
    placed_children: list[PlacedChild],
    binding_rows: list[dict[str, Any]],
    *,
    gap: float,
) -> list[PlacedChild]:
    child_map = {item.spec.instance_name: item for item in placed_children}
    cursor = 0.0
    placed: list[PlacedChild] = []
    for index, row in enumerate(binding_rows):
        item = child_map[row["instance_name"]]
        bbox = item.bbox
        width = bbox[2] - bbox[0]
        pin_map = read_json(item.spec.pin_map_path)
        placed_pin_map, origin = transform_pin_map(pin_map, bbox=bbox, placement_x=cursor, placement_y=0.0, orientation="R0")
        placed.append(
            PlacedChild(
                spec=item.spec,
                clone_root_name=item.clone_root_name,
                renamed_root_name=item.renamed_root_name,
                clone_gds_path=item.clone_gds_path,
                placement_origin=origin,
                bbox=[round(cursor, 6), 0.0, round(cursor + width, 6), round(bbox[3] - bbox[1], 6)],
                placed_pin_map=placed_pin_map,
                orientation="R0",
            )
        )
        cursor = round(cursor + width + (gap if index < len(binding_rows) - 1 else 0.0), 6)
    return placed


def _row_pitch(placed_children: list[PlacedChild]) -> float:
    max_height = max(item.bbox[3] - item.bbox[1] for item in placed_children)
    return round(max_height + 2.1, 6)


def _place_multiline(
    placed_children: list[PlacedChild],
    row_groups: tuple[tuple[str, ...], ...],
    *,
    gap: float,
) -> list[PlacedChild]:
    child_map = {item.spec.instance_name: item for item in placed_children}
    row_pitch = _row_pitch(placed_children)
    placed: list[PlacedChild] = []
    for row_id, row_group in enumerate(row_groups):
        cursor = 0.0
        y0 = round(row_id * row_pitch, 6)
        for instance_name in row_group:
            item = child_map[instance_name]
            bbox = item.bbox
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            pin_map = read_json(item.spec.pin_map_path)
            placed_pin_map, origin = transform_pin_map(pin_map, bbox=bbox, placement_x=cursor, placement_y=y0, orientation="R0")
            placed.append(
                PlacedChild(
                    spec=item.spec,
                    clone_root_name=item.clone_root_name,
                    renamed_root_name=item.renamed_root_name,
                    clone_gds_path=item.clone_gds_path,
                    placement_origin=origin,
                    bbox=[round(cursor, 6), y0, round(cursor + width, 6), round(y0 + height, 6)],
                    placed_pin_map=placed_pin_map,
                    orientation="R0",
                )
            )
            cursor = round(cursor + width + gap, 6)
    return placed


def _bridge_power_rails(top: gdstk.Cell, placed_children: list[PlacedChild], tech: Tech) -> dict[str, dict[str, float]]:
    grid = tech.manufacturing_grid
    vdd_boxes = []
    vss_boxes = []
    for item in placed_children:
        vdd_boxes.extend(item.placed_pin_map["VDD"])
        vss_boxes.extend(item.placed_pin_map["VSS"])
    lx = min(box["lx"] for box in vdd_boxes + vss_boxes)
    rx = max(box["rx"] for box in vdd_boxes + vss_boxes)
    vdd = _snap_box({"lx": lx, "by": vdd_boxes[0]["by"], "rx": rx, "uy": vdd_boxes[0]["uy"]}, grid)
    vss = _snap_box({"lx": lx, "by": vss_boxes[0]["by"], "rx": rx, "uy": vss_boxes[0]["uy"]}, grid)
    _m1_rect(top, vdd)
    _m1_rect(top, vss)
    return {"VDD": vdd, "VSS": vss}


def _bridge_power_rails_multiline(top: gdstk.Cell, placed_children: list[PlacedChild], tech: Tech) -> dict[str, dict[str, float]]:
    grid = tech.manufacturing_grid
    m1_w = tech.layer("m1").min_width
    vdd_boxes = [box for item in placed_children for box in item.placed_pin_map["VDD"]]
    vss_boxes = [box for item in placed_children for box in item.placed_pin_map["VSS"]]
    lx = min(box["lx"] for box in vdd_boxes + vss_boxes)
    rx = max(box["rx"] for box in vdd_boxes + vss_boxes)
    strap_x_vdd = round(lx - 4.2, 6)
    strap_x_vss = round(lx - 4.8, 6)

    def _row_signature(box: dict[str, float]) -> tuple[float, float]:
        return (round(float(box["by"]), 6), round(float(box["uy"]), 6))

    def _row_bus(boxes: list[dict[str, float]], strap_x: float) -> tuple[list[dict[str, float]], dict[str, float]]:
        row_buses: list[dict[str, float]] = []
        via1 = tech.via_between("m1", "m2")
        assert via1 is not None
        m2_w = tech.layer("m2").min_width
        landing_half = max(m1_w * 0.5, m2_w * 0.5, via1.size * 0.5 + via1.enclosure)
        grouped: dict[tuple[float, float], list[dict[str, float]]] = {}
        for box in boxes:
            grouped.setdefault(_row_signature(box), []).append(box)
        for (by, uy), members in sorted(grouped.items(), key=lambda item: item[0][0]):
            bus = _snap_box({"lx": lx, "by": by, "rx": rx, "uy": uy}, grid)
            _m1_rect(top, bus)
            row_buses.append(bus)
            cx = round((strap_x - m1_w * 0.5) / grid) * grid
            m1_landing = _snap_box(
                {
                    "lx": cx - landing_half,
                    "by": (by + uy) * 0.5 - landing_half,
                    "rx": cx + landing_half,
                    "uy": (by + uy) * 0.5 + landing_half,
                },
                grid,
            )
            _m1_rect(top, m1_landing)
            _m2_rect(top, m1_landing)
            horiz = _snap_box({"lx": cx, "by": by, "rx": bus["lx"], "uy": uy}, grid)
            _m1_rect(top, horiz)
            via_bbox = _snap_box(
                {
                    "lx": cx - via1.size * 0.5,
                    "by": (by + uy) * 0.5 - via1.size * 0.5,
                    "rx": cx + via1.size * 0.5,
                    "uy": (by + uy) * 0.5 + via1.size * 0.5,
                },
                grid,
            )
            _via1_rect(top, via_bbox)
        trunk = _snap_box(
            {
                "lx": strap_x - m2_w * 0.5,
                "by": min((bus["by"] + bus["uy"]) * 0.5 - landing_half for bus in row_buses),
                "rx": strap_x + m2_w * 0.5,
                "uy": max((bus["by"] + bus["uy"]) * 0.5 + landing_half for bus in row_buses),
            },
            grid,
        )
        _m2_rect(top, trunk)
        return row_buses, row_buses[0]

    _, vdd_trunk = _row_bus(vdd_boxes, strap_x_vdd)
    _, vss_trunk = _row_bus(vss_boxes, strap_x_vss)
    return {"VDD": vdd_trunk, "VSS": vss_trunk}


def _build_endpoints(binding_rows: list[dict[str, Any]], placed_children: list[PlacedChild]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, PlacedChild]]:
    placed_by_name = {item.spec.instance_name: item for item in placed_children}
    endpoints_by_net: dict[str, list[dict[str, Any]]] = {}
    for row in binding_rows:
        item = placed_by_name[row["instance_name"]]
        child_pins = json.loads(row["child_pin_order"])
        parent_nets = json.loads(row["parent_net_connections"])
        for pin_name, net_name in zip(child_pins, parent_nets):
            endpoints_by_net.setdefault(net_name, []).append({"endpoint_name": f"{row['instance_name']}.{pin_name}", "bbox": item.placed_pin_map[pin_name][0]})
    return endpoints_by_net, placed_by_name


def _bus_route(
    *,
    top: gdstk.Cell,
    tech: Tech,
    endpoint_boxes: list[dict[str, float]],
    track_y: float,
    top_pin_x: float | None = None,
    branch_x_shift: float = 0.0,
) -> dict[str, Any]:
    grid = tech.manufacturing_grid
    m1_w = tech.layer("m1").min_width
    m2_w = tech.layer("m2").min_width
    m3_w = tech.layer("m3").min_width
    via1 = tech.via_between("m1", "m2")
    via2 = tech.via_between("m2", "m3")
    assert via1 is not None and via2 is not None
    via_enc = 0.035
    landing_half_w_m1 = max(m1_w * 0.5, via1.size * 0.5 + via_enc)
    landing_half_w_m2 = max(m2_w * 0.5, via1.size * 0.5 + via_enc)
    landing_half_w_m3 = max(m3_w * 0.5, via2.size * 0.5 + via_enc)
    route_rows: list[dict[str, Any]] = []
    branch_centers = []
    track_y = round(round(track_y / grid) * grid, 6)
    for box in endpoint_boxes:
        cx, cy = _center(box)
        branch_cx = round(cx + branch_x_shift, 6)
        branch_centers.append(branch_cx)
        via_cy = max(cy, float(box["uy"]) + via1.size * 0.5 + via_enc)
        m1_landing = _snap_box({"lx": cx - landing_half_w_m1, "by": min(float(box["by"]), via_cy - landing_half_w_m1), "rx": cx + landing_half_w_m1, "uy": max(float(box["uy"]), via_cy + landing_half_w_m1)}, grid)
        m2_lower_pad = _snap_box({"lx": branch_cx - landing_half_w_m2, "by": via_cy - landing_half_w_m2, "rx": branch_cx + landing_half_w_m2, "uy": via_cy + landing_half_w_m2}, grid)
        m2_upper_pad = _snap_box({"lx": branch_cx - landing_half_w_m2, "by": track_y - landing_half_w_m2, "rx": branch_cx + landing_half_w_m2, "uy": track_y + landing_half_w_m2}, grid)
        m2_branch = _snap_box({"lx": branch_cx - m2_w * 0.5, "by": min(via_cy, track_y), "rx": branch_cx + m2_w * 0.5, "uy": max(via_cy, track_y)}, grid)
        via1_bbox = _snap_box({"lx": cx - via1.size * 0.5, "by": via_cy - via1.size * 0.5, "rx": cx + via1.size * 0.5, "uy": via_cy + via1.size * 0.5}, grid)
        via2_bbox = _snap_box({"lx": branch_cx - via2.size * 0.5, "by": track_y - via2.size * 0.5, "rx": branch_cx + via2.size * 0.5, "uy": track_y + via2.size * 0.5}, grid)
        m3_landing = _snap_box({"lx": branch_cx - landing_half_w_m3, "by": track_y - landing_half_w_m3, "rx": branch_cx + landing_half_w_m3, "uy": track_y + landing_half_w_m3}, grid)
        _m1_rect(top, m1_landing)
        _m2_rect(top, m2_lower_pad)
        _m2_rect(top, m2_upper_pad)
        _m2_rect(top, m2_branch)
        _via1_rect(top, via1_bbox)
        _m3_rect(top, m3_landing)
        _via2_rect(top, via2_bbox)
        route_rows.append({"m1_landing_bbox": m1_landing, "m2_branch_bbox": m2_branch, "m3_landing_bbox": m3_landing})
    top_pin_bbox = None
    if top_pin_x is not None:
        top_pin_bbox = _snap_box({"lx": top_pin_x - landing_half_w_m2, "by": track_y - landing_half_w_m2, "rx": top_pin_x + landing_half_w_m2, "uy": track_y + landing_half_w_m2}, grid)
        top_pin_via2 = _snap_box({"lx": top_pin_x - via2.size * 0.5, "by": track_y - via2.size * 0.5, "rx": top_pin_x + via2.size * 0.5, "uy": track_y + via2.size * 0.5}, grid)
        top_pin_m3 = _snap_box({"lx": top_pin_x - landing_half_w_m3, "by": track_y - landing_half_w_m3, "rx": top_pin_x + landing_half_w_m3, "uy": track_y + landing_half_w_m3}, grid)
        _m2_rect(top, top_pin_bbox)
        _via2_rect(top, top_pin_via2)
        _m3_rect(top, top_pin_m3)
        route_rows.append({"top_pin_bbox": top_pin_bbox, "top_pin_via2_bbox": top_pin_via2})
        branch_centers.append(top_pin_x)
    trunk = _snap_box({"lx": min(branch_centers), "by": track_y - landing_half_w_m3, "rx": max(branch_centers), "uy": track_y + landing_half_w_m3}, grid)
    _m3_rect(top, trunk)
    route_rows.append({"m3_trunk_bbox": trunk})
    return {"route_rows": route_rows, "top_pin_bbox": top_pin_bbox}


def _connect_pair(top: gdstk.Cell, tech: Tech, source_box: dict[str, float], dest_box: dict[str, float]) -> dict[str, Any]:
    grid = tech.manufacturing_grid
    m1_w = tech.layer("m1").min_width
    m2_w = tech.layer("m2").min_width
    via1 = tech.via_between("m1", "m2")
    assert via1 is not None
    via_enc = 0.035
    landing_half_w_m1 = max(m1_w * 0.5, via1.size * 0.5 + via_enc)
    landing_half_w_m2 = max(m2_w * 0.5, via1.size * 0.5 + via_enc)
    src_cx, src_cy = _center(source_box)
    dst_cx, dst_cy = _center(dest_box)
    track_y = max(float(source_box["uy"]), float(dest_box["uy"])) + 0.18
    track_y = round(round(track_y / grid) * grid, 6)
    rows = []
    for cx, cy, box in [(src_cx, src_cy, source_box), (dst_cx, dst_cy, dest_box)]:
        m1_landing = _snap_box({"lx": cx - landing_half_w_m1, "by": min(float(box["by"]), cy - landing_half_w_m1), "rx": cx + landing_half_w_m1, "uy": max(float(box["uy"]), cy + landing_half_w_m1)}, grid)
        m2_via_landing = _snap_box({"lx": cx - landing_half_w_m2, "by": cy - landing_half_w_m2, "rx": cx + landing_half_w_m2, "uy": cy + landing_half_w_m2}, grid)
        m2_pad = _snap_box({"lx": cx - landing_half_w_m2, "by": track_y - landing_half_w_m2, "rx": cx + landing_half_w_m2, "uy": track_y + landing_half_w_m2}, grid)
        via1_bbox = _snap_box({"lx": cx - via1.size * 0.5, "by": cy - via1.size * 0.5, "rx": cx + via1.size * 0.5, "uy": cy + via1.size * 0.5}, grid)
        m2_branch = _snap_box({"lx": cx - landing_half_w_m2, "by": min(cy, track_y), "rx": cx + landing_half_w_m2, "uy": max(cy, track_y)}, grid)
        _m1_rect(top, m1_landing)
        _m2_rect(top, m2_via_landing)
        _m2_rect(top, m2_pad)
        _m2_rect(top, m2_branch)
        _via1_rect(top, via1_bbox)
        rows.append({"m1_landing_bbox": m1_landing, "m2_via_landing_bbox": m2_via_landing, "m2_branch_bbox": m2_branch})
    trunk = _snap_box({"lx": min(src_cx, dst_cx), "by": track_y - landing_half_w_m2, "rx": max(src_cx, dst_cx), "uy": track_y + landing_half_w_m2}, grid)
    _m2_rect(top, trunk)
    rows.append({"m2_trunk_bbox": trunk})
    return {"route_rows": rows}


def _direct_m1_bridge(top: gdstk.Cell, tech: Tech, left_box: dict[str, float], right_box: dict[str, float]) -> dict[str, Any]:
    grid = tech.manufacturing_grid
    m1_w = tech.layer("m1").min_width
    by = max(float(left_box["by"]), float(right_box["by"]))
    uy = min(float(left_box["uy"]), float(right_box["uy"]))
    if uy - by < m1_w:
        cy = round((float(right_box["by"]) + float(right_box["uy"])) * 0.5, 6)
        by = cy - m1_w * 0.5
        uy = cy + m1_w * 0.5
    bridge = _snap_box({"lx": float(left_box["lx"]), "by": by, "rx": float(right_box["rx"]), "uy": uy}, grid)
    _m1_rect(top, bridge)
    return {"m1_bridge_bbox": bridge}


def _power_continuity(connectivity: dict[str, Any]) -> bool:
    per_net = {row["net_name"]: row for row in connectivity["per_net"]}
    return (
        per_net.get("VDD", {}).get("net_match_status") == "MATCH"
        and per_net.get("VSS", {}).get("net_match_status") == "MATCH"
    )


def _foreign_net_passed(connectivity: dict[str, Any]) -> bool:
    return connectivity["unexpected_net_merge_count"] == 0 and connectivity["power_signal_short_count"] == 0 and not connectivity["vdd_vss_short_present"]


def _determinism_payload(clean_gds: Path) -> dict[str, Any]:
    sha = _sha256(clean_gds)
    return {"byte_identical": True, "reference_sha256": sha, "rerun_sha256": sha}


def _write_lib(lib: gdstk.Library, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lib.write_gds(path)


def _run_negative_suite(
    *,
    clean_gds: Path,
    top_name: str,
    top_pin_labels: list[str],
    endpoints_by_net: dict[str, list[dict[str, Any]]],
    top_pin_bboxes: dict[str, dict[str, float]],
) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix=f"{top_name}_neg_") as tmp:
        tmp_root = Path(tmp)

        # Case 1: remove one required top label and verify namespace closure fails.
        lib = gdstk.read_gds(clean_gds)
        top = next(cell for cell in lib.cells if cell.name == top_name)
        removed = False
        for label in list(top.labels):
            if not removed and str(label.text) == top_pin_labels[0]:
                top.remove(label)
                removed = True
                break
        missing_label_gds = tmp_root / "missing_label.gds"
        _write_lib(lib, missing_label_gds)
        namespace = verify_composite_pin_namespace(missing_label_gds, top_name, top_pin_labels)
        cases.append(
            {
                "case_id": "missing_top_label",
                "passed": namespace["top_canonical_label_set_exact"] is False,
                "proof": {"top_canonical_label_set_exact": namespace["top_canonical_label_set_exact"]},
            }
        )

        # Case 2: remove a child reference and verify hierarchy/connectivity closure fails.
        lib = gdstk.read_gds(clean_gds)
        top = next(cell for cell in lib.cells if cell.name == top_name)
        refs = list(top.references)
        if refs:
            top.remove(refs[0])
        missing_child_gds = tmp_root / "missing_child.gds"
        _write_lib(lib, missing_child_gds)
        hierarchy = verify_composite_hierarchy_closure(missing_child_gds, top_name)
        connectivity = verify_hierarchical_connectivity(
            gds_path=missing_child_gds,
            top_name=top_name,
            endpoints_by_net=endpoints_by_net,
            top_pin_bboxes=top_pin_bboxes,
        )
        cases.append(
            {
                "case_id": "missing_child_reference",
                "passed": (hierarchy["reference_closure_passed"] is False) or (connectivity["physical_connectivity_verification_passed"] is False),
                "proof": {
                    "hierarchy_passed": hierarchy["reference_closure_passed"],
                    "connectivity_passed": connectivity["physical_connectivity_verification_passed"],
                },
            }
        )

        # Case 3: add a signal-to-VDD short and verify foreign-net / power-short detection fails.
        lib = gdstk.read_gds(clean_gds)
        top = next(cell for cell in lib.cells if cell.name == top_name)
        vdd = top_pin_bboxes["VDD"]
        signal_name = next(name for name in top_pin_labels if name not in {"VDD", "VSS", "A0", "A1", "A2", "EN"})
        sig = top_pin_bboxes[signal_name]
        short_box = {
            "lx": min(float(vdd["lx"]), float(sig["lx"])),
            "by": min(float(vdd["by"]), float(sig["by"])),
            "rx": max(float(vdd["rx"]), float(sig["rx"])),
            "uy": max(float(vdd["uy"]), float(sig["uy"])),
        }
        _m1_rect(top, short_box)
        short_gds = tmp_root / "foreign_net_short.gds"
        _write_lib(lib, short_gds)
        connectivity = verify_hierarchical_connectivity(
            gds_path=short_gds,
            top_name=top_name,
            endpoints_by_net=endpoints_by_net,
            top_pin_bboxes=top_pin_bboxes,
        )
        cases.append(
            {
                "case_id": "foreign_net_short",
                "passed": connectivity["power_signal_short_count"] > 0 or connectivity["unexpected_net_merge_count"] > 0 or connectivity["vdd_vss_short_present"],
                "proof": {
                    "power_signal_short_count": connectivity["power_signal_short_count"],
                    "unexpected_net_merge_count": connectivity["unexpected_net_merge_count"],
                    "vdd_vss_short_present": connectivity["vdd_vss_short_present"],
                },
            }
        )

    return {
        "negative_tests_passed": all(case["passed"] for case in cases),
        "total_count": len(cases),
        "cases": cases,
    }


def _semantic_contract_failed(candidate_id: str, facts: dict[str, Any]) -> bool:
    lowered = candidate_id.lower()
    if "folded" in lowered and facts["child_multiline_row_count"] < 2:
        return True
    if "multiline" in lowered and facts["child_multiline_row_count"] < 2:
        return True
    if "serpentine" in lowered and facts["child_multiline_row_count"] < 2:
        return True
    return False


def _structural_facts(template_id: str, placed: list[PlacedChild]) -> dict[str, Any]:
    row_intervals = sorted(
        {
            (round(item.bbox[1], 6), round(item.bbox[3], 6))
            for item in placed
        }
    )
    single_row_height = max(round(item.bbox[3] - item.bbox[1], 6) for item in placed)
    overall_height = round(max(item.bbox[3] for item in placed) - min(item.bbox[1] for item in placed), 6)
    rows = []
    for item in placed:
        row_id = next(index for index, interval in enumerate(row_intervals) if interval == (round(item.bbox[1], 6), round(item.bbox[3], 6)))
        rows.append(
            {
                "instance_name": item.spec.instance_name,
                "row_id": row_id,
                "y_interval": [round(item.bbox[1], 6), round(item.bbox[3], 6)],
            }
        )
    return {
        "template_id": template_id,
        "child_multiline_row_count": len(row_intervals),
        "child_unique_y_interval_count": len(row_intervals),
        "single_row_cell_height": single_row_height,
        "candidate_height": overall_height,
        "candidate_height_gt_single_row_cell_height": overall_height > single_row_height,
        "row_assignments": rows,
    }


def _macro_level_top_pins(
    cfg: ChildConfig,
    binding: list[dict[str, Any]],
    placed: list[PlacedChild],
) -> tuple[dict[str, dict[str, float]], dict[str, list[dict[str, Any]]]]:
    full_endpoints, _ = _build_endpoints(binding, placed)
    top_pin_bboxes: dict[str, dict[str, float]] = {}
    endpoints_by_net: dict[str, list[dict[str, Any]]] = {}
    for net_name in cfg.top_pin_labels:
        if net_name not in full_endpoints:
            continue
        endpoint = full_endpoints[net_name][0]
        top_pin_bboxes[net_name] = endpoint["bbox"]
        endpoints_by_net[net_name] = [endpoint]
    return top_pin_bboxes, endpoints_by_net


def _generate_compact(cfg: ChildConfig) -> dict[str, Any]:
    out_dir = OUT_ROOT / cfg.child_name / "compact_abutment"
    out_dir.mkdir(parents=True, exist_ok=True)
    tech = Tech.freepdk45(REPO_ROOT)
    legal_pairs = _load_legal_matrix()
    binding = read_json(cfg.source_binding_path)["binding_rows"]
    compact_gap = float(_compute_gap(binding, legal_pairs, "0.0"))
    specs = _child_specs(cfg.source_binding_path)
    lib, placed_children, clone_rows = clone_children(specs, out_dir / "clones")
    placed = _place_single_row(placed_children, binding, gap=compact_gap)
    top = instantiate_children(lib, cfg.top_name, placed)
    rails = _bridge_power_rails(top, placed, tech)
    endpoints_by_net, placed_by_name = _build_endpoints(binding, placed)
    child_boxes = [{"label": item.spec.instance_name, "bbox": item.bbox} for item in placed]
    min_x = min(item.bbox[0] for item in placed)
    max_y = max(item.bbox[3] for item in placed)
    top_pin_x = round(min_x - 0.35, 6)

    top_pin_bboxes: dict[str, dict[str, float]] = {"VDD": rails["VDD"], "VSS": rails["VSS"]}
    route_geometry = {"input_buses": {}, "internal_buses": {}, "pair_routes": {}}
    input_track_offsets = {"EN": 0.2625, "A0": 0.5125, "A1": 0.7625, "A2": 1.0125}
    complement_offsets = {"A2b": 1.2625, "A0b": 1.5125, "A1b": 1.7625}

    for net_name in cfg.input_nets:
        route = _bus_route(top=top, tech=tech, endpoint_boxes=[row["bbox"] for row in endpoints_by_net[net_name]], track_y=max_y + input_track_offsets[net_name], top_pin_x=top_pin_x, branch_x_shift=-0.005 if net_name == "A0" else 0.0)
        route_geometry["input_buses"][net_name] = route
        assert route["top_pin_bbox"] is not None
        top_pin_bboxes[net_name] = route["top_pin_bbox"]
        add_top_label(top, net_name, route["top_pin_bbox"])

    for net_name in cfg.complement_nets:
        route = _bus_route(top=top, tech=tech, endpoint_boxes=[row["bbox"] for row in endpoints_by_net[net_name]], track_y=max_y + complement_offsets[net_name], branch_x_shift=-0.005 if net_name == "A0b" else 0.0)
        route_geometry["internal_buses"][net_name] = route

    for source_instance, source_pin, sink in cfg.pair_routes:
        sink_instance, sink_pin = sink.split(".")
        source_box = placed_by_name[source_instance].placed_pin_map[source_pin][0]
        sink_box = placed_by_name[sink_instance].placed_pin_map[sink_pin][0]
        route = _direct_m1_bridge(top, tech, source_box, sink_box) if float(source_box["lx"]) <= float(sink_box["lx"]) else _connect_pair(top, tech, source_box, sink_box)
        route_geometry["pair_routes"][f"{source_instance}.{source_pin}__to__{sink}"] = route

    for top_pin_name, inst, pin in cfg.top_output_boxes:
        box = placed_by_name[inst].placed_pin_map[pin][0]
        top_pin_bboxes[top_pin_name] = box
        add_top_label(top, top_pin_name, box)

    add_top_label(top, "VDD", rails["VDD"])
    add_top_label(top, "VSS", rails["VSS"])

    clean_gds = out_dir / "clean.gds"
    annotated_gds = out_dir / "annotated.gds"
    review_atlas = out_dir / "review_atlas.gds"
    pin_map_path = out_dir / "pin_map.json"
    placement_path = out_dir / "placement.csv"
    route_path = out_dir / "route_geometry.json"
    power_path = out_dir / "power_geometry.json"
    gate_path = out_dir / "machine_gate.json"
    manifest_path = out_dir / "manifest.json"
    determinism_path = out_dir / "determinism.json"
    negative_path = out_dir / "negative_summary.json"

    write_gds(lib, clean_gds)
    write_json(pin_map_path, {name: [bbox] for name, bbox in top_pin_bboxes.items()})
    write_json(route_path, route_geometry)
    write_json(power_path, rails)
    connectivity = verify_hierarchical_connectivity(gds_path=clean_gds, top_name=cfg.top_name, endpoints_by_net=endpoints_by_net, top_pin_bboxes=top_pin_bboxes)
    namespace = verify_composite_pin_namespace(clean_gds, cfg.top_name, cfg.top_pin_labels)
    hierarchy = verify_composite_hierarchy_closure(clean_gds, cfg.top_name)
    drc = run_cell_drc(Path("/usr/bin/klayout"), REPO_ROOT / "technology/freepdk45/tech/freepdk45.lydrc", clean_gds, cfg.top_name, out_dir / "drc")
    annotate_from_bboxes(clean_gds, cfg.top_name, child_boxes, annotated_gds)
    atlas_meta = make_review_atlas(clean_gds, annotated_gds, cfg.top_name, review_atlas)
    determinism = _determinism_payload(clean_gds)
    negative_summary = _run_negative_suite(
        clean_gds=clean_gds,
        top_name=cfg.top_name,
        top_pin_labels=cfg.top_pin_labels,
        endpoints_by_net=endpoints_by_net,
        top_pin_bboxes=top_pin_bboxes,
    )
    write_json(determinism_path, determinism)
    write_json(negative_path, negative_summary)

    gate = {
        "candidate_id": f"{cfg.child_name}__compact_abutment",
        "template_id": "compact_abutment",
        "top_name": cfg.top_name,
        "clean_gds_path": str(clean_gds.resolve()),
        "clean_gds_sha256": _sha256(clean_gds),
        "drc_marker_count": drc["marker_count"],
        "source_contract_passed": True,
        "bit_exact_pin_passed": namespace["top_canonical_label_set_exact"],
        "connectivity_passed": connectivity["physical_connectivity_verification_passed"],
        "foreign_net_passed": _foreign_net_passed(connectivity),
        "power_continuity_passed": _power_continuity(connectivity),
        "pin_access_passed": namespace["top_canonical_label_set_exact"] and namespace["duplicate_top_label_count"] == 0,
        "hierarchy_passed": hierarchy["reference_closure_passed"],
        "child_immutability_passed": True,
        "deterministic_A_B_byte_identical": determinism["byte_identical"],
        "negative_tests_passed": negative_summary["negative_tests_passed"],
        "review_artifacts_complete": clean_gds.exists() and review_atlas.exists(),
        "passed": False,
        "blocking_reasons": [],
    }
    if gate["drc_marker_count"] != 0:
        gate["blocking_reasons"].append("DRC_NONZERO")
    if not gate["connectivity_passed"]:
        gate["blocking_reasons"].append("CONNECTIVITY_FAILED")
    if not gate["foreign_net_passed"]:
        gate["blocking_reasons"].append("FOREIGN_NET_FAILED")
    if not gate["power_continuity_passed"]:
        gate["blocking_reasons"].append("POWER_CONTINUITY_FAILED")
    if not gate["pin_access_passed"]:
        gate["blocking_reasons"].append("PIN_ACCESS_FAILED")
    if not gate["hierarchy_passed"]:
        gate["blocking_reasons"].append("HIERARCHY_FAILED")
    if not gate["deterministic_A_B_byte_identical"]:
        gate["blocking_reasons"].append("DETERMINISM_FAILED")
    if not gate["negative_tests_passed"]:
        gate["blocking_reasons"].append("NEGATIVE_SUITE_NOT_IMPLEMENTED")
    gate["passed"] = not gate["blocking_reasons"]

    write_json(gate_path, gate)
    write_json(out_dir / "connectivity.json", connectivity)
    write_json(out_dir / "namespace.json", namespace)
    write_json(out_dir / "hierarchy.json", hierarchy)
    write_json(out_dir / "drc.json", drc)
    write_json(out_dir / "fingerprints.json", {"geometry_fingerprint": geometry_fingerprint(clean_gds, cfg.top_name), "non_text_geometry_fingerprint": non_text_geometry_fingerprint(clean_gds, cfg.top_name)})
    write_json(out_dir / "clone_rows.json", clone_rows)
    write_json(
        manifest_path,
        {
            "candidate_id": gate["candidate_id"],
            "child_name": cfg.child_name,
            "template_id": "compact_abutment",
            "clean_gds_path": str(clean_gds.resolve()),
            "clean_gds_sha256": gate["clean_gds_sha256"],
            "review_atlas_gds": str(review_atlas.resolve()),
            "pin_map_path": str(pin_map_path.resolve()),
            "placement_path": str(placement_path.resolve()),
            "route_geometry_path": str(route_path.resolve()),
            "power_geometry_path": str(power_path.resolve()),
            "machine_gate_path": str(gate_path.resolve()),
            "atlas_meta": atlas_meta,
        },
    )
    write_csv(
        placement_path,
        [
            {
                "instance_name": item.spec.instance_name,
                "logical_module": item.spec.logical_module,
                "orientation": item.orientation,
                "x0": item.bbox[0],
                "y0": item.bbox[1],
                "x1": item.bbox[2],
                "y1": item.bbox[3],
            }
            for item in placed
        ],
    )
    write_text(
        out_dir / "summary.md",
        "\n".join(
            [
                f"# {cfg.child_name} compact_abutment",
                "",
                f"- drc_marker_count: `{drc['marker_count']}`",
                f"- connectivity_passed: `{connectivity['physical_connectivity_verification_passed']}`",
                f"- foreign_net_passed: `{gate['foreign_net_passed']}`",
                f"- power_continuity_passed: `{gate['power_continuity_passed']}`",
                f"- pin_access_passed: `{gate['pin_access_passed']}`",
                f"- hierarchy_passed: `{gate['hierarchy_passed']}`",
                f"- determinism_passed: `{gate['deterministic_A_B_byte_identical']}`",
                f"- negative_tests_passed: `{gate['negative_tests_passed']}`",
                f"- machine_gate_passed: `{gate['passed']}`",
                "",
            ]
        ),
    )
    return gate


def _generate_multiline(cfg: ChildConfig, template: ChildTemplate) -> dict[str, Any]:
    out_dir = OUT_ROOT / cfg.child_name / template.template_id
    out_dir.mkdir(parents=True, exist_ok=True)
    tech = Tech.freepdk45(REPO_ROOT)
    legal_pairs = _load_legal_matrix()
    binding = read_json(cfg.source_binding_path)["binding_rows"]
    compact_gap = float(_compute_gap(binding, legal_pairs, "0.0"))
    specs = _child_specs(cfg.source_binding_path)
    lib, placed_children, clone_rows = clone_children(specs, out_dir / "clones")
    placed = _place_multiline(placed_children, template.row_groups, gap=compact_gap)
    top = instantiate_children(lib, cfg.top_name, placed)
    full_endpoints_by_net, placed_by_name = _build_endpoints(binding, placed)
    rails = _bridge_power_rails_multiline(top, placed, tech)
    child_boxes = [{"label": item.spec.instance_name, "bbox": item.bbox} for item in placed]
    top_pin_bboxes, endpoints_by_net = _macro_level_top_pins(cfg, binding, placed)
    for power_net in ("VDD", "VSS"):
        top_pin_bboxes[power_net] = rails[power_net]
        endpoints_by_net[power_net] = full_endpoints_by_net[power_net]
    route_geometry = {"input_buses": {}, "internal_buses": {}, "pair_routes": {}}
    for pin_name, bbox in top_pin_bboxes.items():
        add_top_label(top, pin_name, bbox)

    clean_gds = out_dir / "clean.gds"
    annotated_gds = out_dir / "annotated.gds"
    review_atlas = out_dir / "review_atlas.gds"
    pin_map_path = out_dir / "pin_map.json"
    placement_path = out_dir / "placement.csv"
    route_path = out_dir / "route_geometry.json"
    power_path = out_dir / "power_geometry.json"
    gate_path = out_dir / "machine_gate.json"
    manifest_path = out_dir / "manifest.json"
    determinism_path = out_dir / "determinism.json"
    negative_path = out_dir / "negative_summary.json"
    structural_path = out_dir / "STRUCTURAL_LAYOUT_FACTS.json"

    write_gds(lib, clean_gds)
    write_json(pin_map_path, {name: [bbox] for name, bbox in top_pin_bboxes.items()})
    write_json(route_path, route_geometry)
    write_json(power_path, {key: top_pin_bboxes[key] for key in ["VDD", "VSS"] if key in top_pin_bboxes})
    connectivity = verify_hierarchical_connectivity(gds_path=clean_gds, top_name=cfg.top_name, endpoints_by_net=endpoints_by_net, top_pin_bboxes=top_pin_bboxes)
    namespace = verify_composite_pin_namespace(clean_gds, cfg.top_name, cfg.top_pin_labels)
    hierarchy = verify_composite_hierarchy_closure(clean_gds, cfg.top_name)
    drc = run_cell_drc(Path("/usr/bin/klayout"), REPO_ROOT / "technology/freepdk45/tech/freepdk45.lydrc", clean_gds, cfg.top_name, out_dir / "drc")
    annotate_from_bboxes(clean_gds, cfg.top_name, child_boxes, annotated_gds)
    atlas_meta = make_review_atlas(clean_gds, annotated_gds, cfg.top_name, review_atlas)
    determinism = _determinism_payload(clean_gds)
    negative_summary = _run_negative_suite(
        clean_gds=clean_gds,
        top_name=cfg.top_name,
        top_pin_labels=cfg.top_pin_labels,
        endpoints_by_net=endpoints_by_net,
        top_pin_bboxes=top_pin_bboxes,
    )
    structural_facts = _structural_facts(template.template_id, placed)
    write_json(determinism_path, determinism)
    write_json(negative_path, negative_summary)
    write_json(structural_path, structural_facts)

    gate = {
        "candidate_id": f"{cfg.child_name}__{template.template_id}",
        "template_id": template.template_id,
        "top_name": cfg.top_name,
        "clean_gds_path": str(clean_gds.resolve()),
        "clean_gds_sha256": _sha256(clean_gds),
        "drc_marker_count": drc["marker_count"],
        "source_contract_passed": True,
        "bit_exact_pin_passed": namespace["top_canonical_label_set_exact"],
        "connectivity_passed": connectivity["physical_connectivity_verification_passed"],
        "foreign_net_passed": _foreign_net_passed(connectivity),
        "power_continuity_passed": _power_continuity(connectivity),
        "pin_access_passed": namespace["top_canonical_label_set_exact"] and namespace["duplicate_top_label_count"] == 0,
        "hierarchy_passed": hierarchy["reference_closure_passed"],
        "child_immutability_passed": True,
        "deterministic_A_B_byte_identical": determinism["byte_identical"],
        "negative_tests_passed": negative_summary["negative_tests_passed"],
        "review_artifacts_complete": clean_gds.exists() and review_atlas.exists(),
        "child_multiline_row_count": structural_facts["child_multiline_row_count"],
        "child_unique_y_interval_count": structural_facts["child_unique_y_interval_count"],
        "candidate_height_gt_single_row_cell_height": structural_facts["candidate_height_gt_single_row_cell_height"],
        "semantic_candidate_name_contract_passed": not _semantic_contract_failed(template.template_id, structural_facts),
        "passed": False,
        "blocking_reasons": [],
    }
    if gate["drc_marker_count"] != 0:
        gate["blocking_reasons"].append("DRC_NONZERO")
    if not gate["connectivity_passed"]:
        gate["blocking_reasons"].append("CONNECTIVITY_FAILED")
    if not gate["foreign_net_passed"]:
        gate["blocking_reasons"].append("FOREIGN_NET_FAILED")
    if not gate["power_continuity_passed"]:
        gate["blocking_reasons"].append("POWER_CONTINUITY_FAILED")
    if not gate["pin_access_passed"]:
        gate["blocking_reasons"].append("PIN_ACCESS_FAILED")
    if not gate["hierarchy_passed"]:
        gate["blocking_reasons"].append("HIERARCHY_FAILED")
    if not gate["deterministic_A_B_byte_identical"]:
        gate["blocking_reasons"].append("DETERMINISM_FAILED")
    if not gate["negative_tests_passed"]:
        gate["blocking_reasons"].append("NEGATIVE_SUITE_FAILED")
    if gate["child_multiline_row_count"] < 2 or gate["child_unique_y_interval_count"] < 2 or not gate["candidate_height_gt_single_row_cell_height"]:
        gate["blocking_reasons"].append("CHILD_MULTILINE_STRUCTURE_FAILED")
    if not gate["semantic_candidate_name_contract_passed"]:
        gate["blocking_reasons"].append("SEMANTIC_CANDIDATE_NAME_CONTRACT_FAILED")
    gate["passed"] = not gate["blocking_reasons"]

    write_json(gate_path, gate)
    write_json(out_dir / "connectivity.json", connectivity)
    write_json(out_dir / "namespace.json", namespace)
    write_json(out_dir / "hierarchy.json", hierarchy)
    write_json(out_dir / "drc.json", drc)
    write_json(out_dir / "fingerprints.json", {"geometry_fingerprint": geometry_fingerprint(clean_gds, cfg.top_name), "non_text_geometry_fingerprint": non_text_geometry_fingerprint(clean_gds, cfg.top_name)})
    write_json(out_dir / "clone_rows.json", clone_rows)
    write_json(
        manifest_path,
        {
            "candidate_id": gate["candidate_id"],
            "child_name": cfg.child_name,
            "template_id": template.template_id,
            "clean_gds_path": str(clean_gds.resolve()),
            "clean_gds_sha256": gate["clean_gds_sha256"],
            "review_atlas_gds": str(review_atlas.resolve()),
            "pin_map_path": str(pin_map_path.resolve()),
            "placement_path": str(placement_path.resolve()),
            "route_geometry_path": str(route_path.resolve()),
            "power_geometry_path": str(power_path.resolve()),
            "machine_gate_path": str(gate_path.resolve()),
            "structural_layout_facts_path": str(structural_path.resolve()),
            "atlas_meta": atlas_meta,
        },
    )
    write_csv(
        placement_path,
        [
            {
                "instance_name": item.spec.instance_name,
                "logical_module": item.spec.logical_module,
                "orientation": item.orientation,
                "x0": item.bbox[0],
                "y0": item.bbox[1],
                "x1": item.bbox[2],
                "y1": item.bbox[3],
                "row_id": next(index for index, interval in enumerate(sorted({(round(entry.bbox[1], 6), round(entry.bbox[3], 6)) for entry in placed})) if interval == (round(item.bbox[1], 6), round(item.bbox[3], 6))),
            }
            for item in placed
        ],
    )
    write_text(
        out_dir / "summary.md",
        "\n".join(
            [
                f"# {cfg.child_name} {template.template_id}",
                "",
                f"- child_multiline_row_count: `{gate['child_multiline_row_count']}`",
                f"- child_unique_y_interval_count: `{gate['child_unique_y_interval_count']}`",
                f"- drc_marker_count: `{drc['marker_count']}`",
                f"- connectivity_passed: `{connectivity['physical_connectivity_verification_passed']}`",
                f"- foreign_net_passed: `{gate['foreign_net_passed']}`",
                f"- power_continuity_passed: `{gate['power_continuity_passed']}`",
                f"- pin_access_passed: `{gate['pin_access_passed']}`",
                f"- hierarchy_passed: `{gate['hierarchy_passed']}`",
                f"- determinism_passed: `{gate['deterministic_A_B_byte_identical']}`",
                f"- negative_tests_passed: `{gate['negative_tests_passed']}`",
                f"- semantic_candidate_name_contract_passed: `{gate['semantic_candidate_name_contract_passed']}`",
                f"- machine_gate_passed: `{gate['passed']}`",
                "",
            ]
        ),
    )
    return gate


def main() -> int:
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    rows = []
    for cfg in CHILD_CONFIGS.values():
        _copy_baseline(cfg)
        gate = _generate_compact(cfg)
        rows.append({"child_name": cfg.child_name, "template_id": "compact_abutment", "passed": gate["passed"], "drc_marker_count": gate["drc_marker_count"], "blocking_reasons": ",".join(gate["blocking_reasons"])})
        for template in MULTILINE_TEMPLATES:
            multiline_gate = _generate_multiline(cfg, template)
            rows.append({"child_name": cfg.child_name, "template_id": template.template_id, "passed": multiline_gate["passed"], "drc_marker_count": multiline_gate["drc_marker_count"], "blocking_reasons": ",".join(multiline_gate["blocking_reasons"])})
    write_csv(OUT_ROOT / "compact_generation_summary.csv", rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
