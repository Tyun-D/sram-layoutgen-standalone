"""Metadata-only control target envelope helpers for OpenYield control rows."""

from __future__ import annotations

from typing import Any


def build_control_target_envelopes(
    anchor_binding: dict[str, Any],
    geometry_windows: dict[str, Any],
    addr_width: int,
    data_width: int,
    channel_width: float,
    row_height: float,
    decoder_envelope_policy: str,
    write_driver_target_policy: str,
    route_pitch: float = 0.2,
    route_margin: float = 0.2,
) -> dict[str, Any]:
    decoder_anchor = anchor_binding["decoder_anchor"]
    write_driver_anchor = anchor_binding["write_driver_anchor"]
    dff_rows = geometry_windows["dff_row_bboxes"]
    clock_keepout = next(
        item for item in geometry_windows["keepout_rectangle_list"] if item["keepout_name"] == "CLOCK_CHANNEL_KEEPOUT"
    )

    decoder_candidate_width = max(float(channel_width) * 2.0, float(addr_width) * float(route_pitch) + 2.0 * float(route_margin))
    decoder_candidate_height = float(row_height)
    decoder_envelope = {
        "envelope_name": "DECODER_CASCADE_ENVELOPE",
        "target_block": "DECODER_CASCADE",
        "envelope_policy": decoder_envelope_policy,
        "geometry_source": "decomposition_graph_plus_anchor_window",
        "pin_proven": False,
        "input_nets": [f"A[{bit}]" for bit in range(max(0, int(addr_width)))],
        "input_source_nets": [f"addr_q[{bit}]" for bit in range(max(0, int(addr_width)))],
        "input_anchor": decoder_anchor["anchor_name"],
        "input_window": decoder_anchor["source_window"],
        "input_side_hint": "decoder_input_side",
        "output_nets": ["WL[*]"],
        "output_consumer": "WORDLINEDRIVER.A / decoder_input",
        "output_side_hint": "wordline_driver_side",
        "metadata_only": True,
        "physical_access_proven": False,
        "physical_routing_proven": False,
        "candidate_bbox": {
            "x0": float(decoder_anchor["bbox"]["x1"]),
            "y0": float(decoder_anchor["bbox"]["y0"]),
            "x1": float(decoder_anchor["bbox"]["x1"]) + float(decoder_candidate_width),
            "y1": float(decoder_anchor["bbox"]["y0"]) + float(decoder_candidate_height),
        },
        "decoder_envelope_bbox_is_estimated": True,
        "decoder_candidate_bbox_is_metadata_only": True,
        "decoder_candidate_bbox_not_physical_layout": True,
        "decoder_hardmacro_pin_proven": False,
    }
    decoder_envelope["candidate_bbox"]["width"] = decoder_envelope["candidate_bbox"]["x1"] - decoder_envelope["candidate_bbox"]["x0"]
    decoder_envelope["candidate_bbox"]["height"] = decoder_envelope["candidate_bbox"]["y1"] - decoder_envelope["candidate_bbox"]["y0"]
    decoder_envelope_bound = _touches(decoder_envelope["candidate_bbox"], decoder_anchor["bbox"])

    write_driver_target = {
        "target_name": "WRITEDRIVER_ARRAY_INPUT_TARGET",
        "target_block": "WRITEDRIVER",
        "target_policy": write_driver_target_policy,
        "geometry_source": "write_driver_gds_pin_side",
        "write_driver_side_pin_known": True,
        "write_driver_input_side": "bottom",
        "input_nets": [f"DIN[{bit}]" for bit in range(max(0, int(data_width)))],
        "source_nets": [f"din_q[{bit}]" for bit in range(max(0, int(data_width)))],
        "source_window": write_driver_anchor["source_window"],
        "array_reference": "WRITEDRIVER column/data group input side",
        "metadata_only": True,
        "physical_access_proven": True,
        "physical_routing_proven": False,
        "target_bbox": dict(write_driver_anchor["bbox"]),
    }
    write_driver_target_bound = _touches(write_driver_target["target_bbox"], write_driver_anchor["bbox"])

    decoder_envelope_conflict_found = any(
        _overlaps(decoder_envelope["candidate_bbox"], bbox) for bbox in dff_rows.values()
    ) or _overlaps(decoder_envelope["candidate_bbox"], clock_keepout)
    write_driver_target_conflict_found = any(
        _overlaps(write_driver_target["target_bbox"], bbox) for bbox in dff_rows.values()
    )
    hardmacro_overlap_found = False

    blockers = [
        "Decoder envelope is still an estimated generated-block metadata box, not a physical decoder layout.",
        "Write-driver target is tied to GDS pin-side evidence, but no routed connection from DATA_DFF_ROW exists yet.",
        "No physical routing or clock skew proof exists for decoder/output handoff.",
        "Very-limited physical smoke still lacks decoder-side concrete layout evidence.",
    ]
    if decoder_envelope_conflict_found or write_driver_target_conflict_found:
        blockers.insert(0, "At least one envelope/target overlaps a forbidden metadata region.")

    return {
        "decoder_envelope": decoder_envelope,
        "write_driver_target": write_driver_target,
        "decoder_envelope_bound": decoder_envelope_bound,
        "write_driver_target_bound": write_driver_target_bound,
        "decoder_envelope_is_metadata_only": True,
        "decoder_hardmacro_pin_proven": False,
        "write_driver_target_uses_gds_pin_side": True,
        "decoder_envelope_conflict_found": decoder_envelope_conflict_found,
        "write_driver_target_conflict_found": write_driver_target_conflict_found,
        "hardmacro_overlap_found": hardmacro_overlap_found,
        "physical_routing_proven": False,
        "safe_for_target_envelope_metadata": bool(decoder_envelope_bound and write_driver_target_bound and not decoder_envelope_conflict_found and not write_driver_target_conflict_found),
        "can_enter_very_limited_physical_smoke": False,
        "can_enter_standalone_control_placement": False,
        "blockers": blockers,
    }


def _touches(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return not (
        float(a["x1"]) < float(b["x0"])
        or float(b["x1"]) < float(a["x0"])
        or float(a["y1"]) < float(b["y0"])
        or float(b["y1"]) < float(a["y0"])
    )


def _overlaps(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return not (
        float(a["x1"]) <= float(b["x0"])
        or float(b["x1"]) <= float(a["x0"])
        or float(a["y1"]) <= float(b["y0"])
        or float(b["y1"]) <= float(a["y0"])
    )
