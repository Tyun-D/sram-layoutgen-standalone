from __future__ import annotations

from typing import Any

from sram_layoutgen.openyield_adapter.grid_legal_geometry import snap_coordinate


def allocate_signal_tracks(
    *,
    net_names: list[str],
    base_y: float,
    track_width: float,
    track_pitch: float,
    grid: float,
) -> dict[str, Any]:
    rows = []
    seen_y: set[float] = set()
    for index, net_name in enumerate(net_names):
        track_y = snap_coordinate(base_y + index * track_pitch, grid)
        rows.append(
            {
                "net_name": net_name,
                "track_layer": "m1",
                "track_y": track_y,
                "track_width": track_width,
                "track_clearance": track_pitch - track_width,
            }
        )
        seen_y.add(track_y)
    return {
        "rows": rows,
        "duplicate_track_y_count": len(rows) - len(seen_y),
    }

