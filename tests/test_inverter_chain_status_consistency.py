from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.inverter_chain_layout_quality import recompute_final_status


MODULES = ["pdrive2_for_pre", "wl_pdrive", "pdrive"]


def _write_module(root: Path, module_name: str, *, gate_overrides: dict | None = None, negative_passed: bool = True, clean_bytes: bytes | None = None) -> str:
    cell_dir = root / "current_supported_config" / module_name
    (cell_dir / "drc").mkdir(parents=True, exist_ok=True)
    (cell_dir / "negative_tests").mkdir(parents=True, exist_ok=True)
    machine_gate = {
        "source_lock_complete": True,
        "parameter_binding_closed": True,
        "top_pin_contract_exact": True,
        "internal_net_not_exposed": True,
        "child_count_exact": True,
        "stage_order_exact": True,
        "topology_match": True,
        "hierarchy_closure_passed": True,
        "child_immutability_passed": True,
        "connectivity_passed": True,
        "foreign_net_passed": True,
        "strict_source_derived_structural_gate_passed": True,
        "deterministic_A_B_byte_identical": True,
        "negative_tests_passed": True,
        "review_artifacts_complete": True,
        "drc_marker_count": 0,
    }
    if gate_overrides:
        machine_gate.update(gate_overrides)
    (cell_dir / "machine_gate.json").write_text(json.dumps(machine_gate) + "\n", encoding="utf-8")
    (cell_dir / "drc" / f"{module_name}_drc_summary.json").write_text(json.dumps({"marker_count": machine_gate["drc_marker_count"], "drc_passed": machine_gate["drc_marker_count"] == 0}) + "\n", encoding="utf-8")
    (cell_dir / "negative_tests" / f"{module_name}_negative_test_summary.json").write_text(
        json.dumps(
            {
                "total_count": 1,
                "mutation_effective_count": 1,
                "production_validator_invoked_count": 1,
                "unexpected_negative_test_pass_count": 0 if negative_passed else 1,
                "negative_tests_passed": negative_passed,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    payload = clean_bytes if clean_bytes is not None else module_name.encode("utf-8")
    (cell_dir / "clean.gds").write_bytes(payload)
    return hashlib.sha256(payload).hexdigest()


def test_recompute_final_status_all_green(tmp_path: Path) -> None:
    expected = {}
    for module_name in MODULES:
        expected[module_name] = _write_module(tmp_path, module_name)
    payload = recompute_final_status(out_root=tmp_path, module_order=MODULES)
    assert payload["all_modules_green"] is True
    assert [row["module_name"] for row in payload["modules"]] == MODULES
    assert {row["module_name"]: row["clean_gds_sha256"] for row in payload["modules"]} == expected
    assert (tmp_path / "INVERTER_CHAIN_FINAL_STATUS.json").exists()
    assert (tmp_path / "INVERTER_CHAIN_FINAL_STATUS.md").exists()


def test_recompute_final_status_detects_machine_gate_conflict(tmp_path: Path) -> None:
    for module_name in MODULES:
        _write_module(tmp_path, module_name)
    _write_module(tmp_path, "wl_pdrive", gate_overrides={"connectivity_passed": False})
    payload = recompute_final_status(out_root=tmp_path, module_order=MODULES)
    failing = next(row for row in payload["modules"] if row["module_name"] == "wl_pdrive")
    assert failing["all_required_gates_true"] is False
    assert payload["all_modules_green"] is False


def test_recompute_final_status_detects_negative_summary_conflict(tmp_path: Path) -> None:
    for module_name in MODULES:
        _write_module(tmp_path, module_name)
    _write_module(tmp_path, "pdrive", negative_passed=False)
    payload = recompute_final_status(out_root=tmp_path, module_order=MODULES)
    failing = next(row for row in payload["modules"] if row["module_name"] == "pdrive")
    assert failing["negative_tests_passed"] is False
    assert payload["all_modules_green"] is False


def test_recompute_final_status_missing_module_raises(tmp_path: Path) -> None:
    _write_module(tmp_path, "pdrive2_for_pre")
    _write_module(tmp_path, "wl_pdrive")
    with pytest.raises(FileNotFoundError):
        recompute_final_status(out_root=tmp_path, module_order=MODULES)
