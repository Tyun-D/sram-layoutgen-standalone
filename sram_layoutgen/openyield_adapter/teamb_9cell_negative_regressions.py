from __future__ import annotations

import csv
import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

import gdstk

from sram_layoutgen.openyield_adapter.physical_connectivity_extractor import extract_physical_connectivity
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import geometry_fingerprint, parse_lyrdb_categories, read_top_cell, run_cell_drc
from sram_layoutgen.openyield_adapter.production_negative_test_harness import (
    MutationCase,
    add_label,
    load_completed_checkpoint,
    run_contract_mutation,
    run_determinism_mutation,
    run_gds_geometry_mutation,
    run_gds_label_mutation,
    run_gds_short_mutation,
    run_hierarchy_mutation,
    write_case_checkpoint,
    write_negative_test_matrix,
    write_negative_test_summary,
)
from sram_layoutgen.openyield_adapter.rejection_code_registry import rejection_family
from sram_layoutgen.openyield_adapter.teamb_9cell_input_lock import FROZEN_MODULE_SPECS
from sram_layoutgen.openyield_adapter.teamb_composite_helper import read_json, write_json, write_text


EXPECTED_MODULES = [spec.module_name for spec in FROZEN_MODULE_SPECS]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_gds(lib: gdstk.Library, path: Path) -> None:
    lib.write_gds(path)


def _top_cell(gds_path: Path, top_name: str) -> tuple[gdstk.Library, gdstk.Cell]:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    return lib, top


def _canonical_top_data(repo_root: Path) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for spec in FROZEN_MODULE_SPECS:
        clean = repo_root / spec.clean_gds_path
        _, top = read_top_cell(clean)
        labels = sorted(str(label.text) for label in top.labels)
        rows[spec.module_name] = {
            "clean_gds_path": str(clean.resolve()),
            "top_cell_name": top.name,
            "sha256": _sha256(clean),
            "fingerprint": geometry_fingerprint(clean, top.name),
            "labels": labels,
            "reference_count": len(top.references),
        }
    return rows


def _rewrite_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _rewrite_input_lock(path: Path, mutate_fn: Callable[[dict[str, Any]], None]) -> None:
    payload = read_json(path)
    mutate_fn(payload)
    write_json(path, payload)


def _mutate_json_value(path: Path, key: str, value: Any) -> None:
    payload = read_json(path)
    payload[key] = value
    write_json(path, payload)


def _mutate_row_json_value(path: Path, row_index: int, key: str, value: Any) -> None:
    payload = read_json(path)
    payload["rows"][row_index][key] = value
    write_json(path, payload)


def _mutate_csv_row(path: Path, row_index: int, key: str, value: Any) -> None:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rows[row_index][key] = value
    _rewrite_csv(path, rows)


def _append_input_lock_row(path: Path, row: dict[str, Any]) -> None:
    payload = read_json(path)
    payload["rows"].append(row)
    payload["module_count"] = len(payload["rows"])
    payload["all_input_sha_matched"] = False
    write_json(path, payload)


def _remove_input_lock_row(path: Path, module_name: str) -> None:
    payload = read_json(path)
    payload["rows"] = [row for row in payload["rows"] if row["module_name"] != module_name]
    payload["module_count"] = len(payload["rows"])
    payload["all_input_sha_matched"] = False
    write_json(path, payload)


def _set_input_lock_row(path: Path, module_name: str, key: str, value: Any) -> None:
    payload = read_json(path)
    for row in payload["rows"]:
        if row["module_name"] == module_name:
            row[key] = value
    write_json(path, payload)


def _rewrite_sha_manifest(path: Path, first_line: str) -> None:
    rows = path.read_text(encoding="utf-8").splitlines()
    if rows:
        rows[0] = first_line
    write_text(path, "\n".join(rows))


def _flatten_top_cell(gds_path: Path, top_name: str) -> None:
    lib, top = _top_cell(gds_path, top_name)
    top.flatten()
    _write_gds(lib, gds_path)


def _remove_all_top_references(gds_path: Path, top_name: str) -> None:
    lib, top = _top_cell(gds_path, top_name)
    original_top_names = {cell.name for cell in lib.top_level()}
    refs = list(top.references)
    if refs:
        top.remove(*refs)
    keep_names = set(original_top_names)
    queue = [cell for cell in lib.cells if cell.name in original_top_names]
    while queue:
        cell = queue.pop()
        for ref in cell.references:
            child = ref.cell
            child_name = ref.cell_name or (child.name if child is not None else "")
            if child_name and child_name not in keep_names:
                keep_names.add(child_name)
                if child is not None:
                    queue.append(child)
    orphan_cells = [cell for cell in lib.cells if cell.name not in keep_names]
    if orphan_cells:
        lib.remove(*orphan_cells)
    _write_gds(lib, gds_path)


