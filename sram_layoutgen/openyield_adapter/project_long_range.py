from __future__ import annotations

import csv
import hashlib
import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sram_layoutgen.openyield_adapter.openyield_config_extractor import (
    build_variation_support_summary,
    parse_variation_text,
    variation_to_openyield_dimensions,
)


FORBIDDEN_CLAIMS = [
    "tapeout-ready",
    "foundry signoff passed",
    "silicon-proven",
    "full external signoff",
]

NEGATIVE_GUARD_PATTERNS = [
    r"cannot claim",
    r"can not claim",
    r"not ",
    r"no ",
    r"without ",
    r"未",
    r"不是",
    r"不得",
    r"不能",
]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def parse_sram_top_name(name: str) -> dict[str, int | None]:
    if name == "sram_1rw_32x16_freepdk45":
        return {
            "word_size": 16,
            "num_words": 32,
            "words_per_row": 1,
            "num_rows": 32,
            "num_cols": 16,
            "num_banks": 1,
        }
    match = re.fullmatch(r"sram_(\d+)x(\d+)_wpr(\d+)_fd45", name)
    if not match:
        return {
            "word_size": None,
            "num_words": None,
            "words_per_row": None,
            "num_rows": None,
            "num_cols": None,
            "num_banks": None,
        }
    word_size = int(match.group(1))
    num_words = int(match.group(2))
    words_per_row = int(match.group(3))
    return {
        "word_size": word_size,
        "num_words": num_words,
        "words_per_row": words_per_row,
        "num_rows": num_words // words_per_row,
        "num_cols": word_size * words_per_row,
        "num_banks": 1,
    }


def addr_width(num_words: int | None) -> int | None:
    if num_words is None or num_words <= 0:
        return None
    return int(math.log2(num_words)) if num_words & (num_words - 1) == 0 else None


def build_formal_sram_config_schema() -> dict[str, Any]:
    return {
        "schema_name": "FORMAL_SRAM_CONFIG_SCHEMA",
        "schema_version": "2026-07-26",
        "fields": [
            {"name": "config_id", "type": "string", "required": True},
            {"name": "top_cell_name", "type": "string", "required": False},
            {"name": "word_size", "type": "integer", "required": True},
            {"name": "num_words", "type": "integer", "required": True},
            {"name": "words_per_row", "type": "integer", "required": True},
            {"name": "num_rows", "type": "integer", "required": True},
            {"name": "num_cols", "type": "integer", "required": True},
            {"name": "addr_width", "type": "integer", "required": False},
            {"name": "num_banks", "type": "integer", "required": True},
            {"name": "num_ports", "type": "integer", "required": True},
            {"name": "source_authority", "type": "enum", "required": True, "values": ["OPENYIELD_RAW_VARIATION", "M2R_LOCKED_SPEC", "HISTORICAL_GDS_NAME_DERIVED", "OPENRAM_REFERENCE_NAME_DERIVED"]},
            {"name": "support_level", "type": "enum", "required": True, "values": ["FULLY_SUPPORTED", "SUPPORTED_WITH_CONSTRAINTS", "PARTIALLY_SUPPORTED", "EXPERIMENTAL", "ROADMAP"]},
            {"name": "inventory_status", "type": "enum", "required": True, "values": ["CURRENT_SOURCE_BACKED", "CURRENT_LOCKED_BASELINE", "HISTORICAL_EVIDENCE_ONLY", "REFERENCE_ONLY"]},
            {"name": "evidence_path", "type": "string", "required": True},
            {"name": "evidence_sha", "type": "string", "required": False},
        ],
        "validation_rules": [
            "num_rows * words_per_row == num_words",
            "num_cols / words_per_row == word_size",
            "addr_width = log2(num_words) when num_words is a power of two",
            "num_banks stays 1 unless a canonical multi-bank source contract exists",
        ],
        "degrade_policy": "Rows without raw-source-backed authority stay in the inventory but must use HISTORICAL_EVIDENCE_ONLY or REFERENCE_ONLY inventory_status.",
    }


@dataclass(frozen=True)
class FormalConfig:
    config_id: str
    top_cell_name: str
    word_size: int
    num_words: int
    words_per_row: int
    num_rows: int
    num_cols: int
    addr_width: int | None
    num_banks: int
    num_ports: int
    source_authority: str
    support_level: str
    inventory_status: str
    evidence_path: str
    evidence_sha: str
    notes: str


