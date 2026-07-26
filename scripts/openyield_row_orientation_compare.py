from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent


PITCH_X = 0.895
PITCH_Y = 1.565
DEFAULT_OUT_JSON = Path("docs/openyield_row_orientation_compare_report.json")
DEFAULT_OUT_MD = Path("docs/openyield_row_orientation_compare_report.md")
DEFAULT_POLICY_OUT_JSON = Path("docs/openyield_array_aggregation_row_policy_report.json")
DEFAULT_POLICY_OUT_MD = Path("docs/openyield_array_aggregation_row_policy_report.md")
DRC_DECK = Path("technology/freepdk45/tech/freepdk45.lydrc")


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare all-R0 versus alternating-MX storage-only row orientation policies.")
    parser.add_argument("--rows", type=int, default=2)
    parser.add_argument("--cols", type=int, default=4)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--policy-out-json", type=Path, default=DEFAULT_POLICY_OUT_JSON)
    parser.add_argument("--policy-out-md", type=Path, default=DEFAULT_POLICY_OUT_MD)
    args = parser.parse_args()

    out_json = resolve(args.out_json)
    out_md = resolve(args.out_md)
    policy_out_json = resolve(args.policy_out_json)
    policy_out_md = resolve(args.policy_out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    policy_out_json.parent.mkdir(parents=True, exist_ok=True)
    policy_out_md.parent.mkdir(parents=True, exist_ok=True)

    baseline = run_case("all_r0", args.rows, args.cols)
    candidate = run_case("alternating_mx", args.rows, args.cols)
    report = build_compare_report(args.rows, args.cols, baseline, candidate)
    policy_report = build_policy_report(report)

    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(format_markdown(report), encoding="utf-8")
    policy_out_json.write_text(json.dumps(policy_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    policy_out_md.write_text(format_policy_markdown(policy_report), encoding="utf-8")

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(f"Wrote {policy_out_json}")
    print(f"Wrote {policy_out_md}")
    print(
        f"all_r0_markers={baseline['drc']['violation_count']} "
        f"alternating_mx_markers={candidate['drc']['violation_count']} "
        f"recommend={report['decision']['recommend_storage_row_policy']}"
    )
    return 0


def run_case(policy: str, rows: int, cols: int) -> dict[str, Any]:
    case_dir = case_build_dir(policy, rows, cols)
    case_dir.mkdir(parents=True, exist_ok=True)
    smoke_json = case_dir / "storage_only_report.json"
    smoke_md = case_dir / "storage_only_report.md"
    gds_path = case_dir / f"storage_only_{rows}x{cols}_{policy}.gds"
    svg_path = gds_path.with_suffix(".svg")
    drc_json = case_dir / "storage_only_drc_report.json"
    drc_md = case_dir / "storage_only_drc_report.md"
    lyrdb_path = case_dir / "storage_only_drc.lyrdb"
    log_path = case_dir / "storage_only_drc.log"
    classify_json = case_dir / "storage_only_marker_classification.json"
    classify_md = case_dir / "storage_only_marker_classification.md"

    run_python(
        [
            "scripts/openyield_storage_only_gds_smoke.py",
            "--rows",
            str(rows),
            "--cols",
            str(cols),
            "--out-gds",
            str(relative_to_root(gds_path)),
            "--out-json",
            str(relative_to_root(smoke_json)),
            "--out-md",
            str(relative_to_root(smoke_md)),
            "--stitch-power-rails",
            "--row-orientation-policy",
            policy,
        ]
    )
    run_python(
        [
            "scripts/openyield_storage_only_drc_smoke.py",
            "--input-gds",
            str(relative_to_root(gds_path)),
            "--power-report",
            str(relative_to_root(smoke_json)),
            "--drc-deck",
            str(relative_to_root(resolve(DRC_DECK))),
            "--lyrdb",
            str(relative_to_root(lyrdb_path)),
            "--log",
            str(relative_to_root(log_path)),
            "--out-json",
            str(relative_to_root(drc_json)),
            "--out-md",
            str(relative_to_root(drc_md)),
        ]
    )
    run_python(
        [
            "scripts/openyield_drc_marker_classify.py",
            "--gds",
            str(relative_to_root(gds_path)),
            "--lyrdb",
            str(relative_to_root(lyrdb_path)),
            "--power-report",
            str(relative_to_root(smoke_json)),
            "--out-json",
            str(relative_to_root(classify_json)),
            "--out-md",
            str(relative_to_root(classify_md)),
        ]
    )

    smoke = load_json(smoke_json)
    drc = load_json(drc_json)
    classification = load_json(classify_json)
    return {
        "policy": policy,
        "case_dir": str(case_dir),
        "gds": smoke["gds_output"],
        "svg": smoke["svg_output"],
        "smoke": smoke,
        "drc": drc["drc"],
        "drc_findings": drc["findings"],
        "classification": classification,
        "summary": summarize_case(smoke, drc, classification),
    }


def summarize_case(smoke: dict[str, Any], drc: dict[str, Any], classification: dict[str, Any]) -> dict[str, Any]:
    rule_stats = classification.get("summary", {}).get("rule_type_stats", {})
    location_stats = classification.get("summary", {}).get("location_class_stats", {})
    seam_markers = [
        marker
        for marker in classification.get("markers", [])
        if marker.get("rule_name") == "METAL2.2" and marker.get("near_row_boundary")
    ]
    power_stitch_markers = int(drc.get("power_stitch_analysis", {}).get("power_stitch_related_violation_count", 0))
    return {
        "rows": smoke["rows"],
        "cols": smoke["cols"],
        "pitch_x": smoke["pitch"]["x"],
        "pitch_y": smoke["pitch"]["y"],
        "orientation": smoke["orientation"],
        "row_orientation_policy": smoke["row_orientation_policy"],
        "instance_total": smoke["instance_count"]["total"],
        "gds_path": smoke["gds_output"]["path"],
        "svg_path": smoke["svg_output"]["path"],
        "cross_row_power_short_risk": bool(smoke.get("cross_row_power_short_risk", False)),
        "total_markers": int(drc["drc"]["violation_count"] or 0),
        "metal1_2_count": int(rule_stats.get("METAL1.2", 0)),
        "metal2_2_count": int(rule_stats.get("METAL2.2", 0)),
        "row_boundary_metal2_count": len(seam_markers),
        "power_stitch_related_marker_count": int(power_stitch_markers),
        "location_class_stats": location_stats,
    }


def build_compare_report(rows: int, cols: int, baseline: dict[str, Any], candidate: dict[str, Any]) -> dict[str, Any]:
    before = baseline["summary"]
    after = candidate["summary"]
    seam_delta = after["row_boundary_metal2_count"] - before["row_boundary_metal2_count"]
    total_delta = after["total_markers"] - before["total_markers"]
    metal1_delta = after["metal1_2_count"] - before["metal1_2_count"]
    metal2_delta = after["metal2_2_count"] - before["metal2_2_count"]
    recommend_mx = (
        after["row_boundary_metal2_count"] < before["row_boundary_metal2_count"]
        and not after["cross_row_power_short_risk"]
        and after["power_stitch_related_marker_count"] <= before["power_stitch_related_marker_count"]
        and after["metal1_2_count"] <= before["metal1_2_count"] + 2
        and after["metal2_2_count"] <= before["metal2_2_count"]
        and after["total_markers"] <= before["total_markers"]
    )
    recommendation = "alternating_mx" if recommend_mx else "all_r0_with_row_gap_or_context"

    return {
        "scope": "storage_only_row_orientation_compare_smoke_not_main_flow",
        "rows": rows,
        "cols": cols,
        "pitch": {"x": PITCH_X, "y": PITCH_Y},
        "constraints": {
            "storage_only": True,
            "same_horizontal_power_stitch": True,
            "side_power_trunk": False,
            "routing_changed": False,
            "main_gds_flow_changed": False,
            "shared_rail_merge_changed": False,
            "peripheral_macros_included": False,
        },
        "all_r0": before,
        "alternating_mx": after,
        "compare": {
            "delta_total_markers": total_delta,
            "delta_metal1_2": metal1_delta,
            "delta_metal2_2": metal2_delta,
            "delta_row_boundary_metal2": seam_delta,
            "delta_power_stitch_related_markers": after["power_stitch_related_marker_count"] - before["power_stitch_related_marker_count"],
            "seam_marker_reduction": before["row_boundary_metal2_count"] - after["row_boundary_metal2_count"],
            "all_r0_cross_row_power_short_risk": before["cross_row_power_short_risk"],
            "alternating_mx_cross_row_power_short_risk": after["cross_row_power_short_risk"],
        },
        "decision": {
            "recommend_storage_row_policy": recommendation,
            "recommend_modify_array_aggregation_py": recommend_mx,
            "recommend_modify_standalone_py": False,
            "storage_aggregation_can_continue": recommend_mx,
            "reason": decision_reason(before, after, recommendation),
        },
        "next_step_recommendations": next_steps(recommendation),
    }


def build_policy_report(compare_report: dict[str, Any]) -> dict[str, Any]:
    decision = compare_report["decision"]
    all_r0 = compare_report["all_r0"]
    alt = compare_report["alternating_mx"]
    return {
        "scope": "array_aggregation_row_orientation_policy_integration",
        "supported_row_orientation_policies": ["all_r0", "alternating_mx"],
        "default_row_orientation_policy": "all_r0",
        "alternating_mx_supported_in_array_aggregation": True,
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "power_stitch_policy_modified": False,
        "array_aggregation_source_used_by_smoke": True,
        "all_r0_vs_alternating_mx": {
            "all_r0_total_markers": all_r0["total_markers"],
            "alternating_mx_total_markers": alt["total_markers"],
            "all_r0_metal2_2": all_r0["metal2_2_count"],
            "alternating_mx_metal2_2": alt["metal2_2_count"],
            "all_r0_row_boundary_metal2": all_r0["row_boundary_metal2_count"],
            "alternating_mx_row_boundary_metal2": alt["row_boundary_metal2_count"],
            "all_r0_cross_row_power_short_risk": all_r0["cross_row_power_short_risk"],
            "alternating_mx_cross_row_power_short_risk": alt["cross_row_power_short_risk"],
            "all_r0_power_stitch_related_markers": all_r0["power_stitch_related_marker_count"],
            "alternating_mx_power_stitch_related_markers": alt["power_stitch_related_marker_count"],
        },
        "metal2_seam_marker_cleared_with_alternating_mx": alt["row_boundary_metal2_count"] == 0,
        "power_stitch_still_safe_relative_to_baseline": alt["power_stitch_related_marker_count"] <= all_r0["power_stitch_related_marker_count"],
        "recommend_storage_row_policy": decision["recommend_storage_row_policy"],
        "recommend_future_standalone_integration": decision["recommend_storage_row_policy"] == "alternating_mx",
        "next_step_recommendations": [
            "Keep standalone.py unchanged in this step.",
            "If promoted later, wire alternating_mx into standalone storage placement behind an explicit opt-in flag only.",
            "Re-run the same storage-only compare smoke after any future adapter-to-standalone integration.",
        ],
    }


def decision_reason(before: dict[str, Any], after: dict[str, Any], recommendation: str) -> list[str]:
    reasons = [
        f"METAL2.2 seam markers: {before['row_boundary_metal2_count']} -> {after['row_boundary_metal2_count']}",
        f"total DRC markers: {before['total_markers']} -> {after['total_markers']}",
        f"cross-row power short risk: {before['cross_row_power_short_risk']} -> {after['cross_row_power_short_risk']}",
        f"power-stitch-related markers: {before['power_stitch_related_marker_count']} -> {after['power_stitch_related_marker_count']}",
    ]
    if recommendation == "alternating_mx":
        reasons.append("Alternating MX reduced row-seam METAL2 pressure without introducing a new power-stitch hazard in this smoke.")
    else:
        reasons.append("Alternating MX did not reduce seam markers enough, or it introduced a new short-risk / marker-risk signal in this smoke.")
    return reasons


def next_steps(recommendation: str) -> list[str]:
    if recommendation == "alternating_mx":
        return [
            "Keep this as a storage-only policy result first; do not wire it into standalone until a follow-up storage-array-only integration step is approved.",
            "If adopted later, update array aggregation placement only; do not change routing, GDS writer, or peripheral placement in the same step.",
            "Re-run the stitched storage-only DRC smoke after any future integration change to confirm the seam result holds.",
        ]
    return [
        "Keep main-flow storage aggregation unchanged for now.",
        "If seam markers remain high, study row-gap or missing-context options before touching array_aggregation.py.",
        "Do not modify standalone.py from this compare smoke alone.",
    ]


def format_markdown(report: dict[str, Any]) -> str:
    all_r0 = report["all_r0"]
    alt = report["alternating_mx"]
    compare = report["compare"]
    decision = report["decision"]
    lines = [
        "# OpenYield Row Orientation Compare Report",
        "",
        "This is a storage-only compare smoke. It does not modify the main standalone flow, routing, shared-rail behavior, or peripheral placement.",
        "",
        "## Summary",
        "",
        f"- rows / cols: `{report['rows']} x {report['cols']}`",
        f"- pitch: `{report['pitch']['x']} x {report['pitch']['y']}`",
        f"- all_r0 GDS: `{all_r0['gds_path']}`",
        f"- alternating_mx GDS: `{alt['gds_path']}`",
        f"- all_r0 total markers: `{all_r0['total_markers']}`",
        f"- alternating_mx total markers: `{alt['total_markers']}`",
        f"- all_r0 METAL1.2: `{all_r0['metal1_2_count']}`",
        f"- alternating_mx METAL1.2: `{alt['metal1_2_count']}`",
        f"- all_r0 METAL2.2: `{all_r0['metal2_2_count']}`",
        f"- alternating_mx METAL2.2: `{alt['metal2_2_count']}`",
        f"- row-boundary METAL2 markers: `{all_r0['row_boundary_metal2_count']} -> {alt['row_boundary_metal2_count']}`",
        f"- power stitch related markers: `{all_r0['power_stitch_related_marker_count']} -> {alt['power_stitch_related_marker_count']}`",
        f"- cross-row power short risk: `{all_r0['cross_row_power_short_risk']} -> {alt['cross_row_power_short_risk']}`",
        f"- recommend storage row policy: `{decision['recommend_storage_row_policy']}`",
        f"- recommend modify array_aggregation.py: `{decision['recommend_modify_array_aggregation_py']}`",
        f"- recommend modify standalone.py: `{decision['recommend_modify_standalone_py']}`",
        f"- storage aggregation can continue: `{decision['storage_aggregation_can_continue']}`",
        "",
        "## Compare Table",
        "",
        table(
            ["metric", "all_r0", "alternating_mx", "delta"],
            [
                ["total_markers", all_r0["total_markers"], alt["total_markers"], compare["delta_total_markers"]],
                ["METAL1.2", all_r0["metal1_2_count"], alt["metal1_2_count"], compare["delta_metal1_2"]],
                ["METAL2.2", all_r0["metal2_2_count"], alt["metal2_2_count"], compare["delta_metal2_2"]],
                [
                    "row_boundary_METAL2",
                    all_r0["row_boundary_metal2_count"],
                    alt["row_boundary_metal2_count"],
                    compare["delta_row_boundary_metal2"],
                ],
                [
                    "power_stitch_related",
                    all_r0["power_stitch_related_marker_count"],
                    alt["power_stitch_related_marker_count"],
                    compare["delta_power_stitch_related_markers"],
                ],
                ["cross_row_power_short_risk", all_r0["cross_row_power_short_risk"], alt["cross_row_power_short_risk"], "n/a"],
            ],
        ),
        "",
        "## Decision Notes",
        "",
        *[f"- {item}" for item in decision["reason"]],
        "",
        "## Next Steps",
        "",
        *[f"- {item}" for item in report["next_step_recommendations"]],
        "",
    ]
    return "\n".join(lines)


def format_policy_markdown(report: dict[str, Any]) -> str:
    comp = report["all_r0_vs_alternating_mx"]
    lines = [
        "# OpenYield Array Aggregation Row Policy Report",
        "",
        "This report records row-orientation-policy support added to `array_aggregation.py`. It does not modify standalone.py, routing, or the main GDS writer.",
        "",
        "## Summary",
        "",
        f"- supported row orientation policies: `{report['supported_row_orientation_policies']}`",
        f"- default row orientation policy: `{report['default_row_orientation_policy']}`",
        f"- alternating_mx supported in array_aggregation: `{report['alternating_mx_supported_in_array_aggregation']}`",
        f"- standalone.py modified: `{report['standalone_modified']}`",
        f"- routing modified: `{report['routing_modified']}`",
        f"- GDS writer modified: `{report['gds_writer_modified']}`",
        f"- power stitch policy modified: `{report['power_stitch_policy_modified']}`",
        f"- smoke uses array_aggregation source: `{report['array_aggregation_source_used_by_smoke']}`",
        f"- METAL2 seam marker cleared with alternating_mx: `{report['metal2_seam_marker_cleared_with_alternating_mx']}`",
        f"- power stitch still safe relative to baseline: `{report['power_stitch_still_safe_relative_to_baseline']}`",
        f"- recommend storage row policy: `{report['recommend_storage_row_policy']}`",
        f"- recommend future standalone integration: `{report['recommend_future_standalone_integration']}`",
        "",
        "## DRC Compare",
        "",
        table(
            ["metric", "all_r0", "alternating_mx"],
            [
                ["total_markers", comp["all_r0_total_markers"], comp["alternating_mx_total_markers"]],
                ["METAL2.2", comp["all_r0_metal2_2"], comp["alternating_mx_metal2_2"]],
                ["row_boundary_METAL2", comp["all_r0_row_boundary_metal2"], comp["alternating_mx_row_boundary_metal2"]],
                ["power_stitch_related", comp["all_r0_power_stitch_related_markers"], comp["alternating_mx_power_stitch_related_markers"]],
                ["cross_row_power_short_risk", comp["all_r0_cross_row_power_short_risk"], comp["alternating_mx_cross_row_power_short_risk"]],
            ],
        ),
        "",
        "## Next Steps",
        "",
        *[f"- {item}" for item in report["next_step_recommendations"]],
        "",
    ]
    return "\n".join(lines)


def table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell).replace("|", "\\|") for cell in row) + " |")
    return "\n".join(out)


def run_python(args: list[str]) -> None:
    command = [sys.executable, *args]
    completed = subprocess.run(command, cwd=STANDALONE_ROOT, text=True, capture_output=True, check=False)
    if completed.returncode != 0:
        raise RuntimeError(
            "Command failed:\n"
            + " ".join(command)
            + "\n\nSTDOUT:\n"
            + completed.stdout
            + "\n\nSTDERR:\n"
            + completed.stderr
        )


def case_build_dir(policy: str, rows: int, cols: int) -> Path:
    suffix = "stitched" if policy == "all_r0" else "mx"
    return STANDALONE_ROOT / "build" / f"openyield_storage_only_smoke_{rows}x{cols}_{suffix}"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else (STANDALONE_ROOT / path)


def relative_to_root(path: Path) -> Path:
    return path.relative_to(STANDALONE_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
