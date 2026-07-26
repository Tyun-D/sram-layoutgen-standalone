from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.columnmux_adapter import (  # noqa: E402
    build_columnmux_adapter,
    classify_columnmux_power_status,
    columnmux_semantics,
    inspect_local_columnmux_macro,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit OpenYield column mux adapter and power metadata.")
    parser.add_argument("--contracts", required=True)
    parser.add_argument("--tech-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    contracts_path = resolve_existing_path(args.contracts)
    tech_dir = resolve_existing_path(args.tech_dir)
    payload = json.loads(contracts_path.read_text(encoding="utf-8"))
    contract = find_contract(payload, "COLUMNMUX*")
    local_macro = inspect_local_columnmux_macro(tech_dir)
    semantics = columnmux_semantics(local_macro)
    power_status = classify_columnmux_power_status(local_macro, contract)
    adapter = build_columnmux_adapter(
        out_to_mux_out=semantics["out_to_mux_out"],
        outb_to_mux_out_b=semantics["outb_to_mux_out_b"],
        power_status=power_status,
    )

    can_enter = "limited_or_metadata_only" if adapter.safe_for_physical_mapping and not adapter.safe_for_shared_rail else (
        True if adapter.safe_for_physical_mapping and adapter.safe_for_shared_rail else False
    )
    report: dict[str, Any] = {
        "scope": "step5_4_columnmux_adapter_power_metadata_audit",
        "inputs": {
            "contracts": str(contracts_path.resolve()),
            "tech_dir": str(tech_dir.resolve()),
            "gds_path": local_macro["gds_path"],
            "replacement_macro_gds": str((tech_dir / "replacement_macros.json").resolve()),
        },
        "openyield_columnmux_module_names": ["COLUMNMUX*", "ColumnMuxFactory"],
        "openyield_pin_list": [pin["original_name"] for pin in contract.get("pins", [])],
        "openyield_power_pins": dict(contract.get("power_pins", {})),
        "local_gen_col_mux_gds_labels": local_macro["raw_gds_labels"],
        "local_gen_col_mux_gds_canonical_pins": [
            {
                "pin": pin.get("pin_name"),
                "canonical": pin.get("canonical_pin"),
                "shape_source": pin.get("pin_shape_source"),
                "shape_bbox": pin.get("pin_shape_bbox"),
            }
            for pin in local_macro["audit"].get("pins", [])
        ],
        "local_spice_pins": local_macro["spice_subckt_pins"],
        "replacement_macro_pins": local_macro["replacement_macro"].get("pins", []),
        "pin_mapping_table": [item.to_dict() for item in adapter.pin_adaptations],
        "semantics": semantics,
        "out_to_mux_out_established": semantics["out_to_mux_out"],
        "outb_to_mux_out_b_established": semantics["outb_to_mux_out_b"],
        "vdd_metadata_present": power_status == "vdd_gnd_metadata_present",
        "gnd_metadata_present": semantics["gnd_present"],
        "power_status": adapter.power_status,
        "safe_for_physical_mapping": adapter.safe_for_physical_mapping,
        "safe_for_shared_rail": adapter.safe_for_shared_rail,
        "requires_power_metadata_fix": adapter.requires_power_metadata_fix,
        "senseamp_mux_interface": {
            "IN": "mux_out[group]",
            "INB": "mux_out_b[group]",
            "Q": "dout[group]",
            "QB": "dropped_complementary_output",
        },
        "columnmux_can_pair_with_senseamp_adapter": bool(
            semantics["out_to_mux_out"] and semantics["outb_to_mux_out_b"]
        ),
        "can_enter_columnmux_placement": can_enter,
        "notes": list(adapter.notes),
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
    }

    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    out_md.write_text(render_markdown(report), encoding="utf-8")
    print(
        "out={out} outb={outb} power={power} physical={physical} shared={shared} enter={enter}".format(
            out=report["out_to_mux_out_established"],
            outb=report["outb_to_mux_out_b_established"],
            power=report["power_status"],
            physical=report["safe_for_physical_mapping"],
            shared=report["safe_for_shared_rail"],
            enter=report["can_enter_columnmux_placement"],
        )
    )
    return 0


def resolve_existing_path(path_text: str) -> Path:
    raw = Path(path_text)
    candidates = [raw, REPO_ROOT / raw]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not resolve path: {path_text}")


def find_contract(payload: dict[str, Any], original_module: str) -> dict[str, Any]:
    matches = [item for item in payload.get("contracts", []) if item.get("original_module_name") == original_module]
    if not matches:
        raise ValueError(f"Contract not found: {original_module}")
    return matches[0]


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield ColumnMux Adapter Report",
        "",
        "This Step 5.4 report is read-only. It audits column mux signal semantics and power metadata without modifying standalone placement, routing, or GDS writer.",
        "",
        "## Summary",
        "",
        f"- OpenYield pin list: `{', '.join(report['openyield_pin_list'])}`",
        f"- local gen_col_mux GDS labels: `{report['local_gen_col_mux_gds_labels']}`",
        f"- local SPICE pins: `{report['local_spice_pins']}`",
        f"- OUT -> mux_out established: `{report['out_to_mux_out_established']}`",
        f"- OUTB -> mux_out_b established: `{report['outb_to_mux_out_b_established']}`",
        f"- VDD metadata present: `{report['vdd_metadata_present']}`",
        f"- GND metadata present: `{report['gnd_metadata_present']}`",
        f"- power_status: `{report['power_status']}`",
        f"- safe_for_physical_mapping: `{report['safe_for_physical_mapping']}`",
        f"- safe_for_shared_rail: `{report['safe_for_shared_rail']}`",
        f"- requires_power_metadata_fix: `{report['requires_power_metadata_fix']}`",
        f"- can enter column mux placement: `{report['can_enter_columnmux_placement']}`",
        "",
        "## Pin Mapping",
        "",
        "| OpenYield pin | Local pin | Canonical | Type | Required | Notes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["pin_mapping_table"]:
        notes = "; ".join(item.get("notes") or ())
        lines.append(
            f"| {item['openyield_pin']} | {item['local_pin'] or '-'} | {item['canonical_signal']} | "
            f"{item['adaptation_type']} | {item['required']} | {notes or '-'} |"
        )
    lines += [
        "",
        "## SenseAmp Pairing",
        "",
        f"- sense_amp mux interface: `{report['senseamp_mux_interface']}`",
        f"- column mux can pair with sense_amp adapter: `{report['columnmux_can_pair_with_senseamp_adapter']}`",
        "",
        "## Notes",
        "",
    ]
    for note in report["notes"]:
        lines.append(f"- {note}")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
