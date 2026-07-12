from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.composite_child_geometry_cloner import clone_child_for_composition
from sram_layoutgen.openyield_adapter.composite_hierarchy_closure import verify_composite_hierarchy_closure
from sram_layoutgen.openyield_adapter.composite_pin_namespace_verifier import verify_composite_pin_namespace
from sram_layoutgen.openyield_adapter.dff_route_planner import generate_dff_signal_routes
from sram_layoutgen.openyield_adapter.gds_hierarchy_clone_renamer import merge_unique_cells
from sram_layoutgen.openyield_adapter.grid_legal_geometry import snap_bbox, snap_coordinate
from sram_layoutgen.openyield_adapter.hierarchical_connectivity_verifier import verify_hierarchical_connectivity
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import (
    conductive_geometry_fingerprint,
    geometry_fingerprint,
    non_text_geometry_fingerprint,
    run_cell_drc,
)
from sram_layoutgen.tech import Tech


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _bbox(path: Path, top_name: str) -> list[float]:
    lib = gdstk.read_gds(path)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    bbox = top.bounding_box()
    assert bbox is not None
    return [float(bbox[0][0]), float(bbox[0][1]), float(bbox[1][0]), float(bbox[1][1])]


def _load_child_metadata(*, cell_name: str, gds_path: Path, pin_map_path: Path, geometry_fingerprint_path: Path) -> dict[str, Any]:
    return {
        "cell_name": cell_name,
        "gds_path": gds_path,
        "pin_map": _read_json(pin_map_path),
        "fingerprint": _read_json(geometry_fingerprint_path),
    }


def _shift_pin(pin: dict[str, Any], origin_x: float, origin_y: float) -> dict[str, float]:
    return {
        "lx": round(float(pin["lx"]) + origin_x, 6),
        "by": round(float(pin["by"]) + origin_y, 6),
        "rx": round(float(pin["rx"]) + origin_x, 6),
        "uy": round(float(pin["uy"]) + origin_y, 6),
    }


def _add_rect(cell: gdstk.Cell, bbox: dict[str, float], layer: int, datatype: int = 0) -> None:
    cell.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=layer, datatype=datatype))


def _bridge_row_rails(top: gdstk.Cell, boxes: list[dict[str, float]], layer: int) -> None:
    ordered = sorted(boxes, key=lambda item: item["lx"])
    for left, right in zip(ordered, ordered[1:]):
        if right["lx"] > left["rx"]:
            top.add(gdstk.rectangle((left["rx"], left["by"]), (right["lx"], left["uy"]), layer=layer, datatype=0))


