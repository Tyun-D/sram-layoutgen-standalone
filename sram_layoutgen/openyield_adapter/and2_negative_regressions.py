from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.and2_production_verification_gate import AND2_NAME, PNAND2_NAME, PINV_NAME, validate_and2_bundle
from sram_layoutgen.openyield_adapter.pnand2_verification_gate import write_json, write_text
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
    run_hierarchy_mutation,
    swap_labels,
    write_case_checkpoint,
    write_negative_test_matrix,
    write_negative_test_summary,
)
from sram_layoutgen.openyield_adapter.rejection_code_registry import rejection_family


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _replace_json_value(path: Path, key: str, value: Any) -> None:
    payload = _json(path)
    payload[key] = value
    write_json(path, payload)


def _mutate_instance_binding(path: Path, logical_child: str, field: str, value: Any) -> None:
    payload = _json(path)
    for row in payload["children"]:
        if row["logical_child"] == logical_child:
            row[field] = value
    write_json(path, payload)


def _mutate_instance_binding_csv(path: Path, logical_child: str, field: str, value: Any) -> None:
    import csv

    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = rows[0].keys()
    for row in rows:
        if row["logical_child"] == logical_child:
            row[field] = value
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _remove_reference(gds_path: Path, match: str) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == AND2_NAME)
    victims = [ref for ref in top.references if match in (ref.cell_name or ref.cell.name)]
    if victims:
        top.remove(*victims)
    lib.write_gds(gds_path)


def _duplicate_reference(gds_path: Path) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == AND2_NAME)
    ref = top.references[0]
    top.add(gdstk.Reference(ref.cell, origin=(ref.origin[0] + 0.05, ref.origin[1] + 0.05)))
    lib.write_gds(gds_path)


def _swap_reference_type(gds_path: Path, from_match: str, to_match: str) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == AND2_NAME)
    target = next(cell for cell in lib.cells if to_match in cell.name)
    for ref in top.references:
        if from_match in (ref.cell_name or ref.cell.name):
            ref.cell = target
    lib.write_gds(gds_path)


def _remove_polygons_in_bbox(gds_path: Path, bbox: tuple[float, float, float, float], *, layers: set[int] | None = None) -> None:
    lib = gdstk.read_gds(gds_path)
    for cell in lib.cells:
        victims = []
        for poly in cell.polygons:
            if layers and poly.layer not in layers:
                continue
            pb = poly.bounding_box()
            if pb is None:
                continue
            if not (float(pb[1][0]) < bbox[0] or float(pb[0][0]) > bbox[2] or float(pb[1][1]) < bbox[1] or float(pb[0][1]) > bbox[3]):
                victims.append(poly)
        if victims:
            cell.remove(*victims)
    lib.write_gds(gds_path)


def _add_rect(gds_path: Path, bbox: tuple[float, float, float, float], *, layer: int) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == AND2_NAME)
    top.add(gdstk.rectangle((bbox[0], bbox[1]), (bbox[2], bbox[3]), layer=layer, datatype=0))
    lib.write_gds(gds_path)


def _mutate_child_clone(gds_path: Path, bbox: tuple[float, float, float, float], *, layer: int = 11) -> None:
    lib = gdstk.read_gds(gds_path)
    root = lib.cells[0]
    root.add(gdstk.rectangle((bbox[0], bbox[1]), (bbox[2], bbox[3]), layer=layer, datatype=0))
    lib.write_gds(gds_path)


