"""Consumer API for OpenYield source-linked timing metadata."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ControlMappingEntry:
    openyield_object: str
    openyield_source_file: str
    openyield_signal_or_node: str
    local_timing_object: str
    local_candidate_artifact: str
    local_metadata_artifact: str
    evidence_status: str
    measured_delay_available: bool
    worst_smoke_delay_s: float | None
    corner_coverage: str
    integration_readiness: str
    next_required_action: str
    forbidden_claims: list[str] = field(default_factory=list)

    @property
    def ready_for_metadata_consumption(self) -> bool:
        return self.evidence_status == 'source_linked_and_smoke_timing_metadata_available'

    @property
    def ready_for_physical_integration(self) -> bool:
        return False

    @property
    def blocked_reason(self) -> str:
        if self.ready_for_metadata_consumption:
            return ''
        return self.next_required_action or self.evidence_status


@dataclass
class CandidateContractEntry:
    control_object: str
    priority: int
    openyield_source_file: str
    source_symbol: str
    source_ports_or_nodes: str
    local_candidate_name: str
    candidate_type: str
    candidate_artifact: str
    spice_candidate_available: bool
    testbench_skeleton_available: bool
    timing_metadata_available: bool
    source_evidence_status: str
    recovery_status: str
    blocked_reason: str
    next_required_action: str
    integration_readiness: str
    forbidden_claims: list[str] = field(default_factory=list)


@dataclass
class TimingObjectMetadata:
    name: str
    source_signal: str
    target_signal: str
    stage_count: int
    load_policy: str
    inversion: str
    corner_delays: dict[str, dict[str, float]]
    worst_smoke_delay_s: float
    worst_corner: str
    evidence_status: str
    source_linked: bool
    ready_for_metadata_consumption: bool
    ready_for_physical_integration: bool
    forbidden_claims: list[str]
    model_corners: list[str]
    vdd: float
    temp_c: float
    delay_unit: str


@dataclass
class TimingConsumerSummary:
    ready_objects: list[str]
    blocked_objects: list[str]
    delay_chain_consumable: bool
    delay_chain_worst_smoke_delay_s: float
    delay_chain_worst_corner: str
    delay_chain_corner_table: dict[str, dict[str, float]]
    metadata_consumer_api_available: bool
    next_adapter_action: str
    forbidden_actions: list[str]
    gates: dict[str, Any]


def load_timing_metadata(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    timing = payload['timing_metadata']
    corner_table = payload['corner_delay_table']
    return {
        'raw_report': payload,
        'timing_metadata': timing,
        'corner_delay_table': corner_table,
    }


def load_control_mapping(path: str | Path) -> list[ControlMappingEntry]:
    entries: list[ControlMappingEntry] = []
    with Path(path).open('r', encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            entries.append(
                ControlMappingEntry(
                    openyield_object=row['openyield_object'],
                    openyield_source_file=row['openyield_source_file'],
                    openyield_signal_or_node=row['openyield_signal_or_node'],
                    local_timing_object=row['local_timing_object'],
                    local_candidate_artifact=row['local_candidate_artifact'],
                    local_metadata_artifact=row['local_metadata_artifact'],
                    evidence_status=row['evidence_status'],
                    measured_delay_available=_parse_bool(row['measured_delay_available']),
                    worst_smoke_delay_s=_parse_float(row['worst_smoke_delay_s']),
                    corner_coverage=row['corner_coverage'],
                    integration_readiness=row['integration_readiness'],
                    next_required_action=row['next_required_action'],
                    forbidden_claims=[item for item in row['forbidden_claims'].split(';') if item],
                )
            )
    return entries


def load_candidate_contracts(path: str | Path) -> list[CandidateContractEntry]:
    entries: list[CandidateContractEntry] = []
    with Path(path).open('r', encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            entries.append(
                CandidateContractEntry(
                    control_object=row['control_object'],
                    priority=int(row['priority']),
                    openyield_source_file=row['openyield_source_file'],
                    source_symbol=row['source_symbol'],
                    source_ports_or_nodes=row['source_ports_or_nodes'],
                    local_candidate_name=row['local_candidate_name'],
                    candidate_type=row['candidate_type'],
                    candidate_artifact=row['candidate_artifact'],
                    spice_candidate_available=_parse_bool(row['spice_candidate_available']),
                    testbench_skeleton_available=_parse_bool(row['testbench_skeleton_available']),
                    timing_metadata_available=_parse_bool(row['timing_metadata_available']),
                    source_evidence_status=row['source_evidence_status'],
                    recovery_status=row['recovery_status'],
                    blocked_reason=row['blocked_reason'],
                    next_required_action=row['next_required_action'],
                    integration_readiness=row['integration_readiness'],
                    forbidden_claims=[item for item in row['forbidden_claims'].split(';') if item],
                )
            )
    return entries


def get_control_object_status(
    mapping_csv: str | Path,
    contracts_csv: str | Path,
    control_object: str,
) -> dict[str, Any]:
    mapping = next(
        entry for entry in load_control_mapping(mapping_csv)
        if entry.openyield_object == control_object
    )
    contract = next(
        entry for entry in load_candidate_contracts(contracts_csv)
        if entry.control_object == control_object
    )
    return {
        "control_object": control_object,
        "mapping_evidence_status": mapping.evidence_status,
        "mapping_candidate_artifact": mapping.local_candidate_artifact,
        "mapping_next_required_action": mapping.next_required_action,
        "contract_evidence_status": contract.source_evidence_status,
        "contract_candidate_artifact": contract.candidate_artifact,
        "contract_recovery_status": contract.recovery_status,
        "contract_next_required_action": contract.next_required_action,
        "ready_for_metadata_consumption": mapping.ready_for_metadata_consumption,
        "ready_for_physical_integration": False,
        "forbidden_claims": contract.forbidden_claims,
    }


def build_consumable_timing_objects(
    timing_json: str | Path,
    source_json: str | Path,
    mapping_csv: str | Path,
) -> dict[str, TimingObjectMetadata]:
    timing_bundle = load_timing_metadata(timing_json)
    source_payload = json.loads(Path(source_json).read_text(encoding='utf-8'))
    mappings = load_control_mapping(mapping_csv)
    delay_chain = get_delay_chain_metadata(timing_bundle, source_payload, mappings)
    return {delay_chain.name: delay_chain}


def get_delay_chain_metadata(
    timing_bundle: dict[str, Any],
    source_payload: dict[str, Any],
    mappings: list[ControlMappingEntry],
) -> TimingObjectMetadata:
    timing = timing_bundle['timing_metadata']
    corner_table = timing_bundle['corner_delay_table']
    mapping = next(entry for entry in mappings if entry.openyield_object == 'DELAY_CHAIN')
    source_linked = bool(
        source_payload['gates']['delay_chain_source_found']
        and source_payload['gates']['source_to_candidate_spice_consistent']
        and source_payload['gates']['source_to_timing_metadata_consistent']
    )
    corner_delays = {
        corner: {
            'rise_to_fall_delay_s': values['rise_to_fall_delay_s'],
            'fall_to_rise_delay_s': values['fall_to_rise_delay_s'],
            'max_delay_s': values['max_delay_s'],
        }
        for corner, values in corner_table.items()
    }
    return TimingObjectMetadata(
        name='DELAY_CHAIN',
        source_signal=timing['source_signal'],
        target_signal=timing['target_signal'],
        stage_count=int(timing['stage_count']),
        load_policy=timing['load_policy'],
        inversion=timing['inversion'],
        corner_delays=corner_delays,
        worst_smoke_delay_s=float(timing['worst_smoke_delay']),
        worst_corner=timing['worst_smoke_delay_corner'],
        evidence_status=mapping.evidence_status,
        source_linked=source_linked,
        ready_for_metadata_consumption=source_linked and mapping.ready_for_metadata_consumption,
        ready_for_physical_integration=False,
        forbidden_claims=mapping.forbidden_claims,
        model_corners=list(timing['model_corners']),
        vdd=float(timing['VDD']),
        temp_c=float(timing['TEMP']),
        delay_unit=timing['delay_unit'],
    )


def get_ready_objects(mappings: list[ControlMappingEntry]) -> list[ControlMappingEntry]:
    return [entry for entry in mappings if entry.ready_for_metadata_consumption]


def get_blocked_objects(mappings: list[ControlMappingEntry]) -> list[ControlMappingEntry]:
    return [entry for entry in mappings if not entry.ready_for_metadata_consumption]


def validate_delay_chain_consistency(
    timing_bundle: dict[str, Any],
    source_payload: dict[str, Any],
    audit_payload: dict[str, Any],
    mappings: list[ControlMappingEntry],
) -> dict[str, Any]:
    timing = timing_bundle['timing_metadata']
    mapping = next(entry for entry in mappings if entry.openyield_object == 'DELAY_CHAIN')
    checks = {
        'delay_chain_source_linked': bool(source_payload['gates']['delay_chain_source_found']),
        'delay_chain_timing_metadata_available': bool(timing_bundle['raw_report']['audit_summary']['delay_chain_timing_metadata_update_available']),
        'source_signal_match': timing['source_signal'] == 'rbl',
        'target_signal_match': timing['target_signal'] == 'rbl_delay',
        'stage_count_match': int(timing['stage_count']) == 9,
        'four_load_policy_recorded': timing['load_policy'] == 'four_load_inverters_per_stage',
        'worst_delay_match': abs(float(timing['worst_smoke_delay']) - 2.15738e-10) < 1e-18,
        'worst_corner_match': timing['worst_smoke_delay_corner'] == 'ss',
        'corner_coverage_match': list(timing['model_corners']) == ['nom', 'ff', 'ss'],
        'mapping_ready_match': mapping.ready_for_metadata_consumption,
        'audit_ready_match': bool(audit_payload['gates']['delay_chain_ready_for_metadata_consumption']),
    }
    checks['all_pass'] = all(checks.values())
    return checks


def emit_consumer_summary(
    timing_json: str | Path,
    source_json: str | Path,
    audit_json: str | Path,
    mapping_csv: str | Path,
) -> TimingConsumerSummary:
    timing_bundle = load_timing_metadata(timing_json)
    source_payload = json.loads(Path(source_json).read_text(encoding='utf-8'))
    audit_payload = json.loads(Path(audit_json).read_text(encoding='utf-8'))
    mappings = load_control_mapping(mapping_csv)
    objects = build_consumable_timing_objects(timing_json, source_json, mapping_csv)
    delay_chain = objects['DELAY_CHAIN']
    consistency = validate_delay_chain_consistency(timing_bundle, source_payload, audit_payload, mappings)
    ready = get_ready_objects(mappings)
    blocked = get_blocked_objects(mappings)
    ready_names = [entry.openyield_object for entry in ready]
    blocked_names = [entry.openyield_object for entry in blocked]
    gates = {
        'metadata_consumer_adapter_available': True,
        'metadata_consumer_smoke_pass': consistency['all_pass'],
        'delay_chain_metadata_loaded': delay_chain.name == 'DELAY_CHAIN',
        'delay_chain_source_linked': delay_chain.source_linked,
        'delay_chain_ready_for_metadata_consumption': delay_chain.ready_for_metadata_consumption,
        'delay_chain_ready_for_physical_integration': False,
        'blocked_control_objects_recorded': bool(blocked_names),
        'control_mapping_loaded': bool(mappings),
        'consumer_api_ready': consistency['all_pass'],
        'can_enter_control_path_candidate_generation': consistency['all_pass'],
        'can_enter_guarded_adapter_integration': consistency['all_pass'],
        'can_modify_standalone_now': False,
        'can_generate_time_control_gds_now': False,
        'can_claim_openyield_full_integration_now': False,
        'can_claim_timing_closure_now': False,
    }
    return TimingConsumerSummary(
        ready_objects=ready_names,
        blocked_objects=blocked_names,
        delay_chain_consumable=delay_chain.ready_for_metadata_consumption,
        delay_chain_worst_smoke_delay_s=delay_chain.worst_smoke_delay_s,
        delay_chain_worst_corner=delay_chain.worst_corner,
        delay_chain_corner_table=delay_chain.corner_delays,
        metadata_consumer_api_available=True,
        next_adapter_action='control_path_candidate_generation_or_guarded_adapter_integration',
        forbidden_actions=[
            'modify_standalone',
            'modify_routing',
            'modify_gds_writer',
            'generate_time_control_gds',
            'claim_openyield_full_integration',
            'claim_timing_closure',
            'claim_physical_integration',
        ],
        gates=gates,
    )


def summary_to_dict(summary: TimingConsumerSummary) -> dict[str, Any]:
    return asdict(summary)


def _parse_bool(value: str) -> bool:
    return str(value).strip().lower() == 'true'


def _parse_float(value: str) -> float | None:
    text = str(value).strip()
    if not text:
        return None
    return float(text)
