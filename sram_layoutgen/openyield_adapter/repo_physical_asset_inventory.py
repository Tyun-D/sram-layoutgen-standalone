"""Readonly repository physical asset inventory for OpenYield/OpenRAM evidence collection.

This module scans the current standalone-generator repository for physical-layout
assets and related evidence without modifying placement, routing, or GDS flows.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from .gds_pin_audit import read_gds_labels_and_shapes


FOCUS_MACROS = (
    "gen_precharge",
    "gen_inv",
    "gen_nand2",
    "gen_delay_inv",
    "dff",
    "sense_amp",
    "write_driver",
    "gen_wl_driver",
    "gen_col_mux",
    "gen_col_mux_vdd_labeled",
    "cell_1rw",
    "dummy_cell_1rw",
    "replica_cell_1rw",
)

OPENRAM_OUTPUT_EXTENSIONS = {".gds", ".sp", ".spi", ".cdl", ".v", ".sv", ".lef", ".log", ".lyrdb", ".json", ".md"}
NETLIST_EXTENSIONS = {".sp", ".spi", ".spice", ".cdl", ".net"}
TECH_EXTENSIONS = {".lef", ".lib", ".lydrc", ".drc", ".lyp", ".lyt"}


def build_repo_physical_asset_inventory(repo_root: str | Path) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    tech_dir = root / "technology" / "freepdk45"
    docs_dir = root / "docs"
    build_dir = root / "build"
    gds_lib = tech_dir / "gds_lib"
    sp_lib = tech_dir / "sp_lib"
    replacement_path = tech_dir / "replacement_macros.json"
    aliases_path = tech_dir / "openyield_macro_aliases.json"

    replacement = _load_json(replacement_path).get("macros", [])
    aliases = _load_json(aliases_path).get("aliases", [])
    replacement_by_name = {str(item.get("name")): item for item in replacement if item.get("name")}
    alias_by_macro = defaultdict(list)
    for item in aliases:
        macro_name = str(item.get("macro_name") or "")
        if macro_name:
            alias_by_macro[macro_name].append(item)

    hardcell_inventory = _collect_hardcell_inventory(gds_lib, replacement_by_name, alias_by_macro)
    spice_inventory = _collect_spice_inventory(root, hardcell_inventory)
    tech_inventory = _collect_tech_inventory(tech_dir)
    drc_inventory = _collect_drc_inventory(root)
    output_inventory = _collect_generated_output_inventory(build_dir)
    layout_inventory = _collect_layout_readonly_inventory(root)
    time_inventory = _collect_time_metadata_inventory(docs_dir)
    graph = _build_graph(root, hardcell_inventory, spice_inventory, tech_inventory, drc_inventory, output_inventory, layout_inventory)

    hardcell_gds_available = bool(hardcell_inventory["items"])
    spice_available = bool(spice_inventory["items"])
    tech_available = bool(tech_inventory["items"])
    drc_available = any(item["path"].endswith(".lydrc") or item["path"].endswith(".drc") for item in drc_inventory["items"])
    outputs_available = bool(output_inventory["items"])
    layout_writer_available = any(item["component"] == "gds_writer" for item in layout_inventory["items"])
    routing_available = any(item["component"] == "routing" for item in layout_inventory["items"])
    standalone_available = any(item["component"] == "standalone" for item in layout_inventory["items"])

    can_hardcell_power = hardcell_gds_available and tech_available and drc_available
    can_legal_placement = hardcell_gds_available and tech_available and standalone_available
    can_routing_obstacle = tech_available and routing_available and standalone_available
    can_timing_metadata = bool(time_inventory["items"])

    missing_assets = _build_missing_assets(
        hardcell_gds_available,
        spice_available,
        tech_available,
        drc_available,
        outputs_available,
        layout_writer_available,
        routing_available,
        standalone_available,
        hardcell_inventory,
    )
    usable_assets = _build_usable_assets_for_next_proof(hardcell_inventory, tech_inventory, drc_inventory, layout_inventory, time_inventory)
    next_tasks = _rank_next_tasks(can_hardcell_power, hardcell_gds_available, drc_available, can_legal_placement, can_routing_obstacle, can_timing_metadata)

    recommended_next_goal = "hardcell_power_rail_continuity_readonly_audit"
    if not hardcell_gds_available:
        recommended_next_goal = "hardcell_asset_path_recovery"
    elif not drc_available:
        recommended_next_goal = "hardcell_gds_pin_rail_geometry_inventory"

    report = {
        "scope": "repo_physical_asset_discovery_readonly_evidence_collection",
        "repo_root": str(root),
        "searched_roots": [str(root), str(tech_dir), str(docs_dir), str(build_dir)],
        "searched_extensions": sorted(OPENRAM_OUTPUT_EXTENSIONS | NETLIST_EXTENSIONS | TECH_EXTENSIONS | {".py", ".tcl", ".rb"}),
        "hardcell_macro_gds_inventory": hardcell_inventory,
        "spice_cdl_inventory": spice_inventory,
        "lef_tech_inventory": tech_inventory,
        "drc_klayout_verification_inventory": drc_inventory,
        "openram_generated_output_inventory": output_inventory,
        "layout_writer_routing_standalone_readonly_inventory": layout_inventory,
        "timing_metadata_inventory": time_inventory,
        "missing_assets": missing_assets,
        "usable_assets_for_next_proof": usable_assets,
        "ranked_next_tasks": next_tasks,
        "recommended_next_goal": recommended_next_goal,
        "hardcell_power_rail_continuity_readonly_audit_inputs": _hardcell_power_inputs(hardcell_inventory, drc_inventory, tech_dir),
        "decision_flags": {
            "repo_physical_asset_inventory_available": True,
            "hardcell_gds_inventory_available": hardcell_gds_available,
            "spice_inventory_available": spice_available,
            "lef_or_tech_inventory_available": tech_available,
            "drc_deck_inventory_available": drc_available,
            "openram_generated_output_inventory_available": outputs_available,
            "layout_writer_inventory_available": layout_writer_available,
            "routing_inventory_available": routing_available,
            "standalone_inventory_available": standalone_available,
            "can_enter_hardcell_power_rail_continuity_readonly_audit": can_hardcell_power,
            "can_enter_legal_placement_readonly_audit": can_legal_placement,
            "can_enter_routing_obstacle_readonly_audit": can_routing_obstacle,
            "can_enter_timing_metadata_inventory": can_timing_metadata,
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "boundary_assertions": {
            "standalone_modified": False,
            "routing_modified": False,
            "gds_writer_modified": False,
            "legacy_path_unchanged": True,
        },
        "notes": [
            "This inventory is filesystem-driven and read-only.",
            "Locating GDS/SPICE/DRC assets is evidence of asset presence, not proof of rail continuity, routing correctness, DRC clean, or LVS clean.",
            "TIME/control physical placement and GDS generation remain blocked by the current metadata-only boundary.",
        ],
    }
    return {"report": report, "graph": graph}


def _collect_hardcell_inventory(
    gds_lib: Path,
    replacement_by_name: dict[str, dict[str, Any]],
    alias_by_macro: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    all_gds = sorted(gds_lib.rglob("*.gds")) if gds_lib.exists() else []
    for path in all_gds:
        macro_name = path.stem
        labels, bbox, notes = _gds_metadata(path)
        replacement = replacement_by_name.get(macro_name)
        aliases = alias_by_macro.get(macro_name, [])
        known_power_labels = [label for label in labels if label.lower() in {"vdd", "gnd", "vss", "vpwr", "vgnd"}]
        binding_sources = []
        if replacement:
            binding_sources.append("replacement_macros.json")
        if aliases:
            binding_sources.append("openyield_macro_aliases.json")
        if "openyield_repaired" in path.parts:
            binding_sources.append("openyield_repaired_gds")
        if "openram_replacements" in path.parts:
            binding_sources.append("openram_replacements_gds")
        item = {
            "macro_name": macro_name,
            "gds_path": str(path),
            "gds_exists": path.exists(),
            "source_of_binding": binding_sources or ["filesystem_scan"],
            "known_labels": labels[:24],
            "known_power_labels": known_power_labels,
            "vdd_known": any(label.lower() == "vdd" for label in labels),
            "gnd_known": any(label.lower() in {"gnd", "vss"} for label in labels),
            "pin_side_known": False,
            "bbox_known": bbox is not None,
            "bbox": bbox,
            "role_guess": _macro_role_guess(macro_name, path),
            "focus_macro": macro_name in FOCUS_MACROS,
            "openyield_bindings": [str(entry.get("openyield_module")) for entry in aliases if entry.get("openyield_module")],
            "replacement_binding_present": replacement is not None,
            "notes": notes,
        }
        items.append(item)
    focus_missing = [name for name in FOCUS_MACROS if not any(item["macro_name"] == name for item in items)]
    return {
        "root": str(gds_lib),
        "count": len(items),
        "focus_macros": list(FOCUS_MACROS),
        "focus_missing": focus_missing,
        "items": items,
    }


def _collect_spice_inventory(root: Path, hardcell_inventory: dict[str, Any]) -> dict[str, Any]:
    gds_names = {item["macro_name"] for item in hardcell_inventory["items"]}
    items: list[dict[str, Any]] = []
    tech_root = root / "technology"
    for path in sorted(p for p in tech_root.rglob("*") if p.is_file() and p.suffix.lower() in NETLIST_EXTENSIONS):
        subckt_name, pins = _parse_subckt(path)
        macro_name = path.stem
        items.append(
            {
                "cell_or_macro": macro_name,
                "spice_path": str(path),
                "spice_exists": True,
                "subckt_name": subckt_name,
                "pins_if_parseable": pins,
                "power_pins_if_parseable": [pin for pin in pins if pin.lower() in {"vdd", "gnd", "vss", "vpwr", "vgnd"}],
                "matches_gds_macro_name": macro_name in gds_names or subckt_name in gds_names,
                "notes": [] if subckt_name else ["No .subckt header parsed from file."],
            }
        )
    return {"count": len(items), "items": items}


def _collect_tech_inventory(tech_root: Path) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    for path in sorted(p for p in tech_root.rglob("*") if p.is_file() and p.suffix.lower() in TECH_EXTENSIONS):
        suffix = path.suffix.lower()
        items.append(
            {
                "asset_type": _tech_asset_type(path),
                "path": str(path),
                "exists": True,
                "relevant_layers": _guess_relevant_layers(path),
                "pin_layer_info_available": suffix in {".lef", ".lyp", ".lyt", ".lydrc"},
                "routing_layer_info_available": suffix in {".lef", ".lyp", ".lyt", ".lydrc", ".drc"},
                "notes": [],
            }
        )
    return {"count": len(items), "items": items}


def _collect_drc_inventory(root: Path) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    patterns = ("*drc*", "*lvs*", "*klayout*", "*signoff*")
    matched: set[Path] = set()
    for pattern in patterns:
        matched.update(path for path in root.rglob(pattern) if path.is_file())
    for path in sorted(matched):
        suffix = path.suffix.lower()
        items.append(
            {
                "tool_or_deck": _verification_role(path),
                "path": str(path),
                "exists": True,
                "used_before": "docs" in path.parts or "build" in path.parts,
                "target_technology": "freepdk45" if "freepdk45" in str(path).lower() else "unknown",
                "can_run_readonly": suffix in {".lydrc", ".drc", ".rb", ".ps1", ".py"},
                "requires_gds_input": suffix in {".lydrc", ".drc", ".rb", ".ps1"},
                "notes": [],
            }
        )
    return {"count": len(items), "items": items}


def _collect_generated_output_inventory(build_dir: Path) -> dict[str, Any]:
    items: list[dict[str, Any]] = []
    counts_by_ext: Counter[str] = Counter()
    counts_by_dir: Counter[str] = Counter()
    if build_dir.exists():
        for path in sorted(p for p in build_dir.rglob("*") if p.is_file() and p.suffix.lower() in OPENRAM_OUTPUT_EXTENSIONS):
            rel_parent = path.parent.relative_to(build_dir).as_posix() if path.parent != build_dir else "."
            counts_by_ext[path.suffix.lower()] += 1
            counts_by_dir[rel_parent] += 1
            items.append(
                {
                    "output_name": path.stem,
                    "path": str(path),
                    "type": path.suffix.lower().lstrip("."),
                    "config_if_known": _config_from_name(path.name),
                    "area_if_known": None,
                    "drc_if_known": "marker_report" if path.suffix.lower() == ".lyrdb" else None,
                    "notes": [],
                }
            )
    return {
        "root": str(build_dir),
        "count": len(items),
        "counts_by_extension": dict(sorted(counts_by_ext.items())),
        "top_output_directories": counts_by_dir.most_common(20),
        "items": items[:200],
        "truncated": len(items) > 200,
        "total_item_count": len(items),
    }


def _collect_layout_readonly_inventory(root: Path) -> dict[str, Any]:
    components = [
        ("standalone", root / "sram_layoutgen" / "standalone.py", "top-level generator / integration entry"),
        ("gds_writer", root / "sram_layoutgen" / "gds_writer.py", "GDS emission"),
        ("lef_writer", root / "sram_layoutgen" / "lef_writer.py", "LEF writer"),
        ("routing", root / "sram_layoutgen" / "geometry.py", "geometry primitives used by routing/layout"),
        ("routing", root / "sram_layoutgen" / "verifier.py", "route/connectivity verification entry"),
        ("signoff", root / "sram_layoutgen" / "signoff.py", "external DRC/LVS helpers"),
        ("placement", root / "sram_layoutgen" / "openram_placement.py", "OpenRAM-style placement"),
        ("power_stitch_script", root / "scripts" / "openyield_storage_only_gds_smoke.py", "storage-only smoke/export"),
        ("power_stitch_script", root / "scripts" / "openyield_storage_only_drc_smoke.py", "storage-only DRC smoke"),
        ("time_control_readonly", root / "scripts" / "openyield_time_control_final_boundary_summary.py", "TIME/control boundary summary"),
    ]
    items = []
    for component, path, role in components:
        items.append(
            {
                "component": component,
                "path": str(path),
                "role_guess": role,
                "read_only_inspected": path.exists(),
                "modified": False,
                "notes": [] if path.exists() else ["Path not found during inventory scan."],
            }
        )
    return {"count": len(items), "items": items}


def _collect_time_metadata_inventory(docs_dir: Path) -> dict[str, Any]:
    items = []
    for path in sorted(docs_dir.glob("openyield_time_control*_report.json")):
        items.append({"name": path.name, "path": str(path), "kind": "time_control_report"})
    return {"count": len(items), "items": items}


def _build_graph(
    root: Path,
    hardcell_inventory: dict[str, Any],
    spice_inventory: dict[str, Any],
    tech_inventory: dict[str, Any],
    drc_inventory: dict[str, Any],
    output_inventory: dict[str, Any],
    layout_inventory: dict[str, Any],
) -> dict[str, Any]:
    nodes: list[dict[str, Any]] = [{"id": "repo_root", "label": str(root), "kind": "root"}]
    edges: list[dict[str, str]] = []

    category_nodes = {
        "hardcell_gds": "Hardcell/Macro GDS",
        "spice": "SPICE/CDL/Netlist",
        "tech": "LEF/Tech",
        "drc": "DRC/KLayout/Verification",
        "outputs": "Generated Outputs",
        "layout": "Layout/Writer/Routing",
    }
    for node_id, label in category_nodes.items():
        nodes.append({"id": node_id, "label": label, "kind": "category"})
        edges.append({"from": "repo_root", "to": node_id, "relation": "contains"})

    for index, item in enumerate(hardcell_inventory["items"]):
        node_id = f"gds:{index}:{item['macro_name']}"
        nodes.append({"id": node_id, "label": item["macro_name"], "kind": "gds_macro", "path": item["gds_path"]})
        edges.append({"from": "hardcell_gds", "to": node_id, "relation": "contains"})
    for item in spice_inventory["items"]:
        node_id = f"spice:{item['cell_or_macro']}"
        nodes.append({"id": node_id, "label": item["cell_or_macro"], "kind": "spice_macro", "path": item["spice_path"]})
        edges.append({"from": "spice", "to": node_id, "relation": "contains"})
        if item["matches_gds_macro_name"]:
            for index, gds_item in enumerate(hardcell_inventory["items"]):
                if gds_item["macro_name"] == item["cell_or_macro"]:
                    edges.append({"from": f"gds:{index}:{gds_item['macro_name']}", "to": node_id, "relation": "paired_with"})
    for item in tech_inventory["items"][:40]:
        node_id = f"tech:{Path(item['path']).name}"
        nodes.append({"id": node_id, "label": Path(item["path"]).name, "kind": "tech_asset", "path": item["path"]})
        edges.append({"from": "tech", "to": node_id, "relation": "contains"})
    for item in drc_inventory["items"][:40]:
        node_id = f"drc:{Path(item['path']).name}"
        nodes.append({"id": node_id, "label": Path(item["path"]).name, "kind": "verification_asset", "path": item["path"]})
        edges.append({"from": "drc", "to": node_id, "relation": "contains"})
    for item in output_inventory["items"][:60]:
        node_id = f"out:{Path(item['path']).name}"
        nodes.append({"id": node_id, "label": Path(item["path"]).name, "kind": "generated_output", "path": item["path"]})
        edges.append({"from": "outputs", "to": node_id, "relation": "contains"})
    for item in layout_inventory["items"]:
        node_id = f"layout:{item['component']}:{Path(item['path']).name}"
        nodes.append({"id": node_id, "label": Path(item["path"]).name, "kind": "layout_asset", "path": item["path"]})
        edges.append({"from": "layout", "to": node_id, "relation": "contains"})
    return {"nodes": nodes, "edges": edges}


def _build_missing_assets(
    hardcell_gds_available: bool,
    spice_available: bool,
    tech_available: bool,
    drc_available: bool,
    outputs_available: bool,
    layout_writer_available: bool,
    routing_available: bool,
    standalone_available: bool,
    hardcell_inventory: dict[str, Any],
) -> list[dict[str, Any]]:
    missing = []
    if not hardcell_gds_available:
        missing.append({"asset": "hardcell_gds", "reason": "No hardcell GDS files were found under technology/freepdk45/gds_lib."})
    if hardcell_inventory["focus_missing"]:
        missing.append({"asset": "focus_macro_gds", "reason": f"Missing focus macros: {', '.join(hardcell_inventory['focus_missing'])}"})
    if not spice_available:
        missing.append({"asset": "spice_inventory", "reason": "No SPICE/CDL/netlist files were found."})
    if not tech_available:
        missing.append({"asset": "lef_or_tech_inventory", "reason": "No LEF/lib/tech deck assets were found."})
    if not drc_available:
        missing.append({"asset": "drc_deck_inventory", "reason": "No .lydrc or .drc deck was found."})
    if not outputs_available:
        missing.append({"asset": "openram_generated_outputs", "reason": "No generated build outputs were found."})
    if not layout_writer_available:
        missing.append({"asset": "layout_writer", "reason": "No gds_writer.py file was found."})
    if not routing_available:
        missing.append({"asset": "routing", "reason": "No routing-related entry file was found."})
    if not standalone_available:
        missing.append({"asset": "standalone", "reason": "No standalone.py file was found."})
    return missing


def _build_usable_assets_for_next_proof(
    hardcell_inventory: dict[str, Any],
    tech_inventory: dict[str, Any],
    drc_inventory: dict[str, Any],
    layout_inventory: dict[str, Any],
    time_inventory: dict[str, Any],
) -> dict[str, Any]:
    focus_macros = [item for item in hardcell_inventory["items"] if item["focus_macro"]]
    drc_decks = [item for item in drc_inventory["items"] if item["path"].endswith(".lydrc") or item["path"].endswith(".drc")]
    return {
        "hardcell_focus_macros": [{"macro_name": item["macro_name"], "gds_path": item["gds_path"]} for item in focus_macros],
        "drc_decks": [{"tool_or_deck": item["tool_or_deck"], "path": item["path"]} for item in drc_decks],
        "tech_assets": [{"asset_type": item["asset_type"], "path": item["path"]} for item in tech_inventory["items"]],
        "layout_entrypoints": [{"component": item["component"], "path": item["path"]} for item in layout_inventory["items"] if item["read_only_inspected"]],
        "time_metadata_reports": time_inventory["items"][:12],
    }


def _rank_next_tasks(
    can_hardcell_power: bool,
    hardcell_gds_available: bool,
    drc_available: bool,
    can_legal_placement: bool,
    can_routing_obstacle: bool,
    can_timing_metadata: bool,
) -> list[dict[str, Any]]:
    tasks = []
    tasks.append(
        {
            "task": "hardcell_power_rail_continuity_readonly_audit",
            "rank": 1,
            "ready": can_hardcell_power,
            "reason": "Hardcell GDS plus technology and DRC deck are present." if can_hardcell_power else "Needs both hardcell GDS and a readable DRC deck.",
        }
    )
    tasks.append(
        {
            "task": "time_control_leaf_bbox_pin_side_inventory",
            "rank": 2,
            "ready": hardcell_gds_available,
            "reason": "Hardcell GDS and pin labels are present for readonly geometry inventory." if hardcell_gds_available else "Hardcell GDS paths are missing.",
        }
    )
    tasks.append(
        {
            "task": "time_control_composite_internal_placement_feasibility_audit",
            "rank": 3,
            "ready": can_legal_placement,
            "reason": "Placement readonly entrypoints and tech assets are locatable." if can_legal_placement else "Need standalone/placement entrypoints plus tech assets.",
        }
    )
    tasks.append(
        {
            "task": "time_control_route_obstacle_inventory",
            "rank": 4,
            "ready": can_routing_obstacle,
            "reason": "Routing-related code and tech assets are locatable." if can_routing_obstacle else "Need routing entrypoints plus tech assets.",
        }
    )
    tasks.append(
        {
            "task": "delay_chain_timing_metadata_inventory",
            "rank": 5,
            "ready": can_timing_metadata,
            "reason": "TIME/control metadata reports already exist for readonly follow-up." if can_timing_metadata else "TIME/control metadata reports are missing.",
        }
    )
    if hardcell_gds_available and not drc_available:
        tasks.insert(
            0,
            {
                "task": "hardcell_gds_pin_rail_geometry_inventory",
                "rank": 0,
                "ready": True,
                "reason": "Hardcell GDS exists even though no DRC deck was found.",
            },
        )
    if not hardcell_gds_available:
        tasks.insert(
            0,
            {
                "task": "hardcell_asset_path_recovery",
                "rank": 0,
                "ready": True,
                "reason": "Hardcell GDS files are missing, so path recovery comes first.",
            },
        )
    return tasks


def _hardcell_power_inputs(hardcell_inventory: dict[str, Any], drc_inventory: dict[str, Any], tech_dir: Path) -> dict[str, Any]:
    decks = [item["path"] for item in drc_inventory["items"] if item["path"].endswith(".lydrc") or item["path"].endswith(".drc")]
    focus = [item for item in hardcell_inventory["items"] if item["macro_name"] in {"cell_1rw", "dummy_cell_1rw", "replica_cell_1rw", "sense_amp", "write_driver", "gen_wl_driver", "gen_col_mux"}]
    return {
        "tech_dir": str(tech_dir),
        "drc_decks": decks,
        "macro_gds_inputs": [{"macro_name": item["macro_name"], "gds_path": item["gds_path"]} for item in focus],
    }


def _gds_metadata(path: Path) -> tuple[list[str], dict[str, float] | None, list[str]]:
    notes: list[str] = []
    try:
        labels, _shapes, bbox = read_gds_labels_and_shapes(path)
        label_names = sorted({label.text for label in labels})
        return label_names, bbox.to_dict() if bbox else None, notes
    except Exception as exc:
        notes.append(f"GDS label/bbox read failed: {exc}")
        return [], None, notes


def _parse_subckt(path: Path) -> tuple[str | None, list[str]]:
    try:
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            text = line.strip()
            if not text or text.startswith("*"):
                continue
            parts = text.split()
            if parts and parts[0].lower() == ".subckt" and len(parts) > 2:
                return parts[1], parts[2:]
    except Exception:
        return None, []
    return None, []


def _macro_role_guess(macro_name: str, path: Path) -> str:
    name = macro_name.lower()
    if name.startswith("cell_"):
        return "bitcell"
    if name.startswith("dummy_cell"):
        return "dummy_bitcell"
    if name.startswith("replica_cell"):
        return "replica_bitcell"
    if "sense" in name:
        return "sense_amp"
    if "write" in name:
        return "write_driver"
    if "dff" in name:
        return "dff"
    if "wl_driver" in name:
        return "wordline_driver"
    if "precharge" in name:
        return "precharge"
    if "col_mux" in name:
        return "column_mux"
    if "openram_replacements" in path.parts:
        return "replacement_macro"
    return "hard_macro"


def _tech_asset_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".lef":
        return "lef"
    if suffix == ".lib":
        return "timing_lib"
    if suffix in {".lydrc", ".drc"}:
        return "drc_deck"
    if suffix == ".lyp":
        return "klayout_layer_props"
    if suffix == ".lyt":
        return "klayout_tech"
    return "tech_asset"


def _guess_relevant_layers(path: Path) -> list[str]:
    text = path.name.lower()
    layers = []
    if any(key in text for key in ("lef", "lydrc", "drc", "lyp", "lyt")):
        layers.extend(["m1", "m2", "via1", "poly", "active"])
    return layers


def _verification_role(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".lydrc") or name.endswith(".drc"):
        return "drc_deck"
    if name.endswith(".lyrdb"):
        return "drc_report"
    if "lvs" in name:
        return "lvs_asset"
    if "signoff" in name:
        return "signoff_script_or_report"
    if "klayout" in name:
        return "klayout_helper"
    return "verification_asset"


def _config_from_name(name: str) -> str | None:
    lower = name.lower()
    tokens = []
    for token in lower.replace(".", "_").split("_"):
        if token.startswith(("wpr", "x")) or token.isdigit():
            tokens.append(token)
    return "_".join(tokens) or None


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def format_repo_physical_asset_inventory_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Repo Physical Asset Inventory",
        "",
        "This report stays in readonly evidence-collection mode. It inventories filesystem assets and prepares the next proof tasks without modifying standalone integration, routing, or GDS writing.",
        "",
        "## Audit Summary",
        "",
        f"- repo root: `{report['repo_root']}`",
        f"- searched roots: `{json.dumps(report['searched_roots'], ensure_ascii=False)}`",
        f"- searched extensions: `{json.dumps(report['searched_extensions'], ensure_ascii=False)}`",
        f"- recommended next goal: `{report['recommended_next_goal']}`",
        "",
        "## Decision Flags",
        "",
        "```json",
        json.dumps(report["decision_flags"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Hardcell / Macro GDS Inventory",
        "",
        md_table(
            ["macro", "role", "gds exists", "bbox known", "vdd", "gnd", "bindings", "openyield bindings", "path"],
            [
                [
                    item["macro_name"],
                    item["role_guess"],
                    item["gds_exists"],
                    item["bbox_known"],
                    item["vdd_known"],
                    item["gnd_known"],
                    ", ".join(item["source_of_binding"]) or "-",
                    ", ".join(item["openyield_bindings"]) or "-",
                    item["gds_path"],
                ]
                for item in report["hardcell_macro_gds_inventory"]["items"]
            ],
        ),
        "",
        "## SPICE / CDL Inventory",
        "",
        md_table(
            ["macro", "subckt", "power pins", "matches gds", "path"],
            [
                [
                    item["cell_or_macro"],
                    item["subckt_name"] or "-",
                    ", ".join(item["power_pins_if_parseable"]) or "-",
                    item["matches_gds_macro_name"],
                    item["spice_path"],
                ]
                for item in report["spice_cdl_inventory"]["items"]
            ],
        ),
        "",
        "## LEF / Tech Inventory",
        "",
        md_table(
            ["asset type", "pin info", "routing info", "path"],
            [
                [item["asset_type"], item["pin_layer_info_available"], item["routing_layer_info_available"], item["path"]]
                for item in report["lef_tech_inventory"]["items"]
            ],
        ),
        "",
        "## DRC / KLayout / Verification Inventory",
        "",
        md_table(
            ["tool/deck", "readonly", "requires gds", "used before", "path"],
            [
                [item["tool_or_deck"], item["can_run_readonly"], item["requires_gds_input"], item["used_before"], item["path"]]
                for item in report["drc_klayout_verification_inventory"]["items"][:80]
            ],
        ),
        "",
        "## OpenRAM Generated Outputs",
        "",
        f"- output root: `{report['openram_generated_output_inventory']['root']}`",
        f"- total output files counted: `{report['openram_generated_output_inventory']['total_item_count']}`",
        f"- counts by extension: `{json.dumps(report['openram_generated_output_inventory']['counts_by_extension'], ensure_ascii=False)}`",
        f"- top output directories: `{json.dumps(report['openram_generated_output_inventory']['top_output_directories'], ensure_ascii=False)}`",
        "",
        "Representative outputs:",
        "",
        md_table(
            ["name", "type", "config", "path"],
            [
                [item["output_name"], item["type"], item["config_if_known"] or "-", item["path"]]
                for item in report["openram_generated_output_inventory"]["items"][:60]
            ],
        ),
        "",
        "## Layout Writer / Routing / Standalone Readonly Inventory",
        "",
        md_table(
            ["component", "inspected", "modified", "role", "path"],
            [
                [item["component"], item["read_only_inspected"], item["modified"], item["role_guess"], item["path"]]
                for item in report["layout_writer_routing_standalone_readonly_inventory"]["items"]
            ],
        ),
        "",
        "## Missing Assets",
        "",
        list_block([f"{item['asset']}: {item['reason']}" for item in report["missing_assets"]]),
        "",
        "## Usable Assets For Next Proof",
        "",
        "```json",
        json.dumps(report["usable_assets_for_next_proof"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Ranked Next Readonly Proof Tasks",
        "",
        md_table(
            ["rank", "task", "ready", "reason"],
            [[item["rank"], item["task"], item["ready"], item["reason"]] for item in report["ranked_next_tasks"]],
        ),
        "",
        "## Hardcell Power Rail Continuity Audit Inputs",
        "",
        "```json",
        json.dumps(report["hardcell_power_rail_continuity_readonly_audit_inputs"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Boundary Assertions",
        "",
        "```json",
        json.dumps(report["boundary_assertions"], ensure_ascii=False, indent=2),
        "```",
    ]
    return "\n".join(lines)


def md_table(headers: list[str], rows: Iterable[Iterable[Any]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join(["---"] * len(headers)) + " |"]
    for row in rows:
        out.append("| " + " | ".join(str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in row) + " |")
    return "\n".join(out)


def list_block(items: list[str]) -> str:
    if not items:
        return "- none"
    return "\n".join(f"- {item}" for item in items)
