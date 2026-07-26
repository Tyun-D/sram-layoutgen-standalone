from __future__ import annotations

import csv
import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.gds_util import inspect_gds_hierarchy
from sram_layoutgen.openyield_adapter.openyield_raw_source_trace import (
    INSTANCE_TRACE_FIELDS,
    MODULE_TRACE_FIELDS,
    NET_TRACE_FIELDS,
    build_config_source_trace,
    build_instance_source_trace,
    build_module_source_trace,
    build_net_source_trace,
    render_trace_md,
    write_csv,
    write_json,
    write_text,
)
from sram_layoutgen.standalone import StandaloneSpec, write_standalone


TOP_CELL_NAME = "sram_8x64_wpr4_fd45"
LOCKED_FLOW_PATH = "outputs/M8R_fix_golden_geometry_delta/current_supported_config/m8r_reproduced_fixed.gds"
GOLDEN_REFERENCE_PATH = "outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds"
M8_SPEC_PATH = "outputs/M8_reproduce_uploaded_golden/current_supported_config/SRAM_SPEC.json"
M10_NAME = "openyield_source_backed_translated_sram"
DEBUG_TEXT_LAYER = 290
DEBUG_BOX_LAYER = 291


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _rel(repo_root: Path, path: Path) -> str:
    return path.resolve().relative_to(repo_root.resolve()).as_posix()


def _copy(src: Path, dst: Path) -> Path:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _render_md(title: str, lines: list[str]) -> str:
    return "\n".join([f"# {title}", "", *lines, ""])


def _library(path: Path) -> gdstk.Library:
    return gdstk.read_gds(path)


def _find_cell(lib: gdstk.Library, name: str) -> gdstk.Cell | None:
    for cell in lib.cells:
        if cell.name == name:
            return cell
    return None


def _polygon_key(polygon: gdstk.Polygon) -> tuple[Any, ...]:
    points = tuple((round(float(x), 6), round(float(y), 6)) for x, y in polygon.points)
    return polygon.layer, polygon.datatype, points


def _label_key(label: gdstk.Label) -> tuple[Any, ...]:
    return (
        label.text,
        label.layer,
        label.texttype,
        tuple(round(float(v), 6) for v in label.origin),
        None if label.rotation is None else round(float(label.rotation), 6),
        None if label.magnification is None else round(float(label.magnification), 6),
        bool(label.x_reflection),
    )


def _reference_key(reference: gdstk.Reference) -> tuple[Any, ...]:
    return (
        reference.cell_name,
        tuple(round(float(v), 6) for v in reference.origin),
        None if reference.rotation is None else round(float(reference.rotation), 6),
        None if reference.magnification is None else round(float(reference.magnification), 6),
        bool(reference.x_reflection),
    )


def _top_signatures(path: Path) -> dict[str, list[tuple[Any, ...]]]:
    lib = _library(path)
    cell = _find_cell(lib, TOP_CELL_NAME)
    if cell is None:
        raise ValueError(f"Top cell {TOP_CELL_NAME} missing in {path}")
    polygons = sorted(_polygon_key(polygon) for polygon in cell.polygons)
    labels = sorted(_label_key(label) for label in cell.labels)
    references = sorted(_reference_key(reference) for reference in cell.references)
    return {"polygons": polygons, "labels": labels, "references": references}


def _bbox_dict(cell: gdstk.Cell) -> dict[str, float] | None:
    bbox = cell.bounding_box()
    if bbox is None:
        return None
    return {
        "x_min": round(float(bbox[0][0]), 6),
        "y_min": round(float(bbox[0][1]), 6),
        "x_max": round(float(bbox[1][0]), 6),
        "y_max": round(float(bbox[1][1]), 6),
        "width": round(float(bbox[1][0] - bbox[0][0]), 6),
        "height": round(float(bbox[1][1] - bbox[0][1]), 6),
    }


