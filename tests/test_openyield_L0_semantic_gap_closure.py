from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    required_paths = [
        REPO_ROOT / "docs/mapping/openyield_canonical_sram_semantic_contract.md",
        REPO_ROOT / "docs/mapping/openyield_canonical_sram_semantic_contract.json",
        REPO_ROOT / "docs/mapping/openyield_logical_to_openyield_parameter_map.csv",
        REPO_ROOT / "docs/mapping/openyield_logical_to_openyield_parameter_map.md",
        REPO_ROOT / "docs/mapping/openyield_top_bank_semantic_contract.md",
        REPO_ROOT / "docs/mapping/openyield_top_bank_semantic_contract.json",
        REPO_ROOT / "docs/mapping/openyield_time_control_decomposition_contract.md",
        REPO_ROOT / "docs/mapping/openyield_time_control_decomposition_contract.json",
        REPO_ROOT / "docs/mapping/openyield_control_path_semantic_contracts.csv",
        REPO_ROOT / "docs/mapping/openyield_control_path_semantic_contracts.md",
        REPO_ROOT / "docs/mapping/openyield_decoder_wordline_semantic_contract.md",
        REPO_ROOT / "docs/mapping/openyield_decoder_wordline_semantic_contract.json",
        REPO_ROOT / "docs/openyield_L0_semantic_gap_closure_report.json",
    ]
    for path in required_paths:
        assert path.exists(), f"missing required artifact: {path}"

    report = json.loads((REPO_ROOT / "docs/openyield_L0_semantic_gap_closure_report.json").read_text(encoding="utf-8"))

    assert report["canonical_sram_semantic_contract_available"] is True
    assert report["logical_to_openyield_parameter_map_available"] is True
    assert report["top_bank_semantic_contract_available"] is True
    assert report["time_control_decomposition_contract_available"] is True
    assert report["decoder_wordline_semantic_contract_available"] is True
    assert report["control_path_semantic_contracts_available"] is True

    unsupported = set(report["unsupported_features"])
    assert {
        "multi_bank",
        "multi_port",
        "write_mask",
        "words_per_row_gt_2",
    }.issubset(unsupported)

    assert report["remaining_L0_blockers_count"] == 0
    assert report["can_claim_L0_semantics_closed_now"] is True
    assert report["can_enter_L1_physical_primitive_closure"] is True
    assert report["can_enter_L2_placement_rule_closure"] is False
    assert report["can_enter_L3_module_gds_generation"] is False
    assert report["can_claim_full_openyield_gds_now"] is False
    assert report["can_claim_drc_clean_now"] is False
    assert report["can_claim_lvs_clean_now"] is False
    assert report["can_claim_timing_closure_now"] is False

    assert "SRAM_TOP" in report["semantics_closed_modules"]
    assert "BANK" in report["semantics_closed_modules"]
    assert "CONTROL_LOGIC" in report["semantics_closed_modules"]
    assert report["source_found_ports_partial_modules"] == []
    assert report["source_found_connections_unresolved_modules"] == []
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
