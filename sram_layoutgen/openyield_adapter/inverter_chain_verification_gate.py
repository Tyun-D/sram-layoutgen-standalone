from __future__ import annotations

import csv
import hashlib
import inspect
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.composite_hierarchy_closure import verify_composite_hierarchy_closure
from sram_layoutgen.openyield_adapter.hierarchical_connectivity_verifier import verify_hierarchical_connectivity
from sram_layoutgen.openyield_adapter.inverter_chain_generator import regenerate_selected_inverter_chain
from sram_layoutgen.openyield_adapter.inverter_chain_source_lock import MODULE_SPECS, build_inverter_chain_source_lock, resolve_approved_pinv_asset
from sram_layoutgen.openyield_adapter.pnand2_verification_gate import direct_top_labels_report, write_csv, write_json, write_text
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import conductive_geometry_fingerprint, geometry_fingerprint, non_text_geometry_fingerprint, read_top_cell
from sram_layoutgen.openyield_adapter.rejection_code_registry import rejection_family
from sram_layoutgen.openyield_adapter.teamb_composite_helper import read_json


def _render_md(title: str, lines: list[str]) -> str:
    return "\n".join([f"# {title}", "", *lines, ""]).rstrip() + "\n"


def _shift_pin_map(pin_map: dict[str, list[dict[str, Any]]], dx: float, dy: float) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for name, rows in pin_map.items():
        out[name] = []
        for row in rows:
            out[name].append(
                {
                    **row,
                    "lx": round(float(row["lx"]) + dx, 6),
                    "by": round(float(row["by"]) + dy, 6),
                    "rx": round(float(row["rx"]) + dx, 6),
                    "uy": round(float(row["uy"]) + dy, 6),
                }
            )
    return out


def _binding_rows(repo_root: Path, module_name: str) -> list[dict[str, Any]]:
    rows = []
    for child, physical_cell in zip(MODULE_SPECS[module_name]["logical_children"], MODULE_SPECS[module_name]["child_variants"]):
        asset = resolve_approved_pinv_asset(repo_root, physical_cell)
        rows.append(
            {
                "logical_child": child["logical_child"],
                "source_instance_path": child["source_instance_path"],
                "requested_nmos_width_nm": child["requested_nmos_width_nm"],
                "requested_pmos_width_nm": child["requested_pmos_width_nm"],
                "requested_length_nm": child["requested_length_nm"],
                "resolved_physical_cell": physical_cell,
                "child_gds_path": asset["gds_path"],
                "child_gds_sha256": asset["actual_sha256"],
                "pin_map_path": asset["pin_map_path"],
                "approved_reference_status": asset["reusable_status"],
            }
        )
    return rows


