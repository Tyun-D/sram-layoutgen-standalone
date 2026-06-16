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


DEFAULT_OUT_JSON = Path("docs/openyield_senseamp_standalone_smoke_report.json")
DEFAULT_OUT_MD = Path("docs/openyield_senseamp_standalone_smoke_report.md")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test standalone OpenYield sense_amp adapter integration.")
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
        "senseamp_only": run_case(
            "senseamp_only",
            StandaloneSpec(
                word_size=args.word_size,
                num_words=args.num_words,
                words_per_row=args.words_per_row,
                enable_openyield_senseamp_adapter=True,
            ),
        ),
        "storage_plus_senseamp": run_case(
            "storage_plus_senseamp",
            StandaloneSpec(
                word_size=args.word_size,
                num_words=args.num_words,
                words_per_row=args.words_per_row,
                enable_openyield_array_aggregation=True,
                openyield_storage_row_orientation_policy="alternating_mx",
                enable_openyield_senseamp_adapter=True,
            ),
        ),
    }
    report = build_report(args, cases)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(format_markdown(report), encoding="utf-8")
    print(
        "legacy={legacy} senseamp={senseamp} storage_plus={storage}".format(
            legacy=report["checks"]["legacy_default_preserved"],
            senseamp=report["checks"]["senseamp_only_passed"],
            storage=report["checks"]["storage_plus_senseamp_passed"],
        )
    )
    return 0


def run_case(case_name: str, spec: StandaloneSpec) -> dict[str, Any]:
    out_dir = STANDALONE_ROOT / "build" / f"openyield_senseamp_standalone_{case_name}"
    metrics = write_standalone(spec, out_dir)
    sense_meta = dict(metrics.get("openyield_senseamp_adapter", {}))
    storage_meta = dict(metrics.get("openyield_array_aggregation_integration", {}))
    return {
        "spec": {
            "word_size": spec.word_size,
            "num_words": spec.num_words,
            "words_per_row": spec.resolved_words_per_row(),
            "enable_openyield_array_aggregation": spec.enable_openyield_array_aggregation,
            "enable_openyield_senseamp_adapter": spec.enable_openyield_senseamp_adapter,
            "openyield_storage_row_orientation_policy": spec.openyield_storage_row_orientation_policy,
        },
        "outputs": {
            "out_dir": str(out_dir),
            "gds": metrics.get("gds"),
            "report_md": metrics.get("report_md"),
            "generated_gds": bool(metrics.get("gds")),
        },
        "metrics": {
            "width_um": metrics.get("width_um"),
            "height_um": metrics.get("height_um"),
            "macro_area_um2": metrics.get("macro_area_um2"),
            "sense_amp_instance_count": metrics.get("role_counts", {}).get("sense_amp", 0),
        },
        "senseamp_adapter": sense_meta,
        "storage_aggregation": storage_meta,
    }


