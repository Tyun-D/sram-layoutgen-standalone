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
    endpoint_to_net: dict[str, str] = {}
    endpoint_to_component: dict[str, str | None] = {}
    expected_components: dict[str, set[str]] = {}
    for net_name, endpoints in endpoints_by_net.items():
        for endpoint in endpoints:
            endpoint_name = endpoint["endpoint_name"]
            endpoint_to_net[endpoint_name] = net_name
            component = _component_for_bbox(graph, endpoint["bbox"], {"m1", "m2"})
            endpoint_to_component[endpoint_name] = component
            if component is not None:
                expected_components.setdefault(net_name, set()).add(component)
    for pin_name, bbox in top_pin_bboxes.items():
        endpoint_name = f"TOP.{pin_name}"
        endpoint_to_net[endpoint_name] = pin_name
        component = _component_for_bbox(graph, bbox, {"m1", "m2"})
        endpoint_to_component[endpoint_name] = component
        if component is not None:
            expected_components.setdefault(pin_name, set()).add(component)

    component_to_endpoints: dict[str, set[str]] = {}
    for endpoint_name, component in endpoint_to_component.items():
        if component is not None:
            component_to_endpoints.setdefault(component, set()).add(endpoint_name)

    per_net: list[dict[str, Any]] = []
    missing_expected = 0
    unexpected_endpoints_total = 0
    floating_required = 0
    unexpected_merges: dict[str, list[str]] = {}
    for net_name, endpoints in endpoints_by_net.items():
        expected_set = {item["endpoint_name"] for item in endpoints}
        if net_name in top_pin_bboxes:
            expected_set.add(f"TOP.{net_name}")
        components = sorted(expected_components.get(net_name, set()))
        if not components:
            floating_required += len(expected_set)
            missing_expected += len(expected_set)
            actual_set: set[str] = set()
        else:
            component = components[0]
            actual_set = component_to_endpoints.get(component, set())
            if len({endpoint_to_net[name] for name in actual_set}) > 1:
                unexpected_merges[component] = sorted({endpoint_to_net[name] for name in actual_set})
        missing = sorted(expected_set - actual_set)
        unexpected = sorted(actual_set - expected_set)
        missing_expected += len(missing)
        unexpected_endpoints_total += len(unexpected)
        floating_required += sum(1 for name in expected_set if endpoint_to_component.get(name) is None)
        per_net.append(
            {
                "net_name": net_name,
                "expected_endpoint_set": sorted(expected_set),
                "actual_endpoint_set": sorted(actual_set),
                "missing_endpoints": missing,
                "unexpected_endpoints": unexpected,
                "component_id": components[0] if components else None,
                "net_match_status": "MATCH" if not missing and not unexpected and len(components) == 1 else "MISMATCH",
            }
        )

    top_comp = {name: _component_for_bbox(graph, bbox, {"m1", "m2"}) for name, bbox in top_pin_bboxes.items()}
    actual_components = {
        row["component_id"]
        for row in per_net
        if row["component_id"] is not None
    } | {top_comp["VDD"], top_comp["VSS"]}
    power_signal_short_count = sum(1 for signal in ["D", "Q", "CLK"] if top_comp[signal] in {top_comp["VDD"], top_comp["VSS"]})
    report = {
        "graph": graph,
        "per_net": per_net,
        "expected_net_count": len(endpoints_by_net),
        "actual_net_component_count": len(actual_components),
        "unexpected_net_merges": unexpected_merges,
        "unexpected_net_merge_count": len(unexpected_merges),
        "missing_expected_endpoint_count": missing_expected,
        "unexpected_endpoint_count": unexpected_endpoints_total,
        "floating_required_pin_count": floating_required,
        "power_signal_short_count": power_signal_short_count,
        "vdd_vss_short_present": top_comp["VDD"] == top_comp["VSS"],
        "d_q_direct_short_present": top_comp["D"] == top_comp["Q"],
        "physical_connectivity_verification_passed": len(unexpected_merges) == 0
        and missing_expected == 0
        and floating_required == 0
        and unexpected_endpoints_total == 0
        and power_signal_short_count == 0
        and top_comp["VDD"] != top_comp["VSS"]
        and top_comp["D"] != top_comp["Q"]
        and all(row["net_match_status"] == "MATCH" for row in per_net),
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
                "# DFF Physical Connectivity Report",
                "",
                f"- expected_net_count: `{report['expected_net_count']}`",
                f"- actual_net_component_count: `{report['actual_net_component_count']}`",
                f"- unexpected_net_merge_count: `{report['unexpected_net_merge_count']}`",
                f"- missing_expected_endpoint_count: `{report['missing_expected_endpoint_count']}`",
                f"- unexpected_endpoint_count: `{report['unexpected_endpoint_count']}`",
                f"- physical_connectivity_verification_passed: `{report['physical_connectivity_verification_passed']}`",
                "",
            ]
        ),
        encoding="utf-8",
    )
