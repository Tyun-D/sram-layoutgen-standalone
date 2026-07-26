from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

REPO_ROOT = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUT_DIR = REPO_ROOT / "outputs/openyield_drc_triage/current_supported_config"
REPORT_JSON = REPO_ROOT / "docs/openyield_L6_drc_marker_triage_report.json"
REPORT_MD = REPO_ROOT / "docs/openyield_L6_drc_marker_triage_report.md"
MATRIX_CSV = REPO_ROOT / "docs/mapping/openyield_L6_drc_marker_triage_matrix.csv"
MATRIX_MD = REPO_ROOT / "docs/mapping/openyield_L6_drc_marker_triage_matrix.md"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_L6_reports_exist() -> None:
    required = [
        REPORT_JSON,
        REPORT_MD,
        MATRIX_CSV,
        MATRIX_MD,
        REPO_ROOT / "docs/evidence/L6_drc_marker_triage_gap_summary.md",
        OUT_DIR / "drc_marker_raw_extract.json",
        OUT_DIR / "drc_marker_rule_summary.json",
        OUT_DIR / "drc_marker_spatial_clusters.json",
        OUT_DIR / "drc_marker_module_mapping.json",
        OUT_DIR / "drc_marker_root_cause_classification.json",
        OUT_DIR / "drc_marker_representative_samples.json",
        OUT_DIR / "drc_marker_fix_priority.json",
        OUT_DIR / "drc_triage_summary.json",
        OUT_DIR / "drc_triage_summary.md",
    ]
    missing = [str(path) for path in required if not path.exists()]
    assert not missing, f"Missing L6 outputs: {missing}"


def test_L6_summary_gates() -> None:
    report = _read_json(REPORT_JSON)
    assert report["drc_marker_total_count"] > 0
    assert report["drc_marker_classification_coverage"] >= 0.90
    assert report["remaining_L6_triage_blockers_count"] == 0
    assert report["can_claim_L6_drc_triage_completed_now"] is True
    assert report["can_enter_L7_drc_repair_planning"] is True
    assert report["can_claim_drc_clean_now"] is False
    assert report["can_claim_lvs_clean_now"] is False
    assert report["can_claim_timing_closure_now"] is False
    assert report["can_claim_validated_full_openyield_gds_now"] is False


def test_L6_matrix_nonempty() -> None:
    rows = _read_csv(MATRIX_CSV)
    assert rows
    categories = {row["root_cause_category"] for row in rows}
    assert any(category in categories for category in ["LAYER_MAP_OR_DRC_DECK_INTERPRETATION", "CANDIDATE_GEOMETRY_INTERNAL", "TOP_LEVEL_ABUTMENT_BOUNDARY"])


def main() -> None:
    test_L6_reports_exist()
    test_L6_summary_gates()
    test_L6_matrix_nonempty()
    print("OpenYield L6 DRC marker triage tests passed.")


if __name__ == "__main__":
    main()
