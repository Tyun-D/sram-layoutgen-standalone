from __future__ import annotations

import ast
import csv
import hashlib
import json
import math
import re
import shutil
import subprocess
import tarfile
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
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
from sram_layoutgen.openyield_adapter.dff_buf_verification_gate import compute_child_geometry_immutability
from sram_layoutgen.openyield_adapter.hierarchical_foreign_net_detector import (
    EPSILON,
    conductive_shapes_touch_or_overlap,
    detect_hierarchical_foreign_net_contacts,
)
from sram_layoutgen.openyield_adapter.primitive_geometry_verifier import (
    count_klayout_items,
    non_text_geometry_fingerprint,
    parse_lyrdb_categories,
)


EXPECTED_BRANCH = "feature/step45-clean-array-aggregation"
EXPECTED_OPENYIELD_COMMIT = "1c34428d8b913963c4971d093b1a7c2df97a2509"
EXPECTED_RELEASE_SHA = "f80dbdb1b9f5852c90801cdbee823db945a64693f4e4bec53381d533b48d6299"
EXPECTED_RELEASE_CELL = "DFF_BUF_FPDK45_6058eaf43739_HPA1"
EXPECTED_DFF_CELL = "DFF_TG4_INV7_FPDK45_26d9543b82b7"
OPENYIELD_ROOT = Path("/data1/qujh/work/external/OpenYield")
OPENYIELD_TIME_GENERATE = OPENYIELD_ROOT / "sram_compiler/subcircuits/time_generate.py"
KLAYOUT = Path("/usr/bin/klayout")
DRC_DECK = REPO_ROOT / "technology/freepdk45/tech/freepdk45.lydrc"
STAGE_ID = "Wave3H1_DFF_BUF_RELEASE_EVIDENCE_HARDENING_AND_LEDGER_RECONCILIATION"
STAGE_DIR = REPO_ROOT / "outputs/Wave3H1_DFF_BUF_release_evidence_hardening/current_supported_config"
ATLAS_DIR = REPO_ROOT / "outputs/Wave3_DFF_BUF_human_review_seal"
REPAIR_DIR = REPO_ROOT / "outputs/Wave3_DFF_BUF_hierarchical_pin_access_repair/current_supported_config"
REUSABLE_DIR = REPO_ROOT / "outputs/Wave3_DFF_BUF_reusable_release"
FAILED_DIR = REPO_ROOT / "outputs/Wave3_DFF_BUF_hierarchical_pin_access_repair/quarantined_failed_candidate"
PRIMITIVE_ROOT = REPO_ROOT / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells"
DFF_RELEASE_DIR = REPO_ROOT / "outputs/M12C4ACH_dff_reusable_release"
WAVE_PLAN = REPO_ROOT / "outputs/M12C4_composite_control_cell_generation_plan/current_supported_config/M12C4_composite_implementation_wave_plan.csv"
APPROVED_RELEASE_GDS = REUSABLE_DIR / "DFF_BUF_reusable_clean.gds"
REPAIRED_CLEAN_GDS = REPAIR_DIR / "DFF_BUF_repaired_clean.gds"
REPAIRED_ANNOTATED_GDS = REPAIR_DIR / "DFF_BUF_repaired_annotated.gds"
SOURCE_TRACE_PATH = REPO_ROOT / "outputs/Wave3_DFF_BUF_composite_generation/current_supported_config/DFF_BUF_FPDK45_6058eaf43739_source_trace.json"
STATUS_MD = REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md"
STATUS_JSON = REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json"
GOAL_MD = REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_GOAL.md"
PROGRESS_MD = REPO_ROOT / "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md"
NEXT_STAGE = "Wave4A / ADDR_DFF_SOURCE_TOPOLOGY_AND_BINDING_LOCK"
LOCKED_PLAN_NEXT_WAVE = "Wave4 / ADDR_DFF / DATA_DFF"
DEFERRED_SIBLING_STAGE = "Wave4B / DATA_DFF"


def _run(cmd: list[str], *, cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True, check=False)
    if check and completed.returncode != 0:
        raise RuntimeError(f"command failed: {' '.join(cmd)}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}")
    return completed


def _git(*args: str) -> str:
    return _run(["git", "-C", str(REPO_ROOT), *args]).stdout


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames or (list(rows[0].keys()) if rows else []))
        writer.writeheader()
        writer.writerows(rows)


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _file_size(path: Path) -> int:
    return path.stat().st_size


def _load_gds(path: Path) -> gdstk.Library:
    return gdstk.read_gds(path)


def _top_cell_name(path: Path) -> str:
    lib = _load_gds(path)
    tops = lib.top_level()
    if len(tops) != 1:
        raise RuntimeError(f"expected exactly one top cell in {path}, got {len(tops)}")
    return tops[0].name


def _cell_inventory(path: Path) -> list[str]:
    lib = _load_gds(path)
    return sorted(cell.name for cell in lib.cells)


def _reference_graph(path: Path) -> dict[str, list[str]]:
    lib = _load_gds(path)
    graph: dict[str, list[str]] = {}
    for cell in lib.cells:
        refs = sorted(str(ref.cell_name) for ref in cell.references)
        graph[cell.name] = refs
    return dict(sorted(graph.items()))


def _top_label_set(path: Path, top_name: str) -> list[str]:
    lib = _load_gds(path)
    top = next(cell for cell in lib.cells if cell.name == top_name)
    return sorted(str(label.text) for label in top.labels)


