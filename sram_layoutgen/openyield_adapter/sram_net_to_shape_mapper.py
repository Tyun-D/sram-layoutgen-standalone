from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class NetShapeSpec:
    net_name: str
    net_category: str
    source_instance: str
    source_pin: str
    target_instance: str
    target_pin: str
    shape_type: str
    shape_bbox: dict[str, float]
    layer_hint: str
    route_group: str
    routing_status: str
    uses_contract_pin: bool
    uses_approximate_geometry: bool
    required_for_lvs_later: bool
    next_required_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "net_name": self.net_name,
            "net_category": self.net_category,
            "source_instance": self.source_instance,
            "source_pin": self.source_pin,
            "target_instance": self.target_instance,
            "target_pin": self.target_pin,
            "shape_type": self.shape_type,
            "shape_bbox": self.shape_bbox,
            "layer_hint": self.layer_hint,
            "route_group": self.route_group,
            "routing_status": self.routing_status,
            "uses_contract_pin": self.uses_contract_pin,
            "uses_approximate_geometry": self.uses_approximate_geometry,
            "required_for_lvs_later": self.required_for_lvs_later,
            "next_required_action": self.next_required_action,
        }
