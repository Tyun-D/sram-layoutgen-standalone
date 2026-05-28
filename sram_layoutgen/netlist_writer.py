"""Structural SPICE writer for the standalone SRAM research macro."""

from __future__ import annotations

from pathlib import Path
from typing import List

from .geometry import LayoutDB
from .tech import Tech


class NetlistWriter:
    def __init__(self, tech: Tech) -> None:
        self.tech = tech

    def write(self, layout: LayoutDB, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        word_size = int(layout.metadata["word_size"])
        num_words = int(layout.metadata["num_words"])
        wpr = int(layout.metadata["words_per_row"])
        rows = int(layout.metadata["num_rows"])
        cols = int(layout.metadata["num_cols"])
        addr_bits = int(layout.metadata.get("addr_bits", max(1, (num_words - 1).bit_length())))
        row_addr_bits = int(layout.metadata.get("row_addr_bits", max(1, (rows - 1).bit_length())))
        col_addr_bits = int(layout.metadata.get("col_addr_bits", max(0, (wpr - 1).bit_length())))

        ports = ["clk", "csb", "web"]
        ports.extend(f"addr[{i}]" for i in range(addr_bits))
        ports.extend(f"din[{i}]" for i in range(word_size))
        ports.extend(f"dout[{i}]" for i in range(word_size))
        ports.extend(["vdd", "gnd"])

        lines: List[str] = [
            f"* Structural research netlist for {layout.top_name}",
            "* This is generated without OpenRAM compiler code.",
            "* Row decoder/control glue use replacement macro subckt contracts.",
            "",
        ]
        for cell_name in sorted(self._used_cells(layout)):
            if cell_name not in self.tech.cells:
                continue
            cell = self.tech.cell(cell_name)
            if cell.spice_path:
                lines.append(f'.include "{_spice_path(cell.spice_path)}"')
        lines.extend(["", *_generated_stdcell_subckts(), "", f".SUBCKT {layout.top_name} {' '.join(ports)}"])

        for r in range(rows):
            for c in range(cols):
                lines.append(f"Xbit_r{r}_c{c} bl[{c}] br[{c}] wl[{r}] vdd gnd cell_1rw")
            lines.append(f"Xdummy_l_r{r} dummy_bl_l dummy_br_l wl[{r}] vdd gnd dummy_cell_1rw")
            lines.append(f"Xdummy_r_r{r} dummy_bl_r dummy_br_r wl[{r}] vdd gnd dummy_cell_1rw")
            lines.append(f"Xreplica_r{r} rbl rbr replica_wl[{r}] vdd gnd replica_cell_1rw")

        for bit in range(col_addr_bits):
            lines.append(f"Xcoladdr_inv_{bit} addr[{bit}] col_addr_b[{bit}] vdd gnd gen_inv")
        for bit in range(row_addr_bits):
            lines.append(f"Xrowaddr_inv_{bit} addr[{col_addr_bits + bit}] row_addr_b[{bit}] vdd gnd gen_inv")
        if col_addr_bits == 0:
            lines.append("Xcolsel_0 csb col_sel[0] vdd gnd gen_inv")
        elif col_addr_bits == 1:
            lines.append("Xcolsel_0 col_addr_b[0] csb col_sel[0] vdd gnd gen_nand2")
            lines.append("Xcolsel_1 addr[0] csb col_sel[1] vdd gnd gen_nand2")
        else:
            for sel in range(wpr):
                a0 = f"addr[0]" if sel & 1 else "col_addr_b[0]"
                a1 = f"addr[1]" if sel & 2 else "col_addr_b[1]"
                lines.append(f"Xcolsel_{sel} {a0} {a1} col_sel[{sel}] vdd gnd gen_nand2")

        for c in range(cols):
            lines.append(f"Xprecharge_{c} bl[{c}] br[{c}] pchg_en vdd gnd gen_precharge")
            data_index = min(word_size - 1, c // max(wpr, 1))
            lines.append(f"Xcolmux_{c} bl[{c}] br[{c}] mux_d[{data_index}] col_sel[{c % max(wpr, 1)}] vdd gnd gen_col_mux")
        lines.append("Xreplica_precharge rbl rbr pchg_en vdd gnd gen_precharge")

        for i in range(word_size):
            c = i * wpr
            lines.append(f"Xsense_{i} bl[{c}] br[{c}] dout_int[{i}] sense_en vdd gnd sense_amp")
            lines.append(f"Xwrite_{i} din[{i}] bl[{c}] br[{c}] write_en vdd gnd write_driver")
            lines.append(f"Xtri_{i} dout_int[{i}] dout[{i}] tri_en tri_en_bar vdd gnd tri_gate")

        for i in range(word_size):
            lines.append(f"Xdff_data_{i} din[{i}] din_q[{i}] clk vdd gnd dff")

        control_dffs = sum(
            array.columns * array.rows
            for array in layout.cell_arrays
            if array.cell == "dff" and array.role == "control_logic"
        )
        for i in range(control_dffs):
            lines.append(f"Xdff_ctrl_{i} ctrl_d[{i}] ctrl_q[{i}] clk vdd gnd dff")

        delay_count = sum(1 for instance in layout.instances if instance.role == "delay_chain")
        last = "clk"
        for i in range(delay_count):
            out = f"delay[{i}]"
            lines.append(f"Xdelay_{i} {last} {out} vdd gnd gen_delay_inv")
            last = out

        for r in range(rows):
            terms = []
            for bit in range(row_addr_bits):
                terms.append(f"addr[{col_addr_bits + bit}]" if r & (1 << bit) else f"row_addr_b[{bit}]")
            while len(terms) < 4:
                terms.append("vdd")
            lines.append(f"Xdec_nand_{r} {terms[0]} {terms[1]} dec_n[{r}] vdd gnd gen_nand2")
            lines.append(f"Xwl_driver_{r} dec_n[{r}] wl[{r}] vdd gnd gen_wl_driver")

        for i, inst in enumerate(instance for instance in layout.instances if instance.role == "control_glue"):
            if inst.cell == "gen_inv":
                lines.append(f"Xctrl_inv_{i} ctrl_in[{i}] ctrl_out[{i}] vdd gnd gen_inv")
            elif inst.cell == "gen_nand2":
                lines.append(f"Xctrl_nand_{i} ctrl_in[{i}] clk ctrl_out[{i}] vdd gnd gen_nand2")

        lines.extend(
            [
                "* NOTE: generated decoder/control logic is structural and intended for layout integration testing.",
                "* NOTE: matching physical GDS for gen_* macros is a replacement-library task.",
                ".ENDS",
                "",
            ]
        )
        path.write_text("\n".join(lines), encoding="utf-8")

    @staticmethod
    def _used_cells(layout: LayoutDB) -> set[str]:
        return {array.cell for array in layout.cell_arrays} | {instance.cell for instance in layout.instances}


def _spice_path(path: str) -> str:
    """Use slash-separated paths so SPICE parsers do not treat backslashes as escapes."""

    return Path(path).as_posix()


def _generated_stdcell_subckts() -> list[str]:
    return [
        ".SUBCKT gen_inv A Z vdd gnd",
        "Mp0 Z A vdd vdd PMOS_VTG W=360n L=50n",
        "Mn0 Z A gnd gnd NMOS_VTG W=180n L=50n",
        ".ENDS gen_inv",
        "",
        ".SUBCKT gen_nand2 A B Z vdd gnd",
        "Mp0 Z A vdd vdd PMOS_VTG W=360n L=50n",
        "Mp1 Z B vdd vdd PMOS_VTG W=360n L=50n",
        "Mn0 Z A n1 gnd NMOS_VTG W=180n L=50n",
        "Mn1 n1 B gnd gnd NMOS_VTG W=180n L=50n",
        ".ENDS gen_nand2",
        "",
        ".SUBCKT gen_nand4 A B C D Z vdd gnd",
        "Mp0 Z A vdd vdd PMOS_VTG W=360n L=50n",
        "Mp1 Z B vdd vdd PMOS_VTG W=360n L=50n",
        "Mp2 Z C vdd vdd PMOS_VTG W=360n L=50n",
        "Mp3 Z D vdd vdd PMOS_VTG W=360n L=50n",
        "Mn0 Z A n1 gnd NMOS_VTG W=180n L=50n",
        "Mn1 n1 B n2 gnd NMOS_VTG W=180n L=50n",
        "Mn2 n2 C n3 gnd NMOS_VTG W=180n L=50n",
        "Mn3 n3 D gnd gnd NMOS_VTG W=180n L=50n",
        ".ENDS gen_nand4",
        "",
        ".SUBCKT gen_nor2 A B Z vdd gnd",
        "Mp0 p1 A vdd vdd PMOS_VTG W=360n L=50n",
        "Mp1 Z B p1 vdd PMOS_VTG W=360n L=50n",
        "Mn0 Z A gnd gnd NMOS_VTG W=180n L=50n",
        "Mn1 Z B gnd gnd NMOS_VTG W=180n L=50n",
        ".ENDS gen_nor2",
        "",
        ".SUBCKT gen_wl_driver A Z vdd gnd",
        "Xinv0 A Z vdd gnd gen_inv",
        ".ENDS gen_wl_driver",
        "",
        ".SUBCKT gen_precharge BL BR EN vdd gnd",
        "Mp_bl BL EN vdd vdd PMOS_VTG W=720n L=50n",
        "Mp_br BR EN vdd vdd PMOS_VTG W=720n L=50n",
        "Mp_eq BL EN BR vdd PMOS_VTG W=360n L=50n",
        ".ENDS gen_precharge",
        "",
        ".SUBCKT gen_col_mux BL BR OUT SEL vdd gnd",
        "Mn_bl OUT SEL BL gnd NMOS_VTG W=270n L=50n",
        "Mn_br OUT SEL BR gnd NMOS_VTG W=270n L=50n",
        ".ENDS gen_col_mux",
        "",
        ".SUBCKT gen_delay_inv A Z vdd gnd",
        "Xinv0 A Z vdd gnd gen_inv",
        ".ENDS gen_delay_inv",
        "",
        ".SUBCKT gen_well_tap vdd gnd",
        "* physical tap cell placeholder for well/substrate contacts",
        ".ENDS gen_well_tap",
    ]
