from __future__ import annotations

import csv
import json
import re
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.clean_top_export import (
    PIN_ROLE_CONTROL,
    ParsedSpiceNetlist,
    SpiceInstance,
    SpiceSubckt,
    canonical_net_name,
    parse_spice_instance_line,
    parse_spice_text,
    parse_subckt_instances,
)
from sram_layoutgen.openyield_adapter.pyspice_source_parser import parse_openyield_pyspice_sources


def build_clean_graph(
    *,
    clean_text: str,
    top_module_name: str,
    top_pin_roles: list[dict[str, Any]],
    parameters: dict[str, Any],
    openyield_root: Path,
    source_trace: dict[str, Any],
) -> dict[str, Any]:
    parsed = parse_spice_text(clean_text)
    module_trace_map = _module_trace_map(openyield_root)
    modules = []
    instances = []
    nets = []
    pins = []
    instance_pin_connections = []
    subckt_by_name = {subckt.name: subckt for subckt in parsed.subckts}

    top_pin_map = {canonical_net_name(item["name"]): item for item in top_pin_roles}

    for subckt in parsed.subckts:
        modules.append(
            {
                "module_name": subckt.name,
                "pin_count": len(subckt.pins),
                "pins": list(subckt.pins),
                "source_trace": module_trace_map.get(subckt.name, _fallback_trace(subckt.name, source_trace)),
            }
        )
        pin_lookup = _pin_lookup_for_module(subckt, subckt_by_name)
        connections_by_net: dict[str, list[dict[str, Any]]] = {}
        for pin in subckt.pins:
            canon = canonical_net_name(pin)
            connections_by_net.setdefault(canon, []).append({"endpoint_type": "module_pin", "endpoint_name": pin})
        for instance in parse_subckt_instances(subckt):
            instances.append(
                {
                    "instance_id": f"{subckt.name}.{instance.name}",
                    "parent_module": subckt.name,
                    "instance_name": instance.name,
                    "instance_type": instance.instance_type,
                    "module_name": instance.module_name,
                    "pin_count": len(instance.nets),
                    "nets": list(instance.nets),
                    "source_trace": module_trace_map.get(instance.module_name, _fallback_trace(instance.module_name, source_trace)),
                }
            )
            pin_names = pin_lookup.get(instance.module_name)
            if pin_names is None and instance.instance_type == "M":
                pin_names = ["D", "G", "S", "B"]
            for index, net in enumerate(instance.nets):
                pin_name = pin_names[index] if pin_names and index < len(pin_names) else f"PIN{index}"
                record = {
                    "parent_module": subckt.name,
                    "instance_name": instance.name,
                    "instance_type": instance.instance_type,
                    "module_name": instance.module_name,
                    "pin_name": pin_name,
                    "pin_index": index,
                    "net_name": net,
                }
                instance_pin_connections.append(record)
                canon = canonical_net_name(net)
                connections_by_net.setdefault(canon, []).append(
                    {
                        "endpoint_type": "instance_pin",
                        "endpoint_name": f"{instance.name}.{pin_name}",
                    }
                )
        for canon, endpoints in sorted(connections_by_net.items()):
            display_name = _display_net_name(canon, subckt, top_pin_map, endpoints)
            nets.append(
                {
                    "module_name": subckt.name,
                    "net_name": display_name,
                    "canonical_name": canon,
                    "connection_count": len(endpoints),
                    "connections": endpoints,
                    "is_top_pin": subckt.name == top_module_name and canon in top_pin_map,
                    "net_role": top_pin_map.get(canon, {}).get("role", "internal"),
                    "source_trace": module_trace_map.get(subckt.name, _fallback_trace(subckt.name, source_trace)),
                }
            )

    for item in top_pin_roles:
        pins.append(
            {
                "module_name": top_module_name,
                "pin_name": item["name"],
                "canonical_name": item["canonical_name"],
                "pin_role": item["role"],
                "source_trace": source_trace,
            }
        )

    return {
        "top_module": top_module_name,
        "parameters": parameters,
        "modules": modules,
        "instances": instances,
        "nets": nets,
        "pins": pins,
        "instance_pin_connections": instance_pin_connections,
        "control_paths": _control_paths(instance_pin_connections),
        "power_nets": [item["name"] for item in top_pin_roles if item["role"] in {"power", "ground"}],
        "source_trace": source_trace,
        "graph_metrics": {
            "module_count": len(modules),
            "instance_count": len(instances),
            "net_count": len(nets),
            "pin_count": len(pins),
        },
    }


