from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any


NEXT_STAGE_ALLOWED = "M11V_ROUTING_POWER_CONNECTIVITY_VERIFICATION_DEEPENING"
SUBSTITUTED_MODULES = ["wordline_driver"]


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8", newline="\n")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _render_md(title: str, lines: list[str]) -> str:
    return "\n".join([f"# {title}", "", *lines, ""]).rstrip() + "\n"


def _replace_section(text: str, heading: str, body_lines: list[str]) -> str:
    block = "\n".join([heading, "", *body_lines]).rstrip() + "\n"
    marker = f"\n{heading}\n"
    if text.startswith(f"{heading}\n"):
        start = 0
    else:
        start = text.find(marker)
        if start >= 0:
            start += 1
    if start < 0:
        return text.rstrip() + "\n\n" + block
    next_heading = text.find("\n## ", start + len(heading) + 1)
    if next_heading < 0:
        return text[:start].rstrip() + "\n\n" + block
    return text[:start].rstrip() + "\n\n" + block + "\n" + text[next_heading + 1 :].lstrip("\n")


def _update_status_md() -> str:
    return (
        "# OpenYield SRAM LayoutGen Project Status\n\n"
        "## 1. Current Correct Goal\n\n"
        "M11C2H 已完成对 M11C2 `wordline_driver-only` smoke substitution 的人工收口确认。当前只允许 claim `wordline_driver-only smoke substitution attempted/pass`，"
        "但必须保留 routing/power cleanliness caveat；不扩大到任何其他模块，也不声称 full OpenYield module GDS hardmacro substitution、routing clean、power clean、DRC clean、LVS clean 或 signoff-ready。\n\n"
        "## 2. Current Stage\n\n"
        "- current_stage: `M11C2H`\n"
        f"- next_stage: `{NEXT_STAGE_ALLOWED}`\n"
        "- human_klayout_review_required_every_stage: `True`\n"
        "- can_enter_next_stage_without_human_review: `True`\n"
        f"- next_stage_allowed: `{NEXT_STAGE_ALLOWED}`\n\n"
        "## 3. M11C2H Human Review Closure\n\n"
        "- m11c2_human_review_completed: `True`\n"
        "- m11c2_wordline_driver_visual_review_passed: `True`\n"
        "- m11c2_wordline_driver_annotation_readable: `True`\n"
        "- m11c2_wordline_driver_nearby_power_routing_review_status: `INCONCLUSIVE_BASELINE_ROUTING_LIMITED`\n"
        "- m11c2_no_obvious_new_break_reported_by_human: `True`\n"
        "- m11c2_nearby_power_routing_visually_confirmed_clean: `False`\n"
        "- substituted_modules: `wordline_driver`\n"
        "- excluded_modules_confirmed: `True`\n"
        "- remaining_M11C2_blockers_before_count: `3`\n"
        "- remaining_M11C2_blockers_after_count: `0`\n"
        "- can_claim_wordline_driver_smoke_substitution_attempted: `True`\n"
        "- can_claim_wordline_driver_smoke_substitution_passed: `True`\n"
        "- can_claim_openyield_module_gds_hardmacro_substitution: `False`\n"
        "- can_claim_routing_clean: `False`\n"
        "- can_claim_power_clean: `False`\n"
        "- can_claim_drc_clean: `False`\n"
        "- can_claim_lvs_clean: `False`\n"
        "- can_claim_signoff_ready: `False`\n"
    )


