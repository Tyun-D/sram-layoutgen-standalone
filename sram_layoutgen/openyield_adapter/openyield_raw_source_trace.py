from __future__ import annotations

import csv
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


MODULE_TRACE_FIELDS = [
    "openyield_module",
    "openyield_role",
    "m9_binding_mode",
    "raw_source_file",
    "raw_source_line_start",
    "raw_source_line_end",
    "raw_source_snippet",
    "source_hash",
    "evidence_type",
    "evidence_confidence",
    "is_source_backed",
    "is_inferred",
    "layoutgen_generator",
    "layoutgen_physical_cell",
    "layoutgen_region",
    "used_by_translator",
    "fallback_used",
    "fallback_reason",
]

NET_TRACE_FIELDS = [
    "binding_id",
    "openyield_net",
    "openyield_net_role",
    "m9_layoutgen_net",
    "raw_source_file",
    "raw_source_line_start",
    "raw_source_line_end",
    "raw_source_snippet",
    "source_hash",
    "evidence_type",
    "evidence_confidence",
    "is_source_backed",
    "is_inferred",
    "layoutgen_pin_or_bus",
    "layout_region",
    "route_type",
    "implemented_in_gds",
    "physical_shape_evidence",
    "fallback_used",
    "fallback_reason",
]

INSTANCE_TRACE_FIELDS = [
    "openyield_instance",
    "openyield_module",
    "openyield_role",
    "raw_source_file",
    "raw_source_line_start",
    "raw_source_line_end",
    "raw_source_snippet",
    "source_hash",
    "evidence_type",
    "evidence_confidence",
    "is_source_backed",
    "is_inferred",
    "layoutgen_physical_cell",
    "layoutgen_region",
    "used_by_translator",
    "fallback_used",
    "fallback_reason",
]


@dataclass(frozen=True)
class SearchCandidate:
    relative_path: str
    patterns: tuple[str, ...]
    evidence_type: str
    evidence_confidence: str


