from __future__ import annotations

import csv
import shutil
import tempfile
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.delay_chain_connectivity import build_delay_chain_endpoints, verify_intentional_floating_outputs
from sram_layoutgen.openyield_adapter.delay_chain_contract import build_stage_topology
from sram_layoutgen.openyield_adapter.delay_chain_floorplan_planner import build_delay_chain_candidates
from sram_layoutgen.openyield_adapter.delay_chain_review_artifacts import build_delay_chain_review_atlases
from sram_layoutgen.openyield_adapter.delay_chain_route_planner import build_delay_chain_power_rails, build_delay_chain_routes
from sram_layoutgen.openyield_adapter.delay_chain_source_lock import resolve_approved_pinv_asset
from sram_layoutgen.openyield_adapter.inverter_chain_layout_quality import write_poly_metal_overlap_report
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
    write_csv,
    write_gds,
    write_json,
    write_text,
)
from sram_layoutgen.tech import Tech


def _resolve_child_specs(repo_root: Path, child_variant: str, stage_count: int, loads_per_stage: int) -> list[ChildSpec]:
    asset = resolve_approved_pinv_asset(repo_root, child_variant)
    out: list[ChildSpec] = []
    for stage_index in range(stage_count):
        out.append(
            ChildSpec(
                instance_name=f"stage_{stage_index:02d}_driver",
                logical_module="PINV",
                physical_cell_name=child_variant,
                gds_path=Path(asset["gds_path"]),
                pin_map_path=Path(asset["pin_map_path"]),
            )
        )
        for load_index in range(loads_per_stage):
            out.append(
                ChildSpec(
                    instance_name=f"stage_{stage_index:02d}_load_{load_index:02d}",
                    logical_module="PINV",
                    physical_cell_name=child_variant,
                    gds_path=Path(asset["gds_path"]),
                    pin_map_path=Path(asset["pin_map_path"]),
                )
            )
    return out


def _child_bbox(spec: ChildSpec) -> list[float]:
    lib = gdstk.read_gds(spec.gds_path)
    cell = next(c for c in lib.cells if c.name == spec.physical_cell_name)
    bbox = cell.bounding_box()
    assert bbox is not None
    return [round(float(bbox[0][0]), 6), round(float(bbox[0][1]), 6), round(float(bbox[1][0]), 6), round(float(bbox[1][1]), 6)]


def _place_children(cloned: list[Any], placements: list[dict[str, Any]]) -> list[Any]:
    by_name = {row["instance_name"]: row for row in placements}
    updated = []
    for item in cloned:
        placement = by_name[item.spec.instance_name]
        orientation = str(placement.get("orientation", "R0"))
        placed_pin_map, origin = transform_pin_map(
            read_json(item.spec.pin_map_path),
            bbox=item.bbox,
            placement_x=float(placement["x"]),
            placement_y=float(placement["y"]),
            orientation=orientation,
        )
        width = round(float(item.bbox[2]) - float(item.bbox[0]), 6)
        height = round(float(item.bbox[3]) - float(item.bbox[1]), 6)
        updated.append(
            item.__class__(
                spec=item.spec,
                clone_root_name=item.clone_root_name,
                renamed_root_name=item.renamed_root_name,
                clone_gds_path=item.clone_gds_path,
                placement_origin=origin,
                bbox=[
                    round(float(placement["x"]), 6),
                    round(float(placement["y"]), 6),
                    round(float(placement["x"]) + width, 6),
                    round(float(placement["y"]) + height, 6),
                ],
                placed_pin_map=placed_pin_map,
                orientation=orientation,
            )
        )
    return updated


def _layout_bbox(top: gdstk.Cell) -> list[float]:
    bbox = top.bounding_box()
    assert bbox is not None
    return [round(float(bbox[0][0]), 6), round(float(bbox[0][1]), 6), round(float(bbox[1][0]), 6), round(float(bbox[1][1]), 6)]


def _copy_tree_contents(src_dir: Path, dst_dir: Path) -> None:
    if dst_dir.exists():
        shutil.rmtree(dst_dir)
    dst_dir.mkdir(parents=True, exist_ok=True)
    for path in src_dir.iterdir():
        target = dst_dir / path.name
        if path.is_dir():
            shutil.copytree(path, target)
        else:
            shutil.copy2(path, target)


