from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))

from sram_layoutgen.standalone import StandaloneSpec, write_standalone  # noqa: E402


DEFAULT_OUT_JSON = Path("docs/openyield_read_write_path_semantic_review_report.json")
DEFAULT_OUT_MD = Path("docs/openyield_read_write_path_semantic_review_report.md")


def main() -> int:
    parser = argparse.ArgumentParser(description="Review OpenYield read/write path semantics from standalone metadata.")
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
        "read_path_only": run_case(
            "read_path_only",
            StandaloneSpec(
                word_size=args.word_size,
                num_words=args.num_words,
                words_per_row=args.words_per_row,
                enable_openyield_senseamp_adapter=True,
                enable_openyield_columnmux_adapter=True,
            ),
        ),
        "write_path_only": run_case(
            "write_path_only",
            StandaloneSpec(
                word_size=args.word_size,
                num_words=args.num_words,
                words_per_row=args.words_per_row,
                enable_openyield_writedriver_adapter=True,
            ),
        ),
        "read_write_path": run_case(
            "read_write_path",
            StandaloneSpec(
                word_size=args.word_size,
                num_words=args.num_words,
                words_per_row=args.words_per_row,
                enable_openyield_senseamp_adapter=True,
                enable_openyield_columnmux_adapter=True,
                enable_openyield_writedriver_adapter=True,
            ),
        ),
        "storage_plus_read_write_path": run_case(
            "storage_plus_read_write_path",
            StandaloneSpec(
                word_size=args.word_size,
                num_words=args.num_words,
                words_per_row=args.words_per_row,
                enable_openyield_array_aggregation=True,
                openyield_storage_row_orientation_policy="alternating_mx",
                enable_openyield_senseamp_adapter=True,
                enable_openyield_columnmux_adapter=True,
                enable_openyield_writedriver_adapter=True,
            ),
        ),
    }

    report = build_report(args, cases)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(format_markdown(report), encoding="utf-8")
    print(
        "read_ok={read_ok} write_ok={write_ok} conflict={conflict} grouped_confirm={grouped} next={next_step}".format(
            read_ok=report["checks"]["read_path_semantics_ok"],
            write_ok=report["checks"]["write_path_semantics_ok"],
            conflict=report["checks"]["read_write_conflict_found"],
            grouped=report["checks"]["grouped_mapping_needs_confirmation"],
            next_step=report["next_step_recommendation"],
        )
    )
    return 0


def run_case(case_name: str, spec: StandaloneSpec) -> dict[str, Any]:
    out_dir = STANDALONE_ROOT / "build" / f"openyield_read_write_path_semantic_review_{case_name}"
    metrics = write_standalone(spec, out_dir)
    senseamp = dict(metrics.get("openyield_senseamp_adapter", {}))
    columnmux = dict(metrics.get("openyield_columnmux_adapter", {}))
    writedriver = dict(metrics.get("openyield_writedriver_adapter", {}))
    storage = dict(metrics.get("openyield_array_aggregation_integration", {}))
    role_counts = dict(metrics.get("role_counts", {}))
    read_map = build_read_path_mapping(columnmux.get("limited_placement_plan", {}), senseamp.get("plan", {}), senseamp)
    write_map = build_write_path_mapping(writedriver)
    return {
        "mode": case_name,
        "spec": {
            "word_size": spec.word_size,
            "num_words": spec.num_words,
            "words_per_row": spec.resolved_words_per_row(),
            "enable_openyield_array_aggregation": spec.enable_openyield_array_aggregation,
            "enable_openyield_senseamp_adapter": spec.enable_openyield_senseamp_adapter,
            "enable_openyield_columnmux_adapter": spec.enable_openyield_columnmux_adapter,
            "enable_openyield_writedriver_adapter": spec.enable_openyield_writedriver_adapter,
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
            "column_mux_count": role_counts.get("column_mux", 0),
            "sense_amp_count": role_counts.get("sense_amp", 0),
            "write_driver_count": role_counts.get("write_driver", 0),
            "storage_instance_count": storage.get("instance_count", 0),
            "peripheral_instance_count": sum(
                int(role_counts.get(role, 0) or 0)
                for role in ("sense_amp", "write_driver", "tri_gate", "control_logic", "row_decoder", "wordline_driver")
            ),
        },
        "read_path": read_map,
        "write_path": write_map,
        "senseamp_adapter": senseamp,
        "columnmux_adapter": columnmux,
        "writedriver_adapter": writedriver,
        "storage_aggregation": storage,
        "routing_changed": bool(
            metrics.get("openyield_columnmux_adapter", {}).get("routing_changed", False)
            or metrics.get("openyield_senseamp_adapter", {}).get("routing_changed", False)
            or metrics.get("openyield_writedriver_adapter", {}).get("routing_changed", False)
        ),
        "gds_writer_changed": bool(
            metrics.get("openyield_columnmux_adapter", {}).get("gds_writer_changed", False)
            or metrics.get("openyield_senseamp_adapter", {}).get("gds_writer_changed", False)
            or metrics.get("openyield_writedriver_adapter", {}).get("gds_writer_changed", False)
        ),
        "shared_rail_enabled": bool(
            metrics.get("openyield_columnmux_adapter", {}).get("shared_rail_enabled", False)
            or metrics.get("openyield_writedriver_adapter", {}).get("shared_rail_enabled", False)
        ),
    }


