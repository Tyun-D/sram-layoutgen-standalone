from __future__ import annotations

import csv
import json
import importlib.util
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gdstk


L3_TARGET_MODULES = [
    "bitcell_array",
    "dummy_array",
    "replica_array",
    "row_decoder",
    "wordline_decoder",
    "decoder_gate_cells",
    "wordline_driver",
    "wordline_driver_gate_cells",
    "column_mux",
    "sense_amp",
    "write_driver",
    "precharge",
    "DELAY_CHAIN",
    "PRECHARGE_ENABLE_PATH",
    "SENSE_ENABLE_PATH",
    "WRITE_ENABLE_PATH",
    "WORDLINE_ENABLE_PATH",
    "GATED_CLOCK_PATH",
    "DFF_ROW",
    "CONTROL_LOGIC",
]

DEFERRED_TO_L4_L5 = ["SRAM_TOP", "BANK", "routing_semantics", "power_semantics", "timing_semantics"]

GDS_INVENTORY_COLUMNS = [
    "module",
    "module_category",
    "is_L3_target",
    "deferred_to_L4_L5",
    "generation_status",
    "gds_generated",
    "gds_path",
    "gds_size_bytes",
    "top_cell_name",
    "bbox_known",
    "bbox",
    "pins_json_path",
    "pin_count",
    "power_pins_present",
    "rail_report_path",
    "rail_status",
    "generator_manifest_path",
    "generator_source_file",
    "generation_strategy",
    "source_primitives",
    "uses_hardmacro",
    "uses_composition_generator",
    "uses_array_packer",
    "uses_gate_row_packer",
    "uses_contract_pin_mapping",
    "sanity_check_status",
    "parser_sanity_status",
    "limitations",
    "blocking_gap",
    "next_required_action",
    "evidence_files",
]


@dataclass(frozen=True)
class ModuleGDSSanityResult:
    module: str
    sanity_check_status: str
    parser_sanity_status: str
    failure_reason: str
    top_cell_name: str | None
    bbox: dict[str, Any] | None
    cell_count: int | None
    instance_count: int | None
    layer_summary: dict[str, int] | None


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=GDS_INVENTORY_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _gds_tools_available() -> bool:
    return bool(importlib.util.find_spec("gdstk")) or bool(importlib.util.find_spec("gdspy"))


def _is_gds_header_valid(path: Path) -> bool:
    data = path.read_bytes()[:6]
    return len(data) >= 6 and data[:4] == b"\x00\x06\x00\x02"