def _row_abutment_report(placements: list[dict[str, Any]], child_bbox: list[float]) -> dict[str, Any]:
    row_h = round(float(child_bbox[3]) - float(child_bbox[1]), 6)
    rows: dict[float, list[dict[str, Any]]] = {}
    for row in placements:
        rows.setdefault(round(float(row["y"]), 6), []).append(row)
    row_ys = sorted(rows)
    pair_rows = []
    shared = 0
    passed = True
    for lower_y, upper_y in zip(row_ys[:-1], row_ys[1:]):
        lower_orient = sorted({str(item.get("orientation", "R0")) for item in rows[lower_y]})
        upper_orient = sorted({str(item.get("orientation", "R0")) for item in rows[upper_y]})
        vertical_gap = round(upper_y - (lower_y + row_h), 6)
        allowed = vertical_gap == 0.0 and lower_orient == ["R0"] and upper_orient == ["MX"]
        if allowed:
            shared += 1
        elif vertical_gap == 0.0:
            passed = False
        pair_rows.append(
            {
                "lower_row_y": lower_y,
                "upper_row_y": upper_y,
                "vertical_gap": vertical_gap,
                "lower_row_orientations": lower_orient,
                "upper_row_orientations": upper_orient,
                "allowed_same_net_power_abutment": allowed,
            }
        )
    return {
        "row_count": len(row_ys),
        "row_bbox_vertical_gap_zero_pair_count": sum(1 for row in pair_rows if row["vertical_gap"] == 0.0),
        "vertical_shared_rail_pair_count": shared,
        "pair_rows": pair_rows,
        "row_abutment_policy_passed": passed,
    }


def _power_report(power_info: dict[str, Any]) -> dict[str, Any]:
    return {
        "VDD": {"rail_count": len(power_info["VDD"]["rails"]), "spine_bbox": power_info["VDD"]["spine_bbox"]},
        "VSS": {"rail_count": len(power_info["VSS"]["rails"]), "spine_bbox": power_info["VSS"]["spine_bbox"]},
        "power_rail_continuity_passed": len(power_info["VDD"]["rails"]) >= 1 and len(power_info["VSS"]["rails"]) >= 1,
    }


def _write_candidate_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "candidate_id",
        "row_policy",
        "tile_policy",
        "applicable",
        "drc_marker_count",
        "connectivity_passed",
        "foreign_net_passed",
        "power_rail_continuity",
        "row_abutment_policy_passed",
        "row_count",
        "area",
        "aspect_ratio",
        "estimated_signal_wire_length",
        "maximum_stage_net_route_length",
        "maximum_branch_length",
        "cross_row_route_count",
        "horizontal_zero_gap_pair_count",
        "vertical_shared_rail_pair_count",
        "pin_in_clearance",
        "pin_out_clearance",
        "off_grid_count",
        "selected",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key) for key in fieldnames})


def _select_candidate(rows: list[dict[str, Any]], preferred_id: str | None) -> dict[str, Any]:
    passing = [
        row
        for row in rows
        if row["applicable"]
        and row["drc_marker_count"] == 0
        and row["connectivity_passed"]
        and row["foreign_net_passed"]
        and row["power_rail_continuity"]
        and row["row_abutment_policy_passed"]
        and row["off_grid_count"] == 0
    ]
    if preferred_id is not None:
        preferred = next((row for row in passing if row["candidate_id"] == preferred_id), None)
        if preferred is not None:
            return preferred
    ranked = sorted(
        passing if passing else rows,
        key=lambda row: (
            row["candidate_id"] == "single_row_reference",
            row["area"],
            row["estimated_signal_wire_length"],
            row["cross_row_route_count"],
            row["row_count"],
        ),
    )
    return ranked[0]


