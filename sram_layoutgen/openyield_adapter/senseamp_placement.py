"""Placement-planning helpers for adapting OpenYield SENSEAMP to local macros.

This module intentionally stays at the metadata/planning layer.  It does not
change the main standalone placement flow, routing, or GDS writer.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from math import ceil
from pathlib import Path
from typing import Any

from .architecture_adapter import ModuleArchitectureAdapter, build_senseamp_architecture_adapter
from .gds_pin_audit import audit_macros


LOCAL_SENSEAMP_PINS = ("bl", "br", "dout", "en", "vdd", "gnd")


@dataclass(frozen=True)
class SenseAmpPlacement:
    instance_name: str
    macro_name: str
    col: int
    x: float
    y: float
    orientation: str
    nets: dict[str, str]
    dropped_pins: dict[str, str]
    adapter_strategy: str
    safe_for_physical_mapping: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SenseAmpPlacementPlan:
    cols: int
    mux_ratio: int
    placements: tuple[SenseAmpPlacement, ...]
    macro_name: str = "sense_amp"
    adapter_strategy: str = "single_ended_q_to_dout"
    requires_netlist_rewrite: bool = True
    requires_layout_pin: bool = False
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["placements"] = [item.to_dict() for item in self.placements]
        return data


@dataclass(frozen=True)
class SenseAmpPhysicalMacro:
    macro_name: str
    spice_pins: tuple[str, ...]
    gds_label_backed_pins: tuple[str, ...]
    q_to_dout_established: bool
    qb_to_dout_b_established: bool
    safe_for_physical_mapping: bool
    requires_netlist_rewrite: bool
    requires_layout_pin: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def inspect_local_senseamp_macro(tech_dir: str | Path) -> SenseAmpPhysicalMacro:
    tech = Path(tech_dir)
    spice_path = tech / "sp_lib" / "sense_amp.sp"
    spice_pins = _parse_spice_subckt_pins(spice_path)
    gds_audit = audit_macros(tech, tech / "openyield_macro_aliases.json", focus=("sense_amp",))
    sense_gds = next(item for item in gds_audit["audited_macros"] if item["macro_name"] == "sense_amp")
    gds_pins = tuple(
        pin["canonical_pin"]
        for pin in sense_gds.get("pins", [])
        if pin.get("pin_shape_source") == "label_plus_shape"
    )
    q_to_dout = _pin_shape_status(sense_gds, "Q", "dout") == "label_plus_shape"
    qb_to_dout_b = _pin_shape_status(sense_gds, "QB", "dout_b") == "label_plus_shape"
    return SenseAmpPhysicalMacro(
        macro_name="sense_amp",
        spice_pins=spice_pins,
        gds_label_backed_pins=gds_pins,
        q_to_dout_established=q_to_dout,
        qb_to_dout_b_established=qb_to_dout_b,
        safe_for_physical_mapping=bool(q_to_dout and not qb_to_dout_b),
        requires_netlist_rewrite=True,
        requires_layout_pin=False,
        notes=(
            "Local sense_amp physical macro is single-ended.",
            "QB must remain metadata-only and must not become a physical route target.",
        ),
    )


def build_senseamp_placement_plan(
    cols: int,
    mux_ratio: int,
    origin_x: float,
    origin_y: float,
    pitch_x: float,
    adapter: ModuleArchitectureAdapter | None = None,
    local_macro: SenseAmpPhysicalMacro | None = None,
) -> SenseAmpPlacementPlan:
    if cols <= 0:
        raise ValueError("cols must be positive")
    if mux_ratio <= 0:
        raise ValueError("mux_ratio must be positive")
    adapter = adapter or build_senseamp_architecture_adapter(qb_required_downstream=False)
    local_macro = local_macro or SenseAmpPhysicalMacro(
        macro_name="sense_amp",
        spice_pins=LOCAL_SENSEAMP_PINS,
        gds_label_backed_pins=("vdd", "gnd", "sense_enable", "bl", "br", "dout"),
        q_to_dout_established=True,
        qb_to_dout_b_established=False,
        safe_for_physical_mapping=True,
        requires_netlist_rewrite=True,
        requires_layout_pin=False,
    )
    _validate_senseamp_mapping(adapter, local_macro)

    if mux_ratio == 1:
        placements = tuple(
            _build_single_column_placement(col, origin_x, origin_y, pitch_x, adapter)
            for col in range(cols)
        )
        plan_notes = (
            "One sense_amp is planned per storage/data column.",
            "The plan is adapter-only and does not modify standalone placement.",
        )
    else:
        groups = ceil(cols / mux_ratio)
        placements = tuple(
            _build_grouped_placement(group, origin_x, origin_y, pitch_x, adapter)
            for group in range(groups)
        )
        plan_notes = (
            "One sense_amp is planned per mux output group.",
            "This plan does not place column mux macros; it only records grouped sense_amp targets.",
            "The plan is adapter-only and does not modify standalone placement.",
        )
    return SenseAmpPlacementPlan(
        cols=cols,
        mux_ratio=mux_ratio,
        placements=placements,
        macro_name=local_macro.macro_name,
        adapter_strategy="single_ended_q_to_dout",
        requires_netlist_rewrite=adapter.requires_netlist_rewrite,
        requires_layout_pin=adapter.requires_layout_pin,
        notes=plan_notes,
    )


def example_placements(plan: SenseAmpPlacementPlan, limit: int = 3) -> list[dict[str, Any]]:
    return [item.to_dict() for item in plan.placements[:limit]]


def _build_single_column_placement(
    col: int,
    origin_x: float,
    origin_y: float,
    pitch_x: float,
    adapter: ModuleArchitectureAdapter,
) -> SenseAmpPlacement:
    return SenseAmpPlacement(
        instance_name=f"Xsa_c{col}",
        macro_name="sense_amp",
        col=col,
        x=origin_x + col * pitch_x,
        y=origin_y,
        orientation="R0",
        nets={
            "vdd": "vdd",
            "gnd": "gnd",
            "en": "sense_enable",
            "bl": f"bl[{col}]",
            "br": f"br[{col}]",
            "dout": f"dout[{col}]",
        },
        dropped_pins={"QB": "dropped_complementary_output"},
        adapter_strategy="single_ended_q_to_dout",
        safe_for_physical_mapping=adapter.safe_for_physical_mapping,
        notes=("Column-direct sense amp placement plan.",),
    )


def _build_grouped_placement(
    group: int,
    origin_x: float,
    origin_y: float,
    pitch_x: float,
    adapter: ModuleArchitectureAdapter,
) -> SenseAmpPlacement:
    return SenseAmpPlacement(
        instance_name=f"Xsa_g{group}",
        macro_name="sense_amp",
        col=group,
        x=origin_x + group * pitch_x,
        y=origin_y,
        orientation="R0",
        nets={
            "vdd": "vdd",
            "gnd": "gnd",
            "en": "sense_enable",
            "bl": f"mux_out[{group}]",
            "br": f"mux_out_b[{group}]",
            "dout": f"dout[{group}]",
        },
        dropped_pins={"QB": "dropped_complementary_output"},
        adapter_strategy="single_ended_q_to_dout",
        safe_for_physical_mapping=adapter.safe_for_physical_mapping,
        notes=("Mux-grouped sense amp placement plan.",),
    )


def _validate_senseamp_mapping(
    adapter: ModuleArchitectureAdapter,
    local_macro: SenseAmpPhysicalMacro,
) -> None:
    if adapter.openyield_module != "SENSEAMP":
        raise ValueError("adapter must target OpenYield SENSEAMP")
    if adapter.local_macro != "sense_amp":
        raise ValueError("adapter must target local sense_amp")
    if tuple(local_macro.spice_pins) != LOCAL_SENSEAMP_PINS:
        raise ValueError(f"local sense_amp pins must be exactly {LOCAL_SENSEAMP_PINS}")
    if not local_macro.q_to_dout_established:
        raise ValueError("local sense_amp must establish Q -> dout before planning placement")
    if local_macro.qb_to_dout_b_established:
        raise ValueError("local sense_amp unexpectedly exposes QB -> dout_b; adapter assumptions no longer hold")
    if adapter.requires_layout_pin:
        raise ValueError("placement smoke only supports adapters that do not require a new layout pin")
    if not adapter.requires_netlist_rewrite:
        raise ValueError("placement smoke expects requires_netlist_rewrite=True")
    if not adapter.safe_for_physical_mapping:
        raise ValueError("placement smoke only supports safe-for-physical single-ended sense_amp mapping")


def _parse_spice_subckt_pins(path: Path) -> tuple[str, ...]:
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if stripped.lower().startswith(".subckt"):
            parts = stripped.split()
            return tuple(parts[2:])
    return ()


def _pin_shape_status(sense_gds: dict[str, Any], pin_name: str, canonical_pin: str) -> str:
    for pin in sense_gds.get("pins", []):
        if pin.get("pin_name") == pin_name and pin.get("canonical_pin") == canonical_pin:
            return str(pin.get("pin_shape_source") or "")
    return "missing"