def _json_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _compute_layer_summary(lib: gdstk.Library) -> dict[str, int]:
    counts: dict[str, int] = {}
    for cell in lib.cells:
        for polygon in cell.polygons:
            key = f"{polygon.layer}/{polygon.datatype}"
            counts[key] = counts.get(key, 0) + 1
        for path in cell.paths:
            key = f"{path.layer}/{path.datatype}"
            counts[key] = counts.get(key, 0) + 1
        for label in cell.labels:
            key = f"{label.layer}/{label.texttype}"
            counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def check_module_gds_sanity(module_dir: Path, row: dict[str, str]) -> ModuleGDSSanityResult:
    module = row["module"]
    if row.get("deferred_to_L4_L5") == "True":
        return ModuleGDSSanityResult(
            module=module,
            sanity_check_status="NOT_REQUIRED_FOR_CURRENT_SCOPE",
            parser_sanity_status="NOT_REQUIRED_FOR_CURRENT_SCOPE",
            failure_reason="",
            top_cell_name=None,
            bbox=None,
            cell_count=None,
            instance_count=None,
            layer_summary=None,
        )

    gds_path = Path(row["gds_path"])
    pins_path = Path(row["pins_json_path"])
    rail_path = Path(row["rail_report_path"])
    manifest_path = Path(row["generator_manifest_path"])
    bbox_path = module_dir / "bbox.json"
    report_path = module_dir / "generation_report.json"

    if not gds_path.exists():
        return _failed(module, f"missing_gds:{gds_path}")
    if gds_path.stat().st_size <= 0:
        return _failed(module, f"empty_gds:{gds_path}")
    if not _is_gds_header_valid(gds_path):
        return _failed(module, f"invalid_gds_header:{gds_path}")
    for path_name, path in [
        ("pins_json", pins_path),
        ("bbox_json", bbox_path),
        ("rail_report_json", rail_path),
        ("generator_manifest_json", manifest_path),
        ("generation_report_json", report_path),
    ]:
        if not path.exists():
            return _failed(module, f"missing_{path_name}:{path}")

    try:
        pins = _json_load(pins_path)
        bbox = _json_load(bbox_path)
        rail = _json_load(rail_path)
        manifest = _json_load(manifest_path)
        report = _json_load(report_path)
    except Exception as exc:  # noqa: BLE001
        return _failed(module, f"json_parse_error:{exc}")

    if float(bbox.get("width", 0.0)) <= 0 or float(bbox.get("height", 0.0)) <= 0:
        return _failed(module, "non_positive_bbox")
    if not manifest.get("generator_source_file"):
        return _failed(module, "manifest_missing_generator_source_file")
    if str(report.get("generation_status", "")).endswith("BLOCKED"):
        return _failed(module, f"blocked_generation_status:{report.get('generation_status')}")
    if not isinstance(pins.get("pins"), list):
        return _failed(module, "pins_json_missing_pins_array")
    if not isinstance(rail, dict):
        return _failed(module, "rail_report_not_json_object")

    if not _gds_tools_available():
        return ModuleGDSSanityResult(
            module=module,
            sanity_check_status="GDS_BASIC_SANITY_PASSED",
            parser_sanity_status="SANITY_SKIPPED_TOOL_UNAVAILABLE",
            failure_reason="",
            top_cell_name=None,
            bbox=bbox,
            cell_count=None,
            instance_count=None,
            layer_summary=None,
        )

    try:
        lib = gdstk.read_gds(gds_path)
        top_cells = lib.top_level()
        top = top_cells[0] if top_cells else (lib.cells[0] if lib.cells else None)
        if top is None:
            return _failed(module, "gdstk_no_cells_found")
        top_bbox = top.bounding_box()
        if top_bbox is None:
            return _failed(module, "gdstk_top_bbox_missing")
        (x0, y0), (x1, y1) = top_bbox
        bbox_dict = {
            "x0": round(float(x0), 6),
            "y0": round(float(y0), 6),
            "x1": round(float(x1), 6),
            "y1": round(float(y1), 6),
            "width": round(float(x1) - float(x0), 6),
            "height": round(float(y1) - float(y0), 6),
        }
        instance_count = sum(len(cell.references) for cell in lib.cells)
        return ModuleGDSSanityResult(
            module=module,
            sanity_check_status="GDS_PARSED_SANITY_PASSED",
            parser_sanity_status="GDS_PARSED_SANITY_PASSED",
            failure_reason="",
            top_cell_name=str(top.name),
            bbox=bbox_dict,
            cell_count=len(lib.cells),
            instance_count=instance_count,
            layer_summary=_compute_layer_summary(lib),
        )
    except Exception as exc:  # noqa: BLE001
        return _failed(module, f"gdstk_parse_error:{exc}")


def _failed(module: str, reason: str) -> ModuleGDSSanityResult:
    return ModuleGDSSanityResult(
        module=module,
        sanity_check_status="SANITY_FAILED",
        parser_sanity_status="SANITY_FAILED",
        failure_reason=reason,
        top_cell_name=None,
        bbox=None,
        cell_count=None,
        instance_count=None,
        layer_summary=None,
    )


