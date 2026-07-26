from __future__ import annotations

from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.delay_chain_contract import stage_driver_role, stage_load_role, stage_net_name
from sram_layoutgen.openyield_adapter.hierarchical_connectivity_verifier import _component_for_bbox, verify_hierarchical_connectivity
from sram_layoutgen.openyield_adapter.physical_connectivity_extractor import extract_physical_connectivity


def build_delay_chain_endpoints(
    *,
    placed_children: list[Any],
    stage_count: int,
    loads_per_stage: int,
    top_pin_bboxes: dict[str, dict[str, float]],
) -> dict[str, list[dict[str, Any]]]:
    by_name = {child.spec.instance_name: child for child in placed_children}
    endpoints: dict[str, list[dict[str, Any]]] = {"VDD": [], "VSS": [], "in": [], "out": []}
    for child in placed_children:
        endpoints["VDD"].append({"endpoint_name": f"{child.spec.instance_name}.VDD", "bbox": child.placed_pin_map["VDD"][0]})
        endpoints["VSS"].append({"endpoint_name": f"{child.spec.instance_name}.VSS", "bbox": child.placed_pin_map["VSS"][0]})
    endpoints["in"].append({"endpoint_name": f"{stage_driver_role(0)}.A", "bbox": by_name[stage_driver_role(0)].placed_pin_map["A"][0]})
    endpoints["out"].append({"endpoint_name": f"{stage_driver_role(stage_count - 1)}.Z", "bbox": by_name[stage_driver_role(stage_count - 1)].placed_pin_map["Z"][0]})
    for stage_index in range(stage_count):
        net_name = stage_net_name(stage_index, stage_count=stage_count)
        stage_rows = [{"endpoint_name": f"{stage_driver_role(stage_index)}.Z", "bbox": by_name[stage_driver_role(stage_index)].placed_pin_map["Z"][0]}]
        for load_index in range(loads_per_stage):
            load = by_name[stage_load_role(stage_index, load_index)]
            stage_rows.append({"endpoint_name": f"{stage_load_role(stage_index, load_index)}.A", "bbox": load.placed_pin_map["A"][0]})
        if stage_index < stage_count - 1:
            nxt = by_name[stage_driver_role(stage_index + 1)]
            stage_rows.append({"endpoint_name": f"{stage_driver_role(stage_index + 1)}.A", "bbox": nxt.placed_pin_map["A"][0]})
        endpoints[net_name] = stage_rows
    return endpoints


def verify_intentional_floating_outputs(
    *,
    gds_path: Path,
    top_name: str,
    placed_children: list[Any],
    stage_count: int,
    loads_per_stage: int,
    top_pin_bboxes: dict[str, dict[str, float]],
) -> dict[str, Any]:
    graph = extract_physical_connectivity(gds_path, top_name)
    power_components = {
        _component_for_bbox(graph, top_pin_bboxes["VDD"], {"m1", "m2"}),
        _component_for_bbox(graph, top_pin_bboxes["VSS"], {"m1", "m2"}),
    }
    def _role_name(child: Any) -> str:
        return child.spec.instance_name if hasattr(child, "spec") else str(child["instance_role"])

    def _z_bbox(child: Any) -> dict[str, float]:
        if hasattr(child, "placed_pin_map"):
            return child.placed_pin_map["Z"][0]
        return child["pin_map"]["Z"][0]

    by_name = {_role_name(child): child for child in placed_children}
    expected_count = stage_count * loads_per_stage
    signal_components: set[str] = set()
    signal_bboxes = [top_pin_bboxes["in"], top_pin_bboxes["out"]]
    for stage_index in range(stage_count):
        signal_bboxes.append(_z_bbox(by_name[stage_driver_role(stage_index)]))
        for load_index in range(loads_per_stage):
            role = stage_load_role(stage_index, load_index)
            if role in by_name:
                child = by_name[role]
                signal_bboxes.append(child["pin_map"]["A"][0] if isinstance(child, dict) else child.placed_pin_map["A"][0])
    for bbox in signal_bboxes:
        component = _component_for_bbox(graph, bbox, {"m1", "m2"})
        if component is not None:
            signal_components.add(component)
    rows = []
    component_to_roles: dict[str, list[str]] = {}
    missing_roles: list[str] = []
    connected_to_stage_net_count = 0
    for stage_index in range(stage_count):
        for load_index in range(loads_per_stage):
            role = stage_load_role(stage_index, load_index)
            if role not in by_name:
                missing_roles.append(role)
                rows.append(
                    {
                        "instance_role": role,
                        "stage_index": stage_index,
                        "load_index": load_index,
                        "component_id": None,
                        "connected_to_power": False,
                        "connected_to_stage_net": False,
                    }
                )
                continue
            bbox = _z_bbox(by_name[role])
            component = _component_for_bbox(graph, bbox, {"m1", "m2"})
            connected_to_stage_net = component in signal_components if component is not None else False
            if connected_to_stage_net:
                connected_to_stage_net_count += 1
            rows.append(
                {
                    "instance_role": role,
                    "stage_index": stage_index,
                    "load_index": load_index,
                    "component_id": component,
                    "connected_to_power": component in power_components if component is not None else False,
                    "connected_to_stage_net": connected_to_stage_net,
                }
            )
            if component is not None:
                component_to_roles.setdefault(component, []).append(role)
    merged_count = sum(1 for roles in component_to_roles.values() if len(roles) > 1)
    connected_to_power_count = sum(1 for row in rows if row["connected_to_power"])
    missing_count = sum(1 for row in rows if row["component_id"] is None)
    return {
        "expected_intentional_floating_output_count": expected_count,
        "intentional_floating_output_count": len(rows),
        "floating_output_components": rows,
        "missing_roles": missing_roles,
        "missing_floating_output_component_count": missing_count,
        "merged_floating_output_component_count": merged_count,
        "floating_output_connected_to_power_count": connected_to_power_count,
        "floating_output_connected_to_stage_net_count": connected_to_stage_net_count,
        "intentional_floating_outputs_exact": len(rows) == expected_count and missing_count == 0 and merged_count == 0 and connected_to_power_count == 0 and connected_to_stage_net_count == 0,
    }
