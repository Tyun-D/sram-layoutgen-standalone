"""Read-only adapter metadata for OpenYield column mux contracts."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .gds_pin_audit import audit_macros, read_gds_labels_and_shapes


ADAPT_DIRECT = "direct_physical_pin"
ADAPT_MISSING_POWER = "missing_power_metadata"


@dataclass(frozen=True)
class ColumnMuxPinAdaptation:
    openyield_pin: str
    local_pin: str | None
    canonical_signal: str
    adaptation_type: str
    required: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ColumnMuxAdapter:
    openyield_module: str
    local_macro: str
    pin_adaptations: tuple[ColumnMuxPinAdaptation, ...]
    power_status: str
    safe_for_physical_mapping: bool
    safe_for_shared_rail: bool
    requires_power_metadata_fix: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["pin_adaptations"] = [item.to_dict() for item in self.pin_adaptations]
        return data


def inspect_local_columnmux_macro(tech_dir: str | Path) -> dict[str, Any]:
    tech = Path(tech_dir)
    replacement = _load_replacement_macro(tech, "gen_col_mux")
    gds_path = tech / str(replacement.get("gds") or "gds_lib/openram_replacements/gen_col_mux.gds")
    labels, _shapes, bbox = read_gds_labels_and_shapes(gds_path)
    gds_audit = audit_macros(tech, tech / "openyield_macro_aliases.json", focus=("gen_col_mux",))
    macro_audit = next(item for item in gds_audit["audited_macros"] if item["macro_name"] == "gen_col_mux")
    return {
        "macro_name": "gen_col_mux",
        "replacement_macro": replacement,
        "gds_path": str(gds_path.resolve()),
        "gds_bbox": bbox.to_dict() if bbox else None,
        "raw_gds_labels": [label.text for label in labels],
        "audit": macro_audit,
        "spice_path": None,
        "spice_subckt_pins": [],
    }


def build_columnmux_adapter(
    out_to_mux_out: bool,
    outb_to_mux_out_b: bool,
    power_status: str,
) -> ColumnMuxAdapter:
    safe_physical = bool(out_to_mux_out and outb_to_mux_out_b)
    safe_shared = power_status not in {"missing_power_metadata", "spice_power_pin_without_gds_label"}
    requires_fix = power_status in {"missing_power_metadata", "spice_power_pin_without_gds_label"}
    notes = [
        "OUT/OUTB semantics are evaluated independently from power metadata.",
    ]
    if requires_fix:
        notes.append("Do not allow shared rail or claim power-complete placement until VDD metadata is proven.")
    return ColumnMuxAdapter(
        openyield_module="COLUMNMUX*",
        local_macro="gen_col_mux",
        pin_adaptations=(
            ColumnMuxPinAdaptation("VDD", "vdd" if not requires_fix else None, "vdd", ADAPT_MISSING_POWER if requires_fix else ADAPT_DIRECT, False if requires_fix else True, (
                "OpenYield requires VDD.",
                "Local gen_col_mux does not prove a VDD label-backed physical pin." if requires_fix else "VDD metadata is present.",
            )),
            ColumnMuxPinAdaptation("VSS", "gnd", "gnd", ADAPT_DIRECT, True),
            ColumnMuxPinAdaptation("BL", "BL", "bl", ADAPT_DIRECT, True),
            ColumnMuxPinAdaptation("BLB", "BR", "br", ADAPT_DIRECT, True),
            ColumnMuxPinAdaptation("SEL", "SEL", "column_select", ADAPT_DIRECT, True),
            ColumnMuxPinAdaptation("OUT", "OUT", "mux_out", ADAPT_DIRECT, True),
            ColumnMuxPinAdaptation("OUTB", "OUTB", "mux_out_b", ADAPT_DIRECT, True),
        ),
        power_status=power_status,
        safe_for_physical_mapping=safe_physical,
        safe_for_shared_rail=safe_shared,
        requires_power_metadata_fix=requires_fix,
        notes=tuple(notes),
    )


def classify_columnmux_power_status(local_macro: dict[str, Any], contract: dict[str, Any]) -> str:
    replacement_pins = {str(pin.get("name") or "") for pin in local_macro["replacement_macro"].get("pins", [])}
    raw_labels = {str(item).strip() for item in local_macro.get("raw_gds_labels", [])}
    gds_pin_names = {str(pin.get("pin_name") or "") for pin in local_macro["audit"].get("pins", []) if pin.get("pin_shape_source") != "missing"}
    contract_power = {str(key) for key in contract.get("power_pins", {}).keys()}

    has_vdd_contract = "VDD" in contract_power
    has_gds_vdd_label = "VDD" in raw_labels or "vdd" in raw_labels or "VDD" in gds_pin_names or "vdd" in gds_pin_names
    has_replacement_vdd = "vdd" in {name.lower() for name in replacement_pins}

    if has_vdd_contract and not has_gds_vdd_label and not has_replacement_vdd:
        return "missing_power_metadata"
    if has_vdd_contract and not has_gds_vdd_label and has_replacement_vdd:
        return "spice_power_pin_without_gds_label"
    if not has_vdd_contract and not has_gds_vdd_label and not has_replacement_vdd:
        return "no_vdd_pin_required_or_unpowered_pass_mux"
    return "vdd_gnd_metadata_present"


def columnmux_semantics(local_macro: dict[str, Any]) -> dict[str, bool]:
    audit_pins = {
        str(pin.get("canonical_pin") or ""): pin
        for pin in local_macro["audit"].get("pins", [])
    }
    return {
        "out_to_mux_out": audit_pins.get("mux_out", {}).get("pin_shape_source") == "label_plus_shape",
        "outb_to_mux_out_b": audit_pins.get("mux_out_b", {}).get("pin_shape_source") == "label_plus_shape",
        "sel_to_column_select": audit_pins.get("column_select", {}).get("pin_shape_source") == "label_plus_shape",
        "bl_to_bl": audit_pins.get("bl", {}).get("pin_shape_source") == "label_plus_shape",
        "br_to_br": audit_pins.get("br", {}).get("pin_shape_source") == "label_plus_shape",
        "gnd_present": audit_pins.get("gnd", {}).get("pin_shape_source") == "label_plus_shape",
        "vdd_present": audit_pins.get("vdd", {}).get("pin_shape_source") == "label_plus_shape",
    }


def _load_replacement_macro(tech_dir: Path, macro_name: str) -> dict[str, Any]:
    payload = json.loads((tech_dir / "replacement_macros.json").read_text(encoding="utf-8"))
    for item in payload.get("macros", []):
        if item.get("name") == macro_name:
            return item
    raise ValueError(f"replacement macro not found: {macro_name}")
