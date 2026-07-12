from __future__ import annotations

import json
from math import ceil, log2
from pathlib import Path
from typing import Any

from .approved_primitive_binder import resolve_pinv_variant


PDRIVE_SEQUENCE = [
    {"nmos_width_nm": 90, "pmos_width_nm": 270, "physical_cell": "PINV_NW90_PW270_L50"},
    {"nmos_width_nm": 270, "pmos_width_nm": 810, "physical_cell": "PINV_NW270_PW810_L50"},
    {"nmos_width_nm": 910, "pmos_width_nm": 2430, "physical_cell": "PINV_NW910_PW2430_L50"},
    {"nmos_width_nm": 2430, "pmos_width_nm": 7290, "physical_cell": "PINV_NW2430_PW7290_L50"},
]
PDRIVE2_PRE_SEQUENCE = [
    {"nmos_width_nm": 90, "pmos_width_nm": 270, "physical_cell": "PINV_NW90_PW270_L50"},
    {"nmos_width_nm": 270, "pmos_width_nm": 810, "physical_cell": "PINV_NW270_PW810_L50"},
]
WL_PDRIVE_SEQUENCE = [
    {"nmos_width_nm": 90, "pmos_width_nm": 270, "physical_cell": "PINV_NW90_PW270_L50"},
    {"nmos_width_nm": 450, "pmos_width_nm": 1350, "physical_cell": "PINV_NW450_PW1350_L50"},
]
DELAY_CHAIN_STAGE = {"nmos_width_nm": 90, "pmos_width_nm": 270, "physical_cell": "PINV_NW90_PW270_L50"}


def _address_width(num_rows: int) -> int:
    return ceil(log2(num_rows)) if num_rows > 1 else 1


def expand_concrete_configuration(config: dict[str, Any]) -> dict[str, Any]:
    num_rows = int(config["num_rows"])
    num_cols = int(config["num_cols"])
    operation = str(config["operation"])
    address_width = _address_width(num_rows)
    data_dff_count = num_cols if operation in {"write", "read&write"} else 0
    dff_total = address_width + data_dff_count + 2
    clk_drive_scale = 1
    pre_drive_scale = 1
    w_en_scale = max(1, ceil(num_cols / 64))
    return {
        "config": config,
        "address_width": address_width,
        "ADDR_DFF_bit_count": address_width,
        "DATA_DFF_bit_count": data_dff_count,
        "DFF_total_count": dff_total,
        "DFF_BUF_count": 2,
        "AND2_count": 2,
        "AND3_count": 2,
        "PNAND2_count": 2,
        "PNAND3_count": 3,
        "pdrive_child_variant_sequence": PDRIVE_SEQUENCE,
        "pdrive2_for_pre_child_variant_sequence": PDRIVE2_PRE_SEQUENCE,
        "wl_pdrive_child_variant_sequence": WL_PDRIVE_SEQUENCE,
        "delay_chain_stage_count": 9,
        "delay_chain_polarity_parity": "odd_stage_count_inverting",
        "delay_chain_child_variant_sequence": [DELAY_CHAIN_STAGE] * 9,
        "TIME_child_instance_counts": {
            "ADDR_DFF": 1,
            "DATA_DFF": 1 if data_dff_count else 0,
            "DFF_BUF": 2,
            "pdrive": 1,
            "wl_pdrive": 1,
            "delay_chain": 1,
            "AND2": 2,
            "AND3": 2,
            "PNAND3": 1,
            "PINV_wl_en_bar": 1,
        },
        "concrete_physical_children": {
            "DFF_pinv": resolve_pinv_variant("2.5e-07", "5e-07"),
            "DFF_transmission_gate": "TRANSMISSION_GATE_NW250_PW500_L50",
            "DFF_BUF_inv1": resolve_pinv_variant("0.18e-6", "0.54e-6"),
            "DFF_BUF_inv2": resolve_pinv_variant("0.36e-6", "1.08e-6"),
            "PINV_wl_en_bar": resolve_pinv_variant("0.09e-6", "0.27e-6"),
            "PINV_clk_bar": resolve_pinv_variant("0.09e-6", "0.27e-6"),
            "PINV_rbl_delay_bar": resolve_pinv_variant("0.09e-6", "0.27e-6"),
        },
    }


def concrete_instance_matrix(expansions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for expansion in expansions:
        cfg = expansion["config"]
        tag = f"R{cfg['num_rows']}_C{cfg['num_cols']}_{cfg['operation']}"
        for key in ["DFF_total_count", "DFF_BUF_count", "AND2_count", "AND3_count", "PNAND2_count", "PNAND3_count"]:
            rows.append({"config_id": tag, "module_name": key.replace("_count", ""), "instance_count": expansion[key]})
    return rows
