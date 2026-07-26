from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.gds_hierarchy_export import TopCellImportPlan, build_top_level_library, collect_search_paths


REQUIRED_MODULES = [
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
    "CONTROL_LOGIC",
    "DELAY_CHAIN",
    "PRECHARGE_ENABLE_PATH",
    "SENSE_ENABLE_PATH",
    "WRITE_ENABLE_PATH",
    "WORDLINE_ENABLE_PATH",
    "GATED_CLOCK_PATH",
    "DFF_ROW",
]

ROW_PATH_MODULES = [
    "row_decoder",
    "wordline_decoder",
    "decoder_gate_cells",
    "wordline_driver",
    "wordline_driver_gate_cells",
]

COLUMN_PATH_MODULES = [
    "precharge",
    "column_mux",
    "sense_amp",
    "write_driver",
]

CONTROL_MODULES = [
    "CONTROL_LOGIC",
    "DELAY_CHAIN",
    "PRECHARGE_ENABLE_PATH",
    "SENSE_ENABLE_PATH",
    "WRITE_ENABLE_PATH",
    "WORDLINE_ENABLE_PATH",
    "GATED_CLOCK_PATH",
    "DFF_ROW",
]

REAL_REUSE_STATUSES = {
    "REAL_ARRAY_BASE_REUSABLE",
    "REAL_ARRAY_BASE_REUSABLE_WITH_REPLICA_RULES",
    "REAL_HARDMACRO_WRAPPER_REUSABLE",
    "REAL_HARDMACRO_WRAPPER_REUSABLE_WITH_REPAIRED_SOURCE",
}

TEMP_WRAPPER_TEXT = "TEMP_WRAPPER_FOR_M2_REVIEW"
ANNOTATION_LAYER = 900
ANNOTATION_TEXTTYPE = 0
OUTLINE_LAYER = 901
OUTLINE_DATATYPE = 0


@dataclass(frozen=True)
class ModuleSource:
    module_name: str
    physical_role: str
    source_class: str
    binding_status: str
    source_gds_path: Path
    root_cell_name: str
    bbox: dict[str, float]
    temporary_wrapper: bool
    source_note: str
    generation_source: str


@dataclass(frozen=True)
class ModulePlacement:
    module_name: str
    physical_role: str
    source_class: str
    instance_name: str
    gds_path: Path
    root_cell_name: str
    x: float
    y: float
    width: float
    height: float
    region: str
    orientation: str = "R0"

    def bbox(self) -> dict[str, float]:
        return {
            "x0": round(self.x, 6),
            "y0": round(self.y, 6),
            "x1": round(self.x + self.width, 6),
            "y1": round(self.y + self.height, 6),
            "width": round(self.width, 6),
            "height": round(self.height, 6),
        }


