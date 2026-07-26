from __future__ import annotations

import csv
import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    required = [
        REPO_ROOT / "technology/freepdk45/openyield_primitive_composition_library.json",
        REPO_ROOT / "docs/mapping/openyield_primitive_composition_contracts.csv",
        REPO_ROOT / "docs/mapping/openyield_primitive_composition_contracts.md",
        REPO_ROOT / "docs/openyield_physical_primitive_gap_closure_report.json",
        REPO_ROOT / "docs/openyield_physical_primitive_gap_closure_report.md",
    ]
    for path in required:
        assert path.exists(), f"missing artifact: {path}"

    primitive_rows = list(csv.DictReader((REPO_ROOT / "docs/mapping/openyield_leaf_physical_readiness_matrix.csv").open(encoding="utf-8")))
    report = json.loads((REPO_ROOT / "docs/openyield_physical_primitive_gap_closure_report.json").read_text(encoding="utf-8"))
    row_by_name = {row["primitive_name"]: row for row in primitive_rows}

    assert row_by_name["nand3"]["local_physical_source_type"] != "SOURCE_ONLY"
    assert row_by_name["nand3"]["readiness_level"] == "PYTHON_GENERATOR_READY"
    assert row_by_name["and3"]["local_physical_source_type"] != "SOURCE_ONLY"
    assert row_by_name["and3"]["readiness_level"] == "PYTHON_GENERATOR_READY"

    for name in ["enable_path_leaf_gate", "gated_clock_leaf_gate", "control_logic_leaf_gate"]:
        assert row_by_name[name]["local_physical_source_type"] != "CANDIDATE_SPICE_ONLY"
        assert row_by_name[name]["readiness_level"] == "PYTHON_GENERATOR_READY"

    for name in ["and2", "buffer"]:
        assert row_by_name[name]["local_physical_source_type"] != "FALLBACK_ONLY"
        assert row_by_name[name]["readiness_level"] == "PYTHON_GENERATOR_READY"

    precharge = row_by_name["precharge_cell"]
    assert precharge["local_physical_source_type"] == "HARDMACRO_GDS"
    assert precharge["bbox_known"] == "True"
    assert precharge["readiness_level"] in {"HARDMACRO_GDS_READY", "GDS_EXISTS_NEEDS_ABUTMENT_RULE"}
    assert "pin_geometry_requires_L2_extraction" in precharge["blocking_gap"] or precharge["pin_labels_known"] == "True"

    for name in ["nor3", "or2", "or3"]:
        assert "not_required_for_current_L0_supported_scope" in row_by_name[name]["blocking_gap"]
        assert name not in report["remaining_L1_blockers"]

    assert report["remaining_L1_blockers_count"] == 0
    assert report["can_claim_L1_physical_primitives_closed_now"] is True
    assert report["can_enter_L2_placement_abutment_rule_closure"] is True
    assert report["can_enter_L3_module_gds_generation"] is False
    assert report["can_claim_full_openyield_gds_now"] is False
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
