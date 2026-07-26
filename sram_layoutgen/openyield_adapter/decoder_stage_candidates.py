"""Read-only OpenYield decoder stage/group metadata audit helpers.

This module does not place decoder cells or generate GDS. It decomposes
DECODER_CASCADE into conservative stage/group candidates plus local macro
availability and handoff metadata needed before any physical decoder work.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .macro_compat import discover_library_macros, load_contract_payload


@dataclass(frozen=True)
class DecoderStageInstance:
    level: int
    decoder_index: int
    stage_name: str
    enable_net: str
    address_node_order: tuple[str, ...]
    decoder_pin_map: dict[str, str]
    output_nets: tuple[str, ...]
    output_role: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DecoderStageCandidate:
    candidate_name: str
    candidate_type: str
    source_class: str
    role: str
    input_nets: tuple[str, ...]
    output_nets: tuple[str, ...]
    enable_nets: tuple[str, ...]
    internal_nodes: tuple[str, ...]
    subcells: tuple[str, ...]
    candidate_local_macros: tuple[str, ...]
    missing_local_macros: tuple[str, ...]
    mapping_status: str
    placement_feasibility: str
    metadata_only: bool
    pin_proven: bool
    physical_routing_proven: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LocalMacroAvailability:
    macro_name: str
    gds_available: bool
    spice_available: bool
    labels_available: bool
    power_metadata_available: bool
    safe_for_metadata_mapping: bool
    safe_for_physical_placement: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_decoder_stage_candidate_report(
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
    addr_width: int = 5,
    num_rows: int | None = None,
    gds_pin_report_path: str | Path | None = None,
    decomposition_report_path: str | Path | None = None,
    target_envelope_report_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    root = Path(openyield_root)
    tech = Path(tech_dir)
    rows = int(num_rows) if num_rows is not None else 1 << int(addr_width)
    contracts = load_contract_payload(contracts_path)
    contract_index = _build_contract_index(contracts.get("contracts", []))
    gds_pin_report = _load_json_if_exists(gds_pin_report_path)
    decomposition_report = _load_json_if_exists(decomposition_report_path)
    target_envelope_report = _load_json_if_exists(target_envelope_report_path)

    decoder_py = root / "sram_compiler/subcircuits/decoder.py"
    standard_cell_py = root / "sram_compiler/subcircuits/standard_cell.py"
    decoder_source = decoder_py.read_text(encoding="utf-8", errors="replace") if decoder_py.exists() else ""
    stdcell_source = standard_cell_py.read_text(encoding="utf-8", errors="replace") if standard_cell_py.exists() else ""
    source_health = {
        "decoder_py": decoder_py.exists(),
        "standard_cell_py": standard_cell_py.exists(),
    }

    decoder_cascade_exists = ("class DECODER_CASCADE" in decoder_source) or ("DECODER_CASCADE" in contract_index)
    decoder3_8_exists = ("class DECODER3_8" in decoder_source) or ("DECODER3_8" in contract_index)
    pinv_exists = ("class Pinv" in stdcell_source) or ("Pinv" in contract_index)
    pnand2_exists = ("class PNAND2" in stdcell_source) or ("PNAND2" in contract_index)
    pnand3_exists = ("class PNAND3" in stdcell_source) or ("PNAND3" in contract_index)
    and2_exists = ("class AND2" in stdcell_source) or ("AND2" in contract_index)
    and3_exists = ("class AND3" in stdcell_source) or ("AND3" in contract_index)

    n_bits = max(1, int(addr_width))
    n_levels = int(math.ceil(n_bits / 3.0))
    level_groups = _compute_level_groups(rows, n_levels)
    stage_instances = _build_stage_instances(rows=rows, n_bits=n_bits, n_levels=n_levels, level_groups=level_groups)

    library = discover_library_macros(tech)
    gds_pin_index = _build_gds_pin_index(gds_pin_report)
    macro_names = ("gen_inv", "gen_delay_inv", "gen_nand2", "gen_nand4", "tri_gate", "dff", "gen_wl_driver")
    local_macro_availability = [
        _macro_availability(name, library, gds_pin_index)
        for name in macro_names
    ]
    local_macro_index = {item.macro_name: item for item in local_macro_availability}

    nand3_direct_macro_available = "gen_nand3" in library
    and3_requires_composition_or_generated_logic = not nand3_direct_macro_available
    decoder_logic_macros_partially_available = (
        local_macro_index["gen_inv"].gds_available
        and local_macro_index["gen_nand2"].gds_available
        and and3_requires_composition_or_generated_logic
    )

    decoder3_8_inputs = ("EN", "A0", "A1", "A2")
    decoder3_8_outputs = tuple(f"WL{i}" for i in range(8))
    decoder3_8_group_notes = (
        "DECODER3_8 instantiates three input inverters, eight AND3 gates, and eight AND2 enable gates.",
        "A0/A1/A2 pin ordering in DECODER_CASCADE is reversed from the local address_node accumulation order in source.",
        "No direct gen_nand3 hard macro is present in the local library, so AND3 is still composition/generated-logic only.",
    )

    stage_candidates = [
        DecoderStageCandidate(
            candidate_name="DECODER_CASCADE_STAGE_PLAN",
            candidate_type="hierarchical_decoder_plan",
            source_class="DECODER_CASCADE",
            role="decoder",
            input_nets=tuple(f"A[{bit}]" for bit in range(n_bits)),
            output_nets=("WL[*]",),
            enable_nets=("VDD", "EN_<level-1>_<group>_<slot>"),
            internal_nodes=("EN_<level>_<group>_<slot>",),
            subcells=("DECODER3_8",),
            candidate_local_macros=("gen_inv", "gen_nand2", "gen_nand4", "gen_wl_driver"),
            missing_local_macros=("gen_nand3",),
            mapping_status="generated_logic_partial",
            placement_feasibility="metadata_stage_plan_only",
            metadata_only=True,
            pin_proven=False,
            physical_routing_proven=False,
            notes=(
                f"Computed for addr_width={n_bits}, num_rows={rows}, n_levels={n_levels}, level_groups={level_groups}.",
                "Input source is ADDR_DFF_ROW.addr_q[*] via DECODER_INPUT_ANCHOR / ADDR_TO_DECODER_WINDOW metadata.",
                "Output consumer is WORDLINEDRIVER.A[*]; routing and physical access remain unproven.",
            ),
        ),
        DecoderStageCandidate(
            candidate_name="DECODER3_8_GROUP",
            candidate_type="decoder_stage_group",
            source_class="DECODER3_8",
            role="decoder_stage",
            input_nets=decoder3_8_inputs,
            output_nets=decoder3_8_outputs,
            enable_nets=("EN",),
            internal_nodes=("A0b", "A1b", "A2b", "WL0_pre", "WL1_pre", "WL2_pre", "WL3_pre", "WL4_pre", "WL5_pre", "WL6_pre", "WL7_pre"),
            subcells=("Pinv", "AND3", "AND2"),
            candidate_local_macros=("gen_inv", "gen_nand2"),
            missing_local_macros=("gen_nand3",),
            mapping_status="generated_logic_partial",
            placement_feasibility="needs_generated_logic_row_rules",
            metadata_only=True,
            pin_proven=False,
            physical_routing_proven=False,
            notes=decoder3_8_group_notes,
        ),
        DecoderStageCandidate(
            candidate_name="DECODER_LOGIC_CELL_SET",
            candidate_type="logic_cell_set",
            source_class="Pinv/PNAND2/PNAND3/AND2/AND3",
            role="support_logic",
            input_nets=("A", "B", "C"),
            output_nets=("Z",),
            enable_nets=(),
            internal_nodes=(),
            subcells=("Pinv", "PNAND2", "PNAND3", "AND2", "AND3"),
            candidate_local_macros=("gen_inv", "gen_nand2", "gen_nand4"),
            missing_local_macros=("gen_nand3",),
            mapping_status="generated_logic_partial",
            placement_feasibility="needs_generated_logic_row_rules",
            metadata_only=True,
            pin_proven=False,
            physical_routing_proven=False,
            notes=(
                "Pinv maps most directly to gen_inv.",
                "PNAND2 / AND2 can be composed from gen_nand2 and inversion.",
                "PNAND3 / AND3 lack a direct local hard macro and still require composition or generated logic.",
            ),
        ),
    ]

    input_handoff = {
        "source": "ADDR_DFF_ROW.addr_q[i]",
        "sink": "DECODER_CASCADE.A[i]",
        "source_anchor": "DECODER_INPUT_ANCHOR",
        "source_window": "ADDR_TO_DECODER_WINDOW",
        "decoder_stage_input_side": "decoder_input_side",
        "metadata_only": True,
        "pin_proven": False,
        "physical_routing_proven": False,
    }
    output_handoff = {
        "source": "DECODER_CASCADE.WL[row] / decoder_out[row]",
        "consumer": "WORDLINEDRIVER",
        "consumer_pin": "A",
        "sink": "WORDLINEDRIVER.A[row]",
        "wordline_driver_semantics_confirmed": True,
        "metadata_only": True,
        "pin_proven": False,
        "physical_routing_proven": False,
    }

    blockers = [
        "DECODER_CASCADE is still metadata-only and is not a pin-proven hard macro.",
        "No direct local gen_nand3 / AND3 hard macro is available; decoder stage logic remains partially compositional.",
        "Generated-logic row rules, stage grouping row packing, and power rail strategy are not yet proven for decoder placement.",
        "Decoder output handoff to WORDLINEDRIVER.A is semantic-only; no physical routing proof exists.",
        "Control-row physical smoke remains blocked until decoder pin/power/routing evidence exists.",
    ]

    decoder_stage_decomposition_success = bool(
        source_health["decoder_py"]
        and source_health["standard_cell_py"]
        and decoder_cascade_exists
        and decoder3_8_exists
    )
    decoder_generated_block_plan_available = decoder_stage_decomposition_success
    can_enter_decoder_generated_block_planning = decoder_stage_decomposition_success
    can_enter_physical_decoder_placement = False
    can_enter_very_limited_control_row_smoke = False

    report = {
        "scope": "step6_9_openyield_decoder_stage_candidate_audit",
        "openyield_root": str(root.resolve()),
        "contracts_path": str(Path(contracts_path).resolve()),
        "tech_dir": str(tech.resolve()),
        "source_files": {
            "decoder_py": str(decoder_py.resolve()),
            "standard_cell_py": str(standard_cell_py.resolve()),
        },
        "source_health": source_health,
        "addr_width": n_bits,
        "num_rows": rows,
        "decoder_cascade_exists": decoder_cascade_exists,
        "decoder_cascade_source_path": str(decoder_py.resolve()),
        "decoder_cascade_top_inputs": ["VDD", "VSS", *[f"A[{bit}]" for bit in range(n_bits)]],
        "decoder_cascade_top_outputs": [f"WL[{row}]" for row in range(rows)],
        "decoder3_8_exists": decoder3_8_exists,
        "decoder3_8_inputs": list(decoder3_8_inputs),
        "decoder3_8_outputs": list(decoder3_8_outputs),
        "decoder_logic_subcells_present": {
            "Pinv": pinv_exists,
            "PNAND2": pnand2_exists,
            "PNAND3": pnand3_exists,
            "AND2": and2_exists,
            "AND3": and3_exists,
        },
        "decoder_cascade_hierarchy": {
            "n_bits": n_bits,
            "n_levels": n_levels,
            "level_groups": level_groups,
            "total_decoder3_8_instances": sum(level_groups),
            "stage_instances": [item.to_dict() for item in stage_instances],
        },
        "stage_group_candidates": [item.to_dict() for item in stage_candidates],
        "logic_cell_set": stage_candidates[2].to_dict(),
        "local_macro_availability": [item.to_dict() for item in local_macro_availability],
        "nand3_direct_macro_available": nand3_direct_macro_available,
        "and3_requires_composition_or_generated_logic": and3_requires_composition_or_generated_logic,
        "decoder_direct_and3_or_nand3_missing": not nand3_direct_macro_available,
        "decoder_logic_macros_partially_available": decoder_logic_macros_partially_available,
        "input_handoff": input_handoff,
        "output_handoff": output_handoff,
        "decoder_envelope_is_metadata_only": True,
        "decoder_hardmacro_pin_proven": False,
        "physical_routing_proven": False,
        "decoder_stage_decomposition_success": decoder_stage_decomposition_success,
        "decoder_generated_block_plan_available": decoder_generated_block_plan_available,
        "can_enter_decoder_generated_block_planning": can_enter_decoder_generated_block_planning,
        "can_enter_physical_decoder_placement": can_enter_physical_decoder_placement,
        "can_enter_very_limited_control_row_smoke": can_enter_very_limited_control_row_smoke,
        "manual_source_review_required": not decoder_stage_decomposition_success,
        "blocker_list": blockers,
        "step_6_10_recommendation": "Define decoder generated-logic row rules and per-stage power/pin metadata before any decoder physical placement or control-row smoke.",
        "upstream_context": {
            "target_envelope_summary": _extract_target_envelope_summary(target_envelope_report),
            "decomposition_summary": _extract_decomposition_summary(decomposition_report),
        },
    }

    graph = {
        "scope": report["scope"],
        "nodes": _build_graph_nodes(stage_candidates, local_macro_availability),
        "edges": _build_graph_edges(stage_instances),
        "stage_instances": [item.to_dict() for item in stage_instances],
        "input_handoff": input_handoff,
        "output_handoff": output_handoff,
        "blockers": blockers,
    }
    return report, graph


def build_decoder_stage_candidate_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Decoder Stage Candidate Audit",
        "",
        "This is a read-only metadata audit for DECODER_CASCADE stage/group candidates. It does not modify standalone.py, routing, placement, or the GDS writer.",
        "",
        "## Summary",
        "",
        f"- decoder_cascade_exists: `{report['decoder_cascade_exists']}`",
        f"- decoder3_8_exists: `{report['decoder3_8_exists']}`",
        f"- decoder_stage_decomposition_success: `{report['decoder_stage_decomposition_success']}`",
        f"- decoder_generated_block_plan_available: `{report['decoder_generated_block_plan_available']}`",
        f"- decoder_envelope_is_metadata_only: `{report['decoder_envelope_is_metadata_only']}`",
        f"- decoder_hardmacro_pin_proven: `{report['decoder_hardmacro_pin_proven']}`",
        f"- decoder_logic_macros_partially_available: `{report['decoder_logic_macros_partially_available']}`",
        f"- decoder_direct_and3_or_nand3_missing: `{report['decoder_direct_and3_or_nand3_missing']}`",
        f"- can_enter_decoder_generated_block_planning: `{report['can_enter_decoder_generated_block_planning']}`",
        f"- can_enter_physical_decoder_placement: `{report['can_enter_physical_decoder_placement']}`",
        f"- can_enter_very_limited_control_row_smoke: `{report['can_enter_very_limited_control_row_smoke']}`",
        "",
        "## Top-Level Decoder View",
        "",
        f"- source path: `{report['decoder_cascade_source_path']}`",
        f"- addr_width: `{report['addr_width']}`",
        f"- num_rows: `{report['num_rows']}`",
        f"- top inputs: `{', '.join(report['decoder_cascade_top_inputs'])}`",
        f"- top outputs: `{', '.join(report['decoder_cascade_top_outputs'][:8])}{' ...' if len(report['decoder_cascade_top_outputs']) > 8 else ''}`",
        "",
        "## Decoder Hierarchy",
        "",
        f"- n_levels: `{report['decoder_cascade_hierarchy']['n_levels']}`",
        f"- level_groups: `{report['decoder_cascade_hierarchy']['level_groups']}`",
        f"- total_decoder3_8_instances: `{report['decoder_cascade_hierarchy']['total_decoder3_8_instances']}`",
        "",
        md_table(
            ["level", "decoder_index", "stage_name", "enable_net", "address_node_order", "decoder_pin_map", "output_role", "first_outputs"],
            [
                [
                    item["level"],
                    item["decoder_index"],
                    item["stage_name"],
                    item["enable_net"],
                    ", ".join(item["address_node_order"]),
                    ", ".join(f"{k}={v}" for k, v in item["decoder_pin_map"].items()),
                    item["output_role"],
                    ", ".join(item["output_nets"][:4]) + (" ..." if len(item["output_nets"]) > 4 else ""),
                ]
                for item in report["decoder_cascade_hierarchy"]["stage_instances"]
            ],
        ),
        "",
        "## Stage / Group Candidates",
        "",
        md_table(
            ["candidate", "type", "source_class", "inputs", "outputs", "subcells", "local_macros", "missing_macros", "mapping_status", "placement_feasibility"],
            [
                [
                    item["candidate_name"],
                    item["candidate_type"],
                    item["source_class"],
                    ", ".join(item["input_nets"]) or "-",
                    ", ".join(item["output_nets"]) or "-",
                    ", ".join(item["subcells"]) or "-",
                    ", ".join(item["candidate_local_macros"]) or "-",
                    ", ".join(item["missing_local_macros"]) or "-",
                    item["mapping_status"],
                    item["placement_feasibility"],
                ]
                for item in report["stage_group_candidates"]
            ],
        ),
        "",
        "## Local Macro Availability",
        "",
        md_table(
            ["macro", "gds", "spice", "labels", "power_metadata", "safe_metadata_mapping", "safe_physical_placement", "notes"],
            [
                [
                    item["macro_name"],
                    item["gds_available"],
                    item["spice_available"],
                    item["labels_available"],
                    item["power_metadata_available"],
                    item["safe_for_metadata_mapping"],
                    item["safe_for_physical_placement"],
                    _notes_text(item["notes"]),
                ]
                for item in report["local_macro_availability"]
            ],
        ),
        "",
        "## Input Handoff",
        "",
        "```json",
        json.dumps(report["input_handoff"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Output Handoff",
        "",
        "```json",
        json.dumps(report["output_handoff"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Blockers",
        "",
        *[f"- {item}" for item in report["blocker_list"]],
        "",
        "## Step 6.10 Recommendation",
        "",
        f"- {report['step_6_10_recommendation']}",
        "",
    ]
    return "\n".join(lines)


def write_decoder_stage_candidate_reports(
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
    addr_width: int,
    out_json: str | Path,
    out_md: str | Path,
    out_graph: str | Path,
    num_rows: int | None = None,
    gds_pin_report_path: str | Path | None = None,
    decomposition_report_path: str | Path | None = None,
    target_envelope_report_path: str | Path | None = None,
) -> dict[str, Any]:
    report, graph = build_decoder_stage_candidate_report(
        openyield_root=openyield_root,
        contracts_path=contracts_path,
        tech_dir=tech_dir,
        addr_width=addr_width,
        num_rows=num_rows,
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
    out_md.write_text(build_decoder_stage_candidate_markdown(report), encoding="utf-8")
    out_graph.write_text(json.dumps(graph, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def _compute_level_groups(num_rows: int, n_levels: int) -> list[int]:
    groups = [0] * n_levels
    groups[n_levels - 1] = int(math.ceil(num_rows / 8.0))
    for level in range(n_levels - 2, -1, -1):
        groups[level] = int(math.ceil(groups[level + 1] / 8.0))
    return groups


def _build_stage_instances(rows: int, n_bits: int, n_levels: int, level_groups: list[int]) -> list[DecoderStageInstance]:
    previous_level_outputs: list[str] = []
    instances: list[DecoderStageInstance] = []
    for level in range(n_levels):
        current_outputs: list[str] = []
        for decoder_idx in range(level_groups[level]):
            address_nodes: list[str] = []
            start_bit = 3 * (n_levels - level - 1)
            for bit in range(3):
                bit_idx = start_bit + bit
                if 0 <= bit_idx < n_bits:
                    address_nodes.append(f"A{bit_idx}")
                else:
                    address_nodes.append("VSS")
            enable_signal = "VDD" if level == 0 else (previous_level_outputs[decoder_idx] if decoder_idx < len(previous_level_outputs) else "VSS")
            output_nodes: list[str] = []
            for out_idx in range(8):
                if level == n_levels - 1:
                    wl_idx = decoder_idx * 8 + out_idx
                    node_name = f"WL{wl_idx}" if wl_idx < rows else f"NC_{level}_{decoder_idx}_{out_idx}"
                else:
                    node_name = f"EN_{level}_{decoder_idx}_{out_idx}"
                output_nodes.append(node_name)
            current_outputs.extend(output_nodes)
            instances.append(
                DecoderStageInstance(
                    level=level,
                    decoder_index=decoder_idx,
                    stage_name=f"DEC_{level}_{decoder_idx}",
                    enable_net=enable_signal,
                    address_node_order=tuple(address_nodes),
                    decoder_pin_map={
                        "EN": enable_signal,
                        "A0": address_nodes[2],
                        "A1": address_nodes[1],
                        "A2": address_nodes[0],
                    },
                    output_nets=tuple(output_nodes),
                    output_role="wordline_outputs" if level == n_levels - 1 else "intermediate_enable_bus",
                )
            )
        previous_level_outputs = current_outputs
    return instances


def _macro_availability(
    macro_name: str,
    library: dict[str, dict[str, Any]],
    gds_pin_index: dict[str, dict[str, Any]],
) -> LocalMacroAvailability:
    library_entry = library.get(macro_name, {})
    pin_audit = gds_pin_index.get(macro_name, {})
    gds_available = bool(library_entry.get("gds"))
    spice_available = bool(library_entry.get("spice"))
    labels = pin_audit.get("labels", [])
    power_audit = pin_audit.get("power_rail_audit", {})
    labels_available = bool(labels)
    power_metadata_available = bool(power_audit.get("has_vdd") and power_audit.get("has_gnd"))
    safe_for_metadata_mapping = bool(gds_available or spice_available or labels_available)
    safe_for_physical_placement = bool(
        gds_available
        and spice_available
        and labels_available
        and power_metadata_available
        and pin_audit.get("abutment_readiness") == "abutment_ready"
    )
    notes: list[str] = []
    if not gds_available:
        notes.append("No local GDS file discovered.")
    if not spice_available:
        notes.append("No local SPICE leaf discovered.")
    if gds_available and not labels_available:
        notes.append("GDS exists but label coverage is missing or incomplete in current pin audit.")
    if gds_available and not power_metadata_available:
        notes.append("Power metadata is incomplete in current GDS pin audit.")
    if macro_name in {"gen_inv", "gen_nand2", "gen_nand4"}:
        notes.append("Availability supports metadata planning only; decoder row rules and routing remain unproven.")
    if macro_name == "gen_wl_driver":
        notes.append("Wordline driver semantics were confirmed earlier, but decoder-to-driver routing is still metadata-only.")
    if macro_name == "dff":
        notes.append("DFF is a proven local hardcell, but it is upstream of decoder input handoff rather than a decoder logic leaf.")
    return LocalMacroAvailability(
        macro_name=macro_name,
        gds_available=gds_available,
        spice_available=spice_available,
        labels_available=labels_available,
        power_metadata_available=power_metadata_available,
        safe_for_metadata_mapping=safe_for_metadata_mapping,
        safe_for_physical_placement=safe_for_physical_placement,
        notes=tuple(notes),
    )


def _build_gds_pin_index(gds_pin_report: dict[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not gds_pin_report:
        return {}
    return {
        str(item.get("macro_name")): item
        for item in gds_pin_report.get("audited_macros", [])
    }


def _extract_target_envelope_summary(report: dict[str, Any] | None) -> dict[str, Any]:
    if not report:
        return {}
    return {
        "decoder_envelope_bound": report.get("decoder_envelope_bound"),
        "decoder_envelope_is_metadata_only": report.get("decoder_envelope_is_metadata_only"),
        "decoder_hardmacro_pin_proven": report.get("decoder_envelope_pin_proven"),
        "write_driver_target_bound": report.get("write_driver_target_bound"),
        "can_enter_very_limited_physical_smoke": report.get("can_enter_very_limited_physical_smoke"),
    }


def _extract_decomposition_summary(report: dict[str, Any] | None) -> dict[str, Any]:
    if not report:
        return {}
    return {
        "time_decomposition_success": report.get("time_decomposition_success"),
        "can_enter_control_subblock_adapter_planning": report.get("can_enter_control_subblock_adapter_planning"),
        "decoder_nodes": [
            item["node_name"]
            for item in report.get("nodes", [])
            if item.get("node_name") in {"DECODER3_8", "DECODER_CASCADE", "Pinv", "PNAND2", "PNAND3", "AND2", "AND3"}
        ],
    }


def _build_graph_nodes(
    candidates: list[DecoderStageCandidate],
    macros: list[LocalMacroAvailability],
) -> list[dict[str, Any]]:
    nodes: list[dict[str, Any]] = []
    for item in candidates:
        nodes.append(
            {
                "id": item.candidate_name,
                "kind": "candidate",
                "candidate_type": item.candidate_type,
                "source_class": item.source_class,
                "mapping_status": item.mapping_status,
                "placement_feasibility": item.placement_feasibility,
            }
        )
    for item in macros:
        nodes.append(
            {
                "id": item.macro_name,
                "kind": "local_macro",
                "safe_for_metadata_mapping": item.safe_for_metadata_mapping,
                "safe_for_physical_placement": item.safe_for_physical_placement,
            }
        )
    return nodes


def _build_graph_edges(stage_instances: list[DecoderStageInstance]) -> list[dict[str, Any]]:
    edges: list[dict[str, Any]] = [
        {
            "source": "ADDR_DFF_ROW.addr_q[*]",
            "target": "DECODER_CASCADE_STAGE_PLAN",
            "relation": "input_handoff",
        },
        {
            "source": "DECODER_CASCADE_STAGE_PLAN",
            "target": "WORDLINEDRIVER.A[*]",
            "relation": "output_handoff",
        },
        {
            "source": "DECODER_CASCADE_STAGE_PLAN",
            "target": "DECODER3_8_GROUP",
            "relation": "repeats",
        },
        {
            "source": "DECODER3_8_GROUP",
            "target": "DECODER_LOGIC_CELL_SET",
            "relation": "contains",
        },
        {
            "source": "DECODER_LOGIC_CELL_SET",
            "target": "gen_inv",
            "relation": "candidate_macro",
        },
        {
            "source": "DECODER_LOGIC_CELL_SET",
            "target": "gen_nand2",
            "relation": "candidate_macro",
        },
        {
            "source": "DECODER_CASCADE_STAGE_PLAN",
            "target": "gen_wl_driver",
            "relation": "downstream_consumer_macro",
        },
    ]
    for item in stage_instances:
        edges.append(
            {
                "source": "DECODER_CASCADE_STAGE_PLAN",
                "target": item.stage_name,
                "relation": "stage_instance",
                "level": item.level,
            }
        )
    return edges


def _build_contract_index(contracts: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}
    for contract in contracts:
        for key in {str(contract.get("original_module_name") or ""), str(contract.get("class_name") or "")}:
            if key:
                index[key] = contract
    return index


def _load_json_if_exists(path: str | Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    candidate = Path(path)
    if not candidate.exists():
        return None
    return json.loads(candidate.read_text(encoding="utf-8"))


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_md_cell(item) for item in row) + " |")
    return "\n".join(lines)


def _md_cell(value: Any) -> str:
    return str(value).replace("\n", "<br>")


def _notes_text(notes: Any) -> str:
    if isinstance(notes, (list, tuple)):
        return "; ".join(str(item) for item in notes) or "-"
    if not notes:
        return "-"
    return str(notes)
