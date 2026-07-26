from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.inverter_chain_source_lock import MODULE_SPECS
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
from sram_layoutgen.openyield_adapter.teamb_composite_helper import read_json, write_json, write_text


def _top_label_origins(gds_path: Path, top_name: str) -> dict[str, tuple[float, float]]:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    return {str(label.text): (float(label.origin[0]), float(label.origin[1])) for label in top.labels}


def _top_label_bbox(gds_path: Path, top_name: str, label_name: str) -> dict[str, float]:
    x, y = _top_label_origins(gds_path, top_name)[label_name]
    return {"lx": round(x - 0.03, 6), "by": round(y - 0.03, 6), "rx": round(x + 0.03, 6), "uy": round(y + 0.03, 6)}


def _reorder_top_labels(gds_path: Path, top_name: str, ordered_names: list[str]) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    origin_by_name = {str(label.text): (float(label.origin[0]), float(label.origin[1]), int(label.layer), int(label.texttype)) for label in top.labels}
    victims = list(top.labels)
    if victims:
        top.remove(*victims)
    for name in ordered_names:
        x, y, layer, texttype = origin_by_name[name]
        top.add(gdstk.Label(name, (x, y), layer=layer, texttype=texttype))
    lib.write_gds(gds_path)


def _resolved_child_pin_bbox(bundle_dir: Path, module_name: str, child_index: int, pin_name: str) -> dict[str, float]:
    bindings = read_json(bundle_dir / "parameter_mapping.json")["child_bindings"]
    lib = gdstk.read_gds(bundle_dir / "clean.gds")
    top = next(cell for cell in lib.cells if cell.name == MODULE_SPECS[module_name]["top_cell_name"])
    ref = list(top.references)[child_index]
    pin_map = read_json(Path(bindings[child_index]["pin_map_path"]))
    bbox = pin_map[pin_name][0]
    dx = float(ref.origin[0])
    dy = float(ref.origin[1])
    return {
        "lx": round(float(bbox["lx"]) + dx, 6),
        "by": round(float(bbox["by"]) + dy, 6),
        "rx": round(float(bbox["rx"]) + dx, 6),
        "uy": round(float(bbox["uy"]) + dy, 6),
    }


def _move_label_to_bbox_center(gds_path: Path, top_name: str, label_name: str, bbox: dict[str, float]) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    target = next(label for label in top.labels if str(label.text) == label_name)
    target.origin = ((bbox["lx"] + bbox["rx"]) * 0.5, (bbox["by"] + bbox["uy"]) * 0.5)
    lib.write_gds(gds_path)


def _move_label_to_point(gds_path: Path, top_name: str, label_name: str, origin: tuple[float, float]) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    target = next(label for label in top.labels if str(label.text) == label_name)
    target.origin = origin
    lib.write_gds(gds_path)


def _bridge_bboxes(gds_path: Path, left_bbox: dict[str, float], right_bbox: dict[str, float], *, layer: int = 11, margin: float = 0.02) -> None:
    _add_rect(
        gds_path,
        (
            round(min(left_bbox["lx"], right_bbox["lx"]) - margin, 6),
            round(min(left_bbox["by"], right_bbox["by"]) - margin, 6),
            round(max(left_bbox["rx"], right_bbox["rx"]) + margin, 6),
            round(max(left_bbox["uy"], right_bbox["uy"]) + margin, 6),
        ),
        layer=layer,
    )


def _short_top_labels(gds_path: Path, top_name: str, left: str, right: str, *, layer: int = 11) -> None:
    origins = _top_label_origins(gds_path, top_name)
    ax, ay = origins[left]
    bx, by = origins[right]
    margin = 0.04
    _add_rect(
        gds_path,
        (
            round(min(ax, bx) - margin, 6),
            round(min(ay, by) - margin, 6),
            round(max(ax, bx) + margin, 6),
            round(max(ay, by) + margin, 6),
        ),
        layer=layer,
    )


def _replace_json_value(path: Path, key: str, value: Any) -> None:
    payload = read_json(path)
    payload[key] = value
    write_json(path, payload)


def _mutate_child_binding(path: Path, index: int, key: str, value: Any) -> None:
    payload = read_json(path)
    payload["child_bindings"][index][key] = value
    write_json(path, payload)


