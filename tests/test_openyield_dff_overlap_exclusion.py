from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.cell_rail_overlap_eligibility import classify_cell_rail_overlap  # noqa: E402
from sram_layoutgen.openyield_adapter.gds_row_abutment_audit import audit_gds_row_abutment  # noqa: E402
from sram_layoutgen.openyield_adapter.layout_prototype import build_spec, generate_layout_prototype  # noqa: E402
from sram_layoutgen.standalone import StandaloneSpec  # noqa: E402


def main() -> int:
    spec = StandaloneSpec(word_size=4, num_words=32, words_per_row=2)
    assert spec.enable_openyield_power_rail_overlap_packing is False
    assert spec.exclude_dff_vertical_overlap is False

    overlap_spec = build_spec(
        mode="hybrid_openyield_prototype",
        word_size=4,
        num_words=32,
        words_per_row=2,
        enable_openyield_gate_row_packing=True,
        enable_openyield_rail_to_rail_abutment=True,
        enable_openyield_power_rail_overlap_packing=True,
        exclude_dff_vertical_overlap=True,
    )
    assert overlap_spec.enable_openyield_dff_row_packing is True
    assert overlap_spec.exclude_dff_vertical_overlap is True

    dff = classify_cell_rail_overlap(REPO_ROOT, "dff")
    assert dff.eligibility_class == "excluded_dff_pending_manual_review"

    out_dir = REPO_ROOT / "outputs/test_openyield_dff_overlap_exclusion"
    result = generate_layout_prototype(
        repo_root=REPO_ROOT,
        mode="hybrid_openyield_prototype",
        out_dir=out_dir,
        metadata_dir=REPO_ROOT / "docs",
        word_size=4,
        num_words=32,
        words_per_row=2,
        enable_openyield_gate_row_packing=True,
        enable_openyield_rail_to_rail_abutment=True,
        enable_openyield_power_rail_overlap_packing=True,
        exclude_dff_vertical_overlap=True,
    )
    audit = audit_gds_row_abutment(
        Path(result["gds_path"]),
        layout_json=Path(result["metrics"]["layout_json"]),
        eligibility=REPO_ROOT / "docs/mapping/openyield_cell_rail_overlap_eligibility.csv",
    )
    assert audit["dff_row_packing_attempted"] is True
    assert audit["dff_left_right_abutment_pass"] is True
    assert audit["dff_vertical_overlap_found"] is False
    assert audit["dff_vertical_overlap_forbidden_pass"] is True
    payload = json.loads((out_dir / "prototype_result.json").read_text(encoding="utf-8"))
    assert payload["spec"]["exclude_dff_vertical_overlap"] is True
    print("openyield_dff_overlap_exclusion_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
