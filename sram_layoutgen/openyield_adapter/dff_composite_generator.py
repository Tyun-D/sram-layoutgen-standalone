from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.composite_child_geometry_cloner import clone_child_for_composition
from sram_layoutgen.openyield_adapter.composite_hierarchy_closure import verify_composite_hierarchy_closure
from sram_layoutgen.openyield_adapter.composite_pin_namespace_verifier import verify_composite_pin_namespace
from sram_layoutgen.openyield_adapter.dff_floorplan_planner import build_dff_floorplan_candidates
from sram_layoutgen.openyield_adapter.dff_route_planner import generate_dff_signal_routes
from sram_layoutgen.openyield_adapter.gds_hierarchy_clone_renamer import merge_unique_cells
from sram_layoutgen.openyield_adapter.hierarchical_connectivity_verifier import verify_hierarchical_connectivity
from sram_layoutgen.openyield_adapter.module_pin_role_registry import MODULE_PIN_ROLE_REGISTRY
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import (
    conductive_geometry_fingerprint,
    geometry_fingerprint,
    non_text_geometry_fingerprint,
    run_cell_drc,
)
from sram_layoutgen.tech import Tech


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _topology_hash(binding_rows: list[dict[str, str]], net_contract: dict[str, Any]) -> str:
    payload = {
        "binding_rows": [
            {
                "instance_name": row["instance_name"],
                "child_logical_module": row["child_logical_module"],
                "parent_net_connections": row["parent_net_connections"],
            }
            for row in binding_rows
        ],
        "net_contract": net_contract,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]


def _load_child_metadata(approved_root: Path, cell_name: str) -> dict[str, Any]:
    cell_dir = approved_root / cell_name
    return {
        "cell_name": cell_name,
        "cell_dir": cell_dir,
        "gds_path": cell_dir / f"{cell_name}.gds",
        "pin_map": _read_json(cell_dir / f"{cell_name}_pin_map.json"),
        "connectivity": _read_json(cell_dir / f"{cell_name}_connectivity.json"),
        "fingerprint": _read_json(cell_dir / f"{cell_name}_geometry_fingerprint.json"),
    }


def _bbox(path: Path, top_name: str) -> list[float]:
    lib = gdstk.read_gds(path)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    bbox = top.bounding_box()
    assert bbox is not None
    return [float(bbox[0][0]), float(bbox[0][1]), float(bbox[1][0]), float(bbox[1][1])]


