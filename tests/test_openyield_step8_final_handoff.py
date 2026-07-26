from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

OUT_DIR = REPO_ROOT / "outputs/openyield_final_handoff/current_supported_config"
REPORT_JSON = REPO_ROOT / "docs/openyield_step8_final_handoff_report.json"
REPORT_MD = REPO_ROOT / "docs/openyield_step8_final_handoff_report.md"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_step8_reports_exist() -> None:
    required = [
        REPORT_JSON,
        REPORT_MD,
        REPO_ROOT / "docs/evidence/step8_final_handoff_summary.md",
        OUT_DIR / "final_project_summary.json",
        OUT_DIR / "final_project_summary.md",
        OUT_DIR / "final_technical_report.md",
        OUT_DIR / "final_evidence_index.json",
        OUT_DIR / "final_evidence_index.md",
        OUT_DIR / "final_capability_boundary.md",
        OUT_DIR / "final_limitations_and_risks.md",
        OUT_DIR / "final_future_work_plan.md",
        OUT_DIR / "final_delivery_checklist.md",
        OUT_DIR / "final_one_page_summary.md",
        REPO_ROOT / "outputs/openyield_top_level_assembly/current_supported_config/openyield_top_level_candidate.gds",
    ]
    missing = [str(path) for path in required if not path.exists()]
    assert not missing, f"Missing Step 8 outputs: {missing}"


def test_step8_summary_gates() -> None:
    report = _read_json(REPORT_JSON)
    assert report["Step8_final_handoff_available"] is True
    assert report["final_technical_report_available"] is True
    assert report["final_one_page_summary_available"] is True
    assert report["final_evidence_index_available"] is True
    assert report["final_capability_boundary_available"] is True
    assert report["final_limitations_and_risks_available"] is True
    assert report["final_future_work_plan_available"] is True
    assert report["final_delivery_checklist_available"] is True
    assert report["top_level_candidate_gds_exists"] is True
    assert report["can_claim_final_handoff_completed_now"] is True
    assert report["remaining_step8_blockers_count"] == 0
    assert report["can_claim_drc_clean_now"] is False
    assert report["can_claim_lvs_clean_now"] is False
    assert report["can_claim_timing_closure_now"] is False
    assert report["can_claim_validated_full_openyield_gds_now"] is False
    assert report["can_claim_signoff_ready_sram_compiler_now"] is False


def main() -> None:
    test_step8_reports_exist()
    test_step8_summary_gates()
    print("OpenYield Step 8 final handoff tests passed.")


if __name__ == "__main__":
    main()
