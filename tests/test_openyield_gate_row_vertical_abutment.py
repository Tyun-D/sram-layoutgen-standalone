from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.gate_row_packer import (  # noqa: E402
    build_gate_cell_footprint,
    build_gate_row_packing_plan,
)
from sram_layoutgen.openyield_adapter.layout_prototype import generate_layout_prototype  # noqa: E402
from sram_layoutgen.standalone import StandaloneSpec  # noqa: E402


def main() -> int:
    footprints = {
        "gen_nand2": build_gate_cell_footprint("gen_nand2", 1.65, 1.565),
        "gen_wl_driver": build_gate_cell_footprint("gen_wl_driver", 1.55, 1.565),
    }
    plan = build_gate_row_packing_plan(
        block_name="vertical_unit",
        row_cells=[["gen_nand2", "gen_wl_driver"], ["gen_nand2", "gen_wl_driver"], ["gen_nand2", "gen_wl_driver"]],
        footprints=footprints,
        origin_x=0.0,
        origin_y=0.0,
        explicit_opt_in=True,
        vertical_abutment_policy="zero_gap_alternating_mx",
    )
    assert plan.row_gap == 0.0
    assert abs(plan.row_pitch - 1.565) < 1e-9
    assert abs(plan.rows[1].origin_y - plan.rows[0].origin_y - 1.565) < 1e-9
    assert [row.mirror for row in plan.rows] == ["R0", "MX", "R0"]
    assert plan.extra_interrow_power_stripe_inserted is False
    assert "boundaries" in plan.rail_alignment
    assert StandaloneSpec(word_size=4, num_words=32, words_per_row=2).enable_openyield_gate_row_vertical_abutment is False

    out_dir = REPO_ROOT / "outputs/test_openyield_gate_row_vertical_abutment"
    result = generate_layout_prototype(
        repo_root=REPO_ROOT,
        mode="hybrid_openyield_prototype",
        out_dir=out_dir,
        metadata_dir=REPO_ROOT / "docs",
        word_size=4,
        num_words=32,
        words_per_row=2,
        enable_openyield_gate_row_packing=True,
        enable_openyield_gate_row_vertical_abutment=True,
    )
    gds_path = Path(result["gds_path"])
    assert gds_path.exists()
    assert gds_path.stat().st_size > 0
    report = json.loads((out_dir / "gate_row_vertical_abutment_report.json").read_text(encoding="utf-8"))
    assert report["gate_row_vertical_abutment_available"] is True
    assert report["row_gap_removed"] is True
    assert report["extra_interrow_power_stripe_removed"] is True
    assert report["new_vertical_gap_um"] == 0.0
    print("openyield_gate_row_vertical_abutment_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
