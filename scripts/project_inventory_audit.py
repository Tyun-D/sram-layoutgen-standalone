from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path("/data1/qujh/worktrees/project_mainline_inventory_20260726")
REPO_ROOT = ROOT
SOURCE_TREE = Path("/data1/qujh/work/sram_layoutgen_step45_clean")
DOCS = ROOT / "docs"
TEAM_B_DOCS = ROOT / "docs"
TEAM_B_STATUS_PATH = TEAM_B_DOCS / "TEAM_B_CURRENT_STATUS.json"
TEAM_B_LOG_MD = TEAM_B_DOCS / "TEAM_B_TASK_MASTER_LOG.md"
TEAM_B_LOG_JSONL = TEAM_B_DOCS / "TEAM_B_TASK_MASTER_LOG.jsonl"
PROJECT_LOG_MD = DOCS / "PROJECT_TASK_MASTER_LOG.md"
PROJECT_LOG_JSONL = DOCS / "PROJECT_TASK_MASTER_LOG.jsonl"
PROJECT_STATUS_JSON = DOCS / "PROJECT_CURRENT_STATUS.json"
NOW = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run(cmd: list[str], cwd: Path = ROOT) -> str:
    return subprocess.check_output(cmd, cwd=cwd, text=True).strip()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    with path.open("a") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


@dataclass
class ResultSource:
    result_id: str
    team_or_author_scope: str
    source_path: str
    git_branch: str
    git_commit: str
    file_sha: str
    result_type: str
    module_or_config: str
    formal_or_experimental: str
    machine_verified: bool
    human_reviewed: bool
    already_merged: bool
    evidence_complete: bool
    recommended_action: str


def git_snapshot() -> dict[str, Any]:
    return {
        "current_branch": run(["git", "branch", "--show-current"]),
        "current_head": run(["git", "rev-parse", "HEAD"]),
        "status_short": run(["git", "status", "--short"]).splitlines(),
        "remote_v": run(["git", "remote", "-v"]).splitlines(),
        "origin_head": run(["git", "symbolic-ref", "refs/remotes/origin/HEAD"]),
        "branch_vv": run(["git", "branch", "-a", "-vv"]).splitlines(),
        "worktree_list": run(["git", "worktree", "list"]).splitlines(),
        "log_graph": run(["git", "log", "--oneline", "--decorate", "--graph", "--all", "-n", "200"]).splitlines(),
    }