def graph_metrics_from_text(clean_text: str) -> dict[str, int]:
    parsed = parse_spice_text(clean_text)
    module_count = len(parsed.subckts)
    instance_count = 0
    for subckt in parsed.subckts:
        instance_count += len(parse_subckt_instances(subckt))
    return {
        "module_count": module_count,
        "instance_count": instance_count,
    }


def verify_graph_against_spice(clean_text: str, graph: dict[str, Any]) -> dict[str, Any]:
    parsed = parse_spice_text(clean_text)
    subckt_by_name = {subckt.name: subckt for subckt in parsed.subckts}
    x_resolved = True
    x_port_match = True
    for subckt in parsed.subckts:
        for instance in parse_subckt_instances(subckt):
            if instance.instance_type == "X":
                target = subckt_by_name.get(instance.module_name)
                if target is None:
                    x_resolved = False
                else:
                    x_port_match = x_port_match and len(target.pins) == len(instance.nets)
            elif instance.instance_type == "M":
                x_port_match = x_port_match and len(instance.nets) == 4
    spice_instance_count = sum(len(parse_subckt_instances(subckt)) for subckt in parsed.subckts)
    spice_net_count = _net_count(parsed)
    return {
        "all_instance_subcircuits_resolved": x_resolved,
        "all_instance_port_counts_match": x_port_match,
        "graph_spice_instance_count_match": spice_instance_count == len(graph["instances"]),
        "graph_spice_module_count_match": len(parsed.subckts) == len(graph["modules"]),
        "graph_spice_net_count_match": spice_net_count == len(graph["nets"]),
        "spice_instance_count": spice_instance_count,
        "spice_module_count": len(parsed.subckts),
        "spice_net_count": spice_net_count,
    }


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _module_trace_map(openyield_root: Path) -> dict[str, dict[str, Any]]:
    parsed_modules, _warnings = parse_openyield_pyspice_sources(openyield_root)
    rows = {item.original_module_name: item for item in parsed_modules}
    mapping: dict[str, dict[str, Any]] = {}
    for key, item in rows.items():
        mapping[key] = {
            "source_file": item.source_file,
            "source_class": item.class_name,
            "source_module_name": item.original_module_name,
            "role_hint": item.role_hint,
        }
    return mapping


def _fallback_trace(module_name: str, source_trace: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_file": source_trace["generator"],
        "source_class": "",
        "source_module_name": module_name,
        "role_hint": "EXTRACTED_FROM_GENERATED_NETLIST",
    }


def _pin_lookup_for_module(subckt: SpiceSubckt, subckt_by_name: dict[str, SpiceSubckt]) -> dict[str, list[str]]:
    lookup: dict[str, list[str]] = {}
    for child in subckt_by_name.values():
        lookup[child.name] = list(child.pins)
    return lookup


def _display_net_name(
    canon: str,
    subckt: SpiceSubckt,
    top_pin_map: dict[str, dict[str, Any]],
    endpoints: list[dict[str, Any]],
) -> str:
    if canon in top_pin_map:
        return top_pin_map[canon]["name"]
    for endpoint in endpoints:
        name = endpoint["endpoint_name"]
        if "." not in name:
            return name
    return canon


def _control_paths(instance_pin_connections: list[dict[str, Any]]) -> list[dict[str, Any]]:
    control_nets = {"wl_en", "s_en", "w_en", "pre", "clk", "csb", "web", "rbl_delay", "rbl_delay_bar"}
    rows: list[dict[str, Any]] = []
    for row in instance_pin_connections:
        if canonical_net_name(row["net_name"]) in control_nets:
            rows.append(
                {
                    "net_name": row["net_name"],
                    "instance_name": row["instance_name"],
                    "module_name": row["module_name"],
                    "pin_name": row["pin_name"],
                    "path_role": PIN_ROLE_CONTROL,
                }
            )
    return rows


def _net_count(parsed: ParsedSpiceNetlist) -> int:
    total = 0
    for subckt in parsed.subckts:
        canon: set[str] = set()
        for pin in subckt.pins:
            canon.add(canonical_net_name(pin))
        for instance in parse_subckt_instances(subckt):
            for net in instance.nets:
                canon.add(canonical_net_name(net))
        total += len(canon)
    return total
