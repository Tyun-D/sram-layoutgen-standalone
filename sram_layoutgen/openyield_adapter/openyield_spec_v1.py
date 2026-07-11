from __future__ import annotations

import json
from pathlib import Path
from typing import Any


SPEC_VERSION = "OPENYIELD_SRAM_SPEC_V1"


def build_spec_schema() -> dict[str, Any]:
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": SPEC_VERSION,
        "type": "object",
        "required": [
            "num_rows",
            "num_cols",
            "num_words",
            "word_size",
            "words_per_row",
            "mux_ratio",
            "choose_columnmux",
            "sram_cell_type",
        ],
        "properties": {
            "num_rows": {"type": "integer", "minimum": 1},
            "num_cols": {"type": "integer", "minimum": 1},
            "num_words": {"type": "integer", "minimum": 1},
            "word_size": {"type": "integer", "minimum": 1},
            "words_per_row": {"type": "integer", "const": 1},
            "mux_ratio": {"type": "integer", "const": 1},
            "choose_columnmux": {"type": "boolean", "const": False},
            "sram_cell_type": {"type": "string", "enum": ["6T"]},
            "corner": {"type": "string", "default": "TT"},
            "temperature": {"type": "number", "default": 27},
            "control_timing_parameters": {
                "type": "object",
                "additionalProperties": True,
                "description": "Simulation-backed control timing defaults traced from BaseTestbench/TIME.",
            },
        },
        "additionalProperties": False,
    }


def build_spec_example(num_rows: int, num_cols: int) -> dict[str, Any]:
    return {
        "num_rows": num_rows,
        "num_cols": num_cols,
        "num_words": num_rows,
        "word_size": num_cols,
        "words_per_row": 1,
        "mux_ratio": 1,
        "choose_columnmux": False,
        "sram_cell_type": "6T",
    }


def validate_spec_v1(spec: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for key in ["num_rows", "num_cols", "num_words", "word_size", "words_per_row", "mux_ratio"]:
        if not isinstance(spec.get(key), int) or spec[key] <= 0:
            errors.append(f"{key} must be a positive integer")
    if spec.get("choose_columnmux") is not False:
        errors.append("choose_columnmux must be False in V1")
    if spec.get("words_per_row") != 1:
        errors.append("words_per_row must be 1 in V1")
    if spec.get("mux_ratio") != 1:
        errors.append("mux_ratio must be 1 in V1")
    if spec.get("num_words") != spec.get("num_rows"):
        errors.append("num_words must equal num_rows in V1")
    if spec.get("word_size") != spec.get("num_cols"):
        errors.append("word_size must equal num_cols in V1")
    if spec.get("sram_cell_type") != "6T":
        errors.append("sram_cell_type must be 6T in V1")
    return errors


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def render_spec_md() -> str:
    return "\n".join(
        [
            f"# {SPEC_VERSION}",
            "",
            "- scope: `layout-facing clean SRAM top extracted from the OpenYield testbench-backed generator`",
            "- supported_now: `num_rows, num_cols, num_words=num_rows, word_size=num_cols, choose_columnmux=false, words_per_row=1, mux_ratio=1, sram_cell_type=6T, corner, temperature, control_timing_parameters`",
            "- unsupported_now: `words_per_row > 1, arbitrary column mux ratio, arbitrary PDK physical generation, custom-netlist-driven final GDS`",
            "- authority_boundary: `V1 is proven only for choose_columnmux=false and the generated 16x16 / 64x8 clean-top samples.`",
            "",
        ]
    )
