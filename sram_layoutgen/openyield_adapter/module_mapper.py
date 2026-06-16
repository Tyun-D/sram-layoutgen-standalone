"""Map parsed OpenYield PySpice modules into canonical ModuleContract objects."""

from __future__ import annotations

from collections import defaultdict

from .canonical_names import canonical_module_name, canonical_pin_name, module_role, pin_polarity, pin_role
from .contracts import ModuleContract, ParsedPySpiceModule, PinContract
from .pyspice_source_parser import parse_openyield_pyspice_sources


def build_module_contracts(openyield_root: str) -> tuple[list[ModuleContract], list[str]]:
    parsed, warnings = parse_openyield_pyspice_sources(openyield_root)
    contracts = [module_to_contract(module) for module in parsed]
    return _deduplicate_contracts(contracts), warnings


def module_to_contract(module: ParsedPySpiceModule) -> ModuleContract:
    original = module.original_module_name
    role = _contract_role(original, module)
    canonical_module = canonical_module_name(original, role)
    pins = tuple(_pin_contract(pin) for pin in module.nodes)
    power = {
        pin.original_name: pin.canonical_name
        for pin in pins
        if pin.role in {"power", "ground"}
    }
    candidates = _gds_candidates(original, role)
    openram_roles = _openram_roles(role)
    notes = list(_notes_for_module(original, role))
    warnings = list(module.warnings)
    if not candidates:
        warnings.append("No current layoutgen GDS macro candidate is known for this OpenYield module.")
    if any("{i}" in pin.original_name for pin in pins):
        notes.append("Pins contain dynamic bus patterns; expand with SRAM size before placement.")
    return ModuleContract(
        source="openyield_pyspice_static",
        original_module_name=original,
        canonical_module_name=canonical_module,
        role=role,
        pins=pins,
        power_pins=power,
        equivalent_openram_roles=openram_roles,
        gds_macro_candidates=candidates,
        requires_physical_implementation=_requires_physical(role),
        notes=tuple(notes),
        warnings=tuple(warnings),
        class_name=module.class_name,
        source_file=module.source_file,
        mos_call_count=module.mos_call_count,
        self_instance_call_count=module.self_instance_call_count,
        circuit_instance_call_count=module.circuit_instance_call_count,
    )


def _pin_contract(name: str) -> PinContract:
    canonical = canonical_pin_name(name)
    return PinContract(
        original_name=name,
        canonical_name=canonical,
        role=pin_role(name, canonical),
        direction=_pin_direction(canonical),
        polarity=pin_polarity(name, canonical),
        aliases=_aliases_for_pin(name, canonical),
    )


def _pin_direction(canonical: str) -> str | None:
    if canonical in {"vdd", "gnd", "bl", "br", "wl"}:
        return "INOUT"
    if canonical in {"dout", "dout_b", "addr_q", "din_q", "clk_buf", "clk_bar", "sense_enable", "write_enable", "wordline_enable", "precharge_enb"}:
        return "OUTPUT"
    if canonical in {"din", "addr", "clk", "en", "enb", "web", "csb"}:
        return "INPUT"
    return None


def _aliases_for_pin(original: str, canonical: str) -> tuple[str, ...]:
    aliases = {
        "vdd": ("VDD", "vdd"),
        "gnd": ("VSS", "GND", "gnd"),
        "bl": ("BL", "BL0", "BL{i}", "bl"),
        "br": ("BLB", "BR", "br", "BLB0", "BLB{i}"),
        "wl": ("WL", "WL0", "WL{i}", "wl"),
        "clk": ("CLK", "clk0", "clk"),
        "web": ("web0", "web"),
        "csb": ("csb0", "csb"),
        "precharge_enb": ("ENB", "PRE", "pre", "p_en_bar"),
        "sense_enable": ("s_en", "sense_en"),
        "write_enable": ("w_en", "write_en"),
        "wordline_enable": ("wl_en",),
        "din": ("DIN", "DIN{i}", "din0[*]", "din"),
        "dout": ("Q", "OUT", "dout0[*]", "dout"),
        "dout_b": ("QB", "OUTB"),
        "addr": ("A{i}", "A0", "addr0[*]", "addr"),
        "addr_q": ("A_dff{i}", "addr_q[*]"),
        "din_q": ("DIN_dff{i}", "din_q[*]"),
    }.get(canonical, ())
    if original not in aliases:
        aliases = (original, *aliases)
    return tuple(dict.fromkeys(aliases))


