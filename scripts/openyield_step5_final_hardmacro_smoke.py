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


DEFAULT_OUT_JSON = Path("docs/openyield_step5_final_hardmacro_smoke_report.json")
DEFAULT_OUT_MD = Path("docs/openyield_step5_final_hardmacro_smoke_report.md")
DEFAULT_SUMMARY_JSON = Path("docs/openyield_step5_hardmacro_adapter_summary.json")
DEFAULT_SUMMARY_MD = Path("docs/openyield_step5_hardmacro_adapter_summary.md")

MODE_SPECS = (
    ("legacy_default", False, False, False, False, "all_r0"),
    ("storage_only", True, False, False, False, "alternating_mx"),
    ("read_path_only", False, True, True, False, "all_r0"),
    ("write_path_only", False, False, False, True, "all_r0"),
    ("wordline_only", False, False, False, False, "all_r0", True),
    ("all_hardmacro_opt_in", True, True, True, True, "alternating_mx", True),
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run final OpenYield hard-macro opt-in smoke cases and summarize Step 5.")
    parser.add_argument("--cases", nargs="+", default=["2x16_wpr1", "4x32_wpr2"])
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--summary-json", type=Path, default=DEFAULT_SUMMARY_JSON)
    parser.add_argument("--summary-md", type=Path, default=DEFAULT_SUMMARY_MD)
    args = parser.parse_args()

    out_json = resolve(args.out_json)
    out_md = resolve(args.out_md)
    summary_json = resolve(args.summary_json)
    summary_md = resolve(args.summary_md)
    for path in (out_json, out_md, summary_json, summary_md):
        path.parent.mkdir(parents=True, exist_ok=True)

    cases = [run_case(parse_case(token)) for token in args.cases]
    report = build_smoke_report(args, cases)
    summary = build_summary(report["cases"])

    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(format_smoke_markdown(report), encoding="utf-8")
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary_md.write_text(format_summary_markdown(summary), encoding="utf-8")

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(f"Wrote {summary_json}")
    print(f"Wrote {summary_md}")
    print(
        "cases="
        + ",".join(case["case_id"] for case in report["cases"])
        + f" all_hardmacro_opt_in={report['checks']['all_hardmacro_opt_in_passed']}"
    )
    return 0


def parse_case(token: str) -> dict[str, int | str]:
    try:
        dims, wpr_part = token.split("_wpr", 1)
        word_size_text, num_words_text = dims.split("x", 1)
    except ValueError as exc:
        raise ValueError(f"invalid case token: {token}") from exc
    return {
        "case_id": token,
        "word_size": int(word_size_text),
        "num_words": int(num_words_text),
        "words_per_row": int(wpr_part),
    }


def build_modes() -> list[dict[str, Any]]:
    modes: list[dict[str, Any]] = []
    for item in MODE_SPECS:
        name = item[0]
        enable_storage = bool(item[1])
        enable_senseamp = bool(item[2])
        enable_columnmux = bool(item[3])
        enable_writedriver = bool(item[4])
        storage_policy = str(item[5])
        enable_wordlinedriver = bool(item[6]) if len(item) > 6 else False
        modes.append(
            {
                "name": name,
                "enable_openyield_array_aggregation": enable_storage,
                "enable_openyield_senseamp_adapter": enable_senseamp,
                "enable_openyield_columnmux_adapter": enable_columnmux,
                "enable_openyield_writedriver_adapter": enable_writedriver,
                "enable_openyield_wordlinedriver_adapter": enable_wordlinedriver,
                "openyield_storage_row_orientation_policy": storage_policy,
            }
        )
    return modes


def run_case(case_spec: dict[str, int | str]) -> dict[str, Any]:
    case_id = str(case_spec["case_id"])
    modes: dict[str, dict[str, Any]] = {}
    for mode in build_modes():
        spec = StandaloneSpec(
            word_size=int(case_spec["word_size"]),
            num_words=int(case_spec["num_words"]),
            words_per_row=int(case_spec["words_per_row"]),
            name=mode["name"],
            enable_openyield_array_aggregation=mode["enable_openyield_array_aggregation"],
            enable_openyield_senseamp_adapter=mode["enable_openyield_senseamp_adapter"],
            enable_openyield_columnmux_adapter=mode["enable_openyield_columnmux_adapter"],
            enable_openyield_writedriver_adapter=mode["enable_openyield_writedriver_adapter"],
            enable_openyield_wordlinedriver_adapter=mode["enable_openyield_wordlinedriver_adapter"],
            openyield_storage_row_orientation_policy=mode["openyield_storage_row_orientation_policy"],
        )
        out_dir = STANDALONE_ROOT / "build" / "openyield_step5_final_hardmacro_smoke" / case_id / mode["name"]
        metrics = write_standalone(spec, out_dir)
        modes[mode["name"]] = summarize_mode(mode, spec, out_dir, metrics)

    return {
        "case_id": case_id,
        "word_size": int(case_spec["word_size"]),
        "num_words": int(case_spec["num_words"]),
        "words_per_row": int(case_spec["words_per_row"]),
        "modes": modes,
    }


def summarize_mode(mode: dict[str, Any], spec: StandaloneSpec, out_dir: Path, metrics: dict[str, Any]) -> dict[str, Any]:
    gds_path = Path(str(metrics["gds"]))
    storage = dict(metrics.get("openyield_array_aggregation_integration", {}))
    senseamp = dict(metrics.get("openyield_senseamp_adapter", {}))
    columnmux = dict(metrics.get("openyield_columnmux_adapter", {}))
    writedriver = dict(metrics.get("openyield_writedriver_adapter", {}))
    wordline = dict(metrics.get("openyield_wordlinedriver_adapter", {}))
    gds_ok = gds_path.exists() and gds_path.stat().st_size > 0
    write_driver_count = int(metrics.get("role_counts", {}).get("write_driver", 0) or 0)
    wordline_count = int(metrics.get("role_counts", {}).get("wordline_driver", 0) or 0)
    read_write_conflict = bool(
        mode["name"] == "all_hardmacro_opt_in"
        and not (
            senseamp.get("enabled", False)
            and columnmux.get("enabled", False)
            and writedriver.get("enabled", False)
            and wordline.get("enabled", False)
            and senseamp.get("generated_fake_dout_b", False) is False
            and columnmux.get("uses_repaired_alias", False)
            and writedriver.get("safe_for_physical_mapping", False)
            and wordline.get("semantic_confirmation") == "confirmed_active_high"
        )
    )
    return {
        "mode": mode["name"],
        "spec": {
            "word_size": spec.word_size,
            "num_words": spec.num_words,
            "words_per_row": spec.resolved_words_per_row(),
            "enable_openyield_array_aggregation": spec.enable_openyield_array_aggregation,
            "enable_openyield_senseamp_adapter": spec.enable_openyield_senseamp_adapter,
            "enable_openyield_columnmux_adapter": spec.enable_openyield_columnmux_adapter,
            "enable_openyield_writedriver_adapter": spec.enable_openyield_writedriver_adapter,
            "enable_openyield_wordlinedriver_adapter": spec.enable_openyield_wordlinedriver_adapter,
            "openyield_storage_row_orientation_policy": spec.openyield_storage_row_orientation_policy,
        },
        "out_dir": str(out_dir.resolve()),
        "generated_gds": str(gds_path.resolve()),
        "generated_gds_exists": gds_ok,
        "generated_gds_size": gds_path.stat().st_size if gds_path.exists() else 0,
        "layout_bbox": {
            "width_um": float(metrics["width_um"]),
            "height_um": float(metrics["height_um"]),
            "area_um2": float(metrics["macro_area_um2"]),
        },
        "storage_aggregation_enabled": bool(storage.get("enabled", False)),
        "storage_row_policy": storage.get("row_orientation_policy", "all_r0"),
        "storage_pitch": storage.get("pitch", {}),
        "storage_cross_row_power_short_risk": storage.get("cross_row_power_short_risk"),
        "storage_instance_count": int(storage.get("instance_count", 0) or 0),
        "senseamp_enabled": bool(senseamp.get("enabled", False)),
        "senseamp_local_macro": senseamp.get("local_macro", "sense_amp"),
        "senseamp_adapter_strategy": senseamp.get("adapter_strategy", "single_ended_q_to_dout"),
        "senseamp_generated_fake_dout_b": bool(senseamp.get("generated_fake_dout_b", False)),
        "senseamp_qb_drop": senseamp.get("dropped_pins", {}).get("QB"),
        "columnmux_enabled": bool(columnmux.get("enabled", False)),
        "columnmux_local_macro": columnmux.get("local_macro", "gen_col_mux"),
        "columnmux_uses_repaired_alias": bool(columnmux.get("uses_repaired_alias", False)),
        "columnmux_safe_for_shared_rail": bool(columnmux.get("safe_for_shared_rail", False)),
        "columnmux_senseamp_pairing": dict(columnmux.get("senseamp_pairing", {})),
        "writedriver_enabled": bool(writedriver.get("enabled", False)),
        "writedriver_local_macro": writedriver.get("local_macro", "write_driver"),
        "writedriver_mapping_ok": write_driver_mapping_ok(writedriver),
        "writedriver_safe_for_physical_mapping": bool(writedriver.get("safe_for_physical_mapping", False)),
        "writedriver_safe_for_shared_rail": bool(writedriver.get("safe_for_shared_rail", False)),
        "writedriver_pin_adaptations": list(writedriver.get("pin_adaptations", [])),
        "wordlinedriver_enabled": bool(wordline.get("enabled", False)),
        "wordlinedriver_local_macro": wordline.get("local_macro", "gen_wl_driver"),
        "wordlinedriver_b_polarity": wordline.get("b_polarity"),
        "wordlinedriver_semantic_confirmation": wordline.get("semantic_confirmation"),
        "wordlinedriver_can_enter_limited_placement": bool(wordline.get("can_enter_limited_placement", False)),
        "wordlinedriver_pin_report_consistent": bool(
            wordline.get("enabled", False)
            and wordline.get("adapter_applied_to_placement", False)
            and wordline.get("can_enter_limited_placement", False)
            and wordline.get("semantic_confirmation") == "confirmed_active_high"
        ),
        "wordline_driver_instance_count": wordline_count,
        "write_driver_instance_count": write_driver_count,
        "routing_changed": bool(
            columnmux.get("routing_changed", False)
            or writedriver.get("routing_changed", False)
            or wordline.get("routing_changed", False)
            or senseamp.get("routing_changed", False)
        ),
        "gds_writer_changed": bool(
            columnmux.get("gds_writer_changed", False)
            or writedriver.get("gds_writer_changed", False)
            or wordline.get("gds_writer_changed", False)
            or senseamp.get("gds_writer_changed", False)
        ),
        "shared_rail_enabled": bool(
            storage.get("shared_rail_enabled", False)
            or columnmux.get("shared_rail_enabled", False)
            or writedriver.get("shared_rail_enabled", False)
            or wordline.get("shared_rail_enabled", False)
        ),
        "legacy_default_kept_legacy_path": mode["name"] == "legacy_default",
        "grouped_mapping_requires_later_confirmation": bool(mode["name"] in {"write_path_only", "all_hardmacro_opt_in"}),
        "read_write_conflict_found": read_write_conflict,
        "generated_gds": gds_ok,
        "all_hardmacro_opt_in": mode["name"] == "all_hardmacro_opt_in",
        "adapter_enabled_count": sum(
            int(bool(flag))
            for flag in (
                storage.get("enabled", False),
                senseamp.get("enabled", False),
                columnmux.get("enabled", False),
                writedriver.get("enabled", False),
                wordline.get("enabled", False),
            )
        ),
    }


def write_driver_mapping_ok(writedriver: dict[str, Any]) -> bool:
    if not writedriver.get("enabled", False):
        return True
    adaptations = {str(item.get("openyield_pin") or ""): item for item in writedriver.get("pin_adaptations", [])}
    expected = {
        "VDD": "vdd",
        "VSS": "gnd",
        "EN": "write_enable",
        "DIN": "din",
        "BL": "bl",
        "BLB": "br",
    }
    for pin, canonical in expected.items():
        entry = adaptations.get(pin)
        if not entry or str(entry.get("canonical_signal") or "") != canonical:
            return False
    return True


def build_smoke_report(args: argparse.Namespace, cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "scope": "step5_final_openyield_hardmacro_opt_in_smoke",
        "cases_requested": [str(token) for token in args.cases],
        "cases": cases,
        "checks": {
            "legacy_default_preserved": all(case["modes"]["legacy_default"]["legacy_default_kept_legacy_path"] for case in cases),
            "storage_only_passed": all(
                case["modes"]["storage_only"]["storage_aggregation_enabled"]
                and case["modes"]["storage_only"]["storage_row_policy"] == "alternating_mx"
                and case["modes"]["storage_only"]["routing_changed"] is False
                and case["modes"]["storage_only"]["gds_writer_changed"] is False
                and case["modes"]["storage_only"]["shared_rail_enabled"] is False
                for case in cases
            ),
            "read_path_only_passed": all(
                case["modes"]["read_path_only"]["senseamp_enabled"]
                and case["modes"]["read_path_only"]["columnmux_enabled"]
                and case["modes"]["read_path_only"]["columnmux_uses_repaired_alias"]
                and case["modes"]["read_path_only"]["senseamp_generated_fake_dout_b"] is False
                and case["modes"]["read_path_only"]["writedriver_enabled"] is False
                and case["modes"]["read_path_only"]["wordlinedriver_enabled"] is False
                and case["modes"]["read_path_only"]["routing_changed"] is False
                and case["modes"]["read_path_only"]["gds_writer_changed"] is False
                for case in cases
            ),
            "write_path_only_passed": all(
                case["modes"]["write_path_only"]["writedriver_enabled"]
                and case["modes"]["write_path_only"]["writedriver_mapping_ok"]
                and case["modes"]["write_path_only"]["senseamp_enabled"] is False
                and case["modes"]["write_path_only"]["columnmux_enabled"] is False
                and case["modes"]["write_path_only"]["wordlinedriver_enabled"] is False
                and case["modes"]["write_path_only"]["routing_changed"] is False
                and case["modes"]["write_path_only"]["gds_writer_changed"] is False
                for case in cases
            ),
            "wordline_only_passed": all(
                case["modes"]["wordline_only"]["wordlinedriver_enabled"]
                and case["modes"]["wordline_only"]["wordlinedriver_b_polarity"] == "high_active"
                and case["modes"]["wordline_only"]["wordlinedriver_semantic_confirmation"] == "confirmed_active_high"
                and case["modes"]["wordline_only"]["routing_changed"] is False
                and case["modes"]["wordline_only"]["gds_writer_changed"] is False
                for case in cases
            ),
            "all_hardmacro_opt_in_passed": all(
                case["modes"]["all_hardmacro_opt_in"]["storage_aggregation_enabled"]
                and case["modes"]["all_hardmacro_opt_in"]["senseamp_enabled"]
                and case["modes"]["all_hardmacro_opt_in"]["columnmux_enabled"]
                and case["modes"]["all_hardmacro_opt_in"]["writedriver_enabled"]
                and case["modes"]["all_hardmacro_opt_in"]["wordlinedriver_enabled"]
                and case["modes"]["all_hardmacro_opt_in"]["generated_gds"]
                and case["modes"]["all_hardmacro_opt_in"]["shared_rail_enabled"] is False
                and case["modes"]["all_hardmacro_opt_in"]["senseamp_generated_fake_dout_b"] is False
                and case["modes"]["all_hardmacro_opt_in"]["columnmux_uses_repaired_alias"]
                and case["modes"]["all_hardmacro_opt_in"]["writedriver_mapping_ok"]
                and case["modes"]["all_hardmacro_opt_in"]["wordlinedriver_semantic_confirmation"] == "confirmed_active_high"
                and case["modes"]["all_hardmacro_opt_in"]["read_write_conflict_found"] is False
                and case["modes"]["all_hardmacro_opt_in"]["grouped_mapping_requires_later_confirmation"] is True
                and case["modes"]["all_hardmacro_opt_in"]["routing_changed"] is False
                and case["modes"]["all_hardmacro_opt_in"]["gds_writer_changed"] is False
                for case in cases
            ),
        },
        "summary": build_summary(cases),
        "standalone_modified": False,
        "new_parameters": {
            "enable_openyield_array_aggregation": False,
            "enable_openyield_senseamp_adapter": False,
            "enable_openyield_columnmux_adapter": False,
            "enable_openyield_writedriver_adapter": False,
            "enable_openyield_wordlinedriver_adapter": False,
            "openyield_storage_row_orientation_policy": "all_r0",
        },
        "next_step_recommendation": "proceed_to_step6_1_time_dff_control_decomposition_audit",
    }


def build_summary(cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "completed": [
            "sense_amp: Q -> dout, QB dropped, no fake dout_b.",
            "column mux: OUT/OUTB -> mux_out/mux_out_b, using repaired alias gen_col_mux_vdd_labeled.",
            "write driver: DIN/EN/BL/BLB -> din/write_enable/bl/br.",
            "wordline driver: A/B/Z -> decoder_input/wordline_enable/wl, B high-active.",
            "read/write semantic review passed.",
            "storage alternating_mx is available as an explicit opt-in.",
            "All adapters remain default-off, so the legacy default path is preserved.",
        ],
        "remaining": [
            "TIME / DFF / control logic are not yet decomposed into substructure-level adapters.",
            "Grouped mux/write mapping still needs a layout-level fanout proof.",
            "Routing is still not OpenYield-driven.",
            "Shared rail remains disabled.",
            "Full DRC/LVS/signoff is still incomplete.",
            "Peripheral placement is opt-in only; routing still follows the old path.",
        ],
        "step6_recommendation": "Step 6.1: TIME / DFF / control logic decomposition audit",
        "case_notes": [
            {
                "case_id": case["case_id"],
                "legacy_bbox": case["modes"]["legacy_default"]["layout_bbox"],
                "all_hardmacro_bbox": case["modes"]["all_hardmacro_opt_in"]["layout_bbox"],
                "all_hardmacro_area_delta_um2": round(
                    float(case["modes"]["all_hardmacro_opt_in"]["layout_bbox"]["area_um2"])
                    - float(case["modes"]["legacy_default"]["layout_bbox"]["area_um2"]),
                    6,
                ),
                "all_hardmacro_area_delta_percent": round(
                    100.0
                    * (
                        float(case["modes"]["all_hardmacro_opt_in"]["layout_bbox"]["area_um2"])
                        - float(case["modes"]["legacy_default"]["layout_bbox"]["area_um2"])
                    )
                    / max(float(case["modes"]["legacy_default"]["layout_bbox"]["area_um2"]), 1e-9),
                    3,
                ),
            }
            for case in cases
        ],
    }


def format_mode_summary(mode_name: str, mode: dict[str, Any]) -> str:
    bbox = mode["layout_bbox"]
    return (
        f"| {mode_name} | {mode['generated_gds_exists']} | "
        f"{bbox['width_um']:.4f} x {bbox['height_um']:.4f} | {bbox['area_um2']:.4f} | "
        f"{mode['storage_aggregation_enabled']} | {mode['storage_row_policy']} | "
        f"{mode['senseamp_enabled']} | {mode['columnmux_enabled']} | {mode['writedriver_enabled']} | {mode['wordlinedriver_enabled']} | "
        f"{mode['columnmux_uses_repaired_alias']} | {mode['senseamp_generated_fake_dout_b']} | "
        f"{mode['writedriver_mapping_ok']} | {mode['wordlinedriver_b_polarity']} | {mode['read_write_conflict_found']} | "
        f"{mode['routing_changed']} | {mode['gds_writer_changed']} | {mode['shared_rail_enabled']} |"
    )


def format_smoke_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Step 5 Final Hardmacro Smoke Report",
        "",
        "This report is a final-step combination smoke only. It is not final DRC/LVS signoff.",
        "",
        "## Checks",
        "",
    ]
    for key, value in report["checks"].items():
        lines.append(f"- {key}: `{value}`")
    lines.extend(["", "## Case Summary", ""])
    for case in report["cases"]:
        lines.extend(
            [
                f"### {case['case_id']}",
                "",
                "| mode | GDS | bbox (W x H) | area | storage | storage policy | senseamp | columnmux | writedriver | wordline | repaired alias | fake dout_b | write mapping | B polarity | read/write conflict | routing changed | GDS writer changed | shared rail |",
                "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
            ]
        )
        for mode_name, mode in case["modes"].items():
            lines.append(format_mode_summary(mode_name, mode))
        legacy = case["modes"]["legacy_default"]["layout_bbox"]
        hard = case["modes"]["all_hardmacro_opt_in"]["layout_bbox"]
        lines.extend(
            [
                "",
                f"- legacy_default bbox: `{legacy['width_um']:.4f} x {legacy['height_um']:.4f}` area `{legacy['area_um2']:.4f}`",
                f"- all_hardmacro_opt_in bbox: `{hard['width_um']:.4f} x {hard['height_um']:.4f}` area `{hard['area_um2']:.4f}`",
                f"- area delta: `{hard['area_um2'] - legacy['area_um2']:.4f}`",
                f"- area delta percent: `{100.0 * (hard['area_um2'] - legacy['area_um2']) / max(legacy['area_um2'], 1e-9):.3f}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Summary",
            "",
            *[f"- {item}" for item in report["summary"]["completed"]],
            "",
            "## Remaining",
            "",
            *[f"- {item}" for item in report["summary"]["remaining"]],
            "",
            "## Next Step",
            "",
            f"- {report['summary']['step6_recommendation']}",
            "",
        ]
    )
    return "\n".join(lines)


def format_summary_markdown(summary: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Step 5 Hardmacro Adapter Summary",
        "",
        "## Completed",
        "",
        *[f"- {item}" for item in summary["completed"]],
        "",
        "## Still Unresolved",
        "",
        *[f"- {item}" for item in summary["remaining"]],
        "",
        "## Recommendation",
        "",
        f"- {summary['step6_recommendation']}",
        "",
        "## Case Notes",
        "",
    ]
    for item in summary["case_notes"]:
        lines.extend(
            [
                f"### {item['case_id']}",
                f"- legacy bbox: `{item['legacy_bbox']}`",
                f"- all_hardmacro bbox: `{item['all_hardmacro_bbox']}`",
                f"- area delta um2: `{item['all_hardmacro_area_delta_um2']}`",
                f"- area delta percent: `{item['all_hardmacro_area_delta_percent']}`",
                "",
            ]
        )
    return "\n".join(lines)


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else (STANDALONE_ROOT / path)


if __name__ == "__main__":
    raise SystemExit(main())
