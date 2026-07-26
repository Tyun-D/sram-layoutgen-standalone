from __future__ import annotations

import argparse
import csv
import json
import subprocess
import shutil
import tempfile
from pathlib import Path
from typing import Any

import gdstk

REPO_ROOT = Path(__file__).resolve().parents[1]
import sys

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.openram_device_adapter import build_backend_context
from sram_layoutgen.openyield_adapter.openram_pnand2_adapter import generate_pnand2_cell
from sram_layoutgen.openyield_adapter.pnand2_source_lock import build_pnand2_source_lock
from sram_layoutgen.openyield_adapter.pnand2_verification_gate import (
    ValidationResult,
    _component_for_bbox,
    build_annotated_gds,
    build_geometry_report,
    build_review_atlas,
    build_source_reference_spice,
    canonicalize_pnand2_export,
    compare_determinism,
    compare_lvs_contract,
    direct_top_labels_report,
    export_raw_gds,
    run_recorded_drc,
    run_recorded_lvs,
    sha256_file,
    validate_bundle,
    verify_connectivity,
    write_csv,
    write_json,
    write_text,
)


TOP_NAME = "PNAND2_NW180_PW270_L50_FPDK45"


def _render_md(title: str, lines: list[str]) -> str:
    return "\n".join([f"# {title}", "", *lines, ""]).rstrip() + "\n"


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _run_single_generation(
    *,
    output_dir: Path,
    openram_root: Path,
    drc_deck: Path,
    lvs_deck: Path,
    klayout_bin: Path,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    raw_gds = output_dir / f"{TOP_NAME}_raw.gds"
    clean_gds = output_dir / f"{TOP_NAME}.gds"
    annotated_gds = output_dir / f"{TOP_NAME}_annotated.gds"
    review_atlas = output_dir / f"{TOP_NAME}_review_atlas.gds"
    with build_backend_context(openram_root) as ctx:
        result = generate_pnand2_cell(
            ctx,
            cell_name=TOP_NAME,
            requested_nmos_width_nm=180,
            requested_pmos_width_nm=270,
            requested_length_nm=50,
            source_instance_paths=["AND2.nand_gate", "WordlineDriver.nand_gate"],
            reference_configs=["AND2", "WordlineDriver"],
        )
        export_raw_gds(result.cell, raw_gds)
    export_meta = canonicalize_pnand2_export(raw_gds=raw_gds, top_name=TOP_NAME, pin_map=result.pin_map, output_gds=clean_gds)
    build_annotated_gds(clean_gds=clean_gds, top_name=TOP_NAME, device_layout=result.device_layout, output_gds=annotated_gds)
    build_review_atlas(clean_gds=clean_gds, annotated_gds=annotated_gds, top_name=TOP_NAME, output_gds=review_atlas)
    build_source_reference_spice(top_name=TOP_NAME, output_path=output_dir / "PNAND2_source_reference.spice")
    drc = run_recorded_drc(klayout_bin=klayout_bin, drc_deck=drc_deck, input_gds=clean_gds, top_name=TOP_NAME, output_dir=output_dir / "drc")
    lvs = run_recorded_lvs(
        klayout_bin=klayout_bin,
        lvs_deck=lvs_deck,
        clean_gds=clean_gds,
        top_name=TOP_NAME,
        source_reference_spice=output_dir / "PNAND2_source_reference.spice",
        extracted_spice=output_dir / "PNAND2_extracted.spice",
        output_dir=output_dir / "lvs",
    )
    return {
        "generation_result": result,
        "export_meta": export_meta,
        "drc": drc,
        "lvs": lvs,
        "clean_gds": clean_gds,
        "annotated_gds": annotated_gds,
        "review_atlas": review_atlas,
    }


def _write_negative_test_report(path: Path, rows: list[dict[str, Any]]) -> None:
    write_csv(path, rows)
    summary = {
        "negative_test_count": len(rows),
        "mutation_effective_count": sum(1 for row in rows if row["mutation_effective"]),
        "production_validator_invoked_count": sum(1 for row in rows if row["production_validator_name"]),
        "unexpected_negative_test_pass_count": sum(1 for row in rows if row["rejected_as_expected"] is False),
        "failed_to_reject_count": sum(1 for row in rows if row["rejected_as_expected"] is False),
        "negative_tests_passed": all(row["rejected_as_expected"] for row in rows),
    }
    write_json(path.parent / "PNAND2_negative_test_summary.json", summary)


def _mutate_add_debug_label(gds_path: Path) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == TOP_NAME)
    top.add(gdstk.Label("DEBUG", (0.2, 1.0), layer=11, texttype=2))
    lib.write_gds(gds_path)


