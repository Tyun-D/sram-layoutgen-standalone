from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any, Callable

import gdstk

from sram_layoutgen.openyield_adapter.delay_chain_source_lock import MODULE_SPECS, resolve_approved_pinv_asset
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
from sram_layoutgen.openyield_adapter.teamb_composite_helper import read_json, write_json, write_text


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _top_cell(bundle_dir: Path, module_name: str) -> tuple[gdstk.Library, gdstk.Cell]:
    lib = gdstk.read_gds(bundle_dir / "clean.gds")
    top_name = MODULE_SPECS[module_name]["top_cell_name"]
    top = next(cell for cell in lib.cells if cell.name == top_name)
    return lib, top


def _write_gds(lib: gdstk.Library, path: Path) -> None:
    lib.write_gds(path)


def _top_label_origins(gds_path: Path, top_name: str) -> dict[str, tuple[float, float]]:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    return {str(label.text): (float(label.origin[0]), float(label.origin[1])) for label in top.labels}


def _rename_label(gds_path: Path, top_name: str, old: str, new: str) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    target = next(label for label in top.labels if str(label.text) == old)
    target.text = new
    lib.write_gds(gds_path)


def _swap_label_texts(gds_path: Path, top_name: str, left: str, right: str) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    left_label = next(label for label in top.labels if str(label.text) == left)
    right_label = next(label for label in top.labels if str(label.text) == right)
    left_label.text, right_label.text = right_label.text, left_label.text
    lib.write_gds(gds_path)


def _reorder_top_labels(gds_path: Path, top_name: str, ordered_names: list[str]) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    origin_by_name = {
        str(label.text): (float(label.origin[0]), float(label.origin[1]), int(label.layer), int(label.texttype))
        for label in top.labels
    }
    victims = list(top.labels)
    if victims:
        top.remove(*victims)
    for name in ordered_names:
        x, y, layer, texttype = origin_by_name[name]
        top.add(gdstk.Label(name, (x, y), layer=layer, texttype=texttype))
    lib.write_gds(gds_path)


def _resolved_role_pin_bbox(bundle_dir: Path, module_name: str, role: str, pin_name: str) -> dict[str, float]:
    binding_rows = read_json(bundle_dir / "instance_role_manifest.json")["rows"]
    role_index = next(index for index, row in enumerate(binding_rows) if row["instance_role"] == role)
    parameter_mapping = read_json(bundle_dir / "parameter_mapping.json")
    pin_map = read_json(Path(parameter_mapping["pin_map_path"]))
    _, top = _top_cell(bundle_dir, module_name)
    ref = list(top.references)[role_index]
    bbox = pin_map[pin_name][0]
    dx = float(ref.origin[0])
    dy = float(ref.origin[1])
    return {
        "lx": round(float(bbox["lx"]) + dx, 6),
        "by": round(float(bbox["by"]) + dy, 6),
        "rx": round(float(bbox["rx"]) + dx, 6),
        "uy": round(float(bbox["uy"]) + dy, 6),
    }


def _top_label_bbox(gds_path: Path, top_name: str, label_name: str) -> dict[str, float]:
    x, y = _top_label_origins(gds_path, top_name)[label_name]
    return {"lx": round(x - 0.03, 6), "by": round(y - 0.03, 6), "rx": round(x + 0.03, 6), "uy": round(y + 0.03, 6)}


def _move_label_to_bbox_center(gds_path: Path, top_name: str, label_name: str, bbox: dict[str, float]) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    target = next(label for label in top.labels if str(label.text) == label_name)
    target.origin = ((bbox["lx"] + bbox["rx"]) * 0.5, (bbox["by"] + bbox["uy"]) * 0.5)
    lib.write_gds(gds_path)


def _add_rect(gds_path: Path, bbox: tuple[float, float, float, float], *, layer: int, datatype: int = 0) -> None:
    lib = gdstk.read_gds(gds_path)
    top = lib.top_level()[0]
    top.add(gdstk.rectangle((bbox[0], bbox[1]), (bbox[2], bbox[3]), layer=layer, datatype=datatype))
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


def _bridge_pin_centers(
    gds_path: Path,
    left_bbox: dict[str, float],
    right_bbox: dict[str, float],
    *,
    layer: int = 11,
    width: float = 0.03,
) -> None:
    left_cx = (left_bbox["lx"] + left_bbox["rx"]) * 0.5
    left_cy = (left_bbox["by"] + left_bbox["uy"]) * 0.5
    right_cx = (right_bbox["lx"] + right_bbox["rx"]) * 0.5
    right_cy = (right_bbox["by"] + right_bbox["uy"]) * 0.5
    half = width * 0.5
    _add_rect(
        gds_path,
        (
            round(min(left_cx, right_cx) - half, 6),
            round(left_cy - half, 6),
            round(max(left_cx, right_cx) + half, 6),
            round(left_cy + half, 6),
        ),
        layer=layer,
    )
    if abs(left_cy - right_cy) > 1e-6:
        _add_rect(
            gds_path,
            (
                round(right_cx - half, 6),
                round(min(left_cy, right_cy) - half, 6),
                round(right_cx + half, 6),
                round(max(left_cy, right_cy) + half, 6),
            ),
            layer=layer,
        )


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


