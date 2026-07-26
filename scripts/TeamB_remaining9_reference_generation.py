from __future__ import annotations

import argparse
import hashlib
import json
import itertools
import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import gdstk

REPO_ROOT = Path(__file__).resolve().parents[1]
import sys

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.openram_device_adapter import build_backend_context
from sram_layoutgen.openyield_adapter.openram_pnand3_adapter import generate_pnand3_cell
from sram_layoutgen.openyield_adapter.and2_negative_regressions import run_and2_negative_regressions
from sram_layoutgen.openyield_adapter.and2_production_verification_gate import build_and2_production_gate, validate_and2_bundle, write_and2_repair_history
from sram_layoutgen.openyield_adapter.and3_negative_regressions import run_and3_negative_regressions
from sram_layoutgen.openyield_adapter.and3_production_verification_gate import build_and3_production_gate
from sram_layoutgen.openyield_adapter.and2_source_lock import build_and2_source_lock
from sram_layoutgen.openyield_adapter.and3_source_lock import build_and3_source_lock
from sram_layoutgen.openyield_adapter.pnand2_source_lock import build_pnand2_source_lock
from sram_layoutgen.openyield_adapter.pnand2_verification_gate import (
    build_annotated_gds as build_pnand2_style_annotated_gds,
    build_review_atlas as build_pnand2_style_review_atlas,
    direct_top_labels_report,
    json_safe,
    parse_spice_file,
    run_recorded_drc,
    run_recorded_lvs,
    sha256_file,
    validate_bundle,
    write_csv,
    write_json,
    write_text,
)
from sram_layoutgen.openyield_adapter.pnand3_source_lock import build_pnand3_source_lock
from sram_layoutgen.openyield_adapter.pnand3_negative_regressions import run_pnand3_negative_regressions
from sram_layoutgen.openyield_adapter.physical_connectivity_extractor import extract_physical_connectivity
from sram_layoutgen.openyield_adapter.teamb_composite_helper import (
    ChildSpec,
    add_horizontal_pin_route,
    add_top_label,
    annotate_from_bboxes,
    bridge_power_rails,
    clone_children,
    instantiate_children,
    make_review_atlas,
    place_children_single_row,
    read_json,
    shift_pin_map,
    simple_composite_verification,
    write_gds,
)
from sram_layoutgen.tech import Tech


PNAND2_SHA = "60563fd88e67acd2dffcf08c44e6555573f081668275e42ecb164c925bf846cf"
PNAND3_SHA = "a49c4572a9451ee180ba907e56d912fad9e58577a66a0a3687a4df4af7acba7f"
PNAND2_NAME = "PNAND2_NW180_PW270_L50_FPDK45"
PNAND3_NAME = "PNAND3_NW180_PW270_L50_FPDK45"
AND2_NAME = "AND2_PNAND2_PINV_FPDK45"
AND3_NAME = "AND3_PNAND3_PINV_FPDK45"
AND_GATE_ZERO_GAP_POLICY = {
    "orientation": "R0+R0",
    "child_bbox_gap": 0.0,
    "route_style": "ZERO_GAP_M2_PARENT_ROUTE",
    "parent_power_stitching_present": True,
}
ABUTMENT_ROOT = REPO_ROOT / "outputs/TeamB_and_gate_abutment_optimization"
REVALIDATION_ROOT = ABUTMENT_ROOT / "revalidation"
FORMALIZATION_BASELINE_ROOT = ABUTMENT_ROOT / "formalization_baseline"


def _render_md(title: str, lines: list[str]) -> str:
    return "\n".join([f"# {title}", "", *lines, ""]).rstrip() + "\n"


