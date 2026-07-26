# OpenYield TIME Control Prototype Artifact Contract Audit

This is a metadata-only artifact-schema audit for future default-off prototype builders.

## Audit Summary

```json
{
  "prototype_artifact_contract_audit_available": true,
  "required_top_level_keys_explicit": true,
  "forbidden_top_level_keys_explicit": true,
  "gate_snapshot_closed": true,
  "future_default_off_builder_artifact_contract_clean": true,
  "can_modify_standalone_now": false,
  "can_generate_time_control_gds_now": false,
  "can_enter_physical_placement_now": false
}
```

## Required Top-Level Keys

| key | required | metadata-only ok | notes |
| --- | --- | --- | --- |
| artifact_kind | True | True | Must identify a metadata-only artifact class such as abstract_plan_bundle. |
| schema_version | True | True | Needed for deterministic report/builder compatibility. |
| config_snapshot | True | True | Must mirror default-off experimental config state. |
| gate_snapshot | True | True | Must preserve current closed physical/standalone gates. |
| regions | True | True | Abstract region metadata only, not physical geometry. |
| subblocks | True | True | Abstract subblock ordering / grouping metadata only. |
| handoffs | True | True | Metadata-only handoff contracts and reservations. |
| group_order | True | True | Deterministic abstract materialization order. |
| blocker_summary | True | True | Must carry unresolved blocker propagation explicitly. |
| notes | True | True | Human-readable metadata-only scope reminders. |

## Forbidden Top-Level Keys

| key | forbidden now | reason |
| --- | --- | --- |
| gds_path | True | Would imply physical layout generation. |
| topcell_name | True | Would imply a concrete layout database artifact. |
| routed_shapes | True | Routing geometry remains forbidden. |
| via_shapes | True | Via geometry remains forbidden. |
| placed_instances | True | Would overstate abstract metadata as legalized placement. |
| physical_bbox | True | Physical bbox would imply concrete placement proof. |
| standalone_patch | True | Main generator integration remains forbidden. |
| drc_result | True | No physical DRC signoff artifact may be claimed here. |
| lvs_result | True | No physical LVS signoff artifact may be claimed here. |

## Candidate Artifact Shape

```json
{
  "artifact_kind": "abstract_plan_bundle",
  "schema_version": 1,
  "config_snapshot": {
    "flag_name": "enable_openyield_time_control_experimental_placement",
    "default_enabled": false,
    "allowed_mode": "metadata_prototype_only",
    "legacy_path_unchanged": true
  },
  "gate_snapshot": {
    "can_modify_standalone_now": false,
    "can_generate_time_control_gds_now": false,
    "can_enter_physical_placement_now": false
  },
  "regions": "abstract region payload rows only",
  "subblocks": "abstract subblock payload rows only",
  "handoffs": "metadata-only handoff rows only",
  "group_order": "deterministic payload materialization order only",
  "blocker_summary": "propagated unresolved blockers only",
  "notes": "metadata-only scope reminder"
}
```

## Schema Sections

| section | required fields | metadata-only ok |
| --- | --- | --- |
| config_snapshot | flag_name, default_enabled, allowed_mode, legacy_path_unchanged, standalone_py_modified, routing_modified, gds_writer_modified, physical_gds_generated | True |
| gate_snapshot | can_modify_standalone_now, can_generate_time_control_gds_now, can_enter_physical_placement_now | True |
| regions | region_name, preferred_neighbor_regions, required_channel_width, reserved_channel_width, budget_margin, risk_level, metadata_only | True |
| subblocks | subblock_name, plan_kind, assigned_region, relative_order_group, metadata_ready, physical_ready, requires_opt_in, blocked_by | True |
| handoffs | interface_name, source_regions, target_macro, control_signals, metadata_ready, physical_ready | True |

## Payload Topology Counts

```json
{
  "region_count": 7,
  "subblock_count": 11,
  "handoff_count": 4,
  "blocked_capability_count": 6
}
```

## Violations

```json
{
  "missing_required_top_level_keys": [],
  "forbidden_top_level_keys_present": [],
  "schema_section_violations": [],
  "gate_snapshot_violation": false
}
```

## Consistency Checks

| check | value |
| --- | --- |
| prototype_artifact_contract_audit_available | True |
| required_top_level_keys_explicit | True |
| forbidden_top_level_keys_explicit | True |
| artifact_schema_sections_explicit | True |
| candidate_artifact_shape_explicit | True |
| gate_snapshot_closed | True |
| metadata_only_mode_preserved | True |
| default_off_preserved | True |
| future_default_off_builder_artifact_contract_clean | True |
| can_modify_standalone_now | False |
| can_generate_time_control_gds_now | False |
| can_enter_physical_placement_now | False |

## Notes

- This audit constrains future builder artifacts to metadata-only plan bundles.
- Passing this audit still does not authorize standalone integration, routing, GDS generation, or physical placement.
- The purpose is to prevent metadata artifacts from drifting into physical-result claims through schema creep.