def _mutate_remove_label(gds_path: Path, label_name: str) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == TOP_NAME)
    victims = [label for label in top.labels if str(label.text) == label_name]
    if victims:
        top.remove(*victims)
    lib.write_gds(gds_path)


def _mutate_add_label(gds_path: Path, label_name: str, origin: tuple[float, float]) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == TOP_NAME)
    top.add(gdstk.Label(label_name, origin, layer=11, texttype=2))
    lib.write_gds(gds_path)


def _mutate_off_grid(gds_path: Path) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == TOP_NAME)
    top.add(gdstk.rectangle((0.1234, 0.4567), (0.1884, 0.5217), layer=11, datatype=0))
    lib.write_gds(gds_path)


def _mutate_short(gds_path: Path, y: float) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == TOP_NAME)
    top.add(gdstk.rectangle((0.0, y - 0.0325), (0.75, y + 0.0325), layer=11, datatype=0))
    lib.write_gds(gds_path)


def _mutate_delete_bbox_region(gds_path: Path, bbox: dict[str, float]) -> None:
    lib = gdstk.read_gds(gds_path)
    target_cells = list(lib.cells)
    for cell in target_cells:
        survivors = []
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
                continue
            survivors.append(poly)
        if survivors:
            cell.remove(*survivors)
    lib.write_gds(gds_path)


