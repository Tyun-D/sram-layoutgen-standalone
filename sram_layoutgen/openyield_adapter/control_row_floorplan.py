"""Metadata-only control-row floorplan helpers for OpenYield DFF arrays."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .dff_array_placement import build_dff_array_metadata_plan


@dataclass(frozen=True)
class ControlRowSummary:
    row_name: str
    array_type: str
    bit_count: int
    macro: str
    clock_domain: str
    input_bus: str
    output_bus: str
    downstream_consumer: str
    relative_position_hint: str
    origin_x: float
    origin_y: float
    pitch_x: float
    row_height: float
    row_width_estimate: float
    orientation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def resolve_pitch_x(
    dff_width: float,
    pitch_policy: str,
    input_pitch_x: float | None = None,
    extra_margin: float = 0.0,
) -> float:
    if pitch_policy == "bbox_width":
        return float(dff_width)
    if pitch_policy == "bbox_width_plus_margin":
        return float(dff_width) + float(extra_margin)
    if pitch_policy == "input_pitch":
        if input_pitch_x is None:
            raise ValueError("input_pitch policy requires --pitch-x")
        return float(input_pitch_x)
    raise ValueError(f"Unsupported pitch policy: {pitch_policy}")


def resolve_row_gap(
    dff_height: float,
    row_gap_policy: str,
    explicit_gap: float | None = None,
    extra_margin: float = 0.0,
) -> float:
    if row_gap_policy == "bbox_height":
        return float(dff_height)
    if row_gap_policy == "bbox_height_plus_margin":
        return float(dff_height) + float(extra_margin)
    if row_gap_policy == "explicit_gap":
        if explicit_gap is None:
            raise ValueError("explicit_gap policy requires an explicit row gap")
        return float(explicit_gap)
    raise ValueError(f"Unsupported row gap policy: {row_gap_policy}")


def build_control_row_floorplan(
    addr_width: int,
    data_width: int,
    origin_x: float,
    origin_y: float,
    dff_width: float,
    dff_height: float,
    pitch_policy: str,
    row_gap_policy: str,
    input_pitch_x: float | None = None,
    explicit_row_gap: float | None = None,
    pitch_margin: float = 0.0,
    row_gap_margin: float = 0.0,
    clock_source: str = "TIME.clk_buf",
    orientation: str = "R0",
) -> dict[str, Any]:
    recommended_pitch_x = resolve_pitch_x(dff_width, "bbox_width")
    recommended_row_height = float(dff_height)
    recommended_row_gap = resolve_row_gap(dff_height, "bbox_height")
    chosen_pitch_x = resolve_pitch_x(dff_width, pitch_policy, input_pitch_x=input_pitch_x, extra_margin=pitch_margin)
    chosen_row_gap = resolve_row_gap(dff_height, row_gap_policy, explicit_gap=explicit_row_gap, extra_margin=row_gap_margin)

    placement_plan = build_dff_array_metadata_plan(
        addr_width=addr_width,
        data_width=data_width,
        origin_x=origin_x,
        origin_y=origin_y,
        pitch_x=chosen_pitch_x,
        row_gap=chosen_row_gap,
        dff_width=dff_width,
        dff_height=dff_height,
        clk_net="clk_buf",
        orientation=orientation,
    )

    addr_row = ControlRowSummary(
        row_name="ADDR_DFF_ROW",
        array_type="ADDR_DFF",
        bit_count=int(addr_width),
        macro="dff",
        clock_domain="clk_buf",
        input_bus="addr[i]",
        output_bus="addr_q[i]",
        downstream_consumer="DECODER_CASCADE.A[i]",
        relative_position_hint="near_decoder_input_side",
        origin_x=float(origin_x),
        origin_y=float(origin_y),
        pitch_x=chosen_pitch_x,
        row_height=recommended_row_height,
        row_width_estimate=_row_width(chosen_pitch_x, dff_width, addr_width),
        orientation=orientation,
    )
    data_row = ControlRowSummary(
        row_name="DATA_DFF_ROW",
        array_type="DATA_DFF",
        bit_count=int(data_width),
        macro="dff",
        clock_domain="clk_buf",
        input_bus="din[i]",
        output_bus="din_q[i]",
        downstream_consumer="WRITEDRIVER.DIN[i]",
        relative_position_hint="near_write_driver_input_side",
        origin_x=float(origin_x),
        origin_y=float(origin_y) + float(dff_height) + float(chosen_row_gap),
        pitch_x=chosen_pitch_x,
        row_height=recommended_row_height,
        row_width_estimate=_row_width(chosen_pitch_x, dff_width, data_width),
        orientation=orientation,
    )

    pitch_x_legal_for_bbox = chosen_pitch_x >= float(dff_width)
    overlap_risk_if_physically_placed = not pitch_x_legal_for_bbox
    recommended_pitch_avoids_bbox_overlap = recommended_pitch_x >= float(dff_width)

    return {
        "addr_width": int(addr_width),
        "data_width": int(data_width),
        "local_dff_bbox": {
            "width": float(dff_width),
            "height": float(dff_height),
        },
        "recommended_pitch_x": recommended_pitch_x,
        "recommended_row_height": recommended_row_height,
        "recommended_row_gap": recommended_row_gap,
        "recommended_pitch_avoids_bbox_overlap": recommended_pitch_avoids_bbox_overlap,
        "chosen_pitch_x": chosen_pitch_x,
        "chosen_row_gap": chosen_row_gap,
        "pitch_policy": pitch_policy,
        "row_gap_policy": row_gap_policy,
        "pitch_x_legal_for_bbox": pitch_x_legal_for_bbox,
        "overlap_risk_if_physically_placed": overlap_risk_if_physically_placed,
        "addr_row": addr_row.to_dict(),
        "data_row": data_row.to_dict(),
        "clock_domain_metadata": {
            "clock_source": clock_source,
            "clock_sink_rows": ["ADDR_DFF_ROW", "DATA_DFF_ROW"],
            "clock_tree_generated": False,
            "clock_routing_changed": False,
            "clock_skew_checked": False,
        },
        "relative_placement_hints": [
            "ADDR_DFF_ROW should be placed between TIME/control and DECODER_CASCADE.",
            "DATA_DFF_ROW should be placed between TIME/control and WRITEDRIVER input side.",
            "Clock input should enter both rows from the control/TIME side.",
            "No physical routing is generated in this step.",
        ],
        "placement_plan": placement_plan,
        "safe_for_metadata_floorplan": True,
        "pitch_recommendation_available": True,
        "can_enter_physical_row_placement": False,
        "can_enter_standalone_control_placement": False,
    }


def _row_width(pitch_x: float, dff_width: float, bit_count: int) -> float:
    if bit_count <= 0:
        return 0.0
    return float(dff_width) + max(0, int(bit_count) - 1) * float(pitch_x)
