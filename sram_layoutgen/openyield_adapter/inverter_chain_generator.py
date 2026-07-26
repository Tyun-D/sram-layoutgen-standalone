from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.inverter_chain_layout_quality import (
    build_compact_review_atlas,
    build_single_row_placements,
    build_two_row_serpentine_placements,
    compute_adjacent_gaps,
    infer_selected_gap_rows,
    pin_edge_clearances,
    write_gap_constraint_report,
    write_gap_sweep_csv,
    write_poly_metal_overlap_report,
)
from sram_layoutgen.openyield_adapter.inverter_chain_route_planner import build_inverter_chain_routes, build_row_aware_power_rails
from sram_layoutgen.openyield_adapter.inverter_chain_source_lock import MODULE_SPECS, resolve_approved_pinv_asset
from sram_layoutgen.openyield_adapter.teamb_composite_helper import (
    ChildSpec,
    add_top_label,
    annotate_from_bboxes,
    clone_children,
    instantiate_children,
    make_review_atlas,
    read_json,
    simple_composite_verification,
    transform_pin_map,
    write_gds,
)
from sram_layoutgen.tech import Tech


def _instance_order(module_name: str) -> list[str]:
    return [row["logical_child"] for row in MODULE_SPECS[module_name]["logical_children"]]


def _resolve_child_specs(repo_root: Path, module_name: str) -> list[ChildSpec]:
    out = []
    for child, physical_cell in zip(MODULE_SPECS[module_name]["logical_children"], MODULE_SPECS[module_name]["child_variants"]):
        asset = resolve_approved_pinv_asset(repo_root, physical_cell)
        out.append(
            ChildSpec(
                instance_name=child["logical_child"],
                logical_module="PINV",
                physical_cell_name=physical_cell,
                gds_path=Path(asset["gds_path"]),
                pin_map_path=Path(asset["pin_map_path"]),
            )
        )
    return out


def _child_bbox_map(child_specs: list[ChildSpec]) -> dict[str, list[float]]:
    out = {}
    for spec in child_specs:
        lib = gdstk.read_gds(spec.gds_path)
        top = next(cell for cell in lib.cells if cell.name == spec.physical_cell_name)
        bbox = top.bounding_box()
        assert bbox is not None
        out[spec.instance_name] = [round(float(bbox[0][0]), 6), round(float(bbox[0][1]), 6), round(float(bbox[1][0]), 6), round(float(bbox[1][1]), 6)]
    return out


def _place_children_from_candidate(cloned: list[Any], candidate_rows: list[dict[str, Any]]) -> list[Any]:
    by_name = {row["instance_name"]: row for row in candidate_rows}
    updated = []
    for item in cloned:
        placement = by_name[item.spec.instance_name]
        bbox = item.bbox
        orientation = str(placement.get("orientation", "R0"))
        placed_pin_map, origin = transform_pin_map(
            read_json(item.spec.pin_map_path),
            bbox=bbox,
            placement_x=float(placement["x"]),
            placement_y=float(placement["y"]),
            orientation=orientation,
        )
        width = round(float(bbox[2]) - float(bbox[0]), 6)
        height = round(float(bbox[3]) - float(bbox[1]), 6)
        placed_bbox = [
            round(float(placement["x"]), 6),
            round(float(placement["y"]), 6),
            round(float(placement["x"]) + width, 6),
            round(float(placement["y"]) + height, 6),
        ]
        updated.append(
            item.__class__(
                spec=item.spec,
                clone_root_name=item.clone_root_name,
                renamed_root_name=item.renamed_root_name,
                clone_gds_path=item.clone_gds_path,
                placement_origin=origin,
                bbox=placed_bbox,
                placed_pin_map=placed_pin_map,
                orientation=orientation,
            )
        )
    return updated


def _top_pin_bboxes(module_name: str, power_info: dict[str, Any], placed_children: list[Any]) -> dict[str, dict[str, float]]:
    return {
        "VDD": power_info["VDD"]["rails"][0],
        "VSS": power_info["VSS"]["rails"][0],
        "A": placed_children[0].placed_pin_map["A"][0],
        "Z": placed_children[-1].placed_pin_map["Z"][0],
    }


