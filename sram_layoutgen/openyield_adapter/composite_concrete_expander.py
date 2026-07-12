from __future__ import annotations

import json
from math import ceil, log2
from pathlib import Path
from typing import Any


def _address_width(num_rows: int) -> int:
    return ceil(log2(num_rows)) if num_rows > 1 else 1


def _read_resolution_rows(path: Path) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))["rows"]


def _resolution_index(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {(row["source_class"], row["source_instance_path"]): row for row in rows}


def expand_concrete_configuration(config: dict[str, Any]) -> dict[str, Any]:
    num_rows = int(config["num_rows"])
    num_cols = int(config["num_cols"])
    operation = str(config["operation"])
    address_width = _address_width(num_rows)
    data_bits = num_cols if operation in {"write", "read&write"} else 0
    return {
        "config": config,
        "address_width": address_width,
        "ADDR_DFF_bit_count": address_width,
        "DATA_DFF_bit_count": data_bits,
        "DFF_total_count": address_width + data_bits + 2,
        "DFF_BUF_count": 2,
        "AND2_count": 2,
        "AND3_count": 2,
        "PNAND2_count": 2,
        "PNAND3_count": 3,
        "source_template_instance_count": 12,
        "concrete_expanded_instance_count": 12,
    }


def build_concrete_binding_report(
    *,
    config: dict[str, Any],
    resolution_json: Path,
    contract: dict[str, Any],
) -> dict[str, Any]:
    expansion = expand_concrete_configuration(config)
    rows = _read_resolution_rows(resolution_json)
    index = _resolution_index(rows)
    approved_root = contract["approved_reusable_cell_root"]
    config_id = f"R{config['num_rows']}_C{config['num_cols']}_{config['operation']}"
    leaf_rows: list[dict[str, Any]] = []
    failure_rows: list[dict[str, Any]] = []
    for key, row in sorted(index.items()):
        physical = row["canonical_physical_cell_name"]
        binding_status = "APPROVED_PRIMITIVE_BINDING" if physical in contract["approved_geometry_fingerprints"] else "NEW_PRIMITIVE_REQUIRED"
        leaf_rows.append(
            {
                "config_id": config_id,
                "concrete_instance_name": row["source_instance_path"],
                "parent_module": row["source_class"],
                "child_module": physical if physical.startswith("TRANSMISSION_GATE") else "PINV",
                "concrete_parameter_values": json.dumps(
                    {
                        "resolved_nmos_width_nm": row["resolved_nmos_width_nm"],
                        "resolved_pmos_width_nm": row["resolved_pmos_width_nm"],
                        "resolved_channel_length_nm": row["resolved_channel_length_nm"],
                    },
                    sort_keys=True,
                ),
                "parent_net_connections": "",
                "resolved_physical_cell_name": physical,
                "binding_status": binding_status,
                "source_trace": row["resolution_source_trace"],
            }
        )
        if binding_status != "APPROVED_PRIMITIVE_BINDING":
            failure_rows.append(
                {
                    "config_id": config_id,
                    "failure_class": "NEW_PRIMITIVE_REQUIRED",
                    "instance_name": row["source_instance_path"],
                    "parent_module": row["source_class"],
                    "reason": f"{physical} not found in approved reusable contract",
                }
            )
    for composite_name, count in {
        "DFF": expansion["DFF_total_count"],
        "DFF_BUF": expansion["DFF_BUF_count"],
        "AND2": expansion["AND2_count"],
        "AND3": expansion["AND3_count"],
        "PNAND2": expansion["PNAND2_count"],
        "PNAND3": expansion["PNAND3_count"],
    }.items():
        if composite_name in {"PNAND2", "PNAND3"}:
            failure_rows.append(
                {
                    "config_id": config_id,
                    "failure_class": "NEW_PRIMITIVE_REQUIRED",
                    "instance_name": composite_name,
                    "parent_module": "TIME",
                    "reason": "OpenYield PNAND physical primitive is not yet approved",
                }
            )
        else:
            failure_rows.append(
                {
                    "config_id": config_id,
                    "failure_class": "COMPOSITE_CHILD_NOT_YET_GENERATED",
                    "instance_name": composite_name,
                    "parent_module": "TIME",
                    "reason": f"{count} composite child instances remain hierarchical in M12C4R",
                }
            )
    expansion["concrete_leaf_primitive_instance_count"] = len(leaf_rows)
    expansion["concrete_composite_instance_count"] = 12
    expansion["leaf_rows"] = leaf_rows
    expansion["failure_rows"] = failure_rows
    expansion["approved_reusable_root"] = approved_root
    return expansion


def concrete_instance_matrix(expansions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for expansion in expansions:
        cfg = expansion["config"]
        tag = f"R{cfg['num_rows']}_C{cfg['num_cols']}_{cfg['operation']}"
        for key in ["DFF_total_count", "DFF_BUF_count", "AND2_count", "AND3_count", "PNAND2_count", "PNAND3_count"]:
            rows.append({"config_id": tag, "module_name": key.replace("_count", ""), "instance_count": expansion[key]})
    return rows