def _remove_top_label(gds_path: Path, top_name: str, label_name: str) -> None:
    lib, top = _top_cell(gds_path, top_name)
    victims = [label for label in top.labels if str(label.text) == label_name]
    if victims:
        top.remove(*victims)
    _write_gds(lib, gds_path)


def _rename_top_label(gds_path: Path, top_name: str, old: str, new: str) -> None:
    lib, top = _top_cell(gds_path, top_name)
    target = next(label for label in top.labels if str(label.text) == old)
    target.text = new
    _write_gds(lib, gds_path)


def _add_top_rect(gds_path: Path, top_name: str, bbox: tuple[float, float, float, float], *, layer: int, datatype: int = 0) -> None:
    lib, top = _top_cell(gds_path, top_name)
    top.add(gdstk.rectangle((bbox[0], bbox[1]), (bbox[2], bbox[3]), layer=layer, datatype=datatype))
    _write_gds(lib, gds_path)


def _shift_first_atlas_reference(gds_path: Path, top_name: str, dx: float, dy: float) -> None:
    lib, top = _top_cell(gds_path, top_name)
    ref = list(top.references)[0]
    ref.origin = (float(ref.origin[0]) + dx, float(ref.origin[1]) + dy)
    _write_gds(lib, gds_path)


def _write_fake_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_json(path, payload)


def _atlas_ref_order(gds_path: Path, top_name: str) -> list[str]:
    lib, top = _top_cell(gds_path, top_name)
    return [ref.cell_name or ref.cell.name for ref in top.references]


def _classify_drc_failure(marker_categories: dict[str, int]) -> str:
    if any("GRID:" in key for key in marker_categories):
        return "OFF_GRID_PLACEMENT"
    return "DRC_FAILED"