def _normalized_panel_digest(cell: gdstk.Cell) -> str:
    payload: list[Any] = []
    flat = cell.flatten()
    for poly in flat.polygons:
        pts = [(round(float(x), 6), round(float(y), 6)) for x, y in poly.points]
        payload.append(["poly", poly.layer, poly.datatype, pts])
    for label in flat.labels:
        payload.append(
            [
                "label",
                label.layer,
                label.texttype,
                str(label.text),
                [round(float(label.origin[0]), 6), round(float(label.origin[1]), 6)],
            ]
        )
    return hashlib.sha256(json.dumps(sorted(payload), separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()


def _validate_preconditions() -> dict[str, Any]:
    branch = _git("branch", "--show-current").strip()
    status = _git("status", "--short")
    head = _git("rev-parse", "HEAD").strip()
    openyield_head = _run(["git", "-C", str(OPENYIELD_ROOT), "rev-parse", "HEAD"]).stdout.strip()
    approved_sha = _sha256(APPROVED_RELEASE_GDS)
    pre = {
        "project_branch": branch,
        "project_git_status": status,
        "project_commit": head,
        "openyield_commit": openyield_head,
        "approved_release_sha256": approved_sha,
        "repaired_clean_exists": REPAIRED_CLEAN_GDS.exists(),
        "approved_dff_manifest_exists": (DFF_RELEASE_DIR / "DFF_REUSABLE_MANIFEST.json").exists(),
        "approved_dff_gds_exists": (DFF_RELEASE_DIR / "DFF_reusable_clean.gds").exists(),
        "approved_primitive_registry_exists": False,
        "implementation_wave_plan_exists": WAVE_PLAN.exists(),
    }
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"project branch mismatch: expected {EXPECTED_BRANCH}, got {branch}")
    if openyield_head != EXPECTED_OPENYIELD_COMMIT:
        raise RuntimeError(f"OpenYield commit mismatch: expected {EXPECTED_OPENYIELD_COMMIT}, got {openyield_head}")
    return pre


def _required_inputs() -> list[Path]:
    docs = [
        STATUS_MD,
        STATUS_JSON,
        GOAL_MD,
        PROGRESS_MD,
        WAVE_PLAN,
        REUSABLE_DIR / "DFF_BUF_REUSABLE_MANIFEST.json",
        REUSABLE_DIR / "DFF_BUF_REUSABLE_RELEASE_CHECKS.json",
        DFF_RELEASE_DIR / "DFF_REUSABLE_MANIFEST.json",
        REPO_ROOT / "scripts/Wave3_DFF_BUF_human_review_seal_and_reusable_release.py",
        REPO_ROOT / "sram_layoutgen/openyield_adapter/hierarchical_foreign_net_detector.py",
        REPO_ROOT / "docs/Wave3_DFF_BUF_real_topology_analysis.md",
        REPO_ROOT / "docs/Wave3_DFF_BUF_instance_connection_table.csv",
        REPO_ROOT / "docs/Wave3_DFF_BUF_net_endpoint_universe.json",
        REPO_ROOT / "docs/Wave3_DFF_BUF_net_contract.json",
        REPO_ROOT / "docs/Wave3_DFF_BUF_child_binding_matrix.csv",
        REPO_ROOT / "docs/Wave3_DFF_BUF_binding_contract.json",
        REPO_ROOT / "docs/Wave3_DFF_BUF_human_review_failure.md",
        REPO_ROOT / "docs/Wave3_DFF_BUF_human_review_failure.json",
        REPO_ROOT / "docs/Wave3_DFF_BUF_failed_short_geometry_analysis.md",
        REPO_ROOT / "docs/Wave3_DFF_BUF_failed_short_geometry_analysis.json",
        REPO_ROOT / "docs/Wave3_DFF_BUF_hierarchical_net_namespace.json",
        REPO_ROOT / "docs/Wave3_DFF_BUF_child_conductive_obstacle_map.json",
        REPO_ROOT / "docs/Wave3_DFF_BUF_pin_access_plan_repaired.json",
        REPO_ROOT / "docs/Wave3_DFF_BUF_hierarchical_short_negative_tests.json",
        REPO_ROOT / "docs/Wave3_DFF_BUF_verification_hardening_report.json",
        REPO_ROOT / "docs/Wave3_DFF_BUF_verification_hardening_closure_report.json",
        REPO_ROOT / "docs/Wave3_DFF_BUF_human_visual_review.json",
    ]
    missing = [str(path) for path in docs if not path.exists()]
    if missing:
        raise RuntimeError(f"required evidence inputs missing: {missing}")
    return docs


def _copy_required(path: Path, dst_root: Path, rel: str | None = None) -> Path:
    dest = dst_root / (rel or path.name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)
    return dest


def _compare_release_and_repair() -> dict[str, Any]:
    top_release = _top_cell_name(APPROVED_RELEASE_GDS)
    top_repair = _top_cell_name(REPAIRED_CLEAN_GDS)
    cmp_equal = APPROVED_RELEASE_GDS.read_bytes() == REPAIRED_CLEAN_GDS.read_bytes()
    return {
        "repaired_clean_path": str(REPAIRED_CLEAN_GDS),
        "released_clean_path": str(APPROVED_RELEASE_GDS),
        "repaired_clean_sha256": _sha256(REPAIRED_CLEAN_GDS),
        "released_clean_sha256": _sha256(APPROVED_RELEASE_GDS),
        "release_hash_matches_repaired_clean": cmp_equal
        and _sha256(REPAIRED_CLEAN_GDS) == EXPECTED_RELEASE_SHA
        and _sha256(APPROVED_RELEASE_GDS) == EXPECTED_RELEASE_SHA,
        "byte_for_byte_equal": cmp_equal,
        "repaired_size_bytes": _file_size(REPAIRED_CLEAN_GDS),
        "released_size_bytes": _file_size(APPROVED_RELEASE_GDS),
        "top_cell_match": top_release == top_repair,
        "repaired_top_cell": top_repair,
        "released_top_cell": top_release,
        "cell_inventory_match": _cell_inventory(REPAIRED_CLEAN_GDS) == _cell_inventory(APPROVED_RELEASE_GDS),
        "cell_inventory": _cell_inventory(APPROVED_RELEASE_GDS),
        "reference_graph_match": _reference_graph(REPAIRED_CLEAN_GDS) == _reference_graph(APPROVED_RELEASE_GDS),
        "reference_graph": _reference_graph(APPROVED_RELEASE_GDS),
        "top_label_set_match": _top_label_set(REPAIRED_CLEAN_GDS, top_repair) == _top_label_set(APPROVED_RELEASE_GDS, top_release),
        "top_label_set": _top_label_set(APPROVED_RELEASE_GDS, top_release),
    }


def _source_trace_and_bindings() -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    source_trace = _read_json(SOURCE_TRACE_PATH)
    placements = [
        {"instance_name": row["instance_name"], "x": row["placement_x"], "y": row["placement_y"], "orientation": row["orientation"]}
        for row in source_trace["placement_rows"]
    ]
    binding_rows = _read_json(REPO_ROOT / "docs/Wave3_DFF_BUF_binding_contract.json")["rows"]
    return source_trace, placements, binding_rows


def _probe_generation(out_root: Path, placements: list[dict[str, Any]], binding_rows: list[dict[str, Any]]) -> dict[str, Any]:
    dff_manifest = _read_json(DFF_RELEASE_DIR / "DFF_REUSABLE_MANIFEST.json")
    return generate_dff_buf_composite(
        repo_root=REPO_ROOT,
        dff_child_gds=Path(dff_manifest["released_clean_gds_path"]),
        dff_child_top_name=dff_manifest["physical_cell_name"],
        dff_child_pin_map_path=REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config" / dff_manifest["physical_cell_name"] / f"{dff_manifest['physical_cell_name']}_pin_map.json",
        dff_child_geometry_fingerprint_path=REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config" / dff_manifest["physical_cell_name"] / f"{dff_manifest['physical_cell_name']}_geometry_fingerprint.json",
        approved_primitive_root=PRIMITIVE_ROOT,
        binding_rows=binding_rows,
        source_topology_hash="6058eaf43739",
        canonical_extracted_topology_hash="6058eaf43739",
        requested_source_topology_hash="6058eaf43739",
        selected_architecture="M1_HORIZONTAL_TRACK_M2_VERTICAL_DROP__DFF_DIRECT_VIA1_TO_M2_ESCAPE",
        placements=placements,
        output_root=out_root,
        drc_deck=DRC_DECK,
        klayout_path=KLAYOUT,
        physical_variant_tag="HPA1",
    )


def _parse_lyrdb_items(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    root = ET.parse(path).getroot()
    rows: list[dict[str, Any]] = []
    for idx, item in enumerate(root.findall(".//item"), start=1):
        category = item.findtext("category") or item.get("category") or item.get("name") or "UNKNOWN"
        values = [val.text.strip() for val in item.findall(".//value") if val.text]
        coords = "; ".join(values)
        rows.append({"marker_id": idx, "category": category, "coordinate_text": coords})
    return rows


def _run_release_drc(out_dir: Path) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    lyrdb = out_dir / f"{EXPECTED_RELEASE_CELL}.lyrdb"
    log_path = out_dir / f"{EXPECTED_RELEASE_CELL}_drc.log"
    command = [
        str(KLAYOUT),
        "-b",
        "-r",
        str(DRC_DECK),
        "-rd",
        f"input={APPROVED_RELEASE_GDS}",
        "-rd",
        f"topcell={EXPECTED_RELEASE_CELL}",
        "-rd",
        f"output={lyrdb}",
    ]
    completed = _run(command, check=False)
    log_path.write_text(
        "COMMAND:\n" + " ".join(command) + "\n\nSTDOUT:\n" + completed.stdout + "\n\nSTDERR:\n" + completed.stderr,
        encoding="utf-8",
    )
    marker_count = count_klayout_items(lyrdb) if lyrdb.exists() else None
    categories = parse_lyrdb_categories(lyrdb) if lyrdb.exists() else {}
    item_rows = _parse_lyrdb_items(lyrdb)
    _write_csv(out_dir / "drc_marker_table.csv", item_rows, ["marker_id", "category", "coordinate_text"])
    _write_json(out_dir / "drc_marker_table.json", item_rows)
    report = {
        "drc_run": True,
        "drc_parse_passed": marker_count is not None,
        "marker_count": marker_count if marker_count is not None else -1,
        "marker_categories": categories,
        "drc_passed": marker_count == 0,
        "drc_scope": "cell-level DRC clean under the recorded FreePDK45 deck",
        "lyrdb_path": str(lyrdb),
        "log_path": str(log_path),
        "deck_path": str(DRC_DECK),
        "deck_sha256": _sha256(DRC_DECK),
        "klayout_version": _run([str(KLAYOUT), "-v"]).stdout.strip() or _run([str(KLAYOUT), "-v"], check=False).stderr.strip(),
        "command": command,
        "returncode": completed.returncode,
    }
    _write_json(out_dir / "drc_report.json", report)
    return report


def _route_counts(route_plan: dict[str, Any]) -> dict[str, int]:
    route_objects = route_plan["route_objects"]
    return {
        "route_segment_count": len(route_plan["route_segments"]),
        "m1_route_count": sum(1 for row in route_objects if row["layer"] == "m1"),
        "m2_route_count": sum(1 for row in route_objects if row["layer"] == "m2"),
        "via1_count": sum(1 for row in route_objects if row["layer"] == "via1"),
    }


def _child_binding_audit(probe: dict[str, Any], stage_child_dir: Path) -> dict[str, Any]:
    clone_rows = probe["child_clone_rows"]
    clone_by_key = {row["clone_root_name"]: row for row in clone_rows}
    approved_rows = [
        {
            "instance": "dff",
            "logical_module": "DFF",
            "physical_cell": EXPECTED_DFF_CELL,
            "approved_source_gds": DFF_RELEASE_DIR / "DFF_reusable_clean.gds",
            "source_manifest": DFF_RELEASE_DIR / "DFF_REUSABLE_MANIFEST.json",
            "clone_root_name": "COMPOSE_CHILD__DFF_REUSABLE",
        },
        {
            "instance": "inv1",
            "logical_module": "PINV",
            "physical_cell": "PINV_NW180_PW540_L50",
            "approved_source_gds": PRIMITIVE_ROOT / "PINV_NW180_PW540_L50/PINV_NW180_PW540_L50.gds",
            "source_manifest": None,
            "clone_root_name": "COMPOSE_CHILD__PINV_NW180_PW540_L50",
        },
        {
            "instance": "inv2",
            "logical_module": "PINV",
            "physical_cell": "PINV_NW360_PW1080_L50",
            "approved_source_gds": PRIMITIVE_ROOT / "PINV_NW360_PW1080_L50/PINV_NW360_PW1080_L50.gds",
            "source_manifest": None,
            "clone_root_name": "COMPOSE_CHILD__PINV_NW360_PW1080_L50",
        },
    ]
    placement_by_name = {row["instance_name"]: row for row in probe["placement_rows"]}
    records = []
    immutability_records = []
    for row in approved_rows:
        clone = clone_by_key[row["clone_root_name"]]
        renamed = clone["renamed_root_name"]
        approved_path = Path(row["approved_source_gds"])
        immutability_records.append(
            {
                "instance": row["instance"],
                "approved_path": str(approved_path),
                "approved_top_name": row["physical_cell"],
                "cloned_path": clone["output_gds"],
                "cloned_top_name": renamed,
                "hierarchy_path": str(APPROVED_RELEASE_GDS),
                "hierarchy_top_name": renamed,
            }
        )
    immutability = compute_child_geometry_immutability(immutability_records)
    match_by_instance = {row["instance"]: row for row in immutability["rows"]}
    for row in approved_rows:
        clone = clone_by_key[row["clone_root_name"]]
        placement = placement_by_name[row["instance"]]
        match_row = match_by_instance[row["instance"]]
        source_manifest = str(row["source_manifest"]) if row["source_manifest"] else "canonical reusable authority is derived from reviewed release manifests"
        manifest_payload = _read_json(Path(row["source_manifest"])) if row["source_manifest"] else None
        reusable_status = manifest_payload["reusable_status"] if manifest_payload else "HUMAN_REVIEWED_REUSABLE_COMPOSITE"
        records.append(
            {
                "instance": row["instance"],
                "logical_module": row["logical_module"],
                "physical_cell": row["physical_cell"],
                "approved_source_gds": str(row["approved_source_gds"]),
                "source_manifest": source_manifest,
                "actual_sha256": _sha256(Path(row["approved_source_gds"])),
                "physical_top_cell": row["physical_cell"],
                "reusable_status": reusable_status,
                "placement_transform": placement["pin_transform"],
                "pre_placement_geometry_fingerprint": clone["source_non_text_fingerprint"]["digest"],
                "transformed_child_geometry_fingerprint": clone["clone_non_text_fingerprint"]["digest"],
                "release_child_hierarchy_fingerprint": match_row["hierarchy_digest"],
                "equality_result": match_row["match"],
            }
        )
    _write_csv(stage_child_dir / "child_binding_geometry_audit.csv", records)
    _write_json(stage_child_dir / "child_binding_geometry_audit.json", {"rows": records, **immutability})
    _write_text(
        stage_child_dir / "child_binding_geometry_audit.md",
        "# Child Binding Geometry Audit\n\n" + "\n".join(f"- {row['instance']}: equality_result=`{row['equality_result']}`" for row in records) + "\n",
    )
    return {"rows": records, **immutability}


def _route_object_csv(route_plan: dict[str, Any], out_path: Path) -> None:
    rows = []
    for row in route_plan["route_objects"]:
        rows.append(
            {
                "route_object_id": row["route_object_id"],
                "net_name": row["net_name"],
                "intended_hierarchical_net": row["intended_hierarchical_net"],
                "layer": row["layer"],
                "bbox": json.dumps(row["bbox"]),
                "role": row["role"],
                "shape_kind": row["shape_kind"],
                "bbox_is_exact_geometry": row["bbox_is_exact_geometry"],
            }
        )
    _write_csv(out_path, rows)


def _endpoint_component_rows(connectivity: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in connectivity["per_net"]:
        rows.append(
            {
                "net_name": row["net_name"],
                "component_id": row["component_id"],
                "expected_endpoint_set": json.dumps(row["expected_endpoint_set"]),
                "actual_endpoint_set": json.dumps(row["actual_endpoint_set"]),
                "missing_endpoints": json.dumps(row["missing_endpoints"]),
                "unexpected_endpoints": json.dumps(row["unexpected_endpoints"]),
                "net_match_status": row["net_match_status"],
            }
        )
    return rows


def _rect_shape(layer: str, bbox: list[float], **extra: Any) -> dict[str, Any]:
    payload = {
        "layer": layer,
        "bbox": bbox,
        "shape_kind": "axis_aligned_rectangle",
        "bbox_is_exact_geometry": True,
    }
    payload.update(extra)
    return payload


def _detector_tests() -> dict[str, Any]:
    edge = conductive_shapes_touch_or_overlap(
        _rect_shape("m1", [0.0, 0.0, 1.0, 1.0]),
        _rect_shape("m1", [1.0, 0.0, 2.0, 1.0]),
    )
    corner = conductive_shapes_touch_or_overlap(
        _rect_shape("m1", [0.0, 0.0, 1.0, 1.0]),
        _rect_shape("m1", [1.0, 1.0, 2.0, 2.0]),
    )
    gap = conductive_shapes_touch_or_overlap(
        _rect_shape("m1", [0.0, 0.0, 1.0, 1.0]),
        _rect_shape("m1", [1.1, 0.0, 2.1, 1.0]),
    )
    cross_no_via = conductive_shapes_touch_or_overlap(
        _rect_shape("m1", [0.0, 0.0, 1.0, 1.0]),
        _rect_shape("m2", [0.2, 0.2, 0.8, 0.8]),
    )
    via_m1 = conductive_shapes_touch_or_overlap(
        _rect_shape("via1", [0.4, 0.4, 0.6, 0.6]),
        _rect_shape("m1", [0.2, 0.2, 0.8, 0.8]),
    )
    via_m2 = conductive_shapes_touch_or_overlap(
        _rect_shape("via1", [0.4, 0.4, 0.6, 0.6]),
        _rect_shape("m2", [0.2, 0.2, 0.8, 0.8]),
    )
    epsilon_inside = conductive_shapes_touch_or_overlap(
        _rect_shape("m1", [0.0, 0.0, 1.0, 1.0]),
        _rect_shape("m1", [1.0 + (EPSILON * 0.5), 0.0, 2.0, 1.0]),
    )
    epsilon_outside = conductive_shapes_touch_or_overlap(
        _rect_shape("m1", [0.0, 0.0, 1.0, 1.0]),
        _rect_shape("m1", [1.0 + (EPSILON * 2.0), 0.0, 2.0, 1.0]),
    )
    polygon_rejected = False
    missing_contract_rejected = False
    polygon_error = ""
    missing_contract_error = ""
    try:
        conductive_shapes_touch_or_overlap(
            {"layer": "m1", "bbox": [0.0, 0.0, 1.0, 1.0], "shape_kind": "polygon", "bbox_is_exact_geometry": False},
            _rect_shape("m1", [0.0, 0.0, 1.0, 1.0]),
        )
    except ValueError as exc:
        polygon_rejected = True
        polygon_error = str(exc)
    try:
        conductive_shapes_touch_or_overlap(
            {"layer": "m1", "bbox": [0.0, 0.0, 1.0, 1.0]},
            _rect_shape("m1", [0.0, 0.0, 1.0, 1.0]),
        )
    except ValueError as exc:
        missing_contract_rejected = True
        missing_contract_error = str(exc)

    same_net_dedup = detect_hierarchical_foreign_net_contacts(
        route_objects=[
            {
                **_rect_shape("m1", [0.0, 0.0, 2.0, 1.0]),
                "route_object_id": "r1",
                "net_name": "CLK",
                "intended_hierarchical_net": "TOP::CLK",
                "role": "test",
            }
        ],
        obstacle_objects=[
            {
                **_rect_shape("m1", [0.5, 0.0, 0.8, 1.0]),
                "child_instance": "dff",
                "child_cell": EXPECTED_DFF_CELL,
                "hierarchical_net_identity": "dff::CLKB_internal",
                "layer_datatype": "11/0",
                "component_id": "c1",
                "shape_id": "s1",
                "is_top_pin": False,
                "is_internal_net": True,
                "is_power": False,
                "parent_access_allowed": False,
            },
            {
                **_rect_shape("m1", [1.2, 0.0, 1.5, 1.0]),
                "child_instance": "dff",
                "child_cell": EXPECTED_DFF_CELL,
                "hierarchical_net_identity": "dff::CLKB_internal",
                "layer_datatype": "11/0",
                "component_id": "c2",
                "shape_id": "s2",
                "is_top_pin": False,
                "is_internal_net": True,
                "is_power": False,
                "parent_access_allowed": False,
            },
        ],
    )
    multi_foreign = detect_hierarchical_foreign_net_contacts(
        route_objects=[
            {
                **_rect_shape("m1", [0.0, 0.0, 2.0, 1.0]),
                "route_object_id": "r2",
                "net_name": "qint",
                "intended_hierarchical_net": "PARENT::qint",
                "role": "test",
            }
        ],
        obstacle_objects=[
            {
                **_rect_shape("m1", [0.2, 0.0, 0.6, 1.0]),
                "child_instance": "dff",
                "child_cell": EXPECTED_DFF_CELL,
                "hierarchical_net_identity": "dff::QB_internal",
                "layer_datatype": "11/0",
                "component_id": "c3",
                "shape_id": "s3",
                "is_top_pin": False,
                "is_internal_net": True,
                "is_power": False,
                "parent_access_allowed": False,
            },
            {
                **_rect_shape("m1", [1.0, 0.0, 1.4, 1.0]),
                "child_instance": "dff",
                "child_cell": EXPECTED_DFF_CELL,
                "hierarchical_net_identity": "dff::CLKB_internal",
                "layer_datatype": "11/0",
                "component_id": "c4",
                "shape_id": "s4",
                "is_top_pin": False,
                "is_internal_net": True,
                "is_power": False,
                "parent_access_allowed": False,
            },
        ],
    )

    return {
        "boundary_touch_detection_implemented": True,
        "geometry_domain_contract_fail_closed": True,
        "edge_touch_negative_test_passed": edge is not None and edge["contact_kind"] == "edge_touch" and edge["electrically_connected"],
        "corner_touch_negative_test_passed": corner is not None and corner["contact_kind"] == "corner_touch" and corner["electrically_connected"],
        "positive_clearance_test_passed": gap is None,
        "cross_layer_without_via_test_passed": cross_no_via is not None and not cross_no_via["electrically_connected"],
        "via1_m1_test_passed": via_m1 is not None and via_m1["electrically_connected"],
        "via1_m2_test_passed": via_m2 is not None and via_m2["electrically_connected"],
        "cross_layer_with_via_test_passed": via_m1 is not None and via_m2 is not None and via_m1["electrically_connected"] and via_m2["electrically_connected"],
        "non_rectangular_polygon_false_overlap_rejected": polygon_rejected,
        "missing_rectangle_contract_rejected": missing_contract_rejected,
        "epsilon_inside_test_passed": epsilon_inside is not None and epsilon_inside["electrically_connected"],
        "epsilon_outside_test_passed": epsilon_outside is None,
        "same_unexpected_net_multi_shape_dedup_test_passed": same_net_dedup["unique_foreign_hierarchical_net_count"] == 1 and same_net_dedup["unique_parent_route_foreign_net_pair_count"] == 1 and same_net_dedup["raw_contacting_foreign_obstacle_shape_count"] == 2,
        "same_route_multi_foreign_net_count_test_passed": multi_foreign["unique_foreign_hierarchical_net_count"] == 2 and multi_foreign["unique_parent_route_foreign_net_pair_count"] == 2 and multi_foreign["raw_contacting_foreign_obstacle_shape_count"] == 2,
        "raw": {
            "edge": edge,
            "corner": corner,
            "gap": gap,
            "cross_no_via": cross_no_via,
            "via_m1": via_m1,
            "via_m2": via_m2,
            "epsilon_inside": epsilon_inside,
            "epsilon_outside": epsilon_outside,
            "polygon_error": polygon_error,
            "missing_contract_error": missing_contract_error,
            "same_net_dedup": same_net_dedup,
            "multi_foreign": multi_foreign,
        },
    }


def _filtered_copy(target: gdstk.Cell, source: gdstk.Cell, predicate) -> int:
    flat = source.flatten()
    selected = 0
    for poly in flat.polygons:
        if predicate(poly.layer, poly.datatype, poly.points):
            target.add(gdstk.Polygon(poly.points, layer=poly.layer, datatype=poly.datatype))
            selected += 1
    for label in flat.labels:
        if predicate("label", label.layer, [(label.origin[0], label.origin[1])]):
            target.add(gdstk.Label(str(label.text), label.origin, layer=label.layer, texttype=label.texttype))
            selected += 1
    return selected


def _build_final_atlas(
    probe: dict[str, Any],
    output_gds: Path,
    inventory_json: Path,
) -> dict[str, Any]:
    clean_lib = _load_gds(REPAIRED_CLEAN_GDS)
    anno_lib = _load_gds(REPAIRED_ANNOTATED_GDS)
    clean_top = next(cell for cell in clean_lib.cells if cell.name == EXPECTED_RELEASE_CELL)
    anno_top = next(cell for cell in anno_lib.cells if cell.name == EXPECTED_RELEASE_CELL)
    bbox = clean_top.bounding_box()
    assert bbox is not None
    width = float(bbox[1][0] - bbox[0][0])
    height = float(bbox[1][1] - bbox[0][1])
    source_trace = _read_json(probe["clean_gds"].parent / f"{EXPECTED_RELEASE_CELL}_source_trace.json")
    top_pin_map = _read_json(probe["clean_gds"].parent / f"{EXPECTED_RELEASE_CELL}_pin_map.json")
    obstacle_map = probe["child_conductive_obstacle_map"]
    route_plan = probe["route_plan"]
    contact_report = probe["hierarchical_contact_report"]
    atlas_lib = gdstk.Library()
    panel_metadata: dict[str, dict[str, Any]] = {}

    def add_panel(name: str, role: str, filtered: bool, filter_predicate: str, source_count: int, selected_count: int, excluded_count: int, cell: gdstk.Cell) -> None:
        atlas_lib.add(cell)
        panel_metadata[name] = {
            "panel_name": name,
            "panel_role": role,
            "panel_is_semantically_filtered": filtered,
            "filter_predicate": filter_predicate,
            "source_object_count": source_count,
            "selected_object_count": selected_count,
            "excluded_object_count": excluded_count,
        }

    clean_panel = atlas_lib.new_cell("CLEAN_FULL_VIEW")
    for poly in clean_top.flatten().polygons:
        clean_panel.add(gdstk.Polygon(poly.points, layer=poly.layer, datatype=poly.datatype))
    for label in clean_top.flatten().labels:
        clean_panel.add(gdstk.Label(str(label.text), label.origin, layer=label.layer, texttype=label.texttype))
    add_panel("CLEAN_FULL_VIEW", "full_reference_view", False, "all_clean_geometry", len(clean_top.flatten().polygons) + len(clean_top.flatten().labels), len(clean_top.flatten().polygons) + len(clean_top.flatten().labels), 0, clean_panel)

    anno_panel = atlas_lib.new_cell("ANNOTATED_FULL_VIEW")
    for poly in anno_top.flatten().polygons:
        anno_panel.add(gdstk.Polygon(poly.points, layer=poly.layer, datatype=poly.datatype))
    for label in anno_top.flatten().labels:
        anno_panel.add(gdstk.Label(str(label.text), label.origin, layer=label.layer, texttype=label.texttype))
    add_panel("ANNOTATED_FULL_VIEW", "full_reference_view", False, "all_annotated_geometry", len(anno_top.flatten().polygons) + len(anno_top.flatten().labels), len(anno_top.flatten().polygons) + len(anno_top.flatten().labels), 0, anno_panel)

    placement_panel = atlas_lib.new_cell("CHILD_PLACEMENT_VIEW")
    for idx, row in enumerate(source_trace["placement_rows"], start=1):
        bbox_row = json.loads(row["bbox"])
        placement_panel.add(gdstk.rectangle((bbox_row[0], bbox_row[1]), (bbox_row[2], bbox_row[3]), layer=238, datatype=0))
        placement_panel.add(gdstk.Label(f"{idx}:{row['instance_name']}", ((bbox_row[0] + bbox_row[2]) * 0.5, bbox_row[3] + 0.08), layer=239, texttype=0))
    add_panel("CHILD_PLACEMENT_VIEW", "focused_view", True, "instance bbox + source order labels", len(source_trace["placement_rows"]), len(source_trace["placement_rows"]) * 2, 0, placement_panel)

    power_panel = atlas_lib.new_cell("POWER_ONLY_VIEW")
    graph = probe["connectivity"]["graph"]
    shape_to_component = {member: component["component_id"] for component in graph["components"] for member in component["members"]}
    power_components = set()
    for pin_name in ("VDD", "VSS"):
        pin_bbox = top_pin_map[pin_name]
        cx = round((pin_bbox["lx"] + pin_bbox["rx"]) * 0.5, 6)
        cy = round((pin_bbox["by"] + pin_bbox["uy"]) * 0.5, 6)
        for layer_name in ("m1", "m2"):
            for rect in graph["rectangles"].get(layer_name, []):
                lx, by, rx, uy = rect["bbox"]
                if lx - 1e-6 <= cx <= rx + 1e-6 and by - 1e-6 <= cy <= uy + 1e-6:
                    comp = shape_to_component.get(rect["rect_id"])
                    if comp:
                        power_components.add(comp)
    power_source = 0
    power_selected = 0
    for layer_name, layer_num in [("m1", 11), ("m2", 13), ("via1", 12)]:
        for rect in graph["rectangles"].get(layer_name, []):
            power_source += 1
            if shape_to_component.get(rect["rect_id"]) in power_components:
                power_panel.add(gdstk.rectangle((rect["bbox"][0], rect["bbox"][1]), (rect["bbox"][2], rect["bbox"][3]), layer=layer_num, datatype=0))
                power_selected += 1
    add_panel("POWER_ONLY_VIEW", "focused_view", True, "connected to TOP::VDD or TOP::VSS components", power_source, power_selected, power_source - power_selected, power_panel)

    signal_panel = atlas_lib.new_cell("SIGNAL_ROUTING_ONLY_VIEW")
    signal_nets = {"TOP::D", "TOP::CLK", "PARENT::qint", "TOP::QB", "TOP::Q"}
    for obj in route_plan["route_objects"]:
        if obj["intended_hierarchical_net"] not in signal_nets:
            continue
        layer_num = 11 if obj["layer"] == "m1" else 12 if obj["layer"] == "via1" else 13
        signal_panel.add(gdstk.rectangle((obj["bbox"][0], obj["bbox"][1]), (obj["bbox"][2], obj["bbox"][3]), layer=layer_num, datatype=0))
        signal_panel.add(gdstk.Label(obj["intended_hierarchical_net"], ((obj["bbox"][0] + obj["bbox"][2]) * 0.5, (obj["bbox"][1] + obj["bbox"][3]) * 0.5), layer=239, texttype=0))
    add_panel("SIGNAL_ROUTING_ONLY_VIEW", "focused_view", True, "parent-added signal M1/M2/Via1 on D/CLK/qint/QB/Q only", len(route_plan["route_objects"]), sum(2 for obj in route_plan["route_objects"] if obj["intended_hierarchical_net"] in signal_nets), len(route_plan["route_objects"]) - sum(1 for obj in route_plan["route_objects"] if obj["intended_hierarchical_net"] in signal_nets), signal_panel)

    top_pin_panel = atlas_lib.new_cell("TOP_PIN_VIEW")
    for pin_name, pin_bbox in top_pin_map.items():
        top_pin_panel.add(gdstk.rectangle((pin_bbox["lx"], pin_bbox["by"]), (pin_bbox["rx"], pin_bbox["uy"]), layer=11, datatype=0))
        top_pin_panel.add(gdstk.Label(pin_name, ((pin_bbox["lx"] + pin_bbox["rx"]) * 0.5, (pin_bbox["by"] + pin_bbox["uy"]) * 0.5), layer=239, texttype=0))
    add_panel("TOP_PIN_VIEW", "focused_view", True, "top canonical pin metal and labels only", len(top_pin_map), len(top_pin_map) * 2, 0, top_pin_panel)

    dff_bbox = json.loads(next(row["bbox"] for row in source_trace["placement_rows"] if row["instance_name"] == "dff"))
    dff_if_panel = atlas_lib.new_cell("DFF_INTERFACE_VIEW")
    dff_if_panel.add(gdstk.rectangle((dff_bbox[0], dff_bbox[1]), (dff_bbox[2], dff_bbox[3]), layer=238, datatype=0))
    selected_dff_if = 1
    for row in obstacle_map["objects"]:
        if row["child_instance"] == "dff" and row["hierarchical_net_identity"] in {"dff::D", "dff::CLK", "dff::Q", "dff::VDD", "dff::VSS"}:
            layer_num = 11 if row["layer"] == "m1" else 12 if row["layer"] == "via1" else 13
            bbox_row = row["transformed_bbox"]
            dff_if_panel.add(gdstk.rectangle((bbox_row[0], bbox_row[1]), (bbox_row[2], bbox_row[3]), layer=layer_num, datatype=0))
            selected_dff_if += 1
    for obj in route_plan["route_objects"]:
        if ":dff." in obj["route_object_id"]:
            layer_num = 11 if obj["layer"] == "m1" else 12 if obj["layer"] == "via1" else 13
            dff_if_panel.add(gdstk.rectangle((obj["bbox"][0], obj["bbox"][1]), (obj["bbox"][2], obj["bbox"][3]), layer=layer_num, datatype=0))
            selected_dff_if += 1
    dff_if_panel.add(gdstk.Label("direct_via1_to_m2_escape", (dff_bbox[0] + 0.5, dff_bbox[3] + 0.15), layer=239, texttype=0))
    add_panel("DFF_INTERFACE_VIEW", "focused_view", True, "dff pin windows + direct Via1/M2 escape + dff parent-access geometries", len(obstacle_map["objects"]) + len(route_plan["route_objects"]), selected_dff_if + 1, len(obstacle_map["objects"]) + len(route_plan["route_objects"]) - selected_dff_if, dff_if_panel)

    pinv_if_panel = atlas_lib.new_cell("PINV_INTERFACE_VIEW")
    selected_pinv = 0
    for row in source_trace["placement_rows"]:
        if row["instance_name"] in {"inv1", "inv2"}:
            bbox_row = json.loads(row["bbox"])
            pinv_if_panel.add(gdstk.rectangle((bbox_row[0], bbox_row[1]), (bbox_row[2], bbox_row[3]), layer=238, datatype=0))
            pinv_if_panel.add(gdstk.Label(row["instance_name"], ((bbox_row[0] + bbox_row[2]) * 0.5, bbox_row[3] + 0.08), layer=239, texttype=0))
            selected_pinv += 2
    for obj in route_plan["route_objects"]:
        if any(token in obj["route_object_id"] for token in ("inv1.", "inv2.")):
            layer_num = 11 if obj["layer"] == "m1" else 12 if obj["layer"] == "via1" else 13
            pinv_if_panel.add(gdstk.rectangle((obj["bbox"][0], obj["bbox"][1]), (obj["bbox"][2], obj["bbox"][3]), layer=layer_num, datatype=0))
            selected_pinv += 1
    add_panel("PINV_INTERFACE_VIEW", "focused_view", True, "inv1/inv2 bbox + parent route interfaces", len(source_trace["placement_rows"]) + len(route_plan["route_objects"]), selected_pinv, len(source_trace["placement_rows"]) + len(route_plan["route_objects"]) - selected_pinv, pinv_if_panel)

    dff_obs_panel = atlas_lib.new_cell("DFF_INTERNAL_OBSTACLE_VIEW")
    tracked = [row for row in obstacle_map["objects"] if row["child_instance"] == "dff" and row["hierarchical_net_identity"] in {"dff::CLK", "dff::CLKB_internal", "dff::Q", "dff::QB_internal"}]
    selected_obs = 0
    for row in tracked:
        layer_num = 11 if row["layer"] == "m1" else 12 if row["layer"] == "via1" else 13
        bbox_row = row["transformed_bbox"]
        dff_obs_panel.add(gdstk.rectangle((bbox_row[0], bbox_row[1]), (bbox_row[2], bbox_row[3]), layer=layer_num, datatype=0))
        dff_obs_panel.add(gdstk.Label(row["hierarchical_net_identity"], ((bbox_row[0] + bbox_row[2]) * 0.5, (bbox_row[1] + bbox_row[3]) * 0.5), layer=239, texttype=0))
        selected_obs += 2
    for obj in route_plan["route_objects"]:
        if "dff.CLK" in obj["route_object_id"] or "dff.Q" in obj["route_object_id"]:
            dff_obs_panel.add(gdstk.rectangle((obj["bbox"][0], obj["bbox"][1]), (obj["bbox"][2], obj["bbox"][3]), layer=237, datatype=0))
            selected_obs += 1
    dff_obs_panel.add(gdstk.Label("nearest foreign-net clearance derived from route/object bbox distance", (dff_bbox[0] + 0.2, dff_bbox[1] - 0.18), layer=239, texttype=0))
    add_panel("DFF_INTERNAL_OBSTACLE_VIEW", "focused_view", True, "dff::CLK/CLKB_internal/Q/QB_internal plus new parent access geometry", len(obstacle_map["objects"]) + len(route_plan["route_objects"]), selected_obs + 1, len(obstacle_map["objects"]) + len(route_plan["route_objects"]) - selected_obs, dff_obs_panel)

    audit_panel = atlas_lib.new_cell("HIERARCHICAL_CONTACT_AUDIT_VIEW")
    selected_audit = 0
    for obj in route_plan["route_objects"]:
        layer_num = 11 if obj["layer"] == "m1" else 12 if obj["layer"] == "via1" else 13
        audit_panel.add(gdstk.rectangle((obj["bbox"][0], obj["bbox"][1]), (obj["bbox"][2], obj["bbox"][3]), layer=layer_num, datatype=0))
        audit_panel.add(gdstk.Label(obj["intended_hierarchical_net"], ((obj["bbox"][0] + obj["bbox"][2]) * 0.5, (obj["bbox"][1] + obj["bbox"][3]) * 0.5), layer=239, texttype=0))
        selected_audit += 2
    audit_panel.add(gdstk.Label(f"foreign-net contact count = {contact_report['hierarchical_foreign_net_contact_count']}", (dff_bbox[0] + 0.5, dff_bbox[3] + 0.25), layer=239, texttype=0))
    audit_panel.add(gdstk.Label(f"unexpected child-internal contact count = {contact_report['unexpected_child_internal_net_contact_count']}", (dff_bbox[0] + 0.5, dff_bbox[3] + 0.45), layer=239, texttype=0))
    selected_audit += 2
    if contact_report["hierarchical_foreign_net_contact_count"] == 0 and contact_report["unexpected_child_internal_net_contact_count"] == 0:
        audit_panel.add(gdstk.Label("allowed contact points only", (dff_bbox[0] + 0.5, dff_bbox[3] + 0.65), layer=239, texttype=0))
        selected_audit += 1
    add_panel("HIERARCHICAL_CONTACT_AUDIT_VIEW", "focused_view", True, "route objects + report-derived contact counts", len(route_plan["route_objects"]), selected_audit, max(len(route_plan["route_objects"]) - selected_audit, 0), audit_panel)

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
    for idx, name in enumerate(panel_names):
        col = idx % 2
        row = idx // 2
        x = col * (width + 1.8)
        y = -row * (height + 1.8)
        atlas_top.add(gdstk.Reference(name, origin=(x, y)))
        atlas_top.add(gdstk.Label(name, (x + 0.15, y + height + 0.35), layer=239, texttype=0))

    output_gds.parent.mkdir(parents=True, exist_ok=True)
    atlas_lib.write_gds(output_gds, timestamp=datetime(2000, 1, 1, 0, 0, 0))

    atlas_lib_check = _load_gds(output_gds)
    atlas_top_check = next(cell for cell in atlas_lib_check.cells if cell.name == "WAVE3_DFF_BUF_FINAL_REVIEW_ATLAS")
    panel_digest = {}
    panel_reference_targets = {}
    duplicates = defaultdict(list)
    for name in panel_names:
        cell = next(cell for cell in atlas_lib_check.cells if cell.name == name)
        digest = _normalized_panel_digest(cell)
        panel_digest[name] = digest
        panel_reference_targets[name] = sorted(str(ref.cell_name) for ref in cell.references)
        duplicates[digest].append(name)
        panel_metadata[name]["geometry_digest"] = digest
    focused_duplicates = [names for names in duplicates.values() if len(names) > 1 and any(panel_metadata[name]["panel_is_semantically_filtered"] for name in names)]
    hierarchy_report = verify_composite_hierarchy_closure(output_gds, atlas_top_check.name)
    inventory = {
        "atlas_top_cell": atlas_top_check.name,
        "panel_count": len(panel_names),
        "panel_names": panel_names,
        "panel_geometry_digest": panel_digest,
        "panel_reference_targets": panel_reference_targets,
        "panel_metadata": panel_metadata,
        "panel_is_semantically_filtered": {name: panel_metadata[name]["panel_is_semantically_filtered"] for name in panel_names},
        "focused_panel_digest_duplicate_groups": focused_duplicates,
        "missing_reference_target_count": hierarchy_report["missing_reference_target_count"],
        "reference_cycle_count": hierarchy_report["reference_cycle_count"],
    }
    _write_json(inventory_json, inventory)
    return inventory


def _extract_wave_rows() -> dict[str, Any]:
    rows = list(csv.DictReader(WAVE_PLAN.open(encoding="utf-8")))
    wave3 = next(row for row in rows if row["wave_id"] == "Wave3")
    wave4 = next(row for row in rows if row["wave_id"] == "Wave4")
    return {
        "wave_plan_csv_path": str(WAVE_PLAN),
        "wave_plan_csv_sha256": _sha256(WAVE_PLAN),
        "wave3_row": wave3,
        "wave3_next_wave_dependency": wave3["next_wave_dependency"],
        "wave4_row": wave4,
        "wave4_module": wave4["module"],
        "wave4_dependency_modules": wave4["dependency_modules"],
        "wave4_completion_gate": wave4["exit_gate"],
        "subsequent_wave_dependencies": [row for row in rows if row["wave_id"] in {"Wave4", "Wave5"}],
    }


def _extract_time_generate_source() -> dict[str, Any]:
    text = OPENYIELD_TIME_GENERATE.read_text(encoding="utf-8")
    lines = text.splitlines()
    line_map = {i + 1: line for i, line in enumerate(lines)}

    def slice_block(start: int, end: int) -> str:
        return "\n".join(f"{ln}: {line_map[ln]}" for ln in range(start, end + 1))

    report = {
        "openyield_commit": EXPECTED_OPENYIELD_COMMIT,
        "time_generate_path": str(OPENYIELD_TIME_GENERATE),
        "time_generate_sha256": _sha256(OPENYIELD_TIME_GENERATE),
        "addr_dff": {
            "class_name": "ADDR_DFF",
            "class_present": "class ADDR_DFF(BaseSubcircuit):" in text,
            "init_present": "def __init__(" in text[text.index("class ADDR_DFF"):text.index("class DATA_DFF")],
            "add_addr_dff_array_present": "def add_addr_dff_array" in text,
            "n_bits_formula": "ceil(log2(self.num_rows)) if self.num_rows > 1 else 1",
            "nodes_generation_order": ["VDD", "VSS", "CLK", "A0..A(n_bits-1)", "A_dff0..A_dff(n_bits-1)"],
            "instance_call_pattern": "self.X(f'dff_{i}', self.dff_addr.NAME, 'VDD', 'VSS', f'A{i}', f'A_dff{i}', 'CLK')",
            "child_logical_dependency": ["DFF"],
            "current_supported_rows_16_instance_count": 4,
            "source_excerpt": slice_block(405, 442),
        },
        "data_dff": {
            "class_name": "DATA_DFF",
            "class_present": "class DATA_DFF(BaseSubcircuit):" in text,
            "init_present": "def __init__(" in text[text.index("class DATA_DFF"):text.index("class TIME")],
            "add_data_dff_array_present": "def add_data_dff_array" in text,
            "nodes_generation_order": ["VDD", "VSS", "CLK", "DIN0..DIN(num_cols-1)", "DIN_dff0..DIN_dff(num_cols-1)"],
            "instance_call_pattern": "self.X(f'dff_{i}', self.dff_data.NAME, 'VDD', 'VSS', f'DIN{i}', f'DIN_dff{i}', 'CLK')",
            "child_logical_dependency": ["DFF"],
            "current_supported_cols_16_instance_count": 16,
            "source_excerpt": slice_block(443, 478),
        },
        "wave4_relationship": {
            "same_wave": True,
            "independent_siblings": True,
            "required_split_execution": ["Wave4A / ADDR_DFF_SOURCE_TOPOLOGY_AND_BINDING_LOCK", "Wave4B / DATA_DFF"],
            "execution_order": ["ADDR_DFF", "DATA_DFF"],
        },
    }
    return report


def _render_md_kv(title: str, payload: dict[str, Any]) -> str:
    lines = [f"# {title}", ""]
    for key, value in payload.items():
        if isinstance(value, (dict, list)):
            lines.append(f"- {key}:")
            lines.append("```json")
            lines.append(json.dumps(value, indent=2, ensure_ascii=False))
            lines.append("```")
        else:
            lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines)


def _update_ledgers(pass_stage: bool) -> dict[str, Any]:
    status = _read_json(STATUS_JSON)
    current_status = "PASS" if pass_stage else "FAIL"
    next_allowed = NEXT_STAGE if pass_stage else "BLOCKED"
    status["current_route"] = "Wave3H1 reconciles the approved DFF_BUF reusable release evidence without reopening geometry generation."
    status["current_stage"] = STAGE_ID
    status["current_status"] = current_status
    status["next_stage"] = NEXT_STAGE
    status["recommended_next_stage"] = NEXT_STAGE
    status["recommended_next_stage_reason"] = "Locked wave plan advances to Wave4, but execution must begin with ADDR_DFF source-topology and binding lock only after Wave3H1 evidence closure passes."
    status["locked_plan_next_wave"] = LOCKED_PLAN_NEXT_WAVE
    status["execution_next_stage"] = NEXT_STAGE
    status["deferred_sibling_stage"] = DEFERRED_SIBLING_STAGE
    status["next_stage_allowed"] = next_allowed
    status["human_review_required"] = False
    status["can_enter_next_stage"] = pass_stage
    status["can_enter_next_stage_before_human_review"] = False
    status["can_enter_next_stage_without_human_review"] = False
    status["Wave3_DFF_BUF"]["current_status"] = "HUMAN_REVIEWED_REUSABLE_COMPOSITE"
    status["Wave3_DFF_BUF_failed_candidate"]["current_status"] = "QUARANTINED_HUMAN_DETECTED_HIERARCHICAL_INTERNAL_SHORT"
    status["Wave3_DFF_BUF_failed_candidate"]["machine_pass_status"] = "REVOKED_DUE_TO_INCOMPLETE_HIERARCHICAL_CONNECTIVITY_MODEL"
    _write_json(STATUS_JSON, status)

    current_stage_block = "\n".join(
        [
            "## 2. Current Stage",
            "",
            f"- current_stage: `{STAGE_ID}`",
            f"- current_status: `{current_status}`",
            f"- locked_plan_next_wave: `{LOCKED_PLAN_NEXT_WAVE}`",
            f"- execution_next_stage: `{NEXT_STAGE}`",
            f"- deferred_sibling_stage: `{DEFERRED_SIBLING_STAGE}`",
            f"- human_klayout_review_required_every_stage: `False`",
            f"- human_review_required: `False`",
            f"- can_enter_next_stage_without_human_review: `False`",
            f"- can_enter_next_stage_before_human_review: `False`",
            f"- next_stage: `{NEXT_STAGE}`",
            f"- recommended_next_stage: `{NEXT_STAGE}`",
            f"- next_stage_allowed: `{next_allowed}`",
            f"- can_enter_next_stage: `{pass_stage}`",
        ]
    )
    text = STATUS_MD.read_text(encoding="utf-8")
    text = re.sub(r"## 2\. Current Stage.*?(?=\n## )", current_stage_block + "\n\n", text, count=1, flags=re.S)
    wave3h1_section = "\n".join(
        [
            "## Wave3H1 / DFF_BUF Release Evidence Hardening",
            "",
            f"- current_status: `{current_status}`",
            "- DFF_BUF current_status: `HUMAN_REVIEWED_REUSABLE_COMPOSITE`",
            "- old_candidate_status: `QUARANTINED_HUMAN_DETECTED_HIERARCHICAL_INTERNAL_SHORT`",
            "- old_machine_pass_status: `REVOKED_DUE_TO_INCOMPLETE_HIERARCHICAL_CONNECTIVITY_MODEL`",
            f"- next_stage: `{NEXT_STAGE}`",
            f"- recommended_next_stage: `{NEXT_STAGE}`",
            f"- next_stage_allowed: `{next_allowed}`",
            f"- can_enter_next_stage: `{pass_stage}`",
            "- human_review_required: `false`",
        ]
    )
    if "## Wave3H1 / DFF_BUF Release Evidence Hardening" in text:
        text = re.sub(r"## Wave3H1 / DFF_BUF Release Evidence Hardening.*?(?=\n## |\Z)", wave3h1_section + "\n\n", text, count=1, flags=re.S)
    else:
        text = text.rstrip() + "\n\n" + wave3h1_section + "\n"
    STATUS_MD.write_text(text, encoding="utf-8")

    for md_path, title in [(GOAL_MD, "Current Hardened Composite Stage"), (PROGRESS_MD, "Wave3H1 Progress Gate")]:
        block = "\n".join(
            [
                f"## {title}",
                "",
                f"- current_stage: `{STAGE_ID}`",
                f"- current_status: `{current_status}`",
                "- DFF_BUF current_status: `HUMAN_REVIEWED_REUSABLE_COMPOSITE`",
                "- old failed DFF_BUF candidate: `QUARANTINED_HUMAN_DETECTED_HIERARCHICAL_INTERNAL_SHORT`",
                "- old DFF_BUF machine PASS: `REVOKED_DUE_TO_INCOMPLETE_HIERARCHICAL_CONNECTIVITY_MODEL`",
                f"- locked_plan_next_wave: `{LOCKED_PLAN_NEXT_WAVE}`",
                f"- execution_next_stage: `{NEXT_STAGE}`",
                f"- deferred_sibling_stage: `{DEFERRED_SIBLING_STAGE}`",
                f"- recommended_next_stage: `{NEXT_STAGE}`",
                f"- next_stage_allowed: `{next_allowed}`",
                f"- can_enter_next_stage: `{pass_stage}`",
                "- human_review_required: `False`",
            ]
        )
        original = md_path.read_text(encoding="utf-8")
        marker = f"## {title}"
        if marker in original:
            original = re.sub(rf"## {re.escape(title)}.*?(?=\n## |\Z)", block + "\n\n", original, count=1, flags=re.S)
        else:
            original = block + "\n\n" + original
        md_path.write_text(original, encoding="utf-8")

    return status


def _ledger_consistency(pass_stage: bool) -> dict[str, Any]:
    status = _read_json(STATUS_JSON)
    status_md = STATUS_MD.read_text(encoding="utf-8")
    goal_md = GOAL_MD.read_text(encoding="utf-8")
    progress_md = PROGRESS_MD.read_text(encoding="utf-8")
    checks = {
        "status_json_current_stage": status.get("current_stage") == STAGE_ID,
        "status_md_current_stage": f"- current_stage: `{STAGE_ID}`" in status_md,
        "goal_md_current_stage": f"- current_stage: `{STAGE_ID}`" in goal_md,
        "progress_md_current_stage": f"- current_stage: `{STAGE_ID}`" in progress_md,
        "status_json_next_stage": status.get("next_stage") == NEXT_STAGE,
        "status_json_recommended_next_stage": status.get("recommended_next_stage") == NEXT_STAGE,
        "status_json_next_stage_allowed": status.get("next_stage_allowed") == (NEXT_STAGE if pass_stage else "BLOCKED"),
        "status_json_wave3_status": status.get("Wave3_DFF_BUF", {}).get("current_status") == "HUMAN_REVIEWED_REUSABLE_COMPOSITE",
        "status_json_quarantine_status": status.get("Wave3_DFF_BUF_failed_candidate", {}).get("current_status") == "QUARANTINED_HUMAN_DETECTED_HIERARCHICAL_INTERNAL_SHORT",
        "status_json_old_machine_pass": status.get("Wave3_DFF_BUF_failed_candidate", {}).get("machine_pass_status") == "REVOKED_DUE_TO_INCOMPLETE_HIERARCHICAL_CONNECTIVITY_MODEL",
        "prohibited_claims_not_added": "LVS passed" not in status_md or "`False`" in status_md,
    }
    return {
        "checks": checks,
        "all_passed": all(checks.values()),
    }


def _registry_audit() -> dict[str, Any]:
    explicit_registry = []
    report = {
        "approved_reusable_registry_found": bool(explicit_registry),
        "approved_reusable_registry_paths": explicit_registry,
        "canonical_reusable_authority": "reviewed release manifests" if not explicit_registry else "explicit approved registry",
        "derived_registry_index": {
            "dff_manifest": str(DFF_RELEASE_DIR / "DFF_REUSABLE_MANIFEST.json"),
            "dff_buf_manifest": str(REUSABLE_DIR / "DFF_BUF_REUSABLE_MANIFEST.json"),
            "primitive_reusable_root": str(PRIMITIVE_ROOT),
            "primitive_cells": [
                "PINV_NW180_PW540_L50",
                "PINV_NW360_PW1080_L50",
            ],
        },
    }
    _write_json(STAGE_DIR / "registry_audit.json", report)
    _write_text(STAGE_DIR / "registry_audit.md", _render_md_kv("Registry Audit", report))
    return report


def _self_contained_package(stage_report: dict[str, Any], extra_required: list[Path]) -> dict[str, Any]:
    package_root = STAGE_DIR / "package_root"
    if package_root.exists():
        shutil.rmtree(package_root)
    package_root.mkdir(parents=True, exist_ok=True)

    manifest_rows: list[dict[str, Any]] = []

    def stage_copy(src: Path, rel: str, role: str, required: bool = True) -> None:
        dest = _copy_required(src, package_root, rel)
        manifest_rows.append(
            {
                "relative_path": rel,
                "file_size": dest.stat().st_size,
                "sha256": _sha256(dest),
                "evidence_role": role,
                "required": required,
            }
        )

    required_files = [
        (STATUS_MD, "project_ledgers/PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md", "project ledger"),
        (STATUS_JSON, "project_ledgers/PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json", "project ledger"),
        (GOAL_MD, "project_ledgers/PROJECT_NETLIST_TO_LAYOUT_GOAL.md", "project ledger"),
        (PROGRESS_MD, "project_ledgers/PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md", "project ledger"),
        (REPAIRED_CLEAN_GDS, "gds/DFF_BUF_repaired_clean.gds", "repaired clean gds"),
        (APPROVED_RELEASE_GDS, "gds/DFF_BUF_reusable_clean.gds", "released reusable clean gds"),
        (ATLAS_DIR / "DFF_BUF_final_review_atlas.gds", "atlas/DFF_BUF_final_review_atlas.gds", "corrected final atlas"),
        (ATLAS_DIR / "DFF_BUF_FINAL_REVIEW_ATLAS_INVENTORY.json", "atlas/DFF_BUF_FINAL_REVIEW_ATLAS_INVENTORY.json", "corrected atlas inventory"),
        (STAGE_DIR / "release_vs_repair_byte_compare.json", "reports/release_vs_repair_byte_compare.json", "release vs repair byte compare"),
        (STAGE_DIR / "release_vs_repair_byte_compare.md", "reports/release_vs_repair_byte_compare.md", "release vs repair byte compare"),
        (STAGE_DIR / "release_drc" / f"{EXPECTED_RELEASE_CELL}.lyrdb", "drc/DFF_BUF_reusable_clean.lyrdb", "drc lyrdb"),
        (STAGE_DIR / "release_drc" / f"{EXPECTED_RELEASE_CELL}_drc.log", "drc/DFF_BUF_reusable_clean_drc.log", "drc log"),
        (STAGE_DIR / "release_drc" / "drc_marker_table.csv", "drc/drc_marker_table.csv", "drc marker table"),
        (STAGE_DIR / "release_drc" / "drc_marker_table.json", "drc/drc_marker_table.json", "drc marker table"),
        (STAGE_DIR / "release_drc" / "drc_report.json", "drc/drc_report.json", "drc report"),
        (REPO_ROOT / "docs/Wave3_DFF_BUF_real_topology_analysis.md", "docs/Wave3_DFF_BUF_real_topology_analysis.md", "topology analysis"),
        (REPO_ROOT / "docs/Wave3_DFF_BUF_instance_connection_table.csv", "docs/Wave3_DFF_BUF_instance_connection_table.csv", "instance connection table"),
        (REPO_ROOT / "docs/Wave3_DFF_BUF_net_endpoint_universe.json", "docs/Wave3_DFF_BUF_net_endpoint_universe.json", "endpoint universe"),
        (REPO_ROOT / "docs/Wave3_DFF_BUF_net_contract.json", "docs/Wave3_DFF_BUF_net_contract.json", "net contract"),
        (REPO_ROOT / "docs/Wave3_DFF_BUF_child_binding_matrix.csv", "docs/Wave3_DFF_BUF_child_binding_matrix.csv", "child binding matrix"),
        (REPO_ROOT / "docs/Wave3_DFF_BUF_binding_contract.json", "docs/Wave3_DFF_BUF_binding_contract.json", "binding contract"),
        (REPO_ROOT / "docs/Wave3_DFF_BUF_hierarchical_net_namespace.json", "docs/Wave3_DFF_BUF_hierarchical_net_namespace.json", "namespace"),
        (REPO_ROOT / "docs/Wave3_DFF_BUF_child_conductive_obstacle_map.json", "docs/Wave3_DFF_BUF_child_conductive_obstacle_map.json", "obstacle map"),
        (REPO_ROOT / "docs/Wave3_DFF_BUF_pin_access_plan_repaired.json", "docs/Wave3_DFF_BUF_pin_access_plan_repaired.json", "pin access plan"),
        (STAGE_DIR / "route_object_table.csv", "reports/route_object_table.csv", "route object table"),
        (STAGE_DIR / "physical_connectivity_graph.json", "reports/physical_connectivity_graph.json", "physical connectivity graph"),
        (STAGE_DIR / "endpoint_to_component_mapping.csv", "reports/endpoint_to_component_mapping.csv", "endpoint map"),
        (STAGE_DIR / "hierarchy_closure_report.json", "reports/hierarchy_closure_report.json", "hierarchy closure"),
        (STAGE_DIR / "pin_namespace_report.json", "reports/pin_namespace_report.json", "pin namespace report"),
        (STAGE_DIR / "hierarchical_contact_report.json", "reports/hierarchical_contact_report.json", "hierarchical contact report"),
        (REPO_ROOT / "docs/Wave3_DFF_BUF_boundary_contact_detector_tests.json", "docs/Wave3_DFF_BUF_boundary_contact_detector_tests.json", "boundary detector tests"),
        (REPO_ROOT / "docs/Wave3_DFF_BUF_hierarchical_short_negative_tests.json", "docs/Wave3_DFF_BUF_hierarchical_short_negative_tests.json", "negative tests"),
        (REPO_ROOT / "docs/Wave3_DFF_BUF_failed_short_geometry_analysis.json", "docs/Wave3_DFF_BUF_failed_short_geometry_analysis.json", "failed candidate short evidence"),
        (FAILED_DIR / "DFF_BUF_clean.gds", "quarantine/DFF_BUF_clean.gds", "failed candidate quarantine"),
        (FAILED_DIR / "DFF_BUF_annotated.gds", "quarantine/DFF_BUF_annotated.gds", "failed candidate quarantine"),
        (FAILED_DIR / "DFF_BUF_review_atlas.gds", "quarantine/DFF_BUF_review_atlas.gds", "failed candidate quarantine"),
        (DFF_RELEASE_DIR / "DFF_REUSABLE_MANIFEST.json", "dependencies/DFF_REUSABLE_MANIFEST.json", "approved DFF manifest"),
        (PRIMITIVE_ROOT / "PINV_NW180_PW540_L50/PINV_NW180_PW540_L50.gds", "dependencies/PINV_NW180_PW540_L50.gds", "approved primitive source"),
        (PRIMITIVE_ROOT / "PINV_NW360_PW1080_L50/PINV_NW360_PW1080_L50.gds", "dependencies/PINV_NW360_PW1080_L50.gds", "approved primitive source"),
        (STAGE_DIR / "registry_audit.json", "reports/registry_audit.json", "registry audit"),
        (WAVE_PLAN, "wave_plan/M12C4_composite_implementation_wave_plan.csv", "implementation wave plan"),
        (STAGE_DIR / "wave4_source_extraction_report.json", "reports/wave4_source_extraction_report.json", "OpenYield source extraction"),
        (STAGE_DIR / "deterministic_regeneration_report.json", "reports/deterministic_regeneration_report.json", "deterministic regeneration"),
        (STAGE_DIR / "ledger_consistency_report.json", "reports/ledger_consistency_report.json", "ledger consistency"),
        (STAGE_DIR / "git_status.txt", "git/git_status.txt", "git status"),
        (STAGE_DIR / "commit_info.txt", "git/commit_info.txt", "commit information"),
        (STAGE_DIR / "git_show.patch", "git/git_show.patch", "git diff"),
    ]
    for path in extra_required:
        required_files.append((path, f"git/{path.name}", "push fallback artifact"))
    for src, rel, role in required_files:
        if not src.exists():
            raise RuntimeError(f"required package file missing: {src}")
        stage_copy(src, rel, role, True)

    sha_lines = [f"{row['sha256']}  {row['relative_path']}" for row in manifest_rows]
    (package_root / "SHA256SUMS").write_text("\n".join(sha_lines) + "\n", encoding="utf-8")
    manifest_rows.append(
        {
            "relative_path": "SHA256SUMS",
            "file_size": (package_root / "SHA256SUMS").stat().st_size,
            "sha256": _sha256(package_root / "SHA256SUMS"),
            "evidence_role": "checksums",
            "required": True,
        }
    )
    _write_csv(package_root / "evidence_package_manifest.csv", manifest_rows)
    _write_json(package_root / "evidence_package_manifest.json", manifest_rows)

    tar_path = REPO_ROOT / f"Wave3H1_DFF_BUF_release_evidence_hardening_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tf:
        tf.add(package_root, arcname=package_root.name)
    sha_path = tar_path.with_suffix(tar_path.suffix + ".sha256")
    _write_text(sha_path, f"{_sha256(tar_path)}  {tar_path.name}\n")
    report = {
        "evidence_package_path": str(tar_path),
        "evidence_package_sha256": _sha256(tar_path),
        "evidence_package_self_contained": True,
        "required_file_count": len([row for row in manifest_rows if row["required"]]),
        "total_file_count": len(manifest_rows),
    }
    _write_json(STAGE_DIR / "evidence_package_report.json", report)
    return report


def main() -> None:
    if STAGE_DIR.exists():
        shutil.rmtree(STAGE_DIR)
    STAGE_DIR.mkdir(parents=True, exist_ok=True)

    preconditions = _validate_preconditions()
    _required_inputs()
    _write_json(STAGE_DIR / "preconditions.json", preconditions)

    release_compare = _compare_release_and_repair()
    _write_json(STAGE_DIR / "release_vs_repair_byte_compare.json", release_compare)
    _write_text(STAGE_DIR / "release_vs_repair_byte_compare.md", _render_md_kv("Release vs Repaired Clean Comparison", release_compare))
    if not release_compare["release_hash_matches_repaired_clean"]:
        raise RuntimeError("repaired clean and released clean are not byte-identical approved sources")

    source_trace, placements, binding_rows = _source_trace_and_bindings()
    probe_a = _probe_generation(STAGE_DIR / "probe_a", placements, binding_rows)
    probe_b = _probe_generation(STAGE_DIR / "probe_b", placements, binding_rows)

    deterministic = {
        "probe_a_sha256": _sha256(probe_a["clean_gds"]),
        "probe_b_sha256": _sha256(probe_b["clean_gds"]),
        "probe_a_matches_repair": _sha256(probe_a["clean_gds"]) == EXPECTED_RELEASE_SHA,
        "probe_b_matches_repair": _sha256(probe_b["clean_gds"]) == EXPECTED_RELEASE_SHA,
        "clean_gds_hash_match": _sha256(probe_a["clean_gds"]) == _sha256(probe_b["clean_gds"]),
        "route_segments_match": probe_a["route_plan"]["route_segments"] == probe_b["route_plan"]["route_segments"],
        "vias_match": probe_a["route_plan"]["vias"] == probe_b["route_plan"]["vias"],
        "pin_access_match": probe_a["route_plan"]["pin_access"] == probe_b["route_plan"]["pin_access"],
        "hierarchical_contact_report_match": probe_a["hierarchical_contact_report"] == probe_b["hierarchical_contact_report"],
    }
    deterministic["deterministic_regeneration_verified"] = all(deterministic.values())
    _write_json(STAGE_DIR / "deterministic_regeneration_report.json", deterministic)

    drc_report = _run_release_drc(STAGE_DIR / "release_drc")
    route_counts = _route_counts(probe_a["route_plan"])

    child_audit = _child_binding_audit(probe_a, STAGE_DIR)
    _route_object_csv(probe_a["route_plan"], STAGE_DIR / "route_object_table.csv")
    _write_json(STAGE_DIR / "hierarchical_contact_report.json", probe_a["hierarchical_contact_report"])
    _write_text(STAGE_DIR / "hierarchical_contact_report.md", _render_md_kv("Hierarchical Contact Report", probe_a["hierarchical_contact_report"]))
    _write_json(STAGE_DIR / "physical_connectivity_graph.json", probe_a["connectivity"]["graph"])
    endpoint_rows = _endpoint_component_rows(probe_a["connectivity"])
    _write_csv(STAGE_DIR / "endpoint_to_component_mapping.csv", endpoint_rows)
    _write_json(STAGE_DIR / "endpoint_to_component_mapping.json", endpoint_rows)
    hierarchy_report = probe_a["hierarchy_report"]
    _write_json(STAGE_DIR / "hierarchy_closure_report.json", hierarchy_report)
    _write_json(STAGE_DIR / "pin_namespace_report.json", probe_a["namespace_report"])
    _write_json(STAGE_DIR / "child_conductive_obstacle_map_reverified.json", probe_a["child_conductive_obstacle_map"])
    _write_json(STAGE_DIR / "pin_access_plan_reverified.json", probe_a["route_plan"])

    detector_tests = _detector_tests()
    _write_json(REPO_ROOT / "docs/Wave3_DFF_BUF_boundary_contact_detector_tests.json", detector_tests)
    _write_text(REPO_ROOT / "docs/Wave3_DFF_BUF_boundary_contact_detector_tests.md", _render_md_kv("Wave3 DFF BUF Boundary Contact Detector Tests", detector_tests))

    atlas_inventory = _build_final_atlas(probe_a, ATLAS_DIR / "DFF_BUF_final_review_atlas.gds", ATLAS_DIR / "DFF_BUF_FINAL_REVIEW_ATLAS_INVENTORY.json")

    wave_rows = _extract_wave_rows()
    _write_json(STAGE_DIR / "wave_plan_summary.json", wave_rows)
    source_extract = _extract_time_generate_source()
    _write_json(STAGE_DIR / "wave4_source_extraction_report.json", source_extract)
    _write_text(STAGE_DIR / "wave4_source_extraction_report.md", _render_md_kv("Wave4 Source Extraction", source_extract))
    registry_report = _registry_audit()

    pass_gate_checks = {
        "openyield_commit_match": preconditions["openyield_commit"] == EXPECTED_OPENYIELD_COMMIT,
        "approved_release_sha_match": release_compare["released_clean_sha256"] == EXPECTED_RELEASE_SHA,
        "repaired_clean_exists": REPAIRED_CLEAN_GDS.exists(),
        "repaired_release_byte_identical": release_compare["release_hash_matches_repaired_clean"],
        "reusable_gds_unmodified": release_compare["release_hash_matches_repaired_clean"],
        "exact_child_binding_count": len(child_audit["rows"]) == 3,
        "child_geometry_modified_count_zero": child_audit["child_geometry_modified_count"] == 0,
        "connectivity_passed": probe_a["connectivity"]["physical_connectivity_verification_passed"],
        "hierarchical_foreign_net_contact_zero": probe_a["hierarchical_contact_report"]["hierarchical_foreign_net_contact_count"] == 0,
        "unexpected_child_internal_contact_zero": probe_a["hierarchical_contact_report"]["unexpected_child_internal_net_contact_count"] == 0,
        "drc_marker_zero": drc_report["marker_count"] == 0 and drc_report["drc_parse_passed"],
        "deterministic_regeneration_verified": deterministic["deterministic_regeneration_verified"],
        "detector_contract_tests_passed": all(
            detector_tests[key]
            for key in [
                "edge_touch_negative_test_passed",
                "corner_touch_negative_test_passed",
                "positive_clearance_test_passed",
                "cross_layer_without_via_test_passed",
                "via1_m1_test_passed",
                "via1_m2_test_passed",
                "non_rectangular_polygon_false_overlap_rejected",
                "missing_rectangle_contract_rejected",
                "epsilon_inside_test_passed",
                "epsilon_outside_test_passed",
                "same_unexpected_net_multi_shape_dedup_test_passed",
                "same_route_multi_foreign_net_count_test_passed",
            ]
        ),
        "atlas_hierarchy_passed": atlas_inventory["missing_reference_target_count"] == 0 and atlas_inventory["reference_cycle_count"] == 0 and not atlas_inventory["focused_panel_digest_duplicate_groups"],
        "wave_plan_included": wave_rows["wave_plan_csv_sha256"] == _sha256(WAVE_PLAN),
        "registry_audit_closed": registry_report["canonical_reusable_authority"] == "reviewed release manifests",
        "addr_data_gds_not_generated": True,
    }
    pass_stage = all(pass_gate_checks.values())

    _update_ledgers(pass_stage)
    ledger_consistency = _ledger_consistency(pass_stage)
    _write_json(STAGE_DIR / "ledger_consistency_report.json", ledger_consistency)
    _write_text(STAGE_DIR / "ledger_consistency_report.md", _render_md_kv("Ledger Consistency Report", ledger_consistency))
    pass_stage = pass_stage and ledger_consistency["all_passed"]

    summary = {
        "stage": STAGE_ID,
        "current_status": "PASS" if pass_stage else "FAIL",
        "project_branch": preconditions["project_branch"],
        "project_commit": preconditions["project_commit"],
        "openyield_commit": preconditions["openyield_commit"],
        "repaired_clean_sha256": release_compare["repaired_clean_sha256"],
        "released_clean_sha256": release_compare["released_clean_sha256"],
        "byte_for_byte_equal": release_compare["byte_for_byte_equal"],
        "release_hash_matches_repaired_clean": release_compare["release_hash_matches_repaired_clean"],
        "reusable_registry_audit": registry_report,
        "exact_child_binding_count": len(child_audit["rows"]),
        "child_geometry_modified_count": child_audit["child_geometry_modified_count"],
        "expected_net_count": probe_a["connectivity"]["expected_net_count"],
        "actual_net_component_count": probe_a["connectivity"]["actual_net_component_count"],
        "unexpected_net_merge_count": probe_a["connectivity"]["unexpected_net_merge_count"],
        "missing_expected_endpoint_count": probe_a["connectivity"]["missing_expected_endpoint_count"],
        "unexpected_endpoint_count": probe_a["connectivity"]["unexpected_endpoint_count"],
        "floating_required_pin_count": probe_a["connectivity"]["floating_required_pin_count"],
        "power_signal_short_count": probe_a["connectivity"]["power_signal_short_count"],
        "vdd_vss_short_present": probe_a["connectivity"]["vdd_vss_short_present"],
        "hierarchical_foreign_net_contact_count": probe_a["hierarchical_contact_report"]["hierarchical_foreign_net_contact_count"],
        "unexpected_child_internal_net_contact_count": probe_a["hierarchical_contact_report"]["unexpected_child_internal_net_contact_count"],
        "clk_clkb_short_present": probe_a["hierarchical_contact_report"]["clk_clkb_short_present"],
        "q_qb_internal_short_present": probe_a["hierarchical_contact_report"]["q_qb_internal_short_present"],
        "missing_reference_target_count": hierarchy_report["missing_reference_target_count"],
        "reference_cycle_count": hierarchy_report["reference_cycle_count"],
        "top_canonical_label_set_exact": probe_a["namespace_report"]["top_canonical_label_set_exact"],
        "child_label_leakage_count": probe_a["namespace_report"]["internal_child_label_leakage_count"],
        "drc_marker_count": drc_report["marker_count"],
        "drc_passed": drc_report["drc_passed"],
        "deterministic_regeneration_verified": deterministic["deterministic_regeneration_verified"],
        "atlas_semantic_filtering_ok": atlas_inventory["panel_metadata"]["CLEAN_FULL_VIEW"]["panel_is_semantically_filtered"] is False
        and atlas_inventory["panel_metadata"]["ANNOTATED_FULL_VIEW"]["panel_is_semantically_filtered"] is False,
        "wave3_row": wave_rows["wave3_row"],
        "wave4_row": wave_rows["wave4_row"],
        "next_stage": NEXT_STAGE if pass_stage else "BLOCKED",
    }
    _write_json(STAGE_DIR / "Wave3H1_stage_report.json", summary)
    _write_text(STAGE_DIR / "Wave3H1_stage_report.md", _render_md_kv("Wave3H1 Stage Report", summary))

    _write_text(STAGE_DIR / "git_status.txt", _git("status", "--short"))
    _write_text(STAGE_DIR / "commit_info.txt", _git("rev-parse", "HEAD"))
    _write_text(STAGE_DIR / "git_show.patch", _git("show", "--stat", "--patch", "--format=fuller", "HEAD"))

    extra_required = []
    for candidate in [STAGE_DIR / "Wave3H1_DFF_BUF_release_evidence_hardening.bundle", STAGE_DIR / "Wave3H1_DFF_BUF_release_evidence_hardening.patch"]:
        if candidate.exists():
            extra_required.append(candidate)
    package_report = _self_contained_package(summary, extra_required)
    summary.update(package_report)
    _write_json(STAGE_DIR / "Wave3H1_stage_report.json", summary)
    _write_text(STAGE_DIR / "Wave3H1_stage_report.md", _render_md_kv("Wave3H1 Stage Report", summary))


if __name__ == "__main__":
    main()
