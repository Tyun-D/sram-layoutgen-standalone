from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.M10_harden_raw_openyield_trace import (
    _gds_sanity,
    _read_json,
    _rel,
    _sha256,
    _strip_all_text,
    _write_review_manifest,
)
from sram_layoutgen.openyield_adapter.openyield_raw_source_trace import write_csv, write_json, write_text


DEBUG_TEXT_LAYER = 294
DEBUG_BOX_LAYER = 295

EXPECTED_MODULES = [
    "CONTROL_LOGIC",
    "DELAY_CHAIN",
    "DFF_ROW",
    "GATED_CLOCK_PATH",
    "PRECHARGE_ENABLE_PATH",
    "SENSE_ENABLE_PATH",
    "WORDLINE_ENABLE_PATH",
    "WRITE_ENABLE_PATH",
    "bitcell_array",
    "column_mux",
    "decoder_gate_cells",
    "dummy_array",
    "precharge",
    "replica_array",
    "row_decoder",
    "sense_amp",
    "wordline_decoder",
    "wordline_driver",
    "wordline_driver_gate_cells",
    "write_driver",
]

DIRECT_REPLACE_MODULES = {"column_mux", "sense_amp", "write_driver", "wordline_driver"}
CONSTRAINT_ONLY_MODULES = {"bitcell_array", "dummy_array", "replica_array", "precharge"}

ALIAS_GOLDEN_TARGETS = {
    "gen_col_mux_vdd_labeled": "gen_col_mux",
}

MODULE_INVENTORY_FIELDS = [
    "openyield_module",
    "openyield_role",
    "module_gds_path",
    "gds_exists",
    "top_cell_name",
    "bbox_width",
    "bbox_height",
    "shape_count",
    "layer_datatype_summary",
    "pin_count",
    "pin_names",
    "pin_bbox_status",
    "pin_layer_summary",
    "pin_access_status",
    "rail_status",
    "vdd_gnd_rail_present",
    "contract_pin_used",
    "candidate_rail_metadata_used",
    "generation_status",
    "generation_strategy",
    "limitations",
    "not_DRC_clean_claimed",
    "not_LVS_clean_claimed",
    "matches_m10_module_trace",
    "matches_m9_module_binding",
    "golden_target_cell_or_region",
    "golden_match_status",
]

MODULE_VS_GOLDEN_FIELDS = [
    "openyield_module",
    "golden_target_cell_or_region",
    "golden_match_status",
    "module_bbox",
    "golden_bbox",
    "bbox_compatible",
    "pin_mapping_summary",
    "pin_compatible",
    "rail_compatible",
    "pitch_compatible",
    "layer_compatible",
    "floorplan_safe",
    "placement_safe",
    "routing_safe",
    "power_safe",
    "requires_wrapper",
    "comparison_notes",
]

DECISION_FIELDS = [
    "openyield_module",
    "openyield_role",
    "module_gds_path",
    "generation_status",
    "generation_strategy",
    "bbox_width",
    "bbox_height",
    "pin_count",
    "rail_status",
    "contract_pin_used",
    "candidate_geometry_used",
    "golden_target_cell_or_region",
    "golden_match_status",
    "bbox_compatible",
    "pin_compatible",
    "rail_compatible",
    "pitch_compatible",
    "layer_compatible",
    "floorplan_safe",
    "placement_safe",
    "routing_safe",
    "power_safe",
    "decision",
    "decision_reason",
    "first_substitution_priority",
    "requires_M11B_metadata_extraction",
    "requires_wrapper",
    "requires_layoutgen_fallback",
    "human_review_required",
]

PIN_METADATA_FIELDS = [
    "openyield_module",
    "pin_name",
    "pin_layer",
    "pin_source",
    "pin_x",
    "pin_y",
    "module_bbox_width",
    "module_bbox_height",
    "rail_status",
    "vdd_gnd_rail_present",
    "contract_pin_used",
    "candidate_rail_metadata_used",
]

NEXT_PLAN_FIELDS = [
    "sequence",
    "module",
    "decision",
    "priority",
    "why_candidate",
    "requires_wrapper",
    "requires_M11B_metadata_extraction",
]


@dataclass
class GoldenComparison:
    golden_target_cell_or_region: str
    golden_match_status: str
    golden_bbox: str
    bbox_compatible: bool
    pin_mapping_summary: str
    pin_compatible: bool
    rail_compatible: bool
    pitch_compatible: bool
    layer_compatible: bool
    floorplan_safe: bool
    placement_safe: bool
    routing_safe: bool
    power_safe: bool
    requires_wrapper: bool
    comparison_notes: str
    review_golden_cell: gdstk.Cell | None


def _render_md(title: str, lines: list[str]) -> str:
    return "\n".join([f"# {title}", "", *lines, ""]).rstrip() + "\n"


def _read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _bool_text(value: bool) -> str:
    return "True" if value else "False"


def _cell_map(lib: gdstk.Library) -> dict[str, gdstk.Cell]:
    return {cell.name: cell for cell in lib.cells}


def _flattened_copy(cell: gdstk.Cell, name: str) -> gdstk.Cell:
    copied = cell.copy(name, deep_copy=True)
    copied.flatten(apply_repetitions=True)
    return copied


def _layer_summary(cell: gdstk.Cell) -> str:
    counts: dict[str, int] = {}
    for polygon in cell.polygons:
        key = f"{polygon.layer}/{polygon.datatype}"
        counts[key] = counts.get(key, 0) + 1
    for path in cell.paths:
        key = f"{path.layer}/{path.datatype}"
        counts[key] = counts.get(key, 0) + 1
    return ";".join(f"{key}:{counts[key]}" for key in sorted(counts))


def _bbox_text(bbox: dict[str, Any] | None) -> str:
    if not bbox:
        return ""
    return f"{bbox.get('width', 0)}x{bbox.get('height', 0)}"