def _read_instance_binding_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_source_artifacts(repo_root: Path, openyield_root: Path, cell_dir: Path, module_name: str) -> dict[str, Any]:
    source_lock = build_inverter_chain_source_lock(openyield_root, repo_root, module_name)
    write_json(cell_dir / "source_lock.json", source_lock)
    write_text(
        cell_dir / "source_lock.md",
        _render_md(
            f"{module_name} Source Lock",
            [
                f"- authority_commit: `{source_lock['authority_commit']}`",
                f"- git_blob_sha: `{source_lock['git_blob_sha']}`",
                f"- class_name: `{source_lock['class_name']}`",
                f"- topology_digest: `{source_lock['topology_digest']}`",
            ],
        ),
    )
    bindings = _binding_rows(repo_root, module_name)
    write_json(
        cell_dir / "parameter_mapping.json",
        {
            "module_name": module_name,
            "top_cell_name": MODULE_SPECS[module_name]["top_cell_name"],
            "top_pin_order": MODULE_SPECS[module_name]["top_pin_order"],
            "internal_net_names": MODULE_SPECS[module_name]["internal_nets"],
            "output_polarity": MODULE_SPECS[module_name]["output_polarity"],
            "child_bindings": bindings,
        },
    )
    with (cell_dir / "instance_binding.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(bindings[0].keys()))
        writer.writeheader()
        writer.writerows(bindings)
    write_json(
        cell_dir / "top_pin_contract.json",
        {
            "top_pin_order": MODULE_SPECS[module_name]["top_pin_order"],
            "internal_net_names": MODULE_SPECS[module_name]["internal_nets"],
            "top_cell_name": MODULE_SPECS[module_name]["top_cell_name"],
        },
    )
    return {"source_lock": source_lock, "bindings": bindings}


def _top_labels_as_bboxes(clean_gds: Path, top_name: str) -> dict[str, dict[str, float]]:
    _, top = read_top_cell(clean_gds, top_name)
    out = {}
    for label in top.labels:
        out[str(label.text)] = {
            "lx": round(float(label.origin[0]) - 0.03, 6),
            "by": round(float(label.origin[1]) - 0.03, 6),
            "rx": round(float(label.origin[0]) + 0.03, 6),
            "uy": round(float(label.origin[1]) + 0.03, 6),
        }
    return out


def _resolve_bindings_from_gds(bundle_dir: Path, module_name: str) -> dict[str, Any]:
    bindings = read_json(bundle_dir / "parameter_mapping.json")["child_bindings"]
    clean_gds = bundle_dir / "clean.gds"
    lib, top = read_top_cell(clean_gds, MODULE_SPECS[module_name]["top_cell_name"])
    refs = list(top.references)
    resolved = []
    for binding, ref in zip(bindings, refs):
        origin = [round(float(ref.origin[0]), 6), round(float(ref.origin[1]), 6)]
        resolved.append(
            {
                **binding,
                "ref_cell_name": ref.cell_name or ref.cell.name,
                "origin": origin,
                "pin_map": _shift_pin_map(read_json(Path(binding["pin_map_path"])), *origin),
            }
        )
    return {"bindings": bindings, "refs": refs, "resolved": resolved}


def _export_reachable_subtree(lib: gdstk.Library, root_name: str, output_gds: Path) -> None:
    cell_by_name = {cell.name: cell for cell in lib.cells}
    seen: set[str] = set()
    ordered: list[gdstk.Cell] = []

    def visit(name: str) -> None:
        if name in seen:
            return
        seen.add(name)
        cell = cell_by_name[name]
        for ref in cell.references:
            target_name = ref.cell_name or ref.cell.name
            if target_name in cell_by_name:
                visit(target_name)
        ordered.append(cell)

    visit(root_name)
    child_lib = gdstk.Library(unit=lib.unit, precision=lib.precision)
    clones: dict[str, gdstk.Cell] = {}
    for cell in ordered:
        clones[cell.name] = cell.copy(cell.name, deep_copy=True)
    for cell in ordered:
        cloned = clones[cell.name]
        for reference in cloned.references:
            target_name = reference.cell_name or reference.cell.name
            if target_name in clones:
                reference.cell = clones[target_name]
        child_lib.add(cloned)
    output_gds.parent.mkdir(parents=True, exist_ok=True)
    child_lib.write_gds(output_gds)


def _child_immutability(bundle_dir: Path, module_name: str, resolved: list[dict[str, Any]]) -> dict[str, Any]:
    lib = gdstk.read_gds(bundle_dir / "clean.gds")
    rows = []
    modified = 0
    for row in resolved:
        actual_name = row["ref_cell_name"]
        with tempfile.TemporaryDirectory(prefix="inv_chain_child_") as tmp:
            tmp_path = Path(tmp) / f"{actual_name}.gds"
            _export_reachable_subtree(lib, actual_name, tmp_path)
            original = Path(row["child_gds_path"])
            match = (
                non_text_geometry_fingerprint(original, None)["digest"] == non_text_geometry_fingerprint(tmp_path, actual_name)["digest"]
                and conductive_geometry_fingerprint(original, None)["digest"] == conductive_geometry_fingerprint(tmp_path, actual_name)["digest"]
            )
            modified += 0 if match else 1
            rows.append({"logical_child": row["logical_child"], "resolved_physical_cell": row["resolved_physical_cell"], "ref_cell_name": actual_name, "geometry_match": match})
    report = {"child_immutability_passed": modified == 0, "child_geometry_modified_count": modified, "rows": rows}
    write_json(bundle_dir / "child_immutability.json", report)
    return report


def _endpoints_and_top_pins(bundle_dir: Path, module_name: str, resolved: list[dict[str, Any]]) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, float]]]:
    top_pin_bboxes = _top_labels_as_bboxes(bundle_dir / "clean.gds", MODULE_SPECS[module_name]["top_cell_name"])
    endpoints = {
        "A": [{"endpoint_name": f"{resolved[0]['logical_child']}.A", "bbox": resolved[0]["pin_map"]["A"][0]}],
        "Z": [{"endpoint_name": f"{resolved[-1]['logical_child']}.Z", "bbox": resolved[-1]["pin_map"]["Z"][0]}],
        "VDD": [],
        "VSS": [],
    }
    for row in resolved:
        endpoints["VDD"].append({"endpoint_name": f"{row['logical_child']}.VDD", "bbox": row["pin_map"]["VDD"][0]})
        endpoints["VSS"].append({"endpoint_name": f"{row['logical_child']}.VSS", "bbox": row["pin_map"]["VSS"][0]})
    for net_name, left, right in zip(MODULE_SPECS[module_name]["internal_nets"], resolved[:-1], resolved[1:]):
        endpoints[net_name] = [
            {"endpoint_name": f"{left['logical_child']}.Z", "bbox": left["pin_map"]["Z"][0]},
            {"endpoint_name": f"{right['logical_child']}.A", "bbox": right["pin_map"]["A"][0]},
        ]
    return endpoints, top_pin_bboxes


