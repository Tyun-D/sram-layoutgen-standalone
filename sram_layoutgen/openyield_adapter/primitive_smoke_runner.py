from __future__ import annotations

from pathlib import Path
from typing import Any


def run_primitive_smoke_generation(
    *,
    allowed: bool,
    out_dir: Path,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    if not allowed:
        return {
            "primitive_smoke_generation_allowed": False,
            "primitive_smoke_generation_attempted": False,
            "transmission_gate_smoke_generated": False,
            "pinv1_smoke_generated": False,
            "pinv2_smoke_generated": False,
            "pinv3_smoke_generated": False,
            "pinv4_smoke_generated": False,
            "distinct_variant_fingerprints_verified": False,
            "deterministic_regeneration_verified": False,
            "primitive_pin_sets_verified": False,
            "primitive_power_rails_verified": False,
            "primitive_device_counts_verified": False,
            "primitive_smoke_drc_run": False,
            "primitive_smoke_total_drc_marker_count": 0,
            "primitive_smoke_drc_passed": False,
            "reason": "Smoke generation is blocked because the trusted generator path is not fully parameter-complete.",
            "artifacts": [],
        }
    raise NotImplementedError("Smoke generation is intentionally blocked unless all trusted-generator gates pass.")