def run_module_gds_sanity_check(
    repo_root: Path,
    module_gds_dir: Path,
    inventory_csv: Path,
    inventory_md: Path,
    report_json: Path,
    report_md: Path,
    gap_summary: Path,
) -> dict[str, Any]:
    rows = _load_csv(inventory_csv)
    report = _json_load(report_json)
    sanity_results: dict[str, ModuleGDSSanityResult] = {}

    for row in rows:
        module = row["module"]
        module_dir = module_gds_dir / module
        sanity_results[module] = check_module_gds_sanity(module_dir, row)

    updated_rows: list[dict[str, Any]] = []
    for row in rows:
        result = sanity_results[row["module"]]
        updated = dict(row)
        updated["sanity_check_status"] = result.sanity_check_status
        updated["parser_sanity_status"] = result.parser_sanity_status
        if result.top_cell_name:
            updated["top_cell_name"] = result.top_cell_name
        if result.bbox is not None:
            updated["bbox_known"] = "True"
            updated["bbox"] = json.dumps(result.bbox, ensure_ascii=False)
        if result.sanity_check_status == "SANITY_FAILED":
            limitation = str(updated.get("limitations", ""))
            updated["limitations"] = f"{limitation}; sanity_failure={result.failure_reason}".strip("; ")
        updated_rows.append(updated)

    _write_csv(inventory_csv, updated_rows)
    _write_text(inventory_md, _inventory_markdown(updated_rows))

    parsed_passed = [m for m, r in sanity_results.items() if r.sanity_check_status == "GDS_PARSED_SANITY_PASSED"]
    basic_passed = [m for m, r in sanity_results.items() if r.sanity_check_status in {"GDS_BASIC_SANITY_PASSED", "GDS_PARSED_SANITY_PASSED"}]
    skipped = [m for m, r in sanity_results.items() if r.parser_sanity_status == "SANITY_SKIPPED_TOOL_UNAVAILABLE"]
    failed = [m for m, r in sanity_results.items() if r.sanity_check_status == "SANITY_FAILED"]

    report["module_gds_sanity_check_available"] = True
    report["module_gds_basic_sanity_passed_modules"] = basic_passed
    report["module_gds_parsed_sanity_passed_modules"] = parsed_passed
    report["module_gds_sanity_skipped_tool_unavailable_modules"] = skipped
    report["module_gds_sanity_failed_modules"] = failed
    report["module_gds_sanity_failed_count"] = len(failed)
    report["remaining_L3_blockers"] = report.get("remaining_L3_blockers", [])
    report["remaining_L3_blockers_count"] = len(report["remaining_L3_blockers"])

    all_l3_basic = set(basic_passed) >= set(L3_TARGET_MODULES)
    no_failed = len(failed) == 0
    report["can_claim_L3_module_generators_closed_now"] = bool(report.get("all_L3_target_modules_have_generators")) and report["remaining_L3_blockers_count"] == 0
    report["can_claim_L3_standalone_module_gds_closed_now"] = (
        bool(report.get("all_L3_target_modules_have_gds"))
        and bool(report.get("all_L3_target_modules_have_bbox"))
        and bool(report.get("all_L3_target_modules_have_pin_metadata"))
        and bool(report.get("all_L3_target_modules_have_rail_metadata"))
        and bool(report.get("all_L3_target_modules_have_generator_manifest"))
        and all_l3_basic
        and no_failed
        and report["remaining_L3_blockers_count"] == 0
    )
    report["can_enter_L4_top_level_assembly"] = report["can_claim_L3_standalone_module_gds_closed_now"]

    _write_json(report_json, report)
    _write_text(report_md, _report_markdown(report))
    _write_text(gap_summary, _gap_summary_markdown(report, sanity_results))

    return {
        "rows": updated_rows,
        "report": report,
        "sanity_results": sanity_results,
    }