def build_read_path_mapping(
    columnmux_plan: dict[str, Any],
    senseamp_plan: dict[str, Any],
    senseamp_meta: dict[str, Any],
) -> dict[str, Any]:
    columnmux_placements = list(columnmux_plan.get("placements", []))
    senseamp_placements = list(senseamp_plan.get("placements", []))
    out_to_mux_out = all(
        placement.get("nets", {}).get("out") == f"mux_out[{placement.get('group')}]"
        for placement in columnmux_placements
    ) and bool(columnmux_placements)
    outb_to_mux_out_b = all(
        placement.get("nets", {}).get("outb") == f"mux_out_b[{placement.get('group')}]"
        for placement in columnmux_placements
    ) and bool(columnmux_placements)
    in_to_mux_out_group = all(
        placement.get("nets", {}).get("bl") == f"mux_out[{placement.get('col')}]"
        for placement in senseamp_placements
    ) and bool(senseamp_placements)
    inb_to_mux_out_b_group = all(
        placement.get("nets", {}).get("br") == f"mux_out_b[{placement.get('col')}]"
        for placement in senseamp_placements
    ) and bool(senseamp_placements)
    q_to_dout = all(
        placement.get("nets", {}).get("dout") == f"dout[{placement.get('col')}]"
        for placement in senseamp_placements
    ) and bool(senseamp_placements)
    qb_dropped = bool(senseamp_meta.get("dropped_pins", {}).get("QB") == "dropped_complementary_output")
    fake_dout_b = bool(senseamp_meta.get("generated_fake_dout_b", False))
    read_path_semantics_ok = bool(
        out_to_mux_out
        and outb_to_mux_out_b
        and in_to_mux_out_group
        and inb_to_mux_out_b_group
        and q_to_dout
        and qb_dropped
        and not fake_dout_b
        and not bool(senseamp_meta.get("routing_changed", False))
        and not bool(senseamp_meta.get("gds_writer_changed", False))
    )
    return {
        "columnmux_out_to_mux_out": out_to_mux_out,
        "columnmux_outb_to_mux_out_b": outb_to_mux_out_b,
        "senseamp_in_to_mux_out_group": in_to_mux_out_group,
        "senseamp_inb_to_mux_out_b_group": inb_to_mux_out_b_group,
        "senseamp_q_to_dout_group": q_to_dout,
        "qb_dropped": qb_dropped,
        "fake_dout_b_generated": fake_dout_b,
        "read_path_semantics_ok": read_path_semantics_ok,
        "mapping_table": [
            {"openyield_pin": "OUT", "local_pin": "mux_out[group]", "canonical_signal": "mux_out"},
            {"openyield_pin": "OUTB", "local_pin": "mux_out_b[group]", "canonical_signal": "mux_out_b"},
            {"openyield_pin": "IN", "local_pin": "mux_out[group]", "canonical_signal": "mux_out"},
            {"openyield_pin": "INB", "local_pin": "mux_out_b[group]", "canonical_signal": "mux_out_b"},
            {"openyield_pin": "Q", "local_pin": "dout[group]", "canonical_signal": "dout"},
            {"openyield_pin": "QB", "local_pin": "-", "canonical_signal": "dropped_complementary_output"},
        ],
    }


