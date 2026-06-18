"""Metadata-only feasibility audit helpers for OpenYield control rows."""

from __future__ import annotations

from typing import Any

from .control_row_floorplan import build_control_row_floorplan


def build_control_row_feasibility(
    addr_width: int,
    data_width: int,
    dff_width: float,
    dff_height: float,
    pitch_margin: float,
    channel_width: float,
    clock_entry_side: str,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
) -> dict[str, Any]:
    minimum_no_overlap_pitch_x = float(dff_width)
    recommended_pitch_x_no_margin = float(dff_width)
    recommended_pitch_x_with_margin = float(dff_width) + max(0.0, float(pitch_margin))
    recommended_row_height = float(dff_height)
    recommended_row_gap = float(dff_height)
    margin_added = float(pitch_margin) > 0.0

    floorplan = build_control_row_floorplan(
        addr_width=addr_width,
        data_width=data_width,
        origin_x=origin_x,
        origin_y=origin_y,
        dff_width=dff_width,
        dff_height=dff_height,
        pitch_policy="bbox_width_plus_margin" if margin_added else "bbox_width",
        row_gap_policy="bbox_height",
        pitch_margin=pitch_margin,
    )

    clock_channel = {
        "clock_source": "TIME.clk_buf",
        "clock_sink_rows": ["ADDR_DFF_ROW", "DATA_DFF_ROW"],
        "clock_entry_side": clock_entry_side,
        "clock_channel_reserved": True,
        "clock_channel_width_um": float(channel_width),
        "clock_channel_is_metadata_only": True,
        "clock_channel_physical_routing_proven": False,
        "clock_tree_generated": False,
        "clock_routing_changed": False,
        "clock_skew_checked": False,
    }

    row_to_decoder_channel = {
        "source_row": "ADDR_DFF_ROW",
        "sink_block": "DECODER_CASCADE",
        "nets": [f"addr_q[{bit}]" for bit in range(max(0, int(addr_width)))],
        "relative_position_hint": "ADDR_DFF_ROW near decoder input side",
        "channel_reserved": True,
        "channel_width_um": float(channel_width),
        "physical_routing_proven": False,
    }
    row_to_write_driver_channel = {
        "source_row": "DATA_DFF_ROW",
        "sink_block": "WRITEDRIVER",
        "nets": [f"din_q[{bit}]" for bit in range(max(0, int(data_width)))],
        "relative_position_hint": "DATA_DFF_ROW near write driver input side",
        "channel_reserved": True,
        "channel_width_um": float(channel_width),
        "physical_routing_proven": False,
    }

    blockers = [
        "Clock channel is metadata-only; no physical clock route or skew proof exists.",
        "Row-to-decoder channel is reserved only in metadata; addr_q routing is not physically proven.",
        "Row-to-write-driver channel is reserved only in metadata; din_q routing is not physically proven.",
        "Row rail sharing / shared rail policy is still disabled.",
        "Control-row abutment and integration with surrounding control logic remain unproven.",
    ]

    return {
        "addr_width": int(addr_width),
        "data_width": int(data_width),
        "dff_bbox": {
            "width": float(dff_width),
            "height": float(dff_height),
        },
        "minimum_no_overlap_pitch_x": minimum_no_overlap_pitch_x,
        "recommended_pitch_x_no_margin": recommended_pitch_x_no_margin,
        "recommended_pitch_x_with_margin": recommended_pitch_x_with_margin,
        "pitch_margin_um": float(pitch_margin),
        "pitch_margin_policy": "conservative_spacing_margin",
        "bbox_overlap_avoided": recommended_pitch_x_with_margin >= minimum_no_overlap_pitch_x,
        "margin_added": margin_added,
        "recommended_row_height": recommended_row_height,
        "recommended_row_gap": recommended_row_gap,
        "clock_entry_side": clock_entry_side,
        "clock_channel": clock_channel,
        "row_to_decoder_channel": row_to_decoder_channel,
        "row_to_write_driver_channel": row_to_write_driver_channel,
        "addr_dff_row_feasibility": {
            **floorplan["addr_row"],
            "clock_entry_side": clock_entry_side,
            "channel_to_decoder_reserved": True,
            "channel_width_um": float(channel_width),
            "physical_routing_proven": False,
        },
        "data_dff_row_feasibility": {
            **floorplan["data_row"],
            "clock_entry_side": clock_entry_side,
            "channel_to_write_driver_reserved": True,
            "channel_width_um": float(channel_width),
            "physical_routing_proven": False,
        },
        "safe_for_control_row_metadata_feasibility": True,
        "channel_reservation_available": True,
        "clock_channel_reserved": True,
        "row_to_decoder_channel_reserved": True,
        "row_to_write_driver_channel_reserved": True,
        "physical_routing_proven": False,
        "clock_skew_checked": False,
        "shared_rail_enabled": False,
        "can_enter_physical_row_placement": False,
        "can_enter_standalone_control_placement": False,
        "blocking_items": blockers,
        "floorplan_reference": floorplan,
    }
