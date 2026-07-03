from __future__ import annotations

from typing import Any


def control_route_specs() -> list[dict[str, Any]]:
    return [
        {"net_name": "precharge_en", "source": ("CONTROL_LOGIC", "precharge_en"), "target": ("precharge", "precharge_en")},
        {"net_name": "sense_en", "source": ("CONTROL_LOGIC", "sense_en"), "target": ("sense_amp", "en")},
        {"net_name": "write_en", "source": ("CONTROL_LOGIC", "write_en"), "target": ("write_driver", "en")},
        {"net_name": "wordline_en", "source": ("CONTROL_LOGIC", "wl_en"), "target": ("wordline_driver", "B")},
        {"net_name": "clk", "source": ("CONTROL_LOGIC", "clk"), "target": ("DFF_ROW", "clk")},
        {"net_name": "gated_clk", "source": ("CONTROL_LOGIC", "gated_clk"), "target": ("GATED_CLOCK_PATH", "gated_clk")},
        {"net_name": "rbl_delay", "source": ("DELAY_CHAIN", "delay_out"), "target": ("replica_array", "RBL")},
    ]
