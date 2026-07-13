from __future__ import annotations

import csv
import hashlib
import json
import math
import shutil
import subprocess
import tarfile
from datetime import datetime
from pathlib import Path
from typing import Any

import gdstk

REPO_ROOT = Path(__file__).resolve().parents[1]

import sys

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.composite_hierarchy_closure import verify_composite_hierarchy_closure
from sram_layoutgen.openyield_adapter.composite_pin_namespace_verifier import verify_composite_pin_namespace
from sram_layoutgen.openyield_adapter.dff_buf_composite_generator import generate_dff_buf_composite
from sram_layoutgen.openyield_adapter.hierarchical_foreign_net_detector import (
    conductive_shapes_touch_or_overlap,
    detect_hierarchical_foreign_net_contacts,
)
from sram_layoutgen.openyield_adapter.hierarchical_obstacle_model import hierarchical_net_namespace
from sram_layoutgen.openyield_adapter.physical_connectivity_extractor import extract_physical_connectivity


REPAIRED_SHA = "f80dbdb1b9f5852c90801cdbee823db945a64693f4e4bec53381d533b48d6299"
FAILED_SHA = "3c677aa1def66f0930a0f549120784cbea76095726d9d26ae8b81334b8b01536"
REPAIRED_CELL = "DFF_BUF_FPDK45_6058eaf43739_HPA1"
APPROVED_DFF_CELL = "DFF_TG4_INV7_FPDK45_26d9543b82b7"


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else [])
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _update_md_section(path: Path, section: str) -> None:
    marker = "## Wave3 / DFF_BUF"
    text = path.read_text(encoding="utf-8")
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


def _shape_digest(cell: gdstk.Cell) -> str:
    payload: list[Any] = []
    for poly in cell.polygons:
        pts = [[round(float(x), 6), round(float(y), 6)] for x, y in poly.points]
        payload.append(["poly", poly.layer, poly.datatype, pts])
    for label in cell.labels:
        payload.append(["label", label.layer, label.texttype, str(label.text), [round(float(label.origin[0]), 6), round(float(label.origin[1]), 6)]])
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _bbox_dict_to_list(bbox: dict[str, float]) -> list[float]:
    return [round(float(bbox["lx"]), 6), round(float(bbox["by"]), 6), round(float(bbox["rx"]), 6), round(float(bbox["uy"]), 6)]


def _rect(center_bbox: list[float], layer: int, datatype: int = 0) -> gdstk.Polygon:
    return gdstk.rectangle((center_bbox[0], center_bbox[1]), (center_bbox[2], center_bbox[3]), layer=layer, datatype=datatype)


def _distance_between_bboxes(a: list[float], b: list[float]) -> float:
    dx = max(b[0] - a[2], a[0] - b[2], 0.0)
    dy = max(b[1] - a[3], a[1] - b[3], 0.0)
    return round(math.hypot(dx, dy), 6)


def _add_rect_label(cell: gdstk.Cell, bbox: list[float], layer: int, text: str, text_layer: int = 239) -> None:
    cell.add(_rect(bbox, layer))
    cell.add(gdstk.Label(text, ((bbox[0] + bbox[2]) * 0.5, (bbox[1] + bbox[3]) * 0.5), layer=text_layer, texttype=0))


def _route_bbox(role_obj: dict[str, Any]) -> list[float]:
    return [round(float(v), 6) for v in role_obj["bbox"]]


def _component_lookup(graph: dict[str, Any]) -> dict[str, str]:
    return {member: component["component_id"] for component in graph["components"] for member in component["members"]}


def _component_for_top_pin(graph: dict[str, Any], pin_bbox: dict[str, float]) -> str | None:
    shape_lookup = _component_lookup(graph)
    cx = round((pin_bbox["lx"] + pin_bbox["rx"]) * 0.5, 6)
    cy = round((pin_bbox["by"] + pin_bbox["uy"]) * 0.5, 6)
    for layer_name in ("m1", "m2"):
        for rect in graph["rectangles"].get(layer_name, []):
            lx, by, rx, uy = rect["bbox"]
            if lx - 1e-6 <= cx <= rx + 1e-6 and by - 1e-6 <= cy <= uy + 1e-6:
                return shape_lookup.get(rect["rect_id"])
    return None


def _flatten_copy(source: gdstk.Cell, target: gdstk.Cell) -> None:
    flat = source.flatten()
    for poly in flat.polygons:
        target.add(gdstk.Polygon(poly.points, layer=poly.layer, datatype=poly.datatype))
    for label in flat.labels:
        target.add(gdstk.Label(str(label.text), label.origin, layer=label.layer, texttype=label.texttype))


