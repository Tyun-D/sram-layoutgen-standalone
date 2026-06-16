"""Canonical contracts for OpenYield-derived SRAM modules.

These contracts are intentionally independent of OpenYield/PySpice runtime
imports.  They describe what the layout generator needs to know before a
netlist-derived module can be mapped onto physical GDS macros.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class PinContract:
    original_name: str
    canonical_name: str
    role: str
    direction: str | None = None
    polarity: str | None = None
    aliases: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModuleContract:
    source: str
    original_module_name: str
    canonical_module_name: str
    role: str
    pins: tuple[PinContract, ...] = ()
    power_pins: dict[str, str] = field(default_factory=dict)
    equivalent_openram_roles: tuple[str, ...] = ()
    gds_macro_candidates: tuple[str, ...] = ()
    requires_physical_implementation: bool = True
    notes: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()
    class_name: str | None = None
    source_file: str | None = None
    mos_call_count: int = 0
    self_instance_call_count: int = 0
    circuit_instance_call_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["pins"] = [pin.to_dict() for pin in self.pins]
        return data


@dataclass(frozen=True)
class ParsedPySpiceModule:
    source_file: str
    class_name: str
    original_module_name: str
    nodes: tuple[str, ...] = ()
    node_expr: str = ""
    name_expr: str = ""
    role_hint: str = "unknown"
    mos_call_count: int = 0
    self_instance_call_count: int = 0
    circuit_instance_call_count: int = 0
    subcircuit_call_count: int = 0
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