def _endpoints_by_net(module_name: str, placed_children: list[Any]) -> dict[str, list[dict[str, Any]]]:
    internal_nets = MODULE_SPECS[module_name]["internal_nets"]
    rows = {
        "A": [{"endpoint_name": f"{placed_children[0].spec.instance_name}.A", "bbox": placed_children[0].placed_pin_map["A"][0]}],
        "Z": [{"endpoint_name": f"{placed_children[-1].spec.instance_name}.Z", "bbox": placed_children[-1].placed_pin_map["Z"][0]}],
        "VDD": [],
        "VSS": [],
    }
    for item in placed_children:
        rows["VDD"].append({"endpoint_name": f"{item.spec.instance_name}.VDD", "bbox": item.placed_pin_map["VDD"][0]})
        rows["VSS"].append({"endpoint_name": f"{item.spec.instance_name}.VSS", "bbox": item.placed_pin_map["VSS"][0]})
    for net_name, left, right in zip(internal_nets, placed_children[:-1], placed_children[1:]):
        rows[net_name] = [
            {"endpoint_name": f"{left.spec.instance_name}.Z", "bbox": left.placed_pin_map["Z"][0]},
            {"endpoint_name": f"{right.spec.instance_name}.A", "bbox": right.placed_pin_map["A"][0]},
        ]
    return rows


def _layout_bbox(top: gdstk.Cell) -> list[float]:
    bbox = top.bounding_box()
    assert bbox is not None
    return [round(float(bbox[0][0]), 6), round(float(bbox[0][1]), 6), round(float(bbox[1][0]), 6), round(float(bbox[1][1]), 6)]


def _route_m2_length(route_rows: list[dict[str, Any]]) -> float:
    total = 0.0
    for row in route_rows:
        for key in ("m2_landing_bbox", "m2_trunk_bbox"):
            if key in row:
                bbox = row[key]
                total += max(float(bbox["rx"]) - float(bbox["lx"]), float(bbox["uy"]) - float(bbox["by"]))
    return round(total, 6)


def _candidate_gap_map(child_bboxes: dict[str, list[float]], placements: list[dict[str, Any]]) -> dict[str, float]:
    return {row["pair_id"]: float(row["gap"]) for row in compute_adjacent_gaps(child_bboxes=child_bboxes, placements=placements)}


def _candidate_pin_access_threshold(tech: Tech) -> float:
    return round(max(tech.layer("m1").min_space, tech.manufacturing_grid), 6)


