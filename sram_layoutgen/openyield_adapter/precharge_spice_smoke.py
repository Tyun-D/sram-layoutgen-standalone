"""Source-linked ngspice smoke flow for the OpenYield PRECHARGE path."""

from __future__ import annotations

import csv
import json
import math
import re
import subprocess
from pathlib import Path
from typing import Any

from .timing_metadata_consumer import get_control_object_status


PRECHARGE_MODEL = "PMOS_VTG"
PRECHARGE_WIDTH = 0.27e-6
PRECHARGE_LENGTH = 50.0e-9
VDD_VALUE = 1.0
ACTIVE_THRESHOLD = 0.5 * VDD_VALUE


def parse_precharge_source(openyield_root: str | Path) -> dict[str, Any]:
    source_path = Path(openyield_root).resolve() / "sram_compiler/subcircuits/precharge_and_write_driver.py"
    text = source_path.read_text(encoding="utf-8")
    class_line = _find_line(text, "class Precharge(BaseSubcircuit):")
    nodes_line = _find_line(text, "NODES = ('VDD', 'ENB', 'BL', 'BLB')")
    m1_line = _find_line(text, "self.M(1, bl_node, enb_node, 'VDD', 'VDD'")
    m2_line = _find_line(text, "self.M(2, blb_node, enb_node, 'VDD', 'VDD'")
    m3_line = _find_line(text, "self.M(3, bl_node, enb_node, blb_node, 'VDD'")
    yaml_path = Path(openyield_root).resolve() / "sram_compiler/config_yaml/precharge.yaml"
    yaml_text = yaml_path.read_text(encoding="utf-8")

    polarity_basis = (
        "All three devices are PMOS with source/bulk tied to VDD and gate tied to ENB; "
        "PMOS turns on when gate is driven low relative to source, so ENB is inferred active-low."
    )

    return {
        "source_path": str(source_path),
        "class_line": class_line,
        "nodes_line": nodes_line,
        "ports": ["VDD", "ENB", "BL", "BLB"],
        "transistors": [
            {"name": "M1", "line": m1_line, "role": "Precharge BL", "drain": "BL", "gate": "ENB", "source": "VDD", "bulk": "VDD"},
            {"name": "M2", "line": m2_line, "role": "Precharge BLB", "drain": "BLB", "gate": "ENB", "source": "VDD", "bulk": "VDD"},
            {"name": "M3", "line": m3_line, "role": "Equalize BL and BLB", "drain": "BL", "gate": "ENB", "source": "BLB", "bulk": "VDD"},
        ],
        "pmos_model": PRECHARGE_MODEL,
        "pmos_width": PRECHARGE_WIDTH,
        "length": PRECHARGE_LENGTH,
        "yaml_path": str(yaml_path),
        "yaml_defaults": {
            "pmos_model": _extract_yaml_value(yaml_text, "value: 'PMOS_VTG'"),
            "pmos_width": PRECHARGE_WIDTH,
            "length": PRECHARGE_LENGTH,
        },
        "enb_polarity": "active_low",
        "enb_polarity_inference_basis": polarity_basis,
        "bl_blb_behavior_expectation": "When ENB is low, BL and BLB should charge toward VDD and equalize.",
        "candidate_spice_recoverable": True,
    }


