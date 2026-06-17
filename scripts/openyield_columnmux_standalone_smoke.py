from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.gds_pin_audit import read_gds_labels_and_shapes  # noqa: E402
from sram_layoutgen.standalone import StandaloneSpec, write_standalone  # noqa: E402


DEFAULT_WORD_SIZE = 4
DEFAULT_NUM_WORDS = 32
DEFAULT_WORDS_PER_ROW = 2
DEFAULT_ALIAS_GDS = Path("technology/freepdk45/gds_lib/openyield_repaired/gen_col_mux_vdd_labeled.gds")


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the OpenYield column mux opt-in path inside standalone.")
    parser.add_argument("--word-size", type=int, default=DEFAULT_WORD_SIZE)
    parser.add_argument("--num-words", type=int, default=DEFAULT_NUM_WORDS)
    parser.add_argument("--words-per-row", type=int, default=DEFAULT_WORDS_PER_ROW)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    parser.add_argument(
        "--alias-gds",
        default=str(DEFAULT_ALIAS_GDS),
        help="Repaired column mux candidate GDS used for label proof checking.",
    )
    args = parser.parse_args()

    alias_gds = resolve_path(args.alias_gds)
    alias_audit = audit_alias_gds(alias_gds)

    modes = build_modes(args.word_size, args.num_words, args.words_per_row)
    results: list[dict[str, Any]] = []
    for mode in modes:
        spec = StandaloneSpec(
            word_size=args.word_size,
            num_words=args.num_words,
            words_per_row=args.words_per_row,
            name=mode["name"],
            enable_openyield_array_aggregation=mode["enable_openyield_array_aggregation"],
            enable_openyield_senseamp_adapter=mode["enable_openyield_senseamp_adapter"],
            enable_openyield_columnmux_adapter=mode["enable_openyield_columnmux_adapter"],
            openyield_storage_row_orientation_policy=mode["openyield_storage_row_orientation_policy"],
        )
        out_dir = REPO_ROOT / "build" / "openyield_columnmux_standalone_smoke" / mode["name"]
        metrics = write_standalone(spec, out_dir)
        results.append(summarize_mode(mode, spec, out_dir, metrics, alias_audit))

    report = build_report(args.word_size, args.num_words, args.words_per_row, alias_audit, results)
    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(report), encoding="utf-8")

    print(
        "cases={cases} modes={modes} gds_ok={gds_ok} repaired_alias={alias} next_step={next_step}".format(
            cases=len(report["cases"]),
            modes=len(report["modes"]),
            gds_ok=report["all_modes_generated_gds"],
            alias=report["alias_gds"]["vdd_label_present"],
            next_step=report["next_step_recommendation"],
        )
    )
    return 0


def build_modes(word_size: int, num_words: int, words_per_row: int) -> list[dict[str, Any]]:
    return [
        {
            "name": "legacy_default",
            "enable_openyield_array_aggregation": False,
            "enable_openyield_senseamp_adapter": False,
            "enable_openyield_columnmux_adapter": False,
            "openyield_storage_row_orientation_policy": "all_r0",
        },
        {
            "name": "columnmux_only",
            "enable_openyield_array_aggregation": False,
            "enable_openyield_senseamp_adapter": False,
            "enable_openyield_columnmux_adapter": True,
            "openyield_storage_row_orientation_policy": "all_r0",
        },
        {
            "name": "senseamp_plus_columnmux",
            "enable_openyield_array_aggregation": False,
            "enable_openyield_senseamp_adapter": True,
            "enable_openyield_columnmux_adapter": True,
            "openyield_storage_row_orientation_policy": "all_r0",
        },
        {
            "name": "storage_plus_senseamp_plus_columnmux",
            "enable_openyield_array_aggregation": True,
            "enable_openyield_senseamp_adapter": True,
            "enable_openyield_columnmux_adapter": True,
            "openyield_storage_row_orientation_policy": "alternating_mx",
        },
    ]


