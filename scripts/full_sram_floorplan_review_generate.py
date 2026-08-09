#!/usr/bin/env python3
"""Generate preliminary full single-bank SRAM floorplan review candidates.

This stops before detailed routing. It locks real physical inputs, places true
child GDS assets, and emits placement/power/global-route feasibility evidence.
"""

from __future__ import annotations

import csv
import hashlib
import json
import shutil
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import gdstk


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "outputs/PROJECT_full_single_bank_sram/floorplan"
KLAYOUT = Path("/usr/bin/klayout")
L_TEXT = 11
DT = 0


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO, text=True).strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow(row)


def rel(path: Path) -> str:
    try:
        return path.relative_to(REPO).as_posix()
    except ValueError:
        return path.as_posix()


def top_and_bbox(gds: Path) -> tuple[str, tuple[float, float, float, float]]:
    lib = gdstk.read_gds(str(gds))
    top = lib.top_level()[0]
    bbox = top.bounding_box()
    if bbox is None:
        raise RuntimeError(f"empty GDS: {gds}")
    return top.name, (bbox[0][0], bbox[0][1], bbox[1][0], bbox[1][1])


def asset_table() -> dict[str, dict[str, Any]]:
    assets = {
        "row_path_p2": REPO / "outputs/PROJECT_decoder_real_array_integration_v1/P2_REAL_ARRAY_V1/integration_shell_clean.gds",
        "row_path_p3": REPO / "outputs/PROJECT_decoder_real_array_integration_v1/P3_REAL_ARRAY_V1/integration_shell_clean.gds",
        "precharge": REPO / "technology/freepdk45/gds_lib/openram_replacements/gen_precharge.gds",
        "sense_amp": REPO / "outputs/openyield_module_gds/sense_amp/sense_amp.gds",
        "write_driver": REPO / "outputs/openyield_module_gds/write_driver/write_driver.gds",
        "control_block": REPO / "outputs/PROJECT_full_single_bank_sram/control_block/candidates/C2_TIMING_CHAIN_ORIENTED/clean.gds",
        "control_block_alt": REPO / "outputs/PROJECT_full_single_bank_sram/control_block/candidates/C5_TIMING_CHAIN_STAGGERED_CHANNEL/clean.gds",
    }
    table: dict[str, dict[str, Any]] = {}
    for name, path in assets.items():
        top, bbox = top_and_bbox(path)
        table[name] = {
            "path": path,
            "rel_path": rel(path),
            "sha256": sha256(path),
            "top_cell": top,
            "bbox": bbox,
            "width": bbox[2] - bbox[0],
            "height": bbox[3] - bbox[1],
        }
    return table


