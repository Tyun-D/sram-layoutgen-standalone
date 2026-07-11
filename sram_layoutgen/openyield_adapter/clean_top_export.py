from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


CLASS_DESIGN = "DESIGN_CIRCUIT"
CLASS_STIM = "TESTBENCH_STIMULUS"
CLASS_SIM = "SIMULATION_COMMAND"
CLASS_MODEL = "MODEL_INCLUDE"
CLASS_MEAS = "MEASUREMENT_SCAFFOLD"
CLASS_UNKNOWN = "UNKNOWN"

TOP_MODULE_NAME = "OPENYIELD_SRAM_TOP_V1"

PIN_ROLE_POWER = "power"
PIN_ROLE_GROUND = "ground"
PIN_ROLE_CLOCK = "clock"
PIN_ROLE_CHIP_SELECT = "chip_select_bar"
PIN_ROLE_WRITE_ENABLE = "write_enable_bar"
PIN_ROLE_ADDRESS = "address"
PIN_ROLE_DATA_IN = "data_input"
PIN_ROLE_DATA_OUT = "data_output"
PIN_ROLE_DATA_OUT_BAR = "data_output_bar"
PIN_ROLE_CONTROL = "control"

PIN_ORDER_RANK = {
    PIN_ROLE_POWER: 0,
    PIN_ROLE_GROUND: 1,
    PIN_ROLE_CLOCK: 2,
    PIN_ROLE_CHIP_SELECT: 3,
    PIN_ROLE_WRITE_ENABLE: 4,
    PIN_ROLE_ADDRESS: 5,
    PIN_ROLE_DATA_IN: 6,
    PIN_ROLE_DATA_OUT: 7,
    PIN_ROLE_DATA_OUT_BAR: 8,
    PIN_ROLE_CONTROL: 9,
}

_RE_ADDRESS = re.compile(r"^A\d+$", re.IGNORECASE)
_RE_DATA_IN = re.compile(r"^DIN\d+$", re.IGNORECASE)
_RE_DATA_OUT = re.compile(r"^SA_Q\d+$", re.IGNORECASE)
_RE_DATA_OUT_BAR = re.compile(r"^SA_QB\d+$", re.IGNORECASE)
_RE_WORDLINE = re.compile(r"^WL\d+$", re.IGNORECASE)
_RE_DEC_WL = re.compile(r"^DEC_WL\d+$", re.IGNORECASE)
_RE_BITLINE = re.compile(r"^BLB?\d+$", re.IGNORECASE)
_RE_REPLICA_WL = re.compile(r"^RWL$", re.IGNORECASE)


@dataclass(frozen=True)
class SpiceInstance:
    instance_type: str
    name: str
    raw_line: str
    nets: tuple[str, ...]
    module_name: str
    params: tuple[str, ...] = ()


@dataclass
class SpiceSubckt:
    name: str
    pins: list[str]
    body_lines: list[str]
    start_line: int
    end_line: int = 0


@dataclass
class ParsedSpiceNetlist:
    title: str
    includes: list[str]
    subckts: list[SpiceSubckt]
    top_level_lines: list[str]


def canonical_net_name(name: str) -> str:
    return name.strip().lower()


def parse_spice_text(text: str) -> ParsedSpiceNetlist:
    raw_lines = _merge_continuations(text.splitlines())
    includes: list[str] = []
    subckts: list[SpiceSubckt] = []
    top_level_lines: list[str] = []
    title = ""
    stack: list[SpiceSubckt] = []
    for lineno, raw_line in enumerate(raw_lines, start=1):
        line = raw_line.strip()
        if not line or line.startswith("*"):
            continue
        lower = line.lower()
        if lower.startswith(".title"):
            title = raw_line.strip()
            if not stack:
                top_level_lines.append(raw_line.strip())
            continue
        if lower.startswith(".include"):
            includes.append(raw_line.strip())
            if not stack:
                top_level_lines.append(raw_line.strip())
            continue
        if lower.startswith(".subckt"):
            tokens = raw_line.split()
            subckt = SpiceSubckt(
                name=tokens[1],
                pins=tokens[2:],
                body_lines=[],
                start_line=lineno,
            )
            subckts.append(subckt)
            stack.append(subckt)
            continue
        if lower.startswith(".ends"):
            if not stack:
                raise ValueError(f"unmatched .ends at line {lineno}")
            stack[-1].end_line = lineno
            stack.pop()
            continue
        if stack:
            stack[-1].body_lines.append(raw_line.strip())
        else:
            top_level_lines.append(raw_line.strip())
    if stack:
        raise ValueError(f"unclosed .subckt: {stack[-1].name}")
    return ParsedSpiceNetlist(title=title, includes=includes, subckts=subckts, top_level_lines=top_level_lines)


