"""Metadata-only geometry window and keepout helpers for OpenYield control rows."""

from __future__ import annotations

from typing import Any


def build_control_geometry_windows(
    addr_width: int,
    data_width: int,
    dff_pitch_x: float,
    dff_width: float,
    row_height: float,
    row_gap: float,
    channel_width: float,
    clock_channel_width: float,
    origin_x: float,
    origin_y: float,
    decoder_side: str,
    write_driver_side: str,
    clock_entry_side: str,
    row_to_decoder_required_width: float,
    row_to_write_driver_required_width: float,
    clock_required_width: float,
    write_driver_bbox: dict[str, float] | None,
    write_driver_input_side: str,
    write_driver_pin_side_confirmed: bool,
) -> dict[str, Any]:
    addr_row_bbox = _row_bbox(origin_x, origin_y, addr_width, dff_pitch_x, dff_width, row_height)
    data_row_y0 = float(origin_y) + float(row_height) + float(row_gap)
    data_row_bbox = _row_bbox(origin_x, data_row_y0, data_width, dff_pitch_x, dff_width, row_height)

    clock_window = _rect(
        "CLOCK_ENTRY_WINDOW",
        float(origin_x) - float(clock_channel_width),
        float(origin_y),
        float(origin_x),
        data_row_bbox["y1"],
    )
    clock_window.update(
        {
            "source_side": clock_entry_side,
            "sink_rows": ["ADDR_DFF_ROW", "DATA_DFF_ROW"],
            "nets": ["clk_buf", "future_control_net"],
            "metadata_only": True,
            "physical_access_proven": False,
            "physical_routing_proven": False,
            "source_basis": "metadata_hint_from_control_side",
            "budget_required_width": float(clock_required_width),
            "window_budget_pass": float(clock_window["width"]) >= float(clock_required_width),
        }
    )

    addr_to_decoder_window = _rect(
        "ADDR_TO_DECODER_WINDOW",
        addr_row_bbox["x1"],
        addr_row_bbox["y0"],
        addr_row_bbox["x1"] + float(channel_width),
        addr_row_bbox["y1"],
    )
    addr_to_decoder_window.update(
        {
            "source_row": "ADDR_DFF_ROW",
            "sink_block": "DECODER_CASCADE",
            "source_side": "row_output_side_toward_decoder",
            "sink_side": decoder_side,
            "nets": [f"addr_q[{bit}]" for bit in range(max(0, int(addr_width)))],
            "decoder_side_geometry_proven": False,
            "decoder_window_is_metadata_hint": True,
            "metadata_only": True,
            "physical_routing_proven": False,
            "source_basis": "metadata_hint_from_control_decomposition",
            "budget_required_width": float(row_to_decoder_required_width),
            "window_budget_pass": float(addr_to_decoder_window["width"]) >= float(row_to_decoder_required_width),
        }
    )

    data_to_writedriver_window = _rect(
        "DATA_TO_WRITEDRIVER_WINDOW",
        data_row_bbox["x0"],
        data_row_bbox["y1"],
        data_row_bbox["x1"],
        data_row_bbox["y1"] + float(channel_width),
    )
    data_to_writedriver_window.update(
        {
            "source_row": "DATA_DFF_ROW",
            "sink_block": "WRITEDRIVER",
            "source_side": "row_output_side_toward_write_driver",
            "sink_side": write_driver_side,
            "nets": [f"din_q[{bit}]" for bit in range(max(0, int(data_width)))],
            "write_driver_side_pin_known": bool(write_driver_pin_side_confirmed),
            "write_driver_input_side": write_driver_input_side,
            "metadata_only": True,
            "physical_routing_proven": False,
            "source_basis": "write_driver_gds_pin_audit_plus_metadata_row_hint",
            "budget_required_width": float(row_to_write_driver_required_width),
            "window_budget_pass": float(data_to_writedriver_window["height"]) >= float(row_to_write_driver_required_width),
        }
    )

    write_driver_preview_bbox = None
    if write_driver_bbox:
        array_width = max(0, int(data_width)) * max(0.0, float(write_driver_bbox["x1"]) - float(write_driver_bbox["x0"]))
        write_driver_preview_bbox = {
            "x0": data_row_bbox["x0"],
            "y0": data_to_writedriver_window["y1"],
            "x1": data_row_bbox["x0"] + array_width,
            "y1": data_to_writedriver_window["y1"] + max(0.0, float(write_driver_bbox["y1"]) - float(write_driver_bbox["y0"])),
        }

    keepouts = [
        _keepout("CLOCK_CHANNEL_KEEPOUT", "reserve control-side clock ingress band", clock_window, clock_window["nets"]),
        _keepout("ADDR_TO_DECODER_KEEPOUT", "reserve addr_q bus band toward decoder side", addr_to_decoder_window, addr_to_decoder_window["nets"]),
        _keepout(
            "DATA_TO_WRITEDRIVER_KEEPOUT",
            "reserve din_q bus band toward write-driver input side",
            data_to_writedriver_window,
            data_to_writedriver_window["nets"],
        ),
    ]

    row_bboxes = {
        "ADDR_DFF_ROW": addr_row_bbox,
        "DATA_DFF_ROW": data_row_bbox,
    }
    for keepout in keepouts:
        keepout["overlaps_dff_rows"] = {
            name: _overlaps(keepout, bbox)
            for name, bbox in row_bboxes.items()
        }
        keepout["overlaps_known_hardmacro"] = (
            _overlaps(keepout, write_driver_preview_bbox) if write_driver_preview_bbox and keepout["keepout_name"] == "DATA_TO_WRITEDRIVER_KEEPOUT" else False
        )
        keepout["keepout_is_metadata_only"] = True
        keepout["keepout_enforced_in_layout"] = False
        keepout["physical_routing_proven"] = False

    keepout_conflict_found = any(any(flags.values()) for flags in (k["overlaps_dff_rows"] for k in keepouts))
    hardmacro_overlap_found = any(bool(k["overlaps_known_hardmacro"]) for k in keepouts)
    geometry_window_budget_pass = bool(
        clock_window["window_budget_pass"]
        and addr_to_decoder_window["window_budget_pass"]
        and data_to_writedriver_window["window_budget_pass"]
    )
    geometry_contradiction = keepout_conflict_found or hardmacro_overlap_found or not geometry_window_budget_pass

    blockers = [
        "Decoder input side is still not pin-proven at hardmacro level.",
        "All geometry windows and keepouts remain metadata-only; no physical routing exists yet.",
        "Clock skew and real clock tree distribution remain unchecked.",
        "Shared rail and integrated control-row legalization are still out of scope.",
    ]
    if geometry_contradiction:
        blockers.insert(0, "At least one geometry window or keepout conflicts with the current metadata model.")

    return {
        "addr_width": int(addr_width),
        "data_width": int(data_width),
        "dff_row_bboxes": row_bboxes,
        "geometry_windows": [clock_window, addr_to_decoder_window, data_to_writedriver_window],
        "keepout_rectangles": keepouts,
        "write_driver_preview_bbox": write_driver_preview_bbox,
        "decoder_side_geometry_proven": False,
        "write_driver_pin_side_confirmed": bool(write_driver_pin_side_confirmed),
        "geometry_window_budget_pass": geometry_window_budget_pass,
        "keepout_conflict_found": keepout_conflict_found,
        "hardmacro_overlap_found": hardmacro_overlap_found,
        "decoder_pin_proof_required": True,
        "clock_window_physical_access_proven": False,
        "physical_routing_proven": False,
        "clock_skew_checked": False,
        "shared_rail_enabled": False,
        "safe_for_geometry_window_metadata": not geometry_contradiction,
        "can_enter_physical_row_placement": False,
        "can_enter_standalone_control_placement": False,
        "blockers": blockers,
    }


