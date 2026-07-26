"""Build an evidence-backed OpenYield netlist-to-GDS readiness matrix."""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


READINESS_LEVELS = {
    "READY_FOR_CURRENT_HYBRID_GDS",
    "READY_FOR_METADATA_CONSUMPTION",
    "CANDIDATE_CONTRACT_ONLY",
    "PHYSICAL_CELL_EXISTS_NEEDS_PLACEMENT",
    "PHYSICAL_PLACED_NEEDS_ROUTING",
    "PHYSICAL_PLACED_NEEDS_RAIL_STITCH",
    "FALLBACK_USED",
    "MISSING_PHYSICAL_IMPLEMENTATION",
    "MISSING_SOURCE_LINK",
    "BLOCKED",
}

MATRIX_COLUMNS = [
    "module",
    "module_category",
    "openyield_source_found",
    "openyield_source_path",
    "openyield_netlist_or_semantics_status",
    "ports_or_pins_known",
    "local_adapter_or_module_found",
    "local_adapter_path",
    "physical_cell_or_gds_found",
    "physical_cell_path",
    "pin_mapping_status",
    "bbox_or_size_status",
    "placement_status",
    "row_or_array_abutment_status",
    "vdd_gnd_rail_status",
    "routing_status",
    "timing_evidence_status",
    "drc_status",
    "lvs_status",
    "used_in_current_hybrid_gds",
    "current_hybrid_status",
    "fallback_used",
    "fallback_reason",
    "readiness_level",
    "blocking_gap",
    "next_required_action",
    "evidence_files",
]


@dataclass(frozen=True)
class ModuleSpec:
    module: str
    category: str
    source_paths: tuple[str, ...]
    adapter_paths: tuple[str, ...]
    physical_paths: tuple[str, ...]
    evidence_files: tuple[str, ...]


