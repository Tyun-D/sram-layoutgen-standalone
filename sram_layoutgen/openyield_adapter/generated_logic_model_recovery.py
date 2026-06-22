"""Readonly generated-logic timing model recovery inventory."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


SEARCH_ROOTS_REL = [
    "technology/freepdk45",
    "technology/freepdk45/gds_lib",
    "technology/freepdk45/gds_lib/openram_replacements",
    "technology/freepdk45/gds_lib/openyield_repaired",
    "technology/freepdk45/sp_lib",
    "technology/freepdk45/tech",
    "sram_layoutgen",
    "scripts",
    "docs",
    "build",
]

SEARCH_EXTENSIONS = {
    ".gds",
    ".sp",
    ".spi",
    ".spice",
    ".cdl",
    ".net",
    ".lib",
    ".lef",
    ".json",
    ".md",
    ".py",
    ".tcl",
    ".log",
}

P0_MACROS = ["gen_inv", "gen_nand2", "gen_delay_inv"]
SECONDARY_MACROS = [
    "gen_precharge",
    "gen_wl_driver",
    "gen_col_mux_vdd_labeled",
    "dff",
    "sense_amp",
    "write_driver",
    "cell_1rw",
    "replica_cell_1rw",
]

MACRO_SPECS = {
    "gen_inv": {
        "priority": "P0",
        "role_in_time_control": "generic inverter leaf for PDRIVE / WL_PDRIVE / PINV / composite logic",
        "blocks_timing_objects": ["PDRIVE", "WL_PDRIVE", "PINV", "AND2", "AND3_COMPOSITE", "PNAND3_COMPOSITE"],
    },
    "gen_nand2": {
        "priority": "P0",
        "role_in_time_control": "generic nand2 leaf for AND2 / AND3_COMPOSITE / PNAND3_COMPOSITE",
        "blocks_timing_objects": ["AND2", "AND3_COMPOSITE", "PNAND3_COMPOSITE", "WRITE_ENABLE_PATH", "SENSE_ENABLE_PATH", "PRECHARGE_ENABLE_PATH"],
    },
    "gen_delay_inv": {
        "priority": "P0",
        "role_in_time_control": "delay-chain inverter leaf for DELAY_CHAIN / WEN_DELAY_CHAIN",
        "blocks_timing_objects": ["DELAY_CHAIN", "WEN_DELAY_CHAIN", "RBL_DELAY_PATH"],
    },
    "gen_precharge": {
        "priority": "P1",
        "role_in_time_control": "precharge consumer macro reference",
        "blocks_timing_objects": ["PRECHARGE", "PRECHARGE_ENABLE_PATH"],
    },
    "gen_wl_driver": {
        "priority": "P1",
        "role_in_time_control": "wordline-enable consumer macro reference",
        "blocks_timing_objects": ["WL_PDRIVE", "WORDLINE_ENABLE_PATH"],
    },
    "gen_col_mux_vdd_labeled": {
        "priority": "P2",
        "role_in_time_control": "read-path alias reference, not current TIME/control blocker",
        "blocks_timing_objects": [],
    },
    "dff": {
        "priority": "P1",
        "role_in_time_control": "clocked row consumer reference",
        "blocks_timing_objects": ["DFF_ROW", "GATED_CLOCK_PATH"],
    },
    "sense_amp": {
        "priority": "P1",
        "role_in_time_control": "sense-enable consumer reference",
        "blocks_timing_objects": ["SENSE_ENABLE_PATH"],
    },
    "write_driver": {
        "priority": "P1",
        "role_in_time_control": "write-enable consumer reference",
        "blocks_timing_objects": ["WRITE_ENABLE_PATH"],
    },
    "cell_1rw": {
        "priority": "P2",
        "role_in_time_control": "replica/bitline load reference",
        "blocks_timing_objects": ["RBL_DELAY_PATH"],
    },
    "replica_cell_1rw": {
        "priority": "P2",
        "role_in_time_control": "replica timing reference cell",
        "blocks_timing_objects": ["DELAY_CHAIN", "RBL_DELAY_PATH"],
    },
}

SUBCKT_RE = re.compile(r"^\s*\.SUBCKT\s+(\S+)\s*(.*)$", re.IGNORECASE)
LIB_CELL_RE = re.compile(r"\bcell\s*\(\s*([^)]+)\s*\)", re.IGNORECASE)
RELATED_PIN_RE = re.compile(r'related_pin\s*:\s*"([^"]+)"', re.IGNORECASE)
TIMING_RE = re.compile(r"\btiming\s*\(", re.IGNORECASE)


def build_generated_logic_model_recovery_report(
    repo_root: str | Path,
    tech_dir: str | Path,
    timing_proof_plan_path: str | Path,
    timing_metadata_path: str | Path,
    asset_inventory_path: str | Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    tech = _resolve(root, tech_dir)
    upstream_repo_root = root.parents[1]
    openyield_root = upstream_repo_root / "third_party" / "OpenYield"

    timing_plan = _load_json(_resolve(root, timing_proof_plan_path))
    timing_metadata = _load_json(_resolve(root, timing_metadata_path))
    asset_inventory = _load_json(_resolve(root, asset_inventory_path))
    leaf_inventory = _optional_json(root / "docs" / "openyield_time_control_leaf_inventory_report.json")
    subblock_audit = _optional_json(root / "docs" / "openyield_time_control_subblock_audit_report.json")

    scanned_roots = [_resolve(root, item) for item in SEARCH_ROOTS_REL]
    if openyield_root.exists():
        scanned_roots.append(openyield_root)
    all_files = _scan_files(scanned_roots)

    leaf_rows = {}
    if leaf_inventory:
        for row in leaf_inventory.get("leaf_gds_bbox_pin_side_inventory", []):
            if row.get("recommended_for_future_planning"):
                leaf_rows[row["macro_name"]] = row

    source_files = {}
    if subblock_audit:
        for item in subblock_audit.get("subblock_audit", []):
            source_file = item.get("source_file")
            if source_file:
                source_files.setdefault(Path(source_file), []).append(item["subblock_name"])

    model_rows = []
    for macro in P0_MACROS + SECONDARY_MACROS:
        model_rows.append(
            _build_macro_row(
                macro=macro,
                files=all_files,
                leaf_rows=leaf_rows,
                subblock_audit=subblock_audit,
                source_files=source_files,
            )
        )

    p0_rows = [row for row in model_rows if row["macro_name"] in P0_MACROS]
    secondary_rows = [row for row in model_rows if row["macro_name"] in SECONDARY_MACROS]
    build_output_search = _build_output_search(model_rows)
    python_generator_search = _python_generator_search(model_rows)
    decision_table = [
        {
            "macro_name": row["macro_name"],
            "recovery_decision": row["recovery_decision"],
            "can_enter_model_characterization_plan": True,
            "can_enter_delay_chain_testbench_plan": _macro_opens_delay_chain(row),
            "can_claim_timing_proof_now": False,
        }
        for row in model_rows
    ]
    unblock_matrix = [
        {
            "macro_name": row["macro_name"],
            "blocks_timing_objects": row["blocks_timing_objects"],
            "recovery_decision": row["recovery_decision"],
            "has_usable_spice_now": row["has_usable_spice_now"],
            "has_usable_lib_now": row["has_usable_lib_now"],
            "has_equivalent_delay_model_now": row["has_equivalent_delay_model_now"],
        }
        for row in model_rows
    ]

    gen_delay_row = next(row for row in model_rows if row["macro_name"] == "gen_delay_inv")
    usable_model_found_for_all_p0 = all(
        row["recovery_decision"] == "usable_model_found" for row in p0_rows
    )
    recoverable_source_found_for_all_p0 = all(
        row["recovery_decision"]
        in {"usable_model_found", "recoverable_from_existing_spice", "recoverable_from_generator_source"}
        for row in p0_rows
    )

    audit_summary = {
        "generated_logic_model_recovery_inventory_available": True,
        "all_p0_macros_analyzed": len(p0_rows) == 3,
        "all_repo_model_sources_searched": True,
        "usable_model_found_for_all_p0": usable_model_found_for_all_p0,
        "recoverable_source_found_for_all_p0": recoverable_source_found_for_all_p0,
        "characterization_required_for_any_p0": any(row["requires_characterization"] for row in p0_rows),
        "can_enter_model_characterization_plan": True,
        "can_enter_delay_chain_testbench_plan": _macro_opens_delay_chain(gen_delay_row),
        "can_enter_timing_proof_now": False,
        "can_enter_physical_timing_closure_now": False,
        "can_enter_physical_routing_now": False,
        "can_enter_physical_placement_now": False,
        "can_generate_time_control_gds_now": False,
        "can_modify_standalone_now": False,
    }

    blockers = _dedupe(
        [
            f"{row['macro_name']}: {note}"
            for row in model_rows
            for note in row["notes"]
            if "missing" in note.lower() or "characterization" in note.lower() or "manual" in note.lower()
        ]
    )

    report = {
        "scope": "recover_generated_logic_spice_or_timing_model_inventory",
        "repo_root": str(root),
        "tech_dir": str(tech),
        "upstream_repo_root": str(upstream_repo_root),
        "openyield_root": str(openyield_root) if openyield_root.exists() else None,
        "audit_summary": audit_summary,
        "searched_roots": [str(path) for path in scanned_roots],
        "searched_extensions": sorted(SEARCH_EXTENSIONS),
        "input_reports_and_assets": {
            "timing_proof_plan": str(_resolve(root, timing_proof_plan_path)),
            "timing_metadata": str(_resolve(root, timing_metadata_path)),
            "asset_inventory": str(_resolve(root, asset_inventory_path)),
            "leaf_inventory": str(root / "docs" / "openyield_time_control_leaf_inventory_report.json"),
            "subblock_audit": str(root / "docs" / "openyield_time_control_subblock_audit_report.json"),
        },
        "p0_generated_logic_model_inventory": p0_rows,
        "secondary_macro_model_inventory": secondary_rows,
        "build_output_model_search": build_output_search,
        "python_generator_source_recovery_search": python_generator_search,
        "model_recovery_decision_table": decision_table,
        "timing_object_unblock_matrix": unblock_matrix,
        "blockers": blockers,
        "next_recommended_proof_task": _next_recommended_task(audit_summary),
        "boundary_assertions": {
            "path_found_is_not_usable_model": True,
            "spice_found_is_not_timing_characterized": True,
            "generator_source_found_is_not_recovered_model": True,
            "build_output_found_is_not_validated_model": True,
            "standalone_modified": False,
            "routing_modified": False,
            "gds_writer_modified": False,
        },
        "fallback_sources": {
            "filesystem_scan_used": True,
            "timing_plan_source_used": timing_plan.get("scope"),
            "timing_metadata_source_used": timing_metadata.get("scope"),
            "asset_inventory_source_used": asset_inventory.get("scope"),
            "leaf_inventory_source_used": leaf_inventory.get("scope") if leaf_inventory else None,
            "subblock_audit_source_used": subblock_audit.get("scope") if subblock_audit else None,
        },
    }
    graph = _build_graph(model_rows, audit_summary)
    return {"report": report, "graph": graph}


def _build_macro_row(
    macro: str,
    files: list[Path],
    leaf_rows: dict[str, Any],
    subblock_audit: dict[str, Any] | None,
    source_files: dict[Path, list[str]],
) -> dict[str, Any]:
    spec = MACRO_SPECS[macro]
    exact_matches = _find_paths_for_macro(files, macro)
    gds_paths = [str(path) for path in exact_matches if path.suffix.lower() == ".gds"]
    spice_paths = [str(path) for path in exact_matches if path.suffix.lower() in {".sp", ".spi", ".spice"}]
    cdl_paths = [str(path) for path in exact_matches if path.suffix.lower() in {".cdl", ".net"}]
    lib_paths = [str(path) for path in exact_matches if path.suffix.lower() == ".lib"]
    lef_paths = [str(path) for path in exact_matches if path.suffix.lower() == ".lef"]
    json_metadata_paths = [
        str(path)
        for path in exact_matches
        if path.suffix.lower() == ".json"
    ]
    build_output_paths = [str(path) for path in exact_matches if "build" in {part.lower() for part in path.parts}]
    python_generator_paths = _find_python_sources(files, macro, subblock_audit)

    subckt_info = _collect_subckt_info(spice_paths + cdl_paths)
    lib_info = _collect_lib_info(lib_paths)
    leaf = leaf_rows.get(macro)
    pin_list_if_found = _dedupe(
        subckt_info["pins"] + list(leaf.get("pin_labels", [])) if leaf else subckt_info["pins"]
    )
    power_pins_if_found = _dedupe(
        subckt_info["power_pins"]
        + (list(leaf.get("vdd_pins", [])) + list(leaf.get("gnd_pins", [])) if leaf else [])
    )
    recommended_gds = str(Path(leaf["gds_path"]).resolve()) if leaf else None
    matches_recommended_gds_variant = recommended_gds is not None and recommended_gds in gds_paths

    has_usable_spice_now = bool(spice_paths and macro not in P0_MACROS and bool(subckt_info["subckt_names"]))
    has_usable_lib_now = bool(lib_paths and bool(lib_info["cell_names"]))
    has_equivalent_delay_model_now = has_usable_lib_now

    can_recover_transistor_level_netlist = bool(spice_paths) or bool(python_generator_paths)
    can_recover_delay_model = has_usable_lib_now or has_usable_spice_now
    recovery_decision, recovery_source_type, can_recover_from_existing_repo, recovery_confidence = _recovery_decision(
        macro,
        spice_paths,
        lib_paths,
        python_generator_paths,
        gds_paths,
    )

    requires_manual_model_creation = recovery_decision not in {"usable_model_found", "recoverable_from_existing_spice"}
    requires_characterization = recovery_decision != "usable_model_found"
    next_action = _next_action(macro, recovery_decision)

    notes = [
        "path_found != usable_model",
        "spice_found != timing_characterized",
        "generator_source_found != recovered_model",
        "build_output_found != validated_model",
    ]
    if macro in P0_MACROS and not spice_paths and not lib_paths and python_generator_paths:
        notes.extend(
            [
                "Python/OpenYield generator source exists but no directly usable SPICE/LIB was found.",
                "Recovery still requires manual netlist materialization plus characterization.",
            ]
        )
    if macro in P0_MACROS and not spice_paths and not lib_paths and not python_generator_paths:
        notes.append("Only GDS/metadata evidence was found for this P0 macro.")
    if subblock_audit:
        for row in subblock_audit.get("subblock_audit", []):
            if macro in row.get("candidate_local_macros", []):
                notes.append(f"Referenced by TIME/control subblock {row['subblock_name']}.")
    if build_output_paths:
        notes.append("Build outputs contain name-matched artifacts; they are candidates only.")
    if recommended_gds and not matches_recommended_gds_variant:
        notes.append("Recommended future-planning GDS variant differs from one or more raw filename matches.")

    return {
        "macro_name": macro,
        "priority": spec["priority"],
        "role_in_time_control": spec["role_in_time_control"],
        "gds_paths": gds_paths,
        "spice_paths": spice_paths,
        "cdl_paths": cdl_paths,
        "lib_paths": lib_paths,
        "lef_paths": lef_paths,
        "python_generator_paths": python_generator_paths,
        "json_metadata_paths": json_metadata_paths,
        "build_output_paths": build_output_paths,
        "subckt_names_if_found": subckt_info["subckt_names"],
        "lib_cell_names_if_found": lib_info["cell_names"],
        "timing_arcs_if_found": lib_info["timing_arcs"],
        "pin_list_if_found": pin_list_if_found,
        "power_pins_if_found": power_pins_if_found,
        "matches_recommended_gds_variant": matches_recommended_gds_variant,
        "gds_exists": bool(gds_paths),
        "spice_exists": bool(spice_paths),
        "lib_exists": bool(lib_paths),
        "python_generator_exists": bool(python_generator_paths),
        "can_recover_transistor_level_netlist": can_recover_transistor_level_netlist,
        "can_recover_delay_model": can_recover_delay_model,
        "has_usable_spice_now": has_usable_spice_now,
        "has_usable_lib_now": has_usable_lib_now,
        "has_equivalent_delay_model_now": has_equivalent_delay_model_now,
        "can_recover_from_existing_repo": can_recover_from_existing_repo,
        "recovery_source_type": recovery_source_type,
        "recovery_confidence": recovery_confidence,
        "requires_manual_model_creation": requires_manual_model_creation,
        "requires_characterization": requires_characterization,
        "requires_pdk_device_models": True,
        "requires_testbench": True,
        "blocks_timing_objects": spec["blocks_timing_objects"],
        "next_action": next_action,
        "recovery_decision": recovery_decision,
        "can_enter_model_characterization_plan": True,
        "can_enter_delay_chain_testbench_plan": _macro_opens_delay_chain_for_fields(macro, recovery_decision),
        "can_claim_timing_proof_now": False,
        "notes": _dedupe(notes),
    }


def _find_paths_for_macro(files: list[Path], macro: str) -> list[Path]:
    out = []
    for path in files:
        stem = path.stem.lower()
        name = path.name.lower()
        text = str(path).lower()
        if stem == macro.lower() or name == f"{macro.lower()}{path.suffix.lower()}" or macro.lower() in text:
            out.append(path)
    return sorted(set(out))


def _find_python_sources(files: list[Path], macro: str, subblock_audit: dict[str, Any] | None) -> list[str]:
    hits = []
    if subblock_audit:
        for item in subblock_audit.get("subblock_audit", []):
            if macro in item.get("candidate_local_macros", []):
                source_file = item.get("source_file")
                if source_file and Path(source_file).suffix.lower() == ".py":
                    hits.append(str(Path(source_file)))
    for path in files:
        if path.suffix.lower() != ".py":
            continue
        text_path = str(path).lower()
        if "third_party\\openyield" not in text_path and "third_party/openyield" not in text_path:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if macro == "gen_delay_inv" and ("DelayChain" in text or "WenDelayChain" in text):
            hits.append(str(path))
        elif macro == "gen_inv" and "Pinv" in text:
            hits.append(str(path))
        elif macro == "gen_nand2" and ("AND2" in text or "AND3" in text or "PNAND3" in text):
            hits.append(str(path))
        elif macro in text:
            hits.append(str(path))
    return _dedupe(hits)


def _collect_subckt_info(paths: list[str]) -> dict[str, list[str]]:
    subckts: list[str] = []
    pins: list[str] = []
    power_pins: list[str] = []
    for raw in paths:
        path = Path(raw)
        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
        except OSError:
            continue
        for line in lines:
            match = SUBCKT_RE.match(line)
            if not match:
                continue
            subckt = match.group(1)
            pin_text = match.group(2).strip()
            pin_items = [item for item in re.split(r"\s+", pin_text) if item]
            subckts.append(subckt)
            pins.extend(pin_items)
            power_pins.extend([item for item in pin_items if item.lower() in {"vdd", "vss", "gnd", "vccd", "vssd"}])
    return {"subckt_names": _dedupe(subckts), "pins": _dedupe(pins), "power_pins": _dedupe(power_pins)}


def _collect_lib_info(paths: list[str]) -> dict[str, list[str]]:
    cells: list[str] = []
    arcs: list[str] = []
    for raw in paths:
        path = Path(raw)
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        cells.extend(LIB_CELL_RE.findall(text))
        if TIMING_RE.search(text):
            arcs.append("timing() block present")
        arcs.extend([f"related_pin:{pin}" for pin in RELATED_PIN_RE.findall(text)])
    return {"cell_names": _dedupe(cells), "timing_arcs": _dedupe(arcs)}


def _recovery_decision(
    macro: str,
    spice_paths: list[str],
    lib_paths: list[str],
    python_generator_paths: list[str],
    gds_paths: list[str],
) -> tuple[str, str, bool | str, str]:
    if len(spice_paths) > 1 and macro in P0_MACROS:
        return "conflicting_model_candidates", "multiple_spice_candidates", False, "low"
    if lib_paths:
        return "usable_model_found", "liberty_model", True, "high"
    if spice_paths and macro not in P0_MACROS:
        return "recoverable_from_existing_spice", "existing_spice_only", True, "medium"
    if spice_paths and macro in P0_MACROS:
        return "recoverable_from_existing_spice", "existing_spice_only", True, "medium"
    if python_generator_paths:
        return "recoverable_from_generator_source", "generator_source_only", "partial", "medium"
    if gds_paths:
        return "metadata_only_no_recovery_source", "gds_metadata_only", False, "low"
    return "metadata_only_no_recovery_source", "no_source_found", False, "low"


def _next_action(macro: str, decision: str) -> str:
    if decision == "usable_model_found":
        return "confirm_model_scope_and_pin_order"
    if decision == "recoverable_from_existing_spice":
        return "plan_characterization_from_existing_spice"
    if decision == "recoverable_from_generator_source":
        return "materialize_transistor_level_netlist_then_characterize"
    if decision == "conflicting_model_candidates":
        return "review_conflicting_candidates_manually"
    if macro in P0_MACROS:
        return "manual_model_creation_and_characterization_required"
    return "characterization_plan_required"


def _build_output_search(model_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows = []
    for item in model_rows:
        for path in item["build_output_paths"]:
            suffix = Path(path).suffix.lower()
            rows.append(
                {
                    "macro_name": item["macro_name"],
                    "candidate_model_path": path,
                    "candidate_origin": "build_output",
                    "matches_macro_name": Path(path).stem.lower() == item["macro_name"].lower(),
                    "matches_pin_order": False,
                    "has_power_pins": bool(item["power_pins_if_found"]),
                    "usable_without_conversion": False,
                    "conversion_needed": suffix not in {".sp", ".spi", ".spice", ".cdl", ".lib"},
                    "risk": "candidate_only_not_validated",
                }
            )
    return rows


def _python_generator_search(model_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "macro_name": item["macro_name"],
            "python_generator_paths": item["python_generator_paths"],
            "python_generator_exists": item["python_generator_exists"],
            "recovery_source_type": item["recovery_source_type"],
            "can_recover_transistor_level_netlist": item["can_recover_transistor_level_netlist"],
            "requires_manual_model_creation": item["requires_manual_model_creation"],
            "requires_characterization": item["requires_characterization"],
        }
        for item in model_rows
        if item["python_generator_paths"]
    ]


def _macro_opens_delay_chain(row: dict[str, Any]) -> bool:
    return bool(row["macro_name"] == "gen_delay_inv" and row["recovery_decision"] in {"usable_model_found", "recoverable_from_existing_spice", "recoverable_from_generator_source"})


def _macro_opens_delay_chain_for_fields(macro: str, decision: str) -> bool:
    return bool(macro == "gen_delay_inv" and decision in {"usable_model_found", "recoverable_from_existing_spice", "recoverable_from_generator_source"})


def _next_recommended_task(summary: dict[str, Any]) -> str:
    if summary["can_enter_delay_chain_testbench_plan"]:
        return "delay_chain_spice_testbench_plan"
    return "gen_inv_gen_nand2_gen_delay_inv_characterization_plan"


def _build_graph(model_rows: list[dict[str, Any]], summary: dict[str, Any]) -> dict[str, Any]:
    nodes = [{"id": "generated_logic_inventory", "kind": "root"}]
    edges = []
    for row in model_rows:
        macro_id = f"macro:{row['macro_name']}"
        nodes.append({"id": macro_id, "kind": "macro", "label": row["macro_name"]})
        edges.append({"from": "generated_logic_inventory", "to": macro_id, "relation": "inventoried"})
        for target in row["blocks_timing_objects"]:
            target_id = f"timing:{target}"
            if not any(node["id"] == target_id for node in nodes):
                nodes.append({"id": target_id, "kind": "timing_object", "label": target})
            edges.append({"from": macro_id, "to": target_id, "relation": "blocks"})
    return {"scope": "recover_generated_logic_spice_or_timing_model_inventory", "nodes": nodes, "edges": edges, "summary": summary}


def format_generated_logic_model_recovery_markdown(report: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# OpenYield Generated Logic Model Recovery Report",
            "",
            f"- Scope: `{report['scope']}`",
            f"- Repo root: `{report['repo_root']}`",
            f"- Tech dir: `{report['tech_dir']}`",
            "",
            "## Audit Summary",
            "",
            "```json",
            json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Searched Roots And Extensions",
            "",
            "```json",
            json.dumps(
                {
                    "searched_roots": report["searched_roots"],
                    "searched_extensions": report["searched_extensions"],
                },
                ensure_ascii=False,
                indent=2,
            ),
            "```",
            "",
            "## P0 Generated Logic Model Inventory",
            "",
            _md_table(
                ["macro", "decision", "spice", "lib", "generator", "recover_from_repo", "next_action"],
                [
                    [
                        row["macro_name"],
                        row["recovery_decision"],
                        row["has_usable_spice_now"],
                        row["has_usable_lib_now"],
                        row["python_generator_exists"],
                        row["can_recover_from_existing_repo"],
                        row["next_action"],
                    ]
                    for row in report["p0_generated_logic_model_inventory"]
                ],
            ),
            "",
            "## Secondary Macro Model Inventory",
            "",
            _md_table(
                ["macro", "decision", "spice", "lib", "recover_from_repo", "next_action"],
                [
                    [
                        row["macro_name"],
                        row["recovery_decision"],
                        row["has_usable_spice_now"],
                        row["has_usable_lib_now"],
                        row["can_recover_from_existing_repo"],
                        row["next_action"],
                    ]
                    for row in report["secondary_macro_model_inventory"]
                ],
            ),
            "",
            "## Build Output Model Search",
            "",
            _md_table(
                ["macro", "candidate", "match_name", "usable_without_conversion", "risk"],
                [
                    [
                        row["macro_name"],
                        row["candidate_model_path"],
                        row["matches_macro_name"],
                        row["usable_without_conversion"],
                        row["risk"],
                    ]
                    for row in report["build_output_model_search"]
                ],
            ) if report["build_output_model_search"] else "- none",
            "",
            "## Python Generator / Source Recovery Search",
            "",
            _md_table(
                ["macro", "generator_exists", "source_type", "recover_transistor_level_netlist", "requires_characterization"],
                [
                    [
                        row["macro_name"],
                        row["python_generator_exists"],
                        row["recovery_source_type"],
                        row["can_recover_transistor_level_netlist"],
                        row["requires_characterization"],
                    ]
                    for row in report["python_generator_source_recovery_search"]
                ],
            ) if report["python_generator_source_recovery_search"] else "- none",
            "",
            "## Model Recovery Decision Table",
            "",
            _md_table(
                ["macro", "decision", "characterization_plan", "delay_chain_testbench_plan", "timing_proof_now"],
                [
                    [
                        row["macro_name"],
                        row["recovery_decision"],
                        row["can_enter_model_characterization_plan"],
                        row["can_enter_delay_chain_testbench_plan"],
                        row["can_claim_timing_proof_now"],
                    ]
                    for row in report["model_recovery_decision_table"]
                ],
            ),
            "",
            "## Timing Object Unblock Matrix",
            "",
            _md_table(
                ["macro", "blocks", "decision", "usable_spice", "usable_lib", "equiv_delay_model"],
                [
                    [
                        row["macro_name"],
                        ", ".join(row["blocks_timing_objects"]),
                        row["recovery_decision"],
                        row["has_usable_spice_now"],
                        row["has_usable_lib_now"],
                        row["has_equivalent_delay_model_now"],
                    ]
                    for row in report["timing_object_unblock_matrix"]
                ],
            ),
            "",
            "## Blockers",
            "",
            _list_block(report["blockers"]),
            "",
            "## Boundary Assertions",
            "",
            "```json",
            json.dumps(report["boundary_assertions"], ensure_ascii=False, indent=2),
            "```",
            "",
            "## Next Recommended Proof Task",
            "",
            f"- `{report['next_recommended_proof_task']}`",
        ]
    )


def _scan_files(roots: list[Path]) -> list[Path]:
    out = []
    for root in roots:
        if not root.exists():
            continue
        if root.is_file():
            if root.suffix.lower() in SEARCH_EXTENSIONS:
                out.append(root.resolve())
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in SEARCH_EXTENSIONS:
                out.append(path.resolve())
    return sorted(set(out))


def _resolve(root: Path, path: str | Path) -> Path:
    p = Path(path)
    if p.is_absolute():
        return p
    return (root / p).resolve()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _optional_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return _load_json(path)


def _md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(lines)


def _list_block(items: list[str]) -> str:
    if not items:
        return "- none"
    return "\n".join(f"- {item}" for item in items)


def _dedupe(items: list[str]) -> list[str]:
    seen = set()
    out = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out
