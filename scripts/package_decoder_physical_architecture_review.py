#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEST_ROOT = Path("/data1/qujh/decoder_physical_architecture_review")
LATEST = DEST_ROOT / "latest"
PACKAGES = DEST_ROOT / "packages"
INTEGRATION_ROOT = ROOT / "outputs" / "PROJECT_decoder_wl_array_integration_shell"
TOP_ROOT = ROOT / "outputs" / "PROJECT_decoder_top_v3"
CHILD = ROOT / "outputs" / "PROJECT_decoder_child_v3" / "decoder_gate_cells_v3" / "output_oriented_multiline"

PARETO = {
    "p2_control_centered_partitioned_decoder": "candidate_p2_partitioned_control_centered",
    "p3_symmetric_lower_left_control_right": "candidate_p3_symmetric_lower_left_control_right",
}
DIAGNOSTIC = "candidate_true_wl_driver_array_oriented"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_tree(source: Path, target: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(source)
    shutil.copytree(source, target)


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def description(path: Path) -> str:
    name = path.name
    if name == "integration_shell_clean.gds":
        return "Final clean integration geometry"
    if name == "POWER_WITNESS_ATLAS.gds":
        return "Per-instance final-GDS power witness atlas"
    if name == "WL_route_atlas.gds":
        return "WL route atlas"
    if name == "integration_drc.lyrdb":
        return "Combined KLayout DRC database"
    if name == "WL_TIMING_PROXY.csv":
        return "ngspice timing proxy measurements"
    if name == "WL_GEOMETRY_RC.csv":
        return "Normalized geometry RC evidence"
    if name == "POWER_ENDPOINT_COVERAGE.csv":
        return "Final-GDS power endpoint witness table"
    if "MACHINE_GATE" in name or "machine_gate" in name:
        return "Machine gate"
    return "Review evidence"


def main() -> int:
    created = datetime.now(timezone.utc).replace(microsecond=0)
    stamp = created.strftime("%Y%m%d_%H%M%S")
    branch = git("branch", "--show-current")
    head = git("rev-parse", "HEAD")
    dirty = bool(git("status", "--short"))

    LATEST.parent.mkdir(parents=True, exist_ok=True)
    PACKAGES.mkdir(parents=True, exist_ok=True)
    if LATEST.exists():
        shutil.rmtree(LATEST)
    LATEST.mkdir()

    copy_tree(CHILD, LATEST / "child_output_oriented_multiline")
    copy_tree(INTEGRATION_ROOT / DIAGNOSTIC, LATEST / "diagnostic_interface_routing_harness")
    for candidate, top in PARETO.items():
        copy_tree(INTEGRATION_ROOT / candidate, LATEST / "pareto_candidates" / candidate / "integration")
        copy_tree(TOP_ROOT / top, LATEST / "pareto_candidates" / candidate / "top")

    docs_dir = LATEST / "docs"
    docs_dir.mkdir()
    doc_names = [
        "CURRENT_CANDIDATE_FORENSIC_AUDIT.json",
        "CURRENT_CANDIDATE_FORENSIC_AUDIT.md",
        "DECODER_WL_ARRAY_PHYSICAL_ARCHITECTURE_CONTRACT.json",
        "DECODER_WL_ARRAY_PHYSICAL_ARCHITECTURE_CONTRACT.md",
        "DECODER_PHYSICAL_ARCHITECTURE_COMPARISON.csv",
        "DECODER_PHYSICAL_ARCHITECTURE_COMPARISON.md",
        "DECODER_PHYSICAL_ARCHITECTURE_PARETO.json",
        "DECODER_PHYSICAL_ARCHITECTURE_HUMAN_REVIEW_CHECKLIST.md",
    ]
    for name in doc_names:
        shutil.copy2(ROOT / "docs" / name, docs_dir / name)

    readme = f"""# Decoder Physical Architecture Review

- created_at: `{created.isoformat().replace('+00:00', 'Z')}`
- source_worktree: `{ROOT}`
- git_branch: `{branch}`
- git_head: `{head}`
- working_tree: `{'dirty' if dirty else 'clean'}`
- Pareto candidates: `p2_control_centered_partitioned_decoder`, `p3_symmetric_lower_left_control_right`
- diagnostic baseline: `INTERFACE_ROUTING_HARNESS_MACHINE_PASS`
- integration level: `FLOORPLAN_FEASIBILITY_SHELL`
- array object: `approved_nonzero_physical_shell`
- full bitcell array GDS included: `false`
- full bitcell array GDS integration: `PENDING`
- RC model: `NORMALIZED_GEOMETRY_RC_PROXY`, not PEX
- timing authority: `TIMING_BUDGET_AUTHORITY_PENDING`
- normalized RC temporary threshold passed: `false`

## KLayout Order

1. `pareto_candidates/p2_control_centered_partitioned_decoder/integration/integration_shell_clean.gds`
2. `pareto_candidates/p3_symmetric_lower_left_control_right/integration/integration_shell_clean.gds`
3. Each candidate's `POWER_WITNESS_ATLAS.gds`
4. Each candidate's `WL_route_atlas.gds`
5. Each candidate's `integration_drc.lyrdb`
6. `diagnostic_interface_routing_harness/integration_shell_clean.gds` for comparison only

The two Pareto candidates have combined DRC=0, 148/148 final-GDS power endpoint witnesses, 16 bit-exact aligned WL paths, completed ngspice timing proxies, and architecture-negative unexpected-pass count 0. This package is for human floorplan review, not final SRAM signoff.
"""
    (LATEST / "00_README_FIRST.md").write_text(readme, encoding="utf-8")

    manifest = {
        "created_at": created.isoformat().replace("+00:00", "Z"),
        "source_worktree": str(ROOT),
        "git_branch": branch,
        "git_head": head,
        "working_tree_clean": not dirty,
        "diagnostic_baseline": DIAGNOSTIC,
        "pareto_candidates": list(PARETO),
        "array_object_type": "approved_nonzero_physical_shell",
        "array_integration_level": "FLOORPLAN_FEASIBILITY_SHELL",
        "full_bitcell_array_gds_included": False,
        "timing_budget_authority": "TIMING_BUDGET_AUTHORITY_PENDING",
        "rc_model_kind": "NORMALIZED_GEOMETRY_RC_PROXY",
        "rc_proxy_temporary_threshold_passed": False,
    }
    (LATEST / "03_PACKAGE_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    indexed = [path for path in sorted(LATEST.rglob("*")) if path.is_file() and path.name not in {"01_INDEX.csv", "02_SHA256SUMS.txt"}]
    with (LATEST / "01_INDEX.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["category", "relative_path", "description", "size_bytes", "sha256", "required_for_human_review"])
        writer.writeheader()
        for path in indexed:
            rel = path.relative_to(LATEST)
            required = path.suffix in {".gds", ".lyrdb"} or path.name in {"POWER_ENDPOINT_COVERAGE.csv", "WL_GEOMETRY_RC.csv", "WL_TIMING_PROXY.csv", "PHYSICAL_ARCHITECTURE_MACHINE_GATE.json"}
            writer.writerow({"category": rel.parts[0], "relative_path": rel, "description": description(path), "size_bytes": path.stat().st_size, "sha256": sha256(path), "required_for_human_review": str(required).lower()})

    checksum_files = [path for path in sorted(LATEST.rglob("*")) if path.is_file() and path.name != "02_SHA256SUMS.txt"]
    (LATEST / "02_SHA256SUMS.txt").write_text("".join(f"{sha256(path)}  {path.relative_to(LATEST)}\n" for path in checksum_files), encoding="utf-8")

    human = PACKAGES / f"PROJECT_DECODER_PHYSICAL_ARCHITECTURE_HUMAN_REVIEW_{stamp}.tar.gz"
    full = PACKAGES / f"PROJECT_DECODER_PHYSICAL_ARCHITECTURE_FULL_EVIDENCE_{stamp}.tar.gz"
    human_names = {"00_README_FIRST.md", "01_INDEX.csv", "02_SHA256SUMS.txt", "03_PACKAGE_MANIFEST.json"}
    human_suffixes = {".gds", ".lyrdb", ".csv", ".json", ".md"}
    with tarfile.open(human, "w:gz") as archive:
        for path in sorted(LATEST.rglob("*")):
            if not path.is_file():
                continue
            rel = path.relative_to(LATEST)
            if path.name in human_names or ("clones" not in rel.parts and "WL_TIMING_PROXY_WAVEFORMS" not in rel.parts and path.suffix in human_suffixes):
                archive.add(path, arcname=Path("PROJECT_DECODER_PHYSICAL_ARCHITECTURE_HUMAN_REVIEW") / rel)
    with tarfile.open(full, "w:gz") as archive:
        archive.add(LATEST, arcname="PROJECT_DECODER_PHYSICAL_ARCHITECTURE_FULL_EVIDENCE")

    links = {
        Path("/data1/qujh/PROJECT_DECODER_PHYSICAL_ARCHITECTURE_HUMAN_REVIEW_PACKAGE_LATEST.tar.gz"): human,
        Path("/data1/qujh/PROJECT_DECODER_PHYSICAL_ARCHITECTURE_FULL_EVIDENCE_PACKAGE_LATEST.tar.gz"): full,
    }
    for link, target in links.items():
        if link.is_symlink() or link.exists():
            link.unlink()
        link.symlink_to(target)

    result = {
        "browse_directory": str(LATEST),
        "human_package": str(human),
        "human_sha256": sha256(human),
        "full_package": str(full),
        "full_sha256": sha256(full),
        "git_branch": branch,
        "git_head": head,
        "working_tree_clean": not dirty,
    }
    (DEST_ROOT / "LATEST_PACKAGE_PATHS.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