MODULE_SPECS = [
    ModuleSpec(
        "bitcell_array",
        "storage_array",
        ("sram_compiler/subcircuits/sram_6t_core.py",),
        ("sram_layoutgen/openyield_adapter/array_aggregation.py", "sram_layoutgen/openyield_adapter/layout_prototype.py"),
        ("technology/freepdk45/gds_lib/cell_1rw.gds",),
        ("outputs/layout_prototype/hybrid_openyield/module_coverage.json", "docs/openyield_layout_prototype_generation_report.json"),
    ),
    ModuleSpec(
        "dummy_array",
        "storage_array",
        ("sram_compiler/subcircuits/dummy_row_or_column.py",),
        ("sram_layoutgen/openyield_adapter/array_aggregation.py", "sram_layoutgen/openyield_adapter/layout_prototype.py"),
        ("technology/freepdk45/gds_lib/dummy_cell_1rw.gds",),
        ("outputs/layout_prototype/hybrid_openyield/module_coverage.json",),
    ),
    ModuleSpec(
        "replica_array",
        "storage_array",
        ("sram_compiler/subcircuits/replica_column.py",),
        ("sram_layoutgen/openyield_adapter/array_aggregation.py", "sram_layoutgen/openyield_adapter/layout_prototype.py"),
        ("technology/freepdk45/gds_lib/replica_cell_1rw.gds",),
        ("outputs/layout_prototype/hybrid_openyield/module_coverage.json",),
    ),
    ModuleSpec(
        "sense_amp",
        "read_path_peripheral",
        ("sram_compiler/subcircuits/mux_and_sa.py",),
        ("sram_layoutgen/openyield_adapter/architecture_adapter.py", "sram_layoutgen/openyield_adapter/senseamp_placement.py"),
        ("technology/freepdk45/gds_lib/sense_amp.gds",),
        ("docs/openyield_senseamp_adapter_report.json", "docs/openyield_senseamp_placement_report.json", "outputs/layout_prototype/hybrid_openyield/module_coverage.json"),
    ),
    ModuleSpec(
        "write_driver",
        "write_path_peripheral",
        ("sram_compiler/subcircuits/precharge_and_write_driver.py",),
        ("sram_layoutgen/openyield_adapter/writedriver_adapter.py", "sram_layoutgen/openyield_adapter/writedriver_placement.py"),
        ("technology/freepdk45/gds_lib/write_driver.gds", "technology/freepdk45/sp_lib/write_driver.sp"),
        ("docs/openyield_writedriver_adapter_report.json", "docs/openyield_writedriver_placement_report.json", "outputs/layout_prototype/hybrid_openyield/module_coverage.json"),
    ),
    ModuleSpec(
        "column_mux",
        "read_path_peripheral",
        ("sram_compiler/subcircuits/mux_and_sa.py",),
        ("sram_layoutgen/openyield_adapter/columnmux_adapter.py", "sram_layoutgen/openyield_adapter/columnmux_placement.py"),
        ("technology/freepdk45/gds_lib/openyield_repaired/gen_col_mux_vdd_labeled.gds", "technology/freepdk45/gds_lib/openram_replacements/gen_col_mux.gds"),
        ("docs/openyield_columnmux_adapter_report.json", "docs/openyield_columnmux_placement_report.json", "docs/openyield_colmux_repaired_alias_report.json", "outputs/layout_prototype/hybrid_openyield/module_coverage.json"),
    ),
    ModuleSpec(
        "wordline_driver",
        "row_driver_peripheral",
        ("sram_compiler/subcircuits/wordline_driver.py",),
        ("sram_layoutgen/openyield_adapter/wordlinedriver_adapter.py", "sram_layoutgen/openyield_adapter/wordlinedriver_placement.py"),
        ("technology/freepdk45/gds_lib/openram_replacements/gen_wl_driver.gds", "technology/freepdk45/gds_lib/gen_wl_driver.gds"),
        ("docs/openyield_wordlinedriver_adapter_report.json", "docs/openyield_wordlinedriver_placement_report.json", "outputs/layout_prototype/hybrid_openyield/module_coverage.json"),
    ),
    ModuleSpec(
        "decoder",
        "decoder_logic",
        ("sram_compiler/subcircuits/decoder.py",),
        (
            "sram_layoutgen/openyield_adapter/decoder_row_rules.py",
            "sram_layoutgen/openyield_adapter/decoder_preplacement_feasibility.py",
            "sram_layoutgen/openyield_adapter/gate_row_packer.py",
        ),
        ("technology/freepdk45/gds_lib/openram_replacements/gen_inv.gds", "technology/freepdk45/gds_lib/openram_replacements/gen_nand2.gds"),
        ("docs/openyield_decoder_row_rule_report.json", "docs/openyield_decoder_preplacement_feasibility_report.json"),
    ),
    ModuleSpec(
        "decoder_gate_cells",
        "decoder_logic",
        ("sram_compiler/subcircuits/decoder.py", "sram_compiler/subcircuits/standard_cell.py"),
        ("sram_layoutgen/openyield_adapter/gate_row_packer.py", "sram_layoutgen/openyield_adapter/cell_rail_overlap_eligibility.py"),
        (
            "technology/freepdk45/gds_lib/openram_replacements/gen_inv.gds",
            "technology/freepdk45/gds_lib/openram_replacements/gen_nand2.gds",
            "technology/freepdk45/gds_lib/gen_nand4.gds",
        ),
        (
            "docs/openyield_decoder_row_rule_report.json",
            "docs/openyield_decoder_preplacement_feasibility_report.json",
            "docs/openyield_cell_rail_overlap_eligibility_report.json",
        ),
    ),
    ModuleSpec(
        "wordline_decoder",
        "decoder_logic",
        ("sram_compiler/subcircuits/decoder.py", "sram_compiler/subcircuits/wordline_driver.py"),
        ("sram_layoutgen/openyield_adapter/decoder_output_contracts.py", "sram_layoutgen/openyield_adapter/decoder_preplacement_feasibility.py"),
        ("technology/freepdk45/gds_lib/openram_replacements/gen_wl_driver.gds",),
        ("docs/openyield_decoder_preplacement_feasibility_report.json", "docs/openyield_decoder_row_rule_report.json"),
    ),
    ModuleSpec(
        "wordline_driver_gate_cells",
        "decoder_logic",
        ("sram_compiler/subcircuits/wordline_driver.py", "sram_compiler/subcircuits/standard_cell.py"),
        ("sram_layoutgen/openyield_adapter/gate_row_packer.py", "sram_layoutgen/openyield_adapter/wordlinedriver_adapter.py"),
        ("technology/freepdk45/gds_lib/openram_replacements/gen_wl_driver.gds",),
        ("docs/openyield_wordlinedriver_adapter_report.json", "docs/openyield_cell_rail_overlap_eligibility_report.json"),
    ),
    ModuleSpec(
        "DELAY_CHAIN",
        "time_control",
        ("sram_compiler/subcircuits/time_generate.py",),
        ("sram_layoutgen/openyield_adapter/timing_metadata_consumer.py", "sram_layoutgen/openyield_adapter/source_linked_timing_metadata.py"),
        ("technology/freepdk45/gds_lib/openram_replacements/gen_delay_inv.gds", "technology/freepdk45/gds_lib/gen_delay_inv.gds"),
        (
            "docs/openyield_source_provenance_linking_report.md",
            "docs/openyield_source_linked_timing_metadata_audit_report.json",
            "docs/openyield_timing_metadata_consumer_smoke_report.json",
            "docs/openyield_delay_chain_timing_metadata_report.json",
            "docs/openyield_delay_chain_pvt_corner_smoke_report.json",
            "outputs/layout_prototype/hybrid_openyield/module_coverage.json",
        ),
    ),
    ModuleSpec(
        "PRECHARGE",
        "time_control",
        ("sram_compiler/subcircuits/precharge_and_write_driver.py",),
        ("sram_layoutgen/openyield_adapter/control_path_candidate_generation.py", "sram_layoutgen/openyield_adapter/time_control_generated_logic_contracts.py"),
        ("technology/freepdk45/gds_lib/openram_replacements/gen_precharge.gds", "technology/freepdk45/gds_lib/gen_precharge.gds"),
        ("docs/mapping/openyield_control_timing_mapping.csv", "docs/mapping/openyield_control_path_candidate_contracts.csv", "outputs/layout_prototype/hybrid_openyield/module_coverage.json"),
    ),
    ModuleSpec(
        "PRECHARGE_ENABLE_PATH",
        "time_control",
        ("sram_compiler/subcircuits/time_generate.py",),
        ("sram_layoutgen/openyield_adapter/control_path_candidate_generation.py", "sram_layoutgen/openyield_adapter/time_control_generated_logic_contracts.py"),
        (),
        ("docs/mapping/openyield_control_timing_mapping.csv", "docs/mapping/openyield_control_path_candidate_contracts.csv", "outputs/layout_prototype/hybrid_openyield/module_coverage.json"),
    ),
    ModuleSpec(
        "SENSE_ENABLE_PATH",
        "time_control",
        ("sram_compiler/subcircuits/time_generate.py",),
        ("sram_layoutgen/openyield_adapter/control_path_candidate_generation.py", "sram_layoutgen/openyield_adapter/time_control_signal_bindings.py"),
        (),
        ("docs/mapping/openyield_control_timing_mapping.csv", "docs/mapping/openyield_control_path_candidate_contracts.csv", "outputs/layout_prototype/hybrid_openyield/module_coverage.json"),
    ),
    ModuleSpec(
        "WRITE_ENABLE_PATH",
        "time_control",
        ("sram_compiler/subcircuits/time_generate.py",),
        ("sram_layoutgen/openyield_adapter/control_path_candidate_generation.py", "sram_layoutgen/openyield_adapter/time_control_signal_bindings.py"),
        (),
        ("docs/mapping/openyield_control_timing_mapping.csv", "docs/mapping/openyield_control_path_candidate_contracts.csv", "outputs/layout_prototype/hybrid_openyield/module_coverage.json"),
    ),
    ModuleSpec(
        "WORDLINE_ENABLE_PATH",
        "time_control",
        ("sram_compiler/subcircuits/time_generate.py",),
        ("sram_layoutgen/openyield_adapter/control_path_candidate_generation.py", "sram_layoutgen/openyield_adapter/time_control_signal_bindings.py"),
        (),
        ("docs/mapping/openyield_control_timing_mapping.csv", "docs/mapping/openyield_control_path_candidate_contracts.csv", "outputs/layout_prototype/hybrid_openyield/module_coverage.json"),
    ),
    ModuleSpec(
        "GATED_CLOCK_PATH",
        "time_control",
        ("sram_compiler/subcircuits/time_generate.py",),
        ("sram_layoutgen/openyield_adapter/control_path_candidate_generation.py", "sram_layoutgen/openyield_adapter/time_control_signal_bindings.py"),
        (),
        ("docs/mapping/openyield_control_timing_mapping.csv", "docs/mapping/openyield_control_path_candidate_contracts.csv", "outputs/layout_prototype/hybrid_openyield/module_coverage.json"),
    ),
    ModuleSpec(
        "DFF_ROW",
        "time_control",
        ("sram_compiler/subcircuits/time_generate.py", "sram_compiler/subcircuits/standard_cell.py"),
        ("sram_layoutgen/openyield_adapter/dff_array_adapter.py", "sram_layoutgen/openyield_adapter/dff_array_placement.py"),
        ("technology/freepdk45/gds_lib/dff.gds", "technology/freepdk45/sp_lib/dff.sp"),
        ("docs/openyield_dff_array_adapter_report.json", "docs/mapping/openyield_control_path_candidate_contracts.csv", "outputs/layout_prototype/hybrid_openyield/module_coverage.json"),
    ),
    ModuleSpec("routing", "integration", (), ("sram_layoutgen/standalone.py",), (), ("docs/openyield_layout_prototype_generation_report.json",)),
    ModuleSpec("power_rail_stitching", "integration", (), ("sram_layoutgen/openyield_adapter/hardcell_power_rail_continuity.py",), (), ("docs/openyield_hardcell_power_rail_continuity_report.json", "docs/openyield_cell_rail_overlap_eligibility_report.json")),
    ModuleSpec("GDS_writer", "integration", (), ("sram_layoutgen/gds_writer.py",), (), ("docs/openyield_layout_prototype_generation_report.json",)),
    ModuleSpec("DRC", "signoff", (), ("sram_layoutgen/signoff.py", "sram_layoutgen/verifier.py"), ("technology/freepdk45/tech/freepdk45.lydrc",), ("docs/openyield_layout_prototype_generation_report.json",)),
    ModuleSpec("LVS", "signoff", (), ("sram_layoutgen/signoff.py", "sram_layoutgen/verifier.py"), ("technology/freepdk45/tech/freepdk45.lylvs",), ("docs/openyield_layout_prototype_generation_report.json",)),
    ModuleSpec("timing", "signoff", ("sram_compiler/subcircuits/time_generate.py",), ("sram_layoutgen/openyield_adapter/timing_metadata_consumer.py",), (), ("docs/openyield_delay_chain_timing_metadata_report.json", "docs/openyield_timing_metadata_consumer_smoke_report.json", "docs/openyield_layout_prototype_generation_report.json")),
]


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def _load_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _join_existing(root: Path, rel_paths: tuple[str, ...]) -> tuple[bool, str]:
    found = []
    for rel in rel_paths:
        path = root / rel
        if path.exists():
            found.append(rel)
    return bool(found), ";".join(found)


