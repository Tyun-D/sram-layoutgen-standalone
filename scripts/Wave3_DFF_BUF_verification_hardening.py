from __future__ import annotations

import csv
import hashlib
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import gdstk

SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.canonical_dff_topology_identity import build_canonical_composite_topology_payload, canonical_dff_topology_hash
from sram_layoutgen.openyield_adapter.composite_hierarchy_closure import verify_composite_hierarchy_closure, write_composite_hierarchy_outputs
from sram_layoutgen.openyield_adapter.composite_pin_namespace_verifier import verify_composite_pin_namespace, write_pin_namespace_outputs
from sram_layoutgen.openyield_adapter.dff_buf_composite_generator import _logical_structural_match
from sram_layoutgen.openyield_adapter.gds_hierarchy_clone_renamer import clone_hierarchy_with_renamed_cells, merge_unique_cells
from sram_layoutgen.openyield_adapter.hierarchical_connectivity_verifier import verify_hierarchical_connectivity, write_connectivity_outputs
from sram_layoutgen.openyield_adapter.module_pin_role_registry import MODULE_PIN_ROLE_REGISTRY
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import non_text_geometry_fingerprint, run_cell_drc, read_top_cell


OUT_DIR = REPO_ROOT / "outputs/Wave3_DFF_BUF_composite_generation/current_supported_config"
EXPECTED_CLEAN_SHA = "3c677aa1def66f0930a0f549120784cbea76095726d9d26ae8b81334b8b01536"
OPENYIELD_FILES = [
    Path("/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/time_generate.py"),
    Path("/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/standard_cell.py"),
    Path("/data1/qujh/work/external/OpenYield/sram_compiler/subcircuits/base_subcircuit.py"),
]
DEBUG_TEXT_LAYER = 239
DEBUG_SHAPE_LAYER = 240


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _ordered_binding_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: (int(row["source_line"]), row["instance_name"]))


def _instance_table_rows() -> list[dict[str, str]]:
    return _load_csv(REPO_ROOT / "docs/Wave3_DFF_BUF_instance_connection_table.csv")


def _binding_rows() -> list[dict[str, str]]:
    return _ordered_binding_rows(_load_csv(REPO_ROOT / "docs/Wave3_DFF_BUF_child_binding_matrix.csv"))


