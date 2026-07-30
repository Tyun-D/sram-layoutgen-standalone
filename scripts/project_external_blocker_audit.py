#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import read_top_cell

DOCS = REPO_ROOT / "docs"


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def decoder_child_pin_authority_audit() -> dict[str, object]:
    contract = read_json(DOCS / "DECODER_REBUILD_CONTRACT_LOCK.json")
    expected_inputs = {
        "decoder_gate_cells": ["A_dff[*]", "enable"],
        "row_decoder": ["A_dff[*]", "enable"],
        "wordline_decoder": ["A_dff[*]", "enable"],
    }
    expected_outputs = {
        "decoder_gate_cells": ["dec_stage[*]"],
        "row_decoder": ["dec_out[*]"],
        "wordline_decoder": ["DEC_WL[*]"],
    }
    rows: list[dict[str, object]] = []
    module_summary = []
    contract_manifest = {"modules": []}
    for child in contract["child_assets"]:
        module = child["module"]
        gds_path = Path(child["gds_path"])
        pins = read_json(Path(child["pin_map_path"]))["pins"]
        generator_manifest = read_json(Path(child["generator_manifest_path"]))
        generation_report = read_json(gds_path.parent / "generation_report.json")
        _, top = read_top_cell(gds_path, child["root_cell_name"])
        label_count = len(top.labels)
        module_rows = []
        for pin in pins:
            name = str(pin["name"])
            is_bus = "[*]" in name
            expected_net = ""
            if name in {"VDD", "GND", "VSS"}:
                expected_net = "top_power_rail"
            elif name == "enable":
                expected_net = "decoder_enable_chain"
            elif is_bus:
                if name.startswith("A"):
                    expected_net = ",".join(expected_inputs[module])
                else:
                    expected_net = ",".join(expected_outputs[module])
            resolution = (
                "AMBIGUOUS_REQUIRES_NEW_ASSET_CONTRACT"
                if is_bus or label_count == 0
                else "GEOMETRY_RESOLVED_WITH_AUTHORITY"
            )
            confidence = "LOW" if resolution == "AMBIGUOUS_REQUIRES_NEW_ASSET_CONTRACT" else "MEDIUM"
            row = {
                "instance": module,
                "logical_child_type": module,
                "logical_pin": name,
                "expected_parent_net": expected_net,
                "physical_asset_path": str(gds_path),
                "physical_asset_sha256": child["gds_sha256"],
                "top_cell_name": child["root_cell_name"],
                "physical_pin_label": name if not is_bus else "",
                "physical_pin_layer": pin["layer"],
                "physical_pin_datatype": 0,
                "physical_pin_bbox": f"[{pin['x']}, {pin['y']}, {pin['x']}, {pin['y']}]",
                "pin_authority_source": pin["pin_source"],
                "gds_top_label_count": label_count,
                "mapping_confidence": confidence,
                "resolution": resolution,
            }
            rows.append(row)
            module_rows.append(row)
        module_summary.append(
            {
                "module": module,
                "gds_sha256": child["gds_sha256"],
                "gds_top_label_count": label_count,
                "generation_status": generation_report["generation_status"],
                "not_drc_clean_claimed": generation_report["not_DRC_clean_claimed"],
                "pin_limitations": generator_manifest["limitations"],
                "all_bus_pins_require_new_contract": all("[*]" in str(p["logical_pin"]) or p["resolution"] == "AMBIGUOUS_REQUIRES_NEW_ASSET_CONTRACT" for p in module_rows),
            }
        )
        contract_manifest["modules"].append(
            {
                "module": module,
                "gds_path": str(gds_path),
                "gds_sha256": child["gds_sha256"],
                "pins_json_path": child["pin_map_path"],
                "generator_manifest_path": child["generator_manifest_path"],
                "formal_scalar_pins": [r["logical_pin"] for r in module_rows if r["resolution"] != "AMBIGUOUS_REQUIRES_NEW_ASSET_CONTRACT"],
                "bus_pins_requiring_new_contract": [r["logical_pin"] for r in module_rows if r["resolution"] == "AMBIGUOUS_REQUIRES_NEW_ASSET_CONTRACT"],
            }
        )
    fieldnames = list(rows[0].keys())
    write_csv(DOCS / "DECODER_CHILD_PIN_AUTHORITY_MATRIX.csv", fieldnames, rows)
    payload = {
        "scope": "decoder_child_pin_authority_audit",
        "decoder_top_status": "BLOCKED_BY_CHILD_PIN_AUTHORITY",
        "source_contract_path": str((DOCS / "DECODER_REBUILD_CONTRACT_LOCK.json").resolve()),
        "module_summary": module_summary,
        "rows": rows,
        "blocking_conclusion": [
            "All current decoder child bus handoff pins remain wildcard contracts rather than bit-exact physical authorities.",
            "Current child top cells expose zero native GDS text labels, so bit-exact WL/input handoff cannot be promoted from GDS labels.",
            "Current child generation manifests explicitly describe semantic boundary pin exports on candidate geometry and explicitly do not claim final routing/signoff.",
        ],
    }
    write_json(DOCS / "DECODER_CHILD_PIN_AUTHORITY_AUDIT.json", payload)
    write_json(REPO_ROOT / "outputs/PROJECT_decoder_rebuild/current_supported_config/DECODER_CHILD_PIN_CONTRACT.json", contract_manifest)
    lines = [
        "# Decoder Child Pin Authority Audit",
        "",
        "## Conclusion",
        "",
        "- Current decoder child assets are sufficient for executable candidate rebuilds, but not for bit-exact production handoff.",
        "- Every bus handoff remains wildcard-only in the locked child manifests.",
        "- Every audited child top cell has `gds_top_label_count = 0`.",
        "- Each child generation report explicitly says `L3_GDS_GENERATED_CANDIDATE_GEOMETRY` and `not_DRC_clean_claimed = true`.",
        "",
        "## Blocking Detail",
        "",
        "- `A[*]`, `dec_out[*]`, `DEC_WL[*]`, and `dec_stage[*]` remain `AMBIGUOUS_REQUIRES_NEW_ASSET_CONTRACT`.",
        "- The present `pins.json` files are semantic/contract exports (`pin_source = composition_contract_and_base_leaf_pin_map`) rather than extracted native GDS pin labels.",
        "- Under the current project rules, these wildcard exports cannot be upgraded to formal bit-exact decoder authority without a new child pin contract bound to exact physical shapes.",
        "",
        "## Module Summary",
        "",
    ]
    for item in module_summary:
        lines.extend(
            [
                f"- `{item['module']}`: `gds_top_label_count={item['gds_top_label_count']}`, `generation_status={item['generation_status']}`, `not_drc_clean_claimed={item['not_drc_clean_claimed']}`",
            ]
        )
    lines.append("")
    write_text(DOCS / "DECODER_CHILD_PIN_AUTHORITY_AUDIT.md", "\n".join(lines))
    return payload