def _swap_binding_rows(path: Path, left_index: int, right_index: int) -> None:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = rows[0].keys()
    rows[left_index], rows[right_index] = rows[right_index], rows[left_index]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _remove_reference(gds_path: Path, match: str) -> None:
    lib = gdstk.read_gds(gds_path)
    top = lib.top_level()[0]
    victims = [ref for ref in top.references if match in (ref.cell_name or ref.cell.name)]
    if victims:
        top.remove(victims[-1])
    lib.write_gds(gds_path)


def _duplicate_reference(gds_path: Path) -> None:
    lib = gdstk.read_gds(gds_path)
    top = lib.top_level()[0]
    ref = top.references[0]
    top.add(gdstk.Reference(ref.cell, origin=(ref.origin[0] + 0.05, ref.origin[1] + 0.05)))
    lib.write_gds(gds_path)


def _add_rect(gds_path: Path, bbox: tuple[float, float, float, float], *, layer: int) -> None:
    lib = gdstk.read_gds(gds_path)
    top = lib.top_level()[0]
    top.add(gdstk.rectangle((bbox[0], bbox[1]), (bbox[2], bbox[3]), layer=layer, datatype=0))
    lib.write_gds(gds_path)


def _remove_polygons_in_bbox(gds_path: Path, bbox: tuple[float, float, float, float], *, layers: set[int] | None = None) -> None:
    lib = gdstk.read_gds(gds_path)
    for cell in lib.cells:
        victims = []
        for poly in cell.polygons:
            if layers and int(poly.layer) not in layers:
                continue
            pb = poly.bounding_box()
            if pb is None:
                continue
            if not (float(pb[1][0]) < bbox[0] or float(pb[0][0]) > bbox[2] or float(pb[1][1]) < bbox[1] or float(pb[0][1]) > bbox[3]):
                victims.append(poly)
        if victims:
            cell.remove(*victims)
    lib.write_gds(gds_path)


def _mutate_child_geometry(gds_path: Path, cell_name_fragment: str) -> None:
    lib = gdstk.read_gds(gds_path)
    target = next(cell for cell in lib.cells if cell_name_fragment in cell.name)
    target.add(gdstk.rectangle((0.2, 0.2), (0.28, 0.28), layer=11, datatype=0))
    lib.write_gds(gds_path)


def _internal_net_track_bbox(module_name: str, stage_index: int) -> tuple[float, float, float, float]:
    # Conservative bbox on the routed M2 corridor for the generated chain.
    if module_name in {"pdrive2_for_pre", "wl_pdrive"}:
        return (0.36, 0.98, 1.28, 1.16)
    boxes = [
        (0.36, 0.98, 1.55, 1.16),
        (1.25, 1.10, 3.20, 1.28),
        (3.05, 1.22, 6.40, 1.40),
    ]
    return boxes[stage_index]


