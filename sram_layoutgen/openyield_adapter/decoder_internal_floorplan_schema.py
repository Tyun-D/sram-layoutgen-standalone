from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class DecoderPlacementRecord:
    instance: str
    logical_type: str
    asset_sha: str
    x: float
    y: float
    orientation: str
    movable: bool
    allowed_orientations: tuple[str, ...]
    row_id: int
    anchor: str = "LEFT_BOTTOM"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecoderCandidateRow:
    row_id: int
    direction: str
    y: float
    height: float
    keepout_above: float = 0.0
    keepout_below: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecoderRoutePolicy:
    input_bus_layer: str
    output_bus_layer: str
    internal_branch_layer: str
    power_layer: str
    route_style: str
    allow_zero_gap_abutment: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class DecoderChildCandidate:
    child_name: str
    candidate_id: str
    candidate_type: str
    placement_records: list[DecoderPlacementRecord]
    rows: list[DecoderCandidateRow]
    route_policy: DecoderRoutePolicy
    notes: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)

    def bbox(self, instance_sizes: dict[str, tuple[float, float]]) -> list[float]:
        if not self.placement_records:
            return [0.0, 0.0, 0.0, 0.0]
        x0 = min(record.x for record in self.placement_records)
        y0 = min(record.y for record in self.placement_records)
        x1 = max(record.x + instance_sizes[record.instance][0] for record in self.placement_records)
        y1 = max(record.y + instance_sizes[record.instance][1] for record in self.placement_records)
        return [round(x0, 6), round(y0, 6), round(x1, 6), round(y1, 6)]

    def to_dict(self) -> dict[str, Any]:
        return {
            "child_name": self.child_name,
            "candidate_id": self.candidate_id,
            "candidate_type": self.candidate_type,
            "placement_records": [record.to_dict() for record in self.placement_records],
            "rows": [row.to_dict() for row in self.rows],
            "route_policy": self.route_policy.to_dict(),
            "notes": list(self.notes),
            "metrics": dict(self.metrics),
        }


@dataclass(frozen=True)
class DecoderCandidateScore:
    child_name: str
    candidate_id: str
    candidate_type: str
    bbox_width: float
    bbox_height: float
    area: float
    aspect_ratio: float
    instance_gap_sum: float
    zero_gap_pair_count: int
    internal_hpwl: float
    route_length: float
    maximum_net_length: float
    via_count: int
    crossing_count: int
    routing_channel_demand: float
    power_rail_length: float
    pin_access_margin: float
    output_pin_monotonicity: bool
    output_pin_pitch: float
    gate_passed: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def candidate_metric_defaults() -> dict[str, Any]:
    return {
        "bbox_width": 0.0,
        "bbox_height": 0.0,
        "area": 0.0,
        "aspect_ratio": 0.0,
        "instance_gap_sum": 0.0,
        "zero_gap_pair_count": 0,
        "internal_hpwl": 0.0,
        "route_length": 0.0,
        "maximum_net_length": 0.0,
        "via_count": 0,
        "crossing_count": 0,
        "routing_channel_demand": 0.0,
        "power_rail_length": 0.0,
        "pin_access_margin": 0.0,
        "output_pin_monotonicity": False,
        "output_pin_pitch": 0.0,
        "gate_passed": False,
    }

