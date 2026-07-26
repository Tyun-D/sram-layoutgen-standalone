from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
STANDALONE_ROOT = SCRIPT_DIR.parent
if str(STANDALONE_ROOT) not in sys.path:
    sys.path.insert(0, str(STANDALONE_ROOT))

from sram_layoutgen.gds_util import inspect_gds_hierarchy  # noqa: E402
from sram_layoutgen.signoff import count_klayout_items  # noqa: E402


DEFAULT_GDS = Path("build/openyield_storage_only_smoke_2x4_stitched/storage_only_2x4_stitched.gds")
DEFAULT_POWER_REPORT = Path("docs/openyield_storage_power_stitch_report.json")
DEFAULT_DRC_DECK = Path("technology/freepdk45/tech/freepdk45.lydrc")
DEFAULT_LYRDB = Path("build/openyield_storage_only_smoke_2x4_stitched/storage_only_2x4_stitched_drc.lyrdb")
DEFAULT_LOG = Path("build/openyield_storage_only_smoke_2x4_stitched/storage_only_2x4_stitched_drc.log")
DEFAULT_OUT_JSON = Path("docs/openyield_storage_only_drc_smoke_report.json")
DEFAULT_OUT_MD = Path("docs/openyield_storage_only_drc_smoke_report.md")

SPACING_RE = re.compile(r"space|spacing|notch|minimum width|min[ _-]?width|separation", re.IGNORECASE)
RED_GAP_RE = re.compile(r"active|poly|metal1|m1|implant|well|nwell|pwell", re.IGNORECASE)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tiny KLayout DRC smoke on the OpenYield storage-only stitched GDS.")
    parser.add_argument("--input-gds", type=Path, default=DEFAULT_GDS)
    parser.add_argument("--power-report", type=Path, default=DEFAULT_POWER_REPORT)
    parser.add_argument("--drc-deck", type=Path, default=DEFAULT_DRC_DECK)
    parser.add_argument("--lyrdb", type=Path, default=DEFAULT_LYRDB)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--out-json", type=Path, default=DEFAULT_OUT_JSON)
    parser.add_argument("--out-md", type=Path, default=DEFAULT_OUT_MD)
    parser.add_argument("--topcell")
    parser.add_argument("--klayout")
    args = parser.parse_args()

    report = build_report(args)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.out_md.write_text(format_markdown(report), encoding="utf-8")

    print(f"Wrote {args.out_json}")
    print(f"Wrote {args.out_md}")
    if report["drc"]["ran"]:
        print(
            "DRC ran: "
            f"violations={report['drc']['violation_count']} "
            f"clean={report['drc']['clean']}"
        )
    else:
        print("DRC did not run; see manual checklist in report.")
    return 0