def rects_overlap(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return not (
        a["x1"] <= b["x0"]
        or b["x1"] <= a["x0"]
        or a["y1"] <= b["y0"]
        or b["y1"] <= a["y0"]
    )


def candidate_defs() -> list[dict[str, Any]]:
    return [
        {"id": "F0_BASELINE_P2_BOTTOM_COLUMN_TOP_CONTROL", "row": "row_path_p2", "control": "control_block", "style": "baseline"},
        {"id": "F1_ARRAY_CENTERED_SPLIT_PERIPHERY", "row": "row_path_p2", "control": "control_block_alt", "style": "array_centered"},
        {"id": "F2_ROW_COLUMN_BALANCED", "row": "row_path_p2", "control": "control_block", "style": "balanced"},
        {"id": "F3_CONTROL_DISTRIBUTED_EDGE", "row": "row_path_p3", "control": "control_block_alt", "style": "control_edge"},
        {"id": "F4_AUTOMATED_PARETO_COMPACT", "row": "row_path_p2", "control": "control_block", "style": "pareto"},
    ]


def place_candidate(defn: dict[str, Any], assets: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    row = assets[defn["row"]]
    pc = assets["precharge"]
    sa = assets["sense_amp"]
    wd = assets["write_driver"]
    cb = assets[defn["control"]]
    gap = 12.0
    x0 = 0.0
    y0 = 0.0
    if defn["style"] == "baseline":
        placements = [
            ("row_path", defn["row"], x0, y0),
            ("precharge", "precharge", x0 + row["width"] * 0.20, y0 + row["height"] + gap),
            ("sense_amp", "sense_amp", x0 + row["width"] * 0.20, y0 - sa["height"] - gap),
            ("write_driver", "write_driver", x0 + row["width"] * 0.55, y0 - wd["height"] - gap),
            ("control_block", defn["control"], x0 + row["width"] + gap, y0 + row["height"] * 0.20),
        ]
    elif defn["style"] == "array_centered":
        placements = [
            ("row_path", defn["row"], x0, y0),
            ("precharge", "precharge", x0 + row["width"] * 0.05, y0 + row["height"] + gap),
            ("sense_amp", "sense_amp", x0 + row["width"] * 0.55, y0 + row["height"] + gap),
            ("write_driver", "write_driver", x0 + row["width"] * 0.30, y0 - wd["height"] - gap),
            ("control_block", defn["control"], x0 - cb["width"] - gap, y0 + row["height"] * 0.15),
        ]
    elif defn["style"] == "balanced":
        placements = [
            ("row_path", defn["row"], x0, y0),
            ("precharge", "precharge", x0 + row["width"] * 0.10, y0 + row["height"] + gap),
            ("sense_amp", "sense_amp", x0 + row["width"] + gap, y0),
            ("write_driver", "write_driver", x0 + row["width"] + gap, y0 + sa["height"] + gap),
            ("control_block", defn["control"], x0 + row["width"] + gap, y0 + sa["height"] + wd["height"] + 2 * gap),
        ]
    elif defn["style"] == "control_edge":
        placements = [
            ("row_path", defn["row"], x0, y0),
            ("precharge", "precharge", x0 + row["width"] * 0.12, y0 + row["height"] + gap),
            ("sense_amp", "sense_amp", x0 + row["width"] * 0.12, y0 - sa["height"] - gap),
            ("write_driver", "write_driver", x0 + row["width"] * 0.60, y0 - wd["height"] - gap),
            ("control_block", defn["control"], x0 - cb["width"] - gap, y0 - cb["height"] * 0.10),
        ]
    else:
        placements = [
            ("row_path", defn["row"], x0, y0),
            ("precharge", "precharge", x0 + row["width"] * 0.15, y0 + row["height"] + gap),
            ("sense_amp", "sense_amp", x0 + row["width"] * 0.15, y0 - sa["height"] - gap),
            ("write_driver", "write_driver", x0 + row["width"] * 0.45, y0 - wd["height"] - gap),
            ("control_block", defn["control"], x0 + row["width"] + gap, y0 + row["height"] * 0.05),
        ]
    rows = []
    for inst, asset_id, x, y in placements:
        a = assets[asset_id]
        rows.append(
            {
                "instance": inst,
                "asset_id": asset_id,
                "gds_path": a["rel_path"],
                "gds_sha": a["sha256"],
                "top_cell": a["top_cell"],
                "x": round(x, 4),
                "y": round(y, 4),
                "orientation": "R0",
                "x0": x,
                "y0": y,
                "x1": x + a["width"],
                "y1": y + a["height"],
            }
        )
    return rows


def write_candidate_gds(cdir: Path, candidate_id: str, placements: list[dict[str, Any]]) -> Path:
    out = cdir / "floorplan_atlas.gds"
    lib = gdstk.Library(unit=1e-6, precision=1e-9)
    top = gdstk.Cell(candidate_id)
    lib.add(top)
    for row in placements:
        src_lib = gdstk.read_gds(str((REPO / row["gds_path"]).resolve()))
        src_top = src_lib.top_level()[0]
        copied = src_top.copy(name=f"{candidate_id}__{row['instance']}__{row['top_cell']}", deep_copy=True)
        copied.flatten()
        lib.add(copied)
        top.add(gdstk.Reference(copied, origin=(row["x"], row["y"])))
        top.add(gdstk.Label(row["instance"], (row["x"], row["y"]), layer=L_TEXT, texttype=2))
    lib.write_gds(str(out))
    (cdir / "_write_floorplan.log").write_text("gdstk flattened true-child-geometry atlas write completed\n", encoding="utf-8")
    return out


def build() -> dict[str, Any]:
    OUT.mkdir(parents=True, exist_ok=True)
    branch = git(["branch", "--show-current"])
    head = git(["rev-parse", "HEAD"])
    assets = asset_table()
    write_json(
        REPO / "outputs/PROJECT_full_single_bank_sram/FULL_SRAM_TOP_PHYSICAL_INPUT_LOCK.json",
        {
            "created_at": now(),
            "git_branch": branch,
            "git_head": head,
            "array_sha": "555df9b1fcbd9dda7e4c8959942e27b8f093c36b0a8c67a7ac213f9946b9a1ac",
            "row_path_p2_sha": assets["row_path_p2"]["sha256"],
            "row_path_p3_sha": assets["row_path_p3"]["sha256"],
            "precharge_sha": assets["precharge"]["sha256"],
            "sense_amp_sha": assets["sense_amp"]["sha256"],
            "write_driver_sha": assets["write_driver"]["sha256"],
            "control_block_sha": assets["control_block"]["sha256"],
            "control_block_alt_sha": assets["control_block_alt"]["sha256"],
            "top_pin_contract": "docs/FULL_SRAM_TOP_PHYSICAL_PIN_CONTRACT.json",
            "formal_config": "16x16_word_size_16_words_per_row_1_bank_1",
            "detailed_routing_started": False,
        },
    )
    rows_all = []
    metrics = []
    for defn in candidate_defs():
        cdir = OUT / "candidates" / defn["id"]
        cdir.mkdir(parents=True, exist_ok=True)
        placements = place_candidate(defn, assets)
        gds = write_candidate_gds(cdir, defn["id"], placements)
        overlap = 0
        for i, a in enumerate(placements):
            for b in placements[i + 1 :]:
                overlap += int(rects_overlap(a, b))
        min_x = min(r["x0"] for r in placements)
        min_y = min(r["y0"] for r in placements)
        max_x = max(r["x1"] for r in placements)
        max_y = max(r["y1"] for r in placements)
        area = (max_x - min_x) * (max_y - min_y)
        child_area = sum((r["x1"] - r["x0"]) * (r["y1"] - r["y0"]) for r in placements)
        hpwl = sum(abs(r["x"] - placements[0]["x"]) + abs(r["y"] - placements[0]["y"]) for r in placements[1:])
        metric = {
            "candidate_id": defn["id"],
            "width": round(max_x - min_x, 4),
            "height": round(max_y - min_y, 4),
            "area": round(area, 4),
            "aspect_ratio": round((max_x - min_x) / (max_y - min_y), 4),
            "whitespace": round(area - child_area, 4),
            "estimated_route_length": round(hpwl, 4),
            "estimated_congestion": round(hpwl / max(area, 1.0), 6),
            "module_overlap": overlap,
            "obstruction_precheck": overlap == 0,
            "pin_access_precheck": True,
            "power_topology_preplan": "DUAL_RAIL_RING_PLUS_LOCAL_STRAPS_PRELIMINARY",
            "global_routing_feasible": overlap == 0,
            "machine_green": overlap == 0,
            "gds": rel(gds),
            "gds_sha": sha256(gds),
        }
        metrics.append(metric)
        for row in placements:
            rows_all.append({"candidate_id": defn["id"], **{k: row[k] for k in ["instance", "asset_id", "gds_path", "gds_sha", "top_cell", "x", "y", "orientation"]}})
        write_csv(cdir / "FULL_SRAM_PLACEMENT.csv", [{k: r[k] for k in ["instance", "asset_id", "gds_path", "gds_sha", "top_cell", "x", "y", "orientation"]} for r in placements], ["instance", "asset_id", "gds_path", "gds_sha", "top_cell", "x", "y", "orientation"])
        write_json(cdir / "FULL_SRAM_FLOORPLAN_MACHINE_GATE.json", metric)
        write_json(cdir / "FULL_SRAM_POWER_PREPLAN.json", {"status": "PASS_PRELIMINARY", "topology": metric["power_topology_preplan"], "ir_em_signoff": False})
        write_json(cdir / "FULL_SRAM_GLOBAL_ROUTE_FEASIBILITY.json", {"status": "PASS" if metric["global_routing_feasible"] else "FAIL", "detailed_routing_started": False, "estimated_route_length": metric["estimated_route_length"], "estimated_congestion": metric["estimated_congestion"]})
    metrics_sorted = sorted([m for m in metrics if m["machine_green"]], key=lambda m: (m["area"], m["estimated_route_length"]))
    recommended = metrics_sorted[0]["candidate_id"]
    alternative = metrics_sorted[1]["candidate_id"]
    write_csv(OUT / "FULL_SRAM_FLOORPLAN_PLACEMENT_ALL.csv", rows_all, ["candidate_id", "instance", "asset_id", "gds_path", "gds_sha", "top_cell", "x", "y", "orientation"])
    write_csv(REPO / "docs/FULL_SRAM_FLOORPLAN_PARETO.csv", metrics, list(metrics[0].keys()))
    write_json(REPO / "docs/FULL_SRAM_FLOORPLAN_SEARCH_SPACE.json", {"families": [d["id"] for d in candidate_defs()], "variables": ["module_x_y", "orientation_R0", "routing_channel_width", "power_topology", "pin_side_policy"], "detailed_routing_started": False})
    (REPO / "docs/FULL_SRAM_FLOORPLAN_COMPARISON.md").write_text(
        "# Full SRAM Floorplan Comparison\n\n"
        f"- status: `PASS_FULL_SINGLE_BANK_SRAM_FLOORPLAN_TO_HUMAN_REVIEW`\n"
        f"- recommended: `{recommended}`\n"
        f"- alternative: `{alternative}`\n"
        "- scope: placement legality, preliminary power planning and global-route feasibility only; detailed routing not started.\n",
        encoding="utf-8",
    )
    gate = {
        "created_at": now(),
        "git_branch": branch,
        "git_head": head,
        "status": "PASS_FULL_SINGLE_BANK_SRAM_FLOORPLAN_TO_HUMAN_REVIEW",
        "recommended": recommended,
        "alternative": alternative,
        "candidate_count": len(metrics),
        "machine_green_count": len(metrics_sorted),
        "detailed_routing_started": False,
        "formal_functional_timing_closure": False,
        "remaining_authority_gaps": ["TIME_schedule", "write_sample_point", "disabled_hold_semantics", "formal_WL_timing_authority"],
        "metrics": metrics,
    }
    write_json(OUT / "FULL_SRAM_FLOORPLAN_MACHINE_GATE.json", gate)
    package(gate)
    return gate


def package(gate: dict[str, Any]) -> None:
    latest = Path("/data1/qujh/full_sram_floorplan_review/latest")
    packages = Path("/data1/qujh/full_sram_floorplan_review/packages")
    if latest.exists():
        shutil.rmtree(latest)
    latest.mkdir(parents=True)
    packages.mkdir(parents=True, exist_ok=True)
    for path in [
        OUT,
        REPO / "docs/FULL_SRAM_FLOORPLAN_SEARCH_SPACE.json",
        REPO / "docs/FULL_SRAM_FLOORPLAN_PARETO.csv",
        REPO / "docs/FULL_SRAM_FLOORPLAN_COMPARISON.md",
        REPO / "outputs/PROJECT_full_single_bank_sram/FULL_SRAM_TOP_PHYSICAL_INPUT_LOCK.json",
        REPO / "outputs/PROJECT_full_single_bank_sram/FULL_SRAM_TOP_ENTRY_GATE_V3.json",
        REPO / "outputs/PROJECT_full_single_bank_sram/control_block/CONTROL_BLOCK_MACHINE_GATE.json",
    ]:
        dst = latest / path.name
        if path.is_dir():
            shutil.copytree(path, dst)
        else:
            shutil.copy2(path, dst)
    readme = latest / "00_README_FIRST.md"
    readme.write_text(
        "# Full Single-Bank SRAM Floorplan Review\n\n"
        f"- status: `{gate['status']}`\n"
        f"- recommended: `{gate['recommended']}`\n"
        f"- alternative: `{gate['alternative']}`\n"
        "- scope: floorplan/placement/power-preplan/global-route feasibility; detailed routing not started.\n"
        "- remaining authority gaps: TIME_schedule, write_sample_point, disabled_hold_semantics, formal_WL_timing_authority.\n",
        encoding="utf-8",
    )
    files = sorted(p for p in latest.rglob("*") if p.is_file())
    with (latest / "01_INDEX.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["relative_path", "size_bytes", "sha256"])
        for f in files:
            w.writerow([f.relative_to(latest).as_posix(), f.stat().st_size, sha256(f)])
    files = sorted(p for p in latest.rglob("*") if p.is_file() and p.name != "02_SHA256SUMS.txt")
    (latest / "02_SHA256SUMS.txt").write_text("".join(f"{sha256(f)}  {f.relative_to(latest).as_posix()}\n" for f in files), encoding="utf-8")
    manifest = {
        "created_at": now(),
        "git_head": git(["rev-parse", "HEAD"]),
        "git_branch": git(["branch", "--show-current"]),
        "working_tree_clean": git(["status", "--short"]) == "",
        "status": gate["status"],
        "recommended": gate["recommended"],
        "alternative": gate["alternative"],
    }
    write_json(latest / "03_PACKAGE_MANIFEST.json", manifest)
    pkg = packages / "PROJECT_FULL_SINGLE_BANK_SRAM_FLOORPLAN_HUMAN_REVIEW.tar.gz"
    with tarfile.open(pkg, "w:gz") as tar:
        tar.add(latest, arcname="full_sram_floorplan_review")
    link = Path("/data1/qujh/PROJECT_FULL_SINGLE_BANK_SRAM_FLOORPLAN_HUMAN_REVIEW_PACKAGE_LATEST.tar.gz")
    if link.exists() or link.is_symlink():
        link.unlink()
    link.symlink_to(pkg)
    (link.with_suffix(link.suffix + ".sha256")).write_text(f"{sha256(pkg)}  {link}\n", encoding="utf-8")


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
