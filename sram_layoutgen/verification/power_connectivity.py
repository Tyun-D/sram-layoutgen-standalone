from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate_power_summary(summary: dict[str, Any]) -> list[str]:
    codes: list[str] = []
    if not summary["drc_clean"]:
        codes.append("DRC_NOT_CLEAN")
    if not summary["row_side_clean"]:
        codes.append("ROW_SIDE_AUDIT_FAILED")
    if summary["missing_vdd_pins"] != 0:
        codes.append("CHILD_VDD_ENDPOINT_MISSING")
    if summary["missing_gnd_pins"] != 0:
        codes.append("CHILD_VSS_ENDPOINT_MISSING")
    if summary["guide_only_power_connections"] != 0:
        codes.append("GUIDE_ONLY_POWER_CONNECTION")
    if summary["macros_without_power_pin_contract"] != 0:
        codes.append("POWER_PIN_CONTRACT_MISSING")
    if not summary["array_clean"]:
        codes.append("ARRAY_POWER_STITCH_AUDIT_FAILED")
    if summary["row_vdd_rails_expected"] != summary["row_vdd_rails_connected"]:
        codes.append("MISSING_VDD_SEGMENT")
    if summary["row_gnd_rails_expected"] != summary["row_gnd_rails_connected"]:
        codes.append("MISSING_VSS_SEGMENT")
    if summary["rows_missing_vdd_connection"] != 0:
        codes.append("ARRAY_ROW_VDD_DISCONNECTED")
    if summary["rows_missing_gnd_connection"] != 0:
        codes.append("ARRAY_ROW_VSS_DISCONNECTED")
    if not summary["left_vdd_strap_present"] or not summary["right_vdd_strap_present"]:
        codes.append("TOP_LEVEL_VDD_STRAP_MISSING")
    if not summary["left_gnd_strap_present"] or not summary["right_gnd_strap_present"]:
        codes.append("TOP_LEVEL_VSS_STRAP_MISSING")
    if not summary["top_ring_vdd_connected"] or not summary["array_vdd_connected_to_top_vdd"] or not summary["peripheral_vdd_connected_to_top_vdd"]:
        codes.append("VDD_TO_TOP_COMPONENT_BROKEN")
    if not summary["top_ring_gnd_connected"] or not summary["array_gnd_connected_to_top_gnd"] or not summary["peripheral_gnd_connected_to_top_gnd"]:
        codes.append("VSS_TO_TOP_COMPONENT_BROKEN")
    if not summary["array_and_peripheral_vdd_same_component"] or not summary["array_and_peripheral_gnd_same_component"]:
        codes.append("POWER_COMPONENT_SPLIT")
    if not summary["vdd_gnd_short_free"]:
        codes.append("VDD_VSS_SHORT")
    if summary["global_guide_only_power_links"] != 0:
        codes.append("GUIDE_ONLY_GLOBAL_POWER_LINK")
    if not summary["topology_clean"]:
        codes.append("POWER_JUNCTION_TOPOLOGY_FAILED")
    if summary["missing_junctions"] != 0:
        codes.append("MISSING_POWER_VIA")
    if summary["unnecessary_jogs"] != 0:
        codes.append("UNNECESSARY_POWER_JOG")
    if summary["guide_only_junctions"] != 0:
        codes.append("GUIDE_ONLY_POWER_JUNCTION")
    if summary["suspicious_power_routes"] != 0:
        codes.append("POWER_TO_SIGNAL_CONTACT")
    return codes


def summarize_power_report(path: Path) -> dict[str, Any]:
    report = load_json(path)
    row_side = report.get("row_side_power_audit", {})
    array = report.get("array_power_stitching_audit", {})
    global_power = report.get("global_power_consistency_audit", {})
    topology = report.get("power_junction_topology_audit", {})

    summary = {
        "source_report": str(path),
        "config_name": report.get("name", path.stem),
        "word_size": report.get("word_size"),
        "num_words": report.get("num_words"),
        "words_per_row": report.get("words_per_row"),
        "drc_clean": bool(report.get("drc_clean", False)),
        "row_side_clean": bool(row_side.get("clean", False)),
        "missing_vdd_pins": len(row_side.get("missing_vdd_pins", [])),
        "missing_gnd_pins": len(row_side.get("missing_gnd_pins", [])),
        "guide_only_power_connections": len(row_side.get("guide_only_power_connections", [])),
        "macros_without_power_pin_contract": len(row_side.get("macros_without_power_pin_contract", [])),
        "checked_power_pins": len(row_side.get("checked_power_pins", [])),
        "array_clean": bool(array.get("clean", False)),
        "array_rows_checked": int(array.get("array_rows_checked", 0)),
        "row_vdd_rails_expected": int(array.get("row_vdd_rails_expected", 0)),
        "row_vdd_rails_connected": int(array.get("row_vdd_rails_connected", 0)),
        "row_gnd_rails_expected": int(array.get("row_gnd_rails_expected", 0)),
        "row_gnd_rails_connected": int(array.get("row_gnd_rails_connected", 0)),
        "rows_missing_vdd_connection": len(array.get("rows_missing_vdd_connection", [])),
        "rows_missing_gnd_connection": len(array.get("rows_missing_gnd_connection", [])),
        "left_vdd_strap_present": bool(array.get("left_vdd_strap", {}).get("present", False)),
        "left_gnd_strap_present": bool(array.get("left_gnd_strap", {}).get("present", False)),
        "right_vdd_strap_present": bool(array.get("right_vdd_strap", {}).get("present", False)),
        "right_gnd_strap_present": bool(array.get("right_gnd_strap", {}).get("present", False)),
        "top_ring_vdd_connected": bool(array.get("top_ring_connection", {}).get("vdd", False)),
        "top_ring_gnd_connected": bool(array.get("top_ring_connection", {}).get("gnd", False)),
        "global_clean": bool(global_power.get("clean", False)),
        "array_vdd_connected_to_top_vdd": bool(global_power.get("array_vdd_connected_to_top_vdd", False)),
        "array_gnd_connected_to_top_gnd": bool(global_power.get("array_gnd_connected_to_top_gnd", False)),
        "peripheral_vdd_connected_to_top_vdd": bool(global_power.get("peripheral_vdd_connected_to_top_vdd", False)),
        "peripheral_gnd_connected_to_top_gnd": bool(global_power.get("peripheral_gnd_connected_to_top_gnd", False)),
        "array_and_peripheral_vdd_same_component": bool(global_power.get("array_and_peripheral_vdd_same_component", False)),
        "array_and_peripheral_gnd_same_component": bool(global_power.get("array_and_peripheral_gnd_same_component", False)),
        "vdd_gnd_short_free": bool(global_power.get("vdd_gnd_short_free", False)),
        "global_guide_only_power_links": len(global_power.get("guide_only_power_links", [])),
        "topology_clean": bool(topology.get("clean", False)),
        "checked_junctions": len(topology.get("checked_junctions", [])),
        "missing_junctions": len(topology.get("missing_junctions", [])),
        "unnecessary_jogs": len(topology.get("unnecessary_jogs", [])),
        "guide_only_junctions": len(topology.get("guide_only_junctions", [])),
        "suspicious_power_routes": len(topology.get("suspicious_power_routes", [])),
    }
    summary["rejection_codes"] = evaluate_power_summary(summary)
    summary["power_gate_passed"] = not summary["rejection_codes"]
    return summary
