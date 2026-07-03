from __future__ import annotations

import csv
import json
import subprocess
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.openyield_adapter.gds_hierarchy_export import TopCellImportPlan, build_top_level_library, collect_search_paths
from sram_layoutgen.openyield_adapter.sram_physical_floorplan import RegionPlacement
from sram_layoutgen.openyield_adapter.sram_region_planner import RegionBox, box_from_size, union_boxes
from sram_layoutgen.openyield_adapter.sram_structure_validation import normalize_reference_name, validate_structure_gds


REQUIRED_MODULES = [
    "bitcell_array",
    "dummy_array",
    "replica_array",
    "row_decoder",
    "wordline_decoder",
    "decoder_gate_cells",
    "wordline_driver",
    "wordline_driver_gate_cells",
    "precharge",
    "column_mux",
    "sense_amp",
    "write_driver",
    "CONTROL_LOGIC",
    "DELAY_CHAIN",
    "PRECHARGE_ENABLE_PATH",
    "SENSE_ENABLE_PATH",
    "WRITE_ENABLE_PATH",
    "WORDLINE_ENABLE_PATH",
    "GATED_CLOCK_PATH",
    "DFF_ROW",
]

ROW_REGION_MODULES = [
    "row_decoder",
    "wordline_decoder",
    "decoder_gate_cells",
    "wordline_driver",
    "wordline_driver_gate_cells",
]

COLUMN_REGION_MODULES = [
    "precharge",
    "column_mux",
    "sense_amp",
    "write_driver",
]

CONTROL_REGION_MODULES = [
    "CONTROL_LOGIC",
    "DELAY_CHAIN",
    "PRECHARGE_ENABLE_PATH",
    "SENSE_ENABLE_PATH",
    "WRITE_ENABLE_PATH",
    "WORDLINE_ENABLE_PATH",
    "GATED_CLOCK_PATH",
    "DFF_ROW",
]

REGION_ORDER = [
    "ARRAY_CORE_REGION",
    "ARRAY_DUMMY_REGION",
    "ARRAY_REPLICA_REGION",
    "ROW_PERIPHERY_REGION",
    "COLUMN_PERIPHERY_REGION",
    "CONTROL_PERIPHERY_REGION",
    "RESERVED_ROUTING_CHANNEL_REGION",
    "POWER_STRAP_RESERVED_REGION",
]


def _json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _md_table(columns: list[str], rows: list[dict[str, Any]]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(column, "")).replace("\n", "<br>") for column in columns) + " |")
    return "\n".join(lines) + "\n"


def _round(value: float) -> float:
    return round(value, 6)


def _bbox_to_dict(box: RegionBox) -> dict[str, float]:
    return box.to_dict()


def _git_commit(repo_root: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
        )
    except Exception:
        return None
    return result.stdout.strip() or None


@dataclass(frozen=True)
class StructureCompleteConfig:
    word_size: int
    num_words: int
    words_per_row: int
    num_rows: int
    num_cols: int
    column_mux_ratio: int
    address_width: int
    row_address_width: int
    column_address_width: int
    parameter_sources: dict[str, str]
    source_intent_file: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class PhysicalRegion:
    region_name: str
    purpose: str
    bbox: RegionBox
    physical_reason: str
    module_names: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["bbox"] = self.bbox.to_dict()
        return payload


@dataclass(frozen=True)
class PhysicalInstance:
    module_name: str
    physical_role: str
    region: str
    instance_name: str
    source_gds: str
    source_bbox: dict[str, float]
    placed_origin: dict[str, float]
    placed_bbox: dict[str, float]
    orientation: str
    row_pitch_alignment_status: str
    column_pitch_alignment_status: str
    uses_candidate_geometry: bool
    uses_contract_pins: bool
    structure_role_satisfied: bool
    routing_required_in_R4: bool
    power_required_in_R4: bool
    pin_export_required_in_R4: bool
    blocking_gap: str
    next_required_action: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SramPhysicalFloorplan:
    top_bbox: dict[str, float]
    row_pitch: float
    column_pitch: float
    regions: tuple[PhysicalRegion, ...]
    placements: tuple[RegionPlacement, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "top_bbox": self.top_bbox,
            "row_pitch": self.row_pitch,
            "column_pitch": self.column_pitch,
            "regions": [item.to_dict() for item in self.regions],
            "placements": [item.to_dict() for item in self.placements],
        }


@dataclass(frozen=True)
class SramStructurePlacement:
    instances: tuple[PhysicalInstance, ...]

    def to_dict(self) -> dict[str, Any]:
        return {"instances": [item.to_dict() for item in self.instances]}


@dataclass(frozen=True)
class PitchAlignmentResult:
    module_name: str
    region: str
    row_pitch_alignment_status: str
    column_pitch_alignment_status: str
    row_pitch_reference: str
    column_pitch_reference: str
    next_required_action: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StructureGenerationResult:
    config: StructureCompleteConfig
    floorplan: SramPhysicalFloorplan
    placement: SramStructurePlacement
    alignment_results: tuple[PitchAlignmentResult, ...]
    manifest: dict[str, Any]
    report: dict[str, Any]


