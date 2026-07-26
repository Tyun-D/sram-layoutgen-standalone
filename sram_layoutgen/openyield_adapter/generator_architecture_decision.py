from __future__ import annotations

from typing import Any


COMPARISON_FIELDS = [
    "architecture_option",
    "technology_correctness",
    "device_geometry_support",
    "contact_via_support",
    "well_implant_support",
    "parameterized_width",
    "parameterized_length",
    "pin_generation",
    "power_rail_generation",
    "hierarchy",
    "deterministic_naming",
    "drc_history",
    "integration_effort",
    "licensing_provenance",
    "maintenance",
    "risk",
    "recommended_scope",
]


def decide_generator_architecture(
    *,
    trusted_device_generator_found: bool,
    trusted_gate_generator_found: bool,
    contact_via_generator_found: bool,
    well_implant_generation_supported: bool,
    parameterized_width_supported: bool,
    parameterized_length_supported: bool,
    openram_generator_can_be_called_outside_openram: bool,
) -> dict[str, Any]:
    rows = [
        {
            "architecture_option": "A_LAYOUTGEN_EXISTING_DEVICE_GATE_GENERATOR",
            "technology_correctness": "Partial proxy-style rule binding only",
            "device_geometry_support": "No trusted transistor primitive generator found",
            "contact_via_support": "Limited",
            "well_implant_support": "Limited",
            "parameterized_width": False,
            "parameterized_length": False,
            "pin_generation": "Partial",
            "power_rail_generation": "Partial",
            "hierarchy": "Good for composition only",
            "deterministic_naming": "Weak",
            "drc_history": "Candidate-only",
            "integration_effort": "Low",
            "licensing_provenance": "Local",
            "maintenance": "Low",
            "risk": "High risk of proxy geometry misuse",
            "recommended_scope": "REFERENCE_ONLY",
        },
        {
            "architecture_option": "B_OPENRAM_FREEPDK45_DEVICE_CONTACT_ADAPTER",
            "technology_correctness": "Strong FreePDK45 source-backed contract",
            "device_geometry_support": trusted_device_generator_found,
            "contact_via_support": contact_via_generator_found,
            "well_implant_support": well_implant_generation_supported,
            "parameterized_width": parameterized_width_supported,
            "parameterized_length": parameterized_length_supported,
            "pin_generation": trusted_gate_generator_found,
            "power_rail_generation": trusted_gate_generator_found,
            "hierarchy": "Good primitive hierarchy",
            "deterministic_naming": "Can be enforced by adapter",
            "drc_history": "OpenRAM-backed, but not yet requalified for OpenYield adapter",
            "integration_effort": "Medium",
            "licensing_provenance": "Known but bounded",
            "maintenance": "Medium",
            "risk": "Best option if adapter controls cache and source trace",
            "recommended_scope": "TRUSTED_REUSE_CANDIDATE",
        },
        {
            "architecture_option": "C_NEW_KLAYOUT_PRIMITIVE_GENERATOR",
            "technology_correctness": "Possible but not yet proven",
            "device_geometry_support": "Would require fresh implementation",
            "contact_via_support": "Would require fresh implementation",
            "well_implant_support": "Would require fresh implementation",
            "parameterized_width": True,
            "parameterized_length": True,
            "pin_generation": True,
            "power_rail_generation": True,
            "hierarchy": "Flexible",
            "deterministic_naming": "Can be enforced",
            "drc_history": "None in this project",
            "integration_effort": "High",
            "licensing_provenance": "Local",
            "maintenance": "High",
            "risk": "Highest implementation risk",
            "recommended_scope": "FALLBACK_ONLY",
        },
    ]
    decision = "OPENRAM_FREEPDK45_DEVICE_CONTACT_ADAPTER"
    reason = (
        "OpenRAM already provides FreePDK45-backed transistor, contact, and inverter generators. "
        "The safest next step is a thin adapter that locks naming, source trace, and OpenYield-specific parameter contracts "
        "instead of drawing new proxy geometry."
    )
    implementation_ready = (
        trusted_device_generator_found
        and trusted_gate_generator_found
        and contact_via_generator_found
        and well_implant_generation_supported
        and parameterized_width_supported
        and parameterized_length_supported
        and openram_generator_can_be_called_outside_openram
    )
    return {
        "comparison_rows": rows,
        "comparison_fields": COMPARISON_FIELDS,
        "generator_architecture_decision": decision,
        "generator_architecture_decision_reason": reason,
        "generator_adapter_required": True,
        "generator_implementation_ready": implementation_ready,
    }
