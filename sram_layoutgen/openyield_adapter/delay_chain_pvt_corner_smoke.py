"""Delay-chain PVT corner smoke summary helpers."""

from __future__ import annotations

import csv
import json
import re
import subprocess
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.delay_chain_measurement_refinement import (
    parse_ngspice_print_log,
    postprocess_delays,
)

PREVIOUS_MEASUREMENT_REFINEMENT_COMMIT = "4eeeee106db316f4d09322c02c4152c28acf5d77"
CORNER_ORDER = ["nom", "ff", "ss"]
CORNER_CONFIG = {
    "nom": {
        "include": "local_model_include_nom_server.inc",
        "nmos": "/data1/qujh/OpenRAM/technology/freepdk45/models/tran_models/models_nom/NMOS_VTG.inc",
        "pmos": "/data1/qujh/OpenRAM/technology/freepdk45/models/tran_models/models_nom/PMOS_VTG.inc",
    },
    "ff": {
        "include": "local_model_include_ff_server.inc",
        "nmos": "/data1/qujh/OpenRAM/technology/freepdk45/models/tran_models/models_ff/NMOS_VTG.inc",
        "pmos": "/data1/qujh/OpenRAM/technology/freepdk45/models/tran_models/models_ff/PMOS_VTG.inc",
    },
    "ss": {
        "include": "local_model_include_ss_server.inc",
        "nmos": "/data1/qujh/OpenRAM/technology/freepdk45/models/tran_models/models_ss/NMOS_VTG.inc",
        "pmos": "/data1/qujh/OpenRAM/technology/freepdk45/models/tran_models/models_ss/PMOS_VTG.inc",
    },
}