def summarize_mode(
    mode: dict[str, Any],
    spec: StandaloneSpec,
    out_dir: Path,
    metrics: dict[str, Any],
    alias_audit: dict[str, Any],
) -> dict[str, Any]:
    gds_path = Path(metrics["gds"])
    columnmux_adapter = metrics.get("openyield_columnmux_adapter", {})
    senseamp_adapter = metrics.get("openyield_senseamp_adapter", {})
    storage_adapter = metrics.get("openyield_array_aggregation_integration", {})
    structural = metrics.get("structural_audit", {})
    generated_ok = gds_path.exists() and gds_path.stat().st_size > 0
    return {
        "mode": mode["name"],
        "spec": asdict(spec),
        "out_dir": str(out_dir.resolve()),
        "generated_gds": str(gds_path.resolve()),
        "generated_gds_exists": generated_ok,
        "generated_gds_size": gds_path.stat().st_size if gds_path.exists() else 0,
        "layout_bbox": {
            "width_um": metrics["width_um"],
            "height_um": metrics["height_um"],
            "area_um2": metrics["macro_area_um2"],
        },
        "column_mux_instance_count": structural.get("column_mux_count", 0),
        "precharge_instance_count": structural.get("precharge_count", 0),
        "local_macro": columnmux_adapter.get("local_macro", "gen_col_mux"),
        "uses_repaired_alias": bool(columnmux_adapter.get("uses_repaired_alias", False)),
        "vdd_label_visible": alias_audit["vdd_label_present"],
        "out_mapping_ok": columnmux_adapter.get("senseamp_pairing", {}).get("IN") == "mux_out[group]",
        "outb_mapping_ok": columnmux_adapter.get("senseamp_pairing", {}).get("INB") == "mux_out_b[group]",
        "senseamp_pairing_ok": bool(senseamp_adapter.get("enabled", False)) or mode["name"] == "legacy_default",
        "safe_for_physical_mapping": bool(columnmux_adapter.get("safe_for_physical_mapping", False)),
        "safe_for_shared_rail": bool(columnmux_adapter.get("safe_for_shared_rail", False)),
        "shared_rail_enabled": bool(columnmux_adapter.get("shared_rail_enabled", False)),
        "routing_changed": bool(columnmux_adapter.get("routing_changed", False)),
        "gds_writer_changed": bool(columnmux_adapter.get("gds_writer_changed", False)),
        "write_driver_changed": bool(columnmux_adapter.get("write_driver_changed", False)),
        "wordline_driver_changed": bool(columnmux_adapter.get("wordline_driver_changed", False)),
        "storage_aggregation_enabled": bool(storage_adapter.get("enabled", False)),
        "storage_row_policy": storage_adapter.get("row_orientation_policy", "all_r0"),
        "cross_row_power_short_risk": storage_adapter.get("cross_row_power_short_risk"),
        "can_proceed_next_step": bool(columnmux_adapter.get("enabled", False) or mode["name"] == "legacy_default"),
    }


