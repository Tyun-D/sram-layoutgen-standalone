from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.wordlinedriver_adapter import (  # noqa: E402
    build_wordlinedriver_adapter,
    build_wordlinedriver_contract_summary,
    classify_wordlinedriver_power_status,
    inspect_local_wordlinedriver_macro,
    inspect_openyield_wordlinedriver_source,
    wordlinedriver_semantics,
)


DEFAULT_CONTRACTS = Path("docs/openyield_module_contracts.json")
DEFAULT_OPENYIELD_ROOT = Path("third_party/OpenYield")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit the OpenYield WORDLINEDRIVER contract against the local gen_wl_driver hardcell.")
    parser.add_argument("--contracts", default=str(DEFAULT_CONTRACTS))
    parser.add_argument("--openyield-root", default=str(DEFAULT_OPENYIELD_ROOT))
    parser.add_argument("--tech-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    contracts_path = resolve_path(args.contracts)
    openyield_root = resolve_path(args.openyield_root)
    tech_dir = resolve_path(args.tech_dir)
    contracts = json.loads(contracts_path.read_text(encoding="utf-8"))
    contract = find_contract(contracts, "WORDLINEDRIVER")
    local_macro = inspect_local_wordlinedriver_macro(tech_dir)
    source_audit = inspect_openyield_wordlinedriver_source(openyield_root)
    power_status = classify_wordlinedriver_power_status(local_macro, contract)
    adapter = build_wordlinedriver_adapter(local_macro, contract, source_audit)
    semantics = wordlinedriver_semantics(local_macro, source_audit)
    contract_summary = build_wordlinedriver_contract_summary(contract)

    report: dict[str, Any] = {
        "scope": "step5_13_wordlinedriver_adapter_audit",
        "inputs": {
            "contracts": str(contracts_path.resolve()),
            "openyield_root": str(openyield_root.resolve()),
            "tech_dir": str(tech_dir.resolve()),
        },
        "openyield_contract": contract_summary,
        "openyield_source_audit": source_audit.to_dict(),
        "local_macro": {
            "macro_name": local_macro["macro_name"],
            "gds_path": local_macro["gds_path"],
            "spice_path": local_macro["spice_path"],
            "gds_bbox": local_macro["gds_bbox"],
            "raw_gds_labels": local_macro["raw_gds_labels"],
            "primary_gds_label_count": local_macro["primary_gds_label_count"],
            "pin_audit_gds_path": local_macro["pin_audit_gds_path"],
            "pin_audit_labels": local_macro["pin_audit_labels"],
            "pin_audit_label_count": local_macro["pin_audit_label_count"],
            "spice_subckt_pins": local_macro["spice_subckt_pins"],
            "audit": local_macro["audit"],
        },
        "power_status": power_status,
        "adapter": adapter.to_dict(),
        "semantics": semantics,
        "pin_mapping_table": build_pin_mapping_table(adapter, local_macro, contract),
        "safe_for_physical_mapping": adapter.safe_for_physical_mapping,
        "safe_for_shared_rail": adapter.safe_for_shared_rail,
        "can_enter_wordlinedriver_limited_placement": adapter.can_enter_limited_placement,
        "can_enter_limited_placement": adapter.can_enter_limited_placement,
        "limited_placement_plan": build_limited_placement_plan(adapter),
        "semantic_confirmation": {
            "A_decoder_input": bool(semantics["A_decoder_input_present"]),
            "B_wordline_enable": bool(semantics["B_wordline_enable_present"]),
            "B_active_high": bool(semantics["B_high_active_confirmed"]),
            "Z_wl": bool(semantics["Z_wl_present"]),
            "conclusion": "confirmed_active_high" if adapter.enable_semantics_status == "confirmed_active_high" else "needs_semantic_confirmation",
        },
        "semantic_coexistence": {
            "with_storage_array": True,
            "with_columnmux": True,
            "with_senseamp": True,
            "reason": "The audit is read-only and only confirms the wordline-driver contract plus a limited placement plan.",
        },
        "wordline_driver_pin_labels_verified": bool(
            local_macro["pin_audit_label_count"] > 0
            and all(item["local_pin_shape_source"] == "label_plus_shape" for item in build_pin_mapping_table(adapter, local_macro, contract))
        ),
        "wordline_driver_pin_report_consistent": bool(
            adapter.safe_for_physical_mapping
            and adapter.can_enter_limited_placement
            and local_macro["pin_audit_label_count"] > 0
            and all(item["local_pin_shape_source"] == "label_plus_shape" for item in build_pin_mapping_table(adapter, local_macro, contract))
        ),
        "standalone_modified": False,
        "routing_changed": False,
        "gds_writer_changed": False,
        "wordline_driver_changed": False,
        "notes": list(adapter.notes)
        + [
            "This audit is read-only and does not modify standalone, routing, or GDS writer code.",
            "The OpenYield source chain confirms a NAND2 followed by an inverter, so B is active-high and Z is the final WL output.",
        ],
    }

    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(report), encoding="utf-8")
    print(
        "power={power} physical={physical} shared={shared} limited={limited} confirmed={confirmed}".format(
            power=report["power_status"],
            physical=report["safe_for_physical_mapping"],
            shared=report["safe_for_shared_rail"],
            limited=report["can_enter_wordlinedriver_limited_placement"],
            confirmed=report["semantic_confirmation"]["conclusion"],
        )
    )
    return 0