def build_delay_chain_pvt_corner_smoke_report(
    repo_root: str | Path,
    candidate_dir: str | Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    candidate = _resolve_path(root, candidate_dir)
    pvt_dir = candidate / "pvt_smoke"
    summary_csv = pvt_dir / "delay_chain_pvt_smoke_summary.csv"

    head = _run_text(["git", "rev-parse", "HEAD"], cwd=root)
    ngspice_path = _which("ngspice")
    ngspice_version = _run_text(["ngspice", "-v"], cwd=root) if ngspice_path else None

    corner_models: dict[str, dict[str, Any]] = {}
    rows: list[dict[str, Any]] = []
    for corner in CORNER_ORDER:
        cfg = CORNER_CONFIG[corner]
        include_path = candidate / cfg["include"]
        deck_path = pvt_dir / f"delay_chain_pvt_{corner}_ngspice.sp"
        log_path = pvt_dir / f"delay_chain_pvt_{corner}_ngspice.log"
        found = include_path.exists() and Path(cfg["nmos"]).exists() and Path(cfg["pmos"]).exists()
        corner_models[corner] = {
            "include_path": str(include_path),
            "nmos_model": cfg["nmos"],
            "pmos_model": cfg["pmos"],
            "found": found,
        }
        row = summarize_corner(corner, deck_path, log_path)
        rows.append(row)

    write_summary_csv(summary_csv, rows)

    available_rows = [row for row in rows if row["max_delay_s"] is not None]
    worst = max(available_rows, key=lambda row: row["max_delay_s"]) if available_rows else None

    audit_summary = {
        "delay_chain_pvt_corner_smoke_available": True,
        "repo_head": head,
        "ngspice_found": ngspice_path is not None,
        "corner_models_found": all(corner_models[c]["found"] for c in CORNER_ORDER),
        "nom_model_found": corner_models["nom"]["found"],
        "ff_model_found": corner_models["ff"]["found"],
        "ss_model_found": corner_models["ss"]["found"],
        "pvt_matrix_defined": True,
        "corner_decks_generated": all((pvt_dir / f"delay_chain_pvt_{c}_ngspice.sp").exists() for c in CORNER_ORDER),
        "corner_runs_attempted": all((pvt_dir / f"delay_chain_pvt_{c}_ngspice.log").exists() for c in CORNER_ORDER),
        "nom_run_pass": _find_row(rows, "nom")["ngspice_run_pass"],
        "ff_run_pass": _find_row(rows, "ff")["ngspice_run_pass"],
        "ss_run_pass": _find_row(rows, "ss")["ngspice_run_pass"],
        "nom_delay_available": _find_row(rows, "nom")["max_delay_s"] is not None,
        "ff_delay_available": _find_row(rows, "ff")["max_delay_s"] is not None,
        "ss_delay_available": _find_row(rows, "ss")["max_delay_s"] is not None,
        "pvt_summary_available": summary_csv.exists(),
        "worst_smoke_delay_available": worst is not None,
        "worst_smoke_delay_corner": worst["corner"] if worst else None,
        "can_enter_timing_metadata_update": all(row["ngspice_run_pass"] and row["max_delay_s"] is not None for row in rows),
        "can_claim_delay_proof_now": False,
        "can_claim_timing_closure_now": False,
        "can_enter_physical_timing_closure_now": False,
        "can_enter_physical_routing_now": False,
        "can_enter_physical_placement_now": False,
        "can_generate_time_control_gds_now": False,
        "can_modify_standalone_now": False,
        "evidence_timeline_updated": True,
        "milestone_summary_updated": True,
    }

    report = {
        "scope": "delay_chain_pvt_corner_smoke",
        "repo_root": str(root),
        "repo_head": head,
        "previous_measurement_refinement_commit": PREVIOUS_MEASUREMENT_REFINEMENT_COMMIT,
        "ngspice": {"path": ngspice_path, "version": ngspice_version},
        "corner_models": corner_models,
        "pvt_matrix": {
            "corners": CORNER_ORDER,
            "vdd_volts": 1.0,
            "temp_c": 25,
            "optional_not_run": {
                "low_vdd": 0.9,
                "high_vdd": 1.1,
                "low_temp_c": 0,
                "high_temp_c": 85,
            },
        },
        "rows": rows,
        "summary_csv_path": str(summary_csv),
        "worst_smoke_delay": worst,
        "boundary_assertions": {
            "pvt_smoke_is_not_delay_proof": True,
            "timing_closure_not_claimed": True,
            "physical_timing_closure_not_claimed": True,
            "physical_routing_not_claimed": True,
            "physical_placement_not_claimed": True,
            "time_control_gds_not_claimed": True,
            "standalone_modified": False,
            "routing_modified": False,
            "gds_writer_modified": False,
        },
        "audit_summary": audit_summary,
    }
    return report


def summarize_corner(corner: str, deck_path: Path, log_path: Path) -> dict[str, Any]:
    log_text = log_path.read_text(encoding="utf-8", errors="replace") if log_path.exists() else ""
    ngspice_run_pass = _classify_run_pass(log_text)
    measure_results = _extract_measure_results(log_text)
    measure_pass = all(v["success"] for v in measure_results.values()) if measure_results else False
    parsed = parse_ngspice_print_log(log_text)
    post = postprocess_delays(parsed, 0.5)
    rise_to_fall = measure_results.get("smoke_delay_rise_to_fall", {}).get("seconds")
    fall_to_rise = measure_results.get("smoke_delay_fall_to_rise", {}).get("seconds")
    if rise_to_fall is None:
        rise_to_fall = post["delays"].get("rise_to_fall_delay")
    if fall_to_rise is None:
        fall_to_rise = post["delays"].get("fall_to_rise_delay")
    max_delay = max([v for v in [rise_to_fall, fall_to_rise] if v is not None], default=None)
    return {
        "corner": corner,
        "VDD": 1.0,
        "TEMP": 25,
        "deck_path": str(deck_path),
        "log_path": str(log_path),
        "ngspice_run_pass": ngspice_run_pass,
        "measure_pass": measure_pass,
        "postprocess_pass": post["pass"],
        "rise_to_fall_delay_s": rise_to_fall,
        "fall_to_rise_delay_s": fall_to_rise,
        "max_delay_s": max_delay,
        "warnings": _extract_warnings(log_text),
        "failure_classification": None if ngspice_run_pass else _classify_failure(log_text),
        "notes": _notes(ngspice_run_pass, measure_pass, post["pass"]),
    }


def write_summary_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "corner",
        "VDD",
        "TEMP",
        "ngspice_run_pass",
        "measure_pass",
        "postprocess_pass",
        "rise_to_fall_delay_s",
        "fall_to_rise_delay_s",
        "max_delay_s",
        "warnings",
        "failure_classification",
    ]
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "corner": row["corner"],
                "VDD": row["VDD"],
                "TEMP": row["TEMP"],
                "ngspice_run_pass": row["ngspice_run_pass"],
                "measure_pass": row["measure_pass"],
                "postprocess_pass": row["postprocess_pass"],
                "rise_to_fall_delay_s": row["rise_to_fall_delay_s"],
                "fall_to_rise_delay_s": row["fall_to_rise_delay_s"],
                "max_delay_s": row["max_delay_s"],
                "warnings": " | ".join(row["warnings"]),
                "failure_classification": json.dumps(row["failure_classification"], ensure_ascii=False) if row["failure_classification"] else "",
            })


