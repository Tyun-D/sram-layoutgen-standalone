from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.parameterized_cell_naming import build_cache_key, canonical_cell_name


REFERENCE_CONFIGS = {
    "16x16": {
        "num_rows": 16,
        "num_cols": 16,
        "num_words": 16,
        "word_size": 16,
        "words_per_row": 1,
        "mux_ratio": 1,
        "choose_columnmux": False,
        "sram_cell_type": "6T",
        "operation": "read&write",
        "tech": "FreePDK45",
    },
    "64x8": {
        "num_rows": 64,
        "num_cols": 8,
        "num_words": 64,
        "word_size": 8,
        "words_per_row": 1,
        "mux_ratio": 1,
        "choose_columnmux": False,
        "sram_cell_type": "6T",
        "operation": "read&write",
        "tech": "FreePDK45",
    },
}

PINV_RELEVANT_MODULES = {
    "pdrive",
    "pdrive2_for_pre",
    "wl_pdrive",
    "dff",
    "DFF_BUF",
    "DelayChain",
    "WenDelayChain",
    "TIME",
    "AND2",
    "AND3",
    "D_latch",
}


def _load_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _n_bits(num_rows: int) -> int:
    return math.ceil(math.log2(num_rows)) if num_rows > 1 else 1


def derive_drive_scales(config: dict[str, Any]) -> dict[str, Any]:
    num_rows = int(config["num_rows"])
    num_cols = int(config["num_cols"])
    n_bits = _n_bits(num_rows)
    ref_rows = 16
    ref_cols = 16
    ref_bits = _n_bits(ref_rows)
    clk_dff_count = n_bits + 2 + num_cols
    ref_dff_count = ref_bits + 2 + ref_cols
    clk_drive_scale = max(1.0, clk_dff_count / ref_dff_count)
    pre_col_scale = (num_cols + 1) / 65
    pre_pmos_scale = max(0.5, num_rows / 16)
    pre_drive_scale = max(1, math.ceil(pre_col_scale * pre_pmos_scale))
    w_en_scale = max(1, math.ceil(num_cols / 64))
    return {
        "address_bits": n_bits,
        "clk_dff_count": clk_dff_count,
        "ref_dff_count": ref_dff_count,
        "clk_drive_scale": clk_drive_scale,
        "pre_col_scale": pre_col_scale,
        "pre_pmos_scale": pre_pmos_scale,
        "pre_drive_scale": pre_drive_scale,
        "w_en_scale": w_en_scale,
        "resolved_scales": {
            "pdrive": clk_drive_scale,
            "pdrive2_for_pre": pre_drive_scale,
            "w_en_scale": w_en_scale,
        },
    }


def _resolved_pair(source_path: str, config: dict[str, Any]) -> tuple[int, int, int, dict[str, Any]]:
    scales = derive_drive_scales(config)
    if source_path == "pdrive.inv1":
        scale = max(1.0, float(scales["clk_drive_scale"])) ** 0.25
        return round(90 * scale), round(270 * scale), 50, {"resolved_drive_scale": scales["clk_drive_scale"], "stage_scale": scale}
    if source_path == "pdrive.inv2":
        scale = max(1.0, float(scales["clk_drive_scale"])) ** 0.5
        return round(270 * scale), round(810 * scale), 50, {"resolved_drive_scale": scales["clk_drive_scale"], "stage_scale": scale}
    if source_path == "pdrive.inv3":
        scale = max(1.0, float(scales["clk_drive_scale"])) ** 0.75
        return round(910 * scale), round(2430 * scale), 50, {"resolved_drive_scale": scales["clk_drive_scale"], "stage_scale": scale}
    if source_path == "pdrive.inv4":
        scale = max(1.0, float(scales["clk_drive_scale"]))
        return round(2430 * scale), round(7290 * scale), 50, {"resolved_drive_scale": scales["clk_drive_scale"], "stage_scale": scale}
    if source_path == "pdrive2_for_pre.inv1":
        drive_scale = max(1.0, float(scales["pre_drive_scale"]))
        stage_scale = max(1.0, drive_scale ** 0.5)
        return round(90 * stage_scale), round(270 * stage_scale), 50, {"resolved_drive_scale": drive_scale, "stage_scale": stage_scale}
    if source_path == "pdrive2_for_pre.inv2":
        drive_scale = max(1.0, float(scales["pre_drive_scale"]))
        return round(270 * drive_scale), round(810 * drive_scale), 50, {"resolved_drive_scale": drive_scale, "stage_scale": drive_scale}
    fixed = {
        "wl_pdrive.inv1": (90, 270, 50),
        "wl_pdrive.inv2": (450, 1350, 50),
        "dff.inv_dff": (250, 500, 50),
        "DFF_BUF.inv1": (180, 540, 50),
        "DFF_BUF.inv2": (360, 1080, 50),
        "DelayChain.inv": (90, 270, 50),
        "WenDelayChain.inv": (90, 270, 50),
        "TIME.inv_clk_bar": (90, 270, 50),
        "TIME.inv_wl_en_bar": (90, 270, 50),
        "TIME.inv_rbl_delay_bar": (90, 270, 50),
        "AND2.inv_driver": (90, 270, 50),
        "AND3.inv_driver": (90, 270, 50),
        "D_latch.inv1": (180, 270, 50),
    }
    if source_path in fixed:
        nw, pw, ln = fixed[source_path]
        return nw, pw, ln, {"resolved_drive_scale": 1.0, "stage_scale": 1.0}
    raise KeyError(source_path)