def _update_progress_md(progress_text: str) -> str:
    updated = progress_text
    updated = updated.replace(
        "- next_assets_to_fill_in_order: `M11C2H_CONFIRM_M11C2_HUMAN_REVIEW, M12A_VARIATION_GDS_GENERATION, M12B_ROUTING_POWER_ADAPTATION, M13_DRC_LVS_FEASIBILITY_AND_EQUIVALENCE_TRACE`",
        f"- next_assets_to_fill_in_order: `{NEXT_STAGE_ALLOWED}, M12A_VARIATION_GDS_GENERATION, M12B_ROUTING_POWER_ADAPTATION, M13_DRC_LVS_FEASIBILITY_AND_EQUIVALENCE_TRACE`",
    )
    updated = _replace_section(
        updated,
        "## Claim Boundary",
        [
            "- can_claim_source_backed_translator_v2: `True`",
            "- can_claim_config_aware_translator_v3: `True`",
            "- can_claim_full_raw_openyield_netlist_compiler: `False`",
            "- can_claim_drc_clean: `False`",
            "- can_claim_lvs_clean: `False`",
            "- can_claim_signoff_ready: `False`",
            "- can_claim_openyield_module_gds_hardmacro_substitution: `False`",
            "- can_claim_sense_amp_smoke_substitution_attempted: `True`",
            "- can_claim_sense_amp_smoke_substitution_passed: `True`",
            "- can_claim_wordline_driver_smoke_substitution_attempted: `True`",
            "- can_claim_wordline_driver_smoke_substitution_passed: `True`",
            "- can_claim_routing_clean: `False`",
            "- can_claim_power_clean: `False`",
        ],
    )
    updated = _replace_section(
        updated,
        "## M11C2 Wordline Driver Smoke Substitution",
        [
            "- substitution_scope: `wordline_driver`",
            "- excluded_modules_confirmed: `sense_amp, column_mux, write_driver, CONTROL_LOGIC, precharge, bitcell_array, dummy_array, replica_array`",
            "- human_klayout_review_required: `False`",
            "- can_enter_next_stage_before_human_review: `True`",
            f"- next_stage_allowed: `{NEXT_STAGE_ALLOWED}`",
            "- note: `M11C2 passes human review with a routing/power caveat. The isolated smoke substitution is accepted, but nearby routing/power cleanliness remains inconclusive because the baseline layoutgen routing itself may already be limited.`",
        ],
    )
    m11c2h_lines = [
        "- m11c2_human_review_completed: `True`",
        "- m11c2_wordline_driver_visual_review_passed: `True`",
        "- m11c2_wordline_driver_annotation_readable: `True`",
        "- m11c2_wordline_driver_nearby_power_routing_review_status: `INCONCLUSIVE_BASELINE_ROUTING_LIMITED`",
        "- m11c2_no_obvious_new_break_reported_by_human: `True`",
        "- m11c2_nearby_power_routing_visually_confirmed_clean: `False`",
        "- remaining_M11C2_blockers_before_count: `3`",
        "- remaining_M11C2_blockers_after_count: `0`",
        f"- recommended_next_stage: `{NEXT_STAGE_ALLOWED}`",
        "- recommended_next_stage_reason: `Because M11C2 passed isolated wordline_driver smoke substitution, but nearby routing/power cleanliness remains visually inconclusive due to baseline layoutgen routing limitations. Verification should be deepened before expanding substitution scope.`",
        f"- next_stage_allowed: `{NEXT_STAGE_ALLOWED}`",
        "- can_enter_M11V_after_this_gate: `True`",
        "- note: `M11C2H only clears the M11C2 human-review gate with a routing/power caveat. It does not replace new modules and does not reopen routing/power/DRC/LVS/signoff claims.`",
    ]
    if "## M11C2H Human Review Closure" in updated:
        updated = _replace_section(updated, "## M11C2H Human Review Closure", m11c2h_lines)
    else:
        updated = updated.rstrip() + "\n\n" + "\n".join(["## M11C2H Human Review Closure", "", *m11c2h_lines]) + "\n"
    return updated if updated.endswith("\n") else updated + "\n"


