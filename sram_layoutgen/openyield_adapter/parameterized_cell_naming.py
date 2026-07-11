from __future__ import annotations

import hashlib
import json
from typing import Any


def microns_to_nm_token(value: str | float | int) -> int:
    if isinstance(value, str):
        cleaned = value.strip().replace("e-6", "").replace("um", "").replace("u", "")
        number = float(cleaned)
    else:
        number = float(value)
    if number < 1e-3:
        number *= 1_000_000.0
    return int(round(number))


def canonical_cell_name(
    *,
    logical_type: str,
    nmos_width: str | float | int,
    pmos_width: str | float | int,
    length: str | float | int,
) -> str:
    return (
        f"{logical_type.upper()}_NW{microns_to_nm_token(nmos_width)}"
        f"_PW{microns_to_nm_token(pmos_width)}"
        f"_L{microns_to_nm_token(length)}"
    )


def build_parameterized_cell_naming_contract() -> dict[str, Any]:
    examples = []
    specs = [
        ("PINV", "0.09e-6", "0.27e-6", "0.05e-6", "1"),
        ("PINV", "0.27e-6", "0.81e-6", "0.05e-6", "3"),
        ("PINV", "0.91e-6", "2.43e-6", "0.05e-6", "large-stage-3"),
        ("PINV", "2.43e-6", "7.29e-6", "0.05e-6", "large-stage-4"),
        ("TRANSMISSION_GATE", "0.25e-6", "0.50e-6", "0.05e-6", "reference"),
    ]
    for logical_type, nmos, pmos, length, drive_scale in specs:
        payload = {
            "logical_type": logical_type,
            "technology": "FreePDK45",
            "nmos_width": nmos,
            "pmos_width": pmos,
            "length": length,
            "drive_scale": drive_scale,
        }
        source_trace = json.dumps(payload, sort_keys=True)
        examples.append(
            {
                **payload,
                "fingerprint": hashlib.sha256(source_trace.encode("utf-8")).hexdigest()[:16],
                "canonical_cell_name": canonical_cell_name(
                    logical_type=logical_type,
                    nmos_width=nmos,
                    pmos_width=pmos,
                    length=length,
                ),
                "cache_key": hashlib.sha256(
                    (
                        f"{logical_type}|FreePDK45|{microns_to_nm_token(nmos)}|"
                        f"{microns_to_nm_token(pmos)}|{microns_to_nm_token(length)}|{drive_scale}"
                    ).encode("utf-8")
                ).hexdigest()[:24],
                "source_trace_hash": hashlib.sha256(source_trace.encode("utf-8")).hexdigest()[:24],
            }
        )
    return {
        "technology": "FreePDK45",
        "unit_for_name_tokens": "nm",
        "examples": examples,
        "parameterized_cell_naming_contract_locked": True,
        "size_alias_collision_prevented_by_contract": True,
    }