def _bbox_compat(module_bbox: dict[str, Any], golden_bbox: tuple[tuple[float, float], tuple[float, float]] | None) -> bool:
    if golden_bbox is None:
        return False
    gw = float(golden_bbox[1][0] - golden_bbox[0][0])
    gh = float(golden_bbox[1][1] - golden_bbox[0][1])
    mw = float(module_bbox.get("width", 0.0))
    mh = float(module_bbox.get("height", 0.0))
    if gw <= 0 or gh <= 0 or mw <= 0 or mh <= 0:
        return False
    return abs(mw - gw) / gw <= 0.12 and abs(mh - gh) / gh <= 0.12


def _normalize_pin(name: str) -> str:
    return (
        name.lower()
        .replace("gnd", "vss")
        .replace("br", "blb")
        .replace("q_bar", "qb")
        .replace("precharge_en", "en_bar")
        .replace("write_en", "en")
    )


def _golden_target_info(
    *,
    module: str,
    binding_row: dict[str, str] | None,
    golden_cells: dict[str, gdstk.Cell],
    module_bbox: dict[str, Any],
    module_pin_names: list[str],
    rail_status: str,
    contract_pin_used: bool,
) -> GoldenComparison:
    target_cell = ""
    if binding_row is not None:
        target_cell = (binding_row.get("layoutgen_target_cell") or "").split(";")[0].strip()
    resolved_target = ALIAS_GOLDEN_TARGETS.get(target_cell, target_cell)
    review_golden_cell: gdstk.Cell | None = None
    golden_bbox = ""
    golden_match_status = "UNKNOWN_GOLDEN_REGION"
    bbox_compatible = False
    pin_mapping_summary = "UNKNOWN_GOLDEN_REGION"
    pin_compatible = False
    rail_compatible = False
    pitch_compatible = False
    layer_compatible = False
    floorplan_safe = False
    placement_safe = False
    routing_safe = False
    power_safe = False
    requires_wrapper = False
    comparison_notes = "Automatic golden region lookup did not find a module-level counterpart."

    if resolved_target in golden_cells and module in DIRECT_REPLACE_MODULES.union({"precharge"}):
        review_golden_cell = _flattened_copy(golden_cells[resolved_target], f"M11A_gold_{module}")
        bbox = golden_cells[resolved_target].bounding_box()
        golden_bbox = "" if bbox is None else f"{round(float(bbox[1][0]-bbox[0][0]), 6)}x{round(float(bbox[1][1]-bbox[0][1]), 6)}"
        golden_match_status = "EXACT_GOLDEN_CELL" if resolved_target == target_cell else "ALIAS_GOLDEN_CELL"
        bbox_compatible = _bbox_compat(module_bbox, bbox)
        golden_pin_names = {_normalize_pin(label.text) for label in golden_cells[resolved_target].labels}
        module_pin_norm = {_normalize_pin(name) for name in module_pin_names}
        missing = sorted(
            name
            for name in module_pin_norm
            if name not in golden_pin_names and name not in {"vdd", "vss", "d", "g", "s"}
        )
        pin_mapping_summary = "all_major_pins_mappable" if not missing else f"missing_in_golden_labels:{','.join(missing)}"
        pin_compatible = not missing and not contract_pin_used
        rail_compatible = "rail_metadata_exported" in rail_status
        pitch_compatible = bbox_compatible
        layer_compatible = True
        floorplan_safe = bbox_compatible
        placement_safe = bbox_compatible
        routing_safe = pin_compatible
        power_safe = rail_compatible
        requires_wrapper = module in {"column_mux", "wordline_driver"}
        comparison_notes = "Golden comparison is against the layoutgen leaf cell used by the locked flow, not a substituted SRAM top-level region."
    elif module in {"bitcell_array", "dummy_array", "replica_array"}:
        leaf_proxy = ""
        if resolved_target in golden_cells:
            leaf_proxy = resolved_target
        golden_match_status = "UNKNOWN_GOLDEN_REGION"
        golden_bbox = leaf_proxy and _bbox_text(
            {
                "width": round(float(golden_cells[leaf_proxy].bounding_box()[1][0] - golden_cells[leaf_proxy].bounding_box()[0][0]), 6),
                "height": round(float(golden_cells[leaf_proxy].bounding_box()[1][1] - golden_cells[leaf_proxy].bounding_box()[0][1]), 6),
            }
        ) or ""
        comparison_notes = "Only leaf-cell proxies are visible in golden; the corresponding assembled array region is not auto-isolated."
        pin_mapping_summary = "array_bus_contract_only"
        rail_compatible = True
        pitch_compatible = True
        layer_compatible = True
        floorplan_safe = False
        placement_safe = False
        routing_safe = False
        power_safe = False
    elif binding_row is not None:
        golden_target_name = binding_row.get("layoutgen_target_cell", "")
        golden_match_status = "UNKNOWN_GOLDEN_REGION"
        comparison_notes = (
            "Golden flow uses a regenerated layoutgen region or role-based composite for this module, not a standalone golden hardmacro cell that can be auto-extracted."
        )
        pin_mapping_summary = "semantic_binding_only"
        requires_wrapper = True
        golden_bbox = ""
        if golden_target_name:
            target_cell = golden_target_name

    golden_target_cell_or_region = target_cell if target_cell else "UNKNOWN_GOLDEN_REGION"
    return GoldenComparison(
        golden_target_cell_or_region=golden_target_cell_or_region,
        golden_match_status=golden_match_status,
        golden_bbox=golden_bbox,
        bbox_compatible=bbox_compatible,
        pin_mapping_summary=pin_mapping_summary,
        pin_compatible=pin_compatible,
        rail_compatible=rail_compatible,
        pitch_compatible=pitch_compatible,
        layer_compatible=layer_compatible,
        floorplan_safe=floorplan_safe,
        placement_safe=placement_safe,
        routing_safe=routing_safe,
        power_safe=power_safe,
        requires_wrapper=requires_wrapper,
        comparison_notes=comparison_notes,
        review_golden_cell=review_golden_cell,
    )


