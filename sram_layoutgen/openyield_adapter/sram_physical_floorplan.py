from __future__ import annotations

from dataclasses import dataclass

from sram_layoutgen.openyield_adapter.sram_region_planner import RegionBox


@dataclass(frozen=True)
class RegionPlacement:
    region_name: str
    box: RegionBox
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "region_name": self.region_name,
            "bbox": self.box.to_dict(),
            "reason": self.reason,
        }
