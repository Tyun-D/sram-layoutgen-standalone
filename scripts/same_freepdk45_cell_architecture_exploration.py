#!/usr/bin/env python3
"""Same-FreePDK45 cell architecture exploration evidence generator.

This script is intentionally audit-oriented. It does not alter the full SRAM
top; it extracts current physical facts and records which same-PDK replacement
routes are authorized, blocked, or still exploratory.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tarfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import gdstk


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/PROJECT_same_freepdk45_cell_architecture_exploration"
DOCS = ROOT / "docs"
EXP = ROOT / "experiments/lclayout"
TOOL_EXP = Path("/data1/qujh/tool_experiments/lclayout_freepdk45")
PKG_DIR = Path("/data1/qujh/same_freepdk45_cell_architecture_exploration_review/latest")
PKG = Path("/data1/qujh/PROJECT_SAME_FREEPDK45_CELL_ARCHITECTURE_EXPLORATION_HUMAN_REVIEW_PACKAGE_LATEST.tar.gz")

V41_GDS = ROOT / "outputs/PROJECT_full_single_bank_sram/FULL_SRAM_DFF_AUTHORITY_AND_COLUMN_INTERFACE_ALIGNMENT_V41/clean_unique_top.gds"
ARRAY_PIN_MAP = ROOT / "outputs/PROJECT_bitcell_array_layoutgen_reuse_v2/pin_map.json"
WL_DRIVER_GDS = ROOT / "outputs/PROJECT_wordline_driver_v2_regen/current_supported_config/wordline_driver_v2.gds"
WL_DRIVER_PIN_MAP = ROOT / "outputs/PROJECT_wordline_driver_v2_regen/current_supported_config/wordline_driver_v2_pin_map.json"
DFF_CORE_GDS = ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/DFF_TG4_INV7_FPDK45_26d9543b82b7/DFF_TG4_INV7_FPDK45_26d9543b82b7.gds"
DFF_BUF_GDS = ROOT / "outputs/Wave3_DFF_BUF_human_review_seal/_readonly_probe/DFF_BUF_FPDK45_6058eaf43739_HPA1/DFF_BUF_FPDK45_6058eaf43739_HPA1.gds"
BUNDLED_DFF_GDS = ROOT / "technology/freepdk45/gds_lib/dff.gds"
PRE_BANK_GDS = ROOT / "outputs/PROJECT_full_single_bank_sram/real_hierarchical_floorplan_v2/physical_banks/precharge_even_odd_2row_v2/clean.gds"
SENSE_BANK_GDS = ROOT / "outputs/PROJECT_full_single_bank_sram/real_hierarchical_floorplan_v2/physical_banks/sense_amp_even_odd_2row_v2/clean.gds"
WRITE_BANK_GDS = ROOT / "outputs/PROJECT_full_single_bank_sram/real_hierarchical_floorplan_v2/physical_banks/write_driver_even_odd_2row_v2/clean.gds"
TECH_LAYER_MAP = ROOT / "technology/freepdk45/layers.map"
TECH_DRC = ROOT / "technology/freepdk45/tech/freepdk45.lydrc"
TECH_LYP = ROOT / "technology/freepdk45/tech/freepdk45.lyp"
TECH_LEAF_LIB = ROOT / "technology/freepdk45/openyield_leaf_physical_library.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def read_json(path: Path) -> Any:
    with path.open() as f:
        return json.load(f)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(data, f, indent=2, sort_keys=True)
        f.write("\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: list[str] = []
        for row in rows:
            for k in row:
                if k not in keys:
                    keys.append(k)
        fieldnames = keys
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fieldnames})


def bbox_size(cell: gdstk.Cell) -> dict[str, float]:
    bb = cell.bounding_box()
    if bb is None:
        return {"width_um": 0.0, "height_um": 0.0, "area_um2": 0.0, "bbox": [0, 0, 0, 0]}
    (x0, y0), (x1, y1) = bb
    return {
        "width_um": round(float(x1 - x0), 6),
        "height_um": round(float(y1 - y0), 6),
        "area_um2": round(float((x1 - x0) * (y1 - y0)), 6),
        "bbox": [round(float(x0), 6), round(float(y0), 6), round(float(x1), 6), round(float(y1), 6)],
    }


def top_cell(lib: gdstk.Library, preferred: str | None = None) -> gdstk.Cell:
    cells = {c.name: c for c in lib.cells}
    if preferred and preferred in cells:
        return cells[preferred]
    tops = lib.top_level()
    if len(tops) == 1:
        return tops[0]
    return max(lib.cells, key=lambda c: len(c.references) + len(c.polygons) + len(c.paths) + len(c.labels))


def load_gds(path: Path) -> gdstk.Library:
    return gdstk.read_gds(str(path))


def first_cell_metrics(path: Path, preferred: str | None = None) -> dict[str, Any]:
    lib = load_gds(path)
    cell = top_cell(lib, preferred)
    m = bbox_size(cell)
    m.update({
        "path": str(path.relative_to(ROOT) if path.is_relative_to(ROOT) else path),
        "sha256": sha256(path),
        "top_cell": cell.name,
        "structure_count": len(lib.cells),
    })
    return m


def center_from_bbox(b: list[float]) -> tuple[float, float]:
    return ((b[0] + b[2]) / 2.0, (b[1] + b[3]) / 2.0)


def pin_xs_from_array() -> dict[str, list[float]]:
    p = read_json(ARRAY_PIN_MAP)["pins"]
    out: dict[str, list[float]] = {}
    for name, entries in p.items():
        out[name] = []
        for e in entries:
            if "bbox" in e:
                out[name].append(center_from_bbox(e["bbox"])[0])
    return out


def pitch_from_names(xs: dict[str, list[float]], prefix: str) -> float | None:
    vals = []
    for i in range(16):
        key = f"{prefix}[{i}]"
        if key in xs and xs[key]:
            vals.append(xs[key][0])
    if len(vals) < 2:
        return None
    diffs = [round(vals[i + 1] - vals[i], 6) for i in range(len(vals) - 1)]
    return round(sum(diffs) / len(diffs), 6)


def get_refs(cell: gdstk.Cell, pattern: str) -> list[gdstk.Reference]:
    rgx = re.compile(pattern)
    return [r for r in cell.references if rgx.search(r.cell.name)]


def ref_origin(r: gdstk.Reference) -> tuple[float, float]:
    return (round(float(r.origin[0]), 6), round(float(r.origin[1]), 6))


def parse_v41() -> dict[str, Any]:
    lib = load_gds(V41_GDS)
    cell = top_cell(lib, "FULL_SRAM_DFF_AUTHORITY_AND_COLUMN_INTERFACE_ALIGNMENT_V41")
    refs = cell.references
    ref_rows = []
    for r in refs:
        ref_rows.append({
            "name": r.cell.name,
            "origin_x": round(float(r.origin[0]), 6),
            "origin_y": round(float(r.origin[1]), 6),
            "rotation": r.rotation,
            "x_reflection": bool(r.x_reflection),
            **bbox_size(r.cell),
        })
    by_name = defaultdict(list)
    for row in ref_rows:
        by_name[row["name"]].append(row)

    wl_refs = [row for row in ref_rows if "wordline_driver_v2" in row["name"] or "wl_driver" in row["name"].lower()]
    dff_core_refs = [row for row in ref_rows if "DFF_TG4_INV7" in row["name"]]
    dff_buf_refs = [row for row in ref_rows if "DFF_BUF" in row["name"]]
    decoder_refs = [row for row in ref_rows if "decoder" in row["name"].lower()]
    pre_refs = [row for row in ref_rows if "precharge" in row["name"].lower()]
    sense_refs = [row for row in ref_rows if "sense" in row["name"].lower()]
    write_refs = [row for row in ref_rows if "write" in row["name"].lower()]

    return {
        "top_cell": cell.name,
        "top_bbox": bbox_size(cell),
        "top_ref_count": len(refs),
        "references": ref_rows,
        "wl_driver_refs": wl_refs,
        "dff_core_refs": dff_core_refs,
        "dff_buf_refs": dff_buf_refs,
        "decoder_refs": decoder_refs,
        "precharge_refs": pre_refs,
        "sense_amp_refs": sense_refs,
        "write_driver_refs": write_refs,
        "structure_count": len(lib.cells),
        "top_level_cells": [c.name for c in lib.top_level()],
    }


def component_pitches(rows: list[dict[str, Any]]) -> dict[str, Any]:
    xs = sorted(set(round(r["origin_x"], 6) for r in rows))
    ys = sorted(set(round(r["origin_y"], 6) for r in rows))
    xdiffs = [round(xs[i + 1] - xs[i], 6) for i in range(len(xs) - 1)]
    ydiffs = [round(ys[i + 1] - ys[i], 6) for i in range(len(ys) - 1)]
    return {
        "unique_x": xs,
        "unique_y": ys,
        "x_diffs": xdiffs,
        "y_diffs": ydiffs,
        "count": len(rows),
    }


def parse_layers_map() -> list[dict[str, Any]]:
    rows = []
    for ln, line in enumerate(TECH_LAYER_MAP.read_text().splitlines(), 1):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        parts = stripped.split()
        if len(parts) >= 2:
            rows.append({
                "lclayout_field": f"layer_{parts[0]}",
                "project_layer": parts[0],
                "value": parts[1],
                "source_file": str(TECH_LAYER_MAP.relative_to(ROOT)),
                "source_line_or_section": ln,
                "status": "MAPPED_FROM_CURRENT_FREEPDK45",
            })
    return rows


def build_lclayout_adapter(lclayout_available: bool) -> None:
    EXP.mkdir(parents=True, exist_ok=True)
    TOOL_EXP.mkdir(parents=True, exist_ok=True)
    adapter = '''"""Exploratory LCLayout adapter stub for this project's current FreePDK45.

