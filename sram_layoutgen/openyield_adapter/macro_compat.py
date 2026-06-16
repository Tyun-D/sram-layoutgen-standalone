"""Compatibility checks between OpenYield ModuleContract data and replacement macros."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .aggregation import (
    COMPOSITE_REQUIRED,
    NON_LAYOUT_SOURCE,
    UNSUPPORTED_ARCHITECTURE,
    AggregationFootprint,
    aggregation_status_for_contract,
    build_aggregation_footprint,
)


@dataclass(frozen=True)
class MacroPinCheck:
    canonical_pin: str
    expected_aliases: tuple[str, ...]
    matched_macro_pin: str | None
    status: str
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MacroCompatibility:
    original_module_name: str
    canonical_module_name: str
    role: str
    candidate_macros: tuple[str, ...]
    existing_macros: tuple[str, ...]
    selected_macro: str | None
    pin_checks: tuple[MacroPinCheck, ...]
    power_status: str
    aggregation_status: str
    implementation_status: str
    footprint: AggregationFootprint | None = None
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["pin_checks"] = [check.to_dict() for check in self.pin_checks]
        data["footprint"] = self.footprint.to_dict() if self.footprint else None
        return data


def load_contract_payload(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_replacement_macros(tech_dir: str | Path) -> dict[str, dict[str, Any]]:
    path = Path(tech_dir) / "replacement_macros.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {str(item.get("name")): item for item in payload.get("macros", [])}


def check_contract_payload(contracts_payload: dict[str, Any], tech_dir: str | Path) -> dict[str, Any]:
    macros = load_replacement_macros(tech_dir)
    checks = [check_contract(contract, macros) for contract in contracts_payload.get("contracts", [])]
    return {
        "contracts_source": contracts_payload.get("openyield_root"),
        "replacement_macro_count": len(macros),
        "contract_count": len(checks),
        "compatibilities": [check.to_dict() for check in checks],
        "summary": summarize_compatibilities(checks),
    }


def check_contract(contract: dict[str, Any], macros: dict[str, dict[str, Any]]) -> MacroCompatibility:
    original = str(contract.get("original_module_name") or "")
    role = str(contract.get("role") or "")
    implementation_status = _implementation_status(contract)
    candidates = tuple(str(name) for name in contract.get("gds_macro_candidates", []) if name)
    existing = tuple(name for name in candidates if name in macros)
    selected = existing[0] if existing else None
    macro = macros[selected] if selected else None

    pin_checks: tuple[MacroPinCheck, ...] = ()
    if macro:
        pin_checks = tuple(_pin_check(contract, macro, pin) for pin in _unique_canonical_pins(contract))
    elif candidates:
        pin_checks = tuple(
            MacroPinCheck(
                canonical_pin=str(pin.get("canonical_name") or ""),
                expected_aliases=tuple(pin.get("aliases") or ()),
                matched_macro_pin=None,
                status="missing_macro",
                notes=("Candidate macro names are not present in replacement_macros.json.",),
            )
            for pin in _unique_canonical_pins(contract)
        )
    footprint = build_aggregation_footprint(macro, role, implementation_status) if macro else None
    aggregation_status = (
        footprint.status
        if footprint
        else aggregation_status_for_contract(role, implementation_status, has_macro=False)
    )
    notes = tuple(_notes(contract, selected, pin_checks, implementation_status))
    return MacroCompatibility(
        original_module_name=original,
        canonical_module_name=str(contract.get("canonical_module_name") or ""),
        role=role,
        candidate_macros=candidates,
        existing_macros=existing,
        selected_macro=selected,
        pin_checks=pin_checks,
        power_status=_power_status(contract, macro, pin_checks),
        aggregation_status=aggregation_status,
        implementation_status=implementation_status,
        footprint=footprint,
        notes=notes,
    )


def summarize_compatibilities(checks: list[MacroCompatibility]) -> dict[str, Any]:
    macro_success = [
        check.original_module_name
        for check in checks
        if check.implementation_status == "macro_candidate"
        and check.selected_macro
        and all(pin.status == "matched" for pin in check.pin_checks)
    ]
    missing_macro = [
        check.original_module_name
        for check in checks
        if check.candidate_macros and not check.existing_macros and check.implementation_status not in {COMPOSITE_REQUIRED, UNSUPPORTED_ARCHITECTURE, NON_LAYOUT_SOURCE}
    ]
    pin_mismatch = [
        check.original_module_name
        for check in checks
        if check.implementation_status == "macro_candidate"
        and check.selected_macro
        and any(pin.status != "matched" for pin in check.pin_checks)
    ]
    no_physical = [
        check.original_module_name
        for check in checks
        if not check.candidate_macros and check.implementation_status not in {COMPOSITE_REQUIRED, UNSUPPORTED_ARCHITECTURE, NON_LAYOUT_SOURCE}
    ]
    return {
        "matched_existing_macro": macro_success,
        "candidate_macro_missing": missing_macro,
        "macro_exists_pin_mismatch": pin_mismatch,
        "no_physical_implementation": no_physical,
        "composite_required": [check.original_module_name for check in checks if check.implementation_status == COMPOSITE_REQUIRED],
        "unsupported_architecture": [check.original_module_name for check in checks if check.implementation_status == UNSUPPORTED_ARCHITECTURE],
        "non_layout_source": [check.original_module_name for check in checks if check.implementation_status == NON_LAYOUT_SOURCE],
        "aggregation_status_counts": _count_by(checks, "aggregation_status"),
        "implementation_status_counts": _count_by(checks, "implementation_status"),
        "power_status_counts": _count_by(checks, "power_status"),
        "vdd_gnd_shared_rail_risks": [
            check.original_module_name
            for check in checks
            if check.footprint and any("No power/ground rail" in note or "GDS pin shapes" in note for note in check.footprint.notes)
        ],
    }


def _unique_canonical_pins(contract: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    seen: set[str] = set()
    pins = []
    for pin in contract.get("pins", []):
        canonical = str(pin.get("canonical_name") or "")
        if not canonical or canonical in seen:
            continue
        seen.add(canonical)
        pins.append(pin)
    return tuple(pins)


def _pin_check(contract: dict[str, Any], macro: dict[str, Any], pin: dict[str, Any]) -> MacroPinCheck:
    canonical = str(pin.get("canonical_name") or "")
    expected = tuple(str(alias) for alias in pin.get("aliases", []) if alias)
    macro_pins = tuple(macro.get("pins") or ())
    matches = [
        macro_pin
        for macro_pin in macro_pins
        if _canonical_macro_pin(str(macro_pin.get("name") or ""), macro, contract) == canonical
    ]
    if matches:
        return MacroPinCheck(canonical, expected, str(matches[0].get("name") or ""), "matched")
    return MacroPinCheck(
        canonical,
        expected,
        None,
        "missing_pin",
        (f"No replacement macro pin maps to canonical `{canonical}`.",),
    )


def _canonical_macro_pin(name: str, macro: dict[str, Any], contract: dict[str, Any]) -> str:
    original = str(contract.get("original_module_name") or "")
    macro_name = str(macro.get("name") or "")
    overrides = {
        "PRECHARGE": {
            "EN": "precharge_enb",
        },
        "WORDLINEDRIVER": {
            "A": "decoder_input",
            "Z": "wl",
        },
        "COLUMNMUX*": {
            "BL": "bl",
            "BR": "br",
            "OUT": "mux_out",
            "OUTB": "mux_out_b",
            "SEL": "column_select",
        },
    }
    if name in overrides.get(original, {}):
        return overrides[original][name]
    if macro_name == "gen_precharge" and name == "EN":
        return "precharge_enb"
    if macro_name == "gen_col_mux" and name in {"OUT", "OUTB", "SEL"}:
        return {"OUT": "mux_out", "OUTB": "mux_out_b", "SEL": "column_select"}[name]
    low = name.lower()
    if low in {"vss", "gnd"}:
        return "gnd"
    if low == "vdd":
        return "vdd"
    if name in {"BL", "BL0"}:
        return "bl"
    if name in {"BLB", "BR", "BLB0"}:
        return "br"
    if name in {"WL", "Z"} and str(contract.get("role")) == "wordline_driver":
        return "wl"
    if name in {"Q", "OUT"}:
        return "dout"
    if name in {"QB", "OUTB"}:
        return "dout_b"
    return low


def _power_status(contract: dict[str, Any], macro: dict[str, Any] | None, pin_checks: tuple[MacroPinCheck, ...]) -> str:
    contract_pins = {str(pin.get("canonical_name") or "") for pin in contract.get("pins", [])}
    if not macro:
        return "no_macro"
    matched = {pin.canonical_pin for pin in pin_checks if pin.status == "matched"}
    if "vdd" in contract_pins and "vdd" not in matched:
        return "missing_vdd"
    if "gnd" in contract_pins and "gnd" not in matched:
        return "missing_gnd"
    if "gnd" not in contract_pins:
        return "no_gnd_required"
    if {"vdd", "gnd"} <= matched:
        return "vdd_gnd_alias_ok"
    return "ok"


def _implementation_status(contract: dict[str, Any]) -> str:
    status = str(contract.get("implementation_status") or "")
    if status:
        return status
    original = str(contract.get("original_module_name") or "")
    role = str(contract.get("role") or "")
    source = str(contract.get("source_file") or "").lower()
    class_name = str(contract.get("class_name") or "").lower()
    if "testbenches/" in source or "factory" in class_name or "testbench" in class_name or "factory" in original.lower():
        return NON_LAYOUT_SOURCE
    if original.startswith("SRAM_10T") or role == "bitcell_10t":
        return UNSUPPORTED_ARCHITECTURE
    if original in {"TIME", "ADDR_DFF", "DATA_DFF", "delay_chain", "wen_delay_chain", "DECODER_CASCADE", "SRAM_6T_CORE_*"}:
        return COMPOSITE_REQUIRED
    if role == "support_cell":
        return "needs_stdcell_or_generated_layout"
    return "macro_candidate"


def _notes(
    contract: dict[str, Any],
    selected_macro: str | None,
    pin_checks: tuple[MacroPinCheck, ...],
    implementation_status: str,
) -> list[str]:
    notes = list(contract.get("notes") or ())
    if implementation_status == COMPOSITE_REQUIRED:
        notes.append("Do not map this OpenYield module to one single GDS macro; build it from lower-level contracts.")
    if implementation_status == UNSUPPORTED_ARCHITECTURE:
        notes.append("Current layout generator/replacement macro library is 6T-focused; this OpenYield architecture is unsupported.")
    if selected_macro and any(check.status != "matched" for check in pin_checks):
        notes.append("Replacement macro exists, but one or more canonical pins do not match current metadata.")
    return notes


def _count_by(checks: list[MacroCompatibility], attr: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for check in checks:
        value = str(getattr(check, attr))
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))
