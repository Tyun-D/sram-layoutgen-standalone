"""Read-only default-off prototype plan for future OpenYield TIME control placement."""

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


def build_time_control_opt_in_prototype_plan_report(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    openyield_root = Path(openyield_root)
    contracts_path = Path(contracts_path)
    tech_dir = Path(tech_dir)

    readiness = _load_json("docs/openyield_time_control_placement_readiness_report.json")
    metadata_closure = _load_json("docs/openyield_time_control_metadata_closure_report.json")

    if not readiness["can_create_experimental_opt_in_placement_plan"]:
        raise ValueError("Stage C does not permit a default-off experimental opt-in prototype plan.")

    phased_steps = [
        {
            "step_name": "prototype_config_surface_only",
            "allowed": True,
            "default_enabled": False,
            "touches": ["future spec/config surface only"],
            "forbidden": ["standalone.py", "routing", "gds writer"],
            "notes": ["Do not wire this into the active generator path yet."],
        },
        {
            "step_name": "abstract_subblock_row_packing_plan",
            "allowed": True,
            "default_enabled": False,
            "touches": ["metadata plan objects", "abstract region packing"],
            "forbidden": ["physical placement", "GDS generation", "real routed wires"],
            "notes": ["Only encode rows, ordering, neighbor intent, and handoff placeholders."],
        },
        {
            "step_name": "consumer_handoff_stub_contracts",
            "allowed": True,
            "default_enabled": False,
            "touches": ["metadata-only consumer handoff reservations"],
            "forbidden": ["sense/write/WL physical rewiring", "shared rail"],
            "notes": ["Keep peripheral routing on legacy path until later proof exists."],
        },
        {
            "step_name": "standalone_opt_in_gate_review",
            "allowed": False,
            "default_enabled": False,
            "touches": ["standalone.py only after a later gate"],
            "forbidden": ["current turn integration"],
            "notes": ["Blocked until later physical/layout proof exists."],
        },
    ]

    prototype_contract = {
        "default_enabled": False,
        "legacy_path_unchanged": True,
        "standalone_py_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "physical_gds_generated": False,
        "shared_rail_enabled": False,
        "uses_time_as_single_macro": False,
        "allows_only_metadata_prototype": True,
    }

    candidate_interfaces = [
        {
            "name": "ADDR_DFF_ROW",
            "future_plan_kind": "abstract_dff_row",
            "must_remain_default_off": True,
            "blocked_by": ["addr bus physical proof missing", "standalone integration blocked"],
        },
        {
            "name": "DATA_DFF_ROW",
            "future_plan_kind": "abstract_dff_row",
            "must_remain_default_off": True,
            "blocked_by": ["data bus physical proof missing", "standalone integration blocked"],
        },
        {
            "name": "GENERATED_LOGIC_CLUSTER",
            "future_plan_kind": "stdcell_row_abstract_cluster",
            "must_remain_default_off": True,
            "blocked_by": ["stdcell physical library proof missing", "routing proof missing"],
        },
        {
            "name": "PRECHARGE_HANDOFF",
            "future_plan_kind": "consumer_handoff_reservation_only",
            "must_remain_default_off": True,
            "blocked_by": ["rail continuity proof missing", "routing proof missing"],
        },
        {
            "name": "WORDLINEDRIVER_HANDOFF",
            "future_plan_kind": "consumer_handoff_reservation_only",
            "must_remain_default_off": True,
            "blocked_by": ["wordline routing proof missing", "decoder coordination unresolved"],
        },
    ]

    consistency_checks = {
        "default_off_experimental_opt_in_prototype_plan_available": True,
        "stage_c_gate_passed": True,
        "time_control_metadata_closure_available": bool(
            metadata_closure["consistency_checks"]["time_control_metadata_closure_available"]
        ),
        "legacy_path_unchanged": True,
        "default_enabled": False,
        "can_modify_standalone_now": False,
        "can_generate_time_control_gds_now": False,
        "can_enter_physical_placement_now": False,
        "can_claim_routing_proof": False,
        "safe_for_metadata_prototype_only": True,
    }

    unresolved_items = [
        "This plan is intentionally non-executable in the main generator path.",
        "No standalone integration is allowed in this stage.",
        "No TIME/control physical placement is allowed in this stage.",
        "No TIME/control GDS is allowed in this stage.",
        "No routing proof, DRC proof, or LVS proof is added by this plan.",
        "Decoder/TIME boundary still needs a later coordinated physical proof.",
    ]

    report = {
        "scope": "stage_d_openyield_time_control_opt_in_prototype_plan",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(contracts_path.resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "source_reports": {
            "time_control_placement_readiness": readiness.get("scope"),
            "time_control_metadata_closure": metadata_closure.get("scope"),
        },
        "prototype_contract": prototype_contract,
        "phased_steps": phased_steps,
        "candidate_interfaces": candidate_interfaces,
        "consistency_checks": consistency_checks,
        "unresolved_items": unresolved_items,
        "audit_summary": {
            "default_off_experimental_opt_in_prototype_plan_available": True,
            "default_enabled": False,
            "legacy_path_unchanged": True,
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "default_enabled": False,
        "legacy_path_unchanged": True,
        "can_modify_standalone_now": False,
        "can_generate_time_control_gds_now": False,
        "can_enter_physical_placement_now": False,
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
    }

    graph = {
        "scope": report["scope"],
        "nodes": (
            [{"id": step["step_name"], "kind": "prototype_step"} for step in phased_steps]
            + [{"id": item["name"], "kind": "candidate_interface"} for item in candidate_interfaces]
        ),
        "edges": [
            {
                "source": item["name"],
                "target": "prototype_config_surface_only",
                "relation": "candidate_for_future_opt_in",
            }
            for item in candidate_interfaces
        ],
        "summary": report["audit_summary"],
    }
    return report, graph


def build_time_control_opt_in_prototype_plan_markdown(report: dict[str, Any]) -> str:
    step_rows = [
        [
            item["step_name"],
            item["allowed"],
            item["default_enabled"],
            ", ".join(item["touches"]),
            ", ".join(item["forbidden"]),
        ]
        for item in report["phased_steps"]
    ]
    interface_rows = [
        [
            item["name"],
            item["future_plan_kind"],
            item["must_remain_default_off"],
            ", ".join(item["blocked_by"]),
        ]
        for item in report["candidate_interfaces"]
    ]
    consistency_rows = [[key, value] for key, value in report["consistency_checks"].items()]
    lines = [
        "# OpenYield TIME Control Default-Off Prototype Plan",
        "",
        "This is a planning artifact only. It does not modify standalone integration, routing, GDS writing, or physical placement.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Prototype Contract",
        "",
        "```json",
        json.dumps(report["prototype_contract"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Phased Steps",
        "",
        _md_table(["step", "allowed", "default enabled", "touches", "forbidden"], step_rows),
        "",
        "## Candidate Interfaces",
        "",
        _md_table(["interface", "future plan kind", "must stay default-off", "blocked by"], interface_rows),
        "",
        "## Consistency Checks",
        "",
        _md_table(["check", "value"], consistency_rows),
        "",
        "## Unresolved Items",
        "",
    ]
    lines.extend(f"- {item}" for item in report["unresolved_items"])
    return "\n".join(lines)
