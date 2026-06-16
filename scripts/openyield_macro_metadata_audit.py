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

from sram_layoutgen.openyield_adapter.aggregation import aggregation_status_for_contract  # noqa: E402
from sram_layoutgen.openyield_adapter.macro_compat import (  # noqa: E402
    build_macro_catalog,
    check_contract_payload,
    discover_library_macros,
    load_contract_payload,
    load_macro_aliases,
    load_replacement_macros,
)


FOCUS_NAMES = (
    "cell_1rw",
    "cell_2rw",
    "cell_6t",
    "dummy_cell_1rw",
    "dummy_cell_2rw",
    "replica_cell_1rw",
    "replica_cell_2rw",
    "sense_amp",
    "write_driver",
    "tri_gate",
    "dff",
    "precharge",
    "gen_precharge",
    "gen_col_mux",
    "gen_wl_driver",
    "gen_nand2",
    "gen_nand4",
    "row_decoder",
    "wordline_driver",
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit OpenYield macro metadata against local FreePDK45 GDS/SPICE libraries.")
    parser.add_argument("--contracts", default="docs/openyield_module_contracts.json")
    parser.add_argument("--compat", default="docs/openyield_macro_compat_report.json")
    parser.add_argument("--tech-dir", default="technology/freepdk45")
    parser.add_argument("--out-json", default="docs/openyield_macro_metadata_audit.json")
    parser.add_argument("--out-md", default="docs/openyield_macro_metadata_audit.md")
    args = parser.parse_args()

    contracts_path = resolve_input(args.contracts)
    compat_path = resolve_input(args.compat)
    tech_dir = resolve_input(args.tech_dir)
    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)

    contracts = load_contract_payload(contracts_path)
    compat = json.loads(compat_path.read_text(encoding="utf-8"))
    replacements = load_replacement_macros(tech_dir)
    aliases = load_macro_aliases(tech_dir)
    discovered = discover_library_macros(tech_dir)
    catalog, catalog_stats = build_macro_catalog(tech_dir)
    augmented = check_contract_payload(contracts, tech_dir)
    report = build_report(contracts, compat, augmented, replacements, aliases, discovered, catalog, catalog_stats, tech_dir)
    report["contracts_path"] = str(contracts_path.resolve())
    report["compat_path"] = str(compat_path.resolve())
    report["tech_dir"] = str(tech_dir.resolve())

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    out_md.write_text(format_markdown(report), encoding="utf-8", newline="\n")
    smoke_assertions(report)
    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(
        "replacement_macros="
        f"{report['replacement_macro_count']} aliases={report['alias_count']} "
        f"library_gds={report['library_gds_count']} library_spice={report['library_spice_count']} "
        f"resolved_missing={len(report['missing_macros_resolved_by_alias'])}"
    )
    return 0