def run_and2_negative_regressions(*, baseline_clean_gds: Path, production_validator: dict[str, Any], output_dir: Path, resume: bool = False) -> dict[str, Any]:
    base_dir = baseline_clean_gds.parent
    work_root = output_dir.parents[2] / "negative_test_work" / "AND2"
    if work_root.exists():
        shutil.rmtree(work_root)
    work_root.mkdir(parents=True, exist_ok=True)
    baseline_clean = Path("clean.gds")
    cases: list[tuple[MutationCase, Any, str]] = [
        (MutationCase("01_wrong_authority_commit", "contract", "SOURCE_LOCK_FAILED", "SOURCE_COMMIT_MISMATCH", Path("source_lock.json"), "validate_and2_bundle"), lambda d: (_replace_json_value(d / "source_lock.json", "authority_commit", "deadbeef"), d / "source_lock.json")[1], "contract"),
        (MutationCase("02_wrong_authority_blob", "contract", "SOURCE_LOCK_FAILED", "SOURCE_BLOB_MISMATCH", Path("source_lock.json"), "validate_and2_bundle"), lambda d: (_replace_json_value(d / "source_lock.json", "git_blob_sha", "deadbeef"), d / "source_lock.json")[1], "contract"),
        (MutationCase("03_wrong_PNAND2_SHA", "contract", "STRUCTURAL_CONTRACT_FAILED", "PNAND2_CHILD_SHA_MISMATCH", Path("parameter_mapping.json"), "validate_and2_bundle"), lambda d: (_mutate_instance_binding(d / "parameter_mapping.json", "nand_gate", "child_gds_sha256", "deadbeef"), d / "parameter_mapping.json")[1], "contract"),
        (MutationCase("04_wrong_PINV_SHA", "contract", "STRUCTURAL_CONTRACT_FAILED", "PINV_CHILD_SHA_MISMATCH", Path("parameter_mapping.json"), "validate_and2_bundle"), lambda d: (_mutate_instance_binding(d / "parameter_mapping.json", "inv_driver", "child_gds_sha256", "deadbeef"), d / "parameter_mapping.json")[1], "contract"),
        (MutationCase("05_missing_PNAND2", "hierarchy", "STRUCTURAL_CONTRACT_FAILED", "CHILD_COUNT_MISMATCH", baseline_clean, "validate_and2_bundle"), lambda d: (_remove_reference(d / "clean.gds", PNAND2_NAME), d / "clean.gds")[1], "hierarchy"),
        (MutationCase("06_missing_PINV", "hierarchy", "STRUCTURAL_CONTRACT_FAILED", "CHILD_COUNT_MISMATCH", baseline_clean, "validate_and2_bundle"), lambda d: (_remove_reference(d / "clean.gds", PINV_NAME), d / "clean.gds")[1], "hierarchy"),
        (MutationCase("07_extra_child", "hierarchy", "STRUCTURAL_CONTRACT_FAILED", "CHILD_COUNT_MISMATCH", baseline_clean, "validate_and2_bundle"), lambda d: (_duplicate_reference(d / "clean.gds"), d / "clean.gds")[1], "hierarchy"),
        (MutationCase("08_wrong_NAND_child_type", "hierarchy", "STRUCTURAL_CONTRACT_FAILED", "WRONG_CHILD_TYPE", baseline_clean, "validate_and2_bundle"), lambda d: (_swap_reference_type(d / "clean.gds", PNAND2_NAME, PINV_NAME), d / "clean.gds")[1], "hierarchy"),
        (MutationCase("09_wrong_PINV_variant", "contract", "STRUCTURAL_CONTRACT_FAILED", "WRONG_PINV_VARIANT", Path("parameter_mapping.json"), "validate_and2_bundle"), lambda d: (_mutate_instance_binding(d / "parameter_mapping.json", "inv_driver", "resolved_physical_cell", "PINV_NW180_PW270_L50"), d / "parameter_mapping.json")[1], "contract"),
        (MutationCase("10_wrong_top_pin_order", "contract", "TOP_PIN_CONTRACT_FAILED", "TOP_PIN_ORDER_MISMATCH", Path("top_pin_contract.json"), "validate_and2_bundle"), lambda d: (_replace_json_value(d / "top_pin_contract.json", "top_pin_order", ["A", "B", "Z", "VDD", "VSS"]), d / "top_pin_contract.json")[1], "contract"),
        (MutationCase("11_missing_top_pin_A", "label", "TOP_PIN_CONTRACT_FAILED", "DIRECT_TOP_LABEL_CONTRACT_FAILED", baseline_clean, "validate_and2_bundle"), lambda d: (remove_label(d / "clean.gds", AND2_NAME, "A"), d / "clean.gds")[1], "label"),
        (MutationCase("12_extra_top_pin_zb_int", "label", "TOP_PIN_CONTRACT_FAILED", "DIRECT_TOP_LABEL_CONTRACT_FAILED", baseline_clean, "validate_and2_bundle"), lambda d: (add_label(d / "clean.gds", AND2_NAME, "zb_int", (1.12, 0.92)), d / "clean.gds")[1], "label"),
        (MutationCase("13_PNAND2_Z_not_connected_to_PINV_A", "geometry", "CONNECTIVITY_MISMATCH", "MISSING_VIA1_CONNECTIVITY_BREAK", baseline_clean, "validate_and2_bundle"), lambda d: (_remove_polygons_in_bbox(d / "clean.gds", (0.84, 0.85, 1.10, 0.99), layers={13}), d / "clean.gds")[1], "geometry"),
        (MutationCase("14_zb_int_short_to_Z", "short", "CONNECTIVITY_MISMATCH", "UNEXPECTED_NET_MERGE_ZB_INT_Z", baseline_clean, "validate_and2_bundle"), lambda d: (_add_rect(d / "clean.gds", (1.27, 0.86, 1.49, 0.93), layer=11), d / "clean.gds")[1], "short"),
        (MutationCase("15_zb_int_short_to_VDD", "short", "POWER_SIGNAL_SHORT", "POWER_SIGNAL_SHORT_ZB_INT_VDD", baseline_clean, "validate_and2_bundle"), lambda d: (_add_rect(d / "clean.gds", (1.19, 0.92, 1.26, 1.86), layer=11), d / "clean.gds")[1], "short"),
        (MutationCase("16_zb_int_short_to_VSS", "short", "POWER_SIGNAL_SHORT", "POWER_SIGNAL_SHORT_ZB_INT_VSS", baseline_clean, "validate_and2_bundle"), lambda d: (_add_rect(d / "clean.gds", (1.19, 0.0, 1.26, 0.92), layer=11), d / "clean.gds")[1], "short"),
        (MutationCase("17_A_B_wrong_binding", "label", "CONNECTIVITY_MISMATCH", "TOP_INPUT_BINDING_MISMATCH_A_B", baseline_clean, "validate_and2_bundle"), lambda d: (swap_labels(d / "clean.gds", AND2_NAME, "A", "B"), d / "clean.gds")[1], "label"),
        (MutationCase("18_PINV_input_output_reversed", "contract", "STRUCTURAL_CONTRACT_FAILED", "PINV_INPUT_OUTPUT_BINDING_REVERSED", Path("instance_binding.csv"), "validate_and2_bundle"), lambda d: (_mutate_instance_binding_csv(d / "instance_binding.csv", "inv_driver", "source_instance_path", "AND2.inv_driver.Z->zb_int,A->Z"), d / "instance_binding.csv")[1], "contract"),
        (MutationCase("19_missing_Via1", "geometry", "CONNECTIVITY_MISMATCH", "MISSING_VIA1_CONNECTIVITY_BREAK", baseline_clean, "validate_and2_bundle"), lambda d: (_remove_polygons_in_bbox(d / "clean.gds", (0.92, 0.88, 1.62, 0.97), layers={12}), d / "clean.gds")[1], "geometry"),
        (MutationCase("20_foreign_net_contact", "short", "FOREIGN_NET_FAILED", "FOREIGN_NET_CONTACT", baseline_clean, "validate_and2_bundle"), lambda d: (_add_rect(d / "clean.gds", (0.48, 0.74, 1.12, 0.805), layer=11), d / "clean.gds")[1], "short"),
        (MutationCase("21_child_geometry_mutation", "geometry", "CHILD_IMMUTABILITY_FAILED", "CHILD_GEOMETRY_MUTATED", Path("_clones/TEAMB_CLONE__nand.gds"), "validate_and2_bundle"), lambda d: (_mutate_child_clone(d / "_clones/TEAMB_CLONE__nand.gds", (0.20, 0.20, 0.28, 0.28), layer=11), d / "_clones/TEAMB_CLONE__nand.gds")[1], "geometry"),
        (MutationCase("22_debug_label_in_clean", "label", "TOP_PIN_CONTRACT_FAILED", "DIRECT_TOP_LABEL_CONTRACT_FAILED", baseline_clean, "validate_and2_bundle"), lambda d: (add_label(d / "clean.gds", AND2_NAME, "DEBUG", (0.2, 1.0)), d / "clean.gds")[1], "label"),
        (MutationCase("23_deterministic_A_B_mutation", "determinism", "DETERMINISM_FAILED", "DETERMINISM_FAILED", Path("determinism.json"), "validate_and2_bundle"), lambda d: (_replace_json_value(d / "determinism.json", "byte_identical", False), d / "determinism.json")[1], "determinism"),
    ]
    rows = []
    validator = lambda work_dir: validate_and2_bundle(
        repo_root=Path(production_validator["repo_root"]),
        bundle_dir=work_dir,
        openyield_root=Path(production_validator["openyield_root"]),
        klayout_bin=Path(production_validator["klayout_bin"]),
        drc_deck=Path(production_validator["drc_deck"]),
    )
    for case, mutator, kind in cases:
        baseline_abs = base_dir / case.baseline_input_path
        baseline_sha = baseline_abs.exists() and __import__("hashlib").sha256(baseline_abs.read_bytes()).hexdigest() or ""
        if resume and baseline_sha:
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
                        "expected_rejection_family": case.expected_rejection_family,
                        "expected_rejection_code": cached["expected_rejection_code"],
                        "actual_rejection_family": rejection_family(cached["actual_rejection_code"]),
                        "actual_rejection_code": cached["actual_rejection_code"],
                        "family_matched": case.expected_rejection_family == rejection_family(cached["actual_rejection_code"]),
                        "code_matched": cached["expected_rejection_code"] == cached["actual_rejection_code"],
                        "rejected_as_expected": cached["rejected_as_expected"],
                        "all_actual_rejection_codes": cached["actual_rejection_code"],
                    }
                )
                continue
        if kind == "contract":
            row = run_contract_mutation(base_dir=base_dir, checkpoint_root=work_root, case_work_root=work_root, case=case, mutate_fn=mutator, validate_fn=validator)
        elif kind == "label":
            row = run_gds_label_mutation(base_dir=base_dir, checkpoint_root=work_root, case_work_root=work_root, case=case, mutate_fn=mutator, validate_fn=validator)
        elif kind == "hierarchy":
            row = run_hierarchy_mutation(base_dir=base_dir, checkpoint_root=work_root, case_work_root=work_root, case=case, mutate_fn=mutator, validate_fn=validator)
        elif kind == "determinism":
            row = run_determinism_mutation(base_dir=base_dir, checkpoint_root=work_root, case_work_root=work_root, case=case, mutate_fn=mutator, validate_fn=validator)
        elif kind == "short":
            row = run_gds_short_mutation(base_dir=base_dir, checkpoint_root=work_root, case_work_root=work_root, case=case, mutate_fn=mutator, validate_fn=validator)
        else:
            row = run_gds_geometry_mutation(base_dir=base_dir, checkpoint_root=work_root, case_work_root=work_root, case=case, mutate_fn=mutator, validate_fn=validator)
        rows.append(row)
        write_case_checkpoint(
            checkpoint_root=work_root,
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
    write_negative_test_matrix(output_dir / "AND2_negative_test_matrix.csv", rows)
    summary = write_negative_test_summary(output_dir / "AND2_negative_test_summary.json", rows)
    write_text(output_dir / "AND2_negative_test_execution.log", "\n".join(f"{row['test_id']} {row['actual_rejection_code']}" for row in rows))
    return {"rows": rows, "summary": summary}
