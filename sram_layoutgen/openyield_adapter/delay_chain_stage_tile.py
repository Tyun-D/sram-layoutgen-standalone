from __future__ import annotations

from typing import Any


def build_stage_tile_rows(
    *,
    stage_index: int,
    base_x: float,
    base_y: float,
    cell_width: float,
    row_orientation: str,
    tile_policy: str,
) -> list[dict[str, Any]]:
    if tile_policy not in {"driver_left", "driver_centered", "balanced_fanout"}:
        raise ValueError(f"unsupported tile policy {tile_policy}")
    if tile_policy == "driver_left":
        order = [
            ("driver", None, row_orientation),
            ("load", 0, row_orientation),
            ("load", 1, row_orientation),
            ("load", 2, row_orientation),
            ("load", 3, row_orientation),
        ]
    elif tile_policy == "driver_centered":
        order = [
            ("load", 0, row_orientation),
            ("load", 1, row_orientation),
            ("driver", None, row_orientation),
            ("load", 2, row_orientation),
            ("load", 3, row_orientation),
        ]
    else:
        left_orientation = "MY" if row_orientation == "R0" else row_orientation
        order = [
            ("load", 0, left_orientation),
            ("load", 1, left_orientation),
            ("driver", None, row_orientation),
            ("load", 2, row_orientation),
            ("load", 3, row_orientation),
        ]
    rows: list[dict[str, Any]] = []
    cursor = float(base_x)
    for role_type, load_index, orientation in order:
        if role_type == "driver":
            instance_name = f"stage_{stage_index:02d}_driver"
        else:
            assert load_index is not None
            instance_name = f"stage_{stage_index:02d}_load_{load_index:02d}"
        rows.append(
            {
                "instance_name": instance_name,
                "stage_index": stage_index,
                "role_type": role_type,
                "load_index": load_index,
                "x": round(cursor, 6),
                "y": round(base_y, 6),
                "orientation": orientation,
            }
        )
        cursor = round(cursor + cell_width, 6)
    return rows
