from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import tarfile
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
import sys

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.inverter_chain_generator import generate_inverter_chain
from sram_layoutgen.openyield_adapter.inverter_chain_layout_quality import module_timestamp_slug, recompute_final_status
from sram_layoutgen.openyield_adapter.inverter_chain_negative_regressions import run_inverter_chain_negative_regressions
from sram_layoutgen.openyield_adapter.inverter_chain_source_lock import MODULE_SPECS
from sram_layoutgen.openyield_adapter.inverter_chain_verification_gate import build_inverter_chain_production_gate, validate_inverter_chain_bundle
from sram_layoutgen.openyield_adapter.teamb_composite_helper import read_json, write_json, write_text


MODULE_ORDER = ["pdrive2_for_pre", "wl_pdrive", "pdrive"]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_report(out_root: Path, rows: list[dict[str, Any]]) -> None:
    lines = ["# Team B Inverter Chain Technical Report", ""]
    for row in rows:
        selected = read_json(Path(row["cell_dir"]) / "selected_floorplan.json")
        layout_metrics = read_json(Path(row["cell_dir"]) / "layout_quality_metrics.json")
        gap_json = read_json(Path(row["cell_dir"]) / "adjacent_gap_sweep.json")
        lines.extend(
            [
                f"## {row['module_name']}",
                "",
                f"- clean_gds_sha256: `{row['clean_gds_sha256']}`",
                f"- selected_floorplan: `{selected['selected_architecture']}`",
                f"- drc_marker_count: `{row['machine_gate']['drc_marker_count']}`",
                f"- negative_tests_passed: `{row['machine_gate']['negative_tests_passed']}`",
                f"- area: `{layout_metrics['area']}`",
                f"- estimated_signal_wire_length: `{layout_metrics['estimated_signal_wire_length']}`",
                "",
            ]
        )
        for pair in gap_json["pairs"]:
            lines.append(
                f"  - {pair['pair_id']}: baseline `{pair['baseline_gap']}`, minimum_legal `{pair['minimum_legal_gap']}`, first_failed `{pair['first_failed_gap']}`"
            )
        lines.append("")
    write_text(out_root / "INVERTER_CHAIN_TECHNICAL_REPORT.md", "\n".join(lines))
    with (out_root / "INVERTER_CHAIN_FILE_INDEX.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["module_name", "artifact_path", "sha256"])
        writer.writeheader()
        for row in rows:
            base = Path(row["cell_dir"])
            for rel in [
                "clean.gds",
                "annotated.gds",
                "review_atlas.gds",
                "review_atlas_gap_dimensions.gds",
                "review_atlas_pin_access.gds",
                "review_atlas_power_rails.gds",
                "machine_gate.json",
                "source_lock.json",
                "parameter_mapping.json",
                "instance_binding.csv",
                "top_pin_contract.json",
                "floorplan_candidates.json",
                "selected_floorplan.json",
                "layout_quality_metrics.json",
                "adjacent_gap_sweep.csv",
                "adjacent_gap_sweep.json",
                "gap_constraint_report.md",
                "poly_metal_overlap_report.json",
            ]:
                p = base / rel
                if p.exists():
                    writer.writerow({"module_name": row["module_name"], "artifact_path": str(p.resolve()), "sha256": _sha256(p)})
    sha_lines = []
    for row in rows:
        for rel in [
            "clean.gds",
            "annotated.gds",
            "review_atlas.gds",
            "review_atlas_gap_dimensions.gds",
            "review_atlas_pin_access.gds",
            "review_atlas_power_rails.gds",
            "machine_gate.json",
            "floorplan_candidates.json",
            "selected_floorplan.json",
            "layout_quality_metrics.json",
            "adjacent_gap_sweep.csv",
            "adjacent_gap_sweep.json",
            "gap_constraint_report.md",
            "poly_metal_overlap_report.json",
        ]:
            p = Path(row["cell_dir"]) / rel
            if p.exists():
                sha_lines.append(f"{_sha256(p)}  {p.resolve()}")
    write_text(out_root / "INVERTER_CHAIN_SHA256SUMS.txt", "\n".join(sha_lines))


def _package_review(repo_root: Path, out_root: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    package_path = Path("/data1/qujh/TEAM_B_INVERTER_CHAIN_HUMAN_REVIEW_PACKAGE_LATEST.tar.gz")
    sha_path = Path("/data1/qujh/TEAM_B_INVERTER_CHAIN_HUMAN_REVIEW_PACKAGE_LATEST.tar.gz.sha256")
    include_paths = [
        out_root / "INVERTER_CHAIN_FINAL_STATUS.json",
        out_root / "INVERTER_CHAIN_FINAL_STATUS.md",
        out_root / "INVERTER_CHAIN_TECHNICAL_REPORT.md",
        out_root / "INVERTER_CHAIN_FILE_INDEX.csv",
        out_root / "INVERTER_CHAIN_SHA256SUMS.txt",
    ]
    for row in rows:
        cell_dir = Path(row["cell_dir"])
        include_paths.extend(
            [
                cell_dir / "clean.gds",
                cell_dir / "annotated.gds",
                cell_dir / "review_atlas.gds",
                cell_dir / "review_atlas_gap_dimensions.gds",
                cell_dir / "review_atlas_pin_access.gds",
                cell_dir / "review_atlas_power_rails.gds",
                cell_dir / "machine_gate.json",
                cell_dir / "source_lock.json",
                cell_dir / "parameter_mapping.json",
                cell_dir / "instance_binding.csv",
                cell_dir / "top_pin_contract.json",
                cell_dir / "hierarchy_closure.json",
                cell_dir / "child_immutability.json",
                cell_dir / "connectivity_graph.json",
                cell_dir / "physical_connectivity_report.json",
                cell_dir / "foreign_net_report.json",
                cell_dir / "floorplan_candidates.json",
                cell_dir / "selected_floorplan.json",
                cell_dir / "layout_quality_metrics.json",
                cell_dir / "adjacent_gap_sweep.csv",
                cell_dir / "adjacent_gap_sweep.json",
                cell_dir / "gap_constraint_report.md",
                cell_dir / "poly_metal_overlap_report.json",
                cell_dir / "negative_tests" / f"{row['module_name']}_negative_test_summary.json",
                cell_dir / "human_review",
            ]
        )
        include_paths.extend(list((cell_dir / "drc").glob("*")))
    with tarfile.open(package_path, "w:gz") as tar:
        for path in include_paths:
            if path.exists():
                tar.add(path, arcname=str(path.relative_to(repo_root)))
    sha = _sha256(package_path)
    write_text(sha_path, f"{sha}  {package_path.name}")
    stamped = out_root / f"TEAM_B_INVERTER_CHAIN_HUMAN_REVIEW_PACKAGE_{module_timestamp_slug()}.tar.gz"
    shutil.copy2(package_path, stamped)
    return {"package_path": str(package_path), "package_sha256": sha, "package_size_bytes": package_path.stat().st_size, "timestamped_package_path": str(stamped.resolve())}


def _run_one_module(repo_root: Path, out_root: Path, module_name: str, openyield_root: Path, klayout_bin: Path, drc_deck: Path) -> dict[str, Any]:
    cell_dir = out_root / module_name
    cell_dir.mkdir(parents=True, exist_ok=True)
    spec = MODULE_SPECS[module_name]
    generated = generate_inverter_chain(
        repo_root=repo_root,
        module_name=module_name,
        top_cell_name=spec["top_cell_name"],
        top_pin_order=spec["top_pin_order"],
        child_variants=spec["child_variants"],
        internal_net_names=spec["internal_nets"],
        output_dir=cell_dir,
        klayout_bin=klayout_bin,
        drc_deck=drc_deck,
    )
    build = build_inverter_chain_production_gate(
        repo_root=repo_root,
        cell_dir=cell_dir,
        module_name=module_name,
        openyield_root=openyield_root,
        klayout_bin=klayout_bin,
        drc_deck=drc_deck,
    )
    negative = run_inverter_chain_negative_regressions(
        module_name=module_name,
        baseline_clean_gds=cell_dir / "clean.gds",
        production_validator={
            "repo_root": repo_root,
            "openyield_root": openyield_root,
            "klayout_bin": klayout_bin,
            "drc_deck": drc_deck,
            "validate_fn": validate_inverter_chain_bundle,
        },
        output_dir=cell_dir / "negative_tests",
        resume=False,
    )
    machine_gate = read_json(cell_dir / "machine_gate.json")
    machine_gate["negative_tests_passed"] = negative["summary"]["negative_tests_passed"]
    write_json(cell_dir / "machine_gate.json", machine_gate)
    return {
        "module_name": module_name,
        "cell_dir": str(cell_dir.resolve()),
        "clean_gds_sha256": _sha256(cell_dir / "clean.gds"),
        "machine_gate": machine_gate,
    }


def _rows_from_disk(out_root: Path) -> list[dict[str, Any]]:
    rows = []
    for module_name in MODULE_ORDER:
        cell_dir = out_root / module_name
        rows.append(
            {
                "module_name": module_name,
                "cell_dir": str(cell_dir.resolve()),
                "clean_gds_sha256": _sha256(cell_dir / "clean.gds"),
                "machine_gate": read_json(cell_dir / "machine_gate.json"),
            }
        )
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=str(REPO_ROOT))
    parser.add_argument("--openyield-root", default="/data1/qujh/work/external/OpenYield")
    parser.add_argument("--out-dir", default="outputs/TeamB_inverter_chain_reference_demo/current_supported_config")
    parser.add_argument("--klayout-bin", default="/usr/bin/klayout")
    parser.add_argument("--drc-deck", default="technology/freepdk45/tech/freepdk45.lydrc")
    parser.add_argument("--only", choices=MODULE_ORDER, default=None)
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
        rows.append(_run_one_module(repo_root, out_root, module_name, openyield_root, klayout_bin, drc_deck))
        if args.only:
            break

    report_root = out_root.parents[0]
    disk_rows = _rows_from_disk(out_root)
    _write_report(report_root, disk_rows)
    status = recompute_final_status(out_root=report_root, module_order=MODULE_ORDER)
    if status["all_modules_green"]:
        status["human_review_package"] = _package_review(repo_root, report_root, disk_rows)
        write_json(report_root / "INVERTER_CHAIN_FINAL_STATUS.json", status)
    print(json.dumps(status, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
