from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.gds_pin_audit import read_gds_labels_and_shapes


OPENYIELD_CANDIDATE_MAP = {
    "TIME": "CONTROL_LOGIC",
    "ADDR_DFF": "DFF_ROW",
    "DATA_DFF": "DFF_ROW",
    "DFF_BUF": "DFF_ROW",
    "delay_chain": "DELAY_CHAIN",
    "wen_delay_chain": "",
    "pdrive": "GATED_CLOCK_PATH",
    "pdrive2_for_pre": "PRECHARGE_ENABLE_PATH",
    "wl_pdrive": "WORDLINE_ENABLE_PATH",
    "AND2": "decoder_gate_cells",
    "AND3": "decoder_gate_cells",
    "PNAND2": "wordline_driver_gate_cells",
    "PNAND3": "decoder_gate_cells",
    "PINV": "wordline_driver_gate_cells",
    "PINV1": "wordline_driver_gate_cells",
    "PINV2": "wordline_driver_gate_cells",
    "PINV3": "wordline_driver_gate_cells",
    "PINV4": "wordline_driver_gate_cells",
    "PINV_wl_en_bar": "wordline_driver_gate_cells",
    "TRANSMISSION_GATE": "",
    "DFF": "",
}

LAYOUTGEN_CELL_MAP = {
    "Pinv": "gen_inv",
    "PINV": "gen_inv",
    "PINV1": "gen_inv",
    "PINV2": "gen_inv",
    "PINV3": "gen_inv",
    "PINV4": "gen_inv",
    "PINV_wl_en_bar": "gen_inv",
    "PNAND2": "gen_nand2",
    "PNAND3": "gen_nand4",
    "AND2": "gen_nand2",
    "AND3": "gen_nand4",
    "dff": "dff",
    "DFF": "dff",
    "DelayChain": "gen_delay_inv",
    "delay_chain": "gen_delay_inv",
    "WenDelayChain": "gen_delay_inv",
    "wen_delay_chain": "gen_delay_inv",
    "DFF_BUF": "dff",
    "ADDR_DFF": "dff",
    "DATA_DFF": "dff",
    "WORDLINEDRIVER": "gen_wl_driver",
    "wl_pdrive": "gen_wl_driver",
    "PRECHARGE": "gen_precharge",
    "WRITEDRIVER": "write_driver",
    "SENSEAMP": "sense_amp",
}

OPENRAM_REFERENCE_MAP = {
    "TIME": "control_logic_rw",
    "ADDR_DFF": "row_addr_dff",
    "DATA_DFF": "data_dff",
    "DFF_BUF": "data_dff",
    "delay_chain": "control_logic_rw delay path",
    "wen_delay_chain": "control_logic_rw write delay path",
    "pdrive": "control_logic_rw gated clock path",
    "pdrive2_for_pre": "control_logic_rw precharge enable path",
    "wl_pdrive": "control_logic_rw wordline enable path",
    "AND2": "decoder primitive gates",
    "AND3": "decoder primitive gates",
    "PNAND2": "decoder primitive gates",
    "PNAND3": "decoder primitive gates",
    "TRANSMISSION_GATE": "latch internals reference only",
    "DFF": "latch internals reference only",
}


