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

from sram_layoutgen.standalone import StandaloneSpec, write_standalone  # noqa: E402


DEFAULT_WORD_SIZE = 4
DEFAULT_NUM_WORDS = 32
DEFAULT_WORDS_PER_ROW = 2


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-test the OpenYield write driver opt-in path inside standalone.")
    parser.add_argument("--word-size", type=int, default=DEFAULT_WORD_SIZE)
    parser.add_argument("--num-words", type=int, default=DEFAULT_NUM_WORDS)
    parser.add_argument("--words-per-row", type=int, default=DEFAULT_WORDS_PER_ROW)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    modes = build_modes()
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
            enable_openyield_writedriver_adapter=mode["enable_openyield_writedriver_adapter"],
            openyield_storage_row_orientation_policy=mode["openyield_storage_row_orientation_policy"],
        )
        out_dir = REPO_ROOT / "build" / "openyield_writedriver_standalone_smoke" / mode["name"]
        metrics = write_standalone(spec, out_dir)
        results.append(summarize_mode(mode, spec, out_dir, metrics))

    report = build_report(args.word_size, args.num_words, args.words_per_row, results)
    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(report), encoding="utf-8")

    print(
        "cases={cases} modes={modes} gds_ok={gds_ok} next_step={next_step}".format(
            cases=len(report["cases"]),
            modes=len(report["modes"]),
            gds_ok=report["all_modes_generated_gds"],
            next_step=report["next_step_recommendation"],
        )
    )
    return 0


def build_modes() -> list[dict[str, Any]]:
    return [
        {
            "name": "legacy_default",
            "enable_openyield_array_aggregation": False,
            "enable_openyield_senseamp_adapter": False,
            "enable_openyield_columnmux_adapter": False,
            "enable_openyield_writedriver_adapter": False,
            "openyield_storage_row_orientation_policy": "all_r0",
        },
        {
            "name": "writedriver_only",
            "enable_openyield_array_aggregation": False,
            "enable_openyield_senseamp_adapter": False,
            "enable_openyield_columnmux_adapter": False,
            "enable_openyield_writedriver_adapter": True,
            "openyield_storage_row_orientation_policy": "all_r0",
        },
        {
            "name": "read_path_plus_writedriver",
            "enable_openyield_array_aggregation": False,
            "enable_openyield_senseamp_adapter": True,
            "enable_openyield_columnmux_adapter": True,
            "enable_openyield_writedriver_adapter": True,
            "openyield_storage_row_orientation_policy": "all_r0",
        },
        {
            "name": "storage_plus_read_write_path",
            "enable_openyield_array_aggregation": True,
            "enable_openyield_senseamp_adapter": True,
            "enable_openyield_columnmux_adapter": True,
            "enable_openyield_writedriver_adapter": True,
            "openyield_storage_row_orientation_policy": "alternating_mx",
        },
    ]