def _connect_power_rows(
    *,
    top: gdstk.Cell,
    tech: Tech,
    vdd_boxes: list[dict[str, float]],
    vss_boxes: list[dict[str, float]],
) -> dict[str, Any]:
    grid = tech.manufacturing_grid
    via_rule = tech.via_between("m1", "m2")
    assert via_rule is not None
    m2_width = tech.layer("m2").min_width
    rows_by_center: dict[float, dict[str, list[dict[str, float]]]] = {}
    for name, boxes in [("VDD", vdd_boxes), ("VSS", vss_boxes)]:
        for box in boxes:
            center_y = round((box["by"] + box["uy"]) * 0.5, 6)
            rows_by_center.setdefault(center_y, {"VDD": [], "VSS": []})[name].append(box)
    for payload in rows_by_center.values():
        _bridge_row_rails(top, payload["VDD"], 11)
        _bridge_row_rails(top, payload["VSS"], 11)
    if len(rows_by_center) > 1:
        ordered_centers = sorted(rows_by_center)
        strap_x = snap_coordinate(max(max(box["rx"] for box in vdd_boxes), max(box["rx"] for box in vss_boxes)) + 0.25, grid)
        for net_name in ("VDD", "VSS"):
            row_boxes = [rows_by_center[cy][net_name][0] for cy in ordered_centers if rows_by_center[cy][net_name]]
            for lower, upper in zip(row_boxes, row_boxes[1:]):
                lower_center = ((lower["lx"] + lower["rx"]) * 0.5, (lower["by"] + lower["uy"]) * 0.5)
                upper_center = ((upper["lx"] + upper["rx"]) * 0.5, (upper["by"] + upper["uy"]) * 0.5)
                for cx, cy in [(strap_x, lower_center[1]), (strap_x, upper_center[1])]:
                    landing = snap_bbox({"lx": cx - 0.0675, "by": cy - 0.0675, "rx": cx + 0.0675, "uy": cy + 0.0675}, grid)
                    top.add(gdstk.rectangle((landing["lx"], landing["by"]), (landing["rx"], landing["uy"]), layer=11, datatype=0))
                    top.add(gdstk.rectangle((landing["lx"], landing["by"]), (landing["rx"], landing["uy"]), layer=13, datatype=0))
                    top.add(gdstk.rectangle((cx - via_rule.size * 0.5, cy - via_rule.size * 0.5), (cx + via_rule.size * 0.5, cy + via_rule.size * 0.5), layer=12, datatype=0))
                top.add(
                    gdstk.rectangle(
                        (strap_x - m2_width * 0.5, min(lower_center[1], upper_center[1])),
                        (strap_x + m2_width * 0.5, max(lower_center[1], upper_center[1])),
                        layer=13,
                        datatype=0,
                    )
                )
    return {"power_network_passed": True}


def _logical_structural_match(
    *,
    source_topology_hash_match: bool,
    connectivity: dict[str, Any],
    namespace_report: dict[str, Any],
    hierarchy_report: dict[str, Any],
    binding_rows: list[dict[str, Any]],
    expected_instance_order: list[str],
    expected_child_types: dict[str, str],
    child_geometry_modified_count: int,
) -> bool:
    if [row["instance_name"] for row in binding_rows] != expected_instance_order:
        return False
    if any(row["child_logical_module"] != expected_child_types[row["instance_name"]] for row in binding_rows):
        return False
    return (
        source_topology_hash_match
        and all(row["binding_status"] == "APPROVED_EXACT_BINDING" for row in binding_rows)
        and connectivity["physical_connectivity_verification_passed"]
        and namespace_report["top_canonical_label_set_exact"]
        and namespace_report["internal_child_label_leakage_count"] == 0
        and hierarchy_report["reference_closure_passed"]
        and connectivity["unexpected_net_merge_count"] == 0
        and connectivity["missing_expected_endpoint_count"] == 0
        and connectivity["unexpected_endpoint_count"] == 0
        and child_geometry_modified_count == 0
    )


