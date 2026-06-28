from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.gate_row_packer import build_gate_cell_footprint, build_gate_row_packing_plan  # noqa: E402
from sram_layoutgen.openyield_adapter.gds_row_abutment_audit import audit_gds_row_abutment  # noqa: E402
from sram_layoutgen.tech import Tech  # noqa: E402


def main() -> int:
    tech = Tech.freepdk45(REPO_ROOT)
    dff = tech.cell("dff")
    fp = build_gate_cell_footprint(
        "dff",
        dff.width,
        dff.height,
        gds_path=dff.gds_path,
        bbox_x0=dff.bbox_x0,
        bbox_y0=dff.bbox_y0,
        bbox_x1=dff.bbox_x1,
        bbox_y1=dff.bbox_y1,
    )
    plan = build_gate_row_packing_plan(
        block_name="dff_unit",
        row_cells=[["dff", "dff"], ["dff", "dff"], ["dff"]],
        footprints={"dff": fp},
        origin_x=0.0,
        origin_y=0.0,
        explicit_opt_in=True,
        vertical_abutment_policy="rail_to_rail_geometry_abutment",
    )
    assert plan.rows[0].cells[1].x + fp.bbox_x0 == plan.rows[0].cells[0].x + fp.bbox_x1
    assert plan.rail_alignment["same_net_rail_touch_or_overlap_pass"] is True
    audit = audit_gds_row_abutment(
        REPO_ROOT / "outputs/layout_prototype/hybrid_openyield_rail_abutted/hybrid_openyield_rail_abutted.gds",
        layout_json=REPO_ROOT / "outputs/layout_prototype/hybrid_openyield_rail_abutted/hybrid_openyield_rail_abutted.layout.json",
    )
    assert audit["dff_row_packing_attempted"] is True
    assert audit["dff_left_right_abutment_pass"] is True
    assert audit["dff_vertical_abutment_pass"] is True
    assert audit["dff_real_abutment_pass"] is True
    payload = json.loads((REPO_ROOT / "outputs/layout_prototype/hybrid_openyield_rail_abutted/gds_row_abutment_audit.json").read_text(encoding="utf-8"))
    assert payload["dff_real_abutment_pass"] is True
    print("openyield_dff_row_packing_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
