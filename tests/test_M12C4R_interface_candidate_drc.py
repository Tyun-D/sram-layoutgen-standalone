from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.primitive_pair_interface_qualifier import qualify_pinv_tg_interfaces
from sram_layoutgen.signoff import count_klayout_items


def main() -> None:
    reusable_root = REPO_ROOT / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells"
    with TemporaryDirectory(prefix="m12c4r_interface_") as tmp:
        tmp_root = Path(tmp)
        qualify_pinv_tg_interfaces(
            reusable_root,
            tmp_root,
            REPO_ROOT / "technology/freepdk45/tech/freepdk45.lydrc",
            Path("/usr/bin/klayout"),
        )
        direct = tmp_root / "direct_boundary_abutment/M12C4R_DIRECT_BOUNDARY_ABUTMENT.lyrdb"
        spaced = tmp_root / "rail_aligned_spaced_row_with_power_stitch/M12C4R_RAIL_ALIGNED_SPACED_ROW_WITH_POWER_STITCH.lyrdb"
        wrapper = tmp_root / "common_wrapper_envelope_with_spaced_children/M12C4R_COMMON_WRAPPER_ENVELOPE_WITH_SPACED_CHILDREN.lyrdb"
        assert count_klayout_items(direct) == 0
        assert count_klayout_items(spaced) == 1
        assert count_klayout_items(wrapper) == 1
    root = REPO_ROOT / "outputs/M12C4R_source_interface_routing_correction/current_supported_config"
    matrix = json.loads((root / "M12C4R_interface_candidate_drc_report.json").read_text(encoding="utf-8"))["rows"]
    direct_row = next(row for row in matrix if row["candidate_name"] == "DIRECT_BOUNDARY_ABUTMENT")
    assert direct_row["drc_passed"] is True
    graph = json.loads((root / "direct_boundary_abutment/connectivity.json").read_text(encoding="utf-8"))
    assert "PINV_VDD" in graph["pin_labels"]
    assert "TG_VDD" in graph["pin_labels"]


if __name__ == "__main__":
    main()