def build_formal_sram_config_inventory(
    *,
    repo_root: Path,
    source_tree: Path,
    openyield_root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    variation_report = read_json(source_tree / "outputs/M11_openyield_config_variation/current_supported_config/M11_variation_support_report.json")
    m2r_locked = read_json(source_tree / "outputs/M2R_full_sram_regen/current_supported_config/M2R_locked_sram_spec.json")
    inventory_rows = read_csv(repo_root / "docs/SRAM_CONFIGURATION_INVENTORY.csv")
    bank_contract = read_json(repo_root / "docs/mapping/openyield_top_bank_semantic_contract.json")
    variation_summary = build_variation_support_summary(openyield_root)
    raw_variations = {(row["rows"], row["cols"]): row for row in variation_summary["raw_variations"]}

    configs: list[FormalConfig] = []
    binding_rows: list[dict[str, Any]] = []

    def add_binding(
        *,
        config_id: str,
        field_name: str,
        value: Any,
        binding_type: str,
        authority_path: str,
        authority_sha: str,
        evidence_kind: str,
        source_backed: bool,
        degraded: bool,
        note: str,
    ) -> None:
        binding_rows.append(
            {
                "config_id": config_id,
                "field_name": field_name,
                "value": value,
                "binding_type": binding_type,
                "authority_path": authority_path,
                "authority_sha": authority_sha,
                "evidence_kind": evidence_kind,
                "source_backed": source_backed,
                "degraded": degraded,
                "note": note,
            }
        )

    supported_variations = variation_report["supported_variations"]
    m11_report_path = source_tree / "outputs/M11_openyield_config_variation/current_supported_config/M11_variation_support_report.json"
    m11_report_sha = sha256_file(m11_report_path)
    experiment_path = openyield_root / "size_optimization/experiment.py"
    experiment_sha = sha256_file(experiment_path)
    bank_contract_path = repo_root / "docs/mapping/openyield_top_bank_semantic_contract.json"
    bank_contract_sha = sha256_file(bank_contract_path)
    m2r_locked_path = source_tree / "outputs/M2R_full_sram_regen/current_supported_config/M2R_locked_sram_spec.json"
    m2r_locked_sha = sha256_file(m2r_locked_path)

    for variation_text in supported_variations:
        parsed = parse_variation_text(variation_text)
        dims = variation_to_openyield_dimensions(
            parsed["word_size"], parsed["num_words"], parsed["words_per_row"]
        )
        config_id = f"formal_{variation_text}"
        configs.append(
            FormalConfig(
                config_id=config_id,
                top_cell_name=f"sram_{variation_text}_fd45",
                word_size=parsed["word_size"],
                num_words=parsed["num_words"],
                words_per_row=parsed["words_per_row"],
                num_rows=dims["num_rows"],
                num_cols=dims["num_cols"],
                addr_width=addr_width(parsed["num_words"]),
                num_banks=1,
                num_ports=1,
                source_authority="OPENYIELD_RAW_VARIATION",
                support_level="SUPPORTED_WITH_CONSTRAINTS",
                inventory_status="CURRENT_SOURCE_BACKED",
                evidence_path=f"{m11_report_path}; {experiment_path}",
                evidence_sha=f"{m11_report_sha}; {experiment_sha}",
                notes="Variation is backed by OpenYield row/column choice space and current project translation rules.",
            )
        )
        raw_var = raw_variations.get((dims["num_rows"], dims["num_cols"]), {})
        for field_name, value, binding_type, authority_path, authority_sha, note in [
            ("word_size", parsed["word_size"], "DERIVED_FROM_RAW_VARIATION", str(experiment_path), experiment_sha, "Derived from raw row/column variation plus words_per_row."),
            ("num_words", parsed["num_words"], "DERIVED_FROM_RAW_VARIATION", str(experiment_path), experiment_sha, "Derived from num_rows * words_per_row."),
            ("words_per_row", parsed["words_per_row"], "PROJECT_MUX_RULE", str(m11_report_path), m11_report_sha, "Current project only proves mux ratios 1/2/4 from explicit supported variations."),
            ("num_rows", dims["num_rows"], "RAW_VARIATION_SPACE", str(experiment_path), experiment_sha, f"Row choice present in experiment variation space with num_arrays={raw_var.get('num_arrays', '')}."),
            ("num_cols", dims["num_cols"], "RAW_VARIATION_SPACE", str(experiment_path), experiment_sha, "Column choice present in experiment variation space."),
            ("addr_width", addr_width(parsed["num_words"]), "DERIVED_FROM_LOGICAL_NUM_WORDS", str(m11_report_path), m11_report_sha, "Derived from num_words."),
            ("num_banks", bank_contract["BANK"]["bank_count_supported"], "CANONICAL_SINGLE_BANK_CONTRACT", str(bank_contract_path), bank_contract_sha, "Current canonical top-bank contract supports exactly one bank."),
            ("num_ports", 1, "CANONICAL_SINGLE_PORT_CONTRACT", str(bank_contract_path), bank_contract_sha, "Current canonical SRAM top contract uses one shared read/write port."),
        ]:
            add_binding(
                config_id=config_id,
                field_name=field_name,
                value=value,
                binding_type=binding_type,
                authority_path=authority_path,
                authority_sha=authority_sha,
                evidence_kind="raw_or_derived",
                source_backed=True,
                degraded=False,
                note=note,
            )

    configs.append(
        FormalConfig(
            config_id="formal_current_locked_8x64_wpr4",
            top_cell_name="openyield_layoutgen_full_sram_M2R",
            word_size=int(m2r_locked["word_size"]),
            num_words=int(m2r_locked["num_words"]),
            words_per_row=int(m2r_locked["words_per_row"]),
            num_rows=int(m2r_locked["num_rows"]),
            num_cols=int(m2r_locked["num_cols"]),
            addr_width=addr_width(int(m2r_locked["num_words"])),
            num_banks=int(m2r_locked["num_banks"]),
            num_ports=int(m2r_locked["num_ports"]),
            source_authority="M2R_LOCKED_SPEC",
            support_level="SUPPORTED_WITH_CONSTRAINTS",
            inventory_status="CURRENT_LOCKED_BASELINE",
            evidence_path=str(m2r_locked_path),
            evidence_sha=m2r_locked_sha,
            notes="Current physical top-level delivery remains bound to the M2R locked spec.",
        )
    )
    for field_name in ["word_size", "num_words", "words_per_row", "num_rows", "num_cols", "num_banks", "num_ports"]:
        add_binding(
            config_id="formal_current_locked_8x64_wpr4",
            field_name=field_name,
            value=m2r_locked[field_name],
            binding_type="LOCKED_FORMAL_SPEC",
            authority_path=str(m2r_locked_path),
            authority_sha=m2r_locked_sha,
            evidence_kind="locked_spec",
            source_backed=field_name in {"num_rows", "num_cols"},
            degraded=False,
            note="Current shipped full-SRAM trial uses the locked M2R spec.",
        )

    for row in inventory_rows:
        config_id = row["config_id"]
        if row["config_id"] == "cfg_8x64_wpr4":
            continue
        if row["config_id"] in {"cfg_16x16_wpr1", "cfg_4x32_wpr2"}:
            continue
        top_guess = ""
        evidence_path = row["evidence_path"]
        if "::" in evidence_path:
            suffix = evidence_path.split("::", 1)[1]
            top_guess = Path(suffix).name
            if top_guess.endswith(".complete.gds"):
                top_guess = top_guess.replace(".complete.gds", "").split("__")[-1]
            elif top_guess.endswith(".gds"):
                top_guess = top_guess.replace(".gds", "")
        if not top_guess:
            top_guess = row["config_id"]
        parsed = parse_sram_top_name(top_guess)
        if parsed["word_size"] is None:
            continue
        inventory_status = "REFERENCE_ONLY" if config_id == "cfg_openram_32x16_reference" else "HISTORICAL_EVIDENCE_ONLY"
        source_authority = "OPENRAM_REFERENCE_NAME_DERIVED" if config_id == "cfg_openram_32x16_reference" else "HISTORICAL_GDS_NAME_DERIVED"
        support_level = "EXPERIMENTAL" if config_id == "cfg_openram_32x16_reference" else "PARTIALLY_SUPPORTED"
        configs.append(
            FormalConfig(
                config_id=config_id,
                top_cell_name=top_guess,
                word_size=int(parsed["word_size"]),
                num_words=int(parsed["num_words"]),
                words_per_row=int(parsed["words_per_row"]),
                num_rows=int(parsed["num_rows"]),
                num_cols=int(parsed["num_cols"]),
                addr_width=addr_width(int(parsed["num_words"])),
                num_banks=int(parsed["num_banks"]),
                num_ports=1,
                source_authority=source_authority,
                support_level=support_level,
                inventory_status=inventory_status,
                evidence_path=evidence_path,
                evidence_sha=sha256_text(evidence_path),
                notes="Recovered from historical explicit GDS naming/evidence rather than current raw OpenYield authority.",
            )
        )
        for field_name in ["word_size", "num_words", "words_per_row", "num_rows", "num_cols", "addr_width", "num_banks"]:
            add_binding(
                config_id=config_id,
                field_name=field_name,
                value=parsed[field_name] if field_name != "addr_width" else addr_width(int(parsed["num_words"])),
                binding_type=source_authority,
                authority_path=evidence_path,
                authority_sha=sha256_text(evidence_path),
                evidence_kind="historical_manifest" if config_id != "cfg_openram_32x16_reference" else "openram_reference",
                source_backed=False,
                degraded=True,
                note="Kept in explicit inventory, but downgraded because it is not backed by current raw OpenYield config authority.",
            )

    config_rows = [config.__dict__.copy() for config in configs]
    counts = {
        "total_configs": len(config_rows),
        "inventory_status_counts": {},
        "support_level_counts": {},
    }
    for row in config_rows:
        counts["inventory_status_counts"][row["inventory_status"]] = counts["inventory_status_counts"].get(row["inventory_status"], 0) + 1
        counts["support_level_counts"][row["support_level"]] = counts["support_level_counts"].get(row["support_level"], 0) + 1
    summary = {
        "schema_name": "FORMAL_SRAM_CONFIG_INVENTORY",
        "source_backed_variation_count": len(supported_variations),
        "locked_baseline_count": 1,
        "degraded_historical_count": sum(1 for row in config_rows if row["inventory_status"] in {"HISTORICAL_EVIDENCE_ONLY", "REFERENCE_ONLY"}),
        "counts": counts,
    }
    return config_rows, binding_rows, summary


def validate_formal_sram_config_inventory(rows: list[dict[str, Any]]) -> dict[str, Any]:
    required_fields = [
        "config_id",
        "word_size",
        "num_words",
        "words_per_row",
        "num_rows",
        "num_cols",
        "num_banks",
        "num_ports",
        "support_level",
        "inventory_status",
    ]
    errors: list[str] = []
    for row in rows:
        for field in required_fields:
            if row.get(field, "") in {"", None}:
                errors.append(f"{row.get('config_id', 'unknown')} missing {field}")
        if int(row["num_rows"]) * int(row["words_per_row"]) != int(row["num_words"]):
            errors.append(f"{row['config_id']} num_rows * words_per_row != num_words")
        if int(row["num_cols"]) // int(row["words_per_row"]) != int(row["word_size"]):
            errors.append(f"{row['config_id']} num_cols / words_per_row != word_size")
    return {
        "valid": not errors,
        "error_count": len(errors),
        "errors": errors,
    }


def assess_owner_confirmation_evidence(paths: list[Path]) -> dict[str, Any]:
    patterns = {
        "actual_author_or_scope": [r"OWNER_A_LOGICAL_DATA_MODEL_V1", r"正式作者", r"归属范围", r"author"],
        "canonical_source": [r"canonical source", r"规范源码", r"source files", r"recover into git"],
        "bundle_to_source_match": [r"review bundle", r"对应", r"canonical source"],
        "recovery_authorization": [r"授权", r"recover", r"回收到 Git", r"回收到当前项目分支"],
        "report_author_attribution": [r"作者贡献", r"Owner A", r"归属"],
    }
    findings: dict[str, dict[str, Any]] = {}
    for key, pats in patterns.items():
        findings[key] = {"matched": False, "hits": []}
        for path in paths:
            if not path.exists():
                continue
            text = path.read_text(encoding="utf-8")
            for pat in pats:
                if re.search(pat, text, re.IGNORECASE):
                    findings[key]["matched"] = True
                    findings[key]["hits"].append({"path": str(path), "pattern": pat})
    all_confirmed = all(item["matched"] for item in findings.values())
    return {
        "all_five_confirmed": all_confirmed,
        "findings": findings,
    }


def check_claim_policy(paths: list[Path]) -> dict[str, Any]:
    violations: list[dict[str, Any]] = []
    for path in paths:
        if not path.exists():
            continue
        lines = path.read_text(encoding="utf-8").splitlines()
        for line_no, line in enumerate(lines, start=1):
            lowered = line.lower()
            for claim in FORBIDDEN_CLAIMS:
                if claim in lowered:
                    window = lowered[max(0, lowered.index(claim) - 32) : lowered.index(claim) + len(claim) + 32]
                    guarded = any(re.search(pattern, window) for pattern in NEGATIVE_GUARD_PATTERNS)
                    if not guarded:
                        violations.append(
                            {
                                "path": str(path),
                                "line": line_no,
                                "claim": claim,
                                "text": line.strip(),
                            }
                        )
    return {
        "forbidden_claims": FORBIDDEN_CLAIMS,
        "checked_file_count": len(paths),
        "violation_count": len(violations),
        "violations": violations,
        "passed": not violations,
    }
