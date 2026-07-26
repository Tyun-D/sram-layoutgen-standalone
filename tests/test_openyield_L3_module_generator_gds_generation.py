from __future__ import annotations

import csv
import json
from pathlib import Path


REPO_ROOT = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
L3_TARGETS = [
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
DEFERRED = ["SRAM_TOP", "BANK", "routing_semantics", "power_semantics", "timing_semantics"]


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_L3_outputs_exist() -> None:
    required = [
        REPO_ROOT / "docs/mapping/openyield_module_generator_inventory.csv",
        REPO_ROOT / "docs/mapping/openyield_module_generator_inventory.md",
        REPO_ROOT / "docs/mapping/openyield_module_gds_inventory.csv",
        REPO_ROOT / "docs/mapping/openyield_module_gds_inventory.md",
        REPO_ROOT / "docs/openyield_L3_module_generator_gds_generation_report.json",
        REPO_ROOT / "docs/openyield_L3_module_generator_gds_generation_report.md",
        REPO_ROOT / "docs/evidence/L3_module_generator_gds_gap_summary.md",
    ]
    missing = [str(path) for path in required if not path.exists()]
    assert not missing, f"Missing L3 outputs: {missing}"


def test_all_L3_targets_appear_in_both_inventories() -> None:
    generator_rows = {row["module"]: row for row in _load_csv(REPO_ROOT / "docs/mapping/openyield_module_generator_inventory.csv")}
    gds_rows = {row["module"]: row for row in _load_csv(REPO_ROOT / "docs/mapping/openyield_module_gds_inventory.csv")}
    assert set(L3_TARGETS).issubset(generator_rows)
    assert set(L3_TARGETS).issubset(gds_rows)


def test_deferred_objects_are_not_L3_blockers() -> None:
    generator_rows = {row["module"]: row for row in _load_csv(REPO_ROOT / "docs/mapping/openyield_module_generator_inventory.csv")}
    gds_rows = {row["module"]: row for row in _load_csv(REPO_ROOT / "docs/mapping/openyield_module_gds_inventory.csv")}
    for module in DEFERRED:
        assert generator_rows[module]["generator_status"] == "DEFERRED_TO_L4_L5"
        assert gds_rows[module]["generation_status"] == "DEFERRED_TO_L4_L5"


def test_every_generator_ready_row_has_source_file() -> None:
    rows = _load_csv(REPO_ROOT / "docs/mapping/openyield_module_generator_inventory.csv")
    for row in rows:
        if row["generator_status"] in {"GENERATOR_READY", "GENERATOR_READY_FOR_HARDMACRO_WRAPPER", "GENERATOR_READY_FOR_CANDIDATE_GEOMETRY"}:
            assert row["generator_source_file"]


def test_every_generated_module_has_artifacts() -> None:
    rows = _load_csv(REPO_ROOT / "docs/mapping/openyield_module_gds_inventory.csv")
    for row in rows:
        if row["generation_status"] in {"L3_GDS_GENERATED", "L3_GDS_GENERATED_WITH_CONTRACT_PINS", "L3_GDS_GENERATED_CANDIDATE_GEOMETRY"}:
            gds_path = Path(row["gds_path"])
            assert gds_path.exists() and gds_path.stat().st_size > 0
            module_dir = gds_path.parent
            required = [
                module_dir / "pins.json",
                module_dir / "bbox.json",
                module_dir / "rail_report.json",
                module_dir / "generation_report.json",
                module_dir / "generator_manifest.json",
            ]
            missing = [str(path) for path in required if not path.exists()]
            assert not missing, f"Missing generated artifacts for {row['module']}: {missing}"


def test_manifest_references_generator_source() -> None:
    rows = _load_csv(REPO_ROOT / "docs/mapping/openyield_module_gds_inventory.csv")
    for row in rows:
        manifest_path = row["generator_manifest_path"]
        if not manifest_path:
            continue
        manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
        assert manifest["generator_source_file"]
        assert manifest["generator_source_file"].endswith("module_gds_generators.py")


def test_report_contains_required_gates_and_false_signoff_claims() -> None:
    report = json.loads((REPO_ROOT / "docs/openyield_L3_module_generator_gds_generation_report.json").read_text(encoding="utf-8"))
    required_keys = [
        "L3_module_generator_gds_generation_available",
        "module_generator_inventory_available",
        "module_gds_inventory_available",
        "module_generator_rows_count",
        "module_gds_rows_count",
        "remaining_L3_blockers_count",
        "all_L3_target_modules_have_generators",
        "all_L3_target_modules_have_gds",
        "all_L3_target_modules_have_bbox",
        "all_L3_target_modules_have_pin_metadata",
        "all_L3_target_modules_have_rail_metadata",
        "all_L3_target_modules_have_generator_manifest",
        "can_claim_L3_module_generators_closed_now",
        "can_claim_L3_standalone_module_gds_closed_now",
        "can_enter_L4_top_level_assembly",
        "can_claim_full_openyield_gds_now",
        "can_claim_drc_clean_now",
        "can_claim_lvs_clean_now",
        "can_claim_timing_closure_now",
    ]
    for key in required_keys:
        assert key in report, f"Missing report key: {key}"
    assert report["can_claim_full_openyield_gds_now"] is False
    assert report["can_claim_drc_clean_now"] is False
    assert report["can_claim_lvs_clean_now"] is False
    assert report["can_claim_timing_closure_now"] is False