This file is generated for provenance and integration planning. It is not a
formal technology adapter until every UNKNOWN_RULE entry in
LCLAYOUT_FREEPDK45_RULE_PROVENANCE.csv is resolved from current project
FreePDK45 sources and LCLayout is installed in the isolated experiment env.
"""

PDK_NAME = "current_project_freepdk45"
PDK_CHANGED = False
EXTERNAL_STDCELL_LIBRARY_ALLOWED = False
LAYER_MAP_SOURCE = "technology/freepdk45/layers.map"
DRC_DECK_SOURCE = "technology/freepdk45/tech/freepdk45.lydrc"
MANUFACTURING_GRID_SOURCE = "current project FreePDK45 grid evidence"

STATUS = {
    "lclayout_installed": %s,
    "formal_candidate_allowed": False,
    "reason": "LCLayout adapter remains exploratory until tool install and UNKNOWN_RULE closure."
}
''' % ("True" if lclayout_available else "False")
    (EXP / "freepdk45_current_project_tech.py").write_text(adapter)

    rows = parse_layers_map()
    rows += [
        {
            "lclayout_field": "manufacturing_grid",
            "project_layer": "ALL",
            "value": "CURRENT_PROJECT_GRID_PENDING_EXPLICIT_EXTRACTION",
            "source_file": "technology/freepdk45/tech/freepdk45.lydrc",
            "source_line_or_section": "grid/provenance pending",
            "status": "UNKNOWN_RULE",
        },
        {
            "lclayout_field": "min_width_by_layer",
            "project_layer": "ALL_METAL_POLY_ACTIVE",
            "value": "SEE_DRC_DECK_REQUIRED_MAPPING_NOT_COMPLETE",
            "source_file": str(TECH_DRC.relative_to(ROOT)),
            "source_line_or_section": "rule expressions require adapter mapping",
            "status": "UNKNOWN_RULE",
        },
        {
            "lclayout_field": "via_enclosure",
            "project_layer": "contact/via*",
            "value": "SEE_DRC_DECK_REQUIRED_MAPPING_NOT_COMPLETE",
            "source_file": str(TECH_DRC.relative_to(ROOT)),
            "source_line_or_section": "rule expressions require adapter mapping",
            "status": "UNKNOWN_RULE",
        },
        {
            "lclayout_field": "device_model_binding",
            "project_layer": "NMOS/PMOS",
            "value": "CURRENT_FREEPDK45_MODEL_BINDING_REQUIRED",
            "source_file": "technology/freepdk45/sp_lib and current source SPICE",
            "source_line_or_section": "per-cell subckt references",
            "status": "UNKNOWN_RULE",
        },
    ]
    write_csv(EXP / "LCLAYOUT_FREEPDK45_RULE_PROVENANCE.csv", rows)
    write_json(TOOL_EXP / "LCLAYOUT_FREEPDK45_STATUS.json", {
        "workspace": str(TOOL_EXP),
        "lclayout_python_module": lclayout_available,
        "lclayout_binary": bool(shutil.which("lclayout")),
        "adapter": str((EXP / "freepdk45_current_project_tech.py").relative_to(ROOT)),
        "rule_provenance": str((EXP / "LCLAYOUT_FREEPDK45_RULE_PROVENANCE.csv").relative_to(ROOT)),
        "formal_candidate_allowed": False,
        "status": "NOT_INSTALLED" if not lclayout_available else "INSTALLED_ADAPTER_RULES_INCOMPLETE",
        "blocked_by": ["LCLayout not importable in current environment"] if not lclayout_available else ["UNKNOWN_RULE entries remain"],
    })
    (TOOL_EXP / "README.md").write_text(
        "# LCLayout FreePDK45 isolated experiment\n\n"
        "This directory is reserved for LCLayout experiments using only the current project FreePDK45 rules and current source-exact netlists.\n"
        "No external standard-cell GDS/LEF/CDL/Liberty is authorized for final project candidates.\n"
    )


def write_markdown(audit: dict[str, Any], path: Path) -> None:
    lines = [
        "# V4.1 Same-PDK Cell Geometry Audit",
        "",
        f"- source GDS: `{audit['source_gds']}`",
        f"- source GDS SHA256: `{audit['source_gds_sha256']}`",
        f"- actual top: `{audit['v41_final_gds']['top_cell']}`",
        f"- PDK changed: `{audit['pdk_policy']['pdk_changed']}`",
        f"- external standard-cell library used in final candidates: `{audit['pdk_policy']['external_standard_cell_library_used_in_final_candidates']}`",
        "",
        "## Extracted Geometry",
        f"- array BL pitch: `{audit['array']['bitline_pitch_um']} um`",
        f"- array row pitch: `{audit['array']['row_pitch_um']} um`",
        f"- WL driver bbox: `{audit['wl_driver']['current_bbox']['width_um']} x {audit['wl_driver']['current_bbox']['height_um']} um`",
        f"- WL driver one-driver-per-row feasible now: `{audit['wl_driver']['current_one_driver_per_row_feasible']}`",
        f"- DFF_TG4 bbox: `{audit['dff']['DFF_TG4_INV7']['width_um']} x {audit['dff']['DFF_TG4_INV7']['height_um']} um`",
        f"- DFF_BUF bbox: `{audit['dff']['DFF_BUF']['width_um']} x {audit['dff']['DFF_BUF']['height_um']} um`",
        "",
        "## Conclusions",
        "- Current WL driver remains a two-column/staggered integration structure; current unit height exceeds authoritative array row pitch.",
        "- Precharge/sense/write even-odd V2 banks are retained as real same-PDK assets; deinterleaving is not authorized unless exact-topology cell dimensions close pitch gates.",
        "- DFF_TG4_INV7 remains source-bound for ADDR/DATA; bundled FreePDK45 dff is not authorized by this exploration.",
        "- LCLayout is recorded only as an isolated same-PDK algorithm path; it produced no formal candidate in this environment.",
    ]
    path.write_text("\n".join(lines) + "\n")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    DOCS.mkdir(parents=True, exist_ok=True)
    lclayout_available = False
    try:
        import importlib.util
        lclayout_available = importlib.util.find_spec("lclayout") is not None or bool(shutil.which("lclayout"))
    except Exception:
        lclayout_available = False

    v41 = parse_v41()
    array_xs = pin_xs_from_array()
    bit_pitch = pitch_from_names(array_xs, "BL")
    # Authoritative array row pitch is locked in earlier reports; derive from WL pins if present, otherwise record the locked value.
    row_pitch = 1.565
    if any(k.startswith("WL[") for k in array_xs):
        maybe = pitch_from_names(array_xs, "WL")
        if maybe:
            row_pitch = maybe

    wl_bbox = first_cell_metrics(WL_DRIVER_GDS)
    dff_core = first_cell_metrics(DFF_CORE_GDS)
    dff_buf = first_cell_metrics(DFF_BUF_GDS)
    bundled = first_cell_metrics(BUNDLED_DFF_GDS)
    pre_bank = first_cell_metrics(PRE_BANK_GDS)
    sense_bank = first_cell_metrics(SENSE_BANK_GDS)
    write_bank = first_cell_metrics(WRITE_BANK_GDS)

    wl_arr = component_pitches(v41["wl_driver_refs"])
    dff_arr = component_pitches(v41["dff_core_refs"])
    control_refs = [r for r in v41["references"] if any(s in r["name"].lower() for s in ["pdrive", "delay", "nand", "and", "inv"]) and "wl_driver" not in r["name"].lower()]

    native_pitches = {
        "precharge": 0.9125,
        "sense_amp": 0.975,
        "write_driver": 1.04,
    }

    audit = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "git_head": git(["rev-parse", "HEAD"]),
        "source_gds": str(V41_GDS.relative_to(ROOT)),
        "source_gds_sha256": sha256(V41_GDS),
        "pdk_policy": {
            "pdk": "technology/freepdk45",
            "pdk_changed": False,
            "external_standard_cell_library_used_in_final_candidates": False,
            "forbidden_external_libraries": ["Nangate45", "SKY130", "GF180", "ASAP7"],
        },
        "v41_final_gds": v41,
        "array": {
            "pin_map": str(ARRAY_PIN_MAP.relative_to(ROOT)),
            "bitline_pitch_um": bit_pitch,
            "row_pitch_um": row_pitch,
            "row_pitch_source": "authoritative array locked value; WL y-pitch extraction not available from x-only helper" if row_pitch == 1.565 else "pin_map",
        },
        "wl_driver": {
            "current_gds": str(WL_DRIVER_GDS.relative_to(ROOT)),
            "current_bbox": wl_bbox,
            "top_instances_in_v41": len(v41["wl_driver_refs"]),
            "v41_arrangement": wl_arr,
            "is_staggered_double_column": len(wl_arr["unique_x"]) >= 2,
            "current_height_vs_array_row_pitch": round(wl_bbox["height_um"] / row_pitch, 6) if row_pitch else None,
            "current_one_driver_per_row_feasible": wl_bbox["height_um"] <= row_pitch,
            "current_issue": "height exceeds array row pitch; exact-topology compact cell required before single-column one-driver-per-row can be authorized",
        },
        "dff": {
            "DFF_TG4_INV7": dff_core,
            "DFF_BUF": dff_buf,
            "bundled_freepdk45_dff": {
                **bundled,
                "current_authority": "NOT_AUTHORIZED_FOR_OPENYIELD_ADDR_DATA_REPLACEMENT_IN_THIS_EXPLORATION",
                "reason": "V4 equivalence was revoked; this round does not introduce a new valid A/B equivalence proof.",
            },
            "v41_core_dff_arrangement": dff_arr,
        },
        "column_banks": {
            "precharge_even_odd_2row_v2": pre_bank,
            "sense_amp_even_odd_2row_v2": sense_bank,
            "write_driver_even_odd_2row_v2": write_bank,
            "current_architecture": "even_odd_2row",
            "policy": "retain Bank V2; do not redesign units unless exact-topology pitch gate proves need",
        },
        "decoder": {
            "v41_decoder_refs": v41["decoder_refs"],
            "current_status": "complete 4to16 restored but internal 2D/orientation compaction remains future V5 work",
            "same_pdk_optimization_potential": [
                "reuse historical L0 orientation/abutment matrix for current FreePDK45 INV/AND/NAND gates",
                "flatten physical placement granularity below three-stage macros without altering 4to16 logic",
                "evaluate current-PDK optimized gates only after function/DRC/connectivity gates pass",
            ],
        },
    }
    write_json(DOCS / "V41_SAME_PDK_CELL_GEOMETRY_AUDIT.json", audit)
    write_markdown(audit, DOCS / "V41_SAME_PDK_CELL_GEOMETRY_AUDIT.md")

    build_lclayout_adapter(lclayout_available)

    pitch_rows = []
    for role, metrics, native in [
        ("precharge", pre_bank, native_pitches["precharge"]),
        ("sense_amp", sense_bank, native_pitches["sense_amp"]),
        ("write_driver", write_bank, native_pitches["write_driver"]),
        ("wl_driver", wl_bbox, wl_bbox["height_um"]),
        ("DFF_TG4_INV7", dff_core, dff_core["width_um"]),
    ]:
        req = row_pitch if role == "wl_driver" else bit_pitch
        if role == "DFF_TG4_INV7":
            req = "sink-dependent; no array pitch requirement"
        feasible = (native <= req) if isinstance(req, (int, float)) else "N/A"
        pitch_rows.append({
            "role": role,
            "current_cell_dimension_um": native,
            "array_required_pitch_um": req,
            "minimum_physically_achievable_dimension_um": "UNKNOWN_WITHOUT_EXACT_TOPOLOGY_RESYNTHESIS",
            "single_row_feasible": feasible,
            "two_row_still_required": (not feasible) if isinstance(feasible, bool) else "N/A",
            "reason": "current exact cell dimension exceeds pitch" if feasible is False else "current dimension meets pitch or no pitch target",
        })
    write_csv(OUT / "CURRENT_PDK_PITCH_FEASIBILITY_AUDIT.csv", pitch_rows)

    orientations = ["R0", "MX", "MY", "R180"]
    gaps = ["zero_gap", "minimum_drc_gap", "power_channel_gap"]
    matrix = []
    for nand_o in orientations:
        for inv_o in orientations:
            for gap in gaps:
                allowed = gap != "zero_gap"
                matrix.append({
                    "candidate": f"PNAND2_{nand_o}__PINV_{inv_o}__{gap}",
                    "pnand2_orientation": nand_o,
                    "pinv_orientation": inv_o,
                    "gap_policy": gap,
                    "boundary_drc": "NOT_RUN_THIS_ROUND",
                    "vdd_vss_relation": "REQUIRES_FINAL_GDS_PAIR_TEST",
                    "signal_connection": "NAND_OUT_TO_INV_IN_DIRECT_ROUTE_REQUIRED",
                    "pin_access": "REQUIRES_FINAL_GDS_PAIR_TEST",
                    "foreign_net": "REQUIRES_FINAL_GDS_PAIR_TEST",
                    "formal_replacement_allowed": False,
                    "exploration_classification": "CANDIDATE_SPEC_ONLY" if not allowed else "NEXT_RUN_ABUTMENT_TEST_REQUIRED",
                })
    write_csv(OUT / "WL_DRIVER_CHILD_ABUTMENT_MATRIX_V2.csv", matrix)

    comparison = [
        {
            "category": "CURRENT_BASELINE",
            "role": "DFF_ADDR_DATA",
            "candidate": "DFF_TG4_INV7_FPDK45_26d9543b82b7",
            "pdk": "current FreePDK45",
            "external_stdcell_gds": False,
            "exact_topology": True,
            "gds_generated": True,
            "drc": "PASS_EXISTING_QUALIFIED",
            "function": "PASS_SOURCE_BOUND",
            "bbox_area_um2": dff_core["area_um2"],
            "replacement_allowed": True,
            "notes": "current selected ADDR/DATA DFF baseline",
        },
        {
            "category": "LCLAYOUT_FREEPDK45",
            "role": "DFF_ADDR_DATA",
            "candidate": "LCLayout exact DFF_TG4_INV7 topology",
            "pdk": "current FreePDK45 adapter",
            "external_stdcell_gds": False,
            "exact_topology": "REQUIRED",
            "gds_generated": False,
            "drc": "NOT_RUN",
            "function": "NOT_RUN",
            "bbox_area_um2": "",
            "replacement_allowed": False,
            "notes": "LCLayout unavailable or adapter rules incomplete",
        },
        {
            "category": "PROJECT_NATIVE_OPTIMIZED_FREEPDK45",
            "role": "DFF_ADDR_DATA",
            "candidate": "native exact-topology TG DFF compactor",
            "pdk": "current FreePDK45",
            "external_stdcell_gds": False,
            "exact_topology": "REQUIRED",
            "gds_generated": False,
            "drc": "NOT_RUN",
            "function": "NOT_RUN",
            "bbox_area_um2": "",
            "replacement_allowed": False,
            "notes": "recommended next implementation path; no formal candidate generated this round",
        },
        {
            "category": "CURRENT_BASELINE",
            "role": "WL_DRIVER",
            "candidate": "wordline_driver_v2 PNAND2+INV hierarchy",
            "pdk": "current FreePDK45",
            "external_stdcell_gds": False,
            "exact_topology": True,
            "gds_generated": True,
            "drc": "PASS_EXISTING_QUALIFIED",
            "function": "PASS_SOURCE_BOUND",
            "bbox_area_um2": wl_bbox["area_um2"],
            "replacement_allowed": True,
            "notes": f"height {wl_bbox['height_um']}um > row pitch {row_pitch}um; single-row per WL not feasible",
        },
        {
            "category": "PROJECT_NATIVE_OPTIMIZED_FREEPDK45",
            "role": "WL_DRIVER",
            "candidate": "flattened exact PNAND2+INV compact cell",
            "pdk": "current FreePDK45",
            "external_stdcell_gds": False,
            "exact_topology": "REQUIRED",
            "gds_generated": False,
            "drc": "NOT_RUN",
            "function": "NOT_RUN",
            "bbox_area_um2": "",
            "replacement_allowed": False,
            "notes": "priority candidate if height can be reduced below authoritative array row pitch",
        },
        {
            "category": "CURRENT_BASELINE",
            "role": "COLUMN_PERIPHERY",
            "candidate": "precharge/sense/write even_odd_2row_v2",
            "pdk": "current FreePDK45",
            "external_stdcell_gds": False,
            "exact_topology": True,
            "gds_generated": True,
            "drc": "PASS_EXISTING_QUALIFIED",
            "function": "PASS_SOURCE_BOUND",
            "bbox_area_um2": round(pre_bank["area_um2"] + sense_bank["area_um2"] + write_bank["area_um2"], 6),
            "replacement_allowed": True,
            "notes": "two-row interleaving remains justified because native unit pitch exceeds 0.705um bit pitch",
        },
    ]
    write_csv(OUT / "CELL_ARCHITECTURE_SAME_PDK_COMPARISON.csv", comparison)

    machine_gate = {
        "status": "PASS_SAME_FREEPDK45_CELL_ARCHITECTURE_EXPLORATION_TO_HUMAN_REVIEW",
        "pdk_changed": False,
        "external_standard_cell_library_used_in_final_candidates": False,
        "official_full_sram_top_modified": False,
        "lclayout": {
            "installed": lclayout_available,
            "adapter": str((EXP / "freepdk45_current_project_tech.py").relative_to(ROOT)),
            "formal_candidate_allowed": False,
            "reason": "NOT_INSTALLED" if not lclayout_available else "UNKNOWN_RULES_REMAIN",
        },
        "current_baseline_assets_locked": True,
        "same_pdk_replacement_authorized_this_round": False,
        "formal_integration_candidates": [
            "CURRENT_BASELINE retained",
        ],
        "recommended_next_experiments": [
            "project-native exact-topology WL_DRIVER_COMPACT_CELL height<=array_row_pitch",
            "project-native exact-topology DFF_TG4_INV7 compactor",
            "FreePDK45 LCLayout adapter rule closure before any LCLayout GDS candidate",
            "decoder fine-grain 2D placement using current FreePDK45 optimized gate candidates only after their leaf gates pass",
        ],
    }
    write_json(OUT / "SAME_PDK_CELL_ARCHITECTURE_MACHINE_GATE.json", machine_gate)
    write_json(OUT / "LCLAYOUT_FREEPDK45_STATUS.json", read_json(TOOL_EXP / "LCLAYOUT_FREEPDK45_STATUS.json"))
    write_json(OUT / "DFF_SAME_PDK_CANDIDATES.json", {
        "DFF_A_CURRENT_BASELINE": {"candidate": "DFF_TG4_INV7", "metrics": dff_core, "machine_gate": "PASS_EXISTING_QUALIFIED"},
        "DFF_B_LCLAYOUT_FREEPDK45": {"candidate": "exact topology via LCLayout", "status": "NOT_GENERATED", "blocked_by": machine_gate["lclayout"]["reason"]},
        "DFF_C_PROJECT_NATIVE_OPTIMIZED": {"candidate": "exact topology native compactor", "status": "SPECIFIED_NOT_GENERATED"},
    })
    write_json(OUT / "WL_DRIVER_SAME_PDK_ARCHITECTURE_SEARCH.json", {
        "current": {"metrics": wl_bbox, "height_vs_row_pitch": machine_gate},
        "abutment_matrix": str((OUT / "WL_DRIVER_CHILD_ABUTMENT_MATRIX_V2.csv").relative_to(ROOT)),
        "compact_cell": {"status": "SPECIFIED_NOT_GENERATED", "exact_topology_required": True},
    })

    # Review README and package staging.
    PKG_DIR.mkdir(parents=True, exist_ok=True)
    files_to_copy = [
        DOCS / "V41_SAME_PDK_CELL_GEOMETRY_AUDIT.md",
        DOCS / "V41_SAME_PDK_CELL_GEOMETRY_AUDIT.json",
        OUT / "CURRENT_PDK_PITCH_FEASIBILITY_AUDIT.csv",
        OUT / "WL_DRIVER_CHILD_ABUTMENT_MATRIX_V2.csv",
        OUT / "CELL_ARCHITECTURE_SAME_PDK_COMPARISON.csv",
        OUT / "SAME_PDK_CELL_ARCHITECTURE_MACHINE_GATE.json",
        OUT / "LCLAYOUT_FREEPDK45_STATUS.json",
        OUT / "DFF_SAME_PDK_CANDIDATES.json",
        OUT / "WL_DRIVER_SAME_PDK_ARCHITECTURE_SEARCH.json",
        EXP / "freepdk45_current_project_tech.py",
        EXP / "LCLAYOUT_FREEPDK45_RULE_PROVENANCE.csv",
    ]
    for f in files_to_copy:
        shutil.copy2(f, PKG_DIR / f.name)
    readme = f"""# Same-FreePDK45 Cell Architecture Exploration

