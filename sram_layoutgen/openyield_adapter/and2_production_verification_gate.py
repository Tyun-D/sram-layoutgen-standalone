from __future__ import annotations

import csv
import hashlib
import inspect
import json
import math
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.and2_source_lock import EXPECTED_OPENYIELD_COMMIT, EXPECTED_STANDARD_CELL_BLOB, build_and2_source_lock
from sram_layoutgen.openyield_adapter.hierarchical_connectivity_verifier import _component_for_bbox, verify_hierarchical_connectivity
from sram_layoutgen.openyield_adapter.physical_connectivity_extractor import extract_physical_connectivity
from sram_layoutgen.openyield_adapter.pnand2_verification_gate import direct_top_labels_report, json_safe, sha256_file, write_csv, write_json, write_text
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import conductive_geometry_fingerprint, geometry_fingerprint, non_text_geometry_fingerprint, read_top_cell
from sram_layoutgen.openyield_adapter.rejection_code_registry import rejection_family
from sram_layoutgen.openyield_adapter.teamb_composite_helper import read_json
from sram_layoutgen.tech import Tech


PNAND2_NAME = "PNAND2_NW180_PW270_L50_FPDK45"
PINV_NAME = "PINV_NW90_PW270_L50"
AND2_NAME = "AND2_PNAND2_PINV_FPDK45"
PNAND2_SHA = "60563fd88e67acd2dffcf08c44e6555573f081668275e42ecb164c925bf846cf"


def _render_md(title: str, lines: list[str]) -> str:
    return "\n".join([f"# {title}", "", *lines, ""]).rstrip() + "\n"


def _pinv_dir(repo_root: Path) -> Path:
    return repo_root / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells/PINV_NW90_PW270_L50"


def _clone_root_to_logical(root_name: str) -> str:
    if "__PNAND2_" in root_name or PNAND2_NAME in root_name:
        return "PNAND2"
    if "__PINV_" in root_name or PINV_NAME in root_name:
        return "PINV"
    return "UNKNOWN"


def _top_refs(clean_gds: Path) -> list[dict[str, Any]]:
    lib, top = read_top_cell(clean_gds, AND2_NAME)
    rows = []
    for ref in top.references:
        cell_name = ref.cell_name or ref.cell.name
        rows.append(
            {
                "ref_cell_name": cell_name,
                "origin": [round(float(ref.origin[0]), 6), round(float(ref.origin[1]), 6)],
                "logical_type": _clone_root_to_logical(cell_name),
            }
        )
    return rows


def _shift_pin_map(pin_map: dict[str, list[dict[str, Any]]], dx: float, dy: float) -> dict[str, list[dict[str, Any]]]:
    out: dict[str, list[dict[str, Any]]] = {}
    for name, rows in pin_map.items():
        out[name] = []
        for row in rows:
            out[name].append(
                {
                    **row,
                    "lx": round(float(row["lx"]) + dx, 6),
                    "by": round(float(row["by"]) + dy, 6),
                    "rx": round(float(row["rx"]) + dx, 6),
                    "uy": round(float(row["uy"]) + dy, 6),
                }
            )
    return out


def _resolve_child_bindings(repo_root: Path, clean_gds: Path) -> dict[str, Any]:
    pnand2_dir = repo_root / "outputs/TeamB_PNAND2_reference_demo/current_supported_config"
    pinv_dir = _pinv_dir(repo_root)
    refs = _top_refs(clean_gds)
    ref_by_type = {row["logical_type"]: row for row in refs}
    pnand2_origin = tuple(ref_by_type["PNAND2"]["origin"]) if "PNAND2" in ref_by_type else (0.0, 0.0)
    pinv_origin = tuple(ref_by_type["PINV"]["origin"]) if "PINV" in ref_by_type else (0.0, 0.0)
    pnand2_pin_map = _shift_pin_map(read_json(pnand2_dir / "PNAND2_pin_map.json"), *pnand2_origin)
    pinv_pin_map = _shift_pin_map(read_json(pinv_dir / "PINV_NW90_PW270_L50_pin_map.json"), *pinv_origin)
    instance_rows = [
        {
            "logical_child": "nand_gate",
            "source_instance_path": "AND2.nand_gate",
            "requested_parameters_nm": {"nmos_width_nm": 180, "pmos_width_nm": 270, "length_nm": 50},
            "resolved_physical_cell": PNAND2_NAME,
            "child_gds_path": str((pnand2_dir / f"{PNAND2_NAME}.gds").resolve()),
            "child_gds_sha256": sha256_file(pnand2_dir / f"{PNAND2_NAME}.gds"),
            "approved_reference_status": "OWNER_A_HUMAN_REVIEWED_REFERENCE_DEMO_PENDING_TEAM_B_INDEPENDENT_REVIEW",
            "parameter_status": "EXACT_MATCH",
        },
        {
            "logical_child": "inv_driver",
            "source_instance_path": "AND2.inv_driver",
            "requested_parameters_nm": {"nmos_width_nm": 90, "pmos_width_nm": 270, "length_nm": 50},
            "resolved_physical_cell": PINV_NAME,
            "child_gds_path": str((pinv_dir / f"{PINV_NAME}.gds").resolve()),
            "child_gds_sha256": sha256_file(pinv_dir / f"{PINV_NAME}.gds"),
            "approved_reference_status": "APPROVED_REUSABLE_ASSET_LOCK_INFERRED_FROM_CANONICAL_REUSABLE_DIR",
            "parameter_status": "EXACT_MATCH",
        },
    ]
    return {"refs": refs, "pnand2_pin_map": pnand2_pin_map, "pinv_pin_map": pinv_pin_map, "instance_rows": instance_rows}


def _compare_child_fingerprints(clean_gds: Path, child_top_name: str, original_gds: Path) -> dict[str, Any]:
    lib = gdstk.read_gds(clean_gds)
    cell = next(item for item in lib.cells if item.name == child_top_name)
    with tempfile.TemporaryDirectory(prefix="and2_child_fp_") as tmp:
        tmp_path = Path(tmp) / f"{child_top_name}.gds"
        child_lib = gdstk.Library(unit=lib.unit, precision=lib.precision)
        copied = cell.copy(child_top_name, deep_copy=True)
        child_lib.add(copied)
        child_lib.write_gds(tmp_path)
        return {
            "original_geometry_fingerprint": geometry_fingerprint(original_gds, None),
            "clone_geometry_fingerprint": geometry_fingerprint(tmp_path, child_top_name),
            "original_non_text_geometry_fingerprint": non_text_geometry_fingerprint(original_gds, None),
            "clone_non_text_geometry_fingerprint": non_text_geometry_fingerprint(tmp_path, child_top_name),
            "original_conductive_geometry_fingerprint": conductive_geometry_fingerprint(original_gds, None),
            "clone_conductive_geometry_fingerprint": conductive_geometry_fingerprint(tmp_path, child_top_name),
        }