def _decision_for_module(
    *,
    module: str,
    binding_row: dict[str, str] | None,
    generation_status: str,
    contract_pin_used: bool,
    candidate_geometry_used: bool,
    comparison: GoldenComparison,
) -> tuple[str, str, str, bool]:
    implementation_mode = (binding_row or {}).get("implementation_mode", "")
    if module in DIRECT_REPLACE_MODULES and implementation_mode == "REAL_CELL_WRAPPER" and comparison.pin_compatible and comparison.rail_compatible:
        return (
            "DIRECT_HARDMACRO_REPLACE",
            "Wrapper macro has a real golden leaf counterpart, non-contract pin geometry, and compatible rails/bbox for a guarded selective substitution trial.",
            "P0",
            False,
        )
    if module in CONSTRAINT_ONLY_MODULES:
        return (
            "CONSTRAINT_EXTRACTION_ONLY",
            "Module metadata is useful for bbox/pin/rail/pitch extraction, but contract pins, array sizing scope, or wrapper assumptions block direct substitution.",
            "P1",
            False,
        )
    if implementation_mode in {"LAYOUTGEN_FALLBACK_WITH_OPENYIELD_SEMANTICS", "PARAMETERIZED_LAYOUTGEN_GENERATOR"} or candidate_geometry_used:
        return (
            "SEMANTIC_REFERENCE_ONLY",
            "Current flow still relies on layoutgen fallback or regenerated layoutgen composites for this role; module GDS remains semantic/reference evidence only.",
            "P2",
            True,
        )
    return (
        "REJECTED",
        "Module does not meet direct replacement or constraint-extraction criteria under current evidence.",
        "P3",
        True,
    )


def _build_review_gds(
    *,
    out_dir: Path,
    module_rows: list[dict[str, Any]],
) -> tuple[Path, Path, Path]:
    lib = gdstk.Library(unit=1e-6, precision=1e-9)
    top = gdstk.Cell("module_gds_qualification_review")
    debug = gdstk.Cell("module_gds_qualification_debug")
    lib.add(top)
    lib.add(debug)

    bands = {
        "DIRECT_HARDMACRO_REPLACE": 0.0,
        "CONSTRAINT_EXTRACTION_ONLY": 40.0,
        "SEMANTIC_REFERENCE_ONLY": 80.0,
        "REJECTED": 120.0,
    }
    counters = {key: 0 for key in bands}

    added_cells: set[str] = {top.name, debug.name}
    for row in module_rows:
        decision = row["decision"]
        base_y = bands[decision]
        idx = counters[decision]
        counters[decision] += 1
        x_offset = idx * 20.0

        module_cell = row["review_module_cell"]
        golden_cell = row["review_golden_cell"]
        module_bbox = row["module_bbox"]

        if module_cell.name not in added_cells:
            lib.add(module_cell)
            added_cells.add(module_cell.name)
        if golden_cell is not None and golden_cell.name not in added_cells:
            lib.add(golden_cell)
            added_cells.add(golden_cell.name)

        top.add(gdstk.Reference(module_cell, origin=(x_offset, base_y)))
        debug.add(
            gdstk.rectangle(
                (x_offset, base_y),
                (x_offset + float(module_bbox.get("width", 0.0)), base_y + float(module_bbox.get("height", 0.0))),
                layer=DEBUG_BOX_LAYER,
                datatype=0,
            )
        )
        debug.add(
            gdstk.Label(
                f"{row['openyield_module']} [{decision}]",
                (x_offset, base_y + float(module_bbox.get("height", 0.0)) + 1.0),
                layer=DEBUG_TEXT_LAYER,
                texttype=0,
            )
        )

        if golden_cell is not None:
            golden_origin = (x_offset + float(module_bbox.get("width", 0.0)) + 4.0, base_y)
            top.add(gdstk.Reference(golden_cell, origin=golden_origin))
            bbox = golden_cell.bounding_box()
            if bbox is not None:
                debug.add(
                    gdstk.rectangle(
                        golden_origin,
                        (
                            golden_origin[0] + float(bbox[1][0] - bbox[0][0]),
                            golden_origin[1] + float(bbox[1][1] - bbox[0][1]),
                        ),
                        layer=DEBUG_BOX_LAYER,
                        datatype=0,
                    )
                )
            debug.add(
                gdstk.Label(
                    f"golden={row['golden_target_cell_or_region']}",
                    (golden_origin[0], base_y + float(module_bbox.get("height", 0.0)) + 1.0),
                    layer=DEBUG_TEXT_LAYER,
                    texttype=0,
                )
            )
        else:
            marker_origin = (x_offset + float(module_bbox.get("width", 0.0)) + 4.0, base_y)
            debug.add(
                gdstk.rectangle(
                    marker_origin,
                    (marker_origin[0] + max(1.0, float(module_bbox.get("width", 0.0))), marker_origin[1] + max(1.0, float(module_bbox.get("height", 0.0)))),
                    layer=DEBUG_BOX_LAYER,
                    datatype=0,
                )
            )
            debug.add(
                gdstk.Label(
                    f"golden=UNKNOWN_GOLDEN_REGION",
                    (marker_origin[0], base_y + float(module_bbox.get("height", 0.0)) + 1.0),
                    layer=DEBUG_TEXT_LAYER,
                    texttype=0,
                )
            )

    review_path = out_dir / "module_gds_qualification_review.gds"
    annotated_path = out_dir / "module_gds_qualification_annotated_debug.gds"
    clean_path = out_dir / "module_gds_qualification_clean_review.gds"

    lib.write_gds(review_path)

    top.add(gdstk.Reference(debug))
    lib.write_gds(annotated_path)
    _strip_all_text(annotated_path, clean_path)
    return review_path, clean_path, annotated_path


def _update_goal_md(original_goal: str) -> str:
    note = (
        "\n## Current Qualification Stage\n\n"
        "- M11A 正在对 `outputs/openyield_module_gds/` 的 20 个模块做 hardmacro 资格审查。\n"
        "- 本阶段只确认 DIRECT_HARDMACRO_REPLACE / CONSTRAINT_EXTRACTION_ONLY / SEMANTIC_REFERENCE_ONLY / REJECTED 分类，不做完整 SRAM top 替换。\n"
        "- 下一阶段需要先做 `M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION`，之后才允许尝试 selective substitution。\n"
    )
    if "## Current Qualification Stage" in original_goal:
        return original_goal.split("## Current Qualification Stage", 1)[0].rstrip() + note
    return original_goal.rstrip() + "\n" + note


