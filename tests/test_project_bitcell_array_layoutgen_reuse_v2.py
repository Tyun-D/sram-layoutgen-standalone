from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from project_bitcell_array_layoutgen_reuse_v2 import NEGATIVE_CASES, run_negative_suite, validate_facts  # noqa: E402


def passing_facts() -> dict[str, object]:
    return {
        "formal_config_match": True,
        "real_bitcell_hierarchy": True,
        "horizontal_gap": 0,
        "vertical_gap": 0,
        "same_net_power_union": True,
        "power_component_count_ok": True,
        "power_polarity_ok": True,
        "dummy_row_ok": True,
        "dummy_column_ok": True,
        "tap_policy_ok": True,
        "replica_ok": True,
        "wl_order_ok": True,
        "duplicate_pin": False,
        "bl_complete": True,
        "br_complete": True,
        "manifest_sha_ok": True,
    }


def test_positive_facts_pass() -> None:
    assert validate_facts(passing_facts()) == (True, None)


def test_all_required_negative_cases_are_rejected_with_specific_code() -> None:
    report = run_negative_suite(passing_facts())
    assert report["case_count"] == len(NEGATIVE_CASES) == 16
    assert report["unexpected_pass_count"] == 0
    assert report["passed"] is True