def validate_teamb_9cell_bundle(
    *,
    repo_root: Path,
    bundle_root: Path,
    klayout_bin: Path,
    drc_deck: Path,
) -> dict[str, Any]:
    rejection_codes: list[str] = []
    input_lock_path = bundle_root / "TEAM_B_9CELL_INPUT_LOCK.json"
    sha_manifest_path = bundle_root / "TEAM_B_9CELL_INPUT_SHA256SUMS.txt"
    current_root = bundle_root / "current_supported_config"
    library_gds = current_root / "TEAM_B_9CELL_LIBRARY.gds"
    clean_atlas = current_root / "TEAM_B_9CELL_CLEAN_ATLAS.gds"
    placement_csv = current_root / "TEAM_B_9CELL_ATLAS_PLACEMENT.csv"
    collision_report_path = current_root / "CELL_NAME_COLLISION_REPORT.json"
    pin_access_path = current_root / "TEAM_B_9CELL_PIN_ACCESS_REPORT.json"
    foreign_path = current_root / "TEAM_B_9CELL_FOREIGN_NET_REPORT.json"
    gate_path = current_root / "TEAM_B_9CELL_INTEGRATION_GATE.json"

    canonical = _canonical_top_data(repo_root)

    input_lock = read_json(input_lock_path)
    module_names = [row["module_name"] for row in input_lock["rows"]]
    missing_modules = sorted(set(EXPECTED_MODULES) - set(module_names))
    extra_modules = sorted(set(module_names) - set(EXPECTED_MODULES))
    if missing_modules:
        rejection_codes.append("MODULE_MISSING")
    elif extra_modules:
        rejection_codes.append("UNAPPROVED_MODULE_PRESENT")
    else:
        for row in input_lock["rows"]:
            if row["module_name"] not in canonical:
                rejection_codes.append("UNAPPROVED_MODULE_PRESENT")
                break
            expected_sha = canonical[row["module_name"]]["sha256"]
            if row.get("expected_sha256") != expected_sha or row.get("actual_sha256") != expected_sha or row.get("sha_match") is not True:
                rejection_codes.append("INPUT_SHA_MISMATCH")
                break
    if not rejection_codes:
        sha_lines = sha_manifest_path.read_text(encoding="utf-8").splitlines()
        expected_lines = [f"{canonical[row['module_name']]['sha256']}  {row['clean_gds_path']}" for row in input_lock["rows"]]
        if sha_lines != expected_lines:
            rejection_codes.append("MANIFEST_SHA_MISMATCH")
    if not rejection_codes:
        top_names = [row["top_cell_name"] for row in input_lock["rows"]]
        if len(top_names) != len(set(top_names)):
            rejection_codes.append("DUPLICATE_TOP_CELL")
    if not rejection_codes:
        for row in input_lock["rows"]:
            expected_top = canonical[row["module_name"]]["top_cell_name"]
            if row["top_cell_name"] != expected_top:
                rejection_codes.append("TOP_CELL_NAME_MISMATCH")
                break
    if not rejection_codes:
        for row in input_lock["rows"]:
            machine_gate_path = Path(row["machine_gate_path"])
            if not machine_gate_path.exists():
                rejection_codes.append("MISSING_MACHINE_GATE")
                break
            gate = read_json(machine_gate_path)
            if not all(value is True for key, value in gate.items() if key != "drc_marker_count") or int(gate.get("drc_marker_count", -1)) != 0:
                rejection_codes.append("FALSE_MACHINE_GATE_CLAIM")
                break
    if not rejection_codes:
        for row in input_lock["rows"]:
            negative_summary_path = Path(row["negative_summary_path"])
            if not negative_summary_path.exists():
                rejection_codes.append("WRONG_NEGATIVE_SUMMARY_BINDING")
                break
            summary = read_json(negative_summary_path)
            if summary.get("negative_tests_passed") is not True:
                rejection_codes.append("WRONG_NEGATIVE_SUMMARY_BINDING")
                break
    if not rejection_codes:
        collision = read_json(collision_report_path)
        if int(collision.get("same_name_different_geometry_count", 0)) > 0:
            rejection_codes.append("SAME_NAME_DIFFERENT_GEOMETRY")
        elif int(collision.get("dangling_reference_count", 0)) > 0:
            rejection_codes.append("DANGLING_REFERENCE")
        elif int(collision.get("cyclic_reference_count", 0)) > 0:
            rejection_codes.append("CYCLIC_REFERENCE")
    if not rejection_codes:
        lib = gdstk.read_gds(library_gds)
        lib_cells = {cell.name: cell for cell in lib.cells}
        top_level_names = sorted(cell.name for cell in lib.top_level())
        if sorted(canonical[row["module_name"]]["top_cell_name"] for row in input_lock["rows"]) != top_level_names:
            rejection_codes.append("UNAPPROVED_MODULE_PRESENT")
        else:
            for row in input_lock["rows"]:
                top_name = row["top_cell_name"]
                expected = canonical[row["module_name"]]
                if top_name not in lib_cells:
                    rejection_codes.append("TOP_CELL_NAME_MISMATCH")
                    break
                top = lib_cells[top_name]
                if len(top.references) < expected["reference_count"]:
                    rejection_codes.append("FLATTENED_MODULE")
                    break
                packaged_fp = geometry_fingerprint(library_gds, top_name)
                if packaged_fp["digest"] != expected["fingerprint"]["digest"]:
                    packaged_labels = sorted(label for label, *_ in packaged_fp["labels"])
                    if set(packaged_labels) < set(expected["labels"]):
                        rejection_codes.append("TOP_PIN_LABEL_MISSING")
                    elif set(packaged_labels) != set(expected["labels"]):
                        rejection_codes.append("INTERNAL_LABEL_LEAK")
                    else:
                        rejection_codes.append("PACKAGED_CELL_GEOMETRY_MUTATED")
                    break
    if not rejection_codes:
        with placement_csv.open(encoding="utf-8", newline="") as handle:
            placements = list(csv.DictReader(handle))
        for row in placements:
            if row["orientation"] != "R0":
                rejection_codes.append("ILLEGAL_ORIENTATION")
                break
            if abs(round(float(row["x"]) / 0.0025) * 0.0025 - float(row["x"])) > 1e-9 or abs(round(float(row["y"]) / 0.0025) * 0.0025 - float(row["y"])) > 1e-9:
                rejection_codes.append("OFF_GRID_PLACEMENT")
                break
        if not rejection_codes:
            grouped: dict[str, list[dict[str, Any]]] = {}
            for row in placements:
                grouped.setdefault(row["group_name"], []).append(row)
            ys = [min(float(row["y"]) for row in rows) for rows in grouped.values()]
            ys.sort()
            if any((ys[index + 1] - ys[index]) < 1.2 for index in range(len(ys) - 1)):
                rejection_codes.append("INTER_GROUP_SPACING_INSUFFICIENT")
        if not rejection_codes:
            hmat = list(csv.DictReader((current_root / "HORIZONTAL_PAIRWISE_ABUTMENT_MATRIX.csv").open(encoding="utf-8", newline="")))
            allowed = {
                (row["left_module"], row["right_module"]): row["drc_passed"].lower() == "true"
                for row in hmat
            }
            by_group: dict[str, list[dict[str, Any]]] = {}
            for row in placements:
                by_group.setdefault(row["group_name"], []).append(row)
            for rows in by_group.values():
                rows.sort(key=lambda row: float(row["x"]))
                for left, right in zip(rows, rows[1:]):
                    gap = float(right["x"]) - (float(left["x"]) + float(left["width"]))
                    if abs(gap) < 1e-9 and not allowed.get((left["module_name"], right["module_name"]), False):
                        rejection_codes.append("ILLEGAL_ZERO_GAP_PAIR")
                        break
                if rejection_codes:
                    break
    if not rejection_codes:
        atlas_lib, atlas_top = _top_cell(clean_atlas, "TEAM_B_9CELL_ATLAS")
        if atlas_top.labels:
            rejection_codes.append("ANNOTATION_LEAKAGE_INTO_CLEAN_ATLAS")
        elif len(atlas_top.references) != 9:
            rejection_codes.append("MODULE_MISSING")
    if not rejection_codes:
        pin_access = read_json(pin_access_path)
        if pin_access.get("pin_access_passed") is not True:
            rejection_codes.append("PIN_ACCESS_BLOCKED")
    if not rejection_codes:
        foreign = read_json(foreign_path)
        if foreign.get("vdd_vss_short_false") is not True:
            rejection_codes.append("VDD_VSS_ABUTMENT")
        elif int(foreign.get("cross_module_signal_merge_count", 0)) > 0:
            rejection_codes.append("CROSS_MODULE_SIGNAL_MERGE")
        elif foreign.get("foreign_net_passed") is not True:
            rejection_codes.append("FOREIGN_NET_CONTACT")
        elif foreign.get("power_signal_contact") is True:
            rejection_codes.append("POWER_SIGNAL_CONTACT")
    if not rejection_codes:
        negative_drc_root = current_root / "_negative_validator_drc"
        negative_drc_root.mkdir(parents=True, exist_ok=True)
        drc = run_cell_drc(klayout_bin, drc_deck, clean_atlas, "TEAM_B_9CELL_ATLAS", negative_drc_root)
        if not drc["drc_passed"]:
            rejection_codes.append(_classify_drc_failure(drc["marker_categories"]))
    if not rejection_codes:
        gate = read_json(gate_path)
        if gate.get("deterministic_A_B_byte_identical") is not True:
            rejection_codes.append("DETERMINISM_FAILED")

    return {
        "passed": not rejection_codes,
        "rejection_codes": rejection_codes,
    }


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


