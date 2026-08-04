from __future__ import annotations

from collections import deque
from typing import Any


EPSILON = 1e-6


def _touch_or_overlap(a: list[float], b: list[float]) -> bool:
    return not (a[2] < b[0] - EPSILON or b[2] < a[0] - EPSILON or a[3] < b[1] - EPSILON or b[3] < a[1] - EPSILON)


def _bbox_center(box: list[float]) -> tuple[float, float]:
    return ((box[0] + box[2]) * 0.5, (box[1] + box[3]) * 0.5)


def _bbox_distance(a: list[float], b: list[float]) -> float:
    acx, acy = _bbox_center(a)
    bcx, bcy = _bbox_center(b)
    return abs(acx - bcx) + abs(acy - bcy)


def build_shape_graph(graph: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, set[str]]]:
    rects: dict[str, dict[str, Any]] = {}
    for layer_name, rows in graph.get("rectangles", {}).items():
        for row in rows:
            rects[row["rect_id"]] = {
                "rect_id": row["rect_id"],
                "layer": layer_name,
                "bbox": row["bbox"],
                "source": row.get("source"),
            }
    adjacency: dict[str, set[str]] = {rect_id: set() for rect_id in rects}
    for layer_name, rows in graph.get("rectangles", {}).items():
        if layer_name not in {"m1", "m2", "m3", "via1", "via2", "poly", "active_segments", "contact"}:
            continue
        for idx, left in enumerate(rows):
            for right in rows[idx + 1 :]:
                if _touch_or_overlap(left["bbox"], right["bbox"]):
                    adjacency[left["rect_id"]].add(right["rect_id"])
                    adjacency[right["rect_id"]].add(left["rect_id"])
    for link_map_name in ("contact_links", "via1_links", "via2_links"):
        for rect_id, linked in graph.get(link_map_name, {}).items():
            if rect_id not in rects:
                continue
            adjacency.setdefault(rect_id, set())
            for other in linked:
                if other not in rects:
                    continue
                adjacency.setdefault(other, set())
                adjacency[rect_id].add(other)
                adjacency[other].add(rect_id)
    return rects, adjacency


