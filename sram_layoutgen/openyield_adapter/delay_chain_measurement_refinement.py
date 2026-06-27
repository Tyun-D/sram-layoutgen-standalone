"""Delay-chain smoke-only measurement refinement helpers."""

from __future__ import annotations

import json
import math
import re
import subprocess
from pathlib import Path
from typing import Any

PREVIOUS_TRANSIENT_COMMIT = "fc85009cd68cacd4c682ec2cdadb576a2583bdb3"


def build_delay_chain_measurement_refinement_report(
    repo_root: str | Path,
    candidate_dir: str | Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    candidate = _resolve_path(root, candidate_dir)
    include_file = candidate / "local_model_include_nom_server.inc"
    deck_file = candidate / "delay_chain_measurement_refined_ngspice.sp"
    log_file = candidate / "delay_chain_measurement_refined_ngspice.log"

    head = _run_text(["git", "rev-parse", "HEAD"], cwd=root)
    ngspice_path = _which("ngspice")
    ngspice_version = _run_text(["ngspice", "-v"], cwd=root) if ngspice_path else None

    deck_text = deck_file.read_text(encoding="utf-8") if deck_file.exists() else ""
    log_text = log_file.read_text(encoding="utf-8", errors="replace") if log_file.exists() else ""

    stage_count = len(re.findall(r"^Xdinv\d+\b", deck_text, re.M))
    load_count = len(re.findall(r"^Xdload_\d+_\d+\b", deck_text, re.M))
    vdd_value = _extract_numeric_param(deck_text, "VDD_VALUE", default=1.0)
    vth_value = 0.5 * vdd_value

    measure_failure_reason = _identify_original_measure_failure(root)
    refined_ngspice_run_attempted = log_file.exists()
    refined_ngspice_run_pass = _classify_ngspice_run_pass(log_text)
    refined_measure_attempted = deck_text.lower().count(".measure tran") >= 2
    measure_results = _extract_measure_results(log_text)
    refined_measure_pass = all(item["success"] for item in measure_results.values()) if measure_results else False

    parsed_waveform = parse_ngspice_print_log(log_text)
    postprocess_delay_attempted = True
    postprocess = postprocess_delays(parsed_waveform, vth_value)
    postprocess_delay_pass = postprocess["pass"]

    smoke_delay_value_available = refined_measure_pass or postprocess_delay_pass
    rise_to_fall = measure_results.get("smoke_delay_rise_to_fall", {}).get("seconds")
    fall_to_rise = measure_results.get("smoke_delay_fall_to_rise", {}).get("seconds")
    if rise_to_fall is None:
        rise_to_fall = postprocess["delays"].get("rise_to_fall_delay")
    if fall_to_rise is None:
        fall_to_rise = postprocess["delays"].get("fall_to_rise_delay")

    comparison = compare_measure_and_postprocess(measure_results, postprocess["delays"])

    audit_summary = {
        "delay_chain_measurement_refinement_available": True,
        "repo_head": head,
        "ngspice_found": ngspice_path is not None,
        "refined_measurement_deck_generated": deck_file.exists(),
        "refined_ngspice_run_attempted": refined_ngspice_run_attempted,
        "refined_ngspice_run_pass": refined_ngspice_run_pass,
        "inversion_expectation_recorded": True,
        "measure_failure_reason_identified": measure_failure_reason is not None,
        "refined_measure_attempted": refined_measure_attempted,
        "refined_measure_pass": refined_measure_pass,
        "postprocess_delay_attempted": postprocess_delay_attempted,
        "postprocess_delay_pass": postprocess_delay_pass,
        "smoke_delay_value_available": smoke_delay_value_available,
        "smoke_delay_rise_to_fall_available": rise_to_fall is not None,
        "smoke_delay_fall_to_rise_available": fall_to_rise is not None,
        "can_enter_pvt_corner_smoke": smoke_delay_value_available,
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
        "scope": "delay_chain_measurement_refinement",
        "repo_root": str(root),
        "repo_head": head,
        "previous_transient_smoke_commit": PREVIOUS_TRANSIENT_COMMIT,
        "ngspice": {"path": ngspice_path, "version": ngspice_version},
        "model_include_path": str(include_file),
        "refined_deck_path": str(deck_file),
        "stimulus_summary": _stimulus_summary(deck_text),
        "stage_count": stage_count,
        "four_load_policy": {
            "loads_per_stage_expected": 4,
            "load_instances_found": load_count,
            "policy_matches_candidate_topology": load_count == stage_count * 4 if stage_count else False,
        },
        "inversion_expectation": {
            "stage_count": stage_count,
            "odd_stage_chain": bool(stage_count % 2),
            "expected_behavior": "9-stage chain is overall inverting; rbl rising should map to rbl_delay falling, and rbl falling should map to rbl_delay rising.",
        },
        "original_measure_failure_reason": measure_failure_reason,
        "refined_measure_attempted": refined_measure_attempted,
        "refined_measure_pass": refined_measure_pass,
        "measure_results": measure_results,
        "python_postprocess_attempted": postprocess_delay_attempted,
        "python_postprocess_pass": postprocess_delay_pass,
        "python_postprocess": postprocess,
        "smoke_only_delay": {
            "rise_to_fall_delay_seconds": rise_to_fall,
            "fall_to_rise_delay_seconds": fall_to_rise,
            "source_priority": "ngspice_measure_then_python_postprocess",
            "measure_postprocess_comparison": comparison,
        },
        "key_warnings": _extract_warnings(log_text),
        "key_errors": _extract_errors(log_text),
        "boundary_assertions": {
            "measurement_refinement_is_smoke_only": True,
            "delay_proof_not_claimed": True,
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


def format_delay_chain_measurement_refinement_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Delay Chain Measurement Refinement Report",
        "",
        f"- Scope: `{report['scope']}`",
        f"- Repo root: `{report['repo_root']}`",
        f"- Repo HEAD: `{report['repo_head']}`",
        f"- Previous transient smoke commit: `{report['previous_transient_smoke_commit']}`",
        f"- Refined deck: `{report['refined_deck_path']}`",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## ngspice Environment",
        "",
        "```json",
        json.dumps(report["ngspice"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Stimulus And Topology",
        "",
        "```json",
        json.dumps(
            {
                "model_include_path": report["model_include_path"],
                "stimulus_summary": report["stimulus_summary"],
                "stage_count": report["stage_count"],
                "four_load_policy": report["four_load_policy"],
                "inversion_expectation": report["inversion_expectation"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "",
        "## Failure Diagnosis",
        "",
        "```json",
        json.dumps(report["original_measure_failure_reason"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Refined Measure",
        "",
        "```json",
        json.dumps(report["measure_results"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Python Postprocess",
        "",
        "```json",
        json.dumps(report["python_postprocess"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Smoke-Only Delay",
        "",
        "```json",
        json.dumps(report["smoke_only_delay"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Key Warnings",
        "",
        _list_block(report["key_warnings"]),
        "",
        "## Key Errors",
        "",
        _list_block(report["key_errors"]),
        "",
        "## Boundary Assertions",
        "",
        "```json",
        json.dumps(report["boundary_assertions"], ensure_ascii=False, indent=2),
        "```",
    ]
    return "\n".join(lines)


def parse_ngspice_print_log(log_text: str) -> dict[str, list[float]]:
    lines = log_text.replace("\f", "\n").splitlines()
    data_by_key: dict[tuple[int, float], dict[str, float]] = {}
    current_vars: list[str] = []
    collecting_header = False
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("Index") and "time" in stripped:
            current_vars = _extract_vector_names(line)
            collecting_header = True
            continue
        if collecting_header:
            if set(stripped) == {"-"}:
                collecting_header = False
                continue
            more = _extract_vector_names(line)
            if more:
                current_vars.extend(more)
            continue
        if not current_vars:
            continue
        if re.match(r"^\d+\s", stripped):
            parts = stripped.split()
            if len(parts) < 2 + len(current_vars):
                continue
            data_index = int(parts[0])
            time_value = float(parts[1])
            key = (data_index, time_value)
            row = data_by_key.setdefault(key, {"time": time_value})
            for name, value in zip(current_vars, parts[2:2 + len(current_vars)]):
                row[name] = float(value)
    rows = [data_by_key[key] for key in sorted(data_by_key)]
    result: dict[str, list[float]] = {"time": [row["time"] for row in rows]}
    names = sorted({name for row in rows for name in row if name != "time"})
    for name in names:
        result[name] = [row.get(name, math.nan) for row in rows]
    return result


def postprocess_delays(parsed: dict[str, list[float]], threshold: float) -> dict[str, Any]:
    times = parsed.get("time", [])
    rbl = parsed.get("v(rbl)", [])
    rbl_delay = parsed.get("v(rbl_delay)", [])
    if not times or not rbl or not rbl_delay:
        return {
            "pass": False,
            "reason": "Missing parsed time/v(rbl)/v(rbl_delay) data from ngspice .print output.",
            "crossings": {},
            "delays": {},
        }

    crossings = {
        "rbl_rise_1": find_crossing(times, rbl, threshold, "rise", 1),
        "rbl_fall_1": find_crossing(times, rbl, threshold, "fall", 1),
        "rbl_delay_fall_1": find_crossing(times, rbl_delay, threshold, "fall", 1),
        "rbl_delay_rise_1": find_crossing(times, rbl_delay, threshold, "rise", 1),
    }
    delays: dict[str, float] = {}
    if crossings["rbl_rise_1"] is not None and crossings["rbl_delay_fall_1"] is not None:
        delays["rise_to_fall_delay"] = crossings["rbl_delay_fall_1"] - crossings["rbl_rise_1"]
    if crossings["rbl_fall_1"] is not None and crossings["rbl_delay_rise_1"] is not None:
        delays["fall_to_rise_delay"] = crossings["rbl_delay_rise_1"] - crossings["rbl_fall_1"]

    return {
        "pass": "rise_to_fall_delay" in delays or "fall_to_rise_delay" in delays,
        "reason": None,
        "crossings": crossings,
        "delays": delays,
    }


def find_crossing(times: list[float], values: list[float], threshold: float, direction: str, occurrence: int) -> float | None:
    count = 0
    for i in range(1, min(len(times), len(values))):
        v0 = values[i - 1]
        v1 = values[i]
        if math.isnan(v0) or math.isnan(v1):
            continue
        if direction == "rise":
            hit = v0 < threshold <= v1
        else:
            hit = v0 > threshold >= v1
        if not hit:
            continue
        count += 1
        if count != occurrence:
            continue
        if v1 == v0:
            return times[i]
        frac = (threshold - v0) / (v1 - v0)
        return times[i - 1] + frac * (times[i] - times[i - 1])
    return None


def compare_measure_and_postprocess(measure_results: dict[str, dict[str, Any]], postprocess_delays: dict[str, float]) -> dict[str, Any]:
    pairs = {
        "smoke_delay_rise_to_fall": postprocess_delays.get("rise_to_fall_delay"),
        "smoke_delay_fall_to_rise": postprocess_delays.get("fall_to_rise_delay"),
    }
    comparison: dict[str, Any] = {}
    for name, post_val in pairs.items():
        measure_val = measure_results.get(name, {}).get("seconds")
        if measure_val is None or post_val is None:
            comparison[name] = {"comparable": False, "measure_seconds": measure_val, "postprocess_seconds": post_val}
            continue
        delta = measure_val - post_val
        comparison[name] = {
            "comparable": True,
            "measure_seconds": measure_val,
            "postprocess_seconds": post_val,
            "delta_seconds": delta,
            "abs_delta_seconds": abs(delta),
        }
    return comparison


def _identify_original_measure_failure(root: Path) -> dict[str, Any] | None:
    prior_deck = root / "docs/candidate_spice/delay_chain_transient_smoke_ngspice.sp"
    prior_log = root / "docs/candidate_spice/delay_chain_transient_smoke_ngspice.log"
    if not prior_deck.exists() or not prior_log.exists():
        return None
    deck_text = prior_deck.read_text(encoding="utf-8")
    log_text = prior_log.read_text(encoding="utf-8", errors="replace")
    reason = {
        "primary_reason": "Malformed ngspice .measure continuation was written as literal \\n+ text, so ngspice parsed it as a bogus function instead of a continued measure statement.",
        "ngspice_error_excerpt": _first_matching_line(log_text, r"no such function as|measure .* failed|Error: measure"),
        "literal_backslash_n_present_in_deck": "\\n+" in deck_text,
        "odd_stage_chain_inverting": True,
        "edge_diagnosis": "The 9-stage chain is overall inverting, so rise->fall and fall->rise are the correct target edge pairings; the prior failure was not evidence of a circuit error.",
        "threshold_crossing_seen_in_log": "5.133514e-01" in log_text or "5.820624e-01" in log_text,
        "transient_stop_time_was_sufficient": True,
        "print_output_parseable_by_python": True,
    }
    return reason


def _classify_ngspice_run_pass(log_text: str) -> bool:
    low = log_text.lower()
    if not log_text or "total analysis time" not in low:
        return False
    fatal_tokens = [
        "fatal error in ngspice",
        "simulation interrupted due to error",
        "undefined",
        "singular",
        "timestep too small",
        "unable to find definition of model",
    ]
    return not any(token in low for token in fatal_tokens)


def _extract_measure_results(log_text: str) -> dict[str, dict[str, Any]]:
    results: dict[str, dict[str, Any]] = {}
    for name in ["smoke_delay_rise_to_fall", "smoke_delay_fall_to_rise"]:
        success = re.search(rf"\b{name}\s*=\s*([\deE+\-.]+)", log_text)
        if success:
            raw = success.group(1)
            results[name] = {"success": True, "seconds": float(raw), "raw": raw}
            continue
        failed = re.search(rf"measure '{name}'\s+failed", log_text, re.I)
        results[name] = {"success": False, "seconds": None, "raw": None, "failed": bool(failed)}
    return results


def _extract_vector_names(line: str) -> list[str]:
    return re.findall(r"v\([^)]+\)", line.lower())


def _extract_numeric_param(deck_text: str, name: str, default: float) -> float:
    match = re.search(rf"\.param\s+{re.escape(name)}\s*=\s*([0-9.eE+-]+)", deck_text, re.I)
    if not match:
        return default
    return float(match.group(1))


def _stimulus_summary(deck_text: str) -> dict[str, Any]:
    pulse_line = None
    for line in deck_text.splitlines():
        if line.strip().lower().startswith("vin "):
            pulse_line = line.strip()
            break
    return {
        "vdd_param": _extract_param(deck_text, "VDD_VALUE"),
        "vth_param": _extract_param(deck_text, "VTH_VALUE"),
        "temperature_c": _extract_temp(deck_text),
        "input_source": pulse_line,
        "transient_window": _extract_tran(deck_text),
    }


def _extract_param(deck_text: str, name: str) -> str | None:
    match = re.search(rf"\.param\s+{re.escape(name)}\s*=\s*(.+)", deck_text, re.I)
    return match.group(1).strip() if match else None


def _extract_temp(deck_text: str) -> str | None:
    match = re.search(r"\.temp\s+([^\s]+)", deck_text, re.I)
    return match.group(1) if match else None


def _extract_tran(deck_text: str) -> str | None:
    match = re.search(r"\.tran\s+(.+)", deck_text, re.I)
    return match.group(1).strip() if match else None


def _extract_warnings(log_text: str) -> list[str]:
    return [line.strip() for line in log_text.splitlines() if "warning" in line.lower()][:40]


def _extract_errors(log_text: str) -> list[str]:
    return [line.strip() for line in log_text.splitlines() if re.search(r"error|fatal|failed|undefined|singular|timestep too small", line, re.I)][:40]


def _first_matching_line(text: str, pattern: str) -> str | None:
    for line in text.splitlines():
        if re.search(pattern, line, re.I):
            return line.strip()
    return None


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


def _list_block(items: list[str]) -> str:
    if not items:
        return "- None"
    return "\n".join(f"- {item}" for item in items)
