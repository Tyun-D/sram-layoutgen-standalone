from __future__ import annotations

from typing import Any


def build_operation_payload(operation_result: dict[str, Any]) -> dict[str, Any]:
    graph = operation_result["graph"]
    top_modules = sorted({row["module_name"] for row in graph["instances"] if row["parent_module"] == graph["top_module"]})
    time_nets = sorted(row["canonical_name"] for row in graph["nets"] if row["module_name"] == "TIME")
    time_children = sorted({row["module_name"] for row in graph["instances"] if row["parent_module"] == "TIME"})
    return {
        "operation": operation_result["operation"],
        "top_module": graph["top_module"],
        "module_count": len(graph["modules"]),
        "instance_count": len(graph["instances"]),
        "net_count": len(graph["nets"]),
        "pin_count": len(graph["pins"]),
        "module_set": sorted({row["module_name"] for row in graph["modules"]}),
        "top_level_module_set": top_modules,
        "top_pin_set": sorted(row["pin_name"] for row in graph["pins"]),
        "time_top_level_pins": _time_pin_list(graph),
        "time_module_children": time_children,
        "time_net_set": time_nets,
        "time_has_data_dff": "DATA_DFF" in time_children,
        "write_path_present": "WRITEDRIVER" in top_modules,
        "sense_path_present": "SENSEAMP" in top_modules,
        "precharge_path_present": "PRECHARGE" in top_modules,
        "delay_chain_present": "delay_chain" in {row["module_name"] for row in graph["modules"]},
        "wen_delay_chain_present": "wen_delay_chain" in {row["module_name"] for row in graph["modules"]},
        "time_control_outputs": sorted(_time_control_outputs(graph)),
    }


def compare_operation_payloads(payloads: dict[str, dict[str, Any]]) -> dict[str, Any]:
    read = payloads["read"]
    write = payloads["write"]
    read_write = payloads["read&write"]
    diff_rows: list[dict[str, Any]] = []

    _append_diff(diff_rows, "TIME_TOP_LEVEL_PIN_SET", read["time_top_level_pins"], write["time_top_level_pins"], read_write["time_top_level_pins"])
    _append_diff(diff_rows, "TIME_MODULE_CHILDREN", read["time_module_children"], write["time_module_children"], read_write["time_module_children"])
    _append_diff(diff_rows, "TOP_LEVEL_MODULE_SET", read["top_level_module_set"], write["top_level_module_set"], read_write["top_level_module_set"])
    _append_diff(diff_rows, "TOP_PIN_SET", read["top_pin_set"], write["top_pin_set"], read_write["top_pin_set"])
    _append_diff(diff_rows, "TIME_NET_SET", read["time_net_set"], write["time_net_set"], read_write["time_net_set"])

    union_modules = sorted(set(read["top_level_module_set"]) | set(write["top_level_module_set"]))
    union_pins = sorted(set(read["top_pin_set"]) | set(write["top_pin_set"]))
    union_time_nets = sorted(set(read["time_net_set"]) | set(write["time_net_set"]))

    superset_ok = (
        read_write["top_level_module_set"] == union_modules
        and read_write["top_pin_set"] == union_pins
        and read_write["time_net_set"] == union_time_nets
        and read_write["time_has_data_dff"] is True
        and read["time_has_data_dff"] is False
        and write["time_has_data_dff"] is True
    )

    if superset_ok:
        status = "READ_WRITE_SUPERSET_CANONICAL"
        canonical = "READ_WRITE_SUPERSET"
        locked = True
        needs_team = False
        human_review_required = False
        can_enter = True
        human_items: list[str] = []
    else:
        status = "TOPOLOGY_VARIANTS_REQUIRE_LOCK"
        canonical = ""
        locked = False
        needs_team = False
        human_review_required = True
        can_enter = False
        human_items = [
            "Review M12C_operation_topology_diff.md and confirm whether one canonical control-logic hardware topology can cover read, write, and read&write without over-constraining the macro implementation."
        ]

    return {
        "diff_rows": diff_rows,
        "operation_topology_status": status,
        "canonical_physical_operation_topology": canonical,
        "canonical_operation_topology_locked": locked,
        "operation_topology_requires_team_confirmation": needs_team,
        "human_review_required": human_review_required,
        "can_enter_physical_implementation_before_topology_lock": can_enter,
        "human_review_required_items": human_items,
    }


def _time_pin_list(graph: dict[str, Any]) -> list[str]:
    for row in graph["modules"]:
        if row["module_name"] == "TIME":
            return list(row["pins"])
    return []


def _time_control_outputs(graph: dict[str, Any]) -> set[str]:
    outputs = set()
    for row in graph["nets"]:
        if row["module_name"] != "TIME":
            continue
        if row["canonical_name"] in {"clk_buf", "clk_bar", "cs_bar", "cs", "we_bar", "we", "gated_clk_bar", "gated_clk_buf", "wl_en", "rbl_delay", "rbl_delay_bar", "s_en", "w_en", "pre"}:
            outputs.add(row["net_name"])
    return outputs


def _append_diff(rows: list[dict[str, Any]], category: str, read_value: list[str], write_value: list[str], read_write_value: list[str]) -> None:
    rows.append(
        {
            "diff_category": category,
            "read_value": "|".join(read_value),
            "write_value": "|".join(write_value),
            "read_write_value": "|".join(read_write_value),
            "read_equals_write": read_value == write_value,
            "read_equals_read_write": read_value == read_write_value,
            "write_equals_read_write": write_value == read_write_value,
        }
    )
