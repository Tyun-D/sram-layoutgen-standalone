"""Read-only adapter metadata for OpenYield WRITEDRIVER contracts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .gds_pin_audit import audit_macros, read_gds_labels_and_shapes


ADAPT_DIRECT = "direct_physical_pin"
ADAPT_ALIAS = "semantic_alias"
ADAPT_MISSING_POWER = "missing_power_metadata"


@dataclass(frozen=True)
class WriteDriverPinAdaptation:
    openyield_pin: str
    local_pin: str | None
    canonical_signal: str
    adaptation_type: str
    required: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WriteDriverAdapter:
    openyield_module: str
    local_macro: str
    pin_adaptations: tuple[WriteDriverPinAdaptation, ...]
    power_status: str
    safe_for_physical_mapping: bool
    safe_for_shared_rail: bool
    requires_netlist_rewrite: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["pin_adaptations"] = [item.to_dict() for item in self.pin_adaptations]
        return data


def inspect_local_writedriver_macro(tech_dir: str | Path) -> dict[str, Any]:
    tech = Path(tech_dir)
    gds_path = tech / "gds_lib" / "write_driver.gds"
    spice_path = tech / "sp_lib" / "write_driver.sp"
    labels, _shapes, bbox = read_gds_labels_and_shapes(gds_path)
    gds_audit = audit_macros(tech, tech / "openyield_macro_aliases.json", focus=("write_driver",))
    macro_audit = next(item for item in gds_audit["audited_macros"] if item["macro_name"] == "write_driver")
    spice_pins = _parse_spice_subckt_pins(spice_path)
    return {
        "macro_name": "write_driver",
        "gds_path": str(gds_path.resolve()),
        "spice_path": str(spice_path.resolve()),
        "gds_bbox": bbox.to_dict() if bbox else None,
        "raw_gds_labels": [label.text for label in labels],
        "audit": macro_audit,
        "spice_subckt_pins": list(spice_pins),
    }


def build_writedriver_adapter(local_macro: dict[str, Any], contract: dict[str, Any]) -> WriteDriverAdapter:
    power_status = classify_writedriver_power_status(local_macro, contract)
    safe_physical = all(
        _pin_shape_status(local_macro, pin_name, canonical) == "label_plus_shape"
        for pin_name, canonical in [
            ("VDD", "vdd"),
            ("VSS", "gnd"),
            ("EN", "write_enable"),
            ("DIN", "din"),
            ("BL", "bl"),
            ("BLB", "br"),
        ]
    )
    safe_shared = False
    notes = [
        "OpenYield WRITEDRIVER exposes only DIN and EN externally; internal DINB/ENB generation stays inside the SPICE macro.",
        "BL/BLB map to the local bl/br pins without a routing rewrite.",
    ]
    if not safe_physical:
        notes.append("Do not claim physical mapping until all pin labels and pin shapes are proven.")
    if not safe_shared:
        notes.append("Shared rail remains disabled until a separate rail continuity proof exists.")
    return WriteDriverAdapter(
        openyield_module="WRITEDRIVER",
        local_macro="write_driver",
        pin_adaptations=(
            WriteDriverPinAdaptation(
                "VDD",
                "vdd",
                "vdd",
                ADAPT_DIRECT,
                True,
                ("Power pin is present in GDS and SPICE.",),
            ),
            WriteDriverPinAdaptation(
                "VSS",
                "gnd",
                "gnd",
                ADAPT_DIRECT,
                True,
                ("Ground pin is present in GDS and SPICE.",),
            ),
            WriteDriverPinAdaptation(
                "EN",
                "write_enable",
                "write_enable",
                ADAPT_ALIAS,
                True,
                ("Local pin name is `en`; canonical signal is `write_enable`.",),
            ),
            WriteDriverPinAdaptation(
                "DIN",
                "din",
                "din",
                ADAPT_DIRECT,
                True,
                ("Local pin name matches the canonical data-in signal.",),
            ),
            WriteDriverPinAdaptation(
                "BL",
                "bl",
                "bl",
                ADAPT_DIRECT,
                True,
                ("Left bitline pin is label-backed.",),
            ),
            WriteDriverPinAdaptation(
                "BLB",
                "br",
                "br",
                ADAPT_ALIAS,
                True,
                ("OpenYield BLB maps to local `br` on this hardcell.",),
            ),
        ),
        power_status=power_status,
        safe_for_physical_mapping=safe_physical,
        safe_for_shared_rail=safe_shared,
        requires_netlist_rewrite=False,
        notes=tuple(notes),
    )


def build_writedriver_contract_summary(contract: dict[str, Any]) -> dict[str, Any]:
    pins = contract.get("pins", [])
    power = contract.get("power_pins", {})
    return {
        "original_module_name": contract.get("original_module_name"),
        "canonical_module_name": contract.get("canonical_module_name"),
        "role": contract.get("role"),
        "pin_list": [str(pin.get("original_name") or "") for pin in pins],
        "canonical_pins": [str(pin.get("canonical_name") or "") for pin in pins],
        "power_pins": dict(power),
        "notes": list(contract.get("notes", [])),
        "warnings": list(contract.get("warnings", [])),
    }


def classify_writedriver_power_status(local_macro: dict[str, Any], contract: dict[str, Any]) -> str:
    raw_labels = {str(item).strip() for item in local_macro.get("raw_gds_labels", [])}
    gds_pin_names = {str(pin.get("pin_name") or "") for pin in local_macro["audit"].get("pins", []) if pin.get("pin_shape_source") != "missing"}
    contract_power = {str(key) for key in contract.get("power_pins", {}).keys()}
    has_vdd_contract = "VDD" in contract_power
    has_gnd_contract = "VSS" in contract_power
    has_vdd = "vdd" in {label.lower() for label in raw_labels} or "vdd" in {name.lower() for name in gds_pin_names}
    has_gnd = "gnd" in {label.lower() for label in raw_labels} or "gnd" in {name.lower() for name in gds_pin_names}
    if has_vdd_contract and has_gnd_contract and has_vdd and has_gnd:
        return "vdd_gnd_metadata_present"
    if has_vdd_contract and has_gnd_contract:
        return "missing_power_metadata"
    return "no_vdd_pin_required_or_unpowered_pass_driver"


def writedriver_semantics(local_macro: dict[str, Any]) -> dict[str, bool]:
    audit_pins = {
        str(pin.get("canonical_pin") or ""): pin
        for pin in local_macro["audit"].get("pins", [])
    }
    return {
        "en_to_write_enable": audit_pins.get("write_enable", {}).get("pin_shape_source") == "label_plus_shape",
        "din_to_din": audit_pins.get("din", {}).get("pin_shape_source") == "label_plus_shape",
        "bl_to_bl": audit_pins.get("bl", {}).get("pin_shape_source") == "label_plus_shape",
        "blb_to_br": audit_pins.get("br", {}).get("pin_shape_source") == "label_plus_shape",
        "vdd_present": audit_pins.get("vdd", {}).get("pin_shape_source") == "label_plus_shape",
        "gnd_present": audit_pins.get("gnd", {}).get("pin_shape_source") == "label_plus_shape",
    }


def _pin_shape_status(local_macro: dict[str, Any], pin_name: str, canonical_pin: str) -> str:
    for pin in local_macro.get("audit", {}).get("pins", []):
        if pin.get("pin_name") == pin_name and pin.get("canonical_pin") == canonical_pin:
            return str(pin.get("pin_shape_source") or "")
    return "missing"


def _parse_spice_subckt_pins(path: Path) -> tuple[str, ...]:
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if stripped.lower().startswith(".subckt"):
            parts = stripped.split()
            return tuple(parts[2:])
    return ()
