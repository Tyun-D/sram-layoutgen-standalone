from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.gds_reference_closure_verifier import verify_gds_reference_closure


def main() -> int:
    original_atlas = REPO_ROOT / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/M12C3A4_label_cleanup_review_atlas.gds"
    repaired_atlas = REPO_ROOT / "outputs/M12C3A4R_review_atlas_state_normalization/current_supported_config/M12C3A4R_label_cleanup_review_atlas.gds"

    original = verify_gds_reference_closure(original_atlas, "M12C3A4_LABEL_CLEANUP_REVIEW_ATLAS")
    assert original["structure_count"] == 1
    assert original["reference_count"] == 20
    assert original["missing_reference_target_count"] == 20
    assert original["reference_closure_passed"] is False

    repaired = verify_gds_reference_closure(repaired_atlas, "M12C3A4R_LABEL_CLEANUP_REVIEW_ATLAS")
    assert repaired["duplicate_structure_name_count"] == 0
    assert repaired["missing_sref_target_count"] == 0
    assert repaired["missing_aref_target_count"] == 0
    assert repaired["missing_reference_target_count"] == 0
    assert repaired["reference_closure_passed"] is True
    assert repaired["structure_count"] > 1
    assert repaired["top_level_cell_count"] == 1
    assert repaired["top_level_cell_name"] == "M12C3A4R_LABEL_CLEANUP_REVIEW_ATLAS"
    assert len(repaired["before_after_root_mapping"]) == 10

    report = json.loads((REPO_ROOT / "docs/M12C3A4R_review_atlas_state_normalization_report.json").read_text())
    assert report["review_pair_count"] == 10
    assert report["review_before_instance_count"] == 10
    assert report["review_after_instance_count"] == 10
    assert report["all_before_hierarchies_resolved"] is True
    assert report["all_after_hierarchies_resolved"] is True

    print("M12C3A4R_review_atlas_reference_closure_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
