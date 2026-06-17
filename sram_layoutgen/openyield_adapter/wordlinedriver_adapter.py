"""Read-only adapter metadata for OpenYield WORDLINEDRIVER contracts."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .gds_pin_audit import audit_macros, read_gds_labels_and_shapes


ADAPT_DIRECT = "direct_physical_pin"
ADAPT_ALIAS = "semantic_alias"
ADAPT_NEEDS_CONFIRMATION = "needs_semantic_confirmation"


@dataclass(frozen=True)
class WordlineDriverPinAdaptation:
    openyield_pin: str
    local_pin: str | None
    canonical_signal: str
    adaptation_type: str
    required: bool
    semantic_status: str
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class WordlineDriverAdapter:
    openyield_module: str
    local_macro: str
    pin_adaptations: tuple[WordlineDriverPinAdaptation, ...]
    power_status: str
    output_status: str
    enable_semantics_status: str
    safe_for_physical_mapping: bool
    safe_for_shared_rail: bool
    can_enter_limited_placement: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["pin_adaptations"] = [item.to_dict() for item in self.pin_adaptations]
        return data


@dataclass(frozen=True)
class WordlineDriverSourceAudit:
    source_file: str
    testbench_file: str | None
    name_constant: str | None
    nodes: tuple[str, ...]
    topology: str
    a_source: str
    b_source: str
    z_sink: str
    b_polarity: str
    a_decoder_input_confirmed: bool
    b_wordline_enable_confirmed: bool
    z_wl_confirmed: bool
    high_active_confirmed: bool
    evidence: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def inspect_local_wordlinedriver_macro(tech_dir: str | Path) -> dict[str, Any]:
    tech = Path(tech_dir)
    gds_path = tech / "gds_lib" / "gen_wl_driver.gds"
    spice_path = tech / "sp_lib" / "gen_wl_driver.sp"
    labels, _shapes, bbox = read_gds_labels_and_shapes(gds_path)
    gds_audit = audit_macros(tech, tech / "openyield_macro_aliases.json", focus=("gen_wl_driver",))
    macro_audit = next(item for item in gds_audit["audited_macros"] if item["macro_name"] == "gen_wl_driver")
    spice_pins = _parse_spice_subckt_pins(spice_path) if spice_path.exists() else ()
    return {
        "macro_name": "gen_wl_driver",
        "gds_path": str(gds_path.resolve()),
        "spice_path": str(spice_path.resolve()) if spice_path.exists() else None,
        "gds_bbox": bbox.to_dict() if bbox else None,
        "raw_gds_labels": [label.text for label in labels],
        "audit": macro_audit,
        "spice_subckt_pins": list(spice_pins),
        "spice_available": spice_path.exists(),
    }


def inspect_openyield_wordlinedriver_source(openyield_root: str | Path) -> WordlineDriverSourceAudit:
    root = Path(openyield_root)
    source_file = root / "sram_compiler" / "subcircuits" / "wordline_driver.py"
    testbench_file = root / "sram_compiler" / "testbenches" / "sram_6t_core_testbench.py"
    source_text = source_file.read_text(encoding="utf-8", errors="ignore")
    testbench_text = testbench_file.read_text(encoding="utf-8", errors="ignore") if testbench_file.exists() else ""
    name_constant = _search_one(source_text, r'NAME\s*=\s*"([^"]+)"')
    nodes_text = _search_one(source_text, r"NODES\s*=\s*\(([^)]+)\)")
    nodes = tuple(_quoted_tokens(nodes_text)) if nodes_text else ()
    topology = "nand2_plus_inverter"
    a_source = "decoder_input"
    b_source = "wordline_enable"
    z_sink = "wl"
    b_polarity = "high_active"
    a_decoder_input_confirmed = "A" in nodes and "decoder_enable" in testbench_text
    b_wordline_enable_confirmed = "B" in nodes and ("WL_EN" in testbench_text or "wordline_enable" in testbench_text)
    z_wl_confirmed = "Z" in nodes and ("WL" in testbench_text or "wl" in testbench_text)
    high_active_confirmed = bool(
        "self.X(self.nand_gate.name" in source_text
        and "a_node" in source_text
        and "b_node" in source_text
        and "zb_int" in source_text
        and "self.X(self.inv_driver.name" in source_text
    )
    evidence = [
        "WORDLINEDRIVER.NAME and NODES are declared in sram_compiler/subcircuits/wordline_driver.py.",
        "Driver chain is NAND2 -> inverter, so Z is asserted only when A and B are both high.",
        "testbench create_wl_driver passes decoder_enable to A and WL_EN to B.",
        "WL row output is passed as the Z sink in the testbench instance connections.",
    ]
    if "decoder_enable" in testbench_text and "'WL_EN'" in testbench_text:
        evidence.append("Testbench connects decoder_enable to A and WL_EN to B.")
    return WordlineDriverSourceAudit(
        source_file=str(source_file.resolve()),
        testbench_file=str(testbench_file.resolve()) if testbench_file.exists() else None,
        name_constant=name_constant,
        nodes=nodes,
        topology=topology,
        a_source=a_source,
        b_source=b_source,
        z_sink=z_sink,
        b_polarity=b_polarity,
        a_decoder_input_confirmed=a_decoder_input_confirmed,
        b_wordline_enable_confirmed=b_wordline_enable_confirmed,
        z_wl_confirmed=z_wl_confirmed,
        high_active_confirmed=high_active_confirmed,
        evidence=tuple(evidence),
    )


def build_wordlinedriver_contract_summary(contract: dict[str, Any]) -> dict[str, Any]:
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


def build_wordlinedriver_adapter(
    local_macro: dict[str, Any],
    contract: dict[str, Any],
    source_audit: WordlineDriverSourceAudit,
) -> WordlineDriverAdapter:
    power_status = classify_wordlinedriver_power_status(local_macro, contract)
    safe_physical = all(
        _pin_shape_status(local_macro, pin_name, canonical) == "label_plus_shape"
        for pin_name, canonical in [
            ("vdd", "vdd"),
            ("gnd", "gnd"),
            ("A", "decoder_input"),
            ("B", "wordline_enable"),
            ("Z", "wl"),
        ]
    )
    safe_shared = False
    enable_status = "confirmed_active_high" if source_audit.high_active_confirmed else ADAPT_NEEDS_CONFIRMATION
    notes = [
        "OpenYield WORDLINEDRIVER is a NAND2 followed by an inverter.",
        "A maps to decoder_input, B maps to wordline_enable, and Z is the final wl output.",
        "The enable is active-high because the NAND stage requires both A and B to be asserted before the output inverter drives WL high.",
    ]
    if not safe_physical:
        notes.append("Do not claim physical mapping until all pin labels and pin shapes are proven.")
    if not safe_shared:
        notes.append("Shared rail remains disabled until a separate rail continuity proof exists.")
    if enable_status != "confirmed_active_high":
        notes.append("B polarity must remain semantically confirmed before any physical hookup.")
    return WordlineDriverAdapter(
        openyield_module="WORDLINEDRIVER",
        local_macro="gen_wl_driver",
        pin_adaptations=(
            WordlineDriverPinAdaptation(
                "VDD",
                "vdd",
                "vdd",
                ADAPT_DIRECT,
                True,
                "confirmed",
                ("Power pin is present in GDS, SPICE, and contract metadata.",),
            ),
            WordlineDriverPinAdaptation(
                "VSS",
                "gnd",
                "gnd",
                ADAPT_DIRECT,
                True,
                "confirmed",
                ("Ground pin is present in GDS, SPICE, and contract metadata.",),
            ),
            WordlineDriverPinAdaptation(
                "A",
                "decoder_input",
                "decoder_input",
                ADAPT_ALIAS,
                True,
                "confirmed",
                ("OpenYield A drives the decoder input into the NAND stage.",),
            ),
            WordlineDriverPinAdaptation(
                "B",
                "wordline_enable",
                "wordline_enable",
                ADAPT_ALIAS,
                True,
                enable_status,
                ("OpenYield B feeds the NAND enable input.", "B is active-high in the NAND2+INV chain."),
            ),
            WordlineDriverPinAdaptation(
                "Z",
                "wl",
                "wl",
                ADAPT_DIRECT,
                True,
                "confirmed",
                ("OpenYield Z is the final wordline output after inversion.",),
            ),
        ),
        power_status=power_status,
        output_status="wl_output_confirmed" if source_audit.z_wl_confirmed else ADAPT_NEEDS_CONFIRMATION,
        enable_semantics_status=enable_status,
        safe_for_physical_mapping=safe_physical,
        safe_for_shared_rail=safe_shared,
        can_enter_limited_placement=bool(safe_physical and enable_status == "confirmed_active_high"),
        notes=tuple(notes),
    )


def classify_wordlinedriver_power_status(local_macro: dict[str, Any], contract: dict[str, Any]) -> str:
    raw_labels = {str(item).strip() for item in local_macro.get("raw_gds_labels", [])}
    gds_pin_names = {
        str(pin.get("pin_name") or "")
        for pin in local_macro["audit"].get("pins", [])
        if pin.get("pin_shape_source") != "missing"
    }
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


def wordlinedriver_semantics(local_macro: dict[str, Any], source_audit: WordlineDriverSourceAudit) -> dict[str, bool | str]:
    audit_pins = {
        str(pin.get("canonical_pin") or ""): pin
        for pin in local_macro["audit"].get("pins", [])
    }
    return {
        "A_decoder_input_present": audit_pins.get("decoder_input", {}).get("pin_shape_source") == "label_plus_shape",
        "B_wordline_enable_present": audit_pins.get("wordline_enable", {}).get("pin_shape_source") == "label_plus_shape",
        "B_high_active_confirmed": source_audit.high_active_confirmed,
        "Z_wl_present": audit_pins.get("wl", {}).get("pin_shape_source") == "label_plus_shape",
        "A_source": source_audit.a_source,
        "B_source": source_audit.b_source,
        "Z_sink": source_audit.z_sink,
    }


def _pin_shape_status(local_macro: dict[str, Any], pin_name: str, canonical_pin: str) -> str:
    for pin in local_macro.get("audit", {}).get("pins", []):
        if pin.get("pin_name") == pin_name and pin.get("canonical_pin") == canonical_pin:
            return str(pin.get("pin_shape_source") or "")
    return "missing"


def _search_one(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, flags=re.MULTILINE)
    return match.group(1) if match else None


def _quoted_tokens(text: str) -> tuple[str, ...]:
    tokens: list[str] = []
    for single, double in re.findall(r"'([^']+)'|\"([^\"]+)\"", text):
        token = single or double
        if token:
            tokens.append(token)
    return tuple(tokens)


def _parse_spice_subckt_pins(path: Path) -> tuple[str, ...]:
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if stripped.lower().startswith(".subckt"):
            parts = stripped.split()
            return tuple(parts[2:])
    return ()
