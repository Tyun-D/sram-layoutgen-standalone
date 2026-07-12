from __future__ import annotations

from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.physical_connectivity_extractor import EPSILON, extract_physical_connectivity


def _component_by_pin(graph: dict[str, Any], pin_name: str) -> str | None:
    labels = graph["pin_labels"].get(pin_name, [])
    if not labels:
        return None
    shape_ids = labels[0].get("shape_ids", [])
    if not shape_ids:
        return None
    shape_id = shape_ids[0]
    for component in graph["components"]:
        if shape_id in component["members"]:
            return component["component_id"]
    return None


def _active_segments(graph: dict[str, Any], *, nwell: bool, pwell: bool, nimplant: bool, pimplant: bool) -> list[dict[str, Any]]:
    return [
        segment
        for segment in graph["active_segments"]
        if segment["nwell"] is nwell
        and segment["pwell"] is pwell
        and segment["nimplant"] is nimplant
        and segment["pimplant"] is pimplant
    ]


def _representative_segments(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_component: dict[str, dict[str, Any]] = {}
    for segment in segments:
        bbox = segment["bbox"]
        area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        existing = by_component.get(str(segment["component_id"]))
        if existing is None:
            by_component[str(segment["component_id"])] = {**segment, "_area": area}
            continue
        if area > existing["_area"]:
            by_component[str(segment["component_id"])] = {**segment, "_area": area}
    return [{key: value for key, value in segment.items() if key != "_area"} for segment in by_component.values()]


def _sorted_left_right(segments: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, Any]]:
    ordered = sorted(segments, key=lambda segment: (segment["bbox"][0] + segment["bbox"][2]) * 0.5)
    if len(ordered) != 2:
        raise ValueError(f"expected exactly 2 diffusion terminals, got {len(ordered)}")
    return ordered[0], ordered[1]


def _component_of_segment(segment: dict[str, Any]) -> str:
    return str(segment["component_id"])


def _metal_only_component(graph: dict[str, Any], pin_name: str) -> str | None:
    labels = graph["pin_labels"].get(pin_name, [])
    if not labels or not labels[0].get("shape_ids"):
        return None
    shape_id = labels[0]["shape_ids"][0]
    component_map: dict[str, set[str]] = {}
    for component in graph["components"]:
        metal_members = {member for member in component["members"] if member.startswith("m1_") or member.startswith("contact_")}
        if metal_members:
            component_map[component["component_id"]] = metal_members
    for component_id, members in component_map.items():
        if shape_id in members:
            return component_id
    return None


