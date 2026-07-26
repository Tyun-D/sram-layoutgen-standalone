from __future__ import annotations

from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.primitive_interface_auditor import audit_approved_primitive_interfaces


def main() -> None:
    reusable_root = REPO_ROOT / "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells"
    audit = audit_approved_primitive_interfaces(reusable_root)
    rows = {row["cell_name"]: row for row in audit["exact_rows"]}
    pinv = rows["PINV_NW250_PW500_L50"]
    tg = rows["TRANSMISSION_GATE_NW250_PW500_L50"]
    pinv_height = float(pinv["layout_bbox"][3]) - float(pinv["layout_bbox"][1])
    tg_height = float(tg["layout_bbox"][3]) - float(tg["layout_bbox"][1])
    assert abs(pinv_height - 1.8875) < 1e-9
    assert abs(tg_height - 1.8850) < 1e-9
    assert round(abs(pinv_height - tg_height), 4) == 0.0025
    assert pinv["vdd_bbox"][1] == 1.7875
    assert pinv["vdd_bbox"][3] == 1.8525
    assert pinv["vdd_bbox"][1] == tg["vdd_bbox"][1]
    assert pinv["vdd_bbox"][3] == tg["vdd_bbox"][3]
    assert pinv["vss_bbox"][1] == -0.0325
    assert pinv["vss_bbox"][3] == 0.0325
    assert pinv["vss_bbox"][1] == tg["vss_bbox"][1]
    assert pinv["vss_bbox"][3] == tg["vss_bbox"][3]


if __name__ == "__main__":
    main()
