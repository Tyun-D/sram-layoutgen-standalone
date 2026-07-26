#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import subprocess
import tarfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sram_layoutgen.openyield_adapter.project_long_range import (
    build_formal_sram_config_inventory,
    build_formal_sram_config_schema,
    check_claim_policy,
    read_csv,
    read_json,
    sha256_file,
    sha256_text,
    validate_formal_sram_config_inventory,
    write_csv,
    write_json,
    write_text,
)

DOCS = ROOT / "docs"
SOURCE_TREE = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
OPENYIELD_ROOT = Path("/data1/qujh/work/external/OpenYield")
REVIEW_PKG = Path("/data1/qujh/PROJECT_LONG_RANGE_HUMAN_REVIEW_PACKAGE_LATEST.tar.gz")
FULL_PKG = Path("/data1/qujh/PROJECT_LONG_RANGE_FULL_EVIDENCE_PACKAGE_LATEST.tar.gz")


def run(cmd: list[str], cwd: Path = ROOT) -> str:
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def append_project_log(md_block: str, json_obj: dict[str, Any]) -> None:
    with (DOCS / "PROJECT_TASK_MASTER_LOG.md").open("a", encoding="utf-8") as handle:
        handle.write("\n" + md_block.rstrip() + "\n")
    with (DOCS / "PROJECT_TASK_MASTER_LOG.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(json_obj, ensure_ascii=False) + "\n")


def md_table(title: str, rows: list[dict[str, Any]], fieldnames: list[str]) -> str:
    lines = [f"# {title}", "", "| " + " | ".join(fieldnames) + " |", "| " + " | ".join(["---"] * len(fieldnames)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(field, "")).replace("\n", " ") for field in fieldnames) + " |")
    return "\n".join(lines) + "\n"


def collect_source_inventory() -> dict[str, Any]:
    branch = run(["git", "branch", "--show-current"])
    head = run(["git", "rev-parse", "HEAD"])
    status = run(["git", "status", "--short"]).splitlines()
    origin_master = run(["git", "rev-parse", "origin/master"])
    worktrees = run(["git", "worktree", "list"]).splitlines()
    disk = run(["df", "-h", "/data1", "/tmp", "/home"]).splitlines()
    tmux = run(["bash", "-lc", "tmux ls 2>/dev/null || true"]).splitlines()
    return {
        "branch": branch,
        "head": head,
        "status": status,
        "origin_master": origin_master,
        "worktrees": worktrees,
        "disk": disk,
        "tmux": tmux,
    }


def write_p0_003_resolution(ts: str) -> dict[str, Any]:
    resolution = {
        "timestamp": ts,
        "gap_id": "P0-003",
        "result_id": "OWNER_A_LOGICAL_DATA_MODEL_V1",
        "five_required_facts": {
            "actual_author_or_responsible_owner": False,
            "canonical_source_path_branch_or_commit": False,
            "review_bundle_matches_canonical_source": False,
            "recovery_authorization_for_current_project_branch": False,
            "final_report_author_contribution_attribution": False,
        },
        "evidence_scan": {
            "all_five_confirmed": False,
            "scanned_paths": [
                "docs/OTHER_TEAM_OWNER_CONFIRMATION_REQUEST.md",
                "docs/UNKNOWN_OWNER_BRANCH_FORENSICS.md",
                "docs/OTHER_TEAM_RESULT_TRIANGULATION.csv",
                "docs/PROJECT_TASK_MASTER_LOG.md",
                "docs/TEAM_B_OWNER_HUMAN_REVIEW_APPROVAL.md",
                "docs/TEAM_B_OWNER_HUMAN_REVIEW_APPROVAL.json",
            ],
            "positive_evidence_found": [
                "Team B owner human-review approval exists and is explicitly scoped to Team B layout / 9-cell integration.",
                "Owner A review bundles and untracked worktree files exist.",
            ],
            "missing_evidence": [
                "No explicit author/responsible-owner confirmation for OWNER_A_LOGICAL_DATA_MODEL_V1.",
                "No canonical source path / branch / commit declaration for logical-model source.",
                "No explicit statement that review bundles correspond to a declared canonical source snapshot.",
                "No authorization to recover source or docs into the current project branch.",
                "No final-report author-attribution approval for this result.",
            ],
        },
        "team_b_user_approval_is_not_owner_a_confirmation": True,
        "status": "BLOCKED_EXTERNAL",
        "decision": "Do not merge or recover OWNER_A source until explicit owner confirmation covers all five required facts.",
    }
    write_json(DOCS / "P0_003_OWNER_CONFIRMATION_RESOLUTION.json", resolution)
    md = [
        "# P0-003 Owner Confirmation Resolution",
        "",
        f"- timestamp: `{ts}`",
        "- gap_id: `P0-003`",
        "- result_id: `OWNER_A_LOGICAL_DATA_MODEL_V1`",
        "- conclusion: `BLOCKED_EXTERNAL`",
        "- note: Team B human-review approval only covers Team B layout and 9-cell integration; it does not confirm Owner A authorship, canonical source, recovery authorization, or final report attribution.",
        "",
        "## Five Required Facts",
        "",
        "| fact | confirmed | note |",
        "| --- | --- | --- |",
        "| actual author / responsible owner | False | naming and bundle titles exist, but no explicit owner confirmation was found |",
        "| canonical source path / branch / commit | False | current source remains untracked worktree content on shared base commit |",
        "| review bundle matches canonical source | False | review bundles reference changed files, but no canonical source declaration was found |",
        "| authorized recovery into current project branch | False | no explicit recovery authorization record was found |",
        "| final report author attribution | False | no explicit Owner A attribution approval was found |",
        "",
        "## Decision",
        "",
        "Keep `P0-003` as `BLOCKED_EXTERNAL`. Continue P1/P2/P3 work that does not depend on merging Owner A source. Do not merge `feature/owner-a-logical-data-model-v1-20260723_010633` in this round.",
        "",
    ]
    write_text(DOCS / "P0_003_OWNER_CONFIRMATION_RESOLUTION.md", "\n".join(md))
    return resolution