def build_report(
    contracts: dict[str, Any],
    compat: dict[str, Any],
    augmented: dict[str, Any],
    replacements: dict[str, dict[str, Any]],
    aliases: dict[str, dict[str, Any]],
    discovered: dict[str, dict[str, Any]],
    catalog: dict[str, dict[str, Any]],
    catalog_stats: dict[str, Any],
    tech_dir: Path,
) -> dict[str, Any]:
    before_missing = set(compat.get("summary", {}).get("candidate_macro_missing", []))
    after_missing = set(augmented.get("summary", {}).get("candidate_macro_missing", []))
    resolved = sorted(before_missing - after_missing)
    local_hardcells = sorted(name for name, item in discovered.items() if item.get("gds") or item.get("spice"))
    unregistered = sorted(name for name in local_hardcells if name not in replacements)
    contract_by_name = {item["original_module_name"]: item for item in contracts.get("contracts", [])}
    compat_by_name = {item["original_module_name"]: item for item in augmented.get("compatibilities", [])}
    focus = []
    for name in FOCUS_NAMES:
        item = discovered.get(name)
        focus.append(
            {
                "name": name,
                "has_gds": bool(item and item.get("gds")),
                "has_spice": bool(item and item.get("spice")),
                "registered_replacement": name in replacements,
                "alias_targets": sorted(module for module, alias in aliases.items() if alias.get("macro_name") == name),
                "pins": [pin["name"] for pin in (item or {}).get("pins", [])],
            }
        )
    module_rows = []
    for name in sorted(contract_by_name):
        contract = contract_by_name[name]
        check = compat_by_name.get(name)
        alias = aliases.get(name)
        selected = check.get("selected_macro") if check else None
        local = catalog.get(selected) if selected else None
        module_rows.append(
            {
                "module": name,
                "role": contract.get("role"),
                "implementation_status": (check or {}).get("implementation_status", contract.get("implementation_status")),
                "selected_macro": selected,
                "resolved_by_alias": bool(alias and selected),
                "has_local_gds": bool(local and local.get("gds")),
                "has_local_spice": bool(local and local.get("spice")),
                "pin_status": pin_status_counts(check or {}),
                "power_status": (check or {}).get("power_status", "unknown"),
                "abutment_status": (check or {}).get(
                    "aggregation_status",
                    aggregation_status_for_contract(str(contract.get("role")), str(contract.get("implementation_status")), bool(local)),
                ),
                "needs_gds_pin_shape_audit": bool(local and local.get("source_kind") != "replacement_macro"),
                "notes": (check or {}).get("notes", []),
            }
        )
    return {
        **catalog_stats,
        "replacement_macro_names": sorted(replacements),
        "local_library_macros": local_hardcells,
        "unregistered_local_gds_or_spice_macros": unregistered,
        "focus_macro_audit": focus,
        "suggested_macro_aliases": sorted(aliases.values(), key=lambda item: str(item.get("openyield_module"))),
        "missing_macros_before_alias": sorted(before_missing),
        "missing_macros_after_alias": sorted(after_missing),
        "missing_macros_resolved_by_alias": resolved,
        "still_no_physical_implementation": augmented.get("summary", {}).get("no_physical_implementation", []),
        "macro_exists_pin_mismatch_after_alias": augmented.get("summary", {}).get("macro_exists_pin_mismatch", []),
        "vdd_gnd_shared_rail_risks_after_alias": augmented.get("summary", {}).get("vdd_gnd_shared_rail_risks", []),
        "compat_summary_after_alias": augmented.get("summary", {}),
        "module_metadata_audit": module_rows,
        "can_enter_placement_aggregation": False,
        "blocking_metadata_before_placement": [
            "Run a real GDS pin-shape audit for alias-augmented hardcells; current aliases use SPICE pins and file presence.",
            "Resolve SENSEAMP dout_b/QB semantic mismatch because local sense_amp SPICE has a single dout pin.",
            "Resolve COLUMNMUX* missing vdd metadata before shared power rails.",
            "Confirm WORDLINEDRIVER A/B polarity and missing B pin in gen_wl_driver before routing wordline_enable.",
        ],
    }


