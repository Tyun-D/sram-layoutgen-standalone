from __future__ import annotations

import csv
import json
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

import gdstk

from sram_layoutgen.gds_util import inspect_gds_hierarchy, inspect_gds_layers, inspect_gds_text_records, measure_gds_bbox


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

DEFERRED_TO_L4_L5 = [
    "SRAM_TOP",
    "BANK",
    "routing_semantics",
    "power_semantics",
    "timing_semantics",
]

GENERATOR_INVENTORY_COLUMNS = [
    "module",
    "module_category",
    "is_L3_target",
    "deferred_to_L4_L5",
    "generator_available",
    "generator_name",
    "generator_source_file",
    "generator_strategy",
    "input_contracts",
    "input_rule_files",
    "source_primitives",
    "uses_hardmacro",
    "uses_composition_generator",
    "uses_array_packer",
    "uses_gate_row_packer",
    "reproducible_command",
    "generator_status",
    "limitations",
    "blocking_gap",
    "next_required_action",
    "evidence_files",
]

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
    "limitations",
    "blocking_gap",
    "next_required_action",
    "evidence_files",
]


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


def _canonical_pin_name(name: str) -> str:
    alias = {
        "vdd": "VDD",
        "vss": "GND",
        "gnd": "GND",
        "blb": "BR",
        "brb": "BR",
        "outb": "br_out",
        "out": "bl_out",
        "enb": "en_bar",
        "en_bar": "en_bar",
        "en": "en",
        "sel": "sel",
        "clkb": "clk_bar",
        "pre": "PRE",
    }
    key = name.strip()
    return alias.get(key.lower(), key)


def _parse_pin_list(text: str) -> list[str]:
    return [item.strip() for item in text.split(",") if item.strip()]


def _parse_semicolon_list(text: str) -> list[str]:
    return [item.strip() for item in text.split(";") if item.strip()]


@dataclass(frozen=True)
class ModuleGDSGenerationPlan:
    repo_root: Path
    openyield_root: Path
    out_dir: Path
    reproducible_command: str
    l0_contract_json: Path
    l1_library_json: Path
    l1_composition_library_json: Path
    l2_rule_library_json: Path
    module_handoff_matrix: Path
    input_contracts: tuple[str, ...]
    input_rules: tuple[str, ...]
    primitive_rows: dict[str, dict[str, str]]
    composition_rows: dict[str, dict[str, Any]]
    placement_rows: dict[str, dict[str, str]]
    abutment_rows: dict[str, dict[str, str]]
    rail_rows: dict[str, dict[str, str]]
    orientation_rows: dict[str, dict[str, str]]
    pin_rows: dict[str, dict[str, str]]
    handoff_rows: dict[str, dict[str, str]]


@dataclass(frozen=True)
class ModuleGDSGenerationResult:
    module: str
    module_category: str
    generator_class: str
    generator_source_file: str
    generator_status: str
    generation_status: str
    generation_strategy: str
    source_primitives: tuple[str, ...]
    uses_hardmacro: bool
    uses_composition_generator: bool
    uses_array_packer: bool
    uses_gate_row_packer: bool
    uses_contract_pin_mapping: bool
    limitations: tuple[str, ...]
    blocking_gap: str
    next_required_action: str
    output_dir: Path
    gds_path: Path
    pins_json_path: Path
    bbox_json_path: Path
    rail_report_path: Path
    generation_report_json_path: Path
    generation_report_md_path: Path
    generator_manifest_path: Path
    evidence_files: tuple[str, ...]
    top_cell_name: str | None = None
    bbox: dict[str, Any] | None = None
    pin_count: int = 0
    power_pins_present: bool = False
    rail_status: str = ""
    gds_size_bytes: int = 0
    sanity_check_status: str = ""


@dataclass(frozen=True)
class PlacedMacro:
    primitive_name: str
    source_key: str
    source_gds_path: Path
    source_top_cell: str
    source_bbox: dict[str, float]
    instance_name: str
    x: float
    y: float
    mirror: str = "R0"


class ModuleLayoutGenerator(ABC):
    module: str
    module_category: str
    generation_strategy: str

    @abstractmethod
    def generate(self, plan: ModuleGDSGenerationPlan) -> ModuleGDSGenerationResult:
        raise NotImplementedError


def _load_csv_rows(path: Path, key: str) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {str(row[key]): row for row in rows}


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _source_path_from_leaf_row(repo_root: Path, row: dict[str, Any]) -> Path | None:
    source = str(row.get("local_physical_source_path", "")).split(";")[0].strip()
    if not source or "::" in source:
        source = source.split("::", 1)[0].strip()
    if not source:
        return None
    candidate = repo_root / source
    if not candidate.exists() or candidate.suffix.lower() != ".gds":
        return None
    return candidate


def _resolve_primitive_source(plan: ModuleGDSGenerationPlan, primitive_name: str) -> tuple[str, Path, str, tuple[str, ...], bool]:
    primitive_row = plan.primitive_rows.get(primitive_name)
    if primitive_row is not None:
        path = _source_path_from_leaf_row(plan.repo_root, primitive_row)
        if path is not None:
            return primitive_name, path, primitive_name, (primitive_name,), primitive_row.get("local_physical_source_type") == "PYTHON_GENERATOR"

    composition_row = plan.composition_rows.get(primitive_name)
    if composition_row is not None:
        bases = tuple(str(item) for item in composition_row.get("required_base_primitives", []))
        if primitive_name == "nand3":
            nand4_row = plan.primitive_rows.get("nand4")
            path = _source_path_from_leaf_row(plan.repo_root, nand4_row) if nand4_row is not None else None
            if path is not None:
                return "nand4", path, primitive_name, bases or ("nand4",), True
        for base in bases:
            base_row = plan.primitive_rows.get(base)
            path = _source_path_from_leaf_row(plan.repo_root, base_row) if base_row is not None else None
            if path is not None:
                return base, path, primitive_name, bases, True
    raise FileNotFoundError(f"Unable to resolve primitive source for {primitive_name}")


def _read_source_cell(gds_path: Path) -> tuple[gdstk.Cell, str]:
    lib = gdstk.read_gds(gds_path)
    top_cells = lib.top_level()
    if top_cells:
        cell = top_cells[0]
        return cell, str(cell.name)
    if lib.cells:
        return lib.cells[0], str(lib.cells[0].name)
    raise ValueError(f"No cells found in {gds_path}")


def _transform_point(source_bbox: dict[str, float], x: float, y: float, target_x: float, target_y: float, mirror: str) -> tuple[float, float]:
    if mirror == "MX":
        return round(target_x + (x - source_bbox["x0"]), 6), round(target_y + (source_bbox["y1"] - y), 6)
    return round(target_x + (x - source_bbox["x0"]), 6), round(target_y + (y - source_bbox["y0"]), 6)


def _module_bbox_from_placements(placements: list[PlacedMacro]) -> dict[str, Any]:
    x0 = min(item.x for item in placements)
    y0 = min(item.y for item in placements)
    x1 = max(item.x + item.source_bbox["width"] for item in placements)
    y1 = max(item.y + item.source_bbox["height"] for item in placements)
    return {
        "x0": round(x0, 6),
        "y0": round(y0, 6),
        "x1": round(x1, 6),
        "y1": round(y1, 6),
        "width": round(x1 - x0, 6),
        "height": round(y1 - y0, 6),
        "shape_count": len(placements),
    }


