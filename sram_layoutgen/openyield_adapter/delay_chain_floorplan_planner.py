from __future__ import annotations

from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.delay_chain_stage_tile import build_stage_tile_rows
from sram_layoutgen.openyield_adapter.delay_chain_source_lock import MODULE_SPECS


def _cell_dimensions(child_bbox: list[float]) -> tuple[float, float]:
    return round(float(child_bbox[2]) - float(child_bbox[0]), 6), round(float(child_bbox[3]) - float(child_bbox[1]), 6)


def build_delay_chain_candidates(
    *,
    module_name: str,
    child_bbox: list[float],
) -> list[dict[str, Any]]:
    spec = MODULE_SPECS[module_name]
    stage_count = spec["stage_count"]
    cell_w, cell_h = _cell_dimensions(child_bbox)
    row_pitch_open = round(cell_h + 0.95, 6)
    row_pitch_abutted = round(cell_h, 6)
    stage_w = round(cell_w * 5, 6)

    def row_policy_row(stage_index: int, *, alternating: bool) -> str:
        if not alternating:
            return "R0"
        return "R0" if stage_index % 2 == 0 else "MX"

    def build_rows_one_stage(*, serpentine: bool, tile_policy: str, alternating: bool, abutted_rows: bool) -> list[dict[str, Any]]:
        placements: list[dict[str, Any]] = []
        row_pitch = row_pitch_abutted if abutted_rows else row_pitch_open
        for stage_index in range(stage_count):
            y = round(stage_index * row_pitch, 6)
            base_x = 0.0 if (not serpentine or stage_index % 2 == 0) else 0.25
            placements.extend(
                build_stage_tile_rows(
                    stage_index=stage_index,
                    base_x=base_x,
                    base_y=y,
                    cell_width=cell_w,
                    row_orientation=row_policy_row(stage_index, alternating=alternating),
                    tile_policy=tile_policy,
                )
            )
        return placements

    def build_rows_two_stage() -> list[dict[str, Any]]:
        placements: list[dict[str, Any]] = []
        for stage_index in range(stage_count):
            row_index = stage_index // 2
            y = round(row_index * row_pitch_open, 6)
            x = 0.0 if stage_index % 2 == 0 else round(stage_w + 0.9, 6)
            placements.extend(
                build_stage_tile_rows(
                    stage_index=stage_index,
                    base_x=x,
                    base_y=y,
                    cell_width=cell_w,
                    row_orientation="R0",
                    tile_policy="balanced_fanout",
                )
            )
        return placements

    def build_single_row() -> list[dict[str, Any]]:
        placements: list[dict[str, Any]] = []
        cursor = 0.0
        for stage_index in range(stage_count):
            placements.extend(
                build_stage_tile_rows(
                    stage_index=stage_index,
                    base_x=cursor,
                    base_y=0.0,
                    cell_width=cell_w,
                    row_orientation="R0",
                    tile_policy="driver_left",
                )
            )
            cursor = round(cursor + stage_w + 0.95, 6)
        return placements

    return [
        {
            "candidate_id": "single_row_reference",
            "placements": build_single_row(),
            "tile_policy": "driver_left",
            "row_policy": "single_row",
            "applicable": True,
        },
        {
            "candidate_id": "one_stage_per_row",
            "placements": build_rows_one_stage(serpentine=False, tile_policy="driver_left", alternating=False, abutted_rows=False),
            "tile_policy": "driver_left",
            "row_policy": "one_stage_per_row",
            "applicable": True,
        },
        {
            "candidate_id": "one_stage_per_row_serpentine",
            "placements": build_rows_one_stage(serpentine=True, tile_policy="balanced_fanout", alternating=True, abutted_rows=True),
            "tile_policy": "balanced_fanout",
            "row_policy": "one_stage_per_row_serpentine",
            "applicable": True,
        },
        {
            "candidate_id": "centered_driver_stage_rows",
            "placements": build_rows_one_stage(serpentine=False, tile_policy="driver_centered", alternating=True, abutted_rows=True),
            "tile_policy": "driver_centered",
            "row_policy": "centered_driver_stage_rows",
            "applicable": True,
        },
        {
            "candidate_id": "two_stage_compact_rows",
            "placements": build_rows_two_stage(),
            "tile_policy": "balanced_fanout",
            "row_policy": "two_stage_compact_rows",
            "applicable": True,
        },
        {
            "candidate_id": "driver_spine_with_load_clusters",
            "placements": build_rows_one_stage(serpentine=False, tile_policy="balanced_fanout", alternating=True, abutted_rows=True),
            "tile_policy": "balanced_fanout",
            "row_policy": "driver_spine_with_load_clusters",
            "applicable": True,
        },
    ]
