from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.gds_reference_closure_verifier import verify_gds_reference_closure


def main() -> int:
    atlas = REPO_ROOT / "outputs/M12C3A4R_review_atlas_state_normalization/current_supported_config/M12C3A4R_label_cleanup_review_atlas.gds"
    closure = verify_gds_reference_closure(atlas, "M12C3A4R_LABEL_CLEANUP_REVIEW_ATLAS")
    mapping = closure["before_after_root_mapping"]
    assert len(mapping) == 10
    assert all("before_root_name" in row and "after_root_name" in row for row in mapping.values())

    matrix_path = REPO_ROOT / "docs/mapping/M12C3A4R_review_atlas_before_after_label_matrix.csv"
    with matrix_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 10
    assert all(int(row["after_lowercase_alias_count"]) == 0 for row in rows)
    assert all(int(row["after_internal_gsd_count"]) == 0 for row in rows)
    assert all(int(row["after_duplicate_label_count"]) == 0 for row in rows)
    assert all(row["after_canonical_label_set_exact"] == "True" for row in rows)
    assert any(
        int(row["before_lowercase_alias_count"]) > 0 or int(row["before_internal_gsd_count"]) > 0 or int(row["before_duplicate_label_count"]) > 0 for row in rows
    )

    print("M12C3A4R_review_atlas_before_after_labels_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