def decoder_drc_summary() -> dict[str, object]:
    gate = read_json(REPO_ROOT / "outputs/PROJECT_decoder_rebuild/current_supported_config/DECODER_MACHINE_GATE.json")
    generation_reports = {
        module: read_json(REPO_ROOT / "outputs/openyield_module_gds" / module / "generation_report.json")
        for module in ("decoder_gate_cells", "row_decoder", "wordline_decoder")
    }
    categories = gate["drc"]["marker_categories"]
    rows = [
        {"rule": rule.strip("'"), "count": count}
        for rule, count in sorted(categories.items(), key=lambda item: (-item[1], item[0]))
    ]
    write_csv(DOCS / "DECODER_DRC_RULE_SUMMARY.csv", ["rule", "count"], rows)
    root_cause = {
        "scope": "decoder_drc_root_cause",
        "top_gds_sha256": "bda075700fd8c5b7b7b26955830b7210aad2be3843e0ff6d2dbb768cd5ed8026",
        "top_marker_count": gate["drc"]["marker_count"],
        "dominant_rule_families": rows[:8],
        "child_generation_status": {
            module: {
                "generation_status": report["generation_status"],
                "not_drc_clean_claimed": report["not_DRC_clean_claimed"],
            }
            for module, report in generation_reports.items()
        },
        "root_cause_conclusion": [
            "The 2663-marker explosion is dominated by grid violations plus contact/metal/poly/well template violations, not by a small number of route-end shorts.",
            "All three imported decoder children are candidate geometry modules that explicitly do not claim DRC-clean status.",
            "Under the current rules, top-level decoder DRC cannot be driven to 0 without either replacing these child candidates with new approved assets or generating new approved child pin/geometry contracts.",
        ],
    }
    write_json(DOCS / "DECODER_DRC_GEOMETRY_CLUSTERS.json", root_cause)
    write_text(
        DOCS / "DECODER_DRC_ROOT_CAUSE.md",
        "\n".join(
            [
                "# Decoder DRC Root Cause",
                "",
                f"- fresh decoder rebuild marker_count: `{gate['drc']['marker_count']}`",
                "- Dominant rules are systemic grid/contact/template violations rather than a handful of isolated parent routes.",
                "- Current decoder children are L3 candidate geometry with `not_DRC_clean_claimed = true` in their own generation reports.",
                "- Because child internals are not approved hard-macro signoff assets, the project cannot legitimately claim decoder top DRC closure without new child-level authority.",
                "",
                "## Dominant Rule Families",
                "",
                *[f"- `{row['rule']}`: `{row['count']}`" for row in rows[:10]],
                "",
            ]
        ),
    )
    return root_cause


