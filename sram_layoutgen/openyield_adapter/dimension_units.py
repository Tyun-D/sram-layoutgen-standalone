from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Literal


InputUnit = Literal["METER", "MICROMETER", "NANOMETER"]

_UNIT_TO_NM = {
    "METER": Decimal("1000000000"),
    "MICROMETER": Decimal("1000"),
    "NANOMETER": Decimal("1"),
}


def normalize_dimension_nm(value: str | int | float | Decimal, input_unit: InputUnit) -> int:
    if input_unit not in _UNIT_TO_NM:
        raise ValueError(f"unsupported input_unit: {input_unit}")
    decimal_value = value if isinstance(value, Decimal) else Decimal(str(value))
    normalized = (decimal_value * _UNIT_TO_NM[input_unit]).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(normalized)


def ensure_nonzero_nm(value_nm: int, label: str) -> int:
    if value_nm <= 0:
        raise ValueError(f"{label} must be > 0 nm, got {value_nm}")
    return value_nm
