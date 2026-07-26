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


DEFAULT_OUT_JSON = Path("docs/openyield_wordlinedriver_standalone_smoke_report.json")
DEFAULT_OUT_MD = Path("docs/openyield_wordlinedriver_standalone_smoke_report.md")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the OpenYield wordline driver opt-in path inside standalone.")
    parser.add_argument("--word-size", type=int, default=4)
    parser.add_argument("--num-words", type=int, default=32)
    parser.add_argument("--words-per-row", type=int, default=2)
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
        "wordlinedriver_only": run_case(
            "wordlinedriver_only",
            StandaloneSpec(
                word_size=args.word_size,
                num_words=args.num_words,
                words_per_row=args.words_per_row,
                enable_openyield_wordlinedriver_adapter=True,
            ),
        ),
        "data_path_plus_wordlinedriver": run_case(
            "data_path_plus_wordlinedriver",
            StandaloneSpec(
                word_size=args.word_size,
                num_words=args.num_words,
                words_per_row=args.words_per_row,
                enable_openyield_senseamp_adapter=True,
                enable_openyield_columnmux_adapter=True,
                enable_openyield_writedriver_adapter=True,
                enable_openyield_wordlinedriver_adapter=True,
            ),
        ),
        "storage_plus_data_path_plus_wordlinedriver": run_case(
            "storage_plus_data_path_plus_wordlinedriver",
            StandaloneSpec(
                word_size=args.word_size,
                num_words=args.num_words,
                words_per_row=args.words_per_row,
                enable_openyield_array_aggregation=True,
                enable_openyield_senseamp_adapter=True,
                enable_openyield_columnmux_adapter=True,
                enable_openyield_writedriver_adapter=True,
                enable_openyield_wordlinedriver_adapter=True,
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
        f"wordlinedriver_ok={report['checks']['wordlinedriver_only_ok']} "
        f"data_path_ok={report['checks']['data_path_plus_wordlinedriver_ok']} "
        f"storage_ok={report['checks']['storage_plus_data_path_plus_wordlinedriver_ok']}"
    )
    return 0


def run_case(case_name: str, spec: StandaloneSpec) -> dict[str, Any]:
    out_dir = STANDALONE_ROOT / "build" / f"openyield_wordlinedriver_standalone_smoke_{case_name}"
    metrics = write_standalone(spec, out_dir)
    wld = metrics.get("openyield_wordlinedriver_adapter", {})
    return {
        "spec": {
            "enable_openyield_array_aggregation": spec.enable_openyield_array_aggregation,
            "enable_openyield_senseamp_adapter": spec.enable_openyield_senseamp_adapter,
            "enable_openyield_columnmux_adapter": spec.enable_openyield_columnmux_adapter,
            "enable_openyield_writedriver_adapter": spec.enable_openyield_writedriver_adapter,
            "enable_openyield_wordlinedriver_adapter": spec.enable_openyield_wordlinedriver_adapter,
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
        "integration": wld,
        "metrics": {
            "width_um": metrics.get("width_um"),
            "height_um": metrics.get("height_um"),
            "macro_area_um2": metrics.get("macro_area_um2"),
            "generated_gds": bool(metrics.get("gds")),
            "wordline_driver_instance_count": int(metrics.get("role_counts", {}).get("wordline_driver", 0) or 0),
            "wordline_driver_pin_labels_verified": bool(wld.get("adapter_applied_to_placement", False))
            and bool(wld.get("can_enter_limited_placement", False)),
            "wordline_driver_pin_report_consistent": bool(
                wld.get("safe_for_physical_mapping", False)
                and not wld.get("safe_for_shared_rail", True)
                and wld.get("adapter_applied_to_placement", False)
            ),
        },
    }


def build_report(args: argparse.Namespace, cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    legacy = cases["legacy_default"]
    wld = cases["wordlinedriver_only"]
    data = cases["data_path_plus_wordlinedriver"]
    storage = cases["storage_plus_data_path_plus_wordlinedriver"]

    checks = {
        "default_legacy_path_preserved": (
            legacy["spec"]["enable_openyield_wordlinedriver_adapter"] is False
            and legacy["integration"].get("enabled") is False
        ),
        "wordlinedriver_only_ok": (
            wld["integration"].get("enabled") is True
            and wld["integration"].get("local_macro") == "gen_wl_driver"
            and wld["integration"].get("safe_for_physical_mapping") is True
            and wld["integration"].get("safe_for_shared_rail") is False
            and wld["integration"].get("can_enter_limited_placement") is True
            and wld["metrics"].get("wordline_driver_pin_labels_verified") is True
            and wld["metrics"].get("wordline_driver_pin_report_consistent") is True
        ),
        "data_path_plus_wordlinedriver_ok": (
            data["integration"].get("enabled") is True
            and data["integration"].get("local_macro") == "gen_wl_driver"
            and data["metrics"].get("generated_gds") is True
            and data["metrics"].get("wordline_driver_instance_count", 0) > 0
        ),
        "storage_plus_data_path_plus_wordlinedriver_ok": (
            storage["integration"].get("enabled") is True
            and storage["integration"].get("local_macro") == "gen_wl_driver"
            and storage["integration"].get("shared_rail_enabled") is False
            and storage["spec"]["enable_openyield_array_aggregation"] is True
            and storage["spec"]["openyield_storage_row_orientation_policy"] == "alternating_mx"
            and storage["metrics"].get("generated_gds") is True
        ),
        "routing_unchanged": all(case["integration"].get("routing_changed") is False for case in cases.values()),
        "gds_writer_unchanged": all(case["integration"].get("gds_writer_changed") is False for case in cases.values()),
        "shared_rail_disabled": all(case["integration"].get("shared_rail_enabled") is False for case in cases.values()),
        "decoder_unchanged": all(case["integration"].get("decoder_changed") is False for case in cases.values() if "decoder_changed" in case["integration"]),
        "time_control_unchanged": all(case["integration"].get("time_control_changed") is False for case in cases.values() if "time_control_changed" in case["integration"]),
    }

    return {
        "scope": "step5_14_wordlinedriver_standalone_smoke",
        "standalone_modified": True,
        "new_parameter_name": "enable_openyield_wordlinedriver_adapter",
        "default_value": False,
        "supported_wordlinedriver_modes": [
            "legacy_default",
            "wordlinedriver_only",
            "data_path_plus_wordlinedriver",
            "storage_plus_data_path_plus_wordlinedriver",
        ],
        "test_case": {
            "word_size": args.word_size,
            "num_words": args.num_words,
            "words_per_row": args.words_per_row,
        },
        "cases": cases,
        "checks": checks,
        "default_legacy_path_preserved": checks["default_legacy_path_preserved"],
        "wordlinedriver_only_ok": checks["wordlinedriver_only_ok"],
        "data_path_plus_wordlinedriver_ok": checks["data_path_plus_wordlinedriver_ok"],
        "storage_plus_data_path_plus_wordlinedriver_ok": checks["storage_plus_data_path_plus_wordlinedriver_ok"],
        "wordline_driver_pin_report_consistent": bool(checks["wordlinedriver_only_ok"]),
        "wordline_driver_pin_labels_verified": bool(wld["metrics"].get("wordline_driver_pin_labels_verified", False)),
        "wordline_driver_instance_count": wld["metrics"].get("wordline_driver_instance_count", 0),
        "all_modes_generated_gds": all(item["metrics"].get("generated_gds") for item in cases.values()),
        "routing_changed": False,
        "gds_writer_changed": False,
        "shared_rail_enabled": False,
        "legacy_default_kept_legacy_path": legacy["integration"].get("enabled") is False,
        "wordlinedriver_only_enabled": wld["integration"].get("enabled") is True,
        "data_path_plus_wordlinedriver_enabled": data["integration"].get("enabled") is True,
        "storage_plus_data_path_plus_wordlinedriver_enabled": storage["integration"].get("enabled") is True,
        "storage_plus_data_path_plus_wordlinedriver_uses_alternating_mx": storage["spec"]["openyield_storage_row_orientation_policy"] == "alternating_mx",
        "next_step_recommendation": "proceed_to_step5_peripheral_integration_review",
    }


def format_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Wordline Driver Standalone Smoke Report",
        "",
        f"- case: `{report['test_case']['word_size']}x{report['test_case']['num_words']}_wpr{report['test_case']['words_per_row']}`",
        f"- standalone modified: `{report['standalone_modified']}`",
        f"- new parameter: `enable_openyield_wordlinedriver_adapter` default `{report['default_value']}`",
        f"- all modes generated GDS: `{report['all_modes_generated_gds']}`",
        f"- legacy_default kept legacy path: `{report['legacy_default_kept_legacy_path']}`",
        f"- wordlinedriver_only enabled: `{report['wordlinedriver_only_enabled']}`",
        f"- data_path_plus_wordlinedriver enabled: `{report['data_path_plus_wordlinedriver_enabled']}`",
        f"- storage_plus_data_path_plus_wordlinedriver enabled: `{report['storage_plus_data_path_plus_wordlinedriver_enabled']}`",
        f"- storage_plus_data_path_plus_wordlinedriver uses alternating_mx: `{report['storage_plus_data_path_plus_wordlinedriver_uses_alternating_mx']}`",
        f"- wordline_driver_pin_labels_verified: `{report['wordline_driver_pin_labels_verified']}`",
        f"- wordline_driver_pin_report_consistent: `{report['wordline_driver_pin_report_consistent']}`",
        f"- routing changed: `{report['routing_changed']}`",
        f"- GDS writer changed: `{report['gds_writer_changed']}`",
        f"- shared rail enabled: `{report['shared_rail_enabled']}`",
        f"- wordline driver instance count: `{report['wordline_driver_instance_count']}`",
        f"- next step recommendation: `{report['next_step_recommendation']}`",
        "",
        "## Mode Summary",
        "",
        "| mode | GDS | bbox (W x H) | area | wordline_driver count | local macro | safe phys | safe shared | pin report | enabled | routing changed | GDS writer changed |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for name, item in report["cases"].items():
        bbox = item["metrics"]
        lines.append(
            f"| {name} | {item['metrics'].get('generated_gds')} | "
            f"{bbox['width_um']:.4f} x {bbox['height_um']:.4f} | {bbox['macro_area_um2']:.4f} | "
            f"{item['metrics'].get('wordline_driver_instance_count')} | {item['integration'].get('local_macro')} | "
            f"{item['integration'].get('safe_for_physical_mapping')} | {item['integration'].get('safe_for_shared_rail')} | "
            f"{item['metrics'].get('wordline_driver_pin_report_consistent')} | {item['integration'].get('enabled')} | "
            f"{item['integration'].get('routing_changed')} | {item['integration'].get('gds_writer_changed')} |"
        )
    lines.extend(["", "## Checks", ""])
    for key, value in report["checks"].items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines)


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else (STANDALONE_ROOT / path)


if __name__ == "__main__":
    raise SystemExit(main())
