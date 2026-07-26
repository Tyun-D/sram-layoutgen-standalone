from __future__ import annotations

import csv
import json
from pathlib import Path
import sys

REPO_ROOT = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUT_DIR = REPO_ROOT / "outputs/openyield_project_closure/current_supported_config"
REPORT_JSON = REPO_ROOT / "docs/openyield_step7_final_repair_planning_report.json"
REPORT_MD = REPO_ROOT / "docs/openyield_step7_final_repair_planning_report.md"
MATRIX_CSV = REPO_ROOT / "docs/mapping/openyield_step7_final_repair_plan_matrix.csv"
MATRIX_MD = REPO_ROOT / "docs/mapping/openyield_step7_final_repair_plan_matrix.md"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_step7_reports_exist() -> None:
    required = [
        REPORT_JSON,
        REPORT_MD,
        MATRIX_CSV,
        MATRIX_MD,
        REPO_ROOT / "docs/evidence/step7_final_repair_planning_gap_summary.md",
        OUT_DIR / "final_repair_plan.json",
        OUT_DIR / "final_repair_plan.md",
        OUT_DIR / "project_v1_capability_statement.json",
        OUT_DIR / "project_v1_capability_statement.md",
        OUT_DIR / "project_v1_limitation_statement.json",
        OUT_DIR / "project_v1_limitation_statement.md",
        OUT_DIR / "future_work_roadmap.json",
        OUT_DIR / "future_work_roadmap.md",
        OUT_DIR / "final_handoff_checklist.json",
        OUT_DIR / "final_handoff_checklist.md",
    ]
    missing = [str(path) for path in required if not path.exists()]
    assert not missing, f"Missing Step 7 outputs: {missing}"


def test_step7_summary_gates() -> None:
    report = _read_json(REPORT_JSON)
    assert report["drc_marker_total_count"] == 24687
    assert report["drc_marker_classification_coverage"] == 1.0
    assert report["top_repair_root_cause"] == "LAYER_MAP_OR_DRC_DECK_INTERPRETATION"
    assert report["can_claim_project_v1_closure_ready"] is True
    assert report["can_enter_step8_final_report_handoff"] is True
    assert report["can_claim_drc_clean_now"] is False
    assert report["can_claim_lvs_clean_now"] is False
    assert report["can_claim_timing_closure_now"] is False
    assert report["can_claim_validated_full_openyield_gds_now"] is False
    assert report["can_claim_signoff_ready_sram_compiler_now"] is False


def test_step7_matrix_and_plan_content() -> None:
    rows = _read_csv(MATRIX_CSV)
    assert rows
    assert rows[0]["root_cause_category"] == "LAYER_MAP_OR_DRC_DECK_INTERPRETATION"
    assert rows[0]["priority"] == "P1"
    plan = _read_json(OUT_DIR / "final_repair_plan.json")
    items = plan["repair_plan_items"]
    assert items[0]["root_cause_category"] == "LAYER_MAP_OR_DRC_DECK_INTERPRETATION"
    assert items[0]["marker_count"] == 12012


def main() -> None:
    test_step7_reports_exist()
    test_step7_summary_gates()
    test_step7_matrix_and_plan_content()
    print("OpenYield Step 7 final repair planning tests passed.")


if __name__ == "__main__":
    main()