def _foreign_net_report(connectivity: dict[str, Any], internal_nets: list[str]) -> dict[str, Any]:
    passed = connectivity["unexpected_net_merge_count"] == 0 and connectivity["unexpected_endpoint_count"] == 0 and connectivity["power_signal_short_count"] == 0
    suspicious = []
    for row in connectivity["per_net"]:
        if row["net_name"] in internal_nets and row["net_match_status"] != "MATCH":
            suspicious.append(row["net_name"])
    return {"foreign_net_passed": passed, "suspicious_nets": suspicious, "connectivity_report": {k: v for k, v in connectivity.items() if k != "graph"}}


def _structural_contract_report(source_lock: dict[str, Any], expected_source_lock: dict[str, Any], bindings: list[dict[str, Any]], resolved: list[dict[str, Any]], labels: dict[str, Any], hierarchy: dict[str, Any], connectivity: dict[str, Any], child_immutability: dict[str, Any]) -> dict[str, Any]:
    actual_order = [row["resolved_physical_cell"] for row in resolved]
    expected_order = [row["resolved_physical_cell"] for row in bindings]
    return {
        "source_lock_complete": source_lock["authority_commit"] == expected_source_lock["authority_commit"] and source_lock["git_blob_sha"] == expected_source_lock["git_blob_sha"] and source_lock["topology_digest"] == expected_source_lock["topology_digest"],
        "parameter_binding_closed": all(row["child_gds_sha256"] for row in bindings),
        "top_pin_contract_exact": labels["direct_top_labels_exact"] and labels["no_internal_net_promoted_to_top_port"] and labels["no_duplicate_top_labels"],
        "internal_net_not_exposed": labels["no_internal_net_promoted_to_top_port"],
        "child_count_exact": len(resolved) == len(bindings),
        "stage_order_exact": actual_order == expected_order,
        "topology_match": connectivity["physical_connectivity_verification_passed"],
        "hierarchy_closure_passed": hierarchy["reference_closure_passed"],
        "child_immutability_passed": child_immutability["child_immutability_passed"],
        "connectivity_passed": connectivity["physical_connectivity_verification_passed"],
        "strict_source_derived_structural_gate_passed": actual_order == expected_order and connectivity["physical_connectivity_verification_passed"] and hierarchy["reference_closure_passed"] and child_immutability["child_immutability_passed"],
        "expected_order": expected_order,
        "actual_order": actual_order,
    }