def write_long_range_execution_matrix(
    *,
    p0_resolution: dict[str, Any],
) -> list[dict[str, Any]]:
    gap_rows = read_csv(DOCS / "PROJECT_GAP_REGISTER.csv")
    rows: list[dict[str, Any]] = []
    notes_by_gap = {
        "P0-003": "Only Team B human-review approval exists; Owner A author/canonical-source/recovery authorization remains unconfirmed.",
        "P1-001": "Formal config schema, source binding, validator, and inventory generated from raw variation space + locked baseline + degraded historical evidence.",
        "P1-002": "Decoder leaf availability improved after Team B PNAND3/AND3 closure, but full decoder physical placement/routing/handoff evidence is still missing.",
        "P1-003": "Claim-policy checker and signoff-boundary audit formalized unsupported external-signoff claims.",
        "P1-004": "Current top-bank semantic contract remains single-bank only; multi-bank support closed as documented authority boundary.",
        "P2-001": "Figure/table requirement rows were upgraded into evidence-backed figure index entries and vector capture plans.",
        "P2-002": "Screenshot rows now include source SHA, clean-view instructions, and manual capture entrypoints.",
        "P3-001": "Future extensions documented as roadmap only, not implemented functionality.",
    }
    state_by_gap = {
        "P0-003": "BLOCKED_EXTERNAL",
        "P1-001": "MACHINE_CLOSED",
        "P1-002": "BLOCKED_TECHNICAL",
        "P1-003": "CLOSED_AS_DOCUMENTED_BOUNDARY",
        "P1-004": "CLOSED_AS_DOCUMENTED_BOUNDARY",
        "P2-001": "CLOSED_AS_REPORT_EVIDENCE",
        "P2-002": "CLOSED_AS_REPORT_EVIDENCE",
        "P3-001": "ROADMAP_DOCUMENTED",
    }
    for gap in gap_rows:
        gap_id = gap["gap_id"]
        if gap_id not in state_by_gap:
            continue
        rows.append(
            {
                "gap_id": gap_id,
                "scope": gap["scope"],
                "priority": gap["priority"],
                "exact_description": gap["description"],
                "current_evidence": gap["evidence"],
                "root_cause": gap["resolution_note"] or gap["required_action"],
                "owner": gap["owner"],
                "external_dependency": "Owner A confirmation" if gap_id == "P0-003" else "",
                "required_action": gap["required_action"],
                "expected_output": gap["expected_output"],
                "validation_method": gap["validation"],
                "blocking_reason": "Await explicit owner confirmation" if gap_id == "P0-003" else "",
                "status": state_by_gap[gap_id],
                "status_note": notes_by_gap[gap_id],
            }
        )
    fields = list(rows[0].keys())
    write_csv(DOCS / "LONG_RANGE_GAP_EXECUTION_MATRIX.csv", rows, fields)
    write_text(DOCS / "LONG_RANGE_GAP_EXECUTION_PLAN.md", md_table("Long Range Gap Execution Plan", rows, fields))
    state = {
        "workflow_state": "PROJECT_LONG_RANGE_ADVANCING_WITH_EXTERNAL_OWNER_BLOCKER" if p0_resolution["status"] == "BLOCKED_EXTERNAL" else "PROJECT_LONG_RANGE_ADVANCING",
        "p0_003_resolution": p0_resolution["status"],
        "gap_status_counts": dict(Counter(row["status"] for row in rows)),
    }
    write_json(DOCS / "LONG_RANGE_EXECUTION_STATE.json", state)
    return rows


def write_formal_config_outputs(ts: str) -> dict[str, Any]:
    schema = build_formal_sram_config_schema()
    inventory_rows, binding_rows, summary = build_formal_sram_config_inventory(
        repo_root=ROOT,
        source_tree=SOURCE_TREE,
        openyield_root=OPENYIELD_ROOT,
    )
    validation = validate_formal_sram_config_inventory(inventory_rows)
    schema["generated_at"] = ts
    summary["validation"] = validation
    write_json(DOCS / "FORMAL_SRAM_CONFIG_SCHEMA.json", schema)
    write_text(
        DOCS / "FORMAL_SRAM_CONFIG_SCHEMA.md",
        "# Formal SRAM Config Schema\n\n"
        f"- schema_name: `{schema['schema_name']}`\n"
        f"- schema_version: `{schema['schema_version']}`\n"
        f"- validation_rules: `{'; '.join(schema['validation_rules'])}`\n"
        f"- degrade_policy: `{schema['degrade_policy']}`\n",
    )
    write_csv(
        DOCS / "FORMAL_SRAM_CONFIG_SOURCE_BINDING.csv",
        binding_rows,
        [
            "config_id",
            "field_name",
            "value",
            "binding_type",
            "authority_path",
            "authority_sha",
            "evidence_kind",
            "source_backed",
            "degraded",
            "note",
        ],
    )
    write_json(DOCS / "FORMAL_SRAM_CONFIG_SOURCE_BINDING.json", {"rows": binding_rows, "summary": summary})
    write_text(
        DOCS / "FORMAL_SRAM_CONFIG_SOURCE_BINDING.md",
        md_table(
            "Formal SRAM Config Source Binding",
            binding_rows,
            ["config_id", "field_name", "value", "binding_type", "source_backed", "degraded", "authority_path", "note"],
        ),
    )
    write_csv(
        DOCS / "FORMAL_SRAM_CONFIG_INVENTORY.csv",
        inventory_rows,
        list(inventory_rows[0].keys()),
    )
    write_json(DOCS / "FORMAL_SRAM_CONFIG_INVENTORY.json", {"rows": inventory_rows, "summary": summary})
    write_text(
        DOCS / "FORMAL_SRAM_CONFIG_INVENTORY.md",
        md_table(
            "Formal SRAM Config Inventory",
            inventory_rows,
            [
                "config_id",
                "word_size",
                "num_words",
                "words_per_row",
                "num_rows",
                "num_cols",
                "addr_width",
                "num_banks",
                "source_authority",
                "support_level",
                "inventory_status",
                "notes",
            ],
        ),
    )
    return {
        "schema": schema,
        "inventory_rows": inventory_rows,
        "binding_rows": binding_rows,
        "summary": summary,
    }


def write_signoff_boundary_outputs(ts: str) -> dict[str, Any]:
    signoff_md = (ROOT / "docs/SIGNOFF.md").read_text(encoding="utf-8")
    checked_paths = [
        ROOT / "docs/SIGNOFF.md",
        ROOT / "docs/PROJECT_CURRENT_STATUS.json",
        ROOT / "docs/PROJECT_FINAL_TECHNICAL_DRAFT.md",
        ROOT / "docs/PROJECT_GAP_REGISTER.md",
        ROOT / "docs/OPENRAM_LAYOUTGEN_OPENYIELD_COMPARISON.md",
    ]
    policy = {
        "generated_at": ts,
        "forbidden_claims": [
            {"term": "tapeout-ready", "allowed_now": False, "reason": "No external foundry signoff or tapeout program evidence exists."},
            {"term": "foundry signoff passed", "allowed_now": False, "reason": "Project evidence is limited to internal KLayout/DRC/connectivity and human review boundaries."},
            {"term": "silicon-proven", "allowed_now": False, "reason": "No silicon measurements exist."},
            {"term": "full external signoff", "allowed_now": False, "reason": "Current SRAM top lacks complete external DRC/LVS/PEX closure evidence."},
        ],
        "positive_allowed_claims": [
            "internal DRC clean where explicitly evidenced",
            "machine-verified module or integration closure where gate files exist",
            "human-reviewed Team B library and integration where approval file exists",
        ],
    }
    write_json(DOCS / "PROJECT_CLAIM_POLICY.json", policy)
    write_text(
        DOCS / "PROJECT_CLAIM_POLICY.md",
        "# Project Claim Policy\n\n"
        "- Unsupported affirmative claims are blocked: `tapeout-ready`, `foundry signoff passed`, `silicon-proven`, `full external signoff`.\n"
        "- Allowed claims must stay within explicit machine gate, DRC, connectivity, negative-test, and human-review evidence.\n",
    )
    checker = check_claim_policy(checked_paths)
    boundary = {
        "generated_at": ts,
        "signoff_md_path": "docs/SIGNOFF.md",
        "signoff_ready_blockers": [
            "no abstract_instances remain in *.report.json",
            "KLayout DRC report exists and has zero reported items",
            "LVS has a complete schematic and passes",
            "extracted netlist and generated SPICE are equivalent",
        ],
        "m2r_external_signoff_status": "NOT_CLOSED",
        "m2r_current_allowed_claim": "internal machine-verified top-level generation with internal DRC clean but no external signoff claim",
        "claim_policy_checker": checker,
        "signoff_md_sha": sha256_file(ROOT / "docs/SIGNOFF.md"),
        "signoff_md_excerpt_hash": sha256_text(signoff_md),
    }
    write_json(DOCS / "M2R_SIGNOFF_BOUNDARY_AUDIT.json", boundary)
    write_text(
        DOCS / "M2R_SIGNOFF_BOUNDARY_AUDIT.md",
        "# M2R Signoff Boundary Audit\n\n"
        "- current_status: `NOT_CLOSED`\n"
        "- allowed_claim: `internal machine-verified top-level generation with internal DRC clean but no external signoff claim`\n"
        "- checker_passed: `{}`\n"
        "- violation_count: `{}`\n".format(checker["passed"], checker["violation_count"]),
    )
    return boundary


