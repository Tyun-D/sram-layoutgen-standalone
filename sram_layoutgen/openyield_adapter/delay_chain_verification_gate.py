from __future__ import annotations

import csv
import hashlib
import tempfile
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.composite_hierarchy_closure import verify_composite_hierarchy_closure
from sram_layoutgen.openyield_adapter.delay_chain_connectivity import build_delay_chain_endpoints, verify_intentional_floating_outputs
from sram_layoutgen.openyield_adapter.delay_chain_contract import build_stage_topology, stage_endpoint_contract
from sram_layoutgen.openyield_adapter.delay_chain_generator import generate_delay_chain_layout
from sram_layoutgen.openyield_adapter.delay_chain_source_lock import MODULE_SPECS, build_delay_chain_source_lock, resolve_approved_pinv_asset
from sram_layoutgen.openyield_adapter.hierarchical_connectivity_verifier import verify_hierarchical_connectivity
from sram_layoutgen.openyield_adapter.pnand2_verification_gate import direct_top_labels_report
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import conductive_geometry_fingerprint, non_text_geometry_fingerprint, read_top_cell
from sram_layoutgen.openyield_adapter.rejection_code_registry import rejection_family
from sram_layoutgen.openyield_adapter.teamb_composite_helper import read_json, write_csv, write_json, write_text


def _render_md(title: str, lines: list[str]) -> str:
    return "\n".join([f"# {title}", "", *lines, ""]).rstrip() + "\n"


def normalize_connectivity_report_schema(
    *,
    contract_rows: list[dict[str, Any]],
    graph: dict[str, Any] | None = None,
) -> dict[str, Any]:
    per_net = []
    missing_total = 0
    for row in contract_rows:
        per_net.append(
            {
                "net_name": row["net_name"],
                "expected_endpoint_set": row["expected_endpoints"],
                "actual_endpoint_set": [],
                "missing_endpoints": row["expected_endpoints"],
                "unexpected_endpoints": [],
                "component_id": None,
                "net_match_status": "MISSING",
            }
        )
        missing_total += len(row["expected_endpoints"])
    return {
        "graph": graph or {
            "gds_path": "",
            "top_cell": "",
            "components": {},
            "pin_labels": {},
            "label_hits": {},
            "labels": [],
            "rectangles": [],
        },
        "per_net": per_net,
        "expected_net_count": len(contract_rows),
        "actual_net_component_count": 0,
        "unexpected_net_merges": {},
        "unexpected_net_merge_count": 0,
        "missing_expected_endpoint_count": missing_total,
        "unexpected_endpoint_count": 0,
        "floating_required_pin_count": 0,
        "power_signal_short_count": 0,
        "vdd_vss_short_present": False,
        "D_Q_direct_short_present": False,
        "physical_connectivity_verification_passed": False,
        "component_summary": {},
        "stage_components": {},
        "top_pin_components": {},
        "child_pin_components": {},
        "intentional_floating_components": {},
        "unexpected_merges": {},
        "missing_connections": {row["net_name"]: row["expected_endpoints"] for row in contract_rows},
    }


def _shift_pin_map(pin_map: dict[str, list[dict[str, Any]]], dx: float, dy: float) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for name, rows in pin_map.items():
        out[name] = []
        for row in rows:
            out[name].append({**row, "lx": round(float(row["lx"]) + dx, 6), "by": round(float(row["by"]) + dy, 6), "rx": round(float(row["rx"]) + dx, 6), "uy": round(float(row["uy"]) + dy, 6)})
    return out


def _label_bbox(labels: dict[str, Any], text: str) -> dict[str, float] | None:
    for row in labels.get("direct_top_label_rows", []):
        if str(row.get("text")) != text:
            continue
        x = float(row["origin"][0])
        y = float(row["origin"][1])
        return {
            "lx": round(x - 0.03, 6),
            "by": round(y - 0.03, 6),
            "rx": round(x + 0.03, 6),
            "uy": round(y + 0.03, 6),
        }
    return None