def _run_negative_tests(
    *,
    base_dir: Path,
    drc_deck: Path,
    lvs_deck: Path,
    klayout_bin: Path,
) -> list[dict[str, Any]]:
    source_lock_path = base_dir / "PNAND2_source_lock.json"
    parameter_path = base_dir / "PNAND2_parameter_mapping.json"
    top_contract_path = base_dir / "PNAND2_top_pin_contract.json"
    device_inventory = _json(base_dir / "PNAND2_device_inventory.json")
    rows: list[dict[str, Any]] = []
    mutations = [
        ("openyield_commit_wrong", "PNAND2_source_lock.json", lambda d: _replace_json_value(source_lock_path, d, "authority_commit", "deadbeef"), "SOURCE_COMMIT_MISMATCH"),
        ("source_blob_wrong", "PNAND2_source_lock.json", lambda d: _replace_json_value(source_lock_path, d, "git_blob_sha", "deadbeef"), "SOURCE_BLOB_MISMATCH"),
        ("delete_A_pin", f"{TOP_NAME}.gds", lambda d: _mutate_remove_label(d / f"{TOP_NAME}.gds", "A"), "DIRECT_TOP_LABEL_CONTRACT_FAILED"),
        ("add_net1_top_label", f"{TOP_NAME}.gds", lambda d: _mutate_add_label(d / f"{TOP_NAME}.gds", "net1", (0.45, 0.25)), "DIRECT_TOP_LABEL_CONTRACT_FAILED"),
        ("top_pin_order_wrong", "PNAND2_top_pin_contract.json", lambda d: _replace_json_value(top_contract_path, d, "top_pin_order", ["A", "B", "Z", "VDD", "VSS"]), "TOP_PIN_ORDER_MISMATCH"),
        ("wn_90", "PNAND2_parameter_mapping.json", lambda d: _replace_json_value(parameter_path, d, "requested_nmos_width_nm", 90), "NMOS_WIDTH_MISMATCH"),
        ("wp_540", "PNAND2_parameter_mapping.json", lambda d: _replace_json_value(parameter_path, d, "requested_pmos_width_nm", 540), "PMOS_WIDTH_MISMATCH"),
        ("l_non_50", "PNAND2_parameter_mapping.json", lambda d: _replace_json_value(parameter_path, d, "requested_length_nm", 60), "LENGTH_MISMATCH"),
        ("delete_one_pmos", f"{TOP_NAME}.gds", lambda d: _mutate_delete_bbox_region(d / f"{TOP_NAME}.gds", device_inventory["device_layout"][0]["terminal_bboxes"]["G"]), "STRICT_LVS_FAILED"),
        ("delete_one_nmos", f"{TOP_NAME}.gds", lambda d: _mutate_delete_bbox_region(d / f"{TOP_NAME}.gds", device_inventory["device_layout"][2]["terminal_bboxes"]["G"]), "STRICT_LVS_FAILED"),
        ("nmos_parallel_contract", "PNAND2_source_reference.spice", lambda d: _replace_reference_lines(d / "PNAND2_source_reference.spice", {"Mpnand2_nmos1": "Mpnand2_nmos1 Z B VSS VSS NMOS_VTG W=180n L=50n", "Mpnand2_nmos2": "Mpnand2_nmos2 Z A VSS VSS NMOS_VTG W=180n L=50n"}), "TOPOLOGY_MISMATCH_NMOS_NOT_SERIES"),
        ("pmos_series_contract", "PNAND2_source_reference.spice", lambda d: _replace_reference_lines(d / "PNAND2_source_reference.spice", {"Mpnand2_pmos1": "Mpnand2_pmos1 netp A VDD VDD PMOS_VTG W=270n L=50n", "Mpnand2_pmos2": "Mpnand2_pmos2 Z B netp VDD PMOS_VTG W=270n L=50n"}), "TOPOLOGY_MISMATCH_PMOS_NOT_PARALLEL"),
        ("gate_binding_swap", f"{TOP_NAME}.gds", lambda d: _mutate_swap_a_b_labels(d / f"{TOP_NAME}.gds"), "STRICT_LVS_FAILED"),
        ("net1_z_short", f"{TOP_NAME}.gds", lambda d: _mutate_short_z_to_net1(d / f"{TOP_NAME}.gds"), "UNEXPECTED_NET_MERGE_Z_NET1"),
        ("net1_vss_short", f"{TOP_NAME}.gds", lambda d: _mutate_short_net1_to_vss(d / f"{TOP_NAME}.gds"), "STRICT_LVS_FAILED"),
        ("vdd_vss_short", f"{TOP_NAME}.gds", lambda d: _mutate_short_vdd_to_vss(d / f"{TOP_NAME}.gds"), "VDD_VSS_SHORT"),
        ("pmos_body_wrong_contract", "PNAND2_source_reference.spice", lambda d: _replace_reference_lines(d / "PNAND2_source_reference.spice", {"Mpnand2_pmos1": "Mpnand2_pmos1 Z A VDD VSS PMOS_VTG W=270n L=50n"}), "PMOS_BULK_NOT_CONNECTED_TO_VDD"),
        ("nmos_body_wrong_contract", "PNAND2_source_reference.spice", lambda d: _replace_reference_lines(d / "PNAND2_source_reference.spice", {"Mpnand2_nmos1": "Mpnand2_nmos1 Z B net1 VDD NMOS_VTG W=180n L=50n"}), "NMOS_BULK_NOT_CONNECTED_TO_VSS"),
        ("delete_contact_via", f"{TOP_NAME}.gds", lambda d: _mutate_delete_bbox_region(d / f"{TOP_NAME}.gds", {"lx": 0.18, "by": 0.35, "rx": 0.29, "uy": 0.48}), "STRICT_LVS_FAILED"),
        ("edge_corner_short", f"{TOP_NAME}.gds", lambda d: _mutate_short(d / f"{TOP_NAME}.gds", 0.70), "STRICT_LVS_FAILED"),
        ("off_grid_geometry", f"{TOP_NAME}.gds", lambda d: _mutate_off_grid(d / f"{TOP_NAME}.gds"), "DRC_FAILED"),
        ("debug_label", f"{TOP_NAME}.gds", lambda d: _mutate_add_debug_label(d / f"{TOP_NAME}.gds"), "DIRECT_TOP_LABEL_CONTRACT_FAILED"),
        ("determinism_b_mutation", f"determinism_B/{TOP_NAME}.gds", lambda d: _mutate_add_debug_label(d / "determinism_B" / f"{TOP_NAME}.gds"), "DETERMINISM_FAILED"),
    ]
    for name, input_rel, mutator, expected_code in mutations:
        with tempfile.TemporaryDirectory(prefix=f"pnand2_neg_{name}_") as tmp:
            tmp_dir = Path(tmp) / "bundle"
            shutil.copytree(base_dir, tmp_dir)
            baseline_input_path = tmp_dir / input_rel
            baseline_input_sha = sha256_file(baseline_input_path)
            mutator(tmp_dir)
            mutated_input_path = tmp_dir / input_rel
            mutated_input_sha = sha256_file(mutated_input_path)
            mutation_effective = baseline_input_sha != mutated_input_sha
            validation = validate_bundle(bundle_dir=tmp_dir, klayout_bin=klayout_bin, drc_deck=drc_deck, lvs_deck=lvs_deck, top_name=TOP_NAME)
            actual_code = validation.rejection_codes[0] if validation.rejection_codes else ""
            rows.append(
                {
                    "mutation_name": name,
                    "baseline_input_path": str(baseline_input_path),
                    "baseline_input_sha256": baseline_input_sha,
                    "mutated_input_path": str(mutated_input_path),
                    "mutated_input_sha256": mutated_input_sha,
                    "mutation_effective": mutation_effective,
                    "production_validator_name": "validate_bundle",
                    "production_validator_input_path": str(mutated_input_path),
                    "production_validator_input_sha256": mutated_input_sha,
                    "validator_cache_disabled": True,
                    "expected_rejection_code": expected_code,
                    "actual_rejection_code": actual_code,
                    "actual_rejection_codes": "|".join(validation.rejection_codes),
                    "rejected": validation.passed is False,
                    "rejected_as_expected": mutation_effective and validation.passed is False and expected_code in validation.rejection_codes,
                }
            )
    return rows