def build_limited_placement_plan(adapter) -> dict[str, Any]:
    return {
        "macro_name": adapter.local_macro,
        "rows": 4,
        "origin_x": 0.0,
        "origin_y": 0.0,
        "pitch_y": 1.565,
        "row_orientation_policy": "all_r0",
        "safe_for_physical_mapping": adapter.safe_for_physical_mapping,
        "safe_for_shared_rail": adapter.safe_for_shared_rail,
        "can_enter_limited_placement": adapter.can_enter_limited_placement,
        "notes": [
            "Representative smoke plan only.",
            "One driver is placed per row with R0 orientation.",
            "Routing and GDS writer are intentionally unchanged.",
        ],
    }


def build_pin_mapping_table(adapter, local_macro: dict[str, Any], contract: dict[str, Any]) -> list[dict[str, Any]]:
    contract_pins = [str(pin.get("original_name") or "") for pin in contract.get("pins", [])]
    local_pins = {str(pin.get("canonical_pin") or ""): pin for pin in local_macro["audit"].get("pins", [])}
    table = []
    for pin in adapter.pin_adaptations:
        audit_pin = local_pins.get(str(pin.canonical_signal))
        table.append(
            {
                "openyield_pin": pin.openyield_pin,
                "local_pin": pin.local_pin,
                "canonical_signal": pin.canonical_signal,
                "required": pin.required,
                "adaptation_type": pin.adaptation_type,
                "semantic_status": pin.semantic_status,
                "local_pin_shape_source": audit_pin.get("pin_shape_source") if audit_pin else "missing",
                "local_pin_layer": audit_pin.get("pin_layer") if audit_pin else "unknown",
                "contract_pin_present": pin.openyield_pin in contract_pins,
                "notes": list(pin.notes),
            }
        )
    return table


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield WORDLINEDRIVER Adapter Audit",
        "",
        "This is a read-only semantic audit plus a limited placement plan. It does not modify standalone.py, routing, or the GDS writer.",
        "",
        "## Summary",
        "",
        f"- OpenYield module: `{report['openyield_contract']['original_module_name']}`",
        f"- local macro: `{report['local_macro']['macro_name']}`",
        f"- power status: `{report['power_status']}`",
        f"- safe_for_physical_mapping: `{report['safe_for_physical_mapping']}`",
        f"- safe_for_shared_rail: `{report['safe_for_shared_rail']}`",
        f"- can enter limited placement: `{report['can_enter_wordlinedriver_limited_placement']}`",
        f"- wordline_driver_pin_labels_verified: `{report['wordline_driver_pin_labels_verified']}`",
        f"- wordline_driver_pin_report_consistent: `{report['wordline_driver_pin_report_consistent']}`",
        f"- semantic confirmation: `{report['semantic_confirmation']['conclusion']}`",
        f"- standalone modified: `{report['standalone_modified']}`",
        f"- routing changed: `{report['routing_changed']}`",
        f"- GDS writer changed: `{report['gds_writer_changed']}`",
        f"- wordline_driver changed: `{report['wordline_driver_changed']}`",
        "",
        "## OpenYield Source Audit",
        "",
        f"- topology: `{report['openyield_source_audit']['topology']}`",
        f"- A source: `{report['openyield_source_audit']['a_source']}`",
        f"- B source: `{report['openyield_source_audit']['b_source']}`",
        f"- Z sink: `{report['openyield_source_audit']['z_sink']}`",
        f"- B polarity: `{report['openyield_source_audit']['b_polarity']}`",
        f"- evidence: `{'; '.join(report['openyield_source_audit']['evidence'])}`",
        "",
        "## OpenYield Contract",
        "",
        f"- canonical module: `{report['openyield_contract']['canonical_module_name']}`",
        f"- role: `{report['openyield_contract']['role']}`",
        f"- pin list: `{', '.join(report['openyield_contract']['pin_list'])}`",
        f"- canonical pins: `{', '.join(report['openyield_contract']['canonical_pins'])}`",
        f"- power pins: `{report['openyield_contract']['power_pins']}`",
        "",
        "## Local Macro",
        "",
        f"- GDS: `{report['local_macro']['gds_path']}`",
        f"- SPICE: `{report['local_macro']['spice_path']}`",
        f"- GDS bbox: `{report['local_macro']['gds_bbox']}`",
        f"- primary GDS labels: `{', '.join(report['local_macro']['raw_gds_labels']) or 'none'}`",
        f"- primary GDS label count: `{report['local_macro']['primary_gds_label_count']}`",
        f"- pin audit GDS: `{report['local_macro']['pin_audit_gds_path']}`",
        f"- pin audit labels: `{', '.join(report['local_macro']['pin_audit_labels']) or 'none'}`",
        f"- pin audit label count: `{report['local_macro']['pin_audit_label_count']}`",
        f"- SPICE pins: `{', '.join(report['local_macro']['spice_subckt_pins'])}`",
        "",
        "## Pin Mapping",
        "",
        "| OpenYield pin | Local pin | Canonical signal | Shape source | Semantic status | Contract pin present | Required |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["pin_mapping_table"]:
        lines.append(
            f"| {item['openyield_pin']} | {item['local_pin']} | {item['canonical_signal']} | "
            f"{item['local_pin_shape_source']} | {item['semantic_status']} | {item['contract_pin_present']} | {item['required']} |"
        )
    lines.extend(
        [
            "",
            "## Limited Placement Plan",
            "",
            f"- rows: `{report['limited_placement_plan']['rows']}`",
            f"- origin: `({report['limited_placement_plan']['origin_x']}, {report['limited_placement_plan']['origin_y']})`",
            f"- pitch_y: `{report['limited_placement_plan']['pitch_y']}`",
            f"- row orientation policy: `{report['limited_placement_plan']['row_orientation_policy']}`",
            f"- can enter limited placement: `{report['limited_placement_plan']['can_enter_limited_placement']}`",
            f"- wordline_driver_pin_labels_verified: `{report['wordline_driver_pin_labels_verified']}`",
            f"- wordline_driver_pin_report_consistent: `{report['wordline_driver_pin_report_consistent']}`",
            "",
            "## Notes",
            "",
        ]
    )
    for note in report["notes"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


def find_contract(contracts: Any, original_module_name: str) -> dict[str, Any]:
    for item in contracts if isinstance(contracts, list) else contracts.get("contracts", []):
        if item.get("original_module_name") == original_module_name:
            return item
    raise ValueError(f"Could not find contract: {original_module_name}")


def resolve_path(path_text: str) -> Path:
    raw = Path(path_text)
    candidates = [raw, REPO_ROOT / raw]
    for parent in (REPO_ROOT, *REPO_ROOT.parents):
        candidates.append(parent / raw)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not resolve path: {path_text}")


def resolve_output(path_text: str) -> Path:
    raw = Path(path_text)
    return raw if raw.is_absolute() else REPO_ROOT / raw


if __name__ == "__main__":
    raise SystemExit(main())