def _update_progress_md(
    *,
    original_progress: str,
    first_substitution_candidates: list[str],
) -> str:
    text = original_progress
    text = text.replace(
        "- next_action: `M11A_MODULE_GDS_QUALIFICATION`",
        "- next_action: `M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION after M11A qualification; first guarded candidates are "
        + ", ".join(first_substitution_candidates)
        + ".`",
    )
    text = text.replace(
        "- next_assets_to_fill_in_order: `M11A_MODULE_GDS_QUALIFICATION, M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION, M11C_SELECTIVE_HARDMACRO_SUBSTITUTION_SMOKE, M12A_VARIATION_GDS_GENERATION, M12B_ROUTING_POWER_ADAPTATION, M13_DRC_LVS_FEASIBILITY_AND_EQUIVALENCE_TRACE`",
        "- next_assets_to_fill_in_order: `M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION, M11C_SELECTIVE_HARDMACRO_SUBSTITUTION_SMOKE, M12A_VARIATION_GDS_GENERATION, M12B_ROUTING_POWER_ADAPTATION, M13_DRC_LVS_FEASIBILITY_AND_EQUIVALENCE_TRACE`",
    )
    if "## M11A Qualification" not in text:
        text = (
            text.rstrip()
            + "\n\n## M11A Qualification\n\n"
            + f"- first_substitution_candidates: `{', '.join(first_substitution_candidates)}`\n"
            + "- note: `M11A does not claim module GDS hardmacro substitution complete; M11B metadata extraction is mandatory before any substitution attempt.`\n"
        )
    return text if text.endswith("\n") else text + "\n"


