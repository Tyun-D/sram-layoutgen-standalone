from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.M9_openyield_netlist_translator import run_m9_openyield_netlist_translator  # noqa: E402


def main() -> int:
    out_dir = REPO_ROOT / "outputs/M9_openyield_netlist_translator/current_supported_config"
    out_json = REPO_ROOT / "docs/M9_openyield_netlist_translator_report.json"
    out_report = REPO_ROOT / "docs/M9_openyield_netlist_translator_report.md"
    report = run_m9_openyield_netlist_translator(
        repo_root=REPO_ROOT,
        status_md=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
        status_json=REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json",
        out_dir=out_dir,
        out_json=out_json,
        out_report=out_report,
    )
    assert report["status_file_read"] is True
    assert report["status_file_updated"] is True
    assert report["m8rc_confirmation_loaded"] is True
    assert report["generated_from_layoutgen_source"] is True
    assert report["reference_file_copied_as_output"] is False
    assert report["uses_access_module"] is False
    assert report["uses_floorplan_proxy"] is False
    assert report["arbitrary_module_scatter_used"] is False
    assert report["label_only_binding_as_implementation_count"] == 0
    assert report["translated_top_cell_name"] == "openyield_netlist_translated_sram"
    assert report["translated_gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["annotated_debug_gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["clean_review_gds_sanity_status"] == "GDS_PARSED_SANITY_PASSED"
    assert report["openyield_module_binding_count"] == 20
    assert report["openyield_net_binding_count"] >= 34
    assert report["human_klayout_review_required"] is True
    assert report["can_enter_next_stage_before_human_review"] is False
    for name in [
        "openyield_netlist_translated_sram.gds",
        "openyield_netlist_translated_sram_clean_review.gds",
        "openyield_netlist_translated_sram_annotated_debug.gds",
        "M9_SRAM_SPEC.json",
        "M9_SRAM_SPEC.md",
        "M9_module_binding_matrix.json",
        "M9_module_binding_matrix.md",
        "M9_module_binding_matrix.csv",
        "M9_net_binding_matrix.json",
        "M9_net_binding_matrix.md",
        "M9_net_binding_matrix.csv",
        "M9_placement_routing_power_intent.json",
        "M9_placement_routing_power_intent.md",
        "M9_translator_run_report.json",
        "M9_translator_run_report.md",
        "review_gds_manifest.json",
        "review_gds_manifest.md",
    ]:
        assert (out_dir / name).exists(), name
    assert out_json.exists()
    assert out_report.exists()
    for name in [
        "docs/evidence/M9_openyield_netlist_translator_summary.md",
        "docs/mapping/M9_module_binding_matrix.csv",
        "docs/mapping/M9_net_binding_matrix.csv",
    ]:
        assert (REPO_ROOT / name).exists(), name
    status = json.loads((REPO_ROOT / "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json").read_text(encoding="utf-8"))
    assert status["current_stage"] == "M9"
    assert status["next_stage"] == "WAIT_HUMAN_KLAYOUT_REVIEW"
    print("M9_openyield_netlist_translator_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