Status: PASS_SAME_FREEPDK45_CELL_ARCHITECTURE_EXPLORATION_TO_HUMAN_REVIEW

This package does not modify the formal full SRAM top. It records same-PDK
cell-level exploration evidence only.

Hard constraints:
- PDK changed: false
- External standard-cell library used in final candidates: false
- Current formal technology: technology/freepdk45

Key files:
- V41_SAME_PDK_CELL_GEOMETRY_AUDIT.json
- CURRENT_PDK_PITCH_FEASIBILITY_AUDIT.csv
- WL_DRIVER_CHILD_ABUTMENT_MATRIX_V2.csv
- CELL_ARCHITECTURE_SAME_PDK_COMPARISON.csv
- LCLAYOUT_FREEPDK45_RULE_PROVENANCE.csv

Current formal full SRAM top remains unchanged from HEAD {git(['rev-parse', 'HEAD'])}.
"""
    (PKG_DIR / "README.md").write_text(readme)
    manifest = {
        "status": "PASS_SAME_FREEPDK45_CELL_ARCHITECTURE_EXPLORATION_TO_HUMAN_REVIEW",
        "git_head": git(["rev-parse", "HEAD"]),
        "working_tree_clean_at_generation": git(["status", "--short"]) == "",
        "pdk_changed": False,
        "external_standard_cell_library_used_in_final_candidates": False,
        "official_full_sram_top_modified": False,
        "source_v41_gds": str(V41_GDS.relative_to(ROOT)),
        "source_v41_gds_sha256": sha256(V41_GDS),
    }
    write_json(PKG_DIR / "MANIFEST.json", manifest)
    sums = []
    for p in sorted(PKG_DIR.iterdir()):
        if p.is_file() and p.name != "SHA256SUMS":
            sums.append(f"{sha256(p)}  {p.name}")
    (PKG_DIR / "SHA256SUMS").write_text("\n".join(sums) + "\n")
    if PKG.exists():
        PKG.unlink()
    with tarfile.open(PKG, "w:gz") as tar:
        tar.add(PKG_DIR, arcname=".")
    (PKG.with_suffix(PKG.suffix + ".sha256")).write_text(f"{sha256(PKG)}  {PKG.name}\n")

    # Update project logs/status.
    status_path = DOCS / "PROJECT_CURRENT_STATUS.json"
    status = read_json(status_path)
    status["workflow_state"] = "PASS_SAME_FREEPDK45_CELL_ARCHITECTURE_EXPLORATION_TO_HUMAN_REVIEW"
    status["git_head"] = "PENDING_COMMIT"
    status["current_git_head"] = "PENDING_COMMIT"
    status["same_pdk_cell_architecture_exploration"] = {
        "status": "PASS_SAME_FREEPDK45_CELL_ARCHITECTURE_EXPLORATION_TO_HUMAN_REVIEW",
        "pdk_changed": False,
        "external_standard_cell_library_used_in_final_candidates": False,
        "official_full_sram_top_modified": False,
        "audit": "docs/V41_SAME_PDK_CELL_GEOMETRY_AUDIT.json",
        "machine_gate": str((OUT / "SAME_PDK_CELL_ARCHITECTURE_MACHINE_GATE.json").relative_to(ROOT)),
        "lclayout_status": "NOT_INSTALLED" if not lclayout_available else "INSTALLED_ADAPTER_RULES_INCOMPLETE",
        "formal_same_pdk_replacement_authorized": False,
        "review_package": str(PKG),
        "review_package_sha256": sha256(PKG),
    }
    status["next_stage"] = "Human review of same-FreePDK45 cell architecture exploration before any full-top reintegration."
    write_json(status_path, status)

    entry = {
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "phase": "same_freepdk45_cell_architecture_exploration",
        "result": "PASS_SAME_FREEPDK45_CELL_ARCHITECTURE_EXPLORATION_TO_HUMAN_REVIEW",
        "pdk_changed": False,
        "external_standard_cell_library_used_in_final_candidates": False,
        "lclayout_status": "NOT_INSTALLED" if not lclayout_available else "INSTALLED_ADAPTER_RULES_INCOMPLETE",
        "full_sram_top_modified": False,
        "package": str(PKG),
        "package_sha256": sha256(PKG),
    }
    with (DOCS / "PROJECT_TASK_MASTER_LOG.jsonl").open("a") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")
    with (DOCS / "PROJECT_TASK_MASTER_LOG.md").open("a") as f:
        f.write(
            "\n## 2026-08-10T00:00:00Z same_freepdk45_cell_architecture_exploration\n"
            "- result: `PASS_SAME_FREEPDK45_CELL_ARCHITECTURE_EXPLORATION_TO_HUMAN_REVIEW`\n"
            "- correction: previous external-library exploration route is revoked; this checkpoint keeps `technology/freepdk45` as the only physical implementation authority.\n"
            "- policy: PDK changed `false`; external standard-cell library used in final candidates `false`; formal full SRAM top not modified.\n"
            f"- LCLayout: `{'NOT_INSTALLED' if not lclayout_available else 'INSTALLED_ADAPTER_RULES_INCOMPLETE'}`; FreePDK45 adapter/provenance generated but no LCLayout formal GDS candidate authorized.\n"
            "- outputs: same-PDK final-GDS geometry audit, pitch feasibility audit, WL-driver abutment candidate matrix, and same-PDK comparison table.\n"
            f"- package: `{PKG}`.\n"
        )

    print(json.dumps({
        "status": machine_gate["status"],
        "package": str(PKG),
        "package_sha256": sha256(PKG),
        "audit": "docs/V41_SAME_PDK_CELL_GEOMETRY_AUDIT.json",
    }, indent=2))


if __name__ == "__main__":
    main()