def build_physical_mapping_matrix(
    *,
    hierarchy_rows: list[dict[str, Any]],
    openyield_module_gds_dir: Path,
    repo_root: Path,
    openram_gap_matrix: Path,
) -> dict[str, Any]:
    gap_rows = list(csv.DictReader(openram_gap_matrix.open("r", encoding="utf-8", newline="")))
    gap_by_module = {row["module_or_function"]: row for row in gap_rows}
    layoutgen_root = repo_root / "technology" / "freepdk45" / "gds_lib"
    rows: list[dict[str, Any]] = []
    ready = 0
    partial = 0
    reference_only = 0
    missing = 0
    transistor_required = 0
    layoutgen_control_cells: set[str] = set()
    openyield_control_gds: set[str] = set()
    bbox_count = 0
    pin_count = 0
    rail_count = 0
    layer_count = 0
    for item in hierarchy_rows:
        logical_module = item["module_name"]
        openyield_candidate = OPENYIELD_CANDIDATE_MAP.get(logical_module, "")
        openyield_path = openyield_module_gds_dir / openyield_candidate if openyield_candidate else None
        openyield_gds = openyield_path / f"{openyield_candidate}.gds" if openyield_path else None
        openyield_found = bool(openyield_gds and openyield_gds.exists())
        if openyield_found and openyield_candidate:
            openyield_control_gds.add(openyield_candidate)
        metadata = _load_candidate_metadata(openyield_path) if openyield_found and openyield_path else {}
        bbox_available = bool(metadata.get("bbox"))
        pin_available = bool(metadata.get("pins"))
        rail_available = bool(metadata.get("rail"))
        layer_available = any(pin.get("layer") for pin in metadata.get("pins", []))
        bbox_count += int(bbox_available)
        pin_count += int(pin_available)
        rail_count += int(rail_available)
        layer_count += int(layer_available)

        layoutgen_cell = _layoutgen_cell_name(logical_module, item["source_class"])
        layoutgen_path = layoutgen_root / f"{layoutgen_cell}.gds" if layoutgen_cell else None
        layoutgen_found = bool(layoutgen_path and layoutgen_path.exists())
        if layoutgen_found and layoutgen_cell:
            layoutgen_control_cells.add(layoutgen_cell)

        openram_ref = OPENRAM_REFERENCE_MAP.get(logical_module) or gap_by_module.get(logical_module, {}).get("openram_cell_or_region", "")
        existing_openram_reference_found = bool(openram_ref)

        strategy, readiness, blocking_reason, recommended_action = _strategy_and_readiness(
            logical_module=logical_module,
            source_class=item["source_class"],
            openyield_found=openyield_found,
            layoutgen_found=layoutgen_found,
            existing_openram_reference_found=existing_openram_reference_found,
        )
        if readiness == "READY_FOR_QUALIFICATION":
            ready += 1
        elif readiness == "PARTIAL_METADATA_ONLY":
            partial += 1
        elif readiness == "REFERENCE_ONLY":
            reference_only += 1
        elif readiness in {"MISSING", "UNKNOWN"}:
            missing += 1
        if strategy == "PARAMETERIZED_TRANSISTOR_LAYOUT_REQUIRED":
            transistor_required += 1

        rows.append(
            {
                "logical_module": logical_module,
                "source_file": item["source_file"],
                "source_class": item["source_class"],
                "parent_path": item["parent_module"],
                "logical_function": _logical_function(logical_module),
                "pin_names": item["pin_order"],
                "pin_count": len(item["pin_order"].split("|")) if item["pin_order"] else 0,
                "instance_count_or_formula": item["instance_count_formula"],
                "parameter_dependencies": item["parameter_dependencies"],
                "operation_dependencies": item["operation_dependencies"],
                "existing_openyield_gds_found": openyield_found,
                "existing_openyield_gds_path": str(openyield_gds) if openyield_gds else "",
                "existing_layoutgen_cell_found": layoutgen_found,
                "existing_layoutgen_cell_name": layoutgen_cell,
                "existing_openram_reference_found": existing_openram_reference_found,
                "existing_openram_cell_or_region": openram_ref,
                "bbox_metadata_available": bbox_available,
                "pin_geometry_available": pin_available,
                "power_rail_metadata_available": rail_available,
                "layer_metadata_available": layer_available,
                "physical_strategy": strategy,
                "physical_readiness": readiness,
                "blocking_reason": blocking_reason,
                "recommended_action": recommended_action,
                "requires_human_review": False,
            }
        )

    total = max(1, len(rows))
    return {
        "rows": rows,
        "physical_module_total_count": len(rows),
        "physical_ready_for_qualification_count": ready,
        "physical_partial_count": partial,
        "physical_reference_only_count": reference_only,
        "physical_missing_count": missing,
        "parameterized_transistor_layout_required_count": transistor_required,
        "existing_openyield_control_primitive_gds_count": len(openyield_control_gds),
        "existing_layoutgen_control_cell_count": len(layoutgen_control_cells),
        "bbox_metadata_coverage": f"{bbox_count}/{total}",
        "pin_geometry_coverage": f"{pin_count}/{total}",
        "power_rail_metadata_coverage": f"{rail_count}/{total}",
        "layer_metadata_coverage": f"{layer_count}/{total}",
        "openram_control_reference_region_found": any(bool(row["existing_openram_reference_found"]) for row in rows),
    }


