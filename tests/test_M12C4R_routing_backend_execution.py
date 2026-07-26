from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.routing_backend_execution_qualifier import execute_routing_backend_diagnostic
from sram_layoutgen.signoff import count_klayout_items


def main() -> None:
    reusable_root = REPO_ROOT / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells"
    with TemporaryDirectory(prefix="m12c4r_route_") as tmp:
        tmp_root = Path(tmp)
        result = execute_routing_backend_diagnostic(
            reusable_root,
            tmp_root,
            REPO_ROOT / "technology/freepdk45/tech/freepdk45.lydrc",
            Path("/usr/bin/klayout"),
            REPO_ROOT,
        )
        assert result["summary"]["route_drc_marker_count"] == 0
        assert result["summary"]["routing_backend_execution_test_passed"] is True
    root = REPO_ROOT / "outputs/M12C4R_source_interface_routing_correction/current_supported_config/routing_diagnostic"
    assert count_klayout_items(root / "M12C4R_ROUTING_BACKEND_DIAGNOSTIC.lyrdb") == 0
    connectivity = json.loads((root / "connectivity_report.json").read_text(encoding="utf-8"))
    assert connectivity["PINV1.Z connected_to PINV2.A"] is True
    assert connectivity["signal_connected_to_VDD"] is False
    assert connectivity["signal_connected_to_VSS"] is False
    assert connectivity["VDD_connected_across_children"] is True
    assert connectivity["VSS_connected_across_children"] is True
    assert connectivity["VDD_connected_to_VSS"] is False
    route_graph = json.loads((root / "route_graph.json").read_text(encoding="utf-8"))
    assert [segment["layer"] for segment in route_graph["segments"]] == ["m1", "via1", "m2", "via1", "m1"]


if __name__ == "__main__":
    main()