def classify_spice_line(line: str) -> str:
    stripped = line.strip()
    lower = stripped.lower()
    if not stripped:
        return CLASS_UNKNOWN
    if lower.startswith(".include") or lower.startswith(".lib"):
        return CLASS_MODEL
    if lower.startswith(".tran") or lower.startswith(".print") or lower.startswith(".plot") or lower.startswith(".option") or lower.startswith(".probe") or lower.startswith(".control") or lower.startswith(".endc"):
        return CLASS_SIM
    if lower.startswith(".measure") or lower.startswith(".meas") or lower.startswith(".step") or lower.startswith(".mc"):
        return CLASS_MEAS
    if lower.startswith(".title"):
        return CLASS_UNKNOWN
    head = stripped[0].upper()
    if head in {"V", "I"}:
        return CLASS_STIM
    if head == "X":
        instance = parse_spice_instance_line(stripped)
        if instance.module_name.lower() == "d_latch":
            return CLASS_MEAS
        return CLASS_DESIGN
    if head in {"M", "R", "C", "E"}:
        return CLASS_DESIGN
    return CLASS_UNKNOWN


def parse_spice_instance_line(line: str) -> SpiceInstance:
    tokens = line.split()
    if not tokens:
        raise ValueError("empty SPICE instance line")
    head = tokens[0][0].upper()
    if head == "X":
        return SpiceInstance(
            instance_type="X",
            name=tokens[0],
            raw_line=line,
            nets=tuple(tokens[1:-1]),
            module_name=tokens[-1],
        )
    if head == "M":
        if len(tokens) < 6:
            raise ValueError(f"invalid MOS line: {line}")
        return SpiceInstance(
            instance_type="M",
            name=tokens[0],
            raw_line=line,
            nets=tuple(tokens[1:5]),
            module_name=tokens[5],
            params=tuple(tokens[6:]),
        )
    raise ValueError(f"unsupported instance line: {line}")


def parse_subckt_instances(subckt: SpiceSubckt) -> list[SpiceInstance]:
    instances: list[SpiceInstance] = []
    for line in subckt.body_lines:
        if not line:
            continue
        first = line[0].upper()
        if first in {"X", "M"}:
            instances.append(parse_spice_instance_line(line))
    return instances


def top_level_design_instances(parsed: ParsedSpiceNetlist) -> list[SpiceInstance]:
    design: list[SpiceInstance] = []
    for line in parsed.top_level_lines:
        if classify_spice_line(line) != CLASS_DESIGN:
            continue
        instance = parse_spice_instance_line(line)
        if instance.instance_type != "X":
            continue
        if instance.module_name.lower() == "d_latch":
            continue
        design.append(instance)
    return design


def build_top_pin_roles(instances: list[SpiceInstance]) -> dict[str, dict[str, Any]]:
    by_canon: dict[str, dict[str, Any]] = {}
    net_usage: dict[str, int] = {}
    representatives: dict[str, str] = {}
    for instance in instances:
        for net in instance.nets:
            canon = canonical_net_name(net)
            net_usage[canon] = net_usage.get(canon, 0) + 1
            representatives.setdefault(canon, net)
    for canon, usage in net_usage.items():
        name = representatives[canon]
        role = infer_top_pin_role(name, usage)
        if role is None:
            continue
        by_canon[canon] = {
            "name": name,
            "canonical_name": canon,
            "role": role,
            "usage_count": usage,
        }
    ordered = dict(
        sorted(
            by_canon.items(),
            key=lambda item: (
                PIN_ORDER_RANK[item[1]["role"]],
                _pin_sort_key(item[1]["name"]),
            ),
        )
    )
    return ordered


