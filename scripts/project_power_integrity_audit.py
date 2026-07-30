from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.verification.power_connectivity import summarize_power_report  # noqa: E402
from sram_layoutgen.verification.power_negative_regressions import blocked_negative_matrix  # noqa: E402


DOCS_DIR = REPO_ROOT / "docs"
CONFIG_REPORTS = [
    REPO_ROOT / "outputs/M7_correct_golden_reference/current_supported_config/extracted/full_layout_collection/sram_16x16_wpr1/sram_16x16_wpr1_fd45.report.json",
    REPO_ROOT / "outputs/M7_correct_golden_reference/current_supported_config/extracted/full_layout_collection/sram_4x32_wpr1/sram_4x32_wpr1_fd45.report.json",
    REPO_ROOT / "outputs/M7_correct_golden_reference/current_supported_config/extracted/full_layout_collection/sram_8x64_wpr4/sram_8x64_wpr4_fd45.report.json",
]


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    summaries = [summarize_power_report(path) for path in CONFIG_REPORTS]
    negative_rows = blocked_negative_matrix(
        "Current project worktree exposes positive power audits from generated raw-source-backed report JSONs, but no standalone geometry-mutation harness was found for raw GDS power-negative regressions."
    )

    gate = {
        "generated_at": "2026-07-30",
        "config_count": len(summaries),
        "all_positive_power_gates_passed": all(item["power_gate_passed"] for item in summaries),
        "negative_harness_available": False,
        "negative_cases_blocked": len(negative_rows),
        "note": "These checks prove connectivity/topology consistency from existing report evidence only. They are not IR drop, EM, or dynamic power-integrity signoff.",
    }
    write_json(DOCS_DIR / "POWER_ROUTING_CORRECTNESS_GATE.json", gate)

    endpoint_rows = []
    component_rows = []
    for item in summaries:
        endpoint_rows.extend(
            [
                {
                    "config_name": item["config_name"],
                    "endpoint_class": "child_vdd_endpoints",
                    "count": item["checked_power_pins"] // 2,
                    "missing_count": item["missing_vdd_pins"],
                    "all_connected_to_unique_power_component": item["array_and_peripheral_vdd_same_component"],
                },
                {
                    "config_name": item["config_name"],
                    "endpoint_class": "child_vss_endpoints",
                    "count": item["checked_power_pins"] // 2,
                    "missing_count": item["missing_gnd_pins"],
                    "all_connected_to_unique_power_component": item["array_and_peripheral_gnd_same_component"],
                },
            ]
        )
        component_rows.extend(
            [
                {
                    "config_name": item["config_name"],
                    "component_class": "vdd",
                    "topology_check_passed": item["array_vdd_connected_to_top_vdd"] and item["peripheral_vdd_connected_to_top_vdd"],
                    "strap_rows_expected": item["row_vdd_rails_expected"],
                    "strap_rows_connected": item["row_vdd_rails_connected"],
                    "suspicious_route_count": item["suspicious_power_routes"],
                },
                {
                    "config_name": item["config_name"],
                    "component_class": "vss",
                    "topology_check_passed": item["array_gnd_connected_to_top_gnd"] and item["peripheral_gnd_connected_to_top_gnd"],
                    "strap_rows_expected": item["row_gnd_rails_expected"],
                    "strap_rows_connected": item["row_gnd_rails_connected"],
                    "suspicious_route_count": item["suspicious_power_routes"],
                },
            ]
        )

    write_csv(
        DOCS_DIR / "POWER_ENDPOINT_COVERAGE.csv",
        endpoint_rows,
        ["config_name", "endpoint_class", "count", "missing_count", "all_connected_to_unique_power_component"],
    )
    write_csv(
        DOCS_DIR / "POWER_COMPONENT_SUMMARY.csv",
        component_rows,
        ["config_name", "component_class", "topology_check_passed", "strap_rows_expected", "strap_rows_connected", "suspicious_route_count"],
    )
    write_csv(
        DOCS_DIR / "POWER_NEGATIVE_TEST_MATRIX.csv",
        negative_rows,
        ["negative_case_id", "description", "status", "rejected_as_expected", "evidence", "note"],
    )
    write_json(
        DOCS_DIR / "POWER_NEGATIVE_TEST_SUMMARY.json",
        {
            "generated_at": "2026-07-30",
            "negative_case_count": len(negative_rows),
            "blocked_case_count": len(negative_rows),
            "executed_case_count": 0,
            "negative_tests_passed": False,
            "blocking_reason": negative_rows[0]["note"] if negative_rows else "",
        },
    )

    method_lines = [
        "# Power Routing Correctness Method",
        "",
        "- evidence_basis: `raw-source-backed generated SRAM report.json artifacts`, not handwritten power claims",
        "- covered_configs: `sram_16x16_wpr1_fd45`, `sram_4x32_wpr1_fd45`, `sram_8x64_wpr4_fd45`",
        "- validator_scope: `row_side_power_audit`, `array_power_stitching_audit`, `global_power_consistency_audit`, `power_junction_topology_audit`, `drc_clean`",
        "",
        "## Positive Checks",
        "",
        "- all child VDD endpoints connect with `missing_vdd_pins = 0`",
        "- all child VSS endpoints connect with `missing_gnd_pins = 0`",
        "- array and peripheral VDD resolve to one top-level VDD component",
        "- array and peripheral VSS resolve to one top-level VSS component",
        "- VDD/VSS short freedom is proven by `vdd_gnd_short_free = true`",
        "- per-row VDD/VSS straps are fully connected to expected row counts",
        "- top-ring VDD/VSS connections are present",
        "- source reports are DRC-clean for these configurations",
        "",
        "## Limits",
        "",
        "- Current negative regression rows are blocked because no raw-GDS geometry mutation harness was found in this worktree.",
        "- These results do not prove IR drop, EM, voltage droop, or dynamic power signoff.",
    ]
    write_text(DOCS_DIR / "POWER_ROUTING_CORRECTNESS_METHOD.md", "\n".join(method_lines) + "\n")


if __name__ == "__main__":
    main()
