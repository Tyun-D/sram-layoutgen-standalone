from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class PowerRouteSpec:
    net_name: str
    region: str
    affected_modules: tuple[str, ...]
    shape_bbox: dict[str, float]
    layer_hint: str
    power_status: str
    next_required_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "net_name": self.net_name,
            "region": self.region,
            "affected_modules": list(self.affected_modules),
            "shape_bbox": self.shape_bbox,
            "layer_hint": self.layer_hint,
            "power_status": self.power_status,
            "next_required_action": self.next_required_action,
        }
