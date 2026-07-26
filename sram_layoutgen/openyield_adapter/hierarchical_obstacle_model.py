from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.physical_connectivity_extractor import extract_physical_connectivity


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _rect_polygon(bbox: list[float]) -> list[list[float]]:
    lx, by, rx, uy = bbox
    return [
        [round(lx, 6), round(by, 6)],
        [round(rx, 6), round(by, 6)],
        [round(rx, 6), round(uy, 6)],
        [round(lx, 6), round(uy, 6)],
    ]


def _shift_bbox(bbox: list[float], dx: float, dy: float) -> list[float]:
    return [
        round(float(bbox[0]) + dx, 6),
        round(float(bbox[1]) + dy, 6),
        round(float(bbox[2]) + dx, 6),
        round(float(bbox[3]) + dy, 6),
    ]


def _bbox_overlaps(a: list[float], b: list[float]) -> bool:
    return not (a[2] <= b[0] or b[2] <= a[0] or a[3] <= b[1] or b[3] <= a[1])


def _component_lookup(graph: dict[str, Any]) -> dict[str, str]:
    return {member: component["component_id"] for component in graph["components"] for member in component["members"]}


def _component_map_from_connectivity(
    *,
    instance_name: str,
    connectivity: dict[str, Any],
    graph: dict[str, Any],
) -> dict[str, str]:
    if "per_net" in connectivity:
        return {
            row["component_id"]: _net_name_to_hierarchical(instance_name, row["net_name"])
            for row in connectivity["per_net"]
        }
    shape_to_component = _component_lookup(graph)
    component_map: dict[str, str] = {}
    for label_text, entries in connectivity.get("pin_labels", {}).items():
        try:
            hierarchical_name = _net_name_to_hierarchical(instance_name, label_text)
        except KeyError:
            continue
        for entry in entries:
            for shape_id in entry.get("shape_ids", []):
                component_id = shape_to_component.get(shape_id)
                if component_id is not None:
                    component_map[component_id] = hierarchical_name
    return component_map


def _net_name_to_hierarchical(instance_name: str, raw_net_name: str) -> str:
    if instance_name == "dff":
        mapping = {
            "VDD": "dff::VDD",
            "VSS": "dff::VSS",
            "D": "dff::D",
            "Q": "dff::Q",
            "CLK": "dff::CLK",
            "CLKB": "dff::CLKB_internal",
            "D_b": "dff::D_b_internal",
            "z1": "dff::z1_internal",
            "z2": "dff::z2_internal",
            "z3": "dff::z3_internal",
            "z4": "dff::z4_internal",
            "z5": "dff::z5_internal",
            "QB": "dff::QB_internal",
        }
        return mapping[raw_net_name]
    if instance_name in {"inv1", "inv2"}:
        return f"{instance_name}::{raw_net_name}"
    raise KeyError(f"Unsupported child instance for hierarchical naming: {instance_name}")


def hierarchical_net_namespace() -> dict[str, Any]:
    return {
        "top_level_nets": ["TOP::VDD", "TOP::VSS", "TOP::D", "TOP::CLK", "TOP::Q", "TOP::QB"],
        "parent_internal_nets": ["PARENT::qint"],
        "dff_nets": [
            "dff::VDD",
            "dff::VSS",
            "dff::D",
            "dff::Q",
            "dff::CLK",
            "dff::CLKB_internal",
            "dff::D_b_internal",
            "dff::z1_internal",
            "dff::z2_internal",
            "dff::z3_internal",
            "dff::z4_internal",
            "dff::z5_internal",
            "dff::QB_internal",
        ],
        "inv1_nets": ["inv1::A", "inv1::Z", "inv1::VDD", "inv1::VSS"],
        "inv2_nets": ["inv2::A", "inv2::Z", "inv2::VDD", "inv2::VSS"],
        "binding_authorizations": {
            "TOP::D": ["dff::D"],
            "TOP::CLK": ["dff::CLK"],
            "PARENT::qint": ["dff::Q", "inv1::A"],
            "TOP::QB": ["inv1::Z", "inv2::A"],
            "TOP::Q": ["inv2::Z"],
            "TOP::VDD": ["dff::VDD", "inv1::VDD", "inv2::VDD"],
            "TOP::VSS": ["dff::VSS", "inv1::VSS", "inv2::VSS"],
        },
        "notes": [
            "TOP::QB is distinct from dff::QB_internal.",
            "PARENT::qint may connect only to dff::Q and inv1::A.",
            "TOP::CLK may connect only to dff::CLK.",
        ],
    }


