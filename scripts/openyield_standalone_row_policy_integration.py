from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))

from sram_layoutgen.standalone import StandaloneSpec, write_standalone  # noqa: E402


DEFAULT_OUT_JSON = Path("docs/openyield_standalone_row_policy_integration_report.json")
DEFAULT_OUT_MD = Path("docs/openyield_standalone_row_policy_integration_report.md")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test standalone storage row orientation policy integration.")
    parser.add_argument("--word-size", type=int, default=2)
    parser.add_argument("--num-words", type=int, default=16)
    parser.add_argument("--words-per-row", type=int, default=1)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    args = parser.parse_args()

    out_json = resolve(args.out_json)
    out_md = resolve(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)

    cases = {
        "legacy_default": run_case(
            "legacy_default",
            StandaloneSpec(
                word_size=args.word_size,
                num_words=args.num_words,
                words_per_row=args.words_per_row,
            ),
        ),
        "openyield_all_r0": run_case(
            "openyield_all_r0",
            StandaloneSpec(
                word_size=args.word_size,
                num_words=args.num_words,
                words_per_row=args.words_per_row,
                enable_openyield_array_aggregation=True,
                openyield_storage_row_orientation_policy="all_r0",
            ),
        ),
        "openyield_alternating_mx": run_case(
            "openyield_alternating_mx",
            StandaloneSpec(
                word_size=args.word_size,
                num_words=args.num_words,
                words_per_row=args.words_per_row,
                enable_openyield_array_aggregation=True,
                openyield_storage_row_orientation_policy="alternating_mx",
            ),
        ),
    }
    report = build_report(args, cases)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(format_markdown(report), encoding="utf-8")

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(
        f"legacy_ok={report['checks']['default_legacy_path_preserved']} "
        f"all_r0_ok={report['checks']['all_r0_path_ok']} "
        f"alternating_mx_ok={report['checks']['alternating_mx_path_ok']}"
    )
    return 0


def run_case(case_name: str, spec: StandaloneSpec) -> dict[str, Any]:
    out_dir = STANDALONE_ROOT / "build" / f"openyield_standalone_row_policy_{case_name}"
    metrics = write_standalone(spec, out_dir)
    integration = dict(metrics.get("openyield_array_aggregation_integration", {}))
    mirror_audit = dict(metrics.get("cell_array_mirror_audit", {}))
    storage_arrays = [
        item
        for item in mirror_audit.get("arrays", [])
        if item.get("array") in {"bitcell_array", "dummy_left_array", "dummy_right_array", "replica_bitline_array"}
    ]
    return {
        "spec": {
            "enable_openyield_array_aggregation": spec.enable_openyield_array_aggregation,
            "openyield_storage_row_orientation_policy": spec.openyield_storage_row_orientation_policy,
            "word_size": spec.word_size,
            "num_words": spec.num_words,
            "words_per_row": spec.resolved_words_per_row(),
        },
        "outputs": {
            "out_dir": str(out_dir),
            "gds": metrics.get("gds"),
            "report_json": str(out_dir / f"{spec.resolved_name()}.report.json"),
            "report_md": metrics.get("report_md"),
        },
        "integration": integration,
        "mirror_audit": {
            "clean": mirror_audit.get("clean"),
            "missing_required_row_mirror_count": mirror_audit.get("missing_required_row_mirror_count"),
            "storage_arrays": storage_arrays,
        },
        "metrics": {
            "width_um": metrics.get("width_um"),
            "height_um": metrics.get("height_um"),
            "macro_area_um2": metrics.get("macro_area_um2"),
            "route_guide_count": metrics.get("layout_completeness", {}).get("route_guide_count"),
            "generated_gds": bool(metrics.get("gds")),
        },
    }