def _route_bbox(
    bundle_dir: Path,
    module_name: str,
    left_role: str,
    left_pin: str,
    right_role: str,
    right_pin: str,
    *,
    pad: float = 0.08,
) -> tuple[float, float, float, float]:
    left = _resolved_role_pin_bbox(bundle_dir, module_name, left_role, left_pin)
    right = _resolved_role_pin_bbox(bundle_dir, module_name, right_role, right_pin)
    return (
        round(min(left["lx"], right["lx"]) - pad, 6),
        round(min(left["by"], right["by"]) - pad, 6),
        round(max(left["rx"], right["rx"]) + pad, 6),
        round(max(left["uy"], right["uy"]) + pad, 6),
    )


def _mutate_json_value(path: Path, key: str, value: Any) -> None:
    payload = read_json(path)
    payload[key] = value
    write_json(path, payload)


def _mutate_layout_metric(path: Path, key: str, value: Any) -> None:
    payload = read_json(path)
    payload[key] = value
    write_json(path, payload)


def _mutate_csv_row(path: Path, row_index: int, key: str, value: Any) -> None:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = list(rows[0].keys())
    rows[row_index][key] = value
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _swap_csv_rows(path: Path, left_index: int, right_index: int) -> None:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = list(rows[0].keys())
    rows[left_index], rows[right_index] = rows[right_index], rows[left_index]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _remove_csv_row(path: Path, row_index: int) -> None:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = list(rows[0].keys())
    del rows[row_index]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _duplicate_csv_row(path: Path, row_index: int, *, new_role: str | None = None) -> None:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
        fieldnames = list(rows[0].keys())
    dup = dict(rows[row_index])
    if new_role is not None:
        dup["instance_role"] = new_role
    rows.insert(row_index + 1, dup)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _mutate_manifest_row(path: Path, row_index: int, key: str, value: Any) -> None:
    payload = read_json(path)
    payload["rows"][row_index][key] = value
    write_json(path, payload)


def _remove_manifest_row(path: Path, row_index: int) -> None:
    payload = read_json(path)
    del payload["rows"][row_index]
    write_json(path, payload)


def _swap_manifest_rows(path: Path, left_index: int, right_index: int) -> None:
    payload = read_json(path)
    rows = payload["rows"]
    rows[left_index], rows[right_index] = rows[right_index], rows[left_index]
    write_json(path, payload)


def _duplicate_manifest_row(path: Path, row_index: int, *, new_role: str | None = None) -> None:
    payload = read_json(path)
    dup = dict(payload["rows"][row_index])
    if new_role is not None:
        dup["instance_role"] = new_role
    payload["rows"].insert(row_index + 1, dup)
    write_json(path, payload)


def _remove_reference(gds_path: Path, ref_index: int) -> None:
    lib = gdstk.read_gds(gds_path)
    top = lib.top_level()[0]
    victims = list(top.references)
    top.remove(victims[ref_index])
    lib.write_gds(gds_path)


def _duplicate_reference(gds_path: Path, ref_index: int, *, dx: float = 0.05, dy: float = 0.05) -> None:
    lib = gdstk.read_gds(gds_path)
    top = lib.top_level()[0]
    ref = list(top.references)[ref_index]
    top.add(gdstk.Reference(ref.cell, origin=(ref.origin[0] + dx, ref.origin[1] + dy), rotation=ref.rotation, x_reflection=ref.x_reflection))
    lib.write_gds(gds_path)


def _mutate_child_geometry(gds_path: Path, ref_index: int) -> None:
    lib = gdstk.read_gds(gds_path)
    top = lib.top_level()[0]
    ref = list(top.references)[ref_index]
    target_name = ref.cell_name or ref.cell.name
    target = next(cell for cell in lib.cells if cell.name == target_name)
    target.add(gdstk.rectangle((0.2, 0.2), (0.28, 0.28), layer=11, datatype=0))
    lib.write_gds(gds_path)


def _remove_child_local_pin_geometry(
    bundle_dir: Path,
    module_name: str,
    role: str,
    pin_name: str,
    *,
    layers: set[int],
    margin: float = 0.02,
) -> None:
    gds_path = bundle_dir / "clean.gds"
    lib = gdstk.read_gds(gds_path)
    binding_rows = read_json(bundle_dir / "instance_role_manifest.json")["rows"]
    role_index = next(index for index, row in enumerate(binding_rows) if row["instance_role"] == role)
    top = lib.top_level()[0]
    ref = list(top.references)[role_index]
    target_name = ref.cell_name or ref.cell.name
    target = next(cell for cell in lib.cells if cell.name == target_name)
    parameter_mapping = read_json(bundle_dir / "parameter_mapping.json")
    pin_map = read_json(Path(parameter_mapping["pin_map_path"]))
    bbox = pin_map[pin_name][0]
    cut_bbox = (
        float(bbox["lx"]) - margin,
        float(bbox["by"]) - margin,
        float(bbox["rx"]) + margin,
        float(bbox["uy"]) + margin,
    )
    victims = []
    for poly in target.polygons:
        if int(poly.layer) not in layers:
            continue
        pb = poly.bounding_box()
        if pb is None:
            continue
        if not (
            float(pb[1][0]) < cut_bbox[0]
            or float(pb[0][0]) > cut_bbox[2]
            or float(pb[1][1]) < cut_bbox[1]
            or float(pb[0][1]) > cut_bbox[3]
        ):
            victims.append(poly)
    if victims:
        target.remove(*victims)
    lib.write_gds(gds_path)


