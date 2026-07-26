from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WordlineRouteSpec:
    net_name: str
    source_instance: str
    source_pin: str
    target_instance: str
    target_pin: str
    layer_hint: str
    shape_bbox: dict[str, float]
    routing_status: str
    uses_contract_pin: bool
    next_required_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "net_name": self.net_name,
            "source_instance": self.source_instance,
            "source_pin": self.source_pin,
            "target_instance": self.target_instance,
            "target_pin": self.target_pin,
            "layer_hint": self.layer_hint,
            "shape_bbox": self.shape_bbox,
            "routing_status": self.routing_status,
            "uses_contract_pin": self.uses_contract_pin,
            "next_required_action": self.next_required_action,
        }