def build_report(args: argparse.Namespace, cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    legacy = cases["legacy_default"]
    all_r0 = cases["openyield_all_r0"]
    alt = cases["openyield_alternating_mx"]
    legacy_integration = legacy["integration"]
    all_r0_integration = all_r0["integration"]
    alt_integration = alt["integration"]

    checks = {
        "default_legacy_path_preserved": (
            legacy["spec"]["enable_openyield_array_aggregation"] is False
            and legacy_integration.get("enabled") is False
            and legacy_integration.get("row_orientation_policy") == "all_r0"
        ),
        "all_r0_path_ok": (
            all_r0_integration.get("enabled") is True
            and all_r0_integration.get("row_orientation_policy") == "all_r0"
            and all_r0_integration.get("cross_row_power_short_risk") is True
        ),
        "alternating_mx_path_ok": (
            alt_integration.get("enabled") is True
            and alt_integration.get("row_orientation_policy") == "alternating_mx"
            and alt_integration.get("cross_row_power_short_risk") is False
        ),
        "peripherals_old_path_preserved": (
            all_r0_integration.get("peripherals_old_path") is True
            and alt_integration.get("peripherals_old_path") is True
        ),
        "routing_unchanged": (
            all_r0_integration.get("routing_changed") is False
            and alt_integration.get("routing_changed") is False
        ),
        "gds_writer_unchanged": (
            all_r0_integration.get("gds_writer_changed") is False
            and alt_integration.get("gds_writer_changed") is False
        ),
        "shared_rail_merge_unchanged": (
            all_r0_integration.get("shared_rail_merge") is False
            and alt_integration.get("shared_rail_merge") is False
        ),
    }

    return {
        "scope": "standalone_storage_row_orientation_policy_integration",
        "standalone_modified": True,
        "new_parameter_name": "openyield_storage_row_orientation_policy",
        "default_value": "all_r0",
        "supported_row_orientation_policies": ["all_r0", "alternating_mx"],
        "test_case": {
            "word_size": args.word_size,
            "num_words": args.num_words,
            "words_per_row": args.words_per_row,
        },
        "cases": cases,
        "checks": checks,
        "all_r0_vs_alternating_mx_drc_compare": {
            "source_report": str(STANDALONE_ROOT / "docs" / "openyield_row_orientation_compare_report.json"),
            "all_r0_total_markers": 84,
            "alternating_mx_total_markers": 44,
            "all_r0_metal2_2": 34,
            "alternating_mx_metal2_2": 0,
            "all_r0_row_boundary_metal2": 34,
            "alternating_mx_row_boundary_metal2": 0,
            "all_r0_cross_row_power_short_risk": True,
            "alternating_mx_cross_row_power_short_risk": False,
        },
        "recommend_continue": all(checks.values()),
        "next_step_recommendations": [
            "Keep the default standalone behavior unchanged; only explicit opt-in should activate OpenYield storage aggregation.",
            "If promoted further, expose the row policy only for storage placement and keep peripheral placement on the old path.",
            "Before broader rollout, re-run the standalone path on representative SRAM sizes and inspect the generated GDS in KLayout.",
        ],
    }


def format_markdown(report: dict[str, Any]) -> str:
    checks = report["checks"]
    compare = report["all_r0_vs_alternating_mx_drc_compare"]
    lines = [
        "# OpenYield Standalone Row Policy Integration Report",
        "",
        "This report checks that the standalone opt-in storage path now accepts an explicit row orientation policy while keeping the default legacy path unchanged.",
        "",
        "## Summary",
        "",
        f"- standalone.py modified: `{report['standalone_modified']}`",
        f"- new parameter name: `{report['new_parameter_name']}`",
        f"- default value: `{report['default_value']}`",
        f"- supported policies: `{report['supported_row_orientation_policies']}`",
        f"- default legacy path preserved: `{checks['default_legacy_path_preserved']}`",
        f"- all_r0 path ok: `{checks['all_r0_path_ok']}`",
        f"- alternating_mx path ok: `{checks['alternating_mx_path_ok']}`",
        f"- peripherals old path preserved: `{checks['peripherals_old_path_preserved']}`",
        f"- routing unchanged: `{checks['routing_unchanged']}`",
        f"- GDS writer unchanged: `{checks['gds_writer_unchanged']}`",
        f"- shared rail merge unchanged: `{checks['shared_rail_merge_unchanged']}`",
        "",
        "## Standalone Cases",
        "",
        table(
            ["case", "enabled", "policy", "cross_row_power_short_risk", "generated_gds", "gds"],
            [
                [
                    name,
                    case["integration"].get("enabled"),
                    case["integration"].get("row_orientation_policy"),
                    case["integration"].get("cross_row_power_short_risk"),
                    case["metrics"].get("generated_gds"),
                    case["outputs"].get("gds"),
                ]
                for name, case in report["cases"].items()
            ],
        ),
        "",
        "## Storage Array Mirror Audit",
        "",
        table(
            ["case", "array", "mirror_x", "role", "policy"],
            [
                [
                    case_name,
                    item.get("array"),
                    item.get("mirror_x"),
                    item.get("role"),
                    item.get("openyield_storage_policy"),
                ]
                for case_name, case in report["cases"].items()
                for item in case["mirror_audit"]["storage_arrays"]
            ],
        ),
        "",
        "## DRC Compare Reference",
        "",
        table(
            ["metric", "all_r0", "alternating_mx"],
            [
                ["total_markers", compare["all_r0_total_markers"], compare["alternating_mx_total_markers"]],
                ["METAL2.2", compare["all_r0_metal2_2"], compare["alternating_mx_metal2_2"]],
                ["row_boundary_METAL2", compare["all_r0_row_boundary_metal2"], compare["alternating_mx_row_boundary_metal2"]],
                ["cross_row_power_short_risk", compare["all_r0_cross_row_power_short_risk"], compare["alternating_mx_cross_row_power_short_risk"]],
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


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else (STANDALONE_ROOT / path)


if __name__ == "__main__":
    raise SystemExit(main())
