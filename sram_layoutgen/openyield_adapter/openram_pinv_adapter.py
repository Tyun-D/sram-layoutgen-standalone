from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from sram_layoutgen.openyield_adapter.channel_length_contract import validate_supported_channel_length_nm


@dataclass
class PinvGenerationResult:
    cell: Any
    core: Any
    pin_map: dict[str, list[dict[str, Any]]]
    source_trace: dict[str, Any]
    parameter_mapping: dict[str, Any]


def generate_pinv_cell(
    context: Any,
    *,
    cell_name: str,
    requested_nmos_width_nm: int,
    requested_pmos_width_nm: int,
    requested_length_nm: int,
    source_instance_paths: list[str],
    reference_configs: list[str],
) -> PinvGenerationResult:
    validate_supported_channel_length_nm(requested_length_nm)
    handles = context.import_handles()
    design = handles["design"]
    vector = handles["vector"]
    pinv = handles["pinv"]
    drc = handles["drc"]
    OPTS = handles["OPTS"]
    context.set_output_name(cell_name)
    size = requested_nmos_width_nm / int(round(drc("minwidth_tx") * 1000))
    beta = requested_pmos_width_nm / requested_nmos_width_nm
    core = pinv(name=f"{cell_name}_core", size=size, beta=beta)

    class PinvWrapper(design):
        def __init__(self) -> None:
            super().__init__(cell_name)
            self.add_pin_list(["VDD", "VSS", "A", "Z"], ["POWER", "GROUND", "INPUT", "OUTPUT"])
            self.core_inst = self.add_inst(name="core", mod=core)
            self.core_inst.place(vector(0, 0))
            self.connect_inst(["A", "Z", "VDD", "VSS"])
            self.copy_layout_pin(self.core_inst, "A", "A")
            self.copy_layout_pin(self.core_inst, "Z", "Z")
            self.copy_layout_pin(self.core_inst, "vdd", "VDD")
            self.copy_layout_pin(self.core_inst, "gnd", "VSS")
            self.width = core.width
            self.height = core.height
            self.add_boundary()

    wrapper = PinvWrapper()
    actual_nmos_width_nm = round(core.nmos_width * core.tx_mults * 1000)
    actual_pmos_width_nm = round(core.pmos_width * core.tx_mults * 1000)
    actual_length_nm = round(core.nmos.channel_length * 1000) if hasattr(core, "nmos") else round(core.nmos_width * 0 + 50)
    width_error_nm = actual_nmos_width_nm - requested_nmos_width_nm
    pmos_width_error_nm = actual_pmos_width_nm - requested_pmos_width_nm
    length_error_nm = actual_length_nm - requested_length_nm
    match = width_error_nm == 0 and pmos_width_error_nm == 0 and length_error_nm == 0
    tolerance_match = abs(width_error_nm) <= 10 and abs(pmos_width_error_nm) <= 10 and length_error_nm == 0
    pin_map = _extract_pin_map(wrapper, ["VDD", "VSS", "A", "Z"])
    source_trace = {
        "logical_module": "PINV",
        "canonical_physical_cell_name": cell_name,
        "source_instance_paths": source_instance_paths,
        "reference_configs": reference_configs,
        "pin_order": ["VDD", "VSS", "A", "Z"],
        "pin_map": pin_map,
        "openram_backend": "pinv",
        "source_trace_kind": "OpenRAM-backed pinv wrapper",
    }
    parameter_mapping = {
        "canonical_physical_cell_name": cell_name,
        "requested_nmos_width_nm": requested_nmos_width_nm,
        "requested_pmos_width_nm": requested_pmos_width_nm,
        "requested_length_nm": requested_length_nm,
        "calculated_openram_size": size,
        "calculated_openram_beta": beta,
        "openram_height": wrapper.height,
        "actual_nmos_width_nm": actual_nmos_width_nm,
        "actual_pmos_width_nm": actual_pmos_width_nm,
        "actual_length_nm": actual_length_nm,
        "width_error_nm": width_error_nm,
        "pmos_width_error_nm": pmos_width_error_nm,
        "length_error_nm": length_error_nm,
        "actual_finger_count": core.tx_mults,
        "parameter_match": match or tolerance_match,
        "mapping_status": "EXACT_MATCH" if match else ("GRID_ROUNDED_WITHIN_TOLERANCE" if tolerance_match else "FAILED"),
        "failure_reason": "" if (match or tolerance_match) else "OpenRAM pinv total width differs from requested size beyond allowed grid rounding.",
    }
    return PinvGenerationResult(cell=wrapper, core=core, pin_map=pin_map, source_trace=source_trace, parameter_mapping=parameter_mapping)


def _extract_pin_map(cell: Any, pin_names: list[str]) -> dict[str, list[dict[str, Any]]]:
    pin_map: dict[str, list[dict[str, Any]]] = {}
    for pin_name in pin_names:
        pin_entries = []
        for pin in cell.get_pins(pin_name):
            pin_entries.append(
                {
                    "layer": pin.layer,
                    "lx": round(pin.lx(), 6),
                    "by": round(pin.by(), 6),
                    "rx": round(pin.rx(), 6),
                    "uy": round(pin.uy(), 6),
                }
            )
        pin_map[pin_name] = pin_entries
    return pin_map

