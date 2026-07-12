from __future__ import annotations

import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def main() -> None:
    identity = json.loads((REPO_ROOT / "outputs/M12C4AC_dff_connectivity_repair/current_supported_config/M12C4AC_canonical_topology_identity.json").read_text())
    report = json.loads((REPO_ROOT / "docs/M12C4AC_dff_connectivity_repair_report.json").read_text())
    topo_hash = identity["source_topology_hash"]
    assert len(topo_hash) == 12
    assert report["source_topology_hash_match"] is True
    assert report["selected_floorplan_architecture"] == "SINGLE_ROW_SOURCE_ORDER"
    assert identity["legacy_hashes"]["m12c4a_source_contract_hash"] != topo_hash
    assert identity["legacy_hashes"]["m12c4a_generator_hash"] != topo_hash


if __name__ == "__main__":
    main()

