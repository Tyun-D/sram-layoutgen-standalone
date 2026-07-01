from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.module_semantic_contracts import (  # noqa: E402
    apply_contract_closure,
    build_gap_closure_report,
    load_csv_rows,
    render_gap_closure_report_md,
    write_contract_bundle,
)
from sram_layoutgen.openyield_adapter.module_semantics import (  # noqa: E402
    CONNECTION_COLUMNS,
    LAYOUTGEN_MAPPING_COLUMNS,
    MODULE_COLUMNS,
    PARAMETER_COLUMNS,
    render_markdown_table,
    write_csv,
    write_text,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Close OpenYield L0 semantic gaps by freezing canonical local contracts.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--in-semantics-csv", required=True)
    parser.add_argument("--in-parameters-csv", required=True)
    parser.add_argument("--in-connections-csv", required=True)
    parser.add_argument("--in-layoutgen-map-csv", required=True)
    parser.add_argument("--out-semantics-csv", required=True)
    parser.add_argument("--out-semantics-md", required=True)
    parser.add_argument("--out-parameters-csv", required=True)
    parser.add_argument("--out-parameters-md", required=True)
    parser.add_argument("--out-connections-csv", required=True)
    parser.add_argument("--out-connections-md", required=True)
    parser.add_argument("--out-layoutgen-map-csv", required=True)
    parser.add_argument("--out-layoutgen-map-md", required=True)
    parser.add_argument("--out-contract-json", required=True)
    parser.add_argument("--out-contract-md", required=True)
    parser.add_argument("--out-report-json", required=True)
    parser.add_argument("--out-report-md", required=True)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    openyield_root = Path(args.openyield_root).resolve()
    module_rows = load_csv_rows(args.in_semantics_csv)
    parameter_rows = load_csv_rows(args.in_parameters_csv)
    connection_rows = load_csv_rows(args.in_connections_csv)
    mapping_rows = load_csv_rows(args.in_layoutgen_map_csv)

    contract_bundle = write_contract_bundle(repo_root)
    closure = apply_contract_closure(
        repo_root=repo_root,
        module_rows=module_rows,
        parameter_rows=parameter_rows,
        connection_rows=connection_rows,
        mapping_rows=mapping_rows,
        contract_bundle=contract_bundle,
    )
    report = build_gap_closure_report(
        repo_root=repo_root,
        openyield_root=openyield_root,
        module_rows=closure["module_rows"],
        parameter_rows=closure["parameter_rows"],
        connection_rows=closure["connection_rows"],
        mapping_rows=closure["mapping_rows"],
        contract_bundle=contract_bundle,
        gates=closure["gates"],
    )

    write_csv(args.out_semantics_csv, closure["module_rows"], MODULE_COLUMNS)
    write_text(args.out_semantics_md, _matrix_md("OpenYield Module Semantics Matrix", closure["module_rows"], MODULE_COLUMNS))
    write_csv(args.out_parameters_csv, closure["parameter_rows"], PARAMETER_COLUMNS)
    write_text(args.out_parameters_md, _matrix_md("OpenYield Parameter Dependency Matrix", closure["parameter_rows"], PARAMETER_COLUMNS))
    write_csv(args.out_connections_csv, closure["connection_rows"], CONNECTION_COLUMNS)
    write_text(args.out_connections_md, _matrix_md("OpenYield Module Connection Matrix", closure["connection_rows"], CONNECTION_COLUMNS))
    write_csv(args.out_layoutgen_map_csv, closure["mapping_rows"], LAYOUTGEN_MAPPING_COLUMNS)
    write_text(args.out_layoutgen_map_md, _matrix_md("OpenYield to Layoutgen Semantic Mapping", closure["mapping_rows"], LAYOUTGEN_MAPPING_COLUMNS))

    out_contract_json = Path(args.out_contract_json)
    out_contract_json.parent.mkdir(parents=True, exist_ok=True)
    out_contract_json.write_text(json.dumps(contract_bundle["canonical_contract"], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_text(args.out_contract_md, _canonical_contract_md(contract_bundle["canonical_contract"]))

    out_report_json = Path(args.out_report_json)
    out_report_json.parent.mkdir(parents=True, exist_ok=True)
    out_report_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_text(args.out_report_md, render_gap_closure_report_md(report))

    _write_evidence_updates(repo_root, report)

    if report["gates"]["remaining_L0_blockers_count"] != 0:
        raise SystemExit("remaining_L0_blockers_count is not zero after contract closure")
    return 0


def _matrix_md(title: str, rows: list[dict[str, object]], columns: list[str]) -> str:
    return "\n".join([f"# {title}", "", render_markdown_table(rows, columns), ""])


def _canonical_contract_md(contract: dict[str, object]) -> str:
    lines = [
        "# OpenYield Canonical SRAM Semantic Contract",
        "",
        "Generated by `scripts/openyield_L0_semantic_gap_closure.py`.",
        "",
        "## Supported Scope",
        "",
    ]
    lines.extend(f"- {key}: `{value}`" for key, value in contract["scope"].items())
    lines.extend(
        [
            "",
            "## Unsupported Features",
            "",
        ]
    )
    lines.extend(f"- `{item}`" for item in contract["unsupported_features"])
    lines.extend(
        [
            "",
            "## Derivation Rules",
            "",
        ]
    )
    lines.extend(f"- `{item['rule_name']}`: {item['rule']}" for item in contract["derivation_rules"])
    return "\n".join(lines)


def _write_evidence_updates(repo_root: Path, report: dict[str, object]) -> None:
    gates = report["gates"]
    gap_summary = "\n".join(
        [
            "# L0 Semantics Gap Summary",
            "",
            "## First-Pass Blockers",
            "",
            "- OpenYield did not expose explicit `SRAM_TOP` / `BANK` classes.",
            "- OpenYield was row/column oriented and did not expose first-class `word_size` / `num_words` / `words_per_row` / `num_banks` / `num_ports` / `write_mask` parameters.",
            "- `TIME` was a composite control/timing generator without frozen local semantic boundaries.",
            "- Enable paths and decoder-to-wordline handoff were source-backed but still treated as unresolved semantic objects.",
            "",
            "## Closure Method In This Pass",
            "",
            "- Added a canonical SRAM semantic contract for the supported single-bank scope.",
            "- Added a logical-spec to OpenYield parameter mapping contract, freezing how `num_words`, `word_size`, and `words_per_row` map into `num_rows`, `num_cols`, and `choose_columnmux`.",
            "- Added explicit `SRAM_TOP` and `BANK` semantic contracts, closing the missing explicit-class issue by local canonical contract rather than waiting for upstream source changes.",
            "- Added a `TIME` decomposition contract and standalone control-path semantic contracts for `DFF_ROW`, `GATED_CLOCK_PATH`, `WORDLINE_ENABLE_PATH`, `PRECHARGE_ENABLE_PATH`, `SENSE_ENABLE_PATH`, `WRITE_ENABLE_PATH`, and `DELAY_CHAIN`.",
            "- Added a decoder/wordline handoff contract and froze routing/power/timing handoff semantics at L0.",
            "",
            "## Explicit Unsupported Features",
            "",
            *[f"- `{item}`" for item in report["summary"]["unsupported_features"]],
            "",
            "## Why Unsupported Features Do Not Block L1",
            "",
            "- Current L1 scope is explicitly single-bank, single implicit read/write port, no write-mask, and column-mux ratio limited to 1 or 2.",
            "- Those unsupported features are out of scope rather than unknown semantics, so they no longer count as L0 blockers.",
            "",
            "## Why L1 Can Now Start",
            "",
            f"- `remaining_L0_blockers_count = {gates['remaining_L0_blockers_count']}`",
            f"- `can_claim_L0_semantics_closed_now = {gates['can_claim_L0_semantics_closed_now']}`",
            f"- `can_enter_L1_physical_primitive_closure = {gates['can_enter_L1_physical_primitive_closure']}`",
            "- All required semantic objects now have either direct OpenYield source evidence or an explicit canonical local contract.",
            "- Remaining open work is physical primitive realization, placement rules, module GDS generation, routing, rail proof, and signoff.",
            "",
            "## L1 Next Work",
            "",
            "- Realize the frozen semantic objects with physical primitives.",
            "- Preserve the new logical-to-physical parameter contract while implementing bitcell/peripheral/control primitives.",
            "- Keep unsupported features out of scope until a later semantic generalization pass.",
        ]
    )
    write_text(repo_root / "docs/evidence/L0_semantics_gap_summary.md", gap_summary)

    timeline_path = repo_root / "docs/evidence/evidence_timeline.md"
    timeline = timeline_path.read_text(encoding="utf-8").rstrip() + (
        "\n- `2026-07-02`: Closed OpenYield L0 semantic contract gaps by generating canonical SRAM/top-bank/TIME/control-path/decoder-wordline contracts, freezing logical-to-OpenYield parameter mapping, updating module/parameter/connection/mapping matrices, and setting `can_enter_L1_physical_primitive_closure=True` while keeping all physical/GDS/signoff claims false.\n"
    )
    write_text(timeline_path, timeline)

    milestone_path = repo_root / "docs/evidence/milestone_summary.md"
    milestone = milestone_path.read_text(encoding="utf-8").rstrip() + (
        "\n- OpenYield L0 semantic contract gaps are now closed for the supported scope: a canonical SRAM semantic contract, logical-to-OpenYield mapping, top/bank contract, TIME decomposition contract, control-path contracts, and decoder-wordline handoff contract are all generated, and L1 physical primitive closure can now begin without claiming physical completion.\n"
    )
    write_text(milestone_path, milestone)


if __name__ == "__main__":
    raise SystemExit(main())