def _generate_once(
    *,
    repo_root: Path,
    module_name: str,
    top_cell_name: str,
    top_pin_order: list[str],
    stage_count: int,
    loads_per_stage: int,
    child_variant: str,
    output_polarity: str,
    candidate: dict[str, Any],
    output_dir: Path,
    klayout_bin: Path,
    drc_deck: Path,
) -> dict[str, Any]:
    tech = Tech.freepdk45(repo_root)
    child_specs = _resolve_child_specs(repo_root, child_variant, stage_count, loads_per_stage)
    child_bbox = _child_bbox(child_specs[0])
    lib, cloned, clone_rows = clone_children(child_specs, output_dir / "_clones")
    placed = _place_children(cloned, candidate["placements"])
    top = instantiate_children(lib, top_cell_name, placed)
    power_info = build_delay_chain_power_rails(top, placed, tech)
    route_plan = build_delay_chain_routes(top=top, placed_children=placed, stage_count=stage_count, loads_per_stage=loads_per_stage, tech=tech)
    by_name = {child.spec.instance_name: child for child in placed}
    top_pin_bboxes = {
        "VDD": power_info["VDD"]["rails"][0],
        "VSS": power_info["VSS"]["rails"][0],
        "in": by_name["stage_00_driver"].placed_pin_map["A"][0],
        "out": by_name[f"stage_{stage_count - 1:02d}_driver"].placed_pin_map["Z"][0],
    }
    for pin_name in top_pin_order:
        add_top_label(top, pin_name, top_pin_bboxes[pin_name])
    clean_gds = output_dir / "clean.gds"
    write_gds(lib, clean_gds)
    annotate_from_bboxes(clean_gds, top_cell_name, [{"label": item.spec.instance_name, "bbox": item.bbox} for item in placed], output_dir / "annotated.gds")
    make_review_atlas(clean_gds, output_dir / "annotated.gds", top_cell_name, output_dir / "review_atlas.gds")
    endpoints_by_net = build_delay_chain_endpoints(placed_children=placed, stage_count=stage_count, loads_per_stage=loads_per_stage, top_pin_bboxes=top_pin_bboxes)
    report = simple_composite_verification(clean_gds=clean_gds, top_name=top_cell_name, canonical_labels=top_pin_order, endpoints_by_net=endpoints_by_net, top_pin_bboxes=top_pin_bboxes, klayout_path=klayout_bin, drc_deck=drc_deck, drc_dir=output_dir / "drc")
    floating = verify_intentional_floating_outputs(gds_path=clean_gds, top_name=top_cell_name, placed_children=placed, stage_count=stage_count, loads_per_stage=loads_per_stage, top_pin_bboxes=top_pin_bboxes)
    floating_rows = [{**row, "bbox": by_name[row["instance_role"]].placed_pin_map["Z"][0]} for row in floating["floating_output_components"]]
    build_delay_chain_review_atlases(clean_gds=clean_gds, top_cell_name=top_cell_name, placements=[{"instance_name": child.spec.instance_name, "bbox": child.bbox} for child in placed], route_rows=route_plan["route_rows"], top_pin_bboxes=top_pin_bboxes, floating_rows=floating_rows, output_dir=output_dir)
    bbox = _layout_bbox(top)
    row_abutment = _row_abutment_report(candidate["placements"], child_bbox)
    power_report = _power_report(power_info)
    ordered_by_row: dict[float, list[Any]] = {}
    for child in placed:
        ordered_by_row.setdefault(round(child.bbox[1], 6), []).append(child)
    zero_gap = 0
    for row_children in ordered_by_row.values():
        row_children.sort(key=lambda child: child.bbox[0])
        for left, right in zip(row_children[:-1], row_children[1:]):
            if abs(round(right.bbox[0] - left.bbox[2], 6)) <= 1e-9:
                zero_gap += 1
    metrics = {
        "bbox": bbox,
        "bbox_width": round(bbox[2] - bbox[0], 6),
        "bbox_height": round(bbox[3] - bbox[1], 6),
        "area": round((bbox[2] - bbox[0]) * (bbox[3] - bbox[1]), 6),
        "aspect_ratio": round((bbox[2] - bbox[0]) / (bbox[3] - bbox[1]), 6) if (bbox[3] - bbox[1]) else 0.0,
        "row_count": len(ordered_by_row),
        "child_count": len(placed),
        "horizontal_zero_gap_pair_count": zero_gap,
        "vertical_shared_rail_pair_count": row_abutment["vertical_shared_rail_pair_count"],
        "estimated_signal_wire_length": route_plan["total_signal_wire_length"],
        "maximum_stage_net_route_length": route_plan["maximum_route_length"],
        "maximum_branch_length": route_plan["maximum_route_length"],
        "via1_count": route_plan["via1_count"],
        "route_bend_count": 0,
        "cross_row_route_count": route_plan["cross_row_route_count"],
        "pin_in_clearance": round(top_pin_bboxes["in"]["lx"] - bbox[0], 6),
        "pin_out_clearance": round(bbox[2] - top_pin_bboxes["out"]["rx"], 6),
        "power_rail_continuity": report["connectivity"]["physical_connectivity_verification_passed"] and power_report["power_rail_continuity_passed"],
        "row_abutment_policy_passed": row_abutment["row_abutment_policy_passed"],
        "drc_marker_count": report["drc"]["marker_count"],
        "connectivity_passed": report["connectivity"]["physical_connectivity_verification_passed"],
        "foreign_net_passed": report["connectivity"]["unexpected_net_merge_count"] == 0 and report["connectivity"]["unexpected_endpoint_count"] == 0 and report["connectivity"]["power_signal_short_count"] == 0,
        "off_grid_count": route_plan["off_grid_count"],
        "selected_candidate_id": candidate["candidate_id"],
    }
    write_json(output_dir / "layout_quality_metrics.json", metrics)
    write_json(output_dir / "stage_topology.json", build_stage_topology(module_name=module_name, stage_count=stage_count, loads_per_stage=loads_per_stage, output_polarity=output_polarity))
    asset = resolve_approved_pinv_asset(repo_root, child_variant)
    binding_rows = []
    for child in placed:
        role = child.spec.instance_name
        role_type = "driver" if role.endswith("driver") else "load"
        stage_index = int(role.split("_")[1])
        load_index = None if role_type == "driver" else int(role.split("_")[-1])
        binding_rows.append({"instance_role": role, "stage_index": stage_index, "role_type": role_type, "load_index": load_index, "child_variant": child_variant, "approved_child_sha": asset["actual_sha256"], "orientation": child.orientation, "x": round(child.bbox[0], 6), "y": round(child.bbox[1], 6), "Pin A logical net": "in" if role == "stage_00_driver" else (f"stage_{stage_index - 1:02d}_net" if role_type == "driver" else f"stage_{stage_index:02d}_net"), "Pin Z logical role": "out" if role == f"stage_{stage_count - 1:02d}_driver" else (f"stage_{stage_index:02d}_net" if role_type == "driver" else "intentional_floating_load_output"), "VDD logical net": "VDD", "VSS logical net": "VSS"})
    write_csv(output_dir / "instance_binding.csv", binding_rows)
    write_json(output_dir / "instance_role_manifest.json", {"rows": binding_rows})
    write_json(output_dir / "intentional_floating_output_report.json", floating)
    write_csv(output_dir / "intentional_floating_output_components.csv", floating["floating_output_components"])
    write_json(output_dir / "power_rail_report.json", power_report)
    write_json(output_dir / "vertical_row_abutment_report.json", row_abutment)
    write_poly_metal_overlap_report(clean_gds=clean_gds, top_cell_name=top_cell_name, output_path=output_dir / "poly_metal_active_report.json")
    return {"clean_gds": clean_gds, "metrics": metrics, "connectivity": report["connectivity"], "drc": report["drc"], "floating": floating, "candidate": candidate, "clone_rows": clone_rows}


