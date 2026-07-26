"""Limited placement planning for OpenYield column mux integration.

This module stays at the metadata/planning layer. It does not modify the
standalone flow, routing, or GDS writer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import ceil
from typing import Any


@dataclass(frozen=True)
class ColumnMuxPlacement:
    instance_name: str
    macro_name: str
    group: int
    cols: tuple[int, ...]
    x: float
    y: float
    orientation: str
    nets: dict[str, str]
    power_status: str
    safe_for_shared_rail: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ColumnMuxPlacementPlan:
    cols: int
    mux_ratio: int
    placements: tuple[ColumnMuxPlacement, ...]
    macro_name: str
    power_status: str
    safe_for_physical_mapping: bool
    safe_for_shared_rail: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["placements"] = [item.to_dict() for item in self.placements]
        return data


def build_columnmux_limited_placement_plan(
    *,
    cols: int,
    mux_ratio: int,
    origin_x: float,
    origin_y: float,
    pitch_x: float,
    use_repaired_vdd_label: bool,
    power_status: str,
    safe_for_physical_mapping: bool,
    safe_for_shared_rail: bool,
    repaired_macro_name: str = "gen_col_mux_vdd_labeled",
) -> ColumnMuxPlacementPlan:
    if cols <= 0:
        raise ValueError("cols must be positive")
    if mux_ratio <= 0:
        raise ValueError("mux_ratio must be positive")

    groups = ceil(cols / mux_ratio)
    placements: list[ColumnMuxPlacement] = []
    for group in range(groups):
        start = group * mux_ratio
        group_cols = tuple(col for col in range(start, min(start + mux_ratio, cols)))
        placements.append(
            ColumnMuxPlacement(
                instance_name=f"Xcmux_g{group}",
                macro_name=repaired_macro_name if use_repaired_vdd_label else "gen_col_mux",
                group=group,
                cols=group_cols,
                x=origin_x + group * pitch_x,
                y=origin_y,
                orientation="R0",
                nets={
                    "vdd": "vdd",
                    "gnd": "gnd",
                    "sel": f"col_sel[{group}]",
                    "bl": f"bl[{group_cols[0]}]",
                    "br": f"br[{group_cols[0]}]",
                    "out": f"mux_out[{group}]",
                    "outb": f"mux_out_b[{group}]",
                },
                power_status=power_status,
                safe_for_shared_rail=safe_for_shared_rail,
                notes=_placement_notes(mux_ratio, group_cols, use_repaired_vdd_label, power_status),
            )
        )

    return ColumnMuxPlacementPlan(
        cols=cols,
        mux_ratio=mux_ratio,
        placements=tuple(placements),
        macro_name=repaired_macro_name if use_repaired_vdd_label else "gen_col_mux",
        power_status=power_status,
        safe_for_physical_mapping=safe_for_physical_mapping,
        safe_for_shared_rail=safe_for_shared_rail,
        notes=_plan_notes(mux_ratio, use_repaired_vdd_label, power_status, safe_for_shared_rail),
    )


def _placement_notes(mux_ratio: int, cols: tuple[int, ...], use_repaired_vdd_label: bool, power_status: str) -> tuple[str, ...]:
    notes = [
        "Limited placement plan only; standalone is not modified.",
        "SenseAmp pairing stays semantic: mux_out/mux_out_b feed sense_amp IN/INB.",
    ]
    if mux_ratio > 1:
        notes.append(f"Grouped semantic plan for columns {cols[0]}..{cols[-1]}.")
        notes.append("The physical BL/BLB fan-in is intentionally not expanded in this smoke.")
    if use_repaired_vdd_label:
        notes.append("Uses repaired proof candidate with label-backed VDD metadata.")
    if power_status != "vdd_label_present":
        notes.append(f"Power status remains {power_status}; shared rail remains disabled.")
    return tuple(notes)


def _plan_notes(
    mux_ratio: int,
    use_repaired_vdd_label: bool,
    power_status: str,
    safe_for_shared_rail: bool,
) -> tuple[str, ...]:
    notes = [
        "This plan is generated from repaired alias metadata and existing sense_amp adapter semantics.",
        "No routing, GDS writer, or standalone placement code is changed.",
    ]
    if mux_ratio > 1:
        notes.append("Mux ratio greater than one is handled as a grouped semantic plan only.")
    if use_repaired_vdd_label:
        notes.append("Candidate alias uses gen_col_mux_vdd_labeled from the proof GDS.")
    if not safe_for_shared_rail:
        notes.append("Shared rail remains disabled until a separate rail continuity proof exists.")
    if power_status != "vdd_label_present":
        notes.append(f"Power status is {power_status}; this is a metadata-only placement proof.")
    return tuple(notes)