def infer_top_pin_role(net_name: str, usage_count: int) -> str | None:
    lower = net_name.lower()
    if lower == "vdd":
        return PIN_ROLE_POWER
    if lower in {"vss", "gnd", "0"}:
        return PIN_ROLE_GROUND
    if lower == "clk":
        return PIN_ROLE_CLOCK
    if lower == "csb":
        return PIN_ROLE_CHIP_SELECT
    if lower == "web":
        return PIN_ROLE_WRITE_ENABLE
    if _RE_ADDRESS.match(net_name):
        return PIN_ROLE_ADDRESS
    if _RE_DATA_IN.match(net_name):
        return PIN_ROLE_DATA_IN
    if _RE_DATA_OUT.match(net_name):
        return PIN_ROLE_DATA_OUT
    if _RE_DATA_OUT_BAR.match(net_name):
        return PIN_ROLE_DATA_OUT_BAR
    if lower in {"sel0", "sel1", "selb0", "selb1"}:
        return PIN_ROLE_CONTROL
    if usage_count == 1 and lower in {"out", "out_b"}:
        return PIN_ROLE_DATA_OUT if lower == "out" else PIN_ROLE_DATA_OUT_BAR
    return None


def extract_clean_top(parsed: ParsedSpiceNetlist, parameters: dict[str, Any], source_trace: dict[str, Any]) -> dict[str, Any]:
    design_instances = top_level_design_instances(parsed)
    pin_roles = build_top_pin_roles(design_instances)
    top_pins = [item["name"] for item in pin_roles.values()]
    rendered = render_clean_top_netlist(
        title=parsed.title or ".title OPENYIELD_SRAM_TOP_V1",
        includes=parsed.includes,
        subckts=parsed.subckts,
        top_module_name=TOP_MODULE_NAME,
        top_pins=top_pins,
        design_instance_lines=[instance.raw_line for instance in design_instances],
        source_trace=source_trace,
    )
    return {
        "top_module_name": TOP_MODULE_NAME,
        "top_pins": top_pins,
        "pin_roles": list(pin_roles.values()),
        "design_instances": design_instances,
        "clean_netlist_text": rendered,
        "parameters": parameters,
    }


def render_clean_top_netlist(
    *,
    title: str,
    includes: list[str],
    subckts: list[SpiceSubckt],
    top_module_name: str,
    top_pins: list[str],
    design_instance_lines: list[str],
    source_trace: dict[str, Any],
) -> str:
    lines: list[str] = []
    lines.append(title)
    lines.append(f"* Clean layout-facing extraction generated from {source_trace['generator']}")
    lines.append(f"* Source testbench netlist: {source_trace['sample_netlist']}")
    lines.extend(includes)
    for subckt in subckts:
        lines.append("")
        lines.append(".subckt " + " ".join([subckt.name, *subckt.pins]))
        lines.extend(subckt.body_lines)
        lines.append(f".ends {subckt.name}")
    lines.append("")
    lines.append(".subckt " + " ".join([top_module_name, *top_pins]))
    lines.extend(design_instance_lines)
    lines.append(f".ends {top_module_name}")
    lines.append("")
    return "\n".join(lines)


def _merge_continuations(lines: list[str]) -> list[str]:
    merged: list[str] = []
    for line in lines:
        if line.lstrip().startswith("+") and merged:
            merged[-1] = merged[-1] + " " + line.lstrip()[1:].strip()
        else:
            merged.append(line.rstrip())
    return merged


def _pin_sort_key(name: str) -> tuple[int, str]:
    match = re.search(r"(\d+)$", name)
    if match:
        return int(match.group(1)), name
    return (10**9, name)


