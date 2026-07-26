from __future__ import annotations

import json
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    report = json.loads((repo_root / "docs/M1_layoutgen_openyield_binding_report.json").read_text(encoding="utf-8"))
    status = json.loads((repo_root / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))

    assert report["M1_layoutgen_openyield_binding_available"] is True
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["layoutgen_generator_inventory_available"] is True
    assert report["first_round_module_physical_audit_available"] is True
    assert report["openyield_to_layoutgen_binding_available"] is True
    assert report["openyield_net_to_layoutgen_pin_binding_available"] is True
    assert report["physical_cell_binding_review_gds_available"] is True
    assert report["review_gds_manifest_available"] is True
    assert report["first_round_openyield_module_audited_count"] == 20
    assert report["critical_modules_with_binding_or_gap"] is True
    assert report["human_klayout_review_required"] is True
    assert report["can_enter_M2_before_human_review"] is False
    assert report["remaining_M1_blockers_count"] == 0

    assert (repo_root / "docs/mapping/M1_layoutgen_generator_inventory.csv").exists()
    assert (repo_root / "docs/mapping/M1_first_round_module_physical_audit.csv").exists()
    assert (repo_root / "docs/mapping/M1_openyield_to_layoutgen_binding.csv").exists()
    assert (repo_root / "docs/mapping/M1_openyield_net_to_layoutgen_pin_binding.csv").exists()
    assert (repo_root / "outputs/M1_layoutgen_binding_review/current_supported_config/physical_cell_binding_review.gds").exists()
    assert (repo_root / "outputs/M1_layoutgen_binding_review/current_supported_config/review_gds_manifest.json").exists()

    assert status["current_stage"] == "M1"
    assert status["next_stage"] == "M2"
    assert status["must_read_this_file_before_every_task"] is True
    assert status["must_update_this_file_after_every_task"] is True
    assert status["human_klayout_review_required_every_stage"] is True
    assert status["can_enter_next_stage_without_human_review"] is False

    print("M1 layoutgen OpenYield binding tests passed.")


if __name__ == "__main__":
    main()