def build_write_path_mapping(writedriver: dict[str, Any]) -> dict[str, Any]:
    pin_map = {
        str(item.get("openyield_pin") or ""): item
        for item in writedriver.get("pin_adaptations", [])
    }
    din_ok = str(pin_map.get("DIN", {}).get("canonical_signal") or "") == "din"
    en_ok = str(pin_map.get("EN", {}).get("canonical_signal") or "") == "write_enable"
    bl_ok = str(pin_map.get("BL", {}).get("canonical_signal") or "") == "bl"
    blb_ok = str(pin_map.get("BLB", {}).get("canonical_signal") or "") == "br"
    uses_columnmux = any(
        str(item.get("canonical_signal") or "") in {"mux_out", "mux_out_b"}
        for item in writedriver.get("pin_adaptations", [])
    )
    write_path_semantics_ok = bool(
        din_ok
        and en_ok
        and bl_ok
        and blb_ok
        and not uses_columnmux
        and not bool(writedriver.get("routing_changed", False))
        and not bool(writedriver.get("gds_writer_changed", False))
        and not bool(writedriver.get("shared_rail_enabled", False))
    )
    grouped_mapping_needs_confirmation = bool(writedriver.get("placement_count", 0) > 0) and bool(
        writedriver.get("notes", [])
    )
    return {
        "din_to_din": din_ok,
        "en_to_write_enable": en_ok,
        "bl_to_bl": bl_ok,
        "blb_to_br": blb_ok,
        "uses_columnmux_nets": uses_columnmux,
        "write_path_semantics_ok": write_path_semantics_ok,
        "grouped_mapping_needs_confirmation": grouped_mapping_needs_confirmation,
        "mapping_table": [
            {"openyield_pin": "DIN", "local_pin": "din", "canonical_signal": "din"},
            {"openyield_pin": "EN", "local_pin": "write_enable", "canonical_signal": "write_enable"},
            {"openyield_pin": "BL", "local_pin": "bl", "canonical_signal": "bl"},
            {"openyield_pin": "BLB", "local_pin": "br", "canonical_signal": "br"},
        ],
    }


def build_report(args: argparse.Namespace, cases: dict[str, dict[str, Any]]) -> dict[str, Any]:
    legacy = cases["legacy_default"]
    read_only = cases["read_path_only"]
    write_only = cases["write_path_only"]
    read_write = cases["read_write_path"]
    storage = cases["storage_plus_read_write_path"]

    checks = {
        "legacy_default_preserved": (
            legacy["outputs"]["generated_gds"] is True
            and legacy["spec"]["enable_openyield_senseamp_adapter"] is False
            and legacy["spec"]["enable_openyield_columnmux_adapter"] is False
            and legacy["spec"]["enable_openyield_writedriver_adapter"] is False
            and legacy["spec"]["enable_openyield_array_aggregation"] is False
        ),
        "read_path_semantics_ok": all(
            case["read_path"]["read_path_semantics_ok"]
            for case in (read_only, read_write, storage)
        ),
        "write_path_semantics_ok": all(
            case["write_path"]["write_path_semantics_ok"]
            for case in (write_only, read_write, storage)
        ),
        "read_write_conflict_found": any(conflict_detected(case) for case in (read_only, write_only, read_write, storage)),
        "grouped_mapping_needs_confirmation": bool(storage["spec"]["words_per_row"] > 1),
        "can_continue_to_wordline_driver": not any(conflict_detected(case) for case in (read_only, write_only, read_write, storage)),
    }

    summary = {
        "generated_fake_dout_b": any(case["read_path"]["fake_dout_b_generated"] for case in cases.values()),
        "routing_changed": any(case["routing_changed"] for case in cases.values()),
        "gds_writer_changed": any(case["gds_writer_changed"] for case in cases.values()),
        "shared_rail_enabled": any(case["shared_rail_enabled"] for case in cases.values()),
        "read_path_enabled_modes": [
            name for name, case in cases.items()
            if case["spec"]["enable_openyield_senseamp_adapter"] or case["spec"]["enable_openyield_columnmux_adapter"]
        ],
        "write_path_enabled_modes": [
            name for name, case in cases.items()
            if case["spec"]["enable_openyield_writedriver_adapter"]
        ],
        "storage_enabled_modes": [
            name for name, case in cases.items()
            if case["spec"]["enable_openyield_array_aggregation"]
        ],
    }

    return {
        "scope": "step5_12_read_write_path_semantic_review",
        "standalone_modified": False,
        "new_script": "scripts/openyield_read_write_path_semantic_review.py",
        "new_parameters": {},
        "test_case": {
            "word_size": args.word_size,
            "num_words": args.num_words,
            "words_per_row": args.words_per_row,
        },
        "cases": cases,
        "checks": checks,
        "summary": summary,
        "read_path_mapping_table": read_only["read_path"]["mapping_table"],
        "write_path_mapping_table": write_only["write_path"]["mapping_table"],
        "read_path_semantics_ok": checks["read_path_semantics_ok"],
        "write_path_semantics_ok": checks["write_path_semantics_ok"],
        "read_write_conflict_found": checks["read_write_conflict_found"],
        "grouped_mapping_needs_confirmation": checks["grouped_mapping_needs_confirmation"],
        "can_continue_to_wordline_driver": checks["can_continue_to_wordline_driver"],
        "next_step_recommendation": "proceed_to_wordline_driver_only_if_no_conflicts_remain",
        "next_step_notes": [
            "QB remains observation-only; do not force dout_b into the local sense_amp path.",
            "Write driver semantics stay on bl/br and should not be cross-wired to mux_out/mux_out_b.",
            "Grouped mapping is still metadata-level until layout-level fanout is explicitly proven.",
        ],
    }