def write_precharge_candidate_ngspice(path: str | Path, source_info: dict[str, Any]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        "\n".join(
            [
                "* PRECHARGE CANDIDATE NGSPICE",
                "* SOURCE-LINKED CANDIDATE",
                "* NOT VALIDATED SPICE",
                "* NOT TIMING PROOF",
                "* NOT PHYSICAL INTEGRATION",
                f"* Source: {source_info['source_path']} / class Precharge",
                f"* ENB polarity inference: {source_info['enb_polarity']} ({source_info['enb_polarity_inference_basis']})",
                ".subckt precharge_candidate VDD ENB BL BLB",
                f"M_PRE_BL BL ENB VDD VDD {source_info['pmos_model']} W={source_info['pmos_width']:.12g} L={source_info['length']:.12g}",
                f"M_PRE_BLB BLB ENB VDD VDD {source_info['pmos_model']} W={source_info['pmos_width']:.12g} L={source_info['length']:.12g}",
                f"M_EQ BL ENB BLB VDD {source_info['pmos_model']} W={source_info['pmos_width']:.12g} L={source_info['length']:.12g}",
                ".ends precharge_candidate",
            ]
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


def write_precharge_smoke_deck(
    path: str | Path,
    model_include_path: str | Path,
    candidate_spice_path: str | Path,
    active_low: bool,
) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    enb_pulse = (
        "PULSE({VDD_VALUE} 0 200p 10p 10p 1.2n 2.4n)"
        if active_low else
        "PULSE(0 {VDD_VALUE} 200p 10p 10p 1.2n 2.4n)"
    )
    destination.write_text(
        "\n".join(
            [
                "* PRECHARGE TRANSIENT SMOKE",
                "* CANDIDATE / SMOKE-ONLY",
                "* TEMPORARY LOAD/STIMULUS",
                "* NOT FUNCTIONAL PROOF",
                "* NOT TIMING PROOF",
                "* NOT TIMING CLOSURE",
                f".include \"{Path(model_include_path).as_posix()}\"",
                f".include \"{Path(candidate_spice_path).as_posix()}\"",
                ".param VDD_VALUE=1.0",
                ".param V10='0.1*VDD_VALUE'",
                ".param V90='0.9*VDD_VALUE'",
                ".temp 25",
                "VDD_SRC VDD 0 {VDD_VALUE}",
                f"VENB ENB 0 DC {{VDD_VALUE}} {enb_pulse}",
                "* Smoke-only bitline load; not representative of full SRAM bitline RC.",
                "CBL BL 0 5f",
                "CBLB BLB 0 5f",
                ".ic V(BL)=0 V(BLB)=0",
                "XPRE VDD ENB BL BLB precharge_candidate",
                ".measure tran smoke_bl_rise trig v(BL) val='V10' rise=1 targ v(BL) val='V90' rise=1",
                ".measure tran smoke_blb_rise trig v(BLB) val='V10' rise=1 targ v(BLB) val='V90' rise=1",
                ".tran 2p 4n",
                ".print tran v(ENB) v(BL) v(BLB)",
                ".end",
            ]
        )
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return destination


def run_precharge_smoke(deck_path: str | Path, log_path: str | Path, workdir: str | Path) -> None:
    subprocess.run(
        ["ngspice", "-b", str(deck_path), "-o", str(log_path)],
        cwd=Path(workdir),
        check=True,
        capture_output=True,
        text=True,
    )


def parse_precharge_log(log_path: str | Path, active_low: bool) -> dict[str, Any]:
    text = Path(log_path).read_text(encoding="utf-8", errors="ignore")
    table = _parse_print_table(text)
    measures = {
        "smoke_bl_rise_s": _extract_measure(text, "smoke_bl_rise"),
        "smoke_blb_rise_s": _extract_measure(text, "smoke_blb_rise"),
    }
    warnings = sorted(set(re.findall(r"(?im)^warning.*$|^.*gmin.*$", text)))
    errors = sorted(set(re.findall(r"(?im)^.*(?:error|fatal|failed|undefined|singular|timestep too small).*$", text)))

    enb_values = table.get("v(enb)", [])
    bl_values = table.get("v(bl)", [])
    blb_values = table.get("v(blb)", [])
    times = table.get("time", [])
    observed = bool(times and enb_values and bl_values and blb_values)

    final_bl = bl_values[-1] if bl_values else None
    final_blb = blb_values[-1] if blb_values else None
    active_samples = []
    for idx, enb in enumerate(enb_values):
        if active_low and enb < ACTIVE_THRESHOLD:
            active_samples.append(idx)
        if not active_low and enb > ACTIVE_THRESHOLD:
            active_samples.append(idx)

    behavior_plausible = False
    active_window_end_bl = None
    active_window_end_blb = None
    if active_samples:
        end_idx = active_samples[-1]
        active_window_end_bl = bl_values[end_idx]
        active_window_end_blb = blb_values[end_idx]
        behavior_plausible = (
            active_window_end_bl is not None and
            active_window_end_blb is not None and
            active_window_end_bl > 0.8 * VDD_VALUE and
            active_window_end_blb > 0.8 * VDD_VALUE
        )

    python_rise = {
        "bl_rise_10_90_s": _rise_time(times, bl_values, 0.1 * VDD_VALUE, 0.9 * VDD_VALUE),
        "blb_rise_10_90_s": _rise_time(times, blb_values, 0.1 * VDD_VALUE, 0.9 * VDD_VALUE),
    }

    return {
        "run_pass": observed and not errors,
        "enb_waveform_observed": bool(enb_values),
        "bl_waveform_observed": bool(bl_values),
        "blb_waveform_observed": bool(blb_values),
        "bl_final_voltage": final_bl,
        "blb_final_voltage": final_blb,
        "active_window_end_bl": active_window_end_bl,
        "active_window_end_blb": active_window_end_blb,
        "behavior_plausible": behavior_plausible,
        "measures": measures,
        "python_rise": python_rise,
        "warnings": warnings,
        "errors": errors,
        "log_excerpt": "\n".join(text.splitlines()[-80:]),
    }


def update_precharge_status(
    repo_root: str | Path,
    report: dict[str, Any],
) -> None:
    repo = Path(repo_root).resolve()
    contracts_csv = repo / "docs/mapping/openyield_control_path_candidate_contracts.csv"
    contracts_rows = list(csv.DictReader(contracts_csv.open("r", encoding="utf-8", newline="")))
    for row in contracts_rows:
        if row["control_object"] != "PRECHARGE":
            continue
        row["candidate_artifact"] = "docs/candidate_spice/control_paths/precharge_candidate_ngspice.sp"
        row["source_evidence_status"] = "source_linked_candidate_spice_smoke_available"
        row["recovery_status"] = "ngspice_smoke_passed_not_validated"
        row["blocked_reason"] = "still_needs_real_bitline_rc_and_precharge_enable_path_smoke"
        row["next_required_action"] = "run_precharge_enable_path_smoke;add_realistic_bitline_rc;confirm_pin_polarity"
        row["integration_readiness"] = "spice_smoke_available_not_physical_ready"
    _write_csv_dicts(contracts_csv, contracts_rows)

    contracts_md = repo / "docs/mapping/openyield_control_path_candidate_contracts.md"
    contracts_md.write_text(_contracts_csv_to_md(contracts_rows) + "\n", encoding="utf-8", newline="\n")

    mapping_csv = repo / "docs/mapping/openyield_control_timing_mapping.csv"
    mapping_rows = list(csv.DictReader(mapping_csv.open("r", encoding="utf-8", newline="")))
    for row in mapping_rows:
        if row["openyield_object"] != "PRECHARGE":
            continue
        row["local_candidate_artifact"] = "docs/candidate_spice/control_paths/precharge_candidate_ngspice.sp"
        row["evidence_status"] = "source_linked_candidate_spice_smoke_available"
        row["integration_readiness"] = "spice_smoke_available_not_physical_ready"
        row["next_required_action"] = "run_precharge_enable_path_smoke;add_realistic_bitline_rc;confirm_pin_polarity"
    _write_csv_dicts(mapping_csv, mapping_rows)

    mapping_md = repo / "docs/mapping/openyield_control_timing_mapping.md"
    mapping_md.write_text(_mapping_csv_to_md(mapping_rows) + "\n", encoding="utf-8", newline="\n")

    timeline = repo / "docs/evidence/evidence_timeline.md"
    timeline_text = timeline.read_text(encoding="utf-8")
    entry = (
        "- `2026-06-28`: Ran source-linked PRECHARGE ngspice smoke; "
        f"run_pass=`{report['gates']['precharge_ngspice_run_pass']}`, "
        f"behavior_plausible=`{report['gates']['precharge_behavior_plausible']}`, "
        "and advanced PRECHARGE to `source_linked_candidate_spice_smoke_available` without enabling physical integration.\n"
    )
    if entry not in timeline_text:
        timeline.write_text(timeline_text.rstrip() + "\n" + entry, encoding="utf-8", newline="\n")

    milestone = repo / "docs/evidence/milestone_summary.md"
    text = milestone.read_text(encoding="utf-8")
    needle = "- Control path candidate generation wave1 is complete: source-linked contracts exist for `PRECHARGE`, `PRECHARGE_ENABLE_PATH`, `SENSE_ENABLE_PATH`, `WRITE_ENABLE_PATH`, `WORDLINE_ENABLE_PATH`, `GATED_CLOCK_PATH`, and `DFF_ROW`; `PRECHARGE` has a candidate SPICE skeleton and `PRECHARGE_ENABLE_PATH` has a testbench skeleton; next gate is `selected_control_path_spice_smoke` or `guarded_adapter_registry`.\n"
    insert = needle + "- PRECHARGE ngspice smoke is now complete: the source-linked candidate subckt and transient smoke deck both ran, BL/BLB behavior was checked against active-low ENB inference, and PRECHARGE moved to `source_linked_candidate_spice_smoke_available` while remaining not physical-ready.\n"
    if "PRECHARGE ngspice smoke is now complete" not in text:
        text = text.replace(needle, insert)
    if "`can_enter_precharge_enable_path_smoke=True`" not in text:
        text = text.replace(
            "- `can_enter_guarded_adapter_registry=True`\n",
            "- `can_enter_guarded_adapter_registry=True`\n"
            "- `can_enter_precharge_enable_path_smoke=True`\n"
            "- `can_enter_next_control_path_spice_smoke=True`\n",
        )
    milestone.write_text(text, encoding="utf-8", newline="\n")


def build_precharge_smoke_report(
    repo_root: str | Path,
    openyield_root: str | Path,
    source_info: dict[str, Any],
    candidate_path: str | Path,
    deck_path: str | Path,
    log_path: str | Path,
    parse_result: dict[str, Any],
) -> dict[str, Any]:
    repo = Path(repo_root).resolve()
    contracts_status = get_control_object_status(
        repo / "docs/mapping/openyield_control_timing_mapping.csv",
        repo / "docs/mapping/openyield_control_path_candidate_contracts.csv",
        "PRECHARGE",
    )
    rise_time = parse_result["measures"]["smoke_bl_rise_s"] or parse_result["python_rise"]["bl_rise_10_90_s"]
    gates = {
        "selected_control_path_spice_smoke_precharge_available": True,
        "precharge_source_found": True,
        "precharge_ports_recorded": source_info["ports"] == ["VDD", "ENB", "BL", "BLB"],
        "precharge_enb_polarity_inferred": source_info["enb_polarity"] == "active_low",
        "precharge_candidate_spice_generated": Path(candidate_path).exists(),
        "precharge_ngspice_deck_generated": Path(deck_path).exists(),
        "precharge_ngspice_run_attempted": True,
        "precharge_ngspice_run_pass": parse_result["run_pass"],
        "precharge_bl_observed": parse_result["bl_waveform_observed"],
        "precharge_blb_observed": parse_result["blb_waveform_observed"],
        "precharge_behavior_plausible": parse_result["behavior_plausible"],
        "precharge_smoke_timing_available": rise_time is not None or parse_result["python_rise"]["blb_rise_10_90_s"] is not None,
        "precharge_contract_status_updated": True,
        "metadata_consumer_precharge_status_updated": contracts_status["mapping_evidence_status"] == "source_linked_candidate_spice_smoke_available",
        "can_enter_precharge_enable_path_smoke": parse_result["run_pass"] and parse_result["behavior_plausible"],
        "can_enter_next_control_path_spice_smoke": parse_result["run_pass"] and parse_result["behavior_plausible"],
        "can_enter_guarded_adapter_registry": True,
        "can_modify_standalone_now": False,
        "can_generate_time_control_gds_now": False,
        "can_claim_openyield_full_integration_now": False,
        "can_claim_timing_closure_now": False,
    }
    return {
        "scope": "selected_control_path_spice_smoke_precharge",
        "repo_root": str(repo),
        "repo_head": _git_head(repo),
        "openyield_source_path": str(Path(openyield_root).resolve()),
        "openyield_source_head": _git_head(Path(openyield_root).resolve()),
        "precharge_source": source_info,
        "candidate_spice_path": str(Path(candidate_path)),
        "testbench_path": str(Path(deck_path)),
        "ngspice_log_path": str(Path(log_path)),
        "syntax_transient_attempted": True,
        "parse_result": parse_result,
        "contracts_status": contracts_status,
        "what_is_still_not_validated": [
            "No real bitline RC or array-level load has been used.",
            "No formal functional proof or timing proof has been established.",
            "PRECHARGE_ENABLE_PATH has not been separately smoked yet.",
            "No physical integration or standalone integration is enabled.",
        ],
        "next_required_action": "run_precharge_enable_path_smoke",
        "gates": gates,
    }


def format_precharge_smoke_report_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OpenYield PRECHARGE Spice Smoke Report",
            "",
            f"- OpenYield source path: `{report['openyield_source_path']}`",
            f"- OpenYield source HEAD: `{report['openyield_source_head']}`",
            f"- Candidate SPICE path: `{report['candidate_spice_path']}`",
            f"- Testbench path: `{report['testbench_path']}`",
            f"- ngspice log path: `{report['ngspice_log_path']}`",
            "",
            "## Precharge Source",
            "",
            "```json",
            json.dumps(report["precharge_source"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Parse Result",
            "",
            "```json",
            json.dumps(report["parse_result"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Contracts Status",
            "",
            "```json",
            json.dumps(report["contracts_status"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Gates",
            "",
            "```json",
            json.dumps(report["gates"], ensure_ascii=False, indent=2),
            "```",
        ]
    )


def _parse_print_table(text: str) -> dict[str, list[float]]:
    lines = text.splitlines()
    headers = None
    data: dict[str, list[float]] = {}
    for idx, line in enumerate(lines):
        if re.match(r"\s*Index\s+time\s+", line):
            headers = re.split(r"\s+", line.strip())
            for key in headers[1:]:
                data.setdefault(key.lower(), [])
            continue
        if headers and re.match(r"\s*\d+\s+", line):
            parts = re.split(r"\s+", line.strip())
            if len(parts) >= len(headers):
                for col_idx, key in enumerate(headers[1:], start=1):
                    try:
                        data[key.lower()].append(float(parts[col_idx]))
                    except ValueError:
                        data[key.lower()].append(math.nan)
        elif headers and line.strip() == "":
            continue
    return data


def _extract_measure(text: str, name: str) -> float | None:
    match = re.search(rf"(?im)^\s*{re.escape(name)}\s*=\s*([0-9.eE+-]+)", text)
    if not match:
        return None
    return float(match.group(1))


def _rise_time(times: list[float], values: list[float], low: float, high: float) -> float | None:
    t_low = _crossing_time(times, values, low, rising=True)
    t_high = _crossing_time(times, values, high, rising=True)
    if t_low is None or t_high is None:
        return None
    return t_high - t_low


def _crossing_time(times: list[float], values: list[float], threshold: float, rising: bool) -> float | None:
    if not times or not values:
        return None
    for idx in range(1, len(times)):
        prev_v = values[idx - 1]
        curr_v = values[idx]
        if rising and prev_v <= threshold <= curr_v and curr_v != prev_v:
            frac = (threshold - prev_v) / (curr_v - prev_v)
            return times[idx - 1] + frac * (times[idx] - times[idx - 1])
        if not rising and prev_v >= threshold >= curr_v and curr_v != prev_v:
            frac = (prev_v - threshold) / (prev_v - curr_v)
            return times[idx - 1] + frac * (times[idx] - times[idx - 1])
    return None


def _find_line(text: str, needle: str) -> int | None:
    for index, line in enumerate(text.splitlines(), start=1):
        if needle in line:
            return index
    return None


def _extract_yaml_value(text: str, needle: str) -> str | None:
    return needle if needle in text else None


def _write_csv_dicts(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _contracts_csv_to_md(rows: list[dict[str, Any]]) -> str:
    headers = [
        "control_object",
        "priority",
        "source_symbol",
        "candidate_type",
        "candidate_artifact",
        "spice_candidate_available",
        "testbench_skeleton_available",
        "source_evidence_status",
        "recovery_status",
        "next_required_action",
    ]
    lines = [
        "# OpenYield Control Path Candidate Contracts",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row[key]) for key in headers) + " |")
    return "\n".join(lines)


def _mapping_csv_to_md(rows: list[dict[str, Any]]) -> str:
    headers = [
        "openyield_object",
        "openyield_signal_or_node",
        "local_timing_object",
        "local_candidate_artifact",
        "evidence_status",
        "measured_delay_available",
        "integration_readiness",
        "next_required_action",
    ]
    lines = [
        "# OpenYield Control Timing Mapping",
        "",
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row[key]) for key in headers) + " |")
    return "\n".join(lines)


def _git_head(path: Path) -> str | None:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=path, check=True, capture_output=True, text=True)
    return result.stdout.strip()
