# OpenYield TIME Control Builder Output Regression Audit

This is a metadata-only regression audit for future builder outputs.

## Audit Summary

```json
{
  "builder_output_regression_audit_available": true,
  "candidate_artifact_shape_complete": true,
  "sample_outputs_forbidden_field_free": true,
  "goal_gates_still_closed": true,
  "future_default_off_builder_output_regression_clean": true,
  "can_modify_standalone_now": false,
  "can_generate_time_control_gds_now": false,
  "can_enter_physical_placement_now": false
}
```

## Artifact Samples

| artifact | kind | top keys | deep keys | forbidden top hits | forbidden deep hits | ok |
| --- | --- | --- | --- | --- | --- | --- |
| candidate_artifact_shape | metadata_plan_object | 10 | 17 | - | - | True |
| experimental_contract.config_surface | metadata_plan_object | 11 | 11 | - | - | True |
| experimental_contract.prototype_subplans | metadata_plan_object | 0 | 99 | - | - | True |
| abstract_floorplan_payload.payload | metadata_plan_object | 13 | 219 | - | - | True |
| goal_progress_audit.audit_summary | json_report | 8 | 8 | - | - | True |

## Output Classes

| artifact class | allowed | must remain nonphysical | notes |
| --- | --- | --- | --- |
| metadata_plan_object | True | True | Abstract builder output may be an in-memory metadata plan only. |
| json_report | True | True | Audit/report outputs are allowed. |
| markdown_report | True | True | Human-readable audit outputs are allowed. |
| gds_layout | False | True | GDS generation remains forbidden. |
| routed_geometry | False | True | Routing geometry remains forbidden. |
| standalone_generator_patch | False | True | Main generator integration remains forbidden. |

## Violations

```json
{
  "missing_required_sections": [],
  "forbidden_field_hits": [],
  "regression_warnings": []
}
```

## Consistency Checks

| check | value |
| --- | --- |
| builder_output_regression_audit_available | True |
| allowed_output_classes_explicit | True |
| forbidden_output_classes_explicit | True |
| candidate_artifact_shape_complete | True |
| sample_outputs_forbidden_field_free | True |
| goal_gates_still_closed | True |
| metadata_only_mode_preserved | True |
| default_off_preserved | True |
| future_default_off_builder_output_regression_clean | True |
| can_modify_standalone_now | False |
| can_generate_time_control_gds_now | False |
| can_enter_physical_placement_now | False |

## Notes

- This audit checks regression drift in metadata-only builder outputs.
- Passing this audit still does not authorize standalone integration, routing, GDS generation, or physical placement.
- The intent is to catch schema creep before any future builder starts emitting physical-looking payloads.

