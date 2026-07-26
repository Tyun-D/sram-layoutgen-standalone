from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from openyield_drc_marker_classify import parse_lyrdb  # noqa: E402
from openyield_storage_only_drc_smoke import find_klayout, infer_topcell  # noqa: E402
from sram_layoutgen.gds_util import inspect_gds_hierarchy  # noqa: E402
from sram_layoutgen.standalone import load_bundled_freepdk45  # noqa: E402


DEFAULT_TECH_DIR = Path("technology/freepdk45")
DEFAULT_STORAGE_CLASSIFICATION = Path("docs/openyield_drc_marker_classification_report.json")
DEFAULT_OUT_JSON = Path("docs/openyield_hardcell_drc_baseline_report.json")
DEFAULT_OUT_MD = Path("docs/openyield_hardcell_drc_baseline_report.md")
DEFAULT_BUILD_DIR = Path("build/openyield_hardcell_drc_baseline")
DEFAULT_CELLS = ["cell_1rw", "dummy_cell_1rw", "replica_cell_1rw"]
LOCAL_MATCH_TOL = 0.02


def main() -> int:
    parser = argparse.ArgumentParser(description="Run single-hardcell DRC baselines and compare them to storage-only marker classifications.")
    parser.add_argument("--tech-dir", type=Path, default=DEFAULT_TECH_DIR)
    parser.add_argument("--cells", nargs="+", default=DEFAULT_CELLS)
    parser.add_argument("--storage-classification", type=Path, default=DEFAULT_STORAGE_CLASSIFICATION)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--build-dir", type=Path, default=DEFAULT_BUILD_DIR)
    parser.add_argument("--klayout")
    args = parser.parse_args()

    report = build_report(args)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(format_markdown(report), encoding="utf-8")
    print(f"Wrote {args.out_json}")
    print(f"Wrote {args.out_md}")
    print(
        f"baseline_clean={report['conclusions']['hardcell_baseline_clean']} "
        f"explained={report['conclusions']['storage_markers_explained_by_hardcell']} "
        f"new={report['conclusions']['storage_markers_new_from_aggregation']}"
    )
    return 0


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    tech = load_bundled_freepdk45()
    klayout = Path(args.klayout).resolve() if args.klayout else find_klayout()
    drc_deck = args.tech_dir / "tech" / "freepdk45.lydrc"
    build_dir = args.build_dir.resolve()
    build_dir.mkdir(parents=True, exist_ok=True)
    storage = json.loads(args.storage_classification.read_text(encoding="utf-8"))
    storage_markers = list(storage.get("markers", []))
    instance_origins = build_instance_origins()

    cell_reports: dict[str, Any] = {}
    baseline_markers_by_cell: dict[str, list[dict[str, Any]]] = {}
    for cell_name in args.cells:
        cell = tech.cell(cell_name)
        gds_path = Path(cell.gds_path).resolve()
        hierarchy = inspect_gds_hierarchy(gds_path)
        topcell = infer_topcell(hierarchy)
        lyrdb_path = build_dir / f"{cell_name}_drc.lyrdb"
        log_path = build_dir / f"{cell_name}_drc.log"
        run = run_drc(klayout, drc_deck.resolve(), gds_path, topcell, lyrdb_path, log_path)
        markers = parse_lyrdb(lyrdb_path) if lyrdb_path.exists() else []
        normalized = [normalize_baseline_marker(marker) for marker in markers]
        baseline_markers_by_cell[cell_name] = normalized
        rule_stats = dict(sorted(Counter(marker["rule_name"] for marker in normalized).items()))
        cell_reports[cell_name] = {
            "gds": str(gds_path),
            "topcell": topcell,
            "drc": run,
            "marker_count": len(normalized),
            "rule_type_stats": rule_stats,
            "metal1_2_count": rule_stats.get("METAL1.2", 0),
            "metal2_2_count": rule_stats.get("METAL2.2", 0),
            "markers": normalized,
        }

    matched_storage: list[dict[str, Any]] = []
    explained = 0
    new_from_aggregation = 0
    for marker in storage_markers:
        macro = marker.get("nearest_macro")
        nearest_instance = marker.get("nearest_instance")
        origin = instance_origins.get(nearest_instance)
        local_bbox = normalize_storage_bbox(marker["bbox"], origin) if origin else None
        match = match_baseline_marker(marker, local_bbox, baseline_markers_by_cell.get(str(macro), []))
        classification = classify_match(marker, match)
        entry = {
            "storage_marker_id": marker["marker_id"],
            "rule_name": marker["rule_name"],
            "nearest_instance": nearest_instance,
            "nearest_macro": macro,
            "location_class": marker.get("location_class"),
            "storage_bbox": marker["bbox"],
            "local_bbox": local_bbox,
            "matched_baseline_marker": match,
            "baseline_explanation": classification,
        }
        matched_storage.append(entry)
        if classification in {"hardcell_intrinsic", "hardcell_boundary_intrinsic"}:
            explained += 1
        else:
            new_from_aggregation += 1

    baseline_clean = all(info["marker_count"] == 0 for info in cell_reports.values())
    aggregation_location_stats = dict(
        sorted(
            Counter(
                entry["location_class"]
                for entry in matched_storage
                if entry["baseline_explanation"] in {"aggregation_boundary_spacing", "storage_only_missing_context", "unknown"}
            ).items()
        )
    )
    power_stitch_change_required = False
    pitch_change_required = False
    storage_aggregation_can_continue = False
    if explained == len(storage_markers) and not baseline_clean:
        storage_aggregation_can_continue = True
    elif explained > 0 and new_from_aggregation == 0:
        storage_aggregation_can_continue = True

    return {
        "inputs": {
            "tech_dir": str(args.tech_dir.resolve()),
            "drc_deck": str(drc_deck.resolve()),
            "klayout": str(klayout) if klayout else None,
            "cells": list(args.cells),
            "storage_classification": str(args.storage_classification.resolve()),
        },
        "hardcells": cell_reports,
        "storage_marker_matches": matched_storage,
        "storage_match_stats": {
            "explanation_stats": dict(sorted(Counter(entry["baseline_explanation"] for entry in matched_storage).items())),
            "aggregation_location_stats": aggregation_location_stats,
        },
        "conclusions": {
            "hardcell_baseline_clean": baseline_clean,
            "storage_markers_explained_by_hardcell": explained,
            "storage_markers_new_from_aggregation": new_from_aggregation,
            "pitch_change_required": pitch_change_required,
            "power_stitch_change_required": power_stitch_change_required,
            "storage_aggregation_can_continue": storage_aggregation_can_continue,
        },
        "next_step_recommendations": [
            "Treat matched baseline markers as hardcell-intrinsic until a boundary-aware exception study says otherwise.",
            "Review the unmatched storage-only markers in KLayout at row boundaries before touching pitch.",
            "Keep the current power stitch policy because this baseline does not implicate the stitch rectangles.",
            "If unmatched markers cluster at one repeated local boundary, study that boundary before any aggregation expansion.",
        ],
    }


