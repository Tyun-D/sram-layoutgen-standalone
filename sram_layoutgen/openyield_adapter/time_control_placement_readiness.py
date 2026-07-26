"""Read-only OpenYield TIME control very-limited placement readiness audit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


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


def _subblock(
    *,
    name: str,
    category: str,
    placement_style: str,
    metadata_ready: bool | str,
    physical_ready: bool,
    depends_on: list[str],
    blocked_by: list[str],
    notes: list[str],
) -> dict[str, Any]:
    return {
        "subblock_name": name,
        "category": category,
        "placement_style": placement_style,
        "metadata_ready": metadata_ready,
        "physical_ready": physical_ready,
        "depends_on": depends_on,
        "blocked_by": blocked_by,
        "notes": notes,
    }


def build_time_control_placement_readiness_report(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    openyield_root = Path(openyield_root)
    contracts_path = Path(contracts_path)
    tech_dir = Path(tech_dir)

    decomposition = _load_json("docs/openyield_time_control_decomposition_report.json")
    generated_logic = _load_json("docs/openyield_time_control_generated_logic_contract_report.json")
    consumer_contracts = _load_json("docs/openyield_time_control_consumer_contract_report.json")
    metadata_closure = _load_json("docs/openyield_time_control_metadata_closure_report.json")
    region_refinement = _load_json("docs/openyield_time_control_region_refinement_report.json")
    closure_unblock = _load_json("docs/openyield_time_control_closure_unblock_report.json")

    metadata_chain_complete = bool(
        metadata_closure["consistency_checks"]["time_control_metadata_chain_complete"]
    )
    precharge_status = metadata_closure["precharge_closure_status"]
    crossing_complete = bool(
        metadata_closure["consistency_checks"]["control_region_crossing_coverage_complete"]
    )
    region_ready = bool(
        region_refinement["consistency_checks"]["can_enter_time_control_region_metadata_planning"]
    )

    subblocks = [
        _subblock(
            name="ADDR_DFF_ROW",
            category="latched_address_array",
            placement_style="row_based_dff_array",
            metadata_ready=True,
            physical_ready=False,
            depends_on=["DFF", "clk distribution metadata", "addr bus isolation proof"],
            blocked_by=["no legal placement proof", "no routing proof", "no standalone integration"],
            notes=["Address DFF decomposition is closed at metadata level only."],
        ),
        _subblock(
            name="DATA_DFF_ROW",
            category="latched_write_data_array",
            placement_style="row_based_dff_array",
            metadata_ready=True,
            physical_ready=False,
            depends_on=["DFF", "clk distribution metadata", "din bus routing proof"],
            blocked_by=["no legal placement proof", "no routing proof", "no standalone integration"],
            notes=["Data DFF decomposition is closed at metadata level only."],
        ),
        _subblock(
            name="DELAY_CHAIN_CLUSTER",
            category="generated_logic_timing_chain",
            placement_style="generated_logic_or_stdcell_row",
            metadata_ready=True,
            physical_ready=False,
            depends_on=["Pinv chain metadata", "rbl delay timing metadata"],
            blocked_by=["delay timing proof missing", "no legal placement proof", "no routing proof"],
            notes=["Replica-bitline delay chain is structurally decomposed but not physically proven."],
        ),
        _subblock(
            name="WEN_DELAY_CHAIN_CLUSTER",
            category="generated_logic_timing_chain",
            placement_style="generated_logic_or_stdcell_row",
            metadata_ready=True,
            physical_ready=False,
            depends_on=["Pinv chain metadata", "wen-delay metadata"],
            blocked_by=["wen-delay timing proof missing", "no legal placement proof", "no routing proof"],
            notes=["Write-enable delay chain remains metadata-only."],
        ),
        _subblock(
            name="PDRIVE_CLUSTER",
            category="generated_logic_buffer_chain",
            placement_style="generated_logic_or_stdcell_row",
            metadata_ready=True,
            physical_ready=False,
            depends_on=["Pinv chain metadata", "clock buffer fanout metadata"],
            blocked_by=["no legal placement proof", "no routing proof"],
            notes=["Clock/precharge/wordline buffer chains are abstractly placeable, not physically placeable yet."],
        ),
        _subblock(
            name="GENERATED_LOGIC_CLUSTER",
            category="nand_and_inverter_logic",
            placement_style="stdcell_row_candidate",
            metadata_ready=True,
            physical_ready=False,
            depends_on=["PNAND2/PNAND3/Pinv abstract contracts", "region adjacency metadata"],
            blocked_by=["stdcell physical library not proven", "no legal routing proof", "no DRC/LVS proof"],
            notes=["Suitable for future prototype planning only."],
        ),
        _subblock(
            name="PRECHARGE_HANDOFF",
            category="consumer_macro_handoff",
            placement_style="control_to_macro_handoff_only",
            metadata_ready=True if precharge_status != "retained_partial_blocker" else "partial",
            physical_ready=False,
            depends_on=["PRE signal binding", "consumer handoff metadata", "precharge power semantics"],
            blocked_by=["rail continuity proof missing", "no legal routing proof", "no physical placement proof"],
            notes=[
                "PRECHARGE stays at metadata/handoff readiness only.",
                f"Current closure status: {precharge_status}.",
            ],
        ),
        _subblock(
            name="SENSEAMP_HANDOFF",
            category="consumer_macro_handoff",
            placement_style="control_to_macro_handoff_only",
            metadata_ready=True,
            physical_ready=False,
            depends_on=["sense_enable contract", "consumer handoff metadata"],
            blocked_by=["no legal routing proof", "no physical placement proof"],
            notes=["Sense path adapter is already opt-in elsewhere; TIME-side proof here remains metadata-only."],
        ),
        _subblock(
            name="WRITEDRIVER_HANDOFF",
            category="consumer_macro_handoff",
            placement_style="control_to_macro_handoff_only",
            metadata_ready=True,
            physical_ready=False,
            depends_on=["write_enable contract", "consumer handoff metadata"],
            blocked_by=["no legal routing proof", "no physical placement proof"],
            notes=["Write path consumer contract is closed only at the semantic metadata level."],
        ),
        _subblock(
            name="WORDLINEDRIVER_HANDOFF",
            category="consumer_macro_handoff",
            placement_style="control_to_macro_handoff_only",
            metadata_ready=True,
            physical_ready=False,
            depends_on=["wordline_enable polarity metadata", "consumer handoff metadata"],
            blocked_by=["no legal routing proof", "no physical placement proof"],
            notes=["B high-active semantics are known, but no physical TIME/control placement is allowed yet."],
        ),
        _subblock(
            name="DECODER_INTERFACE",
            category="decoder_boundary_handoff",
            placement_style="decoder_boundary_only",
            metadata_ready=True,
            physical_ready=False,
            depends_on=["addr_q semantics", "decoder input contract"],
            blocked_by=["decoder placement intentionally untouched", "no legal routing proof", "no standalone integration"],
            notes=["This is only a boundary contract for future coordination with decoder placement."],
        ),
    ]

    metadata_ready_subblocks = [
        item["subblock_name"] for item in subblocks if item["metadata_ready"] is True
    ]
    partial_metadata_subblocks = [
        item["subblock_name"] for item in subblocks if item["metadata_ready"] == "partial"
    ]
    physical_blocked_subblocks = [
        item["subblock_name"] for item in subblocks if not item["physical_ready"]
    ]

    can_create_experimental_opt_in_placement_plan = bool(
        metadata_chain_complete and crossing_complete and region_ready
    )

    consistency_checks = {
        "time_control_placement_readiness_available": True,
        "time_control_metadata_closure_available": bool(
            metadata_closure["consistency_checks"]["time_control_metadata_closure_available"]
        ),
        "time_control_metadata_chain_complete": metadata_chain_complete,
        "control_region_crossing_coverage_complete": crossing_complete,
        "time_control_region_metadata_planning_available": region_ready,
        "precharge_closure_status": precharge_status,
        "metadata_ready_subblock_count": len(metadata_ready_subblocks),
        "partial_metadata_subblock_count": len(partial_metadata_subblocks),
        "physical_ready_subblock_count": 0,
        "can_create_experimental_opt_in_placement_plan": can_create_experimental_opt_in_placement_plan,
        "can_modify_standalone": False,
        "can_generate_time_control_gds": False,
        "can_enter_physical_placement": False,
        "safe_for_metadata_prototype_only": can_create_experimental_opt_in_placement_plan,
        "safe_for_physical_placement": False,
    }

    unresolved_items = [
        "This audit is abstract-to-placement readiness only; it is not legal placement proof.",
        "No TIME/control routed wires are proven.",
        "No TIME/control GDS is generated.",
        "PRECHARGE rail continuity proof is still missing.",
        "Delay timing proof is missing.",
        "WEN-delay timing proof is missing.",
        "Decoder physical placement remains intentionally out of scope.",
        "Standalone integration remains blocked at this stage.",
        "No DRC/LVS proof exists for a TIME/control assembly.",
    ]

    report = {
        "scope": "stage_c_openyield_time_control_placement_readiness",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(contracts_path.resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "source_reports": {
            "time_control_decomposition": decomposition.get("scope"),
            "time_control_generated_logic_contract": generated_logic.get("scope"),
            "time_control_consumer_contract": consumer_contracts.get("scope"),
            "time_control_region_refinement": region_refinement.get("scope"),
            "time_control_closure_unblock": closure_unblock.get("scope"),
            "time_control_metadata_closure": metadata_closure.get("scope"),
        },
        "subblock_readiness": subblocks,
        "readiness_summary": {
            "metadata_ready_subblocks": metadata_ready_subblocks,
            "partial_metadata_subblocks": partial_metadata_subblocks,
            "physical_blocked_subblocks": physical_blocked_subblocks,
            "recommended_next_stage": (
                "default_off_experimental_opt_in_prototype_plan"
                if can_create_experimental_opt_in_placement_plan
                else "metadata_gap_closure"
            ),
        },
        "consistency_checks": consistency_checks,
        "unresolved_items": unresolved_items,
        "audit_summary": {
            "time_control_placement_readiness_available": True,
            "metadata_ready_subblock_count": len(metadata_ready_subblocks),
            "partial_metadata_subblock_count": len(partial_metadata_subblocks),
            "can_create_experimental_opt_in_placement_plan": can_create_experimental_opt_in_placement_plan,
            "can_modify_standalone": False,
            "can_generate_time_control_gds": False,
            "can_enter_physical_placement": False,
        },
        "can_create_experimental_opt_in_placement_plan": can_create_experimental_opt_in_placement_plan,
        "can_modify_standalone": False,
        "can_generate_time_control_gds": False,
        "can_enter_physical_placement": False,
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
    }

    graph = {
        "scope": report["scope"],
        "nodes": [{"id": item["subblock_name"], "kind": item["category"]} for item in subblocks],
        "edges": [
            {
                "source": item["subblock_name"],
                "target": dependency,
                "relation": "depends_on",
            }
            for item in subblocks
            for dependency in item["depends_on"]
        ],
        "summary": report["audit_summary"],
    }
    return report, graph


def build_time_control_placement_readiness_markdown(report: dict[str, Any]) -> str:
    subblock_rows = [
        [
            item["subblock_name"],
            item["category"],
            item["placement_style"],
            item["metadata_ready"],
            item["physical_ready"],
            ", ".join(item["blocked_by"]),
        ]
        for item in report["subblock_readiness"]
    ]
    consistency_rows = [[key, value] for key, value in report["consistency_checks"].items()]
    lines = [
        "# OpenYield TIME Control Placement Readiness Report",
        "",
        "This is a very-limited abstract readiness audit only. It does not authorize physical placement, standalone integration, routing changes, or GDS generation.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Subblock Readiness",
        "",
        _md_table(
            ["subblock", "category", "placement style", "metadata ready", "physical ready", "blocked by"],
            subblock_rows,
        ),
        "",
        "## Readiness Summary",
        "",
        "```json",
        json.dumps(report["readiness_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Consistency Checks",
        "",
        _md_table(["check", "value"], consistency_rows),
        "",
        "## Unresolved Items",
        "",
    ]
    lines.extend(f"- {item}" for item in report["unresolved_items"])
    lines.extend(
        [
            "",
            "## Entry Decisions",
            "",
            f"- can_create_experimental_opt_in_placement_plan: `{report['can_create_experimental_opt_in_placement_plan']}`",
            f"- can_modify_standalone: `{report['can_modify_standalone']}`",
            f"- can_generate_time_control_gds: `{report['can_generate_time_control_gds']}`",
            f"- can_enter_physical_placement: `{report['can_enter_physical_placement']}`",
            "",
        ]
    )
    return "\n".join(lines)
