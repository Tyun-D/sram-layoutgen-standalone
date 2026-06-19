"""Read-only OpenYield decoder truth-table binding audit helpers."""

from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

from .decoder_stage_candidates import build_decoder_stage_candidate_report, md_table, _notes_text
from .decoder_stage_templates import build_decoder_stage_template_report


def build_decoder_truth_table_binding_report(
    openyield_root: str | Path,
    tech_dir: str | Path,
    addr_width: int = 5,
    internal_gap: float = 0.2,
    contracts_path: str | Path | None = None,
    gds_pin_report_path: str | Path | None = None,
    decomposition_report_path: str | Path | None = None,
    target_envelope_report_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    cwd = Path.cwd()
    contracts_path = contracts_path or cwd / "docs/openyield_module_contracts.json"
    gds_pin_report_path = gds_pin_report_path or cwd / "docs/openyield_gds_pin_audit_report.json"
    decomposition_report_path = decomposition_report_path or cwd / "docs/openyield_time_control_decomposition_report.json"
    target_envelope_report_path = target_envelope_report_path or cwd / "docs/openyield_control_target_envelope_report.json"

    template_report, _template_graph = build_decoder_stage_template_report(
        openyield_root=openyield_root,
        tech_dir=tech_dir,
        addr_width=addr_width,
        internal_gap=internal_gap,
        contracts_path=contracts_path,
        gds_pin_report_path=gds_pin_report_path,
        decomposition_report_path=decomposition_report_path,
        target_envelope_report_path=target_envelope_report_path,
    )
    candidate_report, _candidate_graph = build_decoder_stage_candidate_report(
        openyield_root=openyield_root,
        contracts_path=contracts_path,
        tech_dir=tech_dir,
        addr_width=addr_width,
        num_rows=None,
        gds_pin_report_path=gds_pin_report_path,
        decomposition_report_path=decomposition_report_path,
        target_envelope_report_path=target_envelope_report_path,
    )

    decoder_py = Path(openyield_root) / "sram_compiler/subcircuits/decoder.py"
    decoder_source = decoder_py.read_text(encoding="utf-8", errors="replace")
    combinations = _parse_input_combinations(decoder_source)
    truth_table_auto_parse_success = combinations is not None
    manual_source_review_required = not truth_table_auto_parse_success

    generic_truth_table: list[dict[str, Any]] = []
    if truth_table_auto_parse_success and combinations is not None:
        for idx, combo in enumerate(combinations):
            polarity = {
                "A0": combo[0] == "A0",
                "A1": combo[1] == "A1",
                "A2": combo[2] == "A2",
            }
            inverted = [f"{name}_bar" for name, active_high in polarity.items() if not active_high]
            generic_truth_table.append(
                {
                    "output_slot": f"WL{idx}",
                    "output_index": idx,
                    "output_net": f"WL{idx}",
                    "enable_required": "EN",
                    "input_polarity_terms": polarity,
                    "uses_inverted_inputs": bool(inverted),
                    "required_inverted_nets": inverted,
                    "and3_leaf_slot": f"Xdec_and3_wl{idx}",
                    "and2_leaf_slot": f"Xdec_and2_wl{idx}",
                    "composite_leaf_convention": "AND3_COMPOSITE_NAND2_INV",
                    "source_evidence": f"decoder.py input_combinations[{idx}] = {combo}",
                    "metadata_only": True,
                    "physical_routing_proven": False,
                }
            )

    stage_instances = candidate_report["decoder_cascade_hierarchy"]["stage_instances"]
    level0 = next(item for item in stage_instances if item["level"] == 0)
    level1 = [item for item in stage_instances if item["level"] == 1]

    level0_binding = {
        "level0_truth_binding": truth_table_auto_parse_success,
        "level0_stage_name": level0["stage_name"],
        "local_slot_to_global_net_map": {
            "EN": level0["decoder_pin_map"]["EN"],
            "A0": level0["decoder_pin_map"]["A0"],
            "A1": level0["decoder_pin_map"]["A1"],
            "A2": level0["decoder_pin_map"]["A2"],
        },
        "stage_local_output_to_enable_bus_map": {
            f"WL{i}": level0["output_nets"][i] for i in range(len(level0["output_nets"]))
        },
        "downstream_consumed_enable_outputs": list(level0["output_nets"][:4]),
        "unused_or_unconsumed_enable_outputs": list(level0["output_nets"][4:]),
        "metadata_only": True,
        "physical_routing_proven": False,
    }

    level1_binding = []
    global_map = []
    for stage_index, item in enumerate(level1):
        local_output_map = {
            f"WL{i}": item["output_nets"][i] for i in range(len(item["output_nets"]))
        }
        global_map.extend(
            {
                "stage_name": item["stage_name"],
                "local_output_slot": f"WL{i}",
                "global_wordline": item["output_nets"][i],
            }
            for i in range(len(item["output_nets"]))
        )
        truth_rows = []
        for i, row in enumerate(generic_truth_table):
            truth_rows.append(
                {
                    "local_output_slot": row["output_slot"],
                    "global_wordline": item["output_nets"][i],
                    "input_polarity_terms": row["input_polarity_terms"],
                    "required_inverted_nets": row["required_inverted_nets"],
                    "and3_leaf_slot": row["and3_leaf_slot"],
                    "and2_leaf_slot": row["and2_leaf_slot"],
                }
            )
        level1_binding.append(
            {
                "stage_name": item["stage_name"],
                "stage_index": stage_index,
                "enable_net": item["enable_net"],
                "local_slot_to_global_net_map": {
                    "EN": item["decoder_pin_map"]["EN"],
                    "A0": item["decoder_pin_map"]["A0"],
                    "A1": item["decoder_pin_map"]["A1"],
                    "A2": item["decoder_pin_map"]["A2"],
                },
                "local_output_slot_to_global_wl_map": local_output_map,
                "truth_table_rows": truth_rows,
                "metadata_only": True,
                "physical_routing_proven": False,
            }
        )

    slot_level_contract = {
        "slot_binding_available": truth_table_auto_parse_success,
        "input_inversion_slot_binding_available": truth_table_auto_parse_success,
        "output_leaf_slot_binding_available": truth_table_auto_parse_success,
        "enable_distribution_binding_available": True,
        "truth_table_binding_complete": truth_table_auto_parse_success,
        "requires_decoder_truth_table_binding": not truth_table_auto_parse_success,
    }

    handoff = {
        "input_handoff_consistent": candidate_report["input_handoff"]["sink"] == "DECODER_CASCADE.A[i]",
        "level_enable_handoff_consistent": all(
            level0["output_nets"][i] == level1[i]["enable_net"] for i in range(min(4, len(level1)))
        ),
        "output_handoff_consistent": candidate_report["output_handoff"]["sink"] == "WORDLINEDRIVER.A[row]",
        "wordline_driver_semantics_confirmed": candidate_report["output_handoff"]["wordline_driver_semantics_confirmed"],
        "physical_routing_proven": False,
    }

    report = {
        "scope": "step6_14_openyield_decoder_truth_table_binding_audit",
        "truth_table_auto_parse_success": truth_table_auto_parse_success,
        "manual_source_review_required": manual_source_review_required,
        "decoder_truth_table_binding_available": truth_table_auto_parse_success,
        "generic_decoder3_8_truth_table": generic_truth_table,
        "level0_binding": level0_binding,
        "level1_binding": level1_binding,
        "global_wordline_mapping": global_map,
        "enable_bus_mapping": {
            f"DEC_0_0.EN_0_0_{i}": f"DEC_1_{i}.EN" for i in range(4)
        },
        "slot_level_contract": slot_level_contract,
        "handoff_consistency": handoff,
        "truth_table_binding_complete": truth_table_auto_parse_success,
        "requires_decoder_truth_table_binding": not truth_table_auto_parse_success,
        "can_enter_decoder_generated_block_planning": True,
        "can_enter_physical_decoder_placement": False,
        "can_enter_very_limited_control_row_smoke": False,
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "blocker_list": [
            "Truth-table binding is metadata-only and does not prove physical routing.",
            "Per-slot physical access, internal routing, and rail continuity remain unproven.",
            "Decoder placement and control-row smoke remain blocked even after output binding.",
        ] if truth_table_auto_parse_success else [
            "decoder.py truth table could not be safely parsed automatically.",
            "Manual source review is required before output-slot binding can be claimed complete.",
            "Physical decoder placement and control-row smoke remain blocked.",
        ],
        "step_6_15_recommendation": "Audit output-specific decoder contracts next: bind each WL slot to explicit input-bar usage, output handoff metadata, and per-output reservation subzones before any placement-oriented prototype.",
    }

    graph = {
        "scope": report["scope"],
        "nodes": [{"id": row["output_slot"], "kind": "output_slot"} for row in generic_truth_table],
        "edges": [
            {"source": row["and3_leaf_slot"], "target": row["output_slot"], "relation": "drives_pre_enable"}
            for row in generic_truth_table
        ] + [
            {"source": row["and2_leaf_slot"], "target": row["output_slot"], "relation": "gates_with_enable"}
            for row in generic_truth_table
        ],
        "level0_binding": level0_binding,
        "level1_binding": level1_binding,
        "handoff_consistency": handoff,
        "blockers": report["blocker_list"],
    }
    return report, graph


def build_decoder_truth_table_binding_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Decoder Truth Table Binding Audit",
        "",
        "This is a metadata-only audit for decoder output truth-table binding. It does not modify placement, routing, standalone.py, or the GDS writer.",
        "",
        "## Summary",
        "",
        f"- truth_table_auto_parse_success: `{report['truth_table_auto_parse_success']}`",
        f"- decoder_truth_table_binding_available: `{report['decoder_truth_table_binding_available']}`",
        f"- truth_table_binding_complete: `{report['truth_table_binding_complete']}`",
        f"- requires_decoder_truth_table_binding: `{report['requires_decoder_truth_table_binding']}`",
        f"- can_enter_decoder_generated_block_planning: `{report['can_enter_decoder_generated_block_planning']}`",
        f"- can_enter_physical_decoder_placement: `{report['can_enter_physical_decoder_placement']}`",
        f"- can_enter_very_limited_control_row_smoke: `{report['can_enter_very_limited_control_row_smoke']}`",
        "",
        "## Generic DECODER3_8 Truth Table",
        "",
        md_table(
            ["output", "polarity_terms", "required_inverted_nets", "and3_slot", "and2_slot", "source"],
            [
                [
                    row["output_slot"],
                    json.dumps(row["input_polarity_terms"], ensure_ascii=False),
                    ", ".join(row["required_inverted_nets"]) or "-",
                    row["and3_leaf_slot"],
                    row["and2_leaf_slot"],
                    row["source_evidence"],
                ]
                for row in report["generic_decoder3_8_truth_table"]
            ],
        ),
        "",
        "## Level 0 Binding",
        "",
        "```json",
        json.dumps(report["level0_binding"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Level 1 Binding",
        "",
        "```json",
        json.dumps(report["level1_binding"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Slot-Level Contract",
        "",
        "```json",
        json.dumps(report["slot_level_contract"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Handoff Consistency",
        "",
        "```json",
        json.dumps(report["handoff_consistency"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Blockers",
        "",
        *[f"- {item}" for item in report["blocker_list"]],
        "",
        "## Step 6.15 Recommendation",
        "",
        f"- {report['step_6_15_recommendation']}",
        "",
    ]
    return "\n".join(lines)


def write_decoder_truth_table_binding_reports(
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
    report, graph = build_decoder_truth_table_binding_report(
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
    out_md.write_text(build_decoder_truth_table_binding_markdown(report), encoding="utf-8")
    out_graph.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def _parse_input_combinations(source: str) -> list[tuple[str, str, str]] | None:
    match = re.search(r"input_combinations\s*=\s*\[(.*?)\]", source, re.S)
    if not match:
        return None
    body = "[" + match.group(1) + "]"
    cleaned = re.sub(r"#.*", "", body)
    try:
        value = ast.literal_eval(cleaned)
    except Exception:
        return None
    combos: list[tuple[str, str, str]] = []
    for item in value:
        if not isinstance(item, tuple) or len(item) != 3:
            return None
        combos.append(tuple(str(x) for x in item))
    return combos