def _build_review_atlases(
    *,
    module_name: str,
    clean_gds: Path,
    top_cell_name: str,
    placed_children: list[Any],
    route_plan: dict[str, Any],
    top_pin_bboxes: dict[str, dict[str, float]],
    power_info: dict[str, Any],
    selected_floorplan_id: str,
    gap_rows: list[dict[str, Any]],
    output_dir: Path,
) -> None:
    stage_labels: list[dict[str, Any]] = []
    stage_boxes: list[dict[str, Any]] = []
    gap_labels: list[dict[str, Any]] = []
    pin_labels: list[dict[str, Any]] = []
    power_labels: list[dict[str, Any]] = []
    power_boxes: list[dict[str, Any]] = []
    route_name_labels: list[dict[str, Any]] = []
    for index, child in enumerate(placed_children, start=1):
        bbox = child.bbox
        stage_boxes.append({"bbox": bbox})
        stage_labels.extend(
            [
                {"text": f"stage {index}", "x": round((bbox[0] + bbox[2]) * 0.5, 6), "y": round(bbox[3] + 0.10, 6)},
                {"text": child.spec.physical_cell_name, "x": round((bbox[0] + bbox[2]) * 0.5, 6), "y": round(bbox[3] + 0.20, 6)},
                {"text": f"bbox=({bbox[0]:.4f},{bbox[1]:.4f})-({bbox[2]:.4f},{bbox[3]:.4f})", "x": round((bbox[0] + bbox[2]) * 0.5, 6), "y": round(bbox[3] + 0.30, 6)},
            ]
        )
    stage_labels.append({"text": f"selected_floorplan={selected_floorplan_id}", "x": 0.2, "y": round(max(row["bbox"][3] for row in stage_boxes) + 0.45, 6)})
    for row in gap_rows:
        left = next(item for item in placed_children if item.spec.instance_name == row["left_instance"])
        right = next(item for item in placed_children if item.spec.instance_name == row["right_instance"])
        x = round((left.bbox[2] + right.bbox[0]) * 0.5, 6)
        y = round(max(left.bbox[3], right.bbox[3]) + 0.12, 6)
        gap_labels.append({"text": f"{row['pair_id']}={float(row['gap']):.4f}", "x": x, "y": y})
    for pin_name in ("A", "Z"):
        bbox = top_pin_bboxes[pin_name]
        pin_labels.append({"text": f"{pin_name}@({bbox['lx']:.4f},{bbox['by']:.4f})-({bbox['rx']:.4f},{bbox['uy']:.4f})", "x": round((bbox["lx"] + bbox["rx"]) * 0.5, 6), "y": round(bbox["uy"] + 0.10, 6)})
    for index, row in enumerate(route_plan["route_rows"]):
        if "m2_trunk_bbox" in row:
            bbox = row["m2_trunk_bbox"]
            route_name_labels.append({"text": row["net_name"], "x": round((bbox["lx"] + bbox["rx"]) * 0.5, 6), "y": round(bbox["uy"] + 0.08, 6)})
        if "via_bbox" in row:
            bbox = row["via_bbox"]
            route_name_labels.append({"text": "Via1", "x": round((bbox["lx"] + bbox["rx"]) * 0.5, 6), "y": round(bbox["uy"] + 0.05, 6)})
    for net_name in ("VDD", "VSS"):
        for rail in power_info[net_name]["rails"]:
            power_boxes.append({"bbox": [rail["lx"], rail["by"], rail["rx"], rail["uy"]]})
            power_labels.append({"text": net_name, "x": round((rail["lx"] + rail["rx"]) * 0.5, 6), "y": round(rail["uy"] + 0.06, 6)})
    build_compact_review_atlas(clean_gds=clean_gds, top_cell_name=top_cell_name, output_gds=output_dir / "review_atlas_gap_dimensions.gds", labels=stage_labels + gap_labels + route_name_labels, boxes=stage_boxes)
    build_compact_review_atlas(clean_gds=clean_gds, top_cell_name=top_cell_name, output_gds=output_dir / "review_atlas_pin_access.gds", labels=pin_labels + route_name_labels, boxes=[])
    build_compact_review_atlas(clean_gds=clean_gds, top_cell_name=top_cell_name, output_gds=output_dir / "review_atlas_power_rails.gds", labels=power_labels, boxes=power_boxes)
    build_compact_review_atlas(clean_gds=clean_gds, top_cell_name=top_cell_name, output_gds=output_dir / "review_atlas.gds", labels=stage_labels + gap_labels + pin_labels + power_labels + route_name_labels, boxes=stage_boxes + power_boxes)


