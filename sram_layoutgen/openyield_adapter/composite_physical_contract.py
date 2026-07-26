from __future__ import annotations

from typing import Any


def build_composite_module_contracts() -> dict[str, Any]:
    contracts = {
        "DFF": {
            "child_instances": {"PINV": 7, "TRANSMISSION_GATE": 4},
            "top_pins": ["VDD", "VSS", "D", "Q", "CLK"],
            "internal_nets": ["CLKB", "D_b", "z1", "z2", "z3", "z4", "z5", "QB"],
            "placement_order": ["inv1_clk", "inv2_D", "tg1", "inv3", "inv4", "tg2", "inv5", "tg3", "inv6", "inv7", "tg4"],
            "routing_crossings": ["clock/control crossover around tg1-tg4 feedback loop"],
            "requires_m2": True,
            "output_polarity": "Q non-inverted, internal QB feedback present",
        },
        "DFF_BUF": {
            "child_instances": {"DFF": 1, "PINV": 2},
            "top_pins": ["VDD", "VSS", "D", "Q", "QB", "CLK"],
            "placement_order": ["dff", "inv1", "inv2"],
        },
        "ADDR_DFF": {"bit_count_formula": "ceil(log2(num_rows))", "array_policy": "row_array_of_dff"},
        "DATA_DFF": {"bit_count_formula": "num_cols", "array_policy": "row_array_of_dff"},
        "PNAND2": {"openram_pnand2_generator_found": True, "canonical_pin_mapping_possible": True, "qualified_for_binding": False},
        "PNAND3": {"openram_pnand3_generator_found": True, "canonical_pin_mapping_possible": True, "qualified_for_binding": False},
        "AND2": {"composition": ["PNAND2", "PINV"], "internal_net": "zb_int"},
        "AND3": {"composition": ["PNAND3", "PINV"], "internal_net": "zb_int"},
        "buffer_chains": {
            "pdrive": "four_stage_pinv_chain",
            "pdrive2_for_pre": "two_stage_pinv_chain",
            "wl_pdrive": "two_stage_pinv_chain",
        },
        "delay_chain": {"stage_count": 9, "loads_per_stage": 4, "polarity": "inverting"},
        "TIME": {"operation_topology": "READ_WRITE_SUPERSET_CANONICAL", "generation_allowed_in_m12c4": False},
    }
    matrix_rows = []
    for module_name, contract in contracts.items():
        matrix_rows.append({"module_name": module_name, "contract_summary": str(contract)})
    return {"contracts": contracts, "matrix_rows": matrix_rows}
