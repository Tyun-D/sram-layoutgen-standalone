from __future__ import annotations

import csv
import json
from pathlib import Path


def main() -> None:
    root = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
    out_dir = root / "outputs/openyield_layout_intent/current_supported_config"
    report_json = root / "docs/openyield_R1_layout_intent_report.json"
    report_md = root / "docs/openyield_R1_layout_intent_report.md"
    matrix_csv = root / "docs/mapping/openyield_R1_layout_intent_matrix.csv"
    matrix_md = root / "docs/mapping/openyield_R1_layout_intent_matrix.md"

    required = [
        report_json,
        report_md,
        matrix_csv,
        matrix_md,
        root / "docs/evidence/R1_layout_intent_gap_summary.md",
        out_dir / "openyield_sram_layout_intent.json",
        out_dir / "openyield_array_topology_contract.json",
        out_dir / "openyield_row_path_intent.json",
        out_dir / "openyield_column_path_intent.json",
        out_dir / "openyield_control_path_intent.json",
        out_dir / "openyield_power_intent.json",
        out_dir / "openyield_pin_intent.json",
        out_dir / "openyield_net_to_layout_role_map.csv",
        out_dir / "openyield_module_to_physical_role_map.csv",
    ]
    for path in required:
        assert path.exists(), f"missing required artifact: {path}"

    report = json.loads(report_json.read_text(encoding="utf-8"))
    assert report["R1_layout_intent_available"] is True
    assert report["canonical_parameters_available"] is True
    assert report["array_topology_contract_available"] is True
    assert report["row_path_intent_available"] is True
    assert report["column_path_intent_available"] is True
    assert report["control_path_intent_available"] is True
    assert report["power_intent_available"] is True
    assert report["pin_intent_available"] is True
    assert report["net_to_layout_role_map_available"] is True
    assert report["module_to_physical_role_map_available"] is True
    assert report["layout_intent_matrix_available"] is True
    assert report["unknown_module_role_count"] == 0
    assert report["remaining_R1_blockers_count"] == 0
    assert report["can_claim_R1_layout_intent_defined_now"] is True
    assert report["can_enter_R2_generator_architecture_design"] is True
    assert report["can_claim_structure_complete_sram_gds_now"] is False
    assert report["can_claim_drc_clean_now"] is False
    assert report["can_claim_lvs_clean_now"] is False
    assert report["can_claim_timing_closure_now"] is False
    assert report["can_claim_signoff_ready_now"] is False

    with (out_dir / "openyield_module_to_physical_role_map.csv").open(newline="", encoding="utf-8") as handle:
        module_rows = list(csv.DictReader(handle))
    l3_rows = [row for row in module_rows if row["module_name"]]
    assert len(l3_rows) == 20, f"expected 20 L3 target modules, got {len(l3_rows)}"
    assert all(row["physical_role"] != "UNKNOWN" for row in l3_rows)

    with (out_dir / "openyield_net_to_layout_role_map.csv").open(newline="", encoding="utf-8") as handle:
        net_rows = list(csv.DictReader(handle))
    assert len(net_rows) == report["net_layout_role_count"]

    layout_intent = json.loads((out_dir / "openyield_sram_layout_intent.json").read_text(encoding="utf-8"))
    params = layout_intent["canonical_parameters"]["parameters"]
    assert len(params) == report["canonical_parameter_count"]
    assert any(item["parameter_name"] == "supported_scope" for item in params)

    print("OpenYield R1 layout intent tests passed.")


if __name__ == "__main__":
    main()