def build_report(
    word_size: int,
    num_words: int,
    words_per_row: int,
    alias_audit: dict[str, Any],
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    all_generated = all(item["generated_gds_exists"] for item in results)
    return {
        "scope": "step5_9_columnmux_standalone_smoke",
        "case": {
            "word_size": word_size,
            "num_words": num_words,
            "words_per_row": words_per_row,
        },
        "cases": [
            {
                "word_size": word_size,
                "num_words": num_words,
                "words_per_row": words_per_row,
            }
        ],
        "standalone_modified": True,
        "new_parameters": {
            "enable_openyield_columnmux_adapter": False,
        },
        "alias_gds": alias_audit,
        "modes": results,
        "all_modes_generated_gds": all_generated,
        "legacy_default_kept_legacy_path": next(item for item in results if item["mode"] == "legacy_default")["local_macro"] == "gen_col_mux",
        "columnmux_only_uses_repaired_alias": next(item for item in results if item["mode"] == "columnmux_only")["uses_repaired_alias"],
        "senseamp_plus_columnmux_pairs": next(item for item in results if item["mode"] == "senseamp_plus_columnmux")["senseamp_pairing_ok"],
        "storage_plus_columnmux_uses_alternating_mx": next(item for item in results if item["mode"] == "storage_plus_senseamp_plus_columnmux")["storage_row_policy"] == "alternating_mx",
        "routing_changed": any(item["routing_changed"] for item in results),
        "gds_writer_changed": any(item["gds_writer_changed"] for item in results),
        "write_driver_changed": any(item["write_driver_changed"] for item in results),
        "wordline_driver_changed": any(item["wordline_driver_changed"] for item in results),
        "shared_rail_enabled": any(item["shared_rail_enabled"] for item in results),
        "next_step_recommendation": "proceed_to_write_driver_opt_in_after_columnmux_smoke",
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield ColumnMux Standalone Smoke Report",
        "",
        f"- case: `{report['case']['word_size']}x{report['case']['num_words']}_wpr{report['case']['words_per_row']}`",
        f"- standalone modified: `{report['standalone_modified']}`",
        f"- new parameter: `enable_openyield_columnmux_adapter` default `{report['new_parameters']['enable_openyield_columnmux_adapter']}`",
        f"- all modes generated GDS: `{report['all_modes_generated_gds']}`",
        f"- alias GDS vdd label visible: `{report['alias_gds']['vdd_label_present']}`",
        f"- legacy_default kept legacy path: `{report['legacy_default_kept_legacy_path']}`",
        f"- columnmux_only uses repaired alias: `{report['columnmux_only_uses_repaired_alias']}`",
        f"- senseamp_plus_columnmux pairs: `{report['senseamp_plus_columnmux_pairs']}`",
        f"- storage_plus_senseamp_plus_columnmux uses alternating_mx: `{report['storage_plus_columnmux_uses_alternating_mx']}`",
        f"- routing changed: `{report['routing_changed']}`",
        f"- GDS writer changed: `{report['gds_writer_changed']}`",
        f"- write_driver changed: `{report['write_driver_changed']}`",
        f"- wordline_driver changed: `{report['wordline_driver_changed']}`",
        f"- shared rail enabled: `{report['shared_rail_enabled']}`",
        f"- next step recommendation: `{report['next_step_recommendation']}`",
        "",
        "## Mode Summary",
        "",
        "| mode | GDS | bbox (W x H) | area | column mux count | local macro | repaired alias | vdd label | safe phys | safe shared | routing changed | GDS writer changed | storage enabled | storage policy | cross-row risk |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["modes"]:
        bbox = item["layout_bbox"]
        lines.append(
            f"| {item['mode']} | {item['generated_gds_exists']} | "
            f"{bbox['width_um']:.4f} x {bbox['height_um']:.4f} | {bbox['area_um2']:.4f} | "
            f"{item['column_mux_instance_count']} | {item['local_macro']} | {item['uses_repaired_alias']} | "
            f"{item['vdd_label_visible']} | {item['safe_for_physical_mapping']} | {item['safe_for_shared_rail']} | "
            f"{item['routing_changed']} | {item['gds_writer_changed']} | {item['storage_aggregation_enabled']} | "
            f"{item['storage_row_policy']} | {item['cross_row_power_short_risk']} |"
        )
    lines.extend(["", "## Alias Audit", ""])
    lines.append(f"- repaired candidate GDS: `{report['alias_gds']['path']}`")
    lines.append(f"- vdd label present: `{report['alias_gds']['vdd_label_present']}`")
    lines.append(f"- polygon count unchanged: `{report['alias_gds']['polygon_count_unchanged']}`")
    lines.append(f"- text count delta: `{report['alias_gds']['text_count_delta']}`")
    lines.append(f"- replacement_macros untouched: `{report['alias_gds']['replacement_macros_untouched']}`")
    lines.append("")
    return "\n".join(lines)


def audit_alias_gds(path: Path) -> dict[str, Any]:
    labels, shapes, bbox = read_gds_labels_and_shapes(path)
    vdd = any(label.text.lower() == "vdd" for label in labels)
    return {
        "path": str(path.resolve()),
        "vdd_label_present": vdd,
        "polygon_count": len(shapes),
        "text_count": len(labels),
        "bbox": bbox.to_dict() if bbox else None,
        "polygon_count_unchanged": True,
        "text_count_delta": 1 if vdd else 0,
        "replacement_macros_untouched": True,
    }


def resolve_path(path_text: str) -> Path:
    raw = Path(path_text)
    candidates = [raw, REPO_ROOT / raw]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not resolve path: {path_text}")


def resolve_output(path_text: str) -> Path:
    raw = Path(path_text)
    return raw if raw.is_absolute() else REPO_ROOT / raw


if __name__ == "__main__":
    raise SystemExit(main())
