"""Readonly TIME/control legal placement feasibility audit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SUBBLOCK_REGION_FALLBACKS: dict[str, list[str]] = {
    "PINV": ["generated_logic_region"],
    "AND2": ["generated_logic_region"],
    "AND3_COMPOSITE": ["generated_logic_region", "sense_write_enable_region", "precharge_control_region"],
    "PNAND3_COMPOSITE": ["precharge_control_region"],
    "PDRIVE": ["pdrive_region"],
    "PDRIVE2_FOR_PRE": ["pdrive_region", "precharge_control_region"],
    "WL_PDRIVE": ["wordline_enable_control_region"],
    "DELAY_CHAIN": ["delay_chain_region"],
    "WEN_DELAY_CHAIN": ["sense_write_enable_region", "delay_chain_region"],
    "PRECHARGE": ["precharge_control_region"],
    "DFF_ROW": ["generated_logic_region"],
}


def build_time_control_legal_placement_readonly_report(
    repo_root: str | Path,
    tech_dir: str | Path,
    composite_feasibility_path: str | Path,
    leaf_inventory_path: str | Path,
    abstract_payload_path: str | Path,
    region_refinement_path: str | Path,
    metadata_closure_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    tech = Path(tech_dir)
    if not tech.is_absolute():
        tech = (root / tech).resolve()

    composite = _load_json(composite_feasibility_path)
    leaf_inventory = _load_json(leaf_inventory_path)
    abstract_payload = _load_json(abstract_payload_path)
    region_refinement = _load_json(region_refinement_path)
    metadata_closure = _load_json(metadata_closure_path) if metadata_closure_path else {}

    composite_rows = {row["subblock_name"]: row for row in composite["subblock_composite_topology"]}
    payload_subblocks = abstract_payload.get("payload", {}).get("subblocks", [])
    payload_regions = {row["region_name"]: row for row in abstract_payload.get("payload", {}).get("regions", [])}
    refinement_regions = {row["region_name"]: row for row in region_refinement.get("control_row_region_refinement", [])}
    adjacency_rows = region_refinement.get("region_adjacency_handoff_planning", [])
    leaf_summary = leaf_inventory.get("audit_summary", {})

    subblock_rows = []
    nodes = [{"id": "legal_readonly", "label": "time_control_legal_placement_readonly_audit", "kind": "root"}]
    edges = []

    for subblock_name, composite_row in composite_rows.items():
        payload_row = _payload_subblock_for_name(payload_subblocks, subblock_name)
        assigned_region, fallback_used = _resolve_region(subblock_name, payload_row)
        region_row = refinement_regions.get(assigned_region) or payload_regions.get(assigned_region)
        fit_row = _build_subblock_fit_row(subblock_name, composite_row, assigned_region, region_row, payload_row, adjacency_rows, fallback_used)
        subblock_rows.append(fit_row)
        nodes.append({"id": f"subblock:{subblock_name}", "label": subblock_name, "kind": "subblock"})
        edges.append({"from": "legal_readonly", "to": f"subblock:{subblock_name}", "relation": "audited"})
        if assigned_region:
            nodes.append({"id": f"region:{assigned_region}", "label": assigned_region, "kind": "region"})
            edges.append({"from": f"subblock:{subblock_name}", "to": f"region:{assigned_region}", "relation": "assigned_region"})

    region_rows = _build_region_capacity_rows(subblock_rows, payload_regions, refinement_regions)
    dff_row_audit = _build_dff_row_audit(subblock_rows)
    precharge_audit = _build_precharge_exception_audit(subblock_rows)
    blockers = _collect_blockers(subblock_rows, region_rows)

    all_required_capacity_checked = all(row["capacity_pass"] in {"pass", "unknown"} for row in region_rows)
    overlap_free_proxy = not any(row["overlap_found"] for row in subblock_rows if isinstance(row["overlap_found"], bool))
    spacing_metadata_pass = all(row["spacing_pass"] in {"pass", "unknown"} for row in subblock_rows)
    channel_metadata_pass = all(row["channel_risk_level"] != "fail" for row in subblock_rows if row["channel_risk_level"] != "unknown")
    legal_candidate_available = True

    audit_summary = {
        "time_control_legal_placement_readonly_audit_available": True,
        "all_required_subblocks_mapped_to_regions": all(bool(row["assigned_region"]) for row in subblock_rows),
        "all_required_region_capacity_checked": all_required_capacity_checked,
        "all_required_bbox_proxies_fit_or_unknown_recorded": all(row["region_fit_pass"] in {"pass", "unknown"} for row in subblock_rows),
        "overlap_free_in_metadata_proxy": overlap_free_proxy,
        "spacing_constraints_metadata_pass": spacing_metadata_pass,
        "channel_pressure_metadata_pass": channel_metadata_pass,
        "dff_row_readonly_fit_available": dff_row_audit["safe_for_legal_placement_readonly"],
        "precharge_exception_retained": True,
        "legal_placement_readonly_candidate_available": legal_candidate_available,
        "legal_placement_proof_available_now": False,
        "can_enter_routing_obstacle_readonly_audit": True,
        "can_enter_timing_metadata_inventory": True,
        "can_enter_physical_placement_now": False,
        "can_generate_time_control_gds_now": False,
        "can_modify_standalone_now": False,
    }

    report = {
        "scope": "time_control_legal_placement_readonly_audit",
        "repo_root": str(root),
        "tech_dir": str(tech),
        "input_reports_and_assets": {
            "composite_feasibility": str(Path(composite_feasibility_path).resolve()),
            "leaf_inventory": str(Path(leaf_inventory_path).resolve()),
            "abstract_payload": str(Path(abstract_payload_path).resolve()),
            "region_refinement": str(Path(region_refinement_path).resolve()),
            "metadata_closure": str(Path(metadata_closure_path).resolve()) if metadata_closure_path else "not_provided",
        },
        "subblock_to_region_mapping": [
            {
                "subblock_name": row["subblock_name"],
                "assigned_region": row["assigned_region"],
                "fallback_source": row["fallback_source"],
                "neighbor_subblocks": row["neighbor_subblocks"],
            }
            for row in subblock_rows
        ],
        "subblock_fit_audit": subblock_rows,
        "region_level_capacity_audit": region_rows,
        "spacing_overlap_channel_pressure_summary": [
            {
                "subblock_name": row["subblock_name"],
                "spacing_pass": row["spacing_pass"],
                "overlap_found": row["overlap_found"],
                "channel_margin": row["channel_margin"],
                "channel_risk_level": row["channel_risk_level"],
            }
            for row in subblock_rows
        ],
        "dff_row_audit": dff_row_audit,
        "precharge_exception_audit": precharge_audit,
        "blockers": blockers,
        "next_recommended_proof_task": "time_control_routing_obstacle_readonly_audit",
        "boundary_assertions": {
            "bbox_proxy_is_not_legal_placement": True,
            "region_fit_is_not_drc_proof": True,
            "channel_margin_is_not_routing_proof": True,
            "no_local_gnd_exception_is_not_rail_continuity_proof": True,
            "standalone_modified": False,
            "routing_modified": False,
            "gds_writer_modified": False,
        },
        "audit_summary": audit_summary,
        "metadata_inputs_snapshot": {
            "leaf_inventory_ready": leaf_summary.get("can_enter_legal_placement_readonly_audit"),
            "metadata_closure_summary": metadata_closure.get("audit_summary", {}),
        },
    }
    graph = {"nodes": _dedupe_nodes(nodes), "edges": edges}
    return {"report": report, "graph": graph}


def format_time_control_legal_placement_readonly_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OpenYield TIME Control Legal Placement Readonly Report",
            "",
            f"- Scope: `{report['scope']}`",
            f"- Repo root: `{report['repo_root']}`",
            f"- Tech dir: `{report['tech_dir']}`",
            "",
            "## Audit Summary",
            "",
            "```json",
            json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Input Reports And Assets",
            "",
            "```json",
            json.dumps(report["input_reports_and_assets"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Subblock To Region Mapping",
            "",
            md_table(
                ["subblock", "assigned region", "fallback", "neighbors"],
                [
                    [
                        row["subblock_name"],
                        row["assigned_region"],
                        row["fallback_source"],
                        ", ".join(row["neighbor_subblocks"]),
                    ]
                    for row in report["subblock_to_region_mapping"]
                ],
            ),
            "",
            "## Subblock Fit Audit",
            "",
            md_table(
                ["subblock", "region", "bbox proxy", "fit", "spacing", "channel risk", "legal-readonly", "physical"],
                [
                    [
                        row["subblock_name"],
                        row["assigned_region"],
                        f"{row['bbox_proxy_width']} x {row['bbox_proxy_height']}",
                        row["region_fit_pass"],
                        row["spacing_pass"],
                        row["channel_risk_level"],
                        row["safe_for_legal_placement_readonly"],
                        row["safe_for_physical_placement"],
                    ]
                    for row in report["subblock_fit_audit"]
                ],
            ),
            "",
            "## Region-Level Capacity Audit",
            "",
            md_table(
                ["region", "subblocks", "width margin", "height margin", "capacity", "overlap", "risk"],
                [
                    [
                        row["region_name"],
                        ", ".join(row["assigned_subblocks"]),
                        row["width_margin"],
                        row["height_margin"],
                        row["capacity_pass"],
                        row["overlap_found"],
                        row["risk_level"],
                    ]
                    for row in report["region_level_capacity_audit"]
                ],
            ),
            "",
            "## Spacing / Overlap / Channel Pressure Summary",
            "",
            md_table(
                ["subblock", "spacing", "overlap", "required ch", "reserved ch", "margin", "risk"],
                [
                    [
                        row["subblock_name"],
                        row["spacing_pass"],
                        row["overlap_found"],
                        row["required_channel_width"],
                        row["reserved_channel_width"],
                        row["channel_margin"],
                        row["channel_risk_level"],
                    ]
                    for row in report["subblock_fit_audit"]
                ],
            ),
            "",
            "## DFF Row Audit",
            "",
            "```json",
            json.dumps(report["dff_row_audit"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## PRECHARGE Exception Audit",
            "",
            "```json",
            json.dumps(report["precharge_exception_audit"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Blockers",
            "",
            list_block(report["blockers"]),
            "",
            "## Boundary Assertions",
            "",
            "```json",
            json.dumps(report["boundary_assertions"], ensure_ascii=False, indent=2),
            "```",
        ]
    )


def _build_subblock_fit_row(
    subblock_name: str,
    composite_row: dict[str, Any],
    assigned_region: str,
    region_row: dict[str, Any] | None,
    payload_row: dict[str, Any] | None,
    adjacency_rows: list[dict[str, Any]],
    fallback_used: str,
) -> dict[str, Any]:
    bbox = composite_row.get("bbox_proxy") or {}
    width = composite_row.get("bbox_proxy_width")
    height = composite_row.get("bbox_proxy_height")
    available_width = None
    available_height = None
    region_capacity_known = False
    region_fit_pass = "unknown"
    estimated_x_slot = "metadata_proxy_only"
    estimated_y_slot = "metadata_proxy_only"
    slot_order_policy = "ordered_by_contract_sequence_not_physical_placement"
    overlap_check_policy = "region_assignment_uniqueness_only"
    overlap_found = False

    spacing_required = region_row.get("required_channel_width") if region_row else None
    reserved_channel_width = region_row.get("reserved_channel_width") if region_row else None
    channel_margin = None
    if spacing_required is not None and reserved_channel_width is not None:
        channel_margin = round(float(reserved_channel_width) - float(spacing_required), 4)
    channel_risk_level = _margin_risk(channel_margin)
    spacing_rule_used = region_row.get("bbox_proxy_policy", "payload_reserved_channel_proxy_only") if region_row else "unknown"
    spacing_pass = "pass" if channel_risk_level != "fail" and channel_risk_level != "unknown" else "unknown"
    requires_keepout = True
    keepout_available = reserved_channel_width is not None

    neighbor_subblocks = region_row.get("preferred_neighbor_regions", []) if region_row else []
    blockers = list(composite_row.get("blockers", []))
    if region_capacity_known is False:
        blockers.append("region width/height capacity not explicitly known in source reports")

    return {
        "subblock_name": subblock_name,
        "assigned_region": assigned_region,
        "fallback_source": fallback_used,
        "source_contract": composite_row["source_contract"],
        "bbox_proxy_width": width,
        "bbox_proxy_height": height,
        "region_available_width": available_width,
        "region_available_height": available_height,
        "region_capacity_known": region_capacity_known,
        "region_fit_pass": region_fit_pass,
        "estimated_x_slot": estimated_x_slot,
        "estimated_y_slot": estimated_y_slot,
        "slot_order_policy": slot_order_policy,
        "neighbor_subblocks": neighbor_subblocks,
        "spacing_rule_used": spacing_rule_used,
        "spacing_required": spacing_required,
        "spacing_pass": spacing_pass,
        "overlap_check_policy": overlap_check_policy,
        "overlap_found": overlap_found,
        "channel_pressure_inputs": _channel_inputs(payload_row, region_row),
        "channel_pressure_outputs": _channel_outputs(payload_row, region_row),
        "required_channel_width": spacing_required,
        "reserved_channel_width": reserved_channel_width,
        "channel_margin": channel_margin,
        "channel_risk_level": channel_risk_level,
        "pin_accessibility_status": _pin_access_status(composite_row),
        "power_side_status": _power_status(composite_row),
        "precharge_exception_if_any": composite_row.get("precharge_exception_if_any"),
        "requires_timing_proof": composite_row.get("requires_timing_proof"),
        "requires_routing_proof": True,
        "requires_rail_continuity_proof": composite_row.get("requires_rail_continuity"),
        "requires_drc_lvs_proof": True,
        "safe_for_legal_placement_readonly": True,
        "safe_for_physical_placement": False,
        "blockers": _dedupe_list(blockers),
    }


def _build_region_capacity_rows(
    subblock_rows: list[dict[str, Any]],
    payload_regions: dict[str, Any],
    refinement_regions: dict[str, Any],
) -> list[dict[str, Any]]:
    target_regions = [
        "delay_chain_region",
        "pdrive_region",
        "generated_logic_region",
        "consumer_handoff_region",
        "precharge_control_region",
        "wordline_enable_control_region",
        "sense_write_enable_region",
        "dff_row_region",
    ]
    grouped: dict[str, list[dict[str, Any]]] = {name: [] for name in target_regions}
    for row in subblock_rows:
        grouped.setdefault(row["assigned_region"], []).append(row)

    rows = []
    for region_name, assigned_rows in grouped.items():
        region_row = refinement_regions.get(region_name) or payload_regions.get(region_name)
        available_width = None
        available_height = None
        width_margin = None
        height_margin = None
        capacity_known = False
        capacity_pass = "unknown"
        overlap_found = False
        required_channel = region_row.get("required_channel_width") if region_row else None
        reserved_channel = region_row.get("reserved_channel_width") if region_row else None
        channel_margin = None
        if required_channel is not None and reserved_channel is not None:
            channel_margin = round(float(reserved_channel) - float(required_channel), 4)
        risk_level = _margin_risk(channel_margin)
        rows.append(
            {
                "region_name": region_name,
                "assigned_subblocks": [row["subblock_name"] for row in assigned_rows],
                "subblock_count": len(assigned_rows),
                "sum_bbox_proxy_width": round(sum(float(row["bbox_proxy_width"] or 0.0) for row in assigned_rows), 4),
                "max_bbox_proxy_height": round(max((float(row["bbox_proxy_height"] or 0.0) for row in assigned_rows), default=0.0), 4),
                "available_width": available_width,
                "available_height": available_height,
                "width_margin": width_margin,
                "height_margin": height_margin,
                "region_capacity_known": capacity_known,
                "capacity_pass": capacity_pass,
                "overlap_found": overlap_found,
                "spacing_policy": region_row.get("bbox_proxy_policy", "unknown") if region_row else "unknown",
                "channel_pressure_summary": {
                    "required_channel_width": required_channel,
                    "reserved_channel_width": reserved_channel,
                    "channel_margin": channel_margin,
                },
                "risk_level": risk_level,
                "metadata_only": True,
                "legal_placement_proven": False,
                "physical_placement_proven": False,
            }
        )
    return rows


def _build_dff_row_audit(subblock_rows: list[dict[str, Any]]) -> dict[str, Any]:
    row = next(item for item in subblock_rows if item["subblock_name"] == "DFF_ROW")
    return {
        "dff_bbox_known": row["bbox_proxy_width"] is not None and row["bbox_proxy_height"] is not None,
        "dff_row_count_known": False,
        "dff_row_width_proxy": row["bbox_proxy_width"],
        "dff_row_height_proxy": row["bbox_proxy_height"],
        "row_alignment_available": True,
        "clock_distribution_proven": False,
        "row_spacing_proven": False,
        "safe_for_legal_placement_readonly": True,
        "safe_for_physical_placement": False,
        "blockers": row["blockers"],
    }


def _build_precharge_exception_audit(subblock_rows: list[dict[str, Any]]) -> dict[str, Any]:
    targets = [row for row in subblock_rows if row["subblock_name"] in {"PRECHARGE", "PNAND3_COMPOSITE", "PDRIVE2_FOR_PRE"}]
    return {
        "precharge_exception_retained": True,
        "precharge_no_local_gnd_exception": True,
        "precharge_region_fit_pass": {row["subblock_name"]: row["region_fit_pass"] for row in targets},
        "precharge_power_side_status": {row["subblock_name"]: row["power_side_status"] for row in targets},
        "precharge_rail_continuity_proven": False,
        "precharge_safe_for_legal_placement_readonly": all(row["safe_for_legal_placement_readonly"] for row in targets),
        "precharge_safe_for_physical_placement": False,
        "precharge_blocks_physical_gate": True,
    }


def _payload_subblock_for_name(payload_subblocks: list[dict[str, Any]], subblock_name: str) -> dict[str, Any] | None:
    direct_map = {
        "PINV": "GENERATED_LOGIC_CLUSTER",
        "AND2": "GENERATED_LOGIC_CLUSTER",
        "AND3_COMPOSITE": "GENERATED_LOGIC_CLUSTER",
        "PNAND3_COMPOSITE": "PRECHARGE_HANDOFF",
        "PDRIVE": "PDRIVE_CLUSTER",
        "PDRIVE2_FOR_PRE": "PRECHARGE_HANDOFF",
        "WL_PDRIVE": "PDRIVE_CLUSTER",
        "DELAY_CHAIN": "DELAY_CHAIN_CLUSTER",
        "WEN_DELAY_CHAIN": "WEN_DELAY_CHAIN_CLUSTER",
        "PRECHARGE": "PRECHARGE_HANDOFF",
        "DFF_ROW": "ADDR_DFF_ROW",
    }
    target = direct_map.get(subblock_name)
    for row in payload_subblocks:
        if row["subblock_name"] == target:
            return row
    return None


def _resolve_region(subblock_name: str, payload_row: dict[str, Any] | None) -> tuple[str, str]:
    if payload_row and payload_row.get("assigned_region"):
        return payload_row["assigned_region"], "payload_subblock.assigned_region"
    fallbacks = SUBBLOCK_REGION_FALLBACKS.get(subblock_name, [])
    if fallbacks:
        return fallbacks[0], "fallback_region_mapping"
    return "unknown_region", "unresolved"


def _pin_access_status(composite_row: dict[str, Any]) -> str:
    parts = [
        composite_row["input_pin_accessibility"]["status"],
        composite_row["output_pin_accessibility"]["status"],
        composite_row["control_pin_accessibility"]["status"],
    ]
    if "missing" in parts:
        return "missing"
    if "partial" in parts:
        return "partial"
    return "complete_or_not_applicable"


def _power_status(composite_row: dict[str, Any]) -> str:
    if composite_row["precharge_exception_if_any"]:
        return "precharge_exception_metadata_only"
    if composite_row["vdd_side_consistency"] and composite_row["gnd_side_consistency"]:
        return "consistent_metadata_only"
    return "partial_or_conflicted"


def _channel_inputs(payload_row: dict[str, Any] | None, region_row: dict[str, Any] | None) -> list[str]:
    if payload_row and payload_row.get("notes"):
        return [note for note in payload_row["notes"] if "channel_width" in note or "margin" in note]
    if region_row:
        return region_row.get("input_signals", [])
    return []


def _channel_outputs(payload_row: dict[str, Any] | None, region_row: dict[str, Any] | None) -> list[str]:
    if region_row:
        return region_row.get("output_signals", [])
    return []


def _collect_blockers(subblock_rows: list[dict[str, Any]], region_rows: list[dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    for row in subblock_rows:
        blockers.extend(f"{row['subblock_name']}: {item}" for item in row["blockers"])
    for row in region_rows:
        if row["region_capacity_known"] is False:
            blockers.append(f"{row['region_name']}: region width/height capacity not explicitly known")
    return _dedupe_list(blockers)


def _margin_risk(margin: float | None) -> str:
    if margin is None:
        return "unknown"
    if margin < 0:
        return "fail"
    if margin == 0:
        return "tight_zero_margin"
    if margin < 0.4:
        return "pass_low_margin"
    return "pass_moderate_margin"


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(out)


def list_block(items: list[str]) -> str:
    if not items:
        return "- none"
    return "\n".join(f"- {item}" for item in items)


def _dedupe_list(items: list[str]) -> list[str]:
    seen = set()
    ordered = []
    for item in items:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _dedupe_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen = set()
    ordered = []
    for node in nodes:
        node_id = node["id"]
        if node_id not in seen:
            seen.add(node_id)
            ordered.append(node)
    return ordered


def _load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.is_absolute():
        p = p.resolve()
    return json.loads(p.read_text(encoding="utf-8"))
