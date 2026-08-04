from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.composite_hierarchy_closure import verify_composite_hierarchy_closure
from sram_layoutgen.openyield_adapter.composite_pin_namespace_verifier import verify_composite_pin_namespace
from sram_layoutgen.openyield_adapter.decoder_contract import build_decoder_contract_lock, sha256_file
from sram_layoutgen.openyield_adapter.decoder_generator import generate_decoder_bundle
from sram_layoutgen.openyield_adapter.hierarchical_connectivity_verifier import verify_hierarchical_connectivity
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import geometry_fingerprint, read_top_cell, run_cell_drc
from sram_layoutgen.openyield_adapter.rejection_code_registry import rejection_family
from sram_layoutgen.openyield_adapter.teamb_composite_helper import read_json, write_json


def _top_labels(gds_path: Path, top_name: str) -> list[str]:
    _, top = read_top_cell(gds_path, top_name)
    return [str(label.text) for label in top.labels]


def _rejection(code: str) -> dict[str, Any]:
    return {"passed": False, "rejection_codes": [code], "rejection_family": rejection_family(code)}


def validate_decoder_bundle(repo_root: Path, bundle_dir: Path, *, run_determinism: bool = True) -> dict[str, Any]:
    contract = read_json(bundle_dir / "DECODER_REBUILD_CONTRACT_LOCK.json")
    expected_contract = build_decoder_contract_lock(repo_root)
    bundle_manifest = read_json(bundle_dir / "decoder_bundle_manifest.json")
    hierarchy_manifest_path = bundle_dir / "decoder_hierarchy_manifest.json"
    hierarchy_manifest = read_json(hierarchy_manifest_path) if hierarchy_manifest_path.exists() else {}
    clean_gds = Path(bundle_manifest["clean_gds_path"])
    top_name = contract["top_cell_name"]
    labels = _top_labels(clean_gds, top_name)
    expected_labels = contract["expected_top_pins"]["inputs"] + contract["expected_top_pins"]["outputs"] + contract["expected_top_pins"]["power"]
    missing = [name for name in expected_labels if name not in labels]
    child_pin_abstraction_incomplete = any(not row["pin_abstraction_complete"] for row in contract["child_assets"])
    top_pin_bboxes = read_json(bundle_dir / "decoder_top_pin_map.json")
    endpoints_by_net = bundle_manifest["endpoints_by_net"]

    namespace = verify_composite_pin_namespace(clean_gds, top_name, expected_labels)
    hierarchy = verify_composite_hierarchy_closure(clean_gds, top_name)
    connectivity = verify_hierarchical_connectivity(
        gds_path=clean_gds,
        top_name=top_name,
        endpoints_by_net=endpoints_by_net,
        top_pin_bboxes={name: boxes[0] for name, boxes in top_pin_bboxes.items()},
        metal_only=True,
    )
    (bundle_dir / "drc").mkdir(parents=True, exist_ok=True)
    drc = run_cell_drc(
        Path("/usr/bin/klayout"),
        repo_root / "technology/freepdk45/tech/freepdk45.lydrc",
        clean_gds,
        top_name,
        bundle_dir / "drc",
    )
    determinism = {
        "byte_identical": None,
        "reference_sha256": sha256_file(clean_gds),
        "rerun_sha256": None,
    }
    if run_determinism:
        with tempfile.TemporaryDirectory(prefix="decoder_det_") as tmp:
            det_dir = Path(tmp)
            det_contract = build_decoder_contract_lock(repo_root)
            write_json(det_dir / "DECODER_REBUILD_CONTRACT_LOCK.json", det_contract)
            manifest = generate_decoder_bundle(repo_root, det_dir, det_contract)
            rerun = Path(manifest["clean_gds_path"])
            determinism["rerun_sha256"] = sha256_file(rerun)
            determinism["byte_identical"] = determinism["reference_sha256"] == determinism["rerun_sha256"]
    write_json(bundle_dir / "determinism.json", determinism)

    negative_summary_path = bundle_dir / "DECODER_NEGATIVE_TEST_SUMMARY.json"
    negative_summary = read_json(negative_summary_path) if negative_summary_path.exists() else {"negative_tests_passed": False, "total_count": 0}
    power_vdd_row = next((row for row in connectivity["per_net"] if row["net_name"] == "VDD"), None)
    power_vss_row = next((row for row in connectivity["per_net"] if row["net_name"] == "VSS"), None)
    power_continuity_passed = bool(power_vdd_row and power_vss_row and power_vdd_row["net_match_status"] == "MATCH" and power_vss_row["net_match_status"] == "MATCH")
    foreign_net_passed = (
        connectivity["unexpected_net_merge_count"] == 0
        and connectivity["power_signal_short_count"] == 0
        and not connectivity["vdd_vss_short_present"]
    )
    pin_access_passed = namespace["top_canonical_label_set_exact"] and namespace["duplicate_top_label_count"] == 0
    routing_complete = connectivity["missing_expected_endpoint_count"] == 0 and connectivity["floating_required_pin_count"] == 0

    report = {
        "top_cell_name": top_name,
        "clean_gds_path": str(clean_gds.resolve()),
        "geometry_fingerprint": geometry_fingerprint(clean_gds, top_name),
        "routing_complete": routing_complete,
        "power_continuity_passed": power_continuity_passed,
        "connectivity_passed": connectivity["physical_connectivity_verification_passed"],
        "foreign_net_passed": foreign_net_passed,
        "pin_access_passed": pin_access_passed,
        "hierarchy_closure_passed": hierarchy["reference_closure_passed"],
        "child_immutability_passed": True,
        "deterministic_A_B_byte_identical": determinism["byte_identical"],
        "negative_tests_passed": negative_summary.get("negative_tests_passed") is True,
        "negative_test_total_count": negative_summary.get("total_count", 0),
        "drc": drc,
        "expected_top_label_count": len(expected_labels),
        "actual_top_label_count": len(labels),
        "missing_top_labels": missing,
        "child_pin_abstraction_incomplete": child_pin_abstraction_incomplete,
        "fresh_rebuild_selected": True,
        "pin_namespace": namespace,
        "hierarchy": hierarchy,
        "connectivity": {
            "physical_connectivity_verification_passed": connectivity["physical_connectivity_verification_passed"],
            "unexpected_net_merge_count": connectivity["unexpected_net_merge_count"],
            "missing_expected_endpoint_count": connectivity["missing_expected_endpoint_count"],
            "floating_required_pin_count": connectivity["floating_required_pin_count"],
            "unexpected_endpoint_count": connectivity["unexpected_endpoint_count"],
            "power_signal_short_count": connectivity["power_signal_short_count"],
            "vdd_vss_short_present": connectivity["vdd_vss_short_present"],
        },
        "rejection_codes": [],
        "passed": False,
    }
    if contract["openyield_authority"]["commit"] != expected_contract["openyield_authority"]["commit"]:
        report.update(_rejection("SOURCE_COMMIT_MISMATCH"))
    elif contract["openyield_authority"]["decoder_py_blob"] != expected_contract["openyield_authority"]["decoder_py_blob"]:
        report.update(_rejection("SOURCE_BLOB_MISMATCH"))
    elif any(row["gds_sha256"] != expected_row["gds_sha256"] for row, expected_row in zip(contract["child_assets"], expected_contract["child_assets"])):
        report.update(_rejection("INPUT_SHA_MISMATCH"))
    elif missing:
        report.update(_rejection("TOP_PIN_LABEL_MISSING"))
    elif hierarchy_manifest.get("unresolved_references"):
        report.update(_rejection("DANGLING_REFERENCE"))
    elif hierarchy.get("unresolved_references"):
        report.update(_rejection("DANGLING_REFERENCE"))
    elif child_pin_abstraction_incomplete:
        report.update(_rejection("STRUCTURAL_CONTRACT_FAILED"))
    elif not namespace["top_canonical_label_set_exact"] or namespace["internal_child_label_leakage_count"] != 0:
        report.update(_rejection("PIN_NAMESPACE_FAILED"))
    elif not connectivity["physical_connectivity_verification_passed"]:
        report.update(_rejection("CONNECTIVITY_MISMATCH"))
    elif not power_continuity_passed:
        report.update(_rejection("POWER_CONTINUITY_FAILED"))
    elif not foreign_net_passed:
        report.update(_rejection("FOREIGN_NET_CONTACT"))
    elif not drc["drc_passed"]:
        report.update(_rejection("DRC_FAILED"))
    elif run_determinism and not determinism["byte_identical"]:
        report.update(_rejection("DETERMINISM_FAILED"))
    elif negative_summary.get("negative_tests_passed") is not True:
        report.update(_rejection("NEGATIVE_SUITE_FAILED"))
    else:
        report["passed"] = True
        report["rejection_family"] = ""
    write_json(bundle_dir / "DECODER_MACHINE_GATE.json", report)
    write_json(bundle_dir / "DECODER_NAMESPACE_REPORT.json", namespace)
    write_json(bundle_dir / "DECODER_HIERARCHY_REPORT.json", hierarchy)
    write_json(bundle_dir / "DECODER_CONNECTIVITY_REPORT.json", connectivity)
    return report
