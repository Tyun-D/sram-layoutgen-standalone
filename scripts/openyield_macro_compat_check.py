from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
REPO_ROOT = STANDALONE_ROOT.parents[1]
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))

from sram_layoutgen.openyield_adapter.macro_compat import check_contract_payload, load_contract_payload  # noqa: E402


FOCUS_MODULES = (
    "SRAM_6T_CELL",
    "SRAM_6T_CORE_*",
    "Dummy_CELL",
    "Dummy_Row",
    "Dummy_Column",
    "Replica_CELL",
    "Replica_Column",
    "PRECHARGE",
    "WRITEDRIVER",
    "SENSEAMP",
    "COLUMNMUX*",
    "DECODER3_8",
    "DECODER_CASCADE",
    "WORDLINEDRIVER",
    "DFF",
    "ADDR_DFF",
    "DATA_DFF",
    "delay_chain",
    "wen_delay_chain",
    "TIME",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check OpenYield contracts against replacement macro metadata.")
    parser.add_argument("--contracts", default="docs/openyield_module_contracts.json")
    parser.add_argument("--tech-dir", default="technology/freepdk45")
    parser.add_argument("--out-json", default="docs/openyield_macro_compat_report.json")
    parser.add_argument("--out-md", default="docs/openyield_macro_compat_report.md")
    args = parser.parse_args()

    contracts_path = resolve_input(args.contracts)
    tech_dir = resolve_input(args.tech_dir)
    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)

    contracts_payload = load_contract_payload(contracts_path)
    report = check_contract_payload(contracts_payload, tech_dir)
    report["contracts_path"] = str(contracts_path.resolve())
    report["tech_dir"] = str(tech_dir.resolve())
    report["focus_modules"] = FOCUS_MODULES
    report["missing_focus_modules"] = sorted(set(FOCUS_MODULES) - {item["original_module_name"] for item in report["compatibilities"]})

    smoke_assertions(contracts_payload, report)

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    out_md.write_text(format_markdown(report), encoding="utf-8", newline="\n")
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    summary = report["summary"]
    print(
        "contracts="
        f"{report['contract_count']} matched_existing_macro={len(summary['matched_existing_macro'])} "
        f"missing_macro={len(summary['candidate_macro_missing'])} "
        f"pin_mismatch={len(summary['macro_exists_pin_mismatch'])} "
        f"composite={len(summary['composite_required'])}"
    )
    return 0


def resolve_input(value: str) -> Path:
    path = Path(value)
    if path.exists():
        return path
    for base in (Path.cwd(), STANDALONE_ROOT, REPO_ROOT):
        candidate = base / value
        if candidate.exists():
            return candidate
    return path


