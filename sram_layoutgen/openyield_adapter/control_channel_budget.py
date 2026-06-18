"""Metadata-only channel budget and side-geometry audit for OpenYield control rows."""

from __future__ import annotations

from typing import Any


def build_channel_budget(
    addr_width: int,
    data_width: int,
    channel_width: float,
    clock_channel_width: float,
    route_pitch: float,
    route_margin: float,
    clock_entry_side: str,
    decoder_side: str,
    write_driver_side: str,
    write_driver_pin_known: bool,
) -> dict[str, Any]:
    row_to_decoder = _budget_entry(
        channel_name="ADDR_TO_DECODER_CHANNEL",
        source_block="ADDR_DFF_ROW",
        sink_block="DECODER_CASCADE",
        source_side_hint="row_output_side_toward_decoder",
        sink_side_hint=decoder_side,
        source_pins_or_nets=[f"addr_q[{bit}]" for bit in range(max(0, int(addr_width)))],
        sink_pins_or_nets=[f"A[{bit}]" for bit in range(max(0, int(addr_width)))],
        available_width=channel_width,
        required_tracks=max(0, int(addr_width)),
        route_pitch=route_pitch,
        route_margin=route_margin,
        physical_access_proven=False,
        physical_routing_proven=False,
        notes=(
            "DECODER_CASCADE remains a hierarchical decoder block, not a single hard macro pin-proven leaf.",
            "Decoder side geometry is still metadata-only in this step.",
        ),
    )
    row_to_decoder["decoder_side_geometry_proven"] = False
    row_to_decoder["decoder_channel_budget_is_metadata_only"] = True

    row_to_write_driver = _budget_entry(
        channel_name="DATA_TO_WRITEDRIVER_CHANNEL",
        source_block="DATA_DFF_ROW",
        sink_block="WRITEDRIVER",
        source_side_hint="row_output_side_toward_write_driver",
        sink_side_hint=write_driver_side,
        source_pins_or_nets=[f"din_q[{bit}]" for bit in range(max(0, int(data_width)))],
        sink_pins_or_nets=[f"DIN[{bit}]" for bit in range(max(0, int(data_width)))],
        available_width=channel_width,
        required_tracks=max(0, int(data_width)),
        route_pitch=route_pitch,
        route_margin=route_margin,
        physical_access_proven=bool(write_driver_pin_known),
        physical_routing_proven=False,
        notes=(
            "write_driver GDS audit shows DIN/EN on the bottom side and BL/BLB on the top side.",
            "The input-side pin location is known, but the interconnect from DATA_DFF_ROW is still not physically routed.",
        ),
    )
    row_to_write_driver["write_driver_side_pin_known"] = bool(write_driver_pin_known)
    row_to_write_driver["write_driver_channel_physical_route_proven"] = False

    known_clock_nets = 1
    reserved_future_control_tracks = 1
    clock_channel = _budget_entry(
        channel_name="CLOCK_CHANNEL",
        source_block="TIME/control side",
        sink_block="ADDR_DFF_ROW + DATA_DFF_ROW",
        source_side_hint=clock_entry_side,
        sink_side_hint="control_facing_row_side",
        source_pins_or_nets=["clk_buf", "future_control_net"],
        sink_pins_or_nets=["ADDR_DFF_ROW.clk", "DATA_DFF_ROW.clk"],
        available_width=clock_channel_width,
        required_tracks=known_clock_nets + reserved_future_control_tracks,
        route_pitch=route_pitch,
        route_margin=route_margin,
        physical_access_proven=False,
        physical_routing_proven=False,
        notes=(
            "Known clock net is clk_buf.",
            "One extra future control track is reserved conservatively for gated/control-side clock distribution planning.",
        ),
    )
    clock_channel["known_clock_nets"] = known_clock_nets
    clock_channel["reserved_future_control_tracks"] = reserved_future_control_tracks
    clock_channel["clock_tree_generated"] = False
    clock_channel["clock_skew_checked"] = False

    collision_risk = not (
        row_to_decoder["metadata_budget_pass"]
        and row_to_write_driver["metadata_budget_pass"]
        and clock_channel["metadata_budget_pass"]
    )

    blockers = [
        "Channel budgets are metadata-only; no physical route or via plan is proven.",
        "Decoder side geometry is not pin-proven at hardcell level.",
        "Clock skew and real clock tree distribution remain unchecked.",
        "No row-abutment, rail-sharing, or integrated control-row routing proof exists yet.",
    ]
    if collision_risk:
        blockers.insert(0, "At least one reserved channel fails the conservative metadata budget estimate.")

    safe_for_metadata = (
        row_to_decoder["metadata_budget_pass"]
        and row_to_write_driver["metadata_budget_pass"]
        and clock_channel["metadata_budget_pass"]
    )

    return {
        "addr_width": int(addr_width),
        "data_width": int(data_width),
        "channel_width": float(channel_width),
        "clock_channel_width": float(clock_channel_width),
        "route_pitch": float(route_pitch),
        "route_margin": float(route_margin),
        "clock_entry_side": clock_entry_side,
        "decoder_side": decoder_side,
        "write_driver_side": write_driver_side,
        "row_to_decoder_channel": row_to_decoder,
        "row_to_write_driver_channel": row_to_write_driver,
        "clock_channel": clock_channel,
        "row_to_decoder_budget_pass": row_to_decoder["metadata_budget_pass"],
        "row_to_write_driver_budget_pass": row_to_write_driver["metadata_budget_pass"],
        "clock_channel_budget_pass": clock_channel["metadata_budget_pass"],
        "decoder_side_geometry_proven": False,
        "write_driver_side_pin_known": bool(write_driver_pin_known),
        "physical_routing_proven": False,
        "clock_skew_checked": False,
        "bbox_overlap_or_channel_collision_risk": collision_risk,
        "safe_for_channel_budget_metadata": safe_for_metadata,
        "can_enter_physical_row_placement": False,
        "can_enter_standalone_control_placement": False,
        "blockers": blockers,
    }


def _budget_entry(
    channel_name: str,
    source_block: str,
    sink_block: str,
    source_side_hint: str,
    sink_side_hint: str,
    source_pins_or_nets: list[str],
    sink_pins_or_nets: list[str],
    available_width: float,
    required_tracks: int,
    route_pitch: float,
    route_margin: float,
    physical_access_proven: bool,
    physical_routing_proven: bool,
    notes: tuple[str, ...],
) -> dict[str, Any]:
    estimated_required_width = float(required_tracks) * float(route_pitch) + 2.0 * float(route_margin)
    return {
        "channel_name": channel_name,
        "source_block": source_block,
        "sink_block": sink_block,
        "source_side_hint": source_side_hint,
        "sink_side_hint": sink_side_hint,
        "source_pins_or_nets": list(source_pins_or_nets),
        "sink_pins_or_nets": list(sink_pins_or_nets),
        "channel_width_um": float(available_width),
        "required_tracks": int(required_tracks),
        "estimated_required_width": float(estimated_required_width),
        "available_width": float(available_width),
        "metadata_budget_pass": float(available_width) >= float(estimated_required_width),
        "physical_access_proven": bool(physical_access_proven),
        "physical_routing_proven": bool(physical_routing_proven),
        "notes": list(notes),
    }