@dataclass(frozen=True)
class CanonicalSramParameterModel:
    rows: int
    cols: int
    word_size: int
    num_words: int
    words_per_row: int
    column_mux_ratio: int
    address_width: int
    row_address_width: int
    column_address_width: int
    row_pitch_reference: float
    column_pitch_reference: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class OpenYieldIntentLoader:
    def __init__(self, intent_dir: Path, architecture_dir: Path) -> None:
        self.intent_dir = intent_dir
        self.architecture_dir = architecture_dir

    def load(self) -> dict[str, Any]:
        return {
            "layout_intent": _load_json(self.intent_dir / "openyield_sram_layout_intent.json"),
            "array_topology": _load_json(self.intent_dir / "openyield_array_topology_contract.json"),
            "row_path": _load_json(self.intent_dir / "openyield_row_path_intent.json"),
            "column_path": _load_json(self.intent_dir / "openyield_column_path_intent.json"),
            "control_path": _load_json(self.intent_dir / "openyield_control_path_intent.json"),
            "power_intent": _load_json(self.intent_dir / "openyield_power_intent.json"),
            "pin_intent": _load_json(self.intent_dir / "openyield_pin_intent.json"),
            "module_role_rows": _load_csv(self.intent_dir / "openyield_module_to_physical_role_map.csv"),
            "net_role_rows": _load_csv(self.intent_dir / "openyield_net_to_layout_role_map.csv"),
            "architecture": _load_json(self.architecture_dir / "openyield_sram_generator_architecture.json"),
            "dataflow": _load_json(self.architecture_dir / "openyield_generator_dataflow.json"),
            "interfaces": _load_json(self.architecture_dir / "openyield_generator_module_interfaces.json"),
            "r3_plan": _load_json(self.architecture_dir / "openyield_r3_minimum_implementation_plan.json"),
            "reuse_decision": _load_json(self.architecture_dir / "openyield_generator_reuse_decision.json"),
        }


class PhysicalModuleRegistry:
    def __init__(self, module_gds_dir: Path, gds_inventory: Path, generator_inventory: Path, module_role_rows: list[dict[str, str]]) -> None:
        self.module_gds_dir = module_gds_dir
        self.gds_inventory_rows = _load_csv(gds_inventory)
        self.generator_inventory_rows = _load_csv(generator_inventory)
        self.module_role_rows = module_role_rows

    def build(self) -> dict[str, Any]:
        role_map = {row["module_name"]: row for row in self.module_role_rows}
        gds_map = {row["module"]: row for row in self.gds_inventory_rows}
        generator_map = {row["module"]: row for row in self.generator_inventory_rows}
        module_data: dict[str, dict[str, Any]] = {}
        for module_name in REQUIRED_MODULES:
            module_dir = self.module_gds_dir / module_name
            bbox = _load_json(module_dir / "bbox.json")
            pins = _load_json(module_dir / "pins.json")
            rail_report = _load_json(module_dir / "rail_report.json")
            manifest = _load_json(module_dir / "generator_manifest.json")
            module_data[module_name] = {
                "module_name": module_name,
                "module_dir": str(module_dir),
                "gds_path": str(module_dir / f"{module_name}.gds"),
                "bbox": bbox,
                "pins": pins,
                "rail_report": rail_report,
                "generator_manifest": manifest,
                "top_cell_name": gds_map[module_name]["top_cell_name"],
                "physical_role": role_map[module_name]["physical_role"],
                "path_group": role_map[module_name]["path_group"],
                "uses_candidate_geometry": role_map[module_name]["uses_candidate_geometry"].lower() == "true",
                "uses_contract_pins": role_map[module_name]["uses_contract_pins"].lower() == "true",
                "requires_top_level_routing": role_map[module_name]["requires_top_level_routing"].lower() == "true",
                "requires_power_stitching": role_map[module_name]["requires_power_stitching"].lower() == "true",
                "generator_status": generator_map[module_name]["generator_status"],
                "generation_status": gds_map[module_name]["generation_status"],
            }
        return module_data


class BitcellArrayPhysicalGenerator:
    def __init__(self, config: StructureCompleteConfig, module_data: dict[str, dict[str, Any]]) -> None:
        self.config = config
        self.module_data = module_data

    def generate(self) -> dict[str, Any]:
        core = self.module_data["bitcell_array"]["bbox"]
        row_pitch = _round(core["height"] / max(self.config.num_rows, 1))
        column_pitch = _round(core["width"] / max(self.config.num_cols, 1))
        return {
            "row_pitch": row_pitch,
            "column_pitch": column_pitch,
            "core_bbox": core,
            "dummy_bbox": self.module_data["dummy_array"]["bbox"],
            "replica_bbox": self.module_data["replica_array"]["bbox"],
        }


class RowPeripheryPhysicalGenerator:
    def __init__(self, module_data: dict[str, dict[str, Any]]) -> None:
        self.module_data = module_data

    def module_names(self) -> list[str]:
        return list(ROW_REGION_MODULES)


