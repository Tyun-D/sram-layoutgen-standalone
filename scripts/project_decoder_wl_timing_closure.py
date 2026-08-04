#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import json
import shutil
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import project_decoder_physical_architecture_evidence as evidence
import project_decoder_wl_array_integration_generate as integration

OUT = ROOT / "outputs" / "PROJECT_decoder_physical_timing_closure"
P2_TOP = "candidate_p2_partitioned_control_centered"


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def make_v2(candidate_id: str) -> dict[str, object]:
    out = OUT / candidate_id
    source_csv = out / "WL_GEOMETRY_RC.csv"
    rows = list(csv.DictReader(source_csv.open(encoding="utf-8", newline="")))
    for row in rows:
        row["rc_evidence_level"] = "NORMALIZED_GEOMETRY_RC_PROXY"
        row["not_post_layout_pex"] = "True"
        row["estimated_R_ohm"] = "AUTHORITY_PENDING"
        row["estimated_C_fF"] = "AUTHORITY_PENDING"
        row["estimated_RC_s"] = "AUTHORITY_PENDING"
    fields = list(rows[0])
    with (out / "WL_GEOMETRY_RC_V2.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    shutil.copy2(out / "WL_TIMING_PROXY.csv", out / "WL_TIMING_PROXY_V2.csv")
    waveform_src = out / "WL_TIMING_PROXY_WAVEFORMS"
    waveform_dst = out / "WL_TIMING_PROXY_V2_WAVEFORMS"
    if waveform_dst.exists():
        shutil.rmtree(waveform_dst)
    shutil.copytree(waveform_src, waveform_dst)
    old_summary = json.loads((out / "WL_TIMING_PROXY_SUMMARY.json").read_text(encoding="utf-8"))
    old_summary.update({
        "schema_version": 2,
        "rc_evidence_level": "NORMALIZED_GEOMETRY_RC_PROXY",
        "not_post_layout_pex": True,
        "formal_timing_authority": "PENDING",
    })
    write_json(out / "WL_TIMING_PROXY_V2_SUMMARY.json", old_summary)
    return old_summary


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    integration.OUT_ROOT = OUT
    candidates = [
        integration.IntegrationCandidate("T0_p2_interleaved_baseline", P2_TOP, "T0_P2_locked_local_baseline", "col16", 5.0, 4.0),
        integration.IntegrationCandidate("T1_common_egress_plane", P2_TOP, "T1_common_egress_plane", "col16", 5.0, 4.0, interleave_gap=0.50),
        integration.IntegrationCandidate("T2_controlled_short_path_compensation", P2_TOP, "T2_controlled_short_path_compensation", "col16", 5.0, 4.0, interleave_gap=0.80),
        integration.IntegrationCandidate("T3_driver_column_spacing_pareto", P2_TOP, "T3_driver_column_spacing_optimization", "col16", 4.0, 3.0, interleave_gap=1.20),
        integration.IntegrationCandidate("TREAL_L3_array_authority_pending", P2_TOP, "REAL_ARRAY_GEOMETRY_AUTHORITY_PENDING", "col16", 5.0, 4.0, interleave_gap=0.80, array_object="full_bitcell_array_gds"),
    ]
    generation = []
    for candidate in candidates:
        generation.append(integration._generate_candidate(candidate))

    evidence.INTEGRATION_ROOT = OUT
    evidence.CANDIDATES = {candidate.candidate_id: P2_TOP for candidate in candidates}
    summaries = []
    for candidate in candidates:
        power = evidence.build_power_evidence(candidate.candidate_id, P2_TOP)
        timing = evidence.build_wl_and_timing(candidate.candidate_id)
        negative = evidence.build_architecture_negative_suite(candidate.candidate_id)
        metrics = evidence.candidate_metrics(candidate.candidate_id, power, timing)
        v2 = make_v2(candidate.candidate_id)
        gate = json.loads((OUT / candidate.candidate_id / "integration_machine_gate.json").read_text(encoding="utf-8"))
        gate.update({
            "power_endpoint_coverage_passed": power["passed"],
            "power_endpoint_count": power["endpoint_count"],
            "architecture_negative_suite_passed": negative["negative_tests_passed"],
            "architecture_negative_unexpected_pass_count": negative["unexpected_pass_count"],
            "timing_proxy_v2_completed": v2["timing_proxy_completed"],
            "formal_timing_passed": False,
            "timing_budget_authority": "TIMING_BUDGET_AUTHORITY_PENDING",
            "rc_evidence_level": "NORMALIZED_GEOMETRY_RC_PROXY",
            "not_post_layout_pex": True,
            "source_p2_integration_sha256": "ab782be31840705a225c1e2a71a2bb88fe31d9ae5ac792cbe0c7bfe9348d88d9",
        })
        semantic_implemented = not candidate.candidate_id.startswith(("T1_", "T2_"))
        gate["semantic_candidate_name_contract_passed"] = semantic_implemented
        if not semantic_implemented:
            gate.setdefault("blocking_reasons", []).append("SEMANTIC_CANDIDATE_NAME_CONTRACT_FAILED")
        gate["machine_green"] = all([
            gate["drc_marker_count"] == 0, gate["connectivity_passed"], gate["power_continuity_passed"],
            gate["foreign_net_passed"], gate["pin_access_passed"], gate["hierarchy_passed"],
            gate["determinism_passed"], gate["negative_tests_passed"], gate["bit_exact_wl_mapping_passed"],
            gate["driver_row_alignment_passed"], gate["driver_output_to_array_crossing_count"] == 0,
            power["passed"], negative["negative_tests_passed"], v2["timing_proxy_completed"], semantic_implemented,
        ])
        write_json(OUT / candidate.candidate_id / "machine_gate.json", gate)
        summaries.append({**metrics, "machine_green": gate["machine_green"], "max_rc_over_median": v2["max_rc_proxy_over_median"], "max_arrival_skew_s": v2["max_arrival_skew_s"], "slew_ratio": v2["slew_ratio"]})

    t4 = {
        "candidate_id": "T4_1x16_single_column_feasibility",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "passed": False,
        "rejection_code": "T4_DRIVER_HEIGHT_EXCEEDS_ARRAY_ROW_PITCH",
        "driver_height_um": 1.8875,
        "array_row_pitch_um": 1.565,
        "reason": "A literal 1x16 R0 column overlaps adjacent physical driver instances; unproven rotations and power-polarity changes are prohibited.",
    }
    write_json(OUT / "T4_1x16_single_column_feasibility" / "feasibility_gate.json", t4)
    with (OUT / "WL_TIMING_CLOSURE_COMPARISON.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)
    write_json(OUT / "WL_TIMING_CLOSURE_SUMMARY.json", {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "candidate_count": len(summaries),
        "machine_green_count": sum(bool(row["machine_green"]) for row in summaries),
        "formal_timing_authority": "PENDING",
        "rc_evidence_level": "NORMALIZED_GEOMETRY_RC_PROXY",
        "not_post_layout_pex": True,
        "candidates": summaries,
        "t4": t4,
    })
    return 0 if any(row["machine_green"] for row in summaries if str(row["candidate_id"]).startswith("T3")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