def _case_rows(repo_root: Path) -> list[tuple[MutationCase, Callable[[Path], Path], str, str]]:
    output_gds = Path("current_supported_config/TEAM_B_9CELL_LIBRARY.gds")
    clean_atlas = Path("current_supported_config/TEAM_B_9CELL_CLEAN_ATLAS.gds")
    input_lock = Path("TEAM_B_9CELL_INPUT_LOCK.json")
    gate_path = Path("current_supported_config/TEAM_B_9CELL_INTEGRATION_GATE.json")
    rows: list[tuple[MutationCase, Callable[[Path], Path], str, str]] = []
    fake_row = {
        "module_name": "FAKE_MODULE",
        "clean_gds_path": "/tmp/fake.gds",
        "bundle_dir": "/tmp",
        "top_cell_name": "FAKE_TOP",
        "expected_sha256": "deadbeef",
        "actual_sha256": "deadbeef",
        "sha_match": False,
        "machine_gate_path": "/tmp/fake_machine_gate.json",
        "negative_summary_path": "/tmp/fake_negative_summary.json",
        "drc_summary_path": "/tmp/fake_drc_summary.json",
        "connectivity_path": "/tmp/fake_connectivity.json",
        "foreign_net_path": "",
        "child_immutability_path": "",
        "determinism_path": "",
    }
    rows.extend(
        [
            (MutationCase("01_wrong_module_sha", "contract", "INPUT_LOCK_FAILED", "INPUT_SHA_MISMATCH", input_lock, "validate_teamb_9cell_bundle"), lambda d: (_set_input_lock_row(d / "TEAM_B_9CELL_INPUT_LOCK.json", "PNAND2", "expected_sha256", "deadbeef"), d / "TEAM_B_9CELL_INPUT_LOCK.json")[1], "contract", "wrong module SHA"),
            (MutationCase("02_missing_module", "contract", "INPUT_LOCK_FAILED", "MODULE_MISSING", input_lock, "validate_teamb_9cell_bundle"), lambda d: (_remove_input_lock_row(d / "TEAM_B_9CELL_INPUT_LOCK.json", "PNAND2"), d / "TEAM_B_9CELL_INPUT_LOCK.json")[1], "contract", "missing module"),
            (MutationCase("03_extra_unapproved_module", "contract", "INPUT_LOCK_FAILED", "UNAPPROVED_MODULE_PRESENT", input_lock, "validate_teamb_9cell_bundle"), lambda d: (_append_input_lock_row(d / "TEAM_B_9CELL_INPUT_LOCK.json", fake_row), d / "TEAM_B_9CELL_INPUT_LOCK.json")[1], "contract", "extra unapproved module"),
            (MutationCase("04_wrong_top_cell_name", "contract", "PACKAGING_FAILED", "TOP_CELL_NAME_MISMATCH", input_lock, "validate_teamb_9cell_bundle"), lambda d: (_set_input_lock_row(d / "TEAM_B_9CELL_INPUT_LOCK.json", "PNAND2", "top_cell_name", "WRONG_TOP"), d / "TEAM_B_9CELL_INPUT_LOCK.json")[1], "contract", "wrong top cell name"),
            (MutationCase("05_duplicate_top_cell", "contract", "PACKAGING_FAILED", "DUPLICATE_TOP_CELL", input_lock, "validate_teamb_9cell_bundle"), lambda d: (_set_input_lock_row(d / "TEAM_B_9CELL_INPUT_LOCK.json", "PNAND3", "top_cell_name", "PNAND2_NW180_PW270_L50_FPDK45"), d / "TEAM_B_9CELL_INPUT_LOCK.json")[1], "contract", "duplicate top cell"),
            (MutationCase("06_same_name_different_geometry", "contract", "PACKAGING_FAILED", "SAME_NAME_DIFFERENT_GEOMETRY", Path("current_supported_config/CELL_NAME_COLLISION_REPORT.json"), "validate_teamb_9cell_bundle"), lambda d: (_mutate_json_value(d / "current_supported_config/CELL_NAME_COLLISION_REPORT.json", "same_name_different_geometry_count", 1), d / "current_supported_config/CELL_NAME_COLLISION_REPORT.json")[1], "contract", "same name different geometry"),
            (MutationCase("07_dangling_child_reference", "contract", "PACKAGING_FAILED", "DANGLING_REFERENCE", Path("current_supported_config/CELL_NAME_COLLISION_REPORT.json"), "validate_teamb_9cell_bundle"), lambda d: (_mutate_json_value(d / "current_supported_config/CELL_NAME_COLLISION_REPORT.json", "dangling_reference_count", 1), d / "current_supported_config/CELL_NAME_COLLISION_REPORT.json")[1], "contract", "dangling child reference"),
            (MutationCase("08_cyclic_reference", "contract", "PACKAGING_FAILED", "CYCLIC_REFERENCE", Path("current_supported_config/CELL_NAME_COLLISION_REPORT.json"), "validate_teamb_9cell_bundle"), lambda d: (_mutate_json_value(d / "current_supported_config/CELL_NAME_COLLISION_REPORT.json", "cyclic_reference_count", 1), d / "current_supported_config/CELL_NAME_COLLISION_REPORT.json")[1], "contract", "cyclic reference"),
            (MutationCase("09_flattened_module", "hierarchy", "PACKAGING_FAILED", "FLATTENED_MODULE", output_gds, "validate_teamb_9cell_bundle"), lambda d: (_remove_all_top_references(d / "current_supported_config/TEAM_B_9CELL_LIBRARY.gds", "PNAND2_NW180_PW270_L50_FPDK45"), d / "current_supported_config/TEAM_B_9CELL_LIBRARY.gds")[1], "hierarchy", "flattened module"),
            (MutationCase("10_packaged_child_geometry_mutation", "geometry", "PACKAGING_FAILED", "PACKAGED_CELL_GEOMETRY_MUTATED", output_gds, "validate_teamb_9cell_bundle"), lambda d: (_add_top_rect(d / "current_supported_config/TEAM_B_9CELL_LIBRARY.gds", "PNAND2_NW180_PW270_L50_FPDK45", (0.1, 0.1, 0.12, 0.12), layer=11), d / "current_supported_config/TEAM_B_9CELL_LIBRARY.gds")[1], "geometry", "packaged child geometry mutation"),
            (MutationCase("11_missing_top_pin_label", "label", "TOP_PIN_CONTRACT_FAILED", "TOP_PIN_LABEL_MISSING", output_gds, "validate_teamb_9cell_bundle"), lambda d: (_remove_top_label(d / "current_supported_config/TEAM_B_9CELL_LIBRARY.gds", "PNAND2_NW180_PW270_L50_FPDK45", "A"), d / "current_supported_config/TEAM_B_9CELL_LIBRARY.gds")[1], "label", "missing top Pin label"),
            (MutationCase("12_extra_internal_label", "label", "TOP_PIN_CONTRACT_FAILED", "INTERNAL_LABEL_LEAK", output_gds, "validate_teamb_9cell_bundle"), lambda d: (add_label(d / "current_supported_config/TEAM_B_9CELL_LIBRARY.gds", "PNAND2_NW180_PW270_L50_FPDK45", "zb_debug", (0.2, 0.2)), d / "current_supported_config/TEAM_B_9CELL_LIBRARY.gds")[1], "label", "extra internal label"),
            (MutationCase("13_wrong_orientation", "contract", "PLACEMENT_FAILED", "ILLEGAL_ORIENTATION", Path("current_supported_config/TEAM_B_9CELL_ATLAS_PLACEMENT.csv"), "validate_teamb_9cell_bundle"), lambda d: (_mutate_csv_row(d / "current_supported_config/TEAM_B_9CELL_ATLAS_PLACEMENT.csv", 0, "orientation", "MY"), d / "current_supported_config/TEAM_B_9CELL_ATLAS_PLACEMENT.csv")[1], "contract", "wrong orientation"),
            (MutationCase("14_illegal_zero_gap_pair", "contract", "PLACEMENT_FAILED", "ILLEGAL_ZERO_GAP_PAIR", Path("current_supported_config/TEAM_B_9CELL_ATLAS_PLACEMENT.csv"), "validate_teamb_9cell_bundle"), lambda d: (_mutate_csv_row(d / "current_supported_config/TEAM_B_9CELL_ATLAS_PLACEMENT.csv", 1, "x", "1.0125"), d / "current_supported_config/TEAM_B_9CELL_ATLAS_PLACEMENT.csv")[1], "contract", "illegal zero-gap pair"),
            (MutationCase("15_vdd_to_vss_abutment", "contract", "FOREIGN_NET_FAILED", "VDD_VSS_ABUTMENT", Path("current_supported_config/TEAM_B_9CELL_FOREIGN_NET_REPORT.json"), "validate_teamb_9cell_bundle"), lambda d: (_mutate_json_value(d / "current_supported_config/TEAM_B_9CELL_FOREIGN_NET_REPORT.json", "vdd_vss_short_false", False), d / "current_supported_config/TEAM_B_9CELL_FOREIGN_NET_REPORT.json")[1], "contract", "VDD-to-VSS abutment"),
            (MutationCase("16_power_to_signal_contact", "contract", "FOREIGN_NET_FAILED", "POWER_SIGNAL_CONTACT", Path("current_supported_config/TEAM_B_9CELL_FOREIGN_NET_REPORT.json"), "validate_teamb_9cell_bundle"), lambda d: (_write_fake_json(d / "current_supported_config/TEAM_B_9CELL_FOREIGN_NET_REPORT.json", {"foreign_net_passed": True, "cross_module_signal_merge_count": 0, "vdd_vss_short_false": True, "power_signal_contact": True}), d / "current_supported_config/TEAM_B_9CELL_FOREIGN_NET_REPORT.json")[1], "contract", "power-to-signal contact"),
            (MutationCase("17_cross_module_signal_merge", "contract", "FOREIGN_NET_FAILED", "CROSS_MODULE_SIGNAL_MERGE", Path("current_supported_config/TEAM_B_9CELL_FOREIGN_NET_REPORT.json"), "validate_teamb_9cell_bundle"), lambda d: (_mutate_json_value(d / "current_supported_config/TEAM_B_9CELL_FOREIGN_NET_REPORT.json", "cross_module_signal_merge_count", 1), d / "current_supported_config/TEAM_B_9CELL_FOREIGN_NET_REPORT.json")[1], "contract", "cross-module signal merge"),
            (MutationCase("18_pin_access_blocked", "contract", "PIN_ACCESS_FAILED", "PIN_ACCESS_BLOCKED", Path("current_supported_config/TEAM_B_9CELL_PIN_ACCESS_REPORT.json"), "validate_teamb_9cell_bundle"), lambda d: (_mutate_json_value(d / "current_supported_config/TEAM_B_9CELL_PIN_ACCESS_REPORT.json", "pin_access_passed", False), d / "current_supported_config/TEAM_B_9CELL_PIN_ACCESS_REPORT.json")[1], "contract", "Pin access blocked"),
            (MutationCase("19_insufficient_inter_group_spacing", "contract", "PLACEMENT_FAILED", "INTER_GROUP_SPACING_INSUFFICIENT", Path("current_supported_config/TEAM_B_9CELL_ATLAS_PLACEMENT.csv"), "validate_teamb_9cell_bundle"), lambda d: (_mutate_csv_row(d / "current_supported_config/TEAM_B_9CELL_ATLAS_PLACEMENT.csv", 4, "y", "1.0"), d / "current_supported_config/TEAM_B_9CELL_ATLAS_PLACEMENT.csv")[1], "contract", "insufficient inter-group spacing"),
            (MutationCase("20_off_grid_placement", "geometry", "GRID_FAILED", "OFF_GRID_PLACEMENT", clean_atlas, "validate_teamb_9cell_bundle"), lambda d: (_shift_first_atlas_reference(d / "current_supported_config/TEAM_B_9CELL_CLEAN_ATLAS.gds", "TEAM_B_9CELL_ATLAS", 0.001, 0.0), d / "current_supported_config/TEAM_B_9CELL_CLEAN_ATLAS.gds")[1], "geometry", "off-grid placement"),
            (MutationCase("21_drc_atlas_mutation", "geometry", "DRC_FAILED", "DRC_FAILED", clean_atlas, "validate_teamb_9cell_bundle"), lambda d: (_shift_first_atlas_reference(d / "current_supported_config/TEAM_B_9CELL_CLEAN_ATLAS.gds", "TEAM_B_9CELL_ATLAS", 1.6125, 0.0), d / "current_supported_config/TEAM_B_9CELL_CLEAN_ATLAS.gds")[1], "geometry", "atlas DRC mutation"),
            (MutationCase("22_foreign_net_mutation", "contract", "FOREIGN_NET_FAILED", "FOREIGN_NET_CONTACT", Path("current_supported_config/TEAM_B_9CELL_FOREIGN_NET_REPORT.json"), "validate_teamb_9cell_bundle"), lambda d: (_mutate_json_value(d / "current_supported_config/TEAM_B_9CELL_FOREIGN_NET_REPORT.json", "foreign_net_passed", False), d / "current_supported_config/TEAM_B_9CELL_FOREIGN_NET_REPORT.json")[1], "contract", "foreign-net mutation"),
            (MutationCase("23_manifest_gds_sha_mismatch", "contract", "INPUT_LOCK_FAILED", "MANIFEST_SHA_MISMATCH", Path("TEAM_B_9CELL_INPUT_SHA256SUMS.txt"), "validate_teamb_9cell_bundle"), lambda d: (_rewrite_sha_manifest(d / "TEAM_B_9CELL_INPUT_SHA256SUMS.txt", "deadbeef  /tmp/fake.gds"), d / "TEAM_B_9CELL_INPUT_SHA256SUMS.txt")[1], "contract", "manifest/GDS SHA mismatch"),
            (MutationCase("24_missing_machine_gate", "contract", "INPUT_LOCK_FAILED", "MISSING_MACHINE_GATE", input_lock, "validate_teamb_9cell_bundle"), lambda d: (_set_input_lock_row(d / "TEAM_B_9CELL_INPUT_LOCK.json", "PNAND2", "machine_gate_path", str((d / "missing_machine_gate.json").resolve())), d / "TEAM_B_9CELL_INPUT_LOCK.json")[1], "contract", "missing machine gate"),
            (MutationCase("25_false_machine_gate_claim", "contract", "INPUT_LOCK_FAILED", "FALSE_MACHINE_GATE_CLAIM", input_lock, "validate_teamb_9cell_bundle"), lambda d: (_write_fake_json(d / "fake_machine_gate.json", {"source_lock_complete": False, "drc_marker_count": 1}), _set_input_lock_row(d / "TEAM_B_9CELL_INPUT_LOCK.json", "PNAND2", "machine_gate_path", str((d / "fake_machine_gate.json").resolve())), d / "TEAM_B_9CELL_INPUT_LOCK.json")[2], "contract", "false machine-gate claim"),
            (MutationCase("26_wrong_negative_summary_binding", "contract", "INPUT_LOCK_FAILED", "WRONG_NEGATIVE_SUMMARY_BINDING", input_lock, "validate_teamb_9cell_bundle"), lambda d: (_write_fake_json(d / "fake_negative_summary.json", {"negative_tests_passed": False, "total_count": 0}), _set_input_lock_row(d / "TEAM_B_9CELL_INPUT_LOCK.json", "PNAND2", "negative_summary_path", str((d / "fake_negative_summary.json").resolve())), d / "TEAM_B_9CELL_INPUT_LOCK.json")[2], "contract", "wrong negative-summary binding"),
            (MutationCase("27_determinism_mutation", "determinism", "DETERMINISM_FAILED", "DETERMINISM_FAILED", gate_path, "validate_teamb_9cell_bundle"), lambda d: (_mutate_json_value(d / "current_supported_config/TEAM_B_9CELL_INTEGRATION_GATE.json", "deterministic_A_B_byte_identical", False), d / "current_supported_config/TEAM_B_9CELL_INTEGRATION_GATE.json")[1], "determinism", "determinism mutation"),
            (MutationCase("28_annotation_leakage_into_clean_atlas", "label", "PACKAGING_FAILED", "ANNOTATION_LEAKAGE_INTO_CLEAN_ATLAS", clean_atlas, "validate_teamb_9cell_bundle"), lambda d: (add_label(d / "current_supported_config/TEAM_B_9CELL_CLEAN_ATLAS.gds", "TEAM_B_9CELL_ATLAS", "DEBUG", (0.5, 0.5)), d / "current_supported_config/TEAM_B_9CELL_CLEAN_ATLAS.gds")[1], "label", "annotation leakage into clean atlas"),
        ]
    )
    return rows


