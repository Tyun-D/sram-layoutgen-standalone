from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

REPO_ROOT = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.top_level_validation import (  # noqa: E402
    L3_REQUIRED_MODULES,
    normalize_top_gds_module_reference,
)

OUT_DIR = REPO_ROOT / "outputs/openyield_validation/current_supported_config"
REPORT_JSON = REPO_ROOT / "docs/openyield_L5_validation_report.json"
REPORT_MD = REPO_ROOT / "docs/openyield_L5_validation_report.md"
MATRIX_CSV = REPO_ROOT / "docs/mapping/openyield_L5_validation_matrix.csv"
MATRIX_MD = REPO_ROOT / "docs/mapping/openyield_L5_validation_matrix.md"
TOP_GDS_SANITY_JSON = OUT_DIR / "top_gds_sanity_report.json"
MODULE_COMPLETENESS_JSON = OUT_DIR / "module_completeness_report.json"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_L5_reports_exist() -> None:
    required = [
        REPORT_JSON,
        REPORT_MD,
        MATRIX_CSV,
        MATRIX_MD,
        REPO_ROOT / "docs/evidence/L5_validation_gap_summary.md",
        OUT_DIR / "top_gds_sanity_report.json",
        OUT_DIR / "module_completeness_report.json",
        OUT_DIR / "placement_consistency_report.json",
        OUT_DIR / "pin_accessibility_audit.json",
        OUT_DIR / "rail_stitch_audit.json",
        OUT_DIR / "routing_handoff_audit.json",
        OUT_DIR / "candidate_geometry_risk_report.json",
        OUT_DIR / "drc_smoke_report.json",
        OUT_DIR / "lvs_feasibility_report.json",
        OUT_DIR / "timing_metadata_consistency_report.json",
        OUT_DIR / "validation_summary.json",
        OUT_DIR / "validation_summary.md",
    ]
    missing = [str(path) for path in required if not path.exists()]
    assert not missing, f"Missing L5 outputs: {missing}"


def test_L5_summary_contains_required_gates() -> None:
    report = _read_json(REPORT_JSON)
    required_keys = [
        "L5_validation_available",
        "top_gds_sanity_status",
        "module_completeness_status",
        "placement_consistency_status",
        "pin_accessibility_status",
        "rail_stitch_audit_status",
        "routing_handoff_audit_status",
        "candidate_geometry_risk_status",
        "drc_smoke_status",
        "lvs_feasibility_status",
        "timing_metadata_consistency_status",
        "remaining_L5_basic_validation_blockers_count",
        "can_claim_L5_basic_validation_passed_now",
        "can_claim_validated_full_openyield_gds_now",
        "can_claim_drc_clean_now",
        "can_claim_lvs_clean_now",
        "can_claim_timing_closure_now",
        "recommended_next_validation_tasks",
    ]
    for key in required_keys:
        assert key in report, f"Missing report key: {key}"
    assert report["top_gds_sanity_status"] == "PASSED"
    assert report["remaining_L5_basic_validation_blockers_count"] == 0
    assert report["can_claim_L5_basic_validation_passed_now"] is True
    assert report["can_claim_validated_full_openyield_gds_now"] is False
    assert report["can_claim_drc_clean_now"] is False
    assert report["can_claim_lvs_clean_now"] is False
    assert report["can_claim_timing_closure_now"] is False


def test_L5_matrix_has_all_checks() -> None:
    rows = _read_csv(MATRIX_CSV)
    names = {row["check_name"] for row in rows}
    assert names == {
        "top_gds_sanity",
        "module_completeness",
        "placement_consistency",
        "pin_accessibility",
        "rail_stitch_audit",
        "routing_handoff_audit",
        "candidate_geometry_risk",
        "drc_smoke",
        "lvs_feasibility",
        "timing_metadata_consistency",
    }


def test_top_gds_sanity_report_passed_with_real_parser() -> None:
    report = _read_json(TOP_GDS_SANITY_JSON)
    assert report["top_gds_sanity_status"] == "PASSED"
    assert report["gds_exists"] is True
    assert report["gds_size_bytes"] > 0
    assert report["top_cell_name"] == "openyield_top_level_candidate"
    assert report["top_instance_count"] == 20
    assert any(attempt["success"] for attempt in report["parser_attempts"])


def test_module_reference_normalization_rules() -> None:
    required = set(L3_REQUIRED_MODULES)
    assert normalize_top_gds_module_reference("bitcell_array__bitcell_array", required) == "bitcell_array"
    assert normalize_top_gds_module_reference("CONTROL_LOGIC__CONTROL_LOGIC", required) == "CONTROL_LOGIC"
    assert normalize_top_gds_module_reference("bitcell_array__leaf_cell", required) == "bitcell_array"
    assert normalize_top_gds_module_reference("not_a_required_module__leaf_cell", required) is None


def test_module_completeness_report_normalizes_prefixed_top_refs() -> None:
    report = _read_json(MODULE_COMPLETENESS_JSON)
    required = set(L3_REQUIRED_MODULES)
    assert report["module_completeness_status"] == "PASSED"
    assert report["required_modules_missing_from_top_gds_references"] == []
    assert set(report["required_modules_present_in_top_gds_references"]) == required
    assert "bitcell_array__bitcell_array" in report["module_references_seen_raw"]
    assert "CONTROL_LOGIC__CONTROL_LOGIC" in report["module_references_seen_raw"]
    assert "bitcell_array" in report["module_references_normalized"]
    assert "CONTROL_LOGIC" in report["module_references_normalized"]
    assert set(report["module_references_normalized"]) == required


def main() -> None:
    test_L5_reports_exist()
    test_L5_summary_contains_required_gates()
    test_L5_matrix_has_all_checks()
    test_top_gds_sanity_report_passed_with_real_parser()
    test_module_reference_normalization_rules()
    test_module_completeness_report_normalizes_prefixed_top_refs()
    print("OpenYield L5 validation tests passed.")


if __name__ == "__main__":
    main()