def _write_source_artifacts(repo_root: Path, openyield_root: Path, cell_dir: Path, module_name: str) -> dict[str, Any]:
    spec = MODULE_SPECS[module_name]
    source_lock = build_delay_chain_source_lock(openyield_root, repo_root, module_name)
    write_json(cell_dir / "source_lock.json", source_lock)
    write_text(cell_dir / "source_lock.md", _render_md(f"{module_name} Source Lock", [f"- authority_commit: `{source_lock['authority_commit']}`", f"- git_blob_sha: `{source_lock['git_blob_sha']}`", f"- class_name: `{source_lock['class_name']}`", f"- topology_digest: `{source_lock['topology_digest']}`"]))
    asset = resolve_approved_pinv_asset(repo_root, spec["child_variant"])
    parameter_mapping = {
        "module_name": module_name,
        "top_cell_name": spec["top_cell_name"],
        "top_pin_order": spec["top_pin_order"],
        "stage_count": spec["stage_count"],
        "loads_per_stage": spec["loads_per_stage"],
        "child_variant": spec["child_variant"],
        "output_polarity": spec["output_polarity"],
        "approved_child_gds_path": asset["gds_path"],
        "approved_child_sha256": asset["actual_sha256"],
        "pin_map_path": asset["pin_map_path"],
    }
    write_json(cell_dir / "parameter_mapping.json", parameter_mapping)
    write_json(cell_dir / "top_pin_contract.json", {"top_pin_order": spec["top_pin_order"], "top_cell_name": spec["top_cell_name"], "internal_stage_net_policy": "not top labels"})
    return {"source_lock": source_lock, "parameter_mapping": parameter_mapping}


def _resolve_bindings_from_gds(bundle_dir: Path, module_name: str, repo_root: Path) -> dict[str, Any]:
    spec = MODULE_SPECS[module_name]
    binding_rows = read_json(bundle_dir / "instance_role_manifest.json")["rows"]
    asset = resolve_approved_pinv_asset(repo_root, spec["child_variant"])
    pin_map = read_json(Path(asset["pin_map_path"]))
    clean_gds = bundle_dir / "clean.gds"
    _, top = read_top_cell(clean_gds, spec["top_cell_name"])
    refs = list(top.references)
    resolved = []
    for binding, ref in zip(binding_rows, refs):
        origin = [round(float(ref.origin[0]), 6), round(float(ref.origin[1]), 6)]
        resolved.append({**binding, "ref_cell_name": ref.cell_name or ref.cell.name, "origin": origin, "pin_map": _shift_pin_map(pin_map, *origin)})
    return {"bindings": binding_rows, "refs": refs, "resolved": resolved, "actual_ref_count": len(refs)}


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
    clones: dict[str, gdstk.Cell] = {cell.name: cell.copy(cell.name, deep_copy=True) for cell in ordered}
    for cell in ordered:
        cloned = clones[cell.name]
        for reference in cloned.references:
            target_name = reference.cell_name or reference.cell.name
            if target_name in clones:
                reference.cell = clones[target_name]
        child_lib.add(cloned)
    output_gds.parent.mkdir(parents=True, exist_ok=True)
    child_lib.write_gds(output_gds)


def _child_immutability(bundle_dir: Path, module_name: str, resolved: list[dict[str, Any]], repo_root: Path) -> dict[str, Any]:
    spec = MODULE_SPECS[module_name]
    asset = resolve_approved_pinv_asset(repo_root, spec["child_variant"])
    lib = gdstk.read_gds(bundle_dir / "clean.gds")
    rows = []
    modified = 0
    for row in resolved:
        actual_name = row["ref_cell_name"]
        with tempfile.TemporaryDirectory(prefix="delay_chain_child_") as tmp:
            tmp_path = Path(tmp) / f"{actual_name}.gds"
            _export_reachable_subtree(lib, actual_name, tmp_path)
            original = Path(asset["gds_path"])
            match = non_text_geometry_fingerprint(original, None)["digest"] == non_text_geometry_fingerprint(tmp_path, actual_name)["digest"] and conductive_geometry_fingerprint(original, None)["digest"] == conductive_geometry_fingerprint(tmp_path, actual_name)["digest"]
            modified += 0 if match else 1
            rows.append({"instance_role": row["instance_role"], "resolved_physical_cell": spec["child_variant"], "ref_cell_name": actual_name, "geometry_match": match})
    report = {"child_immutability_passed": modified == 0, "child_geometry_modified_count": modified, "rows": rows}
    write_json(bundle_dir / "child_immutability.json", report)
    return report


