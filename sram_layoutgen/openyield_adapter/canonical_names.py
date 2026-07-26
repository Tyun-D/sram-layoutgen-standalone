"""Canonical naming rules for OpenYield/OpenRAM/layoutgen contracts."""

from __future__ import annotations

import re


POWER_ALIASES = {
    "VDD": "vdd",
    "vdd": "vdd",
    "VSS": "gnd",
    "GND": "gnd",
    "gnd": "gnd",
}

PIN_ALIASES = {
    **POWER_ALIASES,
    "BL": "bl",
    "BL0": "bl",
    "bl": "bl",
    "BLB": "br",
    "BLB0": "br",
    "BR": "br",
    "br": "br",
    "WL": "wl",
    "WL0": "wl",
    "wl": "wl",
    "EN": "en",
    "ENB": "enb",
    "CLK": "clk",
    "clk": "clk",
    "clk0": "clk",
    "web0": "web",
    "csb0": "csb",
    "pre": "precharge_enb",
    "PRE": "precharge_enb",
    "p_en_bar": "precharge_enb",
    "s_en": "sense_enable",
    "w_en": "write_enable",
    "wl_en": "wordline_enable",
    "DIN": "din",
    "Q": "dout",
    "OUT": "dout",
    "out": "dout",
    "QB": "dout_b",
}

MODULE_ALIASES = {
    "SRAM_6T_CELL": ("bitcell", "cell_1rw", "cell_6t"),
    "SRAM_10T_CELL": ("bitcell_10t",),
    "PRECHARGE": ("precharge", "precharge_array"),
    "WRITEDRIVER": ("write_driver", "write_driver_array"),
    "SENSEAMP": ("sense_amp", "sense_amp_array"),
    "DECODER3_8": ("decoder", "row_decoder"),
    "DECODER_CASCADE": ("decoder", "row_decoder"),
    "WORDLINEDRIVER": ("wl_driver", "wordline_driver"),
    "Dummy_CELL": ("dummy_cell", "dummy_cell_1rw"),
    "Replica_CELL": ("replica_cell", "replica_cell_1rw"),
    "TIME": ("control_logic", "time_generator"),
    "ADDR_DFF": ("control_dff", "addr_dff"),
    "DATA_DFF": ("data_dff",),
    "DFF": ("dff",),
    "delay_chain": ("delay_chain",),
    "wen_delay_chain": ("wen_delay_chain",),
}


def canonical_pin_name(name: str) -> str:
    if name in PIN_ALIASES:
        return PIN_ALIASES[name]
    if re.fullmatch(r"BL\{?i\}?|\bBL\d+\b", name):
        return "bl"
    if re.fullmatch(r"BLB\{?i\}?|\bBLB\d+\b|BR\d+", name):
        return "br"
    if re.fullmatch(r"WL\{?i\}?|WL\d+", name):
        return "wl"
    if re.fullmatch(r"A\{?i\}?|A\d+", name):
        return "addr"
    if re.fullmatch(r"A_dff\{?i\}?|A_dff\d+", name):
        return "addr_q"
    if re.fullmatch(r"DIN\{?i\}?|DIN\d+|din0\[\d+\]", name):
        return "din"
    if re.fullmatch(r"DIN_dff\{?i\}?|DIN_dff\d+", name):
        return "din_q"
    if re.fullmatch(r"dout0\[\d+\]", name):
        return "dout"
    low = name.lower()
    if low == "csb":
        return "csb"
    if low == "web":
        return "web"
    if low == "clk_buf":
        return "clk_buf"
    if low == "clk_bar":
        return "clk_bar"
    if low in {"pre_unbuf", "precharge_enable_bar", "precharge_enb"}:
        return "precharge_enb"
    if low in {"sense_enable", "write_enable", "wordline_enable"}:
        return low
    return low


def pin_role(name: str, canonical: str | None = None) -> str:
    canonical = canonical or canonical_pin_name(name)
    if canonical == "vdd":
        return "power"
    if canonical == "gnd":
        return "ground"
    if canonical in {"bl", "br"}:
        return "bitline"
    if canonical == "wl":
        return "wordline"
    if canonical in {"addr", "addr_q"}:
        return "address"
    if canonical in {"din", "din_q"}:
        return "data_in"
    if canonical in {"dout", "dout_b"}:
        return "data_out"
    if canonical in {"clk", "clk_buf", "clk_bar"}:
        return "clock"
    if canonical in {
        "en",
        "enb",
        "web",
        "csb",
        "precharge_enb",
        "sense_enable",
        "write_enable",
        "wordline_enable",
    }:
        return "control"
    return "signal"


def pin_polarity(name: str, canonical: str | None = None) -> str | None:
    canonical = canonical or canonical_pin_name(name)
    if canonical.endswith("_b") or canonical.endswith("_bar") or canonical in {"enb", "csb", "web", "precharge_enb"}:
        return "active_low"
    if canonical in {"en", "sense_enable", "write_enable", "wordline_enable"}:
        return "active_high"
    return None


def canonical_module_name(original: str, role: str | None = None) -> str:
    if original.startswith("COLUMNMUX"):
        return "column_mux"
    if original.startswith("SRAM_6T_CORE"):
        return "sram_6t_core"
    if original.startswith("SRAM_10T_CORE"):
        return "sram_10t_core"
    if original in MODULE_ALIASES:
        return MODULE_ALIASES[original][0]
    normalized = re.sub(r"[^0-9A-Za-z]+", "_", original).strip("_").lower()
    if role and role != "unknown":
        return role.replace("/", "_").replace(" ", "_")
    return normalized


def module_role(original: str, class_name: str = "", source_file: str = "") -> str:
    explicit = original.lower()
    class_text = class_name.lower()
    path_text = source_file.lower()
    text = f"{explicit} {class_text} {path_text}"
    if explicit == "sram_6t_cell" or class_name == "Sram6TCell":
        return "bitcell"
    if explicit == "sram_10t_cell" or class_name == "Sram10TCell":
        return "bitcell_10t"
    if explicit.startswith("sram_6t_core") or class_name == "Sram6TCore":
        return "bitcell_array"
    if explicit.startswith("sram_10t_core") or class_name == "Sram10TCore":
        return "bitcell_array_10t"
    if explicit == "writedriver" or "writedriver" in class_text or "write_driver" in class_text:
        return "write_driver"
    if explicit == "precharge" or "precharge" in class_text:
        return "precharge"
    if explicit == "senseamp" or "senseamp" in class_text or "sense_amp" in class_text:
        return "sense_amp"
    if explicit.startswith("columnmux") or "columnmux" in class_text or "column_mux" in class_text:
        return "column_mux"
    if "decoder" in explicit or "decoder" in class_text:
        return "decoder"
    if "wordline" in explicit or "wordline" in class_text:
        return "wordline_driver"
    if "dummy" in explicit or "dummy" in class_text:
        return "dummy"
    if "replica" in explicit or "replica" in class_text:
        return "replica"
    if original in {"TIME", "ADDR_DFF", "DATA_DFF", "DFF", "delay_chain", "wen_delay_chain"}:
        return "control_timing"
    if any(k in text for k in ["dff", "delaychain", "transmissiongate", "pdrive", "latch", "nand", "and", "pinv"]):
        return "support_cell"
    return "unknown"