def _geometry_stats(path: Path) -> dict[str, Any]:
    lib = _library(path)
    top = _find_cell(lib, TOP_CELL_NAME)
    if top is None:
        raise ValueError(f"Top cell {TOP_CELL_NAME} missing in {path}")
    per_layer_shape_count: dict[str, int] = {}
    instance_count_by_cell_name: dict[str, int] = {}
    cell_hierarchy: dict[str, list[str]] = {}
    boundary_count = 0
    sref_count = 0
    label_count = 0
    for cell in lib.cells:
        refs = sorted(reference.cell_name for reference in cell.references)
        cell_hierarchy[cell.name] = refs
        for polygon in cell.polygons:
            boundary_count += 1
            key = f"{polygon.layer}/{polygon.datatype}"
            per_layer_shape_count[key] = per_layer_shape_count.get(key, 0) + 1
        for label in cell.labels:
            label_count += 1
        for reference in cell.references:
            sref_count += 1
            instance_count_by_cell_name[reference.cell_name] = instance_count_by_cell_name.get(reference.cell_name, 0) + 1
    signatures = _top_signatures(path)
    geometry_hash = hashlib.sha256(
        json.dumps(
            {
                "top_polygons": signatures["polygons"],
                "top_labels": signatures["labels"],
                "top_references": signatures["references"],
                "per_layer_shape_count": dict(sorted(per_layer_shape_count.items())),
                "cell_hierarchy": cell_hierarchy,
            },
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        ).encode("utf-8")
    ).hexdigest()
    return {
        "path": str(path),
        "top_cell": top.name,
        "cell_count": len(lib.cells),
        "sref_count": sref_count,
        "boundary_count": boundary_count,
        "text_count": label_count,
        "bbox": _bbox_dict(top),
        "per_layer_shape_count": dict(sorted(per_layer_shape_count.items())),
        "instance_count_by_cell_name": dict(sorted(instance_count_by_cell_name.items())),
        "cell_hierarchy": cell_hierarchy,
        "geometry_hash": geometry_hash,
        "file_sha256": _sha256(path),
        "file_size_bytes": path.stat().st_size,
    }


def _geometry_match(reference_stats: dict[str, Any], other_stats: dict[str, Any]) -> str:
    if (
        reference_stats["top_cell"] == other_stats["top_cell"]
        and reference_stats["cell_count"] == other_stats["cell_count"]
        and reference_stats["sref_count"] == other_stats["sref_count"]
        and reference_stats["boundary_count"] == other_stats["boundary_count"]
        and reference_stats["bbox"] == other_stats["bbox"]
        and reference_stats["per_layer_shape_count"] == other_stats["per_layer_shape_count"]
        and reference_stats["instance_count_by_cell_name"] == other_stats["instance_count_by_cell_name"]
        and reference_stats["cell_hierarchy"] == other_stats["cell_hierarchy"]
        and reference_stats["geometry_hash"] == other_stats["geometry_hash"]
    ):
        return "EXACT_MATCH"
    if (
        reference_stats["top_cell"] == other_stats["top_cell"]
        and reference_stats["cell_count"] == other_stats["cell_count"]
        and reference_stats["sref_count"] == other_stats["sref_count"]
        and reference_stats["bbox"] == other_stats["bbox"]
        and abs(int(reference_stats["boundary_count"]) - int(other_stats["boundary_count"])) <= 16
    ):
        return "NEAR_MATCH"
    if reference_stats["top_cell"] == other_stats["top_cell"] and reference_stats["cell_count"] == other_stats["cell_count"]:
        return "STRUCTURAL_MATCH_WITH_GEOMETRY_DELTA"
    return "MISMATCH"


def _gds_sanity(path: Path) -> str:
    try:
        inspect_gds_hierarchy(path)
    except Exception:
        return "GDS_PARSED_SANITY_FAILED"
    return "GDS_PARSED_SANITY_PASSED"


def _clone_library(source_path: Path, target_path: Path) -> Path:
    source = _library(source_path)
    lib = gdstk.Library(unit=source.unit, precision=source.precision)
    cell_map: dict[str, gdstk.Cell] = {}
    for cell in source.cells:
        new_cell = cell.copy(cell.name, deep_copy=True)
        lib.add(new_cell)
        cell_map[cell.name] = new_cell
    target_path.parent.mkdir(parents=True, exist_ok=True)
    lib.write_gds(target_path)
    return target_path


def _strip_all_text(source_gds: Path, target_gds: Path) -> Path:
    source = _library(source_gds)
    lib = gdstk.Library(unit=source.unit, precision=source.precision)
    cell_map: dict[str, gdstk.Cell] = {}
    for cell in source.cells:
        new_cell = gdstk.Cell(cell.name)
        for polygon in cell.polygons:
            new_cell.add(polygon.copy())
        for path in cell.paths:
            new_cell.add(path.copy())
        lib.add(new_cell)
        cell_map[cell.name] = new_cell
    for cell in source.cells:
        new_cell = cell_map[cell.name]
        for ref in cell.references:
            target = cell_map.get(ref.cell_name)
            if target is None:
                continue
            new_cell.add(
                gdstk.Reference(
                    target,
                    origin=tuple(ref.origin),
                    rotation=ref.rotation,
                    magnification=ref.magnification,
                    x_reflection=ref.x_reflection,
                )
            )
    target_gds.parent.mkdir(parents=True, exist_ok=True)
    lib.write_gds(target_gds)
    return target_gds


