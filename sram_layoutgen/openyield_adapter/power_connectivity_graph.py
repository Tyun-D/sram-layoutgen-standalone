from __future__ import annotations

from typing import Any


def graph_summary(nodes: list[dict[str, Any]], edges: list[dict[str, Any]]) -> dict[str, Any]:
    vdd_edges = [edge for edge in edges if edge["net_name"] == "VDD"]
    gnd_edges = [edge for edge in edges if edge["net_name"] == "GND"]
    return {
        "nodes": nodes,
        "edges": edges,
        "vdd_graph_connected": bool(vdd_edges),
        "gnd_graph_connected": bool(gnd_edges),
        "power_graph_blocked_edge_count": sum(1 for edge in edges if edge["edge_status"] == "BLOCKED"),
        "power_graph_contract_edge_count": sum(1 for edge in edges if "CONTRACT" in edge["edge_status"]),
    }
