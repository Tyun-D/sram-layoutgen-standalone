from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


VALID_READINESS = {
    "LEAF_GDS_READY",
    "HARDMACRO_GDS_READY",
    "PYTHON_GENERATOR_READY",
    "GDS_EXISTS_NEEDS_PIN_RAIL_EXTRACTION",
    "GDS_EXISTS_NEEDS_ABUTMENT_RULE",
    "SPICE_ONLY_NEEDS_LAYOUT_GENERATOR",
    "SOURCE_ONLY_NEEDS_PHYSICAL_GENERATOR",
    "METADATA_ONLY_NEEDS_PHYSICAL_SOURCE",
    "FALLBACK_ONLY",
    "MISSING_PHYSICAL_SOURCE",
    "BLOCKED",
}

REQUIRED_MODULES = {
    "SRAM_TOP",
    "BANK",
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
    "routing_semantics",
    "power_semantics",
    "timing_semantics",
}


def main() -> int:
    required_paths = [
        REPO_ROOT / "docs/mapping/openyield_leaf_physical_readiness_matrix.csv",
        REPO_ROOT / "docs/mapping/openyield_leaf_physical_readiness_matrix.md",
        REPO_ROOT / "docs/mapping/openyield_module_to_primitive_dependency_matrix.csv",
        REPO_ROOT / "docs/mapping/openyield_module_to_primitive_dependency_matrix.md",
        REPO_ROOT / "docs/openyield_physical_primitive_closure_report.json",
        REPO_ROOT / "docs/openyield_physical_primitive_closure_report.md",
        REPO_ROOT / "technology/freepdk45/openyield_leaf_physical_library.json",
    ]
    for path in required_paths:
        assert path.exists(), f"missing artifact: {path}"

    primitive_rows = list(csv.DictReader((REPO_ROOT / "docs/mapping/openyield_leaf_physical_readiness_matrix.csv").open(encoding="utf-8")))
    module_rows = list(csv.DictReader((REPO_ROOT / "docs/mapping/openyield_module_to_primitive_dependency_matrix.csv").open(encoding="utf-8")))
    report = json.loads((REPO_ROOT / "docs/openyield_physical_primitive_closure_report.json").read_text(encoding="utf-8"))
    library = json.loads((REPO_ROOT / "technology/freepdk45/openyield_leaf_physical_library.json").read_text(encoding="utf-8"))

    assert len(primitive_rows) > 0
    assert report["primitive_rows_count"] == len(primitive_rows)
    assert report["module_dependency_rows_count"] == len(module_rows)
    assert library["primitive_count"] == len(primitive_rows)

    module_map = {row["module"]: row for row in module_rows}
    assert REQUIRED_MODULES.issubset(module_map)
    for name in REQUIRED_MODULES:
        assert module_map[name]["required_primitives"], f"module missing primitive dependencies: {name}"

    for row in primitive_rows:
        assert row["readiness_level"] in VALID_READINESS, row

    for key in [
        "physical_primitive_closure_available",
        "leaf_physical_readiness_matrix_available",
        "module_to_primitive_dependency_matrix_available",
        "leaf_physical_library_available",
        "primitive_rows_count",
        "module_dependency_rows_count",
        "can_claim_L1_physical_primitives_closed_now",
        "can_enter_L2_placement_abutment_rule_closure",
        "can_enter_L3_module_gds_generation",
        "can_claim_full_openyield_gds_now",
        "can_claim_drc_clean_now",
        "can_claim_lvs_clean_now",
        "can_claim_timing_closure_now",
    ]:
        assert key in report, key

    assert report["can_claim_full_openyield_gds_now"] is False
    assert report["can_claim_drc_clean_now"] is False
    assert report["can_claim_lvs_clean_now"] is False
    assert report["can_claim_timing_closure_now"] is False
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
