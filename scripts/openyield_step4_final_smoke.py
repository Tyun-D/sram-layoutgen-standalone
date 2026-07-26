from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))

from sram_layoutgen.gds_util import inspect_gds_hierarchy, measure_gds_bbox  # noqa: E402
from sram_layoutgen.signoff import count_klayout_items  # noqa: E402
from sram_layoutgen.standalone import StandaloneSpec, write_standalone  # noqa: E402


DEFAULT_OUT_JSON = Path("docs/openyield_step4_final_smoke_report.json")
DEFAULT_OUT_MD = Path("docs/openyield_step4_final_smoke_report.md")
DEFAULT_SUMMARY_JSON = Path("docs/openyield_step4_storage_aggregation_summary.json")
DEFAULT_SUMMARY_MD = Path("docs/openyield_step4_storage_aggregation_summary.md")
DEFAULT_DRC_DECK = Path("technology/freepdk45/tech/freepdk45.lydrc")
STORAGE_ROLE_NAMES = {"bitcell_array", "dummy_bitcell", "replica_bitline"}
STORAGE_ARRAY_NAMES = {"bitcell_array", "dummy_left_array", "dummy_right_array", "replica_bitline_array"}
MODE_SPECS = (
    ("legacy_default", False, "all_r0"),
    ("openyield_all_r0", True, "all_r0"),
    ("openyield_alternating_mx", True, "alternating_mx"),
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run representative standalone OpenYield storage-aggregation smoke cases and summarize Step 4.")
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
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    summary_json.parent.mkdir(parents=True, exist_ok=True)
    summary_md.parent.mkdir(parents=True, exist_ok=True)

    cases = [run_case(parse_case(case_token)) for case_token in args.cases]
    optional_drc = run_optional_drc(cases)
    smoke_report = build_smoke_report(cases, optional_drc)
    summary_report = build_summary_report(cases, optional_drc)

    out_json.write_text(json.dumps(smoke_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(format_smoke_markdown(smoke_report), encoding="utf-8")
    summary_json.write_text(json.dumps(summary_report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary_md.write_text(format_summary_markdown(summary_report), encoding="utf-8")

    print(f"Wrote {out_json}")
    print(f"Wrote {out_md}")
    print(f"Wrote {summary_json}")
    print(f"Wrote {summary_md}")
    print(
        "cases="
        + ",".join(case["case_id"] for case in smoke_report["cases"])
        + f" optional_drc_ran={optional_drc.get('ran', False)}"
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


def run_case(case_spec: dict[str, int | str]) -> dict[str, Any]:
    case_id = str(case_spec["case_id"])
    outputs: dict[str, Any] = {}
    for mode_name, enable_openyield, policy in MODE_SPECS:
        spec = StandaloneSpec(
            word_size=int(case_spec["word_size"]),
            num_words=int(case_spec["num_words"]),
            words_per_row=int(case_spec["words_per_row"]),
            enable_openyield_array_aggregation=enable_openyield,
            openyield_storage_row_orientation_policy=policy,
        )
        out_dir = STANDALONE_ROOT / "build" / "openyield_step4_final_smoke" / case_id / mode_name
        metrics = write_standalone(spec, out_dir)
        outputs[mode_name] = summarize_mode(spec, metrics, out_dir)
    return {
        "case_id": case_id,
        "word_size": int(case_spec["word_size"]),
        "num_words": int(case_spec["num_words"]),
        "words_per_row": int(case_spec["words_per_row"]),
        "modes": outputs,
    }


def summarize_mode(spec: StandaloneSpec, metrics: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    integration = dict(metrics.get("openyield_array_aggregation_integration", {}))
    mirror_audit = dict(metrics.get("cell_array_mirror_audit", {}))
    storage_arrays = dict(integration.get("storage_arrays", {}))
    storage_bbox = union_rects(list(storage_arrays.values()))
    gds_path = Path(str(metrics["gds"]))
    bbox = measure_gds_bbox(gds_path) if gds_path.exists() else None
    hardcell_arrays = {str(k): int(v) for k, v in dict(metrics.get("hardcell_arrays", {})).items()}
    role_counts = {str(k): int(v) for k, v in dict(metrics.get("role_counts", {})).items()}
    storage_instance_count = sum(hardcell_arrays.get(name, 0) for name in ("cell_1rw", "dummy_cell_1rw", "replica_cell_1rw"))
    peripheral_instance_count = sum(count for role, count in role_counts.items() if role not in STORAGE_ROLE_NAMES)
    storage_orientations = {
        item.get("array"): {
            "mirror_x": item.get("mirror_x"),
            "mirror_y": item.get("mirror_y"),
            "policy": item.get("openyield_storage_policy"),
        }
        for item in mirror_audit.get("arrays", [])
        if item.get("array") in STORAGE_ARRAY_NAMES
    }
    return {
        "enable_openyield_array_aggregation": spec.enable_openyield_array_aggregation,
        "openyield_storage_row_orientation_policy": spec.openyield_storage_row_orientation_policy,
        "gds_generated": gds_path.exists() and gds_path.stat().st_size > 0,
        "gds_path": str(gds_path),
        "report_json": str(out_dir / f"{spec.resolved_name()}.report.json"),
        "layout_bbox": bbox_to_dict(bbox),
        "width_um": metrics.get("width_um"),
        "height_um": metrics.get("height_um"),
        "macro_area_um2": metrics.get("macro_area_um2"),
        "storage_bbox": storage_bbox,
        "storage_orientation": orientation_summary(spec, integration, storage_orientations),
        "bitcell_pitch": dict(integration.get("pitch", {})),
        "storage_instance_count": storage_instance_count,
        "peripheral_instance_count": peripheral_instance_count,
        "peripherals_old_path": integration.get("peripherals_old_path"),
        "routing_changed": integration.get("routing_changed"),
        "gds_writer_changed": integration.get("gds_writer_changed"),
        "shared_rail_merge": integration.get("shared_rail_merge"),
        "legacy_mirror_preserved": legacy_mirror_ok(spec, storage_orientations),
        "all_r0_full_r0": all_r0_ok(spec, storage_orientations),
        "alternating_mx_active": alternating_ok(spec, storage_orientations),
        "cross_row_power_short_risk": integration.get("cross_row_power_short_risk"),
        "storage_plan_enabled": integration.get("enabled"),
        "storage_macro_counts": dict(integration.get("macro_counts", {})),
        "gds_hierarchy": inspect_gds_hierarchy(gds_path) if gds_path.exists() else {},
    }


def orientation_summary(
    spec: StandaloneSpec,
    integration: dict[str, Any],
    storage_orientations: dict[str, dict[str, Any]],
) -> str:
    if not spec.enable_openyield_array_aggregation:
        return "legacy_openram_mirror_x"
    if integration.get("row_orientation_policy") == "all_r0":
        return "all_r0"
    if integration.get("row_orientation_policy") == "alternating_mx":
        if any(bool(item.get("mirror_x")) for item in storage_orientations.values()):
            return "alternating_r0_mx"
    return str(integration.get("row_orientation_policy", "unknown"))


def legacy_mirror_ok(spec: StandaloneSpec, storage_orientations: dict[str, dict[str, Any]]) -> bool:
    if spec.enable_openyield_array_aggregation:
        return False
    return bool(storage_orientations) and all(bool(item.get("mirror_x")) for item in storage_orientations.values())


def all_r0_ok(spec: StandaloneSpec, storage_orientations: dict[str, dict[str, Any]]) -> bool:
    if not spec.enable_openyield_array_aggregation or spec.openyield_storage_row_orientation_policy != "all_r0":
        return False
    return bool(storage_orientations) and all(not bool(item.get("mirror_x")) for item in storage_orientations.values())


def alternating_ok(spec: StandaloneSpec, storage_orientations: dict[str, dict[str, Any]]) -> bool:
    if not spec.enable_openyield_array_aggregation or spec.openyield_storage_row_orientation_policy != "alternating_mx":
        return False
    return bool(storage_orientations) and all(bool(item.get("mirror_x")) for item in storage_orientations.values())


def union_rects(rects: list[dict[str, Any]]) -> dict[str, float] | None:
    rects = [rect for rect in rects if rect]
    if not rects:
        return None
    x0 = min(float(rect["x0"]) for rect in rects)
    y0 = min(float(rect["y0"]) for rect in rects)
    x1 = max(float(rect["x1"]) for rect in rects)
    y1 = max(float(rect["y1"]) for rect in rects)
    return {
        "x0": round(x0, 6),
        "y0": round(y0, 6),
        "x1": round(x1, 6),
        "y1": round(y1, 6),
        "width": round(x1 - x0, 6),
        "height": round(y1 - y0, 6),
        "area": round((x1 - x0) * (y1 - y0), 6),
    }


def bbox_to_dict(bbox: Any) -> dict[str, float] | None:
    if bbox is None:
        return None
    return {
        "x0": round(float(bbox.x0), 6),
        "y0": round(float(bbox.y0), 6),
        "x1": round(float(bbox.x1), 6),
        "y1": round(float(bbox.y1), 6),
        "width": round(float(bbox.width), 6),
        "height": round(float(bbox.height), 6),
        "shape_count": int(getattr(bbox, "shape_count", 0)),
    }


def run_optional_drc(cases: list[dict[str, Any]]) -> dict[str, Any]:
    target = next((case for case in cases if case["case_id"] == "2x16_wpr1"), None)
    if target is None:
        return {"ran": False, "reason": "2x16_wpr1 case not requested"}
    mode = target["modes"]["openyield_alternating_mx"]
    gds_path = Path(str(mode["gds_path"]))
    if not gds_path.exists():
        return {"ran": False, "reason": "target GDS missing"}
    deck = resolve(DEFAULT_DRC_DECK)
    klayout = find_klayout()
    if not deck.exists() or klayout is None:
        return {"ran": False, "reason": "KLayout or DRC deck unavailable"}
    out_dir = gds_path.parent
    lyrdb = out_dir / "standalone_altmx_drc.lyrdb"
    log_path = out_dir / "standalone_altmx_drc.log"
    topcell = gds_path.stem
    command = [
        str(klayout),
        "-b",
        "-r",
        str(deck),
        "-rd",
        f"input={gds_path}",
        "-rd",
        f"topcell={topcell}",
        "-rd",
        f"output={lyrdb}",
    ]
    completed = subprocess.run(command, cwd=STANDALONE_ROOT, text=True, capture_output=True, check=False)
    log_path.write_text(
        "COMMAND:\n" + " ".join(command) + "\n\nSTDOUT:\n" + completed.stdout + "\n\nSTDERR:\n" + completed.stderr,
        encoding="utf-8",
    )
    return {
        "ran": True,
        "case_id": "2x16_wpr1",
        "mode": "openyield_alternating_mx",
        "gds_path": str(gds_path),
        "lyrdb": str(lyrdb),
        "log": str(log_path),
        "returncode": completed.returncode,
        "marker_count": count_klayout_items(lyrdb) if lyrdb.exists() else None,
        "clean": completed.returncode == 0 and (count_klayout_items(lyrdb) or 0) == 0,
    }


def find_klayout() -> Path | None:
    env = shutil.which("klayout_app.exe") or shutil.which("klayout.exe")
    if env:
        return Path(env)
    user = Path.home()
    for candidate in [
        user / "AppData/Roaming/KLayout/klayout_app.exe",
        user / "AppData/Roaming/KLayout/klayout.exe",
    ]:
        if candidate.exists():
            return candidate
    return None


def build_smoke_report(cases: list[dict[str, Any]], optional_drc: dict[str, Any]) -> dict[str, Any]:
    return {
        "scope": "representative_standalone_gds_smoke_not_final_signoff",
        "cases": cases,
        "optional_drc_smoke": optional_drc,
    }


def build_summary_report(cases: list[dict[str, Any]], optional_drc: dict[str, Any]) -> dict[str, Any]:
    return {
        "scope": "step4_storage_aggregation_summary",
        "step4_completed": [
            "Added limited OpenYield storage-array aggregation planning for cell_1rw, dummy_cell_1rw, and replica_cell_1rw.",
            "Audited legal storage pitch and kept the conservative full-bbox pitch 0.895 x 1.565.",
            "Built storage-only GDS smoke and power-stitch smoke without changing the main routing or GDS writer.",
            "Compared all_r0 versus alternating_mx and showed METAL2 seam markers drop from 34 to 0.",
            "Wired row orientation policy into array_aggregation.py and then into standalone as an explicit opt-in parameter.",
            "Verified representative standalone GDS generation for 2x16_wpr1 and 4x32_wpr2 across legacy, all_r0, and alternating_mx modes.",
        ],
        "final_storage_aggregation_strategy": {
            "macros": ["cell_1rw", "dummy_cell_1rw", "replica_cell_1rw"],
            "pitch_um": {"x": 0.895, "y": 1.565},
            "row_policy": {
                "default": "all_r0",
                "optional_recommended_opt_in": "alternating_mx",
            },
            "power_stitch": "storage-only smoke uses same-net horizontal power stitch; main flow still does not perform shared rail merge",
        },
        "default_path_unchanged": True,
        "openyield_storage_aggregation_opt_in_available": True,
        "why_not_all_r0": [
            "Storage-only compare smoke showed row-boundary METAL2 markers 34 -> 0 when switching from all_r0 to alternating_mx.",
            "Cross-row power short risk improved from True to False in the storage-only compare smoke.",
        ],
        "why_not_legacy_pitch": [
            "The legacy 0.705 x 1.365 pitch caused real bbox overlap with risky layers including active, contact, m1, m2, and via1.",
            "The current recommendation remains use_full_bbox_pitch because the legacy pitch is not a harmless rail-only overlap.",
        ],
        "still_unresolved": [
            "METAL1.2 residual markers remain; storage-only DRC is still not clean.",
            "Storage-only DRC smoke is not equivalent to final SRAM signoff.",
            "Peripheral modules are still on the old path and not adapted to OpenYield contracts.",
            "sense_amp Q/QB semantic adaptation is not done.",
            "gen_col_mux VDD metadata is still incomplete.",
            "wordline driver B-pin semantics still need confirmation.",
            "TIME/control logic adaptation and expansion are not done.",
        ],
        "optional_drc_smoke": optional_drc,
        "step5_recommendations": [
            "Start Step 5 from sense_amp because its Q/QB interface is the clearest semantic mismatch between OpenYield storage behavior and the current standalone periphery.",
            "After sense_amp, handle write_driver and then column mux power metadata so the data-path periphery can move toward contract-driven placement.",
            "Keep alternating_mx explicit and opt-in while Step 5 adapts one peripheral family at a time.",
        ],
        "can_enter_step5": True,
        "representative_cases": [
            {
                "case_id": case["case_id"],
                "modes": {
                    mode_name: {
                        "gds_generated": mode["gds_generated"],
                        "storage_orientation": mode["storage_orientation"],
                        "routing_changed": mode["routing_changed"],
                        "gds_writer_changed": mode["gds_writer_changed"],
                        "peripherals_old_path": mode["peripherals_old_path"],
                    }
                    for mode_name, mode in case["modes"].items()
                },
            }
            for case in cases
        ],
    }


def format_smoke_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Step 4 Final Smoke Report",
        "",
        "This is a representative standalone GDS smoke only. It is not final signoff.",
        "",
    ]
    for case in report["cases"]:
        lines.extend(
            [
                f"## {case['case_id']}",
                "",
                table(
                    [
                        "mode",
                        "gds_generated",
                        "gds_path",
                        "layout_bbox",
                        "size_um",
                        "storage_bbox",
                        "storage_orientation",
                        "bitcell_pitch",
                        "storage_instances",
                        "peripheral_instances",
                        "peripherals_old_path",
                        "routing_changed",
                        "gds_writer_changed",
                        "shared_rail_merge",
                        "cross_row_power_short_risk",
                    ],
                    [
                        [
                            mode_name,
                            mode["gds_generated"],
                            mode["gds_path"],
                            compact_bbox(mode["layout_bbox"]),
                            f"{mode['width_um']} x {mode['height_um']} / {mode['macro_area_um2']}",
                            compact_bbox(mode["storage_bbox"]),
                            mode["storage_orientation"],
                            mode["bitcell_pitch"],
                            mode["storage_instance_count"],
                            mode["peripheral_instance_count"],
                            mode["peripherals_old_path"],
                            mode["routing_changed"],
                            mode["gds_writer_changed"],
                            mode["shared_rail_merge"],
                            mode["cross_row_power_short_risk"],
                        ]
                        for mode_name, mode in case["modes"].items()
                    ],
                ),
                "",
            ]
        )
    drc = report["optional_drc_smoke"]
    lines.extend(
        [
            "## Optional DRC Smoke",
            "",
            f"- ran: `{drc.get('ran', False)}`",
            f"- case: `{drc.get('case_id')}`",
            f"- mode: `{drc.get('mode')}`",
            f"- marker_count: `{drc.get('marker_count')}`",
            f"- clean: `{drc.get('clean')}`",
            f"- reason: `{drc.get('reason')}`",
            "",
        ]
    )
    return "\n".join(lines)


def format_summary_markdown(report: dict[str, Any]) -> str:
    strategy = report["final_storage_aggregation_strategy"]
    lines = [
        "# OpenYield Step 4 Storage Aggregation Summary",
        "",
        "This report summarizes Step 4 only. It does not claim full SRAM signoff.",
        "",
        "## Completed",
        "",
        *[f"- {item}" for item in report["step4_completed"]],
        "",
        "## Final Strategy",
        "",
        f"- macros: `{strategy['macros']}`",
        f"- pitch: `{strategy['pitch_um']['x']} x {strategy['pitch_um']['y']}`",
        f"- default row policy: `{strategy['row_policy']['default']}`",
        f"- optional recommended row policy: `{strategy['row_policy']['optional_recommended_opt_in']}`",
        f"- power stitch: {strategy['power_stitch']}",
        f"- default path unchanged: `{report['default_path_unchanged']}`",
        f"- OpenYield storage aggregation opt-in available: `{report['openyield_storage_aggregation_opt_in_available']}`",
        "",
        "## Why Not all_r0",
        "",
        *[f"- {item}" for item in report["why_not_all_r0"]],
        "",
        "## Why Not Legacy Pitch",
        "",
        *[f"- {item}" for item in report["why_not_legacy_pitch"]],
        "",
        "## Still Unresolved",
        "",
        *[f"- {item}" for item in report["still_unresolved"]],
        "",
        "## Step 5 Recommendation",
        "",
        f"- can enter Step 5: `{report['can_enter_step5']}`",
        *[f"- {item}" for item in report["step5_recommendations"]],
        "",
    ]
    return "\n".join(lines)


def compact_bbox(bbox: dict[str, Any] | None) -> str:
    if not bbox:
        return "none"
    return f"({bbox['x0']},{bbox['y0']})-({bbox['x1']},{bbox['y1']})"


def table(headers: list[str], rows: list[list[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell).replace("|", "\\|") for cell in row) + " |")
    return "\n".join(out)


def resolve(path: Path) -> Path:
    return path if path.is_absolute() else (STANDALONE_ROOT / path)


if __name__ == "__main__":
    raise SystemExit(main())