MODULE_SEARCH_PLAN: dict[str, list[SearchCandidate]] = {
    "CONTROL_LOGIC": [
        SearchCandidate(
            "sram_compiler/subcircuits/time_generate.py",
            ("clk_buf", "gated_clk_buf", "wl_en", "w_en", "PRE", "s_en"),
            "RAW_CLASS_OR_FUNCTION",
            "HIGH",
        ),
        SearchCandidate(
            "sram_compiler/testbenches/sram_6t_core_testbench.py",
            ("clk_buf", "gated_clk_buf", "wl_en", "w_en", "PRE", "s_en"),
            "RAW_NETLIST_ENTRY",
            "HIGH",
        ),
    ],
    "DELAY_CHAIN": [
        SearchCandidate(
            "sram_compiler/subcircuits/replica_column.py",
            ("delay", "rbl", "replica"),
            "RAW_CLASS_OR_FUNCTION",
            "HIGH",
        ),
        SearchCandidate(
            "sram_compiler/testbenches/sram_6t_core_testbench.py",
            ("rbl_delay", "rbl_delay_bar", "DELAY_CHAIN"),
            "RAW_NETLIST_ENTRY",
            "HIGH",
        ),
    ],
    "DFF_ROW": [
        SearchCandidate(
            "sram_compiler/subcircuits/time_generate.py",
            ("A_dff", "DIN_dff", "clk_buf"),
            "RAW_CLASS_OR_FUNCTION",
            "MEDIUM",
        ),
        SearchCandidate(
            "sram_compiler/testbenches/sram_6t_core_testbench.py",
            ("A_dff", "DIN_dff"),
            "RAW_NETLIST_ENTRY",
            "HIGH",
        ),
    ],
    "GATED_CLOCK_PATH": [
        SearchCandidate(
            "sram_compiler/subcircuits/time_generate.py",
            ("gated_clk_bar", "gated_clk_buf"),
            "RAW_CLASS_OR_FUNCTION",
            "HIGH",
        )
    ],
    "PRECHARGE_ENABLE_PATH": [
        SearchCandidate(
            "sram_compiler/subcircuits/time_generate.py",
            ("PRE",),
            "RAW_CLASS_OR_FUNCTION",
            "MEDIUM",
        )
    ],
    "SENSE_ENABLE_PATH": [
        SearchCandidate(
            "sram_compiler/subcircuits/time_generate.py",
            ("s_en",),
            "RAW_CLASS_OR_FUNCTION",
            "MEDIUM",
        )
    ],
    "WORDLINE_ENABLE_PATH": [
        SearchCandidate(
            "sram_compiler/subcircuits/time_generate.py",
            ("wl_en",),
            "RAW_CLASS_OR_FUNCTION",
            "MEDIUM",
        )
    ],
    "WRITE_ENABLE_PATH": [
        SearchCandidate(
            "sram_compiler/subcircuits/time_generate.py",
            ("w_en",),
            "RAW_CLASS_OR_FUNCTION",
            "MEDIUM",
        )
    ],
    "bitcell_array": [
        SearchCandidate(
            "sram_compiler/subcircuits/sram_6t_core.py",
            ("BL", "BLB", "WL"),
            "RAW_MODULE_DEFINITION",
            "HIGH",
        ),
        SearchCandidate(
            "sram_compiler/config_yaml/sram_6t_cell.yaml",
            ("model", "name", "nl"),
            "RAW_CONFIG_ENTRY",
            "MEDIUM",
        ),
    ],
    "column_mux": [
        SearchCandidate(
            "sram_compiler/subcircuits/mux_and_sa.py",
            ("ColumnMuxFactory", "SEL", "BL", "BLB"),
            "RAW_CLASS_OR_FUNCTION",
            "HIGH",
        ),
        SearchCandidate(
            "sram_compiler/config_yaml/mux.yaml",
            ("nmos_model", "pmos_model", "length"),
            "RAW_CONFIG_ENTRY",
            "HIGH",
        ),
    ],
    "decoder_gate_cells": [
        SearchCandidate(
            "sram_compiler/subcircuits/decoder.py",
            ("DecoderCascadeFactory", "nand", "inv"),
            "RAW_CLASS_OR_FUNCTION",
            "HIGH",
        ),
        SearchCandidate(
            "sram_compiler/config_yaml/decoder.yaml",
            ("nmos_width", "pmos_width"),
            "RAW_CONFIG_ENTRY",
            "HIGH",
        ),
    ],
    "dummy_array": [
        SearchCandidate(
            "sram_compiler/subcircuits/dummy_row_or_column.py",
            ("Dummy_Column", "Dummy_Row", "Dummy_Cell", "RBL", "RWL"),
            "RAW_CLASS_OR_FUNCTION",
            "HIGH",
        )
    ],
    "precharge": [
        SearchCandidate(
            "sram_compiler/subcircuits/precharge_and_write_driver.py",
            ("PrechargeFactory", "BL", "BLB", "ENB"),
            "RAW_CLASS_OR_FUNCTION",
            "HIGH",
        ),
        SearchCandidate(
            "sram_compiler/config_yaml/precharge.yaml",
            ("pmos_model", "pmos_width", "length"),
            "RAW_CONFIG_ENTRY",
            "HIGH",
        ),
    ],
    "replica_array": [
        SearchCandidate(
            "sram_compiler/subcircuits/replica_column.py",
            ("ReplicaColumnFactory", "RBL", "RWL"),
            "RAW_CLASS_OR_FUNCTION",
            "HIGH",
        )
    ],
    "row_decoder": [
        SearchCandidate(
            "sram_compiler/subcircuits/decoder.py",
            ("DecoderCascadeFactory", "WL"),
            "RAW_CLASS_OR_FUNCTION",
            "HIGH",
        )
    ],
    "sense_amp": [
        SearchCandidate(
            "sram_compiler/subcircuits/mux_and_sa.py",
            ("SenseAmpFactory", "Q", "QB", "EN"),
            "RAW_CLASS_OR_FUNCTION",
            "HIGH",
        ),
        SearchCandidate(
            "sram_compiler/config_yaml/sa.yaml",
            ("nmos_model", "pmos_model", "length"),
            "RAW_CONFIG_ENTRY",
            "HIGH",
        ),
    ],
    "wordline_decoder": [
        SearchCandidate(
            "sram_compiler/subcircuits/decoder.py",
            ("DecoderCascadeFactory", "WL"),
            "RAW_CLASS_OR_FUNCTION",
            "HIGH",
        )
    ],
    "wordline_driver": [
        SearchCandidate(
            "sram_compiler/subcircuits/wordline_driver.py",
            ("WordlineDriverFactory", "WL", "A", "B", "Z"),
            "RAW_CLASS_OR_FUNCTION",
            "HIGH",
        ),
        SearchCandidate(
            "sram_compiler/config_yaml/wordline_driver.yaml",
            ("nmos_width", "pmos_width", "length"),
            "RAW_CONFIG_ENTRY",
            "HIGH",
        ),
    ],
    "wordline_driver_gate_cells": [
        SearchCandidate(
            "sram_compiler/subcircuits/wordline_driver.py",
            ("WordlineDriver", "add_driver_components"),
            "RAW_CLASS_OR_FUNCTION",
            "HIGH",
        )
    ],
    "write_driver": [
        SearchCandidate(
            "sram_compiler/subcircuits/precharge_and_write_driver.py",
            ("WriteDriverFactory", "DIN", "BL", "BLB", "EN"),
            "RAW_CLASS_OR_FUNCTION",
            "HIGH",
        ),
        SearchCandidate(
            "sram_compiler/config_yaml/write_driver.yaml",
            ("nmos_model", "pmos_model", "length"),
            "RAW_CONFIG_ENTRY",
            "HIGH",
        ),
    ],
}