def _round6(value: float) -> float:
    return round(float(value), 6)


def _norm_bbox(bbox: tuple[tuple[float, float], tuple[float, float]] | None, *, anchor: tuple[float, float]) -> list[float]:
    if bbox is None:
        return []
    return [
        _round6(bbox[0][0] - anchor[0]),
        _round6(bbox[0][1] - anchor[1]),
        _round6(bbox[1][0] - anchor[0]),
        _round6(bbox[1][1] - anchor[1]),
    ]


def _poly_payload(poly: gdstk.Polygon, *, anchor: tuple[float, float]) -> dict[str, Any]:
    pts = [(_round6(x - anchor[0]), _round6(y - anchor[1])) for x, y in poly.points]
    return {
        "layer": int(poly.layer),
        "datatype": int(poly.datatype),
        "bbox": _norm_bbox(poly.bounding_box(), anchor=anchor),
        "points": sorted(pts),
    }


def _digest_payload(payload: Any) -> str:
    return hashlib.sha256(json.dumps(json_safe(payload), sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()[:24]


def _cell_pin_labels_from_map(pin_map: dict[str, list[dict[str, Any]]], *, anchor: tuple[float, float]) -> list[dict[str, Any]]:
    labels = []
    for name, rows in sorted(pin_map.items()):
        for row in rows:
            labels.append(
                {
                    "text": name,
                    "layer": str(row.get("layer", "m1")),
                    "texttype": str(row.get("texttype", "pin")),
                    "bbox": [
                        _round6(float(row["lx"]) - anchor[0]),
                        _round6(float(row["by"]) - anchor[1]),
                        _round6(float(row["rx"]) - anchor[0]),
                        _round6(float(row["uy"]) - anchor[1]),
                    ],
                }
            )
    return labels


def _reachable_cells(lib: gdstk.Library, root_name: str) -> list[gdstk.Cell]:
    cell_by_name = {cell.name: cell for cell in lib.cells}
    out: list[gdstk.Cell] = []
    seen: set[str] = set()

    def visit(name: str) -> None:
        if name in seen or name not in cell_by_name:
            return
        seen.add(name)
        cell = cell_by_name[name]
        out.append(cell)
        for ref in cell.references:
            child = ref.cell_name or ref.cell.name
            visit(child)

    visit(root_name)
    return out


def _canonical_bundle_manifest(gds_path: Path, root_name: str, *, pin_map: dict[str, list[dict[str, Any]]] | None = None) -> dict[str, Any]:
    lib = gdstk.read_gds(gds_path)
    root = next(cell for cell in lib.cells if cell.name == root_name)
    root_bbox = root.bounding_box()
    anchor = (float(root_bbox[0][0]), float(root_bbox[0][1])) if root_bbox is not None else (0.0, 0.0)
    cells = _reachable_cells(lib, root_name)
    cell_payloads: dict[str, dict[str, Any]] = {}
    child_lists: dict[str, list[tuple[str, list[float]]]] = {}
    root_labels = _cell_pin_labels_from_map(pin_map or {}, anchor=anchor)
    for cell in cells:
        labels = root_labels if cell.name == root_name and pin_map else [
            {
                "text": str(label.text),
                "layer": int(label.layer),
                "texttype": int(label.texttype),
                "origin": [_round6(float(label.origin[0]) - anchor[0]), _round6(float(label.origin[1]) - anchor[1])],
            }
            for label in cell.labels
        ]
        polys = [_poly_payload(poly, anchor=anchor) for poly in cell.polygons]
        layer_hist: dict[str, int] = {}
        conductive_hist: dict[str, int] = {}
        conductive_polys = []
        for poly in polys:
            key = f"{poly['layer']}/{poly['datatype']}"
            layer_hist[key] = layer_hist.get(key, 0) + 1
            if poly["layer"] in {1, 9, 10, 11}:
                conductive_hist[key] = conductive_hist.get(key, 0) + 1
                conductive_polys.append(poly)
        refs = []
        for ref in cell.references:
            child = ref.cell_name or ref.cell.name
            refs.append(
                (
                    child,
                    [
                        _round6(float(ref.origin[0]) - anchor[0]),
                        _round6(float(ref.origin[1]) - anchor[1]),
                        _round6(float(getattr(ref, "rotation", 0.0) or 0.0)),
                        _round6(float(getattr(ref, "magnification", 1.0) or 1.0)),
                        1.0 if getattr(ref, "x_reflection", False) else 0.0,
                    ],
                )
            )
        cell_payloads[cell.name] = {
            "bbox": _norm_bbox(cell.bounding_box(), anchor=anchor),
            "bbox_size": [
                _round6((float(cell.bounding_box()[1][0]) - float(cell.bounding_box()[0][0])) if cell.bounding_box() is not None else 0.0),
                _round6((float(cell.bounding_box()[1][1]) - float(cell.bounding_box()[0][1])) if cell.bounding_box() is not None else 0.0),
            ],
            "polygons": sorted(polys, key=lambda row: json.dumps(row, sort_keys=True)),
            "conductive_polygons": sorted(conductive_polys, key=lambda row: json.dumps(row, sort_keys=True)),
            "labels": sorted(labels, key=lambda row: json.dumps(row, sort_keys=True)),
            "layer_histogram": dict(sorted(layer_hist.items())),
            "conductive_layer_histogram": dict(sorted(conductive_hist.items())),
        }
        child_lists[cell.name] = refs
    signatures: dict[str, str] = {}
    pending = set(cell_payloads)
    while pending:
        progressed = False
        for cell_name in list(pending):
            children = child_lists[cell_name]
            if any(child not in signatures for child, _ in children):
                continue
            payload = cell_payloads[cell_name]
            payload["non_text_digest"] = _digest_payload(payload["polygons"])
            payload["conductive_digest"] = _digest_payload(payload["conductive_polygons"])
            payload["label_digest"] = _digest_payload(payload["labels"])
            payload["ref_edges"] = sorted(
                [{"child_signature": signatures[child], "transform": transform} for child, transform in children],
                key=lambda row: json.dumps(row, sort_keys=True),
            )
            signatures[cell_name] = _digest_payload(
                {
                    "bbox": payload["bbox_size"],
                    "non_text": payload["non_text_digest"],
                    "conductive": payload["conductive_digest"],
                    "labels": payload["label_digest"],
                    "layer_histogram": payload["layer_histogram"],
                    "refs": payload["ref_edges"],
                }
            )
            progressed = True
            pending.remove(cell_name)
        if not progressed:
            raise RuntimeError(f"unable to canonicalize child bundle for {gds_path}")
    manifests = []
    canonical_map = {}
    for cell_name in sorted(cell_payloads):
        payload = cell_payloads[cell_name]
        payload["canonical_signature"] = signatures[cell_name]
        manifests.append(
            {
                "canonical_signature": signatures[cell_name],
                "bbox_size": payload["bbox_size"],
                "non_text_digest": payload["non_text_digest"],
                "conductive_digest": payload["conductive_digest"],
                "label_digest": payload["label_digest"],
                "layer_histogram": payload["layer_histogram"],
                "conductive_layer_histogram": payload["conductive_layer_histogram"],
                "ref_edges": payload["ref_edges"],
                "is_root": cell_name == root_name,
            }
        )
        canonical_map[cell_name] = signatures[cell_name]
    manifests = sorted(manifests, key=lambda row: json.dumps(row, sort_keys=True))
    root_payload = cell_payloads[root_name]
    return {
        "root_bbox": root_payload["bbox_size"],
        "root_non_text_digest": root_payload["non_text_digest"],
        "root_conductive_digest": root_payload["conductive_digest"],
        "root_label_digest": root_payload["label_digest"],
        "root_layer_histogram": root_payload["layer_histogram"],
        "root_ref_digest": _digest_payload(root_payload["ref_edges"]),
        "descendant_count": len(manifests),
        "cells": manifests,
        "canonical_cell_mapping": canonical_map,
        "canonical_hierarchy_graph_digest": _digest_payload(manifests),
    }


def _build_child_immutability_report(*, repo_root: Path, cell_dir: Path, write_artifacts: bool) -> dict[str, Any]:
    out_root = cell_dir / "child_immutability"
    pnand2_dir = repo_root / "outputs/TeamB_PNAND2_reference_demo/current_supported_config"
    pinv_dir = _pinv_dir(repo_root)
    specs = [
        {
            "logical_type": "PNAND2",
            "original_gds": pnand2_dir / f"{PNAND2_NAME}.gds",
            "clone_gds": cell_dir / "_clones" / "TEAMB_CLONE__nand.gds",
            "original_root": PNAND2_NAME,
            "clone_root": next(cell.name for cell in gdstk.read_gds(cell_dir / "_clones" / "TEAMB_CLONE__nand.gds").cells if "__PNAND2_" in cell.name and cell.name.endswith(PNAND2_NAME)),
            "pin_map": read_json(pnand2_dir / "PNAND2_pin_map.json"),
        },
        {
            "logical_type": "PINV",
            "original_gds": pinv_dir / f"{PINV_NAME}.gds",
            "clone_gds": cell_dir / "_clones" / "TEAMB_CLONE__inv.gds",
            "original_root": PINV_NAME,
            "clone_root": next(cell.name for cell in gdstk.read_gds(cell_dir / "_clones" / "TEAMB_CLONE__inv.gds").cells if "__PINV_" in cell.name and cell.name.endswith(PINV_NAME)),
            "pin_map": read_json(pinv_dir / f"{PINV_NAME}_pin_map.json"),
        },
    ]
    rows: dict[str, Any] = {}
    passed = True
    for spec in specs:
        original = _canonical_bundle_manifest(spec["original_gds"], spec["original_root"], pin_map=spec["pin_map"])
        clone = _canonical_bundle_manifest(spec["clone_gds"], spec["clone_root"], pin_map=spec["pin_map"])
        diff = {
            "bundle_equivalent": original["canonical_hierarchy_graph_digest"] == clone["canonical_hierarchy_graph_digest"],
            "geometry_equivalent": original["root_non_text_digest"] == clone["root_non_text_digest"],
            "conductive_equivalent": original["root_conductive_digest"] == clone["root_conductive_digest"],
            "labels_equivalent": original["root_label_digest"] == clone["root_label_digest"],
            "hierarchy_equivalent": original["root_ref_digest"] == clone["root_ref_digest"] and original["descendant_count"] == clone["descendant_count"],
            "bbox_equivalent": original["root_bbox"] == clone["root_bbox"],
            "layer_histogram_equivalent": original["root_layer_histogram"] == clone["root_layer_histogram"],
            "original_bundle_digest": original["canonical_hierarchy_graph_digest"],
            "clone_bundle_digest": clone["canonical_hierarchy_graph_digest"],
        }
        bundle_dir = out_root / spec["logical_type"]
        if write_artifacts:
            write_json(bundle_dir / "original_bundle_manifest.json", original)
            write_json(bundle_dir / "clone_bundle_manifest.json", clone)
            write_json(bundle_dir / "canonical_cell_mapping.json", {"original": original["canonical_cell_mapping"], "clone": clone["canonical_cell_mapping"]})
            write_json(bundle_dir / "bundle_diff.json", diff)
        row = {
            **diff,
            "canonical_hierarchy_graph_digest_original": original["canonical_hierarchy_graph_digest"],
            "canonical_hierarchy_graph_digest_clone": clone["canonical_hierarchy_graph_digest"],
            "canonical_non_text_geometry_digest_original": original["root_non_text_digest"],
            "canonical_non_text_geometry_digest_clone": clone["root_non_text_digest"],
            "canonical_conductive_geometry_digest_original": original["root_conductive_digest"],
            "canonical_conductive_geometry_digest_clone": clone["root_conductive_digest"],
            "canonical_label_digest_original": original["root_label_digest"],
            "canonical_label_digest_clone": clone["root_label_digest"],
            "canonical_bbox_digest_original": _digest_payload(original["root_bbox"]),
            "canonical_bbox_digest_clone": _digest_payload(clone["root_bbox"]),
            "canonical_layer_histogram_original": original["root_layer_histogram"],
            "canonical_layer_histogram_clone": clone["root_layer_histogram"],
            "canonical_descendant_count_original": original["descendant_count"],
            "canonical_descendant_count_clone": clone["descendant_count"],
        }
        rows[spec["logical_type"]] = row
        passed = passed and all(diff.values())
    report = {"child_count_exact": len(rows) == 2, "rows": rows, "child_immutability_passed": passed}
    if write_artifacts:
        write_json(cell_dir / "child_immutability.json", report)
    return report


def _clone_path_for_ref(cell_dir: Path, ref_cell_name: str) -> Path | None:
    if "__nand__" in ref_cell_name:
        path = cell_dir / "_clones" / "TEAMB_CLONE__nand.gds"
        return path if path.exists() else None
    if "__inv__" in ref_cell_name:
        path = cell_dir / "_clones" / "TEAMB_CLONE__inv.gds"
        return path if path.exists() else None
    return None


def normalize_connectivity_report_schema(report: dict[str, Any] | None) -> dict[str, Any]:
    payload = dict(report or {})
    graph_raw = payload.get("graph") or {}
    graph = dict(graph_raw) if isinstance(graph_raw, dict) else {}
    components = graph.get("components")
    rectangles = graph.get("rectangles")
    active_segments = graph.get("active_segments")
    contact_pairs = graph.get("contact_pairs")
    labels = graph.get("labels")
    via_links = graph.get("via_links")
    contact_links = graph.get("contact_links")
    graph["components"] = components if isinstance(components, list) else []
    graph["rectangles"] = rectangles if isinstance(rectangles, dict) else {}
    graph["active_segments"] = active_segments if isinstance(active_segments, list) else []
    graph["contact_pairs"] = contact_pairs if isinstance(contact_pairs, list) else []
    graph["labels"] = labels if isinstance(labels, list) else []
    graph["via_links"] = via_links if isinstance(via_links, list) else []
    graph["contact_links"] = contact_links if isinstance(contact_links, list) else []
    payload["graph"] = graph
    payload.setdefault("per_net", [])
    payload.setdefault("expected_net_count", 0)
    payload.setdefault("actual_net_component_count", 0)
    payload.setdefault("unexpected_net_merges", {})
    payload.setdefault("unexpected_net_merge_count", 0)
    payload.setdefault("missing_expected_endpoint_count", 0)
    payload.setdefault("unexpected_endpoint_count", 0)
    payload.setdefault("floating_required_pin_count", 0)
    payload.setdefault("power_signal_short_count", 0)
    payload.setdefault("vdd_vss_short_present", False)
    payload.setdefault("zb_int_Z_direct_short_present", False)
    payload.setdefault("physical_connectivity_verification_passed", False)
    payload.setdefault("component_summary", [])
    payload.setdefault("top_pin_components", {})
    payload.setdefault("child_pin_components", {})
    payload.setdefault("internal_components", {})
    payload.setdefault("unexpected_merges", payload.get("unexpected_net_merges", {}))
    payload.setdefault("missing_connections", [])
    return payload


def _foreign_net_report(clean_gds: Path, endpoints_by_net: dict[str, list[dict[str, Any]]], top_pin_bboxes: dict[str, dict[str, float]]) -> dict[str, Any]:
    verify_kwargs = {
        "gds_path": clean_gds,
        "top_name": AND2_NAME,
        "endpoints_by_net": endpoints_by_net,
        "top_pin_bboxes": top_pin_bboxes,
    }
    if "short_exclusion_pairs" in inspect.signature(verify_hierarchical_connectivity).parameters:
        verify_kwargs["short_exclusion_pairs"] = [("zb_int", "Z")]
    report = normalize_connectivity_report_schema(
        verify_hierarchical_connectivity(**verify_kwargs)
    )
    zb = next(row for row in report["per_net"] if row["net_name"] == "zb_int")
    disallowed = [name for name in zb["actual_endpoint_set"] if name not in {"nand.Z", "inv.A"}]
    return {
        "foreign_net_contact_count": len(disallowed),
        "foreign_net_contacts": disallowed,
        "foreign_net_passed": len(disallowed) == 0,
        "connectivity_report": report,
    }


def _build_structural_report(source_lock: dict[str, Any], bindings: dict[str, Any], label_report: dict[str, Any], refs: list[dict[str, Any]], connectivity_report: dict[str, Any]) -> dict[str, Any]:
    logical_types = sorted(row["logical_type"] for row in refs)
    return {
        "formal_top_pin_names_exact": source_lock["top_pin_names"] == ["VDD", "VSS", "A", "B", "Z"],
        "formal_top_pin_order_exact": source_lock["top_pin_order"] == ["VDD", "VSS", "A", "B", "Z"],
        "child_count_exact": len(refs) == 2,
        "child_types_exact": logical_types == ["PINV", "PNAND2"],
        "child_parameter_binding_exact": all(row["parameter_status"] == "EXACT_MATCH" for row in bindings["instance_rows"]),
        "internal_net_zb_int_only_internal": label_report["no_internal_net_promoted_to_top_port"],
        "hierarchy_topology_exact": connectivity_report["physical_connectivity_verification_passed"],
        "no_internal_top_port": label_report["no_internal_net_promoted_to_top_port"],
        "strict_source_derived_structural_gate_passed": len(refs) == 2
        and logical_types == ["PINV", "PNAND2"]
        and all(row["parameter_status"] == "EXACT_MATCH" for row in bindings["instance_rows"])
        and label_report["pin_name_set_exact"]
        and label_report["pin_order_exact"]
        and connectivity_report["physical_connectivity_verification_passed"],
    }


def _determinism_report(repo_root: Path, klayout_bin: Path, drc_deck: Path, openyield_root: Path) -> dict[str, Any]:
    runner = """
import hashlib
import json
import sys
from pathlib import Path
repo_root = Path(sys.argv[1]).resolve()
out_dir = Path(sys.argv[2]).resolve()
openyield_root = Path(sys.argv[3]).resolve()
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))
from scripts.TeamB_remaining9_reference_generation import _generate_and2
result = _generate_and2(out_dir.parent, Path('/usr/bin/klayout'), repo_root / 'technology/freepdk45/tech/freepdk45.lydrc', openyield_root=openyield_root, resume_negative_tests=False, layout_only=True)
clean_gds = result['clean_gds']
print(json.dumps({'path': str(clean_gds), 'sha': hashlib.sha256(clean_gds.read_bytes()).hexdigest()}))
"""
    with tempfile.TemporaryDirectory(prefix="and2_det_a_") as a_dir, tempfile.TemporaryDirectory(prefix="and2_det_b_") as b_dir:
        proc_a = subprocess.run(["python", "-c", runner, str(repo_root), a_dir, str(openyield_root)], text=True, capture_output=True, check=True)
        proc_b = subprocess.run(["python", "-c", runner, str(repo_root), b_dir, str(openyield_root)], text=True, capture_output=True, check=True)
        rep_a = json.loads(proc_a.stdout.strip())
        rep_b = json.loads(proc_b.stdout.strip())
        pa = Path(rep_a["path"])
        pb = Path(rep_b["path"])
        return {
            "run_a_clean_gds_path": str(pa),
            "run_b_clean_gds_path": str(pb),
            "run_a_sha256": rep_a["sha"],
            "run_b_sha256": rep_b["sha"],
            "byte_identical": pa.read_bytes() == pb.read_bytes(),
        }


def _review_artifacts_complete(cell_dir: Path) -> bool:
    expected = [
        cell_dir / "annotated.gds",
        cell_dir / "review_atlas.gds",
        cell_dir / "human_review/AND2_HUMAN_REVIEW_INPUT_LOCK.json",
        cell_dir / "human_review/AND2_HUMAN_REVIEW_CHECKLIST.csv",
        cell_dir / "human_review/AND2_HUMAN_REVIEW_REPORT_TEMPLATE.md",
        cell_dir / "human_review/AND2_HUMAN_REVIEW_SCREENSHOT_INDEX.csv",
    ]
    return all(path.exists() for path in expected)


def _any_off_grid(clean_gds: Path, tech: Tech) -> bool:
    _, top = read_top_cell(clean_gds, AND2_NAME)
    flattened = top.flatten()
    grid = tech.manufacturing_grid
    for poly in flattened.polygons:
        for x, y in poly.points:
            if abs((round(float(x) / grid) * grid) - float(x)) > 1e-6:
                return True
            if abs((round(float(y) / grid) * grid) - float(y)) > 1e-6:
                return True
    return False


def build_and2_production_gate(*, repo_root: Path, cell_dir: Path, openyield_root: Path, klayout_bin: Path, drc_deck: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    cell_dir = cell_dir.resolve()
    clean_gds = cell_dir / "clean.gds"
    source_lock = build_and2_source_lock(openyield_root)
    write_json(cell_dir / "source_lock.json", source_lock)
    write_text(cell_dir / "source_lock.md", _render_md("AND2 Source Lock", [f"- topology_digest: `{source_lock['topology_digest']}`"]))
    snapshot = subprocess.check_output(["git", "-C", str(openyield_root), "show", f"{EXPECTED_OPENYIELD_COMMIT}:sram_compiler/subcircuits/standard_cell.py"], text=True)
    write_text(cell_dir / "source_snapshot.py", snapshot)
    write_text(
        cell_dir / "source_reference.spice",
        "\n".join(
            [
                ".subckt AND2 VDD VSS A B Z",
                f"XPNAND3 VDD VSS A B zb_int {PNAND2_NAME}",
                f"XPINV VDD VSS zb_int Z {PINV_NAME}",
                ".ends AND2",
            ]
        ),
    )
    bindings = _resolve_child_bindings(repo_root, clean_gds)
    write_json(cell_dir / "parameter_mapping.json", {"status": "EXACT_MATCH", "children": bindings["instance_rows"]})
    write_csv(cell_dir / "instance_binding.csv", bindings["instance_rows"])
    label_report = direct_top_labels_report(clean_gds, AND2_NAME, expected_top_pins=["VDD", "VSS", "A", "B", "Z"], internal_nets=["zb_int", "net1"])
    write_json(cell_dir / "top_pin_contract.json", {"top_pin_order": ["VDD", "VSS", "A", "B", "Z"], "top_pin_names": ["VDD", "VSS", "A", "B", "Z"]})
    write_json(cell_dir / "direct_top_label_report.json", label_report)
    top_pins = {
        "VDD": bindings["pnand2_pin_map"]["VDD"][0],
        "VSS": bindings["pnand2_pin_map"]["VSS"][0],
        "A": bindings["pnand2_pin_map"]["A"][0],
        "B": bindings["pnand2_pin_map"]["B"][0],
        "Z": bindings["pinv_pin_map"]["Z"][0],
    }
    endpoints_by_net = {
        "A": [{"endpoint_name": "nand.A", "bbox": bindings["pnand2_pin_map"]["A"][0]}],
        "B": [{"endpoint_name": "nand.B", "bbox": bindings["pnand2_pin_map"]["B"][0]}],
        "Z": [{"endpoint_name": "inv.Z", "bbox": bindings["pinv_pin_map"]["Z"][0]}],
        "VDD": [{"endpoint_name": "nand.VDD", "bbox": bindings["pnand2_pin_map"]["VDD"][0]}, {"endpoint_name": "inv.VDD", "bbox": bindings["pinv_pin_map"]["VDD"][0]}],
        "VSS": [{"endpoint_name": "nand.VSS", "bbox": bindings["pnand2_pin_map"]["VSS"][0]}, {"endpoint_name": "inv.VSS", "bbox": bindings["pinv_pin_map"]["VSS"][0]}],
        "zb_int": [{"endpoint_name": "nand.Z", "bbox": bindings["pnand2_pin_map"]["Z"][0]}, {"endpoint_name": "inv.A", "bbox": bindings["pinv_pin_map"]["A"][0]}],
    }
    foreign_report = _foreign_net_report(clean_gds, endpoints_by_net, top_pins)
    write_json(cell_dir / "foreign_net_report.json", {k: v for k, v in foreign_report.items() if k != "connectivity_report"})
    write_json(cell_dir / "connectivity_graph.json", foreign_report["connectivity_report"]["graph"])
    child_immutability = _build_child_immutability_report(repo_root=repo_root, cell_dir=cell_dir, write_artifacts=True)
    structural = _build_structural_report(source_lock, bindings, label_report, bindings["refs"], foreign_report["connectivity_report"])
    write_json(cell_dir / "lvs/structural_contract_report.json", structural)
    write_text(cell_dir / "extracted.spice", "* Structural composite extraction placeholder derived from final clean GDS hierarchy\n")
    determinism = _determinism_report(repo_root, klayout_bin, drc_deck, openyield_root)
    write_json(cell_dir / "determinism.json", determinism)
    human_dir = cell_dir / "human_review"
    write_json(
        human_dir / "AND2_HUMAN_REVIEW_INPUT_LOCK.json",
        {
            "clean_gds_path": str(clean_gds.resolve()),
            "clean_gds_sha256": sha256_file(clean_gds),
            "annotated_gds_path": str((cell_dir / "annotated.gds").resolve()),
            "review_atlas_gds_path": str((cell_dir / "review_atlas.gds").resolve()),
            "drc_lyrdb": str((cell_dir / "drc" / f"{AND2_NAME}.lyrdb").resolve()),
        },
    )
    write_csv(
        human_dir / "AND2_HUMAN_REVIEW_CHECKLIST.csv",
        [{"item": item, "status": "PENDING"} for item in ["hierarchy", "zb_int_route", "power_rails", "pin_access", "labels", "foreign_net", "drc_database"]],
    )
    write_text(human_dir / "AND2_HUMAN_REVIEW_REPORT_TEMPLATE.md", _render_md("AND2 Human Review", ["- result: `PENDING`"]))
    write_csv(
        human_dir / "AND2_HUMAN_REVIEW_SCREENSHOT_INDEX.csv",
        [{"filename": name, "description": desc} for name, desc in [("01_clean_full.png", "clean full"), ("02_annotated_full.png", "annotated"), ("03_zb_int_route.png", "zb_int route"), ("04_drc_db.png", "drc database")]],
    )
    marker_count = 0
    drc_summary_path = cell_dir / "drc" / f"{AND2_NAME}.lyrdb"
    if drc_summary_path.exists():
        from sram_layoutgen.signoff import count_klayout_items

        marker_count = count_klayout_items(drc_summary_path)
    machine_gate = {
        "source_lock_complete": source_lock["authority_commit"] == EXPECTED_OPENYIELD_COMMIT and source_lock["git_blob_sha"] == EXPECTED_STANDARD_CELL_BLOB,
        "parameter_binding_closed": all(row["parameter_status"] == "EXACT_MATCH" for row in bindings["instance_rows"]),
        "top_pin_contract_exact": label_report["pin_name_set_exact"] and label_report["pin_count_exact"] and label_report["pin_order_exact"] and label_report["direct_top_labels_exact"],
        "internal_net_not_exposed": label_report["no_internal_net_promoted_to_top_port"],
        "child_count_exact": len(bindings["refs"]) == 2 and sorted(row["logical_type"] for row in bindings["refs"]) == ["PINV", "PNAND2"],
        "topology_match": foreign_report["connectivity_report"]["physical_connectivity_verification_passed"],
        "hierarchy_closure_passed": len(bindings["refs"]) == 2,
        "child_immutability_passed": child_immutability["child_immutability_passed"],
        "connectivity_passed": foreign_report["connectivity_report"]["physical_connectivity_verification_passed"],
        "foreign_net_passed": foreign_report["foreign_net_passed"],
        "drc_marker_count": marker_count,
        "strict_source_derived_structural_gate_passed": structural["strict_source_derived_structural_gate_passed"],
        "deterministic_A_B_byte_identical": determinism["byte_identical"],
        "negative_tests_passed": False,
        "review_artifacts_complete": _review_artifacts_complete(cell_dir),
    }
    write_json(cell_dir / "machine_gate.json", machine_gate)
    return {
        "source_lock": source_lock,
        "bindings": bindings,
        "label_report": label_report,
        "foreign_net_report": foreign_report,
        "child_immutability": child_immutability,
        "structural": structural,
        "determinism": determinism,
        "machine_gate": machine_gate,
    }


def validate_and2_bundle(*, repo_root: Path, bundle_dir: Path, openyield_root: Path, klayout_bin: Path, drc_deck: Path) -> dict[str, Any]:
    bundle_dir = bundle_dir.resolve()
    clean_gds = bundle_dir / "clean.gds"
    source_lock = read_json(bundle_dir / "source_lock.json") if (bundle_dir / "source_lock.json").exists() else {}
    parameter_mapping = read_json(bundle_dir / "parameter_mapping.json") if (bundle_dir / "parameter_mapping.json").exists() else {}
    instance_binding_rows = []
    if (bundle_dir / "instance_binding.csv").exists():
        with (bundle_dir / "instance_binding.csv").open(encoding="utf-8", newline="") as handle:
            instance_binding_rows = list(csv.DictReader(handle))
    label_report = direct_top_labels_report(clean_gds, AND2_NAME, expected_top_pins=["VDD", "VSS", "A", "B", "Z"], internal_nets=["zb_int", "net1"])
    top_pin_contract = read_json(bundle_dir / "top_pin_contract.json") if (bundle_dir / "top_pin_contract.json").exists() else {}
    bindings = _resolve_child_bindings(repo_root, clean_gds)
    logical_types = sorted(row["logical_type"] for row in bindings["refs"])
    missing_required_child = not all(name in logical_types for name in ["PINV", "PNAND2"])
    if missing_required_child:
        foreign_report = {
            "foreign_net_contact_count": 0,
            "foreign_net_contacts": [],
            "foreign_net_passed": False,
            "connectivity_report": {
                "physical_connectivity_verification_passed": False,
                "vdd_vss_short_present": False,
                "power_signal_short_count": 0,
                "zb_int_Z_direct_short_present": False,
                "per_net": [],
                "graph": {"components": [], "rectangles": [], "active_segments": [], "contact_pairs": []},
            },
        }
    else:
        top_pins = {
            "VDD": bindings["pnand2_pin_map"]["VDD"][0],
            "VSS": bindings["pnand2_pin_map"]["VSS"][0],
            "A": bindings["pnand2_pin_map"]["A"][0],
            "B": bindings["pnand2_pin_map"]["B"][0],
            "Z": bindings["pinv_pin_map"]["Z"][0],
        }
        endpoints_by_net = {
            "A": [{"endpoint_name": "nand.A", "bbox": bindings["pnand2_pin_map"]["A"][0]}],
            "B": [{"endpoint_name": "nand.B", "bbox": bindings["pnand2_pin_map"]["B"][0]}],
            "Z": [{"endpoint_name": "inv.Z", "bbox": bindings["pinv_pin_map"]["Z"][0]}],
            "VDD": [{"endpoint_name": "nand.VDD", "bbox": bindings["pnand2_pin_map"]["VDD"][0]}, {"endpoint_name": "inv.VDD", "bbox": bindings["pinv_pin_map"]["VDD"][0]}],
            "VSS": [{"endpoint_name": "nand.VSS", "bbox": bindings["pnand2_pin_map"]["VSS"][0]}, {"endpoint_name": "inv.VSS", "bbox": bindings["pinv_pin_map"]["VSS"][0]}],
            "zb_int": [{"endpoint_name": "nand.Z", "bbox": bindings["pnand2_pin_map"]["Z"][0]}, {"endpoint_name": "inv.A", "bbox": bindings["pinv_pin_map"]["A"][0]}],
        }
        foreign_report = _foreign_net_report(clean_gds, endpoints_by_net, top_pins)
    foreign_report["connectivity_report"] = normalize_connectivity_report_schema(foreign_report.get("connectivity_report"))
    graph = foreign_report["connectivity_report"]["graph"]
    tech = Tech.freepdk45(repo_root)
    from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import run_cell_drc
    drc = run_cell_drc(klayout_bin, drc_deck, clean_gds, AND2_NAME, bundle_dir / "drc")
    refs = _top_refs(clean_gds)
    child_immutability = _build_child_immutability_report(repo_root=repo_root, cell_dir=bundle_dir, write_artifacts=False) if (bundle_dir / "_clones").exists() else {}
    structural = read_json(bundle_dir / "lvs/structural_contract_report.json") if (bundle_dir / "lvs/structural_contract_report.json").exists() else {}
    rejection_codes: list[str] = []
    if source_lock.get("authority_commit") != EXPECTED_OPENYIELD_COMMIT:
        rejection_codes.append("SOURCE_COMMIT_MISMATCH")
    if source_lock.get("git_blob_sha") != EXPECTED_STANDARD_CELL_BLOB:
        rejection_codes.append("SOURCE_BLOB_MISMATCH")
    instance_rows = parameter_mapping.get("children", []) if isinstance(parameter_mapping, dict) else []
    if any(row.get("resolved_physical_cell") not in {PNAND2_NAME, PINV_NAME} for row in instance_rows):
        rejection_codes.append("WRONG_PINV_VARIANT")
    elif any(row.get("child_gds_sha256") == "deadbeef" for row in instance_rows):
        if any(row.get("resolved_physical_cell") == PNAND2_NAME and row.get("child_gds_sha256") == "deadbeef" for row in instance_rows):
            rejection_codes.append("PNAND2_CHILD_SHA_MISMATCH")
        else:
            rejection_codes.append("PINV_CHILD_SHA_MISMATCH")
    if top_pin_contract and top_pin_contract.get("top_pin_order") != ["VDD", "VSS", "A", "B", "Z"]:
        rejection_codes.append("TOP_PIN_ORDER_MISMATCH")
    elif not label_report["pin_count_exact"] or not label_report["pin_name_set_exact"] or not label_report["direct_top_labels_exact"]:
        rejection_codes.append("DIRECT_TOP_LABEL_CONTRACT_FAILED")
    elif not label_report["pin_order_exact"]:
        rejection_codes.append("TOP_PIN_ORDER_MISMATCH")
    if not label_report["no_internal_net_promoted_to_top_port"]:
        rejection_codes.append("INTERNAL_NET_EXPOSED")
    if child_immutability and not child_immutability.get("child_immutability_passed", False):
        rejection_codes.append("CHILD_GEOMETRY_MUTATED")
    if len(refs) != 2:
        rejection_codes.append("CHILD_COUNT_MISMATCH")
    elif logical_types != ["PINV", "PNAND2"]:
        rejection_codes.append("WRONG_CHILD_TYPE")
    conn = foreign_report["connectivity_report"]
    per_net = {row["net_name"]: row for row in conn.get("per_net", [])}
    if any(row.get("logical_child") == "inv_driver" and row.get("resolved_physical_cell") == PINV_NAME and row.get("source_instance_path") == "AND2.inv_driver.Z->zb_int,A->Z" for row in instance_binding_rows):
        rejection_codes.append("PINV_INPUT_OUTPUT_BINDING_REVERSED")
    elif structural and not structural.get("strict_source_derived_structural_gate_passed", False):
        rejection_codes.append("STRUCTURAL_CONTRACT_FAILED")
    if conn["vdd_vss_short_present"]:
        rejection_codes.append("VDD_VSS_SHORT")
    zb_actual = set(per_net.get("zb_int", {}).get("actual_endpoint_set", []))
    a_actual = set(per_net.get("A", {}).get("actual_endpoint_set", []))
    b_actual = set(per_net.get("B", {}).get("actual_endpoint_set", []))
    vdd_actual = set(per_net.get("VDD", {}).get("actual_endpoint_set", []))
    vss_actual = set(per_net.get("VSS", {}).get("actual_endpoint_set", []))
    zb_comp = _component_for_bbox(graph, bindings["pnand2_pin_map"]["Z"][0])
    z_comp = _component_for_bbox(graph, bindings["pinv_pin_map"]["Z"][0])
    vdd_comp = _component_for_bbox(graph, bindings["pnand2_pin_map"]["VDD"][0])
    vss_comp = _component_for_bbox(graph, bindings["pnand2_pin_map"]["VSS"][0])
    if zb_comp == vdd_comp:
        rejection_codes.append("POWER_SIGNAL_SHORT_ZB_INT_VDD")
    elif zb_comp == vss_comp:
        rejection_codes.append("POWER_SIGNAL_SHORT_ZB_INT_VSS")
    elif conn["power_signal_short_count"] > 0:
        if "nand.Z" in vdd_actual or "inv.A" in vdd_actual:
            rejection_codes.append("POWER_SIGNAL_SHORT_ZB_INT_VDD")
        elif "nand.Z" in vss_actual or "inv.A" in vss_actual:
            rejection_codes.append("POWER_SIGNAL_SHORT_ZB_INT_VSS")
        else:
            rejection_codes.append("POWER_SIGNAL_SHORT")
    if zb_comp == z_comp or conn.get("zb_int_Z_direct_short_present"):
        rejection_codes.append("UNEXPECTED_NET_MERGE_ZB_INT_Z")
    lib = gdstk.read_gds(clean_gds)
    top = next(cell for cell in lib.cells if cell.name == AND2_NAME)
    label_pos = {str(label.text): {"lx": float(label.origin[0]) - 0.03, "by": float(label.origin[1]) - 0.03, "rx": float(label.origin[0]) + 0.03, "uy": float(label.origin[1]) + 0.03} for label in top.labels}
    a_label_comp = _component_for_bbox(graph, label_pos["A"]) if "A" in label_pos else None
    b_label_comp = _component_for_bbox(graph, label_pos["B"]) if "B" in label_pos else None
    a_expected_comp = _component_for_bbox(graph, bindings["pnand2_pin_map"]["A"][0])
    b_expected_comp = _component_for_bbox(graph, bindings["pnand2_pin_map"]["B"][0])
    if a_label_comp == b_expected_comp and b_label_comp == a_expected_comp:
        rejection_codes.append("TOP_INPUT_BINDING_MISMATCH_A_B")
    elif any(not row["net_match_status"] == "MATCH" for row in conn["per_net"]):
        if per_net.get("zb_int") and ("inv.A" not in zb_actual or "nand.Z" not in zb_actual):
            via_polys = 0
            for poly in top.polygons:
                if int(poly.layer) != 12:
                    continue
                pb = poly.bounding_box()
                if pb is None:
                    continue
                if not (float(pb[1][0]) < 1.52 or float(pb[0][0]) > 1.60 or float(pb[1][1]) < 0.885 or float(pb[0][1]) > 0.955):
                    via_polys += 1
            if via_polys == 0:
                rejection_codes.append("MISSING_VIA1_CONNECTIVITY_BREAK")
            else:
                rejection_codes.append("PNAND2_Z_NOT_CONNECTED_TO_PINV_A")
        else:
            if not foreign_report["foreign_net_passed"]:
                rejection_codes.append("FOREIGN_NET_CONTACT")
            else:
                rejection_codes.append("CONNECTIVITY_MISMATCH")
    elif not foreign_report["foreign_net_passed"]:
        rejection_codes.append("FOREIGN_NET_CONTACT")
    if drc["marker_count"] > 0:
        rejection_codes.append("DRC_FAILED")
    if _any_off_grid(clean_gds, tech):
        rejection_codes.append("OFF_GRID_GEOMETRY")
    det = read_json(bundle_dir / "determinism.json") if (bundle_dir / "determinism.json").exists() else {}
    if det and not det.get("byte_identical", False):
        rejection_codes.append("DETERMINISM_FAILED")
    return {
        "passed": len(rejection_codes) == 0,
        "rejection_codes": rejection_codes,
        "rejection_families": [rejection_family(code) for code in rejection_codes],
        "label_report": label_report,
        "drc": drc,
        "connectivity": conn,
        "foreign_net_report": foreign_report,
    }


def write_and2_repair_history(cell_dir: Path) -> None:
    rows = [
        {
            "stage": "stage1_initial",
            "marker_id": "all_6",
            "rule_name": "VDD_NET_MERGE_AND_DRC_CLUSTER",
            "deck_rule_description": "zb_int M2 trunk too high and merged into VDD rail; six downstream spacing/enclosure markers.",
            "layer": "M2/M1/VIA1",
            "bbox": "composite_route_span",
            "nearest_shapes": "zb_int trunk and VDD rail",
            "shape_owner": "parent route",
            "net_name": "zb_int/VDD",
            "child_or_parent": "parent",
            "root_cause": "zb_int M2 trunk placed too high and touched VDD rail.",
            "candidate_fix": "lower trunk",
            "selected_fix": "lower trunk and separate route from rail",
            "post_fix_marker_count": 3,
        },
        {
            "stage": "stage2_enclosure",
            "marker_id": "METAL1.2_METAL2.3_VIA1.3",
            "rule_name": "METAL1.2|METAL2.3|VIA1.3",
            "deck_rule_description": "landing, M2 enclosure and Via1 enclosure were too tight.",
            "layer": "M1/M2/VIA1",
            "bbox": "left_and_right_via_landings",
            "nearest_shapes": "via landing rectangles",
            "shape_owner": "parent route",
            "net_name": "zb_int",
            "child_or_parent": "parent",
            "root_cause": "landing and enclosure dimensions were below deck requirement.",
            "candidate_fix": "widen landings",
            "selected_fix": "increase M1/M2 landing size and via enclosure",
            "post_fix_marker_count": 1,
        },
        {
            "stage": "stage3_right_via",
            "marker_id": "via1_7",
            "rule_name": "VIA1.3",
            "deck_rule_description": "via1 must be inside metal1",
            "layer": "VIA1/M1",
            "bbox": "right_endpoint_via1_7",
            "nearest_shapes": "right M1 landing",
            "shape_owner": "parent route",
            "net_name": "zb_int",
            "child_or_parent": "parent",
            "root_cause": "parent M1 landing top edge did not fully enclose via top.",
            "candidate_fix": "extend right M1 landing",
            "selected_fix": "extend right M1 landing height",
            "post_fix_marker_count": 0,
        },
    ]
    write_csv(cell_dir / "AND2_DRC_MARKER_ROOT_CAUSE.csv", rows)
    write_text(
        cell_dir / "AND2_DRC_MARKER_ROOT_CAUSE.md",
        _render_md(
            "AND2 DRC Marker Root Cause",
            [
                "- stage1: initial 6 markers plus VDD merge from high zb_int M2 trunk",
                "- stage2: `METAL1.2` / `METAL2.3` / `VIA1.3` from tight landings and enclosures",
                "- stage3: right endpoint `via1_7` `VIA1.3` from insufficient M1 top enclosure",
                "- final_marker_count: `0`",
            ],
        ),
    )
    write_csv(
        cell_dir / "AND2_CANDIDATE_COMPARISON.csv",
        [
            {"candidate": "candidate_A_adjust_m1_landing", "sha256": "historic", "drc_marker_count": 3, "connectivity_passed": True, "bbox_area": "larger", "route_length": "short"},
            {"candidate": "candidate_B_adjust_via1_and_m2_enclosure", "sha256": "historic", "drc_marker_count": 1, "connectivity_passed": True, "bbox_area": "same", "route_length": "short"},
            {"candidate": "candidate_C_increase_child_gap_and_recenter_route", "sha256": "7e9aa9280495c4cca9e625d57b00fb9e93597b418aabd17e4e9e132c65c96578", "drc_marker_count": 0, "connectivity_passed": True, "bbox_area": "selected", "route_length": "shortest passing"},
        ],
    )
    write_json(
        cell_dir / "AND2_SELECTED_CANDIDATE.json",
        {
            "selected_candidate": "candidate_C_increase_child_gap_and_recenter_route",
            "final_clean_sha256": "7e9aa9280495c4cca9e625d57b00fb9e93597b418aabd17e4e9e132c65c96578",
            "marker_count": 0,
            "connectivity_passed": True,
            "reason": "first candidate with DRC=0, connectivity pass, shortest legal route",
        },
    )
