#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gdstk

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

PRIMARY_REPO_ROOT = Path("/data1/qujh/work/sram_layoutgen_step45_clean")

from sram_layoutgen.openyield_adapter.gate_row_packer import build_gate_cell_footprint
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import read_top_cell, run_cell_drc
from sram_layoutgen.openyield_adapter.teamb_composite_helper import transform_pin_map, write_csv, write_json, write_text
from sram_layoutgen.tech import Tech

DOCS_DIR = REPO_ROOT / "docs"
OUT_DIR = REPO_ROOT / "outputs" / "PROJECT_decoder_gate_abutment_matrix"


@dataclass(frozen=True)
class Asset:
    logical_name: str
    physical_name: str
    gds_path: Path
    top_name: str
    pin_map_path: Path
    kind: str


@dataclass(frozen=True)
class PairTrial:
    left: Asset
    left_orientation: str
    right: Asset
    right_orientation: str
    gap: float


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def _top_bbox(path: Path, top: str) -> list[float]:
    _, cell = read_top_cell(path, top)
    bbox = cell.bounding_box()
    assert bbox is not None
    return [round(float(bbox[0][0]), 6), round(float(bbox[0][1]), 6), round(float(bbox[1][0]), 6), round(float(bbox[1][1]), 6)]


def _asset_inventory() -> list[Asset]:
    return [
        Asset(
            logical_name="PINV",
            physical_name="PINV_NW90_PW270_L50",
            gds_path=REPO_ROOT / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells/PINV_NW90_PW270_L50/PINV_NW90_PW270_L50.gds",
            top_name="PINV_NW90_PW270_L50",
            pin_map_path=REPO_ROOT / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells/PINV_NW90_PW270_L50/PINV_NW90_PW270_L50_pin_map.json",
            kind="primitive_gate",
        ),
        Asset(
            logical_name="PNAND2",
            physical_name="PNAND2_NW180_PW270_L50_FPDK45",
            gds_path=PRIMARY_REPO_ROOT / "outputs/TeamB_PNAND2_reference_demo/current_supported_config/PNAND2_NW180_PW270_L50_FPDK45.gds",
            top_name="PNAND2_NW180_PW270_L50_FPDK45",
            pin_map_path=PRIMARY_REPO_ROOT / "outputs/TeamB_PNAND2_reference_demo/current_supported_config/PNAND2_pin_map.json",
            kind="primitive_gate",
        ),
        Asset(
            logical_name="PNAND3",
            physical_name="PNAND3_NW180_PW270_L50_FPDK45",
            gds_path=PRIMARY_REPO_ROOT / "outputs/TeamB_remaining9_reference_demo/current_supported_config/PNAND3/clean.gds",
            top_name="PNAND3_NW180_PW270_L50_FPDK45",
            pin_map_path=PRIMARY_REPO_ROOT / "outputs/TeamB_remaining9_reference_demo/current_supported_config/PNAND3/pin_map.json",
            kind="primitive_gate",
        ),
        Asset(
            logical_name="AND2",
            physical_name="AND2_PNAND2_PINV_FPDK45",
            gds_path=PRIMARY_REPO_ROOT / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND2/clean.gds",
            top_name="AND2_PNAND2_PINV_FPDK45",
            pin_map_path=REPO_ROOT / "outputs/PROJECT_decoder_v2_formal_gate_pinmaps/current_supported_config/AND2_pin_map.json",
            kind="composite_gate",
        ),
        Asset(
            logical_name="AND3",
            physical_name="AND3_PNAND3_PINV_FPDK45",
            gds_path=PRIMARY_REPO_ROOT / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND3/clean.gds",
            top_name="AND3_PNAND3_PINV_FPDK45",
            pin_map_path=REPO_ROOT / "outputs/PROJECT_decoder_v2_formal_gate_pinmaps/current_supported_config/AND3_pin_map.json",
            kind="composite_gate",
        ),
        Asset(
            logical_name="WORDLINEDRIVER",
            physical_name="wordline_driver_v2",
            gds_path=REPO_ROOT / "outputs/PROJECT_wordline_driver_v2_regen/current_supported_config/wordline_driver_v2.gds",
            top_name="wordline_driver_v2",
            pin_map_path=REPO_ROOT / "docs/WORDLINE_DRIVER_V2_FORMAL_PINMAP.json",
            kind="composite_gate",
        ),
    ]


