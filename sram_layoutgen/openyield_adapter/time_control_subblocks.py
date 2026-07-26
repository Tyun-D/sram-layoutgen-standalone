"""Read-only OpenYield TIME remaining control-subblock audit helpers."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _load_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8", errors="ignore")


def _md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in row)
            + " |"
        )
    return "\n".join(lines)


def _macro_audit_entry(gds_pin_audit: dict[str, Any], macro_name: str) -> dict[str, Any] | None:
    for item in gds_pin_audit.get("audited_macros", []):
        if item.get("macro_name") == macro_name:
            return item
    return None


def _contract_entry(contracts_payload: dict[str, Any], class_name: str) -> dict[str, Any] | None:
    for item in contracts_payload.get("contracts", []):
        if item.get("class_name") == class_name or item.get("original_module_name") == class_name:
            return item
    return None


def _candidate_paths(tech_dir: Path, stem: str) -> tuple[list[str], list[str]]:
    gds_paths = sorted(str(path.resolve()) for path in tech_dir.glob(f"**/{stem}.gds"))
    spice_paths = sorted(str(path.resolve()) for path in tech_dir.glob(f"**/{stem}.sp"))
    return gds_paths, spice_paths


def _snippet(text: str, start_pattern: str, stop_pattern: str | None = None) -> str:
    start = text.find(start_pattern)
    if start < 0:
        return ""
    if stop_pattern:
        stop = text.find(stop_pattern, start + len(start_pattern))
        if stop > start:
            return text[start:stop]
    return text[start : start + 2200]


def _has_all(text: str, patterns: list[str]) -> bool:
    return all(pattern in text for pattern in patterns)


def build_time_control_subblock_audit_report(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
    time_control_decomposition_report_path: str | Path | None = None,
    gds_pin_audit_report_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    openyield_root = Path(openyield_root)
    tech_dir = Path(tech_dir)
    contracts_payload = _load_json(contracts_path)
    time_decomp = _load_json(
        time_control_decomposition_report_path or "docs/openyield_time_control_decomposition_report.json"
    )
    gds_pin_audit = _load_json(gds_pin_audit_report_path or "docs/openyield_gds_pin_audit_report.json")

    time_source = openyield_root / "sram_compiler" / "subcircuits" / "time_generate.py"
    testbench_source = openyield_root / "sram_compiler" / "testbenches" / "sram_6t_core_testbench.py"
    time_text = _load_text(time_source)
    testbench_text = _load_text(testbench_source)

    keyword_patterns = [
        "TIME",
        "delay_chain",
        "DelayChain",
        "wen_delay_chain",
        "pdrive",
        "pdrive2_for_pre",
        "wl_pdrive",
        "rbl_delay",
        "rbl_delay_bar",
        "s_en",
        "w_en",
        "PRE",
        "wl_en",
        "clk_buf",
        "clk_bar",
        "gated_clk_buf",
        "gated_clk_bar",
    ]
    keyword_hits = {pattern: (pattern in time_text or pattern in testbench_text) for pattern in keyword_patterns}
    auto_parse_success = all(keyword_hits.values())

    subblocks = [
        {
            "subblock_name": "DELAY_CHAIN",
            "openyield_source_name": "delay_chain",
            "source_file": str(time_source.resolve()),
            "source_class_or_function": "DelayChain",
            "input_signals": ["rbl"],
            "output_signals": ["rbl_delay"],
            "internal_signals": ["dout_1..dout_8", "n_0_*..n_8_*"],
            "control_role": "replica-delay based timing generation",
            "consumer_signals": ["rbl_delay_bar inverter", "sense_enable path", "precharge path"],
            "producer_signals": ["replica bitline rbl"],
            "candidate_local_macros": ["gen_delay_inv", "gen_inv"],
            "candidate_generated_cells": ["Pinv inverter chain"],
            "mapping_status": "partial_generated_chain_candidate",
            "safe_for_metadata_planning": True,
            "safe_for_physical_placement": False,
            "requires_generated_layout_or_stdcell_row": True,
            "requires_timing_proof": True,
            "requires_routing_proof": True,
            "metadata_only": True,
            "source_confirmed": _has_all(time_text, ["class DelayChain", "NAME = \"delay_chain\"", "'rbl', 'rbl_delay'"]),
            "manual_source_review_required": False,
            "notes": [
                "OpenYield source defines a nine-stage inverter delay chain with four load inverters per stage.",
                "TIME instantiates DelayChain from rbl to rbl_delay.",
            ],
        },
        {
            "subblock_name": "WEN_DELAY_CHAIN",
            "openyield_source_name": "wen_delay_chain",
            "source_file": str(time_source.resolve()),
            "source_class_or_function": "WenDelayChain",
            "input_signals": ["rbl_delay_bar"],
            "output_signals": ["rbl_delay_bar_wen"],
            "internal_signals": ["wen_dly_1..N", "wn_i_j"],
            "control_role": "write-enable timing generation",
            "consumer_signals": ["write_enable / w_en special-case path"],
            "producer_signals": ["rbl_delay_bar inverter output"],
            "candidate_local_macros": ["gen_delay_inv", "gen_inv"],
            "candidate_generated_cells": ["Pinv inverter chain"],
            "mapping_status": "partial_generated_chain_candidate",
            "safe_for_metadata_planning": True,
            "safe_for_physical_placement": False,
            "requires_generated_layout_or_stdcell_row": True,
            "requires_timing_proof": True,
            "requires_routing_proof": True,
            "metadata_only": True,
            "source_confirmed": _has_all(
                time_text,
                ["class WenDelayChain", "NAME = \"wen_delay_chain\"", "'rbl_delay_bar', 'rbl_delay_bar_wen'"],
            ),
            "manual_source_review_required": False,
            "notes": [
                "The chain is only instantiated in the special-case `write` + `16x512` branch.",
                "This keeps the adapter audit at source-semantic level; the general path still uses rbl_delay_bar directly.",
            ],
        },
        {
            "subblock_name": "PDRIVE",
            "openyield_source_name": "pdrive",
            "source_file": str(time_source.resolve()),
            "source_class_or_function": "pdrive",
            "input_signals": ["clk"],
            "output_signals": ["clk_buf"],
            "internal_signals": ["zb1_node", "zb2_node", "zb3_node"],
            "control_role": "clock buffer / pulse driver chain",
            "consumer_signals": ["clk_bar inverter", "gated_clk_buf", "ADDR_DFF", "DATA_DFF"],
            "producer_signals": ["top-level clk"],
            "candidate_local_macros": ["gen_inv"],
            "candidate_generated_cells": ["Pinv staged buffer chain"],
            "mapping_status": "partial_generated_chain_candidate",
            "safe_for_metadata_planning": True,
            "safe_for_physical_placement": False,
            "requires_generated_layout_or_stdcell_row": True,
            "requires_timing_proof": True,
            "requires_routing_proof": True,
            "metadata_only": True,
            "source_confirmed": _has_all(time_text, ["class pdrive", "NAME = \"pdrive\"", "'clk', 'clk_buf'"]),
            "manual_source_review_required": False,
            "notes": [
                "The source is a four-stage inverter chain with progressive upsizing.",
                "TIME uses pdrive to generate clk_buf, then a separate inverter derives clk_bar.",
            ],
        },
        {
            "subblock_name": "PDRIVE2_FOR_PRE",
            "openyield_source_name": "pdrive2_for_pre",
            "source_file": str(time_source.resolve()),
            "source_class_or_function": "pdrive2_for_pre",
            "input_signals": ["PRE_UNBUF"],
            "output_signals": ["PRE"],
            "internal_signals": ["zb1_node"],
            "control_role": "precharge control driver",
            "consumer_signals": ["precharge_enb / PRE"],
            "producer_signals": ["PRE_UNBUF from PNAND3(gated_clk_buf, rbl_delay, wl_en_bar)"],
            "candidate_local_macros": ["gen_inv"],
            "candidate_generated_cells": ["Pinv two-stage buffer chain"],
            "mapping_status": "partial_generated_chain_candidate",
            "safe_for_metadata_planning": True,
            "safe_for_physical_placement": False,
            "requires_generated_layout_or_stdcell_row": True,
            "requires_timing_proof": True,
            "requires_routing_proof": True,
            "metadata_only": True,
            "source_confirmed": _has_all(time_text, ["class pdrive2_for_pre", "NAME = \"pdrive2_for_pre\"", "'PRE_UNBUF', 'PRE'"]),
            "manual_source_review_required": False,
            "notes": [
                "The source is a two-stage inverter chain with drive scaling for precharge.",
                "It is downstream of the PNAND3 precharge gating node, not a standalone timing source.",
            ],
        },
        {
            "subblock_name": "WL_PDRIVE",
            "openyield_source_name": "wl_pdrive",
            "source_file": str(time_source.resolve()),
            "source_class_or_function": "wl_pdrive",
            "input_signals": ["gated_clk_bar"],
            "output_signals": ["wl_en"],
            "internal_signals": ["zb1_node", "wl_en_bar"],
            "control_role": "wordline enable pulse driver",
            "consumer_signals": ["wordline_enable", "wl_en_bar", "precharge gating"],
            "producer_signals": ["gated_clk_bar"],
            "candidate_local_macros": ["gen_inv", "gen_nand2"],
            "candidate_generated_cells": ["Pinv two-stage buffer chain", "downstream inverter for wl_en_bar"],
            "mapping_status": "partial_generated_chain_candidate",
            "safe_for_metadata_planning": True,
            "safe_for_physical_placement": False,
            "requires_generated_layout_or_stdcell_row": True,
            "requires_timing_proof": True,
            "requires_routing_proof": True,
            "metadata_only": True,
            "source_confirmed": _has_all(time_text, ["class wl_pdrive", "NAME = \"wl_pdrive\"", "'gated_clk_bar', 'wl_en'"]),
            "manual_source_review_required": False,
            "notes": [
                "The source is a two-stage inverter chain that drives wl_en from gated_clk_bar.",
                "The testbench and earlier wordline audit confirm wl_en feeds the WordlineDriver B domain as active-high enable.",
            ],
        },
    ]

    candidate_specs = [
        ("gen_delay_inv", "delay-chain inverter candidate"),
        ("gen_inv", "generic inverter candidate"),
        ("gen_nand2", "generic nand2 candidate"),
        ("gen_nand4", "generic nand4 candidate"),
        ("dff", "hardcell DFF candidate"),
    ]
    candidate_audit = []
    for macro_name, note in candidate_specs:
        gds_paths, spice_paths = _candidate_paths(tech_dir, macro_name)
        macro_entry = _macro_audit_entry(gds_pin_audit, macro_name)
        candidate_audit.append(
            {
                "candidate_name": macro_name,
                "gds_available": bool(gds_paths),
                "spice_available": bool(spice_paths),
                "pin_metadata_available": bool(macro_entry and macro_entry.get("pins")),
                "power_metadata_available": bool(
                    macro_entry
                    and macro_entry.get("power_rail_audit", {}).get("has_vdd")
                    and macro_entry.get("power_rail_audit", {}).get("has_gnd")
                ),
                "safe_for_metadata_planning": True if macro_name != "gen_nand4" else "partial",
                "safe_for_physical_placement": False,
                "gds_paths": gds_paths,
                "spice_paths": spice_paths,
                "notes": [
                    note,
                    "Conservative policy: physical placement remains blocked without routing, rail continuity, and pin-coverage proof.",
                ],
            }
        )

    dependency_graph = {
        "signals": [
            {
                "source": "clk",
                "target": "clk_buf",
                "via": "PDRIVE",
                "dependency_confirmed": _has_all(time_text, ["'clk', 'clk_buf'", "class pdrive"]),
            },
            {
                "source": "clk_buf",
                "target": "clk_bar",
                "via": "Pinv",
                "dependency_confirmed": "clk_buf', 'clk_bar'" in time_text,
            },
            {
                "source": "cs + clk_bar",
                "target": "gated_clk_bar",
                "via": "AND2",
                "dependency_confirmed": "'cs', 'clk_bar','gated_clk_bar'" in time_text,
            },
            {
                "source": "cs + clk_buf",
                "target": "gated_clk_buf",
                "via": "AND2",
                "dependency_confirmed": "'cs', 'clk_buf','gated_clk_buf'" in time_text,
            },
            {
                "source": "gated_clk_bar",
                "target": "wordline_enable / wl_en",
                "via": "WL_PDRIVE",
                "dependency_confirmed": "'gated_clk_bar', 'wl_en'" in time_text and "'VDD', 'VSS', 'wl_en', 'VDD', 'RWL'" in testbench_text,
            },
            {
                "source": "rbl",
                "target": "rbl_delay",
                "via": "DELAY_CHAIN",
                "dependency_confirmed": "'rbl', 'rbl_delay'" in time_text,
            },
            {
                "source": "rbl_delay",
                "target": "rbl_delay_bar",
                "via": "Pinv",
                "dependency_confirmed": "'rbl_delay', 'rbl_delay_bar'" in time_text,
            },
            {
                "source": "rbl_delay_bar + gated_clk_bar + we",
                "target": "write_enable / w_en",
                "via": "AND3",
                "dependency_confirmed": "'rbl_delay_bar' ,'gated_clk_bar' ,'we', 'w_en'" in time_text
                or "w_en_rbl_input , 'gated_clk_bar' ,'we', 'w_en'" in time_text,
            },
            {
                "source": "rbl_delay + gated_clk_bar + we_bar",
                "target": "sense_enable / s_en",
                "via": "AND3",
                "dependency_confirmed": "'rbl_delay', 'gated_clk_bar' ,'we_bar' ,'s_en'" in time_text,
            },
            {
                "source": "gated_clk_buf + rbl_delay + wl_en_bar",
                "target": "PRE_UNBUF",
                "via": "PNAND3",
                "dependency_confirmed": "'gated_clk_buf', 'rbl_delay', 'wl_en_bar', 'PRE_UNBUF'" in time_text,
            },
            {
                "source": "PRE_UNBUF",
                "target": "precharge_enb / PRE",
                "via": "PDRIVE2_FOR_PRE",
                "dependency_confirmed": "'PRE_UNBUF', 'PRE'" in time_text,
            },
        ]
    }

    remaining_subblocks_without_direct_macro = [
        item["subblock_name"]
        for item in subblocks
        if item["mapping_status"] != "direct_hardcell_available"
    ]
    unresolved_items = [
        "TIME must remain decomposed; treating TIME as one macro is not allowed.",
        "delay_chain / wen_delay_chain / pdrive / pdrive2_for_pre / wl_pdrive still require generated layout or stdcell-row realization.",
        "gen_nand4 exists as GDS candidate but current pin metadata is incomplete.",
        "Physical timing proof, routing proof, and control-row placement proof are all still missing.",
        "This audit closes semantic planning only; it does not allow physical control placement or standalone control placement.",
    ]

    report = {
        "scope": "step6_23_openyield_time_control_subblock_adapter_audit",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(Path(contracts_path).resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "time_control_subblock_audit_available": True,
        "time_as_single_macro_allowed": False,
        "auto_parse_success": auto_parse_success,
        "manual_source_review_required": False if auto_parse_success else True,
        "source_files": {
            "time_generate": str(time_source.resolve()),
            "testbench": str(testbench_source.resolve()),
        },
        "keyword_hits": keyword_hits,
        "time_control_decomposition_reference": {
            "scope": time_decomp.get("scope"),
            "can_enter_control_subblock_adapter_planning": time_decomp.get("can_enter_control_subblock_adapter_planning"),
        },
        "remaining_time_control_subblocks": [item["subblock_name"] for item in subblocks],
        "subblock_audit": subblocks,
        "local_candidate_macro_generated_cell_audit": candidate_audit,
        "control_signal_dependency_graph": dependency_graph,
        "delay_chain_metadata_available": "partial",
        "wen_delay_chain_metadata_available": "partial",
        "pdrive_metadata_available": "partial",
        "pdrive2_for_pre_metadata_available": "partial",
        "wl_pdrive_metadata_available": "partial",
        "safe_for_metadata_planning": {
            item["subblock_name"]: item["safe_for_metadata_planning"] for item in subblocks
        },
        "safe_for_physical_placement": {
            item["subblock_name"]: item["safe_for_physical_placement"] for item in subblocks
        },
        "can_enter_time_control_subblock_metadata_planning": True,
        "can_enter_time_control_physical_placement": False,
        "can_enter_standalone_control_placement": False,
        "unresolved_items": unresolved_items,
        "audit_summary": {
            "remaining_control_subblocks_without_adapter_level_physical_closure": remaining_subblocks_without_direct_macro,
            "subblocks_safe_for_metadata_planning": [
                item["subblock_name"] for item in subblocks if item["safe_for_metadata_planning"]
            ],
            "subblocks_safe_for_physical_placement": [
                item["subblock_name"] for item in subblocks if item["safe_for_physical_placement"]
            ],
            "time_control_subblock_audit_available": True,
            "time_as_single_macro_allowed": False,
            "can_enter_time_control_subblock_metadata_planning": True,
            "can_enter_time_control_physical_placement": False,
            "can_enter_standalone_control_placement": False,
        },
        "step_6_24_recommendation": {
            "recommended_next_phase": "time_control_signal_binding_contracts",
            "candidate_directions": [
                "delay_chain_binding_contracts",
                "wen_delay_chain_binding_contracts",
                "precharge_control_contracts",
                "wordline_enable_control_contracts",
                "sense_write_enable_signal_binding",
            ],
            "reason": [
                "Source-level semantics are now sufficient for metadata planning.",
                "Physical control placement is still blocked, so the next useful step is binding contracts rather than placement.",
                "The remaining uncertainty is at signal-binding and generated-logic contract level, not decoder metadata level.",
            ],
        },
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "source_snippets": {
            "delay_chain": _snippet(time_text, "class DelayChain", "class WenDelayChain"),
            "wen_delay_chain": _snippet(time_text, "class WenDelayChain", "class ADDR_DFF"),
            "pdrive_family": _snippet(time_text, "class pdrive", "class dff"),
            "time_wiring": _snippet(time_text, "wl_en=wl_pdrive()", "if __name__ == '__main__':"),
        },
    }

    graph = {
        "scope": report["scope"],
        "nodes": [
            {"id": "TIME", "kind": "control_root"},
            *[
                {
                    "id": item["subblock_name"],
                    "kind": "time_subblock",
                    "safe_for_metadata_planning": item["safe_for_metadata_planning"],
                    "safe_for_physical_placement": item["safe_for_physical_placement"],
                }
                for item in subblocks
            ],
            *[
                {"id": item["candidate_name"], "kind": "local_candidate"}
                for item in candidate_audit
            ],
        ],
        "edges": [
            {"source": "TIME", "target": item["subblock_name"], "relation": "decomposes_into"}
            for item in subblocks
        ]
        + [
            {
                "source": entry["source"],
                "target": entry["target"],
                "relation": entry["via"],
                "dependency_confirmed": entry["dependency_confirmed"],
            }
            for entry in dependency_graph["signals"]
        ],
        "summary": report["audit_summary"],
    }

    return report, graph


def build_time_control_subblock_audit_markdown(report: dict[str, Any]) -> str:
    subblock_rows = []
    for item in report["subblock_audit"]:
        subblock_rows.append(
            [
                item["subblock_name"],
                item["openyield_source_name"],
                ", ".join(item["input_signals"]),
                ", ".join(item["output_signals"]),
                item["control_role"],
                item["mapping_status"],
                item["safe_for_metadata_planning"],
                item["safe_for_physical_placement"],
                item["source_confirmed"],
            ]
        )

    candidate_rows = []
    for item in report["local_candidate_macro_generated_cell_audit"]:
        candidate_rows.append(
            [
                item["candidate_name"],
                item["gds_available"],
                item["spice_available"],
                item["pin_metadata_available"],
                item["power_metadata_available"],
                item["safe_for_metadata_planning"],
                item["safe_for_physical_placement"],
            ]
        )

    dependency_rows = []
    for item in report["control_signal_dependency_graph"]["signals"]:
        dependency_rows.append(
            [
                item["source"],
                item["via"],
                item["target"],
                item["dependency_confirmed"],
            ]
        )

    lines = [
        "# OpenYield TIME Control Subblock Audit Report",
        "",
        "This is a read-only source / contract / candidate-macro audit for the remaining TIME control subblocks. It does not modify placement, routing, standalone.py, or the GDS writer.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Remaining TIME Subblocks",
        "",
        _md_table(
            [
                "subblock",
                "OpenYield source",
                "inputs",
                "outputs",
                "role",
                "mapping",
                "metadata planning",
                "physical placement",
                "source confirmed",
            ],
            subblock_rows,
        ),
        "",
        "## Local Candidate Macro / Generated Cell Audit",
        "",
        _md_table(
            [
                "candidate",
                "GDS",
                "SPICE",
                "pin metadata",
                "power metadata",
                "metadata planning",
                "physical placement",
            ],
            candidate_rows,
        ),
        "",
        "## Control Signal Dependency Graph",
        "",
        _md_table(["source", "via", "target", "confirmed"], dependency_rows),
        "",
        "## Unresolved Items",
        "",
    ]
    lines.extend(f"- {item}" for item in report["unresolved_items"])
    lines.extend(
        [
            "",
            "## Step 6.24 Recommendation",
            "",
            "```json",
            json.dumps(report["step_6_24_recommendation"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Entry Decisions",
            "",
            f"- can_enter_time_control_subblock_metadata_planning: `{report['can_enter_time_control_subblock_metadata_planning']}`",
            f"- can_enter_time_control_physical_placement: `{report['can_enter_time_control_physical_placement']}`",
            f"- can_enter_standalone_control_placement: `{report['can_enter_standalone_control_placement']}`",
            "",
        ]
    )
    return "\n".join(lines)
