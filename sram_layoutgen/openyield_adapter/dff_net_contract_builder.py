from __future__ import annotations

import json
from collections import defaultdict
from typing import Any

from sram_layoutgen.openyield_adapter.module_pin_role_registry import MODULE_PIN_ROLE_REGISTRY, pin_role

TOP_PINS = ["VDD", "VSS", "D", "Q", "CLK"]
INTERNAL_NETS = ["CLKB", "D_b", "z1", "z2", "z3", "z4", "z5", "QB"]


def build_dff_net_contract(dff_net_rows: list[dict[str, Any]]) -> dict[str, Any]:
    instance_names = sorted({str(row["instance_name_expression"]).strip("'\"") for row in dff_net_rows})
    contract_nets: dict[str, dict[str, Any]] = {
        net: {
            "net_name": net,
            "power_terminals": [],
            "ground_terminals": [],
            "drivers_or_output_terminals": [],
            "loads_or_input_terminals": [],
            "bidirectional_terminals": [],
            "control_terminals": [],
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
                "power_terminals": [],
                "ground_terminals": [],
                "drivers_or_output_terminals": [],
                "loads_or_input_terminals": [],
                "bidirectional_terminals": [],
                "control_terminals": [],
                "connected_child_pins": [],
                "source_lines": [],
                "net_role": "UNKNOWN",
            }
        pin_ref = f"{instance_name}.{pin_name}"
        role = pin_role(child_module, pin_name)
        contract_nets[net_name]["connected_child_pins"].append(pin_ref)
        contract_nets[net_name]["source_lines"].append(int(row["source_line"]))
        if role in {"POWER", "BODY_POWER"}:
            contract_nets[net_name]["power_terminals"].append(pin_ref)
        elif role in {"GROUND", "BODY_GROUND"}:
            contract_nets[net_name]["ground_terminals"].append(pin_ref)
        elif role == "SIGNAL_OUTPUT":
            contract_nets[net_name]["drivers_or_output_terminals"].append(pin_ref)
        elif role == "SIGNAL_INPUT":
            contract_nets[net_name]["loads_or_input_terminals"].append(pin_ref)
        elif role == "BIDIRECTIONAL_SWITCH_TERMINAL":
            contract_nets[net_name]["bidirectional_terminals"].append(pin_ref)
        elif role in {"CONTROL_INPUT", "CLOCK_INPUT"}:
            contract_nets[net_name]["control_terminals"].append(pin_ref)
            contract_nets[net_name]["loads_or_input_terminals"].append(pin_ref)
        if contract_nets[net_name]["net_role"] == "INTERNAL" and role == "BIDIRECTIONAL_SWITCH_TERMINAL":
            contract_nets[net_name]["net_role"] = "BIDIRECTIONAL_SWITCH_NET"
        if net_name == "CLK":
            contract_nets[net_name]["net_role"] = "CLOCK_TOP_PIN"
        elif net_name == "Q":
            contract_nets[net_name]["net_role"] = "TOP_SIGNAL_OUTPUT"
        elif net_name == "D":
            contract_nets[net_name]["net_role"] = "TOP_SIGNAL_INPUT"
        elif net_name == "VDD":
            contract_nets[net_name]["net_role"] = "POWER"
        elif net_name == "VSS":
            contract_nets[net_name]["net_role"] = "GROUND"

    for net in contract_nets.values():
        net["power_terminals"] = sorted(set(net["power_terminals"]))
        net["ground_terminals"] = sorted(set(net["ground_terminals"]))
        net["drivers_or_output_terminals"] = sorted(set(net["drivers_or_output_terminals"]))
        net["loads_or_input_terminals"] = sorted(set(net["loads_or_input_terminals"]))
        net["bidirectional_terminals"] = sorted(set(net["bidirectional_terminals"]))
        net["control_terminals"] = sorted(set(net["control_terminals"]))
        net["connected_child_pins"] = sorted(set(net["connected_child_pins"]))
        net["source_lines"] = sorted(set(net["source_lines"]))

    duplicate_instance_count = len(instance_names) - len(set(instance_names))
    return {
        "top_pins": TOP_PINS,
        "internal_nets": {name: contract_nets[name] for name in INTERNAL_NETS},
        "top_pin_contracts": {name: contract_nets[name] for name in TOP_PINS},
        "dff_top_pin_count": len(TOP_PINS),
        "dff_internal_net_count": len(INTERNAL_NETS),
        "dff_unknown_net_count": len(unknown_nets),
        "dff_unconnected_required_child_pin_count": unconnected_required,
        "dff_duplicate_instance_name_count": duplicate_instance_count,
        "instance_names": instance_names,
        "module_pin_role_registry": MODULE_PIN_ROLE_REGISTRY,
    }