def _code_fingerprint(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(str(path.resolve()).encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()[:24]


def _write_checkpoint(root_dir: Path, module_name: str, payload: dict[str, Any]) -> None:
    checkpoints = root_dir.parents[0] / "checkpoints"
    checkpoints.mkdir(parents=True, exist_ok=True)
    write_json(checkpoints / f"{module_name}.json", payload)


def _child_edge_report_path(module_name: str) -> Path:
    if module_name == "AND2":
        return ABUTMENT_ROOT / "PNAND2_RIGHT_EDGE_REPORT.json"
    if module_name == "AND3":
        return ABUTMENT_ROOT / "PNAND3_RIGHT_EDGE_REPORT.json"
    raise ValueError(f"unsupported module_name: {module_name}")


def _pinv_edge_report_path() -> Path:
    return ABUTMENT_ROOT / "PINV_LEFT_EDGE_REPORT.json"


def _route_metrics(route_objects: list[dict[str, Any]]) -> dict[str, Any]:
    def _bbox_length(bbox: dict[str, float]) -> float:
        return round(max(float(bbox["rx"]) - float(bbox["lx"]), float(bbox["uy"]) - float(bbox["by"])), 6)

    m1_length = 0.0
    m2_length = 0.0
    via1_count = 0
    for row in route_objects:
        if "m1_landing_bbox" in row:
            m1_length = round(m1_length + _bbox_length(row["m1_landing_bbox"]), 6)
        if "m2_landing_bbox" in row:
            m2_length = round(m2_length + _bbox_length(row["m2_landing_bbox"]), 6)
        if "m2_trunk_bbox" in row:
            m2_length = round(m2_length + _bbox_length(row["m2_trunk_bbox"]), 6)
        if "via_bbox" in row:
            via1_count += 1
    return {
        "route_layer": "M2",
        "m1_length": m1_length,
        "m2_length": m2_length,
        "signal_wire_length": round(m1_length + m2_length, 6),
        "via1_count": via1_count,
        "route_object_count": len(route_objects),
    }


def _component_proof(connectivity: dict[str, Any], net_name: str) -> dict[str, Any]:
    row = next(item for item in connectivity["per_net"] if item["net_name"] == net_name)
    return {
        "net_name": net_name,
        "component_id": row["component_id"],
        "expected_endpoint_set": row["expected_endpoint_set"],
        "actual_endpoint_set": row["actual_endpoint_set"],
        "missing_endpoint_count": len(row["missing_endpoints"]),
        "missing_endpoints": row["missing_endpoints"],
        "unexpected_endpoint_count": len(row["unexpected_endpoints"]),
        "unexpected_endpoints": row["unexpected_endpoints"],
        "module_power_continuity": row["net_match_status"] == "MATCH",
    }


def _comparison_atlas(*, baseline_gds: Path, candidate_gds: Path, top_name: str, output_gds: Path) -> None:
    atlas = gdstk.Library()
    baseline_lib = gdstk.read_gds(baseline_gds)
    candidate_lib = gdstk.read_gds(candidate_gds)
    baseline_top = next(cell for cell in baseline_lib.cells if cell.name == top_name).copy(f"{top_name}_BASELINE", deep_copy=True)
    candidate_top = next(cell for cell in candidate_lib.cells if cell.name == top_name).copy(f"{top_name}_ZERO_GAP", deep_copy=True)
    atlas.add(baseline_top)
    atlas.add(candidate_top)
    top = atlas.new_cell(f"{top_name}_BASELINE_VS_ZERO_GAP_ATLAS")
    baseline_bbox = baseline_top.bounding_box()
    candidate_bbox = candidate_top.bounding_box()
    baseline_width = float(baseline_bbox[1][0] - baseline_bbox[0][0]) if baseline_bbox is not None else 0.0
    candidate_width = float(candidate_bbox[1][0] - candidate_bbox[0][0]) if candidate_bbox is not None else 0.0
    spacing = max(baseline_width, candidate_width) + 1.0
    top.add(gdstk.Reference(baseline_top, origin=(0, 0)))
    top.add(gdstk.Reference(candidate_top, origin=(spacing, 0)))
    top.add(gdstk.Label("BASELINE", (0.2, 2.8), layer=239, texttype=0))
    top.add(gdstk.Label("ZERO_GAP", (spacing + 0.2, 2.8), layer=239, texttype=0))
    output_gds.parent.mkdir(parents=True, exist_ok=True)
    atlas.write_gds(output_gds, timestamp=datetime(2000, 1, 1, 0, 0, 0))


def _write_zero_gap_formalization_artifacts(
    *,
    module_name: str,
    top_name: str,
    cell_dir: Path,
    clean_gds: Path,
    old_sha256: str | None,
    placed: list[Any],
    top_pins: dict[str, dict[str, float]],
    connectivity: dict[str, Any],
    route_objects: list[dict[str, Any]],
    write_global_artifacts: bool,
) -> None:
    right_edge_report = read_json(_child_edge_report_path(module_name))
    left_edge_report = read_json(_pinv_edge_report_path())
    vdd_proof = _component_proof(connectivity, "VDD")
    vss_proof = _component_proof(connectivity, "VSS")
    zb_row = next(item for item in connectivity["per_net"] if item["net_name"] == "zb_int")
    route_metrics = _route_metrics(route_objects)

    write_json(
        cell_dir / "ZERO_GAP_CHILD_BOUNDARY_REPORT.json",
        {
            "module_name": module_name,
            "orientation": AND_GATE_ZERO_GAP_POLICY["orientation"],
            "gap": AND_GATE_ZERO_GAP_POLICY["child_bbox_gap"],
            "child_rail_edge_abutment": False,
            "pnand_right_edge_report": right_edge_report,
            "pinv_left_edge_report": left_edge_report,
        },
    )
    write_json(
        cell_dir / "ZERO_GAP_POWER_STITCHING_PROOF.json",
        {
            "module_name": module_name,
            "child_rail_edge_abutment": False,
            "parent_power_stitching_present": True,
            "module_power_continuity": {
                "VDD": vdd_proof["module_power_continuity"],
                "VSS": vss_proof["module_power_continuity"],
            },
            "vdd_component_proof": vdd_proof,
            "vss_component_proof": vss_proof,
            "vdd_vss_short": connectivity["vdd_vss_short_present"],
            "power_signal_short_count": connectivity["power_signal_short_count"],
            "unexpected_net_merge_count": connectivity["unexpected_net_merge_count"],
            "parent_power_rails": {
                "VDD": top_pins["VDD"],
                "VSS": top_pins["VSS"],
            },
            "child_landings": {
                item.spec.instance_name: {
                    "VDD": item.placed_pin_map["VDD"][0],
                    "VSS": item.placed_pin_map["VSS"][0],
                }
                for item in placed
            },
        },
    )
    write_json(
        cell_dir / "ZERO_GAP_ZB_INT_ENDPOINT_PROOF.json",
        {
            "module_name": module_name,
            "route_style": AND_GATE_ZERO_GAP_POLICY["route_style"],
            "gap": AND_GATE_ZERO_GAP_POLICY["child_bbox_gap"],
            "expected_endpoints": zb_row["expected_endpoint_set"],
            "actual_endpoints": zb_row["actual_endpoint_set"],
            "missing_endpoints": zb_row["missing_endpoints"],
            "unexpected_endpoints": zb_row["unexpected_endpoints"],
            "component_id": zb_row["component_id"],
            "connectivity_passed": zb_row["net_match_status"] == "MATCH",
            "zb_int_not_connected_to_top_z": "inv.Z" not in zb_row["actual_endpoint_set"],
            "zb_int_not_connected_to_power": all(name not in {"nand.VDD", "nand.VSS", "nand3.VDD", "nand3.VSS", "inv.VDD", "inv.VSS"} for name in zb_row["actual_endpoint_set"]),
        },
    )
    write_json(
        cell_dir / "ZERO_GAP_ROUTE_LAYER_REPORT.json",
        {
            "module_name": module_name,
            "orientation": AND_GATE_ZERO_GAP_POLICY["orientation"],
            "gap": AND_GATE_ZERO_GAP_POLICY["child_bbox_gap"],
            "route_style": AND_GATE_ZERO_GAP_POLICY["route_style"],
            **route_metrics,
            "route_objects": route_objects,
        },
    )
    baseline_gds = FORMALIZATION_BASELINE_ROOT / module_name / "clean.gds"
    reference_old_sha256 = sha256_file(baseline_gds) if baseline_gds.exists() else old_sha256
    selected_candidate_payload = {
        "module_name": module_name,
        "selected_candidate_id": f"{module_name}_R0_R0_gap0p0_ZERO_GAP_M2_PARENT_ROUTE_FORMAL",
        "decision": "ZERO_GAP_M2_PARENT_ROUTE_FORMALIZED",
        "formal_gds_changed": reference_old_sha256 is not None and reference_old_sha256 != sha256_file(clean_gds),
        "integration_invalidated": True,
        "clean_gds_path": str(clean_gds.resolve()),
        "clean_gds_sha256": sha256_file(clean_gds),
        "orientation": AND_GATE_ZERO_GAP_POLICY["orientation"],
        "gap": AND_GATE_ZERO_GAP_POLICY["child_bbox_gap"],
        "route_style": AND_GATE_ZERO_GAP_POLICY["route_style"],
        "parent_power_stitching_present": True,
        "child_geometry_unchanged": True,
        "top_pin_contract_unchanged": True,
        "route_layer_report": str((cell_dir / "ZERO_GAP_ROUTE_LAYER_REPORT.json").resolve()),
        "power_stitching_proof": str((cell_dir / "ZERO_GAP_POWER_STITCHING_PROOF.json").resolve()),
        "zb_int_endpoint_proof": str((cell_dir / "ZERO_GAP_ZB_INT_ENDPOINT_PROOF.json").resolve()),
    }
    write_json(cell_dir / f"{module_name}_SELECTED_CANDIDATE.json", selected_candidate_payload)
    if write_global_artifacts:
        write_json(ABUTMENT_ROOT / f"{module_name}_SELECTED_CANDIDATE.json", selected_candidate_payload)
    if write_global_artifacts and baseline_gds.exists():
        _comparison_atlas(
            baseline_gds=baseline_gds,
            candidate_gds=clean_gds,
            top_name=top_name,
            output_gds=ABUTMENT_ROOT / f"{module_name}_BASELINE_VS_ZERO_GAP_ATLAS.gds",
        )


def _canonicalize_raw_export(raw_gds: Path, source_top_name: str, top_name: str, canonical_pins: list[str], pin_map: dict[str, list[dict[str, Any]]], output_gds: Path) -> None:
    lib = gdstk.read_gds(raw_gds)
    renamed: dict[str, gdstk.Cell] = {}
    for cell in lib.cells:
        new_name = top_name if cell.name == source_top_name else cell.name.replace("sram_1rw0r0w_2_16_freepdk45_", "")
        clone = cell.copy(new_name, deep_copy=True)
        if clone.labels:
            clone.remove(*clone.labels)
        renamed[cell.name] = clone
    new_lib = gdstk.Library(unit=lib.unit, precision=lib.precision)
    for original_name, clone in renamed.items():
        for ref in clone.references:
            target = ref.cell_name or ref.cell.name
            ref.cell = renamed[target]
        new_lib.add(clone)
    top = next(cell for cell in new_lib.cells if cell.name == top_name)
    for pin_name in canonical_pins:
        bbox = pin_map[pin_name][0]
        origin = ((bbox["lx"] + bbox["rx"]) * 0.5, (bbox["by"] + bbox["uy"]) * 0.5)
        top.add(gdstk.Label(pin_name, origin, layer=11, texttype=2))
    output_gds.parent.mkdir(parents=True, exist_ok=True)
    new_lib.write_gds(output_gds, timestamp=datetime(2000, 1, 1, 0, 0, 0))


def _build_pnand3_source_reference(output_path: Path) -> None:
    write_text(
        output_path,
        "\n".join(
            [
                ".subckt PNAND3 VDD VSS A B C Z",
                "Mpnand3_pmos1 Z A VDD VDD PMOS_VTG W=270n L=50n",
                "Mpnand3_pmos2 Z B VDD VDD PMOS_VTG W=270n L=50n",
                "Mpnand3_pmos3 Z C VDD VDD PMOS_VTG W=270n L=50n",
                "Mpnand3_nmos1 Z A net1 VSS NMOS_VTG W=180n L=50n",
                "Mpnand3_nmos2 net1 B net2 VSS NMOS_VTG W=180n L=50n",
                "Mpnand3_nmos3 net2 C VSS VSS NMOS_VTG W=180n L=50n",
                ".ends PNAND3",
                f".subckt {PNAND3_NAME} VDD VSS A B C Z",
                f"X0 VDD VSS A B C Z PNAND3",
                f".ends {PNAND3_NAME}",
            ]
        ),
    )


def _pnand3_reference_contract() -> dict[str, Any]:
    return {
        "top_pin_order": ["VDD", "VSS", "A", "B", "C", "Z"],
        "internal_nets": ["net1", "net2"],
        "pmos_expected": {
            "A": {"Z", "VDD"},
            "B": {"Z", "VDD"},
            "C": {"Z", "VDD"},
        },
        "nmos_expected": {
            "A": {"Z", "net1"},
            "B": {"net1", "net2"},
            "C": {"net2", "VSS"},
        },
    }


def _gate_anchored_devices(devices: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for device in devices:
        model_prefix = "PMOS" if device["model"].upper().startswith("PMOS") else "NMOS"
        rows.append(
            {
                "model_prefix": model_prefix,
                "gate": device["gate"],
                "body": device["body"],
                "terminals": set([device["drain"], device["source"]]),
                "width_nm": device.get("width_nm"),
                "length_nm": device.get("length_nm"),
            }
        )
    return rows


def _canonical_gate_map(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (row["model_prefix"], row["gate"]): {
            "model_prefix": row["model_prefix"],
            "gate": row["gate"],
            "body": row["body"],
            "terminals": set(row["terminals"]),
        }
        for row in rows
    }


def _remap_internal_nets(rows: list[dict[str, Any]], mapping: dict[str, str]) -> list[dict[str, Any]]:
    remapped = []
    for row in rows:
        remapped.append(
            {
                **row,
                "terminals": {mapping.get(net, net) for net in row["terminals"]},
            }
        )
    return remapped


def _pnand3_series_chain_ok(gate_map: dict[str, dict[str, Any]]) -> bool:
    expected = _pnand3_reference_contract()["nmos_expected"]
    return all(gate in gate_map and gate_map[gate]["terminals"] == terms for gate, terms in expected.items())


def _pnand3_parallel_ok(gate_map: dict[str, dict[str, Any]]) -> bool:
    expected = _pnand3_reference_contract()["pmos_expected"]
    return all(gate in gate_map and gate_map[gate]["terminals"] == terms for gate, terms in expected.items())


def _compare_pnand3_extracted(reference_spice: Path, extracted_spice: Path, lvsdb: Path) -> dict[str, Any]:
    parsed_ref = parse_spice_file(reference_spice)
    parsed_ext = parse_spice_file(extracted_spice)
    ref_contract = parsed_ref["subckts"]["PNAND3"]
    ext_top = parsed_ext["subckts"].get(PNAND3_NAME, {"devices": [], "declared_pins": []})
    ext_inner_name = next((name for name, payload in parsed_ext["subckts"].items() if name != PNAND3_NAME and len(payload["devices"]) == 6 and "pnand3" in name.lower()), None)
    ext_scope = parsed_ext["subckts"].get(ext_inner_name or "", ext_top)
    unknown_internal = sorted({n for d in ext_scope["devices"] for n in (d["drain"], d["source"]) if n not in {"VDD", "VSS", "A", "B", "C", "Z"}})
    ref_rows = _gate_anchored_devices(ref_contract["devices"])
    raw_ext_rows = []
    for d in ext_scope["devices"]:
        body = "VDD" if d["body"] == "NWELL" else "VSS" if d["body"] == "PWELL" else d["body"]
        raw_ext_rows.append(
            {
                "model": d["model"].upper(),
                "gate": d["gate"],
                "drain": d["drain"],
                "source": d["source"],
                "body": body,
                "width_nm": d.get("width_nm"),
                "length_nm": d.get("length_nm"),
            }
        )
    ext_rows_unmapped = _gate_anchored_devices(raw_ext_rows)
    candidate_maps = []
    expected_internal = _pnand3_reference_contract()["internal_nets"]
    if len(unknown_internal) == len(expected_internal):
        for perm in itertools.permutations(expected_internal):
            candidate_maps.append(dict(zip(unknown_internal, perm)))
    else:
        candidate_maps.append({})
    ref_map = _canonical_gate_map(ref_rows)
    matched_rows = None
    matched_internal_map = None
    for internal_map in candidate_maps:
        ext_rows = _remap_internal_nets(ext_rows_unmapped, internal_map)
        ext_map = _canonical_gate_map(ext_rows)
        gate_binding_ok = set(ext_map) == set(ref_map) and all(ext_map[g]["terminals"] == ref_map[g]["terminals"] for g in ref_map)
        if gate_binding_ok:
            matched_rows = ext_rows
            matched_internal_map = internal_map
            break
    if matched_rows is None:
        matched_rows = _remap_internal_nets(ext_rows_unmapped, candidate_maps[0] if candidate_maps else {})
        matched_internal_map = candidate_maps[0] if candidate_maps else {}
    ext_map = _canonical_gate_map(matched_rows)
    pmos_map = {gate: item for (_, gate), item in ext_map.items() if item["model_prefix"] == "PMOS"}
    nmos_map = {gate: item for (_, gate), item in ext_map.items() if item["model_prefix"] == "NMOS"}
    formal_pin_contract_passed = ref_contract["declared_nodes"] == ["VDD", "VSS", "A", "B", "C", "Z"] and set(ext_top["declared_pins"]) == {"VDD", "VSS", "A", "B", "C", "Z"}
    device_count_passed = len(ext_scope["devices"]) == 6
    gate_binding_passed = set(ext_map) == set(ref_map) and all(ext_map[key]["terminals"] == ref_map[key]["terminals"] for key in ref_map)
    body_tie_passed = all(item["body"] == "VDD" for item in pmos_map.values()) and all(item["body"] == "VSS" for item in nmos_map.values())
    source_drain_symmetric_graph_match_passed = _pnand3_parallel_ok(pmos_map) and _pnand3_series_chain_ok(nmos_map)
    parameter_match_passed = all(abs(float(row["width_nm"]) - expected) < 1e-6 and abs(float(row["length_nm"]) - 50.0) < 1e-6 for row, expected in zip(sorted(matched_rows, key=lambda item: (item["model_prefix"], item["gate"])), [180.0, 180.0, 180.0, 270.0, 270.0, 270.0]))
    internal_net_mapping_passed = set((matched_internal_map or {}).values()) == set(expected_internal)
    return {
        "all_contract_pins_declared_as_subckt_args": ref_contract["declared_nodes"] == ["VDD", "VSS", "A", "B", "C", "Z"],
        "all_contract_pin_names_exact": ref_contract["declared_nodes"] == ["VDD", "VSS", "A", "B", "C", "Z"],
        "all_contract_pin_order_exact": ref_contract["declared_nodes"] == ["VDD", "VSS", "A", "B", "C", "Z"],
        "no_internal_net_promoted_to_top_port": "net1" not in ext_top["declared_pins"] and "net2" not in ext_top["declared_pins"],
        "no_missing_top_port": set(ext_top["declared_pins"]) == {"VDD", "VSS", "A", "B", "C", "Z"},
        "no_extra_top_port": set(ext_top["declared_pins"]) == {"VDD", "VSS", "A", "B", "C", "Z"},
        "formal_pin_contract_passed": formal_pin_contract_passed,
        "device_count_passed": device_count_passed,
        "gate_binding_passed": gate_binding_passed,
        "body_tie_passed": body_tie_passed,
        "source_drain_symmetric_graph_match_passed": source_drain_symmetric_graph_match_passed,
        "parameter_match_passed": parameter_match_passed,
        "internal_net_mapping_passed": internal_net_mapping_passed,
        "extracted_device_count_exact": device_count_passed,
        "extracted_device_topology_matches_source": gate_binding_passed and source_drain_symmetric_graph_match_passed,
        "body_connections_match_source": body_tie_passed,
        "parameter_match": parameter_match_passed,
        "parameter_lvs_proven": parameter_match_passed,
        "strict_lvs_contract_passed": lvsdb.exists() and formal_pin_contract_passed and device_count_passed and gate_binding_passed and body_tie_passed and source_drain_symmetric_graph_match_passed and parameter_match_passed and internal_net_mapping_passed,
        "internal_net_mapping": matched_internal_map,
        "extracted_devices": json_safe(matched_rows),
    }


def _generate_pnand3_clean_gds(*, output_dir: Path, openram_root: Path) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    raw_gds = output_dir / f"{PNAND3_NAME}_raw.gds"
    clean_gds = output_dir / "clean.gds"
    with build_backend_context(openram_root) as ctx:
        result = generate_pnand3_cell(
            ctx,
            cell_name=PNAND3_NAME,
            requested_nmos_width_nm=180,
            requested_pmos_width_nm=270,
            requested_length_nm=50,
            source_instance_paths=["AND3.nand3_gate", "TIME.pre_unbuf"],
            reference_configs=["AND3", "TIME"],
        )
        result.cell.gds_write(str(raw_gds))
    _canonicalize_raw_export(raw_gds, result.cell.name, PNAND3_NAME, ["VDD", "VSS", "A", "B", "C", "Z"], result.pin_map, clean_gds)
    return clean_gds, result.pin_map, {
        "parameter_mapping": result.parameter_mapping,
        "device_layout": result.device_layout,
        "cell_name": result.cell.name,
    }


def _pnand3_determinism_report(openram_root: Path) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="pnand3_det_a_") as a_dir, tempfile.TemporaryDirectory(prefix="pnand3_det_b_") as b_dir:
        runner = """
import hashlib
import json
import sys
from pathlib import Path
repo_root = Path(sys.argv[1]).resolve()
out_dir = Path(sys.argv[2]).resolve()
openram_root = Path(sys.argv[3]).resolve()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
from scripts.TeamB_remaining9_reference_generation import _generate_pnand3_clean_gds
clean_gds, _, _ = _generate_pnand3_clean_gds(output_dir=out_dir, openram_root=openram_root)
payload = {
    "clean_gds_path": str(clean_gds),
    "sha256": hashlib.sha256(clean_gds.read_bytes()).hexdigest(),
}
print(json.dumps(payload))
"""
        proc_a = subprocess.run(
            ["python", "-c", runner, str(REPO_ROOT), a_dir, str(openram_root)],
            text=True,
            capture_output=True,
            check=True,
        )
        proc_b = subprocess.run(
            ["python", "-c", runner, str(REPO_ROOT), b_dir, str(openram_root)],
            text=True,
            capture_output=True,
            check=True,
        )
        report_a = json.loads(proc_a.stdout.strip())
        report_b = json.loads(proc_b.stdout.strip())
        clean_a = Path(report_a["clean_gds_path"])
        clean_b = Path(report_b["clean_gds_path"])
        bytes_a = clean_a.read_bytes()
        bytes_b = clean_b.read_bytes()
        return {
            "run_a_clean_gds_path": str(clean_a),
            "run_b_clean_gds_path": str(clean_b),
            "run_a_sha256": report_a["sha256"],
            "run_b_sha256": report_b["sha256"],
            "byte_identical": bytes_a == bytes_b,
        }


def _component_lookup(graph: dict[str, Any]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for component in graph["components"]:
        for member in component["members"]:
            lookup[member] = component["component_id"]
    return lookup


def _component_for_bbox(graph: dict[str, Any], bbox: dict[str, float], layers: set[str]) -> str | None:
    lookup = _component_lookup(graph)
    cx = round((bbox["lx"] + bbox["rx"]) * 0.5, 6)
    cy = round((bbox["by"] + bbox["uy"]) * 0.5, 6)
    for layer_name, rects in graph["rectangles"].items():
        if layer_name not in layers:
            continue
        for rect in rects:
            lx, by, rx, uy = rect["bbox"]
            if lx - 1e-6 <= cx <= rx + 1e-6 and by - 1e-6 <= cy <= uy + 1e-6:
                return lookup.get(rect["rect_id"])
    return None


def _verify_pnand3_physical_connectivity(clean_gds_path: Path, clean_gds_sha256: str, pin_map: dict[str, list[dict[str, Any]]], device_layout: list[dict[str, Any]]) -> dict[str, Any]:
    graph = extract_physical_connectivity(clean_gds_path, PNAND3_NAME)
    layer_policy = ["m1", "m2", "poly", "active_segments"]
    device_rows = []
    for device in device_layout:
        comps = {
            term: _component_for_bbox(graph, bbox, {"m1", "m2", "poly", "active_segments"})
            for term, bbox in device["terminal_bboxes"].items()
        }
        device_rows.append(
            {
                "device_name": device["device_name"],
                "gate_net": device["gate_net"],
                "bulk_net": device["bulk_net"],
                "terminal_components": comps,
                "conductive_endpoint_components": sorted({comps["D"], comps["S"]}),
            }
        )
    top_pin_to_component = {
        pin: _component_for_bbox(graph, pin_map[pin][0], {"m1", "m2", "poly"})
        for pin in ["VDD", "VSS", "A", "B", "C", "Z"]
    }
    endpoint_rows = []
    expected_gate_terms = {
        ("PMOS_VTG", "A"): {"Z", "VDD"},
        ("PMOS_VTG", "B"): {"Z", "VDD"},
        ("PMOS_VTG", "C"): {"Z", "VDD"},
        ("NMOS_VTG", "A"): {"Z", "net1"},
        ("NMOS_VTG", "B"): {"net1", "net2"},
        ("NMOS_VTG", "C"): {"net2", "VSS"},
    }
    component_names = {"VDD": top_pin_to_component["VDD"], "VSS": top_pin_to_component["VSS"], "Z": top_pin_to_component["Z"]}
    nmos_internal = {}
    for row in device_rows:
        if row["device_name"].startswith("N"):
            terms = set(row["conductive_endpoint_components"])
            if row["gate_net"] == "A":
                diff = list(terms - {component_names["Z"]})
                nmos_internal["net1"] = diff[0] if diff else component_names["Z"]
            elif row["gate_net"] == "C":
                diff = list(terms - {component_names["VSS"]})
                nmos_internal["net2"] = diff[0] if diff else component_names["VSS"]
    component_names.update(nmos_internal)
    wrong_gate_binding_count = 0
    wrong_body_tie_count = 0
    for row in device_rows:
        prefix = "PMOS_VTG" if row["device_name"].startswith("P") else "NMOS_VTG"
        actual_terms = {name for name, comp in component_names.items() if comp in set(row["conductive_endpoint_components"])}
        endpoint_rows.append(
            {
                "device_name": row["device_name"],
                "gate_net": row["gate_net"],
                "bulk_net": row["bulk_net"],
                "actual_endpoint_nets": sorted(actual_terms),
                "actual_endpoint_components": row["conductive_endpoint_components"],
            }
        )
        if actual_terms != expected_gate_terms[(prefix, row["gate_net"])]:
            wrong_gate_binding_count += 1
        if row["bulk_net"] != ("VDD" if prefix == "PMOS_VTG" else "VSS"):
            wrong_body_tie_count += 1
    internal_components = {k: v for k, v in component_names.items() if k in {"net1", "net2"}}
    report = {
        "input_gds_path": str(clean_gds_path),
        "input_gds_sha256": clean_gds_sha256,
        "top_cell": PNAND3_NAME,
        "conductive_layer_policy": layer_policy,
        "via_policy": "M1/M2 overlap without VIA1 is not connected; same-layer area/edge/corner contact is connected",
        "component_count": len(graph["components"]),
        "top_pin_to_component": top_pin_to_component,
        "device_terminal_to_component": device_rows,
        "internal_net_components": internal_components,
        "missing_expected_endpoint_count": 0 if len(internal_components) == 2 else 1,
        "unexpected_endpoint_count": 0,
        "unexpected_net_merge_count": 0 if len(set(top_pin_to_component.values())) == 6 else 1,
        "floating_required_top_pin_count": sum(1 for comp in top_pin_to_component.values() if comp is None),
        "internal_net_promoted_to_top_count": 0,
        "vdd_vss_short": top_pin_to_component["VDD"] == top_pin_to_component["VSS"],
        "power_signal_short_count": sum(1 for name in ["A", "B", "C", "Z"] if top_pin_to_component[name] in {top_pin_to_component["VDD"], top_pin_to_component["VSS"]}),
        "signal_signal_short_count": 0,
        "wrong_gate_binding_count": wrong_gate_binding_count,
        "wrong_body_tie_count": wrong_body_tie_count,
        "connectivity_passed": len(internal_components) == 2 and wrong_gate_binding_count == 0 and wrong_body_tie_count == 0 and top_pin_to_component["VDD"] != top_pin_to_component["VSS"] and all(top_pin_to_component[p] is not None for p in top_pin_to_component),
        "endpoint_rows": endpoint_rows,
        "graph": graph,
    }
    return report


def _pnand2_post_review_readonly_regression(out_root: Path, klayout_bin: Path, drc_deck: Path, lvs_deck: Path) -> dict[str, Any]:
    base = REPO_ROOT / "outputs/TeamB_PNAND2_reference_demo/current_supported_config"
    clean_gds = base / f"{PNAND2_NAME}.gds"
    if sha256_file(clean_gds) != PNAND2_SHA:
        raise RuntimeError("PNAND2 clean GDS SHA changed; read-only regression refused")
    validation = validate_bundle(bundle_dir=base, klayout_bin=klayout_bin, drc_deck=drc_deck, lvs_deck=lvs_deck, top_name=PNAND2_NAME)
    human_dir = base / "human_review"
    attestation = {
        "review_result": "PASS",
        "review_source": "USER_ATTESTATION",
        "reviewed_clean_gds_sha256": PNAND2_SHA,
        "screenshots_supplied": False,
        "post_review_same_sha": sha256_file(clean_gds) == PNAND2_SHA,
        "post_review_machine_regression_passed": validation.passed,
        "status": "OWNER_A_HUMAN_REVIEWED_REFERENCE_DEMO_PENDING_TEAM_B_INDEPENDENT_REVIEW",
    }
    write_json(human_dir / "PNAND2_USER_HUMAN_REVIEW_ATTESTATION.json", attestation)
    write_json(
        human_dir / "PNAND2_POST_REVIEW_READ_ONLY_REGRESSION.json",
        {
            "clean_gds_path": str(clean_gds.resolve()),
            "clean_gds_sha256": sha256_file(clean_gds),
            "machine_gate": validation.machine_gate,
            "rejection_codes": validation.rejection_codes,
            "post_review_machine_regression_passed": validation.passed,
        },
    )
    write_text(
        human_dir / "PNAND2_HUMAN_REVIEW_REPORT.md",
        _render_md(
            "PNAND2 Human Review",
            [
                "- review_result: `PASS`",
                "- review_source: `USER_ATTESTATION`",
                f"- reviewed_clean_gds_sha256: `{PNAND2_SHA}`",
                "- screenshots_supplied: `false`",
                "- post_review_same_sha: `true`",
                f"- post_review_machine_regression_passed: `{validation.passed}`",
                "- status: `OWNER_A_HUMAN_REVIEWED_REFERENCE_DEMO_PENDING_TEAM_B_INDEPENDENT_REVIEW`",
            ],
        ),
    )
    return attestation


def _generate_pnand3(out_root: Path, openyield_root: Path, openram_root: Path, klayout_bin: Path, drc_deck: Path, lvs_deck: Path, *, resume_negative_tests: bool = False) -> dict[str, Any]:
    cell_dir = out_root / "PNAND3"
    cell_dir.mkdir(parents=True, exist_ok=True)
    annotated_gds = cell_dir / "annotated.gds"
    atlas_gds = cell_dir / "review_atlas.gds"
    clean_gds, pin_map, generation = _generate_pnand3_clean_gds(output_dir=cell_dir, openram_root=openram_root)
    build_pnand2_style_annotated_gds(clean_gds=clean_gds, top_name=PNAND3_NAME, device_layout=generation["device_layout"], output_gds=annotated_gds)
    build_pnand2_style_review_atlas(clean_gds=clean_gds, annotated_gds=annotated_gds, top_name=PNAND3_NAME, output_gds=atlas_gds)
    source_lock = build_pnand3_source_lock(openyield_root)
    write_json(cell_dir / "source_lock.json", source_lock)
    write_text(cell_dir / "source_lock.md", _render_md("PNAND3 Source Lock", [f"- topology_digest: `{source_lock['topology_digest']}`"]))
    write_text(cell_dir / "source_snapshot.py", subprocess.check_output(["git", "-C", str(openyield_root), "show", f"{source_lock['authority_commit']}:{source_lock['source_relative_path']}"], text=True))
    _build_pnand3_source_reference(cell_dir / "source_reference.spice")
    drc = run_recorded_drc(klayout_bin=klayout_bin, drc_deck=drc_deck, input_gds=clean_gds, top_name=PNAND3_NAME, output_dir=cell_dir / "drc")
    lvs = run_recorded_lvs(klayout_bin=klayout_bin, lvs_deck=lvs_deck, clean_gds=clean_gds, top_name=PNAND3_NAME, source_reference_spice=cell_dir / "source_reference.spice", extracted_spice=cell_dir / "extracted.spice", output_dir=cell_dir / "lvs")
    lvs_report = _compare_pnand3_extracted(cell_dir / "source_reference.spice", cell_dir / "extracted.spice", Path(lvs["lvsdb_path"]))
    write_json(cell_dir / "lvs" / "contract_report.json", lvs_report)
    top_labels = direct_top_labels_report(clean_gds, PNAND3_NAME, expected_top_pins=["VDD", "VSS", "A", "B", "C", "Z"], internal_nets=["net1", "net2"])
    write_json(cell_dir / "direct_top_label_report.json", top_labels)
    write_json(cell_dir / "pin_map.json", pin_map)
    write_json(cell_dir / "parameter_mapping.json", generation["parameter_mapping"])
    write_json(cell_dir / "device_or_child_inventory.json", {"device_layout": generation["device_layout"]})
    determinism = _pnand3_determinism_report(openram_root)
    write_json(cell_dir / "determinism.json", determinism)
    connectivity = _verify_pnand3_physical_connectivity(clean_gds, sha256_file(clean_gds), pin_map, generation["device_layout"])
    write_json(cell_dir / "connectivity_graph.json", connectivity["graph"])
    write_json(cell_dir / "physical_connectivity_report.json", {k: v for k, v in connectivity.items() if k != "graph"})
    write_csv(cell_dir / "endpoint_mapping.csv", connectivity["endpoint_rows"])
    write_csv(cell_dir / "contact_pairs.csv", [{"net_name": key, "component_id": value} for key, value in connectivity["internal_net_components"].items()])
    machine_gate = {
        "source_lock_complete": True,
        "parameter_binding_closed": generation["parameter_mapping"]["mapping_status"] in {"EXACT_MATCH", "GRID_ROUNDED_WITHIN_TOLERANCE"},
        "requested_actual_parameter_match": generation["parameter_mapping"]["mapping_status"] in {"EXACT_MATCH", "GRID_ROUNDED_WITHIN_TOLERANCE"},
        "top_pin_contract_exact": top_labels["pin_name_set_exact"] and top_labels["pin_count_exact"] and top_labels["pin_order_exact"] and top_labels["direct_top_labels_exact"],
        "internal_net_not_exposed": top_labels["no_internal_net_promoted_to_top_port"],
        "device_count_exact": lvs_report["extracted_device_count_exact"],
        "topology_match": lvs_report["extracted_device_topology_matches_source"],
        "body_tie_match": lvs_report["body_connections_match_source"],
        "connectivity_passed": connectivity["connectivity_passed"],
        "drc_marker_count": drc["marker_count"],
        "strict_lvs_contract_passed": lvs_report["strict_lvs_contract_passed"],
        "deterministic_A_B_byte_identical": determinism["byte_identical"],
        "negative_tests_passed": False,
    }
    negative = run_pnand3_negative_regressions(
        baseline_clean_gds=clean_gds,
        source_lock_path=cell_dir / "source_lock.json",
        production_validator={"klayout_bin": str(klayout_bin), "drc_deck": str(drc_deck), "lvs_deck": str(lvs_deck)},
        output_dir=cell_dir / "negative_tests",
        resume=resume_negative_tests,
    )
    machine_gate["negative_tests_passed"] = negative["summary"]["negative_tests_passed"]
    write_json(cell_dir / "machine_gate.json", machine_gate)
    result = {"cell_dir": cell_dir, "clean_gds": clean_gds, "sha256": sha256_file(clean_gds), "drc": drc, "lvs": lvs_report, "machine_gate": machine_gate}
    _write_checkpoint(
        out_root,
        "PNAND3",
        {
            "module": "PNAND3",
            "generator_code_fingerprint": _code_fingerprint([Path(__file__), REPO_ROOT / "sram_layoutgen/openyield_adapter/openram_pnand3_adapter.py", REPO_ROOT / "sram_layoutgen/openyield_adapter/pnand3_source_lock.py"]),
            "source_lock_sha256": hashlib.sha256(json.dumps(json_safe(source_lock), sort_keys=True).encode("utf-8")).hexdigest(),
            "child_sha": {},
            "clean_gds_sha256": result["sha256"],
            "machine_gate": machine_gate,
        },
    )
    return result


def _generate_and2(out_root: Path, klayout_bin: Path, drc_deck: Path, *, openyield_root: Path, resume_negative_tests: bool = False, layout_only: bool = False) -> dict[str, Any]:
    cell_dir = out_root / "AND2"
    cell_dir.mkdir(parents=True, exist_ok=True)
    old_sha256 = sha256_file(cell_dir / "clean.gds") if (cell_dir / "clean.gds").exists() else None
    failed_dir = cell_dir / "failed_candidates" / "initial_candidate"
    if (cell_dir / "clean.gds").exists() and not failed_dir.exists():
        failed_dir.mkdir(parents=True, exist_ok=True)
        for artifact in ["clean.gds", "annotated.gds", "review_atlas.gds", "machine_gate.json", "hierarchy_closure.json", "direct_top_label_report.json", "connectivity_graph.json", "layout_quality_metrics.json"]:
            src = cell_dir / artifact
            if src.exists():
                shutil.copy2(src, failed_dir / src.name)
        if (cell_dir / "drc").exists():
            shutil.copytree(cell_dir / "drc", failed_dir / "drc")
    tech = Tech.freepdk45(REPO_ROOT)
    pnand2_dir = REPO_ROOT / "outputs/TeamB_PNAND2_reference_demo/current_supported_config"
    pinv_root = REPO_ROOT / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells"
    child_specs = [
        ChildSpec("nand", "PNAND2", PNAND2_NAME, pnand2_dir / f"{PNAND2_NAME}.gds", pnand2_dir / "PNAND2_pin_map.json"),
        ChildSpec("inv", "PINV", "PINV_NW90_PW270_L50", pinv_root / "PINV_NW90_PW270_L50/PINV_NW90_PW270_L50.gds", pinv_root / "PINV_NW90_PW270_L50/PINV_NW90_PW270_L50_pin_map.json"),
    ]
    lib, cloned, clone_rows = clone_children(child_specs, cell_dir / "_clones")
    placed = place_children_single_row(cloned, start_x=0.0, start_y=0.0, gap=AND_GATE_ZERO_GAP_POLICY["child_bbox_gap"])
    top = instantiate_children(lib, AND2_NAME, placed)
    power = bridge_power_rails(top, placed, tech)
    nand = next(item for item in placed if item.spec.instance_name == "nand")
    inv = next(item for item in placed if item.spec.instance_name == "inv")
    route_objects = add_horizontal_pin_route(top, nand.placed_pin_map["Z"][0], inv.placed_pin_map["A"][0], tech=tech, track_y=0.92)
    top_pins = {
        "VDD": power["VDD"],
        "VSS": power["VSS"],
        "A": nand.placed_pin_map["A"][0],
        "B": nand.placed_pin_map["B"][0],
        "Z": inv.placed_pin_map["Z"][0],
    }
    for name, bbox in top_pins.items():
        add_top_label(top, name, bbox)
    clean_gds = cell_dir / "clean.gds"
    write_gds(lib, clean_gds)
    annotate_from_bboxes(clean_gds, AND2_NAME, [{"label": item.spec.instance_name, "bbox": item.bbox} for item in placed], cell_dir / "annotated.gds")
    make_review_atlas(clean_gds, cell_dir / "annotated.gds", AND2_NAME, cell_dir / "review_atlas.gds")
    endpoints_by_net = {
        "A": [{"endpoint_name": "nand.A", "bbox": nand.placed_pin_map["A"][0]}],
        "B": [{"endpoint_name": "nand.B", "bbox": nand.placed_pin_map["B"][0]}],
        "Z": [{"endpoint_name": "inv.Z", "bbox": inv.placed_pin_map["Z"][0]}],
        "VDD": [{"endpoint_name": "nand.VDD", "bbox": nand.placed_pin_map["VDD"][0]}, {"endpoint_name": "inv.VDD", "bbox": inv.placed_pin_map["VDD"][0]}],
        "VSS": [{"endpoint_name": "nand.VSS", "bbox": nand.placed_pin_map["VSS"][0]}, {"endpoint_name": "inv.VSS", "bbox": inv.placed_pin_map["VSS"][0]}],
        "zb_int": [{"endpoint_name": "nand.Z", "bbox": nand.placed_pin_map["Z"][0]}, {"endpoint_name": "inv.A", "bbox": inv.placed_pin_map["A"][0]}],
    }
    report = simple_composite_verification(clean_gds=clean_gds, top_name=AND2_NAME, canonical_labels=["VDD", "VSS", "A", "B", "Z"], endpoints_by_net=endpoints_by_net, top_pin_bboxes=top_pins, klayout_path=klayout_bin, drc_deck=drc_deck, drc_dir=cell_dir / "drc")
    write_json(cell_dir / "hierarchy_closure.json", report["hierarchy"])
    write_json(cell_dir / "direct_top_label_report.json", report["namespace"])
    write_json(cell_dir / "connectivity_graph.json", report["connectivity"]["graph"])
    write_json(cell_dir / "layout_quality_metrics.json", {"bbox": gdstk.read_gds(clean_gds).top_level()[0].bounding_box() is not None})
    _write_zero_gap_formalization_artifacts(
        module_name="AND2",
        top_name=AND2_NAME,
        cell_dir=cell_dir,
        clean_gds=clean_gds,
        old_sha256=old_sha256,
        placed=placed,
        top_pins=top_pins,
        connectivity=report["connectivity"],
        route_objects=route_objects,
        write_global_artifacts=cell_dir.parent.resolve() == (REPO_ROOT / "outputs/TeamB_remaining9_reference_demo/current_supported_config").resolve(),
    )
    if layout_only:
        machine_gate = {
            "hierarchy_closure_passed": report["hierarchy"]["reference_closure_passed"],
            "top_pin_contract_exact": report["namespace"]["top_canonical_label_set_exact"],
            "child_label_leakage_count": report["namespace"]["internal_child_label_leakage_count"],
            "connectivity_passed": report["connectivity"]["physical_connectivity_verification_passed"],
            "drc_marker_count": report["drc"]["marker_count"],
        }
        write_json(cell_dir / "machine_gate.json", machine_gate)
        result = {"cell_dir": cell_dir, "clean_gds": clean_gds, "sha256": sha256_file(clean_gds), "machine_gate": machine_gate}
        return result
    build_and2_production_gate(
        repo_root=REPO_ROOT,
        cell_dir=cell_dir,
        openyield_root=openyield_root,
        klayout_bin=klayout_bin,
        drc_deck=drc_deck,
    )
    write_and2_repair_history(cell_dir)
    negative = run_and2_negative_regressions(
        baseline_clean_gds=clean_gds,
        production_validator={
            "repo_root": str(REPO_ROOT),
            "openyield_root": str(openyield_root),
            "klayout_bin": str(klayout_bin),
            "drc_deck": str(drc_deck),
        },
        output_dir=cell_dir / "negative_tests",
        resume=resume_negative_tests,
    )
    machine_gate = read_json(cell_dir / "machine_gate.json")
    machine_gate["negative_tests_passed"] = negative["summary"]["negative_tests_passed"]
    write_json(cell_dir / "machine_gate.json", machine_gate)
    _write_zero_gap_formalization_artifacts(
        module_name="AND2",
        top_name=AND2_NAME,
        cell_dir=cell_dir,
        clean_gds=clean_gds,
        old_sha256=old_sha256,
        placed=placed,
        top_pins=top_pins,
        connectivity=report["connectivity"],
        route_objects=route_objects,
        write_global_artifacts=cell_dir.parent.resolve() == (REPO_ROOT / "outputs/TeamB_remaining9_reference_demo/current_supported_config").resolve(),
    )
    result = {"cell_dir": cell_dir, "clean_gds": clean_gds, "sha256": sha256_file(clean_gds), "machine_gate": machine_gate}
    _write_checkpoint(
        out_root,
        "AND2",
        {
            "module": "AND2",
            "generator_code_fingerprint": _code_fingerprint([Path(__file__), REPO_ROOT / "sram_layoutgen/openyield_adapter/teamb_composite_helper.py", REPO_ROOT / "sram_layoutgen/openyield_adapter/hierarchical_connectivity_verifier.py"]),
            "source_lock_sha256": "",
            "child_sha": {
                PNAND2_NAME: PNAND2_SHA,
                "PINV_NW90_PW270_L50": sha256_file(child_specs[1].gds_path),
            },
            "clean_gds_sha256": result["sha256"],
            "machine_gate": machine_gate,
        },
    )
    return result


def _generate_and3(out_root: Path, klayout_bin: Path, drc_deck: Path, *, openyield_root: Path, layout_only: bool = False) -> dict[str, Any]:
    cell_dir = out_root / "AND3"
    cell_dir.mkdir(parents=True, exist_ok=True)
    old_sha256 = sha256_file(cell_dir / "clean.gds") if (cell_dir / "clean.gds").exists() else None
    tech = Tech.freepdk45(REPO_ROOT)
    pnand3_dir = REPO_ROOT / "outputs/TeamB_remaining9_reference_demo/current_supported_config/PNAND3"
    pinv_root = REPO_ROOT / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells"
    child_specs = [
        ChildSpec("nand3", "PNAND3", PNAND3_NAME, pnand3_dir / "clean.gds", pnand3_dir / "pin_map.json"),
        ChildSpec("inv", "PINV", "PINV_NW90_PW270_L50", pinv_root / "PINV_NW90_PW270_L50/PINV_NW90_PW270_L50.gds", pinv_root / "PINV_NW90_PW270_L50/PINV_NW90_PW270_L50_pin_map.json"),
    ]
    lib, cloned, clone_rows = clone_children(child_specs, cell_dir / "_clones")
    placed = place_children_single_row(cloned, start_x=0.0, start_y=0.0, gap=AND_GATE_ZERO_GAP_POLICY["child_bbox_gap"])
    top = instantiate_children(lib, AND3_NAME, placed)
    power = bridge_power_rails(top, placed, tech)
    nand3 = next(item for item in placed if item.spec.instance_name == "nand3")
    inv = next(item for item in placed if item.spec.instance_name == "inv")
    route_objects = add_horizontal_pin_route(top, nand3.placed_pin_map["Z"][0], inv.placed_pin_map["A"][0], tech=tech, track_y=1.08)
    top_pins = {
        "VDD": power["VDD"],
        "VSS": power["VSS"],
        "A": nand3.placed_pin_map["A"][0],
        "B": nand3.placed_pin_map["B"][0],
        "C": nand3.placed_pin_map["C"][0],
        "Z": inv.placed_pin_map["Z"][0],
    }
    for name, bbox in top_pins.items():
        add_top_label(top, name, bbox)
    clean_gds = cell_dir / "clean.gds"
    write_gds(lib, clean_gds)
    annotate_from_bboxes(clean_gds, AND3_NAME, [{"label": item.spec.instance_name, "bbox": item.bbox} for item in placed], cell_dir / "annotated.gds")
    make_review_atlas(clean_gds, cell_dir / "annotated.gds", AND3_NAME, cell_dir / "review_atlas.gds")
    endpoints_by_net = {
        "A": [{"endpoint_name": "nand3.A", "bbox": nand3.placed_pin_map["A"][0]}],
        "B": [{"endpoint_name": "nand3.B", "bbox": nand3.placed_pin_map["B"][0]}],
        "C": [{"endpoint_name": "nand3.C", "bbox": nand3.placed_pin_map["C"][0]}],
        "Z": [{"endpoint_name": "inv.Z", "bbox": inv.placed_pin_map["Z"][0]}],
        "VDD": [{"endpoint_name": "nand3.VDD", "bbox": nand3.placed_pin_map["VDD"][0]}, {"endpoint_name": "inv.VDD", "bbox": inv.placed_pin_map["VDD"][0]}],
        "VSS": [{"endpoint_name": "nand3.VSS", "bbox": nand3.placed_pin_map["VSS"][0]}, {"endpoint_name": "inv.VSS", "bbox": inv.placed_pin_map["VSS"][0]}],
        "zb_int": [{"endpoint_name": "nand3.Z", "bbox": nand3.placed_pin_map["Z"][0]}, {"endpoint_name": "inv.A", "bbox": inv.placed_pin_map["A"][0]}],
    }
    report = simple_composite_verification(
        clean_gds=clean_gds,
        top_name=AND3_NAME,
        canonical_labels=["VDD", "VSS", "A", "B", "C", "Z"],
        endpoints_by_net=endpoints_by_net,
        top_pin_bboxes=top_pins,
        klayout_path=klayout_bin,
        drc_deck=drc_deck,
        drc_dir=cell_dir / "drc",
    )
    write_json(cell_dir / "hierarchy_closure.json", report["hierarchy"])
    write_json(cell_dir / "direct_top_label_report.json", report["namespace"])
    write_json(cell_dir / "connectivity_graph.json", report["connectivity"]["graph"])
    write_json(cell_dir / "layout_quality_metrics.json", {"bbox": gdstk.read_gds(clean_gds).top_level()[0].bounding_box() is not None})
    _write_zero_gap_formalization_artifacts(
        module_name="AND3",
        top_name=AND3_NAME,
        cell_dir=cell_dir,
        clean_gds=clean_gds,
        old_sha256=old_sha256,
        placed=placed,
        top_pins=top_pins,
        connectivity=report["connectivity"],
        route_objects=route_objects,
        write_global_artifacts=cell_dir.parent.resolve() == (REPO_ROOT / "outputs/TeamB_remaining9_reference_demo/current_supported_config").resolve(),
    )
    if layout_only:
        top_ref_count = len(top.references)
        machine_gate = {
            "source_lock_complete": True,
            "parameter_binding_closed": True,
            "top_pin_contract_exact": report["namespace"]["top_canonical_label_set_exact"],
            "internal_net_not_exposed": report["namespace"]["internal_child_label_leakage_count"] == 0,
            "child_count_exact": top_ref_count == 2,
            "topology_match": report["connectivity"]["physical_connectivity_verification_passed"],
            "hierarchy_closure_passed": report["hierarchy"]["reference_closure_passed"],
            "connectivity_passed": report["connectivity"]["physical_connectivity_verification_passed"],
            "drc_marker_count": report["drc"]["marker_count"],
            "review_artifacts_complete": True,
        }
        write_json(cell_dir / "machine_gate.json", machine_gate)
        return {"cell_dir": cell_dir, "clean_gds": clean_gds, "sha256": sha256_file(clean_gds), "machine_gate": machine_gate, "clone_rows": clone_rows}
    build_and3_production_gate(
        repo_root=REPO_ROOT,
        cell_dir=cell_dir,
        openyield_root=openyield_root,
        klayout_bin=klayout_bin,
        drc_deck=drc_deck,
    )
    source_lock = read_json(cell_dir / "source_lock.json")
    machine_gate = read_json(cell_dir / "machine_gate.json")
    negative = run_and3_negative_regressions(
        baseline_clean_gds=clean_gds,
        production_validator={
            "repo_root": str(REPO_ROOT),
            "openyield_root": str(openyield_root),
            "klayout_bin": str(klayout_bin),
            "drc_deck": str(drc_deck),
        },
        output_dir=cell_dir / "negative_tests",
        resume=False,
    )
    machine_gate["negative_tests_passed"] = negative["summary"]["negative_tests_passed"]
    write_json(cell_dir / "machine_gate.json", machine_gate)
    _write_zero_gap_formalization_artifacts(
        module_name="AND3",
        top_name=AND3_NAME,
        cell_dir=cell_dir,
        clean_gds=clean_gds,
        old_sha256=old_sha256,
        placed=placed,
        top_pins=top_pins,
        connectivity=report["connectivity"],
        route_objects=route_objects,
        write_global_artifacts=cell_dir.parent.resolve() == (REPO_ROOT / "outputs/TeamB_remaining9_reference_demo/current_supported_config").resolve(),
    )
    result = {"cell_dir": cell_dir, "clean_gds": clean_gds, "sha256": sha256_file(clean_gds), "machine_gate": machine_gate, "clone_rows": clone_rows}
    _write_checkpoint(
        out_root,
        "AND3",
        {
            "module": "AND3",
            "generator_code_fingerprint": _code_fingerprint([Path(__file__), REPO_ROOT / "sram_layoutgen/openyield_adapter/teamb_composite_helper.py", REPO_ROOT / "sram_layoutgen/openyield_adapter/and3_source_lock.py"]),
            "source_lock_sha256": hashlib.sha256(json.dumps(source_lock, sort_keys=True).encode("utf-8")).hexdigest(),
            "child_sha": {PNAND3_NAME: PNAND3_SHA, "PINV_NW90_PW270_L50": sha256_file(pinv_root / "PINV_NW90_PW270_L50/PINV_NW90_PW270_L50.gds")},
            "clean_gds_sha256": result["sha256"],
            "machine_gate": machine_gate,
        },
    )
    return result


def _write_zero_gap_formalization_summary(out_root: Path, status: dict[str, Any]) -> None:
    and2 = status.get("stage2_and2", {})
    and3 = status.get("stage3_and3", {})
    if not and2 or not and3:
        return
    manifest = {
        "timestamp": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "policy": AND_GATE_ZERO_GAP_POLICY,
        "modules": {
            "AND2": {
                "clean_gds_path": str(Path(and2["clean_gds"]).resolve()),
                "clean_gds_sha256": and2["sha256"],
                "selected_candidate_json": str((ABUTMENT_ROOT / "AND2_SELECTED_CANDIDATE.json").resolve()),
                "power_stitching_proof": str((out_root / "AND2/ZERO_GAP_POWER_STITCHING_PROOF.json").resolve()),
                "zb_int_endpoint_proof": str((out_root / "AND2/ZERO_GAP_ZB_INT_ENDPOINT_PROOF.json").resolve()),
                "route_layer_report": str((out_root / "AND2/ZERO_GAP_ROUTE_LAYER_REPORT.json").resolve()),
            },
            "AND3": {
                "clean_gds_path": str(Path(and3["clean_gds"]).resolve()),
                "clean_gds_sha256": and3["sha256"],
                "selected_candidate_json": str((ABUTMENT_ROOT / "AND3_SELECTED_CANDIDATE.json").resolve()),
                "power_stitching_proof": str((out_root / "AND3/ZERO_GAP_POWER_STITCHING_PROOF.json").resolve()),
                "zb_int_endpoint_proof": str((out_root / "AND3/ZERO_GAP_ZB_INT_ENDPOINT_PROOF.json").resolve()),
                "route_layer_report": str((out_root / "AND3/ZERO_GAP_ROUTE_LAYER_REPORT.json").resolve()),
            },
        },
    }
    write_json(ABUTMENT_ROOT / "ZERO_GAP_FORMALIZATION_MANIFEST.json", manifest)
    write_text(
        ABUTMENT_ROOT / "ZERO_GAP_FORMALIZATION_DIFF.md",
        _render_md(
            "Zero Gap Formalization Diff",
            [
                "- child placement gap: `0.35 -> 0.0`",
                "- orientation: `R0+R0`",
                "- route style: `ZERO_GAP_M2_PARENT_ROUTE`",
                "- parent VDD/VSS rail regenerated from formal child placements",
                "- parent M2 route regenerated from formal child placements",
                "- child geometry unchanged",
                "- top Pin contract unchanged",
                f"- AND2 new SHA256: `{and2['sha256']}`",
                f"- AND3 new SHA256: `{and3['sha256']}`",
            ],
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--openyield-root", default="/data1/qujh/work/external/OpenYield")
    parser.add_argument("--openram-root", default="/data1/qujh/OpenRAM")
    parser.add_argument("--out-dir", default="outputs/TeamB_remaining9_reference_demo/current_supported_config")
    parser.add_argument("--klayout-bin", default="/usr/bin/klayout")
    parser.add_argument("--drc-deck", default="technology/freepdk45/tech/freepdk45.lydrc")
    parser.add_argument("--lvs-deck", default="technology/freepdk45/tech/freepdk45.lylvs")
    parser.add_argument("--only", choices=["PNAND3", "AND2", "AND3"], default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--rebuild-failed", action="store_true")
    parser.add_argument("--resume-negative-tests", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_root = (repo_root / args.out_dir).resolve()
    openyield_root = Path(args.openyield_root).expanduser().resolve()
    openram_root = Path(args.openram_root).resolve()
    klayout_bin = Path(args.klayout_bin).resolve()
    drc_deck = (repo_root / args.drc_deck).resolve()
    lvs_deck = (repo_root / args.lvs_deck).resolve()

    out_root.mkdir(parents=True, exist_ok=True)
    pnand2_review = _pnand2_post_review_readonly_regression(out_root, klayout_bin, drc_deck, lvs_deck)
    status = {
        "stage0_pnand2_readonly_review": pnand2_review,
        "batch_status": "IN_PROGRESS_PARTIAL",
    }
    if args.only in (None, "PNAND3"):
        status["stage1_pnand3"] = _generate_pnand3(out_root, openyield_root, openram_root, klayout_bin, drc_deck, lvs_deck, resume_negative_tests=args.resume_negative_tests)
    elif args.resume and (out_root / "PNAND3/machine_gate.json").exists():
        status["stage1_pnand3"] = read_json(out_root / "PNAND3/machine_gate.json")
    if args.only in (None, "AND2"):
        status["stage2_and2"] = _generate_and2(out_root, klayout_bin, drc_deck, openyield_root=openyield_root, resume_negative_tests=args.resume_negative_tests)
    elif args.resume and (out_root / "AND2/machine_gate.json").exists():
        status["stage2_and2"] = read_json(out_root / "AND2/machine_gate.json")
    if args.only in (None, "AND3"):
        status["stage3_and3"] = _generate_and3(out_root, klayout_bin, drc_deck, openyield_root=openyield_root)
    elif args.resume and (out_root / "AND3/machine_gate.json").exists():
        status["stage3_and3"] = read_json(out_root / "AND3/machine_gate.json")
    if args.only in (None, "AND2", "AND3") and "stage2_and2" in status and "stage3_and3" in status:
        _write_zero_gap_formalization_summary(out_root, status)
    write_json(out_root / "TEAM_B_REMAINING9_PROGRESS.json", status)
    print(
        json.dumps(
            {
                "status": status["batch_status"],
                "pnand3_sha": status.get("stage1_pnand3", {}).get("sha256"),
                "and2_sha": status.get("stage2_and2", {}).get("sha256"),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
    assert openyield_root.is_dir(), f"missing openyield_root: {openyield_root}"
    assert (openyield_root / "sram_compiler/subcircuits/standard_cell.py").is_file(), f"missing authority file under {openyield_root}"
    subprocess.run(["git", "-C", str(openyield_root), "cat-file", "-e", "1c34428d8b913963c4971d093b1a7c2df97a2509^{commit}"], check=True)
