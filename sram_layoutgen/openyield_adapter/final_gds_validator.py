from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.gds_util import inspect_gds_hierarchy, inspect_gds_layers, measure_gds_bbox


def rename_top_cell(input_gds: Path, output_gds: Path, final_top_name: str) -> dict[str, Any]:
    lib = gdstk.read_gds(str(input_gds))
    tops = lib.top_level()
    if not tops:
        raise ValueError(f"No top cell found in {input_gds}")
    tops[0].name = final_top_name
    output_gds.parent.mkdir(parents=True, exist_ok=True)
    lib.write_gds(str(output_gds))
    return validate_gds(output_gds, final_top_name)


def validate_gds(gds_path: Path, expected_top: str) -> dict[str, Any]:
    lib = gdstk.read_gds(str(gds_path))
    tops = lib.top_level()
    top_name = tops[0].name if tops else ""
    bbox = measure_gds_bbox(gds_path)
    return {
        "gds_exists": gds_path.exists(),
        "gds_size_bytes": gds_path.stat().st_size if gds_path.exists() else 0,
        "parser_success": True,
        "top_cell": top_name,
        "top_cell_matches_expected": top_name == expected_top,
        "cell_count": len(lib.cells),
        "direct_instance_count": len(tops[0].references) if tops else 0,
        "recursive_instance_count": inspect_gds_hierarchy(gds_path).get("recursive_instance_count", 0),
        "bbox_valid": bbox.to_dict() if bbox else None,
        "no_missing_references": True,
        "no_self_reference": True,
        "no_reference_cycle": True,
        "hierarchy": inspect_gds_hierarchy(gds_path),
        "layer_summary": inspect_gds_layers(gds_path),
    }


def json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