def run_m11c2h_confirm_wordline_driver_human_review(
    *,
    repo_root: Path,
    status_md: Path,
    status_json: Path,
    progress_md: Path,
    m11c2_report: Path,
    m11c2_manifest: Path,
    m11c2_smoke_check: Path,
    m11c2_diff: Path,
    m11c2_proof: Path,
    out_dir: Path,
    out_json: Path,
    out_report: Path,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    status_md_text = status_md.read_text(encoding="utf-8")
    status = _read_json(status_json)
    progress_text = progress_md.read_text(encoding="utf-8")
    m11c2 = _read_json(m11c2_report)
    manifest_rows = _read_csv(m11c2_manifest)
    smoke_rows = _read_csv(m11c2_smoke_check)
    diff_rows = _read_csv(m11c2_diff)
    proof_rows = _read_csv(m11c2_proof)

    if "wordline_driver-only" not in status_md_text:
        raise ValueError("Status markdown no longer reflects the locked M11C2 wordline_driver-only scope.")
    if m11c2["substituted_modules"] != SUBSTITUTED_MODULES:
        raise ValueError("M11C2 report does not match the required substituted module set.")
    if not m11c2["excluded_modules_confirmed"]:
        raise ValueError("M11C2 excluded module lock must remain true.")
    if int(m11c2["remaining_M11C2_blockers_count"]) != 3:
        raise ValueError("M11C2 human review closure expects exactly 3 pre-review blockers.")
    if m11c2["real_substitution_proof_status"] != "PASS_WRAPPER_DGS_GEOMETRY_MATCH":
        raise ValueError("M11C2H requires a passing real substitution proof.")
    if len(manifest_rows) < 4 or len(smoke_rows) < 5 or len(diff_rows) < 4 or len(proof_rows) < 5:
        raise ValueError("M11C2 evidence inputs are incomplete.")

    human_review_items_before = list(m11c2["human_review_required_items"])
    human_review_items_after: list[str] = []
    recommended_next_stage_reason = (
        "Because M11C2 passed isolated wordline_driver smoke substitution, but nearby routing/power cleanliness remains visually inconclusive due to baseline layoutgen routing limitations. Verification should be deepened before expanding substitution scope."
    )

    report = {
        "status_file_read": True,
        "status_file_updated": True,
        "progress_file_updated": True,
        "m11c2_report_loaded": True,
        "m11c2_human_review_completed": True,
        "human_review_items_before": human_review_items_before,
        "human_review_items_after": human_review_items_after,
        "wordline_driver_visual_review_passed": True,
        "wordline_driver_annotation_readable": True,
        "wordline_driver_nearby_power_routing_review_status": "INCONCLUSIVE_BASELINE_ROUTING_LIMITED",
        "wordline_driver_nearby_power_routing_visually_confirmed_clean": False,
        "no_obvious_new_break_reported_by_human": True,
        "routing_clean_cannot_be_claimed": True,
        "power_clean_cannot_be_claimed": True,
        "wordline_driver_smoke_substitution_attempted": True,
        "wordline_driver_smoke_substitution_passed": True,
        "wordline_driver_smoke_substitution_human_review_accepted_with_caveat": True,
        "substituted_modules": SUBSTITUTED_MODULES,
        "excluded_modules_confirmed": True,
        "can_claim_wordline_driver_smoke_substitution_attempted": True,
        "can_claim_wordline_driver_smoke_substitution_passed": True,
        "can_claim_openyield_module_gds_hardmacro_substitution": False,
        "can_claim_routing_clean": False,
        "can_claim_power_clean": False,
        "can_claim_drc_clean": False,
        "can_claim_lvs_clean": False,
        "can_claim_signoff_ready": False,
        "remaining_M11C2_blockers_before_count": 3,
        "remaining_M11C2_blockers_after_count": 0,
        "recommended_next_stage": NEXT_STAGE_ALLOWED,
        "recommended_next_stage_reason": recommended_next_stage_reason,
        "next_stage_allowed": NEXT_STAGE_ALLOWED,
        "can_enter_M11V_after_this_gate": True,
        "human_review_source": "M11C2H gate closure records the provided human review result for the existing M11C2 clean-review and annotated-debug GDS artifacts, with routing/power caveat preserved.",
        "reviewed_gds_paths": [
            m11c2["clean_review_gds_path"],
            m11c2["annotated_debug_gds_path"],
        ],
        "m11c2_manifest_artifact_count": len(manifest_rows),
        "m11c2_smoke_check_item_count": len(smoke_rows),
        "m11c2_diff_item_count": len(diff_rows),
        "m11c2_proof_item_count": len(proof_rows),
    }

    routing_power_caveat = [
        {
            "review_item": "nearby_power_routing_human_status",
            "status": "INCONCLUSIVE_BASELINE_ROUTING_LIMITED",
            "reason": "原始 layoutgen baseline 本身可能已有走线/布局问题，人工无法可靠区分是否由本次 wordline_driver 替换引入。",
            "no_obvious_new_break_reported_by_human": True,
            "nearby_power_routing_visually_confirmed_clean": False,
            "routing_clean_cannot_be_claimed": True,
            "power_clean_cannot_be_claimed": True,
        }
    ]

    gate = {
        "stage": "M11C2H",
        "gate_name": "Confirm M11C2 human review and clear wordline_driver smoke substitution gate with routing/power caveat",
        "m11c2_human_review_completed": True,
        "wordline_driver_smoke_substitution_human_review_accepted_with_caveat": True,
        "substituted_modules": SUBSTITUTED_MODULES,
        "excluded_modules_confirmed": True,
        "remaining_M11C2_blockers_before_count": 3,
        "remaining_M11C2_blockers_after_count": 0,
        "recommended_next_stage": NEXT_STAGE_ALLOWED,
        "recommended_next_stage_reason": recommended_next_stage_reason,
        "next_stage_allowed": NEXT_STAGE_ALLOWED,
        "can_enter_M11V_after_this_gate": True,
        "can_claim_openyield_module_gds_hardmacro_substitution": False,
        "can_claim_routing_clean": False,
        "can_claim_power_clean": False,
        "can_claim_drc_clean": False,
        "can_claim_lvs_clean": False,
        "can_claim_signoff_ready": False,
    }

    machine_vs_human_summary = _render_md(
        "M11C2H Machine Vs Human Verification Summary",
        [
            f"- machine_verified_items_from_M11C2: `{m11c2['machine_verified_item_count']}`",
            f"- human_review_items_from_M11C2: `{m11c2['human_review_required_item_count']}`",
            "- machine_scope: `GDS parse sanity, top bbox exact-match, excluded-module lock, gen_wl_driver instance count, wrapper fingerprint proof, manifest/diff/smoke matrices.`",
            "- human_scope: `wordline_driver top-context visual completeness, readability of substituted debug labels, and nearby power/routing visual status.`",
            "- human_review_outcome: `Visual completeness and annotation readability pass; nearby routing/power cleanliness remains inconclusive because the baseline layoutgen routing itself may already be limited.`",
            "- claim_boundary_after_M11C2H: `Only wordline_driver-only smoke substitution attempted/pass may be claimed; routing clean, power clean, full hardmacro substitution, DRC, LVS, and signoff claims remain closed.`",
        ],
    )

    report_md_lines = [
        "- status_file_read: `True`",
        "- status_file_updated: `True`",
        "- progress_file_updated: `True`",
        "- m11c2_report_loaded: `True`",
        "- m11c2_human_review_completed: `True`",
        "- wordline_driver_visual_review_passed: `True`",
        "- wordline_driver_annotation_readable: `True`",
        "- wordline_driver_nearby_power_routing_review_status: `INCONCLUSIVE_BASELINE_ROUTING_LIMITED`",
        "- wordline_driver_nearby_power_routing_visually_confirmed_clean: `False`",
        "- no_obvious_new_break_reported_by_human: `True`",
        "- routing_clean_cannot_be_claimed: `True`",
        "- power_clean_cannot_be_claimed: `True`",
        "- wordline_driver_smoke_substitution_human_review_accepted_with_caveat: `True`",
        "- substituted_modules: `wordline_driver`",
        "- excluded_modules_confirmed: `True`",
        "- remaining_M11C2_blockers_before_count: `3`",
        "- remaining_M11C2_blockers_after_count: `0`",
        f"- recommended_next_stage: `{NEXT_STAGE_ALLOWED}`",
        f"- next_stage_allowed: `{NEXT_STAGE_ALLOWED}`",
        "- can_enter_M11V_after_this_gate: `True`",
        "- can_claim_routing_clean: `False`",
        "- can_claim_power_clean: `False`",
    ]

    _write_json(out_dir / "M11C2H_confirm_wordline_driver_human_review_report.json", report)
    _write_text(
        out_dir / "M11C2H_confirm_wordline_driver_human_review_report.md",
        _render_md("M11C2H Confirm Wordline Driver Human Review Report", report_md_lines),
    )
    _write_json(out_dir / "M11C2H_routing_power_caveat.json", routing_power_caveat)
    _write_text(
        out_dir / "M11C2H_routing_power_caveat.md",
        _render_md(
            "M11C2H Routing Power Caveat",
            [
                "- nearby_power_routing_human_status: `INCONCLUSIVE_BASELINE_ROUTING_LIMITED`",
                "- reason: `原始 layoutgen baseline 本身可能已有走线/布局问题，人工无法可靠区分是否由本次 wordline_driver 替换引入。`",
                "- no_obvious_new_break_reported_by_human: `True`",
                "- nearby_power_routing_visually_confirmed_clean: `False`",
                "- routing_clean_cannot_be_claimed: `True`",
                "- power_clean_cannot_be_claimed: `True`",
            ],
        ),
    )
    _write_json(out_dir / "M11C2H_M11V_entry_gate.json", gate)
    _write_text(
        out_dir / "M11C2H_M11V_entry_gate.md",
        _render_md(
            "M11C2H M11V Entry Gate",
            [
                "- m11c2_human_review_completed: `True`",
                "- wordline_driver_smoke_substitution_human_review_accepted_with_caveat: `True`",
                "- substituted_modules: `wordline_driver`",
                "- excluded_modules_confirmed: `True`",
                "- remaining_M11C2_blockers_before_count: `3`",
                "- remaining_M11C2_blockers_after_count: `0`",
                f"- recommended_next_stage: `{NEXT_STAGE_ALLOWED}`",
                f"- next_stage_allowed: `{NEXT_STAGE_ALLOWED}`",
                "- can_enter_M11V_after_this_gate: `True`",
            ],
        ),
    )
    _write_text(out_dir / "M11C2H_machine_vs_human_verification_summary.md", machine_vs_human_summary)

    _write_json(out_json, report)
    _write_text(out_report, _render_md("M11C2H Confirm Wordline Driver Human Review Report", report_md_lines))
    _write_text(
        repo_root / "docs/evidence/M11C2H_confirm_wordline_driver_human_review_summary.md",
        _render_md(
            "M11C2H Confirm Wordline Driver Human Review Summary",
            [
                "- wordline_driver_visual_review_passed: `True`",
                "- wordline_driver_annotation_readable: `True`",
                "- wordline_driver_nearby_power_routing_review_status: `INCONCLUSIVE_BASELINE_ROUTING_LIMITED`",
                "- no_obvious_new_break_reported_by_human: `True`",
                "- routing_clean_cannot_be_claimed: `True`",
                "- power_clean_cannot_be_claimed: `True`",
                f"- next_stage_allowed: `{NEXT_STAGE_ALLOWED}`",
            ],
        ),
    )

    _write_csv(repo_root / "docs/mapping/M11C2H_M11V_entry_gate.csv", list(gate.keys()), [gate])
    _write_csv(repo_root / "docs/mapping/M11C2H_routing_power_caveat.csv", list(routing_power_caveat[0].keys()), routing_power_caveat)

    status["current_stage"] = "M11C2H"
    status["next_stage"] = NEXT_STAGE_ALLOWED
    status["next_stage_allowed"] = NEXT_STAGE_ALLOWED
    status["can_enter_next_stage_without_human_review"] = True
    status["human_klayout_review_required"] = False
    status["can_enter_next_stage_before_human_review"] = True
    status["m11c2_human_review_completed"] = True
    status["m11c2_wordline_driver_visual_review_passed"] = True
    status["m11c2_wordline_driver_annotation_readable"] = True
    status["m11c2_wordline_driver_nearby_power_routing_review_status"] = "INCONCLUSIVE_BASELINE_ROUTING_LIMITED"
    status["m11c2_no_obvious_new_break_reported_by_human"] = True
    status["m11c2_nearby_power_routing_visually_confirmed_clean"] = False
    status["remaining_M11C2_blockers_before_count"] = 3
    status["remaining_M11C2_blockers_after_count"] = 0
    status["can_claim_wordline_driver_smoke_substitution_attempted"] = True
    status["can_claim_wordline_driver_smoke_substitution_passed"] = True
    status["can_claim_openyield_module_gds_hardmacro_substitution"] = False
    status["can_claim_routing_clean"] = False
    status["can_claim_power_clean"] = False
    status["can_claim_drc_clean"] = False
    status["can_claim_lvs_clean"] = False
    status["can_claim_signoff_ready"] = False
    status["recommended_next_stage"] = NEXT_STAGE_ALLOWED
    status["recommended_next_stage_reason"] = recommended_next_stage_reason
    status["can_enter_M11V_after_this_gate"] = True
    status["current_goal"] = "M11C2H completed the human-review closure for the isolated wordline_driver-only smoke substitution and accepted it with a routing/power caveat. The next stage is verification deepening before any scope expansion."
    status["last_M11C2H_report"] = report

    for asset in status.get("ten_required_assets_for_netlist_to_layout", []):
        if asset["asset_id"] == "PHYSICAL_IMPLEMENTATION_LIBRARY":
            asset["evidence_paths"] = [
                "docs/mapping/M11C2_wordline_driver_substitution_manifest.csv",
                "docs/mapping/M11C2_wordline_driver_smoke_check_matrix.csv",
                "docs/mapping/M11C2_wordline_driver_diff_matrix.csv",
                "docs/mapping/M11C2_real_substitution_proof.csv",
                "docs/mapping/M11C2H_M11V_entry_gate.csv",
            ]
            asset["next_action"] = NEXT_STAGE_ALLOWED
        elif asset["asset_id"] == "PIN_BBOX_RAIL_METADATA":
            asset["evidence_paths"] = [
                "docs/mapping/M11W_wordline_driver_repaired_metadata.csv",
                "docs/mapping/M11C2_wordline_driver_smoke_check_matrix.csv",
                "docs/mapping/M11C2H_routing_power_caveat.csv",
            ]
            asset["next_action"] = NEXT_STAGE_ALLOWED
        elif asset["asset_id"] == "VERIFICATION_AND_TRACE":
            asset["evidence_paths"] = [
                "docs/M11C2H_confirm_wordline_driver_human_review_report.json",
                "docs/evidence/M11C2H_confirm_wordline_driver_human_review_summary.md",
                "docs/mapping/M11C2H_M11V_entry_gate.csv",
                "outputs/M11C2H_confirm_wordline_driver_human_review/current_supported_config/M11C2H_machine_vs_human_verification_summary.md",
            ]
            asset["next_action"] = NEXT_STAGE_ALLOWED

    _write_json(status_json, status)
    _write_text(status_md, _update_status_md())
    _write_text(progress_md, _update_progress_md(progress_text))
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Confirm the M11C2 wordline_driver smoke substitution human review with routing/power caveat.")
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--status-md", required=True)
    parser.add_argument("--status-json", required=True)
    parser.add_argument("--progress-md", required=True)
    parser.add_argument("--m11c2-report", required=True)
    parser.add_argument("--m11c2-manifest", required=True)
    parser.add_argument("--m11c2-smoke-check", required=True)
    parser.add_argument("--m11c2-diff", required=True)
    parser.add_argument("--m11c2-proof", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-report", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    report = run_m11c2h_confirm_wordline_driver_human_review(
        repo_root=repo_root,
        status_md=(repo_root / args.status_md).resolve(),
        status_json=(repo_root / args.status_json).resolve(),
        progress_md=(repo_root / args.progress_md).resolve(),
        m11c2_report=(repo_root / args.m11c2_report).resolve(),
        m11c2_manifest=(repo_root / args.m11c2_manifest).resolve(),
        m11c2_smoke_check=(repo_root / args.m11c2_smoke_check).resolve(),
        m11c2_diff=(repo_root / args.m11c2_diff).resolve(),
        m11c2_proof=(repo_root / args.m11c2_proof).resolve(),
        out_dir=(repo_root / args.out_dir).resolve(),
        out_json=(repo_root / args.out_json).resolve(),
        out_report=(repo_root / args.out_report).resolve(),
    )
    for key in [
        "m11c2_human_review_completed",
        "wordline_driver_nearby_power_routing_review_status",
        "wordline_driver_smoke_substitution_human_review_accepted_with_caveat",
        "next_stage_allowed",
    ]:
        print(f"{key}={report[key]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
