#!/usr/bin/env python3
"""Fail closed unless a complete Layoutgen physical reuse contract is loaded."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REQUIRED_CONTRACTS = {
    "BITCELL_ROW_PITCH_CONTRACT",
    "BITCELL_COLUMN_PITCH_CONTRACT",
    "BITCELL_EDGE_ABUTMENT_CONTRACT",
    "SAME_NET_POWER_RAIL_OVERLAP_CONTRACT",
    "PARENT_POWER_STITCH_CONTRACT",
    "WL_DRIVER_ARRAY_SEAM_CONTRACT",
    "DUMMY_ROW_COLUMN_CONTRACT",
    "TAP_INSERTION_CONTRACT",
    "REPLICA_CELL_COLUMN_CONTRACT",
    "PIN_ACCESS_CONTRACT",
    "HIERARCHICAL_CONNECTIVITY_CONTRACT",
}
REJECTION_CODE = "REUSE_CONTRACT_NOT_LOADED"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def evaluate(contract_path: Path) -> dict[str, Any]:
    errors: list[str] = []
    contract: dict[str, Any] = {}
    if not contract_path.is_file():
        errors.append("contract_file_missing")
    else:
        try:
            contract = json.loads(contract_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"contract_parse_failed:{type(exc).__name__}")

    declared = set(contract.get("contracts", {}))
    missing = sorted(REQUIRED_CONTRACTS - declared)
    if missing:
        errors.append("required_contracts_missing:" + ",".join(missing))
    if contract.get("load_policy", {}).get("missing_or_invalid_rejection_code") != REJECTION_CODE:
        errors.append("fail_closed_rejection_code_missing")
    if not contract.get("authority_requirements", {}).get("forbid_as_authoritative_array"):
        errors.append("forbidden_authority_object_list_missing")

    passed = not errors
    return {
        "gate": "LAYOUTGEN_PHYSICAL_REUSE_CONTRACT_LOAD_GATE",
        "passed": passed,
        "status": "REUSE_CONTRACT_LOADED" if passed else REJECTION_CODE,
        "rejection_code": None if passed else REJECTION_CODE,
        "contract_path": str(contract_path.resolve()),
        "contract_sha256": sha256(contract_path) if contract_path.is_file() else None,
        "contract_id": contract.get("contract_id"),
        "required_contract_count": len(REQUIRED_CONTRACTS),
        "loaded_contract_count": len(declared & REQUIRED_CONTRACTS),
        "missing_contracts": missing,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(args.contract)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(report["status"])
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
