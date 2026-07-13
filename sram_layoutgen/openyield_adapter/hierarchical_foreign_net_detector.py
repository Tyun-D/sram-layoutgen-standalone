from __future__ import annotations

from typing import Any

from sram_layoutgen.openyield_adapter.hierarchical_obstacle_model import hierarchical_net_namespace

EPSILON = 1e-6


def _validate_rectangle_contract(shape: dict[str, Any]) -> None:
    shape_kind = shape.get("shape_kind")
    bbox_is_exact_geometry = shape.get("bbox_is_exact_geometry")
    if shape_kind != "axis_aligned_rectangle":
        raise ValueError(
            "conductive object rejected: shape_kind must be 'axis_aligned_rectangle' "
            f"for bbox-based contact detection, got {shape_kind!r}"
        )
    if bbox_is_exact_geometry is not True:
        raise ValueError(
            "conductive object rejected: bbox_is_exact_geometry must be True "
            f"for bbox-based contact detection, got {bbox_is_exact_geometry!r}"
        )


def _normalize_bbox(shape: dict[str, Any]) -> list[float]:
    if "bbox" in shape:
        bbox = shape["bbox"]
    elif "transformed_bbox" in shape:
        bbox = shape["transformed_bbox"]
    else:
        raise KeyError("shape must provide bbox or transformed_bbox")
    return [round(float(bbox[0]), 6), round(float(bbox[1]), 6), round(float(bbox[2]), 6), round(float(bbox[3]), 6)]


def _bbox_contact_geometry(a: list[float], b: list[float]) -> dict[str, Any] | None:
    lx = max(a[0], b[0])
    by = max(a[1], b[1])
    rx = min(a[2], b[2])
    uy = min(a[3], b[3])
    if rx < lx - EPSILON or uy < by - EPSILON:
        return None
    width = max(0.0, round(rx - lx, 6))
    height = max(0.0, round(uy - by, 6))
    if width > EPSILON and height > EPSILON:
        kind = "area_overlap"
    elif width > EPSILON or height > EPSILON:
        kind = "edge_touch"
    else:
        kind = "corner_touch"
    return {
        "contact_bbox": [round(lx, 6), round(by, 6), round(rx, 6), round(uy, 6)],
        "contact_area": round(width * height, 6),
        "contact_kind": kind,
    }


def conductive_shapes_touch_or_overlap(
    shape_a: dict[str, Any],
    shape_b: dict[str, Any],
) -> dict[str, Any] | None:
    _validate_rectangle_contract(shape_a)
    _validate_rectangle_contract(shape_b)
    bbox_a = _normalize_bbox(shape_a)
    bbox_b = _normalize_bbox(shape_b)
    layer_a = shape_a["layer"]
    layer_b = shape_b["layer"]
    geometry = _bbox_contact_geometry(bbox_a, bbox_b)
    if geometry is None:
        return None
    if layer_a == layer_b:
        return {
            **geometry,
            "electrically_connected": True,
            "cross_layer_connection": False,
            "reason": "same_layer_distance_zero",
        }
    layer_pair = {layer_a, layer_b}
    if layer_pair == {"via1", "m1"} or layer_pair == {"via1", "m2"}:
        return {
            **geometry,
            "electrically_connected": True,
            "cross_layer_connection": True,
            "reason": "explicit_via_connection",
        }
    return {
        **geometry,
        "electrically_connected": False,
        "cross_layer_connection": True,
        "reason": "cross_layer_without_via",
    }


def detect_hierarchical_foreign_net_contacts(
    *,
    route_objects: list[dict[str, Any]],
    obstacle_objects: list[dict[str, Any]],
) -> dict[str, Any]:
    allowed_by_net = hierarchical_net_namespace()["binding_authorizations"]
    for shape in route_objects:
        _validate_rectangle_contract(shape)
    for shape in obstacle_objects:
        _validate_rectangle_contract(shape)
    per_route: list[dict[str, Any]] = []
    foreign_net_names: set[str] = set()
    foreign_route_net_pairs: set[tuple[str, str]] = set()
    foreign_internal_net_names: set[str] = set()
    foreign_internal_route_net_pairs: set[tuple[str, str]] = set()
    raw_contacting_foreign_obstacle_shape_count = 0
    clk_clkb_short_present = False
    q_qb_internal_short_present = False
    for route_object in route_objects:
        intended_net = route_object["intended_hierarchical_net"]
        allowed_hierarchical_nets = sorted(allowed_by_net.get(intended_net, []))
        overlaps = []
        contacted_nets = set()
        unexpected_nets = set()
        for obstacle in obstacle_objects:
            contact = conductive_shapes_touch_or_overlap(route_object, obstacle)
            if contact is None or not contact["electrically_connected"]:
                continue
            net_name = obstacle["hierarchical_net_identity"]
            contacted_nets.add(net_name)
            if net_name not in allowed_hierarchical_nets:
                unexpected_nets.add(net_name)
                foreign_net_names.add(net_name)
                foreign_route_net_pairs.add((route_object["route_object_id"], net_name))
                raw_contacting_foreign_obstacle_shape_count += 1
                if obstacle["is_internal_net"]:
                    foreign_internal_net_names.add(net_name)
                    foreign_internal_route_net_pairs.add((route_object["route_object_id"], net_name))
            overlaps.append(
                {
                    "contacted_hierarchical_net": net_name,
                    "child_instance": obstacle["child_instance"],
                    "layer": obstacle["layer"],
                    "obstacle_shape_id": obstacle["shape_id"],
                    "contact_bbox": contact["contact_bbox"],
                    "contact_area": contact["contact_area"],
                    "overlap_bbox": contact["contact_bbox"],
                    "overlap_area": contact["contact_area"],
                    "contact_kind": contact["contact_kind"],
                    "reason": contact["reason"],
                }
            )
        if "dff::CLKB_internal" in unexpected_nets and intended_net == "TOP::CLK":
            clk_clkb_short_present = True
        if "dff::QB_internal" in unexpected_nets and intended_net == "PARENT::qint":
            q_qb_internal_short_present = True
        short_classification = "FOREIGN_NET_CONTACT" if unexpected_nets else "AUTHORIZED_ONLY"
        per_route.append(
            {
                "parent_route_id": route_object["route_object_id"],
                "intended_net": intended_net,
                "contacted_hierarchical_nets": sorted(contacted_nets),
                "allowed_hierarchical_nets": allowed_hierarchical_nets,
                "unexpected_hierarchical_nets": sorted(unexpected_nets),
                "overlap_layer": route_object["layer"],
                "overlap_geometry": overlaps,
                "short_classification": short_classification,
            }
        )
    return {
        "per_route": per_route,
        "hierarchical_foreign_net_contact_count": len(foreign_route_net_pairs),
        "unexpected_child_internal_net_contact_count": len(foreign_internal_route_net_pairs),
        "unique_foreign_hierarchical_net_count": len(foreign_net_names),
        "unique_parent_route_foreign_net_pair_count": len(foreign_route_net_pairs),
        "raw_contacting_foreign_obstacle_shape_count": raw_contacting_foreign_obstacle_shape_count,
        "unique_unexpected_child_internal_net_count": len(foreign_internal_net_names),
        "unique_parent_route_unexpected_child_internal_net_pair_count": len(foreign_internal_route_net_pairs),
        "clk_clkb_short_present": clk_clkb_short_present,
        "q_qb_internal_short_present": q_qb_internal_short_present,
        "geometry_domain_contract": {
            "shape_kind_required": "axis_aligned_rectangle",
            "bbox_is_exact_geometry_required": True,
            "epsilon": EPSILON,
        },
    }
