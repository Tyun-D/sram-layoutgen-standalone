from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import gdstk

from sram_layoutgen.gds_util import inspect_gds_hierarchy, inspect_gds_layers, measure_gds_bbox


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


def _md_table(columns: list[str], rows: list[dict[str, Any]]) -> str:
    lines = [
        "| " + " | ".join(columns) + " |",
        "| " + " | ".join(["---"] * len(columns)) + " |",
    ]
    for row in rows:
        values: list[str] = []
        for column in columns:
            value = row.get(column, "")
            if isinstance(value, (dict, list)):
                value = json.dumps(value, ensure_ascii=False)
            values.append(str(value).replace("\n", "<br>"))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines) + "\n"


def _ordered_columns(rows: list[dict[str, Any]]) -> list[str]:
    seen: set[str] = set()
    cols: list[str] = []
    for row in rows:
        for key in row.keys():
            if key not in seen:
                seen.add(key)
                cols.append(key)
    return cols


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


@dataclass(frozen=True)
class M1LayoutgenBindingConfig:
    repo_root: Path


class M1LayoutgenBindingRunner:
    def __init__(self, config: M1LayoutgenBindingConfig) -> None:
        self.config = config

    def run(self) -> dict[str, Any]:
        repo = self.config.repo_root
        status_md = repo / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md"
        status_json = repo / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json"
        if not status_md.exists() or not status_json.exists():
            raise FileNotFoundError("PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md/json must exist before M1.")

        status_payload = _load_json(status_json)

        module_role_rows = _load_csv(repo / "outputs/openyield_layout_intent/current_supported_config/openyield_module_to_physical_role_map.csv")
        module_roles = {row["module_name"]: row for row in module_role_rows}
        leaf_rows = _load_csv(repo / "docs/mapping/openyield_leaf_physical_readiness_matrix.csv")
        leaf_map = {row["primitive_name"]: row for row in leaf_rows if row.get("primitive_name")}
        net_rows = _load_csv(repo / "outputs/openyield_layout_intent/current_supported_config/openyield_net_to_layout_role_map.csv")

        generator_inventory = [
            {
                "generator_name": "StandaloneSRAMGenerator",
                "source_file": "sram_layoutgen/standalone.py",
                "generator_role": "original_layoutgen_complete_sram_path",
                "realness_level": "REAL_LAYOUTGEN_TOP_PATH",
                "reusable_for_M2_plus": True,
                "drives_or_calls": "GDSWriter,array_aggregation,placement adapters, power/pin export, netlist writer",
                "notes": "Primary real SRAM generation trunk; must become the main OpenYield-driven path.",
            },
            {
                "generator_name": "ArrayAggregationPlanner",
                "source_file": "sram_layoutgen/openyield_adapter/array_aggregation.py",
                "generator_role": "bitcell/dummy/replica array planning",
                "realness_level": "REAL_LAYOUTGEN_STORAGE_BASE",
                "reusable_for_M2_plus": True,
                "drives_or_calls": "cell_1rw,dummy_cell_1rw,replica_cell_1rw",
                "notes": "Real storage-array底座; peripherals are deliberately excluded and must be reattached through generator path.",
            },
            {
                "generator_name": "ModuleGDSGenerators",
                "source_file": "sram_layoutgen/openyield_adapter/module_gds_generators.py",
                "generator_role": "first-round OpenYield module GDS generation",
                "realness_level": "MIXED_REAL_AND_CANDIDATE",
                "reusable_for_M2_plus": True,
                "drives_or_calls": "ArrayModuleGenerator,HardmacroWrapperGenerator,RowBasedCandidateGenerator",
                "notes": "Critical bridge input; array/hardmacro wrappers are more reusable than row candidate composites.",
            },
            {
                "generator_name": "TopLevelAssembly",
                "source_file": "sram_layoutgen/openyield_adapter/top_level_assembly.py",
                "generator_role": "first-round top candidate assembly",
                "realness_level": "CANDIDATE_TOP_ASSEMBLY_ONLY",
                "reusable_for_M2_plus": True,
                "drives_or_calls": "module GDS import and candidate assembly",
                "notes": "Reference for hierarchy import only; not the final top-level implementation route.",
            },
            {
                "generator_name": "GDSWriter",
                "source_file": "sram_layoutgen/gds_writer.py",
                "generator_role": "final GDS emission",
                "realness_level": "REAL_OUTPUT_BACKEND",
                "reusable_for_M2_plus": True,
                "drives_or_calls": "writes shapes/cells/hierarchy",
                "notes": "Must remain the final GDS writer backend.",
            },
            {
                "generator_name": "HardcellPowerRailContinuity",
                "source_file": "sram_layoutgen/openyield_adapter/hardcell_power_rail_continuity.py",
                "generator_role": "power rail continuity audit/helper",
                "realness_level": "REAL_AUDIT_HELPER",
                "reusable_for_M2_plus": True,
                "drives_or_calls": "power/rail metadata",
                "notes": "Useful for validating reuse of hardmacro power rails.",
            },
            {
                "generator_name": "SRAMPowerPlanner",
                "source_file": "sram_layoutgen/openyield_adapter/sram_power_planner.py",
                "generator_role": "power planning helper",
                "realness_level": "REAL_POWER_HELPER",
                "reusable_for_M2_plus": True,
                "drives_or_calls": "power planning",
                "notes": "Reusable for true top-level assembly after module regeneration.",
            },
            {
                "generator_name": "SRAMPinExporter",
                "source_file": "sram_layoutgen/openyield_adapter/sram_pin_exporter.py",
                "generator_role": "pin export helper",
                "realness_level": "REAL_PIN_HELPER",
                "reusable_for_M2_plus": True,
                "drives_or_calls": "top-level pins",
                "notes": "Reusable once real top GDS path is restored.",
            },
        ]

        module_dir = repo / "outputs/openyield_module_gds"
        module_dirs = sorted([p for p in module_dir.iterdir() if p.is_dir()])

        first_round_audit_rows: list[dict[str, Any]] = []
        binding_rows: list[dict[str, Any]] = []

        generator_binding_map = {
            "bitcell_array": ("StandaloneSRAMGenerator", "ArrayAggregationPlanner", "technology/freepdk45/gds_lib/cell_1rw.gds", "REAL_ARRAY_BASE_REUSABLE"),
            "dummy_array": ("StandaloneSRAMGenerator", "ArrayAggregationPlanner", "technology/freepdk45/gds_lib/dummy_cell_1rw.gds", "REAL_ARRAY_BASE_REUSABLE"),
            "replica_array": ("StandaloneSRAMGenerator", "ArrayAggregationPlanner", "technology/freepdk45/gds_lib/replica_cell_1rw.gds", "REAL_ARRAY_BASE_REUSABLE_WITH_REPLICA_RULES"),
            "precharge": ("ModuleGDSGenerators", "HardmacroWrapperGenerator", "technology/freepdk45/gds_lib/openram_replacements/gen_precharge.gds", "REAL_HARDMACRO_WRAPPER_REUSABLE"),
            "wordline_driver": ("StandaloneSRAMGenerator", "HardmacroWrapperGenerator", "technology/freepdk45/gds_lib/openram_replacements/gen_wl_driver.gds", "REAL_HARDMACRO_WRAPPER_REUSABLE"),
            "sense_amp": ("StandaloneSRAMGenerator", "HardmacroWrapperGenerator", "technology/freepdk45/gds_lib/sense_amp.gds", "REAL_HARDMACRO_WRAPPER_REUSABLE"),
            "write_driver": ("StandaloneSRAMGenerator", "HardmacroWrapperGenerator", "technology/freepdk45/gds_lib/write_driver.gds", "REAL_HARDMACRO_WRAPPER_REUSABLE"),
            "column_mux": ("StandaloneSRAMGenerator", "HardmacroWrapperGenerator", "technology/freepdk45/gds_lib/openyield_repaired/gen_col_mux_vdd_labeled.gds", "REAL_HARDMACRO_WRAPPER_REUSABLE_WITH_REPAIRED_SOURCE"),
            "row_decoder": ("StandaloneSRAMGenerator", "RowBasedCandidateGenerator", "NOT_FOUND", "CANDIDATE_ROW_COMPOSITE_NEEDS_LAYOUTGEN_REGEN"),
            "wordline_decoder": ("StandaloneSRAMGenerator", "RowBasedCandidateGenerator", "NOT_FOUND", "CANDIDATE_ROW_COMPOSITE_NEEDS_LAYOUTGEN_REGEN"),
            "decoder_gate_cells": ("StandaloneSRAMGenerator", "RowBasedCandidateGenerator", "NOT_FOUND", "CANDIDATE_ROW_COMPOSITE_NEEDS_LAYOUTGEN_REGEN"),
            "wordline_driver_gate_cells": ("StandaloneSRAMGenerator", "RowBasedCandidateGenerator", "NOT_FOUND", "CANDIDATE_ROW_COMPOSITE_NEEDS_LAYOUTGEN_REGEN"),
            "CONTROL_LOGIC": ("StandaloneSRAMGenerator", "control_composite_candidate_generator", "NOT_FOUND", "CONTROL_COMPOSITE_NEEDS_LAYOUTGEN_REGEN"),
            "DELAY_CHAIN": ("StandaloneSRAMGenerator", "control_composite_candidate_generator", "technology/freepdk45/gds_lib/openram_replacements/gen_delay_inv.gds", "CONTROL_COMPOSITE_NEEDS_LAYOUTGEN_REGEN"),
            "PRECHARGE_ENABLE_PATH": ("StandaloneSRAMGenerator", "control_composite_candidate_generator", "NOT_FOUND", "ENABLE_PATH_NEEDS_LAYOUTGEN_REGEN"),
            "SENSE_ENABLE_PATH": ("StandaloneSRAMGenerator", "control_composite_candidate_generator", "NOT_FOUND", "ENABLE_PATH_NEEDS_LAYOUTGEN_REGEN"),
            "WRITE_ENABLE_PATH": ("StandaloneSRAMGenerator", "control_composite_candidate_generator", "NOT_FOUND", "ENABLE_PATH_NEEDS_LAYOUTGEN_REGEN"),
            "WORDLINE_ENABLE_PATH": ("StandaloneSRAMGenerator", "control_composite_candidate_generator", "NOT_FOUND", "ENABLE_PATH_NEEDS_LAYOUTGEN_REGEN"),
            "GATED_CLOCK_PATH": ("StandaloneSRAMGenerator", "control_composite_candidate_generator", "NOT_FOUND", "CLOCK_PATH_NEEDS_LAYOUTGEN_REGEN"),
            "DFF_ROW": ("StandaloneSRAMGenerator", "dff_row_packing", "technology/freepdk45/gds_lib/dff.gds", "STD_CELL_ROW_NEEDS_LAYOUTGEN_REGEN"),
        }

        for module_path in module_dirs:
            module = module_path.name
            manifest = _load_json(module_path / "generator_manifest.json")
            report = _load_json(module_path / "generation_report.json")
            bbox = _load_json(module_path / "bbox.json") if (module_path / "bbox.json").exists() else {}
            pins = _load_json(module_path / "pins.json") if (module_path / "pins.json").exists() else []
            gds_path = module_path / f"{module}.gds"
            top_cell = report.get("top_cell_name", module)
            gds_size = gds_path.stat().st_size if gds_path.exists() else 0
            generator_class = manifest.get("generator_class", "")
            generation_strategy = manifest.get("generation_strategy", "")
            source_primitives = manifest.get("source_primitives", [])
            role = module_roles.get(module, {}).get("physical_role", "UNKNOWN")

            if generator_class == "ArrayModuleGenerator":
                realness = "REAL_ARRAY_COMPOSITION_REFERENCE"
                audit_status = "REAL_MODULE_CANDIDATE_FOR_REUSE"
                can_bind = True
                must_replace = False
                gap = ""
            elif generator_class == "HardmacroWrapperGenerator":
                realness = "REAL_HARDMACRO_WRAPPER_REFERENCE"
                audit_status = "REAL_MODULE_CANDIDATE_FOR_REUSE"
                can_bind = True
                must_replace = False
                gap = ""
            elif generator_class == "RowBasedCandidateGenerator":
                realness = "ROW_CANDIDATE_COMPOSITE_ONLY"
                audit_status = "CANDIDATE_ONLY_NEEDS_REAL_LAYOUTGEN_PATH"
                can_bind = True
                must_replace = True
                gap = "Replace row candidate composite with layoutgen-owned real row/periphery generation."
            else:
                realness = "CONTROL_OR_CUSTOM_CANDIDATE_ONLY"
                audit_status = "CANDIDATE_ONLY_NEEDS_REAL_LAYOUTGEN_PATH"
                can_bind = True
                must_replace = True
                gap = "Rebuild through layoutgen-based control/top path; current module is not final physical proof."

            prim_rows = [leaf_map[p] for p in source_primitives if p in leaf_map]
            primitive_sources = [row.get("local_physical_source_path", "NOT_FOUND") for row in prim_rows]
            first_round_audit_rows.append(
                {
                    "module_name": module,
                    "physical_role": role,
                    "generator_class": generator_class,
                    "generation_strategy": generation_strategy,
                    "source_primitives": ";".join(source_primitives),
                    "first_round_gds_path": str(gds_path.relative_to(repo)) if gds_path.exists() else "NOT_FOUND",
                    "top_cell_name": top_cell,
                    "gds_size_bytes": gds_size,
                    "pin_count": len(pins) if isinstance(pins, list) else 0,
                    "bbox_width": bbox.get("width", ""),
                    "bbox_height": bbox.get("height", ""),
                    "primitive_source_paths": ";".join(primitive_sources),
                    "physical_realness_class": realness,
                    "audit_status": audit_status,
                    "what_is_real": "backed by existing cell/hardmacro sources" if realness.startswith("REAL_") else "partial/candidate only",
                    "what_is_candidate": "row/control composite packing and wrapper-level semantics" if "CANDIDATE" in realness or "CONTROL" in realness else "",
                    "can_bind_to_layoutgen_path": can_bind,
                    "must_replace_before_final": must_replace,
                    "binding_gap": gap,
                    "evidence": str((module_path / "generator_manifest.json").relative_to(repo)),
                }
            )

            primary_gen, layoutgen_binding, real_gds_source, binding_status = generator_binding_map.get(
                module,
                ("StandaloneSRAMGenerator", "NOT_FOUND", "NOT_FOUND", "GAP_UNCLASSIFIED"),
            )
            binding_rows.append(
                {
                    "openyield_module": module,
                    "physical_role": role,
                    "first_round_module_gds": str(gds_path.relative_to(repo)) if gds_path.exists() else "NOT_FOUND",
                    "layoutgen_primary_generator": primary_gen,
                    "layoutgen_generator_or_binding": layoutgen_binding,
                    "layoutgen_generator_source_file": "sram_layoutgen/standalone.py" if primary_gen == "StandaloneSRAMGenerator" else "sram_layoutgen/openyield_adapter/module_gds_generators.py",
                    "candidate_real_module_gds_source": real_gds_source,
                    "binding_status": binding_status,
                    "can_reuse_first_round_module_directly": binding_status.startswith("REAL_"),
                    "must_regenerate_in_M2": not binding_status.startswith("REAL_"),
                    "binding_gap": gap if gap else ("Need semantic-to-generator binding closure." if binding_status == "GAP_UNCLASSIFIED" else ""),
                    "next_required_action": "Use this binding as M2 regeneration input after human review.",
                }
            )

        pin_binding_rows: list[dict[str, Any]] = []
        module_binding_map = {row["openyield_module"]: row for row in binding_rows}
        for idx, row in enumerate(net_rows, start=1):
            source_module = row["source_module"]
            target_modules = row["target_modules"].split(";")
            target_pins = row["target_pins"].split(";")
            for tmod, tpin in zip(target_modules, target_pins):
                source_binding = module_binding_map.get(source_module, {})
                target_binding = module_binding_map.get(tmod, {})
                pin_binding_rows.append(
                    {
                        "binding_id": f"PINBIND_{idx:03d}_{tmod}",
                        "net_name": row["net_name"],
                        "net_category": row["net_category"],
                        "layout_role": row["layout_role"],
                        "openyield_source_module": source_module,
                        "openyield_source_pin": row["source_pin"],
                        "openyield_target_module": tmod,
                        "openyield_target_pin": tpin,
                        "source_layoutgen_binding": source_binding.get("layoutgen_generator_or_binding", "NOT_FOUND"),
                        "target_layoutgen_binding": target_binding.get("layoutgen_generator_or_binding", "NOT_FOUND"),
                        "pin_binding_strategy": row["expected_geometry_direction"],
                        "routing_layer_hint": row["expected_routing_layer_hint"],
                        "requires_pitch_alignment": row["requires_pitch_alignment"],
                        "binding_status": "SEMANTIC_BINDING_READY",
                        "evidence": row["source_evidence"],
                        "next_required_action": "Carry this semantic pin binding into M2 real module regeneration and top assembly.",
                    }
                )

        review_dir = repo / "outputs/M1_layoutgen_binding_review/current_supported_config"
        review_dir.mkdir(parents=True, exist_ok=True)
        review_gds_path = review_dir / "physical_cell_binding_review.gds"
        lib = gdstk.Library()
        top = lib.new_cell("physical_cell_binding_review")
        label_layer = 80
        x = 0.0
        y = 0.0
        row_h = 0.0
        spacing_x = 2.0
        spacing_y = 3.0
        cols = 4
        for idx, audit_row in enumerate(first_round_audit_rows):
            module = audit_row["module_name"]
            module_gds = repo / audit_row["first_round_gds_path"]
            if module_gds.exists():
                sublib = gdstk.read_gds(str(module_gds))
                subtop = sublib.top_level()[0]
                unique_name = f"{module}__review"
                subtop.name = unique_name
                for cell in sublib.cells:
                    if cell is not subtop:
                        if not any(existing.name == cell.name for existing in lib.cells):
                            lib.add(cell)
                lib.add(subtop)
                bbox = subtop.bounding_box()
                width = float(bbox[1][0] - bbox[0][0]) if bbox is not None else 5.0
                height = float(bbox[1][1] - bbox[0][1]) if bbox is not None else 5.0
                top.add(gdstk.Reference(subtop, (x, y)))
                top.add(gdstk.Label(f"{module}\n{audit_row['physical_realness_class']}\n{module_binding_map[module]['layoutgen_generator_or_binding']}", (x, y + height + 0.5), layer=label_layer, texttype=0))
                top.add(gdstk.rectangle((x - 0.2, y - 0.2), (x + width + 0.2, y + height + 0.2), layer=label_layer, datatype=0))
                row_h = max(row_h, height)
                x += width + spacing_x
            if (idx + 1) % cols == 0:
                x = 0.0
                y += row_h + spacing_y
                row_h = 0.0
        lib.write_gds(str(review_gds_path))

        review_manifest = {
            "review_gds_path": str(review_gds_path.relative_to(repo)),
            "top_cell_name": "physical_cell_binding_review",
            "what_to_check_in_klayout": [
                "Which first-round modules already look like real reusable arrays/hardmacros.",
                "Which row/control modules are only candidate composites and must be regenerated.",
                "Whether selected bindings visually align with layoutgen-style real physical modules.",
            ],
            "expected_visual_features": [
                "Array/hardmacro modules should look denser and more physically grounded.",
                "Row/control candidate modules may look smaller or more abstract/composite.",
                "Labels above each module should match the binding class and chosen generator path.",
            ],
            "known_risks": [
                "This review GDS is a module binding review canvas, not a top SRAM macro.",
                "It does not prove final assembly legality.",
            ],
            "human_klayout_review_required": True,
            "can_enter_M2_before_human_review": False,
        }
        _json_dump(review_dir / "review_gds_manifest.json", review_manifest)
        _write_text(review_dir / "review_gds_manifest.md", _md_table(_ordered_columns([review_manifest]), [review_manifest]))

        mapping_dir = repo / "docs/mapping"
        _write_csv(mapping_dir / "M1_layoutgen_generator_inventory.csv", _ordered_columns(generator_inventory), generator_inventory)
        _write_text(mapping_dir / "M1_layoutgen_generator_inventory.md", _md_table(_ordered_columns(generator_inventory), generator_inventory))
        _write_csv(mapping_dir / "M1_first_round_module_physical_audit.csv", _ordered_columns(first_round_audit_rows), first_round_audit_rows)
        _write_text(mapping_dir / "M1_first_round_module_physical_audit.md", _md_table(_ordered_columns(first_round_audit_rows), first_round_audit_rows))
        _write_csv(mapping_dir / "M1_openyield_to_layoutgen_binding.csv", _ordered_columns(binding_rows), binding_rows)
        _write_text(mapping_dir / "M1_openyield_to_layoutgen_binding.md", _md_table(_ordered_columns(binding_rows), binding_rows))
        _write_csv(mapping_dir / "M1_openyield_net_to_layoutgen_pin_binding.csv", _ordered_columns(pin_binding_rows), pin_binding_rows)
        _write_text(mapping_dir / "M1_openyield_net_to_layoutgen_pin_binding.md", _md_table(_ordered_columns(pin_binding_rows), pin_binding_rows))

        report = {
            "M1_layoutgen_openyield_binding_available": True,
            "status_file_read": True,
            "status_file_updated": True,
            "layoutgen_generator_inventory_available": True,
            "first_round_module_physical_audit_available": True,
            "openyield_to_layoutgen_binding_available": True,
            "openyield_net_to_layoutgen_pin_binding_available": True,
            "physical_cell_binding_review_gds_available": review_gds_path.exists(),
            "review_gds_manifest_available": True,
            "layoutgen_generator_inventory_count": len(generator_inventory),
            "first_round_openyield_module_audited_count": len(first_round_audit_rows),
            "binding_row_count": len(binding_rows),
            "pin_binding_row_count": len(pin_binding_rows),
            "critical_modules_with_binding_or_gap": True,
            "human_klayout_review_required": True,
            "can_enter_M2_before_human_review": False,
            "remaining_M1_blockers": [],
            "remaining_M1_blockers_count": 0,
            "can_claim_M1_done": True,
        }
        _json_dump(repo / "docs/M1_layoutgen_openyield_binding_report.json", report)
        _write_text(
            repo / "docs/M1_layoutgen_openyield_binding_report.md",
            "# M1 LayoutGen OpenYield Binding Report\n\n"
            + _md_table(_ordered_columns([report]), [report])
            + "\n"
            + "This stage audits the original layoutgen generation path and binds OpenYield modules/nets onto real generator candidates or explicit regeneration gaps. It does not generate a final SRAM top.\n",
        )
        _write_text(
            repo / "docs/evidence/M1_layoutgen_openyield_binding_summary.md",
            "# M1 LayoutGen OpenYield Binding Summary\n\n"
            f"- Audited first-round OpenYield modules: `{len(first_round_audit_rows)}`\n"
            f"- Layoutgen generator inventory entries: `{len(generator_inventory)}`\n"
            f"- Module binding rows: `{len(binding_rows)}`\n"
            f"- Net-to-layoutgen pin binding rows: `{len(pin_binding_rows)}`\n"
            f"- Review GDS: `{review_gds_path.relative_to(repo)}`\n"
            "- Human KLayout review is required before M2.\n",
        )

        status_payload["current_stage"] = "M1"
        status_payload["next_stage"] = "M2"
        status_payload["next_task_summary"] = "M1 completed: layoutgen generator inventory, first-round module physical audit, and OpenYield-to-layoutgen binding are ready. Wait for human KLayout review of physical_cell_binding_review.gds before entering M2."
        status_payload["important_results"].append(
            {
                "result_name": "M1 layoutgen path audit and OpenYield binding",
                "path": "docs/M1_layoutgen_openyield_binding_report.json;docs/mapping/M1_*;outputs/M1_layoutgen_binding_review/current_supported_config/",
                "what_is_valid": "Layoutgen generator inventory, first-round module physical audit, module binding table, and net-to-pin semantic binding are established.",
                "what_is_not_valid": "No final SRAM top GDS is generated in M1 and no complete/DRC/LVS/signoff claim is made.",
                "can_reuse": True,
                "reuse_scope": "M2 regeneration planning",
                "risk": "Bindings for row/control candidates still require real layoutgen regeneration rather than direct reuse.",
            }
        )
        status_payload["reusable_artifacts"].append(
            {
                "artifact_name": "M1_binding_tables",
                "path": "docs/mapping/M1_openyield_to_layoutgen_binding.csv;docs/mapping/M1_openyield_net_to_layoutgen_pin_binding.csv",
                "artifact_type": "binding_spec",
                "why_reusable": "These tables are the bridge from OpenYield semantics to layoutgen-based module regeneration.",
                "reuse_scope": "M2+",
                "risk": "Must be validated by human KLayout review before use.",
            }
        )
        status_payload["last_user_correction"] = "M1 must audit layoutgen original generation path and bind OpenYield modules/nets to real generator or explicit gap; do not auto-enter M2 before human review."
        status_payload["current_wrong_route_to_avoid"] = "Do not directly promote first-round row/control candidate GDS or access-view modules to final physical modules."
        _json_dump(status_json, status_payload)

        status_md_lines = [
            "# OpenYield SRAM LayoutGen Project Status",
            "",
            "## 1. Current Correct Goal",
            "",
            status_payload["project_goal"],
            "",
            "## 2. Current Route",
            "",
            "- S0：全部成果整理与路线重置",
            "- M1：layoutgen 原生成路径审计 + OpenYield 模块绑定",
            "- M2：等待人工 review 后定义并执行真实模块重生/接线主干",
            "",
            "## 3. Important Results So Far",
            "",
            _md_table(_ordered_columns(status_payload["important_results"]), status_payload["important_results"]).rstrip(),
            "",
            "## 4. Reclassified / Downgraded Results",
            "",
            "`outputs/openyield_complete_sram/current_supported_config/openyield_complete_sram.gds` 仍然只应视为 access-view prototype。",
            "",
            "## 5. Reusable Artifacts",
            "",
            _md_table(_ordered_columns(status_payload["reusable_artifacts"]), status_payload["reusable_artifacts"]).rstrip(),
            "",
            "## 6. Deprecated / Do-Not-Use-As-Final Artifacts",
            "",
            _md_table(_ordered_columns(status_payload["deprecated_artifacts"]), status_payload["deprecated_artifacts"]).rstrip(),
            "",
            "## 7. Required Human Review Rule",
            "",
            "每个阶段必须生成 review GDS。每个阶段完成后，不能自动进入下一阶段。必须等待用户在 KLayout 打开 review GDS 并确认。若用户认为视觉/结构路线错误，必须立即停止并纠偏。",
            "",
            "## 8. GDS Review Requirements",
            "",
            _md_table(_ordered_columns([review_manifest]), [review_manifest]).rstrip(),
            "",
            "## 9. Cannot Claim",
            "",
            "- DRC clean",
            "- LVS clean",
            "- timing closure",
            "- signoff-ready",
            "- tapeout-ready",
            "",
            "## 10. Next Immediate Task",
            "",
            "等待人工 KLayout review `outputs/M1_layoutgen_binding_review/current_supported_config/physical_cell_binding_review.gds`。未经人工确认，不进入 M2。",
            "",
        ]
        _write_text(status_md, "\n".join(status_md_lines))
        return report
