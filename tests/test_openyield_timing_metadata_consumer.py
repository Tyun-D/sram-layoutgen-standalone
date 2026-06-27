from __future__ import annotations

import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sram_layoutgen.openyield_adapter.timing_metadata_consumer import (  # noqa: E402
    build_consumable_timing_objects,
    emit_consumer_summary,
    load_control_mapping,
    load_timing_metadata,
)


def main() -> int:
    repo_root = REPO_ROOT
    timing_json = repo_root / 'docs/openyield_delay_chain_timing_metadata_report.json'
    source_json = repo_root / 'docs/openyield_source_provenance_linking_report.json'
    audit_json = repo_root / 'docs/openyield_source_linked_timing_metadata_audit_report.json'
    mapping_csv = repo_root / 'docs/mapping/openyield_control_timing_mapping.csv'

    mappings = load_control_mapping(mapping_csv)
    assert any(entry.openyield_object == 'DELAY_CHAIN' for entry in mappings)
    assert any(entry.openyield_object == 'SENSE_ENABLE_PATH' for entry in mappings)

    timing_bundle = load_timing_metadata(timing_json)
    timing = timing_bundle['timing_metadata']
    assert timing['source_signal'] == 'rbl'
    assert timing['target_signal'] == 'rbl_delay'
    assert timing['stage_count'] == 9
    assert timing['load_policy'] == 'four_load_inverters_per_stage'

    objects = build_consumable_timing_objects(timing_json, source_json, mapping_csv)
    delay_chain = objects['DELAY_CHAIN']
    assert delay_chain.ready_for_metadata_consumption is True
    assert abs(delay_chain.worst_smoke_delay_s - 2.15738e-10) < 1e-18
    assert delay_chain.ready_for_physical_integration is False

    blocked = [entry for entry in mappings if not entry.ready_for_metadata_consumption]
    blocked_names = {entry.openyield_object for entry in blocked}
    assert 'SENSE_ENABLE_PATH' in blocked_names
    assert 'PRECHARGE_ENABLE_PATH' in blocked_names
    assert 'WRITE_ENABLE_PATH' in blocked_names
    assert 'WORDLINE_ENABLE_PATH' in blocked_names
    assert 'GATED_CLOCK_PATH' in blocked_names
    assert 'DFF_ROW' in blocked_names
    assert 'PRECHARGE' in blocked_names
    assert all(entry.ready_for_physical_integration is False for entry in mappings)

    summary = emit_consumer_summary(timing_json, source_json, audit_json, mapping_csv)
    assert summary.gates['can_modify_standalone_now'] is False
    assert summary.gates['metadata_consumer_smoke_pass'] is True
    assert summary.gates['can_enter_control_path_candidate_generation'] is True
    assert summary.gates['can_enter_guarded_adapter_integration'] is True
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
