from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from .source_connection_expander import expand_source_connections
from .source_module_registry import build_source_registry


TARGET_MODULES = {
    "PINV",
    "TRANSMISSION_GATE",
    "DFF",
    "DFF_BUF",
    "ADDR_DFF",
    "DATA_DFF",
    "PNAND2",
    "PNAND3",
    "AND2",
    "AND3",
    "pdrive",
    "pdrive2_for_pre",
    "wl_pdrive",
    "delay_chain",
    "wen_delay_chain",
    "TIME",
}
def _role_pins(pin_order: list[str]) -> dict[str, list[str]]:
    return {
        "power_pin_names": [pin for pin in pin_order if pin.upper() == "VDD"],
        "ground_pin_names": [pin for pin in pin_order if pin.upper() == "VSS"],
        "clock_pin_names": [pin for pin in pin_order if "CLK" in pin.upper()],
        "control_pin_names": [pin for pin in pin_order if pin.upper() in {"CSB", "WEB", "CS", "WE", "CTR_P", "CTR_N"} or "EN" in pin.upper()],
    }


def _formula_fields(module_name: str) -> dict[str, str]:
    defaults = {
        "instance_count_formula": "constant_per_module_definition",
        "operation_dependency": "none",
        "row_dependency": "none",
        "column_dependency": "none",
        "address_width_dependency": "none",
        "data_width_dependency": "none",
        "drive_scale_dependency": "none",
        "stage_count_dependency": "none",
    }
    if module_name == "ADDR_DFF":
        defaults.update({"instance_count_formula": "ceil(log2(num_rows)) DFF children", "row_dependency": "num_rows", "address_width_dependency": "ceil(log2(num_rows))"})
    elif module_name == "DATA_DFF":
        defaults.update({"instance_count_formula": "num_cols DFF children", "column_dependency": "num_cols", "data_width_dependency": "num_cols"})
    elif module_name == "TIME":
        defaults.update(
            {
                "instance_count_formula": "source topology includes conditional address/data DFF arrays and parameterized drivers",
                "operation_dependency": "read vs write vs read&write",
                "row_dependency": "num_rows",
                "column_dependency": "num_cols",
                "address_width_dependency": "ceil(log2(num_rows))",
                "data_width_dependency": "num_cols when operation includes write",
                "drive_scale_dependency": "clk_drive_scale, pre_drive_scale, w_en_scale",
                "stage_count_dependency": "wen_delay_chain stages conditional; delay_chain fixed",
            }
        )
    return defaults


def _status_for(module_name: str) -> str:
    if module_name in {"TIME", "ADDR_DFF", "DATA_DFF", "pdrive", "pdrive2_for_pre", "wen_delay_chain"}:
        return "SOURCE_EXACT_PARAMETERIZED"
    return "SOURCE_EXACT_RESOLVED"


def extract_source_exact_composite_topology(openyield_root: str | Path) -> dict[str, Any]:
    root = Path(openyield_root)
    registry_payload = build_source_registry(root)
    registry = registry_payload["records"]
    inventory_rows: list[dict[str, Any]] = []
    child_rows: list[dict[str, Any]] = []
    all_branch_net_rows: list[dict[str, Any]] = []
    default_active_net_rows: list[dict[str, Any]] = []
    alias_rows: list[dict[str, Any]] = []
    seen_modules: set[str] = set()
    for key, record in registry.items():
        module_name = record.canonical_module_name
        if module_name not in TARGET_MODULES or module_name in seen_modules:
            continue
        seen_modules.add(module_name)
        expanded = expand_source_connections(record, registry)
        role_info = _role_pins(record.normalized_pin_order)
        internal_nets = sorted(
            {
                row["normalized_parent_net"]
                for row in expanded["net_rows"]
                if row["normalized_parent_net"]
                and row["normalized_parent_net"] not in record.normalized_pin_order
                and row["normalized_parent_net"] not in {"VDD", "VSS"}
            }
        )
        source_hash = hashlib.sha256(
            (
                record.class_name
                + "|"
                + "|".join(record.normalized_pin_order)
                + "|"
                + "|".join(f"{row['instance_name_expression']}:{row['child_module']}" for row in expanded["net_rows"])
            ).encode("utf-8")
        ).hexdigest()[:24]
        inventory_rows.append(
            {
                "module_name": module_name,
                "source_file": record.source_file,
                "source_class": record.class_name,
                "source_function": "__class__",
                "source_line": record.source_line,
                "parent_modules": "",
                "top_pin_order": record.normalized_pin_order,
                **role_info,
                "internal_net_names": internal_nets,
                "source_topology_hash": source_hash,
                "parameter_contract_status": "RESOLVED" if record.normalized_pin_order else "UNRESOLVED",
                "topology_resolution_status": _status_for(module_name) if record.normalized_pin_order else "UNRESOLVED_SYMBOLIC",
                "unresolved_reason": "" if record.normalized_pin_order else record.failure_reason,
                **_formula_fields(module_name),
            }
        )
        for row in expanded["child_rows"]:
            child_rows.append(row)
        for row in expanded["net_rows"]:
            all_branch_net_rows.append(row)
            if row.get("active_in_default_environment"):
                default_active_net_rows.append(row)
        alias_rows.extend(expanded["alias_rows"])

    inventory_rows.sort(key=lambda row: row["module_name"])
    child_rows.sort(key=lambda row: (row["module_name"], int(row["source_line"])))
    all_branch_net_rows.sort(key=lambda row: (row["parent_module"], int(row["source_line"]), str(row["instance_name_expression"]), int(row["child_pin_index"])))
    default_active_net_rows.sort(key=lambda row: (row["parent_module"], int(row["source_line"]), str(row["instance_name_expression"]), int(row["child_pin_index"])))
    return {
        "inventory_rows": inventory_rows,
        "child_rows": child_rows,
        "net_rows": all_branch_net_rows,
        "all_branch_net_rows": all_branch_net_rows,
        "default_active_net_rows": default_active_net_rows,
        "alias_rows": alias_rows,
        "registry_rows": registry_payload["rows"],
        "registry": registry,
    }
