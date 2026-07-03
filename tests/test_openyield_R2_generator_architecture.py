from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    root = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
    out_dir = root / "outputs/openyield_generator_architecture/current_supported_config"
    report_json = root / "docs/openyield_R2_generator_architecture_report.json"
    report_md = root / "docs/openyield_R2_generator_architecture_report.md"
    matrix_csv = root / "docs/mapping/openyield_R2_generator_architecture_matrix.csv"
    matrix_md = root / "docs/mapping/openyield_R2_generator_architecture_matrix.md"

    required = [
        report_json,
        report_md,
        matrix_csv,
        matrix_md,
        root / "docs/evidence/R2_generator_architecture_gap_summary.md",
        out_dir / "openyield_sram_generator_architecture.json",
        out_dir / "openyield_sram_generator_architecture.md",
        out_dir / "openyield_generator_dataflow.json",
        out_dir / "openyield_generator_dataflow.md",
        out_dir / "openyield_generator_module_interfaces.json",
        out_dir / "openyield_generator_module_interfaces.md",
        out_dir / "openyield_generator_component_plan.json",
        out_dir / "openyield_generator_component_plan.md",
        out_dir / "openyield_r3_minimum_implementation_plan.json",
        out_dir / "openyield_r3_minimum_implementation_plan.md",
        out_dir / "openyield_r4_routing_power_pin_plan.json",
        out_dir / "openyield_r4_routing_power_pin_plan.md",
        out_dir / "openyield_generator_reuse_decision.json",
        out_dir / "openyield_generator_reuse_decision.md",
    ]
    for path in required:
        assert path.exists(), f"missing required artifact: {path}"

    report = json.loads(report_json.read_text(encoding="utf-8"))
    assert report["R2_generator_architecture_available"] is True
    assert report["generator_dataflow_available"] is True
    assert report["module_interfaces_available"] is True
    assert report["component_plan_available"] is True
    assert report["r3_minimum_implementation_plan_available"] is True
    assert report["r4_routing_power_pin_plan_available"] is True
    assert report["reuse_decision_available"] is True
    assert report["architecture_matrix_available"] is True
    assert report["component_count"] >= 12
    assert report["remaining_R2_blockers_count"] == 0
    assert report["can_claim_R2_generator_architecture_defined_now"] is True
    assert report["can_enter_R3_structure_complete_gds_minimum_implementation"] is True
    assert report["can_claim_structure_complete_sram_gds_now"] is False
    assert report["can_claim_drc_clean_now"] is False
    assert report["can_claim_lvs_clean_now"] is False
    assert report["can_claim_timing_closure_now"] is False
    assert report["can_claim_signoff_ready_now"] is False

    architecture = json.loads((out_dir / "openyield_sram_generator_architecture.json").read_text(encoding="utf-8"))
    components = architecture["components"]
    component_names = {item["component_name"] for item in components}
    required_components = {
        "OpenYieldIntentLoader",
        "CanonicalSramParameterModel",
        "PhysicalModuleRegistry",
        "BitcellArrayPhysicalGenerator",
        "RowPeripheryPhysicalGenerator",
        "ColumnPeripheryPhysicalGenerator",
        "ControlPeripheryPhysicalGenerator",
        "SRAMTopologyFloorplanner",
        "WordlineRouter",
        "BitlineRouter",
        "ControlRouter",
        "PowerPlanner",
        "PinLabelExporter",
        "NetToShapeMapper",
        "InstanceMapper",
        "GDSBackend",
        "ValidationHookManager",
    }
    assert required_components.issubset(component_names)

    print("OpenYield R2 generator architecture tests passed.")


if __name__ == "__main__":
    main()