def _replace_json_value(source_path: Path, tmp_dir: Path, key: str, value: Any) -> None:
    target = tmp_dir / source_path.relative_to(source_path.parents[1]) if source_path.is_absolute() else tmp_dir / source_path.name
    if not target.exists():
        target = tmp_dir / source_path.name
    payload = _json(target)
    payload[key] = value
    write_json(target, payload)


def _rewrite_reference_spice(path: Path, replacement_line: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    new_lines = []
    replaced = False
    for line in lines:
        if not replaced and line.startswith("Mpnand2_"):
            new_lines.append(replacement_line)
            replaced = True
        else:
            new_lines.append(line)
    write_text(path, "\n".join(new_lines))


def _replace_reference_lines(path: Path, replacements: dict[str, str]) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    new_lines = []
    for line in lines:
        key = line.split()[0] if line.strip() else ""
        new_lines.append(replacements.get(key, line))
    write_text(path, "\n".join(new_lines))


def _mutate_swap_a_b_labels(gds_path: Path) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == TOP_NAME)
    a = next(label for label in top.labels if str(label.text) == "A")
    b = next(label for label in top.labels if str(label.text) == "B")
    a.origin, b.origin = b.origin, a.origin
    lib.write_gds(gds_path)


def _bridge_components(gds_path: Path, left_label: str, right_label: str) -> None:
    from sram_layoutgen.openyield_adapter.physical_connectivity_extractor import extract_physical_connectivity

    graph = extract_physical_connectivity(gds_path, TOP_NAME)
    label_to_component = {}
    for hit in graph["label_hits"]:
        if hit["text"] in {left_label, right_label} and hit["shape_ids"]:
            shape_id = hit["shape_ids"][0]
            for component in graph["components"]:
                if shape_id in component["members"]:
                    label_to_component[hit["text"]] = component["component_id"]
                    break
    component_rects = {}
    lookup = {component["component_id"]: component for component in graph["components"]}
    for name, comp_id in label_to_component.items():
        rects = []
        for rect in graph["rectangles"]["m1"]:
            if rect["rect_id"] in lookup[comp_id]["members"]:
                rects.append(rect["bbox"])
        component_rects[name] = rects
    left_rect = component_rects[left_label][0]
    right_rect = component_rects[right_label][0]
    y = round(((left_rect[1] + left_rect[3]) * 0.5 + (right_rect[1] + right_rect[3]) * 0.5) * 0.5 / 0.0025) * 0.0025
    width = 0.065
    lx = min(left_rect[0], right_rect[0])
    rx = max(left_rect[2], right_rect[2])
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == TOP_NAME)
    top.add(gdstk.rectangle((lx, y - width / 2), (rx, y + width / 2), layer=11, datatype=0))
    lib.write_gds(gds_path)