def conflict_detected(case: dict[str, Any]) -> bool:
    read = case["read_path"]
    write = case["write_path"]
    if case["spec"]["enable_openyield_senseamp_adapter"] or case["spec"]["enable_openyield_columnmux_adapter"]:
        if read["fake_dout_b_generated"]:
            return True
        if not read["read_path_semantics_ok"]:
            return True
        if read["columnmux_out_to_mux_out"] is False or read["columnmux_outb_to_mux_out_b"] is False:
            return True
    if case["spec"]["enable_openyield_writedriver_adapter"]:
        if not write["write_path_semantics_ok"]:
            return True
        if write["uses_columnmux_nets"]:
            return True
    return False


def format_markdown(report: dict[str, Any]) -> str:
    checks = report["checks"]
    summary = report["summary"]
    lines = [
        "# OpenYield Read/Write Path Semantic Review",
        "",
        "This is a metadata-only semantic review. It does not modify routing, GDS writer, placement, or OpenYield sources.",
        "",
        "## Summary",
        "",
        f"- standalone.py modified in this step: `{report['standalone_modified']}`",
        f"- new script: `{report['new_script']}`",
        f"- legacy_default preserved: `{checks['legacy_default_preserved']}`",
        f"- read path semantics ok: `{checks['read_path_semantics_ok']}`",
        f"- write path semantics ok: `{checks['write_path_semantics_ok']}`",
        f"- read/write conflict found: `{checks['read_write_conflict_found']}`",
        f"- grouped mapping needs confirmation: `{checks['grouped_mapping_needs_confirmation']}`",
        f"- can continue to wordline driver: `{checks['can_continue_to_wordline_driver']}`",
        f"- generated fake dout_b: `{summary['generated_fake_dout_b']}`",
        f"- routing changed: `{summary['routing_changed']}`",
        f"- GDS writer changed: `{summary['gds_writer_changed']}`",
        f"- shared rail enabled: `{summary['shared_rail_enabled']}`",
        "",
        "## Cases",
        "",
        table(
            [
                "case",
                "gds",
                "senseamp",
                "columnmux",
                "writedriver",
                "storage",
                "storage policy",
                "cmux count",
                "sa count",
                "wd count",
                "storage inst",
                "read ok",
                "write ok",
                "conflict",
                "grouped confirm",
                "gds path",
            ],
            [
                [
                    name,
                    case["outputs"]["generated_gds"],
                    case["spec"]["enable_openyield_senseamp_adapter"],
                    case["spec"]["enable_openyield_columnmux_adapter"],
                    case["spec"]["enable_openyield_writedriver_adapter"],
                    case["spec"]["enable_openyield_array_aggregation"],
                    case["spec"]["openyield_storage_row_orientation_policy"],
                    case["metrics"]["column_mux_count"],
                    case["metrics"]["sense_amp_count"],
                    case["metrics"]["write_driver_count"],
                    case["metrics"]["storage_instance_count"],
                    case["read_path"]["read_path_semantics_ok"],
                    case["write_path"]["write_path_semantics_ok"],
                    conflict_detected(case),
                    case["write_path"]["grouped_mapping_needs_confirmation"],
                    case["outputs"]["gds"],
                ]
                for name, case in report["cases"].items()
            ],
        ),
        "",
        "## Read Path Mapping",
        "",
        table(
            ["OpenYield pin", "Local pin", "Canonical signal"],
            [[item["openyield_pin"], item["local_pin"], item["canonical_signal"]] for item in report["read_path_mapping_table"]],
        ),
        "",
        "## Write Path Mapping",
        "",
        table(
            ["OpenYield pin", "Local pin", "Canonical signal"],
            [[item["openyield_pin"], item["local_pin"], item["canonical_signal"]] for item in report["write_path_mapping_table"]],
        ),
        "",
        "## Notes",
        "",
    ]
    for note in report["next_step_notes"]:
        lines.append(f"- {note}")
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