def _load_candidate_metadata(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    bbox = _load_json(path / "bbox.json")
    pins_obj = _load_json(path / "pins.json")
    rail = _load_json(path / "rail_report.json")
    pins = pins_obj.get("pins", []) if isinstance(pins_obj, dict) else pins_obj or []
    return {"bbox": bbox, "pins": pins, "rail": rail}


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _layoutgen_cell_name(logical_module: str, source_class: str) -> str:
    return LAYOUTGEN_CELL_MAP.get(logical_module) or LAYOUTGEN_CELL_MAP.get(source_class) or ""


def _logical_function(module_name: str) -> str:
    mapping = {
        "TIME": "top-level SRAM control timing generator",
        "ADDR_DFF": "address register bank",
        "DATA_DFF": "write-data register bank",
        "DFF_BUF": "cs/web capture register with buffered outputs",
        "DFF": "transmission-gate flip-flop primitive",
        "TRANSMISSION_GATE": "latch pass device primitive",
        "delay_chain": "replica bitline delay chain",
        "wen_delay_chain": "special write-enable delay extension",
        "pdrive": "clock buffer chain",
        "pdrive2_for_pre": "precharge buffer chain",
        "wl_pdrive": "wordline enable buffer chain",
        "AND2": "2-input gating primitive",
        "AND3": "3-input enable-generation primitive",
        "PNAND2": "2-input NAND primitive",
        "PNAND3": "3-input NAND primitive",
    }
    return mapping.get(module_name, "source-traced control-logic support block")


def _strategy_and_readiness(
    *,
    logical_module: str,
    source_class: str,
    openyield_found: bool,
    layoutgen_found: bool,
    existing_openram_reference_found: bool,
) -> tuple[str, str, str, str]:
    primitive = source_class in {"TransmissionGate", "dff"} or logical_module in {"TRANSMISSION_GATE", "DFF", "wen_delay_chain"}
    if primitive and not openyield_found and not layoutgen_found:
        return (
            "PARAMETERIZED_TRANSISTOR_LAYOUT_REQUIRED",
            "MISSING",
            "No standalone OpenYield candidate GDS or reusable layoutgen hardcell exists for this transistor-level primitive.",
            "Plan a parameterized transistor-level primitive generator or a legal wrapper strategy before physical implementation.",
        )
    if openyield_found and layoutgen_found:
        return (
            "HIERARCHICAL_PRIMITIVE_COMPOSITION",
            "READY_FOR_QUALIFICATION",
            "Candidate GDS exists but still requires bbox/pin/rail qualification against the locked topology.",
            "Run physical-library qualification on the existing candidate and base hardcells before any assembly claim.",
        )
    if openyield_found and not layoutgen_found:
        return (
            "HIERARCHICAL_PRIMITIVE_COMPOSITION",
            "PARTIAL_METADATA_ONLY",
            "Only an OpenYield candidate composite is present; it is not yet proven as a final reusable implementation.",
            "Audit candidate GDS metadata and confirm whether a primitive-backed implementation can be qualified or must be regenerated.",
        )
    if layoutgen_found and not openyield_found:
        return (
            "LAYOUTGEN_REFERENCE_ONLY",
            "REFERENCE_ONLY",
            "A layoutgen hardcell exists, but there is no OpenYield-specific candidate composite proving direct reuse for this control role.",
            "Use the layoutgen cell as a primitive reference only and bind it through an OpenYield-specific qualification stage.",
        )
    if existing_openram_reference_found:
        return (
            "OPENRAM_REFERENCE_ONLY",
            "REFERENCE_ONLY",
            "Only an OpenRAM reference region is available; it cannot be promoted into a final OpenYield control implementation.",
            "Use the OpenRAM region only for floorplan and interface reference, not for direct reuse.",
        )
    return (
        "UNKNOWN",
        "UNKNOWN",
        "No trustworthy physical implementation source was found.",
        "Keep this block in the missing/unknown set until a primitive or candidate source is qualified.",
    )
