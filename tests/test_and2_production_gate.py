import shutil
import tempfile
from pathlib import Path
import sys

import gdstk
import pytest

CHECKOUT_ROOT = Path(__file__).resolve().parents[1]
if str(CHECKOUT_ROOT) not in sys.path:
    sys.path.insert(0, str(CHECKOUT_ROOT))

DEFAULT_EVIDENCE_ROOT = Path("/data1/qujh/work/sram_layoutgen_step45_clean")


def _evidence_root() -> Path:
    team_b_bundle = CHECKOUT_ROOT / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND2/clean.gds"
    return CHECKOUT_ROOT if team_b_bundle.exists() else DEFAULT_EVIDENCE_ROOT

from sram_layoutgen.openyield_adapter.and2_production_verification_gate import AND2_NAME, _build_child_immutability_report
from sram_layoutgen.openyield_adapter.and2_source_lock import build_and2_source_lock


def test_and2_source_lock_extracts_anomaly() -> None:
    root = Path("/data1/qujh/work/external/OpenYield")
    lock = build_and2_source_lock(root)
    assert lock["class_name"] == "AND2"
    assert lock["source_instance_display_name_anomaly"]["present"] is True


def test_child_immutability_tolerates_parent_route_and_transform() -> None:
    evidence_root = _evidence_root()
    base = evidence_root / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND2"
    if not base.exists():
        pytest.skip("AND2 evidence bundle not present")
    with tempfile.TemporaryDirectory(prefix="and2_immutability_pass_") as tmp:
        work = Path(tmp) / "AND2"
        shutil.copytree(base, work)
        lib = gdstk.read_gds(work / "clean.gds")
        top = next(cell for cell in lib.cells if cell.name == AND2_NAME)
        top.add(gdstk.rectangle((2.0, 0.2), (2.08, 0.28), layer=11, datatype=0))
        top.references[0].origin = (top.references[0].origin[0] + 0.03, top.references[0].origin[1] + 0.02)
        lib.write_gds(work / "clean.gds")
        report = _build_child_immutability_report(repo_root=evidence_root, cell_dir=work, write_artifacts=False)
        assert report["child_immutability_passed"] is True


def test_child_immutability_detects_clone_geometry_change() -> None:
    evidence_root = _evidence_root()
    base = evidence_root / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND2"
    if not base.exists():
        pytest.skip("AND2 evidence bundle not present")
    with tempfile.TemporaryDirectory(prefix="and2_immutability_fail_") as tmp:
        work = Path(tmp) / "AND2"
        shutil.copytree(base, work)
        lib = gdstk.read_gds(work / "_clones/TEAMB_CLONE__nand.gds")
        lib.cells[0].add(gdstk.rectangle((0.1, 0.1), (0.18, 0.18), layer=11, datatype=0))
        lib.write_gds(work / "_clones/TEAMB_CLONE__nand.gds")
        report = _build_child_immutability_report(repo_root=evidence_root, cell_dir=work, write_artifacts=False)
        assert report["child_immutability_passed"] is False
