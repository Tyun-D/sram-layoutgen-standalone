"""Metadata-only placement helpers for OpenYield DFF arrays."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DffPlacement:
    instance_name: str
    array_type: str
    bit_index: int
    macro_name: str
    x: float
    y: float
    orientation: str
    nets: dict[str, str]
    semantic_role: str
    downstream_consumer: str
    safe_for_physical_mapping: bool
    safe_for_shared_rail: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_dff_array_metadata_plan(
    addr_width: int,
    data_width: int,
    origin_x: float,
    origin_y: float,
    pitch_x: float,
    row_gap: float,
    dff_width: float,
    dff_height: float,
    clk_net: str = "clk_buf",
    orientation: str = "R0",
) -> dict[str, Any]:
    addr_y = float(origin_y)
    data_y = float(origin_y) + float(dff_height) + float(row_gap)

    placements: list[DffPlacement] = []
    for bit in range(max(0, int(addr_width))):
        placements.append(
            DffPlacement(
                instance_name=f"Xaddr_dff_b{bit}",
                array_type="ADDR_DFF",
                bit_index=bit,
                macro_name="dff",
                x=float(origin_x) + bit * float(pitch_x),
                y=addr_y,
                orientation=orientation,
                nets={
                    "d": f"addr[{bit}]",
                    "clk": clk_net,
                    "q": f"addr_q[{bit}]",
                    "vdd": "vdd",
                    "gnd": "gnd",
                },
                semantic_role="address_latch",
                downstream_consumer=f"DECODER_CASCADE.A[{bit}]",
                safe_for_physical_mapping=True,
                safe_for_shared_rail=False,
            )
        )
    for bit in range(max(0, int(data_width))):
        placements.append(
            DffPlacement(
                instance_name=f"Xdata_dff_b{bit}",
                array_type="DATA_DFF",
                bit_index=bit,
                macro_name="dff",
                x=float(origin_x) + bit * float(pitch_x),
                y=data_y,
                orientation=orientation,
                nets={
                    "d": f"din[{bit}]",
                    "clk": clk_net,
                    "q": f"din_q[{bit}]",
                    "vdd": "vdd",
                    "gnd": "gnd",
                },
                semantic_role="data_latch",
                downstream_consumer=f"WRITEDRIVER.DIN[{bit}]",
                safe_for_physical_mapping=True,
                safe_for_shared_rail=False,
            )
        )

    overlaps_bbox = float(pitch_x) < float(dff_width)
    total_width = 0.0
    if addr_width > 0 or data_width > 0:
        longest = max(addr_width, data_width)
        total_width = float(dff_width) + max(0, longest - 1) * float(pitch_x)
    total_height = (2 * float(dff_height) + float(row_gap)) if (addr_width > 0 or data_width > 0) else 0.0

    return {
        "placements": [item.to_dict() for item in placements],
        "origin_x": float(origin_x),
        "origin_y": float(origin_y),
        "pitch_x": float(pitch_x),
        "row_gap": float(row_gap),
        "macro_name": "dff",
        "orientation": orientation,
        "clk_net": clk_net,
        "dff_width": float(dff_width),
        "dff_height": float(dff_height),
        "address_dff_count": int(addr_width),
        "data_dff_count": int(data_width),
        "placement_count": len(placements),
        "addr_row_y": addr_y,
        "data_row_y": data_y,
        "bbox_estimate": {
            "x0": float(origin_x),
            "y0": float(origin_y),
            "x1": float(origin_x) + total_width,
            "y1": float(origin_y) + total_height,
            "width": total_width,
            "height": total_height,
        },
        "pitch_x_legal_for_bbox": not overlaps_bbox,
        "overlap_risk_if_physically_placed": overlaps_bbox,
        "safe_for_shared_rail": False,
        "row_placement_readiness": "metadata_only",
        "dff_array_can_enter_metadata_placement": True,
        "dff_array_can_enter_standalone_placement": False,
        "notes": [
            "This plan is metadata-only and does not imply legal physical row abutment.",
            "Clock routing, power stitching, and real row legalization remain out of scope.",
        ],
    }
