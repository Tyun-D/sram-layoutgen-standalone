"""Server-side ngspice transient smoke report helpers for candidate delay-chain SPICE."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any



def build_delay_chain_transient_smoke_report(
    repo_root: str | Path,
    candidate_dir: str | Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    candidate = _resolve_path(root, candidate_dir)
    include_file = candidate / "local_model_include_nom_server.inc"
    deck_file = candidate / "delay_chain_transient_smoke_ngspice.sp"
    log_file = candidate / "delay_chain_transient_smoke_ngspice.log"

    head = _run_text(["git", "rev-parse", "HEAD"], cwd=root)
    ngspice_path = _which("ngspice")
    ngspice_version = _run_text(["ngspice", "-v"], cwd=root) if ngspice_path else None

    deck_text = deck_file.read_text(encoding="utf-8") if deck_file.exists() else ""
    log_text = log_file.read_text(encoding="utf-8", errors="replace") if log_file.exists() else ""

    model_paths = _parse_include_paths(include_file)
    stage_count = len(re.findall(r"^Xdinv\d+\b", deck_text, re.M))
    load_count = len(re.findall(r"^Xdload_\d+_\d+\b", deck_text, re.M))
    transient_attempted = log_file.exists()
    transient_run_pass = _classify_transient_pass(log_text)
    rbl_delay_observed = _rbl_delay_observed(log_text)
    measure_attempted = ".measure" in deck_text.lower()
    measure_pass, smoke_delay_value = _extract_measure(log_text)
    warnings = _extract_warnings(log_text)
    errors = _extract_errors(log_text)
    failure_classification = None
    if not transient_run_pass:
        failure_classification = _classify_failure(log_text)
    elif measure_attempted and not measure_pass:
        failure_classification = {"code": "E", "label": "measure syntax issue"}

    audit_summary = {
        "delay_chain_transient_smoke_available": True,
        "repo_head": head,
        "ngspice_found": ngspice_path is not None,
        "model_include_available": include_file.exists(),
        "transient_deck_generated": deck_file.exists(),
        "transient_attempted": transient_attempted,
        "transient_run_pass": transient_run_pass,
        "rbl_delay_observed": rbl_delay_observed,
        "measure_attempted": measure_attempted,
        "measure_pass": measure_pass,
        "smoke_delay_value_available": smoke_delay_value is not None,
        "can_enter_delay_measurement_refinement": transient_run_pass and rbl_delay_observed,
        "can_claim_delay_proof_now": False,
        "can_claim_timing_closure_now": False,
        "can_enter_physical_timing_closure_now": False,
        "can_enter_physical_routing_now": False,
        "can_enter_physical_placement_now": False,
        "can_generate_time_control_gds_now": False,
        "can_modify_standalone_now": False,
    }

    report = {
        "scope": "delay_chain_ngspice_transient_smoke",
        "repo_root": str(root),
        "repo_head": head,
        "candidate_dir": str(candidate),
        "ngspice": {"path": ngspice_path, "version": ngspice_version},
        "model_include": {
            "path": str(include_file),
            "exists": include_file.exists(),
            "model_paths": model_paths,
        },
        "transient_deck": {
            "path": str(deck_file),
            "exists": deck_file.exists(),
            "contents": deck_text,
        },
        "stimulus_summary": _stimulus_summary(deck_text),
        "stage_count": stage_count,
        "four_load_policy": {
            "loads_per_stage_expected": 4,
            "load_instances_found": load_count,
            "policy_matches_candidate_topology": load_count == stage_count * 4 if stage_count else False,
        },
        "transient_attempted": transient_attempted,
        "transient_run_pass": transient_run_pass,
        "rbl_delay_observed": rbl_delay_observed,
        "measure_attempted": measure_attempted,
        "measure_pass": measure_pass,
        "smoke_only_measured_delay": smoke_delay_value,
        "key_warnings": warnings,
        "key_errors": errors,
        "failure_classification": failure_classification,
        "key_log_excerpt": _build_log_excerpt(log_text),
        "boundary_assertions": {
            "transient_smoke_is_not_delay_proof": True,
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


def format_delay_chain_transient_smoke_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Delay Chain Transient Smoke Report",
        "",
        f"- Scope: `{report['scope']}`",
        f"- Repo root: `{report['repo_root']}`",
        f"- Repo HEAD: `{report['repo_head']}`",
        f"- Candidate dir: `{report['candidate_dir']}`",
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
        "## Model Include",
        "",
        "```json",
        json.dumps(report["model_include"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Transient Deck",
        "",
        "```json",
        json.dumps(report["transient_deck"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Stimulus And Topology",
        "",
        "```json",
        json.dumps(
            {
                "stimulus_summary": report["stimulus_summary"],
                "stage_count": report["stage_count"],
                "four_load_policy": report["four_load_policy"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        "```",
        "",
        "## Transient Result",
        "",
        "```json",
        json.dumps(
            {
                "transient_attempted": report["transient_attempted"],
                "transient_run_pass": report["transient_run_pass"],
                "rbl_delay_observed": report["rbl_delay_observed"],
                "measure_attempted": report["measure_attempted"],
                "measure_pass": report["measure_pass"],
                "smoke_only_measured_delay": report["smoke_only_measured_delay"],
                "failure_classification": report["failure_classification"],
            },
            ensure_ascii=False,
            indent=2,
        ),
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
        "## Key Log Excerpt",
        "",
        "```text",
        report["key_log_excerpt"] or "",
        "```",
        "",
        "## Boundary Assertions",
        "",
        "```json",
        json.dumps(report["boundary_assertions"], ensure_ascii=False, indent=2),
        "```",
    ]
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


def _parse_include_paths(include_file: Path) -> list[str] | dict[str, str]:
    if not include_file.exists():
        return {"include_file_missing": str(include_file)}
    includes: list[str] = []
    for line in include_file.read_text(encoding="utf-8").splitlines():
        text = line.strip()
        if not text.lower().startswith(".include"):
            continue
        match = re.search(r'"([^"]+)"', text)
        if match:
            includes.append(match.group(1))
    return includes


def _stimulus_summary(deck_text: str) -> dict[str, Any]:
    pulse_line = None
    for line in deck_text.splitlines():
        if line.strip().lower().startswith("vin "):
            pulse_line = line.strip()
            break
    return {
        "vdd_param": _extract_param(deck_text, "VDD_VALUE"),
        "temperature_c": _extract_temp(deck_text),
        "input_source": pulse_line,
        "measurement_note": "Smoke-only delay measure is not timing proof." if ".measure" in deck_text.lower() else None,
    }


def _extract_param(deck_text: str, name: str) -> str | None:
    match = re.search(rf"\.param\s+{re.escape(name)}\s*=\s*([^\s]+)", deck_text, re.I)
    return match.group(1) if match else None


def _extract_temp(deck_text: str) -> str | None:
    match = re.search(r"\.temp\s+([^\s]+)", deck_text, re.I)
    return match.group(1) if match else None


def _classify_transient_pass(log_text: str) -> bool:
    if not log_text:
        return False
    low = log_text.lower()
    if "total analysis time" not in low:
        return False
    fatal_tokens = (
        "fatal error in ngspice",
        "simulation interrupted due to error",
        "undefined",
        "singular",
        "timestep too small",
        "unknown parameter",
        "unable to find definition of model",
    )
    return not any(token in low for token in fatal_tokens)


def _rbl_delay_observed(log_text: str) -> bool:
    if "v(rbl_delay)" not in log_text.lower():
        return False
    return bool(re.search(r"\d+\s+[\deE+\-.]+\s+[\deE+\-.]+(?:\s+[\deE+\-.]+){2,}", log_text))


def _extract_measure(log_text: str) -> tuple[bool, dict[str, Any] | None]:
    match = re.search(r"smoke_delay_rise_to_fall\s*=\s*([\deE+\-.]+)", log_text, re.I)
    if not match:
        return False, None
    raw = match.group(1)
    try:
        value = float(raw)
    except ValueError:
        return False, {"name": "smoke_delay_rise_to_fall", "raw": raw}
    return True, {"name": "smoke_delay_rise_to_fall", "seconds": value, "raw": raw}


def _extract_warnings(log_text: str) -> list[str]:
    warnings = []
    for line in log_text.splitlines():
        if "warning" in line.lower():
            warnings.append(line.strip())
    return warnings[:40]


def _extract_errors(log_text: str) -> list[str]:
    errors = []
    for line in log_text.splitlines():
        if re.search(r"error|fatal|failed|undefined|singular|timestep too small", line, re.I):
            errors.append(line.strip())
    return errors[:40]


def _classify_failure(log_text: str) -> dict[str, str]:
    low = log_text.lower()
    if any(token in low for token in ["gmin", "source stepping", "timestep too small", "singular"]):
        return {"code": "A", "label": "convergence issue"}
    if any(token in low for token in ["pulse", "vin", "no dc value"]):
        return {"code": "B", "label": "deck stimulus issue"}
    if any(token in low for token in ["unknown node", "vector rbl_delay is not available", "no such vector"]):
        return {"code": "C", "label": "node naming issue"}
    if any(token in low for token in ["unknown parameter", "unknown model", "unable to find definition of model", "mos1", "bsim"]):
        return {"code": "D", "label": "model/device issue"}
    if any(token in low for token in ["measure", "bad syntax"]):
        return {"code": "E", "label": "measure syntax issue"}
    return {"code": "F", "label": "other"}


def _build_log_excerpt(log_text: str, line_limit: int = 60) -> str:
    if not log_text:
        return ""
    selected = []
    for line in log_text.splitlines():
        low = line.lower()
        if any(token in low for token in ["warning", "error", "fatal", "measure", "rbl_delay", "smoke_delay"]):
            selected.append(line)
    if selected:
        return "\n".join(selected[:line_limit])
    return "\n".join(log_text.splitlines()[-line_limit:])


def _list_block(items: list[str]) -> str:
    if not items:
        return "- None"
    return "\n".join(f"- {item}" for item in items)
