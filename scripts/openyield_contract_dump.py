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

from sram_layoutgen.openyield_adapter import build_module_contracts  # noqa: E402


REQUIRED_MODULES = {
    "PRECHARGE",
    "WRITEDRIVER",
    "SENSEAMP",
    "COLUMNMUX*",
    "SRAM_6T_CELL",
    "SRAM_6T_CORE_*",
    "DECODER3_8",
    "DECODER_CASCADE",
    "WORDLINEDRIVER",
    "Dummy_CELL",
    "Replica_CELL",
    "TIME",
    "DFF",
    "ADDR_DFF",
    "DATA_DFF",
    "delay_chain",
    "wen_delay_chain",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Dump canonical OpenYield ModuleContract data.")
    parser.add_argument("--openyield-root", default="third_party/OpenYield")
    parser.add_argument("--out-json", default="docs/openyield_module_contracts.json")
    parser.add_argument("--out-md", default="docs/openyield_module_contracts.md")
    args = parser.parse_args()

    openyield_root = resolve_path(args.openyield_root)
    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)
    contracts, warnings = build_module_contracts(str(openyield_root))

    names = {contract.original_module_name for contract in contracts}
    missing_required = sorted(REQUIRED_MODULES - names)
    unknown = [contract for contract in contracts if contract.role == "unknown"]
    no_physical = [
        contract
        for contract in contracts
        if contract.requires_physical_implementation and not contract.gds_macro_candidates
    ]
    payload = {
        "openyield_root": str(openyield_root.resolve()),
        "scan_paths": [
            str((openyield_root / "sram_compiler" / "subcircuits").resolve()),
            str((openyield_root / "sram_compiler" / "testbenches").resolve()),
        ],
        "module_count": len(contracts),
        "contracts": [contract.to_dict() for contract in contracts],
        "warnings": warnings,
        "missing_required_modules": missing_required,
        "unknown_role_modules": [contract.to_dict() for contract in unknown],
        "modules_without_physical_candidate": [contract.to_dict() for contract in no_physical],
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    out_md.write_text(format_markdown(payload), encoding="utf-8", newline="\n")

    if missing_required:
        print(f"ERROR missing required contracts: {', '.join(missing_required)}", file=sys.stderr)
        return 2
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(
        "contracts="
        f"{len(contracts)} unknown_roles={len(unknown)} "
        f"no_physical_candidates={len(no_physical)} warnings={len(warnings)}"
    )
    return 0


def resolve_path(value: str) -> Path:
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


def format_markdown(payload: dict[str, Any]) -> str:
    contracts = payload["contracts"]
    rows = []
    for item in contracts:
        rows.append(
            [
                item.get("source_file") or "-",
                item.get("class_name") or "-",
                item["original_module_name"],
                item["canonical_module_name"],
                item["role"],
                ", ".join(pin["original_name"] for pin in item["pins"]) or "-",
                ", ".join(f"{pin['original_name']}->{pin['canonical_name']}" for pin in item["pins"]) or "-",
                json.dumps(item["power_pins"], ensure_ascii=False),
                ", ".join(item["gds_macro_candidates"]) or "-",
                "; ".join(item["warnings"]) or "-",
            ]
        )
    unknown_rows = [
        [
            item.get("source_file") or "-",
            item.get("class_name") or "-",
            item["original_module_name"],
            item["role"],
        ]
        for item in payload["unknown_role_modules"]
    ]
    no_physical_rows = [
        [
            item.get("source_file") or "-",
            item.get("class_name") or "-",
            item["original_module_name"],
            item["role"],
            "; ".join(item["notes"]) or "-",
        ]
        for item in payload["modules_without_physical_candidate"]
    ]
    role_counts: dict[str, int] = {}
    for item in contracts:
        role_counts[item["role"]] = role_counts.get(item["role"], 0) + 1
    return "\n".join(
        [
            "# OpenYield Module Contracts",
            "",
            "This report is generated by `scripts/openyield_contract_dump.py` through static AST parsing of OpenYield PySpice source. It does not import OpenYield, run Xyce/PySpice, or connect to the main GDS generation flow.",
            "",
            "## Summary",
            "",
            f"- OpenYield root: `{payload['openyield_root']}`",
            f"- scan paths: `{'; '.join(payload['scan_paths'])}`",
            f"- parsed module contracts: `{payload['module_count']}`",
            f"- missing required modules: `{', '.join(payload['missing_required_modules']) or 'none'}`",
            f"- parser warnings: `{len(payload['warnings'])}`",
            "",
            "Role counts:",
            "",
            "```json",
            json.dumps(role_counts, ensure_ascii=False, indent=2),
            "```",
            "",
            "## Contract Table",
            "",
            md_table(
                [
                    "source file",
                    "class",
                    "original module",
                    "canonical module",
                    "role",
                    "original pins",
                    "canonical pins",
                    "power mapping",
                    "GDS macro candidates",
                    "warnings",
                ],
                rows,
            ),
            "",
            "## Unknown Role Modules",
            "",
            md_table(["source file", "class", "original module", "role"], unknown_rows)
            if unknown_rows
            else "none",
            "",
            "## Modules Without Physical Candidate",
            "",
            md_table(["source file", "class", "original module", "role", "notes"], no_physical_rows)
            if no_physical_rows
            else "none",
            "",
            "## Next Integration Notes",
            "",
            "- Cross-check `gds_macro_candidates` against `technology/freepdk45/replacement_macros.json` in both directions.",
            "- Build architecture/control contracts for composite modules such as `TIME`, `ADDR_DFF`, `DATA_DFF`, and `delay_chain`; do not flatten them into one physical GDS macro.",
            "- Reuse these canonical pins and power aliases in the future aggregation/abutment cell abstraction so placement and routing do not continue to hand-code pin spellings.",
        ]
    )


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(out)


if __name__ == "__main__":
    raise SystemExit(main())
