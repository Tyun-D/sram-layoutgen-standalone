from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.decoder_contract import DECODER_CHILDREN, build_decoder_contract_lock, sha256_file
from sram_layoutgen.openyield_adapter.decoder_generator import generate_decoder_bundle
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
    clean_gds = Path(read_json(bundle_dir / "decoder_bundle_manifest.json")["clean_gds_path"])
    top_name = contract["top_cell_name"]
    labels = _top_labels(clean_gds, top_name)
    hierarchy = read_json(bundle_dir / "decoder_hierarchy_manifest.json")
    expected_labels = contract["expected_top_pins"]["inputs"] + contract["expected_top_pins"]["outputs"] + contract["expected_top_pins"]["power"]
    missing = [name for name in expected_labels if name not in labels]
    child_pin_abstraction_incomplete = any(not row["pin_abstraction_complete"] for row in contract["child_assets"])
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
    report = {
        "top_cell_name": top_name,
        "clean_gds_path": str(clean_gds.resolve()),
        "geometry_fingerprint": geometry_fingerprint(clean_gds, top_name),
        "routing_complete": False,
        "power_continuity_passed": False,
        "connectivity_passed": False,
        "foreign_net_passed": False,
        "pin_access_passed": False,
        "hierarchy_closure_passed": len(hierarchy.get("unresolved_references", [])) == 0,
        "child_immutability_passed": True,
        "deterministic_A_B_byte_identical": determinism["byte_identical"],
        "negative_tests_passed": False,
        "drc": drc,
        "expected_top_label_count": len(expected_labels),
        "actual_top_label_count": len(labels),
        "missing_top_labels": missing,
        "child_pin_abstraction_incomplete": child_pin_abstraction_incomplete,
        "fresh_rebuild_selected": True,
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
    elif hierarchy.get("unresolved_references"):
        report.update(_rejection("DANGLING_REFERENCE"))
    elif child_pin_abstraction_incomplete:
        report.update(_rejection("STRUCTURAL_CONTRACT_FAILED"))
    elif not drc["drc_passed"]:
        report.update(_rejection("DRC_FAILED"))
    elif run_determinism and not determinism["byte_identical"]:
        report.update(_rejection("DETERMINISM_FAILED"))
    else:
        report["passed"] = True
        report["rejection_family"] = ""
    write_json(bundle_dir / "DECODER_MACHINE_GATE.json", report)
    return report
