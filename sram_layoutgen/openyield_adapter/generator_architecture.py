from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


MATRIX_COLUMNS = [
    "component_name",
    "component_category",
    "responsibility",
    "input_artifacts",
    "output_artifacts",
    "required_for_R3",
    "required_for_R4",
    "reuse_existing_code",
    "new_code_required",
    "learned_from_openram",
    "openyield_specific_behavior",
    "implementation_priority",
    "risk",
    "next_required_action",
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
        values = [str(row.get(column, "")).replace("\n", "<br>") for column in columns]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


@dataclass(frozen=True)
class GeneratorComponent:
    component_name: str
    component_category: str
    responsibility: str
    input_artifacts: tuple[str, ...]
    output_artifacts: tuple[str, ...]
    depends_on: tuple[str, ...]
    learned_from_openram_mechanism: str
    openyield_specific_behavior: str
    reuse_existing_project_code: str
    new_code_required: bool
    required_for_R3: bool
    required_for_R4: bool
    risk: str
    implementation_notes: str
    implementation_priority: str
    next_required_action: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_matrix_row(self) -> dict[str, Any]:
        return {
            "component_name": self.component_name,
            "component_category": self.component_category,
            "responsibility": self.responsibility,
            "input_artifacts": "; ".join(self.input_artifacts),
            "output_artifacts": "; ".join(self.output_artifacts),
            "required_for_R3": self.required_for_R3,
            "required_for_R4": self.required_for_R4,
            "reuse_existing_code": self.reuse_existing_project_code,
            "new_code_required": self.new_code_required,
            "learned_from_openram": self.learned_from_openram_mechanism,
            "openyield_specific_behavior": self.openyield_specific_behavior,
            "implementation_priority": self.implementation_priority,
            "risk": self.risk,
            "next_required_action": self.next_required_action,
        }


@dataclass(frozen=True)
class GeneratorInterface:
    component_name: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    notes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GeneratorDataflow:
    flow_name: str
    stages: tuple[dict[str, Any], ...]
    openyield_inputs: tuple[str, ...]
    r1_rules: tuple[str, ...]
    learned_from_openram: tuple[str, ...]
    openyield_specific_mechanisms: tuple[str, ...]
    legacy_candidate_limits: tuple[str, ...]
    r3_r4_to_r5_support: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GeneratorReuseDecision:
    reusable_now: tuple[dict[str, str], ...]
    adaptable: tuple[dict[str, str], ...]
    do_not_reuse_or_extend: tuple[dict[str, str], ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class R3MinimumImplementationPlan:
    target_configuration: dict[str, Any]
    minimum_scope: tuple[str, ...]
    explicitly_not_required: tuple[str, ...]
    deliverables: tuple[str, ...]
    architecture_constraints: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class R4RoutingPowerPinPlan:
    wordline_router_scope: tuple[str, ...]
    bitline_router_scope: tuple[str, ...]
    control_router_scope: tuple[str, ...]
    power_planner_scope: tuple[str, ...]
    pin_label_exporter_scope: tuple[str, ...]
    net_to_shape_mapper_scope: tuple[str, ...]
    r5_support: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OpenYieldGeneratorArchitecture:
    architecture_name: str
    intent_centric: bool
    openram_independent_main_flow: bool
    components: tuple[GeneratorComponent, ...]
    supported_scope: dict[str, Any]
    architecture_constraints: tuple[str, ...]
    baseline_configuration: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["components"] = [component.to_dict() for component in self.components]
        return payload


class GeneratorArchitectureBuilder:
    def __init__(self, context: dict[str, Any]) -> None:
        self.context = context

    def run(self) -> dict[str, Any]:
        self._validate_inputs()
        r0_report = _load_json(self.context["r0_audit_json"])
        r1_report = _load_json(self.context["r1_report_json"])
        intent_dir = self.context["r1_intent_dir"]
        layout_intent = _load_json(intent_dir / "openyield_sram_layout_intent.json")
        array_contract = _load_json(intent_dir / "openyield_array_topology_contract.json")
        row_intent = _load_json(intent_dir / "openyield_row_path_intent.json")
        column_intent = _load_json(intent_dir / "openyield_column_path_intent.json")
        control_intent = _load_json(intent_dir / "openyield_control_path_intent.json")
        power_intent = _load_json(intent_dir / "openyield_power_intent.json")
        pin_intent = _load_json(intent_dir / "openyield_pin_intent.json")
        net_role_rows = _load_csv(intent_dir / "openyield_net_to_layout_role_map.csv")
        module_role_rows = _load_csv(intent_dir / "openyield_module_to_physical_role_map.csv")
        module_gds_rows = _load_csv(self.context["module_gds_inventory"])
        module_generator_rows = _load_csv(self.context["module_generator_inventory"])

        baseline = self._extract_baseline(layout_intent)
        registry = self._build_registry(module_gds_rows, module_generator_rows, module_role_rows)
        components = self._build_components(registry)
        architecture = OpenYieldGeneratorArchitecture(
            architecture_name="openyield_sram_generator_architecture",
            intent_centric=True,
            openram_independent_main_flow=True,
            components=tuple(components),
            supported_scope=layout_intent["canonical_parameters"]["supported_scope"],
            architecture_constraints=(
                "Do not invoke the OpenRAM main compiler flow as a black-box layout generator.",
                "Do not continue patching openyield_top_level_candidate.gds into the new SRAM generator path.",
                "Do not claim structure-complete SRAM GDS, DRC clean, LVS clean, timing closure, or signoff-ready status in R2.",
                "Keep the generator lightweight, but retain generator-owned placement, routing, power, and pin export boundaries.",
            ),
            baseline_configuration=baseline,
        )
        interfaces = self._build_interfaces(registry, baseline)
        dataflow = self._build_dataflow(array_contract, row_intent, column_intent, control_intent, power_intent, pin_intent)
        reuse_decision = self._build_reuse_decision()
        r3_plan = self._build_r3_plan(baseline)
        r4_plan = self._build_r4_plan()
        component_plan = self._build_component_plan(components)
        report = self._build_report(architecture, r0_report, r1_report, net_role_rows, module_role_rows, registry)

        out_dir = self.context["out_dir"]
        out_dir.mkdir(parents=True, exist_ok=True)
        self._write_architecture(out_dir, architecture)
        self._write_dataflow(out_dir, dataflow)
        self._write_interfaces(out_dir, interfaces)
        self._write_component_plan(out_dir, component_plan)
        self._write_r3_plan(out_dir, r3_plan)
        self._write_r4_plan(out_dir, r4_plan)
        self._write_reuse_decision(out_dir, reuse_decision)
        self._write_matrix([component.to_matrix_row() for component in components])
        self._write_report(report, architecture, dataflow, interfaces, r3_plan, r4_plan, reuse_decision)
        self._write_gap_summary(report)
        return report

    def _validate_inputs(self) -> None:
        required = [
            self.context["r0_audit_json"],
            self.context["r0_reuse_matrix"],
            self.context["r1_report_json"],
            self.context["module_gds_inventory"],
            self.context["module_generator_inventory"],
            self.context["r1_intent_dir"] / "openyield_sram_layout_intent.json",
            self.context["r1_intent_dir"] / "openyield_array_topology_contract.json",
            self.context["r1_intent_dir"] / "openyield_row_path_intent.json",
            self.context["r1_intent_dir"] / "openyield_column_path_intent.json",
            self.context["r1_intent_dir"] / "openyield_control_path_intent.json",
            self.context["r1_intent_dir"] / "openyield_power_intent.json",
            self.context["r1_intent_dir"] / "openyield_pin_intent.json",
            self.context["r1_intent_dir"] / "openyield_net_to_layout_role_map.csv",
            self.context["r1_intent_dir"] / "openyield_module_to_physical_role_map.csv",
        ]
        missing = [str(path) for path in required if not Path(path).exists()]
        if missing:
            raise FileNotFoundError("Missing required R2 inputs: " + "; ".join(missing))

    def _extract_baseline(self, layout_intent: dict[str, Any]) -> dict[str, Any]:
        params = {item["parameter_name"]: item["value"] for item in layout_intent["canonical_parameters"]["parameters"]}
        return {
            "word_size": params["word_size"],
            "num_words": params["num_words"],
            "words_per_row": params["words_per_row"],
            "num_rows": params["num_rows"],
            "num_cols": params["num_cols"],
            "column_mux_ratio": params["column_mux_ratio"],
            "address_width": params["address_width"],
            "row_address_width": params["row_address_width"],
            "column_address_width": params["column_address_width"],
        }

    def _build_registry(self, module_gds_rows: list[dict[str, str]], module_generator_rows: list[dict[str, str]], module_role_rows: list[dict[str, str]]) -> dict[str, Any]:
        available_hardmacros = sorted(row["module"] for row in module_gds_rows if row.get("uses_hardmacro", "").lower() == "true")
        candidate_geometry_modules = sorted(
            row["module"]
            for row in module_gds_rows
            if "candidate" in row.get("generation_status", "").lower() or row.get("uses_composition_generator", "").lower() == "true"
        )
        generator_ready = sorted(row["module"] for row in module_generator_rows if row.get("generator_available", "").lower() == "true")
        module_physical_roles = {row["module_name"]: row["physical_role"] for row in module_role_rows}
        return {
            "available_hardmacros": available_hardmacros,
            "candidate_geometry_modules": candidate_geometry_modules,
            "generator_ready_modules": generator_ready,
            "modules_requiring_new_generator": [
                "bitcell_array_wrapper",
                "row_periphery_composer",
                "column_periphery_composer",
                "control_periphery_composer",
                "sram_topology_floorplanner",
                "wordline_router",
                "bitline_router",
                "control_router",
                "power_planner",
                "pin_label_exporter",
                "net_to_shape_mapper",
                "instance_mapper",
            ],
            "module_physical_roles": module_physical_roles,
        }

    def _component(self, **kwargs: Any) -> GeneratorComponent:
        return GeneratorComponent(**kwargs)

    def _build_components(self, registry: dict[str, Any]) -> list[GeneratorComponent]:
        return [
            self._component(component_name="OpenYieldIntentLoader", component_category="front_end", responsibility="Load OpenYield semantic contracts and frozen R1 layout intent artifacts into a generator-owned input bundle.", input_artifacts=("openyield_sram_layout_intent.json", "openyield_array_topology_contract.json", "openyield_row_path_intent.json", "openyield_column_path_intent.json", "openyield_control_path_intent.json", "openyield_power_intent.json", "openyield_pin_intent.json"), output_artifacts=("LoadedLayoutIntent",), depends_on=(), learned_from_openram_mechanism="OpenRAM starts from a compact semantic configuration before any geometry is created.", openyield_specific_behavior="Treat R1 artifacts as the authoritative input surface instead of parsing OpenRAM globals or config files.", reuse_existing_project_code="Adapt layout_intent.py loading helpers and report conventions.", new_code_required=True, required_for_R3=True, required_for_R4=True, risk="Low; schema drift between R1 and R2 must stay explicit.", implementation_notes="Own strict file existence checks and schema normalization.", implementation_priority="P0", next_required_action="Implement a LoadedLayoutIntent dataclass and file validation entry point."),
            self._component(component_name="CanonicalSramParameterModel", component_category="parameter_model", responsibility="Normalize canonical SRAM parameters, derived widths, and physical pitch requirements into a generator-owned model.", input_artifacts=("LoadedLayoutIntent",), output_artifacts=("CanonicalSramParameterModel",), depends_on=("OpenYieldIntentLoader",), learned_from_openram_mechanism="OpenRAM sram_config centralizes derived geometry-driving parameters before module creation.", openyield_specific_behavior="Keep the model parameterized beyond the 4x4 baseline while honoring the current supported single-bank single-port scope.", reuse_existing_project_code="Reuse parameter names and R1 canonical intent definitions; no direct OpenRAM state reuse.", new_code_required=True, required_for_R3=True, required_for_R4=True, risk="Low; incorrect derivation would misalign every downstream generator.", implementation_notes="Carry row and column address widths, mux ratio, and pitch requirements as first-class fields.", implementation_priority="P0", next_required_action="Implement derivation checks that reject unsupported multi-bank or multi-port requests."),
            self._component(component_name="PhysicalModuleRegistry", component_category="registry", responsibility="Resolve which physical modules come from existing hardmacros, candidate geometry, or new R3/R4 generator code.", input_artifacts=("openyield_module_to_physical_role_map.csv", "openyield_module_gds_inventory.csv", "openyield_module_generator_inventory.csv"), output_artifacts=("available_hardmacros", "candidate_geometry_modules", "modules_requiring_new_generator", "module_physical_roles"), depends_on=("OpenYieldIntentLoader",), learned_from_openram_mechanism="OpenRAM chooses concrete module variants before bank or top-level composition.", openyield_specific_behavior="Use the existing OpenYield module inventory as reusable metadata while reserving new composition ownership for bitcell-array and periphery generators plus later routers.", reuse_existing_project_code="Reuse module_gds_generators inventory/manifests and the R1 module-to-role map.", new_code_required=True, required_for_R3=True, required_for_R4=True, risk="Medium; misclassifying contract-only modules as geometry-complete would leak false readiness.", implementation_notes="Registry must distinguish reusable hardmacros from modules that only have candidate wrappers or contract pins.", implementation_priority="P0", next_required_action="Implement explicit readiness classes for hardmacro, candidate, and generator-owned modules."),
            self._component(component_name="BitcellArrayPhysicalGenerator", component_category="physical_generator", responsibility="Create the array-centric storage region including main bitcell array, dummy context, and replica context with pitch ownership.", input_artifacts=("CanonicalSramParameterModel", "ArrayTopologyContract", "PhysicalModuleRegistry"), output_artifacts=("structure_complete_module_layouts", "placement_ready_module_geometry", "pitch_aligned_boundaries"), depends_on=("CanonicalSramParameterModel", "PhysicalModuleRegistry"), learned_from_openram_mechanism="OpenRAM wraps main, replica, and boundary array semantics around a pitch-owned bitcell fabric.", openyield_specific_behavior="Use OpenYield intent to define array-core ownership and preserve lightweight single-bank scope without importing OpenRAM bank flow.", reuse_existing_project_code="Adapt array metadata and standalone array generator knowledge from module_gds_generators.py.", new_code_required=True, required_for_R3=True, required_for_R4=True, risk="Medium; dummy and replica placement policy is necessary for structure-complete claims in R3.", implementation_notes="R3 may reuse existing array hardcells but must move to generator-owned wrapper composition.", implementation_priority="P0", next_required_action="Define wrapper composition rules for core, dummy, replica, boundary, and pitch export."),
            self._component(component_name="RowPeripheryPhysicalGenerator", component_category="physical_generator", responsibility="Compose decoder stages and wordline driver structures into a row-pitch-aligned row periphery region.", input_artifacts=("CanonicalSramParameterModel", "RowPathIntent", "PhysicalModuleRegistry"), output_artifacts=("structure_complete_module_layouts", "placement_ready_module_geometry", "pitch_aligned_boundaries"), depends_on=("CanonicalSramParameterModel", "PhysicalModuleRegistry", "BitcellArrayPhysicalGenerator"), learned_from_openram_mechanism="OpenRAM treats address decode and wordline drive as one explicit row-path module boundary.", openyield_specific_behavior="Allow reuse of existing candidate row logic blocks but move pitch alignment ownership into the new generator.", reuse_existing_project_code="Adapt candidate module metadata and selected import/write utilities; do not reuse legacy placement strategy.", new_code_required=True, required_for_R3=True, required_for_R4=True, risk="Medium; row-pitch mismatch would break later wordline routing.", implementation_notes="Support row decoder, wordline decoder, gate rows, and hardmacro wordline driver under one generator boundary.", implementation_priority="P0", next_required_action="Define array-facing anchors and row expansion contract for decoder-to-driver composition."),
            self._component(component_name="ColumnPeripheryPhysicalGenerator", component_category="physical_generator", responsibility="Compose precharge, column mux, sense amp, and write driver structures into a column-pitch-aligned column periphery region.", input_artifacts=("CanonicalSramParameterModel", "ColumnPathIntent", "PhysicalModuleRegistry"), output_artifacts=("structure_complete_module_layouts", "placement_ready_module_geometry", "pitch_aligned_boundaries"), depends_on=("CanonicalSramParameterModel", "PhysicalModuleRegistry", "BitcellArrayPhysicalGenerator"), learned_from_openram_mechanism="OpenRAM stacks column path blocks in a deterministic order driven by column pitch and mux topology.", openyield_specific_behavior="Preserve words_per_row and column_mux_ratio as generator inputs even when the baseline config is mux-free.", reuse_existing_project_code="Reuse hardmacro wrapper metadata for column_mux, sense_amp, write_driver, and precharge.", new_code_required=True, required_for_R3=True, required_for_R4=True, risk="Medium; wrapper width alone cannot guarantee column-pitch ownership.", implementation_notes="Generator must be able to degenerate cleanly when column mux is structurally absent.", implementation_priority="P0", next_required_action="Define block order, bit-slice ownership, and optional mux insertion contract."),
            self._component(component_name="ControlPeripheryPhysicalGenerator", component_category="physical_generator", responsibility="Compose control logic, delay chain, enable paths, and DFF rows into a peripheral control region with explicit bus ownership.", input_artifacts=("CanonicalSramParameterModel", "ControlPathIntent", "PhysicalModuleRegistry"), output_artifacts=("structure_complete_module_layouts", "placement_ready_module_geometry", "pitch_aligned_boundaries"), depends_on=("CanonicalSramParameterModel", "PhysicalModuleRegistry"), learned_from_openram_mechanism="OpenRAM treats control logic and replica delay semantics as structured periphery objects, not loose modules.", openyield_specific_behavior="Preserve OpenYield-specific control net names and delay/replica semantics as explicit outputs for later routing.", reuse_existing_project_code="Adapt candidate control path metadata and selected sanity checks from top_level_validation.py.", new_code_required=True, required_for_R3=True, required_for_R4=True, risk="Medium; control buses can be semantically correct but physically unreachable without region planning.", implementation_notes="R3 only needs region-level physical completeness; detailed control routing is deferred to R4.", implementation_priority="P1", next_required_action="Define control cluster grouping and exported control spine anchor points."),
            self._component(component_name="SRAMTopologyFloorplanner", component_category="floorplan", responsibility="Own the SRAM-specific region arrangement for array, row periphery, column periphery, control periphery, and power reservations.", input_artifacts=("CanonicalSramParameterModel", "ArrayTopologyContract", "RowPathIntent", "ColumnPathIntent", "ControlPathIntent", "PhysicalModuleRegistry"), output_artifacts=("array_region", "row_periphery_region", "column_periphery_region", "control_region", "power_region", "top_bbox", "placement_plan"), depends_on=("CanonicalSramParameterModel", "PhysicalModuleRegistry", "BitcellArrayPhysicalGenerator", "RowPeripheryPhysicalGenerator", "ColumnPeripheryPhysicalGenerator", "ControlPeripheryPhysicalGenerator"), learned_from_openram_mechanism="OpenRAM bank and sram_1bank place major regions with SRAM-specific quadrants and channels.", openyield_specific_behavior="Keep the topology array-centric and single-bank, avoiding OpenRAM multi-bank/global-state complexity.", reuse_existing_project_code="Adapt only low-level GDS import/write utilities from top_level_assembly.py; do not reuse its candidate-only placement strategy.", new_code_required=True, required_for_R3=True, required_for_R4=True, risk="High; poor region ownership would force later routers to become ad hoc patch layers.", implementation_notes="Floorplanner must output region contracts, not just instance coordinates.", implementation_priority="P0", next_required_action="Define region adjacency, array-facing edges, reserved channels, and top bbox computation policy."),
            self._component(component_name="WordlineRouter", component_category="router", responsibility="Connect wordline driver outputs to one physical WL per array row with row-pitch alignment.", input_artifacts=("placement_plan", "RowPathIntent", "CanonicalSramParameterModel"), output_artifacts=("wordline_routes",), depends_on=("SRAMTopologyFloorplanner", "RowPeripheryPhysicalGenerator"), learned_from_openram_mechanism="OpenRAM keeps decoder-to-driver and driver-to-WL routing explicit and row aligned.", openyield_specific_behavior="Route only deterministic SRAM wordline patterns; avoid a generic router.", reuse_existing_project_code="Potentially reuse future primitive geometry emitters and validation hooks; no existing router should be treated as complete.", new_code_required=True, required_for_R3=False, required_for_R4=True, risk="Medium; routing policy must align with exported row pitch from the array generator.", implementation_notes="Each row owns exactly one WL in the current supported scope.", implementation_priority="P2", next_required_action="Define row-track reservation and array-edge handoff geometry."),
            self._component(component_name="BitlineRouter", component_category="router", responsibility="Connect array BL/BR rails to precharge, optional column mux, sense amp, and write driver while preserving column pitch.", input_artifacts=("placement_plan", "ColumnPathIntent", "CanonicalSramParameterModel"), output_artifacts=("bitline_routes",), depends_on=("SRAMTopologyFloorplanner", "ColumnPeripheryPhysicalGenerator"), learned_from_openram_mechanism="OpenRAM routes bitlines and mux-dependent column-path connectivity explicitly from topology.", openyield_specific_behavior="Support mux-free baseline and later mux-enabled configs through parameterized column routing ownership.", reuse_existing_project_code="Reuse hardmacro pin metadata and future GDS primitive backend only.", new_code_required=True, required_for_R3=False, required_for_R4=True, risk="High; column routing topology changes with mux ratio and directly impacts sense/write ownership.", implementation_notes="Keep BL/BR, BL_out/BR_out, and column-select semantics separate.", implementation_priority="P2", next_required_action="Define array-edge escape pins and per-bit routing templates for mux-free and muxed cases."),
            self._component(component_name="ControlRouter", component_category="router", responsibility="Distribute precharge_en, sense_en, write_en, wordline_en, clk, gated_clk, and replica timing nets across periphery regions.", input_artifacts=("placement_plan", "ControlPathIntent", "openyield_net_to_layout_role_map.csv"), output_artifacts=("control_routes",), depends_on=("SRAMTopologyFloorplanner", "ControlPeripheryPhysicalGenerator"), learned_from_openram_mechanism="OpenRAM models control as structured buses and delay-driven periphery routes.", openyield_specific_behavior="Preserve OpenYield net names and semantic bus ownership in the route model for R5 validation.", reuse_existing_project_code="Reuse net role metadata and selected validation report patterns.", new_code_required=True, required_for_R3=False, required_for_R4=True, risk="Medium; semantic collapse of control and replica nets would undermine later validation.", implementation_notes="Separate control-route planning from power stitching and from data-path routing.", implementation_priority="P2", next_required_action="Define control spine anchors, route classes, and timing/replica route tags."),
            self._component(component_name="PowerPlanner", component_category="power", responsibility="Plan VDD/GND ownership, rail stitching, regional distribution, and top-level power export for array and periphery regions.", input_artifacts=("placement_plan", "openyield_power_intent.json", "PhysicalModuleRegistry"), output_artifacts=("power_routes", "power_region", "top_level_power_pins"), depends_on=("SRAMTopologyFloorplanner", "BitcellArrayPhysicalGenerator", "RowPeripheryPhysicalGenerator", "ColumnPeripheryPhysicalGenerator", "ControlPeripheryPhysicalGenerator"), learned_from_openram_mechanism="OpenRAM treats power export as a layered routing problem instead of pin copying.", openyield_specific_behavior="Use existing module rail metadata as input hints, but require generator-owned top-level stitching in R4.", reuse_existing_project_code="Adapt rail metadata, hierarchy export backend, and validation evidence framework.", new_code_required=True, required_for_R3=False, required_for_R4=True, risk="High; power continuity is a core boundary between prototype assembly and a real SRAM generator.", implementation_notes="Keep well/tap policy visible as an explicit future extension rather than hiding it in generic export code.", implementation_priority="P2", next_required_action="Define region-level rail entry sides, stitch points, and VDD/GND perimeter pin ownership."),
            self._component(component_name="PinLabelExporter", component_category="export", responsibility="Export top-level pin shapes, labels, and naming-consistent IO/power metadata from routed geometry.", input_artifacts=("placement_plan", "openyield_pin_intent.json", "wordline_routes", "bitline_routes", "control_routes", "power_routes"), output_artifacts=("top_level_pin_shapes", "top_level_labels", "pin_export_report"), depends_on=("WordlineRouter", "BitlineRouter", "ControlRouter", "PowerPlanner"), learned_from_openram_mechanism="OpenRAM derives pin exports from layout-owned geometry and naming consistency rules.", openyield_specific_behavior="Use OpenYield addr/din/dout/control naming exactly as defined in R1 intent.", reuse_existing_project_code="Reuse custom GDS writer label capability and existing pin audit/report patterns.", new_code_required=True, required_for_R3=False, required_for_R4=True, risk="Medium; pin naming drift would break later LEF/LVS correlation.", implementation_notes="Exporter should emit geometry-backed labels only after routes or pin shapes exist.", implementation_priority="P2", next_required_action="Define top-level pin classes, legal placement edges, and label naming policy."),
            self._component(component_name="NetToShapeMapper", component_category="metadata", responsibility="Map OpenYield semantic net names to source/target instance pins and produced geometry references.", input_artifacts=("openyield_net_to_layout_role_map.csv", "wordline_routes", "bitline_routes", "control_routes", "power_routes"), output_artifacts=("net_to_shape_map",), depends_on=("WordlineRouter", "BitlineRouter", "ControlRouter", "PowerPlanner"), learned_from_openram_mechanism="OpenRAM relies on naming consistency at instantiation time and keeps route ownership aligned to module roles.", openyield_specific_behavior="Expose OpenYield net names, route status, and geometry ids or bbox handles as first-class evidence for R5.", reuse_existing_project_code="Reuse R1 net role mapping and report infrastructure.", new_code_required=True, required_for_R3=False, required_for_R4=True, risk="Medium; without this map R5 cannot audit semantic-to-physical correspondence cleanly.", implementation_notes="Allow unresolved or pending routes to remain explicit instead of silently dropping them.", implementation_priority="P2", next_required_action="Define stable geometry identifiers and route-status enums."),
            self._component(component_name="InstanceMapper", component_category="metadata", responsibility="Track which logical SRAM roles instantiate which physical module implementations inside the generator-owned hierarchy.", input_artifacts=("PhysicalModuleRegistry", "placement_plan"), output_artifacts=("instance_map",), depends_on=("PhysicalModuleRegistry", "SRAMTopologyFloorplanner"), learned_from_openram_mechanism="OpenRAM composes layout through explicit instance ownership instead of top-level patching.", openyield_specific_behavior="Record when an OpenYield role uses existing hardmacro geometry versus new R3 composition code.", reuse_existing_project_code="Adapt generator manifests and module inventory metadata.", new_code_required=True, required_for_R3=True, required_for_R4=True, risk="Low; mapping gaps mainly hurt traceability rather than immediate geometry.", implementation_notes="This map becomes the bridge between registry decisions and validation evidence.", implementation_priority="P1", next_required_action="Define stable instance ids and role-to-module ownership schema."),
            self._component(component_name="GDSBackend", component_category="backend", responsibility="Serialize the generator-owned hierarchical SRAM layout into a GDS artifact without re-entering the OpenRAM save() flow.", input_artifacts=("placement_plan", "structure_complete_module_layouts", "top_level_pin_shapes", "top_level_labels"), output_artifacts=("structure_complete_sram_gds",), depends_on=("SRAMTopologyFloorplanner", "PinLabelExporter"), learned_from_openram_mechanism="OpenRAM separates layout construction from recursive GDS serialization.", openyield_specific_behavior="Keep the backend thin and driven by generator-owned geometry objects rather than old candidate assembly state.", reuse_existing_project_code="Directly reuse sram_layoutgen.gds_writer and supporting hierarchy export experience.", new_code_required=False, required_for_R3=True, required_for_R4=True, risk="Low; the backend exists, but its call boundary must stay decoupled from legacy assembly flow.", implementation_notes="R3 can emit structure-complete prototype geometry through this backend once placement objects exist.", implementation_priority="P1", next_required_action="Define the minimal backend adapter interface from generator geometry objects to GDS writer primitives."),
            self._component(component_name="ValidationHookManager", component_category="validation", responsibility="Emit generator-stage sanity, topology, routing, power, and pin audit reports without upgrading R2 claims beyond prototype scope.", input_artifacts=("placement_plan", "net_to_shape_map", "pin_export_report", "structure_complete_sram_gds"), output_artifacts=("sanity_report", "topology_validation_report", "routing_audit", "power_audit", "pin_audit"), depends_on=("GDSBackend", "NetToShapeMapper", "PinLabelExporter"), learned_from_openram_mechanism="OpenRAM routes verification through explicit hook points and backend dispatch rather than embedding closure claims everywhere.", openyield_specific_behavior="Keep evidence generation rich while preserving strict False gates for DRC/LVS/timing/signoff claims in R2 and baseline R3.", reuse_existing_project_code="Reuse top_level_validation.py checks, report layout, and docs/evidence workflow where applicable.", new_code_required=False, required_for_R3=True, required_for_R4=True, risk="Low; the main risk is overstating claims rather than missing geometry.", implementation_notes="Validation hooks should report readiness gaps, not silently skip them.", implementation_priority="P1", next_required_action="Define stage-specific validation hooks for R3 structure and R4 routing/pin/power audits."),
        ]

    def _build_interfaces(self, registry: dict[str, Any], baseline: dict[str, Any]) -> list[GeneratorInterface]:
        return [
            GeneratorInterface("OpenYieldIntentLoader", {"openyield_sram_layout_intent.json": "canonical parameters and supported scope", "array_topology_contract": "array role and pitch semantics", "row_path_intent": "row path responsibilities", "column_path_intent": "column path responsibilities", "control_path_intent": "control path responsibilities", "power_intent": "VDD/GND ownership and stitching expectations", "pin_intent": "top-level and internal pin naming contracts"}, {"LoadedLayoutIntent": {"canonical_parameters": "list of parameter definitions from R1", "path_intents": ["array", "row", "column", "control"], "power_intent": "module power summary and rail expectations", "pin_intent": "IO/control/power pin naming contracts"}}, ("This is the only generator front door.", "No OpenRAM config parsing is allowed here.")),
            GeneratorInterface("CanonicalSramParameterModel", {"LoadedLayoutIntent": "normalized R1 intent bundle"}, {"rows": baseline["num_rows"], "cols": baseline["num_cols"], "word_size": baseline["word_size"], "num_words": baseline["num_words"], "words_per_row": baseline["words_per_row"], "column_mux_ratio": baseline["column_mux_ratio"], "address_width": baseline["address_width"], "row_address_width": baseline["row_address_width"], "column_address_width": baseline["column_address_width"], "physical_pitch_requirements": {"row_pitch": "owned by BitcellArrayPhysicalGenerator output", "column_pitch": "owned by BitcellArrayPhysicalGenerator output"}}, ("Model must stay parameterized beyond the 4x4 baseline.",)),
            GeneratorInterface("PhysicalModuleRegistry", {"module_to_physical_role_map": "R1 physical role ownership", "module_gds_inventory": "existing GDS and metadata inventory", "generator_inventory": "existing standalone generator inventory"}, {"available_hardmacros": registry["available_hardmacros"], "candidate_geometry_modules": registry["candidate_geometry_modules"], "modules_requiring_new_generator": registry["modules_requiring_new_generator"], "module_physical_roles": registry["module_physical_roles"]}, ("Registry outputs drive reuse decisions and implementation priority.",)),
            GeneratorInterface("SRAMTopologyFloorplanner", {"CanonicalSramParameterModel": "canonical rows/cols/mux/pitch requirements", "ArrayTopologyContract": "array wrapper constraints", "RowPathIntent": "row path constraints", "ColumnPathIntent": "column path constraints", "ControlPathIntent": "control path constraints", "PhysicalModuleRegistry": "module implementation availability"}, {"array_region": "ARRAY_CORE and boundary wrapper region", "row_periphery_region": "decoder and WL driver region", "column_periphery_region": "precharge/mux/sense/write region", "control_region": "control logic and timing region", "power_region": "reserved top-level power channels", "top_bbox": "generator-owned final bounding box", "placement_plan": "region-level and instance-level placement intent"}, ("Floorplanner owns adjacency and reserved channels, not just XY placement.",)),
            GeneratorInterface("R3 Generators", {"BitcellArrayPhysicalGenerator": "array wrapper composition rules", "RowPeripheryPhysicalGenerator": "row periphery composition rules", "ColumnPeripheryPhysicalGenerator": "column periphery composition rules", "ControlPeripheryPhysicalGenerator": "control region composition rules"}, {"structure_complete_module_layouts": "module-level geometry bundles", "placement-ready module geometry": "placed region-local module geometry", "pitch-aligned boundaries": "array/row/column alignment surfaces"}, ("R3 stops at structure-complete prototype geometry, before full routing closure.",)),
            GeneratorInterface("R4 Routers", {"WordlineRouter": "row path to array routing ownership", "BitlineRouter": "column path to array routing ownership", "ControlRouter": "control spine routing ownership", "PowerPlanner": "power distribution ownership"}, {"wordline_routes": "WL driver to array row routes", "bitline_routes": "BL/BR and column-path routes", "control_routes": "control and timing routes", "power_routes": "VDD/GND distribution routes", "net_to_shape_map": "semantic net to geometry mapping"}, ("R4 adds routing, power, and pin proof on top of the R3 structure.",)),
            GeneratorInterface("PinLabelExporter", {"pin_intent": "top-level IO/control/power naming contract", "routes": "route-backed geometry or pin shapes"}, {"top_level_pin_shapes": "geometry-backed pin shapes", "top_level_labels": "text labels aligned to pin intent", "pin_export_report": "pin coverage and naming audit"}, ("Pin export must not rely on contract-only placeholders once R4 is implemented.",)),
            GeneratorInterface("GDSBackend", {"generator_layout_objects": "generator-owned hierarchy objects", "pin_shapes": "final pin geometry"}, {"structure_complete_sram_gds": "R3 or R4 GDS artifact depending on implemented stage"}, ("Must reuse the project GDS backend instead of OpenRAM save().",)),
            GeneratorInterface("ValidationHookManager", {"generated_artifacts": "placement, routes, pins, gds, evidence metadata"}, {"sanity_report": "basic structural checks", "topology_validation_report": "region and hierarchy checks", "routing_audit": "route coverage status", "power_audit": "VDD/GND distribution status", "pin_audit": "pin naming and reachability status"}, ("Validation hooks must preserve False signoff claims until later evidence exists.",)),
        ]

    def _build_dataflow(self, array_contract: dict[str, Any], row_intent: dict[str, Any], column_intent: dict[str, Any], control_intent: dict[str, Any], power_intent: dict[str, Any], pin_intent: dict[str, Any]) -> GeneratorDataflow:
        return GeneratorDataflow(
            flow_name="openyield_intent_to_gds_dataflow",
            stages=(
                {"stage_name": "OpenYield semantic contracts", "inputs": ["OpenYield netlist semantics", "OpenYield module/connection contracts"], "outputs": ["R1 layout intent inputs"], "classification": "openyield_origin"},
                {"stage_name": "R1 layout intent", "inputs": ["openyield_sram_layout_intent", "array/row/column/control/power/pin intent"], "outputs": ["generator-consumable semantic/physical contracts"], "classification": "r1_rule_surface"},
                {"stage_name": "CanonicalSramParameterModel", "inputs": ["LoadedLayoutIntent"], "outputs": ["rows", "cols", "address widths", "pitch requirements"], "classification": "derived_parameter_model"},
                {"stage_name": "PhysicalModuleRegistry", "inputs": ["module role map", "GDS inventory", "generator inventory"], "outputs": ["reuse decisions", "implementation ownership"], "classification": "reuse_and_binding"},
                {"stage_name": "Array / row / column / control generators", "inputs": ["parameter model", "path intents", "registry"], "outputs": ["structure-complete module layouts", "alignment boundaries"], "classification": "generator_owned_physical_composition"},
                {"stage_name": "SRAMTopologyFloorplanner", "inputs": ["module layouts", "topology constraints"], "outputs": ["placement_plan", "top_bbox", "regions"], "classification": "array_centric_floorplan"},
                {"stage_name": "WL / BL / control / power routing", "inputs": ["placement_plan", "net role map", "power intent"], "outputs": ["signal/power routes", "net_to_shape_map"], "classification": "r4_route_and_power_layer"},
                {"stage_name": "PinLabelExporter", "inputs": ["pin intent", "routes", "placement"], "outputs": ["pin shapes", "labels", "pin report"], "classification": "pin_export_layer"},
                {"stage_name": "GDSBackend", "inputs": ["generator-owned hierarchy and pin geometry"], "outputs": ["structure_complete_sram_gds"], "classification": "serialization_backend"},
                {"stage_name": "ValidationHookManager", "inputs": ["gds", "placement", "route", "pin", "power metadata"], "outputs": ["sanity/topology/routing/power/pin audits"], "classification": "evidence_and_gate_layer"},
            ),
            openyield_inputs=(
                "Semantic contracts define SRAM function and naming.",
                "R1 layout intent defines path-group responsibilities and alignment expectations.",
                f"Pin intent exposes top-level pins: {', '.join(pin_intent['clock_and_control_pins'])} plus addr/din/dout buses.",
            ),
            r1_rules=(
                array_contract["num_rows_to_wl_relation"],
                row_intent["pitch_alignment_expectation"],
                column_intent["pitch_expectation"],
                control_intent["r4_router_requirements"][0],
                power_intent["top_level_power_pin_export_expectation"],
            ),
            learned_from_openram=(
                "Canonical parameter normalization precedes layout generation.",
                "Array, row path, column path, and control path are distinct generator boundaries.",
                "Floorplanning and routing are SRAM-specific, not generic top-level patching.",
                "GDS serialization is separated from geometry construction.",
            ),
            openyield_specific_mechanisms=(
                "R1 layout intent is the generator contract, not an OpenRAM config mirror.",
                "OpenYield net names and module physical roles remain visible through net-to-shape mapping.",
                "Existing candidate assembly artifacts are treated only as reusable metadata or cautionary examples.",
            ),
            legacy_candidate_limits=(
                "old top_level_candidate.gds is a non-authoritative legacy artifact and cannot define the new generator architecture",
                "old candidate-only placement strategy is not promoted into the new floorplanner",
                "contract-pin-only assumptions remain insufficient for R3 structure-complete or R4 route-backed proof",
            ),
            r3_r4_to_r5_support=(
                "R3 emits structure-complete hierarchy and instance ownership for later verification intake.",
                "R4 adds route-backed net, power, and pin evidence needed by R5 validation.",
                "ValidationHookManager and NetToShapeMapper form the handoff surface for later DRC/LVS/pin audits without claiming closure now.",
            ),
        )

    def _build_reuse_decision(self) -> GeneratorReuseDecision:
        return GeneratorReuseDecision(
            reusable_now=(
                {"item": "Custom GDS backend and hierarchy export experience", "reason": "Existing gds_writer.py and gds_hierarchy_export.py already solve project-local serialization and import concerns."},
                {"item": "Module metadata and generator manifest framework", "reason": "Module inventories, manifests, bbox, pin, and rail metadata are directly useful to the new registry layer."},
                {"item": "Validation report and evidence framework", "reason": "Existing JSON/MD report patterns and sanity checks can host R3/R4 audits."},
                {"item": "DRC triage framework", "reason": "Later validation evidence can still reuse the current external DRC marker analysis flow."},
                {"item": "R1 layout intent framework", "reason": "R1 is the authoritative semantic/physical contract for the new generator front end."},
            ),
            adaptable=(
                {"item": "module_gds_generators.py", "reason": "Reuse registry conventions and standalone metadata, but not as the full SRAM generator."},
                {"item": "top_level_assembly.py import/write utilities", "reason": "Selected GDS import and output helpers are reusable after removing candidate-only placement assumptions."},
                {"item": "top_level_validation.py sanity logic", "reason": "Structural checks and report formatting are reusable as generator-stage validation hooks."},
                {"item": "OpenRAM hierarchy_layout primitive API ideas", "reason": "Primitive routing and pin-export concepts are informative, but implementation remains self-developed."},
            ),
            do_not_reuse_or_extend=(
                {"item": "old top_level_candidate.gds", "reason": "Legacy candidate output is evidence only; it is not the new generator substrate."},
                {"item": "old candidate-only placement strategy", "reason": "The new floorplanner must be array-centric and generator-owned."},
                {"item": "contract-pin-only signoff assumption", "reason": "R3/R4 need route- and geometry-backed ownership, not only contract edges."},
                {"item": "patching top_level_assembly into full SRAM generator", "reason": "That path would preserve the wrong abstraction boundary and technical debt."},
                {"item": "OpenRAM OPTS/global-state architecture", "reason": "The new flow should remain local, explicit, and intent-driven."},
                {"item": "OpenRAM full save() mixed flow", "reason": "OpenYield should keep backend serialization separate from generator composition logic."},
                {"item": "OpenRAM multi-bank/multi-port complexity at R3", "reason": "Current supported scope is intentionally single-bank and single-port."},
            ),
        )

    def _build_r3_plan(self, baseline: dict[str, Any]) -> R3MinimumImplementationPlan:
        return R3MinimumImplementationPlan(
            target_configuration={"word_size": baseline["word_size"], "num_words": baseline["num_words"], "words_per_row": baseline["words_per_row"], "parameterized_beyond_baseline": True},
            minimum_scope=(
                "array-centric layout with bitcell_array as the physical core",
                "generator-owned main/dummy/replica array placement with meaningful boundary positions",
                "row decoder and wordline driver composition aligned to row pitch",
                "precharge/column_mux/sense_amp/write_driver composition aligned to column pitch",
                "control modules placed in a dedicated periphery region with explicit ownership",
                "structure-complete SRAM GDS prototype generation through the existing GDS backend",
                "R3 structure report covering hierarchy, placement regions, and claimed limits",
            ),
            explicitly_not_required=("DRC clean", "LVS clean", "complete routing closure", "timing closure", "multi-bank support", "multi-port support"),
            deliverables=("structure-complete module layouts", "placement_plan with array/row/column/control regions", "structure_complete_sram_gds prototype", "R3 structure report with non-signoff gate wording"),
            architecture_constraints=("Do not hard-code 4x4, even though the baseline config remains 4x4.", "Do not use OpenRAM as a black-box generator.", "Do not route everything in R3; leave WL/BL/control/power/pin proof to R4."),
        )

    def _build_r4_plan(self) -> R4RoutingPowerPinPlan:
        return R4RoutingPowerPinPlan(
            wordline_router_scope=("Route WL driver outputs to bitcell rows", "Own exactly one WL per physical row", "Keep all WL routes row-pitch aligned"),
            bitline_router_scope=("Route bitcell BL/BR to precharge", "Route bitcell BL/BR to column mux, sense amp, and write driver as required", "Keep all BL/BR routes column-pitch aligned"),
            control_router_scope=("Route precharge_en to precharge", "Route sense_en to sense_amp", "Route write_en to write_driver", "Route wordline_en to the wordline path", "Route clk and gated_clk through control and DFF paths"),
            power_planner_scope=("Plan array VDD/GND distribution", "Plan row path VDD/GND distribution", "Plan column path VDD/GND distribution", "Plan control path VDD/GND distribution", "Export top-level VDD/GND pins"),
            pin_label_exporter_scope=("Export addr pins", "Export din pins", "Export dout pins", "Export clk and control pins", "Export VDD/GND pins"),
            net_to_shape_mapper_scope=("Track OpenYield net name", "Track source instance/pin", "Track target instance/pin", "Track geometry shape ids or bbox handles", "Track routing status"),
            r5_support=("Provide semantic-to-geometry net coverage for validation", "Provide route-backed pin export evidence for naming audits", "Provide power and routing audits without claiming signoff closure"),
        )

    def _build_component_plan(self, components: list[GeneratorComponent]) -> dict[str, Any]:
        phases: dict[str, list[str]] = {"P0": [], "P1": [], "P2": []}
        for component in components:
            phases[component.implementation_priority].append(component.component_name)
        return {
            "plan_name": "openyield_generator_component_plan",
            "phases": {
                "P0": {"goal": "Unblock R3 structure-complete prototype architecture and generator-owned floorplanning", "components": phases["P0"]},
                "P1": {"goal": "Complete traceability, backend binding, and structure-stage validation", "components": phases["P1"]},
                "P2": {"goal": "Add R4 routing, power, and pin proof layers", "components": phases["P2"]},
            },
        }

    def _build_report(self, architecture: OpenYieldGeneratorArchitecture, r0_report: dict[str, Any], r1_report: dict[str, Any], net_role_rows: list[dict[str, str]], module_role_rows: list[dict[str, str]], registry: dict[str, Any]) -> dict[str, Any]:
        component_count = len(architecture.components)
        required_r3_count = sum(1 for component in architecture.components if component.required_for_R3)
        required_r4_count = sum(1 for component in architecture.components if component.required_for_R4)
        new_code_required_count = sum(1 for component in architecture.components if component.new_code_required)
        reusable_count = sum(1 for component in architecture.components if component.reuse_existing_project_code)
        blockers: list[str] = []
        if not r0_report.get("openram_source_found", False):
            blockers.append("R0 audit does not confirm OpenRAM source evidence.")
        if not r1_report.get("can_enter_R2_generator_architecture_design", False):
            blockers.append("R1 gate does not allow entry to R2.")
        if not net_role_rows:
            blockers.append("R1 net-to-layout-role map is empty.")
        if not module_role_rows:
            blockers.append("R1 module-to-physical-role map is empty.")
        if not registry["available_hardmacros"]:
            blockers.append("PhysicalModuleRegistry found no reusable hardmacro metadata.")
        return {
            "R2_generator_architecture_available": True,
            "generator_dataflow_available": True,
            "module_interfaces_available": True,
            "component_plan_available": True,
            "r3_minimum_implementation_plan_available": True,
            "r4_routing_power_pin_plan_available": True,
            "reuse_decision_available": True,
            "architecture_matrix_available": True,
            "component_count": component_count,
            "required_R3_component_count": required_r3_count,
            "required_R4_component_count": required_r4_count,
            "new_code_required_component_count": new_code_required_count,
            "reusable_component_count": reusable_count,
            "remaining_R2_blockers": blockers,
            "remaining_R2_blockers_count": len(blockers),
            "can_claim_R2_generator_architecture_defined_now": len(blockers) == 0 and component_count >= 12,
            "can_enter_R3_structure_complete_gds_minimum_implementation": len(blockers) == 0 and component_count >= 12,
            "can_claim_structure_complete_sram_gds_now": False,
            "can_claim_drc_clean_now": False,
            "can_claim_lvs_clean_now": False,
            "can_claim_timing_closure_now": False,
            "can_claim_signoff_ready_now": False,
        }

    def _write_architecture(self, out_dir: Path, architecture: OpenYieldGeneratorArchitecture) -> None:
        _json_dump(out_dir / "openyield_sram_generator_architecture.json", architecture.to_dict())
        lines = [
            "# OpenYield SRAM Generator Architecture",
            "",
            f"- intent_centric: `{architecture.intent_centric}`",
            f"- openram_independent_main_flow: `{architecture.openram_independent_main_flow}`",
            f"- component_count: `{len(architecture.components)}`",
            "",
            "## Architecture Constraints",
            "",
        ]
        lines.extend(f"- {item}" for item in architecture.architecture_constraints)
        lines.extend(["", "## Components", ""])
        for component in architecture.components:
            lines.extend([
                f"### {component.component_name}",
                "",
                f"- category: `{component.component_category}`",
                f"- responsibility: {component.responsibility}",
                f"- input_artifacts: `{'; '.join(component.input_artifacts)}`",
                f"- output_artifacts: `{'; '.join(component.output_artifacts)}`",
                f"- depends_on: `{'; '.join(component.depends_on)}`",
                f"- learned_from_openram_mechanism: {component.learned_from_openram_mechanism}",
                f"- openyield_specific_behavior: {component.openyield_specific_behavior}",
                f"- reuse_existing_project_code: {component.reuse_existing_project_code}",
                f"- new_code_required: `{component.new_code_required}`",
                f"- required_for_R3: `{component.required_for_R3}`",
                f"- required_for_R4: `{component.required_for_R4}`",
                f"- risk: {component.risk}",
                f"- implementation_notes: {component.implementation_notes}",
                "",
            ])
        _write_text(out_dir / "openyield_sram_generator_architecture.md", "\n".join(lines))

    def _write_dataflow(self, out_dir: Path, dataflow: GeneratorDataflow) -> None:
        _json_dump(out_dir / "openyield_generator_dataflow.json", dataflow.to_dict())
        lines = [
            "# OpenYield Generator Dataflow",
            "",
            "OpenYield semantic contracts",
            "        ↓",
            "R1 layout intent",
            "        ↓",
            "CanonicalSramParameterModel",
            "        ↓",
            "PhysicalModuleRegistry",
            "        ↓",
            "Array / row / column / control generators",
            "        ↓",
            "SRAMTopologyFloorplanner",
            "        ↓",
            "WL / BL / control / power routing",
            "        ↓",
            "PinLabelExporter",
            "        ↓",
            "GDSBackend",
            "        ↓",
            "ValidationHookManager",
            "",
            "## Stages",
            "",
        ]
        for stage in dataflow.stages:
            lines.extend([
                f"### {stage['stage_name']}",
                "",
                f"- inputs: `{'; '.join(stage['inputs'])}`",
                f"- outputs: `{'; '.join(stage['outputs'])}`",
                f"- classification: `{stage['classification']}`",
                "",
            ])
        for title, items in [
            ("OpenYield Inputs", dataflow.openyield_inputs),
            ("R1 Rules", dataflow.r1_rules),
            ("Learned From OpenRAM", dataflow.learned_from_openram),
            ("OpenYield-Specific", dataflow.openyield_specific_mechanisms),
            ("Legacy Candidate Limits", dataflow.legacy_candidate_limits),
            ("R3/R4 To R5 Support", dataflow.r3_r4_to_r5_support),
        ]:
            lines.extend([f"## {title}", ""])
            lines.extend(f"- {item}" for item in items)
            lines.append("")
        _write_text(out_dir / "openyield_generator_dataflow.md", "\n".join(lines))

    def _write_interfaces(self, out_dir: Path, interfaces: list[GeneratorInterface]) -> None:
        _json_dump(out_dir / "openyield_generator_module_interfaces.json", {"interfaces": [item.to_dict() for item in interfaces]})
        lines = ["# OpenYield Generator Module Interfaces", ""]
        for interface in interfaces:
            lines.extend([
                f"## {interface.component_name}",
                "",
                "### Inputs",
                "",
                json.dumps(interface.inputs, ensure_ascii=False, indent=2),
                "",
                "### Outputs",
                "",
                json.dumps(interface.outputs, ensure_ascii=False, indent=2),
                "",
                "### Notes",
                "",
            ])
            lines.extend(f"- {note}" for note in interface.notes)
            lines.append("")
        _write_text(out_dir / "openyield_generator_module_interfaces.md", "\n".join(lines))

    def _write_component_plan(self, out_dir: Path, component_plan: dict[str, Any]) -> None:
        _json_dump(out_dir / "openyield_generator_component_plan.json", component_plan)
        lines = ["# OpenYield Generator Component Plan", ""]
        for phase_name, payload in component_plan["phases"].items():
            lines.extend([f"## {phase_name}", "", f"- goal: {payload['goal']}", f"- components: `{'; '.join(payload['components'])}`", ""])
        _write_text(out_dir / "openyield_generator_component_plan.md", "\n".join(lines))

    def _write_r3_plan(self, out_dir: Path, plan: R3MinimumImplementationPlan) -> None:
        _json_dump(out_dir / "openyield_r3_minimum_implementation_plan.json", plan.to_dict())
        lines = ["# OpenYield R3 Minimum Implementation Plan", "", "## Target Configuration", "", json.dumps(plan.target_configuration, ensure_ascii=False, indent=2), "", "## Minimum Scope", ""]
        lines.extend(f"- {item}" for item in plan.minimum_scope)
        lines.extend(["", "## Explicitly Not Required", ""])
        lines.extend(f"- {item}" for item in plan.explicitly_not_required)
        lines.extend(["", "## Deliverables", ""])
        lines.extend(f"- {item}" for item in plan.deliverables)
        lines.extend(["", "## Constraints", ""])
        lines.extend(f"- {item}" for item in plan.architecture_constraints)
        _write_text(out_dir / "openyield_r3_minimum_implementation_plan.md", "\n".join(lines) + "\n")

    def _write_r4_plan(self, out_dir: Path, plan: R4RoutingPowerPinPlan) -> None:
        _json_dump(out_dir / "openyield_r4_routing_power_pin_plan.json", plan.to_dict())
        lines = ["# OpenYield R4 Routing Power Pin Plan", ""]
        for title, items in [
            ("WordlineRouter", plan.wordline_router_scope),
            ("BitlineRouter", plan.bitline_router_scope),
            ("ControlRouter", plan.control_router_scope),
            ("PowerPlanner", plan.power_planner_scope),
            ("PinLabelExporter", plan.pin_label_exporter_scope),
            ("NetToShapeMapper", plan.net_to_shape_mapper_scope),
            ("R5 Support", plan.r5_support),
        ]:
            lines.extend([f"## {title}", ""])
            lines.extend(f"- {item}" for item in items)
            lines.append("")
        _write_text(out_dir / "openyield_r4_routing_power_pin_plan.md", "\n".join(lines))

    def _write_reuse_decision(self, out_dir: Path, decision: GeneratorReuseDecision) -> None:
        _json_dump(out_dir / "openyield_generator_reuse_decision.json", decision.to_dict())
        lines = ["# OpenYield Generator Reuse Decision", ""]
        for title, items in [
            ("Can Reuse", decision.reusable_now),
            ("Can Adapt", decision.adaptable),
            ("Do Not Reuse Or Extend", decision.do_not_reuse_or_extend),
        ]:
            lines.extend([f"## {title}", ""])
            for item in items:
                lines.append(f"- {item['item']}: {item['reason']}")
            lines.append("")
        _write_text(out_dir / "openyield_generator_reuse_decision.md", "\n".join(lines))

    def _write_matrix(self, rows: list[dict[str, Any]]) -> None:
        _write_csv(self.context["out_matrix_csv"], MATRIX_COLUMNS, rows)
        _write_text(self.context["out_matrix_md"], "# OpenYield R2 Generator Architecture Matrix\n\n" + _md_table(MATRIX_COLUMNS, rows))

    def _write_report(self, report: dict[str, Any], architecture: OpenYieldGeneratorArchitecture, dataflow: GeneratorDataflow, interfaces: list[GeneratorInterface], r3_plan: R3MinimumImplementationPlan, r4_plan: R4RoutingPowerPinPlan, reuse_decision: GeneratorReuseDecision) -> None:
        _json_dump(self.context["out_json"], report)
        lines = [
            "# OpenYield R2 Generator Architecture Report",
            "",
            f"- R2_generator_architecture_available: `{report['R2_generator_architecture_available']}`",
            f"- generator_dataflow_available: `{report['generator_dataflow_available']}`",
            f"- module_interfaces_available: `{report['module_interfaces_available']}`",
            f"- component_plan_available: `{report['component_plan_available']}`",
            f"- r3_minimum_implementation_plan_available: `{report['r3_minimum_implementation_plan_available']}`",
            f"- r4_routing_power_pin_plan_available: `{report['r4_routing_power_pin_plan_available']}`",
            f"- reuse_decision_available: `{report['reuse_decision_available']}`",
            f"- architecture_matrix_available: `{report['architecture_matrix_available']}`",
            f"- component_count: `{report['component_count']}`",
            f"- required_R3_component_count: `{report['required_R3_component_count']}`",
            f"- required_R4_component_count: `{report['required_R4_component_count']}`",
            f"- new_code_required_component_count: `{report['new_code_required_component_count']}`",
            f"- reusable_component_count: `{report['reusable_component_count']}`",
            f"- remaining_R2_blockers_count: `{report['remaining_R2_blockers_count']}`",
            f"- can_claim_R2_generator_architecture_defined_now: `{report['can_claim_R2_generator_architecture_defined_now']}`",
            f"- can_enter_R3_structure_complete_gds_minimum_implementation: `{report['can_enter_R3_structure_complete_gds_minimum_implementation']}`",
            f"- can_claim_structure_complete_sram_gds_now: `{report['can_claim_structure_complete_sram_gds_now']}`",
            f"- can_claim_drc_clean_now: `{report['can_claim_drc_clean_now']}`",
            f"- can_claim_lvs_clean_now: `{report['can_claim_lvs_clean_now']}`",
            f"- can_claim_timing_closure_now: `{report['can_claim_timing_closure_now']}`",
            f"- can_claim_signoff_ready_now: `{report['can_claim_signoff_ready_now']}`",
            "",
            "## Remaining R2 Blockers",
            "",
        ]
        if report["remaining_R2_blockers"]:
            lines.extend(f"- {item}" for item in report["remaining_R2_blockers"])
        else:
            lines.append("- none")
        lines.extend([
            "",
            "## Architecture Summary",
            "",
            f"- architecture_name: `{architecture.architecture_name}`",
            f"- component_count: `{len(architecture.components)}`",
            f"- dataflow_stage_count: `{len(dataflow.stages)}`",
            f"- interface_count: `{len(interfaces)}`",
            f"- r3_minimum_scope_count: `{len(r3_plan.minimum_scope)}`",
            f"- r4_scope_count: `{len(r4_plan.wordline_router_scope) + len(r4_plan.bitline_router_scope) + len(r4_plan.control_router_scope)}`",
            f"- reuse_decision_sections: `{len(reuse_decision.reusable_now)}/{len(reuse_decision.adaptable)}/{len(reuse_decision.do_not_reuse_or_extend)}`",
            "",
        ])
        _write_text(self.context["out_report"], "\n".join(lines))

    def _write_gap_summary(self, report: dict[str, Any]) -> None:
        lines = [
            "# R2 Generator Architecture Gap Summary",
            "",
            f"- remaining_R2_blockers_count: `{report['remaining_R2_blockers_count']}`",
            f"- can_claim_R2_generator_architecture_defined_now: `{report['can_claim_R2_generator_architecture_defined_now']}`",
            f"- can_enter_R3_structure_complete_gds_minimum_implementation: `{report['can_enter_R3_structure_complete_gds_minimum_implementation']}`",
            "",
            "## Remaining Blockers",
            "",
        ]
        if report["remaining_R2_blockers"]:
            lines.extend(f"- {item}" for item in report["remaining_R2_blockers"])
        else:
            lines.append("- none")
        _write_text(self.context["repo_root"] / "docs/evidence/R2_generator_architecture_gap_summary.md", "\n".join(lines) + "\n")