def verification_flags(clean_text: str) -> dict[str, bool]:
    lower = clean_text.lower()
    return {
        "clean_top_contains_independent_stimulus": bool(re.search(r"^[vi]\S+", clean_text, re.MULTILINE | re.IGNORECASE)),
        "clean_top_contains_pulse": "pulse(" in lower,
        "clean_top_contains_pwl": "pwl(" in lower,
        "clean_top_contains_tran": ".tran" in lower,
        "clean_top_contains_measure": ".measure" in lower or ".meas" in lower,
        "clean_top_contains_monte_carlo": ".mc" in lower or "monte" in lower,
    }


def top_level_classification_rows(parsed: ParsedSpiceNetlist, origin: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for subckt in parsed.subckts:
        rows.append(
            {
                "origin": origin,
                "element_scope": "NETLIST_SUBCKT_DEF",
                "element_name": subckt.name,
                "element_type": ".subckt",
                "raw_text": f".subckt {subckt.name} {' '.join(subckt.pins)}",
                "classification": CLASS_DESIGN,
                "reason": "Subcircuit definition for generated SRAM design or support logic.",
            }
        )
    for line in parsed.top_level_lines:
        name = line.split()[0] if line.split() else line
        rows.append(
            {
                "origin": origin,
                "element_scope": "NETLIST_TOP_LEVEL",
                "element_name": name,
                "element_type": name[0].upper() if name else "",
                "raw_text": line,
                "classification": classify_spice_line(line),
                "reason": classification_reason(line),
            }
        )
    return rows


def classification_reason(line: str) -> str:
    classified = classify_spice_line(line)
    if classified == CLASS_MODEL:
        return "Model include required by design netlist."
    if classified == CLASS_SIM:
        return "Simulation-only command."
    if classified == CLASS_MEAS:
        return "Measurement or target-column observation scaffolding."
    if classified == CLASS_STIM:
        return "Independent testbench source or waveform stimulus."
    if classified == CLASS_DESIGN:
        return "Design hierarchy instance or device."
    return "Unclassified top-level text."


def generator_call_classification_rows() -> list[dict[str, Any]]:
    rows = [
        ("create_sram_array", CLASS_DESIGN, "Creates the SRAM core array subcircuit and top instance."),
        ("create_replica_column", CLASS_DESIGN, "Creates the replica column design path."),
        ("create_and2_for_rwl", CLASS_DESIGN, "Creates RWL control gate consumed by replica column path."),
        ("create_time_circuit", CLASS_DESIGN, "Creates TIME control candidate subcircuit and design instance."),
        ("add_cs_startup_clamp", CLASS_STIM, "Adds startup clamp pulse sources only for simulation stimulus."),
        ("create_decoder", CLASS_DESIGN, "Creates decoder design circuitry."),
        ("create_wl_driver", CLASS_DESIGN, "Creates wordline driver design circuitry."),
        ("create_D_latch", CLASS_MEAS, "Adds a target-column observation latch rather than a full macro output bus."),
        ("create_read_periphery", CLASS_DESIGN, "Creates precharge, optional mux, and sense-amplifier design circuitry."),
        ("create_write_periphery", CLASS_DESIGN, "Creates write-driver design circuitry."),
        ("address_pulse_sources", CLASS_STIM, "Top-level target-address pulse or DC stimulus."),
        ("clock_pulse_source", CLASS_STIM, "Top-level testbench clock source."),
        ("csb_pulse_source", CLASS_STIM, "Top-level chip-select-bar stimulus."),
        ("web_pulse_source", CLASS_STIM, "Top-level write-enable-bar stimulus."),
    ]
    return [
        {
            "origin": "generator_call_chain",
            "element_scope": "GENERATOR_CALL",
            "element_name": name,
            "element_type": "python_call",
            "raw_text": name,
            "classification": classification,
            "reason": reason,
        }
        for name, classification, reason in rows
    ]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8")
