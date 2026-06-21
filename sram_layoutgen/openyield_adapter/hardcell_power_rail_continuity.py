"""Readonly hardcell power-rail continuity audit helpers."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .gds_pin_audit import BBox, GdsShape, GdsText, read_gds_labels_and_shapes


REQUIRED_GDS_VARIANTS = [
    ("cell_1rw", "default_gds_lib", "technology/freepdk45/gds_lib/cell_1rw.gds"),
    ("dummy_cell_1rw", "default_gds_lib", "technology/freepdk45/gds_lib/dummy_cell_1rw.gds"),
    ("replica_cell_1rw", "default_gds_lib", "technology/freepdk45/gds_lib/replica_cell_1rw.gds"),
    ("sense_amp", "default_gds_lib", "technology/freepdk45/gds_lib/sense_amp.gds"),
    ("write_driver", "default_gds_lib", "technology/freepdk45/gds_lib/write_driver.gds"),
    ("gen_wl_driver", "default_gds_lib", "technology/freepdk45/gds_lib/gen_wl_driver.gds"),
    ("gen_wl_driver", "openram_replacements", "technology/freepdk45/gds_lib/openram_replacements/gen_wl_driver.gds"),
    ("gen_col_mux", "default_gds_lib", "technology/freepdk45/gds_lib/gen_col_mux.gds"),
    ("gen_col_mux", "openram_replacements", "technology/freepdk45/gds_lib/openram_replacements/gen_col_mux.gds"),
    ("gen_col_mux_vdd_labeled", "openyield_repaired", "technology/freepdk45/gds_lib/openyield_repaired/gen_col_mux_vdd_labeled.gds"),
    ("gen_inv", "default_gds_lib", "technology/freepdk45/gds_lib/gen_inv.gds"),
    ("gen_inv", "openram_replacements", "technology/freepdk45/gds_lib/openram_replacements/gen_inv.gds"),
    ("gen_nand2", "default_gds_lib", "technology/freepdk45/gds_lib/gen_nand2.gds"),
    ("gen_nand2", "openram_replacements", "technology/freepdk45/gds_lib/openram_replacements/gen_nand2.gds"),
    ("gen_delay_inv", "default_gds_lib", "technology/freepdk45/gds_lib/gen_delay_inv.gds"),
    ("gen_delay_inv", "openram_replacements", "technology/freepdk45/gds_lib/openram_replacements/gen_delay_inv.gds"),
    ("gen_precharge", "default_gds_lib", "technology/freepdk45/gds_lib/gen_precharge.gds"),
    ("gen_precharge", "openram_replacements", "technology/freepdk45/gds_lib/openram_replacements/gen_precharge.gds"),
    ("dff", "default_gds_lib", "technology/freepdk45/gds_lib/dff.gds"),
]

SPICE_EXPECTED = [
    "cell_1rw",
    "dummy_cell_1rw",
    "replica_cell_1rw",
    "sense_amp",
    "write_driver",
    "dff",
    "gen_inv",
    "gen_nand2",
    "gen_delay_inv",
    "gen_precharge",
    "gen_wl_driver",
    "gen_col_mux",
    "gen_col_mux_vdd_labeled",
]


@dataclass(frozen=True)
class RailEvidence:
    label_names: tuple[str, ...]
    label_count: int
    label_layer: int | None
    side: str
    layer: int | None
    shape_bboxes: tuple[dict[str, float], ...]
    shape_count: int
    rail_span: dict[str, float] | None
    touches_left_edge: bool
    touches_right_edge: bool
    touches_bottom_edge: bool
    touches_top_edge: bool
    orientation: str
    within_macro_continuity_proven: bool


def build_hardcell_power_rail_continuity_report(
    repo_root: str | Path,
    tech_dir: str | Path,
    inventory_path: str | Path,
    gds_pin_audit_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    tech = Path(tech_dir)
    if not tech.is_absolute():
        tech = (root / tech).resolve()
    inventory = json.loads(Path(inventory_path).read_text(encoding="utf-8"))
    gds_pin_audit = _load_optional_json(gds_pin_audit_path or root / "docs" / "openyield_gds_pin_audit_report.json")
    aliases = _load_json(tech / "openyield_macro_aliases.json").get("aliases", [])
    replacements = _load_json(tech / "replacement_macros.json").get("macros", [])
    alias_by_macro = defaultdict(list)
    for item in aliases:
        alias_by_macro[str(item.get("macro_name") or "")].append(item)
    replacement_by_name = {str(item.get("name") or ""): item for item in replacements if item.get("name")}

    variant_rows = []
    graph_nodes = []
    graph_edges = []
    required_found = True
    for macro_name, variant_name, rel_path in REQUIRED_GDS_VARIANTS:
        path = (root / rel_path).resolve()
        row = _audit_gds_variant(path, macro_name, variant_name, alias_by_macro.get(macro_name, []), replacement_by_name.get(macro_name), gds_pin_audit)
        variant_rows.append(row)
        graph_nodes.append({"id": f"gds:{macro_name}:{variant_name}", "label": f"{macro_name}:{variant_name}", "kind": "gds_variant", "path": str(path)})
        graph_edges.append({"from": "audit_root", "to": f"gds:{macro_name}:{variant_name}", "relation": "audited"})
        required_found = required_found and row["gds_exists"]

    spice_rows = [_audit_spice_macro(tech, macro_name, alias_by_macro.get(macro_name, [])) for macro_name in SPICE_EXPECTED]
    variant_comparison = _variant_comparison(variant_rows, spice_rows)
    precharge_decisions = _precharge_decisions([row for row in variant_rows if row["macro_name"] == "gen_precharge"], spice_rows)

    unresolved_blockers = _collect_blockers(variant_rows, spice_rows, precharge_decisions)
    all_power_metadata = all(
        row["vdd_label_count"] > 0 or row["variant_name"] == "default_gds_lib"
        for row in variant_rows
        if row["macro_name"] != "gen_precharge"
    )
    all_spice_checked = len(spice_rows) == len(SPICE_EXPECTED)
    within_macro_available = any(row["rail_continuity_within_macro_proven"] for row in variant_rows)
    abutment_candidates = [row for row in variant_rows if row["gds_exists"]]
    abutment_proven = bool(abutment_candidates) and all(row["rail_continuity_across_abutment_proven"] for row in abutment_candidates)
    shared_rail_candidates = [row for row in variant_rows if row["safe_for_shared_rail"]]
    shared_rail_safe = bool(shared_rail_candidates) and abutment_proven and len(shared_rail_candidates) == len(abutment_candidates)

    decision = {
        "hardcell_power_rail_continuity_readonly_audit_available": True,
        "all_required_macro_gds_found": required_found,
        "all_required_macro_power_metadata_available": all_power_metadata,
        "all_required_macro_spice_checked_or_missing_recorded": all_spice_checked,
        "precharge_power_exception_recorded": True,
        "within_macro_rail_evidence_available": within_macro_available,
        "abutment_rail_continuity_proven": abutment_proven,
        "shared_rail_safe": shared_rail_safe and abutment_proven,
        "can_enter_legal_placement_readonly_audit": True,
        "can_enter_physical_placement_now": False,
        "can_generate_time_control_gds_now": False,
        "can_modify_standalone_now": False,
    }

    next_goal = "time_control_leaf_bbox_pin_side_inventory"
    if decision["all_required_macro_gds_found"] and decision["within_macro_rail_evidence_available"]:
        next_goal = "time_control_leaf_bbox_pin_side_inventory"

    report = {
        "scope": "hardcell_power_rail_continuity_readonly_audit",
        "repo_root": str(root),
        "tech_dir": str(tech),
        "inventory_path": str(Path(inventory_path).resolve()),
        "gds_pin_audit_path": str((root / "docs" / "openyield_gds_pin_audit_report.json").resolve()),
        "input_assets": {
            "inventory_report": inventory.get("hardcell_power_rail_continuity_readonly_audit_inputs", {}),
            "gds_variant_count": len(variant_rows),
            "spice_macro_count": len(spice_rows),
        },
        "gds_geometry_parse_available": True,
        "gds_power_rail_label_audit": variant_rows,
        "spice_cross_check": spice_rows,
        "precharge_special_decision": precharge_decisions,
        "macro_variant_comparison": variant_comparison,
        "rail_continuity_decision": decision,
        "unresolved_blockers": unresolved_blockers,
        "next_recommended_proof_task": next_goal,
        "boundary_assertions": {
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
            "standalone_modified": False,
            "routing_modified": False,
            "gds_writer_modified": False,
        },
        "audit_summary": _audit_summary(variant_rows, spice_rows, precharge_decisions, decision),
    }
    graph = {
        "nodes": [{"id": "audit_root", "label": "hardcell_power_rail_continuity_readonly_audit", "kind": "root"}, *graph_nodes],
        "edges": graph_edges,
    }
    return {"report": report, "graph": graph}


def _audit_gds_variant(
    path: Path,
    macro_name: str,
    variant_name: str,
    aliases: list[dict[str, Any]],
    replacement: dict[str, Any] | None,
    gds_pin_audit: dict[str, Any],
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "macro_name": macro_name,
        "variant_name": variant_name,
        "gds_path": str(path),
        "gds_exists": path.exists(),
        "top_cell": path.stem,
        "bbox": None,
        "labels": [],
        "vdd_labels": [],
        "gnd_labels": [],
        "vdd_label_count": 0,
        "gnd_label_count": 0,
        "vdd_side": "unknown",
        "gnd_side": "unknown",
        "vdd_layer": None,
        "gnd_layer": None,
        "vdd_bbox_if_known": None,
        "gnd_bbox_if_known": None,
        "power_rail_shapes_found": False,
        "vdd_rail_shape_count": 0,
        "gnd_rail_shape_count": 0,
        "vdd_rail_span": None,
        "gnd_rail_span": None,
        "vdd_rail_touches_left_edge": False,
        "vdd_rail_touches_right_edge": False,
        "gnd_rail_touches_left_edge": False,
        "gnd_rail_touches_right_edge": False,
        "top_bottom_rail_policy": "unknown",
        "left_right_abutment_possible": False,
        "rail_continuity_within_macro_proven": False,
        "rail_continuity_across_abutment_proven": False,
        "safe_for_row_power_planning": False,
        "safe_for_shared_rail": False,
        "safe_for_physical_placement": False,
        "notes": [],
    }
    if not path.exists():
        row["notes"].append("GDS file missing.")
        return row
    labels, shapes, bbox = read_gds_labels_and_shapes(path)
    row["bbox"] = bbox.to_dict() if bbox else None
    row["labels"] = sorted({label.text for label in labels})
    vdd_ev = _rail_evidence("vdd", labels, shapes, bbox, aliases, replacement, gds_pin_audit, macro_name, variant_name)
    gnd_ev = _rail_evidence("gnd", labels, shapes, bbox, aliases, replacement, gds_pin_audit, macro_name, variant_name)
    row.update(
        {
            "vdd_labels": list(vdd_ev.label_names),
            "gnd_labels": list(gnd_ev.label_names),
            "vdd_label_count": vdd_ev.label_count,
            "gnd_label_count": gnd_ev.label_count,
            "vdd_side": vdd_ev.side,
            "gnd_side": gnd_ev.side,
            "vdd_layer": vdd_ev.layer,
            "gnd_layer": gnd_ev.layer,
            "vdd_bbox_if_known": vdd_ev.shape_bboxes[0] if vdd_ev.shape_bboxes else None,
            "gnd_bbox_if_known": gnd_ev.shape_bboxes[0] if gnd_ev.shape_bboxes else None,
            "power_rail_shapes_found": vdd_ev.shape_count > 0 or gnd_ev.shape_count > 0,
            "vdd_rail_shape_count": vdd_ev.shape_count,
            "gnd_rail_shape_count": gnd_ev.shape_count,
            "vdd_rail_span": vdd_ev.rail_span,
            "gnd_rail_span": gnd_ev.rail_span,
            "vdd_rail_touches_left_edge": vdd_ev.touches_left_edge,
            "vdd_rail_touches_right_edge": vdd_ev.touches_right_edge,
            "gnd_rail_touches_left_edge": gnd_ev.touches_left_edge,
            "gnd_rail_touches_right_edge": gnd_ev.touches_right_edge,
            "top_bottom_rail_policy": _top_bottom_policy(vdd_ev, gnd_ev),
            "left_right_abutment_possible": _left_right_abutment_possible(vdd_ev, gnd_ev),
            "rail_continuity_within_macro_proven": _within_macro_proven(vdd_ev, gnd_ev, macro_name, variant_name),
            "rail_continuity_across_abutment_proven": _across_abutment_proven(vdd_ev, gnd_ev, macro_name, variant_name),
        }
    )
    row["safe_for_row_power_planning"] = row["rail_continuity_within_macro_proven"] and macro_name in {"cell_1rw", "dummy_cell_1rw", "replica_cell_1rw"}
    row["safe_for_shared_rail"] = row["rail_continuity_across_abutment_proven"] and row["left_right_abutment_possible"]
    row["safe_for_physical_placement"] = _safe_for_physical_placement(row)
    row["notes"].extend(_row_notes(row, macro_name, variant_name))
    return row


def _rail_evidence(
    canonical: str,
    labels: tuple[GdsText, ...],
    shapes: tuple[GdsShape, ...],
    bbox: BBox | None,
    aliases: list[dict[str, Any]],
    replacement: dict[str, Any] | None,
    gds_pin_audit: dict[str, Any],
    macro_name: str,
    variant_name: str,
) -> RailEvidence:
    alias_names = {"vdd"} if canonical == "vdd" else {"gnd", "vss"}
    for alias in aliases:
        power_aliases = alias.get("power_aliases") or {}
        for key, value in power_aliases.items():
            if str(value).lower() == canonical:
                alias_names.add(str(key).lower())
    if replacement:
        for pin in replacement.get("pins", []):
            if str(pin.get("use") or "").upper() == ("POWER" if canonical == "vdd" else "GROUND"):
                alias_names.add(str(pin.get("name") or "").lower())
    label_hits = [label for label in labels if label.text.lower() in alias_names]
    layer = label_hits[0].layer if label_hits else None
    relevant_shapes = []
    for label in label_hits:
        containing = [shape for shape in shapes if shape.layer == label.layer and _contains(shape.bbox, label.x, label.y, tol=0.02)]
        if containing:
            relevant_shapes.extend(containing)
    relevant_shapes = _dedupe_shapes(relevant_shapes)
    if not relevant_shapes and gds_pin_audit:
        relevant_shapes = _fallback_shapes_from_gds_pin_audit(gds_pin_audit, macro_name, canonical)
    side = "unknown"
    if bbox and label_hits:
        side, _ = bbox.side_for_point(label_hits[0].x, label_hits[0].y)
    elif bbox and relevant_shapes:
        cx = (relevant_shapes[0].bbox.x0 + relevant_shapes[0].bbox.x1) / 2.0
        cy = (relevant_shapes[0].bbox.y0 + relevant_shapes[0].bbox.y1) / 2.0
        side, _ = bbox.side_for_point(cx, cy)
    span = _merge_span(relevant_shapes)
    return RailEvidence(
        label_names=tuple(sorted({label.text for label in label_hits})),
        label_count=len(label_hits),
        label_layer=layer,
        side=side,
        layer=relevant_shapes[0].layer if relevant_shapes else layer,
        shape_bboxes=tuple(shape.bbox.to_dict() for shape in relevant_shapes),
        shape_count=len(relevant_shapes),
        rail_span=span.to_dict() if span else None,
        touches_left_edge=bool(span and bbox and abs(span.x0 - bbox.x0) <= 0.05),
        touches_right_edge=bool(span and bbox and abs(span.x1 - bbox.x1) <= 0.05),
        touches_bottom_edge=bool(span and bbox and abs(span.y0 - bbox.y0) <= 0.05),
        touches_top_edge=bool(span and bbox and abs(span.y1 - bbox.y1) <= 0.05),
        orientation=_orientation(span),
        within_macro_continuity_proven=bool(label_hits and relevant_shapes),
    )


def _fallback_shapes_from_gds_pin_audit(gds_pin_audit: dict[str, Any], macro_name: str, canonical: str) -> list[GdsShape]:
    for item in gds_pin_audit.get("audited_macros", []):
        if item.get("macro_name") != macro_name:
            continue
        for pin in item.get("pins", []):
            if pin.get("canonical_pin") == canonical and pin.get("pin_shape_bbox"):
                bbox = pin["pin_shape_bbox"]
                return [GdsShape("boundary", None, None, BBox(bbox["x0"], bbox["y0"], bbox["x1"], bbox["y1"]))]
    return []


def _audit_spice_macro(tech: Path, macro_name: str, aliases: list[dict[str, Any]]) -> dict[str, Any]:
    spice_path = tech / "sp_lib" / f"{macro_name}.sp"
    if not spice_path.exists():
        for alias in aliases:
            rel = alias.get("spice")
            if rel:
                candidate = tech / str(rel)
                if candidate.exists():
                    spice_path = candidate
                    break
    subckt_name, pins = _parse_subckt(spice_path) if spice_path.exists() else (None, [])
    power_pins = [pin for pin in pins if pin.lower() in {"vdd", "gnd", "vss"}]
    gnd_found = any(pin.lower() in {"gnd", "vss"} for pin in pins)
    vdd_found = any(pin.lower() == "vdd" for pin in pins)
    return {
        "macro_name": macro_name,
        "spice_path": str(spice_path) if spice_path.exists() else None,
        "spice_exists": spice_path.exists(),
        "subckt_name": subckt_name,
        "spice_power_pins": power_pins,
        "spice_has_vdd": vdd_found,
        "spice_has_gnd": gnd_found,
        "matches_gds_macro": bool(subckt_name == macro_name or macro_name in {subckt_name, spice_path.stem}),
        "spice_gds_power_consistency": _spice_gds_power_consistency(macro_name, vdd_found, gnd_found),
    }


def _spice_gds_power_consistency(macro_name: str, vdd_found: bool, gnd_found: bool) -> str:
    if macro_name == "gen_precharge":
        return "spice_missing"
    if vdd_found and gnd_found:
        return "power_pins_present"
    if vdd_found and not gnd_found:
        return "vdd_only"
    return "missing_power_pins"


def _variant_comparison(variant_rows: list[dict[str, Any]], spice_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    spice_by_name = {row["macro_name"]: row for row in spice_rows}
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in variant_rows:
        grouped[row["macro_name"]].append(row)
    results = []
    for macro_name, rows in sorted(grouped.items()):
        recommended = _recommended_variant(rows, macro_name)
        spice = spice_by_name.get(macro_name)
        results.append(
            {
                "macro_name": macro_name,
                "variants": [row["variant_name"] for row in rows],
                "recommended_variant_for_future_time_control_planning": recommended["variant_name"] if recommended else None,
                "reason": _variant_reason(macro_name, recommended),
                "power_metadata_quality": {row["variant_name"]: _power_quality(row) for row in rows},
                "rail_geometry_quality": {row["variant_name"]: _geometry_quality(row) for row in rows},
                "spice_consistency": spice["spice_gds_power_consistency"] if spice else "spice_missing",
                "warnings": _variant_warnings(macro_name, rows),
            }
        )
    return results


def _precharge_decisions(precharge_rows: list[dict[str, Any]], spice_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    spice = next((row for row in spice_rows if row["macro_name"] == "gen_precharge"), None)
    results = []
    for row in precharge_rows:
        vdd_found = row["vdd_label_count"] > 0
        gnd_found = row["gnd_label_count"] > 0
        status = "explicit_vdd_gnd_power_closed_rail_unproven"
        if vdd_found and not gnd_found:
            status = "vdd_only_no_local_gnd_exception_metadata_only"
        elif not vdd_found and not gnd_found:
            status = "partial_missing_gnd"
        if spice and spice["spice_exists"] and spice["spice_has_gnd"] and status == "vdd_only_no_local_gnd_exception_metadata_only":
            status = "conflicting_power_metadata"
        results.append(
            {
                "precharge_variant": row["variant_name"],
                "gds_path": row["gds_path"],
                "vdd_found": vdd_found,
                "gnd_found": gnd_found,
                "en_label_found": any(label.lower() in {"en", "en_bar", "pre", "precharge_enb"} for label in row["labels"]),
                "openyield_no_local_gnd_exception": status == "vdd_only_no_local_gnd_exception_metadata_only",
                "gds_no_gnd_confirmed": not gnd_found,
                "spice_available": bool(spice and spice["spice_exists"]),
                "spice_gnd_found": bool(spice and spice["spice_has_gnd"]),
                "power_metadata_completion_basis": "gds_labels" if vdd_found and gnd_found else "metadata_exception" if vdd_found else "missing",
                "rail_continuity_proven": False,
                "safe_for_metadata_planning": status in {"explicit_vdd_gnd_power_closed_rail_unproven", "vdd_only_no_local_gnd_exception_metadata_only"},
                "safe_for_physical_placement": False,
                "precharge_power_status": status,
            }
        )
    return results


def _audit_summary(
    variant_rows: list[dict[str, Any]],
    spice_rows: list[dict[str, Any]],
    precharge_decisions: list[dict[str, Any]],
    decision: dict[str, Any],
) -> dict[str, Any]:
    return {
        "audited_gds_variants": len(variant_rows),
        "audited_spice_macros": len(spice_rows),
        "storage_abutment_ready_variants": [
            row["variant_name"]
            for row in variant_rows
            if row["macro_name"] in {"cell_1rw", "dummy_cell_1rw", "replica_cell_1rw"} and row["safe_for_row_power_planning"]
        ],
        "precharge_statuses": {row["precharge_variant"]: row["precharge_power_status"] for row in precharge_decisions},
        "decision": decision,
    }


def _collect_blockers(
    variant_rows: list[dict[str, Any]],
    spice_rows: list[dict[str, Any]],
    precharge_decisions: list[dict[str, Any]],
) -> list[str]:
    blockers = []
    for row in variant_rows:
        if not row["rail_continuity_within_macro_proven"]:
            blockers.append(f"{row['macro_name']}:{row['variant_name']} lacks proven within-macro rail evidence.")
        if not row["safe_for_physical_placement"]:
            blockers.append(f"{row['macro_name']}:{row['variant_name']} is not physical-placement ready.")
    for row in spice_rows:
        if not row["spice_exists"]:
            blockers.append(f"{row['macro_name']} has no local SPICE and remains metadata-only for power cross-check.")
    for row in precharge_decisions:
        if row["precharge_power_status"] != "explicit_vdd_gnd_power_closed_rail_unproven":
            blockers.append(f"PRECHARGE {row['precharge_variant']} remains exception-based: {row['precharge_power_status']}.")
    # de-duplicate while preserving order
    seen = set()
    ordered = []
    for item in blockers:
        if item not in seen:
            ordered.append(item)
            seen.add(item)
    return ordered


def format_hardcell_power_rail_continuity_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OpenYield Hardcell Power Rail Continuity Readonly Audit",
            "",
            "This report stays in readonly evidence mode. It distinguishes label presence, local rail-shape evidence, and cross-abutment proof instead of collapsing them into one readiness claim.",
            "",
            "## Audit Summary",
            "",
            f"- repo root: `{report['repo_root']}`",
            f"- tech dir: `{report['tech_dir']}`",
            f"- next recommended proof task: `{report['next_recommended_proof_task']}`",
            "",
            "```json",
            json.dumps(report["rail_continuity_decision"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Input Assets",
            "",
            "```json",
            json.dumps(report["input_assets"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## GDS Power Rail / Label Audit",
            "",
            md_table(
                [
                    "macro",
                    "variant",
                    "vdd labels",
                    "gnd labels",
                    "vdd side",
                    "gnd side",
                    "policy",
                    "within macro",
                    "across abutment",
                    "shared rail",
                    "physical-ready",
                ],
                [
                    [
                        row["macro_name"],
                        row["variant_name"],
                        row["vdd_label_count"],
                        row["gnd_label_count"],
                        row["vdd_side"],
                        row["gnd_side"],
                        row["top_bottom_rail_policy"],
                        row["rail_continuity_within_macro_proven"],
                        row["rail_continuity_across_abutment_proven"],
                        row["safe_for_shared_rail"],
                        row["safe_for_physical_placement"],
                    ]
                    for row in report["gds_power_rail_label_audit"]
                ],
            ),
            "",
            "## SPICE Cross-Check",
            "",
            md_table(
                ["macro", "spice exists", "subckt", "power pins", "consistency"],
                [
                    [
                        row["macro_name"],
                        row["spice_exists"],
                        row["subckt_name"] or "-",
                        ", ".join(row["spice_power_pins"]) or "-",
                        row["spice_gds_power_consistency"],
                    ]
                    for row in report["spice_cross_check"]
                ],
            ),
            "",
            "## PRECHARGE Special Decision",
            "",
            md_table(
                ["variant", "vdd", "gnd", "spice", "metadata planning", "physical placement", "status"],
                [
                    [
                        row["precharge_variant"],
                        row["vdd_found"],
                        row["gnd_found"],
                        row["spice_available"],
                        row["safe_for_metadata_planning"],
                        row["safe_for_physical_placement"],
                        row["precharge_power_status"],
                    ]
                    for row in report["precharge_special_decision"]
                ],
            ),
            "",
            "## Macro Variant Comparison",
            "",
            md_table(
                ["macro", "recommended variant", "spice consistency", "reason", "warnings"],
                [
                    [
                        row["macro_name"],
                        row["recommended_variant_for_future_time_control_planning"] or "-",
                        row["spice_consistency"],
                        row["reason"],
                        ", ".join(row["warnings"]) or "-",
                    ]
                    for row in report["macro_variant_comparison"]
                ],
            ),
            "",
            "## Unresolved Blockers",
            "",
            list_block(report["unresolved_blockers"]),
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


def _recommended_variant(rows: list[dict[str, Any]], macro_name: str) -> dict[str, Any] | None:
    if macro_name in {"cell_1rw", "dummy_cell_1rw", "replica_cell_1rw"}:
        return next((row for row in rows if row["variant_name"] == "default_gds_lib"), rows[0] if rows else None)
    if macro_name == "gen_col_mux_vdd_labeled":
        return rows[0] if rows else None
    if macro_name == "gen_col_mux":
        return next((row for row in rows if row["variant_name"] == "openram_replacements"), rows[0] if rows else None)
    if macro_name == "gen_precharge":
        return next((row for row in rows if row["variant_name"] == "openram_replacements"), rows[0] if rows else None)
    if macro_name in {"gen_inv", "gen_nand2", "gen_delay_inv", "gen_wl_driver"}:
        return next((row for row in rows if row["variant_name"] == "openram_replacements"), rows[0] if rows else None)
    return rows[0] if rows else None


def _variant_reason(macro_name: str, row: dict[str, Any] | None) -> str:
    if row is None:
        return "No variant available."
    if macro_name in {"cell_1rw", "dummy_cell_1rw", "replica_cell_1rw"}:
        return "Storage hardcells should stay on technology/freepdk45/gds_lib/*.gds."
    if macro_name == "gen_col_mux_vdd_labeled":
        return "Repaired column mux exposes explicit VDD/GND labels and is preferred for future planning."
    if macro_name == "gen_precharge":
        return "OpenRAM replacement carries the clearest power metadata, but remains metadata-only if GND is absent."
    return "OpenRAM replacement variant carries the strongest local power metadata among generated-logic candidates."


def _variant_warnings(macro_name: str, rows: list[dict[str, Any]]) -> list[str]:
    warnings = []
    if macro_name == "gen_precharge":
        warnings.append("PRECHARGE may remain vdd-only and metadata-only; do not treat as physical-ready.")
    if macro_name == "gen_col_mux":
        warnings.append("Unrepaired gen_col_mux variants lack complete VDD metadata.")
    if macro_name == "sense_amp":
        warnings.append("QB/dout_b remains unresolved; power audit does not prove signal-side compatibility.")
    return warnings


def _power_quality(row: dict[str, Any]) -> str:
    if row["vdd_label_count"] > 0 and row["gnd_label_count"] > 0:
        return "explicit_vdd_gnd"
    if row["vdd_label_count"] > 0:
        return "vdd_only"
    return "power_metadata_incomplete"


def _geometry_quality(row: dict[str, Any]) -> str:
    if row["rail_continuity_across_abutment_proven"]:
        return "abutment_proven"
    if row["rail_continuity_within_macro_proven"]:
        return "within_macro_only"
    return "geometry_unproven"


def _top_bottom_policy(vdd: RailEvidence, gnd: RailEvidence) -> str:
    if vdd.side == "top" and gnd.side == "bottom":
        return "top_vdd_bottom_gnd"
    if vdd.side == "bottom" and gnd.side == "top":
        return "top_gnd_bottom_vdd"
    if vdd.side in {"left", "right"} or gnd.side in {"left", "right"}:
        return "side_rails_or_mixed"
    return "unknown"


def _left_right_abutment_possible(vdd: RailEvidence, gnd: RailEvidence) -> bool:
    return (
        vdd.orientation == "vertical"
        and gnd.orientation == "vertical"
        and (vdd.touches_left_edge or vdd.touches_right_edge)
        and (gnd.touches_left_edge or gnd.touches_right_edge)
    )


def _within_macro_proven(vdd: RailEvidence, gnd: RailEvidence, macro_name: str, variant_name: str) -> bool:
    if macro_name == "gen_precharge":
        return False
    if not (vdd.within_macro_continuity_proven and (gnd.within_macro_continuity_proven or macro_name == "gen_col_mux_vdd_labeled")):
        return False
    if macro_name in {"cell_1rw", "dummy_cell_1rw", "replica_cell_1rw"}:
        return vdd.orientation == "horizontal" and gnd.orientation == "horizontal"
    return bool(vdd.shape_count or gnd.shape_count)


def _across_abutment_proven(vdd: RailEvidence, gnd: RailEvidence, macro_name: str, variant_name: str) -> bool:
    if macro_name not in {"cell_1rw", "dummy_cell_1rw", "replica_cell_1rw"}:
        return False
    return (
        vdd.orientation == "horizontal"
        and gnd.orientation == "horizontal"
        and vdd.touches_left_edge
        and vdd.touches_right_edge
        and gnd.touches_left_edge
        and gnd.touches_right_edge
    )


def _safe_for_physical_placement(row: dict[str, Any]) -> bool:
    if row["macro_name"] == "gen_precharge":
        return False
    if row["macro_name"] in {"cell_1rw", "dummy_cell_1rw", "replica_cell_1rw"}:
        return row["rail_continuity_within_macro_proven"]
    return row["rail_continuity_within_macro_proven"] and row["vdd_label_count"] > 0 and row["gnd_label_count"] > 0


def _row_notes(row: dict[str, Any], macro_name: str, variant_name: str) -> list[str]:
    notes = []
    if row["vdd_label_count"] == 0:
        notes.append("VDD label not found in GDS TEXT.")
    if row["gnd_label_count"] == 0:
        notes.append("GND label not found in GDS TEXT.")
    if not row["rail_continuity_within_macro_proven"]:
        notes.append("Within-macro rail continuity is not proven by current readonly geometry evidence.")
    if not row["rail_continuity_across_abutment_proven"]:
        notes.append("Across-abutment rail continuity is not proven.")
    if macro_name == "gen_precharge":
        notes.append("PRECHARGE is evaluated conservatively; metadata exceptions are not physical proof.")
    if macro_name == "gen_col_mux" and variant_name != "openyield_repaired":
        notes.append("Column mux VDD completeness is variant-sensitive.")
    return notes


def _contains(bbox: BBox, x: float, y: float, tol: float = 0.0) -> bool:
    return bbox.x0 - tol <= x <= bbox.x1 + tol and bbox.y0 - tol <= y <= bbox.y1 + tol


def _dedupe_shapes(shapes: list[GdsShape]) -> list[GdsShape]:
    seen = set()
    result = []
    for shape in shapes:
        key = (shape.layer, shape.datatype, round(shape.bbox.x0, 6), round(shape.bbox.y0, 6), round(shape.bbox.x1, 6), round(shape.bbox.y1, 6))
        if key not in seen:
            seen.add(key)
            result.append(shape)
    return result


def _merge_span(shapes: list[GdsShape]) -> BBox | None:
    if not shapes:
        return None
    return BBox(
        min(shape.bbox.x0 for shape in shapes),
        min(shape.bbox.y0 for shape in shapes),
        max(shape.bbox.x1 for shape in shapes),
        max(shape.bbox.y1 for shape in shapes),
    )


def _orientation(bbox: BBox | None) -> str:
    if bbox is None:
        return "unknown"
    return "horizontal" if bbox.width >= bbox.height else "vertical"


def _parse_subckt(path: Path) -> tuple[str | None, list[str]]:
    if not path.exists():
        return None, []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        text = line.strip()
        if not text or text.startswith("*"):
            continue
        parts = text.split()
        if parts and parts[0].lower() == ".subckt" and len(parts) > 2:
            return parts[1], parts[2:]
    return None, []


def _load_optional_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))