def _topology_rows_from_binding(binding_rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    ordered = []
    for row in binding_rows:
        ordered.append(
            {
                "instance_name": row["instance_name"],
                "child_logical_module": row["child_logical_module"],
                "source_line": int(row["source_line"]),
                "child_pin_order": json.loads(row["child_pin_order"]),
                "parent_net_connections": json.loads(row["parent_net_connections"]),
            }
        )
    return ordered


def _canonical_payload(binding_rows: list[dict[str, str]], net_contract: dict[str, Any]) -> dict[str, Any]:
    registry_payload = {"schema_version": "M12C4A_PIN_ROLE_REGISTRY_V1", "modules": MODULE_PIN_ROLE_REGISTRY}
    return build_canonical_composite_topology_payload(
        module_name="DFF_BUF",
        binding_rows=binding_rows,
        net_contract=net_contract,
        top_pin_order=["VDD", "VSS", "D", "Q", "QB", "CLK"],
        internal_net_order=["qint"],
        module_pin_role_registry=registry_payload,
        openyield_files=OPENYIELD_FILES,
    )


def _topology_hash_report(binding_rows: list[dict[str, str]], net_contract: dict[str, Any]) -> tuple[str, bool]:
    payload = _canonical_payload(binding_rows, net_contract)
    computed = canonical_dff_topology_hash(payload)
    report_hash = _read_json(REPO_ROOT / "docs/Wave3_DFF_BUF_stage_report.json")["canonical_topology_hash"]
    return computed, computed == report_hash


def _topology_negative_test(binding_rows: list[dict[str, str]], net_contract: dict[str, Any]) -> dict[str, Any]:
    positive_payload = _canonical_payload(binding_rows, net_contract)
    positive_hash = canonical_dff_topology_hash(positive_payload)
    mutated_rows = [dict(row) for row in binding_rows]
    for row in mutated_rows:
        if row["instance_name"] == "inv1":
            nets = json.loads(row["parent_net_connections"])
            nets[2] = "QB"
            row["parent_net_connections"] = json.dumps(nets)
            break
    negative_payload = _canonical_payload(mutated_rows, net_contract)
    negative_hash = canonical_dff_topology_hash(negative_payload)
    structural_false = _logical_structural_match(
        source_topology_hash_match=negative_hash == positive_hash,
        connectivity={
            "physical_connectivity_verification_passed": True,
            "unexpected_net_merge_count": 0,
            "missing_expected_endpoint_count": 0,
            "unexpected_endpoint_count": 0,
        },
        namespace_report={"top_canonical_label_set_exact": True, "internal_child_label_leakage_count": 0},
        hierarchy_report={"reference_closure_passed": True},
        binding_rows=mutated_rows,
        expected_instance_order=["dff", "inv1", "inv2"],
        expected_child_types={"dff": "DFF", "inv1": "PINV", "inv2": "PINV"},
        child_geometry_modified_count=0,
    )
    return {
        "positive_hash": positive_hash,
        "negative_hash": negative_hash,
        "hash_changed": positive_hash != negative_hash,
        "source_topology_hash_match_after_mutation": negative_hash == positive_hash,
        "logical_physical_structural_match_after_mutation": structural_false,
        "passed": positive_hash != negative_hash and structural_false is False,
    }


def _cell_top_name(path: Path) -> str:
    lib = gdstk.read_gds(path)
    tops = lib.top_level()
    if len(tops) != 1:
        raise RuntimeError(f"Expected one top-level cell in {path}, found {len(tops)}")
    return tops[0].name


def _child_geometry_immutability(binding_rows: list[dict[str, str]], physical_cell_name: str) -> tuple[list[dict[str, Any]], int, dict[str, Any]]:
    source_trace = _read_json(OUT_DIR / f"{physical_cell_name}_source_trace.json")
    placement_rows = {row["instance_name"]: row for row in source_trace["placement_rows"]}
    clone_dir = OUT_DIR / "candidate" / physical_cell_name
    clone_path_by_instance = {
        "dff": clone_dir / "COMPOSE_CHILD__DFF_REUSABLE.gds",
        "inv1": clone_dir / "COMPOSE_CHILD__PINV_NW180_PW540_L50.gds",
        "inv2": clone_dir / "COMPOSE_CHILD__PINV_NW360_PW1080_L50.gds",
    }
    rows: list[dict[str, Any]] = []
    modified = 0
    for row in binding_rows:
        instance = row["instance_name"]
        approved_path = Path(row["approved_physical_source_path"])
        approved_top = row["resolved_physical_cell_name"]
        clone_path = clone_path_by_instance[instance]
        clone_top = _cell_top_name(clone_path)
        approved_digest = non_text_geometry_fingerprint(approved_path, approved_top)["digest"]
        cloned_digest = non_text_geometry_fingerprint(clone_path, clone_top)["digest"]
        hierarchy_digest = non_text_geometry_fingerprint(OUT_DIR / "DFF_BUF_clean.gds", clone_top)["digest"]
        match = approved_digest == cloned_digest == hierarchy_digest
        if not match:
            modified += 1
        rows.append(
            {
                "instance": instance,
                "approved_digest": approved_digest,
                "cloned_digest": cloned_digest,
                "hierarchy_digest": hierarchy_digest,
                "match": match,
            }
        )

    negative_dir = OUT_DIR / "_hardening_negative_tests"
    negative_dir.mkdir(parents=True, exist_ok=True)
    negative_gds = negative_dir / "child_geometry_negative.gds"
    shutil.copyfile(clone_path_by_instance["inv1"], negative_gds)
    lib, top = read_top_cell(negative_gds, _cell_top_name(negative_gds))
    top.add(gdstk.rectangle((0.0, 0.0), (0.05, 0.05), layer=250, datatype=0))
    lib.write_gds(negative_gds, timestamp=datetime(2000, 1, 1, 0, 0, 0))
    negative_digest = non_text_geometry_fingerprint(negative_gds, _cell_top_name(negative_gds))["digest"]
    negative_test = {
        "reference_digest": rows[1]["cloned_digest"],
        "mutated_digest": negative_digest,
        "detected_modified": negative_digest != rows[1]["cloned_digest"],
        "passed": negative_digest != rows[1]["cloned_digest"],
    }
    return rows, modified, negative_test


def _pin_role(module_name: str, pin_name: str) -> str:
    return MODULE_PIN_ROLE_REGISTRY[module_name][pin_name]


def _polarity_audit_from_instance_table(rows: list[dict[str, str]]) -> dict[str, Any]:
    pin_to_net = {(row["instance"], row["child_pin"]): row["parent_net"] for row in rows}
    inverter_edges = []
    for row in rows:
        if row["type"] == "PINV" and row["child_pin"] == "A":
            instance = row["instance"]
            src = row["parent_net"]
            dst = pin_to_net[(instance, "Z")]
            inverter_edges.append({"instance": instance, "input_net": src, "output_net": dst})
    edge_by_input = {edge["input_net"]: edge for edge in inverter_edges}
    path = []
    current = "qint"
    visited_inputs: set[str] = set()
    cycle_detected = False
    while current in edge_by_input:
        if current in visited_inputs:
            cycle_detected = True
            break
        visited_inputs.add(current)
        edge = edge_by_input[current]
        path.append(edge)
        current = edge["output_net"]
    qint_to_qb = len([edge for edge in path if edge["output_net"] == "QB"])
    qb_to_q = 1 if any(edge["input_net"] == "QB" and edge["output_net"] == "Q" for edge in path) else 0
    qint_to_q = len(path) if path and path[-1]["output_net"] == "Q" else None
    d_extra = any(edge["input_net"] == "D" for edge in inverter_edges)
    clk_extra = any(edge["input_net"] == "CLK" for edge in inverter_edges)
    passed = (
        qint_to_qb == 1
        and qb_to_q == 1
        and qint_to_q == 2
        and not d_extra
        and not clk_extra
        and len(path) == 2
        and path[0]["output_net"] == "QB"
        and path[1]["output_net"] == "Q"
        and not cycle_detected
    )
    return {
        "inverter_edges": inverter_edges,
        "path_from_qint": path,
        "cycle_detected": cycle_detected,
        "qint_to_qb_inverter_count": qint_to_qb,
        "qb_to_q_inverter_count": qb_to_q,
        "qint_to_q_inverter_count": qint_to_q,
        "final_q_same_polarity_as_dff_q": qint_to_q == 2,
        "final_qb_inverted_from_dff_q": qint_to_qb == 1,
        "d_has_no_parent_level_inverter": not d_extra,
        "clk_has_no_parent_level_inverter": not clk_extra,
        "source_level_functional_polarity_audit_passed": passed,
    }


def _polarity_negative_test(rows: list[dict[str, str]]) -> dict[str, Any]:
    mutated = [dict(row) for row in rows]
    for row in mutated:
        if row["instance"] == "inv2" and row["child_pin"] == "Z":
            row["parent_net"] = "QB"
            break
    result = _polarity_audit_from_instance_table(mutated)
    return {
        "mutated_inv2_z_parent_net": "QB",
        "source_level_functional_polarity_audit_passed_after_mutation": result["source_level_functional_polarity_audit_passed"],
        "passed": result["source_level_functional_polarity_audit_passed"] is False,
    }


def _shift_pin(pin: dict[str, Any], origin_x: float, origin_y: float) -> dict[str, float]:
    return {
        "lx": round(float(pin["lx"]) + origin_x, 6),
        "by": round(float(pin["by"]) + origin_y, 6),
        "rx": round(float(pin["rx"]) + origin_x, 6),
        "uy": round(float(pin["uy"]) + origin_y, 6),
    }


def _load_endpoints(binding_rows: list[dict[str, str]], physical_cell_name: str) -> tuple[dict[str, list[dict[str, Any]]], dict[str, dict[str, float]], dict[str, Any]]:
    top_pin_map = _read_json(OUT_DIR / f"{physical_cell_name}_pin_map.json")
    source_trace = _read_json(OUT_DIR / f"{physical_cell_name}_source_trace.json")
    placements = {row["instance_name"]: row for row in source_trace["placement_rows"]}
    endpoints_by_net: dict[str, list[dict[str, Any]]] = {name: [] for name in ["VDD", "VSS", "D", "Q", "QB", "CLK", "qint"]}
    for row in binding_rows:
        pin_map = _read_json(Path(row["approved_pin_map_path"]))
        pins = json.loads(row["child_pin_order"])
        nets = json.loads(row["parent_net_connections"])
        transform = json.loads(placements[row["instance_name"]]["pin_transform"])
        for pin_name, net_name in zip(pins, nets):
            pin_data = pin_map[pin_name] if isinstance(pin_map[pin_name], dict) else pin_map[pin_name][0]
            bbox = _shift_pin(pin_data, transform["origin_x"], transform["origin_y"])
            endpoints_by_net[net_name].append({"endpoint_name": f"{row['instance_name']}.{pin_name}", "bbox": bbox})
    return endpoints_by_net, top_pin_map, source_trace


def _quick_reference_inventory(gds_path: Path, top_name: str) -> dict[str, Any]:
    lib = gdstk.read_gds(gds_path)
    cells = {cell.name: cell for cell in lib.cells}
    targets: list[str] = []
    missing: set[str] = set()

    def visit(name: str, stack: list[str], seen: set[str]) -> int:
        if name in stack:
            return 1
        if name in seen:
            return 0
        seen.add(name)
        cell = cells[name]
        cycles = 0
        for ref in cell.references:
            target = ref.cell_name or ref.cell.name
            targets.append(target)
            if target not in cells:
                missing.add(target)
                continue
            cycles += visit(target, stack + [name], seen)
        return cycles

    top_levels = [cell.name for cell in lib.top_level()]
    seen: set[str] = set()
    cycle_count = visit(top_name, [], seen)
    return {
        "atlas_top_cell": top_name,
        "top_level_cell_count": len(top_levels),
        "top_level_cells": top_levels,
        "reference_target_count": len(targets),
        "missing_reference_target_count": len(missing),
        "missing_reference_targets": sorted(missing),
        "reference_cycle_count": cycle_count,
    }


def _build_review_atlas(
    *,
    clean_gds: Path,
    clean_top_name: str,
    annotated_gds: Path,
    annotated_top_name: str,
    binding_rows: list[dict[str, str]],
    source_trace: dict[str, Any],
    route_plan: dict[str, Any],
    top_pin_map: dict[str, dict[str, Any]],
    output_gds: Path,
) -> dict[str, Any]:
    atlas_lib = gdstk.Library()
    clean_lib, clean_root, _ = clone_hierarchy_with_renamed_cells(
        source_gds=clean_gds,
        root_cell_name=clean_top_name,
        namespace_prefix="CLEAN_FULL_VIEW",
    )
    anno_lib, anno_root, _ = clone_hierarchy_with_renamed_cells(
        source_gds=annotated_gds,
        root_cell_name=annotated_top_name,
        namespace_prefix="ANNOTATED_FULL_VIEW",
    )
    merge_unique_cells(atlas_lib, clean_lib)
    merge_unique_cells(atlas_lib, anno_lib)

    placement_rows = {row["instance_name"]: row for row in source_trace["placement_rows"]}
    child_pin_maps = {row["instance_name"]: _read_json(Path(row["approved_pin_map_path"])) for row in binding_rows}

    def add_panel_title(cell: gdstk.Cell, title: str, y: float = 0.0) -> None:
        cell.add(gdstk.Label(title, (0.2, y), layer=DEBUG_TEXT_LAYER, texttype=0))

    def add_box(cell: gdstk.Cell, bbox: dict[str, float], layer: int = DEBUG_SHAPE_LAYER) -> None:
        cell.add(gdstk.rectangle((bbox["lx"], bbox["by"]), (bbox["rx"], bbox["uy"]), layer=layer, datatype=0))

    clean_cell = next(cell for cell in atlas_lib.cells if cell.name == clean_root)
    anno_cell = next(cell for cell in atlas_lib.cells if cell.name == anno_root)
    clean_bbox = clean_cell.bounding_box()
    assert clean_bbox is not None
    clean_w = float(clean_bbox[1][0] - clean_bbox[0][0])
    clean_h = float(clean_bbox[1][1] - clean_bbox[0][1])

    panel_names: list[str] = []

    panel_clean = atlas_lib.new_cell("CLEAN_FULL_VIEW")
    panel_clean.add(gdstk.Reference(clean_cell, origin=(0, 0)))
    add_panel_title(panel_clean, "CLEAN_FULL_VIEW", clean_h + 0.4)
    panel_names.append(panel_clean.name)

    panel_anno = atlas_lib.new_cell("ANNOTATED_FULL_VIEW")
    panel_anno.add(gdstk.Reference(anno_cell, origin=(0, 0)))
    add_panel_title(panel_anno, "ANNOTATED_FULL_VIEW", clean_h + 0.4)
    panel_names.append(panel_anno.name)

    panel_place = atlas_lib.new_cell("CHILD_PLACEMENT_VIEW")
    add_panel_title(panel_place, "CHILD_PLACEMENT_VIEW", clean_h + 0.4)
    for row in binding_rows:
        placement = placement_rows[row["instance_name"]]
        bbox = json.loads(placement["bbox"])
        box = {"lx": bbox[0], "by": bbox[1], "rx": bbox[2], "uy": bbox[3]}
        add_box(panel_place, box, DEBUG_SHAPE_LAYER)
        panel_place.add(gdstk.Label(f"{row['instance_name']}:{row['resolved_physical_cell_name']}", (box["lx"] + 0.1, box["uy"] + 0.1), layer=DEBUG_TEXT_LAYER, texttype=0))
    panel_names.append(panel_place.name)

    panel_power = atlas_lib.new_cell("POWER_ONLY_VIEW")
    add_panel_title(panel_power, "POWER_ONLY_VIEW", clean_h + 0.4)
    for name in ("VDD", "VSS"):
        add_box(panel_power, top_pin_map[name], 241 if name == "VDD" else 242)
        panel_power.add(gdstk.Label(name, ((top_pin_map[name]["lx"] + top_pin_map[name]["rx"]) * 0.5, (top_pin_map[name]["by"] + top_pin_map[name]["uy"]) * 0.5), layer=DEBUG_TEXT_LAYER, texttype=0))
    for row in binding_rows:
        transform = json.loads(placement_rows[row["instance_name"]]["pin_transform"])
        pin_map = child_pin_maps[row["instance_name"]]
        for pin_name in ("VDD", "VSS"):
            pin = pin_map[pin_name] if isinstance(pin_map[pin_name], dict) else pin_map[pin_name][0]
            add_box(panel_power, _shift_pin(pin, transform["origin_x"], transform["origin_y"]), 241 if pin_name == "VDD" else 242)
    panel_names.append(panel_power.name)

    panel_signal = atlas_lib.new_cell("SIGNAL_ROUTING_ONLY_VIEW")
    add_panel_title(panel_signal, "SIGNAL_ROUTING_ONLY_VIEW", clean_h + 0.4)
    for segment in route_plan["route_segments"]:
        layer = 243 if segment["layer"] == "m1" else 244
        x0, y0 = segment["start"]
        x1, y1 = segment["end"]
        width = segment["width"]
        if x0 == x1:
            bbox = {"lx": x0 - width * 0.5, "by": min(y0, y1), "rx": x0 + width * 0.5, "uy": max(y0, y1)}
        else:
            bbox = {"lx": min(x0, x1), "by": y0 - width * 0.5, "rx": max(x0, x1), "uy": y0 + width * 0.5}
        add_box(panel_signal, bbox, layer)
        panel_signal.add(gdstk.Label(segment["net_name"], (bbox["lx"], bbox["uy"] + 0.05), layer=DEBUG_TEXT_LAYER, texttype=0))
    for via in route_plan["vias"]:
        add_box(panel_signal, {"lx": via["x"] - via["size"] * 0.5, "by": via["y"] - via["size"] * 0.5, "rx": via["x"] + via["size"] * 0.5, "uy": via["y"] + via["size"] * 0.5}, 245)
        panel_signal.add(gdstk.Label("Via1", (via["x"], via["y"]), layer=DEBUG_TEXT_LAYER, texttype=0))
    panel_names.append(panel_signal.name)

    panel_top = atlas_lib.new_cell("TOP_PIN_VIEW")
    add_panel_title(panel_top, "TOP_PIN_VIEW", clean_h + 0.4)
    for name, bbox in top_pin_map.items():
        add_box(panel_top, bbox, 246)
        panel_top.add(gdstk.Label(name, ((bbox["lx"] + bbox["rx"]) * 0.5, (bbox["by"] + bbox["uy"]) * 0.5), layer=DEBUG_TEXT_LAYER, texttype=0))
    panel_names.append(panel_top.name)

    panel_dff = atlas_lib.new_cell("DFF_INTERFACE_VIEW")
    add_panel_title(panel_dff, "DFF_INTERFACE_VIEW", clean_h + 0.4)
    dff_place = placement_rows["dff"]
    dff_bbox = json.loads(dff_place["bbox"])
    add_box(panel_dff, {"lx": dff_bbox[0], "by": dff_bbox[1], "rx": dff_bbox[2], "uy": dff_bbox[3]}, 247)
    dff_transform = json.loads(dff_place["pin_transform"])
    dff_map = child_pin_maps["dff"]
    for pin_name in ("D", "Q", "CLK", "VDD", "VSS"):
        add_box(panel_dff, _shift_pin(dff_map[pin_name], dff_transform["origin_x"], dff_transform["origin_y"]), 247)
        panel_dff.add(gdstk.Label(f"dff.{pin_name}", (_shift_pin(dff_map[pin_name], dff_transform["origin_x"], dff_transform["origin_y"])["lx"], _shift_pin(dff_map[pin_name], dff_transform["origin_x"], dff_transform["origin_y"])["uy"] + 0.05), layer=DEBUG_TEXT_LAYER, texttype=0))
    for segment in route_plan["route_segments"]:
        if segment["net_name"] in {"D", "CLK", "qint"}:
            x0, y0 = segment["start"]
            x1, y1 = segment["end"]
            width = segment["width"]
            if x0 == x1:
                bbox = {"lx": x0 - width * 0.5, "by": min(y0, y1), "rx": x0 + width * 0.5, "uy": max(y0, y1)}
            else:
                bbox = {"lx": min(x0, x1), "by": y0 - width * 0.5, "rx": max(x0, x1), "uy": y0 + width * 0.5}
            add_box(panel_dff, bbox, 243 if segment["layer"] == "m1" else 244)
    panel_names.append(panel_dff.name)

    panel_pinv = atlas_lib.new_cell("PINV_INTERFACE_VIEW")
    add_panel_title(panel_pinv, "PINV_INTERFACE_VIEW", clean_h + 0.4)
    for inst in ("inv1", "inv2"):
        place = placement_rows[inst]
        bbox = json.loads(place["bbox"])
        add_box(panel_pinv, {"lx": bbox[0], "by": bbox[1], "rx": bbox[2], "uy": bbox[3]}, 248)
        transform = json.loads(place["pin_transform"])
        pin_map = child_pin_maps[inst]
        for pin_name in ("A", "Z"):
            pin_data = pin_map[pin_name] if isinstance(pin_map[pin_name], dict) else pin_map[pin_name][0]
            shifted = _shift_pin(pin_data, transform["origin_x"], transform["origin_y"])
            add_box(panel_pinv, shifted, 248)
            panel_pinv.add(gdstk.Label(f"{inst}.{pin_name}", (shifted["lx"], shifted["uy"] + 0.05), layer=DEBUG_TEXT_LAYER, texttype=0))
    for segment in route_plan["route_segments"]:
        if segment["net_name"] in {"qint", "QB", "Q"}:
            x0, y0 = segment["start"]
            x1, y1 = segment["end"]
            width = segment["width"]
            if x0 == x1:
                bbox = {"lx": x0 - width * 0.5, "by": min(y0, y1), "rx": x0 + width * 0.5, "uy": max(y0, y1)}
            else:
                bbox = {"lx": min(x0, x1), "by": y0 - width * 0.5, "rx": max(x0, x1), "uy": y0 + width * 0.5}
            add_box(panel_pinv, bbox, 243 if segment["layer"] == "m1" else 244)
    panel_names.append(panel_pinv.name)

    atlas_top = atlas_lib.new_cell("WAVE3_DFF_BUF_REVIEW_ATLAS")
    panels = [next(cell for cell in atlas_lib.cells if cell.name == name) for name in panel_names]
    x_step = clean_w + 2.0
    y_step = clean_h + 2.2
    for idx, panel in enumerate(panels):
        col = idx % 2
        row = idx // 2
        atlas_top.add(gdstk.Reference(panel, origin=(col * x_step, -row * y_step)))
    output_gds.parent.mkdir(parents=True, exist_ok=True)
    atlas_lib.write_gds(output_gds, timestamp=datetime(2000, 1, 1, 0, 0, 0))
    inventory = _quick_reference_inventory(output_gds, "WAVE3_DFF_BUF_REVIEW_ATLAS")
    return {
        "atlas_top_cell": "WAVE3_DFF_BUF_REVIEW_ATLAS",
        "panel_count": len(panel_names),
        "panel_names": panel_names,
        "reference_target_count": inventory["reference_target_count"],
        "missing_reference_target_count": inventory["missing_reference_target_count"],
        "reference_cycle_count": inventory["reference_cycle_count"],
    }


def _update_ledgers(stage_status: str, recommended_next_stage: str, recommended_next_stage_reason: str) -> None:
    json_path = REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json"
    status = _read_json(json_path)
    status["current_stage"] = "Wave3 / DFF_BUF_VERIFICATION_HARDENING"
    status["recommended_next_stage"] = recommended_next_stage
    status["recommended_next_stage_reason"] = recommended_next_stage_reason
    status["Wave3_DFF_BUF"] = {"current_status": stage_status}
    _write_json(json_path, status)
    for md_name in [
        "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        "PROJECT_NETLIST_TO_LAYOUT_GOAL.md",
        "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
    ]:
        path = REPO_ROOT / md_name
        text = path.read_text(encoding="utf-8")
        section = "\n".join(
            [
                "## Wave3 / DFF_BUF",
                "",
                f"- current_status: `{stage_status}`.",
                "- Verification hardening now computes topology-hash match, child geometry immutability, and source-level polarity audit instead of hardcoding them.",
                "- Review atlas has been regenerated as `WAVE3_DFF_BUF_REVIEW_ATLAS` with 8 dedicated review panels.",
                "- Clean GDS remained byte-identical during hardening.",
                f"- Recommended next stage: `{recommended_next_stage}`.",
                f"- Recommended next stage reason: `{recommended_next_stage_reason}`",
            ]
        )
        marker = "## Wave3 / DFF_BUF"
        if marker in text:
            start = text.index(marker)
            next_idx = text.find("\n## ", start + len(marker))
            if next_idx == -1:
                text = text[:start].rstrip() + "\n\n" + section + "\n"
            else:
                text = text[:start].rstrip() + "\n\n" + section + "\n\n" + text[next_idx + 1 :].lstrip("\n")
        else:
            text = text.rstrip() + "\n\n" + section + "\n"
        path.write_text(text, encoding="utf-8")


def main() -> None:
    print("hardening:start", flush=True)
    clean_gds = OUT_DIR / "DFF_BUF_clean.gds"
    pre_sha = _sha256(clean_gds)
    if pre_sha != EXPECTED_CLEAN_SHA:
        raise RuntimeError(f"Unexpected pre-hardening clean SHA: {pre_sha}")

    stage_report = _read_json(REPO_ROOT / "docs/Wave3_DFF_BUF_stage_report.json")
    physical_cell_name = stage_report["clean_gds_path"].split("/")[-1].replace("_clean.gds", "")
    if not physical_cell_name.startswith("DFF_BUF_FPDK45_"):
        physical_cell_name = stage_report["clean_gds_path"]  # fallback, replaced below
    physical_cell_name = _read_json(OUT_DIR / "Wave3_DFF_BUF_GENERATION_MANIFEST.json")["physical_cell_name"]
    net_contract = _read_json(REPO_ROOT / "docs/Wave3_DFF_BUF_net_contract.json")
    binding_rows = _binding_rows()
    instance_rows = _instance_table_rows()

    computed_hash, hash_match = _topology_hash_report(binding_rows, net_contract)
    print("hardening:topology_hash", flush=True)
    topology_negative = _topology_negative_test(binding_rows, net_contract)
    _write_json(REPO_ROOT / "docs/Wave3_DFF_BUF_topology_hash_negative_test.json", topology_negative)
    _write_text(
        REPO_ROOT / "docs/Wave3_DFF_BUF_topology_hash_negative_test.md",
        "\n".join(
            [
                "# Wave3 DFF_BUF Topology Hash Negative Test",
                "",
                f"- positive_hash: `{topology_negative['positive_hash']}`",
                f"- negative_hash: `{topology_negative['negative_hash']}`",
                f"- hash_changed: `{topology_negative['hash_changed']}`",
                f"- source_topology_hash_match_after_mutation: `{topology_negative['source_topology_hash_match_after_mutation']}`",
                f"- logical_physical_structural_match_after_mutation: `{topology_negative['logical_physical_structural_match_after_mutation']}`",
                f"- passed: `{topology_negative['passed']}`",
                "",
            ]
        )
        + "\n",
    )

    immutability_rows, child_geometry_modified_count, geometry_negative = _child_geometry_immutability(binding_rows, physical_cell_name)
    print("hardening:child_geometry", flush=True)
    _write_csv(OUT_DIR / "Wave3_DFF_BUF_child_geometry_immutability_report.csv", immutability_rows)
    _write_json(
        OUT_DIR / "Wave3_DFF_BUF_child_geometry_immutability_report.json",
        {
            "rows": immutability_rows,
            "child_geometry_modified_count": child_geometry_modified_count,
            "negative_test": geometry_negative,
        },
    )

    polarity_audit = _polarity_audit_from_instance_table(instance_rows)
    polarity_negative = _polarity_negative_test(instance_rows)
    _write_json(REPO_ROOT / "docs/Wave3_DFF_BUF_source_level_function_audit.json", polarity_audit)
    _write_text(
        REPO_ROOT / "docs/Wave3_DFF_BUF_source_level_function_audit.md",
        "\n".join(
            [
                "# Wave3 DFF_BUF Source-Level Function Audit",
                "",
                f"- source_level_functional_polarity_audit_passed: `{polarity_audit['source_level_functional_polarity_audit_passed']}`",
                f"- qint_to_qb_inverter_count: `{polarity_audit['qint_to_qb_inverter_count']}`",
                f"- qb_to_q_inverter_count: `{polarity_audit['qb_to_q_inverter_count']}`",
                f"- qint_to_q_inverter_count: `{polarity_audit['qint_to_q_inverter_count']}`",
                f"- final_q_same_polarity_as_dff_q: `{polarity_audit['final_q_same_polarity_as_dff_q']}`",
                f"- final_qb_inverted_from_dff_q: `{polarity_audit['final_qb_inverted_from_dff_q']}`",
                f"- d_has_no_parent_level_inverter: `{polarity_audit['d_has_no_parent_level_inverter']}`",
                f"- clk_has_no_parent_level_inverter: `{polarity_audit['clk_has_no_parent_level_inverter']}`",
                "",
            ]
        )
        + "\n",
    )
    _write_json(REPO_ROOT / "docs/Wave3_DFF_BUF_source_level_function_negative_test.json", polarity_negative)
    print("hardening:polarity", flush=True)

    endpoints_by_net, top_pin_map, source_trace = _load_endpoints(binding_rows, physical_cell_name)
    connectivity = verify_hierarchical_connectivity(
        gds_path=clean_gds,
        top_name=physical_cell_name,
        endpoints_by_net=endpoints_by_net,
        top_pin_bboxes=top_pin_map,
    )
    write_connectivity_outputs(
        report=connectivity,
        graph_json_path=OUT_DIR / "Wave3_DFF_BUF_physical_connectivity_graph.json",
        matrix_csv_path=OUT_DIR / "Wave3_DFF_BUF_physical_connectivity_matrix.csv",
        report_json_path=OUT_DIR / "Wave3_DFF_BUF_physical_connectivity_report.json",
        report_md_path=OUT_DIR / "Wave3_DFF_BUF_physical_connectivity_report.md",
    )
    namespace_report = verify_composite_pin_namespace(clean_gds, physical_cell_name, ["VDD", "VSS", "D", "Q", "QB", "CLK"])
    write_pin_namespace_outputs(
        report=namespace_report,
        csv_path=OUT_DIR / "Wave3_DFF_BUF_label_inventory.csv",
        report_json_path=OUT_DIR / "Wave3_DFF_BUF_pin_namespace_report.json",
        report_md_path=OUT_DIR / "Wave3_DFF_BUF_pin_namespace_report.md",
    )
    hierarchy = verify_composite_hierarchy_closure(clean_gds, physical_cell_name)
    write_composite_hierarchy_outputs(
        report=hierarchy,
        json_path=OUT_DIR / "Wave3_DFF_BUF_hierarchy_closure.json",
        md_path=OUT_DIR / "Wave3_DFF_BUF_hierarchy_closure.md",
        structure_csv_path=OUT_DIR / "Wave3_DFF_BUF_structure_inventory.csv",
        reference_csv_path=OUT_DIR / "Wave3_DFF_BUF_reference_matrix.csv",
    )
    hardening_drc_dir = OUT_DIR / "_hardening_drc_recheck"
    print("hardening:connectivity_namespace_hierarchy", flush=True)
    if hardening_drc_dir.exists():
        shutil.rmtree(hardening_drc_dir)
    hardening_drc_dir.mkdir(parents=True, exist_ok=True)
    drc = run_cell_drc(Path("/usr/bin/klayout"), REPO_ROOT / "technology/freepdk45/tech/freepdk45.lydrc", clean_gds, physical_cell_name, hardening_drc_dir)
    _write_csv(
        OUT_DIR / "Wave3_DFF_BUF_drc_category_matrix.csv",
        [{"category": name.strip("'"), "count": count} for name, count in sorted(drc["marker_categories"].items())] or [{"category": "TOTAL", "count": drc["marker_count"]}],
    )
    _write_json(
        OUT_DIR / "Wave3_DFF_BUF_drc_report.json",
        {
            "drc_marker_count": drc["marker_count"],
            "drc_passed": drc["drc_passed"],
            "marker_categories": drc["marker_categories"],
            "log_path": drc["log_path"],
            "lyrdb_path": drc["marker_report_path"],
        },
    )
    _write_text(
        OUT_DIR / "Wave3_DFF_BUF_drc_report.md",
        "\n".join(["# Wave3 DFF_BUF DRC Recheck", "", f"- drc_marker_count: `{drc['marker_count']}`", f"- drc_passed: `{drc['drc_passed']}`", ""]) + "\n",
    )
    shutil.copyfile(Path(drc["marker_report_path"]), OUT_DIR / "Wave3_DFF_BUF_drc.lyrdb")
    shutil.copyfile(Path(drc["log_path"]), OUT_DIR / "Wave3_DFF_BUF_drc.log")
    print("hardening:drc", flush=True)

    determinism = _read_json(OUT_DIR / "Wave3_DFF_BUF_deterministic_regeneration_report.json")
    deterministic_identity_preserved = determinism["deterministic_regeneration_verified"] and determinism["clean_gds_sha256_a"] == EXPECTED_CLEAN_SHA and determinism["clean_gds_sha256_b"] == EXPECTED_CLEAN_SHA

    actual_source_topology_hash_match = hash_match
    exact_child_binding_count = sum(1 for row in binding_rows if row["binding_status"] == "APPROVED_EXACT_BINDING")
    non_exact_child_binding_count = sum(1 for row in binding_rows if row["binding_status"] != "APPROVED_EXACT_BINDING")

    logical_physical_structural_match = _logical_structural_match(
        source_topology_hash_match=actual_source_topology_hash_match,
        connectivity=connectivity,
        namespace_report=namespace_report,
        hierarchy_report=hierarchy,
        binding_rows=binding_rows,
        expected_instance_order=["dff", "inv1", "inv2"],
        expected_child_types={"dff": "DFF", "inv1": "PINV", "inv2": "PINV"},
        child_geometry_modified_count=child_geometry_modified_count,
    )

    signal_routing_completed = (
        connectivity["physical_connectivity_verification_passed"]
        and connectivity["missing_expected_endpoint_count"] == 0
        and connectivity["unexpected_endpoint_count"] == 0
        and connectivity["unexpected_net_merge_count"] == 0
        and connectivity["floating_required_pin_count"] == 0
        and connectivity["power_signal_short_count"] == 0
    )
    machine_pass = (
        stage_report["source_commit_match"]
        and actual_source_topology_hash_match
        and exact_child_binding_count == 3
        and non_exact_child_binding_count == 0
        and child_geometry_modified_count == 0
        and stage_report["pin_access_planning_passed"]
        and stage_report["routing_architecture_has_no_same_layer_crossovers"]
        and signal_routing_completed
        and connectivity["physical_connectivity_verification_passed"]
        and logical_physical_structural_match
        and namespace_report["top_canonical_label_set_exact"]
        and namespace_report["internal_child_label_leakage_count"] == 0
        and hierarchy["reference_closure_passed"]
        and hierarchy["missing_reference_target_count"] == 0
        and hierarchy["reference_cycle_count"] == 0
        and drc["marker_count"] == 0
        and deterministic_identity_preserved
        and polarity_audit["source_level_functional_polarity_audit_passed"]
    )

    annotated_gds = OUT_DIR / "DFF_BUF_annotated.gds"
    atlas_inventory = _build_review_atlas(
        clean_gds=clean_gds,
        clean_top_name=physical_cell_name,
        annotated_gds=annotated_gds,
        annotated_top_name=physical_cell_name,
        binding_rows=binding_rows,
        source_trace=source_trace,
        route_plan=_read_json(OUT_DIR / "Wave3_DFF_BUF_dff_route_plan.json"),
        top_pin_map=top_pin_map,
        output_gds=OUT_DIR / "DFF_BUF_review_atlas.gds",
    )
    _write_json(OUT_DIR / "Wave3_DFF_BUF_review_atlas_inventory.json", atlas_inventory)
    print("hardening:atlas", flush=True)

    if machine_pass:
        human_review_required = True
        can_enter = False
        recommended_next_stage = "Wave3 / DFF_BUF human visual review"
        recommended_next_stage_reason = "Machine verification hardened successfully. The candidate now requires focused human visual review before any reusable or higher-wave claim."
        stage_status = "MACHINE_VERIFIED_CANDIDATE_PENDING_HUMAN_REVIEW"
    else:
        human_review_required = False
        can_enter = False
        recommended_next_stage = "Wave3 / DFF_BUF repair"
        recommended_next_stage_reason = "Hardening exposed a machine-gate failure. Repair is required before human review."
        stage_status = "QUALIFICATION_FAILED_MACHINE"

    report = dict(stage_report)
    report.update(
        {
            "canonical_topology_hash": computed_hash,
            "source_topology_hash_match": actual_source_topology_hash_match,
            "child_geometry_modified_count": child_geometry_modified_count,
            "signal_routing_completed": signal_routing_completed,
            "expected_net_count": connectivity["expected_net_count"],
            "actual_net_component_count": connectivity["actual_net_component_count"],
            "unexpected_net_merge_count": connectivity["unexpected_net_merge_count"],
            "missing_expected_endpoint_count": connectivity["missing_expected_endpoint_count"],
            "unexpected_endpoint_count": connectivity["unexpected_endpoint_count"],
            "floating_required_pin_count": connectivity["floating_required_pin_count"],
            "power_signal_short_count": connectivity["power_signal_short_count"],
            "vdd_vss_short_present": connectivity["vdd_vss_short_present"],
            "physical_connectivity_verification_passed": connectivity["physical_connectivity_verification_passed"],
            "logical_physical_structural_match": logical_physical_structural_match,
            "hierarchy_closure_passed": hierarchy["reference_closure_passed"],
            "missing_reference_target_count": hierarchy["missing_reference_target_count"],
            "reference_cycle_count": hierarchy["reference_cycle_count"],
            "drc_marker_count": drc["marker_count"],
            "drc_passed": drc["drc_passed"],
            "deterministic_regeneration_verified": deterministic_identity_preserved,
            "source_level_functional_polarity_audit_passed": polarity_audit["source_level_functional_polarity_audit_passed"],
            "can_claim_dff_buf_machine_verified": machine_pass,
            "can_claim_dff_buf_human_verified": False,
            "can_claim_dff_buf_reusable": False,
            "human_review_required": human_review_required,
            "can_enter_next_stage_before_human_review": can_enter,
            "recommended_next_stage": recommended_next_stage,
            "recommended_next_stage_reason": recommended_next_stage_reason,
        }
    )
    _write_json(REPO_ROOT / "docs/Wave3_DFF_BUF_stage_report.json", report)
    _write_text(REPO_ROOT / "docs/Wave3_DFF_BUF_stage_report.md", "\n".join([f"- {k}: `{v}`" for k, v in report.items() if k != "human_review_required_items"]) + "\n")

    hardening_report = {
        "pre_hardening_clean_gds_sha256": pre_sha,
        "post_hardening_clean_gds_sha256": _sha256(clean_gds),
        "clean_gds_geometry_unchanged": _sha256(clean_gds) == pre_sha == EXPECTED_CLEAN_SHA,
        "topology_hash_check_is_computed_not_hardcoded": True,
        "topology_hash_positive_test_passed": actual_source_topology_hash_match,
        "topology_hash_negative_test_passed": topology_negative["passed"],
        "child_geometry_modified_count_is_computed": True,
        "child_geometry_modified_count": child_geometry_modified_count,
        "child_geometry_negative_test_passed": geometry_negative["passed"],
        "polarity_audit_is_computed_not_hardcoded": True,
        "source_level_functional_polarity_audit_passed": polarity_audit["source_level_functional_polarity_audit_passed"],
        "polarity_negative_test_passed": polarity_negative["passed"],
        "machine_pass_includes_topology_hash_match": True,
        "machine_pass_includes_child_geometry_immutability": True,
        "machine_pass_includes_signal_routing_completed": True,
        "machine_pass_includes_structural_match": True,
        "failed_machine_gate_blocks_human_review": True,
        "failed_machine_gate_blocks_next_stage": True,
        "review_atlas_top_cell": atlas_inventory["atlas_top_cell"],
        "review_atlas_panel_count": atlas_inventory["panel_count"],
        "review_atlas_panel_names": atlas_inventory["panel_names"],
        "atlas_missing_reference_target_count": atlas_inventory["missing_reference_target_count"],
        "atlas_reference_cycle_count": atlas_inventory["reference_cycle_count"],
        "expected_net_count": connectivity["expected_net_count"],
        "actual_net_component_count": connectivity["actual_net_component_count"],
        "unexpected_net_merge_count": connectivity["unexpected_net_merge_count"],
        "missing_expected_endpoint_count": connectivity["missing_expected_endpoint_count"],
        "unexpected_endpoint_count": connectivity["unexpected_endpoint_count"],
        "physical_connectivity_verification_passed": connectivity["physical_connectivity_verification_passed"],
        "hierarchy_closure_passed": hierarchy["reference_closure_passed"],
        "drc_marker_count": drc["marker_count"],
        "drc_passed": drc["drc_passed"],
        "deterministic_identity_preserved": deterministic_identity_preserved,
        "can_claim_dff_buf_machine_verified": machine_pass,
        "can_claim_dff_buf_human_verified": False,
        "can_claim_dff_buf_reusable": False,
        "human_review_required": human_review_required,
        "can_enter_next_stage_before_human_review": can_enter,
        "recommended_next_stage": recommended_next_stage,
        "recommended_next_stage_reason": recommended_next_stage_reason,
    }
    _write_json(REPO_ROOT / "docs/Wave3_DFF_BUF_verification_hardening_report.json", hardening_report)
    _write_text(REPO_ROOT / "docs/Wave3_DFF_BUF_verification_hardening_report.md", "\n".join([f"- {k}: `{v}`" for k, v in hardening_report.items()]) + "\n")

    _update_ledgers(stage_status, recommended_next_stage, recommended_next_stage_reason)
    print("hardening:done", flush=True)


if __name__ == "__main__":
    main()