def _join_repo_or_external(repo_root: Path, openyield_root: Path, rel_paths: tuple[str, ...], *, external: bool = False) -> tuple[bool, str]:
    base = openyield_root if external else repo_root
    return _join_existing(base, rel_paths)


def _module_coverage_map(path: Path) -> dict[str, dict[str, Any]]:
    rows = _load_json(path) or []
    return {str(row["module_or_object"]): row for row in rows}


def _csv_map(path: Path, key: str) -> dict[str, dict[str, str]]:
    return {str(row[key]): row for row in _load_csv_rows(path)}


def _find_report_value(payload: dict[str, Any] | None, *keys: str, default: Any = None) -> Any:
    cur: Any = payload
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def build_readiness_report(repo_root: str | Path, openyield_root: str | Path, module_coverage_path: str | Path) -> dict[str, Any]:
    repo = Path(repo_root).resolve()
    openyield = Path(openyield_root).resolve()
    coverage_path = (repo / module_coverage_path).resolve() if not Path(module_coverage_path).is_absolute() else Path(module_coverage_path).resolve()

    coverage = _module_coverage_map(coverage_path)
    layout_report = _load_json(repo / "docs/openyield_layout_prototype_generation_report.json") or {}
    timing_audit = _load_json(repo / "docs/openyield_source_linked_timing_metadata_audit_report.json") or {}
    timing_consumer = _load_json(repo / "docs/openyield_timing_metadata_consumer_smoke_report.json") or {}
    delay_timing = _load_json(repo / "docs/openyield_delay_chain_timing_metadata_report.json") or {}
    decoder_row = _load_json(repo / "docs/openyield_decoder_row_rule_report.json") or {}
    decoder_pre = _load_json(repo / "docs/openyield_decoder_preplacement_feasibility_report.json") or {}
    dff_adapter = _load_json(repo / "docs/openyield_dff_array_adapter_report.json") or {}
    rail_report = _load_json(repo / "docs/openyield_hardcell_power_rail_continuity_report.json") or {}
    colmux_report = _load_json(repo / "docs/openyield_columnmux_adapter_report.json") or {}
    writedriver_report = _load_json(repo / "docs/openyield_writedriver_adapter_report.json") or {}
    wl_driver_report = _load_json(repo / "docs/openyield_wordlinedriver_adapter_report.json") or {}
    senseamp_report = _load_json(repo / "docs/openyield_senseamp_adapter_report.json") or {}
    control_mapping = _csv_map(repo / "docs/mapping/openyield_control_timing_mapping.csv", "openyield_object")
    control_contracts = _csv_map(repo / "docs/mapping/openyield_control_path_candidate_contracts.csv", "control_object")

    current_hybrid_gds = repo / "outputs/layout_prototype/hybrid_openyield/hybrid_openyield_prototype.gds"

    rows = []
    for spec in MODULE_SPECS:
        coverage_row = coverage.get(spec.module, {})
        source_found, source_path = _join_repo_or_external(repo, openyield, spec.source_paths, external=True)
        adapter_found, adapter_path = _join_repo_or_external(repo, openyield, spec.adapter_paths)
        physical_found, physical_path = _join_repo_or_external(repo, openyield, spec.physical_paths)
        evidence_found, evidence_path = _join_repo_or_external(repo, openyield, spec.evidence_files)
        row = {
            "module": spec.module,
            "module_category": spec.category,
            "openyield_source_found": source_found,
            "openyield_source_path": source_path,
            "openyield_netlist_or_semantics_status": "unknown",
            "ports_or_pins_known": "unknown",
            "local_adapter_or_module_found": adapter_found,
            "local_adapter_path": adapter_path,
            "physical_cell_or_gds_found": physical_found,
            "physical_cell_path": physical_path,
            "pin_mapping_status": "unknown",
            "bbox_or_size_status": "unknown",
            "placement_status": "unknown",
            "row_or_array_abutment_status": "unknown",
            "vdd_gnd_rail_status": "unknown",
            "routing_status": "unknown",
            "timing_evidence_status": "unknown",
            "drc_status": "not_claimed",
            "lvs_status": "not_claimed",
            "used_in_current_hybrid_gds": bool(coverage_row.get("used_in_gds", False)),
            "current_hybrid_status": "not_in_current_hybrid",
            "fallback_used": bool(coverage_row.get("fallback_used", False)),
            "fallback_reason": str(coverage_row.get("fallback_reason", "")),
            "readiness_level": "BLOCKED",
            "blocking_gap": "needs_module_specific_readiness_classification",
            "next_required_action": str(coverage_row.get("next_required_action", "derive from evidence")),
            "evidence_files": evidence_path if evidence_found else "",
        }

        _classify_row(
            row,
            coverage_row,
            control_mapping.get(spec.module, {}),
            control_contracts.get(spec.module, {}),
            timing_audit=timing_audit,
            timing_consumer=timing_consumer,
            delay_timing=delay_timing,
            decoder_row=decoder_row,
            decoder_pre=decoder_pre,
            dff_adapter=dff_adapter,
            rail_report=rail_report,
            colmux_report=colmux_report,
            writedriver_report=writedriver_report,
            wl_driver_report=wl_driver_report,
            senseamp_report=senseamp_report,
        )
        assert row["readiness_level"] in READINESS_LEVELS, row
        rows.append(row)

    blockers = [
        {
            "blocking_gap": "TIME/DFF/control logic are not physical-ready",
            "why_it_blocks_full_gds": "DELAY_CHAIN is metadata-only and PRECHARGE/enable-path/DFF control objects remain fallback or candidate-contract only, so full OpenYield time-control replacement is unavailable.",
            "minimum_fix": "Close DFF row placement hooks and convert candidate control-path contracts into physical leaf-to-placement mappings.",
            "recommended_next_task": "Start with decoder/gate-row abutment plus DFF/control-row placement contract closure before any full control replacement claim.",
        },
        {
            "blocking_gap": "DELAY_CHAIN lacks proven physical integration",
            "why_it_blocks_full_gds": "Timing metadata is consumable, but the current hybrid still uses a legacy delay-chain macro path and no OpenYield physical placement/routing is claimed.",
            "minimum_fix": "Add a guarded physical representation and placement hook for DELAY_CHAIN without changing legacy default behavior.",
            "recommended_next_task": "Implement delay-chain physical gap closure after decoder row work.",
        },
        {
            "blocking_gap": "PRECHARGE has source-linked smoke evidence but no OpenYield physical integration",
            "why_it_blocks_full_gds": "Current hybrid falls back to legacy gen_precharge usage and the OpenYield-side PRECHARGE path has not been physically connected into the layout flow.",
            "minimum_fix": "Define PRECHARGE physical hook, validate polarity, and bind it into placement metadata.",
            "recommended_next_task": "Do precharge physical representation / placement hook after DELAY_CHAIN.",
        },
        {
            "blocking_gap": "Enable paths and gated clock remain candidate-contract only",
            "why_it_blocks_full_gds": "PRECHARGE_ENABLE_PATH, SENSE_ENABLE_PATH, WRITE_ENABLE_PATH, WORDLINE_ENABLE_PATH, and GATED_CLOCK_PATH have no physical placement/routing implementation.",
            "minimum_fix": "Recover/bind leaf cells, validate pins, and add placement-ready control path mappings.",
            "recommended_next_task": "Physical mapping for enable-path control logic.",
        },
        {
            "blocking_gap": "Decoder and gate rows are not signoff-ready",
            "why_it_blocks_full_gds": "Decoder row rules and preplacement are metadata/proxy based; routing, legal physical placement, and zero-risk handoff are unproven.",
            "minimum_fix": "Turn decoder gate rows into a guarded placement-capable row domain with rail and handoff proof.",
            "recommended_next_task": "Decoder/gate row abutment and rail stitching audit.",
        },
        {
            "blocking_gap": "VDD/GND rail continuity is not globally proven",
            "why_it_blocks_full_gds": "Peripheral macros such as sense_amp, write_driver, column_mux, gen_precharge, and many gate rows still lack across-abutment continuity proof or shared-rail safety.",
            "minimum_fix": "Audit and stitch row/domain rail continuity before enabling shared rail assumptions.",
            "recommended_next_task": "Power rail continuity verification and selective stitching.",
        },
        {
            "blocking_gap": "Routing is still legacy",
            "why_it_blocks_full_gds": "Current hybrid uses legacy top-level routing rather than OpenYield-driven control/peripheral routing.",
            "minimum_fix": "Replace or compact legacy routing for OpenYield-driven control/peripheral domains.",
            "recommended_next_task": "Routing compaction / routing replacement after placement and rail closure.",
        },
        {
            "blocking_gap": "DRC/LVS/timing closure are not claimed",
            "why_it_blocks_full_gds": "Reports explicitly forbid claiming full-chip DRC clean, LVS clean, or timing closure now.",
            "minimum_fix": "Run guarded sanity/signoff passes after physical integration is materially complete.",
            "recommended_next_task": "DRC/LVS sanity and timing closure audit after routing closure.",
        },
    ]

    next_action_priority = [
        {
            "priority": 1,
            "target_module": "decoder_gate_cells",
            "reason": "Decoder gate rows already have leaf-cell, row-packing, and metadata feasibility evidence, so this is the highest-leverage path to convert proxies into placement-ready control logic.",
            "expected_result": "Guarded decoder/gate-row abutment with clearer rail continuity and reduced ambiguity for downstream control placement.",
            "files_to_modify": "sram_layoutgen/openyield_adapter/gate_row_packer.py;sram_layoutgen/openyield_adapter/decoder_*;tests/test_openyield_gate_row_vertical_abutment.py",
            "risk_level": "medium",
            "whether_affects_legacy_default": "False",
            "estimated_gate_after_completion": "can_enter_decoder_gate_row_abutment=True with fewer placement blockers",
        },
        {
            "priority": 2,
            "target_module": "DELAY_CHAIN",
            "reason": "DELAY_CHAIN is the only control object already admitted for metadata consumption, so adding a physical hook closes a concrete gap rather than starting from candidate-only state.",
            "expected_result": "DELAY_CHAIN transitions from metadata-only to placement-hook-ready without changing legacy default mode.",
            "files_to_modify": "sram_layoutgen/openyield_adapter/timing_metadata_consumer.py;sram_layoutgen/openyield_adapter/time_control_*;tests/test_openyield_timing_metadata_consumer.py",
            "risk_level": "medium",
            "whether_affects_legacy_default": "False",
            "estimated_gate_after_completion": "can_enter_delay_chain_physical_gap_closure=True with a concrete placement representation",
        },
        {
            "priority": 3,
            "target_module": "PRECHARGE",
            "reason": "PRECHARGE already has source-linked candidate smoke and a local macro; the missing step is physical hook closure rather than source discovery.",
            "expected_result": "PRECHARGE moves from candidate/spice-only into guarded physical placement readiness.",
            "files_to_modify": "sram_layoutgen/openyield_adapter/time_control_generated_logic_contracts.py;sram_layoutgen/openyield_adapter/control_path_candidate_generation.py;tests/test_openyield_precharge_spice_smoke.py",
            "risk_level": "medium",
            "whether_affects_legacy_default": "False",
            "estimated_gate_after_completion": "can_enter_precharge_physical_gap_closure=True with a physical placement hook",
        },
        {
            "priority": 4,
            "target_module": "PRECHARGE_ENABLE_PATH/SENSE_ENABLE_PATH/WRITE_ENABLE_PATH/WORDLINE_ENABLE_PATH/GATED_CLOCK_PATH",
            "reason": "These remain candidate-contract-only and block full control replacement.",
            "expected_result": "Control-path leaf binding and placement-ready mapping.",
            "files_to_modify": "sram_layoutgen/openyield_adapter/control_path_candidate_generation.py;sram_layoutgen/openyield_adapter/time_control_signal_bindings.py",
            "risk_level": "high",
            "whether_affects_legacy_default": "False",
            "estimated_gate_after_completion": "candidate_contract_only_modules_count decreases",
        },
        {
            "priority": 5,
            "target_module": "routing",
            "reason": "Current hybrid still uses legacy routing even when modules are OpenYield-driven.",
            "expected_result": "Reduced dependence on legacy top-level routing for OpenYield domains.",
            "files_to_modify": "sram_layoutgen/standalone.py;sram_layoutgen/*routing*",
            "risk_level": "high",
            "whether_affects_legacy_default": "Potentially",
            "estimated_gate_after_completion": "can_enter_routing_compaction=True with lower blocker severity",
        },
        {
            "priority": 6,
            "target_module": "power_rail_stitching",
            "reason": "Shared-rail continuity remains explicitly unproven across peripherals and control rows.",
            "expected_result": "Sharper proof of rail continuity and safer row-abutment claims.",
            "files_to_modify": "sram_layoutgen/openyield_adapter/hardcell_power_rail_continuity.py;sram_layoutgen/openyield_adapter/cell_rail_overlap_eligibility.py",
            "risk_level": "medium",
            "whether_affects_legacy_default": "False",
            "estimated_gate_after_completion": "can_enter_power_rail_stitching_verification=True with narrower unresolved set",
        },
        {
            "priority": 7,
            "target_module": "DRC/LVS/timing",
            "reason": "Signoff should only be attempted after major physical gaps are closed.",
            "expected_result": "Guarded sanity evidence without overclaiming closure.",
            "files_to_modify": "sram_layoutgen/signoff.py;sram_layoutgen/verifier.py;scripts/*signoff*",
            "risk_level": "medium",
            "whether_affects_legacy_default": "False",
            "estimated_gate_after_completion": "drc/lvs/timing blocker language can become more specific",
        },
    ]

    ready_for_current_hybrid = [row["module"] for row in rows if row["readiness_level"] == "READY_FOR_CURRENT_HYBRID_GDS"]
    metadata_only = [row["module"] for row in rows if row["readiness_level"] == "READY_FOR_METADATA_CONSUMPTION"]
    candidate_only = [row["module"] for row in rows if row["readiness_level"] == "CANDIDATE_CONTRACT_ONLY"]
    missing_physical = [row["module"] for row in rows if row["readiness_level"] == "MISSING_PHYSICAL_IMPLEMENTATION"]

    report = {
        "scope": "openyield_netlist_to_gds_readiness",
        "repo_root": str(repo),
        "openyield_root": str(openyield),
        "current_hybrid_gds_path": _rel(current_hybrid_gds, repo),
        "current_gds_generatable_modules": ready_for_current_hybrid,
        "fallback_modules": list(layout_report.get("fallback_modules", [])),
        "blocking_gaps_for_full_openyield_gds": blockers,
        "next_action_priority": next_action_priority,
        "matrix_rows": rows,
        "gates": {
            "netlist_to_gds_readiness_matrix_available": True,
            "module_readiness_rows_count": len(rows),
            "current_hybrid_gds_available": current_hybrid_gds.exists(),
            "current_hybrid_gds_path": _rel(current_hybrid_gds, repo),
            "openyield_driven_modules_count": len(layout_report.get("openyield_driven_modules", [])),
            "fallback_modules_count": len(layout_report.get("fallback_modules", [])),
            "ready_for_current_hybrid_modules": ready_for_current_hybrid,
            "metadata_only_modules": metadata_only,
            "candidate_contract_only_modules": candidate_only,
            "missing_physical_implementation_modules": missing_physical,
            "full_openyield_gds_blockers_identified": True,
            "next_action_priority_available": True,
            "can_enter_decoder_gate_row_abutment": True,
            "can_enter_delay_chain_physical_gap_closure": True,
            "can_enter_precharge_physical_gap_closure": True,
            "can_enter_power_rail_stitching_verification": True,
            "can_enter_routing_compaction": True,
            "can_claim_full_openyield_gds_now": False,
            "can_claim_drc_clean_now": False,
            "can_claim_lvs_clean_now": False,
            "can_claim_timing_closure_now": False,
        },
    }
    return report