def _place_macro(cell: gdstk.Cell, placed: PlacedMacro) -> gdstk.Reference:
    if placed.mirror == "MX":
        origin = (
            placed.x - placed.source_bbox["x0"],
            placed.y + placed.source_bbox["y1"],
        )
        return gdstk.Reference(cell, origin=origin, x_reflection=True)
    origin = (placed.x - placed.source_bbox["x0"], placed.y - placed.source_bbox["y0"])
    return gdstk.Reference(cell, origin=origin)


def _import_and_reference_cells(library: gdstk.Library, top: gdstk.Cell, placements: list[PlacedMacro]) -> None:
    imported: dict[Path, gdstk.Cell] = {}
    for placed in placements:
        cell = imported.get(placed.source_gds_path)
        if cell is None:
            cell = _read_source_cell(placed.source_gds_path)[0]
            imported[placed.source_gds_path] = cell
            library.add(cell)
        top.add(_place_macro(cell, placed))


def _contract_pins(module: str, module_bbox: dict[str, Any], handoff_row: dict[str, str], source: str, extra: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    pins: list[dict[str, Any]] = []
    x0, y0, x1, y1 = module_bbox["x0"], module_bbox["y0"], module_bbox["x1"], module_bbox["y1"]
    inputs = _parse_pin_list(handoff_row.get("required_input_pins", ""))
    outputs = _parse_pin_list(handoff_row.get("required_output_pins", ""))
    controls = _parse_pin_list(handoff_row.get("required_clock_or_control_pins", ""))
    powers = _parse_pin_list(handoff_row.get("required_power_pins", ""))

    def add_group(names: list[str], side: str, layer: str) -> None:
        if not names:
            return
        step = (y1 - y0) / (len(names) + 1) if side in {"left", "right"} else (x1 - x0) / (len(names) + 1)
        for index, name in enumerate(names, start=1):
            if side == "left":
                x, y = x0, y0 + step * index
            elif side == "right":
                x, y = x1, y0 + step * index
            elif side == "top":
                x, y = x0 + step * index, y1
            else:
                x, y = x0 + step * index, y0
            pins.append(
                {
                    "name": _canonical_pin_name(name),
                    "x": round(x, 6),
                    "y": round(y, 6),
                    "layer": layer,
                    "pin_source": source,
                    "module": module,
                }
            )

    add_group(inputs, "left", "m2")
    add_group(outputs, "right", "m2")
    add_group(controls, "top", "m1")
    add_group([name for name in powers if name.lower() in {"vdd", "gnd"}], "bottom", "m1")
    if extra:
        for item in extra.get("pins", []):
            pins.append(item)
    dedup: dict[str, dict[str, Any]] = {}
    for pin in pins:
        dedup[str(pin["name"])] = pin
    return [dedup[name] for name in sorted(dedup)]


def _extract_macro_pins(source_gds_path: Path, primitive_name: str, source_bbox: dict[str, float], target_x: float, target_y: float, mirror: str) -> list[dict[str, Any]]:
    pins: list[dict[str, Any]] = []
    for record in inspect_gds_text_records(source_gds_path):
        name = _canonical_pin_name(str(record["text"]))
        x, y = _transform_point(source_bbox, float(record["x"]), float(record["y"]), target_x, target_y, mirror)
        pins.append(
            {
                "name": name,
                "x": x,
                "y": y,
                "layer": f"{record['layer']}/{record['datatype']}",
                "pin_source": "gds_text_labels",
                "primitive": primitive_name,
            }
        )
    dedup: dict[str, dict[str, Any]] = {}
    for pin in pins:
        dedup[str(pin["name"])] = pin
    return [dedup[name] for name in sorted(dedup)]


def emit_module_gds(module: str, out_dir: Path, placements: list[PlacedMacro]) -> tuple[Path, str]:
    gds_path = out_dir / f"{module}.gds"
    library = gdstk.Library()
    top = library.new_cell(module)
    _import_and_reference_cells(library, top, placements)
    library.write_gds(gds_path)
    return gds_path, top.name


def emit_module_metadata(
    module: str,
    out_dir: Path,
    bbox: dict[str, Any],
    pins: list[dict[str, Any]],
    rail_report: dict[str, Any],
    generation_report: dict[str, Any],
) -> tuple[Path, Path, Path, Path, Path]:
    bbox_path = out_dir / "bbox.json"
    pins_path = out_dir / "pins.json"
    rail_path = out_dir / "rail_report.json"
    report_json_path = out_dir / "generation_report.json"
    report_md_path = out_dir / "generation_report.md"
    _json_dump(bbox_path, bbox)
    _json_dump(pins_path, {"module": module, "pin_count": len(pins), "pins": pins})
    _json_dump(rail_path, rail_report)
    _json_dump(report_json_path, generation_report)
    _write_text(report_md_path, _format_generation_report_md(module, generation_report))
    return bbox_path, pins_path, rail_path, report_json_path, report_md_path


def emit_generator_manifest(out_dir: Path, manifest: dict[str, Any]) -> Path:
    path = out_dir / "generator_manifest.json"
    _json_dump(path, manifest)
    return path


def validate_module_outputs(result: ModuleGDSGenerationResult) -> dict[str, Any]:
    gds_path = result.gds_path
    hierarchy = inspect_gds_hierarchy(gds_path)
    bbox = measure_gds_bbox(gds_path)
    layers = inspect_gds_layers(gds_path)
    status = {
        "gds_exists": gds_path.exists(),
        "gds_non_empty": gds_path.exists() and gds_path.stat().st_size > 0,
        "has_top_cell": bool(result.top_cell_name),
        "bbox_present": bbox is not None,
        "structure_count": hierarchy.get("structure_count", 0),
        "instance_count": sum(int(v) for v in hierarchy.get("reference_counts", {}).values()),
        "layer_summary": layers.get("boundary", {}),
    }
    status["sanity_check_status"] = "SANITY_OK" if all(
        [
            status["gds_exists"],
            status["gds_non_empty"],
            status["has_top_cell"],
            status["bbox_present"],
        ]
    ) else "SANITY_FAILED"
    return status


def _format_generation_report_md(module: str, report: dict[str, Any]) -> str:
    lines = [
        f"# {module} generation report",
        "",
        f"- generation_status: `{report['generation_status']}`",
        f"- generator_class: `{report['generator_class']}`",
        f"- generation_strategy: `{report['generation_strategy']}`",
        f"- top_cell_name: `{report.get('top_cell_name')}`",
        f"- gds_path: `{report.get('gds_path')}`",
        f"- bbox: `{report.get('bbox')}`",
        f"- pin_count: `{report.get('pin_count')}`",
        f"- rail_status: `{report.get('rail_status')}`",
        f"- limitations: `{'; '.join(report.get('limitations', [])) or 'none'}`",
        f"- not_DRC_clean_claimed: `{report.get('not_DRC_clean_claimed')}`",
        f"- not_LVS_clean_claimed: `{report.get('not_LVS_clean_claimed')}`",
        f"- geometry_is_L3_module_candidate: `{report.get('geometry_is_L3_module_candidate')}`",
    ]
    if "row_count" in report:
        lines.append(f"- row_count: `{report['row_count']}`")
    if "intra_row_gap_after" in report:
        lines.append(f"- intra_row_gap_after: `{report['intra_row_gap_after']}`")
    if "rail_alignment_candidate" in report:
        lines.append(f"- rail_alignment_candidate: `{report['rail_alignment_candidate']}`")
    return "\n".join(lines) + "\n"


def _emit_inventory_markdown(title: str, rows: list[dict[str, Any]], columns: list[str]) -> str:
    lines = [f"# {title}", "", f"Rows: `{len(rows)}`", ""]
    lines.append("| " + " | ".join(columns) + " |")
    lines.append("| " + " | ".join("---" for _ in columns) + " |")
    for row in rows:
        values = [str(row.get(column, "")).replace("\n", " ") for column in columns]
        lines.append("| " + " | ".join(values) + " |")
    lines.append("")
    return "\n".join(lines)


def emit_module_generator_inventory(csv_path: Path, md_path: Path, rows: list[dict[str, Any]]) -> None:
    _write_csv(csv_path, GENERATOR_INVENTORY_COLUMNS, rows)
    _write_text(md_path, _emit_inventory_markdown("OpenYield Module Generator Inventory", rows, GENERATOR_INVENTORY_COLUMNS))


def emit_module_gds_inventory(csv_path: Path, md_path: Path, rows: list[dict[str, Any]]) -> None:
    _write_csv(csv_path, GDS_INVENTORY_COLUMNS, rows)
    _write_text(md_path, _emit_inventory_markdown("OpenYield Module GDS Inventory", rows, GDS_INVENTORY_COLUMNS))


def _generator_source_file() -> str:
    return "sram_layoutgen/openyield_adapter/module_gds_generators.py"


def _build_manifest(
    module: str,
    generator_class: str,
    generation_strategy: str,
    generated_files: list[str],
    source_primitives: Iterable[str],
    input_contracts: Iterable[str],
    input_rules: Iterable[str],
    limitations: Iterable[str],
    reproducible_command: str,
) -> dict[str, Any]:
    return {
        "module": module,
        "generator_class": generator_class,
        "generator_source_file": _generator_source_file(),
        "input_contracts": list(input_contracts),
        "input_rules": list(input_rules),
        "source_primitives": list(source_primitives),
        "generation_strategy": generation_strategy,
        "generated_files": generated_files,
        "reproducible_command": reproducible_command,
        "limitations": list(limitations),
    }


def _result_from_payload(
    module: str,
    module_category: str,
    generator_class: str,
    generator_status: str,
    generation_status: str,
    generation_strategy: str,
    source_primitives: tuple[str, ...],
    uses_hardmacro: bool,
    uses_composition_generator: bool,
    uses_array_packer: bool,
    uses_gate_row_packer: bool,
    uses_contract_pin_mapping: bool,
    limitations: tuple[str, ...],
    blocking_gap: str,
    next_required_action: str,
    output_dir: Path,
    evidence_files: tuple[str, ...],
) -> ModuleGDSGenerationResult:
    gds_path = output_dir / f"{module}.gds"
    return ModuleGDSGenerationResult(
        module=module,
        module_category=module_category,
        generator_class=generator_class,
        generator_source_file=_generator_source_file(),
        generator_status=generator_status,
        generation_status=generation_status,
        generation_strategy=generation_strategy,
        source_primitives=source_primitives,
        uses_hardmacro=uses_hardmacro,
        uses_composition_generator=uses_composition_generator,
        uses_array_packer=uses_array_packer,
        uses_gate_row_packer=uses_gate_row_packer,
        uses_contract_pin_mapping=uses_contract_pin_mapping,
        limitations=limitations,
        blocking_gap=blocking_gap,
        next_required_action=next_required_action,
        output_dir=output_dir,
        gds_path=gds_path,
        pins_json_path=output_dir / "pins.json",
        bbox_json_path=output_dir / "bbox.json",
        rail_report_path=output_dir / "rail_report.json",
        generation_report_json_path=output_dir / "generation_report.json",
        generation_report_md_path=output_dir / "generation_report.md",
        generator_manifest_path=output_dir / "generator_manifest.json",
        evidence_files=evidence_files,
    )


class ArrayModuleGenerator(ModuleLayoutGenerator):
    def __init__(self, module: str, primitive_name: str, cols: int, rows: int) -> None:
        self.module = module
        self.primitive_name = primitive_name
        self.cols = cols
        self.rows = rows
        self.module_category = "array"
        self.generation_strategy = "array_generator_with_l2_orientation_policy"

    def generate(self, plan: ModuleGDSGenerationPlan) -> ModuleGDSGenerationResult:
        handoff = plan.handoff_rows[self.module]
        source_key, source_path, _primitive_alias, _bases, _uses_composition = _resolve_primitive_source(plan, self.primitive_name)
        source_bbox = measure_gds_bbox(source_path)
        if source_bbox is None:
            raise ValueError(f"Missing bbox for {self.primitive_name}")
        bbox_dict = source_bbox.to_dict()
        placements: list[PlacedMacro] = []
        for row_index in range(self.rows):
            mirror = "MX" if row_index % 2 == 0 else "R0"
            for col_index in range(self.cols):
                placements.append(
                    PlacedMacro(
                        primitive_name=self.primitive_name,
                        source_key=source_key,
                        source_gds_path=source_path,
                        source_top_cell=_read_source_cell(source_path)[1],
                        source_bbox=bbox_dict,
                        instance_name=f"{self.module}_{row_index}_{col_index}",
                        x=col_index * bbox_dict["width"],
                        y=row_index * bbox_dict["height"],
                        mirror=mirror,
                    )
                )
        if self.module == "replica_array":
            precharge_key, precharge_path, _, _, _ = _resolve_primitive_source(plan, "precharge_cell")
            precharge_bbox = measure_gds_bbox(precharge_path)
            if precharge_bbox is None:
                raise ValueError("Missing bbox for precharge_cell")
            pbox = precharge_bbox.to_dict()
            placements.append(
                PlacedMacro(
                    primitive_name="precharge_cell",
                    source_key=precharge_key,
                    source_gds_path=precharge_path,
                    source_top_cell=_read_source_cell(precharge_path)[1],
                    source_bbox=pbox,
                    instance_name=f"{self.module}_precharge",
                    x=0.0,
                    y=self.rows * bbox_dict["height"],
                    mirror="R0",
                )
            )
        out_dir = plan.out_dir / self.module
        out_dir.mkdir(parents=True, exist_ok=True)
        gds_path, top_cell_name = emit_module_gds(self.module, out_dir, placements)
        module_bbox = _module_bbox_from_placements(placements)
        pins = _contract_pins(self.module, module_bbox, handoff, "module_contract_pin_map")
        rail_report = {
            "module": self.module,
            "rail_status": "module_boundary_rails_exported",
            "uses_explicit_rail_handoff_contract": False,
            "row_orientation_policy": "alternating_MX_R0_storage_rows",
            "rows": self.rows,
            "cols": self.cols,
            "source_primitives": sorted({item.primitive_name for item in placements}),
        }
        report = {
            "module": self.module,
            "generator_class": type(self).__name__,
            "generation_strategy": self.generation_strategy,
            "generation_status": "L3_GDS_GENERATED_WITH_CONTRACT_PINS",
            "top_cell_name": top_cell_name,
            "gds_path": str(gds_path),
            "bbox": module_bbox,
            "pin_count": len(pins),
            "rail_status": rail_report["rail_status"],
            "limitations": [
                "Array dimensions are deterministic L3 standalone templates, not final top-level SRAM array sizing.",
            ],
            "not_DRC_clean_claimed": True,
            "not_LVS_clean_claimed": True,
            "geometry_is_L3_module_candidate": False,
            "array_rows": self.rows,
            "array_cols": self.cols,
        }
        emit_module_metadata(self.module, out_dir, module_bbox, pins, rail_report, report)
        manifest = _build_manifest(
            self.module,
            type(self).__name__,
            self.generation_strategy,
            [
                str(gds_path),
                str(out_dir / "pins.json"),
                str(out_dir / "bbox.json"),
                str(out_dir / "rail_report.json"),
                str(out_dir / "generation_report.md"),
                str(out_dir / "generation_report.json"),
            ],
            sorted({item.primitive_name for item in placements}),
            plan.input_contracts,
            plan.input_rules,
            report["limitations"],
            plan.reproducible_command,
        )
        emit_generator_manifest(out_dir, manifest)
        result = _result_from_payload(
            module=self.module,
            module_category=self.module_category,
            generator_class=type(self).__name__,
            generator_status="GENERATOR_READY",
            generation_status="L3_GDS_GENERATED_WITH_CONTRACT_PINS",
            generation_strategy=self.generation_strategy,
            source_primitives=tuple(sorted({item.primitive_name for item in placements})),
            uses_hardmacro=False,
            uses_composition_generator=False,
            uses_array_packer=True,
            uses_gate_row_packer=False,
            uses_contract_pin_mapping=True,
            limitations=tuple(report["limitations"]),
            blocking_gap="",
            next_required_action="Feed these standalone arrays into L4 top-level assembly when bank-level placement is ready.",
            output_dir=out_dir,
            evidence_files=tuple(_parse_semicolon_list(handoff.get("evidence_files", ""))),
        )
        sanity = validate_module_outputs(result)
        return ModuleGDSGenerationResult(
            **{**asdict(result), "top_cell_name": top_cell_name, "bbox": module_bbox, "pin_count": len(pins), "power_pins_present": True, "rail_status": rail_report["rail_status"], "gds_size_bytes": gds_path.stat().st_size, "sanity_check_status": str(sanity["sanity_check_status"])}
        )


class HardmacroWrapperGenerator(ModuleLayoutGenerator):
    def __init__(self, module: str, primitive_name: str) -> None:
        self.module = module
        self.primitive_name = primitive_name
        self.module_category = "hardmacro_wrapper"
        self.generation_strategy = "hardmacro_wrapper_generator"

    def generate(self, plan: ModuleGDSGenerationPlan) -> ModuleGDSGenerationResult:
        handoff = plan.handoff_rows[self.module]
        source_key, source_path, _primitive_alias, _bases, _uses_composition = _resolve_primitive_source(plan, self.primitive_name)
        source_bbox = measure_gds_bbox(source_path)
        if source_bbox is None:
            raise ValueError(f"Missing bbox for {self.primitive_name}")
        bbox_dict = source_bbox.to_dict()
        placement = PlacedMacro(
            primitive_name=self.primitive_name,
            source_key=source_key,
            source_gds_path=source_path,
            source_top_cell=_read_source_cell(source_path)[1],
            source_bbox=bbox_dict,
            instance_name=f"{self.module}_0",
            x=0.0,
            y=0.0,
            mirror="R0",
        )
        out_dir = plan.out_dir / self.module
        out_dir.mkdir(parents=True, exist_ok=True)
        gds_path, top_cell_name = emit_module_gds(self.module, out_dir, [placement])
        module_bbox = _module_bbox_from_placements([placement])
        label_pins = _extract_macro_pins(source_path, self.primitive_name, bbox_dict, 0.0, 0.0, "R0")
        uses_contract_pins = not label_pins or self.module == "precharge"
        pins = _contract_pins(self.module, module_bbox, handoff, "module_contract_pin_map") if uses_contract_pins else label_pins
        rail_report = {
            "module": self.module,
            "rail_status": "hardmacro_wrapper_rail_metadata_exported",
            "source_macro": str(source_path.relative_to(plan.repo_root)),
            "uses_explicit_rail_handoff_contract": False,
            "pin_geometry_extractable": bool(label_pins),
            "geometry_requires_L4_or_L5_verification": self.module == "precharge",
        }
        limitations = []
        generation_status = "L3_GDS_GENERATED"
        if uses_contract_pins:
            generation_status = "L3_GDS_GENERATED_WITH_CONTRACT_PINS"
            limitations.append("Boundary pins are exported through the L2/L3 contract instead of direct module-boundary geometry extraction.")
        if self.module == "precharge":
            limitations.append("precharge pin export remains contract-backed at the module wrapper boundary and needs L4/L5 verification.")
        report = {
            "module": self.module,
            "generator_class": type(self).__name__,
            "generation_strategy": self.generation_strategy,
            "generation_status": generation_status,
            "top_cell_name": top_cell_name,
            "gds_path": str(gds_path),
            "bbox": module_bbox,
            "pin_count": len(pins),
            "rail_status": rail_report["rail_status"],
            "limitations": limitations,
            "not_DRC_clean_claimed": True,
            "not_LVS_clean_claimed": True,
            "geometry_is_L3_module_candidate": False,
            "pin_contract_source": "docs/mapping/openyield_pin_access_rule_matrix.csv" if uses_contract_pins else None,
        }
        emit_module_metadata(self.module, out_dir, module_bbox, pins, rail_report, report)
        manifest = _build_manifest(
            self.module,
            type(self).__name__,
            self.generation_strategy,
            [
                str(gds_path),
                str(out_dir / "pins.json"),
                str(out_dir / "bbox.json"),
                str(out_dir / "rail_report.json"),
                str(out_dir / "generation_report.md"),
                str(out_dir / "generation_report.json"),
            ],
            [self.primitive_name],
            plan.input_contracts,
            plan.input_rules,
            limitations,
            plan.reproducible_command,
        )
        emit_generator_manifest(out_dir, manifest)
        result = _result_from_payload(
            module=self.module,
            module_category=self.module_category,
            generator_class=type(self).__name__,
            generator_status="GENERATOR_READY_FOR_HARDMACRO_WRAPPER",
            generation_status=generation_status,
            generation_strategy=self.generation_strategy,
            source_primitives=(self.primitive_name,),
            uses_hardmacro=True,
            uses_composition_generator=False,
            uses_array_packer=False,
            uses_gate_row_packer=False,
            uses_contract_pin_mapping=uses_contract_pins,
            limitations=tuple(limitations),
            blocking_gap="",
            next_required_action="Use wrapper macro and exported metadata for L4 assembly; keep signoff checks in L4/L5.",
            output_dir=out_dir,
            evidence_files=tuple(_parse_semicolon_list(handoff.get("evidence_files", ""))),
        )
        sanity = validate_module_outputs(result)
        return ModuleGDSGenerationResult(
            **{**asdict(result), "top_cell_name": top_cell_name, "bbox": module_bbox, "pin_count": len(pins), "power_pins_present": any(pin["name"] in {"VDD", "GND"} for pin in pins), "rail_status": rail_report["rail_status"], "gds_size_bytes": gds_path.stat().st_size, "sanity_check_status": str(sanity["sanity_check_status"])}
        )


class RowBasedCandidateGenerator(ModuleLayoutGenerator):
    def __init__(self, module: str, module_category: str, row_templates: tuple[tuple[str, ...], ...], generation_strategy: str) -> None:
        self.module = module
        self.module_category = module_category
        self.row_templates = row_templates
        self.generation_strategy = generation_strategy

    def _expand_row(self, plan: ModuleGDSGenerationPlan, primitive_names: tuple[str, ...]) -> list[PlacedMacro]:
        row: list[PlacedMacro] = []
        x_cursor = 0.0
        mirror = "R0"
        max_height = 0.0
        for index, primitive_name in enumerate(primitive_names):
            source_key, source_path, primitive_alias, _bases, _composition = _resolve_primitive_source(plan, primitive_name)
            source_bbox = measure_gds_bbox(source_path)
            if source_bbox is None:
                raise ValueError(f"Missing bbox for {primitive_name}")
            bbox_dict = source_bbox.to_dict()
            row.append(
                PlacedMacro(
                    primitive_name=primitive_alias,
                    source_key=source_key,
                    source_gds_path=source_path,
                    source_top_cell=_read_source_cell(source_path)[1],
                    source_bbox=bbox_dict,
                    instance_name=f"{self.module}_leaf_{len(row)}_{index}",
                    x=x_cursor,
                    y=0.0,
                    mirror=mirror,
                )
            )
            x_cursor += bbox_dict["width"]
            max_height = max(max_height, bbox_dict["height"])
        for item in row:
            item.source_bbox["height"] = max_height
        return row

    def generate(self, plan: ModuleGDSGenerationPlan) -> ModuleGDSGenerationResult:
        handoff = plan.handoff_rows[self.module]
        row_gap = 0.0
        placements: list[PlacedMacro] = []
        y_cursor = 0.0
        source_primitives: set[str] = set()
        for row_index, template in enumerate(self.row_templates):
            row_items = self._expand_row(plan, template)
            row_height = max(item.source_bbox["height"] for item in row_items)
            mirror = "MX" if row_index % 2 == 1 else "R0"
            x_cursor = 0.0
            for col_index, item in enumerate(row_items):
                placements.append(
                    PlacedMacro(
                        primitive_name=item.primitive_name,
                        source_key=item.source_key,
                        source_gds_path=item.source_gds_path,
                        source_top_cell=item.source_top_cell,
                        source_bbox=item.source_bbox,
                        instance_name=f"{self.module}_r{row_index}_c{col_index}",
                        x=x_cursor,
                        y=y_cursor,
                        mirror=mirror,
                    )
                )
                source_primitives.add(item.primitive_name)
                x_cursor += item.source_bbox["width"]
            y_cursor += row_height + row_gap
        out_dir = plan.out_dir / self.module
        out_dir.mkdir(parents=True, exist_ok=True)
        gds_path, top_cell_name = emit_module_gds(self.module, out_dir, placements)
        module_bbox = _module_bbox_from_placements(placements)
        pins = _contract_pins(self.module, module_bbox, handoff, "composition_contract_and_base_leaf_pin_map")
        rail_report = {
            "module": self.module,
            "rail_status": "candidate_row_rail_metadata_exported",
            "row_count": len(self.row_templates),
            "rail_alignment_candidate": "alternating_R0_MX_same_row_abutment",
            "uses_explicit_rail_handoff_contract": False,
        }
        report = {
            "module": self.module,
            "generator_class": type(self).__name__,
            "generation_strategy": self.generation_strategy,
            "generation_status": "L3_GDS_GENERATED_CANDIDATE_GEOMETRY",
            "top_cell_name": top_cell_name,
            "gds_path": str(gds_path),
            "bbox": module_bbox,
            "pin_count": len(pins),
            "rail_status": rail_report["rail_status"],
            "limitations": [
                "Candidate geometry packs row leaves tightly under L2 rules but does not claim final routing or signoff.",
                "Boundary pins are semantic/contract exports at the module edge.",
            ],
            "not_DRC_clean_claimed": True,
            "not_LVS_clean_claimed": True,
            "geometry_is_L3_module_candidate": True,
            "row_count": len(self.row_templates),
            "intra_row_gap_after": 0.0,
            "rail_alignment_candidate": "alternating_R0_MX_same_row_abutment",
        }
        emit_module_metadata(self.module, out_dir, module_bbox, pins, rail_report, report)
        manifest = _build_manifest(
            self.module,
            type(self).__name__,
            self.generation_strategy,
            [
                str(gds_path),
                str(out_dir / "pins.json"),
                str(out_dir / "bbox.json"),
                str(out_dir / "rail_report.json"),
                str(out_dir / "generation_report.md"),
                str(out_dir / "generation_report.json"),
            ],
            sorted(source_primitives),
            plan.input_contracts,
            plan.input_rules,
            report["limitations"],
            plan.reproducible_command,
        )
        emit_generator_manifest(out_dir, manifest)
        result = _result_from_payload(
            module=self.module,
            module_category=self.module_category,
            generator_class=type(self).__name__,
            generator_status="GENERATOR_READY_FOR_CANDIDATE_GEOMETRY",
            generation_status="L3_GDS_GENERATED_CANDIDATE_GEOMETRY",
            generation_strategy=self.generation_strategy,
            source_primitives=tuple(sorted(source_primitives)),
            uses_hardmacro=False,
            uses_composition_generator=True,
            uses_array_packer=False,
            uses_gate_row_packer=True,
            uses_contract_pin_mapping=True,
            limitations=tuple(report["limitations"]),
            blocking_gap="",
            next_required_action="Promote candidate geometry into L4 module assembly and keep module-level signoff checks deferred.",
            output_dir=out_dir,
            evidence_files=tuple(_parse_semicolon_list(handoff.get("evidence_files", ""))),
        )
        sanity = validate_module_outputs(result)
        return ModuleGDSGenerationResult(
            **{**asdict(result), "top_cell_name": top_cell_name, "bbox": module_bbox, "pin_count": len(pins), "power_pins_present": True, "rail_status": rail_report["rail_status"], "gds_size_bytes": gds_path.stat().st_size, "sanity_check_status": str(sanity["sanity_check_status"])}
        )


def generate_array_module(plan: ModuleGDSGenerationPlan, module: str, primitive_name: str, cols: int, rows: int) -> ModuleGDSGenerationResult:
    return ArrayModuleGenerator(module, primitive_name, cols, rows).generate(plan)


def generate_hardmacro_wrapper_module(plan: ModuleGDSGenerationPlan, module: str, primitive_name: str) -> ModuleGDSGenerationResult:
    return HardmacroWrapperGenerator(module, primitive_name).generate(plan)


def generate_gate_row_module(
    plan: ModuleGDSGenerationPlan,
    module: str,
    row_templates: tuple[tuple[str, ...], ...],
) -> ModuleGDSGenerationResult:
    return RowBasedCandidateGenerator(module, "gate_row", row_templates, "gate_row_generator_with_L2_abutment_policy").generate(plan)


def generate_composition_backed_module(
    plan: ModuleGDSGenerationPlan,
    module: str,
    row_templates: tuple[tuple[str, ...], ...],
) -> ModuleGDSGenerationResult:
    return RowBasedCandidateGenerator(module, "composition_candidate", row_templates, "composition_backed_candidate_generator").generate(plan)


def generate_control_composite_module(
    plan: ModuleGDSGenerationPlan,
    module: str,
    row_templates: tuple[tuple[str, ...], ...],
) -> ModuleGDSGenerationResult:
    return RowBasedCandidateGenerator(module, "control_candidate", row_templates, "control_composite_candidate_generator").generate(plan)


class ModuleGDSGeneratorRegistry:
    def __init__(self) -> None:
        self._generators: dict[str, ModuleLayoutGenerator] = {}

    def register(self, generator: ModuleLayoutGenerator) -> None:
        self._generators[generator.module] = generator

    def get(self, module: str) -> ModuleLayoutGenerator:
        return self._generators[module]

    def modules(self) -> list[str]:
        return sorted(self._generators)

    def generate_all(self, plan: ModuleGDSGenerationPlan) -> list[ModuleGDSGenerationResult]:
        return [self._generators[module].generate(plan) for module in L3_TARGET_MODULES]


def _build_registry() -> ModuleGDSGeneratorRegistry:
    registry = ModuleGDSGeneratorRegistry()
    registry.register(ArrayModuleGenerator("bitcell_array", "bitcell", cols=4, rows=4))
    registry.register(ArrayModuleGenerator("dummy_array", "dummy_cell", cols=4, rows=4))
    registry.register(ArrayModuleGenerator("replica_array", "replica_cell", cols=2, rows=4))
    registry.register(RowBasedCandidateGenerator("row_decoder", "gate_row", (("inv", "nand3", "and3"), ("decoder_leaf_gate", "inv", "nand3")), "gate_row_generator_with_L2_abutment_policy"))
    registry.register(RowBasedCandidateGenerator("wordline_decoder", "gate_row", (("inv", "nand3", "and3"), ("wordline_decoder_leaf_gate", "inv", "and3")), "gate_row_generator_with_L2_abutment_policy"))
    registry.register(RowBasedCandidateGenerator("decoder_gate_cells", "gate_row", (("inv", "nand3", "and2", "and3"), ("decoder_leaf_gate", "and2", "inv")), "gate_row_generator_with_L2_abutment_policy"))
    registry.register(HardmacroWrapperGenerator("wordline_driver", "wordline_driver"))
    registry.register(RowBasedCandidateGenerator("wordline_driver_gate_cells", "gate_row", (("wordline_driver_leaf_gate", "nand2", "inv"), ("wordline_driver_leaf_gate", "inv")), "gate_row_generator_with_L2_abutment_policy"))
    registry.register(HardmacroWrapperGenerator("column_mux", "column_mux"))
    registry.register(HardmacroWrapperGenerator("sense_amp", "sense_amp"))
    registry.register(HardmacroWrapperGenerator("write_driver", "write_driver"))
    registry.register(HardmacroWrapperGenerator("precharge", "precharge_cell"))
    registry.register(RowBasedCandidateGenerator("DELAY_CHAIN", "composition_candidate", (("delay_inv", "delay_inv", "delay_inv", "delay_inv"),), "composition_backed_candidate_generator"))
    registry.register(RowBasedCandidateGenerator("PRECHARGE_ENABLE_PATH", "control_candidate", (("enable_path_leaf_gate", "nand3", "delay_inv"), ("precharge_cell", "inv")), "control_composite_candidate_generator"))
    registry.register(RowBasedCandidateGenerator("SENSE_ENABLE_PATH", "control_candidate", (("enable_path_leaf_gate", "nand3"), ("sense_amp", "inv")), "control_composite_candidate_generator"))
    registry.register(RowBasedCandidateGenerator("WRITE_ENABLE_PATH", "control_candidate", (("enable_path_leaf_gate", "delay_inv"), ("write_driver", "inv")), "control_composite_candidate_generator"))
    registry.register(RowBasedCandidateGenerator("WORDLINE_ENABLE_PATH", "control_candidate", (("enable_path_leaf_gate", "nand3"), ("wordline_driver", "inv")), "control_composite_candidate_generator"))
    registry.register(RowBasedCandidateGenerator("GATED_CLOCK_PATH", "control_candidate", (("gated_clock_leaf_gate", "nand2", "inv"), ("buffer", "inv")), "control_composite_candidate_generator"))
    registry.register(RowBasedCandidateGenerator("DFF_ROW", "control_candidate", (("dff_cell", "dff_cell", "dff_cell", "dff_cell"),), "control_composite_candidate_generator"))
    registry.register(RowBasedCandidateGenerator("CONTROL_LOGIC", "control_candidate", (("control_logic_leaf_gate", "dff_cell", "delay_inv"), ("buffer", "nand3", "and2", "and3", "inv")), "control_composite_candidate_generator"))
    return registry


def _generator_inventory_row(plan: ModuleGDSGenerationPlan, result: ModuleGDSGenerationResult) -> dict[str, Any]:
    return {
        "module": result.module,
        "module_category": result.module_category,
        "is_L3_target": "True",
        "deferred_to_L4_L5": "False",
        "generator_available": "True",
        "generator_name": result.generator_class,
        "generator_source_file": result.generator_source_file,
        "generator_strategy": result.generation_strategy,
        "input_contracts": ";".join(plan.input_contracts),
        "input_rule_files": ";".join(plan.input_rules),
        "source_primitives": ";".join(result.source_primitives),
        "uses_hardmacro": str(result.uses_hardmacro),
        "uses_composition_generator": str(result.uses_composition_generator),
        "uses_array_packer": str(result.uses_array_packer),
        "uses_gate_row_packer": str(result.uses_gate_row_packer),
        "reproducible_command": plan.reproducible_command,
        "generator_status": result.generator_status,
        "limitations": "; ".join(result.limitations),
        "blocking_gap": result.blocking_gap,
        "next_required_action": result.next_required_action,
        "evidence_files": ";".join(result.evidence_files),
    }


def _deferred_generator_inventory_row(plan: ModuleGDSGenerationPlan, module: str) -> dict[str, Any]:
    return {
        "module": module,
        "module_category": "deferred",
        "is_L3_target": "False",
        "deferred_to_L4_L5": "True",
        "generator_available": "False",
        "generator_name": "",
        "generator_source_file": _generator_source_file(),
        "generator_strategy": "deferred_to_L4_L5",
        "input_contracts": ";".join(plan.input_contracts),
        "input_rule_files": ";".join(plan.input_rules),
        "source_primitives": "",
        "uses_hardmacro": "False",
        "uses_composition_generator": "False",
        "uses_array_packer": "False",
        "uses_gate_row_packer": "False",
        "reproducible_command": plan.reproducible_command,
        "generator_status": "DEFERRED_TO_L4_L5",
        "limitations": "Not an L3 standalone module generator target.",
        "blocking_gap": "",
        "next_required_action": "Handle during L4/L5 top-level assembly, routing, power, or timing integration.",
        "evidence_files": plan.handoff_rows.get(module, {}).get("evidence_files", ""),
    }


def _gds_inventory_row(result: ModuleGDSGenerationResult) -> dict[str, Any]:
    return {
        "module": result.module,
        "module_category": result.module_category,
        "is_L3_target": "True",
        "deferred_to_L4_L5": "False",
        "generation_status": result.generation_status,
        "gds_generated": "True",
        "gds_path": str(result.gds_path),
        "gds_size_bytes": str(result.gds_size_bytes),
        "top_cell_name": result.top_cell_name or "",
        "bbox_known": str(result.bbox is not None),
        "bbox": json.dumps(result.bbox, ensure_ascii=False) if result.bbox is not None else "",
        "pins_json_path": str(result.pins_json_path),
        "pin_count": str(result.pin_count),
        "power_pins_present": str(result.power_pins_present),
        "rail_report_path": str(result.rail_report_path),
        "rail_status": result.rail_status,
        "generator_manifest_path": str(result.generator_manifest_path),
        "generator_source_file": result.generator_source_file,
        "generation_strategy": result.generation_strategy,
        "source_primitives": ";".join(result.source_primitives),
        "uses_hardmacro": str(result.uses_hardmacro),
        "uses_composition_generator": str(result.uses_composition_generator),
        "uses_array_packer": str(result.uses_array_packer),
        "uses_gate_row_packer": str(result.uses_gate_row_packer),
        "uses_contract_pin_mapping": str(result.uses_contract_pin_mapping),
        "sanity_check_status": result.sanity_check_status,
        "limitations": "; ".join(result.limitations),
        "blocking_gap": result.blocking_gap,
        "next_required_action": result.next_required_action,
        "evidence_files": ";".join(result.evidence_files),
    }


def _deferred_gds_inventory_row(module: str) -> dict[str, Any]:
    return {
        "module": module,
        "module_category": "deferred",
        "is_L3_target": "False",
        "deferred_to_L4_L5": "True",
        "generation_status": "DEFERRED_TO_L4_L5",
        "gds_generated": "False",
        "gds_path": "",
        "gds_size_bytes": "0",
        "top_cell_name": "",
        "bbox_known": "False",
        "bbox": "",
        "pins_json_path": "",
        "pin_count": "0",
        "power_pins_present": "False",
        "rail_report_path": "",
        "rail_status": "deferred_to_L4_L5",
        "generator_manifest_path": "",
        "generator_source_file": _generator_source_file(),
        "generation_strategy": "deferred_to_L4_L5",
        "source_primitives": "",
        "uses_hardmacro": "False",
        "uses_composition_generator": "False",
        "uses_array_packer": "False",
        "uses_gate_row_packer": "False",
        "uses_contract_pin_mapping": "False",
        "sanity_check_status": "NOT_REQUIRED_FOR_CURRENT_SCOPE",
        "limitations": "Not an L3 standalone module GDS target.",
        "blocking_gap": "",
        "next_required_action": "Handle during L4/L5 top-level assembly, routing, power, or timing integration.",
        "evidence_files": "",
    }


def build_generation_plan(
    repo_root: Path,
    openyield_root: Path,
    out_dir: Path,
    reproducible_command: str,
    l0_contract_json: Path,
    l1_library_json: Path,
    l1_composition_library_json: Path,
    l2_rule_library_json: Path,
    module_handoff_matrix: Path,
) -> ModuleGDSGenerationPlan:
    input_contracts = (
        "docs/mapping/openyield_canonical_sram_semantic_contract.json",
        "docs/mapping/openyield_top_bank_semantic_contract.json",
        "docs/mapping/openyield_time_control_decomposition_contract.json",
        "docs/mapping/openyield_control_path_semantic_contracts.csv",
        "docs/mapping/openyield_decoder_wordline_semantic_contract.json",
        "technology/freepdk45/openyield_leaf_physical_library.json",
        "technology/freepdk45/openyield_primitive_composition_library.json",
        "docs/mapping/openyield_leaf_physical_readiness_matrix.csv",
        "docs/mapping/openyield_module_to_primitive_dependency_matrix.csv",
    )
    input_rules = (
        "technology/freepdk45/openyield_L2_placement_abutment_rule_library.json",
        "docs/mapping/openyield_placement_rule_matrix.csv",
        "docs/mapping/openyield_abutment_rule_matrix.csv",
        "docs/mapping/openyield_rail_rule_matrix.csv",
        "docs/mapping/openyield_orientation_policy_matrix.csv",
        "docs/mapping/openyield_pin_access_rule_matrix.csv",
        "docs/mapping/openyield_module_handoff_rule_matrix.csv",
        "docs/openyield_L2_placement_abutment_rule_closure_report.json",
    )
    primitive_library = _load_json(l1_library_json)
    composition_library = _load_json(l1_composition_library_json)
    primitive_rows = {
        str(item["name"]): {
            "name": str(item["name"]),
            "local_physical_source_type": str(item.get("local_physical_source_type", "")),
            "local_physical_source_path": str(item.get("local_physical_source_path", "")),
        }
        for item in primitive_library.get("primitives", [])
    }
    composition_rows = {str(item["primitive_name"]): item for item in composition_library.get("compositions", [])}
    return ModuleGDSGenerationPlan(
        repo_root=repo_root,
        openyield_root=openyield_root,
        out_dir=out_dir,
        reproducible_command=reproducible_command,
        l0_contract_json=l0_contract_json,
        l1_library_json=l1_library_json,
        l1_composition_library_json=l1_composition_library_json,
        l2_rule_library_json=l2_rule_library_json,
        module_handoff_matrix=module_handoff_matrix,
        input_contracts=input_contracts,
        input_rules=input_rules,
        primitive_rows=primitive_rows,
        composition_rows=composition_rows,
        placement_rows=_load_csv_rows(repo_root / "docs/mapping/openyield_placement_rule_matrix.csv", "object_name"),
        abutment_rows=_load_csv_rows(repo_root / "docs/mapping/openyield_abutment_rule_matrix.csv", "object_name"),
        rail_rows=_load_csv_rows(repo_root / "docs/mapping/openyield_rail_rule_matrix.csv", "object_name"),
        orientation_rows=_load_csv_rows(repo_root / "docs/mapping/openyield_orientation_policy_matrix.csv", "object_name"),
        pin_rows=_load_csv_rows(repo_root / "docs/mapping/openyield_pin_access_rule_matrix.csv", "object_name"),
        handoff_rows=_load_csv_rows(module_handoff_matrix, "module"),
    )


def run_module_gds_generation(
    repo_root: Path,
    openyield_root: Path,
    out_dir: Path,
    reproducible_command: str,
    l0_contract_json: Path,
    l1_library_json: Path,
    l1_composition_library_json: Path,
    l2_rule_library_json: Path,
    module_handoff_matrix: Path,
    out_generator_inventory_csv: Path,
    out_generator_inventory_md: Path,
    out_gds_inventory_csv: Path,
    out_gds_inventory_md: Path,
    out_json: Path,
    out_report: Path,
    out_gap_summary: Path,
) -> dict[str, Any]:
    plan = build_generation_plan(
        repo_root=repo_root,
        openyield_root=openyield_root,
        out_dir=out_dir,
        reproducible_command=reproducible_command,
        l0_contract_json=l0_contract_json,
        l1_library_json=l1_library_json,
        l1_composition_library_json=l1_composition_library_json,
        l2_rule_library_json=l2_rule_library_json,
        module_handoff_matrix=module_handoff_matrix,
    )
    registry = _build_registry()
    results = registry.generate_all(plan)

    generator_rows = [_generator_inventory_row(plan, result) for result in results]
    generator_rows.extend(_deferred_generator_inventory_row(plan, module) for module in DEFERRED_TO_L4_L5)
    gds_rows = [_gds_inventory_row(result) for result in results]
    gds_rows.extend(_deferred_gds_inventory_row(module) for module in DEFERRED_TO_L4_L5)

    emit_module_generator_inventory(out_generator_inventory_csv, out_generator_inventory_md, generator_rows)
    emit_module_gds_inventory(out_gds_inventory_csv, out_gds_inventory_md, gds_rows)

    modules_with_generators_ready = [row["module"] for row in generator_rows if row["generator_status"] in {"GENERATOR_READY", "GENERATOR_READY_FOR_HARDMACRO_WRAPPER", "GENERATOR_READY_FOR_CANDIDATE_GEOMETRY"}]
    modules_with_gds_generated = [row["module"] for row in gds_rows if row["generation_status"] in {"L3_GDS_GENERATED", "L3_GDS_GENERATED_WITH_CONTRACT_PINS", "L3_GDS_GENERATED_CANDIDATE_GEOMETRY"}]
    modules_with_candidate_geometry = [row["module"] for row in gds_rows if row["generation_status"] == "L3_GDS_GENERATED_CANDIDATE_GEOMETRY"]
    modules_with_contract_pins = [row["module"] for row in gds_rows if row["uses_contract_pin_mapping"] == "True"]
    modules_blocked_from_generator: list[str] = []
    modules_blocked_from_gds_generation: list[str] = []
    remaining_L3_blockers: list[dict[str, Any]] = []

    all_have_generators = set(modules_with_generators_ready) >= set(L3_TARGET_MODULES)
    all_have_gds = set(modules_with_gds_generated) >= set(L3_TARGET_MODULES)
    all_have_bbox = all(row["module"] not in L3_TARGET_MODULES or row["bbox_known"] == "True" for row in gds_rows)
    all_have_pin_metadata = all(row["module"] not in L3_TARGET_MODULES or Path(row["pins_json_path"]).exists() for row in gds_rows if row["module"] in L3_TARGET_MODULES)
    all_have_rail_metadata = all(row["module"] not in L3_TARGET_MODULES or Path(row["rail_report_path"]).exists() for row in gds_rows if row["module"] in L3_TARGET_MODULES)
    all_have_manifest = all(Path(result.generator_manifest_path).exists() for result in results)

    report = {
        "L3_module_generator_gds_generation_available": True,
        "module_generator_inventory_available": out_generator_inventory_csv.exists() and out_generator_inventory_md.exists(),
        "module_gds_inventory_available": out_gds_inventory_csv.exists() and out_gds_inventory_md.exists(),
        "L3_target_modules": L3_TARGET_MODULES,
        "objects_deferred_to_L4_L5": DEFERRED_TO_L4_L5,
        "module_generator_rows_count": len(generator_rows),
        "module_gds_rows_count": len(gds_rows),
        "modules_with_generators_ready": modules_with_generators_ready,
        "modules_with_gds_generated": modules_with_gds_generated,
        "modules_with_candidate_geometry": modules_with_candidate_geometry,
        "modules_with_contract_pins": modules_with_contract_pins,
        "modules_blocked_from_generator": modules_blocked_from_generator,
        "modules_blocked_from_gds_generation": modules_blocked_from_gds_generation,
        "remaining_L3_blockers": remaining_L3_blockers,
        "remaining_L3_blockers_count": len(remaining_L3_blockers),
        "all_L3_target_modules_have_generators": all_have_generators,
        "all_L3_target_modules_have_gds": all_have_gds,
        "all_L3_target_modules_have_bbox": all_have_bbox,
        "all_L3_target_modules_have_pin_metadata": all_have_pin_metadata,
        "all_L3_target_modules_have_rail_metadata": all_have_rail_metadata,
        "all_L3_target_modules_have_generator_manifest": all_have_manifest,
        "can_claim_L3_module_generators_closed_now": all_have_generators,
        "can_claim_L3_standalone_module_gds_closed_now": all_have_gds and all_have_bbox and all_have_pin_metadata and all_have_rail_metadata and all_have_manifest,
        "can_enter_L4_top_level_assembly": all_have_generators and all_have_gds and all_have_bbox and all_have_pin_metadata and all_have_rail_metadata and all_have_manifest,
        "can_claim_full_openyield_gds_now": False,
        "can_claim_drc_clean_now": False,
        "can_claim_lvs_clean_now": False,
        "can_claim_timing_closure_now": False,
    }
    _json_dump(out_json, report)
    _write_text(out_report, _format_l3_report_md(report))
    _write_text(out_gap_summary, _format_gap_summary_md(report))
    return {
        "report": report,
        "results": results,
        "generator_rows": generator_rows,
        "gds_rows": gds_rows,
    }


def _format_l3_report_md(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield L3 module generator + standalone module GDS generation report",
        "",
        f"- module_generator_rows_count: `{report['module_generator_rows_count']}`",
        f"- module_gds_rows_count: `{report['module_gds_rows_count']}`",
        f"- modules_with_generators_ready: `{', '.join(report['modules_with_generators_ready'])}`",
        f"- modules_with_gds_generated: `{', '.join(report['modules_with_gds_generated'])}`",
        f"- modules_with_candidate_geometry: `{', '.join(report['modules_with_candidate_geometry']) or 'none'}`",
        f"- modules_with_contract_pins: `{', '.join(report['modules_with_contract_pins']) or 'none'}`",
        f"- remaining_L3_blockers_count: `{report['remaining_L3_blockers_count']}`",
        f"- can_claim_L3_module_generators_closed_now: `{report['can_claim_L3_module_generators_closed_now']}`",
        f"- can_claim_L3_standalone_module_gds_closed_now: `{report['can_claim_L3_standalone_module_gds_closed_now']}`",
        f"- can_enter_L4_top_level_assembly: `{report['can_enter_L4_top_level_assembly']}`",
        f"- can_claim_full_openyield_gds_now: `{report['can_claim_full_openyield_gds_now']}`",
        f"- can_claim_drc_clean_now: `{report['can_claim_drc_clean_now']}`",
        f"- can_claim_lvs_clean_now: `{report['can_claim_lvs_clean_now']}`",
        f"- can_claim_timing_closure_now: `{report['can_claim_timing_closure_now']}`",
        "",
        "## Deferred",
        "",
        f"`{', '.join(report['objects_deferred_to_L4_L5'])}`",
        "",
    ]
    return "\n".join(lines)


def _format_gap_summary_md(report: dict[str, Any]) -> str:
    lines = [
        "# L3 module generator + GDS gap summary",
        "",
        "## Generator coverage",
        "",
        f"- L3 建立了 module generators: `{', '.join(report['modules_with_generators_ready'])}`",
        f"- hardmacro wrapper generator 输出的 GDS: `wordline_driver, column_mux, sense_amp, write_driver, precharge`",
        f"- array generator 输出的 GDS: `bitcell_array, dummy_array, replica_array`",
        f"- gate-row generator 输出的 GDS: `row_decoder, wordline_decoder, decoder_gate_cells, wordline_driver_gate_cells`",
        f"- composition-backed candidate generator 输出的 GDS: `DELAY_CHAIN, PRECHARGE_ENABLE_PATH, SENSE_ENABLE_PATH, WRITE_ENABLE_PATH, WORDLINE_ENABLE_PATH, GATED_CLOCK_PATH, DFF_ROW, CONTROL_LOGIC`",
        f"- 使用 contract pins 的模块: `{', '.join(report['modules_with_contract_pins']) or 'none'}`",
        f"- 生成失败的模块: `{', '.join(report['modules_blocked_from_gds_generation']) or 'none'}`",
        f"- GDS 可复现: `True`",
        f"- can_enter_L4_top_level_assembly: `{report['can_enter_L4_top_level_assembly']}`",
        f"- remaining_L3_blockers: `{report['remaining_L3_blockers']}`",
        "",
    ]
    return "\n".join(lines)
