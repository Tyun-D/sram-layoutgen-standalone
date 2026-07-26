from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.pnand2_source_lock import build_pnand2_source_lock


def test_pnand2_source_lock_matches_authority() -> None:
    payload = build_pnand2_source_lock(Path("/data1/qujh/work/external/OpenYield"))
    assert payload["authority_commit"] == "1c34428d8b913963c4971d093b1a7c2df97a2509"
    assert payload["git_blob_sha"] == "e3269a942e18931d5a75eda7252a8abda6540bf5"
    assert payload["top_pin_order"] == ["VDD", "VSS", "A", "B", "Z"]
    assert payload["requested_parameter_contract_nm"] == {"nmos_width_nm": 180, "pmos_width_nm": 270, "length_nm": 50}
    assert len(payload["device_inventory"]) == 4
