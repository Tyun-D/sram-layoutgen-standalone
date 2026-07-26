from __future__ import annotations

import argparse
import csv
import hashlib
import json
import tarfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
import sys

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.delay_chain_generator import generate_delay_chain_layout
from sram_layoutgen.openyield_adapter.delay_chain_negative_regressions import run_delay_chain_negative_regressions
from sram_layoutgen.openyield_adapter.delay_chain_source_lock import MODULE_SPECS
from sram_layoutgen.openyield_adapter.delay_chain_verification_gate import build_delay_chain_production_gate, validate_delay_chain_bundle
from sram_layoutgen.openyield_adapter.teamb_composite_helper import read_json, write_json, write_text


MODULE_ORDER = ["wen_delay_chain", "delay_chain"]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _required_true_keys() -> list[str]:
    return [
        "source_lock_complete",
        "parameter_binding_closed",
        "top_pin_contract_exact",
        "internal_net_not_exposed",
        "driver_count_exact",
        "load_count_exact",
        "child_count_exact",
        "loads_per_stage_exact",
        "stage_order_exact",
        "topology_match",
        "output_polarity_match",
        "intentional_floating_outputs_exact",
        "hierarchy_closure_passed",
        "child_immutability_passed",
        "connectivity_passed",
        "foreign_net_passed",
        "power_rail_continuity_passed",
        "row_abutment_policy_passed",
        "strict_source_derived_structural_gate_passed",
        "deterministic_A_B_byte_identical",
        "negative_tests_passed",
        "review_artifacts_complete",
    ]