def build_report(args: argparse.Namespace) -> dict[str, Any]:
    input_gds = args.input_gds.resolve()
    power_report_path = args.power_report.resolve()
    drc_deck = args.drc_deck.resolve()
    lyrdb = args.lyrdb.resolve()
    log_path = args.log.resolve()
    out_json = args.out_json.resolve()
    out_md = args.out_md.resolve()
    klayout = Path(args.klayout).resolve() if args.klayout else find_klayout()
    hierarchy = inspect_gds_hierarchy(input_gds) if input_gds.exists() else {}
    topcell = args.topcell or infer_topcell(hierarchy)
    power_report = load_json(power_report_path)

    drc_available = bool(drc_deck.exists() and klayout and Path(klayout).exists())
    run_info: dict[str, Any] = {
        "ran": False,
        "clean": False,
        "violation_count": None,
        "lyrdb": str(lyrdb),
        "log": str(log_path),
        "returncode": None,
        "command": None,
        "stdout_tail": "",
        "stderr_tail": "",
    }
    category_stats: dict[str, int] = {}
    markers: list[dict[str, Any]] = []
    if drc_available and input_gds.exists():
        lyrdb.parent.mkdir(parents=True, exist_ok=True)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        command = [
            str(klayout),
            "-b",
            "-r",
            str(drc_deck),
            "-rd",
            f"input={input_gds}",
            "-rd",
            f"topcell={topcell}",
            "-rd",
            f"output={lyrdb}",
        ]
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        log_path.write_text(
            "COMMAND:\n"
            + " ".join(command)
            + "\n\nSTDOUT:\n"
            + completed.stdout
            + "\n\nSTDERR:\n"
            + completed.stderr,
            encoding="utf-8",
        )
        run_info.update(
            {
                "ran": True,
                "returncode": completed.returncode,
                "command": command,
                "stdout_tail": tail(completed.stdout),
                "stderr_tail": tail(completed.stderr),
                "violation_count": count_klayout_items(lyrdb),
            }
        )
        category_stats, markers = parse_lyrdb(lyrdb)
        if run_info["violation_count"] is None:
            run_info["violation_count"] = len(markers)
        run_info["clean"] = completed.returncode == 0 and run_info["violation_count"] == 0

    power_stitches = power_report.get("power_stitches", {})
    geometry_checks = power_report.get("geometry_smoke_checks", {})
    marker_analysis = analyze_markers(markers, power_stitches)
    red_gap_stats = {
        category: count
        for category, count in sorted(category_stats.items())
        if SPACING_RE.search(category) and RED_GAP_RE.search(category)
    }
    power_stitch_violation_count = marker_analysis["power_stitch_related_violation_count"]
    red_gap_violation_count = sum(red_gap_stats.values())
    can_keep_stitch = (
        run_info["ran"]
        and power_stitch_violation_count == 0
        and bool(power_stitches.get("same_net_power_only"))
        and not bool(power_stitches.get("crosses_bl_br_wl"))
        and geometry_checks.get("no_vdd_gnd_cross_stitch") is True
        and geometry_checks.get("no_bl_br_wl_stitch") is True
    )
    can_enter_next_step = can_keep_stitch and run_info["clean"] and red_gap_violation_count == 0

    return {
        "scope": "storage_only_tiny_drc_smoke_not_full_sram_signoff",
        "input_gds": {
            "path": str(input_gds),
            "exists": input_gds.exists(),
            "size_bytes": input_gds.stat().st_size if input_gds.exists() else 0,
            "topcell": topcell,
            "hierarchy": hierarchy,
        },
        "drc_deck": {
            "path": str(drc_deck),
            "available": drc_deck.exists(),
        },
        "klayout": {
            "path": str(klayout) if klayout else None,
            "available": bool(klayout and Path(klayout).exists()),
        },
        "drc": run_info,
        "violation_type_stats": category_stats,
        "spacing_notch_min_width_stats": {
            category: count for category, count in sorted(category_stats.items()) if SPACING_RE.search(category)
        },
        "red_layer_gap_related_stats": red_gap_stats,
        "power_stitch_analysis": {
            "stitch_power_rails": power_report.get("stitch_power_rails"),
            "power_rail_layer": power_report.get("power_rail_layer"),
            "vdd_stitch_count": power_stitches.get("vdd_count", 0),
            "gnd_stitch_count": power_stitches.get("gnd_count", 0),
            "total_stitch_count": power_stitches.get("total_count", 0),
            "same_net_power_only": bool(power_stitches.get("same_net_power_only")),
            "crosses_bl_br_wl": bool(power_stitches.get("crosses_bl_br_wl")),
            "side_power_trunk_added": power_report.get("side_power_trunk_added"),
            **marker_analysis,
        },
        "connectivity_smoke": {
            "vdd_gnd_short_risk": "not_detected_by_stitch_geometry; KLayout DRC is not LVS",
            "bl_br_wl_misconnect": bool(power_stitches.get("crosses_bl_br_wl")),
            "source": "storage power stitch report geometry checks plus KLayout DRC marker overlap",
        },
        "findings": {
            "drc_deck_available": drc_deck.exists(),
            "drc_ran": run_info["ran"],
            "violation_count": run_info["violation_count"],
            "power_stitch_related_violation": power_stitch_violation_count > 0,
            "red_layer_gap_related_violation": red_gap_violation_count > 0,
            "vdd_gnd_short_observed": False
            if geometry_checks.get("no_vdd_gnd_cross_stitch") is True
            else "unknown_requires_lvs_or_net_trace",
            "bl_br_wl_bridge_observed": bool(power_stitches.get("crosses_bl_br_wl")),
            "recommend_keep_current_power_stitch": can_keep_stitch,
            "can_enter_next_step": can_enter_next_step,
            "next_step_blocker": None
            if can_enter_next_step
            else "tiny DRC has spacing markers outside the power stitch bridges; inspect M1/M2 cell-internal or abutment gaps before expanding aggregation",
        },
        "manual_klayout_checklist": manual_checklist(input_gds, lyrdb),
        "outputs": {
            "json": str(out_json),
            "md": str(out_md),
            "lyrdb": str(lyrdb),
            "log": str(log_path),
        },
        "notes": [
            "This is a tiny storage-only DRC smoke; it is not full SRAM signoff.",
            "KLayout DRC reports geometric rule markers, not full net-aware LVS connectivity.",
            "Power-stitch connectivity conclusions are limited to same-net bridge construction and marker overlap.",
        ],
    }