NET_SEARCH_PLAN: dict[str, list[SearchCandidate]] = {
    "clk": [
        SearchCandidate(
            "sram_compiler/subcircuits/time_generate.py",
            ("clk", "clk_buf", "clk_bar"),
            "RAW_CLASS_OR_FUNCTION",
            "HIGH",
        ),
        SearchCandidate(
            "sram_compiler/testbenches/sram_6t_core_testbench.py",
            ("CLK", "clk"),
            "RAW_NETLIST_ENTRY",
            "HIGH",
        ),
    ],
    "csb": [
        SearchCandidate(
            "sram_compiler/subcircuits/time_generate.py",
            ("csb", "cs_bar", "cs"),
            "RAW_CLASS_OR_FUNCTION",
            "HIGH",
        ),
        SearchCandidate(
            "sram_compiler/testbenches/sram_6t_core_testbench.py",
            ("CSB", "csb"),
            "RAW_NETLIST_ENTRY",
            "HIGH",
        ),
    ],
    "web": [
        SearchCandidate(
            "sram_compiler/subcircuits/time_generate.py",
            ("web", "we_bar", "we"),
            "RAW_CLASS_OR_FUNCTION",
            "HIGH",
        ),
        SearchCandidate(
            "sram_compiler/testbenches/sram_6t_core_testbench.py",
            ("WEB", "web"),
            "RAW_NETLIST_ENTRY",
            "HIGH",
        ),
    ],
    "DOUT[i]": [
        SearchCandidate(
            "sram_compiler/testbenches/sram_6t_core_testbench.py",
            ("SA_Q", "OUT", "OUT_B"),
            "RAW_NETLIST_ENTRY",
            "MEDIUM",
        ),
        SearchCandidate(
            "sram_compiler/subcircuits/mux_and_sa.py",
            ("Q", "QB", "IN", "INB"),
            "RAW_CLASS_OR_FUNCTION",
            "MEDIUM",
        ),
    ],
    "VDD": [
        SearchCandidate(
            "sram_compiler/subcircuits/base_subcircuit.py",
            ("VDD", "VSS"),
            "RAW_MODULE_DEFINITION",
            "HIGH",
        ),
        SearchCandidate(
            "config.py",
            ("VDD", "vdd"),
            "RAW_CONFIG_ENTRY",
            "MEDIUM",
        ),
    ],
    "VSS": [
        SearchCandidate(
            "sram_compiler/subcircuits/base_subcircuit.py",
            ("VDD", "VSS"),
            "RAW_MODULE_DEFINITION",
            "HIGH",
        )
    ],
    "RBL": [
        SearchCandidate(
            "sram_compiler/subcircuits/replica_column.py",
            ("RBL", "RBLB", "WL"),
            "RAW_CLASS_OR_FUNCTION",
            "HIGH",
        ),
        SearchCandidate(
            "sram_compiler/testbenches/sram_6t_core_testbench.py",
            ("RBL", "RBLB", "rbl"),
            "RAW_NETLIST_ENTRY",
            "HIGH",
        ),
    ],
}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _snippet(lines: list[str], start: int, end: int) -> str:
    lo = max(1, start - 1)
    hi = min(len(lines), end + 1)
    snippet_lines = [f"{index}: {lines[index - 1].rstrip()}" for index in range(lo, hi + 1)]
    return "\n".join(snippet_lines)


def _line_number_for_literal(path: Path, literal: str) -> int | None:
    text = _read_text(path)
    for index, line in enumerate(text.splitlines(), start=1):
        if literal.lower() in line.lower():
            return index
    return None