def _shift_pin(pin: dict[str, Any], origin_x: float, origin_y: float, base_bbox: list[float]) -> dict[str, float]:
    return {
        "lx": round(float(pin["lx"]) - base_bbox[0] + origin_x, 6),
        "by": round(float(pin["by"]) - base_bbox[1] + origin_y, 6),
        "rx": round(float(pin["rx"]) - base_bbox[0] + origin_x, 6),
        "uy": round(float(pin["uy"]) - base_bbox[1] + origin_y, 6),
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def generate_dff_composite(
    *,
    repo_root: Path,
    approved_root: Path,
    composition_contract: dict[str, Any],
    binding_rows: list[dict[str, str]],
    corrected_net_contract: dict[str, Any],
    output_root: Path,
    drc_deck: Path,
    klayout_path: Path,
) -> dict[str, Any]:
    top_hash = _topology_hash(binding_rows, corrected_net_contract)
    physical_cell_name = f"DFF_TG4_INV7_FPDK45_{top_hash}"
    cell_dir = output_root / physical_cell_name
    cell_dir.mkdir(parents=True, exist_ok=True)
    tech = Tech.freepdk45(repo_root)

    pinv_name = "PINV_NW250_PW500_L50"
    tg_name = "TRANSMISSION_GATE_NW250_PW500_L50"
    pinv_meta = _load_child_metadata(approved_root, pinv_name)
    tg_meta = _load_child_metadata(approved_root, tg_name)

    clone_rows = []
    clone_outputs = {}
    for source_name, clone_prefix in [(pinv_name, "COMPOSE_CHILD__PINV_NW250_PW500_L50"), (tg_name, "COMPOSE_CHILD__TRANSMISSION_GATE_NW250_PW500_L50")]:
        clone_path = cell_dir / f"{clone_prefix}.gds"
        clone_rows.append(
            clone_child_for_composition(
                source_gds=approved_root / source_name / f"{source_name}.gds",
                source_top_name=source_name,
                clone_root_name=clone_prefix,
                output_gds=clone_path,
            )
        )
        clone_outputs[source_name] = clone_rows[-1]

    child_bboxes = {
        "PINV": _bbox(clone_outputs[pinv_name]["output_gds"], clone_outputs[pinv_name]["renamed_root_name"]),
        "TRANSMISSION_GATE": _bbox(clone_outputs[tg_name]["output_gds"], clone_outputs[tg_name]["renamed_root_name"]),
    }
    instance_order = [row["instance_name"] for row in binding_rows]
    floorplan = build_dff_floorplan_candidates(instance_order=instance_order, child_bboxes=child_bboxes)
    selected = next(row for row in floorplan["rows"] if row["architecture"] == floorplan["selected_architecture"])
    placements = {row["instance_name"]: row for row in selected["placements"]}

    pin_maps = {pinv_name: pinv_meta["pin_map"], tg_name: tg_meta["pin_map"]}
    base_bboxes = {pinv_name: child_bboxes["PINV"], tg_name: child_bboxes["TRANSMISSION_GATE"]}

    clean_lib: gdstk.Library | None = None
    clone_libs = {}
    clone_root_names = {}
    for source_name, clone_info in clone_outputs.items():
        lib = gdstk.read_gds(clone_info["output_gds"])
        clone_libs[source_name] = lib
        if clean_lib is None:
            clean_lib = gdstk.Library(unit=lib.unit, precision=lib.precision)
        assert clean_lib is not None
        merge_unique_cells(clean_lib, lib)
        clone_root_names[source_name] = clone_info["renamed_root_name"]
    assert clean_lib is not None
    top = clean_lib.new_cell(physical_cell_name)

    placement_rows: list[dict[str, Any]] = []
    endpoints_by_net: dict[str, list[dict[str, Any]]] = {net: [] for net in ["VDD", "VSS", "D", "Q", "CLK", "CLKB", "D_b", "z1", "z2", "z3", "z4", "z5", "QB"]}

    max_y = 0.0
    max_x = 0.0
    for row in binding_rows:
        instance_name = row["instance_name"]
        child_module = row["child_logical_module"]
        physical_child = pinv_name if child_module == "PINV" else tg_name
        clone_root_name = clone_root_names[physical_child]
        ref_cell = next(cell for cell in clean_lib.cells if cell.name == clone_root_name)
        placement = placements[instance_name]
        origin = (placement["x"] - base_bboxes[physical_child][0], placement["y"] - base_bboxes[physical_child][1])
        top.add(gdstk.Reference(ref_cell, origin=origin))
        bbox = [
            round(base_bboxes[physical_child][0] + origin[0], 6),
            round(base_bboxes[physical_child][1] + origin[1], 6),
            round(base_bboxes[physical_child][2] + origin[0], 6),
            round(base_bboxes[physical_child][3] + origin[1], 6),
        ]
        max_x = max(max_x, bbox[2])
        max_y = max(max_y, bbox[3])
        net_names = json.loads(row["parent_net_connections"])
        pin_order = json.loads(row["child_pin_order"])
        for pin_name, net_name in zip(pin_order, net_names):
            shifted = _shift_pin(pin_maps[physical_child][pin_name][0], origin[0], origin[1], base_bboxes[physical_child])
            escape = None
            if child_module == "TRANSMISSION_GATE" and pin_name == "IN":
                escape = "left"
            elif child_module == "TRANSMISSION_GATE" and pin_name == "OUT":
                escape = "right"
            endpoints_by_net[net_name].append({"endpoint_name": f"{instance_name}.{pin_name}", "bbox": shifted, "m1_escape": escape})
        placement_rows.append(
            {
                "instance_name": instance_name,
                "logical_module": child_module,
                "physical_child_cell": clone_root_name,
                "source_line": int(row["source_line"]),
                "placement_x": placement["x"],
                "placement_y": placement["y"],
                "orientation": placement["orientation"],
                "bbox": json.dumps(bbox),
                "pin_transform": json.dumps({"origin_x": origin[0], "origin_y": origin[1]}),
                "geometry_fingerprint": row["approved_geometry_fingerprint"],
            }
        )

    placement_sorted = sorted(placement_rows, key=lambda row: row["placement_x"])
    for index, current in enumerate(placement_sorted[:-1]):
        current_bbox = json.loads(current["bbox"])
        next_bbox = json.loads(placement_sorted[index + 1]["bbox"])
        top.add(gdstk.rectangle((current_bbox[2], 1.7875), (next_bbox[0], 1.8525), layer=11, datatype=0))
        top.add(gdstk.rectangle((current_bbox[2], -0.0325), (next_bbox[0], 0.0325), layer=11, datatype=0))

    top_pin_pads = {
        "D": {"lx": 0.10, "by": max_y + 0.22, "rx": 0.30, "uy": max_y + 0.285},
        "CLK": {"lx": max_x * 0.5 - 0.10, "by": max_y + 0.22, "rx": max_x * 0.5 + 0.10, "uy": max_y + 0.285},
        "Q": {"lx": max_x - 0.30, "by": max_y + 0.22, "rx": max_x - 0.10, "uy": max_y + 0.285},
        "VDD": {"lx": 0.0, "by": 1.7875, "rx": max_x, "uy": 1.8525},
        "VSS": {"lx": 0.0, "by": -0.0325, "rx": max_x, "uy": 0.0325},
    }
    for name, bbox in top_pin_pads.items():
        top.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=11, datatype=0))
        top.add(gdstk.Label(name, ((bbox["lx"] + bbox["rx"]) * 0.5, (bbox["by"] + bbox["uy"]) * 0.5), layer=11, texttype=0))

    route_plan = generate_dff_signal_routes(
        top=top,
        tech=tech,
        endpoints_by_net={name: endpoints_by_net[name] for name in ["CLK", "CLKB", "D", "D_b", "z1", "z2", "z3", "z4", "z5", "Q", "QB"]},
        top_pin_pads={key: top_pin_pads[key] for key in ["D", "Q", "CLK"]},
        row_top_y=max_y,
    )

    clean_gds = cell_dir / f"{physical_cell_name}.gds"
    clean_lib.write_gds(clean_gds)

    connectivity = verify_hierarchical_connectivity(
        gds_path=clean_gds,
        top_name=physical_cell_name,
        endpoints_by_net=endpoints_by_net,
        top_pin_bboxes=top_pin_pads,
    )
    namespace_report = verify_composite_pin_namespace(clean_gds, physical_cell_name, ["VDD", "VSS", "D", "Q", "CLK"])
    hierarchy_report = verify_composite_hierarchy_closure(clean_gds, physical_cell_name)
    drc = run_cell_drc(klayout_path, drc_deck, clean_gds, physical_cell_name, output_root)

    return {
        "physical_cell_name": physical_cell_name,
        "physical_cache_key": f"FreePDK45|DFF|{top_hash}|{pinv_meta['fingerprint']['digest']}|{tg_meta['fingerprint']['digest']}|{floorplan['selected_architecture']}|LOCKED_COMPOSITE_ROUTING_V1",
        "clean_gds": clean_gds,
        "child_clone_rows": clone_rows,
        "floorplan": floorplan,
        "placement_rows": placement_rows,
        "top_pin_pads": top_pin_pads,
        "route_plan": route_plan,
        "connectivity": connectivity,
        "namespace_report": namespace_report,
        "hierarchy_report": hierarchy_report,
        "drc": drc,
        "geometry_fingerprint": geometry_fingerprint(clean_gds, physical_cell_name),
        "non_text_fingerprint": non_text_geometry_fingerprint(clean_gds, physical_cell_name),
        "conductive_fingerprint": conductive_geometry_fingerprint(clean_gds, physical_cell_name),
        "source_topology_hash": top_hash,
        "logical_physical_correspondence": [
            {
                "logical_instance_name": row["instance_name"],
                "source_child_module": row["child_logical_module"],
                "source_pin_order": row["child_pin_order"],
                "source_parent_net_connections": row["parent_net_connections"],
                "physical_instance_name": row["instance_name"],
                "physical_child_cell": row["resolved_physical_cell_name"],
                "physical_pin_map": json.dumps(pin_maps[row["resolved_physical_cell_name"]]),
                "actual_connected_nets": row["parent_net_connections"],
                "source_trace": f"{row['child_logical_module']}:{row['source_line']}",
                "binding_status": row["binding_status"],
                "structural_match": row["binding_status"] == "APPROVED_EXACT_BINDING",
                "lvs_proven": False,
            }
            for row in binding_rows
        ],
    }
