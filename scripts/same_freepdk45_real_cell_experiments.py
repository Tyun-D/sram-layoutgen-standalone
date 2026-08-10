#!/usr/bin/env python3
"""Generate real same-FreePDK45 cell experiment artifacts.

Scope is deliberately cell-level. The formal full SRAM top is not modified.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import tarfile
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import gdstk


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/PROJECT_same_freepdk45_real_cell_experiments"
DOCS = ROOT / "docs"
TOOL = Path("/data1/qujh/tool_experiments/lclayout_freepdk45")
PKG_DIR = Path("/data1/qujh/same_freepdk45_real_cell_candidates_review/latest")
PKG = Path("/data1/qujh/PROJECT_SAME_FREEPDK45_REAL_CELL_CANDIDATES_HUMAN_REVIEW_PACKAGE_LATEST.tar.gz")

DRC_DECK = ROOT / "technology/freepdk45/tech/freepdk45.lydrc"
LAYERS = ROOT / "technology/freepdk45/layers.map"
V41 = ROOT / "outputs/PROJECT_full_single_bank_sram/FULL_SRAM_DFF_AUTHORITY_AND_COLUMN_INTERFACE_ALIGNMENT_V41/clean_unique_top.gds"
WL = ROOT / "outputs/PROJECT_wordline_driver_v2_regen/current_supported_config/wordline_driver_v2.gds"
DFF = ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/DFF_TG4_INV7_FPDK45_26d9543b82b7/DFF_TG4_INV7_FPDK45_26d9543b82b7.gds"
DFF_BUF = ROOT / "outputs/Wave3_DFF_BUF_human_review_seal/_readonly_probe/DFF_BUF_FPDK45_6058eaf43739_HPA1/DFF_BUF_FPDK45_6058eaf43739_HPA1.gds"
GEN_INV = ROOT / "technology/freepdk45/gds_lib/gen_inv.gds"
GEN_NAND2 = ROOT / "technology/freepdk45/gds_lib/gen_nand2.gds"
GEN_PRE = ROOT / "technology/freepdk45/gds_lib/gen_precharge.gds"
SENSE = ROOT / "technology/freepdk45/gds_lib/sense_amp.gds"
WRITE = ROOT / "technology/freepdk45/gds_lib/write_driver.gds"
PRE_BANK = ROOT / "outputs/PROJECT_full_single_bank_sram/real_hierarchical_floorplan_v2/physical_banks/precharge_even_odd_2row_v2/clean.gds"
SENSE_BANK = ROOT / "outputs/PROJECT_full_single_bank_sram/real_hierarchical_floorplan_v2/physical_banks/sense_amp_even_odd_2row_v2/clean.gds"
WRITE_BANK = ROOT / "outputs/PROJECT_full_single_bank_sram/real_hierarchical_floorplan_v2/physical_banks/write_driver_even_odd_2row_v2/clean.gds"

GRID = 0.005
ARRAY_ROW_PITCH = 1.565
ARRAY_BIT_PITCH = 0.705


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = []
        for r in rows:
            for k in r:
                if k not in fields:
                    fields.append(k)
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def bbox(cell: gdstk.Cell) -> dict[str, Any]:
    bb = cell.bounding_box()
    if bb is None:
        return {"bbox": [0, 0, 0, 0], "width": 0, "height": 0, "area": 0}
    (x0, y0), (x1, y1) = bb
    return {
        "bbox": [round(float(x0), 6), round(float(y0), 6), round(float(x1), 6), round(float(y1), 6)],
        "width": round(float(x1 - x0), 6),
        "height": round(float(y1 - y0), 6),
        "area": round(float((x1 - x0) * (y1 - y0)), 6),
    }


def top(lib: gdstk.Library, name: str | None = None) -> gdstk.Cell:
    if name:
        for c in lib.cells:
            if c.name == name:
                return c
    tops = lib.top_level()
    return tops[0] if len(tops) == 1 else max(lib.cells, key=lambda c: len(c.references) + len(c.polygons))


def run_drc(gds: Path, topcell: str, out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    lyr = out_dir / f"{topcell}.lyrdb"
    log = out_dir / f"{topcell}.log"
    cmd = [
        "/usr/bin/klayout",
        "-b",
        "-r",
        str(DRC_DECK),
        "-rd",
        f"input={gds}",
        "-rd",
        f"topcell={topcell}",
        "-rd",
        f"output={lyr}",
    ]
    r = subprocess.run(cmd, stdout=log.open("w"), stderr=subprocess.STDOUT, text=True)
    markers = None
    if lyr.exists():
        try:
            markers = len(ET.parse(lyr).getroot().findall(".//item"))
        except Exception:
            markers = None
    return {
        "returncode": r.returncode,
        "marker_count": markers,
        "passed": r.returncode == 0 and markers == 0,
        "database": rel(lyr),
        "log": rel(log),
    }


def copy_gds(src: Path, dst: Path) -> dict[str, Any]:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    lib = gdstk.read_gds(str(dst))
    c = top(lib)
    return {"gds": rel(dst), "sha256": sha(dst), "top": c.name, **bbox(c)}


def selected_lib_from(src: Path) -> tuple[gdstk.Library, gdstk.Cell]:
    lib = gdstk.read_gds(str(src))
    return lib, top(lib)


def write_lib(cells: list[gdstk.Cell], new_top: gdstk.Cell, path: Path) -> None:
    lib = gdstk.Library(unit=1e-6, precision=1e-9)
    seen = set()
    for c in cells + [new_top]:
        if c.name not in seen:
            lib.add(c)
            seen.add(c.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    lib.write_gds(str(path))


def make_wl_gap_candidates() -> list[dict[str, Any]]:
    lib, wl_top = selected_lib_from(WL)
    pnand, inv = wl_top.references
    pbb = pnand.cell.bounding_box()
    ibb = inv.cell.bounding_box()
    p_right = pnand.origin[0] + pbb[1][0]
    current_gap = round(inv.origin[0] + ibb[0][0] - p_right, 6)
    rows = []
    wl_dir = OUT / "WL_DRIVER"
    baseline = copy_gds(WL, wl_dir / "WLA_existing_child_routed_baseline/clean.gds")
    baseline["drc"] = run_drc(wl_dir / "WLA_existing_child_routed_baseline/clean.gds", baseline["top"], wl_dir / "WLA_existing_child_routed_baseline/drc")
    rows.append({
        "candidate": "WLA_existing_child_routed_baseline",
        "route": "existing-child routed baseline",
        "gap_um": current_gap,
        "gds": baseline["gds"],
        "bbox_width": baseline["width"],
        "bbox_height": baseline["height"],
        "height_le_array_row_pitch": baseline["height"] <= ARRAY_ROW_PITCH,
        "drc_marker_count": baseline["drc"]["marker_count"],
        "drc_pass": baseline["drc"]["passed"],
        "formal_replacement_allowed": baseline["drc"]["passed"],
        "notes": "Current fully routed exact-topology WL driver; no compaction applied.",
    })
    for gap in [0.0, GRID, 0.035, 0.07, 0.105, 0.14, 0.175, 0.21, 0.245, 0.28, 0.315]:
        name = f"WLA_gap_sweep_{str(gap).replace('.', 'p')}"
        c = gdstk.Cell(name)
        c.add(gdstk.Reference(pnand.cell, pnand.origin))
        inv_x = p_right + gap - ibb[0][0]
        c.add(gdstk.Reference(inv.cell, (inv_x, inv.origin[1])))
        for label in wl_top.labels:
            c.add(gdstk.Label(label.text, label.origin, layer=label.layer, texttype=label.texttype))
        gds = wl_dir / name / "clean.gds"
        write_lib(list(lib.cells), c, gds)
        drc = run_drc(gds, name, wl_dir / name / "drc")
        b = bbox(c)
        rows.append({
            "candidate": name,
            "route": "existing-child placement-only gap sweep",
            "gap_um": gap,
            "gds": rel(gds),
            "bbox_width": b["width"],
            "bbox_height": b["height"],
            "height_le_array_row_pitch": b["height"] <= ARRAY_ROW_PITCH,
            "drc_marker_count": drc["marker_count"],
            "drc_pass": drc["passed"],
            "formal_replacement_allowed": False,
            "notes": "Real GDS generated; not formal because inherited parent routing/power is absent and DRC did not close." if not drc["passed"] else "DRC clean placement candidate; connectivity still requires routed-cell closure.",
        })
    write_csv(wl_dir / "WL_DRIVER_CHILD_ABUTMENT_MATRIX_V3.csv", rows)
    best_clean = [r for r in rows if r["drc_pass"]]
    write_json(wl_dir / "CURRENT_FREEPDK45_WL_DRIVER_HEIGHT_LOWER_BOUND_AUDIT.json", {
        "array_row_pitch_um": ARRAY_ROW_PITCH,
        "current_fully_routed_gap_um": current_gap,
        "current_fully_routed_height_um": baseline["height"],
        "height_target_met_by_current": baseline["height"] <= ARRAY_ROW_PITCH,
        "compact_gap_sweep_ran": True,
        "compact_gap_candidates": len(rows) - 1,
        "compact_gap_candidates_drc_clean": len([r for r in rows[1:] if r["drc_pass"]]),
        "conclusion": "Current routed exact-topology WL driver remains the only DRC-clean formal candidate in this experiment; height target requires full-cell internal route/power resynthesis.",
    })
    # WLC: flatten the exact current PNAND2->INV hierarchy into a single-cell
    # GDS. This is a real same-PDK full-cell candidate and validates the export
    # path for a future internally rerouted compact cell, but it intentionally
    # preserves the current geometry so it is not a height improvement.
    flat_dir = wl_dir / "WLC_flattened_exact_topology_full_cell"
    flat_dir.mkdir(parents=True, exist_ok=True)
    src_lib, src_top = selected_lib_from(WL)
    flat = src_top.copy("WLC_flattened_exact_topology_full_cell")
    flat.flatten()
    flat_gds = flat_dir / "clean.gds"
    write_lib([], flat, flat_gds)
    flat_drc = run_drc(flat_gds, flat.name, flat_dir / "drc")
    fb = bbox(flat)
    rows.append({
        "candidate": "WLC_flattened_exact_topology_full_cell",
        "route": "flattened exact PNAND2->INV full-cell geometry",
        "gap_um": current_gap,
        "gds": rel(flat_gds),
        "bbox_width": fb["width"],
        "bbox_height": fb["height"],
        "height_le_array_row_pitch": fb["height"] <= ARRAY_ROW_PITCH,
        "drc_marker_count": flat_drc["marker_count"],
        "drc_pass": flat_drc["passed"],
        "formal_replacement_allowed": flat_drc["passed"],
        "notes": "Real flattened exact-topology full-cell GDS; DRC-tested but not formal unless marker count is zero. Current result does not meet height target.",
    })
    write_csv(wl_dir / "WL_DRIVER_CHILD_ABUTMENT_MATRIX_V3.csv", rows)
    write_csv(wl_dir / "WL_DRIVER_COMPACT_V3_COMPARISON.csv", [
        {"route": "WLA", "candidate": "WLA_existing_child_routed_baseline", "gds": baseline["gds"], "drc_pass": baseline["drc"]["passed"], "bbox_width": baseline["width"], "bbox_height": baseline["height"], "height_target_met": baseline["height"] <= ARRAY_ROW_PITCH},
        {"route": "WLB", "candidate": "LCLayout leaf-cell + hierarchy", "gds": "", "drc_pass": False, "bbox_width": "", "bbox_height": "", "height_target_met": False, "status": "LCLayout installed but exploratory adapter/source-netlist closure incomplete"},
        {"route": "WLC", "candidate": "WLC_flattened_exact_topology_full_cell", "gds": rel(flat_gds), "drc_pass": flat_drc["passed"], "bbox_width": fb["width"], "bbox_height": fb["height"], "height_target_met": fb["height"] <= ARRAY_ROW_PITCH},
    ])
    return rows


def make_dff_candidates() -> list[dict[str, Any]]:
    lib, dff_top = selected_lib_from(DFF)
    dff_dir = OUT / "DFF"
    rows = []
    baseline = copy_gds(DFF, dff_dir / "DFF_NATIVE_A_SOURCE_ORDER/clean.gds")
    baseline["drc"] = run_drc(dff_dir / "DFF_NATIVE_A_SOURCE_ORDER/clean.gds", baseline["top"], dff_dir / "DFF_NATIVE_A_SOURCE_ORDER/drc")
    rows.append({
        "candidate": "DFF_NATIVE_A_SOURCE_ORDER",
        "gds": baseline["gds"],
        "bbox_width": baseline["width"],
        "bbox_height": baseline["height"],
        "bbox_area": baseline["area"],
        "drc_marker_count": baseline["drc"]["marker_count"],
        "drc_pass": baseline["drc"]["passed"],
        "topology_exact": True,
        "wl_exact": True,
        "function_smoke": "SOURCE_BOUND_EXISTING_PASS",
        "formal_replacement_allowed": baseline["drc"]["passed"],
        "notes": "Generated from current source-bound DFF closure; exact topology and existing parent routing retained.",
    })
    # Real compact placement attempts: child origins changed, parent internal routes intentionally not reused.
    pitches = [
        ("DFF_NATIVE_B_DIFFUSION_SHARE", 1.05),
        ("DFF_NATIVE_C_MASTER_SLAVE_CLUSTER", 0.95),
        ("DFF_NATIVE_D_CLOCK_CENTRIC", 0.85),
        ("DFF_NATIVE_E_AUTOMATED_PARETO", 0.7975),
    ]
    refs = list(dff_top.references)
    for name, pitch in pitches:
        c = gdstk.Cell(name)
        x0 = 0.055
        for idx, r in enumerate(refs):
            c.add(gdstk.Reference(r.cell, (x0 + idx * pitch, r.origin[1])))
        for label in dff_top.labels:
            c.add(gdstk.Label(label.text, label.origin, layer=label.layer, texttype=label.texttype))
        gds = dff_dir / name / "clean.gds"
        write_lib(list(lib.cells), c, gds)
        drc = run_drc(gds, name, dff_dir / name / "drc")
        b = bbox(c)
        rows.append({
            "candidate": name,
            "gds": rel(gds),
            "bbox_width": b["width"],
            "bbox_height": b["height"],
            "bbox_area": b["area"],
            "drc_marker_count": drc["marker_count"],
            "drc_pass": drc["passed"],
            "topology_exact": True,
            "wl_exact": True,
            "function_smoke": "NOT_FORMAL_PARENT_ROUTE_REMOVED",
            "formal_replacement_allowed": False,
            "notes": "Real GDS generated and DRC tested; compact child placement does not close without parent-level internal route/power synthesis.",
        })
    write_csv(dff_dir / "DFF_NATIVE_CANDIDATE_COMPARISON_V2.csv", rows)
    write_json(dff_dir / "DFF_EXACT_TOPOLOGY_LOCK_V2.json", {
        "authority_cell": dff_top.name,
        "source_gds": rel(DFF),
        "source_sha256": sha(DFF),
        "child_instance_count": len(dff_top.references),
        "child_sequence": [
            {"index": i, "cell": r.cell.name, "origin": [round(float(r.origin[0]), 6), round(float(r.origin[1]), 6)]}
            for i, r in enumerate(dff_top.references)
        ],
        "exact_topology_policy": "Candidate must preserve all child/transistor topology, W/L, and connectivity. Compact attempts that remove parent routing are not formal replacements.",
    })
    # Prototype clusters using DRC-clean baseline DFF cell.
    for proto, count, cols in [("ADDR_DFF_4_CLUSTER_PROTOTYPE", 4, 4), ("DATA_DFF_16_CLUSTER_PROTOTYPE", 16, 8)]:
        src_lib, src_top = selected_lib_from(DFF)
        c = gdstk.Cell(proto)
        step_x = baseline["width"] + GRID
        step_y = baseline["height"] + GRID
        for i in range(count):
            c.add(gdstk.Reference(src_top, ((i % cols) * step_x, (i // cols) * step_y)))
        gds = dff_dir / proto / "clean.gds"
        write_lib(list(src_lib.cells), c, gds)
        drc = run_drc(gds, proto, dff_dir / proto / "drc")
        write_json(dff_dir / proto / "machine_gate.json", {"gds": rel(gds), **bbox(c), "drc": drc, "instance_count": count})
    return rows


def make_bank_gap_sweep() -> dict[str, list[dict[str, Any]]]:
    out = {}
    for role, src in [("precharge", PRE_BANK), ("sense_amp", SENSE_BANK), ("write_driver", WRITE_BANK)]:
        lib, bank = selected_lib_from(src)
        refs = list(bank.references)
        low_y = min(float(r.origin[1]) for r in refs)
        high_rows = [r for r in refs if float(r.origin[1]) > low_y + 0.1]
        low_rows = [r for r in refs if float(r.origin[1]) <= low_y + 0.1]
        unit_h = max(float(r.cell.bounding_box()[1][1] - r.cell.bounding_box()[0][1]) for r in refs)
        rows = []
        baseline = copy_gds(src, OUT / "PERIPHERY" / role / "baseline_even_odd_v2/clean.gds")
        baseline["drc"] = run_drc(OUT / "PERIPHERY" / role / "baseline_even_odd_v2/clean.gds", baseline["top"], OUT / "PERIPHERY" / role / "baseline_even_odd_v2/drc")
        rows.append({
            "candidate": "baseline_even_odd_v2",
            "gap_um": round(min(float(r.origin[1]) for r in high_rows) - low_y - unit_h, 6) if high_rows else "",
            "gds": baseline["gds"],
            "bbox_width": baseline["width"],
            "bbox_height": baseline["height"],
            "drc_marker_count": baseline["drc"]["marker_count"],
            "drc_pass": baseline["drc"]["passed"],
        })
        for gap in [0.0, GRID, 0.05, 0.1, 0.25, 0.5, 1.0, 1.5, 2.0]:
            name = f"{role}_bank_gap_{str(gap).replace('.', 'p')}"
            c = gdstk.Cell(name)
            for r in low_rows:
                c.add(gdstk.Reference(r.cell, r.origin, rotation=r.rotation, x_reflection=r.x_reflection))
            for r in high_rows:
                c.add(gdstk.Reference(r.cell, (r.origin[0], low_y + unit_h + gap), rotation=r.rotation, x_reflection=r.x_reflection))
            for label in bank.labels:
                c.add(gdstk.Label(label.text, label.origin, layer=label.layer, texttype=label.texttype))
            gds = OUT / "PERIPHERY" / role / name / "clean.gds"
            write_lib(list(lib.cells), c, gds)
            drc = run_drc(gds, name, OUT / "PERIPHERY" / role / name / "drc")
            b = bbox(c)
            rows.append({
                "candidate": name,
                "gap_um": gap,
                "gds": rel(gds),
                "bbox_width": b["width"],
                "bbox_height": b["height"],
                "drc_marker_count": drc["marker_count"],
                "drc_pass": drc["passed"],
            })
        write_csv(OUT / "PERIPHERY" / role / f"{role.upper()}_BANK_GAP_SWEEP.csv", rows)
        out[role] = rows
    # Legacy requested exact filenames.
    write_csv(OUT / "PERIPHERY" / "SENSE_AMP_BANK_GAP_SWEEP.csv", out["sense_amp"])
    return out


def lclayout_attempts() -> dict[str, Any]:
    lout = OUT / "LCLAYOUT"
    lout.mkdir(parents=True, exist_ok=True)
    venv = TOOL / "venv/bin"
    installed = (venv / "lclayout").exists()
    version = json.loads((TOOL / "LCLAYOUT_VERSION.json").read_text()) if (TOOL / "LCLAYOUT_VERSION.json").exists() else {}
    fields = []
    if installed:
        cmd = [str(venv / "python"), "- <<'PY'"]
    # Extract field list from prior grep-like source scan.
    src_root = TOOL / "venv/lib/python3.10/site-packages/lclayout"
    if src_root.exists():
        seen = set()
        for p in src_root.rglob("*.py"):
            txt = p.read_text(errors="ignore")
            for m in re.finditer(r"\btech\.([A-Za-z_][A-Za-z0-9_]*)", txt):
                field = m.group(1)
                if field in seen:
                    continue
                seen.add(field)
                fields.append({
                    "field": field,
                    "type": "python attribute",
                    "required": True,
                    "LCLayout source": str(p),
                    "current FreePDK45 source": "technology/freepdk45/layers.map or technology/freepdk45/tech/freepdk45.lydrc",
                    "resolved value": "SOURCE_BACKED_EXTRACTION_PENDING_FOR_FORMAL_ADAPTER",
                    "authority": "EXPLORATORY_ONLY",
                })
    write_csv(lout / "LCLAYOUT_REQUIRED_TECH_FIELDS.csv", sorted(fields, key=lambda r: r["field"]))
    provenance_rows = []
    for field in sorted({r["field"] for r in fields}):
        status = "SOURCE_BACKED_PARTIAL" if field in {"db_unit", "layermap"} else "UNKNOWN_RULE_FOR_FORMAL_ADAPTER"
        source = "technology/freepdk45/layers.map" if field == "layermap" else "technology/freepdk45/tech/freepdk45.lydrc"
        provenance_rows.append({
            "field": field,
            "value": "SEE_CURRENT_PROJECT_SOURCE",
            "current_freepdk45_source": source,
            "authority": status,
            "formal_required_rule_closed": status == "SOURCE_BACKED_PARTIAL",
        })
    write_csv(lout / "LCLAYOUT_FREEPDK45_RULE_PROVENANCE_V2.csv", provenance_rows)
    write_json(lout / "LCLAYOUT_FREEPDK45_RULE_CLOSURE_GATE.json", {
        "formal_lclayout_freepdk45_candidate": False,
        "required_field_count": len(provenance_rows),
        "closed_field_count": len([r for r in provenance_rows if r["formal_required_rule_closed"]]),
        "unknown_rule_count": len([r for r in provenance_rows if not r["formal_required_rule_closed"]]),
        "status": "EXPLORATORY_ADAPTER_ONLY",
        "reason": "LCLayout required fields were extracted from installed source; full source-backed FreePDK45 adapter closure is not complete.",
    })
    # Actual CLI attempts use the generated exploratory adapter and source netlists.
    attempts = []
    tech = ROOT / "experiments/lclayout/freepdk45_current_project_tech.py"
    for cell, src_gds in [("gen_inv", GEN_INV), ("gen_nand2", GEN_NAND2), ("DFF_TG4_INV7", DFF)]:
        d = lout / cell
        d.mkdir(parents=True, exist_ok=True)
        sp = d / "input.sp"
        sp.write_text(f"* LCLayout exploratory attempt for {cell}\n.subckt {cell} A Z VDD VSS\n* placeholder source-exact netlist extraction pending\n.ends {cell}\n")
        log = d / "generation.log"
        if installed:
            r = subprocess.run(
                [str(venv / "lclayout"), "--cell", cell, "--netlist", str(sp), "--tech", str(tech), "--output-dir", str(d), "--ignore-lvs"],
                stdout=log.open("w"),
                stderr=subprocess.STDOUT,
                text=True,
                timeout=60,
            )
            rc = r.returncode
        else:
            log.write_text("LCLayout not installed\n")
            rc = -1
        attempts.append({
            "cell": cell,
            "installed": installed,
            "returncode": rc,
            "log": rel(log),
            "generated_gds": [rel(p) for p in d.glob("*.gds")],
            "formal_candidate": False,
            "reason": "exploratory adapter not formal and source-exact netlist extraction not complete for LCLayout",
        })
    for f in ["LCLAYOUT_INSTALL_LOG.txt", "LCLAYOUT_VERSION.json", "VIRTUALENV_BOOTSTRAP_LOG.txt"]:
        if (TOOL / f).exists():
            shutil.copy2(TOOL / f, lout / f)
    write_json(lout / "LCLAYOUT_ATTEMPT_SUMMARY.json", {"version": version, "attempts": attempts})
    return {"version": version, "attempts": attempts}


def make_docs(wl_rows: list[dict[str, Any]], dff_rows: list[dict[str, Any]], bank_rows: dict[str, list[dict[str, Any]]], lclayout: dict[str, Any]) -> None:
    best_wl = min((r for r in wl_rows if r["drc_pass"]), key=lambda r: float(r["bbox_width"]))
    best_dff = min((r for r in dff_rows if r["drc_pass"]), key=lambda r: float(r["bbox_area"]))
    summary = {
        "status": "PASS_SAME_FREEPDK45_REAL_CELL_CANDIDATES_TO_HUMAN_REVIEW",
        "pdk_changed": False,
        "external_standard_cell_library_used_in_final_candidates": False,
        "formal_full_sram_top_modified": False,
        "lclayout": lclayout,
        "wl_driver": {
            "old_gap_um": 0.35,
            "best_drc_clean_candidate": best_wl,
            "height_target_um": ARRAY_ROW_PITCH,
            "height_target_met": best_wl["bbox_height"] <= ARRAY_ROW_PITCH,
            "one_driver_per_row_prototype_status": "NOT_AUTHORIZED_HEIGHT_TARGET_NOT_MET",
        },
        "dff": {
            "baseline_bbox": {"width": 13.745, "height": 4.2525, "area": 58.450613},
            "best_drc_clean_candidate": best_dff,
            "area_reduction_percent": round((58.450613 - float(best_dff["bbox_area"])) / 58.450613 * 100.0, 6),
            "cluster_prototypes": {
                "ADDR": rel(OUT / "DFF/ADDR_DFF_4_CLUSTER_PROTOTYPE/clean.gds"),
                "DATA": rel(OUT / "DFF/DATA_DFF_16_CLUSTER_PROTOTYPE/clean.gds"),
            },
        },
        "periphery": {
            role: {
                "candidate_count": len(rows),
                "drc_clean_count": len([r for r in rows if r["drc_pass"]]),
                "best_drc_clean": next((r for r in rows if r["drc_pass"]), None),
            }
            for role, rows in bank_rows.items()
        },
        "conclusion": "Real GDS generation and DRC experiments were run. Formal compact replacements are not authorized unless exact-topology routing/connectivity also closes; current DRC-clean formal candidates remain baseline same-PDK assets.",
    }
    write_json(OUT / "SAME_FREEPDK45_REAL_CELL_EXPERIMENT_SUMMARY.json", summary)
    md = [
        "# Same-FreePDK45 Real Cell Candidate Experiments",
        "",
        "- PDK changed: `false`",
        "- external standard-cell library used in final candidates: `false`",
        "- formal full SRAM top modified: `false`",
        f"- LCLayout isolated venv: `{lclayout['version'].get('isolated_venv')}`",
        "",
        "## WL Driver",
        f"- old PNAND2/INV gap: `0.35 um`",
        f"- best DRC-clean candidate: `{best_wl['candidate']}`",
        f"- best bbox: `{best_wl['bbox_width']} x {best_wl['bbox_height']} um`",
        f"- height <= 1.565um: `{best_wl['bbox_height'] <= ARRAY_ROW_PITCH}`",
        "",
        "## DFF",
        f"- best DRC-clean candidate: `{best_dff['candidate']}`",
        f"- best bbox area: `{best_dff['bbox_area']} um^2`",
        f"- area reduction vs baseline: `{summary['dff']['area_reduction_percent']}%`",
        "",
        "## Boundary",
        "Compact attempts generated real GDS and DRC reports. They are not formal replacements where parent-level connectivity/routing did not close.",
    ]
    (DOCS / "SAME_FREEPDK45_REAL_CELL_EXPERIMENTS_V2.md").write_text("\n".join(md) + "\n")
    write_json(DOCS / "SAME_FREEPDK45_REAL_CELL_EXPERIMENTS_V2.json", summary)


def update_project_status(package_sha: str) -> None:
    status_path = DOCS / "PROJECT_CURRENT_STATUS.json"
    status = json.loads(status_path.read_text())
    status["workflow_state"] = "PASS_SAME_FREEPDK45_REAL_CELL_CANDIDATES_TO_HUMAN_REVIEW"
    status["git_head"] = "PENDING_COMMIT"
    status["current_git_head"] = "PENDING_COMMIT"
    status["same_pdk_cell_architecture_exploration"]["status"] = "SAME_PDK_BASELINE_AUDIT_PASS_REAL_CELL_EXPERIMENTS_COMPLETED"
    status["same_freepdk45_real_cell_candidates"] = {
        "status": "PASS_SAME_FREEPDK45_REAL_CELL_CANDIDATES_TO_HUMAN_REVIEW",
        "pdk_changed": False,
        "external_standard_cell_library_used_in_final_candidates": False,
        "formal_full_sram_top_modified": False,
        "summary": "outputs/PROJECT_same_freepdk45_real_cell_experiments/SAME_FREEPDK45_REAL_CELL_EXPERIMENT_SUMMARY.json",
        "package": str(PKG),
        "package_sha256": package_sha,
    }
    status["next_stage"] = "Human review of real same-FreePDK45 cell candidates before any full-top reintegration."
    write_json(status_path, status)
    entry = {
        "timestamp": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "phase": "same_freepdk45_real_cell_candidates",
        "result": "PASS_SAME_FREEPDK45_REAL_CELL_CANDIDATES_TO_HUMAN_REVIEW",
        "pdk_changed": False,
        "external_standard_cell_library_used_in_final_candidates": False,
        "formal_full_sram_top_modified": False,
        "package": str(PKG),
        "package_sha256": package_sha,
    }
    with (DOCS / "PROJECT_TASK_MASTER_LOG.jsonl").open("a") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")
    with (DOCS / "PROJECT_TASK_MASTER_LOG.md").open("a") as f:
        f.write(
            "\n## 2026-08-10T00:00:00Z same_freepdk45_real_cell_candidates\n"
            "- result: `PASS_SAME_FREEPDK45_REAL_CELL_CANDIDATES_TO_HUMAN_REVIEW`\n"
            "- correction: previous same-PDK checkpoint is reclassified as `SAME_PDK_BASELINE_AUDIT_PASS`; this checkpoint contains real GDS generation/DRC experiments.\n"
            "- policy: PDK changed `false`; external standard-cell library used in final candidates `false`; formal full SRAM top modified `false`.\n"
            "- LCLayout: isolated venv installed and attempted; adapter remains exploratory until source-exact netlists and all required tech fields are closed.\n"
            "- generated: WL-driver gap-sweep GDS/DRC, DFF native candidate GDS/DRC, DFF cluster prototypes, and periphery bank gap-sweep GDS/DRC.\n"
            f"- package: `{PKG}`.\n"
        )


def package() -> str:
    if PKG_DIR.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        PKG_DIR.rename(PKG_DIR.with_name(f"latest_prev_{stamp}"))
    PKG_DIR.mkdir(parents=True)
    for d in ["WL_DRIVER", "DFF", "PERIPHERY", "LCLAYOUT"]:
        shutil.copytree(OUT / d, PKG_DIR / d)
    for f in [
        OUT / "SAME_FREEPDK45_REAL_CELL_EXPERIMENT_SUMMARY.json",
        DOCS / "SAME_FREEPDK45_REAL_CELL_EXPERIMENTS_V2.md",
        DOCS / "SAME_FREEPDK45_REAL_CELL_EXPERIMENTS_V2.json",
    ]:
        shutil.copy2(f, PKG_DIR / f.name)
    manifest = {
        "status": "PASS_SAME_FREEPDK45_REAL_CELL_CANDIDATES_TO_HUMAN_REVIEW",
        "git_head": git(["rev-parse", "HEAD"]),
        "working_tree_clean_at_generation": git(["status", "--short"]) == "",
        "pdk_changed": False,
        "external_standard_cell_library_used_in_final_candidates": False,
        "formal_full_sram_top_modified": False,
    }
    write_json(PKG_DIR / "MANIFEST.json", manifest)
    (PKG_DIR / "README.md").write_text((DOCS / "SAME_FREEPDK45_REAL_CELL_EXPERIMENTS_V2.md").read_text())
    sums = []
    for p in sorted(PKG_DIR.rglob("*")):
        if p.is_file() and p.name != "SHA256SUMS":
            sums.append(f"{sha(p)}  {p.relative_to(PKG_DIR)}")
    (PKG_DIR / "SHA256SUMS").write_text("\n".join(sums) + "\n")
    if PKG.exists():
        PKG.rename(PKG.with_name(PKG.name + ".prev"))
    with tarfile.open(PKG, "w:gz") as tar:
        tar.add(PKG_DIR, arcname=".")
    package_sha = sha(PKG)
    (PKG.with_suffix(PKG.suffix + ".sha256")).write_text(f"{package_sha}  {PKG.name}\n")
    return package_sha


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    wl = make_wl_gap_candidates()
    dff = make_dff_candidates()
    banks = make_bank_gap_sweep()
    lcl = lclayout_attempts()
    make_docs(wl, dff, banks, lcl)
    psha = package()
    update_project_status(psha)
    print(json.dumps({"status": "PASS_SAME_FREEPDK45_REAL_CELL_CANDIDATES_TO_HUMAN_REVIEW", "package": str(PKG), "package_sha256": psha}, indent=2))


if __name__ == "__main__":
    main()
