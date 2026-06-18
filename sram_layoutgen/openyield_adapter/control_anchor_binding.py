"""Metadata-only anchor binding helpers for OpenYield control rows."""

from __future__ import annotations

from typing import Any


def build_control_anchor_binding(
    geometry_windows: dict[str, Any],
    decoder_anchor_policy: str,
    write_driver_anchor_policy: str,
    write_driver_bbox: dict[str, float] | None,
    write_driver_preview_bbox: dict[str, float] | None,
    addr_width: int,
    data_width: int,
) -> dict[str, Any]:
    dff_rows = geometry_windows["dff_row_bboxes"]
    decoder_window = geometry_windows["decoder_input_window"]
    write_driver_window = geometry_windows["write_driver_input_window"]
    keepouts = {item["keepout_name"]: item for item in geometry_windows["keepout_rectangle_list"]}

    decoder_anchor = {
        "anchor_name": "DECODER_INPUT_ANCHOR",
        "target_block": "DECODER_CASCADE",
        "anchor_policy": decoder_anchor_policy,
        "input_nets": [f"A[{bit}]" for bit in range(max(0, int(addr_width)))],
        "source_nets": [f"addr_q[{bit}]" for bit in range(max(0, int(addr_width)))],
        "source_window": decoder_window["window_name"],
        "geometry_source": "metadata_only" if decoder_anchor_policy == "metadata_window" else decoder_anchor_policy,
        "decoder_side_geometry_proven": False,
        "decoder_pin_proof_required": True,
        "physical_access_proven": False,
        "physical_routing_proven": False,
        "bbox": _copy_rect(decoder_window),
        "side_hint": decoder_window["sink_side"],
        "metadata_only": True,
        "decoder_anchor_geometry_source": "metadata_window",
    }

    write_driver_anchor_bbox = _write_driver_anchor_bbox(write_driver_window, write_driver_bbox)
    write_driver_anchor = {
        "anchor_name": "WRITEDRIVER_INPUT_ANCHOR",
        "target_block": "WRITEDRIVER",
        "anchor_policy": write_driver_anchor_policy,
        "input_nets": [f"DIN[{bit}]" for bit in range(max(0, int(data_width)))],
        "source_nets": [f"din_q[{bit}]" for bit in range(max(0, int(data_width)))],
        "source_window": write_driver_window["window_name"],
        "geometry_source": "write_driver_gds_pin_side" if write_driver_anchor_policy == "gds_pin_side" else write_driver_anchor_policy,
        "write_driver_side_pin_known": True,
        "write_driver_input_side": "bottom",
        "physical_access_proven": True,
        "physical_routing_proven": False,
        "bbox": write_driver_anchor_bbox,
        "side_hint": write_driver_window["sink_side"],
        "metadata_only": False if write_driver_anchor_policy == "gds_pin_side" else True,
    }

    decoder_anchor_bound = _touches(decoder_anchor["bbox"], decoder_window)
    write_driver_anchor_bound = _touches(write_driver_anchor["bbox"], write_driver_window)

    row_overlap = {
        "decoder_anchor": {name: _overlaps(decoder_anchor["bbox"], bbox) for name, bbox in dff_rows.items()},
        "write_driver_anchor": {name: _overlaps(write_driver_anchor["bbox"], bbox) for name, bbox in dff_rows.items()},
    }
    keepout_overlap = {
        "decoder_anchor": {name: _overlaps(decoder_anchor["bbox"], rect) for name, rect in keepouts.items()},
        "write_driver_anchor": {name: _overlaps(write_driver_anchor["bbox"], rect) for name, rect in keepouts.items()},
    }
    expected_keepout_binding = {
        "decoder_anchor": "ADDR_TO_DECODER_KEEPOUT",
        "write_driver_anchor": "DATA_TO_WRITEDRIVER_KEEPOUT",
    }

    anchor_keepout_conflict_found = any(
        overlaps
        for anchor_name, family in keepout_overlap.items()
        for keepout_name, overlaps in family.items()
        if keepout_name != expected_keepout_binding[anchor_name]
    )
    anchor_hardmacro_overlap_found = False
    anchor_binding_success = bool(decoder_anchor_bound and write_driver_anchor_bound)

    blockers = [
        "Decoder anchor is still metadata-only because DECODER_CASCADE is not a pin-proven hard macro.",
        "Write-driver anchor uses GDS pin-side evidence, but route completion is still unproven.",
        "No physical routing or clock skew proof exists for the bound anchors.",
        "Standalone control placement remains disabled until anchor binding is backed by real placement/legalization evidence.",
    ]
    if anchor_keepout_conflict_found or anchor_hardmacro_overlap_found:
        blockers.insert(0, "At least one anchor conflicts with a keepout or known hardmacro box.")
    if not anchor_binding_success:
        blockers.insert(0, "At least one required anchor could not be bound to its source window.")

    return {
        "decoder_anchor": decoder_anchor,
        "write_driver_anchor": write_driver_anchor,
        "decoder_side_geometry_proven": False,
        "write_driver_side_pin_known": True,
        "anchor_binding_success": anchor_binding_success,
        "decoder_anchor_bound": decoder_anchor_bound,
        "write_driver_anchor_bound": write_driver_anchor_bound,
        "decoder_anchor_is_metadata_only": True,
        "write_driver_anchor_uses_gds_pin_side": write_driver_anchor_policy == "gds_pin_side",
        "write_driver_preview_bbox": write_driver_preview_bbox,
        "anchor_row_overlap": row_overlap,
        "anchor_keepout_overlap": keepout_overlap,
        "expected_keepout_binding": expected_keepout_binding,
        "anchor_keepout_conflict_found": anchor_keepout_conflict_found,
        "anchor_hardmacro_overlap_found": anchor_hardmacro_overlap_found,
        "physical_routing_proven": False,
        "safe_for_anchor_binding_metadata": anchor_binding_success and not anchor_keepout_conflict_found and not anchor_hardmacro_overlap_found,
        "can_enter_limited_physical_smoke": False,
        "can_enter_standalone_control_placement": False,
        "blockers": blockers,
    }


def _copy_rect(rect: dict[str, Any]) -> dict[str, float]:
    return {
        "x0": float(rect["x0"]),
        "y0": float(rect["y0"]),
        "x1": float(rect["x1"]),
        "y1": float(rect["y1"]),
        "width": float(rect["width"]),
        "height": float(rect["height"]),
    }


def _write_driver_anchor_bbox(window: dict[str, Any], write_driver_bbox: dict[str, float] | None) -> dict[str, float]:
    if not write_driver_bbox:
        return _copy_rect(window)
    width = max(0.0, float(write_driver_bbox["x1"]) - float(write_driver_bbox["x0"]))
    anchor_height = min(float(window["height"]), max(0.0, float(write_driver_bbox["y1"]) - float(write_driver_bbox["y0"])))
    return {
        "x0": float(window["x0"]),
        "y0": float(window["y1"]) - anchor_height,
        "x1": float(window["x0"]) + width,
        "y1": float(window["y1"]),
        "width": width,
        "height": anchor_height,
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


def _inside(inner: dict[str, Any], outer: dict[str, Any]) -> bool:
    return (
        float(outer["x0"]) <= float(inner["x0"]) <= float(outer["x1"])
        and float(outer["x0"]) <= float(inner["x1"]) <= float(outer["x1"])
        and float(outer["y0"]) <= float(inner["y0"]) <= float(outer["y1"])
        and float(outer["y0"]) <= float(inner["y1"]) <= float(outer["y1"])
    )