def summarize_mode(
    mode: dict[str, Any],
    spec: StandaloneSpec,
    out_dir: Path,
    metrics: dict[str, Any],
) -> dict[str, Any]:
    gds_path = Path(metrics["gds"])
    storage = metrics.get("openyield_array_aggregation_integration", {})
    columnmux = metrics.get("openyield_columnmux_adapter", {})
    senseamp = metrics.get("openyield_senseamp_adapter", {})
    writedriver = metrics.get("openyield_writedriver_adapter", {})
    generated_ok = gds_path.exists() and gds_path.stat().st_size > 0
    write_driver_count = int(metrics.get("hardcell_instances", {}).get("write_driver", 0) or metrics.get("role_counts", {}).get("write_driver", 0))
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
        "storage_enabled": bool(storage.get("enabled", False)),
        "storage_policy": storage.get("row_orientation_policy", "all_r0"),
        "storage_cross_row_power_short_risk": storage.get("cross_row_power_short_risk"),
        "storage_pitch": storage.get("pitch", {}),
        "storage_instance_count": storage.get("instance_count", 0),
        "peripheral_instance_count": sum(
            int(metrics.get("role_counts", {}).get(role, 0) or 0)
            for role in ("sense_amp", "write_driver", "tri_gate", "control_logic", "row_decoder", "wordline_driver")
        ),
        "write_driver_instance_count": write_driver_count,
        "write_driver_local_macro": writedriver.get("local_macro", "write_driver"),
        "write_driver_power_status": writedriver.get("power_status", "unknown"),
        "write_driver_safe_for_physical_mapping": bool(writedriver.get("safe_for_physical_mapping", False)),
        "write_driver_safe_for_shared_rail": bool(writedriver.get("safe_for_shared_rail", False)),
        "write_driver_requires_netlist_rewrite": bool(writedriver.get("requires_netlist_rewrite", False)),
        "write_driver_placement_count": int(writedriver.get("placement_count", 0) or 0),
        "write_driver_mapping_ok": (not bool(writedriver.get("enabled", False))) or pin_mapping_ok(writedriver),
        "write_driver_routing_changed": bool(writedriver.get("routing_changed", False)),
        "write_driver_gds_writer_changed": bool(writedriver.get("gds_writer_changed", False)),
        "write_driver_shared_rail_enabled": bool(writedriver.get("shared_rail_enabled", False)),
        "senseamp_enabled": bool(senseamp.get("enabled", False)),
        "columnmux_enabled": bool(columnmux.get("enabled", False)),
        "routing_changed": bool(metrics.get("openyield_columnmux_adapter", {}).get("routing_changed", False) or writedriver.get("routing_changed", False)),
        "gds_writer_changed": bool(metrics.get("openyield_columnmux_adapter", {}).get("gds_writer_changed", False) or writedriver.get("gds_writer_changed", False)),
        "shared_rail_enabled": bool(metrics.get("openyield_columnmux_adapter", {}).get("shared_rail_enabled", False) or writedriver.get("shared_rail_enabled", False)),
        "legacy_default_kept_legacy_path": mode["name"] == "legacy_default",
        "writedriver_only_enabled": mode["name"] == "writedriver_only" and writedriver.get("enabled", False),
        "read_path_plus_writedriver_enabled": mode["name"] == "read_path_plus_writedriver" and writedriver.get("enabled", False),
        "storage_plus_read_write_path_uses_alternating_mx": mode["name"] == "storage_plus_read_write_path" and storage.get("row_orientation_policy") == "alternating_mx",
        "can_proceed_next_step": bool(writedriver.get("enabled", False)),
    }


def pin_mapping_ok(writedriver: dict[str, Any]) -> bool:
    adaptations = {str(item.get("openyield_pin") or ""): item for item in writedriver.get("pin_adaptations", [])}
    required_pairs = {
        "VDD": "vdd",
        "VSS": "gnd",
        "EN": "write_enable",
        "DIN": "din",
        "BL": "bl",
        "BLB": "br",
    }
    for pin, canonical in required_pairs.items():
        entry = adaptations.get(pin)
        if not entry:
            return False
        if str(entry.get("canonical_signal") or "") != canonical:
            return False
    return True


