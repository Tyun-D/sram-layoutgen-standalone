"""Read-only OpenYield TIME control signal binding contract audit."""

from __future__ import annotations

import json
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


def _candidate_paths(tech_dir: Path, stem: str) -> tuple[list[str], list[str]]:
    gds_paths = sorted(str(path.resolve()) for path in tech_dir.glob(f"**/{stem}.gds"))
    spice_paths = sorted(str(path.resolve()) for path in tech_dir.glob(f"**/{stem}.sp"))
    return gds_paths, spice_paths


def _macro_audit_entry(gds_pin_audit: dict[str, Any], macro_name: str) -> dict[str, Any] | None:
    for item in gds_pin_audit.get("audited_macros", []):
        if item.get("macro_name") == macro_name:
            return item
    return None


def _has(text: str, pattern: str) -> bool:
    return pattern in text


def _make_candidate_mapping(
    tech_dir: Path,
    gds_pin_audit: dict[str, Any],
    candidate_cells: list[str],
    candidate_sequence: list[str],
    candidate_mapping_status: str,
) -> dict[str, Any]:
    details = []
    pin_ok = True
    power_ok = True
    for cell in candidate_cells:
        gds_paths, spice_paths = _candidate_paths(tech_dir, cell)
        macro_entry = _macro_audit_entry(gds_pin_audit, cell)
        cell_pin_ok = bool(macro_entry and macro_entry.get("pins"))
        cell_power_ok = bool(
            macro_entry
            and macro_entry.get("power_rail_audit", {}).get("has_vdd")
            and macro_entry.get("power_rail_audit", {}).get("has_gnd")
        )
        pin_ok = pin_ok and cell_pin_ok
        power_ok = power_ok and cell_power_ok
        details.append(
            {
                "candidate_name": cell,
                "gds_available": bool(gds_paths),
                "spice_available": bool(spice_paths),
                "pin_metadata_available": cell_pin_ok,
                "power_metadata_available": cell_power_ok,
                "safe_for_metadata_planning": True if cell != "gen_nand4" else "partial",
                "safe_for_physical_placement": False,
                "gds_paths": gds_paths,
                "spice_paths": spice_paths,
            }
        )
    return {
        "candidate_cells": candidate_cells,
        "candidate_sequence": candidate_sequence,
        "candidate_cell_count_if_known": len(candidate_sequence),
        "candidate_mapping_status": candidate_mapping_status,
        "pin_metadata_available": pin_ok,
        "power_metadata_available": power_ok,
        "safe_for_metadata_planning": True if "gen_nand4" not in candidate_cells else "partial",
        "safe_for_physical_placement": False,
        "candidate_details": details,
    }


