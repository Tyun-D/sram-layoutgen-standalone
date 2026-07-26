"""Limited placement planning for OpenYield WORDLINEDRIVER integration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class WordlineDriverPlacement:
    instance_name: str
    macro_name: str
    row: int
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
class WordlineDriverPlacementPlan:
    rows: int
    origin_x: float
    origin_y: float
    pitch_y: float
    placements: tuple[WordlineDriverPlacement, ...]
    macro_name: str = "gen_wl_driver"
    row_orientation_policy: str = "all_r0"
    power_status: str = "unknown"
    safe_for_physical_mapping: bool = False
    safe_for_shared_rail: bool = False
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["placements"] = [item.to_dict() for item in self.placements]
        return data


def build_wordlinedriver_limited_placement_plan(
    *,
    rows: int,
    origin_x: float,
    origin_y: float,
    pitch_y: float,
    power_status: str,
    safe_for_physical_mapping: bool,
    safe_for_shared_rail: bool,
    macro_name: str = "gen_wl_driver",
    row_orientation_policy: str = "all_r0",
) -> WordlineDriverPlacementPlan:
    if rows <= 0:
        raise ValueError("rows must be positive")
    if pitch_y <= 0:
        raise ValueError("pitch_y must be positive")
    if row_orientation_policy != "all_r0":
        raise ValueError("wordline drivers only support the all_r0 placement policy in this step")

    placements = tuple(
        WordlineDriverPlacement(
            instance_name=f"Xwld_r{row}",
            macro_name=macro_name,
            row=row,
            x=origin_x,
            y=origin_y + row * pitch_y,
            orientation="R0",
            nets={
                "vdd": "vdd",
                "gnd": "gnd",
                "a": f"decoder_input[{row}]",
                "b": "wordline_enable",
                "z": f"wl[{row}]",
            },
            power_status=power_status,
            safe_for_shared_rail=safe_for_shared_rail,
            notes=(
                "Limited placement plan only; standalone is not modified.",
                "A maps to decoder_input, B maps to wordline_enable, and Z maps to wl.",
            ),
        )
        for row in range(rows)
    )

    notes = [
        "Adapter-only placement metadata; this does not emit GDS or modify the main flow.",
        "One wordline driver is planned per row.",
        "B is treated as active-high based on the NAND2+INV OpenYield source chain.",
    ]
    if not safe_for_physical_mapping:
        notes.append("Physical mapping remains conditional until all pin labels and shapes are proven.")
    if not safe_for_shared_rail:
        notes.append("Shared rail is intentionally left disabled in this step.")

    return WordlineDriverPlacementPlan(
        rows=rows,
        origin_x=origin_x,
        origin_y=origin_y,
        pitch_y=pitch_y,
        placements=placements,
        macro_name=macro_name,
        row_orientation_policy=row_orientation_policy,
        power_status=power_status,
        safe_for_physical_mapping=safe_for_physical_mapping,
        safe_for_shared_rail=safe_for_shared_rail,
        notes=tuple(notes),
    )
