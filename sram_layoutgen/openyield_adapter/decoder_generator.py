from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.decoder_contract import DECODER_CHILDREN
from sram_layoutgen.openyield_adapter.gds_hierarchy_export import TopCellImportPlan, build_top_level_library, collect_search_paths
from sram_layoutgen.openyield_adapter.teamb_composite_helper import read_json, write_csv, write_json


def _bbox(repo_root: Path, module: str) -> dict[str, float]:
    payload = read_json(repo_root / "outputs" / "openyield_module_gds" / module / "bbox.json")
    return {
        "lx": float(payload["x0"]),
        "by": float(payload["y0"]),
        "rx": float(payload["x1"]),
        "uy": float(payload["y1"]),
    }


def _module_path(repo_root: Path, module: str, gds_name: str) -> Path:
    return repo_root / "outputs" / "openyield_module_gds" / module / gds_name


def _top_cell(lib: gdstk.Library, name: str) -> gdstk.Cell:
    return next(cell for cell in lib.cells if cell.name == name)


def _top_pin_labels(contract: dict[str, Any]) -> list[tuple[str, tuple[float, float]]]:
    labels: list[tuple[str, tuple[float, float]]] = []
    for index, name in enumerate(contract["expected_top_pins"]["inputs"]):
        labels.append((name, (-0.25, 0.45 + 0.35 * index)))
    for index, name in enumerate(contract["expected_top_pins"]["outputs"]):
        labels.append((name, (16.0, 0.25 + 0.18 * index)))
    labels.append(("VDD", (8.0, 4.0)))
    labels.append(("VSS", (8.0, -0.2)))
    return labels


def _add_route_geometry(top: gdstk.Cell) -> dict[str, Any]:
    top.add(gdstk.rectangle((-0.1, 3.55), (15.8, 3.7), layer=11, datatype=0))
    for idx in range(16):
        x = 10.1 + idx * 0.18
        top.add(gdstk.rectangle((x, 0.2), (x + 0.08, 3.3), layer=10, datatype=0))
    top.add(gdstk.rectangle((-0.1, -0.05), (15.8, 0.05), layer=9, datatype=0))
    return {
        "en_bus_bbox": [-0.1, 3.55, 15.8, 3.7],
        "wl_pre_vertical_link_count": 16,
        "power_stitch_bbox": [-0.1, -0.05, 15.8, 0.05],
    }


def generate_decoder_bundle(repo_root: Path, out_dir: Path, contract: dict[str, Any]) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    placements = [
        ("decoder_gate_cells", "decoder_gate_cells.gds", "decoder_gate_cells", 0.0, 0.0),
        ("row_decoder", "row_decoder.gds", "row_decoder", 5.8, 0.0),
        ("wordline_decoder", "wordline_decoder.gds", "wordline_decoder", 10.5, 0.0),
    ]
    import_plans = [
        TopCellImportPlan(
            module_name=module,
            module_gds_path=_module_path(repo_root, module, gds_name),
            root_cell_name=root_cell,
            instance_name=f"X_{module.upper()}",
            origin_x=x,
            origin_y=y,
            orientation="R0",
        )
        for module, gds_name, root_cell, x, y in placements
    ]
    search_paths = collect_search_paths(
        [_module_path(repo_root, module, gds_name) for module, gds_name, _, _, _ in placements],
        repo_root / "technology" / "freepdk45" / "gds_lib",
    )
    lib, hierarchy_manifest = build_top_level_library(import_plans, search_paths, top_cell_name=contract["top_cell_name"])
    top = _top_cell(lib, contract["top_cell_name"])
    for text, origin in _top_pin_labels(contract):
        top.add(gdstk.Label(text, origin, layer=11, texttype=0))
    route_geometry = _add_route_geometry(top)
    clean_gds = out_dir / "decoder_rebuild_clean.gds"
    review_gds = out_dir / "decoder_rebuild_review_atlas.gds"
    lib.write_gds(clean_gds)
    lib.write_gds(review_gds)
    placement_rows = []
    for module, _, _, x, y in placements:
        bbox = _bbox(repo_root, module)
        placement_rows.append(
            {
                "module": module,
                "x": x,
                "y": y,
                "orientation": "R0",
                "width": round(bbox["rx"] - bbox["lx"], 6),
                "height": round(bbox["uy"] - bbox["by"], 6),
            }
        )
    write_csv(out_dir / "decoder_placement.csv", placement_rows)
    write_json(out_dir / "decoder_hierarchy_manifest.json", hierarchy_manifest)
    write_json(out_dir / "decoder_route_strategy.json", contract["route_strategy"])
    write_json(out_dir / "decoder_route_geometry.json", route_geometry)
    metrics = {
        "top_cell_name": contract["top_cell_name"],
        "instance_count": len(placements),
        "route_strategy": contract["route_strategy"],
        "child_modules": [row["module"] for row in placement_rows],
        "fresh_rebuild": True,
    }
    write_json(out_dir / "decoder_layout_metrics.json", metrics)
    return {
        "clean_gds_path": str(clean_gds.resolve()),
        "review_atlas_path": str(review_gds.resolve()),
        "placement_csv_path": str((out_dir / "decoder_placement.csv").resolve()),
        "hierarchy_manifest_path": str((out_dir / "decoder_hierarchy_manifest.json").resolve()),
        "layout_metrics_path": str((out_dir / "decoder_layout_metrics.json").resolve()),
        "route_geometry_path": str((out_dir / "decoder_route_geometry.json").resolve()),
    }
