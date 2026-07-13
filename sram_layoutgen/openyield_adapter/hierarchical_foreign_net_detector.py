from __future__ import annotations

from typing import Any

from sram_layoutgen.openyield_adapter.hierarchical_obstacle_model import hierarchical_net_namespace

EPSILON = 1e-6


def _bbox_overlap(a: list[float], b: list[float]) -> list[float] | None:
    lx = max(a[0], b[0])
    by = max(a[1], b[1])
    rx = min(a[2], b[2])
    uy = min(a[3], b[3])
    if rx <= lx + EPSILON or uy <= by + EPSILON:
        return None
    return [round(lx, 6), round(by, 6), round(rx, 6), round(uy, 6)]


def _bbox_area(bbox: list[float]) -> float:
    return round(max(0.0, bbox[2] - bbox[0]) * max(0.0, bbox[3] - bbox[1]), 6)


def detect_hierarchical_foreign_net_contacts(
    *,
    route_objects: list[dict[str, Any]],
    obstacle_objects: list[dict[str, Any]],
) -> dict[str, Any]:
    allowed_by_net = hierarchical_net_namespace()["binding_authorizations"]
    per_route: list[dict[str, Any]] = []
    foreign_count = 0
    unexpected_child_internal_net_contact_count = 0
    clk_clkb_short_present = False
    q_qb_internal_short_present = False
    for route_object in route_objects:
        intended_net = route_object["intended_hierarchical_net"]
        allowed_hierarchical_nets = sorted(allowed_by_net.get(intended_net, []))
        overlaps = []
        contacted_nets = set()
        unexpected_nets = set()
        for obstacle in obstacle_objects:
            if obstacle["layer"] != route_object["layer"]:
                continue
            overlap_bbox = _bbox_overlap(route_object["bbox"], obstacle["transformed_bbox"])
            if overlap_bbox is None:
                continue
            net_name = obstacle["hierarchical_net_identity"]
            contacted_nets.add(net_name)
            if net_name not in allowed_hierarchical_nets:
                unexpected_nets.add(net_name)
                if obstacle["is_internal_net"]:
                    unexpected_child_internal_net_contact_count += 1
            overlaps.append(
                {
                    "contacted_hierarchical_net": net_name,
                    "child_instance": obstacle["child_instance"],
                    "layer": obstacle["layer"],
                    "obstacle_shape_id": obstacle["shape_id"],
                    "overlap_bbox": overlap_bbox,
                    "overlap_area": _bbox_area(overlap_bbox),
                }
            )
        if "dff::CLKB_internal" in unexpected_nets and intended_net == "TOP::CLK":
            clk_clkb_short_present = True
        if "dff::QB_internal" in unexpected_nets and intended_net == "PARENT::qint":
            q_qb_internal_short_present = True
        short_classification = "FOREIGN_NET_CONTACT" if unexpected_nets else "AUTHORIZED_ONLY"
        if unexpected_nets:
            foreign_count += len(unexpected_nets)
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
        "hierarchical_foreign_net_contact_count": foreign_count,
        "unexpected_child_internal_net_contact_count": unexpected_child_internal_net_contact_count,
        "clk_clkb_short_present": clk_clkb_short_present,
        "q_qb_internal_short_present": q_qb_internal_short_present,
    }