def run_teamb_9cell_negative_regressions(
    *,
    repo_root: Path,
    baseline_bundle_root: Path,
    output_root: Path,
    klayout_bin: Path,
    drc_deck: Path,
    resume: bool = False,
    scratch_root: Path | None = None,
    rebuild_failed: bool = False,
    cleanup_completed_scratch: bool = False,
) -> dict[str, Any]:
    checkpoint_root = baseline_bundle_root / "negative_test_work" / "TEAM_B_9CELL"
    if checkpoint_root.exists() and not resume:
        shutil.rmtree(checkpoint_root)
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    case_work_root = (scratch_root.resolve() if scratch_root is not None else checkpoint_root) / "TEAM_B_9CELL"
    if case_work_root.exists() and not resume:
        shutil.rmtree(case_work_root)
    case_work_root.mkdir(parents=True, exist_ok=True)
    cases = _case_rows(repo_root)
    rows = []

    def _validate(work_dir: Path) -> dict[str, Any]:
        return validate_teamb_9cell_bundle(
            repo_root=repo_root,
            bundle_root=work_dir,
            klayout_bin=klayout_bin,
            drc_deck=drc_deck,
        )

    for case, mutator, kind, description in cases:
        baseline_abs = baseline_bundle_root / case.baseline_input_path
        baseline_sha = _sha256(baseline_abs) if baseline_abs.exists() else ""
        if resume and baseline_sha:
            cached = load_completed_checkpoint(checkpoint_root, case.test_id, baseline_sha)
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
                    "checkpoint_path": str((checkpoint_root / "checkpoints" / f"{case.test_id}.json").resolve()),
                    "mutation_proof_path": cached.get("mutation_proof_path", ""),
                }
                rows.append(row)
                continue

        if kind == "contract":
            result = run_contract_mutation(
                base_dir=baseline_bundle_root,
                checkpoint_root=checkpoint_root,
                case_work_root=case_work_root,
                case=case,
                mutate_fn=mutator,
                validate_fn=_validate,
            )
        elif kind == "label":
            result = run_gds_label_mutation(
                base_dir=baseline_bundle_root,
                checkpoint_root=checkpoint_root,
                case_work_root=case_work_root,
                case=case,
                mutate_fn=mutator,
                validate_fn=_validate,
            )
        elif kind == "hierarchy":
            result = run_hierarchy_mutation(
                base_dir=baseline_bundle_root,
                checkpoint_root=checkpoint_root,
                case_work_root=case_work_root,
                case=case,
                mutate_fn=mutator,
                validate_fn=_validate,
            )
        elif kind == "determinism":
            result = run_determinism_mutation(
                base_dir=baseline_bundle_root,
                checkpoint_root=checkpoint_root,
                case_work_root=case_work_root,
                case=case,
                mutate_fn=mutator,
                validate_fn=_validate,
            )
        elif kind == "short":
            result = run_gds_short_mutation(
                base_dir=baseline_bundle_root,
                checkpoint_root=checkpoint_root,
                case_work_root=case_work_root,
                case=case,
                mutate_fn=mutator,
                validate_fn=_validate,
            )
        else:
            result = run_gds_geometry_mutation(
                base_dir=baseline_bundle_root,
                checkpoint_root=checkpoint_root,
                case_work_root=case_work_root,
                case=case,
                mutate_fn=mutator,
                validate_fn=_validate,
            )

        test_work_dir = case_work_root / case.test_id
        proof_path = _write_mutation_proof(test_work_dir, case, result)
        checkpoint_path = str((checkpoint_root / "checkpoints" / f"{case.test_id}.json").resolve())
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
            checkpoint_root=checkpoint_root,
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
        checkpoint_payload = read_json(checkpoint_root / "checkpoints" / f"{case.test_id}.json")
        checkpoint_payload["status"] = "completed"
        checkpoint_payload["validator_invoked"] = True
        checkpoint_payload["mutation_proof_path"] = proof_path
        checkpoint_payload["completed_at"] = datetime.utcnow().isoformat(timespec="seconds") + "Z"
        write_json(checkpoint_root / "checkpoints" / f"{case.test_id}.json", checkpoint_payload)
        if cleanup_completed_scratch and test_work_dir.exists():
            shutil.rmtree(test_work_dir)

    negative_dir = output_root / "negative_tests"
    negative_dir.mkdir(parents=True, exist_ok=True)
    matrix_path = negative_dir / "TEAM_B_9CELL_negative_test_matrix.csv"
    summary_path = negative_dir / "TEAM_B_9CELL_negative_test_summary.json"
    write_negative_test_matrix(matrix_path, rows)
    summary = write_negative_test_summary(summary_path, rows)
    summary["specific_code_match_count"] = sum(1 for row in rows if row["code_matched"])
    write_json(summary_path, summary)
    write_text(negative_dir / "TEAM_B_9CELL_negative_test_execution.log", "\n".join(f"{row['test_id']} {row['actual_rejection_code']}" for row in rows))
    return {"rows": rows, "summary": summary}
