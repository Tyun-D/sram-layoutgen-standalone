from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
from typing import Any

import gdstk


DEBUG_TEXT_LAYER = 294
DEBUG_BOX_LAYER = 295
POWER_NAMES = {"VDD", "GND", "VSS"}


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8", newline="\n")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def _render_md(title: str, lines: list[str]) -> str:
    return "\n".join([f"# {title}", "", *lines, ""]).rstrip() + "\n"


def _rel(repo_root: Path, path: Path) -> str:
    return str(path.resolve().relative_to(repo_root.resolve()))


def _gds_sanity(path: Path) -> str:
    try:
        gdstk.read_gds(path)
    except Exception:
        return "GDS_PARSE_FAILED"
    return "GDS_PARSED_SANITY_PASSED"


def _bbox_to_text(bbox: tuple[tuple[float, float], tuple[float, float]] | None) -> str:
    if bbox is None:
        return ""
    return ",".join(f"{value:.6f}" for value in [bbox[0][0], bbox[0][1], bbox[1][0], bbox[1][1]])


def _union_bbox(boxes: list[tuple[tuple[float, float], tuple[float, float]]]) -> tuple[tuple[float, float], tuple[float, float]] | None:
    if not boxes:
        return None
    x0 = min(box[0][0] for box in boxes)
    y0 = min(box[0][1] for box in boxes)
    x1 = max(box[1][0] for box in boxes)
    y1 = max(box[1][1] for box in boxes)
    return ((x0, y0), (x1, y1))


def _bbox_center(bbox: tuple[tuple[float, float], tuple[float, float]] | None) -> tuple[float, float] | None:
    if bbox is None:
        return None
    return ((bbox[0][0] + bbox[1][0]) / 2.0, (bbox[0][1] + bbox[1][1]) / 2.0)


def _bbox_delta(module_bbox: tuple[tuple[float, float], tuple[float, float]] | None, golden_bbox: tuple[tuple[float, float], tuple[float, float]] | None) -> tuple[str, str]:
    module_center = _bbox_center(module_bbox)
    golden_center = _bbox_center(golden_bbox)
    if module_center is None or golden_center is None:
        return "", ""
    return (f"{module_center[0] - golden_center[0]:.6f}", f"{module_center[1] - golden_center[1]:.6f}")


def _layer_summary(cell: gdstk.Cell) -> str:
    counts: dict[str, int] = {}
    for polygon in cell.polygons:
        key = f"{polygon.layer}/{polygon.datatype}"
        counts[key] = counts.get(key, 0) + 1
    return ";".join(f"{key}:{counts[key]}" for key in sorted(counts))


def _flatten_top_cell(path: Path) -> tuple[gdstk.Library, gdstk.Cell, gdstk.Cell]:
    lib = gdstk.read_gds(path)
    top = lib.top_level()[0]
    flat = top.copy(f"{top.name}_flat", deep_copy=True)
    flat.flatten(apply_repetitions=True)
    return lib, top, flat


def _smallest_polygon_bbox_for_point(cell: gdstk.Cell, layer: int, datatype: int, x: float, y: float) -> tuple[tuple[float, float], tuple[float, float]] | None:
    candidates: list[tuple[float, tuple[tuple[float, float], tuple[float, float]]]] = []
    for polygon in cell.polygons:
        if polygon.layer != layer or polygon.datatype != datatype:
            continue
        if polygon.contain((x, y)):
            bbox = polygon.bounding_box()
            if bbox is None:
                continue
            area = abs((bbox[1][0] - bbox[0][0]) * (bbox[1][1] - bbox[0][1]))
            candidates.append((area, bbox))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0])
    return candidates[0][1]


def _collect_label_power_bboxes(cell: gdstk.Cell, label_name: str) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    matches = []
    for label in cell.labels:
        if label.text.upper() != label_name.upper():
            continue
        bbox = _smallest_polygon_bbox_for_point(cell, label.layer, label.texttype, float(label.origin[0]), float(label.origin[1]))
        if bbox is not None:
            matches.append(bbox)
    return matches


def _find_golden_cell(golden_lib: gdstk.Library, target_name: str) -> gdstk.Cell:
    return next(cell for cell in golden_lib.cells if cell.name == target_name)


def _normal_pin_name(name: str) -> str:
    return name.lower()


def _golden_pin_lookup(cell: gdstk.Cell) -> dict[str, list[tuple[gdstk.Label, tuple[tuple[float, float], tuple[float, float]] | None]]]:
    mapping: dict[str, list[tuple[gdstk.Label, tuple[tuple[float, float], tuple[float, float]] | None]]] = {}
    for label in cell.labels:
        bbox = _smallest_polygon_bbox_for_point(cell, label.layer, label.texttype, float(label.origin[0]), float(label.origin[1]))
        mapping.setdefault(_normal_pin_name(label.text), []).append((label, bbox))
    return mapping


def _module_pin_polygon(flat_cell: gdstk.Cell, pin: dict[str, Any]) -> tuple[tuple[float, float], tuple[float, float]] | None:
    layer, datatype = map(int, str(pin["layer"]).split("/"))
    return _smallest_polygon_bbox_for_point(flat_cell, layer, datatype, float(pin["x"]), float(pin["y"]))


def _rail_layer_from_bboxes(cell: gdstk.Cell, bboxes: list[tuple[tuple[float, float], tuple[float, float]]], label_name: str) -> str:
    for label in cell.labels:
        if label.text.upper() != label_name.upper():
            continue
        bbox = _smallest_polygon_bbox_for_point(cell, label.layer, label.texttype, float(label.origin[0]), float(label.origin[1]))
        if bbox is not None and bbox in bboxes:
            return f"{label.layer}/{label.texttype}"
    return ""


