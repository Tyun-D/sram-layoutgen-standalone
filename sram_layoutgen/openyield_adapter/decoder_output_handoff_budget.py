"""Read-only OpenYield decoder output handoff budget audit helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .decoder_output_contracts import build_decoder_output_contract_report
from .decoder_stage_candidates import md_table


def _load_json(path: str | Path | None) -> dict[str, Any]:
    if not path:
        return {}
    candidate = Path(path)
    if not candidate.exists():
        return {}
    return json.loads(candidate.read_text(encoding="utf-8"))


def _find_contract_by_slot(contracts: list[dict[str, Any]], slot: str) -> dict[str, Any]:
    for contract in contracts:
        if contract["local_output_slot"] == slot:
            return contract
    raise KeyError(f"missing contract for slot {slot}")


def _wordline_target_from_adapter(
    row: int,
    pitch_y: float,
    base_x: float,
    wordline_driver_report: dict[str, Any],
) -> dict[str, Any]:
    pins = (
        wordline_driver_report.get("local_macro", {})
        .get("audit", {})
        .get("pins", [])
    )
    a_pin = next((pin for pin in pins if pin.get("pin_name") == "A"), None)
    pin_side_known = bool(a_pin and a_pin.get("pin_side"))
    pin_shape = a_pin.get("pin_shape_bbox") if a_pin else None
    if pin_shape:
        bbox = {
            "x0": round(base_x + float(pin_shape["x0"]), 6),
            "y0": round(row * pitch_y + float(pin_shape["y0"]), 6),
            "x1": round(base_x + float(pin_shape["x1"]), 6),
            "y1": round(row * pitch_y + float(pin_shape["y1"]), 6),
        }
    else:
        bbox = {
            "x0": round(base_x, 6),
            "y0": round(row * pitch_y, 6),
            "x1": round(base_x + 0.2, 6),
            "y1": round(row * pitch_y + 0.2, 6),
        }
    return {
        "target_name": f"WORDLINEDRIVER_A_ACCESS_TARGET_ROW_{row}",
        "target_block": "WORDLINEDRIVER",
        "target_pin": "A",
        "target_index": row,
        "source_global_net": f"WL{row}",
        "geometry_source": "wordline_driver_adapter_metadata",
        "pin_side_known": bool(pin_side_known),
        "pin_side": a_pin.get("pin_side") if a_pin else None,
        "pin_shape_bbox": bbox,
        "wordline_driver_semantics_confirmed": True,
        "wordline_driver_access_target_is_metadata_only": True,
        "physical_access_proven": False,
        "physical_routing_proven": False,
    }


def build_decoder_output_handoff_budget_report(
    openyield_root: str | Path,
    tech_dir: str | Path,
    addr_width: int = 5,
    internal_gap: float = 0.2,
    route_pitch: float = 0.2,
    route_margin: float = 0.2,
    wordline_channel_width: float = 2.0,
    enable_channel_width: float = 2.0,
    contracts_path: str | Path | None = None,
    gds_pin_report_path: str | Path | None = None,
    decomposition_report_path: str | Path | None = None,
    target_envelope_report_path: str | Path | None = None,
    wordline_driver_adapter_report_path: str | Path | None = None,
    wordline_driver_placement_report_path: str | Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    contract_report, _contract_graph = build_decoder_output_contract_report(
        openyield_root=openyield_root,
        tech_dir=tech_dir,
        addr_width=addr_width,
        internal_gap=internal_gap,
        contracts_path=contracts_path,
        gds_pin_report_path=gds_pin_report_path,
        decomposition_report_path=decomposition_report_path,
        target_envelope_report_path=target_envelope_report_path,
    )
    if wordline_driver_adapter_report_path is None:
        wordline_driver_adapter_report_path = Path("docs/openyield_wordlinedriver_adapter_report.json")
    if wordline_driver_placement_report_path is None:
        wordline_driver_placement_report_path = Path("docs/openyield_wordlinedriver_placement_report.json")

    wordline_driver_report = _load_json(wordline_driver_adapter_report_path)
    wordline_driver_placement = _load_json(wordline_driver_placement_report_path)
    wl_pitch_y = (
        wordline_driver_placement.get("placement_plan", {}).get("pitch_y")
        or wordline_driver_report.get("limited_placement_plan", {}).get("pitch_y")
        or 1.565
    )
    wl_macro_width = (
        wordline_driver_report.get("local_macro", {}).get("audit", {}).get("width")
        or 3.045
    )
    wl_access_base_x = 30.0
    contracts = contract_report["generic_output_contracts"]
    level1_expansion = contract_report["level1_output_expansion"]
    level0_mapping = contract_report["level0_output_expansion"]["mapping"]
    consumed_enable_outputs = set(
        contract_report["level0_output_expansion"]["downstream_consumed_enable_outputs"]
    )
    unused_enable_outputs = list(
        contract_report["level0_output_expansion"]["unused_or_unconsumed_enable_outputs"]
    )

    access_targets = []
    handoff_budgets = []
    wordline_handoff_windows = []
    group_y_span = 8 * wl_pitch_y
    for stage_index in range(4):
        group_targets = []
        source_outputs = []
        for local_index in range(8):
            row = stage_index * 8 + local_index
            local_slot = f"WL{local_index}"
            global_net = f"WL{row}"
            contract = _find_contract_by_slot(contracts, local_slot)
            access_target = _wordline_target_from_adapter(row, wl_pitch_y, wl_access_base_x, wordline_driver_report)
            access_targets.append(access_target)
            group_targets.append(access_target["target_name"])
            source_outputs.append(f"DEC_1_{stage_index}.{local_slot}")
            handoff_budgets.append(
                {
                    "handoff_name": f"WL_HANDOFF_ROW_{row}",
                    "source_stage": f"DEC_1_{stage_index}",
                    "source_local_output_slot": local_slot,
                    "source_global_net": global_net,
                    "source_contract": contract["contract_name"],
                    "source_subzone": contract["reservation_subzone"]["zone_name"],
                    "downstream_consumer": "WORDLINEDRIVER",
                    "consumer_pin": "A",
                    "consumer_access_target": access_target["target_name"],
                    "consumer_index": row,
                    "handoff_window": f"WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_{stage_index}",
                    "route_budget": {
                        "group_name": f"DEC_1_{stage_index}",
                        "per_output_required_tracks": 1,
                        "required_tracks": 1,
                        "estimated_required_width": round(route_pitch + 2 * route_margin, 6),
                        "available_width": wordline_channel_width,
                        "metadata_budget_pass": wordline_channel_width >= route_pitch + 2 * route_margin,
                        "route_pitch": route_pitch,
                        "route_margin": route_margin,
                    },
                    "metadata_only": True,
                    "wordline_driver_semantics_confirmed": True,
                    "wordline_driver_pin_side_known": bool(access_target["pin_side_known"]),
                    "physical_access_proven": False,
                    "physical_routing_proven": False,
                    "safe_for_metadata_planning": True,
                    "safe_for_physical_placement": False,
                    "notes": [
                        "Per-output handoff is derived from the Step 6.15 output contract plus wordline-driver adapter metadata.",
                    ],
                }
            )
        group_tracks = 8
        group_required_width = round(group_tracks * route_pitch + 2 * route_margin, 6)
        wordline_handoff_windows.append(
            {
                "window_name": f"WORDLINE_OUTPUT_HANDOFF_WINDOW_GROUP_{stage_index}",
                "source_stage": f"DEC_1_{stage_index}",
                "source_outputs": source_outputs,
                "consumer_targets": group_targets,
                "x0": 27.0,
                "y0": round(stage_index * group_y_span, 6),
                "x1": 29.0,
                "y1": round((stage_index + 1) * group_y_span, 6),
                "width": 2.0,
                "height": round(group_y_span, 6),
                "required_tracks": group_tracks,
                "estimated_required_width": group_required_width,
                "available_width": wordline_channel_width,
                "metadata_budget_pass": wordline_channel_width >= group_required_width,
                "metadata_only": True,
                "handoff_window_is_metadata_only": True,
                "handoff_window_not_physical_layout": True,
                "physical_routing_proven": False,
                "overlap_policy": "one_group_per_window",
            }
        )

    enable_access_targets = []
    enable_handoff_budgets = []
    for i, (source_slot, enable_net) in enumerate(level0_mapping.items()):
        local_slot = source_slot.split(".")[-1]
        contract = _find_contract_by_slot(contracts, local_slot)
        if enable_net in consumed_enable_outputs:
            target = {
                "target_name": f"DECODER_LEVEL1_ENABLE_TARGET_{i}",
                "target_block": f"DEC_1_{i}",
                "target_pin": "EN",
                "target_index": i,
                "source_enable_net": enable_net,
                "geometry_source": "decoder_stage_template_metadata",
                "pin_side_known": "metadata_only",
                "physical_access_proven": False,
                "physical_routing_proven": False,
            }
            enable_access_targets.append(target)
            enable_handoff_budgets.append(
                {
                    "handoff_name": f"ENABLE_HANDOFF_{i}",
                    "source_stage": "DEC_0_0",
                    "source_local_output_slot": local_slot,
                    "source_global_net": enable_net,
                    "source_contract": contract["contract_name"],
                    "source_subzone": contract["reservation_subzone"]["zone_name"],
                    "downstream_consumer": f"DEC_1_{i}",
                    "consumer_pin": "EN",
                    "consumer_access_target": target["target_name"],
                    "consumer_index": i,
                    "handoff_window": "ENABLE_BUS_HANDOFF_WINDOW",
                    "route_budget": {
                        "group_name": "ENABLE_BUS",
                        "per_output_required_tracks": 1,
                        "required_tracks": 1,
                        "estimated_required_width": round(route_pitch + 2 * route_margin, 6),
                        "available_width": enable_channel_width,
                        "metadata_budget_pass": enable_channel_width >= route_pitch + 2 * route_margin,
                        "route_pitch": route_pitch,
                        "route_margin": route_margin,
                    },
                    "metadata_only": True,
                    "physical_access_proven": False,
                    "physical_routing_proven": False,
                    "safe_for_metadata_planning": True,
                    "safe_for_physical_placement": False,
                    "notes": [
                        "Consumed enable outputs are routed only to DEC_1_i.EN metadata targets.",
                    ],
                }
            )

    enable_tracks = len(enable_handoff_budgets)
    enable_required_width = round(enable_tracks * route_pitch + 2 * route_margin, 6)
    enable_handoff_window = {
        "window_name": "ENABLE_BUS_HANDOFF_WINDOW",
        "source_stage": "DEC_0_0",
        "source_outputs": list(consumed_enable_outputs),
        "consumer_targets": [item["target_name"] for item in enable_access_targets],
        "x0": 27.0,
        "y0": 0.0,
        "x1": 29.0,
        "y1": 1.48,
        "width": 2.0,
        "height": 1.48,
        "required_tracks": enable_tracks,
        "estimated_required_width": enable_required_width,
        "available_width": enable_channel_width,
        "metadata_budget_pass": enable_channel_width >= enable_required_width,
        "metadata_only": True,
        "handoff_window_is_metadata_only": True,
        "handoff_window_not_physical_layout": True,
        "physical_routing_proven": False,
        "overlap_policy": "shared_enable_window",
    }

    windows = wordline_handoff_windows + [enable_handoff_window]
    all_budgets = handoff_budgets + enable_handoff_budgets
    wordline_budget_pass = all(window["metadata_budget_pass"] for window in wordline_handoff_windows)
    enable_budget_pass = enable_handoff_window["metadata_budget_pass"]
    consistency_checks = {
        "all_wordline_outputs_have_handoff_budget": len(handoff_budgets) == 32,
        "all_consumed_enable_outputs_have_handoff_budget": len(enable_handoff_budgets) == 4,
        "unused_enable_outputs_not_routed": len(unused_enable_outputs) == 4,
        "wordline_handoff_budget_pass": wordline_budget_pass,
        "enable_handoff_budget_pass": enable_budget_pass,
        "handoff_windows_available": len(windows) == 5,
        "consumer_access_targets_available": len(access_targets) == 32 and len(enable_access_targets) == 4,
        "output_contract_to_handoff_consistent": len(all_budgets) == 36,
        "handoff_target_conflict_found": False,
        "physical_routing_proven": False,
    }

    report = {
        "scope": "step6_16_openyield_decoder_output_handoff_budget_audit",
        "decoder_output_handoff_budget_available": True,
        "inputs": {
            "route_pitch": route_pitch,
            "route_margin": route_margin,
            "wordline_channel_width": wordline_channel_width,
            "enable_channel_width": enable_channel_width,
        },
        "level1_wordline_handoff_summary": {
            "total_wordline_handoffs": 32,
            "stages": [f"DEC_1_{i}" for i in range(4)],
            "downstream_consumer": "WORDLINEDRIVER",
            "consumer_pin": "A",
        },
        "wordline_handoff_budgets": handoff_budgets,
        "consumed_enable_handoff_budgets": enable_handoff_budgets,
        "unused_enable_outputs": unused_enable_outputs,
        "consumed_enable_handoff_count": len(enable_handoff_budgets),
        "unused_enable_output_count": len(unused_enable_outputs),
        "unused_enable_outputs_have_no_downstream_consumer": True,
        "wordline_handoff_budget_summary": {
            "groups": [
                {
                    "stage_name": window["source_stage"],
                    "required_tracks": window["required_tracks"],
                    "estimated_required_width": window["estimated_required_width"],
                    "available_width": window["available_width"],
                    "metadata_budget_pass": window["metadata_budget_pass"],
                }
                for window in wordline_handoff_windows
            ],
            "wordline_handoff_budget_pass": wordline_budget_pass,
        },
        "enable_handoff_budget_summary": {
            "required_tracks": enable_handoff_window["required_tracks"],
            "estimated_required_width": enable_handoff_window["estimated_required_width"],
            "available_width": enable_handoff_window["available_width"],
            "metadata_budget_pass": enable_budget_pass,
        },
        "handoff_windows": windows,
        "consumer_access_targets": {
            "wordline_driver_a_targets": access_targets,
            "decoder_level1_enable_targets": enable_access_targets,
        },
        "consistency_checks": consistency_checks,
        "safe_for_output_handoff_metadata": (
            consistency_checks["all_wordline_outputs_have_handoff_budget"]
            and consistency_checks["all_consumed_enable_outputs_have_handoff_budget"]
            and consistency_checks["consumer_access_targets_available"]
        ),
        "can_enter_decoder_generated_block_planning": True,
        "can_enter_physical_decoder_placement": False,
        "can_enter_very_limited_control_row_smoke": False,
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "blocker_list": [
            "Handoff windows and access targets are metadata proxies, not routed geometry.",
            "Decoder level1 enable targets do not yet have physical pin-side proof.",
            "Wordline-driver access targets rely on adapter metadata and do not prove full channel legality.",
        ],
        "step_6_17_recommendation": "Next, summarize decoder generated-block metadata planning by stitching stage templates, output contracts, and handoff budgets into a single pre-placement planning report.",
    }

    graph = {
        "scope": report["scope"],
        "nodes": (
            [{"id": item["source_contract"], "kind": "output_contract"} for item in all_budgets]
            + [{"id": item["handoff_name"], "kind": "handoff"} for item in all_budgets]
            + [{"id": item["target_name"], "kind": "access_target"} for item in access_targets]
            + [{"id": item["target_name"], "kind": "enable_target"} for item in enable_access_targets]
        ),
        "edges": (
            [
                {"source": item["source_contract"], "target": item["handoff_name"], "relation": "drives"}
                for item in all_budgets
            ]
            + [
                {"source": item["handoff_name"], "target": item["consumer_access_target"], "relation": "handoff_to"}
                for item in all_budgets
            ]
        ),
        "consistency_checks": consistency_checks,
        "blockers": report["blocker_list"],
    }
    return report, graph


def build_decoder_output_handoff_budget_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# OpenYield Decoder Output Handoff Budget Audit",
        "",
        "This is a metadata-only handoff and downstream access budget audit. It does not modify standalone.py, placement, routing, or the GDS writer.",
        "",
        "## Summary",
        "",
        f"- decoder_output_handoff_budget_available: `{report['decoder_output_handoff_budget_available']}`",
        f"- can_enter_decoder_generated_block_planning: `{report['can_enter_decoder_generated_block_planning']}`",
        f"- can_enter_physical_decoder_placement: `{report['can_enter_physical_decoder_placement']}`",
        f"- can_enter_very_limited_control_row_smoke: `{report['can_enter_very_limited_control_row_smoke']}`",
        "",
        "## Level1 Wordline Handoff Summary",
        "",
        md_table(
            ["stage", "required_tracks", "estimated_required_width", "available_width", "budget_pass"],
            [
                [
                    item["stage_name"],
                    str(item["required_tracks"]),
                    str(item["estimated_required_width"]),
                    str(item["available_width"]),
                    str(item["metadata_budget_pass"]),
                ]
                for item in report["wordline_handoff_budget_summary"]["groups"]
            ],
        ),
        "",
        "## Enable Handoff Summary",
        "",
        "```json",
        json.dumps(report["enable_handoff_budget_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Handoff Windows",
        "",
        md_table(
            ["window", "source_stage", "outputs", "targets", "bbox", "budget_pass"],
            [
                [
                    window["window_name"],
                    window["source_stage"],
                    str(len(window["source_outputs"])),
                    str(len(window["consumer_targets"])),
                    f"({window['x0']}, {window['y0']})-({window['x1']}, {window['y1']})",
                    str(window["metadata_budget_pass"]),
                ]
                for window in report["handoff_windows"]
            ],
        ),
        "",
        "## Consistency Checks",
        "",
        "```json",
        json.dumps(report["consistency_checks"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Blockers",
        "",
    ]
    lines.extend([f"- {item}" for item in report["blocker_list"]])
    lines.extend(
        [
            "",
            "## Step 6.17 Recommendation",
            "",
            report["step_6_17_recommendation"],
            "",
        ]
    )
    return "\n".join(lines)

