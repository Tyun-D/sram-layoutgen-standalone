from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sram_layoutgen.openyield_adapter.channel_length_contract import validate_supported_channel_length_nm


@dataclass
class Pnand2GenerationResult:
    cell: Any
    core: Any
    pin_map: dict[str, list[dict[str, Any]]]
    source_trace: dict[str, Any]
    parameter_mapping: dict[str, Any]
    device_layout: list[dict[str, Any]]


def _pin_bbox(pin: Any) -> dict[str, float]:
    return {
        "lx": round(pin.lx(), 6),
        "by": round(pin.by(), 6),
        "rx": round(pin.rx(), 6),
        "uy": round(pin.uy(), 6),
    }


def _extract_pin_map(cell: Any, pin_names: list[str]) -> dict[str, list[dict[str, Any]]]:
    pin_map: dict[str, list[dict[str, Any]]] = {}
    for pin_name in pin_names:
        pin_map[pin_name] = [
            {
                "layer": pin.layer,
                "lx": round(pin.lx(), 6),
                "by": round(pin.by(), 6),
                "rx": round(pin.rx(), 6),
                "uy": round(pin.uy(), 6),
            }
            for pin in cell.get_pins(pin_name)
        ]
    return pin_map


def generate_pnand2_cell(
    context: Any,
    *,
    cell_name: str,
    requested_nmos_width_nm: int,
    requested_pmos_width_nm: int,
    requested_length_nm: int,
    source_instance_paths: list[str],
    reference_configs: list[str],
) -> Pnand2GenerationResult:
    validate_supported_channel_length_nm(requested_length_nm)
    handles = context.import_handles()
    design = handles["design"]
    vector = handles["vector"]
    factory = handles["factory"]
    context.set_output_name(cell_name)
    core = factory.create(module_type="pnand2", size=1)

    class Pnand2Wrapper(design):
        def __init__(self) -> None:
            super().__init__(cell_name)
            self.add_pin_list(["VDD", "VSS", "A", "B", "Z"], ["POWER", "GROUND", "INPUT", "INPUT", "OUTPUT"])
            self.core_inst = self.add_inst(name="core", mod=core)
            self.core_inst.place(vector(0, 0))
            self.connect_inst(["A", "B", "Z", "VDD", "VSS"])
            self.copy_layout_pin(self.core_inst, "A", "A")
            self.copy_layout_pin(self.core_inst, "B", "B")
            self.copy_layout_pin(self.core_inst, "Z", "Z")
            self.copy_layout_pin(self.core_inst, "vdd", "VDD")
            self.copy_layout_pin(self.core_inst, "gnd", "VSS")
            self.width = core.width
            self.height = core.height
            self.add_boundary()

    wrapper = Pnand2Wrapper()
    actual_nmos_width_nm = round(float(core.nmos_width) * 1000)
    actual_pmos_width_nm = round(float(core.pmos_width) * 1000)
    actual_length_nm = round(float(core.nmos_left.channel_length) * 1000)
    width_error_nm = actual_nmos_width_nm - requested_nmos_width_nm
    pmos_width_error_nm = actual_pmos_width_nm - requested_pmos_width_nm
    length_error_nm = actual_length_nm - requested_length_nm
    match = width_error_nm == 0 and pmos_width_error_nm == 0 and length_error_nm == 0
    tolerance_match = abs(width_error_nm) <= 10 and abs(pmos_width_error_nm) <= 10 and length_error_nm == 0
    pin_map = _extract_pin_map(wrapper, ["VDD", "VSS", "A", "B", "Z"])
    device_layout = [
        {
            "device_name": "P1",
            "device_model": "PMOS_VTG",
            "terminal_bboxes": {
                "D": _pin_bbox(core.pmos1_inst.get_pin("D")),
                "G": _pin_bbox(core.pmos1_inst.get_pin("G")),
                "S": _pin_bbox(core.pmos1_inst.get_pin("S")),
            },
            "gate_net": "A",
            "bulk_net": "VDD",
        },
        {
            "device_name": "P2",
            "device_model": "PMOS_VTG",
            "terminal_bboxes": {
                "D": _pin_bbox(core.pmos2_inst.get_pin("D")),
                "G": _pin_bbox(core.pmos2_inst.get_pin("G")),
                "S": _pin_bbox(core.pmos2_inst.get_pin("S")),
            },
            "gate_net": "B",
            "bulk_net": "VDD",
        },
        {
            "device_name": "N1",
            "device_model": "NMOS_VTG",
            "terminal_bboxes": {
                "D": _pin_bbox(core.nmos1_inst.get_pin("D")),
                "G": _pin_bbox(core.nmos1_inst.get_pin("G")),
                "S": _pin_bbox(core.nmos1_inst.get_pin("S")),
            },
            "gate_net": "B",
            "bulk_net": "VSS",
        },
        {
            "device_name": "N2",
            "device_model": "NMOS_VTG",
            "terminal_bboxes": {
                "D": _pin_bbox(core.nmos2_inst.get_pin("D")),
                "G": _pin_bbox(core.nmos2_inst.get_pin("G")),
                "S": _pin_bbox(core.nmos2_inst.get_pin("S")),
            },
            "gate_net": "A",
            "bulk_net": "VSS",
        },
    ]
    source_trace = {
        "logical_module": "PNAND2",
        "canonical_physical_cell_name": cell_name,
        "source_instance_paths": source_instance_paths,
        "reference_configs": reference_configs,
        "pin_order": ["VDD", "VSS", "A", "B", "Z"],
        "pin_map": pin_map,
        "openram_backend": "native_pnand2_wrapper",
        "openram_core_name": core.name,
    }
    parameter_mapping = {
        "canonical_physical_cell_name": cell_name,
        "requested_nmos_width_nm": requested_nmos_width_nm,
        "requested_pmos_width_nm": requested_pmos_width_nm,
        "requested_length_nm": requested_length_nm,
        "actual_nmos_width_nm": actual_nmos_width_nm,
        "actual_pmos_width_nm": actual_pmos_width_nm,
        "actual_length_nm": actual_length_nm,
        "width_error_nm": width_error_nm,
        "pmos_width_error_nm": pmos_width_error_nm,
        "length_error_nm": length_error_nm,
        "actual_finger_count": int(core.tx_mults),
        "parameter_match": match or tolerance_match,
        "mapping_status": "EXACT_MATCH" if match else ("GRID_ROUNDED_WITHIN_TOLERANCE" if tolerance_match else "FAILED"),
        "failure_reason": "" if (match or tolerance_match) else "OpenRAM pnand2 total width differs from requested size beyond allowed tolerance.",
        "openram_core_width_um": round(float(core.width), 6),
        "openram_core_height_um": round(float(core.height), 6),
    }
    return Pnand2GenerationResult(
        cell=wrapper,
        core=core,
        pin_map=pin_map,
        source_trace=source_trace,
        parameter_mapping=parameter_mapping,
        device_layout=device_layout,
    )

