from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.physical_connectivity_extractor import extract_physical_connectivity


def _shape_to_component(graph: dict[str, Any]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for component in graph["components"]:
        for member in component["members"]:
            lookup[member] = component["component_id"]
    return lookup


def _component_for_bbox(graph: dict[str, Any], bbox: dict[str, float], layers: set[str] | None = None) -> str | None:
    shape_lookup = _shape_to_component(graph)
    cx = round((bbox["lx"] + bbox["rx"]) * 0.5, 6)
    cy = round((bbox["by"] + bbox["uy"]) * 0.5, 6)
    for layer_name, rects in graph.get("rectangles", {}).items():
        if layers and layer_name not in layers:
            continue
        for rect in rects:
            lx, by, rx, uy = rect["bbox"]
            if lx - 1e-6 <= cx <= rx + 1e-6 and by - 1e-6 <= cy <= uy + 1e-6:
                return shape_lookup.get(rect["rect_id"])
    return None


def verify_hierarchical_connectivity(
    *,
    gds_path: Path,
    top_name: str,
    endpoints_by_net: dict[str, list[dict[str, Any]]],
    top_pin_bboxes: dict[str, dict[str, float]],
) -> dict[str, Any]:
    graph = extract_physical_connectivity(gds_path, top_name)
    per_net: list[dict[str, Any]] = []
    component_to_nets: dict[str, set[str]] = {}
    missing_expected = 0
    floating_required = 0
    for net_name, endpoints in endpoints_by_net.items():
        endpoint_ids: list[str] = []
        endpoint_names: list[str] = []
        for endpoint in endpoints:
            component = _component_for_bbox(graph, endpoint["bbox"], {"m1", "m2"})
            endpoint_names.append(endpoint["endpoint_name"])
            if component is None:
                floating_required += 1
                missing_expected += 1
                continue
            endpoint_ids.append(component)
            component_to_nets.setdefault(component, set()).add(net_name)
        if net_name in top_pin_bboxes:
            component = _component_for_bbox(graph, top_pin_bboxes[net_name], {"m1", "m2"})
            endpoint_names.append(f"TOP.{net_name}")
            if component is None:
                floating_required += 1
                missing_expected += 1
            else:
                endpoint_ids.append(component)
                component_to_nets.setdefault(component, set()).add(net_name)
        unique_ids = sorted(set(endpoint_ids))
        per_net.append(
            {
                "net_name": net_name,
                "expected_endpoints": endpoint_names,
                "component_ids": unique_ids,
                "component_count": len(unique_ids),
                "all_endpoints_connected": len(unique_ids) == 1 and len(endpoint_ids) == len(endpoint_names),
            }
        )

    unexpected_merges = {component: sorted(nets) for component, nets in component_to_nets.items() if len(nets) > 1}
    top_comp = {name: _component_for_bbox(graph, bbox, {"m1", "m2"}) for name, bbox in top_pin_bboxes.items()}
    power_signal_short_count = sum(1 for signal in ["D", "Q", "CLK"] if top_comp[signal] in {top_comp["VDD"], top_comp["VSS"]})
    report = {
        "graph": graph,
        "per_net": per_net,
        "expected_net_count": len(endpoints_by_net),
        "actual_net_component_count": len({row["component_ids"][0] for row in per_net if row["component_ids"]}),
        "unexpected_net_merges": unexpected_merges,
        "unexpected_net_merge_count": len(unexpected_merges),
        "missing_expected_endpoint_count": missing_expected,
        "unexpected_endpoint_count": 0,
        "floating_required_pin_count": floating_required,
        "power_signal_short_count": power_signal_short_count,
        "vdd_vss_short_present": top_comp["VDD"] == top_comp["VSS"],
        "d_q_direct_short_present": top_comp["D"] == top_comp["Q"],
        "physical_connectivity_verification_passed": len(unexpected_merges) == 0 and missing_expected == 0 and floating_required == 0 and power_signal_short_count == 0 and top_comp["VDD"] != top_comp["VSS"] and top_comp["D"] != top_comp["Q"] and all(row["all_endpoints_connected"] for row in per_net),
    }
    return report


def write_connectivity_outputs(
    *,
    report: dict[str, Any],
    graph_json_path: Path,
    matrix_csv_path: Path,
    report_json_path: Path,
    report_md_path: Path,
) -> None:
    import csv

    graph_json_path.write_text(json.dumps(report["graph"], indent=2) + "\n", encoding="utf-8")
    with matrix_csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(report["per_net"][0].keys()) if report["per_net"] else [])
        writer.writeheader()
        writer.writerows(report["per_net"])
    slim = {key: value for key, value in report.items() if key != "graph"}
    report_json_path.write_text(json.dumps(slim, indent=2) + "\n", encoding="utf-8")
    report_md_path.write_text(
        "\n".join(
            [
                "# M12C4A DFF Physical Connectivity Report",
                "",
                f"- expected_net_count: `{report['expected_net_count']}`",
                f"- actual_net_component_count: `{report['actual_net_component_count']}`",
                f"- unexpected_net_merge_count: `{report['unexpected_net_merge_count']}`",
                f"- missing_expected_endpoint_count: `{report['missing_expected_endpoint_count']}`",
                f"- physical_connectivity_verification_passed: `{report['physical_connectivity_verification_passed']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
