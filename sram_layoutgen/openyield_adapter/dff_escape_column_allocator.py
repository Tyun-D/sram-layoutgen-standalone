from __future__ import annotations

import ast
from typing import Any

from sram_layoutgen.openyield_adapter.grid_legal_geometry import snap_coordinate


def allocate_escape_columns(
    *,
    pin_access_rows: list[dict[str, Any]],
    column_pitch: float,
    grid: float,
) -> dict[str, Any]:
    rows = []
    last_x: float | None = None
    duplicate_count = 0
    overlapping_count = 0
    seen: set[float] = set()
    for row in sorted(pin_access_rows, key=lambda item: (float(ast.literal_eval(item["selected_via_center"])[0]), item["endpoint"])):
        desired_x = float(ast.literal_eval(row["selected_via_center"])[0])
        column_x = snap_coordinate(desired_x if last_x is None else max(desired_x, last_x + column_pitch), grid)
        if last_x is not None and column_x - last_x < column_pitch - 1e-6:
            overlapping_count += 1
        if column_x in seen:
            duplicate_count += 1
        seen.add(column_x)
        last_x = column_x
        rows.append(
            {
                **row,
                "vertical_column_x": column_x,
                "overlap_adjustment": round(column_x - desired_x, 6),
            }
        )
    return {
        "rows": rows,
        "overlapping_different_net_vertical_column_count": overlapping_count,
        "duplicate_column_x_count": duplicate_count,
    }
