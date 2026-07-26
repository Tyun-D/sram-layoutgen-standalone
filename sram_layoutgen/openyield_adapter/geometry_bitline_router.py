from __future__ import annotations

from typing import Any


def bitline_route_specs() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx in range(4):
        rows.extend(
            [
                {"net_name": f"BL[{idx}]", "net_category": "BITLINE", "column_index": idx, "source": ("bitcell_array", f"BL[{idx}]"), "target": ("precharge", "bl")},
                {"net_name": f"BR[{idx}]", "net_category": "BITLINE_BAR", "column_index": idx, "source": ("bitcell_array", f"BR[{idx}]"), "target": ("precharge", "br")},
                {"net_name": f"BL[{idx}]", "net_category": "BITLINE", "column_index": idx, "source": ("bitcell_array", f"BL[{idx}]"), "target": ("column_mux", "bl")},
                {"net_name": f"BR[{idx}]", "net_category": "BITLINE_BAR", "column_index": idx, "source": ("bitcell_array", f"BR[{idx}]"), "target": ("column_mux", "br")},
                {"net_name": f"BL[{idx}]", "net_category": "BITLINE", "column_index": idx, "source": ("column_mux", "bl_out"), "target": ("sense_amp", "bl")},
                {"net_name": f"BR[{idx}]", "net_category": "BITLINE_BAR", "column_index": idx, "source": ("column_mux", "br_out"), "target": ("sense_amp", "br")},
                {"net_name": f"BL[{idx}]", "net_category": "BITLINE", "column_index": idx, "source": ("write_driver", "bl"), "target": ("bitcell_array", f"BL[{idx}]")},
                {"net_name": f"BR[{idx}]", "net_category": "BITLINE_BAR", "column_index": idx, "source": ("write_driver", "br"), "target": ("bitcell_array", f"BR[{idx}]")},
            ]
        )
    return rows
