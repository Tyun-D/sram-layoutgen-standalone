"""Read-only OpenYield decoder output-specific contract audit helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .decoder_truth_table_binding import build_decoder_truth_table_binding_report
from .decoder_stage_candidates import md_table


def build_decoder_output_contract_report(
    openyield_root: str | Path,
    tech_dir: str | Path,
    addr_width: int = 5,
    internal_gap: float = 0.2,
    contracts_path: str | Path | None = None,
    gds_pin_report_path: str | Path | None = None,
    decomposition_report_path: str | Path | None = None,
    target_envelope_report_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    binding_report, _graph = build_decoder_truth_table_binding_report(
        openyield_root=openyield_root,
        tech_dir=tech_dir,
        addr_width=addr_width,
        internal_gap=internal_gap,
        contracts_path=contracts_path,
        gds_pin_report_path=gds_pin_report_path,
        decomposition_report_path=decomposition_report_path,
        target_envelope_report_path=target_envelope_report_path,
    )

    generic_rows = binding_report["generic_decoder3_8_truth_table"]
    output_contracts: list[dict[str, Any]] = []
    stage_output_region = {"x0": 24.0, "y0": 0.0, "x1": 27.0, "y1": 1.48}
    slice_width = (stage_output_region["x1"] - stage_output_region["x0"]) / 8.0
    for row in generic_rows:
        i = int(row["output_index"])
        selected = {
            "A0_term": "A0" if row["input_polarity_terms"]["A0"] else "A0_bar",
            "A1_term": "A1" if row["input_polarity_terms"]["A1"] else "A1_bar",
            "A2_term": "A2" if row["input_polarity_terms"]["A2"] else "A2_bar",
        }
        internal_nets = [
            f"wl{i}_and3_ab_n",
            f"wl{i}_and3_ab",
            f"wl{i}_and3_abc_n",
            f"wl{i}_and2_ab_n",
            f"wl{i}_and2_ab",
        ]
        subzone = {
            "zone_name": f"OUTPUT_CONTRACT_ZONE_WL{i}",
            "local_output_slot": row["output_slot"],
            "purpose": "reserve_output_specific_leaf_and_internal_nets",
            "reserved_input_terms": selected,
            "reserved_internal_nets": internal_nets,
            "reserved_output_net": row["output_net"],
            "x0": round(stage_output_region["x0"] + slice_width * i, 6),
            "y0": stage_output_region["y0"],
            "x1": round(stage_output_region["x0"] + slice_width * (i + 1), 6),
            "y1": stage_output_region["y1"],
            "subzone_policy": "divide_stage_output_region_by_8",
            "metadata_only": True,
            "subzone_is_metadata_only": True,
            "subzone_not_physical_layout": True,
            "physical_routing_proven": False,
            "overlap_policy": "disjoint_output_slice",
        }
        handoff = {
            "local_output_slot": row["output_slot"],
            "stage_role": "wordline_outputs_or_intermediate_enable_bus",
            "local_output_net": row["output_net"],
            "global_output_net_template": "WL[8*stage_index + local_output_index] or EN_0_0_i",
            "downstream_consumer": "WORDLINEDRIVER or DECODER_LEVEL1_STAGE.EN",
            "consumer_pin": "A or EN",
            "handoff_anchor": "WORDLINE_DRIVER_INPUT_HANDOFF_ANCHOR or ENABLE_BUS_ANCHOR",
            "handoff_window": "metadata_only_output_slice",
            "physical_routing_proven": False,
        }
        output_contracts.append(
            {
                "contract_name": f"DECODER3_8_OUTPUT_CONTRACT_WL{i}",
                "local_output_slot": row["output_slot"],
                "local_output_index": i,
                "polarity_terms": row["input_polarity_terms"],
                "required_inverted_nets": row["required_inverted_nets"],
                "raw_input_nets": ["A0", "A1", "A2"],
                "available_inverted_nets": ["A0_bar", "A1_bar", "A2_bar"],
                "selected_input_nets": selected,
                "and3_leaf_slot": row["and3_leaf_slot"],
                "and2_leaf_slot": row["and2_leaf_slot"],
                "composite_leaf_convention": row["composite_leaf_convention"],
                "internal_nets": internal_nets,
                "reservation_subzone": subzone,
                "output_handoff": handoff,
                "metadata_only": True,
                "physical_routing_proven": False,
                "safe_for_metadata_planning": True,
                "safe_for_physical_placement": False,
                "notes": [row["source_evidence"]],
            }
        )

    level0_expansion = {
        f"DEC_0_0.WL{i}": f"EN_0_0_{i}" for i in range(8)
    }
    level1_expansion = []
    for stage in binding_report["level1_binding"]:
        stage_name = stage["stage_name"]
        for local_slot, global_wl in stage["local_output_slot_to_global_wl_map"].items():
            level1_expansion.append(
                {
                    "stage_name": stage_name,
                    "local_output_slot": local_slot,
                    "global_wordline": global_wl,
                }
            )

    consistency = {
        "truth_table_binding_complete": binding_report["truth_table_binding_complete"],
        "output_contracts_available": len(output_contracts) == 8,
        "all_local_outputs_have_contract": len(output_contracts) == 8,
        "all_level0_outputs_have_expansion": len(level0_expansion) == 8,
        "all_level1_outputs_have_expansion": len(level1_expansion) == 32,
        "enable_bus_handoff_consistent": binding_report["handoff_consistency"]["level_enable_handoff_consistent"],
        "wordline_output_handoff_consistent": binding_report["handoff_consistency"]["output_handoff_consistent"],
        "slot_binding_consistent": binding_report["slot_level_contract"]["slot_binding_available"],
        "reservation_subzones_available": len(output_contracts) == 8,
        "physical_routing_proven": False,
    }

    report = {
        "scope": "step6_15_openyield_decoder_output_contract_audit",
        "decoder_output_contracts_available": True,
        "generic_output_contracts": output_contracts,
        "level0_output_expansion": {
            "mapping": level0_expansion,
            "downstream_consumed_enable_outputs": binding_report["level0_binding"]["downstream_consumed_enable_outputs"],
            "unused_or_unconsumed_enable_outputs": binding_report["level0_binding"]["unused_or_unconsumed_enable_outputs"],
        },
        "level1_output_expansion": level1_expansion,
        "enable_bus_handoff": {
            f"DEC_0_0.EN_0_0_{i}": f"DEC_1_{i}.EN" for i in range(4)
        },
        "wordline_output_handoff": {
            "downstream_consumer": "WORDLINEDRIVER",
            "consumer_pin": "A",
            "handoff_anchor": "WORDLINE_DRIVER_INPUT_HANDOFF_ANCHOR",
            "physical_routing_proven": False,
        },
        "consistency_checks": consistency,
        "can_enter_decoder_generated_block_planning": True,
        "can_enter_physical_decoder_placement": False,
        "can_enter_very_limited_control_row_smoke": False,
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "blocker_list": [
            "Output-specific contracts are metadata-only and do not prove route completion.",
            "Reservation subzones are planning partitions, not legal physical layout regions.",
            "Physical decoder placement and control-row smoke remain blocked.",
        ],
        "step_6_16_recommendation": "Refine decoder output handoff windows next: split wordline-driver-side consumers into per-output access targets and add output-to-consumer budget metadata.",
    }

    graph = {
        "scope": report["scope"],
        "nodes": [{"id": item["contract_name"], "kind": "output_contract"} for item in output_contracts],
        "edges": [
            {"source": item["and3_leaf_slot"], "target": item["contract_name"], "relation": "binds_logic"}
            for item in output_contracts
        ] + [
            {"source": item["and2_leaf_slot"], "target": item["contract_name"], "relation": "binds_enable_gate"}
            for item in output_contracts
        ],
        "consistency_checks": consistency,
        "blockers": report["blocker_list"],
    }
    return report, graph


def build_decoder_output_contract_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Decoder Output Contract Audit",
        "",
        "This is a metadata-only audit for decoder output-specific contracts. It does not modify placement, routing, standalone.py, or the GDS writer.",
        "",
        "## Summary",
        "",
        f"- decoder_output_contracts_available: `{report['decoder_output_contracts_available']}`",
        f"- can_enter_decoder_generated_block_planning: `{report['can_enter_decoder_generated_block_planning']}`",
        f"- can_enter_physical_decoder_placement: `{report['can_enter_physical_decoder_placement']}`",
        f"- can_enter_very_limited_control_row_smoke: `{report['can_enter_very_limited_control_row_smoke']}`",
        "",
        "## Generic Output Contracts",
        "",
        md_table(
            ["contract", "slot", "polarity", "selected_input_nets", "and3_slot", "and2_slot", "internal_nets", "subzone"],
            [
                [
                    item["contract_name"],
                    item["local_output_slot"],
                    json.dumps(item["polarity_terms"], ensure_ascii=False),
                    json.dumps(item["selected_input_nets"], ensure_ascii=False),
                    item["and3_leaf_slot"],
                    item["and2_leaf_slot"],
                    ", ".join(item["internal_nets"]),
                    item["reservation_subzone"]["zone_name"],
                ]
                for item in report["generic_output_contracts"]
            ],
        ),
        "",
        "## Level 0 Output Expansion",
        "",
        "```json",
        json.dumps(report["level0_output_expansion"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Level 1 Output Expansion",
        "",
        "```json",
        json.dumps(report["level1_output_expansion"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Consistency Checks",
        "",
        "```json",
        json.dumps(report["consistency_checks"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Blockers",
        "",
        *[f"- {item}" for item in report["blocker_list"]],
        "",
        "## Step 6.16 Recommendation",
        "",
        f"- {report['step_6_16_recommendation']}",
        "",
    ]
    return "\n".join(lines)


def write_decoder_output_contract_reports(
    openyield_root: str | Path,
    tech_dir: str | Path,
    addr_width: int,
    out_json: str | Path,
    out_md: str | Path,
    out_graph: str | Path,
    internal_gap: float = 0.2,
    contracts_path: str | Path | None = None,
    gds_pin_report_path: str | Path | None = None,
    decomposition_report_path: str | Path | None = None,
    target_envelope_report_path: str | Path | None = None,
) -> dict[str, Any]:
    report, graph = build_decoder_output_contract_report(
        openyield_root=openyield_root,
        tech_dir=tech_dir,
        addr_width=addr_width,
        internal_gap=internal_gap,
        contracts_path=contracts_path,
        gds_pin_report_path=gds_pin_report_path,
        decomposition_report_path=decomposition_report_path,
        target_envelope_report_path=target_envelope_report_path,
    )
    out_json = Path(out_json)
    out_md = Path(out_md)
    out_graph = Path(out_graph)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_graph.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(build_decoder_output_contract_markdown(report), encoding="utf-8")
    out_graph.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report