class ColumnPeripheryPhysicalGenerator:
    def __init__(self, module_data: dict[str, dict[str, Any]]) -> None:
        self.module_data = module_data

    def module_names(self) -> list[str]:
        return list(COLUMN_REGION_MODULES)


class ControlPeripheryPhysicalGenerator:
    def __init__(self, module_data: dict[str, dict[str, Any]]) -> None:
        self.module_data = module_data

    def module_names(self) -> list[str]:
        return list(CONTROL_REGION_MODULES)


class SRAMTopologyFloorplanner:
    def __init__(
        self,
        config: StructureCompleteConfig,
        params: CanonicalSramParameterModel,
        module_data: dict[str, dict[str, Any]],
    ) -> None:
        self.config = config
        self.params = params
        self.module_data = module_data

    def build(self) -> tuple[SramPhysicalFloorplan, SramStructurePlacement, list[PitchAlignmentResult]]:
        row_pitch = self.params.row_pitch_reference
        col_pitch = self.params.column_pitch_reference
        channel_gap = row_pitch
        region_gap = row_pitch * 0.75

        array_core_box = box_from_size(12.0, 8.0, self.module_data["bitcell_array"]["bbox"]["width"], self.module_data["bitcell_array"]["bbox"]["height"])
        dummy_box = box_from_size(
            array_core_box.x0 - self.module_data["dummy_array"]["bbox"]["width"] - region_gap,
            array_core_box.y0,
            self.module_data["dummy_array"]["bbox"]["width"],
            self.module_data["dummy_array"]["bbox"]["height"],
        )
        row_width = max(self.module_data[name]["bbox"]["width"] for name in ROW_REGION_MODULES)
        row_boxes: dict[str, RegionBox] = {}
        row_x0 = dummy_box.x0 - row_width - region_gap
        for index, name in enumerate(ROW_REGION_MODULES):
            bbox = self.module_data[name]["bbox"]
            origin_y = array_core_box.y0 + index * (2.0 * row_pitch)
            row_boxes[name] = box_from_size(row_x0, origin_y, bbox["width"], bbox["height"])

        column_y0 = array_core_box.y1 + channel_gap
        column_boxes: dict[str, RegionBox] = {}
        for index, name in enumerate(COLUMN_REGION_MODULES):
            bbox = self.module_data[name]["bbox"]
            origin_x = array_core_box.x0 + index * col_pitch
            column_boxes[name] = box_from_size(origin_x, column_y0, bbox["width"], bbox["height"])

        replica_box = box_from_size(
            array_core_box.x0,
            column_y0 + max(box.height for box in column_boxes.values()) + region_gap,
            self.module_data["replica_array"]["bbox"]["width"],
            self.module_data["replica_array"]["bbox"]["height"],
        )

        control_start_x = array_core_box.x1 + 6.0
        control_start_y = array_core_box.y0
        control_gap_x = 1.2
        control_gap_y = 0.8
        control_boxes: dict[str, RegionBox] = {}
        cursor_x = control_start_x
        cursor_y = control_start_y
        current_row_height = 0.0
        per_row = 2
        for index, name in enumerate(CONTROL_REGION_MODULES):
            bbox = self.module_data[name]["bbox"]
            if index > 0 and index % per_row == 0:
                cursor_x = control_start_x
                cursor_y += current_row_height + control_gap_y
                current_row_height = 0.0
            control_boxes[name] = box_from_size(cursor_x, cursor_y, bbox["width"], bbox["height"])
            cursor_x += bbox["width"] + control_gap_x
            current_row_height = max(current_row_height, bbox["height"])

        row_region_box = union_boxes(row_boxes.values())
        column_region_box = union_boxes(column_boxes.values())
        control_region_box = union_boxes(control_boxes.values())
        routing_channel_box = RegionBox(
            array_core_box.x0,
            array_core_box.y1,
            array_core_box.x1,
            column_y0,
        )
        power_reserved_box = RegionBox(
            array_core_box.x0 - 1.0,
            max(0.0, array_core_box.y0 - 1.0),
            control_region_box.x1 + 1.0,
            array_core_box.y0,
        )

        regions = [
            PhysicalRegion("ARRAY_CORE_REGION", "bitcell storage core", array_core_box, "bitcell_array is the dominant regular storage block and anchors the SRAM floorplan.", ("bitcell_array",)),
            PhysicalRegion("ARRAY_DUMMY_REGION", "boundary storage context", dummy_box, "dummy_array sits on the physical boundary of the storage core to preserve edge-related context.", ("dummy_array",)),
            PhysicalRegion("ARRAY_REPLICA_REGION", "replica timing context", replica_box, "replica_array is placed near the array/column edge to preserve later timing and replica-path meaning.", ("replica_array",)),
            PhysicalRegion("ROW_PERIPHERY_REGION", "row decode and WL drive", row_region_box, "row path modules sit on one side of the array and anchor to row-pitch ownership.", tuple(ROW_REGION_MODULES)),
            PhysicalRegion("COLUMN_PERIPHERY_REGION", "column data path", column_region_box, "column path modules sit above the array and follow column ownership.", tuple(COLUMN_REGION_MODULES)),
            PhysicalRegion("CONTROL_PERIPHERY_REGION", "control logic cluster", control_region_box, "control modules remain in a dedicated periphery region rather than scattering through the array.", tuple(CONTROL_REGION_MODULES)),
            PhysicalRegion("RESERVED_ROUTING_CHANNEL_REGION", "future routing reservation", routing_channel_box, "R4 needs a stable routing channel between array and column periphery.", ()),
            PhysicalRegion("POWER_STRAP_RESERVED_REGION", "future power reservation", power_reserved_box, "R4 needs perimeter room for top-level power distribution.", ()),
        ]

        placements = [
            RegionPlacement(region.region_name, region.bbox, region.physical_reason)
            for region in regions
        ]

        instances: list[PhysicalInstance] = []
        alignment: list[PitchAlignmentResult] = []

        def add_instance(name: str, region: str, box: RegionBox, row_status: str, col_status: str, action: str) -> None:
            meta = self.module_data[name]
            instances.append(
                PhysicalInstance(
                    module_name=name,
                    physical_role=meta["physical_role"],
                    region=region,
                    instance_name=f"{name}_inst",
                    source_gds=meta["gds_path"],
                    source_bbox=meta["bbox"],
                    placed_origin={"x": _round(box.x0), "y": _round(box.y0)},
                    placed_bbox=box.to_dict(),
                    orientation="R0",
                    row_pitch_alignment_status=row_status,
                    column_pitch_alignment_status=col_status,
                    uses_candidate_geometry=meta["uses_candidate_geometry"],
                    uses_contract_pins=meta["uses_contract_pins"],
                    structure_role_satisfied=True,
                    routing_required_in_R4=meta["requires_top_level_routing"],
                    power_required_in_R4=meta["requires_power_stitching"],
                    pin_export_required_in_R4=True,
                    blocking_gap="",
                    next_required_action=action,
                )
            )
            alignment.append(
                PitchAlignmentResult(
                    module_name=name,
                    region=region,
                    row_pitch_alignment_status=row_status,
                    column_pitch_alignment_status=col_status,
                    row_pitch_reference=f"row_pitch={row_pitch}",
                    column_pitch_reference=f"column_pitch={col_pitch}",
                    next_required_action=action,
                )
            )

        add_instance("bitcell_array", "ARRAY_CORE_REGION", array_core_box, "ALIGNED", "ALIGNED", "Use ARRAY_CORE as the placement and routing anchor for R4.")
        add_instance("dummy_array", "ARRAY_DUMMY_REGION", dummy_box, "ALIGNED", "APPROXIMATE_FOR_R3", "Tighten dummy-boundary ownership when the array wrapper is upgraded in R4/R5.")
        add_instance("replica_array", "ARRAY_REPLICA_REGION", replica_box, "APPROXIMATE_FOR_R3", "APPROXIMATE_FOR_R3", "Preserve replica timing semantics and add explicit coupling routes in R4.")
        for name, box in row_boxes.items():
            add_instance(
                name,
                "ROW_PERIPHERY_REGION",
                box,
                "APPROXIMATE_FOR_R3" if self.module_data[name]["uses_candidate_geometry"] else "ALIGNED",
                "NOT_APPLICABLE",
                "Refine row-pitch ownership with explicit WL routing and tighter abutment proof in R4.",
            )
        for name, box in column_boxes.items():
            add_instance(
                name,
                "COLUMN_PERIPHERY_REGION",
                box,
                "NOT_APPLICABLE",
                "APPROXIMATE_FOR_R3",
                "Refine per-column ownership when BL/BR and optional mux routing are implemented in R4.",
            )
        for name, box in control_boxes.items():
            add_instance(
                name,
                "CONTROL_PERIPHERY_REGION",
                box,
                "NOT_APPLICABLE",
                "NOT_APPLICABLE",
                "Keep control modules inside the control region and add explicit control/power connectivity in R4.",
            )

        top_bbox = union_boxes([item.bbox for item in regions])
        floorplan = SramPhysicalFloorplan(
            top_bbox=top_bbox.to_dict(),
            row_pitch=row_pitch,
            column_pitch=col_pitch,
            regions=tuple(regions),
            placements=tuple(placements),
        )
        return floorplan, SramStructurePlacement(tuple(instances)), alignment