def build_child_conductive_obstacle_map(
    *,
    placement_rows: list[dict[str, Any]],
    child_source_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    source_by_instance = {row["instance_name"]: row for row in child_source_rows}
    object_rows: list[dict[str, Any]] = []
    summary_rows: list[dict[str, Any]] = []
    for placement in placement_rows:
        instance_name = placement["instance_name"]
        source_row = source_by_instance[instance_name]
        origin = json.loads(placement["pin_transform"])
        origin_x = float(origin["origin_x"])
        origin_y = float(origin["origin_y"])
        gds_path = Path(source_row["approved_physical_source_path"])
        top_name = source_row["resolved_physical_cell_name"]
        pin_map = _read_json(Path(source_row["approved_pin_map_path"]))
        graph = extract_physical_connectivity(gds_path, top_name)
        connectivity_path = Path(source_row["approved_pin_map_path"]).with_name(f"{top_name}_physical_connectivity.json")
        if not connectivity_path.exists():
            connectivity_path = Path(source_row["approved_pin_map_path"]).with_name(f"{top_name}_connectivity.json")
        if not connectivity_path.exists():
            connectivity_path = gds_path.with_name(f"{top_name}_physical_connectivity.json")
        if not connectivity_path.exists():
            connectivity_path = Path(str(gds_path).replace(".gds", "_connectivity.json"))
        connectivity = _read_json(connectivity_path)
        component_to_hierarchical = _component_map_from_connectivity(
            instance_name=instance_name,
            connectivity=connectivity,
            graph=graph,
        )
        top_pin_bboxes = {}
        for raw_pin, pin in pin_map.items():
            pin_bbox = pin[0] if isinstance(pin, list) else pin
            top_pin_bboxes[_net_name_to_hierarchical(instance_name, raw_pin)] = [
                float(pin_bbox["lx"]),
                float(pin_bbox["by"]),
                float(pin_bbox["rx"]),
                float(pin_bbox["uy"]),
            ]
        shape_to_component = _component_lookup(graph)
        for layer_name in ("m1", "via1", "m2"):
            for rect in graph["rectangles"].get(layer_name, []):
                component_id = shape_to_component.get(rect["rect_id"])
                hierarchical_net = component_to_hierarchical.get(component_id)
                if hierarchical_net is None:
                    continue
                shifted_bbox = _shift_bbox(rect["bbox"], origin_x, origin_y)
                top_pin_bbox = top_pin_bboxes.get(hierarchical_net)
                is_top_pin = top_pin_bbox is not None and _bbox_overlaps(shifted_bbox, _shift_bbox(top_pin_bbox, origin_x, origin_y))
                is_power = hierarchical_net.endswith("::VDD") or hierarchical_net.endswith("::VSS")
                is_internal_net = hierarchical_net.startswith("dff::") and hierarchical_net.endswith("_internal")
                parent_access_allowed = not is_internal_net
                object_rows.append(
                    {
                        "child_instance": instance_name,
                        "child_cell": top_name,
                        "hierarchical_net_identity": hierarchical_net,
                        "layer": layer_name,
                        "layer_datatype": "11/0" if layer_name == "m1" else "12/0" if layer_name == "via1" else "13/0",
                        "component_id": component_id,
                        "shape_id": rect["rect_id"],
                        "transformed_bbox": shifted_bbox,
                        "transformed_polygon": _rect_polygon(shifted_bbox),
                        "is_top_pin": is_top_pin,
                        "is_internal_net": is_internal_net,
                        "is_power": is_power,
                        "parent_access_allowed": parent_access_allowed,
                        "shape_kind": "axis_aligned_rectangle",
                        "bbox_is_exact_geometry": True,
                    }
                )
        summary_rows.append(
            {
                "child_instance": instance_name,
                "child_cell": top_name,
                "conductive_object_count": sum(1 for row in object_rows if row["child_instance"] == instance_name),
                "internal_object_count": sum(1 for row in object_rows if row["child_instance"] == instance_name and row["is_internal_net"]),
                "forbidden_parent_access_object_count": sum(1 for row in object_rows if row["child_instance"] == instance_name and not row["parent_access_allowed"]),
            }
        )
    return {
        "hierarchical_namespace": hierarchical_net_namespace(),
        "objects": object_rows,
        "summary_rows": summary_rows,
    }