def _classify_row(
    row: dict[str, Any],
    coverage_row: dict[str, Any],
    mapping_row: dict[str, str],
    contract_row: dict[str, str],
    **reports: Any,
) -> None:
    module = row["module"]
    used = row["used_in_current_hybrid_gds"]
    fallback = row["fallback_used"]
    coverage_source = str(coverage_row.get("source", ""))

    if module in {"bitcell_array", "dummy_array", "replica_array"}:
        row.update(
            openyield_netlist_or_semantics_status="source_linked_storage_array_aggregation",
            ports_or_pins_known="array_role_known_from_layout_prototype",
            pin_mapping_status="array_hardcell_binding_known",
            bbox_or_size_status="hardcell_array_dimensions_known",
            placement_status=str(coverage_row.get("placement_status", "openyield_storage_opt_in")),
            row_or_array_abutment_status="array_abutment_in_current_hybrid",
            vdd_gnd_rail_status=str(coverage_row.get("power_status", "bundled_freepdk45_power_rails")),
            routing_status=str(coverage_row.get("routing_status", "array_abutment")),
            timing_evidence_status="not_a_time_control_object",
            drc_status="no_full_openyield_drc_claim",
            lvs_status="no_full_openyield_lvs_claim",
            current_hybrid_status="OpenYield-driven storage aggregation" if used and not fallback else "legacy",
            readiness_level="READY_FOR_CURRENT_HYBRID_GDS",
            blocking_gap="non-storage peripherals remain incomplete for full OpenYield GDS",
        )
        return

    if module == "sense_amp":
        row.update(
            openyield_netlist_or_semantics_status="semantic_adapter_ready_single_ended_q_to_dout",
            ports_or_pins_known="VDD,VSS,EN,IN,INB,Q,QB contract known",
            pin_mapping_status="usable_direct_pin_mapping_qb_dropped",
            bbox_or_size_status="local_sense_amp_bbox_known",
            placement_status="adapter_placement_plan_available",
            row_or_array_abutment_status="column_direct_not_row_abutted",
            vdd_gnd_rail_status="side_rails_present_across_abutment_unproven",
            routing_status=str(coverage_row.get("routing_status", "legacy_top_level_routing")),
            timing_evidence_status="semantic_adapter_only_not_timing_closure",
            current_hybrid_status="OpenYield-driven semantic adapter",
            readiness_level="READY_FOR_CURRENT_HYBRID_GDS",
            blocking_gap="read-path fanout/timing proof and rail continuity remain incomplete",
        )
        return

    if module == "write_driver":
        row.update(
            openyield_netlist_or_semantics_status="source_and_adapter_semantics_confirmed",
            ports_or_pins_known="VDD,VSS,EN,DIN,BL,BLB contract known",
            pin_mapping_status="usable_semantic_alias_blb_to_br",
            bbox_or_size_status="write_driver_bbox_known",
            placement_status="limited_adapter_placement_available",
            row_or_array_abutment_status="no_shared_rail_row_abutment_claim",
            vdd_gnd_rail_status="vdd_gnd_present_shared_rail_disabled",
            routing_status=str(coverage_row.get("routing_status", "legacy_top_level_routing")),
            timing_evidence_status="not_timing_closed",
            current_hybrid_status="OpenYield-driven adapter",
            readiness_level="READY_FOR_CURRENT_HYBRID_GDS",
            blocking_gap="shared rail continuity and grouped write-path proof remain incomplete",
        )
        return

    if module == "column_mux":
        row.update(
            openyield_netlist_or_semantics_status="adapter_semantics_confirmed_repaired_alias_used",
            ports_or_pins_known="VDD,VSS,SEL,BL,BLB,OUT,OUTB contract known",
            pin_mapping_status="usable_repaired_alias_vdd_metadata_incomplete",
            bbox_or_size_status="column_mux_bbox_known_from_repaired_alias",
            placement_status="limited_adapter_placement_available",
            row_or_array_abutment_status="shared_rail_not_enabled",
            vdd_gnd_rail_status="gnd_proven_vdd_metadata_missing_shared_rail_disabled",
            routing_status=str(coverage_row.get("routing_status", "legacy_top_level_routing")),
            timing_evidence_status="not_timing_closed",
            current_hybrid_status="OpenYield-driven repaired alias",
            readiness_level="READY_FOR_CURRENT_HYBRID_GDS",
            blocking_gap="VDD metadata and shared rail continuity are still not proven",
        )
        return

    if module == "wordline_driver":
        row.update(
            openyield_netlist_or_semantics_status="source_semantics_confirmed_active_high",
            ports_or_pins_known="VDD,VSS,A,B,Z contract known",
            pin_mapping_status="usable_semantic_alias_a_b_z_confirmed",
            bbox_or_size_status="wordline_driver_bbox_known",
            placement_status="limited_adapter_placement_available",
            row_or_array_abutment_status="row_driver_placement_plan_only",
            vdd_gnd_rail_status="vdd_gnd_present_shared_rail_disabled",
            routing_status=str(coverage_row.get("routing_status", "legacy_top_level_routing")),
            timing_evidence_status="not_timing_closed",
            current_hybrid_status="OpenYield-driven adapter",
            readiness_level="READY_FOR_CURRENT_HYBRID_GDS",
            blocking_gap="downstream TIME/control physical decomposition and rail proof remain open",
        )
        return

    if module == "DELAY_CHAIN":
        row.update(
            openyield_netlist_or_semantics_status="source_linked_delay_chain_timing_metadata_available",
            ports_or_pins_known="DelayChain VDD,VSS,in,out and rbl->rbl_delay usage proven",
            pin_mapping_status="metadata_consumer_api_ready_no_physical_pin_mapping_claim",
            bbox_or_size_status="leaf_bbox_known_but_chain_placement_not_enabled",
            placement_status=str(coverage_row.get("placement_status", "legacy_fallback_control_timing")),
            row_or_array_abutment_status="not_physically_integrated",
            vdd_gnd_rail_status="leaf_rail_geometry_exists_but_chain_integration_unproven",
            routing_status=str(coverage_row.get("routing_status", "legacy_top_level_routing")),
            timing_evidence_status=str(mapping_row.get("evidence_status", "source_linked_and_smoke_timing_metadata_available")),
            current_hybrid_status="legacy fallback with metadata consumer",
            readiness_level="READY_FOR_METADATA_CONSUMPTION",
            blocking_gap="timing metadata is consumable but there is no physical DELAY_CHAIN integration in layoutgen",
            next_required_action=str(mapping_row.get("next_required_action", row["next_required_action"])),
        )
        return

    if module == "PRECHARGE":
        row.update(
            openyield_netlist_or_semantics_status="source_linked_precharge_candidate_with_smoke_only",
            ports_or_pins_known="PRECHARGE VDD,ENB,BL,BLB contract known",
            pin_mapping_status="candidate_only_en_bar_alias_known_not_physically_integrated",
            bbox_or_size_status="gen_precharge_bbox_known",
            placement_status=str(coverage_row.get("placement_status", "legacy_fallback_precharge_row")),
            row_or_array_abutment_status="precharge_row_not_openyield_driven",
            vdd_gnd_rail_status="vdd_only_exception_no_physical_ready_rail_proof",
            routing_status=str(coverage_row.get("routing_status", "legacy_top_level_routing")),
            timing_evidence_status=str(mapping_row.get("evidence_status", "source_linked_candidate_spice_smoke_available")),
            current_hybrid_status="legacy fallback precharge row",
            readiness_level="CANDIDATE_CONTRACT_ONLY",
            blocking_gap="local gen_precharge exists but OpenYield PRECHARGE is not physically integrated into placement/routing",
            next_required_action=str(mapping_row.get("next_required_action", row["next_required_action"])),
        )
        return

    if module in {"PRECHARGE_ENABLE_PATH", "SENSE_ENABLE_PATH", "WRITE_ENABLE_PATH", "WORDLINE_ENABLE_PATH", "GATED_CLOCK_PATH"}:
        row.update(
            openyield_netlist_or_semantics_status="source_linked_candidate_contract_only",
            ports_or_pins_known=str(contract_row.get("source_ports_or_nodes", "candidate contract known")),
            pin_mapping_status="candidate_contract_only_no_physical_pin_mapping",
            bbox_or_size_status="no_physical_bbox_for_control_path",
            placement_status=str(coverage_row.get("placement_status", "legacy_fallback_control_logic")),
            row_or_array_abutment_status="no_control_path_physical_abutment",
            vdd_gnd_rail_status="no_control_path_physical_rail_proof",
            routing_status=str(coverage_row.get("routing_status", "legacy_top_level_routing")),
            timing_evidence_status=str(mapping_row.get("evidence_status", "source_linked_candidate_contract_available")),
            current_hybrid_status="legacy fallback control logic",
            readiness_level="CANDIDATE_CONTRACT_ONLY",
            blocking_gap="candidate contract exists, but no physical-ready OpenYield implementation or placement hook is present",
            next_required_action=str(mapping_row.get("next_required_action", row["next_required_action"])),
        )
        return

    if module == "DFF_ROW":
        row.update(
            openyield_netlist_or_semantics_status="dff_leaf_semantics_mappable_metadata_only",
            ports_or_pins_known="VDD,VSS,D,Q,CLK plus row semantics known",
            pin_mapping_status="dff_leaf_mapping_matched_but_row_integration_not_enabled",
            bbox_or_size_status="dff_bbox_known",
            placement_status="metadata_only_dff_row",
            row_or_array_abutment_status="dff_row_abutment_unproven_for_main_flow",
            vdd_gnd_rail_status="shared_rail_disabled_row_continuity_unproven",
            routing_status=str(coverage_row.get("routing_status", "legacy_top_level_routing")),
            timing_evidence_status=str(mapping_row.get("evidence_status", "source_linked_candidate_contract_available")),
            current_hybrid_status="legacy fallback control logic",
            readiness_level="CANDIDATE_CONTRACT_ONLY",
            blocking_gap="DFF leaf mapping exists, but DFF_ROW is still metadata-only and not physically integrated into the hybrid flow",
            next_required_action=str(mapping_row.get("next_required_action", row["next_required_action"])),
        )
        return

    if module == "decoder":
        row.update(
            openyield_netlist_or_semantics_status="decoder_hierarchy_and_stage_rules_known",
            ports_or_pins_known="decoder input/output ordering known from row-rule audit",
            pin_mapping_status="partial_proxy_level_only",
            bbox_or_size_status="metadata_bbox_proxy_only",
            placement_status="preplacement_proxy_only_not_legal_physical_placement",
            row_or_array_abutment_status="decoder_rows_not_physically_proven",
            vdd_gnd_rail_status="power_policy_defined_but_continuity_unproven",
            routing_status="internal_decoder_routing_unproven",
            timing_evidence_status="decoder_metadata_only_no_closure",
            current_hybrid_status="not_openyield_driven_in_current_hybrid",
            readiness_level="PHYSICAL_CELL_EXISTS_NEEDS_PLACEMENT",
            blocking_gap="decoder remains at proxy-row / metadata stage and cannot be treated as legal physical placement",
            next_required_action="convert decoder bbox proxies into guarded placement-capable rows with pin-side and handoff proof",
        )
        return

    if module == "decoder_gate_cells":
        row.update(
            openyield_netlist_or_semantics_status="gate_row_leaf_cells_known_with_opt_in_packing",
            ports_or_pins_known="gen_inv/gen_nand2/gen_nand4 metadata known; gen_nand3 still missing",
            pin_mapping_status="partial_leaf_pin_metadata_with_missing_gen_nand3",
            bbox_or_size_status="leaf_bbox_known",
            placement_status="explicit_opt_in_gate_row_packing_available",
            row_or_array_abutment_status="vertical_abutment_available_not_main_flow_default",
            vdd_gnd_rail_status="rail_overlap_partially_classified_composite_continuity_unproven",
            routing_status="gate_rows_packed_but_routing_unproven",
            timing_evidence_status="decoder_metadata_only_no_timing_closure",
            current_hybrid_status="not_used_in_current_hybrid_prototype_baseline",
            readiness_level="PHYSICAL_PLACED_NEEDS_RAIL_STITCH",
            blocking_gap="gate rows can be packed, but composite rail continuity, gen_nand3 replacement policy, and routed handoff proof remain incomplete",
            next_required_action="decoder/gate row abutment and rail stitching verification",
        )
        return

    if module == "wordline_decoder":
        row.update(
            openyield_netlist_or_semantics_status="wordline handoff semantics known",
            ports_or_pins_known="wordline group outputs and enable-bus mapping known",
            pin_mapping_status="partial_wordline_handoff_proxy_only",
            bbox_or_size_status="metadata_bbox_proxy_only",
            placement_status="preplacement_proxy_only_not_legal_physical_placement",
            row_or_array_abutment_status="wordline handoff windows are metadata-only",
            vdd_gnd_rail_status="power policy metadata only",
            routing_status="tight_zero_margin_handoff_budget_unrouted",
            timing_evidence_status="no_wordline_decoder_timing_closure",
            current_hybrid_status="not_openyield_driven_in_current_hybrid",
            readiness_level="PHYSICAL_CELL_EXISTS_NEEDS_PLACEMENT",
            blocking_gap="wordline decoder handoff is proxy-based with zero margin and no routed geometry",
            next_required_action="relieve wordline handoff budget and prove legal placement before physical integration",
        )
        return

    if module == "wordline_driver_gate_cells":
        row.update(
            openyield_netlist_or_semantics_status="wordline-driver leaf semantics confirmed",
            ports_or_pins_known="A/B/Z plus vdd/gnd confirmed",
            pin_mapping_status="leaf_pin_mapping_confirmed",
            bbox_or_size_status="leaf_bbox_known",
            placement_status="limited_row_driver_placement_plan_available",
            row_or_array_abutment_status="row packing possible_shared_rail_disabled",
            vdd_gnd_rail_status="leaf_vdd_gnd_present_across_row_continuity_unproven",
            routing_status="wordline_driver_rows_not_routing_closed",
            timing_evidence_status="no_time_control_timing_closure",
            current_hybrid_status="not_separately_materialized_in_current_hybrid",
            readiness_level="PHYSICAL_PLACED_NEEDS_RAIL_STITCH",
            blocking_gap="wordline-driver leaves are mapped, but row-abutment rail continuity and routed integration are not proven",
            next_required_action="fold wordline-driver leaves into decoder/control row abutment and rail audit",
        )
        return

    if module == "routing":
        row.update(
            openyield_netlist_or_semantics_status="not_an_openyield_leaf_module",
            ports_or_pins_known="not_applicable",
            pin_mapping_status="not_applicable",
            bbox_or_size_status="not_applicable",
            placement_status="legacy_routing_only",
            row_or_array_abutment_status="not_applicable",
            vdd_gnd_rail_status="depends_on_unfinished_physical_domains",
            routing_status="legacy_top_level_routing_still_active",
            timing_evidence_status="routing_not_timing_closed",
            current_hybrid_status="legacy routing retained",
            readiness_level="BLOCKED",
            blocking_gap="current hybrid still depends on legacy top-level routing rather than OpenYield-driven routing",
            next_required_action="replace or compact legacy routing after control/peripheral placement closure",
        )
        return

    if module == "power_rail_stitching":
        row.update(
            openyield_netlist_or_semantics_status="not_an_openyield_leaf_module",
            ports_or_pins_known="power-rail geometry partially inventoried",
            pin_mapping_status="not_applicable",
            bbox_or_size_status="macro rail geometry partially known",
            placement_status="verification_only",
            row_or_array_abutment_status="some_row_abutment_evidence_exists",
            vdd_gnd_rail_status="global continuity unproven",
            routing_status="depends_on_unfinished_domains",
            timing_evidence_status="not_applicable",
            current_hybrid_status="verification gate only",
            readiness_level="BLOCKED",
            blocking_gap="shared rail continuity is not globally proven across peripherals and control rows",
            next_required_action="run rail continuity verification and selective stitching for decoder/control/peripheral domains",
        )
        return

    if module == "GDS_writer":
        row.update(
            openyield_netlist_or_semantics_status="not_an_openyield_leaf_module",
            ports_or_pins_known="not_applicable",
            pin_mapping_status="not_applicable",
            bbox_or_size_status="not_applicable",
            placement_status="legacy_writer_retained",
            row_or_array_abutment_status="not_applicable",
            vdd_gnd_rail_status="not_applicable",
            routing_status="writer unchanged",
            timing_evidence_status="not_applicable",
            current_hybrid_status="legacy writer retained",
            readiness_level="BLOCKED",
            blocking_gap="current reports deliberately keep gds_writer unchanged and do not prove a full OpenYield writer path",
            next_required_action="avoid writer work until physical integration justifies it",
        )
        return

    if module == "DRC":
        row.update(
            openyield_netlist_or_semantics_status="signoff_capability",
            ports_or_pins_known="not_applicable",
            pin_mapping_status="not_applicable",
            bbox_or_size_status="signoff_deck_available",
            placement_status="not_applicable",
            row_or_array_abutment_status="depends_on_physical_completion",
            vdd_gnd_rail_status="depends_on_physical_completion",
            routing_status="depends_on_physical_completion",
            timing_evidence_status="not_applicable",
            current_hybrid_status="cannot_claim_drc_clean_now",
            readiness_level="BLOCKED",
            blocking_gap="full-chip OpenYield DRC clean is explicitly not claimed",
            next_required_action="run guarded DRC sanity only after placement/routing/rail closure",
        )
        return

    if module == "LVS":
        row.update(
            openyield_netlist_or_semantics_status="signoff_capability",
            ports_or_pins_known="not_applicable",
            pin_mapping_status="not_applicable",
            bbox_or_size_status="lvs_deck_available",
            placement_status="not_applicable",
            row_or_array_abutment_status="depends_on_physical_completion",
            vdd_gnd_rail_status="depends_on_physical_completion",
            routing_status="depends_on_physical_completion",
            timing_evidence_status="not_applicable",
            current_hybrid_status="cannot_claim_lvs_clean_now",
            readiness_level="BLOCKED",
            blocking_gap="full-chip OpenYield LVS clean is explicitly not claimed",
            next_required_action="run guarded LVS sanity only after physical integration is materially complete",
        )
        return

    if module == "timing":
        row.update(
            openyield_netlist_or_semantics_status="delay_chain_smoke_timing_only_control_paths_unproven",
            ports_or_pins_known="DELAY_CHAIN timing nodes proven; control-path timing mostly candidate-only",
            pin_mapping_status="not_applicable",
            bbox_or_size_status="not_applicable",
            placement_status="not_applicable",
            row_or_array_abutment_status="not_applicable",
            vdd_gnd_rail_status="not_applicable",
            routing_status="routing_not_closed",
            timing_evidence_status="smoke_only_no_timing_closure",
            current_hybrid_status="cannot_claim_timing_closure_now",
            readiness_level="BLOCKED",
            blocking_gap="timing evidence is limited to smoke metadata and does not constitute timing closure",
            next_required_action="expand physical timing evidence only after control-path placement and routing are integrated",
        )
        return

    raise ValueError(f"unclassified module: {module}")


