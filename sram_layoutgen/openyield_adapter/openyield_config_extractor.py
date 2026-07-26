from __future__ import annotations

import csv
import hashlib
import math
import re
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.openyield_raw_source_trace import write_csv, write_json, write_text


TEXT_EXTENSIONS = {
    ".py",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".cfg",
    ".ini",
    ".sp",
    ".spi",
    ".cdl",
    ".v",
    ".sv",
    ".txt",
    ".md",
}
KEY_ENTRYPOINTS = {
    "main_sram.py",
    "main_opt.py",
    "main_estimation.py",
    "equivalent_modeling/main_sram.py",
    "demo_run_a_testbench.py",
}
KEYWORDS = [
    "word_size",
    "num_words",
    "words_per_row",
    "wpr",
    "num_rows",
    "num_cols",
    "rows",
    "cols",
    "addr",
    "data",
    "bit",
    "sram",
    "size",
    "capacity",
    "config",
    "yaml",
    "json",
    "cfg",
    "argparse",
    "parameter",
    "sample",
    "benchmark",
    "testbench",
    "netlist",
    "array",
]
SOURCE_TYPES = {
    "RAW_OPENYIELD_CONFIG",
    "RAW_OPENYIELD_SCRIPT_ARGUMENT",
    "RAW_OPENYIELD_NETLIST_EVIDENCE",
    "DERIVED_FROM_RAW_SOURCE",
    "LOCKED_GOLDEN_FALLBACK",
    "LAYOUTGEN_DEFAULT",
    "UNKNOWN",
}
CONFIG_CANDIDATE_FIELDS = [
    "candidate_id",
    "file_id",
    "relative_path",
    "category",
    "is_key_entrypoint",
    "is_config_file",
    "matched_keywords",
    "matched_keyword_count",
    "capacity_keyword_count",
    "variation_keyword_count",
    "size_bytes",
    "line_count",
]
SPEC_FIELD_SOURCE_FIELDS = [
    "spec_field",
    "value",
    "source_type",
    "raw_source_file",
    "raw_source_line_start",
    "raw_source_line_end",
    "raw_source_snippet",
    "source_hash",
    "is_raw_source_backed",
    "is_fallback",
    "fallback_source",
    "fallback_reason",
    "used_by_translator",
]


def _read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "latin-1"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Unable to decode text file: {path}")


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _snippet(lines: list[str], start: int, end: int) -> str:
    lo = max(1, start - 1)
    hi = min(len(lines), end + 1)
    return "\n".join(f"{index}: {lines[index - 1].rstrip()}" for index in range(lo, hi + 1))


def _find_line_range(lines: list[str], patterns: list[str]) -> tuple[int, int] | None:
    matched: list[int] = []
    for pattern in patterns:
        if pattern.startswith("re:"):
            regex = re.compile(pattern[3:], re.IGNORECASE)
            for index, line in enumerate(lines, start=1):
                if regex.search(line):
                    matched.append(index)
                    break
        else:
            lowered = pattern.lower()
            for index, line in enumerate(lines, start=1):
                if lowered in line.lower():
                    matched.append(index)
                    break
    if not matched:
        return None
    return min(matched), max(matched)


def _evidence_from_patterns(openyield_root: Path, relative_path: str, patterns: list[str]) -> dict[str, Any] | None:
    path = (openyield_root / relative_path).resolve()
    if not path.exists():
        return None
    lines = _read_text(path).splitlines()
    line_range = _find_line_range(lines, patterns)
    if line_range is None:
        return None
    start, end = line_range
    text = "\n".join(lines[start - 1 : end])
    return {
        "raw_source_file": str(path),
        "raw_source_line_start": start,
        "raw_source_line_end": end,
        "raw_source_snippet": _snippet(lines, start, end),
        "source_hash": _sha256_text(text),
    }


def _inventory_index(t1_inventory: Path | None) -> dict[str, str]:
    if t1_inventory is None or not t1_inventory.exists():
        return {}
    with t1_inventory.open(newline="", encoding="utf-8") as handle:
        return {row["relative_path"]: row.get("file_id", "") for row in csv.DictReader(handle)}