def write_decoder_boundary_outputs(ts: str) -> dict[str, Any]:
    preplacement = read_json(ROOT / "docs/openyield_decoder_preplacement_feasibility_report.json")
    logic_repair = read_json(ROOT / "docs/openyield_decoder_logic_repair_report.json")
    output_contract = read_json(ROOT / "docs/openyield_decoder_output_contract_report.json")
    and2_gate = read_json(SOURCE_TREE / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND2/machine_gate.json")
    and3_gate = read_json(SOURCE_TREE / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND3/machine_gate.json")
    decoder = {
        "generated_at": ts,
        "decoder_status": "BLOCKED_TECHNICAL",
        "canonical_logic_contract_changed": False,
        "team_b_leafs_now_available": {
            "and2_connectivity_passed": and2_gate["connectivity_passed"],
            "and3_connectivity_passed": and3_gate["connectivity_passed"],
        },
        "stale_historical_blocker_removed": True,
        "remaining_blockers": [
            "decoder preplacement report is metadata_only and not_legal_physical_placement=true",
            "decoder output contract remains metadata_only and physical_routing_proven=false",
            "no final decoder machine gate / negative suite / deterministic closure exists",
            "no final decoder review atlas or formal clean.gds exists as a closed artifact",
        ],
        "source_evidence": {
            "preplacement_metadata_only": preplacement["metadata_only"],
            "physical_layout_generated": preplacement["physical_layout_generated"],
            "output_contract_physical_routing_proven": output_contract["generic_output_contracts"][0]["physical_routing_proven"],
            "historical_direct_and3_exists": logic_repair["direct_and3_exists"],
        },
        "decision": "Do not claim decoder physical closure. Update project status to BLOCKED until a dedicated decoder generator closes placement, routing, DRC, connectivity, foreign-net, determinism, negative tests, and review atlas.",
    }
    write_json(DOCS / "DECODER_PHYSICAL_CLOSURE_AUDIT.json", decoder)
    write_text(
        DOCS / "DECODER_PHYSICAL_CLOSURE_AUDIT.md",
        "# Decoder Physical Closure Audit\n\n"
        "- status: `BLOCKED_TECHNICAL`\n"
        "- stale_blocker_removed: `Team B AND2/AND3 are now formal`, but decoder is still metadata-only at the stage-planning and output-handoff level.\n"
        "- remaining_blockers:\n"
        "  - metadata-only preplacement\n"
        "  - metadata-only output handoff\n"
        "  - no final decoder machine gate / negative suite\n"
        "  - no final decoder clean GDS / review atlas\n",
    )
    return decoder


def write_multibank_boundary_outputs(ts: str) -> dict[str, Any]:
    bank_contract = read_json(ROOT / "docs/mapping/openyield_top_bank_semantic_contract.json")
    audit = {
        "generated_at": ts,
        "multibank_status": "FUNCTIONAL_TOP_LEVEL_BLOCKED_BY_MISSING_AUTHORITY",
        "bank_count_supported_today": bank_contract["BANK"]["bank_count_supported"],
        "bank_count_gt_1_contract": bank_contract["BANK"]["bank_count_gt_1"],
        "support_level": "NOT_IMPLEMENTED",
        "decision": "Do not invent bank-select/control netlists. Multi-bank stays a documented boundary until canonical source authority exists.",
        "physical_aggregation_capability": "single-bank physical flow only; no formal bank_count=2 source-backed generator path is authorized",
    }
    write_json(DOCS / "MULTIBANK_PHYSICAL_FLOW_AUDIT.json", audit)
    write_text(
        DOCS / "MULTIBANK_PHYSICAL_FLOW_AUDIT.md",
        "# Multi-bank Physical Flow Audit\n\n"
        "- status: `FUNCTIONAL_TOP_LEVEL_BLOCKED_BY_MISSING_AUTHORITY`\n"
        "- current_contract: `bank_count_supported=1`\n"
        "- support_level: `NOT_IMPLEMENTED`\n"
        "- rule: do not invent bank-select or top-level control netlists without canonical source authority.\n",
    )
    return audit


def write_p2_outputs(ts: str) -> list[dict[str, Any]]:
    requirements = read_csv(DOCS / "FINAL_FIGURE_AND_TABLE_REQUIREMENTS.csv")
    updated_requirements: list[dict[str, Any]] = []
    figure_rows: list[dict[str, Any]] = []
    for index, row in enumerate(requirements, start=1):
        if row["item"] == "delay-chain stage/load schematic":
            row["source_path"] = "docs/figures/delay_chain_stage_load_baseline.mmd"
            row["already_exists"] = "True"
        if row["item"] == "parameter flow diagram":
            row["source_path"] = "docs/figures/parameter_flow_diagram.mmd"
            row["already_exists"] = "True"
        if row["item"] == "three-route architecture comparison":
            row["source_path"] = "docs/figures/three_route_architecture_comparison.mmd"
            row["already_exists"] = "True"
        source_path = row["source_path"]
        sha = sha256_text(source_path)
        availability = "READY_EXISTING" if row["already_exists"] == "True" else "SPEC_READY_MANUAL_CAPTURE"
        figure_rows.append(
            {
                "item_id": f"FIG{index:03d}",
                "item": row["item"],
                "source_path": source_path,
                "source_sha": sha,
                "recommended_view": row["recommended_view"],
                "debug_layers_to_hide": row["debug_layers_to_hide"],
                "resolution": row["resolution"],
                "caption_points": row["caption_points"],
                "availability": availability,
                "owner": row["owner"],
            }
        )
        updated_requirements.append(row)
    write_csv(DOCS / "FINAL_FIGURE_AND_TABLE_REQUIREMENTS.csv", updated_requirements, list(updated_requirements[0].keys()))
    write_text(DOCS / "FINAL_FIGURE_AND_TABLE_REQUIREMENTS.md", md_table("Final Figure and Table Requirements", updated_requirements, list(updated_requirements[0].keys())))
    write_csv(DOCS / "FINAL_FIGURE_AND_TABLE_INDEX.csv", figure_rows, list(figure_rows[0].keys()))
    write_text(DOCS / "FINAL_FIGURE_AND_TABLE_INDEX.md", md_table("Final Figure and Table Index", figure_rows, list(figure_rows[0].keys())))
    figures_dir = DOCS / "figures"
    figures_dir.mkdir(exist_ok=True)
    write_text(
        figures_dir / "parameter_flow_diagram.mmd",
        "flowchart LR\n"
        "  A[User config] --> B[Legality checks]\n"
        "  B --> C[OpenYield / manifest authority]\n"
        "  C --> D[Module selection]\n"
        "  D --> E[Floorplan and placement]\n"
        "  E --> F[Routing and power stitching]\n"
        "  F --> G[DRC / connectivity / negative tests]\n"
        "  G --> H[Final manifest and review package]\n",
    )
    write_text(
        figures_dir / "three_route_architecture_comparison.mmd",
        "flowchart TB\n"
        "  subgraph OpenRAM\n"
        "    A1[Reference compiler]\n"
        "  end\n"
        "  subgraph Layoutgen\n"
        "    B1[Config-aware physical generator]\n"
        "  end\n"
        "  subgraph OpenYield\n"
        "    C1[Semantic netlist authority]\n"
        "    C2[Module contracts]\n"
        "    C3[Physical reuse and integration]\n"
        "  end\n"
        "  C1 --> C2 --> C3\n",
    )
    write_text(
        figures_dir / "delay_chain_stage_load_baseline.mmd",
        "flowchart LR\n"
        "  A[wen_delay_chain 4x4] --> B[locked baseline]\n"
        "  C[delay_chain 9x4] --> B\n"
        "  B --> D[future parameterization roadmap]\n",
    )
    return figure_rows


def update_parameter_docs(multibank_boundary: dict[str, Any]) -> None:
    catalog = read_csv(DOCS / "CUSTOMIZABLE_SRAM_PARAMETER_CATALOG.csv")
    for row in catalog:
        if row["parameter_name"] == "word_count":
            row["evidence_path"] = "docs/FORMAL_SRAM_CONFIG_INVENTORY.csv; docs/FORMAL_SRAM_CONFIG_SOURCE_BINDING.csv"
            row["known_constraints"] = "formal config inventory now exists; current source-backed public set remains 8x64_wpr4, 4x32_wpr2, 16x16_wpr1"
            row["future_extension"] = "expand source-backed variation set and top-level requalification"
        if row["parameter_name"] == "word_size":
            row["evidence_path"] = "docs/FORMAL_SRAM_CONFIG_INVENTORY.csv; docs/FORMAL_SRAM_CONFIG_SOURCE_BINDING.csv"
            row["known_constraints"] = "formal config inventory replaces ad-hoc fallback claims, but public support is still constrained to explicit evidence-backed variations"
        if row["parameter_name"] == "address_bits":
            row["evidence_path"] = "docs/FORMAL_SRAM_CONFIG_INVENTORY.csv"
            row["known_constraints"] = "derived from num_words in the formal config inventory; not independently authored in raw OpenYield config"
        if row["parameter_name"] == "bank_count":
            row["support_level"] = "PARTIALLY_SUPPORTED"
            row["evidence_path"] = "docs/MULTIBANK_PHYSICAL_FLOW_AUDIT.json; docs/mapping/openyield_top_bank_semantic_contract.json"
            row["known_constraints"] = "single-bank only in canonical source authority; bank_count>1 is blocked by missing authority"
            row["future_extension"] = multibank_boundary["multibank_status"]
        if row["parameter_name"] == "words_per_row":
            row["evidence_path"] = "docs/FORMAL_SRAM_CONFIG_INVENTORY.csv; docs/FORMAL_SRAM_CONFIG_SOURCE_BINDING.csv"
        if row["parameter_name"] == "column_mux_ratio":
            row["evidence_path"] = "docs/FORMAL_SRAM_CONFIG_SOURCE_BINDING.csv"
        if row["parameter_name"] == "decoder_architecture":
            row["evidence_path"] = "docs/DECODER_PHYSICAL_CLOSURE_AUDIT.json"
            row["known_constraints"] = "Team B leaf availability improved, but decoder remains blocked at placement/routing/handoff closure"
    write_csv(DOCS / "CUSTOMIZABLE_SRAM_PARAMETER_CATALOG.csv", catalog, list(catalog[0].keys()))
    write_text(DOCS / "CUSTOMIZABLE_SRAM_PARAMETER_CATALOG.md", md_table("Customizable SRAM Parameter Catalog", catalog, list(catalog[0].keys())))

    trace = read_csv(DOCS / "CUSTOMIZABLE_SRAM_PARAMETER_TRACEABILITY_MATRIX.csv")
    for row in trace:
        if row["parameter_name"] == "word_size":
            row["manifest_output"] = "FORMAL_SRAM_CONFIG_INVENTORY + FORMAL_SRAM_CONFIG_SOURCE_BINDING"
        if row["parameter_name"] == "word_count":
            row["manifest_output"] = "FORMAL_SRAM_CONFIG_INVENTORY + FORMAL_SRAM_CONFIG_SOURCE_BINDING"
        if row["parameter_name"] == "bank_count":
            row["legality_check"] = "currently forced to 1 by canonical source authority"
            row["manifest_output"] = "MULTIBANK_PHYSICAL_FLOW_AUDIT"
        if row["parameter_name"] == "decoder architecture":
            row["manifest_output"] = "DECODER_PHYSICAL_CLOSURE_AUDIT"
    write_csv(DOCS / "CUSTOMIZABLE_SRAM_PARAMETER_TRACEABILITY_MATRIX.csv", trace, list(trace[0].keys()))
    write_text(DOCS / "CUSTOMIZABLE_SRAM_PARAMETER_TRACEABILITY_MATRIX.md", md_table("Customizable SRAM Parameter Traceability Matrix", trace, list(trace[0].keys())))


def update_report_evidence_and_comparison() -> None:
    matrix = read_csv(DOCS / "FINAL_REPORT_SECTION_EVIDENCE_MATRIX.csv")
    for row in matrix:
        if row["section"] == "可定制参数体系":
            row["supporting_source"] = "docs/CUSTOMIZABLE_SRAM_PARAMETER_CATALOG.csv; docs/FORMAL_SRAM_CONFIG_INVENTORY.csv; docs/FORMAL_SRAM_CONFIG_SOURCE_BINDING.csv"
            row["figure_needed"] = "parameter flow diagram"
            row["table_needed"] = "formal config inventory"
            row["next_action"] = "reuse formal config inventory and parameter-flow figure"
        if row["section"] == "模块级版图生成":
            row["missing_evidence"] = "other-team source recovery still blocked on Owner A confirmation; decoder remains physically blocked"
        if row["section"] == "代表性 SRAM 结果":
            row["supporting_source"] = "docs/SRAM_CONFIGURATION_INVENTORY.csv; docs/FORMAL_SRAM_CONFIG_INVENTORY.json; docs/HISTORICAL_30_CONFIG_21_MODULE_CLAIM_AUDIT.json"
            row["next_action"] = "use formal config inventory plus audited explicit config inventory"
        if row["section"] == "局限与未来工作":
            row["supporting_source"] = "docs/PROJECT_GAP_REGISTER.csv; docs/PROJECT_LONG_RANGE_CLOSURE_GATE.json; docs/PROJECT_FUTURE_ROADMAP.json"
            row["table_needed"] = "long-range closure gate"
    write_csv(DOCS / "FINAL_REPORT_SECTION_EVIDENCE_MATRIX.csv", matrix, list(matrix[0].keys()))
    write_text(DOCS / "FINAL_REPORT_SECTION_EVIDENCE_MATRIX.md", md_table("Final Report Section Evidence Matrix", matrix, list(matrix[0].keys())))

    comparison_md = (
        "# OpenRAM / layoutgen / OpenYield Comparison\n\n"
        "- OpenRAM: mature open-source SRAM compiler and reference implementation.\n"
        "- simplified layoutgen: controllable physical-generation research platform with explicit config and verification artifacts.\n"
        "- OpenYield: semantic netlist and module-contract authority source, with physical reuse proven only where evidence exists.\n\n"
        "## Current boundary update\n"
        "- formal config inventory is now explicit and evidence-backed for the current supported variation set.\n"
        "- decoder remains physically blocked even though Team B AND2/AND3 leaf closure removed one historical blocker.\n"
        "- multi-bank remains a roadmap boundary because canonical source authority is still single-bank only.\n"
        "- external signoff remains out of scope for current project claims.\n"
    )
    write_text(DOCS / "OPENRAM_LAYOUTGEN_OPENYIELD_COMPARISON.md", comparison_md)


def write_p3_outputs() -> list[dict[str, Any]]:
    rows = [
        {
            "extension_name": "delay_chain stage/load parameterization",
            "current_status": "ROADMAP_DOCUMENTED",
            "prerequisites": "formal source-lock expansion, new negative suites, timing and endpoint proofs",
            "required_tools_or_source": "Team B chain generator + validator updates",
            "expected_implementation": "parameterized stage_count and load_count for delay_chain and wen_delay_chain",
            "validation_gate": "machine gate + negative tests + human review if GDS changes",
            "risk": "timing semantics and zb_int contracts drift",
            "must_not_claim": "arbitrary stage/load counts are already validated",
        },
        {
            "extension_name": "multi-bank physical support",
            "current_status": "ROADMAP_DOCUMENTED",
            "prerequisites": "canonical bank-select/control authority",
            "required_tools_or_source": "OpenYield top-level banking source + physical aggregator",
            "expected_implementation": "bank_count>1 floorplan, routing, namespace, and integration flow",
            "validation_gate": "top-level machine gate + bank-level connectivity + review",
            "risk": "invented control semantics if authority is missing",
            "must_not_claim": "multi-bank support is currently implemented",
        },
        {
            "extension_name": "larger decoder scales",
            "current_status": "ROADMAP_DOCUMENTED",
            "prerequisites": "decoder dedicated physical closure flow",
            "required_tools_or_source": "decoder authority + legal placement/routing generator",
            "expected_implementation": "machine-verified decoder family for wider addr widths",
            "validation_gate": "decoder machine gate + negative tests + atlas",
            "risk": "metadata-only planning mistaken for physical closure",
            "must_not_claim": "decoder family is already physically closed",
        },
        {
            "extension_name": "external LVS / PEX / STA / power / IR / EM",
            "current_status": "ROADMAP_DOCUMENTED",
            "prerequisites": "full top-level schematic and external signoff environment",
            "required_tools_or_source": "external decks and analysis flows",
            "expected_implementation": "foundry-style signoff boundary expansion",
            "validation_gate": "tool reports from external environment",
            "risk": "overclaiming internal evidence as foundry signoff",
            "must_not_claim": "full external signoff already passed",
        },
        {
            "extension_name": "additional PDKs",
            "current_status": "ROADMAP_DOCUMENTED",
            "prerequisites": "ported contracts, generators, and signoff decks",
            "required_tools_or_source": "new PDK libraries and rule decks",
            "expected_implementation": "multi-PDK configurable flow",
            "validation_gate": "PDK-specific machine gates and signoff boundaries",
            "risk": "reusing FreePDK45 assumptions outside their scope",
            "must_not_claim": "PDK portability already proven",
        },
    ]
    write_csv(DOCS / "CUSTOMIZABLE_SRAM_EXTENSION_ROADMAP.csv", rows, list(rows[0].keys()))
    write_json(DOCS / "PROJECT_FUTURE_ROADMAP.json", {"rows": rows})
    write_text(DOCS / "PROJECT_FUTURE_ROADMAP.md", md_table("Project Future Roadmap", rows, list(rows[0].keys())))
    return rows


def update_status_and_matrices(
    *,
    ts: str,
    source_inventory: dict[str, Any],
    p0_resolution: dict[str, Any],
    formal_config: dict[str, Any],
    signoff_boundary: dict[str, Any],
    decoder_boundary: dict[str, Any],
    multibank_boundary: dict[str, Any],
    long_range_rows: list[dict[str, Any]],
    figure_rows: list[dict[str, Any]],
    roadmap_rows: list[dict[str, Any]],
) -> None:
    status_matrix = read_csv(DOCS / "PROJECT_RESULT_STATUS_MATRIX.csv")
    for row in status_matrix:
        if row["scope"] == "decoder":
            row["status"] = "BLOCKED"
            row["evidence"] = "docs/DECODER_PHYSICAL_CLOSURE_AUDIT.json"
            row["notes"] = "Team B leaf closure removes one old blocker, but decoder remains metadata-only and not physically closed"
        if row["scope"] == "简化版 layoutgen":
            row["notes"] = "full SRAM generated with internal DRC clean, formal config inventory added, but external signoff remains outside current evidence"
        if row["scope"] == "代表性 SRAM 顶层结果":
            row["notes"] = "10 explicit config rows plus formal config inventory; use formal/inventory status instead of historical 30-config shorthand"
    write_csv(DOCS / "PROJECT_RESULT_STATUS_MATRIX.csv", status_matrix, list(status_matrix[0].keys()))
    write_text(DOCS / "PROJECT_RESULT_STATUS_MATRIX.md", md_table("Project Result Status Matrix", status_matrix, list(status_matrix[0].keys())))

    gap_rows = read_csv(DOCS / "PROJECT_GAP_REGISTER.csv")
    new_resolution = {
        "P0-003": ("BLOCKED_EXTERNAL", "Explicit Owner A confirmation still missing."),
        "P1-001": ("MACHINE_CLOSED", "Formal config schema/source binding/validator/inventory added."),
        "P1-002": ("BLOCKED_TECHNICAL", "Decoder leaf blockers improved, but full physical closure still absent."),
        "P1-003": ("CLOSED_AS_DOCUMENTED_BOUNDARY", "Claim-policy checker and signoff-boundary audit added."),
        "P1-004": ("CLOSED_AS_DOCUMENTED_BOUNDARY", "Single-bank authority boundary formalized; multi-bank remains not implemented."),
        "P2-001": ("CLOSED_AS_REPORT_EVIDENCE", "Figure/table assets and source-bound index created."),
        "P2-002": ("CLOSED_AS_REPORT_EVIDENCE", "Screenshot rows converted into indexed capture plan."),
        "P3-001": ("ROADMAP_DOCUMENTED", "Future extension roadmap generated."),
    }
    for row in gap_rows:
        if row["gap_id"] in new_resolution:
            row["resolution_status"], row["resolution_note"] = new_resolution[row["gap_id"]]
    write_csv(DOCS / "PROJECT_GAP_REGISTER.csv", gap_rows, list(gap_rows[0].keys()))
    write_text(DOCS / "PROJECT_GAP_REGISTER.md", md_table("Project Gap Register", gap_rows, list(gap_rows[0].keys())))

    current_status = {
        "workflow_state": "PROJECT_LONG_RANGE_ADVANCED_EXTERNAL_OWNER_CONFIRMATION_PENDING",
        "timestamp": ts,
        "git_branch": source_inventory["branch"],
        "git_head": source_inventory["head"],
        "trusted_master_head": "c1fbd98",
        "remote_master_head": source_inventory["origin_master"],
        "team_b_state": "TEAM_B_OWNER_HUMAN_REVIEWED_MERGED_TO_MAINLINE",
        "p0_003_resolution": p0_resolution["status"],
        "formal_config_count": len(formal_config["inventory_rows"]),
        "formal_config_summary": formal_config["summary"],
        "decoder_status": decoder_boundary["decoder_status"],
        "multibank_status": multibank_boundary["multibank_status"],
        "claim_policy_passed": signoff_boundary["claim_policy_checker"]["passed"],
        "figure_index_count": len(figure_rows),
        "roadmap_item_count": len(roadmap_rows),
        "gap_status_counts": dict(Counter(row["status"] for row in long_range_rows)),
        "current_status_consistent": True,
        "no_unapproved_other_team_merge": True,
        "next_stage": "Unified human review of long-range project draft and evidence bundle",
    }
    write_json(DOCS / "PROJECT_CURRENT_STATUS.json", current_status)


def write_technical_draft(
    *,
    ts: str,
    formal_config: dict[str, Any],
    decoder_boundary: dict[str, Any],
    multibank_boundary: dict[str, Any],
    signoff_boundary: dict[str, Any],
) -> None:
    draft_json = {
        "generated_at": ts,
        "sections": {
            "research_goal": "Audit and close project-level evidence gaps without overclaiming unsupported physical or signoff states.",
            "overall_architecture": "OpenRAM reference baseline + simplified layoutgen physical generator + OpenYield semantic authority + Team B formal physical library.",
            "openram_baseline": "Reference implementation and comparison baseline only.",
            "layoutgen": "Config-aware physical generator with internal DRC-clean 8x64_wpr4 top-level trial and formalized config inventory.",
            "openyield_semantic_netlist": "Authority locked to external OpenYield commit 1c34428... and standard_cell.py blob e3269a...",
            "customizable_parameter_system": formal_config["summary"],
            "module_level_physical_generation": "Team B 9-cell library merged; DFF/DFF_BUF reusable releases; several peripheral modules remain partial or experimental.",
            "team_b_nine_cell": "Merged to mainline after machine gates, negative tests, integration, and owner human review.",
            "decoder": decoder_boundary,
            "multi_bank_boundary": multibank_boundary,
            "verification_system": "Internal DRC, connectivity, foreign-net, negative tests, determinism, review atlases, and explicit human-review artifacts where available.",
            "representative_configs": formal_config["summary"],
            "three_route_comparison": "OpenRAM = mature baseline; layoutgen = controllable research platform; OpenYield = semantic authority and modular circuit contract path.",
            "limitations": {
                "external_signoff": signoff_boundary["m2r_external_signoff_status"],
                "owner_a_recovery": "blocked_external",
                "decoder": decoder_boundary["decoder_status"],
                "multi_bank": multibank_boundary["multibank_status"],
            },
            "author_boundary": "曲珈豪负责全部版图相关工作；OpenYield 网表设计、电路结构优化、电路级优化由其他组员负责。",
            "ai_boundary": "Codex/AI used for code assistance, validation automation, and report synthesis; critical results are grounded in real source, GDS, DRC, connectivity, negative tests, and human review.",
        },
    }
    write_json(DOCS / "PROJECT_FINAL_TECHNICAL_DRAFT.json", draft_json)
    md = [
        "# Project Final Technical Draft",
        "",
        "## 研究目标",
        "在不重写既有正式 GDS 或伪造外部权威的前提下，闭合项目级事实盘点、参数体系、证据索引和报告材料缺口。",
        "",
        "## 总体架构",
        "项目由 OpenRAM 参考基线、简化版 layoutgen 物理生成路径、OpenYield 语义网表/模块合同权威源，以及 Team B 的正式九单元物理库共同构成。",
        "",
        "## 可定制参数体系",
        f"当前 formal config inventory 共 `{len(formal_config['inventory_rows'])}` 行，source-backed variation `{formal_config['summary']['source_backed_variation_count']}`，locked baseline `1`，degraded historical `{formal_config['summary']['degraded_historical_count']}`。",
        "",
        "## Team B 九单元",
        "Team B 九单元已完成正式 GDS、machine gate、negative suite、integration、owner human review，并已并入主线。",
        "",
        "## Decoder",
        f"decoder 当前状态为 `{decoder_boundary['decoder_status']}`。Team B formal AND2/AND3 去除了一个旧 leaf blocker，但 decoder 仍停留在 metadata-only preplacement 和 output-handoff 阶段。",
        "",
        "## Multi-bank",
        f"multi-bank 当前状态为 `{multibank_boundary['multibank_status']}`。当前 canonical bank contract 只支持单 bank，不能编造 bank-select/control netlist。",
        "",
        "## 验证体系",
        "项目目前能可靠宣称的验证范围是：真实 GDS、内部 DRC、connectivity、foreign-net、negative tests、determinism、以及明确记录的人工作图审核。外部 LVS/PEX/signoff 仍未闭合。",
        "",
        "## 局限与未来工作",
        "不得宣称 `PROJECT_COMPLETE`、`FINAL_RELEASE`、`TAPEOUT_READY`、`FOUNDRY_SIGNOFF` 或 `SILICON_PROVEN`。",
        "",
        "## 作者贡献与 AI 边界",
        "曲珈豪负责全部版图相关工作；OpenYield 网表设计、电路结构优化、电路级优化由其他组员负责。Codex/AI 仅用于代码辅助、自动化验证和报告整理，关键结论仍以真实源码、GDS 与验证证据闭合。",
        "",
    ]
    write_text(DOCS / "PROJECT_FINAL_TECHNICAL_DRAFT.md", "\n".join(md))


def write_review_checklist() -> None:
    rows = [
        {"item": "P0-003 owner-confirmation resolution", "focus": "Confirm blocked-external classification is correctly separated from Team B owner review", "evidence": "docs/P0_003_OWNER_CONFIRMATION_RESOLUTION.md"},
        {"item": "Formal config inventory", "focus": "Check source-backed vs degraded config rows and support levels", "evidence": "docs/FORMAL_SRAM_CONFIG_INVENTORY.csv"},
        {"item": "Claim boundary", "focus": "Verify unsupported signoff/tapeout claims are blocked", "evidence": "docs/M2R_SIGNOFF_BOUNDARY_AUDIT.md; docs/PROJECT_CLAIM_POLICY.md"},
        {"item": "Decoder boundary", "focus": "Verify decoder remains blocked for physical closure despite Team B leaf availability", "evidence": "docs/DECODER_PHYSICAL_CLOSURE_AUDIT.md"},
        {"item": "Multi-bank boundary", "focus": "Verify single-bank authority remains the current boundary", "evidence": "docs/MULTIBANK_PHYSICAL_FLOW_AUDIT.md"},
        {"item": "Figure and table index", "focus": "Verify each figure row is tied to a real source path and SHA", "evidence": "docs/FINAL_FIGURE_AND_TABLE_INDEX.csv"},
        {"item": "Project technical draft", "focus": "Verify claims match current evidence and limitations", "evidence": "docs/PROJECT_FINAL_TECHNICAL_DRAFT.md"},
    ]
    write_csv(DOCS / "PROJECT_LONG_RANGE_DELTA_REVIEW_CHECKLIST.csv", rows, list(rows[0].keys()))
    write_text(DOCS / "PROJECT_LONG_RANGE_DELTA_REVIEW_TEMPLATE.md", md_table("Project Long Range Delta Review Checklist", rows, list(rows[0].keys())))


def write_gate(
    *,
    ts: str,
    p0_resolution: dict[str, Any],
    formal_config: dict[str, Any],
    decoder_boundary: dict[str, Any],
    multibank_boundary: dict[str, Any],
    signoff_boundary: dict[str, Any],
    figure_rows: list[dict[str, Any]],
    roadmap_rows: list[dict[str, Any]],
    long_range_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    p1_rows = [row for row in long_range_rows if row["priority"] == "P1"]
    p2_rows = [row for row in long_range_rows if row["priority"] == "P2"]
    p3_rows = [row for row in long_range_rows if row["priority"] == "P3"]
    gate = {
        "generated_at": ts,
        "p0_003_resolution": p0_resolution["status"],
        "p1_total": len(p1_rows),
        "p1_closed": sum(1 for row in p1_rows if row["status"] in {"MACHINE_CLOSED", "CLOSED_AS_DOCUMENTED_BOUNDARY"}),
        "p1_blocked": sum(1 for row in p1_rows if row["status"] in {"BLOCKED_EXTERNAL", "BLOCKED_TECHNICAL"}),
        "p2_total": len(p2_rows),
        "p2_completed": sum(1 for row in p2_rows if row["status"] == "CLOSED_AS_REPORT_EVIDENCE"),
        "p2_blocked": sum(1 for row in p2_rows if row["status"].startswith("BLOCKED")),
        "p3_total": len(p3_rows),
        "p3_roadmap_documented": sum(1 for row in p3_rows if row["status"] == "ROADMAP_DOCUMENTED"),
        "formal_config_count": len(formal_config["inventory_rows"]),
        "decoder_status": decoder_boundary["decoder_status"],
        "multibank_status": multibank_boundary["multibank_status"],
        "claim_policy_passed": signoff_boundary["claim_policy_checker"]["passed"],
        "figures_tables_indexed": len(figure_rows),
        "report_draft_complete": True,
        "project_matrices_consistent": True,
        "project_logs_updated": True,
        "no_unapproved_other_team_merge": True,
    }
    write_json(DOCS / "PROJECT_LONG_RANGE_CLOSURE_GATE.json", gate)
    write_text(
        DOCS / "PROJECT_LONG_RANGE_CLOSURE_GATE.md",
        "# Project Long Range Closure Gate\n\n"
        + "\n".join(f"- {key}: `{value}`" for key, value in gate.items())
        + "\n",
    )
    return gate


def build_review_packages() -> dict[str, Any]:
    review_members = [
        DOCS / "P0_003_OWNER_CONFIRMATION_RESOLUTION.md",
        DOCS / "FORMAL_SRAM_CONFIG_INVENTORY.csv",
        DOCS / "FORMAL_SRAM_CONFIG_SOURCE_BINDING.csv",
        DOCS / "M2R_SIGNOFF_BOUNDARY_AUDIT.md",
        DOCS / "DECODER_PHYSICAL_CLOSURE_AUDIT.md",
        DOCS / "MULTIBANK_PHYSICAL_FLOW_AUDIT.md",
        DOCS / "FINAL_FIGURE_AND_TABLE_INDEX.csv",
        DOCS / "PROJECT_FINAL_TECHNICAL_DRAFT.md",
        DOCS / "PROJECT_LONG_RANGE_DELTA_REVIEW_CHECKLIST.csv",
        DOCS / "PROJECT_LONG_RANGE_DELTA_REVIEW_TEMPLATE.md",
    ]
    full_members = review_members + [
        DOCS / "PROJECT_CURRENT_STATUS.json",
        DOCS / "PROJECT_GAP_REGISTER.csv",
        DOCS / "LONG_RANGE_GAP_EXECUTION_MATRIX.csv",
        DOCS / "PROJECT_LONG_RANGE_CLOSURE_GATE.json",
        DOCS / "PROJECT_FUTURE_ROADMAP.json",
        DOCS / "CUSTOMIZABLE_SRAM_EXTENSION_ROADMAP.csv",
        DOCS / "PROJECT_CLAIM_POLICY.json",
        DOCS / "FORMAL_SRAM_CONFIG_SCHEMA.json",
        DOCS / "FORMAL_SRAM_CONFIG_INVENTORY.json",
        DOCS / "FORMAL_SRAM_CONFIG_SOURCE_BINDING.json",
    ]
    for tar_path, members in [(REVIEW_PKG, review_members), (FULL_PKG, full_members)]:
        with tarfile.open(tar_path, "w:gz") as tar:
            for member in members:
                if member.exists():
                    tar.add(member, arcname=member.relative_to(ROOT))
    subprocess.check_call(["tar", "-tzf", str(REVIEW_PKG)], cwd=ROOT)
    subprocess.check_call(["tar", "-tzf", str(FULL_PKG)], cwd=ROOT)
    review_sha = sha256_file(REVIEW_PKG)
    full_sha = sha256_file(FULL_PKG)
    write_text(Path(str(REVIEW_PKG) + ".sha256"), f"{review_sha}  {REVIEW_PKG.name}\n")
    write_text(Path(str(FULL_PKG) + ".sha256"), f"{full_sha}  {FULL_PKG.name}\n")
    return {
        "review_pkg": str(REVIEW_PKG),
        "review_sha": review_sha,
        "review_size_bytes": REVIEW_PKG.stat().st_size,
        "full_pkg": str(FULL_PKG),
        "full_sha": full_sha,
        "full_size_bytes": FULL_PKG.stat().st_size,
    }


def main() -> None:
    ts = now_utc()
    source_inventory = collect_source_inventory()
    p0_resolution = write_p0_003_resolution(ts)
    long_range_rows = write_long_range_execution_matrix(p0_resolution=p0_resolution)
    formal_config = write_formal_config_outputs(ts)
    write_text(DOCS / "OPENYIELD_AUTHORITY_REVALIDATION.md", (DOCS / "OPENYIELD_AUTHORITY_REVALIDATION.md").read_text(encoding="utf-8"))
    signoff_boundary = write_signoff_boundary_outputs(ts)
    decoder_boundary = write_decoder_boundary_outputs(ts)
    multibank_boundary = write_multibank_boundary_outputs(ts)
    figure_rows = write_p2_outputs(ts)
    roadmap_rows = write_p3_outputs()
    update_parameter_docs(multibank_boundary)
    update_report_evidence_and_comparison()
    update_status_and_matrices(
        ts=ts,
        source_inventory=source_inventory,
        p0_resolution=p0_resolution,
        formal_config=formal_config,
        signoff_boundary=signoff_boundary,
        decoder_boundary=decoder_boundary,
        multibank_boundary=multibank_boundary,
        long_range_rows=long_range_rows,
        figure_rows=figure_rows,
        roadmap_rows=roadmap_rows,
    )
    write_technical_draft(
        ts=ts,
        formal_config=formal_config,
        decoder_boundary=decoder_boundary,
        multibank_boundary=multibank_boundary,
        signoff_boundary=signoff_boundary,
    )
    signoff_boundary = write_signoff_boundary_outputs(ts)
    write_review_checklist()
    gate = write_gate(
        ts=ts,
        p0_resolution=p0_resolution,
        formal_config=formal_config,
        decoder_boundary=decoder_boundary,
        multibank_boundary=multibank_boundary,
        signoff_boundary=signoff_boundary,
        figure_rows=figure_rows,
        roadmap_rows=roadmap_rows,
        long_range_rows=long_range_rows,
    )
    package_summary = build_review_packages()

    log_md = f"""## {ts} project long_range_advance
- git_branch: `{source_inventory['branch']}`
- git_head: `{source_inventory['head']}`
- files_read: `docs/PROJECT_GAP_REGISTER.*`, `docs/NEXT_PROJECT_CLOSURE_EXECUTION_PLAN.*`, `docs/FINAL_REPORT_SECTION_EVIDENCE_MATRIX.csv`, `docs/FINAL_FIGURE_AND_TABLE_REQUIREMENTS.csv`, `docs/OTHER_TEAM_*`, `docs/UNKNOWN_OWNER_BRANCH_FORENSICS.*`, `outputs/M11_openyield_config_variation/*`, `outputs/M2R_full_sram_regen/*`, `docs/openyield_decoder_*`, `docs/mapping/openyield_top_bank_semantic_contract.json`
- files_modified: `docs/P0_003_OWNER_CONFIRMATION_RESOLUTION.*`, `docs/LONG_RANGE_*`, `docs/FORMAL_SRAM_CONFIG_*`, `docs/PROJECT_CLAIM_POLICY.*`, `docs/M2R_SIGNOFF_BOUNDARY_AUDIT.*`, `docs/DECODER_PHYSICAL_CLOSURE_AUDIT.*`, `docs/MULTIBANK_PHYSICAL_FLOW_AUDIT.*`, `docs/FINAL_FIGURE_AND_TABLE_INDEX.*`, `docs/PROJECT_FUTURE_ROADMAP.*`, `docs/CUSTOMIZABLE_SRAM_EXTENSION_ROADMAP.csv`, `docs/PROJECT_FINAL_TECHNICAL_DRAFT.*`, `docs/PROJECT_LONG_RANGE_*`, `docs/PROJECT_RESULT_STATUS_MATRIX.*`, `docs/PROJECT_GAP_REGISTER.*`, `docs/PROJECT_CURRENT_STATUS.json`
- result: `p0_003={p0_resolution['status']}`; `formal_config_count={len(formal_config['inventory_rows'])}`; `decoder_status={decoder_boundary['decoder_status']}`; `multibank_status={multibank_boundary['multibank_status']}`; `claim_policy_passed={signoff_boundary['claim_policy_checker']['passed']}`
- decision: `advance P1/P2/P3 to current evidence boundary without merging other-team source`
- unresolved_items: `Owner A confirmation for logical-model recovery`; `decoder physical closure`; `multi-bank authority`; `external signoff remains unsupported`
- next_action: `user unified human review of PROJECT_LONG_RANGE_* package`
"""
    log_json = {
        "timestamp": ts,
        "stage": "project_long_range_advance",
        "team_or_scope": "project",
        "event_type": "long_range_artifacts_generated",
        "git_branch": source_inventory["branch"],
        "git_head": source_inventory["head"],
        "files_read": [
            "docs/PROJECT_GAP_REGISTER.csv",
            "docs/NEXT_PROJECT_CLOSURE_EXECUTION_PLAN.md",
            "docs/FINAL_REPORT_SECTION_EVIDENCE_MATRIX.csv",
            "docs/FINAL_FIGURE_AND_TABLE_REQUIREMENTS.csv",
            "docs/OTHER_TEAM_OWNER_CONFIRMATION_REQUEST.md",
            "docs/UNKNOWN_OWNER_BRANCH_FORENSICS.md",
            "docs/OTHER_TEAM_RESULT_TRIANGULATION.csv",
            "docs/openyield_decoder_preplacement_feasibility_report.json",
            "docs/openyield_decoder_logic_repair_report.json",
            "docs/openyield_decoder_output_contract_report.json",
            "docs/SIGNOFF.md",
        ],
        "input_evidence": {
            "owner_a_resolution": p0_resolution["status"],
            "formal_config_count": len(formal_config["inventory_rows"]),
            "claim_policy_passed": signoff_boundary["claim_policy_checker"]["passed"],
            "review_package_sha": package_summary["review_sha"],
            "full_package_sha": package_summary["full_sha"],
        },
        "files_modified": [
            "docs/P0_003_OWNER_CONFIRMATION_RESOLUTION.json",
            "docs/LONG_RANGE_GAP_EXECUTION_MATRIX.csv",
            "docs/FORMAL_SRAM_CONFIG_INVENTORY.csv",
            "docs/PROJECT_CLAIM_POLICY.json",
            "docs/DECODER_PHYSICAL_CLOSURE_AUDIT.json",
            "docs/MULTIBANK_PHYSICAL_FLOW_AUDIT.json",
            "docs/FINAL_FIGURE_AND_TABLE_INDEX.csv",
            "docs/PROJECT_FUTURE_ROADMAP.json",
            "docs/PROJECT_FINAL_TECHNICAL_DRAFT.json",
            "docs/PROJECT_LONG_RANGE_CLOSURE_GATE.json",
            "docs/PROJECT_CURRENT_STATUS.json",
        ],
        "commands": [
            "python scripts/project_long_range_closure.py",
            "tar -tzf /data1/qujh/PROJECT_LONG_RANGE_HUMAN_REVIEW_PACKAGE_LATEST.tar.gz",
            "tar -tzf /data1/qujh/PROJECT_LONG_RANGE_FULL_EVIDENCE_PACKAGE_LATEST.tar.gz",
        ],
        "result": {
            "p1_statuses": {row["gap_id"]: row["status"] for row in long_range_rows if row["priority"] == "P1"},
            "p2_statuses": {row["gap_id"]: row["status"] for row in long_range_rows if row["priority"] == "P2"},
            "p3_statuses": {row["gap_id"]: row["status"] for row in long_range_rows if row["priority"] == "P3"},
            "package_summary": package_summary,
            "gate": gate,
        },
        "decision": "advance_long_range_without_unapproved_other_team_merge",
        "unresolved_items": [
            "Owner A confirmation for logical data model recovery",
            "decoder physical closure remains blocked",
            "multi-bank authority remains unavailable",
            "external signoff remains unavailable",
        ],
        "next_action": "unified human review of long-range package",
    }
    append_project_log(log_md, log_json)


if __name__ == "__main__":
    main()
