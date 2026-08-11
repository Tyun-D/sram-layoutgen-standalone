from __future__ import annotations


def power_policy() -> dict[str, object]:
    return {
        "policy": "horizontal_m1_top_bottom_rails_v1",
        "vdd": "top rail",
        "vss": "bottom rail",
        "power_endpoint_coverage_by_plan": "100%",
    }