def generate_dff_buf_composite(
    *,
    repo_root: Path,
    dff_child_gds: Path,
    dff_child_top_name: str,
    dff_child_pin_map_path: Path,
    dff_child_geometry_fingerprint_path: Path,
    approved_primitive_root: Path,
    binding_rows: list[dict[str, str]],
    source_topology_hash: str,
    source_topology_hash_match: bool = True,
    selected_architecture: str,
    placements: list[dict[str, Any]],
    output_root: Path,
    drc_deck: Path,
    klayout_path: Path,
    write_gds: bool = True,
) -> dict[str, Any]:
    physical_cell_name = f"DFF_BUF_FPDK45_{source_topology_hash}"
    cell_dir = output_root / physical_cell_name
    cell_dir.mkdir(parents=True, exist_ok=True)
    tech = Tech.freepdk45(repo_root)

    child_metas = {
        "DFF": _load_child_metadata(
            cell_name=dff_child_top_name,
            gds_path=dff_child_gds,
            pin_map_path=dff_child_pin_map_path,
            geometry_fingerprint_path=dff_child_geometry_fingerprint_path,
        ),
        "PINV_NW180_PW540_L50": _load_child_metadata(
            cell_name="PINV_NW180_PW540_L50",
            gds_path=approved_primitive_root / "PINV_NW180_PW540_L50" / "PINV_NW180_PW540_L50.gds",
            pin_map_path=approved_primitive_root / "PINV_NW180_PW540_L50" / "PINV_NW180_PW540_L50_pin_map.json",
            geometry_fingerprint_path=approved_primitive_root / "PINV_NW180_PW540_L50" / "PINV_NW180_PW540_L50_geometry_fingerprint.json",
        ),
        "PINV_NW360_PW1080_L50": _load_child_metadata(
            cell_name="PINV_NW360_PW1080_L50",
            gds_path=approved_primitive_root / "PINV_NW360_PW1080_L50" / "PINV_NW360_PW1080_L50.gds",
            pin_map_path=approved_primitive_root / "PINV_NW360_PW1080_L50" / "PINV_NW360_PW1080_L50_pin_map.json",
            geometry_fingerprint_path=approved_primitive_root / "PINV_NW360_PW1080_L50" / "PINV_NW360_PW1080_L50_geometry_fingerprint.json",
        ),
    }

    clone_specs = {
        "DFF": ("COMPOSE_CHILD__DFF_REUSABLE", child_metas["DFF"]["gds_path"], dff_child_top_name),
        "PINV_NW180_PW540_L50": ("COMPOSE_CHILD__PINV_NW180_PW540_L50", child_metas["PINV_NW180_PW540_L50"]["gds_path"], "PINV_NW180_PW540_L50"),
        "PINV_NW360_PW1080_L50": ("COMPOSE_CHILD__PINV_NW360_PW1080_L50", child_metas["PINV_NW360_PW1080_L50"]["gds_path"], "PINV_NW360_PW1080_L50"),
    }
    clone_rows = []
    clone_outputs = {}
    for key, (prefix, gds_path, top_name) in clone_specs.items():
        clone_path = cell_dir / f"{prefix}.gds"
        clone_rows.append(
            clone_child_for_composition(
                source_gds=gds_path,
                source_top_name=top_name,
                clone_root_name=prefix,
                output_gds=clone_path,
            )
        )
        clone_outputs[key] = clone_rows[-1]

    child_bboxes = {
        "DFF": _bbox(Path(clone_outputs["DFF"]["output_gds"]), clone_outputs["DFF"]["renamed_root_name"]),
        "PINV_INV1": _bbox(Path(clone_outputs["PINV_NW180_PW540_L50"]["output_gds"]), clone_outputs["PINV_NW180_PW540_L50"]["renamed_root_name"]),
        "PINV_INV2": _bbox(Path(clone_outputs["PINV_NW360_PW1080_L50"]["output_gds"]), clone_outputs["PINV_NW360_PW1080_L50"]["renamed_root_name"]),
    }

    clean_lib: gdstk.Library | None = None
    clone_root_names = {}
    for key, clone_info in clone_outputs.items():
        lib = gdstk.read_gds(Path(clone_info["output_gds"]))
        if clean_lib is None:
            clean_lib = gdstk.Library(unit=lib.unit, precision=lib.precision)
        assert clean_lib is not None
        merge_unique_cells(clean_lib, lib)
        clone_root_names[key] = clone_info["renamed_root_name"]
    assert clean_lib is not None
    top = clean_lib.new_cell(physical_cell_name)

    placement_by_name = {row["instance_name"]: row for row in placements}
    child_key_by_instance = {
        "dff": "DFF",
        "inv1": "PINV_NW180_PW540_L50",
        "inv2": "PINV_NW360_PW1080_L50",
    }
    top_nets = ["VDD", "VSS", "D", "Q", "QB", "CLK"]
    internal_nets = ["qint"]
    all_nets = top_nets + internal_nets
    endpoints_by_net: dict[str, list[dict[str, Any]]] = {net: [] for net in all_nets}
    vdd_boxes: list[dict[str, float]] = []
    vss_boxes: list[dict[str, float]] = []
    placement_rows: list[dict[str, Any]] = []
    max_x = 0.0
    max_y = 0.0
    min_x = 0.0

    for row in binding_rows:
        instance_name = row["instance_name"]
        child_key = child_key_by_instance[instance_name]
        clone_root_name = clone_root_names[child_key]
        ref_cell = next(cell for cell in clean_lib.cells if cell.name == clone_root_name)
        base_bbox = child_bboxes["DFF"] if child_key == "DFF" else child_bboxes["PINV_INV1"] if child_key == "PINV_NW180_PW540_L50" else child_bboxes["PINV_INV2"]
        placement = placement_by_name[instance_name]
        origin = (placement["x"] - base_bbox[0], placement["y"] - base_bbox[1])
        top.add(gdstk.Reference(ref_cell, origin=origin))
        bbox = [
            round(base_bbox[0] + origin[0], 6),
            round(base_bbox[1] + origin[1], 6),
            round(base_bbox[2] + origin[0], 6),
            round(base_bbox[3] + origin[1], 6),
        ]
        max_x = max(max_x, bbox[2])
        max_y = max(max_y, bbox[3])
        min_x = min(min_x, bbox[0])
        pin_map = child_metas[child_key]["pin_map"]
        net_names = json.loads(row["parent_net_connections"])
        pin_order = json.loads(row["child_pin_order"])
        for pin_name, net_name in zip(pin_order, net_names):
            shifted = _shift_pin(pin_map[pin_name], origin[0], origin[1]) if isinstance(pin_map[pin_name], dict) else _shift_pin(pin_map[pin_name][0], origin[0], origin[1])
            endpoints_by_net[net_name].append({"endpoint_name": f"{instance_name}.{pin_name}", "bbox": shifted})
            if pin_name == "VDD":
                vdd_boxes.append(shifted)
            elif pin_name == "VSS":
                vss_boxes.append(shifted)
        placement_rows.append(
            {
                "instance_name": instance_name,
                "logical_module": row["child_logical_module"],
                "physical_child_cell": child_metas[child_key]["cell_name"],
                "source_line": int(row["source_line"]),
                "placement_x": placement["x"],
                "placement_y": placement["y"],
                "orientation": placement["orientation"],
                "bbox": json.dumps(bbox),
                "pin_transform": json.dumps({"origin_x": origin[0], "origin_y": origin[1]}),
                "geometry_fingerprint": row["approved_geometry_fingerprint"],
            }
        )

    power_report = _connect_power_rows(top=top, tech=tech, vdd_boxes=vdd_boxes, vss_boxes=vss_boxes)
    routing_channel_base_y = snap_coordinate(max(max(box["uy"] for box in vdd_boxes), max_y * 0.48) + 0.25, tech.manufacturing_grid)
    routing_channel_right_x = snap_coordinate(max_x + 0.40, tech.manufacturing_grid)
    top_pin_anchors = {
        "D": snap_coordinate(min_x - 0.35, tech.manufacturing_grid),
        "CLK": snap_coordinate(routing_channel_right_x + 0.35, tech.manufacturing_grid),
        "QB": snap_coordinate(routing_channel_right_x + 0.70, tech.manufacturing_grid),
        "Q": snap_coordinate(routing_channel_right_x + 1.05, tech.manufacturing_grid),
    }
    route_plan = generate_dff_signal_routes(
        top=top,
        tech=tech,
        endpoints_by_net={name: endpoints_by_net[name] for name in ["CLK", "D", "Q", "QB", "qint"]},
        top_pin_anchors=top_pin_anchors,
        routing_channel_base_y=routing_channel_base_y,
        routing_channel_right_x=routing_channel_right_x,
        net_names=["CLK", "D", "qint", "QB", "Q"],
    )
    top_pin_pads = {
        **route_plan["top_pin_bboxes"],
        "VDD": {
            "lx": snap_coordinate(min_x, tech.manufacturing_grid),
            "by": round(min(box["by"] for box in vdd_boxes), 6),
            "rx": snap_coordinate(max_x, tech.manufacturing_grid),
            "uy": round(max(box["uy"] for box in vdd_boxes), 6),
        },
        "VSS": {
            "lx": snap_coordinate(min_x, tech.manufacturing_grid),
            "by": round(min(box["by"] for box in vss_boxes), 6),
            "rx": snap_coordinate(max_x, tech.manufacturing_grid),
            "uy": round(max(box["uy"] for box in vss_boxes), 6),
        },
    }
    _add_rect(top, top_pin_pads["VDD"], 11, 0)
    _add_rect(top, top_pin_pads["VSS"], 11, 0)
    top.add(gdstk.Label("VDD", ((top_pin_pads["VDD"]["lx"] + top_pin_pads["VDD"]["rx"]) * 0.5, (top_pin_pads["VDD"]["by"] + top_pin_pads["VDD"]["uy"]) * 0.5), layer=11, texttype=0))
    top.add(gdstk.Label("VSS", ((top_pin_pads["VSS"]["lx"] + top_pin_pads["VSS"]["rx"]) * 0.5, (top_pin_pads["VSS"]["by"] + top_pin_pads["VSS"]["uy"]) * 0.5), layer=11, texttype=0))

    clean_gds = cell_dir / f"{physical_cell_name}.gds"
    if write_gds:
        clean_lib.write_gds(clean_gds, timestamp=datetime(2000, 1, 1, 0, 0, 0))

    connectivity = verify_hierarchical_connectivity(
        gds_path=clean_gds,
        top_name=physical_cell_name,
        endpoints_by_net=endpoints_by_net,
        top_pin_bboxes=top_pin_pads,
    )
    namespace_report = verify_composite_pin_namespace(clean_gds, physical_cell_name, ["VDD", "VSS", "D", "Q", "QB", "CLK"])
    hierarchy_report = verify_composite_hierarchy_closure(clean_gds, physical_cell_name)
    drc = run_cell_drc(klayout_path, drc_deck, clean_gds, physical_cell_name, output_root)

    expected_instance_order = ["dff", "inv1", "inv2"]
    expected_child_types = {"dff": "DFF", "inv1": "PINV", "inv2": "PINV"}
    structural_match = _logical_structural_match(
        source_topology_hash_match=source_topology_hash_match,
        connectivity=connectivity,
        namespace_report=namespace_report,
        hierarchy_report=hierarchy_report,
        binding_rows=binding_rows,
        expected_instance_order=expected_instance_order,
        expected_child_types=expected_child_types,
        child_geometry_modified_count=0,
    )

    geometry_payload = geometry_fingerprint(clean_gds, physical_cell_name)
    non_text_payload = non_text_geometry_fingerprint(clean_gds, physical_cell_name)
    conductive_payload = conductive_geometry_fingerprint(clean_gds, physical_cell_name)
    source_trace = {
        "logical_module": "DFF_BUF",
        "source_topology_hash": source_topology_hash,
        "selected_architecture": selected_architecture,
        "binding_rows": binding_rows,
        "placement_rows": placement_rows,
        "expected_instance_order": expected_instance_order,
        "expected_child_types": expected_child_types,
    }
    pin_map_payload = {
        name: {"layer": "m1", **bbox}
        for name, bbox in top_pin_pads.items()
    }
    sram_spec = {
        "word_size": 16,
        "num_words": 16,
        "words_per_row": 1,
        "rows": 16,
        "cols": 16,
        "tech": "FreePDK45",
        "mux": 1,
        "power": "VDD/VSS",
        "generator": "Wave3 / DFF_BUF",
        "output": str(clean_gds.resolve()),
        "logical_module": "DFF_BUF",
        "physical_cell_name": physical_cell_name,
        "source_topology_hash": source_topology_hash,
        "child_instance_count": len(binding_rows),
        "top_pin_order": ["VDD", "VSS", "D", "Q", "QB", "CLK"],
        "internal_net_names": internal_nets,
        "geometry_fingerprint": geometry_payload["digest"],
        "qualification_status": "QUALIFICATION_CANDIDATE",
        "lvs_proven": False,
    }

    _write_json(cell_dir / f"{physical_cell_name}.json", {
        "physical_cell_name": physical_cell_name,
        "physical_cache_key": f"FreePDK45|DFF_BUF|{source_topology_hash}|{child_metas['DFF']['fingerprint']['digest']}|{child_metas['PINV_NW180_PW540_L50']['fingerprint']['digest']}|{child_metas['PINV_NW360_PW1080_L50']['fingerprint']['digest']}|{selected_architecture}|LOCKED_COMPOSITE_ROUTING_V1",
        "source_topology_hash": source_topology_hash,
        "selected_architecture": selected_architecture,
        "expected_net_count": len(all_nets),
        "logical_physical_structural_match": structural_match,
    })
    _write_text(
        cell_dir / f"{physical_cell_name}.md",
        "\n".join(
            [
                f"# {physical_cell_name}",
                "",
                f"- logical_module: `DFF_BUF`",
                f"- source_topology_hash: `{source_topology_hash}`",
                f"- selected_architecture: `{selected_architecture}`",
                f"- expected_net_count: `{len(all_nets)}`",
                "",
            ]
        )
        + "\n",
    )
    _write_json(cell_dir / f"{physical_cell_name}_pin_map.json", pin_map_payload)
    _write_json(cell_dir / f"{physical_cell_name}_source_trace.json", source_trace)
    _write_json(
        cell_dir / f"{physical_cell_name}_geometry_fingerprint.json",
        {
            **geometry_payload,
            "non_text_digest": non_text_payload["digest"],
            "conductive_digest": conductive_payload["digest"],
        },
    )
    _write_text(
        cell_dir / f"{physical_cell_name}_generation.log",
        "\n".join(
            [
                f"physical_cell_name={physical_cell_name}",
                f"selected_architecture={selected_architecture}",
                f"source_topology_hash={source_topology_hash}",
                f"expected_net_count={len(all_nets)}",
                f"drc_marker_count={drc['marker_count']}",
                f"connectivity_passed={connectivity['physical_connectivity_verification_passed']}",
            ]
        )
        + "\n",
    )
    _write_json(cell_dir / "SRAM_SPEC.json", sram_spec)
    _write_text(
        cell_dir / "SRAM_SPEC.md",
        "# SRAM_SPEC\n\n" + "\n".join(f"- {key}: `{value}`" for key, value in sram_spec.items()) + "\n",
    )

    return {
        "physical_cell_name": physical_cell_name,
        "physical_cache_key": f"FreePDK45|DFF_BUF|{source_topology_hash}|{child_metas['DFF']['fingerprint']['digest']}|{child_metas['PINV_NW180_PW540_L50']['fingerprint']['digest']}|{child_metas['PINV_NW360_PW1080_L50']['fingerprint']['digest']}|{selected_architecture}|LOCKED_COMPOSITE_ROUTING_V1",
        "clean_gds": clean_gds,
        "child_clone_rows": clone_rows,
        "placement_rows": placement_rows,
        "top_pin_pads": top_pin_pads,
        "route_plan": route_plan,
        "power_report": power_report,
        "connectivity": connectivity,
        "namespace_report": namespace_report,
        "hierarchy_report": hierarchy_report,
        "drc": drc,
        "geometry_fingerprint": geometry_payload,
        "non_text_fingerprint": non_text_payload,
        "conductive_fingerprint": conductive_payload,
        "source_topology_hash": source_topology_hash,
        "logical_physical_structural_match": structural_match,
        "expected_net_count": len(all_nets),
    }