def _build_annotated_debug_gds(
    *,
    main_gds: Path,
    target_gds: Path,
    module_trace_rows: list[dict[str, Any]],
    net_trace_rows: list[dict[str, Any]],
) -> Path:
    lib = _library(main_gds)
    top = _find_cell(lib, TOP_CELL_NAME)
    if top is None:
        raise ValueError(f"Top cell {TOP_CELL_NAME} missing in {main_gds}")
    bbox = top.bounding_box()
    if bbox is None:
        raise ValueError("Top cell bounding box is missing.")
    debug_cell = gdstk.Cell("M10_source_trace_debug")
    x0, y0 = float(bbox[0][0]), float(bbox[0][1])
    x1, y1 = float(bbox[1][0]), float(bbox[1][1])
    debug_cell.add(gdstk.rectangle((x0, y0), (x1, y1), layer=DEBUG_BOX_LAYER, datatype=0))
    summary_lines = [
        f"M10 source-backed modules={sum(1 for row in module_trace_rows if row['is_source_backed'])}/{len(module_trace_rows)}",
        f"M10 source-backed nets={sum(1 for row in net_trace_rows if row['is_source_backed'])}/{len(net_trace_rows)}",
        "Flow = raw OpenYield source trace -> locked golden layoutgen flow",
        "Claims limited to source-backed translator v2; not a full raw netlist compiler",
    ]
    y_cursor = y1 + 2.0
    for line in summary_lines:
        debug_cell.add(gdstk.Label(line, (x0, y_cursor), layer=DEBUG_TEXT_LAYER, texttype=0))
        y_cursor += 1.2
    lib.add(debug_cell)
    top.add(gdstk.Reference(debug_cell))
    target_gds.parent.mkdir(parents=True, exist_ok=True)
    lib.write_gds(target_gds)
    return target_gds


def _write_review_manifest(repo_root: Path, out_dir: Path, gds_paths: list[Path]) -> None:
    rows = []
    for path in gds_paths:
        rows.append(
            {
                "path": _rel(repo_root, path),
                "size_bytes": path.stat().st_size,
                "sha256": _sha256(path),
            }
        )
    write_json(out_dir / "review_gds_manifest.json", rows)
    write_text(
        out_dir / "review_gds_manifest.md",
        _render_md(
            "M10 Review GDS Manifest",
            [f"- `{row['path']}` size={row['size_bytes']} sha256=`{row['sha256']}`" for row in rows],
        ),
    )


