from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.signoff import count_klayout_items


def main() -> int:
    report = json.loads((REPO_ROOT / "docs/M12C3A4R_review_atlas_state_normalization_report.json").read_text())
    assert report["reusable_cell_count"] == 10
    assert report["reusable_cell_changed_count"] == 0
    assert report["reusable_clean_aggregate_changed"] is False
    assert report["reusable_annotated_aggregate_changed"] is False
    assert report["reusable_outputs_immutable"] is True
    assert report["existing_drc_report_count"] == 10
    assert report["existing_drc_marker_count"] == 0
    assert report["drc_rerun_required"] is False

    matrix_path = REPO_ROOT / "docs/mapping/M12C3A4R_reusable_output_immutability_matrix.csv"
    with matrix_path.open("r", encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    cell_rows = [row for row in rows if row["artifact"].endswith("_L50") or row["artifact"].startswith("TRANSMISSION_GATE_")]
    assert len(cell_rows) == 10
    assert all(row["changed"] == "False" for row in rows)

    drc_root = REPO_ROOT / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/drc"
    lyrdb_paths = sorted(drc_root.glob("*.lyrdb"))
    assert len(lyrdb_paths) == 10
    assert sum(count_klayout_items(path) for path in lyrdb_paths) == 0

    print("M12C3A4R_reusable_outputs_unchanged_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
