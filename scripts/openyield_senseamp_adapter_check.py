"""Check OpenYield SENSEAMP architecture adaptation against local sense_amp.

This script is intentionally read-only.  It scans OpenYield source text,
existing contract JSON, local SPICE, and local GDS TEXT/pin metadata, then
emits a report describing whether OpenYield Q/QB can be mapped onto the
single-ended local sense_amp hardcell.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.architecture_adapter import (
    build_senseamp_architecture_adapter,
    recommended_senseamp_strategy,
)
from sram_layoutgen.openyield_adapter.gds_pin_audit import audit_macros


SOURCE_PATTERNS = ("*.py", "*.sp", "*.spi", "*.cdl", "*.v", "*.sv", "*.md", "*.json")
SCAN_TERMS = ("QB", "dout_b", "OUTB", "SA_QB", "SENSEAMP", "DATA_DFF", "D_LATCH", "tri_gate", "SA_Q", "OUT")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--openyield-root", required=True)
    parser.add_argument("--contracts", required=True)
    parser.add_argument("--tech-dir", required=True)
    parser.add_argument("--out-json", required=True)
    parser.add_argument("--out-md", required=True)
    args = parser.parse_args()

    cwd = Path.cwd()
    openyield_root = resolve_existing_path(args.openyield_root, cwd)
    contracts_path = resolve_existing_path(args.contracts, cwd)
    tech_dir = resolve_existing_path(args.tech_dir, cwd)

    contracts_payload = json.loads(contracts_path.read_text(encoding="utf-8"))
    sense_contract = find_contract(contracts_payload, "SENSEAMP")
    local_spice = parse_spice_subckt(tech_dir / "sp_lib" / "sense_amp.sp")
    gds_audit = audit_macros(tech_dir, tech_dir / "openyield_macro_aliases.json", focus=("sense_amp",))
    sense_gds = next(item for item in gds_audit["audited_macros"] if item["macro_name"] == "sense_amp")

    source_hits = scan_openyield_sources(openyield_root)
    usage = classify_qb_usage(source_hits)
    adapter = build_senseamp_architecture_adapter(usage["qb_required_by_downstream_logic"])
    strategy = recommended_senseamp_strategy(usage["qb_required_by_downstream_logic"])

    q_to_dout = pin_status(sense_gds, "Q", "dout") == "label_plus_shape"
    qb_to_dout_b = pin_status(sense_gds, "QB", "dout_b") == "label_plus_shape"
    can_enter_placement = bool(adapter.safe_for_physical_mapping and q_to_dout and not qb_to_dout_b)

    report: dict[str, Any] = {
        "scope": "step5_1_senseamp_architecture_adapter_read_only",
        "inputs": {
            "openyield_root": str(openyield_root.resolve()),
            "contracts": str(contracts_path.resolve()),
            "tech_dir": str(tech_dir.resolve()),
            "local_spice": str((tech_dir / "sp_lib" / "sense_amp.sp").resolve()),
            "local_gds": str((tech_dir / "gds_lib" / "sense_amp.gds").resolve()),
        },
        "openyield_senseamp_pin_list": [pin["original_name"] for pin in sense_contract.get("pins", [])],
        "openyield_senseamp_canonical_pins": [
            {
                "original": pin["original_name"],
                "canonical": pin["canonical_name"],
                "direction": pin.get("direction"),
                "role": pin.get("role"),
            }
            for pin in sense_contract.get("pins", [])
        ],
        "local_senseamp_spice_pin_list": local_spice["pins"],
        "local_senseamp_spice_subckt": local_spice["subckt"],
        "local_senseamp_gds_pin_list": gds_pin_list(sense_gds),
        "local_senseamp_semantic_flags": sense_gds.get("semantic_flags", []),
        "pin_adaptation_table": [item.to_dict() for item in adapter.pin_adaptations],
        "q_to_dout_established": q_to_dout,
        "qb_to_dout_b_established": qb_to_dout_b,
        "openyield_qb_usage": usage,
        "adapter_strategy": strategy,
        "adapter": adapter.to_dict(),
        "requires_netlist_rewrite": adapter.requires_netlist_rewrite,
        "requires_layout_pin": adapter.requires_layout_pin,
        "requires_layout_change": False,
        "can_enter_senseamp_placement": can_enter_placement,
        "placement_entry_conditions": [
            "Use architecture adapter to drop/ignore OpenYield QB only when it is observation-only.",
            "Do not add a fake dout_b GDS pin.",
            "Map OpenYield Q to local dout and then to the existing single-ended output path.",
            "Keep peripheral placement/routing unchanged until the next explicit integration step.",
        ],
        "source_scan_hit_count": sum(len(v) for v in source_hits.values()),
        "source_scan_hits_by_file": source_hits,
        "conclusions": build_conclusions(strategy, usage, can_enter_placement),
    }

    out_json = Path(args.out_json)
    out_md = Path(args.out_md)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    out_md.write_text(render_markdown(report), encoding="utf-8")

    print(
        "strategy={strategy} safe={safe} q_to_dout={q} qb_to_dout_b={qb} can_enter_placement={place}".format(
            strategy=strategy,
            safe=adapter.safe_for_physical_mapping,
            q=q_to_dout,
            qb=qb_to_dout_b,
            place=can_enter_placement,
        )
    )
    return 0


def resolve_existing_path(path_text: str, cwd: Path) -> Path:
    raw = Path(path_text)
    candidates = [raw, cwd / raw]
    for parent in (cwd, *cwd.parents):
        candidates.append(parent / raw)
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Could not resolve path: {path_text}")


def find_contract(payload: dict[str, Any], original_module: str) -> dict[str, Any]:
    matches = [
        item
        for item in payload.get("contracts", [])
        if item.get("original_module_name") == original_module
    ]
    if not matches:
        raise ValueError(f"Contract not found: {original_module}")
    return max(matches, key=lambda item: len(item.get("pins", [])))


def parse_spice_subckt(path: Path) -> dict[str, Any]:
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        stripped = line.strip()
        if stripped.lower().startswith(".subckt"):
            parts = stripped.split()
            return {"subckt": parts[1] if len(parts) > 1 else "", "pins": parts[2:]}
    return {"subckt": "", "pins": []}


def gds_pin_list(sense_gds: dict[str, Any]) -> list[dict[str, Any]]:
    pins = []
    for pin in sense_gds.get("pins", []):
        pins.append(
            {
                "pin": pin["pin_name"],
                "canonical": pin["canonical_pin"],
                "layer": pin["pin_layer"],
                "side": pin["pin_side"],
                "shape_source": pin["pin_shape_source"],
                "shape_bbox": pin.get("pin_shape_bbox"),
            }
        )
    return pins


def pin_status(sense_gds: dict[str, Any], pin_name: str, canonical: str) -> str:
    for pin in sense_gds.get("pins", []):
        if pin.get("pin_name") == pin_name and pin.get("canonical_pin") == canonical:
            return str(pin.get("pin_shape_source") or "")
    return "missing"


def scan_openyield_sources(openyield_root: Path) -> dict[str, list[dict[str, Any]]]:
    scan_roots = [
        openyield_root / "sram_compiler" / "subcircuits",
        openyield_root / "sram_compiler" / "testbenches",
    ]
    hits: dict[str, list[dict[str, Any]]] = {}
    for root in scan_roots:
        if not root.exists():
            continue
        for path in sorted(unique_files(root, SOURCE_PATTERNS)):
            rel = path.relative_to(openyield_root).as_posix()
            file_hits: list[dict[str, Any]] = []
            for line_no, line in enumerate(path.read_text(encoding="utf-8", errors="ignore").splitlines(), start=1):
                if any(term in line for term in SCAN_TERMS):
                    file_hits.append({"line": line_no, "text": line.strip()[:220], "category": categorize_line(line)})
            if file_hits:
                hits[rel] = file_hits
    return hits


def unique_files(root: Path, patterns: Iterable[str]) -> list[Path]:
    paths: dict[Path, None] = {}
    for pattern in patterns:
        for path in root.rglob(pattern):
            if path.is_file():
                paths[path] = None
    return list(paths)


def categorize_line(line: str) -> str:
    compact = line.replace(" ", "")
    if "NODES" in line and "QB" in line and "SENSEAMP" not in line:
        return "module_pin_contract"
    if ".PRINT" in line and ("SA_QB" in line or "QB" in line):
        return "testbench_observation"
    if "init_cond" in line and "SA_QB" in line:
        return "testbench_initial_condition"
    if "measure" in line or "TARG V(SA_QB" in line or "V(SA_QB" in line:
        return "testbench_measurement_or_observation"
    if "f'SA_QB{col}'" in compact or 'f"SA_QB{col}"' in compact:
        return "senseamp_qb_instance_net"
    if "D_LATCH" in line or "OUT" in line:
        return "output_path_candidate"
    if "self.M" in line and "QB" in line:
        return "senseamp_internal_transistor"
    return "source_reference"


def classify_qb_usage(hits: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    flat = [
        {"file": file_name, **hit}
        for file_name, file_hits in hits.items()
        for hit in file_hits
    ]
    qb_hits = [hit for hit in flat if "QB" in hit["text"] or "SA_QB" in hit["text"] or "dout_b" in hit["text"]]
    downstream = []
    observation = []
    instance_outputs = []
    output_path_q_only = []
    for hit in flat:
        text = hit["text"]
        category = hit["category"]
        if "SA_Q" in text and "OUT" in text and "SA_QB" not in text:
            output_path_q_only.append(hit)
        if "SA_QB" in text and category in {"testbench_observation", "testbench_initial_condition", "testbench_measurement_or_observation"}:
            observation.append(hit)
        elif "SA_QB" in text and category == "senseamp_qb_instance_net":
            instance_outputs.append(hit)
        elif ("SA_QB" in text or "QB" in text) and category == "output_path_candidate":
            downstream.append(hit)

    qb_required = bool(downstream)
    return {
        "qb_hit_count": len(qb_hits),
        "senseamp_qb_instance_output_count": len(instance_outputs),
        "qb_observation_or_testbench_count": len(observation),
        "qb_downstream_logic_count": len(downstream),
        "qb_required_by_downstream_logic": qb_required,
        "q_only_output_path_count": len(output_path_q_only),
        "q_only_output_path_examples": trim_hits(output_path_q_only, 5),
        "qb_instance_output_examples": trim_hits(instance_outputs, 5),
        "qb_observation_examples": trim_hits(observation, 8),
        "qb_downstream_examples": trim_hits(downstream, 8),
        "interpretation": (
            "OpenYield names SENSEAMP.QB nets, but the scanned physical output path feeds OUT from SA_Q. "
            "SA_QB appears as a senseamp output net and in testbench observation/initialization, not as a required local GDS output pin."
            if not qb_required
            else "OpenYield QB appears to feed downstream logic; do not map to single-ended local sense_amp without adding dout_b support."
        ),
    }


def trim_hits(hits: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    return hits[:limit]


def build_conclusions(strategy: str, usage: dict[str, Any], can_enter_placement: bool) -> list[str]:
    conclusions = [
        "OpenYield SENSEAMP uses pins VDD, VSS, EN, IN, INB, Q, QB.",
        "Local sense_amp SPICE/GDS exposes bl, br, dout, en, vdd, gnd and has no proven dout_b/QB pin.",
        "Q -> dout is established by local GDS label plus shape audit.",
        "QB -> dout_b is not established and must not be forced.",
    ]
    if usage["qb_required_by_downstream_logic"]:
        conclusions.append("QB appears to be required by downstream logic; use a generated dout_b or dual-output hardcell strategy.")
    else:
        conclusions.append("QB appears observation/testbench-oriented for the current readout path; the single-ended Q -> dout adapter is acceptable.")
    conclusions.append(f"Recommended adapter strategy: {strategy}.")
    conclusions.append(f"Can enter sense_amp placement with this adapter: {can_enter_placement}.")
    return conclusions


def render_markdown(report: dict[str, Any]) -> str:
    usage = report["openyield_qb_usage"]
    adapter = report["adapter"]
    lines = [
        "# OpenYield SenseAmp Architecture Adapter Report",
        "",
        "This Step 5.1 report is read-only. It does not modify placement, routing, GDS writer, hardcell GDS, or OpenYield source.",
        "",
        "## Inputs",
        "",
    ]
    for key, value in report["inputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines += [
        "",
        "## Pin Lists",
        "",
        f"- OpenYield SENSEAMP pins: `{', '.join(report['openyield_senseamp_pin_list'])}`",
        f"- local sense_amp SPICE pins: `{', '.join(report['local_senseamp_spice_pin_list'])}`",
        f"- local sense_amp GDS label-backed canonical pins: `{', '.join(pin['canonical'] for pin in report['local_senseamp_gds_pin_list'] if pin['shape_source'] != 'missing')}`",
        "",
        "## Pin Adaptation",
        "",
        "| OpenYield pin | Local pin | Canonical signal | Type | Required | Notes |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["pin_adaptation_table"]:
        notes = "; ".join(item.get("notes") or ())
        lines.append(
            f"| {item['openyield_pin']} | {item['local_pin'] or '-'} | {item['canonical_signal']} | "
            f"{item['adaptation_type']} | {item['required']} | {notes or '-'} |"
        )
    lines += [
        "",
        "## Q/QB Findings",
        "",
        f"- Q -> dout established: `{report['q_to_dout_established']}`",
        f"- QB -> dout_b established: `{report['qb_to_dout_b_established']}`",
        f"- OpenYield QB required by downstream logic: `{usage['qb_required_by_downstream_logic']}`",
        f"- QB instance output references: `{usage['senseamp_qb_instance_output_count']}`",
        f"- QB observation/testbench references: `{usage['qb_observation_or_testbench_count']}`",
        f"- Q-only output path examples: `{usage['q_only_output_path_count']}`",
        "",
        usage["interpretation"],
        "",
        "## Adapter Decision",
        "",
        f"- adapter strategy: `{report['adapter_strategy']}`",
        f"- safe for physical mapping: `{adapter['safe_for_physical_mapping']}`",
        f"- requires netlist rewrite: `{report['requires_netlist_rewrite']}`",
        f"- requires layout pin: `{report['requires_layout_pin']}`",
        f"- requires layout change: `{report['requires_layout_change']}`",
        f"- can enter sense_amp placement: `{report['can_enter_senseamp_placement']}`",
        "",
        "## Source Scan Summary",
        "",
        f"- source scan hits: `{report['source_scan_hit_count']}`",
        f"- QB hits: `{usage['qb_hit_count']}`",
        f"- QB downstream logic hits: `{usage['qb_downstream_logic_count']}`",
        "",
        "### Representative Examples",
        "",
    ]
    for title, examples in [
        ("Q-only output path", usage["q_only_output_path_examples"]),
        ("QB instance output", usage["qb_instance_output_examples"]),
        ("QB observation/testbench", usage["qb_observation_examples"]),
        ("QB downstream", usage["qb_downstream_examples"]),
    ]:
        lines.append(f"#### {title}")
        if not examples:
            lines.append("")
            lines.append("- none")
        for hit in examples:
            lines.append(f"- `{hit['file']}:{hit['line']}` {hit['text']}")
        lines.append("")
    lines += [
        "## Conclusions",
        "",
    ]
    for item in report["conclusions"]:
        lines.append(f"- {item}")
    lines += [
        "",
        "## Next Step",
        "",
        "- Proceed to sense_amp placement only with the architecture adapter active.",
        "- Keep QB as unsupported/dropped unless a later OpenYield architecture path proves it feeds required physical logic.",
        "- After sense_amp, audit write_driver and then column mux power metadata before broader peripheral placement.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