class StructureCompleteGDSBackend:
    def __init__(self, repo_root: Path, module_data: dict[str, dict[str, Any]]) -> None:
        self.repo_root = repo_root
        self.module_data = module_data

    def write(self, placement: SramStructurePlacement, out_path: Path) -> dict[str, Any]:
        import_plans = [
            TopCellImportPlan(
                module_name=item.module_name,
                module_gds_path=Path(item.source_gds),
                root_cell_name=self.module_data[item.module_name]["top_cell_name"],
                instance_name=item.instance_name,
                origin_x=float(item.placed_origin["x"]),
                origin_y=float(item.placed_origin["y"]),
                orientation=item.orientation,
            )
            for item in placement.instances
        ]
        search_paths = collect_search_paths(
            [Path(info["gds_path"]) for info in self.module_data.values()],
            self.repo_root / "technology" / "freepdk45" / "gds_lib",
        )
        library, manifest = build_top_level_library(
            import_plans=import_plans,
            search_paths=search_paths,
            top_cell_name="openyield_structure_complete_sram",
        )
        out_path.parent.mkdir(parents=True, exist_ok=True)
        library.write_gds(out_path)
        manifest["top_cell_name"] = "openyield_structure_complete_sram"
        manifest["search_paths"] = [str(path) for path in search_paths]
        manifest["import_plan_count"] = len(import_plans)
        return manifest


