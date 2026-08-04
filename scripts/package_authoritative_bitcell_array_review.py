#!/usr/bin/env python3
"""Build browsable and compressed authoritative-array review evidence."""

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


REPO = Path(__file__).resolve().parents[1]
ROOT = Path("/data1/qujh/authoritative_bitcell_array_review")
LATEST = ROOT / "latest"
PACKAGES = ROOT / "packages"
ARRAY = REPO / "outputs/PROJECT_bitcell_array_layoutgen_reuse_v2"

DOCS = [
    "BITCELL_ARRAY_RECOVERY_CANDIDATE_INVENTORY.csv",
    "BITCELL_ARRAY_RECOVERY_CANDIDATE_INVENTORY.json",
    "CURRENT_FORMAL_ARRAY_CONFIG_LOCK.json",
    "LAYOUTGEN_EXISTING_ACHIEVEMENT_AUDIT.md",
    "LAYOUTGEN_EXISTING_ACHIEVEMENT_AUDIT.json",
    "LAYOUTGEN_PHYSICAL_REUSE_CONTRACT.md",
    "LAYOUTGEN_PHYSICAL_REUSE_CONTRACT.json",
    "BITCELL_ARRAY_PHYSICAL_AUTHORITY_LOCK.md",
    "BITCELL_ARRAY_PHYSICAL_AUTHORITY_LOCK.json",
    "PROJECT_CURRENT_STATUS.json",
]

HUMAN_ARRAY_FILES = [
    "clean.gds",
    "review_atlas.gds",
    "BITCELL_ABUTMENT_WITNESS_ATLAS.gds",
    "POWER_RAIL_UNION_ATLAS.gds",
    "DUMMY_TAP_REPLICA_ATLAS.gds",
    "PIN_ATLAS.gds",
    "placement.csv",
    "instance_map.csv",
    "BITCELL_ABUTMENT_MATRIX.csv",
    "pin_map.json",
    "power_endpoint_coverage.csv",
    "same_net_power_union_report.json",
    "hierarchy_inventory.json",
    "manifest.json",
    "machine_gate.json",
    "BITCELL_ARRAY_MACHINE_GATE.json",
    "BITCELL_ARRAY_AUTHORITY_LOCK.json",
    "BITCELL_ARRAY_AUTHORITY_LOCK.md",
    "REUSE_CONTRACT_LOAD_REPORT.json",
    "negative_summary.json",
    "determinism.json",
    "source_lock.json",
    "drc/bitcell_array_layoutgen_reuse_v2.lyrdb",
    "drc/bitcell_array_layoutgen_reuse_v2.log",
]


def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=REPO, text=True).strip()


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            value.update(block)
    return value.hexdigest()


def copy_tree() -> None:
    if LATEST.exists():
        shutil.rmtree(LATEST)
    (LATEST / "array").mkdir(parents=True)
    (LATEST / "docs").mkdir()
    (LATEST / "status").mkdir()
    shutil.copytree(ARRAY, LATEST / "array", dirs_exist_ok=True)
    for name in DOCS:
        source = REPO / "docs" / name
        if source.exists():
            shutil.copy2(source, LATEST / "docs" / name)
    shutil.copy2(REPO / "scripts/project_bitcell_array_layoutgen_reuse_v2.py", LATEST / "status/generator.py")
    shutil.copy2(REPO / "tests/test_project_bitcell_array_layoutgen_reuse_v2.py", LATEST / "status/generator_test.py")


def write_metadata(branch: str, head: str, remote: str, clean: bool) -> None:
    gate = json.loads((ARRAY / "BITCELL_ARRAY_MACHINE_GATE.json").read_text())
    lock = json.loads((ARRAY / "BITCELL_ARRAY_AUTHORITY_LOCK.json").read_text())
    status_path = LATEST / "docs/PROJECT_CURRENT_STATUS.json"
    status = json.loads(status_path.read_text())
    status["git_head"] = head
    status["current_git_head"] = head
    status["remote_branch_head"] = head
    status["layoutgen_reuse_closure"]["new_architecture_review_package_generated"] = True
    status_path.write_text(json.dumps(status, indent=2, sort_keys=True) + "\n")

    readme = f"""# Authoritative Bitcell Array Review

- Git branch: `{branch}`
- Package build HEAD: `{head}`
- Remote branch HEAD at package build: `{remote}`
- Local/remote synchronized: `{str(head == remote).lower()}`
- Source worktree: `{REPO}`
- Authority: `A_CURRENT_SOURCE_EXACT`
- Formal configuration: 16 rows x 16 columns, word size 16, words per row 1, one bank, FreePDK45 `cell_1rw`
- Top cell: `sram_capped_replica_bitcell_array`
- Array GDS SHA256: `{lock['gds']['sha256']}`
- Machine gate: `{gate['status']}`
- Working tree clean at package build: `{str(clean).lower()}`
- Full Decoder/WL-driver integration: `false`; integration rerun remains pending.

## KLayout Review Order

1. `array/clean.gds`
2. `array/review_atlas.gds`
3. `array/BITCELL_ABUTMENT_WITNESS_ATLAS.gds`
4. `array/POWER_RAIL_UNION_ATLAS.gds`
5. `array/DUMMY_TAP_REPLICA_ATLAS.gds`
6. `array/PIN_ATLAS.gds`
7. `array/drc/bitcell_array_layoutgen_reuse_v2.lyrdb`

The clean GDS is Level-A geometry. Atlases are review aids and do not replace the clean GDS, DRC database, hierarchy inventory, conductor graph, or endpoint witnesses.
"""
    (LATEST / "00_README_FIRST.md").write_text(readme)

    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_worktree": str(REPO),
        "git_branch": branch,
        "git_head": head,
        "remote_branch_head": remote,
        "local_remote_synchronized": head == remote,
        "working_tree_clean": clean,
        "authority_level": "A_CURRENT_SOURCE_EXACT",
        "formal_config": "16x16_wpr1_freepdk45",
        "top_cell": "sram_capped_replica_bitcell_array",
        "array_gds": "array/clean.gds",
        "array_gds_sha256": lock["gds"]["sha256"],
        "machine_gate_status": gate["status"],
        "full_bitcell_array_gds_integration": False,
        "integration_status": "STANDALONE_ARRAY_APPROVED_INTEGRATION_RERUN_PENDING",
    }
    (LATEST / "03_PACKAGE_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")