def _contract_role(original: str, module: ParsedPySpiceModule) -> str:
    role = module_role(original, module.class_name, module.source_file)
    if role == "support_cell" and original in {"DFF", "ADDR_DFF", "DATA_DFF", "TIME", "delay_chain", "wen_delay_chain"}:
        return "control_timing"
    if role != "unknown":
        return role
    return module.role_hint


def _gds_candidates(original: str, role: str) -> tuple[str, ...]:
    if original == "SRAM_6T_CELL" or role == "bitcell":
        return ("cell_1rw", "cell_6t")
    if original == "SRAM_6T_CORE_*" or role == "bitcell_array":
        return ("cell_1rw_array", "bitcell_array")
    if role == "precharge":
        return ("gen_precharge", "precharge_array")
    if role == "write_driver":
        return ("write_driver", "write_driver_array")
    if role == "sense_amp":
        return ("sense_amp", "sense_amp_array")
    if role == "column_mux":
        return ("gen_col_mux", "column_mux")
    if role == "decoder":
        return ("gen_nand2", "gen_nand4", "row_decoder")
    if role == "wordline_driver":
        return ("gen_wl_driver", "wordline_driver")
    if role == "dummy":
        return ("dummy_cell_1rw", "dummy_cell_array")
    if role == "replica":
        return ("replica_cell_1rw", "replica_column")
    if original in {"DFF", "ADDR_DFF", "DATA_DFF"}:
        return ("dff",)
    if original == "delay_chain":
        return ("gen_delay_inv", "delay_chain")
    if original == "TIME":
        return ("control_glue", "gen_inv", "gen_nand2", "gen_nor2", "dff", "gen_delay_inv")
    return ()


def _openram_roles(role: str) -> tuple[str, ...]:
    mapping = {
        "bitcell": ("bitcell", "cell_1rw"),
        "bitcell_array": ("bitcell_array",),
        "precharge": ("precharge", "precharge_array"),
        "write_driver": ("write_driver", "write_driver_array"),
        "sense_amp": ("sense_amp", "sense_amp_array"),
        "column_mux": ("column_mux",),
        "decoder": ("row_decoder", "predecoder"),
        "wordline_driver": ("wordline_driver", "wordline_driver_array"),
        "dummy": ("dummy_cell", "dummy_array"),
        "replica": ("replica_cell", "replica_column"),
        "control_timing": ("control_logic", "delay_chain", "dff_array"),
    }
    return mapping.get(role, ())


def _requires_physical(role: str) -> bool:
    return role not in {"testbench", "unknown"}


def _notes_for_module(original: str, role: str) -> tuple[str, ...]:
    notes: list[str] = []
    if original == "PRECHARGE":
        notes.append("OpenYield PRECHARGE uses ENB; map to active-low precharge enable.")
    if original == "WRITEDRIVER":
        notes.append("OpenYield WRITEDRIVER has internal DINB/ENB generation; only DIN/EN are external pins.")
    if original == "SENSEAMP":
        notes.append("Map IN/INB to selected BL/BR and Q/QB to dout/dout_b or tri-state stage.")
    if original == "WORDLINEDRIVER":
        notes.append("A/B are decoder/control inputs; Z is the wordline output.")
    if original == "TIME":
        notes.append("Composite control/timing module; should become architecture/control contract before placement.")
    if role in {"bitcell_array", "control_timing"}:
        notes.append("This contract is hierarchical and should not map to one single flat GDS macro.")
    return tuple(notes)


def _deduplicate_contracts(contracts: list[ModuleContract]) -> list[ModuleContract]:
    grouped: dict[tuple[str, str], list[ModuleContract]] = defaultdict(list)
    for contract in contracts:
        grouped[(contract.original_module_name, contract.class_name or "")].append(contract)
    deduped = []
    for _key, items in grouped.items():
        deduped.append(max(items, key=lambda item: (len(item.pins), item.mos_call_count + item.self_instance_call_count + item.circuit_instance_call_count)))
    return sorted(deduped, key=lambda item: (item.role, item.original_module_name, item.class_name or ""))