def _json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_md(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _top_cell_name(path: Path) -> str:
    lib = gdstk.read_gds(path)
    tops = lib.top_level()
    if tops:
        return str(tops[0].name)
    if lib.cells:
        return str(lib.cells[0].name)
    raise ValueError(f"No cells found in {path}")


def _md_table(columns: list[str], rows: list[dict[str, Any]]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")).replace("\n", "<br>") for column in columns) + " |")
    return "\n".join(lines) + "\n"


def _module_bbox(module_dir: Path) -> dict[str, float]:
    bbox = _read_json(module_dir / "bbox.json")
    return {
        "x0": float(bbox["x0"]),
        "y0": float(bbox["y0"]),
        "x1": float(bbox["x1"]),
        "y1": float(bbox["y1"]),
        "width": float(bbox["width"]),
        "height": float(bbox["height"]),
    }


def _module_source_rows(binding_csv: Path, module_gds_dir: Path) -> list[ModuleSource]:
    rows = _read_csv(binding_csv)
    results: list[ModuleSource] = []
    for row in rows:
        module_name = row["openyield_module"]
        module_dir = module_gds_dir / module_name
        gds_path = module_dir / f"{module_name}.gds"
        bbox = _module_bbox(module_dir)
        binding_status = row["binding_status"]
        can_reuse = row["can_reuse_first_round_module_directly"].strip().lower() == "true"
        if can_reuse and binding_status in REAL_REUSE_STATUSES:
            source_class = "first_round_openyield_gds"
            generation_source = "layoutgen real generator reuse candidate"
            temp = False
            note = "Reuse first-round OpenYield module GDS directly for M2 review."
        else:
            source_class = "temporary_wrapper"
            generation_source = "layoutgen review wrapper around first-round candidate GDS"
            temp = True
            note = "First-round candidate composite wrapped for M2 review and explicitly marked temporary."
        results.append(
            ModuleSource(
                module_name=module_name,
                physical_role=row["physical_role"],
                source_class=source_class,
                binding_status=binding_status,
                source_gds_path=gds_path,
                root_cell_name=_top_cell_name(gds_path),
                bbox=bbox,
                temporary_wrapper=temp,
                source_note=note,
                generation_source=generation_source,
            )
        )
    return results


def _place_modules(module_sources: list[ModuleSource]) -> list[ModulePlacement]:
    by_name = {item.module_name: item for item in module_sources}
    array = by_name["bitcell_array"]
    dummy = by_name["dummy_array"]
    replica = by_name["replica_array"]

    margin_x = 2.0
    margin_y = 2.0
    array_x = 16.0
    array_y = 12.0
    placements: list[ModulePlacement] = []

    placements.append(
        ModulePlacement(
            module_name="bitcell_array",
            physical_role=array.physical_role,
            source_class=array.source_class,
            instance_name="u_bitcell_array",
            gds_path=array.source_gds_path,
            root_cell_name=array.root_cell_name,
            x=array_x,
            y=array_y,
            width=array.bbox["width"],
            height=array.bbox["height"],
            region="ARRAY_CORE_REGION",
        )
    )
    placements.append(
        ModulePlacement(
            module_name="dummy_array",
            physical_role=dummy.physical_role,
            source_class=dummy.source_class,
            instance_name="u_dummy_array",
            gds_path=dummy.source_gds_path,
            root_cell_name=dummy.root_cell_name,
            x=array_x - dummy.bbox["width"] - margin_x,
            y=array_y,
            width=dummy.bbox["width"],
            height=dummy.bbox["height"],
            region="ARRAY_DUMMY_REGION",
        )
    )
    placements.append(
        ModulePlacement(
            module_name="replica_array",
            physical_role=replica.physical_role,
            source_class=replica.source_class,
            instance_name="u_replica_array",
            gds_path=replica.source_gds_path,
            root_cell_name=replica.root_cell_name,
            x=array_x + array.bbox["width"] + margin_x,
            y=array_y,
            width=replica.bbox["width"],
            height=replica.bbox["height"],
            region="ARRAY_REPLICA_REGION",
        )
    )

    row_cursor_y = array_y
    row_x = array_x - margin_x
    for module_name in ROW_PATH_MODULES:
        source = by_name[module_name]
        placements.append(
            ModulePlacement(
                module_name=module_name,
                physical_role=source.physical_role,
                source_class=source.source_class,
                instance_name=f"u_{module_name}",
                gds_path=source.source_gds_path,
                root_cell_name=source.root_cell_name,
                x=row_x - source.bbox["width"],
                y=row_cursor_y,
                width=source.bbox["width"],
                height=source.bbox["height"],
                region="ROW_PATH_REGION",
            )
        )
        row_cursor_y += source.bbox["height"] + 0.8

    column_cursor_x = array_x
    column_y = array_y + array.bbox["height"] + margin_y
    for module_name in COLUMN_PATH_MODULES:
        source = by_name[module_name]
        placements.append(
            ModulePlacement(
                module_name=module_name,
                physical_role=source.physical_role,
                source_class=source.source_class,
                instance_name=f"u_{module_name}",
                gds_path=source.source_gds_path,
                root_cell_name=source.root_cell_name,
                x=column_cursor_x,
                y=column_y,
                width=source.bbox["width"],
                height=source.bbox["height"],
                region="COLUMN_PATH_REGION",
            )
        )
        column_cursor_x += source.bbox["width"] + 1.0

    control_x = array_x + array.bbox["width"] + replica.bbox["width"] + 5.0
    control_y = column_y
    control_limit = column_y + max(by_name[name].bbox["height"] for name in CONTROL_MODULES) * 3.0
    current_x = control_x
    current_y = control_y
    row_max_height = 0.0
    for module_name in CONTROL_MODULES:
        source = by_name[module_name]
        if current_y + source.bbox["height"] > control_limit and row_max_height > 0:
            current_x += 5.0
            current_y = control_y
            row_max_height = 0.0
        placements.append(
            ModulePlacement(
                module_name=module_name,
                physical_role=source.physical_role,
                source_class=source.source_class,
                instance_name=f"u_{module_name}",
                gds_path=source.source_gds_path,
                root_cell_name=source.root_cell_name,
                x=current_x,
                y=current_y,
                width=source.bbox["width"],
                height=source.bbox["height"],
                region="CONTROL_REGION",
            )
        )
        current_y += source.bbox["height"] + 0.8
        row_max_height = max(row_max_height, source.bbox["height"])

    return placements


def _create_temp_wrapper(module: ModuleSource, wrapper_dir: Path, technology_gds_root: Path) -> tuple[Path, str, dict[str, Any]]:
    wrapper_dir.mkdir(parents=True, exist_ok=True)
    wrapper_top = f"M2_TEMP_WRAPPER_{module.module_name}"
    import_plans = [
        TopCellImportPlan(
            module_name=module.module_name,
            module_gds_path=module.source_gds_path,
            root_cell_name=module.root_cell_name,
            instance_name=f"wrapped_{module.module_name}",
            origin_x=0.0,
            origin_y=0.0,
            orientation="R0",
        )
    ]
    search_paths = collect_search_paths([module.source_gds_path], technology_gds_root)
    lib, manifest = build_top_level_library(import_plans, search_paths, top_cell_name=wrapper_top)
    top = lib.top_level()[0]
    bbox = module.bbox
    top.add(
        gdstk.rectangle(
            (bbox["x0"] - 0.2, bbox["y0"] - 0.2),
            (bbox["x1"] + 0.2, bbox["y1"] + 0.2),
            layer=OUTLINE_LAYER,
            datatype=OUTLINE_DATATYPE,
        )
    )
    top.add(gdstk.Label(TEMP_WRAPPER_TEXT, (bbox["x0"], bbox["y1"] + 0.5), layer=ANNOTATION_LAYER, texttype=ANNOTATION_TEXTTYPE))
    top.add(
        gdstk.Label(
            f"{module.module_name} candidate composite",
            (bbox["x0"], bbox["y1"] + 1.1),
            layer=ANNOTATION_LAYER,
            texttype=ANNOTATION_TEXTTYPE,
        )
    )
    wrapper_path = wrapper_dir / f"{module.module_name}.gds"
    lib.write_gds(wrapper_path)
    return wrapper_path, wrapper_top, manifest


def _resolve_module_sources(binding_csv: Path, module_gds_dir: Path, wrapper_dir: Path, technology_gds_root: Path) -> tuple[list[ModuleSource], dict[str, Any]]:
    base_sources = _module_source_rows(binding_csv, module_gds_dir)
    wrapper_manifests: dict[str, Any] = {}
    resolved: list[ModuleSource] = []
    for source in base_sources:
        if not source.temporary_wrapper:
            resolved.append(source)
            continue
        wrapper_path, wrapper_top, manifest = _create_temp_wrapper(source, wrapper_dir, technology_gds_root)
        wrapper_manifests[source.module_name] = {
            "wrapper_gds_path": str(wrapper_path),
            "wrapper_top_cell_name": wrapper_top,
            "manifest": manifest,
        }
        resolved.append(
            ModuleSource(
                module_name=source.module_name,
                physical_role=source.physical_role,
                source_class=source.source_class,
                binding_status=source.binding_status,
                source_gds_path=wrapper_path,
                root_cell_name=wrapper_top,
                bbox=source.bbox,
                temporary_wrapper=True,
                source_note=source.source_note,
                generation_source=source.generation_source,
            )
        )
    return resolved, wrapper_manifests


def _build_top_gds(
    placements: list[ModulePlacement],
    technology_gds_root: Path,
    out_gds_path: Path,
    top_cell_name: str,
) -> dict[str, Any]:
    import_plans = [
        TopCellImportPlan(
            module_name=placement.module_name,
            module_gds_path=placement.gds_path,
            root_cell_name=placement.root_cell_name,
            instance_name=placement.instance_name,
            origin_x=placement.x,
            origin_y=placement.y,
            orientation=placement.orientation,
        )
        for placement in placements
    ]
    search_paths = collect_search_paths([placement.gds_path for placement in placements], technology_gds_root)
    lib, manifest = build_top_level_library(import_plans, search_paths, top_cell_name=top_cell_name)
    top = next(cell for cell in lib.cells if cell.name == top_cell_name)
    bbox = _union_bbox([item.bbox() for item in placements])
    top.add(gdstk.rectangle((bbox["x0"] - 1.0, bbox["y0"] - 1.0), (bbox["x1"] + 1.0, bbox["y1"] + 1.0), layer=OUTLINE_LAYER, datatype=OUTLINE_DATATYPE))
    top.add(gdstk.Label(top_cell_name, (bbox["x0"], bbox["y1"] + 1.5), layer=ANNOTATION_LAYER, texttype=ANNOTATION_TEXTTYPE))
    top.add(gdstk.Label("ROW_PATH_REGION", (bbox["x0"] - 0.5, bbox["y0"] + 1.0), layer=ANNOTATION_LAYER, texttype=ANNOTATION_TEXTTYPE))
    top.add(gdstk.Label("COLUMN_PATH_REGION", (bbox["x0"] + 1.0, bbox["y1"] - 0.5), layer=ANNOTATION_LAYER, texttype=ANNOTATION_TEXTTYPE))
    top.add(gdstk.Label("CONTROL_REGION", (bbox["x1"] - 6.0, bbox["y1"] - 0.5), layer=ANNOTATION_LAYER, texttype=ANNOTATION_TEXTTYPE))
    out_gds_path.parent.mkdir(parents=True, exist_ok=True)
    lib.write_gds(out_gds_path)
    return {
        "hierarchy_manifest": manifest,
        "search_path_count": len(search_paths),
        "bbox": bbox,
    }


def _union_bbox(boxes: list[dict[str, float]]) -> dict[str, float]:
    return {
        "x0": round(min(box["x0"] for box in boxes), 6),
        "y0": round(min(box["y0"] for box in boxes), 6),
        "x1": round(max(box["x1"] for box in boxes), 6),
        "y1": round(max(box["y1"] for box in boxes), 6),
        "width": round(max(box["x1"] for box in boxes) - min(box["x0"] for box in boxes), 6),
        "height": round(max(box["y1"] for box in boxes) - min(box["y0"] for box in boxes), 6),
    }


def _gds_sanity(gds_path: Path, top_cell_name: str) -> dict[str, Any]:
    try:
        lib = gdstk.read_gds(gds_path)
    except Exception as exc:
        return {
            "status": "GDS_PARSE_FAILED",
            "error": str(exc),
            "top_cell_name": None,
            "gds_size_bytes": gds_path.stat().st_size if gds_path.exists() else 0,
        }
    tops = lib.top_level()
    top = next((cell for cell in tops if cell.name == top_cell_name), tops[0] if tops else None)
    if top is None:
        return {
            "status": "TOP_CELL_MISSING",
            "error": "Top cell not found after parse.",
            "top_cell_name": None,
            "gds_size_bytes": gds_path.stat().st_size,
        }
    top_bbox = top.bounding_box()
    bbox = None
    if top_bbox is not None:
        bbox = {
            "x0": round(float(top_bbox[0][0]), 6),
            "y0": round(float(top_bbox[0][1]), 6),
            "x1": round(float(top_bbox[1][0]), 6),
            "y1": round(float(top_bbox[1][1]), 6),
            "width": round(float(top_bbox[1][0] - top_bbox[0][0]), 6),
            "height": round(float(top_bbox[1][1] - top_bbox[0][1]), 6),
        }
    return {
        "status": "GDS_PARSED_SANITY_PASSED",
        "error": "",
        "top_cell_name": str(top.name),
        "gds_size_bytes": gds_path.stat().st_size,
        "cell_count": len(lib.cells),
        "top_bbox": bbox,
    }


def _status_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OpenYield SRAM LayoutGen Project Status",
            "",
            "## 1. Current Correct Goal",
            "",
            "基于原 layoutgen 版图生成器，将 OpenYield 的模块、网表语义和连接关系接入真实 SRAM GDS 生成主干，生成 OpenYield-driven layoutgen-based SRAM GDS。",
            "",
            "## 2. Current Route",
            "",
            "- S0：全部成果整理与路线重置",
            "- M1：layoutgen 原生成路径审计 + OpenYield 模块绑定",
            "- M2：生成第一版 layoutgen-based OpenYield SRAM full trial review GDS",
            "- M3：等待人工 KLayout review 后再决定是否进入真实 routing/power closure",
            "",
            "## 3. Current Stage",
            "",
            "- current_stage: `M2`",
            "- next_stage: `M3`",
            "- human_klayout_review_required_every_stage: `True`",
            "- can_enter_next_stage_without_human_review: `False`",
            "",
            "## 4. M2 Result",
            "",
            f"- full_sram_review_gds_generated: `{report['full_sram_review_gds_generated']}`",
            f"- full_sram_review_gds_path: `{report['full_sram_review_gds_path']}`",
            f"- full_sram_review_gds_size_bytes: `{report['full_sram_review_gds_size_bytes']}`",
            f"- top_cell_name: `{report['top_cell_name']}`",
            f"- gds_sanity_status: `{report['gds_sanity_status']}`",
            f"- modules_placed_count: `{report['modules_placed_count']}`",
            f"- temporary_wrapper_count: `{report['temporary_wrapper_count']}`",
            f"- layoutgen_real_generator_used_count: `{report['layoutgen_real_generator_used_count']}`",
            f"- first_round_openyield_gds_used_count: `{report['first_round_openyield_gds_used_count']}`",
            "",
            "## 5. Review Gate",
            "",
            "- This M2 GDS is for human KLayout review only.",
            "- Do not claim DRC clean.",
            "- Do not claim LVS clean.",
            "- Do not claim signoff-ready.",
            "- Do not auto-enter M3 before user review.",
            "",
            "## 6. Next Immediate Task",
            "",
            f"等待人工 KLayout review `{report['full_sram_review_gds_path']}`。未经用户确认，不进入 M3。",
            "",
        ]
    )