def _stage_connectivity_reports(bundle_dir: Path, module_name: str, resolved: list[dict[str, Any]], top_pin_bboxes: dict[str, dict[str, float]]) -> dict[str, Any]:
    spec = MODULE_SPECS[module_name]
    contract_rows = stage_endpoint_contract(stage_count=spec["stage_count"], loads_per_stage=spec["loads_per_stage"])
    by_name = {row["instance_role"]: row for row in resolved}
    expected_roles = {f"stage_{stage_index:02d}_driver" for stage_index in range(spec["stage_count"])}
    expected_roles.update(
        {f"stage_{stage_index:02d}_load_{load_index:02d}" for stage_index in range(spec["stage_count"]) for load_index in range(spec["loads_per_stage"])}
    )
    missing_roles = sorted(expected_roles - set(by_name))
    if missing_roles:
        connectivity = normalize_connectivity_report_schema(contract_rows=contract_rows)
        write_json(bundle_dir / "connectivity_graph.json", connectivity["graph"])
        write_json(bundle_dir / "physical_connectivity_report.json", {k: v for k, v in connectivity.items() if k != "graph"})
        write_json(bundle_dir / "stage_endpoint_contract.json", {"rows": contract_rows})
        matrix_rows = [
            {
                "stage_index": row["stage_index"],
                "net_name": row["net_name"],
                "expected_endpoint_count": row["expected_endpoint_count"],
                "actual_endpoint_count": 0,
                "match": False,
                "expected_endpoints": "|".join(row["expected_endpoints"]),
                "actual_endpoints": "",
            }
            for row in contract_rows
        ]
        write_csv(bundle_dir / "stage_connectivity_matrix.csv", matrix_rows)
        return {
            "connectivity": connectivity,
            "missing_expected_endpoint_count": connectivity["missing_expected_endpoint_count"],
            "unexpected_endpoint_count": 0,
            "wrong_stage_binding_count": len(contract_rows),
            "missing_roles": missing_roles,
        }
    endpoints: dict[str, list[dict[str, Any]]] = {"VDD": [], "VSS": [], "in": [], "out": []}
    for row in resolved:
        endpoints["VDD"].append({"endpoint_name": f"{row['instance_role']}.VDD", "bbox": row["pin_map"]["VDD"][0]})
        endpoints["VSS"].append({"endpoint_name": f"{row['instance_role']}.VSS", "bbox": row["pin_map"]["VSS"][0]})
    endpoints["in"].append({"endpoint_name": "stage_00_driver.A", "bbox": by_name["stage_00_driver"]["pin_map"]["A"][0]})
    endpoints["out"].append({"endpoint_name": f"stage_{spec['stage_count'] - 1:02d}_driver.Z", "bbox": by_name[f"stage_{spec['stage_count'] - 1:02d}_driver"]["pin_map"]["Z"][0]})
    for stage_index in range(spec["stage_count"]):
        net_name = "out" if stage_index == spec["stage_count"] - 1 else f"stage_{stage_index:02d}_net"
        rows = [{"endpoint_name": f"stage_{stage_index:02d}_driver.Z", "bbox": by_name[f"stage_{stage_index:02d}_driver"]["pin_map"]["Z"][0]}]
        for load_index in range(spec["loads_per_stage"]):
            rows.append({"endpoint_name": f"stage_{stage_index:02d}_load_{load_index:02d}.A", "bbox": by_name[f"stage_{stage_index:02d}_load_{load_index:02d}"]["pin_map"]["A"][0]})
        if stage_index < spec["stage_count"] - 1:
            rows.append({"endpoint_name": f"stage_{stage_index + 1:02d}_driver.A", "bbox": by_name[f"stage_{stage_index + 1:02d}_driver"]["pin_map"]["A"][0]})
        endpoints[net_name] = rows
    connectivity = verify_hierarchical_connectivity(gds_path=bundle_dir / "clean.gds", top_name=spec["top_cell_name"], endpoints_by_net=endpoints, top_pin_bboxes=top_pin_bboxes)
    write_json(bundle_dir / "connectivity_graph.json", connectivity["graph"])
    write_json(bundle_dir / "physical_connectivity_report.json", {k: v for k, v in connectivity.items() if k != "graph"})
    write_json(bundle_dir / "stage_endpoint_contract.json", {"rows": contract_rows})
    matrix_rows = []
    per_net = {row["net_name"]: row for row in connectivity["per_net"]}
    missing_expected = 0
    unexpected_endpoint = 0
    wrong_stage_binding = 0
    for row in contract_rows:
        actual = per_net.get(row["net_name"], {"actual_endpoint_set": [], "missing_endpoints": [], "unexpected_endpoints": []})
        missing_expected += len(actual["missing_endpoints"])
        unexpected_endpoint += len(actual["unexpected_endpoints"])
        if sorted(actual["actual_endpoint_set"]) != sorted(row["expected_endpoints"]):
            wrong_stage_binding += 1
        matrix_rows.append({"stage_index": row["stage_index"], "net_name": row["net_name"], "expected_endpoint_count": row["expected_endpoint_count"], "actual_endpoint_count": len(actual["actual_endpoint_set"]), "match": sorted(actual["actual_endpoint_set"]) == sorted(row["expected_endpoints"]), "expected_endpoints": "|".join(row["expected_endpoints"]), "actual_endpoints": "|".join(actual["actual_endpoint_set"])})
    write_csv(bundle_dir / "stage_connectivity_matrix.csv", matrix_rows)
    return {"connectivity": connectivity, "missing_expected_endpoint_count": missing_expected, "unexpected_endpoint_count": unexpected_endpoint, "wrong_stage_binding_count": wrong_stage_binding}


