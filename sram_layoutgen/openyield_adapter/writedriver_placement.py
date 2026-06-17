"""Limited placement planning for OpenYield WRITEDRIVER integration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import ceil
from typing import Any


@dataclass(frozen=True)
class WriteDriverPlacement:
    instance_name: str
    macro_name: str
    col: int
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
class WriteDriverPlacementPlan:
    cols: int
    mux_ratio: int
    placements: tuple[WriteDriverPlacement, ...]
    macro_name: str = "write_driver"
    power_status: str = "unknown"
    safe_for_physical_mapping: bool = False
    safe_for_shared_rail: bool = False
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["placements"] = [item.to_dict() for item in self.placements]
        return data


def build_writedriver_limited_placement_plan(
    *,
    cols: int,
    mux_ratio: int,
    origin_x: float,
    origin_y: float,
    pitch_x: float,
    power_status: str,
    safe_for_physical_mapping: bool,
    safe_for_shared_rail: bool,
    use_grouped_semantics: bool = False,
    macro_name: str = "write_driver",
) -> WriteDriverPlacementPlan:
    if cols <= 0:
        raise ValueError("cols must be positive")
    if mux_ratio <= 0:
        raise ValueError("mux_ratio must be positive")

    placements: list[WriteDriverPlacement] = []
    if mux_ratio == 1 and not use_grouped_semantics:
        for col in range(cols):
            placements.append(
                _build_single_column_placement(
                    col=col,
                    origin_x=origin_x,
                    origin_y=origin_y,
                    pitch_x=pitch_x,
                    power_status=power_status,
                    safe_for_shared_rail=safe_for_shared_rail,
                    macro_name=macro_name,
                )
            )
    else:
        groups = ceil(cols / mux_ratio)
        for group in range(groups):
            start = group * mux_ratio
            group_cols = tuple(col for col in range(start, min(start + mux_ratio, cols)))
            placements.append(
                _build_grouped_placement(
                    group=group,
                    group_cols=group_cols,
                    origin_x=origin_x,
                    origin_y=origin_y,
                    pitch_x=pitch_x,
                    power_status=power_status,
                    safe_for_shared_rail=safe_for_shared_rail,
                    macro_name=macro_name,
                )
            )

    notes = [
        "Limited placement plan only; standalone is not modified.",
        "Write driver placement stays adapter-only and does not change routing or GDS writer code.",
    ]
    if mux_ratio == 1:
        notes.append("One write_driver is planned per storage/data column.")
    else:
        notes.append("Mux-ratio greater than one is represented as a grouped semantic plan only.")
        notes.append("grouped_write_mapping_needs_confirmation")
        notes.append("Physical fan-in is intentionally not expanded in this smoke.")
    if power_status != "vdd_gnd_metadata_present":
        notes.append(f"Power status is {power_status}; shared rail remains disabled.")

    return WriteDriverPlacementPlan(
        cols=cols,
        mux_ratio=mux_ratio,
        placements=tuple(placements),
        macro_name=macro_name,
        power_status=power_status,
        safe_for_physical_mapping=safe_for_physical_mapping,
        safe_for_shared_rail=safe_for_shared_rail,
        notes=tuple(notes),
    )


def _build_single_column_placement(
    *,
    col: int,
    origin_x: float,
    origin_y: float,
    pitch_x: float,
    power_status: str,
    safe_for_shared_rail: bool,
    macro_name: str,
) -> WriteDriverPlacement:
    return WriteDriverPlacement(
        instance_name=f"Xwd_c{col}",
        macro_name=macro_name,
        col=col,
        group=col,
        cols=(col,),
        x=origin_x + col * pitch_x,
        y=origin_y,
        orientation="R0",
        nets={
            "vdd": "vdd",
            "gnd": "gnd",
            "en": "write_enable",
            "din": f"din[{col}]",
            "bl": f"bl[{col}]",
            "br": f"br[{col}]",
        },
        power_status=power_status,
        safe_for_shared_rail=safe_for_shared_rail,
        notes=("Direct per-column write driver placement plan.",),
    )


def _build_grouped_placement(
    *,
    group: int,
    group_cols: tuple[int, ...],
    origin_x: float,
    origin_y: float,
    pitch_x: float,
    power_status: str,
    safe_for_shared_rail: bool,
    macro_name: str,
) -> WriteDriverPlacement:
    return WriteDriverPlacement(
        instance_name=f"Xwd_g{group}",
        macro_name=macro_name,
        col=group_cols[0],
        group=group,
        cols=group_cols,
        x=origin_x + group * pitch_x,
        y=origin_y,
        orientation="R0",
        nets={
            "vdd": "vdd",
            "gnd": "gnd",
            "en": "write_enable",
            "din": f"din[{group}]",
            "bl": f"bl[{group_cols[0]}]",
            "br": f"br[{group_cols[0]}]",
        },
        power_status=power_status,
        safe_for_shared_rail=safe_for_shared_rail,
        notes=(
            "Grouped semantic plan only; physical fan-in is not expanded.",
            f"Grouped columns {group_cols[0]}..{group_cols[-1]}.",
        ),
    )