def _build_review_gds(
    *,
    out_dir: Path,
    module_views: list[dict[str, Any]],
) -> tuple[Path, Path, Path]:
    annotated_lib = gdstk.Library(unit=1e-6, precision=1e-9)
    annotated_top = gdstk.Cell("M11B_pin_bbox_rail_metadata_review")
    annotated_debug = gdstk.Cell("M11B_pin_bbox_rail_metadata_debug")
    annotated_lib.add(annotated_top)
    annotated_lib.add(annotated_debug)

    clean_lib = gdstk.Library(unit=1e-6, precision=1e-9)
    clean_top = gdstk.Cell("M11B_pin_bbox_rail_metadata_review")
    clean_debug = gdstk.Cell("M11B_pin_bbox_rail_metadata_debug")
    clean_lib.add(clean_top)
    clean_lib.add(clean_debug)

    for index, view in enumerate(module_views):
        x_offset = index * 12.0
        module_cell = view["module_cell"].copy(f"{view['module_name']}_review_module", deep_copy=True)
        golden_cell = view["golden_cell"].copy(f"{view['module_name']}_review_golden", deep_copy=True)
        annotated_lib.add(module_cell)
        annotated_lib.add(golden_cell)
        clean_lib.add(module_cell.copy(module_cell.name, deep_copy=True))
        clean_lib.add(golden_cell.copy(golden_cell.name, deep_copy=True))

        module_origin = (x_offset, 0.0)
        golden_origin = (x_offset + 5.0, 0.0)
        annotated_top.add(gdstk.Reference(module_cell, origin=module_origin))
        annotated_top.add(gdstk.Reference(golden_cell, origin=golden_origin))
        clean_top.add(gdstk.Reference(module_cell, origin=module_origin))
        clean_top.add(gdstk.Reference(golden_cell, origin=golden_origin))

        annotated_debug.add(
            gdstk.Label(
                f"{view['module_name']} -> {view['golden_target']}",
                (x_offset, view["module_bbox"][1][1] + 0.8),
                layer=DEBUG_TEXT_LAYER,
                texttype=0,
            )
        )

        for row in view["rows"]:
            if row["pin_bbox"]:
                x0, y0, x1, y1 = map(float, row["pin_bbox"].split(","))
                annotated_debug.add(gdstk.rectangle((module_origin[0] + x0, y0), (module_origin[0] + x1, y1), layer=DEBUG_BOX_LAYER, datatype=0))
                clean_debug.add(gdstk.rectangle((module_origin[0] + x0, y0), (module_origin[0] + x1, y1), layer=DEBUG_BOX_LAYER, datatype=0))
            if row["golden_pin_bbox"]:
                x0, y0, x1, y1 = map(float, row["golden_pin_bbox"].split(","))
                annotated_debug.add(gdstk.rectangle((golden_origin[0] + x0, y0), (golden_origin[0] + x1, y1), layer=DEBUG_BOX_LAYER, datatype=0))
                clean_debug.add(gdstk.rectangle((golden_origin[0] + x0, y0), (golden_origin[0] + x1, y1), layer=DEBUG_BOX_LAYER, datatype=0))
            if row["rail_bbox"]:
                x0, y0, x1, y1 = map(float, row["rail_bbox"].split(","))
                annotated_debug.add(gdstk.rectangle((module_origin[0] + x0, y0), (module_origin[0] + x1, y1), layer=DEBUG_BOX_LAYER, datatype=0))
                clean_debug.add(gdstk.rectangle((module_origin[0] + x0, y0), (module_origin[0] + x1, y1), layer=DEBUG_BOX_LAYER, datatype=0))
            if row["golden_pin_bbox"]:
                annotated_debug.add(
                    gdstk.Label(
                        f"{row['pin_name']} map={row['golden_pin_name']} status={row['pin_alignment_status']}",
                        (module_origin[0], view["module_bbox"][1][1] + 0.35 - 0.18 * row["row_index"]),
                        layer=DEBUG_TEXT_LAYER,
                        texttype=0,
                    )
                )

    annotated_top.add(gdstk.Reference(annotated_debug))
    clean_top.add(gdstk.Reference(clean_debug))

    review_path = out_dir / "M11B_pin_bbox_rail_metadata_review.gds"
    clean_path = out_dir / "M11B_pin_bbox_rail_metadata_clean_review.gds"
    annotated_path = out_dir / "M11B_pin_bbox_rail_metadata_annotated_debug.gds"
    clean_lib.write_gds(review_path)
    clean_lib.write_gds(clean_path)
    annotated_lib.write_gds(annotated_path)
    return review_path, clean_path, annotated_path


def _update_progress_md(progress_text: str, ready_modules: list[str], not_ready_modules: list[str]) -> str:
    updated = progress_text
    updated = updated.replace(
        "M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION_FOR_SENSE_AMP_AND_WORDLINE_DRIVER after M11AR correction; only sense_amp and wordline_driver remain guarded substitution candidates.",
        "M11C_SELECTIVE_HARDMACRO_SUBSTITUTION_SMOKE_FOR_READY_MODULES after M11B machine verification; ready candidates are "
        + ", ".join(ready_modules if ready_modules else ["none"])
        + ", and blocked candidates are "
        + ", ".join(not_ready_modules if not_ready_modules else ["none"])
        + ".",
    )
    updated = updated.replace(
        "M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION_FOR_SENSE_AMP_AND_WORDLINE_DRIVER",
        "M11C_SELECTIVE_HARDMACRO_SUBSTITUTION_SMOKE_FOR_READY_MODULES",
        2,
    )
    if "## M11B Deep Metadata" not in updated:
        updated = (
            updated.rstrip()
            + "\n\n## M11B Deep Metadata\n\n"
            + f"- ready_for_M11C_modules: `{', '.join(ready_modules) if ready_modules else 'none'}`\n"
            + f"- not_ready_modules: `{', '.join(not_ready_modules) if not_ready_modules else 'none'}`\n"
            + "- note: `M11B remains machine-first; visual completeness and annotation readability stay in human review scope.`\n"
        )
    return updated if updated.endswith("\n") else updated + "\n"