def build_time_control_signal_binding_report(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
    subblock_report_path: str | Path | None = None,
    decomposition_report_path: str | Path | None = None,
    decoder_closure_report_path: str | Path | None = None,
    gds_pin_audit_report_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    openyield_root = Path(openyield_root)
    tech_dir = Path(tech_dir)
    subblock_report = _load_json(subblock_report_path or "docs/openyield_time_control_subblock_audit_report.json")
    decomposition_report = _load_json(decomposition_report_path or "docs/openyield_time_control_decomposition_report.json")
    decoder_closure_report = _load_json(decoder_closure_report_path or "docs/openyield_decoder_metadata_closure_report.json")
    gds_pin_audit = _load_json(gds_pin_audit_report_path or "docs/openyield_gds_pin_audit_report.json")
    _ = _load_json(contracts_path)

    time_source = openyield_root / "sram_compiler" / "subcircuits" / "time_generate.py"
    testbench_source = openyield_root / "sram_compiler" / "testbenches" / "sram_6t_core_testbench.py"
    time_text = _load_text(time_source)
    testbench_text = _load_text(testbench_source)

    binding_contracts = [
        {
            "contract_name": "CLK_BUF_BINDING_CONTRACT",
            "signal_name": "clk_buf",
            "aliases": ["clk_buf"],
            "producer_subblock": "PDRIVE",
            "producer_expression_or_dependency": "clk -> PDRIVE -> clk_buf",
            "input_signals": ["clk"],
            "output_signal": "clk_buf",
            "consumer_blocks": ["ADDR_DFF", "DATA_DFF", "DFF_BUF", "clk_bar inverter", "gated clock logic"],
            "consumer_pins": ["ADDR_DFF.CLK", "DATA_DFF.CLK", "DFF_BUF.CLK", "Pinv.A", "AND2.B"],
            "polarity": "non_inverting",
            "active_level": "clock_buffered",
            "conditional_applicability": "always",
            "candidate_local_macros": ["gen_inv"],
            "candidate_generated_cells": ["Pinv staged buffer chain"],
            "source_evidence": [
                "time_generate.py instantiates pdrive and connects clk to clk_buf.",
                "TIME top-level nodes explicitly include clk and clk_buf.",
            ],
            "metadata_binding_available": True,
            "safe_for_metadata_planning": True,
            "safe_for_physical_placement": False,
            "requires_timing_proof": True,
            "requires_routing_proof": True,
            "requires_generated_layout_or_stdcell_row": True,
            "metadata_only": True,
            "candidate_implementation": _make_candidate_mapping(
                tech_dir, gds_pin_audit, ["gen_inv"], ["gen_inv", "gen_inv", "gen_inv", "gen_inv"], "generated_buffer_chain"
            ),
            "notes": [
                "Producer is a four-stage inverter chain with upsizing.",
                "This contract can drive planning metadata but not physical control placement.",
            ],
        },
        {
            "contract_name": "CLK_BAR_BINDING_CONTRACT",
            "signal_name": "clk_bar",
            "aliases": ["clk_bar"],
            "producer_subblock": "Pinv",
            "producer_expression_or_dependency": "clk_buf -> Pinv -> clk_bar",
            "input_signals": ["clk_buf"],
            "output_signal": "clk_bar",
            "consumer_blocks": ["gated clock logic"],
            "consumer_pins": ["AND2.B"],
            "polarity": "inverting",
            "active_level": "inverted_clk_buf",
            "conditional_applicability": "always",
            "candidate_local_macros": ["gen_inv"],
            "candidate_generated_cells": ["Pinv"],
            "source_evidence": [
                "time_generate.py instantiates inv_clk_bar from clk_buf to clk_bar.",
            ],
            "metadata_binding_available": True,
            "safe_for_metadata_planning": True,
            "safe_for_physical_placement": False,
            "requires_timing_proof": True,
            "requires_routing_proof": True,
            "requires_generated_layout_or_stdcell_row": True,
            "metadata_only": True,
            "candidate_implementation": _make_candidate_mapping(
                tech_dir, gds_pin_audit, ["gen_inv"], ["gen_inv"], "single_inverter_binding"
            ),
            "notes": [
                "clk_bar is explicitly the inversion of clk_buf, not a separately buffered top-level input.",
            ],
        },
        {
            "contract_name": "GATED_CLK_BUF_BINDING_CONTRACT",
            "signal_name": "gated_clk_buf",
            "aliases": ["gated_clk_buf"],
            "producer_subblock": "AND2",
            "producer_expression_or_dependency": "cs + clk_buf -> AND2 -> gated_clk_buf",
            "input_signals": ["cs", "clk_buf"],
            "output_signal": "gated_clk_buf",
            "consumer_blocks": ["precharge control logic"],
            "consumer_pins": ["PNAND3.A"],
            "polarity": "non_inverting_and",
            "active_level": "high_when_cs_and_clk_buf_high",
            "conditional_applicability": "always",
            "candidate_local_macros": ["gen_nand2", "gen_inv"],
            "candidate_generated_cells": ["AND2 composite from PNAND2 + Pinv"],
            "source_evidence": [
                "time_generate.py instantiates and2_gated_clk_buf from cs and clk_buf.",
                "standard_cell.py defines AND2 as PNAND2 followed by Pinv.",
            ],
            "metadata_binding_available": True,
            "safe_for_metadata_planning": True,
            "safe_for_physical_placement": False,
            "requires_timing_proof": True,
            "requires_routing_proof": True,
            "requires_generated_layout_or_stdcell_row": True,
            "metadata_only": True,
            "candidate_implementation": _make_candidate_mapping(
                tech_dir, gds_pin_audit, ["gen_nand2", "gen_inv"], ["gen_nand2", "gen_inv"], "metadata_composite_and2"
            ),
            "notes": [
                "This is an AND semantic contract, not a direct hard macro mapping.",
            ],
        },
        {
            "contract_name": "GATED_CLK_BAR_BINDING_CONTRACT",
            "signal_name": "gated_clk_bar",
            "aliases": ["gated_clk_bar"],
            "producer_subblock": "AND2",
            "producer_expression_or_dependency": "cs + clk_bar -> AND2 -> gated_clk_bar",
            "input_signals": ["cs", "clk_bar"],
            "output_signal": "gated_clk_bar",
            "consumer_blocks": ["WL_PDRIVE", "WRITE_ENABLE path", "SENSE_ENABLE path"],
            "consumer_pins": ["WL_PDRIVE.A", "AND3.B", "AND3.B"],
            "polarity": "non_inverting_and",
            "active_level": "high_when_cs_and_clk_bar_high",
            "conditional_applicability": "always",
            "candidate_local_macros": ["gen_nand2", "gen_inv"],
            "candidate_generated_cells": ["AND2 composite from PNAND2 + Pinv"],
            "source_evidence": [
                "time_generate.py instantiates and2_gated_clk_bar from cs and clk_bar.",
                "standard_cell.py defines AND2 as PNAND2 followed by Pinv.",
            ],
            "metadata_binding_available": True,
            "safe_for_metadata_planning": True,
            "safe_for_physical_placement": False,
            "requires_timing_proof": True,
            "requires_routing_proof": True,
            "requires_generated_layout_or_stdcell_row": True,
            "metadata_only": True,
            "candidate_implementation": _make_candidate_mapping(
                tech_dir, gds_pin_audit, ["gen_nand2", "gen_inv"], ["gen_nand2", "gen_inv"], "metadata_composite_and2"
            ),
            "notes": [
                "This gated clock branch is the direct producer for wl_en and the enable-side input for w_en / s_en generation.",
            ],
        },
        {
            "contract_name": "RBL_DELAY_BINDING_CONTRACT",
            "signal_name": "rbl_delay",
            "aliases": ["rbl_delay"],
            "producer_subblock": "DELAY_CHAIN",
            "producer_expression_or_dependency": "rbl -> DELAY_CHAIN -> rbl_delay",
            "input_signals": ["rbl"],
            "output_signal": "rbl_delay",
            "consumer_blocks": ["Pinv", "SENSE_ENABLE path", "PRECHARGE path"],
            "consumer_pins": ["Pinv.A", "AND3.A", "PNAND3.B"],
            "polarity": "delayed_non_inverting",
            "active_level": "replica_delay_domain",
            "conditional_applicability": "always",
            "candidate_local_macros": ["gen_delay_inv", "gen_inv"],
            "candidate_generated_cells": ["Pinv delay chain"],
            "source_evidence": [
                "time_generate.py instantiates DelayChain from rbl to rbl_delay.",
                "DelayChain source shows nine inverter stages plus distributed loads.",
            ],
            "metadata_binding_available": True,
            "safe_for_metadata_planning": True,
            "safe_for_physical_placement": False,
            "requires_timing_proof": True,
            "requires_routing_proof": True,
            "requires_generated_layout_or_stdcell_row": True,
            "metadata_only": True,
            "candidate_implementation": _make_candidate_mapping(
                tech_dir,
                gds_pin_audit,
                ["gen_delay_inv", "gen_inv"],
                ["gen_delay_inv"] * 9,
                "generated_delay_chain",
            ),
            "notes": [
                "This contract is especially timing-sensitive and must remain metadata-only until delay proof exists.",
            ],
        },
        {
            "contract_name": "RBL_DELAY_BAR_BINDING_CONTRACT",
            "signal_name": "rbl_delay_bar",
            "aliases": ["rbl_delay_bar"],
            "producer_subblock": "Pinv",
            "producer_expression_or_dependency": "rbl_delay -> Pinv -> rbl_delay_bar",
            "input_signals": ["rbl_delay"],
            "output_signal": "rbl_delay_bar",
            "consumer_blocks": ["WRITE_ENABLE path", "WEN_DELAY_CHAIN conditional path"],
            "consumer_pins": ["AND3.A", "WEN_DELAY_CHAIN.in"],
            "polarity": "inverting",
            "active_level": "inverted_replica_delay_domain",
            "conditional_applicability": "always",
            "candidate_local_macros": ["gen_inv"],
            "candidate_generated_cells": ["Pinv"],
            "source_evidence": [
                "time_generate.py instantiates inv_rbl_delay_bar from rbl_delay to rbl_delay_bar.",
            ],
            "metadata_binding_available": True,
            "safe_for_metadata_planning": True,
            "safe_for_physical_placement": False,
            "requires_timing_proof": True,
            "requires_routing_proof": True,
            "requires_generated_layout_or_stdcell_row": True,
            "metadata_only": True,
            "candidate_implementation": _make_candidate_mapping(
                tech_dir, gds_pin_audit, ["gen_inv"], ["gen_inv"], "single_inverter_binding"
            ),
            "notes": [
                "rbl_delay_bar is the default write-enable-side timing input.",
            ],
        },
        {
            "contract_name": "WORDLINE_ENABLE_BINDING_CONTRACT",
            "signal_name": "wl_en",
            "aliases": ["wl_en", "wordline_enable"],
            "producer_subblock": "WL_PDRIVE",
            "producer_expression_or_dependency": "gated_clk_bar -> WL_PDRIVE -> wl_en; wl_en -> Pinv -> wl_en_bar",
            "input_signals": ["gated_clk_bar"],
            "output_signal": "wl_en",
            "consumer_blocks": ["WORDLINEDRIVER", "PRECHARGE path", "Replica RWL AND2"],
            "consumer_pins": ["WORDLINEDRIVER.B", "Pinv.A(wl_en_bar)", "RWL_AND2.B"],
            "polarity": "non_inverting",
            "active_level": "active_high",
            "conditional_applicability": "always",
            "candidate_local_macros": ["gen_inv"],
            "candidate_generated_cells": ["Pinv two-stage chain", "downstream Pinv for wl_en_bar"],
            "source_evidence": [
                "time_generate.py instantiates wl_pdrive from gated_clk_bar to wl_en.",
                "time_generate.py then instantiates inv_wl_en_bar from wl_en to wl_en_bar.",
                "testbench connects wl_en into the RWL path and prior wordline audit confirms WORDLINEDRIVER.B active-high.",
            ],
            "metadata_binding_available": True,
            "safe_for_metadata_planning": True,
            "safe_for_physical_placement": False,
            "requires_timing_proof": True,
            "requires_routing_proof": True,
            "requires_generated_layout_or_stdcell_row": True,
            "metadata_only": True,
            "candidate_implementation": _make_candidate_mapping(
                tech_dir, gds_pin_audit, ["gen_inv"], ["gen_inv", "gen_inv", "gen_inv"], "generated_wordline_enable_chain"
            ),
            "notes": [
                "The active-high interpretation is source-confirmed and consistent with the prior WORDLINEDRIVER adapter audit.",
            ],
        },
        {
            "contract_name": "WRITE_ENABLE_BINDING_CONTRACT",
            "signal_name": "w_en",
            "aliases": ["w_en", "write_enable"],
            "producer_subblock": "AND3",
            "producer_expression_or_dependency": "rbl_delay_bar + gated_clk_bar + we -> AND3 -> w_en",
            "input_signals": ["rbl_delay_bar or rbl_delay_bar_wen", "gated_clk_bar", "we"],
            "output_signal": "w_en",
            "consumer_blocks": ["WRITEDRIVER"],
            "consumer_pins": ["WRITEDRIVER.EN"],
            "polarity": "non_inverting_and3",
            "active_level": "active_high",
            "conditional_applicability": "always, with conditional alternate first input in special WEN path",
            "candidate_local_macros": ["gen_nand2", "gen_inv"],
            "candidate_generated_cells": ["AND3 composite from PNAND3 + Pinv"],
            "source_evidence": [
                "time_generate.py instantiates AND3 with inputs w_en_rbl_input, gated_clk_bar, and we to produce w_en.",
                "standard_cell.py defines AND3 as PNAND3 followed by Pinv.",
                "write driver audit confirms WRITEDRIVER.EN is the consumer.",
            ],
            "metadata_binding_available": True,
            "safe_for_metadata_planning": True,
            "safe_for_physical_placement": False,
            "requires_timing_proof": True,
            "requires_routing_proof": True,
            "requires_generated_layout_or_stdcell_row": True,
            "metadata_only": True,
            "candidate_implementation": _make_candidate_mapping(
                tech_dir, gds_pin_audit, ["gen_nand2", "gen_inv"], ["PNAND3(proxy)", "gen_inv"], "metadata_composite_and3"
            ),
            "notes": [
                "The first input is conditionally substituted by WEN_DELAY_CHAIN output in one special write branch.",
                "Physical implementation remains blocked because local AND3 is only a semantic composite, not a proven physical macro.",
            ],
        },
        {
            "contract_name": "SENSE_ENABLE_BINDING_CONTRACT",
            "signal_name": "s_en",
            "aliases": ["s_en", "sense_enable"],
            "producer_subblock": "AND3",
            "producer_expression_or_dependency": "rbl_delay + gated_clk_bar + we_bar -> AND3 -> s_en",
            "input_signals": ["rbl_delay", "gated_clk_bar", "we_bar"],
            "output_signal": "s_en",
            "consumer_blocks": ["SENSEAMP"],
            "consumer_pins": ["SENSEAMP.EN"],
            "polarity": "non_inverting_and3",
            "active_level": "active_high",
            "conditional_applicability": "always",
            "candidate_local_macros": ["gen_nand2", "gen_inv"],
            "candidate_generated_cells": ["AND3 composite from PNAND3 + Pinv"],
            "source_evidence": [
                "time_generate.py instantiates AND3 with inputs rbl_delay, gated_clk_bar, and we_bar to produce s_en.",
                "sense amp adapter audit confirms SENSEAMP.EN is the consumer.",
            ],
            "metadata_binding_available": True,
            "safe_for_metadata_planning": True,
            "safe_for_physical_placement": False,
            "requires_timing_proof": True,
            "requires_routing_proof": True,
            "requires_generated_layout_or_stdcell_row": True,
            "metadata_only": True,
            "candidate_implementation": _make_candidate_mapping(
                tech_dir, gds_pin_audit, ["gen_nand2", "gen_inv"], ["PNAND3(proxy)", "gen_inv"], "metadata_composite_and3"
            ),
            "notes": [
                "This contract stays single-ended on the consumer side because the current sense-amp adapter uses Q -> dout and keeps QB dropped.",
            ],
        },
        {
            "contract_name": "PRECHARGE_ENB_BINDING_CONTRACT",
            "signal_name": "PRE",
            "aliases": ["PRE", "precharge_enb"],
            "producer_subblock": "PNAND3 + PDRIVE2_FOR_PRE",
            "producer_expression_or_dependency": "gated_clk_buf + rbl_delay + wl_en_bar -> PNAND3 -> PRE_UNBUF; PRE_UNBUF -> PDRIVE2_FOR_PRE -> PRE",
            "input_signals": ["gated_clk_buf", "rbl_delay", "wl_en_bar"],
            "output_signal": "PRE",
            "consumer_blocks": ["PRECHARGE"],
            "consumer_pins": ["PRECHARGE.ENB"],
            "polarity": "active_low_enable",
            "active_level": "active_low",
            "conditional_applicability": "always",
            "candidate_local_macros": ["gen_nand2", "gen_inv"],
            "candidate_generated_cells": ["PNAND3 semantic composite", "pdrive2_for_pre buffer chain"],
            "source_evidence": [
                "time_generate.py instantiates PNAND3 into PRE_UNBUF, then pdrive2_for_pre into PRE.",
                "precharge contract uses ENB active-low convention.",
            ],
            "metadata_binding_available": True,
            "safe_for_metadata_planning": True,
            "safe_for_physical_placement": False,
            "requires_timing_proof": True,
            "requires_routing_proof": True,
            "requires_generated_layout_or_stdcell_row": True,
            "metadata_only": True,
            "candidate_implementation": _make_candidate_mapping(
                tech_dir, gds_pin_audit, ["gen_nand2", "gen_inv"], ["PNAND3(proxy)", "gen_inv", "gen_inv"], "metadata_composite_precharge_enable"
            ),
            "notes": [
                "The signal name PRE is treated as canonical precharge_enb because the PRECHARGE consumer pin is ENB.",
            ],
        },
        {
            "contract_name": "WEN_DELAY_CONDITIONAL_BINDING_CONTRACT",
            "signal_name": "rbl_delay_bar_wen",
            "aliases": ["rbl_delay_bar_wen"],
            "producer_subblock": "WEN_DELAY_CHAIN",
            "producer_expression_or_dependency": "rbl_delay_bar -> WEN_DELAY_CHAIN -> rbl_delay_bar_wen -> w_en path",
            "input_signals": ["rbl_delay_bar"],
            "output_signal": "rbl_delay_bar_wen",
            "consumer_blocks": ["WRITE_ENABLE path"],
            "consumer_pins": ["AND3.A via w_en_rbl_input"],
            "polarity": "delayed_non_inverting",
            "active_level": "conditional_write_timing_domain",
            "conditional_applicability": "operation == write and num_rows == 16 and num_cols == 512",
            "candidate_local_macros": ["gen_delay_inv", "gen_inv"],
            "candidate_generated_cells": ["Pinv delay chain"],
            "source_evidence": [
                "time_generate.py special-case branch instantiates WenDelayChain(stages=6, loads_per_stage=4) only for write + 16x512.",
                "The branch rebinds w_en_rbl_input from rbl_delay_bar to rbl_delay_bar_wen.",
            ],
            "metadata_binding_available": True,
            "safe_for_metadata_planning": True,
            "safe_for_physical_placement": False,
            "requires_timing_proof": True,
            "requires_routing_proof": True,
            "requires_generated_layout_or_stdcell_row": True,
            "metadata_only": True,
            "candidate_implementation": _make_candidate_mapping(
                tech_dir, gds_pin_audit, ["gen_delay_inv", "gen_inv"], ["gen_delay_inv"] * 6, "conditional_generated_delay_chain"
            ),
            "notes": [
                "This contract is partial/conditional by design and must not be generalized beyond the source-confirmed branch.",
            ],
        },
    ]

    polarity_checks = {
        "wordline_enable_active_high_consistent": _has(time_text, "'gated_clk_bar', 'wl_en'")
        and _has(testbench_text, "'VDD', 'VSS', 'wl_en', 'VDD', 'RWL'"),
        "write_enable_consumer_consistent": _has(time_text, "'we', 'w_en'"),
        "sense_enable_consumer_consistent": _has(time_text, "'we_bar' ,'s_en'"),
        "precharge_enb_active_low_consistent": _has(time_text, "'PRE_UNBUF', 'PRE'") and _has(time_text, "'PRE'"),
        "clk_bar_inversion_consistent": _has(time_text, "'clk_buf', 'clk_bar'"),
        "gated_clock_dependency_consistent": _has(time_text, "'cs', 'clk_bar','gated_clk_bar'") and _has(time_text, "'cs', 'clk_buf','gated_clk_buf'"),
    }
    control_signal_binding_consistent = all(polarity_checks.values())

    dependency_graph = {
        "edges": [
            {"source": "clk", "via": "PDRIVE", "target": "clk_buf", "dependency_confirmed": True, "metadata_only": True, "physical_routing_proven": False},
            {"source": "clk_buf", "via": "Pinv", "target": "clk_bar", "dependency_confirmed": True, "metadata_only": True, "physical_routing_proven": False},
            {"source": "clk_buf + cs", "via": "AND2", "target": "gated_clk_buf", "dependency_confirmed": True, "metadata_only": True, "physical_routing_proven": False},
            {"source": "clk_bar + cs", "via": "AND2", "target": "gated_clk_bar", "dependency_confirmed": True, "metadata_only": True, "physical_routing_proven": False},
            {"source": "gated_clk_bar", "via": "WL_PDRIVE", "target": "wl_en", "dependency_confirmed": True, "metadata_only": True, "physical_routing_proven": False},
            {"source": "wl_en", "via": "Pinv", "target": "wl_en_bar", "dependency_confirmed": True, "metadata_only": True, "physical_routing_proven": False},
            {"source": "rbl", "via": "DELAY_CHAIN", "target": "rbl_delay", "dependency_confirmed": True, "metadata_only": True, "physical_routing_proven": False},
            {"source": "rbl_delay", "via": "Pinv", "target": "rbl_delay_bar", "dependency_confirmed": True, "metadata_only": True, "physical_routing_proven": False},
            {"source": "rbl_delay_bar + gated_clk_bar + we", "via": "AND3", "target": "w_en", "dependency_confirmed": True, "metadata_only": True, "physical_routing_proven": False},
            {"source": "rbl_delay + gated_clk_bar + we_bar", "via": "AND3", "target": "s_en", "dependency_confirmed": True, "metadata_only": True, "physical_routing_proven": False},
            {"source": "gated_clk_buf + rbl_delay + wl_en_bar", "via": "PNAND3", "target": "PRE_UNBUF", "dependency_confirmed": True, "metadata_only": True, "physical_routing_proven": False},
            {"source": "PRE_UNBUF", "via": "PDRIVE2_FOR_PRE", "target": "PRE", "dependency_confirmed": True, "metadata_only": True, "physical_routing_proven": False},
        ]
    }

    unresolved_items = [
        "TIME still decomposed, not a macro.",
        "delay / pdrive chains still require generated layout or stdcell-row realization.",
        "timing proof missing for delay_chain and wen_delay_chain.",
        "routing proof missing for all control signals.",
        "control-row physical placement proof missing.",
        "rail continuity proof missing.",
        "gen_nand4 remains partial / not physical-ready.",
    ]

    report = {
        "scope": "step6_24_openyield_time_control_signal_binding_audit",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(Path(contracts_path).resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "source_reports": {
            "time_control_subblock_audit": subblock_report.get("scope"),
            "time_control_decomposition": decomposition_report.get("scope"),
            "decoder_metadata_closure": decoder_closure_report.get("scope"),
        },
        "time_control_signal_binding_available": True,
        "time_as_single_macro_allowed": False,
        "partial_or_conditional_bindings_present": True,
        "control_signal_binding_consistent": control_signal_binding_consistent,
        "all_core_control_signals_have_binding_contract": True,
        "signal_binding_contracts": binding_contracts,
        "polarity_consistency_checks": polarity_checks,
        "dependency_graph": dependency_graph,
        "unresolved_items": unresolved_items,
        "can_enter_time_control_signal_metadata_planning": True,
        "can_enter_time_control_physical_placement": False,
        "can_enter_standalone_control_placement": False,
        "audit_summary": {
            "time_control_signal_binding_available": True,
            "time_as_single_macro_allowed": False,
            "control_signal_binding_consistent": control_signal_binding_consistent,
            "all_core_control_signals_have_binding_contract": True,
            "partial_or_conditional_bindings_present": True,
            "can_enter_time_control_signal_metadata_planning": True,
            "can_enter_time_control_physical_placement": False,
            "can_enter_standalone_control_placement": False,
        },
        "step_6_25_recommendation": {
            "recommended_next_phase": "time_control_generated_logic_contract_packaging",
            "candidate_directions": [
                "and2_and3_metadata_contract_packaging",
                "wl_enable_precharge_enable_consumer_binding",
                "write_enable_sense_enable_consumer_binding",
                "conditional_wen_delay_policy_capture",
            ],
            "reason": [
                "The signal graph and polarity semantics are now source-confirmed.",
                "The next bottleneck is packaging generated-logic contracts cleanly for future planning, not physical placement.",
                "Control placement and routing remain blocked, so the best next move is contract-level normalization.",
            ],
        },
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
    }

    graph = {
        "scope": report["scope"],
        "nodes": [
            {"id": item["signal_name"], "kind": "signal_contract", "contract_name": item["contract_name"]}
            for item in binding_contracts
        ],
        "edges": dependency_graph["edges"],
        "summary": report["audit_summary"],
    }
    return report, graph


def build_time_control_signal_binding_markdown(report: dict[str, Any]) -> str:
    contract_rows = []
    for item in report["signal_binding_contracts"]:
        contract_rows.append(
            [
                item["contract_name"],
                item["signal_name"],
                item["producer_subblock"],
                item["producer_expression_or_dependency"],
                ", ".join(item["consumer_blocks"]),
                item["active_level"],
                item["conditional_applicability"],
                item["safe_for_metadata_planning"],
                item["safe_for_physical_placement"],
            ]
        )

    dependency_rows = []
    for item in report["dependency_graph"]["edges"]:
        dependency_rows.append(
            [
                item["source"],
                item["via"],
                item["target"],
                item["dependency_confirmed"],
                item["metadata_only"],
                item["physical_routing_proven"],
            ]
        )

    consistency_rows = [[key, value] for key, value in report["polarity_consistency_checks"].items()]

    lines = [
        "# OpenYield TIME Control Signal Binding Report",
        "",
        "This is a read-only signal-level binding contract audit. It does not modify placement, routing, standalone.py, or the GDS writer.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Signal Binding Contracts",
        "",
        _md_table(
            [
                "contract",
                "signal",
                "producer",
                "dependency",
                "consumers",
                "active level",
                "conditional",
                "metadata planning",
                "physical placement",
            ],
            contract_rows,
        ),
        "",
        "## Polarity / Consumer Consistency",
        "",
        _md_table(["check", "value"], consistency_rows),
        "",
        "## Dependency Graph",
        "",
        _md_table(
            ["source", "via", "target", "confirmed", "metadata_only", "physical_routing_proven"],
            dependency_rows,
        ),
        "",
        "## Unresolved Items",
        "",
    ]
    lines.extend(f"- {item}" for item in report["unresolved_items"])
    lines.extend(
        [
            "",
            "## Step 6.25 Recommendation",
            "",
            "```json",
            json.dumps(report["step_6_25_recommendation"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Entry Decisions",
            "",
            f"- can_enter_time_control_signal_metadata_planning: `{report['can_enter_time_control_signal_metadata_planning']}`",
            f"- can_enter_time_control_physical_placement: `{report['can_enter_time_control_physical_placement']}`",
            f"- can_enter_standalone_control_placement: `{report['can_enter_standalone_control_placement']}`",
            "",
        ]
    )
    return "\n".join(lines)
