from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    report = json.loads((repo_root / "docs/project_asset_reclassification_report.json").read_text(encoding="utf-8"))

    assert (repo_root / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md").exists()
    assert (repo_root / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").exists()
    assert (repo_root / "docs/project_result_downgrade_statement.md").exists()
    assert (repo_root / "docs/mapping/reusable_artifact_inventory.csv").exists()
    assert (repo_root / "docs/mapping/deprecated_artifact_inventory.csv").exists()
    assert (repo_root / "docs/mapping/first_round_openyield_module_gds_inventory.csv").exists()
    assert (repo_root / "docs/mapping/layoutgen_generator_code_inventory.csv").exists()
    assert (repo_root / "docs/mapping/next_phase_dependency_matrix.csv").exists()
    assert (repo_root / "outputs/project_status_reset_review/current_supported_config/review_gds_manifest.json").exists()

    assert report["S0_project_status_reset_available"] is True
    assert report["project_status_md_available"] is True
    assert report["project_status_json_available"] is True
    assert report["previous_result_downgraded"] is True
    assert report["access_view_gds_reclassified"] is True
    assert report["layoutgen_based_route_defined"] is True
    assert report["must_read_status_file_before_every_task"] is True
    assert report["must_update_status_file_after_every_task"] is True
    assert report["human_klayout_review_required_every_stage"] is True
    assert report["can_enter_next_stage_without_human_review"] is False
    assert report["remaining_S0_blockers_count"] == 0
    assert report["can_claim_S0_project_status_reset_done"] is True
    assert report["can_enter_L0_after_human_review"] is True
    assert report["reusable_artifact_count"] > 0
    assert report["deprecated_artifact_count"] > 0
    assert report["first_round_openyield_module_gds_count"] == 20
    assert report["layoutgen_generator_code_inventory_count"] > 0

    status = json.loads((repo_root / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] == "S0"
    assert status["next_stage"] == "L0"
    assert status["must_read_this_file_before_every_task"] is True
    assert status["must_update_this_file_after_every_task"] is True
    assert status["human_klayout_review_required_every_stage"] is True
    assert status["can_enter_next_stage_without_human_review"] is False

    manifest = json.loads((repo_root / "outputs/project_status_reset_review/current_supported_config/review_gds_manifest.json").read_text(encoding="utf-8"))
    assert manifest["human_klayout_review_required"] is True
    assert manifest["can_enter_L0_before_human_review"] is False
    assert len(manifest["review_gds"]) >= 2
    print("S0 project status reset tests passed.")


if __name__ == "__main__":
    main()
