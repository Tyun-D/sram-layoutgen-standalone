"""Helpers for recording external KLayout signoff results."""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path


def count_klayout_items(path: Path) -> int | None:
    if not path.exists():
        return None
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError:
        text = path.read_text(errors="ignore")
        return text.lower().count("<item")
    count = 0
    for elem in root.iter():
        if elem.tag.lower().endswith("item"):
            count += 1
    return count


def update_report(
    report_path: Path,
    drc_path: Path | None,
    lvs_path: Path | None,
    extracted_path: Path | None,
    integration_drc_only: bool = False,
) -> dict:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    signoff = report.setdefault("external_signoff", {})
    if drc_path is not None:
        count = count_klayout_items(drc_path)
        drc_key = "integration_klayout_drc" if integration_drc_only else "klayout_drc"
        if integration_drc_only:
            previous_full_drc = signoff.get("klayout_drc", {})
            previous_report = str(previous_full_drc.get("report", ""))
            if previous_report == str(drc_path) or "integration_klayout_drc" in previous_report:
                signoff.pop("klayout_drc", None)
        signoff[drc_key] = {
            "report": str(drc_path),
            "available": drc_path.exists(),
            "violation_count": count,
            "clean": count == 0 if count is not None else False,
            "scope": "integration_blackbox" if integration_drc_only else "full_gds",
        }
    if lvs_path is not None:
        count = count_klayout_items(lvs_path)
        signoff["klayout_lvs"] = {
            "report": str(lvs_path),
            "available": lvs_path.exists(),
            "item_count": count,
            "clean": count == 0 if count is not None else False,
        }
    if extracted_path is not None:
        signoff["extracted_netlist"] = {
            "path": str(extracted_path),
            "available": extracted_path.exists(),
        }

    abstract = bool(report.get("abstract_instances"))
    full_drc_clean = signoff.get("klayout_drc", {}).get("clean") is True
    integration_drc_clean = signoff.get("integration_klayout_drc", {}).get("clean") is True
    lvs_clean = signoff.get("klayout_lvs", {}).get("clean") is True
    criteria = report.setdefault("signoff_criteria", {})
    criteria["external_drc_clean"] = full_drc_clean
    criteria["integration_drc_clean"] = integration_drc_clean
    criteria["external_lvs_clean"] = lvs_clean
    criteria["external_pex_available"] = bool(signoff.get("extracted_netlist", {}).get("available"))
    base_ready = (
        (not abstract)
        and criteria.get("all_structural_roles_present") is not False
        and criteria.get("drawn_routes_touch_generated_roles") is not False
        and criteria.get("drawn_routes_cover_generated_signal_pins") is not False
        and criteria.get("built_in_drc_clean") is not False
        and criteria.get("layers_match_freepdk45") is not False
        and criteria.get("architecture_floorplan_clean") is not False
        and criteria.get("geometry_clean") is not False
    )
    report["integration_signoff_ready"] = base_ready and integration_drc_clean
    report["signoff_ready"] = (
        base_ready
        and full_drc_clean
        and lvs_clean
    )
    base_blockers = []
    if abstract:
        base_blockers.append("abstract peripheral logic remains")
    if criteria.get("all_structural_roles_present") is False:
        base_blockers.append("not all structural SRAM roles are present")
    if criteria.get("drawn_routes_touch_generated_roles") is False:
        base_blockers.append("some replacement macro roles are not touched by drawn detailed routes")
    if criteria.get("drawn_routes_cover_generated_signal_pins") is False:
        base_blockers.append("some replacement macro signal pins are not covered by drawn detailed routes")
    if criteria.get("built_in_drc_clean") is False:
        base_blockers.append("built-in DRC-lite is not clean")
    if criteria.get("layers_match_freepdk45") is False:
        base_blockers.append("GDS layers do not match the bundled FreePDK45 layer map")
    if criteria.get("architecture_floorplan_clean") is False:
        base_blockers.append("architecture floorplan audit is not clean")
    if criteria.get("geometry_clean") is False:
        base_blockers.append("geometry audit is not clean")
    integration_blockers = list(base_blockers)
    if not integration_drc_clean:
        integration_blockers.append("integration KLayout DRC is not clean or was not run")
    report["integration_signoff_blockers"] = [] if report["integration_signoff_ready"] else integration_blockers
    blockers = list(base_blockers)
    if not full_drc_clean:
        blockers.append("full external KLayout DRC is not clean or was not run")
    if not lvs_clean:
        blockers.append("external KLayout LVS is not clean or was not run")
    if report["signoff_ready"]:
        report["signoff_blockers"] = []
    else:
        report["signoff_blockers"] = blockers
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    _refresh_markdown_report(report_path, report)
    return report


def _refresh_markdown_report(report_path: Path, report: dict) -> None:
    md_path = report_path.with_suffix(".md")
    if not md_path.exists():
        return
    try:
        from .standalone import _format_report_md
    except Exception:
        return
    md_path.write_text(_format_report_md(report), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--drc", type=Path)
    parser.add_argument("--lvs", type=Path)
    parser.add_argument("--extracted", type=Path)
    parser.add_argument("--integration-drc-only", action="store_true")
    args = parser.parse_args()
    updated = update_report(args.report, args.drc, args.lvs, args.extracted, args.integration_drc_only)
    print(json.dumps(updated.get("external_signoff", {}), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