def _component_rect_for_bbox(gds_path: Path, bbox: dict[str, float], layers: set[str]) -> tuple[str, list[float]]:
    from sram_layoutgen.openyield_adapter.physical_connectivity_extractor import extract_physical_connectivity

    graph = extract_physical_connectivity(gds_path, TOP_NAME)
    component_id = _component_for_bbox(graph, bbox, layers)
    if component_id is None:
        raise RuntimeError(f"unable to resolve component for bbox {bbox}")
    component = next(item for item in graph["components"] if item["component_id"] == component_id)
    members = set(component["members"])
    rect = next(rect["bbox"] for rect in graph["rectangles"]["m1"] if rect["rect_id"] in members)
    return component_id, rect


def _bridge_bbox_components(gds_path: Path, left_bbox: dict[str, float], right_bbox: dict[str, float], *, width: float = 0.065) -> None:
    _, left_rect = _component_rect_for_bbox(gds_path, left_bbox, {"m1", "m2", "active_segment", "poly"})
    _, right_rect = _component_rect_for_bbox(gds_path, right_bbox, {"m1", "m2", "active_segment", "poly"})
    y = round(((left_rect[1] + left_rect[3]) * 0.5 + (right_rect[1] + right_rect[3]) * 0.5) * 0.5 / 0.0025) * 0.0025
    lx = min(left_rect[0], right_rect[0])
    rx = max(left_rect[2], right_rect[2])
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == TOP_NAME)
    top.add(gdstk.rectangle((lx, y - width / 2), (rx, y + width / 2), layer=11, datatype=0))
    lib.write_gds(gds_path)


def _mutate_short_z_to_net1(gds_path: Path) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == TOP_NAME)
    # Add a real active contact on the shared NMOS diffusion, then bridge it to the Z metal.
    top.add(gdstk.rectangle((0.3075, 0.1825), (0.3725, 0.2475), layer=10, datatype=0))
    top.add(gdstk.rectangle((0.3075, 0.1825), (0.3725, 0.2475), layer=11, datatype=0))
    top.add(gdstk.rectangle((0.34, 0.1825), (0.685, 0.2475), layer=11, datatype=0))
    lib.write_gds(gds_path)


def _mutate_short_vdd_to_vss(gds_path: Path) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == TOP_NAME)
    # A vertical M1 strap that overlaps both rails.
    top.add(gdstk.rectangle((0.6925, 0.0), (0.7575, 1.8525), layer=11, datatype=0))
    lib.write_gds(gds_path)