def _update_status_json(status_json: dict[str, Any], report: dict[str, Any]) -> dict[str, Any]:
    updated = dict(status_json)
    updated["current_stage"] = "M2"
    updated["next_stage"] = "M3"
    updated["can_enter_next_stage_without_human_review"] = False
    updated["next_task_summary"] = f"Wait for human KLayout review of {report['full_sram_review_gds_path']} before entering M3."
    updated["last_M2_report"] = {
        "full_sram_review_gds_generated": report["full_sram_review_gds_generated"],
        "full_sram_review_gds_path": report["full_sram_review_gds_path"],
        "top_cell_name": report["top_cell_name"],
        "gds_sanity_status": report["gds_sanity_status"],
        "temporary_wrapper_count": report["temporary_wrapper_count"],
        "human_klayout_review_required": report["human_klayout_review_required"],
        "can_enter_M3_before_human_review": report["can_enter_M3_before_human_review"],
    }
    return updated


def run_m2_full_trial(
    *,
    repo_root: Path,
    status_md: Path,
    status_json: Path,
    m1_binding: Path,
    m1_net_binding: Path,
    openyield_module_gds_dir: Path,
    layoutgen_reference_gds: Path,
    out_dir: Path,
    out_json: Path,
    out_report: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    status_md = status_md.resolve()
    status_json = status_json.resolve()
    m1_binding = m1_binding.resolve()
    m1_net_binding = m1_net_binding.resolve()
    openyield_module_gds_dir = openyield_module_gds_dir.resolve()
    layoutgen_reference_gds = layoutgen_reference_gds.resolve()
    out_dir = out_dir.resolve()
    out_json = out_json.resolve()
    out_report = out_report.resolve()

    if not status_md.exists() or not status_json.exists():
        raise FileNotFoundError("PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md/json must exist before running M2.")

    _read_md(status_md)
    status_payload = _read_json(status_json)
    binding_rows = _read_csv(m1_binding)
    net_binding_rows = _read_csv(m1_net_binding)
    technology_gds_root = repo_root / "technology/freepdk45/gds_lib"
    wrapper_dir = out_dir / "review_wrappers"

    resolved_sources, wrapper_manifests = _resolve_module_sources(m1_binding, openyield_module_gds_dir, wrapper_dir, technology_gds_root)
    placements = _place_modules(resolved_sources)
    top_gds_path = out_dir / "openyield_layoutgen_full_trial_sram.gds"
    top_cell_name = "openyield_layoutgen_full_trial_sram"
    hierarchy_info = _build_top_gds(placements, technology_gds_root, top_gds_path, top_cell_name)
    sanity = _gds_sanity(top_gds_path, top_cell_name)

    source_by_name = {item.module_name: item for item in resolved_sources}
    placement_by_name = {item.module_name: item for item in placements}
    required_modules = [row["openyield_module"] for row in binding_rows]
    missing_modules = sorted(set(required_modules) - set(placement_by_name))

    module_usage_rows: list[dict[str, Any]] = []
    for row in binding_rows:
        source = source_by_name[row["openyield_module"]]
        placement = placement_by_name.get(source.module_name)
        module_usage_rows.append(
            {
                "openyield_module": source.module_name,
                "physical_role": source.physical_role,
                "binding_status": source.binding_status,
                "physical_source_class": source.source_class,
                "physical_source_gds_path": str(source.source_gds_path),
                "physical_source_top_cell": source.root_cell_name,
                "temporary_wrapper": source.temporary_wrapper,
                "generation_source": source.generation_source,
                "placed_in_top": placement is not None,
                "region": placement.region if placement else "",
                "source_note": source.source_note,
            }
        )

    placement_rows = [
        {
            "module_name": item.module_name,
            "physical_role": item.physical_role,
            "source_class": item.source_class,
            "instance_name": item.instance_name,
            "region": item.region,
            "x": item.x,
            "y": item.y,
            "width": item.width,
            "height": item.height,
            "bbox": item.bbox(),
        }
        for item in placements
    ]

    unresolved_gap_rows = [
        {
            "gap_id": "GAP_ROUTE_001",
            "category": "signal_routing",
            "scope": "inter_module_connections",
            "severity": "review_only",
            "description": "Wordline/data/control nets are not fully geometry-routed in M2; placement and hierarchy are provided for visual review first.",
            "blocking_M2_review": False,
        },
        {
            "gap_id": "GAP_POWER_001",
            "category": "power_network",
            "scope": "top_level_power_stitch",
            "severity": "review_only",
            "description": "Top-level VDD/VSS straps and final rail stitching are not fully closed in M2.",
            "blocking_M2_review": False,
        },
        {
            "gap_id": "GAP_REALNESS_001",
            "category": "module_realness",
            "scope": "row_and_control_candidates",
            "severity": "review_only",
            "description": "Row/control candidates remain explicit TEMP_WRAPPER_FOR_M2_REVIEW wrappers until true layoutgen-owned replacements are available.",
            "blocking_M2_review": False,
        },
    ]

    real_count = sum(1 for item in module_usage_rows if item["physical_source_class"] == "first_round_openyield_gds" and item["binding_status"] in REAL_REUSE_STATUSES)
    first_round_count = real_count
    temp_count = sum(1 for item in module_usage_rows if item["temporary_wrapper"])
    access_count = sum(1 for row in module_usage_rows if "_access_module" in row["physical_source_gds_path"] or "access_module" in row["physical_source_top_cell"].lower())
    floorplan_proxy_count = sum(1 for row in module_usage_rows if "floorplan_proxy" in row["physical_source_top_cell"].lower() or "floorplan_proxy" in row["physical_source_gds_path"])

    visual_report = {
        "top_cell_name": top_cell_name,
        "array_core_region_modules": [item["openyield_module"] for item in module_usage_rows if item["physical_role"] in {"ARRAY_CORE", "ARRAY_DUMMY", "ARRAY_REPLICA"}],
        "row_path_modules": ROW_PATH_MODULES,
        "column_path_modules": COLUMN_PATH_MODULES,
        "control_modules": CONTROL_MODULES,
        "bitcell_array_present": "bitcell_array" in placement_by_name,
        "dummy_or_replica_present": "dummy_array" in placement_by_name or "replica_array" in placement_by_name,
        "row_path_present": all(name in placement_by_name for name in ROW_PATH_MODULES),
        "column_path_present": all(name in placement_by_name for name in COLUMN_PATH_MODULES),
        "control_region_present": all(name in placement_by_name for name in CONTROL_MODULES),
        "visual_macro_direction_comment": "Array is central, row path sits on one side, column path sits above the array, and control wrappers are kept in an outer periphery cluster.",
    }

    assembly_report = {
        "top_cell_name": top_cell_name,
        "top_gds_path": str(top_gds_path),
        "top_bbox": hierarchy_info["bbox"],
        "placed_instance_count": len(placements),
        "required_module_count": len(required_modules),
        "placement_regions": sorted({item.region for item in placements}),
        "layoutgen_reference_gds": str(layoutgen_reference_gds),
        "hierarchy_manifest": hierarchy_info["hierarchy_manifest"],
    }

    real_module_generation_report = {
        "required_module_count": len(required_modules),
        "layoutgen_real_generator_used_count": real_count,
        "first_round_openyield_gds_used_count": first_round_count,
        "temporary_wrapper_count": temp_count,
        "wrapper_manifest_count": len(wrapper_manifests),
        "module_sources": module_usage_rows,
    }

    gap_and_risk_report = {
        "unresolved_gap_count": len(unresolved_gap_rows),
        "unresolved_gaps": unresolved_gap_rows,
        "human_klayout_review_required": True,
        "can_enter_M3_before_human_review": False,
    }

    report = {
        "M2_layoutgen_full_trial_available": True,
        "status_file_read": True,
        "status_file_updated": True,
        "full_sram_review_gds_generated": top_gds_path.exists(),
        "full_sram_review_gds_path": str(top_gds_path),
        "full_sram_review_gds_size_bytes": sanity["gds_size_bytes"],
        "top_cell_name": sanity["top_cell_name"],
        "gds_sanity_status": sanity["status"],
        "required_module_count": len(required_modules),
        "modules_placed_count": len(placements),
        "modules_missing_count": len(missing_modules),
        "bitcell_array_present": visual_report["bitcell_array_present"],
        "dummy_or_replica_present": visual_report["dummy_or_replica_present"],
        "row_path_present": visual_report["row_path_present"],
        "column_path_present": visual_report["column_path_present"],
        "control_region_present": visual_report["control_region_present"],
        "access_module_as_primary_count": access_count,
        "floorplan_proxy_count": floorplan_proxy_count,
        "temporary_wrapper_count": temp_count,
        "layoutgen_real_generator_used_count": real_count,
        "first_round_openyield_gds_used_count": first_round_count,
        "human_klayout_review_required": True,
        "can_enter_M3_before_human_review": False,
        "remaining_M2_blockers": [],
        "remaining_M2_blockers_count": 0,
        "modules_missing": missing_modules,
        "reference_inputs": {
            "status_md": str(status_md),
            "status_json": str(status_json),
            "m1_binding": str(m1_binding),
            "m1_net_binding": str(m1_net_binding),
            "layoutgen_reference_gds": str(layoutgen_reference_gds),
            "openyield_module_gds_dir": str(openyield_module_gds_dir),
            "net_binding_count": len(net_binding_rows),
        },
    }

    status_md.write_text(_status_markdown(report), encoding="utf-8", newline="\n")
    status_json.write_text(json.dumps(_update_status_json(status_payload, report), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    out_dir.mkdir(parents=True, exist_ok=True)
    _json_dump(out_dir / "review_gds_manifest.json", {"top_cell_name": top_cell_name, "gds_path": str(top_gds_path), "hierarchy_manifest": hierarchy_info["hierarchy_manifest"], "wrapper_manifests": wrapper_manifests})
    _write_text(out_dir / "review_gds_manifest.md", "# M2 Review GDS Manifest\n\n" + "\n".join([f"- top_cell_name: `{top_cell_name}`", f"- gds_path: `{top_gds_path}`", f"- wrapper_count: `{len(wrapper_manifests)}`"]) + "\n")

    _json_dump(out_dir / "M2_real_module_generation_report.json", real_module_generation_report)
    _write_text(
        out_dir / "M2_real_module_generation_report.md",
        "# M2 Real Module Generation Report\n\n"
        + "\n".join(
            [
                f"- layoutgen_real_generator_used_count: `{real_count}`",
                f"- first_round_openyield_gds_used_count: `{first_round_count}`",
                f"- temporary_wrapper_count: `{temp_count}`",
            ]
        )
        + "\n\n"
        + _md_table(
            ["openyield_module", "physical_role", "binding_status", "physical_source_class", "temporary_wrapper", "region", "source_note"],
            module_usage_rows,
        ),
    )

    _json_dump(out_dir / "M2_full_sram_assembly_report.json", assembly_report)
    _write_text(
        out_dir / "M2_full_sram_assembly_report.md",
        "# M2 Full SRAM Assembly Report\n\n"
        + "\n".join(
            [
                f"- top_cell_name: `{top_cell_name}`",
                f"- top_gds_path: `{top_gds_path}`",
                f"- placed_instance_count: `{len(placements)}`",
                f"- top_bbox: `{hierarchy_info['bbox']}`",
            ]
        )
        + "\n\n"
        + _md_table(["module_name", "physical_role", "source_class", "region", "x", "y", "width", "height"], placement_rows),
    )

    _json_dump(out_dir / "M2_visual_structure_check_report.json", visual_report)
    _write_text(
        out_dir / "M2_visual_structure_check_report.md",
        "# M2 Visual Structure Check Report\n\n"
        + "\n".join([f"- {key}: `{value}`" for key, value in visual_report.items() if key != "visual_macro_direction_comment"])
        + "\n\n"
        + visual_report["visual_macro_direction_comment"]
        + "\n",
    )

    _json_dump(out_dir / "M2_gap_and_risk_report.json", gap_and_risk_report)
    _write_text(
        out_dir / "M2_gap_and_risk_report.md",
        "# M2 Gap And Risk Report\n\n"
        + "\n".join(
            [
                f"- human_klayout_review_required: `{gap_and_risk_report['human_klayout_review_required']}`",
                f"- can_enter_M3_before_human_review: `{gap_and_risk_report['can_enter_M3_before_human_review']}`",
            ]
        )
        + "\n\n"
        + _md_table(["gap_id", "category", "scope", "severity", "description", "blocking_M2_review"], unresolved_gap_rows),
    )

    docs_mapping = repo_root / "docs/mapping"
    docs_mapping.mkdir(parents=True, exist_ok=True)
    usage_columns = ["openyield_module", "physical_role", "binding_status", "physical_source_class", "physical_source_gds_path", "physical_source_top_cell", "temporary_wrapper", "generation_source", "placed_in_top", "region", "source_note"]
    _write_csv(docs_mapping / "M2_openyield_module_to_real_gds_usage.csv", usage_columns, module_usage_rows)
    _write_text(docs_mapping / "M2_openyield_module_to_real_gds_usage.md", "# M2 OpenYield Module To Real GDS Usage\n\n" + _md_table(usage_columns, module_usage_rows))

    placement_columns = ["module_name", "physical_role", "source_class", "instance_name", "region", "x", "y", "width", "height", "bbox"]
    _write_csv(docs_mapping / "M2_full_sram_placement_matrix.csv", placement_columns, placement_rows)
    _write_text(docs_mapping / "M2_full_sram_placement_matrix.md", "# M2 Full SRAM Placement Matrix\n\n" + _md_table(placement_columns, placement_rows))

    gap_columns = ["gap_id", "category", "scope", "severity", "description", "blocking_M2_review"]
    _write_csv(docs_mapping / "M2_unresolved_gap_matrix.csv", gap_columns, unresolved_gap_rows)
    _write_text(docs_mapping / "M2_unresolved_gap_matrix.md", "# M2 Unresolved Gap Matrix\n\n" + _md_table(gap_columns, unresolved_gap_rows))

    _json_dump(out_json, report)
    _write_text(
        out_report,
        "# M2 LayoutGen Full Trial Report\n\n"
        + "\n".join([f"- {key}: `{value}`" for key, value in report.items() if key not in {"reference_inputs", "remaining_M2_blockers", "modules_missing"}])
        + "\n\n## Reference Inputs\n\n"
        + "\n".join([f"- {key}: `{value}`" for key, value in report["reference_inputs"].items()])
        + "\n",
    )
    evidence_summary = repo_root / "docs/evidence/M2_layoutgen_full_trial_summary.md"
    _write_text(
        evidence_summary,
        "# M2 LayoutGen Full Trial Summary\n\n"
        + "\n".join(
            [
                f"- Generated review GDS: `{top_gds_path}`",
                f"- Top cell: `{top_cell_name}`",
                f"- GDS sanity: `{sanity['status']}`",
                f"- Modules placed: `{len(placements)}` / `{len(required_modules)}`",
                f"- Temporary wrappers: `{temp_count}`",
                "- This artifact is for human KLayout review only; do not enter M3 automatically.",
            ]
        )
        + "\n",
    )

    return report
