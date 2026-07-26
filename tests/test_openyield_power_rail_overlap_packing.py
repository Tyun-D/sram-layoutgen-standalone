from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.cell_rail_overlap_eligibility import classify_cell_rail_overlap  # noqa: E402
from sram_layoutgen.openyield_adapter.gate_row_packer import build_gate_cell_footprint, build_gate_row_packing_plan  # noqa: E402
from sram_layoutgen.openyield_adapter.gds_row_abutment_audit import audit_gds_row_abutment  # noqa: E402
from sram_layoutgen.openyield_adapter.layout_prototype import generate_layout_prototype  # noqa: E402
from sram_layoutgen.tech import Tech  # noqa: E402


def main() -> int:
    tech = Tech.freepdk45(REPO_ROOT)
    footprints = {
        name: build_gate_cell_footprint(
            name,
            tech.cell(name).width,
            tech.cell(name).height,
            gds_path=tech.cell(name).gds_path,
            bbox_x0=tech.cell(name).bbox_x0,
            bbox_y0=tech.cell(name).bbox_y0,
            bbox_x1=tech.cell(name).bbox_x1,
            bbox_y1=tech.cell(name).bbox_y1,
        )
        for name in ["gen_nand2", "gen_wl_driver"]
    }
    eligibility = {name: classify_cell_rail_overlap(REPO_ROOT, name) for name in footprints}
    plan = build_gate_row_packing_plan(
        block_name="overlap_unit",
        row_cells=[["gen_nand2", "gen_wl_driver"], ["gen_nand2", "gen_wl_driver"]],
        footprints=footprints,
        origin_x=0.0,
        origin_y=0.0,
        explicit_opt_in=True,
        vertical_abutment_policy="same_net_power_rail_overlap_packing",
        overlap_eligibility=eligibility,
        row_domain="standard_gate_domain",
    )
    assert plan.vertical_abutment_policy == "same_net_power_rail_overlap_packing"
    assert plan.rail_alignment["positive_overlap_count"] > 0
    assert plan.rail_alignment["positive_overlap_depth_um"] > 0.0
    assert plan.rail_alignment["diff_net_short_found"] is False

    out_dir = REPO_ROOT / "outputs/test_openyield_power_rail_overlap_packing"
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
    gds_path = Path(result["gds_path"])
    assert gds_path.exists() and gds_path.stat().st_size > 0
    report = json.loads((out_dir / "rail_overlap_packing_report.json").read_text(encoding="utf-8"))
    assert report["same_net_power_rail_overlap_packing_available"] is True
    assert report["positive_overlap_applied"] is True
    assert report["positive_overlap_depth_um"] > 0.0
    audit = audit_gds_row_abutment(
        gds_path,
        layout_json=Path(result["metrics"]["layout_json"]),
        eligibility=REPO_ROOT / "docs/mapping/openyield_cell_rail_overlap_eligibility.csv",
    )
    assert audit["positive_overlap_count"] > 0
    assert audit["same_net_power_overlap_pass"] is True
    print("openyield_power_rail_overlap_packing_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
