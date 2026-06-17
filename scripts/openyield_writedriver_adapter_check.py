from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.writedriver_adapter import (  # noqa: E402
    build_writedriver_adapter,
    build_writedriver_contract_summary,
    classify_writedriver_power_status,
    inspect_local_writedriver_macro,
    writedriver_semantics,
)


DEFAULT_CONTRACTS = Path("docs/openyield_module_contracts.json")


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit the OpenYield WRITEDRIVER contract against the local write_driver hardcell.")
    parser.add_argument("--contracts", default=str(DEFAULT_CONTRACTS))
    parser.add_argument("--tech-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    contracts_path = resolve_path(args.contracts)
    tech_dir = resolve_path(args.tech_dir)
    contracts = json.loads(contracts_path.read_text(encoding="utf-8"))
    contract = find_contract(contracts, "WRITEDRIVER")
    local_macro = inspect_local_writedriver_macro(tech_dir)
    power_status = classify_writedriver_power_status(local_macro, contract)
    adapter = build_writedriver_adapter(local_macro, contract)
    semantics = writedriver_semantics(local_macro)
    contract_summary = build_writedriver_contract_summary(contract)

    report = {
        "scope": "step5_10_writedriver_adapter_audit",
        "inputs": {
            "contracts": str(contracts_path.resolve()),
            "tech_dir": str(tech_dir.resolve()),
        },
        "openyield_contract": contract_summary,
        "local_macro": {
            "macro_name": local_macro["macro_name"],
            "gds_path": local_macro["gds_path"],
            "spice_path": local_macro["spice_path"],
            "gds_bbox": local_macro["gds_bbox"],
            "raw_gds_labels": local_macro["raw_gds_labels"],
            "spice_subckt_pins": local_macro["spice_subckt_pins"],
            "audit": local_macro["audit"],
        },
        "power_status": power_status,
        "adapter": adapter.to_dict(),
        "semantics": semantics,
        "pin_mapping_table": build_pin_mapping_table(adapter, local_macro, contract),
        "safe_for_physical_mapping": adapter.safe_for_physical_mapping,
        "safe_for_shared_rail": adapter.safe_for_shared_rail,
        "can_enter_writedriver_limited_placement": adapter.safe_for_physical_mapping and not adapter.safe_for_shared_rail,
        "semantic_coexistence": {
            "with_columnmux": True,
            "with_senseamp": True,
            "with_storage_array": True,
            "reason": "adapter-only metadata and placement planning do not change routing or shared rails.",
        },
        "standalone_modified": False,
        "routing_changed": False,
        "gds_writer_changed": False,
        "write_driver_changed": False,
        "notes": list(adapter.notes) + [
            "This audit is read-only and does not modify standalone, routing, or GDS writer code.",
        ],
    }

    out_json = resolve_output(args.out_json)
    out_md = resolve_output(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(report), encoding="utf-8")
    print(
        "power={power} physical={physical} shared={shared} limited={limited}".format(
            power=report["power_status"],
            physical=report["safe_for_physical_mapping"],
            shared=report["safe_for_shared_rail"],
            limited=report["can_enter_writedriver_limited_placement"],
        )
    )
    return 0


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
                "local_pin_shape_source": audit_pin.get("pin_shape_source") if audit_pin else "missing",
                "local_pin_layer": audit_pin.get("pin_layer") if audit_pin else "unknown",
                "contract_pin_present": pin.openyield_pin in contract_pins,
                "notes": list(pin.notes),
            }
        )
    return table


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield WRITEDRIVER Adapter Audit",
        "",
        f"- OpenYield module: `{report['openyield_contract']['original_module_name']}`",
        f"- local macro: `{report['local_macro']['macro_name']}`",
        f"- power status: `{report['power_status']}`",
        f"- safe_for_physical_mapping: `{report['safe_for_physical_mapping']}`",
        f"- safe_for_shared_rail: `{report['safe_for_shared_rail']}`",
        f"- can enter limited placement: `{report['can_enter_writedriver_limited_placement']}`",
        f"- semantic coexistence with column mux / sense amp / storage array: `{report['semantic_coexistence']['with_columnmux'] and report['semantic_coexistence']['with_senseamp'] and report['semantic_coexistence']['with_storage_array']}`",
        f"- standalone modified: `{report['standalone_modified']}`",
        f"- routing changed: `{report['routing_changed']}`",
        f"- GDS writer changed: `{report['gds_writer_changed']}`",
        f"- write_driver changed: `{report['write_driver_changed']}`",
        "",
        "## OpenYield Contract",
        "",
        f"- canonical module: `{report['openyield_contract']['canonical_module_name']}`",
        f"- role: `{report['openyield_contract']['role']}`",
        f"- pin list: `{', '.join(report['openyield_contract']['pin_list'])}`",
        f"- canonical pins: `{', '.join(report['openyield_contract']['canonical_pins'])}`",
        f"- power pins: `{report['openyield_contract']['power_pins']}`",
        f"- semantic coexistence reason: `{report['semantic_coexistence']['reason']}`",
        "",
        "## Local Macro",
        "",
        f"- GDS: `{report['local_macro']['gds_path']}`",
        f"- SPICE: `{report['local_macro']['spice_path']}`",
        f"- GDS bbox: `{report['local_macro']['gds_bbox']}`",
        f"- GDS labels: `{', '.join(report['local_macro']['raw_gds_labels'])}`",
        f"- SPICE pins: `{', '.join(report['local_macro']['spice_subckt_pins'])}`",
        "",
        "## Pin Mapping",
        "",
        "| OpenYield pin | Local pin | Canonical signal | Shape source | Contract pin present | Required |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["pin_mapping_table"]:
        lines.append(
            f"| {item['openyield_pin']} | {item['local_pin']} | {item['canonical_signal']} | "
            f"{item['local_pin_shape_source']} | {item['contract_pin_present']} | {item['required']} |"
        )
    lines.extend(["", "## Notes", ""])
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
    for candidate in (raw, REPO_ROOT / raw):
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not resolve path: {path_text}")


def resolve_output(path_text: str) -> Path:
    raw = Path(path_text)
    return raw if raw.is_absolute() else REPO_ROOT / raw


if __name__ == "__main__":
    raise SystemExit(main())
