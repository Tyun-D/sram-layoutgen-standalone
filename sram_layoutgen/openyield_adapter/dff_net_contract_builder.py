from __future__ import annotations

from collections import defaultdict
from typing import Any


TOP_PINS = ["VDD", "VSS", "D", "Q", "CLK"]
INTERNAL_NETS = ["CLKB", "D_b", "z1", "z2", "z3", "z4", "z5", "QB"]


def _pin_role(child_module: str, pin_name: str) -> str:
    if child_module == "PINV":
        return "INVERTER_INPUT" if pin_name == "A" else "INVERTER_OUTPUT"
    if child_module == "TRANSMISSION_GATE":
        if pin_name in {"IN", "OUT"}:
            return "BIDIRECTIONAL_SWITCH_TERMINAL"
        return "CONTROL_GATE_INPUT"
    return "UNKNOWN"


def build_dff_net_contract(dff_net_rows: list[dict[str, Any]]) -> dict[str, Any]:
    instance_names = sorted({str(row["instance_name_expression"]).strip("'\"") for row in dff_net_rows})
    contract_nets: dict[str, dict[str, Any]] = {
        net: {
            "net_name": net,
            "drivers_or_output_terminals": [],
            "loads_or_input_terminals": [],
            "connected_child_pins": [],
            "source_lines": [],
            "net_role": "TOP_PIN" if net in TOP_PINS else "INTERNAL",
        }
        for net in [*TOP_PINS, *INTERNAL_NETS]
    }
    unknown_nets: set[str] = set()
    unconnected_required = 0
    for row in dff_net_rows:
        net_name = row["normalized_parent_net"]
        instance_name = str(row["instance_name_expression"]).strip("'\"")
        child_module = row["child_module"]
        pin_name = row["child_pin_name"]
        if not net_name:
            unconnected_required += 1
            continue
        if net_name not in contract_nets:
            unknown_nets.add(net_name)
            contract_nets[net_name] = {
                "net_name": net_name,
                "drivers_or_output_terminals": [],
                "loads_or_input_terminals": [],
                "connected_child_pins": [],
                "source_lines": [],
                "net_role": "UNKNOWN",
            }
        pin_ref = f"{instance_name}.{pin_name}"
        role = _pin_role(child_module, pin_name)
        contract_nets[net_name]["connected_child_pins"].append(pin_ref)
        contract_nets[net_name]["source_lines"].append(int(row["source_line"]))
        if role in {"INVERTER_OUTPUT", "BIDIRECTIONAL_SWITCH_TERMINAL"}:
            contract_nets[net_name]["drivers_or_output_terminals"].append(pin_ref)
        if role in {"INVERTER_INPUT", "CONTROL_GATE_INPUT", "BIDIRECTIONAL_SWITCH_TERMINAL"}:
            contract_nets[net_name]["loads_or_input_terminals"].append(pin_ref)
        if contract_nets[net_name]["net_role"] == "INTERNAL" and role == "BIDIRECTIONAL_SWITCH_TERMINAL":
            contract_nets[net_name]["net_role"] = "BIDIRECTIONAL_SWITCH_NET"

    for net in contract_nets.values():
        net["drivers_or_output_terminals"] = sorted(set(net["drivers_or_output_terminals"]))
        net["loads_or_input_terminals"] = sorted(set(net["loads_or_input_terminals"]))
        net["connected_child_pins"] = sorted(set(net["connected_child_pins"]))
        net["source_lines"] = sorted(set(net["source_lines"]))

    return {
        "top_pins": TOP_PINS,
        "internal_nets": {name: contract_nets[name] for name in INTERNAL_NETS},
        "top_pin_contracts": {name: contract_nets[name] for name in TOP_PINS},
        "dff_top_pin_count": len(TOP_PINS),
        "dff_internal_net_count": len(INTERNAL_NETS),
        "dff_unknown_net_count": len(unknown_nets),
        "dff_unconnected_required_child_pin_count": unconnected_required,
        "dff_duplicate_instance_name_count": 0,
    }