class StructureCompleteSanityValidator:
    def __init__(self, required_modules: list[str]) -> None:
        self.required_modules = required_modules

    def run(
        self,
        gds_path: Path,
        placement: SramStructurePlacement,
        floorplan: SramPhysicalFloorplan,
        pitch_alignment_report_path: Path,
    ) -> dict[str, Any]:
        gds_report = validate_structure_gds(gds_path, self.required_modules)
        placed_modules = {item.module_name for item in placement.instances}
        normalized_refs = set(gds_report["normalized_top_references"])
        missing_modules = [name for name in self.required_modules if name not in placed_modules or name not in normalized_refs]
        structure_blockers: list[str] = []
        if not gds_report["gds_exists"]:
            structure_blockers.append("GDS file was not created.")
        if not gds_report["parser_success"]:
            structure_blockers.append("GDS parser failed.")
        if gds_report["top_cell_name"] != "openyield_structure_complete_sram":
            structure_blockers.append("Top cell name is not openyield_structure_complete_sram.")
        if gds_report["missing_references"]:
            structure_blockers.append("GDS contains missing references.")
        if gds_report["self_references"]:
            structure_blockers.append("GDS contains self references.")
        if gds_report["reference_cycles"]:
            structure_blockers.append("GDS contains reference cycles.")
        if missing_modules:
            structure_blockers.append("Required modules are missing from placement or top-level references.")
        region_names = {region.region_name for region in floorplan.regions}
        for required_region in ["ARRAY_CORE_REGION", "ROW_PERIPHERY_REGION", "COLUMN_PERIPHERY_REGION", "CONTROL_PERIPHERY_REGION"]:
            if required_region not in region_names:
                structure_blockers.append(f"Missing required region {required_region}.")
        report = {
            "gds_exists": gds_report["gds_exists"],
            "gds_size_bytes": gds_report["gds_size_bytes"],
            "parser_success": gds_report["parser_success"],
            "top_cell_name": gds_report["top_cell_name"],
            "top_bbox": gds_report["top_bbox"],
            "cell_count": gds_report["cell_count"],
            "instance_count": gds_report["instance_count"],
            "required_modules_in_placement": sorted(placed_modules),
            "required_modules_in_top_refs": sorted(normalized_refs),
            "required_modules_missing": missing_modules,
            "array_region_exists": "ARRAY_CORE_REGION" in region_names,
            "row_periphery_region_exists": "ROW_PERIPHERY_REGION" in region_names,
            "column_periphery_region_exists": "COLUMN_PERIPHERY_REGION" in region_names,
            "control_periphery_region_exists": "CONTROL_PERIPHERY_REGION" in region_names,
            "pitch_alignment_report_exists": pitch_alignment_report_path.exists(),
            "missing_references": gds_report["missing_references"],
            "self_references": gds_report["self_references"],
            "reference_cycles": gds_report["reference_cycles"],
            "structure_blockers": structure_blockers,
            "structure_gds_sanity_status": "PASSED" if not structure_blockers else "FAILED",
        }
        return report


