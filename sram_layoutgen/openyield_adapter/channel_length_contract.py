from __future__ import annotations

import ast
import csv
import re
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.dimension_units import normalize_dimension_nm


def build_channel_length_contract(
    *,
    source_files: list[Path],
    requirement_csv: Path,
    freepdk45_tech: Path,
    openram_ptx: Path,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    found_values: set[int] = set()
    for source_file in source_files:
        tree = ast.parse(source_file.read_text(encoding="utf-8"), filename=str(source_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and abs(float(node.value) - 0.05e-6) < 1e-15:
                rows.append(
                    {
                        "source": str(source_file),
                        "location": f"line {getattr(node, 'lineno', 0)}",
                        "kind": "source_constant",
                        "length_expression": str(node.value),
                        "length_nm": 50,
                    }
                )
                found_values.add(50)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "__init__":
                defaults = node.args.defaults
                args = node.args.args
                if defaults:
                    pairs = zip(args[-len(defaults):], defaults)
                    for arg, default in pairs:
                        if arg.arg == "length" and isinstance(default, ast.Constant) and isinstance(default.value, (int, float)):
                            nm = normalize_dimension_nm(str(default.value), "METER")
                            found_values.add(nm)
                            rows.append(
                                {
                                    "source": str(source_file),
                                    "location": f"{node.name}:{getattr(default, 'lineno', 0)}",
                                    "kind": "init_default",
                                    "length_expression": str(default.value),
                                    "length_nm": nm,
                                }
                            )
    with requirement_csv.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            length = row.get("length", "")
            if length:
                nm = normalize_dimension_nm(length, "METER")
                found_values.add(nm)
                rows.append(
                    {
                        "source": str(requirement_csv),
                        "location": row["logical_module"],
                        "kind": "requirement_row",
                        "length_expression": length,
                        "length_nm": nm,
                    }
                )
    tech_text = freepdk45_tech.read_text(encoding="utf-8")
    match = re.search(r'drc\["minlength_channel"\]\s*=\s*([0-9.]+)', tech_text)
    min_length_nm = normalize_dimension_nm(match.group(1), "MICROMETER") if match else 0
    ptx_text = openram_ptx.read_text(encoding="utf-8")
    fixed_match = re.search(r'self\.channel_length\s*=\s*drc\("minlength_channel"\)', ptx_text)
    contract = {
        "channel_length_policy": "FIXED_TECH_MINIMUM",
        "channel_length_nm": 50,
        "arbitrary_channel_length_supported": False,
        "current_v1_channel_length_requirement_satisfied": found_values == {50},
        "channel_length_blocks_M12C3A": found_values != {50},
        "future_non_50nm_request_policy": "REJECT_WITH_EXPLICIT_ERROR",
        "required_channel_length_values_nm": sorted(found_values),
        "all_current_v1_lengths_equal_50nm": found_values == {50},
        "freepdk45_minimum_channel_length_nm": min_length_nm,
        "openram_ptx_fixed_length_nm": 50 if fixed_match else 0,
    }
    return {"rows": rows, "contract": contract}


def validate_supported_channel_length_nm(length_nm: int) -> int:
    if int(length_nm) != 50:
        raise ValueError(f"unsupported channel length for FreePDK45 V1: {length_nm} nm; expected 50 nm")
    return 50