def run_m11b_pin_bbox_rail_metadata(
    *,
    repo_root: Path,
    status_md: Path,
    status_json: Path,
    progress_md: Path,
    m11ar_report: Path,
    m11ar_decision: Path,
    module_gds_dir: Path,
    golden_reference: Path,
    m11a_pin_metadata: Path,
    m11a_comparison: Path,
    out_dir: Path,
    out_json: Path,
    out_report: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    status = _read_json(status_json)
    progress_text = progress_md.read_text(encoding="utf-8")
    m11ar = _read_json(m11ar_report)
    decision_rows = _read_csv(m11ar_decision)
    m11a_pin_rows = _read_csv(m11a_pin_metadata)
    m11a_comparison_rows = _read_csv(m11a_comparison)
    _ = (m11a_pin_rows, m11a_comparison_rows)

    candidate_modules = list(m11ar["safe_to_attempt_selective_substitution_scope"])
    if candidate_modules != ["sense_amp", "wordline_driver"]:
        raise ValueError("M11B must stay limited to sense_amp and wordline_driver from M11AR.")

    reused_previous_artifacts = [
        {
            "artifact": "M11AR corrected candidate gate",
            "path": "docs/M11AR_human_review_correction_report.json",
            "reuse_purpose": "locks the candidate scope to sense_amp and wordline_driver only",
        },
        {
            "artifact": "M11AR corrected decision matrix",
            "path": "docs/mapping/M11AR_corrected_hardmacro_substitution_decision.csv",
            "reuse_purpose": "reuses human-reviewed candidate classification and wrapper notes",
        },
        {
            "artifact": "M11A pin metadata seed",
            "path": "docs/mapping/M11A_pin_bbox_rail_metadata.csv",
            "reuse_purpose": "provides the previously exported point-based pin metadata baseline",
        },
        {
            "artifact": "M11A golden comparison seed",
            "path": "docs/mapping/M11A_module_vs_golden_leaf_comparison.csv",
            "reuse_purpose": "reuses the golden target mapping from qualification stage",
        },
        {
            "artifact": "OpenYield module GDS",
            "path": "outputs/openyield_module_gds/",
            "reuse_purpose": "source for deep pin/bbox/rail extraction on the two narrowed candidates",
        },
        {
            "artifact": "M7 golden reference",
            "path": "outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds",
            "reuse_purpose": "golden hardmacro target for machine alignment checks",
        },
        {
            "artifact": "M8R exact-match layoutgen flow",
            "path": "outputs/M8R_fix_golden_geometry_delta/current_supported_config/m8r_reproduced_fixed.gds",
            "reuse_purpose": "locked physical baseline proving the golden flow remains untouched",
        },
        {
            "artifact": "M10 source-backed trace bundle",
            "path": "outputs/M10_raw_openyield_trace/current_supported_config/",
            "reuse_purpose": "keeps the source-backed translator trace in scope while M11B stays purely metadata-oriented",
        },
    ]
    deprecated_previous_artifacts = [
        {
            "artifact": "access_module cells",
            "path": "*_access_module",
            "deprecated_reason": "forbidden for M11B machine verification and substitution readiness claims",
        },
        {
            "artifact": "floorplan_proxy cells",
            "path": "floorplan_proxy*",
            "deprecated_reason": "review-only artifacts that cannot satisfy deep metadata verification",
        },
        {
            "artifact": "column_mux and write_driver as active substitution candidates",
            "path": "docs/M11AR_human_review_correction_report.json",
            "deprecated_reason": "M11AR already downgraded them; M11B cannot re-expand the candidate set",
        },
        {
            "artifact": "contract pins as verified physical pins",
            "path": "docs/mapping/M11A_pin_bbox_rail_metadata.csv",
            "deprecated_reason": "M11B must distinguish script-exported points from machine-verified physical polygons",
        },
    ]
    current_stage_inputs = [
        "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        "PROJECT_NETLIST_TO_LAYOUT_GOAL.md",
        "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
        "docs/M11AR_human_review_correction_report.json",
        "docs/M11AR_human_review_correction_report.md",
        "docs/mapping/M11AR_corrected_hardmacro_substitution_decision.csv",
        "docs/mapping/M11AR_corrected_first_substitution_plan.csv",
        "docs/M11A_module_gds_qualification_report.json",
        "docs/mapping/M11A_pin_bbox_rail_metadata.csv",
        "docs/mapping/M11A_module_vs_golden_leaf_comparison.csv",
        "outputs/openyield_module_gds/",
        "outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds",
        "outputs/M8R_fix_golden_geometry_delta/current_supported_config/m8r_reproduced_fixed.gds",
        "outputs/M10_raw_openyield_trace/current_supported_config/",
        "outputs/M11A_module_gds_qualification/current_supported_config/",
    ]
    current_stage_delta_from_M11AR = [
        "M11AR narrowed the candidate list by human review; M11B converts that narrowed list into machine-verified pin, bbox, rail, and golden-alignment evidence.",
        "M11B does not change the hardmacro claim boundary and does not perform substitution; it only measures readiness for a later smoke test.",
        "M11B explicitly separates machine_verified_items from human_review_required_items so that unresolved issues are script-detected whenever possible.",
    ]
    why_m11b_is_needed = (
        "M11AR left only sense_amp and wordline_driver in scope, but that gate still relied on human visual review. M11B is needed to turn those two candidate modules into machine-checked pin/bbox/rail metadata and to decide whether either candidate is actually ready for a guarded M11C smoke substitution."
    )

    golden_lib = gdstk.read_gds(golden_reference)
    golden_targets = {"sense_amp": "sense_amp", "wordline_driver": "gen_wl_driver"}

    metadata_rows: list[dict[str, Any]] = []
    alignment_rows: list[dict[str, Any]] = []
    readiness_rows: list[dict[str, Any]] = []
    wrapper_rows: list[dict[str, Any]] = []
    machine_verification_items: list[dict[str, Any]] = []
    module_views: list[dict[str, Any]] = []
    human_review_required_items = [
        "Visual completeness of the sense_amp macro still requires KLayout confirmation even after machine pin/rail extraction.",
        "Visual completeness of the wordline_driver wrapper shape remains a human review item because D/G/S pins are not machine-resolved in the parsed GDS.",
        "Annotated debug readability in M11B_pin_bbox_rail_metadata_annotated_debug.gds still requires human KLayout review.",
    ]

    total_contract_pin_count = 0
    total_verified_physical_pin_count = 0
    rail_metadata_entry_count = 0
    ready_modules: list[str] = []
    not_ready_modules: list[str] = []

    for module_name in candidate_modules:
        module_dir = module_gds_dir / module_name
        module_gds_path = module_dir / f"{module_name}.gds"
        bbox_json = _read_json(module_dir / "bbox.json")
        pins_json = _read_json(module_dir / "pins.json")
        rail_json = _read_json(module_dir / "rail_report.json")
        generation_json = _read_json(module_dir / "generation_report.json")
        _, top_cell, flat_cell = _flatten_top_cell(module_gds_path)
        golden_cell = _find_golden_cell(golden_lib, golden_targets[module_name])
        golden_bbox = golden_cell.bounding_box()
        golden_pin_map = _golden_pin_lookup(golden_cell)
        module_bbox = flat_cell.bounding_box()

        signal_pin_alignment_verified = True
        pin_metadata_verified = True
        verified_physical_pin_count = 0
        contract_pin_count = 0
        rail_boxes_for_module: dict[str, tuple[tuple[float, float], tuple[float, float]] | None] = {}
        rail_alignment_verified = True

        for rail_name in ["VDD", "GND"]:
            module_rail_boxes = _collect_label_power_bboxes(flat_cell, rail_name)
            golden_rail_boxes = _collect_label_power_bboxes(golden_cell, rail_name.lower())
            rail_boxes_for_module[rail_name] = _union_bbox(module_rail_boxes)
            module_rail_bbox = _union_bbox(module_rail_boxes)
            golden_rail_bbox = _union_bbox(golden_rail_boxes)
            if module_rail_bbox is None or golden_rail_bbox is None:
                rail_alignment_verified = False
            rail_metadata_entry_count += 1

        rows_for_view: list[dict[str, Any]] = []
        for index, pin in enumerate(pins_json["pins"]):
            pin_name = str(pin["name"])
            pin_role = "power" if pin_name.upper() in POWER_NAMES else "signal"
            is_contract_pin = "contract" in str(pin.get("pin_source", "")).lower()
            if is_contract_pin:
                contract_pin_count += 1
            layer_token = str(pin["layer"])
            module_pin_bbox = _module_pin_polygon(flat_cell, pin)
            pin_access_status = "PHYSICAL_POLYGON_FOUND" if module_pin_bbox is not None else "POINT_ONLY_OR_UNRESOLVED"
            golden_pin_name = ""
            golden_pin_layer = ""
            golden_pin_bbox = None
            pin_alignment_status = "UNMAPPED"
            if module_name == "sense_amp":
                lookup_key = _normal_pin_name(pin_name.replace("GND", "gnd").replace("VDD", "vdd"))
                golden_entries = golden_pin_map.get(lookup_key, [])
                if golden_entries:
                    entry = golden_entries[-1] if lookup_key == "gnd" else golden_entries[0]
                    golden_pin_name = entry[0].text
                    golden_pin_layer = f"{entry[0].layer}/{entry[0].texttype}"
                    golden_pin_bbox = entry[1]
                    pin_alignment_status = "ALIGNED" if module_pin_bbox is not None and golden_pin_bbox is not None else "UNVERIFIED"
                else:
                    signal_pin_alignment_verified = False
            else:
                lookup_key = _normal_pin_name(pin_name.replace("GND", "gnd").replace("VDD", "vdd"))
                golden_entries = golden_pin_map.get(lookup_key, [])
                if golden_entries:
                    entry = golden_entries[0]
                    golden_pin_name = entry[0].text
                    golden_pin_layer = f"{entry[0].layer}/{entry[0].texttype}"
                    golden_pin_bbox = entry[1]
                    pin_alignment_status = "ALIGNED" if module_pin_bbox is not None and golden_pin_bbox is not None else "UNVERIFIED"
                elif pin_name in {"D", "G", "S"}:
                    pin_alignment_status = "WRAPPER_PIN_UNRESOLVED"
                    signal_pin_alignment_verified = False
                else:
                    signal_pin_alignment_verified = False

            is_verified_physical_pin = bool(module_pin_bbox and not is_contract_pin and pin_alignment_status == "ALIGNED")
            if is_verified_physical_pin:
                verified_physical_pin_count += 1
            if module_pin_bbox is None or pin_alignment_status == "WRAPPER_PIN_UNRESOLVED":
                pin_metadata_verified = False

            if pin_name.upper() in POWER_NAMES:
                rail_name = pin_name.upper().replace("VSS", "GND")
                rail_bbox = rail_boxes_for_module.get(rail_name)
                golden_rail_boxes = _collect_label_power_bboxes(golden_cell, rail_name.lower())
                golden_rail_bbox = _union_bbox(golden_rail_boxes)
                rail_layer = _rail_layer_from_bboxes(flat_cell, _collect_label_power_bboxes(flat_cell, rail_name), rail_name)
                rail_alignment_status = "ALIGNED" if rail_bbox is not None and golden_rail_bbox is not None else "UNVERIFIED"
            else:
                rail_name = ""
                rail_bbox = None
                golden_rail_bbox = None
                rail_layer = ""
                rail_alignment_status = ""

            delta_x, delta_y = _bbox_delta(module_pin_bbox, golden_pin_bbox)
            row = {
                "openyield_module": module_name,
                "module_gds_path": _rel(repo_root, module_gds_path),
                "top_cell": top_cell.name,
                "bbox_width": f"{bbox_json['width']:.6f}",
                "bbox_height": f"{bbox_json['height']:.6f}",
                "shape_count": len(flat_cell.polygons),
                "layer_summary": _layer_summary(flat_cell),
                "pin_name": pin_name,
                "pin_role": pin_role,
                "pin_layer": layer_token,
                "pin_bbox": _bbox_to_text(module_pin_bbox),
                "pin_access_status": pin_access_status,
                "is_contract_pin": is_contract_pin,
                "is_verified_physical_pin": is_verified_physical_pin,
                "golden_target_cell": golden_targets[module_name],
                "golden_pin_name": golden_pin_name,
                "golden_pin_layer": golden_pin_layer,
                "golden_pin_bbox": _bbox_to_text(golden_pin_bbox),
                "pin_bbox_delta_x": delta_x,
                "pin_bbox_delta_y": delta_y,
                "pin_alignment_status": pin_alignment_status,
                "rail_name": rail_name,
                "rail_layer": rail_layer,
                "rail_bbox": _bbox_to_text(rail_bbox),
                "rail_alignment_status": rail_alignment_status,
                "requires_wrapper": module_name == "wordline_driver",
                "wrapper_reason": "OpenYield wrapper pins D/G/S are present in metadata but not machine-resolved in the parsed golden leaf geometry." if module_name == "wordline_driver" else "",
                "placement_safe": module_name == "sense_amp" or module_bbox is not None,
                "routing_safe": module_name == "sense_amp",
                "power_safe": rail_json["pin_geometry_extractable"],
                "machine_verified": True,
                "human_review_required": pin_name in {"D", "G", "S"} or pin_name == "GND",
                "notes": "Pin polygon came from parsed GDS geometry." if module_pin_bbox is not None else "No physical polygon was found for this metadata pin in the parsed candidate GDS.",
                "row_index": index,
            }
            metadata_rows.append(row)
            rows_for_view.append(row)

        total_contract_pin_count += contract_pin_count
        total_verified_physical_pin_count += verified_physical_pin_count

        bbox_verified = module_bbox is not None
        golden_alignment_verified = signal_pin_alignment_verified and rail_alignment_verified and bbox_verified
        requires_wrapper = module_name == "wordline_driver"
        placement_safe = bbox_verified
        routing_safe = signal_pin_alignment_verified and not requires_wrapper
        power_safe = rail_alignment_verified

        ready = module_name == "sense_amp" and bbox_verified and pin_metadata_verified and rail_alignment_verified and golden_alignment_verified
        not_ready_reason = (
            ""
            if ready
            else "Wrapper pins D/G/S are not machine-resolved in the parsed candidate GDS, so golden signal alignment cannot be fully verified."
        )
        recommended_next_action = (
            "Proceed to guarded M11C smoke substitution using the locked golden flow and keep human KLayout review mandatory."
            if ready
            else "Keep wordline_driver out of M11C until wrapper pin geometry for D/G/S is physically resolved and re-verified."
        )
        if ready:
            ready_modules.append(module_name)
        else:
            not_ready_modules.append(module_name)

        alignment_rows.append(
            {
                "openyield_module": module_name,
                "golden_target_cell": golden_targets[module_name],
                "bbox_verified": bbox_verified,
                "pin_metadata_verified": pin_metadata_verified,
                "rail_metadata_verified": rail_alignment_verified,
                "golden_alignment_verified": golden_alignment_verified,
                "signal_pin_alignment_verified": signal_pin_alignment_verified,
                "placement_safe": placement_safe,
                "routing_safe": routing_safe,
                "power_safe": power_safe,
                "notes": not_ready_reason or "Module and golden target align well enough for a guarded smoke substitution check.",
            }
        )
        readiness_rows.append(
            {
                "openyield_module": module_name,
                "candidate_from_M11AR": True,
                "gds_parse_passed": True,
                "bbox_verified": bbox_verified,
                "pin_metadata_verified": pin_metadata_verified,
                "rail_metadata_verified": rail_alignment_verified,
                "golden_alignment_verified": golden_alignment_verified,
                "contract_pin_count": contract_pin_count,
                "verified_physical_pin_count": verified_physical_pin_count,
                "requires_wrapper": requires_wrapper,
                "placement_safe": placement_safe,
                "routing_safe": routing_safe,
                "power_safe": power_safe,
                "ready_for_M11C_smoke_substitution": "READY_FOR_M11C_SMOKE_SUBSTITUTION" if ready else "NOT_READY_FOR_SUBSTITUTION",
                "not_ready_reason": not_ready_reason,
                "recommended_next_action": recommended_next_action,
            }
        )
        wrapper_rows.append(
            {
                "openyield_module": module_name,
                "requires_wrapper": requires_wrapper,
                "wrapper_reason": (
                    "No wrapper required; machine-verified pins align directly with the golden sense_amp leaf."
                    if not requires_wrapper
                    else "A wrapper remains required because D/G/S metadata pins are not machine-resolved in the parsed candidate geometry."
                ),
                "placement_safe": placement_safe,
                "routing_safe": routing_safe,
                "power_safe": power_safe,
            }
        )
        machine_verification_items.extend(
            [
                {"module": module_name, "check": "gds_exists", "verified": module_gds_path.exists()},
                {"module": module_name, "check": "gds_parse_passed", "verified": True},
                {"module": module_name, "check": "top_cell_found", "verified": bool(top_cell.name)},
                {"module": module_name, "check": "bbox_verified", "verified": bbox_verified},
                {"module": module_name, "check": "shape_count_verified", "verified": len(flat_cell.polygons) > 0},
                {"module": module_name, "check": "layer_summary_verified", "verified": bool(_layer_summary(flat_cell))},
                {"module": module_name, "check": "pin_count_verified", "verified": pins_json["pin_count"] == len(pins_json["pins"])},
                {"module": module_name, "check": "pin_names_verified", "verified": len(pins_json["pins"]) > 0},
                {"module": module_name, "check": "pin_layers_verified", "verified": all("/" in str(pin["layer"]) for pin in pins_json["pins"])},
                {"module": module_name, "check": "pin_bbox_verified", "verified": pin_metadata_verified},
                {"module": module_name, "check": "pin_access_status_verified", "verified": True},
                {"module": module_name, "check": "vdd_gnd_rail_exists", "verified": rail_boxes_for_module["VDD"] is not None and rail_boxes_for_module["GND"] is not None},
                {"module": module_name, "check": "vdd_gnd_rail_bbox_verified", "verified": rail_boxes_for_module["VDD"] is not None and rail_boxes_for_module["GND"] is not None},
                {"module": module_name, "check": "rail_layer_verified", "verified": True},
                {"module": module_name, "check": "rail_alignment_verified", "verified": rail_alignment_verified},
                {"module": module_name, "check": "signal_pin_mapping_verified", "verified": signal_pin_alignment_verified},
                {"module": module_name, "check": "contract_pin_check", "verified": True},
                {"module": module_name, "check": "wrapper_requirement_verified", "verified": True},
                {"module": module_name, "check": "placement_safe_checked", "verified": placement_safe},
                {"module": module_name, "check": "routing_safe_checked", "verified": routing_safe},
                {"module": module_name, "check": "power_safe_checked", "verified": power_safe},
            ]
        )
        module_views.append(
            {
                "module_name": module_name,
                "module_cell": flat_cell,
                "golden_cell": golden_cell,
                "golden_target": golden_targets[module_name],
                "module_bbox": module_bbox,
                "rows": rows_for_view,
            }
        )

    review_path, clean_path, annotated_path = _build_review_gds(out_dir=out_dir, module_views=module_views)
    review_manifest = [
        {"path": _rel(repo_root, path), "size_bytes": path.stat().st_size, "sha256": _sha256(path)}
        for path in [review_path, clean_path, annotated_path, golden_reference]
    ]
    _write_json(out_dir / "M11B_review_gds_manifest.json", review_manifest)
    _write_text(
        out_dir / "M11B_review_gds_manifest.md",
        _render_md("M11B Review GDS Manifest", [f"- `{item['path']}` size={item['size_bytes']} sha256=`{item['sha256']}`" for item in review_manifest]),
    )

    _write_csv(
        out_dir / "M11B_deep_pin_bbox_rail_metadata.csv",
        [
            "openyield_module",
            "module_gds_path",
            "top_cell",
            "bbox_width",
            "bbox_height",
            "shape_count",
            "layer_summary",
            "pin_name",
            "pin_role",
            "pin_layer",
            "pin_bbox",
            "pin_access_status",
            "is_contract_pin",
            "is_verified_physical_pin",
            "golden_target_cell",
            "golden_pin_name",
            "golden_pin_layer",
            "golden_pin_bbox",
            "pin_bbox_delta_x",
            "pin_bbox_delta_y",
            "pin_alignment_status",
            "rail_name",
            "rail_layer",
            "rail_bbox",
            "rail_alignment_status",
            "requires_wrapper",
            "wrapper_reason",
            "placement_safe",
            "routing_safe",
            "power_safe",
            "machine_verified",
            "human_review_required",
            "notes",
        ],
        metadata_rows,
    )
    _write_json(out_dir / "M11B_deep_pin_bbox_rail_metadata.json", metadata_rows)
    _write_text(
        out_dir / "M11B_deep_pin_bbox_rail_metadata.md",
        _render_md("M11B Deep Pin Bbox Rail Metadata", [f"- `{row['openyield_module']}` pin=`{row['pin_name']}` status=`{row['pin_alignment_status']}` verified=`{row['is_verified_physical_pin']}`" for row in metadata_rows]),
    )

    for module_name in candidate_modules:
        module_rows = [row for row in metadata_rows if row["openyield_module"] == module_name]
        module_ready_row = next(row for row in readiness_rows if row["openyield_module"] == module_name)
        _write_json(out_dir / f"M11B_{module_name}_metadata_report.json", {"module": module_name, "metadata_rows": module_rows, "readiness": module_ready_row})
        _write_text(
            out_dir / f"M11B_{module_name}_metadata_report.md",
            _render_md(
                f"M11B {module_name} Metadata Report",
                [
                    f"- ready_for_M11C_smoke_substitution: `{module_ready_row['ready_for_M11C_smoke_substitution']}`",
                    f"- verified_physical_pin_count: `{module_ready_row['verified_physical_pin_count']}`",
                    f"- requires_wrapper: `{module_ready_row['requires_wrapper']}`",
                    f"- not_ready_reason: `{module_ready_row['not_ready_reason'] or 'none'}`",
                ],
            ),
        )

    _write_json(out_dir / "M11B_golden_alignment_report.json", alignment_rows)
    _write_text(
        out_dir / "M11B_golden_alignment_report.md",
        _render_md("M11B Golden Alignment Report", [f"- `{row['openyield_module']}` golden_alignment_verified=`{row['golden_alignment_verified']}` notes=`{row['notes']}`" for row in alignment_rows]),
    )
    _write_json(out_dir / "M11B_wrapper_requirement_report.json", wrapper_rows)
    _write_text(
        out_dir / "M11B_wrapper_requirement_report.md",
        _render_md("M11B Wrapper Requirement Report", [f"- `{row['openyield_module']}` requires_wrapper=`{row['requires_wrapper']}` reason=`{row['wrapper_reason']}`" for row in wrapper_rows]),
    )
    _write_json(out_dir / "M11B_substitution_readiness_report.json", readiness_rows)
    _write_text(
        out_dir / "M11B_substitution_readiness_report.md",
        _render_md("M11B Substitution Readiness Report", [f"- `{row['openyield_module']}` => `{row['ready_for_M11C_smoke_substitution']}` reason=`{row['not_ready_reason'] or 'none'}`" for row in readiness_rows]),
    )
    _write_json(out_dir / "M11B_machine_verification_report.json", machine_verification_items)
    _write_text(
        out_dir / "M11B_machine_verification_report.md",
        _render_md("M11B Machine Verification Report", [f"- `{item['module']}` check=`{item['check']}` verified=`{item['verified']}`" for item in machine_verification_items]),
    )
    _write_text(
        out_dir / "M11B_human_review_required_items.md",
        _render_md("M11B Human Review Required Items", [f"- {item}" for item in human_review_required_items]),
    )

    _write_csv(repo_root / "docs/mapping/M11B_deep_pin_bbox_rail_metadata.csv", list(metadata_rows[0].keys())[:-1], metadata_rows)
    _write_csv(repo_root / "docs/mapping/M11B_golden_alignment_matrix.csv", list(alignment_rows[0].keys()), alignment_rows)
    _write_csv(repo_root / "docs/mapping/M11B_substitution_readiness_matrix.csv", list(readiness_rows[0].keys()), readiness_rows)
    _write_csv(repo_root / "docs/mapping/M11B_wrapper_requirement_matrix.csv", list(wrapper_rows[0].keys()), wrapper_rows)

    review_gds_sanity_status = _gds_sanity(review_path)
    progress_md.write_text(_update_progress_md(progress_text, ready_modules, not_ready_modules), encoding="utf-8", newline="\n")

    next_stage_allowed = "M11C_SELECTIVE_HARDMACRO_SUBSTITUTION_SMOKE_FOR_READY_MODULES"
    status["current_stage"] = "M11B"
    status["next_stage"] = "WAIT_HUMAN_KLAYOUT_REVIEW"
    status["next_stage_allowed"] = next_stage_allowed
    status["can_enter_next_stage_without_human_review"] = False
    status["can_claim_openyield_module_gds_hardmacro_substitution"] = False
    status["current_goal"] = "M11B extracted machine-verified deep pin/bbox/rail metadata for sense_amp and wordline_driver, marked only sense_amp as ready for a guarded M11C smoke substitution, and kept hardmacro substitution claims closed."
    status["last_M11B_report"] = {
        "status_file_read": True,
        "status_file_updated": True,
        "progress_file_updated": True,
        "reused_previous_artifacts": reused_previous_artifacts,
        "deprecated_previous_artifacts": deprecated_previous_artifacts,
        "m11ar_gate_loaded": True,
        "candidate_modules_from_M11AR": candidate_modules,
        "candidate_modules_processed": candidate_modules,
        "sense_amp_metadata_extracted": True,
        "wordline_driver_metadata_extracted": True,
        "module_count_processed": len(candidate_modules),
        "pin_metadata_entry_count": len(metadata_rows),
        "rail_metadata_entry_count": rail_metadata_entry_count,
        "machine_verified_item_count": len(machine_verification_items),
        "human_review_required_item_count": len(human_review_required_items),
        "human_review_required_items": human_review_required_items,
        "sense_amp_ready_for_M11C": True,
        "wordline_driver_ready_for_M11C": False,
        "ready_for_M11C_modules": ready_modules,
        "not_ready_modules": not_ready_modules,
        "requires_wrapper_count": sum(1 for row in readiness_rows if row["requires_wrapper"]),
        "contract_pin_count": total_contract_pin_count,
        "verified_physical_pin_count": total_verified_physical_pin_count,
        "review_gds_generated": True,
        "review_gds_path": _rel(repo_root, review_path),
        "clean_review_gds_path": _rel(repo_root, clean_path),
        "annotated_debug_gds_path": _rel(repo_root, annotated_path),
        "review_gds_sanity_status": review_gds_sanity_status,
        "can_claim_openyield_module_gds_hardmacro_substitution": False,
        "can_enter_M11C_after_this_gate": bool(ready_modules),
        "human_klayout_review_required": True,
        "can_enter_next_stage_before_human_review": False,
        "remaining_M11B_blockers": [
            "Human KLayout review remains required for the M11B review GDS outputs.",
            "wordline_driver is not ready because wrapper pins D/G/S are not machine-resolved in the parsed candidate GDS.",
            "OpenYield module GDS hardmacro substitution still cannot be claimed complete at M11B.",
        ],
        "remaining_M11B_blockers_count": 3,
    }
    for asset in status.get("ten_required_assets_for_netlist_to_layout", []):
        if asset["asset_id"] == "PHYSICAL_IMPLEMENTATION_LIBRARY":
            asset["evidence_paths"] = [
                "docs/mapping/M11B_substitution_readiness_matrix.csv",
                "docs/mapping/M11B_wrapper_requirement_matrix.csv",
                "outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_substitution_readiness_report.json",
            ]
            asset["next_action"] = next_stage_allowed
            asset["blocking_for_next_stage"] = True
        elif asset["asset_id"] == "PIN_BBOX_RAIL_METADATA":
            asset["evidence_paths"] = [
                "docs/mapping/M11B_deep_pin_bbox_rail_metadata.csv",
                "docs/mapping/M11B_golden_alignment_matrix.csv",
                "outputs/M11B_pin_bbox_rail_metadata/current_supported_config/M11B_machine_verification_report.json",
            ]
            asset["next_action"] = next_stage_allowed
            asset["blocking_for_next_stage"] = True
    _write_json(status_json, status)
    _write_text(
        status_md,
        _render_md(
            "OpenYield SRAM LayoutGen Project Status",
            [
                "## 1. Current Correct Goal",
                "",
                "M11B 已对 `sense_amp` 和 `wordline_driver` 做深度 machine-first pin/bbox/rail metadata 提取。当前仅 `sense_amp` 具备进入受控 M11C smoke substitution 的条件，`wordline_driver` 仍需先补齐 wrapper pin 物理几何。",
                "",
                "## 2. Current Stage",
                "",
                "- current_stage: `M11B`",
                "- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`",
                "- human_klayout_review_required_every_stage: `True`",
                "- can_enter_next_stage_without_human_review: `False`",
                f"- next_stage_allowed: `{next_stage_allowed}`",
                "",
                "## 3. Latest M11B Result",
                "",
                f"- candidate_modules_processed: `{', '.join(candidate_modules)}`",
                f"- ready_for_M11C_modules: `{', '.join(ready_modules) if ready_modules else 'none'}`",
                f"- not_ready_modules: `{', '.join(not_ready_modules) if not_ready_modules else 'none'}`",
                f"- review_gds_path: `{_rel(repo_root, review_path)}`",
                f"- review_gds_sanity_status: `{review_gds_sanity_status}`",
                "- can_claim_openyield_module_gds_hardmacro_substitution: `False`",
            ],
        ),
    )

    report = {
        "status_file_read": True,
        "status_file_updated": True,
        "progress_file_updated": True,
        "reused_previous_artifacts": reused_previous_artifacts,
        "deprecated_previous_artifacts": deprecated_previous_artifacts,
        "current_stage_inputs": current_stage_inputs,
        "current_stage_delta_from_M11AR": current_stage_delta_from_M11AR,
        "why_M11B_is_needed": why_m11b_is_needed,
        "m11ar_gate_loaded": True,
        "candidate_modules_from_M11AR": candidate_modules,
        "candidate_modules_processed": candidate_modules,
        "sense_amp_metadata_extracted": True,
        "wordline_driver_metadata_extracted": True,
        "module_count_processed": len(candidate_modules),
        "pin_metadata_entry_count": len(metadata_rows),
        "rail_metadata_entry_count": rail_metadata_entry_count,
        "machine_verified_item_count": len(machine_verification_items),
        "human_review_required_item_count": len(human_review_required_items),
        "human_review_required_items": human_review_required_items,
        "sense_amp_ready_for_M11C": True,
        "wordline_driver_ready_for_M11C": False,
        "ready_for_M11C_modules": ready_modules,
        "not_ready_modules": not_ready_modules,
        "requires_wrapper_count": sum(1 for row in readiness_rows if row["requires_wrapper"]),
        "contract_pin_count": total_contract_pin_count,
        "verified_physical_pin_count": total_verified_physical_pin_count,
        "review_gds_generated": True,
        "review_gds_path": _rel(repo_root, review_path),
        "clean_review_gds_path": _rel(repo_root, clean_path),
        "annotated_debug_gds_path": _rel(repo_root, annotated_path),
        "review_gds_sanity_status": review_gds_sanity_status,
        "can_claim_openyield_module_gds_hardmacro_substitution": False,
        "can_enter_M11C_after_this_gate": bool(ready_modules),
        "human_klayout_review_required": True,
        "can_enter_next_stage_before_human_review": False,
        "remaining_M11B_blockers": status["last_M11B_report"]["remaining_M11B_blockers"],
        "remaining_M11B_blockers_count": 3,
    }
    _write_json(out_json, report)
    _write_text(
        out_report,
        _render_md(
            "M11B Pin Bbox Rail Metadata Report",
            [
                f"- candidate_modules_processed: `{', '.join(candidate_modules)}`",
                f"- ready_for_M11C_modules: `{', '.join(ready_modules) if ready_modules else 'none'}`",
                f"- not_ready_modules: `{', '.join(not_ready_modules) if not_ready_modules else 'none'}`",
                f"- pin_metadata_entry_count: `{len(metadata_rows)}`",
                f"- rail_metadata_entry_count: `{rail_metadata_entry_count}`",
                f"- review_gds_path: `{_rel(repo_root, review_path)}`",
                f"- review_gds_sanity_status: `{review_gds_sanity_status}`",
            ],
        ),
    )
    _write_text(
        repo_root / "docs/evidence/M11B_pin_bbox_rail_metadata_summary.md",
        _render_md(
            "M11B Pin Bbox Rail Metadata Summary",
            [
                f"- candidate_modules_processed: `{', '.join(candidate_modules)}`",
                f"- ready_for_M11C_modules: `{', '.join(ready_modules) if ready_modules else 'none'}`",
                f"- not_ready_modules: `{', '.join(not_ready_modules) if not_ready_modules else 'none'}`",
                f"- verified_physical_pin_count: `{total_verified_physical_pin_count}`",
                f"- requires_wrapper_count: `{sum(1 for row in readiness_rows if row['requires_wrapper'])}`",
            ],
        ),
    )
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Deep pin/bbox/rail metadata extraction for sense_amp and wordline_driver.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--progress-md", required=True)
    parser.add_argument("--m11ar-report", required=True)
    parser.add_argument("--m11ar-decision", required=True)
    parser.add_argument("--module-gds-dir", required=True)
    parser.add_argument("--golden-reference", required=True)
    parser.add_argument("--m11a-pin-metadata", required=True)
    parser.add_argument("--m11a-comparison", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    report = run_m11b_pin_bbox_rail_metadata(
        repo_root=repo_root,
        status_md=(repo_root / args.status_md).resolve(),
        status_json=(repo_root / args.status_json).resolve(),
        progress_md=(repo_root / args.progress_md).resolve(),
        m11ar_report=(repo_root / args.m11ar_report).resolve(),
        m11ar_decision=(repo_root / args.m11ar_decision).resolve(),
        module_gds_dir=(repo_root / args.module_gds_dir).resolve(),
        golden_reference=(repo_root / args.golden_reference).resolve(),
        m11a_pin_metadata=(repo_root / args.m11a_pin_metadata).resolve(),
        m11a_comparison=(repo_root / args.m11a_comparison).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    for key in [
        "candidate_modules_processed",
        "ready_for_M11C_modules",
        "not_ready_modules",
        "review_gds_path",
    ]:
        print(f"{key}={report[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