def _determinism(repo_root: Path, bundle_dir: Path, module_name: str, klayout_bin: Path, drc_deck: Path) -> dict[str, Any]:
    spec = MODULE_SPECS[module_name]
    selected = read_json(bundle_dir / "selected_floorplan.json")
    with tempfile.TemporaryDirectory(prefix=f"{module_name}_det_a_") as a_dir, tempfile.TemporaryDirectory(prefix=f"{module_name}_det_b_") as b_dir:
        generate_delay_chain_layout(repo_root=repo_root, module_name=module_name, top_cell_name=spec["top_cell_name"], top_pin_order=spec["top_pin_order"], stage_count=spec["stage_count"], loads_per_stage=spec["loads_per_stage"], child_variant=spec["child_variant"], output_polarity=spec["output_polarity"], floorplan_policy=selected["selected_candidate_id"], output_dir=Path(a_dir), klayout_bin=klayout_bin, drc_deck=drc_deck)
        generate_delay_chain_layout(repo_root=repo_root, module_name=module_name, top_cell_name=spec["top_cell_name"], top_pin_order=spec["top_pin_order"], stage_count=spec["stage_count"], loads_per_stage=spec["loads_per_stage"], child_variant=spec["child_variant"], output_polarity=spec["output_polarity"], floorplan_policy=selected["selected_candidate_id"], output_dir=Path(b_dir), klayout_bin=klayout_bin, drc_deck=drc_deck)
        sha_a = hashlib.sha256((Path(a_dir) / "clean.gds").read_bytes()).hexdigest()
        sha_b = hashlib.sha256((Path(b_dir) / "clean.gds").read_bytes()).hexdigest()
        return {"run_a_clean_gds_path": str((Path(a_dir) / "clean.gds").resolve()), "run_b_clean_gds_path": str((Path(b_dir) / "clean.gds").resolve()), "run_a_sha256": sha_a, "run_b_sha256": sha_b, "byte_identical": sha_a == sha_b}