def build_report(args: argparse.Namespace, cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    legacy = cases["legacy_default"]
    senseamp = cases["senseamp_only"]
    storage_plus = cases["storage_plus_senseamp"]

    legacy_adapter = legacy["senseamp_adapter"]
    senseamp_adapter = senseamp["senseamp_adapter"]
    storage_plus_adapter = storage_plus["senseamp_adapter"]
    legacy_storage = legacy["storage_aggregation"]
    storage_plus_storage = storage_plus["storage_aggregation"]

    checks = {
        "legacy_default_preserved": (
            legacy["spec"]["enable_openyield_senseamp_adapter"] is False
            and legacy_adapter.get("enabled") is False
            and legacy_adapter.get("adapter_applied_to_placement") is False
            and legacy_storage.get("enabled") is False
            and legacy_adapter.get("routing_changed") is False
            and legacy_adapter.get("gds_writer_changed") is False
        ),
        "senseamp_only_passed": (
            senseamp["spec"]["enable_openyield_senseamp_adapter"] is True
            and senseamp_adapter.get("enabled") is True
            and senseamp_adapter.get("adapter_applied_to_placement") is True
            and senseamp_adapter.get("adapter_strategy") == "single_ended_q_to_dout"
            and senseamp_adapter.get("generated_fake_dout_b") is False
            and senseamp_adapter.get("write_driver_changed") is False
            and senseamp_adapter.get("column_mux_changed") is False
            and senseamp_adapter.get("wordline_driver_changed") is False
            and senseamp_adapter.get("routing_changed") is False
            and senseamp_adapter.get("gds_writer_changed") is False
            and senseamp["outputs"]["generated_gds"] is True
        ),
        "storage_plus_senseamp_passed": (
            storage_plus["spec"]["enable_openyield_senseamp_adapter"] is True
            and storage_plus["spec"]["enable_openyield_array_aggregation"] is True
            and storage_plus_adapter.get("enabled") is True
            and storage_plus_storage.get("enabled") is True
            and storage_plus_storage.get("row_orientation_policy") == "alternating_mx"
            and storage_plus_adapter.get("generated_fake_dout_b") is False
            and storage_plus["outputs"]["generated_gds"] is True
        ),
    }

    return {
        "scope": "standalone_openyield_senseamp_adapter_opt_in_smoke",
        "standalone_modified": True,
        "new_parameter_name": "enable_openyield_senseamp_adapter",
        "default_value": False,
        "test_case": {
            "word_size": args.word_size,
            "num_words": args.num_words,
            "words_per_row": args.words_per_row,
        },
        "cases": cases,
        "checks": checks,
        "summary": {
            "generated_fake_dout_b": any(
                case["senseamp_adapter"].get("generated_fake_dout_b", False)
                for case in cases.values()
            ),
            "routing_changed": any(
                case["senseamp_adapter"].get("routing_changed", False)
                for case in cases.values()
            ),
            "gds_writer_changed": any(
                case["senseamp_adapter"].get("gds_writer_changed", False)
                for case in cases.values()
            ),
            "write_driver_changed": any(
                case["senseamp_adapter"].get("write_driver_changed", False)
                for case in cases.values()
            ),
            "column_mux_changed": any(
                case["senseamp_adapter"].get("column_mux_changed", False)
                for case in cases.values()
            ),
            "wordline_driver_changed": any(
                case["senseamp_adapter"].get("wordline_driver_changed", False)
                for case in cases.values()
            ),
        },
        "can_continue_to_next_adapter": all(checks.values()),
        "next_step_recommendations": [
            "Keep the sense_amp adapter opt-in only; do not enable it by default yet.",
            "Use the same pattern for the next peripheral adapter so the main flow stays easy to audit.",
            "The next adapter should be column mux or write driver, depending on whether you want to settle data-path source semantics or write-path semantics first.",
        ],
    }


def format_markdown(report: dict[str, Any]) -> str:
    checks = report["checks"]
    summary = report["summary"]
    lines = [
        "# OpenYield SenseAmp Standalone Smoke Report",
        "",
        "This report checks that the sense_amp adapter is wired into standalone as an explicit opt-in path while leaving the legacy path unchanged.",
        "",
        "## Summary",
        "",
        f"- standalone.py modified: `{report['standalone_modified']}`",
        f"- new parameter: `{report['new_parameter_name']}`",
        f"- default value: `{report['default_value']}`",
        f"- legacy_default preserved: `{checks['legacy_default_preserved']}`",
        f"- senseamp_only passed: `{checks['senseamp_only_passed']}`",
        f"- storage_plus_senseamp passed: `{checks['storage_plus_senseamp_passed']}`",
        f"- generated fake dout_b: `{summary['generated_fake_dout_b']}`",
        f"- routing changed: `{summary['routing_changed']}`",
        f"- GDS writer changed: `{summary['gds_writer_changed']}`",
        f"- write_driver changed: `{summary['write_driver_changed']}`",
        f"- column_mux changed: `{summary['column_mux_changed']}`",
        f"- wordline_driver changed: `{summary['wordline_driver_changed']}`",
        "",
        "## Cases",
        "",
        table(
            ["case", "senseamp_enabled", "storage_enabled", "generated_gds", "sense_amp_count", "adapter_strategy", "gds"],
            [
                [
                    name,
                    case["spec"]["enable_openyield_senseamp_adapter"],
                    case["spec"]["enable_openyield_array_aggregation"],
                    case["outputs"]["generated_gds"],
                    case["metrics"]["sense_amp_instance_count"],
                    case["senseamp_adapter"].get("adapter_strategy"),
                    case["outputs"]["gds"],
                ]
                for name, case in report["cases"].items()
            ],
        ),
        "",
        "## SenseAmp Mapping",
        "",
        f"- local macro: `{report['cases']['senseamp_only']['senseamp_adapter'].get('local_macro')}`",
        f"- local pins: `{', '.join(report['cases']['senseamp_only']['senseamp_adapter'].get('local_pins', []))}`",
        f"- dropped pins: `{report['cases']['senseamp_only']['senseamp_adapter'].get('dropped_pins')}`",
        f"- example placements: `{report['cases']['senseamp_only']['senseamp_adapter'].get('example_placements', [])}`",
        "",
        "## Next Step",
        "",
    ]
    for item in report["next_step_recommendations"]:
        lines.append(f"- {item}")
    lines.append("")
    return "\n".join(lines)


def table(headers: list[str], rows: list[list[object]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(str(item) for item in row) + " |")
    return "\n".join(lines)


def resolve(path: Path) -> Path:
    if path.is_absolute():
        return path
    return STANDALONE_ROOT / path


if __name__ == "__main__":
    raise SystemExit(main())