def find_klayout() -> Path | None:
    env = os.environ.get("KLAYOUT_EXE")
    candidates = []
    if env:
        candidates.append(Path(env))
    for name in ("klayout_app.exe", "klayout.exe", "klayout_vo_app.exe"):
        found = shutil.which(name)
        if found:
            candidates.append(Path(found))
    user = Path.home()
    candidates.extend(
        [
            user / "AppData/Roaming/KLayout/klayout_app.exe",
            user / "AppData/Roaming/KLayout/klayout.exe",
            user / "AppData/Roaming/KLayout/klayout_vo_app.exe",
        ]
    )
    for candidate in candidates:
        if candidate.exists() and candidate.name != "klayout-uninstall.exe":
            return candidate
    return None


def infer_topcell(hierarchy: dict[str, Any]) -> str:
    structures = list(hierarchy.get("structures", []))
    referenced = set(hierarchy.get("reference_counts", {}).keys())
    unreferenced = [name for name in structures if name not in referenced]
    if unreferenced:
        return str(unreferenced[-1])
    if structures:
        return str(structures[-1])
    return "openyield_storage_only_2x4"


def parse_lyrdb(path: Path) -> tuple[dict[str, int], list[dict[str, Any]]]:
    if not path.exists():
        return {}, []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        return {"unparsed_lyrdb_items": count_klayout_items(path) or 0}, []
    descriptions = category_descriptions(root)
    stats: dict[str, int] = {}
    markers: list[dict[str, Any]] = []
    for item in root.iter():
        if strip_ns(item.tag) != "item":
            continue
        category = child_text(item, "category").strip("'") or "uncategorized"
        description = descriptions.get(category, "")
        label = f"{category}: {description}" if description else category
        values = " ".join(
            value.text or ""
            for child in item
            if strip_ns(child.tag) == "values"
            for value in child
            if strip_ns(value.tag) == "value"
        )
        stats[label] = stats.get(label, 0) + 1
        markers.append(
            {
                "category": label,
                "rule": category,
                "description": description,
                "text": compact(values),
                "bbox": marker_bbox(values),
            }
        )
    return dict(sorted(stats.items())), markers


def category_descriptions(root: ET.Element) -> dict[str, str]:
    descriptions: dict[str, str] = {}
    for category in root.iter():
        if strip_ns(category.tag) != "category":
            continue
        name = child_text(category, "name")
        if not name:
            continue
        descriptions[name] = compact(child_text(category, "description"))
    return descriptions


def analyze_markers(markers: list[dict[str, Any]], power_stitches: dict[str, Any]) -> dict[str, Any]:
    stitch_rects = [
        {
            "name": str(record.get("name")),
            "net": str(record.get("net")),
            "rect": record.get("rect"),
        }
        for record in power_stitches.get("records", [])
        if isinstance(record.get("rect"), dict)
    ]
    related: list[dict[str, Any]] = []
    for marker in markers:
        bbox = marker.get("bbox")
        if not bbox:
            continue
        for stitch in stitch_rects:
            if rects_intersect(bbox, stitch["rect"]):
                related.append(
                    {
                        "marker_category": marker.get("category"),
                        "stitch_name": stitch["name"],
                        "stitch_net": stitch["net"],
                        "marker_bbox": bbox,
                    }
                )
                break
    return {
        "power_stitch_related_violation_count": len(related),
        "power_stitch_related_markers": related[:50],
        "marker_bbox_parse_count": sum(1 for marker in markers if marker.get("bbox")),
    }


def marker_bbox(text: str) -> dict[str, float] | None:
    numbers = [float(value) for value in re.findall(r"-?\d+(?:\.\d+)?", text)]
    if len(numbers) < 4:
        return None
    xs = numbers[0::2]
    ys = numbers[1::2]
    return {
        "x0": round(min(xs), 6),
        "y0": round(min(ys), 6),
        "x1": round(max(xs), 6),
        "y1": round(max(ys), 6),
    }


def rects_intersect(a: dict[str, float], b: dict[str, float]) -> bool:
    return not (a["x1"] <= b["x0"] or b["x1"] <= a["x0"] or a["y1"] <= b["y0"] or b["y1"] <= a["y0"])


