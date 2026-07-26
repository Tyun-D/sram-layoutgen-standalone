# OpenYield TIME Control Prototype Interface Surface Audit

This is a metadata-only interface-surface audit for future default-off prototype builders.

## Audit Summary

```json
{
  "prototype_interface_surface_audit_available": true,
  "config_surface_restricted": true,
  "input_surface_restricted": true,
  "output_surface_restricted": true,
  "future_default_off_builder_interface_surface_clean": true,
  "can_modify_standalone_now": false,
  "can_generate_time_control_gds_now": false,
  "can_enter_physical_placement_now": false
}
```

## Config Surface

| field | allowed | value | metadata-only ok |
| --- | --- | --- | --- |
| flag_name | True | enable_openyield_time_control_experimental_placement | True |
| default_enabled | True | False | True |
| allowed_mode | True | metadata_prototype_only | True |
| legacy_path_unchanged | True | True | True |
| standalone_py_modified | True | False | True |
| routing_modified | True | False | True |
| gds_writer_modified | True | False | True |
| physical_gds_generated | True | False | True |
| shared_rail_enabled | True | False | True |
| uses_time_as_single_macro | True | False | True |
| notes | True | ['This is a future config surface only; do not wire into the active generator path yet.', 'The flag remains default-off until later physical proof explicitly reopens the gate.'] | True |

## Required Inputs

| input | required | metadata-only | present |
| --- | --- | --- | --- |
| experimental_contract.config_surface | True | True | True |
| abstract_floorplan_payload.payload | True | True | True |
| payload_completeness_report | True | True | True |
| payload_consumption_contract_report | True | True | True |
| payload_materialization_boundary_report | True | True | True |
| prototype_execution_guard_report | True | True | True |
| prototype_state_machine_report | True | True | True |

## Output Surface

| artifact | allowed | must remain nonphysical | notes |
| --- | --- | --- | --- |
| metadata_plan_object | True | True | Abstract builder output may be an in-memory metadata plan only. |
| json_report | True | True | Audit/report outputs are allowed. |
| markdown_report | True | True | Human-readable audit outputs are allowed. |
| gds_layout | False | True | GDS generation remains forbidden. |
| routed_geometry | False | True | Routing geometry remains forbidden. |
| standalone_generator_patch | False | True | Main generator integration remains forbidden. |

## Payload Input Counts

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
  "config_violations": [],
  "input_violations": [],
  "output_violations": [],
  "payload_surface_not_explicit": false
}
```

## Consistency Checks

| check | value |
| --- | --- |
| prototype_interface_surface_audit_available | True |
| config_surface_restricted | True |
| input_surface_restricted | True |
| output_surface_restricted | True |
| payload_surface_explicit | True |
| metadata_only_mode_preserved | True |
| default_off_preserved | True |
| future_default_off_builder_interface_surface_clean | True |
| can_modify_standalone_now | False |
| can_generate_time_control_gds_now | False |
| can_enter_physical_placement_now | False |

## Notes

- This audit constrains the future builder's public interface to a minimal metadata-only surface.
- Passing this audit still does not authorize standalone integration, routing, GDS generation, or physical placement.
- The purpose is to keep future implementation scope narrow and explicit.