def _binding_contract_report(repo_root: Path, bundle_dir: Path, module_name: str, resolved: list[dict[str, Any]]) -> dict[str, Any]:
    parameter_mapping = read_json(bundle_dir / "parameter_mapping.json")
    contract_rows = parameter_mapping["child_bindings"]
    csv_rows = _read_instance_binding_csv(bundle_dir / "instance_binding.csv")
    expected_rows = _binding_rows(repo_root, module_name)
    rows = []
    parameter_mapping_exact = len(contract_rows) == len(expected_rows)
    instance_binding_exact = len(csv_rows) == len(expected_rows)
    actual_reference_exact = len(resolved) == len(expected_rows)
    for index, expected in enumerate(expected_rows):
        contract = contract_rows[index] if index < len(contract_rows) else None
        csv_row = csv_rows[index] if index < len(csv_rows) else None
        actual_ref = resolved[index] if index < len(resolved) else None
        expected_subset = {key: str(value) for key, value in expected.items()}
        contract_subset = {key: str(contract[key]) for key in expected.keys()} if contract is not None else {}
        csv_subset = {key: str(csv_row[key]) for key in expected.keys()} if csv_row is not None else {}
        actual_ref_match = actual_ref is not None and expected["resolved_physical_cell"] in actual_ref["ref_cell_name"]
        parameter_mapping_exact = parameter_mapping_exact and contract_subset == expected_subset
        instance_binding_exact = instance_binding_exact and csv_subset == expected_subset
        actual_reference_exact = actual_reference_exact and actual_ref_match
        rows.append(
            {
                "logical_child": expected["logical_child"],
                "expected_resolved_physical_cell": expected["resolved_physical_cell"],
                "expected_child_gds_sha256": expected["child_gds_sha256"],
                "parameter_mapping_exact": contract_subset == expected_subset,
                "instance_binding_exact": csv_subset == expected_subset,
                "actual_reference_exact": actual_ref_match,
                "actual_ref_cell_name": "" if actual_ref is None else actual_ref["ref_cell_name"],
            }
        )
    report = {
        "parameter_mapping_exact": parameter_mapping_exact,
        "instance_binding_exact": instance_binding_exact,
        "actual_reference_exact": actual_reference_exact,
        "rows": rows,
    }
    write_json(bundle_dir / "binding_contract_report.json", report)
    return report


def _determinism(repo_root: Path, bundle_dir: Path, module_name: str, klayout_bin: Path, drc_deck: Path) -> dict[str, Any]:
    selected_payload = read_json(bundle_dir / "selected_floorplan.json")
    selected = selected_payload["selected_architecture"]
    selected_placements = selected_payload.get("selected_placements")
    with tempfile.TemporaryDirectory(prefix=f"{module_name}_det_a_") as a_dir, tempfile.TemporaryDirectory(prefix=f"{module_name}_det_b_") as b_dir:
        gen_a = regenerate_selected_inverter_chain(repo_root=repo_root, module_name=module_name, selected_architecture=selected, selected_placements=selected_placements, output_dir=Path(a_dir), klayout_bin=klayout_bin, drc_deck=drc_deck)
        gen_b = regenerate_selected_inverter_chain(repo_root=repo_root, module_name=module_name, selected_architecture=selected, selected_placements=selected_placements, output_dir=Path(b_dir), klayout_bin=klayout_bin, drc_deck=drc_deck)
        sha_a = hashlib.sha256((Path(a_dir) / "clean.gds").read_bytes()).hexdigest()
        sha_b = hashlib.sha256((Path(b_dir) / "clean.gds").read_bytes()).hexdigest()
        return {
            "run_a_clean_gds_path": str((Path(a_dir) / "clean.gds").resolve()),
            "run_b_clean_gds_path": str((Path(b_dir) / "clean.gds").resolve()),
            "run_a_sha256": sha_a,
            "run_b_sha256": sha_b,
            "byte_identical": sha_a == sha_b,
        }