def pin_status_counts(check: dict[str, Any]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for pin in check.get("pin_checks", []):
        status = pin.get("status", "unknown")
        counts[status] = counts.get(status, 0) + 1
    return counts


def smoke_assertions(report: dict[str, Any]) -> None:
    resolved = set(report["missing_macros_resolved_by_alias"])
    for name in ["SRAM_6T_CELL", "Dummy_CELL", "Dummy_Row", "Dummy_Column", "Replica_CELL", "Replica_Column", "SENSEAMP", "WRITEDRIVER", "DFF"]:
        assert name in resolved, f"{name} was not resolved by alias"
    assert "TIME" in report["compat_summary_after_alias"]["composite_required"]
    assert "SRAM_10T_CELL" in report["compat_summary_after_alias"]["unsupported_architecture"]
    assert "SRAM_10T_CORE_*" in report["compat_summary_after_alias"]["unsupported_architecture"]


def format_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OpenYield Macro Metadata Audit",
            "",
            "This audit scans local FreePDK45 GDS/SPICE libraries and OpenYield alias metadata. It does not modify placement, routing, GDS generation, or OpenYield source.",
            "",
            "## Inputs",
            "",
            f"- contracts: `{report['contracts_path']}`",
            f"- prior compat report: `{report['compat_path']}`",
            f"- tech dir: `{report['tech_dir']}`",
            "",
            "## Library Summary",
            "",
            f"- replacement macros registered: `{report['replacement_macro_count']}`",
            f"- alias entries: `{report['alias_count']}`",
            f"- catalog macros after alias/discovery merge: `{report['catalog_macro_count']}`",
            f"- local GDS macros scanned: `{report['library_gds_count']}`",
            f"- local SPICE subckts scanned: `{report['library_spice_count']}`",
            "",
            "## Missing Macro Resolution",
            "",
            f"- before alias: `{', '.join(report['missing_macros_before_alias']) or 'none'}`",
            f"- after alias: `{', '.join(report['missing_macros_after_alias']) or 'none'}`",
            f"- resolved by alias: `{', '.join(report['missing_macros_resolved_by_alias']) or 'none'}`",
            "",
            "## Focus Macro Audit",
            "",
            md_table(
                ["macro", "GDS", "SPICE", "registered", "alias targets", "pins"],
                [
                    [
                        item["name"],
                        item["has_gds"],
                        item["has_spice"],
                        item["registered_replacement"],
                        ", ".join(item["alias_targets"]) or "-",
                        ", ".join(item["pins"]) or "-",
                    ]
                    for item in report["focus_macro_audit"]
                ],
            ),
            "",
            "## Module Metadata Audit",
            "",
            md_table(
                [
                    "module",
                    "role",
                    "implementation",
                    "selected macro",
                    "alias",
                    "GDS",
                    "SPICE",
                    "pin status",
                    "power",
                    "abutment",
                    "needs GDS pin audit",
                ],
                [
                    [
                        item["module"],
                        item["role"],
                        item["implementation_status"],
                        item["selected_macro"] or "-",
                        item["resolved_by_alias"],
                        item["has_local_gds"],
                        item["has_local_spice"],
                        json.dumps(item["pin_status"], ensure_ascii=False),
                        item["power_status"],
                        item["abutment_status"],
                        item["needs_gds_pin_shape_audit"],
                    ]
                    for item in report["module_metadata_audit"]
                ],
            ),
            "",
            "## Unregistered Local GDS/SPICE Macros",
            "",
            list_block(report["unregistered_local_gds_or_spice_macros"]),
            "",
            "## Suggested Macro Aliases",
            "",
            md_table(
                ["OpenYield module", "macro", "GDS", "SPICE", "aggregation hint", "notes"],
                [
                    [
                        item.get("openyield_module"),
                        item.get("macro_name"),
                        item.get("gds"),
                        item.get("spice"),
                        item.get("aggregation_hint"),
                        "; ".join(item.get("notes") or []),
                    ]
                    for item in report["suggested_macro_aliases"]
                ],
            ),
            "",
            "## Remaining Physical Gaps",
            "",
            f"- no physical/generated/stdcell implementation: `{', '.join(report['still_no_physical_implementation']) or 'none'}`",
            f"- pin mismatch after alias: `{', '.join(report['macro_exists_pin_mismatch_after_alias']) or 'none'}`",
            f"- VDD/GND shared rail risks after alias: `{', '.join(report['vdd_gnd_shared_rail_risks_after_alias']) or 'none'}`",
            "",
            "## Placement Aggregation Readiness",
            "",
            f"- can enter placement aggregation now: `{report['can_enter_placement_aggregation']}`",
            "",
            "Blocking metadata before placement:",
            "",
            list_block(report["blocking_metadata_before_placement"]),
        ]
    )


def md_table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(out)


def list_block(items: list[str]) -> str:
    if not items:
        return "none"
    return "\n".join(f"- `{item}`" for item in items)


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


if __name__ == "__main__":
    raise SystemExit(main())