def generate_inverter_chain_layout(
    *,
    repo_root: Path,
    module_name: str,
    top_cell_name: str,
    top_pin_order: list[str],
    child_variants: list[str],
    internal_net_names: list[str],
    output_dir: Path,
    candidate_placements: list[dict[str, Any]],
    klayout_bin: Path,
    drc_deck: Path,
) -> dict[str, Any]:
    tech = Tech.freepdk45(repo_root)
    child_specs = _resolve_child_specs(repo_root, module_name)
    lib, cloned, clone_rows = clone_children(child_specs, output_dir / "_clones")
    placed = _place_children_from_candidate(cloned, candidate_placements)
    top = instantiate_children(lib, top_cell_name, placed)
    power_info = build_row_aware_power_rails(top, placed, tech)
    route_plan = build_inverter_chain_routes(top=top, placed_children=placed, internal_net_names=internal_net_names, tech=tech)
    top_pins = _top_pin_bboxes(module_name, power_info, placed)
    for pin_name in top_pin_order:
        add_top_label(top, pin_name, top_pins[pin_name])
    clean_gds = output_dir / "clean.gds"
    write_gds(lib, clean_gds)
    annotate_from_bboxes(clean_gds, top_cell_name, [{"label": item.spec.instance_name, "bbox": item.bbox} for item in placed], output_dir / "annotated.gds")
    make_review_atlas(clean_gds, output_dir / "annotated.gds", top_cell_name, output_dir / "review_atlas.gds")
    endpoints_by_net = _endpoints_by_net(module_name, placed)
    report = simple_composite_verification(
        clean_gds=clean_gds,
        top_name=top_cell_name,
        canonical_labels=top_pin_order,
        endpoints_by_net=endpoints_by_net,
        top_pin_bboxes=top_pins,
        klayout_path=klayout_bin,
        drc_deck=drc_deck,
        drc_dir=output_dir / "drc",
    )
    bbox = _layout_bbox(top)
    width = round(bbox[2] - bbox[0], 6)
    height = round(bbox[3] - bbox[1], 6)
    area = round(width * height, 6)
    pin_clearances = pin_edge_clearances(top_bbox=bbox, top_pin_bboxes=top_pins)
    adjacent_gaps = compute_adjacent_gaps(child_bboxes=_child_bbox_map(child_specs), placements=candidate_placements)
    metrics = {
        "bbox": bbox,
        "bbox_width": width,
        "bbox_height": height,
        "area": area,
        "aspect_ratio": round(width / height, 6) if height else 0.0,
        "rail_alignment": len(power_info["VDD"]["rails"]) >= 1 and len(power_info["VSS"]["rails"]) >= 1,
        "rail_continuity": report["connectivity"]["physical_connectivity_verification_passed"],
        "estimated_signal_wire_length": route_plan["total_signal_wire_length"],
        "maximum_route_length": route_plan["maximum_route_length"],
        "cross_row_route_count": route_plan["cross_row_route_count"],
        "pin_access_clearance": round(min(pin_clearances["pin_A_clearance"], pin_clearances["pin_Z_clearance"]), 6),
        "pin_A_clearance": pin_clearances["pin_A_clearance"],
        "pin_Z_clearance": pin_clearances["pin_Z_clearance"],
        "foreign_net_risk": "LOW" if report["connectivity"]["unexpected_net_merge_count"] == 0 and report["connectivity"]["unexpected_endpoint_count"] == 0 else "HIGH",
        "off_grid_count": route_plan["off_grid_count"],
        "drc_marker_count": report["drc"]["marker_count"],
        "connectivity_passed": report["connectivity"]["physical_connectivity_verification_passed"],
        "foreign_net_passed": report["connectivity"]["unexpected_net_merge_count"] == 0 and report["connectivity"]["unexpected_endpoint_count"] == 0 and report["connectivity"]["power_signal_short_count"] == 0,
        "via1_count": route_plan["via1_count"],
        "m2_route_length": _route_m2_length(route_plan["route_rows"]),
        "adjacent_gaps": adjacent_gaps,
        "parent_route_geometry": route_plan["route_rows"],
    }
    (output_dir / "layout_quality_metrics.json").write_text(json.dumps(metrics, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "child_specs": child_specs,
        "clone_rows": clone_rows,
        "placement_rows": candidate_placements,
        "placed_children": placed,
        "power_info": power_info,
        "route_plan": route_plan,
        "top_pin_bboxes": top_pins,
        "endpoints_by_net": endpoints_by_net,
        "namespace": report["namespace"],
        "hierarchy": report["hierarchy"],
        "connectivity": report["connectivity"],
        "drc": report["drc"],
        "metrics": metrics,
        "clean_gds": clean_gds,
    }


def _trial_row(candidate_id: str, result: dict[str, Any], *, applicable: bool = True, applicability_reason: str = "") -> dict[str, Any]:
    metrics = result["metrics"]
    return {
        "candidate_id": candidate_id,
        "applicable": applicable,
        "applicability_reason": applicability_reason,
        "bbox_width": metrics["bbox_width"],
        "bbox_height": metrics["bbox_height"],
        "area": metrics["area"],
        "aspect_ratio": metrics["aspect_ratio"],
        "rail_alignment": metrics["rail_alignment"],
        "rail_continuity": metrics["rail_continuity"],
        "estimated_signal_wire_length": metrics["estimated_signal_wire_length"],
        "maximum_route_length": metrics["maximum_route_length"],
        "cross_row_route_count": metrics["cross_row_route_count"],
        "pin_access_clearance": metrics["pin_access_clearance"],
        "pin_A_clearance": metrics["pin_A_clearance"],
        "pin_Z_clearance": metrics["pin_Z_clearance"],
        "foreign_net_risk": metrics["foreign_net_risk"],
        "foreign_net_passed": metrics["foreign_net_passed"],
        "off_grid_count": metrics["off_grid_count"],
        "drc_marker_count": metrics["drc_marker_count"],
        "connectivity_passed": metrics["connectivity_passed"],
        "via1_count": metrics["via1_count"],
        "m2_route_length": metrics["m2_route_length"],
        "adjacent_gaps": metrics["adjacent_gaps"],
        "parent_route_geometry": metrics["parent_route_geometry"],
    }


def regenerate_selected_inverter_chain(
    *,
    repo_root: Path,
    module_name: str,
    selected_architecture: str,
    selected_placements: list[dict[str, Any]] | None,
    output_dir: Path,
    klayout_bin: Path,
    drc_deck: Path,
) -> dict[str, Any]:
    child_specs = _resolve_child_specs(repo_root, module_name)
    child_bboxes = _child_bbox_map(child_specs)
    instance_order = _instance_order(module_name)
    if selected_placements is not None:
        placements = selected_placements
    elif selected_architecture == "two_row_serpentine":
        placements = build_two_row_serpentine_placements(child_bboxes=child_bboxes, instance_order=instance_order, h_gap=0.35, v_gap=0.95)
    else:
        placements = build_single_row_placements(child_bboxes=child_bboxes, instance_order=instance_order, gaps=[0.35] * max(0, len(instance_order) - 1))
    return generate_inverter_chain_layout(
        repo_root=repo_root,
        module_name=module_name,
        top_cell_name=MODULE_SPECS[module_name]["top_cell_name"],
        top_pin_order=MODULE_SPECS[module_name]["top_pin_order"],
        child_variants=MODULE_SPECS[module_name]["child_variants"],
        internal_net_names=MODULE_SPECS[module_name]["internal_nets"],
        output_dir=output_dir,
        candidate_placements=placements,
        klayout_bin=klayout_bin,
        drc_deck=drc_deck,
    )


def generate_inverter_chain(
    *,
    repo_root: Path,
    module_name: str,
    top_cell_name: str,
    top_pin_order: list[str],
    child_variants: list[str],
    internal_net_names: list[str],
    output_dir: Path,
    klayout_bin: Path,
    drc_deck: Path,
) -> dict[str, Any]:
    child_specs = _resolve_child_specs(repo_root, module_name)
    child_bboxes = _child_bbox_map(child_specs)
    instance_order = _instance_order(module_name)
    tech = Tech.freepdk45(repo_root)
    baseline_path = output_dir / "selected_floorplan.json"
    if baseline_path.exists():
        baseline_placements = read_json(baseline_path)["selected_placements"]
    else:
        baseline_placements = build_single_row_placements(
            child_bboxes=child_bboxes,
            instance_order=instance_order,
            gaps=[0.35] * max(0, len(instance_order) - 1),
        )
    baseline_gaps = compute_adjacent_gaps(child_bboxes=child_bboxes, placements=baseline_placements)
    with tempfile.TemporaryDirectory(prefix=f"{module_name}_floorplan_", dir="/tmp") as trial_tmp:
        trial_root = Path(trial_tmp)
        generate_inverter_chain_layout(
            repo_root=repo_root,
            module_name=module_name,
            top_cell_name=top_cell_name,
            top_pin_order=top_pin_order,
            child_variants=child_variants,
            internal_net_names=internal_net_names,
            output_dir=trial_root / "baseline_current",
            candidate_placements=baseline_placements,
            klayout_bin=klayout_bin,
            drc_deck=drc_deck,
        )

        sweep_rows: list[dict[str, Any]] = []
        sweep_summary_rows: list[dict[str, Any]] = []
        gap_threshold = _candidate_pin_access_threshold(tech)
        baseline_gap_map = _candidate_gap_map(child_bboxes, baseline_placements)
        for pair_index, pair in enumerate(baseline_gaps):
            pair_id = pair["pair_id"]
            trial_index = 0
            legal_gap = float(pair["gap"])
            first_failed_gap: float | None = None
            current_gap = float(pair["gap"])
            while current_gap - tech.manufacturing_grid >= 0:
                next_gap = round(current_gap - tech.manufacturing_grid, 6)
                gap_values = [baseline_gap_map[row["pair_id"]] for row in baseline_gaps]
                gap_values[pair_index] = next_gap
                placements = build_single_row_placements(child_bboxes=child_bboxes, instance_order=instance_order, gaps=gap_values)
                trial_dir = trial_root / "gap_sweep" / pair_id / f"trial_{trial_index:03d}"
                result = generate_inverter_chain_layout(
                    repo_root=repo_root,
                    module_name=module_name,
                    top_cell_name=top_cell_name,
                    top_pin_order=top_pin_order,
                    child_variants=child_variants,
                    internal_net_names=internal_net_names,
                    output_dir=trial_dir,
                    candidate_placements=placements,
                    klayout_bin=klayout_bin,
                    drc_deck=drc_deck,
                )
                metrics = result["metrics"]
                overlap = any(float(row["gap"]) < 0 for row in metrics["adjacent_gaps"])
                pin_clearance_ok = metrics["pin_A_clearance"] >= gap_threshold and metrics["pin_Z_clearance"] >= gap_threshold
                passed = (
                    metrics["drc_marker_count"] == 0
                    and metrics["connectivity_passed"]
                    and metrics["foreign_net_passed"]
                    and metrics["rail_continuity"]
                    and not overlap
                    and pin_clearance_ok
                )
                stop_reason = ""
                if not passed:
                    if metrics["drc_marker_count"] > 0:
                        stop_reason = "DRC_MARKER"
                    elif not metrics["connectivity_passed"]:
                        stop_reason = "CONNECTIVITY_FAIL"
                    elif not metrics["foreign_net_passed"]:
                        stop_reason = "FOREIGN_NET_CONTACT"
                    elif overlap:
                        stop_reason = "CHILD_BBOX_OVERLAP"
                    elif not pin_clearance_ok:
                        stop_reason = "PIN_ACCESS_CLEARANCE"
                    elif not metrics["rail_continuity"]:
                        stop_reason = "RAIL_DISCONTINUITY"
                    else:
                        stop_reason = "ROUTE_REGEN_FAILED"
                    first_failed_gap = next_gap
                else:
                    legal_gap = next_gap
                    current_gap = next_gap
                sweep_rows.append(
                    {
                        "pair_id": pair_id,
                        "trial_index": trial_index,
                        "gap": next_gap,
                        "drc_marker_count": metrics["drc_marker_count"],
                        "connectivity_passed": metrics["connectivity_passed"],
                        "foreign_net_passed": metrics["foreign_net_passed"],
                        "rail_continuity": metrics["rail_continuity"],
                        "pin_A_clearance": metrics["pin_A_clearance"],
                        "pin_Z_clearance": metrics["pin_Z_clearance"],
                        "route_regenerated": True,
                        "child_bbox_overlap": overlap,
                        "stop_reason": stop_reason,
                        "trial_dir": str(trial_dir),
                    }
                )
                trial_index += 1
                if not passed:
                    break
            sweep_summary_rows.append(
                {
                    "pair_id": pair_id,
                    "left_instance": pair["left_instance"],
                    "right_instance": pair["right_instance"],
                    "baseline_gap": pair["gap"],
                    "minimum_legal_gap": legal_gap,
                    "first_failed_gap": first_failed_gap,
                }
            )
        sweep_summary = {"module_name": module_name, "pairs": sweep_summary_rows}
        write_gap_sweep_csv(output_dir / "adjacent_gap_sweep.csv", sweep_rows)
        (output_dir / "adjacent_gap_sweep.json").write_text(json.dumps({"module_name": module_name, "trials": sweep_rows, "pairs": sweep_summary_rows}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        selected_gap_rows = infer_selected_gap_rows(baseline_gaps=baseline_gaps, sweep_summary=sweep_summary, tech=tech)
        selected_gap_values = [row.selected_gap for row in selected_gap_rows]
        uniform_gap = max(selected_gap_values) if selected_gap_values else 0.35
        size_aware_gap_values = []
        for index, row in enumerate(selected_gap_rows):
            extra = tech.manufacturing_grid if index == len(selected_gap_rows) - 1 else 0.0
            size_aware_gap_values.append(round(max(row.selected_gap, row.minimum_legal_gap + extra), 6))

        candidates: list[dict[str, Any]] = [
            {"candidate_id": "baseline_current", "placements": baseline_placements, "applicable": True, "selection_reason_hint": "Current accepted machine-verified baseline."},
            {"candidate_id": "single_row_zero_gap_abutment", "placements": build_single_row_placements(child_bboxes=child_bboxes, instance_order=instance_order, gaps=[0.0] * max(0, len(instance_order) - 1)), "applicable": True, "selection_reason_hint": "Boundary-abutted row with zero inter-cell gap and parent-rerouted internal nets."},
            {"candidate_id": "single_row_compacted", "placements": build_single_row_placements(child_bboxes=child_bboxes, instance_order=instance_order, gaps=[uniform_gap] * max(0, len(instance_order) - 1)), "applicable": True, "selection_reason_hint": "Uniform compaction keeps a common escape corridor."},
            {"candidate_id": "single_row_min_legal_plus_margin", "placements": build_single_row_placements(child_bboxes=child_bboxes, instance_order=instance_order, gaps=selected_gap_values), "applicable": True, "selection_reason_hint": "Each adjacent pair stops one grid above the minimum legal gap."},
            {"candidate_id": "size_aware_nonuniform_gap", "placements": build_single_row_placements(child_bboxes=child_bboxes, instance_order=instance_order, gaps=size_aware_gap_values), "applicable": True, "selection_reason_hint": "Larger downstream stages keep slightly more local breathing room."},
        ]
        if module_name == "pdrive":
            candidates.append({"candidate_id": "two_row_serpentine", "placements": build_two_row_serpentine_placements(child_bboxes=child_bboxes, instance_order=instance_order, h_gap=uniform_gap, v_gap=0.95), "applicable": True, "selection_reason_hint": "Width reduction candidate for the four-stage chain."})
        else:
            candidates.append({"candidate_id": "two_row_serpentine", "placements": [], "applicable": False, "applicability_reason": "Two-stage chain remains more reviewable in a single row."})

        trial_rows = []
        for candidate in candidates:
            if not candidate["applicable"]:
                trial_rows.append(
                    {
                        "candidate_id": candidate["candidate_id"],
                        "applicable": False,
                        "applicability_reason": candidate["applicability_reason"],
                        "selection_reason_hint": candidate.get("selection_reason_hint", ""),
                    }
                )
                continue
            trial_dir = trial_root / candidate["candidate_id"]
            result = generate_inverter_chain_layout(
                repo_root=repo_root,
                module_name=module_name,
                top_cell_name=top_cell_name,
                top_pin_order=top_pin_order,
                child_variants=child_variants,
                internal_net_names=internal_net_names,
                output_dir=trial_dir,
                candidate_placements=candidate["placements"],
                klayout_bin=klayout_bin,
                drc_deck=drc_deck,
            )
            row = _trial_row(candidate["candidate_id"], result)
            row["selection_reason_hint"] = candidate["selection_reason_hint"]
            trial_rows.append(row)

    def sort_key(row: dict[str, Any]) -> tuple[int, int, int, int, int, float, float, float]:
        applicable = row.get("applicable", True)
        passes = applicable and row.get("drc_marker_count", 1) == 0 and row.get("connectivity_passed", False) and row.get("foreign_net_passed", False) and row.get("rail_continuity", False) and row.get("pin_access_clearance", -1.0) >= gap_threshold
        return (
            0 if passes else 1,
            0 if row.get("pin_access_clearance", -1.0) >= gap_threshold else 1,
            int(row.get("drc_marker_count", 9999)),
            int(row.get("cross_row_route_count", 9999)),
            int(row.get("off_grid_count", 9999)),
            float(row.get("area", 1e12)),
            float(row.get("estimated_signal_wire_length", 1e12)),
            float(row.get("maximum_route_length", 1e12)),
        )

    selected_trial = sorted([row for row in trial_rows if row.get("applicable", True)], key=sort_key)[0]
    selected_candidate = next(candidate for candidate in candidates if candidate["candidate_id"] == selected_trial["candidate_id"])
    floorplan_candidates_payload = {"module_name": module_name, "candidate_count": len(candidates), "rows": candidates, "trial_rows": trial_rows}
    (output_dir / "floorplan_candidates.json").write_text(json.dumps(floorplan_candidates_payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output_dir / "selected_floorplan.json").write_text(json.dumps({"selected_architecture": selected_trial["candidate_id"], "selected_trial": selected_trial, "selected_placements": selected_candidate["placements"]}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if output_dir.exists():
        for name in [
            "clean.gds",
            "annotated.gds",
            "review_atlas.gds",
            "review_atlas_gap_dimensions.gds",
            "review_atlas_pin_access.gds",
            "review_atlas_power_rails.gds",
            "layout_quality_metrics.json",
            "poly_metal_overlap_report.json",
            "gap_constraint_report.md",
        ]:
            path = output_dir / name
            if path.exists():
                path.unlink()
    final_result = generate_inverter_chain_layout(
        repo_root=repo_root,
        module_name=module_name,
        top_cell_name=top_cell_name,
        top_pin_order=top_pin_order,
        child_variants=child_variants,
        internal_net_names=internal_net_names,
        output_dir=output_dir,
        candidate_placements=selected_candidate["placements"],
        klayout_bin=klayout_bin,
        drc_deck=drc_deck,
    )
    final_gap_rows = final_result["metrics"]["adjacent_gaps"]
    write_gap_constraint_report(
        module_name=module_name,
        baseline_candidate_id="baseline_current",
        selected_candidate_id=selected_trial["candidate_id"],
        gap_rows=selected_gap_rows,
        output_path=output_dir / "gap_constraint_report.md",
    )
    write_poly_metal_overlap_report(clean_gds=output_dir / "clean.gds", top_cell_name=top_cell_name, output_path=output_dir / "poly_metal_overlap_report.json")
    _build_review_atlases(
        module_name=module_name,
        clean_gds=output_dir / "clean.gds",
        top_cell_name=top_cell_name,
        placed_children=final_result["placed_children"],
        route_plan=final_result["route_plan"],
        top_pin_bboxes=final_result["top_pin_bboxes"],
        power_info=final_result["power_info"],
        selected_floorplan_id=selected_trial["candidate_id"],
        gap_rows=final_gap_rows,
        output_dir=output_dir,
    )
    final_result["floorplan_selection"] = {"selected_architecture": selected_trial["candidate_id"], "selected_trial": selected_trial, "selected_placements": selected_candidate["placements"]}
    final_result["floorplan_trials"] = trial_rows
    final_result["gap_sweep_summary"] = sweep_summary
    return final_result
