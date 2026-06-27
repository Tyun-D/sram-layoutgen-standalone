"""Timing metadata summary for OpenYield delay-chain smoke evidence."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

PREVIOUS_PVT_CORNER_SMOKE_COMMIT = "fbf2827a9f87234878c0d0c78dd5390a76d344b4"


def build_delay_chain_timing_metadata_report(
    repo_root: str | Path,
    pvt_json_path: str | Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    pvt_json = _resolve_path(root, pvt_json_path)
    pvt_report = json.loads(pvt_json.read_text(encoding="utf-8"))

    head = _run_text(["git", "rev-parse", "HEAD"], cwd=root)
    rows = pvt_report.get("rows", [])
    corner_delay_table = {
        row["corner"]: {
            "VDD": row["VDD"],
            "TEMP": row["TEMP"],
            "rise_to_fall_delay_s": row["rise_to_fall_delay_s"],
            "fall_to_rise_delay_s": row["fall_to_rise_delay_s"],
            "max_delay_s": row["max_delay_s"],
            "notes": row["notes"],
        }
        for row in rows
    }
    worst = pvt_report.get("worst_smoke_delay") or {}

    timing_metadata = {
        "timing_object": "DELAY_CHAIN",
        "source_signal": "rbl",
        "target_signal": "rbl_delay",
        "stage_count": 9,
        "load_policy": "four_load_inverters_per_stage",
        "inversion": "odd_stage_chain_inverts",
        "model_corners": ["nom", "ff", "ss"],
        "VDD": 1.0,
        "TEMP": 25,
        "delay_unit": "s",
        "rise_to_fall_delay_by_corner": {k: v["rise_to_fall_delay_s"] for k, v in corner_delay_table.items()},
        "fall_to_rise_delay_by_corner": {k: v["fall_to_rise_delay_s"] for k, v in corner_delay_table.items()},
        "worst_smoke_delay": worst.get("max_delay_s"),
        "worst_smoke_delay_corner": worst.get("corner"),
        "evidence_type": "ngspice_smoke_only",
        "proof_status": "not_formal_proof",
        "timing_closure_status": "not_timing_closure",
        "physical_integration_status": "not_enabled",
    }

    audit_summary = {
        "delay_chain_timing_metadata_update_available": True,
        "repo_head": head,
        "pvt_corner_smoke_report_found": pvt_json.exists(),
        "pvt_corner_smoke_values_loaded": bool(rows),
        "timing_object_recorded": timing_metadata["timing_object"] == "DELAY_CHAIN",
        "source_signal_recorded": timing_metadata["source_signal"] == "rbl",
        "target_signal_recorded": timing_metadata["target_signal"] == "rbl_delay",
        "stage_count_recorded": timing_metadata["stage_count"] == 9,
        "four_load_policy_recorded": timing_metadata["load_policy"] == "four_load_inverters_per_stage",
        "inversion_recorded": timing_metadata["inversion"] == "odd_stage_chain_inverts",
        "corner_delay_table_recorded": len(corner_delay_table) == 3,
        "worst_smoke_delay_recorded": timing_metadata["worst_smoke_delay"] is not None,
        "timing_metadata_summary_available": True,
        "evidence_timeline_updated": True,
        "milestone_summary_updated": True,
        "can_enter_openyield_source_provenance_linking": True,
        "can_enter_control_timing_mapping_review": True,
        "can_claim_delay_proof_now": False,
        "can_claim_timing_closure_now": False,
        "can_enter_physical_timing_closure_now": False,
        "can_enter_physical_routing_now": False,
        "can_enter_physical_placement_now": False,
        "can_generate_time_control_gds_now": False,
        "can_modify_standalone_now": False,
    }

    return {
        "scope": "delay_chain_timing_metadata_update",
        "repo_root": str(root),
        "repo_head": head,
        "previous_pvt_corner_smoke_commit": PREVIOUS_PVT_CORNER_SMOKE_COMMIT,
        "pvt_corner_smoke_report_path": str(pvt_json),
        "timing_metadata": timing_metadata,
        "corner_delay_table": corner_delay_table,
        "boundary_assertions": {
            "timing_metadata_is_smoke_only": True,
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


def format_delay_chain_timing_metadata_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Delay Chain Timing Metadata Report",
        "",
        f"- Scope: `{report['scope']}`",
        f"- Repo root: `{report['repo_root']}`",
        f"- Repo HEAD: `{report['repo_head']}`",
        f"- Previous PVT corner smoke commit: `{report['previous_pvt_corner_smoke_commit']}`",
        f"- PVT source report: `{report['pvt_corner_smoke_report_path']}`",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Timing Metadata",
        "",
        "```json",
        json.dumps(report["timing_metadata"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Corner Delay Table",
        "",
        "```json",
        json.dumps(report["corner_delay_table"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Boundary Assertions",
        "",
        "```json",
        json.dumps(report["boundary_assertions"], ensure_ascii=False, indent=2),
        "```",
    ]
    return "\n".join(lines)


def format_timing_metadata_summary(report: dict[str, Any]) -> str:
    md = report["timing_metadata"]
    return "\n".join([
        "# Timing Metadata Summary",
        "",
        "## Delay Chain",
        "",
        f"- Timing object: `{md['timing_object']}`",
        f"- Source signal: `{md['source_signal']}`",
        f"- Target signal: `{md['target_signal']}`",
        f"- Stage count: `{md['stage_count']}`",
        f"- Load policy: `{md['load_policy']}`",
        f"- Inversion: `{md['inversion']}`",
        f"- Model corners: `{', '.join(md['model_corners'])}`",
        f"- VDD: `{md['VDD']} V`",
        f"- TEMP: `{md['TEMP']} C`",
        f"- Worst smoke delay: `{md['worst_smoke_delay']} s` at `{md['worst_smoke_delay_corner']}`",
        "",
        "## Corner Delays",
        "",
        f"- `nom`: rise-to-fall `{md['rise_to_fall_delay_by_corner']['nom']} s`, fall-to-rise `{md['fall_to_rise_delay_by_corner']['nom']} s`",
        f"- `ff`: rise-to-fall `{md['rise_to_fall_delay_by_corner']['ff']} s`, fall-to-rise `{md['fall_to_rise_delay_by_corner']['ff']} s`",
        f"- `ss`: rise-to-fall `{md['rise_to_fall_delay_by_corner']['ss']} s`, fall-to-rise `{md['fall_to_rise_delay_by_corner']['ss']} s`",
        "",
        "## Status",
        "",
        "- Evidence type: `ngspice_smoke_only`",
        "- Proof status: `not_formal_proof`",
        "- Timing closure status: `not_timing_closure`",
        "- Physical integration status: `not_enabled`",
    ])


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
