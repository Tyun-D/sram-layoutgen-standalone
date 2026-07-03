from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TopPinSpec:
    pin_name: str
    pin_category: str
    geometry_bbox: dict[str, float]
    layer_hint: str
    label_text: str
    connected_internal_net: str
    pin_status: str
    uses_contract_mapping: bool
    next_required_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "pin_name": self.pin_name,
            "pin_category": self.pin_category,
            "geometry_bbox": self.geometry_bbox,
            "layer_hint": self.layer_hint,
            "label_text": self.label_text,
            "connected_internal_net": self.connected_internal_net,
            "pin_status": self.pin_status,
            "uses_contract_mapping": self.uses_contract_mapping,
            "next_required_action": self.next_required_action,
        }
