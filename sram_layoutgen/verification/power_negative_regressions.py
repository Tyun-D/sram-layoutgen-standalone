from __future__ import annotations

from typing import Any


NEGATIVE_CASES = [
    ("delete_vdd_rail", "删除 VDD rail"),
    ("delete_power_via", "删除电源 via"),
    ("disconnect_child_vss", "断开 child VSS"),
    ("vdd_vss_short", "制造 VDD/VSS short"),
    ("power_to_signal_contact", "制造 power-to-signal contact"),
    ("wrong_power_pin_label", "错误 power pin label"),
]


def blocked_negative_matrix(reason: str) -> list[dict[str, Any]]:
    rows = []
    for case_id, description in NEGATIVE_CASES:
        rows.append(
            {
                "negative_case_id": case_id,
                "description": description,
                "status": "BLOCKED_NO_GEOMETRY_MUTATION_HARNESS",
                "rejected_as_expected": False,
                "evidence": "",
                "note": reason,
            }
        )
    return rows