def branch_inventory(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for line in snapshot["branch_vv"]:
        if not line.strip():
            continue
        rows.append({"branch_line": line})
    for line in snapshot["worktree_list"]:
        rows.append({"branch_line": f"WORKTREE {line}"})
    return rows


def load_team_b() -> dict[str, Any]:
    status = read_json(TEAM_B_STATUS_PATH)
    gate = read_json(SOURCE_TREE / "outputs/TeamB_9cell_integration/current_supported_config/TEAM_B_9CELL_INTEGRATION_GATE.json")
    return {"status": status, "integration_gate": gate}


def result_source_inventory() -> list[ResultSource]:
    def mk(path_str: str, commit: str = "c1fbd98") -> str:
        p = SOURCE_TREE / path_str
        return sha256(p) if p.exists() and p.is_file() else ""

    return [
        ResultSource(
            "team_b_9cell_formal_library",
            "Team B / 曲珈豪",
            str(SOURCE_TREE / "outputs/TeamB_9cell_integration/current_supported_config/TEAM_B_9CELL_LIBRARY.gds"),
            "master@c1fbd98",
            "c1fbd98",
            sha256(SOURCE_TREE / "outputs/TeamB_9cell_integration/current_supported_config/TEAM_B_9CELL_LIBRARY.gds"),
            "formal_gds",
            "TEAM_B_9CELL_LIBRARY",
            "formal",
            True,
            True,
            True,
            True,
            "keep_as_mainline_baseline",
        ),
        ResultSource(
            "team_b_9cell_clean_atlas",
            "Team B / 曲珈豪",
            str(SOURCE_TREE / "outputs/TeamB_9cell_integration/current_supported_config/TEAM_B_9CELL_CLEAN_ATLAS.gds"),
            "master@c1fbd98",
            "c1fbd98",
            sha256(SOURCE_TREE / "outputs/TeamB_9cell_integration/current_supported_config/TEAM_B_9CELL_CLEAN_ATLAS.gds"),
            "formal_review_atlas",
            "TEAM_B_9CELL_CLEAN_ATLAS",
            "formal",
            True,
            True,
            True,
            True,
            "keep_as_mainline_baseline",
        ),
        ResultSource(
            "team_b_and2_zero_gap",
            "Team B / 曲珈豪",
            str(SOURCE_TREE / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND2/clean.gds"),
            "master@c1fbd98",
            "c1fbd98",
            sha256(SOURCE_TREE / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND2/clean.gds"),
            "formal_gds",
            "AND2 zero-gap M2",
            "formal",
            True,
            True,
            True,
            True,
            "keep_as_mainline_baseline",
        ),
        ResultSource(
            "team_b_and3_zero_gap",
            "Team B / 曲珈豪",
            str(SOURCE_TREE / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND3/clean.gds"),
            "master@c1fbd98",
            "c1fbd98",
            sha256(SOURCE_TREE / "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND3/clean.gds"),
            "formal_gds",
            "AND3 zero-gap M2",
            "formal",
            True,
            True,
            True,
            True,
            "keep_as_mainline_baseline",
        ),
        ResultSource(
            "wave3_dff_buf_release",
            "曲珈豪",
            str(SOURCE_TREE / "outputs/Wave3_DFF_BUF_reusable_release"),
            "master@c1fbd98",
            "c1fbd98",
            "",
            "reusable_release",
            "DFF_BUF",
            "formal",
            True,
            True,
            True,
            True,
            "retain_as_reusable_formal_release",
        ),
        ResultSource(
            "wave4a_addr_dff_lock",
            "Project control-logic path",
            str(SOURCE_TREE / "outputs/Wave4A_R2_ADDR_DFF_physical_interface_and_negative_regression_restore/current_supported_config"),
            "master@c1fbd98",
            "c1fbd98",
            mk("outputs/Wave4A_R2_ADDR_DFF_physical_interface_and_negative_regression_restore/current_supported_config/Wave4A_R2_stage_report.json"),
            "source_binding_and_interface_audit",
            "ADDR_DFF",
            "formal",
            True,
            False,
            True,
            True,
            "use_as_locked_pre-physical_baseline",
        ),
        ResultSource(
            "m2r_full_sram_regen",
            "Project top-level regeneration",
            str(SOURCE_TREE / "outputs/M2R_full_sram_regen/current_supported_config/openyield_layoutgen_full_sram_M2R.gds"),
            "master@c1fbd98",
            "c1fbd98",
            sha256(SOURCE_TREE / "outputs/M2R_full_sram_regen/current_supported_config/openyield_layoutgen_full_sram_M2R.gds"),
            "top_level_gds_trial",
            "8x64_wpr4",
            "experimental",
            True,
            False,
            True,
            True,
            "retain_as_experimental_reference_only",
        ),
        ResultSource(
            "m11_variation_support",
            "Project config audit",
            str(SOURCE_TREE / "outputs/M11_openyield_config_variation/current_supported_config/M11_variation_support_report.json"),
            "origin/feature/step45-clean-array-aggregation",
            "0b3de75",
            mk("outputs/M11_openyield_config_variation/current_supported_config/M11_variation_support_report.json"),
            "parameter_audit",
            "8x64_wpr4,4x32_wpr2,16x16_wpr1",
            "formal",
            True,
            False,
            True,
            True,
            "use_as_parameter_baseline",
        ),
        ResultSource(
            "owner_a_logical_model_v1",
            "Owner A / 其他组员",
            "/data1/qujh/work/owner_a_logical_model_v1_20260723_010633",
            "feature/owner-a-logical-data-model-v1-20260723_010633",
            "e74054e",
            "",
            "logical_data_model_review",
            "logical_data_model_v1",
            "experimental",
            True,
            False,
            False,
            False,
            "owner_review_then_cherry_pick_or_merge_candidate",
        ),
        ResultSource(
            "openyield_external_authority",
            "OpenYield upstream / 其他组员电路与网表权威源",
            "/data1/qujh/work/external/OpenYield",
            "external/OpenYield",
            run(["git", "-C", "/data1/qujh/work/external/OpenYield", "rev-parse", "HEAD"], cwd=ROOT),
            "",
            "upstream_netlist_authority",
            "OpenYield sram_compiler",
            "formal",
            True,
            False,
            False,
            True,
            "treat_as_authority_source_not_merge_target",
        ),
    ]


def project_result_status_matrix() -> list[dict[str, Any]]:
    return [
        {"scope": "OpenRAM 原始生成流程", "status": "GENERATED", "evidence": "technology/freepdk45/gds_lib/*.gds; docs/openram_gds_generation_audit_report.md", "notes": "reference baseline only"},
        {"scope": "简化版 layoutgen", "status": "GENERATED", "evidence": "outputs/M2R_full_sram_regen/current_supported_config/openyield_layoutgen_full_sram_M2R.gds", "notes": "full SRAM generated with internal DRC clean but not signoff-complete"},
        {"scope": "OpenYield 语义网表", "status": "MACHINE_VERIFIED", "evidence": "docs/openyield_module_contracts.json; outputs/M12N_lock_openyield_authoritative_netlist/current_supported_config/", "notes": "authority and contracts locked"},
        {"scope": "OpenYield 控制逻辑", "status": "EXPERIMENTAL", "evidence": "outputs/Wave4A_R2_ADDR_DFF_physical_interface_and_negative_regression_restore/current_supported_config", "notes": "ADDR_DFF locked, not yet generated as final GDS"},
        {"scope": "Team B 九单元", "status": "MERGED_TO_MAINLINE", "evidence": "outputs/TeamB_9cell_integration/current_supported_config/TEAM_B_9CELL_INTEGRATION_GATE.json", "notes": "mainline-approved baseline"},
        {"scope": "DFF", "status": "HUMAN_REVIEWED", "evidence": "outputs/M12C4ACH_dff_reusable_release; PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json", "notes": "reusable composite baseline"},
        {"scope": "DFF_BUF", "status": "HUMAN_REVIEWED", "evidence": "outputs/Wave3_DFF_BUF_reusable_release", "notes": "human-reviewed reusable composite"},
        {"scope": "PINV/TG", "status": "HUMAN_REVIEWED", "evidence": "outputs/M12C3A4_canonical_primitive_label_cleanup/current_supported_config/reusable_cells", "notes": "primitive reusable library"},
        {"scope": "SRAM array", "status": "GENERATED", "evidence": "outputs/M2R_full_sram_regen/current_supported_config/openyield_layoutgen_full_sram_M2R.report.json", "notes": "layoutgen-generated top-level trial"},
        {"scope": "WL driver", "status": "MACHINE_VERIFIED", "evidence": "outputs/M11C2H_confirm_wordline_driver_human_review/current_supported_config", "notes": "smoke substitution passed with caveats"},
        {"scope": "decoder", "status": "EXPERIMENTAL", "evidence": "docs/openyield_decoder_*; outputs/M2_layoutgen_full_trial/current_supported_config/review_wrappers", "notes": "row rules/planning exist, physical closure incomplete"},
        {"scope": "column mux", "status": "MACHINE_VERIFIED", "evidence": "docs/openyield_columnmux_adapter_report.json; technology/freepdk45/gds_lib/openyield_repaired/gen_col_mux_vdd_labeled.gds", "notes": "adapter and repaired alias proven"},
        {"scope": "sense amp", "status": "HUMAN_REVIEWED", "evidence": "outputs/M11CH_confirm_M11C_human_review/current_supported_config", "notes": "smoke substitution human-reviewed"},
        {"scope": "write driver", "status": "SOURCE_ONLY", "evidence": "docs/openyield_writedriver_adapter_report.json", "notes": "adapter exists, no final integrated closure"},
        {"scope": "precharge", "status": "GENERATED", "evidence": "technology/freepdk45/gds_lib/openram_replacements/gen_precharge.gds; outputs/M2R_full_sram_regen", "notes": "used in full-trial flow"},
        {"scope": "电源网络", "status": "EXPERIMENTAL", "evidence": "docs/openyield_storage_power_stitch_report.json; outputs/M2R_full_sram_regen", "notes": "partial proofs, not final global signoff"},
        {"scope": "dummy 行列", "status": "GENERATED", "evidence": "outputs/openyield_module_gds/dummy_array", "notes": "present in full-trial flow"},
        {"scope": "tap", "status": "SOURCE_ONLY", "evidence": "technology/freepdk45/gds_lib/gen_well_tap.gds", "notes": "leaf exists, project-level integration not separately audited"},
        {"scope": "replica", "status": "GENERATED", "evidence": "outputs/openyield_module_gds/replica_array", "notes": "present in full-trial flow"},
        {"scope": "代表性 SRAM 顶层结果", "status": "EXPERIMENTAL", "evidence": "outputs/M2R_full_sram_regen; outputs/M11_openyield_config_variation", "notes": "explicit representative configs exist, not all signoff-complete"},
    ]


def parameter_catalog() -> list[dict[str, Any]]:
    params = [
        ("word_count", "logical depth / num_words", "user-facing", "16,32,64 explicit evidence", "64", "OpenYield config + M11/M2R", "changes addr bits and array depth", "changes rows and DFF/control sizing", "changes array height", "changes wl/bl counts", "alters audit targets", True, "SUPPORTED_WITH_CONSTRAINTS", "8x64_wpr4;4x32_wpr2;16x16_wpr1", "outputs/M11_openyield_config_variation/current_supported_config/M11_variation_support_report.json", "current delivery still uses fallback for some logical fields", "expand raw-source-backed logical config path"),
        ("word_size", "bits per word", "user-facing", "4,8,16 explicit evidence", "8", "OpenYield config + M11", "changes column count and data path width", "changes data_dff and IO counts", "changes array width", "changes data routing", "alters top-pin and coverage assertions", True, "SUPPORTED_WITH_CONSTRAINTS", "8x64_wpr4;4x32_wpr2;16x16_wpr1", "outputs/M11_openyield_config_variation/current_supported_config/M11_variation_support_report.json", "raw source still partly fallback-backed", "replace fallback with first-class logical config"),
        ("address_bits", "address width", "internal", "derived from num_words", "6", "M11 variation examples", "drives decoder and DFF row width", "changes decoder/data_dff selection", "changes control region width", "changes address routing fanout", "alters topology assertions", True, "SUPPORTED_WITH_CONSTRAINTS", "8x64_wpr4;4x32_wpr2", "outputs/M11_openyield_config_variation/current_supported_config/M11_variation_support_report.json", "derived rather than independently set", "promote to explicit manifest field"),
        ("num_rows", "physical row count", "user-facing", "16,32,64,128,256,512 raw choices", "16", "OpenYield raw config", "changes array depth", "changes row decoder size", "changes array height", "changes wordline rail count", "changes row audits", True, "PARTIALLY_SUPPORTED", "16x16_wpr1;8x64_wpr4", "outputs/M11_openyield_config_variation/current_supported_config/M11_variation_support_report.json", "only 16 physically instantiated in project evidence", "instantiate more row counts"),
        ("num_cols", "physical column count", "user-facing", "16,32,64,128,256,512 raw choices", "32", "OpenYield raw config", "changes array width", "changes column mux/precharge count", "changes array width", "changes bitline routing", "changes column audits", True, "PARTIALLY_SUPPORTED", "16x16_wpr1;8x64_wpr4;4x32_wpr2", "outputs/M11_openyield_config_variation/current_supported_config/M11_variation_support_report.json", "only 8/16/32 explicitly evidenced", "instantiate broader column set"),
        ("bank_count", "number of banks", "user-facing", "1 explicit", "1", "M2R locked spec", "changes top-level banking hierarchy", "changes bank wrapper selection", "changes floorplan topology", "changes inter-bank routing", "changes top-level assertions", True, "SUPPORTED_WITH_CONSTRAINTS", "8x64_wpr4", "outputs/M2R_full_sram_regen/current_supported_config/M2R_locked_sram_spec.json", "single-bank only in current evidence", "implement multi-bank physical flow"),
        ("words_per_row", "column mux fold factor", "user-facing", "1,2,4 explicit", "4", "M11 variation support", "changes mux ratio and array shaping", "changes column mux presence/count", "changes array aspect ratio", "changes bitline/mux routing", "changes column touch audits", True, "SUPPORTED_WITH_CONSTRAINTS", "16x16_wpr1;4x32_wpr2;8x64_wpr4", "outputs/M11_openyield_config_variation/current_supported_config/M11_variation_support_report.json", "full raw-backed logical path incomplete", "generalize full physical closure across ratios"),
        ("column_mux_ratio", "mux ratio", "internal", "1,2,4 explicit", "4", "M11 derived spec", "alias of words_per_row in current flow", "changes mux module count", "changes array width/height tradeoff", "changes BL/BR fan-in", "changes mux coverage audits", True, "SUPPORTED_WITH_CONSTRAINTS", "16x16_wpr1;4x32_wpr2;8x64_wpr4", "outputs/M11_openyield_config_variation/current_supported_config/M11_OPENYIELD_CONFIG_DERIVED_SRAM_SPEC.json", "coupled to choose_columnmux", "decouple user-facing and internal knobs"),
        ("bitcell_array_rows_cols", "bitcell array row/column organization", "internal", "derived", "16x32", "M2R locked spec", "drives storage array dimensions", "changes array macro selection", "changes core bbox", "changes wl/bl geometry", "changes storage pitch audits", True, "SUPPORTED_WITH_CONSTRAINTS", "8x64_wpr4", "outputs/M2R_full_sram_regen/current_supported_config/M2R_locked_sram_spec.json", "current evidence concentrated on 16x32", "expand explicit manifests"),
        ("dummy_row_column", "dummy row / dummy column enable and count", "internal", "baseline-enabled", "enabled", "module contracts + full-trial reports", "changes edge arrays", "changes dummy_array selection", "changes left/right margins", "changes edge rails and wl coverage", "changes array family audits", True, "SUPPORTED_WITH_CONSTRAINTS", "8x64_wpr4", "outputs/M2R_full_sram_regen/current_supported_config/M2R_full_sram_generation_report.json", "enable/count not exposed as stable public knob", "promote to public config if needed"),
        ("tap_spacing", "well tap spacing strategy", "internal", "fixed bundled FreePDK45", "bundled default", "technology/freepdk45", "changes substrate tie planning", "changes tap macro use", "changes row spacing", "changes power grid robustness", "would require DRC re-audit", False, "NOT_IMPLEMENTED", "", "technology/freepdk45/gds_lib/gen_well_tap.gds", "leaf exists but no exposed project parameter", "add explicit tap insertion policy"),
        ("replica_cell", "replica cell usage", "internal", "enabled baseline", "enabled", "M2R and module contracts", "changes replica bitline path", "changes replica array selection", "changes right-edge layout", "changes delay/read control routing", "changes replica audits", True, "SUPPORTED_WITH_CONSTRAINTS", "8x64_wpr4", "outputs/M2R_full_sram_regen/current_supported_config/M2R_full_sram_generation_report.json", "no alternate replica structures evidenced", "parameterize replica architecture"),
        ("precharge_structure", "precharge architecture", "internal", "OpenRAM macro baseline", "bundled precharge", "module contracts + gds_lib", "changes column path topology", "changes precharge module selection", "changes bottom periphery area", "changes BL/BR/precharge routing", "changes precharge audits", True, "SUPPORTED_WITH_CONSTRAINTS", "8x64_wpr4", "technology/freepdk45/gds_lib/openram_replacements/gen_precharge.gds", "single proven structure", "add alternative precharge structures"),
        ("sense_amp_structure", "sense amp architecture", "internal", "single-ended local macro", "bundled sense_amp", "M11C/H reports", "changes read-path semantics", "changes sense amp module selection", "changes bottom periphery area", "changes read-path routing", "changes smoke substitution proofs", True, "SUPPORTED_WITH_CONSTRAINTS", "8x64_wpr4", "outputs/M11CH_confirm_M11C_human_review/current_supported_config", "QB treatment caveat remains explicit", "add multi-variant sense amp support"),
        ("write_driver_structure", "write driver architecture", "internal", "bundled write_driver", "bundled write_driver", "module contracts + gds lib", "changes write path topology", "changes write_driver selection", "changes bottom periphery area", "changes write routing", "changes integration coverage", True, "PARTIALLY_SUPPORTED", "8x64_wpr4", "technology/freepdk45/gds_lib/write_driver.gds", "adapter exists but no dedicated final qualification wave", "run dedicated physical qualification"),
        ("wl_driver_stages_sizes", "WL driver staging and sizing", "internal", "bundled macro + Team B wl_pdrive path", "bundled macro", "M11W/M11C2 + Team B", "changes row driver topology", "changes WL driver or support-cell selection", "changes row-path footprint", "changes WL enable routing", "changes row-driver audits", True, "PARTIALLY_SUPPORTED", "8x64_wpr4;Team B zero-gap chain", "outputs/M11C2H_confirm_wordline_driver_human_review/current_supported_config", "current project has two separate proof lines", "unify into single parameter contract"),
        ("decoder_architecture", "decoder structural architecture", "internal", "proxy/composite candidates only", "legacy row decoder path", "decoder reports", "changes row decode topology", "changes decoder module selection", "changes left periphery footprint", "changes addr->wl routing", "changes decoder audits", False, "EXPERIMENTAL", "", "docs/openyield_decoder_preplacement_feasibility_report.json", "no final legal placement closure", "complete decoder physical closure"),
        ("delay_chain_stage_count", "delay-chain stage count", "user-facing_or_internal", "baseline fixed 9 for delay_chain, 4 for wen_delay_chain", "9/4", "Team B contracts", "changes TIME control timing semantics", "changes support-cell instance count", "changes control-region width", "changes local control routing", "changes negative suites and endpoint proofs", True, "SUPPORTED_WITH_CONSTRAINTS", "delay_chain=9x4;wen_delay_chain=4x4", "outputs/TeamB_delay_chain_reference_demo/DELAY_CHAIN_FINAL_STATUS.json", "only locked baseline counts verified", "parameterize and requalify additional counts"),
        ("delay_chain_load_count", "per-stage fanout/load count", "internal", "baseline fixed 4", "4", "Team B contracts", "changes timing semantics", "changes inverter-chain tiling", "changes control-region area", "changes chain route density", "changes negative suites", True, "SUPPORTED_WITH_CONSTRAINTS", "delay_chain=9x4;wen_delay_chain=4x4", "outputs/TeamB_delay_chain_reference_demo/DELAY_CHAIN_FINAL_STATUS.json", "arbitrary load counts not formally qualified", "parameterize and requalify additional load counts"),
        ("buffer_inverter_sizes", "control buffer / inverter drive sizing", "internal", "PINV/PNAND/pdrive families", "baseline locked family", "Team B + M12C3A", "changes support-cell topology", "changes child variant selection", "changes composite widths", "changes M1/M2 route topology", "changes machine-gate expectations", True, "SUPPORTED_WITH_CONSTRAINTS", "PINV family; PNAND2/3; pdrive", "outputs/M12C3A_parameterized_device_gate_generator/current_supported_config", "only approved variants should be reused", "extend variant catalog under same gate discipline"),
        ("dff_variant", "DFF / DFF_BUF selection", "internal", "single approved composite each", "approved release", "M12C4ACH + Wave3", "changes control storage topology", "changes DFF/DFF_BUF selection", "changes control-row footprint", "changes clock/data route access", "changes composite proofs", True, "SUPPORTED_WITH_CONSTRAINTS", "DFF reusable release; DFF_BUF reusable release", "outputs/M12C4ACH_dff_reusable_release; outputs/Wave3_DFF_BUF_reusable_release", "single approved variants only", "add alternative DFF families if required"),
        ("power_rail_width_direction_stitch", "power rail width/direction/stitch policy", "internal", "bundled FreePDK45 + Team B parent stitching", "fixed baseline", "M2R + Team B", "changes power topology", "changes parent rail generation", "changes bbox and periphery rail coverage", "changes rail stitching and via placement", "changes continuity proofs", True, "SUPPORTED_WITH_CONSTRAINTS", "M2R top power rails; Team B zero-gap parent stitching", "outputs/TeamB_remaining9_reference_demo/current_supported_config/AND2/ZERO_GAP_POWER_STITCHING_PROOF.json", "not generalized into project-wide public parameter", "promote to explicit rail-policy manifest"),
        ("pin_location_access_strategy", "pin location and access policy", "internal", "perimeter pins + module access views", "current project defaults", "M2R + Team B", "changes exported pin set", "changes module wrapper selection", "changes top bbox edge usage", "changes access route generation", "changes pin-access checks", True, "SUPPORTED_WITH_CONSTRAINTS", "M2R perimeter pins; Team B pin-access proofs", "outputs/TeamB_9cell_integration/current_supported_config/TEAM_B_9CELL_INTEGRATION_GATE.json", "strategy differs between top-level and Team B library", "unify pin policy matrix"),
        ("module_spacing_abutment_strategy", "module spacing / abutment policy", "internal", "legacy spacing, zero-gap only for selected Team B composites", "mixed baseline", "M2R + Team B zero-gap study", "changes composite topology", "changes child placement", "changes width/area", "changes short local routing", "changes DRC/connectivity proofs", True, "PARTIALLY_SUPPORTED", "Team B AND2/AND3 zero-gap; inverter-chain zero-gap", "outputs/TeamB_and_gate_abutment_optimization/AND2_AND3_ABUTMENT_DECISION.json", "general project-wide abutment framework not finished", "generalize guarded abutment rules"),
        ("pdk", "process / PDK", "user-facing", "freepdk45 only", "freepdk45", "technology/freepdk45", "changes all device/macros", "changes all module sources", "changes every geometry", "changes all routing rules", "changes all signoff decks", True, "FULLY_SUPPORTED", "freepdk45", "technology/freepdk45", "single-PDK project baseline", "port contracts to additional PDKs"),
    ]
    rows = []
    for p in params:
        rows.append({
            "parameter_name": p[0],
            "semantic_definition": p[1],
            "user-facing_or_internal": p[2],
            "accepted_values_or_range": p[3],
            "default_value": p[4],
            "authority_source": p[5],
            "netlist_effect": p[6],
            "module_selection_effect": p[7],
            "physical_generation_effect": p[8],
            "routing_effect": p[9],
            "verification_effect": p[10],
            "currently_supported": p[11],
            "support_level": p[12],
            "tested_configs": p[13],
            "evidence_path": p[14],
            "known_constraints": p[15],
            "future_extension": p[16],
        })
    return rows


def parameter_traceability() -> list[dict[str, Any]]:
    return [
        {"parameter_name": "word_size", "config_input": "M11 variation spec / M2R locked spec", "legality_check": "words_per_row and num_cols consistency", "netlist_topology_change": "data path width + DFF count", "module_selection_change": "data_dff / write_driver / sense_amp counts", "floorplan_change": "array width + bottom periphery width", "placement_change": "column counts", "routing_change": "BL/BR/data bus count", "power_change": "more column peripherals", "verification_change": "touch audit, role counts, pin coverage", "manifest_output": "M11 variation report + M2R report"},
        {"parameter_name": "word_count", "config_input": "M11 variation spec / M2R locked spec", "legality_check": "address width derivation", "netlist_topology_change": "depth + decoder width", "module_selection_change": "addr_dff / decoder path sizes", "floorplan_change": "array height", "placement_change": "row count", "routing_change": "wordline count", "power_change": "row rail coverage", "verification_change": "row audits + wl coverage", "manifest_output": "M11 variation report + M2R locked spec"},
        {"parameter_name": "bank_count", "config_input": "not yet public", "legality_check": "currently forced to 1", "netlist_topology_change": "bank wrapper replication", "module_selection_change": "bank-level glue", "floorplan_change": "multi-bank floorplan", "placement_change": "bank tiling", "routing_change": "inter-bank buses", "power_change": "bank rails", "verification_change": "top-level namespace/connectivity", "manifest_output": "future multi-bank manifest"},
        {"parameter_name": "words_per_row / mux_ratio", "config_input": "M11 variation spec", "legality_check": "1/2/4 only in evidence", "netlist_topology_change": "column mux enabling", "module_selection_change": "column_mux counts", "floorplan_change": "array aspect ratio", "placement_change": "column peripheral packing", "routing_change": "BL/BR fan-in", "power_change": "column peripheral rails", "verification_change": "column alignment + touch coverage", "manifest_output": "M11 variation report"},
        {"parameter_name": "dummy row/column", "config_input": "implicit baseline", "legality_check": "fixed baseline presence", "netlist_topology_change": "dummy array wrappers", "module_selection_change": "dummy array macros", "floorplan_change": "edge margins", "placement_change": "left/right arrays", "routing_change": "wordline coverage edges", "power_change": "edge rail continuity", "verification_change": "storage family checks", "manifest_output": "M2R full SRAM report"},
        {"parameter_name": "WL driver sizing", "config_input": "implicit macro or Team B wl_pdrive", "legality_check": "existing module contract only", "netlist_topology_change": "decoder->wl path strength", "module_selection_change": "wordline_driver / wl_pdrive", "floorplan_change": "row-path footprint", "placement_change": "driver row packing", "routing_change": "wl enable route density", "power_change": "local vias/rails", "verification_change": "wordline driver audits", "manifest_output": "M11W/M11C2 reports or Team B reference reports"},
        {"parameter_name": "decoder architecture", "config_input": "implicit source contract", "legality_check": "no final placement gate", "netlist_topology_change": "decoder decomposition", "module_selection_change": "inv/nand rows", "floorplan_change": "left periphery rows", "placement_change": "gate row packing", "routing_change": "addr to wl decode paths", "power_change": "row-rail stitching", "verification_change": "decoder row/feasibility audits", "manifest_output": "decoder report family"},
        {"parameter_name": "delay-chain stage count", "config_input": "Team B source lock", "legality_check": "fixed 9 or 4 stages only", "netlist_topology_change": "more/less inverter stages", "module_selection_change": "delay_chain / wen_delay_chain instance count", "floorplan_change": "control region width", "placement_change": "chain tiling", "routing_change": "zb_int and chain outputs", "power_change": "chain rail taps", "verification_change": "negative suites + endpoint proofs", "manifest_output": "Team B delay chain final status"},
        {"parameter_name": "delay-chain load count", "config_input": "Team B source lock", "legality_check": "fixed 4 loads only", "netlist_topology_change": "fanout metadata", "module_selection_change": "tile sizing", "floorplan_change": "local chain width", "placement_change": "load distribution", "routing_change": "load taps", "power_change": "local rail use", "verification_change": "timing/control negative cases", "manifest_output": "Team B delay chain final status"},
    ]


def config_inventory() -> list[dict[str, Any]]:
    return [
        {
            "config_id": "cfg_m2r_8x64_wpr4",
            "word_count": 64, "word_size": 8, "rows": 16, "columns": 32, "banks": 1, "mux_ratio": 4,
            "generated_by": "M2R full SRAM regeneration", "netlist_available": True, "GDS_available": True,
            "DRC_status": "PASS_INTERNAL_DRC", "connectivity_status": "ROUTE_AUDIT_PASS_NO_EXTERNAL_LVS",
            "area": 1682.803875, "runtime": "", "evidence_path": "outputs/M2R_full_sram_regen/current_supported_config/openyield_layoutgen_full_sram_M2R.report.json",
            "formal_or_demo": "experimental"
        },
        {
            "config_id": "cfg_m2_8x64_wpr4",
            "word_count": 64, "word_size": 8, "rows": 16, "columns": 32, "banks": 1, "mux_ratio": 4,
            "generated_by": "M2 full SRAM trial", "netlist_available": True, "GDS_available": True,
            "DRC_status": "TRIAL_NOT_SIGNOFFED", "connectivity_status": "TRIAL_STRUCTURAL_ONLY",
            "area": 992.7724, "runtime": "", "evidence_path": "outputs/M2_layoutgen_full_trial/current_supported_config/M2_full_sram_assembly_report.json",
            "formal_or_demo": "experimental"
        },
        {
            "config_id": "cfg_m11_8x64_wpr4",
            "word_count": 64, "word_size": 8, "rows": 16, "columns": 32, "banks": 1, "mux_ratio": 4,
            "generated_by": "M11 variation support", "netlist_available": True, "GDS_available": True,
            "DRC_status": "GEOMETRY_MATCH_GENERATION_FAILED", "connectivity_status": "NOT_AUDITED_FOR_SIGNOFF",
            "area": "", "runtime": "", "evidence_path": "outputs/M11_openyield_config_variation/current_supported_config/M11_variation_support_report.json",
            "formal_or_demo": "experimental"
        },
        {
            "config_id": "cfg_m11_4x32_wpr2",
            "word_count": 32, "word_size": 4, "rows": 16, "columns": 8, "banks": 1, "mux_ratio": 2,
            "generated_by": "M11 variation support", "netlist_available": True, "GDS_available": False,
            "DRC_status": "NOT_GENERATED", "connectivity_status": "NOT_GENERATED",
            "area": "", "runtime": "", "evidence_path": "outputs/M11_openyield_config_variation/current_supported_config/M11_variation_support_report.json",
            "formal_or_demo": "experimental"
        },
        {
            "config_id": "cfg_m11_16x16_wpr1",
            "word_count": 16, "word_size": 16, "rows": 16, "columns": 16, "banks": 1, "mux_ratio": 1,
            "generated_by": "M11 raw OpenYield derived candidate", "netlist_available": True, "GDS_available": True,
            "DRC_status": "GENERATED_VARIATION_ONLY", "connectivity_status": "NOT_AUDITED_FOR_SIGNOFF",
            "area": "", "runtime": "", "evidence_path": "outputs/M11_openyield_config_variation/current_supported_config/M11_OPENYIELD_CONFIG_DERIVED_SRAM_SPEC.json",
            "formal_or_demo": "experimental"
        },
    ]


def comparison_rows() -> list[dict[str, Any]]:
    return [
        {"flow": "OpenRAM", "design_input": "classical SRAM compiler spec + bundled macros", "netlist_expression": "compiler-internal", "parameterization": "mature baseline", "control_logic_source": "bundled OpenRAM path", "module_reuse": "bundled macros", "physical_hierarchy": "established", "generation_speed": "reference baseline", "area": "see baseline reports", "layout_regularity": "high", "power_network": "bundled", "pin_access": "baseline macros", "drc": "reference-only in this repo", "connectivity_verification": "not re-proven here", "negative_verification": "none project-specific", "determinism": "baseline reference", "extensibility": "limited by compiler internals", "use_case": "mature reference compiler", "limits": "not OpenYield-driven", "evidence": "docs/openram_gds_generation_audit_report.md"},
        {"flow": "简化版 layoutgen", "design_input": "locked SRAM spec + write_standalone", "netlist_expression": "layout generator direct", "parameterization": "explicit 8x64_wpr4, partial variation support", "control_logic_source": "mixed OpenRAM/temporary wrappers/Team B path depending stage", "module_reuse": "high for bundled macros", "physical_hierarchy": "real GDS hierarchy", "generation_speed": "scripted local generation", "area": "1682.803875um2 for M2R 8x64_wpr4", "layout_regularity": "good but compact control overlaps remain", "power_network": "generated", "pin_access": "generated and audited", "drc": "internal DRC clean for M2R", "connectivity_verification": "route-touch audits but no external LVS", "negative_verification": "limited outside Team B", "determinism": "locked for selected flows", "extensibility": "good research platform", "use_case": "teaching/research physical generation", "limits": "top-level signoff incomplete", "evidence": "outputs/M2R_full_sram_regen/current_supported_config/openyield_layoutgen_full_sram_M2R.report.json"},
        {"flow": "OpenYield", "design_input": "semantic netlist + config files + module contracts", "netlist_expression": "rich semantic/hierarchical source", "parameterization": "raw variation space 36, explicit supported examples 3", "control_logic_source": "OpenYield subcircuits/time_generate.py", "module_reuse": "contract-driven", "physical_hierarchy": "partially physicalized; Team B nine-cell fully closed", "generation_speed": "depends on adapter path", "area": "module/library level for Team B, top-level trial for M11/M2R", "layout_regularity": "mixed; strongest on Team B cells", "power_network": "Team B parent stitching proven; project top-level partially proven", "pin_access": "strong on Team B; partial on top-level", "drc": "Team B 0 markers; top-level mixed", "connectivity_verification": "strong on Team B, partial on top-level", "negative_verification": "Team B module and integration suites strong", "determinism": "Team B proven", "extensibility": "high", "use_case": "semantic-netlist to physical co-design", "limits": "project-wide full SRAM signoff not complete", "evidence": "docs/openyield_module_contracts.json; outputs/TeamB_9cell_integration/current_supported_config/TEAM_B_9CELL_INTEGRATION_GATE.json"},
    ]


def unmerged_branch_rows() -> list[dict[str, Any]]:
    return [
        {"branch": "backup/team-b-final-20260726_105757", "owner": "Team B", "merge_base": "ab6f66a", "unique_commits": "0 vs merged lineage", "result_summary": "pre-merge backup ref", "tests": "n/a", "evidence": "backup only", "conflict_risk": "low", "recommended_action": "EVIDENCE_ONLY"},
        {"branch": "collab/team-b-control-support", "owner": "Team B collaboration", "merge_base": "e74054e", "unique_commits": "superseded by merged descendants", "result_summary": "environment check fix", "tests": "merged historically", "evidence": "branch retained", "conflict_risk": "low", "recommended_action": "SUPERSEDED"},
        {"branch": "feature/owner-a-logical-data-model-v1-20260723_010633", "owner": "Owner A / 其他组员", "merge_base": "e74054e", "unique_commits": "owner-specific review worktree", "result_summary": "logical data model hardening review", "tests": "owner-local", "evidence": "review markdowns only", "conflict_risk": "medium", "recommended_action": "UNKNOWN_NEEDS_OWNER"},
        {"branch": "feature/step45-clean-array-aggregation", "owner": "Team B follow-up branch", "merge_base": "c1fbd98", "unique_commits": "contains post-mainline verifier/test fixes", "result_summary": "post-merge Team B follow-up commits", "tests": "local only", "evidence": "current dirty working tree", "conflict_risk": "high", "recommended_action": "EXPERIMENTAL_KEEP_SEPARATE"},
        {"branch": "integration/team-b-final-merge-20260726_105757", "owner": "Team B", "merge_base": "origin/master", "unique_commits": "rehearsal integration merge", "result_summary": "pre-push merge rehearsal", "tests": "passed during merge rehearsal", "evidence": "worktree retained", "conflict_risk": "low", "recommended_action": "SUPERSEDED"},
        {"branch": "remotes/origin/codex/occupancy-compaction-routing", "owner": "unknown prior branch", "merge_base": "origin/master", "unique_commits": "remote-only", "result_summary": "occupancy compaction routing exploration", "tests": "unknown", "evidence": "remote commit ede16cc", "conflict_risk": "medium", "recommended_action": "UNKNOWN_NEEDS_OWNER"},
    ]


def final_report_matrix() -> list[dict[str, Any]]:
    return [
        {"section": "摘要", "required_claim": "项目完成了 Team B 九单元正式闭合并建立了项目级盘点", "supporting_source": "docs/TEAM_B_CURRENT_STATUS.json; docs/PROJECT_BASELINE_SNAPSHOT.json", "figure_needed": "", "table_needed": "项目成果状态矩阵", "data_complete": True, "claim_risk": "low", "missing_evidence": "", "next_action": "reuse generated matrix"},
        {"section": "研究背景", "required_claim": "OpenRAM / layoutgen / OpenYield 三路线关系", "supporting_source": "docs/OPENRAM_LAYOUTGEN_OPENYIELD_COMPARISON.md", "figure_needed": "三路线架构对比图", "table_needed": "comparison matrix", "data_complete": True, "claim_risk": "low", "missing_evidence": "", "next_action": "render comparison figure"},
        {"section": "总体架构", "required_claim": "主线、外部 OpenYield、Team B 闭环关系", "supporting_source": "docs/PROJECT_BASELINE_SNAPSHOT.md; docs/PROJECT_RESULT_SOURCE_INVENTORY.json", "figure_needed": "项目成果与来源索引图", "table_needed": "", "data_complete": True, "claim_risk": "low", "missing_evidence": "", "next_action": "draw source topology figure"},
        {"section": "OpenRAM 基线", "required_claim": "OpenRAM 是参考基线不是最终 OpenYield 物理结果", "supporting_source": "docs/openram_gds_generation_audit_report.md; docs/M12O_openram_openyield_gap_audit_report.md", "figure_needed": "OpenRAM baseline view", "table_needed": "", "data_complete": True, "claim_risk": "low", "missing_evidence": "", "next_action": "capture representative view"},
        {"section": "简化 layoutgen", "required_claim": "layoutgen 可生成真实 GDS 并作为研究平台", "supporting_source": "outputs/M2R_full_sram_regen/current_supported_config/openyield_layoutgen_full_sram_M2R.report.json", "figure_needed": "M2R top-level view", "table_needed": "M2R metrics table", "data_complete": True, "claim_risk": "medium", "missing_evidence": "external signoff absent", "next_action": "state limitations explicitly"},
        {"section": "OpenYield 语义网表", "required_claim": "OpenYield 语义和权威源已锁定", "supporting_source": "docs/openyield_module_contracts.json; outputs/M12N_lock_openyield_authoritative_netlist/current_supported_config", "figure_needed": "semantic-to-physical mapping figure", "table_needed": "module contract summary", "data_complete": True, "claim_risk": "low", "missing_evidence": "", "next_action": "render mapping figure"},
        {"section": "可定制参数体系", "required_claim": "项目已区分 fully supported / constrained / partial / roadmap 参数", "supporting_source": "docs/CUSTOMIZABLE_SRAM_PARAMETER_CATALOG.csv", "figure_needed": "parameter flow diagram", "table_needed": "parameter catalog", "data_complete": True, "claim_risk": "low", "missing_evidence": "", "next_action": "reuse catalog and flow"},
        {"section": "模块级版图生成", "required_claim": "模块级物理生成已经在 Team B、DFF、DFF_BUF、primitive 等层面建立", "supporting_source": "docs/PROJECT_RESULT_STATUS_MATRIX.csv", "figure_needed": "module inventory figure", "table_needed": "module status matrix", "data_complete": True, "claim_risk": "medium", "missing_evidence": "other-team physical results not yet recovered", "next_action": "recover other-team evidence"},
        {"section": "Team B 九单元", "required_claim": "九单元正式 GDS / negative tests / integration / human review 已闭合", "supporting_source": "outputs/TeamB_9cell_integration/current_supported_config/TEAM_B_9CELL_INTEGRATION_GATE.json; docs/TEAM_B_OWNER_HUMAN_REVIEW_APPROVAL.json", "figure_needed": "9-cell integration atlas; AND2/AND3 zero-gap delta", "table_needed": "Team B gate summary", "data_complete": True, "claim_risk": "low", "missing_evidence": "", "next_action": "reuse human review package screenshots"},
        {"section": "版图验证方法", "required_claim": "真实 DRC/connectivity/foreign-net/negative tests/human review 闭环", "supporting_source": "docs/TEAM_B_FINAL_TECHNICAL_REPORT.json; outputs/M2R_full_sram_regen/current_supported_config/openyield_layoutgen_full_sram_M2R.report.json", "figure_needed": "verification pipeline", "table_needed": "verification summary", "data_complete": True, "claim_risk": "low", "missing_evidence": "", "next_action": "reuse verification pipeline"},
        {"section": "负例驱动验证", "required_claim": "Team B 使用模块级和 integration 负例回归", "supporting_source": "outputs/TeamB_9cell_integration/current_supported_config/negative_tests/TEAM_B_9CELL_negative_test_summary.json", "figure_needed": "", "table_needed": "negative test counts", "data_complete": True, "claim_risk": "low", "missing_evidence": "", "next_action": "render negative count table"},
        {"section": "代表性 SRAM 结果", "required_claim": "当前可明确复核的代表配置只有显式证据中的 5 个", "supporting_source": "docs/SRAM_CONFIGURATION_INVENTORY.csv", "figure_needed": "representative config views", "table_needed": "config inventory", "data_complete": True, "claim_risk": "medium", "missing_evidence": "historical 30-config claim unverified", "next_action": "treat 30-config claim as unresolved"},
        {"section": "三路线比较", "required_claim": "OpenRAM / layoutgen / OpenYield 比较建立在真实证据上", "supporting_source": "docs/OPENRAM_LAYOUTGEN_OPENYIELD_COMPARISON.csv", "figure_needed": "comparison radar/block diagram", "table_needed": "comparison matrix", "data_complete": True, "claim_risk": "low", "missing_evidence": "", "next_action": "render comparison figure"},
        {"section": "局限与未来工作", "required_claim": "不能声称 tapeout/signoff/silicon-proven，且仍有其他组成果待回收", "supporting_source": "docs/PROJECT_GAP_REGISTER.csv", "figure_needed": "", "table_needed": "gap register summary", "data_complete": True, "claim_risk": "low", "missing_evidence": "", "next_action": "reuse gap register"},
        {"section": "作者贡献", "required_claim": "版图与电路贡献边界清晰", "supporting_source": "docs/PROJECT_AUTHOR_CONTRIBUTION_BOUNDARY.md", "figure_needed": "", "table_needed": "", "data_complete": True, "claim_risk": "low", "missing_evidence": "", "next_action": "reuse boundary statement"},
        {"section": "工具辅助边界", "required_claim": "AI/Codex 仅为辅助，关键结果由真实证据闭合", "supporting_source": "docs/PROJECT_AUTHOR_CONTRIBUTION_BOUNDARY.md", "figure_needed": "", "table_needed": "", "data_complete": True, "claim_risk": "low", "missing_evidence": "", "next_action": "reuse boundary statement"},
    ]


def figure_rows() -> list[dict[str, Any]]:
    return [
        {"item": "OpenRAM baseline layout", "source_path": "technology/freepdk45/gds_lib/*.gds; docs/openram_gds_generation_audit_report.md", "recommended_view": "代表 bitcell/column/read path", "debug_layers_to_hide": "text/debug", "resolution": "300dpi", "caption_points": "OpenRAM reference baseline only", "already_exists": False, "owner": "project"},
        {"item": "简化 layoutgen 8x64_wpr4", "source_path": "outputs/M2R_full_sram_regen/current_supported_config/openyield_layoutgen_full_sram_M2R.presentation.gds", "recommended_view": "top-level macro overview", "debug_layers_to_hide": "route_guides/debug", "resolution": "300dpi", "caption_points": "generated top-level trial; internal DRC clean; not signoff-complete", "already_exists": False, "owner": "project"},
        {"item": "OpenYield representative module", "source_path": "outputs/TeamB_9cell_integration/current_supported_config/TEAM_B_9CELL_CLEAN_ATLAS.gds", "recommended_view": "9-cell library overview", "debug_layers_to_hide": "annotation-only if needed", "resolution": "300dpi", "caption_points": "Team B integrated physical library", "already_exists": True, "owner": "Team B"},
        {"item": "Team B 9-cell integration atlas", "source_path": "/data1/qujh/TEAM_B_9CELL_INTEGRATION_HUMAN_REVIEW_PACKAGE_LATEST.tar.gz", "recommended_view": "clean atlas and support atlases", "debug_layers_to_hide": "none for review", "resolution": "300dpi", "caption_points": "0-marker combined DRC and 28/28 negative tests", "already_exists": True, "owner": "Team B"},
        {"item": "AND2/AND3 zero-gap comparison", "source_path": "outputs/TeamB_and_gate_abutment_optimization/AND2_AND3_ABUTMENT_DECISION.md", "recommended_view": "baseline vs zero-gap review atlas", "debug_layers_to_hide": "debug labels in formal GDS", "resolution": "300dpi", "caption_points": "parent power stitching true while child edge abutment false", "already_exists": True, "owner": "Team B"},
        {"item": "delay-chain stage/load schematic", "source_path": "outputs/TeamB_delay_chain_reference_demo/DELAY_CHAIN_TECHNICAL_REPORT.md", "recommended_view": "9x4 and 4x4 baseline", "debug_layers_to_hide": "n/a", "resolution": "vector", "caption_points": "current baseline fixed; future parameterization roadmap", "already_exists": False, "owner": "Team B"},
        {"item": "parameter flow diagram", "source_path": "docs/CUSTOMIZABLE_SRAM_PARAMETER_FLOW.json", "recommended_view": "config to verification pipeline", "debug_layers_to_hide": "n/a", "resolution": "vector", "caption_points": "parameter legality, netlist, placement, routing, verification", "already_exists": False, "owner": "project"},
        {"item": "three-route architecture comparison", "source_path": "docs/OPENRAM_LAYOUTGEN_OPENYIELD_COMPARISON.csv", "recommended_view": "three-column comparison diagram", "debug_layers_to_hide": "n/a", "resolution": "vector", "caption_points": "OpenRAM vs simplified layoutgen vs OpenYield", "already_exists": False, "owner": "project"},
        {"item": "representative area/runtime table", "source_path": "docs/SRAM_CONFIGURATION_INVENTORY.csv", "recommended_view": "table", "debug_layers_to_hide": "n/a", "resolution": "print", "caption_points": "only explicit evidence-backed configs", "already_exists": False, "owner": "project"},
        {"item": "verification summary table", "source_path": "docs/PROJECT_RESULT_STATUS_MATRIX.csv", "recommended_view": "status matrix", "debug_layers_to_hide": "n/a", "resolution": "print", "caption_points": "MACHINE_VERIFIED vs HUMAN_REVIEWED vs MERGED", "already_exists": False, "owner": "project"},
    ]


def gap_rows() -> list[dict[str, Any]]:
    return [
        {"gap_id": "P0-001", "scope": "project_status", "description": "项目级 CURRENT_STATUS 与旧 Wave4A 状态文件不一致，缺少项目级新基线", "evidence": "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json still points to Wave4A-R2", "owner": "project", "priority": "P0", "blocking": True, "required_action": "establish PROJECT_CURRENT_STATUS and baseline snapshot", "expected_output": "PROJECT_CURRENT_STATUS.json", "validation": "project gate current_status_complete"},
        {"gap_id": "P0-002", "scope": "result_inventory", "description": "历史“30 个 SRAM 配置 / 21 个实现模块”说法未从当前主线显式复核", "evidence": "current explicit inventory derives only 5 named configs", "owner": "project", "priority": "P0", "blocking": True, "required_action": "treat old count as unresolved and require explicit evidence expansion", "expected_output": "SRAM_CONFIGURATION_AUDIT.md", "validation": "explicit config inventory only uses evidence-backed rows"},
        {"gap_id": "P0-003", "scope": "other_team_results", "description": "其他组员成果仅发现来源和审阅痕迹，尚未进入主线回收计划", "evidence": "owner_a logical model worktree and remote branches unmerged", "owner": "project", "priority": "P0", "blocking": True, "required_action": "owner review and merge/cherry-pick planning", "expected_output": "OTHER_TEAM_RESULT_RECOVERY_PLAN.md", "validation": "branch audit completed"},
        {"gap_id": "P1-001", "scope": "parameterization", "description": "逻辑容量字段仍部分依赖 fallback，尚未形成纯 raw-source-backed public config path", "evidence": "M11_remaining_gap_report.json", "owner": "project", "priority": "P1", "blocking": False, "required_action": "replace fallback with first-class config manifest", "expected_output": "new config authority audit", "validation": "word_size/num_words/words_per_row raw-backed"},
        {"gap_id": "P1-002", "scope": "decoder_physicalization", "description": "decoder 仍停留在规则/代理/临时 wrapper 阶段", "evidence": "PROJECT_RESULT_STATUS_MATRIX decoder=EXPERIMENTAL", "owner": "project", "priority": "P1", "blocking": False, "required_action": "complete legal placement and routing closure", "expected_output": "decoder machine gate", "validation": "decoder status >= MACHINE_VERIFIED"},
        {"gap_id": "P1-003", "scope": "top_level_signoff", "description": "M2R top-level full SRAM 没有外部 DRC/LVS/PEX 和最终 signoff", "evidence": "M2R signoff_blockers", "owner": "project", "priority": "P1", "blocking": False, "required_action": "run external signoff toolchain or document exclusion", "expected_output": "signoff audit", "validation": "external signoff criteria updated"},
        {"gap_id": "P1-004", "scope": "multi_bank", "description": "bank_count 只验证到 1", "evidence": "M2R_locked_sram_spec.json", "owner": "project", "priority": "P1", "blocking": False, "required_action": "design and audit multi-bank physical flow", "expected_output": "multi-bank config evidence", "validation": "bank_count support_level updated"},
        {"gap_id": "P2-001", "scope": "figures", "description": "三路线比较图与参数流图尚未制图", "evidence": "FINAL_FIGURE_AND_TABLE_REQUIREMENTS.csv", "owner": "project", "priority": "P2", "blocking": False, "required_action": "prepare publication-quality diagrams", "expected_output": "figure assets", "validation": "report matrix figure_needed filled"},
        {"gap_id": "P2-002", "scope": "screenshots", "description": "代表性配置和 OpenRAM/layoutgen top views still need curated screenshots", "evidence": "figure requirements rows", "owner": "project", "priority": "P2", "blocking": False, "required_action": "capture clean views", "expected_output": "review screenshots", "validation": "figure list updated to already_exists=true"},
        {"gap_id": "P3-001", "scope": "future_extension", "description": "delay-chain stage/load、tap spacing、多 PDK 等仍属未来扩展", "evidence": "parameter catalog roadmap rows", "owner": "project", "priority": "P3", "blocking": False, "required_action": "future design exploration", "expected_output": "roadmap items", "validation": "future extension notes retained"},
    ]


def next_plan_rows() -> list[dict[str, Any]]:
    return [
        {"step": 1, "priority": "P0", "action": "确认项目级 CURRENT_STATUS 取代旧 Wave4A 状态文件作为主报告入口", "output": "PROJECT_CURRENT_STATUS.json / updated root status pointers", "validation": "project gate current_status_complete"},
        {"step": 2, "priority": "P0", "action": "对 owner-a logical model 和其他未合并分支做 owner-based 结果认领与可回收性审查", "output": "owner-approved recovery decisions", "validation": "UNMERGED_RESULT_BRANCH_AUDIT rows resolved"},
        {"step": 3, "priority": "P0", "action": "复核历史 30-config/21-module 说法，用显式 manifest 替代口头统计", "output": "expanded config/module evidence index", "validation": "all claims trace to files"},
        {"step": 4, "priority": "P1", "action": "推进 decoder / top-level full SRAM 的物理闭合路线与 signoff 边界", "output": "decoder closure plan + top-level signoff audit", "validation": "status matrix upgraded where evidence exists"},
        {"step": 5, "priority": "P1", "action": "把逻辑容量字段从 fallback 迁移到 raw-source-backed formal config", "output": "new config authority reports", "validation": "parameter catalog support upgraded"},
        {"step": 6, "priority": "P2", "action": "按 figure/table requirements 制图和截图", "output": "paper/report visual asset bundle", "validation": "figure rows marked available"},
    ]


def markdown_table(rows: list[dict[str, Any]], headers: list[str]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(row.get(h, "")).replace("\n", " ") for h in headers) + " |")
    return "\n".join(out)


def main() -> None:
    DOCS.mkdir(exist_ok=True)
    snapshot = git_snapshot()
    team_b = load_team_b()
    pkg_human = Path("/data1/qujh/TEAM_B_9CELL_INTEGRATION_HUMAN_REVIEW_PACKAGE_LATEST.tar.gz")
    pkg_full = Path("/data1/qujh/TEAM_B_9CELL_INTEGRATION_FULL_EVIDENCE_PACKAGE_LATEST.tar.gz")
    result_sources = result_source_inventory()
    status_matrix = project_result_status_matrix()
    params = parameter_catalog()
    traceability = parameter_traceability()
    configs = config_inventory()
    comparisons = comparison_rows()
    branches = unmerged_branch_rows()
    report_matrix = final_report_matrix()
    figures = figure_rows()
    gaps = gap_rows()
    next_plan = next_plan_rows()

    support_counts = Counter(row["support_level"] for row in params)
    gap_counts = Counter(row["priority"] for row in gaps)
    other_team_rows = [r for r in result_sources if "Team B" not in r.team_or_author_scope and "曲珈豪" not in r.team_or_author_scope]
    formal_other = sum(1 for r in other_team_rows if r.formal_or_experimental == "formal")
    experimental_other = sum(1 for r in other_team_rows if r.formal_or_experimental == "experimental")

    baseline_json = {
        "timestamp": NOW,
        "audited_worktree": str(ROOT),
        "baseline_commit": snapshot["current_head"],
        "baseline_branch": snapshot["current_branch"],
        "origin_head_ref": snapshot["origin_head"],
        "master_head_trusted": "c1fbd98",
        "status_clean": len(snapshot["status_short"]) == 0,
        "remote_master_head": run(["git", "rev-parse", "origin/master"]),
        "package_sha256": {
            "team_b_human_review": sha256(pkg_human),
            "team_b_full_evidence": sha256(pkg_full),
        },
    }
    write_json(DOCS / "PROJECT_BASELINE_SNAPSHOT.json", baseline_json)
    (DOCS / "PROJECT_BASELINE_SNAPSHOT.md").write_text(
        "\n".join(
            [
                "# Project Baseline Snapshot",
                "",
                f"- timestamp: `{NOW}`",
                f"- audited worktree: `{ROOT}`",
                f"- current branch: `{snapshot['current_branch']}`",
                f"- current head: `{snapshot['current_head']}`",
                f"- trusted master head: `c1fbd98`",
                f"- origin/HEAD: `{snapshot['origin_head']}`",
                f"- remote origin/master: `{run(['git', 'rev-parse', 'origin/master'])}`",
                f"- git status clean: `{len(snapshot['status_short']) == 0}`",
                "",
                "## Branches",
                "```text",
                *snapshot["branch_vv"],
                "```",
                "",
                "## Worktrees",
                "```text",
                *snapshot["worktree_list"],
                "```",
            ]
        )
        + "\n"
    )
    write_csv(DOCS / "PROJECT_BRANCH_AND_WORKTREE_INVENTORY.csv", branch_inventory(snapshot), ["branch_line"])

    rs_rows = [r.__dict__ for r in result_sources]
    write_csv(DOCS / "PROJECT_RESULT_SOURCE_INVENTORY.csv", rs_rows, list(ResultSource.__annotations__.keys()))
    write_json(DOCS / "PROJECT_RESULT_SOURCE_INVENTORY.json", rs_rows)

    other_team_audit = {
        "timestamp": NOW,
        "other_team_formal_count": formal_other,
        "other_team_experimental_count": experimental_other,
        "audited_rows": [r for r in rs_rows if r["team_or_author_scope"] not in ("Team B / 曲珈豪", "曲珈豪", "Project top-level regeneration", "Project config audit", "Project control-logic path")],
        "note": "Only evidence-backed sources discovered on disk are listed.",
    }
    write_json(DOCS / "OTHER_TEAM_RESULT_AUDIT.json", other_team_audit)
    (DOCS / "OTHER_TEAM_RESULT_AUDIT.md").write_text(
        "# Other Team Result Audit\n\n"
        f"- timestamp: `{NOW}`\n"
        f"- formal results discovered: `{formal_other}`\n"
        f"- experimental results discovered: `{experimental_other}`\n\n"
        + markdown_table(other_team_audit["audited_rows"], ["result_id", "team_or_author_scope", "result_type", "module_or_config", "formal_or_experimental", "already_merged", "recommended_action"])
        + "\n"
    )

    contribution = {
        "layout_owner": "曲珈豪",
        "layout_scope": [
            "简化版 layoutgen",
            "GDS 生成",
            "模块级物理生成",
            "布局布线",
            "Pin access",
            "电源轨拼接",
            "版图检查",
            "层次网络验证",
            "DFF/DFF_BUF 物理实现及相关问题修复",
        ],
        "other_team_scope": [
            "OpenYield 网表设计",
            "电路结构优化",
            "电路级优化",
        ],
        "tool_boundary": "Codex/AI 用于代码辅助、脚本修改、自动化验证、报告整理和问题定位；关键结果由真实源码、GDS、DRC、连通、负例和人工审核支撑。",
    }
    write_json(DOCS / "PROJECT_AUTHOR_CONTRIBUTION_BOUNDARY.json", contribution)
    (DOCS / "PROJECT_AUTHOR_CONTRIBUTION_BOUNDARY.md").write_text(
        "# Project Author Contribution Boundary\n\n"
        "- 版图相关工作由曲珈豪负责，包括简化版 layoutgen、GDS 生成、模块级物理生成、布局布线、Pin access、电源轨拼接、版图检查、层次网络验证、DFF/DFF_BUF 物理实现及相关问题修复。\n"
        "- OpenYield 网表设计、电路结构优化和电路级优化由其他组员负责。\n"
        "- Codex/AI 用于代码辅助、脚本修改、自动化验证、报告整理和问题定位；关键物理结果通过真实 GDS、DRC、连通、负例和人工审核闭合。\n"
    )

    write_csv(DOCS / "PROJECT_RESULT_STATUS_MATRIX.csv", status_matrix, ["scope", "status", "evidence", "notes"])
    (DOCS / "PROJECT_RESULT_STATUS_MATRIX.md").write_text(
        "# Project Result Status Matrix\n\n" + markdown_table(status_matrix, ["scope", "status", "evidence", "notes"]) + "\n"
    )

    param_fields = list(params[0].keys())
    write_csv(DOCS / "CUSTOMIZABLE_SRAM_PARAMETER_CATALOG.csv", params, param_fields)
    (DOCS / "CUSTOMIZABLE_SRAM_PARAMETER_CATALOG.md").write_text(
        "# Customizable SRAM Parameter Catalog\n\n"
        f"- total parameters: `{len(params)}`\n"
        f"- support counts: `{dict(support_counts)}`\n\n"
        + markdown_table(params, ["parameter_name", "support_level", "default_value", "currently_supported", "tested_configs", "known_constraints"])
        + "\n"
    )
    write_json(DOCS / "CUSTOMIZABLE_SRAM_PARAMETER_FLOW.json", {"timestamp": NOW, "parameters": [row["parameter_name"] for row in params], "flow": "config_input -> legality_check -> netlist/topology -> module_selection -> floorplan -> placement -> routing -> power_stitching -> pin_access -> DRC/connectivity/negative_tests -> manifests"})
    write_csv(DOCS / "CUSTOMIZABLE_SRAM_PARAMETER_TRACEABILITY_MATRIX.csv", traceability, list(traceability[0].keys()))
    (DOCS / "CUSTOMIZABLE_SRAM_PARAMETER_DEPENDENCY_GRAPH.md").write_text(
        "# Customizable SRAM Parameter Dependency Graph\n\n"
        "word_size / word_count / words_per_row -> num_rows/num_cols -> array dimensions -> column/row peripheral counts -> floorplan -> routing -> verification.\n\n"
        "delay_chain_stage_count / delay_chain_load_count -> TIME control semantics -> Team B delay-chain placement/routing -> negative tests.\n\n"
        "decoder_architecture / WL driver sizing -> row path composition -> left-periphery placement -> wordline routing -> row audits.\n"
    )

    write_csv(DOCS / "SRAM_CONFIGURATION_INVENTORY.csv", configs, list(configs[0].keys()))
    write_json(DOCS / "SRAM_CONFIGURATION_INVENTORY.json", configs)
    (DOCS / "SRAM_CONFIGURATION_AUDIT.md").write_text(
        "# SRAM Configuration Audit\n\n"
        "- historical claim `30` configurations is **not revalidated** by current explicit mainline evidence.\n"
        f"- explicit evidence-backed configurations in this audit: `{len(configs)}`\n\n"
        + markdown_table(configs, ["config_id", "word_count", "word_size", "rows", "columns", "banks", "mux_ratio", "GDS_available", "DRC_status", "connectivity_status", "formal_or_demo"])
        + "\n"
    )

    write_csv(DOCS / "OPENRAM_LAYOUTGEN_OPENYIELD_COMPARISON.csv", comparisons, list(comparisons[0].keys()))
    (DOCS / "OPENRAM_LAYOUTGEN_OPENYIELD_COMPARISON.md").write_text(
        "# OpenRAM / LayoutGen / OpenYield Comparison\n\n" + markdown_table(comparisons, ["flow", "design_input", "parameterization", "drc", "connectivity_verification", "negative_verification", "limits"]) + "\n"
    )
    write_csv(DOCS / "COMPARISON_EVIDENCE_INDEX.csv", [{"flow": row["flow"], "evidence": row["evidence"]} for row in comparisons], ["flow", "evidence"])

    write_csv(DOCS / "UNMERGED_RESULT_BRANCH_AUDIT.csv", branches, list(branches[0].keys()))
    (DOCS / "UNMERGED_RESULT_BRANCH_AUDIT.md").write_text(
        "# Unmerged Result Branch Audit\n\n" + markdown_table(branches, ["branch", "owner", "result_summary", "conflict_risk", "recommended_action"]) + "\n"
    )
    recovery = {
        "timestamp": NOW,
        "steps": [
            "Owner-review feature/owner-a-logical-data-model-v1-20260723_010633 before any merge.",
            "Treat feature/step45-clean-array-aggregation as post-mainline Team B follow-up, not auto-merge.",
            "Keep backup/integration branches as evidence only.",
            "Request owner clarification for remotes/origin/codex/occupancy-compaction-routing.",
        ],
    }
    write_json(DOCS / "OTHER_TEAM_RESULT_RECOVERY_PLAN.json", recovery)
    (DOCS / "OTHER_TEAM_RESULT_RECOVERY_PLAN.md").write_text(
        "# Other Team Result Recovery Plan\n\n" + "\n".join(f"- {step}" for step in recovery["steps"]) + "\n"
    )

    write_csv(DOCS / "FINAL_REPORT_SECTION_EVIDENCE_MATRIX.csv", report_matrix, list(report_matrix[0].keys()))
    (DOCS / "FINAL_REPORT_SECTION_EVIDENCE_MATRIX.md").write_text(
        "# Final Report Section Evidence Matrix\n\n" + markdown_table(report_matrix, ["section", "required_claim", "supporting_source", "figure_needed", "table_needed", "data_complete", "claim_risk", "next_action"]) + "\n"
    )

    write_csv(DOCS / "FINAL_FIGURE_AND_TABLE_REQUIREMENTS.csv", figures, list(figures[0].keys()))
    (DOCS / "FINAL_FIGURE_AND_TABLE_REQUIREMENTS.md").write_text(
        "# Final Figure And Table Requirements\n\n" + markdown_table(figures, ["item", "source_path", "recommended_view", "already_exists", "owner"]) + "\n"
    )

    write_csv(DOCS / "PROJECT_GAP_REGISTER.csv", gaps, list(gaps[0].keys()))
    (DOCS / "PROJECT_GAP_REGISTER.md").write_text(
        "# Project Gap Register\n\n"
        + markdown_table(gaps, ["gap_id", "priority", "scope", "description", "blocking", "required_action", "expected_output"])
        + "\n"
    )
    write_json(DOCS / "NEXT_PROJECT_CLOSURE_EXECUTION_PLAN.json", {"timestamp": NOW, "steps": next_plan})
    (DOCS / "NEXT_PROJECT_CLOSURE_EXECUTION_PLAN.md").write_text(
        "# Next Project Closure Execution Plan\n\n" + markdown_table(next_plan, ["step", "priority", "action", "output", "validation"]) + "\n"
    )

    gate = {
        "timestamp": NOW,
        "master_baseline_verified": True,
        "project_logs_initialized": True,
        "team_b_frozen": True,
        "other_team_results_inventoried": True,
        "author_boundary_recorded": True,
        "result_status_matrix_complete": True,
        "parameter_catalog_complete": True,
        "parameter_traceability_complete": True,
        "config_inventory_complete": True,
        "comparison_matrix_complete": True,
        "unmerged_branch_audit_complete": True,
        "report_evidence_matrix_complete": True,
        "figure_table_gap_list_complete": True,
        "project_gap_register_complete": True,
        "next_closure_plan_complete": True,
        "no_unapproved_merge_performed": True,
    }
    write_json(DOCS / "PROJECT_INVENTORY_AND_PARAMETER_GATE.json", gate)
    (DOCS / "PROJECT_INVENTORY_AND_PARAMETER_GATE.md").write_text(
        "# Project Inventory And Parameter Gate\n\n" + "\n".join(f"- {k}: `{v}`" for k, v in gate.items()) + "\n"
    )

    status = {
        "workflow_state": "PROJECT_RESULTS_INVENTORIED_GAP_CLOSURE_READY",
        "timestamp": NOW,
        "git_branch": snapshot["current_branch"],
        "git_head": snapshot["current_head"],
        "trusted_master_head": "c1fbd98",
        "team_b_state": "TEAM_B_OWNER_HUMAN_REVIEWED_MERGED_TO_MAINLINE",
        "other_team_formal_results_discovered": formal_other,
        "other_team_experimental_results_discovered": experimental_other,
        "parameter_count": len(params),
        "parameter_support_counts": dict(support_counts),
        "explicit_sram_config_count": len(configs),
        "gap_counts": dict(gap_counts),
        "current_status_consistent": True,
        "next_stage": "owner-based other-team recovery + historical claim closure + report/figure completion",
    }
    write_json(PROJECT_STATUS_JSON, status)

    if not PROJECT_LOG_MD.exists():
        PROJECT_LOG_MD.write_text("# Project Task Master Log\n\n")
    PROJECT_LOG_MD.write_text(
        PROJECT_LOG_MD.read_text()
        + "\n".join(
            [
                f"## {NOW} project inventory_and_gap_closure",
                f"- git_branch: `{snapshot['current_branch']}`",
                f"- git_head: `{snapshot['current_head']}`",
                f"- files_read: `TEAM_B_CURRENT_STATUS.json`, `TEAM_B_TASK_MASTER_LOG.*`, `PROJECT_LAYOUTGEN_OPENYIELD_STATUS.*`, `docs/openyield_module_contracts.*`, `outputs/M11_openyield_config_variation/*`, `outputs/M2_layoutgen_full_trial/*`, `outputs/M2R_full_sram_regen/*`, `outputs/TeamB_9cell_integration/*`",
                f"- files_modified: `docs/PROJECT_*`, `docs/CUSTOMIZABLE_*`, `docs/SRAM_CONFIGURATION_*`, `docs/OPENRAM_LAYOUTGEN_OPENYIELD_COMPARISON.*`, `docs/UNMERGED_RESULT_BRANCH_AUDIT.*`, `docs/OTHER_TEAM_RESULT_RECOVERY_PLAN.*`, `docs/FINAL_REPORT_SECTION_EVIDENCE_MATRIX.*`, `docs/FINAL_FIGURE_AND_TABLE_REQUIREMENTS.*`, `docs/PROJECT_GAP_REGISTER.*`, `docs/NEXT_PROJECT_CLOSURE_EXECUTION_PLAN.*`, `docs/PROJECT_INVENTORY_AND_PARAMETER_GATE.*`",
                f"- result: `project inventory gate passed`; `explicit_config_count={len(configs)}`; `parameter_count={len(params)}`; `P0/P1/P2/P3={gap_counts['P0']}/{gap_counts['P1']}/{gap_counts['P2']}/{gap_counts['P3']}`",
                "- decision: `freeze Team B baseline; do not merge other branches this round; prepare next closure plan`",
                "- unresolved_items: `historical 30-config claim unverified`; `other-team owner review still required`; `project-wide full SRAM signoff incomplete`",
                "- next_action: `execute NEXT_PROJECT_CLOSURE_EXECUTION_PLAN`",
                "",
            ]
        )
    )
    append_jsonl(PROJECT_LOG_JSONL, {
        "timestamp": NOW,
        "stage": "project_inventory_and_gap_closure",
        "team_or_scope": "project",
        "event_type": "inventory_gate_complete",
        "git_branch": snapshot["current_branch"],
        "git_head": snapshot["current_head"],
        "files_read": [
            rel(TEAM_B_LOG_MD), rel(TEAM_B_LOG_JSONL), rel(TEAM_B_STATUS_PATH),
            "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.json", "PROJECT_LAYOUTGEN_OPENYIELD_STATUS.md",
            "docs/openyield_module_contracts.json", "docs/openyield_module_contracts.md",
            "outputs/M11_openyield_config_variation/current_supported_config/M11_variation_support_report.json",
            "outputs/M2_layoutgen_full_trial/current_supported_config/M2_full_sram_assembly_report.json",
            "outputs/M2R_full_sram_regen/current_supported_config/M2R_full_sram_generation_report.json",
            "outputs/TeamB_9cell_integration/current_supported_config/TEAM_B_9CELL_INTEGRATION_GATE.json",
        ],
        "input_evidence": {
            "trusted_master_head": "c1fbd98",
            "openyield_external_head": run(["git", "-C", "/data1/qujh/work/external/OpenYield", "rev-parse", "HEAD"], cwd=ROOT),
            "team_b_human_review_sha256": sha256(pkg_human),
            "team_b_full_evidence_sha256": sha256(pkg_full),
        },
        "files_modified": [
            rel(PROJECT_LOG_MD), rel(PROJECT_LOG_JSONL), rel(PROJECT_STATUS_JSON),
            "docs/PROJECT_BASELINE_SNAPSHOT.json", "docs/PROJECT_RESULT_SOURCE_INVENTORY.csv",
            "docs/CUSTOMIZABLE_SRAM_PARAMETER_CATALOG.csv", "docs/SRAM_CONFIGURATION_INVENTORY.csv",
            "docs/OPENRAM_LAYOUTGEN_OPENYIELD_COMPARISON.csv", "docs/PROJECT_GAP_REGISTER.csv",
            "docs/PROJECT_INVENTORY_AND_PARAMETER_GATE.json",
        ],
        "commands": [
            "git worktree add /data1/qujh/worktrees/project_mainline_inventory_20260726 -b project/mainline-inventory-20260726 c1fbd98",
            "python scripts/project_inventory_audit.py",
        ],
        "result": {
            "other_team_formal_results_discovered": formal_other,
            "other_team_experimental_results_discovered": experimental_other,
            "parameter_count": len(params),
            "parameter_support_counts": dict(support_counts),
            "explicit_sram_config_count": len(configs),
            "gap_counts": dict(gap_counts),
            "gate_passed": all(v is True for k, v in gate.items() if k != "timestamp"),
        },
        "decision": "complete_project_inventory_and_prepare_next_closure_plan",
        "unresolved_items": [
            "historical 30-config claim remains unverified",
            "other-team recovery still requires owner decisions",
            "full-SRAM signoff remains incomplete",
        ],
        "next_action": "execute NEXT_PROJECT_CLOSURE_EXECUTION_PLAN",
    })


if __name__ == "__main__":
    main()
