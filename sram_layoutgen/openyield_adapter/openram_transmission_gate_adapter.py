from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sram_layoutgen.openyield_adapter.channel_length_contract import validate_supported_channel_length_nm


@dataclass
class TransmissionGateGenerationResult:
    cell: Any
    core: Any
    pin_map: dict[str, list[dict[str, Any]]]
    source_trace: dict[str, Any]
    connectivity_contract: dict[str, Any]


def generate_transmission_gate_cell(
    context: Any,
    *,
    cell_name: str,
    nmos_width_nm: int,
    pmos_width_nm: int,
    channel_length_nm: int,
    source_instance_paths: list[str],
    reference_configs: list[str],
) -> TransmissionGateGenerationResult:
    validate_supported_channel_length_nm(channel_length_nm)
    handles = context.import_handles()
    design = handles["design"]
    vector = handles["vector"]
    pgate = handles["pgate"]
    factory = handles["factory"]
    drc = handles["drc"]
    context.set_output_name(cell_name)

    class TransmissionGateCore(pgate):
        def __init__(self) -> None:
            self.nmos_width_requested_um = nmos_width_nm / 1000
            self.pmos_width_requested_um = pmos_width_nm / 1000
            super().__init__(f"{cell_name}_core", height=None, add_wells=True)

        def create_netlist(self) -> None:
            self.add_pin_list(["in", "out", "ctr_p", "ctr_n", "vdd", "gnd"], ["INOUT", "INOUT", "INPUT", "INPUT", "POWER", "GROUND"])
            self.nmos = factory.create(module_type="ptx", width=self.nmos_width_requested_um, mults=1, tx_type="nmos", connect_poly=False)
            self.pmos = factory.create(module_type="ptx", width=self.pmos_width_requested_um, mults=1, tx_type="pmos", connect_poly=False)
            self.pmos_inst = self.add_inst(name="tg_pmos", mod=self.pmos)
            self.connect_inst(["out", "ctr_p", "in", "vdd"])
            self.nmos_inst = self.add_inst(name="tg_nmos", mod=self.nmos)
            self.connect_inst(["out", "ctr_n", "in", "gnd"])

        def create_layout(self) -> None:
            self.overlap_offset = self.pmos.get_pin("D").ll() - self.pmos.get_pin("S").ll()
            self.well_width = max(self.pmos.active_width, self.nmos.active_width) + self.nwell_enclose_active
            self.width = max(self.pmos.active_width, self.nmos.active_width) + 2 * self.nwell_enclose_active + self.active_space + self.contact_width
            self.route_supply_rails()
            pmos_yoff = self.height - self.pmos.active_height - self.top_bottom_space - 0.5 * self.active_contact.height
            nmos_yoff = self.top_bottom_space + 0.5 * self.active_contact.height
            self.pmos_pos = vector(self.pmos.active_offset.x, pmos_yoff)
            self.nmos_pos = vector(self.nmos.active_offset.x, nmos_yoff)
            self.pmos_inst.place(self.pmos_pos)
            self.nmos_inst.place(self.nmos_pos)
            self.add_nwell_contact(self.pmos, self.pmos_pos)
            self.add_pwell_contact(self.nmos, self.nmos_pos)
            self.determine_width()
            self.extend_wells()
            self._connect_terminal_pair("S", "in")
            self._connect_terminal_pair("D", "out")
            self._route_gate_pin(self.pmos_inst, "ctr_p", rail_name="vdd")
            self._route_gate_pin(self.nmos_inst, "ctr_n", rail_name="gnd")
            self.add_boundary()

        def _connect_terminal_pair(self, terminal: str, exported_name: str) -> None:
            p_pin = self.pmos_inst.get_pin(terminal)
            n_pin = self.nmos_inst.get_pin(terminal)
            llx = min(p_pin.lx(), n_pin.lx())
            by = n_pin.by()
            width = max(p_pin.rx(), n_pin.rx()) - llx
            height = p_pin.uy() - by
            self.add_layout_pin(text=exported_name, layer="m1", offset=vector(llx, by), width=width, height=height)

        def _route_gate_pin(self, inst: Any, exported_name: str, *, rail_name: str) -> None:
            gate_pin = inst.get_pin("G")
            gate_center_x = gate_pin.cx()
            if rail_name == "gnd":
                access_y = gate_pin.uy() + 0.5 * self.poly_contact.first_layer_height
            else:
                access_y = gate_pin.by() - 0.5 * self.poly_contact.first_layer_height
            access_x = self.width - 0.5 * self.poly_contact.first_layer_width
            via_center = vector(access_x, access_y)
            self.add_path("poly", [vector(gate_center_x, gate_pin.cy()), vector(gate_center_x, access_y), vector(access_x, access_y)])
            self.add_via_stack_center(offset=via_center, from_layer="poly", to_layer=self.route_layer, directions=("V", "H"))
            self.add_layout_pin(
                text=exported_name,
                layer=self.route_layer,
                offset=vector(via_center.x - 0.5 * self.poly_contact.second_layer_width, access_y - 0.5 * self.poly_contact.second_layer_height),
                width=self.poly_contact.second_layer_width,
                height=self.poly_contact.second_layer_height,
            )

    core = TransmissionGateCore()

    class TgWrapper(design):
        def __init__(self) -> None:
            super().__init__(cell_name)
            self.add_pin_list(["VDD", "VSS", "IN", "OUT", "CTR_P", "CTR_N"], ["POWER", "GROUND", "INOUT", "INOUT", "INPUT", "INPUT"])
            self.core_inst = self.add_inst(name="core", mod=core)
            self.core_inst.place(vector(0, 0))
            self.connect_inst(["IN", "OUT", "CTR_P", "CTR_N", "VDD", "VSS"])
            self.copy_layout_pin(self.core_inst, "in", "IN")
            self.copy_layout_pin(self.core_inst, "out", "OUT")
            self.copy_layout_pin(self.core_inst, "ctr_p", "CTR_P")
            self.copy_layout_pin(self.core_inst, "ctr_n", "CTR_N")
            self.copy_layout_pin(self.core_inst, "vdd", "VDD")
            self.copy_layout_pin(self.core_inst, "gnd", "VSS")
            self.width = core.width
            self.height = core.height
            self.add_boundary()

    wrapper = TgWrapper()
    pin_map = _extract_pin_map(wrapper, ["VDD", "VSS", "IN", "OUT", "CTR_P", "CTR_N"])
    connectivity_contract = {
        "cell_name": cell_name,
        "nmos_logical_device_count": 1,
        "pmos_logical_device_count": 1,
        "source_drain_mapping_policy": "PHYSICAL_LEFT_TERMINAL_TO_IN_AND_RIGHT_TERMINAL_TO_OUT_FOR_BOTH_DEVICES",
        "source_drain_swapped_for_symmetry": True,
        "nmos_gate_pin": "CTR_N",
        "pmos_gate_pin": "CTR_P",
        "shared_signal_pins": ["IN", "OUT"],
        "power_pins": ["VDD", "VSS"],
        "actual_nmos_width_nm": round(core.nmos.tx_width * 1000),
        "actual_pmos_width_nm": round(core.pmos.tx_width * 1000),
        "actual_length_nm": round(core.nmos.channel_length * 1000),
        "transmission_gate_parameter_match": round(core.nmos.tx_width * 1000) == nmos_width_nm and round(core.pmos.tx_width * 1000) == pmos_width_nm,
    }
    source_trace = {
        "logical_module": "TRANSMISSION_GATE",
        "canonical_physical_cell_name": cell_name,
        "source_instance_paths": source_instance_paths,
        "reference_configs": reference_configs,
        "pin_order": ["VDD", "VSS", "IN", "OUT", "CTR_P", "CTR_N"],
        "pin_map": pin_map,
        "openram_backend": "ptx+pgate composition",
    }
    return TransmissionGateGenerationResult(cell=wrapper, core=core, pin_map=pin_map, source_trace=source_trace, connectivity_contract=connectivity_contract)


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
