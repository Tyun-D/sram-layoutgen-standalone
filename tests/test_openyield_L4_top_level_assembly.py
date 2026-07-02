from __future__ import annotations

import csv
import json
from pathlib import Path


REPO_ROOT = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
OUT_DIR = REPO_ROOT / "outputs/openyield_top_level_assembly/current_supported_config"
REPORT_JSON = REPO_ROOT / "docs/openyield_L4_top_level_assembly_report.json"
INVENTORY_CSV = REPO_ROOT / "docs/mapping/openyield_top_level_assembly_inventory.csv"
PLACEMENT_JSON = OUT_DIR / "module_placement.json"
PIN_MAP_JSON = OUT_DIR / "top_level_pin_map.json"
RAIL_JSON = OUT_DIR / "top_level_rail_stitch_plan.json"
ROUTING_JSON = OUT_DIR / "top_level_routing_handoff.json"
MANIFEST_JSON = OUT_DIR / "top_level_generator_manifest.json"
GDS_PATH = OUT_DIR / "openyield_top_level_candidate.gds"
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


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_L4_outputs_exist() -> None:
    required = [
        GDS_PATH,
        OUT_DIR / "top_level_config.json",
        OUT_DIR / "top_level_floorplan.json",
        PLACEMENT_JSON,
        PIN_MAP_JSON,
        RAIL_JSON,
        ROUTING_JSON,
        OUT_DIR / "top_level_generation_report.md",
        OUT_DIR / "top_level_generation_report.json",
        MANIFEST_JSON,
        REPO_ROOT / "docs/mapping/openyield_top_level_assembly_inventory.md",
        REPORT_JSON,
        REPO_ROOT / "docs/openyield_L4_top_level_assembly_report.md",
        REPO_ROOT / "docs/evidence/L4_top_level_assembly_gap_summary.md",
        REPO_ROOT / "outputs/openyield_top_level_assembly/configs/current_supported_config.json",
    ]
    missing = [str(path) for path in required if not path.exists()]
    assert not missing, f"Missing L4 outputs: {missing}"
    assert GDS_PATH.stat().st_size > 0


def test_top_level_gds_report_says_parsed_sanity_passed() -> None:
    report = _read_json(REPORT_JSON)
    assert report["top_level_candidate_gds_generated"] is True
    assert report["top_gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["top_gds_size_bytes"] > 0
    assert report["top_cell_name"]
    assert report["top_bbox"]


def test_all_required_modules_appear_in_module_placement() -> None:
    placement = _read_json(PLACEMENT_JSON)
    present = {item["module_name"] for item in placement["instances"]}
    assert present == set(L3_REQUIRED_MODULES)


def test_all_required_modules_are_instantiated_or_explicitly_not_required() -> None:
    inventory = {row["object"]: row for row in _read_csv(INVENTORY_CSV)}
    for module in L3_REQUIRED_MODULES:
        row = inventory[module]
        assert row["instantiated_in_top_gds"] == "True"
        assert row["assembly_status"] in {
            "L4_TOP_LEVEL_INSTANTIATED",
            "L4_TOP_LEVEL_INSTANTIATED_WITH_CANDIDATE_GEOMETRY",
            "L4_TOP_LEVEL_INSTANTIATED_WITH_CONTRACT_PINS",
        }


def test_required_metadata_files_exist() -> None:
    assert PIN_MAP_JSON.exists()
    assert RAIL_JSON.exists()
    assert ROUTING_JSON.exists()
    assert MANIFEST_JSON.exists()


def test_report_contains_required_gates_and_false_signoff_claims() -> None:
    report = _read_json(REPORT_JSON)
    required_keys = [
        "remaining_L4_blockers_count",
        "required_l3_modules_count",
        "required_l3_modules_instantiated_count",
        "required_l3_modules_missing_from_top",
        "can_claim_L4_top_level_candidate_gds_generated_now",
        "can_enter_L5_validation",
        "can_claim_validated_full_openyield_gds_now",
        "can_claim_drc_clean_now",
        "can_claim_lvs_clean_now",
        "can_claim_timing_closure_now",
    ]
    for key in required_keys:
        assert key in report, f"Missing report key: {key}"
    assert report["can_claim_validated_full_openyield_gds_now"] is False
    assert report["can_claim_drc_clean_now"] is False
    assert report["can_claim_lvs_clean_now"] is False
    assert report["can_claim_timing_closure_now"] is False


def main() -> None:
    test_L4_outputs_exist()
    test_top_level_gds_report_says_parsed_sanity_passed()
    test_all_required_modules_appear_in_module_placement()
    test_all_required_modules_are_instantiated_or_explicitly_not_required()
    test_required_metadata_files_exist()
    test_report_contains_required_gates_and_false_signoff_claims()
    print("OpenYield L4 top-level assembly tests passed.")


if __name__ == "__main__":
    main()