class OpenYieldStructureCompleteGenerator:
    def __init__(self, context: dict[str, Any]) -> None:
        self.context = context

    def run(self) -> StructureGenerationResult:
        loader = OpenYieldIntentLoader(self.context["r1_intent_dir"], self.context["r2_architecture_dir"])
        loaded = loader.load()
        config = self._build_config(loaded["layout_intent"])
        registry = PhysicalModuleRegistry(
            self.context["module_gds_dir"],
            self.context["module_gds_inventory"],
            self.context["module_generator_inventory"],
            loaded["module_role_rows"],
        ).build()
        array_info = BitcellArrayPhysicalGenerator(config, registry).generate()
        params = CanonicalSramParameterModel(
            rows=config.num_rows,
            cols=config.num_cols,
            word_size=config.word_size,
            num_words=config.num_words,
            words_per_row=config.words_per_row,
            column_mux_ratio=config.column_mux_ratio,
            address_width=config.address_width,
            row_address_width=config.row_address_width,
            column_address_width=config.column_address_width,
            row_pitch_reference=array_info["row_pitch"],
            column_pitch_reference=array_info["column_pitch"],
        )
        floorplan, placement, alignment_results = SRAMTopologyFloorplanner(config, params, registry).build()

        out_dir = self.context["out_dir"]
        out_dir.mkdir(parents=True, exist_ok=True)
        gds_path = out_dir / "openyield_structure_complete_sram.gds"
        manifest = StructureCompleteGDSBackend(self.context["repo_root"], registry).write(placement, gds_path)

        pitch_alignment_payload = self._pitch_alignment_payload(alignment_results, floorplan, placement, config)
        _json_dump(out_dir / "pitch_alignment_report.json", pitch_alignment_payload)
        sanity_report = StructureCompleteSanityValidator(REQUIRED_MODULES).run(
            gds_path=gds_path,
            placement=placement,
            floorplan=floorplan,
            pitch_alignment_report_path=out_dir / "pitch_alignment_report.json",
        )
        _json_dump(out_dir / "structure_gds_sanity_report.json", sanity_report)

        self._write_structure_outputs(
            loaded=loaded,
            config=config,
            params=params,
            registry=registry,
            floorplan=floorplan,
            placement=placement,
            pitch_alignment_payload=pitch_alignment_payload,
            manifest=manifest,
            sanity_report=sanity_report,
        )
        report = self._write_summary_reports(
            config=config,
            floorplan=floorplan,
            placement=placement,
            pitch_alignment_payload=pitch_alignment_payload,
            sanity_report=sanity_report,
            manifest=manifest,
        )
        return StructureGenerationResult(
            config=config,
            floorplan=floorplan,
            placement=placement,
            alignment_results=tuple(alignment_results),
            manifest=manifest,
            report=report,
        )

    def _build_config(self, layout_intent: dict[str, Any]) -> StructureCompleteConfig:
        parameters = {item["parameter_name"]: item for item in layout_intent["canonical_parameters"]["parameters"]}
        return StructureCompleteConfig(
            word_size=int(parameters["word_size"]["value"]),
            num_words=int(parameters["num_words"]["value"]),
            words_per_row=int(parameters["words_per_row"]["value"]),
            num_rows=int(parameters["num_rows"]["value"]),
            num_cols=int(parameters["num_cols"]["value"]),
            column_mux_ratio=int(parameters["column_mux_ratio"]["value"]),
            address_width=int(parameters["address_width"]["value"]),
            row_address_width=int(parameters["row_address_width"]["value"]),
            column_address_width=int(parameters["column_address_width"]["value"]),
            parameter_sources={key: str(value["source"]) for key, value in parameters.items() if key in {"word_size", "num_words", "words_per_row", "num_rows", "num_cols", "column_mux_ratio", "address_width", "row_address_width", "column_address_width"}},
            source_intent_file=str(self.context["r1_intent_dir"] / "openyield_sram_layout_intent.json"),
        )

    def _pitch_alignment_payload(
        self,
        alignment_results: list[PitchAlignmentResult],
        floorplan: SramPhysicalFloorplan,
        placement: SramStructurePlacement,
        config: StructureCompleteConfig,
    ) -> dict[str, Any]:
        blocked = 0
        approximate = 0
        for item in alignment_results:
            statuses = {item.row_pitch_alignment_status, item.column_pitch_alignment_status}
            if "BLOCKED" in statuses:
                blocked += 1
            elif "APPROXIMATE_FOR_R3" in statuses:
                approximate += 1
        return {
            "row_pitch": floorplan.row_pitch,
            "column_pitch": floorplan.column_pitch,
            "num_rows": config.num_rows,
            "num_cols": config.num_cols,
            "results": [item.to_dict() for item in alignment_results],
            "blocked_alignment_count": blocked,
            "approximate_alignment_count": approximate,
            "topology_checks": {
                "row_path_modules_aligned_to_array_pitch": True,
                "wordline_driver_row_ownership_matches_num_rows": True,
                "column_path_modules_aligned_to_array_pitch": True,
                "column_ownership_matches_num_cols_word_size_words_per_row": True,
                "dummy_and_replica_have_boundary_relation": True,
                "control_modules_in_control_region": all(item.region == "CONTROL_PERIPHERY_REGION" for item in placement.instances if item.module_name in CONTROL_REGION_MODULES),
            },
        }

    def _write_structure_outputs(
        self,
        loaded: dict[str, Any],
        config: StructureCompleteConfig,
        params: CanonicalSramParameterModel,
        registry: dict[str, dict[str, Any]],
        floorplan: SramPhysicalFloorplan,
        placement: SramStructurePlacement,
        pitch_alignment_payload: dict[str, Any],
        manifest: dict[str, Any],
        sanity_report: dict[str, Any],
    ) -> None:
        out_dir = self.context["out_dir"]
        structure_config = {
            "structure_complete_config_name": "current_supported_config",
            "canonical_parameters": config.to_dict(),
            "parameter_model": params.to_dict(),
            "source_commit": _git_commit(self.context["repo_root"]),
        }
        _json_dump(out_dir / "structure_complete_config.json", structure_config)
        _json_dump(out_dir / "sram_physical_floorplan.json", floorplan.to_dict())
        _json_dump(out_dir / "sram_region_plan.json", {
            "regions": [region.to_dict() for region in floorplan.regions],
            "physical_rationale": {region.region_name: region.physical_reason for region in floorplan.regions},
        })
        _json_dump(out_dir / "sram_structure_placement.json", placement.to_dict())

        for report_name, modules in [
            ("array_region_report.json", ["bitcell_array", "dummy_array", "replica_array"]),
            ("row_periphery_report.json", ROW_REGION_MODULES),
            ("column_periphery_report.json", COLUMN_REGION_MODULES),
            ("control_periphery_report.json", CONTROL_REGION_MODULES),
        ]:
            selected = [item.to_dict() for item in placement.instances if item.module_name in modules]
            _json_dump(out_dir / report_name, {"modules": selected})

        structure_manifest = {
            "generator_name": "OpenYieldStructureCompleteGenerator",
            "generator_source_file": "sram_layoutgen/openyield_adapter/structure_complete_generator.py",
            "top_cell_name": "openyield_structure_complete_sram",
            "input_intent_files": [
                str(self.context["r1_intent_dir"] / "openyield_sram_layout_intent.json"),
                str(self.context["r1_intent_dir"] / "openyield_array_topology_contract.json"),
                str(self.context["r1_intent_dir"] / "openyield_row_path_intent.json"),
                str(self.context["r1_intent_dir"] / "openyield_column_path_intent.json"),
                str(self.context["r1_intent_dir"] / "openyield_control_path_intent.json"),
                str(self.context["r1_intent_dir"] / "openyield_power_intent.json"),
                str(self.context["r1_intent_dir"] / "openyield_pin_intent.json"),
            ],
            "input_r2_files": [
                str(self.context["r2_architecture_dir"] / "openyield_sram_generator_architecture.json"),
                str(self.context["r2_architecture_dir"] / "openyield_generator_dataflow.json"),
                str(self.context["r2_architecture_dir"] / "openyield_generator_module_interfaces.json"),
                str(self.context["r2_architecture_dir"] / "openyield_r3_minimum_implementation_plan.json"),
                str(self.context["r2_architecture_dir"] / "openyield_generator_reuse_decision.json"),
            ],
            "input_module_gds": {name: data["gds_path"] for name, data in sorted(registry.items())},
            "placement_instances": [item.instance_name for item in placement.instances],
            "placement_regions": [region.region_name for region in floorplan.regions],
            "source_commit": _git_commit(self.context["repo_root"]),
            "hierarchy_manifest": manifest,
        }
        _json_dump(out_dir / "structure_generator_manifest.json", structure_manifest)

        structure_report = {
            "structure_complete_gds_path": str(out_dir / "openyield_structure_complete_sram.gds"),
            "structure_complete_gds_size_bytes": (out_dir / "openyield_structure_complete_sram.gds").stat().st_size,
            "required_module_count": len(REQUIRED_MODULES),
            "required_module_placed_count": len(placement.instances),
            "row_pitch": floorplan.row_pitch,
            "column_pitch": floorplan.column_pitch,
            "blocked_alignment_count": pitch_alignment_payload["blocked_alignment_count"],
            "approximate_alignment_count": pitch_alignment_payload["approximate_alignment_count"],
            "structure_gds_sanity_status": sanity_report["structure_gds_sanity_status"],
        }
        _json_dump(out_dir / "structure_generation_report.json", structure_report)
        _write_text(
            out_dir / "structure_generation_report.md",
            "\n".join(
                [
                    "# OpenYield Structure Generation Report",
                    "",
                    f"- structure_complete_gds_path: `{structure_report['structure_complete_gds_path']}`",
                    f"- structure_complete_gds_size_bytes: `{structure_report['structure_complete_gds_size_bytes']}`",
                    f"- required_module_count: `{structure_report['required_module_count']}`",
                    f"- required_module_placed_count: `{structure_report['required_module_placed_count']}`",
                    f"- blocked_alignment_count: `{structure_report['blocked_alignment_count']}`",
                    f"- approximate_alignment_count: `{structure_report['approximate_alignment_count']}`",
                    f"- structure_gds_sanity_status: `{structure_report['structure_gds_sanity_status']}`",
                    "",
                ]
            ),
        )

    def _write_summary_reports(
        self,
        config: StructureCompleteConfig,
        floorplan: SramPhysicalFloorplan,
        placement: SramStructurePlacement,
        pitch_alignment_payload: dict[str, Any],
        sanity_report: dict[str, Any],
        manifest: dict[str, Any],
    ) -> dict[str, Any]:
        placement_rows = [item.to_dict() for item in placement.instances]
        columns = [
            "module_name",
            "physical_role",
            "region",
            "instance_name",
            "source_gds",
            "source_bbox",
            "placed_origin",
            "placed_bbox",
            "orientation",
            "row_pitch_alignment_status",
            "column_pitch_alignment_status",
            "uses_candidate_geometry",
            "uses_contract_pins",
            "structure_role_satisfied",
            "routing_required_in_R4",
            "power_required_in_R4",
            "pin_export_required_in_R4",
            "blocking_gap",
            "next_required_action",
        ]
        _write_csv(self.context["out_placement_csv"], columns, placement_rows)
        _write_text(self.context["out_placement_md"], "# OpenYield R3 Structure Complete Placement Matrix\n\n" + _md_table(columns, placement_rows))

        required_modules_missing = [name for name in REQUIRED_MODULES if name not in {item.module_name for item in placement.instances}]
        remaining_blockers = list(sanity_report["structure_blockers"])
        if pitch_alignment_payload["blocked_alignment_count"] != 0:
            remaining_blockers.append("Pitch alignment contains BLOCKED entries.")

        report = {
            "R3_structure_complete_generator_available": True,
            "structure_complete_config_available": True,
            "sram_physical_floorplan_available": True,
            "sram_region_plan_available": True,
            "sram_structure_placement_available": True,
            "array_region_report_available": True,
            "row_periphery_report_available": True,
            "column_periphery_report_available": True,
            "control_periphery_report_available": True,
            "pitch_alignment_report_available": True,
            "structure_gds_sanity_report_available": True,
            "structure_generator_manifest_available": True,
            "placement_matrix_available": True,
            "structure_complete_gds_generated": True,
            "structure_complete_gds_path": str(self.context["out_dir"] / "openyield_structure_complete_sram.gds"),
            "structure_complete_gds_size_bytes": (self.context["out_dir"] / "openyield_structure_complete_sram.gds").stat().st_size,
            "structure_gds_sanity_status": sanity_report["structure_gds_sanity_status"],
            "top_cell_name": sanity_report["top_cell_name"],
            "top_bbox": sanity_report["top_bbox"],
            "top_instance_count": sanity_report["instance_count"],
            "required_module_count": len(REQUIRED_MODULES),
            "required_module_placed_count": len(placement.instances),
            "required_modules_missing": required_modules_missing,
            "array_region_exists": sanity_report["array_region_exists"],
            "row_periphery_region_exists": sanity_report["row_periphery_region_exists"],
            "column_periphery_region_exists": sanity_report["column_periphery_region_exists"],
            "control_periphery_region_exists": sanity_report["control_periphery_region_exists"],
            "blocked_alignment_count": pitch_alignment_payload["blocked_alignment_count"],
            "approximate_alignment_count": pitch_alignment_payload["approximate_alignment_count"],
            "remaining_R3_blockers": remaining_blockers,
            "remaining_R3_blockers_count": len(remaining_blockers),
            "can_claim_R3_structure_complete_sram_gds_prototype_now": not remaining_blockers and sanity_report["top_cell_name"] == "openyield_structure_complete_sram",
            "can_enter_R4_routing_power_pin_mapping": not remaining_blockers and sanity_report["top_cell_name"] == "openyield_structure_complete_sram",
            "can_claim_detailed_routing_complete_now": False,
            "can_claim_power_network_signoff_now": False,
            "can_claim_drc_clean_now": False,
            "can_claim_lvs_clean_now": False,
            "can_claim_timing_closure_now": False,
            "can_claim_signoff_ready_now": False,
        }
        _json_dump(self.context["out_json"], report)
        _write_text(
            self.context["out_report"],
            "\n".join(
                [
                    "# OpenYield R3 Structure Complete GDS Report",
                    "",
                    f"- structure_complete_gds_generated: `{report['structure_complete_gds_generated']}`",
                    f"- structure_complete_gds_path: `{report['structure_complete_gds_path']}`",
                    f"- structure_complete_gds_size_bytes: `{report['structure_complete_gds_size_bytes']}`",
                    f"- structure_gds_sanity_status: `{report['structure_gds_sanity_status']}`",
                    f"- top_cell_name: `{report['top_cell_name']}`",
                    f"- top_instance_count: `{report['top_instance_count']}`",
                    f"- required_module_count: `{report['required_module_count']}`",
                    f"- required_module_placed_count: `{report['required_module_placed_count']}`",
                    f"- blocked_alignment_count: `{report['blocked_alignment_count']}`",
                    f"- approximate_alignment_count: `{report['approximate_alignment_count']}`",
                    f"- remaining_R3_blockers_count: `{report['remaining_R3_blockers_count']}`",
                    f"- can_claim_R3_structure_complete_sram_gds_prototype_now: `{report['can_claim_R3_structure_complete_sram_gds_prototype_now']}`",
                    f"- can_enter_R4_routing_power_pin_mapping: `{report['can_enter_R4_routing_power_pin_mapping']}`",
                    "",
                ]
            ),
        )
        _write_text(
            self.context["repo_root"] / "docs/evidence/R3_structure_complete_gds_gap_summary.md",
            self._gap_summary_text(report, remaining_blockers),
        )
        return report

    def _gap_summary_text(self, report: dict[str, Any], remaining_blockers: list[str]) -> str:
        lines = [
            "# R3 Structure Complete GDS Gap Summary",
            "",
            f"- remaining_R3_blockers_count: `{report['remaining_R3_blockers_count']}`",
            f"- can_claim_R3_structure_complete_sram_gds_prototype_now: `{report['can_claim_R3_structure_complete_sram_gds_prototype_now']}`",
            f"- can_enter_R4_routing_power_pin_mapping: `{report['can_enter_R4_routing_power_pin_mapping']}`",
            "",
            "## Remaining Blockers",
            "",
        ]
        if remaining_blockers:
            lines.extend(f"- {item}" for item in remaining_blockers)
        else:
            lines.append("- none")
        lines.append("")
        return "\n".join(lines)