def build_report(
    word_size: int,
    num_words: int,
    words_per_row: int,
    results: list[dict[str, Any]],
) -> dict[str, Any]:
    all_generated = all(item["generated_gds_exists"] for item in results)
    storage_modes = [item for item in results if item["storage_enabled"]]
    return {
        "scope": "step5_11_writedriver_standalone_smoke",
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
            "enable_openyield_writedriver_adapter": False,
        },
        "modes": results,
        "all_modes_generated_gds": all_generated,
        "legacy_default_kept_legacy_path": next(item for item in results if item["mode"] == "legacy_default")["legacy_default_kept_legacy_path"],
        "writedriver_only_enabled": next(item for item in results if item["mode"] == "writedriver_only")["writedriver_only_enabled"],
        "read_path_plus_writedriver_enabled": next(item for item in results if item["mode"] == "read_path_plus_writedriver")["read_path_plus_writedriver_enabled"],
        "storage_plus_read_write_path_uses_alternating_mx": next(item for item in results if item["mode"] == "storage_plus_read_write_path")["storage_plus_read_write_path_uses_alternating_mx"],
        "write_driver_mapping_ok": all(item["write_driver_mapping_ok"] for item in results),
        "routing_changed": any(item["routing_changed"] for item in results),
        "gds_writer_changed": any(item["gds_writer_changed"] for item in results),
        "shared_rail_enabled": any(item["shared_rail_enabled"] for item in results),
        "storage_modes": [
            {
                "mode": item["mode"],
                "storage_enabled": item["storage_enabled"],
                "storage_policy": item["storage_policy"],
                "storage_cross_row_power_short_risk": item["storage_cross_row_power_short_risk"],
            }
            for item in storage_modes
        ],
        "next_step_recommendation": "proceed_to_write_driver_read_write_path_review",
    }


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield WriteDriver Standalone Smoke Report",
        "",
        f"- case: `{report['case']['word_size']}x{report['case']['num_words']}_wpr{report['case']['words_per_row']}`",
        f"- standalone modified: `{report['standalone_modified']}`",
        f"- new parameter: `enable_openyield_writedriver_adapter` default `{report['new_parameters']['enable_openyield_writedriver_adapter']}`",
        f"- all modes generated GDS: `{report['all_modes_generated_gds']}`",
        f"- legacy_default kept legacy path: `{report['legacy_default_kept_legacy_path']}`",
        f"- writedriver_only enabled: `{report['writedriver_only_enabled']}`",
        f"- read_path_plus_writedriver enabled: `{report['read_path_plus_writedriver_enabled']}`",
        f"- storage_plus_read_write_path uses alternating_mx: `{report['storage_plus_read_write_path_uses_alternating_mx']}`",
        f"- routing changed: `{report['routing_changed']}`",
        f"- GDS writer changed: `{report['gds_writer_changed']}`",
        f"- shared rail enabled: `{report['shared_rail_enabled']}`",
        f"- write_driver mapping ok: `{report['write_driver_mapping_ok']}`",
        f"- next step recommendation: `{report['next_step_recommendation']}`",
        "",
        "## Mode Summary",
        "",
        "| mode | GDS | bbox (W x H) | area | write_driver count | local macro | safe phys | safe shared | mapping ok | senseamp | columnmux | storage enabled | storage policy | routing changed | GDS writer changed |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["modes"]:
        bbox = item["layout_bbox"]
        lines.append(
            f"| {item['mode']} | {item['generated_gds_exists']} | "
            f"{bbox['width_um']:.4f} x {bbox['height_um']:.4f} | {bbox['area_um2']:.4f} | "
            f"{item['write_driver_instance_count']} | {item['write_driver_local_macro']} | "
            f"{item['write_driver_safe_for_physical_mapping']} | {item['write_driver_safe_for_shared_rail']} | "
            f"{item['write_driver_mapping_ok']} | {item['senseamp_enabled']} | {item['columnmux_enabled']} | "
            f"{item['storage_enabled']} | {item['storage_policy']} | "
            f"{item['routing_changed']} | {item['gds_writer_changed']} |"
        )
    lines.extend(["", "## Storage Modes", ""])
    for item in report["storage_modes"]:
        lines.append(
            f"- `{item['mode']}`: enabled=`{item['storage_enabled']}`, policy=`{item['storage_policy']}`, "
            f"cross_row_power_short_risk=`{item['storage_cross_row_power_short_risk']}`"
        )
    lines.append("")
    return "\n".join(lines)


def resolve_output(path_text: str) -> Path:
    raw = Path(path_text)
    return raw if raw.is_absolute() else REPO_ROOT / raw


if __name__ == "__main__":
    raise SystemExit(main())
