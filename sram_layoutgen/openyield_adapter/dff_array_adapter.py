"""OpenYield DFF-array adapter audit helpers.

This module is read-only and metadata-only. It audits the compatibility between
the OpenYield DFF family and the local `dff` hardcell, then summarizes how
ADDR_DFF and DATA_DFF should be interpreted as repeated DFF arrays.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .gds_pin_audit import audit_macros
from .macro_compat import load_contract_payload


@dataclass(frozen=True)
class DffPinMapping:
    openyield_pin: str
    openyield_role: str
    local_target_pin: str | None
    local_gds_label_present: bool
    local_spice_pin_present: bool
    mapping_status: str
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DffArraySemantic:
    array_type: str
    input_pins: tuple[str, ...]
    output_pins: tuple[str, ...]
    input_semantics: tuple[str, ...]
    output_semantics: tuple[str, ...]
    feeds_domain: str
    downstream_consumer: str
    mapping_status: str
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_dff_array_adapter_report(
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
) -> dict[str, Any]:
    contracts_payload = load_contract_payload(contracts_path)
    contracts = {str(item.get("original_module_name") or ""): item for item in contracts_payload.get("contracts", [])}
    dff_contract = contracts["DFF"]
    addr_contract = contracts["ADDR_DFF"]
    data_contract = contracts["DATA_DFF"]

    macro_report = audit_macros(tech_dir, Path(tech_dir) / "openyield_macro_aliases.json", focus=("dff",))
    dff_macro = next(item for item in macro_report["audited_macros"] if str(item.get("macro_name") or "") == "dff")
    gds_labels = [str(item.get("text") or "") for item in dff_macro.get("labels", [])]
    spice_pins = _read_spice_pins(Path(dff_macro["spice_path"])) if dff_macro.get("spice_path") else []

    pin_mappings = _build_dff_pin_mappings(dff_contract, gds_labels, spice_pins)
    shared_rail_safe = False
    physical_mapping_safe = all(item.mapping_status in {"matched", "unused_complementary_output"} for item in pin_mappings)
    has_required_power = _has_required_power(dff_macro)
    no_extra_control_pins = not any(name.lower() in {"qb", "reset", "rst", "set", "enable", "en", "scan", "se", "si", "so"} for name in gds_labels + spice_pins)
    if not has_required_power:
        physical_mapping_safe = False

    addr_width_template = _count_dynamic_suffix(addr_contract, "A{i}")
    data_width_template = _count_dynamic_suffix(data_contract, "DIN{i}")
    semantics = _build_array_semantics()

    report = {
        "scope": "step6_2_dff_array_adapter_audit",
        "openyield_root": str(Path(openyield_root).resolve()),
        "contracts_path": str(Path(contracts_path).resolve()),
        "tech_dir": str(Path(tech_dir).resolve()),
        "openyield_dff_pin_list": [pin["original_name"] for pin in dff_contract.get("pins", [])],
        "local_dff_gds_path": dff_macro.get("gds_path"),
        "local_dff_spice_path": dff_macro.get("spice_path"),
        "local_dff_gds_bbox": dff_macro.get("bbox"),
        "local_dff_gds_labels": gds_labels,
        "local_dff_spice_pins": spice_pins,
        "local_dff_has_qb": "QB" in gds_labels or "qb" in [item.lower() for item in spice_pins],
        "local_dff_has_reset_enable_scan": any(
            name.lower() in {"reset", "rst", "set", "enable", "en", "scan", "se", "si", "so"}
            for name in gds_labels + spice_pins
        ),
        "vdd_gnd_metadata_complete": has_required_power,
        "safe_for_physical_mapping": physical_mapping_safe,
        "safe_for_shared_rail": shared_rail_safe,
        "row_placement_ready": "metadata_only" if physical_mapping_safe else "not_ready",
        "dff_adapter_safe_for_metadata_plan": physical_mapping_safe,
        "dff_array_can_enter_metadata_placement": physical_mapping_safe,
        "dff_array_can_enter_standalone_placement": False,
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "pin_mapping_table": [item.to_dict() for item in pin_mappings],
        "addr_dff_semantics": semantics["ADDR_DFF"].to_dict(),
        "data_dff_semantics": semantics["DATA_DFF"].to_dict(),
        "address_dff_count_template": addr_width_template,
        "data_dff_count_template": data_width_template,
        "notes": _report_notes(dff_macro, physical_mapping_safe, no_extra_control_pins),
        "can_enter_step_6_3": physical_mapping_safe,
        "step_6_3_recommendation": (
            "Proceed to metadata-level control-row floorplan planning, but keep standalone placement disabled until row pitch, clock distribution, and rail strategy are proven."
            if physical_mapping_safe
            else "Do not proceed to Step 6.3 until DFF pin/power mapping is corrected."
        ),
    }
    return report


def build_dff_array_adapter_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OpenYield DFF Array Adapter Audit",
            "",
            "This is a metadata-only adapter audit. It does not modify standalone.py, routing, the GDS writer, or any OpenYield source.",
            "",
            "## Summary",
            "",
            f"- OpenYield DFF pin list: `{', '.join(report['openyield_dff_pin_list'])}`",
            f"- local DFF GDS labels: `{', '.join(report['local_dff_gds_labels'])}`",
            f"- local DFF SPICE pins: `{', '.join(report['local_dff_spice_pins'])}`",
            f"- safe_for_physical_mapping: `{report['safe_for_physical_mapping']}`",
            f"- safe_for_shared_rail: `{report['safe_for_shared_rail']}`",
            f"- row_placement_ready: `{report['row_placement_ready']}`",
            f"- dff_adapter_safe_for_metadata_plan: `{report['dff_adapter_safe_for_metadata_plan']}`",
            f"- dff_array_can_enter_metadata_placement: `{report['dff_array_can_enter_metadata_placement']}`",
            f"- dff_array_can_enter_standalone_placement: `{report['dff_array_can_enter_standalone_placement']}`",
            f"- standalone modified: `{report['standalone_modified']}`",
            f"- routing modified: `{report['routing_modified']}`",
            f"- GDS writer modified: `{report['gds_writer_modified']}`",
            "",
            "## Local DFF Audit",
            "",
            f"- GDS path: `{report['local_dff_gds_path']}`",
            f"- SPICE path: `{report['local_dff_spice_path']}`",
            f"- GDS bbox: `{json.dumps(report['local_dff_gds_bbox'], ensure_ascii=False)}`",
            f"- VDD/GND metadata complete: `{report['vdd_gnd_metadata_complete']}`",
            f"- local QB present: `{report['local_dff_has_qb']}`",
            f"- local reset/enable/scan present: `{report['local_dff_has_reset_enable_scan']}`",
            "",
            "## DFF Pin Mapping",
            "",
            _table(
                ["OpenYield pin", "role", "local target", "GDS label", "SPICE pin", "status", "notes"],
                [
                    [
                        item["openyield_pin"],
                        item["openyield_role"],
                        item["local_target_pin"] or "-",
                        item["local_gds_label_present"],
                        item["local_spice_pin_present"],
                        item["mapping_status"],
                        "; ".join(item["notes"]) or "-",
                    ]
                    for item in report["pin_mapping_table"]
                ],
            ),
            "",
            "## ADDR_DFF Semantic Table",
            "",
            _table(
                ["array", "inputs", "outputs", "input semantics", "output semantics", "feeds", "consumer", "status"],
                [[
                    report["addr_dff_semantics"]["array_type"],
                    ", ".join(report["addr_dff_semantics"]["input_pins"]),
                    ", ".join(report["addr_dff_semantics"]["output_pins"]),
                    ", ".join(report["addr_dff_semantics"]["input_semantics"]),
                    ", ".join(report["addr_dff_semantics"]["output_semantics"]),
                    report["addr_dff_semantics"]["feeds_domain"],
                    report["addr_dff_semantics"]["downstream_consumer"],
                    report["addr_dff_semantics"]["mapping_status"],
                ]],
            ),
            "",
            "## DATA_DFF Semantic Table",
            "",
            _table(
                ["array", "inputs", "outputs", "input semantics", "output semantics", "feeds", "consumer", "status"],
                [[
                    report["data_dff_semantics"]["array_type"],
                    ", ".join(report["data_dff_semantics"]["input_pins"]),
                    ", ".join(report["data_dff_semantics"]["output_pins"]),
                    ", ".join(report["data_dff_semantics"]["input_semantics"]),
                    ", ".join(report["data_dff_semantics"]["output_semantics"]),
                    report["data_dff_semantics"]["feeds_domain"],
                    report["data_dff_semantics"]["downstream_consumer"],
                    report["data_dff_semantics"]["mapping_status"],
                ]],
            ),
            "",
            "## Notes",
            "",
            *[f"- {item}" for item in report["notes"]],
            "",
        ]
    )


def _build_dff_pin_mappings(dff_contract: dict[str, Any], gds_labels: list[str], spice_pins: list[str]) -> list[DffPinMapping]:
    gds_lower = {item.lower() for item in gds_labels}
    spice_lower = {item.lower() for item in spice_pins}
    mappings: list[DffPinMapping] = []
    role_map = {
        "VDD": ("power", "vdd", ("vdd",)),
        "VSS": ("ground", "gnd", ("gnd",)),
        "D": ("data_input", "d", ("d", "din", "data")),
        "Q": ("data_output", "q", ("q",)),
        "CLK": ("clock", "clk", ("clk", "clk_buf")),
    }
    for pin in dff_contract.get("pins", []):
        name = str(pin.get("original_name") or "")
        role, target, aliases = role_map[name]
        gds_present = any(alias.lower() in gds_lower for alias in aliases)
        spice_present = any(alias.lower() in spice_lower for alias in aliases)
        status = "matched" if gds_present and spice_present else "requires_architecture_adapter"
        notes: list[str] = []
        if name == "CLK":
            notes.append("OpenYield DFF uses CLK; local physical pin is clk, and array-level semantic clock domain may be driven by clk_buf.")
        if not gds_present:
            notes.append("Expected local GDS label was not found.")
        if not spice_present:
            notes.append("Expected local SPICE pin was not found.")
        mappings.append(
            DffPinMapping(
                openyield_pin=name,
                openyield_role=role,
                local_target_pin=target,
                local_gds_label_present=gds_present,
                local_spice_pin_present=spice_present,
                mapping_status=status,
                notes=tuple(notes),
            )
        )
    mappings.append(
        DffPinMapping(
            openyield_pin="QB",
            openyield_role="complementary_output",
            local_target_pin=None,
            local_gds_label_present=False,
            local_spice_pin_present=False,
            mapping_status="unused_complementary_output",
            notes=("OpenYield ADDR_DFF/DATA_DFF do not use QB, and the local hardcell does not expose QB.",),
        )
    )
    return mappings


def _build_array_semantics() -> dict[str, DffArraySemantic]:
    return {
        "ADDR_DFF": DffArraySemantic(
            array_type="ADDR_DFF",
            input_pins=("CLK", "A[i]"),
            output_pins=("A_dff[i]",),
            input_semantics=("CLK -> clk_buf / TIME clock domain", "A[i] -> addr[i]"),
            output_semantics=("A_dff[i] -> addr_q[i] / addr_latched[i]",),
            feeds_domain="decoder_input_domain",
            downstream_consumer="DECODER_CASCADE.A[i]",
            mapping_status="dff_array_mappable",
            notes=("ADDR_DFF is a repeated address-flop array only.",),
        ),
        "DATA_DFF": DffArraySemantic(
            array_type="DATA_DFF",
            input_pins=("CLK", "DIN[i]"),
            output_pins=("DIN_dff[i]",),
            input_semantics=("CLK -> clk_buf / TIME clock domain", "DIN[i] -> din[i]"),
            output_semantics=("DIN_dff[i] -> din_q[i] / data_latched[i]",),
            feeds_domain="write_driver_input_domain",
            downstream_consumer="WRITEDRIVER.DIN[i]",
            mapping_status="dff_array_mappable",
            notes=("DATA_DFF is a repeated data-flop array only.",),
        ),
    }


def _has_required_power(dff_macro: dict[str, Any]) -> bool:
    canonical = {item.get("canonical_pin") for item in dff_macro.get("pins", []) if item.get("pin_shape_source") != "missing"}
    return "vdd" in canonical and "gnd" in canonical


def _report_notes(dff_macro: dict[str, Any], physical_mapping_safe: bool, no_extra_control_pins: bool) -> list[str]:
    notes = [
        "OpenYield DFF pin list is VDD, VSS, D, Q, CLK.",
        "Local dff GDS exposes clk, D, Q, gnd, vdd and does not expose QB.",
        "Local dff SPICE subckt order is D Q clk vdd gnd, so the adapter must be name-based rather than order-based.",
        "ADDR_DFF feeds DECODER_CASCADE, while DATA_DFF feeds WRITEDRIVER.",
        "Shared rail remains disabled because DFF row-level rail continuity and abutment are not proven by this audit.",
    ]
    if physical_mapping_safe:
        notes.append("The DFF leaf is safe for metadata-only planning.")
    else:
        notes.append("The DFF leaf is not safe even for metadata-only planning because pin or power mapping is incomplete.")
    if not no_extra_control_pins:
        notes.append("Unexpected extra control pins were found and would require an architecture adapter.")
    return notes


def _count_dynamic_suffix(contract: dict[str, Any], pattern: str) -> int:
    return sum(1 for pin in contract.get("pins", []) if str(pin.get("original_name") or "") == pattern)


def _read_spice_pins(path: Path) -> list[str]:
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        parts = line.strip().split()
        if parts and parts[0].lower() == ".subckt" and len(parts) > 2:
            return parts[2:]
    return []


def _table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item).replace("|", "\\|").replace("\n", "<br>") for item in row) + " |")
    return "\n".join(lines)