def write_index_and_sums() -> None:
    files = sorted(path for path in LATEST.rglob("*") if path.is_file() and path.name not in {"01_INDEX.csv", "02_SHA256SUMS.txt"})
    with (LATEST / "01_INDEX.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["category", "relative_path", "size_bytes", "sha256", "required_for_human_review"])
        writer.writeheader()
        for path in files:
            relative = path.relative_to(LATEST).as_posix()
            category = relative.split("/", 1)[0] if "/" in relative else "package"
            required = relative in {"00_README_FIRST.md", "03_PACKAGE_MANIFEST.json"} or relative.removeprefix("array/") in HUMAN_ARRAY_FILES
            writer.writerow({"category": category, "relative_path": relative, "size_bytes": path.stat().st_size, "sha256": digest(path), "required_for_human_review": str(required).lower()})
    checksum_files = sorted(path for path in LATEST.rglob("*") if path.is_file() and path.name != "02_SHA256SUMS.txt")
    lines = [f"{digest(path)}  ./{path.relative_to(LATEST).as_posix()}" for path in checksum_files]
    (LATEST / "02_SHA256SUMS.txt").write_text("\n".join(lines) + "\n")


def create_package(source: Path, output: Path, arcname: str) -> None:
    with tarfile.open(output, "w:gz") as archive:
        archive.add(source, arcname=arcname)


def main() -> None:
    branch = run("git", "branch", "--show-current")
    head = run("git", "rev-parse", "HEAD")
    remote = run("git", "rev-parse", f"origin/{branch}")
    clean = not run("git", "status", "--short")
    allow_unsynced = os.environ.get("ALLOW_UNSYNCED_PACKAGE") == "1"
    if not clean or (head != remote and not allow_unsynced):
        raise SystemExit("PACKAGE_GIT_STATE_NOT_SYNCHRONIZED")
    copy_tree()
    write_metadata(branch, head, remote, clean)
    write_index_and_sums()

    human = ROOT / "human_staging"
    if human.exists():
        shutil.rmtree(human)
    human.mkdir(parents=True)
    for name in ["00_README_FIRST.md", "01_INDEX.csv", "02_SHA256SUMS.txt", "03_PACKAGE_MANIFEST.json"]:
        shutil.copy2(LATEST / name, human / name)
    shutil.copytree(LATEST / "docs", human / "docs")
    for relative in HUMAN_ARRAY_FILES:
        source = LATEST / "array" / relative
        destination = human / "array" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    PACKAGES.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    human_package = PACKAGES / f"PROJECT_AUTHORITATIVE_BITCELL_ARRAY_HUMAN_REVIEW_{stamp}.tar.gz"
    full_package = PACKAGES / f"PROJECT_AUTHORITATIVE_BITCELL_ARRAY_FULL_EVIDENCE_{stamp}.tar.gz"
    create_package(human, human_package, "authoritative_bitcell_array_human_review")
    create_package(LATEST, full_package, "authoritative_bitcell_array_full_evidence")
    shutil.rmtree(human)

    links = {
        Path("/data1/qujh/PROJECT_AUTHORITATIVE_BITCELL_ARRAY_HUMAN_REVIEW_PACKAGE_LATEST.tar.gz"): human_package,
        Path("/data1/qujh/PROJECT_AUTHORITATIVE_BITCELL_ARRAY_FULL_EVIDENCE_PACKAGE_LATEST.tar.gz"): full_package,
    }
    for link, target in links.items():
        link.unlink(missing_ok=True)
        link.symlink_to(target)
        link.with_suffix(link.suffix + ".sha256").write_text(f"{digest(target)}  {target}\n")
    print(json.dumps({"human_package": str(human_package), "human_sha256": digest(human_package), "full_package": str(full_package), "full_sha256": digest(full_package)}, sort_keys=True))


if __name__ == "__main__":
    main()
