from __future__ import annotations

from pathlib import Path
from typing import Any

from .routing_backend_execution_qualifier import audit_routing_backend_sources


def audit_composite_routing_backend(repo_root: Path) -> dict[str, Any]:
    source_audit = audit_routing_backend_sources(repo_root)
    comparison_rows = [
        {
            "architecture": "LOCAL_M1_ONLY",
            "advantages": "minimal geometry generation",
            "risks": "no proven crossover path",
            "m1_pin_escape_supported": True,
            "m2_intercell_routing_supported": False,
            "via1_supported": False,
            "recommended": False,
        },
        {
            "architecture": "M1_SIGNAL_WITH_M2_CROSSOVER",
            "advantages": "supports pin escape and one controlled crossover layer",
            "risks": "must prove via insertion and M1 obstacle handling with executable evidence",
            "m1_pin_escape_supported": True,
            "m2_intercell_routing_supported": True,
            "via1_supported": True,
            "recommended": True,
        },
        {
            "architecture": "M1_PIN_ESCAPE_M2_COMPOSITE_ROUTING",
            "advantages": "clean primitive composition contract",
            "risks": "requires deterministic route channels around future composite obstacles",
            "m1_pin_escape_supported": True,
            "m2_intercell_routing_supported": True,
            "via1_supported": True,
            "recommended": False,
        },
    ]
    contract = {
        "local_pin_escape_layer": "m1",
        "primary_intercell_signal_layer": "m2",
        "crossover_layer": "m2",
        "via_stack": "m1_via1_m2",
        "power_layer": "m1",
        "ground_layer": "m1",
        "route_width_source": "sram_layoutgen.tech.Tech.freepdk45",
        "route_spacing_source": "sram_layoutgen.tech.Tech.freepdk45",
        "route_grid": "FreePDK45 manufacturing grid 0.0025um",
        "obstacle_layers": ["active", "poly", "contact", "m1"],
        "pin_access_policy": "escape each approved primitive pin on m1 before any m2 crossover",
        "route_determinism_policy": "fixed Manhattan ordering with deterministic route polygon generation",
        "power_stitch_policy": "explicit m1 VDD/VSS stitches only",
        "label_sanitization_policy": "diagnostic-only unique top labels",
        "routing_contract_status": "NOT_PROVEN_BY_M12C4R",
    }
    return {
        "inventory_rows": source_audit["rows"],
        "comparison_rows": comparison_rows,
        "contract": contract,
        "summary": {
            "routing_backend_audit_completed": True,
            "routing_contract_status": contract["routing_contract_status"],
            "composite_routing_contract_locked": False,
            "m1_pin_escape_supported": False,
            "m2_intercell_routing_supported": False,
            "via1_supported": False,
            "power_stitch_supported": False,
        },
    }