def project_sram_timing_oracle() -> dict[str, object]:
    top_spice = REPO_ROOT / "outputs/M12N2_clean_openyield_sram_top/current_supported_config/openyield_sram_top_v1_16x16.sp"
    upstream_tb = Path("/data1/qujh/work/external/OpenYield/sram_compiler/testbenches/sram_6t_core_testbench.py")
    fields = [
        {
            "field": "TIME_schedule",
            "status": "UNRESOLVED",
            "source": f"{upstream_tb}: create_testbench pulse sources + add_cs_startup_clamp",
            "exact_statement_or_relation": "ADDR/DIN pulses start at 1.0ns+0.1*T, CLK rises at 1.0ns+0.2*T, CSB is also pulsed, but add_cs_startup_clamp forces cs/cs_bar startup behavior until 1.0ns+0.2*T+2*t_rise.",
            "confidence": "HIGH",
            "compatibility_with_current_top": "The exact first valid functional cycle is not frozen because startup clamp behavior overlaps the first control pulses.",
        },
        {
            "field": "write_sample_point",
            "status": "UNRESOLVED",
            "source": f"{upstream_tb}: write-mode .measure statements + {top_spice.name}",
            "exact_statement_or_relation": "Upstream write validation measures internal target-cell Q/QB crossings after WL rise; current project top exports SA_Q/SA_QB but not the target-cell Q/QB oracle used by the upstream write measurement.",
            "confidence": "HIGH",
            "compatibility_with_current_top": "No exact exported-top relation currently binds a successful internal write to a project-owned readback sample point.",
        },
        {
            "field": "disabled_hold_semantics",
            "status": "UNRESOLVED",
            "source": f"{upstream_tb}: hold_snm/read_snm/write_snm single-cell branches",
            "exact_statement_or_relation": "Upstream 'hold' evidence exists only as SNM/DC single-cell setup, not as a transient top-level functional disabled/hold contract for OPENYIELD_SRAM_TOP_V1.",
            "confidence": "HIGH",
            "compatibility_with_current_top": "Current top-level functional interface does not freeze a reusable disabled-hold waveform oracle.",
        },
    ]
    write_csv(
        DOCS / "PROJECT_SRAM_TIMING_ORACLE_EVIDENCE.csv",
        list(fields[0].keys()),
        fields,
    )
    payload = {
        "scope": "project_sram_timing_oracle",
        "dut_subckt": "OPENYIELD_SRAM_TOP_V1",
        "top_netlist_path": str(top_spice.resolve()),
        "upstream_reference_testbench": str(upstream_tb),
        "fields": fields,
        "oracle_status": "BLOCKED_BY_EXACT_SOURCE_GAPS",
        "closing_rule": "Only UPSTREAM_EXACT, CURRENT_SOURCE_EXACT, or DERIVED_FROM_EXACT_RELATIONS are allowed.",
        "blocked_reason": [
            "The exact first valid functional cycle remains ambiguous because the startup clamp overlaps the first nominal control cycle.",
            "The upstream write oracle targets internal storage nodes that the current project top does not export as a reviewed pass/fail interface.",
            "No top-level transient disabled-hold contract exists; only single-cell SNM hold exists upstream.",
        ],
    }
    write_json(DOCS / "PROJECT_SRAM_TIMING_ORACLE.json", payload)
    write_text(
        DOCS / "PROJECT_SRAM_TIMING_ORACLE.md",
        "\n".join(
            [
                "# Project SRAM Timing Oracle",
                "",
                "## Status",
                "",
                "- oracle_status: `BLOCKED_BY_EXACT_SOURCE_GAPS`",
                "- allowed derivation policy: `UPSTREAM_EXACT | CURRENT_SOURCE_EXACT | DERIVED_FROM_EXACT_RELATIONS`",
                "",
                "## Blocking Fields",
                "",
                "- `TIME_schedule`: startup clamp overlaps the first nominal functional cycle, so the first valid cycle is not frozen by exact source text alone.",
                "- `write_sample_point`: upstream write proof measures internal storage-node Q/QB, while the current top-level interface exposes SA outputs instead.",
                "- `disabled_hold_semantics`: upstream hold evidence is single-cell SNM/DC, not top-level transient hold behavior.",
                "",
            ]
        ),
    )
    return payload


def main() -> int:
    decoder_child_pin_authority_audit()
    decoder_drc_summary()
    project_sram_timing_oracle()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