def _rows_from_disk(out_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for module_name in MODULE_ORDER:
        cell_dir = out_root / module_name
        if not (cell_dir / "machine_gate.json").exists() or not (cell_dir / "clean.gds").exists():
            continue
        machine_gate = read_json(cell_dir / "machine_gate.json")
        negative_path = cell_dir / "negative_tests" / f"{module_name}_negative_test_summary.json"
        drc_path = cell_dir / "drc" / f"{module_name}_drc_summary.json"
        negative_summary = (
            read_json(negative_path)
            if negative_path.exists()
            else {"negative_tests_passed": machine_gate.get("negative_tests_passed", False), "total_count": 0}
        )
        drc_summary = read_json(drc_path) if drc_path.exists() else {"marker_count": machine_gate.get("drc_marker_count", -1)}
        rows.append(
            {
                "module_name": module_name,
                "cell_dir": str(cell_dir.resolve()),
                "clean_gds_sha256": _sha256(cell_dir / "clean.gds"),
                "machine_gate": machine_gate,
                "negative_summary": negative_summary,
                "drc_summary": drc_summary,
            }
        )
    return rows


def recompute_final_status(out_root: Path) -> dict[str, Any]:
    modules = []
    rows_from_disk = _rows_from_disk(out_root / "current_supported_config")
    for row in rows_from_disk:
        gate = row["machine_gate"]
        required_true = all(gate.get(key) is True for key in _required_true_keys())
        modules.append(
            {
                "module_name": row["module_name"],
                "clean_gds_path": str((Path(row["cell_dir"]) / "clean.gds").resolve()),
                "clean_gds_sha256": row["clean_gds_sha256"],
                "machine_gate_path": str((Path(row["cell_dir"]) / "machine_gate.json").resolve()),
                "all_required_gates_true": required_true and int(gate.get("drc_marker_count", -1)) == 0,
                "negative_tests_passed": row["negative_summary"]["negative_tests_passed"],
                "negative_test_total_count": row["negative_summary"].get("total_count", 0),
                "drc_marker_count": row["drc_summary"]["marker_count"],
                "connectivity_passed": gate["connectivity_passed"],
                "foreign_net_passed": gate["foreign_net_passed"],
                "child_immutability_passed": gate["child_immutability_passed"],
                "deterministic_A_B_byte_identical": gate["deterministic_A_B_byte_identical"],
                "intentional_floating_outputs_exact": gate["intentional_floating_outputs_exact"],
                "power_rail_continuity_passed": gate["power_rail_continuity_passed"],
                "row_abutment_policy_passed": gate["row_abutment_policy_passed"],
                "review_artifacts_complete": gate["review_artifacts_complete"],
            }
        )
    payload = {
        "module_order": MODULE_ORDER,
        "modules": modules,
        "all_modules_green": len(modules) == len(MODULE_ORDER) and all(
            row["all_required_gates_true"] and row["negative_tests_passed"] and row["drc_marker_count"] == 0 for row in modules
        ),
    }
    write_json(out_root / "DELAY_CHAIN_FINAL_STATUS.json", payload)
    md_lines = [
        "# Delay Chain Final Status",
        "",
        f"- all_modules_green: `{payload['all_modules_green']}`",
        "",
        "| module | all_required_gates_true | negative_tests_passed | drc_marker_count | floating_exact | clean_gds_sha256 |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for row in modules:
        md_lines.append(
            f"| {row['module_name']} | {row['all_required_gates_true']} | {row['negative_tests_passed']} | "
            f"{row['drc_marker_count']} | {row['intentional_floating_outputs_exact']} | `{row['clean_gds_sha256']}` |"
        )
    write_text(out_root / "DELAY_CHAIN_FINAL_STATUS.md", "\n".join(md_lines) + "\n")
    return payload


def _write_report(out_root: Path, rows: list[dict[str, Any]]) -> None:
    lines = ["# Team B Delay Chain Technical Report", ""]
    for row in rows:
        selected = read_json(Path(row["cell_dir"]) / "selected_floorplan.json")
        layout_metrics = read_json(Path(row["cell_dir"]) / "layout_quality_metrics.json")
        floating = read_json(Path(row["cell_dir"]) / "intentional_floating_output_report.json")
        lines.extend(
            [
                f"## {row['module_name']}",
                "",
                f"- clean_gds_sha256: `{row['clean_gds_sha256']}`",
                f"- selected_floorplan: `{selected['selected_candidate_id']}`",
                f"- drc_marker_count: `{row['machine_gate']['drc_marker_count']}`",
                f"- negative_tests_passed: `{row['machine_gate']['negative_tests_passed']}`",
                f"- area: `{layout_metrics['area']}`",
                f"- row_count: `{layout_metrics['row_count']}`",
                f"- estimated_signal_wire_length: `{layout_metrics['estimated_signal_wire_length']}`",
                (
                    f"- floating_outputs: `{floating['intentional_floating_output_count']}/"
                    f"{floating['expected_intentional_floating_output_count']}`"
                ),
                "",
            ]
        )
    write_text(out_root / "DELAY_CHAIN_TECHNICAL_REPORT.md", "\n".join(lines))

    rels = [
        "clean.gds",
        "annotated.gds",
        "review_atlas.gds",
        "review_atlas_stage_roles.gds",
        "review_atlas_stage_nets.gds",
        "review_atlas_floating_load_outputs.gds",
        "review_atlas_pin_access.gds",
        "review_atlas_power_rails.gds",
        "machine_gate.json",
        "source_lock.json",
        "parameter_mapping.json",
        "instance_binding.csv",
        "instance_role_manifest.json",
        "stage_topology.json",
        "intentional_floating_output_report.json",
        "stage_endpoint_contract.json",
        "stage_connectivity_matrix.csv",
        "physical_connectivity_report.json",
        "floorplan_candidates.json",
        "floorplan_candidate_comparison.csv",
        "selected_floorplan.json",
        "layout_quality_metrics.json",
        "power_rail_report.json",
        "vertical_row_abutment_report.json",
        "poly_metal_active_report.json",
    ]
    with (out_root / "DELAY_CHAIN_FILE_INDEX.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["module_name", "artifact_path", "sha256"])
        writer.writeheader()
        for row in rows:
            base = Path(row["cell_dir"])
            for rel in rels:
                path = base / rel
                if path.exists():
                    writer.writerow({"module_name": row["module_name"], "artifact_path": str(path.resolve()), "sha256": _sha256(path)})

    sha_lines = []
    for row in rows:
        base = Path(row["cell_dir"])
        for path in sorted(base.rglob("*")):
            if path.is_file():
                sha_lines.append(f"{_sha256(path)}  {path.resolve()}")
    write_text(out_root / "DELAY_CHAIN_SHA256SUMS.txt", "\n".join(sha_lines) + "\n")


def _package_tarball(repo_root: Path, package_path: Path, include_paths: list[Path]) -> dict[str, Any]:
    package_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(package_path, "w:gz") as tar:
        for path in include_paths:
            if path.exists():
                tar.add(path, arcname=str(path.relative_to(repo_root)))
    sha = _sha256(package_path)
    write_text(Path(str(package_path) + ".sha256"), f"{sha}  {package_path.name}\n")
    return {"path": str(package_path), "sha256": sha, "size_bytes": package_path.stat().st_size}


def _package_outputs(repo_root: Path, out_root: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    review_include = [
        out_root / "DELAY_CHAIN_FINAL_STATUS.json",
        out_root / "DELAY_CHAIN_FINAL_STATUS.md",
        out_root / "DELAY_CHAIN_TECHNICAL_REPORT.md",
        out_root / "DELAY_CHAIN_FILE_INDEX.csv",
        out_root / "DELAY_CHAIN_SHA256SUMS.txt",
    ]
    evidence_include = list(review_include)
    for row in rows:
        cell_dir = Path(row["cell_dir"])
        review_include.extend(
            [
                cell_dir / "clean.gds",
                cell_dir / "annotated.gds",
                cell_dir / "review_atlas.gds",
                cell_dir / "review_atlas_stage_roles.gds",
                cell_dir / "review_atlas_stage_nets.gds",
                cell_dir / "review_atlas_floating_load_outputs.gds",
                cell_dir / "review_atlas_pin_access.gds",
                cell_dir / "review_atlas_power_rails.gds",
                cell_dir / "machine_gate.json",
                cell_dir / "source_lock.json",
                cell_dir / "stage_topology.json",
                cell_dir / "instance_binding.csv",
                cell_dir / "intentional_floating_output_report.json",
                cell_dir / "stage_connectivity_matrix.csv",
                cell_dir / "floorplan_candidate_comparison.csv",
                cell_dir / "selected_floorplan.json",
                cell_dir / "layout_quality_metrics.json",
                cell_dir / "negative_tests" / f"{row['module_name']}_negative_test_summary.json",
                cell_dir / "human_review",
            ]
        )
        review_include.extend(list((cell_dir / "drc").glob("*")))
        evidence_include.append(cell_dir)
    return {
        "human_review_package": _package_tarball(
            repo_root,
            Path("/data1/qujh/TEAM_B_DELAY_CHAIN_HUMAN_REVIEW_PACKAGE_LATEST.tar.gz"),
            review_include,
        ),
        "full_evidence_package": _package_tarball(
            repo_root,
            Path("/data1/qujh/TEAM_B_DELAY_CHAIN_FULL_EVIDENCE_PACKAGE_LATEST.tar.gz"),
            evidence_include,
        ),
    }


def _run_one_module(
    repo_root: Path,
    out_root: Path,
    module_name: str,
    openyield_root: Path,
    klayout_bin: Path,
    drc_deck: Path,
    *,
    run_negative_tests: bool,
    resume_negative_tests: bool,
) -> dict[str, Any]:
    cell_dir = out_root / module_name
    cell_dir.mkdir(parents=True, exist_ok=True)
    spec = MODULE_SPECS[module_name]
    generate_delay_chain_layout(
        repo_root=repo_root,
        module_name=module_name,
        top_cell_name=spec["top_cell_name"],
        top_pin_order=spec["top_pin_order"],
        stage_count=spec["stage_count"],
        loads_per_stage=spec["loads_per_stage"],
        child_variant=spec["child_variant"],
        output_polarity=spec["output_polarity"],
        floorplan_policy="driver_spine_with_load_clusters",
        output_dir=cell_dir,
        klayout_bin=klayout_bin,
        drc_deck=drc_deck,
    )
    build = build_delay_chain_production_gate(
        repo_root=repo_root,
        cell_dir=cell_dir,
        module_name=module_name,
        openyield_root=openyield_root,
        klayout_bin=klayout_bin,
        drc_deck=drc_deck,
    )
    if run_negative_tests:
        negative = run_delay_chain_negative_regressions(
            module_name=module_name,
            baseline_clean_gds=cell_dir / "clean.gds",
            production_validator={
                "repo_root": repo_root,
                "openyield_root": openyield_root,
                "klayout_bin": klayout_bin,
                "drc_deck": drc_deck,
                "validate_fn": validate_delay_chain_bundle,
            },
            output_dir=cell_dir / "negative_tests",
            resume=resume_negative_tests,
        )
        machine_gate = read_json(cell_dir / "machine_gate.json")
        machine_gate["negative_tests_passed"] = negative["summary"]["negative_tests_passed"]
        write_json(cell_dir / "machine_gate.json", machine_gate)
        build["machine_gate"] = machine_gate
    return {
        "module_name": module_name,
        "cell_dir": str(cell_dir.resolve()),
        "clean_gds_sha256": _sha256(cell_dir / "clean.gds"),
        "machine_gate": build["machine_gate"],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--openyield-root", default="/data1/qujh/work/external/OpenYield")
    parser.add_argument("--out-dir", default="outputs/TeamB_delay_chain_reference_demo/current_supported_config")
    parser.add_argument("--klayout-bin", default="/usr/bin/klayout")
    parser.add_argument("--drc-deck", default="technology/freepdk45/tech/freepdk45.lydrc")
    parser.add_argument("--only", choices=MODULE_ORDER, default=None)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--resume-negative-tests", action="store_true")
    parser.add_argument("--rebuild-failed", action="store_true")
    parser.add_argument("--scratch-root", default="/tmp/qujh_delay_chain_scratch")
    parser.add_argument("--keep-failed-scratch", action="store_true")
    parser.add_argument("--cleanup-completed-scratch", action="store_true")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    out_root = (repo_root / args.out_dir).resolve()
    openyield_root = Path(args.openyield_root).resolve()
    klayout_bin = Path(args.klayout_bin).resolve()
    drc_deck = (repo_root / args.drc_deck).resolve()
    out_root.mkdir(parents=True, exist_ok=True)

    rows = []
    for module_name in MODULE_ORDER:
        if args.only and module_name != args.only:
            continue
        rows.append(
            _run_one_module(
                repo_root,
                out_root,
                module_name,
                openyield_root,
                klayout_bin,
                drc_deck,
                run_negative_tests=args.resume_negative_tests or args.rebuild_failed,
                resume_negative_tests=args.resume_negative_tests,
            )
        )
        if args.only:
            break

    report_root = out_root.parents[0]
    disk_rows = _rows_from_disk(out_root)
    _write_report(report_root, disk_rows)
    status = recompute_final_status(report_root)
    if status["all_modules_green"]:
        status["packages"] = _package_outputs(repo_root, report_root, disk_rows)
        write_json(report_root / "DELAY_CHAIN_FINAL_STATUS.json", status)
    print(json.dumps(status, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