def format_delay_chain_pvt_corner_smoke_markdown(report: dict[str, Any]) -> str:
    rows = report["rows"]
    table = _md_table(
        ["corner", "VDD", "TEMP", "run pass", "measure pass", "rise-to-fall", "fall-to-rise", "max delay", "notes"],
        [[
            row["corner"],
            row["VDD"],
            row["TEMP"],
            row["ngspice_run_pass"],
            row["measure_pass"],
            row["rise_to_fall_delay_s"],
            row["fall_to_rise_delay_s"],
            row["max_delay_s"],
            row["notes"],
        ] for row in rows],
    )
    lines = [
        "# OpenYield Delay Chain PVT Corner Smoke Report",
        "",
        f"- Scope: `{report['scope']}`",
        f"- Repo root: `{report['repo_root']}`",
        f"- Repo HEAD: `{report['repo_head']}`",
        f"- Previous measurement refinement commit: `{report['previous_measurement_refinement_commit']}`",
        f"- Summary CSV: `{report['summary_csv_path']}`",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Corner Models",
        "",
        "```json",
        json.dumps(report["corner_models"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## PVT Matrix",
        "",
        "```json",
        json.dumps(report["pvt_matrix"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Corner Table",
        "",
        table,
        "",
        "## Worst Smoke Delay",
        "",
        "```json",
        json.dumps(report["worst_smoke_delay"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Boundary Assertions",
        "",
        "```json",
        json.dumps(report["boundary_assertions"], ensure_ascii=False, indent=2),
        "```",
    ]
    return "\n".join(lines)


def _classify_run_pass(log_text: str) -> bool:
    low = log_text.lower()
    if not log_text or "total analysis time" not in low:
        return False
    for token in ["fatal error in ngspice", "simulation interrupted due to error", "undefined", "singular", "timestep too small"]:
        if token in low:
            return False
    return True


def _extract_measure_results(log_text: str) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for name in ["smoke_delay_rise_to_fall", "smoke_delay_fall_to_rise"]:
        m = re.search(rf"\b{name}\s*=\s*([\deE+\-.]+)", log_text)
        if m:
            results[name] = {"success": True, "seconds": float(m.group(1)), "raw": m.group(1)}
        else:
            results[name] = {"success": False, "seconds": None, "raw": None}
    return results


def _extract_warnings(log_text: str) -> list[str]:
    return [line.strip() for line in log_text.splitlines() if "warning" in line.lower()][:20]


def _classify_failure(log_text: str) -> dict[str, str]:
    low = log_text.lower()
    if any(t in low for t in ["gmin", "source stepping", "timestep too small", "singular"]):
        return {"code": "A", "label": "convergence issue"}
    if any(t in low for t in ["pulse", "vin", "no dc value"]):
        return {"code": "B", "label": "deck stimulus issue"}
    if any(t in low for t in ["unknown node", "no such vector"]):
        return {"code": "C", "label": "node naming issue"}
    if any(t in low for t in ["unknown parameter", "unknown model", "unable to find definition of model"]):
        return {"code": "D", "label": "model/device issue"}
    if any(t in low for t in ["measure", "bad syntax"]):
        return {"code": "E", "label": "measure syntax issue"}
    return {"code": "F", "label": "other"}


def _notes(run_pass: bool, measure_pass: bool, postprocess_pass: bool) -> str:
    if run_pass and measure_pass:
        return "ngspice measure passed"
    if run_pass and postprocess_pass:
        return "ngspice run passed; Python fallback available"
    if run_pass:
        return "ngspice run passed without usable delay"
    return "run failed"


def _find_row(rows: list[dict[str, Any]], corner: str) -> dict[str, Any]:
    for row in rows:
        if row["corner"] == corner:
            return row
    raise KeyError(corner)


def _md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join("" if v is None else str(v) for v in row) + " |")
    return "\n".join(lines)


def _resolve_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (root / path).resolve()


def _run_text(cmd: list[str], cwd: Path) -> str | None:
    try:
        result = subprocess.run(cmd, cwd=cwd, check=True, capture_output=True, text=True)
    except (OSError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip() or result.stderr.strip() or None


def _which(tool: str) -> str | None:
    return _run_text(["which", tool], cwd=Path.cwd())
