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
        "gen_inv": build_gate_cell_footprint("gen_inv", 1.20, 1.565),
        "gen_nand2": build_gate_cell_footprint("gen_nand2", 1.65, 1.565),
        "gen_wl_driver": build_gate_cell_footprint("gen_wl_driver", 1.55, 1.565),
    }
    plan = build_gate_row_packing_plan(
        block_name="unit_decoder",
        row_cells=[["gen_nand2", "gen_wl_driver"], ["gen_inv", "gen_nand2"]],
        footprints=footprints,
        origin_x=0.0,
        origin_y=0.0,
        explicit_opt_in=True,
        row_pitch=1.565,
    )
    assert len(plan.rows) == 2
    assert abs(plan.rows[0].cells[1].x - (plan.rows[0].cells[0].x + plan.rows[0].cells[0].width)) < 1e-9
    assert plan.average_intra_row_gap_um == 0.0
    assert plan.rows[0].mirror == "R0"
    assert plan.rows[1].mirror == "MX"
    assert "boundaries" in plan.rail_alignment
    assert StandaloneSpec(word_size=4, num_words=32, words_per_row=2).enable_openyield_gate_row_packing is False

    out_dir = REPO_ROOT / "outputs/test_openyield_gate_row_packing"
    result = generate_layout_prototype(
        repo_root=REPO_ROOT,
        mode="hybrid_openyield_prototype",
        out_dir=out_dir,
        metadata_dir=REPO_ROOT / "docs",
        word_size=4,
        num_words=32,
        words_per_row=2,
        enable_openyield_gate_row_packing=True,
    )
    gds_path = Path(result["gds_path"])
    assert gds_path.exists()
    assert gds_path.stat().st_size > 0
    report = json.loads((out_dir / "gate_row_packing_report.json").read_text(encoding="utf-8"))
    assert report["gate_row_packing_available"] is True
    assert report["hybrid_compacted_gds_generated"] is True
    assert report["intra_row_gap_removed"] is True
    print("openyield_gate_row_packing_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