def _mutate_short_net1_to_vss(gds_path: Path) -> None:
    lib = gdstk.read_gds(gds_path)
    top = next(cell for cell in lib.cells if cell.name == TOP_NAME)
    # Add a real active contact on the shared NMOS diffusion, then bridge it down to the VSS rail.
    top.add(gdstk.rectangle((0.3075, 0.1825), (0.3725, 0.2475), layer=10, datatype=0))
    top.add(gdstk.rectangle((0.3075, 0.1825), (0.3725, 0.2475), layer=11, datatype=0))
    top.add(gdstk.rectangle((0.125, 0.0), (0.34, 0.2475), layer=11, datatype=0))
    lib.write_gds(gds_path)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--openyield-root", default="/data1/qujh/work/external/OpenYield")
    parser.add_argument("--openram-root", default="/data1/qujh/OpenRAM")
    parser.add_argument("--out-dir", default="outputs/TeamB_PNAND2_reference_demo/current_supported_config")
    parser.add_argument("--klayout-bin", default="/usr/bin/klayout")
    parser.add_argument("--drc-deck", default="technology/freepdk45/tech/freepdk45.lydrc")
    parser.add_argument("--lvs-deck", default="technology/freepdk45/tech/freepdk45.lylvs")
    parser.add_argument("--single-run-dir", default="")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_dir = (repo_root / args.out_dir).resolve()
    openyield_root = Path(args.openyield_root).resolve()
    openram_root = Path(args.openram_root).resolve()
    drc_deck = (repo_root / args.drc_deck).resolve()
    lvs_deck = (repo_root / args.lvs_deck).resolve()
    klayout_bin = Path(args.klayout_bin).resolve()

    if args.single_run_dir:
        _run_single_generation(
            output_dir=Path(args.single_run_dir).resolve(),
            openram_root=openram_root,
            drc_deck=drc_deck,
            lvs_deck=lvs_deck,
            klayout_bin=klayout_bin,
        )
        return 0

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    source_lock = build_pnand2_source_lock(openyield_root)
    generation = _run_single_generation(output_dir=out_dir, openram_root=openram_root, drc_deck=drc_deck, lvs_deck=lvs_deck, klayout_bin=klayout_bin)
    result = generation["generation_result"]

    write_json(out_dir / "PNAND2_source_lock.json", source_lock)
    write_text(
        out_dir / "PNAND2_source_lock.md",
        _render_md(
            "PNAND2 Source Lock",
            [
                f"- authority_repository: `{source_lock['authority_repository']}`",
                f"- authority_commit: `{source_lock['authority_commit']}`",
                f"- source_relative_path: `{source_lock['source_relative_path']}`",
                f"- git_blob_sha: `{source_lock['git_blob_sha']}`",
                f"- source_snapshot_sha256: `{source_lock['source_snapshot_sha256']}`",
                f"- topology_digest: `{source_lock['topology_digest']}`",
            ],
        ),
    )
    write_text(out_dir / "PNAND2_source_snapshot.py", subprocess_output(["git", "-C", str(openyield_root), "show", f"{source_lock['authority_commit']}:{source_lock['source_relative_path']}"]))
    write_json(out_dir / "PNAND2_pin_map.json", result.pin_map)
    write_json(out_dir / "PNAND2_top_pin_contract.json", {"top_pin_order": ["VDD", "VSS", "A", "B", "Z"], "top_pin_names": ["VDD", "VSS", "A", "B", "Z"]})
    write_json(out_dir / "PNAND2_parameter_mapping.json", result.parameter_mapping)
    write_json(out_dir / "PNAND2_device_inventory.json", {"device_layout": result.device_layout, "source_devices": source_lock["device_inventory"]})
    label_report = direct_top_labels_report(generation["clean_gds"], TOP_NAME)
    write_json(out_dir / "PNAND2_direct_top_label_report.json", label_report)
    connectivity = verify_connectivity(clean_gds=generation["clean_gds"], top_name=TOP_NAME, pin_map=result.pin_map, device_layout=result.device_layout)
    write_json(out_dir / "PNAND2_connectivity_graph.json", connectivity["graph"])
    write_json(out_dir / "PNAND2_layout_quality_metrics.json", build_geometry_report(generation["clean_gds"], TOP_NAME))
    geometry = _json(out_dir / "PNAND2_layout_quality_metrics.json")
    write_json(out_dir / "PNAND2_geometry_fingerprint.json", geometry["geometry_fingerprint"])
    endpoint_rows = []
    for device in result.device_layout:
        for terminal_name, bbox in device["terminal_bboxes"].items():
            endpoint_rows.append(
                {
                    "device_name": device["device_name"],
                    "terminal_name": terminal_name,
                    "bbox": json.dumps(bbox, sort_keys=True),
                    "gate_net": device["gate_net"],
                    "bulk_net": device["bulk_net"],
                }
            )
    write_csv(out_dir / "PNAND2_endpoint_mapping.csv", endpoint_rows)
    write_csv(
        out_dir / "PNAND2_contact_pairs.csv",
        [
            {"pair_name": "P1_D_Z", "left": "P1.D", "right": "TOP.Z"},
            {"pair_name": "N2_S_VSS", "left": "N2.S", "right": "TOP.VSS"},
        ],
    )
    lvs_contract = compare_lvs_contract(
        source_lock=source_lock,
        source_reference=out_dir / "PNAND2_source_reference.spice",
        extracted_spice=out_dir / "PNAND2_extracted.spice",
        lvsdb=Path(generation["lvs"]["lvsdb_path"]),
        top_name=TOP_NAME,
    )
    write_json(out_dir / "lvs" / "PNAND2_lvs_contract_report.json", lvs_contract)
    write_json(out_dir / "drc" / "PNAND2_drc_summary.json", generation["drc"])
    write_json(out_dir / "PNAND2_machine_gate.json", {})

    det_a = out_dir / "determinism_A"
    det_b = out_dir / "determinism_B"
    for det_dir in (det_a, det_b):
        subprocess.run(
            [
                sys.executable,
                str(Path(__file__).resolve()),
                "--repo-root",
                str(repo_root),
                "--openyield-root",
                str(openyield_root),
                "--openram-root",
                str(openram_root),
                "--klayout-bin",
                str(klayout_bin),
                "--drc-deck",
                str(drc_deck.relative_to(repo_root)),
                "--lvs-deck",
                str(lvs_deck.relative_to(repo_root)),
                "--single-run-dir",
                str(det_dir),
            ],
            check=True,
            cwd=repo_root,
        )
    determinism = compare_determinism(det_a, det_b, TOP_NAME)
    write_json(out_dir / "PNAND2_determinism.json", determinism)

    negative_rows = _run_negative_tests(base_dir=out_dir, drc_deck=drc_deck, lvs_deck=lvs_deck, klayout_bin=klayout_bin)
    _write_negative_test_report(out_dir / "negative_tests" / "PNAND2_negative_test_matrix.csv", negative_rows)

    validation = validate_bundle(bundle_dir=out_dir, klayout_bin=klayout_bin, drc_deck=drc_deck, lvs_deck=lvs_deck, top_name=TOP_NAME)
    machine_gate = dict(validation.machine_gate)
    machine_gate["negative_tests_passed"] = all(row["rejected_as_expected"] for row in negative_rows)
    machine_gate["deterministic_A_B_byte_identical"] = determinism["deterministic_A_B_byte_identical"]
    machine_gate["strict_lvs_contract_passed"] = lvs_contract["strict_lvs_contract_passed"]
    machine_gate["drc_marker_count"] = generation["drc"]["marker_count"]
    status = "MACHINE_VERIFIED_OWNER_A_DEMO_HUMAN_REVIEW_REQUIRED" if all(
        [
            machine_gate["source_lock_complete"],
            machine_gate["parameter_binding_closed"],
            machine_gate["requested_actual_parameter_match"],
            machine_gate["top_pin_contract_exact"],
            machine_gate["internal_net_not_exposed"],
            machine_gate["device_count_exact"],
            machine_gate["topology_match"],
            machine_gate["body_tie_match"],
            machine_gate["connectivity_passed"],
            machine_gate["drc_marker_count"] == 0,
            machine_gate["strict_lvs_contract_passed"],
            machine_gate["deterministic_A_B_byte_identical"],
            machine_gate["negative_tests_passed"],
        ]
    ) else "FAIL_INTERNAL_VALIDATION_NOT_CLOSED"
    write_json(out_dir / "PNAND2_machine_gate.json", machine_gate)

    file_index_rows = []
    for path in sorted(out_dir.rglob("*")):
        if path.is_file():
            file_index_rows.append({"relative_path": str(path.relative_to(out_dir)), "sha256": sha256_file(path), "bytes": path.stat().st_size})
    write_csv(out_dir / "PNAND2_REFERENCE_IMPLEMENTATION_FILE_INDEX.csv", file_index_rows)
    write_json(
        out_dir / "PNAND2_REFERENCE_IMPLEMENTATION_STATUS.json",
        {
            "top_name": TOP_NAME,
            "status": status,
            "machine_gate": machine_gate,
            "clean_gds_sha256": sha256_file(out_dir / f"{TOP_NAME}.gds"),
            "drc_passed": generation["drc"]["drc_passed"],
            "lvs_passed": lvs_contract["strict_lvs_contract_passed"],
            "connectivity_passed": connectivity["connectivity_passed"],
            "negative_tests_passed": machine_gate["negative_tests_passed"],
        },
    )
    write_text(
        out_dir / "PNAND2_REFERENCE_IMPLEMENTATION_TECHNICAL_REPORT.md",
        _render_md(
            "PNAND2 Reference Implementation",
            [
                "- route_selected: `Route A / OpenRAM native pnand2 wrapper`",
                "- source_lock: `standard_cell.py blob e3269a942e18931d5a75eda7252a8abda6540bf5 at commit 1c34428d8b913963c4971d093b1a7c2df97a2509`",
                "- requested_parameters_nm: `Wn=180 Wp=270 L=50`",
                f"- actual_parameters_nm: `Wn={result.parameter_mapping['actual_nmos_width_nm']} Wp={result.parameter_mapping['actual_pmos_width_nm']} L={result.parameter_mapping['actual_length_nm']}`",
                f"- drc_marker_count: `{generation['drc']['marker_count']}`",
                f"- strict_lvs_contract_passed: `{lvs_contract['strict_lvs_contract_passed']}`",
                f"- connectivity_passed: `{connectivity['connectivity_passed']}`",
                f"- deterministic_A_B_byte_identical: `{determinism['deterministic_A_B_byte_identical']}`",
                f"- negative_tests_passed: `{machine_gate['negative_tests_passed']}`",
                "- human_review_pending: `true`",
            ],
        ),
    )
    write_json(
        out_dir / "human_review" / "PNAND2_HUMAN_REVIEW_INPUT_LOCK.json",
        {
            "clean_gds": str((out_dir / f"{TOP_NAME}.gds").resolve()),
            "annotated_gds": str((out_dir / f"{TOP_NAME}_annotated.gds").resolve()),
            "review_atlas": str((out_dir / f"{TOP_NAME}_review_atlas.gds").resolve()),
            "drc_lyrdb": str((out_dir / "drc" / "PNAND2.lyrdb").resolve()),
            "clean_gds_sha256_before_review": sha256_file(out_dir / f"{TOP_NAME}.gds"),
        },
    )
    write_csv(
        out_dir / "human_review" / "PNAND2_HUMAN_REVIEW_CHECKLIST.csv",
        [{"item": item} for item in ["PMOS upper row", "NMOS lower row", "PMOS parallel", "NMOS series", "A/B gate binding", "Z merge point", "net1 internal node", "body/well ties", "pin access", "no internal labels"]],
    )
    write_text(
        out_dir / "human_review" / "PNAND2_HUMAN_REVIEW_REPORT.md",
        _render_md(
            "PNAND2 Human Review",
            [
                "- Open the clean GDS, annotated GDS, review atlas, and DRC database in KLayout.",
                "- Confirm PMOS on top, NMOS on bottom, PMOS parallel, NMOS series, correct A/B gate binding, visible net1 internal node, legal pin access, and no leaked internal labels.",
                f"- clean_gds_sha256_before_review: `{sha256_file(out_dir / f'{TOP_NAME}.gds')}`",
                "- Final status must remain `MACHINE_VERIFIED_OWNER_A_DEMO_HUMAN_REVIEW_REQUIRED` until manual review is completed.",
            ],
        ),
    )
    write_csv(
        out_dir / "human_review" / "PNAND2_HUMAN_REVIEW_SCREENSHOT_INDEX.csv",
        [{"filename": name} for name in ["01_clean_full.png", "02_annotated_full.png", "03_active_poly.png", "04_m1_contacts.png", "05_power_rails.png", "06_A_B_pin_access.png", "07_Z_and_net1.png", "08_well_body.png", "09_drc_database.png", "10_reference_comparison.png"]],
    )
    print(json.dumps({"status": status, "clean_gds_sha256": sha256_file(out_dir / f"{TOP_NAME}.gds")}, ensure_ascii=False))
    return 0


def subprocess_output(command: list[str]) -> str:
    return __import__("subprocess").check_output(command, text=True)


if __name__ == "__main__":
    raise SystemExit(main())