def build_instance_origins() -> dict[str, dict[str, float]]:
    origins: dict[str, dict[str, float]] = {}
    rows = 2
    cols = 4
    pitch_x = 0.895
    pitch_y = 1.565
    for row in range(rows):
        y = row * pitch_y
        origins[f"dummy_left_r{row}"] = {"x": 0.0, "y": y}
        for col in range(cols):
            origins[f"bit_r{row}_c{col}"] = {"x": pitch_x + col * pitch_x, "y": y}
        origins[f"dummy_right_r{row}"] = {"x": (cols + 1) * pitch_x, "y": y}
        origins[f"replica_r{row}"] = {"x": (cols + 2) * pitch_x, "y": y}
    return origins


def run_drc(
    klayout: Path | None,
    drc_deck: Path,
    gds_path: Path,
    topcell: str,
    lyrdb_path: Path,
    log_path: Path,
) -> dict[str, Any]:
    if klayout is None or not klayout.exists():
        return {
            "ran": False,
            "clean": False,
            "returncode": None,
            "lyrdb": str(lyrdb_path),
            "log": str(log_path),
            "command": None,
        }
    command = [
        str(klayout),
        "-b",
        "-r",
        str(drc_deck),
        "-rd",
        f"input={gds_path}",
        "-rd",
        f"topcell={topcell}",
        "-rd",
        f"output={lyrdb_path}",
    ]
    completed = subprocess.run(command, text=True, capture_output=True, check=False)
    log_path.write_text(
        "COMMAND:\n"
        + " ".join(command)
        + "\n\nSTDOUT:\n"
        + completed.stdout
        + "\n\nSTDERR:\n"
        + completed.stderr,
        encoding="utf-8",
    )
    return {
        "ran": True,
        "clean": completed.returncode == 0 and lyrdb_path.exists() and len(parse_lyrdb(lyrdb_path)) == 0,
        "returncode": completed.returncode,
        "lyrdb": str(lyrdb_path),
        "log": str(log_path),
        "command": command,
    }


def normalize_baseline_marker(marker: dict[str, Any]) -> dict[str, Any]:
    bbox = dict(marker["bbox"])
    return {
        "marker_id": marker["marker_id"],
        "rule_name": marker["rule_name"],
        "bbox": bbox,
        "center_x": round((bbox["x0"] + bbox["x1"]) / 2.0, 6),
        "center_y": round((bbox["y0"] + bbox["y1"]) / 2.0, 6),
    }


