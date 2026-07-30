from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


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
    summary["power_gate_passed"] = all(
        [
            summary["drc_clean"],
            summary["row_side_clean"],
            summary["missing_vdd_pins"] == 0,
            summary["missing_gnd_pins"] == 0,
            summary["guide_only_power_connections"] == 0,
            summary["macros_without_power_pin_contract"] == 0,
            summary["array_clean"],
            summary["row_vdd_rails_expected"] == summary["row_vdd_rails_connected"],
            summary["row_gnd_rails_expected"] == summary["row_gnd_rails_connected"],
            summary["rows_missing_vdd_connection"] == 0,
            summary["rows_missing_gnd_connection"] == 0,
            summary["left_vdd_strap_present"],
            summary["left_gnd_strap_present"],
            summary["right_vdd_strap_present"],
            summary["right_gnd_strap_present"],
            summary["top_ring_vdd_connected"],
            summary["top_ring_gnd_connected"],
            summary["global_clean"],
            summary["array_vdd_connected_to_top_vdd"],
            summary["array_gnd_connected_to_top_gnd"],
            summary["peripheral_vdd_connected_to_top_vdd"],
            summary["peripheral_gnd_connected_to_top_gnd"],
            summary["array_and_peripheral_vdd_same_component"],
            summary["array_and_peripheral_gnd_same_component"],
            summary["vdd_gnd_short_free"],
            summary["global_guide_only_power_links"] == 0,
            summary["topology_clean"],
            summary["missing_junctions"] == 0,
            summary["unnecessary_jogs"] == 0,
            summary["guide_only_junctions"] == 0,
        ]
    )
    return summary
