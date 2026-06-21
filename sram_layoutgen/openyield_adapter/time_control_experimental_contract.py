"""Default-off experimental contract for future OpenYield TIME/control prototype work.

This module is intentionally metadata-only. It does not modify standalone
integration, routing, or GDS writing.  The contract exists so later physical
prototype work can reuse a structured, audited configuration surface instead of
ad hoc booleans or free-form notes.
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
class TimeControlExperimentalConfigSurface:
    flag_name: str
    default_enabled: bool
    allowed_mode: str
    legacy_path_unchanged: bool
    standalone_py_modified: bool
    routing_modified: bool
    gds_writer_modified: bool
    physical_gds_generated: bool
    shared_rail_enabled: bool
    uses_time_as_single_macro: bool
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TimeControlPrototypeSubplan:
    subblock_name: str
    plan_kind: str
    region_name: str | None
    consumer_target: str | None
    metadata_ready: bool | str
    physical_ready: bool
    requires_opt_in: bool
    blocked_by: tuple[str, ...] = ()
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TimeControlExperimentalContract:
    config: TimeControlExperimentalConfigSurface
    prototype_subplans: tuple[TimeControlPrototypeSubplan, ...]
    blocked_capabilities: tuple[str, ...]
    allowed_capabilities: tuple[str, ...]
    gate_snapshot: dict[str, Any] = field(default_factory=dict)
    notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["config"] = self.config.to_dict()
        data["prototype_subplans"] = [item.to_dict() for item in self.prototype_subplans]
        return data


def build_time_control_experimental_contract(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
) -> TimeControlExperimentalContract:
    readiness = _load_json("docs/openyield_time_control_placement_readiness_report.json")
    prototype_plan = _load_json("docs/openyield_time_control_opt_in_prototype_plan_report.json")
    metadata_closure = _load_json("docs/openyield_time_control_metadata_closure_report.json")
    region_refinement = _load_json("docs/openyield_time_control_region_refinement_report.json")

    if not readiness["can_create_experimental_opt_in_placement_plan"]:
        raise ValueError("Stage C gate is not open; experimental contract must not be generated.")

    config = TimeControlExperimentalConfigSurface(
        flag_name="enable_openyield_time_control_experimental_placement",
        default_enabled=False,
        allowed_mode="metadata_prototype_only",
        legacy_path_unchanged=True,
        standalone_py_modified=False,
        routing_modified=False,
        gds_writer_modified=False,
        physical_gds_generated=False,
        shared_rail_enabled=False,
        uses_time_as_single_macro=False,
        notes=(
            "This is a future config surface only; do not wire into the active generator path yet.",
            "The flag remains default-off until later physical proof explicitly reopens the gate.",
        ),
    )

    region_lookup = {
        item["region_name"]: item for item in region_refinement["control_row_region_refinement"]
    }
    readiness_lookup = {
        item["subblock_name"]: item for item in readiness["subblock_readiness"]
    }

    def make_subplan(
        name: str,
        plan_kind: str,
        *,
        region_name: str | None = None,
        consumer_target: str | None = None,
    ) -> TimeControlPrototypeSubplan:
        readiness_item = readiness_lookup[name]
        region_notes: list[str] = []
        if region_name and region_name in region_lookup:
            region = region_lookup[region_name]
            region_notes.extend(
                [
                    f"required_channel_width={region['required_channel_width']}",
                    f"reserved_channel_width={region['reserved_channel_width']}",
                    f"budget_margin={region['budget_margin']}",
                ]
            )
        return TimeControlPrototypeSubplan(
            subblock_name=name,
            plan_kind=plan_kind,
            region_name=region_name,
            consumer_target=consumer_target,
            metadata_ready=readiness_item["metadata_ready"],
            physical_ready=readiness_item["physical_ready"],
            requires_opt_in=True,
            blocked_by=tuple(readiness_item["blocked_by"]),
            notes=tuple(readiness_item["notes"] + region_notes),
        )

    subplans = (
        make_subplan("ADDR_DFF_ROW", "abstract_dff_row", region_name="generated_logic_region"),
        make_subplan("DATA_DFF_ROW", "abstract_dff_row", region_name="generated_logic_region"),
        make_subplan("DELAY_CHAIN_CLUSTER", "timing_chain_cluster", region_name="delay_chain_region"),
        make_subplan("WEN_DELAY_CHAIN_CLUSTER", "timing_chain_cluster", region_name="sense_write_enable_region"),
        make_subplan("PDRIVE_CLUSTER", "buffer_chain_cluster", region_name="pdrive_region"),
        make_subplan("GENERATED_LOGIC_CLUSTER", "stdcell_row_abstract_cluster", region_name="generated_logic_region"),
        make_subplan("PRECHARGE_HANDOFF", "consumer_handoff_reservation_only", region_name="precharge_control_region", consumer_target="PRECHARGE"),
        make_subplan("SENSEAMP_HANDOFF", "consumer_handoff_reservation_only", region_name="sense_write_enable_region", consumer_target="SENSEAMP"),
        make_subplan("WRITEDRIVER_HANDOFF", "consumer_handoff_reservation_only", region_name="sense_write_enable_region", consumer_target="WRITEDRIVER"),
        make_subplan("WORDLINEDRIVER_HANDOFF", "consumer_handoff_reservation_only", region_name="wordline_enable_control_region", consumer_target="WORDLINEDRIVER"),
        make_subplan("DECODER_INTERFACE", "decoder_boundary_reservation_only", region_name="consumer_handoff_region", consumer_target="DECODER_CASCADE"),
    )

    gate_snapshot = {
        "time_control_metadata_closure_available": metadata_closure["consistency_checks"]["time_control_metadata_closure_available"],
        "time_control_metadata_chain_complete": metadata_closure["consistency_checks"]["time_control_metadata_chain_complete"],
        "control_region_crossing_coverage_complete": metadata_closure["consistency_checks"]["control_region_crossing_coverage_complete"],
        "precharge_closure_status": metadata_closure["precharge_closure_status"],
        "can_create_experimental_opt_in_placement_plan": readiness["can_create_experimental_opt_in_placement_plan"],
        "can_modify_standalone_now": False,
        "can_generate_time_control_gds_now": False,
        "can_enter_physical_placement_now": False,
    }

    return TimeControlExperimentalContract(
        config=config,
        prototype_subplans=subplans,
        blocked_capabilities=(
            "standalone integration",
            "physical TIME/control placement",
            "TIME/control GDS generation",
            "legal routing proof",
            "rail continuity proof",
            "shared rail enablement",
        ),
        allowed_capabilities=(
            "default-off config surfacing",
            "abstract row/region metadata packing",
            "consumer handoff reservation modeling",
            "future gate bookkeeping",
        ),
        gate_snapshot=gate_snapshot,
        notes=(
            "This contract refines the Stage D prototype plan into a reusable data model.",
            "It remains metadata-only and cannot be treated as placement or routing proof.",
            f"prototype_plan_scope={prototype_plan['scope']}",
        ),
    )


def build_time_control_experimental_contract_report(
    *,
    openyield_root: str | Path,
    contracts_path: str | Path,
    tech_dir: str | Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    openyield_root = Path(openyield_root)
    contracts_path = Path(contracts_path)
    tech_dir = Path(tech_dir)

    contract = build_time_control_experimental_contract(
        openyield_root=openyield_root,
        contracts_path=contracts_path,
        tech_dir=tech_dir,
    )
    config = contract.config.to_dict()

    report = {
        "scope": "step6_31_openyield_time_control_experimental_contract",
        "openyield_root": str(openyield_root.resolve()),
        "contracts_path": str(contracts_path.resolve()),
        "tech_dir": str(tech_dir.resolve()),
        "config_surface": config,
        "prototype_subplans": [item.to_dict() for item in contract.prototype_subplans],
        "allowed_capabilities": list(contract.allowed_capabilities),
        "blocked_capabilities": list(contract.blocked_capabilities),
        "gate_snapshot": contract.gate_snapshot,
        "consistency_checks": {
            "experimental_contract_available": True,
            "default_enabled": config["default_enabled"],
            "legacy_path_unchanged": config["legacy_path_unchanged"],
            "standalone_py_modified": config["standalone_py_modified"],
            "routing_modified": config["routing_modified"],
            "gds_writer_modified": config["gds_writer_modified"],
            "physical_gds_generated": config["physical_gds_generated"],
            "time_as_single_macro_forbidden": not config["uses_time_as_single_macro"],
            "consumer_handoff_subplans_present": any(
                item["plan_kind"] == "consumer_handoff_reservation_only"
                for item in report_subplans(contract)
            ),
            "abstract_row_subplans_present": any(
                item["plan_kind"] in {"abstract_dff_row", "stdcell_row_abstract_cluster"}
                for item in report_subplans(contract)
            ),
            "can_modify_standalone_now": False,
            "can_generate_time_control_gds_now": False,
            "can_enter_physical_placement_now": False,
        },
        "notes": list(contract.notes),
        "audit_summary": {
            "experimental_contract_available": True,
            "default_enabled": config["default_enabled"],
            "legacy_path_unchanged": config["legacy_path_unchanged"],
            "prototype_subplan_count": len(contract.prototype_subplans),
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
    }

    graph = {
        "scope": report["scope"],
        "nodes": (
            [{"id": contract.config.flag_name, "kind": "config_flag"}]
            + [{"id": item.subblock_name, "kind": item.plan_kind} for item in contract.prototype_subplans]
        ),
        "edges": [
            {
                "source": contract.config.flag_name,
                "target": item.subblock_name,
                "relation": "guards_default_off",
            }
            for item in contract.prototype_subplans
        ],
        "summary": report["audit_summary"],
    }
    return report, graph


def report_subplans(contract: TimeControlExperimentalContract) -> list[dict[str, Any]]:
    return [item.to_dict() for item in contract.prototype_subplans]


def build_time_control_experimental_contract_markdown(report: dict[str, Any]) -> str:
    config_rows = [[key, value] for key, value in report["config_surface"].items() if key != "notes"]
    subplan_rows = [
        [
            item["subblock_name"],
            item["plan_kind"],
            item["region_name"] or "-",
            item["consumer_target"] or "-",
            item["metadata_ready"],
            item["physical_ready"],
            ", ".join(item["blocked_by"]),
        ]
        for item in report["prototype_subplans"]
    ]
    consistency_rows = [[key, value] for key, value in report["consistency_checks"].items()]
    lines = [
        "# OpenYield TIME Control Experimental Contract Report",
        "",
        "This report refines the default-off prototype plan into a structured contract. It remains metadata-only and does not authorize standalone integration, routing, or GDS generation.",
        "",
        "## Audit Summary",
        "",
        "```json",
        json.dumps(report["audit_summary"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Config Surface",
        "",
        _md_table(["field", "value"], config_rows),
        "",
        "## Prototype Subplans",
        "",
        _md_table(
            ["subblock", "plan kind", "region", "consumer", "metadata ready", "physical ready", "blocked by"],
            subplan_rows,
        ),
        "",
        "## Gate Snapshot",
        "",
        "```json",
        json.dumps(report["gate_snapshot"], ensure_ascii=False, indent=2),
        "```",
        "",
        "## Consistency Checks",
        "",
        _md_table(["check", "value"], consistency_rows),
        "",
        "## Allowed Capabilities",
        "",
    ]
    lines.extend(f"- {item}" for item in report["allowed_capabilities"])
    lines.extend(["", "## Blocked Capabilities", ""])
    lines.extend(f"- {item}" for item in report["blocked_capabilities"])
    lines.extend(["", "## Notes", ""])
    lines.extend(f"- {item}" for item in report["notes"])
    lines.append("")
    return "\n".join(lines)
