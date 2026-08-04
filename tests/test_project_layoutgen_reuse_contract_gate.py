from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from project_layoutgen_reuse_contract_gate import REJECTION_CODE, evaluate  # noqa: E402


def test_repository_contract_loads() -> None:
    report = evaluate(REPO_ROOT / "docs/LAYOUTGEN_PHYSICAL_REUSE_CONTRACT.json")
    assert report["passed"] is True
    assert report["status"] == "REUSE_CONTRACT_LOADED"
    assert report["loaded_contract_count"] == report["required_contract_count"]


def test_missing_contract_fails_closed(tmp_path: Path) -> None:
    report = evaluate(tmp_path / "missing.json")
    assert report["passed"] is False
    assert report["rejection_code"] == REJECTION_CODE


def test_incomplete_contract_fails_closed(tmp_path: Path) -> None:
    contract = tmp_path / "incomplete.json"
    contract.write_text(json.dumps({"contracts": {}}), encoding="utf-8")
    report = evaluate(contract)
    assert report["passed"] is False
    assert report["rejection_code"] == REJECTION_CODE