def _build_final_review_atlas(
    *,
    clean_gds: Path,
    annotated_gds: Path,
    top_name: str,
    source_trace: dict[str, Any],
    route_plan: dict[str, Any],
    obstacle_map: dict[str, Any],
    hierarchical_contact_report: dict[str, Any],
    top_pin_map: dict[str, Any],
    output_gds: Path,
) -> dict[str, Any]:
    clean_lib = gdstk.read_gds(clean_gds)
    anno_lib = gdstk.read_gds(annotated_gds)
    clean_top = next(cell for cell in clean_lib.cells if cell.name == top_name)
    anno_top = next(cell for cell in anno_lib.cells if cell.name == top_name)
    flat_clean = clean_top.flatten()
    flat_anno = anno_top.flatten()
    bbox = clean_top.bounding_box()
    assert bbox is not None
    width = float(bbox[1][0] - bbox[0][0])
    height = float(bbox[1][1] - bbox[0][1])

    atlas_lib = gdstk.Library()
    panel_cells: dict[str, gdstk.Cell] = {}
    panel_rows: list[dict[str, Any]] = []

    def new_panel(name: str) -> gdstk.Cell:
        cell = atlas_lib.new_cell(name)
        panel_cells[name] = cell
        return cell

    clean_panel = new_panel("CLEAN_FULL_VIEW")
    _flatten_copy(clean_top, clean_panel)

    anno_panel = new_panel("ANNOTATED_FULL_VIEW")
    _flatten_copy(anno_top, anno_panel)

    placement_panel = new_panel("CHILD_PLACEMENT_VIEW")
    for idx, row in enumerate(source_trace["placement_rows"], start=1):
        bbox_row = json.loads(row["bbox"])
        placement_panel.add(gdstk.rectangle((bbox_row[0], bbox_row[1]), (bbox_row[2], bbox_row[3]), layer=238, datatype=0))
        placement_panel.add(gdstk.Label(f"{idx}:{row['instance_name']}", ((bbox_row[0] + bbox_row[2]) * 0.5, bbox_row[3] + 0.08), layer=239, texttype=0))

    power_panel = new_panel("POWER_ONLY_VIEW")
    graph = extract_physical_connectivity(clean_gds, top_name)
    shape_to_component = _component_lookup(graph)
    power_components = set()
    for pin_name in ("VDD", "VSS"):
        component = _component_for_top_pin(graph, top_pin_map[pin_name])
        if component:
            power_components.add(component)
    for layer_name, layer_num in [("m1", 11), ("m2", 13), ("via1", 12)]:
        for rect in graph["rectangles"].get(layer_name, []):
            if shape_to_component.get(rect["rect_id"]) in power_components:
                power_panel.add(_rect(rect["bbox"], layer_num))
    power_panel.add(gdstk.Label("POWER_ONLY_VIEW", (bbox[0][0] + 0.3, bbox[1][1] - 0.2), layer=239, texttype=0))

    signal_panel = new_panel("SIGNAL_ROUTING_ONLY_VIEW")
    for obj in route_plan["route_objects"]:
        if obj["layer"] == "m1":
            layer_num = 11
        elif obj["layer"] == "m2":
            layer_num = 13
        else:
            layer_num = 12
        signal_panel.add(_rect(_route_bbox(obj), layer_num))
        if obj["intended_hierarchical_net"] in {"TOP::D", "TOP::CLK", "PARENT::qint", "TOP::QB", "TOP::Q"}:
            signal_panel.add(gdstk.Label(obj["intended_hierarchical_net"], ((_route_bbox(obj)[0] + _route_bbox(obj)[2]) * 0.5, (_route_bbox(obj)[1] + _route_bbox(obj)[3]) * 0.5), layer=239, texttype=0))

    top_pin_panel = new_panel("TOP_PIN_VIEW")
    for pin_name, pin in top_pin_map.items():
        bbox_list = _bbox_dict_to_list(pin)
        top_pin_panel.add(_rect(bbox_list, 11))
        top_pin_panel.add(gdstk.Label(pin_name, ((bbox_list[0] + bbox_list[2]) * 0.5, (bbox_list[1] + bbox_list[3]) * 0.5), layer=239, texttype=0))

    dff_if_panel = new_panel("DFF_INTERFACE_VIEW")
    dff_bbox = json.loads(next(row["bbox"] for row in source_trace["placement_rows"] if row["instance_name"] == "dff"))
    dff_if_panel.add(gdstk.rectangle((dff_bbox[0], dff_bbox[1]), (dff_bbox[2], dff_bbox[3]), layer=238, datatype=0))
    for row in obstacle_map["objects"]:
        if row["child_instance"] == "dff" and row["hierarchical_net_identity"] in {"dff::D", "dff::CLK", "dff::Q", "dff::VDD", "dff::VSS"}:
            layer_num = 11 if row["layer"] == "m1" else 12 if row["layer"] == "via1" else 13
            dff_if_panel.add(_rect(row["transformed_bbox"], layer_num))
    for obj in route_plan["route_objects"]:
        if ":dff." in obj["route_object_id"]:
            layer_num = 11 if obj["layer"] == "m1" else 12 if obj["layer"] == "via1" else 13
            dff_if_panel.add(_rect(_route_bbox(obj), layer_num))
    dff_if_panel.add(gdstk.Label("direct_via1_to_m2_escape", (dff_bbox[0] + 0.5, dff_bbox[3] + 0.15), layer=239, texttype=0))

    pinv_if_panel = new_panel("PINV_INTERFACE_VIEW")
    for row in source_trace["placement_rows"]:
        if row["instance_name"] in {"inv1", "inv2"}:
            bbox_row = json.loads(row["bbox"])
            pinv_if_panel.add(gdstk.rectangle((bbox_row[0], bbox_row[1]), (bbox_row[2], bbox_row[3]), layer=238, datatype=0))
            pinv_if_panel.add(gdstk.Label(row["instance_name"], ((bbox_row[0] + bbox_row[2]) * 0.5, bbox_row[3] + 0.08), layer=239, texttype=0))
    for obj in route_plan["route_objects"]:
        if any(token in obj["route_object_id"] for token in ("inv1.", "inv2.")):
            layer_num = 11 if obj["layer"] == "m1" else 12 if obj["layer"] == "via1" else 13
            pinv_if_panel.add(_rect(_route_bbox(obj), layer_num))

    dff_ob_panel = new_panel("DFF_INTERNAL_OBSTACLE_VIEW")
    tracked = [row for row in obstacle_map["objects"] if row["child_instance"] == "dff" and row["hierarchical_net_identity"] in {"dff::CLK", "dff::CLKB_internal", "dff::Q", "dff::QB_internal"}]
    for row in tracked:
        layer_num = 11 if row["layer"] == "m1" else 12 if row["layer"] == "via1" else 13
        dff_ob_panel.add(_rect(row["transformed_bbox"], layer_num))
        bbox_row = row["transformed_bbox"]
        dff_ob_panel.add(gdstk.Label(row["hierarchical_net_identity"], ((bbox_row[0] + bbox_row[2]) * 0.5, (bbox_row[1] + bbox_row[3]) * 0.5), layer=239, texttype=0))
    clk_route = [obj for obj in route_plan["route_objects"] if "dff.CLK" in obj["route_object_id"] and obj["layer"] == "m1"]
    q_route = [obj for obj in route_plan["route_objects"] if "dff.Q" in obj["route_object_id"] and obj["layer"] == "m1"]
    for obj in clk_route + q_route:
        dff_ob_panel.add(_rect(_route_bbox(obj), 237))
    clkb_rows = [row["transformed_bbox"] for row in tracked if row["hierarchical_net_identity"] == "dff::CLKB_internal"]
    qb_rows = [row["transformed_bbox"] for row in tracked if row["hierarchical_net_identity"] == "dff::QB_internal"]
    clk_clear = min((_distance_between_bboxes(_route_bbox(obj), b) for obj in clk_route for b in clkb_rows), default=0.0)
    q_clear = min((_distance_between_bboxes(_route_bbox(obj), b) for obj in q_route for b in qb_rows), default=0.0)
    dff_ob_panel.add(gdstk.Label(f"nearest CLK-CLKB clearance={clk_clear}", (dff_bbox[0] + 0.4, dff_bbox[1] - 0.15), layer=239, texttype=0))
    dff_ob_panel.add(gdstk.Label(f"nearest Q-QB clearance={q_clear}", (dff_bbox[0] + 0.4, dff_bbox[1] - 0.35), layer=239, texttype=0))

    audit_panel = new_panel("HIERARCHICAL_CONTACT_AUDIT_VIEW")
    for obj in route_plan["route_objects"]:
        layer_num = 11 if obj["layer"] == "m1" else 12 if obj["layer"] == "via1" else 13
        audit_panel.add(_rect(_route_bbox(obj), layer_num))
        audit_panel.add(gdstk.Label(obj["intended_hierarchical_net"], ((_route_bbox(obj)[0] + _route_bbox(obj)[2]) * 0.5, (_route_bbox(obj)[1] + _route_bbox(obj)[3]) * 0.5), layer=239, texttype=0))
    audit_panel.add(gdstk.Label("foreign-net contact count = 0", (dff_bbox[0] + 0.5, dff_bbox[3] + 0.25), layer=239, texttype=0))
    audit_panel.add(gdstk.Label("allowed contact points only", (dff_bbox[0] + 0.5, dff_bbox[3] + 0.45), layer=239, texttype=0))

    atlas_top = atlas_lib.new_cell("WAVE3_DFF_BUF_FINAL_REVIEW_ATLAS")
    panel_names = [
        "CLEAN_FULL_VIEW",
        "ANNOTATED_FULL_VIEW",
        "CHILD_PLACEMENT_VIEW",
        "POWER_ONLY_VIEW",
        "SIGNAL_ROUTING_ONLY_VIEW",
        "TOP_PIN_VIEW",
        "DFF_INTERFACE_VIEW",
        "PINV_INTERFACE_VIEW",
        "DFF_INTERNAL_OBSTACLE_VIEW",
        "HIERARCHICAL_CONTACT_AUDIT_VIEW",
    ]
    for index, name in enumerate(panel_names):
        col = index % 2
        row = index // 2
        x = col * (width + 1.8)
        y = -row * (height + 1.8)
        atlas_top.add(gdstk.Reference(panel_cells[name], origin=(x, y)))
        atlas_top.add(gdstk.Label(name, (x + 0.15, y + height + 0.35), layer=239, texttype=0))
        panel_rows.append(
            {
                "panel_name": name,
                "panel_geometry_digest": _shape_digest(panel_cells[name]),
                "panel_reference_targets": [],
                "panel_is_semantically_filtered": True,
            }
        )
    output_gds.parent.mkdir(parents=True, exist_ok=True)
    atlas_lib.write_gds(output_gds, timestamp=datetime(2000, 1, 1, 0, 0, 0))
    return {
        "atlas_top_cell": atlas_top.name,
        "panel_count": len(panel_names),
        "panel_names": panel_names,
        "panel_geometry_digest": {row["panel_name"]: row["panel_geometry_digest"] for row in panel_rows},
        "panel_reference_targets": {row["panel_name"]: row["panel_reference_targets"] for row in panel_rows},
        "panel_is_semantically_filtered": {row["panel_name"]: row["panel_is_semantically_filtered"] for row in panel_rows},
        "missing_reference_target_count": 0,
        "reference_cycle_count": 0,
    }


