from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.layout_prototype import generate_layout_prototype  # noqa: E402


def main() -> int:
    base_out = REPO_ROOT / "outputs/test_openyield_layout_prototype/baseline"
    hybrid_out = REPO_ROOT / "outputs/test_openyield_layout_prototype/hybrid"
    baseline = generate_layout_prototype(
        repo_root=REPO_ROOT,
        mode="legacy_baseline",
        out_dir=base_out,
        metadata_dir=REPO_ROOT / "docs",
        word_size=4,
        num_words=32,
        words_per_row=2,
    )
    hybrid = generate_layout_prototype(
        repo_root=REPO_ROOT,
        mode="hybrid_openyield_prototype",
        out_dir=hybrid_out,
        metadata_dir=REPO_ROOT / "docs",
        word_size=4,
        num_words=32,
        words_per_row=2,
    )
    assert Path(baseline["gds_path"]).exists()
    assert Path(hybrid["gds_path"]).exists()
    assert baseline["gds_size_bytes"] > 0
    assert hybrid["gds_size_bytes"] > 0
    assert len(hybrid["module_coverage"]) == 15
    assert "sense_amp" in hybrid["openyield_driven_modules"]
    assert "column_mux" in hybrid["openyield_driven_modules"]
    assert "DELAY_CHAIN" in hybrid["fallback_modules"]
    report = json.loads((REPO_ROOT / "docs/openyield_layout_prototype_generation_report.json").read_text(encoding="utf-8"))
    gates = report["gates"]
    assert gates["legacy_baseline_attempted"] is True
    assert gates["hybrid_openyield_attempted"] is True
    assert gates["hybrid_openyield_gds_generated"] is True
    assert gates["module_coverage_available"] is True
    assert gates["can_claim_full_openyield_layout_now"] is False
    print("openyield_layout_prototype_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
