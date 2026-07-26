from pathlib import Path
import sys

CHECKOUT_ROOT = Path(__file__).resolve().parents[1]
if str(CHECKOUT_ROOT) not in sys.path:
    sys.path.insert(0, str(CHECKOUT_ROOT))

DEFAULT_EVIDENCE_ROOT = Path("/data1/qujh/work/sram_layoutgen_step45_clean")


def _evidence_root() -> Path:
    team_b_bundle = CHECKOUT_ROOT / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND2/clean.gds"
    return CHECKOUT_ROOT if team_b_bundle.exists() else DEFAULT_EVIDENCE_ROOT

from sram_layoutgen.openyield_adapter.and2_production_verification_gate import validate_and2_bundle


def test_and2_validate_bundle_smoke() -> None:
    repo_root = CHECKOUT_ROOT
    evidence_root = _evidence_root()
    bundle_dir = evidence_root / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND2"
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

    repo_root = CHECKOUT_ROOT
    src = _evidence_root() / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND2"
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
