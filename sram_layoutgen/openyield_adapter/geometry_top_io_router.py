from __future__ import annotations

from typing import Any


def top_io_route_specs() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx in range(4):
        rows.append({"pin_name": f"A[{idx}]", "net_name": f"A[{idx}]", "pin_category": "ADDRESS", "target": ("row_decoder", f"A[{idx}]")})
    for idx in range(4):
        rows.append({"pin_name": f"DIN[{idx}]", "net_name": f"DIN[{idx}]", "pin_category": "DATA_IN", "target": ("write_driver", "din")})
    for idx in range(4):
        rows.append({"pin_name": f"DOUT[{idx}]", "net_name": f"DOUT[{idx}]", "pin_category": "DATA_OUT", "target": ("sense_amp", "dout")})
    rows.extend(
        [
            {"pin_name": "clk", "net_name": "clk", "pin_category": "CLOCK", "target": ("CONTROL_LOGIC", "clk")},
            {"pin_name": "csb", "net_name": "csb", "pin_category": "CONTROL", "target": ("CONTROL_LOGIC", "cs")},
            {"pin_name": "web", "net_name": "web", "pin_category": "CONTROL", "target": ("CONTROL_LOGIC", "we")},
        ]
    )
    return rows