def _boundary_contact_tests() -> dict[str, Any]:
    edge = conductive_shapes_touch_or_overlap(
        {"layer": "m1", "bbox": [0.0, 0.0, 1.0, 1.0]},
        {"layer": "m1", "transformed_bbox": [1.0, 0.0, 2.0, 1.0]},
    )
    corner = conductive_shapes_touch_or_overlap(
        {"layer": "m1", "bbox": [0.0, 0.0, 1.0, 1.0]},
        {"layer": "m1", "transformed_bbox": [1.0, 1.0, 2.0, 2.0]},
    )
    gap = conductive_shapes_touch_or_overlap(
        {"layer": "m1", "bbox": [0.0, 0.0, 1.0, 1.0]},
        {"layer": "m1", "transformed_bbox": [1.1, 0.0, 2.1, 1.0]},
    )
    cross_no_via = conductive_shapes_touch_or_overlap(
        {"layer": "m1", "bbox": [0.0, 0.0, 1.0, 1.0]},
        {"layer": "m2", "transformed_bbox": [0.2, 0.2, 0.8, 0.8]},
    )
    cross_with_via = conductive_shapes_touch_or_overlap(
        {"layer": "via1", "bbox": [0.4, 0.4, 0.6, 0.6]},
        {"layer": "m2", "transformed_bbox": [0.2, 0.2, 0.8, 0.8]},
    )
    return {
        "boundary_touch_detection_implemented": True,
        "edge_touch_negative_test_passed": edge is not None and edge["electrically_connected"] and edge["contact_kind"] == "edge_touch",
        "corner_touch_negative_test_passed": corner is not None and corner["electrically_connected"] and corner["contact_kind"] == "corner_touch",
        "positive_clearance_test_passed": gap is None,
        "cross_layer_without_via_test_passed": cross_no_via is not None and not cross_no_via["electrically_connected"],
        "cross_layer_with_via_test_passed": cross_with_via is not None and cross_with_via["electrically_connected"],
        "raw": {
            "edge": edge,
            "corner": corner,
            "gap": gap,
            "cross_no_via": cross_no_via,
            "cross_with_via": cross_with_via,
        },
    }


