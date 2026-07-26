"""Readonly TIME/control composite internal placement feasibility audit."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


SUBBLOCK_ORDER = [
    "PINV",
    "AND2",
    "AND3_COMPOSITE",
    "PNAND3_COMPOSITE",
    "PDRIVE",
    "PDRIVE2_FOR_PRE",
    "WL_PDRIVE",
    "DELAY_CHAIN",
    "WEN_DELAY_CHAIN",
    "PRECHARGE",
    "DFF_ROW",
]

SUBBLOCK_SPECS: dict[str, dict[str, Any]] = {
    "PINV": {
        "contract_name": "PINV_GENERATED_LOGIC_CONTRACT",
        "topology": "single_inverter",
        "internal_ordering": "single_stage",
        "input_ports": ["A"],
        "output_ports": ["Z"],
        "control_ports": [],
        "internal_net_list": [],
        "classification": "ready_for_readonly_legal_placement_planning",
        "payload_subblock": "GENERATED_LOGIC_CLUSTER",
        "region_interfaces": [],
    },
    "AND2": {
        "contract_name": "AND2_GENERATED_LOGIC_CONTRACT",
        "topology": "nand2_plus_inv",
        "internal_ordering": "gen_nand2 -> gen_inv",
        "input_ports": ["A", "B"],
        "output_ports": ["Z"],
        "control_ports": [],
        "internal_net_list": ["n_ab"],
        "classification": "ready_for_readonly_feasibility_but_missing_timing",
        "payload_subblock": "GENERATED_LOGIC_CLUSTER",
        "region_interfaces": [],
    },
    "AND3_COMPOSITE": {
        "contract_name": "AND3_COMPOSITE_GENERATED_LOGIC_CONTRACT",
        "topology": "nand2_plus_inv_plus_nand2_plus_inv",
        "internal_ordering": "gen_nand2 -> gen_inv -> gen_nand2 -> gen_inv",
        "input_ports": ["A", "B", "C"],
        "output_ports": ["Z"],
        "control_ports": [],
        "internal_net_list": ["ab_n", "ab", "abc_n"],
        "classification": "ready_for_readonly_feasibility_but_missing_timing",
        "payload_subblock": "GENERATED_LOGIC_CLUSTER",
        "region_interfaces": [
            "TIME_CONTROL_TO_WRITEDRIVER_INTERFACE",
            "TIME_CONTROL_TO_SENSEAMP_INTERFACE",
        ],
    },
    "PNAND3_COMPOSITE": {
        "contract_name": "PNAND3_COMPOSITE_GENERATED_LOGIC_CONTRACT",
        "topology": "nand2_plus_inv_plus_nand2",
        "internal_ordering": "gen_nand2 -> gen_inv -> gen_nand2",
        "input_ports": ["A", "B", "C"],
        "output_ports": ["ZN"],
        "control_ports": [],
        "internal_net_list": ["ab_n", "ab"],
        "classification": "ready_for_readonly_feasibility_but_precharge_exception",
        "payload_subblock": "PRECHARGE_HANDOFF",
        "region_interfaces": ["TIME_CONTROL_TO_PRECHARGE_INTERFACE"],
    },
    "PDRIVE": {
        "contract_name": "PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT",
        "topology": "buffer_chain",
        "internal_ordering": "repeated gen_inv buffer stages",
        "input_ports": ["A"],
        "output_ports": ["Z"],
        "control_ports": [],
        "internal_net_list": ["stage_0", "stage_1", "stage_2"],
        "classification": "ready_for_readonly_feasibility_but_missing_timing",
        "payload_subblock": "PDRIVE_CLUSTER",
        "region_interfaces": [],
    },
    "PDRIVE2_FOR_PRE": {
        "contract_name": "PDRIVE2_FOR_PRE_CHAIN_GENERATED_LOGIC_CONTRACT",
        "topology": "buffer_chain",
        "internal_ordering": "repeated gen_inv buffer stages",
        "input_ports": ["A"],
        "output_ports": ["Z"],
        "control_ports": [],
        "internal_net_list": ["stage_0"],
        "classification": "ready_for_readonly_feasibility_but_precharge_exception",
        "payload_subblock": "PRECHARGE_HANDOFF",
        "region_interfaces": ["TIME_CONTROL_TO_PRECHARGE_INTERFACE"],
    },
    "WL_PDRIVE": {
        "contract_name": "WL_PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT",
        "topology": "buffer_chain",
        "internal_ordering": "repeated gen_inv buffer stages",
        "input_ports": ["A"],
        "output_ports": ["Z"],
        "control_ports": [],
        "internal_net_list": ["stage_0"],
        "classification": "ready_for_readonly_feasibility_but_missing_timing",
        "payload_subblock": "PDRIVE_CLUSTER",
        "region_interfaces": ["TIME_CONTROL_TO_WORDLINEDRIVER_INTERFACE"],
    },
    "DELAY_CHAIN": {
        "contract_name": "DELAY_CHAIN_GENERATED_LOGIC_CONTRACT",
        "topology": "delay_chain",
        "internal_ordering": "repeated gen_delay_inv stages",
        "input_ports": ["A"],
        "output_ports": ["Z"],
        "control_ports": [],
        "internal_net_list": [f"stage_{index}" for index in range(8)],
        "classification": "ready_for_readonly_feasibility_but_missing_timing",
        "payload_subblock": "DELAY_CHAIN_CLUSTER",
        "region_interfaces": [],
    },
    "WEN_DELAY_CHAIN": {
        "contract_name": "WEN_DELAY_CHAIN_CONDITIONAL_GENERATED_LOGIC_CONTRACT",
        "topology": "conditional_delay_chain",
        "internal_ordering": "repeated gen_delay_inv stages",
        "input_ports": ["A"],
        "output_ports": ["Z"],
        "control_ports": [],
        "internal_net_list": [f"stage_{index}" for index in range(5)],
        "classification": "ready_for_readonly_feasibility_but_missing_timing",
        "payload_subblock": "WEN_DELAY_CHAIN_CLUSTER",
        "region_interfaces": [
            "TIME_CONTROL_TO_WRITEDRIVER_INTERFACE",
            "TIME_CONTROL_TO_SENSEAMP_INTERFACE",
        ],
    },
    "PRECHARGE": {
        "contract_name": "metadata_source_not_found",
        "topology": "single_precharge_leaf",
        "internal_ordering": "gen_precharge",
        "input_ports": [],
        "output_ports": ["BL", "BR"],
        "control_ports": ["ENB"],
        "internal_net_list": [],
        "classification": "ready_for_readonly_feasibility_but_precharge_exception",
        "payload_subblock": "PRECHARGE_HANDOFF",
        "region_interfaces": ["TIME_CONTROL_TO_PRECHARGE_INTERFACE"],
    },
    "DFF_ROW": {
        "contract_name": "metadata_source_not_found",
        "topology": "repeated_dff_row",
        "internal_ordering": "repeated dff in row order",
        "input_ports": ["D", "CLK"],
        "output_ports": ["Q"],
        "control_ports": ["CLK"],
        "internal_net_list": [],
        "classification": "blocked_by_row_placement_requirement",
        "payload_subblock": "ADDR_DFF_ROW",
        "region_interfaces": [],
    },
}


def build_time_control_composite_feasibility_report(
    repo_root: str | Path,
    tech_dir: str | Path,
    leaf_inventory_path: str | Path,
    power_rail_audit_path: str | Path,
    generated_logic_contracts_path: str | Path,
    abstract_payload_path: str | Path,
    region_refinement_path: str | Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    tech = Path(tech_dir)
    if not tech.is_absolute():
        tech = (root / tech).resolve()

    leaf_inventory = _load_json(leaf_inventory_path)
    power_rail_audit = _load_json(power_rail_audit_path)
    generated_logic = _load_json(generated_logic_contracts_path)
    abstract_payload = _load_json(abstract_payload_path)
    region_refinement = _load_json(region_refinement_path)

    leaf_rows = leaf_inventory["leaf_gds_bbox_pin_side_inventory"]
    subblock_map = {row["subblock_name"]: row for row in leaf_inventory["subblock_to_leaf_mapping"]}
    contract_map = {row["contract_name"]: row for row in generated_logic.get("generated_logic_contract_list", [])}
    payload_subblocks = {row["subblock_name"]: row for row in abstract_payload.get("payload", {}).get("subblocks", [])}
    handoffs = {row["interface_name"]: row for row in region_refinement.get("grouped_planning_interface_refinement", [])}
    region_adjacency = region_refinement.get("region_adjacency_handoff_planning", [])

    recommended_leafs = {(row["macro_name"], row["variant_name"]): row for row in leaf_rows if row["recommended_for_future_planning"]}
    composite_rows = []
    graph_nodes = [{"id": "composite_feasibility", "label": "time_control_composite_internal_placement_feasibility", "kind": "root"}]
    graph_edges = []

    for subblock_name in SUBBLOCK_ORDER:
        spec = SUBBLOCK_SPECS[subblock_name]
        mapping_row = subblock_map[subblock_name]
        payload_row = payload_subblocks.get(spec["payload_subblock"])
        contract_row = contract_map.get(spec["contract_name"])
        interface_rows = [handoffs[name] for name in spec["region_interfaces"] if name in handoffs]
        leaf_sequence = _resolve_leaf_sequence(mapping_row, contract_row)
        leaf_variant_rows = [_recommended_leaf_row(recommended_leafs, macro_name) for macro_name in leaf_sequence]
        row = _build_composite_row(
            subblock_name=subblock_name,
            spec=spec,
            mapping_row=mapping_row,
            payload_row=payload_row,
            contract_row=contract_row,
            interface_rows=interface_rows,
            region_adjacency=region_adjacency,
            leaf_variant_rows=leaf_variant_rows,
            power_rail_audit=power_rail_audit,
        )
        composite_rows.append(row)
        graph_nodes.append({"id": f"subblock:{subblock_name}", "label": subblock_name, "kind": "subblock"})
        graph_edges.append({"from": "composite_feasibility", "to": f"subblock:{subblock_name}", "relation": "audited"})
        for index, leaf_macro in enumerate(row["leaf_sequence"]):
            graph_nodes.append(
                {
                    "id": f"subblock:{subblock_name}:leaf:{index}",
                    "label": f"{leaf_macro}[{index}]",
                    "kind": "leaf_reference",
                }
            )
            graph_edges.append(
                {
                    "from": f"subblock:{subblock_name}",
                    "to": f"subblock:{subblock_name}:leaf:{index}",
                    "relation": "uses_leaf",
                }
            )

    precharge_row = next(row for row in composite_rows if row["subblock_name"] == "PRECHARGE")
    dff_row = next(row for row in composite_rows if row["subblock_name"] == "DFF_ROW")
    blockers = _collect_blockers(composite_rows)
    decision = {
        "time_control_composite_internal_placement_feasibility_available": True,
        "all_required_subblocks_analyzed": len(composite_rows) == len(SUBBLOCK_ORDER),
        "all_required_leaf_sequences_available": all(bool(row["leaf_sequence"]) for row in composite_rows),
        "all_required_bbox_proxies_available": all(row["bbox_proxy"] is not None for row in composite_rows),
        "all_required_external_pin_accessibility_available": all(
            row["input_pin_accessibility"]["status"] != "missing"
            and row["output_pin_accessibility"]["status"] != "missing"
            and row["control_pin_accessibility"]["status"] != "missing"
            for row in composite_rows
        ),
        "all_required_power_side_compatibility_checked": True,
        "composite_internal_routing_proven": False,
        "timing_proof_available": False,
        "rail_continuity_proven": False,
        "precharge_exception_retained": True,
        "can_enter_legal_placement_readonly_audit": True,
        "can_enter_routing_obstacle_readonly_audit": True,
        "can_enter_timing_metadata_inventory": True,
        "can_enter_physical_placement_now": False,
        "can_generate_time_control_gds_now": False,
        "can_modify_standalone_now": False,
    }

    report = {
        "scope": "time_control_composite_internal_placement_feasibility_audit",
        "repo_root": str(root),
        "tech_dir": str(tech),
        "input_reports_and_assets": {
            "leaf_inventory": str(Path(leaf_inventory_path).resolve()),
            "power_rail_audit": str(Path(power_rail_audit_path).resolve()),
            "generated_logic_contracts": str(Path(generated_logic_contracts_path).resolve()),
            "abstract_payload": str(Path(abstract_payload_path).resolve()),
            "region_refinement": str(Path(region_refinement_path).resolve()),
        },
        "subblock_composite_topology": composite_rows,
        "leaf_sequence_bbox_proxy_table": [
            {
                "subblock_name": row["subblock_name"],
                "leaf_sequence": row["leaf_sequence"],
                "bbox_proxy": row["bbox_proxy"],
                "bbox_proxy_width": row["bbox_proxy_width"],
                "bbox_proxy_height": row["bbox_proxy_height"],
                "classification": row["feasibility_classification"],
            }
            for row in composite_rows
        ],
        "pin_accessibility_summary": [
            {
                "subblock_name": row["subblock_name"],
                "input_pin_accessibility": row["input_pin_accessibility"],
                "output_pin_accessibility": row["output_pin_accessibility"],
                "control_pin_accessibility": row["control_pin_accessibility"],
                "internal_net_accessibility": row["internal_net_accessibility"],
            }
            for row in composite_rows
        ],
        "power_side_compatibility_summary": [
            {
                "subblock_name": row["subblock_name"],
                "vdd_side_consistency": row["vdd_side_consistency"],
                "gnd_side_consistency": row["gnd_side_consistency"],
                "power_side_policy": row["power_side_policy"],
                "precharge_exception_if_any": row["precharge_exception_if_any"],
            }
            for row in composite_rows
        ],
        "precharge_exception_section": {
            "subblock_name": precharge_row["subblock_name"],
            "precharge_exception_if_any": precharge_row["precharge_exception_if_any"],
            "safe_for_composite_readonly_feasibility": precharge_row["safe_for_composite_readonly_feasibility"],
            "safe_for_legal_placement_readonly": precharge_row["safe_for_legal_placement_readonly"],
            "safe_for_physical_placement": precharge_row["safe_for_physical_placement"],
            "blockers": precharge_row["blockers"],
        },
        "dff_row_feasibility_section": {
            "subblock_name": dff_row["subblock_name"],
            "requires_row_alignment": dff_row["requires_row_alignment"],
            "row_alignment_available": dff_row["row_alignment_available"],
            "safe_for_composite_readonly_feasibility": dff_row["safe_for_composite_readonly_feasibility"],
            "safe_for_legal_placement_readonly": dff_row["safe_for_legal_placement_readonly"],
            "safe_for_physical_placement": dff_row["safe_for_physical_placement"],
            "blockers": dff_row["blockers"],
        },
        "feasibility_classification": [
            {
                "subblock_name": row["subblock_name"],
                "classification": row["feasibility_classification"],
                "safe_for_composite_readonly_feasibility": row["safe_for_composite_readonly_feasibility"],
                "safe_for_legal_placement_readonly": row["safe_for_legal_placement_readonly"],
                "safe_for_physical_placement": row["safe_for_physical_placement"],
            }
            for row in composite_rows
        ],
        "blockers": blockers,
        "next_recommended_proof_task": "time_control_legal_placement_readonly_audit",
        "boundary_assertions": {
            "bbox_proxy_is_not_legal_placement": True,
            "pin_accessibility_is_not_routing_proof": True,
            "power_side_consistency_is_not_rail_continuity_proof": True,
            "readonly_feasibility_is_not_physical_ready": True,
            "standalone_modified": False,
            "routing_modified": False,
            "gds_writer_modified": False,
        },
        "audit_summary": decision,
    }
    graph = {"nodes": _dedupe_nodes(graph_nodes), "edges": graph_edges}
    return {"report": report, "graph": graph}


def _build_composite_row(
    *,
    subblock_name: str,
    spec: dict[str, Any],
    mapping_row: dict[str, Any],
    payload_row: dict[str, Any] | None,
    contract_row: dict[str, Any] | None,
    interface_rows: list[dict[str, Any]],
    region_adjacency: list[dict[str, Any]],
    leaf_variant_rows: list[dict[str, Any] | None],
    power_rail_audit: dict[str, Any],
) -> dict[str, Any]:
    leaf_count = len(leaf_variant_rows)
    bbox_proxy = _bbox_proxy(leaf_variant_rows)
    input_access = _port_accessibility(leaf_variant_rows, spec["input_ports"], "input")
    output_access = _port_accessibility(leaf_variant_rows, spec["output_ports"], "output")
    control_access = _port_accessibility(leaf_variant_rows, spec["control_ports"], "control")
    internal_access = _internal_net_accessibility(spec["internal_net_list"], leaf_variant_rows)
    vdd_consistency, gnd_consistency, power_policy = _power_side_consistency(leaf_variant_rows, subblock_name)
    spacing = _spacing_and_keepout(payload_row, region_adjacency, interface_rows)
    routing_proven = False
    timing_available = False
    rail_continuity = False
    safe_readonly_feasibility = bbox_proxy is not None and input_access["status"] != "missing" and output_access["status"] != "missing"
    safe_legal_readonly = safe_readonly_feasibility and spec["classification"] != "blocked_by_missing_leaf_geometry"

    blockers = []
    if not leaf_variant_rows or any(row is None for row in leaf_variant_rows):
        blockers.append("missing recommended leaf geometry")
    if input_access["status"] == "missing" or output_access["status"] == "missing":
        blockers.append("missing external pin accessibility")
    if spec["classification"] == "ready_for_readonly_feasibility_but_missing_timing":
        blockers.append("timing proof required")
    if spec["classification"] == "ready_for_readonly_feasibility_but_missing_routing":
        blockers.append("routing proof required")
    if spec["classification"] == "ready_for_readonly_feasibility_but_precharge_exception":
        blockers.append("precharge power exception retained")
    if spec["classification"] == "blocked_by_row_placement_requirement":
        blockers.append("row placement proof required")
    if mapping_row:
        blockers.extend(mapping_row.get("blockers", []))
    if payload_row:
        blockers.extend(payload_row.get("blocked_by", []))
    for item in interface_rows:
        blockers.extend(item.get("blocked_by", []))
    if not vdd_consistency:
        blockers.append("vdd side conflict or unknown")
    if not gnd_consistency and subblock_name != "PRECHARGE":
        blockers.append("gnd side conflict or unknown")
    if subblock_name == "PRECHARGE":
        blockers.append("no local GND proof and no across-abutment rail continuity proof")
    if spec["classification"] != "ready_for_readonly_legal_placement_planning":
        safe_legal_readonly = safe_legal_readonly and spec["classification"] in {
            "ready_for_readonly_feasibility_but_missing_timing",
            "ready_for_readonly_feasibility_but_missing_routing",
            "ready_for_readonly_feasibility_but_precharge_exception",
            "blocked_by_row_placement_requirement",
        }
    row_alignment_available = bool(payload_row) if spec["classification"] == "blocked_by_row_placement_requirement" else True
    precharge_exception = None
    if subblock_name in {"PRECHARGE", "PNAND3_COMPOSITE", "PDRIVE2_FOR_PRE"}:
        precharge_exception = "intentional_no_local_gnd_metadata_exception"

    notes = []
    if contract_row:
        notes.extend(contract_row.get("notes", []))
    if payload_row:
        notes.extend(payload_row.get("notes", []))

    return {
        "subblock_name": subblock_name,
        "source_contract": spec["contract_name"],
        "leaf_sequence": [row["macro_name"] if row else "missing" for row in leaf_variant_rows],
        "leaf_macros": list(dict.fromkeys(row["macro_name"] for row in leaf_variant_rows if row)),
        "recommended_leaf_variants": [row["variant_name"] if row else "missing" for row in leaf_variant_rows],
        "leaf_count": leaf_count,
        "leaf_bbox_list": [row["bbox"] if row else None for row in leaf_variant_rows],
        "bbox_proxy": bbox_proxy,
        "bbox_proxy_width": bbox_proxy["width"] if bbox_proxy else None,
        "bbox_proxy_height": bbox_proxy["height"] if bbox_proxy else None,
        "internal_ordering": spec["internal_ordering"],
        "internal_net_list": spec["internal_net_list"],
        "input_ports": spec["input_ports"],
        "output_ports": spec["output_ports"],
        "control_ports": spec["control_ports"],
        "input_pin_accessibility": input_access,
        "output_pin_accessibility": output_access,
        "control_pin_accessibility": control_access,
        "internal_net_accessibility": internal_access,
        "vdd_side_consistency": vdd_consistency,
        "gnd_side_consistency": gnd_consistency,
        "power_side_policy": power_policy,
        "precharge_exception_if_any": precharge_exception,
        "requires_spacing_rule": spacing["requires_spacing_rule"],
        "spacing_rule_available": spacing["spacing_rule_available"],
        "requires_keepout": spacing["requires_keepout"],
        "keepout_available": spacing["keepout_available"],
        "requires_row_alignment": spec["classification"] == "blocked_by_row_placement_requirement",
        "row_alignment_available": row_alignment_available,
        "requires_internal_routing": len(spec["internal_net_list"]) > 0 or leaf_count > 1,
        "internal_routing_proven": routing_proven,
        "requires_timing_proof": True if subblock_name != "PRECHARGE" else True,
        "timing_proof_available": timing_available,
        "requires_rail_continuity": True,
        "rail_continuity_proven": rail_continuity,
        "safe_for_composite_readonly_feasibility": safe_readonly_feasibility,
        "safe_for_legal_placement_readonly": safe_legal_readonly,
        "safe_for_physical_placement": False,
        "feasibility_classification": spec["classification"],
        "notes": _dedupe_list(notes),
        "blockers": _dedupe_list(blockers),
    }


def format_time_control_composite_feasibility_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OpenYield TIME Control Composite Feasibility Report",
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
            "## Subblock Composite Topology",
            "",
            md_table(
                ["subblock", "leaf sequence", "bbox proxy (w x h)", "classification", "legal-readonly", "physical"],
                [
                    [
                        row["subblock_name"],
                        " -> ".join(row["leaf_sequence"]),
                        _fmt_bbox_proxy(row["bbox_proxy"]),
                        row["feasibility_classification"],
                        row["safe_for_legal_placement_readonly"],
                        row["safe_for_physical_placement"],
                    ]
                    for row in report["subblock_composite_topology"]
                ],
            ),
            "",
            "## Leaf Sequence / BBox Proxy Table",
            "",
            md_table(
                ["subblock", "leaf count", "width", "height", "ordering", "internal nets"],
                [
                    [
                        row["subblock_name"],
                        row["leaf_count"],
                        row["bbox_proxy_width"],
                        row["bbox_proxy_height"],
                        row["internal_ordering"],
                        ", ".join(row["internal_net_list"]),
                    ]
                    for row in report["subblock_composite_topology"]
                ],
            ),
            "",
            "## Pin Accessibility Summary",
            "",
            md_table(
                ["subblock", "input", "output", "control", "internal nets"],
                [
                    [
                        row["subblock_name"],
                        row["input_pin_accessibility"]["status"],
                        row["output_pin_accessibility"]["status"],
                        row["control_pin_accessibility"]["status"],
                        row["internal_net_accessibility"]["status"],
                    ]
                    for row in report["subblock_composite_topology"]
                ],
            ),
            "",
            "## Power Side Compatibility Summary",
            "",
            md_table(
                ["subblock", "vdd consistency", "gnd consistency", "policy", "precharge exception"],
                [
                    [
                        row["subblock_name"],
                        row["vdd_side_consistency"],
                        row["gnd_side_consistency"],
                        row["power_side_policy"],
                        row["precharge_exception_if_any"] or "-",
                    ]
                    for row in report["subblock_composite_topology"]
                ],
            ),
            "",
            "## PRECHARGE Exception Section",
            "",
            "```json",
            json.dumps(report["precharge_exception_section"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## DFF Row Feasibility Section",
            "",
            "```json",
            json.dumps(report["dff_row_feasibility_section"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Feasibility Classification",
            "",
            md_table(
                ["subblock", "classification", "readonly feasibility", "legal-readonly", "physical"],
                [
                    [
                        row["subblock_name"],
                        row["classification"],
                        row["safe_for_composite_readonly_feasibility"],
                        row["safe_for_legal_placement_readonly"],
                        row["safe_for_physical_placement"],
                    ]
                    for row in report["feasibility_classification"]
                ],
            ),
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


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(out)


def list_block(items: list[str]) -> str:
    if not items:
        return "- none"
    return "\n".join(f"- {item}" for item in items)


def _resolve_leaf_sequence(mapping_row: dict[str, Any], contract_row: dict[str, Any] | None) -> list[str]:
    if contract_row and contract_row.get("candidate_sequence"):
        return list(contract_row["candidate_sequence"])
    return list(mapping_row.get("candidate_leaf_macros", []))


def _recommended_leaf_row(recommended_leafs: dict[tuple[str, str], dict[str, Any]], macro_name: str) -> dict[str, Any] | None:
    for (candidate_macro, _variant_name), row in recommended_leafs.items():
        if candidate_macro == macro_name:
            return row
    return None


def _bbox_proxy(leaf_variant_rows: list[dict[str, Any] | None]) -> dict[str, Any] | None:
    rows = [row for row in leaf_variant_rows if row and row.get("width") is not None and row.get("height") is not None]
    if not rows:
        return None
    width = sum(float(row["width"]) for row in rows)
    height = max(float(row["height"]) for row in rows)
    return {
        "x0": 0.0,
        "y0": 0.0,
        "x1": width,
        "y1": height,
        "width": width,
        "height": height,
        "origin_policy": "metadata_only_linear_pack_proxy",
        "notes": [
            "bbox proxy is conservative metadata only and is not legal placement proof.",
            "no abutment, routing, or DRC legality is implied by this proxy.",
        ],
    }


def _port_accessibility(leaf_variant_rows: list[dict[str, Any] | None], ports: list[str], role: str) -> dict[str, Any]:
    if not ports:
        return {"status": "not_applicable", "available_ports": [], "missing_ports": [], "side_hints": {}}
    side_hints: dict[str, list[str]] = {}
    missing = []
    for port in ports:
        matched = _collect_port_sides(leaf_variant_rows, port, role)
        if matched:
            side_hints[port] = matched
        else:
            missing.append(port)
    status = "complete" if not missing else ("partial" if side_hints else "missing")
    return {
        "status": status,
        "available_ports": sorted(side_hints.keys()),
        "missing_ports": missing,
        "side_hints": side_hints,
        "notes": "pin-side accessibility is metadata only and is not routing proof.",
    }


def _collect_port_sides(leaf_variant_rows: list[dict[str, Any] | None], port: str, role: str) -> list[str]:
    aliases = _port_aliases(port)
    matched = []
    for row in leaf_variant_rows:
        if row is None:
            continue
        side_maps = [row.get("pin_side_map", {}), row.get(f"{role}_pin_sides", {})]
        for side_map in side_maps:
            for alias in aliases:
                if alias in side_map and side_map[alias] not in matched:
                    matched.append(side_map[alias])
    return matched


def _internal_net_accessibility(internal_nets: list[str], leaf_variant_rows: list[dict[str, Any] | None]) -> dict[str, Any]:
    if not internal_nets:
        return {
            "status": "not_applicable",
            "internal_nets": [],
            "notes": "no internal composite handoff net is required.",
        }
    known = [row for row in leaf_variant_rows if row and row.get("pin_side_map")]
    status = "metadata_proxy_only" if known else "missing"
    return {
        "status": status,
        "internal_nets": internal_nets,
        "notes": "internal net accessibility is inferred from stage ordering and exposed leaf pin sides only; no internal routing is proven.",
    }


def _power_side_consistency(leaf_variant_rows: list[dict[str, Any] | None], subblock_name: str) -> tuple[bool, bool, str]:
    vdd_sides = {row["vdd_side"] for row in leaf_variant_rows if row and row.get("vdd_side") and row["vdd_side"] != "unknown"}
    gnd_sides = {row["gnd_side"] for row in leaf_variant_rows if row and row.get("gnd_side") and row["gnd_side"] != "unknown"}
    vdd_consistency = len(vdd_sides) <= 1 and bool(vdd_sides)
    if subblock_name == "PRECHARGE":
        gnd_consistency = False
        policy = "precharge_vdd_only_exception"
    else:
        gnd_consistency = len(gnd_sides) <= 1 and bool(gnd_sides)
        if vdd_consistency and gnd_consistency:
            policy = f"consistent_vdd_{next(iter(vdd_sides))}_gnd_{next(iter(gnd_sides))}"
        elif vdd_consistency:
            policy = f"partial_vdd_only_{next(iter(vdd_sides))}"
        else:
            policy = "mixed_or_unknown"
    return vdd_consistency, gnd_consistency, policy


def _spacing_and_keepout(
    payload_row: dict[str, Any] | None,
    region_adjacency: list[dict[str, Any]],
    interface_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    requires_spacing = True
    spacing_available = False
    keepout_available = False
    requires_keepout = True
    notes = []
    if payload_row:
        note_blob = " ".join(payload_row.get("notes", []))
        spacing_available = "required_channel_width=" in note_blob and "reserved_channel_width=" in note_blob
        keepout_available = "reserved_channel_width=" in note_blob
        notes.extend(payload_row.get("notes", []))
    if not spacing_available and region_adjacency:
        spacing_available = True
        keepout_available = True
        notes.append("region adjacency metadata provides conservative channel reservation only.")
    if interface_rows:
        keepout_available = True
    return {
        "requires_spacing_rule": requires_spacing,
        "spacing_rule_available": spacing_available,
        "requires_keepout": requires_keepout,
        "keepout_available": keepout_available,
        "notes": notes,
    }


def _collect_blockers(composite_rows: list[dict[str, Any]]) -> list[str]:
    items: list[str] = []
    for row in composite_rows:
        items.extend(f"{row['subblock_name']}: {blocker}" for blocker in row["blockers"])
    return _dedupe_list(items)


def _port_aliases(port: str) -> list[str]:
    aliases = {
        "A": ["A"],
        "B": ["B"],
        "C": ["C"],
        "Z": ["Z", "dout", "OUT"],
        "ZN": ["Z", "ZN", "OUTB"],
        "D": ["D", "DIN"],
        "Q": ["Q", "dout"],
        "CLK": ["CLK", "clk"],
        "ENB": ["ENB", "EN", "en_bar", "precharge_enb", "PRE"],
        "BL": ["BL", "bl"],
        "BR": ["BR", "br", "BLB"],
    }
    return aliases.get(port, [port])


def _extract_channel_metrics(notes: list[str]) -> dict[str, float | None]:
    metrics: dict[str, float | None] = {"required_channel_width": None, "reserved_channel_width": None, "budget_margin": None}
    for note in notes:
        for key in list(metrics):
            match = re.search(rf"{key}=([0-9.]+)", note)
            if match:
                metrics[key] = float(match.group(1))
    return metrics


def _fmt_bbox_proxy(bbox: dict[str, Any] | None) -> str:
    if not bbox:
        return "-"
    return f"{bbox['width']:.4g} x {bbox['height']:.4g}"


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
