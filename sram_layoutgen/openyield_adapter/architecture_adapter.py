"""Architecture-level adapters for OpenYield module contracts.

These adapters describe semantic translations that cannot be represented as a
simple one-to-one physical pin map.  They are intentionally read-only metadata:
placement and routing code must opt in explicitly before using them.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


ADAPT_DIRECT = "direct_physical_pin"
ADAPT_DROPPED_COMPLEMENT = "dropped_complementary_output"
ADAPT_UNSUPPORTED_PHYSICAL = "unsupported_physical_pin"


@dataclass(frozen=True)
class PinAdaptation:
    openyield_pin: str
    local_pin: str | None
    canonical_signal: str
    adaptation_type: str
    required: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ModuleArchitectureAdapter:
    openyield_module: str
    local_macro: str
    role: str
    pin_adaptations: tuple[PinAdaptation, ...]
    unsupported_pins: tuple[str, ...] = ()
    generated_nets: dict[str, str] = field(default_factory=dict)
    requires_netlist_rewrite: bool = False
    requires_layout_pin: bool = False
    safe_for_physical_mapping: bool = False
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["pin_adaptations"] = [item.to_dict() for item in self.pin_adaptations]
        return data


def build_senseamp_architecture_adapter(qb_required_downstream: bool) -> ModuleArchitectureAdapter:
    """Build the current OpenYield SENSEAMP to local sense_amp adapter.

    The local FreePDK45/OpenRAM-style sense_amp hardcell exposes one read-data
    output, `dout`.  OpenYield's behavioral subcircuit exposes both `Q` and
    `QB`.  `QB` is safe to drop only when downstream physical readout uses `Q`
    and treats `QB` as observation-only.
    """

    if qb_required_downstream:
        strategy_note = (
            "OpenYield QB is consumed by downstream logic, so a generated dout_b "
            "path or a dual-output sense_amp hardcell is required before physical mapping.",
        )
        return ModuleArchitectureAdapter(
            openyield_module="SENSEAMP",
            local_macro="sense_amp",
            role="sense_amp",
            pin_adaptations=_senseamp_pin_adaptations(qb_required_downstream=True),
            unsupported_pins=("QB",),
            generated_nets={"QB": "dout_b_required_unimplemented"},
            requires_netlist_rewrite=True,
            requires_layout_pin=True,
            safe_for_physical_mapping=False,
            notes=strategy_note,
        )

    return ModuleArchitectureAdapter(
        openyield_module="SENSEAMP",
        local_macro="sense_amp",
        role="sense_amp",
        pin_adaptations=_senseamp_pin_adaptations(qb_required_downstream=False),
        unsupported_pins=("QB",),
        generated_nets={"QB": "dropped_observation_only_complement"},
        requires_netlist_rewrite=True,
        requires_layout_pin=False,
        safe_for_physical_mapping=True,
        notes=(
            "Local sense_amp is a single-ended output hardcell.",
            "OpenYield QB must not be forced onto a non-existent local GDS pin.",
            "The current adapter supports the single-ended Q -> dout readout path.",
            "If later logic consumes QB, add an inverter/differential-output adapter or a dual-output hardcell.",
        ),
    )


def recommended_senseamp_strategy(qb_required_downstream: bool) -> str:
    if qb_required_downstream:
        return "requires_generated_dout_b_or_dual_output_senseamp"
    return "single_ended_q_to_dout"


def _senseamp_pin_adaptations(qb_required_downstream: bool) -> tuple[PinAdaptation, ...]:
    qb_type = ADAPT_UNSUPPORTED_PHYSICAL if qb_required_downstream else ADAPT_DROPPED_COMPLEMENT
    qb_notes = (
        "Local sense_amp has no proven dout_b/QB physical pin.",
        "Do not add a fake layout pin.",
    )
    if qb_required_downstream:
        qb_notes += ("Downstream logic requires QB, so physical mapping is blocked.",)
    else:
        qb_notes += ("QB is treated as observation-only for the current physical readout path.",)
    return (
        PinAdaptation("VDD", "vdd", "vdd", ADAPT_DIRECT, True),
        PinAdaptation("VSS", "gnd", "gnd", ADAPT_DIRECT, True),
        PinAdaptation("EN", "en", "sense_enable", ADAPT_DIRECT, True),
        PinAdaptation("IN", "bl", "bl", ADAPT_DIRECT, True),
        PinAdaptation("INB", "br", "br", ADAPT_DIRECT, True),
        PinAdaptation("Q", "dout", "dout", ADAPT_DIRECT, True),
        PinAdaptation("QB", None, "dout_b", qb_type, False, qb_notes),
    )


def build_senseamp_m5_net_bindings(qb_required_downstream: bool = False) -> list[dict[str, str]]:
    strategy = recommended_senseamp_strategy(qb_required_downstream)
    rows = [
        {"openyield_net": "SA_IN[*]", "openyield_pin": "IN", "local_pin": "bl", "physical_role": "column_path", "strategy": strategy},
        {"openyield_net": "SA_INB[*]", "openyield_pin": "INB", "local_pin": "br", "physical_role": "column_path", "strategy": strategy},
        {"openyield_net": "s_en", "openyield_pin": "EN", "local_pin": "en", "physical_role": "control", "strategy": strategy},
        {"openyield_net": "SA_Q[*]", "openyield_pin": "Q", "local_pin": "dout", "physical_role": "read_data", "strategy": strategy},
        {"openyield_net": "VDD", "openyield_pin": "VDD", "local_pin": "vdd", "physical_role": "power", "strategy": strategy},
        {"openyield_net": "VSS", "openyield_pin": "VSS", "local_pin": "gnd", "physical_role": "power", "strategy": strategy},
    ]
    if qb_required_downstream:
        rows.append({"openyield_net": "SA_QB[*]", "openyield_pin": "QB", "local_pin": "dout_b_required_unimplemented", "physical_role": "read_data", "strategy": strategy})
    return rows