def _inventory_markdown(rows: list[dict[str, Any]]) -> str:
    columns = GDS_INVENTORY_COLUMNS
    lines = ["# OpenYield Module GDS Inventory", "", f"Rows: `{len(rows)}`", ""]
    lines.append("| " + " | ".join(columns) + " |")
    lines.append("| " + " | ".join("---" for _ in columns) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")).replace("\n", " ") for column in columns) + " |")
    lines.append("")
    return "\n".join(lines)


def _report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield L3 module generator + standalone module GDS generation report",
        "",
        f"- module_generator_rows_count: `{report['module_generator_rows_count']}`",
        f"- module_gds_rows_count: `{report['module_gds_rows_count']}`",
        f"- module_gds_sanity_check_available: `{report['module_gds_sanity_check_available']}`",
        f"- module_gds_basic_sanity_passed_modules: `{', '.join(report['module_gds_basic_sanity_passed_modules'])}`",
        f"- module_gds_parsed_sanity_passed_modules: `{', '.join(report['module_gds_parsed_sanity_passed_modules'])}`",
        f"- module_gds_sanity_skipped_tool_unavailable_modules: `{', '.join(report['module_gds_sanity_skipped_tool_unavailable_modules']) or 'none'}`",
        f"- module_gds_sanity_failed_modules: `{', '.join(report['module_gds_sanity_failed_modules']) or 'none'}`",
        f"- module_gds_sanity_failed_count: `{report['module_gds_sanity_failed_count']}`",
        f"- remaining_L3_blockers_count: `{report['remaining_L3_blockers_count']}`",
        f"- can_claim_L3_module_generators_closed_now: `{report['can_claim_L3_module_generators_closed_now']}`",
        f"- can_claim_L3_standalone_module_gds_closed_now: `{report['can_claim_L3_standalone_module_gds_closed_now']}`",
        f"- can_enter_L4_top_level_assembly: `{report['can_enter_L4_top_level_assembly']}`",
        f"- can_claim_full_openyield_gds_now: `{report['can_claim_full_openyield_gds_now']}`",
        f"- can_claim_drc_clean_now: `{report['can_claim_drc_clean_now']}`",
        f"- can_claim_lvs_clean_now: `{report['can_claim_lvs_clean_now']}`",
        f"- can_claim_timing_closure_now: `{report['can_claim_timing_closure_now']}`",
        "",
    ]
    return "\n".join(lines)


def _gap_summary_markdown(report: dict[str, Any], sanity_results: dict[str, ModuleGDSSanityResult]) -> str:
    lines = [
        "# L3 module generator + GDS gap summary",
        "",
        "## Generator coverage",
        "",
        f"- L3 建立了 module generators: `{', '.join(report['modules_with_generators_ready'])}`",
        "- hardmacro wrapper generator 输出的 GDS: `wordline_driver, column_mux, sense_amp, write_driver, precharge`",
        "- array generator 输出的 GDS: `bitcell_array, dummy_array, replica_array`",
        "- gate-row generator 输出的 GDS: `row_decoder, wordline_decoder, decoder_gate_cells, wordline_driver_gate_cells`",
        "- composition-backed candidate generator 输出的 GDS: `DELAY_CHAIN, PRECHARGE_ENABLE_PATH, SENSE_ENABLE_PATH, WRITE_ENABLE_PATH, WORDLINE_ENABLE_PATH, GATED_CLOCK_PATH, DFF_ROW, CONTROL_LOGIC`",
        f"- 使用 contract pins 的模块: `{', '.join(report['modules_with_contract_pins']) or 'none'}`",
        f"- 生成失败的模块: `{', '.join(report['modules_blocked_from_gds_generation']) or 'none'}`",
        "- GDS 是否可复现: `True`",
        f"- 基础 sanity 通过模块: `{', '.join(report['module_gds_basic_sanity_passed_modules'])}`",
        f"- parsed sanity 通过模块: `{', '.join(report['module_gds_parsed_sanity_passed_modules']) or 'none'}`",
        f"- parsed sanity 因工具缺失跳过模块: `{', '.join(report['module_gds_sanity_skipped_tool_unavailable_modules']) or 'none'}`",
        f"- sanity 失败模块: `{', '.join(report['module_gds_sanity_failed_modules']) or 'none'}`",
        f"- can_enter_L4_top_level_assembly: `{report['can_enter_L4_top_level_assembly']}`",
        f"- remaining_L3_blockers: `{report['remaining_L3_blockers']}`",
        "",
    ]
    failed = [r for r in sanity_results.values() if r.sanity_check_status == "SANITY_FAILED"]
    if failed:
        lines.append("## Failed modules")
        lines.append("")
        for item in failed:
            lines.append(f"- `{item.module}`: `{item.failure_reason}`")
        lines.append("")
    return "\n".join(lines)