def validate_delay_chain_bundle(
    *,
    repo_root: Path,
    bundle_dir: Path,
    module_name: str,
    openyield_root: Path,
    klayout_bin: Path,
    drc_deck: Path,
    run_determinism: bool = True,
) -> dict[str, Any]:
    spec = MODULE_SPECS[module_name]
    source_lock = read_json(bundle_dir / "source_lock.json")
    expected_source_lock = build_delay_chain_source_lock(openyield_root, repo_root, module_name)
    parameter_mapping = read_json(bundle_dir / "parameter_mapping.json")
    labels = direct_top_labels_report(bundle_dir / "clean.gds", spec["top_cell_name"], expected_top_pins=spec["top_pin_order"], internal_nets=[f"stage_{i:02d}_net" for i in range(spec["stage_count"] - 1)])
    write_json(bundle_dir / "direct_top_label_report.json", labels)
    hierarchy = verify_composite_hierarchy_closure(bundle_dir / "clean.gds", spec["top_cell_name"])
    write_json(bundle_dir / "hierarchy_closure.json", hierarchy)
    resolved_bundle = _resolve_bindings_from_gds(bundle_dir, module_name, repo_root)
    expected_child_count = spec["stage_count"] * (spec["loads_per_stage"] + 1)
    by_role = {row["instance_role"]: row for row in resolved_bundle["resolved"]}
    top_pin_bboxes = {"VDD": read_json(bundle_dir / "power_rail_report.json")["VDD"]["spine_bbox"], "VSS": read_json(bundle_dir / "power_rail_report.json")["VSS"]["spine_bbox"]}
    in_role = "stage_00_driver"
    out_role = f"stage_{spec['stage_count'] - 1:02d}_driver"
    if in_role not in by_role or out_role not in by_role:
        contract_rows = stage_endpoint_contract(stage_count=spec["stage_count"], loads_per_stage=spec["loads_per_stage"])
        connectivity = normalize_connectivity_report_schema(contract_rows=contract_rows)
        floating = {
            "expected_intentional_floating_output_count": spec["stage_count"] * spec["loads_per_stage"],
            "intentional_floating_output_count": 0,
            "floating_output_components": [],
            "missing_roles": [in_role] if in_role not in by_role else [],
            "missing_floating_output_component_count": spec["stage_count"] * spec["loads_per_stage"],
            "merged_floating_output_component_count": 0,
            "floating_output_connected_to_power_count": 0,
            "intentional_floating_outputs_exact": False,
        }
        write_json(bundle_dir / "connectivity_graph.json", connectivity["graph"])
        write_json(bundle_dir / "physical_connectivity_report.json", {k: v for k, v in connectivity.items() if k != "graph"})
        write_json(bundle_dir / "stage_endpoint_contract.json", {"rows": contract_rows})
        write_csv(
            bundle_dir / "stage_connectivity_matrix.csv",
            [
                {
                    "stage_index": row["stage_index"],
                    "net_name": row["net_name"],
                    "expected_endpoint_count": row["expected_endpoint_count"],
                    "actual_endpoint_count": 0,
                    "match": False,
                    "expected_endpoints": "|".join(row["expected_endpoints"]),
                    "actual_endpoints": "",
                }
                for row in contract_rows
            ],
        )
        child_immutability = _child_immutability(bundle_dir, module_name, resolved_bundle["resolved"], repo_root)
        if resolved_bundle["actual_ref_count"] == 0:
            child_immutability = {
                "child_immutability_passed": False,
                "child_geometry_modified_count": expected_child_count,
                "rows": [],
                "reason": "flattened_or_missing_child_references",
            }
        write_json(bundle_dir / "intentional_floating_output_report.json", floating)
        determinism_path = bundle_dir / "determinism.json"
        if run_determinism or not determinism_path.exists():
            determinism = _determinism(repo_root, bundle_dir, module_name, klayout_bin, drc_deck)
            write_json(determinism_path, determinism)
        else:
            determinism = read_json(determinism_path)
        metrics = read_json(bundle_dir / "layout_quality_metrics.json")
        vertical_row = read_json(bundle_dir / "vertical_row_abutment_report.json")
        power_report = read_json(bundle_dir / "power_rail_report.json")
        poly_report = read_json(bundle_dir / "poly_metal_active_report.json")
        approved_asset = resolve_approved_pinv_asset(repo_root, spec["child_variant"])
        binding_variants_match = all(row.get("child_variant") == spec["child_variant"] for row in resolved_bundle["bindings"])
        binding_sha_match = all(row.get("approved_child_sha") == approved_asset["actual_sha256"] for row in resolved_bundle["bindings"])
        parameter_mapping_match = (
            parameter_mapping.get("child_variant") == spec["child_variant"]
            and parameter_mapping.get("approved_child_sha256") == approved_asset["actual_sha256"]
        )
        drc_summary = {"marker_count": metrics["drc_marker_count"], "drc_passed": metrics["drc_marker_count"] == 0}
        write_json(bundle_dir / "drc" / f"{module_name}_drc_summary.json", drc_summary)
        source_commit_match = source_lock["authority_commit"] == expected_source_lock["authority_commit"]
        source_blob_match = source_lock["git_blob_sha"] == expected_source_lock["git_blob_sha"]
        source_topology_match = source_lock["topology_digest"] == expected_source_lock["topology_digest"]
        driver_count_exact = sum(1 for row in resolved_bundle["bindings"] if row["role_type"] == "driver") == spec["stage_count"] and resolved_bundle["actual_ref_count"] == expected_child_count
        load_count_exact = sum(1 for row in resolved_bundle["bindings"] if row["role_type"] == "load") == spec["stage_count"] * spec["loads_per_stage"] and resolved_bundle["actual_ref_count"] == expected_child_count
        machine_gate = {
            "source_lock_complete": source_commit_match and source_blob_match and source_topology_match,
            "parameter_binding_closed": binding_variants_match and binding_sha_match and parameter_mapping_match,
            "top_pin_contract_exact": labels["direct_top_labels_exact"] and labels["no_duplicate_top_labels"],
            "internal_net_not_exposed": labels["no_internal_net_promoted_to_top_port"],
            "driver_count_exact": driver_count_exact,
            "load_count_exact": load_count_exact,
            "child_count_exact": len(resolved_bundle["bindings"]) == expected_child_count and resolved_bundle["actual_ref_count"] == expected_child_count,
            "loads_per_stage_exact": False,
            "stage_order_exact": False,
            "topology_match": False,
            "output_polarity_match": expected_source_lock["output_polarity"] == spec["output_polarity"],
            "intentional_floating_outputs_exact": False,
            "hierarchy_closure_passed": hierarchy["reference_closure_passed"],
            "child_immutability_passed": child_immutability["child_immutability_passed"],
            "connectivity_passed": False,
            "foreign_net_passed": False,
            "power_rail_continuity_passed": power_report["power_rail_continuity_passed"],
            "row_abutment_policy_passed": vertical_row["row_abutment_policy_passed"],
            "strict_source_derived_structural_gate_passed": False,
            "deterministic_A_B_byte_identical": determinism["byte_identical"],
            "negative_tests_passed": False,
            "review_artifacts_complete": False,
            "drc_marker_count": metrics["drc_marker_count"],
        }
        rejection_codes = []
        if not source_commit_match:
            rejection_codes.append("SOURCE_COMMIT_MISMATCH")
        elif not source_blob_match:
            rejection_codes.append("SOURCE_BLOB_MISMATCH")
        elif not source_topology_match:
            rejection_codes.append("STRUCTURAL_CONTRACT_FAILED")
        if not machine_gate["parameter_binding_closed"]:
            if not binding_variants_match or parameter_mapping.get("child_variant") != spec["child_variant"]:
                rejection_codes.append("WRONG_PINV_VARIANT")
            else:
                rejection_codes.append("PINV_CHILD_SHA_MISMATCH")
        if not child_immutability["child_immutability_passed"]:
            rejection_codes.append("CHILD_GEOMETRY_MUTATED")
        if not driver_count_exact:
            rejection_codes.append("DRIVER_COUNT_MISMATCH")
        if not load_count_exact:
            rejection_codes.append("LOAD_COUNT_MISMATCH")
        if not machine_gate["child_count_exact"] and "DRIVER_COUNT_MISMATCH" not in rejection_codes and "LOAD_COUNT_MISMATCH" not in rejection_codes:
            rejection_codes.append("CHILD_COUNT_MISMATCH")
        return {
            "passed": False,
            "rejection_codes": rejection_codes,
            "rejection_families": [rejection_family(code) for code in rejection_codes],
            "machine_gate": machine_gate,
            "label_report": labels,
            "hierarchy": hierarchy,
            "connectivity": connectivity,
            "child_immutability": child_immutability,
            "floating": floating,
        }
    top_pin_bboxes["in"] = _label_bbox(labels, "in") or by_role[in_role]["pin_map"]["A"][0]
    top_pin_bboxes["out"] = _label_bbox(labels, "out") or by_role[out_role]["pin_map"]["Z"][0]
    stage_reports = _stage_connectivity_reports(bundle_dir, module_name, resolved_bundle["resolved"], top_pin_bboxes)
    connectivity = stage_reports["connectivity"]
    child_immutability = _child_immutability(bundle_dir, module_name, resolved_bundle["resolved"], repo_root)
    floating = verify_intentional_floating_outputs(gds_path=bundle_dir / "clean.gds", top_name=spec["top_cell_name"], placed_children=resolved_bundle["resolved"], stage_count=spec["stage_count"], loads_per_stage=spec["loads_per_stage"], top_pin_bboxes=top_pin_bboxes)
    write_json(bundle_dir / "intentional_floating_output_report.json", floating)
    determinism_path = bundle_dir / "determinism.json"
    if run_determinism or not determinism_path.exists():
        determinism = _determinism(repo_root, bundle_dir, module_name, klayout_bin, drc_deck)
        write_json(determinism_path, determinism)
    else:
        determinism = read_json(determinism_path)
    metrics = read_json(bundle_dir / "layout_quality_metrics.json")
    vertical_row = read_json(bundle_dir / "vertical_row_abutment_report.json")
    power_report = read_json(bundle_dir / "power_rail_report.json")
    poly_report = read_json(bundle_dir / "poly_metal_active_report.json")
    approved_asset = resolve_approved_pinv_asset(repo_root, spec["child_variant"])
    binding_variants_match = all(row.get("child_variant") == spec["child_variant"] for row in resolved_bundle["bindings"])
    binding_sha_match = all(row.get("approved_child_sha") == approved_asset["actual_sha256"] for row in resolved_bundle["bindings"])
    parameter_mapping_match = (
        parameter_mapping.get("child_variant") == spec["child_variant"]
        and parameter_mapping.get("approved_child_sha256") == approved_asset["actual_sha256"]
    )
    drc_summary = {"marker_count": metrics["drc_marker_count"], "drc_passed": metrics["drc_marker_count"] == 0}
    write_json(bundle_dir / "drc" / f"{module_name}_drc_summary.json", drc_summary)
    foreign_net_passed = connectivity["unexpected_net_merge_count"] == 0 and connectivity["unexpected_endpoint_count"] == 0 and connectivity["power_signal_short_count"] == 0
    source_commit_match = source_lock["authority_commit"] == expected_source_lock["authority_commit"]
    source_blob_match = source_lock["git_blob_sha"] == expected_source_lock["git_blob_sha"]
    source_topology_match = source_lock["topology_digest"] == expected_source_lock["topology_digest"]
    machine_gate = {
        "source_lock_complete": source_commit_match and source_blob_match and source_topology_match,
        "parameter_binding_closed": binding_variants_match and binding_sha_match and parameter_mapping_match,
        "top_pin_contract_exact": labels["direct_top_labels_exact"] and labels["no_duplicate_top_labels"],
        "internal_net_not_exposed": labels["no_internal_net_promoted_to_top_port"],
        "driver_count_exact": sum(1 for row in resolved_bundle["bindings"] if row["role_type"] == "driver") == spec["stage_count"],
        "load_count_exact": sum(1 for row in resolved_bundle["bindings"] if row["role_type"] == "load") == spec["stage_count"] * spec["loads_per_stage"],
        "child_count_exact": len(resolved_bundle["bindings"]) == expected_child_count and resolved_bundle["actual_ref_count"] == expected_child_count,
        "loads_per_stage_exact": all(sum(1 for row in resolved_bundle["bindings"] if row["stage_index"] == stage and row["role_type"] == "load") == spec["loads_per_stage"] for stage in range(spec["stage_count"])),
        "stage_order_exact": [row["instance_role"] for row in resolved_bundle["bindings"]] == [row["logical_child"] for row in expected_source_lock["child_contract"]],
        "topology_match": stage_reports["wrong_stage_binding_count"] == 0 and connectivity["physical_connectivity_verification_passed"],
        "output_polarity_match": expected_source_lock["output_polarity"] == spec["output_polarity"],
        "intentional_floating_outputs_exact": floating["intentional_floating_outputs_exact"],
        "hierarchy_closure_passed": hierarchy["reference_closure_passed"],
        "child_immutability_passed": child_immutability["child_immutability_passed"],
        "connectivity_passed": connectivity["physical_connectivity_verification_passed"],
        "foreign_net_passed": foreign_net_passed,
        "power_rail_continuity_passed": power_report["power_rail_continuity_passed"],
        "row_abutment_policy_passed": vertical_row["row_abutment_policy_passed"],
        "strict_source_derived_structural_gate_passed": hierarchy["reference_closure_passed"] and child_immutability["child_immutability_passed"] and connectivity["physical_connectivity_verification_passed"],
        "deterministic_A_B_byte_identical": determinism["byte_identical"],
        "negative_tests_passed": False,
        "review_artifacts_complete": False,
        "drc_marker_count": metrics["drc_marker_count"],
    }
    rejection_codes = []
    if not source_commit_match:
        rejection_codes.append("SOURCE_COMMIT_MISMATCH")
    elif not source_blob_match:
        rejection_codes.append("SOURCE_BLOB_MISMATCH")
    elif not source_topology_match:
        rejection_codes.append("STRUCTURAL_CONTRACT_FAILED")
    if not machine_gate["parameter_binding_closed"]:
        if not binding_variants_match or parameter_mapping.get("child_variant") != spec["child_variant"]:
            rejection_codes.append("WRONG_PINV_VARIANT")
        else:
            rejection_codes.append("PINV_CHILD_SHA_MISMATCH")
    if not machine_gate["driver_count_exact"]:
        rejection_codes.append("DRIVER_COUNT_MISMATCH")
    if not machine_gate["load_count_exact"]:
        rejection_codes.append("LOAD_COUNT_MISMATCH")
    if not machine_gate["loads_per_stage_exact"]:
        rejection_codes.append("LOADS_PER_STAGE_MISMATCH")
    if not machine_gate["stage_order_exact"]:
        rejection_codes.append("STAGE_ORDER_MISMATCH")
    if not machine_gate["child_count_exact"] and "DRIVER_COUNT_MISMATCH" not in rejection_codes and "LOAD_COUNT_MISMATCH" not in rejection_codes:
        rejection_codes.append("CHILD_COUNT_MISMATCH")
    if not machine_gate["internal_net_not_exposed"]:
        rejection_codes.append("INTERNAL_NET_EXPOSED")
    elif not machine_gate["top_pin_contract_exact"]:
        rejection_codes.append("TOP_PIN_ORDER_MISMATCH")
    if connectivity["power_signal_short_count"] > 0 or connectivity.get("vdd_vss_short_present"):
        rejection_codes.append("POWER_SIGNAL_SHORT")
    elif floating.get("floating_output_connected_to_power_count", 0) > 0:
        rejection_codes.append("POWER_SIGNAL_SHORT")
    elif connectivity["unexpected_net_merge_count"] > 0:
        rejection_codes.append("FOREIGN_NET_CONTACT")
    elif floating.get("floating_output_connected_to_stage_net_count", 0) > 0 or floating.get("merged_floating_output_component_count", 0) > 0 or floating.get("missing_floating_output_component_count", 0) > 0:
        rejection_codes.append("FLOATING_OUTPUT_VIOLATION")
    elif not machine_gate["connectivity_passed"]:
        rejection_codes.append("STAGE_DISCONNECTED")
    elif not machine_gate["foreign_net_passed"]:
        rejection_codes.append("FOREIGN_NET_CONTACT")
    if not machine_gate["child_immutability_passed"]:
        rejection_codes.append("CHILD_GEOMETRY_MUTATED")
    if not poly_report["pass"]:
        rejection_codes.append("POLY_METAL_ACTIVE_VIOLATION")
    if metrics["off_grid_count"] > 0:
        rejection_codes.append("OFF_GRID_GEOMETRY")
    if metrics["drc_marker_count"] > 0:
        rejection_codes.append("DRC_FAILED")
    if not determinism["byte_identical"]:
        rejection_codes.append("DETERMINISM_FAILED")
    return {"passed": len(rejection_codes) == 0, "rejection_codes": rejection_codes, "rejection_families": [rejection_family(code) for code in rejection_codes], "machine_gate": machine_gate, "label_report": labels, "hierarchy": hierarchy, "connectivity": connectivity, "child_immutability": child_immutability, "floating": floating}


