#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEST = Path("/data1/qujh/decoder_real_array_wl_timing_review")
LATEST = DEST / "latest"
PACKAGES = DEST / "packages"
OUT = ROOT / "outputs" / "PROJECT_decoder_physical_timing_closure"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def copy_file(source: Path, relative: Path) -> None:
    target = LATEST / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def main() -> int:
    branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    if LATEST.exists():
        shutil.rmtree(LATEST)
    LATEST.mkdir(parents=True)
    PACKAGES.mkdir(parents=True, exist_ok=True)

    docs = [
        "DECODER_PHYSICAL_ARCHITECTURE_GOLDEN_LOCK.json", "DECODER_PHYSICAL_ARCHITECTURE_GOLDEN_LOCK.md",
        "WL_TIMING_AUTHORITY_AUDIT.json", "WL_TIMING_AUTHORITY_AUDIT.md",
        "WL_TIMING_AUTHORITY_REVIEW_PACKET.json", "WL_TIMING_AUTHORITY_REVIEW_PACKET.md",
        "PDK_INTERCONNECT_RC_AUTHORITY_AUDIT.json", "PDK_INTERCONNECT_RC_AUTHORITY_AUDIT.md",
        "BITCELL_ARRAY_PHYSICAL_AUTHORITY_LOCK.json", "BITCELL_ARRAY_PHYSICAL_AUTHORITY_LOCK.md",
        "PROJECT_CURRENT_STATUS.json", "PROJECT_TASK_MASTER_LOG.md",
    ]
    for name in docs:
        copy_file(ROOT / "docs" / name, Path("docs") / name)

    for candidate in ["T0_p2_interleaved_baseline", "T1_common_egress_plane", "T2_controlled_short_path_compensation", "T3_driver_column_spacing_pareto", "TREAL_L3_array_authority_pending"]:
        source = OUT / candidate
        target = LATEST / "candidates" / candidate
        shutil.copytree(source, target, ignore=shutil.ignore_patterns("*.log", "*.sp", "WL_TIMING_PROXY_WAVEFORMS"))
    copy_file(OUT / "T4_1x16_single_column_feasibility" / "feasibility_gate.json", Path("candidates/T4_1x16_single_column_feasibility/feasibility_gate.json"))
    copy_file(OUT / "WL_TIMING_CLOSURE_COMPARISON.csv", Path("comparison/WL_TIMING_CLOSURE_COMPARISON.csv"))
    copy_file(OUT / "WL_TIMING_CLOSURE_SUMMARY.json", Path("comparison/WL_TIMING_CLOSURE_SUMMARY.json"))

    readme = f"""# Decoder WL timing engineering closure

- Git branch: `{branch}`
- package build HEAD: `{head}`
- recommended implemented local candidate: `T3_driver_column_spacing_pareto`
- formal timing authority: `PENDING`
- RC evidence: `NORMALIZED_GEOMETRY_RC_PROXY` (`NOT_POST_LAYOUT_PEX`)
- array integration level: `FLOORPLAN_FEASIBILITY_SHELL`
- full bitcell array GDS integration: `PENDING`

Open `candidates/T3_driver_column_spacing_pareto/integration_shell_clean.gds` first, followed by its power witness atlas, WL route atlas, DRC database, V2 RC/timing reports, and machine gate. T0 is the locked local baseline. T1/T2 are semantic-contract rejects. TREAL is a failed diagnostic and must not be treated as real-array closure.
"""
    (LATEST / "00_README_FIRST.md").write_text(readme, encoding="utf-8")

    rows = []
    for path in sorted(LATEST.rglob("*")):
        if path.is_file() and path.name not in {"01_INDEX.csv", "02_SHA256SUMS.txt", "03_PACKAGE_MANIFEST.json"}:
            rel = path.relative_to(LATEST).as_posix()
            rows.append({"relative_path": rel, "size_bytes": path.stat().st_size, "sha256": sha256(path), "category": rel.split("/", 1)[0], "required_for_human_review": path.suffix in {".gds", ".lyrdb", ".json", ".csv", ".md"}})
    with (LATEST / "01_INDEX.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    sums = []
    for path in sorted(LATEST.rglob("*")):
        if path.is_file() and path.name not in {"02_SHA256SUMS.txt", "03_PACKAGE_MANIFEST.json"}:
            sums.append(f"{sha256(path)}  {path.relative_to(LATEST).as_posix()}")
    (LATEST / "02_SHA256SUMS.txt").write_text("\n".join(sums) + "\n", encoding="utf-8")
    manifest = {
        "created_at": datetime.now(timezone.utc).isoformat(), "git_branch": branch, "git_head": head,
        "recommended_candidate": "T3_driver_column_spacing_pareto", "formal_timing_authority": "PENDING",
        "rc_evidence_level": "NORMALIZED_GEOMETRY_RC_PROXY", "not_post_layout_pex": True,
        "array_integration_level": "FLOORPLAN_FEASIBILITY_SHELL", "full_bitcell_array_gds_integrated": False,
        "stop_classification": "PASS_WL_TIMING_ENGINEERING_CLOSURE_PENDING_ARRAY_GDS_AUTHORITY",
        "all_file_count": sum(1 for path in LATEST.rglob("*") if path.is_file()) + 1,
    }
    (LATEST / "03_PACKAGE_MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    human = PACKAGES / f"PROJECT_DECODER_REAL_ARRAY_WL_TIMING_HUMAN_REVIEW_{stamp}.tar.gz"
    full = PACKAGES / f"PROJECT_DECODER_REAL_ARRAY_WL_TIMING_FULL_EVIDENCE_{stamp}.tar.gz"
    with tarfile.open(human, "w:gz") as archive:
        archive.add(LATEST, arcname="decoder_real_array_wl_timing_review")
    with tarfile.open(full, "w:gz") as archive:
        archive.add(LATEST, arcname="decoder_real_array_wl_timing_full_evidence")
        archive.add(OUT, arcname="raw_timing_closure_outputs")
    for package, link_name in [
        (human, "PROJECT_DECODER_REAL_ARRAY_WL_TIMING_HUMAN_REVIEW_PACKAGE_LATEST.tar.gz"),
        (full, "PROJECT_DECODER_REAL_ARRAY_WL_TIMING_FULL_EVIDENCE_PACKAGE_LATEST.tar.gz"),
    ]:
        link = Path("/data1/qujh") / link_name
        link.unlink(missing_ok=True)
        link.symlink_to(package)
        Path(str(link) + ".sha256").write_text(f"{sha256(package)}  {package}\n", encoding="utf-8")
    result = {"human_package": str(human), "human_sha256": sha256(human), "full_package": str(full), "full_sha256": sha256(full), "git_head": head}
    (DEST / "PACKAGE_RESULT.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