def strip_ns(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def child_text(elem: ET.Element, child_name: str) -> str:
    for child in elem:
        if strip_ns(child.tag) == child_name and child.text:
            return child.text
    return ""


def compact(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def tail(text: str, lines: int = 20) -> str:
    return "\n".join(text.splitlines()[-lines:])


def manual_checklist(input_gds: Path, lyrdb: Path) -> list[str]:
    return [
        f"Open {input_gds} in KLayout.",
        "Zoom into boundaries between dummy/bitcell/replica cells.",
        "Open the DRC marker browser and load the generated .lyrdb if available.",
        "Check whether power stitch rectangles have spacing, min-width, or notch markers.",
        "Check whether the small red-layer gaps have any same-layer spacing/notch markers.",
        "Confirm no bridge connects VDD to GND.",
        "Confirm no bridge touches BL, BR, RBL, RBLB, or WL pins.",
        f"If automatic DRC ran, inspect {lyrdb} marker categories and marker locations.",
    ]


def format_markdown(report: dict[str, Any]) -> str:
    drc = report["drc"]
    findings = report["findings"]
    power = report["power_stitch_analysis"]
    lines = [
        "# OpenYield Storage-Only Tiny DRC Smoke Report",
        "",
        "This report checks the stitched storage-only smoke GDS. It is not full SRAM signoff.",
        "",
        "## Summary",
        "",
        f"- input GDS: `{report['input_gds']['path']}`",
        f"- topcell: `{report['input_gds']['topcell']}`",
        f"- DRC deck: `{report['drc_deck']['path']}`",
        f"- DRC deck available: `{report['drc_deck']['available']}`",
        f"- KLayout: `{report['klayout']['path']}`",
        f"- KLayout available: `{report['klayout']['available']}`",
        f"- DRC ran: `{drc['ran']}`",
        f"- DRC violation count: `{drc['violation_count']}`",
        f"- DRC clean: `{drc['clean']}`",
        f"- power stitch related violation: `{findings['power_stitch_related_violation']}`",
        f"- red-layer gap related violation: `{findings['red_layer_gap_related_violation']}`",
        f"- VDD/GND short observed: `{findings['vdd_gnd_short_observed']}`",
        f"- BL/BR/WL bridge observed: `{findings['bl_br_wl_bridge_observed']}`",
        f"- recommend keep current power stitch: `{findings['recommend_keep_current_power_stitch']}`",
        f"- can enter next step: `{findings['can_enter_next_step']}`",
        f"- next step blocker: `{findings['next_step_blocker']}`",
        "",
        "## Power Stitch Context",
        "",
        f"- stitch power rails: `{power['stitch_power_rails']}`",
        f"- power rail layer: `{power['power_rail_layer']}`",
        f"- VDD stitch count: `{power['vdd_stitch_count']}`",
        f"- GND stitch count: `{power['gnd_stitch_count']}`",
        f"- side power trunk added: `{power['side_power_trunk_added']}`",
        f"- same-net power only: `{power['same_net_power_only']}`",
        f"- crosses BL/BR/WL: `{power['crosses_bl_br_wl']}`",
        f"- marker bboxes parsed: `{power['marker_bbox_parse_count']}`",
        f"- stitch-overlapping DRC markers: `{power['power_stitch_related_violation_count']}`",
        "",
        "## Violation Type Stats",
        "",
    ]
    lines.extend(format_table(["type", "count"], [[k, v] for k, v in report["violation_type_stats"].items()]))
    lines.extend(["", "## Spacing / Notch / Min-Width Stats", ""])
    lines.extend(format_table(["type", "count"], [[k, v] for k, v in report["spacing_notch_min_width_stats"].items()]))
    lines.extend(["", "## Red-Layer Gap Related Stats", ""])
    lines.extend(format_table(["type", "count"], [[k, v] for k, v in report["red_layer_gap_related_stats"].items()]))
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- DRC marker DB: `{report['outputs']['lyrdb']}`",
            f"- DRC log: `{report['outputs']['log']}`",
            f"- JSON report: `{report['outputs']['json']}`",
            f"- Markdown report: `{report['outputs']['md']}`",
            "",
            "## Manual KLayout Checklist",
            "",
        ]
    )
    lines.extend(f"{idx}. {item}" for idx, item in enumerate(report["manual_klayout_checklist"], start=1))
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {note}" for note in report["notes"])
    lines.append("")
    return "\n".join(lines)


def format_table(headers: list[str], rows: list[list[Any]]) -> list[str]:
    if not rows:
        return ["- none"]
    output = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        output.append("| " + " | ".join(str(cell).replace("|", "\\|") for cell in row) + " |")
    return output


if __name__ == "__main__":
    raise SystemExit(main())
