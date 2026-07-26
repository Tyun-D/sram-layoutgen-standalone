from pathlib import Path
import sys

REPO_ROOT = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.and2_production_verification_gate import validate_and2_bundle


def test_and2_validate_bundle_smoke() -> None:
    repo_root = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
    bundle_dir = repo_root / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND2"
    result = validate_and2_bundle(
        repo_root=repo_root,
        bundle_dir=bundle_dir,
        openyield_root=Path("/data1/qujh/work/external/OpenYield"),
        klayout_bin=Path("/usr/bin/klayout"),
        drc_deck=repo_root / "technology/freepdk45/tech/freepdk45.lydrc",
    )
    assert "rejection_codes" in result


def test_and2_wrong_pinv_variant_is_specific_code(tmp_path) -> None:
    import shutil

    from sram_layoutgen.openyield_adapter.and2_negative_regressions import _mutate_instance_binding

    repo_root = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
    src = repo_root / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND2"
    work = tmp_path / "AND2"
    shutil.copytree(src, work)
    _mutate_instance_binding(work / "parameter_mapping.json", "inv_driver", "resolved_physical_cell", "PINV_NW180_PW270_L50")
    result = validate_and2_bundle(
        repo_root=repo_root,
        bundle_dir=work,
        openyield_root=Path("/data1/qujh/work/external/OpenYield"),
        klayout_bin=Path("/usr/bin/klayout"),
        drc_deck=repo_root / "technology/freepdk45/tech/freepdk45.lydrc",
    )
    assert result["rejection_codes"][0] == "WRONG_PINV_VARIANT"
