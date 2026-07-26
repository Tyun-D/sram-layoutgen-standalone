from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.physical_connectivity_extractor import extract_physical_connectivity
from sram_layoutgen.openyield_adapter.pnand2_verification_gate import direct_top_labels_report, json_safe, sha256_file, write_json, write_text
from sram_layoutgen.openyield_adapter.pnand3_source_lock import EXPECTED_OPENYIELD_COMMIT, EXPECTED_STANDARD_CELL_BLOB
from sram_layoutgen.openyield_adapter.production_negative_test_harness import (
    MutationCase,
    add_label,
    add_off_grid_rect,
    load_completed_checkpoint,
    remove_label,
    run_contract_mutation,
    run_determinism_mutation,
    run_gds_geometry_mutation,
    run_gds_label_mutation,
    run_gds_short_mutation,
    swap_labels,
    write_case_checkpoint,
    write_negative_test_matrix,
    write_negative_test_summary,
)
from sram_layoutgen.tech import Tech


PNAND3_NAME = "PNAND3_NW180_PW270_L50_FPDK45"


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _replace_json_value(path: Path, key: str, value: Any) -> None:
    payload = _json(path)
    payload[key] = value
    write_json(path, payload)


def _replace_reference_lines(path: Path, replacements: dict[str, str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines:
        key = line.split()[0] if line.strip() else ""
        out.append(replacements.get(key, line))
    write_text(path, "\n".join(out))


def _delete_bbox_region(gds_path: Path, bbox: dict[str, float]) -> None:
    lib = gdstk.read_gds(gds_path)
    for cell in lib.cells:
        victims = []
        for poly in cell.polygons:
            pb = poly.bounding_box()
            if pb is None:
                continue
            if not (
                float(pb[1][0]) < bbox["lx"]
                or float(pb[0][0]) > bbox["rx"]
                or float(pb[1][1]) < bbox["by"]
                or float(pb[0][1]) > bbox["uy"]
            ):
                victims.append(poly)
        if victims:
            cell.remove(*victims)
    lib.write_gds(gds_path)


def _shape_lookup(graph: dict[str, Any]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for comp in graph["components"]:
        for member in comp["members"]:
            lookup[member] = comp["component_id"]
    return lookup


def _first_rect(graph: dict[str, Any], component_id: str, preferred_layers: list[str]) -> tuple[str, list[float]] | None:
    comp = next(item for item in graph["components"] if item["component_id"] == component_id)
    members = set(comp["members"])
    for layer in preferred_layers:
        if layer == "active_segment":
            for rect in graph.get("active_segments", []):
                if rect["segment_id"] in members:
                    return layer, rect["bbox"]
        else:
            for rect in graph["rectangles"].get(layer, []):
                if rect["rect_id"] in members:
                    return layer, rect["bbox"]
    return None


def _component_from_bbox(graph: dict[str, Any], bbox: dict[str, float], layers: set[str]) -> str | None:
    from sram_layoutgen.openyield_adapter.hierarchical_connectivity_verifier import _component_for_bbox

    return _component_for_bbox(graph, bbox, layers)


def _bridge_components(clean_gds: Path, left_component: str, right_component: str) -> None:
    graph = extract_physical_connectivity(clean_gds, PNAND3_NAME)
    left = _first_rect(graph, left_component, ["m1", "active_segment"])
    right = _first_rect(graph, right_component, ["m1", "active_segment"])
    if left is None or right is None:
        raise RuntimeError("unable to locate components for bridge mutation")
    grid = 0.0025

    def snap(value: float) -> float:
        return round(round(value / grid) * grid, 6)

    before_shape_count = sum(len(v) for v in graph.get("rectangles", {}).values()) + len(graph.get("active_segments", []))
    before_component_count = len(graph.get("components", []))
    lib = gdstk.read_gds(clean_gds)
    top = next(cell for cell in lib.cells if cell.name == PNAND3_NAME)
    anchors = []
    bridge_layers: list[str] = []
    endpoint_specs = []
    for layer_name, bbox in [left, right]:
        cx = snap((bbox[0] + bbox[2]) * 0.5)
        cy = snap((bbox[1] + bbox[3]) * 0.5)
        if layer_name == "active_segment":
            top.add(gdstk.rectangle((snap(cx - 0.0325), snap(cy - 0.0325)), (snap(cx + 0.0325), snap(cy + 0.0325)), layer=10, datatype=0))
            top.add(gdstk.rectangle((snap(cx - 0.045), snap(cy - 0.045)), (snap(cx + 0.045), snap(cy + 0.045)), layer=11, datatype=0))
            bridge_layers.extend(["contact", "m1"])
        endpoint_specs.append((layer_name, bbox, cx, cy))
        anchors.append((cx, cy))
    y = snap((anchors[0][1] + anchors[1][1]) * 0.5)
    width = 0.065
    for layer_name, bbox, cx, cy in endpoint_specs:
        if abs(cy - y) > 1e-6:
            top.add(
                gdstk.rectangle(
                    (snap(cx - width / 2), snap(min(cy, y))),
                    (snap(cx + width / 2), snap(max(cy, y))),
                    layer=11,
                    datatype=0,
                )
            )
            bridge_layers.append("m1")
    top.add(gdstk.rectangle((snap(min(anchors[0][0], anchors[1][0])), snap(y - width / 2)), (snap(max(anchors[0][0], anchors[1][0])), snap(y + width / 2)), layer=11, datatype=0))
    bridge_layers.append("m1")
    lib.write_gds(clean_gds)
    after_graph = extract_physical_connectivity(clean_gds, PNAND3_NAME)
    after_shape_count = sum(len(v) for v in after_graph.get("rectangles", {}).values()) + len(after_graph.get("active_segments", []))
    after_component_count = len(after_graph.get("components", []))
    def locate_after(layer_name: str, bbox: list[float]) -> str | None:
        cx = snap((bbox[0] + bbox[2]) * 0.5)
        cy = snap((bbox[1] + bbox[3]) * 0.5)
        if layer_name == "active_segment":
            row = next((seg for seg in after_graph.get("active_segments", []) if seg["bbox"][0] - 1e-6 <= cx <= seg["bbox"][2] + 1e-6 and seg["bbox"][1] - 1e-6 <= cy <= seg["bbox"][3] + 1e-6), None)
            return row["component_id"] if row else None
        row = next((rect for rect in after_graph.get("rectangles", {}).get(layer_name, []) if rect["bbox"][0] - 1e-6 <= cx <= rect["bbox"][2] + 1e-6 and rect["bbox"][1] - 1e-6 <= cy <= rect["bbox"][3] + 1e-6), None)
        if row is None:
            return None
        for comp in after_graph["components"]:
            if row["rect_id"] in comp["members"]:
                return comp["component_id"]
        return None
    left_after = locate_after(left[0], left[1])
    right_after = locate_after(right[0], right[1])
    proof = {
        "baseline_sha256": None,
        "mutated_sha256": None,
        "shape_count_before": before_shape_count,
        "shape_count_after": after_shape_count,
        "left_component_before": left_component,
        "right_component_before": right_component,
        "bridge_geometry": {"anchors": anchors, "track_y": y},
        "bridge_layers": bridge_layers,
        "component_count_before": before_component_count,
        "component_count_after": after_component_count,
        "merged_component_after": left_after if left_after == right_after else None,
        "mutation_effective": after_shape_count > before_shape_count,
    }
    return proof


def validate_pnand3_bundle(*, bundle_dir: Path, klayout_bin: Path, drc_deck: Path, lvs_deck: Path) -> dict[str, Any]:
    bundle_dir = bundle_dir.resolve()
    clean_gds = bundle_dir / "clean.gds"
    source_lock = _json(bundle_dir / "source_lock.json")
    parameter_mapping = _json(bundle_dir / "parameter_mapping.json")
    label_report = direct_top_labels_report(clean_gds, PNAND3_NAME, expected_top_pins=["VDD", "VSS", "A", "B", "C", "Z"], internal_nets=["net1", "net2"])
    source_reference_text = (bundle_dir / "source_reference.spice").read_text(encoding="utf-8")
    determinism = _json(bundle_dir / "determinism.json")
    tech = Tech.freepdk45(bundle_dir.parents[3])
    rejection_codes: list[str] = []
    contract_order = _json(bundle_dir / "top_pin_contract.json")["top_pin_order"] if (bundle_dir / "top_pin_contract.json").exists() else ["VDD", "VSS", "A", "B", "C", "Z"]
    if contract_order != ["VDD", "VSS", "A", "B", "C", "Z"]:
        rejection_codes.append("TOP_PIN_ORDER_MISMATCH")
    if source_lock.get("authority_commit") != EXPECTED_OPENYIELD_COMMIT:
        rejection_codes.append("SOURCE_COMMIT_MISMATCH")
    if source_lock.get("git_blob_sha") != EXPECTED_STANDARD_CELL_BLOB:
        rejection_codes.append("SOURCE_BLOB_MISMATCH")
    if not label_report["pin_name_set_exact"] or not label_report["pin_count_exact"] or not label_report["direct_top_labels_exact"] or not label_report["no_internal_net_promoted_to_top_port"]:
        rejection_codes.append("DIRECT_TOP_LABEL_CONTRACT_FAILED")
    elif not label_report["pin_order_exact"] and "TOP_PIN_ORDER_MISMATCH" not in rejection_codes:
        rejection_codes.append("TOP_PIN_ORDER_MISMATCH")
    if parameter_mapping.get("requested_nmos_width_nm") != 180:
        rejection_codes.append("NMOS_WIDTH_MISMATCH")
    if parameter_mapping.get("requested_pmos_width_nm") != 270:
        rejection_codes.append("PMOS_WIDTH_MISMATCH")
    if parameter_mapping.get("requested_length_nm") != 50:
        rejection_codes.append("LENGTH_MISMATCH")
    if "Mpnand3_pmos1 netp A VDD VDD" in source_reference_text or "Mpnand3_pmos2 Z B netp VDD" in source_reference_text:
        rejection_codes.append("PNAND3_PMOS_PARALLEL_TOPOLOGY_MISMATCH")
    if "Mpnand3_nmos1 Z A VSS VSS" in source_reference_text or "Mpnand3_nmos2 Z B VSS VSS" in source_reference_text:
        rejection_codes.append("PNAND3_NMOS_SERIES_CHAIN_MISMATCH")
    if "* Mpnand3_pmos1 removed" in source_reference_text:
        rejection_codes.append("MISSING_PMOS_DEVICE")
    if "* Mpnand3_nmos1 removed" in source_reference_text:
        rejection_codes.append("MISSING_NMOS_DEVICE")
    if "Mpnand3_pmos1 Z A VDD VSS" in source_reference_text:
        rejection_codes.append("PMOS_BULK_NOT_CONNECTED_TO_VDD")
    if "Mpnand3_nmos1 Z A net1 VDD" in source_reference_text:
        rejection_codes.append("NMOS_BULK_NOT_CONNECTED_TO_VSS")
    if not determinism.get("byte_identical", False):
        rejection_codes.append("DETERMINISM_FAILED")
    for poly in gdstk.read_gds(clean_gds).top_level()[0].flatten().polygons:
        for x, y in poly.points:
            if abs((round(float(x) / tech.manufacturing_grid) * tech.manufacturing_grid) - float(x)) > 1e-6 or abs((round(float(y) / tech.manufacturing_grid) * tech.manufacturing_grid) - float(y)) > 1e-6:
                rejection_codes.append("OFF_GRID_GEOMETRY")
                break
        if "OFF_GRID_GEOMETRY" in rejection_codes:
            break
    from scripts.TeamB_remaining9_reference_generation import _compare_pnand3_extracted, _verify_pnand3_physical_connectivity
    from sram_layoutgen.openyield_adapter.pnand2_verification_gate import run_recorded_lvs, run_recorded_drc
    drc = run_recorded_drc(klayout_bin=klayout_bin, drc_deck=drc_deck, input_gds=clean_gds, top_name=PNAND3_NAME, output_dir=bundle_dir / "drc")
    run_recorded_lvs(
        klayout_bin=klayout_bin,
        lvs_deck=lvs_deck,
        clean_gds=clean_gds,
        top_name=PNAND3_NAME,
        source_reference_spice=bundle_dir / "source_reference.spice",
        extracted_spice=bundle_dir / "extracted.spice",
        output_dir=bundle_dir / "lvs",
    )
    lvs = _compare_pnand3_extracted(bundle_dir / "source_reference.spice", bundle_dir / "extracted.spice", bundle_dir / "lvs/PNAND3_NW180_PW270_L50_FPDK45.lvsdb")
    device_inventory = _json(bundle_dir / "device_or_child_inventory.json")
    pin_map = _json(bundle_dir / "pin_map.json")
    conn = _verify_pnand3_physical_connectivity(clean_gds, sha256_file(clean_gds), pin_map, device_inventory["device_layout"])
    internal = conn["internal_net_components"]
    if not lvs["device_count_passed"] and "MISSING_PMOS_DEVICE" not in rejection_codes and "MISSING_NMOS_DEVICE" not in rejection_codes:
        devs = lvs.get("extracted_devices", [])
        pcount = sum(1 for row in devs if row["model_prefix"] == "PMOS")
        ncount = sum(1 for row in devs if row["model_prefix"] == "NMOS")
        if pcount < 3:
            rejection_codes.append("MISSING_PMOS_DEVICE")
        elif ncount < 3:
            rejection_codes.append("MISSING_NMOS_DEVICE")
        else:
            rejection_codes.append("STRICT_LVS_FAILED")
    if conn["vdd_vss_short"] and "VDD_VSS_SHORT" not in rejection_codes:
        rejection_codes.append("VDD_VSS_SHORT")
    if len(set(internal.values())) < 2:
        rejection_codes.append("UNEXPECTED_NET_MERGE_NET1_NET2")
    if conn["top_pin_to_component"]["Z"] in set(internal.values()):
        rejection_codes.append("UNEXPECTED_NET_MERGE_Z_NET1")
    if conn["top_pin_to_component"]["VSS"] in set(internal.values()):
        rejection_codes.append("UNEXPECTED_NET_MERGE_NET2_VSS")
    if drc["marker_count"] > 0 and "OFF_GRID_GEOMETRY" not in rejection_codes and "MISSING_PMOS_DEVICE" not in rejection_codes and "MISSING_NMOS_DEVICE" not in rejection_codes:
        rejection_codes.append("DRC_FAILED")
    if not lvs["gate_binding_passed"]:
        rejection_codes.append("PNAND3_GATE_BINDING_MISMATCH")
    if not lvs["source_drain_symmetric_graph_match_passed"] and "PNAND3_NMOS_SERIES_CHAIN_MISMATCH" not in rejection_codes and "PNAND3_PMOS_PARALLEL_TOPOLOGY_MISMATCH" not in rejection_codes:
        rejection_codes.append("STRICT_LVS_FAILED")
    return {"passed": len(rejection_codes) == 0, "rejection_codes": rejection_codes, "connectivity": json_safe(conn), "lvs": lvs, "drc": drc}


def run_pnand3_negative_regressions(*, baseline_clean_gds: Path, source_lock_path: Path, production_validator: dict[str, Any], output_dir: Path, resume: bool = False) -> dict[str, Any]:
    base_dir = baseline_clean_gds.parent
    work_root = output_dir.parents[2] / "negative_test_work" / "PNAND3"
    if work_root.exists() and not resume:
        shutil.rmtree(work_root)
    work_root.mkdir(parents=True, exist_ok=True)
    device_inventory = _json(base_dir / "device_or_child_inventory.json")
    pin_map = _json(base_dir / "pin_map.json")
    baseline_clean = Path("clean.gds")
    cases: list[tuple[MutationCase, Any, str]] = []
    cases.extend(
        [
            (MutationCase("01_wrong_authority_commit", "contract", "SOURCE_COMMIT_MISMATCH", Path("source_lock.json"), "validate_pnand3_bundle"), lambda d: (_replace_json_value(d / "source_lock.json", "authority_commit", "deadbeef"), d / "source_lock.json")[1], "contract"),
            (MutationCase("02_wrong_authority_blob", "contract", "SOURCE_BLOB_MISMATCH", Path("source_lock.json"), "validate_pnand3_bundle"), lambda d: (_replace_json_value(d / "source_lock.json", "git_blob_sha", "deadbeef"), d / "source_lock.json")[1], "contract"),
            (MutationCase("03_missing_top_pin_A", "label", "DIRECT_TOP_LABEL_CONTRACT_FAILED", baseline_clean, "validate_pnand3_bundle"), lambda d: (remove_label(d / "clean.gds", PNAND3_NAME, "A"), d / "clean.gds")[1], "label"),
            (MutationCase("04_extra_top_pin_net1", "label", "DIRECT_TOP_LABEL_CONTRACT_FAILED", baseline_clean, "validate_pnand3_bundle"), lambda d: (add_label(d / "clean.gds", PNAND3_NAME, "net1", (0.45, 0.25)), d / "clean.gds")[1], "label"),
            (MutationCase("05_wrong_top_pin_order", "contract", "TOP_PIN_ORDER_MISMATCH", Path("top_pin_contract.json"), "validate_pnand3_bundle"), lambda d: (_replace_json_value(d / "top_pin_contract.json", "top_pin_order", ["A", "B", "C", "Z", "VDD", "VSS"]), d / "top_pin_contract.json")[1], "contract"),
            (MutationCase("06_wrong_Wn", "contract", "NMOS_WIDTH_MISMATCH", Path("parameter_mapping.json"), "validate_pnand3_bundle"), lambda d: (_replace_json_value(d / "parameter_mapping.json", "requested_nmos_width_nm", 90), d / "parameter_mapping.json")[1], "contract"),
            (MutationCase("07_wrong_Wp", "contract", "PMOS_WIDTH_MISMATCH", Path("parameter_mapping.json"), "validate_pnand3_bundle"), lambda d: (_replace_json_value(d / "parameter_mapping.json", "requested_pmos_width_nm", 540), d / "parameter_mapping.json")[1], "contract"),
            (MutationCase("08_wrong_L", "contract", "LENGTH_MISMATCH", Path("parameter_mapping.json"), "validate_pnand3_bundle"), lambda d: (_replace_json_value(d / "parameter_mapping.json", "requested_length_nm", 60), d / "parameter_mapping.json")[1], "contract"),
            (MutationCase("09_missing_one_pmos", "contract", "MISSING_PMOS_DEVICE", Path("source_reference.spice"), "validate_pnand3_bundle"), lambda d: (_replace_reference_lines(d / "source_reference.spice", {"Mpnand3_pmos1": "* Mpnand3_pmos1 removed"}), d / "source_reference.spice")[1], "contract"),
            (MutationCase("10_missing_one_nmos", "contract", "MISSING_NMOS_DEVICE", Path("source_reference.spice"), "validate_pnand3_bundle"), lambda d: (_replace_reference_lines(d / "source_reference.spice", {"Mpnand3_nmos1": "* Mpnand3_nmos1 removed"}), d / "source_reference.spice")[1], "contract"),
            (MutationCase("11_pmos_series_contract", "contract", "PNAND3_PMOS_PARALLEL_TOPOLOGY_MISMATCH", Path("source_reference.spice"), "validate_pnand3_bundle"), lambda d: (_replace_reference_lines(d / "source_reference.spice", {"Mpnand3_pmos1": "Mpnand3_pmos1 netp A VDD VDD PMOS_VTG W=270n L=50n", "Mpnand3_pmos2": "Mpnand3_pmos2 Z B netp VDD PMOS_VTG W=270n L=50n"}), d / "source_reference.spice")[1], "contract"),
            (MutationCase("12_nmos_parallel_contract", "contract", "PNAND3_NMOS_SERIES_CHAIN_MISMATCH", Path("source_reference.spice"), "validate_pnand3_bundle"), lambda d: (_replace_reference_lines(d / "source_reference.spice", {"Mpnand3_nmos1": "Mpnand3_nmos1 Z A VSS VSS NMOS_VTG W=180n L=50n", "Mpnand3_nmos2": "Mpnand3_nmos2 Z B VSS VSS NMOS_VTG W=180n L=50n"}), d / "source_reference.spice")[1], "contract"),
            (MutationCase("13_gate_A_B_local_swap", "label", "PNAND3_GATE_BINDING_MISMATCH", baseline_clean, "validate_pnand3_bundle"), lambda d: (swap_labels(d / "clean.gds", PNAND3_NAME, "A", "B"), d / "clean.gds")[1], "label"),
            (MutationCase("14_gate_B_C_local_swap", "label", "PNAND3_GATE_BINDING_MISMATCH", baseline_clean, "validate_pnand3_bundle"), lambda d: (swap_labels(d / "clean.gds", PNAND3_NAME, "B", "C"), d / "clean.gds")[1], "label"),
            (MutationCase("19_pmos_body_wrong", "contract", "PMOS_BULK_NOT_CONNECTED_TO_VDD", Path("source_reference.spice"), "validate_pnand3_bundle"), lambda d: (_replace_reference_lines(d / "source_reference.spice", {"Mpnand3_pmos1": "Mpnand3_pmos1 Z A VDD VSS PMOS_VTG W=270n L=50n"}), d / "source_reference.spice")[1], "contract"),
            (MutationCase("20_nmos_body_wrong", "contract", "NMOS_BULK_NOT_CONNECTED_TO_VSS", Path("source_reference.spice"), "validate_pnand3_bundle"), lambda d: (_replace_reference_lines(d / "source_reference.spice", {"Mpnand3_nmos1": "Mpnand3_nmos1 Z A net1 VDD NMOS_VTG W=180n L=50n"}), d / "source_reference.spice")[1], "contract"),
            (MutationCase("21_debug_label_in_clean", "label", "DIRECT_TOP_LABEL_CONTRACT_FAILED", baseline_clean, "validate_pnand3_bundle"), lambda d: (add_label(d / "clean.gds", PNAND3_NAME, "DEBUG", (0.2, 1.0)), d / "clean.gds")[1], "label"),
            (MutationCase("22_off_grid_geometry", "geometry", "OFF_GRID_GEOMETRY", baseline_clean, "validate_pnand3_bundle"), lambda d: (add_off_grid_rect(d / "clean.gds", PNAND3_NAME, (0.1234, 0.4567, 0.1884, 0.5217)), d / "clean.gds")[1], "geometry"),
            (MutationCase("23_deterministic_A_B_mutation", "determinism", "DETERMINISM_FAILED", Path("determinism.json"), "validate_pnand3_bundle"), lambda d: (_replace_json_value(d / "determinism.json", "byte_identical", False), d / "determinism.json")[1], "determinism"),
        ]
    )
    def _short_mutation(net_a: str, net_b: str):
        def inner(d: Path) -> Path:
            graph = extract_physical_connectivity(d / "clean.gds", PNAND3_NAME)
            top_comp = {}
            for name in ["VDD", "VSS", "A", "B", "C", "Z"]:
                top_comp[name] = _component_from_bbox(graph, pin_map[name][0], {"m1", "m2", "poly"})
            if net_a in {"net1", "net2"}:
                left = _json(d / "physical_connectivity_report.json")["internal_net_components"][net_a]
            else:
                left = top_comp[net_a]
            if net_b in {"net1", "net2"}:
                right = _json(d / "physical_connectivity_report.json")["internal_net_components"][net_b]
            else:
                right = top_comp[net_b]
            baseline_sha = sha256_file(d / "clean.gds")
            proof = _bridge_components(d / "clean.gds", left, right)
            proof["baseline_sha256"] = baseline_sha
            proof["mutated_sha256"] = sha256_file(d / "clean.gds")
            after_graph = extract_physical_connectivity(d / "clean.gds", PNAND3_NAME)
            merged = None
            for comp in after_graph["components"]:
                members = set(comp["members"])
                if left in members or right in members:
                    merged = comp["component_id"]
                    break
            proof["merged_component_after"] = merged
            write_json(d / "mutation_proof.json", proof)
            return d / "clean.gds"
        return inner
    cases.extend(
        [
            (MutationCase("15_net1_net2_short", "short", "UNEXPECTED_NET_MERGE_NET1_NET2", baseline_clean, "validate_pnand3_bundle"), _short_mutation("net1", "net2"), "short"),
            (MutationCase("16_Z_net1_short", "short", "UNEXPECTED_NET_MERGE_Z_NET1", baseline_clean, "validate_pnand3_bundle"), _short_mutation("Z", "net1"), "short"),
            (MutationCase("17_net2_VSS_short", "short", "UNEXPECTED_NET_MERGE_NET2_VSS", baseline_clean, "validate_pnand3_bundle"), _short_mutation("net2", "VSS"), "short"),
            (MutationCase("18_VDD_VSS_short", "short", "VDD_VSS_SHORT", baseline_clean, "validate_pnand3_bundle"), _short_mutation("VDD", "VSS"), "short"),
        ]
    )
    rows = []
    for case, mutator, kind in cases:
        baseline_abs = base_dir / case.baseline_input_path
        baseline_sha = sha256_file(baseline_abs)
        if resume:
            cached = load_completed_checkpoint(work_root, case.test_id, baseline_sha)
            if cached is not None:
                rows.append(
                    {
                        "test_id": cached["test_id"],
                        "baseline_input_path": str(baseline_abs),
                        "baseline_input_sha256": cached["baseline_sha"],
                        "mutated_input_path": str(work_root / case.test_id / case.baseline_input_path),
                        "mutated_input_sha256": cached["mutated_sha"],
                        "mutation_effective": cached["mutation_effective"],
                        "production_validator_name": cached["validator_name"],
                        "production_validator_input_path": str(work_root / case.test_id / case.baseline_input_path),
                        "production_validator_input_sha256": cached["validator_input_sha"],
                        "validator_cache_disabled": True,
                        "expected_rejection_code": cached["expected_rejection_code"],
                        "actual_rejection_code": cached["actual_rejection_code"],
                        "rejected_as_expected": cached["rejected_as_expected"],
                        "all_actual_rejection_codes": cached["actual_rejection_code"],
                    }
                )
                continue
        validate = lambda work_dir: validate_pnand3_bundle(bundle_dir=work_dir, klayout_bin=Path(production_validator["klayout_bin"]), drc_deck=Path(production_validator["drc_deck"]), lvs_deck=Path(production_validator["lvs_deck"]))
        if kind == "contract":
            row = run_contract_mutation(base_dir=base_dir, work_root=work_root, case=case, mutate_fn=mutator, validate_fn=validate)
        elif kind == "label":
            row = run_gds_label_mutation(base_dir=base_dir, work_root=work_root, case=case, mutate_fn=mutator, validate_fn=validate)
        elif kind == "short":
            row = run_gds_short_mutation(base_dir=base_dir, work_root=work_root, case=case, mutate_fn=mutator, validate_fn=validate)
        elif kind == "determinism":
            row = run_determinism_mutation(base_dir=base_dir, work_root=work_root, case=case, mutate_fn=mutator, validate_fn=validate)
        else:
            row = run_gds_geometry_mutation(base_dir=base_dir, work_root=work_root, case=case, mutate_fn=mutator, validate_fn=validate)
        rows.append(row)
        write_case_checkpoint(
            work_root=work_root,
            test_id=case.test_id,
            baseline_sha=row["baseline_input_sha256"],
            mutated_sha=row["mutated_input_sha256"],
            mutation_effective=row["mutation_effective"],
            validator_name=row["production_validator_name"],
            validator_input_sha=row["production_validator_input_sha256"],
            expected_rejection_code=row["expected_rejection_code"],
            actual_rejection_code=row["actual_rejection_code"],
            rejected_as_expected=row["rejected_as_expected"],
        )
    write_negative_test_matrix(output_dir / "PNAND3_negative_test_matrix.csv", rows)
    summary = write_negative_test_summary(output_dir / "PNAND3_negative_test_summary.json", rows)
    write_text(output_dir / "PNAND3_negative_test_execution.log", "\n".join(f"{row['test_id']} {row['actual_rejection_code']}" for row in rows))
    return {"rows": rows, "summary": summary}
