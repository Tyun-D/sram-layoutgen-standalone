from __future__ import annotations

from typing import Any


def wordline_route_specs() -> list[dict[str, Any]]:
    return [{"net_name": f"WL[{idx}]", "row_index": idx} for idx in range(4)]
