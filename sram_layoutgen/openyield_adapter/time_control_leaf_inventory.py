"""Readonly TIME/control leaf geometry and pin-side inventory."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from .gds_pin_audit import BBox, GdsShape, GdsText, read_gds_labels_and_shapes


LEAF_VARIANTS = [
    ("gen_inv", "openram_replacements", "technology/freepdk45/gds_lib/openram_replacements/gen_inv.gds"),
    ("gen_nand2", "openram_replacements", "technology/freepdk45/gds_lib/openram_replacements/gen_nand2.gds"),
    ("gen_delay_inv", "openram_replacements", "technology/freepdk45/gds_lib/openram_replacements/gen_delay_inv.gds"),
    ("gen_precharge", "openram_replacements", "technology/freepdk45/gds_lib/openram_replacements/gen_precharge.gds"),
    ("dff", "default_gds_lib", "technology/freepdk45/gds_lib/dff.gds"),
    ("gen_inv", "default_gds_lib", "technology/freepdk45/gds_lib/gen_inv.gds"),
    ("gen_nand2", "default_gds_lib", "technology/freepdk45/gds_lib/gen_nand2.gds"),
    ("gen_delay_inv", "default_gds_lib", "technology/freepdk45/gds_lib/gen_delay_inv.gds"),
    ("gen_precharge", "default_gds_lib", "technology/freepdk45/gds_lib/gen_precharge.gds"),
    ("sense_amp", "default_gds_lib", "technology/freepdk45/gds_lib/sense_amp.gds"),
    ("write_driver", "default_gds_lib", "technology/freepdk45/gds_lib/write_driver.gds"),
    ("gen_wl_driver", "openram_replacements", "technology/freepdk45/gds_lib/openram_replacements/gen_wl_driver.gds"),
    ("gen_col_mux_vdd_labeled", "openyield_repaired", "technology/freepdk45/gds_lib/openyield_repaired/gen_col_mux_vdd_labeled.gds"),
    ("cell_1rw", "default_gds_lib", "technology/freepdk45/gds_lib/cell_1rw.gds"),
    ("dummy_cell_1rw", "default_gds_lib", "technology/freepdk45/gds_lib/dummy_cell_1rw.gds"),
    ("replica_cell_1rw", "default_gds_lib", "technology/freepdk45/gds_lib/replica_cell_1rw.gds"),
]

PIN_ROLE_MAP: dict[str, dict[str, list[str]]] = {
    "gen_inv": {"input": ["A"], "output": ["Z"], "control": []},
    "gen_nand2": {"input": ["A", "B"], "output": ["Z"], "control": []},
    "gen_delay_inv": {"input": ["A"], "output": ["Z"], "control": []},
    "gen_precharge": {"input": [], "output": ["BL", "BR"], "control": ["EN", "ENB", "en_bar", "precharge_enb", "PRE"]},
    "dff": {"input": ["D", "CLK"], "output": ["Q"], "control": ["CLK"]},
    "sense_amp": {"input": ["IN", "INB", "BL", "BR"], "output": ["Q", "QB", "dout"], "control": ["EN"]},
    "write_driver": {"input": ["DIN"], "output": ["BL", "BLB", "BR"], "control": ["EN"]},
    "gen_wl_driver": {"input": ["A"], "output": ["Z"], "control": ["B"]},
    "gen_col_mux_vdd_labeled": {"input": ["BL", "BR", "SEL"], "output": ["OUT", "OUTB"], "control": ["SEL"]},
    "cell_1rw": {"input": ["WL"], "output": ["BL", "BLB", "BR", "Q", "Q_bar"], "control": ["WL"]},
    "dummy_cell_1rw": {"input": ["WL"], "output": ["BL", "BLB", "BR"], "control": ["WL"]},
    "replica_cell_1rw": {"input": ["WL"], "output": ["RBL", "RBLB", "BL", "BR"], "control": ["WL"]},
}

SUBBLOCK_SPECS = [
    ("PINV", ["gen_inv"], ["openram_replacements"], False, False, False, True),
    ("AND2", ["gen_nand2", "gen_inv"], ["openram_replacements", "openram_replacements"], True, False, False, True),
    ("AND3_COMPOSITE", ["gen_nand2", "gen_inv"], ["openram_replacements", "openram_replacements"], True, False, False, True),
    ("PNAND3_COMPOSITE", ["gen_nand2", "gen_inv"], ["openram_replacements", "openram_replacements"], True, False, False, True),
    ("PDRIVE", ["gen_inv"], ["openram_replacements"], True, True, False, True),
    ("PDRIVE2_FOR_PRE", ["gen_inv", "gen_precharge"], ["openram_replacements", "openram_replacements"], True, True, False, True),
    ("WL_PDRIVE", ["gen_inv"], ["openram_replacements"], True, True, False, True),
    ("DELAY_CHAIN", ["gen_delay_inv", "gen_inv"], ["openram_replacements", "openram_replacements"], True, True, False, True),
    ("WEN_DELAY_CHAIN", ["gen_delay_inv", "gen_inv"], ["openram_replacements", "openram_replacements"], True, True, False, True),
    ("PRECHARGE", ["gen_precharge"], ["openram_replacements"], False, False, False, True),
    ("DFF_ROW", ["dff"], ["default_gds_lib"], False, False, True, True),
]


def build_time_control_leaf_inventory_report(
    repo_root: str | Path,
    tech_dir: str | Path,
    asset_inventory_path: str | Path,
    power_rail_audit_path: str | Path,
    generated_logic_report_path: str | Path | None = None,
    abstract_payload_report_path: str | Path | None = None,
    region_refinement_report_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    tech = Path(tech_dir)
    if not tech.is_absolute():
        tech = (root / tech).resolve()
    asset_inventory = _load_json(asset_inventory_path)
    power_audit = _load_json(power_rail_audit_path)
    generated_logic = _load_json(generated_logic_report_path or root / "docs" / "openyield_time_control_generated_logic_contract_report.json")
    abstract_payload = _load_json(abstract_payload_report_path or root / "docs" / "openyield_time_control_abstract_floorplan_payload_report.json")
    region_refinement = _load_json(region_refinement_report_path or root / "docs" / "openyield_time_control_region_refinement_report.json")

    leaf_rows = []
    nodes = [{"id": "leaf_inventory", "label": "time_control_leaf_bbox_pin_side_inventory", "kind": "root"}]
    edges = []
    for macro_name, variant_name, rel_path in LEAF_VARIANTS:
        path = (root / rel_path).resolve()
        row = _audit_leaf_variant(path, macro_name, variant_name, power_audit)
        leaf_rows.append(row)
        node_id = f"leaf:{macro_name}:{variant_name}"
        nodes.append({"id": node_id, "label": f"{macro_name}:{variant_name}", "kind": "leaf_variant", "path": str(path)})
        edges.append({"from": "leaf_inventory", "to": node_id, "relation": "audited"})

    subblock_map = _subblock_to_leaf_inventory(leaf_rows, generated_logic, abstract_payload, region_refinement)
    composite_readiness = _composite_readiness(subblock_map)
    blockers = _collect_blockers(leaf_rows, subblock_map, composite_readiness)
    precharge_special = _precharge_special(leaf_rows)

    decision = {
        "time_control_leaf_bbox_pin_side_inventory_available": True,
        "all_required_leaf_gds_found": all(row["gds_exists"] for row in leaf_rows),
        "all_recommended_leaf_variants_selected": _all_recommended_selected(leaf_rows),
        "all_required_leaf_bbox_known": all(row["bbox"] is not None for row in leaf_rows),
        "all_required_leaf_pin_sides_known": all(row["pin_side_map"] for row in leaf_rows),
        "all_required_leaf_power_sides_known_or_exception_recorded": _all_power_sides_known_or_exception(leaf_rows),
        "precharge_exception_retained": True,
        "all_subblocks_have_leaf_inventory": all(item["candidate_leaf_macros"] for item in subblock_map),
        "composite_readiness_classified": len(composite_readiness) >= 8,
        "can_enter_composite_internal_placement_feasibility_audit": True,
        "can_enter_legal_placement_readonly_audit": True,
        "can_enter_physical_placement_now": False,
        "can_generate_time_control_gds_now": False,
        "can_modify_standalone_now": False,
    }

    report = {
        "scope": "time_control_leaf_bbox_pin_side_inventory",
        "repo_root": str(root),
        "tech_dir": str(tech),
        "input_reports_and_assets": {
            "asset_inventory": str(Path(asset_inventory_path).resolve()),
            "power_rail_audit": str(Path(power_rail_audit_path).resolve()),
            "generated_logic_report": str((root / "docs" / "openyield_time_control_generated_logic_contract_report.json").resolve()),
            "abstract_payload_report": str((root / "docs" / "openyield_time_control_abstract_floorplan_payload_report.json").resolve()),
            "region_refinement_report": str((root / "docs" / "openyield_time_control_region_refinement_report.json").resolve()),
        },
        "gds_geometry_parse_available": True,
        "leaf_gds_bbox_pin_side_inventory": leaf_rows,
        "power_side_summary": _power_side_summary(leaf_rows),
        "subblock_to_leaf_mapping": subblock_map,
        "composite_readiness_classification": composite_readiness,
        "precharge_special_section": precharge_special,
        "blockers": blockers,
        "next_recommended_proof_task": "time_control_composite_internal_placement_feasibility_audit",
        "boundary_assertions": {
            "can_enter_physical_placement_now": False,
            "can_generate_time_control_gds_now": False,
            "can_modify_standalone_now": False,
            "standalone_modified": False,
            "routing_modified": False,
            "gds_writer_modified": False,
        },
        "audit_summary": decision,
    }
    graph = {"nodes": nodes, "edges": edges}
    return {"report": report, "graph": graph}


def _audit_leaf_variant(path: Path, macro_name: str, variant_name: str, power_audit: dict[str, Any]) -> dict[str, Any]:
    row = {
        "macro_name": macro_name,
        "variant_name": variant_name,
        "gds_path": str(path),
        "gds_exists": path.exists(),
        "recommended_for_future_planning": _is_recommended_variant(macro_name, variant_name),
        "top_cell": path.stem,
        "bbox": None,
        "width": None,
        "height": None,
        "origin_policy": "real_gds_bbox",
        "pin_labels": [],
        "input_pins": [],
        "output_pins": [],
        "bidirectional_pins": [],
        "control_pins": [],
        "vdd_pins": [],
        "gnd_pins": [],
        "pin_side_map": {},
        "input_pin_sides": {},
        "output_pin_sides": {},
        "control_pin_sides": {},
        "vdd_side": "unknown",
        "gnd_side": "unknown",
        "vdd_gnd_policy": "unknown",
        "power_metadata_quality": "unknown",
        "rail_evidence_status": "unavailable",
        "within_macro_rail_evidence": False,
        "across_abutment_rail_evidence": False,
        "safe_for_metadata_planning": False,
        "safe_for_legal_placement_readonly": False,
        "safe_for_physical_placement": False,
        "notes": [],
    }
    if not path.exists():
        row["notes"].append("GDS file missing.")
        return row
    labels, shapes, bbox = read_gds_labels_and_shapes(path)
    role_spec = PIN_ROLE_MAP.get(macro_name, {"input": [], "output": [], "control": []})
    row["bbox"] = bbox.to_dict() if bbox else None
    row["width"] = bbox.width if bbox else None
    row["height"] = bbox.height if bbox else None
    row["pin_labels"] = sorted({label.text for label in labels})
    row["input_pins"] = role_spec["input"]
    row["output_pins"] = role_spec["output"]
    row["control_pins"] = role_spec["control"]
    row["vdd_pins"] = [label.text for label in labels if label.text.lower() == "vdd"]
    row["gnd_pins"] = [label.text for label in labels if label.text.lower() in {"gnd", "vss"}]
    row["pin_side_map"] = _pin_side_map(labels, shapes, bbox)
    row["input_pin_sides"] = {pin: row["pin_side_map"].get(pin) for pin in row["input_pins"] if pin in row["pin_side_map"]}
    row["output_pin_sides"] = {pin: row["pin_side_map"].get(pin) for pin in row["output_pins"] if pin in row["pin_side_map"]}
    row["control_pin_sides"] = {pin: row["pin_side_map"].get(pin) for pin in row["control_pins"] if pin in row["pin_side_map"]}
    power_info = _power_from_audit(power_audit, macro_name, variant_name)
    row["vdd_side"] = power_info.get("vdd_side", "unknown")
    row["gnd_side"] = power_info.get("gnd_side", "unknown")
    row["vdd_gnd_policy"] = power_info.get("top_bottom_rail_policy", "unknown")
    row["power_metadata_quality"] = _power_metadata_quality(row, macro_name)
    row["rail_evidence_status"] = _rail_evidence_status(power_info)
    row["within_macro_rail_evidence"] = bool(power_info.get("rail_continuity_within_macro_proven"))
    row["across_abutment_rail_evidence"] = bool(power_info.get("rail_continuity_across_abutment_proven"))
    row["safe_for_metadata_planning"] = _safe_for_metadata_planning(row, macro_name)
    row["safe_for_legal_placement_readonly"] = _safe_for_legal_readonly(row, macro_name)
    row["safe_for_physical_placement"] = _safe_for_physical(row, macro_name)
    row["notes"] = _leaf_notes(row, macro_name)
    return row


def _subblock_to_leaf_inventory(
    leaf_rows: list[dict[str, Any]],
    generated_logic: dict[str, Any],
    abstract_payload: dict[str, Any],
    region_refinement: dict[str, Any],
) -> list[dict[str, Any]]:
    by_key = {(row["macro_name"], row["variant_name"]): row for row in leaf_rows}
    generated_contracts = generated_logic.get("generated_logic_contract_list", [])
    generated_by_name = {entry["contract_name"]: entry for entry in generated_contracts}
    payload_subblocks = {entry["subblock_name"]: entry for entry in abstract_payload.get("payload", {}).get("subblocks", [])}
    grouped_interfaces = {entry["interface_name"]: entry for entry in region_refinement.get("grouped_planning_interface_refinement", [])}
    rows = []
    for subblock_name, macros, variants, req_comp, req_chain, req_row, req_timing in SUBBLOCK_SPECS:
        candidates = [by_key.get((macro, variant)) for macro, variant in zip(macros, variants)]
        candidates = [item for item in candidates if item]
        payload_hint = next((payload_subblocks[key] for key in payload_subblocks if subblock_name in key or key.startswith(subblock_name)), None)
        contract_hint = _contract_hint(subblock_name, generated_by_name)
        consumer_hint = _consumer_hint(subblock_name, grouped_interfaces)
        rows.append(
            {
                "subblock_name": subblock_name,
                "source_contract": contract_hint,
                "candidate_leaf_macros": macros,
                "recommended_leaf_variants": variants,
                "leaf_count_if_known": len(candidates),
                "bbox_inputs_available": all(item["bbox"] is not None for item in candidates) if candidates else False,
                "pin_side_inputs_available": all(item["pin_side_map"] for item in candidates) if candidates else False,
                "power_side_inputs_available": all(item["vdd_side"] != "unknown" for item in candidates) if candidates else False,
                "requires_composite_internal_placement": req_comp,
                "requires_chain_stage_ordering": req_chain,
                "requires_row_placement": req_row,
                "requires_timing_proof": req_timing,
                "requires_routing_proof": True,
                "safe_for_legal_placement_readonly": bool(candidates) and all(item["safe_for_legal_placement_readonly"] for item in candidates),
                "safe_for_physical_placement": False,
                "blockers": _subblock_blockers(subblock_name, candidates, payload_hint, consumer_hint),
            }
        )
    return rows


def _composite_readiness(subblock_map: list[dict[str, Any]]) -> list[dict[str, Any]]:
    targets = {"AND2", "AND3_COMPOSITE", "PNAND3_COMPOSITE", "PDRIVE", "PDRIVE2_FOR_PRE", "WL_PDRIVE", "DELAY_CHAIN", "WEN_DELAY_CHAIN"}
    rows = []
    for item in subblock_map:
        if item["subblock_name"] not in targets:
            continue
        cls = "ready_for_readonly_placement_feasibility"
        if "precharge" in item["subblock_name"].lower() and any("PRECHARGE" in blocker or "precharge" in blocker.lower() for blocker in item["blockers"]):
            cls = "blocked_by_precharge_power_exception"
        elif item["requires_timing_proof"]:
            cls = "blocked_by_timing_requirement"
        elif not item["bbox_inputs_available"] or not item["pin_side_inputs_available"]:
            cls = "blocked_by_missing_leaf_geometry"
        elif not item["power_side_inputs_available"]:
            cls = "metadata_ready_but_missing_pin_or_power_side"
        rows.append(
            {
                "subblock_name": item["subblock_name"],
                "classification": cls,
                "safe_for_legal_placement_readonly": item["safe_for_legal_placement_readonly"],
                "safe_for_physical_placement": False,
                "blockers": item["blockers"],
            }
        )
    return rows


def _precharge_special(leaf_rows: list[dict[str, Any]]) -> dict[str, Any]:
    pre = next((row for row in leaf_rows if row["macro_name"] == "gen_precharge" and row["variant_name"] == "openram_replacements"), None)
    if not pre:
        return {}
    return {
        "precharge_leaf_bbox_known": pre["bbox"] is not None,
        "precharge_en_pin_side_known": any(pin in pre["control_pin_sides"] for pin in ("EN", "ENB", "en_bar", "PRE")),
        "precharge_vdd_side_known": pre["vdd_side"] != "unknown",
        "precharge_gnd_side_known": pre["gnd_side"] != "unknown",
        "precharge_no_local_gnd_exception": pre["gnd_side"] == "missing" or pre["power_metadata_quality"] == "vdd_only_exception",
        "precharge_safe_for_legal_placement_readonly": pre["safe_for_legal_placement_readonly"],
        "precharge_safe_for_physical_placement": False,
        "precharge_blocker_for_physical_gate": "no local GND proof and no across-abutment rail continuity proof",
    }


def _power_side_summary(leaf_rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "storage_reference_cells": [
            {"macro_name": row["macro_name"], "vdd_side": row["vdd_side"], "gnd_side": row["gnd_side"], "policy": row["vdd_gnd_policy"]}
            for row in leaf_rows
            if row["macro_name"] in {"cell_1rw", "dummy_cell_1rw", "replica_cell_1rw"}
        ],
        "generated_logic_leaves": [
            {"macro_name": row["macro_name"], "variant_name": row["variant_name"], "vdd_side": row["vdd_side"], "gnd_side": row["gnd_side"], "quality": row["power_metadata_quality"]}
            for row in leaf_rows
            if row["macro_name"] in {"gen_inv", "gen_nand2", "gen_delay_inv", "gen_precharge", "dff"}
        ],
        "consumer_hard_macros": [
            {"macro_name": row["macro_name"], "variant_name": row["variant_name"], "vdd_side": row["vdd_side"], "gnd_side": row["gnd_side"], "quality": row["power_metadata_quality"]}
            for row in leaf_rows
            if row["macro_name"] in {"sense_amp", "write_driver", "gen_wl_driver", "gen_col_mux_vdd_labeled"}
        ],
    }


def format_time_control_leaf_inventory_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OpenYield TIME Control Leaf Inventory",
            "",
            "This report inventories leaf macro geometry, pin-side metadata, and power-side evidence for later readonly feasibility work. It is not placement proof, routing proof, or physical-ready signoff.",
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
            "## Leaf GDS BBox / Pin Side Inventory",
            "",
            md_table(
                ["macro", "variant", "bbox", "input sides", "output sides", "control sides", "vdd", "gnd", "legal-readonly", "physical"],
                [
                    [
                        row["macro_name"],
                        row["variant_name"],
                        _fmt_bbox(row["bbox"]),
                        json.dumps(row["input_pin_sides"], ensure_ascii=False),
                        json.dumps(row["output_pin_sides"], ensure_ascii=False),
                        json.dumps(row["control_pin_sides"], ensure_ascii=False),
                        row["vdd_side"],
                        row["gnd_side"],
                        row["safe_for_legal_placement_readonly"],
                        row["safe_for_physical_placement"],
                    ]
                    for row in report["leaf_gds_bbox_pin_side_inventory"]
                ],
            ),
            "",
            "## Power Side Summary",
            "",
            "```json",
            json.dumps(report["power_side_summary"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Subblock To Leaf Mapping",
            "",
            md_table(
                ["subblock", "leafs", "bbox inputs", "pin sides", "power sides", "legal-readonly", "blockers"],
                [
                    [
                        row["subblock_name"],
                        ", ".join(row["candidate_leaf_macros"]),
                        row["bbox_inputs_available"],
                        row["pin_side_inputs_available"],
                        row["power_side_inputs_available"],
                        row["safe_for_legal_placement_readonly"],
                        "; ".join(row["blockers"]),
                    ]
                    for row in report["subblock_to_leaf_mapping"]
                ],
            ),
            "",
            "## Composite Readiness Classification",
            "",
            md_table(
                ["subblock", "classification", "legal-readonly", "physical", "blockers"],
                [
                    [row["subblock_name"], row["classification"], row["safe_for_legal_placement_readonly"], row["safe_for_physical_placement"], "; ".join(row["blockers"])]
                    for row in report["composite_readiness_classification"]
                ],
            ),
            "",
            "## PRECHARGE Special Section",
            "",
            "```json",
            json.dumps(report["precharge_special_section"], ensure_ascii=False, indent=2),
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


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(out)


def list_block(items: list[str]) -> str:
    if not items:
        return "- none"
    return "\n".join(f"- {item}" for item in items)


def _is_recommended_variant(macro_name: str, variant_name: str) -> bool:
    mapping = {
        ("gen_inv", "openram_replacements"),
        ("gen_nand2", "openram_replacements"),
        ("gen_delay_inv", "openram_replacements"),
        ("gen_precharge", "openram_replacements"),
        ("dff", "default_gds_lib"),
        ("sense_amp", "default_gds_lib"),
        ("write_driver", "default_gds_lib"),
        ("gen_wl_driver", "openram_replacements"),
        ("gen_col_mux_vdd_labeled", "openyield_repaired"),
        ("cell_1rw", "default_gds_lib"),
        ("dummy_cell_1rw", "default_gds_lib"),
        ("replica_cell_1rw", "default_gds_lib"),
    }
    return (macro_name, variant_name) in mapping


def _pin_side_map(labels: tuple[GdsText, ...], shapes: tuple[GdsShape, ...], bbox: BBox | None) -> dict[str, str]:
    result: dict[str, str] = {}
    for label in labels:
        if bbox is None:
            result[label.text] = "unknown"
            continue
        same_layer = [shape for shape in shapes if shape.layer == label.layer and _contains(shape.bbox, label.x, label.y, 0.02)]
        if same_layer:
            cx = (same_layer[0].bbox.x0 + same_layer[0].bbox.x1) / 2.0
            cy = (same_layer[0].bbox.y0 + same_layer[0].bbox.y1) / 2.0
            side, _ = bbox.side_for_point(cx, cy)
        else:
            side, _ = bbox.side_for_point(label.x, label.y)
        result[label.text] = side
    return result


def _power_from_audit(power_audit: dict[str, Any], macro_name: str, variant_name: str) -> dict[str, Any]:
    for row in power_audit.get("gds_power_rail_label_audit", []):
        if row.get("macro_name") == macro_name and row.get("variant_name") == variant_name:
            return row
    return {}


def _power_metadata_quality(row: dict[str, Any], macro_name: str) -> str:
    if macro_name == "gen_precharge":
        if row["vdd_side"] != "unknown" and row["gnd_side"] == "unknown":
            return "vdd_only_exception"
    if row["vdd_side"] != "unknown" and row["gnd_side"] != "unknown":
        return "explicit_vdd_gnd"
    if row["vdd_side"] != "unknown":
        return "partial_vdd_only"
    return "incomplete"


def _rail_evidence_status(power_info: dict[str, Any]) -> str:
    if not power_info:
        return "unavailable"
    if power_info.get("rail_continuity_across_abutment_proven"):
        return "across_abutment_proven"
    if power_info.get("rail_continuity_within_macro_proven"):
        return "within_macro_only"
    return "geometry_unproven"


def _safe_for_metadata_planning(row: dict[str, Any], macro_name: str) -> bool:
    if row["bbox"] is None:
        return False
    if macro_name == "gen_precharge":
        return row["vdd_side"] != "unknown" and any(pin in row["control_pin_sides"] for pin in ("EN", "ENB", "en_bar", "PRE"))
    return bool(row["pin_side_map"])


def _safe_for_legal_readonly(row: dict[str, Any], macro_name: str) -> bool:
    if not _safe_for_metadata_planning(row, macro_name):
        return False
    if macro_name == "gen_precharge":
        return True
    return row["vdd_side"] != "unknown" and row["within_macro_rail_evidence"]


def _safe_for_physical(row: dict[str, Any], macro_name: str) -> bool:
    if macro_name == "gen_precharge":
        return False
    return row["across_abutment_rail_evidence"] and macro_name in {"cell_1rw", "dummy_cell_1rw", "replica_cell_1rw"}


def _leaf_notes(row: dict[str, Any], macro_name: str) -> list[str]:
    notes = []
    if row["bbox"] is not None:
        notes.append("bbox inventory is geometry evidence only, not placement proof.")
    if row["pin_side_map"]:
        notes.append("pin side inventory is access-side evidence only, not routing proof.")
    if row["within_macro_rail_evidence"] and not row["across_abutment_rail_evidence"]:
        notes.append("within-macro rail evidence does not prove abutment continuity.")
    if row["recommended_for_future_planning"] and not row["safe_for_physical_placement"]:
        notes.append("recommended future planning variant is not automatically physical-ready.")
    if macro_name == "gen_precharge":
        notes.append("PRECHARGE retains the no-local-GND metadata exception and stays non-physical-ready.")
    return notes


def _contract_hint(subblock_name: str, generated_by_name: dict[str, Any]) -> str:
    mapping = {
        "PINV": "PINV_GENERATED_LOGIC_CONTRACT",
        "AND2": "AND2_GENERATED_LOGIC_CONTRACT",
        "AND3_COMPOSITE": "AND3_COMPOSITE_GENERATED_LOGIC_CONTRACT",
        "PNAND3_COMPOSITE": "PNAND3_COMPOSITE_GENERATED_LOGIC_CONTRACT",
        "PDRIVE": "PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT",
        "PDRIVE2_FOR_PRE": "PDRIVE2_FOR_PRE_CHAIN_GENERATED_LOGIC_CONTRACT",
        "WL_PDRIVE": "WL_PDRIVE_CHAIN_GENERATED_LOGIC_CONTRACT",
        "DELAY_CHAIN": "DELAY_CHAIN_GENERATED_LOGIC_CONTRACT",
        "WEN_DELAY_CHAIN": "WEN_DELAY_CHAIN_CONDITIONAL_GENERATED_LOGIC_CONTRACT",
    }
    name = mapping.get(subblock_name)
    if name and name in generated_by_name:
        return name
    return "metadata_source_not_found"


def _consumer_hint(subblock_name: str, grouped_interfaces: dict[str, Any]) -> dict[str, Any] | None:
    if subblock_name == "PRECHARGE":
        return grouped_interfaces.get("TIME_CONTROL_TO_PRECHARGE_INTERFACE")
    return None


def _subblock_blockers(subblock_name: str, candidates: list[dict[str, Any]], payload_hint: dict[str, Any] | None, consumer_hint: dict[str, Any] | None) -> list[str]:
    blockers = []
    if not candidates:
        blockers.append("missing leaf geometry")
    if candidates and not all(item["pin_side_map"] for item in candidates):
        blockers.append("missing pin side metadata")
    if candidates and not all(item["vdd_side"] != "unknown" for item in candidates):
        blockers.append("missing power side metadata")
    if subblock_name in {"AND2", "AND3_COMPOSITE", "PNAND3_COMPOSITE", "PDRIVE", "PDRIVE2_FOR_PRE", "WL_PDRIVE", "DELAY_CHAIN", "WEN_DELAY_CHAIN"}:
        blockers.append("timing proof required")
        blockers.append("routing proof required")
    if subblock_name == "PRECHARGE":
        blockers.append("blocked by precharge power exception")
    if subblock_name == "DFF_ROW":
        blockers.append("row placement proof required")
    if payload_hint:
        blockers.extend(payload_hint.get("blocked_by", []))
    if consumer_hint:
        blockers.extend(consumer_hint.get("blocked_by", []))
    seen = set()
    ordered = []
    for item in blockers:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _collect_blockers(leaf_rows: list[dict[str, Any]], subblock_map: list[dict[str, Any]], composite_readiness: list[dict[str, Any]]) -> list[str]:
    blockers = []
    for row in leaf_rows:
        if not row["safe_for_legal_placement_readonly"]:
            blockers.append(f"{row['macro_name']}:{row['variant_name']} is not ready for legal-placement readonly planning.")
    for row in subblock_map:
        blockers.extend(f"{row['subblock_name']}: {item}" for item in row["blockers"])
    seen = set()
    ordered = []
    for item in blockers:
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def _all_recommended_selected(leaf_rows: list[dict[str, Any]]) -> bool:
    recommended = [row for row in leaf_rows if row["recommended_for_future_planning"]]
    return bool(recommended) and all(row["gds_exists"] for row in recommended)


def _all_power_sides_known_or_exception(leaf_rows: list[dict[str, Any]]) -> bool:
    for row in leaf_rows:
        if row["macro_name"] == "gen_precharge":
            continue
        if row["vdd_side"] == "unknown":
            return False
    return True


def _contains(bbox: BBox, x: float, y: float, tol: float = 0.0) -> bool:
    return bbox.x0 - tol <= x <= bbox.x1 + tol and bbox.y0 - tol <= y <= bbox.y1 + tol


def _fmt_bbox(bbox: dict[str, Any] | None) -> str:
    if not bbox:
        return "-"
    return f"({bbox['x0']:.4g},{bbox['y0']:.4g})-({bbox['x1']:.4g},{bbox['y1']:.4g})"


def _load_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.is_absolute():
        p = p.resolve()
    return json.loads(p.read_text(encoding="utf-8"))
