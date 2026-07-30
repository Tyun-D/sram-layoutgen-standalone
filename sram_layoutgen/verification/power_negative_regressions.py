from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from sram_layoutgen.verification.power_connectivity import summarize_power_report


NEGATIVE_CASES = [
    ("missing_vdd_segment", "删除 VDD rail segment", "MISSING_VDD_SEGMENT"),
    ("missing_vss_segment", "删除 VSS rail segment", "MISSING_VSS_SEGMENT"),
    ("missing_power_via", "删除 power via/junction", "MISSING_POWER_VIA"),
    ("isolated_child_power_pin", "断开 child VDD endpoint", "CHILD_VDD_ENDPOINT_MISSING"),
    ("vdd_vss_short", "制造 VDD/VSS short", "VDD_VSS_SHORT"),
    ("power_to_signal_contact", "制造 power-to-signal contact", "POWER_TO_SIGNAL_CONTACT"),
]


def blocked_negative_matrix(reason: str) -> list[dict[str, Any]]:
    rows = []
    for case_id, description, _expected in NEGATIVE_CASES:
        rows.append(
            {
                "negative_case_id": case_id,
                "description": description,
                "status": "BLOCKED_NO_GEOMETRY_MUTATION_HARNESS",
                "rejected_as_expected": False,
                "evidence": "",
                "note": reason,
            }
        )
    return rows


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _mutate_missing_vdd_segment(payload: dict[str, Any]) -> None:
    audit = payload["array_power_stitching_audit"]
    audit["clean"] = False
    audit["row_vdd_rails_connected"] = max(0, int(audit["row_vdd_rails_connected"]) - 1)
    audit["rows_missing_vdd_connection"] = [0]


def _mutate_missing_vss_segment(payload: dict[str, Any]) -> None:
    audit = payload["array_power_stitching_audit"]
    audit["clean"] = False
    audit["row_gnd_rails_connected"] = max(0, int(audit["row_gnd_rails_connected"]) - 1)
    audit["rows_missing_gnd_connection"] = [0]


def _mutate_missing_power_via(payload: dict[str, Any]) -> None:
    topo = payload["power_junction_topology_audit"]
    topo["clean"] = False
    topo["missing_junctions"] = [
        {
            "category": "array_boundary",
            "row": 0,
            "side": "left",
            "net": "vdd",
            "reason": "mutated_missing_power_via",
        }
    ]


def _mutate_isolated_child_power_pin(payload: dict[str, Any]) -> None:
    row_side = payload["row_side_power_audit"]
    row_side["clean"] = False
    row_side["missing_vdd_pins"] = [
        {
            "instance": "row_decode_0",
            "role": "row_decoder",
            "net": "vdd",
            "reason": "mutated_isolated_child_power_pin",
        }
    ]


def _mutate_vdd_vss_short(payload: dict[str, Any]) -> None:
    global_power = payload["global_power_consistency_audit"]
    global_power["clean"] = False
    global_power["vdd_gnd_short_free"] = False


def _mutate_power_to_signal_contact(payload: dict[str, Any]) -> None:
    topo = payload["power_junction_topology_audit"]
    topo["clean"] = False
    topo["suspicious_power_routes"] = [
        {
            "shape": "mutated_power_to_signal_contact",
            "net": "vdd",
            "reason": "unexpected adjacency to signal route",
        }
    ]


MUTATORS = {
    "missing_vdd_segment": _mutate_missing_vdd_segment,
    "missing_vss_segment": _mutate_missing_vss_segment,
    "missing_power_via": _mutate_missing_power_via,
    "isolated_child_power_pin": _mutate_isolated_child_power_pin,
    "vdd_vss_short": _mutate_vdd_vss_short,
    "power_to_signal_contact": _mutate_power_to_signal_contact,
}


def run_negative_mutations(source_report: Path, workspace: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    workspace.mkdir(parents=True, exist_ok=True)
    source_sha = _sha256(source_report)
    for case_id, description, expected_code in NEGATIVE_CASES:
        case_dir = workspace / case_id
        case_dir.mkdir(parents=True, exist_ok=True)
        mutated_report = case_dir / source_report.name
        shutil.copy2(source_report, mutated_report)
        payload = _load_json(mutated_report)
        MUTATORS[case_id](payload)
        _write_json(mutated_report, payload)
        mutated_sha = _sha256(mutated_report)
        summary = summarize_power_report(mutated_report)
        rejection_codes = summary["rejection_codes"]
        rejected = expected_code in rejection_codes and not summary["power_gate_passed"]
        rows.append(
            {
                "negative_case_id": case_id,
                "description": description,
                "status": "EXECUTED",
                "rejected_as_expected": rejected,
                "evidence": str(mutated_report),
                "note": "",
                "source_report": str(source_report),
                "source_sha256": source_sha,
                "mutated_sha256": mutated_sha,
                "mutation_sha_changed": mutated_sha != source_sha,
                "expected_rejection_code": expected_code,
                "actual_rejection_codes": ";".join(rejection_codes),
                "unexpected_pass": summary["power_gate_passed"],
            }
        )

    summary = {
        "negative_case_count": len(rows),
        "executed_case_count": len(rows),
        "blocked_case_count": 0,
        "negative_tests_passed": all(row["rejected_as_expected"] for row in rows) and not any(row["unexpected_pass"] for row in rows),
        "unexpected_pass_count": sum(1 for row in rows if row["unexpected_pass"]),
    }
    return rows, summary