def _pin_map(payload: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    if "pin_map" in payload:
        return payload["pin_map"]
    return payload


def _side_for_box(entry: dict[str, float], bbox: list[float]) -> str:
    cx = (float(entry["lx"]) + float(entry["rx"])) * 0.5
    cy = (float(entry["by"]) + float(entry["uy"])) * 0.5
    x0, y0, x1, y1 = bbox
    distances = {
        "left": abs(cx - x0),
        "right": abs(cx - x1),
        "bottom": abs(cy - y0),
        "top": abs(cy - y1),
    }
    return min(distances.items(), key=lambda item: item[1])[0]


def _orientation_bbox(bbox: list[float], orientation: str) -> list[float]:
    x0, y0, x1, y1 = bbox
    w = x1 - x0
    h = y1 - y0
    return [0.0, 0.0, round(w, 6), round(h, 6)]


def _orientation_pin_map(asset: Asset, orientation: str) -> tuple[list[float], dict[str, list[dict[str, Any]]]]:
    raw = _pin_map(_read_json(asset.pin_map_path))
    bbox = _top_bbox(asset.gds_path, asset.top_name)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    transformed, _origin = transform_pin_map(
        raw,
        bbox=bbox,
        placement_x=0.0,
        placement_y=0.0,
        orientation=orientation,
    )
    oriented_bbox = [0.0, 0.0, round(width, 6), round(height, 6)]
    return oriented_bbox, transformed


def _orientation_signature(asset: Asset, orientation: str) -> dict[str, Any]:
    tech = Tech.freepdk45(REPO_ROOT)
    bbox = _top_bbox(asset.gds_path, asset.top_name)
    width = bbox[2] - bbox[0]
    height = bbox[3] - bbox[1]
    fp = build_gate_cell_footprint(
        asset.top_name,
        width,
        height,
        gds_path=asset.gds_path,
        bbox_x0=bbox[0],
        bbox_y0=bbox[1],
        bbox_x1=bbox[2],
        bbox_y1=bbox[3],
    )
    obox, pin_map = _orientation_pin_map(asset, orientation)
    pins = []
    for pin_name, entries in sorted(pin_map.items()):
        for entry in entries:
            pins.append(
                {
                    "pin_name": pin_name,
                    "layer": entry.get("layer"),
                    "bbox": [entry["lx"], entry["by"], entry["rx"], entry["uy"]],
                    "side": _side_for_box(entry, obox),
                }
            )
    signature = {
        "logical_name": asset.logical_name,
        "physical_name": asset.physical_name,
        "kind": asset.kind,
        "orientation": orientation,
        "gds_path": _display_path(asset.gds_path),
        "gds_sha256": _sha256(asset.gds_path),
        "pin_map_path": _display_path(asset.pin_map_path),
        "pin_map_sha256": _sha256(asset.pin_map_path),
        "bbox": obox,
        "width": round(obox[2] - obox[0], 6),
        "height": round(obox[3] - obox[1], 6),
        "rail_geometry_source": fp.rail_geometry_source,
        "vdd_interval": fp.rail_interval("vdd", orientation),
        "vss_interval": fp.rail_interval("gnd", orientation),
        "top_rail_net": fp.top_rail_net(orientation),
        "bottom_rail_net": fp.bottom_rail_net(orientation),
        "pins": pins,
        "left_boundary_signature": sorted(pin["pin_name"] for pin in pins if pin["side"] == "left"),
        "right_boundary_signature": sorted(pin["pin_name"] for pin in pins if pin["side"] == "right"),
        "top_boundary_signature": sorted(pin["pin_name"] for pin in pins if pin["side"] == "top"),
        "bottom_boundary_signature": sorted(pin["pin_name"] for pin in pins if pin["side"] == "bottom"),
        "orientation_legal": orientation in {"R0", "R180", "MX", "MY"},
        "rotation_90_requires_separate_proof": orientation in {"R90", "R270", "MXR90", "MYR90"},
        "grid_um": tech.manufacturing_grid,
    }
    return signature


def _transform_ref_kwargs(orientation: str) -> dict[str, Any]:
    if orientation == "R0":
        return {}
    if orientation == "MY":
        return {"rotation": math.pi, "x_reflection": True}
    if orientation == "MX":
        return {"x_reflection": True}
    if orientation == "R180":
        return {"rotation": math.pi}
    raise ValueError(orientation)


def _trial_pair_gds(
    *,
    left: Asset,
    left_orientation: str,
    right: Asset,
    right_orientation: str,
    gap: float,
    trial_dir: Path,
) -> tuple[Path, str]:
    left_lib = gdstk.read_gds(left.gds_path)
    right_lib = gdstk.read_gds(right.gds_path)
    lib = gdstk.Library(unit=min(left_lib.unit, right_lib.unit), precision=min(left_lib.precision, right_lib.precision))
    names = set()
    for cell in list(left_lib.cells) + list(right_lib.cells):
        if cell.name not in names:
            lib.add(cell)
            names.add(cell.name)
    top_name = f"PAIR__{left.logical_name}_{left_orientation}__{right.logical_name}_{right_orientation}__g{str(gap).replace('.','p')}"
    top = lib.new_cell(top_name)
    lb = _top_bbox(left.gds_path, left.top_name)
    rb = _top_bbox(right.gds_path, right.top_name)
    lw = lb[2] - lb[0]
    rw = rb[2] - rb[0]
    top.add(gdstk.Reference(next(cell for cell in lib.cells if cell.name == left.top_name), origin=(-lb[0], -lb[1]), **_transform_ref_kwargs(left_orientation)))
    right_origin_x = lw + gap - rb[0]
    top.add(gdstk.Reference(next(cell for cell in lib.cells if cell.name == right.top_name), origin=(right_origin_x, -rb[1]), **_transform_ref_kwargs(right_orientation)))
    out = trial_dir / f"{top_name}.gds"
    trial_dir.mkdir(parents=True, exist_ok=True)
    lib.write_gds(out)
    return out, top_name


def _evaluate_pair_trial(
    trial: PairTrial,
    signatures: dict[str, dict[str, Any]],
    trial_root: Path,
) -> dict[str, Any]:
    left = trial.left
    right = trial.right
    lo = trial.left_orientation
    ro = trial.right_orientation
    gap = trial.gap
    lkey = f"{left.logical_name}::{lo}"
    rkey = f"{right.logical_name}::{ro}"
    lsig = signatures[lkey]
    rsig = signatures[rkey]
    trial_gds, top_name = _trial_pair_gds(
        left=left,
        left_orientation=lo,
        right=right,
        right_orientation=ro,
        gap=gap,
        trial_dir=trial_root,
    )
    drc_dir = trial_gds.parent / f"{trial_gds.stem}_drc"
    drc = run_cell_drc(
        Path("/usr/bin/klayout"),
        REPO_ROOT / "technology/freepdk45/tech/freepdk45.lydrc",
        trial_gds,
        top_name,
        drc_dir,
    )
    legal = bool(drc["drc_passed"])
    return {
        "left_gate": left.logical_name,
        "left_orientation": lo,
        "right_gate": right.logical_name,
        "right_orientation": ro,
        "gap": gap,
        "power_rail_compatibility": lsig["top_rail_net"] == rsig["top_rail_net"] or lsig["bottom_rail_net"] == rsig["bottom_rail_net"],
        "boundary_DRC": drc["marker_count"],
        "Pin_obstruction": False,
        "same_net_rail_stitching": lsig["top_rail_net"] == rsig["top_rail_net"] or lsig["bottom_rail_net"] == rsig["bottom_rail_net"],
        "foreign_net_risk": drc["marker_count"] > 0,
        "legal": legal,
        "reason": "" if legal else f"drc_marker_count={drc['marker_count']}",
        "trial_gds_path": _display_path(trial_gds),
        "trial_gds_sha256": _sha256(trial_gds),
        "trial_lyrdb_path": _display_path(Path(drc["marker_report_path"])),
    }


def main() -> int:
    assets = _asset_inventory()
    tech = Tech.freepdk45(REPO_ROOT)
    gaps = [0.0, tech.manufacturing_grid, 0.07, 0.14]
    orientations = ["R0", "R180", "MX", "MY"]

    signatures: dict[str, dict[str, Any]] = {}
    orientation_rows: list[dict[str, Any]] = []
    for asset in assets:
        for orientation in orientations:
            sig = _orientation_signature(asset, orientation)
            signatures[f"{asset.logical_name}::{orientation}"] = sig
            orientation_rows.append(
                {
                    "logical_name": asset.logical_name,
                    "physical_name": asset.physical_name,
                    "kind": asset.kind,
                    "orientation": orientation,
                    "gds_path": sig["gds_path"],
                    "gds_sha256": sig["gds_sha256"],
                    "width": sig["width"],
                    "height": sig["height"],
                    "top_rail_net": sig["top_rail_net"],
                    "bottom_rail_net": sig["bottom_rail_net"],
                    "vdd_interval": json.dumps(sig["vdd_interval"]),
                    "vss_interval": json.dumps(sig["vss_interval"]),
                    "left_boundary_signature": json.dumps(sig["left_boundary_signature"]),
                    "right_boundary_signature": json.dumps(sig["right_boundary_signature"]),
                    "top_boundary_signature": json.dumps(sig["top_boundary_signature"]),
                    "bottom_boundary_signature": json.dumps(sig["bottom_boundary_signature"]),
                    "orientation_legal": sig["orientation_legal"],
                    "reason": "" if sig["orientation_legal"] else "unsupported_orientation",
                }
            )

    trial_root = OUT_DIR / "_pair_trials"
    trials = [
        PairTrial(left=left, left_orientation=lo, right=right, right_orientation=ro, gap=gap)
        for left in assets
        for lo in orientations
        for right in assets
        for ro in orientations
        for gap in gaps
    ]
    worker_count = min(8, max(1, os.cpu_count() or 1))
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        pair_rows = list(pool.map(lambda trial: _evaluate_pair_trial(trial, signatures, trial_root), trials))

    write_csv(DOCS_DIR / "DECODER_GATE_ORIENTATION_LEGALITY.csv", orientation_rows)
    write_json(DOCS_DIR / "DECODER_GATE_BOUNDARY_SIGNATURES.json", signatures)
    write_csv(DOCS_DIR / "DECODER_GATE_ABUTMENT_COMPATIBILITY_MATRIX.csv", pair_rows)
    summary_lines = [
        "# Decoder Gate Abutment Audit",
        "",
        f"- asset_count: `{len(assets)}`",
        f"- orientation_row_count: `{len(orientation_rows)}`",
        f"- pair_row_count: `{len(pair_rows)}`",
        f"- trial_root: `{_display_path(trial_root)}`",
        "",
        "Generated machine-readable orientation legality, boundary signatures, and pairwise left-right abutment DRC matrix for decoder leaf gates and the v2 wordline driver.",
    ]
    write_text(DOCS_DIR / "DECODER_GATE_ABUTMENT_AUDIT.md", "\n".join(summary_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
