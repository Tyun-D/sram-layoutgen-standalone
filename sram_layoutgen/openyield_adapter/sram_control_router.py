from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ControlRouteSpec:
    net_name: str
    source_module: str
    target_module: str
    source_pin: str
    target_pin: str
    route_geometry_bbox: dict[str, float]
    routing_status: str
    uses_contract_pin: bool
    next_required_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "net_name": self.net_name,
            "source_module": self.source_module,
            "target_module": self.target_module,
            "source_pin": self.source_pin,
            "target_pin": self.target_pin,
            "route_geometry_bbox": self.route_geometry_bbox,
            "routing_status": self.routing_status,
            "uses_contract_pin": self.uses_contract_pin,
            "next_required_action": self.next_required_action,
        }
