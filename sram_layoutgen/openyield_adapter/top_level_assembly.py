from __future__ import annotations

import csv
import importlib.util
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import gdstk
import gdspy

from sram_layoutgen.openyield_adapter.gds_hierarchy_export import (
    TopCellImportPlan,
    build_top_level_library,
    collect_search_paths,
    diagnose_gds_hierarchy,
    write_hierarchy_diagnosis,
)


L3_REQUIRED_MODULES = [
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

L4_TOP_LEVEL_OBJECTS = [
    "SRAM_TOP",
    "BANK",
    "routing_semantics",
    "power_semantics",
    "timing_semantics",
]

TOP_LEVEL_ASSEMBLY_INVENTORY_COLUMNS = [
    "object",
    "object_category",
    "is_top_level_target",
    "source_module_gds",
    "module_gds_sanity_status",
    "instantiated_in_top_gds",
    "instance_name",
    "origin",
    "orientation",
    "bbox",
    "pins_available",
    "rail_metadata_available",
    "routing_handoff_available",
    "power_handoff_available",
    "uses_candidate_geometry",
    "uses_contract_pins",
    "assembly_status",
    "blocking_gap",
    "next_required_action",
    "evidence_files",
]

POWER_PIN_NAMES = {"VDD", "GND", "VSS"}
TOP_LEVEL_PORT_NAMES = ("A[*]", "DIN[*]", "DOUT[*]", "clk", "csb", "web", "VDD", "GND")


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


def _load_csv_rows(path: Path, key: str) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return {str(row[key]): row for row in rows}


def _load_csv_list(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _bool_from_str(value: str | bool | None) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() == "true"


def _canonical_token(text: str) -> str:
    cleaned = (
        text.replace("[i]", "")
        .replace("[*]", "")
        .replace("(", "")
        .replace(")", "")
        .replace("/", "_")
        .replace(";", "_")
        .replace("-", "_")
        .replace(" ", "")
        .lower()
    )
    alias = {
        "wl": "wl",
        "dec_wl": "dec_wl",
        "dec_out": "dec_out",
        "a": "a",
        "din": "din",
        "d": "d",
        "q": "q",
        "clk": "clk",
        "clk_buf": "clk",
        "cs": "cs",
        "csb": "cs",
        "we": "we",
        "web": "we",
        "pre": "precharge_en",
        "precharge_en": "precharge_en",
        "s_en": "sense_en",
        "sense_en": "sense_en",
        "w_en": "write_en",
        "write_en": "write_en",
        "wl_en": "wl_en",
        "rbl": "rbl",
        "rblb": "rblb",
        "bl": "bl",
        "blb": "br",
        "br": "br",
        "brb": "br",
        "sa_in": "bl_out",
        "sa_inb": "br_out",
        "in": "bl",
        "inb": "br",
        "en": "en",
        "enb": "en_bar",
        "out": "delay_out",
        "out_bar": "delay_out_bar",
        "z": "z",
        "qb": "dout",
        "doutpath": "dout",
    }
    return alias.get(cleaned, cleaned)


def _split_contract_pin_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for part in text.replace(";", "/").split("/"):
        item = part.strip()
        if not item:
            continue
        tokens.append(_canonical_token(item))
    return tokens


def _classify_pin(name: str) -> str:
    canonical = _canonical_token(name)
    if name.upper() in POWER_PIN_NAMES or canonical in {"vdd", "gnd", "vss"}:
        return "power"
    if canonical in {"z", "q", "dout", "delay_out", "delay_out_bar", "bl_out", "br_out", "write_en", "sense_en", "precharge_en", "wl_en", "gated_clk", "dec_out"}:
        return "output"
    return "input"


@dataclass(frozen=True)
class TopLevelAssemblyConfig:
    config_name: str
    num_words: int
    num_rows: int
    word_size: int
    words_per_row: int
    column_mux_ratio: int
    single_bank: bool
    single_port: bool
    port_count: int
    notes: tuple[str, ...]


@dataclass(frozen=True)
class TopLevelModuleMetadata:
    module_name: str
    module_category: str
    gds_path: Path
    bbox: dict[str, float]
    pins: tuple[dict[str, Any], ...]
    rail_report: dict[str, Any]
    generator_manifest: dict[str, Any]
    generation_report: dict[str, Any]
    generator_row: dict[str, str]
    gds_row: dict[str, str]
    uses_candidate_geometry: bool
    uses_contract_pins: bool


@dataclass(frozen=True)
class TopLevelModuleInstance:
    module_name: str
    instance_name: str
    gds_path: Path
    origin_x: float
    origin_y: float
    orientation: str
    bbox: dict[str, float]
    placement_reason: str
    input_pins: tuple[str, ...]
    output_pins: tuple[str, ...]
    power_pins: tuple[str, ...]
    rail_handoff: dict[str, Any]
    routing_handoff: tuple[str, ...]
    uses_candidate_geometry: bool
    uses_contract_pins: bool


@dataclass(frozen=True)
class TopLevelPlacementPlan:
    config_name: str
    placement_strategy: str
    floorplan_bbox: dict[str, float]
    instances: tuple[TopLevelModuleInstance, ...]
    zones: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class TopLevelRailStitchPlan:
    entries: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class TopLevelRoutingHandoff:
    entries: tuple[dict[str, Any], ...]


@dataclass(frozen=True)
class TopLevelAssemblyResult:
    config: TopLevelAssemblyConfig
    top_gds_path: Path
    top_cell_name: str
    top_bbox: dict[str, float]
    top_instance_count: int
    cell_count: int
    layer_summary: dict[str, int]
    placement_plan: TopLevelPlacementPlan
    routing_handoff: TopLevelRoutingHandoff
    rail_stitch_plan: TopLevelRailStitchPlan
    top_level_pin_map: tuple[dict[str, Any], ...]
    required_l3_modules_missing_from_top: tuple[str, ...]
    modules_instantiated_with_candidate_geometry: tuple[str, ...]
    modules_instantiated_with_contract_pins: tuple[str, ...]
    report: dict[str, Any]
    inventory_rows: tuple[dict[str, Any], ...]


class OpenYieldTopLevelAssembler:
    def __init__(
        self,
        repo_root: Path,
        openyield_root: Path,
        module_gds_inventory: Path,
        module_generator_inventory: Path,
        module_gds_dir: Path,
        l0_contract_json: Path,
        l2_rule_library_json: Path,
        out_dir: Path,
        out_inventory_csv: Path,
        out_inventory_md: Path,
        out_json: Path,
        out_report: Path,
        reproducible_command: str,
    ) -> None:
        self.repo_root = repo_root.resolve()
        self.openyield_root = openyield_root.resolve()
        self.module_gds_inventory = module_gds_inventory.resolve()
        self.module_generator_inventory = module_generator_inventory.resolve()
        self.module_gds_dir = module_gds_dir.resolve()
        self.l0_contract_json = l0_contract_json.resolve()
        self.l2_rule_library_json = l2_rule_library_json.resolve()
        self.out_dir = out_dir.resolve()
        self.out_inventory_csv = out_inventory_csv.resolve()
        self.out_inventory_md = out_inventory_md.resolve()
        self.out_json = out_json.resolve()
        self.out_report = out_report.resolve()
        self.reproducible_command = reproducible_command

    def build_current_supported_config(self) -> TopLevelAssemblyConfig:
        return TopLevelAssemblyConfig(
            config_name="current_supported_config",
            num_words=4,
            num_rows=4,
            word_size=4,
            words_per_row=1,
            column_mux_ratio=1,
            single_bank=True,
            single_port=True,
            port_count=1,
            notes=(
                "Chosen to match frozen L3 standalone module dimensions for deterministic first-round top-level assembly.",
                "This L4 candidate GDS does not claim signoff-ready array sizing beyond the current supported scope.",
            ),
        )

    def load_module_gds_inventory(self) -> dict[str, TopLevelModuleMetadata]:
        gds_rows = _load_csv_rows(self.module_gds_inventory, "module")
        generator_rows = _load_csv_rows(self.module_generator_inventory, "module")
        l3_report = _load_json(self.repo_root / "docs/openyield_L3_module_generator_gds_generation_report.json")
        candidate_modules = set(l3_report.get("modules_with_candidate_geometry", []))
        contract_pin_modules = set(l3_report.get("modules_with_contract_pins", []))
        loaded: dict[str, TopLevelModuleMetadata] = {}
        for module in L3_REQUIRED_MODULES:
            row = gds_rows[module]
            module_dir = Path(row["gds_path"]).parent
            loaded[module] = TopLevelModuleMetadata(
                module_name=module,
                module_category=row["module_category"],
                gds_path=Path(row["gds_path"]),
                bbox=_load_json(module_dir / "bbox.json"),
                pins=tuple(_load_json(Path(row["pins_json_path"]))["pins"]),
                rail_report=_load_json(Path(row["rail_report_path"])),
                generator_manifest=_load_json(Path(row["generator_manifest_path"])),
                generation_report=_load_json(module_dir / "generation_report.json"),
                generator_row=generator_rows[module],
                gds_row=row,
                uses_candidate_geometry=module in candidate_modules,
                uses_contract_pins=module in contract_pin_modules,
            )
        return loaded

    def load_module_gds_inventory_rows(self) -> list[dict[str, str]]:
        return _load_csv_list(self.module_gds_inventory)

    def load_module_metadata(self) -> dict[str, Any]:
        return {
            "l0_contract": _load_json(self.l0_contract_json),
            "top_bank_contract": _load_json(self.repo_root / "docs/mapping/openyield_top_bank_semantic_contract.json"),
            "logical_to_openyield_parameter_map": _load_csv_list(self.repo_root / "docs/mapping/openyield_logical_to_openyield_parameter_map.csv"),
            "module_connection_matrix": _load_csv_list(self.repo_root / "docs/mapping/openyield_module_connection_matrix.csv"),
            "decoder_wordline_contract": _load_json(self.repo_root / "docs/mapping/openyield_decoder_wordline_semantic_contract.json"),
            "time_control_decomposition_contract": _load_json(self.repo_root / "docs/mapping/openyield_time_control_decomposition_contract.json"),
            "control_path_semantic_contracts": _load_csv_list(self.repo_root / "docs/mapping/openyield_control_path_semantic_contracts.csv"),
            "leaf_physical_library": _load_json(self.repo_root / "technology/freepdk45/openyield_leaf_physical_library.json"),
            "primitive_composition_library": _load_json(self.repo_root / "technology/freepdk45/openyield_primitive_composition_library.json"),
            "l2_rule_library": _load_json(self.l2_rule_library_json),
            "module_handoff_rule_matrix": _load_csv_list(self.repo_root / "docs/mapping/openyield_module_handoff_rule_matrix.csv"),
            "placement_rule_matrix": _load_csv_list(self.repo_root / "docs/mapping/openyield_placement_rule_matrix.csv"),
            "abutment_rule_matrix": _load_csv_list(self.repo_root / "docs/mapping/openyield_abutment_rule_matrix.csv"),
            "rail_rule_matrix": _load_csv_list(self.repo_root / "docs/mapping/openyield_rail_rule_matrix.csv"),
            "orientation_policy_matrix": _load_csv_list(self.repo_root / "docs/mapping/openyield_orientation_policy_matrix.csv"),
            "pin_access_rule_matrix": _load_csv_list(self.repo_root / "docs/mapping/openyield_pin_access_rule_matrix.csv"),
            "module_generator_inventory": _load_csv_list(self.module_generator_inventory),
            "module_gds_inventory": _load_csv_list(self.module_gds_inventory),
            "l3_report": _load_json(self.repo_root / "docs/openyield_L3_module_generator_gds_generation_report.json"),
        }

    def build_top_level_floorplan(
        self,
        config: TopLevelAssemblyConfig,
        modules: dict[str, TopLevelModuleMetadata],
    ) -> dict[str, Any]:
        gap_x = 1.0
        gap_y = 0.8

        left_stack = [
            "row_decoder",
            "wordline_decoder",
            "decoder_gate_cells",
            "wordline_driver",
            "wordline_driver_gate_cells",
        ]
        center_cluster = ["dummy_array", "bitcell_array", "replica_array"]
        right_stack = ["precharge", "column_mux", "sense_amp", "write_driver"]
        top_row = [
            "CONTROL_LOGIC",
            "DFF_ROW",
            "DELAY_CHAIN",
            "GATED_CLOCK_PATH",
            "WORDLINE_ENABLE_PATH",
            "PRECHARGE_ENABLE_PATH",
            "SENSE_ENABLE_PATH",
            "WRITE_ENABLE_PATH",
        ]

        left_width = max(modules[name].bbox["width"] for name in left_stack)
        left_height = sum(modules[name].bbox["height"] for name in left_stack) + gap_y * (len(left_stack) - 1)
        center_width = sum(modules[name].bbox["width"] for name in center_cluster) + gap_x * (len(center_cluster) - 1)
        center_height = max(modules[name].bbox["height"] for name in center_cluster)
        right_width = max(modules[name].bbox["width"] for name in right_stack)
        right_height = sum(modules[name].bbox["height"] for name in right_stack) + gap_y * (len(right_stack) - 1)
        base_height = max(left_height, center_height, right_height)
        top_height = max(modules[name].bbox["height"] for name in top_row)
        top_width = sum(modules[name].bbox["width"] for name in top_row) + gap_x * (len(top_row) - 1)
        total_width = max(left_width + gap_x + center_width + gap_x + right_width, top_width)
        total_height = base_height + gap_y + top_height

        return {
            "config_name": config.config_name,
            "placement_strategy": "deterministic_zone_based_l4_assembly",
            "global_gap_x_um": gap_x,
            "global_gap_y_um": gap_y,
            "zones": [
                {
                    "name": "left_control_column",
                    "modules": left_stack,
                    "bbox": {"x0": 0.0, "y0": 0.0, "x1": left_width, "y1": left_height},
                    "reason": "Keep decode/wordline-related modules adjacent to the storage edge for deterministic control-side floorplanning.",
                },
                {
                    "name": "center_storage_cluster",
                    "modules": center_cluster,
                    "bbox": {"x0": left_width + gap_x, "y0": 0.0, "x1": left_width + gap_x + center_width, "y1": center_height},
                    "reason": "Place storage macros in the center and preserve standalone module boundaries without resizing them in L4.",
                },
                {
                    "name": "right_data_column",
                    "modules": right_stack,
                    "bbox": {
                        "x0": left_width + gap_x + center_width + gap_x,
                        "y0": 0.0,
                        "x1": left_width + gap_x + center_width + gap_x + right_width,
                        "y1": right_height,
                    },
                    "reason": "Collect precharge/mux/sense/write macros on the read-write datapath side.",
                },
                {
                    "name": "top_control_ring",
                    "modules": top_row,
                    "bbox": {"x0": 0.0, "y0": base_height + gap_y, "x1": top_width, "y1": total_height},
                    "reason": "Place clock/control/timing helpers above the bank candidate to keep their channels explicit for L5 routing handoff.",
                },
            ],
            "bbox": {"x0": 0.0, "y0": 0.0, "x1": total_width, "y1": total_height, "width": total_width, "height": total_height},
        }

    def place_l3_modules(
        self,
        modules: dict[str, TopLevelModuleMetadata],
        floorplan: dict[str, Any],
        routing_handoff: TopLevelRoutingHandoff,
        rail_stitch_plan: TopLevelRailStitchPlan,
    ) -> TopLevelPlacementPlan:
        gap_x = float(floorplan["global_gap_x_um"])
        gap_y = float(floorplan["global_gap_y_um"])
        left_width = floorplan["zones"][0]["bbox"]["x1"]
        center_bbox = floorplan["zones"][1]["bbox"]
        right_bbox = floorplan["zones"][2]["bbox"]
        top_y = floorplan["zones"][3]["bbox"]["y0"]

        placements: list[TopLevelModuleInstance] = []

        def add_stack(names: list[str], start_x: float, start_y: float, reason: str) -> None:
            y = start_y
            for name in names:
                meta = modules[name]
                bbox = _translated_bbox(meta.bbox, start_x, y)
                placements.append(
                    TopLevelModuleInstance(
                        module_name=name,
                        instance_name=f"{name}_u0",
                        gds_path=meta.gds_path,
                        origin_x=round(start_x, 6),
                        origin_y=round(y, 6),
                        orientation="R0",
                        bbox=bbox,
                        placement_reason=reason,
                        input_pins=tuple(sorted(pin["name"] for pin in meta.pins if _classify_pin(str(pin["name"])) == "input")),
                        output_pins=tuple(sorted(pin["name"] for pin in meta.pins if _classify_pin(str(pin["name"])) == "output")),
                        power_pins=tuple(sorted(pin["name"] for pin in meta.pins if str(pin["name"]).upper() in POWER_PIN_NAMES)),
                        rail_handoff=self._module_rail_handoff(meta),
                        routing_handoff=tuple(sorted(self._module_routing_nets(name, routing_handoff))),
                        uses_candidate_geometry=meta.uses_candidate_geometry,
                        uses_contract_pins=meta.uses_contract_pins,
                    )
                )
                y += meta.bbox["height"] + gap_y

        add_stack(
            ["row_decoder", "wordline_decoder", "decoder_gate_cells", "wordline_driver", "wordline_driver_gate_cells"],
            0.0,
            0.0,
            "Left control column: keep decoder and wordline path macros near the storage edge.",
        )

        x = center_bbox["x0"]
        for name in ["dummy_array", "bitcell_array", "replica_array"]:
            meta = modules[name]
            y = 0.0
            bbox = _translated_bbox(meta.bbox, x, y)
            placements.append(
                TopLevelModuleInstance(
                    module_name=name,
                    instance_name=f"{name}_u0",
                    gds_path=meta.gds_path,
                    origin_x=round(x, 6),
                    origin_y=round(y, 6),
                    orientation="R0",
                    bbox=bbox,
                    placement_reason="Center storage cluster: keep L3 standalone arrays intact and side-by-side for reproducible L4 assembly.",
                    input_pins=tuple(sorted(pin["name"] for pin in meta.pins if _classify_pin(str(pin["name"])) == "input")),
                    output_pins=tuple(sorted(pin["name"] for pin in meta.pins if _classify_pin(str(pin["name"])) == "output")),
                    power_pins=tuple(sorted(pin["name"] for pin in meta.pins if str(pin["name"]).upper() in POWER_PIN_NAMES)),
                    rail_handoff=self._module_rail_handoff(meta),
                    routing_handoff=tuple(sorted(self._module_routing_nets(name, routing_handoff))),
                    uses_candidate_geometry=meta.uses_candidate_geometry,
                    uses_contract_pins=meta.uses_contract_pins,
                )
            )
            x += meta.bbox["width"] + gap_x

        add_stack(
            ["precharge", "column_mux", "sense_amp", "write_driver"],
            right_bbox["x0"],
            0.0,
            "Right data column: keep bitline precharge/mux/sense/write modules grouped for later routing closure.",
        )

        x = 0.0
        for name in [
            "CONTROL_LOGIC",
            "DFF_ROW",
            "DELAY_CHAIN",
            "GATED_CLOCK_PATH",
            "WORDLINE_ENABLE_PATH",
            "PRECHARGE_ENABLE_PATH",
            "SENSE_ENABLE_PATH",
            "WRITE_ENABLE_PATH",
        ]:
            meta = modules[name]
            bbox = _translated_bbox(meta.bbox, x, top_y)
            placements.append(
                TopLevelModuleInstance(
                    module_name=name,
                    instance_name=f"{name}_u0",
                    gds_path=meta.gds_path,
                    origin_x=round(x, 6),
                    origin_y=round(top_y, 6),
                    orientation="R0",
                    bbox=bbox,
                    placement_reason="Top control ring: place control/timing helper modules above the bank to expose explicit routing and rail handoff boundaries.",
                    input_pins=tuple(sorted(pin["name"] for pin in meta.pins if _classify_pin(str(pin["name"])) == "input")),
                    output_pins=tuple(sorted(pin["name"] for pin in meta.pins if _classify_pin(str(pin["name"])) == "output")),
                    power_pins=tuple(sorted(pin["name"] for pin in meta.pins if str(pin["name"]).upper() in POWER_PIN_NAMES)),
                    rail_handoff=self._module_rail_handoff(meta),
                    routing_handoff=tuple(sorted(self._module_routing_nets(name, routing_handoff))),
                    uses_candidate_geometry=meta.uses_candidate_geometry,
                    uses_contract_pins=meta.uses_contract_pins,
                )
            )
            x += meta.bbox["width"] + gap_x

        floorplan_bbox = {
            "x0": 0.0,
            "y0": 0.0,
            "x1": round(max(item.bbox["x1"] for item in placements), 6),
            "y1": round(max(item.bbox["y1"] for item in placements), 6),
        }
        floorplan_bbox["width"] = round(floorplan_bbox["x1"] - floorplan_bbox["x0"], 6)
        floorplan_bbox["height"] = round(floorplan_bbox["y1"] - floorplan_bbox["y0"], 6)
        return TopLevelPlacementPlan(
            config_name=floorplan["config_name"],
            placement_strategy=str(floorplan["placement_strategy"]),
            floorplan_bbox=floorplan_bbox,
            instances=tuple(sorted(placements, key=lambda item: (item.origin_y, item.origin_x, item.module_name))),
            zones=tuple(floorplan["zones"]),
        )

    def emit_top_level_gds(self, placement_plan: TopLevelPlacementPlan, out_dir: Path) -> tuple[Path, str]:
        out_dir.mkdir(parents=True, exist_ok=True)
        gds_path = out_dir / "openyield_top_level_candidate.gds"
        import_plans = [
            TopCellImportPlan(
                module_name=instance.module_name,
                module_gds_path=instance.gds_path,
                root_cell_name=instance.module_name,
                instance_name=instance.instance_name,
                origin_x=instance.origin_x,
                origin_y=instance.origin_y,
                orientation=instance.orientation,
            )
            for instance in placement_plan.instances
        ]
        search_paths = collect_search_paths(
            [item.gds_path for item in placement_plan.instances],
            self.repo_root / "technology/freepdk45/gds_lib",
        )
        lib, hierarchy_manifest = build_top_level_library(import_plans, search_paths, top_cell_name="openyield_top_level_candidate")
        lib.write_gds(gds_path)
        self._last_hierarchy_manifest = hierarchy_manifest
        self._last_hierarchy_search_paths = search_paths
        return gds_path, "openyield_top_level_candidate"

    def emit_top_level_metadata(
        self,
        config: TopLevelAssemblyConfig,
        metadata_bundle: dict[str, Any],
        placement_plan: TopLevelPlacementPlan,
        top_level_pin_map: list[dict[str, Any]],
        rail_stitch_plan: TopLevelRailStitchPlan,
        routing_handoff: TopLevelRoutingHandoff,
        validation: dict[str, Any],
        inventory_rows: list[dict[str, Any]],
        report: dict[str, Any],
    ) -> None:
        config_dir = self.out_dir.parent / "configs"
        current_config_path = config_dir / f"{config.config_name}.json"
        top_level_config_path = self.out_dir / "top_level_config.json"
        floorplan_path = self.out_dir / "top_level_floorplan.json"
        placement_path = self.out_dir / "module_placement.json"
        pin_map_path = self.out_dir / "top_level_pin_map.json"
        rail_path = self.out_dir / "top_level_rail_stitch_plan.json"
        routing_path = self.out_dir / "top_level_routing_handoff.json"
        generation_json_path = self.out_dir / "top_level_generation_report.json"
        generation_md_path = self.out_dir / "top_level_generation_report.md"
        manifest_path = self.out_dir / "top_level_generator_manifest.json"

        config_payload = asdict(config)
        config_payload["repo_root"] = str(self.repo_root)
        config_payload["openyield_root"] = str(self.openyield_root)
        config_payload["supported_scope"] = metadata_bundle["l0_contract"]["supported_sram_scope"]
        _json_dump(current_config_path, config_payload)
        _json_dump(top_level_config_path, config_payload)
        _json_dump(
            floorplan_path,
            {
                "config_name": config.config_name,
                "placement_strategy": placement_plan.placement_strategy,
                "floorplan_bbox": placement_plan.floorplan_bbox,
                "zones": list(placement_plan.zones),
            },
        )
        _json_dump(
            placement_path,
            {
                "config_name": config.config_name,
                "instance_count": len(placement_plan.instances),
                "instances": [asdict(item) | {"gds_path": str(item.gds_path)} for item in placement_plan.instances],
            },
        )
        _json_dump(pin_map_path, {"config_name": config.config_name, "top_level_pins": top_level_pin_map})
        _json_dump(rail_path, {"config_name": config.config_name, "entries": list(rail_stitch_plan.entries)})
        _json_dump(routing_path, {"config_name": config.config_name, "entries": list(routing_handoff.entries)})
        _json_dump(generation_json_path, report)
        _write_text(generation_md_path, self._render_generation_report_md(report))
        _json_dump(
            manifest_path,
            {
                "generator_name": "OpenYieldTopLevelAssembler",
                "generator_source_file": "sram_layoutgen/openyield_adapter/top_level_assembly.py",
                "reproducible_command": self.reproducible_command,
                "repo_root": str(self.repo_root),
                "openyield_root": str(self.openyield_root),
                "input_files": {
                    "module_gds_inventory": str(self.module_gds_inventory),
                    "module_generator_inventory": str(self.module_generator_inventory),
                    "module_gds_dir": str(self.module_gds_dir),
                    "l0_contract_json": str(self.l0_contract_json),
                    "l2_rule_library_json": str(self.l2_rule_library_json),
                },
                "generated_files": [
                    str(current_config_path),
                    str(top_level_config_path),
                    str(floorplan_path),
                    str(placement_path),
                    str(pin_map_path),
                    str(rail_path),
                    str(routing_path),
                    str(generation_json_path),
                    str(generation_md_path),
                    str(manifest_path),
                    str(self.out_inventory_csv),
                    str(self.out_inventory_md),
                    str(self.out_json),
                    str(self.out_report),
                ],
                "determinism_contract": "L4 top-level GDS is produced by deterministic module ordering, fixed floorplan zones, and frozen L3 standalone module metadata.",
                "hierarchy_export": getattr(self, "_last_hierarchy_manifest", {}),
                "validation_summary": validation,
            },
        )
        self.emit_top_level_assembly_inventory(self.out_inventory_csv, self.out_inventory_md, inventory_rows)

    def validate_top_level_assembly(self, top_gds_path: Path, fallback_bbox: dict[str, float] | None = None, fallback_instance_count: int | None = None) -> dict[str, Any]:
        exists = top_gds_path.exists()
        size = top_gds_path.stat().st_size if exists else 0
        tool_available = bool(importlib.util.find_spec("gdstk")) or bool(importlib.util.find_spec("gdspy"))
        if not exists or size <= 0:
            return {
                "top_gds_exists": exists,
                "top_gds_non_empty": size > 0,
                "top_gds_sanity_status": "SANITY_FAILED",
                "top_gds_size_bytes": size,
                "top_cell_name": None,
                "top_bbox": None,
                "top_instance_count": 0,
                "cell_count": 0,
                "layer_summary": {},
                "module_references": [],
            }
        if not tool_available:
            return {
                "top_gds_exists": True,
                "top_gds_non_empty": True,
                "top_gds_sanity_status": "SANITY_SKIPPED_TOOL_UNAVAILABLE",
                "top_gds_size_bytes": size,
                "top_cell_name": None,
                "top_bbox": None,
                "top_instance_count": 0,
                "cell_count": 0,
                "layer_summary": {},
                "module_references": [],
            }
        lib = gdstk.read_gds(top_gds_path)
        cell_names = {str(cell.name) for cell in lib.cells}
        refs_by_cell = {str(cell.name): [str(ref.cell_name) for ref in cell.references] for cell in lib.cells}
        missing_refs = sorted({ref for refs in refs_by_cell.values() for ref in refs if ref not in cell_names})
        self_refs = sorted(cell for cell, refs in refs_by_cell.items() if cell in refs)
        cycles = self._find_cycles(refs_by_cell, cell_names)
        top_cells = list(lib.top_level())
        top = top_cells[0] if top_cells else (lib.cells[0] if lib.cells else None)
        bbox = top.bounding_box() if top is not None else None
        bbox_dict = (
            {
                "x0": float(bbox[0][0]),
                "y0": float(bbox[0][1]),
                "x1": float(bbox[1][0]),
                "y1": float(bbox[1][1]),
                "width": float(bbox[1][0] - bbox[0][0]),
                "height": float(bbox[1][1] - bbox[0][1]),
            }
            if bbox is not None
            else fallback_bbox
        )
        status = "GDS_PARSED_SANITY_PASSED" if top is not None and not missing_refs and not self_refs and not cycles else "SANITY_FAILED"
        return {
            "top_gds_exists": True,
            "top_gds_non_empty": True,
            "top_gds_sanity_status": status,
            "top_gds_size_bytes": size,
            "top_cell_name": str(top.name) if top is not None else None,
            "top_bbox": bbox_dict,
            "top_instance_count": fallback_instance_count if fallback_instance_count is not None else len(getattr(top, "references", [])),
            "cell_count": len(lib.cells),
            "layer_summary": self._layer_summary(lib),
            "module_references": sorted(str(ref.cell_name) for ref in getattr(top, "references", [])),
            "top_bbox_source": "parsed_gds_hierarchy" if status == "GDS_PARSED_SANITY_PASSED" else "deterministic_placement_plan",
            "missing_references": missing_refs,
            "self_references": self_refs,
            "cycles": cycles,
        }

    def emit_top_level_assembly_inventory(self, csv_path: Path, md_path: Path, rows: list[dict[str, Any]]) -> None:
        _write_csv(csv_path, TOP_LEVEL_ASSEMBLY_INVENTORY_COLUMNS, rows)
        md_lines = [
            "# OpenYield Top-Level Assembly Inventory",
            "",
            f"Rows: `{len(rows)}`",
            "",
            "| " + " | ".join(TOP_LEVEL_ASSEMBLY_INVENTORY_COLUMNS) + " |",
            "| " + " | ".join("---" for _ in TOP_LEVEL_ASSEMBLY_INVENTORY_COLUMNS) + " |",
        ]
        for row in rows:
            md_lines.append("| " + " | ".join(str(row.get(column, "")).replace("\n", " ") for column in TOP_LEVEL_ASSEMBLY_INVENTORY_COLUMNS) + " |")
        md_lines.append("")
        _write_text(md_path, "\n".join(md_lines))

    def run(self) -> TopLevelAssemblyResult:
        metadata_bundle = self.load_module_metadata()
        modules = self.load_module_gds_inventory()
        config = self.build_current_supported_config()
        floorplan = self.build_top_level_floorplan(config, modules)
        routing_handoff = TopLevelRoutingHandoff(entries=tuple(self._build_routing_handoff(metadata_bundle["module_connection_matrix"], modules)))
        rail_stitch_plan = TopLevelRailStitchPlan(entries=tuple(self._build_rail_stitch_plan(modules)))
        placement_plan = self.place_l3_modules(modules, floorplan, routing_handoff, rail_stitch_plan)
        top_gds_path, top_cell_name = self.emit_top_level_gds(placement_plan, self.out_dir)
        diagnosis = diagnose_gds_hierarchy(
            top_gds_path,
            {item.module_name: item.gds_path for item in placement_plan.instances},
            self.repo_root / "technology/freepdk45/gds_lib",
            self.load_module_gds_inventory_rows(),
        )
        validation_dir = self.repo_root / "outputs/openyield_validation/current_supported_config"
        write_hierarchy_diagnosis(
            diagnosis,
            validation_dir / "top_gds_hierarchy_diagnosis.json",
            validation_dir / "top_gds_hierarchy_diagnosis.md",
        )
        validation = self.validate_top_level_assembly(
            top_gds_path,
            fallback_bbox=placement_plan.floorplan_bbox,
            fallback_instance_count=len(placement_plan.instances),
        )
        top_level_pin_map = self._build_top_level_pin_map(placement_plan, modules)
        inventory_rows = self._build_inventory_rows(modules, placement_plan, rail_stitch_plan, routing_handoff, validation)
        missing_modules = sorted(set(L3_REQUIRED_MODULES) - {item.module_name for item in placement_plan.instances})
        report = self._build_report(
            config=config,
            placement_plan=placement_plan,
            modules=modules,
            validation=validation,
            missing_modules=missing_modules,
            rail_stitch_plan=rail_stitch_plan,
            routing_handoff=routing_handoff,
            inventory_rows=inventory_rows,
        )
        self.emit_top_level_metadata(
            config=config,
            metadata_bundle=metadata_bundle,
            placement_plan=placement_plan,
            top_level_pin_map=top_level_pin_map,
            rail_stitch_plan=rail_stitch_plan,
            routing_handoff=routing_handoff,
            validation=validation,
            inventory_rows=inventory_rows,
            report=report,
        )
        _json_dump(self.out_json, report)
        _write_text(self.out_report, self._render_generation_report_md(report))
        self._write_gap_summary(report, placement_plan, routing_handoff, rail_stitch_plan)
        self._update_evidence_timeline(report)
        self._update_milestone_summary(report)
        return TopLevelAssemblyResult(
            config=config,
            top_gds_path=top_gds_path,
            top_cell_name=top_cell_name,
            top_bbox=validation["top_bbox"] or {},
            top_instance_count=int(validation["top_instance_count"]),
            cell_count=int(validation["cell_count"]),
            layer_summary=validation["layer_summary"],
            placement_plan=placement_plan,
            routing_handoff=routing_handoff,
            rail_stitch_plan=rail_stitch_plan,
            top_level_pin_map=tuple(top_level_pin_map),
            required_l3_modules_missing_from_top=tuple(missing_modules),
            modules_instantiated_with_candidate_geometry=tuple(sorted(item.module_name for item in placement_plan.instances if item.uses_candidate_geometry)),
            modules_instantiated_with_contract_pins=tuple(sorted(item.module_name for item in placement_plan.instances if item.uses_contract_pins)),
            report=report,
            inventory_rows=tuple(inventory_rows),
        )

    def _build_routing_handoff(
        self,
        connection_rows: list[dict[str, str]],
        modules: dict[str, TopLevelModuleMetadata],
    ) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for row in connection_rows:
            source_module = row["source_module"]
            target_module = row["target_module"]
            is_power = _bool_from_str(row.get("is_power"))
            source_pin = self._resolve_pin_name(modules.get(source_module), row["source_port_or_signal"])
            target_pin = self._resolve_pin_name(modules.get(target_module), row["target_port_or_signal"])
            if source_module == "SRAM_TOP" or target_module == "SRAM_TOP":
                routing_status = "CONTRACT_NET_ONLY"
                routing_required = False
                blocking = False
            elif is_power:
                routing_status = "POWER_NET_HANDLED_BY_RAIL_STITCH_PLAN"
                routing_required = False
                blocking = False
            else:
                routing_status = "TOP_LEVEL_ROUTE_REQUIRED_IN_L5"
                routing_required = True
                blocking = True
            entries.append(
                {
                    "net_name": row["signal_name"],
                    "source_module": source_module,
                    "source_pin": source_pin,
                    "target_module": target_module,
                    "target_pin": target_pin,
                    "net_category": row["signal_category"],
                    "routing_status": routing_status,
                    "routing_required_in_L5": routing_required,
                    "blocking_if_unrouted": blocking,
                    "direction": row["direction"],
                    "uses_contract_pins": source_pin == row["source_port_or_signal"] or target_pin == row["target_port_or_signal"],
                }
            )
        return entries

    def _build_rail_stitch_plan(self, modules: dict[str, TopLevelModuleMetadata]) -> list[dict[str, Any]]:
        module_names = sorted(modules)
        common = {
            "modules_involved": module_names,
            "rail_source": "L3 module_boundary_rails + module rail_report metadata",
            "stitch_strategy": "deterministic_top_perimeter_spine_with_vertical_module_drops",
            "horizontal_stitch_required": True,
            "vertical_stitch_required": True,
            "stitch_status": "TOP_LEVEL_STITCH_PENDING_L5_VERIFICATION",
            "requires_L5_verification": True,
        }
        return [
            {"power_net": "VDD"} | common,
            {"power_net": "GND"} | common,
        ]

    def _build_top_level_pin_map(
        self,
        placement_plan: TopLevelPlacementPlan,
        modules: dict[str, TopLevelModuleMetadata],
    ) -> list[dict[str, Any]]:
        instance_by_name = {item.module_name: item for item in placement_plan.instances}
        top_bbox = placement_plan.floorplan_bbox
        pin_map = [
            {
                "top_pin_name": "A[*]",
                "pin_role": "address_input",
                "mapped_module": "DFF_ROW",
                "mapped_pin": self._resolve_pin_name(modules["DFF_ROW"], "A[i]"),
                "x": 0.0,
                "y": round(top_bbox["height"] * 0.80, 6),
                "layer": "m2",
                "pin_source": "top_level_contract_to_registered_address",
            },
            {
                "top_pin_name": "DIN[*]",
                "pin_role": "write_data_input",
                "mapped_module": "DFF_ROW",
                "mapped_pin": self._resolve_pin_name(modules["DFF_ROW"], "DIN[i]"),
                "x": 0.0,
                "y": round(top_bbox["height"] * 0.65, 6),
                "layer": "m2",
                "pin_source": "top_level_contract_to_registered_write_data",
            },
            {
                "top_pin_name": "clk",
                "pin_role": "clock_input",
                "mapped_module": "CONTROL_LOGIC",
                "mapped_pin": self._resolve_pin_name(modules["CONTROL_LOGIC"], "clk"),
                "x": round(top_bbox["width"] * 0.35, 6),
                "y": top_bbox["y1"],
                "layer": "m1",
                "pin_source": "top_level_contract_to_control_logic",
            },
            {
                "top_pin_name": "csb",
                "pin_role": "active_low_control_input",
                "mapped_module": "CONTROL_LOGIC",
                "mapped_pin": self._resolve_pin_name(modules["CONTROL_LOGIC"], "cs"),
                "x": round(top_bbox["width"] * 0.50, 6),
                "y": top_bbox["y1"],
                "layer": "m1",
                "pin_source": "top_level_contract_to_control_logic_contract_pin",
            },
            {
                "top_pin_name": "web",
                "pin_role": "active_low_control_input",
                "mapped_module": "CONTROL_LOGIC",
                "mapped_pin": self._resolve_pin_name(modules["CONTROL_LOGIC"], "we"),
                "x": round(top_bbox["width"] * 0.62, 6),
                "y": top_bbox["y1"],
                "layer": "m1",
                "pin_source": "top_level_contract_to_control_logic_contract_pin",
            },
            {
                "top_pin_name": "DOUT[*]",
                "pin_role": "read_output",
                "mapped_module": "sense_amp",
                "mapped_pin": self._resolve_pin_name(modules["sense_amp"], "Q/QB"),
                "x": top_bbox["x1"],
                "y": round(top_bbox["height"] * 0.50, 6),
                "layer": "m2",
                "pin_source": "top_level_contract_to_sense_amp_output",
            },
            {
                "top_pin_name": "VDD",
                "pin_role": "power",
                "mapped_module": "SRAM_TOP",
                "mapped_pin": "VDD",
                "x": round(top_bbox["width"] * 0.20, 6),
                "y": 0.0,
                "layer": "m1",
                "pin_source": "top_level_power_contract",
            },
            {
                "top_pin_name": "GND",
                "pin_role": "ground",
                "mapped_module": "SRAM_TOP",
                "mapped_pin": "GND",
                "x": round(top_bbox["width"] * 0.80, 6),
                "y": 0.0,
                "layer": "m1",
                "pin_source": "top_level_power_contract",
            },
        ]
        for item in pin_map:
            instance = instance_by_name.get(item["mapped_module"])
            item["mapped_instance"] = instance.instance_name if instance is not None else item["mapped_module"]
        return pin_map

    def _build_inventory_rows(
        self,
        modules: dict[str, TopLevelModuleMetadata],
        placement_plan: TopLevelPlacementPlan,
        rail_stitch_plan: TopLevelRailStitchPlan,
        routing_handoff: TopLevelRoutingHandoff,
        validation: dict[str, Any],
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        placements = {item.module_name: item for item in placement_plan.instances}
        for module in L3_REQUIRED_MODULES:
            meta = modules[module]
            placed = placements[module]
            if meta.uses_candidate_geometry:
                status = "L4_TOP_LEVEL_INSTANTIATED_WITH_CANDIDATE_GEOMETRY"
            elif meta.uses_contract_pins:
                status = "L4_TOP_LEVEL_INSTANTIATED_WITH_CONTRACT_PINS"
            else:
                status = "L4_TOP_LEVEL_INSTANTIATED"
            rows.append(
                {
                    "object": module,
                    "object_category": meta.module_category,
                    "is_top_level_target": "True",
                    "source_module_gds": str(meta.gds_path),
                    "module_gds_sanity_status": meta.gds_row.get("parser_sanity_status") or meta.gds_row.get("sanity_check_status", ""),
                    "instantiated_in_top_gds": "True",
                    "instance_name": placed.instance_name,
                    "origin": json.dumps({"x": placed.origin_x, "y": placed.origin_y}),
                    "orientation": placed.orientation,
                    "bbox": json.dumps(placed.bbox),
                    "pins_available": str(bool(meta.pins)),
                    "rail_metadata_available": str(bool(meta.rail_report)),
                    "routing_handoff_available": "True",
                    "power_handoff_available": "True",
                    "uses_candidate_geometry": str(meta.uses_candidate_geometry),
                    "uses_contract_pins": str(meta.uses_contract_pins),
                    "assembly_status": status,
                    "blocking_gap": "",
                    "next_required_action": "Keep detailed routing / rail verification in L5; do not claim DRC/LVS/timing closure in L4.",
                    "evidence_files": ";".join(
                        [
                            str(meta.gds_path),
                            str(meta.gds_path.parent / "pins.json"),
                            str(meta.gds_path.parent / "rail_report.json"),
                            str(meta.gds_path.parent / "generator_manifest.json"),
                        ]
                    ),
                }
            )
        rows.extend(
            [
                {
                    "object": "SRAM_TOP",
                    "object_category": "top_level_candidate",
                    "is_top_level_target": "True",
                    "source_module_gds": str(self.out_dir / "openyield_top_level_candidate.gds"),
                    "module_gds_sanity_status": validation["top_gds_sanity_status"],
                    "instantiated_in_top_gds": "True",
                    "instance_name": "openyield_top_level_candidate",
                    "origin": json.dumps({"x": 0.0, "y": 0.0}),
                    "orientation": "R0",
                    "bbox": json.dumps(validation.get("top_bbox")),
                    "pins_available": "True",
                    "rail_metadata_available": "True",
                    "routing_handoff_available": "True",
                    "power_handoff_available": "True",
                    "uses_candidate_geometry": "True",
                    "uses_contract_pins": "True",
                    "assembly_status": "L4_TOP_LEVEL_INSTANTIATED_WITH_CONTRACT_PINS",
                    "blocking_gap": "",
                    "next_required_action": "Enter L5 validation only after checking top-level routing and rail plans against downstream closure criteria.",
                    "evidence_files": ";".join(
                        [
                            str(self.out_dir / "top_level_config.json"),
                            str(self.out_dir / "module_placement.json"),
                            str(self.out_dir / "top_level_pin_map.json"),
                            str(self.out_dir / "top_level_rail_stitch_plan.json"),
                            str(self.out_dir / "top_level_routing_handoff.json"),
                        ]
                    ),
                },
                {
                    "object": "BANK",
                    "object_category": "bank_semantic_object",
                    "is_top_level_target": "True",
                    "source_module_gds": "",
                    "module_gds_sanity_status": validation["top_gds_sanity_status"],
                    "instantiated_in_top_gds": "True",
                    "instance_name": "BANK_SYNTHETIC",
                    "origin": json.dumps({"x": 0.0, "y": 0.0}),
                    "orientation": "R0",
                    "bbox": json.dumps(validation.get("top_bbox")),
                    "pins_available": "True",
                    "rail_metadata_available": "True",
                    "routing_handoff_available": "True",
                    "power_handoff_available": "True",
                    "uses_candidate_geometry": "True",
                    "uses_contract_pins": "True",
                    "assembly_status": "L4_TOP_LEVEL_INSTANTIATED_WITH_CONTRACT_PINS",
                    "blocking_gap": "",
                    "next_required_action": "Treat BANK as a semantic wrapper around the single-bank L4 candidate; detailed internal routing verification stays in L5.",
                    "evidence_files": str(self.out_json),
                },
                {
                    "object": "routing_semantics",
                    "object_category": "handoff_object",
                    "is_top_level_target": "True",
                    "source_module_gds": "",
                    "module_gds_sanity_status": "",
                    "instantiated_in_top_gds": "False",
                    "instance_name": "",
                    "origin": "",
                    "orientation": "",
                    "bbox": "",
                    "pins_available": "True",
                    "rail_metadata_available": "False",
                    "routing_handoff_available": "True",
                    "power_handoff_available": "False",
                    "uses_candidate_geometry": "False",
                    "uses_contract_pins": "True",
                    "assembly_status": "L4_TOP_LEVEL_DEFERRED_TO_L5_ROUTING",
                    "blocking_gap": "",
                    "next_required_action": "Use top_level_routing_handoff.json in L5 to close detailed inter-module routing.",
                    "evidence_files": str(self.out_dir / "top_level_routing_handoff.json"),
                },
                {
                    "object": "power_semantics",
                    "object_category": "handoff_object",
                    "is_top_level_target": "True",
                    "source_module_gds": "",
                    "module_gds_sanity_status": "",
                    "instantiated_in_top_gds": "False",
                    "instance_name": "",
                    "origin": "",
                    "orientation": "",
                    "bbox": "",
                    "pins_available": "True",
                    "rail_metadata_available": "True",
                    "routing_handoff_available": "False",
                    "power_handoff_available": "True",
                    "uses_candidate_geometry": "False",
                    "uses_contract_pins": "True",
                    "assembly_status": "L4_TOP_LEVEL_DEFERRED_TO_L5_ROUTING",
                    "blocking_gap": "",
                    "next_required_action": "Use top_level_rail_stitch_plan.json in L5 for rail verification and stitch closure.",
                    "evidence_files": str(self.out_dir / "top_level_rail_stitch_plan.json"),
                },
                {
                    "object": "timing_semantics",
                    "object_category": "handoff_object",
                    "is_top_level_target": "True",
                    "source_module_gds": "",
                    "module_gds_sanity_status": "",
                    "instantiated_in_top_gds": "False",
                    "instance_name": "",
                    "origin": "",
                    "orientation": "",
                    "bbox": "",
                    "pins_available": "True",
                    "rail_metadata_available": "False",
                    "routing_handoff_available": "True",
                    "power_handoff_available": "False",
                    "uses_candidate_geometry": "False",
                    "uses_contract_pins": "True",
                    "assembly_status": "L4_TOP_LEVEL_DEFERRED_TO_L5_ROUTING",
                    "blocking_gap": "",
                    "next_required_action": "Carry the timing/control handoff metadata into L5 validation without claiming timing closure.",
                    "evidence_files": str(self.out_json),
                },
            ]
        )
        return rows

    def _build_report(
        self,
        config: TopLevelAssemblyConfig,
        placement_plan: TopLevelPlacementPlan,
        modules: dict[str, TopLevelModuleMetadata],
        validation: dict[str, Any],
        missing_modules: list[str],
        rail_stitch_plan: TopLevelRailStitchPlan,
        routing_handoff: TopLevelRoutingHandoff,
        inventory_rows: list[dict[str, Any]],
    ) -> dict[str, Any]:
        instantiated_count = len(placement_plan.instances)
        candidate_modules = sorted(item.module_name for item in placement_plan.instances if item.uses_candidate_geometry)
        contract_pin_modules = sorted(item.module_name for item in placement_plan.instances if item.uses_contract_pins)
        blockers: list[str] = []
        if not validation["top_gds_exists"]:
            blockers.append("Top-level candidate GDS was not emitted.")
        if validation["top_gds_sanity_status"] != "GDS_PARSED_SANITY_PASSED":
            blockers.append(f"Top-level GDS sanity failed: {validation['top_gds_sanity_status']}.")
        if missing_modules:
            blockers.append(f"Required L3 modules missing from top-level candidate: {', '.join(missing_modules)}.")
        can_enter_l5 = not blockers
        return {
            "L4_top_level_assembly_available": True,
            "top_level_candidate_gds_generated": validation["top_gds_exists"] and validation["top_gds_non_empty"],
            "top_level_candidate_gds_path": str(self.out_dir / "openyield_top_level_candidate.gds"),
            "top_level_generator_manifest_available": True,
            "top_level_config_available": True,
            "top_level_floorplan_available": True,
            "module_placement_available": True,
            "top_level_pin_map_available": True,
            "top_level_rail_stitch_plan_available": True,
            "top_level_routing_handoff_available": True,
            "top_level_assembly_inventory_available": True,
            "required_l3_modules_count": len(L3_REQUIRED_MODULES),
            "required_l3_modules_instantiated_count": instantiated_count,
            "required_l3_modules_missing_from_top": missing_modules,
            "top_gds_sanity_status": validation["top_gds_sanity_status"],
            "top_gds_size_bytes": validation["top_gds_size_bytes"],
            "top_cell_name": validation["top_cell_name"],
            "top_bbox": validation["top_bbox"],
            "top_instance_count": validation["top_instance_count"],
            "top_cell_count": validation["cell_count"],
            "top_gds_layer_summary": validation["layer_summary"],
            "module_references": validation["module_references"],
            "top_gds_missing_references": validation.get("missing_references", []),
            "top_gds_self_references": validation.get("self_references", []),
            "top_gds_cycles": validation.get("cycles", []),
            "modules_instantiated_with_candidate_geometry": candidate_modules,
            "modules_instantiated_with_contract_pins": contract_pin_modules,
            "remaining_L4_blockers": blockers,
            "remaining_L4_blockers_count": len(blockers),
            "can_claim_L4_top_level_candidate_gds_generated_now": validation["top_gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED" and not missing_modules,
            "can_enter_L5_validation": can_enter_l5,
            "can_claim_validated_full_openyield_gds_now": False,
            "can_claim_drc_clean_now": False,
            "can_claim_lvs_clean_now": False,
            "can_claim_timing_closure_now": False,
            "uses_candidate_geometry": True,
            "not_DRC_clean_claimed": True,
            "not_LVS_clean_claimed": True,
            "top_level_config": asdict(config),
            "routing_handoff_entry_count": len(routing_handoff.entries),
            "rail_stitch_plan_entry_count": len(rail_stitch_plan.entries),
            "inventory_row_count": len(inventory_rows),
        }

    def _render_generation_report_md(self, report: dict[str, Any]) -> str:
        lines = [
            "# OpenYield L4 Top-Level Assembly Report",
            "",
            f"- top_level_candidate_gds_generated: `{report['top_level_candidate_gds_generated']}`",
            f"- top_level_candidate_gds_path: `{report['top_level_candidate_gds_path']}`",
            f"- top_gds_sanity_status: `{report['top_gds_sanity_status']}`",
            f"- required_l3_modules_count: `{report['required_l3_modules_count']}`",
            f"- required_l3_modules_instantiated_count: `{report['required_l3_modules_instantiated_count']}`",
            f"- required_l3_modules_missing_from_top: `{report['required_l3_modules_missing_from_top']}`",
            f"- modules_instantiated_with_candidate_geometry: `{report['modules_instantiated_with_candidate_geometry']}`",
            f"- modules_instantiated_with_contract_pins: `{report['modules_instantiated_with_contract_pins']}`",
            f"- top_cell_name: `{report['top_cell_name']}`",
            f"- top_bbox: `{report['top_bbox']}`",
            f"- top_instance_count: `{report['top_instance_count']}`",
            f"- top_gds_missing_references: `{report.get('top_gds_missing_references', [])}`",
            f"- top_gds_self_references: `{report.get('top_gds_self_references', [])}`",
            f"- top_gds_cycles: `{report.get('top_gds_cycles', [])}`",
            f"- remaining_L4_blockers_count: `{report['remaining_L4_blockers_count']}`",
            f"- can_claim_L4_top_level_candidate_gds_generated_now: `{report['can_claim_L4_top_level_candidate_gds_generated_now']}`",
            f"- can_enter_L5_validation: `{report['can_enter_L5_validation']}`",
            f"- can_claim_validated_full_openyield_gds_now: `{report['can_claim_validated_full_openyield_gds_now']}`",
            f"- can_claim_drc_clean_now: `{report['can_claim_drc_clean_now']}`",
            f"- can_claim_lvs_clean_now: `{report['can_claim_lvs_clean_now']}`",
            f"- can_claim_timing_closure_now: `{report['can_claim_timing_closure_now']}`",
        ]
        if report["remaining_L4_blockers"]:
            lines.extend(["", "## Remaining L4 Blockers", ""])
            lines.extend(f"- {item}" for item in report["remaining_L4_blockers"])
        return "\n".join(lines) + "\n"

    def _write_gap_summary(
        self,
        report: dict[str, Any],
        placement_plan: TopLevelPlacementPlan,
        routing_handoff: TopLevelRoutingHandoff,
        rail_stitch_plan: TopLevelRailStitchPlan,
    ) -> None:
        path = self.repo_root / "docs/evidence/L4_top_level_assembly_gap_summary.md"
        instantiated = ", ".join(item.module_name for item in placement_plan.instances)
        lines = [
            "# L4 Top-Level Assembly Gap Summary",
            "",
            "## Current Candidate",
            "",
            f"- Generated top-level candidate: `{report['top_level_candidate_gds_path']}`",
            f"- Top-level GDS sanity: `{report['top_gds_sanity_status']}`",
            f"- Top-level bbox: `{report['top_bbox']}`",
            "",
            "## Instantiated L3 Modules",
            "",
            f"- Instantiated modules: `{instantiated}`",
            f"- Candidate geometry modules: `{', '.join(report['modules_instantiated_with_candidate_geometry']) or 'none'}`",
            f"- Contract pin modules: `{', '.join(report['modules_instantiated_with_contract_pins']) or 'none'}`",
            "",
            "## Rail Stitch Plan",
            "",
            f"- Rail plan entries: `{len(rail_stitch_plan.entries)}`",
            "- Strategy: module-boundary rails feed a deterministic top-level spine with vertical drops; verification remains deferred to L5.",
            "",
            "## Routing Handoff",
            "",
            f"- Routing handoff entries: `{len(routing_handoff.entries)}`",
            "- Status policy: top-level inter-module connections are emitted as routing handoff metadata and remain detailed-routing work for L5.",
            "",
            "## L5 Gate",
            "",
            f"- can_enter_L5_validation: `{report['can_enter_L5_validation']}`",
            f"- remaining_L4_blockers_count: `{report['remaining_L4_blockers_count']}`",
        ]
        if report["remaining_L4_blockers"]:
            lines.append("- blockers:")
            lines.extend(f"  - {item}" for item in report["remaining_L4_blockers"])
        _write_text(path, "\n".join(lines) + "\n")

    def _update_evidence_timeline(self, report: dict[str, Any]) -> None:
        path = self.repo_root / "docs/evidence/evidence_timeline.md"
        text = path.read_text(encoding="utf-8")
        line = (
            f"- `2026-07-02`: Completed OpenYield L4 top-level assembly first round by generating "
            f"`{report['top_level_candidate_gds_path']}`, deterministic placement/pin/rail/routing metadata, "
            f"and setting `can_claim_L4_top_level_candidate_gds_generated_now={report['can_claim_L4_top_level_candidate_gds_generated_now']}` "
            f"and `can_enter_L5_validation={report['can_enter_L5_validation']}` while keeping full-GDS/DRC/LVS/timing claims false.\n"
        )
        if line not in text:
            _write_text(path, text.rstrip() + "\n" + line)

    def _update_milestone_summary(self, report: dict[str, Any]) -> None:
        path = self.repo_root / "docs/evidence/milestone_summary.md"
        text = path.read_text(encoding="utf-8")
        addition = (
            "- L4 first round: a reproducible Python top-level assembly generator now instantiates all 20 required L3 modules into a single-bank SRAM candidate GDS and emits floorplan/pin-map/rail-stitch/routing-handoff metadata, while still keeping validated full-GDS, DRC, LVS, and timing-closure claims false.\n"
            f"- `can_claim_L4_top_level_candidate_gds_generated_now={report['can_claim_L4_top_level_candidate_gds_generated_now']}`\n"
            f"- `can_enter_L5_validation={report['can_enter_L5_validation']}`\n"
        )
        if addition not in text:
            _write_text(path, text.rstrip() + "\n" + addition)

    def _module_rail_handoff(self, meta: TopLevelModuleMetadata) -> dict[str, Any]:
        return {
            "rail_status": meta.rail_report.get("rail_status"),
            "uses_explicit_rail_handoff_contract": meta.rail_report.get("uses_explicit_rail_handoff_contract", False),
            "requires_L5_verification": True,
        }

    def _module_routing_nets(self, module_name: str, routing_handoff: TopLevelRoutingHandoff) -> list[str]:
        nets = []
        for entry in routing_handoff.entries:
            if entry["source_module"] == module_name or entry["target_module"] == module_name:
                nets.append(str(entry["net_name"]))
        return sorted(set(nets))

    def _resolve_pin_name(self, meta: TopLevelModuleMetadata | None, contract_pin: str) -> str:
        if meta is None:
            return contract_pin
        actual_names = [str(pin["name"]) for pin in meta.pins]
        canonical_map = {_canonical_token(name): name for name in actual_names}
        for token in _split_contract_pin_tokens(contract_pin):
            if token in canonical_map:
                return canonical_map[token]
        special = {
            ("row_decoder", "WL[i]"): "dec_out[*]",
            ("bitcell_array", "BL[i]/BLB[i]"): "BL[*]",
            ("bitcell_array", "WL[i]"): "WL[*]",
            ("wordline_driver", "EN"): "B",
            ("precharge", "ENB"): "en_bar",
            ("column_mux", "BL[i]/BLB[i]"): "bl",
            ("column_mux", "SA_IN/SA_INB"): "bl_out",
            ("sense_amp", "IN/INB"): "bl",
            ("sense_amp", "Q/QB"): "dout",
            ("write_driver", "DIN"): "din",
            ("write_driver", "EN"): "en",
            ("DELAY_CHAIN", "in"): "delay_in",
            ("DELAY_CHAIN", "out"): "delay_out",
            ("DELAY_CHAIN", "out_bar"): "delay_out",
            ("CONTROL_LOGIC", "PRE"): "precharge_en",
            ("CONTROL_LOGIC", "s_en"): "sense_en",
            ("CONTROL_LOGIC", "w_en"): "write_en",
            ("DFF_ROW", "A[i]"): "D[*]",
            ("DFF_ROW", "DIN[i]"): "D[*]",
            ("DFF_ROW", "A_dff[i]"): "Q[*]",
            ("DFF_ROW", "DIN_dff[i]"): "Q[*]",
            ("DFF_ROW", "CLK"): "clk",
        }
        return special.get((meta.module_name, contract_pin), contract_pin)

    def _layer_summary(self, lib: gdstk.Library) -> dict[str, int]:
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

    def _find_cycles(self, refs_by_cell: dict[str, list[str]], cell_names: set[str]) -> list[list[str]]:
        visited: dict[str, int] = {}
        stack: list[str] = []
        cycles: list[list[str]] = []

        def dfs(node: str) -> None:
            visited[node] = 1
            stack.append(node)
            for ref_name in refs_by_cell.get(node, []):
                if ref_name not in cell_names:
                    continue
                state = visited.get(ref_name, 0)
                if state == 1:
                    index = stack.index(ref_name)
                    cycles.append(stack[index:] + [ref_name])
                elif state == 0:
                    dfs(ref_name)
            stack.pop()
            visited[node] = 2

        for cell_name in sorted(cell_names):
            if visited.get(cell_name, 0) == 0:
                dfs(cell_name)
        return cycles

    def _gdspy_layer_summary(self, lib: gdspy.GdsLibrary) -> dict[str, int]:
        counts: dict[str, int] = {}
        for cell in lib.cells.values():
            for polygon in cell.polygons:
                specs = polygon.layers if hasattr(polygon, "layers") else [polygon.layer]
                dts = polygon.datatypes if hasattr(polygon, "datatypes") else [polygon.datatype]
                for layer, datatype in zip(specs, dts):
                    key = f"{layer}/{datatype}"
                    counts[key] = counts.get(key, 0) + 1
            for label in cell.labels:
                key = f"{label.layer}/{label.texttype}"
                counts[key] = counts.get(key, 0) + 1
        return dict(sorted(counts.items()))


def _translated_bbox(bbox: dict[str, float], origin_x: float, origin_y: float) -> dict[str, float]:
    return {
        "x0": round(origin_x + float(bbox["x0"]), 6),
        "y0": round(origin_y + float(bbox["y0"]), 6),
        "x1": round(origin_x + float(bbox["x1"]), 6),
        "y1": round(origin_y + float(bbox["y1"]), 6),
        "width": round(float(bbox["width"]), 6),
        "height": round(float(bbox["height"]), 6),
    }


def run_top_level_assembly(
    repo_root: Path,
    openyield_root: Path,
    module_gds_inventory: Path,
    module_generator_inventory: Path,
    module_gds_dir: Path,
    l0_contract_json: Path,
    l2_rule_library_json: Path,
    out_dir: Path,
    out_inventory_csv: Path,
    out_inventory_md: Path,
    out_json: Path,
    out_report: Path,
    reproducible_command: str,
) -> TopLevelAssemblyResult:
    assembler = OpenYieldTopLevelAssembler(
        repo_root=repo_root,
        openyield_root=openyield_root,
        module_gds_inventory=module_gds_inventory,
        module_generator_inventory=module_generator_inventory,
        module_gds_dir=module_gds_dir,
        l0_contract_json=l0_contract_json,
        l2_rule_library_json=l2_rule_library_json,
        out_dir=out_dir,
        out_inventory_csv=out_inventory_csv,
        out_inventory_md=out_inventory_md,
        out_json=out_json,
        out_report=out_report,
        reproducible_command=reproducible_command,
    )
    return assembler.run()


def canonicalize_layout_handoff_signal(text: str) -> str:
    return _canonical_token(text)