def build_delay_chain_production_gate(*, repo_root: Path, cell_dir: Path, module_name: str, openyield_root: Path, klayout_bin: Path, drc_deck: Path) -> dict[str, Any]:
    _write_source_artifacts(repo_root, openyield_root, cell_dir, module_name)
    validation = validate_delay_chain_bundle(repo_root=repo_root, bundle_dir=cell_dir, module_name=module_name, openyield_root=openyield_root, klayout_bin=klayout_bin, drc_deck=drc_deck)
    human_dir = cell_dir / "human_review"
    human_dir.mkdir(parents=True, exist_ok=True)
    write_text(human_dir / f"{module_name}_HUMAN_REVIEW_REPORT_TEMPLATE.md", _render_md(f"{module_name} Human Review", ["- Inspect stage count, driver/load role placement, and stage ordering.", "- Inspect 4 loads per stage and intentional floating load outputs.", "- Verify zero-gap horizontal abutment and vertical row rail sharing.", "- Inspect stage-net routing, Via1 completeness, VDD/VSS continuity, and top in/out pin access.", "- Confirm DRC database and selected_floorplan.json match the selected clean.gds SHA."]))
    write_text(human_dir / f"{module_name}_HUMAN_REVIEW_CHECKLIST.csv", "item,status,notes\nstage_count,PENDING,\ndriver_count,PENDING,\nload_count,PENDING,\nloads_per_stage,PENDING,\ndriver_load_roles,PENDING,\nstage_order,PENDING,\nload_input_attachment,PENDING,\nintentional_floating_outputs,PENDING,\ntop_in_out_contract,PENDING,\noutput_polarity,PENDING,\nhorizontal_zero_gap_abutment,PENDING,\nvertical_row_rail_sharing,PENDING,\nVDD_VSS_continuity,PENDING,\ninternal_stage_routing,PENDING,\nvia1_complete,PENDING,\npin_access,PENDING,\nno_internal_net_top_label,PENDING,\ndrc_database_matches_selected_sha,PENDING,\n")
    write_text(human_dir / f"{module_name}_HUMAN_REVIEW_SCREENSHOT_INDEX.csv", "panel_id,description,path\nclean,clean layout,\nreview_atlas,overall review atlas,\nstage_roles,stage role atlas,\nstage_nets,stage net atlas,\nfloating,floating output atlas,\npin_access,pin access atlas,\npower_rails,power rail atlas,\ndrc,drc database,\n")
    machine_gate = validation["machine_gate"]
    required_review_artifacts = [cell_dir / "floorplan_candidates.json", cell_dir / "floorplan_candidate_comparison.csv", cell_dir / "selected_floorplan.json", cell_dir / "layout_quality_metrics.json", cell_dir / "floorplan_selection_rationale.md", cell_dir / "power_rail_report.json", cell_dir / "vertical_row_abutment_report.json", cell_dir / "poly_metal_active_report.json", cell_dir / "review_atlas.gds", cell_dir / "review_atlas_stage_roles.gds", cell_dir / "review_atlas_stage_nets.gds", cell_dir / "review_atlas_floating_load_outputs.gds", cell_dir / "review_atlas_pin_access.gds", cell_dir / "review_atlas_power_rails.gds", human_dir / f"{module_name}_HUMAN_REVIEW_CHECKLIST.csv", human_dir / f"{module_name}_HUMAN_REVIEW_REPORT_TEMPLATE.md", human_dir / f"{module_name}_HUMAN_REVIEW_SCREENSHOT_INDEX.csv"]
    machine_gate["review_artifacts_complete"] = all(path.exists() for path in required_review_artifacts)
    write_json(cell_dir / "machine_gate.json", machine_gate)
    return {"machine_gate": machine_gate, **validation}