def build_owner_index(
    *,
    rects: dict[str, dict[str, Any]],
    top_pin_bboxes: dict[str, dict[str, float]],
    top_route_geometry: dict[str, Any],
    integration_route_geometry: dict[str, Any],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    owners: dict[str, list[dict[str, Any]]] = {}
    ownership_rows: list[dict[str, Any]] = []

    def add_owner(shape_bbox: list[float], owner: str, net: str, route_id: str, layer_hint: str | None, segment_key: str) -> None:
        for rect_id, rect in rects.items():
            if layer_hint and rect["layer"] != layer_hint:
                continue
            if _touch_or_overlap(shape_bbox, rect["bbox"]):
                row = {
                    "shape_id": rect_id,
                    "shape_layer": rect["layer"],
                    "shape_bbox": rect["bbox"],
                    "owner": owner,
                    "net": net,
                    "route_id": route_id,
                    "segment_key": segment_key,
                }
                owners.setdefault(rect_id, []).append(row)

    for net_name, bbox in top_pin_bboxes.items():
        add_owner([bbox["lx"], bbox["by"], bbox["rx"], bbox["uy"]], "TOP_PIN", net_name, f"TOP_PIN::{net_name}", bbox.get("layer"), "top_pin_bbox")

    def consume_route(payload: dict[str, Any], owner: str) -> None:
        for route_group, route_map in payload.items():
            if not isinstance(route_map, dict):
                continue
            for route_id, route_row in route_map.items():
                net = route_id if route_group != "power_ties" else route_id.split("_")[-1]
                if isinstance(route_row, dict):
                    for segment_key, segment_val in route_row.items():
                        if isinstance(segment_val, dict) and {"lx", "by", "rx", "uy"} <= set(segment_val):
                            layer_hint = None
                            if "m1" in segment_key:
                                layer_hint = "m1"
                            elif "m2" in segment_key:
                                layer_hint = "m2"
                            elif "m3" in segment_key:
                                layer_hint = "m3"
                            elif "via1" in segment_key:
                                layer_hint = "via1"
                            elif "via2" in segment_key:
                                layer_hint = "via2"
                            add_owner(
                                [segment_val["lx"], segment_val["by"], segment_val["rx"], segment_val["uy"]],
                                owner,
                                net,
                                route_id,
                                layer_hint,
                                segment_key,
                            )

    consume_route(top_route_geometry, "TOP_DECODER_ROUTE")
    consume_route(integration_route_geometry, "PARENT_INTEGRATION_ROUTER")

    for rect_id, rows in owners.items():
        rows.sort(key=lambda row: (row["owner"], row["net"], row["route_id"], row["segment_key"]))
        for row in rows:
            ownership_rows.append(row)
    ownership_rows.sort(key=lambda row: (row["shape_layer"], row["shape_id"], row["owner"], row["net"]))
    return owners, ownership_rows


def shortest_cross_net_witness(
    *,
    graph: dict[str, Any],
    rects: dict[str, dict[str, Any]],
    adjacency: dict[str, set[str]],
    owners: dict[str, list[dict[str, Any]]],
    merged_nets: list[str],
) -> dict[str, Any]:
    net_to_shapes: dict[str, list[str]] = {}
    for shape_id, rows in owners.items():
        for row in rows:
            if row["net"] in merged_nets:
                net_to_shapes.setdefault(row["net"], []).append(shape_id)
    if len(net_to_shapes) < 2:
        return {"witness_found": False, "reason": "insufficient_owned_shapes"}
    root_net = merged_nets[0]
    source_shapes = sorted(set(net_to_shapes.get(root_net, [])))
    best: dict[str, Any] | None = None
    component_lookup = {}
    for component in graph["components"]:
        for shape_id in component["members"]:
            component_lookup[shape_id] = component
    for target_net in merged_nets[1:]:
        target_shapes = sorted(set(net_to_shapes.get(target_net, [])))
        if not target_shapes:
            continue
        queue = deque((shape_id, [shape_id]) for shape_id in source_shapes)
        seen = set(source_shapes)
        target_set = set(target_shapes)
        while queue:
            shape_id, path = queue.popleft()
            if shape_id in target_set:
                candidate = {
                    "source_net": root_net,
                    "target_net": target_net,
                    "path_shape_ids": path,
                    "path_length": len(path),
                }
                if best is None or candidate["path_length"] < best["path_length"]:
                    best = candidate
                break
            neighbors = sorted(adjacency.get(shape_id, []), key=lambda other: _bbox_distance(rects[shape_id]["bbox"], rects[other]["bbox"]))
            for neighbor in neighbors:
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
    if best is None:
        return {"witness_found": False, "reason": "no_cross_net_path_found"}
    detailed_path = []
    first_illegal = None
    prev_net_set: set[str] | None = None
    for idx, shape_id in enumerate(best["path_shape_ids"]):
        row = {
            "shape_id": shape_id,
            "layer": rects[shape_id]["layer"],
            "bbox": rects[shape_id]["bbox"],
            "owners": owners.get(shape_id, []),
            "component_id": component_lookup.get(shape_id, {}).get("component_id"),
        }
        detailed_path.append(row)
        current_nets = {owner["net"] for owner in owners.get(shape_id, [])}
        if idx > 0 and prev_net_set is not None and current_nets and prev_net_set and current_nets != prev_net_set and first_illegal is None:
            first_illegal = {
                "from_shape_id": best["path_shape_ids"][idx - 1],
                "to_shape_id": shape_id,
                "from_nets": sorted(prev_net_set),
                "to_nets": sorted(current_nets),
                "contact_bbox": rects[shape_id]["bbox"],
            }
        if current_nets:
            prev_net_set = current_nets
    return {
        "witness_found": True,
        "source_net": best["source_net"],
        "target_net": best["target_net"],
        "path_shape_ids": best["path_shape_ids"],
        "path_length": best["path_length"],
        "detailed_path": detailed_path,
        "first_illegal_cross_net_contact": first_illegal,
    }