def _row_bbox(origin_x: float, origin_y: float, bit_count: int, pitch_x: float, dff_width: float, row_height: float) -> dict[str, float]:
    width = 0.0 if bit_count <= 0 else float(dff_width) + max(0, int(bit_count) - 1) * float(pitch_x)
    return {
        "x0": float(origin_x),
        "y0": float(origin_y),
        "x1": float(origin_x) + width,
        "y1": float(origin_y) + float(row_height),
        "width": width,
        "height": float(row_height),
    }


def _rect(name: str, x0: float, y0: float, x1: float, y1: float) -> dict[str, float | str]:
    return {
        "window_name": name,
        "x0": float(min(x0, x1)),
        "y0": float(min(y0, y1)),
        "x1": float(max(x0, x1)),
        "y1": float(max(y0, y1)),
        "width": abs(float(x1) - float(x0)),
        "height": abs(float(y1) - float(y0)),
    }


def _keepout(name: str, purpose: str, source_window: dict[str, Any], nets: list[str]) -> dict[str, Any]:
    return {
        "keepout_name": name,
        "purpose": purpose,
        "x0": source_window["x0"],
        "y0": source_window["y0"],
        "x1": source_window["x1"],
        "y1": source_window["y1"],
        "width": source_window["width"],
        "height": source_window["height"],
        "reserved_nets": list(nets),
        "metadata_only": True,
    }


def _overlaps(a: dict[str, Any], b: dict[str, Any] | None) -> bool:
    if not b:
        return False
    return not (
        float(a["x1"]) <= float(b["x0"])
        or float(b["x1"]) <= float(a["x0"])
        or float(a["y1"]) <= float(b["y0"])
        or float(b["y1"]) <= float(a["y0"])
    )
