from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import gdstk


DEBUG_LAYERS = {294, 295, 296, 297, 298}
INVENTORY_FIELDS = [
    "gds_path",
    "cell_name",
    "top_cell",
    "parent_cells",
    "child_cells",
    "bbox",
    "geometry_area",
    "polygon_count",
    "path_count",
    "text_count",
    "instance_count",
    "layer_datatype_pairs",
    "pin_texts",
    "pin_polygon_count",
    "power_texts",
    "power_polygon_count",
    "has_non_debug_geometry",
    "has_only_debug_geometry",
    "contains_annotation_layer",
    "contains_module_gds_qualification_debug",
    "contains_UNKNOWN_GOLDEN_REGION",
    "empty_cell",
    "orphan_geometry",
    "source_generation_report",
    "source_netlist_trace",
    "source_commit_or_hash",
    "parse_status",
]
HIERARCHY_FIELDS = [
    "gds_path",
    "parent_cell",
    "child_cell",
    "child_missing_in_file",
    "parent_is_top_level",
]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json_or_none(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _bbox_dict(bbox: tuple[tuple[float, float], tuple[float, float]] | None) -> dict[str, float]:
    if bbox is None:
        return {"x0": 0.0, "y0": 0.0, "x1": 0.0, "y1": 0.0, "width": 0.0, "height": 0.0}
    return {
        "x0": float(bbox[0][0]),
        "y0": float(bbox[0][1]),
        "x1": float(bbox[1][0]),
        "y1": float(bbox[1][1]),
        "width": float(bbox[1][0] - bbox[0][0]),
        "height": float(bbox[1][1] - bbox[0][1]),
    }


def _geometry_area(cell: gdstk.Cell) -> float:
    total = 0.0
    for polygon in cell.polygons:
        total += abs(float(polygon.area()))
    return total


def _layer_pairs(cell: gdstk.Cell) -> list[str]:
    pairs = {(poly.layer, poly.datatype) for poly in cell.polygons}
    pairs |= {(path.layer, path.datatype) for path in cell.paths}
    return [f"{layer}/{datatype}" for layer, datatype in sorted(pairs)]


def _has_non_debug_geometry(cell: gdstk.Cell) -> bool:
    for polygon in cell.polygons:
        if polygon.layer not in DEBUG_LAYERS:
            return True
    for path in cell.paths:
        if path.layer not in DEBUG_LAYERS:
            return True
    return False


def _has_only_debug_geometry(cell: gdstk.Cell) -> bool:
    if not cell.polygons and not cell.paths:
        return False
    return not _has_non_debug_geometry(cell)


def scan_candidate_gds(gds_dir: Path) -> dict[str, Any]:
    inventory_rows: list[dict[str, Any]] = []
    hierarchy_rows: list[dict[str, Any]] = []
    module_inventory: dict[str, dict[str, Any]] = {}
    file_count = 0
    cell_count = 0
    parse_failure_count = 0
    debug_only_count = 0
    empty_count = 0
    module_dirs = sorted(path for path in gds_dir.iterdir() if path.is_dir())
    for module_dir in module_dirs:
        gds_files = sorted(module_dir.glob("*.gds"))
        generation_report = _json_or_none(module_dir / "generation_report.json")
        manifest = _json_or_none(module_dir / "generator_manifest.json")
        pins = _json_or_none(module_dir / "pins.json")
        file_count += len(gds_files)
        module_name = module_dir.name
        module_inventory[module_name] = {
            "module_dir": str(module_dir),
            "generation_report": generation_report,
            "manifest": manifest,
            "pins": pins,
            "rail_report": _json_or_none(module_dir / "rail_report.json"),
            "bbox": _json_or_none(module_dir / "bbox.json"),
        }
        for gds_path in gds_files:
            try:
                lib = gdstk.read_gds(gds_path)
            except Exception:
                parse_failure_count += 1
                inventory_rows.append(
                    {
                        "gds_path": str(gds_path),
                        "cell_name": "",
                        "top_cell": "",
                        "parent_cells": "",
                        "child_cells": "",
                        "bbox": json.dumps(_bbox_dict(None), ensure_ascii=False),
                        "geometry_area": 0.0,
                        "polygon_count": 0,
                        "path_count": 0,
                        "text_count": 0,
                        "instance_count": 0,
                        "layer_datatype_pairs": "",
                        "pin_texts": "",
                        "pin_polygon_count": 0,
                        "power_texts": "",
                        "power_polygon_count": 0,
                        "has_non_debug_geometry": False,
                        "has_only_debug_geometry": False,
                        "contains_annotation_layer": False,
                        "contains_module_gds_qualification_debug": False,
                        "contains_UNKNOWN_GOLDEN_REGION": False,
                        "empty_cell": True,
                        "orphan_geometry": False,
                        "source_generation_report": str(module_dir / "generation_report.json"),
                        "source_netlist_trace": "",
                        "source_commit_or_hash": _sha256(gds_path),
                        "parse_status": "PARSE_FAILED",
                    }
                )
                continue
            top_names = {cell.name for cell in lib.top_level()}
            cell_map = {cell.name: cell for cell in lib.cells}
            parent_map: dict[str, list[str]] = {name: [] for name in cell_map}
            child_map: dict[str, list[str]] = {name: [] for name in cell_map}
            missing_child = False
            for cell in lib.cells:
                for ref in cell.references:
                    child_map[cell.name].append(ref.cell_name)
                    if ref.cell_name in parent_map:
                        parent_map[ref.cell_name].append(cell.name)
                    else:
                        missing_child = True
                    hierarchy_rows.append(
                        {
                            "gds_path": str(gds_path),
                            "parent_cell": cell.name,
                            "child_cell": ref.cell_name,
                            "child_missing_in_file": ref.cell_name not in cell_map,
                            "parent_is_top_level": cell.name in top_names,
                        }
                    )
            for cell in lib.cells:
                cell_count += 1
                bbox = _bbox_dict(cell.bounding_box())
                labels = [label.text for label in cell.labels]
                pin_texts = sorted({text for text in labels if text})
                power_texts = sorted({text for text in labels if text.upper() in {"VDD", "VSS", "GND"}})
                layer_pairs = _layer_pairs(cell)
                has_non_debug = _has_non_debug_geometry(cell)
                has_only_debug = _has_only_debug_geometry(cell)
                contains_annotation = any(
                    polygon.layer in DEBUG_LAYERS for polygon in cell.polygons
                ) or any(path.layer in DEBUG_LAYERS for path in cell.paths) or any(
                    label.layer in DEBUG_LAYERS for label in cell.labels
                )
                contains_unknown = any("UNKNOWN_GOLDEN_REGION" in text for text in labels)
                contains_debug = cell.name == "module_gds_qualification_debug" or any(
                    "module_gds_qualification_debug" in text for text in labels
                )
                empty_cell = not cell.polygons and not cell.paths and not cell.references and not cell.labels
                if has_only_debug:
                    debug_only_count += 1
                if empty_cell:
                    empty_count += 1
                inventory_rows.append(
                    {
                        "gds_path": str(gds_path),
                        "cell_name": cell.name,
                        "top_cell": cell.name in top_names,
                        "parent_cells": "|".join(sorted(parent_map.get(cell.name, []))),
                        "child_cells": "|".join(sorted(child_map.get(cell.name, []))),
                        "bbox": json.dumps(bbox, ensure_ascii=False),
                        "geometry_area": round(_geometry_area(cell), 6),
                        "polygon_count": len(cell.polygons),
                        "path_count": len(cell.paths),
                        "text_count": len(cell.labels),
                        "instance_count": len(cell.references),
                        "layer_datatype_pairs": "|".join(layer_pairs),
                        "pin_texts": "|".join(pin_texts),
                        "pin_polygon_count": len(pin_texts),
                        "power_texts": "|".join(power_texts),
                        "power_polygon_count": len(power_texts),
                        "has_non_debug_geometry": has_non_debug,
                        "has_only_debug_geometry": has_only_debug,
                        "contains_annotation_layer": contains_annotation,
                        "contains_module_gds_qualification_debug": contains_debug,
                        "contains_UNKNOWN_GOLDEN_REGION": contains_unknown,
                        "empty_cell": empty_cell,
                        "orphan_geometry": has_non_debug and not cell.references and cell.name in top_names and len(lib.cells) == 1,
                        "source_generation_report": str(module_dir / "generation_report.json"),
                        "source_netlist_trace": "|".join((manifest or {}).get("source_primitives", [])),
                        "source_commit_or_hash": _sha256(gds_path),
                        "parse_status": "PARSED_WITH_MISSING_CHILD_REFERENCE" if missing_child else "PARSED",
                    }
                )
    return {
        "inventory_rows": inventory_rows,
        "hierarchy_rows": hierarchy_rows,
        "inventory_fields": INVENTORY_FIELDS,
        "hierarchy_fields": HIERARCHY_FIELDS,
        "module_inventory": module_inventory,
        "candidate_gds_scan_completed": True,
        "candidate_gds_file_count": file_count,
        "candidate_gds_cell_count": cell_count,
        "candidate_gds_parse_failure_count": parse_failure_count,
        "debug_only_candidate_count": debug_only_count,
        "empty_candidate_count": empty_count,
    }
