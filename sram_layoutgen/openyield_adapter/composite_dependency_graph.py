from __future__ import annotations

from collections import defaultdict, deque
from typing import Any


def build_composite_dependency_graph(inventory_rows: list[dict[str, Any]], child_rows: list[dict[str, Any]], approved_primitives: set[str]) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: list[dict[str, str]] = []
    children_by_parent: dict[str, set[str]] = defaultdict(set)
    for row in inventory_rows:
        name = str(row["module_name"])
        nodes[name] = {
            "module_name": name,
            "source_file": row["source_file"],
            "node_kind": "TOP_LEVEL_ONLY" if name == "TIME" else "COMPOSITE_PARAMETERIZED_READY",
        }
    for primitive in approved_primitives:
        if primitive in nodes:
            nodes[primitive]["node_kind"] = "APPROVED_REUSABLE_PRIMITIVE"
    for row in child_rows:
        parent = str(row["module_name"])
        child = str(row["child_logical_module"])
        if child not in nodes:
            nodes[child] = {"module_name": child, "source_file": "", "node_kind": "DEVICE_MODEL_NOT_PHYSICAL_CELL"}
        edges.append({"from": parent, "to": child})
        children_by_parent[parent].add(child)
    for name, node in nodes.items():
        if name in {"PNAND2", "PNAND3"}:
            node["node_kind"] = "PRIMITIVE_GENERATOR_REQUIRED"
        elif name in {"AND2", "AND3"}:
            node["node_kind"] = "COMPOSITE_BLOCKED" if any(child in {"PNAND2", "PNAND3"} for child in children_by_parent.get(name, set())) else "COMPOSITE_DEPENDENCY_READY"
        elif name in {"DFF", "DFF_BUF", "ADDR_DFF", "DATA_DFF", "pdrive", "pdrive2_for_pre", "wl_pdrive", "delay_chain", "WenDelayChain"}:
            if all(child in approved_primitives or child in {"DFF", "DFF_BUF"} for child in children_by_parent.get(name, set())):
                node["node_kind"] = "COMPOSITE_DEPENDENCY_READY"
        elif name == "TIME":
            node["node_kind"] = "TOP_LEVEL_ONLY"
    indegree: dict[str, int] = {name: 0 for name in nodes}
    adjacency: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        adjacency[edge["from"]].append(edge["to"])
        indegree[edge["to"]] = indegree.get(edge["to"], 0) + 1
    queue = deque(sorted(name for name, deg in indegree.items() if deg == 0))
    visited = 0
    topo: list[str] = []
    while queue:
        name = queue.popleft()
        topo.append(name)
        visited += 1
        for child in sorted(adjacency.get(name, [])):
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    cycle_count = max(0, len(nodes) - visited)
    matrix_rows = []
    for name, node in sorted(nodes.items()):
        matrix_rows.append(
            {
                "module_name": name,
                "node_kind": node["node_kind"],
                "dependency_children": "|".join(sorted(children_by_parent.get(name, set()))),
                "dependency_count": len(children_by_parent.get(name, set())),
            }
        )
    return {
        "nodes": sorted(nodes.values(), key=lambda row: row["module_name"]),
        "edges": sorted(edges, key=lambda row: (row["from"], row["to"])),
        "matrix_rows": matrix_rows,
        "summary": {
            "dependency_graph_generated": True,
            "dependency_graph_node_count": len(nodes),
            "dependency_graph_edge_count": len(edges),
            "dependency_graph_cycle_count": cycle_count,
            "dependency_graph_acyclic": cycle_count == 0,
        },
    }


def to_dot(graph: dict[str, Any]) -> str:
    lines = ["digraph M12C4CompositeDependencyGraph {"]
    for node in graph["nodes"]:
        lines.append(f'  "{node["module_name"]}" [label="{node["module_name"]}\\n{node["node_kind"]}"];')
    for edge in graph["edges"]:
        lines.append(f'  "{edge["from"]}" -> "{edge["to"]}";')
    lines.append("}")
    return "\n".join(lines) + "\n"