def verify_transmission_gate_connectivity(gds_path: Path, top_name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    graph = extract_physical_connectivity(gds_path, top_name)
    pin_components = {pin: _component_by_pin(graph, pin) for pin in ("IN", "OUT", "VDD", "VSS", "CTR_P", "CTR_N")}

    pmos_terminals = _representative_segments(_active_segments(graph, nwell=True, pwell=False, nimplant=False, pimplant=True))
    nmos_terminals = _representative_segments(_active_segments(graph, nwell=False, pwell=True, nimplant=True, pimplant=False))
    nwell_taps = _representative_segments(_active_segments(graph, nwell=True, pwell=False, nimplant=True, pimplant=False))
    pwell_taps = _representative_segments(_active_segments(graph, nwell=False, pwell=True, nimplant=False, pimplant=True))

    pmos_left, pmos_right = _sorted_left_right(pmos_terminals)
    nmos_left, nmos_right = _sorted_left_right(nmos_terminals)

    pin_to_expected = {
        "IN": sorted({_component_of_segment(pmos_left), _component_of_segment(nmos_left)}),
        "OUT": sorted({_component_of_segment(pmos_right), _component_of_segment(nmos_right)}),
    }
    ctr_p_component = pin_components["CTR_P"]
    ctr_n_component = pin_components["CTR_N"]
    vdd_component = pin_components["VDD"]
    vss_component = pin_components["VSS"]

    exclusives = [
        ("IN", "OUT"),
        ("IN", "VDD"),
        ("IN", "VSS"),
        ("OUT", "VDD"),
        ("OUT", "VSS"),
        ("VDD", "VSS"),
        ("CTR_P", "CTR_N"),
        ("CTR_P", "IN"),
        ("CTR_P", "OUT"),
        ("CTR_P", "VDD"),
        ("CTR_P", "VSS"),
        ("CTR_N", "IN"),
        ("CTR_N", "OUT"),
        ("CTR_N", "VDD"),
        ("CTR_N", "VSS"),
    ]

    assertions: list[dict[str, Any]] = []

    def add_assertion(name: str, passed: bool, details: Any) -> None:
        assertions.append({"assertion": name, "passed": bool(passed), "details": details})

    for left, right in exclusives:
        add_assertion(f"{left}_not_equal_{right}", pin_components[left] is not None and pin_components[left] != pin_components[right], {"left": pin_components[left], "right": pin_components[right]})

    add_assertion("IN_connects_pmos_left_terminal", pin_components["IN"] == _component_of_segment(pmos_left), pmos_left)
    add_assertion("IN_connects_nmos_left_terminal", pin_components["IN"] == _component_of_segment(nmos_left), nmos_left)
    add_assertion("OUT_connects_pmos_right_terminal", pin_components["OUT"] == _component_of_segment(pmos_right), pmos_right)
    add_assertion("OUT_connects_nmos_right_terminal", pin_components["OUT"] == _component_of_segment(nmos_right), nmos_right)

    pmos_gate_shapes = graph["pin_labels"].get("CTR_P", [])
    nmos_gate_shapes = graph["pin_labels"].get("CTR_N", [])
    add_assertion("CTR_P_has_m1_shape", bool(pmos_gate_shapes and pmos_gate_shapes[0]["shape_ids"]), pmos_gate_shapes)
    add_assertion("CTR_N_has_m1_shape", bool(nmos_gate_shapes and nmos_gate_shapes[0]["shape_ids"]), nmos_gate_shapes)
    add_assertion("VDD_connects_nwell_tap", len(nwell_taps) == 1 and vdd_component == _component_of_segment(nwell_taps[0]), nwell_taps)
    add_assertion("VSS_connects_pwell_tap", len(pwell_taps) == 1 and vss_component == _component_of_segment(pwell_taps[0]), pwell_taps)

    metal_only_in = _metal_only_component(graph, "IN")
    metal_only_out = _metal_only_component(graph, "OUT")
    add_assertion("IN_OUT_no_direct_metal_path", metal_only_in is not None and metal_only_in != metal_only_out, {"IN_metal": metal_only_in, "OUT_metal": metal_only_out})

    component_lookup = {component["component_id"]: component for component in graph["components"]}
    ctr_p_component_layers = component_lookup.get(ctr_p_component or "", {}).get("layers", [])
    ctr_n_component_layers = component_lookup.get(ctr_n_component or "", {}).get("layers", [])
    add_assertion("CTR_P_component_includes_poly_and_m1", {"poly", "m1", "contact"}.issubset(set(ctr_p_component_layers)), ctr_p_component_layers)
    add_assertion("CTR_N_component_includes_poly_and_m1", {"poly", "m1", "contact"}.issubset(set(ctr_n_component_layers)), ctr_n_component_layers)

    add_assertion("all_six_pins_present", all(pin_components.values()), pin_components)

    passed_count = sum(1 for item in assertions if item["passed"])
    report = {
        "physical_connectivity_verification_passed": passed_count == len(assertions),
        "connectivity_assertion_count": len(assertions),
        "connectivity_assertion_pass_count": passed_count,
        "connectivity_assertion_failure_count": len(assertions) - passed_count,
        "pin_components": pin_components,
        "expected_signal_terminal_components": pin_to_expected,
        "pmos_terminal_components": {"left": _component_of_segment(pmos_left), "right": _component_of_segment(pmos_right)},
        "nmos_terminal_components": {"left": _component_of_segment(nmos_left), "right": _component_of_segment(nmos_right)},
        "nwell_tap_component": _component_of_segment(nwell_taps[0]) if len(nwell_taps) == 1 else None,
        "pwell_tap_component": _component_of_segment(pwell_taps[0]) if len(pwell_taps) == 1 else None,
        "mutually_exclusive_pairs_checked": len(exclusives),
        "assertions": assertions,
        "in_connected_to_vdd_after_repair": pin_components["IN"] == pin_components["VDD"],
        "in_connected_to_vss_after_repair": pin_components["IN"] == pin_components["VSS"],
        "out_connected_to_vdd_after_repair": pin_components["OUT"] == pin_components["VDD"],
        "out_connected_to_vss_after_repair": pin_components["OUT"] == pin_components["VSS"],
        "vdd_connected_to_vss_after_repair": pin_components["VDD"] == pin_components["VSS"],
        "in_directly_connected_to_out_after_repair": pin_components["IN"] == pin_components["OUT"],
        "ctr_p_metal1_pin_added": any(shape["shape_ids"] for shape in pmos_gate_shapes),
        "ctr_n_metal1_pin_added": any(shape["shape_ids"] for shape in nmos_gate_shapes),
        "ctr_p_poly_contact_added": "contact" in ctr_p_component_layers,
        "ctr_n_poly_contact_added": "contact" in ctr_n_component_layers,
        "all_six_pins_metal_accessible": all(pin_components.values()),
    }
    return graph, report


def render_transmission_gate_connectivity_report(report: dict[str, Any]) -> str:
    lines = [
        "# M12C3A3 Physical Connectivity Report",
        "",
        f"- physical_connectivity_verification_passed: `{report['physical_connectivity_verification_passed']}`",
        f"- connectivity_assertion_count: `{report['connectivity_assertion_count']}`",
        f"- connectivity_assertion_pass_count: `{report['connectivity_assertion_pass_count']}`",
        f"- connectivity_assertion_failure_count: `{report['connectivity_assertion_failure_count']}`",
        f"- DRC zero markers alone do not prove correct connectivity: `True`",
        "",
        "## Assertions",
        "",
    ]
    for assertion in report["assertions"]:
        lines.append(f"- {assertion['assertion']}: `{assertion['passed']}`")
    lines.append("")
    return "\n".join(lines)
