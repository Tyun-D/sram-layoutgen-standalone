from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.concrete_variant_resolver import derive_drive_scales, resolve_concrete_variants


def main() -> int:
    concrete = resolve_concrete_variants(REPO_ROOT / "docs/mapping/M12C3R_corrected_physical_variant_matrix.csv")
    assert concrete["unresolved_symbolic_variant_count_after_resolution"] == 0
    cfg16 = concrete["per_config"]["16x16"]["scales"]
    cfg64 = concrete["per_config"]["64x8"]["scales"]
    assert cfg16["clk_drive_scale"] == 1.0
    assert cfg64["clk_drive_scale"] == 1.0
    assert cfg16["pre_drive_scale"] == 1
    assert cfg64["pre_drive_scale"] == 1
    assert any(row["canonical_physical_cell_name"] == "PINV_NW250_PW500_L50" for row in concrete["rows"])
    print("M12C3A_concrete_variant_resolution_ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

