"""Aggregation footprint metadata for OpenYield/layoutgen macro matching.

This module is intentionally descriptive only.  It does not place cells,
modify the GDS flow, or infer geometry from GDS files.  It converts available
replacement macro JSON metadata into a conservative footprint contract that a
future placement engine can consume.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


ABUTMENT_READY = "abutment_ready"
NOT_ABUTMENT_READY = "not_abutment_ready"
UNKNOWN_NEED_GDS_PIN_AUDIT = "unknown_need_gds_pin_audit"
COMPOSITE_REQUIRED = "composite_required"
UNSUPPORTED_ARCHITECTURE = "unsupported_architecture"
NON_LAYOUT_SOURCE = "non_layout_source"
NEEDS_STDCELL_OR_GENERATED_LAYOUT = "needs_stdcell_or_generated_layout"


@dataclass(frozen=True)
class PowerRail:
    net: str
    layer: str
    orientation: str
    side: str
    track: float | None = None
    width: float | None = None
    can_share_with_neighbor: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AbutmentRule:
    side: str
    compatible_roles: tuple[str, ...]
    share_power_rails: bool
    min_gap: float
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AggregationFootprint:
    macro_name: str
    role: str
    width: float
    height: float
    left_rails: tuple[PowerRail, ...] = ()
    right_rails: tuple[PowerRail, ...] = ()
    top_rails: tuple[PowerRail, ...] = ()
    bottom_rails: tuple[PowerRail, ...] = ()
    abutment_rules: tuple[AbutmentRule, ...] = ()
    pin_access_sides: dict[str, tuple[str, ...]] = field(default_factory=dict)
    status: str = UNKNOWN_NEED_GDS_PIN_AUDIT
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["left_rails"] = [rail.to_dict() for rail in self.left_rails]
        data["right_rails"] = [rail.to_dict() for rail in self.right_rails]
        data["top_rails"] = [rail.to_dict() for rail in self.top_rails]
        data["bottom_rails"] = [rail.to_dict() for rail in self.bottom_rails]
        data["abutment_rules"] = [rule.to_dict() for rule in self.abutment_rules]
        return data


def aggregation_status_for_contract(role: str, implementation_status: str, has_macro: bool) -> str:
    if implementation_status == UNSUPPORTED_ARCHITECTURE:
        return UNSUPPORTED_ARCHITECTURE
    if implementation_status == NON_LAYOUT_SOURCE:
        return NON_LAYOUT_SOURCE
    if implementation_status == COMPOSITE_REQUIRED:
        return COMPOSITE_REQUIRED
    if implementation_status == NEEDS_STDCELL_OR_GENERATED_LAYOUT:
        return NEEDS_STDCELL_OR_GENERATED_LAYOUT
    if role in {"bitcell", "dummy", "replica"}:
        return ABUTMENT_READY if has_macro else UNKNOWN_NEED_GDS_PIN_AUDIT
    if role in {"precharge", "sense_amp", "write_driver", "wordline_driver", "column_mux"}:
        return UNKNOWN_NEED_GDS_PIN_AUDIT if has_macro else NOT_ABUTMENT_READY
    if role in {"support_cell", "control_timing"}:
        return UNKNOWN_NEED_GDS_PIN_AUDIT if has_macro else NEEDS_STDCELL_OR_GENERATED_LAYOUT
    return UNKNOWN_NEED_GDS_PIN_AUDIT if has_macro else NOT_ABUTMENT_READY


def build_aggregation_footprint(macro: dict[str, Any], role: str, implementation_status: str) -> AggregationFootprint:
    width = float(macro.get("width") or 0.0)
    height = float(macro.get("height") or 0.0)
    pins = tuple(macro.get("pins") or ())
    rails = [_power_rail_from_pin(pin, width, height) for pin in pins if _is_power_pin(pin)]
    top = tuple(rail for rail in rails if rail.side == "top")
    bottom = tuple(rail for rail in rails if rail.side == "bottom")
    left = tuple(rail for rail in rails if rail.side == "left")
    right = tuple(rail for rail in rails if rail.side == "right")
    pin_access = _pin_access_sides(pins, width, height)
    status = aggregation_status_for_contract(role, implementation_status, has_macro=True)
    return AggregationFootprint(
        macro_name=str(macro.get("name") or ""),
        role=role,
        width=width,
        height=height,
        left_rails=left,
        right_rails=right,
        top_rails=top,
        bottom_rails=bottom,
        abutment_rules=_abutment_rules(role, bool(top or bottom or left or right)),
        pin_access_sides=pin_access,
        status=status,
        notes=_footprint_notes(role, status, rails),
    )


def _is_power_pin(pin: dict[str, Any]) -> bool:
    name = str(pin.get("name") or "").lower()
    use = str(pin.get("use") or "").upper()
    return name in {"vdd", "vss", "gnd"} or use in {"POWER", "GROUND"}


def _power_rail_from_pin(pin: dict[str, Any], width: float, height: float) -> PowerRail:
    name = str(pin.get("name") or "")
    net = "gnd" if name.lower() in {"gnd", "vss"} else "vdd"
    layer = str(pin.get("layer") or "unknown")
    x = _float_or_none(pin.get("x"))
    y = _float_or_none(pin.get("y"))
    side = _pin_side(x, y, width, height)
    orientation = "horizontal" if side in {"top", "bottom"} else "vertical"
    return PowerRail(
        net=net,
        layer=layer,
        orientation=orientation,
        side=side,
        track=y if orientation == "horizontal" else x,
        width=_float_or_none(pin.get("width")),
        can_share_with_neighbor=side in {"top", "bottom", "left", "right"},
    )


def _pin_access_sides(pins: tuple[dict[str, Any], ...], width: float, height: float) -> dict[str, tuple[str, ...]]:
    access: dict[str, set[str]] = {}
    for pin in pins:
        name = str(pin.get("name") or "")
        side = _pin_side(_float_or_none(pin.get("x")), _float_or_none(pin.get("y")), width, height)
        access.setdefault(name, set()).add(side)
    return {name: tuple(sorted(sides)) for name, sides in sorted(access.items())}


def _abutment_rules(role: str, has_boundary_power: bool) -> tuple[AbutmentRule, ...]:
    if role in {"bitcell", "dummy", "replica"}:
        return (
            AbutmentRule("left", ("bitcell", "dummy", "replica"), True, 0.0, ("SRAM array cells normally abut horizontally.",)),
            AbutmentRule("right", ("bitcell", "dummy", "replica"), True, 0.0, ("SRAM array cells normally abut horizontally.",)),
            AbutmentRule("top", ("bitcell", "dummy", "replica"), True, 0.0, ("SRAM array rows may share rails when GDS pins confirm continuity.",)),
            AbutmentRule("bottom", ("bitcell", "dummy", "replica"), True, 0.0, ("SRAM array rows may share rails when GDS pins confirm continuity.",)),
        )
    if role in {"precharge", "sense_amp", "write_driver", "column_mux", "wordline_driver", "support_cell"}:
        return (
            AbutmentRule("left", (role,), has_boundary_power, 0.0, ("Requires GDS pin/DRC audit before enabling no-gap abutment.",)),
            AbutmentRule("right", (role,), has_boundary_power, 0.0, ("Requires GDS pin/DRC audit before enabling no-gap abutment.",)),
        )
    return ()


def _footprint_notes(role: str, status: str, rails: list[PowerRail]) -> tuple[str, ...]:
    notes: list[str] = []
    if status == UNKNOWN_NEED_GDS_PIN_AUDIT:
        notes.append("Replacement macro JSON has bbox/pin centers, but full GDS pin shapes are still needed before enabling physical abutment.")
    if role in {"precharge", "sense_amp", "write_driver", "column_mux"}:
        notes.append("Column-side circuits need bitline pitch and power rail continuity checks before sharing rails.")
    if not rails:
        notes.append("No power/ground rail was found in replacement macro metadata.")
    return tuple(notes)


def _pin_side(x: float | None, y: float | None, width: float, height: float) -> str:
    eps = 1e-6
    if y is not None and abs(y) <= eps:
        return "bottom"
    if y is not None and height and abs(y - height) <= 0.2:
        return "top"
    if x is not None and abs(x) <= eps:
        return "left"
    if x is not None and width and abs(x - width) <= 0.2:
        return "right"
    return "internal"


def _float_or_none(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