def resolve_concrete_variants(corrected_variant_matrix_csv: Path) -> dict[str, Any]:
    rows = _load_csv(corrected_variant_matrix_csv)
    relevant_rows = [row for row in rows if row["source_parent_module"] in PINV_RELEVANT_MODULES]
    concrete_rows: list[dict[str, Any]] = []
    per_config: dict[str, Any] = {}
    symbolic_before = 0
    unresolved_after = 0
    for config_name, config in REFERENCE_CONFIGS.items():
        scales = derive_drive_scales(config)
        config_rows = []
        for row in relevant_rows:
            source_path = row["source_instance_path"]
            if any(ch in row["nmos_width_nm"] for ch in "()*floatmax") or any(ch in row["pmos_width_nm"] for ch in "()*floatmax"):
                symbolic_before += 1
            try:
                nw, pw, ln, extra = _resolved_pair(source_path, config)
                status = "RESOLVED_CONCRETE"
                canonical_name = canonical_cell_name(logical_type="PINV", nmos_width_nm=nw, pmos_width_nm=pw, length_nm=ln)
                cache_key = build_cache_key(
                    technology="FreePDK45",
                    logical_type="PINV",
                    nmos_width_nm=nw,
                    pmos_width_nm=pw,
                    channel_length_nm=ln,
                    finger_or_mult_policy="single_inverter_pair",
                    contact_policy=row["contact_policy"],
                    rail_policy=row["rail_policy"],
                    orientation_policy="fixed row orientation",
                    source_netlist_role=source_path,
                )
            except Exception:
                nw = pw = ln = 0
                status = "UNRESOLVED_SYMBOLIC"
                canonical_name = ""
                cache_key = ""
                unresolved_after += 1
                extra = {"resolved_drive_scale": None, "stage_scale": None}
            config_row = {
                "reference_config": config_name,
                "source_file": row.get("source_file", "time_generate.py"),
                "source_class": row["source_parent_module"],
                "source_instance_path": source_path,
                "logical_alias": row["logical_alias"],
                "parameter_expression": row["canonical_parameter_tuple"],
                "drive_scale_inputs": json.dumps(scales, sort_keys=True),
                "resolved_drive_scale": extra["resolved_drive_scale"],
                "resolved_nmos_width_nm": nw,
                "resolved_pmos_width_nm": pw,
                "resolved_channel_length_nm": ln,
                "canonical_physical_cell_name": canonical_name,
                "cache_key": cache_key,
                "parameter_resolution_status": status,
                "resolution_source_trace": json.dumps({"source_path": source_path, "config": config_name, "scales": scales}, sort_keys=True),
            }
            config_rows.append(config_row)
            concrete_rows.append(config_row)
        per_config[config_name] = {"config": config, "scales": scales, "rows": config_rows}

    unique_variants: dict[str, dict[str, Any]] = {}
    variant_to_paths: dict[str, set[str]] = defaultdict(set)
    reference_configs_by_variant: dict[str, set[str]] = defaultdict(set)
    for row in concrete_rows:
        if row["parameter_resolution_status"] != "RESOLVED_CONCRETE":
            continue
        unique_variants.setdefault(row["canonical_physical_cell_name"], row)
        variant_to_paths[row["canonical_physical_cell_name"]].add(row["source_instance_path"])
        reference_configs_by_variant[row["canonical_physical_cell_name"]].add(row["reference_config"])
    unique_rows = []
    for name, row in sorted(unique_variants.items()):
        unique_rows.append(
            {
                **row,
                "source_instance_paths": "|".join(sorted(variant_to_paths[name])),
                "reference_configs": "|".join(sorted(reference_configs_by_variant[name])),
            }
        )
    return {
        "per_config": per_config,
        "rows": concrete_rows,
        "unique_rows": unique_rows,
        "symbolic_variant_count_before_resolution": len(
            [row for row in relevant_rows if any(ch in row["nmos_width_nm"] for ch in "()*floatmax") or any(ch in row["pmos_width_nm"] for ch in "()*floatmax")]
        ),
        "unresolved_symbolic_variant_count_after_resolution": unresolved_after,
        "concrete_variant_count": len(unique_rows),
        "distinct_concrete_inverter_variant_count": len(unique_rows),
    }