def resolve_output(value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    if Path.cwd().resolve() == REPO_ROOT.resolve():
        return STANDALONE_ROOT / value
    return Path.cwd() / value


def smoke_assertions(contracts_payload: dict[str, Any], report: dict[str, Any]) -> None:
    contracts = {item["original_module_name"]: item for item in contracts_payload.get("contracts", [])}
    compat = {item["original_module_name"]: item for item in report.get("compatibilities", [])}
    assert_pin(contracts, "PRECHARGE", "ENB", "precharge_enb")
    assert_pin(contracts, "WRITEDRIVER", "EN", "write_enable")
    assert_pin(contracts, "SENSEAMP", "IN", "bl")
    assert_pin(contracts, "SENSEAMP", "INB", "br")
    assert_pin(contracts, "WORDLINEDRIVER", "Z", "wl")
    assert compat["TIME"]["implementation_status"] == "composite_required"
    if "SRAM_10T_CELL" in compat:
        assert compat["SRAM_10T_CELL"]["implementation_status"] == "unsupported_architecture"
    if "SRAM_10T_CORE_*" in compat:
        assert compat["SRAM_10T_CORE_*"]["implementation_status"] == "unsupported_architecture"
    non_layout_names = [
        item["original_module_name"]
        for item in contracts.values()
        if "testbenches/" in str(item.get("source_file", "")).lower()
        or "factory" in str(item.get("class_name", "")).lower()
        or "testbench" in str(item.get("class_name", "")).lower()
    ]
    for name in non_layout_names:
        assert compat[name]["implementation_status"] == "non_layout_source"


def assert_pin(contracts: dict[str, Any], module: str, original_pin: str, canonical: str) -> None:
    item = contracts[module]
    matches = [pin for pin in item.get("pins", []) if pin.get("original_name") == original_pin]
    assert matches, f"{module}.{original_pin} missing from contract"
    assert matches[0].get("canonical_name") == canonical, (
        f"{module}.{original_pin} expected {canonical}, got {matches[0].get('canonical_name')}"
    )


def format_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    rows = []
    for item in report["compatibilities"]:
        rows.append(
            [
                item["original_module_name"],
                item["role"],
                item["implementation_status"],
                ", ".join(item["candidate_macros"]) or "-",
                ", ".join(item["existing_macros"]) or "-",
                item["selected_macro"] or "-",
                _pin_status_summary(item),
                item["power_status"],
                item["aggregation_status"],
                "; ".join(item["notes"]) or "-",
            ]
        )
    return "\n".join(
        [
            "# OpenYield Macro Compatibility Report",
            "",
            "This report statically compares OpenYield ModuleContract data against `technology/freepdk45/replacement_macros.json`. It does not modify placement, routing, GDS generation, or OpenYield source.",
            "",
            "## Inputs",
            "",
            f"- contracts: `{report['contracts_path']}`",
            f"- tech dir: `{report['tech_dir']}`",
            f"- contract count: `{report['contract_count']}`",
            f"- replacement macro count: `{report['replacement_macro_count']}`",
            f"- alias count: `{report.get('alias_count', 0)}`",
            f"- catalog macro count: `{report.get('catalog_macro_count', report['replacement_macro_count'])}`",
            f"- missing focus modules: `{', '.join(report['missing_focus_modules']) or 'none'}`",
            "",
            "## Summary",
            "",
            "```json",
            json.dumps(summary, ensure_ascii=False, indent=2),
            "```",
            "",
            "## Compatibility Table",
            "",
            md_table(
                [
                    "module",
                    "role",
                    "implementation",
                    "candidate macros",
                    "existing macros",
                    "selected macro",
                    "pin checks",
                    "power",
                    "aggregation",
                    "notes",
                ],
                rows,
            ),
            "",
            "## Existing Macro Matches",
            "",
            list_block(summary["matched_existing_macro"]),
            "",
            "## Candidate Macro Missing",
            "",
            list_block(summary["candidate_macro_missing"]),
            "",
            "## Macro Exists But Pin Mismatch",
            "",
            list_block(summary["macro_exists_pin_mismatch"]),
            "",
            "## Composite Modules",
            "",
            list_block(summary["composite_required"]),
            "",
            "## Unsupported Architecture",
            "",
            list_block(summary["unsupported_architecture"]),
            "",
            "## Non-Layout Sources",
            "",
            list_block(summary["non_layout_source"]),
            "",
            "## VDD/GND Shared Rail Risks",
            "",
            list_block(summary["vdd_gnd_shared_rail_risks"]),
            "",
            "## Next Missing Alias Or Macro Work",
            "",
            "- Add replacement macro metadata for hardcell macros that already exist as GDS but are not listed in `replacement_macros.json`, such as bitcell, dummy, replica, sense amp, write driver, and DFF cells.",
            "- Confirm `WORDLINEDRIVER.A/B` semantics before physical routing; current contract marks `A -> decoder_input`, `B -> wordline_enable`, and `Z -> wl` with `needs_semantic_confirmation`.",
            "- Use full GDS pin-shape audits before enabling abutment or shared rails for generated replacement macros.",
        ]
    )


def _pin_status_summary(item: dict[str, Any]) -> str:
    counts: dict[str, int] = {}
    for check in item.get("pin_checks", []):
        status = check["status"]
        counts[status] = counts.get(status, 0) + 1
    return ", ".join(f"{key}:{value}" for key, value in sorted(counts.items())) or "-"


def list_block(items: list[str]) -> str:
    if not items:
        return "none"
    return "\n".join(f"- `{item}`" for item in items)


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(out)


if __name__ == "__main__":
    raise SystemExit(main())