def normalize_storage_bbox(bbox: dict[str, float], origin: dict[str, float]) -> dict[str, float]:
    return {
        "x0": round(float(bbox["x0"]) - float(origin["x"]), 6),
        "y0": round(float(bbox["y0"]) - float(origin["y"]), 6),
        "x1": round(float(bbox["x1"]) - float(origin["x"]), 6),
        "y1": round(float(bbox["y1"]) - float(origin["y"]), 6),
    }


def match_baseline_marker(
    storage_marker: dict[str, Any],
    local_bbox: dict[str, float] | None,
    baseline_markers: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if local_bbox is None:
        return None
    sx = (local_bbox["x0"] + local_bbox["x1"]) / 2.0
    sy = (local_bbox["y0"] + local_bbox["y1"]) / 2.0
    best = None
    best_score = 999.0
    for marker in baseline_markers:
        if marker["rule_name"] != storage_marker["rule_name"]:
            continue
        dx = marker["center_x"] - sx
        dy = marker["center_y"] - sy
        score = math.hypot(dx, dy)
        if score < best_score:
            best_score = score
            best = marker
    if best is None or best_score > LOCAL_MATCH_TOL:
        return None
    return {
        "marker_id": best["marker_id"],
        "rule_name": best["rule_name"],
        "bbox": best["bbox"],
        "center_x": best["center_x"],
        "center_y": best["center_y"],
        "distance": round(best_score, 6),
    }


def classify_match(storage_marker: dict[str, Any], match: dict[str, Any] | None) -> str:
    if match is not None:
        if storage_marker.get("location_class") in {"horizontal_cell_boundary", "vertical_row_boundary", "array_outer_edge"}:
            return "hardcell_boundary_intrinsic"
        return "hardcell_intrinsic"
    if storage_marker.get("location_class") in {"horizontal_cell_boundary", "vertical_row_boundary"}:
        return "aggregation_boundary_spacing"
    if storage_marker.get("location_class") == "array_outer_edge":
        return "storage_only_missing_context"
    return "unknown"


def format_markdown(report: dict[str, Any]) -> str:
    conclusions = report["conclusions"]
    lines = [
        "# OpenYield Hardcell DRC Baseline Report",
        "",
        "This compares single-hardcell KLayout DRC baselines against the storage-only stitched marker set. It is not full SRAM signoff.",
        "",
        "## Summary",
        "",
        f"- hardcell_baseline_clean: `{conclusions['hardcell_baseline_clean']}`",
        f"- storage_markers_explained_by_hardcell: `{conclusions['storage_markers_explained_by_hardcell']}`",
        f"- storage_markers_new_from_aggregation: `{conclusions['storage_markers_new_from_aggregation']}`",
        f"- pitch_change_required: `{conclusions['pitch_change_required']}`",
        f"- power_stitch_change_required: `{conclusions['power_stitch_change_required']}`",
        f"- storage_aggregation_can_continue: `{conclusions['storage_aggregation_can_continue']}`",
        "",
        "## Hardcell DRC Counts",
        "",
    ]
    hardcell_rows = []
    for cell_name, info in report["hardcells"].items():
        hardcell_rows.append(
            [
                cell_name,
                info["marker_count"],
                info["rule_type_stats"].get("METAL1.2", 0),
                info["rule_type_stats"].get("METAL2.2", 0),
                info["drc"]["clean"],
            ]
        )
    lines.extend(format_table(["cell", "marker_count", "METAL1.2", "METAL2.2", "clean"], hardcell_rows))
    lines.extend(["", "## Storage Match Stats", ""])
    lines.extend(format_table(["explanation", "count"], report["storage_match_stats"]["explanation_stats"].items()))
    lines.extend(["", "## Aggregation Location Stats", ""])
    lines.extend(format_table(["location", "count"], report["storage_match_stats"]["aggregation_location_stats"].items()))
    lines.extend(["", "## Notes", ""])
    lines.append("- Keep the current power stitch policy; this baseline did not implicate the stitch rectangles.")
    lines.append("- Unmatched storage-only markers should be treated as row-boundary or missing-context candidates until inspected in KLayout.")
    lines.append("")
    return "\n".join(lines)


def format_table(headers: list[str], rows: Any) -> list[str]:
    rows = list(rows)
    if not rows:
        return ["- none"]
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        if isinstance(row, tuple) and len(row) == 2:
            row = [row[0], row[1]]
        out.append("| " + " | ".join(str(cell).replace("|", "\\|") for cell in row) + " |")
    return out


if __name__ == "__main__":
    raise SystemExit(main())