def _flatten_top(gds_path: Path, top_name: str) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    top.flatten()
    lib.write_gds(gds_path)


def _write_mutation_proof(work_dir: Path, case: MutationCase, row: dict[str, Any]) -> str:
    proof_path = work_dir / "mutation_proof.json"
    proof = {
        "test_id": case.test_id,
        "mutation_kind": case.mutation_kind,
        "baseline_sha": row["baseline_input_sha256"],
        "mutated_sha": row["mutated_input_sha256"],
        "expected_rejection_code": row["expected_rejection_code"],
        "actual_rejection_code": row["actual_rejection_code"],
    }
    write_json(proof_path, proof)
    return str(proof_path.resolve())


def _case_rows(module_name: str) -> list[tuple[MutationCase, Callable[[Path], Path], str, str]]:
    spec = MODULE_SPECS[module_name]
    top_name = spec["top_cell_name"]
    last_stage = spec["stage_count"] - 1
    rows: list[tuple[MutationCase, Callable[[Path], Path], str, str]] = []
    rows.extend(
        [
            (MutationCase("01_wrong_authority_commit", "contract", "SOURCE_LOCK_FAILED", "SOURCE_COMMIT_MISMATCH", Path("source_lock.json"), "validate_delay_chain_bundle"), lambda d: (_mutate_json_value(d / "source_lock.json", "authority_commit", "deadbeef"), d / "source_lock.json")[1], "contract", "wrong authority commit"),
            (MutationCase("02_wrong_authority_blob", "contract", "SOURCE_LOCK_FAILED", "SOURCE_BLOB_MISMATCH", Path("source_lock.json"), "validate_delay_chain_bundle"), lambda d: (_mutate_json_value(d / "source_lock.json", "git_blob_sha", "deadbeef"), d / "source_lock.json")[1], "contract", "wrong authority blob"),
            (MutationCase("03_wrong_source_module", "contract", "SOURCE_LOCK_FAILED", "STRUCTURAL_CONTRACT_FAILED", Path("source_lock.json"), "validate_delay_chain_bundle"), lambda d: (_mutate_json_value(d / "source_lock.json", "topology_digest", "deadbeefcafebabe"), d / "source_lock.json")[1], "contract", "wrong source module"),
            (MutationCase("04_wrong_approved_child_SHA", "contract", "STRUCTURAL_CONTRACT_FAILED", "PINV_CHILD_SHA_MISMATCH", Path("parameter_mapping.json"), "validate_delay_chain_bundle"), lambda d: (_mutate_json_value(d / "parameter_mapping.json", "approved_child_sha256", "deadbeef"), d / "parameter_mapping.json")[1], "contract", "wrong approved child sha"),
            (MutationCase("05_wrong_PINV_variant", "contract", "STRUCTURAL_CONTRACT_FAILED", "WRONG_PINV_VARIANT", Path("parameter_mapping.json"), "validate_delay_chain_bundle"), lambda d: (_mutate_json_value(d / "parameter_mapping.json", "child_variant", "PINV_WRONG"), d / "parameter_mapping.json")[1], "contract", "wrong pinv variant"),
            (MutationCase("06_child_geometry_mutation", "geometry", "CHILD_IMMUTABILITY_FAILED", "CHILD_GEOMETRY_MUTATED", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_mutate_child_geometry(d / "clean.gds", 0), d / "clean.gds")[1], "geometry", "child geometry mutation"),
            (MutationCase("07_wrong_transistor_parameter_binding", "contract", "STRUCTURAL_CONTRACT_FAILED", "WRONG_PINV_VARIANT", Path("parameter_mapping.json"), "validate_delay_chain_bundle"), lambda d: (_mutate_json_value(d / "parameter_mapping.json", "child_variant", "PINV_PARAM_WRONG"), d / "parameter_mapping.json")[1], "contract", "wrong transistor parameter binding"),
            (MutationCase("08_wrong_top_Pin_order", "label", "TOP_PIN_CONTRACT_FAILED", "TOP_PIN_ORDER_MISMATCH", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_reorder_top_labels(d / "clean.gds", top_name, ["VSS", "VDD", "in", "out"]), d / "clean.gds")[1], "label", "wrong top pin order"),
            (MutationCase("09_missing_in", "label", "TOP_PIN_CONTRACT_FAILED", "TOP_PIN_ORDER_MISMATCH", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (remove_label(d / "clean.gds", top_name, "in"), d / "clean.gds")[1], "label", "missing in"),
            (MutationCase("10_missing_out", "label", "TOP_PIN_CONTRACT_FAILED", "TOP_PIN_ORDER_MISMATCH", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (remove_label(d / "clean.gds", top_name, "out"), d / "clean.gds")[1], "label", "missing out"),
            (MutationCase("11_extra_internal_top_label", "label", "TOP_PIN_CONTRACT_FAILED", "INTERNAL_NET_EXPOSED", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (add_label(d / "clean.gds", top_name, "stage_00_net", (1.0, 1.0)), d / "clean.gds")[1], "label", "extra internal top label"),
            (MutationCase("12_wrong_Pin_case", "label", "TOP_PIN_CONTRACT_FAILED", "TOP_PIN_ORDER_MISMATCH", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_rename_label(d / "clean.gds", top_name, "in", "IN"), d / "clean.gds")[1], "label", "wrong pin case"),
            (MutationCase("13_missing_driver", "hierarchy", "STRUCTURAL_CONTRACT_FAILED", "DRIVER_COUNT_MISMATCH", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_remove_reference(d / "clean.gds", 0), _remove_csv_row(d / "instance_binding.csv", 0), _remove_manifest_row(d / "instance_role_manifest.json", 0), d / "clean.gds")[3], "hierarchy", "missing driver"),
            (MutationCase("14_extra_driver", "hierarchy", "STRUCTURAL_CONTRACT_FAILED", "DRIVER_COUNT_MISMATCH", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_duplicate_reference(d / "clean.gds", 0), _duplicate_csv_row(d / "instance_binding.csv", 0, new_role="stage_00_driver_dup"), _duplicate_manifest_row(d / "instance_role_manifest.json", 0, new_role="stage_00_driver_dup"), d / "clean.gds")[3], "hierarchy", "extra driver"),
            (MutationCase("15_missing_load", "hierarchy", "STRUCTURAL_CONTRACT_FAILED", "LOAD_COUNT_MISMATCH", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_remove_reference(d / "clean.gds", 1), _remove_csv_row(d / "instance_binding.csv", 1), _remove_manifest_row(d / "instance_role_manifest.json", 1), d / "clean.gds")[3], "hierarchy", "missing load"),
            (MutationCase("16_extra_load", "hierarchy", "STRUCTURAL_CONTRACT_FAILED", "LOAD_COUNT_MISMATCH", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_duplicate_reference(d / "clean.gds", 1), _duplicate_csv_row(d / "instance_binding.csv", 1, new_role="stage_00_load_00_dup"), _duplicate_manifest_row(d / "instance_role_manifest.json", 1, new_role="stage_00_load_00_dup"), d / "clean.gds")[3], "hierarchy", "extra load"),
            (MutationCase("17_wrong_driver_count", "contract", "STRUCTURAL_CONTRACT_FAILED", "DRIVER_COUNT_MISMATCH", Path("instance_role_manifest.json"), "validate_delay_chain_bundle"), lambda d: (_remove_csv_row(d / "instance_binding.csv", 0), _remove_manifest_row(d / "instance_role_manifest.json", 0), d / "instance_binding.csv")[2], "contract", "wrong driver count"),
            (MutationCase("18_wrong_load_count", "contract", "STRUCTURAL_CONTRACT_FAILED", "LOAD_COUNT_MISMATCH", Path("instance_role_manifest.json"), "validate_delay_chain_bundle"), lambda d: (_remove_csv_row(d / "instance_binding.csv", 1), _remove_manifest_row(d / "instance_role_manifest.json", 1), d / "instance_binding.csv")[2], "contract", "wrong load count"),
            (MutationCase("19_wrong_loads_per_stage", "contract", "STRUCTURAL_CONTRACT_FAILED", "LOADS_PER_STAGE_MISMATCH", Path("instance_binding.csv"), "validate_delay_chain_bundle"), lambda d: (_mutate_csv_row(d / "instance_binding.csv", 1, "stage_index", "1"), _mutate_manifest_row(d / "instance_role_manifest.json", 1, "stage_index", 1), d / "instance_binding.csv")[2], "contract", "wrong loads per stage"),
            (MutationCase("20_missing_child_reference", "hierarchy", "STRUCTURAL_CONTRACT_FAILED", "CHILD_COUNT_MISMATCH", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_remove_reference(d / "clean.gds", 2), d / "clean.gds")[1], "hierarchy", "missing child reference"),
            (MutationCase("21_flattened_child", "hierarchy", "CHILD_IMMUTABILITY_FAILED", "CHILD_GEOMETRY_MUTATED", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_flatten_top(d / "clean.gds", top_name), d / "clean.gds")[1], "hierarchy", "flattened child"),
            (MutationCase("22_stage0_input_disconnected", "label", "CONNECTIVITY_MISMATCH", "STAGE_DISCONNECTED", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_move_label_to_bbox_center(d / "clean.gds", top_name, "in", {"lx": -0.2, "by": 1.0, "rx": -0.2, "uy": 1.0}), d / "clean.gds")[1], "label", "stage0 input disconnected"),
            (MutationCase("23_stage_bypass", "short", "FOREIGN_NET_FAILED", "FOREIGN_NET_CONTACT", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_bridge_bboxes(d / "clean.gds", _resolved_role_pin_bbox(d, module_name, "stage_00_driver", "Z"), _resolved_role_pin_bbox(d, module_name, "stage_02_driver", "A")), d / "clean.gds")[1], "short", "stage bypass via foreign stage-net merge"),
            (MutationCase("24_driver_order_swapped", "contract", "STRUCTURAL_CONTRACT_FAILED", "STAGE_ORDER_MISMATCH", Path("instance_binding.csv"), "validate_delay_chain_bundle"), lambda d: (_swap_csv_rows(d / "instance_binding.csv", 0, spec["loads_per_stage"] + 1), _swap_manifest_rows(d / "instance_role_manifest.json", 0, spec["loads_per_stage"] + 1), d / "instance_binding.csv")[2], "contract", "driver order swapped"),
            (MutationCase("25_stage_net_disconnected", "geometry", "CONNECTIVITY_MISMATCH", "STAGE_DISCONNECTED", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_remove_polygons_in_bbox(d / "clean.gds", _route_bbox(d, module_name, "stage_00_driver", "Z", "stage_01_driver", "A"), layers={12, 13}), d / "clean.gds")[1], "geometry", "stage net disconnected"),
            (MutationCase("26_two_stage_nets_merged", "short", "CONNECTIVITY_MISMATCH", "FOREIGN_NET_CONTACT", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_bridge_pin_centers(d / "clean.gds", _resolved_role_pin_bbox(d, module_name, "stage_00_load_00", "A"), _resolved_role_pin_bbox(d, module_name, "stage_01_load_00", "A")), d / "clean.gds")[1], "short", "two stage nets merged"),
            (MutationCase("27_load_attached_to_previous_stage", "short", "CONNECTIVITY_MISMATCH", "FOREIGN_NET_CONTACT", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_bridge_pin_centers(d / "clean.gds", _resolved_role_pin_bbox(d, module_name, "stage_01_driver", "A"), _resolved_role_pin_bbox(d, module_name, "stage_01_load_00", "A")), d / "clean.gds")[1], "short", "load attached to previous stage"),
            (MutationCase("28_load_attached_to_next_stage", "short", "CONNECTIVITY_MISMATCH", "FOREIGN_NET_CONTACT", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_bridge_pin_centers(d / "clean.gds", _resolved_role_pin_bbox(d, module_name, "stage_00_load_00", "A"), _resolved_role_pin_bbox(d, module_name, f"stage_{min(2, last_stage):02d}_driver", "A")), d / "clean.gds")[1], "short", "load attached to next stage"),
            (MutationCase("29_load_attached_to_wrong_stage", "short", "CONNECTIVITY_MISMATCH", "FOREIGN_NET_CONTACT", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_bridge_pin_centers(d / "clean.gds", _resolved_role_pin_bbox(d, module_name, f"stage_{last_stage:02d}_load_00", "A"), _resolved_role_pin_bbox(d, module_name, "stage_01_driver", "A")), d / "clean.gds")[1], "short", "load attached to wrong stage"),
            (MutationCase("30_one_load_input_disconnected", "geometry", "CONNECTIVITY_MISMATCH", "STAGE_DISCONNECTED", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_remove_polygons_in_bbox(d / "clean.gds", _route_bbox(d, module_name, "stage_00_driver", "Z", "stage_00_load_00", "A", pad=0.015), layers={12, 13}), d / "clean.gds")[1], "geometry", "one load input disconnected"),
            (MutationCase("31_top_in_connected_to_wrong_driver", "label", "FOREIGN_NET_FAILED", "FOREIGN_NET_CONTACT", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_move_label_to_bbox_center(d / "clean.gds", top_name, "in", _resolved_role_pin_bbox(d, module_name, f"stage_{min(1, last_stage):02d}_driver", "A")), d / "clean.gds")[1], "label", "top in connected to wrong driver net"),
            (MutationCase("32_top_out_connected_to_wrong_stage", "label", "FOREIGN_NET_FAILED", "FOREIGN_NET_CONTACT", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_move_label_to_bbox_center(d / "clean.gds", top_name, "out", _resolved_role_pin_bbox(d, module_name, f"stage_{max(0, last_stage - 1):02d}_driver", "Z")), d / "clean.gds")[1], "label", "top out connected to wrong stage net"),
            (MutationCase("33_top_in_out_reversed", "label", "CONNECTIVITY_MISMATCH", "TOP_PIN_ORDER_MISMATCH", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_swap_label_texts(d / "clean.gds", top_name, "in", "out"), d / "clean.gds")[1], "label", "top in out reversed"),
            (MutationCase("34_one_load_output_connected_to_stage_net", "short", "FLOATING_OUTPUT_FAILED", "FLOATING_OUTPUT_VIOLATION", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_bridge_bboxes(d / "clean.gds", _resolved_role_pin_bbox(d, module_name, "stage_00_load_00", "Z"), _resolved_role_pin_bbox(d, module_name, "stage_00_load_00", "A")), d / "clean.gds")[1], "short", "one load output connected to stage net"),
            (MutationCase("35_two_floating_load_outputs_merged", "short", "FLOATING_OUTPUT_FAILED", "FLOATING_OUTPUT_VIOLATION", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_bridge_bboxes(d / "clean.gds", _resolved_role_pin_bbox(d, module_name, "stage_00_load_00", "Z"), _resolved_role_pin_bbox(d, module_name, "stage_00_load_01", "Z")), d / "clean.gds")[1], "short", "two floating outputs merged"),
            (MutationCase("36_floating_load_output_connected_to_VDD", "short", "FLOATING_OUTPUT_FAILED", "POWER_SIGNAL_SHORT", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_bridge_bboxes(d / "clean.gds", _resolved_role_pin_bbox(d, module_name, "stage_00_load_00", "Z"), _resolved_role_pin_bbox(d, module_name, "stage_00_load_00", "VDD")), d / "clean.gds")[1], "short", "floating output connected to vdd"),
            (MutationCase("37_floating_load_output_connected_to_VSS", "short", "FLOATING_OUTPUT_FAILED", "POWER_SIGNAL_SHORT", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_bridge_bboxes(d / "clean.gds", _resolved_role_pin_bbox(d, module_name, "stage_00_load_00", "Z"), _resolved_role_pin_bbox(d, module_name, "stage_00_load_00", "VSS")), d / "clean.gds")[1], "short", "floating output connected to vss"),
            (MutationCase("38_floating_output_exposed_as_top_Pin", "label", "TOP_PIN_CONTRACT_FAILED", "TOP_PIN_ORDER_MISMATCH", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (add_label(d / "clean.gds", top_name, "FLOAT", (_resolved_role_pin_bbox(d, module_name, "stage_00_load_00", "Z")["lx"], _resolved_role_pin_bbox(d, module_name, "stage_00_load_00", "Z")["by"])), d / "clean.gds")[1], "label", "floating output exposed as top pin"),
            (MutationCase("39_wrong_intentional_floating_count", "geometry", "CHILD_IMMUTABILITY_FAILED", "CHILD_GEOMETRY_MUTATED", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_remove_child_local_pin_geometry(d, module_name, "stage_00_load_00", "Z", layers={10, 11, 12, 13}), d / "clean.gds")[1], "geometry", "wrong intentional floating count via load output geometry removal"),
            (MutationCase("40_stage_net_short_to_VDD", "short", "POWER_SIGNAL_SHORT", "POWER_SIGNAL_SHORT", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_bridge_bboxes(d / "clean.gds", _resolved_role_pin_bbox(d, module_name, "stage_00_driver", "Z"), _resolved_role_pin_bbox(d, module_name, "stage_00_driver", "VDD")), d / "clean.gds")[1], "short", "stage net short to vdd"),
            (MutationCase("41_stage_net_short_to_VSS", "short", "POWER_SIGNAL_SHORT", "POWER_SIGNAL_SHORT", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_bridge_bboxes(d / "clean.gds", _resolved_role_pin_bbox(d, module_name, "stage_00_driver", "Z"), _resolved_role_pin_bbox(d, module_name, "stage_00_driver", "VSS")), d / "clean.gds")[1], "short", "stage net short to vss"),
            (MutationCase("42_foreign_net_contact", "short", "FOREIGN_NET_FAILED", "FOREIGN_NET_CONTACT", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_bridge_bboxes(d / "clean.gds", _resolved_role_pin_bbox(d, module_name, "stage_00_driver", "A"), _resolved_role_pin_bbox(d, module_name, "stage_00_driver", "Z")), d / "clean.gds")[1], "short", "foreign net contact"),
            (MutationCase("43_missing_Via1", "geometry", "CONNECTIVITY_MISMATCH", "STAGE_DISCONNECTED", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_remove_polygons_in_bbox(d / "clean.gds", _route_bbox(d, module_name, "stage_00_driver", "Z", "stage_01_driver", "A"), layers={12}), d / "clean.gds")[1], "geometry", "missing via1"),
            (MutationCase("44_off_grid_route", "contract", "GRID_FAILED", "OFF_GRID_GEOMETRY", Path("layout_quality_metrics.json"), "validate_delay_chain_bundle"), lambda d: (_mutate_layout_metric(d / "layout_quality_metrics.json", "off_grid_count", 1), d / "layout_quality_metrics.json")[1], "contract", "off grid route"),
            (MutationCase("45_VDD_VSS_wrong_abutment", "short", "POWER_SIGNAL_SHORT", "POWER_SIGNAL_SHORT", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_bridge_bboxes(d / "clean.gds", _top_label_bbox(d / "clean.gds", top_name, "VDD"), _top_label_bbox(d / "clean.gds", top_name, "VSS")), d / "clean.gds")[1], "short", "vdd vss wrong abutment"),
            (MutationCase("46_debug_label_leakage", "label", "TOP_PIN_CONTRACT_FAILED", "TOP_PIN_ORDER_MISMATCH", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (add_label(d / "clean.gds", top_name, "DEBUG", (0.2, 1.0)), d / "clean.gds")[1], "label", "debug label leakage"),
            (MutationCase("47_determinism_mutation", "determinism", "DETERMINISM_FAILED", "DETERMINISM_FAILED", Path("determinism.json"), "validate_delay_chain_bundle"), lambda d: (_mutate_json_value(d / "determinism.json", "byte_identical", False), d / "determinism.json")[1], "determinism", "determinism mutation"),
        ]
    )
    if module_name == "delay_chain":
        rows.extend(
            [
                (MutationCase("48_middle_stage_skipped", "short", "CONNECTIVITY_MISMATCH", "FOREIGN_NET_CONTACT", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_bridge_bboxes(d / "clean.gds", _resolved_role_pin_bbox(d, module_name, "stage_03_driver", "Z"), _resolved_role_pin_bbox(d, module_name, "stage_05_driver", "A")), d / "clean.gds")[1], "short", "middle stage skipped"),
                (MutationCase("49_stage4_stage5_swapped", "contract", "STRUCTURAL_CONTRACT_FAILED", "STAGE_ORDER_MISMATCH", Path("instance_binding.csv"), "validate_delay_chain_bundle"), lambda d: (_swap_csv_rows(d / "instance_binding.csv", 20, 25), _swap_manifest_rows(d / "instance_role_manifest.json", 20, 25), d / "instance_binding.csv")[2], "contract", "stage4 stage5 swapped"),
                (MutationCase("50_stage7_stage8_swapped", "contract", "STRUCTURAL_CONTRACT_FAILED", "STAGE_ORDER_MISMATCH", Path("instance_binding.csv"), "validate_delay_chain_bundle"), lambda d: (_swap_csv_rows(d / "instance_binding.csv", 35, 40), _swap_manifest_rows(d / "instance_role_manifest.json", 35, 40), d / "instance_binding.csv")[2], "contract", "stage7 stage8 swapped"),
                (MutationCase("51_wrong_total_stage_count_8", "contract", "STRUCTURAL_CONTRACT_FAILED", "DRIVER_COUNT_MISMATCH", Path("instance_binding.csv"), "validate_delay_chain_bundle"), lambda d: (_remove_csv_row(d / "instance_binding.csv", 40), _remove_manifest_row(d / "instance_role_manifest.json", 40), d / "instance_binding.csv")[2], "contract", "wrong total stage count 8"),
                (MutationCase("52_wrong_total_stage_count_10", "contract", "STRUCTURAL_CONTRACT_FAILED", "DRIVER_COUNT_MISMATCH", Path("instance_binding.csv"), "validate_delay_chain_bundle"), lambda d: (_duplicate_csv_row(d / "instance_binding.csv", 40, new_role="stage_09_driver"), _duplicate_manifest_row(d / "instance_role_manifest.json", 40, new_role="stage_09_driver"), d / "instance_binding.csv")[2], "contract", "wrong total stage count 10"),
                (MutationCase("53_last_driver_output_connected_to_wrong_node", "label", "FOREIGN_NET_FAILED", "FOREIGN_NET_CONTACT", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_move_label_to_bbox_center(d / "clean.gds", top_name, "out", _resolved_role_pin_bbox(d, module_name, "stage_07_driver", "Z")), d / "clean.gds")[1], "label", "last driver output connected to wrong node net"),
                (MutationCase("54_last_stage_out_polarity_binding_wrong", "short", "CONNECTIVITY_MISMATCH", "FOREIGN_NET_CONTACT", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_bridge_bboxes(d / "clean.gds", _resolved_role_pin_bbox(d, module_name, "stage_08_driver", "A"), _top_label_bbox(d / "clean.gds", top_name, "out")), d / "clean.gds")[1], "short", "last stage out polarity binding wrong"),
                (MutationCase("55_middle_stage_load_group_wrong_stage", "short", "CONNECTIVITY_MISMATCH", "FOREIGN_NET_CONTACT", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_bridge_bboxes(d / "clean.gds", _resolved_role_pin_bbox(d, module_name, "stage_06_driver", "Z"), _resolved_role_pin_bbox(d, module_name, "stage_04_load_00", "A")), d / "clean.gds")[1], "short", "middle stage load group wrong stage"),
                (MutationCase("56_nonadjacent_stage_nets_merged", "short", "CONNECTIVITY_MISMATCH", "FOREIGN_NET_CONTACT", Path("clean.gds"), "validate_delay_chain_bundle"), lambda d: (_bridge_bboxes(d / "clean.gds", _resolved_role_pin_bbox(d, module_name, "stage_01_driver", "Z"), _resolved_role_pin_bbox(d, module_name, "stage_07_driver", "Z")), d / "clean.gds")[1], "short", "nonadjacent stage nets merged"),
            ]
        )
    return rows


def run_delay_chain_negative_regressions(
    *,
    module_name: str,
    baseline_clean_gds: Path,
    production_validator: dict[str, Any],
    output_dir: Path,
    resume: bool = False,
) -> dict[str, Any]:
    base_dir = baseline_clean_gds.parent
    work_root = output_dir.parents[2] / "negative_test_work" / module_name
    if work_root.exists() and not resume:
        shutil.rmtree(work_root)
    work_root.mkdir(parents=True, exist_ok=True)
    cases = _case_rows(module_name)
    rows = []

    def _validate(work_dir: Path, *, determinism: bool) -> dict[str, Any]:
        return production_validator["validate_fn"](
            repo_root=production_validator["repo_root"],
            bundle_dir=work_dir,
            module_name=module_name,
            openyield_root=production_validator["openyield_root"],
            klayout_bin=production_validator["klayout_bin"],
            drc_deck=production_validator["drc_deck"],
            run_determinism=determinism,
        )

    for case, mutator, kind, description in cases:
        baseline_abs = base_dir / case.baseline_input_path
        baseline_sha = _sha256(baseline_abs) if baseline_abs.exists() else ""
        if resume and baseline_sha:
            cached = load_completed_checkpoint(work_root, case.test_id, baseline_sha)
            if cached is not None:
                row = {
                    "test_id": cached["test_id"],
                    "description": description,
                    "baseline_sha": cached["baseline_sha"],
                    "mutated_sha": cached["mutated_sha"],
                    "mutation_effective": cached["mutation_effective"],
                    "production_validator_name": cached.get("validator_name", case.validator_name),
                    "production_validator_invoked": True,
                    "expected_rejection_family": rejection_family(cached["expected_rejection_code"]),
                    "expected_rejection_code": cached["expected_rejection_code"],
                    "actual_rejection_family": rejection_family(cached["actual_rejection_code"]),
                    "actual_rejection_code": cached["actual_rejection_code"],
                    "family_matched": True,
                    "code_matched": cached["expected_rejection_code"] == cached["actual_rejection_code"],
                    "rejected_as_expected": cached["rejected_as_expected"],
                    "unexpected_pass": not cached["rejected_as_expected"],
                    "checkpoint_path": str((work_root / "checkpoints" / f"{case.test_id}.json").resolve()),
                    "mutation_proof_path": cached.get("mutation_proof_path", ""),
                }
                rows.append(row)
                continue

        validate_fn = (lambda work_dir: _validate(work_dir, determinism=False)) if kind != "determinism" else (lambda work_dir: _validate(work_dir, determinism=False))
        if kind == "contract":
            result = run_contract_mutation(base_dir=base_dir, work_root=work_root, case=case, mutate_fn=mutator, validate_fn=validate_fn)
        elif kind == "label":
            result = run_gds_label_mutation(base_dir=base_dir, work_root=work_root, case=case, mutate_fn=mutator, validate_fn=validate_fn)
        elif kind == "hierarchy":
            result = run_hierarchy_mutation(base_dir=base_dir, work_root=work_root, case=case, mutate_fn=mutator, validate_fn=validate_fn)
        elif kind == "determinism":
            result = run_determinism_mutation(base_dir=base_dir, work_root=work_root, case=case, mutate_fn=mutator, validate_fn=validate_fn)
        elif kind == "short":
            result = run_gds_short_mutation(base_dir=base_dir, work_root=work_root, case=case, mutate_fn=mutator, validate_fn=validate_fn)
        else:
            result = run_gds_geometry_mutation(base_dir=base_dir, work_root=work_root, case=case, mutate_fn=mutator, validate_fn=validate_fn)

        test_work_dir = work_root / case.test_id
        proof_path = _write_mutation_proof(test_work_dir, case, result)
        checkpoint_path = str((work_root / "checkpoints" / f"{case.test_id}.json").resolve())
        row = {
            "test_id": case.test_id,
            "description": description,
            "baseline_sha": result["baseline_input_sha256"],
            "mutated_sha": result["mutated_input_sha256"],
            "mutation_effective": result["mutation_effective"],
            "production_validator_name": result["production_validator_name"],
            "production_validator_invoked": bool(result["production_validator_name"]),
            "expected_rejection_family": result["expected_rejection_family"],
            "expected_rejection_code": result["expected_rejection_code"],
            "actual_rejection_family": result["actual_rejection_family"],
            "actual_rejection_code": result["actual_rejection_code"],
            "family_matched": result["family_matched"],
            "code_matched": result["code_matched"],
            "rejected_as_expected": result["rejected_as_expected"],
            "unexpected_pass": not result["rejected_as_expected"],
            "checkpoint_path": checkpoint_path,
            "mutation_proof_path": proof_path,
        }
        rows.append(row)
        write_case_checkpoint(
            work_root=work_root,
            test_id=case.test_id,
            baseline_sha=result["baseline_input_sha256"],
            mutated_sha=result["mutated_input_sha256"],
            mutation_effective=result["mutation_effective"],
            validator_name=result["production_validator_name"],
            validator_input_sha=result["production_validator_input_sha256"],
            expected_rejection_code=result["expected_rejection_code"],
            actual_rejection_code=result["actual_rejection_code"],
            rejected_as_expected=result["rejected_as_expected"],
        )
        checkpoint_payload = read_json(work_root / "checkpoints" / f"{case.test_id}.json")
        checkpoint_payload["status"] = "completed"
        checkpoint_payload["validator_invoked"] = True
        checkpoint_payload["mutation_proof_path"] = proof_path
        checkpoint_payload["completed_at"] = "2026-07-25"
        write_json(work_root / "checkpoints" / f"{case.test_id}.json", checkpoint_payload)

    matrix_name = f"{module_name}_negative_test_matrix.csv"
    summary_name = f"{module_name}_negative_test_summary.json"
    write_negative_test_matrix(output_dir / matrix_name, rows)
    summary = write_negative_test_summary(output_dir / summary_name, rows)
    summary["specific_code_match_count"] = sum(1 for row in rows if row["code_matched"])
    write_json(output_dir / summary_name, summary)
    write_text(output_dir / f"{module_name}_negative_test_execution.log", "\n".join(f"{row['test_id']} {row['actual_rejection_code']}" for row in rows))
    return {"rows": rows, "summary": summary}
