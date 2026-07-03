from __future__ import annotations

from sram_layoutgen.openyield_adapter.geometry_power_planner import top_power_pin_bbox


def top_power_pin_specs(vdd_strap_bbox: dict[str, float], gnd_strap_bbox: dict[str, float]) -> list[dict[str, object]]:
    return [
        {
            "pin_name": "VDD",
            "net_name": "VDD",
            "label_text": "VDD",
            "connected_strap": "vdd_strap",
            "bbox": top_power_pin_bbox(vdd_strap_bbox, "left"),
        },
        {
            "pin_name": "GND",
            "net_name": "GND",
            "label_text": "GND",
            "connected_strap": "gnd_strap",
            "bbox": top_power_pin_bbox(gnd_strap_bbox, "right"),
        },
    ]