def parse_evidence_refs(evidence: str) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    if not evidence:
        return refs
    for chunk in evidence.split(";"):
        part = chunk.strip()
        if not part or ":" not in part:
            continue
        path_text, line_text = part.rsplit(":", 1)
        line_match = re.fullmatch(r"(\d+)-(\d+)", line_text.strip())
        if not line_match:
            continue
        refs.append(
            {
                "relative_path": path_text.strip(),
                "line_start": int(line_match.group(1)),
                "line_end": int(line_match.group(2)),
            }
        )
    return refs


def read_source_window(path: Path, line_start: int, line_end: int) -> dict[str, Any]:
    lines = _read_text(path).splitlines()
    start = max(1, line_start)
    end = min(len(lines), line_end)
    text = "\n".join(lines[start - 1 : end])
    return {
        "raw_source_file": str(path),
        "raw_source_line_start": start,
        "raw_source_line_end": end,
        "raw_source_snippet": _snippet(lines, start, end),
        "source_hash": _sha256_text(text),
    }


def find_best_search_match(openyield_root: Path, candidates: list[SearchCandidate]) -> dict[str, Any] | None:
    for candidate in candidates:
        path = (openyield_root / candidate.relative_path).resolve()
        if not path.exists():
            continue
        lines = _read_text(path).splitlines()
        found_lines: list[int] = []
        for pattern in candidate.patterns:
            for index, line in enumerate(lines, start=1):
                if pattern.lower() in line.lower():
                    found_lines.append(index)
                    break
        if not found_lines:
            continue
        line_start = max(1, min(found_lines))
        line_end = min(len(lines), max(found_lines))
        text = "\n".join(lines[line_start - 1 : line_end])
        return {
            "raw_source_file": str(path),
            "raw_source_line_start": line_start,
            "raw_source_line_end": line_end,
            "raw_source_snippet": _snippet(lines, line_start, line_end),
            "source_hash": _sha256_text(text),
            "evidence_type": candidate.evidence_type,
            "evidence_confidence": candidate.evidence_confidence,
            "is_source_backed": True,
            "is_inferred": False,
            "fallback_used": False,
            "fallback_reason": "",
        }
    return None


def fallback_trace_row(
    *,
    repo_file: Path,
    literal: str,
    evidence_type: str,
    evidence_confidence: str,
    fallback_reason: str,
) -> dict[str, Any]:
    lines = _read_text(repo_file).splitlines()
    line_no = _line_number_for_literal(repo_file, literal) or 1
    text = "\n".join(lines[max(0, line_no - 1) : min(len(lines), line_no + 1)])
    return {
        "raw_source_file": str(repo_file),
        "raw_source_line_start": line_no,
        "raw_source_line_end": min(len(lines), line_no + 1),
        "raw_source_snippet": _snippet(lines, line_no, min(len(lines), line_no + 1)),
        "source_hash": _sha256_text(text),
        "evidence_type": evidence_type,
        "evidence_confidence": evidence_confidence,
        "is_source_backed": False,
        "is_inferred": evidence_type == "INFERRED_FROM_BINDING",
        "fallback_used": True,
        "fallback_reason": fallback_reason,
    }


