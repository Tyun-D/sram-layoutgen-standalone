from __future__ import annotations

from pathlib import Path
from typing import Any

import gdstk


def build_floorplan_interface_plan(
    *,
    layoutgen_golden: Path,
    openram_reference_gds: Path,
    mapping_summary: dict[str, Any],
) -> dict[str, Any]:
    golden_lib = gdstk.read_gds(layoutgen_golden)
    openram_lib = gdstk.read_gds(openram_reference_gds)
    golden_top = golden_lib.top_level()[0]
    openram_top = openram_lib.top_level()[0]
    golden_bbox = _bbox(golden_top.bounding_box())
    openram_bbox = _bbox(openram_top.bounding_box())

    candidate_region = {
        "placement_strategy": "LEFT_SIDE_CONTROL_REGION_WITH_DECODER_ADJACENCY",
        "region_bbox_relative": {
            "x0": -0.18,
            "y0": 0.18,
            "x1": -0.02,
            "y1": 0.92,
        },
        "why": "OpenRAM places control logic beside the array/decoder edge, while the current layoutgen golden lacks an explicit OpenYield control block. A left-side control strip keeps replica/decoder/wordline adjacency clear and preserves vertical access to the array edge.",
    }
    interface_nets = [
        {"net_name": "clk", "role": "input", "direction": "top_or_left_entry", "consumer_or_producer": "TIME", "adjacent_module": "TIME"},
        {"net_name": "csb", "role": "input", "direction": "top_or_left_entry", "consumer_or_producer": "TIME", "adjacent_module": "TIME"},
        {"net_name": "web", "role": "input", "direction": "top_or_left_entry", "consumer_or_producer": "TIME", "adjacent_module": "TIME"},
        {"net_name": "A[*]", "role": "input", "direction": "left_entry_toward_decoder", "consumer_or_producer": "ADDR_DFF/TIME", "adjacent_module": "DECODER_CASCADE"},
        {"net_name": "DIN[*]", "role": "input", "direction": "left_or_bottom_entry_for_write_path", "consumer_or_producer": "DATA_DFF/TIME", "adjacent_module": "WRITEDRIVER"},
        {"net_name": "rbl", "role": "input", "direction": "right_entry_from_replica", "consumer_or_producer": "TIME", "adjacent_module": "replica_column"},
        {"net_name": "wl_en", "role": "output", "direction": "right_toward_wordline_driver", "consumer_or_producer": "TIME", "adjacent_module": "WORDLINEDRIVER"},
        {"net_name": "PRE", "role": "output", "direction": "top_or_right_toward_precharge", "consumer_or_producer": "TIME", "adjacent_module": "PRECHARGE"},
        {"net_name": "s_en", "role": "output", "direction": "top_or_right_toward_sense_amp", "consumer_or_producer": "TIME", "adjacent_module": "SENSEAMP"},
        {"net_name": "w_en", "role": "output", "direction": "bottom_or_right_toward_write_driver", "consumer_or_producer": "TIME", "adjacent_module": "WRITEDRIVER"},
        {"net_name": "VDD", "role": "power", "direction": "horizontal_rail_handoff", "consumer_or_producer": "TIME and neighbor rows", "adjacent_module": "global_power"},
        {"net_name": "VSS", "role": "ground", "direction": "horizontal_rail_handoff", "consumer_or_producer": "TIME and neighbor rows", "adjacent_module": "global_power"},
    ]

    return {
        "candidate_control_region_defined": True,
        "top_bbox_change_expected": True,
        "routing_channel_requirement_defined": True,
        "power_interface_requirement_defined": True,
        "candidate_region": candidate_region,
        "layoutgen_golden_bbox": golden_bbox,
        "openram_reference_bbox": openram_bbox,
        "decoder_adjacency": "Control region should abut or sit immediately left of decoder hierarchy.",
        "wordline_driver_adjacency": "wl_en should exit toward the wordline-driver edge with minimal cross-array routing.",
        "replica_bitline_input_position": "rbl should enter the control region from the replica-column side.",
        "precharge_enable_output_direction": "PRE should fan toward the precharge band at the top/side periphery.",
        "sense_enable_output_direction": "s_en should route toward the sense-amp band.",
        "write_enable_output_direction": "w_en should route toward the write-driver band.",
        "input_direction_policy": "clk/csb/web and address/data inputs should enter from top/left IO channels, not through the array center.",
        "power_interface_policy": "VDD/VSS must use continuous rail handoff; candidate OpenYield control composites expose only metadata-level rail exports today.",
        "routing_channel_notes": [
            "Reserve a vertical control channel between the left control strip and decoder/wordline-driver entry points.",
            "Reserve a top-side horizontal channel for PRE and sense-path fanout.",
            "Avoid forcing control routing through bitcell-array pin columns.",
        ],
        "interface_nets": interface_nets,
        "mapping_context": {
            "physical_ready_for_qualification_count": mapping_summary["physical_ready_for_qualification_count"],
            "physical_partial_count": mapping_summary["physical_partial_count"],
            "physical_missing_count": mapping_summary["physical_missing_count"],
        },
    }


def _bbox(box: tuple[tuple[float, float], tuple[float, float]] | None) -> dict[str, float] | None:
    if box is None:
        return None
    return {
        "x0": round(float(box[0][0]), 6),
        "y0": round(float(box[0][1]), 6),
        "x1": round(float(box[1][0]), 6),
        "y1": round(float(box[1][1]), 6),
        "width": round(float(box[1][0] - box[0][0]), 6),
        "height": round(float(box[1][1] - box[0][1]), 6),
    }