def render_matrix_markdown(rows: list[dict[str, Any]]) -> str:
    lines = ["# OpenYield Netlist-to-GDS Readiness Matrix", ""]
    lines.append("| " + " | ".join(MATRIX_COLUMNS) + " |")
    lines.append("| " + " | ".join(["---"] * len(MATRIX_COLUMNS)) + " |")
    for row in rows:
        vals = []
        for col in MATRIX_COLUMNS:
            value = row[col]
            if isinstance(value, bool):
                vals.append("True" if value else "False")
            else:
                vals.append(str(value).replace("\n", " "))
        lines.append("| " + " | ".join(vals) + " |")
    lines.append("")
    return "\n".join(lines)


def render_report_markdown(report: dict[str, Any]) -> str:
    gates = report["gates"]
    lines = [
        "# OpenYield Netlist-to-GDS Readiness Report",
        "",
        f"- current hybrid GDS available: `{gates['current_hybrid_gds_available']}`",
        f"- current hybrid GDS path: `{gates['current_hybrid_gds_path']}`",
        f"- module readiness rows: `{gates['module_readiness_rows_count']}`",
        f"- OpenYield-driven modules count: `{gates['openyield_driven_modules_count']}`",
        f"- fallback modules count: `{gates['fallback_modules_count']}`",
        f"- can claim full OpenYield GDS now: `{gates['can_claim_full_openyield_gds_now']}`",
        f"- can claim DRC clean now: `{gates['can_claim_drc_clean_now']}`",
        f"- can claim LVS clean now: `{gates['can_claim_lvs_clean_now']}`",
        f"- can claim timing closure now: `{gates['can_claim_timing_closure_now']}`",
        "",
        "## Current GDS-generatable modules",
        "",
    ]
    for item in report["current_gds_generatable_modules"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Fallback Modules", ""])
    for item in report["fallback_modules"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Metadata-only Modules", ""])
    for item in gates["metadata_only_modules"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Candidate-contract-only Modules", ""])
    for item in gates["candidate_contract_only_modules"]:
        lines.append(f"- {item}")
    lines.extend(["", "## Missing Physical Implementation Modules", ""])
    if gates["missing_physical_implementation_modules"]:
        for item in gates["missing_physical_implementation_modules"]:
            lines.append(f"- {item}")
    else:
        lines.append("- none")
    lines.extend(["", "## Blocking gaps for full OpenYield GDS", ""])
    lines.append("| blocking_gap | why_it_blocks_full_gds | minimum_fix | recommended_next_task |")
    lines.append("| --- | --- | --- | --- |")
    for item in report["blocking_gaps_for_full_openyield_gds"]:
        lines.append(
            f"| {item['blocking_gap']} | {item['why_it_blocks_full_gds']} | {item['minimum_fix']} | {item['recommended_next_task']} |"
        )
    lines.extend(["", "## next_action_priority", ""])
    lines.append("| priority | target_module | reason | expected_result | files_to_modify | risk_level | whether_affects_legacy_default | estimated_gate_after_completion |")
    lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for item in report["next_action_priority"]:
        lines.append(
            f"| {item['priority']} | {item['target_module']} | {item['reason']} | {item['expected_result']} | {item['files_to_modify']} | {item['risk_level']} | {item['whether_affects_legacy_default']} | {item['estimated_gate_after_completion']} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_gap_summary_markdown(report: dict[str, Any]) -> str:
    gates = report["gates"]
    lines = [
        "# OpenYield Netlist-to-GDS Gap Summary",
        "",
        f"- readiness matrix available: `{gates['netlist_to_gds_readiness_matrix_available']}`",
        f"- rows covered: `{gates['module_readiness_rows_count']}`",
        f"- current GDS-generatable modules: `{', '.join(report['current_gds_generatable_modules'])}`",
        f"- metadata-only modules: `{', '.join(gates['metadata_only_modules']) or 'none'}`",
        f"- candidate-contract-only modules: `{', '.join(gates['candidate_contract_only_modules']) or 'none'}`",
        f"- can claim full OpenYield GDS now: `{gates['can_claim_full_openyield_gds_now']}`",
        "",
        "## Largest blockers",
        "",
    ]
    for item in report["blocking_gaps_for_full_openyield_gds"][:5]:
        lines.append(f"- {item['blocking_gap']}: {item['recommended_next_task']}")
    lines.extend(["", "## Recommended order", ""])
    for item in report["next_action_priority"][:3]:
        lines.append(f"- P{item['priority']} `{item['target_module']}`: {item['expected_result']}")
    lines.append("")
    return "\n".join(lines)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=MATRIX_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--module-coverage", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    parser.add_argument("--out-gap-summary")
    args = parser.parse_args(argv)

    report = build_readiness_report(args.repo_root, args.openyield_root, args.module_coverage)
    repo = Path(args.repo_root).resolve()
    out_csv = (repo / args.out_csv).resolve() if not Path(args.out_csv).is_absolute() else Path(args.out_csv).resolve()
    out_md = (repo / args.out_md).resolve() if not Path(args.out_md).is_absolute() else Path(args.out_md).resolve()
    out_json = (repo / args.out_json).resolve() if not Path(args.out_json).is_absolute() else Path(args.out_json).resolve()
    out_report = (repo / args.out_report).resolve() if not Path(args.out_report).is_absolute() else Path(args.out_report).resolve()
    out_gap_summary = None
    if args.out_gap_summary:
        out_gap_summary = (repo / args.out_gap_summary).resolve() if not Path(args.out_gap_summary).is_absolute() else Path(args.out_gap_summary).resolve()

    for path in [out_csv, out_md, out_json, out_report, out_gap_summary]:
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)

    write_csv(out_csv, report["matrix_rows"])
    out_md.write_text(render_matrix_markdown(report["matrix_rows"]), encoding="utf-8")
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_report.write_text(render_report_markdown(report), encoding="utf-8")
    if out_gap_summary is not None:
        out_gap_summary.write_text(render_gap_summary_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