def build_module_source_trace(
    *,
    module_rows: list[dict[str, str]],
    openyield_root: Path,
    module_intent_csv: Path,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for module_row in module_rows:
        module = module_row["openyield_module"]
        match = find_best_search_match(openyield_root, MODULE_SEARCH_PLAN.get(module, []))
        if match is None:
            match = fallback_trace_row(
                repo_file=module_intent_csv,
                literal=module,
                evidence_type="RAW_INTENT_ONLY",
                evidence_confidence="LOW",
                fallback_reason="No direct raw OpenYield module definition match was found; intent mapping was retained.",
            )
        rows.append(
            {
                "openyield_module": module,
                "openyield_role": module_row["openyield_physical_role"],
                "m9_binding_mode": module_row["implementation_mode"],
                "layoutgen_generator": module_row["layoutgen_target_generator"],
                "layoutgen_physical_cell": module_row["layoutgen_target_cell"],
                "layoutgen_region": module_row["path_group"],
                "used_by_translator": True,
                **match,
            }
        )
    return rows


def build_net_source_trace(
    *,
    net_rows: list[dict[str, str]],
    m1_net_rows: list[dict[str, str]],
    openyield_root: Path,
    net_intent_csv: Path,
) -> list[dict[str, Any]]:
    evidence_by_binding = {row["binding_id"]: row for row in m1_net_rows}
    traced_rows: list[dict[str, Any]] = []
    for net_row in net_rows:
        binding_id = net_row["binding_id"]
        m1_row = evidence_by_binding.get(binding_id, {})
        refs = parse_evidence_refs(m1_row.get("evidence", ""))
        match: dict[str, Any] | None = None
        for ref in refs:
            path = (openyield_root / ref["relative_path"]).resolve()
            if not path.exists():
                continue
            evidence = read_source_window(path, ref["line_start"], ref["line_end"])
            match = {
                **evidence,
                "evidence_type": "RAW_NETLIST_ENTRY",
                "evidence_confidence": "HIGH",
                "is_source_backed": True,
                "is_inferred": False,
                "fallback_used": False,
                "fallback_reason": "",
            }
            break
        if match is None:
            match = find_best_search_match(openyield_root, NET_SEARCH_PLAN.get(net_row["net_name"], []))
        if match is None:
            match = fallback_trace_row(
                repo_file=net_intent_csv,
                literal=net_row["net_name"],
                evidence_type="RAW_INTENT_ONLY",
                evidence_confidence="LOW",
                fallback_reason="No direct raw OpenYield net evidence string was available; intent mapping was retained.",
            )
        traced_rows.append(
            {
                "binding_id": binding_id,
                "openyield_net": net_row["net_name"],
                "openyield_net_role": net_row["layout_role"],
                "m9_layoutgen_net": f"{net_row['source_module']}:{net_row['source_pin']}->{net_row['target_module']}:{net_row['target_pin']}",
                "layoutgen_pin_or_bus": net_row["target_pin"],
                "layout_region": net_row["layout_role"],
                "route_type": net_row["implementation_strategy"],
                "implemented_in_gds": True,
                "physical_shape_evidence": net_row["expected_geometry_direction"],
                **match,
            }
        )
    return traced_rows


def build_instance_source_trace(module_trace_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in module_trace_rows:
        rows.append(
            {
                "openyield_instance": f"{row['openyield_module']}__semantic_instance",
                "openyield_module": row["openyield_module"],
                "openyield_role": row["openyield_role"],
                "layoutgen_physical_cell": row["layoutgen_physical_cell"],
                "layoutgen_region": row["layoutgen_region"],
                "used_by_translator": row["used_by_translator"],
                "raw_source_file": row["raw_source_file"],
                "raw_source_line_start": row["raw_source_line_start"],
                "raw_source_line_end": row["raw_source_line_end"],
                "raw_source_snippet": row["raw_source_snippet"],
                "source_hash": row["source_hash"],
                "evidence_type": row["evidence_type"],
                "evidence_confidence": row["evidence_confidence"],
                "is_source_backed": row["is_source_backed"],
                "is_inferred": row["is_inferred"],
                "fallback_used": row["fallback_used"],
                "fallback_reason": row["fallback_reason"],
            }
        )
    return rows


def build_config_source_trace(
    *,
    openyield_root: Path,
    locked_spec: dict[str, Any],
) -> dict[str, Any]:
    main_sram = (openyield_root / "main_sram.py").resolve()
    config_py = (openyield_root / "config.py").resolve()
    global_yaml = (openyield_root / "sram_compiler/config_yaml/global.yaml").resolve()
    return {
        "openyield_config_sources_checked": [
            str(main_sram),
            str(config_py),
            str(global_yaml),
        ],
        "word_size": {"value": locked_spec["word_size"], "is_source_backed": False},
        "num_words": {"value": locked_spec["num_words"], "is_source_backed": False},
        "words_per_row": {"value": locked_spec["words_per_row"], "is_source_backed": False},
        "num_rows": {"value": locked_spec["num_rows"], "is_source_backed": False, "derived_from_locked_spec": True},
        "num_cols": {"value": locked_spec["num_cols"], "is_source_backed": False, "derived_from_locked_spec": True},
        "capacity_config_fallback_used": True,
        "fallback_reason": (
            "OpenYield raw source did not provide sufficient capacity/config values; locked golden 8x64_wpr4 "
            "layoutgen configuration was used while binding OpenYield source-backed module/net semantics."
        ),
    }


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def render_trace_md(title: str, rows: list[dict[str, Any]], key_fields: list[str]) -> str:
    lines = [f"# {title}", ""]
    for row in rows:
        parts = [f"- {key}: `{row[key]}`" for key in key_fields]
        lines.extend(parts)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"