def validate_inverter_chain_bundle(*, repo_root: Path, bundle_dir: Path, module_name: str, openyield_root: Path, klayout_bin: Path, drc_deck: Path) -> dict[str, Any]:
    source_lock = read_json(bundle_dir / "source_lock.json")
    expected_source_lock = build_inverter_chain_source_lock(openyield_root, repo_root, module_name)
    labels = direct_top_labels_report(bundle_dir / "clean.gds", MODULE_SPECS[module_name]["top_cell_name"], expected_top_pins=MODULE_SPECS[module_name]["top_pin_order"], internal_nets=MODULE_SPECS[module_name]["internal_nets"])
    write_json(bundle_dir / "direct_top_label_report.json", labels)
    hierarchy = verify_composite_hierarchy_closure(bundle_dir / "clean.gds", MODULE_SPECS[module_name]["top_cell_name"])
    write_json(bundle_dir / "hierarchy_closure.json", hierarchy)
    resolved_bundle = _resolve_bindings_from_gds(bundle_dir, module_name)
    binding_contract = _binding_contract_report(repo_root, bundle_dir, module_name, resolved_bundle["resolved"])
    endpoints, top_pin_bboxes = _endpoints_and_top_pins(bundle_dir, module_name, resolved_bundle["resolved"])
    verify_kwargs = {
        "gds_path": bundle_dir / "clean.gds",
        "top_name": MODULE_SPECS[module_name]["top_cell_name"],
        "endpoints_by_net": endpoints,
        "top_pin_bboxes": top_pin_bboxes,
    }
    if "short_exclusion_pairs" in inspect.signature(verify_hierarchical_connectivity).parameters:
        verify_kwargs["short_exclusion_pairs"] = [("A", "Z")]
    connectivity = verify_hierarchical_connectivity(**verify_kwargs)
    write_json(bundle_dir / "connectivity_graph.json", connectivity["graph"])
    write_json(bundle_dir / "physical_connectivity_report.json", {k: v for k, v in connectivity.items() if k != "graph"})
    foreign_report = _foreign_net_report(connectivity, MODULE_SPECS[module_name]["internal_nets"])
    write_json(bundle_dir / "foreign_net_report.json", {k: v for k, v in foreign_report.items() if k != "connectivity_report"})
    child_immutability = _child_immutability(bundle_dir, module_name, resolved_bundle["resolved"])
    structural = _structural_contract_report(source_lock, expected_source_lock, resolved_bundle["bindings"], resolved_bundle["resolved"], labels, hierarchy, connectivity, child_immutability)
    write_json(bundle_dir / "lvs/structural_contract_report.json", structural)
    determinism = _determinism(repo_root, bundle_dir, module_name, klayout_bin, drc_deck)
    stored_determinism = read_json(bundle_dir / "determinism.json") if (bundle_dir / "determinism.json").exists() else None
    determinism_artifact_matches = stored_determinism is None or stored_determinism.get("byte_identical") == determinism["byte_identical"]
    determinism["artifact_matches_recomputed"] = determinism_artifact_matches
    write_json(bundle_dir / "determinism.json", determinism)
    drc = read_json(bundle_dir / "layout_quality_metrics.json")
    rejection_codes = []
    if source_lock["authority_commit"] != expected_source_lock["authority_commit"]:
        rejection_codes.append("SOURCE_COMMIT_MISMATCH")
    if source_lock["git_blob_sha"] != expected_source_lock["git_blob_sha"]:
        rejection_codes.append("SOURCE_BLOB_MISMATCH")
    if len(resolved_bundle["refs"]) != len(resolved_bundle["bindings"]):
        rejection_codes.append("CHILD_COUNT_MISMATCH")
    elif not binding_contract["parameter_mapping_exact"] or not binding_contract["actual_reference_exact"]:
        rejection_codes.append("WRONG_PINV_VARIANT")
    if not labels["no_internal_net_promoted_to_top_port"]:
        rejection_codes.append("INTERNAL_NET_EXPOSED")
    elif not labels["direct_top_labels_exact"]:
        rejection_codes.append("TOP_PIN_ORDER_MISMATCH")
    if len(resolved_bundle["refs"]) == len(resolved_bundle["bindings"]) and not binding_contract["instance_binding_exact"]:
        rejection_codes.append("STAGE_ORDER_MISMATCH")
    if not child_immutability["child_immutability_passed"]:
        rejection_codes.append("CHILD_GEOMETRY_MUTATED")
    if not connectivity["physical_connectivity_verification_passed"]:
        if connectivity["power_signal_short_count"] > 0:
            rejection_codes.append("POWER_SIGNAL_SHORT")
        elif connectivity["A_Z_direct_short_present"]:
            rejection_codes.append("A_Z_REVERSED")
        elif connectivity["unexpected_endpoint_count"] > 0 and connectivity["unexpected_net_merge_count"] == 0:
            rejection_codes.append("FOREIGN_NET_CONTACT")
        elif connectivity["unexpected_net_merge_count"] > 0:
            rejection_codes.append("UNEXPECTED_INTERNAL_NET_MERGE")
        else:
            rejection_codes.append("STAGE_DISCONNECTED")
    elif not foreign_report["foreign_net_passed"]:
        rejection_codes.append("FOREIGN_NET_CONTACT")
    if read_json(bundle_dir / "layout_quality_metrics.json")["off_grid_count"] > 0:
        rejection_codes.append("OFF_GRID_GEOMETRY")
    drc_summary = {
        "marker_count": read_json(bundle_dir / "layout_quality_metrics.json")["drc_marker_count"],
        "drc_passed": read_json(bundle_dir / "layout_quality_metrics.json")["drc_marker_count"] == 0,
    }
    write_json(bundle_dir / "drc" / f"{module_name}_drc_summary.json", drc_summary)
    if drc_summary["marker_count"] > 0:
        rejection_codes.append("DRC_FAILED")
    if not determinism["byte_identical"] or not determinism_artifact_matches:
        rejection_codes.append("DETERMINISM_FAILED")
    machine_gate = {
        "source_lock_complete": not any(code in {"SOURCE_COMMIT_MISMATCH", "SOURCE_BLOB_MISMATCH"} for code in rejection_codes),
        "parameter_binding_closed": structural["parameter_binding_closed"],
        "top_pin_contract_exact": structural["top_pin_contract_exact"],
        "internal_net_not_exposed": structural["internal_net_not_exposed"],
        "child_count_exact": structural["child_count_exact"],
        "stage_order_exact": structural["stage_order_exact"],
        "topology_match": structural["topology_match"],
        "hierarchy_closure_passed": structural["hierarchy_closure_passed"],
        "child_immutability_passed": structural["child_immutability_passed"],
        "connectivity_passed": structural["connectivity_passed"],
        "foreign_net_passed": foreign_report["foreign_net_passed"],
        "strict_source_derived_structural_gate_passed": structural["strict_source_derived_structural_gate_passed"],
        "deterministic_A_B_byte_identical": determinism["byte_identical"],
        "negative_tests_passed": False,
        "review_artifacts_complete": False,
        "drc_marker_count": drc_summary["marker_count"],
    }
    return {
        "passed": len(rejection_codes) == 0,
        "rejection_codes": rejection_codes,
        "rejection_families": [rejection_family(code) for code in rejection_codes],
        "machine_gate": machine_gate,
        "label_report": labels,
        "hierarchy": hierarchy,
        "connectivity": connectivity,
        "foreign_net_report": foreign_report,
        "child_immutability": child_immutability,
        "structural": structural,
        "binding_contract": binding_contract,
        "determinism": determinism,
        "drc": drc_summary,
    }