def _category_for_path(relative_path: str) -> str:
    suffix = Path(relative_path).suffix.lower()
    if relative_path in KEY_ENTRYPOINTS:
        return "KEY_ENTRYPOINT"
    if "config" in relative_path.lower() or suffix in {".yaml", ".yml", ".cfg", ".ini", ".json", ".toml"}:
        return "CONFIG_FILE"
    if "experiment" in relative_path.lower() or "demo_" in relative_path.lower():
        return "OPTIMIZATION_OR_DEMO"
    if suffix in {".md", ".txt"}:
        return "DOCUMENTATION"
    if suffix in {".sp", ".spi", ".cdl", ".v", ".sv"}:
        return "NETLISTISH"
    return "SOURCE_FILE"


def _safe_relpath(path: Path, root: Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def list_candidate_files(openyield_root: Path, t1_inventory: Path | None = None) -> list[dict[str, Any]]:
    inventory = _inventory_index(t1_inventory)
    rows: list[dict[str, Any]] = []
    candidate_id = 1
    for path in sorted(openyield_root.rglob("*")):
        if not path.is_file():
            continue
        relative_path = _safe_relpath(path, openyield_root)
        suffix = path.suffix.lower()
        if suffix not in TEXT_EXTENSIONS:
            continue
        text = _read_text(path)
        lowered = text.lower()
        matched_keywords = [keyword for keyword in KEYWORDS if keyword.lower() in lowered or keyword.lower() in relative_path.lower()]
        if not matched_keywords and relative_path not in KEY_ENTRYPOINTS and "config" not in relative_path.lower():
            continue
        capacity_keywords = [keyword for keyword in matched_keywords if keyword in {"word_size", "num_words", "words_per_row", "wpr", "num_rows", "num_cols", "rows", "cols", "capacity", "array"}]
        variation_keywords = [keyword for keyword in matched_keywords if keyword in {"variation", "rows", "cols", "capacity", "array", "choose_columnmux", "mux"}]
        rows.append(
            {
                "candidate_id": f"M11CFG{candidate_id:04d}",
                "file_id": inventory.get(relative_path, ""),
                "relative_path": relative_path,
                "category": _category_for_path(relative_path),
                "is_key_entrypoint": relative_path in KEY_ENTRYPOINTS,
                "is_config_file": suffix in {".yaml", ".yml", ".json", ".toml", ".cfg", ".ini"} or "config" in relative_path.lower(),
                "matched_keywords": ";".join(sorted(set(matched_keywords))),
                "matched_keyword_count": len(set(matched_keywords)),
                "capacity_keyword_count": len(set(capacity_keywords)),
                "variation_keyword_count": len(set(variation_keywords)),
                "size_bytes": path.stat().st_size,
                "line_count": len(text.splitlines()),
            }
        )
        candidate_id += 1
    return rows


def build_raw_architecture_summary(openyield_root: Path) -> dict[str, Any]:
    global_yaml = _evidence_from_patterns(openyield_root, "sram_compiler/config_yaml/global.yaml", ["num_rows:", "num_cols:", "TOTAL_capacity_KB:", "choose_columnmux:"])
    main_sram = _evidence_from_patterns(openyield_root, "main_sram.py", ["global_config_update = [16, 16, False", "num_rows =", "num_cols =", "choose_columnmux ="])
    testbench_mux = _evidence_from_patterns(openyield_root, "sram_compiler/testbenches/sram_6t_core_testbench.py", ["if self.choose_columnmux:", "self.mux_in = 2"])
    experiment = _evidence_from_patterns(openyield_root, "size_optimization/experiment.py", ["ROW_CHOICES", "COLUMN_CHOICES", "TOTAL_BITS = 262144"])
    opt_doc = _evidence_from_patterns(openyield_root, "电路算法说明文档.md", ["阵列数", "默认总容量为 32 KB", "Column Mux 当前固定为 2 路复用"])
    return {
        "global_yaml": global_yaml,
        "main_sram": main_sram,
        "testbench_mux": testbench_mux,
        "experiment": experiment,
        "opt_doc": opt_doc,
    }


def build_openyield_derived_spec(
    *,
    raw_num_rows: int,
    raw_num_cols: int,
    choose_columnmux: bool,
    locked_spec: dict[str, Any],
) -> dict[str, Any]:
    column_mux_ratio = 2 if choose_columnmux else 1
    derived_word_size = raw_num_cols // column_mux_ratio if raw_num_cols % column_mux_ratio == 0 else raw_num_cols
    derived_words_per_row = column_mux_ratio
    derived_num_words = raw_num_rows * derived_words_per_row
    return {
        "raw_num_rows": raw_num_rows,
        "raw_num_cols": raw_num_cols,
        "raw_choose_columnmux": choose_columnmux,
        "word_size": derived_word_size,
        "num_words": derived_num_words,
        "words_per_row": derived_words_per_row,
        "num_rows": raw_num_rows,
        "num_cols": raw_num_cols,
        "num_banks": 1,
        "num_ports": 1,
        "tech": locked_spec["tech"],
        "column_mux_ratio": column_mux_ratio,
        "mux_enabled": bool(choose_columnmux),
        "derivation_rule": {
            "word_size": "word_size = num_cols / column_mux_ratio",
            "num_words": "num_words = num_rows * words_per_row",
            "words_per_row": "words_per_row = column_mux_ratio = 2 if choose_columnmux else 1",
        },
    }


def build_variation_support_summary(openyield_root: Path) -> dict[str, Any]:
    experiment_text = _read_text(openyield_root / "size_optimization/experiment.py")
    row_match = re.search(r"ROW_CHOICES\s*=\s*\[([^\]]+)\]", experiment_text)
    col_match = re.search(r"COLUMN_CHOICES\s*=\s*\[([^\]]+)\]", experiment_text)
    total_bits_match = re.search(r"TOTAL_BITS\s*=\s*(\d+)", experiment_text)
    row_choices = [int(item.strip()) for item in row_match.group(1).split(",")] if row_match else [16]
    col_choices = [int(item.strip()) for item in col_match.group(1).split(",")] if col_match else [16]
    total_bits = int(total_bits_match.group(1)) if total_bits_match else 262144
    raw_variations: list[dict[str, Any]] = []
    for rows in row_choices:
        for cols in col_choices:
            capacity = rows * cols
            if capacity <= 0 or total_bits % capacity != 0:
                continue
            raw_variations.append(
                {
                    "rows": rows,
                    "cols": cols,
                    "num_arrays": total_bits // capacity,
                    "array_capacity_bits": capacity,
                }
            )
    return {
        "row_choices": row_choices,
        "column_choices": col_choices,
        "total_bits": total_bits,
        "raw_variations": raw_variations,
    }


def build_spec_field_source_matrix(
    *,
    openyield_root: Path,
    locked_spec: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    architecture = build_raw_architecture_summary(openyield_root)
    global_yaml_text = _read_text(openyield_root / "sram_compiler/config_yaml/global.yaml")
    raw_num_rows = int(re.search(r"num_rows:\s*(\d+)", global_yaml_text).group(1))
    raw_num_cols = int(re.search(r"num_cols:\s*(\d+)", global_yaml_text).group(1))
    choose_columnmux_match = re.search(r"choose_columnmux:\s*(true|false)", global_yaml_text, re.IGNORECASE)
    choose_columnmux = bool(choose_columnmux_match and choose_columnmux_match.group(1).lower() == "true")
    derived_spec = build_openyield_derived_spec(
        raw_num_rows=raw_num_rows,
        raw_num_cols=raw_num_cols,
        choose_columnmux=choose_columnmux,
        locked_spec=locked_spec,
    )
    rows: list[dict[str, Any]] = []

    def add_row(
        *,
        spec_field: str,
        value: Any,
        source_type: str,
        evidence: dict[str, Any] | None,
        is_raw_source_backed: bool,
        is_fallback: bool,
        fallback_source: str,
        fallback_reason: str,
        used_by_translator: bool,
    ) -> None:
        if source_type not in SOURCE_TYPES:
            raise ValueError(f"Unsupported source_type: {source_type}")
        rows.append(
            {
                "spec_field": spec_field,
                "value": value,
                "source_type": source_type,
                "raw_source_file": "" if evidence is None else evidence["raw_source_file"],
                "raw_source_line_start": "" if evidence is None else evidence["raw_source_line_start"],
                "raw_source_line_end": "" if evidence is None else evidence["raw_source_line_end"],
                "raw_source_snippet": "" if evidence is None else evidence["raw_source_snippet"],
                "source_hash": "" if evidence is None else evidence["source_hash"],
                "is_raw_source_backed": is_raw_source_backed,
                "is_fallback": is_fallback,
                "fallback_source": fallback_source,
                "fallback_reason": fallback_reason,
                "used_by_translator": used_by_translator,
            }
        )

    add_row(
        spec_field="word_size",
        value=locked_spec["word_size"],
        source_type="LOCKED_GOLDEN_FALLBACK",
        evidence=None,
        is_raw_source_backed=False,
        is_fallback=True,
        fallback_source="outputs/M8_reproduce_uploaded_golden/current_supported_config/SRAM_SPEC.json",
        fallback_reason="OpenYield raw source exposes num_cols, not a first-class logical word_size parameter.",
        used_by_translator=True,
    )
    add_row(
        spec_field="num_words",
        value=locked_spec["num_words"],
        source_type="LOCKED_GOLDEN_FALLBACK",
        evidence=None,
        is_raw_source_backed=False,
        is_fallback=True,
        fallback_source="outputs/M8_reproduce_uploaded_golden/current_supported_config/SRAM_SPEC.json",
        fallback_reason="OpenYield raw source exposes num_rows/num_cols and capacity goals, not a first-class logical num_words parameter.",
        used_by_translator=True,
    )
    add_row(
        spec_field="words_per_row",
        value=locked_spec["words_per_row"],
        source_type="LOCKED_GOLDEN_FALLBACK",
        evidence=None,
        is_raw_source_backed=False,
        is_fallback=True,
        fallback_source="outputs/M8_reproduce_uploaded_golden/current_supported_config/SRAM_SPEC.json",
        fallback_reason="Current translator current_supported_config keeps locked golden 8x64_wpr4; raw OpenYield only proves choose_columnmux -> ratio 1 or 2.",
        used_by_translator=True,
    )
    add_row(
        spec_field="num_rows",
        value=raw_num_rows,
        source_type="RAW_OPENYIELD_CONFIG",
        evidence=architecture["global_yaml"],
        is_raw_source_backed=True,
        is_fallback=False,
        fallback_source="",
        fallback_reason="",
        used_by_translator=True,
    )
    add_row(
        spec_field="num_cols",
        value=raw_num_cols,
        source_type="RAW_OPENYIELD_CONFIG",
        evidence=architecture["global_yaml"],
        is_raw_source_backed=True,
        is_fallback=False,
        fallback_source="",
        fallback_reason="",
        used_by_translator=True,
    )
    add_row(
        spec_field="num_banks",
        value=1,
        source_type="LOCKED_GOLDEN_FALLBACK",
        evidence=None,
        is_raw_source_backed=False,
        is_fallback=True,
        fallback_source="locked single-bank project scope",
        fallback_reason="OpenYield current source uses one implicit bank but does not expose a first-class num_banks config object.",
        used_by_translator=True,
    )
    add_row(
        spec_field="num_ports",
        value=1,
        source_type="LOCKED_GOLDEN_FALLBACK",
        evidence=None,
        is_raw_source_backed=False,
        is_fallback=True,
        fallback_source="locked single-port project scope",
        fallback_reason="OpenYield current source models one shared read/write port but does not expose a first-class num_ports config object.",
        used_by_translator=True,
    )
    add_row(
        spec_field="tech",
        value=locked_spec["tech"],
        source_type="LOCKED_GOLDEN_FALLBACK",
        evidence=None,
        is_raw_source_backed=False,
        is_fallback=True,
        fallback_source="outputs/M8_reproduce_uploaded_golden/current_supported_config/SRAM_SPEC.json",
        fallback_reason="OpenYield config tracks PDK paths but current translator locks delivery to the freepdk45 layoutgen flow.",
        used_by_translator=True,
    )
    add_row(
        spec_field="top_cell_name",
        value=locked_spec["top_cell_name"],
        source_type="LOCKED_GOLDEN_FALLBACK",
        evidence=None,
        is_raw_source_backed=False,
        is_fallback=True,
        fallback_source="outputs/M8_reproduce_uploaded_golden/current_supported_config/SRAM_SPEC.json",
        fallback_reason="Current supported config preserves the locked golden top-cell name for exact-match physical delivery.",
        used_by_translator=True,
    )
    add_row(
        spec_field="column_mux_ratio",
        value=derived_spec["column_mux_ratio"],
        source_type="DERIVED_FROM_RAW_SOURCE",
        evidence=architecture["testbench_mux"] or architecture["global_yaml"],
        is_raw_source_backed=True,
        is_fallback=False,
        fallback_source="",
        fallback_reason="",
        used_by_translator=True,
    )
    add_row(
        spec_field="mux_enabled",
        value=derived_spec["mux_enabled"],
        source_type="RAW_OPENYIELD_CONFIG",
        evidence=architecture["global_yaml"],
        is_raw_source_backed=True,
        is_fallback=False,
        fallback_source="",
        fallback_reason="",
        used_by_translator=True,
    )
    for field in [
        "dummy_enabled",
        "replica_enabled",
        "precharge_enabled",
        "sense_amp_enabled",
        "write_driver_enabled",
        "wordline_driver_enabled",
        "decoder_enabled",
    ]:
        add_row(
            spec_field=field,
            value=bool(locked_spec[field]),
            source_type="LOCKED_GOLDEN_FALLBACK",
            evidence=None,
            is_raw_source_backed=False,
            is_fallback=True,
            fallback_source="outputs/M8_reproduce_uploaded_golden/current_supported_config/SRAM_SPEC.json",
            fallback_reason="M11 preserves the M10/M8R physical feature set; no first-class raw OpenYield physical-feature toggle is consumed by the translator for this field.",
            used_by_translator=True,
        )
    add_row(
        spec_field="power_rail_overlap_enabled",
        value=bool(locked_spec["power_rail_overlap_enabled"]),
        source_type="LAYOUTGEN_DEFAULT",
        evidence=None,
        is_raw_source_backed=False,
        is_fallback=False,
        fallback_source="",
        fallback_reason="",
        used_by_translator=True,
    )
    add_row(
        spec_field="power_stitch_enabled",
        value=bool(locked_spec["power_stitch_enabled"]),
        source_type="LAYOUTGEN_DEFAULT",
        evidence=None,
        is_raw_source_backed=False,
        is_fallback=False,
        fallback_source="",
        fallback_reason="",
        used_by_translator=True,
    )
    add_row(
        spec_field="rail_abutment_enabled",
        value=bool(locked_spec["rail_abutment_enabled"]),
        source_type="LAYOUTGEN_DEFAULT",
        evidence=None,
        is_raw_source_backed=False,
        is_fallback=False,
        fallback_source="",
        fallback_reason="",
        used_by_translator=True,
    )
    return rows, {
        "raw_num_rows": raw_num_rows,
        "raw_num_cols": raw_num_cols,
        "raw_choose_columnmux": choose_columnmux,
        "derived_spec": derived_spec,
        "openyield_capacity_config_found": True,
        "word_size_source_backed": False,
        "num_words_source_backed": False,
        "words_per_row_source_backed": False,
        "num_rows_source_backed": True,
        "num_cols_source_backed": True,
        "capacity_config_fallback_used_after_M11": True,
        "fallback_reason": "Raw OpenYield provides architecture knobs (num_rows/num_cols/choose_columnmux) but not enough first-class logical capacity fields to eliminate the locked 8x64_wpr4 fallback for current_supported_config delivery.",
    }


def render_inventory_md(rows: list[dict[str, Any]]) -> str:
    lines = ["# M11 Config Candidate Inventory", ""]
    for row in rows:
        lines.append(
            f"- `{row['candidate_id']}` `{row['relative_path']}` category=`{row['category']}` "
            f"keywords=`{row['matched_keywords']}`"
        )
    return "\n".join(lines) + "\n"


def render_source_matrix_md(rows: list[dict[str, Any]]) -> str:
    lines = ["# M11 Spec Field Source Matrix", ""]
    for row in rows:
        lines.append(
            f"- `{row['spec_field']}` = `{row['value']}` source_type=`{row['source_type']}` "
            f"raw_backed=`{row['is_raw_source_backed']}` fallback=`{row['is_fallback']}`"
        )
    return "\n".join(lines) + "\n"


def render_trace_md(trace: dict[str, Any]) -> str:
    derived = trace["derived_spec"]
    lines = [
        "# M11 Config Extraction Trace",
        "",
        f"- raw_num_rows: `{trace['raw_num_rows']}`",
        f"- raw_num_cols: `{trace['raw_num_cols']}`",
        f"- raw_choose_columnmux: `{trace['raw_choose_columnmux']}`",
        f"- derived_word_size: `{derived['word_size']}`",
        f"- derived_num_words: `{derived['num_words']}`",
        f"- derived_words_per_row: `{derived['words_per_row']}`",
        f"- capacity_config_fallback_used_after_M11: `{trace['capacity_config_fallback_used_after_M11']}`",
        f"- fallback_reason: `{trace['fallback_reason']}`",
        "",
    ]
    return "\n".join(lines)


def write_extractor_outputs(
    *,
    out_dir: Path,
    mapping_dir: Path,
    candidate_rows: list[dict[str, Any]],
    source_matrix_rows: list[dict[str, Any]],
    extraction_trace: dict[str, Any],
    variation_summary: dict[str, Any],
) -> None:
    write_csv(out_dir / "M11_config_candidate_inventory.csv", CONFIG_CANDIDATE_FIELDS, candidate_rows)
    write_text(out_dir / "M11_config_candidate_inventory.md", render_inventory_md(candidate_rows))
    write_csv(out_dir / "M11_spec_field_source_matrix.csv", SPEC_FIELD_SOURCE_FIELDS, source_matrix_rows)
    write_text(out_dir / "M11_spec_field_source_matrix.md", render_source_matrix_md(source_matrix_rows))
    write_json(out_dir / "M11_config_extraction_trace.json", extraction_trace)
    write_text(out_dir / "M11_config_extraction_trace.md", render_trace_md(extraction_trace))
    write_csv(mapping_dir / "M11_config_candidate_inventory.csv", CONFIG_CANDIDATE_FIELDS, candidate_rows)
    write_csv(mapping_dir / "M11_spec_field_source_matrix.csv", SPEC_FIELD_SOURCE_FIELDS, source_matrix_rows)

    variation_rows = [
        {
            "variation_id": index + 1,
            "rows": item["rows"],
            "cols": item["cols"],
            "num_arrays": item["num_arrays"],
            "array_capacity_bits": item["array_capacity_bits"],
        }
        for index, item in enumerate(variation_summary["raw_variations"])
    ]
    write_csv(
        mapping_dir / "M11_variation_support_matrix.csv",
        ["variation_id", "rows", "cols", "num_arrays", "array_capacity_bits"],
        variation_rows,
    )


def parse_variation_text(text: str) -> dict[str, int]:
    match = re.fullmatch(r"(?P<word>\d+)x(?P<words>\d+)_wpr(?P<wpr>\d+)", text.strip())
    if not match:
        raise ValueError(f"Unsupported variation text: {text}")
    return {
        "word_size": int(match.group("word")),
        "num_words": int(match.group("words")),
        "words_per_row": int(match.group("wpr")),
    }


def variation_to_openyield_dimensions(word_size: int, num_words: int, words_per_row: int) -> dict[str, Any]:
    if words_per_row <= 0:
        raise ValueError("words_per_row must be positive")
    if num_words % words_per_row != 0:
        raise ValueError("num_words must be divisible by words_per_row")
    return {
        "word_size": word_size,
        "num_words": num_words,
        "words_per_row": words_per_row,
        "num_rows": num_words // words_per_row,
        "num_cols": word_size * words_per_row,
        "column_mux_ratio": words_per_row,
        "choose_columnmux": words_per_row > 1,
        "addr_bits": max(1, math.ceil(math.log2(max(1, num_words)))),
    }