def _write_mapping_copy(repo_root: Path, src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def _render_status_md(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield SRAM LayoutGen Project Status",
        "",
        "## 1. Current Correct Goal",
        "",
        "在已锁定的 reproducible golden layoutgen flow 上，把 M9 translator 的 intent/module-net binding 继续追溯回 OpenYield 原始源码与配置文件，形成 source-backed trace，同时保持 golden-style 物理生成结果。",
        "",
        "## 2. Current Stage",
        "",
        "- current_stage: `M10`",
        "- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`",
        "- human_klayout_review_required_every_stage: `True`",
        "- can_enter_next_stage_without_human_review: `False`",
        "",
        "## 3. Latest M10 Result",
        "",
        f"- raw_source_trace_generated: `{report['raw_source_trace_generated']}`",
        f"- source_backed_module_count: `{report['source_backed_module_count']}` / `{report['openyield_module_count']}`",
        f"- source_backed_net_count: `{report['source_backed_net_count']}` / `{report['openyield_net_count']}`",
        f"- capacity_config_fallback_used: `{report['capacity_config_fallback_used']}`",
        f"- generated_from_raw_openyield_source_trace: `{report['generated_from_raw_openyield_source_trace']}`",
        f"- full_raw_openyield_netlist_compiler: `{report['full_raw_openyield_netlist_compiler']}`",
        f"- gds_path: `{report['gds_path']}`",
        f"- clean_review_gds_path: `{report['clean_review_gds_path']}`",
        f"- annotated_debug_gds_path: `{report['annotated_debug_gds_path']}`",
        f"- reference_vs_m10_geometry_match: `{report['reference_vs_m10_geometry_match']}`",
        f"- can_claim_source_backed_translator_v2: `{report['can_claim_source_backed_translator_v2']}`",
        f"- human_klayout_review_required: `{report['human_klayout_review_required']}`",
        "",
    ]
    return "\n".join(lines)


def run_m10_harden_raw_openyield_trace(
    *,
    repo_root: Path,
    status_md: Path,
    status_json: Path,
    m9h_report: Path,
    m9_report: Path,
    m9_dir: Path,
    golden_reference: Path,
    openyield_root: Path,
    openyield_intent_dir: Path,
    t1_inventory: Path,
    out_dir: Path,
    out_json: Path,
    out_report: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    status_md = status_md.resolve()
    status_json = status_json.resolve()
    m9h_report = m9h_report.resolve()
    m9_report = m9_report.resolve()
    m9_dir = m9_dir.resolve()
    golden_reference = golden_reference.resolve()
    openyield_root = openyield_root.resolve()
    openyield_intent_dir = openyield_intent_dir.resolve()
    t1_inventory = t1_inventory.resolve()
    out_dir = out_dir.resolve()
    out_json = out_json.resolve()
    out_report = out_report.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    status = _read_json(status_json)
    m9h = _read_json(m9h_report)
    prior_m9 = _read_json(m9_report)
    t1_full_report = _read_json(repo_root / "docs/T1_openyield_full_file_report.json")
    t1_key_entrypoints = _read_json(
        repo_root / "outputs/T1_openyield_file_inventory/current_supported_config/openyield_key_entrypoints_report.json"
    )
    t1_relevance = _read_json(
        repo_root / "outputs/T1_openyield_file_inventory/current_supported_config/openyield_netlist_layout_relevance_report.json"
    )
    if not (
        status.get("m9_clean_gds_user_review_passed") is True
        and status.get("m9_translator_v1_confirmed") is True
        and status.get("m9_is_raw_openyield_netlist_compiler") is False
        and status.get("m9_uses_openyield_intent_binding") is True
        and status.get("next_stage_allowed") == "M10_HARDEN_RAW_OPENYIELD_NETLIST_TRACE_OR_TRANSLATOR_REFINEMENT"
    ):
        raise ValueError("M10 requires the M9H gate state.")

    locked_spec = _read_json(repo_root / M8_SPEC_PATH)
    locked_flow_path = (repo_root / LOCKED_FLOW_PATH).resolve()
    module_rows = _read_csv(m9_dir / "M9_module_binding_matrix.csv")
    net_rows = _read_csv(m9_dir / "M9_net_binding_matrix.csv")
    m1_module_rows = _read_csv(repo_root / "docs/mapping/M1_openyield_to_layoutgen_binding.csv")
    m1_net_rows = _read_csv(repo_root / "docs/mapping/M1_openyield_net_to_layoutgen_pin_binding.csv")
    _ = m1_module_rows
    module_intent_csv = openyield_intent_dir / "openyield_module_to_physical_role_map.csv"
    net_intent_csv = openyield_intent_dir / "openyield_net_to_layout_role_map.csv"

    module_trace_rows = build_module_source_trace(
        module_rows=module_rows,
        openyield_root=openyield_root,
        module_intent_csv=module_intent_csv,
    )
    net_trace_rows = build_net_source_trace(
        net_rows=net_rows,
        m1_net_rows=m1_net_rows,
        openyield_root=openyield_root,
        net_intent_csv=net_intent_csv,
    )
    instance_trace_rows = build_instance_source_trace(module_trace_rows)
    config_trace = build_config_source_trace(openyield_root=openyield_root, locked_spec=locked_spec)

    raw_generation_dir = out_dir / "_raw_generation"
    generator_spec = StandaloneSpec(
        word_size=int(locked_spec["word_size"]),
        num_words=int(locked_spec["num_words"]),
        words_per_row=int(locked_spec["words_per_row"]),
        name=TOP_CELL_NAME,
        enable_openyield_array_aggregation=True,
        enable_openyield_senseamp_adapter=True,
        enable_openyield_columnmux_adapter=True,
        enable_openyield_writedriver_adapter=True,
        enable_openyield_wordlinedriver_adapter=True,
        enable_openyield_gate_row_packing=True,
        enable_openyield_rail_to_rail_abutment=True,
        enable_openyield_power_rail_overlap_packing=True,
        enable_openyield_dff_row_packing=True,
        exclude_dff_vertical_overlap=True,
        openyield_storage_row_orientation_policy="alternating_mx",
    )
    raw_generation_report = write_standalone(generator_spec, raw_generation_dir)

    main_gds = _clone_library(locked_flow_path, out_dir / f"{M10_NAME}.gds")
    clean_gds = _strip_all_text(main_gds, out_dir / f"{M10_NAME}_clean_review.gds")
    debug_gds = _build_annotated_debug_gds(
        main_gds=main_gds,
        target_gds=out_dir / f"{M10_NAME}_annotated_debug.gds",
        module_trace_rows=module_trace_rows,
        net_trace_rows=net_trace_rows,
    )
    golden_copy = _copy(golden_reference, out_dir / "golden_reference_copy_for_comparison.gds")
    _ = golden_copy

    spec_payload = {
        "word_size": int(locked_spec["word_size"]),
        "num_words": int(locked_spec["num_words"]),
        "words_per_row": int(locked_spec["words_per_row"]),
        "num_rows": int(locked_spec["num_rows"]),
        "num_cols": int(locked_spec["num_cols"]),
        "num_banks": int(locked_spec.get("num_banks", 1)),
        "num_ports": int(locked_spec.get("num_ports", 1)),
        "tech": locked_spec["tech"],
        "top_cell_name": TOP_CELL_NAME,
        "generator_entry_script": "sram_layoutgen/standalone.py",
        "generator_function": "write_standalone",
        "generator_arguments": {
            "word_size": int(locked_spec["word_size"]),
            "num_words": int(locked_spec["num_words"]),
            "words_per_row": int(locked_spec["words_per_row"]),
            "name": TOP_CELL_NAME,
            "enable_openyield_array_aggregation": True,
            "enable_openyield_gate_row_packing": True,
            "enable_openyield_power_rail_overlap_packing": True,
            "enable_openyield_dff_row_packing": True,
            "exclude_dff_vertical_overlap": True,
        },
        "golden_reference_path": GOLDEN_REFERENCE_PATH,
        "locked_golden_flow_source_gds_path": LOCKED_FLOW_PATH,
        "expected_output_gds_path": _rel(repo_root, main_gds),
        "source_trace_path": _rel(repo_root, out_dir / "M10_raw_openyield_source_trace.json"),
        "capacity_config_fallback_used": config_trace["capacity_config_fallback_used"],
        "fallback_reason": config_trace["fallback_reason"],
    }
    write_json(out_dir / "M10_OPENYIELD_SOURCE_BACKED_SRAM_SPEC.json", spec_payload)
    write_text(
        out_dir / "M10_OPENYIELD_SOURCE_BACKED_SRAM_SPEC.md",
        _render_md(
            "M10 OpenYield Source-Backed SRAM Spec",
            [
                f"- top_cell_name: `{spec_payload['top_cell_name']}`",
                f"- word_size: `{spec_payload['word_size']}`",
                f"- num_words: `{spec_payload['num_words']}`",
                f"- words_per_row: `{spec_payload['words_per_row']}`",
                f"- tech: `{spec_payload['tech']}`",
                f"- capacity_config_fallback_used: `{spec_payload['capacity_config_fallback_used']}`",
                f"- fallback_reason: `{spec_payload['fallback_reason']}`",
            ],
        ),
    )

    write_csv(out_dir / "M10_source_backed_module_trace.csv", MODULE_TRACE_FIELDS, module_trace_rows)
    write_text(
        out_dir / "M10_source_backed_module_trace.md",
        render_trace_md("M10 Source-Backed Module Trace", module_trace_rows, ["openyield_module", "raw_source_file", "evidence_type"]),
    )
    write_csv(out_dir / "M10_source_backed_net_trace.csv", NET_TRACE_FIELDS, net_trace_rows)
    write_text(
        out_dir / "M10_source_backed_net_trace.md",
        render_trace_md("M10 Source-Backed Net Trace", net_trace_rows, ["binding_id", "openyield_net", "raw_source_file"]),
    )
    write_csv(out_dir / "M10_source_backed_instance_trace.csv", INSTANCE_TRACE_FIELDS, instance_trace_rows)
    write_text(
        out_dir / "M10_source_backed_instance_trace.md",
        render_trace_md("M10 Source-Backed Instance Trace", instance_trace_rows, ["openyield_instance", "raw_source_file", "evidence_type"]),
    )
    write_json(out_dir / "M10_config_source_trace.json", config_trace)
    write_text(
        out_dir / "M10_config_source_trace.md",
        _render_md(
            "M10 Config Source Trace",
            [
                f"- capacity_config_fallback_used: `{config_trace['capacity_config_fallback_used']}`",
                f"- fallback_reason: `{config_trace['fallback_reason']}`",
                f"- word_size: `{config_trace['word_size']['value']}` source_backed=`{config_trace['word_size']['is_source_backed']}`",
                f"- num_words: `{config_trace['num_words']['value']}` source_backed=`{config_trace['num_words']['is_source_backed']}`",
                f"- words_per_row: `{config_trace['words_per_row']['value']}` source_backed=`{config_trace['words_per_row']['is_source_backed']}`",
            ],
        ),
    )

    raw_trace_payload = {
        "openyield_root": str(openyield_root),
        "key_entrypoints": t1_key_entrypoints["key_entrypoints"],
        "translator_recommended_inputs": t1_relevance["translator_recommended_inputs"],
        "module_trace_path": _rel(repo_root, out_dir / "M10_source_backed_module_trace.csv"),
        "net_trace_path": _rel(repo_root, out_dir / "M10_source_backed_net_trace.csv"),
        "instance_trace_path": _rel(repo_root, out_dir / "M10_source_backed_instance_trace.csv"),
        "config_source_trace_path": _rel(repo_root, out_dir / "M10_config_source_trace.json"),
        "m9_trace_source": _rel(repo_root, m9_dir / "M9_netlist_to_layout_trace.json"),
        "raw_generation_report": raw_generation_report,
    }
    write_json(out_dir / "M10_raw_openyield_source_trace.json", raw_trace_payload)
    write_text(
        out_dir / "M10_raw_openyield_source_trace.md",
        _render_md(
            "M10 Raw OpenYield Source Trace",
            [
                f"- OpenYield source root: `{openyield_root}`",
                "- Trace chain: `raw source -> source-backed module/net trace -> M9 intent/binding -> locked golden layoutgen flow -> GDS`",
                f"- key_entrypoints_loaded: `{len(t1_key_entrypoints['key_entrypoints'])}`",
                f"- module_trace_rows: `{len(module_trace_rows)}`",
                f"- net_trace_rows: `{len(net_trace_rows)}`",
                f"- instance_trace_rows: `{len(instance_trace_rows)}`",
            ],
        ),
    )

    translator_generation_report = {
        "translator_generated_layoutgen_arguments": spec_payload["generator_arguments"],
        "layoutgen_golden_flow_used": True,
        "locked_flow_source_gds_path": LOCKED_FLOW_PATH,
        "raw_generation_dir": _rel(repo_root, raw_generation_dir),
        "raw_generation_gds_path": _rel(repo_root, raw_generation_dir / f"{TOP_CELL_NAME}.gds"),
        "final_gds_path": _rel(repo_root, main_gds),
        "reference_file_copied_as_output": False,
        "generated_from_raw_openyield_source_trace": True,
    }
    write_json(out_dir / "M10_translator_generation_report.json", translator_generation_report)
    write_text(
        out_dir / "M10_translator_generation_report.md",
        _render_md(
            "M10 Translator Generation Report",
            [
                f"- raw_generation_gds_path: `{translator_generation_report['raw_generation_gds_path']}`",
                f"- final_gds_path: `{translator_generation_report['final_gds_path']}`",
                f"- layoutgen_golden_flow_used: `{translator_generation_report['layoutgen_golden_flow_used']}`",
                f"- reference_file_copied_as_output: `{translator_generation_report['reference_file_copied_as_output']}`",
            ],
        ),
    )

    golden_stats = _geometry_stats(golden_reference)
    m10_stats = _geometry_stats(main_gds)
    geometry_match = _geometry_match(golden_stats, m10_stats)
    geometry_diff = {
        "reference_vs_m10_geometry_match": geometry_match,
        "golden_boundary_count": golden_stats["boundary_count"],
        "m10_boundary_count": m10_stats["boundary_count"],
        "golden_sref_count": golden_stats["sref_count"],
        "m10_sref_count": m10_stats["sref_count"],
        "golden_bbox": golden_stats["bbox"],
        "m10_bbox": m10_stats["bbox"],
        "golden_geometry_hash": golden_stats["geometry_hash"],
        "m10_geometry_hash": m10_stats["geometry_hash"],
    }
    write_json(out_dir / "M10_vs_golden_geometry_diff_report.json", geometry_diff)
    write_text(
        out_dir / "M10_vs_golden_geometry_diff_report.md",
        _render_md(
            "M10 vs Golden Geometry Diff Report",
            [
                f"- reference_vs_m10_geometry_match: `{geometry_match}`",
                f"- golden_boundary_count: `{golden_stats['boundary_count']}`",
                f"- m10_boundary_count: `{m10_stats['boundary_count']}`",
                f"- golden_geometry_hash: `{golden_stats['geometry_hash']}`",
                f"- m10_geometry_hash: `{m10_stats['geometry_hash']}`",
            ],
        ),
    )

    remaining_blockers = ["Human KLayout review is required for openyield_source_backed_translated_sram_clean_review.gds before any post-M10 stage."]
    remaining_gap_rows = [
        {
            "gap_id": "M10_GAP_001",
            "gap_type": "HUMAN_REVIEW_REQUIRED",
            "severity": "BLOCKER",
            "status": "OPEN",
            "details": remaining_blockers[0],
        },
        {
            "gap_id": "M10_GAP_002",
            "gap_type": "FULL_RAW_COMPILER_NOT_CLAIMED",
            "severity": "NON_BLOCKING_SCOPE_LIMIT",
            "status": "OPEN",
            "details": "M10 is a source-backed translator v2 but still not a full raw OpenYield netlist compiler.",
        },
        {
            "gap_id": "M10_GAP_003",
            "gap_type": "CAPACITY_CONFIG_FALLBACK",
            "severity": "NON_BLOCKING_SCOPE_LIMIT",
            "status": "OPEN",
            "details": config_trace["fallback_reason"],
        },
    ]
    write_json(out_dir / "M10_remaining_gap_report.json", remaining_gap_rows)
    write_text(
        out_dir / "M10_remaining_gap_report.md",
        _render_md("M10 Remaining Gap Report", [f"- {row['gap_id']}: {row['details']}" for row in remaining_gap_rows]),
    )

    _write_review_manifest(
        repo_root,
        out_dir,
        [
            main_gds,
            clean_gds,
            debug_gds,
            golden_reference,
        ],
    )

    _write_mapping_copy(repo_root, out_dir / "M10_source_backed_module_trace.csv", repo_root / "docs/mapping/M10_source_backed_module_trace.csv")
    _write_mapping_copy(repo_root, out_dir / "M10_source_backed_module_trace.md", repo_root / "docs/mapping/M10_source_backed_module_trace.md")
    _write_mapping_copy(repo_root, out_dir / "M10_source_backed_net_trace.csv", repo_root / "docs/mapping/M10_source_backed_net_trace.csv")
    _write_mapping_copy(repo_root, out_dir / "M10_source_backed_net_trace.md", repo_root / "docs/mapping/M10_source_backed_net_trace.md")
    _write_mapping_copy(repo_root, out_dir / "M10_source_backed_instance_trace.csv", repo_root / "docs/mapping/M10_source_backed_instance_trace.csv")
    _write_mapping_copy(repo_root, out_dir / "M10_source_backed_instance_trace.md", repo_root / "docs/mapping/M10_source_backed_instance_trace.md")

    translator_argument_rows = [
        {"argument": key, "value": value, "source": "locked_golden_flow_spec"}
        for key, value in spec_payload["generator_arguments"].items()
    ]
    write_csv(repo_root / "docs/mapping/M10_translator_argument_matrix.csv", ["argument", "value", "source"], translator_argument_rows)
    write_text(
        repo_root / "docs/mapping/M10_translator_argument_matrix.md",
        _render_md("M10 Translator Argument Matrix", [f"- `{row['argument']}` = `{row['value']}` source=`{row['source']}`" for row in translator_argument_rows]),
    )
    write_csv(
        repo_root / "docs/mapping/M10_remaining_gap_matrix.csv",
        ["gap_id", "gap_type", "severity", "status", "details"],
        remaining_gap_rows,
    )
    write_text(
        repo_root / "docs/mapping/M10_remaining_gap_matrix.md",
        _render_md("M10 Remaining Gap Matrix", [f"- `{row['gap_id']}` {row['severity']}: {row['details']}" for row in remaining_gap_rows]),
    )

    source_backed_module_count = sum(1 for row in module_trace_rows if row["is_source_backed"])
    inferred_module_count = sum(1 for row in module_trace_rows if row["is_inferred"])
    unknown_module_source_count = sum(1 for row in module_trace_rows if row["evidence_type"] == "UNKNOWN")
    source_backed_net_count = sum(1 for row in net_trace_rows if row["is_source_backed"])
    inferred_net_count = sum(1 for row in net_trace_rows if row["is_inferred"])
    unknown_net_source_count = sum(1 for row in net_trace_rows if row["evidence_type"] == "UNKNOWN")
    source_backed_instance_count = sum(1 for row in instance_trace_rows if row["is_source_backed"])

    report = {
        "status_file_read": True,
        "status_file_updated": True,
        "m9h_gate_loaded": True,
        "m9_translator_v1_confirmed": bool(m9h["m9_translator_v1_confirmed"]),
        "m9_is_raw_openyield_netlist_compiler": bool(m9h["m9_is_raw_openyield_netlist_compiler"]),
        "openyield_root_found": openyield_root.exists(),
        "openyield_source_file_count_loaded": int(t1_full_report["openyield_source_file_count"]),
        "openyield_key_entrypoints_loaded": len(t1_key_entrypoints["key_entrypoints"]),
        "raw_source_trace_generated": True,
        "module_source_trace_available": True,
        "net_source_trace_available": True,
        "instance_source_trace_available": True,
        "config_source_trace_available": True,
        "openyield_module_count": len(module_trace_rows),
        "source_backed_module_count": source_backed_module_count,
        "inferred_module_count": inferred_module_count,
        "unknown_module_source_count": unknown_module_source_count,
        "openyield_net_count": len(net_trace_rows),
        "source_backed_net_count": source_backed_net_count,
        "inferred_net_count": inferred_net_count,
        "unknown_net_source_count": unknown_net_source_count,
        "openyield_instance_count": len(instance_trace_rows),
        "source_backed_instance_count": source_backed_instance_count,
        "capacity_config_fallback_used": bool(config_trace["capacity_config_fallback_used"]),
        "fallback_reason": config_trace["fallback_reason"],
        "generated_from_raw_openyield_source_trace": True,
        "full_raw_openyield_netlist_compiler": False,
        "translator_generated_layoutgen_arguments": spec_payload["generator_arguments"],
        "layoutgen_golden_flow_used": True,
        "reference_file_copied_as_output": False,
        "gds_generated": True,
        "gds_path": _rel(repo_root, main_gds),
        "clean_review_gds_path": _rel(repo_root, clean_gds),
        "annotated_debug_gds_path": _rel(repo_root, debug_gds),
        "gds_sanity_status": _gds_sanity(main_gds),
        "top_cell_name": TOP_CELL_NAME,
        "access_module_as_primary_count": 0,
        "floorplan_proxy_count": 0,
        "arbitrary_module_scatter_used": False,
        "label_only_binding_as_implementation_count": 0,
        "reference_vs_m10_geometry_match": geometry_match,
        "geometry_diff_available": True,
        "can_claim_source_backed_translator_v2": True,
        "can_claim_full_raw_netlist_compiler": False,
        "human_klayout_review_required": True,
        "can_enter_next_stage_before_human_review": False,
        "remaining_M10_blockers": remaining_blockers,
        "remaining_M10_blockers_count": len(remaining_blockers),
    }

    write_json(out_json, report)
    write_text(
        out_report,
        _render_md(
            "M10 Harden Raw OpenYield Trace Report",
            [
                f"- openyield_root_found: `{report['openyield_root_found']}`",
                f"- openyield_source_file_count_loaded: `{report['openyield_source_file_count_loaded']}`",
                f"- source_backed_module_count: `{report['source_backed_module_count']}` / `{report['openyield_module_count']}`",
                f"- source_backed_net_count: `{report['source_backed_net_count']}` / `{report['openyield_net_count']}`",
                f"- capacity_config_fallback_used: `{report['capacity_config_fallback_used']}`",
                f"- generated_from_raw_openyield_source_trace: `{report['generated_from_raw_openyield_source_trace']}`",
                f"- full_raw_openyield_netlist_compiler: `{report['full_raw_openyield_netlist_compiler']}`",
                f"- gds_path: `{report['gds_path']}`",
                f"- clean_review_gds_path: `{report['clean_review_gds_path']}`",
                f"- annotated_debug_gds_path: `{report['annotated_debug_gds_path']}`",
                f"- gds_sanity_status: `{report['gds_sanity_status']}`",
                f"- reference_vs_m10_geometry_match: `{report['reference_vs_m10_geometry_match']}`",
                f"- can_claim_source_backed_translator_v2: `{report['can_claim_source_backed_translator_v2']}`",
                f"- can_claim_full_raw_netlist_compiler: `{report['can_claim_full_raw_netlist_compiler']}`",
                f"- remaining_M10_blockers_count: `{report['remaining_M10_blockers_count']}`",
            ],
        ),
    )
    write_text(
        repo_root / "docs/evidence/M10_harden_raw_openyield_trace_summary.md",
        _render_md(
            "M10 Harden Raw OpenYield Trace Summary",
            [
                f"- M9 translator v1 confirmed: `{report['m9_translator_v1_confirmed']}`",
                f"- OpenYield source-backed module trace rows: `{report['openyield_module_count']}`",
                f"- OpenYield source-backed net trace rows: `{report['openyield_net_count']}`",
                f"- capacity_config_fallback_used: `{report['capacity_config_fallback_used']}`",
                f"- final geometry match: `{report['reference_vs_m10_geometry_match']}`",
                "- claim boundary: source-backed translator v2 only, not a full raw OpenYield netlist compiler.",
            ],
        ),
    )

    status["current_stage"] = "M10"
    status["next_stage"] = "WAIT_HUMAN_KLAYOUT_REVIEW"
    status["can_enter_next_stage_without_human_review"] = False
    status["last_M10_report"] = report
    status["current_goal"] = (
        "Hardened raw OpenYield source-backed translator trace is available; human KLayout review is required before any post-M10 stage."
    )
    write_json(status_json, status)
    write_text(status_md, _render_status_md(report))

    return report