def build_inverter_chain_production_gate(*, repo_root: Path, cell_dir: Path, module_name: str, openyield_root: Path, klayout_bin: Path, drc_deck: Path) -> dict[str, Any]:
    artifacts = _write_source_artifacts(repo_root, openyield_root, cell_dir, module_name)
    validation = validate_inverter_chain_bundle(repo_root=repo_root, bundle_dir=cell_dir, module_name=module_name, openyield_root=openyield_root, klayout_bin=klayout_bin, drc_deck=drc_deck)
    human_dir = cell_dir / "human_review"
    human_dir.mkdir(parents=True, exist_ok=True)
    write_text(
        human_dir / f"{module_name}_HUMAN_REVIEW_REPORT_TEMPLATE.md",
        _render_md(
            f"{module_name} Human Review",
            [
                "- Inspect child order and size progression.",
                "- Inspect adjacent gap reasonableness against gap_constraint_report.md.",
                "- Verify Poly/metal overlap is visual-only unless a contact is present.",
                "- Inspect VDD/VSS rail continuity, stage routing, and A/Z pin access.",
                "- Confirm the DRC database and selected_floorplan.json match the selected clean.gds SHA.",
            ],
        ),
    )
    write_text(
        human_dir / f"{module_name}_HUMAN_REVIEW_CHECKLIST.csv",
        "item,status,notes\nchild_order,PENDING,\nchild_size_progression,PENDING,\nadjacent_gap_reasonableness,PENDING,\ngap_does_not_hide_routing_error,PENDING,\npoly_metal_overlap_has_no_unintended_contact,PENDING,\nVDD_VSS_rail_continuity,PENDING,\ninternal_stage_routing,PENDING,\nA_Z_pin_access,PENDING,\nno_internal_net_top_label,PENDING,\ndrc_database_matches_selected_sha,PENDING,\nselected_floorplan_matches_json,PENDING,\n",
    )
    write_text(
        human_dir / f"{module_name}_HUMAN_REVIEW_SCREENSHOT_INDEX.csv",
        "panel_id,description,path\nclean,clean layout,\nreview_atlas,overall review atlas,\ngap_dimensions,gap dimensions atlas,\npin_access,pin access atlas,\npower_rails,power rail atlas,\ndrc,drc database,\n",
    )
    write_json(
        human_dir / f"{module_name}_HUMAN_REVIEW_INPUT_LOCK.json",
        {
            "clean_gds": str((cell_dir / "clean.gds").resolve()),
            "annotated_gds": str((cell_dir / "annotated.gds").resolve()),
            "review_atlas": str((cell_dir / "review_atlas.gds").resolve()),
            "review_atlas_gap_dimensions": str((cell_dir / "review_atlas_gap_dimensions.gds").resolve()),
            "review_atlas_pin_access": str((cell_dir / "review_atlas_pin_access.gds").resolve()),
            "review_atlas_power_rails": str((cell_dir / "review_atlas_power_rails.gds").resolve()),
        },
    )
    machine_gate = validation["machine_gate"]
    required_review_artifacts = [
        cell_dir / "floorplan_candidates.json",
        cell_dir / "selected_floorplan.json",
        cell_dir / "layout_quality_metrics.json",
        cell_dir / "adjacent_gap_sweep.csv",
        cell_dir / "adjacent_gap_sweep.json",
        cell_dir / "gap_constraint_report.md",
        cell_dir / "poly_metal_overlap_report.json",
        cell_dir / "review_atlas.gds",
        cell_dir / "review_atlas_gap_dimensions.gds",
        cell_dir / "review_atlas_pin_access.gds",
        cell_dir / "review_atlas_power_rails.gds",
        human_dir / f"{module_name}_HUMAN_REVIEW_CHECKLIST.csv",
        human_dir / f"{module_name}_HUMAN_REVIEW_REPORT_TEMPLATE.md",
        human_dir / f"{module_name}_HUMAN_REVIEW_SCREENSHOT_INDEX.csv",
    ]
    machine_gate["review_artifacts_complete"] = all(path.exists() for path in required_review_artifacts)
    write_json(cell_dir / "machine_gate.json", machine_gate)
    return {"machine_gate": machine_gate, **validation}
