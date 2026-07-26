from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.pnand2_verification_gate import validate_bundle


@pytest.mark.skipif(
    not Path("/data1/qujh/work/sram_layoutgen_step45_clean/outputs/TeamB_PNAND2_reference_demo/current_supported_config/PNAND2_source_lock.json").exists(),
    reason="generation bundle not present",
)
def test_pnand2_debug_label_negative_rejected() -> None:
    import gdstk

    base = Path("/data1/qujh/work/sram_layoutgen_step45_clean/outputs/TeamB_PNAND2_reference_demo/current_supported_config")
    with tempfile.TemporaryDirectory(prefix="pnand2_neg_pytest_") as tmp:
        tmp_dir = Path(tmp) / "bundle"
        shutil.copytree(base, tmp_dir)
        gds_path = tmp_dir / "PNAND2_NW180_PW270_L50_FPDK45.gds"
        lib = gdstk.read_gds(gds_path)
        top = next(cell for cell in lib.cells if cell.name == "PNAND2_NW180_PW270_L50_FPDK45")
        top.add(gdstk.Label("DEBUG", (0.2, 1.0), layer=11, texttype=2))
        lib.write_gds(gds_path)
        validation = validate_bundle(
            bundle_dir=tmp_dir,
            klayout_bin=Path("/usr/bin/klayout"),
            drc_deck=Path("/data1/qujh/work/sram_layoutgen_step45_clean/technology/freepdk45/tech/freepdk45.lydrc"),
            lvs_deck=Path("/data1/qujh/work/sram_layoutgen_step45_clean/technology/freepdk45/tech/freepdk45.lylvs"),
            top_name="PNAND2_NW180_PW270_L50_FPDK45",
        )
        assert "DIRECT_TOP_LABEL_CONTRACT_FAILED" in validation.rejection_codes