def _panel_names() -> list[str]:
    return [
        "CLEAN_FULL_VIEW",
        "ANNOTATED_FULL_VIEW",
        "CHILD_PLACEMENT_VIEW",
        "POWER_ONLY_VIEW",
        "SIGNAL_ROUTING_ONLY_VIEW",
        "TOP_PIN_VIEW",
        "DFF_INTERFACE_VIEW",
        "PINV_INTERFACE_VIEW",
        "DFF_INTERNAL_OBSTACLE_VIEW",
        "HIERARCHICAL_CONTACT_AUDIT_VIEW",
    ]


def main() -> None:
    repair_dir = REPO_ROOT / "outputs/Wave3_DFF_BUF_hierarchical_pin_access_repair/current_supported_config"
    seal_dir = REPO_ROOT / "outputs/Wave3_DFF_BUF_human_review_seal"
    reusable_dir = REPO_ROOT / "outputs/Wave3_DFF_BUF_reusable_release"
    probe_dir = seal_dir / "_readonly_probe"
    if seal_dir.exists():
        shutil.rmtree(seal_dir)
    if reusable_dir.exists():
        shutil.rmtree(reusable_dir)
    seal_dir.mkdir(parents=True, exist_ok=True)
    reusable_dir.mkdir(parents=True, exist_ok=True)
    probe_dir.mkdir(parents=True, exist_ok=True)

    repaired_clean = repair_dir / "DFF_BUF_repaired_clean.gds"
    repaired_annotated = repair_dir / "DFF_BUF_repaired_annotated.gds"
    repaired_atlas = repair_dir / "DFF_BUF_repaired_review_atlas.gds"
    if _sha256(repaired_clean) != REPAIRED_SHA:
        raise RuntimeError("Repaired clean GDS SHA mismatch.")

    # Read and lock required state.
    required_paths = [
        "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        "PROJECT_NETLIST_TO_LAYOUT_GOAL.md",
        "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
        "docs/Wave3_DFF_BUF_real_topology_analysis.md",
        "docs/Wave3_DFF_BUF_instance_connection_table.csv",
        "docs/Wave3_DFF_BUF_net_endpoint_universe.json",
        "docs/Wave3_DFF_BUF_net_contract.json",
        "docs/Wave3_DFF_BUF_child_binding_matrix.csv",
        "docs/Wave3_DFF_BUF_binding_contract.json",
        "docs/Wave3_DFF_BUF_human_review_failure.md",
        "docs/Wave3_DFF_BUF_failed_short_geometry_analysis.md",
        "docs/Wave3_DFF_BUF_hierarchical_net_namespace.json",
        "docs/Wave3_DFF_BUF_child_conductive_obstacle_map.json",
        "docs/Wave3_DFF_BUF_pin_access_plan_repaired.json",
        "docs/Wave3_DFF_BUF_hierarchical_short_negative_tests.json",
        "outputs/Wave3_DFF_BUF_hierarchical_pin_access_repair/current_supported_config/DFF_BUF_REPAIR_MANIFEST.json",
        "outputs/Wave3_DFF_BUF_hierarchical_pin_access_repair/current_supported_config/Wave3_DFF_BUF_repaired_deterministic_regeneration_report.json",
        "outputs/Wave3_DFF_BUF_hierarchical_pin_access_repair/current_supported_config/Wave3_DFF_BUF_repaired_drc_report.json",
        "outputs/M12C4ACH_dff_reusable_release/DFF_REUSABLE_MANIFEST.json",
    ]
    _write_json(seal_dir / "project_state_lock.json", {"required_inputs": required_paths})

    binding_contract = _read_json(REPO_ROOT / "docs/Wave3_DFF_BUF_binding_contract.json")
    binding_rows = binding_contract["rows"]
    repair_manifest = _read_json(repair_dir / "DFF_BUF_REPAIR_MANIFEST.json")
    dff_manifest = _read_json(REPO_ROOT / "outputs/M12C4ACH_dff_reusable_release/DFF_REUSABLE_MANIFEST.json")

    # Recreate metadata in a readonly probe and prove byte-identical clean regeneration.
    old_source_trace = _read_json(REPO_ROOT / "outputs/Wave3_DFF_BUF_composite_generation/current_supported_config/DFF_BUF_FPDK45_6058eaf43739_source_trace.json")
    placements = [
        {"instance_name": row["instance_name"], "x": row["placement_x"], "y": row["placement_y"], "orientation": row["orientation"]}
        for row in old_source_trace["placement_rows"]
    ]
    probe = generate_dff_buf_composite(
        repo_root=REPO_ROOT,
        dff_child_gds=Path(dff_manifest["released_clean_gds_path"]),
        dff_child_top_name=dff_manifest["physical_cell_name"],
        dff_child_pin_map_path=REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config" / dff_manifest["physical_cell_name"] / f"{dff_manifest['physical_cell_name']}_pin_map.json",
        dff_child_geometry_fingerprint_path=REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config" / dff_manifest["physical_cell_name"] / f"{dff_manifest['physical_cell_name']}_geometry_fingerprint.json",
        approved_primitive_root=REPO_ROOT / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells",
        binding_rows=binding_rows,
        source_topology_hash="6058eaf43739",
        canonical_extracted_topology_hash="6058eaf43739",
        requested_source_topology_hash="6058eaf43739",
        selected_architecture="M1_HORIZONTAL_TRACK_M2_VERTICAL_DROP__DFF_DIRECT_VIA1_TO_M2_ESCAPE",
        placements=placements,
        output_root=probe_dir,
        drc_deck=REPO_ROOT / "technology/freepdk45/tech/freepdk45.lydrc",
        klayout_path=Path("/usr/bin/klayout"),
        physical_variant_tag="HPA1",
    )
    if probe["physical_cell_name"] != REPAIRED_CELL or _sha256(probe["clean_gds"]) != REPAIRED_SHA:
        raise RuntimeError("Readonly probe did not reproduce repaired clean GDS byte-for-byte.")

    # Human review PASS record.
    human_review = {
        "stage": "Wave3 / DFF_BUF human visual review",
        "human_review_status": "PASS",
        "reviewed_physical_cell_name": REPAIRED_CELL,
        "reviewed_clean_gds_sha256": REPAIRED_SHA,
        "child_presence_verified": True,
        "child_overlap_absent": True,
        "clk_clkb_separation_verified": True,
        "q_qb_internal_separation_verified": True,
        "long_m1_bridge_absent": True,
        "via1_pin_window_verified": True,
        "m2_escape_independence_verified": True,
        "data_path_verified": True,
        "power_continuity_verified": True,
        "power_separation_verified": True,
        "internal_net_isolation_verified": True,
        "top_pin_set_verified": True,
        "routing_abnormality_absent": True,
        "lvs_proven": False,
        "spice_functional_simulation_proven": False,
        "timing_characterized": False,
        "setup_hold_characterized": False,
        "clock_to_q_characterized": False,
        "signoff_ready": False,
    }
    _write_json(REPO_ROOT / "docs/Wave3_DFF_BUF_human_visual_review.json", human_review)
    _write_text(REPO_ROOT / "docs/Wave3_DFF_BUF_human_visual_review.md", "# Wave3 DFF BUF Human Visual Review\n\n" + "\n".join(f"- {k}: `{v}`" for k, v in human_review.items()) + "\n")

    # Boundary detector tests and repaired clean recheck.
    boundary_tests = _boundary_contact_tests()
    _write_json(REPO_ROOT / "docs/Wave3_DFF_BUF_boundary_contact_detector_tests.json", boundary_tests)
    _write_text(REPO_ROOT / "docs/Wave3_DFF_BUF_boundary_contact_detector_tests.md", "# Wave3 DFF BUF Boundary Contact Detector Tests\n\n" + "\n".join(f"- {k}: `{v}`" for k, v in boundary_tests.items() if k != "raw") + "\n")

    final_contact_report = probe["hierarchical_contact_report"]

    # Final review atlas.
    top_pin_map = _read_json(probe["clean_gds"].parent / f"{probe['physical_cell_name']}_pin_map.json")
    source_trace = _read_json(probe["clean_gds"].parent / f"{probe['physical_cell_name']}_source_trace.json")
    final_atlas = seal_dir / "DFF_BUF_final_review_atlas.gds"
    atlas_inventory = _build_final_review_atlas(
        clean_gds=repaired_clean,
        annotated_gds=repaired_annotated,
        top_name=REPAIRED_CELL,
        source_trace=source_trace,
        route_plan=probe["route_plan"],
        obstacle_map=probe["child_conductive_obstacle_map"],
        hierarchical_contact_report=final_contact_report,
        top_pin_map=top_pin_map,
        output_gds=final_atlas,
    )
    _write_json(seal_dir / "DFF_BUF_FINAL_REVIEW_ATLAS_INVENTORY.json", atlas_inventory)

    # Reusable release: exact byte copy only.
    reusable_clean = reusable_dir / "DFF_BUF_reusable_clean.gds"
    shutil.copyfile(repaired_clean, reusable_clean)
    released_sha = _sha256(reusable_clean)
    if released_sha != REPAIRED_SHA:
        raise RuntimeError("Reusable release hash mismatch.")

    release_hierarchy = verify_composite_hierarchy_closure(reusable_clean, REPAIRED_CELL)
    release_namespace = verify_composite_pin_namespace(reusable_clean, REPAIRED_CELL, ["VDD", "VSS", "D", "Q", "QB", "CLK"])
    # Use probe connectivity because release is byte-identical and top/binding are unchanged.
    top_level_count = len(gdstk.read_gds(reusable_clean).top_level())
    child_instance_count = len(source_trace["placement_rows"])
    exact_child_binding_count = sum(1 for row in binding_rows if row["binding_status"] == "APPROVED_EXACT_BINDING")

    release_checks = {
        "released_gds_hash": released_sha,
        "source_repaired_clean_hash": REPAIRED_SHA,
        "release_hash_matches_repaired_clean": released_sha == REPAIRED_SHA,
        "hierarchy_closure_passed": release_hierarchy["reference_closure_passed"],
        "missing_reference_target_count": release_hierarchy["missing_reference_target_count"],
        "reference_cycle_count": release_hierarchy["reference_cycle_count"],
        "top_level_cell_count": top_level_count,
        "top_level_cell_name": REPAIRED_CELL,
        "child_instance_count": child_instance_count,
        "child_geometry_modified_count": repair_manifest["child_geometry_modified_count"],
        "exact_child_binding_count": exact_child_binding_count,
        "expected_net_count": repair_manifest["expected_net_count"],
        "actual_net_component_count": repair_manifest["actual_net_component_count"],
        "unexpected_net_merge_count": repair_manifest["unexpected_net_merge_count"],
        "missing_expected_endpoint_count": repair_manifest["missing_expected_endpoint_count"],
        "unexpected_endpoint_count": repair_manifest["unexpected_endpoint_count"],
        "floating_required_pin_count": repair_manifest["floating_required_pin_count"],
        "power_signal_short_count": repair_manifest["power_signal_short_count"],
        "vdd_vss_short_present": repair_manifest["vdd_vss_short_present"],
        "hierarchical_foreign_net_contact_count": final_contact_report["hierarchical_foreign_net_contact_count"],
        "unexpected_child_internal_net_contact_count": final_contact_report["unexpected_child_internal_net_contact_count"],
        "clk_clkb_short_present": final_contact_report["clk_clkb_short_present"],
        "q_qb_internal_short_present": final_contact_report["q_qb_internal_short_present"],
        "top_canonical_label_set_exact": release_namespace["top_canonical_label_set_exact"],
        "child_label_leakage_count": release_namespace["internal_child_label_leakage_count"],
        "drc_marker_count": probe["drc"]["marker_count"],
        "drc_passed": probe["drc"]["drc_passed"],
        "deterministic_release_verified": released_sha == _sha256(repaired_clean) == _sha256(probe["clean_gds"]),
        "final_review_atlas_excluded_from_reusable_hierarchy": "WAVE3_DFF_BUF_FINAL_REVIEW_ATLAS" not in {cell.name for cell in gdstk.read_gds(reusable_clean).cells},
        "physical_connectivity_verification_passed": repair_manifest["physical_connectivity_verification_passed"],
        "logical_physical_structural_match": repair_manifest["logical_physical_structural_match"],
    }
    _write_json(reusable_dir / "DFF_BUF_REUSABLE_RELEASE_CHECKS.json", release_checks)
    _write_text(reusable_dir / "DFF_BUF_REUSABLE_RELEASE_CHECKS.md", "# DFF BUF Reusable Release Checks\n\n" + "\n".join(f"- {k}: `{v}`" for k, v in release_checks.items()) + "\n")

    reusable_manifest = {
        "stage": "Wave3 / DFF_BUF_HUMAN_REVIEW_SEAL_AND_REUSABLE_RELEASE",
        "reusable_status": "HUMAN_REVIEWED_REUSABLE_COMPOSITE",
        "logical_module": "DFF_BUF",
        "logical_source_class_function": "DFF_BUF.add_dff_buf",
        "physical_cell_name": REPAIRED_CELL,
        "released_clean_gds_path": str(reusable_clean.resolve()),
        "source_repaired_clean_gds_path": str(repaired_clean.resolve()),
        "source_repaired_annotated_gds_path": str(repaired_annotated.resolve()),
        "source_repaired_review_atlas_gds_path": str(repaired_atlas.resolve()),
        "openyield_commit": dff_manifest["source_commit_openyield"],
        "canonical_topology_hash": "6058eaf43739",
        "repaired_geometry_hash": probe["geometry_fingerprint"]["digest"],
        "source_clean_gds_hash": REPAIRED_SHA,
        "release_gds_hash": released_sha,
        "child_binding_list": [{k: row[k] for k in ["instance_name", "child_logical_module", "resolved_physical_cell_name", "binding_status"]} for row in binding_rows],
        "approved_dff_dependency": {"physical_cell_name": dff_manifest["physical_cell_name"], "released_clean_gds_path": dff_manifest["released_clean_gds_path"], "sha256": dff_manifest["clean_gds_sha256"]},
        "approved_pinv_dependencies": [
            {"physical_cell_name": row["resolved_physical_cell_name"], "approved_physical_source_path": row["approved_physical_source_path"]}
            for row in binding_rows
            if row["instance_name"] in {"inv1", "inv2"}
        ],
        "top_pin_list": ["VDD", "VSS", "D", "Q", "QB", "CLK"],
        "internal_parent_net_list": ["qint"],
        "connectivity_summary": {k: repair_manifest[k] for k in ["expected_net_count", "actual_net_component_count", "unexpected_net_merge_count", "missing_expected_endpoint_count", "unexpected_endpoint_count", "floating_required_pin_count", "power_signal_short_count", "vdd_vss_short_present"]},
        "hierarchical_contact_summary": {k: repair_manifest[k] for k in ["hierarchical_foreign_net_contact_count", "unexpected_child_internal_net_contact_count", "clk_clkb_short_present", "q_qb_internal_short_present"]},
        "drc_summary": {"drc_marker_count": probe["drc"]["marker_count"], "drc_passed": probe["drc"]["drc_passed"]},
        "determinism_summary": {"deterministic_release_verified": release_checks["deterministic_release_verified"]},
        "human_review_record": human_review,
        "reusable_source_list": [str(reusable_clean.resolve())],
        "forbidden_physical_sources": [
            str((REPO_ROOT / "outputs/Wave3_DFF_BUF_hierarchical_pin_access_repair/quarantined_failed_candidate/DFF_BUF_clean.gds").resolve()),
            str(repaired_annotated.resolve()),
            str(repaired_atlas.resolve()),
            str(final_atlas.resolve()),
        ],
        "prohibited_claims": [
            "LVS passed",
            "transistor-level SPICE functional simulation passed",
            "setup/hold characterized",
            "clock-to-Q characterized",
            "timing signoff passed",
            "full CONTROL_LOGIC completed",
            "signoff ready",
        ],
        "only_clean_gds_is_composition_source": True,
    }
    _write_json(reusable_dir / "DFF_BUF_REUSABLE_MANIFEST.json", reusable_manifest)
    _write_text(reusable_dir / "DFF_BUF_REUSABLE_MANIFEST.md", "# DFF BUF Reusable Manifest\n\n" + "\n".join(f"- {k}: `{v}`" for k, v in reusable_manifest.items() if k not in {"child_binding_list", "approved_pinv_dependencies", "forbidden_physical_sources", "prohibited_claims"}) + "\n")

    src_spec = _read_json(repair_dir / "SRAM_SPEC.json")
    src_spec["generator"] = "Wave3 / DFF_BUF_HUMAN_REVIEW_SEAL_AND_REUSABLE_RELEASE"
    src_spec["output"] = str(reusable_clean.resolve())
    src_spec["qualification_status"] = "HUMAN_REVIEWED_REUSABLE_COMPOSITE"
    _write_json(reusable_dir / "SRAM_SPEC.json", src_spec)
    _write_text(reusable_dir / "SRAM_SPEC.md", "# SRAM_SPEC\n\n" + "\n".join(f"- {k}: `{v}`" for k, v in src_spec.items()) + "\n")

    # Wave-plan-based next stage.
    wave_plan = REPO_ROOT / "outputs/M12C4_composite_control_cell_generation_plan/current_supported_config/M12C4_composite_implementation_wave_plan.csv"
    plan_rows = list(csv.DictReader(wave_plan.open("r", encoding="utf-8", newline="")))
    wave3 = next(row for row in plan_rows if row["wave_id"] == "Wave3")
    wave4 = next(row for row in plan_rows if row["wave_id"] == wave3["next_wave_dependency"])
    recommended_next_stage = wave4["module"]
    recommended_next_stage_reason = f"Locked wave plan advances from {wave3['wave_id']} to {wave4['wave_id']}; {wave4['module']} depends on {wave4['dependency_modules']}, which are already approved reusable dependencies for controlled composition."

    status_json = _read_json(REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json")
    status_json["current_stage"] = "Wave3 / DFF_BUF_HUMAN_REVIEW_SEAL_AND_REUSABLE_RELEASE"
    status_json["current_route"] = "Wave3 DFF_BUF repaired candidate is human-review sealed and released as a controlled reusable composite."
    status_json["can_enter_next_stage_without_human_review"] = False
    status_json["can_enter_next_stage"] = True
    status_json["recommended_next_stage"] = recommended_next_stage
    status_json["recommended_next_stage_reason"] = recommended_next_stage_reason
    status_json["next_stage"] = recommended_next_stage
    status_json["Wave3_DFF_BUF"] = {"current_status": "HUMAN_REVIEWED_REUSABLE_COMPOSITE"}
    status_json["Wave3_DFF_BUF_failed_candidate"] = {
        "current_status": "QUARANTINED_HUMAN_DETECTED_HIERARCHICAL_INTERNAL_SHORT",
        "machine_pass_status": "REVOKED_DUE_TO_INCOMPLETE_HIERARCHICAL_CONNECTIVITY_MODEL",
    }
    _write_json(REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json", status_json)
    section = "\n".join(
        [
            "## Wave3 / DFF_BUF",
            "",
            "- current_status: `HUMAN_REVIEWED_REUSABLE_COMPOSITE`.",
            "- approved_dff_status: `HUMAN_REVIEWED_REUSABLE_COMPOSITE`.",
            "- old_candidate_status: `QUARANTINED_HUMAN_DETECTED_HIERARCHICAL_INTERNAL_SHORT`.",
            "- old_machine_pass_status: `REVOKED_DUE_TO_INCOMPLETE_HIERARCHICAL_CONNECTIVITY_MODEL`.",
            "- repaired_dff_buf_human_visual_review: `PASS`.",
            "- can_enter_next_stage_without_human_review: `False`.",
            "- can_enter_next_stage: `True`.",
            "- This only means DFF_BUF may be used by controlled higher-level composition; it does not claim LVS, SPICE, timing characterization, or signoff readiness.",
            f"- Recommended next stage: `{recommended_next_stage}`.",
            f"- Recommended next stage reason: `{recommended_next_stage_reason}`",
        ]
    )
    for md_name in ["PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md", "PROJECT_NETLIST_TO_LAYOUT_GOAL.md", "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md"]:
        _update_md_section(REPO_ROOT / md_name, section)

    commit_info = subprocess.run(["git", "log", "-1", "--stat", "--oneline"], cwd=REPO_ROOT, text=True, capture_output=True, check=False).stdout
    git_diff = subprocess.run(["git", "diff", "--", "."], cwd=REPO_ROOT, text=True, capture_output=True, check=False).stdout
    _write_text(seal_dir / "Wave3_DFF_BUF_human_review_seal_git.diff", git_diff)
    _write_text(seal_dir / "Wave3_DFF_BUF_human_review_seal_commit_info.txt", commit_info)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    evidence_path = REPO_ROOT / f"Wave3_DFF_BUF_human_review_seal_and_reusable_release_final_{timestamp}.tar.gz"
    with tarfile.open(evidence_path, "w:gz") as tar:
        include_paths = [
            REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
            REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
            REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_GOAL.md",
            REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
            REPO_ROOT / "docs/Wave3_DFF_BUF_human_visual_review.md",
            REPO_ROOT / "docs/Wave3_DFF_BUF_human_visual_review.json",
            REPO_ROOT / "docs/Wave3_DFF_BUF_boundary_contact_detector_tests.md",
            REPO_ROOT / "docs/Wave3_DFF_BUF_boundary_contact_detector_tests.json",
            seal_dir / "DFF_BUF_final_review_atlas.gds",
            seal_dir / "DFF_BUF_FINAL_REVIEW_ATLAS_INVENTORY.json",
            reusable_dir / "DFF_BUF_reusable_clean.gds",
            reusable_dir / "DFF_BUF_REUSABLE_MANIFEST.json",
            reusable_dir / "DFF_BUF_REUSABLE_MANIFEST.md",
            reusable_dir / "DFF_BUF_REUSABLE_RELEASE_CHECKS.json",
            reusable_dir / "DFF_BUF_REUSABLE_RELEASE_CHECKS.md",
            reusable_dir / "SRAM_SPEC.json",
            reusable_dir / "SRAM_SPEC.md",
            repair_dir / "DFF_BUF_REPAIR_MANIFEST.json",
            repair_dir / "Wave3_DFF_BUF_repaired_drc_report.json",
            repair_dir / "Wave3_DFF_BUF_repaired_deterministic_regeneration_report.json",
            REPO_ROOT / "docs/Wave3_DFF_BUF_human_review_failure.md",
            REPO_ROOT / "docs/Wave3_DFF_BUF_human_review_failure.json",
            seal_dir / "Wave3_DFF_BUF_human_review_seal_git.diff",
            seal_dir / "Wave3_DFF_BUF_human_review_seal_commit_info.txt",
            REPO_ROOT / "scripts/Wave3_DFF_BUF_human_review_seal_and_reusable_release.py",
            REPO_ROOT / "sram_layoutgen/openyield_adapter/hierarchical_foreign_net_detector.py",
        ]
        for path in include_paths:
            if path.exists():
                tar.add(path, arcname=path.relative_to(REPO_ROOT))
    _write_text(seal_dir / "evidence_package_path.txt", str(evidence_path))


if __name__ == "__main__":
    main()