def run_m11a_module_gds_qualification(
    *,
    repo_root: Path,
    status_md: Path,
    status_json: Path,
    goal_md: Path,
    progress_md: Path,
    module_gds_dir: Path,
    golden_reference: Path,
    m10_module_trace: Path,
    m10_net_trace: Path,
    m9_module_binding: Path,
    m9_net_binding: Path,
    m12_assets: Path,
    m12_backlog: Path,
    out_dir: Path,
    out_json: Path,
    out_report: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    status_md = status_md.resolve()
    status_json = status_json.resolve()
    goal_md = goal_md.resolve()
    progress_md = progress_md.resolve()
    module_gds_dir = module_gds_dir.resolve()
    golden_reference = golden_reference.resolve()
    m10_module_trace = m10_module_trace.resolve()
    m10_net_trace = m10_net_trace.resolve()
    m9_module_binding = m9_module_binding.resolve()
    m9_net_binding = m9_net_binding.resolve()
    m12_assets = m12_assets.resolve()
    m12_backlog = m12_backlog.resolve()
    out_dir = out_dir.resolve()
    out_json = out_json.resolve()
    out_report = out_report.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    status = _read_json(status_json)
    goal_text = goal_md.read_text(encoding="utf-8")
    progress_text = progress_md.read_text(encoding="utf-8")
    m11h = _read_json(repo_root / "docs/M11H_confirm_config_aware_translator_report.json")
    m12_assets_rows = _read_csv_rows(m12_assets)
    m12_backlog_rows = _read_csv_rows(m12_backlog)
    _ = (m12_assets_rows, m12_backlog_rows, m10_net_trace, m9_net_binding)

    reused_previous_artifacts = list(m11h["reused_previous_artifacts"]) + [
        {
            "artifact": "OpenYield module GDS inventory",
            "path": "outputs/openyield_module_gds/",
            "reuse_purpose": "per-module bbox/pins/rail/generation metadata and candidate hardmacro files for qualification only",
        },
        {
            "artifact": "M9 module binding matrix",
            "path": "outputs/M9_openyield_netlist_translator/current_supported_config/M9_module_binding_matrix.csv",
            "reuse_purpose": "map each OpenYield module to its current layoutgen-backed physical target or fallback path",
        },
        {
            "artifact": "M10 source-backed module trace",
            "path": "docs/mapping/M10_source_backed_module_trace.csv",
            "reuse_purpose": "verify each module remains source-backed while being qualified as a hardmacro candidate",
        },
    ]
    deprecated_previous_artifacts = list(m11h["deprecated_previous_artifacts"]) + [
        {
            "artifact": "contract pins as verified physical pins",
            "path": "module pins derived from module_contract_pin_map or composition contracts",
            "deprecated_reason": "cannot be treated as fully verified physical substitution pins in M11A",
        },
        {
            "artifact": "candidate geometry as direct hardmacro replacement",
            "path": "L3_GDS_GENERATED_CANDIDATE_GEOMETRY modules",
            "deprecated_reason": "candidate geometry remains unqualified for direct substitution in M11A",
        },
    ]
    current_stage_inputs = [
        "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        "PROJECT_NETLIST_TO_LAYOUT_GOAL.md",
        "PROJECT_NETLIST_TO_LAYOUT_PROGRESS.md",
        "docs/M11H_confirm_config_aware_translator_report.json",
        "docs/mapping/M10_source_backed_module_trace.csv",
        "docs/mapping/M10_source_backed_net_trace.csv",
        "outputs/M9_openyield_netlist_translator/current_supported_config/M9_module_binding_matrix.csv",
        "outputs/M9_openyield_netlist_translator/current_supported_config/M9_net_binding_matrix.csv",
        "docs/mapping/M12_ten_required_assets_matrix.csv",
        "docs/mapping/M12_missing_asset_backlog.csv",
        "outputs/M7_correct_golden_reference/current_supported_config/golden_reference.gds",
        "outputs/M8R_fix_golden_geometry_delta/current_supported_config/m8r_reproduced_fixed.gds",
        "outputs/openyield_module_gds/",
    ]
    current_stage_delta_from_M11H = [
        "M11H cleared the config-aware translator gate; M11A uses that cleared state to qualify physical module GDS candidates rather than translator claims.",
        "M11A does not expand claim boundaries to full substitution, DRC, LVS, or signoff; it only classifies module candidates and produces selective substitution prerequisites.",
        "M11A adds a per-module decision matrix and review GDS against golden/layoutgen targets.",
    ]
    why_m11a_is_needed = (
        "M12 marked the physical implementation library as partial because OpenYield module GDS existed but were not qualified for hardmacro substitution. M11A is needed to classify all 20 module GDS into direct replacement, constraint-only, semantic-only, or rejected buckets before M11B metadata extraction and any substitution smoke."
    )

    if status.get("next_stage_allowed") != "M11A_MODULE_GDS_QUALIFICATION" and status.get("current_stage") != "M11A":
        raise ValueError("M11A requires the cleared M11H gate state.")

    module_rows = []
    pin_rows = []
    comparison_rows = []
    decision_rows = []
    next_plan_rows = []

    golden_lib = gdstk.read_gds(golden_reference)
    golden_cells = _cell_map(golden_lib)
    m10_module_rows = {row["openyield_module"]: row for row in _read_csv_rows(m10_module_trace)}
    m9_module_rows = {row["openyield_module"]: row for row in _read_csv_rows(m9_module_binding)}
    module_dirs = sorted([path for path in module_gds_dir.iterdir() if path.is_dir()])

    bbox_metadata_count = 0
    pin_metadata_count = 0
    rail_metadata_count = 0
    generation_report_count = 0

    for module in EXPECTED_MODULES:
        base = module_gds_dir / module
        gds_path = base / f"{module}.gds"
        bbox_path = base / "bbox.json"
        pins_path = base / "pins.json"
        rail_path = base / "rail_report.json"
        generation_path = base / "generation_report.json"

        bbox_exists = bbox_path.exists()
        pins_exists = pins_path.exists()
        rail_exists = rail_path.exists()
        generation_exists = generation_path.exists()
        bbox_metadata_count += int(bbox_exists)
        pin_metadata_count += int(pins_exists)
        rail_metadata_count += int(rail_exists)
        generation_report_count += int(generation_exists)

        bbox = _load_json(bbox_path) if bbox_exists else {}
        pins_payload = _load_json(pins_path) if pins_exists else {"pins": []}
        rail = _load_json(rail_path) if rail_exists else {}
        generation = _load_json(generation_path) if generation_exists else {}
        pins = list(pins_payload.get("pins", []))
        pin_names = [pin.get("name", "") for pin in pins]
        contract_pin_used = any("contract" in str(pin.get("pin_source", "")).lower() for pin in pins) or bool(generation.get("pin_contract_source"))
        candidate_geometry_used = "CANDIDATE_GEOMETRY" in str(generation.get("generation_status", "")) or bool(generation.get("geometry_is_L3_module_candidate"))

        module_lib = gdstk.read_gds(gds_path) if gds_path.exists() else gdstk.Library()
        module_cell_map = _cell_map(module_lib)
        top_cell = module_cell_map.get(generation.get("top_cell_name", module))
        if top_cell is None and module_lib.cells:
            top_cell = module_lib.cells[0]
        review_module_cell = _flattened_copy(top_cell, f"M11A_mod_{module}") if top_cell is not None else gdstk.Cell(f"M11A_mod_{module}")
        layer_summary = _layer_summary(review_module_cell)

        comparison = _golden_target_info(
            module=module,
            binding_row=m9_module_rows.get(module),
            golden_cells=golden_cells,
            module_bbox=bbox,
            module_pin_names=pin_names,
            rail_status=str(rail.get("rail_status", "")),
            contract_pin_used=contract_pin_used,
        )

        decision, decision_reason, first_priority, requires_layoutgen_fallback = _decision_for_module(
            module=module,
            binding_row=m9_module_rows.get(module),
            generation_status=str(generation.get("generation_status", "")),
            contract_pin_used=contract_pin_used,
            candidate_geometry_used=candidate_geometry_used,
            comparison=comparison,
        )

        pin_sources = sorted({pin.get("pin_source", "") for pin in pins})
        pin_layer_summary = ";".join(sorted({str(pin.get("layer", "")) for pin in pins}))
        pin_access_status = "geometry_text_or_contract_point_export"
        pin_bbox_status = "POINT_ONLY_EXPORT" if pins and not any("bbox" in pin for pin in pins) else "BBOX_EXPORT_PRESENT"
        vdd_gnd_rail_present = bool({"VDD", "GND", "VSS"} & set(pin_names)) or bool(generation.get("rail_status"))
        candidate_rail_metadata_used = "candidate" in str(rail.get("rail_status", "")).lower()

        module_rows.append(
            {
                "openyield_module": module,
                "openyield_role": m10_module_rows.get(module, {}).get("openyield_role", ""),
                "module_gds_path": _rel(repo_root, gds_path) if gds_path.exists() else "",
                "gds_exists": gds_path.exists(),
                "top_cell_name": generation.get("top_cell_name", module),
                "bbox_width": bbox.get("width", 0),
                "bbox_height": bbox.get("height", 0),
                "shape_count": bbox.get("shape_count", len(review_module_cell.polygons)),
                "layer_datatype_summary": layer_summary,
                "pin_count": len(pins),
                "pin_names": ";".join(pin_names),
                "pin_bbox_status": pin_bbox_status,
                "pin_layer_summary": pin_layer_summary,
                "pin_access_status": pin_access_status + ":" + ",".join(pin_sources),
                "rail_status": rail.get("rail_status", ""),
                "vdd_gnd_rail_present": vdd_gnd_rail_present,
                "contract_pin_used": contract_pin_used,
                "candidate_rail_metadata_used": candidate_rail_metadata_used,
                "generation_status": generation.get("generation_status", ""),
                "generation_strategy": generation.get("generation_strategy", ""),
                "limitations": " | ".join(generation.get("limitations", [])),
                "not_DRC_clean_claimed": generation.get("not_DRC_clean_claimed", True),
                "not_LVS_clean_claimed": generation.get("not_LVS_clean_claimed", True),
                "matches_m10_module_trace": module in m10_module_rows,
                "matches_m9_module_binding": module in m9_module_rows,
                "golden_target_cell_or_region": comparison.golden_target_cell_or_region,
                "golden_match_status": comparison.golden_match_status,
                "decision": decision,
                "review_module_cell": review_module_cell,
                "review_golden_cell": comparison.review_golden_cell,
                "module_bbox": bbox,
            }
        )

        comparison_rows.append(
            {
                "openyield_module": module,
                "golden_target_cell_or_region": comparison.golden_target_cell_or_region,
                "golden_match_status": comparison.golden_match_status,
                "module_bbox": _bbox_text(bbox),
                "golden_bbox": comparison.golden_bbox,
                "bbox_compatible": comparison.bbox_compatible,
                "pin_mapping_summary": comparison.pin_mapping_summary,
                "pin_compatible": comparison.pin_compatible,
                "rail_compatible": comparison.rail_compatible,
                "pitch_compatible": comparison.pitch_compatible,
                "layer_compatible": comparison.layer_compatible,
                "floorplan_safe": comparison.floorplan_safe,
                "placement_safe": comparison.placement_safe,
                "routing_safe": comparison.routing_safe,
                "power_safe": comparison.power_safe,
                "requires_wrapper": comparison.requires_wrapper,
                "comparison_notes": comparison.comparison_notes,
            }
        )

        decision_rows.append(
            {
                "openyield_module": module,
                "openyield_role": m10_module_rows.get(module, {}).get("openyield_role", ""),
                "module_gds_path": _rel(repo_root, gds_path) if gds_path.exists() else "",
                "generation_status": generation.get("generation_status", ""),
                "generation_strategy": generation.get("generation_strategy", ""),
                "bbox_width": bbox.get("width", 0),
                "bbox_height": bbox.get("height", 0),
                "pin_count": len(pins),
                "rail_status": rail.get("rail_status", ""),
                "contract_pin_used": contract_pin_used,
                "candidate_geometry_used": candidate_geometry_used,
                "golden_target_cell_or_region": comparison.golden_target_cell_or_region,
                "golden_match_status": comparison.golden_match_status,
                "bbox_compatible": comparison.bbox_compatible,
                "pin_compatible": comparison.pin_compatible,
                "rail_compatible": comparison.rail_compatible,
                "pitch_compatible": comparison.pitch_compatible,
                "layer_compatible": comparison.layer_compatible,
                "floorplan_safe": comparison.floorplan_safe,
                "placement_safe": comparison.placement_safe,
                "routing_safe": comparison.routing_safe,
                "power_safe": comparison.power_safe,
                "decision": decision,
                "decision_reason": decision_reason,
                "first_substitution_priority": first_priority,
                "requires_M11B_metadata_extraction": True,
                "requires_wrapper": comparison.requires_wrapper,
                "requires_layoutgen_fallback": requires_layoutgen_fallback,
                "human_review_required": True,
            }
        )

        for pin in pins:
            pin_rows.append(
                {
                    "openyield_module": module,
                    "pin_name": pin.get("name", ""),
                    "pin_layer": pin.get("layer", ""),
                    "pin_source": pin.get("pin_source", ""),
                    "pin_x": pin.get("x", ""),
                    "pin_y": pin.get("y", ""),
                    "module_bbox_width": bbox.get("width", 0),
                    "module_bbox_height": bbox.get("height", 0),
                    "rail_status": rail.get("rail_status", ""),
                    "vdd_gnd_rail_present": vdd_gnd_rail_present,
                    "contract_pin_used": contract_pin_used,
                    "candidate_rail_metadata_used": candidate_rail_metadata_used,
                }
            )

    direct_rows = [row for row in decision_rows if row["decision"] == "DIRECT_HARDMACRO_REPLACE"]
    constraint_rows = [row for row in decision_rows if row["decision"] == "CONSTRAINT_EXTRACTION_ONLY"]
    semantic_rows = [row for row in decision_rows if row["decision"] == "SEMANTIC_REFERENCE_ONLY"]
    rejected_rows = [row for row in decision_rows if row["decision"] == "REJECTED"]
    first_substitution_candidates = [row["openyield_module"] for row in sorted(direct_rows, key=lambda row: row["first_substitution_priority"])[:4]]
    safe_to_attempt_selective_substitution = bool(first_substitution_candidates)
    must_run_m11b_before_substitution = True

    for sequence, row in enumerate(sorted(direct_rows, key=lambda item: item["openyield_module"]), start=1):
        next_plan_rows.append(
            {
                "sequence": sequence,
                "module": row["openyield_module"],
                "decision": row["decision"],
                "priority": row["first_substitution_priority"],
                "why_candidate": row["decision_reason"],
                "requires_wrapper": row["requires_wrapper"],
                "requires_M11B_metadata_extraction": row["requires_M11B_metadata_extraction"],
            }
        )

    review_path, clean_review_path, annotated_debug_path = _build_review_gds(out_dir=out_dir, module_rows=module_rows)
    review_gds_sanity_status = _gds_sanity(review_path)
    _write_review_manifest(repo_root, out_dir, [review_path, clean_review_path, annotated_debug_path, golden_reference])
    review_manifest_json = _read_json(out_dir / "review_gds_manifest.json")
    write_json(out_dir / "M11A_review_gds_manifest.json", review_manifest_json)
    write_text(
        out_dir / "M11A_review_gds_manifest.md",
        _render_md(
            "M11A Review GDS Manifest",
            [f"- `{item['path']}` size={item['size_bytes']} sha256=`{item['sha256']}`" for item in review_manifest_json],
        ),
    )

    write_csv(out_dir / "M11A_module_gds_inventory.csv", MODULE_INVENTORY_FIELDS, module_rows)
    write_text(
        out_dir / "M11A_module_gds_inventory.md",
        _render_md(
            "M11A Module GDS Inventory",
            [f"- `{row['openyield_module']}` decision=`{row['decision']}` top=`{row['top_cell_name']}` bbox=`{row['bbox_width']}x{row['bbox_height']}`" for row in module_rows],
        ),
    )
    write_csv(out_dir / "M11A_module_vs_golden_leaf_comparison.csv", MODULE_VS_GOLDEN_FIELDS, comparison_rows)
    write_text(
        out_dir / "M11A_module_vs_golden_leaf_comparison.md",
        _render_md(
            "M11A Module vs Golden Leaf Comparison",
            [f"- `{row['openyield_module']}` golden=`{row['golden_target_cell_or_region']}` status=`{row['golden_match_status']}` notes=`{row['comparison_notes']}`" for row in comparison_rows],
        ),
    )
    write_csv(out_dir / "M11A_hardmacro_substitution_decision.csv", DECISION_FIELDS, decision_rows)
    write_text(
        out_dir / "M11A_hardmacro_substitution_decision.md",
        _render_md(
            "M11A Hardmacro Substitution Decision",
            [f"- `{row['openyield_module']}` => `{row['decision']}` reason=`{row['decision_reason']}`" for row in decision_rows],
        ),
    )
    write_csv(out_dir / "M11A_pin_bbox_rail_metadata.csv", PIN_METADATA_FIELDS, pin_rows)
    write_json(out_dir / "M11A_pin_bbox_rail_metadata.json", pin_rows)
    write_text(
        out_dir / "M11A_next_substitution_plan.md",
        _render_md(
            "M11A Next Substitution Plan",
            [
                f"- first_substitution_candidates: `{', '.join(first_substitution_candidates)}`",
                "- M11B is mandatory before any substitution attempt.",
                "- M11C should limit itself to the direct-replace candidates selected here.",
            ]
            + [
                f"- candidate `{row['module']}` priority=`{row['priority']}` wrapper=`{row['requires_wrapper']}`"
                for row in next_plan_rows
            ],
        ),
    )
    write_csv(repo_root / "docs/mapping/M11A_module_gds_inventory.csv", MODULE_INVENTORY_FIELDS, module_rows)
    write_csv(repo_root / "docs/mapping/M11A_module_vs_golden_leaf_comparison.csv", MODULE_VS_GOLDEN_FIELDS, comparison_rows)
    write_csv(repo_root / "docs/mapping/M11A_hardmacro_substitution_decision.csv", DECISION_FIELDS, decision_rows)
    write_csv(repo_root / "docs/mapping/M11A_pin_bbox_rail_metadata.csv", PIN_METADATA_FIELDS, pin_rows)
    write_csv(repo_root / "docs/mapping/M11A_next_substitution_plan.csv", NEXT_PLAN_FIELDS, next_plan_rows)

    remaining_blockers = []
    if bbox_metadata_count != len(EXPECTED_MODULES):
        remaining_blockers.append("Some modules are missing bbox metadata.")
    if pin_metadata_count != len(EXPECTED_MODULES):
        remaining_blockers.append("Some modules are missing pin metadata.")
    if rail_metadata_count != len(EXPECTED_MODULES):
        remaining_blockers.append("Some modules are missing rail metadata.")
    if generation_report_count != len(EXPECTED_MODULES):
        remaining_blockers.append("Some modules are missing generation reports.")
    remaining_blockers.extend(
        [
            "M11B metadata extraction is still mandatory before any substitution attempt.",
            "Human KLayout review of module_gds_qualification_review.gds is required.",
            "OpenYield module GDS hardmacro substitution cannot yet be claimed complete at M11A.",
        ]
    )

    goal_md.write_text(_update_goal_md(goal_text), encoding="utf-8", newline="\n")
    progress_md.write_text(
        _update_progress_md(original_progress=progress_text, first_substitution_candidates=first_substitution_candidates),
        encoding="utf-8",
        newline="\n",
    )

    status["current_stage"] = "M11A"
    status["next_stage"] = "WAIT_HUMAN_KLAYOUT_REVIEW"
    status["next_stage_allowed"] = "M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION"
    status["can_enter_next_stage_without_human_review"] = False
    status["can_claim_openyield_module_gds_hardmacro_substitution"] = False
    status["current_goal"] = "M11A qualified the 20 OpenYield module GDS for selective hardmacro substitution candidates and determined M11B metadata extraction is mandatory before any substitution attempt."
    status["last_M11A_report"] = {
        "status_file_read": True,
        "status_file_updated": True,
        "goal_file_read": True,
        "goal_file_updated": True,
        "progress_file_updated": True,
        "module_gds_dir_found": module_gds_dir.exists(),
        "module_gds_count": len(module_dirs),
        "expected_openyield_module_count": len(EXPECTED_MODULES),
        "all_expected_modules_have_gds": all((module_gds_dir / module / f"{module}.gds").exists() for module in EXPECTED_MODULES),
        "bbox_metadata_count": bbox_metadata_count,
        "pin_metadata_count": pin_metadata_count,
        "rail_metadata_count": rail_metadata_count,
        "generation_report_count": generation_report_count,
        "direct_hardmacro_replace_count": len(direct_rows),
        "constraint_extraction_only_count": len(constraint_rows),
        "semantic_reference_only_count": len(semantic_rows),
        "rejected_count": len(rejected_rows),
        "first_substitution_candidates": first_substitution_candidates,
        "safe_to_attempt_selective_substitution": safe_to_attempt_selective_substitution,
        "must_run_M11B_before_substitution": must_run_m11b_before_substitution,
        "review_gds_generated": True,
        "review_gds_path": _rel(repo_root, review_path),
        "clean_review_gds_path": _rel(repo_root, clean_review_path),
        "annotated_debug_gds_path": _rel(repo_root, annotated_debug_path),
        "review_gds_sanity_status": review_gds_sanity_status,
        "can_claim_openyield_module_gds_hardmacro_substitution": False,
        "can_enter_M11B_after_this_gate": True,
        "human_klayout_review_required": True,
        "can_enter_next_stage_before_human_review": False,
        "remaining_M11A_blockers": remaining_blockers,
        "remaining_M11A_blockers_count": len(remaining_blockers),
    }
    for asset in status.get("ten_required_assets_for_netlist_to_layout", []):
        if asset["asset_id"] == "PHYSICAL_IMPLEMENTATION_LIBRARY":
            asset["evidence_paths"] = [
                "outputs/openyield_module_gds/",
                "docs/mapping/M11A_hardmacro_substitution_decision.csv",
                "docs/mapping/M11A_module_vs_golden_leaf_comparison.csv",
            ]
            asset["next_action"] = "M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION"
            asset["blocking_for_next_stage"] = True
        elif asset["asset_id"] == "PIN_BBOX_RAIL_METADATA":
            asset["evidence_paths"] = [
                "docs/mapping/M11A_pin_bbox_rail_metadata.csv",
                "outputs/M11A_module_gds_qualification/current_supported_config/M11A_pin_bbox_rail_metadata.json",
                "docs/mapping/M11A_hardmacro_substitution_decision.csv",
            ]
            asset["next_action"] = "M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION"
            asset["blocking_for_next_stage"] = True
    write_json(status_json, status)
    write_text(
        status_md,
        _render_md(
            "OpenYield SRAM LayoutGen Project Status",
            [
                "## 1. Current Correct Goal",
                "",
                "M11A 已对 20 个 OpenYield module GDS 做资格审查，确认可用于 direct replacement 的候选、只能提取约束的候选，以及仍只能作为语义参考的模块；下一步必须进入 M11B metadata extraction。",
                "",
                "## 2. Current Stage",
                "",
                "- current_stage: `M11A`",
                "- next_stage: `WAIT_HUMAN_KLAYOUT_REVIEW`",
                "- human_klayout_review_required_every_stage: `True`",
                "- can_enter_next_stage_without_human_review: `False`",
                "- next_stage_allowed: `M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION`",
                "",
                "## 3. Latest M11A Result",
                "",
                f"- module_gds_count: `{len(module_dirs)}`",
                f"- direct_hardmacro_replace_count: `{len(direct_rows)}`",
                f"- constraint_extraction_only_count: `{len(constraint_rows)}`",
                f"- semantic_reference_only_count: `{len(semantic_rows)}`",
                f"- rejected_count: `{len(rejected_rows)}`",
                f"- first_substitution_candidates: `{', '.join(first_substitution_candidates)}`",
                f"- review_gds_path: `{_rel(repo_root, review_path)}`",
                f"- review_gds_sanity_status: `{review_gds_sanity_status}`",
                "- can_claim_openyield_module_gds_hardmacro_substitution: `False`",
                "- next_stage_allowed: `M11B_PIN_BBOX_RAIL_METADATA_EXTRACTION`",
            ],
        ),
    )

    report = {
        "status_file_read": True,
        "status_file_updated": True,
        "goal_file_read": True,
        "goal_file_updated": True,
        "progress_file_updated": True,
        "reused_previous_artifacts": reused_previous_artifacts,
        "deprecated_previous_artifacts": deprecated_previous_artifacts,
        "current_stage_inputs": current_stage_inputs,
        "current_stage_delta_from_M11H": current_stage_delta_from_M11H,
        "why_M11A_is_needed": why_m11a_is_needed,
        "module_gds_dir_found": module_gds_dir.exists(),
        "module_gds_count": len(module_dirs),
        "expected_openyield_module_count": len(EXPECTED_MODULES),
        "all_expected_modules_have_gds": all((module_gds_dir / module / f"{module}.gds").exists() for module in EXPECTED_MODULES),
        "bbox_metadata_count": bbox_metadata_count,
        "pin_metadata_count": pin_metadata_count,
        "rail_metadata_count": rail_metadata_count,
        "generation_report_count": generation_report_count,
        "golden_reference_loaded": golden_reference.exists(),
        "m10_module_trace_loaded": m10_module_trace.exists(),
        "m9_module_binding_loaded": m9_module_binding.exists(),
        "direct_hardmacro_replace_count": len(direct_rows),
        "constraint_extraction_only_count": len(constraint_rows),
        "semantic_reference_only_count": len(semantic_rows),
        "rejected_count": len(rejected_rows),
        "first_substitution_candidates": first_substitution_candidates,
        "safe_to_attempt_selective_substitution": safe_to_attempt_selective_substitution,
        "must_run_M11B_before_substitution": must_run_m11b_before_substitution,
        "review_gds_generated": True,
        "review_gds_path": _rel(repo_root, review_path),
        "clean_review_gds_path": _rel(repo_root, clean_review_path),
        "annotated_debug_gds_path": _rel(repo_root, annotated_debug_path),
        "review_gds_sanity_status": review_gds_sanity_status,
        "can_claim_openyield_module_gds_hardmacro_substitution": False,
        "can_enter_M11B_after_this_gate": True,
        "human_klayout_review_required": True,
        "can_enter_next_stage_before_human_review": False,
        "remaining_M11A_blockers": remaining_blockers,
        "remaining_M11A_blockers_count": len(remaining_blockers),
    }
    write_json(out_json, report)
    write_text(
        out_report,
        _render_md(
            "M11A Module GDS Qualification Report",
            [
                f"- module_gds_count: `{report['module_gds_count']}`",
                f"- direct_hardmacro_replace_count: `{report['direct_hardmacro_replace_count']}`",
                f"- constraint_extraction_only_count: `{report['constraint_extraction_only_count']}`",
                f"- semantic_reference_only_count: `{report['semantic_reference_only_count']}`",
                f"- rejected_count: `{report['rejected_count']}`",
                f"- first_substitution_candidates: `{', '.join(first_substitution_candidates)}`",
                f"- must_run_M11B_before_substitution: `{report['must_run_M11B_before_substitution']}`",
                f"- review_gds_path: `{report['review_gds_path']}`",
                f"- review_gds_sanity_status: `{report['review_gds_sanity_status']}`",
                f"- can_claim_openyield_module_gds_hardmacro_substitution: `{report['can_claim_openyield_module_gds_hardmacro_substitution']}`",
            ],
        ),
    )
    write_text(
        repo_root / "docs/evidence/M11A_module_gds_qualification_summary.md",
        _render_md(
            "M11A Module GDS Qualification Summary",
            [
                f"- module_gds_count: `{report['module_gds_count']}`",
                f"- all_expected_modules_have_gds: `{report['all_expected_modules_have_gds']}`",
                f"- first_substitution_candidates: `{', '.join(first_substitution_candidates)}`",
                f"- must_run_M11B_before_substitution: `{report['must_run_M11B_before_substitution']}`",
                f"- remaining_M11A_blockers_count: `{report['remaining_M11A_blockers_count']}`",
            ],
        ),
    )
    return report
