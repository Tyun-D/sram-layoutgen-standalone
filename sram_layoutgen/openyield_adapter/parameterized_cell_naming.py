from __future__ import annotations

import hashlib
import json
from typing import Any

from sram_layoutgen.openyield_adapter.dimension_units import ensure_nonzero_nm, normalize_dimension_nm


def canonical_cell_name(*, logical_type: str, nmos_width_nm: str | int, pmos_width_nm: str | int, length_nm: str | int) -> str:
    nw = ensure_nonzero_nm(int(nmos_width_nm), "nmos_width_nm")
    pw = ensure_nonzero_nm(int(pmos_width_nm), "pmos_width_nm")
    ln = ensure_nonzero_nm(int(length_nm), "length_nm")
    return (
        f"{logical_type.upper()}_NW{nw}"
        f"_PW{pw}"
        f"_L{ln}"
    )


def build_cache_key(
    *,
    technology: str,
    logical_type: str,
    nmos_width_nm: str | int,
    pmos_width_nm: str | int,
    channel_length_nm: str | int,
    finger_or_mult_policy: str,
    contact_policy: str,
    rail_policy: str,
    orientation_policy: str,
    source_netlist_role: str,
) -> str:
    # `source_netlist_role` is kept in the signature for call-site compatibility,
    # but physical cache identity is intentionally parameter-based. Source-role
    # provenance belongs in source_trace_hash, not in the reusable cell key.
    payload = {
        "technology": technology,
        "logical_type": logical_type,
        "nmos_width_nm": str(nmos_width_nm),
        "pmos_width_nm": str(pmos_width_nm),
        "channel_length_nm": str(channel_length_nm),
        "finger_or_mult_policy": finger_or_mult_policy,
        "contact_policy": contact_policy,
        "rail_policy": rail_policy,
        "orientation_policy": orientation_policy,
    }
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:24]


def build_corrected_parameterized_cell_naming_contract(variant_rows: list[dict[str, Any]]) -> dict[str, Any]:
    examples = []
    for row in variant_rows:
        payload = {
            "logical_type": "PINV",
            "technology": row["technology"],
            "nmos_width_nm": row["nmos_width_nm"],
            "pmos_width_nm": row["pmos_width_nm"],
            "channel_length_nm": row["channel_length_nm"],
            "finger_or_mult_policy": row["finger_or_mult_policy"],
            "contact_policy": row["contact_policy"],
            "rail_policy": row["rail_policy"],
            "orientation_policy": "fixed row orientation",
            "source_netlist_role": row["source_instance_path"],
            "cache_identity_excludes_source_netlist_role": True,
        }
        examples.append(
            {
                **payload,
                "canonical_physical_cell_name": row["canonical_physical_cell_name"],
                "cache_key": row["cache_key"],
                "source_trace_hash": row["source_trace_hash"],
            }
        )
    return {
        "technology": "FreePDK45",
        "unit_for_name_tokens": "nm",
        "examples": examples,
        "corrected_parameterized_cell_naming_contract_locked": True,
        "source_derived_variant_contract_locked": True,
        "size_alias_collision_prevented_by_corrected_contract": True,
    }


def build_legacy_m12c3_examples() -> list[dict[str, Any]]:
    specs = [
        ("PINV", "0.09e-6", "0.27e-6", "0.05e-6", "1"),
        ("PINV", "0.27e-6", "0.81e-6", "0.05e-6", "3"),
        ("PINV", "0.91e-6", "2.43e-6", "0.05e-6", "large-stage-3"),
        ("PINV", "2.43e-6", "7.29e-6", "0.05e-6", "large-stage-4"),
        ("TRANSMISSION_GATE", "0.25e-6", "0.50e-6", "0.05e-6", "reference"),
    ]
    rows = []
    for logical_type, nmos, pmos, length, drive_scale in specs:
        nmos_nm = normalize_dimension_nm(nmos, "METER")
        pmos_nm = normalize_dimension_nm(pmos, "METER")
        length_nm = normalize_dimension_nm(length, "METER")
        payload = {
            "logical_type": logical_type,
            "technology": "FreePDK45",
            "nmos_width": nmos,
            "pmos_width": pmos,
            "length": length,
            "drive_scale": drive_scale,
        }
        source_trace = json.dumps(payload, sort_keys=True)
        rows.append(
            {
                **payload,
                "fingerprint": hashlib.sha256(source_trace.encode("utf-8")).hexdigest()[:16],
                "canonical_cell_name": canonical_cell_name(
                    logical_type=logical_type,
                    nmos_width_nm=nmos_nm,
                    pmos_width_nm=pmos_nm,
                    length_nm=length_nm,
                ),
                "cache_key": hashlib.sha256(
                    (
                        f"{logical_type}|FreePDK45|{nmos_nm}|"
                        f"{pmos_nm}|{length_nm}|{drive_scale}"
                    ).encode("utf-8")
                ).hexdigest()[:24],
                "source_trace_hash": hashlib.sha256(source_trace.encode("utf-8")).hexdigest()[:24],
            }
        )
    return rows
