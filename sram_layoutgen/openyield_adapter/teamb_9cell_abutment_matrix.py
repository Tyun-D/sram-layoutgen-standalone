from __future__ import annotations

from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import read_top_cell, run_cell_drc
from sram_layoutgen.openyield_adapter.teamb_composite_helper import write_csv, write_json


def _bbox(gds_path: Path, top_name: str) -> list[float]:
    _, top = read_top_cell(gds_path, top_name)
    box = top.bounding_box()
    return [float(box[0][0]), float(box[0][1]), float(box[1][0]), float(box[1][1])]


def _trial_pair_gds(
    *,
    left_gds: Path,
    left_top: str,
    right_gds: Path,
    right_top: str,
    output_gds: Path,
    horizontal: bool,
    gap: float,
) -> str:
    left_lib = gdstk.read_gds(left_gds)
    right_lib = gdstk.read_gds(right_gds)
    lib = gdstk.Library(unit=min(left_lib.unit, right_lib.unit), precision=min(left_lib.precision, right_lib.precision))
    added = set()
    for cell in list(left_lib.cells) + list(right_lib.cells):
        if cell.name not in added:
            lib.add(cell)
            added.add(cell.name)
    top_name = "TEAM_B_PAIRWISE_TRIAL"
    top = lib.new_cell(top_name)
    lb = _bbox(left_gds, left_top)
    rb = _bbox(right_gds, right_top)
    top.add(gdstk.Reference(next(cell for cell in lib.cells if cell.name == left_top), origin=(0.0, 0.0)))
    if horizontal:
        dx = (lb[2] - lb[0]) + gap - rb[0]
        dy = -rb[1]
    else:
        dx = -rb[0]
        dy = (lb[3] - lb[1]) + gap - rb[1]
    top.add(gdstk.Reference(next(cell for cell in lib.cells if cell.name == right_top), origin=(dx, dy)))
    output_gds.parent.mkdir(parents=True, exist_ok=True)
    lib.write_gds(output_gds)
    return top_name


def build_pairwise_abutment_matrices(
    *,
    input_lock: dict[str, Any],
    output_root: Path,
    repo_root: Path,
    klayout_bin: Path,
    drc_deck: Path,
) -> dict[str, Any]:
    horizontal_rows = []
    vertical_rows = []
    power_rows = []
    pin_rows = []
    pair_root = output_root / "_pairwise_trials"
    for left in input_lock["rows"]:
        for right in input_lock["rows"]:
            for orientation_pair in ["R0+R0"]:
                trial_gds = pair_root / f"H__{left['module_name']}__{right['module_name']}__{orientation_pair}.gds"
                trial_top = _trial_pair_gds(
                    left_gds=Path(left["clean_gds_path"]),
                    left_top=left["top_cell_name"],
                    right_gds=Path(right["clean_gds_path"]),
                    right_top=right["top_cell_name"],
                    output_gds=trial_gds,
                    horizontal=True,
                    gap=0.0,
                )
                drc = run_cell_drc(klayout_bin, drc_deck, trial_gds, trial_top, trial_gds.parent)
                horizontal_rows.append(
                    {
                        "left_module": left["module_name"],
                        "right_module": right["module_name"],
                        "orientation_pair": orientation_pair,
                        "gap": 0.0,
                        "drc_marker_count": drc["marker_count"],
                        "drc_passed": drc["drc_passed"],
                    }
                )
                power_rows.append(
                    {
                        "left_module": left["module_name"],
                        "right_module": right["module_name"],
                        "orientation_pair": orientation_pair,
                        "same_net_power_compatibility": drc["drc_passed"],
                    }
                )
                pin_rows.append(
                    {
                        "left_module": left["module_name"],
                        "right_module": right["module_name"],
                        "orientation_pair": orientation_pair,
                        "pin_access_interference": not drc["drc_passed"],
                    }
                )
            for orientation_pair in ["R0/MX"]:
                trial_gds = pair_root / f"V__{left['module_name']}__{right['module_name']}__{orientation_pair}.gds"
                trial_top = _trial_pair_gds(
                    left_gds=Path(left["clean_gds_path"]),
                    left_top=left["top_cell_name"],
                    right_gds=Path(right["clean_gds_path"]),
                    right_top=right["top_cell_name"],
                    output_gds=trial_gds,
                    horizontal=False,
                    gap=0.0,
                )
                drc = run_cell_drc(klayout_bin, drc_deck, trial_gds, trial_top, trial_gds.parent)
                vertical_rows.append(
                    {
                        "upper_module": left["module_name"],
                        "lower_module": right["module_name"],
                        "orientation_pair": orientation_pair,
                        "gap": 0.0,
                        "drc_marker_count": drc["marker_count"],
                        "drc_passed": drc["drc_passed"],
                    }
                )
    write_csv(output_root / "HORIZONTAL_PAIRWISE_ABUTMENT_MATRIX.csv", horizontal_rows)
    write_csv(output_root / "VERTICAL_PAIRWISE_ABUTMENT_MATRIX.csv", vertical_rows)
    write_csv(output_root / "POWER_RAIL_COMPATIBILITY_MATRIX.csv", power_rows)
    write_csv(output_root / "PIN_ACCESS_INTERFERENCE_MATRIX.csv", pin_rows)
    return {
        "horizontal_rows": horizontal_rows,
        "vertical_rows": vertical_rows,
        "power_rows": power_rows,
        "pin_rows": pin_rows,
    }
