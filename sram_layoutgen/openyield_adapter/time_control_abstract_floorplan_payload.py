"""Metadata-only abstract floorplan payload for future TIME/control prototype work.

This module packages the Stage C/D readiness outputs into a single payload that
future experimental prototype code could consume.  It does not authorize or
perform standalone integration, physical placement, routing, or GDS writing.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _md_table(headers: list[str], rows: list[list[Any]]) -> str:
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(str(cell).replace("|", "\\|").replace("\n", "<br>") for cell in row)
            + " |"
        )
    return "\n".join(lines)


@dataclass(frozen=True)
class AbstractFloorplanRegion:
    region_name: str
    preferred_neighbor_regions: tuple[str, ...]
    required_channel_width: float
    reserved_channel_width: float
    budget_margin: float
    risk_level: str
    metadata_only: bool
    legal_physical_placement: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AbstractFloorplanSubblock:
    subblock_name: str
    plan_kind: str
    assigned_region: str | None
    relative_order_group: str
    metadata_ready: bool | str
    physical_ready: bool
    requires_opt_in: bool
    consumer_target: str | None
    blocked_by: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AbstractFloorplanHandoff:
    interface_name: str
    source_regions: tuple[str, ...]
    target_macro: str
    control_signals: tuple[str, ...]
    metadata_ready: bool | str
    physical_ready: bool
    blocked_by: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TimeControlAbstractFloorplanPayload:
    flag_name: str
    default_enabled: bool
    legacy_path_unchanged: bool
    standalone_py_modified: bool
    routing_modified: bool
    gds_writer_modified: bool
    physical_gds_generated: bool
    regions: tuple[AbstractFloorplanRegion, ...]
    subblocks: tuple[AbstractFloorplanSubblock, ...]
    handoffs: tuple[AbstractFloorplanHandoff, ...]
    blocked_capabilities: tuple[str, ...]
    notes: tuple[str, ...] = ()
    gate_snapshot: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["regions"] = [item.to_dict() for item in self.regions]
        data["subblocks"] = [item.to_dict() for item in self.subblocks]
        data["handoffs"] = [item.to_dict() for item in self.handoffs]
        return data


def build_time_control_abstract_floorplan_payload(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
) -> TimeControlAbstractFloorplanPayload:
    region_refinement = _load_json("docs/openyield_time_control_region_refinement_report.json")
    readiness = _load_json("docs/openyield_time_control_placement_readiness_report.json")
    contract = _load_json("docs/openyield_time_control_experimental_contract_report.json")

    if not readiness["can_create_experimental_opt_in_placement_plan"]:
        raise ValueError("Stage C gate is closed; abstract floorplan payload must not be generated.")

    regions = tuple(
        AbstractFloorplanRegion(
            region_name=item["region_name"],
            preferred_neighbor_regions=tuple(item["preferred_neighbor_regions"]),
            required_channel_width=float(item["required_channel_width"]),
            reserved_channel_width=float(item["reserved_channel_width"]),
            budget_margin=float(item["budget_margin"]),
            risk_level=str(item["risk_level"]),
            metadata_only=bool(item["metadata_only"]),
            legal_physical_placement=bool(item["legal_physical_placement"]),
            notes=tuple(
                [
                    f"estimated_signal_count={item['estimated_signal_count']}",
                    f"estimated_track_count={item['estimated_track_count']}",
                ]
            ),
        )
        for item in region_refinement["control_row_region_refinement"]
    )

    contract_subplans = {item["subblock_name"]: item for item in contract["prototype_subplans"]}
    relative_order_group_map = {
        "ADDR_DFF_ROW": "front_end_registers",
        "DATA_DFF_ROW": "front_end_registers",
        "DELAY_CHAIN_CLUSTER": "timing_generation",
        "WEN_DELAY_CHAIN_CLUSTER": "timing_generation",
        "PDRIVE_CLUSTER": "timing_generation",
        "GENERATED_LOGIC_CLUSTER": "generated_logic_core",
        "PRECHARGE_HANDOFF": "consumer_handoff_boundary",
        "SENSEAMP_HANDOFF": "consumer_handoff_boundary",
        "WRITEDRIVER_HANDOFF": "consumer_handoff_boundary",
        "WORDLINEDRIVER_HANDOFF": "consumer_handoff_boundary",
        "DECODER_INTERFACE": "decoder_boundary",
    }

    subblocks = tuple(
        AbstractFloorplanSubblock(
            subblock_name=item["subblock_name"],
            plan_kind=contract_subplans[item["subblock_name"]]["plan_kind"],
            assigned_region=contract_subplans[item["subblock_name"]]["region_name"],
            relative_order_group=relative_order_group_map.get(item["subblock_name"], "ungrouped"),
            metadata_ready=item["metadata_ready"],
            physical_ready=bool(item["physical_ready"]),
            requires_opt_in=True,
            consumer_target=contract_subplans[item["subblock_name"]]["consumer_target"],
            blocked_by=tuple(item["blocked_by"]),
            notes=tuple(contract_subplans[item["subblock_name"]]["notes"]),
        )
        for item in readiness["subblock_readiness"]
    )

    handoffs = tuple(
        AbstractFloorplanHandoff(
            interface_name=item["interface_name"],
            source_regions=tuple(item["source_regions"]),
            target_macro=item["target_macro"],
            control_signals=tuple(item["control_signals"]),
            metadata_ready=item["metadata_ready"],
            physical_ready=bool(item["physical_ready"]),
            blocked_by=tuple(item["blocked_by"]),
        )
        for item in region_refinement["grouped_planning_interface_refinement"]
    )

    return TimeControlAbstractFloorplanPayload(
        flag_name=contract["config_surface"]["flag_name"],
        default_enabled=bool(contract["config_surface"]["default_enabled"]),
        legacy_path_unchanged=bool(contract["config_surface"]["legacy_path_unchanged"]),
        standalone_py_modified=False,
        routing_modified=False,
        gds_writer_modified=False,
        physical_gds_generated=False,
        regions=regions,
        subblocks=subblocks,
        handoffs=handoffs,
        blocked_capabilities=tuple(contract["blocked_capabilities"]),
        notes=(
            "This payload is metadata-only and intended for future default-off prototype planning.",
            "It does not prove legal placement, legal routing, rail continuity, or timing closure.",
            "Do not connect this payload to standalone until a later readiness gate explicitly allows it.",
        ),
        gate_snapshot={
            "can_create_experimental_opt_in_placement_plan": readiness["can_create_experimental_opt_in_placement_plan"],
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
            "precharge_closure_status": readiness["consistency_checks"]["precharge_closure_status"],
        },
    )


def build_time_control_abstract_floorplan_payload_report(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    openyield_root = Path(openyield_root)
    contracts_path = Path(contracts_path)
    tech_dir = Path(tech_dir)

    payload = build_time_control_abstract_floorplan_payload(
        openyield_root=openyield_root,
        contracts_path=contracts_path,
        tech_dir=tech_dir,
    )

    report = {
        "scope": "step6_32_openyield_time_control_abstract_floorplan_payload",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(contracts_path.resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "payload": payload.to_dict(),
        "consistency_checks": {
            "abstract_floorplan_payload_available": True,
            "default_enabled": payload.default_enabled,
            "legacy_path_unchanged": payload.legacy_path_unchanged,
            "region_count": len(payload.regions),
            "subblock_count": len(payload.subblocks),
            "handoff_count": len(payload.handoffs),
            "all_regions_metadata_only": all(item.metadata_only for item in payload.regions),
            "all_subblocks_require_opt_in": all(item.requires_opt_in for item in payload.subblocks),
            "any_physical_ready_subblocks": any(item.physical_ready for item in payload.subblocks),
            "standalone_py_modified": payload.standalone_py_modified,
            "routing_modified": payload.routing_modified,
            "gds_writer_modified": payload.gds_writer_modified,
            "physical_gds_generated": payload.physical_gds_generated,
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "audit_summary": {
            "abstract_floorplan_payload_available": True,
            "default_enabled": payload.default_enabled,
            "region_count": len(payload.regions),
            "subblock_count": len(payload.subblocks),
            "handoff_count": len(payload.handoffs),
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "standalone_modified": False,
        "routing_modified": False,
        "gds_writer_modified": False,
        "can_modify_standalone_now": False,
        "can_generate_time_control_gds_now": False,
        "can_enter_physical_placement_now": False,
        "notes": list(payload.notes),
    }

    graph = {
        "scope": report["scope"],
        "nodes": (
            [{"id": item.region_name, "kind": "region"} for item in payload.regions]
            + [{"id": item.subblock_name, "kind": item.plan_kind} for item in payload.subblocks]
            + [{"id": item.interface_name, "kind": "handoff"} for item in payload.handoffs]
        ),
        "edges": (
            [
                {
                    "source": item.subblock_name,
                    "target": item.assigned_region,
                    "relation": "assigned_region",
                }
                for item in payload.subblocks
                if item.assigned_region is not None
            ]
            + [
                {
                    "source": item.interface_name,
                    "target": region,
                    "relation": "draws_from_region",
                }
                for item in payload.handoffs
                for region in item.source_regions
            ]
        ),
        "summary": report["audit_summary"],
    }
    return report, graph


def build_time_control_abstract_floorplan_payload_markdown(report: dict[str, Any]) -> str:
    payload = report["payload"]
    region_rows = [
        [
            item["region_name"],
            ", ".join(item["preferred_neighbor_regions"]),
            item["required_channel_width"],
            item["reserved_channel_width"],
            item["budget_margin"],
            item["risk_level"],
            item["metadata_only"],
        ]
        for item in payload["regions"]
    ]
    subblock_rows = [
        [
            item["subblock_name"],
            item["plan_kind"],
            item["assigned_region"] or "-",
            item["relative_order_group"],
            item["metadata_ready"],
            item["physical_ready"],
            item["consumer_target"] or "-",
        ]
        for item in payload["subblocks"]
    ]
    handoff_rows = [
        [
            item["interface_name"],
            ", ".join(item["source_regions"]),
            item["target_macro"],
            ", ".join(item["control_signals"]),
            item["metadata_ready"],
            item["physical_ready"],
        ]
        for item in payload["handoffs"]
    ]
    consistency_rows = [[key, value] for key, value in report["consistency_checks"].items()]

    lines = [
        "# OpenYield TIME Control Abstract Floorplan Payload Report",
        "",
        "This report packages the TIME/control abstract floorplan payload for future default-off prototype work. It remains metadata-only and does not authorize standalone integration, routing, or GDS generation.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Regions",
        "",
        _md_table(
            ["region", "preferred neighbors", "required width", "reserved width", "margin", "risk", "metadata only"],
            region_rows,
        ),
        "",
        "## Subblocks",
        "",
        _md_table(
            ["subblock", "plan kind", "assigned region", "order group", "metadata ready", "physical ready", "consumer"],
            subblock_rows,
        ),
        "",
        "## Handoffs",
        "",
        _md_table(
            ["interface", "source regions", "target macro", "signals", "metadata ready", "physical ready"],
            handoff_rows,
        ),
        "",
        "## Gate Snapshot",
        "",
        "```json",
        json.dumps(payload["gate_snapshot"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Consistency Checks",
        "",
        _md_table(["check", "value"], consistency_rows),
        "",
        "## Notes",
        "",
    ]
    lines.extend(f"- {item}" for item in report["notes"])
    lines.append("")
    return "\n".join(lines)