def generate_delay_chain_layout(*, repo_root: Path, module_name: str, top_cell_name: str, top_pin_order: list[str], stage_count: int, loads_per_stage: int, child_variant: str, output_polarity: str, floorplan_policy: str, output_dir: Path, klayout_bin: Path, drc_deck: Path) -> dict[str, Any]:
    child_bbox = _child_bbox(_resolve_child_specs(repo_root, child_variant, stage_count, loads_per_stage)[0])
    candidates = build_delay_chain_candidates(module_name=module_name, child_bbox=child_bbox)
    candidate_rows: list[dict[str, Any]] = []
    candidate_results: dict[str, dict[str, Any]] = {}
    candidate_dirs: dict[str, Path] = {}
    temp_dirs: list[tempfile.TemporaryDirectory[str]] = []
    try:
        for candidate in candidates:
            holder = tempfile.TemporaryDirectory(prefix=f"{module_name}_{candidate['candidate_id']}_")
            temp_dirs.append(holder)
            tmp_dir = Path(holder.name)
            result = _generate_once(repo_root=repo_root, module_name=module_name, top_cell_name=top_cell_name, top_pin_order=top_pin_order, stage_count=stage_count, loads_per_stage=loads_per_stage, child_variant=child_variant, output_polarity=output_polarity, candidate=candidate, output_dir=tmp_dir, klayout_bin=klayout_bin, drc_deck=drc_deck)
            candidate_dirs[candidate["candidate_id"]] = tmp_dir
            metrics = result["metrics"]
            candidate_rows.append({"candidate_id": candidate["candidate_id"], "row_policy": candidate["row_policy"], "tile_policy": candidate["tile_policy"], "applicable": candidate.get("applicable", True), "applicability_reason": candidate.get("applicability_reason", ""), "placements": candidate["placements"], "bbox_width": metrics["bbox_width"], "bbox_height": metrics["bbox_height"], "area": metrics["area"], "aspect_ratio": metrics["aspect_ratio"], "row_count": metrics["row_count"], "child_count": metrics["child_count"], "horizontal_zero_gap_pair_count": metrics["horizontal_zero_gap_pair_count"], "vertical_shared_rail_pair_count": metrics["vertical_shared_rail_pair_count"], "estimated_signal_wire_length": metrics["estimated_signal_wire_length"], "maximum_stage_net_route_length": metrics["maximum_stage_net_route_length"], "maximum_branch_length": metrics["maximum_branch_length"], "cross_row_route_count": metrics["cross_row_route_count"], "pin_in_clearance": metrics["pin_in_clearance"], "pin_out_clearance": metrics["pin_out_clearance"], "power_rail_continuity": metrics["power_rail_continuity"], "row_abutment_policy_passed": metrics["row_abutment_policy_passed"], "drc_marker_count": metrics["drc_marker_count"], "connectivity_passed": metrics["connectivity_passed"], "foreign_net_passed": metrics["foreign_net_passed"], "off_grid_count": metrics["off_grid_count"]})
            candidate_results[candidate["candidate_id"]] = result
        selected = _select_candidate(candidate_rows, floorplan_policy)
        selected_id = selected["candidate_id"]
        _copy_tree_contents(candidate_dirs[selected_id], output_dir)
    finally:
        for holder in temp_dirs:
            holder.cleanup()
    for row in candidate_rows:
        row["selected"] = row["candidate_id"] == selected_id
    write_json(output_dir / "floorplan_candidates.json", {"module_name": module_name, "candidates": candidate_rows})
    write_json(output_dir / "selected_floorplan.json", {"module_name": module_name, "selected_candidate_id": selected_id, "selected_architecture": selected["row_policy"], "selected_tile_policy": selected["tile_policy"], "selected_placements": selected["placements"], "selection_inputs": {"preferred_policy": floorplan_policy, "pass_requirements": ["drc_marker_count == 0", "connectivity_passed", "foreign_net_passed", "power_rail_continuity", "row_abutment_policy_passed", "off_grid_count == 0"]}})
    _write_candidate_csv(output_dir / "floorplan_candidate_comparison.csv", candidate_rows)
    write_text(output_dir / "floorplan_selection_rationale.md", "\n".join([f"# {module_name} Floorplan Selection", "", f"- preferred_policy: `{floorplan_policy}`", f"- selected_candidate_id: `{selected_id}`", f"- selected_row_policy: `{selected['row_policy']}`", f"- selected_tile_policy: `{selected['tile_policy']}`", "- selection_rule: choose a candidate that is DRC clean, connectivity clean, foreign-net clean, power-rail continuous, row-abutment legal, and off-grid clean; then minimize single-row bias, area, and signal wire length."]))
    result = candidate_results[selected_id]
    result["candidate_rows"] = candidate_rows
    result["selected_candidate_id"] = selected_id
    return result