def run_inverter_chain_negative_regressions(*, module_name: str, baseline_clean_gds: Path, production_validator: dict[str, Any], output_dir: Path, resume: bool = False) -> dict[str, Any]:
    base_dir = baseline_clean_gds.parent
    work_root = output_dir.parents[2] / "negative_test_work" / module_name
    if work_root.exists() and not resume:
        shutil.rmtree(work_root)
    work_root.mkdir(parents=True, exist_ok=True)
    internal_nets = MODULE_SPECS[module_name]["internal_nets"]
    child_variants = MODULE_SPECS[module_name]["child_variants"]
    top_name = MODULE_SPECS[module_name]["top_cell_name"]
    cases: list[tuple[MutationCase, Any, str]] = [
        (MutationCase("01_wrong_authority_commit", "contract", "SOURCE_LOCK_FAILED", "SOURCE_COMMIT_MISMATCH", Path("source_lock.json"), "validate_inverter_chain_bundle"), lambda d: (_replace_json_value(d / "source_lock.json", "authority_commit", "deadbeef"), d / "source_lock.json")[1], "contract"),
        (MutationCase("02_wrong_authority_blob", "contract", "SOURCE_LOCK_FAILED", "SOURCE_BLOB_MISMATCH", Path("source_lock.json"), "validate_inverter_chain_bundle"), lambda d: (_replace_json_value(d / "source_lock.json", "git_blob_sha", "deadbeef"), d / "source_lock.json")[1], "contract"),
        (MutationCase("03_wrong_child_SHA", "contract", "STRUCTURAL_CONTRACT_FAILED", "WRONG_PINV_VARIANT", Path("parameter_mapping.json"), "validate_inverter_chain_bundle"), lambda d: (_mutate_child_binding(d / "parameter_mapping.json", 0, "child_gds_sha256", "deadbeef"), d / "parameter_mapping.json")[1], "contract"),
        (MutationCase("04_wrong_child_variant", "contract", "STRUCTURAL_CONTRACT_FAILED", "WRONG_PINV_VARIANT", Path("parameter_mapping.json"), "validate_inverter_chain_bundle"), lambda d: (_mutate_child_binding(d / "parameter_mapping.json", len(child_variants) - 1, "resolved_physical_cell", "PINV_NW180_PW270_L50"), d / "parameter_mapping.json")[1], "contract"),
        (MutationCase("05_missing_child", "hierarchy", "STRUCTURAL_CONTRACT_FAILED", "CHILD_COUNT_MISMATCH", Path("clean.gds"), "validate_inverter_chain_bundle"), lambda d: (_remove_reference(d / "clean.gds", child_variants[-1]), d / "clean.gds")[1], "hierarchy"),
        (MutationCase("06_extra_child", "hierarchy", "STRUCTURAL_CONTRACT_FAILED", "CHILD_COUNT_MISMATCH", Path("clean.gds"), "validate_inverter_chain_bundle"), lambda d: (_duplicate_reference(d / "clean.gds"), d / "clean.gds")[1], "hierarchy"),
        (MutationCase("07_wrong_child_order", "contract", "STRUCTURAL_CONTRACT_FAILED", "STAGE_ORDER_MISMATCH", Path("instance_binding.csv"), "validate_inverter_chain_bundle"), lambda d: (_swap_binding_rows(d / "instance_binding.csv", 0, 1), d / "instance_binding.csv")[1], "contract"),
        (MutationCase("08_wrong_top_pin_order", "label", "TOP_PIN_CONTRACT_FAILED", "TOP_PIN_ORDER_MISMATCH", Path("clean.gds"), "validate_inverter_chain_bundle"), lambda d: (_reorder_top_labels(d / "clean.gds", top_name, ["VSS", "VDD", "A", "Z"]), d / "clean.gds")[1], "label"),
        (MutationCase("09_missing_A", "label", "TOP_PIN_CONTRACT_FAILED", "TOP_PIN_ORDER_MISMATCH", Path("clean.gds"), "validate_inverter_chain_bundle"), lambda d: (remove_label(d / "clean.gds", top_name, "A"), d / "clean.gds")[1], "label"),
        (MutationCase("10_extra_internal_top_label", "label", "TOP_PIN_CONTRACT_FAILED", "INTERNAL_NET_EXPOSED", Path("clean.gds"), "validate_inverter_chain_bundle"), lambda d: (add_label(d / "clean.gds", top_name, internal_nets[0], (1.0, 1.0)), d / "clean.gds")[1], "label"),
        (MutationCase("11_internal_stage_bypass", "short", "CONNECTIVITY_MISMATCH", "UNEXPECTED_INTERNAL_NET_MERGE", Path("clean.gds"), "validate_inverter_chain_bundle"), lambda d: (_bridge_bboxes(d / "clean.gds", _resolved_child_pin_bbox(d, module_name, 0, "A"), _resolved_child_pin_bbox(d, module_name, 0, "Z"), layer=11), d / "clean.gds")[1], "short"),
        (MutationCase("12_stage_disconnected", "geometry", "CONNECTIVITY_MISMATCH", "STAGE_DISCONNECTED", Path("clean.gds"), "validate_inverter_chain_bundle"), lambda d: (_remove_polygons_in_bbox(d / "clean.gds", _internal_net_track_bbox(module_name, 0), layers={13, 12}), d / "clean.gds")[1], "geometry"),
        (MutationCase("13_output_connected_to_wrong_stage", "label", "CONNECTIVITY_MISMATCH", "UNEXPECTED_INTERNAL_NET_MERGE", Path("clean.gds"), "validate_inverter_chain_bundle"), lambda d: (_move_label_to_bbox_center(d / "clean.gds", top_name, "Z", _resolved_child_pin_bbox(d, module_name, max(0, len(child_variants) - 2), "Z")), d / "clean.gds")[1], "label"),
        (MutationCase("14_A_Z_reversed", "short", "CONNECTIVITY_MISMATCH", "A_Z_REVERSED", Path("clean.gds"), "validate_inverter_chain_bundle"), lambda d: (_short_top_labels(d / "clean.gds", top_name, "A", "Z"), d / "clean.gds")[1], "short"),
        (MutationCase("15_internal_net_short_to_Z", "short", "CONNECTIVITY_MISMATCH", "UNEXPECTED_INTERNAL_NET_MERGE", Path("clean.gds"), "validate_inverter_chain_bundle"), lambda d: (_bridge_bboxes(d / "clean.gds", _resolved_child_pin_bbox(d, module_name, 0, "Z"), _resolved_child_pin_bbox(d, module_name, len(child_variants) - 1, "Z"), layer=11), d / "clean.gds")[1], "short"),
        (MutationCase("16_internal_net_short_to_VDD", "short", "POWER_SIGNAL_SHORT", "POWER_SIGNAL_SHORT", Path("clean.gds"), "validate_inverter_chain_bundle"), lambda d: (_bridge_bboxes(d / "clean.gds", _resolved_child_pin_bbox(d, module_name, 0, "Z"), _resolved_child_pin_bbox(d, module_name, 0, "VDD"), layer=11), d / "clean.gds")[1], "short"),
        (MutationCase("17_internal_net_short_to_VSS", "short", "POWER_SIGNAL_SHORT", "POWER_SIGNAL_SHORT", Path("clean.gds"), "validate_inverter_chain_bundle"), lambda d: (_bridge_bboxes(d / "clean.gds", _resolved_child_pin_bbox(d, module_name, 0, "Z"), _resolved_child_pin_bbox(d, module_name, 0, "VSS"), layer=11), d / "clean.gds")[1], "short"),
        (MutationCase("18_missing_Via1", "geometry", "CONNECTIVITY_MISMATCH", "STAGE_DISCONNECTED", Path("clean.gds"), "validate_inverter_chain_bundle"), lambda d: (_remove_polygons_in_bbox(d / "clean.gds", _internal_net_track_bbox(module_name, 0), layers={12}), d / "clean.gds")[1], "geometry"),
        (MutationCase("19_foreign_net_contact", "short", "CONNECTIVITY_MISMATCH", "UNEXPECTED_INTERNAL_NET_MERGE", Path("clean.gds"), "validate_inverter_chain_bundle"), lambda d: (_bridge_bboxes(d / "clean.gds", _top_label_bbox(d / "clean.gds", top_name, "A"), _resolved_child_pin_bbox(d, module_name, len(child_variants) - 1, "A"), layer=11), d / "clean.gds")[1], "short"),
        (MutationCase("20_child_geometry_mutation", "geometry", "CHILD_IMMUTABILITY_FAILED", "CHILD_GEOMETRY_MUTATED", Path("clean.gds"), "validate_inverter_chain_bundle"), lambda d: (_mutate_child_geometry(d / "clean.gds", child_variants[0]), d / "clean.gds")[1], "geometry"),
        (MutationCase("21_debug_label", "label", "TOP_PIN_CONTRACT_FAILED", "TOP_PIN_ORDER_MISMATCH", Path("clean.gds"), "validate_inverter_chain_bundle"), lambda d: (add_label(d / "clean.gds", top_name, "DEBUG", (0.2, 1.0)), d / "clean.gds")[1], "label"),
        (MutationCase("22_off_grid_route", "contract", "GRID_FAILED", "OFF_GRID_GEOMETRY", Path("layout_quality_metrics.json"), "validate_inverter_chain_bundle"), lambda d: (_replace_json_value(d / "layout_quality_metrics.json", "off_grid_count", 1), d / "layout_quality_metrics.json")[1], "contract"),
        (MutationCase("23_determinism_mutation", "determinism", "DETERMINISM_FAILED", "DETERMINISM_FAILED", Path("determinism.json"), "validate_inverter_chain_bundle"), lambda d: (_replace_json_value(d / "determinism.json", "byte_identical", False), d / "determinism.json")[1], "determinism"),
    ]
    if module_name == "pdrive":
        cases.extend(
            [
                (MutationCase("24_stage2_stage3_swapped", "contract", "STRUCTURAL_CONTRACT_FAILED", "STAGE_ORDER_MISMATCH", Path("instance_binding.csv"), "validate_inverter_chain_bundle"), lambda d: (_swap_binding_rows(d / "instance_binding.csv", 1, 2), d / "instance_binding.csv")[1], "contract"),
                (MutationCase("25_stage3_stage4_swapped", "contract", "STRUCTURAL_CONTRACT_FAILED", "STAGE_ORDER_MISMATCH", Path("instance_binding.csv"), "validate_inverter_chain_bundle"), lambda d: (_swap_binding_rows(d / "instance_binding.csv", 2, 3), d / "instance_binding.csv")[1], "contract"),
                (MutationCase("26_wrong_large_PINV_binding", "contract", "STRUCTURAL_CONTRACT_FAILED", "WRONG_PINV_VARIANT", Path("parameter_mapping.json"), "validate_inverter_chain_bundle"), lambda d: (_mutate_child_binding(d / "parameter_mapping.json", 3, "resolved_physical_cell", "PINV_NW910_PW2430_L50"), d / "parameter_mapping.json")[1], "contract"),
                (MutationCase("27_zb1_zb2_merged", "short", "CONNECTIVITY_MISMATCH", "UNEXPECTED_INTERNAL_NET_MERGE", Path("clean.gds"), "validate_inverter_chain_bundle"), lambda d: (_bridge_bboxes(d / "clean.gds", _resolved_child_pin_bbox(d, module_name, 1, "A"), _resolved_child_pin_bbox(d, module_name, 1, "Z"), layer=11), d / "clean.gds")[1], "short"),
                (MutationCase("28_zb2_zb3_merged", "short", "CONNECTIVITY_MISMATCH", "UNEXPECTED_INTERNAL_NET_MERGE", Path("clean.gds"), "validate_inverter_chain_bundle"), lambda d: (_bridge_bboxes(d / "clean.gds", _resolved_child_pin_bbox(d, module_name, 2, "A"), _resolved_child_pin_bbox(d, module_name, 2, "Z"), layer=11), d / "clean.gds")[1], "short"),
            ]
        )
    rows = []
    validator = lambda work_dir: production_validator["validate_fn"](repo_root=production_validator["repo_root"], bundle_dir=work_dir, module_name=module_name, openyield_root=production_validator["openyield_root"], klayout_bin=production_validator["klayout_bin"], drc_deck=production_validator["drc_deck"])
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
                        "actual_rejection_family": __import__("sram_layoutgen.openyield_adapter.rejection_code_registry", fromlist=["rejection_family"]).rejection_family(cached["actual_rejection_code"]),
                        "actual_rejection_code": cached["actual_rejection_code"],
                        "family_matched": True,
                        "code_matched": cached["expected_rejection_code"] == cached["actual_rejection_code"],
                        "rejected_as_expected": cached["rejected_as_expected"],
                        "all_actual_rejection_codes": cached["actual_rejection_code"],
                    }
                )
                continue
        if kind == "contract":
            row = run_contract_mutation(base_dir=base_dir, work_root=work_root, case=case, mutate_fn=mutator, validate_fn=validator)
        elif kind == "label":
            row = run_gds_label_mutation(base_dir=base_dir, work_root=work_root, case=case, mutate_fn=mutator, validate_fn=validator)
        elif kind == "hierarchy":
            row = run_hierarchy_mutation(base_dir=base_dir, work_root=work_root, case=case, mutate_fn=mutator, validate_fn=validator)
        elif kind == "determinism":
            row = run_determinism_mutation(base_dir=base_dir, work_root=work_root, case=case, mutate_fn=mutator, validate_fn=validator)
        elif kind == "short":
            row = run_gds_short_mutation(base_dir=base_dir, work_root=work_root, case=case, mutate_fn=mutator, validate_fn=validator)
        else:
            row = run_gds_geometry_mutation(base_dir=base_dir, work_root=work_root, case=case, mutate_fn=mutator, validate_fn=validator)
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
    matrix_name = f"{module_name}_negative_test_matrix.csv"
    summary_name = f"{module_name}_negative_test_summary.json"
    write_negative_test_matrix(output_dir / matrix_name, rows)
    summary = write_negative_test_summary(output_dir / summary_name, rows)
    write_text(output_dir / f"{module_name}_negative_test_execution.log", "\n".join(f"{row['test_id']} {row['actual_rejection_code']}" for row in rows))
    return {"rows": rows, "summary": summary}
